# -*- coding: utf-8 -*-
"""font_unicode.py - מוסיף טבלת יוניקוד לגופן עברי מן הדור הישן.

‏DBSVILNA.TTF (Guttman Vilna), הגופן שבעל הפרויקט בחר לציוני הדף, הוא
גופן מקודד-סימנים: אין בו אף אות עברית ביוניקוד. האותיות יושבות במשבצות
של אותיות לטיניות מנוקדות (א=agrave ... ת=uacute), כמנהג הגופנים העבריים
של שנות התשעים.

לכן בדפדפן לא נעשה בו שימוש כלל: כל ציוני הדף נצבעו בגופן החלופי
(BA Vilna) בלי שאיש ידע. זהו כישלון שקט, וסוכן סריקת התצוגה גילה אותו.

התיקון אינו נוגע בטקסט - טקסט שנשתנה היה שובר חיפוש, העתקה ועיגון
עריכות. הוא נוגע בגופן: נוספת לו טבלת cmap של יוניקוד, שמכוונת את
א-ת אל אותם גליפים עצמם. הטקסט באתר נשאר עברית תקנית.
"""
import os

# הקידוד הישן: 27 אותיות עבריות רצופות מ-0xE0, ככתיב cp1255 ומקבילותיו.
LEGACY_FIRST = 0xE0
HEB_FIRST = 0x05D0
HEB_COUNT = 27          # א עד ת, כולל האותיות הסופיות שבתוך הרצף


def needs_patch(path):
    """האם בגופן חסרות אותיות עבריות ביוניקוד."""
    from fontTools.ttLib import TTFont
    f = TTFont(path, fontNumber=0, lazy=True)
    try:
        for t in f['cmap'].tables:
            if any(HEB_FIRST <= k <= HEB_FIRST + 40 for k in t.cmap):
                return False
        return True
    finally:
        f.close()


def add_hebrew_cmap(src, dst):
    """מעתיק את הגופן ומוסיף לו טבלת יוניקוד. מחזיר כמה אותיות מופו."""
    from fontTools.ttLib import TTFont
    from fontTools.ttLib.tables._c_m_a_p import CmapSubtable
    f = TTFont(src, fontNumber=0)
    legacy = None
    for t in f['cmap'].tables:
        if t.platformID == 1 and t.platEncID == 0:
            legacy = t; break
    if legacy is None:
        for t in f['cmap'].tables:
            if t.platformID == 3 and t.platEncID == 0:
                # טבלת סימנים: המשבצות ב-0xF000 ומעלה
                legacy = type('L', (), {'cmap': {k - 0xF000: v for k, v in t.cmap.items()}})()
                break
    if legacy is None:
        f.save(dst); f.close(); return 0

    uni = {}
    # פיסוק וספרות: אותם קודים בדיוק, ולכן הם מועברים כמות שהם
    for c in range(0x20, 0x7F):
        if c in legacy.cmap:
            uni[c] = legacy.cmap[c]
    n = 0
    for i in range(HEB_COUNT):
        g = legacy.cmap.get(LEGACY_FIRST + i)
        if g:
            uni[HEB_FIRST + i] = g; n += 1

    # טבלת הסימנים מוסרת: בנוכחותה מטפל הדפדפן בגופן כגופן-סמלים,
    # ומנסה 0xF000 + התו במקום לקרוא את טבלת היוניקוד.
    f['cmap'].tables = [t for t in f['cmap'].tables
                        if not (t.platformID == 3 and t.platEncID == 0)]
    sub = CmapSubtable.newSubtable(4)
    sub.platformID, sub.platEncID, sub.language = 3, 1, 0
    sub.cmap = uni
    f['cmap'].tables.append(sub)
    f.save(dst)
    f.close()
    return n


if __name__ == '__main__':
    import sys
    src, dst = sys.argv[1], sys.argv[2]
    print('מופו', add_hebrew_cmap(src, dst), 'אותיות')
