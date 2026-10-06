# -*- coding: utf-8 -*-
"""chapter_ord.py - מספר הפרק מתוך כותרת ("פרק שני ..."). זהה לחישוב שב-build_site.py (_ord_of)."""
import re

_ORD = {'ראשון': 1, 'שני': 2, 'שלישי': 3, 'רביעי': 4, 'חמישי': 5, 'שישי': 6, 'שביעי': 7, 'שמיני': 8,
        'תשיעי': 9, 'עשירי': 10}
_ORD2 = {'יא': 11, 'יב': 12, 'יג': 13, 'יד': 14, 'טו': 15, 'טז': 16, 'אחד עשר': 11, 'שנים עשר': 12,
         'שלושה עשר': 13, 'ארבעה עשר': 14, 'חמישה עשר': 15, 'שישה עשר': 16}
_Q = '"\'״׳'
_RX1 = re.compile(r'פרק\s+(ראשון|שני|שלישי|רביעי|חמישי|שישי|שביעי|שמיני|תשיעי|עשירי)')
_RX2 = re.compile(r'פרק\s+(?:ה)?(י[' + _Q + r']?[א-ו]|אחד עשר|שנים עשר|שלושה עשר|ארבעה עשר|חמישה עשר|שישה עשר)')
_NIKUD = re.compile('[֑-ׇ]')


def chapter_ordinal(text):
    t = _NIKUD.sub('', text or '')
    m = _RX1.search(t)
    if m:
        return _ORD[m.group(1)]
    m = _RX2.search(t)
    if m:
        v = m.group(1)
        for q in _Q:
            v = v.replace(q, '')
        return _ORD2.get(v)
    return None


if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    print(chapter_ordinal('פרק שני  הישן'), chapter_ordinal('פרק י"א'), chapter_ordinal('הישן'))
