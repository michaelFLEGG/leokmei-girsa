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


def skel(w):
    """מפתח ליישור שאינו רגיש לכתיב מלא מול חסר: בלי ו' ובלי י'.
    מילה שכולה ו' ו-י' נשארת כפי שהיא."""
    k = key(w)
    s = k.replace('ו', '').replace('י', '')
    return s or k


MARKS = re.compile(r'[֑-ׇ]+')
VOWEL_HOLAM = 'ֹ'
SHURUK_DAGESH = 'ּ'
QUBUTS = 'ֻ'


def transfer(mine, src):
    """ניקוד המילה שבמקור על המילה שלו, כשההבדל ביניהן הוא רק כתיב מלא מול
    חסר (ו' או י' שנוספה או ירדה). לא משנה אות: סימן שישב על אות שאינה
    אצלו עובר לאות שלפניה, ואות שנוספה אצלו נשארת בלי סימן.
    מחזיר את המילה מנוקדת, או None כשאין התאמה בטוחה."""
    def groups(w):
        out = []
        for ch in w:
            if '֑' <= ch <= 'ׇ':
                if not out:
                    return None
                out[-1][1] += ch
            else:
                out.append([ch, ''])
        return out
    g = groups(src)
    m = [[c, ''] for c in letters(mine)]
    if not g or not m or len(letters(src)) == 0:
        return None
    A, B = [x[0] for x in m], [x[0] for x in g]
    sm = difflib.SequenceMatcher(None, A, B, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            for k in range(i2 - i1):
                m[i1 + k][1] = g[j1 + k][1]
        elif tag == 'delete':
            if any(c not in 'וי' for c in A[i1:i2]):
                return None
        elif tag == 'insert':
            # אותיות שיש במקור ואין אצלו: רק ו' או י', והסימן עובר אחורה
            if any(c not in 'וי' for c in B[j1:j2]) or i1 == 0:
                return None
            for k in range(j1, j2):
                mk, c = g[k][1], B[k]
                if not mk:
                    continue
                vow = MARKS.sub(lambda x: x.group(0), mk)
                if c == 'ו':
                    if SHURUK_DAGESH in mk and VOWEL_HOLAM not in mk:
                        mk = QUBUTS
                    elif VOWEL_HOLAM in mk:
                        mk = VOWEL_HOLAM
                    else:
                        return None
                if m[i1 - 1][1] and any(ch in m[i1 - 1][1] for ch in 'ְֱֲֳִֵֶַָֹֻ'):
                    return None
                m[i1 - 1][1] += mk
        else:
            return None
    # ו' שנוספה אצלו ואחריה בא ניקוד שישב על האות שלפניה: חולם/שורוק עוברים אליה
    for k in range(1, len(m)):
        if m[k][0] == 'ו' and not m[k][1] and A[k] == 'ו':
            prev = m[k - 1][1]
            if VOWEL_HOLAM in prev and k < len(m) - 0:
                m[k - 1][1] = prev.replace(VOWEL_HOLAM, '')
                m[k][1] = VOWEL_HOLAM
            elif QUBUTS in prev:
                m[k - 1][1] = prev.replace(QUBUTS, '')
                m[k][1] = SHURUK_DAGESH
    return ''.join(c + mk for c, mk in m)


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

    mine = [skel(x[4]) for x in spans]
    theirs = [skel(w) for w in source_words]
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
        if letters(w) != letters(s):
            # כתיב מלא מול חסר בלבד: ניקוד בהתאמה לכתיב שלו; אות אחרת
            # שונה - אין העתקה
            t = transfer(w, s)
            if t is None or letters(t) != letters(w):
                continue
            s = t
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


def plain_text(h):
    return _html.unescape(TAGS.sub('', h or ''))


QUOTES = '"\'׳״'


def eligible_bare(text):
    """אינדקסים (לפי סדר המילים) של מילים שאין בהן שום ניקוד ושמותר לנקד:
    לא ראשי תיבות או קיצורים (גרש או גרשיים בצמוד), ולא ציוני מקור
    שבסוגריים."""
    t = re.sub(r'\([^)]*\)', lambda m: ' ' * len(m.group(0)), text)
    t = re.sub(r'\[[^\]]*\]', lambda m: ' ' * len(m.group(0)), t)
    out = set()
    for i, m in enumerate(WORD.finditer(text)):
        w = m.group(0)
        if has_nikud(w) or t[m.start():m.end()].strip() == '' or len(w) == 1:
            continue          # אות בודדת: מספור (א. ב.) ולא מילה
        pre = t[m.start() - 1:m.start()] if m.start() else ''
        post = t[m.end():m.end() + 1]
        if (pre and pre in QUOTES) or (post and post in QUOTES):
            continue
        out.add(i)
    return out


def complete(pages, est):
    """משלים ניקוד משוער (nikud_generate) למילים שנשארו בלי ניקוד אחרי
    ההעתקה מן הגמרא. מילה מקבלת ניקוד רק כשאותיותיה זהות לגמרי, וכל
    מילה כזאת עטופה ב-nks, שמסומנת בקו תחתי אפור במצב מנהל בלבד."""
    st = {'est': 0, 'left': 0}
    for p in pages:
        for u in p['units']:
            if u.get('k') != 'm':
                continue
            lv = u.get('lv') or [[c, h] for c, h in u['l']]
            if len(lv) != len(u['l']):
                continue
            ch = False
            for pi in range(len(lv)):
                h = lv[pi][1]
                elig = eligible_bare(plain_text(h))
                if not elig:
                    continue
                words = (est or {}).get(plain_text(u['l'][pi][1])) or []
                tok = _tokens(h)
                idx = 0
                for t in tok:
                    if t[0] != 'txt':
                        continue
                    s, out, pos = t[1], [], 0
                    for m in WORD.finditer(s):
                        i, idx = idx, idx + 1
                        if i not in elig:
                            continue
                        e = words[i] if i < len(words) else ''
                        if e and has_nikud(e) and letters(e) == letters(m.group(0)):
                            out.append(s[pos:m.start()] + '<span class="nks">' + e + '</span>')
                            pos = m.end()
                            st['est'] += 1
                        else:
                            st['left'] += 1
                    if pos:
                        t[1] = ''.join(out) + s[pos:]
                new = ''.join(x[1] for x in tok)
                if new != h:
                    lv[pi] = [lv[pi][0], new]
                    ch = True
            if ch:
                u['lv'] = lv
    return st


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


def apply(pages, src, est=None):
    """מנקד את כל המשניות. מחזיר סטטיסטיקה."""
    st = _apply(pages, src)
    st.update(complete(pages, est))
    return st


def _apply(pages, src):
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
