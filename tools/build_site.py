import json, html, re, collections, sys, os, io
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from styles_map import ROLE, CS, MISSING_FONTS, hatz_kind, role_of, STAR_CHARS
# סמן החץ שוורד מציב במסגרת צפה ליד שורה. אינו תוכן.
ARROW = chr(0x25c4)
# העיטור האחיד של החציצה: שלוש כוכביות, שגופן וילנא הופך בליגטורת rlig
# לעיטור האמצעי - בדיוק כפי שנראה בסוכה. כל חציצה מוצגת כך, בכל מספר
# כוכביות שנכתב בוורד (הכרעת בעל הפרויקט, 28.9.2026: אחידות). הנתונים
# עצמם אינם משתנים: זו תצוגה בלבד.
HATZ_HTML = '***'
# עד כמה חלונות כותרת שאין תחתיהם טקסט נערמים בחלון אחד. מעבר לזה זהו
# אינדקס ולא חלון (בכתובות: 106 מסגרות "ב:1", "ג:3" בסוף הקובץ), והוא
# מדווח ואינו מוצג.
STACK_MAX = 4
# עד כמה ציוני דף ריקים רצופים מצטרפים כטווח לציון שאחריהם. שרשרת ארוכה
# מזה היא אינדקס דפים שכתוב בקובץ (ביבמות: מאה ציונים רצופים), ואינה
# עמודים ריקים.
DAF_RANGE_MAX = 3
import match_sources
import font_ink
import nikud_mishna
MISSING_FONTS_REV={v:k for k,v in MISSING_FONTS.items()}

# ---------------------------------------------------------------- ו4
EDITS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         'data', 'edits')


def _slots(pages):
    """כל המקומות הניתנים לעריכה, באותו סדר ובאותם מפתחות שבדפדפן."""
    out = []
    for pi, p in enumerate(pages):
        for u in p['units']:
            def add(kk, holder, key):
                out.append({'pi': pi, 'daf': p['daf'], 'k': 'u%s%s' % (u['id'], kk),
                            'holder': holder, 'key': key})
            if u['k'] == 'u':
                if u.get('a'): add('.0', u, 'a')
                for i, l in enumerate(u['l']): add('.%d' % (i + 1), l, 1)
            elif u['k'] == 'm':
                for i, l in enumerate(u['l']): add('.%d' % (i + 1), l, 1)
            elif u['k'] in ('dh', 'nose'):
                add('.0', u, 'a')
            if u['k'] != 'u' and u.get('w'): add('.w', u, 'w')
    return out


def _bare(h):
    return html.unescape(re.sub('<[^>]+>', '', h or ''))


def _daf_key(d):
    V = {'א':1,'ב':2,'ג':3,'ד':4,'ה':5,'ו':6,'ז':7,'ח':8,'ט':9,'י':10,'כ':20,
         'ל':30,'מ':40,'נ':50,'ס':60,'ע':70,'פ':80,'צ':90,'ק':100,'ר':200,'ש':300,'ת':400}
    if not d: return None
    t = d.strip(); am = 1 if t.endswith(':') else 0
    n = sum(V.get(c, 0) for c in re.sub(r'[.:"\'\u05f3\u05f4]', '', t))
    return n * 2 + am if n else None


def _find_run(pages, texts, daf):
    """רצף פסקאות סמוכות ביחידה אחת שנוסחן הוא texts. דורש ייחוד, ובריבוי
    מופעים מצומצם לדף אחד לכל צד. לא נמצא יחיד - מוחזר None, ולעולם לא
    ניחוש: פיצול או איחוי שנופל על פסקה זרה הורס שתי פסקאות בבת אחת."""
    hits = []
    for p in pages:
        for u in p['units']:
            if u['k'] not in ('u', 'm'):
                continue
            L = u['l']
            for i in range(len(L) - len(texts) + 1):
                if all(_bare(L[i + j][1]) == texts[j] for j in range(len(texts))):
                    hits.append((u, i, p['daf']))
    if len(hits) == 1:
        return hits[0]
    if len(hits) > 1 and daf:
        k0 = _daf_key(daf)
        near = [h for h in hits
                if k0 is not None and _daf_key(h[2]) is not None
                and abs(_daf_key(h[2]) - k0) <= 1]
        if len(near) == 1:
            return near[0]
    return None


def _apply_site_edits(pages, slug, qa):
    """מחיל על הנתונים את התיקונים שנעשו באתר, ומוחק מן הקובץ את מה
    שכבר הגיע מן הוורד. דילוג שקט אסור: כל תיקון שלא אותר נאמר בבקרה."""
    path = os.path.join(EDITS_DIR, slug + '.json')
    if not os.path.exists(path):
        return None
    try:
        doc = json.load(io.open(path, encoding='utf-8'))
    except Exception as e:
        qa.append(('קובץ התיקונים', 'לא ניתן לקרוא את קובץ התיקונים של האתר: %s' % e))
        return None
    edits = doc.get('edits') or []
    if not edits:
        return {'n': 0, 'taken': 0, 'lost': 0, 'done': 0}
    slots = _slots(pages)
    by_key = {}
    for s in slots:
        s['t'] = _bare(s['holder'][s['key']] if isinstance(s['key'], int)
                       else s['holder'].get(s['key'], ''))
        by_key[s['k']] = s
    keep, done, taken, lost = [], 0, 0, []

    def reslot():
        del slots[:]
        slots.extend(_slots(pages))
        by_key.clear()
        for s in slots:
            s['t'] = _bare(s['holder'][s['key']] if isinstance(s['key'], int)
                           else s['holder'].get(s['key'], ''))
            by_key[s['k']] = s

    for e in edits:
        # --- שינוי מבנה: פיצול פסקה או איחוי שתיים ---
        if e.get('op') == 'struct':
            texts = e.get('texts') or []
            res = e.get('res') or []
            hit = _find_run(pages, texts, e.get('daf'))
            if hit is not None:
                u, i, _ = hit
                u['l'][i:i + len(texts)] = [list(x) for x in res]
                done += 1
                keep.append(e)
                reslot()
            elif _find_run(pages, e.get('resT') or [], e.get('daf')) is not None:
                taken += 1                  # כבר בקובץ הוורד
            else:
                lost.append(e)
                keep.append(e)
            continue
        was, now = e.get('was', ''), e.get('now', '')
        s = by_key.get(e.get('k'))
        if s is None or (s['t'] != was and s['t'] != now):
            k0 = _daf_key(e.get('daf'))
            win = [x for x in slots
                   if k0 is None or _daf_key(x['daf']) is None
                   or abs(_daf_key(x['daf']) - k0) <= 1]
            s = None
            for want in (was, now):
                hits = [x for x in win if x['t'] == want]
                if len(hits) == 1:
                    s = hits[0]; break
        if s is None:
            lost.append(e); keep.append(e); continue
        if s['t'] == now and e.get('ps') is None:
            taken += 1                      # כבר הגיע מן הוורד - יוצא מן הקובץ
            continue
        if s['t'] != was:
            lost.append(e); keep.append(e); continue
        h = e.get('nowH')
        if h is None: h = html.escape(now)
        if isinstance(s['key'], int): s['holder'][s['key']] = h
        else: s['holder'][s['key']] = h
        ps = e.get('ps')
        if ps is not None and isinstance(s['key'], int):
            keepsp = ' '.join(c for c in (s['holder'][0] or '').split()
                              if c[:1] in 'ba' and c[1:].isdigit())
            s['holder'][0] = (ps + ' ' + keepsp).strip()
        done += 1
        e['k'] = s['k']
        keep.append(e)
    if lost:
        qa.append(('תיקון תלוש',
                   '%d תיקונים שנעשו באתר לא אותרו בקובץ הוורד ואינם מוחלים. '
                   'הפסקה שלהם השתנתה מאז. הראשון: %r'
                   % (len(lost), (lost[0].get('was')
                                  or ' | '.join(lost[0].get('texts') or []))[:60])))
    if taken:
        qa.append(('תיקון שנקלט',
                   '%d תיקונים כבר נמצאים בקובץ הוורד והוסרו מקובץ התיקונים' % taken))
    if len(keep) != len(edits):
        doc['edits'] = keep
        io.open(path, 'w', encoding='utf-8', newline='\n').write(
            json.dumps(doc, ensure_ascii=False, indent=1))
        print('קובץ התיקונים של %s: %d נשארו, %d נקלטו בוורד' % (slug, len(keep), taken))
    print('תיקוני האתר ב%s: %d הוחלו, %d נקלטו כבר, %d תלושים'
          % (slug, done, taken, len(lost)))
    return {'n': len(edits), 'taken': taken, 'lost': len(lost), 'done': done}


def build(json_path, out_path, masechet, hagaha=False, sources=None, spacing=None):
  blocks = json.load(open(json_path, encoding='utf-8'))
  spacing = spacing or {}

  # ---------- ג1: סולם הכותרות נמדד לעין, לא בנקודות נקובות ----------
  # וילנא מודגש גדול לעין בהרבה מפרנקריהל באותו גודל נקוב: גובה תיבת
  # הדיו שלו הוא 1.017 של ה-em מול 0.933. לכן גודל האות של כל כותרת
  # נגזר כאן מגובה האותיות שנמדד בקובץ הגופן עצמו, וכך היחס שהלומד
  # רואה הוא היחס שנקבע: נושא = גוף כפול 10/9, משנה = כגוף, ודיבור
  # המתחיל של משנה = משנה כפול 8/9. סוכן סריקת התצוגה מאמת את אותם
  # מספרים בדפדפן, ב-canvas measureText.
  _fd = os.path.join(os.path.dirname(os.path.abspath(out_path)), 'fonts')
  def _ink(name, dflt):
      pth = os.path.join(_fd, name)
      try: return font_ink.ink_per_em(pth) if os.path.exists(pth) else dflt
      except Exception: return dflt
  I_body = _ink('frank.ttf', 0.9331)       # גוף: FrankRuehl
  I_fb   = _ink('frank-b.ttf', 1.1960)     # מודגש: PFT_Frank Bold
  I_v700 = _ink('vilna-b.otf', 1.0173)     # משנה ונושא: BA Vilna Bold
  I_v900 = _ink('vilna-xb.otf', 1.0173)    # דיבור המתחיל: BA Vilna Extra-Bold
  K_MISHNA = I_body / I_v700
  K_NOSE   = I_body / I_v700 * 10.0 / 9.0
  K_DH     = I_body / I_v900 * 8.0 / 9.0
  # ההדגשה שהדפדפן מייצר מפרנקריהל קיצונית ומכוערת, ולכן ההדגשה היא
  # גופן ממש: PFT_Frank Bold. הוא גדול בהרבה ליחידת em (1.196 מול
  # 0.933), ו-size-adjust מקטין אותו בדיוק כך שגובה האותיות יהיה כשל
  # הגוף. בלי זה כל מילה מודגשת היתה קופצת בגודל. המספר נמדד ואינו
  # נבחר: זהו בדיוק ה"שתיים פחות" שבעל הפרויקט ראה בעין (7 מול 9).
  K_BOLD   = I_body / I_fb

  # ---------- ג3: רשת השורות ----------
  # כל מרווח אנכי בדף נגזר מ-w:spacing של הסגנון בוורד, ולא ממספר
  # שנבחר לעין, והוא מעוגל לחצאי שורה כדי שהטקסט יחזור לרשת.
  _bl = ((spacing.get('Normal') or {}).get('line')) or 11.0
  def _half(v):
      return max(0, min(4, int(round(((v or 0.0) / _bl) * 2))))
  def sp_cls(style):
      sp = spacing.get(style) or {}
      return 'b%d a%d' % (_half(sp.get('before')), _half(sp.get('after')))
  def line_ratio(role, dflt=1.0):
      """מרווח השורה של תפקיד, ביחידות שורת הגוף."""
      best = None
      for name, sp in spacing.items():
          if ROLE.get(name) == role and sp.get('line'):
              best = sp['line'] if best is None else max(best, sp['line'])
      return round(best / _bl, 4) if best else dflt

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

  def disp(t):
      """הטקסט כפי שהוא מוצג. סמן החץ הוא סמן פריסה של וורד - מסגרת צפה
      שמצביעה על שורה - ואין לו טעם בדף; וטאב ממילא מתמוטט לרווח בהטמעת
      HTML. הנתונים עצמם אינם משתנים."""
      return re.sub(r'[ ]{2,}', ' ', t.replace(ARROW, ' ').replace('	', ' '))

  def runs_html(runs):
      out=[]
      for r in fuse_stars(runs):
          t=html.escape(disp(r['t'])); c=CS.get(r['cs'])
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
  # ---------- א: החציצה אחידה בכל המסכתות ----------
  # פסקה שכל תוכנה כוכביות היא חציצה, יהא סגנונה אשר יהא, ומוצגת בעיטור
  # של סוכה. זו אינה משימה של בעל הפרויקט ולכן אינה משימה בבקרה: היא
  # מידע בלבד, באפור. המונים נמדדים כאן ונכתבים גם לדוח.
  hz_all=[(b,hatz_kind(b['text'])) for b in blocks]
  hz_all=[(b,k) for b,k in hz_all if k]
  hz_restyled=[b for b,k in hz_all if k=='star' and ROLE.get(b['style'],'body')!='hatz']
  hz_orn=[b for b,k in hz_all if k=='orn']
  hz_counts=collections.Counter(sum(1 for ch in b['text'] if ch in STAR_CHARS) for b,k in hz_all if k=='star')
  hz_inline=sum(1 for b in blocks if not hatz_kind(b['text']) and any(ch in STAR_CHARS for ch in b['text']))
  hz_stat={'total':len(hz_all),'restyled':len(hz_restyled),'orn':len(hz_orn),
           'byCount':{str(k):v for k,v in sorted(hz_counts.items())},'inline':hz_inline}
  if hz_restyled:
      qa.append(('טופל בתצוגה: כוכביות שסגנונן אינו חציצה',
                 '%d פסקאות כוכביות יושבות בוורד בסגנון אחר (%s) ומוצגות בעיטור החציצה. הוורד לא נגע'
                 % (len(hz_restyled), ', '.join('%s %d'%(s,n) for s,n in
                    collections.Counter(b['style'] for b in hz_restyled).most_common(4)))))
  odd=[(k,v) for k,v in sorted(hz_counts.items()) if k!=3]
  if odd:
      qa.append(('טופל בתצוגה: מספר כוכביות שונה משלוש',
                 'בוורד: '+', '.join('%d פסקאות של %d כוכביות'%(v,k) for k,v in odd)+
                 '. כולן מוצגות בעיטור האחיד של סוכה'))
  if hz_orn:
      qa.append(('טופל בתצוגה: עיטור בגופן שאינו באתר',
                 '%d פסקאות חציצה כתובות בסימני העיטור של גופן BA שאינו באתר, ומוצגות בעיטור האחיד'
                 % len(hz_orn)))
  if hz_inline:
      qa.append(('כוכבית בתוך שורת טקסט',
                 '%d פסקאות שיש בהן כוכבית בתוך הטקסט. אינן חציצה ולא נגעו - לבקרה בלבד' % hz_inline))
  empty_anchor=[b for b in blocks if b['style']=='חלון 3' and not b['text'].strip()]
  if empty_anchor: qa.append(('חלון ריק',f'{len(empty_anchor)} חלונות ריקים'))

  # ---------- pages ----------
  pages=[]  # {daf, perek, perekName, units:[...]}
  cur=None; perek=''; perekName=''; unit=None
  order=[]
  toc=[]
  # ב2 - סמן החץ שבחלון הצד הוא סמן פריסה של וורד, לא הבחנה תוכנית.
  # נמדד בשלושה קבצים (סוכה, ביצה, בבא בתרא): הפסקה שאחרי חלון שכולו חץ
  # היא משנה ב-69 מקרים, גוף ב-52 ונושא ב-2 - כלומר אין לו מובן אחיד.
  # לפיכך חלון שכולו חץ אינו פותח יחידה (בלעדי זה נפתחו עשרות שורות
  # ריקות בדף) ואף אינו מדליק סימון תצוגה. הנתונים נשארים כמות שהם,
  # והמונה מוצג בבקרה כדי שההשמטה לא תהיה שקטה.
  n_hal=0
  pend=None      # חלון הממתין למה שיבוא אחריו: (html, id, כמה חלונות נערמו)
  n_stack=0      # חלון שאין תחתיו טקסט ונערם מעל החלון הבא (ב2)
  n_stack_drop=0 # חלון שנערם מעבר לתקרה ואינו מוצג
  n_tail_win=0   # חלון בסוף המסכת שאין אחריו דבר
  n_hatz_dup=0   # חציצה מיד אחרי חציצה (עיטור ואחריו כוכביות) - מוצגת פעם אחת
  def take_pend():
      """החלון הממתין נמסר ליחידה. מונה כמה חלונות נערמו בו."""
      nonlocal pend, n_stack
      p=pend; pend=None
      if p[2]>1: n_stack+=p[2]-1
      return p
  # ב: פסקת חציצה שיושבת בתוך משנה - בין פסקת משנה לפסקת משנה - נשארת
  # בתוך יחידת המשנה, על הרקע שלה, באותו עיטור.
  nb=[i for i,b in enumerate(blocks)]
  def next_role(i):
      """תפקיד הפסקה הבאה שיש בה טקסט, מדלג על ריהוט וציוני דף."""
      for j in range(i+1,len(blocks)):
          r=role_of(blocks[j])
          if r in ('skip','daf'): continue
          if not blocks[j]['text'].strip(): continue
          return r
      return None
  def toc_text(raw):
      """כותרת לתוכן העניינים, מן הטקסט הגולמי ולפני כל בריחה.
      כך אין ישויות HTML, ואין חץ ואין טאבים."""
      return re.sub(r'\s+',' ',raw.replace('◄',' ').replace('\t',' ')).strip()
  def add_toc(kind,b):
      t=toc_text(b['text'])
      if t: toc.append([len(pages)-1,b['i'],t,kind])
  n_skip=collections.Counter()
  for bi,b in enumerate(blocks):
      r=role_of(b); h=runs_html(b['runs']); t=b['text'].strip()
      # א: חציצה - העיטור האחיד, בלי תלות במספר הכוכביות שבוורד
      if r=='hatz': h=HATZ_HTML
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
          # ב2: חלון שאין תחתיו טקסט אינו נעצר בציון הדף. הוא ממשיך
          # להמתין ליחידה הבאה, שתקבל אותו במסילתה יחד עם ציון הדף.
          cur={'daf':t,'perek':perek,'perekName':perekName,'units':[]}; pages.append(cur); unit=None
          continue
      if cur is None: continue
      cur['perek']=perek; cur['perekName']=perekName
      # חלון הכותרת הוא מסגרת צפה בוורד, והוא מצביע על מה שאחריו. עד כאן
      # הוא פתח מיד יחידה משלו, וכשאחריו באה כותרת "נושא" נשארה בדף שורה
      # שכל תוכנה חלון - שורה לבנה לכל דבר. מעתה הוא ממתין: אם אחריו גוף,
      # הוא פותח את היחידה כמקודם; ואם אחריו כותרת, הוא יושב במסילה שלה.
      # ב2: ואם אחריו חלון נוסף - הוא נערם מעליו, באותה מסילה. לעולם אין
      # יחידה ריקה בדף. ערימה מעבר לתקרה היא אינדקס ולא חלון, ומדווחת.
      if r=='anchor':
          if t and set(t) <= {ARROW}:
              n_hal+=1; continue            # סמן פריסה של וורד, אינו יחידה
          if pend is not None:
              if pend[2]>=STACK_MAX:
                  n_stack_drop+=1
                  parts=pend[0].split('<br>')[1:]
                  pend=('<br>'.join(parts+[h]),b['i'],pend[2])
              else:
                  pend=(pend[0]+'<br>'+h,b['i'],pend[2]+1)
          else:
              pend=(h,b['i'],1)
          unit=None
      elif r.startswith('body'):
          if pend is not None:
              w=take_pend(); unit={'k':'u','a':w[0],'l':[],'id':w[1]}; cur['units'].append(unit)
          elif unit is None or unit['k']!='u':
              unit={'k':'u','a':'','l':[],'id':b['i']}; cur['units'].append(unit)
          unit['l'].append([((r[5:] if len(r)>4 else '')+' '+sp_cls(b['style'])).strip(),h])
      elif r=='mishna':
          if cur['units'] and cur['units'][-1]['k']=='m' and pend is None:
              cur['units'][-1]['l'].append([sp_cls(b['style']),h])
          else:
              u={'k':'m','a':'','l':[[sp_cls(b['style']),h]],'id':b['i']}
              if pend is not None: u['w']=take_pend()[0]
              cur['units'].append(u); add_toc('m',b)
          unit=None
      elif r=='hatz' and pend is None and cur['units'] and cur['units'][-1]['k']=='m' \
           and unit is None and next_role(bi)=='mishna':
          # א5: חציצה בתוך משנה - אותו עיטור, על רקע המשנה. פעם אחת.
          if cur['units'][-1]['l'] and cur['units'][-1]['l'][-1][0]=='hatz': n_hatz_dup+=1
          else: cur['units'][-1]['l'].append(['hatz',HATZ_HTML])
      elif r=='hatz' and pend is None and cur['units'] and cur['units'][-1]['k']=='hatz':
          # א3: עיטור ואחריו כוכביות (בקידושין: 212 זוגות) - חציצה אחת
          n_hatz_dup+=1
      elif r in ('dh','nose','hatz','perek-num','perek-name','perek-range','perek-start','hadran'):
          u={'k':r,'a':h,'l':[],'id':b['i'],'s':sp_cls(b['style'])}
          if pend is not None: u['w']=take_pend()[0]
          cur['units'].append(u); unit=None
          if r in ('dh','nose'): add_toc(r,b)
  if pend is not None:
      # ב4: חלון בסוף המסכת שאין אחריו דבר - אין למה לצרפו. אינו מוצג
      # כריק, ונרשם.
      n_tail_win+=pend[2]; pend=None

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
  # ---------- ב1: ציון דף שאין אחריו טקסט ----------
  # אינו יוצר שורה ריקה: הוא מצטרף לציון שאחריו במסילה, כטווח עם מקף
  # רגיל ("יד:-טו."). ציון הדף האמיתי של העמוד נשאר בנתונים (daf), כדי
  # שהעיגון, ההצמדה והניקוד ימשיכו לעבוד; רק התווית (label) היא הטווח.
  # ציון בסוף המסכת שאין אחריו דבר - אין למה לצרפו, ואינו מוצג.
  n_range=0; n_tail_daf=0; n_index_daf=0; n_dup_daf=0; carry=[]; kept=[]; newpi={}
  for oldpi,p in enumerate(pages):
      if not p['units']:
          carry.append(p['daf']); newpi[oldpi]=len(kept); continue
      if carry:
          # ציון כפול (אותו דף פעמיים, הראשון ריק) אינו טווח
          carry2=[d for d in carry if d!=p['daf']]
          n_dup_daf+=len(carry)-len(carry2)
          if len(carry2)>DAF_RANGE_MAX:
              # שרשרת ארוכה של ציונים ריקים היא אינדקס דפים שבקובץ, לא
              # עמודים ריקים (ביבמות: מאה ציונים רצופים). אינה מוצגת.
              n_index_daf+=len(carry2)
          elif carry2:
              p['label']=carry2[0]+'-'+p['daf']; p['dafs']=carry2+[p['daf']]
              n_range+=len(carry2)
          carry=[]
      newpi[oldpi]=len(kept); kept.append(p)
  n_tail_daf=len(carry)
  pages=kept
  # תוכן העניינים נרשם לפי מקום העמוד ברשימה המקורית
  toc=[[min(newpi.get(e[0],0),max(0,len(pages)-1))]+e[1:] for e in toc]
  if n_range:
      qa.append(('טופל בתצוגה: ציון דף שאין תחתיו טקסט',
                 f'{n_range} ציוני דף אין אחריהם טקסט עד הציון הבא, והם מוצגים כטווח '
                 'יחד עם הציון שאחריהם. הוורד לא נגע'))
  if n_tail_daf:
      qa.append(('לא ניתן לצרף',
                 f'{n_tail_daf} ציוני דף בסוף המסכת אין אחריהם טקסט ואין ציון לצרפם אליו. אינם מוצגים'))
  if n_index_daf:
      qa.append(('לא ניתן לצרף',
                 f'{n_index_daf} ציוני דף ריקים ברצף של יותר מ-{DAF_RANGE_MAX} - זהו אינדקס דפים שבקובץ ולא עמודים - ואינם מוצגים'))
  if n_dup_daf:
      qa.append(('טופל בתצוגה: ציון דף כפול',
                 f'{n_dup_daf} ציוני דף ריקים כפולים לציון שאחריהם, ואינם מוצגים פעמיים'))
  if n_hatz_dup:
      qa.append(('טופל בתצוגה: חציצה כפולה',
                 f'{n_hatz_dup} פסקאות חציצה באות מיד אחרי חציצה אחרת (עיטור וכוכביות זה אחר זה) ומוצגות פעם אחת'))
  if n_stack:
      qa.append(('טופל בתצוגה: חלון שאין תחתיו טקסט',
                 f'{n_stack} חלונות כותרת אין אחריהם טקסט עד החלון הבא, והם מוצגים מעל '
                 'החלון הבא באותה מסילה. הוורד לא נגע'))
  if n_stack_drop:
      qa.append(('לא ניתן לצרף',
                 f'{n_stack_drop} חלונות נערמו מעבר ל-{STACK_MAX} זה על זה - זהו אינדקס ולא חלון - ואינם מוצגים'))
  if n_tail_win:
      qa.append(('לא ניתן לצרף',
                 f'{n_tail_win} חלונות כותרת בסוף המסכת אין אחריהם דבר. אינם מוצגים'))
  if n_hal:
      qa.append(('סמני חץ של וורד',
                 f'{n_hal} סמני חץ הושמטו מן התצוגה. בוורד זו מסגרת צפה '
                 'שמצביעה על שורה, ולא הבחנה בתוכן'))
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
  nk=None
  if sources:
      st=match_sources.attach(pages,sources)
      srcmeta={'slug':os.path.basename(out_path)[:-5],
               'attribution':sources.get('attribution',''),
               'matched':st['matched'],'eligible':st['eligible']}
      qa.append(('מקור מן הגמרא',
                 '%d יחידות מתוך %d הוצמדו למקטע בגמרא; %d לא עברו את הסף ואין להן כפתור "מקור"'
                 % (st['matched'],st['eligible'],st['low'])))
  # ---------- ו3: מפת הסגנונות לסרגל העריכה הצף ----------
  # שמות הסגנונות שונים מקובץ לקובץ. לכל תפקיד נבחר השם השכיח ביותר
  # באותו תפקיד בקובץ הזה עצמו, כדי שכתיבה לוורד תשתמש בסגנון שכבר
  # קיים בו ולא תמציא חדש. סגנון שאין לו שם בקובץ הזה אינו מוצע כלל:
  # עדיף שלא יופיע מלהציע דבר שלא ניתן לכתוב אותו חזרה.
  CSLAB=[('am','אמוראים'),('ps','פסוק'),('tn','משנה'),('ns','נושא'),
         ('kt','כותרת בשורה'),('hs','רקע והסבר'),('ot','אות פותחת')]
  PSLAB=[('','גוף'),('hr','רקע והסבר'),('in','פיסקת תשובה'),
         ('sp','רווח לפני'),('nk','נקודה')]
  cs_cnt=collections.defaultdict(collections.Counter)
  ps_cnt=collections.defaultdict(collections.Counter)
  for b in blocks:
      r=ROLE.get(b['style'],'body')
      if r.startswith('body'):
          ps_cnt[r[5:] if len(r)>4 else ''][b['style']]+=1
      for rn in b['runs']:
          c=CS.get(rn['cs'])
          if c: cs_cnt[c][rn['cs']]+=1
  def top(cnt):
      return cnt.most_common(1)[0][0] if cnt else ''
  sty={'c':[[c,lab,top(cs_cnt[c])] for c,lab in CSLAB if cs_cnt[c]]+
           [['b','מודגש','']],          # הדגשה ישירה, אינה סגנון בוורד
       'p':[[c,lab,top(ps_cnt[c])] for c,lab in PSLAB if ps_cnt[c]]}
  absent=[lab for c,lab in CSLAB if not cs_cnt[c]]
  if absent:
      qa.append(('סגנון תו שאינו בקובץ',
                 'אינם מוצעים בסרגל העריכה מפני שאין להם סגנון בקובץ הזה: '
                 +', '.join(absent)))

  # ---------- ו4: התיקונים שנעשו באתר, מוחלים כאן ולא בדפדפן ----------
  # התיקון נכנס אל הנתונים עצמם, ולכן הוא נראה לכל לומד, נכנס להדפסה
  # ולחיפוש, ואינו תלוי במכשיר שבו נעשה. העיגון: מפתח היחידה תחילה,
  # ואם זז - התאמה אחת ויחידה של הנוסח שהיה, בטווח דף אחד לכל צד.
  # תיקון שאיבד את עוגנו אינו מוחל בשקט: הוא נשאר בקובץ ונאמר בבקרה.
  ed_stat=_apply_site_edits(pages,os.path.basename(out_path)[:-5],qa)

  # ז - הניקוד מועתק מן הגמרא המנוקדת לפי מקום, ויושב בשכבה נפרדת
  # (u['lv']). נוסח הוורד נשאר כשהיה: הוא שמשמש לחיפוש, לתוכן
  # העניינים ולעריכה, ואליו חוזרים במצב עריכה.
  # הוא נבנה **אחרי** החלת תיקוני האתר, ולא לפניה: פסקת משנה שתוקנה
  # באתר היתה נשארת עם שכבת ניקוד ישנה, והלומד היה רואה את הנוסח
  # הישן כל עוד הניקוד דלוק.
  if sources:
      nk=nikud_mishna.apply(pages,sources)
      if nk['mishnayot']:
          qa.append(('ניקוד המשניות',
                     '%d משניות מתוך %d נוקדו מן הגמרא המנוקדת (%.0f אחוזים), '
                     'ובהן %d מילים מתוך %d (%.0f אחוזים). מילה שכתיבה שונה '
                     'מן המקור נשארת בלי ניקוד במתכוון'
                     % (nk['voc'],nk['mishnayot'],100.0*nk['voc']/nk['mishnayot'],
                        nk['wdone'],nk['words'],100.0*nk['wdone']/max(1,nk['words']))))

  data={'masechet':masechet,'pages':pages,'toc':toc,'sty':sty,'ed':ed_stat,'am':amlist,'qa':qa,'nPsk':len(psk),'nAm':sum(am.values()),'src':srcmeta,'nk':nk}
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
  /* --lhpx הוא גובה שורת הגוף במידה מוחלטת. פריטי המסילה זקוקים לו:
     line-height שהוא מספר מתייחס לגודל האות של האלמנט עצמו, ולכן ציון דף
     של 1.3em היה מקבל שורה גבוהה ב-30 אחוזים ומגביה את כל היחידה. */
  .flow{--lhpx:calc(var(--fs) * 1.06);
        font-size:var(--fs);line-height:1.06;flex:1 1 auto;min-height:0;background:var(--paper);
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
  /* ב1 - המסילה בשני נתיבים, זה לצד זה ולא זה על זה.
     עד כאן היה ציון הדף display:block, ולכן חלון הכותרת ירד לשורה שנייה
     של המסילה. ביחידה בת שורה אחת נפערה שורה לבנה, והחלון עמד ליד חלל
     או ליד היחידה הבאה - לא ליד השורה שהוא מסמן.

     מעתה המסילה היא גריד בן שני נתיבים, בכיוון הקריאה: החיצוני (הימני,
     בקצה העמוד) לציון הדף, והפנימי (הצמוד לטקסט) לחלון או לתווית "משנה".
     כך יושבים שני סמני צד של אותה שורה זה לצד זה, כמו בוורד.

     align-items:baseline בשני המקומות מיישר את שניהם לקו הבסיס של השורה
     הראשונה של הטקסט. line-height:0 לפריטי המסילה הוא הדרך היחידה שבה
     גובה המסילה לעולם אינו עולה על גובה הטקסט: תיבת השורה שלהם אפס,
     האותיות נראות (אין overflow:hidden), וקו הבסיס נשמר. */
  .row{display:grid;grid-template-columns:var(--rail) var(--measure);
       align-items:baseline;break-inside:avoid-column}
  .rail{display:grid;grid-template-columns:var(--dafw,2.9em) minmax(0,1fr);
        align-items:baseline;column-gap:.14em;padding-left:.36em}
  .rail>*{line-height:0}
  .win.w2{line-height:var(--lhpx)}
  /* יחידה שאין לה ציון דף: נתיב הדף מתאפס, והחלון מקבל את כל המסילה */
  .rail:not(:has(.dafmark)){grid-template-columns:0 minmax(0,1fr)}
  /* דף שאין בו יחידות: הטקסט ריק, והמסילה אינה תופסת גובה. בלי המינימום
     הזה היה ציון הדף נופל על השורה הבאה. */
  .row>.main:empty{min-height:var(--lhpx)}
  .main{text-align:justify;text-align-last:right}
  .main p{margin:0} .main p.nk{font-size:1.09em} .main p.hr{font-size:.82em;color:#4a4137}
  /* פסקה מוזחת (פיסקת תשובה, וסעיפי רשימה): הזחה תלויה, כמו בוורד */
  .main p.in{padding-right:.9em;text-indent:-.9em}
  .dafmark{grid-column:1;justify-self:center;font-family:'VilnaG','Vilna',serif;
           font-size:1.3em;color:var(--red);margin:0}
  /* אין עוד overflow:hidden ואין ellipsis: חלון שנחתך בשקט הוא כישלון
     שקט. חלון שאינו נכנס מטופל במדידה (fitAnchors), ובסוף מוצג קטן יותר
     ולא נחתך. */
  /* הנתיב הפנימי: חלון הכותרת ותווית "משנה" יחד, זה לצד זה */
  .win{grid-column:2;justify-self:end;white-space:nowrap;text-align:left}
  .anchor{font-family:'Vilna',serif;font-weight:900;font-size:.9em;color:#5a5044}
  /* חלון שנמדד ואינו נכנס בשורה אחת, וליחידה יש שתי שורות טקסט לפחות */
  .win.w2{white-space:normal;line-height:var(--lhpx);text-align:left}
  .mlabel{font-size:.55em;color:#8a7d66;margin-right:.3em}
  /* ג: גודל האות של כל כותרת נגזר מגובה האותיות שנמדד בקובץ הגופן
     (--k-*, נכתבים בסוף גיליון הסגנונות), ולא מנקודות נקובות. מרווח
     השורה של כולן הוא רשת הגוף, וכל מרווח אנכי בא ממחלקות b/a שנגזרו
     מ-w:spacing שבוורד. בלי זה נפערו חללים שנראו כשורות לבנות. */
  .main.mishna{background:#eeeae1;padding:0 .15em;margin:0;font-family:'Vilna',serif;font-weight:700;
          font-size:calc(var(--k-mishna) * 1em);border-right:.1em solid var(--gold)}
  /* ‏.dh ו-.nose יושבים גם על השורה וגם על הטקסט שבתוכה. כלל שאינו
     מוגבל ל-.main היה מוכפל פעמיים, וגודל הכותרת יצא בריבוע המקדם -
     שורש נוסף לכותרות הגדולות. סוכן סריקת התצוגה מדד זאת. */
  .main.dh{text-align:center;text-align-last:center;font-family:'Vilna',serif;font-weight:900;
      font-size:calc(var(--k-dh) * 1em);margin:0}
  .main.nose{text-align:center;text-align-last:center;font-family:'Vilna',serif;font-weight:700;
        font-size:calc(var(--k-nose) * 1em);margin:0;color:var(--ink)}
  /* ב. הכוכביות אינן כוכביות: בגופני וילנא יש שרשרת ליגטורות ב-rlig,
     וכל מספר כוכביות נותן עיטור אחר. letter-spacing ביטל אותה, ולכן
     הוא חוזר ל-normal והליגטורות נדלקות במפורש. */
  .main.hatz,.main.mishna p.hatz{text-align:center;text-align-last:center;font-family:'Vilna',serif;font-weight:900;
        font-size:1.1em;letter-spacing:normal;word-spacing:normal;color:#8a7d66;margin:0;
        font-variant-ligatures:common-ligatures;font-feature-settings:"rlig" 1,"liga" 1}
  /* א8: חציצה אינה נשארת לבדה בתחתית טור. בעמוד המודפס מנוע הגיליונות
     מצמיד אותה לפסקה שאחריה. */
  .row.hatz{break-after:avoid-column}
  /* ב2: חלונות שנערמו זה מעל זה במסילה אחת. line-height:0 של המסילה
     היה מניח אותם זה על זה, ולכן ערימה מקבלת את רשת הגוף. */
  .win.stk{line-height:var(--lhpx)}
  /* ב1: ציון דף שהוא טווח ("יד:-טו.") - קטן יותר, כדי שלא ירחיב את נתיב
     הדף של כל המסכת. רוחבו נמדד ומוגדר לשורה שלו בלבד. */
  .dafmark.rng{font-size:.95em;letter-spacing:-.02em}
  .perek-num .main{font-family:'Franknatan','Vilna',serif;color:var(--red);font-size:1.45em;line-height:1.1}
  .perek-name .main{font-family:'Franknatan','Vilna',serif;color:#8a7d66;font-size:1.09em}
  .perek-range .main{color:var(--red);font-size:.73em}
  .perek-start .main{text-align:center;text-align-last:center;font-family:'Vilna',serif;font-weight:700;font-size:1.09em}
  .hadran .main{text-align:center;text-align-last:center;font-size:1.09em;margin:0}
  /* מרווחי וורד, בחצאי שורה של רשת הגוף. b=לפני, a=אחרי.
     הכללים נכתבים כצאצא של .row כדי שמשקלם יגבר על '.main p{margin:0}'
     ועל כללי הכותרות. בלי זה הם לא חלו כלל, והמרווח שבוורד נעלם. */
  .row .b0{margin-top:0}.row .b1{margin-top:calc(var(--lhpx) * .5)}
  .row .b2{margin-top:var(--lhpx)}.row .b3{margin-top:calc(var(--lhpx) * 1.5)}
  .row .b4{margin-top:calc(var(--lhpx) * 2)}
  .row .a0{margin-bottom:0}.row .a1{margin-bottom:calc(var(--lhpx) * .5)}
  .row .a2{margin-bottom:var(--lhpx)}.row .a3{margin-bottom:calc(var(--lhpx) * 1.5)}
  .row .a4{margin-bottom:calc(var(--lhpx) * 2)}
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
  /* ב3: מקרה שטופל בתצוגה הוא מידע בלבד, באפור - לא משימה */
  .res.qgrey{color:#8a7d66} .res.qgrey b{color:#8a7d66;font-weight:400}
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
  .edbar .edpub{font-size:13px;color:#cfe0c8}
  .edflash{position:fixed;z-index:14;left:50%;transform:translateX(-50%);bottom:64px;display:none;
     background:#a83c2f;color:#fff;border-radius:6px;padding:7px 16px;font-size:15px;
     box-shadow:0 3px 14px rgba(0,0,0,.3)}
  .edbar .edpub.bad{color:#ffd9d2;font-weight:700}
  /* הסרגל הצף של הסגנונות. הוא נפתח מעל הבחירה, ולעולם אינו מכסה
     את הטקסט הנערך: אם אין מקום מעליו הוא יורד מתחתיו. */
  .stybar{position:fixed;z-index:12;display:none;align-items:center;gap:4px;flex-wrap:wrap;
     max-width:min(92vw,560px);background:#2b2620;color:#f2ede1;border-radius:6px;
     padding:5px 8px;box-shadow:0 4px 18px rgba(0,0,0,.35);font-size:13px}
  .stybar .ttl{color:#c9a24a;font-size:12px;padding:0 3px}
  .stybar .sep{width:1px;align-self:stretch;background:#5a5147;margin:2px 4px}
  .stybar button{font:inherit;font-size:13px;background:#413a31;color:#f2ede1;border:0;
     border-radius:4px;padding:3px 9px;cursor:pointer;white-space:nowrap}
  .stybar button:hover{background:var(--gold);color:#2b2620}
  .stybar button.on{background:var(--gold);color:#2b2620;font-weight:700}
  @media print{.stybar,.edbar{display:none!important}}
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
  .sgrow button{font:inherit;font-size:13px;background:#eeeae1;border:1px solid #e0d8c4;border-radius:4px;padding:2px 9px;cursor:pointer;margin-left:5px;margin-top:4px}
  .sqctx{background:#fff;border:1px dashed #d9d1bd;border-radius:4px;padding:5px 8px;margin:4px 0;font-size:14px;line-height:1.5}
  /* ד4: שורה שיש עליה הצעה ממתינה - צהוב עדין, רק במצב מנהל */
  .sgp{background:rgba(255,226,122,.38);border-radius:2px}
  #sqbtn.on{background:#a83c2f;color:#fff}
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
  @media screen and (max-width:760px){.src.split{left:0;right:0;top:auto;bottom:0;width:auto;height:60vh}
    body.splitsrc .flow{width:auto;margin-left:0}}
  @media print{.src,.srcb{display:none!important}}
  /* ---- תצוגת ספר והדפסה: עמוד הספר, 90x130 מ"מ ----
     הכרעת בעל הפרויקט, 27.9.2026: שורה נטו 6 ס"מ, שוליים ימין 2 ושמאל 1,
     וגובה הדף 13 ס"מ - וההדפסה כמו בוורד וכמו בתצוגה. נמדדו כל 28 קובצי
     הוורד, וזו הגיאומטריה של רובם המכריע; סוכה בת שני הטורים היא החריגה,
     ושני טוריה הם בעצם שני עמודים של 90 זה לצד זה.

     הגיליון הוא עתה העמוד כולו: 90x130 מ"מ, שוליים עליון 10, תחתון 5,
     שמאל 10; ובתוכו מסילה 20 ומידה 60. הכותרת הרצה יושבת בתוך 10 המ"מ
     העליונים ואינה אוכלת מגובה הטקסט, שהוא 115 מ"מ נטו.
     במידות ה-em של היחס הנעול (60 מ"מ = 20.75em): עמוד 31.125x44.979,
     כותרת רצה 3.458, שוליים תחתונים 1.729, וגוף הטקסט 39.792. */
  .flow.book{--lh:1.342;--lhpx:calc(var(--fs) * var(--lh));
             column-width:auto;column-count:auto;column-rule:0;
             column-fill:balance;line-height:var(--lh);
             display:grid;grid-template-columns:repeat(var(--sheets,2),31.125em);
             gap:1.4em;justify-content:center;align-content:start;
             padding:1em var(--gut);overflow:auto;direction:rtl}
  .sheet{width:31.125em;height:44.979em;background:var(--paper);overflow:hidden;
         box-shadow:0 1px 6px rgba(0,0,0,.14);border:1px solid #e6ddc9;border-radius:2px;
         padding:0 0 1.729em 3.458em;display:flex;flex-direction:column}
  .shhd{flex:0 0 auto;height:3.458em;display:flex;align-items:center;gap:.5em;font-size:.62em;
        color:#8a7d66;overflow:hidden;white-space:nowrap}
  /* הנושא הוא החלק שמתקצר, ולא שם המסכת וציון הדף */
  .shhd>span:nth-child(2){overflow:hidden;text-overflow:ellipsis;min-width:0}
  .shhd .nm{font-family:'Vilna',serif;font-weight:700;color:#5a5044}
  .shhd .sp{flex:1}
  .shhd .df{font-family:'VilnaG','Vilna',serif;color:var(--red);font-size:1.25em}
  .shbody{flex:1 1 auto;overflow:hidden;width:27.667em}
  .flow.book .row{break-inside:auto}
  #gauge{position:fixed;top:0;left:0;visibility:hidden;pointer-events:none;
         z-index:-1;overflow:hidden;contain:layout style;background:var(--paper)}
  /* בטלפון גיליון אחד, וגודל האות מוקטן כדי שרוחב הגיליון ייכנס למסך.
     זה בדיוק מה שהכלל הנעול מתיר: היחס קבוע, ורק --fs זז. בלעדי זה
     הגיליון יצא 553 פיקסל במסך של 375, והלומד היה נדרש לגלול לצדדים. */
  @media screen and (max-width:900px){.flow.book{--sheets:1!important;
    font-size:min(var(--fs),calc((100vw - 2.2rem) / 31.125))}}
  /* ד - ההדפסה היא מנוע הגיליונות, גיליון אחד בעמוד. גודל האות נגזר
     מן היחס הנעול (60 מ"מ חלקי 20.75) ורשת השורות 11 נקודות, כבוורד. */
  @media print{
    .flow.book{display:grid!important;grid-template-columns:90mm!important;gap:0;
               width:90mm;padding:0;justify-content:start;
               line-height:11pt;--lhpx:11pt;overflow:visible}
    .sheet{width:90mm;height:130mm;box-shadow:none;border:0;border-radius:0;
           padding:0 0 5mm 10mm;break-inside:avoid;break-after:page}
    .flow.book .sheet:last-child{break-after:auto}
    .shbody{width:80mm}
    .shhd{height:10mm;font-size:6.5pt}
  }
  /* ---- הדפסה: עמוד הספר עצמו ----
     הכרעת בעל הפרויקט, 27.9.2026: עמוד 90x130 מ"מ, טור אחד, מידה 60,
     שוליים ימין 20 (הם המסילה עצמה) ושמאל 10, עליון 10 ותחתון 5. זו
     הגיאומטריה של רוב קובצי הוורד; העמוד של 170 בשני טורים, שכויל
     בשלב ח1 על סוכה, היה החריג ולא הכלל.

     ההדפסה כולה עוברת עתה במנוע הגיליונות: הוא לבדו יודע לעמד בזהירות
     (כותרת אינה נפרדת מן התוכן שאחריה) ולתת כותרת רצה, ושני הדברים
     אינם אפשריים בטורי-CSS. לכן אין כאן עוד מסלול הדפסה של .flow.

     גודל האות בהדפסה נגזר מן היחס הנעול ולא נקבע לחוד: המידה 60 מ"מ
     והיחס 20.75, ולכן האות היא 60/20.75 מ"מ (כ-8.2 נקודות). בוורד היא
     9 נקודות, וההפרש הוא זה שנמדד בח0 - frank.ttf שבדפדפן רחב בכעשרה
     אחוזים ל-em מ-FrankRuehl. כך השורות מתלכדות עם הספר, ורשת השורות
     נשארת 11 נקודות כבוורד. */
  @media print{
    .bar,.panel{display:none}
    html,body{overflow:visible;background:#fff;height:auto}
    body{display:block}
    :root{--measure:60mm;--rail:20mm;--gut:0;--fs:calc(60mm / 20.75)}
    .flow{width:90mm;height:auto;overflow:visible;padding:0;
          font-size:var(--fs);line-height:11pt;--lhpx:11pt;
          columns:auto;column-count:1;column-gap:0;column-rule:0}
    .flow.vert{width:90mm;columns:auto;column-count:1;padding:0}
    .flow.vert .row{width:auto;margin:0}
    .row{grid-template-columns:20mm 60mm;break-inside:avoid}
    @page{size:90mm 130mm;margin:0}
  }
  /* שאילתת הטלפון מוגבלת למסך במפורש. בלעדי זה היא תפסה גם בהדפסה:
     עמוד של 170 מ"מ הוא כ-643 פיקסל, כלומר פחות מ-760, והיא באה אחרי
     גוש ההדפסה - ולכן היא ביטלה את שני הטורים ואת רוחב המסילה, והעמוד
     המודפס יצא טור אחד רחב. */
  @media screen and (max-width:760px){:root{--fs:20px}
    .flow{column-width:auto;column-count:1;column-rule:0;width:auto;padding:.7em .8em}
    .row{grid-template-columns:1fr;align-items:start}
    /* בטלפון המסילה מעל הטקסט, בשורה אחת, וציון הדף והחלון זה לצד זה */
    .rail{display:block;text-align:right;padding:0;line-height:1.06}
    .rail>*{line-height:inherit}
    .win{display:inline;white-space:normal}
    .win.w2{line-height:inherit}
    .anchor{display:inline;font-size:.82em;color:#4a4137}
    .dafmark{display:inline-block;margin-left:.5em}
    .mlabel{display:inline-block;margin-left:.4em}}
  '''

  # שער: סוגר מיותר בגיליון הסגנונות מבטל בשקט את הכלל שאחריו. כך אבדה
  # פעם שאילתת הטלפון כולה, והדף נראה תקין בכל מסך אחר.
  if CSS.count('{') != CSS.count('}'):
      raise SystemExit('עצירה: גיליון הסגנונות אינו מאוזן - %d פתיחות מול %d סגירות'
                       % (CSS.count('{'), CSS.count('}')))

  # ג: המקדמים שנמדדו מן הגופנים, ומרווחי השורה שנמדדו מן הוורד של
  # המסכת הזאת. הם נכתבים בסוף גיליון הסגנונות, ולכן גוברים על מה
  # שנכתב למעלה. מרווח השורה של כותרות פרק אינו נוגע כאן במתכוון:
  # פתיחת פרק תופסת מקום גם בספר.
  CSS = CSS + ('''
  @font-face{font-family:'Frank';src:url(fonts/frank-b.ttf);font-weight:700;
             font-display:swap;size-adjust:%.2f%%}
  @font-face{font-family:'Frank';src:url(fonts/frank-b.ttf);font-weight:900;
             font-display:swap;size-adjust:%.2f%%}
  :root{--k-nose:%.4f;--k-dh:%.4f;--k-mishna:%.4f}
  .main.nose,.main.dh,.main.mishna{line-height:var(--lhpx)}
  .main.hatz{line-height:calc(var(--lhpx) * %.4f)}
  ''' % (K_BOLD * 100, K_BOLD * 100, K_NOSE, K_DH, K_MISHNA, line_ratio('hatz')))

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
      else {
        /* האיחוי מקצר פסקאות, ולכן יחידה שהיו לה שתי שורות יכולה להיות
           בת שורה אחת. החלון נפרש לשתי שורות רק כשיש לטקסט שתיים, ולכן
           ההתאמה נעשית כאן שוב - אחרת נפערה שורה לבנה ליד החלון. */
        fitAnchors();
        if(btn){btn.classList.toggle('on',SQ);btn.title=fixed+' שורות אוחו מתוך '+ps.length}
      }
    }
    requestAnimationFrame(chunk);
  }
  function squeeze(){SQ=!SQ;localStorage.setItem('lg-sq',SQ?'1':'0');
    GEN++;
    $('#flow').querySelectorAll('.main p').forEach(p=>{p.style.wordSpacing='';p.style.letterSpacing=''});
    if(!SQ){$('#fbtn').classList.remove('on');$('#fbtn').title='האיחוי כבוי'}else squeezeRun()}
  /* ---- ב1: רוחב נתיב הדף, והתאמת החלון לנתיב שלו ----
     רוחב נתיב ציון הדף אינו מספר שנבחר: הוא נמדד מציון הדף הרחב ביותר
     במסכת, בגופן שבפועל, ונמדד מחדש אחרי שהגופנים נטענו. */
  /* גובה שורת הגוף בפיקסלים. --lhpx כתוב ביחידות שונות במצבים שונים
     (calc בזרימה ובספר, 11pt בהדפסה), ו-parseFloat על "11pt" נתן 11 -
     כלומר ספירת שורות מוגזמת בשליש בהדפסה, וממנה כותרות יתומות
     ורצועות שלא נפרשו. נמדד. */
  function lhOf(el){
    const v=(getComputedStyle(el).getPropertyValue('--lhpx')||'').trim();
    if(/^-?[\d.]+px$/.test(v))return parseFloat(v);
    if(/^-?[\d.]+pt$/.test(v))return parseFloat(v)*96/72;
    const lh=parseFloat(getComputedStyle(el).lineHeight);
    if(lh&&!isNaN(lh))return lh;
    const fs=parseFloat(getComputedStyle(el).fontSize)||18;
    return fs*1.06}
  let DAFW=0;
  function setDafW(){
    const fs=parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--fs'))||18;
    const cv=document.createElement('canvas'),cx=cv.getContext('2d');
    cx.font='400 '+(1.3*fs)+"px 'VilnaG','Vilna',serif";
    /* תווית טווח ("יד:-טו.") אינה קובעת את רוחב נתיב הדף של כל המסכת;
       היא מקבלת רוחב לשורה שלה בלבד (fitAnchors). */
    let w=0;for(const p of D.pages){const x=cx.measureText(p.daf||'').width;if(x>w)w=x}
    DAFW=Math.max(w+2,fs*1.1);
    document.documentElement.style.setProperty('--dafw',(DAFW/fs).toFixed(3)+'em');
  }
  function dafWidth(txt){
    const fs=parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--fs'))||18;
    const cv=document.createElement('canvas'),cx=cv.getContext('2d');
    cx.font='400 '+(1.3*fs)+"px 'VilnaG','Vilna',serif";
    return cx.measureText(txt||'').width+2;
  }
  /* חלון שאינו נכנס לנתיב הפנימי מטופל בסדר שנקבע: קודם מצטמצם נתיב הדף
     של אותה יחידה בלבד; אחר כך - ורק אם לטקסט שתי שורות לפחות - מותר לו
     לשורה שנייה; ואם גם זה לא, הוא מוקטן. לעולם אינו נחתך ואין ellipsis.
     הקריאות והכתיבות מופרדות, כדי שלא תהיה פריסה מחדש לכל יחידה. */
  const ASCALE=[1,.88,.8,.72];
  function trackW(rail){
    const g=getComputedStyle(rail).gridTemplateColumns.split(' ');
    return parseFloat(g[g.length-1])||0;
  }
  function fitAnchors(){
    const f=$('#flow');if(!f)return;
    const items=[];
    /* ב1: תווית טווח רחבה מנתיב הדף - הנתיב מורחב לשורה שלה בלבד */
    for(const d of f.querySelectorAll('.dafmark.rng')){
      const r=d.closest('.row');if(!r)continue;
      const w=dafWidth(d.textContent.trim())*0.95;
      r.style.setProperty('--dafw',Math.max(w,DAFW).toFixed(1)+'px');
    }
    for(const r of f.querySelectorAll('.row')){
      const a=r.querySelector(':scope > .rail > .win');
      if(!a||!a.textContent.trim())continue;
      a.classList.remove('w2');a.style.fontSize='';
      if(!r.querySelector('.dafmark.rng'))r.style.removeProperty('--dafw');
      items.push({r,a,rail:a.parentElement});
    }
    if(!items.length)return;
    const lhpx=lhOf(f);
    /* קריאה */
    for(const o of items){
      o.aw=o.a.getBoundingClientRect().width;
      o.tw=trackW(o.rail);
      const m=o.r.querySelector(':scope > .main');
      /* מספר שורות הטקסט נמדד על השורות עצמן ולא על גובה האלמנט: מרווח
         שנגזר מוורד יושב בתוך .main, ופסקה בת שורה אחת עם חצי שורת
         מרווח נראתה כשתי שורות - והחלון הורשה להיפרש על שתיים. */
      let ln=1;
      if(m){const rg=document.createRange();rg.selectNodeContents(m);
        const rs=[...rg.getClientRects()].filter(x=>x.height>0.5);
        if(rs.length){const t=Math.min(...rs.map(x=>x.top)),bt=Math.max(...rs.map(x=>x.bottom));
          ln=Math.max(1,Math.round((bt-t)/lhpx))}}
      o.lines=ln;
      o.dm=o.r.querySelector('.dafmark');
      /* ב2: ערימת חלונות גבוהה מן הטקסט שלה - נפרשת לשורה אחת, עם מפריד,
         כדי שהמסילה לא תגבה על היחידה. */
      if(o.a.classList.contains('stk')){
        const an=o.a.querySelector('.anchor');
        const n=an?an.querySelectorAll('br').length+1:1;
        if(n>ln&&an){an.innerHTML=an.innerHTML.replace(/<br\s*\/?>/g,' · ');o.a.classList.remove('stk');
          o.aw=o.a.getBoundingClientRect().width}
      }
    }
    /* כתיבה ראשונה: צמצום נתיב הדף ליחידה שצריכה זאת */
    const still=[];
    for(const o of items){
      if(o.aw<=o.tw+.5)continue;
      if(o.dm&&!o.dm.classList.contains('rng')){const w=dafWidth(o.dm.textContent.trim());
        if(w<DAFW-.5){o.r.style.setProperty('--dafw',w.toFixed(1)+'px');still.push(o);continue}}
      still.push(o);
    }
    if(!still.length)return;
    /* קריאה שנייה, ואז ההכרעה */
    for(const o of still)o.tw=trackW(o.rail);
    const wrapped=[];
    for(const o of still){
      if(o.aw<=o.tw+.5)continue;
      if(o.lines>=2&&!o.a.classList.contains('stk')){o.a.classList.add('w2');wrapped.push(o);continue}
      const need=o.tw/o.aw;
      let sc=ASCALE[ASCALE.length-1];
      for(const c of ASCALE)if(c<=need){sc=c;break}
      o.a.style.fontSize=sc.toFixed(3)+'em';
    }
    /* חלון שנפרש נשאר בגבול שתי שורות, ולעולם אינו עולה על מספר שורות
       הטקסט: אחרת הוא בעצמו פוער את השורה הלבנה שבאנו למנוע. הוא מוקטן
       עד שהוא נכנס, ולעולם אינו נחתך. */
    for(const o of wrapped){
      const cap=Math.min(2,o.lines)*lhpx+1;
      let sc=1;
      while(o.a.getBoundingClientRect().height>cap&&sc>0.62){
        sc-=0.07;o.a.style.fontSize=sc.toFixed(3)+'em';
      }
    }
  }
  /* ---- ד6: ההדפסה עוברת כולה במנוע הגיליונות ----
     רק הוא יודע לעמד בזהירות (כותרת אינה נפרדת מן התוכן שאחריה) ולתת
     כותרת רצה. שני הכפתורים וגם Ctrl+P של הדפדפן עוברים דרכו. */
  let PRINTING=0, PREBOOK=0;
  function printNow(all){
    const wasB=BOOK, wasA=ALL;
    BOOK=true; ALL=all; render(cur);
    setTimeout(()=>{PRINTING=1;window.print();PRINTING=0;
                    BOOK=wasB;ALL=wasA;render(cur)},700);
  }
  function toPdf(){printNow(true)}
  function printPerek(){printNow(false)}
  addEventListener('beforeprint',()=>{if(!PRINTING&&!BOOK){PREBOOK=1;BOOK=true;render(cur)}});
  addEventListener('afterprint',()=>{if(PREBOOK){PREBOOK=0;BOOK=false;render(cur)}});
  /* ב1: ציון הדף שמוצג הוא התווית - טווח כשציון קודם נשאר בלי טקסט -
     וציון הדף האמיתי נשמר ב-data-daf, שממנו קוראים העריכה וההצעות. */
  function dafMark(pi){const p=D.pages[pi];const lab=p.label||p.daf;
    return `<b class="dafmark${p.label?' rng':''}" id="d${pi}" data-daf="${esc(p.daf)}">${esc(lab)}</b>`}
  function unitHTML(u,daf,pi){
    const mk=daf!=null?dafMark(pi):'';
    const H=(u.ref?' data-ref="'+u.ref+'"':''),
          sb=u.ref?`<button class="srcb" onclick="openSrc('${u.ref}')" title="הגמרא המנוקדת (מקש מ)">מקור</button>`:'';
    /* המסילה היא גריד בן שני נתיבים: ציון הדף בחיצוני, וכל סמני הצד
       הפנימיים בתוך .win אחד - כדי שחלון ותווית "משנה" יישבו זה לצד זה
       באותה שורה, ולא ידחפו זה את זה לשורה שנייה.
       ב2: חלון שנערם על חלון (אין תחתיו טקסט) מסומן stk ומקבל רשת שורות. */
    const win=(w,lab)=>`<div class="rail">${mk}<span class="win${w&&w.indexOf('<br>')>-1?' stk':''}">`+
      (w?`<span class="anchor">${w}</span>`:'')+(lab?'<span class="mlabel">משנה</span>':'')+
      `</span></div>`;
    if(u.k==='u')return `<div class="row u" id="u${u.id}"${H}>${win(u.a,0)}<div class="main">${u.l.map((l,n)=>`<p class="${l[0]}">${l[1]}${n===u.l.length-1?sb:''}</p>`).join('')}</div></div>`;
    if(u.k==='m'){
      /* ז3 - הניקוד הוא שכבה נפרדת. במצב עריכה חוזרים לנוסח הוורד,
         כדי שהעיגון (הנוסח שהיה) יעבוד על הטקסט האמיתי ושלא ייכנס
         ניקוד לוורד בלי כוונה. */
      /* שכבת הניקוד תקפה רק כשהיא מקבילה לנוסח הוורד פסקה בפסקה.
         פיצול או איחוי משנים את אורך u.l, ואילו lv נבנה בבנייה הקודמת -
         ואז היה מספר הפסקאות המוצג שונה מזה שהמפתחות נגזרו ממנו. */
      const L=(NK&&!EDIT&&u.lv&&u.lv.length===u.l.length)?u.lv:u.l;
      return `<div class="row" id="u${u.id}"${H}>${win(u.w,1)}<div class="main mishna">${L.map((l,n)=>`<p class="${l[0]}">${l[1]}${n===L.length-1?sb:''}</p>`).join('')}</div></div>`;
    }
    /* א: החציצה אחידה - העיטור של סוכה בכל מקום. הנוסח שבוורד לא נגע. */
    if(u.k==='hatz')return `<div class="row hatz" id="u${u.id}"${H}>${win(u.w,0)}<div class="main hatz ${u.s||''}">${u.a}</div></div>`;
    return `<div class="row ${u.k}" id="u${u.id}"${H}>${win(u.w,0)}<div class="main ${u.k==='dh'||u.k==='nose'?u.k:''} ${u.s||''}">${u.a}${sb}</div></div>`;
  }
  /* ALL: מצב רצף - כל המסכת בטור אחד, מן הדף הראשון עד האחרון בגלילה אחת. */
  let ALL=false;
  function pagesHTML(from,to){let h='';
    for(let pi=from;pi<=to;pi++){const p=D.pages[pi];
      if(!p.units.length)continue;   /* ב1: עמוד בלי טקסט אינו נכתב (הבנייה כבר צירפה אותו לטווח) */
      let first=true;
      for(const u of p.units){h+=unitHTML(u,first?p.daf:null,first?pi:null);first=false}}
    return h}
  function render(si,q){
    cur=Math.max(0,Math.min(SEC.length-1,si));const s=SEC[cur];
    const f=$('#flow');
    f.classList.toggle('book',BOOK);
    if(BOOK)f.style.setProperty('--sheets',sheetsNow());
    const h=BOOK?bookHTML(ALL?0:s.from,ALL?D.pages.length-1:s.to)
                :(ALL?pagesHTML(0,D.pages.length-1):pagesHTML(s.from,s.to));
    f.innerHTML=q?hl(h,esc(q).replace(/"/g,'&quot;').replace(/'/g,'&#x27;')):h;
    if(!ALL&&!BOOK){f.scrollTop=0;f.scrollLeft=SGN>0?f.scrollWidth:0}
    if(BOOK){f.scrollTop=0;f.scrollLeft=0}
    $('#peresel').value=cur;$('#curdaf').textContent=D.pages[s.from].label||D.pages[s.from].daf;$('#dafsel').value=s.from;
    document.title=`לאוקמי גירסא · ${D.masechet} · ${ALL?'רצף':(s.perekName||s.perek||D.pages[s.from].daf)}`;
    location.hash=`p=${cur}`;
    fitAnchors();
    markEditable();applyEdits();
    if(typeof sqMark==='function')sqMark();
    if(EDIT)setEdit(true);
    if(!BOOK)squeezeRun();
  }
  function hl(h,q){const r=new RegExp('('+q.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')+')','g');return h.replace(/>([^<]+)</g,(m,t)=>'>'+t.replace(r,'<mark>$1</mark>')+'<')}
  function toDaf(pi){const si=secOf(pi);if(si!==cur)render(si);
    setTimeout(()=>{const e=$('#d'+pi);if(e)toEl(e);$('#curdaf').textContent=D.pages[pi].label||D.pages[pi].daf;$('#dafsel').value=pi},20)}
  function goDaf(d){const now=+$('#dafsel').value||0;toDaf(Math.max(0,Math.min(D.pages.length-1,now+d)))}
  function goScreen(d){const f=$('#flow');
    if(f.classList.contains('vert'))f.scrollBy({top:d*f.clientHeight*.9,behavior:'smooth'});
    else f.scrollBy({left:-d*f.clientWidth,behavior:'smooth'})}
  function fs(d){const r=document.documentElement;
    const v=Math.max(12,Math.min(60,parseFloat(getComputedStyle(r).getPropertyValue('--fs'))+d));setFs(v)}
  function setFs(v){document.documentElement.style.setProperty('--fs',v+'px');localStorage.setItem('lg-fs',v);sizeBtns(v);setDafW();fitAnchors()}
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
   setDafW();
   if(document.fonts&&document.fonts.ready)
     document.fonts.ready.then(()=>{setDafW();fitAnchors()});
   const ds=$('#dafsel');D.pages.forEach((p,i)=>ds.add(new Option(p.label||p.daf,i)));ds.onchange=()=>toDaf(+ds.value);
   const ps=$('#peresel');SEC.forEach((s,i)=>ps.add(new Option((s.perek||'רצף')+(s.perekName?' · '+s.perekName:''),i)));ps.onchange=()=>render(+ps.value);
   let t='',lp=-1;const TL={dh:'ד\u05f4ה',m:'משנה'};
   for(const [pi,id,s,kind] of D.toc){const si=secOf(pi);
     if(si!==lp){lp=si;t+=`<h3>${esc(SEC[si].perek||'')} ${esc(SEC[si].perekName||'')}</h3>`}
     const lab=TL[kind]?`<span class="tl${kind==='m'?' tlm':''}">${TL[kind]}</span>`:'';
     t+=`<a class="t-${kind}" onclick="jump(${pi},${id})"><small class="n">${esc(D.pages[pi].daf)}</small> ${lab}${esc(s)}</a>`}
   $('#tocb').innerHTML=t;
   $('#amb').innerHTML=`<div class="n">${D.nAm} אזכורי אמוראים מסומנים בקובץ; ${D.nPsk} ציטוטי פסוקים שונים</div><div class="chips">`+D.am.map((a,i)=>`<a class="tag" onclick="amq(${i})">${esc(a[0])} <span class="n">${a[1]}</span></a>`).join('')+'</div>';
   /* ב3: מה שטופל בתצוגה הוא מידע בלבד, באפור - לא משימה של בעל הפרויקט */
   $('#qab').innerHTML=D.qa.length?D.qa.map(q=>`<div class="res${q[0].indexOf('טופל בתצוגה')===0?' qgrey':''}"><b>${q[0]}</b>: ${esc(q[1])}</div>`).join(''):'לא נמצאו חריגות';
   /* מונֵי סוכן סריקת התצוגה, מן הסריקה האחרונה. הקריאה עצלה ואינה
      חוסמת דבר: בפתיחת קובץ מקומי היא נכשלת, והבקרה נשארת כשהיתה. */
   const MDNM={flow:'זרימה',book:'תצוגת ספר',print:'הדפסה'};
   if(location.protocol==='http:'||location.protocol==='https:')
   fetch('layout-audit.json').then(r=>r.json()).then(a=>{
     const m=a.m&&a.m[SLUG];if(!m||!m.modes)return;
     let t='<h3>סריקת תצוגה - '+esc(String(a.stamp||'').slice(0,16).replace('T',' '))+'</h3>';
     for(const md in m.modes){const c=m.modes[md];
       const li=Object.keys(c).filter(k=>c[k]).map(k=>esc(a.codes[k])+' '+c[k]).join(', ');
       t+='<div class="res"><b>'+esc(MDNM[md]||md)+'</b>: '+(li||'נקי')+'</div>'}
     $('#qab').insertAdjacentHTML('beforeend',t);
   }).catch(()=>{});
   const sv=+localStorage.getItem('lg-fs');if(sv)setFs(sv);else sizeBtns(18);
   if(localStorage.getItem('lg-vert')){$('#flow').classList.add('vert');$('#vbtn').classList.add('on');ALL=true}
   if(D.nk&&D.nk.voc){$('#nkbtn').style.display='';$('#nkbtn').classList.toggle('on',NK)}
   if(BOOK){$('#bkbtn').classList.add('on');$('#shsel').style.display=''}
   $('#shsel').value=SHEETS;
   addEventListener('resize',()=>{if(BOOK){$('#flow').style.setProperty('--sheets',sheetsNow())}});
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
   /* שינויי המבנה מוחלים על הנתונים לפני הרנדור הראשון, כדי שמפתחות
      הפסקאות שייקבעו בדף יהיו אלה שאחרי הפיצול. */
   applyStruct();
   const u0=params.get('u');
   if(u0){let pi=0;D.pages.forEach((p,i)=>{if(p.units.some(x=>x.id==u0))pi=i});jump(pi,+u0)}
   else render(+(params.get('p')||0));
   sqBadge();netInit();
  }
  /* =================== מצב עריכה למנהל ===================
     האתר סטטי ונבנה מחדש מן הוורד. עריכה כאן אינה נוגעת במקור: היא
     נשמרת במכשיר, נדחפת לקובץ תיקונים שבמאגר, מוחלת שם בבנייה הבאה
     על נתוני הדף, ונכנסת לוורד במעקב דרך הכלי היחיד שכותב לשם.

     העיגון אינו נשען על מספר הפסקה בלבד: לכל עריכה נשמרים גם הנוסח
     שהיה, הנוסח החדש, ציון הדף וכארבעים תווים מסביב. אם הפסקאות זזו
     בוורד, העריכה מאותרת מחדש באותו דף ועמוד לכל צד - ורק אם נמצאה
     התאמה אחת ויחידה. אחרת היא מוצגת בקול כ"תלושה" ואינה מוחלת, כדי
     ששינוי מבני בוורד לא יפזר עריכות על פסקאות זרות.

     כל ההשוואות נעשות על הטקסט הנקי - בלי כפתור "מקור", בלי תווית
     "משנה" ובלי סימון החיפוש. בלעדי זה נכנסה המילה "מקור" אל תוך
     הנוסח שנשלח לוורד. */
  const AKEY='lg-admin', EKEY='lg-ed-'+SLUG, TKEY='lg-gh', ADMIN_WORD='לאוקמי';
  const REPO='michaelFLEGG/leokmei-girsa', EDPATH='data/edits/'+SLUG+'.json';
  const CSTY=(D.sty&&D.sty.c)||[], PSTY=(D.sty&&D.sty.p)||[];
  const OKCLS=CSTY.map(x=>x[0]);
  const PCLS=PSTY.map(x=>x[0]).filter(Boolean);
  let ED=[]; try{ED=JSON.parse(localStorage.getItem(EKEY)||'[]')}catch(e){ED=[]}
  let EDIT=false, EDSTAT={taken:0,lost:0};
  function isAdmin(){try{return localStorage.getItem(AKEY)==='1'}catch(e){return false}}
  function ghTok(){try{return localStorage.getItem(TKEY)||''}catch(e){return ''}}
  /* אצל לומד שאינו מנהל ED הוא שכבת התיקונים שהתקבלו (מנקודת הקליטה),
     והיא אינה נשמרת במכשיר */
  function saveED(){if(typeof EDRO!=='undefined'&&EDRO)return;try{localStorage.setItem(EKEY,JSON.stringify(ED))}catch(e){}}
  function plain(h){const d=document.createElement('div');d.innerHTML=h;return d.textContent}

  /* ---- קריאה נקייה של אלמנט ניתן לעריכה ---- */
  function edClone(el){const d=el.cloneNode(true);
    d.querySelectorAll('.srcb,.mlabel').forEach(x=>x.remove());
    d.querySelectorAll('mark').forEach(m=>m.replaceWith(...m.childNodes));
    return d}
  function txtOf(el){return edClone(el).textContent}
  /* השוואה בלי ניקוד. במשנה, הטקסט שעל המסך מגיע משכבת הניקוד ואילו
     התיקון נרשם על נוסח הוורד; בלי הנרמול הזה תיקון של משנה פשוט לא
     היה נראה אחרי היציאה ממצב עריכה - ובשקט. */
  function nonik(t){return (t||'').replace(/[֑-ׇ]/g,'')}
  function edSan(root){
    /* רק סגנונות התו שבמפה נשארים. כל תגית אחרת מוסרת והטקסט נשמר.
       כפתור "מקור" ותווית "משנה" אינם טקסט של הספר אלא ריהוט של הדף,
       ולכן הם נשארים שלמים: בלעדי החרגה זו פורק הכפתור והמילה "מקור"
       נכנסה אל תוך נוסח הפסקה שנשלח לוורד. */
    [...root.querySelectorAll('*')].forEach(n=>{
      if(!n.isConnected||(n.closest&&n.closest('.srcb,.mlabel')))return;
      const tag=n.tagName.toLowerCase();
      n.removeAttribute('style');
      const ok=(tag==='i'&&n.classList.length===1&&OKCLS.indexOf(n.className)>-1)||
               (tag==='b'&&!n.className);
      if(!ok)n.replaceWith(...n.childNodes)});
    root.normalize();return root}
  function htmlOf(el){return edSan(edClone(el)).innerHTML}
  function setHTML(el,h){const b=el.querySelector('.srcb');
    el.innerHTML=h; if(b)el.appendChild(b)}
  /* מחלקת הפסקה, בלי מחלקות המרווח שנגזרו מוורד (b0-b4 / a0-a4) */
  function pcls(el){return [...el.classList].filter(c=>PCLS.indexOf(c)>-1).join(' ')}

  /* כל המקומות הניתנים לעריכה, בכל המסכת, באותו סדר שבו הם מסומנים בדף */
  function slots(){const out=[];
    D.pages.forEach((p,pi)=>p.units.forEach(u=>{
      const add=(kk,h)=>out.push({pi,daf:p.daf,k:'u'+u.id+kk,t:plain(h)});
      if(u.k==='u'){ if(u.a)add('.0',u.a);
        u.l.forEach((l,i)=>add('.'+(i+1),l[1])); }
      else if(u.k==='m'){ u.l.forEach((l,i)=>add('.'+(i+1),l[1])); }
      else if(u.k==='dh'||u.k==='nose'){ add('.0',u.a); }
      if(u.k!=='u'&&u.w)add('.w',u.w);
    }));
    return out}
  let SLOTS=null;
  function dafKey(d){if(!d)return null;const V={'א':1,'ב':2,'ג':3,'ד':4,'ה':5,'ו':6,'ז':7,'ח':8,'ט':9,'י':10,'כ':20,'ל':30,'מ':40,'נ':50,'ס':60,'ע':70,'פ':80,'צ':90,'ק':100,'ר':200,'ש':300,'ת':400};
    const t=d.trim();const am=t.endsWith(':')?1:0;let n=0;
    for(const c of t.replace(/[.:"'׳״]/g,''))n+=V[c]||0;return n?n*2+am:null}

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

  /* מסמן כל מקום שניתן לעריכה, ומחיל את מה שנשמר.
     בתצוגת ספר לא מסמנים: שם יחידה ארוכה מתחלקת בין גיליונות, ושני
     חלקיה היו נושאים את אותו מפתח בדיוק. */
  function markEditable(){
    const f=$('#flow');
    if(f.classList.contains('book'))return;
    f.querySelectorAll('.row').forEach(row=>{
      const id=row.id;if(!id)return;
      /* חלון שיושב במסילה של כותרת אינו הכותרת עצמה, ולכן הוא נושא
         מפתח משלו. בלעדי זה היו שני אלמנטים באותו מפתח, ועריכת כותרת
         היתה נופלת על החלון. */
      const a=row.querySelector('.anchor');
      if(a)a.dataset.ek=id+(row.classList.contains('u')?'.0':'.w');
      const m=row.querySelector('.main');
      if(!m)return;
      const ps=m.querySelectorAll('p');
      /* חציצה שבתוך משנה אינה טקסט לעריכה */
      if(ps.length)ps.forEach((x,i)=>{if(!x.classList.contains('hatz'))x.dataset.ek=id+'.'+(i+1)});
      else if(m.classList.contains('dh')||m.classList.contains('nose'))m.dataset.ek=id+'.0';
    });
    /* הכפתור יושב בתוך הפסקה הנערכת. בלי הסימון הזה מחיקה אחת אחורה
       בסוף הפסקה היתה מוחקת אותו. */
    f.querySelectorAll('.srcb,.mlabel').forEach(x=>x.setAttribute('contenteditable','false'))}
  function applyEdits(){
    if(!ED.length)return;
    SLOTS=slots();
    const f=$('#flow');let taken=0,lost=0,keep=[];
    for(const e of ED){
      if(e.op==='struct'){
        if(e.done)  {taken++;continue}       /* כבר בוורד - יוצא מן הרשימה */
        if(e.lost)  lost++;
        keep.push(e);continue}
      const k=locate(e);
      if(k===null){lost++;e.lost=1;keep.push(e);continue}
      e.lost=0;if(k!==e.k)e.k=k;
      const el=f.querySelector('[data-ek="'+k+'"]');
      const cur=el?txtOf(el):(SLOTS.find(s=>s.k===k)||{}).t;
      const same=x=>cur===x||nonik(cur)===nonik(x);
      if(same(e.now)&&e.ps===undefined){taken++;continue}
      /* פסקה שתוקנה מוצגת בנוסח הוורד עד לפרסום: שכבת הניקוד נבנית
         מן המקור בבנייה, ואינה יודעת על התיקון שנעשה זה עתה. */
      if(el&&same(e.was))setHTML(el,e.nowH!==undefined?e.nowH:esc(e.now));
      if(el&&e.ps!==undefined&&el.tagName==='P'){
        PCLS.forEach(c=>el.classList.remove(c));
        if(e.ps)e.ps.split(' ').filter(Boolean).forEach(c=>el.classList.add(c));
      }
      if(el)el.dataset.edited='1';
      keep.push(e)}
    EDSTAT={taken,lost};
    if(keep.length!==ED.length){ED=keep;saveED()}
    if($('#edn'))$('#edn').textContent=ED.length}

  function ctxOf(el){
    const rows=[...$('#flow').querySelectorAll('.main p, .main.dh, .main.nose, .anchor')];
    const i=rows.indexOf(el);
    return {b:(i>0?txtOf(rows[i-1]):'').slice(-40),a:(i>=0&&i<rows.length-1?txtOf(rows[i+1]):'').slice(0,40)}}

  /* ---- לכידת מצבו של אלמנט אחרי עריכה ----
     נקודת המוצא נרשמת לכל מקום ניתן לעריכה ברגע הכניסה למצב עריכה,
     ולא באירוע המיקוד: מיקוד אינו מובטח (מגע בטאבלט, שינוי סגנון
     בסרגל, הדבקה) ובלעדיו נערך טקסט בלי שתישמר נקודת החזרה. אם
     המקום כבר נערך בעבר, נקודת המוצא היא הנוסח המקורי שנשמר
     בעריכה - ולא הנוסח המתוקן שעל המסך. בלעדי זה היה "הנוסח שהיה"
     שנשלח לוורד מתאר טקסט שאינו קיים בו. */
  function edBase(el){
    const e=ED.find(x=>x.k===el.dataset.ek);
    el.__was=e?e.was:txtOf(el);
    el.__wasH=e?(e.wasH!==undefined?e.wasH:htmlOf(el)):htmlOf(el);
    el.__wasP=(e&&e.wasP!==undefined)?e.wasP:pcls(el)}
  function edFocus(ev){const el=ev.target.closest&&ev.target.closest('[contenteditable]');
    if(el&&el.__was===undefined)edBase(el)}
  function edBlur(ev){const el=ev.target.closest&&ev.target.closest('[contenteditable]');if(el)capture(el)}
  function capture(el){
    if(el.__was===undefined)edBase(el);
    edSan(el);
    const now=txtOf(el), nowH=htmlOf(el), nowP=pcls(el);
    const was=el.__was, wasH=el.__wasH, wasP=el.__wasP;
    const same=(now===was&&nowH===wasH&&nowP===wasP);
    const k=el.dataset.ek;const row=el.closest('.row');
    const daf=(()=>{let r=row;while(r){const d=r.querySelector('.dafmark');if(d)return d.dataset.daf||d.textContent;r=r.previousElementSibling}return ''})();
    const old=ED.find(x=>x.k===k);
    if(same){
      if(old){ED=ED.filter(x=>x!==old);delete el.dataset.edited}
    }else if(old){
      if(old.wasP===undefined)old.wasP=wasP;
      old.now=now;old.nowH=nowH;old.t=Date.now();old.pub=0;
      if(nowP!==old.wasP){old.ps=nowP;old.psw=wsty(nowP)} else {delete old.ps;delete old.psw}
      if(now===old.was&&nowH===old.wasH&&old.ps===undefined){
        ED=ED.filter(x=>x!==old);delete el.dataset.edited}
      else el.dataset.edited='1';
    }else{
      const e={k,was,now,wasH,nowH,wasP,daf,ctx:ctxOf(el),t:Date.now(),pub:0};
      if(nowP!==wasP){e.ps=nowP;e.psw=wsty(nowP)}
      ED.push(e);el.dataset.edited='1';
    }
    saveED();if($('#edn'))$('#edn').textContent=ED.length;drawEd();pubSoon();syncSoon()}
  let CAPT=null;
  function captureSoon(el){clearTimeout(CAPT);CAPT=setTimeout(()=>capture(el),700)}

  /* =================== ו2 ג-ד: פיצול פסקה ואיחויה ===================
     Enter מפצל פסקה לשתיים באותו סגנון; מחיקה אחורה בראש פסקה מאחדת
     אותה עם הקודמת. שתי הפעולות אינן עריכת טקסט אלא שינוי מבנה, ולכן
     הן נרשמות ברשומה משלהן ומוחלות על הנתונים עצמם (D) ולא על ה-DOM:
     בלעדי זה היו מפתחות הפסקאות שאחרי הפיצול זזים באחד, וכל תיקון
     שנרשם עליהן היה נופל על פסקה שכנה.

     העיגון אינו מספר הפסקה אלא הטקסט עצמו: הרשומה נושאת את נוסח
     הפסקאות לפני הפעולה ואת נוסחן אחריה, והאיתור דורש התאמה אחת
     ויחידה ברצף פסקאות סמוכות באותה יחידה. אם הנוסח זז בוורד -
     הפעולה אינה מוחלת, ונאמרת בקול כ"תלושה". */
  function unitsAll(){const out=[];
    D.pages.forEach((p,pi)=>p.units.forEach(u=>{if(u.k==='u'||u.k==='m')out.push({u,pi,daf:p.daf})}));
    return out}
  /* מאתר רצף פסקאות סמוכות ביחידה אחת שנוסחן הוא texts. דורש ייחוד. */
  function findRun(texts,daf){
    const hits=[];
    for(const o of unitsAll()){
      const L=o.u.l;
      for(let i=0;i+texts.length<=L.length;i++){
        let ok=true;
        for(let j=0;j<texts.length;j++)if(plain(L[i+j][1])!==texts[j]){ok=false;break}
        if(ok)hits.push({u:o.u,i,daf:o.daf});
      }
    }
    if(hits.length===1)return hits[0];
    if(hits.length>1&&daf){
      const k0=dafKey(daf);
      const near=hits.filter(h=>{const k=dafKey(h.daf);return k0===null||k===null?false:Math.abs(k-k0)<=1});
      if(near.length===1)return near[0];
    }
    return null}
  /* מחיל את שינויי המבנה על D. חייב לרוץ לפני הרנדור הראשון. */
  function applyStruct(){
    let any=false;
    for(const e of ED){
      if(e.op!=='struct')continue;
      const hit=findRun(e.texts,e.daf);
      if(hit){hit.u.l.splice(hit.i,e.texts.length,...e.res.map(x=>x.slice()));
        delete hit.u.lv;        /* שכבת הניקוד אינה תואמת עוד */
        e.lost=0;any=true;continue}
      if(findRun(e.resT,e.daf)){e.lost=0;e.done=1;continue}   /* כבר בוורד */
      e.lost=1;
    }
    if(any)SLOTS=null;
    return any}

  /* --- הפעולות עצמן, מן הדף --- */
  function pInfo(el){
    /* היחידה והמקום של פסקה שנערכת, מתוך המפתח שסומן עליה */
    const k=el.dataset.ek||'';const m=k.match(/^u(\d+)\.(\d+)$/);
    if(!m)return null;
    const id=+m[1], n=+m[2]-1;
    for(const o of unitsAll())if(o.u.id===id&&n>=0&&n<o.u.l.length)
      return {u:o.u,i:n,daf:o.daf,pi:o.pi};
    return null}
  function dafOf(el){let r=el.closest('.row');
    while(r){const d=r.querySelector('.dafmark');if(d)return d.dataset.daf||d.textContent;r=r.previousElementSibling}
    return ''}
  function splitAtCaret(el){
    const info=pInfo(el);if(!info)return false;
    const s=getSelection();if(!s.rangeCount)return false;
    const r=s.getRangeAt(0);
    if(!el.contains(r.startContainer))return false;
    /* שני חצאי הפסקה, כל אחד עם סגנונות התו שבו */
    const a=r.cloneRange();a.selectNodeContents(el);a.setEnd(r.startContainer,r.startOffset);
    const b=r.cloneRange();b.selectNodeContents(el);b.setStart(r.endContainer,r.endOffset);
    const box=x=>{const d=document.createElement('div');d.appendChild(x.cloneContents());
      d.querySelectorAll('.srcb,.mlabel').forEach(n=>n.remove());return edSan(d)};
    const da=box(a), db=box(b);
    const ha=da.innerHTML, hb=db.innerHTML;
    if(!da.textContent.trim()||!db.textContent.trim()){
      flash('אין לפצל כאן: אחד משני החלקים יוצא ריק');return false}
    const cls=info.u.l[info.i][0];
    const was=plain(info.u.l[info.i][1]);
    ED.push({op:'struct',kind:'split',texts:[was],
             res:[[cls,ha],[cls,hb]],resT:[da.textContent,db.textContent],
             daf:dafOf(el),t:Date.now(),pub:0});
    info.u.l.splice(info.i,1,[cls,ha],[cls,hb]);
    delete info.u.lv;
    SLOTS=null;saveED();
    reflow('u'+info.u.id+'.'+(info.i+2),0);
    return true}
  /* איחוי שמבטל בדיוק פיצול שנעשה זה עתה - מוחק את הפיצול במקום
     לרשום פעולה נגדית. בלעדי זה היו נשמרות שתי פעולות שמבטלות זו את
     זו, והן היו נשלחות לוורד ומסמנות שם שני שינויים לחינם. */
  function cancelSplit(texts){
    for(let i=ED.length-1;i>=0;i--){
      const e=ED[i];
      if(e.op!=='struct')continue;
      if(e.kind==='split'&&e.resT.length===2&&
         e.resT[0]===texts[0]&&e.resT[1]===texts[1]){ED.splice(i,1);return true}
      break}
    return false}
  function mergeBack(el){
    const info=pInfo(el);if(!info)return false;
    let u=info.u, i=info.i;
    if(i===0){
      /* פסקה ראשונה ביחידה: אפשר לאחד רק אם אין ליחידה חלון משלה,
         שאם יש - החלון מצביע עליה, ואיחוי היה מנתק אותו ממנה. */
      const all=unitsAll();const n=all.findIndex(o=>o.u===u);
      const prev=n>0?all[n-1]:null;
      if(!prev||prev.u.k!==u.k||plain(u.a||'')||!prev.u.l.length){
        flash('אי אפשר לאחד כאן: הפסקה פותחת קטע משלה');return false}
      /* מעבירים את פסקאות היחידה אל הקודמת */
      const texts=[plain(prev.u.l[prev.u.l.length-1][1]),plain(u.l[0][1])];
      const cls=prev.u.l[prev.u.l.length-1][0];
      const h=prev.u.l[prev.u.l.length-1][1]+u.l[0][1];
      const d=document.createElement('div');d.innerHTML=h;
      if(!cancelSplit(texts))
        ED.push({op:'struct',kind:'merge',texts:texts,res:[[cls,h]],
                 resT:[d.textContent],daf:dafOf(el),t:Date.now(),pub:0});
      prev.u.l[prev.u.l.length-1]=[cls,h];delete prev.u.lv;
      u.l.shift();delete u.lv;
      if(!u.l.length&&!plain(u.a||'')){
        for(const p of D.pages){const k=p.units.indexOf(u);if(k>-1){p.units.splice(k,1);break}}}
      SLOTS=null;saveED();
      reflow('u'+prev.u.id+'.'+prev.u.l.length,texts[0].length);
      return true}
    const texts=[plain(u.l[i-1][1]),plain(u.l[i][1])];
    const cls=u.l[i-1][0];
    const h=u.l[i-1][1]+u.l[i][1];
    const d=document.createElement('div');d.innerHTML=h;
    if(!cancelSplit(texts))
      ED.push({op:'struct',kind:'merge',texts:texts,res:[[cls,h]],
               resT:[d.textContent],daf:dafOf(el),t:Date.now(),pub:0});
    u.l.splice(i-1,2,[cls,h]);
    delete u.lv;
    SLOTS=null;saveED();
    reflow('u'+u.id+'.'+i,texts[0].length);
    return true}
  /* בונה את הדף מחדש אחרי שינוי מבנה, ומחזיר את הסמן למקומו */
  function reflow(key,off){
    render(cur);
    if(EDIT)setEdit(true);
    setTimeout(()=>{
      const el=$('#flow').querySelector('[data-ek="'+key+'"]');
      if(!el)return;
      el.focus();
      try{
        const w=document.createTreeWalker(el,NodeFilter.SHOW_TEXT);
        let n,left=off,node=null,pos=0;
        while((n=w.nextNode())){const L=n.textContent.length;
          if(left<=L){node=n;pos=left;break}left-=L}
        const r=document.createRange();
        if(node)r.setStart(node,pos); else r.selectNodeContents(el),r.collapse(false);
        r.collapse(true);
        const s=getSelection();s.removeAllRanges();s.addRange(r);
        el.scrollIntoView({block:'nearest'});
      }catch(e){}
      drawEd();pubSoon();
    },0)}
  function flash(msg){
    let b=$('#edflash');
    if(!b){b=document.createElement('div');b.id='edflash';b.className='edflash';document.body.appendChild(b)}
    b.textContent=msg;b.style.display='block';
    clearTimeout(b.__t);b.__t=setTimeout(()=>{b.style.display='none'},3200)}
  /* מחיקה אחורה בראש פסקה: רק כשהסמן באמת בתו הראשון ואין בחירה */
  function atStart(el){
    const s=getSelection();if(!s.rangeCount)return false;
    const r=s.getRangeAt(0);if(!r.collapsed)return false;
    const q=document.createRange();q.selectNodeContents(el);q.setEnd(r.startContainer,r.startOffset);
    return q.toString().length===0}

  function setEdit(on){
    const was=EDIT;
    if(on&&$('#flow').classList.contains('book')){
      alert('בתצוגת ספר אין עריכה, מפני שפסקה אחת עשויה להתחלק בין שני גיליונות. סגור את תצוגת הספר ונסה שוב.');
      return}
    EDIT=on;document.body.classList.toggle('ed',on);
    /* המשניות מוצגות מנוקדות, ובמצב עריכה הן חייבות לחזור לנוסח
       הוורד. הבנייה מחדש נעשית לפני סימון המקומות הניתנים לעריכה. */
    if(was!==on&&typeof NK!=='undefined'&&NK&&D.nk&&D.nk.voc)render(cur);
    const f=$('#flow');
    f.querySelectorAll('[data-ek]').forEach(el=>{
      if(on){el.setAttribute('contenteditable','true');el.setAttribute('spellcheck','false');edBase(el)}
      else {el.removeAttribute('contenteditable');delete el.__was;delete el.__wasH;delete el.__wasP}});
    let bar=$('#edbar');
    if(on&&!bar){bar=document.createElement('div');bar.className='edbar';bar.id='edbar';
      bar.innerHTML='<b>מצב עריכה</b><span>· <span id="edn">'+ED.length+'</span> תיקונים</span>'+
        '<span id="edpub" class="edpub"></span>'+
        '<button onclick="panel(\'ed\')">העריכות שלי</button>'+
        '<button onclick="pubNow(1)">פרסם עכשיו</button><span class="sp"></span>'+
        '<button onclick="setEdit(false)">סיום</button>';
      document.body.appendChild(bar);pubDraw()}
    else if(!on&&bar)bar.remove();
    if(!on)hideSty();
    if($('#edbtn'))$('#edbtn').classList.toggle('on',on);
    if(on)drawEd()}
  function askAdmin(){
    if(isAdmin()){setEdit(!EDIT);return}
    const a=prompt('מילת המנהל:');
    if(a===null)return;
    if(a.trim()===ADMIN_WORD){try{localStorage.setItem(AKEY,'1')}catch(e){}setEdit(true);
      sqBadge();if(!admKey())admKeyAsk();else netInit()}
    else alert('המילה אינה נכונה.')}

  /* =================== סרגל הסגנונות הצף ===================
     נפתח מעל הבחירה ואינו מכסה את הטקסט הנערך. שמות הסגנונות הם
     השמות שבעל הפרויקט מכיר מן הוורד, והרשימה נגזרת ממפת הסגנונות
     של הפרויקט ואינה נכתבת כאן ביד. */
  function edEl(){const s=getSelection();if(!s||!s.rangeCount)return null;
    let n=s.getRangeAt(0).commonAncestorContainer;
    if(n.nodeType===3)n=n.parentNode;
    return n&&n.closest?n.closest('[contenteditable="true"]'):null}
  /* selectionchange נורה גם על שינוי DOM ליד הבחירה. בלי חתימה
     שמונעת בנייה מחדש מיותרת, כל פתיחה של הסרגל היתה מפעילה את
     האירוע מחדש - והדף נתקע בלולאה אינסופית. נמדד. */
  let STYSIG='', STYT=null;
  function styLater(){clearTimeout(STYT);STYT=setTimeout(showSty,60)}
  function hideSty(){STYSIG='';const b=$('#stybar');if(b)b.style.display='none'}
  function showSty(){
    if(!EDIT)return;
    const el=edEl();const s=getSelection();
    if(!el||!s||!s.rangeCount){hideSty();return}
    const r=s.getRangeAt(0);
    let rc0=r.getBoundingClientRect();
    if(!rc0.width&&!rc0.height)rc0=el.getBoundingClientRect();
    const sig=[el.dataset.ek||'',r.collapsed,pcls(el),Math.round(rc0.left),Math.round(rc0.top)].join('|');
    if(sig===STYSIG)return;
    STYSIG=sig;
    let bar=$('#stybar');
    if(!bar){bar=document.createElement('div');bar.id='stybar';bar.className='stybar';
      document.body.appendChild(bar)}
    const sel=!r.collapsed;
    let h='';
    if(sel)h+='<span class="ttl">סגנון תו</span>'+
      CSTY.map(c=>'<button onmousedown="event.preventDefault()" onclick="setCs(\''+c[0]+'\')">'+esc(c[1])+'</button>').join('')+
      '<button onmousedown="event.preventDefault()" onclick="setCs(\'\')">ללא סגנון</button>';
    if(el.tagName==='P'){
      const now=pcls(el);
      h+=(sel?'<span class="sep"></span>':'')+'<span class="ttl">סגנון פסקה</span>'+
        PSTY.map(p=>'<button class="'+(now===p[0]?'on':'')+'" onmousedown="event.preventDefault()" onclick="setPs(\''+p[0]+'\')">'+esc(p[1])+'</button>').join('')}
    if(!h){hideSty();return}
    bar.innerHTML=h;bar.style.display='flex';
    let rc=r.getBoundingClientRect();
    if(!rc.width&&!rc.height)rc=el.getBoundingClientRect();
    const bc=bar.getBoundingClientRect();
    let top=rc.top-bc.height-8; if(top<6)top=rc.bottom+8;
    let left=rc.left+rc.width/2-bc.width/2;
    left=Math.max(6,Math.min(innerWidth-bc.width-6,left));
    bar.style.top=top+'px';bar.style.left=left+'px'}
  function setCs(c){
    const el=edEl();if(!el)return;
    const s=getSelection();if(!s.rangeCount||s.getRangeAt(0).collapsed)return;
    const r=s.getRangeAt(0);
    const box=document.createElement('div');
    box.appendChild(r.extractContents());
    /* סגנון קיים בתוך הבחירה מוסר, כדי שלא ייווצרו שכבות על שכבות */
    [...box.querySelectorAll('i,b')].forEach(n=>{
      if((n.tagName==='I'&&OKCLS.indexOf(n.className)>-1)||n.tagName==='B')
        n.replaceWith(...n.childNodes)});
    let node;
    if(c){node=document.createElement('i');node.className=c;
      while(box.firstChild)node.appendChild(box.firstChild)}
    else {node=document.createDocumentFragment();
      while(box.firstChild)node.appendChild(box.firstChild)}
    r.insertNode(node);
    el.normalize();
    getSelection().removeAllRanges();
    capture(el);hideSty()}
  function setPs(c){
    const el=edEl();if(!el||el.tagName!=='P')return;
    PCLS.forEach(x=>el.classList.remove(x));
    if(c)c.split(' ').filter(Boolean).forEach(x=>el.classList.add(x));
    capture(el);STYSIG='';styLater()}

  function drawEd(){
    const box=$('#edb');if(!box)return;
    const by={};for(const e of ED)(by[e.daf||'']=by[e.daf||'']||[]).push(e);
    const np=ED.filter(e=>!e.pub).length;
    let h='<div class="edsum">'+ED.length+' תיקונים'+
      (ED.length?(np?' · <b>'+np+' טרם פורסמו</b>':' · כולם פורסמו'):'')+
      (EDSTAT.taken?' · '+EDSTAT.taken+' כבר נקלטו':'')+
      (EDSTAT.lost?' · <b style="color:#a83c2f">'+EDSTAT.lost+' תלושים</b> - הפסקה שלהם השתנתה בוורד ולכן אינם מוחלים':'')+
      '</div>';
    for(const d of Object.keys(by)){
      h+='<h3>'+esc(d||'בלא ציון דף')+'</h3>';
      by[d].forEach(e=>{const i=ED.indexOf(e);
        const head=(e.lost?'<small>תלוש - לא הוחל</small><br>':'')+
          (e.pub?'':'<small>ממתין לפרסום</small><br>');
        if(e.op==='struct'){
          h+='<div class="edrow'+(e.lost?' edlost':'')+'">'+head+
            '<small>'+(e.kind==='split'?'פיצול פסקה':'איחוי שתי פסקאות')+'</small><br>'+
            '<span class="now">'+esc((e.kind==='split'?e.resT:e.texts).join(' ⟂ ').slice(0,110))+'</span><br>'+
            '<button onclick="undoEd('+i+')">ביטול</button></div>';
          return}
        h+='<div class="edrow'+(e.lost?' edlost':'')+'">'+head+
          (e.ps!==undefined?'<small>סגנון פסקה: '+esc(psName(e.ps))+'</small><br>':'')+
          '<span class="was">'+esc(e.was.slice(0,90))+'</span><br>'+
          '<span class="now">'+esc(e.now.slice(0,90))+'</span><br>'+
          '<button onclick="undoEd('+i+')">ביטול</button></div>'})}
    if(!ED.length)h='<div class="edsum">אין עדיין תיקונים.</div>';
    h+='<div style="margin-top:12px;display:flex;gap:7px;flex-wrap:wrap">'+
       '<button onclick="pubNow(1)">פרסם עכשיו</button>'+
       '<button onclick="edDownload()" title="גיבוי בלבד; הקליטה לוורד קוראת מנקודת הקליטה">הורד לקובץ (גיבוי)</button>'+
       '<button onclick="admKeyAsk()">מפתח המנהל</button>'+
       '<button onclick="edKey()">מפתח הפרסום</button>'+
       '<button onclick="edClear()">נקה הכל</button></div>';
    box.innerHTML=h}
  function psName(c){const f=PSTY.find(p=>p[0]===(c||''));return f?f[1]:(c||'גוף')}
  /* שם הסגנון בוורד, כפי שהוא בקובץ הזה. נשמר עם התיקון כדי שהקליטה
     לא תצטרך לנחש, ולא תמציא סגנון שאינו קיים. */
  function wsty(c){const f=PSTY.find(p=>p[0]===(c||''));return f?f[2]:''}
  function undoEd(i){const e=ED[i];if(!e)return;
    /* ביטול שינוי מבנה מחזיר את הנתונים למקורם, והדרך הבטוחה לכך
       היא לטעון את הדף מחדש: הוא נבנה מן הנתונים שבקובץ. */
    if(e.op==='struct'){ED.splice(i,1);saveED();location.reload();return}
    const el=$('#flow').querySelector('[data-ek="'+e.k+'"]');
    if(el){setHTML(el,e.wasH!==undefined?e.wasH:esc(e.was));delete el.dataset.edited;
      delete el.__was;
      if(e.ps!==undefined&&el.tagName==='P'){PCLS.forEach(c=>el.classList.remove(c));
        (e.wasP||'').split(' ').filter(Boolean).forEach(c=>el.classList.add(c))}}
    ED.splice(i,1);tomb(e.k);saveED();if($('#edn'))$('#edn').textContent=ED.length;drawEd();pubSoon();syncSoon()}
  function edClear(){if(!confirm('למחוק את כל '+ED.length+' התיקונים? הם יימחקו גם מן הפרסום ומכל המכשירים.'))return;
    ED.forEach(e=>tomb(e.k));ED=[];saveED();render(cur);drawEd();pubSoon();syncSoon()}
  function edText(){
    let t='תיקוני '+D.masechet+' - לאוקמי גירסא\n'+new Date().toLocaleString('he-IL')+'\n';
    t+=ED.length+' תיקונים\n\n';
    for(const e of ED){t+='דף '+(e.daf||'-')+(e.lost?'  [תלוש - הפסקה השתנתה בוורד]':'')+'\n';
      if(e.op==='struct'){
        t+='  '+(e.kind==='split'?'פיצול פסקה':'איחוי שתי פסקאות')+'\n';
        t+='  היה: '+e.texts.join(' | ')+'\n  יהיה: '+e.resT.join(' | ')+'\n\n';
        continue}
      if(e.ps!==undefined)t+='  סגנון פסקה: '+psName(e.ps)+'\n';
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

  /* =================== פרסום מיידי ===================
     האתר סטטי ואין לו שרת. התיקונים נדחפים לקובץ אחד שבמאגר דרך
     ממשק גיטהאב, ומשם רצה בנייה קצרה שמחילה אותם על נתוני הדף
     ומפרסמת. מפתח הכתיבה נשמר רק בדפדפן של המנהל, לעולם לא בקוד
     ולא במאגר. */
  /* כשהדף מוגש מן הגשר עצמו - הפנייה אליו היא באותו מקור, ואין שום
     חסימה. מדף שנטען מן הכתובת הציבורית אי אפשר לפנות אליו כלל:
     הדפדפן חוסם פנייה מ-https אל 127.0.0.1. נמדד. */
  const ONGESHER=(location.hostname==='127.0.0.1'&&location.port==='8760');
  const GESHER=ONGESHER?'':(location.protocol==='http:'?'http://127.0.0.1:8760':null);
  let PUBT=null, PUBBUSY=false, PUBMSG='', GOK=null, PUBLAST=null;
  /* הגשר הוא תוכנית קטנה שרצה ברקע במחשב של בעל הפרויקט, וכותבת
     למאגר בהרשאה שכבר קיימת שם. כשהוא עונה - אין צורך בשום מפתח,
     ובעל הפרויקט אינו עושה דבר. במכשיר אחר (טאבלט) הוא אינו עונה,
     ואז נדרש מפתח כתיבה שנשמר באותו מכשיר. */
  async function gesher(path,opt){
    if(GESHER===null)return {ok:false,why:'אין גשר'};
    /* הכתיבה עצמה עוברת שתי פניות לגיטהאב, ובחיבור אטי היא נמשכת.
       פסק זמן קצר מדי נראה בדיוק כמו "אין גשר", והמשתמש היה נשלח
       להזין מפתח בלי סיבה. */
    const c=new AbortController(), t=setTimeout(()=>c.abort(),opt&&opt.body?30000:1500);
    try{const r=await fetch(GESHER+path,Object.assign({signal:c.signal,cache:'no-store'},opt||{}));
      clearTimeout(t);
      if(!r.ok)return {ok:false,why:'הגשר השיב '+r.status};
      return await r.json();
    }catch(e){clearTimeout(t);
      return {ok:false,why:(e&&e.name==='AbortError'&&opt&&opt.body)?'הפרסום לא הספיק':'אין גשר'}}}
  async function gesherAlive(){const r=await gesher('/shalom');GOK=!!r.ok;return GOK}
  function pubDraw(){const e=$('#edpub');if(!e)return;
    const np=ED.filter(x=>!x.pub).length;
    e.textContent=PUBMSG||(np?'· '+np+' ממתינים לפרסום':(ED.length?'· פורסם':''))
      +(GOK===false&&!ghTok()?' · מפרסם כשהמחשב הראשי יידלק':'');
    e.className='edpub'+(PUBMSG.indexOf('לא פורסם')===0?' bad':'')}
  function pubSoon(){clearTimeout(PUBT);PUBT=setTimeout(()=>pubNow(0),2500)}
  function b64(s){return btoa(unescape(encodeURIComponent(s)))}
  function pubBody(){
    return JSON.stringify({v:1,slug:SLUG,masechet:D.masechet,
      when:new Date().toISOString(),sty:D.sty,
      edits:ED.filter(e=>!e.lost).map(e=>e.op==='struct'
        ? {op:'struct',kind:e.kind,texts:e.texts,res:e.res,resT:e.resT,
           daf:e.daf,t:e.t}
        : {k:e.k,was:e.was,now:e.now,wasH:e.wasH,nowH:e.nowH,
           ps:e.ps,psw:e.psw,wasP:e.wasP,daf:e.daf,ctx:e.ctx,t:e.t})},null,1)}
  async function pubNow(loud){
    clearTimeout(PUBT);
    if(PUBBUSY)return;
    const body=pubBody();
    /* אותה רשימה בדיוק אינה נדחפת פעמיים. בלי השער הזה נרשמה עשירייה
       של הפניות ריקות למאגר בתוך דקות, וכל אחת מהן הפעילה בנייה. */
    const sig=body.replace(/"when":"[^"]*",?/,'');
    if(!loud&&sig===PUBLAST)return;
    PUBBUSY=true;PUBMSG='מפרסם…';pubDraw();
    /* הדרך הראשונה: הגשר שבמחשב. אין בה מפתח ואין בה הכנה. */
    const g=await gesher('/edits',{method:'POST',
      headers:{'Content-Type':'application/json'},body:body});
    GOK=g.ok||g.why!=='אין גשר';
    if(g.ok){ED.forEach(e=>e.pub=1);saveED();PUBLAST=sig;
      PUBMSG='· פורסם '+new Date().toLocaleTimeString('he-IL').slice(0,5)+
             ' · יופיע לכל הלומדים בתוך כשתי דקות';
      PUBBUSY=false;pubDraw();drawEd();return}
    const t=ghTok();
    if(!t){
      PUBBUSY=false;
      PUBMSG=(g.why==='אין גשר')
        ? (GESHER===null
           ? 'לא פורסם: התיקון שמור כאן. לפרסום מיידי פתח את הקיצור "לאוקמי גירסא - עריכה" שבשולחן העבודה'
           : 'לא פורסם: המחשב הראשי אינו פועל. התיקון שמור כאן, ויעלה מעצמו כשיידלק')
        : 'לא פורסם: '+g.why+' · התיקון שמור כאן וינוסה שוב';
      pubDraw();drawEd();
      if(loud&&g.why==='אין גשר')edKey();
      PUBT=setTimeout(()=>pubNow(0),45000);
      return}
    const url='https://api.github.com/repos/'+REPO+'/contents/'+EDPATH;
    const H={Authorization:'Bearer '+t,Accept:'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'};
    let ok=false, why='';
    try{
      for(let n=0;n<3&&!ok;n++){
        let sha=null;
        const g=await fetch(url+'?ref=main&z='+Date.now(),{headers:H,cache:'no-store'});
        if(g.status===200){const j=await g.json();sha=j.sha}
        else if(g.status===404)sha=null;
        else if(g.status===401||g.status===403){why='המפתח נדחה';break}
        else {why='שגיאה '+g.status;break}
        const pl={message:'תיקוני '+D.masechet+' מן האתר',content:b64(body),branch:'main'};
        if(sha)pl.sha=sha;
        const r=await fetch(url,{method:'PUT',headers:H,body:JSON.stringify(pl)});
        if(r.ok)ok=true;
        else if(r.status===409||r.status===422)why='התנגשות - מנסה שוב';
        else if(r.status===401||r.status===403){why='למפתח אין הרשאת כתיבה';break}
        else {why='שגיאה '+r.status;break}
      }
    }catch(e){why='אין חיבור'}
    if(ok){ED.forEach(e=>e.pub=1);saveED();PUBLAST=sig;
      PUBMSG='· פורסם '+new Date().toLocaleTimeString('he-IL').slice(0,5)+
             ' · יופיע לכל הלומדים בתוך כשתי דקות';}
    else PUBMSG='לא פורסם: '+why+' · העריכות שמורות במכשיר וינוסו שוב';
    PUBBUSY=false;pubDraw();drawEd();
    if(!ok&&ED.some(e=>!e.pub))PUBT=setTimeout(()=>pubNow(0),45000)}
  function edKey(){
    const cur=ghTok();
    const msg='מפתח פרסום למכשיר הזה.\n\n'+
      'במחשב הראשי אין צורך במפתח: התיקונים עולים מאליהם.\n'+
      'המפתח נחוץ רק במכשיר אחר, כשהמחשב הראשי כבוי.\n\n'+
      'אם יש לך מפתח - הדבק אותו כאן. אם לא, אפשר להשאיר ריק:\n'+
      'התיקון נשמר במכשיר ויעלה מעצמו כשהמחשב יידלק.';
    const v=prompt(msg,cur);
    if(v===null)return;
    try{if(v.trim())localStorage.setItem(TKEY,v.trim());else localStorage.removeItem(TKEY)}catch(e){}
    if(v.trim()){try{localStorage.setItem(AKEY,'1')}catch(e){}PUBMSG='';pubNow(0)}
    else{PUBMSG='';pubDraw()}}

  /* הקלדה: Enter חסום כדי שלא תיווצר פסקה חדשה, והדבקה נכנסת כטקסט נקי */
  document.addEventListener('keydown',e=>{
    if(e.ctrlKey&&e.altKey&&(e.key==='e'||e.key==='E'||e.key==='ק')){askAdmin();e.preventDefault();return}
    if(!EDIT||!e.target.isContentEditable)return;
    const el=e.target.closest('[contenteditable="true"]');
    if(!el)return;
    /* Enter מפצל פסקה לשתיים באותו סגנון. בכותרת ובחלון אין פיצול:
       הם פסקה אחת בוורד מעצם טיבם. */
    if(e.key==='Enter'&&!e.shiftKey){
      e.preventDefault();
      capture(el);
      if(el.tagName!=='P'){flash('כאן אין פיצול: זו כותרת, והיא פסקה אחת');return}
      splitAtCaret(el);
      return}
    /* מחיקה אחורה בתו הראשון של פסקה מאחדת אותה עם הקודמת */
    if(e.key==='Backspace'&&el.tagName==='P'&&atStart(el)){
      e.preventDefault();
      capture(el);
      mergeBack(el);
      return}
  });
  document.addEventListener('paste',e=>{
    if(!EDIT||!e.target.isContentEditable)return;
    e.preventDefault();
    const t=(e.clipboardData||window.clipboardData).getData('text/plain').replace(/\s+/g,' ');
    document.execCommand('insertText',false,t)});
  document.addEventListener('focusin',edFocus);
  document.addEventListener('focusout',edBlur);
  document.addEventListener('input',e=>{const el=e.target.closest&&e.target.closest('[contenteditable="true"]');
    if(EDIT&&el)captureSoon(el)});
  document.addEventListener('selectionchange',()=>{if(EDIT)styLater()});
  document.addEventListener('mousedown',e=>{
    if($('#stybar')&&e.target.closest&&!e.target.closest('#stybar')&&!e.target.closest('[contenteditable="true"]'))hideSty()});
  if(location.hash.indexOf('admin')>-1){try{localStorage.setItem(AKEY,'1')}catch(e){}}
  /* דף שמוגש מן הגשר רץ במחשב של בעל הפרויקט עצמו, ואין שום טעם
     לשאול בו מילת מנהל: מי שהגיע לכאן כבר עבר את כל מה שמילה כזאת
     אמורה לבדוק. */
  if(ONGESHER){try{localStorage.setItem(AKEY,'1')}catch(e){}}
  if(!ED.some(e=>!e.pub))PUBLAST=pubBody().replace(/"when":"[^"]*",?/,'');
  else setTimeout(()=>pubNow(0),3000);

  /* =================== נקודת הקליטה: הצעות, תור המנהל, סנכרון ===================
     האתר סטטי, ולכן עד כאן הצעת תיקון נשמרה רק בדפדפן של המציע ואיש לא
     ראה אותה. מעתה יש נקודת קליטה אחת, קטנה וחינמית (Cloudflare Worker,
     worker/leokmei-suggest), נפרדת לגמרי מממלכת הזוהר:
       - כל לומד: "הצע תיקון" שולח לשם. אין רשת - נשמר במכשיר ונשלח
         בטעינה הבאה. אין מייל, אין העתקה, אין הורדה.
       - המנהל: תג "הצעות ממתינות (N)" בסרגל, פאנל שבו כל הצעה על
         השורה שלה, ושלושה כפתורים: קבל / ערוך וקבל / דחה. "קבל" הופך
         את ההצעה לעריכת מנהל רגילה - מוחלת מיד, ונקלטת לוורד בלילה
         בשם "הצעה מהאתר - <שם המציע>".
       - עריכות המנהר נשמרות גם בנקודת הקליטה, ולכן מה שנערך בטאבלט
         נראה במחשב. הקליטה הלילית לוורד קוראת משם.
       - כל לומד מקבל את העריכות שהתקבלו ישר משם בטעינת הדף (בלי
         שמות), עוד לפני שהבנייה מן הוורד הגיעה.
     קריאת התור ושינוי סטטוס דורשים מפתח סודי שנשמר ב-Worker בלבד;
     המנהל מזין אותו פעם אחת בכל מכשיר. מילת המנהל נשארת שער נוחות
     להצגת כפתור העריכה בלבד. */
  const SUGGEST_API='https://leokmei-suggest.m7654301.workers.dev';
  const ADMKEY='lg-adm', SGOUT='lg-sgout-'+SLUG, TKEY2='lg-tomb-'+SLUG;
  function admKey(){try{return localStorage.getItem(ADMKEY)||''}catch(e){return ''}}
  async function api(path,opt){
    const o=Object.assign({headers:{}},opt||{});
    o.headers['content-type']='application/json; charset=utf-8';
    const k=admKey();if(k)o.headers['x-admin-key']=k;
    const r=await fetch(SUGGEST_API+path,o);
    let j=null;try{j=await r.json()}catch(e){}
    if(!r.ok||!j||!j.ok)throw new Error((j&&j.error)||('שגיאה '+r.status));
    return j}
  function toast(msg,ms){let h=$('#toast');
    if(!h){h=document.createElement('div');h.className='hint';h.id='toast';document.body.appendChild(h)}
    h.textContent=msg;clearTimeout(h.__t);h.__t=setTimeout(()=>h.remove(),ms||3200)}

  /* ---- המבקר: הצע תיקון ---- */
  let SG=[]; try{SG=JSON.parse(localStorage.getItem(SGOUT)||'[]')}catch(e){SG=[]}
  let PICK=false, SGBUSY=false;
  function saveSG(){try{localStorage.setItem(SGOUT,JSON.stringify(SG))}catch(e){}}
  function unitOf(el){const r=el.closest('.row');if(!r)return{daf:'',uid:''};
    let x=r,daf='';while(x){const d=x.querySelector('.dafmark');if(d){daf=d.dataset.daf||d.textContent;break}x=x.previousElementSibling}
    return {daf,uid:(r.id||'').replace(/^u/,'')}}
  function suggest(){
    const s=window.getSelection();
    const t=s&&String(s).trim();
    if(t&&s.rangeCount&&$('#flow').contains(s.getRangeAt(0).commonAncestorContainer)){
      let el=(s.getRangeAt(0).commonAncestorContainer.nodeType===1
                ?s.getRangeAt(0).commonAncestorContainer
                :s.getRangeAt(0).commonAncestorContainer.parentElement);
      el=(el.closest&&el.closest('[data-ek]'))||el;
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
    e.preventDefault();setPick(false);openSg(txtOf(el).trim(),el)});
  function openSg(text,el){
    const u=unitOf(el);
    const m=document.createElement('div');m.className='modal';m.id='sgm';
    m.innerHTML='<div class="box"><h3>הצעת תיקון</h3>'+
      '<div class="ref">'+esc(D.masechet)+(u.daf?' · דף '+esc(u.daf):'')+'</div>'+
      '<div class="sel">'+esc(text)+'</div>'+
      '<label for="sgn">הנוסח המוצע, או ההערה</label><textarea id="sgn" maxlength="1900" placeholder="כתוב כאן את הנוסח המוצע במקום הקטע, או הערה"></textarea>'+
      '<label for="sgw">שמך (לא חובה)</label><input id="sgw" maxlength="80" value="'+esc(localStorage.getItem('lg-sg-name')||'')+'">'+
      '<input id="sgh" name="website" tabindex="-1" autocomplete="off" style="position:absolute;left:-9999px;top:-9999px;opacity:0;height:0" aria-hidden="true">'+
      '<div class="btns"><button class="go" id="sgok">שלח לעורך</button>'+
      '<button onclick="closeSg()">ביטול</button></div></div>';
    document.body.appendChild(m);
    m.addEventListener('click',e=>{if(e.target===m)closeSg()});
    $('#sgn').focus();
    $('#sgok').onclick=()=>{
      const note=$('#sgn').value.trim();
      if(!note){alert('כתוב מה להציע.');return}
      if(/(https?:\/\/|www\.)/i.test(note)){alert('הצעה שיש בה קישור אינה מתקבלת.');return}
      const name=$('#sgw').value.trim();
      try{localStorage.setItem('lg-sg-name',name)}catch(e){}
      const rec={slug:SLUG,masechet:D.masechet,daf:u.daf,uid:u.uid,k:(el&&el.dataset&&el.dataset.ek)||'',
                 ctx:ctxOf(el),was:text,note,name,hp:$('#sgh').value,t:Date.now(),sent:0};
      SG.push(rec);saveSG();closeSg();sgSend()};
  }
  function closeSg(){const m=$('#sgm');if(m)m.remove()}
  async function sgSend(){
    if(SGBUSY)return;SGBUSY=true;let ok=0,fail=0,why='';
    for(const g of SG){
      if(g.sent)continue;
      try{const j=await api('/suggest',{method:'POST',body:JSON.stringify(g)});g.sent=1;g.id=j.id;ok++}
      catch(e){why=e.message||'';if(/קישור|נדחה|מדי/.test(why)){g.sent=1;g.bad=why}else fail++}
    }
    saveSG();SGBUSY=false;
    if(ok)toast('ההצעה נשלחה לעורך. תודה רבה.');
    else if(fail)toast('אין חיבור כרגע. ההצעה נשמרה במכשיר ותישלח בטעינה הבאה.',4500);
    else if(why)toast(why,4500);
    drawSg()}
  function drawSg(){const box=$('#sgb');if(!box)return;
    let h='';
    SG.forEach((g,i)=>{h+='<div class="sgrow"><small>'+esc(g.daf||'')+' · '+new Date(g.t).toLocaleDateString('he-IL')+
      ' · '+(g.bad?'<span style="color:#a83c2f">לא התקבלה: '+esc(g.bad)+'</span>':(g.sent?'נשלחה לעורך':'ממתינה לשליחה'))+'</small> <q>'+esc((g.was||'').slice(0,80))+'</q>'+
      '<b>'+esc(g.note)+'</b></div>'});
    if(!SG.length)h='<div class="edsum">עדיין לא הצעת דבר. סמן טקסט בדף, ולחץ "הצע תיקון".</div>';
    else h+='<div style="margin-top:12px"><button onclick="sgClear()">נקה את הרשימה במכשיר</button></div>';
    box.innerHTML=h}
  function sgClear(){if(SG.some(g=>!g.sent)&&!confirm('יש הצעה שטרם נשלחה. למחוק בכל זאת?'))return;SG=[];saveSG();drawSg()}
  document.addEventListener('keydown',e=>{if(e.key==='Escape'){if(PICK)setPick(false);closeSg()}});
  if(SG.some(g=>!g.sent))setTimeout(sgSend,2500);

  /* ---- החלפת קטע בתוך HTML, בלי לאבד את סגנונות התו ---- */
  function replaceInHTML(h,was,now){
    const d=document.createElement('div');d.innerHTML=h;
    const w=document.createTreeWalker(d,NodeFilter.SHOW_TEXT);const ns=[];let n;
    while(n=w.nextNode())ns.push(n);
    const full=ns.map(x=>x.nodeValue).join('');
    const k=full.indexOf(was);if(k<0)return null;
    let pos=0,first=true;
    for(const x of ns){const L=x.nodeValue.length,a=pos,b=pos+L;pos=b;
      if(b<=k||a>=k+was.length)continue;
      const lo=Math.max(k-a,0),hi=Math.min(k+was.length-a,L);
      x.nodeValue=x.nodeValue.slice(0,lo)+(first?now:'')+x.nodeValue.slice(hi);first=false}
    d.normalize();return d.innerHTML}

  /* ---- המנהל: תור ההצעות ---- */
  let QQ=[],QQTOT=0,QQERR='',QQTIMER=null;
  function slotsFull(){const out=[];
    D.pages.forEach((p,pi)=>p.units.forEach(u=>{
      const add=(kk,h,c)=>out.push({pi,daf:p.daf,id:u.id,k:'u'+u.id+kk,h,c:c||'',t:plain(h)});
      if(u.k==='u'){ if(u.a)add('.0',u.a);
        u.l.forEach((l,i)=>add('.'+(i+1),l[1],l[0])); }
      else if(u.k==='m'){ u.l.forEach((l,i)=>add('.'+(i+1),l[1],l[0])); }
      else if(u.k==='dh'||u.k==='nose'){ add('.0',u.a); }
      if(u.k!=='u'&&u.w)add('.w',u.w);
    }));
    return out}
  /* מאתר את השורה של הצעה: מפתח המקום תחילה, אחר כך היחידה, ולבסוף
     ההקשר - ורק התאמה אחת ויחידה. לא אותרה - לעולם אינה נתלית בשורה
     אחרת; היא עולה ל"הצעות שלא אותרו". */
  function sqLocate(g,S){
    const has=s=>s.t.indexOf(g.was)>-1||nonik(s.t).indexOf(nonik(g.was))>-1;
    if(g.k){const s=S.find(x=>x.k===g.k);if(s&&has(s))return s}
    if(g.uid){const c=S.filter(x=>String(x.id)===String(g.uid)&&has(x));if(c.length===1)return c[0]}
    const k0=dafKey(g.daf);
    let c=S.filter(x=>{const k=dafKey(x.daf);return (k0===null||k===null||Math.abs(k-k0)<=1)&&has(x)});
    if(c.length>1&&g.ctx){const i=x=>S.indexOf(x);
      c=c.filter(x=>{const p=S[i(x)-1],n=S[i(x)+1];
        return (!g.ctx.b||(p&&p.t.slice(-40)===g.ctx.b))&&(!g.ctx.a||(n&&n.t.slice(0,40)===g.ctx.a))})}
    return c.length===1?c[0]:null}
  async function queueLoad(){
    if(!isAdmin()||!admKey()){sqBadge();return}
    try{const j=await api('/queue?slug='+SLUG);QQ=j.items||[];QQTOT=j.total||0;QQERR=''}
    catch(e){QQERR=e.message||'שגיאה'}
    sqBadge();sqMark();
    if($('#sgq')&&$('#sgq').classList.contains('open'))drawSq()}
  function sqBadge(){const b=$('#sqbtn');if(!b)return;
    if(!isAdmin()){b.style.display='none';return}
    b.style.display='';
    b.textContent=admKey()?('הצעות ממתינות ('+QQ.length+(QQTOT>QQ.length?' · '+QQTOT+' בכל המסכתות':'')+')'):'הצעות ממתינות - הזן מפתח';
    b.classList.toggle('on',QQ.length>0)}
  function sqMark(){const f=$('#flow');if(!f)return;
    f.querySelectorAll('.sgp').forEach(x=>x.classList.remove('sgp'));
    if(!isAdmin()||!QQ.length)return;
    const S=slotsFull();
    for(const g of QQ){const s=sqLocate(g,S);if(!s)continue;
      const el=f.querySelector('[data-ek="'+s.k+'"]');if(el)el.classList.add('sgp')}}
  function sqOpen(){if(!admKey()){admKeyAsk();return}panel('sgq');drawSq();queueLoad()}
  function drawSq(){const box=$('#sgqb');if(!box)return;
    const S=slotsFull();let h='';
    if(QQERR)h+='<div class="edsum" style="color:#a83c2f">לא ניתן לקרוא את התור: '+esc(QQERR)+'</div>';
    const lost=[],ok=[];
    QQ.forEach(g=>{const s=sqLocate(g,S);(s?ok:lost).push([g,s])});
    if(lost.length){h+='<h3>הצעות שלא אותרו</h3>';
      lost.forEach(([g])=>{h+=sqRow(g,null)})}
    h+='<h3>'+ok.length+' הצעות ממתינות ב'+esc(D.masechet)+'</h3>';
    if(!ok.length&&!lost.length)h+='<div class="edsum">אין הצעות ממתינות.</div>';
    ok.forEach(([g,s])=>{h+=sqRow(g,s)});
    box.innerHTML=h}
  function sqRow(g,s){
    const when=new Date(g.t).toLocaleString('he-IL');
    const ctxH=s?esc(s.t).replace(esc(g.was),'<mark>'+esc(g.was)+'</mark>'):'';
    return '<div class="sgrow'+(s?'':' edlost')+'" data-id="'+esc(g.id)+'">'+
      '<small>'+esc(g.daf||'')+(g.name?' · '+esc(g.name):' · בלי שם')+' · '+when+'</small>'+
      (s?'<div class="sqctx">'+ctxH+'</div>':'<q>'+esc(g.was.slice(0,120))+'</q><small>לא אותר בקובץ הנוכחי</small>')+
      '<b>'+esc(g.note)+'</b>'+
      (s?'<button onclick="sqDecide(\''+esc(g.id)+'\',\'accepted\')">קבל</button>'+
         '<button onclick="sqDecide(\''+esc(g.id)+'\',\'edited\')">ערוך וקבל</button>'+
         '<button onclick="sqJump(\''+esc(g.id)+'\')">הצג</button>':'')+
      '<button onclick="sqDecide(\''+esc(g.id)+'\',\'rejected\')">דחה</button></div>'}
  function sqJump(id){const g=QQ.find(x=>x.id===id);if(!g)return;const s=sqLocate(g,slotsFull());if(s)jump(s.pi,s.id)}
  async function sqDecide(id,st){
    const g=QQ.find(x=>x.id===id);if(!g)return;
    let edit=null,now='';
    if(st!=='rejected'){
      const s=sqLocate(g,slotsFull());
      if(!s){alert('ההצעה לא אותרה בקובץ הנוכחי ואי אפשר להחיל אותה.');return}
      now=g.note;
      if(st==='edited'){const v=prompt('הנוסח שייכנס במקום הקטע המסומן:',g.note);if(v===null)return;now=v.trim();if(!now)return}
      /* נקודת המוצא היא הנוסח שעל המסך: אם השורה כבר נערכה, ההצעה
         חלה על הנוסח המתוקן, ו"הנוסח שהיה" נשאר זה שבוורד. */
      const old=ED.find(x=>x.k===s.k);
      const curT=old?old.now:s.t, curH=old?(old.nowH!==undefined?old.nowH:esc(old.now)):s.h;
      const wasT=old?old.was:s.t, wasH=old?(old.wasH!==undefined?old.wasH:s.h):s.h;
      if(curT.indexOf(g.was)<0){alert('הקטע שהוצע עליו התיקון כבר אינו בשורה הזאת.');return}
      const nowH=replaceInHTML(curH,g.was,now);
      const nowT=curT.replace(g.was,now);
      const cls=(s.c||'').split(' ').filter(c=>PCLS.indexOf(c)>-1).join(' ');
      edit={k:s.k,was:wasT,now:nowT,wasH,nowH:nowH!==null?nowH:esc(nowT),wasP:old?old.wasP:cls,
            daf:s.daf,ctx:{b:'',a:''},t:Date.now(),pub:0,by:'הצעה מהאתר'+(g.name?' - '+g.name:''),sg:g.id};
      if(old&&old.ps!==undefined){edit.ps=old.ps;edit.psw=old.psw}
      if(old)ED=ED.filter(x=>x!==old);
      ED.push(edit);saveED();
    }
    try{await api('/decide',{method:'POST',body:JSON.stringify({id,st,now,edit,sty:D.sty})})}
    catch(e){alert('ההכרעה לא נרשמה: '+e.message);return}
    QQ=QQ.filter(x=>x.id!==id);QQTOT=Math.max(0,QQTOT-1);
    if(edit){render(cur);drawEd();pubSoon();syncSoon();toast('התיקון הוחל.')}
    else toast('ההצעה נדחתה ועברה לארכיון.');
    sqBadge();drawSq()}
  function admKeyAsk(){
    const v=prompt('מפתח המנהל של לאוקמי גירסא.\n\nהדבק כאן את המפתח. הוא נשמר רק בדפדפן הזה.\nלהסרה - מחק את התוכן ולחץ אישור.',admKey());
    if(v===null)return;
    try{if(v.trim())localStorage.setItem(ADMKEY,v.trim());else localStorage.removeItem(ADMKEY)}catch(e){}
    if(v.trim()){try{localStorage.setItem(AKEY,'1')}catch(e){}netInit(true)}
    sqBadge()}

  /* ---- סנכרון עריכות המנהל בין מכשירים ---- */
  let TOMB=[]; try{TOMB=JSON.parse(localStorage.getItem(TKEY2)||'[]')}catch(e){TOMB=[]}
  let SYNCT=null,SYNCBUSY=false,EDRO=false;
  function tomb(k){TOMB.push({k,del:1,t:Date.now()});TOMB=TOMB.slice(-300);try{localStorage.setItem(TKEY2,JSON.stringify(TOMB))}catch(e){}}
  /* שינוי מבנה (פיצול/איחוי) אין לו מפתח מקום, ומפתחו לסנכרון נגזר מזמנו */
  function edKeys(){ED.forEach(e=>{if(e.op==='struct'&&!e.k)e.k='s'+e.t})}
  function edOut(){edKeys();return ED.filter(e=>!e.lost).map(e=>e.op==='struct'
      ? {k:e.k,op:'struct',kind:e.kind,texts:e.texts,res:e.res,resT:e.resT,daf:e.daf,t:e.t,by:e.by}
      : {k:e.k,was:e.was,now:e.now,wasH:e.wasH,nowH:e.nowH,
         ps:e.ps,psw:e.psw,wasP:e.wasP,daf:e.daf,ctx:e.ctx,t:e.t,by:e.by,sg:e.sg}).concat(TOMB)}
  function mergeIn(list){edKeys();let changed=false;const by={};ED.forEach(e=>by[e.k]=e);
    for(const e of list||[]){const o=by[e.k];
      if(e.del){if(o&&(o.t||0)<=(e.t||0)){ED=ED.filter(x=>x!==o);delete by[e.k];changed=true}continue}
      if(!o||(o.t||0)<(e.t||0)){const n=Object.assign({pub:o?o.pub:1},e);if(o)ED[ED.indexOf(o)]=n;else ED.push(n);by[e.k]=n;changed=true}
      else if(e.ing&&!o.ing){o.ing=e.ing}}
    if(changed)saveED();return changed}
  function syncSoon(){clearTimeout(SYNCT);SYNCT=setTimeout(syncNow,1500)}
  async function syncNow(){
    if(!isAdmin()||!admKey()||SYNCBUSY)return;SYNCBUSY=true;
    try{const j=await api('/edits',{method:'PUT',body:JSON.stringify({slug:SLUG,edits:edOut(),sty:D.sty})});
      if(mergeIn(j.doc&&j.doc.edits)){if(typeof applyStruct==='function')applyStruct();render(cur)}}
    catch(e){}
    SYNCBUSY=false}
  /* ---- בטעינה: המנהל מושך את התור ואת העריכות; הלומד מקבל את מה
     שהתקבל ---- */
  async function netInit(force){
    if(isAdmin()&&admKey()){
      await syncNow();queueLoad();
      clearInterval(QQTIMER);QQTIMER=setInterval(queueLoad,60000);
      return}
    if(isAdmin())return;
    try{const j=await api('/live?slug='+SLUG);const L=(j.doc&&j.doc.edits)||[];
      if(L.length){EDRO=true;ED=L.map(e=>Object.assign({pub:1},e));
        if(typeof applyStruct==='function')applyStruct();render(cur)}}
    catch(e){}}

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

  /* =================== תצוגת ספר (משימה י) ===================
     מנוע עימוד: ממלא גיליון עד שהיחידה הבאה אינה נכנסת, ואינו שובר
     יחידה בין גיליונות.

     המדידה אינה נעשית בדף עצמו. פריסה מחדש של מכולת-טורים עולה
     מילישניות רבות לכל מדידה, ומאות יחידות היו מקפיאות את הדף
     לשניות. לכן נבנה סרגל מבודד באותו רוחב ובאותם class - כולל של
     .main, שאחרת הגופן שונה - וכל היחידות נכתבות אליו בבת אחת.
     ואז, בפריסה אחת, נקראים offsetTop ו-offsetHeight של כולן. זה
     ההבדל בין פריסה אחת ובין מאות.

     הסרגל עצמו ב-position:fixed וב-visibility:hidden ולא ב-
     left:-99999px, שמתח בעבר את רוחב המסמך למאה אלף פיקסלים. */
  /* #book בכתובת מדליק את תצוגת הספר, כדי שאפשר יהיה לשלוח קישור
     ישיר אליה וגם להדפיס אותה בלא לגעת בהעדפה שבמכשיר. */
  /* ז - הניקוד של המשניות. ברירת המחדל: מנוקד. */
  let NK=localStorage.getItem('lg-nk')!=='0';
  function nikud(){NK=!NK;localStorage.setItem('lg-nk',NK?'1':'0');
    const b=$('#nkbtn');if(b)b.classList.toggle('on',NK);render(cur)}
  let BOOK=localStorage.getItem('lg-book')==='1'||location.hash.indexOf('book')>-1;
  let SHEETS=+localStorage.getItem('lg-sheets')||2;
  function sheetsNow(){return innerWidth<900?1:SHEETS}
  function measureRows(html){
    let g=$('#gauge');
    if(!g){g=document.createElement('div');g.id='gauge';document.body.appendChild(g)}
    g.className='flow book';
    g.style.cssText+=';display:block;height:auto;width:auto;padding:0;';
    g.innerHTML='<div class="sheet" style="height:auto;box-shadow:none;border:0;padding:0">'+
                '<div class="shbody">'+html+'</div></div>';
    const body=g.querySelector('.shbody');
    const rows=[...body.children];
    /* פריסה אחת בלבד: כל הקריאות שאחריה אינן מחייבות פריסה נוספת.
       לכל שורה נמדד גם מקומן של הפסקאות שבתוכה ומספר שורות הטקסט שלה,
       כדי שהעימוד יוכל לחתוך יחידה ארוכה בין פסקאות ולדעת אם לכותרת
       יש די טקסט אחריה. */
    const box=body.getBoundingClientRect();
    const out=rows.map(r=>{
      const b=r.getBoundingClientRect();
      /* גובה המלבן אינו כולל את המרווחים האנכיים, ולכן סכום הגבהים היה
         קטן מן הגובה בפועל והעמוד גלש. הגובה נגזר מן ההפרש בין ראשי
         השורות, שכולל את המרווח שביניהן. */
      const main=r.querySelector(':scope > .main');
      const ps=main?[...main.querySelectorAll(':scope > p')]:[];
      const lh=lhOf(r);
      return {h:b.height, top:b.top-box.top,
              lines:main?Math.max(main.textContent.trim()?1:0,Math.round(main.getBoundingClientRect().height/lh)):0,
              pt:ps.map(x=>x.getBoundingClientRect().top-b.top)};});
    for(let i=0;i<out.length;i++){
      out[i].h=(i+1<out.length?out[i+1].top:box.height)-out[i].top;
      out[i].el=rows[i];out[i].box=box.top;}
    /* הסרגל אינו מתרוקן כאן: החיתוך בין שורות (ג) זקוק לאלמנטים
       המדודים. הוא מתרוקן בסוף העימוד. */
    return out}
  function gaugeClear(){const g=$('#gauge');if(g)g.innerHTML=''}
  /* ---- ג: חיתוך פסקה בין שורות ----
     הכרעת בעל הפרויקט: כמו בוורד. פסקה ארוכה רשאית להישבר בין עמודים,
     רק בין שורות, ולפחות שתי שורות בכל צד; והכותרת נשארת עם שתי
     השורות הראשונות של הפסקה. מקומן של השורות נמדד בסרגל, ונקודת
     החיתוך היא תחילת השורה הראשונה שאינה נכנסת - נמצאת בחיפוש בינארי
     על היסט התו, ולא בניחוש. שני החלקים נבנים ב-Range.cloneContents,
     ולכן סגנון תו שנחצה נסגר ונפתח מחדש כדין. */
  function lineTops(p){
    const w=document.createTreeWalker(p,NodeFilter.SHOW_TEXT);const ns=[];let n;
    while(n=w.nextNode())if(n.nodeValue.trim())ns.push(n);
    const r=document.createRange();const raw=[];
    for(const x of ns){r.selectNodeContents(x);for(const b of r.getClientRects())if(b.height>0.5&&b.width>0.05)raw.push(b)}
    raw.sort((a,b)=>a.top-b.top);
    const L=[];for(const b of raw){const last=L[L.length-1];
      if(last&&Math.abs(b.top-last.top)<=Math.max(2,last.h*0.4)){last.top=Math.min(last.top,b.top);last.bottom=Math.max(last.bottom,b.bottom);last.h=last.bottom-last.top}
      else L.push({top:b.top,bottom:b.bottom,h:b.bottom-b.top})}
    return {ns,L}}
  function lineSplit(pEl,rowTop,room){
    if(!pEl||pEl.classList.contains('hatz'))return null;
    const {ns,L}=lineTops(pEl);
    if(L.length<4)return null;
    let nfit=0;for(const l of L){if(l.bottom-rowTop<=room+0.5)nfit++;else break}
    if(nfit<2||L.length-nfit<2)return null;
    const lineTop=L[nfit].top;
    /* היסט התו הראשון שראשו בשורה שאינה נכנסת */
    const lens=ns.map(x=>x.nodeValue.length);const total=lens.reduce((a,b)=>a+b,0);
    const r=document.createRange();
    function at(off){let o=off;for(let i=0;i<ns.length;i++){if(o<lens[i]){return [ns[i],o]}o-=lens[i]}return [ns[ns.length-1],lens[lens.length-1]]}
    function topAt(off){const [nd,o]=at(off);if(o>=nd.nodeValue.length)return Infinity;
      r.setStart(nd,o);r.setEnd(nd,o+1);const b=r.getBoundingClientRect();return b.height?b.top:null}
    let lo=0,hi=total-1;
    while(lo<hi){const mid=(lo+hi)>>1;const t=topAt(mid);
      if(t===null||t<lineTop-1)lo=mid+1;else hi=mid}
    let off=lo;
    /* רווח בתפר אינו נשאר בראש החלק השני */
    const [nd0,o0]=at(off);
    const first=nd0.nodeValue.charAt(o0);
    if(!first.trim()){off++}
    if(off<=0||off>=total)return null;
    const [na,oa]=at(off);
    const ra=document.createRange();ra.setStart(pEl,0);ra.setEnd(na,oa);
    const rb=document.createRange();rb.setStart(na,oa);rb.setEnd(pEl,pEl.childNodes.length);
    const da=document.createElement('div');da.appendChild(ra.cloneContents());
    const db=document.createElement('div');db.appendChild(rb.cloneContents());
    da.querySelectorAll('.srcb').forEach(x=>x.remove());db.querySelectorAll('.srcb').forEach(x=>x.remove());
    const aH=lineTop-rowTop;
    return {a:da.innerHTML.replace(/\s+$/,''),b:db.innerHTML.replace(/^\s+/,''),aH,aLines:nfit,bLines:L.length-nfit}}
  function noMargin(cls,which){return (cls||'').split(' ').filter(c=>!(c.length===2&&c[0]===which&&/\d/.test(c[1]))).join(' ')}

  /* ---- ד4: עימוד זהיר ----
     כותרת לעולם אינה הפריט האחרון בעמוד, ציון דף אינו עומד לבדו
     בתחתיתו, פרק פותח עמוד חדש, ויחידה ארוכה מחצי עמוד רשאית להתחלק -
     אך רק בין פסקאות, ועם לפחות שתי שורות בכל צד. הכללים פועלים על
     מדידה בפועל ולא על הערכה. */
  /* כותרת שהתוכן שלה בא אחריה. 'הדרן' אינו כאן: הוא סיום פרק ואין
     אחריו דבר. 'פרק שם' ו'דפים בפרק' שייכים לגוש פתיחת הפרק, וגוש זה
     נשמר יחד ממילא מפני ש'פרק' פותח עמוד חדש. */
  /* א8: גם החציצה נצמדת לפסקה שאחריה ואינה נשארת לבדה בתחתית העמוד */
  const HEADK=['nose','dh','perek-num','hatz'];
  const isHead=u=>HEADK.indexOf(u.k)>-1||(!u.lines&&u.daf);
  function paginate(units){
    const fs=parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--fs'))||18;
    /* גובה הטקסט נטו בעמוד: 115 מ"מ, והכותרת הרצה כבר מחוץ לו */
    const H=39.79*fs;
    const m=measureRows(units.map(u=>u.html).join(''));
    units.forEach((u,i)=>{u.h=m[i]?m[i].h:0;u.lines=m[i]?m[i].lines:0;u.pt=m[i]?m[i].pt:[];u.el=m[i]?m[i].el:null});

    const sheets=[];let cur=[],h=0;
    const push=()=>{if(cur.length){sheets.push(cur);cur=[];h=0}};
    for(let i=0;i<units.length;i++){
      const u=units[i], nx=units[i+1];
      /* ד. פרק חדש פותח עמוד חדש, כמו sectPr בוורד */
      if(u.k==='perek-num'&&cur.length)push();
      /* א+ג. כותרת, או ציון דף שאין תחתיו טקסט, אינם נשארים לבדם בתחתית
         העמוד: אם אין מקום להם ולשתי שורות מן הבא אחריהם - העמוד נסגר
         כאן, והם יורדים יחד עם התוכן שלהם. הבדיקה לפני החלוקה, ולכן
         אינה מותירה עמוד שחציו ריק. */
      if(cur.length&&nx&&isHead(u)){
        /* הבדיקה אינה "האם יש מקום לשתי שורות" אלא "האם התוכן עצמו
           ייכנס": יחידה אינה נחתכת בידי הדפדפן, ולכן אם היא אינה נכנסת
           כולה ואי אפשר לחתוך אותה כדין - היא תרד לעמוד הבא והכותרת
           תישאר לבדה. שרשרת כותרות (נושא ואחריו ד"ה) נבדקת כגוש אחד. */
        let need=0,j=i;
        while(j<units.length&&isHead(units[j])){need+=units[j].h;j++}
        let got=0;
        for(;j<units.length&&got<2;j++){
          const v=units[j], room=H-h-need;
          /* שורת כותרת אינה "שורת טקסט": כותרת נוספת שנכנסת עדיין
             אינה מספקת את התוכן שהכותרת הראשונה מבטיחה. */
          if(v.h<=room){need+=v.h;if(!isHead(v))got+=v.lines||0;continue}
          const cut=splitAt(v,room);
          if(cut){got+=cut[0].lines||0}
          break;
        }
        if(got<2&&j<units.length)push();
      }
      /* ב. יחידה שאינה נכנסת ביתרת העמוד מתחלקת בין פסקאות, עם שתי
         שורות לפחות בכל צד. אם אי אפשר - העמוד נסגר לפניה. */
      if(cur.length&&h+u.h>H){
        const cut=splitAt(u,H-h);
        if(cut){cur.push(cut[0]);h+=cut[0].h;push();units.splice(i+1,0,cut[1]);continue}
        push();
      }
      /* יחידה ארוכה מעמוד שלם חייבת להתחלק, אחרת היא נחתכת בשקט */
      if(!cur.length&&u.h>H){
        const cut=splitAt(u,H);
        if(cut){cur.push(cut[0]);push();units.splice(i+1,0,cut[1]);continue}
      }
      cur.push(u);h+=u.h;
    }
    push();
    gaugeClear();
    return sheets;
  }
  /* חותך יחידה בגובה 'room': מחזיר שתי יחידות, או null אם אין חיתוך
     חוקי. סמני הצד נשארים עם החלק הראשון.
     ג: קודם ניסיון לחתוך בתוך הפסקה שנחצית, בין שורות, עם שתי שורות
     לפחות בכל צד (כמו בוורד); ואם אי אפשר - בין פסקאות, כמקודם.
     חלק שנחתך פעם ומצריך חיתוך נוסף (יחידה ארוכה משני עמודים) נמדד
     מחדש בסרגל נפרד, ולא מנוחש. */
  function remeasure(u){
    let g=$('#gauge2');
    if(!g){g=document.createElement('div');g.id='gauge2';g.className='flow book';
      g.style.cssText=$('#gauge').style.cssText+';display:block;height:auto;width:auto;padding:0;position:fixed;top:0;left:0;visibility:hidden;pointer-events:none;z-index:-1';
      document.body.appendChild(g)}
    g.innerHTML='<div class="sheet" style="height:auto;box-shadow:none;border:0;padding:0"><div class="shbody">'+u.html+'</div></div>';
    const body=g.querySelector('.shbody');const r=body.firstElementChild;if(!r)return;
    const b=r.getBoundingClientRect();const main=r.querySelector(':scope > .main');
    const ps=main?[...main.querySelectorAll(':scope > p')]:[];
    const lh=lhOf(r);
    u.el=r;u.box=b.top;u.h=body.getBoundingClientRect().height;
    u.lines=main?Math.max(main.textContent.trim()?1:0,Math.round(main.getBoundingClientRect().height/lh)):0;
    u.pt=ps.map(x=>x.getBoundingClientRect().top-b.top)}
  function splitAt(u,room){
    if(!u.u||!u.u.l||!u.pt||!u.pt.length)return null;
    if(!u.el||!u.el.isConnected)remeasure(u);
    const lh=u.h/Math.max(1,u.lines);
    const NKL=(NK&&!EDIT&&u.u.lv)?u.u.lv:u.u.l;
    /* הפסקה שנחצית בגבול העמוד */
    let k=-1;for(let n=0;n<u.pt.length;n++){if(u.pt[n]<room-0.5)k=n;else break}
    if(k<0)return null;
    const rowTop=u.el?u.el.getBoundingClientRect().top:null;
    const ps=u.el?u.el.querySelectorAll(':scope > .main > p'):[];
    const ls=(u.el&&ps[k]&&u.k!=='hatz')?lineSplit(ps[k],rowTop,room):null;
    if(ls){
      const cls=NKL[k][0]||'';
      const la=NKL.slice(0,k).concat([[noMargin(cls,'a'),ls.a]]);
      const lb=[[noMargin(cls,'b'),ls.b]].concat(NKL.slice(k+1));
      const A=Object.assign({},u,{u:Object.assign({},u.u,{l:la,lv:la,ref:undefined})});
      const B=Object.assign({},u,{u:Object.assign({},u.u,{l:lb,lv:lb,a:'',w:''})});
      A.html=unitHTML(A.u,A.daf0,A.pi0); A.h=ls.aH; A.lines=(k?Math.round(u.pt[k]/lh):0)+ls.aLines;
      A.pt=u.pt.slice(0,k+1); A.el=null;
      B.html=unitHTML(B.u,null,null); B.h=u.h-ls.aH; B.lines=Math.max(1,Math.round(B.h/lh));
      B.daf0=null;B.pi0=null;B.split=1;B.el=null;
      B.pt=[0].concat(u.pt.slice(k+1).map(x=>x-ls.aH));
      return [A,B];
    }
    /* חיתוך בין פסקאות: לפני הפסקה k, אם משני צדדיה שתי שורות לפחות.
       אם החלק שאחרי k קצר משתי שורות - מקדימים את החיתוך לפסקה
       קודמת, ולא מוותרים: ויתור השאיר יחידה ארוכה מעמוד שלם כמות
       שהיא, והיא גלשה מן הגיליון (נמדד בהוריות). */
    if(u.u.l.length<2)return null;
    while(k>=1&&(u.pt[k]<2*lh||u.h-u.pt[k]<2*lh))k--;
    if(k<1)return null;
    const A=Object.assign({},u,{u:Object.assign({},u.u,{l:NKL.slice(0,k),lv:NKL.slice(0,k),ref:undefined})});
    const B=Object.assign({},u,{u:Object.assign({},u.u,{l:NKL.slice(k),lv:NKL.slice(k),a:'',w:''})});
    A.html=unitHTML(A.u,A.daf0,A.pi0); A.h=u.pt[k];
    A.lines=Math.max(1,Math.round(A.h/lh)); A.pt=u.pt.slice(0,k); A.el=null;
    B.html=unitHTML(B.u,null,null);    B.h=u.h-u.pt[k];
    B.lines=Math.max(1,Math.round(B.h/lh)); B.daf0=null; B.pi0=null; B.split=1; B.el=null;
    B.pt=u.pt.slice(k).map(x=>x-u.pt[k]);
    return [A,B];
  }
  function bookHTML(from,to){
    /* אוספים את היחידות עם ההקשר שלהן: דף נוכחי ונושא נוכחי */
    const units=[];let nose='';
    for(let pi=from;pi<=to;pi++){const p=D.pages[pi];
      if(!p.units.length)continue;   /* ב1: עמוד בלי טקסט כבר צורף לטווח בבנייה */
      let first=true;
      for(const u of p.units){
        if(u.k==='nose')nose=dec(u.a.replace(/<[^>]+>/g,''));
        units.push({html:unitHTML(u,first?p.daf:null,first?pi:null),daf:p.daf,label:p.label||'',nose,
                    k:u.k,u:u,daf0:first?p.daf:null,pi0:first?pi:null});
        first=false}}
    if(!units.length)return '';
    const sheets=paginate(units);
    return sheets.map(sh=>{
      const d=sh[0].label||sh[0].daf||'', n=sh[0].nose||'';
      return '<div class="sheet"><div class="shhd"><span class="nm">'+esc(D.masechet)+'</span>'+
        (n?'<span>· '+esc(n.slice(0,42))+'</span>':'')+
        '<span class="sp"></span><span class="df">'+esc(d)+'</span></div>'+
        '<div class="shbody">'+sh.map(u=>u.html).join('')+'</div></div>'}).join('')}
  function book(){
    BOOK=!BOOK;localStorage.setItem('lg-book',BOOK?'1':'');
    $('#bkbtn').classList.toggle('on',BOOK);
    $('#shsel').style.display=BOOK?'':'none';
    render(cur)}
  function setSheets(n){SHEETS=+n;localStorage.setItem('lg-sheets',SHEETS);
    $('#flow').style.setProperty('--sheets',sheetsNow());render(cur)}

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
  <button id="nkbtn" style="display:none" onclick="nikud()" title="ניקוד המשניות, מן הגמרא המנוקדת">ניקוד</button>
  <button id="bkbtn" onclick="book()" title="גיליונות זה לצד זה, בגיאומטריה של עמוד הספר">תצוגת ספר</button>
  <select id="shsel" style="display:none" onchange="setSheets(this.value)" title="כמה גיליונות זה לצד זה">
    <option value="1">גיליון אחד</option><option value="2">שני גיליונות</option><option value="3">שלושה גיליונות</option></select>
  <button id="vbtn" onclick="vert()" title="כל המסכת בטור אחד, בגלילה מלמעלה למטה">טור רצוף</button>
  <button id="fbtn" onclick="squeeze()" title="דחיסה עדינה שמעלה מילה בודדת שגלשה לשורה נפרדת">איחוי שורות</button>
  <button onclick="toPdf()" title="כל המסכת: בחלון שייפתח בחר ביעד 'שמירה כ-PDF'. כל פרק פותח עמוד חדש">כל המסכת ל-PDF</button>
  <button data-fs="15" onclick="setFs(15)">קטן</button><button data-fs="18" onclick="setFs(18)">רגיל</button><button data-fs="24" onclick="setFs(24)">גדול</button>
  <button onclick="fs(2)" title="Ctrl+=">א+</button><button onclick="fs(-2)" title="Ctrl+-">א-</button>
  <button onclick="document.body.classList.toggle('hc')">ניגודיות</button><button onclick="printPerek()" title="הדפסת הפרק הנוכחי בלבד, בעמוד הספר">הדפס פרק</button>
  <button id="edbtn" onclick="askAdmin()" title="עריכה תוך כדי לימוד (Ctrl+Alt+E)">עריכה</button>
  <button onclick="suggest()" title="סמן טקסט בדף, או לחץ כאן ובחר קטע">הצע תיקון</button>
  <button onclick="panel('sg');drawSg()">ההצעות שלי</button>
  <button id="sqbtn" style="display:none" onclick="sqOpen()" title="הצעות תיקון שממתינות להכרעתך">הצעות ממתינות</button></div>
  <div class="panel" id="search"><button class="x" onclick="panel('search')">×</button><h3>תוצאות חיפוש</h3><div id="sres"></div></div>
  <div class="panel" id="toc"><button class="x" onclick="panel('toc')">×</button><h3>תוכן העניינים - נושאי הסוגיות</h3><div id="tocb"></div></div>
  <div class="panel" id="am"><button class="x" onclick="panel('am')">×</button><h3>אמוראים ותנאים - לפי הסימון בקובץ</h3><div id="amb"></div></div>
  <div class="panel" id="qa"><button class="x" onclick="panel('qa')">×</button><h3>בקרת הקובץ - חריגות שנמצאו בהמרה</h3><div id="qab"></div></div>
  <div class="panel" id="ed"><button class="x" onclick="panel('ed')">×</button><h3>העריכות שלי</h3><div id="edb"></div></div>
  <div class="panel" id="sg"><button class="x" onclick="panel('sg')">×</button><h3>ההצעות שלי</h3><div id="sgb"></div></div>
  <div class="panel" id="sgq"><button class="x" onclick="panel('sgq')">×</button><h3>הצעות תיקון ממתינות</h3><div id="sgqb"></div></div>
  <div class="flow" id="flow"></div>
  <script>const DATA={J},SLUG="{slug}";</script><script>{JS}</script></body></html>'''

  open(out_path,'w',encoding='utf-8').write(page)
  return {'pages':len(pages),'toc':n_nose,'qa':qa,'empty':n_empty,'heavy':heavy,
          'hatz':hz_stat,
          'joined':{'dafRange':n_range,'dafTail':n_tail_daf,'dafIndex':n_index_daf,'dafDup':n_dup_daf,
                    'winStack':n_stack,'winDrop':n_stack_drop,'winTail':n_tail_win,'hatzDup':n_hatz_dup}}

if __name__=='__main__':
  r=build(sys.argv[1],sys.argv[2],sys.argv[3]); print(r['pages'],'pages',len(r['qa']),'qa')
