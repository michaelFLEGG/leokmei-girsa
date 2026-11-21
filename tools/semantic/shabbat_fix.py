# -*- coding: utf-8 -*-
"""תיקון סמנטי בסיסי למסכת שבת (21.11.2026) - מחשב עריכות מתוך מצב הדף החי (dump.json)."""
import json, re, html, collections, sys, time
sys.path.insert(0, '/home/claude/sem')
import laukmi_rules as R

D = json.load(open('/home/claude/dl/dump.json', encoding='utf-8'))
ROWS = D['rows']
for _r in ROWS:
    if 'h' in _r:
        _r['h'] = re.sub(r'<span class="bkx[^"]*"[^>]*></span>', '', _r['h'])
LIVE = {}
MINE = 1795282688000
BASE = {int(k): v for k, v in (D.get('base') or {}).items()}
for e in D['live']:
    if e.get('t', 0) >= MINE:
        continue
    if e.get('op') != 'struct' and e.get('k'):
        o = LIVE.get(e['k'])
        if not o or e.get('t', 0) > o.get('t', 0):
            LIVE[e['k']] = e


# שחזור הניקוד: יחידה מנוקדת שהניקוד ירד ממנה בגלל עריכה שלי (לא של המנהל) - המקור הוא שכבת הניקוד
_NIK = re.compile(r'[\u0591-\u05C7]')
def _pl(h): return html.unescape(re.sub(r'<[^>]+>', '', h))
_user_units = set()
for _k in LIVE:
    _m = re.match(r'^u(\d+)\.', _k)
    if _m: _user_units.add(int(_m.group(1)))
RESTORED = 0
for _r in ROWS:
    _m = re.match(r'^u(\d+)\.(\d+)$', _r.get('ek') or '')
    if not _m or 'h' not in _r: continue
    _u, _n = int(_m.group(1)), int(_m.group(2))
    if _u not in BASE or _u in _user_units or _NIK.search(_r['t']): continue
    _lv = BASE[_u]['lv']
    if _n - 1 >= len(_lv): continue
    _vh = _lv[_n - 1][1]
    if _NIK.sub('', _pl(_vh)).split() == _r['t'].split() or _NIK.sub('', _pl(_vh)).replace(' ', '') == _r['t'].replace(' ', '').replace('\xa0', ''):
        _r['h'] = _vh; _r['t'] = _pl(_vh); RESTORED += 1
print('restored', RESTORED)

Q = r'(?:&quot;|"|״)'
TAG = re.compile(r'(<[^>]+>)')


def plain(h):
    return html.unescape(re.sub(r'<[^>]+>', '', h))


def segs(h):
    """[(text, eligible)]: eligible = מחוץ לכל תג, או רק בתוך <i class="b">"""
    out, stack = [], []
    for part in TAG.split(h):
        if not part:
            continue
        if part.startswith('<'):
            if part.startswith('</'):
                if stack:
                    stack.pop()
            elif not part.endswith('/>') and not part.startswith('<br'):
                m = re.match(r'<(\w+)(?:\s+class="([^"]*)")?', part)
                stack.append((m.group(1), m.group(2) or '') if m else ('?', ''))
            out.append((part, None))
        else:
            ok = all(t == 'i' and c == 'b' for t, c in stack)
            out.append((part, ok))
    return out


def join(sg):
    return ''.join(s for s, _ in sg)


AM = lambda s: '<i class="am">' + s + '</i>'

# --- א. נוסחאות אמירה ---
W = r'[^\s:,.;!?\'"()\[\]\-–<>&]+'
VERB = (r'(?:אמר(?:ו|ה|י)?|א' + Q + r'ל|שאל(?:ו)?|השיב(?:ו|ם|ה)?|תנן|תנא|תניא|ת' + Q + r'ש|איתמר|מתיב|מתקיף|אמרי|שלחו|שלח)')
PRE = r'(?:ו|ש|וש|כש|ד|כד|מד|ושנה |ממה ש|כמו ש|והרי |וה|מ)?'
SPEECH = re.compile(r'(?<![א-ת"\'&;])(' + PRE + VERB + r'(?:\s+(?:' + W + r'|[א-ת]+' + Q + r'[א-ת]+)){0,3}:)')
BAD_IN = re.compile(r'תורה|רחמנא|הכתוב|קרא|המשנה|שנאמר|דכתיב|כתיב|(?:^|\s)(?:מה|מי|מאי|היכן|למה):')
TANA = re.compile(r'^(?:ו|ש|וש|כש|ד|כד|מד|והרי |וה|מ)?(?:תנן|תנא|תניא|ת(?:&quot;|"|״)ש)(?:\s+(?:שם|כמותו|אידך))?:$')
TANAV = re.compile(r'(?:תנן|תנא|תניא|ת(?:&quot;|"|״)ש)')


def speech(sg, start_line):
    n = 0
    out = []
    for i, (s, ok) in enumerate(sg):
        if not ok:
            out.append((s, ok)); continue
        def rep(m):
            nonlocal n
            g = m.group(1)
            if BAD_IN.search(g) or len(g.split()) > 5:
                return g
            if TANAV.match(re.sub(r'^(?:ו|ש|וש|כש|ד|כד|מד|והרי |וה|מ)', '', g)) and not TANA.match(g):
                return g
            n += 1
            return AM(g)
        s2 = SPEECH.sub(rep, s)
        # קשה: בתחילת שורה
        if start_line and i == 0 or (start_line and all(not x[0].strip() or x[1] is None for x in sg[:i]) and i <= 1):
            m = re.match(r'^(\s*)(קשה:|וקשה:)', s2)
            if m:
                s2 = m.group(1) + AM(m.group(2)) + s2[m.end():]; n += 1
        out.append((s2, ok))
    return out, n


# --- ב. שמות ---
NOT = set(R.NOT_NAME) | {'אמר', 'בר"ה', 'ר"ה', 'מר"ה', 'בר"ח', 'ר"ח'} - {'ר"ה', 'ר"ח'}
# ר"ה ור"ח: ראש השנה / ראש חודש - רק כשאחריהם נקודתיים או "אמר" נחשבים שם
AMBIG = {'ר"ה', 'ר"ח', 'בר"ה', 'בר"ח', 'ור"ה', 'ור"ח', 'לר"ה', 'לר"ח', 'מר"ח', 'דר"ח', 'כר"ח', 'ער"ה'}
ABBR = re.compile(r'(?<![א-ת"\'&;])((?:[ודלכמשב]{0,2})?[א-ת]{0,4}ר[א-ת]{0,4}' + Q + r'[א-ת]{1,3})(?![א-ת"\'&])')
EXTRA_ABBR = re.compile(r'(?<![א-ת"\'&;])((?:[ודלכמש]{0,2})?(?:ב' + Q + r'[שה]|ת' + Q + r'ק))(?![א-ת"\'&])')
NONAME = re.compile(r'רה"[רי]|ער"[שפלהח]|יר"ש|ירא"ש|קר"ש|רי"ש$|^ב?יר"ש')
FIRST = set()
HEAD = r'(?:רבי|רב|ר\'|רבן)'
for r in ROWS:
    for m in re.findall(r'<i class="am">(.*?)</i>', r.get('h', '')):
        t = html.unescape(re.sub('<[^>]+>', '', m)).strip().rstrip(':,')
        mm = re.search(r'(?:^|\s|^[ודלכמש]{1,2})' + HEAD + r'\s+([א-ת]{2,})', t)
        if mm and mm.group(1) not in ('אמר', 'אומר', 'שאמר', 'ואמר', 'הוא', 'מכל', 'גדול', 'כח', 'טוב'):
            FIRST.add(mm.group(1))
FIRST -= {'אמר', 'אומר', 'בר', 'בן', 'היה', 'לא', 'שם'}
FULL = re.compile(r'(?<![א-ת"\'])((?:[ודלכמש]|של |מן )?' + HEAD + r' (?:' + '|'.join(sorted(map(re.escape, FIRST), key=len, reverse=True)) +
                  r')(?: (?:בר|בן|ברבי|בריה דרב) [א-ת]{2,})?)(?![א-ת])')
SINGLE = re.compile(r'(?<![א-ת"\'])((?:[ודלכמש])?(?:אביי|רבא|שמואל|חזקיה|עולא|זעירי|רבינא|רבנן|(?<!תלמידי )(?<!של )חכמים|בית שמאי|בית הלל|ריש לקיש|בן עזאי|בן זומא|רבין|לוי בר [א-ת]+))(?![א-ת"\'])')
SINGLE_COLON = re.compile(r'(?<![א-ת"\'])((?:[ודלכמש])?(?:רב|רבה|רבי|שמאי|הלל|חכמים|לוי):)')


def names(sg):
    n = 0
    out = []
    for s, ok in sg:
        if not ok:
            out.append((s, ok)); continue
        def wrap_abbr(m):
            nonlocal n
            w = m.group(1)
            ww = html.unescape(w)
            if ww in NOT or ww.replace('״', '"') in NOT or NONAME.search(ww.replace('״', '"')):
                return w
            core = re.sub(r'^[ודלכמשב]{0,2}', '', ww)
            if ww in AMBIG or core in ('ר"ה', 'ר"ח', 'ה"ר', 'ע"ר'):
                tail = s[m.end():m.end() + 6]
                if not re.match(r'\s*(:|אמר|אומר|סבר)', tail):
                    return w
            if not re.search(r'ר' + '(?:&quot;|"|״)', w) and not re.search('ר[א-ת]{1,4}(?:&quot;|"|״)', w):
                return w
            n += 1
            return AM(w)
        # הגנה: לא לגעת בתוך תג am שכבר נוצר (המחרוזת כאן היא טקסט בלבד, ולכן מפצלים לפי תגים אחרי כל שלב)
        s1 = ABBR.sub(wrap_abbr, s)
        parts = TAG.split(s1)
        res = []
        depth = 0
        for p in parts:
            if p.startswith('<'):
                depth += -1 if p.startswith('</') else 1
                res.append(p); continue
            if depth:
                res.append(p); continue
            def w2(m):
                nonlocal n
                n += 1
                return AM(m.group(1))
            p = EXTRA_ABBR.sub(w2, p)
            p = FULL.sub(w2, p)
            sub = TAG.split(p)
            p = ''.join(x if x.startswith('<') else SINGLE.sub(w2, x) for x in sub)
            sub = TAG.split(p)
            p = ''.join(x if x.startswith('<') else SINGLE_COLON.sub(w2, x) for x in sub)
            res.append(p)
        out.append((''.join(res), ok))
    return out, n


def fix_nested(h):
    """<i class="am"> שנוצר בתוך am (לא אמור לקרות) - ניקוי"""
    return h


# --- הרצה ---
t0 = int(time.time() * 1000)
seq = [0]


def T():
    seq[0] += 1
    return t0 + seq[0]


edits, report = [], collections.Counter()
samples = collections.defaultdict(list)
daf = ''
rows_by = collections.defaultdict(list)
for r in ROWS:
    rows_by[r['ri']].append(r)
newh = {}
for r in ROWS:
    if r.get('daf'):
        daf = r['daf']
    r['_daf'] = daf
    if 'h' not in r or not r.get('ek'):
        continue
    if r['rc'] not in ('row u', 'row u enl', 'row'):
        continue
    if any(c in r['c'].split() for c in ('nose', 'dh', 'hr', 'hatz')):
        continue
    h = r['h']
    h0 = re.sub(r'<i class="am">([^<]*)</i>', lambda m: m.group(1) if False else m.group(0), h)
    if h0 != h:
        report['unstyled'] += 1
    sg = segs(h0)
    nv = 0
    if r['rc'] != 'row':
        sg, nv = speech(sg, True)
        sg = segs(join(sg))
    sg, nn = names(sg)
    h2 = join(sg)
    # am בתוך am - לא אמור; בדיקה
    if re.search(r'<i class="am">[^<]*<i class="am">', h2):
        report['nested-skip'] += 1
        continue
    if h2 != h:
        newh[r['ek']] = h2
        report['speech'] += nv
        report['names'] += nn
        if len(samples['line']) < 400:
            samples['line'].append((r['_daf'], plain(h)[:90], re.findall(r'<i class="am">(.*?)</i>', h2)))

json.dump({'newh': newh, 'report': report, 'samples': samples}, open('/home/claude/sem/stage1.json', 'w'), ensure_ascii=False, indent=0)
print(report, len(newh))

# ===== שלב ב: כותרות צד, כפולות =====
KEEPC = re.compile(r'^(?:b\d|a\d|sp|in|nose|dh|hr|mu)$')
def dcls(c):
    return ' '.join(x for x in c.split() if KEEPC.match(x))

def dupNorm(t):
    return re.sub(r'[\s \'"׳״\-–—.,:;!?()\[\]•·]', '', re.sub(r'[֑-ׇ]', '', t or ''))

def dupSim(a, b):
    if a == b: return 1
    s, l = (a, b) if len(a) < len(b) else (b, a)
    if len(s) >= 6 and s in l and len(s) / len(l) >= .6: return .95
    def g(x):
        m = collections.Counter(x[i:i+2] for i in range(len(x)-1)); return m
    A, B = g(a), g(b); n = sum(min(v, B[k]) for k, v in A.items())
    return 2 * n / max(1, (len(a)-1) + (len(b)-1))

seq_rows = [r for r in ROWS]
# רצף אלמנטים כמו בדף: עוגן (כותרת צד) של השורה, ראש שורה nose/dh, ושורות p
els = []
for ri in sorted(rows_by):
    rs = rows_by[ri]
    r0 = rs[0]
    if r0.get('side'): els.append(('anchor', r0['side'], None))
    for r in rs:
        if 'h' in r: els.append(('p', r['t'], r))
        elif r['rc'] in ('row nose', 'row dh'): els.append(('head', r['t'], r))
dups = []
pv = None
for el in els:
    t = dupNorm(el[1])
    if not t: continue
    if pv and len(t) >= 6 and len(dupNorm(pv[1])) >= 6:
        s = dupSim(dupNorm(pv[1]), t)
        if s >= .86: dups.append((round(s, 2), pv, el))
    pv = el
print('dups', len(dups))
for s, a, b in dups:
    print(s, a[0], (a[2] or {}).get('c'), a[1][:60], '||', b[0], (b[2] or {}).get('c'), b[1][:60], (a[2] or b[2] or {}).get('_daf'))

# ===== שלב ג: הדגשת עיקר המשנה =====
BOLD = json.load(open('/home/claude/sem/bold.json', encoding='utf-8'))
NIK = re.compile(r'[֑-ׇ]')

def chars(h):
    """[(ch, html_start, html_end)] לתווי הטקסט, ורשימת גבולות תגים"""
    out = []; i = 0
    while i < len(h):
        if h[i] == '<':
            j = h.index('>', i) + 1; i = j; continue
        if h[i] == '&':
            j = h.find(';', i)
            if 0 < j - i < 8:
                out.append((html.unescape(h[i:j+1]), i, j + 1)); i = j + 1; continue
        out.append((h[i], i, i + 1)); i += 1
    return out

def bold_range(h, s, e, cs):
    # מחלקים לפי ריצות טקסט רצופות בתוך ה-HTML
    pieces = []; cur = None
    for k in range(s, e):
        a, b = cs[k][1], cs[k][2]
        if cur and cur[1] == a: cur[1] = b
        else:
            if cur: pieces.append(cur)
            cur = [a, b]
    if cur: pieces.append(cur)
    for a, b in reversed(pieces):
        if not h[a:b].strip(): continue
        h = h[:a] + '<i class="b">' + h[a:b] + '</i>' + h[b:]
    return h

def mbold(h, phrases):
    h = re.sub(r'<i class="b">((?:(?!</i>).)*?(?:<i [^>]*>.*?</i>(?:(?!</i>).)*?)*)</i>', r'\1', h)
    h = h.replace('<i class="b">', '').replace('</i><i', '</i><i')  # שארית
    # ניקוי סגירות יתומות: מאזנים תגי i
    out, depth = [], 0
    for p in TAG.split(h):
        if p.startswith('<i'): depth += 1
        elif p == '</i>':
            if depth == 0: continue
            depth -= 1
        out.append(p)
    h = ''.join(out)
    for ph in phrases:
        cs = chars(h)
        bare = []; idx = []
        for k, (c, a, b) in enumerate(cs):
            if NIK.match(c): continue
            bare.append(c); idx.append(k)
        bt = ''.join(bare).replace('״', '"')
        p = bt.find(ph)
        if p < 0:
            report['bold-miss'] += 1; print('MISS', ph); continue
        s, e = idx[p], idx[p + len(ph) - 1] + 1
        while e < len(cs) and NIK.match(cs[e][0]): e += 1
        h = bold_range(h, s, e, cs)
        report['bold'] += 1
    return h

mfull = set()
for ri, ls in rows_by.items():
    ls = [x for x in ls if 'h' in x and x['rc'] == 'row']
    if not ls: continue
    t = sum(len(x['t']) for x in ls)
    b = sum(len(html.unescape(re.sub('<[^>]+>', '', ''.join(re.findall(r'<i class="b">(.*?)</i>', x['h']))))) for x in ls)
    if b / max(1, t) > .85:
        for x in ls: mfull.add(x['ek'])
BYEK = {r['ek']: r for r in ROWS if r.get('ek')}
for ek in mfull:
    h = newh.get(ek, BYEK[ek]['h'])
    h2 = mbold(h, BOLD.get(ek, []))
    if plain(h2) != plain(BYEK[ek]['h']):
        print('TEXT CHANGED', ek); continue
    newh[ek] = h2
print(report)
json.dump(newh, open("/home/claude/sem/newh.json","w"), ensure_ascii=False)

# ===== שלב ד: ד"ה משנה שסומן כסגנון תו =====
splits = []
for r in ROWS:
    h = newh.get(r.get('ek'), r.get('h', ''))
    if not r.get('ek') or r['rc'] not in ('row u', 'row u enl') or 'class="dm"' not in h: continue
    m = re.match(r'^\s*<i class="dm">(.*?)</i>(.*)$', h, re.S)
    if not m: continue
    inner, rest = m.group(1), m.group(2)
    if not plain(rest).strip():
        newh[r['ek']] = inner
        r['_ps'] = 'dh b0 a0'
        report['dm->dh'] += 1
    else:
        if not re.match(r'^\s*(?:-|–)\s', rest):
            continue
        rest2 = re.sub(r'^\s*(?:-|–)\s*', '', rest).strip()
        splits.append((r, inner, rest2))
        report['dm-split'] += 1

# ===== שלב ה: כותרות צד =====
ENUM = re.compile(r'^(?:[אבגדהוזחטיכ]|י[אבגדזחט]|כ[א-ט]|טו|טז)\.$')
sides = []
for ri, ls in rows_by.items():
    ls = [x for x in ls if 'h' in x]
    for x in ls:
        if x['rc'] not in ('row u', 'row u enl') or not x.get('ek'): continue
        if any(c in x['c'].split() for c in ('nose', 'dh', 'hr', 'in')) or x.get('_ps'): continue
        if x['pi'] == 0 and (x.get('side') or ''):
            continue
        h = newh.get(x['ek'], x['h'])
        m = re.match(r'^(\s*)<i class="am">([^<]+)</i>(?:(\s*)<i class="am">([^<]+)</i>)?', h)
        if not m: continue
        a1 = html.unescape(m.group(2)).strip()
        a2 = html.unescape(m.group(4)).strip() if m.group(4) else ''
        if a2 and ENUM.match(a1):
            sideT, end = a1 + ' ' + a2, m.end()
        else:
            sideT, end = a1, m.start(3) if m.group(3) is not None else m.end()
            if m.group(4): end = h.index('</i>') + 4
        if not (sideT.endswith(':') or ENUM.match(sideT)): continue
        if len(sideT.split()) > (3 if ENUM.match(sideT.split()[0]) else 2) or len(sideT) > 16: continue
        body = h[end:].lstrip()
        if len(plain(body).strip()) < 3: continue
        t = x['t']
        cs = t.find(sideT.split()[0][:2])
        sides.append((x, sideT, body))
report['side'] = len(sides)

# ===== שלב ו: כפולות =====
def voc(t): return bool(NIK.search(t))
dels = []   # (row-line, reason)
for s, a, b in dups:
    if s < .95: continue
    A, B = a, b
    pa, pb = (a[0] == 'p'), (b[0] == 'p')
    if pa and pb:
        ra, rb = a[2], b[2]
        na, nb = dupNorm(a[1]), dupNorm(b[1])
        if voc(a[1]) != voc(b[1]):
            if ra['ri'] != rb['ri']: continue
            if na != nb: continue
            dels.append((rb if voc(a[1]) else ra, 'ניקוד'))   # נשאר המנוקד
            continue
        if na == nb:
            if 'nose' in ra['c'] and 'nose' in rb['c']:
                dels.append((rb, 'כותרת כפולה')); continue
            if ra['ri'] != rb['ri'] and not (len(na) < 20): continue
            dels.append((ra, 'שורה כפולה')); continue
        # הכלה: הקצרה נמחקת, רק באותה יחידה
        if ra['ri'] == rb['ri']:
            dels.append((ra if len(na) < len(nb) else rb, 'נכללת בשכנתה'))
        continue
    p = a if pa else b
    o = b if pa else a
    if not pa and not pb: continue
    r = p[2]
    if voc(p[1]) and not voc(o[1]): continue
    if 'nose' in r['c'] or dupNorm(p[1]) == dupNorm(o[1]) or (o[0] == 'anchor'):
        if dupNorm(p[1]) in dupNorm(o[1]) or dupNorm(o[1]) in dupNorm(p[1]):
            dels.append((r, 'כפולה לכותרת'))
seen = set(); D2 = []
for r, why in dels:
    if r['ek'] in seen: continue
    seen.add(r['ek']); D2.append((r, why))
dels = D2
report['dup-del'] = len(dels)
print(report)
for r, why in dels: print('DEL', r['_daf'], why, r['t'][:70])
for x, s, b in sides[:40]: print('SIDE', x['_daf'], s, '|', plain(b)[:60])

# סינון כותרות צד: רק מספור, שם, או מטבע קבוע
DELK = {r['ek'] for r, _ in dels}
OKSIDE = {'קשה:', 'וקשה:', 'ת"ש:', 'א"ל:', 'וא"ל:', 'מתיב:'}
def has_name(s):
    e = html.escape(s, quote=False)
    return bool(ABBR.search(s) and not NONAME.search(s)) or bool(EXTRA_ABBR.search(s)) or bool(FULL.search(s)) or bool(SINGLE.search(s)) \
        or bool(SINGLE_COLON.search(s)) or bool(re.search(r'חכמים|חכ"א|רבנן|ת"ק', s))
S2 = []
for x, s, b in sides:
    if x['ek'] in DELK: continue
    w0 = s.split()[0]
    if ENUM.match(w0) or s in OKSIDE or has_name(s):
        S2.append((x, s, b))
sides = S2
report['side'] = len(sides)

# ===== בניית העריכות =====
CTX = {}
_ps = [e for e in els if e[0] in ('p', 'anchor', 'head')]
for i, e in enumerate(_ps):
    if e[0] == 'p' and e[2].get('ek'):
        CTX[e[2]['ek']] = {'b': (_ps[i-1][1] if i else '')[-40:], 'a': (_ps[i+1][1] if i + 1 < len(_ps) else '')[:40]}
E = []
def unit_of(ek):
    m = re.match(r'^u(\d+)\.(\d+)$', ek or '')
    return (int(m.group(1)), int(m.group(2))) if m else (None, None)
touched_lv = set()
for ek in list(newh) + list(DELK):
    uid, n = unit_of(ek)
    if uid in BASE: touched_lv.add(uid)
# כל שורות היחידה המנוקדת נשלחות, כדי שהניקוד יישאר בכולן
for r in ROWS:
    uid, n = unit_of(r.get('ek'))
    if uid in touched_lv and r['ek'] not in newh and r['ek'] not in DELK:
        newh[r['ek']] = r['h']
for ek, h2 in newh.items():
    r = BYEK[ek]
    if ek in DELK: continue
    old = LIVE.get(ek)
    uid, n = unit_of(ek)
    if old:
        was = old['was']
        wasH = old.get('wasH') if old.get('wasH') is not None else html.escape(old['was'], quote=False)
        wasP = old.get('wasP') if old.get('wasP') is not None else dcls(r['c'])
    elif uid in BASE and n and n - 1 < len(BASE[uid]['l']):
        bh = BASE[uid]['l'][n - 1][1]
        was, wasH, wasP = plain(bh), bh, BASE[uid]['l'][n - 1][0]
        if h2 == bh: continue
    else:
        was, wasH, wasP = r['t'], r['h'], dcls(r['c'])
        if h2 == r['h']: continue
    if plain(h2).replace('\xa0', ' ') != r['t'].replace('\xa0', ' '):
        report['text-mismatch'] += 1; print('MISMATCH', ek, r['t'][:50], '|', plain(h2)[:50]); continue
    e = {'k': ek, 'was': was, 'now': r['t'], 'wasH': wasH, 'nowH': h2, 'wasP': wasP, 'daf': r['_daf'],
         'ctx': (old.get('ctx') if old and old.get('ctx') else CTX.get(ek, '')), 't': T()}
    ps = r.get('_ps') or (old.get('ps') if old else None)
    if ps:
        e['ps'] = ps
        e['psw'] = 'ד\'\'ה משנה' if 'dh' in ps else ''
    if r.get('_ps'):
        e['now'] = plain(h2)
    E.append(e)
nt = len(E)
# פיצולי ד"ה משנה
for r, inner, rest in splits:
    h = newh.get(r['ek'], r['h'])
    cl = dcls(r['c'])
    E.append({'k': 's' + str(T()), 'op': 'struct', 'kind': 'split', 'texts': [r['t']],
              'res': [['dh b0 a0', inner], [cl, rest]], 'resT': [plain(inner), plain(rest)], 'daf': r['_daf']})
    E[-1]['t'] = int(E[-1]['k'][1:])
# כותרות צד
for x, s, body in sides:
    t = x['t']
    lead = len(t) - len(t.lstrip())
    cs = t.find(s.split()[0], lead)
    ln = len(t) - len(plain(body)) - cs
    tt = T()
    E.append({'k': 's' + str(tt), 't': tt, 'op': 'struct', 'kind': 'side', 'texts': [t],
              'res': [[dcls(x['c']), body], [html.escape(s, quote=False)], [cs, max(0, ln)]],
              'resT': [plain(body), s], 'daf': x['_daf']})
# כפולות: איחוי עם השכנה ביחידה
for r, why in dels:
    ls = [y for y in rows_by[r['ri']] if 'h' in y]
    i = ls.index(r)
    tt = T()
    if i + 1 < len(ls):
        nb = ls[i + 1]; texts = [r['t'], nb['t']]; keep = nb
    elif i > 0:
        nb = ls[i - 1]; texts = [nb['t'], r['t']]; keep = nb
    else:
        report['dup-single-skip'] += 1; print('SKIP single', r['_daf'], r['t'][:50]); continue
    kh = newh.get(keep['ek'], keep['h'])
    E.append({'k': 's' + str(tt), 't': tt, 'op': 'struct', 'kind': 'merge', 'texts': texts,
              'res': [[dcls(keep['c']), kh]], 'resT': [plain(kh)], 'daf': r['_daf']})
    report['dup-done'] += 1
print(report, 'text', nt, 'all', len(E))
json.dump({'slug': 'shabbat', 'edits': E}, open('/home/claude/sem/edits.json', 'w'), ensure_ascii=False, indent=0)
