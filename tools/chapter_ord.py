# -*- coding: utf-8 -*-
"""chapter_ord.py - מספר הפרק מתוך כותרת ("פרק שני ..."). מקור אחד: build_site._ord_of קורא מכאן.
11.10.2026: הורחב לכל המספרים עד 24 (שבת: "פרק שמונה עשר", "פרק עשרים", "פרק אחד ועשרים"), ולמספור באותיות ("פרק א'", "פרק כ"ב")."""
import re

_ORD = {'ראשון': 1, 'שני': 2, 'שלישי': 3, 'רביעי': 4, 'חמישי': 5, 'שישי': 6, 'שביעי': 7, 'שמיני': 8,
        'תשיעי': 9, 'עשירי': 10}
_UNITS = {'אחד': 1, 'אחת': 1, 'שנים': 2, 'שתים': 2, 'שני': 2, 'שתי': 2, 'שלושה': 3, 'שלשה': 3, 'שלוש': 3, 'שלש': 3,
          'ארבעה': 4, 'ארבע': 4, 'חמשה': 5, 'חמישה': 5, 'חמש': 5, 'חמישי': 5, 'ששה': 6, 'שישה': 6, 'שש': 6,
          'שבעה': 7, 'שבע': 7, 'שמונה': 8, 'שמנה': 8, 'תשעה': 9, 'תשע': 9}
_TEN = {'עשר': 10, 'עשרה': 10}
_GEM = {'א': 1, 'ב': 2, 'ג': 3, 'ד': 4, 'ה': 5, 'ו': 6, 'ז': 7, 'ח': 8, 'ט': 9, 'י': 10, 'כ': 20}
_Q = '"\'״׳'
_NIKUD = re.compile('[֑-ׇ]')


def _gem(s):
    s = ''.join(c for c in s if c not in _Q)
    if not s or len(s) > 2 or any(c not in _GEM for c in s):
        return None
    if len(s) == 2 and not (_GEM[s[0]] >= 10 and _GEM[s[1]] < 10):
        return None
    return sum(_GEM[c] for c in s)


def chapter_ordinal(text):
    t = _NIKUD.sub('', text or '')
    m = re.search(r'פרק\s+(?:ה)?([א-ת' + _Q + r']+)(?:\s+([א-ת]+))?(?:\s+([א-ת]+))?', t)
    if not m:
        return None
    w1, w2, w3 = m.group(1), m.group(2), m.group(3)
    if w1 in _ORD:
        return _ORD[w1]
    # מספר בסדר "אחד ועשרים" / "שנים ועשרים"
    if w1 in _UNITS and w2 and w2.startswith('ו') and w2[1:] in ('עשרים',):
        return 20 + _UNITS[w1]
    if w1 in _UNITS and w2 in _TEN:
        return 10 + _UNITS[w1]
    if w1 in ('עשרים',):
        return 20
    if w1 in ('עשר', 'עשרה'):
        return 10
    # מספור באותיות: "א'", "י"ז", "כ"ב"
    g = _gem(w1)
    if g and (any(c in w1 for c in _Q) or len(w1) <= 2):
        return g
    return None


if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    for s in ['פרק שני  הישן', 'פרק י"א', 'הישן', 'פרק שמונה עשר - מפנין', 'פרק עשרים - תולין', 'פרק אחד ועשרים', 'פרק שנים ועשרים',
              'פרק שלוש ועשרים', "פרק א' - הכל ממירין", 'פרק ד', 'פרק ארבעה ועשרים', 'פרק חמשה עשר', 'פרק אחד עשר']:
        print(s, '->', chapter_ordinal(s))
