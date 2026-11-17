# -*- coding: utf-8 -*-
"""בדיקת פרומפט 60 (17.11.2026): מדידת כללי העימוד על כל פרקי מסכת, לפני ואחרי שינוי במנוע.

מודד בכל פרק:
  - כותרות צד שנשברו לשתי שורות (ומתוכן עד שלוש מילים)
  - כותרת (נושא, ד"ה, פתיחת פרק) שאחריה פחות משתי שורות תוכן באותו טור
  - שורה בודדת של יחידה בראש טור או בסוף טור
  - ממצאי המנוע עצמו (R.issues)

הרצה (דרך uv):
  uv run --with playwright python tools/print/p60_check.py --slug sukkah --profile b5lg [--perakim 1,2] [--base]
--base: המנוע והקוד המשותף כפי שהם ב-HEAD של git (לפני השינוי). בלעדיו: העץ.
הקוד המשותף (fitAnchors ועוד, מתוך build_site.py) נלקח מן האתר החי, ועליו מוחלים ההבדלים שבין build_site.py
שבעץ לזה שב-HEAD (חלקי ה-JS בלבד). שום דבר אינו נכתב לאתר: כל בקשה שאינה GET נחסמת.
"""
import argparse, asyncio, json, os, subprocess, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SITE = 'https://leokmei.com/'
EXTRA = os.environ.get('P60_EXTRA', '')
sys.path.insert(0, HERE)


def base_ref():
    """הבסיס להשוואה: נקודת ההתפצלות מן הענף הראשי (main), כדי שגם עבודה שכבר נשמרה בענף תיחשב אחרי"""
    r = subprocess.run(['git', 'merge-base', 'HEAD', 'origin/main'], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    return r or 'HEAD'


def git_show(path):
    return subprocess.run(['git', 'show', base_ref() + ':' + path], cwd=ROOT, capture_output=True, text=True, encoding='utf-8').stdout


def js_patches():
    """זוגות (ישן, חדש): ההבדלים בין build_site.py שבעץ לזה שב-HEAD, בהקשר של שתי שורות - להחלה על mas.js החי
    (הקוד המשותף שבאתר נבנה מאותו טקסט). שורות פייתון שאינן בקוד המשותף אינן נמצאות ב-mas.js - ואז עוצרים בקול"""
    import difflib
    a = git_show('tools/build_site.py').split('\n')
    b = open(os.path.join(ROOT, 'tools', 'build_site.py'), encoding='utf-8').read().split('\n')
    out = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag == 'equal':
            continue
        c = 2
        while True:
            old = '\n'.join(a[max(0, i1 - c):i2 + c])
            if c >= 6 or old.strip():
                break
            c += 1
        out.append(['\n'.join(a[max(0, i1 - c):i2 + c]), '\n'.join(a[max(0, i1 - c):i1] + b[j1:j2] + a[i2:i2 + c]), b[j1:j2]])
    return out


def make_mas(live, base):
    eng = git_show('tools/print_engine.js') if base else open(os.path.join(ROOT, 'tools', 'print_engine.js'), encoding='utf-8').read()
    if base and '__PRNDBG' not in eng:
        eng = eng.replace("    TM('paginate');\n", "    TM('paginate');\n    window.__PRNDBG={L:L,cols:cols,recs:recs.map(function(x){return {kind:x.kind,u:x.u&&x.u.id,daf:x.daf}})};\n", 1)
    pm = git_show('tools/print_mode.js') if base else open(os.path.join(ROOT, 'tools', 'print_mode.js'), encoding='utf-8').read()
    a = live.index('/* =================== מנוע הדפסה ל-PDF'); a = live.rfind('\n', 0, a) + 1
    b = live.index('/* =================== הורד וורד'); b = live.rfind('\n', 0, b) + 1
    js = live[:a] + eng + '\n' + live[b:]
    s0 = js.index('/* =================== מצב דפוס'); s0 = js.rfind('\n', 0, s0) + 1
    s1 = js.index('  })();\n', s0) + len('  })();\n')
    js = js[:s0] + pm + '\n' + js[s1:]
    if not base:
        css = []
        for old, new, added in js_patches():
            if old in js:
                js = js.replace(old, new, 1)
                continue
            # ה-CSS של הדף אינו ב-mas.js: שורות CSS שנוספו מוזרקות כגיליון סגנון
            body = [x for x in added if x.strip() and not x.strip().startswith('/*')]
            if body and all('{' in x and 'function' not in x and '=>' not in x for x in body):
                css.extend(body)
                continue
            raise SystemExit('תיקון שאינו נמצא ב-mas.js החי: ' + old[:80])
        if css:
            js = '(function(){var s=document.createElement("style");s.textContent=' + json.dumps('\n'.join(css)) + ';document.head.appendChild(s)})();\n' + js
    return js


DUMP = r"""()=>{const G=window.__PRNDBG,R=window.__PRN.report;if(!G)return null;const L=G.L,cols=G.cols,recs=G.recs;
 const HEADS={'nose':1,'dh':1,'perek-range':1,'perek-start':1};
 const txt=ri=>{const u=recs[ri]&&recs[ri].u;const r=u!=null?document.querySelector('#prnout .row[data-u="'+u+'"] > .main'):null;return r?r.textContent.replace(/\s+/g,' ').trim().slice(0,50):''};
 const headBottom=[],loneTop=[],loneBot=[];
 cols.forEach((c,ci)=>{const pg=Math.floor(ci/2)+1;
  if(c.e<L.length){for(let q=c.e-1;q>=c.s&&q>=c.e-3;q--){if(HEADS[L[q].kind]||L[q].hb){let cnt=0;for(let z=q+1;z<c.e;z++)if(!(HEADS[L[z].kind]||L[z].hb))cnt++;
      const t0=q;let h0=q;while(h0>c.s&&L[h0-1].ri===L[q].ri)h0--;
      if(cnt<2){headBottom.push({page:pg,col:ci%2,daf:L[q].daf,kind:L[q].kind,u:recs[L[q].ri].u,after:cnt,t:txt(L[q].ri)});}break}}}
  // שורה בודדת של יחידה בראש טור (המשך מן הטור הקודם)
  if(c.s>0&&L[c.s].ri===L[c.s-1].ri){let n=0;for(let z=c.s;z<c.e&&L[z].ri===L[c.s].ri;z++)n++;if(n===1)loneTop.push({page:pg,col:ci%2,daf:L[c.s].daf,kind:L[c.s].kind,u:recs[L[c.s].ri].u,t:txt(L[c.s].ri)})}
  if(c.e<L.length&&L[c.e].ri===L[c.e-1].ri){let n=0;for(let z=c.e-1;z>=c.s&&L[z].ri===L[c.e-1].ri;z--)n++;if(n===1)loneBot.push({page:pg,col:ci%2,daf:L[c.e-1].daf,kind:L[c.e-1].kind,u:recs[L[c.e-1].ri].u,t:txt(L[c.e-1].ri)})}
 });
 const seen={},labels=[];document.querySelectorAll('#prnout .row').forEach(r=>{const u=r.getAttribute('data-u');if(!u||seen[u])return;seen[u]=1;
  r.querySelectorAll(':scope > .rail > .win').forEach(w=>{const t=w.textContent.replace(/\s+/g,' ').trim();if(!t)return;
   const a=w.querySelector('.anchor')||w,rg=document.createRange();rg.selectNodeContents(a);const tops=new Set([...rg.getClientRects()].filter(x=>x.height>0.5&&x.width>0.5).map(x=>Math.round(x.top)));
   labels.push({u:+u,t:t,words:t.split(' ').filter(Boolean).length,lines:tops.size,w2:w.classList.contains('w2'),fs:w.style.fontSize||''})})});
 const ulines={};L.forEach(l=>{const u=recs[l.ri].u;if(u!=null)ulines[u]=(ulines[u]||0)+1});
 return {ulines,pages:R.pages.length,issues:(R.issues||[]).map(i=>({type:i.type,page:i.page,daf:i.daf,unit:i.unit,detail:i.detail})),headBottom,loneTop,loneBot,labels,t:R.t}}"""


async def run_perek(b, mas, slug, perek, profile, tos):
    c = await b.new_context(viewport={'width': 1400, 'height': 900})

    async def rt(route):
        u = route.request.url
        if '/mas.js' in u:
            return await route.fulfill(body=mas, content_type='application/javascript; charset=utf-8')
        if route.request.method != 'GET' and 'leokmei' in u:
            return await route.abort()
        await route.continue_()
    await c.route('**/*', rt)
    pg = await c.new_page()
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto(SITE + slug + '.html', wait_until='load')
    for _ in range(150):
        if await pg.evaluate("typeof lkTos!=='undefined'&&typeof D!=='undefined'"):
            break
        await pg.wait_for_timeout(200)
    q = await pg.evaluate("""([n,prof,tos])=>{const M=lkTos.perekMap(),l=M.lab[n-1];if(!l)return null;const pk=(l.perek||'')+'|'+(l.perekName||'');
        let A=-1,B=-1;D.pages.forEach((p,i)=>{if(p.units&&p.units.length&&((p.perek||'')+'|'+(p.perekName||''))===pk){if(A<0)A=i;B=i}});
        const q=new URLSearchParams();q.set('print','1');q.set('from',D.pages[A].daf);q.set('to',D.pages[B].daf);q.set('pk',pk);q.set('tos',tos);q.set('duplex','0');q.set('profile',prof);
        return q.toString()}""", [perek, profile, tos])
    if q and EXTRA: q += '&' + EXTRA
    if not q:
        await c.close()
        return None
    t0 = time.time()
    await pg.goto(SITE + slug + '.html?' + q, wait_until='load')
    st = None
    for _ in range(1500):
        st = await pg.evaluate("(()=>{try{return window.__PRN&&window.__PRN.state}catch(e){return null}})()")
        if st in ('done', 'error'):
            break
        await pg.wait_for_timeout(200)
    res = await pg.evaluate('(' + DUMP + ')()') if st == 'done' else {'error': await pg.evaluate("window.__PRN&&window.__PRN.error")}
    res['sec'] = round(time.time() - t0, 1)
    res['errs'] = errs[:3]
    res['url'] = SITE + slug + '.html?' + q
    await c.close()
    return res


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--slug', default='sukkah')
    ap.add_argument('--perakim', default='')
    ap.add_argument('--profile', default='b5lg')
    ap.add_argument('--tos', default='1')
    ap.add_argument('--base', action='store_true')
    ap.add_argument('--both', action='store_true', help='לפני ואחרי, פרק אחרי פרק (הנתונים החיים משתנים במהלך הריצה)')
    ap.add_argument('--out', default='')
    a = ap.parse_args()
    from playwright.async_api import async_playwright
    live = urllib.request.urlopen(urllib.request.Request(SITE + 'mas.js', headers={'User-Agent': 'Mozilla/5.0 p60_check'})).read().decode('utf-8')
    modes = [('לפני', make_mas(live, True)), ('אחרי', make_mas(live, False))] if a.both else [('', make_mas(live, a.base))]
    perakim = [int(x) for x in a.perakim.split(',')] if a.perakim else list(range(1, 40))
    out = {}
    tot = {}
    async with async_playwright() as p:
        exe = '/opt/pw-browsers/chromium' if os.path.exists('/opt/pw-browsers/chromium') else None
        b = await p.chromium.launch(executable_path=exe, args=['--no-sandbox'] if exe else [])
        for n in perakim:
            stop = False
            for nm, mas in modes:
                r = await run_perek(b, mas, a.slug, n, a.profile, a.tos)
                if r is None:
                    stop = True
                    break
                out.setdefault(nm or 'x', {})[n] = r
                if 'error' in r:
                    print(f'{nm} פרק {n}: שגיאה {r["error"]} {r["errs"]}')
                    continue
                # כותרות "משנה א" במסגרת המשנה בנויות בכוונה כשתי שורות (משנה / אות) - אינן כותרת צד שנשברה
                w2 = [x for x in r['labels'] if x['lines'] >= 2 and not x['t'].startswith('משנה')]
                w2s = [x for x in w2 if x['words'] <= 3]
                T = tot.setdefault(nm, {'pages': 0, 'w2': 0, 'w2s': 0, 'hb': 0, 'lt': 0, 'lb': 0, 'iss': 0})
                for k, v in (('pages', r['pages']), ('w2', len(w2)), ('w2s', len(w2s)), ('hb', len(r['headBottom'])), ('lt', len(r['loneTop'])), ('lb', len(r['loneBot'])), ('iss', len(r['issues']))):
                    T[k] += v
                print(f'{nm} פרק {n}: {r["pages"]} עמ\' | כותרות צד בשתי שורות: {len(w2)} (עד 3 מילים: {len(w2s)}) | כותרת בתחתית טור: {len(r["headBottom"])}'
                      f' | בודדת בראש טור: {len(r["loneTop"])} | בסוף טור: {len(r["loneBot"])} | ממצאי מנוע: {len(r["issues"])} | {r["sec"]} שנ\'' + (' שגיאות: ' + str(r['errs']) if r['errs'] else ''), flush=True)
            if stop:
                break
        await b.close()
    for nm, T in tot.items():
        print('סה"כ', nm, json.dumps(T, ensure_ascii=False))
    if any(T['hb'] for nm, T in tot.items() if nm != 'לפני'):
        print('תקלה: כותרת בתחתית טור')
        bad_exit = True
    else:
        bad_exit = False
    if a.out:
        json.dump(out, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    sys.exit(1 if bad_exit else 0)


asyncio.run(main())
