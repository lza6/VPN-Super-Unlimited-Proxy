#!/usr/bin/env python3
"""VPN Super 节点 demo 服务 :8910
/api/servers  全量节点(实时拉取+解密, 10min 缓存)
/api/stats    国家/服务分布
/             demo 页
"""
import json, zlib, subprocess, time, threading, os, sys
from collections import Counter
from http.server import HTTPServer, BaseHTTPRequestHandler
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

WS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, WS)
from decrypt_supx import fetch

CACHE = {'ts': 0, 'data': None}
LOCK = threading.Lock()

def get_data():
    with LOCK:
        if CACHE['data'] and time.time() - CACHE['ts'] < 600:
            return CACHE['data']
        j = fetch('US', 'false')
        CACHE.update(ts=time.time(), data=j)
        return j

class H(BaseHTTPRequestHandler):
    def _j(self, obj, code=200):
        b = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if self.path == '/api/servers':
            j = get_data()
            sv = j['servers'] + j['vip_servers']
            out = [{'host': s['host'], 'country': s.get('location', {}).get('country'),
                    'city': s.get('location', {}).get('city'), 'load': s['load'],
                    'vip': s in j['vip_servers'],
                    'services': [{'id': x['id'], 'ip': x['inbound_ip'], 'ports': x['ports']}
                                 for x in s.get('services', [])]}
                  for s in sv]
            self._j({'count': len(out), 'servers': out})
        elif self.path == '/api/stats':
            j = get_data()
            sv = j['servers'] + j['vip_servers']
            self._j({
                'total': len(sv),
                'countries': Counter(s.get('location', {}).get('country') for s in sv).most_common(),
                'services': Counter(x['id'] for s in sv for x in s.get('services', [])).most_common(),
                'generation_ts': j['_meta']['generation_ts'],
            })
        elif self.path == '/':
            p = os.path.join(WS, 'demo.html')
            b = open(p, 'rb').read()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(b)))
            self.end_headers()
            self.wfile.write(b)
        else:
            self._j({'error': 'not found'}, 404)

    def log_message(self, *a): pass

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8910
    print('VPN Super demo :', port)
    HTTPServer(('127.0.0.1', port), H).serve_forever()
