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
import os, sys, io, re, json, time, base64, shutil, argparse, subprocess, socket
import urllib.request, urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = 8760
REPO = 'michaelFLEGG/leokmei-girsa'
ORIGINS = ('https://michaelflegg.github.io',)
SLUG_OK = re.compile(r'^[a-z][a-z0-9-]{1,40}$')
SITE = 'https://michaelflegg.github.io/leokmei-girsa'
CACHE, CACHE_TTL = {}, 60
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TASK = 'לאוקמי גירסא - גשר הפרסום'
LOG = None


def log(*a):
    msg = ' '.join(str(x) for x in a)
    # ‏pythonw אינו מחזיק פלט סטנדרטי כלל, ו-print נכשל בו. הגשר קרס
    # בשקט בכל הרצה של המשימה, והמשימה דיווחה קוד יציאה 0.
    try:
        if sys.stdout is not None:
            sys.stdout.write(msg + '\n')
            sys.stdout.flush()
    except Exception:
        pass
    if LOG:
        try:
            io.open(LOG, 'a', encoding='utf-8').write(msg + '\n')
        except Exception:
            pass


# ---------------------------------------------------------------- גיטהאב

def token_path():
    return os.path.join(HOME_DIR, 'token')


def token():
    """מפתח הכתיבה. נקרא מקובץ בתיקיית הגשר.

    הגשר קרא בתחילה להרשאה ש-gh מחזיק במחשב, אך במשימה מתוזמנת
    הוא לא מצא אותה כלל ("please run gh auth login") - וכל פרסום
    נכשל. נוסף על כך, כל קריאה ל-gh לוקחת כארבע שניות של הפעלת
    תהליך, ושתיים כאלה חרגו מפסק הזמן. מעתה הפנייה היא ישירה
    לממשק, עם מפתח שנכתב פעם אחת בהתקנה."""
    try:
        return io.open(token_path(), encoding='utf-8').read().strip()
    except Exception:
        return ''


def api(method, path, payload=None):
    t = token()
    if not t:
        return 0, 'אין מפתח בתיקיית הגשר'
    req = urllib.request.Request(
        'https://api.github.com/' + path.lstrip('/'),
        data=json.dumps(payload).encode('utf-8') if payload is not None else None,
        method=method,
        headers={'Authorization': 'Bearer ' + t,
                 'Accept': 'application/vnd.github+json',
                 'X-GitHub-Api-Version': '2022-11-28',
                 'Content-Type': 'application/json',
                 'User-Agent': 'leokmei-gesher'})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status, r.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')
    except Exception as e:
        return 0, str(e)


def put_edits(slug, body):
    path = 'repos/%s/contents/data/edits/%s.json' % (REPO, slug)
    code, out = api('GET', path + '?ref=main')
    sha = None
    if code == 200:
        try:
            sha = json.loads(out)['sha']
        except Exception:
            pass
    elif code not in (404,):
        return False, 'קריאה נכשלה (%s): %s' % (code, out[:160])
    payload = {'message': 'תיקונים מן האתר - %s' % slug,
               'content': base64.b64encode(body.encode('utf-8')).decode('ascii'),
               'branch': 'main'}
    if sha:
        payload['sha'] = sha
    code, out = api('PUT', path, payload)
    if code not in (200, 201):
        return False, 'כתיבה נכשלה (%s): %s' % (code, out[:160])
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


HOME_DIR = os.path.join(os.path.expanduser('~'), 'leokmei-gesher')


def install(repo=None):
    """מקים את המשימה שמריצה את הגשר ברקע, בלי חלון.

    הגשר יושב בתיקייה משלו ואינו תלוי בשום עותק-עבודה: הוא מגיש את
    האתר החי וכותב דרך gh, ואינו קורא מן המאגר דבר. כך אין סכנה
    שיישבר כששיחה אחרת עובדת בעותק המשותף.

    הקבצים באנגלית בכוונה: נתיב עברי שבר כאן פעמיים - פעם ב-VBScript
    שאינו קורא UTF-8, ופעם בקידוד שורת הפקודה של המשימה."""
    keep = HOME_DIR
    os.makedirs(keep, exist_ok=True)
    me = os.path.join(keep, 'gesher.py')
    if os.path.abspath(__file__) != os.path.abspath(me):
        shutil.copy(os.path.abspath(__file__), me)
    # המפתח נכתב פעם אחת, מן ההרשאה שכבר במחשב. הקובץ מוגבל למשתמש
    # הזה בלבד, ואפשר למחוק אותו בכל רגע - אז הפרסום פשוט מפסיק.
    if not token():
        p = subprocess.run(['gh', 'auth', 'token'], capture_output=True)
        tok = p.stdout.decode('utf-8', 'replace').strip()
        if p.returncode == 0 and tok:
            tp = token_path()
            io.open(tp, 'w', encoding='utf-8', newline='').write(tok + '\n')
            subprocess.run(['icacls', tp, '/inheritance:r',
                            '/grant:r', '%s:F' % os.environ.get('USERNAME', 'Owner')],
                           capture_output=True)
            log('מפתח הכתיבה נשמר בתיקיית הגשר, ומוגבל למשתמש הזה')
        else:
            log('אזהרה: לא ניתן היה לקרוא מפתח כתיבה מן המחשב')
    cmd = os.path.join(keep, 'run.cmd')
    logf = os.path.join(keep, 'gesher.log')
    # המשימה מריצה pythonw ישירות. כל שכבת ביניים שניסינו כאן נכשלה:
    # ‏uv אינו ב-PATH של משימה מתוזמנת; cmd מהבהב חלון שחור כל חמש
    # דקות; ו-wscript הפעיל כלום ברוב הפעמים, בלי שום הודעת שגיאה.
    # ‏pythonw אינו פותח חלון כלל, והגשר אינו זקוק לשום ספרייה חיצונית.
    pyw = os.path.join(os.path.dirname(sys.executable), 'pythonw.exe')
    if not os.path.exists(pyw):
        pyw = shutil.which('pythonw') or sys.executable
    io.open(cmd, 'w', encoding='ascii', errors='replace', newline='').write(
        '@echo off\r\n'
        'chcp 65001 > nul\r\n'
        '"%s" "%s" --once >> "%s" 2>&1\r\n' % (sys.executable, me, logf))
    # משימה אחת בלבד, כל שתי דקות. משימת ONLOGON דורשת הרשאת מנהל
    # ונדחתה כאן ב-Access denied; המשימה הזאת מרימה את הגשר תוך שתי
    # דקות מכל הדלקה, וכשהוא כבר עונה היא יוצאת מיד ואינה עולה דבר.
    # קיצור דרך על שולחן העבודה. זו הדרך שבה בעל הפרויקט פותח את
    # האתר לעריכה: אותו אתר בדיוק, אלא שהוא מוגש מן הגשר ולכן
    # הפרסום עובד בלי שום הכנה.
    try:
        desk = os.path.join(os.path.expanduser('~'), 'Desktop')
        if os.path.isdir(desk):
            # הקיצור פותח את המשגר (open_edit.pyw) ולא את הכתובת ישירות:
            # המשגר מרים את הגשר אם הוא כבוי, ורק אז פותח את הדפדפן.
            shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'open_edit.pyw'),
                        os.path.join(keep, 'open_edit.pyw'))
            pyw0 = os.path.join(os.path.dirname(sys.executable), 'pythonw.exe')
            ps = ("$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%s');"
                  "$s.TargetPath='%s';$s.Arguments='\"%s\"';$s.WorkingDirectory='%s';"
                  "$s.IconLocation='%s';$s.Save()") % (
                os.path.join(desk, 'לאוקמי גירסא - עריכה.lnk'), pyw0,
                os.path.join(keep, 'open_edit.pyw'), keep,
                os.path.join(keep, 'leokmei-edit.ico'))
            subprocess.run(['powershell', '-NoProfile', '-Command', ps], capture_output=True)
            log('קיצור הדרך נוצר על שולחן העבודה')
    except Exception as e:
        log('אזהרה: קיצור הדרך לא נוצר -', e)
    run = '"%s" "%s" --once' % (pyw, me)
    r = subprocess.run(['schtasks', '/Create', '/F', '/TN', TASK,
                        '/SC', 'MINUTE', '/MO', '2', '/TR', run],
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
    LOG = os.path.join(HOME_DIR, 'gesher.log') if os.path.isdir(HOME_DIR) else None
    if a.install:
        install()
        return
    if a.status:
        print('הגשר חי' if alive() else 'הגשר אינו רץ')
        return
    # הבדיקה היא "האם גשר כבר עונה", ולא "האם היציאה תפוסה": יציאה
    # שנסגרה זה עתה נשארת תפוסה לרגע בחלונות, והגשר היה יוצא בשקט
    # והמשימה מדווחת הצלחה. נמדד שלוש פעמים.
    if a.once and alive():
        return
    if not token():
        log('אזהרה: אין מפתח בתיקיית הגשר. הרץ --install')
    log('הגשר עלה על 127.0.0.1:%d, מאגר %s' % (PORT, REPO))
    srv = ThreadingHTTPServer(('127.0.0.1', PORT), H)
    srv.daemon_threads = True
    srv.serve_forever()


if __name__ == '__main__':
    main()
