# -*- coding: utf-8 -*-
"""font_ttf.py - המרת גופן עם קווי CFF (OpenType/PostScript) לקווי TrueType (פרומפט 78 ט, 22.11.2026).

הבעיה: Chrome (Skia) שומר ב-PDF גופני CFF כ-Type 3. בתי דפוס רבים פוסלים Type 3 בבדיקה המקדימה, והדפוס יוצא פחות
חד. נמדד ב"תענית - B5 - עם תוס' 20.11.pdf": שלושת גופני וילנא שהם CFF (BAWVilna-Bold, BA Vilna Light,
BATM Vilna ExtraBold) - Type 3, וכל גופני ה-TrueType (BAVilna-Regular, PFT Frank, FrankRuehl) - CID TrueType.

הפתרון: אותו גופן בדיוק, עם קווים ריבועיים (cu2qu, סטייה של עד יחידה אחת מתוך 1000). רוחב כל אות, טבלאות הפריסה
(ניקוד, ליגטורות) והשמות - בלי שינוי, ולכן שבירת השורות זהה. הקובץ נשאר באותו שם (הדפדפן מזהה לפי התוכן).
"""
import sys


def to_glyf(path, out=None, max_err=1.0):
    """ממיר במקום (או ל-out). מחזיר True אם הומר, False אם הגופן כבר TrueType."""
    from fontTools.ttLib import TTFont, newTable
    from fontTools.pens.cu2quPen import Cu2QuPen
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    f = TTFont(path)
    if 'CFF ' not in f:
        return False
    gs = f.getGlyphSet()
    order = f.getGlyphOrder()
    glyf = newTable('glyf'); glyf.glyphOrder = order; glyf.glyphs = {}
    for name in order:
        pen = TTGlyphPen(gs)
        gs[name].draw(Cu2QuPen(pen, max_err, reverse_direction=True))
        glyf[name] = pen.glyph()
    f['glyf'] = glyf
    f['loca'] = newTable('loca')
    head = f['head']; head.indexToLocFormat = 0; head.glyphDataFormat = 0
    maxp = newTable('maxp'); maxp.tableVersion = 0x00010000
    for k in ('maxZones', 'maxTwilightPoints', 'maxStorage', 'maxFunctionDefs', 'maxInstructionDefs',
              'maxStackElements', 'maxSizeOfInstructions', 'maxComponentElements'):
        setattr(maxp, k, 0)
    maxp.maxZones = 1; maxp.maxComponentDepth = 0
    f['maxp'] = maxp
    post = f['post']
    post.formatType = 2.0; post.extraNames = []; post.mapping = {}; post.glyphOrder = order
    del f['CFF ']
    if 'VORG' in f:
        del f['VORG']
    f.sfntVersion = '\x00\x01\x00\x00'
    f.recalcBBoxes = True
    f.save(out or path)
    return True


if __name__ == '__main__':
    for p in sys.argv[1:]:
        print(p, 'הומר' if to_glyf(p) else 'כבר TrueType')
