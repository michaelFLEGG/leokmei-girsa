import json, html, re, collections, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from styles_map import ROLE, CS, MISSING_FONTS
import match_sources
MISSING_FONTS_REV={v:k for k,v in MISSING_FONTS.items()}
def build(json_path, out_path, masechet, hagaha=False, sources=None):
  blocks = json.load(open(json_path, encoding='utf-8'))

  # מפת הסגנונות יושבת בקובץ אחד, tools/styles_map.py, שגם מסך ההגהה קורא
  # ממנו. עותק שני היה נפרד בשקט ושובר את העיגון שבין שני המסכים.

  def fuse_stars(runs):
      """כוכביות שוורד פיצל לשני קטעי-תו מתאחות לקטע אחד. בלי זה
      שרשרת הליגטורות נקטעת באמצע, והעיטור אינו נוצר."""
      out=[]
      for r in runs:
          if out and set(out[-1]['t'])<=set('* ') and set(r['t'])<=set('* ') \
             and ('*' in out[-1]['t'] or '*' in r['t']):
              out[-1]=dict(out[-1],t=out[-1]['t']+r['t'])
          else: out.append(dict(r))
      return out

  def runs_html(runs):
      out=[]
      for r in fuse_stars(runs):
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
  # סגנון שאינו ממופה ומופיע הרבה אינו תקלה קטנה: מדור שלם מאבד את
  # צורתו. המסכת נבנית ומתפרסמת בכל זאת - השמטתה היתה גרועה מכך -
  # אבל היא מסומנת באדום בשער ובבקרה.
  heavy=[f'{s} ({n})' for s,n in unknown.most_common() if n>20]
  # סגנון תו שאינו במפה מאבד את עיצובו בלי שיאמר דבר. הוא נמנה כאן כדי שלא ייפער חור שקט.
  unk_cs=collections.Counter(r['cs'] for b in blocks for r in b['runs'] if r['cs'] and r['cs'] not in CS)
  for s,n in unk_cs.items(): qa.append(('סגנון תו לא ממופה',f'{s} ({n})'))
  heavy+= [f'{s} תו ({n})' for s,n in unk_cs.most_common() if n>20]
  if heavy: qa.insert(0,('טעון תשומת לב','סגנון שאינו ממופה ומופיע הרבה: '+', '.join(heavy[:8])))
  long_anchor=[b for b in blocks if b['style']=='חלון 3' and len(b['text'])>25]
  for b in long_anchor: qa.append(('חלון ארוך',b['text'][:40]))
  empty_anchor=[b for b in blocks if b['style']=='חלון 3' and not b['text'].strip()]
  if empty_anchor: qa.append(('חלון ריק',f'{len(empty_anchor)} חלונות ריקים'))

  # ---------- pages ----------
  pages=[]  # {daf, perek, perekName, units:[...]}
  cur=None; perek=''; perekName=''; unit=None
  order=[]
  toc=[]
  # החץ ◄ שבחלון הצד אינו קישוט: פירושו "כך נפסק להלכה", והוא שייך
  # ליחידה שאחריו. חלון שכולו חץ אינו פותח יחידה משלו - הוא מדליק דגל
  # שנצמד ליחידה הבאה. בלעדי זה נפתחו בדף עשרות שורות ריקות.
  halacha=False
  def flag(u):
      nonlocal halacha
      if halacha: u['h']=1; halacha=False
      return u
  def toc_text(raw):
      """כותרת לתוכן העניינים, מן הטקסט הגולמי ולפני כל בריחה.
      כך אין ישויות HTML, ואין חץ ואין טאבים."""
      return re.sub(r'\s+',' ',raw.replace('◄',' ').replace('\t',' ')).strip()
  def add_toc(kind,b):
      t=toc_text(b['text'])
      if t: toc.append([len(pages)-1,b['i'],t,kind])
  n_skip=collections.Counter()
  for b in blocks:
      r=ROLE.get(b['style'],'body'); h=runs_html(b['runs']); t=b['text'].strip()
      # ריהוט עמוד (כותרת רצה, שם המסכת, תווית המסילה) אינו תוכן ואינו
      # נכתב לדף. הוא נספר ומדווח, כדי שההשמטה לא תהיה שקטה.
      if r=='skip':
          n_skip[b['style']]+=1; continue
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
          if t=='◄':
              halacha=True; continue        # דגל בלבד, אינו פותח יחידה
          unit=flag({'k':'u','a':h,'l':[],'id':b['i']}); cur['units'].append(unit)
      elif r.startswith('body'):
          if unit is None or unit['k']!='u':
              unit=flag({'k':'u','a':'','l':[],'id':b['i']}); cur['units'].append(unit)
          unit['l'].append([r[5:] if len(r)>4 else '',h])
      elif r=='mishna':
          if cur['units'] and cur['units'][-1]['k']=='m': cur['units'][-1]['l'].append(['',h])
          else:
              cur['units'].append(flag({'k':'m','a':'','l':[['',h]],'id':b['i']})); add_toc('m',b)
          unit=None
      elif r in ('dh','nose','hatz','perek-num','perek-name','perek-range','perek-start','hadran'):
          cur['units'].append(flag({'k':r,'a':h,'l':[],'id':b['i']})); unit=None
          if r in ('dh','nose'): add_toc(r,b)

  # יחידה בלי חלון ובלי פסקת גוף שיש בה טקסט אינה נכתבת לדף: בדף היא
  # נראית כשורה ריקה, ולומד אינו יודע שחסר כאן דבר. המונה מוצג בבקרה.
  def bare(x): return re.sub('<[^>]+>','',x).replace('\u200f','').strip()
  n_units=sum(len(p['units']) for p in pages); n_empty=0
  drop_ids=set()
  for p in pages:
      keep=[]
      for u in p['units']:
          if not bare(u['a']) and not any(bare(x[1]) for x in u['l']):
              n_empty+=1; drop_ids.add(u['id']); continue
          keep.append(u)
      p['units']=keep
  if n_empty:
      qa.append(('יחידות ריקות',f'{n_empty} יחידות ריקות הושמטו מן הדף'))
  for st,n in n_skip.most_common():
      why=('הגופן %s אינו באתר, והטקסט היה נקרא כג\'יבריש'%MISSING_FONTS_REV[st]) \
          if st in MISSING_FONTS_REV else 'ריהוט עמוד; הדף מצייר אותו בעצמו'
      qa.append(('הושמט במתכוון',f'{st}: {n} פסקאות. {why}'))
  if n_units and n_empty > n_units*0.05:
      raise SystemExit('עצירה: %d מתוך %d היחידות ריקות (מעל חמישה אחוזים) ב%s. '
                       'לא מפרסמים לפני בדיקה.' % (n_empty,n_units,masechet))
  toc=[e for e in toc if e[1] not in drop_ids]
  # שער: ערך שנשארה בו ישות HTML עוצר את הבנייה. הכותרת נבנית מן
  # הטקסט הגולמי, ולכן ישות כאן פירושה שמשהו נשבר בצינור.
  for e in toc:
      if re.search(r'&[a-zA-Z#0-9]+;', e[2]):
          raise SystemExit('עצירה: ישות HTML בתוכן העניינים של %s: %r' % (masechet,e[2]))
  n_nose=sum(1 for e in toc if e[3]=='nose')
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

  # ---------- הצמדת הגמרא המנוקדת (ט2) ----------
  # ההצמדה נעשית כאן, בבנייה, ולא בדפדפן. לדף נכתב רק המזהה; הטקסט
  # עצמו יושב בקובץ נפרד ונטען רק בלחיצה הראשונה.
  srcmeta=None
  if sources:
      st=match_sources.attach(pages,sources)
      srcmeta={'slug':os.path.basename(out_path)[:-5],
               'attribution':sources.get('attribution',''),
               'matched':st['matched'],'eligible':st['eligible']}
      qa.append(('מקור מן הגמרא',
                 '%d יחידות מתוך %d הוצמדו למקטע בגמרא; %d לא עברו את הסף ואין להן כפתור "מקור"'
                 % (st['matched'],st['eligible'],st['low'])))
  data={'masechet':masechet,'pages':pages,'toc':toc,'am':amlist,'qa':qa,'nPsk':len(psk),'nAm':sum(am.values()),'src':srcmeta}
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
  /* היחס בין גודל האות לרוחב השורה נעול. כל המידות נמדדות ב-em של גוף
     הטקסט, ולכן הגדלה והקטנה משנות הכל יחד ושבירת השורות אינה זזה.

     הערכים נמדדו מקובץ הוורד עצמו (27.9.2026), ולא נבחרו לעין:
       sectPr - עמוד 170x260 מ"מ, שוליים 20 ימין ו-10 שמאל, שני טורים
                ומסילה של 20 מ"מ ביניהם. רוחב הטור: (140-20)/2 = 60 מ"מ.
       Normal - szCs 18, כלומר גוף של 9 נקודות, ומרווח שורה מדויק 11.
     9 נקודות הן 3.175 מ"מ, ומכאן: הטור הוא 60/3.175 = 18.9em והמסילה
     20/3.175 = 6.3em, והשוליים 10/3.175 = 3.15em.

     עד היום עמדו כאן 15.46em ו-5.15em. אלה 60 מ"מ ו-20 מ"מ חלקי 11
     נקודות - כלומר היחס נגזר ממרווח השורה במקום מגודל האות, והשורה
     באתר יצאה צרה בכ-18 אחוזים מזו שבספר. משם באו השורות שנשברו
     לשתיים ו"השורה היתומה".

     והערך שנקבע כאן אינו 18.9 אלא 20.75, מפני שהחשבון לבדו אינו מספיק
     ונדרש כיול. נמדדו 43 פסקאות גוף ארוכות מכל רוחב המסכת: נספרו
     השורות שוורד פורש בהן כל פסקה, ומולן נספרו השורות שהדפדפן פורש
     באותו טקסט ברוחבים שונים. התוצאה:
         15.46em - 9 אחוזי התאמה   (המצב עד היום)
         18.90em - 79 אחוזים       (החשבון הגאומטרי לבדו)
         20.75em - 95 אחוזים       (הנבחר)
     ההפרש נובע מן הגופן: frank.ttf שבדפדפן רחב בכעשרה אחוזים ל-em
     מ-FrankRuehl שוורד מצייר. המסילה והשוליים גדלו באותו יחס בדיוק,
     כדי שפרופורציית העמוד תישמר: מסילה = טור חלקי שלוש, שוליים = חלקי שש.

     --fs נקבע ל-18 כדי שרוחב הטור על המסך יישאר כשהיה (כ-373 פיקסל
     במקום 371), והשורה תחזיק מעתה כשליש יותר טקסט - כמו בספר. */
  /* סולם הכותרות נגזר ממידת הגוף שבוורד, ולא ממספרים שנבחרו לעין:
     נושא = נקודה אחת מעל הגוף, משנה = כגוף, וד"ה משנה = נקודה אחת
     מתחת למשנה. שינוי --body-pt מזיז את שלושתם יחד. */
  :root{--fs:18px;--body-pt:9;--measure:20.75em;--rail:6.92em;--gut:3.46em;
        --ink:#1d1a16;--paper:#fbf8f1;--grey:#767171;--gold:#c9a24a;--red:#a83c2f;--bar:46px}
  *{box-sizing:border-box}
  html,body{margin:0;height:100%;background:#e9e4d8;color:var(--ink);font-family:'Frank','Frank Ruhl Libre',serif;overflow:hidden}
  /* פריסת עמודה: בטלפון הסרגל נשבר לשתי שורות ויותר, וגובה קבוע לו
     הסתיר את ראש הטקסט. מעתה הסרגל תופס את גובהו והטקסט את השאר. */
  body{display:flex;flex-direction:column}
  body.hc{--ink:#000;--paper:#fff;--grey:#333}
  .bar{position:relative;z-index:5;flex:0 0 auto;display:flex;flex-wrap:wrap;gap:6px 10px;align-items:center;padding:7px 12px;background:#2b2620;color:#f1ead9;font-size:14px;min-height:var(--bar)}
  .bar .nm{font-family:'Leukmey','Vilna',serif;font-size:20px;line-height:1}
  .bar .sp{flex:1}
  .bar button,.bar select,.bar input{font:inherit;background:#4a4137;color:#f1ead9;border:0;border-radius:4px;padding:3px 9px;cursor:pointer}
  .bar input{cursor:text;width:150px} .bar button.on{background:var(--gold);color:#2b2620}
  .nav{display:flex;gap:4px;align-items:center}
  .nav .daf{min-width:52px;text-align:center;font-family:'VilnaG','Vilna',serif;font-size:17px}
  .flow{font-size:var(--fs);line-height:1.06;flex:1 1 auto;min-height:0;background:var(--paper);
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
  /* פסקה מוזחת (פיסקת תשובה, וסעיפי רשימה): הזחה תלויה, כמו בוורד */
  .main p.in{padding-right:.9em;text-indent:-.9em}
  .dafmark{display:block;font-family:'VilnaG','Vilna',serif;font-size:1.3em;line-height:1;color:var(--red);margin-top:.25em}
  .anchor{display:inline-block;font-family:'Vilna',serif;font-weight:900;font-size:.9em;line-height:1.18;
          color:#5a5044;white-space:nowrap;max-width:calc(var(--rail) - .4em);overflow:hidden;text-overflow:ellipsis}
  .mlabel{font-size:.55em;color:#8a7d66}
  /* החץ של "כך נפסק להלכה". הוא יושב במסילה לפני חלון הכותרת, ברוחב
     קבוע, כדי שלא ידחק אותה ולא יקצר אותה בלא צורך. */
  .hal{display:inline-block;width:.8em;color:var(--gold);font-size:.85em;line-height:1}
  .row[data-halacha] .anchor{max-width:calc(var(--rail) - 1.3em)}
  .mishna{background:#eeeae1;padding:.1em .15em;margin:.15em 0;font-family:'Vilna',serif;font-weight:700;font-size:1em;line-height:1.12;border-right:.1em solid var(--gold)}
  .dh{text-align:center;text-align-last:center;font-family:'Vilna',serif;font-weight:900;
      font-size:calc((var(--body-pt) - 1) / var(--body-pt) * 1em);line-height:1.15;margin:.3em 0 .08em}
  .nose{text-align:center;text-align-last:center;font-family:'Vilna',serif;font-weight:700;
        font-size:calc((var(--body-pt) + 1) / var(--body-pt) * 1em);line-height:1.15;margin-top:.45em;color:var(--ink)}
  /* ב. הכוכביות אינן כוכביות: בגופני וילנא יש שרשרת ליגטורות ב-rlig,
     וכל מספר כוכביות נותן עיטור אחר. letter-spacing ביטל אותה, ולכן
     הוא חוזר ל-normal והליגטורות נדלקות במפורש. */
  .hatz{text-align:center;text-align-last:center;font-family:'Vilna',serif;font-weight:900;
        font-size:1.1em;letter-spacing:normal;color:#8a7d66;margin:.3em 0;
        font-variant-ligatures:common-ligatures;font-feature-settings:"rlig" 1,"liga" 1}
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
  /* שלושת סוגי הערכים בתוכן. נושא הוא העיקר ולכן אין לו תווית;
     ד"ה ומשנה מוזחים ונושאים תווית קטנה, ומשנה בצבע פס-המשנה. */
  .panel a.t-dh,.panel a.t-m{padding-right:1.3em;font-size:14px}
  .panel a.t-dh{font-family:'Vilna',serif;font-weight:700}
  .tl{display:inline-block;font-size:11px;background:#eeeae1;color:#8a7d66;border-radius:3px;padding:0 5px;margin-left:5px;font-family:'Frank',serif;font-weight:400}
  .tl.tlm{background:#f4e9cd;color:#8a6d2f}
  .panel .x{float:left;background:none;border:0;font-size:22px;cursor:pointer;color:#5a5044}
  .panel .n{color:#8a7d66;font-size:12px} .res{padding:5px 0;border-bottom:1px dotted #d9d1bd} .res small{color:#8a7d66}
  .tag{display:inline-block;background:#eeeae1;border-radius:3px;padding:0 6px;margin:2px;font-size:13px}
  .chips{display:flex;flex-wrap:wrap}
  /* ---- מצב עריכה (מנהל) ---- */
  .ed [contenteditable]{outline:1px dashed rgba(201,162,74,.75);outline-offset:1px;border-radius:2px}
  .ed [contenteditable]:focus{outline:1.5px solid var(--gold);background:rgba(201,162,74,.10)}
  .ed [data-edited]{background:rgba(74,107,63,.13)}
  .edbar{position:fixed;bottom:0;right:0;left:0;z-index:8;display:flex;flex-wrap:wrap;gap:8px 14px;
         align-items:center;padding:7px 14px;background:#4a6b3f;color:#fff;font-size:15px}
  .edbar button{font:inherit;font-size:14px;background:#3d5a34;color:#fff;border:0;border-radius:4px;padding:4px 12px;cursor:pointer}
  .edbar .sp{flex:1}
  .edrow{padding:7px 0;border-bottom:1px dotted #d9d1bd;line-height:1.5}
  .edrow .was{color:#a83c2f;text-decoration:line-through} .edrow .now{color:#4a6b3f;font-weight:700}
  .edrow small{color:#8a7d66} .edrow button{font:inherit;font-size:13px;background:#eeeae1;border:1px solid #e0d8c4;border-radius:4px;padding:2px 9px;cursor:pointer;margin-right:6px}
  .edlost{background:#fdf1d8;border-right:3px solid #a83c2f;padding-right:8px}
  .edsum{background:#eeeae1;border-radius:5px;padding:7px 11px;margin-bottom:8px;font-size:14px;line-height:1.6}
  /* ---- הצע תיקון (לכל הלומדים) ---- */
  .pick #flow .main p:hover,.pick #flow .anchor:hover,.pick #flow .main.dh:hover,.pick #flow .main.nose:hover{
    background:rgba(201,162,74,.28);cursor:crosshair;border-radius:2px}
  .hint{position:fixed;top:calc(var(--bar) + 8px);right:50%;transform:translateX(50%);z-index:9;
        background:#2b2620;color:#f1ead9;padding:7px 16px;border-radius:5px;font-size:15px;box-shadow:0 2px 10px rgba(0,0,0,.3)}
  .modal{position:fixed;inset:0;z-index:10;background:rgba(29,26,22,.45);display:flex;align-items:center;justify-content:center;padding:14px}
  .modal .box{background:var(--paper);border-radius:9px;max-width:540px;width:100%;max-height:88vh;overflow:auto;
              padding:16px 20px;box-shadow:0 6px 30px rgba(0,0,0,.35);font-size:15px;line-height:1.6}
  .modal h3{margin:0 0 4px;font-family:'Vilna',serif;font-weight:700;font-size:20px}
  .modal .ref{color:#8a7d66;font-size:13px;margin-bottom:9px}
  .modal .sel{background:#fff;border:1px dashed #d9d1bd;border-radius:5px;padding:8px 11px;margin-bottom:10px;max-height:150px;overflow:auto}
  .modal label{display:block;margin:9px 0 3px;font-size:14px;color:#5a5044}
  .modal textarea,.modal input{font:inherit;width:100%;border:1px solid #d9d1bd;border-radius:5px;padding:6px 9px;background:#fff}
  .modal textarea{min-height:92px;resize:vertical}
  .modal .btns{display:flex;flex-wrap:wrap;gap:8px;margin-top:13px}
  .modal button{font:inherit;font-size:15px;border:0;border-radius:5px;padding:7px 16px;cursor:pointer;background:#eeeae1;color:#4a4137}
  .modal button.go{background:#4a6b3f;color:#fff}
  .sgrow{padding:7px 0;border-bottom:1px dotted #d9d1bd;line-height:1.5}
  .sgrow q{color:#5a5044} .sgrow b{display:block} .sgrow small{color:#8a7d66}
  .sgrow button{font:inherit;font-size:13px;background:#eeeae1;border:1px solid #e0d8c4;border-radius:4px;padding:2px 9px;cursor:pointer}
  /* ---- מגירת "מקור": הגמרא המנוקדת ---- */
  .srcb{font:inherit;font-size:.5em;line-height:1;background:none;border:1px solid #d9d1bd;color:#8a7d66;
        border-radius:3px;padding:1px 5px;margin-right:.3em;cursor:pointer;opacity:.45;vertical-align:.15em}
  .srcb:hover,.srcb:focus{opacity:1;background:var(--gold);color:#2b2620;border-color:#a8842f}
  .src{position:fixed;z-index:9;background:var(--paper);box-shadow:0 -2px 18px rgba(0,0,0,.25);
       display:flex;flex-direction:column;font-size:17px;line-height:1.75}
  .src.peek{left:0;right:0;bottom:0;height:38vh}
  .src.split{left:0;top:var(--barH,52px);bottom:0;width:50vw;box-shadow:2px 0 18px rgba(0,0,0,.22)}
  .src.full{left:0;right:0;top:0;bottom:0}
  body.splitsrc .flow{width:50vw;margin-left:auto}
  .srchd{display:flex;flex-wrap:wrap;gap:6px 10px;align-items:center;padding:7px 14px;background:#2b2620;color:#f1ead9;font-size:14px;flex:0 0 auto}
  .srchd b{font-family:'VilnaG','Vilna',serif;font-size:17px;font-weight:400}
  .srchd .sp{flex:1}
  .srchd button{font:inherit;font-size:13px;background:#4a4137;color:#f1ead9;border:0;border-radius:4px;padding:3px 10px;cursor:pointer}
  .srchd button.on{background:var(--gold);color:#2b2620}
  .srcbody{flex:1 1 auto;overflow:auto;padding:12px 18px}
  .srcbody h4{margin:14px 0 6px;font-size:14px;font-weight:500;color:#8a7d66;border-bottom:1px solid #e0d8c4;padding-bottom:3px}
  .srcseg{background:#fdf6e3;border-right:3px solid var(--gold);border-radius:4px;padding:9px 12px}
  .srcall p{margin:0 0 .5em;padding:2px 5px;border-radius:3px}
  .srcall p.hit{background:#fdf1d8;box-shadow:inset 3px 0 0 var(--gold)}
  .srcft{flex:0 0 auto;padding:6px 14px;font-size:12px;color:#8a7d66;background:#f3eee2;border-top:1px solid #e0d8c4}
  .srcbody .ld{color:#8a7d66;font-size:15px}
  @media(max-width:760px){.src.split{left:0;right:0;top:auto;bottom:0;width:auto;height:60vh}
    body.splitsrc .flow{width:auto;margin-left:0}}
  @media print{.src,.srcb{display:none!important}}
  /* ---- הדפסה: עמוד הספר עצמו ----
     עד היום הדפיס הדף טור אחד על גיליון של 90 מ"מ, וזה לא היה העמוד
     של בעל הפרויקט. מעתה הגיאומטריה היא זו שנמדדה מקובץ הוורד:

       גיליון 170x260 מ"מ, שוליים עליון 10 ותחתון 5.
       שולי ימין 0 - מפני שהמסילה עצמה היא 20 המ"מ שוורד קורא להם
       שוליים ימניים - ושולי שמאל 10. רוחב התוכן: 160 מ"מ.
       שני טורים של 80 מ"מ בלי רווח ביניהם, וכל טור הוא מסילה של
       20 ומידה של 60, בדיוק כבוורד.

     גודל האות בהדפסה נגזר מן היחס הנעול ולא נקבע לחוד: המידה היא
     60 מ"מ, והיחס 20.75, ולכן האות היא 60/20.75 מ"מ (כ-8.2 נקודות).
     בוורד האות היא 9 נקודות, וההפרש הוא אותו הפרש שנמדד בשלב ח0 -
     frank.ttf שבדפדפן רחב בכעשרה אחוזים ל-em מ-FrankRuehl. לו נקבעה
     האות ל-9 נקודות היו השורות נשברות מוקדם מבוורד, וזה בדיוק מה
     שהכלל הנעול בא למנוע. כך השורות מתלכדות עם הספר, ורשת השורות
     נשארת 11 נקודות כבוורד. */
  @media print{
    .bar,.panel{display:none}
    html,body{overflow:visible;background:#fff;height:auto}
    body{display:block}
    :root{--measure:60mm;--rail:20mm;--gut:0;--fs:calc(60mm / 20.75)}
    .flow{width:160mm;height:auto;overflow:visible;padding:0;
          font-size:var(--fs);line-height:11pt;
          columns:80mm 2;column-gap:0;column-rule:0;column-fill:auto}
    /* מצב הרצף שעל המסך אינו נגרר להדפסה: העמוד המודפס הוא תמיד
       עמוד הספר, בשני טורים. */
    .flow.vert{width:160mm;columns:80mm 2;column-gap:0;column-fill:auto;padding:0}
    .flow.vert .row{width:auto;margin:0}
    .row{grid-template-columns:20mm 60mm;break-inside:avoid}
    .anchor{max-width:17mm}
    /* פרק חדש פותח טור חדש, כמו sectPr type=nextColumn בוורד */
    .row.perek-num{break-before:column}
    .flow > .row.perek-num:first-child{break-before:auto}
    @page{size:170mm 260mm;margin:10mm 0 5mm 10mm}
  }
  /* שאילתת הטלפון מוגבלת למסך במפורש. בלעדי זה היא תפסה גם בהדפסה:
     עמוד של 170 מ"מ הוא כ-643 פיקסל, כלומר פחות מ-760, והיא באה אחרי
     גוש ההדפסה - ולכן היא ביטלה את שני הטורים ואת רוחב המסילה, והעמוד
     המודפס יצא טור אחד רחב. */
  @media screen and (max-width:760px){:root{--fs:20px}
    .flow{column-width:auto;column-count:1;column-rule:0;width:auto;padding:.7em .8em}
    .row{grid-template-columns:1fr} .rail{text-align:right;padding:0}
    .anchor{max-width:none;display:inline;margin-top:.2em;font-size:.82em;color:#4a4137}
    .row[data-halacha] .anchor{max-width:none}
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
    /* ◄ פירושו "כך נפסק להלכה". הוא נשען על היחידה שאחריו, ולכן הוא
       נכתב כאן במסילה שלה ולא כשורה משלו. */
    const H=(u.h?' data-halacha="1"':'')+(u.ref?' data-ref="'+u.ref+'"':''),
          hal=u.h?'<span class="hal" title="כך נפסק להלכה">\u25c4</span>':'',
          sb=u.ref?`<button class="srcb" onclick="openSrc('${u.ref}')" title="הגמרא המנוקדת (מקש מ)">מקור</button>`:'';
    if(u.k==='u')return `<div class="row u" id="u${u.id}"${H}><div class="rail">${mk}${hal}<span class="anchor">${u.a}</span></div><div class="main">${u.l.map((l,n)=>`<p class="${l[0]}">${l[1]}${n===u.l.length-1?sb:''}</p>`).join('')}</div></div>`;
    if(u.k==='m')return `<div class="row" id="u${u.id}"${H}><div class="rail">${mk}${hal}<span class="mlabel">משנה</span></div><div class="main mishna">${u.l.map((l,n)=>`<p>${l[1]}${n===u.l.length-1?sb:''}</p>`).join('')}</div></div>`;
    /* הכוכביות מוצגות כלשונן בקובץ. מספרן אינו מנורמל: כל מספר נותן
       עיטור אחר בגופן, וזו כוונת המחבר. */
    if(u.k==='hatz')return `<div class="row" id="u${u.id}"${H}><div class="rail">${mk}${hal}</div><div class="main hatz">${u.a}</div></div>`;
    return `<div class="row ${u.k}" id="u${u.id}"${H}><div class="rail">${mk}${hal}</div><div class="main ${u.k==='dh'||u.k==='nose'?u.k:''}">${u.a}${sb}</div></div>`;
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
    markEditable();applyEdits();
    if(EDIT)setEdit(true);
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
   let t='',lp=-1;const TL={dh:'ד\u05f4ה',m:'משנה'};
   for(const [pi,id,s,kind] of D.toc){const si=secOf(pi);
     if(si!==lp){lp=si;t+=`<h3>${esc(SEC[si].perek||'')} ${esc(SEC[si].perekName||'')}</h3>`}
     const lab=TL[kind]?`<span class="tl${kind==='m'?' tlm':''}">${TL[kind]}</span>`:'';
     t+=`<a class="t-${kind}" onclick="jump(${pi},${id})"><small class="n">${esc(D.pages[pi].daf)}</small> ${lab}${esc(s)}</a>`}
   $('#tocb').innerHTML=t;
   $('#amb').innerHTML=`<div class="n">${D.nAm} אזכורי אמוראים מסומנים בקובץ; ${D.nPsk} ציטוטי פסוקים שונים</div><div class="chips">`+D.am.map((a,i)=>`<a class="tag" onclick="amq(${i})">${esc(a[0])} <span class="n">${a[1]}</span></a>`).join('')+'</div>';
   $('#qab').innerHTML=D.qa.length?D.qa.map(q=>`<div class="res"><b>${q[0]}</b>: ${esc(q[1])}</div>`).join(''):'לא נמצאו חריגות';
   const sv=+localStorage.getItem('lg-fs');if(sv)setFs(sv);else sizeBtns(18);
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
  /* =================== מצב עריכה למנהל ===================
     האתר סטטי ונבנה מחדש מן הוורד, ולכן עריכה כאן אינה יכולה לשנות
     את המקור. היא נשמרת במכשיר, מוחלת מחדש בכל טעינה, ומיוצאת לקובץ
     שנכנס לוורד במעקב דרך הכלי היחיד שכותב לשם.

     העיגון אינו נשען על מספר הפסקה בלבד: לכל עריכה נשמרים גם הנוסח
     שהיה, הנוסח החדש, ציון הדף וכארבעים תווים מסביב. אם הפסקאות זזו
     בוורד, העריכה מאותרת מחדש באותו דף ועמוד לכל צד - ורק אם נמצאה
     התאמה אחת ויחידה. אחרת היא מוצגת בקול כ"תלושה" ואינה מוחלת, כדי
     ששינוי מבני בוורד לא יפזר עריכות על פסקאות זרות. */
  const AKEY='lg-admin', EKEY='lg-ed-'+SLUG, ADMIN_WORD='לאוקמי';
  const OKCLS=['am','ps','kt','hs','ot','tn','ns','df','b'];
  let ED=[]; try{ED=JSON.parse(localStorage.getItem(EKEY)||'[]')}catch(e){ED=[]}
  let EDIT=false, EDSTAT={taken:0,lost:0};
  function isAdmin(){try{return localStorage.getItem(AKEY)==='1'}catch(e){return false}}
  function saveED(){try{localStorage.setItem(EKEY,JSON.stringify(ED))}catch(e){}}
  function plain(h){const d=document.createElement('div');d.innerHTML=h;return d.textContent}

  /* כל המקומות הניתנים לעריכה, בכל המסכת, באותו סדר שבו הם מסומנים בדף */
  function slots(){const out=[];
    D.pages.forEach((p,pi)=>p.units.forEach(u=>{
      if(u.k==='u'){ if(u.a)out.push({pi,daf:p.daf,k:'u'+u.id+'.0',t:plain(u.a)});
        u.l.forEach((l,i)=>out.push({pi,daf:p.daf,k:'u'+u.id+'.'+(i+1),t:plain(l[1])})); }
      else if(u.k==='m'){ u.l.forEach((l,i)=>out.push({pi,daf:p.daf,k:'u'+u.id+'.'+(i+1),t:plain(l[1])})); }
      else if(u.k==='dh'||u.k==='nose'){ out.push({pi,daf:p.daf,k:'u'+u.id+'.0',t:plain(u.a)}); }
    }));
    return out}
  let SLOTS=null;
  function dafKey(d){if(!d)return null;const V={'א':1,'ב':2,'ג':3,'ד':4,'ה':5,'ו':6,'ז':7,'ח':8,'ט':9,'י':10,'כ':20,'ל':30,'מ':40,'נ':50,'ס':60,'ע':70,'פ':80,'צ':90,'ק':100,'ר':200,'ש':300,'ת':400};
    const t=d.trim();const am=t.endsWith(':')?1:0;let n=0;
    for(const c of t.replace(/[.:"'\u05f3\u05f4]/g,''))n+=V[c]||0;return n?n*2+am:null}

  /* מאתר את המקום של עריכה. מחזיר מפתח, או null אם היא תלושה. */
  function locate(e){
    if(!SLOTS)SLOTS=slots();
    const byKey=SLOTS.find(s=>s.k===e.k);
    if(byKey&&(byKey.t===e.now||byKey.t===e.was))return byKey.k;
    const k0=dafKey(e.daf);
    const win=SLOTS.filter(s=>{const k=dafKey(s.daf);return k0===null||k===null?true:Math.abs(k-k0)<=1});
    for(const want of [e.was,e.now]){
      const hits=win.filter(s=>s.t===want);
      if(hits.length===1)return hits[0].k;
    }
    return null}

  /* מסמן כל מקום שניתן לעריכה, ומחיל את מה שנשמר */
  function markEditable(){
    const f=$('#flow');
    f.querySelectorAll('.row').forEach(row=>{
      const id=row.id;if(!id)return;
      const a=row.querySelector('.anchor');
      if(a)a.dataset.ek=id+'.0';
      const m=row.querySelector('.main');
      if(!m)return;
      const ps=m.querySelectorAll('p');
      if(ps.length)ps.forEach((x,i)=>x.dataset.ek=id+'.'+(i+1));
      else if(m.classList.contains('dh')||m.classList.contains('nose'))m.dataset.ek=id+'.0';
    })}
  function applyEdits(){
    if(!ED.length)return;
    SLOTS=slots();
    const f=$('#flow');let taken=0,lost=0,keep=[];
    for(const e of ED){
      const k=locate(e);
      if(k===null){lost++;e.lost=1;keep.push(e);continue}
      e.lost=0;if(k!==e.k)e.k=k;
      const el=f.querySelector('[data-ek="'+k+'"]');
      const cur=el?el.textContent:(SLOTS.find(s=>s.k===k)||{}).t;
      if(cur===e.now){taken++;continue}          /* כבר נכנס לוורד - אין מה להחיל */
      if(el&&cur===e.was){el.textContent=e.now;el.dataset.edited='1'}
      keep.push(e)}
    EDSTAT={taken,lost};
    if(keep.length!==ED.length){ED=keep;saveED()}
    if($('#edn'))$('#edn').textContent=ED.length}

  function ctxOf(el){
    const rows=[...$('#flow').querySelectorAll('.main p, .main.dh, .main.nose, .anchor')];
    const i=rows.indexOf(el);
    return {b:(i>0?rows[i-1].textContent:'').slice(-40),a:(i>=0&&i<rows.length-1?rows[i+1].textContent:'').slice(0,40)}}

  function clean(el){
    /* רק עיצוב התו המוכר נשאר. כל תגית אחרת מוסרת והטקסט נשמר. */
    el.querySelectorAll('*').forEach(n=>{
      const tag=n.tagName.toLowerCase();
      const ok=(tag==='i'&&[...n.classList].every(c=>OKCLS.includes(c)))||tag==='b';
      n.removeAttribute('style');
      if(!ok){const t=document.createTextNode(n.textContent);n.replaceWith(t)}})}

  function edFocus(ev){const el=ev.target.closest('[contenteditable]');if(!el)return;
    el.__was=el.textContent}
  function edBlur(ev){const el=ev.target.closest('[contenteditable]');if(!el)return;
    clean(el);
    const now=el.textContent, was=el.__was;
    if(was===undefined||now===was)return;
    const k=el.dataset.ek;const row=el.closest('.row');
    const daf=(()=>{let r=row;while(r){const d=r.querySelector('.dafmark');if(d)return d.textContent;r=r.previousElementSibling}return ''})();
    const old=ED.find(x=>x.k===k);
    if(old){ if(now===old.was){ED=ED.filter(x=>x!==old);delete el.dataset.edited} else old.now=now }
    else ED.push({k,was,now,daf,ctx:ctxOf(el),t:Date.now()});
    if(now!==was)el.dataset.edited='1';
    saveED();if($('#edn'))$('#edn').textContent=ED.length;drawEd()}

  function setEdit(on){
    EDIT=on;document.body.classList.toggle('ed',on);
    const f=$('#flow');
    f.querySelectorAll('[data-ek]').forEach(el=>{
      if(on){el.setAttribute('contenteditable','true');el.setAttribute('spellcheck','false')}
      else el.removeAttribute('contenteditable')});
    let bar=$('#edbar');
    if(on&&!bar){bar=document.createElement('div');bar.className='edbar';bar.id='edbar';
      bar.innerHTML='<b>מצב עריכה</b><span>· <span id="edn">'+ED.length+'</span> תיקונים</span>'+
        '<button onclick="panel(\'ed\')">העריכות שלי</button><span class="sp"></span>'+
        '<button onclick="setEdit(false)">סיום</button>';
      document.body.appendChild(bar)}
    else if(!on&&bar)bar.remove();
    if(on)drawEd()}
  function askAdmin(){
    if(isAdmin()){setEdit(!EDIT);return}
    const a=prompt('מילת המנהל:');
    if(a===null)return;
    if(a.trim()===ADMIN_WORD){try{localStorage.setItem(AKEY,'1')}catch(e){}
      $('#edbtn').style.display='';setEdit(true)}
    else alert('המילה אינה נכונה.')}

  function drawEd(){
    const box=$('#edb');if(!box)return;
    const by={};for(const e of ED)(by[e.daf||'']=by[e.daf||'']||[]).push(e);
    let h='<div class="edsum">'+ED.length+' תיקונים ממתינים'+
      (EDSTAT.taken?' · '+EDSTAT.taken+' כבר נקלטו בוורד':'')+
      (EDSTAT.lost?' · <b style="color:#a83c2f">'+EDSTAT.lost+' תלושים</b> - הפסקה שלהם השתנתה בוורד ולכן אינם מוחלים':'')+
      '</div>';
    for(const d of Object.keys(by)){
      h+='<h3>'+esc(d||'בלא ציון דף')+'</h3>';
      by[d].forEach(e=>{const i=ED.indexOf(e);
        h+='<div class="edrow'+(e.lost?' edlost':'')+'">'+
          (e.lost?'<small>תלוש - לא הוחל</small><br>':'')+
          '<span class="was">'+esc(e.was.slice(0,90))+'</span><br>'+
          '<span class="now">'+esc(e.now.slice(0,90))+'</span><br>'+
          '<button onclick="undoEd('+i+')">ביטול</button></div>'})}
    if(!ED.length)h='<div class="edsum">אין עדיין תיקונים.</div>';
    h+='<div style="margin-top:12px;display:flex;gap:7px;flex-wrap:wrap">'+
       '<button onclick="edDownload()">הורד את כל התיקונים</button>'+
       '<button id="edcp" onclick="edCopy()">העתק ללוח</button>'+
       '<button onclick="edClear()">נקה הכל</button></div>';
    box.innerHTML=h}
  function undoEd(i){const e=ED[i];if(!e)return;
    const el=$('#flow').querySelector('[data-ek="'+e.k+'"]');
    if(el){el.textContent=e.was;delete el.dataset.edited}
    ED.splice(i,1);saveED();if($('#edn'))$('#edn').textContent=ED.length;drawEd()}
  function edClear(){if(!confirm('למחוק את כל '+ED.length+' התיקונים?'))return;
    ED=[];saveED();render(cur);drawEd()}
  function edText(){
    let t='תיקוני '+D.masechet+' - לאוקמי גירסא\n'+new Date().toLocaleString('he-IL')+'\n';
    t+=ED.length+' תיקונים\n\n';
    for(const e of ED){t+='דף '+(e.daf||'-')+(e.lost?'  [תלוש - הפסקה השתנתה בוורד]':'')+'\n';
      t+='  היה: '+e.was+'\n  יהיה: '+e.now+'\n\n'}
    t+='\n==== נתוני עיבוד (אין לערוך) ====\n';
    t+=JSON.stringify({v:1,slug:SLUG,masechet:D.masechet,when:new Date().toISOString(),edits:ED});
    return t}
  function edDownload(){const a=document.createElement('a');
    a.href=URL.createObjectURL(new Blob([edText()],{type:'text/plain;charset=utf-8'}));
    a.download='תיקוני-'+D.masechet+'.txt';a.click()}
  function edCopy(){const t=edText();const done=()=>{const b=$('#edcp');b.textContent='הועתק ✓';setTimeout(()=>b.textContent='העתק ללוח',2200)};
    if(navigator.clipboard&&navigator.clipboard.writeText)navigator.clipboard.writeText(t).then(done,fb);else fb();
    function fb(){const ta=document.createElement('textarea');ta.value=t;document.body.appendChild(ta);ta.select();
      try{document.execCommand('copy');done()}catch(e){alert('לא הצלחתי להעתיק. השתמש בכפתור ההורדה.')}ta.remove()}}

  /* הקלדה: Enter חסום כדי שלא תיווצר פסקה חדשה, והדבקה נכנסת כטקסט נקי */
  document.addEventListener('keydown',e=>{
    if(e.ctrlKey&&e.altKey&&(e.key==='e'||e.key==='E'||e.key==='ק')){askAdmin();e.preventDefault();return}
    if(EDIT&&e.key==='Enter'&&e.target.isContentEditable)e.preventDefault()});
  document.addEventListener('paste',e=>{
    if(!EDIT||!e.target.isContentEditable)return;
    e.preventDefault();
    const t=(e.clipboardData||window.clipboardData).getData('text/plain').replace(/\s+/g,' ');
    document.execCommand('insertText',false,t)});
  document.addEventListener('focusin',edFocus);
  document.addEventListener('focusout',edBlur);
  if(location.hash.indexOf('admin')>-1){try{localStorage.setItem(AKEY,'1')}catch(e){}}
  if(isAdmin())$('#edbtn').style.display='';

  /* =================== הצע תיקון ===================
     פתוח לכל לומד, בלי שרת ובלי הרשמה. ההצעה נשמרת במכשיר עוד לפני
     שנעשה בה דבר, כדי שלא תאבד אם משהו ייכשל אחר כך. היציאה היא
     העתקה ללוח או הורדה לקובץ - שתיהן עובדות תמיד.

     SUGGEST_MAIL ריק בכוונה. כתובת דואר תיכנס לכאן רק כשבעל הפרויקט
     ימסור אותה; עד אז כפתור הדואר אינו מוצג כלל, ואין להמציא כתובת. */
  const SUGGEST_MAIL='';
  const SKEY='lg-sg-'+SLUG;
  let SG=[]; try{SG=JSON.parse(localStorage.getItem(SKEY)||'[]')}catch(e){SG=[]}
  let PICK=false;
  function saveSG(){try{localStorage.setItem(SKEY,JSON.stringify(SG))}catch(e){}}
  function unitOf(el){const r=el.closest('.row');if(!r)return{daf:'',uid:''};
    let x=r,daf='';while(x){const d=x.querySelector('.dafmark');if(d){daf=d.textContent;break}x=x.previousElementSibling}
    return {daf,uid:(r.id||'').replace(/^u/,'')}}
  function suggest(){
    const s=window.getSelection();
    const t=s&&String(s).trim();
    if(t&&s.rangeCount&&$('#flow').contains(s.getRangeAt(0).commonAncestorContainer)){
      const el=(s.getRangeAt(0).commonAncestorContainer.nodeType===1
                ?s.getRangeAt(0).commonAncestorContainer
                :s.getRangeAt(0).commonAncestorContainer.parentElement);
      openSg(t,el);return}
    setPick(true)}
  function setPick(on){PICK=on;document.body.classList.toggle('pick',on);
    let h=$('#hint');
    if(on&&!h){h=document.createElement('div');h.className='hint';h.id='hint';
      h.textContent='לחץ על הקטע שברצונך להעיר עליו. Esc לביטול.';document.body.appendChild(h)}
    else if(!on&&h)h.remove()}
  $('#flow').addEventListener('click',e=>{
    if(!PICK)return;
    const el=e.target.closest('.main p, .anchor, .main.dh, .main.nose');
    if(!el)return;
    e.preventDefault();setPick(false);openSg(el.textContent.trim(),el)});
  function openSg(text,el){
    const u=unitOf(el);
    const m=document.createElement('div');m.className='modal';m.id='sgm';
    m.innerHTML='<div class="box"><h3>הצעת תיקון</h3>'+
      '<div class="ref">'+esc(D.masechet)+(u.daf?' · דף '+esc(u.daf):'')+(u.uid?' · יחידה '+esc(u.uid):'')+'</div>'+
      '<div class="sel">'+esc(text)+'</div>'+
      '<label for="sgn">מה להציע?</label><textarea id="sgn" placeholder="כתוב כאן את ההערה או את הנוסח המוצע"></textarea>'+
      '<label for="sgw">שמך (לא חובה)</label><input id="sgw" value="'+esc(localStorage.getItem('lg-sg-name')||'')+'">'+
      '<div class="btns"><button class="go" id="sgok">שמור את ההצעה</button>'+
      '<button onclick="closeSg()">ביטול</button></div></div>';
    document.body.appendChild(m);
    m.addEventListener('click',e=>{if(e.target===m)closeSg()});
    $('#sgn').focus();
    $('#sgok').onclick=()=>{
      const note=$('#sgn').value.trim();
      if(!note){alert('כתוב מה להציע.');return}
      const name=$('#sgw').value.trim();
      try{localStorage.setItem('lg-sg-name',name)}catch(e){}
      SG.push({sel:text,note,name,daf:u.daf,uid:u.uid,t:Date.now()});
      saveSG();closeSg();panel('sg');drawSg()};
  }
  function closeSg(){const m=$('#sgm');if(m)m.remove()}
  function drawSg(){const box=$('#sgb');if(!box)return;
    let h='<div class="edsum">'+SG.length+' הצעות שמורות במכשיר הזה.</div>';
    SG.forEach((g,i)=>{h+='<div class="sgrow"><small>'+esc(g.daf||'')+'</small> <q>'+esc(g.sel.slice(0,80))+'</q>'+
      '<b>'+esc(g.note)+'</b><button onclick="delSg('+i+')">מחק</button></div>'});
    if(!SG.length)h='<div class="edsum">עדיין לא הצעת דבר. סמן טקסט בדף, ולחץ "הצע תיקון".</div>';
    h+='<div style="margin-top:12px;display:flex;gap:7px;flex-wrap:wrap">'+
       '<button id="sgcp" onclick="sgCopy()">העתק ללוח</button>'+
       '<button onclick="sgDownload()">הורד לקובץ</button>'+
       (SUGGEST_MAIL?'<button onclick="sgMail()">שלח בדואר</button>':'')+
       '<button onclick="sgClear()">נקה הכל</button></div>';
    box.innerHTML=h}
  function delSg(i){SG.splice(i,1);saveSG();drawSg()}
  function sgClear(){if(!confirm('למחוק את כל '+SG.length+' ההצעות?'))return;SG=[];saveSG();drawSg()}
  function sgText(){let t='הצעות תיקון · '+D.masechet+' · לאוקמי גירסא\n'+new Date().toLocaleString('he-IL')+'\n\n';
    SG.forEach(g=>{t+='דף '+(g.daf||'-')+(g.uid?' · יחידה '+g.uid:'')+(g.name?' · '+g.name:'')+'\n';
      t+='  הקטע: '+g.sel+'\n  ההצעה: '+g.note+'\n\n'});
    return t}
  function sgDownload(){const a=document.createElement('a');
    a.href=URL.createObjectURL(new Blob([sgText()],{type:'text/plain;charset=utf-8'}));
    a.download='הצעות-'+D.masechet+'.txt';a.click()}
  function sgCopy(){const t=sgText();const done=()=>{const b=$('#sgcp');b.textContent='הועתק ✓';setTimeout(()=>b.textContent='העתק ללוח',2200)};
    if(navigator.clipboard&&navigator.clipboard.writeText)navigator.clipboard.writeText(t).then(done,fb);else fb();
    function fb(){const ta=document.createElement('textarea');ta.value=t;document.body.appendChild(ta);ta.select();
      try{document.execCommand('copy');done()}catch(e){alert('לא הצלחתי להעתיק. השתמש בכפתור ההורדה.')}ta.remove()}}
  function sgMail(){if(!SUGGEST_MAIL)return;
    location.href='mailto:'+SUGGEST_MAIL+'?subject='+encodeURIComponent('הצעות תיקון · '+D.masechet)+
      '&body='+encodeURIComponent(sgText().slice(0,1800))}
  document.addEventListener('keydown',e=>{if(e.key==='Escape'){if(PICK)setPick(false);closeSg()}});

  /* =================== "מקור": הגמרא המנוקדת ===================
     המזהה של המקטע נכתב לדף בזמן הבנייה; הטקסט עצמו יושב בקובץ נפרד
     ונטען רק בלחיצה הראשונה, כדי שדף המסכת יישאר קל בטלפון.

     שורת הייחוס בתחתית המגירה היא תנאי הרישיון (CC BY-NC), והיא לעולם
     אינה נכנסת להדפסה - שם היא מוסתרת ב-@media print. */
  let SRC=null, SRCLOAD=null, SRCMODE=localStorage.getItem('lg-srcmode')||'';
  function srcDefault(){return innerWidth<900?'full':'split'}
  function loadSrc(){
    if(SRC)return Promise.resolve(SRC);
    if(SRCLOAD)return SRCLOAD;
    SRCLOAD=fetch('sources/'+SLUG+'.json').then(r=>{if(!r.ok)throw new Error(r.status);return r.json()})
      .then(j=>{SRC=j;return j});
    return SRCLOAD}
  function barH(){const b=document.querySelector('.bar');
    document.documentElement.style.setProperty('--barH',(b?b.getBoundingClientRect().height:52)+'px')}
  function refDaf(ref){const m=/\.(\d+[ab])\.(\d+)$/.exec(ref||'');return m?[m[1],+m[2]]:null}
  function openSrc(ref){
    if(!ref)return;
    barH();
    let box=$('#srcx');
    if(!box){box=document.createElement('div');box.id='srcx';document.body.appendChild(box)}
    const mode=SRCMODE||srcDefault();
    box.className='src '+mode;
    document.body.classList.toggle('splitsrc',mode==='split');
    box.innerHTML='<div class="srchd"><b>מקור</b><span class="sp"></span>'+
      ['peek','split','full'].map(m=>'<button data-m="'+m+'" class="'+(m===mode?'on':'')+'">'+
        ({peek:'הצצה',split:'מסך מפוצל',full:'מלא'})[m]+'</button>').join('')+
      '<button onclick="closeSrc()" title="Esc">×</button></div>'+
      '<div class="srcbody"><div class="ld">טוען את הגמרא…</div></div>';
    box.querySelectorAll('[data-m]').forEach(b=>b.onclick=()=>{
      SRCMODE=b.dataset.m;localStorage.setItem('lg-srcmode',SRCMODE);openSrc(ref)});
    loadSrc().then(j=>{
      const d=refDaf(ref);if(!d)return;
      const heb=Object.keys(j.pages).find(k=>j.pages[k].daf===d[0]);
      const pg=j.pages[heb];if(!pg)return;
      const i=pg.refs.indexOf(ref);
      box.querySelector('.srchd b').textContent='מקור · דף '+heb;
      box.querySelector('.srcbody').innerHTML=
        '<div class="srcseg">'+(pg.gemara[i]||'')+'</div>'+
        '<h4>הדף כולו</h4><div class="srcall">'+
        pg.gemara.map((g,n)=>'<p class="'+(n===i?'hit':'')+'" id="sg'+n+'">'+g+'</p>').join('')+
        '</div>';
      if(!box.querySelector('.srcft')){const f=document.createElement('div');f.className='srcft';
        f.textContent=j.attribution||'';box.appendChild(f)}
      const h=box.querySelector('.hit');if(h)h.scrollIntoView({block:'center'});
    }).catch(e=>{box.querySelector('.srcbody').innerHTML=
      '<div class="ld">לא הצלחתי לטעון את הגמרא ('+esc(String(e.message||e))+').</div>'});
  }
  function closeSrc(){const b=$('#srcx');if(b)b.remove();document.body.classList.remove('splitsrc')}
  /* מקש אחד פותח מקור ליחידה שבמוקד: זו שהעכבר עליה, ואם אין - הראשונה
     הנראית בדף. */
  let HOVER=null;
  document.addEventListener('mouseover',e=>{const r=e.target.closest&&e.target.closest('.row[data-ref]');if(r)HOVER=r});
  function focusedRef(){
    if(HOVER&&document.contains(HOVER))return HOVER.dataset.ref;
    const rows=[...$('#flow').querySelectorAll('.row[data-ref]')];
    const f=$('#flow').getBoundingClientRect();
    const vis=rows.find(r=>{const b=r.getBoundingClientRect();
      return b.top<f.bottom&&b.bottom>f.top&&b.right<=f.right+2&&b.left>=f.left-2});
    return (vis||rows[0]||{dataset:{}}).dataset.ref}
  document.addEventListener('keydown',e=>{
    if(e.target.tagName==='INPUT'||e.target.tagName==='TEXTAREA'||e.target.isContentEditable)return;
    if(e.ctrlKey||e.altKey||e.metaKey)return;
    if(e.key==='מ'||e.key==='m'||e.key==='M'){const r=focusedRef();if(r){openSrc(r);e.preventDefault()}}
    if(e.key==='Escape')closeSrc()});
  addEventListener('resize',barH);

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
  <button data-fs="15" onclick="setFs(15)">קטן</button><button data-fs="18" onclick="setFs(18)">רגיל</button><button data-fs="24" onclick="setFs(24)">גדול</button>
  <button onclick="fs(2)" title="Ctrl+=">א+</button><button onclick="fs(-2)" title="Ctrl+-">א-</button>
  <button onclick="document.body.classList.toggle('hc')">ניגודיות</button><button onclick="window.print()" title="הדפסת הפרק הנוכחי בלבד">הדפס פרק</button>
  <button id="edbtn" style="display:none" onclick="askAdmin()" title="עריכה תוך כדי לימוד (Ctrl+Alt+E)">עריכה</button>
  <button onclick="suggest()" title="סמן טקסט בדף, או לחץ כאן ובחר קטע">הצע תיקון</button>
  <button onclick="panel('sg');drawSg()">ההצעות שלי</button></div>
  <div class="panel" id="search"><button class="x" onclick="panel('search')">×</button><h3>תוצאות חיפוש</h3><div id="sres"></div></div>
  <div class="panel" id="toc"><button class="x" onclick="panel('toc')">×</button><h3>תוכן העניינים - נושאי הסוגיות</h3><div id="tocb"></div></div>
  <div class="panel" id="am"><button class="x" onclick="panel('am')">×</button><h3>אמוראים ותנאים - לפי הסימון בקובץ</h3><div id="amb"></div></div>
  <div class="panel" id="qa"><button class="x" onclick="panel('qa')">×</button><h3>בקרת הקובץ - חריגות שנמצאו בהמרה</h3><div id="qab"></div></div>
  <div class="panel" id="ed"><button class="x" onclick="panel('ed')">×</button><h3>העריכות שלי</h3><div id="edb"></div></div>
  <div class="panel" id="sg"><button class="x" onclick="panel('sg')">×</button><h3>ההצעות שלי</h3><div id="sgb"></div></div>
  <div class="flow" id="flow"></div>
  <script>const DATA={J},SLUG="{slug}";</script><script>{JS}</script></body></html>'''

  open(out_path,'w',encoding='utf-8').write(page)
  return {'pages':len(pages),'toc':n_nose,'qa':qa,'empty':n_empty,'heavy':heavy}

if __name__=='__main__':
  r=build(sys.argv[1],sys.argv[2],sys.argv[3]); print(r['pages'],'pages',len(r['qa']),'qa')
