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


def add_unicode_cmap(f):
    """מוסיף לגופן פתוח טבלת יוניקוד המכוונת אל גליפי הקידוד הישן.
    מחזיר כמה אותיות מופו."""
    from fontTools.ttLib.tables._c_m_a_p import CmapSubtable
    legacy = None
    for t in f['cmap'].tables:
        if t.platformID == 1 and t.platEncID == 0:
            legacy = t.cmap; break
    if legacy is None:
        for t in f['cmap'].tables:
            if t.platformID == 3 and t.platEncID == 0:
                # טבלת סימנים: המשבצות ב-0xF000 ומעלה
                legacy = {k - 0xF000: v for k, v in t.cmap.items()}; break
    if legacy is None:
        return 0

    uni = {}
    # פיסוק וספרות: אותם קודים בדיוק, ולכן הם מועברים כמות שהם
    for c in range(0x20, 0x7F):
        if c in legacy:
            uni[c] = legacy[c]
    n = 0
    for i in range(HEB_COUNT):
        g = legacy.get(LEGACY_FIRST + i)
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
    return n


def add_hebrew_cmap(src, dst):
    """גרסת קובץ-לקובץ, לשימוש משורת הפקודה."""
    from fontTools.ttLib import TTFont
    f = TTFont(src, fontNumber=0)
    n = add_unicode_cmap(f)
    f.save(dst); f.close()
    return n


def fix_wide_glyphs(f, limit=3.0):
    """מתקן רוחב פסיעה מופרך. מחזיר רשימת (גליף, רוחב ישן, רוחב חדש).

    ב-PFT_Frank (שני המשקלים) רוחב הפסיעה של periodcentered - הנקודה
    האמצעית שבעל הפרויקט משתמש בה כתבליט - הוא 64.8 em. מילה שיש בה
    תו כזה נמתחת לרוחב של כמעט מטר ואינה נשברת, והטקסט גולש מן העמוד.
    סוכן סריקת התצוגה גילה זאת ביומא ו:.

    הרוחב החדש נגזר מן הגליף עצמו: רוחב הדיו שלו ועוד שוליים צרים
    משני צדדיו. גליף בלי מתאר מקבל רבע em.
    """
    from fontTools.pens.boundsPen import BoundsPen
    upm = f['head'].unitsPerEm
    hm = f['hmtx'].metrics
    gs = f.getGlyphSet()
    side = int(upm * 0.04)
    fixed = []
    for g, (w, lsb) in list(hm.items()):
        if w <= upm * limit:
            continue
        ink = None
        try:
            bp = BoundsPen(gs)
            gs[g].draw(bp)
            ink = bp.bounds
        except Exception:
            ink = None
        new = int(round(ink[2] - ink[0])) + side * 2 if ink else int(upm * 0.25)
        new = max(new, side * 2)
        hm[g] = (new, side if ink else lsb)
        fixed.append((g, w, new))
    if fixed:
        f['hhea'].advanceWidthMax = max(v[0] for v in hm.values())
    return fixed


def repair(src, dst):
    """קורא את הגופן, מתקן אותו, ושומר לאתר. מחזיר דוח בשורה אחת, או None.

    הכול בפתיחה אחת ובשמירה אחת, ולא בסיבובים על אותו קובץ."""
    from fontTools.ttLib import TTFont
    notes = []
    f = TTFont(src, fontNumber=0)
    try:
        has_uni = any(any(HEB_FIRST <= k <= HEB_FIRST + 40 for k in t.cmap)
                      for t in f['cmap'].tables)
        if not has_uni:
            n = add_unicode_cmap(f)
            if n:
                notes.append('נוספה טבלת יוניקוד ל-%d אותיות' % n)
        wide = fix_wide_glyphs(f)
        if wide:
            notes.append('רוחב פסיעה מופרך תוקן ב-%d גליפים (%s)'
                         % (len(wide), ', '.join(g for g, _, _ in wide[:4])))
        f.save(dst)
    finally:
        f.close()
    return '; '.join(notes) if notes else None


if __name__ == '__main__':
    import sys
    src, dst = sys.argv[1], sys.argv[2]
    print('מופו', add_hebrew_cmap(src, dst), 'אותיות')
