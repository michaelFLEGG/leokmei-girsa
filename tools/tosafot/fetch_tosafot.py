# -*- coding: utf-8 -*-
"""fetch_tosafot.py - מושך את תוספות על מסכת מספריא (מהדורת וילנא), דף אחרי דף.

ספריא מחזירה לכל דף רשימה לפי שורות הגמרא, ובתוכה רשימת דיבורים.
כאן הכול משוטח לרשימה אחת לפי סדר הדף, עם שורת הגמרא שאליה שייך הדיבור.
הפלט הגולמי נשמר ב-tosafot/raw/<slug>.json (לא נוגעים בטקסט).

    uv run python tools/tosafot/fetch_tosafot.py kiddushin 2a 14b
"""
import os, sys, json, io
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from fetch_sources import get
from sefaria_map import SEFARIA
ROOT = os.path.dirname(os.path.dirname(HERE))
API = 'https://www.sefaria.org/api/v3/texts/Tosafot_on_%s.%s?version=hebrew'


def dafim(a, b):
    """רשימת דפים מ-2a עד 14b, בסדר."""
    n1, s1 = int(a[:-1]), a[-1]
    n2, s2 = int(b[:-1]), b[-1]
    out = []
    n, s = n1, s1
    while True:
        out.append('%d%s' % (n, s))
        if (n, s) == (n2, s2):
            break
        if s == 'a':
            s = 'b'
        else:
            n, s = n + 1, 'a'
    return out


def main():
    slug, a, b = sys.argv[1], sys.argv[2], sys.argv[3]
    he = [k for k, v in __import__('build_all').SLUG.items() if v == slug][0]
    book = SEFARIA[he].replace(' ', '_')
    res = []
    for d in dafim(a, b):
        j = get(API % (book, d))
        if j is None:
            raise SystemExit('אין תוספות בספריא לדף %s' % d)
        vs = j.get('versions') or []
        if not vs:
            raise SystemExit('אין נוסח לדף %s' % d)
        txt = vs[0]['text']
        k = 0
        for li, line in enumerate(txt):
            segs = line if isinstance(line, list) else ([line] if line else [])
            for si, s in enumerate(segs):
                if not s or not s.strip():
                    continue
                k += 1
                res.append({'daf': d, 'line': li + 1, 'seg': si + 1, 'ref': 'Tosafot on %s %s:%d:%d' % (SEFARIA[he], d, li + 1, si + 1), 'html': s})
        print(d, k, file=sys.stderr)
    out = os.path.join(ROOT, 'tosafot', 'raw')
    os.makedirs(out, exist_ok=True)
    with io.open(os.path.join(out, slug + '.json'), 'w', encoding='utf-8') as f:
        json.dump({'slug': slug, 'from': a, 'to': b, 'source': 'Sefaria, Tosafot on %s, Vilna Edition' % SEFARIA[he], 'items': res}, f, ensure_ascii=False, indent=1)
    print('סה"כ', len(res), file=sys.stderr)


if __name__ == '__main__':
    main()
