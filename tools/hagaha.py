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
import json, re, html, os, datetime, collections

HEB = 'א-ת'
SKIP_TRUNC = {'אמרי', 'אפי', 'דאפי', 'ואפי', 'שאפי', 'גזרי', 'ילפי', 'דבעי', 'בעי', 'מתני',
              'דממתני', 'ותרצי', 'כדחזי', 'חזי', 'ודחי', 'דחי', 'ומספקי', 'מספקי', 'וספינ',
              'חיישי', 'מיירי', 'אמרינ', 'קמ', 'דמצי', 'מצי'}

# זהה למפה שב-build_site. סגנון שאינו כאן נחשב גוף.
ROLE = {'Normal': 'body', 'רגיל ללא רווח': 'body', 'רווח לפני': 'body-sp', 'נקודה': 'body-nk',
        'הסבר ורקע': 'body-hr', 'הסבר': 'body-hr', 'אמוראים': 'body', 'פסוק': 'body',
        'פרנקיל מודגש': 'body', 'חלון 3': 'anchor', 'דף בצד': 'daf', 'פרק': 'perek-num',
        'פרק שם': 'perek-name', 'דפים בפרק ב': 'perek-range', 'תחילת פרק': 'perek-start',
        'הדרן עלך': 'hadran', 'סוף פרק': 'hadran', 'משניות': 'mishna',
        'חלק משנה מודגש': 'mishna', 'חלק משנה מודגשת': 'mishna', "ד''ה משנה": 'dh',
        "משנה ד''ה": 'dh', "ד''ה משנה מודגש אפור": 'dh', 'נושא': 'nose', 'חציצה': 'hatz'}


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


def _auto(blocks):
    """הגלאים האוטומטיים. מחזיר רשימת (חומרה, סוג, i, הערה, הצעה, סימון)."""
    out = []
    for b in blocks:
        t = b['text']
        # גרש יחיד בתוך ראשי-תיבות: הקב'ה, לת'ק, יד'ח
        for m in re.finditer(r"(?<![%s])([%s]{1,7})'([%s]{1,3})(?![%s'])" % (HEB, HEB, HEB, HEB), t):
            tok = m.group(0)
            # אות בודדת לפני הגרש היא דו-משמעית: או אות-שימוש הפותחת ציטוט
            # ("מ'פני הכפורת"), או ראשי תיבות. שם אין הכרעה, ורק מסמנים.
            if len(m.group(1)) == 1:
                out.append(('קל', 'סימני קיצור', b['i'],
                            'גרש יחיד אחרי אות בודדת ב"%s" - ראשי תיבות, או פתיחת ציטוט?' % tok,
                            'אם ראשי תיבות - גרשיים; אם ציטוט - להשלים את הגרש הסוגר', tok))
            else:
                out.append(('בינוני', 'סימני קיצור', b['i'],
                            'ראשי התיבות "%s" נכתבו בגרש יחיד ולא בגרשיים' % tok,
                            tok + ' ⟵ ' + tok.replace("'", '"'), tok))
        # גרש סוגר בלא פותח על מילה מלאה
        for m in re.finditer(r"(?<![%s\"'])([%s]{4,})'(?![%s'])" % (HEB, HEB, HEB), t):
            w = m.group(1)
            if w in SKIP_TRUNC: continue
            if t[:m.start()].count("'") % 2: continue
            out.append(('בינוני', 'סימני קיצור', b['i'],
                        'הגרש שאחרי "%s" סוגר ציטוט שאין לו גרש פותח' % w,
                        'להוסיף גרש פותח בראש הציטוט', m.group(0)))
        # יו"ד כפולה בראש ראשי-תיבות
        for m in re.finditer(r'(?<![%s])יי[%s]{0,3}["״]' % (HEB, HEB), t):
            out.append(('בינוני', 'שגיאת כתיב', b['i'],
                        'יו"ד כפולה בראש ראשי התיבות "%s"' % m.group(0),
                        m.group(0) + ' ⟵ ' + m.group(0)[1:], m.group(0)))
        # קו נטוי בתוך מילה עברית
        for m in re.finditer(r'[%s]/' % HEB, t):
            out.append(('בינוני', 'שגיאת כתיב', b['i'],
                        'קו נטוי בתוך מילה עברית - כנראה במקום גרש',
                        'להחליף בגרש', m.group(0)))
        # פיסוק בלא רווח אחריו
        for m in re.finditer(r'[%s][:,][%s]' % (HEB, HEB), t):
            out.append(('קל', 'פיסוק', b['i'], 'סימן פיסוק בלא רווח אחריו',
                        'להוסיף רווח', m.group(0)))
        # פסקה ריקה
        if not t.strip() and b['style'] != 'חציצה':
            out.append(('קל', 'פסקה ריקה', b['i'],
                        'פסקה ריקה בסגנון "%s"' % b['style'], 'למחוק, או להשלים את התוכן', ''))
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
.counts{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0 4px}
.cbox{background:var(--paper);border:1px solid var(--line);border-radius:6px;padding:7px 14px;font-size:14px;text-align:center}
.cbox b{font-size:21px;display:block;font-family:'Vilna',serif;font-weight:900}
.f{background:var(--paper);border:1px solid var(--line);border-right:5px solid var(--grey);border-radius:7px;
   padding:12px 15px;margin:9px 0;line-height:1.6}
.f.s0{border-right-color:var(--red)} .f.s1{border-right-color:var(--gold)} .f.s2{border-right-color:#b9b099}
.f.done{opacity:.52}
.f .hd{display:flex;flex-wrap:wrap;gap:8px;align-items:baseline;margin-bottom:5px}
.daf{font-family:'VilnaG','Vilna',serif;color:var(--red);font-size:19px;min-width:44px}
.tag{background:#eeeae1;border-radius:4px;padding:1px 9px;font-size:13px;color:#5a5044}
.note{font-size:16px}
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
const K='lg-hagaha-'+SLUG;
let ST={};try{ST=JSON.parse(localStorage.getItem(K)||'{}')}catch(e){ST={}}
function save(){try{localStorage.setItem(K,JSON.stringify(ST))}catch(e){}}
function esc(s){return s.replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}
const SEV=['חמור','בינוני','קל'];
function mk(text,m){const t=esc(text);if(!m)return t;const e=esc(m);
  const k=t.indexOf(e);if(k<0)return t;return t.slice(0,k)+'<mark>'+e+'</mark>'+t.slice(k+e.length)}
function card(f){const st=ST[f.id]||{};
  return '<div class="f s'+SEV.indexOf(f.sev)+(st.s&&st.s!=='עיון'?' done':'')+'" id="f'+f.id+'">'
   +'<div class="hd"><span class="daf">'+esc(f.daf)+'</span><span class="tag">'+esc(f.kind)+'</span></div>'
   +'<div class="note">'+esc(f.note)+'</div>'
   +'<div class="quote">'+mk(f.text.replace(/\t/g,'   ').trim(),f.mark)+'</div>'
   +(f.fix?'<div class="fix">הצעה: <b>'+esc(f.fix)+'</b></div>':'')
   +'<div class="act">'
   +'<button onclick="set('+f.id+',\'תוקן\')" class="'+(st.s==='תוקן'?'on':'')+'">תוקן בוורד</button>'
   +'<button onclick="set('+f.id+',\'נכון\')" class="'+(st.s==='נכון'?'on':'')+'">נכון כמות שהוא</button>'
   +'<button onclick="set('+f.id+',\'עיון\')" class="'+(st.s==='עיון'?'on':'')+'">להשאיר לעיון</button>'
   +'<a href="'+SLUG+'.html#u='+f.u+'" target="_blank">לראות בדף המסכת ↗</a>'
   +'<textarea placeholder="הערה משלך" oninput="note('+f.id+',this.value)">'+esc(st.n||'')+'</textarea>'
   +'</div></div>'}
function set(id,s){ST[id]=ST[id]||{};ST[id].s=(ST[id].s===s?'':s);save();draw()}
function note(id,v){ST[id]=ST[id]||{};ST[id].n=v;save();counts()}
let FILT='הכל';
function filt(x){FILT=x;document.querySelectorAll('[data-filt]').forEach(b=>b.classList.toggle('on',b.dataset.filt===x));draw()}
function draw(){
  const keep=D.filter(function(f){const st=(ST[f.id]||{}).s||'';
    if(FILT==='הכל')return true;
    if(FILT==='פתוח')return !st||st==='עיון';
    if(FILT==='טופל')return st==='תוקן'||st==='נכון';
    return f.sev===FILT});
  let h='',last='';
  for(const f of keep){if(f.sev!==last){last=f.sev;
      h+='<h2>'+(f.sev==='חמור'?'טעון תיקון':f.sev==='בינוני'?'ראוי לתיקון':'קל — לשיקולך')+'</h2>'}
    h+=card(f)}
  document.getElementById('list').innerHTML=h||'<div class="gen">אין ממצאים בסינון הזה.</div>';
  counts()}
function counts(){const n=D.filter(function(f){const s=(ST[f.id]||{}).s;return s==='תוקן'||s==='נכון'}).length;
  document.getElementById('done').textContent=n;
  document.getElementById('open').textContent=D.length-n}
function out(){
  let t='הגהת מסכת '+MAS+' — לאוקמי גירסא\n'+new Date().toLocaleString('he-IL')+'\n\n';
  for(const f of D){const st=ST[f.id]||{};
    t+='['+(st.s||'טרם הוכרע')+'] דף '+f.daf+'  '+f.kind+'\n  '+f.note+'\n';
    if(f.fix)t+='  הצעה: '+f.fix+'\n';
    t+='  בקובץ: '+f.text.replace(/\t/g,'   ').trim()+'\n';
    if(st.n)t+='  הערתך: '+st.n+'\n';
    t+='\n'}
  const a=document.createElement('a');
  a.href=URL.createObjectURL(new Blob([t],{type:'text/plain;charset=utf-8'}));
  a.download='הגהת-'+MAS+'.txt';a.click()}
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
 <button data-filt="טופל" onclick="filt('טופל')">שהוכרע</button>
 <button data-filt="חמור" onclick="filt('חמור')">טעון תיקון</button>
 <button onclick="out()">ייצוא לקובץ</button></div>
<main>
<div class="lead"><h1>הגהת מסכת __M__</h1>
<p>לפניך מה שנמצא בקובץ בקריאה מלאה ובסריקה: טעויות כתיב, ציוני דף שאינם במקומם, סימני קיצור שאינם אחידים, ומקום שהתוכן בו נראה הפוך. כל ממצא מביא את השורה כלשונה בקובץ, את ההצעה, וקישור אל המקום עצמו בדף המסכת.</p>
<p>סמן בכל ממצא מה עשית בו. הסימון נשמר בדפדפן שלך וימתין לך גם מחר, ובסוף אפשר להוריד את הכל לקובץ אחד.</p></div>
<div class="counts">
 <div class="cbox">טעון תיקון<b>__N0__</b></div>
 <div class="cbox">ראוי לתיקון<b>__N1__</b></div>
 <div class="cbox">קל<b>__N2__</b></div>
 <div class="cbox">הוכרע<b id="done">0</b></div>
 <div class="cbox">ממתין<b id="open">0</b></div></div>
<div id="list"></div>
<h2>הערות כלליות על הקובץ</h2>
__GEN__
</main>
<footer>__TOT__ ממצאים · נבנה מן הקובץ "__SRC__" · __DATE__</footer>
<script>const MAS="__M__",SLUG="__SLUG__",D=__DATA__;</script><script>__JS__</script></body></html>'''


def build(blocks, out_path, masechet, slug, curated_path=None, source=''):
    loc = _locate(blocks)
    daf = {b['i']: (b.get('daf') or '') for b in blocks}
    txt = {b['i']: b['text'] for b in blocks}
    rows = []
    seen = set()
    if curated_path and os.path.exists(curated_path):
        cur = json.load(open(curated_path, encoding='utf-8'))
        source = source or cur.get('source', '')
        for r in cur.get('findings', []):
            rows.append((r['sev'], r['kind'], r['i'], r['note'], r.get('fix', ''), r.get('mark', '')))
            seen.add((r['i'], r.get('mark', '')))
    for r in _auto(blocks):
        if (r[2], r[5]) in seen: continue
        rows.append(r)

    order = {'חמור': 0, 'בינוני': 1, 'קל': 2}
    rows.sort(key=lambda r: (order.get(r[0], 3), r[2]))
    F = []
    for n, (sev, kind, i, note, fix, m) in enumerate(rows):
        p, u = loc.get(i, (0, i))
        F.append({'id': n, 'sev': sev, 'kind': kind, 'daf': daf.get(i, ''), 'note': note,
                  'fix': fix, 'mark': m, 'text': txt.get(i, ''), 'u': u})
    stat = collections.Counter(f['sev'] for f in F)

    empty = sum(1 for b in blocks if b['style'] == 'חלון 3' and b['text'].strip() in ('', '◄', '-'))
    cols = sum(1 for b in blocks if '\t' in b['text'] or re.search(r'  +', b['text']))
    notes = [
        ('יישור בשני טורים', cols,
         'הקובץ בנוי על יישור בטאבים וברווחים כפולים. דפדפן מכווץ כל רצף רווחים לרווח אחד, ולכן '
         'היישור הזה אינו נראה באתר. אף מילה אינה משתנה בשל כך, אבל מי שרגיל לוורד יחוש בחסר.'),
        ('חלון צד ריק', empty,
         'בחלון הצד נכתב רק הסימן ◄ בלא מילה, ולכן הרצועה שליד הטקסט נשארת ריקה בכל המקומות האלה.'),
    ]
    gen = ''.join('<div class="gen"><b>%s</b> <span class="n">%d</span><br>%s</div>'
                  % (t, n, html.escape(d)) for t, n, d in notes if n)
    data = json.dumps(F, ensure_ascii=False).replace('</', '<\\/')
    page = (PAGE.replace('__CSS__', CSS).replace('__JS__', JS).replace('__DATA__', data)
            .replace('__M__', masechet).replace('__SLUG__', slug).replace('__GEN__', gen)
            .replace('__SRC__', html.escape(source or masechet))
            .replace('__N0__', str(stat.get('חמור', 0))).replace('__N1__', str(stat.get('בינוני', 0)))
            .replace('__N2__', str(stat.get('קל', 0))).replace('__TOT__', str(len(F)))
            .replace('__DATE__', datetime.datetime.now().strftime('%d.%m.%Y')))
    open(out_path, 'w', encoding='utf-8').write(page)
    return {'findings': len(F), 'severe': stat.get('חמור', 0)}
