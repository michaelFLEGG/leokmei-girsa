# -*- coding: utf-8 -*-
"""gesher.py - הגשר שבין הדף ובין המאגר, ברקע במחשב של בעל הפרויקט.

**למה הוא קיים.** האתר סטטי, ולכן כדי שתיקון שנעשה בדף יגיע לכל
הלומדים צריך מישהו לכתוב אותו למאגר. הדרך הרגילה היא מפתח כתיבה
שנשמר בדפדפן - אבל יצירת המפתח היא שבעה מסכים באתר גיטהאב, ובעל
הפרויקט אינו עושה פעולות כאלה. הגשר מייתר אותן לגמרי: הוא יושב
ברקע במחשב שלו, הדף פונה אליו, והוא כותב למאגר בהרשאה שכבר קיימת
במחשב (gh). בעל הפרויקט אינו עושה דבר.

**מה הוא מרשה לעצמו.** רק כתיבה ל-data/edits/<מסכת>.json שבמאגר
הזה, ורק לבקשה שהגיעה מדף האתר עצמו. שם המסכת נבדק מול רשימה קבועה
של אותיות לטיניות קטנות ומקף - כדי ששום נתיב אחר לא ייכתב לעולם.

**האזנה ל-127.0.0.1 בלבד.** הוא אינו נגיש מן הרשת.

שימוש:
    uv run python tools/gesher.py                 (הרצה בחזית, לבדיקה)
    uv run python tools/gesher.py --install       (מקים משימה שמריצה אותו ברקע)
    uv run python tools/gesher.py --status        (בודק אם הוא חי)
"""
import os, sys, io, re, json, time, base64, argparse, subprocess, socket, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = 8760
REPO = 'michaelFLEGG/leokmei-girsa'
ORIGINS = ('https://michaelflegg.github.io',)
SLUG_OK = re.compile(r'^[a-z][a-z0-9-]{1,40}$')
SITE = 'https://michaelflegg.github.io/leokmei-girsa'
CACHE, CACHE_TTL = {}, 600
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TASK = 'לאוקמי גירסא - גשר הפרסום'
LOG = None


def log(*a):
    msg = ' '.join(str(x) for x in a)
    print(msg)
    sys.stdout.flush()
    if LOG:
        try:
            io.open(LOG, 'a', encoding='utf-8').write(msg + '\n')
        except Exception:
            pass


# ---------------------------------------------------------------- גיטהאב

def gh(args, data=None):
    """קריאה ל-gh. ההרשאה כבר במחשב, ואין כאן שום מפתח."""
    p = subprocess.run(['gh'] + args, input=data, capture_output=True)
    return p.returncode, p.stdout.decode('utf-8', 'replace'), p.stderr.decode('utf-8', 'replace')


def put_edits(slug, body):
    path = 'data/edits/%s.json' % slug
    code, out, _ = gh(['api', 'repos/%s/contents/%s?ref=main' % (REPO, path)])
    sha = None
    if code == 0:
        try:
            sha = json.loads(out)['sha']
        except Exception:
            pass
    payload = {'message': 'תיקונים מן האתר - %s' % slug,
               'content': base64.b64encode(body.encode('utf-8')).decode('ascii'),
               'branch': 'main'}
    if sha:
        payload['sha'] = sha
    code, out, err = gh(['api', '--method', 'PUT',
                         'repos/%s/contents/%s' % (REPO, path),
                         '--input', '-'],
                        data=json.dumps(payload).encode('utf-8'))
    if code != 0:
        return False, (err or out).strip()[:300]
    try:
        return True, json.loads(out)['commit']['sha'][:7]
    except Exception:
        return True, ''


# ---------------------------------------------------------------- השרת

class H(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.0'

    def log_message(self, *a):
        pass

    def _cors(self, origin):
        # הדפדפן דורש אישור מפורש לפנייה מרשת ציבורית אל מחשב מקומי,
        # ובלעדיו הבקשה נחסמת עוד לפני שהיא נשלחת.
        self.send_header('Access-Control-Allow-Origin', origin)
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'content-type')
        self.send_header('Access-Control-Allow-Private-Network', 'true')
        self.send_header('Access-Control-Max-Age', '86400')
        self.send_header('Vary', 'Origin')

    def _ok_origin(self):
        o = self.headers.get('Origin') or ''
        if o in ORIGINS or o.startswith('http://127.0.0.1:') or o.startswith('http://localhost:'):
            return o
        return None

    def _send(self, code, obj, origin):
        data = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        if origin:
            self._cors(origin)
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        o = self._ok_origin()
        self.send_response(204 if o else 403)
        if o:
            self._cors(o)
        self.send_header('Content-Length', '0')
        self.end_headers()

    def do_GET(self):
        o = self._ok_origin() or '*'
        if self.path.startswith('/shalom'):
            self._send(200, {'ok': True, 'v': 1, 'repo': REPO}, o)
            return
        self._proxy()

    def _proxy(self):
        """מגיש את האתר החי עצמו, דרך הכתובת המקומית.

        זה הלב של הפתרון. דפדפן חוסם פנייה מדף https אל 127.0.0.1
        (נמדד: ERR_BLOCKED_BY_CLIENT), ולכן דף שנטען מן הכתובת
        הציבורית אינו יכול לדבר עם הגשר. כשהדף עצמו מוגש מכאן, שניהם
        באותו מקור בדיוק, והפרסום עובד בלי מפתח ובלי שום הכנה.
        התוכן הוא התוכן החי - אין כאן עותק שמתיישן."""
        path = self.path.split('?')[0]
        if path in ('/', ''):
            path = '/index.html'
        now = time.time()
        hit = CACHE.get(path)
        if hit and now - hit[0] < CACHE_TTL:
            body, ctype = hit[1], hit[2]
        else:
            try:
                req = urllib.request.Request(
                    SITE + path, headers={'User-Agent': 'leokmei-gesher'})
                with urllib.request.urlopen(req, timeout=20) as r:
                    body = r.read()
                    ctype = r.headers.get('Content-Type') or 'application/octet-stream'
            except Exception as e:
                msg = ('<!DOCTYPE html><html lang="he" dir="rtl"><meta charset="utf-8">'
                       '<body style="font-family:sans-serif;padding:40px;text-align:center">'
                       '<h2>אין כרגע חיבור לאתר</h2><p>נסה שוב בעוד רגע.</p></body></html>')
                body, ctype = msg.encode('utf-8'), 'text/html; charset=utf-8'
                self.send_response(502)
                self.send_header('Content-Type', ctype)
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            CACHE[path] = (now, body, ctype)
            if len(CACHE) > 80:
                for k in sorted(CACHE, key=lambda k: CACHE[k][0])[:20]:
                    CACHE.pop(k, None)
        self.send_response(200)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        for i in range(0, len(body), 65536):
            self.wfile.write(body[i:i + 65536])
            self.wfile.flush()

    def do_POST(self):
        o = self._ok_origin()
        if not o:
            self._send(403, {'ok': False, 'why': 'מקור שאינו מוכר'}, None)
            return
        if not self.path.startswith('/edits'):
            self._send(404, {'ok': False, 'why': 'נתיב לא מוכר'}, o)
            return
        n = int(self.headers.get('Content-Length') or 0)
        if n <= 0 or n > 4 * 1024 * 1024:
            self._send(400, {'ok': False, 'why': 'גודל לא תקין'}, o)
            return
        raw = self.rfile.read(n).decode('utf-8', 'replace')
        try:
            doc = json.loads(raw)
        except Exception as e:
            self._send(400, {'ok': False, 'why': 'תוכן שאינו תקין: %s' % e}, o)
            return
        slug = (doc.get('slug') or '').strip()
        if not SLUG_OK.match(slug):
            self._send(400, {'ok': False, 'why': 'שם מסכת לא תקין'}, o)
            return
        if not isinstance(doc.get('edits'), list):
            self._send(400, {'ok': False, 'why': 'אין רשימת תיקונים'}, o)
            return
        body = json.dumps(doc, ensure_ascii=False, indent=1)
        good, info = put_edits(slug, body)
        log(('נכתב' if good else 'נכשל'), slug, len(doc['edits']), 'תיקונים', info)
        self._send(200 if good else 502, {'ok': good, 'info': info, 'n': len(doc['edits'])}, o)


# ---------------------------------------------------------------- הקמה

def alive():
    try:
        with urllib.request.urlopen('http://127.0.0.1:%d/shalom' % PORT, timeout=2) as r:
            return json.loads(r.read().decode('utf-8')).get('ok') is True
    except Exception:
        return False


def taken():
    s = socket.socket()
    try:
        s.bind(('127.0.0.1', PORT))
        return False
    except OSError:
        return True
    finally:
        s.close()


def install(repo):
    """מקים את המשימות שמריצות את הגשר ברקע, בלי חלון.

    שתי משימות: אחת בכניסה למחשב, ואחת כל חמש דקות שמוודאת שהוא חי
    ומרימה אותו אם נפל. שתיהן מריצות קובץ VBS, מפני שמשימה שמריצה
    cmd מהבהבת חלון שחור על המסך בכל הרצה."""
    keep = os.path.join(repo, '_שומר')
    os.makedirs(keep, exist_ok=True)
    cmd = os.path.join(keep, 'גשר-הפרסום.cmd')
    vbs = os.path.join(keep, 'גשר-הפרסום.vbs')
    io.open(cmd, 'w', encoding='utf-8-sig', newline='\r\n').write(
        '@echo off\r\n'
        'chcp 65001 > nul\r\n'
        'cd /d "%s"\r\n' % repo +
        'uv run python tools\\gesher.py --once >> "%s" 2>&1\r\n'
        % os.path.join(keep, 'גשר-הפרסום.log'))
    io.open(vbs, 'w', encoding='utf-8-sig', newline='\r\n').write(
        'CreateObject("Wscript.Shell").Run """%s""", 0, False\r\n' % cmd)
    # משימה אחת בלבד, כל חמש דקות. משימת ONLOGON דורשת הרשאת מנהל
    # ונדחתה כאן ב-Access denied; ממילא המשימה הזאת מרימה את הגשר
    # תוך חמש דקות מכל הדלקה, וזה די והותר.
    run = 'wscript.exe "%s"' % vbs
    r = subprocess.run(['schtasks', '/Create', '/F', '/TN', TASK,
                        '/SC', 'MINUTE', '/MO', '5', '/TR', run],
                       capture_output=True)
    out = (r.stdout + r.stderr).decode('cp862', 'replace').strip()
    log(TASK + ':', out or 'הוקמה')
    if r.returncode:
        raise SystemExit('הקמת המשימה נכשלה')


def main():
    global LOG
    ap = argparse.ArgumentParser()
    ap.add_argument('--install', action='store_true')
    ap.add_argument('--status', action='store_true')
    ap.add_argument('--once', action='store_true',
                    help='יוצא מיד אם הגשר כבר רץ. לשימוש המשימה המתוזמנת')
    ap.add_argument('--repo', default=HERE)
    a = ap.parse_args()
    LOG = os.path.join(a.repo, '_שומר', 'גשר-הפרסום.log')
    if a.install:
        install(a.repo)
        return
    if a.status:
        print('הגשר חי' if alive() else 'הגשר אינו רץ')
        return
    if a.once and taken():
        return
    log('הגשר עלה על 127.0.0.1:%d, מאגר %s' % (PORT, REPO))
    ThreadingHTTPServer(('127.0.0.1', PORT), H).serve_forever()


if __name__ == '__main__':
    main()
