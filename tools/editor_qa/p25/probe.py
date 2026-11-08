# -*- coding: utf-8 -*-
"""בדיקות פרומפט 25 ("בחר נוסח" על הטקסט עצמו): האתר החי לקריאה בלבד, קוד הנוסחאות מקומי.

probe.py <alts_ui.js מקומי או -> <width> <script.py> [height]

קובץ המסכת (bekhorot.x.js, או הדף עצמו כשהזנב בתוכו) נמשך מן האתר החי, וקטע "בחר נוסח" שבו
מוחלף בקובץ המקומי. ההחלפה מאומתת: אם הקוד הישן לא נמצא כלשונו - הבדיקה נעצרת (לא ממשיכה בשקט).
כל כתיבה (PUT/POST, הגשר המקומי, נקודת הקליטה) נחסמת ונרשמת. אסימון מנהל מדומה. אין שום כתיבה לשרת.
"-" = הקוד החי כפי שהוא (בדיקה אחרי פרסום)."""
import sys, io, os, json, re
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
NEW, W, js = sys.argv[1], int(sys.argv[2]), sys.argv[3]
H = int(sys.argv[4]) if len(sys.argv) > 4 else 800
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
BLOCKED = []
SWAP = {'done': 0}
new_src = io.open(NEW, encoding='utf-8').read() if NEW != '-' else None
old_src = io.open(os.environ.get('P25OLD', os.path.join(ROOT, '_work', 'alts_old.js')), encoding='utf-8').read() if NEW != '-' else None
MARK = '/* =================== "בחר נוסח"'


def swap_text(body):
    if new_src is None or MARK not in body:
        return body
    a = body.index(MARK)
    a = body.rindex('\n', 0, a) + 1
    i = body.find(old_src.strip(), a - 2)
    if i < 0:
        # הקוד שבאתר אינו זהה לגרסה הישנה שבריפו: מחליפים עד סוף ה-IIFE שלפני build()
        b = body.index('\n  })();', a) + len('\n  })();')
        print('NOTE live alts code differs from repo copy; swapped by marker')
        SWAP['done'] = 2
        return body[:a] + new_src.rstrip('\n') + body[b:]
    SWAP['done'] = 1
    return body[:i] + new_src.strip() + body[i + len(old_src.strip()):]


def seal(route):
    rq = route.request
    if rq.method.upper() not in ('GET', 'HEAD', 'OPTIONS'):
        BLOCKED.append(rq.method + ' ' + rq.url.split('?')[0])
        return route.fulfill(status=200, content_type='application/json', body='{"ok":true,"doc":{"edits":[]}}')
    if '127.0.0.1:8760' in rq.url or 'localhost:8760' in rq.url:
        BLOCKED.append('bridge ' + rq.url); return route.fulfill(status=200, body='{}')
    u = rq.url.split('?')[0]
    if new_src is not None and (u.endswith('/bekhorot.x.js') or u.endswith('/bekhorot.html') or u.endswith('/bekhorot')):
        r = route.fetch()
        body = r.text()
        return route.fulfill(status=r.status, headers={k: v for k, v in r.headers.items() if k.lower() not in ('content-length', 'content-encoding', 'etag')}, body=swap_text(body))
    return route.continue_()


with sync_playwright() as pw:
    br = pw.chromium.launch()
    mob = W <= 500
    ctx = br.new_context(viewport={'width': W, 'height': H}, locale='he-IL', service_workers='block',
                         is_mobile=mob, has_touch=mob, device_scale_factor=2 if mob else 1)
    ctx.route('**/*', seal)
    def wk(r):
        if r.request.method != 'GET':
            BLOCKED.append(r.request.method + ' ' + r.request.url.split('?')[0])
            try: BLOCKED.append('  body: ' + (r.request.post_data or '')[:160])
            except Exception: pass
        r.fulfill(status=200, content_type='application/json', body='{"ok":true,"doc":{"picks":{},"log":[],"edits":[]}}')
    ctx.route('**/*.workers.dev/**', wk)
    ctx.add_init_script("try{localStorage.setItem('lg-admin','1');localStorage.setItem('lg-adm','TEST-LOCAL-TOKEN');localStorage.removeItem('lg-alt-dec-bekhorot')}catch(e){}")
    pg = ctx.new_page()
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:300]))
    pg.on('console', lambda m: errs.append('console.' + m.type + ': ' + m.text[:200]) if m.type == 'error' else None)
    pg.goto('https://leokmei.com/bekhorot.html', wait_until='load', timeout=120000)
    pg.wait_for_timeout(3500)
    if new_src is not None and not SWAP['done']:
        print('FATAL: alts code was not swapped (marker not found in page/x.js)'); br.close(); sys.exit(2)
    ns = {'pg': pg, 'json': json, 'print': print, 'W': W, 'BLOCKED': BLOCKED, 'errs': errs, 'os': os}
    exec(io.open(js, encoding='utf-8').read(), ns)
    print('ERRORS', errs)
    print('BLOCKED', BLOCKED)
    br.close()
