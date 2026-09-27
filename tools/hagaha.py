# -*- coding: utf-8 -*-
"""hagaha.py - בונה מסך הגהה למסכת.

הוא מאחד שני מקורות: ממצאים שנרשמו ביד בקובץ data/hagaha-<slug>.json,
וממצאים שהגלאים שכאן מוצאים בעצמם בכל בנייה. כל ממצא נקשר ליחידה שבדף
המסכת, כדי שלחיצה תביא את המגיה אל המקום עצמו.

הגלאים נבנו מן הטעויות שנמצאו בקריאת סוכה, ולכן הם מכוונים לסימני-הקיצור
שבספר הזה: גרש יחיד במקום גרשיים, גרש סוגר בלא פותח, יו"ד כפולה, קו נטוי.
מילה שנחתכה בגרש כדרך הקיצור הרגילה ('ואפי, 'מתני) אינה ממצא, ולכן היא
רשומה ברשימת ההיתר שלהלן.
"""
import json, re, html, os, sys, datetime, collections, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from styles_map import ROLE

HEB = 'א-ת'
# הכרעת בעל הפרויקט 27.9.2026: בספר הזה גרש בודד משמש גם לסגור מילה
# שנחתכה (סנהד' במקום סנהדרין), ולא רק לראשי תיבות. לכן זה אינו ממצא.
SKIP_TRUNC = {'אמרי', 'אפי', 'דאפי', 'ואפי', 'שאפי', 'גזרי', 'ילפי', 'דבעי', 'בעי', 'מתני',
              'דממתני', 'ותרצי', 'כדחזי', 'חזי', 'ודחי', 'דחי', 'ומספקי', 'מספקי', 'וספינ',
              'חיישי', 'מיירי', 'אמרינ', 'קמ', 'דמצי', 'מצי', 'סנהד', 'דתני', 'דאמרי',
              'בחצצרות', 'דאמרינ', 'ומתני', 'כדאמרי'}

# המפה יושבת בקובץ אחד, styles_map.py, ששני המסכים קוראים ממנו.
# כך פסקה נופלת לאותה יחידה בדיוק בשני הצדדים, והעיגון אינו נשבר.


def _locate(blocks):
    """לכל פסקה: באיזה עמוד היא, ותחת איזו יחידה היא מוצגת בדף המסכת."""
    loc = {}
    pi, unit, uid = -1, None, 0
    pend = []          # פסקאות שאין להן עדיין יחידה (ציון דף, ופתיח שלפני הדף הראשון)
    for b in blocks:
        r = ROLE.get(b['style'], 'body')
        if r == 'daf':
            pi += 1; unit = None; pend.append(b['i']); continue
        if pi < 0:
            pend.append(b['i']); continue
        if r == 'anchor':
            unit, uid = 'u', b['i']
        elif r.startswith('body'):
            if unit != 'u': unit, uid = 'u', b['i']
        elif r == 'mishna':
            if unit != 'm': unit, uid = 'm', b['i']
        else:
            unit, uid = None, b['i']
        loc[b['i']] = (pi, uid)
        # ציון דף אינו יחידה בפני עצמה בדף המסכת, ולכן הוא נתלה ביחידה
        # הראשונה שאחריו - שם הוא מוצג בפועל.
        for j in pend:
            loc[j] = (max(pi, 0), uid)
        pend = []
    for j in pend:
        loc[j] = (max(pi, 0), uid)
    return loc


GEM = {'א':1,'ב':2,'ג':3,'ד':4,'ה':5,'ו':6,'ז':7,'ח':8,'ט':9,'י':10,'כ':20,'ל':30,'מ':40,
       'נ':50,'ס':60,'ע':70,'פ':80,'צ':90,'ק':100,'ר':200,'ש':300,'ת':400}


def daf_key(d):
    """מפתח מספרי לציון דף: גימטריה כפול שתיים, ועוד אחד לעמוד ב."""
    if not d:
        return None
    t = d.strip()
    amud = 1 if t.endswith(':') else 0
    t = t.rstrip('.:').replace('"', '').replace("'", '').replace('״', '').replace('׳', '').strip()
    n = sum(GEM.get(c, 0) for c in t)
    return n * 2 + amud if n else None


def ctx_of(text, mark, span=20):
    """כ-40 תווים סביב הסימון, כלשונם בקובץ. זהו העוגן היציב של הממצא."""
    if not mark:
        return text.strip()[:60]
    k = text.find(mark)
    if k < 0:
        return text.strip()[:60]
    return text[max(0, k - span):k + len(mark) + span]


def _norm(s):
    """נרמול לצורך התאמה בלבד: רצף רווחים וטאבים נעשה רווח אחד."""
    return re.sub(r'\s+', ' ', s).strip()


def fid(slug, kind, mark, context):
    """מזהה יציב לממצא. אינו תלוי במספר הפסקה, ולכן הוא שורד בנייה מחדש,
    מחיקת פסקה, והוספת פסקה. הסימונים של בעל הפרויקט נצמדים אליו."""
    raw = '|'.join((slug, kind or '', mark or '', _norm(context or '')))
    return hashlib.blake2s(raw.encode('utf-8'), digest_size=5).hexdigest()


def anchor(blocks, rec):
    """מאתר את הפסקה שבה הממצא יושב, לפי ההקשר, בתוך אותו דף ועמוד אחד
    לכל צד. לא נמצא - מוחזר None, והממצא עובר לחלק "שלא אותרו". לעולם
    אינו נתלה בשורה אחרת: זו היתה התקלה של העיגון לפי מספר פסקה."""
    ctx = rec.get('context') or ''
    mark = rec.get('mark') or ''
    k0 = daf_key(rec.get('daf'))
    if k0 is None:
        win = blocks
    else:
        win = [b for b in blocks
               if daf_key(b.get('daf')) is not None and abs(daf_key(b['daf']) - k0) <= 1]
        if not win:
            win = blocks
    hint = rec.get('i')

    def pick(cands, how):
        if not cands:
            return None
        if len(cands) > 1 and hint is not None:
            cands = sorted(cands, key=lambda b: abs(b['i'] - hint))
        return cands[0], how

    if ctx:
        r = pick([b for b in win if ctx in b['text']], 'ctx')
        if r:
            return r
        nc = _norm(ctx)
        r = pick([b for b in win if nc and nc in _norm(b['text'])], 'ctx~')
        if r:
            return r
    if mark:
        cands = [b for b in win if mark in b['text']]
        if len(cands) == 1:
            return cands[0], 'mark'
    return None


def _auto(blocks):
    """הגלאים האוטומטיים. מחזיר רשימת רשומות-ממצא."""
    out = []

    def add(sev, kind, b, note, fix, mark):
        out.append({'sev': sev, 'kind': kind, 'i': b['i'], 'note': note, 'fix': fix,
                    'mark': mark, 'daf': b.get('daf') or '',
                    'context': ctx_of(b['text'], mark), 'src': 'auto'})

    for b in blocks:
        t = b['text']
        # גרש יחיד בתוך ראשי-תיבות: הקב'ה, לת'ק, יד'ח
        for m in re.finditer(r"(?<![%s])([%s]{1,7})'([%s]{1,3})(?![%s'])" % (HEB, HEB, HEB, HEB), t):
            tok = m.group(0)
            # אות בודדת לפני הגרש היא דו-משמעית: או אות-שימוש הפותחת ציטוט
            # ("מ'פני הכפורת"), או ראשי תיבות. שם אין הכרעה, ורק מסמנים.
            if len(m.group(1)) == 1:
                add('קל', 'סימני קיצור', b,
                    'גרש יחיד אחרי אות בודדת ב"%s" - ראשי תיבות, או פתיחת ציטוט?' % tok,
                    'אם ראשי תיבות - גרשיים; אם ציטוט - להשלים את הגרש הסוגר', tok)
            else:
                add('בינוני', 'סימני קיצור', b,
                    'ראשי התיבות "%s" נכתבו בגרש יחיד ולא בגרשיים' % tok,
                    tok + ' ⟵ ' + tok.replace("'", '"'), tok)
        # גרש סוגר בלא פותח על מילה מלאה
        for m in re.finditer(r"(?<![%s\"'])([%s]{4,})'(?![%s'])" % (HEB, HEB, HEB), t):
            w = m.group(1)
            if w in SKIP_TRUNC:
                continue
            if t[:m.start()].count("'") % 2:
                continue
            add('קל', 'סימני קיצור', b,
                'גרש סוגר אחרי "%s" - קיצור של המילה, או ציטוט שחסר לו גרש פותח?' % w,
                'אם ציטוט - להוסיף גרש פותח בראשו', m.group(0))
        # יו"ד כפולה בראש ראשי-תיבות
        for m in re.finditer(r'(?<![%s])יי[%s]{0,3}["״]' % (HEB, HEB), t):
            add('בינוני', 'שגיאת כתיב', b,
                'יו"ד כפולה בראש ראשי התיבות "%s"' % m.group(0),
                m.group(0) + ' ⟵ ' + m.group(0)[1:], m.group(0))
        # קו נטוי בתוך מילה עברית
        for m in re.finditer(r'[%s]/' % HEB, t):
            add('בינוני', 'שגיאת כתיב', b,
                'קו נטוי בתוך מילה עברית - כנראה במקום גרש', 'להחליף בגרש', m.group(0))
        # פיסוק בלא רווח אחריו
        for m in re.finditer(r'[%s][:,][%s]' % (HEB, HEB), t):
            add('קל', 'פיסוק', b, 'סימן פיסוק בלא רווח אחריו', 'להוסיף רווח', m.group(0))
        # פסקה ריקה
        if not t.strip() and b['style'] != 'חציצה':
            add('קל', 'פסקה ריקה', b, 'פסקה ריקה בסגנון "%s"' % b['style'],
                'למחוק, או להשלים את התוכן', '')
    return out


CSS = r'''
@font-face{font-family:'Frank';src:url(fonts/frank.ttf);font-display:swap}
@font-face{font-family:'Vilna';src:url(fonts/vilna-b.otf);font-weight:700;font-display:swap}
@font-face{font-family:'Vilna';src:url(fonts/vilna-xb.otf);font-weight:900;font-display:swap}
@font-face{font-family:'VilnaG';src:url(fonts/vilna-g.ttf);font-display:swap}
@font-face{font-family:'Leukmey';src:url(fonts/leukmey.otf);font-display:swap}
:root{--ink:#1d1a16;--paper:#fbf8f1;--grey:#8a7d66;--gold:#c9a24a;--red:#a83c2f;--line:#e0d8c4}
*{box-sizing:border-box}
html,body{margin:0;background:#e9e4d8;color:var(--ink);font-family:'Frank','Frank Ruhl Libre',serif}
.bar{position:sticky;top:0;z-index:9;display:flex;flex-wrap:wrap;gap:6px 12px;align-items:center;
     padding:9px 14px;background:#2b2620;color:#f1ead9;font-size:15px}
.bar .nm{font-family:'Leukmey','Vilna',serif;font-size:21px;line-height:1}
.bar a{color:#f1ead9;text-decoration:none;border-bottom:1px dotted #7a6f5c}
.bar a.nl{border:0}
.bar .sp{flex:1}
.bar button{font:inherit;background:#4a4137;color:#f1ead9;border:0;border-radius:4px;padding:4px 11px;cursor:pointer}
.bar button.on{background:var(--gold);color:#2b2620}
main{max-width:940px;margin:0 auto;padding:16px 14px 70px}
.lead{background:var(--paper);border:1px solid var(--line);border-radius:8px;padding:14px 18px;margin-bottom:14px;line-height:1.65}
.lead h1{font-family:'Vilna',serif;font-weight:900;font-size:26px;margin:0 0 6px}
.lead p{margin:6px 0}
.ban{background:#e8efe3;border-right:4px solid #4a6b3f;border-radius:5px;padding:9px 13px;margin:9px 0;line-height:1.55}
.counts{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0 4px}
.cbox{background:var(--paper);border:1px solid var(--line);border-radius:6px;padding:7px 14px;font-size:14px;text-align:center}
.cbox b{font-size:21px;display:block;font-family:'Vilna',serif;font-weight:900}
.f{background:var(--paper);border:1px solid var(--line);border-right:5px solid var(--grey);border-radius:7px;
   padding:12px 15px;margin:9px 0;line-height:1.6}
.f.s0{border-right-color:var(--red)} .f.s1{border-right-color:var(--gold)} .f.s2{border-right-color:#b9b099}
.f.done{opacity:.52}
.f.lost{border-right-color:#8a5a2f;background:#fdf6ec}
h2.warn{color:#8a5a2f}
.tag.warn{background:#f2e3cf;color:#8a5a2f}
.mig{display:none;background:#fdf1d8;border-right:4px solid var(--gold);border-radius:5px;padding:9px 13px;margin:9px 0;line-height:1.55}
.f .hd{display:flex;flex-wrap:wrap;gap:8px;align-items:baseline;margin-bottom:5px}
.daf{font-family:'VilnaG','Vilna',serif;color:var(--red);font-size:19px;min-width:44px}
.tag{background:#eeeae1;border-radius:4px;padding:1px 9px;font-size:13px;color:#5a5044}
.note{font-size:16px}
.st{border-radius:4px;padding:1px 9px;font-size:13px;font-weight:700}
.st.ok{background:#4a6b3f;color:#fff} .st.no{background:#8a7d66;color:#fff} .st.wait{background:#c9a24a;color:#2b2620}
.bulk{display:flex;flex-wrap:wrap;gap:8px;margin-top:11px}
.bulk button{font:inherit;font-size:15px;background:#4a6b3f;color:#fff;border:0;border-radius:5px;padding:7px 15px;cursor:pointer}
.bulk button:hover{background:#3d5a34}
.quote{background:#fff;border:1px dashed var(--line);border-radius:5px;padding:8px 11px;margin:7px 0;font-size:17px;white-space:pre-wrap}
.quote mark{background:#ffe27a;color:inherit;padding:0 2px;border-radius:2px}
.fix{color:#4a6b3f;font-size:15px}
.fix b{font-family:'Vilna',serif;font-weight:700}
.act{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin-top:9px}
.act button{font:inherit;font-size:14px;background:#eeeae1;border:1px solid var(--line);border-radius:5px;padding:4px 12px;cursor:pointer;color:#4a4137}
.act button.on{background:var(--gold);border-color:#a8842f;color:#2b2620;font-weight:700}
.act a{font-size:14px;color:#2e3f6b;text-decoration:none;border-bottom:1px dotted}
.act textarea{font:inherit;font-size:15px;flex:1 1 240px;min-height:34px;border:1px solid var(--line);border-radius:5px;padding:5px 8px;background:#fff;resize:vertical}
h2{font-family:'Vilna',serif;font-weight:700;font-size:20px;color:#5a5044;border-bottom:1px solid #c9bfa8;margin:26px 0 8px;padding-bottom:4px}
.gen{background:var(--paper);border:1px solid var(--line);border-radius:7px;padding:12px 15px;margin:9px 0;line-height:1.6}
.gen b{font-family:'Vilna',serif;font-size:17px;font-weight:700}
.gen .n{color:var(--red);font-family:'VilnaG','Vilna',serif;font-size:19px}
footer{text-align:center;color:var(--grey);font-size:13px;padding:24px}
@media(max-width:700px){main{padding:12px 10px 60px}.bar{font-size:14px}}
@media print{.bar,.act{display:none}body{background:#fff}}
'''

JS = r'''
/* מפתח האחסון עבר לגרסה 2 בעקבות המעבר למזהה יציב. הסימונים הישנים
   נשענו על מקום הממצא ברשימה, ואחרי שנמחקו ממצאים הם נצמדו לממצא אחר -
   ולכן אינם מועברים, וזה נאמר במפורש פעם אחת. */
const K='lg-hg2-'+SLUG, KOLD='lg-hagaha-'+SLUG;
let ST={};try{ST=JSON.parse(localStorage.getItem(K)||'{}')}catch(e){ST={}}
/* הכרעות ששמורות במאגר נזרעות פעם אחת, ואינן דורסות סימון טרי שבדפדפן */
for(const f of D){if(f.seed&&!ST[f.id])ST[f.id]={s:f.seed,n:f.seedn||''}}
function save(){try{localStorage.setItem(K,JSON.stringify(ST))}catch(e){}}
function esc(s){return s.replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}
const SEV=['חמור','בינוני','קל'];
function mk(text,m){const t=esc(text);if(!m)return t;const e=esc(m);
  const k=t.indexOf(e);if(k<0)return t;return t.slice(0,k)+'<mark>'+e+'</mark>'+t.slice(k+e.length)}
function card(f,lost){const st=ST[f.id]||{};
  return '<div class="f s'+SEV.indexOf(f.sev)+(lost?' lost':'')+(st.s&&st.s!=='עיון'?' done':'')+'" id="f'+f.id+'">'
   +'<div class="hd"><span class="daf">'+esc(f.daf)+'</span><span class="tag">'+esc(f.kind)+'</span>'
   +(f.how==='mark'?'<span class="tag warn">אותר לפי הסימון בלבד</span>':'')
   +(st.s?'<span class="st '+(st.s==='אושר'?'ok':st.s==='נדחה'?'no':'wait')+'">'+(st.s==='אושר'?'לתיקון':st.s)+'</span>':'')+'</div>'
   +'<div class="note">'+esc(f.note)+'</div>'
   +'<div class="quote">'+mk(f.text.replace(/\t/g,'   ').trim(),f.mark)+'</div>'
   +(f.fix?'<div class="fix">הצעת התיקון: <b>'+esc(f.fix)+'</b></div>':'')
   +'<div class="act">'
   +'<button onclick="set(&quot;'+f.id+'&quot;,&quot;אושר&quot;)" class="'+(st.s==='אושר'?'on':'')+'">תקן</button>'
   +'<button onclick="set(&quot;'+f.id+'&quot;,&quot;נדחה&quot;)" class="'+(st.s==='נדחה'?'on':'')+'">דחה תיקון</button>'
   +'<button onclick="set(&quot;'+f.id+'&quot;,&quot;עיון&quot;)" class="'+(st.s==='עיון'?'on':'')+'">לעיון</button>'
   +(lost?'':'<a href="'+SLUG+'.html#u='+f.u+'" target="_blank">לראות בדף המסכת ↗</a>')
   +'<textarea placeholder="תיקון אחר, או הערה משלך" oninput="note(&quot;'+f.id+'&quot;,this.value)">'+esc(st.n||'')+'</textarea>'
   +'</div></div>'}
function set(id,s){ST[id]=ST[id]||{};ST[id].s=(ST[id].s===s?'':s);save();draw()}
function note(id,v){ST[id]=ST[id]||{};ST[id].n=v;save();counts()}
function allSevere(){if(!confirm('לתקן את כל '+D.filter(f=>f.sev==='חמור').length+' הממצאים שבטעון תיקון?'))return;
  D.filter(f=>f.sev==='חמור').forEach(f=>{ST[f.id]=ST[f.id]||{};ST[f.id].s='אושר'});save();draw()}
function allFix(){const n=D.filter(f=>f.fix&&f.fix.indexOf('\u27f5')>-1);
  if(!confirm('לתקן את כל '+n.length+' הממצאים שיש בהם הצעת החלפה ברורה?'))return;
  n.forEach(f=>{ST[f.id]=ST[f.id]||{};ST[f.id].s='אושר'});save();draw()}
let FILT='הכל';
function filt(x){FILT=x;document.querySelectorAll('[data-filt]').forEach(b=>b.classList.toggle('on',b.dataset.filt===x));draw()}
function draw(){
  const keep=D.filter(function(f){const st=(ST[f.id]||{}).s||'';
    if(FILT==='הכל')return true;
    if(FILT==='פתוח')return !st||st==='עיון';
    if(FILT==='אושר')return st==='אושר';
    return f.sev===FILT});
  let h='';
  if(LOST.length){h+='<h2 class="warn">ממצאים שלא אותרו בקובץ ('+LOST.length+')</h2>'
    +'<div class="gen">השורה שעליה נרשם הממצא אינה עוד בקובץ, או שהשתנתה. הממצא מובא כאן '
    +'כלשונו כשנרשם, ואינו נתלה בשורה אחרת.</div>';
    for(const f of LOST)h+=card(f,true)}
  let last='';
  for(const f of keep){if(f.sev!==last){last=f.sev;
      h+='<h2>'+(f.sev==='חמור'?'טעון תיקון':f.sev==='בינוני'?'ראוי לתיקון':'קל - לשיקולך')+'</h2>'}
    h+=card(f)}
  document.getElementById('list').innerHTML=h||'<div class="gen">אין ממצאים בסינון הזה.</div>';
  counts()}
function counts(){
  const A=D.concat(LOST);
  const a=A.filter(f=>(ST[f.id]||{}).s==='אושר').length;
  const r=A.filter(f=>(ST[f.id]||{}).s==='נדחה').length;
  document.getElementById('nok').textContent=a;
  document.getElementById('nno').textContent=r;
  document.getElementById('open').textContent=A.length-a-r;}
function text(){
  const A=D.concat(LOST);
  const a=A.filter(f=>(ST[f.id]||{}).s==='אושר');
  let t='הגהת מסכת '+MAS+' - לאוקמי גירסא\n'+new Date().toLocaleString('he-IL')+'\n';
  t+='לתיקון: '+a.length+' מתוך '+A.length+'\n\n';
  t+='==== לתקן בקובץ הוורד ====\n\n';
  for(const f of a){const st=ST[f.id]||{};
    t+='דף '+f.daf+' | '+f.kind+' | מזהה '+f.id+'\n  '+f.note+'\n';
    if(f.fix)t+='  התיקון: '+f.fix+'\n';
    t+='  השורה: '+f.text.replace(/\t/g,'   ').trim()+'\n';
    if(st.n)t+='  הוראה משלך: '+st.n+'\n';
    t+='\n'}
  const rest=A.filter(f=>(ST[f.id]||{}).s!=='אושר');
  t+='\n==== שלא אושרו ====\n\n';
  for(const f of rest){const st=ST[f.id]||{};
    t+='['+(st.s||'טרם הוכרע')+'] דף '+f.daf+' | מזהה '+f.id+' | '+f.note+'\n';
    if(st.n)t+='  הערתך: '+st.n+'\n'}
  /* בלוק הנתונים נקרא בידי הכלי שמכניס את התיקונים לוורד. המזהה שבו
     יציב, ולכן הוא מצביע תמיד על הממצא שאושר ולא על שכנו. */
  t+='\n\n==== נתוני עיבוד (אין לערוך) ====\n';
  const out={v:2,slug:SLUG,masechet:MAS,when:new Date().toISOString(),decisions:{}};
  for(const f of A){const st=ST[f.id]||{};if(st.s||st.n)
    out.decisions[f.id]={s:st.s||'',n:st.n||'',daf:f.daf,mark:f.mark,kind:f.kind,note:f.note,fix:f.fix}}
  t+=JSON.stringify(out);
  return t}
function out(){const a=document.createElement('a');
  a.href=URL.createObjectURL(new Blob([text()],{type:'text/plain;charset=utf-8'}));
  a.download='הגהת-'+MAS+'.txt';a.click()}
function copy(){const t=text();
  const done=()=>{const b=document.getElementById('cpb');b.textContent='הועתק \u2713';setTimeout(()=>b.textContent='העתק ללוח',2200)};
  if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(t).then(done,fallback)}else fallback();
  function fallback(){const ta=document.createElement('textarea');ta.value=t;document.body.appendChild(ta);
    ta.select();try{document.execCommand('copy');done()}catch(e){alert('לא הצלחתי להעתיק. השתמש בכפתור ההורדה.')}ta.remove()}}
/* באנר חד-פעמי: הסימונים הישנים נשענו על מקום ברשימה ואינם ניתנים להעברה */
(function(){try{
  if(localStorage.getItem(KOLD)&&!localStorage.getItem(K+'-said')){
    const d=document.getElementById('mig');
    if(d){d.style.display='block';d.textContent='הסימונים שסימנת כאן לפני היום אינם מוצגים עוד. '+
      'עד היום ממצא זוהה לפי מקומו ברשימה, וכשנמחקו ממצאים כל סימון ישן נצמד לממצא אחר. '+
      'מעתה לכל ממצא מזהה קבוע משלו, והסימונים יעמדו גם אחרי כל בנייה מחדש.'}
    localStorage.setItem(K+'-said','1')}
}catch(e){}})();
draw();
'''

PAGE = '''<!DOCTYPE html><html lang="he" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>הגהת מסכת __M__ · לאוקמי גירסא</title>
<link href="https://fonts.googleapis.com/css2?family=Frank+Ruhl+Libre:wght@400;500;700;900&display=swap" rel="stylesheet">
<style>__CSS__</style></head><body>
<div class="bar"><a class="nl" href="index.html"><span class="nm">לאוקמי גירסא</span></a>
 <span>הגהת מסכת __M__</span>
 <a href="__SLUG__.html">לדף המסכת</a>
 <span class="sp"></span>
 <button data-filt="הכל" class="on" onclick="filt('הכל')">הכל</button>
 <button data-filt="פתוח" onclick="filt('פתוח')">שטרם הוכרע</button>
 <button data-filt="אושר" onclick="filt('אושר')">שסומנו לתיקון</button>
 <button data-filt="חמור" onclick="filt('חמור')">טעון תיקון</button>
 <button id="cpb" onclick="copy()">העתק ללוח</button>
 <button onclick="out()">הורד לקובץ</button></div>
<main>
<div class="lead"><h1>הגהת מסכת __M__</h1>__BANNER__<div class="mig" id="mig"></div>
<p>לפניך מה שנמצא בקובץ בקריאה מלאה ובסריקה: טעויות כתיב, ציוני דף שאינם במקומם, סימני קיצור שאינם אחידים, ומקום שהתוכן בו נראה הפוך. כל ממצא מביא את השורה כלשונה בקובץ, את ההצעה, וקישור אל המקום עצמו בדף המסכת.</p>
<p><b>איך מאשרים:</b> בכל ממצא יש שלושה כפתורים. <b>"תקן"</b> אומר לי להכניס את התיקון לקובץ הוורד שלך; <b>"דחה תיקון"</b> סוגר את הממצא; <b>"לעיון"</b> משאיר אותו פתוח. אם התיקון הנכון שונה מהצעתי, כתוב אותו בשורת ההערה שלצד הכפתורים - היא גוברת על ההצעה.</p>
<p>ממהר? <b>"תקן את כל טעוני התיקון"</b> שלמטה מאשר בלחיצה אחת את הממצאים החמורים. הסימון נשמר בדפדפן וימתין לך גם מחר.</p>
<p><b>וכשתסיים:</b> לחץ <b>"הורד לקובץ"</b> שבסרגל העליון, ואמור לי "סיימתי להגיה" - אקרא את הקובץ מתיקיית ההורדות שלך ואכניס את התיקונים. לחלופין "העתק ללוח" והדבק אצלי בשיחה. לכל ממצא מזהה קבוע משלו, ולכן התיקון שאישרת נכנס למקום שאישרת גם אם הקובץ השתנה בינתיים.</p>
<div class="bulk"><button onclick="allSevere()">תקן את כל טעוני התיקון</button>
<button onclick="allFix()">תקן את כל אלה שיש בהם הצעת החלפה ברורה</button></div></div>
<div class="counts">
 <div class="cbox">טעון תיקון<b>__N0__</b></div>
 <div class="cbox">ראוי לתיקון<b>__N1__</b></div>
 <div class="cbox">קל<b>__N2__</b></div>
 <div class="cbox">לתיקון<b id="nok">0</b></div>
 <div class="cbox">נדחו<b id="nno">0</b></div>
 <div class="cbox">ממתין<b id="open">0</b></div></div>
<div id="list"></div>
<h2>הערות כלליות על הקובץ</h2>
__GEN__
</main>
<footer>__TOT__ ממצאים · נבנה מן הקובץ "__SRC__" · __DATE__</footer>
<script>const MAS="__M__",SLUG="__SLUG__",D=__DATA__,LOST=__LOST__;</script><script>__JS__</script></body></html>'''


def build(blocks, out_path, masechet, slug, curated_path=None, source=''):
    loc = _locate(blocks)
    rows, banner, decisions = [], '', {}
    cur = {}
    if curated_path and os.path.exists(curated_path):
        cur = json.load(open(curated_path, encoding='utf-8'))
        source = source or cur.get('source', '')
        banner = cur.get('banner', '')
        decisions = cur.get('decisions', {}) or {}
        for r in cur.get('findings', []):
            r = dict(r); r['src'] = 'cur'
            rows.append(r)
    seen = {(r.get('i'), r.get('mark', '')) for r in rows}
    for r in _auto(blocks):
        if (r['i'], r['mark']) in seen:
            continue
        rows.append(r)

    # --- זהות יציבה ועיגון מחדש ---
    F, lost, done = [], [], 0
    for r in rows:
        r.setdefault('context', '')
        ident = fid(slug, r.get('kind', ''), r.get('mark', ''), r['context'])
        d = decisions.get(ident) or {}
        if d.get('s') in ('בוצע', 'נדחה') and r.get('src') == 'auto':
            # ממצא אוטומטי שנדחה או שכבר תוקן אינו חוזר ומטריד
            done += 1
            continue
        hit = anchor(blocks, r)
        rec = {'id': ident, 'sev': r.get('sev', 'קל'), 'kind': r.get('kind', ''),
               'note': r.get('note', ''), 'fix': r.get('fix', ''), 'mark': r.get('mark', ''),
               'daf': r.get('daf', ''), 'seed': d.get('s', ''), 'seedn': d.get('n', '')}
        if hit is None:
            # לעולם לא נתלה בשורה אחרת. מוצג בקול בראש המסך, עם השורה שנרשמה.
            rec['text'] = r.get('context') or r.get('note', '')
            rec['u'] = None
            rec['how'] = ''
            lost.append(rec)
        else:
            b, how = hit
            p_, u = loc.get(b['i'], (0, b['i']))
            rec['text'] = b['text']
            rec['daf'] = b.get('daf') or rec['daf']
            rec['u'] = u
            rec['how'] = how
            F.append(rec)

    order = {'חמור': 0, 'בינוני': 1, 'קל': 2}
    F.sort(key=lambda r: (order.get(r['sev'], 3), r['u']))
    stat = collections.Counter(f['sev'] for f in F)

    empty = sum(1 for b in blocks if b['style'] == 'חלון 3' and b['text'].strip() in ('', '◄', '-'))
    cols = sum(1 for b in blocks if '\t' in b['text'] or re.search(r'  +', b['text']))
    notes = [
        ('יישור בשני טורים', cols,
         'הקובץ בנוי על יישור בטאבים וברווחים כפולים. דפדפן מכווץ כל רצף רווחים לרווח אחד, ולכן '
         'היישור הזה אינו נראה באתר. אף מילה אינה משתנה בשל כך, אבל מי שרגיל לוורד יחוש בחסר.'),
        ('חלון צד ריק', empty,
         'בחלון הצד נכתב רק הסימן ◄ בלא מילה, ולכן הרצועה שליד הטקסט נשארת ריקה בכל המקומות האלה.'),
        ('הכרעות שכבר נסגרו', done,
         'ממצאים שכבר תוקנו בוורד, או שדחית אותם, ואינם חוזרים להטריד.'),
    ]
    gen = ''.join('<div class="gen"><b>%s</b> <span class="n">%d</span><br>%s</div>'
                  % (t, n, html.escape(d)) for t, n, d in notes if n)
    data = json.dumps(F, ensure_ascii=False).replace('</', '<\\/')
    lostd = json.dumps(lost, ensure_ascii=False).replace('</', '<\\/')
    page = (PAGE.replace('__CSS__', CSS).replace('__JS__', JS).replace('__DATA__', data)
            .replace('__LOST__', lostd)
            .replace('__M__', masechet).replace('__SLUG__', slug).replace('__GEN__', gen)
            .replace('__SRC__', html.escape(source or masechet))
            .replace('__BANNER__', '<div class="ban">' + html.escape(banner) + '</div>' if banner else '')
            .replace('__N0__', str(stat.get('חמור', 0))).replace('__N1__', str(stat.get('בינוני', 0)))
            .replace('__N2__', str(stat.get('קל', 0))).replace('__TOT__', str(len(F)))
            .replace('__DATE__', datetime.datetime.now().strftime('%d.%m.%Y')))
    open(out_path, 'w', encoding='utf-8').write(page)
    return {'findings': len(F), 'severe': stat.get('חמור', 0), 'lost': len(lost), 'closed': done}
