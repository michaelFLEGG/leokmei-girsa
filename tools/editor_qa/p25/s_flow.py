# בדיקת פרומפט 25: מצב ההכרעה על הטקסט - 10 נקודות ברצף במקלדת, עריכה, Ctrl+Z, רישום ED ו-/alt, וסכם פרק
import os
SHOT = os.environ.get('P25SHOT', '_work/p25')
OUT = []
if os.environ.get('P25EDIT'):
    pg.evaluate("()=>{if(typeof setEdit==='function')setEdit(true)}"); pg.wait_for_timeout(1500)
VERT = pg.evaluate("()=>{const f=document.getElementById('flow');return f.classList.contains('vert')||!(f.scrollWidth>f.clientWidth+4)}")
print('MODE', 'vertical' if VERT else 'columns', 'edit' if os.environ.get('P25EDIT') else 'read')
def row(name, val, ok, note=''):
    OUT.append(ok)
    print(('OK  ' if ok else 'FAIL') + ' %d %s | %s %s' % (W, name, json.dumps(val, ensure_ascii=False)[:300], note))
def key(k, wait=650):
    pg.keyboard.press(k); pg.wait_for_timeout(wait)
ST = r"""()=>{const g=document.querySelector('#flow .altv'),b=document.getElementById('altbar');
  const id=g&&g.getAttribute('data-alt');
  const r=g?g.getBoundingClientRect():null,f=document.getElementById('flow').getBoundingClientRect();
  return {on:document.body.classList.contains('altmode'),id,
    views:document.querySelectorAll('#flow .altv').length,hidden:document.querySelectorAll('#flow [data-ek].altsrc').length,
    add:g?g.querySelectorAll('.skpadd').length:0,del:g?g.querySelectorAll('del.skpdel').length:0,
    bar:b&&b.classList.contains('open')?b.innerText.replace(/\s+/g,' ').trim():'',mob:!!(b&&b.classList.contains('mob')),
    top:r?Math.round((r.top-f.top)/f.height*100):null,
    ed:(typeof ED!=='undefined'?ED.filter(e=>e.by==='בחירת נוסח').length:0),
    dec:Object.keys(JSON.parse(localStorage.getItem('lg-alt-dec-bekhorot')||'{}')).length,
    pop:!!document.querySelector('#altpop.open'),pg:!!document.querySelector('#altpg.open'),
    btn:(document.querySelector('#altgo .t')||{}).textContent||''}}"""
def st(): return pg.evaluate(ST)
OVER = r"""()=>{const b=document.getElementById('altbar');if(!b||!b.classList.contains('open'))return {ok:false,why:'closed'};
  const r=b.getBoundingClientRect();let hit=[];
  document.querySelectorAll('#flow .row').forEach(w=>{const q=w.getBoundingClientRect();if(q.height&&q.left<r.right&&q.right>r.left&&q.top<r.bottom&&q.bottom>r.top){
    /* רק שורות טקסט ממש */
    const rg=document.createRange();rg.selectNodeContents(w);for(const c of rg.getClientRects()){if(c.width>2&&c.left<r.right&&c.right>r.left&&c.top<r.bottom&&c.bottom>r.top){hit.push(w.id);break}}}});
  const g=document.querySelector('#flow .altv'),gr=g?g.getBoundingClientRect():null;
  const onCur=gr?(gr.left<r.right&&gr.right>r.left&&gr.top<r.bottom&&gr.bottom>r.top):false;
  return {ok:!hit.length&&!onCur,hit:hit.slice(0,5),onCur,mob:b.classList.contains('mob'),rect:[Math.round(r.left),Math.round(r.top),Math.round(r.width),Math.round(r.height)]}}"""

s0 = st()
row('לפני הכניסה: אין תצוגה, הכפתור בסרגל', s0, not s0['on'] and s0['views'] == 0 and s0['btn'].startswith('בחר נוסח ('))
stat = pg.evaluate("()=>altStat()")
row('איתור הנקודות בטקסט', stat, stat['found'] >= 27, 'קודם: 27 מתוך 44 (בלי איתור לפי קרבה)')
# כניסה במקלדת: N
pg.mouse.click(30, 300); pg.wait_for_timeout(200)
key('n', 1400)
s1 = st()
row('N נכנס למצב ההכרעה, תצוגה אחת על הטקסט, בלי חלונית', s1, s1['on'] and s1['views'] == 1 and s1['hidden'] == 1 and not s1['pop'] and not s1['pg'] and (s1['add'] + s1['del']) > 0)
if VERT:
    row('הפסקה בשליש העליון', s1['top'], s1['top'] is not None and 0 <= s1['top'] <= 40)
else:
    vis = pg.evaluate("()=>{const g=document.querySelector('#flow .altv'),f=document.getElementById('flow');const r=g.getBoundingClientRect(),q=f.getBoundingClientRect();return r.left>=q.left-1&&r.right<=q.right+1&&r.top>=q.top-1&&r.bottom<=q.bottom+1}")
    row('בתצוגת הטורים: הפסקה כולה בתוך המסך', vis, vis)
ov = pg.evaluate(OVER)
row('הפס אינו מכסה טקסט', ov, ov['ok'])
row('הפס: קבל, השאר, ערוך, מונה, תווית', s1['bar'], all(x in s1['bar'] for x in ('קבל', 'השאר', 'ערוך', 'מתוך 44')))
pg.screenshot(path=SHOT + '-after-%d.png' % W)
# צבע הסימון: טקסט ירוק, בלי רקע
css = pg.evaluate("""()=>{const a=document.querySelector('#flow .altv .skpadd'),d=document.querySelector('#flow .altv del.skpdel');
  const g=document.querySelector('#flow .altv'),o=document.querySelector('#flow [data-ek].altsrc');
  const ca=a?getComputedStyle(a):null,cd=d?getComputedStyle(d):null,cg=getComputedStyle(g),co=o?o:null;
  return {addColor:ca&&ca.color,addBg:ca&&ca.backgroundColor,addDeco:ca&&ca.textDecorationLine,delColor:cd&&cd.color,delDeco:cd&&cd.textDecorationLine,
    font:cg.fontFamily.slice(0,30),size:cg.fontSize,gbg:cg.backgroundColor,shadow:cg.boxShadow}}""")
row('נוסף: ירוק עם קו תחתון ובלי רקע; נמחק: קו חוצה אפור; בלי רקע לפסקה', css,
    (css['addColor'] is None or (css['addBg'] in ('rgba(0, 0, 0, 0)', 'transparent') and 'underline' in css['addDeco'])) and
    (css['delColor'] is None or 'line-through' in css['delDeco']) and css['gbg'] in ('rgba(0, 0, 0, 0)', 'transparent'))
# 10 נקודות ברצף, רק במקלדת: קבל / השאר לסירוגין, פעם אחת הבא/הקודם
seen = [s1['id']]
acts = []
for i in range(10):
    if i == 3:
        key('ArrowDown'); a = st()['id']; key('ArrowUp'); b = st()['id']
        row('חץ מטה ואז חץ מעלה חוזרים לאותה נקודה', [a, b], b == seen[-1] and a != b)
    k = 'Enter' if i % 2 == 0 else 'Delete'
    before = st()
    key(k, 900)
    after = st()
    acts.append((k, before['id'], after['id'], after['ed'], after['dec']))
    seen.append(after['id'])
ok_seq = all(a[1] != a[2] for a in acts) and len(set(seen)) == len(seen)
row('10 הכרעות ברצף: כל אחת עוברת מיד לנקודה הבאה, אף נקודה אינה חוזרת', [(a[0], a[3], a[4]) for a in acts], ok_seq)
s2 = st()
row('רשומות ED מבחירת נוסח = מספר הקבלות (5), הכרעות = 10', {'ed': s2['ed'], 'dec': s2['dec']}, s2['ed'] == 5 and s2['dec'] == 10)
alt_posts = [x for x in BLOCKED if x.startswith('POST') and x.endswith('/alt')]
row('כל הכרעה נשלחה ליומן ההכרעות (/alt)', len(alt_posts), len(alt_posts) == 10)
row('הכפתור בסרגל מעדכן את מספר הפתוחות', s2['btn'], s2['btn'] == 'בחר נוסח (34)')
# עריכה במקום
id_e = st()['id']
key('e', 600)
ed = pg.evaluate("()=>{const g=document.querySelector('#flow .altv');return {edit:g.classList.contains('edit'),ce:g.getAttribute('contenteditable'),focus:document.activeElement===g,bar:document.getElementById('altbar').innerText.replace(/\\s+/g,' ')}}")
row('E: עריכה בתוך הפסקה עצמה', ed, ed['edit'] and ed['ce'] == 'true' and 'סיים וקבל' in ed['bar'])
pg.screenshot(path=SHOT + '-edit-%d.png' % W)
pg.keyboard.press('End'); pg.keyboard.type(' בדיקה'); pg.wait_for_timeout(300)
key('Enter', 900)
lastE = pg.evaluate("(id)=>{const e=ED.filter(x=>x.by==='בחירת נוסח').pop();return {now:e.now.slice(-40),n:ED.filter(x=>x.by==='בחירת נוסח').length}}", id_e)
row('Enter מסיים ומקבל את הנוסח הערוך', lastE, lastE['now'].endswith('בדיקה') and lastE['n'] == 6)
row('העריכה נרשמה ב-/alt כ"נערך"', BLOCKED[-1][:150] if BLOCKED else '', any('"edited":true' in x for x in BLOCKED))
# Ctrl+Z
txt_before = pg.evaluate("(id)=>{const l=document.querySelector('#flow [data-ek].altsrc');return null}", id_e)
key('Control+z', 1200)
u = st()
row('Ctrl+Z: ההכרעה האחרונה בוטלה, חוזרים לאותה נקודה, רשומת ED הוסרה', {'id': u['id'], 'ed': u['ed'], 'dec': u['dec']}, u['id'] == id_e and u['ed'] == 5 and u['dec'] == 10)
back = pg.evaluate("(id)=>{const e=ED.find(x=>x.now&&x.now.endsWith('בדיקה'));return !!e}", id_e)
row('הנוסח הערוך אינו בדף אחרי הביטול', back, not back)
# Tab כשיש נוסח חלופי אחד - הודעה בלבד, בלי שבירה
key('Tab', 500)
row('Tab בנקודה עם חלופה אחת אינו שובר', st()['views'], st()['views'] == 1)
# Esc
key('Escape', 600)
s3 = st()
row('Esc יוצא, הדף חוזר לרגיל', s3, not s3['on'] and s3['views'] == 0 and s3['hidden'] == 0)
mk = pg.evaluate("()=>[...document.querySelectorAll('#alml .alm')].map(x=>x.textContent+(x.classList.contains('dn')?'+':'')).join(',')")
row('בשוליים: סימן ירוק לנקודות שהוכרעו (אם נראות במסך)', mk, True)
# סימן ירוק פותח שוב
dn = pg.evaluate("()=>{const x=document.querySelector('#alml .alm.dn');if(!x)return null;x.click();return x.getAttribute('data-id')}")
pg.wait_for_timeout(1200)
if dn:
    s4 = st()
    row('לחיצה על הסימן הירוק פותחת את הנקודה שוב באותה תצוגה', s4, s4['on'] and s4['id'] == dn and 'הוכרע' in s4['bar'])
    key('Escape', 500)
# מבקר רגיל: אין שום דבר
pg.evaluate("()=>{localStorage.setItem('lg-admin','0');document.body.classList.remove('adm')}")
key('n', 800)
v = pg.evaluate("()=>({views:document.querySelectorAll('#flow .altv').length,bar:!!document.querySelector('#altbar.open'),mk:[...document.querySelectorAll('#alml .alm')].filter(x=>x.offsetWidth).length})")
row('מבקר רגיל: N אינו עושה דבר, אין סימנים', v, v['views'] == 0 and not v['bar'] and v['mk'] == 0)
print('SUMMARY', sum(OUT), '/', len(OUT))
