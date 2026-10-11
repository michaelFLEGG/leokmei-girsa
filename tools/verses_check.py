# -*- coding: utf-8 -*-
"""verses_check.py - איתור פסוקים שלא סומנו בסגנון "פסוק".

הזיהוי הוא התאמה לנוסח המקרא עצמו (data/tanakh-ktiv.json, מספריא, כתיב
בלבד), ולא ניחוש: קטע בפסקה נחשב פסוק רק כשרצף מילותיו חופף לרצף מילים
באותו פסוק. שלוש דרכים להגיע לקטע מועמד:

  א. ציטוט בגרשיים ('...')           - רצף של שלוש מילים לפחות, ולפחות
                                        שבעים אחוז מהציטוט; שתי מילים רק
                                        כשהצירוף נדיר במקרא ומקדים אותו
                                        ביטוי פתיחה.
  ב. אחרי ביטוי פתיחה (שנאמר, דכתיב,   - רצף של שלוש מילים לפחות (שתיים
     כתיב, שנא' ...)                     כשהצירוף נדיר) בתוך שבע המילים
                                        הראשונות אחריו.
  ג. בלי גרשיים ובלי פתיחה             - רק רצף ארוך (שש מילים לפחות).

ההשוואה נעשית על שלד האותיות: בלי ניקוד וטעמים, אותיות סופיות כרגילות,
ובלי ו/י (כתיב מלא וחסר), כדי שגמרא שכותבת "בהמת" ומקרא שכותב "בהמת"
או "בהמות" לא יחטיאו זה את זה. שם ה' ("ה'") מתאים ל"יהוה", ו"אלקים"
ל"אלהים".

    uv run python tools/verses_check.py <קובץ.docx>   - דוח בלבד, לא נוגע בקובץ
"""
import os, sys, re, json, io, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TANAKH = os.path.join(ROOT, 'data', 'tanakh-ktiv.json')

NIK = re.compile(r'[֑-ׇ]')
WORD = re.compile(r"[א-ת֑-ׇ]+")
QUOTE = re.compile(r"'([^']{2,260}?)'")
INTRO = re.compile(r"(?:^|[\s(\-–])((?:ו|ד|מ|ש)?(?:שנא'|שנאמר|נאמר|כתיב|דכתיב|וכתיב|מדכתיב|אמר\s+קרא|דאמר\s+קרא|"
                   r"שנאמר|הכתוב|שכתוב|דכתיב)\b|ת\"ל|תלמוד\s+לומר)")
# סימן שמפריד בין פסוק לדברי הגמרא שאחריו: סוף משפט, נקודתיים, נקודה-פסיק, מקף
BARRIER = re.compile(r"[.?!;:–\-]")
FINAL = str.maketrans('ךםןףץ', 'כמנפצ')

MIN_FREE = 6        # רצף ארוך בלי גרשיים ובלי פתיחה
MIN_QUOTE = 3
RARE = 6            # צירוף של שתי מילים שמופיע לכל היותר במספר כזה של פסוקים


def skel(w):
    w = NIK.sub('', w).replace("'", '').replace('׳', '').translate(FINAL)
    if w.startswith(('אלק',)):
        w = 'אלה' + w[3:]                 # אלקים / אלוקים -> אלהים
    s = w.replace('ו', '').replace('י', '')
    return s or w


_IDX = None


def load():
    """מחזיר (פסוקים, אינדקס זוגות). נטען פעם אחת."""
    global _IDX
    if _IDX is not None:
        return _IDX
    if not os.path.exists(TANAKH):
        raise SystemExit('עצירה: אין data/tanakh-ktiv.json. הרץ tools/fetch_tanakh.py')
    rows = json.load(io.open(TANAKH, encoding='utf-8'))
    verses = []
    bi = collections.defaultdict(list)
    for vi, (book, ch, v, words) in enumerate(rows):
        ws = [skel(w) for w in words]
        verses.append((book, ch, v, ws))
        for p in range(len(ws) - 1):
            bi[(ws[p], ws[p + 1])].append((vi, p))
    _IDX = (verses, bi)
    return _IDX


YHVH = {'יהוה', 'הה'}                      # שלד "יהוה" הוא "הה"


def _eq(a, b):
    """האם מילת טקסט שוות למילת מקרא (שניהן שלדים)."""
    if a == '#':
        return False
    if a == b:
        return True
    if a in ('ה', 'ד') and b == 'הה':      # ה' / ד' במקום שם ה'
        return True
    return False


def _tokens(txt):
    """(התחלה, סוף, שלד). מילה שצמוד אליה גרשיים (ש"מ, אב"א) או גרש של קיצור
    (שנא') אינה יכולה להיות חלק מפסוק, והשלד שלה '#' - מחסום שאינו תואם דבר."""
    out = []
    last_end = None
    for m in WORD.finditer(txt):
        a, b = m.start(), m.end()
        brk = last_end is not None and bool(BARRIER.search(txt[last_end:a]))
        last_end = b
        nxt = txt[b:b + 1]
        prv = txt[a - 1:a] if a else ''
        abbr = (nxt == '"' and txt[b + 1:b + 2] and 'א' <= txt[b + 1] <= 'ת') or                (prv == '"' and a >= 2 and 'א' <= txt[a - 2] <= 'ת')
        out.append((a, b, '#' if abbr else skel(m.group()), brk))
    return out


def _letters(toks, i, k):
    return sum(len(t[2]) for t in toks[i:i + k])


def _longest(toks, i):
    """הרצף הארוך ביותר שמתחיל במילה i של toks ותואם פסוק. מחזיר (אורך, פסוק, מקום)."""
    verses, bi = load()
    if i + 1 >= len(toks):
        return 0, None, None
    best = (0, None, None)
    cands = bi.get((toks[i][2], toks[i + 1][2]), [])
    if toks[i][2] in ('ה', 'ד'):
        cands = cands + bi.get(('הה', toks[i + 1][2]), [])
    for vi, p in cands:
        ws = verses[vi][3]
        k = 0
        while i + k < len(toks) and p + k < len(ws) and _eq(toks[i + k][2], ws[p + k])                 and not (k and toks[i + k][3]):
            k += 1
        if k > best[0]:
            best = (k, vi, p)
    return best


def _rare(toks, i):
    verses, bi = load()
    return len(bi.get((toks[i][2], toks[i + 1][2]), [])) <= RARE


def find_spans(txt, flagged):
    """txt - טקסט הפסקה; flagged - רשימת בוליאנים לכל תו (כבר בסגנון פסוק).
    מחזיר רשימת טווחים [{a, b, ref, kind}] שלא סומנו וראויים לסימון."""
    toks = _tokens(txt)
    if len(toks) < 2:
        return []
    verses, _ = load()
    found = []

    def covered(a, b):
        n = sum(1 for c in range(a, b) if flagged[c])
        return n >= max(1, (b - a) * 0.3)

    def best_in(lo, hi, need, rare_ok, anchored, min_letters=9):
        """הרצף הטוב ביותר בטווח מילים [lo, hi); anchored - חייב להתחיל בקרבת lo."""
        top = None
        for i in range(lo, hi):
            k, vi, p = _longest(toks, i)
            ok = (k >= need and _letters(toks, i, k) >= min_letters) or                  (rare_ok and k == 2 and _rare(toks, i) and _letters(toks, i, 2) >= 7)
            if ok:
                if anchored and i - lo > 2:
                    break
                if top is None or k > top[0]:
                    top = (k, i, vi, p)
        return top

    claimed = [False] * len(toks)

    def take(top, kind):
        k, i, vi, p = top
        # מילת חיבור בסוף הרצף ("ואומר") אינה חלק מן הפסוק: נחתכת
        while k > 3 and txt[toks[i + k - 1][0]:toks[i + k - 1][1]] in ('ואומר', 'ואמר', 'ואומרים', 'אומר'):
            k -= 1
        if any(claimed[i:i + k]):
            return
        a, b = toks[i][0], toks[i + k - 1][1]
        if covered(a, b):
            for c in range(i, i + k):
                claimed[c] = True
            return
        for c in range(i, i + k):
            claimed[c] = True
        bk, ch, v, _ = verses[vi]
        found.append({'a': a, 'b': b, 'ref': '%s %d:%d' % (bk, ch, v), 'kind': kind, 'n': k})

    # א. ציטוטים בגרשיים
    for m in QUOTE.finditer(txt):
        qa, qb = m.start(1), m.end(1)
        idx = [n for n, t in enumerate(toks) if t[0] >= qa and t[1] <= qb]
        if len(idx) < 2:
            continue
        lo, hi = idx[0], idx[-1] + 1
        before = txt[max(0, m.start() - 40):m.start()]
        has_intro = bool(INTRO.search(before + ' '))
        top = best_in(lo, hi, MIN_QUOTE, has_intro, False, 6)
        if top and top[0] >= max(2, int(0.7 * (hi - lo) + 0.5)):
            take(top, 'ציטוט')
    # ב. אחרי ביטוי פתיחה
    for m in INTRO.finditer(txt):
        after = m.end()
        idx = [n for n, t in enumerate(toks) if t[0] >= after]
        if len(idx) < 2:
            continue
        lo = idx[0]
        top = best_in(lo, min(len(toks) - 1, lo + 7), MIN_QUOTE, False, True, 10)
        if top:
            take(top, 'אחרי פתיחה')
    # ג. רצף ארוך
    i = 0
    while i < len(toks) - 1:
        if claimed[i]:
            i += 1
            continue
        k, vi, p = _longest(toks, i)
        if k >= MIN_FREE and _letters(toks, i, k) >= 14:
            take((k, i, vi, p), 'רצף ארוך')
            i += k
        else:
            i += 1
    found.sort(key=lambda x: x['a'])
    return found


def flags_of(block, ps_names):
    """רשימת בוליאנים לכל תו בפסקה: האם הוא בסגנון פסוק."""
    fl = []
    for r in block['runs']:
        v = r.get('cs') in ps_names
        fl.extend([v] * len(r['t']))
    return fl


def scan_blocks(blocks, role_of, ps_names):
    """סורק פסקאות גוף. מחזיר רשימת (אינדקס פסקה, טקסט, טווח)."""
    out = []
    for b in blocks:
        r = role_of(b)
        if not str(r).startswith('body'):
            continue
        txt = b['text']
        fl = flags_of(b, ps_names)
        if len(fl) != len(txt):
            continue                      # הטקסט והריצות אינם מיושרים - לא מנחשים
        for s in find_spans(txt, fl):
            out.append((b['i'], txt, s))
    return out


if __name__ == '__main__':
    sys.path.insert(0, os.path.join(ROOT, 'tools'))
    from docx2json import convert
    from styles_map import CS, role_of
    ps = {k for k, v in CS.items() if v == 'ps'}
    blocks = convert(sys.argv[1])
    res = scan_blocks(blocks, role_of, ps)
    print('נמצאו', len(res), 'פסוקים שלא סומנו')
    for i, txt, s in res[:int(sys.argv[2]) if len(sys.argv) > 2 else 40]:
        print('  %-18s %-10s %s' % (s['ref'], s['kind'], txt[s['a']:s['b']]))
