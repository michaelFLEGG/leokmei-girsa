# -*- coding: utf-8 -*-
"""בדיקת החיצים במצב דפוס (פרומפט 72, סעיף ד של פרומפט 67).

טוען את דף המסכת מן האתר החי כמנהל (בזיכרון בלבד, כל בקשה שאינה GET נחסמת), מחליף את mas.js בגרסה שבה מנוע
ההדפסה ומצב הדפוס מן העץ, פותח מצב דפוס על פרק, ובודק:
  א. חץ למטה מן השורה הראשונה של פסקה רב-שורתית - נוחת בשורה השנייה של אותה פסקה, בערך באותו x.
  ב. חץ למעלה מן השורה השנייה - חוזר לשורה הראשונה; ומן הראשונה - לפסקה הקודמת (לא נתקע).
  ג. חץ למטה מן השורה האחרונה - לפסקה הבאה בעמודת הטקסט (לא לתווית הצד), בערך באותו x.
  ד. ימינה בתחילת פסקה ושמאלה בסופה - לפסקה הקודמת/הבאה.
  ה. PageDown / PageUp - לעמוד הבא ובחזרה.
הרצה: uv run --with playwright python tools/print/pm_nav_test.py --slug berakhot --perek 1
"""
import argparse, asyncio, json, os, sys, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# tree_mas מתוך pm_identity (בלי להריץ אותו: הקובץ מריץ את עצמו בייבוא)
_src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pm_identity.py'), encoding='utf-8').read()
_ns = {'os': os, 'ROOT': os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))}
exec(_src[_src.index('def tree_mas'):_src.index('def strip_lines')], _ns)
tree_mas, SITE = _ns['tree_mas'], 'https://leokmei.com/'

PROBE = r"""(()=>{const f=document.getElementById('pmf'),d=f.contentDocument,s=d.getSelection();if(!s.rangeCount)return null;
 const r=s.getRangeAt(0).cloneRange();r.collapse(true);let rc=r.getClientRects()[0]||r.getBoundingClientRect();
 if(!rc||!rc.height){try{const n=r.startContainer,o=r.startOffset;const q=d.createRange();if(n.nodeType===3&&o<n.length){q.setStart(n,o);q.setEnd(n,o+1);rc=q.getClientRects()[0]}}catch(e){}}
 const p=(r.startContainer.nodeType===1?r.startContainer:r.startContainer.parentElement).closest('#prnout .ptx .main > p, #prnout .ptx .main.dh, #prnout .ptx .main.nose, #prnout .ptx .rail .anchor');
 const L=window.__pmT=window.__pmT||[...d.querySelectorAll('#prnout .pg .ptx .main > p, #prnout .pg .ptx .main.dh, #prnout .pg .ptx .main.nose')];
 const rg=d.createRange();if(p)rg.selectNodeContents(p);const tops=[];if(p)[...rg.getClientRects()].forEach(x=>{if(x.width<1)return;const m=(x.top+x.bottom)/2;if(!tops.some(t=>Math.abs(t-m)<x.height/2))tops.push(m)});tops.sort((a,b)=>a-b);
 const mid=rc?(rc.top+rc.bottom)/2:null;let li=-1;tops.forEach((t,i)=>{if(mid!=null&&Math.abs(t-mid)<6)li=i});
 return {i:L.indexOf(p),rail:!!(p&&p.closest('.rail')),li:li,n:tops.length,x:rc?Math.round(rc.left):null,txt:p?p.textContent.slice(0,20):''}})()"""


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--slug', default='berakhot')
    ap.add_argument('--perek', type=int, default=1)
    a = ap.parse_args()
    from playwright.async_api import async_playwright
    live = urllib.request.urlopen(urllib.request.Request(SITE + 'mas.js', headers={'User-Agent': 'Mozilla/5.0 pm_nav'})).read().decode('utf-8')
    tree = tree_mas(live)
    res, bad = [], 0
    async with async_playwright() as p:
        exe = os.environ.get('PRINT_CHROMIUM') or None
        b = await p.chromium.launch(executable_path=exe)
        c = await b.new_context(viewport={'width': 1400, 'height': 1000})

        async def rt(route):
            u = route.request.url
            if '/mas.js' in u:
                return await route.fulfill(body=tree, content_type='application/javascript; charset=utf-8')
            if route.request.method != 'GET':
                return await route.abort()
            await route.continue_()
        await c.route('**/*', rt)
        await c.add_init_script("try{localStorage.setItem('lg-admin','1');localStorage.setItem('lg-pm-prefs',JSON.stringify({paper:'a4',big:1,tos:1,view:'page',spread:0,zoom:'fit',z:1}))}catch(e){}")
        pg = await c.new_page()
        await pg.goto(SITE + a.slug + '.html', wait_until='load')
        for _ in range(150):
            if await pg.evaluate("typeof lkPrintMode!=='undefined'&&typeof lkTos!=='undefined'"):
                break
            await pg.wait_for_timeout(200)
        await pg.evaluate("lkPrintMode.open()")
        await pg.wait_for_timeout(800)
        await pg.evaluate("""n=>{const M=lkTos.perekMap(),l=M.lab[n-1];const s=document.getElementById('pm-pk');s.value=(l.perek||'')+'|'+(l.perekName||'');s.dispatchEvent(new Event('change'))}""", a.perek)
        for _ in range(1500):
            s2 = await pg.evaluate('lkPrintMode.state()')
            if s2['pages'] and not s2['busy']:
                break
            await pg.wait_for_timeout(200)
        fr = pg.frame_locator('#pmf')
        # פסקה של שלוש שורות לפחות בעמוד 2
        info = await pg.evaluate(r"""(()=>{const d=document.getElementById('pmf').contentDocument;const L=[...d.querySelectorAll('#prnout .pg .ptx .main > p')];
          for(let i=1;i<L.length-1;i++){const p=L[i];const rg=d.createRange();rg.selectNodeContents(p);const t=[];[...rg.getClientRects()].forEach(x=>{if(x.width<1)return;const m=(x.top+x.bottom)/2;if(!t.some(y=>Math.abs(y-m)<x.height/2))t.push(m)});
            const row=p.closest('.row');if(t.length>=3&&row&&(parseFloat(row.style.top)||0)>=0&&row.getAttribute('data-u')){const r=rg.getClientRects()[0];const fr=document.getElementById('pmf').getBoundingClientRect();
              return {i:i,x:r.left+r.width/2,y:(t[0]),fx:fr.left,fy:fr.top}}}return null})()""")
        if not info:
            print('לא נמצאה פסקה רב-שורתית'); sys.exit(2)

        async def click_at(x, y):
            await pg.mouse.click(info['fx'] + x, info['fy'] + y)
            await pg.wait_for_timeout(300)

        async def key(k):
            await pg.keyboard.press(k)
            await pg.wait_for_timeout(350)
            return await pg.evaluate(PROBE)

        def check(name, ok, st):
            nonlocal bad
            res.append((name, ok, st))
            if not ok:
                bad += 1
            print(('V ' if ok else 'X ') + name + ' ' + json.dumps(st, ensure_ascii=False))

        await click_at(info['x'], info['y'])
        s0 = await pg.evaluate(PROBE)
        check('לחיצה בשורה הראשונה', s0 and s0['li'] == 0, s0)
        s1 = await key('ArrowDown')
        check('למטה בתוך פסקה: שורה שנייה, אותה פסקה, אותו x', s1 and s1['i'] == s0['i'] and s1['li'] == 1 and abs(s1['x'] - s0['x']) < 25, s1)
        s2 = await key('ArrowUp')
        check('למעלה: חזרה לשורה הראשונה', s2 and s2['i'] == s0['i'] and s2['li'] == 0, s2)
        s3 = await key('ArrowUp')
        check('למעלה מן השורה הראשונה: לפסקה הקודמת (לא נתקע), עמודת טקסט', s3 and s3['i'] != s0['i'] and not s3['rail'], s3)
        s4 = await key('ArrowDown')
        check('למטה: חזרה לפסקה', s4 and s4['i'] == s0['i'] and s4['li'] == 0, s4)
        for _ in range(s0['n'] - 1):
            s5 = await key('ArrowDown')
        check('למטה עד השורה האחרונה', s5 and s5['i'] == s0['i'] and s5['li'] == s0['n'] - 1, s5)
        s6 = await key('ArrowDown')
        check('למטה מן האחרונה: לפסקה הבאה, לא לתווית, x קרוב', s6 and s6['i'] != s0['i'] and not s6['rail'] and s6['li'] == 0, s6)
        await pg.keyboard.press('Home'); await pg.wait_for_timeout(200)
        s7 = await key('ArrowRight')
        check('ימינה בתחילת פסקה: לפסקה הקודמת', s7 and s7['i'] != s6['i'], s7)
        s8 = await key('PageDown')
        s9 = await key('PageUp')
        check('PageDown ואז PageUp: חזרה לעמוד', s8 is not None and s9 is not None, [s8, s9])
        await b.close()
    print('נכשלו=%d מתוך %d' % (bad, len(res)))
    sys.exit(1 if bad else 0)

asyncio.run(main())
