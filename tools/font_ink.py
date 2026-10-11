# -*- coding: utf-8 -*-
"""font_ink.py - גובה האותיות הנראה בפועל של גופן, ליחידת em.

סולם הכותרות אינו נקבע בנקודות נקובות: וילנא מודגש גדול לעין בהרבה
מפרנקריהל באותו גודל נקוב. לכן נמדד כאן, מתוך קובץ הגופן עצמו, גובה
תיבת הדיו של אותיות עבריות מייצגות - מן האות הגבוהה (ל) עד הנמוכה (ך ן
ף ץ) - והמקדמים נגזרים ממנו בבנייה.

זהו בדיוק מה ש-canvas measureText מחזיר ב-actualBoundingBox, ולכן סוכן
סריקת התצוגה מאמת את אותו מספר בדפדפן.
"""
import os

LETTERS = 'אבגדהוזחטיכךלמםנןסעפףצץקרשת'


def ink_per_em(path, letters=LETTERS, cache={}):
    key = (path, letters)
    if key in cache:
        return cache[key]
    from fontTools.ttLib import TTFont
    f = TTFont(path, fontNumber=0, lazy=True)
    upm = f['head'].unitsPerEm
    cmap = f.getBestCmap()
    gs = f.getGlyphSet()
    from fontTools.pens.boundsPen import BoundsPen
    lo, hi = None, None
    for ch in letters:
        gn = cmap.get(ord(ch))
        if not gn or gn not in gs:
            continue
        bp = BoundsPen(gs)
        gs[gn].draw(bp)
        if not bp.bounds:
            continue
        _, ymin, _, ymax = bp.bounds
        lo = ymin if lo is None else min(lo, ymin)
        hi = ymax if hi is None else max(hi, ymax)
    f.close()
    v = ((hi - lo) / upm) if (lo is not None) else 1.0
    cache[key] = v
    return v


if __name__ == '__main__':
    import sys, glob
    d = sys.argv[1] if len(sys.argv) > 1 else 'site/fonts'
    for p in sorted(glob.glob(os.path.join(d, '*'))):
        if p.lower().endswith(('.ttf', '.otf')):
            print('%-18s %.4f' % (os.path.basename(p), ink_per_em(p)))
