# בדיקת פרומפט 25 בטלפון (רוחב 400): אותה תצוגה, הפס צף בתחתית, נגיעה ב"קבל"
import os
SHOT = os.environ.get('P25SHOT', '_work/p25')
OUT = []
def row(name, val, ok):
    OUT.append(ok); print(('OK  ' if ok else 'FAIL') + ' %d %s | %s' % (W, name, json.dumps(val, ensure_ascii=False)[:300]))
vis = pg.evaluate("()=>{const b=document.getElementById('altgo');return b?{vis:!!b.offsetWidth,t:b.textContent.trim()}:null}")
print('altgo button', vis)
pg.evaluate("()=>altMode()"); pg.wait_for_timeout(1800)
s = pg.evaluate("""()=>{const g=document.querySelector('#flow .altv'),b=document.getElementById('altbar');const r=g.getBoundingClientRect(),q=b.getBoundingClientRect();
 return {view:!!g,mob:b.classList.contains('mob'),barTop:Math.round(q.top),barBottom:Math.round(q.bottom),vh:innerHeight,gTop:Math.round(r.top),gBottom:Math.round(r.bottom),
   covered:r.bottom>q.top,add:g.querySelectorAll('.skpadd').length,del:g.querySelectorAll('del.skpdel').length,bar:b.innerText.replace(/\s+/g,' ')}}""")
row('בטלפון: התצוגה על הטקסט, הפס צף בתחתית ואינו מכסה את הפסקה', s, s['view'] and s['mob'] and s['barBottom'] <= s['vh'] and not s['covered'] and s['gTop'] < s['vh'] * 0.45)
pg.screenshot(path=SHOT + '-phone-after.png')
id0 = pg.evaluate("()=>document.querySelector('#flow .altv').getAttribute('data-alt')")
pg.tap('#altbar button[data-a="ok"]'); pg.wait_for_timeout(1500)
s2 = pg.evaluate("()=>({id:(document.querySelector('#flow .altv')||{getAttribute:()=>null}).getAttribute('data-alt'),ed:ED.filter(e=>e.by==='בחירת נוסח').length})")
row('נגיעה ב"קבל": נקלט ועובר לנקודה הבאה', s2, s2['ed'] == 1 and s2['id'] and s2['id'] != id0)
pg.screenshot(path=SHOT + '-phone-next.png')
print('SUMMARY', sum(OUT), '/', len(OUT))
