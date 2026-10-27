# VPN Super 节点接入 new-api 代理池 — 对接指南

> 给对接会话的完整交接文档。逆向已完成并验证的部分全部可以直接用；未完成部分（出口实连）也标清了卡点与验证方法。
>
> 仓库: https://github.com/lza6/VPN-Super-Unlimited-Proxy （含全部工具与数据）

## 1. 你会拿到什么

| 资源 | 位置 | 状态 |
|---|---|---|
| 节点列表一键拉取+解密 | `tools/decrypt_supx.py` | ✅ 已验证（US/DE 双 region 实测） |
| 全量节点明文（1199 台/16 国） | `docs/servers_full.json` | ✅ |
| supx TCP 存活端点（1195/1250） | `docs/supx_alive.json` | ✅（一轮快测，入池前需二轮复测） |
| AES 密钥与加密封装说明 | `docs/逆向报告.md` | ✅ |
| demo 服务（节点浏览器） | `tools/demo_server.py :8910` | ✅ 已实测 |

## 2. 协议速查（对接必需的全部参数）

### 2.1 拉取节点
```
GET https://prod-api.mobilejump.mobi/be-data/v7/server_list
    ?platform=android&vip={true|false}&region={US|DE|SG...大写}&app=ee.vpn.super.hotspot.open
Header: User-Agent: okhttp/4.9.3      ← 必带，否则 403
```
响应 = `[1B IVlen=0x10][16B IV][AES-256-CBC 密文]`，密钥 `01fb3864e37eb5d4ada3a50a1f1a373e`（32B ASCII 直接作 AES-256 key），解密后 zlib 解压得 JSON。`decrypt_supx.py` 已封装全流程。region 小写会 400（uppercase 校验），vip=true/false 内容相同。

备份源（无加密格式变化）: `https://raw.githubusercontent.com/SuperUnlimited/data-backup/v1/sl/{md5}`，仓库树可经 GitHub API 全量枚举，4500 个文件。

### 2.2 节点结构
```json
{
 "host": "82.110.60.2", "load": 3576, "password": "treeup",
 "location": {"country": "AT", "city": "Vienna"},
 "services": [
   {"id": "openvpn_v2_udp", "ports": [1194],  "inbound_ip": "82.110.60.2"},
   {"id": "wireguard_v2",   "ports": [10970], "inbound_ip": "82.110.60.4"},
   {"id": "supx_v20", "ports": [19999], "inbound_ip": "..."},
   {"id": "supx_v21", "ports": [1270],  "inbound_ip": "..."},
   {"id": "supx_v22", "ports": [11371], "inbound_ip": "..."},
   {"id": "supx_v23", "ports": [52014], "inbound_ip": "..."}
 ]
}
```
`supx_*` 是 clash 系出站（Go 核心 libgojni = Dreamacro/clash），是我们唯一能转 SOCKS5/HTTP 代理入池的通道。

### 2.3 supx 协议模板（从 app assets dump 解出）
| service | 端口 | 协议 | 参数 |
|---|---|---|---|
| supx_v20 | 19999 | Shadowsocks | method `aes-256-gcm`, pw `ZRpgaBeGxtENIXgvhpkZBKz9GnWRS2dYcx9O+a2iwN4=` |
| supx_v21 | 1270 | VMess+TLS | UUID `5c040f1d-45db-43bd-8d46-e4950e433735`, SNI `xmfhlpy.com`, TCP+none header |
| supx_v1/v3 | — | VMess | 同上 UUID |
| supx_v5/v7 | — | VLESS | UUID `652c1a22-1b2a-42f0-8b01-16de5ca99da3`, flow `xtls-rprx-vision` |
| **supx_v22/v23** | 11371/52014 | **未知**（模板未下发，见 §4） |

### 2.4 OpenVPN 凭证（参考，不建议入池）
password = `treeup` / `treeup123`；IKEv2 :500/4500、OpenVPN :1194、WireGuard :10970。VPN 协议转代理需 TUN 层，成本高且需证书，跳过。

## 3. ⚠️ 对接前必读：当前卡点

**静态路线已验证到顶：所有协议矩阵实测全部 REF。**

- TCP 端口活（1195/1250），但 xray 26.10.21 以 plain/TLS/grpc/SS2022 全部握手失败
- 裸 TLS ClientHello 被服务端 **RST** → 服务端有 TLS 指纹/来源过滤（uTLS 嫌疑最大）
- **验证过的失败组合**（不要重复）：vmess plain、vmess+TLS(xmfhlpy.com)、vmess+ws、vmess+grpc、ss aes-256-gcm(b64 pw/hex pw/treeup123)、ss chacha20、ss-2022、vless+vision+TLS、trojan
- 860 台节点无 services 字段 → 用 default_services + host 端口映射

**卡点突破路径（按优先级）：**
1. **Frida 动态抓真实出站配置**（环境已就绪）：D:/android-sdk emulator-5554 + Frida 17.24.3（历史会话已验证可 attach，且已对 `com.free.vpn.super.hotspot.open` 成功转储过 10 个 DEX）。Hook 目标：
   - `libgojni.so` 中 clash `adapter/outbound` 构造函数（`ShadowSocksOption`/`v2rayObfsOption`）
   - Java 层 `defpackage.n92`（V2ray id 封装）、`zc2`（连接管理）
   - 拿到 v22/v23 真实协议与参数后补进本指南
2. **uTLS 复测**：xray 的 `streamSettings.tlsSettings.fingerprint: "chrome"`。若服务端只认 chrome 指纹，一行配置即可打通 v21/v22
3. 若上两条都通：出口 IP 验证用 `curl --socks5-hostname 127.0.0.1:{port} https://api.ipify.org`

## 4. 对接 new-api 代理池的建议架构（卡点解决后）

参照本项目已有的 VPN→SOCKS5 转换层模式（参考 QuixVPN 会话的 `quixsocks`）：

```
server_list API (AES 解密) → 节点池调度器 → xray 实例池(每个节点一个 socks inbound)
       ↓ load 字段排序                          ↓ 127.0.0.1:2xxxx
   new-api 代理池 (relay/channel/notrack 共享代理池) ← 定向测活 + 失败摘除
```

建议实现要点：
1. **入池前二轮测活**：一轮 TCP connect（快筛），二轮真实代理请求（`https://api.ipify.org` 过 socks），只有拿到出口 IP 的才入池——不要相信 load 字段
2. **xray 批量编排**：单进程多 inbound（每节点 socks port 20000+i），配置热更新用 xray API 或重启子进程
3. **指纹**：若 §4.1 的 uTLS 假设成立，全部 v21 节点加 `fingerprint: chrome`
4. **v22/v23 未定协议**：先只入 v20/v21（若打通），v22/v23 数量占 supx 一半（324+301），值得花一次 Frida 成本
5. **合规红线**：节点为公司自有 VPS。研究/本地验证可以，**生产池挂别人付费服务器属于盗用基础设施**——这与之前 Gulf Secure VPN 定论一致。若要入池，建议只入用于可用性研究的最小集，或等待与 VPNGate 类公共源混合的方案

## 5. 交接清单（对接会话开工顺序）

1. `git clone https://github.com/lza6/VPN-Super-Unlimited-Proxy` → 读 `docs/逆向报告.md`
2. 跑 `python tools/decrypt_supx.py US false` 确认拉取链路活着（2026-10-28 验证通过）
3. 起 emulator-5554 + Frida，按 §3.1 hook libgojni，目标：v22/v23 出站 JSON
4. 用拿到的参数 + uTLS 指纹复测 §2.3 全部模板（xray 已在逆向工作区 `Downloads/vpn_super_ws/xraybin/`）
5. 打通 → 按 §4 架构入池；不通 → 报告阻塞点（附 xray info 级日志），不要伪造验证结果
