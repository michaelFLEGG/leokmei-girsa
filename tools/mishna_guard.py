# -*- coding: utf-8 -*-
"""mishna_guard.py - שומר תיבת המשנה ובודק המשניות (פרומפט 77, 22.11.2026).

מכני לגמרי, בלי בינה מלאכותית. מקור האמת: data/mishna/<slug>.json (ספריא, מנוקד).

א. כלל ברזל לתיבת משנה: שום עריכה אוטומטית (סכם, קיפול, struct, החלה בבנייה) אינה מחליפה
   פסקה בסגנון משנה בטקסט שאינו נמצא במשניות של המסכת. מותר: תיקון קל (דמיון גבוה לנוסח הקודם),
   או נוסח שנמצא במשניות. guard(slug, was, now) מחזיר (מותר?, סיבה).
ב. בודק המשניות: coverage(slug, text, chapter=None) - כמה מן הטקסט נמצא במשניות (0..1).
   מנורמל: בלי ניקוד וטעמים, בלי פיסוק, ראשי תיבות נפוצים נפתחים, כתיב מלא/חסר מקורב.

אותה לוגיקה בדיוק נמצאת ב-JS (tools/build_site.py, mgGuard) לעריכות שמגיעות מן השרת בדפדפן.
"""
import os, re, json, io, difflib

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MDIR = os.path.join(HERE, 'data', 'mishna')

# ראשי תיבות נפוצים במשנה ובלשון האתר. הפתיחה היא למילים, כדי שההשוואה תהיה מילה מול מילה.
ABBR = {
    'ר': 'רבי', "ר'": 'רבי', 'רא': 'רבי אליעזר', 'ריה': 'רבי יהודה', 'ריו': 'רבי יוסי',
    'רש': 'רבי שמעון', 'רע': 'רבי עקיבא', 'רמ': 'רבי מאיר', 'ריש': 'רבי ישמעאל',
    'בש': 'בית שמאי', 'בה': 'בית הלל', 'עג': 'על גבי', 'אעפ': 'אף על פי', 'אעפי': 'אף על פי',
    'אא': 'אלא אם', 'אאכ': 'אלא אם כן', 'רהר': 'רשות הרבים', 'רה': 'רשות הרבים',
    'רהי': 'רשות היחיד', 'ד': 'ארבע', 'דא': 'ארבע אמות', 'י': 'עשרה', 'טפ': 'טפחים',
    'ככ': 'כל כך', 'אע': 'אף על', 'ת': 'תלמוד', 'מ': 'מאיר', 'רג': 'רבן גמליאל',
    'ריבז': 'רבי יוחנן בן זכאי', 'רט': 'רבי טרפון', 'רא"ש': 'רבי אלעזר', 'כו': 'וכולי',
}
_NIK = re.compile('[֑-ׇ]')
_PUN = re.compile('[^א-ת\\s"\'״׳]')


def norm_words(t):
    t = _NIK.sub('', t or '')
    t = re.sub(r'<[^>]+>', ' ', t)
    t = t.replace('״', '"').replace('׳', "'").replace('־', ' ').replace('-', ' ')
    t = _PUN.sub(' ', t)
    out = []
    for w in t.split():
        if '"' in w or "'" in w:
            k = w.replace('"', '').replace("'", '')
            if k in ABBR:
                out.extend(ABBR[k].split()); continue
            # קידומת + ר"ת: ובש"א, כר"מ
            if len(k) > 2 and k[0] in 'ובכלמהש' and k[1:] in ABBR:
                out.extend(ABBR[k[1:]].split()); continue
            w = k
        out.append(_light(w))
    return [w for w in out if w]


def _light(w):
    """כתיב מלא/חסר מקורב: בלי ו' וי' באמצע מילה (לא בראשה ולא בסופה)."""
    if len(w) <= 3:
        return w
    return w[0] + re.sub('[וי]', '', w[1:-1]) + w[-1]


_CACHE = {}


def load(slug):
    if slug in _CACHE:
        return _CACHE[slug]
    p = os.path.join(MDIR, slug + '.json')
    if not os.path.exists(p):
        _CACHE[slug] = None
        return None
    d = json.load(io.open(p, encoding='utf-8'))
    chs = []
    for ch in d.get('chapters') or []:
        ms = [norm_words(m) for m in ch]
        chs.append(ms)
    allbig = set()
    chbig = []
    for ms in chs:
        b = set()
        for w in ms:
            b.update(zip(w, w[1:]))
        chbig.append(b)
        allbig |= b
    _CACHE[slug] = {'chapters': chs, 'chbig': chbig, 'allbig': allbig,
                    'allw': set(x for ms in chs for w in ms for x in w)}
    return _CACHE[slug]


def coverage(slug, text, chapter=None):
    """חלק הזוגות (מילה, מילה) של הטקסט שנמצאים במשניות (בפרק, או בכל המסכת). None - אין משניות."""
    M = load(slug)
    if M is None:
        return None
    w = norm_words(text)
    if len(w) < 2:
        return 1.0 if (not w or w[0] in M['allw']) else 0.0
    big = list(zip(w, w[1:]))
    S = M['chbig'][chapter - 1] if chapter and 0 < chapter <= len(M['chbig']) else M['allbig']
    return sum(1 for b in big if b in S) / float(len(big))


def similar(a, b):
    a, b = ' '.join(norm_words(a)), ' '.join(norm_words(b))
    if not a and not b:
        return 1.0
    return difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()


SIM_MIN = 0.5       # תיקון או ניסוח מחדש של אותה שורה (נמדד: עריכת מנהל בבכורות נז: 0.64, ברייתא זרה בשבת ק. 0.16, שורת גמרא בבכורות ס. 0.34)
COV_MIN = 0.3       # הנוסח החדש נמצא במשניות (נמדד: ברייתא זרה 0.07, עריכת מנהל לגיטימית שהוסיפה ביאור 0.40)


def guard(slug, was, now):
    """(מותר?, סיבה) לעריכה שמחליפה את תוכן פסקת משנה."""
    if not (now or '').strip():
        return True, 'מחיקה'           # מחיקה נבדקת במקום אחר (אינה מכניסה טקסט זר)
    s = similar(was, now)
    if s >= SIM_MIN:
        return True, 'תיקון קל (%.2f)' % s
    c = coverage(slug, now)
    if c is None:
        return True, 'אין משניות למסכת'
    if c >= COV_MIN:
        return True, 'הנוסח נמצא במשניות (%.2f)' % c
    return False, 'הנוסח החדש אינו במשניות המסכת (כיסוי %.2f) ושונה מן הקודם (דמיון %.2f)' % (c, s)
