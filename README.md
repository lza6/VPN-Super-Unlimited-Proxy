# 🔓 VPN-Super-Unlimited-Proxy 逆向研究

> **VPN Super Unlimited Proxy v2.33.0** (SuperUnlimited / MobileJump) 节点下发协议完整还原 — 仅用于安全研究与学习。

## 状态表

| 里程碑 | 状态 |
|---|---|
| APK 结构分析（三 VPN 通道：OpenVPN / strongSwan IKEv2 / Go-clash 核心） | ✅ |
| 节点下发 API 定位（prod-api.mobilejump.mobi + GitHub 备份源） | ✅ |
| AES 密钥还原（libnative-legacy.sogetKeyBytes 四段 XOR 0xA5） | ✅ |
| 节点列表全量解密（1199 台 / 16 国 / 全服务矩阵） | ✅ |
| supx 协议模板还原（SS / VMess+TLS / VLESS+vision） | ✅ |
| demo 服务（本地节点浏览器 :8910） | ✅ |
| TCP 测活（1195/1250 存活） | ✅ |
| v22/v23 服务协议（模板未下发） | ⏳ 需模拟器 + Frida 动态抓包 |
| 端到端出口实连（服务端有 TLS 指纹过滤） | ⏳ 待 uTLS 复测 |

## 快速开始

```bash
pip install pycryptodome
python tools/decrypt_supx.py US false    # 一键拉取+解密任意 region
python tools/demo_server.py 8910         # 本地 demo → http://127.0.0.1:8910
```

## 核心发现速览

- **节点下发**: `GET https://prod-api.mobilejump.mobi/be-data/v7/server_list?platform=android&vip={bool}&region={大写CC}&app=ee.vpn.super.hotspot.open`（必须带 UA，否则 403）
- **加密格式**: `[1B IV长度][16B IV][AES-256-CBC][zlib JSON]`
- **密钥**: `01fb3864e37eb5d4ada3a50a1f1a373e`（32B ASCII 直接作 AES-256 key，藏在 `libnative-legacy.so getKeyBytes`，四段 8 字节常量 XOR 0xA5 按执行序拼接）
- **官方备份源**: GitHub `SuperUnlimited/data-backup`（v1 分支）的 `sl/` 目录 4500 个同构文件**公开可枚举**
- **协议模板**: v20=Shadowsocks aes-256-gcm / v21=VMess+TLS(SNI `xmfhlpy.com`) / v5,v7=VLESS+vision / v22,v23=模板未下发
- **合规**: 节点为公司自有 VPS，凭证披露 ≠ 授权使用，**请勿接入生产环境**

## 文档

- [完整逆向报告](docs/逆向报告.md)
- [全量节点明文](docs/servers_full.json) · [TCP 测活结果](docs/supx_alive.json)

## 路线图

1. Android 模拟器（D:/android-sdk, emulator-5554）+ Frida 17.24.3 hook `libgojni` 的 clash 出站构造，拿 v22/v23 真实参数
2. 用 xray `fingerprint:chrome`(uTLS) 复测 VMess+TLS——当前裸 TLS ClientHello 被服务端 RST，uTLS 指纹嫌疑最大
3. 打通后可本地验证出口 IP（研究用途）

## License

MIT — 仅供学习，使用者自负责任。
