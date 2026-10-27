#!/usr/bin/env python3
"""VPN Super (SuperUnlimited/MobileJump) 节点列表一键拉取+解密
用法: python decrypt_supx.py [region] [vip]
验证: AES-256-CBC(key=32B ASCII '01fb3864e37eb5d4ada3a50a1f1a373e') + zlib
"""
import sys, json, zlib, subprocess
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

KEY = b'01fb3864e37eb5d4ada3a50a1f1a373e'  # 32B ASCII → AES-256-CBC
API = 'https://prod-api.mobilejump.mobi/be-data/v7/server_list?platform=android&vip={vip}&region={region}&app=ee.vpn.super.hotspot.open'

def fetch(region='US', vip='false'):
    subprocess.run(['curl', '-s', '--ssl-no-revoke', '-m', '30', '-A', 'okhttp/4.9.3',
                    API.format(region=region.upper(), vip=vip), '-o', '_sl_tmp.bin'], check=True)
    d = open('_sl_tmp.bin', 'rb').read()
    ivl = d[0]
    pt = unpad(AES.new(KEY, AES.MODE_CBC, d[1:1+ivl]).decrypt(d[1+ivl:]), 16)
    return json.loads(zlib.decompress(pt))

if __name__ == '__main__':
    region = sys.argv[1] if len(sys.argv) > 1 else 'US'
    vip = sys.argv[2] if len(sys.argv) > 2 else 'false'
    j = fetch(region, vip)
    sv = j['servers'] + j['vip_servers']
    print(f'region={region} vip={vip}: {len(sv)} servers, generation_ts={j["_meta"]["generation_ts"]}')
    json.dump(j, open(f'sl_{region}_{vip}.json', 'w'), indent=1)
    print('saved', f'sl_{region}_{vip}.json')
