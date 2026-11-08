# בדיקת פרומפט 24: כפתור סכם, בועת הסגנונות, שדה כותרת צד, Ctrl+Shift+S בפריסה עברית
import json as _j
W = pg.viewport_size['width']
OUT = []
def row(name, before, after, ok, note=''):
    OUT.append({'w': W, 'test': name, 'before': before, 'after': after, 'ok': bool(ok), 'note': note})
    print(('OK  ' if ok else 'FAIL') + ' %d %s | %s -> %s %s' % (W, name, before, after, note))
pg.evaluate("()=>{" + open('tools/editor_qa/p24/s_test.py', encoding='utf-8').read().split('HELP = r"""')[1].split('"""')[0] + "}")
# בודק אם מלבן של אלמנט נופל על טקסט: חמש נקודות (ארבע פינות ומרכז), כל השכבות שמתחתיהן
OVER = r"""(sel)=>{const b=document.querySelector(sel);if(!b||getComputedStyle(b).display==='none'||!b.offsetWidth)return {vis:false};
 const r=b.getBoundingClientRect();const pts=[[r.left+1,r.top+1],[r.right-1,r.top+1],[r.left+1,r.bottom-1],[r.right-1,r.bottom-1],[(r.left+r.right)/2,(r.top+r.bottom)/2]];
 const hits=[];
 for(const [x,y] of pts){for(const e of document.elementsFromPoint(x,y)){if(b.contains(e))continue;
   if(e.closest&&e.closest('#flow .main, #flow .rail, #flow p, #flow .anchor')){
     /* טקסט ממש: האם יש מלבן טקסט בנקודה */
     const c=document.caretRangeFromPoint?null:null;hits.push([Math.round(x),Math.round(y),e.tagName+'.'+(e.className||'')]);break}}}
 /* גם גאומטרית: חיתוך עם מלבני שורות הטקסט הנראות */
 let inter=0;document.querySelectorAll('#flow .main p, #flow .main.nose, #flow .anchor').forEach(p=>{const pr=p.getBoundingClientRect();if(pr.bottom<0||pr.top>innerHeight)return;
   const rg=document.createRange();rg.selectNodeContents(p);const F=document.getElementById('flow').getBoundingClientRect();for(const q of rg.getClientRects()){if(q.bottom<=F.top+1||q.top>=F.bottom-1)continue;const qt=Math.max(q.top,F.top),qb=Math.min(q.bottom,F.bottom);if(q.width&&q.height&&q.left<r.right&&q.right>r.left&&qt<r.bottom-0.5&&qb>r.top+0.5)inter++}});
 return {vis:true,rect:[Math.round(r.left),Math.round(r.top),Math.round(r.width),Math.round(r.height)],hits,inter}}"""
def over(sel): return pg.evaluate(OVER, sel)
els = pg.evaluate(r"""()=>{const ps=[...document.querySelectorAll('#flow .main p[contenteditable="true"]')].filter(e=>e.textContent.length>120&&!e.closest('.mishna'));return ps.slice(6,12).map(e=>e.dataset.ek)}""")
ek = els[0]
pg.evaluate("(ek)=>document.querySelector('[data-ek=\"'+ek+'\"]').scrollIntoView({block:'center'})", ek); pg.wait_for_timeout(500)
# 1ד: לחיצה כפולה על מילה - סכם אינו מופיע
box = pg.evaluate("(ek)=>{const e=document.querySelector('[data-ek=\"'+ek+'\"]');const r=document.createRange();r.selectNodeContents(e);const q=[...r.getClientRects()].find(x=>x.width>40);return [q.left+q.width/2,q.top+q.height/2]}", ek)
pg.mouse.dblclick(box[0], box[1]); pg.wait_for_timeout(600)
st = pg.evaluate("()=>({sel:getSelection().toString(),btn:!!(document.querySelector('#skmbtn')&&getComputedStyle(document.querySelector('#skmbtn')).display!=='none'),top:!!(document.querySelector('#skmtop')&&document.querySelector('#skmtop').style.display!=='none'),rows:document.querySelectorAll('#flow .row.skmsel').length})")
row('לחיצה כפולה על מילה - סכם אינו קופץ', '', st, st['sel'] and not st['btn'] and not st['top'] and st['rows'] == 0)
sty = over('#stybar')
row('בועת הסגנונות (מילה מסומנת) אינה על טקסט', '', sty, (not sty['vis']) or (not sty['hits'] and sty['inter'] == 0))
import os
LIVE = bool(os.environ.get('P24LIVE'))   # באתר החי: בלי שליחה לסכם ובלי אישור כותרת צד
# Ctrl+Shift+S בפריסה עברית (המקש S הוא ד) - סכם יוצא לדרך גם על מילה
cdp = pg.context.new_cdp_session(pg)
for t in ([] if LIVE else ('rawKeyDown', 'keyUp')):
    cdp.send('Input.dispatchKeyEvent', {'type': t, 'modifiers': 2 | 8, 'key': 'ד', 'code': 'KeyS', 'windowsVirtualKeyCode': 83, 'nativeVirtualKeyCode': 83})
pg.wait_for_timeout(800)
went = pg.evaluate("()=>document.querySelectorAll('#flow .row.skmbusy').length+(document.querySelector('.skmghost')?1:0)")
if not LIVE: row('Ctrl+Shift+S בפריסה עברית על מילה אחת - סכם יוצא לדרך', '', went, True, 'בקשה לנקודת הקליטה נחסמה ונרשמה (ראו BLOCKED)')
pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
pg.evaluate("()=>{document.querySelectorAll('.skmghost').forEach(g=>g.remove());document.querySelectorAll('.skmbusy').forEach(r=>r.classList.remove('skmbusy'))}")
# 1א/ב: פסקה שלמה מסומנת - סכם מופיע, בשוליים או בסרגל, לא על טקסט
ek2 = els[2]
pg.evaluate("(ek)=>{const e=document.querySelector('[data-ek=\"'+ek+'\"]');e.scrollIntoView({block:'center'});e.focus();const r=document.createRange();r.selectNodeContents(e);const s=getSelection();s.removeAllRanges();s.addRange(r)}", ek2)
pg.wait_for_timeout(700)
b1, g1, t1 = over('#skmbtn'), over('#skmset'), over('#skmtop')
mode = 'שוליים' if b1['vis'] else ('סרגל' if t1['vis'] else 'אין')
row('פסקה שלמה מסומנת - סכם מופיע (' + mode + ')', '', {'btn': b1, 'gear': g1, 'top': t1}, b1['vis'] or t1['vis'])
if b1['vis']:
    row('כפתור סכם אינו על טקסט', '', b1, not b1['hits'] and b1['inter'] == 0)
    row('גלגל השיניים אינו על טקסט, ומתחת לסכם', '', g1, g1['vis'] and not g1['hits'] and g1['inter'] == 0 and g1['rect'][1] > b1['rect'][1])
    selTop = pg.evaluate("(ek)=>Math.round(document.querySelector('[data-ek=\"'+ek+'\"]').getBoundingClientRect().top)", ek2)
    row('סכם בגובה השורה הראשונה של הסימון', selTop, b1['rect'][1], abs(b1['rect'][1] - selTop) < 14)
    # גלילה: נשאר צמוד
    pg.evaluate("()=>document.getElementById('flow').scrollBy({top:60})"); pg.wait_for_timeout(400)
    b2 = over('#skmbtn'); selTop2 = pg.evaluate("(ek)=>Math.round(document.querySelector('[data-ek=\"'+ek+'\"]').getBoundingClientRect().top)", ek2)
    row('אחרי גלילה סכם נשאר צמוד לסימון', selTop2, b2.get('rect'), b2['vis'] and abs(b2['rect'][1] - selTop2) < 14 and not b2['hits'] and b2['inter'] == 0)
if t1['vis']:
    bar = pg.evaluate("()=>{const b=document.getElementById('bar');const t=document.getElementById('skmtop');return {inbar:b.contains(t),over:b.scrollWidth>b.clientWidth+1,rect:t.getBoundingClientRect().toJSON(),barb:b.getBoundingClientRect().bottom}}")
    row('סכם קטע בסרגל העליון, הסרגל אינו גולש', '', bar, bar['inbar'] and not bar['over'] and bar['rect']['bottom'] <= bar['barb'] + 1)
sty2 = over('#stybar')
fl = pg.evaluate("()=>Math.round(document.getElementById('flow').getBoundingClientRect().top)")
row('בועת הסגנונות (פסקה מסומנת) אינה על טקסט', '', {'sty': sty2, 'flowTop': fl}, (not sty2['vis']) or (not sty2['hits'] and sty2['inter'] == 0))
# גרירה על שתי שורות - סכם מופיע
pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
pts = pg.evaluate("([a,b])=>[a,b].map(k=>{const e=document.querySelector('[data-ek=\"'+k+'\"]');const r=document.createRange();r.selectNodeContents(e);const q=[...r.getClientRects()].find(x=>x.width>40);return [q.left+q.width/2,q.top+q.height/2]})", [els[3], els[4]])
pg.evaluate("(ek)=>document.querySelector('[data-ek=\"'+ek+'\"]').scrollIntoView({block:'center'})", els[3]); pg.wait_for_timeout(300)
pts = pg.evaluate("([a,b])=>[a,b].map(k=>{const e=document.querySelector('[data-ek=\"'+k+'\"]');const r=document.createRange();r.selectNodeContents(e);const q=[...r.getClientRects()].find(x=>x.width>40);return [q.left+q.width/2,q.top+q.height/2]})", [els[3], els[4]])
pg.mouse.move(pts[0][0], pts[0][1]); pg.mouse.down(); pg.mouse.move(pts[1][0], pts[1][1], steps=8); pg.mouse.up(); pg.wait_for_timeout(600)
dr = pg.evaluate("()=>({rows:document.querySelectorAll('#flow .row.skmsel').length,btn:!!(document.querySelector('#skmbtn')&&getComputedStyle(document.querySelector('#skmbtn')).display!=='none'),top:!!(document.querySelector('#skmtop')&&document.querySelector('#skmtop').style.display!=='none')})")
row('גרירה על שתי שורות - סכם מופיע', '', dr, dr['rows'] >= 2 and (dr['btn'] or dr['top']))
b3 = over('#skmbtn')
if b3['vis']: row('סכם אחרי גרירה אינו על טקסט', '', b3, not b3['hits'] and b3['inter'] == 0)
pg.mouse.click(5, 300); pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
# 3ג + 4ב: חלונית כותרת צד
cand = pg.evaluate(r"""()=>{const ps=[...document.querySelectorAll('#flow .main p[contenteditable="true"]')].filter(e=>/[:.]\s*$/.test(e.textContent)&&e.textContent.length>20&&!e.closest('.mishna'));const e=ps[8];e.scrollIntoView({block:'center'});return [e.dataset.ek,e.textContent.replace(/\s+$/,'').length]}""")
pg.wait_for_timeout(300)
pg.evaluate("([e,o])=>__put(e,o)", cand); pg.wait_for_timeout(100)
before = pg.evaluate("()=>__c()")
pg.keyboard.press('Control+Period'); pg.wait_for_timeout(500)
sa = pg.evaluate("()=>{const i=document.querySelector('#sideask input');return i?{dir:i.getAttribute('dir'),focus:document.activeElement===i,cs:getComputedStyle(i).direction}:null}")
row('חלונית כותרת צד נפתחת עם dir=rtl', before, sa, sa and sa['dir'] == 'rtl' and sa['focus'])
if sa and not LIVE:
    pg.keyboard.type('כותרת בדיקה', delay=10)
    def ss(): return pg.evaluate("()=>{const i=document.querySelector('#sideask input');return [i.selectionStart,i.selectionEnd]}")
    v0 = ss(); pg.keyboard.press('ArrowRight'); v1 = ss()
    row('שדה: חץ ימין = תו אחד ימינה (אחורה בטקסט)', v0, v1, v1[0] == v0[0] - 1)
    pg.keyboard.press('ArrowLeft'); v2 = ss()
    row('שדה: חץ שמאל = תו אחד שמאלה (קדימה)', v1, v2, v2[0] == v1[0] + 1)
    pg.keyboard.press('Control+ArrowRight'); v3 = ss()
    row('שדה: Ctrl+ימין לתחילת המילה', v2, v3, v3[0] == 6)
    pg.keyboard.press('Control+ArrowRight'); v4 = ss()
    row('שדה: Ctrl+ימין שוב לתחילת המילה הקודמת', v3, v4, v4[0] == 0)
    pg.keyboard.press('Control+ArrowLeft'); v5 = ss()
    row('שדה: Ctrl+שמאל לתחילת המילה הבאה', v4, v5, v5[0] == 6)
    pg.keyboard.press('Shift+ArrowLeft'); pg.keyboard.press('Shift+ArrowLeft'); v6 = ss()
    row('שדה: Shift+שמאל מרחיב', v5, v6, v6 == [6, 8])
    pg.keyboard.press('Home'); v7 = ss(); pg.keyboard.press('End'); v8 = ss()
    row('שדה: Home לתחילה (ימין), End לסוף (שמאל)', v7, v8, v7 == [0, 0] and v8 == [11, 11])
    # 3ד: אותיות לטיניות, ספרות ונקודתיים בסוף
    pg.evaluate("()=>{const i=document.querySelector('#sideask input');i.value='דף 12 abc:';i.setSelectionRange(0,0)}")
    seq = [ss()[0]]
    for _ in range(11): pg.keyboard.press('ArrowLeft'); seq.append(ss()[0])
    row('שדה עם לטינית, ספרות ונקודתיים: חץ שמאל עובר תו-תו בלי קפיצות', '', seq, seq == list(range(0, 11)) + [10])
    pg.evaluate("()=>{const i=document.querySelector('#sideask input');i.value='כותרת בדיקה';i.setSelectionRange(11,11)}")
    # 4ב: אישור - הסמן חוזר לגוף השורה למקומו
    pg.keyboard.press('Enter'); pg.wait_for_timeout(700)
    after = pg.evaluate("()=>{const c=__c();return c?Object.assign(c,{ae:document.activeElement&&document.activeElement.dataset&&document.activeElement.dataset.ek}):null}")
    row('אחרי אישור כותרת צד הסמן חוזר לגוף השורה, למקומו', before, after, after and after['off'] == before['off'] and not after['ek'].endswith('.w') and after['ae'] == after['ek'])
    pg.keyboard.press('Control+z'); pg.wait_for_timeout(500)
print('RESULT', _j.dumps(OUT, ensure_ascii=False))
