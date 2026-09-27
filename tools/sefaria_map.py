# -*- coding: utf-8 -*-
"""sefaria_map.py - שמות המסכתות בספריא, והמרה בין ציון דף עברי למספור שלה."""

# שם המסכת אצלנו, ושמה בספריא. נכתב במפורש ולא נגזר מן ה-slug, כדי
# ששינוי ב-slug לא ישבור בשקט את המשיכה.
SEFARIA = {
    'ברכות': 'Berakhot', 'שבת': 'Shabbat', 'עירובין': 'Eruvin', 'פסחים': 'Pesachim',
    'שקלים': 'Shekalim', 'יומא': 'Yoma', 'סוכה': 'Sukkah', 'ביצה': 'Beitzah',
    'ראש השנה': 'Rosh Hashanah', 'תענית': 'Taanit', 'מגילה': 'Megillah',
    'מועד קטן': 'Moed Katan', 'חגיגה': 'Chagigah', 'יבמות': 'Yevamot',
    'כתובות': 'Ketubot', 'נדרים': 'Nedarim', 'נזיר': 'Nazir', 'סוטה': 'Sotah',
    'גיטין': 'Gittin', 'קידושין': 'Kiddushin', 'בבא קמא': 'Bava Kamma',
    'בבא מציעא': 'Bava Metzia', 'בבא בתרא': 'Bava Batra', 'סנהדרין': 'Sanhedrin',
    'מכות': 'Makkot', 'שבועות': 'Shevuot', 'עבודה זרה': 'Avodah Zarah',
    'הוריות': 'Horayot', 'זבחים': 'Zevachim', 'מנחות': 'Menachot', 'חולין': 'Chullin',
    'בכורות': 'Bekhorot', 'ערכין': 'Arakhin', 'תמורה': 'Temurah',
    'כריתות': 'Keritot', 'מעילה': 'Meilah', 'תמיד': 'Tamid', 'נדה': 'Niddah',
}

GEM = {'א': 1, 'ב': 2, 'ג': 3, 'ד': 4, 'ה': 5, 'ו': 6, 'ז': 7, 'ח': 8, 'ט': 9,
       'י': 10, 'כ': 20, 'ל': 30, 'מ': 40, 'נ': 50, 'ס': 60, 'ע': 70, 'פ': 80,
       'צ': 90, 'ק': 100, 'ר': 200, 'ש': 300, 'ת': 400,
       'ך': 20, 'ם': 40, 'ן': 50, 'ף': 80, 'ץ': 90}


def heb_to_num(t):
    """גימטריה של ציון דף עברי, בלי סימני העמוד."""
    t = (t or '').strip().rstrip('.:').replace('"', '').replace("'", '')
    t = t.replace('״', '').replace('׳', '').strip()
    n = sum(GEM.get(c, 0) for c in t)
    return n or None


def heb_to_ref(daf):
    """'כב:' -> '22b'. מחזיר None אם אין ציון ברור."""
    if not daf:
        return None
    n = heb_to_num(daf)
    if not n:
        return None
    return '%d%s' % (n, 'b' if daf.strip().endswith(':') else 'a')


def num_to_heb(n):
    out = ''
    for val, ch in ((400, 'ת'), (300, 'ש'), (200, 'ר'), (100, 'ק'), (90, 'צ'), (80, 'פ'),
                    (70, 'ע'), (60, 'ס'), (50, 'נ'), (40, 'מ'), (30, 'ל'), (20, 'כ'),
                    (10, 'י'), (9, 'ט'), (8, 'ח'), (7, 'ז'), (6, 'ו'), (5, 'ה'),
                    (4, 'ד'), (3, 'ג'), (2, 'ב'), (1, 'א')):
        while n >= val:
            out += ch
            n -= val
    return out.replace('יה', 'טו').replace('יו', 'טז')


def ref_to_heb(ref):
    """'22b' -> 'כב:'"""
    n = int(ref[:-1])
    return num_to_heb(n) + (':' if ref[-1] == 'b' else '.')
