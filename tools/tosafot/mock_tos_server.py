# -*- coding: utf-8 -*-
"""mock_tos_server.py - נקודת קליטה מקומית מדומה לנתיב /tos בלבד, לבדיקת ממשק המבחן בלי מפתח מנהל אמיתי.

משחזר את ההתנהגות של tosApi ב-worker/leokmei-suggest/src/index.js (GET ציבורי ומנהל, PUT זריעה, POST בחירה/הערה/pick=none).
הכל בזיכרון, לא נוגע בשום שרת אמיתי. בדפדפן, בדף שנטען מ-localhost: localStorage['lg-api']='http://127.0.0.1:8788',
localStorage['lg-admin']='1', localStorage['lg-adm']='test-key'.

    uv run python tools/tosafot/mock_tos_server.py 8788
"""
import sys, json, time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

DB = {}
PICKS = ['a', 'b', 'c', 'd', 'e', 'custom']


class H(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'content-type,x-admin-key,x-proposer,x-device,authorization')
        self.send_header('Access-Control-Allow-Methods', 'GET,PUT,POST,OPTIONS')

    def _send(self, code, o):
        b = json.dumps(o, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self._cors()
        self.send_header('content-type', 'application/json; charset=utf-8')
        self.send_header('content-length', str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def _doc(self, slug):
        return DB.setdefault(slug, {'slug': slug, 'styles': {}, 'picks': {}, 'notes': {}, 'log': []})

    def do_GET(self):
        u = urlparse(self.path)
        if u.path != '/tos':
            return self._send(200, {'ok': True, 'service': 'mock'})
        q = parse_qs(u.query)
        doc = self._doc(q.get('slug', [''])[0])
        if q.get('adm', [''])[0] == '1':
            return self._send(200, {'ok': True, 'doc': doc})
        return self._send(200, {'ok': True, 'pub': {n: {'p': p['p'], 't': p['t']} for n, p in doc['picks'].items()}, 't': doc.get('t', 0)})

    def _body(self):
        n = int(self.headers.get('content-length') or 0)
        return json.loads(self.rfile.read(n).decode('utf-8')) if n else {}

    def do_PUT(self):
        b = self._body()
        doc = self._doc(b['slug'])
        for k, v in (b.get('styles') or {}).items():
            doc['styles'][k] = v
        doc['t'] = int(time.time() * 1000)
        self._send(200, {'ok': True, 'n': len(b.get('styles') or {})})

    def do_POST(self):
        b = self._body()
        doc = self._doc(b['slug'])
        n = str(b['n'])
        now = int(time.time() * 1000)
        if isinstance(b.get('note'), str):
            t = b['note'].strip()
            if t:
                doc['notes'][n] = {'t': t[:2000], 'at': now}
            else:
                doc['notes'].pop(n, None)
        if 'pick' in b:
            if b['pick'] == 'none':
                doc['picks'].pop(n, None)
            else:
                if b['pick'] not in PICKS:
                    return self._send(400, {'ok': False, 'error': 'בחירה לא תקינה'})
                txt = (b.get('txt') or '').strip()
                if not txt:
                    return self._send(400, {'ok': False, 'error': 'נוסח ריק'})
                doc['picks'][n] = {'p': b['pick'], 't': txt[:4000], 'at': now}
                doc['log'].append({'n': n, 'p': b['pick'], 't': txt, 'from': (b.get('from') or '')[:2], 'at': now})
        doc['t'] = now
        self._send(200, {'ok': True, 'doc': {'picks': doc['picks'], 'notes': doc['notes']}})

    def log_message(self, *a):
        pass


if __name__ == '__main__':
    HTTPServer(('127.0.0.1', int(sys.argv[1]) if len(sys.argv) > 1 else 8788), H).serve_forever()
