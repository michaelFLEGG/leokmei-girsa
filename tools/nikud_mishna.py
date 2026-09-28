# -*- coding: utf-8 -*-
"""nikud_mishna.py - מנקד את המשניות מן הגמרא המנוקדת שהוצמדה להן.

הניקוד אינו נכתב מחדש ואינו נשען על מילון: אותה מילה מנוקדת אחרת
במקומות שונים. הוא מועתק **לפי מקום** - רצף המילים של המשנה מיושר
לרצף המילים המנוקדות של הדף, ביישור רצפים (difflib), ורק מילה שאותיותיה
זהות לגמרי למילה שמולה מקבלת את ניקודה.

מה שאסור, ונשמר כאן בקפדנות:
- אין משנים אף אות של בעל הפרויקט. ניקוד מועתק רק כשרצף האותיות זהה
  בדיוק; כתיב מלא מול חסר, קיצורים, ראשי תיבות ותוספות שלו - נשארים
  כמות שהם, בלי ניקוד.
- ניקוד שכבר קיים אצלו במילה אינו נדרס לעולם.
- הניקוד יושב בשכבה נפרדת (u['lv']) ולעולם אינו נכתב לקובצי הוורד.
  נוסח הוורד (u['l']) הוא שנשאר לחיפוש, לתוכן העניינים ולעריכה.

המקור: William Davidson, ברישיון CC BY-NC. בעל הפרויקט הכריע (28.9.2026)
שהספר הוא הורדה לשימוש אישי ואינו שימוש מסחרי, ולכן הניקוד מוצג גם
בהדפסה. שורת הייחוס מופיעה בדף.
"""
import re, difflib, html as _html

NIKUD = re.compile(r'[֑-ׇ]')
TAGS = re.compile(r'<[^>]+>')
# מילה = רצף אותיות עבריות, עם הניקוד שעליהן. גרש, גרשיים, ספרות
# וסימני פיסוק הם גבול מילה, ולכן ראשי תיבות אינם מתאימים לשום מילה
# שבמקור - וזו בדיוק הכוונה.
WORD = re.compile(r'[א-ת][א-ת֑-ׇ]*')
FINALS = str.maketrans('ךםןףץ', 'כמנפצ')


def letters(w):
    """רק האותיות, בלי ניקוד."""
    return NIKUD.sub('', w)


def key(w):
    """מפתח ליישור בלבד: בלי ניקוד, בלי אותיות סופיות, יי=י ו-וו=ו."""
    s = letters(w).translate(FINALS)
    return s.replace('יי', 'י').replace('וו', 'ו')


def has_nikud(w):
    return bool(NIKUD.search(w))


def src_words(text):
    """מילות המקור המנוקדות, לפי סדרן."""
    return WORD.findall(TAGS.sub(' ', text or ''))


def _tokens(h):
    """מפצל HTML לרצף: ('tag', s) שאינו נוגעים בו, ו-('txt', s)."""
    out, i = [], 0
    for m in TAGS.finditer(h or ''):
        if m.start() > i:
            out.append(['txt', h[i:m.start()]])
        out.append(['tag', m.group(0)])
        i = m.end()
    if i < len(h or ''):
        out.append(['txt', h[i:]])
    return out


def _para_words(tok):
    """מאתר את המילים שבתוך קטעי הטקסט. מחזיר רשימת (ti, start, end, word)."""
    out = []
    for ti, (kind, s) in enumerate(tok):
        if kind != 'txt':
            continue
        for m in WORD.finditer(s):
            out.append((ti, m.start(), m.end(), m.group(0)))
    return out


def vocalize_unit(paras, source_words):
    """מקבל רשימת [class, html] של יחידה, ומחזיר רשימה מנוקדת + מונים.

    היישור נעשה על היחידה כולה בבת אחת, ולא על כל פסקה לחוד, כדי
    שמשנה שנחתכה לשתי פסקאות תיושר כרצף אחד."""
    toks = [_tokens(h) for _, h in paras]
    spans = []            # (pi, ti, a, b, word)
    for pi, t in enumerate(toks):
        for ti, a, b, w in _para_words(t):
            spans.append((pi, ti, a, b, w))
    if not spans or not source_words:
        return None, 0, len(spans)

    mine = [key(x[4]) for x in spans]
    theirs = [key(w) for w in source_words]
    sm = difflib.SequenceMatcher(None, mine, theirs, autojunk=False)
    pair = {}
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            for k in range(i2 - i1):
                pair[i1 + k] = j1 + k
        elif tag == 'replace' and (i2 - i1) == (j2 - j1):
            # גוש באותו אורך: מותר לזווג לפי מקום, ובדיקת האותיות
            # שלהלן תדחה כל זוג שאינו זהה ממש.
            for k in range(i2 - i1):
                pair[i1 + k] = j1 + k

    done = 0
    repl = {}             # (pi, ti) -> רשימת (a, b, new)
    for i, (pi, ti, a, b, w) in enumerate(spans):
        j = pair.get(i)
        if j is None:
            continue
        s = source_words[j]
        if has_nikud(w):              # ניקוד שלו - לעולם אינו נדרס
            continue
        if not has_nikud(s):
            continue
        if letters(w) != letters(s):  # אות אחת שונה - אין העתקה
            continue
        repl.setdefault((pi, ti), []).append((a, b, s))
        done += 1
    if not done:
        return None, 0, len(spans)

    for (pi, ti), lst in repl.items():
        s = toks[pi][ti][1]
        for a, b, new in sorted(lst, reverse=True):
            s = s[:a] + new + s[b:]
        toks[pi][ti][1] = s
    out = [[paras[pi][0], ''.join(x[1] for x in toks[pi])] for pi in range(len(paras))]
    return out, done, len(spans)


GEM_OPEN = re.compile(r'^\s*(?:<b>)?\s*(?:גמ|מתני)')


def daf_words(spages, daf, nxt=None):
    """מילות הגמרא המנוקדת של הדף, ואחריו הדף הבא - שמשנה עלולה
    להימשך אליו. הסדר נשמר, ולכן היישור מוצא את הגוש הנכון."""
    out = []
    for d in (daf, nxt):
        p = spages.get((d or '').strip())
        if not p:
            continue
        for g in p['gemara']:
            out.extend(src_words(g))
    return out


def apply(pages, src):
    """מנקד את כל המשניות. מחזיר סטטיסטיקה."""
    spages = (src or {}).get('pages') or {}
    if not spages:
        return {'mishnayot': 0, 'voc': 0, 'words': 0, 'wdone': 0}
    order = [p.get('daf') for p in pages]
    st = {'mishnayot': 0, 'voc': 0, 'words': 0, 'wdone': 0}
    for idx, p in enumerate(pages):
        nxt = order[idx + 1] if idx + 1 < len(order) else None
        sw = None
        for u in p['units']:
            if u.get('k') != 'm':
                continue
            st['mishnayot'] += 1
            if sw is None:
                sw = daf_words(spages, p.get('daf'), nxt)
            lv, done, total = vocalize_unit(u.get('l') or [], sw)
            st['words'] += total
            if lv:
                u['lv'] = lv
                st['wdone'] += done
                st['voc'] += 1
    return st
