# -*- coding: utf-8 -*-
"""מפיק קובץ PDF של לאוקמי גירסא מן מנוע ההדפסה שבדף המסכת.

הרצה (תמיד דרך uv):
  uv run --with playwright python tools/print/render_pdf.py \
      --site <תיקיית האתר הבנוי> --slug kiddushin --from "יד:" --to "טז:" --tos 1 --out out.pdf

הדפדפן הוא Chromium אחד קבוע, ולכן התוצאה זהה בכל מכשיר. קובצי האתר מוגשים ישירות מן התיקייה
(בלי שרת): כל בקשה לכתובת print.local נענית מן הדיסק, עם ניסיונות חוזרים (האנטי-וירוס נועל קבצים לרגע).
--dev: מזריק את print_engine.js ואת הפרופילים מן העץ הנוכחי אל דף שנבנה קודם (בדיקה בלי בנייה מלאה).
"""
import argparse, glob, json, mimetypes, os, sys, time, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
ENGINE = os.path.join(ROOT, 'tools', 'print_engine.js')
PROFILES = os.path.join(HERE, 'profiles')
HOST = 'print.local'
MIME = {'.html': 'text/html; charset=utf-8', '.js': 'application/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8',
        '.json': 'application/json; charset=utf-8', '.woff2': 'font/woff2', '.otf': 'font/otf', '.ttf': 'font/ttf',
        '.svg': 'image/svg+xml', '.webp': 'image/webp', '.png': 'image/png', '.jpg': 'image/jpeg', '.ico': 'image/x-icon'}


def read_retry(path, tries=8):
    last = None
    for i in range(tries):
        try:
            with open(path, 'rb') as f:
                return f.read()
        except OSError as e:
            last = e
            time.sleep(0.15 * (i + 1))
    raise last


def patched_mas(site):
    """mas.js (הקוד המשותף) עם מנוע ההדפסה העדכני מן העץ: מחליפים את העותק שנבנה בו, אם יש."""
    js = read_retry(os.path.join(site, 'mas.js')).decode('utf-8')
    eng = open(ENGINE, encoding='utf-8').read()
    mk = '/* =================== מנוע הדפסה ל-PDF'
    s0 = js.find(mk)
    if s0 >= 0:
        s0 = js.rfind('\n', 0, s0) + 1
        return (js[:s0] + eng + '\n').encode('utf-8')
    return (js.rstrip() + '\n' + eng + '\n').encode('utf-8')


def patched_tail(site, slug, tos_dir):
    """<מסכת>.x.js עם נתוני התוספות העדכניים מן העץ (האתר הבנוי עשוי להיות ישן מקובץ ה-live)."""
    fp = os.path.join(site, slug + '.x.js')
    js = read_retry(fp).decode('utf-8') if os.path.exists(fp) else ''
    items = []
    for lf in sorted(glob.glob(os.path.join(tos_dir, slug, 'live-*.json'))):
        items += json.load(open(lf, encoding='utf-8')).get('items', [])
    j = js.find('window.__TOS=')
    if items and j >= 0:
        _, e = json.JSONDecoder().raw_decode(js[j + len('window.__TOS='):])
        js = (js[:j] + 'window.__TOS=' + json.dumps({'slug': slug, 'items': items}, ensure_ascii=False, separators=(',', ':'))
              + js[j + len('window.__TOS=') + e:])
    return js.encode('utf-8')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--site', required=True)
    ap.add_argument('--slug', required=True)
    ap.add_argument('--from', dest='frm', default='')
    ap.add_argument('--to', default='')
    ap.add_argument('--all', action='store_true')
    ap.add_argument('--tos', default='1')
    ap.add_argument('--duplex', default='0')
    ap.add_argument('--profile', default='a4')
    ap.add_argument('--out', required=True)
    ap.add_argument('--dev', action='store_true')
    ap.add_argument('--tos-dir', default=os.path.join(ROOT, 'tosafot'), help='תיקיית נתוני התוספות (live-*.json) לבדיקה')
    ap.add_argument('--no-pdf', action='store_true')
    ap.add_argument('--report', default='', help='נתיב קובץ הדוח (JSON); בלעדיו הדוח נכתב ליד הקובץ')
    a = ap.parse_args()
    from playwright.sync_api import sync_playwright

    q = {'print': '1', 'tos': a.tos, 'duplex': a.duplex, 'profile': a.profile}
    if a.all:
        q['all'] = '1'
    else:
        q['from'] = a.frm
        q['to'] = a.to or a.frm
    url = 'http://%s/%s.html?%s' % (HOST, a.slug, urllib.parse.urlencode(q))
    t0 = time.time()
    logs = []
    site = os.path.abspath(a.site)

    def handler(route):
        req = route.request
        u = urllib.parse.urlparse(req.url)
        if u.hostname != HOST:
            # נקודת הקליטה של נוסחי התוספות מותרת; כל השאר (ניתוח גלישה וכד') נחסם
            if 'workers.dev' in (u.hostname or ''):
                return route.continue_()
            return route.abort()
        path = urllib.parse.unquote(u.path).lstrip('/')
        try:
            if a.dev and path == 'mas.js':
                return route.fulfill(status=200, headers={'content-type': MIME['.js']}, body=patched_mas(site))
            if a.dev and path == a.slug + '.x.js':
                return route.fulfill(status=200, headers={'content-type': MIME['.js']}, body=patched_tail(site, a.slug, a.tos_dir))
            if a.dev and path.startswith('print-profiles/'):
                body = read_retry(os.path.join(PROFILES, path.split('/', 1)[1]))
                return route.fulfill(status=200, headers={'content-type': MIME['.json']}, body=body)
            if a.dev and path == 'print-page2.html':
                return route.fulfill(status=200, headers={'content-type': MIME['.html']}, body=read_retry(os.path.join(HERE, 'page2.html')))
            if a.dev and path == 'print-qr.js':
                return route.fulfill(status=200, headers={'content-type': MIME['.js']}, body=read_retry(os.path.join(HERE, 'qrcode.js')))
            fp = os.path.normpath(os.path.join(site, path))
            if not fp.startswith(site) or not os.path.isfile(fp):
                logs.append('404: ' + path)
                return route.fulfill(status=404, body=b'')
            ext = os.path.splitext(fp)[1].lower()
            route.fulfill(status=200, headers={'content-type': MIME.get(ext) or mimetypes.guess_type(fp)[0] or 'application/octet-stream',
                                                'cache-control': 'no-store'}, body=read_retry(fp))
        except Exception as e:
            logs.append('שגיאת קובץ %s: %s' % (path, e))
            route.fulfill(status=500, body=b'')

    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={'width': 794, 'height': 1123})
        ctx.route('**/*', handler)
        page = ctx.new_page()
        page.on('console', lambda m: logs.append('%s: %s' % (m.type, m.text)))
        page.on('pageerror', lambda e: logs.append('pageerror: %s' % e))
        page.goto(url, wait_until='domcontentloaded', timeout=180000)
        page.wait_for_function("window.__PRN && (window.__PRN.state==='done' || window.__PRN.state==='error')", timeout=600000)
        st = page.evaluate('window.__PRN.state')
        rep = page.evaluate('window.__PRN.report')
        if st != 'done':
            print('שגיאה:', page.evaluate('window.__PRN.error'))
            print('\n'.join(logs[-12:]))
            b.close()
            sys.exit(2)
        if not a.no_pdf:
            page.evaluate('document.fonts.ready')
            rep['dom'] = page.evaluate("({pg: document.querySelectorAll('.pg').length, txt: (document.querySelector('.pg')||{}).innerText ? document.querySelector('.pg').innerText.length : 0, "
                                       "body: [].map.call(document.body.children, e => e.tagName + '#' + e.id + ':' + getComputedStyle(e).display).slice(0, 40)})")
            page.evaluate('new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))')
            page.wait_for_timeout(400)
            page.emulate_media(media='print')
            page.pdf(path=a.out, prefer_css_page_size=True, print_background=True)
        b.close()
    rep['seconds'] = round(time.time() - t0, 1)
    rep['console'] = [l for l in logs if not l.startswith('log:')][-15:]
    print(json.dumps({k: rep[k] for k in ('cols', 'lines', 'notes', 'placed', 'moved', 'warn', 'issues', 'loneFixed',
                                          'msSqueeze', 'glued', 'semicolons', 'msMeasure', 't', 'seconds') if k in rep}, ensure_ascii=False))
    json.dump(rep, open(a.report or (a.out + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('pages=%d  out=%s' % (len(rep['pages']), a.out))


if __name__ == '__main__':
    main()
