# -*- coding: utf-8 -*-
"""פרומפט 86 (23.11.2026): מדידת זמני ההדפסה ובדיקת זהות, על מראה מקומית של האתר החי.

הדף נטען כמו באתר (leokmei.com/<מסכת>.html?print=1...), אבל כל קובץ של leokmei.com נענה מן המראה שבדיסק
(--mirror). --engine tree מחליף בזיכרון את מנוע ההדפסה שבתוך mas.js במנוע מן העץ; live משאיר את מה שבמראה.
בקשות GET לשרת העריכות (workers.dev) עוברות; כל בקשה אחרת שאינה GET נחסמת, ושום דבר אינו נכתב לאתר.

  uv run --with playwright python -X utf8 tools/print/p86_bench.py --mirror <תיקייה> --engine tree --out res.json \
      --case "shabbat|pk=פרק חמישי|במה בהמה|tos=1"

לכל מקרה נרשמים: זמן מן הטעינה עד סוף העימוד, R.t (זמני השלבים), מספר העמודים, ופריסת העמודים (שורה-שורה:
מזהה היחידה, מקום השורה בטור, אורך הטקסט, הערות השוליים, הכותרת הרצה ומספר העמוד) להשוואת זהות.
--compare a.json b.json: משווה שתי ריצות ומדפיס את ההבדל הראשון בכל מקרה.
"""
import argparse, json, os, sys, time, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
MIME = {'.html': 'text/html; charset=utf-8', '.js': 'application/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8',
        '.json': 'application/json; charset=utf-8', '.woff2': 'font/woff2', '.otf': 'font/otf', '.svg': 'image/svg+xml',
        '.webp': 'image/webp', '.png': 'image/png'}
LAYOUT = r"""(()=>{const out=[];document.querySelectorAll('#prnout > .shp, #prnout > .pg').forEach((pe,pi)=>{const pg=pe.classList.contains('pg')?pe:pe.querySelector('.pg');
 pg.querySelectorAll(':scope > .pcol').forEach((c,ci)=>{const tx=c.querySelector('.ptx');if(!tx)return;
  const rows=[...tx.querySelectorAll(':scope > .row')].map(r=>[r.getAttribute('data-u')||'',r.style.top,r.textContent.replace(/\s+/g,' ').trim().length]);
  const fn=c.querySelector('.pfn');out.push({p:pi+1,c:ci,h:tx.style.height,rows,fn:fn?fn.textContent.replace(/\s+/g,' ').trim():''})});
 out.push({p:pi+1,hd:(pg.querySelector('.phd')||{}).textContent,num:(pg.querySelector('.pnum')||{}).textContent})});return out})()"""
ENG_MARK = '/* =================== מנוע הדפסה ל-PDF'


def tree_mas(js, eng_path):
    a = js.index(ENG_MARK); a = js.rfind('\n', 0, a) + 1
    # סוף המנוע = תחילת הקובץ הבא בשרשור (word_export.js). במנוע עצמו יש סמן "/* ====" פנימי, ולכן אין לחפש אותו
    nxt = open(os.path.join(ROOT, 'tools', 'word_export.js'), encoding='utf-8').read()[:160]
    b = js.index(nxt, a)
    if eng_path is None:
        return js[a:b]
    eng = open(eng_path, encoding='utf-8').read()
    return js[:a] + eng.rstrip('\n') + '\n' + js[b:]


def run(a):
    from playwright.sync_api import sync_playwright
    mirror = os.path.abspath(a.mirror)
    mas = open(os.path.join(mirror, 'mas.js'), encoding='utf-8').read()
    if a.engine != 'live':
        mas = tree_mas(mas, a.engine if os.path.isfile(a.engine) else os.path.join(ROOT, 'tools', 'print_engine.js'))
    mas_b = mas.encode('utf-8')
    prof_dir = os.path.join(HERE, 'profiles')
    results = []

    def handler(route):
        req = route.request
        u = urllib.parse.urlparse(req.url)
        if req.method != 'GET':
            return route.abort()
        if u.hostname not in ('leokmei.com', 'www.leokmei.com'):
            if 'workers.dev' in (u.hostname or '') and not a.offline:
                # תשובות שרת העריכות (/live, /tos) נשמרות במראה בפעם הראשונה, כדי שכל הריצות (לפני ואחרי) יראו אותו נוסח
                import hashlib
                key = hashlib.md5(req.url.encode('utf-8')).hexdigest()
                cfp = os.path.join(mirror, '_api', key)
                if os.path.exists(cfp):
                    d = json.load(open(cfp, encoding='utf-8'))
                    return route.fulfill(status=d['status'], headers={'content-type': d['ct'], 'access-control-allow-origin': '*'},
                                         body=d['body'].encode('utf-8'))
                try:
                    r = route.fetch()
                    body = r.text()
                    os.makedirs(os.path.dirname(cfp), exist_ok=True)
                    json.dump({'url': req.url, 'status': r.status, 'ct': r.headers.get('content-type', 'application/json'), 'body': body},
                              open(cfp, 'w', encoding='utf-8'), ensure_ascii=False)
                    return route.fulfill(response=r, body=body)
                except Exception:
                    return route.abort()
            return route.abort()
        path = urllib.parse.unquote(u.path).lstrip('/') or 'index.html'
        if path == 'mas.js':
            return route.fulfill(status=200, headers={'content-type': MIME['.js'], 'cache-control': 'no-store'}, body=mas_b)
        if a.engine != 'live' and path.startswith('print-profiles/'):
            fp = os.path.join(prof_dir, path.split('/', 1)[1])
        elif a.engine != 'live' and path == 'pdf-lib.min.js' and os.path.exists(os.path.join(ROOT, 'tools', 'print', 'pdf-lib.min.js')):
            fp = os.path.join(ROOT, 'tools', 'print', 'pdf-lib.min.js')
        else:
            fp = os.path.normpath(os.path.join(mirror, path))
        if not os.path.isfile(fp) and fp.startswith(mirror) and not a.offline:
            # קובץ שחסר במראה (גופן שנטען רק בהדפסה וכד') נמשך פעם אחת מן האתר החי ונשמר
            try:
                r = route.fetch()
                if r.status == 200:
                    os.makedirs(os.path.dirname(fp), exist_ok=True)
                    open(fp, 'wb').write(r.body())
            except Exception:
                pass
        if not os.path.isfile(fp):
            return route.fulfill(status=404, body=b'')
        ext = os.path.splitext(fp)[1].lower()
        route.fulfill(status=200, headers={'content-type': MIME.get(ext, 'application/octet-stream'), 'cache-control': 'no-store'},
                      body=open(fp, 'rb').read())

    with sync_playwright() as p:
        b = p.chromium.launch(args=['--font-render-hinting=none'])
        for case in a.case:
            parts = case.split('|')
            slug, qs = parts[0], {}
            rest = '|'.join(parts[1:])
            # pk מכיל "|" בעצמו: pk=<פרק>|<שם>
            for kv in rest.split('&'):
                if '=' in kv:
                    k, v = kv.split('=', 1)
                    qs[k] = v
            q = {'print': '1', 'tos': '0', 'duplex': '0', 'profile': 'a4lg'}
            q.update(qs)
            for rep_i in range(a.runs):
                ctx = b.new_context(viewport={'width': 794, 'height': 1123})
                ctx.route('**/*', handler)
                if a.admin:
                    ctx.add_init_script("try{localStorage.setItem('lg-admin','1')}catch(e){}")
                pg = ctx.new_page()
                pg.emulate_media(media='print')
                if a.svc:
                    pg.add_init_script("try{localStorage.setItem('lg-prn-svc','1')}catch(e){}")
                cdp = None
                if a.cpuprofile:
                    cdp = ctx.new_cdp_session(pg)
                    cdp.send('Profiler.enable')
                    cdp.send('Profiler.setSamplingInterval', {'interval': 500})
                    cdp.send('Profiler.start')
                errs = []
                pg.on('pageerror', lambda e: errs.append(str(e)))
                url = 'https://leokmei.com/%s.html?%s' % (slug, urllib.parse.urlencode(q))
                t0 = time.time()
                pg.goto(url, wait_until='domcontentloaded', timeout=180000)
                t_dom = time.time() - t0
                st = None
                while time.time() - t0 < a.timeout:
                    try:
                        st = pg.evaluate("window.__PRN&&window.__PRN.state")
                    except Exception:
                        st = None
                    if st in ('done', 'error', 'blocked'):
                        break
                    pg.wait_for_timeout(100)
                dt = time.time() - t0
                if cdp:
                    prof = cdp.send('Profiler.stop')['profile']
                    json.dump(prof, open(a.cpuprofile + '.%d.cpuprofile' % len(results), 'w'))
                rec = {'case': case, 'run': rep_i, 'state': st, 'sec': round(dt, 2), 'dom': round(t_dom, 2), 'errors': errs[:5]}
                try:
                    rec['t'] = pg.evaluate('window.__PRN.report&&window.__PRN.report.t')
                    rec['error'] = pg.evaluate('window.__PRN.error||null')
                    rec['t0'] = pg.evaluate('window.__PRN.report&&window.__PRN.report.t0||null')
                    rec['tm'] = pg.evaluate('window.__PRN.report&&window.__PRN.report.tm||null')
                    if st != 'done':
                        # פרומפט 86 המשך: גם בריצה שלא הסתיימה - מוני המדידה וקוד הניסוי (לאבחון מקרים שנתקעים)
                        rec['stat'] = pg.evaluate('(function(r){return r?{fn:r.fnStat||null,pooled:r.pooled,ps:r.psStat||null}:null})(window.__PRN.report)')
                        if a.eval_js:
                            rec['evalr'] = pg.evaluate(open(a.eval_js, encoding='utf-8').read())
                    if st == 'done':
                        rec['pages'] = pg.evaluate('window.__PRN.report.pages.length')
                        rec['issues'] = pg.evaluate("(window.__PRN.report.issues||[]).map(i=>i.type+'|'+i.page)")
                        rec['stat'] = pg.evaluate('(function(r){return {fn:r.fnStat||null,pooled:r.pooled,poolTight:r.poolTight,balMid:r.balMid,noteSqueeze:r.noteSqueeze,fnVerify:r.fnVerify||null,estCh:r.estCh,estTc:r.estTc}})(window.__PRN.report)')
                        if a.eval_js:
                            rec['evalr'] = pg.evaluate(open(a.eval_js, encoding='utf-8').read())
                            print('EVAL', json.dumps(rec['evalr'], ensure_ascii=False)[:3000], flush=True)
                        if rep_i == 0:
                            rec['lay'] = pg.evaluate(LAYOUT)
                            # זהות מלאה: גיבוב של כל עמוד מודפס (HTML מלא, כולל סגנונות ומיקומים)
                            import hashlib as _h
                            rec['pgh'] = [_h.md5(x.encode('utf-8')).hexdigest() for x in pg.evaluate("[...document.querySelectorAll('#prnout > .shp, #prnout > .pg')].map(e=>e.outerHTML)")]
                except Exception as e:
                    rec['exc'] = str(e)
                print(json.dumps({k: rec.get(k) for k in ('case', 'run', 'state', 'sec', 'dom', 't0', 'pages', 't', 'tm', 'stat', 'error', 'errors')}, ensure_ascii=False), flush=True)
                results.append(rec)
                ctx.close()
        b.close()
    json.dump(results, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False)


def strip(lay):
    out = []
    for x in lay or []:
        x = dict(x)
        if 'rows' in x:
            x['rows'] = [[r[1], r[2]] for r in x['rows']]
        out.append(x)
    return out


def compare(fa, fb):
    A = {r['case']: r for r in json.load(open(fa, encoding='utf-8')) if r.get('run') == 0}
    B = {r['case']: r for r in json.load(open(fb, encoding='utf-8')) if r.get('run') == 0}
    bad = 0
    for c in A:
        if c not in B:
            continue
        x, y = strip(A[c].get('lay')), strip(B[c].get('lay'))
        same = x == y and A[c].get('issues') == B[c].get('issues')
        hh = A[c].get('pgh') is not None and B[c].get('pgh') is not None
        if hh and A[c]['pgh'] != B[c]['pgh']:
            same = False
            print('   HTML שונה בעמודים', [i + 1 for i, (u, v) in enumerate(zip(A[c]['pgh'], B[c]['pgh'])) if u != v], len(A[c]['pgh']), len(B[c]['pgh']))
        rows = sum(len(e.get('rows', [])) for e in x)
        print(('זהה ' if same else 'שונה') + ' | %s | עמודים %s/%s | שורות %d | %s שנ\' -> %s שנ\'' % (
            c, A[c].get('pages'), B[c].get('pages'), rows, A[c].get('sec'), B[c].get('sec')))
        if not same:
            bad += 1
            for i, (p, q) in enumerate(zip(x, y)):
                if p != q:
                    ks = [k for k in set(p) | set(q) if p.get(k) != q.get(k)]
                    print('   הבדל ראשון: פריט', i, 'עמוד', p.get('p'), 'שדות', ks)
                    break
            if len(x) != len(y):
                print('   מספר פריטים', len(x), len(y))
            if A[c].get('issues') != B[c].get('issues'):
                print('   ממצאי הבודק שונים', A[c].get('issues'), B[c].get('issues'))
    print('תוצאה:', 'הכל זהה' if not bad else '%d מקרים שונים' % bad)
    return bad


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--mirror')
    ap.add_argument('--engine', default='tree', help='live | tree | נתיב לקובץ מנוע')
    ap.add_argument('--case', action='append', default=[])
    ap.add_argument('--runs', type=int, default=1)
    ap.add_argument('--timeout', type=int, default=900)
    ap.add_argument('--admin', action='store_true')
    ap.add_argument('--offline', action='store_true', help='בלי שרת העריכות (גם /live ו-/tos נחסמים)')
    ap.add_argument('--out', default='bench.json')
    ap.add_argument('--cpuprofile', default='', help='קידומת לקובצי פרופיל מעבד (CDP)')
    ap.add_argument('--svc', action='store_true', default=True, help='מסמן את הדף כשירות (בלי הגבלה יומית ובלי רישום)')
    ap.add_argument('--compare', nargs=2)
    ap.add_argument('--eval-js', default='', help='קוד JS שמורץ בדף אחרי שההדפסה הושלמה (ניסויים)')
    a = ap.parse_args()
    if a.compare:
        sys.exit(1 if compare(*a.compare) else 0)
    run(a)
