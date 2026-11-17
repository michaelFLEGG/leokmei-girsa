# -*- coding: utf-8 -*-
"""מפיק קובץ PDF של לאוקמי גירסא מן מנוע ההדפסה שבדף המסכת.

הרצה (תמיד דרך uv):
  uv run --with playwright python tools/print/render_pdf.py \
      --site <תיקיית האתר הבנוי> --slug kiddushin --from "יד:" --to "טז:" --tos 1 --out out.pdf

הדפדפן הוא Chromium אחד קבוע, ולכן התוצאה זהה בכל מכשיר. קובצי האתר מוגשים ישירות מן התיקייה
(בלי שרת): כל בקשה לכתובת print.local נענית מן הדיסק, עם ניסיונות חוזרים (האנטי-וירוס נועל קבצים לרגע).
--dev: מזריק את print_engine.js ואת הפרופילים מן העץ הנוכחי אל דף שנבנה קודם (בדיקה בלי בנייה מלאה).
"""
import argparse, collections, glob, json, mimetypes, os, sys, time, urllib.parse

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
        # כמו הבנייה (build_site.py): "הדרן עלך" אינו הערת תוס'
        items += [x for x in json.load(open(lf, encoding='utf-8')).get('items', []) if not str(x.get('dh', '')).strip().startswith('הדרן')]
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
    ap.add_argument('--pk', default='', help='מפתח הפרק כמו בחלון ההדפסה ("פרק שלישי|כירה"): הדפסת פרק שלם')
    ap.add_argument('--tos', default='1')
    ap.add_argument('--duplex', default='0')
    ap.add_argument('--profile', default='a4')
    ap.add_argument('--holefix', default='1', help='0: בלי פיצול הערות ומתיחה (מדידת "לפני" בבקרת החורים)')
    ap.add_argument('--out', required=True)
    ap.add_argument('--lines', action='store_true', help='פרומפט 41: רישום השורות של כל פסקה בדוח (plines), למחולל "שורה שהתארכה"')
    ap.add_argument('--ovapply', default='', help='פרומפט 41, בדיקה בלבד: קובץ data/overflow/<מסכת>.json - מחיל בזיכרון את ההצעה הראשונה של כל שורה')
    ap.add_argument('--sq25', default='1', help='0: בלי כלי 1 (הצרה עד 2.5%%), למדידת לפני/אחרי')
    ap.add_argument('--dev', action='store_true')
    ap.add_argument('--tos-dir', default=os.path.join(ROOT, 'tosafot'), help='תיקיית נתוני התוספות (live-*.json) לבדיקה')
    ap.add_argument('--no-pdf', action='store_true')
    ap.add_argument('--probe', default='', help='קובץ JS לבדיקת ה-DOM אחרי העימוד (אבחון); התוצאה מודפסת')
    ap.add_argument('--report', default='', help='נתיב קובץ הדוח (JSON); בלעדיו הדוח נכתב ליד הקובץ')
    a = ap.parse_args()
    from playwright.sync_api import sync_playwright

    q = {'print': '1', 'tos': a.tos, 'duplex': a.duplex, 'profile': a.profile}
    if a.holefix == '0':
        q['holefix'] = '0'
    # פרומפט 49 חלק 0: יש מרשם של הכרעות "שורה שהתארכה" למסכת - רושמים את השורות כדי לבדוק אותן בסוף
    keep_fp = os.path.join(ROOT, 'data', 'overflow', 'keep', a.slug + '.json')
    if a.lines or os.path.exists(keep_fp):
        q['lines'] = '1'
    if a.sq25 == '0':
        q['sq25'] = '0'
    if a.all:
        q['all'] = '1'
    else:
        q['from'] = a.frm
        q['to'] = a.to or a.frm
        if a.pk:
            q['pk'] = a.pk
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
                body = patched_tail(site, a.slug, a.tos_dir)
                if a.ovapply:
                    ov, m = json.load(open(a.ovapply, encoding='utf-8')), {}
                    for it in ov['items']:
                        if it['sug']:
                            s0 = it['sug'][0]
                            m.setdefault(str(it['u']), {})[str(it['li'])] = s0['parts'] if s0['kind'] == 'split' else [s0['html']]
                    body += ('\nwindow.__OVAPPLY=' + json.dumps(m, ensure_ascii=False) + ';\n').encode('utf-8')
                return route.fulfill(status=200, headers={'content-type': MIME['.js']}, body=body)
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
        # PRINT_CHROMIUM: נתיב לדפדפן מותקן (כשגרסת playwright אינה תואמת לדפדפן שבמחשב)
        # 14.11.2026: בלי הדגל הזה Chromium מעגל את רוחב כל אות לפיקסל שלם (hinting) ומציב כך את האותיות
        # בקובץ. באותיות קטנות (הסבר, תוספות) זה יצר רווחים לא אחידים בתוך המילים: חלק מן האותיות
        # צמודות וחלקן מרוחקות. עם hinting=none הרוחבים הם הרוחבים האמיתיים של הגופן.
        b = p.chromium.launch(executable_path=os.environ.get('PRINT_CHROMIUM') or None,
                              args=['--font-render-hinting=none'])
        ctx = b.new_context(viewport={'width': 794, 'height': 1123})
        ctx.route('**/*', handler)
        page = ctx.new_page()
        # העימוד נמדד באותה מדיה שבה הקובץ מופק (כמו ב-Worker): מדידה במסך והפקה בהדפסה נתנו גבהים שונים
        page.emulate_media(media='print')
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
        if a.probe:
            page.emulate_media(media='print')
            # בדיקת DOM אחרי העימוד (אבחון): מדפיס את תוצאת הסקריפט
            print('PROBE', json.dumps(page.evaluate(open(a.probe, encoding='utf-8').read()), ensure_ascii=False))
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
                                          'msSqueeze', 'glued', 'semicolons', 'sq25', 'keepAbs', 'ovApplied', 'msMeasure', 'splits', 'stretched', 't', 'seconds') if k in rep}, ensure_ascii=False))
    json.dump(rep, open(a.report or (a.out + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('pages=%d  out=%s' % (len(rep['pages']), a.out))
    # בודק החפיפות (14.10.2026): חפיפה או חריגה מהשוליים = כשל, אין קובץ "תקין"
    ov, bd = rep.get('overlaps') or [], rep.get('bounds') or []
    ist = collections.Counter(x.get('type') for x in rep.get('issues') or [])
    print('חפיפות=%d  חריגות_שוליים=%d  ציון_דף_צמוד=%d  כותרת_בלי_רווח=%d' % (len(ov), len(bd), ist['סימן דף קרוב משלוש אותיות לטקסט'], ist['כותרת בלי רווח לפניה']))
    if rep.get('shrink'):
        print('הקטנה:', json.dumps(rep['shrink'], ensure_ascii=False))
    # בקרת החורים (פרומפט 16): טור עם ריק של יותר משורה וחצי (חוץ מסוף פרק). אזהרה, לא כשל
    holes = rep.get('holes') or []
    print('חורים_בטור=%d  הערות_מפוצלות=%d  טורים_שנמתחו=%d' % (len(holes), rep.get('splits', 0), rep.get('stretched', 0)))
    for h in holes[:30]:
        print('  חור: עמוד %s, טור %s (%s): %s שורות%s' % (h['page'], h['col'], h['daf'], h['lines'], (' - ' + h['why']) if h.get('why') else ''))
    for o in ov[:20]:
        print('  חפיפה: עמוד %s (%s): %s <> %s (%s מ"מ)' % (o['page'], o['daf'], o['a'], o['b'], o['mm']))
    for o in bd[:20]:
        print('  חריגה: עמוד %s (%s): %s - %s' % (o['page'], o['daf'], o['el'], o['why']))
    hm = rep.get('headMulti') or {}
    print('כותרות_ביותר_משורה: לפני=%s  אחרי=%s  (הוצרו=%s, נשברו_במקום_הנכון=%s)' % (hm.get('before', 0), hm.get('after', 0), hm.get('squeezed', 0), hm.get('broken', 0)))
    ce = [x for x in rep.get('issues') or [] if x.get('type') == 'סוף פרק לא מאוזן']
    print('סופי_פרק_מאוזנים=%s  סוף_פרק_לא_מאוזן=%d' % (rep.get('perekBalanced', 0), len(ce)))
    for o in ce[:20]:
        print('  סוף פרק לא מאוזן: עמוד %s (%s): %s' % (o.get('page'), o.get('daf'), o.get('detail')))
    # פרומפט 48 סבב ג: העמוד הראשון פותח במשהו מחוץ לטווח (שורת "המשך", דף אחר, תוספות מדף אחר) - עוצר
    oo = [x for x in rep.get('issues') or [] if x.get('type') == 'פתיחה מחוץ לטווח']
    print('פתיחה_מחוץ_לטווח=%d' % len(oo))
    for o in oo[:20]:
        print('  פתיחה מחוץ לטווח: %s' % o.get('detail'))
    # פרומפט 49 חלק 0: כל הכרעת "שורה שהתארכה" שבמרשם - בשורה אחת. שורה שחסרה או נשברה עוצרת את המסירה
    kb = 0
    if os.path.exists(keep_fp):
        sys.path.insert(0, os.path.join(ROOT, 'tools', 'overflow'))
        import keep as KEEP
        kb = KEEP.check(a.slug, a.report or (a.out + '.json'), partial=not a.all)
    # פרומפט 48: סוף פרק לא מאוזן עוצר את המסירה, כמו חפיפה
    if ov or bd or ce or oo or kb:
        sys.exit(3)


if __name__ == '__main__':
    main()
