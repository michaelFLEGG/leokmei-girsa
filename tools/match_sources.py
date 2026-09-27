# -*- coding: utf-8 -*-
"""match_sources.py - מצמיד לכל יחידה בדף את מקטע הגמרא שממנו היא נלקחה.

ההצמדה נעשית בזמן הבנייה, לא בדפדפן: הלומד מקבל קובץ מוכן, ואין חישוב
בטלפון שלו.

איך: שני הצדדים מנורמלים (בלי ניקוד, גרש, פיסוק וסוגריים; יי=י, וו=ו),
ואז נמדדת חפיפת מילים משוקללת - מילה נדירה שוקלת יותר ממילה שכיחה,
לפי idf שנבנה מן הגמרא של המסכת עצמה. ההשוואה נעשית רק מול מקטעי
אותו דף, ולא מול המסכת כולה.

מתחת לסף אין הצמדה ואין כפתור "מקור". אין ניחוש: יחידה שלא הוצמדה
נספרת ומדווחת בלוח הבקרה.
"""
import re, math, unicodedata, collections

# ניקוד, טעמים, ומקף-מקרא
NIKUD = re.compile(r'[֑-ׇ]')
PUNCT = re.compile(r'[\'"׳״‘’“”()\[\]{}<>.,:;!?|/\\–—‐-―־*+=_~`^&%$#@]')
TAGS = re.compile(r'<[^>]+>')


def norm(s):
    """נרמול להשוואה בלבד. אינו נוגע בטקסט המוצג."""
    s = TAGS.sub(' ', s or '')
    s = unicodedata.normalize('NFKD', s)
    s = NIKUD.sub('', s)
    s = PUNCT.sub(' ', s)
    s = s.replace('\t', ' ')
    s = s.replace('יי', 'י').replace('וו', 'ו')
    # אותיות סופיות
    s = s.translate(str.maketrans('ךםןףץ', 'כמנפצ'))
    return re.sub(r'\s+', ' ', s).strip()


# מילות קישור שכיחות שאינן מלמדות דבר על הזיהוי
STOP = set('''ד ו ה ב ל מ כ ש את של אם או כי לא לו לה הוא היא הם אין יש
אלא אבל גם רק כל כן לכן מה מי זה זו אשר על עם עד כמו אחר בין תחת בלא
בלי אף ואף דאי אי הא הכי כך דהא ולא ואי וכן וכי'''.split())


def words(s):
    return [w for w in norm(s).split() if len(w) > 1 and w not in STOP]


def build_idf(pages_src):
    """idf מתוך הגמרא של המסכת עצמה: מילה נדירה מלמדת יותר."""
    df = collections.Counter()
    n = 0
    for p in pages_src.values():
        for g in p['gemara']:
            n += 1
            for w in set(words(g)):
                df[w] += 1
    return {w: math.log((n + 1) / (c + 0.5)) for w, c in df.items()}, n


def _vec(ws, idf, default):
    v = collections.Counter()
    for w in ws:
        v[w] = idf.get(w, default)
    return v


def score(a, b, idf, default):
    """קוסינוס על משקלי idf. מקטע ארוך אינו זוכה בזכות אורכו בלבד."""
    va, vb = _vec(a, idf, default), _vec(b, idf, default)
    if not va or not vb:
        return 0.0
    shared = set(va) & set(vb)
    if not shared:
        return 0.0
    num = sum(va[w] * vb[w] for w in shared)
    na = math.sqrt(sum(x * x for x in va.values()))
    nb = math.sqrt(sum(x * x for x in vb.values()))
    return num / (na * nb) if na and nb else 0.0


# הסף נקבע במדידה ולא בהערכה. נבדקו ידנית 20 הצמדות אקראיות בסף 0.30
# (20 נכונות) ועוד 12 ברצועה השולית 0.22-0.30 (12 נכונות), ולכן הורד
# הסף ל-0.22: הדיוק נשמר, והכיסוי עולה מ-46 ל-66 אחוזים.
THRESHOLD = 0.22
MIN_WORDS = 4


def attach(pages, src, threshold=THRESHOLD):
    """מצמיד ref לכל יחידה שנמצא לה מקטע. מחזיר סטטיסטיקה."""
    spages = src.get('pages') or {}
    idf, n = build_idf(spages)
    default = math.log((n + 1) / 0.5) if n else 1.0
    # מילות היחידה נאספות מן החלון ומכל פסקאות הגוף שלה
    st = {'units': 0, 'eligible': 0, 'matched': 0, 'nodaf': 0, 'low': 0,
          'scores': []}
    for p in pages:
        sp = spages.get((p.get('daf') or '').strip())
        for u in p['units']:
            if u['k'] in ('perek-num', 'perek-name', 'perek-range', 'perek-start',
                          'hadran', 'hatz'):
                continue
            st['units'] += 1
            txt = (u.get('a') or '') + ' ' + ' '.join(x[1] for x in u.get('l') or [])
            uw = words(txt)
            if len(uw) < MIN_WORDS:
                continue
            if not sp:
                st['nodaf'] += 1
                continue
            st['eligible'] += 1
            best, bi = 0.0, -1
            for i, g in enumerate(sp['gemara']):
                s = score(uw, words(g), idf, default)
                if s > best:
                    best, bi = s, i
            st['scores'].append(round(best, 3))
            if best >= threshold and bi >= 0:
                u['ref'] = sp['refs'][bi]
                u['rs'] = round(best, 3)
                st['matched'] += 1
            else:
                st['low'] += 1
    return st
