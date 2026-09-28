# -*- coding: utf-8 -*-
"""serve.py - שרת מקומי לבדיקה בלבד.

השרת המובנה של פייתון חונק קובצי מאתיים קילובייט ומעלה בסביבה הזאת,
ותשובתו נקטעת באמצע. כאן הקובץ נקרא כולו לזיכרון, נשלח בבת אחת עם
Content-Length מדויק, והחיבור נסגר - ואין קטיעה. השרת הזה אינו חלק
מן האתר ואינו מתפרסם.

    uv run python tools/serve.py [--port 8731] [--dir site]
"""
import os, sys, argparse, mimetypes, urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'site')


class H(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.0'          # בלי keep-alive: אין קטיעה

    def log_message(self, *a):
        pass

    def do_GET(self):
        p = urllib.parse.urlparse(self.path).path
        p = urllib.parse.unquote(p)
        if p.endswith('/'):
            p += 'index.html'
        full = os.path.normpath(os.path.join(ROOT, p.lstrip('/')))
        if not full.startswith(ROOT) or not os.path.isfile(full):
            self.send_error(404)
            return
        data = open(full, 'rb').read()
        ctype = mimetypes.guess_type(full)[0] or 'application/octet-stream'
        if ctype.startswith('text/') or ctype.endswith('json') or ctype.endswith('javascript'):
            ctype += '; charset=utf-8'
        self.send_response(200)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Connection', 'close')
        self.end_headers()
        # כתיבה אחת גדולה נקטעה כאן בעקביות ב-326,400 בתים. בנתחים
        # של 64 קילובייט, עם השטפה אחרי כל נתח, היא עוברת בשלמותה.
        for i in range(0, len(data), 65536):
            self.wfile.write(data[i:i + 65536])
            self.wfile.flush()


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=8731)
    ap.add_argument('--dir', default=ROOT)
    a = ap.parse_args()
    ROOT = os.path.abspath(a.dir)
    print('משרת את', ROOT, 'על', a.port)
    sys.stdout.flush()
    ThreadingHTTPServer(('127.0.0.1', a.port), H).serve_forever()
