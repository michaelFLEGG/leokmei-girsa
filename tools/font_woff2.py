# -*- coding: utf-8 -*-
"""font_woff2.py - מייצר גרסת woff2 מקוצצת לכל גופן באתר (אחרי התיקון של font_unicode), כדי שהגולש יוריד כרבע מהמשקל.
הקיצוץ שומר את כל התווים שהאתר משתמש בהם: לטינית ולטינית-1, כל בלוק העברית (אותיות, ניקוד, טעמים), פיסוק כללי, חצים וצורות,
וצורות התצוגה העבריות; וכל תכונות הפריסה (ניקוד מוצמד, ליגטורות). למנהל רישיון מלא על משפחת BA - קיצוץ לשימוש באתר מותר.
הגופנים המקוריים (otf/ttf) נשארים כגיבוי: ה-CSS מציין קודם woff2 ואחריו את המקור.
דורש brotli (בשרת הפרסום: pip install brotli). בלעדיה - מדלג בקול והמקור נשאר בשימוש."""
import os
UNI = (list(range(0x20, 0x7f)) + list(range(0xa0, 0x100)) + list(range(0x590, 0x600)) + list(range(0x2000, 0x2070)) + [0x20aa, 0x2022]
       + list(range(0x2190, 0x2300)) + list(range(0x25a0, 0x2600)) + list(range(0xfb1d, 0xfb50)))


def run(fdir, names):
    try:
        from fontTools.ttLib import TTFont
        from fontTools import subset
        import brotli  # noqa: F401
    except Exception as e:
        print('אזהרה: אין brotli או fontTools, גופני woff2 לא נוצרו -', e); return 0
    n = 0
    for t in names:
        src = os.path.join(fdir, t)
        if not os.path.exists(src): continue
        dst = os.path.splitext(src)[0] + '.woff2'
        try:
            if os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(src): n += 1; continue
            o = subset.Options(); o.flavor = 'woff2'; o.layout_features = ['*']; o.notdef_outline = True; o.name_IDs = ['*']; o.hinting = False
            f = TTFont(src); s = subset.Subsetter(o); s.populate(unicodes=UNI); s.subset(f); f.flavor = 'woff2'; f.save(dst); n += 1
        except Exception as e:
            print('אזהרה: woff2 נכשל ל-', t, '-', str(e)[:100])
    print('גופני woff2: %d' % n)
    return n
