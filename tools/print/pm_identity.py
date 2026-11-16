# -*- coding: utf-8 -*-
"""בדיקת זהות למצב הדפוס (פרומפט 49, 16.11.2026).

שלוש השוואות, כל אחת שורה-שורה ועמוד-עמוד (מזהה היחידה, מקום השורה בטור, אורך הטקסט, הערות השוליים,
הכותרת הרצה ומספר העמוד):
  1. מנוע העץ מול המנוע שבאתר החי (שינוי במנוע שאמור להיות "מהירות בלבד" אינו מזיז אף שורה).
  2. מצב הדפוס (המסגרת שבדף המנהל) מול דף ההדפסה הרגיל באותם פרמטרים.
  3. ה-PDF של דף ההדפסה הרגיל: מספר העמודים ומספר העמוד בכל עמוד.

הרצה (תמיד דרך uv):
  uv run --with playwright --with pymupdf python tools/print/pm_identity.py --slug berakhot --perakim 1,6 --profile b5lg
הדף נטען מן האתר החי, ו-mas.js מוחלף בזיכרון בגרסה שבה מנוע ההדפסה ומצב הדפוס מן העץ. שום דבר אינו נכתב לאתר:
כל בקשה שאינה GET לדומיינים של האתר נחסמת.
"""
import argparse, asyncio, json, os, sys, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SITE = 'https://leokmei.com/'

LAYOUT = r"""(doc)=>{const out=[];doc.querySelectorAll('#prnout > .shp, #prnout > .pg').forEach((pe,pi)=>{const pg=pe.classList.contains('pg')?pe:pe.querySelector('.pg');
 pg.querySelectorAll(':scope > .pcol').forEach((c,ci)=>{const tx=c.querySelector('.ptx');
  const rows=[...tx.querySelectorAll(':scope > .row')].map(r=>[r.getAttribute('data-u')||'',r.style.top,r.textContent.replace(/\s+/g,' ').trim().length]);
  const fn=c.querySelector('.pfn');out.push({p:pi+1,c:ci,h:tx.style.height,rows,fn:fn?fn.textContent.replace(/\s+/g,' ').trim():''})});
 out.push({p:pi+1,hd:(pg.querySelector('.phd')||{}).textContent,num:(pg.querySelector('.pnum')||{}).textContent})});return out}"""


def tree_mas(live_js):
    eng = open(os.path.join(ROOT, 'tools', 'print_engine.js'), encoding='utf-8').read()
    pm = open(os.path.join(ROOT, 'tools', 'print_mode.js'), encoding='utf-8').read()
    a = live_js.index('/* =================== מנוע הדפסה ל-PDF'); a = live_js.rfind('\n', 0, a) + 1
    b = live_js.index('/* =================== הורד וורד'); b = live_js.rfind('\n', 0, b) + 1
    js = live_js[:a] + eng + '\n' + live_js[b:]
    if '/* =================== מצב דפוס' in js:
        s0 = js.index('/* =================== מצב דפוס'); s0 = js.rfind('\n', 0, s0) + 1
        s1 = js.index('  })();\n', s0) + len('  })();\n')
        return js[:s0] + pm + '\n' + js[s1:]
    k = js.index('window.lkOverflow='); k = js.index('\n', k) + 1
    return js[:k] + pm + '\n' + js[k:]


def strip_lines(s):
    """data-u נוסף לשורות במנוע העץ (פרומפט 49). במנוע החי אין אותו - ההשוואה בלעדיו"""
    for x in s:
        if 'rows' in x:
            x['rows'] = [[r[1], r[2]] for r in x['rows']]
    return s


async def wait_prn(pg, frame_js='window'):
    for _ in range(1500):
        st = await pg.evaluate(f"(()=>{{try{{const P={frame_js}.__PRN;return P&&P.state}}catch(e){{return null}}}})()")
        if st in ('done', 'error'):
            return st
        await pg.wait_for_timeout(200)
    return 'timeout'


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--slug', default='berakhot')
    ap.add_argument('--perakim', default='1')
    ap.add_argument('--profile', default='b5lg')
    ap.add_argument('--tos', default='1')
    ap.add_argument('--out', default='')
    a = ap.parse_args()
    from playwright.async_api import async_playwright
    req = urllib.request.Request(SITE + 'mas.js', headers={'User-Agent': 'Mozilla/5.0 pm_identity'})
    live = urllib.request.urlopen(req).read().decode('utf-8')
    tree = tree_mas(live)
    bad = 0
    async with async_playwright() as p:
        exe = '/opt/pw-browsers/chromium' if os.path.exists('/opt/pw-browsers/chromium') else None
        b = await p.chromium.launch(executable_path=exe, args=['--no-sandbox'] if exe else [])
        for perek in [int(x) for x in a.perakim.split(',')]:
            res = {}
            for which in ('live', 'tree'):
                c = await b.new_context(viewport={'width': 1400, 'height': 900})
                def mk(which):
                    return lambda route: rt0(route, which)
                async def rt0(route, which):
                    u = route.request.url
                    if which == 'tree' and '/mas.js' in u:
                        return await route.fulfill(body=tree, content_type='application/javascript; charset=utf-8')
                    if route.request.method != 'GET' and ('leokmei' in u):
                        return await route.abort()
                    await route.continue_()
                await c.route('**/*', mk(which))
                await c.add_init_script("try{localStorage.setItem('lg-admin','1')}catch(e){}")
                pg = await c.new_page()
                errs = []
                pg.on('pageerror', lambda e: errs.append(str(e)))
                await pg.goto(SITE + a.slug + '.html', wait_until='load')
                for _ in range(100):
                    if await pg.evaluate("typeof lkTos!=='undefined'&&typeof D!=='undefined'"):
                        break
                    await pg.wait_for_timeout(200)
                q = await pg.evaluate("""([n,prof,tos])=>{const M=lkTos.perekMap(),l=M.lab[n-1];const pk=(l.perek||'')+'|'+(l.perekName||'');
                    let A=-1,B=-1;D.pages.forEach((p,i)=>{if(p.units&&p.units.length&&((p.perek||'')+'|'+(p.perekName||''))===pk){if(A<0)A=i;B=i}});
                    const q=new URLSearchParams();q.set('print','1');q.set('from',D.pages[A].daf);q.set('to',D.pages[B].daf);q.set('pk',pk);q.set('tos',tos);q.set('duplex','0');q.set('profile',prof);
                    return q.toString()}""", [perek, a.profile, a.tos])
                t0 = time.time()
                await pg.goto(SITE + a.slug + '.html?' + q, wait_until='load')
                st = await wait_prn(pg)
                dt = time.time() - t0
                lay = await pg.evaluate('(' + LAYOUT + ')(document)')
                res[which] = {'lay': lay, 'st': st, 'sec': round(dt, 1),
                              't': await pg.evaluate('JSON.stringify(window.__PRN.report&&window.__PRN.report.t)'),
                              'issues': await pg.evaluate("(window.__PRN.report.issues||[]).map(i=>i.type+'|'+i.page)")}
                if which == 'tree':
                    pdf = os.path.join(a.out or HERE, f'_pm_{a.slug}_{perek}.pdf') if a.out else None
                    if pdf:
                        await pg.pdf(path=pdf, prefer_css_page_size=True, print_background=True)
                        res['pdf'] = pdf
                    # מצב הדפוס בדף המנהל
                    await pg.goto(SITE + a.slug + '.html', wait_until='load')
                    for _ in range(100):
                        if await pg.evaluate("typeof lkPrintMode!=='undefined'"):
                            break
                        await pg.wait_for_timeout(200)
                    if not await pg.evaluate("typeof lkPrintMode!=='undefined'"):
                        print('   מצב הדפוס לא נטען בדף. שגיאות:', errs[:3], await pg.evaluate("[typeof __pmSnapshot,typeof lkTos,location.href]"), await pg.evaluate("[...document.scripts].map(s=>s.src).join(' ')"))
                        sys.exit(2)
                    await pg.evaluate("([pr,tos])=>localStorage.setItem('lg-pm-prefs',JSON.stringify({paper:pr.slice(0,2),big:pr.endsWith('lg')?1:0,tos:+tos,view:'page',spread:0,zoom:'fit',z:1}))", [a.profile, a.tos])
                    await pg.reload(wait_until='load')
                    for _ in range(100):
                        if await pg.evaluate("typeof lkPrintMode!=='undefined'"):
                            break
                        await pg.wait_for_timeout(200)
                    await pg.evaluate("lkPrintMode.open()")
                    await pg.wait_for_timeout(800)
                    await pg.evaluate("""n=>{const M=lkTos.perekMap(),l=M.lab[n-1];const s=document.getElementById('pm-pk');s.value=(l.perek||'')+'|'+(l.perekName||'');s.dispatchEvent(new Event('change'))}""", perek)
                    t1 = time.time()
                    for _ in range(1500):
                        s2 = await pg.evaluate('lkPrintMode.state()')
                        if s2['pages'] and not s2['busy']:
                            break
                        await pg.wait_for_timeout(200)
                    src = await pg.evaluate("decodeURIComponent(document.getElementById('pmf').src)")
                    if ('pk=' in src) and (urllib.parse.unquote_plus(q.split('pk=')[1].split('&')[0]) not in urllib.parse.unquote_plus(src)):
                        print('   אזהרה: מצב הדפוס טען פרק אחר:', src[-80:])
                    res['pm'] = {'lay': await pg.evaluate("(" + LAYOUT + ")(document.getElementById('pmf').contentDocument)"), 'sec': round(time.time() - t1, 1),
                                 'state': s2}
                if errs:
                    print('   שגיאות בדף (' + which + '):', errs[:3])
                await c.close()
            L, T, PM = strip_lines(json.loads(json.dumps(res['live']['lay']))), strip_lines(json.loads(json.dumps(res['tree']['lay']))), res['pm']['lay']
            ok1 = L == T
            ok2 = PM == res['tree']['lay']
            pages = len([x for x in res['tree']['lay'] if 'hd' in x])
            print(f'פרק {perek}: {pages} עמודים | עץ מול חי: {"זהה" if ok1 else "שונה"} | מצב דפוס מול הדפסה: {"זהה" if ok2 else "שונה"}'
                  f' | זמן: חי {res["live"]["sec"]} שנ\', עץ {res["tree"]["sec"]} שנ\', מצב דפוס {res["pm"]["sec"]} שנ\'')
            print('   מדידה:', res['live']['t'], '->', res['tree']['t'])
            eng_n = len(res['tree']['issues'])
            pm_n = len([i for i in res['pm']['state']['issues'] if i.get('src') == 'engine'])
            print(f'   הבודק החי: {pm_n} ממצאים של המנוע מתוך {eng_n} -', 'כולם' if pm_n == eng_n else 'חסר!')
            bad += 0 if pm_n == eng_n else 1
            print('   ממצאי המנוע:', res['tree']['issues'] == res['live']['issues'], len(res['tree']['issues']), '| בסימני המצב:', len(res['pm']['state']['issues']),
                  json.dumps(__import__('collections').Counter(i['type'] for i in res['pm']['state']['issues']), ensure_ascii=False))
            for (nm, X, Y, ok) in (('עץ/חי', L, T, ok1), ('מצב/הדפסה', PM, res['tree']['lay'], ok2)):
                if not ok:
                    bad += 1
                    for i, (x, y) in enumerate(zip(X, Y)):
                        if x != y:
                            ks = [k for k in set(x) | set(y) if x.get(k) != y.get(k)]
                            det = ''
                            if 'rows' in ks:
                                rx, ry = x.get('rows', []), y.get('rows', [])
                                j = next((j for j in range(min(len(rx), len(ry))) if rx[j] != ry[j]), min(len(rx), len(ry)))
                                det = f' שורה {j}: {rx[j:j+2]} מול {ry[j:j+2]}'
                            print('   הבדל ראשון', nm, 'עמוד', x.get('p'), 'טור', x.get('c'), 'שדות', ks, det,
                                  {k: (str(x.get(k))[:80], str(y.get(k))[:80]) for k in ks if k != 'rows'})
                            break
                    if len(X) != len(Y):
                        print('   מספר פריטים', len(X), len(Y))
            if res.get('pdf'):
                import fitz
                d = fitz.open(res['pdf'])
                nums = [x['num'] for x in res['tree']['lay'] if 'hd' in x]
                miss = [n for i, n in enumerate(nums) if i >= len(d) or (n or '').strip() not in d[i].get_text()]
                okp = len(d) == pages and not miss
                print(f'   PDF: {len(d)} עמודים, {d[0].rect.width/72*25.4:.0f}x{d[0].rect.height/72*25.4:.0f} מ"מ, {"תואם" if okp else "לא תואם"}')
                bad += 0 if okp else 1
        await b.close()
    print('תוצאה:', 'הכל זהה' if not bad else f'{bad} הבדלים')
    sys.exit(1 if bad else 0)


asyncio.run(main())
