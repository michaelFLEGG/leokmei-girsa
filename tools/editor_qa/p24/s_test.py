# בדיקת פרומפט 24 בדפדפן: מקלדת אמיתית (אירועי CDP), מדידת הסמן לפני ואחרי כל מקש.
import json as _j
W = pg.viewport_size['width']
OUT = []
def row(name, before, after, ok, note=''):
    OUT.append({'w': W, 'test': name, 'before': before, 'after': after, 'ok': bool(ok), 'note': note})
    print(('OK  ' if ok else 'FAIL') + ' %d %s | %s -> %s %s' % (W, name, before, after, note))

HELP = r"""
window.__c=()=>{const s=getSelection();if(!s.rangeCount)return null;const h=(s.focusNode.nodeType===3?s.focusNode.parentElement:s.focusNode).closest('[contenteditable="true"]');
 const r=document.createRange();r.setStart(s.focusNode,s.focusOffset);r.collapse(true);let b=[...r.getClientRects()].find(x=>x.height>0);
 if(!b&&s.focusNode.nodeType===3&&s.focusOffset<s.focusNode.length){r.setEnd(s.focusNode,s.focusOffset+1);const q=[...r.getClientRects()].find(x=>x.height>0);if(q)b={left:q.right,top:q.top}}
 const pre=document.createRange();pre.setStart(h,0);pre.setEnd(s.focusNode,s.focusOffset);
 return {ek:h&&h.dataset.ek,off:pre.toString().length,x:b?Math.round(b.left):null,y:b?Math.round(b.top):null,col:s.isCollapsed,len:h?h.textContent.length:0}};
window.__put=(ek,off)=>{const e=document.querySelector('[data-ek="'+ek+'"]');e.focus();const w=document.createTreeWalker(e,NodeFilter.SHOW_TEXT);let t,left=off;
 while((t=w.nextNode())){if(left<=t.length){const s=getSelection();s.collapse(t,left);return true}left-=t.length}return false};
window.__lines=(ek)=>{const e=document.querySelector('[data-ek="'+ek+'"]');const r=document.createRange();r.selectNodeContents(e);
 const L=[];[...r.getClientRects()].filter(x=>x.height>0&&x.width>0).forEach(x=>{const m=(x.top+x.bottom)/2;if(!L.some(l=>Math.abs(l-m)<5))L.push(m)});return L.length};
"""
pg.evaluate("()=>{" + HELP + "}")
# פסקאות לבדיקה: חד-שורתיות ורב-שורתיות בגוף, ברצף
info = pg.evaluate(r"""()=>{const els=[...document.querySelectorAll('#flow .main p[contenteditable="true"]')];
 const pick=[];for(let i=40;i<els.length-3&&pick.length<1;i++){const a=els[i],b=els[i+1],c=els[i+2];
   if(__lines(a.dataset.ek)===1&&__lines(b.dataset.ek)===1&&__lines(c.dataset.ek)>=2&&a.textContent.length>30&&b.textContent.length>30)pick.push([a.dataset.ek,b.dataset.ek,c.dataset.ek])}
 const multi=els.slice(30).find(e=>__lines(e.dataset.ek)>=3);
 return {trio:pick[0],multi:multi&&multi.dataset.ek}}""")
print('targets', info)
a, b, c = info['trio']
pg.evaluate("(ek)=>document.querySelector('[data-ek=\"'+ek+'\"]').scrollIntoView({block:'center'})", a)
pg.wait_for_timeout(400)
K = pg.keyboard
def cur(): return pg.evaluate("()=>__c()")
def put(ek, off): pg.evaluate("([e,o])=>__put(e,o)", [ek, off]); pg.wait_for_timeout(60)
def press(k): K.press(k); pg.wait_for_timeout(120)

# 2א: חץ למטה בשורה של שורה אחת - לחיצה אחת יורדת שורה
put(a, 25); x0 = cur(); press('ArrowDown'); x1 = cur()
row('חץ למטה משורה חד-שורתית', x0, x1, x1['ek'] == b and x1['y'] > x0['y'] and abs(x1['x'] - x0['x']) < 25)
press('ArrowDown'); x2 = cur()
row('חץ למטה שני - לפסקה הבאה', x1, x2, x2['ek'] == c and x2['y'] > x1['y'])
press('ArrowDown'); x3 = cur()
row('חץ למטה בתוך פסקה רב-שורתית - שורה אחת', x2, x3, x3['ek'] == c and x3['y'] > x2['y'] and x3['y'] - x2['y'] < 60)
press('ArrowUp'); press('ArrowUp'); press('ArrowUp'); x4 = cur()
row('שלוש פעמים חץ למעלה - חזרה לנקודה המקורית (עמודה נשמרת)', x0, x4, x4['ek'] == a and abs(x4['x'] - x0['x']) < 14)
put(b, 5); y0 = cur(); press('ArrowUp'); y1 = cur()
row('חץ למעלה משורה חד-שורתית', y0, y1, y1['ek'] == a and y1['y'] < y0['y'])
# 2ג: Shift+חץ למטה
put(a, 10); s0 = cur(); K.down('Shift'); press('ArrowDown'); press('ArrowDown'); K.up('Shift')
sel = pg.evaluate(r"""()=>{const s=getSelection();const rows=[...document.querySelectorAll('#flow .row.skmsel')].map(r=>r.id);
 return {anc:(s.anchorNode.nodeType===3?s.anchorNode.parentElement:s.anchorNode).closest('[contenteditable]').dataset.ek,foc:(s.focusNode.nodeType===3?s.focusNode.parentElement:s.focusNode).closest('[contenteditable]').dataset.ek,text:s.toString().length,skm:rows}}""")
row('Shift+חץ למטה פעמיים - הבחירה מתרחבת שתי שורות', s0, sel, sel['foc'] == c or len(sel['skm']) >= 2)
press('Escape'); put(a, 3)
# 3: ימין/שמאל
put(c, 20); r0 = cur(); press('ArrowRight'); r1 = cur()
row('חץ ימין זז ימינה', r0, r1, r1['x'] > r0['x'] and r1['off'] == r0['off'] - 1)
press('ArrowLeft'); press('ArrowLeft'); r2 = cur()
row('חץ שמאל זז שמאלה', r1, r2, r2['x'] < r1['x'] and r2['off'] == r1['off'] + 2)
# 3ב: Ctrl+חץ
txt = pg.evaluate("(ek)=>document.querySelector('[data-ek=\"'+ek+'\"]').textContent", c)
import re
starts = [m.start() for m in re.finditer(r'[^\s\-־]+', txt) if re.search(r'[א-ת0-9A-Za-z]', m.group())]
mid = starts[3] + 1
put(c, mid); w0 = cur(); K.press('Control+ArrowLeft'); pg.wait_for_timeout(120); w1 = cur()
row('Ctrl+שמאל - לתחילת המילה הבאה', w0, w1, w1['off'] == starts[4])
K.press('Control+ArrowRight'); pg.wait_for_timeout(120); w2 = cur()
row('Ctrl+ימין מתחילת מילה - לתחילת הקודמת', w1, w2, w2['off'] == starts[3])
put(c, mid); K.press('Control+ArrowRight'); pg.wait_for_timeout(120); w3 = cur()
row('Ctrl+ימין מאמצע מילה - לתחילת הנוכחית', {'off': mid}, w3, w3['off'] == starts[3])
# קצה שורה: Ctrl+שמאל בסוף, Ctrl+ימין בתחילה
put(a, pg.evaluate("(ek)=>document.querySelector('[data-ek=\"'+ek+'\"]').textContent.length", a)); e0 = cur()
K.press('Control+ArrowLeft'); pg.wait_for_timeout(150); e1 = cur()
row('Ctrl+שמאל בסוף שורה - תחילת המילה הראשונה בשורה הבאה', e0, e1, e1['ek'] == b and e1['off'] <= 2)
K.press('Control+ArrowRight'); pg.wait_for_timeout(150); e2 = cur()
row('Ctrl+ימין בתחילת שורה - תחילת המילה האחרונה בשורה הקודמת', e1, e2, e2['ek'] == a and e2['off'] > 0)
# Shift+חץ בקצה
put(a, pg.evaluate("(ek)=>document.querySelector('[data-ek=\"'+ek+'\"]').textContent.length", a)); g0 = cur()
K.press('Shift+ArrowLeft'); pg.wait_for_timeout(250)
g1 = pg.evaluate(r"""()=>({skm:[...document.querySelectorAll('#flow .row.skmsel')].map(r=>r.id),foc:(getSelection().focusNode.nodeType===3?getSelection().focusNode.parentElement:getSelection().focusNode).closest('[contenteditable]').dataset.ek})""")
row('Shift+שמאל בסוף שורה - הבחירה עוברת לשורה הבאה', g0, g1, g1['foc'] == b or len(g1['skm']) >= 2)
press('Escape')
# 4א: Home/End בשורה
m = info['multi']
pg.evaluate("(ek)=>document.querySelector('[data-ek=\"'+ek+'\"]').scrollIntoView({block:'center'})", m); pg.wait_for_timeout(300)
put(m, 3); press('ArrowDown'); h0 = cur(); press('Home'); h1 = cur(); press('End'); h2 = cur()
row('Home - תחילת השורה החזותית (לא הפסקה)', h0, h1, h1['y'] == h0['y'] and h1['off'] > 0 and h1['x'] >= h0['x'])
press('Home'); K.press('Shift+End'); pg.wait_for_timeout(150)
ln = pg.evaluate(r"""()=>{const s=getSelection(),r=s.getRangeAt(0);const rs=[...r.getClientRects()].filter(x=>x.width>0);return {len:s.toString().length,tops:rs.reduce((a,x)=>a.some(t=>Math.abs(t-x.top)<4)?a:a.concat([x.top]),[]).length}}""")
row('End - סוף השורה החזותית (Shift+End מסמן בדיוק שורה אחת)', h1, dict(h2, sel=ln), h2['off'] > h1['off'] and h2['off'] < h2['len'] and ln['tops'] == 1 and ln['len'] > 5)
press('ArrowRight')
print('RESULT', _j.dumps(OUT, ensure_ascii=False))
