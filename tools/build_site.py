import json, html, re, collections, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from styles_map import ROLE, CS
def build(json_path, out_path, masechet, hagaha=False):
  blocks = json.load(open(json_path, encoding='utf-8'))

  # מפת הסגנונות יושבת בקובץ אחד, tools/styles_map.py, שגם מסך ההגהה קורא
  # ממנו. עותק שני היה נפרד בשקט ושובר את העיגון שבין שני המסכים.

  def runs_html(runs):
      out=[]
      for r in runs:
          t=html.escape(r['t']); c=CS.get(r['cs'])
          if r['b'] and not c: c='b'
          out.append(f'<i class="{c}">{t}</i>' if c else t)
      return ''.join(out)

  # ---------- QA: daf sequence ----------
  HEB='אבגדהוזחטיכלמנסעפצקרשת'
  def gem(s):
      s=s.strip().rstrip('.:').replace('"','').replace("'",'')
      v={'א':1,'ב':2,'ג':3,'ד':4,'ה':5,'ו':6,'ז':7,'ח':8,'ט':9,'י':10,'כ':20,'ל':30,'מ':40,'נ':50,'ס':60,'ע':70,'פ':80,'צ':90,'ק':100,'ר':200,'ש':300,'ת':400}
      return sum(v.get(ch,0) for ch in s)
  def tog(n):
      out='';
      for val,ch in ((400,'ת'),(300,'ש'),(200,'ר'),(100,'ק'),(90,'צ'),(80,'פ'),(70,'ע'),(60,'ס'),(50,'נ'),(40,'מ'),(30,'ל'),(20,'כ'),(10,'י'),(9,'ט'),(8,'ח'),(7,'ז'),(6,'ו'),(5,'ה'),(4,'ד'),(3,'ג'),(2,'ב'),(1,'א')):
          while n>=val: out+=ch; n-=val
      return out.replace('יה','טו').replace('יו','טז')
  qa=[]
  seq=[(b['i'],b['text'].strip()) for b in blocks if b['style']=='דף בצד']
  seen=collections.Counter(); prev=None
  for i,d in seq:
      seen[d]+=1
      if seen[d]>1: qa.append(('כפילות ציון דף',f'"{d}" מופיע שוב (יחידה {i})'))
      key=gem(d)*2+(1 if d.endswith(':') else 0)
      if prev is not None and key!=prev+1 and seen[d]==1:
          miss=[]; k=prev+1
          while k<key: miss.append(tog(k//2)+('.' if k%2==0 else ':')); k+=1
          if miss: qa.append(('עמוד ללא ציון דף','חסר: '+', '.join(miss)+f' (לפני {d})'))
          if key<prev: qa.append(('סדר דפים הפוך',f'"{d}" אחרי {tog(prev//2)}{"." if prev%2==0 else ":"}'))
      prev=max(prev or 0,key)
  unknown=collections.Counter(b['style'] for b in blocks if b['style'] not in ROLE)
  for s,n in unknown.items(): qa.append(('סגנון לא ממופה',f'{s} ({n})'))
  # סגנון תו שאינו במפה מאבד את עיצובו בלי שיאמר דבר. הוא נמנה כאן כדי שלא ייפער חור שקט.
  unk_cs=collections.Counter(r['cs'] for b in blocks for r in b['runs'] if r['cs'] and r['cs'] not in CS)
  for s,n in unk_cs.items(): qa.append(('סגנון תו לא ממופה',f'{s} ({n})'))
  long_anchor=[b for b in blocks if b['style']=='חלון 3' and len(b['text'])>25]
  for b in long_anchor: qa.append(('חלון ארוך',b['text'][:40]))
  empty_anchor=[b for b in blocks if b['style']=='חלון 3' and not b['text'].strip()]
  if empty_anchor: qa.append(('חלון ריק',f'{len(empty_anchor)} חלונות ריקים'))

  # ---------- pages ----------
  pages=[]  # {daf, perek, perekName, units:[...]}
  cur=None; perek=''; perekName=''; unit=None
  order=[]
  for b in blocks:
      r=ROLE.get(b['style'],'body'); h=runs_html(b['runs']); t=b['text'].strip()
      # כותרת ריקה אינה יוצרת יחידה. בלעדי זה נפער בדף חלל בלא טקסט,
      # ופסקת "פרק" ריקה אף היתה מאפסת את שם הפרק ומזיזה את גבול המקטע.
      if not t and r in ('perek-num','perek-name','perek-range','perek-start','hadran','nose','dh','mishna','hatz'):
          continue
      if r=='perek-num': perek=t
      if r=='perek-name': perekName=t
      if r=='daf':
          cur={'daf':t,'perek':perek,'perekName':perekName,'units':[]}; pages.append(cur); unit=None
          continue
      if cur is None: continue
      cur['perek']=perek; cur['perekName']=perekName
      if r=='anchor':
          unit={'k':'u','a':h,'l':[],'id':b['i']}; cur['units'].append(unit)
      elif r.startswith('body'):
          if unit is None or unit['k']!='u': unit={'k':'u','a':'','l':[],'id':b['i']}; cur['units'].append(unit)
          unit['l'].append([r[5:] if len(r)>4 else '',h])
      elif r=='mishna':
          if cur['units'] and cur['units'][-1]['k']=='m': cur['units'][-1]['l'].append(['',h])
          else: cur['units'].append({'k':'m','a':'','l':[['',h]],'id':b['i']})
          unit=None
      elif r in ('dh','nose','hatz','perek-num','perek-name','perek-range','perek-start','hadran'):
          cur['units'].append({'k':r,'a':h,'l':[],'id':b['i']}); unit=None

  # nose TOC
  toc=[]
  for pi,p in enumerate(pages):
      for u in p['units']:
          if u['k']=='nose': toc.append([pi,u['id'],re.sub('<[^>]+>','',u['a'])])
  # amoraim index
  am=collections.Counter()
  for b in blocks:
      for r in b['runs']:
          if r['cs']=='אמוראים תו':
              n=r['t'].strip(' ,.:;!?-')
              if 2<=len(n)<=18: am[n]+=1
  amlist=[[k,v] for k,v in am.most_common(80)]
  psk=collections.Counter()
  for b in blocks:
      for r in b['runs']:
          if r['cs']=='פסוק תו':
              n=r['t'].strip(" ,.:;!?-'’‘")
              if len(n)>=4: psk[n]+=1

  data={'masechet':masechet,'pages':pages,'toc':toc,'am':amlist,'qa':qa,'nPsk':len(psk),'nAm':sum(am.values())}
  J=json.dumps(data,ensure_ascii=False).replace('</','<\\/')

  CSS=r'''
  @font-face{font-family:'Frank';src:url(fonts/frank.ttf);font-weight:400;font-display:swap}
  @font-face{font-family:'Vilna';src:url(fonts/vilna-r.otf);font-weight:400;font-display:swap}
  @font-face{font-family:'Vilna';src:url(fonts/vilna-m.ttf);font-weight:500;font-display:swap}
  @font-face{font-family:'Vilna';src:url(fonts/vilna-b.otf);font-weight:700;font-display:swap}
  @font-face{font-family:'Vilna';src:url(fonts/vilna-xb.otf);font-weight:900;font-display:swap}
  @font-face{font-family:'VilnaG';src:url(fonts/vilna-g.ttf);font-display:swap}
  @font-face{font-family:'Franknatan';src:url(fonts/franknatan.otf);font-display:swap}
  @font-face{font-family:'Leukmey';src:url(fonts/leukmey.otf);font-display:swap}
  /* היחס בין גודל האות לרוחב השורה נעול. כל המידות נמדדות ב-em של גוף הטקסט:
     עמוד הספר הוא 60 מ"מ טקסט ב-11 נקודות, כלומר 15.46em, ורצועת הדף 5.15em.
     לכן הגדלה והקטנה משנות הכל יחד, ושבירת השורות אינה זזה לעולם. */
  :root{--fs:24px;--measure:15.46em;--rail:5.15em;--gut:2.57em;
        --ink:#1d1a16;--paper:#fbf8f1;--grey:#767171;--gold:#c9a24a;--red:#a83c2f;--bar:46px}
  *{box-sizing:border-box}
  html,body{margin:0;height:100%;background:#e9e4d8;color:var(--ink);font-family:'Frank','Frank Ruhl Libre',serif;overflow:hidden}
  body.hc{--ink:#000;--paper:#fff;--grey:#333}
  .bar{position:relative;z-index:5;display:flex;flex-wrap:wrap;gap:6px 10px;align-items:center;padding:7px 12px;background:#2b2620;color:#f1ead9;font-size:14px;height:var(--bar)}
  .bar .nm{font-family:'Leukmey','Vilna',serif;font-size:20px;line-height:1}
  .bar .sp{flex:1}
  .bar button,.bar select,.bar input{font:inherit;background:#4a4137;color:#f1ead9;border:0;border-radius:4px;padding:3px 9px;cursor:pointer}
  .bar input{cursor:text;width:150px} .bar button.on{background:var(--gold);color:#2b2620}
  .nav{display:flex;gap:4px;align-items:center}
  .nav .daf{min-width:52px;text-align:center;font-family:'VilnaG','Vilna',serif;font-size:17px}
  .flow{font-size:var(--fs);line-height:1.06;height:calc(100vh - var(--bar));background:var(--paper);
        padding:.9em var(--gut);overflow:auto;
        column-width:calc(var(--rail) + var(--measure));column-gap:calc(var(--gut) * 2);
        column-fill:auto;column-rule:1px solid #e6ddc9}
  /* מצב רצף: מבטלים את מכולת-הטורים לגמרי. 'column-count:1' לבדו אינו מספיק -
     המכולה נשארת רב-טורית, ותוכן שאינו נכנס בגובה גולש לטורים נוספים לצדדים
     במקום לגלול למטה. רק 'auto' בשניהם מוציא אותה ממצב טורים. */
  /* המכולה נשארת ברוחב מלא, והשורות עצמן ממורכזות. כך אין תלות ברוחב
     פס-הגלילה ולעולם אין גלילה אופקית. */
  .flow.vert{column-width:auto;column-count:auto;column-rule:0;column-fill:balance;
             width:auto;padding:.9em .6em;overflow-x:hidden}
  /* 'margin:auto' לבדו אינו ממרכז אלמנט-בלוק שרוחבו אוטומטי - הוא נמתח.
     fit-content מצמצם את השורה לרוחב שתי המסילות, ואז המירכוז תופס. */
  .flow.vert .row{width:fit-content;margin:0 auto}
  .row{display:grid;grid-template-columns:var(--rail) var(--measure);break-inside:avoid-column}
  .rail{text-align:left;padding-left:.36em}
  .main{text-align:justify;text-align-last:right}
  .main p{margin:0} .main p.sp{margin-top:.28em} .main p.nk{font-size:1.09em} .main p.hr{font-size:.82em;color:#4a4137}
  .dafmark{display:block;font-family:'VilnaG','Vilna',serif;font-size:1.3em;line-height:1;color:var(--red);margin-top:.25em}
  .anchor{display:inline-block;font-family:'Vilna',serif;font-weight:900;font-size:.9em;line-height:1.18;
          color:#5a5044;white-space:nowrap;max-width:calc(var(--rail) - .4em);overflow:hidden;text-overflow:ellipsis}
  .mlabel{font-size:.55em;color:#8a7d66}
  .mishna{background:#eeeae1;padding:.1em .15em;margin:.15em 0;font-family:'Vilna',serif;font-weight:700;font-size:.97em;line-height:1.12;border-right:.1em solid var(--gold)}
  .dh{text-align:center;text-align-last:center;font-family:'Vilna',serif;font-weight:900;font-size:1.18em;line-height:1.15;margin:.3em 0 .08em}
  .nose{text-align:center;text-align-last:center;font-family:'Vilna',serif;font-weight:700;font-size:1.02em;line-height:1.15;margin-top:.45em;color:var(--ink)}
  .hatz{text-align:center;text-align-last:center;font-family:'Vilna',serif;font-weight:900;font-size:.82em;letter-spacing:.35em;color:#8a7d66;margin:.3em 0}
  .perek-num .main{font-family:'Franknatan','Vilna',serif;color:var(--red);font-size:1.45em;line-height:1.1}
  .perek-name .main{font-family:'Franknatan','Vilna',serif;color:#8a7d66;font-size:1.09em}
  .perek-range .main{color:var(--red);font-size:.73em}
  .perek-start .main{text-align:center;text-align-last:center;font-family:'Vilna',serif;font-weight:700;font-size:1.09em}
  .hadran .main{text-align:center;text-align-last:center;font-size:1.09em;margin:.8em 0}
  i{font-style:normal}
  .am{font-family:'Vilna',serif;font-weight:400;font-size:.88em}
  .ps{font-family:'Vilna',serif;font-weight:700;font-size:.9em;color:#2e3f6b} body.hc .ps{color:#000;text-decoration:underline}
  .df{font-family:'VilnaG','Vilna',serif;color:var(--red)} body.hc .df{color:#000}
  .kt{font-weight:700} .hs{font-size:.82em;color:#4a4137} .ot{font-weight:700;font-size:.8em} .tn{font-weight:900} .ns{font-weight:700} .b{font-weight:700}
  .u .main:hover{background:rgba(201,162,74,.14)} .hit{background:rgba(201,162,74,.3)}
  mark{background:#ffe27a;color:inherit}
  .panel{position:fixed;top:var(--bar);right:0;bottom:0;width:min(420px,100vw);background:#fbf8f1;box-shadow:-2px 0 16px rgba(0,0,0,.25);overflow:auto;padding:14px 18px;z-index:6;display:none;font-size:15px;line-height:1.6}
  .panel.open{display:block} .panel h3{margin:12px 0 4px;font-size:15px;color:#5a5044;font-weight:500;border-bottom:1px solid #d9d1bd}
  .panel a{color:var(--ink);text-decoration:none;display:block;padding:2px 0;cursor:pointer} .panel a:hover{color:var(--red)}
  .panel .x{float:left;background:none;border:0;font-size:22px;cursor:pointer;color:#5a5044}
  .panel .n{color:#8a7d66;font-size:12px} .res{padding:5px 0;border-bottom:1px dotted #d9d1bd} .res small{color:#8a7d66}
  .tag{display:inline-block;background:#eeeae1;border-radius:3px;padding:0 6px;margin:2px;font-size:13px}
  .chips{display:flex;flex-wrap:wrap}
  /* בהדפסה: טור אחד רציף, וכל פרק פותח עמוד חדש. המידות נשארות ב-em,
     ולכן שבירת השורות זהה למסך. */
  @media print{.bar,.panel{display:none} html,body{overflow:visible;background:#fff;height:auto}
    .flow{height:auto;overflow:visible;column-width:auto;column-count:1;column-rule:0;
          width:auto;padding:0;font-size:11pt}
    .row{break-inside:avoid}
    .row.perek-num{break-before:page}
    .flow > .row.perek-num:first-child{break-before:auto}
    @page{size:90mm 260mm;margin:6mm 5mm}}
  @media(max-width:760px){:root{--fs:20px}
    .flow{column-width:auto;column-count:1;column-rule:0;width:auto;padding:.7em .8em}
    .row{grid-template-columns:1fr} .rail{text-align:right;padding:0}
    .anchor{max-width:none;display:block;margin-top:.2em;font-size:.82em;color:#4a4137}
    .dafmark{display:inline-block;margin-left:.5em}}
  '''

  JS=r'''
  const D=DATA;const $=s=>document.querySelector(s);
  const params=new URLSearchParams(location.hash.slice(1));
  function esc(s){return s.replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}

  /* מקטע = פרק. מעבר עמוד קיים רק בין מקטעים, ובתוך המקטע הטקסט רץ ברצף. */
  const SEC=[];
  D.pages.forEach((p,i)=>{const L=SEC[SEC.length-1];
    if(!L||L.perek!==p.perek||L.perekName!==p.perekName)SEC.push({perek:p.perek,perekName:p.perekName,from:i,to:i});
    else L.to=i});
  function secOf(pi){for(let i=0;i<SEC.length;i++)if(pi>=SEC[i].from&&pi<=SEC[i].to)return i;return 0}
  let cur=0;

  /* כיוון הגלילה בטורים מימין לשמאל אינו זהה בכל הדפדפנים, ולכן הוא נמדד ולא מנוחש */
  let SGN=-1;
  (function(){const t=document.createElement('div');t.style.cssText='position:absolute;top:-999px;width:60px;height:10px;overflow:auto;direction:rtl';
    t.innerHTML='<div style="width:300px;height:4px"></div>';document.body.appendChild(t);t.scrollLeft=2;SGN=t.scrollLeft>0?1:-1;t.remove()})();

  /* scrollIntoView אינו גולל מכולת-טורים, ולכן המיקום מחושב במידות פיזיות:
     מיישרים את קצה האלמנט לקצה הימני של המסגרת. הנוסחה נכונה בשני מוסכמות ה-RTL. */
  function toEl(e){const f=$('#flow');
    if(f.classList.contains('vert')){e.scrollIntoView({block:'center'});return}
    f.scrollLeft += e.getBoundingClientRect().right - f.getBoundingClientRect().right;}
  /* ---- איחוי שורה יתומה ----
     מילה בודדת שגלשה לשורה משלה נמשכת אל השורה שמעליה בדחיסה עדינה:
     קודם מצטמצם הרווח בין המילים, ורק אם לא די בכך מצטמצם גם הרווח בין
     האותיות. הסולם עוצר בערך הראשון שמצליח, ואם אף אחד לא הצליח הפסקה
     נשארת כשהיתה - כדי שהדחיסה לא תהיה ניכרת לעין.

     המדידה אינה נעשית על הדף עצמו: פריסה מחדש של מכולת-הטורים עולה
     מילישניות רבות לכל מדידה, ומאות פסקאות היו מקפיאות את הדף לשניות.
     לכן נבנה "סרגל" - עותק מבודד ברוחב זהה, מחוץ למסך - וכל הניסיונות
     נעשים בו. אל הדף עצמו נכתב רק הערך שנבחר. */
  /* הסולם נשען קודם כל על הרווח שבין האותיות ולא על זה שבין המילים:
     צמצום של מאית em באות אינו נראה כלל, ועל פני ארבעים אותיות הוא חוסך
     כשלוש אותיות שלמות - ואילו צמצום הרווח שבין המילים ניכר מיד, והמילים
     נראות נדבקות. לכן הרווח בין המילים מצטמצם לכל היותר בארבע מאיות. */
  const STEPS=[[0,-0.006],[-0.010,-0.010],[-0.020,-0.014],[-0.030,-0.018],[-0.040,-0.022]];
  let SQ=localStorage.getItem('lg-sq')!=='0', GEN=0, GAUGE=null, GP=null, GM=null;
  function gauge(){
    if(GAUGE)return;
    GAUGE=document.createElement('div');
    GAUGE.className='flow';
    /* הסרגל יושב ב-fixed ובלא נראוּת: כך הוא נמדד אך אינו נצבע, ואינו מותח
       את רוחב המסמך. הצבתו ב-left:-99999px מתחה אותו למאה אלף פיקסלים. */
    GAUGE.style.cssText='position:fixed;left:0;top:0;visibility:hidden;pointer-events:none;'+
      'height:auto;overflow:hidden;column-count:1;column-width:auto;column-rule:0;'+
      'padding:0;contain:layout style;z-index:-1;';
    GAUGE.innerHTML='<div class="row"><div class="rail"></div><div class="main"><p></p></div></div>';
    document.body.appendChild(GAUGE);
    GP=GAUGE.querySelector('p');GM=GAUGE.querySelector('.main');
  }
  function lastLineIsLone(p){
    /* משווים את הגובה של המילה האחרונה לזה של המילה שלפניה. אם הן בשורות
       שונות - השורה האחרונה נושאת מילה אחת. */
    const w=document.createTreeWalker(p,NodeFilter.SHOW_TEXT);
    const nodes=[];let nd;while(nd=w.nextNode())if(nd.nodeValue.trim())nodes.push(nd);
    if(!nodes.length)return false;
    const full=nodes.map(x=>x.nodeValue).join('');
    const m=[...full.matchAll(/\S+/g)];
    if(m.length<3)return false;
    const r=document.createRange();
    function topAt(i){let off=m[i].index;
      for(const x of nodes){const L=x.nodeValue.length;
        if(off<L){r.setStart(x,off);r.setEnd(x,Math.min(off+1,L));
          const b=r.getBoundingClientRect();return b.height?b.top:null}
        off-=L}
      return null}
    const a=topAt(m.length-1),b=topAt(m.length-2);
    return a!==null&&b!==null&&Math.abs(a-b)>2;
  }
  function squeezeRun(){
    const g=++GEN;
    if(!SQ)return;
    gauge();
    const ps=[...$('#flow').querySelectorAll('.main p')].filter(p=>p.textContent.trim().length>30);
    let i=0,fixed=0;
    const btn=$('#fbtn');
    function chunk(){
      if(g!==GEN)return;                     /* הדף נבנה מחדש - הריצה בטלה */
      const t0=performance.now();
      while(i<ps.length&&performance.now()-t0<12){
        const p=ps[i++];
        GM.className=p.parentElement.className;   /* mishna וכדומה משנים גופן */
        GP.className=p.className;
        GP.style.wordSpacing='';GP.style.letterSpacing='';
        GP.innerHTML=p.innerHTML;
        const h0=GP.offsetHeight;
        if(h0>=GP.__lh*1.5||true){
          if(lastLineIsLone(GP)){
            for(const [ws,ls] of STEPS){
              GP.style.wordSpacing=ws?ws+'em':'';GP.style.letterSpacing=ls?ls+'em':'';
              if(GP.offsetHeight<h0){if(ws)p.style.wordSpacing=ws+'em';
                if(ls)p.style.letterSpacing=ls+'em';p.dataset.sq='1';fixed++;break}
            }
          }
        }
      }
      if(i<ps.length){requestAnimationFrame(chunk);if(btn)btn.title='מאחה... '+i+'/'+ps.length}
      else if(btn){btn.classList.toggle('on',SQ);btn.title=fixed+' שורות אוחו מתוך '+ps.length}
    }
    requestAnimationFrame(chunk);
  }
  function squeeze(){SQ=!SQ;localStorage.setItem('lg-sq',SQ?'1':'0');
    GEN++;
    $('#flow').querySelectorAll('.main p').forEach(p=>{p.style.wordSpacing='';p.style.letterSpacing=''});
    if(!SQ){$('#fbtn').classList.remove('on');$('#fbtn').title='האיחוי כבוי'}else squeezeRun()}
  /* ---- הדפסה ל-PDF: כל המסכת, טור אחד, פרק בכל עמוד ---- */
  function toPdf(){const was=ALL;ALL=true;render(cur);
    setTimeout(()=>{window.print();ALL=was;render(cur)},600)}
  function unitHTML(u,daf,pi){
    const mk=daf!=null?`<b class="dafmark" id="d${pi}">${esc(daf)}</b>`:'';
    if(u.k==='u')return `<div class="row u" id="u${u.id}"><div class="rail">${mk}<span class="anchor">${u.a}</span></div><div class="main">${u.l.map(l=>`<p class="${l[0]}">${l[1]}</p>`).join('')}</div></div>`;
    if(u.k==='m')return `<div class="row" id="u${u.id}"><div class="rail">${mk}<span class="mlabel">משנה</span></div><div class="main mishna">${u.l.map(l=>`<p>${l[1]}</p>`).join('')}</div></div>`;
    if(u.k==='hatz')return `<div class="row" id="u${u.id}"><div class="rail">${mk}</div><div class="main hatz">* * *</div></div>`;
    return `<div class="row ${u.k}" id="u${u.id}"><div class="rail">${mk}</div><div class="main ${u.k==='dh'||u.k==='nose'?u.k:''}">${u.a}</div></div>`;
  }
  /* ALL: מצב רצף - כל המסכת בטור אחד, מן הדף הראשון עד האחרון בגלילה אחת. */
  let ALL=false;
  function pagesHTML(from,to){let h='';
    for(let pi=from;pi<=to;pi++){const p=D.pages[pi];
      if(!p.units.length){h+=`<div class="row"><div class="rail"><b class="dafmark" id="d${pi}">${esc(p.daf)}</b></div><div class="main"></div></div>`;continue}
      let first=true;
      for(const u of p.units){h+=unitHTML(u,first?p.daf:null,first?pi:null);first=false}}
    return h}
  function render(si,q){
    cur=Math.max(0,Math.min(SEC.length-1,si));const s=SEC[cur];
    const h=ALL?pagesHTML(0,D.pages.length-1):pagesHTML(s.from,s.to);
    const f=$('#flow');f.innerHTML=q?hl(h,esc(q).replace(/"/g,'&quot;').replace(/'/g,'&#x27;')):h;
    if(!ALL){f.scrollTop=0;f.scrollLeft=SGN>0?f.scrollWidth:0}
    $('#peresel').value=cur;$('#curdaf').textContent=D.pages[s.from].daf;$('#dafsel').value=s.from;
    document.title=`לאוקמי גירסא · ${D.masechet} · ${ALL?'רצף':(s.perekName||s.perek||D.pages[s.from].daf)}`;
    location.hash=`p=${cur}`;
    squeezeRun();
  }
  function hl(h,q){const r=new RegExp('('+q.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')+')','g');return h.replace(/>([^<]+)</g,(m,t)=>'>'+t.replace(r,'<mark>$1</mark>')+'<')}
  function toDaf(pi){const si=secOf(pi);if(si!==cur)render(si);
    setTimeout(()=>{const e=$('#d'+pi);if(e)toEl(e);$('#curdaf').textContent=D.pages[pi].daf;$('#dafsel').value=pi},20)}
  function goDaf(d){const now=+$('#dafsel').value||0;toDaf(Math.max(0,Math.min(D.pages.length-1,now+d)))}
  function goScreen(d){const f=$('#flow');
    if(f.classList.contains('vert'))f.scrollBy({top:d*f.clientHeight*.9,behavior:'smooth'});
    else f.scrollBy({left:-d*f.clientWidth,behavior:'smooth'})}
  function fs(d){const r=document.documentElement;
    const v=Math.max(12,Math.min(60,parseFloat(getComputedStyle(r).getPropertyValue('--fs'))+d));setFs(v)}
  function setFs(v){document.documentElement.style.setProperty('--fs',v+'px');localStorage.setItem('lg-fs',v);sizeBtns(v)}
  function sizeBtns(v){document.querySelectorAll('[data-fs]').forEach(b=>b.classList.toggle('on',+b.dataset.fs===+v))}
  function vert(){const v=$('#flow').classList.toggle('vert');
    ALL=v;localStorage.setItem('lg-vert',v?'1':'');$('#vbtn').classList.toggle('on',v);
    const keep=+$('#dafsel').value||0;render(cur);
    if(v)setTimeout(()=>{const e=$('#d'+keep);if(e)e.scrollIntoView({block:'start'})},30)}
  function panel(id){const p=$('#'+id),o=p.classList.contains('open');document.querySelectorAll('.panel').forEach(x=>x.classList.remove('open'));if(!o)p.classList.add('open')}
  function dec(s){return s.replace(/&quot;/g,'"').replace(/&#x27;/g,"'").replace(/&amp;/g,'&')}
  function txt(u){return dec(u.a.replace(/<[^>]+>/g,'')+' '+u.l.map(l=>l[1].replace(/<[^>]+>/g,'')).join(' '))}
  function search(q){q=q.trim();LASTQ=q;const out=$('#sres');if(q.length<2){out.innerHTML='';return}
   RES=[];let res=RES,n=0;D.pages.forEach((p,pi)=>{for(const u of p.units){const t=txt(u);const k=t.indexOf(q);if(k>-1){n++;if(res.length<120)res.push({pi,id:u.id,daf:p.daf,s:t.slice(Math.max(0,k-40),k+60)})}}});
   out.innerHTML=`<div class="n">${n} תוצאות</div>`+res.map((r,i)=>`<div class="res"><a onclick="jumpR(${i})"><small>${r.daf}</small> …${esc(r.s).replace(esc(q),'<mark>'+esc(q)+'</mark>')}…</a></div>`).join('');
   $('#search').classList.add('open')}
  let RES=[],LASTQ='';function jumpR(i){jump(RES[i].pi,RES[i].id,LASTQ)}
  function jump(pi,id,q){const si=secOf(pi);render(si,q);
    setTimeout(()=>{const e=$('#u'+id);if(e){e.classList.add('hit');toEl(e)}$('#dafsel').value=pi;$('#curdaf').textContent=D.pages[pi].daf},20)}
  function amq(i){$('#q').value=D.am[i][0];search(D.am[i][0])}
  function build(){
   const ds=$('#dafsel');D.pages.forEach((p,i)=>ds.add(new Option(p.daf,i)));ds.onchange=()=>toDaf(+ds.value);
   const ps=$('#peresel');SEC.forEach((s,i)=>ps.add(new Option((s.perek||'רצף')+(s.perekName?' · '+s.perekName:''),i)));ps.onchange=()=>render(+ps.value);
   let t='',lp=-1;for(const [pi,id,s] of D.toc){const si=secOf(pi);
     if(si!==lp){lp=si;t+=`<h3>${esc(SEC[si].perek||'')} ${esc(SEC[si].perekName||'')}</h3>`}
     t+=`<a onclick="jump(${pi},${id})"><small class="n">${esc(D.pages[pi].daf)}</small> ${esc(s)}</a>`}
   $('#tocb').innerHTML=t;
   $('#amb').innerHTML=`<div class="n">${D.nAm} אזכורי אמוראים מסומנים בקובץ; ${D.nPsk} ציטוטי פסוקים שונים</div><div class="chips">`+D.am.map((a,i)=>`<a class="tag" onclick="amq(${i})">${esc(a[0])} <span class="n">${a[1]}</span></a>`).join('')+'</div>';
   $('#qab').innerHTML=D.qa.length?D.qa.map(q=>`<div class="res"><b>${q[0]}</b>: ${esc(q[1])}</div>`).join(''):'לא נמצאו חריגות';
   const sv=+localStorage.getItem('lg-fs');if(sv)setFs(sv);else sizeBtns(24);
   if(localStorage.getItem('lg-vert')){$('#flow').classList.add('vert');$('#vbtn').classList.add('on');ALL=true}
   if(SQ)$('#fbtn').classList.add('on');
   let rsz;addEventListener('resize',()=>{clearTimeout(rsz);rsz=setTimeout(squeezeRun,250)});
   $('#flow').addEventListener('wheel',e=>{const f=$('#flow');if(f.classList.contains('vert'))return;
     if(Math.abs(e.deltaY)>Math.abs(e.deltaX)){f.scrollLeft-=e.deltaY;e.preventDefault()}},{passive:false});
   document.addEventListener('keydown',e=>{
     if(e.target.tagName==='INPUT')return;
     if(e.key==='PageDown'||e.key===' '){goScreen(1);e.preventDefault()}
     if(e.key==='PageUp'){goScreen(-1);e.preventDefault()}
     if(e.ctrlKey&&e.key==='ArrowLeft'){goDaf(1);e.preventDefault()}
     if(e.ctrlKey&&e.key==='ArrowRight'){goDaf(-1);e.preventDefault()}
     if(e.ctrlKey&&(e.key==='='||e.key==='+')){fs(2);e.preventDefault()}
     if(e.ctrlKey&&e.key==='-'){fs(-2);e.preventDefault()}
     if(e.key==='Escape')document.querySelectorAll('.panel').forEach(x=>x.classList.remove('open'))});
   /* קישור עמוק מדף ההגהה: p=מקטע, u=מזהה היחידה. היחידה מודגשת ונגללת אליה. */
   const u0=params.get('u');
   if(u0){let pi=0;D.pages.forEach((p,i)=>{if(p.units.some(x=>x.id==u0))pi=i});jump(pi,+u0)}
   else render(+(params.get('p')||0));
  }
  build();
  '''

  # קישור למסך ההגהה נוסף רק כשיש מסך כזה למסכת הזאת.
  slug=os.path.basename(out_path)[:-5]
  hgbtn=(f'<a href="{slug}-hagaha.html" style="background:var(--gold);color:#2b2620;border-radius:4px;'
         f'padding:3px 10px;text-decoration:none;font-weight:700">הגהה</a>') if hagaha else ''
  page=f'''<!DOCTYPE html><html lang="he" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
  <title>לאוקמי גירסא · {masechet}</title>
  <link href="https://fonts.googleapis.com/css2?family=Frank+Ruhl+Libre:wght@400;500;700;900&display=swap" rel="stylesheet">
  <style>{CSS}</style></head><body>
  <div class="bar"><a href="index.html" style="color:inherit;text-decoration:none"><span class="nm">לאוקמי גירסא</span></a> <span>{masechet}</span>
  <select id="peresel" title="פרק"></select>
  <div class="nav"><button onclick="goDaf(-1)" title="דף קודם (Ctrl+חץ ימין)">› הקודם</button><span class="daf" id="curdaf"></span><button onclick="goDaf(1)" title="דף הבא (Ctrl+חץ שמאל)">‹ הבא</button></div>
  <select id="dafsel" title="דף"></select>
  <input id="q" placeholder="חיפוש ב{masechet}" oninput="search(this.value)" onfocus="search(this.value)">
  <span class="sp"></span>
  <button onclick="panel('toc')">תוכן העניינים</button><button onclick="panel('am')">אמוראים</button><button onclick="panel('qa')">בקרה</button>{hgbtn}
  <button id="vbtn" onclick="vert()" title="כל המסכת בטור אחד, בגלילה מלמעלה למטה">טור רצוף</button>
  <button id="fbtn" onclick="squeeze()" title="דחיסה עדינה שמעלה מילה בודדת שגלשה לשורה נפרדת">איחוי שורות</button>
  <button onclick="toPdf()" title="כל המסכת: בחלון שייפתח בחר ביעד 'שמירה כ-PDF'. כל פרק פותח עמוד חדש">כל המסכת ל-PDF</button>
  <button data-fs="18" onclick="setFs(18)">קטן</button><button data-fs="24" onclick="setFs(24)">רגיל</button><button data-fs="32" onclick="setFs(32)">גדול</button>
  <button onclick="fs(2)" title="Ctrl+=">א+</button><button onclick="fs(-2)" title="Ctrl+-">א-</button>
  <button onclick="document.body.classList.toggle('hc')">ניגודיות</button><button onclick="window.print()" title="הדפסת הפרק הנוכחי בלבד">הדפס פרק</button></div>
  <div class="panel" id="search"><button class="x" onclick="panel('search')">×</button><h3>תוצאות חיפוש</h3><div id="sres"></div></div>
  <div class="panel" id="toc"><button class="x" onclick="panel('toc')">×</button><h3>תוכן העניינים - נושאי הסוגיות</h3><div id="tocb"></div></div>
  <div class="panel" id="am"><button class="x" onclick="panel('am')">×</button><h3>אמוראים ותנאים - לפי הסימון בקובץ</h3><div id="amb"></div></div>
  <div class="panel" id="qa"><button class="x" onclick="panel('qa')">×</button><h3>בקרת הקובץ - חריגות שנמצאו בהמרה</h3><div id="qab"></div></div>
  <div class="flow" id="flow"></div>
  <script>const DATA={J};</script><script>{JS}</script></body></html>'''

  open(out_path,'w',encoding='utf-8').write(page)
  return {'pages':len(pages),'toc':len(toc),'qa':qa}

if __name__=='__main__':
  r=build(sys.argv[1],sys.argv[2],sys.argv[3]); print(r['pages'],'pages',len(r['qa']),'qa')
