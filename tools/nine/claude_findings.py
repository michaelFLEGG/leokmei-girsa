# -*- coding: utf-8 -*-
"""claude_findings.py <מסכת> <slug> - מפיק קובצי ממצאים (שכבת "מודל") לבקרה של האתר, לכל פרק:
_work/bakara/<slug>-<פרק>/sem/claude.json, ואותם run.py מאחד לקובץ הממצאים של הפרק.
ממצא מסכם אחד לכל סוג בכל פרק (עם דוגמאות), וממצאים בודדים למקרים נדירים (הדרן שונה, משנה בלי מספר, ספקות המנוע המתקדם)."""
import sys, os, io, re, json, glob, collections
sys.path.insert(0, r'C:\Users\Owner\leokmei-girsa-nine\tools')
from docx2json import convert
M, SLUG = sys.argv[1], sys.argv[2]
W = r'C:\Users\Owner\leokmei-nine-work'
ROOT = r'C:\Users\Owner\leokmei-girsa-nine'
docx = os.path.join(W, 'prod', M + '.docx')
blocks = convert(docx)
byi = {b['i']: b for b in blocks}
starts = [b['i'] for b in blocks if b['style'] == 'פתיחת פרק'] or [b['i'] for b in blocks if b['style'] == 'פרק']
NIK = re.compile(r'[\u0591-\u05C7]')

def chapter_of(i):
    k = 0
    for n, s in enumerate(starts):
        if s <= i: k = n + 1
    return max(1, k)

def norm(t):
    return NIK.sub('', t or '')

texts = [(b['i'], norm(b['text'])) for b in blocks]
def locate(snippet, hint_daf=None):
    sn = norm(snippet).strip()
    if len(sn) < 6:
        return None
    for i, t in texts:
        if sn in t:
            return i
    return None

out = collections.defaultdict(list)       # פרק -> ממצאים
def add(i, kind, note, mark='', fix='', conf='בינוני'):
    b = byi.get(i)
    if b is None: return
    out[chapter_of(i)].append({'i': i, 'daf': b.get('daf') or '', 'kind': kind, 'mark': mark, 'note': note, 'fix': fix, 'conf': conf})

def first_block_of_chapter(ch):
    return starts[ch - 1] if 0 < ch <= len(starts) else (starts[0] if starts else 0)

# --- כותרות נוסח קלוד: מסכם לפרק
heads = []
mp = os.path.join(W, 'heads', M, 'merged.json')
if os.path.exists(mp):
    heads = json.load(io.open(mp, encoding='utf-8'))
by_ch = collections.defaultdict(list)
for h in heads:
    i = None
    for b in blocks:
        if b['style'] == 'נושא' and b['text'].strip() == h['head'] and chapter_of(b['i']) not in ():
            i = b['i']; break
    if i is None: continue
    by_ch[chapter_of(i)].append((i, h['head']))
for ch, lst in by_ch.items():
    ex = '; '.join('%s' % t for _, t in lst[:6])
    add(first_block_of_chapter(ch), 'כותרת נוסח קלוד',
        'בפרק %d נוספו %d כותרות נושא בנוסח קלוד (מוצגות בחום; המחבר משחיר כשהוא מאשר או מתקן). דוגמאות: %s' % (ch, len(lst), ex),
        conf='גבוה')

# --- ארמית שלא תורגמה / ציטוטים בספק: מסכם לפרק
sem = os.path.join(W, 'sem', M)
unres = collections.defaultdict(list); citq = collections.defaultdict(int); cit_unvoc = collections.defaultdict(list)
for f in sorted(glob.glob(os.path.join(sem, 'aram-??.json'))):
    nn = re.search(r'aram-(\d+)\.json', f).group(1)
    dec = json.load(io.open(os.path.join(sem, 'aram-dec-%s.json' % nn), encoding='utf-8'))
    for it in json.load(io.open(f, encoding='utf-8')):
        d = dec.get(it['id']) or {}
        if d.get('תרגום'): continue
        i = locate(it['לפני'][-18:] + it['מילה']) or locate(it['מילה'] + it['אחרי'][:14])
        if i is not None: unres[chapter_of(i)].append((it['מילה'], i))
for f in sorted(glob.glob(os.path.join(sem, 'cit-??.json'))):
    nn = re.search(r'cit-(\d+)\.json', f).group(1)
    dec = json.load(io.open(os.path.join(sem, 'cit-dec-%s.json' % nn), encoding='utf-8'))
    for it in json.load(io.open(f, encoding='utf-8')):
        d = dec.get(it['id']) or {}
        if d.get('סוג') == 'פסוק' and not d.get('ניקוד'):
            i = locate(it['לפני'][-15:] + "'" + it['טקסט']) or locate(it['טקסט'])
            if i is not None: cit_unvoc[chapter_of(i)].append((it['טקסט'], i))
for ch, lst in unres.items():
    words = collections.Counter(w for w, _ in lst)
    ex = '; '.join('%s (%d)' % (w, n) for w, n in words.most_common(10))
    add(first_block_of_chapter(ch), 'ארמית שלא תורגמה',
        'בפרק %d נותרו %d מופעי ארמית שהמנוע לא הכריע בתרגומם (מונח סוגיה, עברית תקנית או ספק). הצורות השכיחות: %s' % (ch, len(lst), ex), conf='נמוך')
for ch, lst in cit_unvoc.items():
    ex = '; '.join(t[:28] for t, _ in lst[:5])
    add(first_block_of_chapter(ch), 'ציטוט בספק',
        'בפרק %d: %d ציטוטים שסומנו כפסוק אך לא נוקדו בוורד (באתר מנוקדים אוטומטית כשנמצא רצף זהה בגמרא). דוגמאות: %s' % (ch, len(lst), ex), conf='נמוך')

# --- הדרן שונה מן הפתיחה, משנה בלי מספר: מיומני ההרצה
for lf in ('struct1.log', 'struct2.log'):
    p = os.path.join(W, lf)
    if not os.path.exists(p): continue
    for line in io.open(p, encoding='utf-8', errors='replace'):
        line = line.strip()
        if not line.startswith('{'): continue
        try: r = json.loads(line)
        except Exception: continue
        if r.get('file') != M + '.docx': continue
        for n in r.get('notes', []) or []:
            m = re.search(r'שם בשורת הדרן שונה מן הפתיחה, לא שונה: "(.+?)" מול פתיחה "(.+?)"', n)
            if m:
                i = locate(m.group(1)[:25])
                if i is not None:
                    add(i, 'שם בהדרן שונה מן הפתיחה', 'שורת ההדרן: "%s"; שורת הפתיחה: "%s". לא שונה אוטומטית (שם הפרק בפתיחה גובר, אלא אם נוסח ההדרן מסורתי).' % (m.group(1), m.group(2)), mark=m.group(1)[:25])
        pass
# משניות בלי מספר (m6)
seen = set()
p = os.path.join(W, 'struct1.log')
if os.path.exists(p):
    cur = None
    for line in io.open(p, encoding='utf-8', errors='replace'):
        if line.startswith('{') and '"no_number"' in line:
            try: r = json.loads(line.strip())
            except Exception: continue
            if r.get('file') != M + '.docx': continue
            for daf, idx in r.get('no_number', []):
                if daf in seen: continue
                seen.add(daf)
                tgt = None
                for b in blocks:
                    if (b.get('daf') or '').strip() == daf.strip() and b['style'] == 'משניות':
                        tgt = b['i']; break
                if tgt is not None:
                    add(tgt, 'ד"ה משנה / מספור', 'יחידת משנה בדף %s שלא נמצא לה מספר משנה בפרק (הנוסח אינו מתאים לאף משנה בנוסח ספריא); נשארה בלי מסגרת "משנה" ממוספרת.' % daf, conf='נמוך')

# --- המנוע המתקדם (שבת): ספקות העורך ושל הבודק, כממצאים בודדים לפי הטקסט
adv = os.path.join(W, 'adv')
if M == 'שבת' and os.path.isdir(adv):
    for ud in sorted(glob.glob(os.path.join(adv, 'unit-*'))):
        nn = ud.rsplit('-', 1)[-1]
        rows = {}
        for line in io.open(os.path.join(ud, 'in.txt'), encoding='utf-8'):
            p_ = line.rstrip('\n').split('|', 2)
            if len(p_) == 3 and p_[0].isdigit(): rows[int(p_[0])] = p_[2]
        for fn, tag in (('doubt-%s.json' % nn, 'ספק העורך'), ('check-%s.json' % nn, 'בדיקה')):
            fp = os.path.join(adv, 'findings', fn)
            if not os.path.exists(fp): continue
            try: arr = json.load(io.open(fp, encoding='utf-8'))
            except Exception: continue
            for d in arr:
                if tag == 'בדיקה' and d.get('action') not in ('ספק', None) and d.get('action') != 'ספק':
                    # תיקון או מחיקה שהבודק ביצע - מידע, לא ספק: נרשם כסיכום בלבד
                    continue
                t = rows.get(d.get('i'))
                if not t: continue
                i = locate(t[:60])
                if i is None: continue
                add(i, 'מנוע מתקדם', '%s: %s' % (tag, d.get('note', '')), mark='', conf='בינוני')
    # סיכום לפרק של מה שתוקן בבדיקה
    # (נמנה בדוח; בבקרה נשאר כל ספק כממצא)

# כתיבה
n = 0
for ch, lst in out.items():
    d = os.path.join(ROOT, '_work', 'bakara', '%s-%d' % (SLUG, ch), 'sem')
    os.makedirs(d, exist_ok=True)
    json.dump(lst, io.open(os.path.join(d, 'claude.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    n += len(lst)
print(M, 'פרקים', len(starts), 'ממצאים', n, dict((k, len(v)) for k, v in sorted(out.items())))
