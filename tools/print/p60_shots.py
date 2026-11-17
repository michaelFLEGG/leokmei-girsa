# -*- coding: utf-8 -*-
"""צילומי לפני/אחרי ומדידת מהירות למצב דפוס (פרומפט 60, 17.11.2026).

  uv run --with playwright python tools/print/p60_shots.py --out <תיקייה>
צילומים: סוכה פרק א, B5 מוגדל - הטור שבו כל אחת מן הדוגמאות של מיכאל, לפני (הקוד שב-main) ואחרי (העץ).
מהירות: מצב דפוס בברכות פרק א - Enter ו-Backspace בשורה, זמן הפקודה (cmdMs של המצב).
שום דבר אינו נכתב לאתר: כל בקשה שאינה GET נחסמת.
"""
import argparse, asyncio, json, os, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, 'p60_check.py'), encoding='utf-8').read().replace('asyncio.run(main())', '')
NS = {'__file__': os.path.join(HERE, 'p60_check.py')}
exec(compile(src, 'p60_check', 'exec'), NS)
SITE = NS['SITE']

SHOTS = [('א-כותרת-צד', 'מתקיף רנב'), ('ב-כותרת-נושא', 'מחזקת ראשו ורובו'), ('ג-שורה-בודדת', 'צריכה אף צורת הפתח'),
         ('ה-רשימה', 'רבי - פוסל בפחות')]


async def ctx(b, mas, admin=False, scale=2):
    c = await b.new_context(viewport={'width': 1400, 'height': 1000}, device_scale_factor=scale)

    async def rt(route):
        u = route.request.url
        if '/mas.js' in u:
            return await route.fulfill(body=mas, content_type='application/javascript; charset=utf-8')
        if route.request.method != 'GET' and 'leokmei' in u:
            return await route.abort()
        await route.continue_()
    await c.route('**/*', rt)
    if admin:
        await c.add_init_script("try{localStorage.setItem('lg-admin','1')}catch(e){}")
    return c


async def shots(b, mas, tag, out, url):
    c = await ctx(b, mas)
    pg = await c.new_page()
    await pg.goto(url, wait_until='load')
    for _ in range(600):
        if await pg.evaluate("window.__PRN&&window.__PRN.state==='done'"):
            break
        await pg.wait_for_timeout(200)
    res = {}
    for name, needle in SHOTS:
        box = await pg.evaluate("""(n)=>{const r=[...document.querySelectorAll('#prnout .pcol .row')].find(r=>r.textContent.includes(n)&&(parseFloat(r.style.top)||0)>=-0.5);
            if(!r)return null;const col=r.closest('.pcol');col.scrollIntoView({block:'center'});const a=col.getBoundingClientRect(),q=r.getBoundingClientRect();
            const top=Math.max(a.top,q.top-170),bot=Math.min(a.bottom+40,q.bottom+170);
            return {x:a.left-60,y:top+window.scrollY,w:a.width+120,h:bot-top}}""", needle)
        if not box:
            res[name] = 'לא נמצא'
            continue
        fp = os.path.join(out, f'{name}-{tag}.png')
        await pg.screenshot(path=fp, clip={'x': box['x'], 'y': box['y'], 'width': box['w'], 'height': box['h']}, full_page=True)
        res[name] = fp
    await c.close()
    return res


async def speed(b, mas):
    c = await ctx(b, mas, admin=True, scale=1)
    pg = await c.new_page()
    await pg.goto(SITE + 'berakhot.html', wait_until='load')
    for _ in range(150):
        if await pg.evaluate("typeof lkPrintMode!=='undefined'&&typeof lkTos!=='undefined'"):
            break
        await pg.wait_for_timeout(200)
    await pg.evaluate("localStorage.setItem('lg-pm-prefs',JSON.stringify({paper:'b5',big:1,tos:1,view:'page',spread:0,zoom:'fit',z:1}))")
    await pg.reload(wait_until='load')
    for _ in range(150):
        if await pg.evaluate("typeof lkPrintMode!=='undefined'"):
            break
        await pg.wait_for_timeout(200)
    await pg.evaluate("lkPrintMode.open()")
    await pg.wait_for_timeout(800)
    await pg.evaluate("""()=>{const M=lkTos.perekMap(),l=M.lab[0];const s=document.getElementById('pm-pk');s.value=(l.perek||'')+'|'+(l.perekName||'');s.dispatchEvent(new Event('change'))}""")
    for _ in range(600):
        st = await pg.evaluate('lkPrintMode.state()')
        if st['pages'] and not st['busy']:
            break
        await pg.wait_for_timeout(200)
    for k in range(5):
        bb = await pg.evaluate("""(k)=>{const f=document.getElementById('pmf'),d=f.contentDocument;
            const ps=[...d.querySelectorAll('#prnout .pg .ptx .row.u .main > p')].filter(p=>p.textContent.trim().length>40&&p.getBoundingClientRect().height>0);
            const p=ps[Math.min(ps.length-1,40+k*7)];p.scrollIntoView({block:'center'});const r=p.getBoundingClientRect(),q=f.getBoundingClientRect();
            return {x:q.left+r.left+r.width*0.5,y:q.top+r.top+5}}""", k)
        await pg.wait_for_timeout(300)
        bb = await pg.evaluate("""(k)=>{const f=document.getElementById('pmf'),d=f.contentDocument;
            const ps=[...d.querySelectorAll('#prnout .pg .ptx .row.u .main > p')].filter(p=>p.textContent.trim().length>40&&p.getBoundingClientRect().height>0);
            const p=ps[Math.min(ps.length-1,40+k*7)];const r=p.getBoundingClientRect(),q=f.getBoundingClientRect();
            return {x:q.left+r.left+r.width*0.5,y:q.top+r.top+5}}""", k)
        await pg.mouse.click(bb['x'], bb['y'])
        await pg.wait_for_timeout(300)
        await pg.keyboard.press('Enter')
        await pg.wait_for_timeout(500)
        await pg.keyboard.press('Backspace')
        await pg.wait_for_timeout(500)
        await pg.keyboard.press('Escape')
        await pg.wait_for_timeout(200)
    st = await pg.evaluate('lkPrintMode.state()')
    await c.close()
    return st.get('cmdMs') or []


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--no-speed', action='store_true')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    from playwright.async_api import async_playwright
    live = urllib.request.urlopen(urllib.request.Request(SITE + 'mas.js', headers={'User-Agent': 'Mozilla/5.0 p60'})).read().decode('utf-8')
    base, tree = NS['make_mas'](live, True), NS['make_mas'](live, False)
    url = json.load(open(os.path.join(a.out, 'url.json')))['url'] if os.path.exists(os.path.join(a.out, 'url.json')) else None
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium', args=['--no-sandbox'])
        if url:
            r1 = await shots(b, base, 'לפני', a.out, url)
            r2 = await shots(b, tree, 'אחרי', a.out, url)
            print(json.dumps({'לפני': r1, 'אחרי': r2}, ensure_ascii=False, indent=1))
        if not a.no_speed:
            for nm, m in (('לפני', base), ('אחרי', tree)):
                ms = await speed(b, m)
                print(nm, 'מהירות פקודות (אלפיות):', ms, 'ממוצע', round(sum(ms) / len(ms)) if ms else '-', 'מקסימום', max(ms) if ms else '-')
        await b.close()


asyncio.run(main())
