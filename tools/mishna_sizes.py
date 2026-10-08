# -*- coding: utf-8 -*-
"""mishna_sizes.py - יחסי הגדלים של המשנה בהגדרות הסגנון של קובץ ורד (6.10.2026).

הכלל הקבוע (ראה styles_map.py): הבסיס הוא גודל פסקת המשנה הרגילה M, והשאר נגזר
ממנו ביחס, ולא בערך קבוע:
    משנה (פסקה, וסגנונות התו שמלווים אותה)      = M
    ד"ה משנה (פסקה ותו)                         = M
    נושא משנה (תו; משקל שונה בלבד)               = M
    תנאי המשנה (תו), "תנאי משנה" הישן             = M - 2 נקודות
    הסבר במשנה (תו)                              = M - 3 נקודות (7.10.2026; היה M - 1)
    נושא (פסקה)                                  <= M (אינו גדול מד"ה משנה)

סגנון תו בוורד אינו משתנה לפי ההקשר ואינו נגזר מסגנון הפסקה, ולכן היחס נשמר כאן
בהגדרות הסגנון עצמן (sz ו-szCs יחד: העברית נמדדת ב-szCs). הרצה חוזרת בטוחה:
היא קוראת את M הנוכחי ומיישרת את הנגזרים אליו.

העלאת המשנה בשתי נקודות (raise=True) נעשית פעם אחת בלבד: רק כש-M הנוכחי הוא
8 או 9 נקודות (הגודל שהיה בכל הקבצים). מ-10 נקודות ומעלה נחשב שכבר הועלה.

    uv run --with lxml python tools/mishna_sizes.py <קובץ.docx> [--raise]    (הדפסת תכנית בלבד)
"""
import os, sys, re, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lxml import etree
from styles_map import (ROLE, TANAI_NAME, TANAI_LEGACY, HALF, MISHNA_RAISE_PT, TANAI_BELOW_PT, HS_BELOW_PT)

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
ns = {'w': W[1:-1]}

# סגנונות הפסקה: לפי התפקיד שבמפה, ובלי "משנה בצד" (תווית מסילה, תפקיד skip)
MISHNA_AS_TANAI_PARA = {'תנאי משנה'}              # פסקה שכולה סגנון תנאים: גודל תנאים
DH_PARA_EXTRA = {'משניות כותרת'}
NOSE_AT_MISHNA_SIZE = {'נושא במשנה'}              # נושא בגודל המשנה (מגילה)

# סגנונות תו: בגודל המשנה / בגודל התנאים / בגודל ההסבר
CHAR_M = {'משניות תו', 'חלק משנה מודגש תו', 'חלק משנה מודגשת תו', 'תחילת משניות תו',
          'נושא משנה', 'נושא משנה תו', 'נושא במשנה תו', 'משניות כותרת תו',
          "ד''ה משנה תו", "משנה ד''ה תו", "ד''ה משנה -2תו"}
CHAR_T = {TANAI_NAME, TANAI_NAME + ' תו', TANAI_LEGACY, TANAI_LEGACY + ' תו', 'תנאי משנה תו',
          'אמוראי משנה תו', "תנאים בד''ה משנה תו"}
CHAR_H = {'הסבר במשנה', 'הסבר במשנה תו'}

# סדר האלמנטים בתוך w:rPr לפי הסכמה, עד sz (כל מה שלפניו)
_BEFORE_SZ = ('rStyle', 'rFonts', 'b', 'bCs', 'i', 'iCs', 'caps', 'smallCaps', 'strike', 'dstrike', 'outline',
              'shadow', 'emboss', 'imprint', 'noProof', 'snapToGrid', 'vanish', 'webHidden', 'color', 'spacing',
              'w', 'kern', 'position')


def _styles(root):
    out = {}
    for st in root.findall('w:style', ns):
        nm = st.find('w:name', ns)
        out[st.get(W + 'styleId')] = (st, nm.get(W + 'val') if nm is not None else '')
    return out


def eff(styles, sid, tag, dflt=None):
    n = 0
    while sid and sid in styles and n < 30:
        st = styles[sid][0]
        e = st.find('w:rPr/w:' + tag, ns)
        if e is not None:
            return int(e.get(W + 'val'))
        b = st.find('w:basedOn', ns)
        sid = b.get(W + 'val') if b is not None else None
        n += 1
    return dflt


def _set(rpr, tag, val):
    e = rpr.find('w:' + tag, ns)
    if e is None:
        e = etree.Element(W + tag)
        pos = 0
        for k, ch in enumerate(rpr):
            if etree.QName(ch).localname in _BEFORE_SZ or (tag == 'szCs' and etree.QName(ch).localname == 'sz'):
                pos = k + 1
        rpr.insert(pos, e)
    old = e.get(W + 'val')
    e.set(W + 'val', str(val))
    return old != str(val)


def _set_both(st, val):
    rpr = st.find('w:rPr', ns)
    if rpr is None:
        rpr = etree.SubElement(st, W + 'rPr')
    a = _set(rpr, 'sz', val)
    b = _set(rpr, 'szCs', val)
    return a or b


def _create_tanai(root, styles):
    """סגנון התו "תנאי המשנה": וילנא מודגש, בגודל שיושר מיד אחר כך. מבוסס על ברירת המחדל של התו."""
    ids = {sid for sid in styles}
    sid, n = 'TanaiHaMishna', 1
    while sid in ids:
        n += 1
        sid = 'TanaiHaMishna%d' % n
    dflt = None
    for s2 in root.findall('w:style', ns):
        if s2.get(W + 'type') == 'character' and s2.get(W + 'default') == '1':
            dflt = s2.get(W + 'styleId')
    st = etree.SubElement(root, W + 'style')
    st.set(W + 'type', 'character')
    st.set(W + 'customStyle', '1')
    st.set(W + 'styleId', sid)
    etree.SubElement(st, W + 'name').set(W + 'val', TANAI_NAME)
    if dflt:
        etree.SubElement(st, W + 'basedOn').set(W + 'val', dflt)
    etree.SubElement(st, W + 'uiPriority').set(W + 'val', '1')
    etree.SubElement(st, W + 'qFormat')
    rp = etree.SubElement(st, W + 'rPr')
    rf = etree.SubElement(rp, W + 'rFonts')
    for k in ('ascii', 'hAnsi', 'cs'):
        rf.set(W + k, 'BA Vilna Bold')
    etree.SubElement(rp, W + 'b')
    etree.SubElement(rp, W + 'bCs')
    etree.SubElement(rp, W + 'spacing').set(W + 'val', '4')
    etree.SubElement(rp, W + 'sz').set(W + 'val', '18')
    etree.SubElement(rp, W + 'szCs').set(W + 'val', '18')
    return sid


def mishna_size(root):
    """M: גודל פסקת המשנה הרגילה, בחצאי נקודה (szCs של הסגנון "משניות")."""
    styles = _styles(root)
    for sid, (st, nm) in styles.items():
        if nm == 'משניות' and st.get(W + 'type') == 'paragraph':
            return eff(styles, sid, 'szCs', eff(styles, sid, 'sz', 18))
    raise ValueError('אין סגנון "משניות"')


def sync(styles_xml, raise_once=False):
    """מיישר את כל הסגנונות הנגזרים ל-M. מחזיר (xml, דוח)."""
    root = etree.fromstring(styles_xml)
    styles = _styles(root)
    m0 = mishna_size(root)
    raised = False
    m = m0
    if raise_once and m0 <= 9 * HALF:
        m = m0 + MISHNA_RAISE_PT * HALF
        raised = True
    t = m - TANAI_BELOW_PT * HALF
    h = m - HS_BELOW_PT * HALF
    rep = {'M_old': m0, 'M': m, 'tanai': t, 'hs': h, 'raised': raised, 'changed': [], 'renamed': None}

    # שם הסגנון: "תנאים במשנה" הישן הופך ל"תנאי המשנה" (באותו מזהה, בלי נגיעה בריצות)
    names = {nm: sid for sid, (st, nm) in styles.items() if st.get(W + 'type') == 'character'}
    if TANAI_NAME not in names and TANAI_LEGACY in names:
        st = styles[names[TANAI_LEGACY]][0]
        st.find('w:name', ns).set(W + 'val', TANAI_NAME)
        rep['renamed'] = TANAI_LEGACY
        styles = _styles(root)

    if TANAI_NAME not in {nm for sid, (st, nm) in styles.items() if st.get(W + 'type') == 'character'}:
        _create_tanai(root, styles)
        styles = _styles(root)
        rep['created'] = True

    for sid, (st, nm) in styles.items():
        typ = st.get(W + 'type')
        want = None
        if typ == 'paragraph':
            role = ROLE.get(nm)
            if nm in MISHNA_AS_TANAI_PARA or nm in (TANAI_LEGACY, "תנאים בד''ה משנה"):
                want = t
            elif nm in NOSE_AT_MISHNA_SIZE:
                want = m
            elif role == 'mishna' or role == 'dh' or nm in DH_PARA_EXTRA:
                want = m
        elif typ == 'character':
            if nm in CHAR_M:
                want = m
            elif nm in CHAR_T:
                want = t
            elif nm in CHAR_H:
                want = h
        if want is None:
            continue
        if _set_both(st, want):
            rep['changed'].append((nm, want))
    return etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True), rep


def nose_check(styles_xml):
    """נושא (פסקה) אינו גדול מ-M. מחזיר רשימת סגנונות חורגים."""
    root = etree.fromstring(styles_xml)
    styles = _styles(root)
    m = mishna_size(root)
    bad = []
    for sid, (st, nm) in styles.items():
        if st.get(W + 'type') == 'paragraph' and ROLE.get(nm) == 'nose':
            v = eff(styles, sid, 'szCs', eff(styles, sid, 'sz', 18))
            if v > m:
                bad.append((nm, v, m))
    return bad


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    path = sys.argv[1]
    z = zipfile.ZipFile(path)
    xml, rep = sync(z.read('word/styles.xml'), raise_once='--raise' in sys.argv)
    print(rep)
    print('נושא חורג:', nose_check(xml))
