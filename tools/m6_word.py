# -*- coding: utf-8 -*-
"""m6_word.py - מנת 6.10.2026 בקובצי הוורד: סגנונות המשנה, מסגרת "משנה בצד"
וסימון תנאים. כל שינוי בעקוב אחר שינויים, בשם המחבר "קלוד", עם גיבוי,
הגנה מדריסה ואימות מלא (המרה חוזרת והשוואה פסקה אחר פסקה).

מה נעשה בכל קובץ (בהרצה אחת, בגיבוי אחד):
א. סגנונות (תוספת בלבד, בלי נגיעה בסגנונות קיימים): תו "נושא משנה",
   תו "תנאים במשנה" (מבוסס אמוראים, גדול בנקודה), תו "הסבר במשנה" (מבוסס
   רקע והסבר, גדול בנקודה), ופסקה "משנה בצד" (מסגרת צד עם גבול דק).
ב. כל מופע של אמוראים או הסבר שבתוך פסקת משנה עובר, כשינוי עיצוב במעקב,
   לסגנון "במשנה" המקביל. (בוורד סגנון תו אינו משתנה לפי ההקשר.)
ג. סימון שמות תנאים מרשימה סגורה בלבד ("רבי מאיר", "בית שמאי"...). מקרה
   מסופק אינו מסומן.
ד. מסגרת "משנה בצד" ממוספרת ("משנה ג") בראש כל יחידת משנה, ומחיקת "מתני'"
   (בכל צורותיו) מתחילת המשנה. תווית ישנה בסגנון "משנה בצד" מוחלפת בנוסח
   החדש במקומה. אין הוספה כפולה בהרצה חוזרת.

    uv run --with lxml python tools/m6_word.py <slug> [--dry] [--copy-to DIR]
    uv run --with lxml python tools/m6_word.py --all [--dry]
"""
import os, sys, io, re, json, zipfile, datetime, argparse, collections, difflib, shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lxml import etree
import word_apply
from word_apply import (ns, W, NS, DRIVE, Refused, convert, _runs_of, _rpr, _mkrun, _mark, _mark_para,
                        _style_ids, _paragraph_map, _rezip, _ensure_track, backup, is_open_in_word,
                        wait_free, _copy_no_change)
from styles_map import ROLE, CS, role_of, TANAI_NAME
import mishna_box
import mishna_sizes

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUTHOR = 'קלוד'
NIKUD = re.compile(r'[֑-ׇ]')
S_NS, S_TN, S_HS, S_MB = 'נושא משנה', TANAI_NAME, 'הסבר במשנה', 'משנה בצד'   # S_TN: עד 6.10.2026 ערב "תנאים במשנה"
NUMBER_STYLES = ('מספר קטע', 'מספר קטע תו')

AM_NAMES = {n for n, c in CS.items() if c == 'am' and n not in (S_TN, S_TN + ' תו')}
HS_NAMES = {n for n, c in CS.items() if c == 'hs' and n not in (S_HS, S_HS + ' תו')}

# רשימה סגורה של שמות תנאים ודפוסים ודאיים. כל פריט: ביטוי בלי ניקוד. הסימון מוגבל
# לתחילת מילה (או אחרי ו/ה/ל/ש) ולסוף מילה, ואינו נוגע בטקסט שכבר מסומן בסגנון תו.
TANNA = [
    'רבי מאיר', 'רבי יהודה', 'רבי יוסי', 'רבי שמעון', 'רבי אליעזר', 'רבי יהושע', 'רבי עקיבא', 'רבי טרפון',
    'רבי ישמעאל', 'רבי נחמיה', 'רבי חנינא', 'רבי דוסא', 'רבי יונתן', 'רבי אלעזר', 'רבי זכריה', 'רבי ישמעאל',
    'רבן גמליאל', 'רבן שמעון בן גמליאל', 'רבן יוחנן בן זכאי', 'אבא שאול', 'בית שמאי', 'בית הלל',
    'חכמים', 'תנא קמא', 'ר"מ', 'ר"י', 'ר"ש', 'ר"ע', 'ר"א', 'ר"ט', 'ר"ג', 'ר\'מ', 'ר\'י',
]
TANNA = sorted(set(TANNA), key=len, reverse=True)
_Q = r'["\'׳״]'
TANNA_RE = re.compile(r'(?<![א-ת])(?:[והלש]?)(' + '|'.join(
    re.escape(t).replace('"', _Q).replace("\\'", _Q) for t in TANNA) + r')(?![א-ת])')

# תוויות "מתני'" בכל צורותיהן (בלי ניקוד): לפתיחת משנה
LABEL_ONLY = re.compile(r"^\s*(?:מתני[׳'’]?|מתניתין|משנה)\s*[.:]?\s*$")
LABEL_INLINE = re.compile(r"^(\s*)(מתני[׳'’]|מתניתין)(\s+)")


def plain_map(text):
    """הטקסט בלי ניקוד, ולכל תו שלו מיקומו בטקסט המקורי."""
    out, idx = [], []
    for i, c in enumerate(text):
        if '֑' <= c <= 'ׇ':
            continue
        out.append(c)
        idx.append(i)
    return ''.join(out), idx


def style_of_p(p):
    ps = p.find('w:pPr/w:pStyle', ns)
    return ps.get(W + 'val') if ps is not None else None


# ---------------------------------------------------------------- סגנונות

def _style_el(root, name):
    for st in root.findall('w:style', ns):
        nm = st.find('w:name', ns)
        if nm is not None and nm.get(W + 'val') == name:
            return st
    return None


def _new_id(root, base):
    ids = {st.get(W + 'styleId') for st in root.findall('w:style', ns)}
    sid, n = base, 1
    while sid in ids:
        n += 1
        sid = '%s%d' % (base, n)
    return sid


def _default_char(root):
    for s in root.findall('w:style', ns):
        if s.get(W + 'type') == 'character' and s.get(W + 'default') == '1':
            return s.get(W + 'styleId')
    return None


def _char_style(root, name, sid_base, rpr_children, based_on=None, link=None):
    st = etree.SubElement(root, W + 'style')
    st.set(W + 'type', 'character')
    st.set(W + 'customStyle', '1')
    sid = _new_id(root, sid_base)
    st.set(W + 'styleId', sid)
    etree.SubElement(st, W + 'name').set(W + 'val', name)
    b = based_on or _default_char(root)
    if b:
        etree.SubElement(st, W + 'basedOn').set(W + 'val', b)
    etree.SubElement(st, W + 'uiPriority').set(W + 'val', '1')
    etree.SubElement(st, W + 'qFormat')
    rp = etree.SubElement(st, W + 'rPr')
    for tag, attrs in rpr_children:
        el = etree.SubElement(rp, W + tag)
        for k, v in attrs.items():
            el.set(W + k, v)
    return sid


def ensure_styles(styles_xml, log=print):
    """מוסיף את הסגנונות החסרים. מחזיר (xml, רשימת מה שנוסף)."""
    # השם הקודם של סגנון התנאים הופך לשם הקבוע (באותו מזהה), לפני כל בדיקת קיום
    styles_xml, _rep = mishna_sizes.sync(styles_xml)
    root = etree.fromstring(styles_xml)
    added = ['תנאי המשנה (נוצר)'] if _rep.get('created') else []
    if _rep.get('renamed'):
        added.append('תנאי המשנה (שונה שם מ-%s)' % _rep['renamed'])
    if _style_el(root, S_NS) is None:
        # כמו הקיים בסוכה: וילנא Extra-Bold, בגודל המשנה (דרגת עובי אחת מעליה)
        _char_style(root, S_NS, 'NoseMishna', [
            ('rFonts', {'cs': 'BA TM • Vilna Extra-Bold'}), ('spacing', {'val': '4'}), ('szCs', {'val': '18'})])
        added.append(S_NS)
    if _style_el(root, S_TN) is None:
        # גדול בנקודה אחת מטקסט המשנה (9 -> 10), באותה משפחת גופן של המשנה
        _char_style(root, S_TN, 'TanaimMishna', [
            ('rFonts', {'ascii': 'BA Vilna Bold', 'hAnsi': 'BA Vilna Bold', 'cs': 'BA Vilna Bold'}),
            ('b', {}), ('bCs', {}), ('spacing', {'val': '4'}), ('sz', {'val': '20'}), ('szCs', {'val': '20'})])
        added.append(S_TN)
    if _style_el(root, S_HS) is None:
        # גדול בנקודה אחת מן ההסבר שבגמרא (כ-7.4 -> 8.5 נקודות)
        _char_style(root, S_HS, 'HesberMishna', [
            ('rFonts', {'ascii': 'Fb Fontext', 'hAnsi': 'Fb Fontext', 'cs': 'FrankRuehl'}),
            ('sz', {'val': '17'}), ('szCs', {'val': '17'})])
        added.append(S_HS)
    mb = _style_el(root, S_MB)
    spec = _mb_style_children()
    if mb is None:
        st = etree.SubElement(root, W + 'style')
        st.set(W + 'type', 'paragraph')
        st.set(W + 'customStyle', '1')
        st.set(W + 'styleId', _new_id(root, 'MishnaBatzad'))
        etree.SubElement(st, W + 'name').set(W + 'val', S_MB)
        base = None
        for s in root.findall('w:style', ns):
            if s.get(W + 'type') == 'paragraph' and s.get(W + 'default') == '1':
                base = s.get(W + 'styleId')
        if base:
            etree.SubElement(st, W + 'basedOn').set(W + 'val', base)
        etree.SubElement(st, W + 'qFormat')
        for el in spec:
            st.append(el)
        added.append(S_MB + ' (נוצר)')
    elif mb.find('w:pPr/w:pBdr', ns) is None:
        # תווית ישנה ("מתני'."): מקבלת מראה ריבוע עדין, בלי לשנות את מקומה במסילה
        for old in mb.findall('w:pPr', ns) + mb.findall('w:rPr', ns):
            mb.remove(old)
        for el in spec:
            mb.append(el)
        added.append(S_MB + ' (עוצב כריבוע)')
    # יישור הגדלים ליחס הקבוע (נוצר סגנון חדש בגודל ברירת מחדל)
    out, _ = mishna_sizes.sync(etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True))
    return out, added


# סגנונות הפסקה של ד"ה משנה (ממורכזים). המספר ("א. ") יושב בתחילת השורה הממורכזת
# ומסיט את הטקסט אל הקצה; הזחה אחורית (בצד השמאלי) שווה לרוחב מספר (נמדד ב-PDF: 16 נקודות) של אות אחת
# מחזירה את מרכז הטקסט למרכז השורה. השינוי בהגדרת הסגנון (לא בכל פסקה): סגנון אינו
# נרשם במעקב, ואין 2,900 שינויי עיצוב בקובץ. הסטייה שנותרת: חצי ההפרש בין רוחב מספר
# של אות לרוחב מספר של שתי אותיות או בלי מספר - פחות ממילימטר.
DH_STYLE_NAMES = ("ד''ה משנה", "משנה ד''ה", "ד''ה משנה מודגש אפור", 'משניות כותרת')
DH_INDENT_END = '320'      # טוויפס (עשרים לנקודה): 16 נקודות = רוחב "א. " בגודל הד"ה


def center_dh_styles(styles_xml):
    """מוסיף הזחה אחורית לסגנונות ד"ה ממורכזים. מחזיר (xml, רשימת סגנונות שעודכנו)."""
    root = etree.fromstring(styles_xml)
    done = []
    after = ('contextualSpacing', 'mirrorIndents', 'suppressOverlap', 'jc', 'textDirection', 'textAlignment',
             'textboxTightWrap', 'outlineLvl', 'divId', 'cnfStyle', 'rPr', 'sectPr', 'pPrChange')
    for st in root.findall('w:style', ns):
        nm = st.find('w:name', ns)
        if st.get(W + 'type') != 'paragraph' or nm is None or nm.get(W + 'val') not in DH_STYLE_NAMES:
            continue
        pPr = st.find('w:pPr', ns)
        if pPr is None:
            continue
        jc = pPr.find('w:jc', ns)
        if jc is None or jc.get(W + 'val') != 'center':
            continue
        ind = pPr.find('w:ind', ns)
        if ind is None:
            ind = etree.Element(W + 'ind')
            pos = len(pPr)
            for k, ch in enumerate(pPr):
                if etree.QName(ch).localname in after:
                    pos = k
                    break
            pPr.insert(pos, ind)
        elif ind.get(W + 'end') == DH_INDENT_END:
            continue
        ind.set(W + 'end', DH_INDENT_END)
        done.append(nm.get(W + 'val'))
    return etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True), done


_PPR_AFTER_IND = ('contextualSpacing', 'mirrorIndents', 'suppressOverlap', 'jc', 'textDirection', 'textAlignment',
                  'textboxTightWrap', 'outlineLvl', 'divId', 'cnfStyle', 'rPr', 'sectPr', 'pPrChange')


def set_ind_end(p, end, author, when, nextid):
    """הזחה אחורית ישירה על פסקה, במעקב (pPrChange). משמש ד"ה בלי מספר, שאינו צריך את
    ההזחה שבהגדרת הסגנון."""
    pPr = p.find('w:pPr', ns)
    if pPr is None:
        pPr = etree.Element(W + 'pPr')
        p.insert(0, pPr)
    old = _copy_no_change(pPr, 'pPrChange')
    for ch in pPr.findall('w:pPrChange', ns):
        pPr.remove(ch)
    ind = pPr.find('w:ind', ns)
    if ind is None:
        ind = etree.Element(W + 'ind')
        pos = len(pPr)
        for k, c in enumerate(pPr):
            if etree.QName(c).localname in _PPR_AFTER_IND:
                pos = k
                break
        pPr.insert(pos, ind)
    elif ind.get(W + 'end') == end:
        return False
    ind.set(W + 'end', end)
    ch = _mark(etree.Element(W + 'pPrChange'), author, when, nextid)
    ch.append(old)
    pPr.append(ch)
    return True


def _mb_style_children():
    """pPr ו-rPr של "משנה בצד": מסגרת צד במסילה (כמו חלון 3), ריבוע עדין, וילנא Bold קטן."""
    pPr = etree.Element(W + 'pPr')
    fr = etree.SubElement(pPr, W + 'framePr')
    for k, v in (('w', '700'), ('hSpace', '57'), ('wrap', 'around'), ('vAnchor', 'text'),
                 ('hAnchor', 'text'), ('x', '3516'), ('y', '1')):
        fr.set(W + k, v)
    bd = etree.SubElement(pPr, W + 'pBdr')
    for side in ('top', 'left', 'bottom', 'right'):
        e = etree.SubElement(bd, W + side)
        e.set(W + 'val', 'single')
        e.set(W + 'sz', '4')
        e.set(W + 'space', '1')
        e.set(W + 'color', '8A7D66')
    etree.SubElement(pPr, W + 'spacing').set(W + 'line', '200')
    pPr[-1].set(W + 'lineRule', 'exact')
    etree.SubElement(pPr, W + 'jc').set(W + 'val', 'center')
    rPr = etree.Element(W + 'rPr')
    rf = etree.SubElement(rPr, W + 'rFonts')
    rf.set(W + 'ascii', 'BA Vilna Bold')
    rf.set(W + 'hAnsi', 'BA Vilna Bold')
    rf.set(W + 'cs', 'BA Vilna Bold')
    etree.SubElement(rPr, W + 'bCs')
    c = etree.SubElement(rPr, W + 'color')
    c.set(W + 'val', '7A6A45')
    etree.SubElement(rPr, W + 'sz').set(W + 'val', '14')
    etree.SubElement(rPr, W + 'szCs').set(W + 'val', '14')
    return [pPr, rPr]


# ---------------------------------------------------------------- עיצוב במעקב

def _live(r):
    el = r.getparent()
    while el is not None and el.tag != W + 'p':
        if el.tag in (W + 'del', W + 'moveFrom'):
            return False
        el = el.getparent()
    return True


def restyle_run(r, sid, author, when, nextid):
    """מחליף את סגנון התו של ריצה ורושם את הקודם ב-rPrChange."""
    rp = r.find('w:rPr', ns)
    if rp is None:
        rp = etree.Element(W + 'rPr')
        r.insert(0, rp)
    old = _copy_no_change(rp, 'rPrChange')
    for ch in rp.findall('w:rPrChange', ns):
        rp.remove(ch)
    cur = rp.find('w:rStyle', ns)
    if cur is None:
        cur = etree.Element(W + 'rStyle')
        rp.insert(0, cur)
    cur.set(W + 'val', sid)
    ch = _mark(etree.Element(W + 'rPrChange'), author, when, nextid)
    ch.append(old)
    rp.append(ch)


def _rstyle_name(r, sid2name):
    rp = r.find('w:rPr', ns)
    if rp is None:
        return None
    st = rp.find('w:rStyle', ns)
    return sid2name.get(st.get(W + 'val')) if st is not None else None


def mark_tanaim(p, tn_sid, author, when, nextid):
    """מסמן שמות תנאים (רשימה סגורה) בסגנון "תנאים במשנה". מחזיר מספר סימונים.
    רק בטקסט שאינו מסומן בסגנון תו ושיושב ישירות בפסקה (לא בתוך שינוי מעקב)."""
    runs = _runs_of(p)
    full = ''.join(t for _, t, _ in runs)
    pl, idx = plain_map(full)
    hits = []
    for m in TANNA_RE.finditer(pl):
        a, b = m.start(1), m.end(1)
        lo, hi = idx[a], idx[b - 1] + 1
        hits.append((lo, hi))
    n = 0
    # מהסוף להתחלה, כדי שהיסטים לא יזוזו
    for lo, hi in reversed(hits):
        runs = _runs_of(p)
        touched = [(pos, txt, r) for pos, txt, r in runs if pos < hi and pos + len(txt) > lo]
        ok = bool(touched)
        for _, _, r in touched:
            rp = r.find('w:rPr', ns)
            if r.getparent().tag != W + 'p' or (rp is not None and rp.find('w:rStyle', ns) is not None):
                ok = False
        if not ok:
            continue
        for pos, txt, r in touched:
            a = max(lo - pos, 0)
            b = min(hi - pos, len(txt))
            rpr = _rpr(r)
            parent = r.getparent()
            i0 = list(parent).index(r)
            new = []
            if txt[:a]:
                new.append(_mkrun(txt[:a], rpr))
            mid = _mkrun(txt[a:b], rpr)
            restyle_run(mid, tn_sid, author, when, nextid)
            new.append(mid)
            if txt[b:]:
                new.append(_mkrun(txt[b:], rpr))
            parent.remove(r)
            for k, el in enumerate(new):
                parent.insert(i0 + k, el)
        n += 1
    return n


# ---------------------------------------------------------------- מבנה

def _first_content_index(p):
    """אינדקס ההכנסה אחרי pPr."""
    return 1 if p.find('w:pPr', ns) is not None else 0


def new_paragraph_before(p, text, sid, author, when, nextid):
    """פסקה חדשה לפני p, כהוספה במעקב (סימן הפסקה והטקסט)."""
    p2 = etree.Element(W + 'p')
    pPr = etree.SubElement(p2, W + 'pPr')
    etree.SubElement(pPr, W + 'pStyle').set(W + 'val', sid)
    ins = _mark(etree.Element(W + 'ins'), author, when, nextid)
    ins.append(_mkrun(text, None))
    p2.append(ins)
    _mark_para(p2, 'ins', author, when, nextid)
    parent = p.getparent()
    parent.insert(list(parent).index(p), p2)
    return p2


def replace_own_ins(p, newtxt, author):
    """תווית שכל טקסטה הוא הוספה במעקב שלי (מהרצה קודמת): מעדכן את נוסח ההוספה במקומה.
    אינו נוגע בהוספה של אחר."""
    runs = [r for r in p.iter(W + 'r') if _live(r)]
    if not runs:
        return False
    for r in runs:
        par = r.getparent()
        if par.tag != W + 'ins' or par.get(W + 'author') != author:
            return False
    first = True
    for r in runs:
        ts = r.findall('w:t', ns)
        if not ts:
            continue
        for k, t in enumerate(ts):
            t.text = newtxt if (first and k == 0) else ''
        first = False
    return not first


def delete_text(p, lo, hi, author, when, nextid):
    """מוחק במעקב את הטקסט שבטווח [lo, hi) של הטקסט החי של הפסקה."""
    return word_apply._replace_in_paragraph(p, ''.join(t for _, t, _ in _runs_of(p))[lo:hi], '',
                                            author, when, nextid, at=lo)


def direct_runs_only(p):
    """כל הריצות החיות של הפסקה יושבות ישירות בה (לא בתוך שינוי מעקב קיים)."""
    return all(r.getparent().tag in (W + 'p', W + 'ins') for r in p.iter(W + 'r') if _live(r))


def delete_paragraph(p, author, when, nextid):
    """מוחק פסקה שלמה במעקב: כל הריצות החיות ל-del וסימן הפסקה ל-del."""
    for r in list(p.iter(W + 'r')):
        if not _live(r) or r.getparent().tag not in (W + 'p', W + 'ins'):
            continue
        parent = r.getparent()
        if parent.tag == W + 'ins':
            # הוספה של אחר שנמחקת: מוחקים בתוך ההוספה (וורד מציג מחיקה של הוספה)
            pass
        d = _mark(etree.Element(W + 'del'), author, when, nextid)
        i0 = list(parent).index(r)
        parent.remove(r)
        for t in r.findall('w:t', ns):
            t.tag = W + 'delText'
            t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
        d.append(r)
        parent.insert(i0, d)
    _mark_para(p, 'del', author, when, nextid)


def insert_number_prefix(p, letter_text, mk_sid, author, when, nextid):
    """"ג. " בסגנון "מספר קטע" בתחילת הפסקה, כהוספה במעקב."""
    rp = etree.Element(W + 'rPr')
    etree.SubElement(rp, W + 'rStyle').set(W + 'val', mk_sid)
    ins = _mark(etree.Element(W + 'ins'), author, when, nextid)
    ins.append(_mkrun(letter_text, rp))
    p.insert(_first_content_index(p), ins)


# ---------------------------------------------------------------- הראשי

def nz(t):
    """נרמול להשוואת נוסח האתר לנוסח הוורד: רווחים וטאבים מכווצים, סימני כיוון מוסרים."""
    t = (t or '').replace('‏', '').replace('‎', '').replace(' ', ' ')
    return re.sub(r'\s+', ' ', t).strip()


def nzs(t):
    """כמו nz, בלי מספר הקטע שבתחילת הפסקה ("א. ")."""
    return re.sub(r'^[א-ת]{1,2}\. ', '', nz(t))


def locate(before, op, used, any_role=False):
    """הפסקה הראשונה של יחידת המשנה בקובץ: לפי האינדקס (אם הנוסח זהה), ואחרת לפי נוסח ודף."""
    ctx = nzs(op.get('text'))
    ix = op.get('i')
    if ix is not None and 0 <= ix < len(before) and nzs(before[ix]['text']) == ctx and ix not in used:
        return before[ix]
    from hagaha import daf_key
    k0 = daf_key(op.get('daf')) if op.get('daf') else None
    win = [b for b in before if k0 is None or daf_key(b.get('daf')) is None or abs(daf_key(b['daf']) - k0) <= 1]
    hits = [b for b in win if nzs(b['text']) == ctx and b['i'] not in used and (any_role or role_of(b) == 'mishna')]
    nxt = nzs(op.get('next'))
    if len(hits) > 1 and nxt:
        hits = [b for b in hits if b['i'] + 1 < len(before) and nzs(before[b['i'] + 1]['text']) == nxt] or hits
    if len(hits) > 1 and ix is not None:
        hits.sort(key=lambda b: abs(b['i'] - ix))
        if abs(hits[0]['i'] - ix) == abs(hits[1]['i'] - ix):
            return None
        hits = hits[:1]
    return hits[0] if len(hits) == 1 else None


def label_info(b):
    """האם הפסקה היא "תווית בלבד" (מתני'. / משנה.), עם מספר קטע אופציונלי לפניה.
    מחזיר (מספר קטע או '', True) או None."""
    runs = b.get('runs') or []
    num_txt = ''
    rest = ''
    for r in runs:
        if (r.get('cs') or '') in NUMBER_STYLES and not rest:
            num_txt += r['t']
        else:
            rest += r['t']
    pl = NIKUD.sub('', rest).strip()
    if pl and LABEL_ONLY.match(pl):
        return num_txt
    return None


def inline_label(b):
    """תווית "מתני'" בתחילת הטקסט של פסקת משנה שיש אחריה טקסט. מחזיר (lo, hi) בטקסט החי, או None."""
    txt = b['text']
    pl, idx = plain_map(txt)
    m = re.match(r"^((?:[א-ת]{1,2}\.\s+)?)(מתני[׳'’]|מתניתין)(\s+)", pl)
    if not m:
        return None
    a = m.start(2)
    z = m.end(3)
    return idx[a], (idx[z] if z < len(idx) else len(txt))


def mb_text(op):
    return 'משנה ' + mishna_box.heb(op['n']) if op.get('n') else 'משנה'


def process(path, slug, ops, dry=False, log=print, author=AUTHOR, only=None, dh_ops=None):
    """מעבד קובץ אחד. ops = ops של data/mbox (יחידות משנה). מחזיר דוח."""
    only_default = not only
    only = only or {'styles', 'restyle', 'tanna', 'frames'}
    dh_ops = dh_ops or []
    if is_open_in_word(path) and not wait_free(path, log=log):
        raise Refused('הקובץ פתוח בוורד ולא התפנה')
    mtime = os.path.getmtime(path)
    before = convert(path)
    pmap_last = dict(word_apply.convert.last)
    z = zipfile.ZipFile(path)
    doc = etree.fromstring(z.read('word/document.xml'))
    settings = z.read('word/settings.xml')
    styles = z.read('word/styles.xml')
    z.close()
    rep = collections.OrderedDict(file=os.path.basename(path), styles_added=[], restyled_tn=0, restyled_hs=0,
                                  tanna_marked=0, frames_new=0, frames_replaced=0, frames_ok=0,
                                  labels_deleted=0, labels_inline=0, no_number=[], unplaced=[], skipped_existing=0,
                                  dh_new=0, dh_unplaced=[])
    extra = {}
    if 'styles' in only:
        styles, added = ensure_styles(styles)
        if 'center' in only or only_default:
            styles, cdone = center_dh_styles(styles)
            added = added + ['ד"ה ממורכז (הזחה): ' + ', '.join(cdone)] if cdone else added
        rep['styles_added'] = added
        if added:
            extra['word/styles.xml'] = styles
    sids = _style_ids(styles)
    sid2name = {}
    for st in etree.fromstring(styles).findall('w:style', ns):
        nm = st.find('w:name', ns)
        if nm is not None:
            sid2name[st.get(W + 'styleId')] = nm.get(W + 'val')
    word_apply.convert.last = pmap_last
    xml_ps = _paragraph_map(doc, before)
    counter = [20000]

    def nextid():
        counter[0] += 1
        return counter[0]

    when = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    mk_sid = (sids.get('מספר קטע') or (None,))[0]
    tn_sid, hs_sid, mb_sid = sids[S_TN][0], sids[S_HS][0], sids[S_MB][0]
    expect = []          # (style, text) צפוי אחרי, בונים בהמשך

    # --- ב + ג: סגנונות תו בתוך משניות
    if 'restyle' in only or 'tanna' in only:
        for b in before:
            if role_of(b) != 'mishna':
                continue
            p = xml_ps.get(b['i'])
            if p is None:
                continue
            if 'restyle' in only:
                for r in list(p.iter(W + 'r')):
                    if not _live(r):
                        continue
                    nm = _rstyle_name(r, sid2name)
                    if nm in AM_NAMES:
                        restyle_run(r, tn_sid, author, when, nextid)
                        rep['restyled_tn'] += 1
                    elif nm in HS_NAMES:
                        restyle_run(r, hs_sid, author, when, nextid)
                        rep['restyled_hs'] += 1
            if 'tanna' in only:
                rep['tanna_marked'] += mark_tanaim(p, tn_sid, author, when, nextid)

    # --- ד"ה בלי מספר קטע: ההזחה של הסגנון (שמחזירה את המרכז אחרי המספר) אינה חלה עליו
    if 'center' in only or only_default:
        for b in before:
            if b['style'] in DH_STYLE_NAMES and b['text'].strip():
                runs = b.get('runs') or []
                if runs and (runs[0].get('cs') or '') in NUMBER_STYLES:
                    continue
                p = xml_ps.get(b['i'])
                if p is not None and set_ind_end(p, '0', author, when, nextid):
                    rep['dh_unnumbered_fixed'] = rep.get('dh_unnumbered_fixed', 0) + 1

    # --- ד: מסגרת "משנה בצד" ומחיקת "מתני'"
    deleted_idx = set()
    prefix_ins = {}        # אינדקס פסקה -> טקסט מספר קטע להוספה בתחילתה
    new_frames = {}        # אינדקס פסקה -> טקסט חדש לפניה
    replaced = {}          # אינדקס פסקת תווית ישנה -> טקסט חדש
    fixed_frames = {}      # אינדקס מסגרת שמספרה שגוי -> (נוסח חדש, דף, נוסח ישן)
    inline_del = {}        # אינדקס -> (lo,hi)
    if 'frames' in only:
        used = set()
        for op in ops:
            b = locate(before, op, used)
            if b is None:
                rep['unplaced'].append([op.get('daf'), op.get('i'), (op.get('text') or '')[:40]])
                continue
            used.add(b['i'])
            i = b['i']
            prev = before[i - 1] if i > 0 else None
            txt = mb_text(op)
            if not op.get('n'):
                rep['no_number'].append([op.get('daf'), i])
            # תווית ישנה / קיימת לפני יחידת המשנה
            if prev is not None and prev['style'] == S_MB:
                ptxt = prev['text'].strip()
                m = mishna_box.MBW.match(ptxt)
                nc = op.get('nc')
                if m and nc and mishna_box.num(m.group(1)) != nc:
                    # מסגרת שמספרה שונה ממה שנגזר מנוסח המשנה: מתוקנת רק אם היא הוספה שלי (מהרצה
                    # קודמת). מסגרת שכתב אדם נשארת, והסתירה נרשמת (הוורד גובר).
                    fixed_frames[prev['i']] = ('משנה ' + mishna_box.heb(nc), op.get('daf'), ptxt)
                    replaced[prev['i']] = 'משנה ' + mishna_box.heb(nc)
                elif m or nz(ptxt) == nz(txt):
                    rep['frames_ok'] += 1
                else:
                    replaced[prev['i']] = txt
                    rep['frames_replaced'] += 1
            elif op.get('n'):
                new_frames[i] = txt
                rep['frames_new'] += 1
            # מחיקת "מתני'" מתחילת המשנה
            li = label_info(b)
            if li is not None:
                nb = before[i + 1] if i + 1 < len(before) else None
                if nb is not None and role_of(nb) == 'mishna' and nb['style'] != S_MB and nb['i'] not in new_frames:
                    deleted_idx.add(i)
                    if li.strip():
                        prefix_ins[nb['i']] = li
                    rep['labels_deleted'] += 1
                else:
                    pass
            else:
                il = inline_label(b)
                if il:
                    inline_del[i] = il
                    rep['labels_inline'] += 1
        # --- יישום (לפי סדר יורד של אינדקסים אינו נדרש: מניפולציות מקומיות)
        for i, newtxt in list(replaced.items()):
            p = xml_ps[i]
            runs = _runs_of(p)
            full = ''.join(t for _, t, _ in runs)
            if i in fixed_frames:
                # תיקון מספר: רק הוספה שלי, בנוסח המוסף במקומו
                if replace_own_ins(p, newtxt, author):
                    rep['frames_fixed'] = rep.get('frames_fixed', 0) + 1
                else:
                    rep.setdefault('frame_conflicts', []).append([fixed_frames[i][1], fixed_frames[i][2], fixed_frames[i][0]])
                    del replaced[i]
                continue
            if not (word_apply._replace_in_paragraph(p, full, newtxt, author, when, nextid)
                    or replace_own_ins(p, newtxt, author)):
                rep['unplaced'].append(['תווית ישנה', i, full[:30]])
                del replaced[i]
                rep['frames_replaced'] -= 1
        for i, (lo, hi) in list(inline_del.items()):
            p = xml_ps[i]
            if not delete_text(p, lo, hi, author, when, nextid):
                rep['unplaced'].append(['מתני\' בתחילת משנה', i, before[i]['text'][:30]])
                del inline_del[i]
                rep['labels_inline'] -= 1
        for i in sorted(deleted_idx):
            if not direct_runs_only(xml_ps[i]):
                # תווית שיושבת בתוך שינוי מעקב של אחר: אין נוגעים בה
                rep['unplaced'].append(['תווית בתוך שינוי מעקב', i, before[i]['text'][:30]])
                deleted_idx.discard(i)
                prefix_ins.pop(i + 1, None)
                rep['labels_deleted'] -= 1
                continue
            delete_paragraph(xml_ps[i], author, when, nextid)
        for i, letter_txt in prefix_ins.items():
            if mk_sid:
                insert_number_prefix(xml_ps[i], letter_txt, mk_sid, author, when, nextid)
        for i, txt in new_frames.items():
            new_paragraph_before(xml_ps[i], txt, mb_sid, author, when, nextid)

    # --- ד"ה משנה חסרים (חלק א): פסקה חדשה לפני יחידת הגוף, במספר הקטע ובסגנון הד"ה של הקובץ
    new_dh = {}
    if 'dh' in only and dh_ops:
        cnt = collections.Counter(b['style'] for b in before if role_of(b) == 'dh')
        dh_style = next((n for n, _ in cnt.most_common() if n in sids), None)
        usedd = set()
        for op in dh_ops:
            b = locate(before, {'daf': op.get('daf'), 'text': op.get('text'), 'next': op.get('next'), 'i': None},
                       usedd, any_role=True)
            if b is None or dh_style is None:
                rep['dh_unplaced'].append([op.get('daf'), op.get('letter'), op.get('dh')])
                continue
            pv = before[b['i'] - 1] if b['i'] > 0 else None
            if pv is not None and role_of(pv) in ('dh', 'mishna', 'nose'):
                rep['dh_unplaced'].append([op.get('daf'), op.get('letter'), 'כבר יש כותרת לפניה'])
                continue
            usedd.add(b['i'])
            new_dh[b['i']] = (dh_style, (op['letter'] + '. ' if op.get('letter') else '') + op['dh'], op)
        for i, (st, txt, op) in new_dh.items():
            p2 = new_paragraph_before(xml_ps[i], op['dh'], sids[st][0], author, when, nextid)
            if op.get('letter') and mk_sid:
                insert_number_prefix(p2, op['letter'] + '. ', mk_sid, author, when, nextid)
            rep['dh_new'] += 1

    # --- הכנת הצפוי
    exp = []
    for b in before:
        i = b['i']
        if i in new_frames:
            exp.append((S_MB, new_frames[i]))
        if i in new_dh:
            exp.append((new_dh[i][0], new_dh[i][1]))
        if i in deleted_idx:
            continue
        t = b['text']
        if i in prefix_ins:
            t = prefix_ins[i] + t
        if i in replaced:
            t = replaced[i]
        if i in inline_del:
            lo, hi = inline_del[i]
            t = t[:lo] + t[hi:]
        exp.append((b['style'], t))
    rep['expected_paragraphs'] = len(exp)
    if dry:
        rep['dry'] = True
        return rep
    if not any([rep['restyled_tn'], rep['restyled_hs'], rep['tanna_marked'], rep['frames_new'],
                rep['frames_replaced'], rep['labels_deleted'], rep['labels_inline'], rep['styles_added'], rep['dh_new'],
                rep['frames_replaced'] or len(replaced)]):
        rep['changed'] = False
        return rep
    if os.path.getmtime(path) != mtime:
        rep['stale'] = True
        return rep
    tmp = path + '.new'
    _rezip(path, tmp, dict({'word/document.xml': etree.tostring(doc, xml_declaration=True, encoding='UTF-8', standalone=True),
                            'word/settings.xml': _ensure_track(settings)[0]}, **extra))
    after = convert(tmp)
    got = [(a['style'], a['text']) for a in after]
    bad = []
    if got != exp:
        sm = difflib.SequenceMatcher(None, got, exp, autojunk=False)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag != 'equal':
                bad.append('%s: קיבלנו %r ציפינו %r' % (tag, got[i1:i2][:2], exp[j1:j2][:2]))
                if len(bad) >= 6:
                    break
    # אימות נוסף: הקובץ נפתח כ-zip תקין ו-XML תקין
    try:
        zz = zipfile.ZipFile(tmp)
        assert zz.testzip() is None
        etree.fromstring(zz.read('word/document.xml'))
        etree.fromstring(zz.read('word/styles.xml'))
        zz.close()
    except Exception as e:
        bad.append('הקובץ החדש אינו תקין: %s' % e)
    if bad:
        os.remove(tmp)
        rep['verified'] = False
        rep['errors'] = bad
        return rep
    # הגנה מדריסה: אם הקובץ השתנה בינתיים - לא כותבים
    if os.path.getmtime(path) != mtime or is_open_in_word(path):
        os.remove(tmp)
        rep['stale'] = True
        return rep
    bk = backup(path, slug)
    os.replace(tmp, path)
    rep['verified'] = True
    rep['backup'] = bk
    return rep


def files_of(masechet):
    st = json.load(io.open(os.path.join(ROOT, 'site', 'status.json'), encoding='utf-8'))
    rec = (st.get('built') or {}).get(masechet)
    if not rec or not rec.get('file'):
        raise Refused('אין רשומת בנייה למסכת %s' % masechet)
    out = []
    for f in rec['file'].split(' + '):
        p = os.path.join(DRIVE, f)
        if not os.path.exists(p):
            raise Refused('הקובץ %s אינו בתיקיית הדרייב' % f)
        out.append(p)
    return out


def run_slug(slug, dry=False, only=None, retries=2, log=print):
    d = json.load(io.open(os.path.join(ROOT, 'data', 'mbox', slug + '.json'), encoding='utf-8'))
    masechet = d['masechet']
    ops = d['ops']
    left = list(ops)
    outs = []
    for path in files_of(masechet):
        r = None
        for attempt in range(retries + 1):
            r = process(path, slug, left, dry=dry, log=log, only=only)
            if not r.get('stale'):
                break
            log('הקובץ השתנה בזמן העיבוד - מנסה שוב (%d)' % (attempt + 1))
        outs.append(r)
        if r.get('verified') is False:
            break
        # יחידות שהוצבו בקובץ הזה אינן עוברות לבא אחריו
        miss = {(x[0], x[1]) for x in r.get('unplaced', [])}
        left = [o for o in left if (o.get('daf'), o.get('i')) in miss]
    return outs


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('slugs', nargs='*')
    ap.add_argument('--all', action='store_true')
    ap.add_argument('--dry', action='store_true')
    ap.add_argument('--only', help='styles,restyle,tanna,frames')
    a = ap.parse_args()
    slugs = a.slugs
    if a.all:
        slugs = sorted(f[:-5] for f in os.listdir(os.path.join(ROOT, 'data', 'mbox')) if f.endswith('.json'))
    only = set(a.only.split(',')) if a.only else None
    for s in slugs:
        try:
            for r in run_slug(s, a.dry, only):
                print(json.dumps(r, ensure_ascii=False))
        except Refused as e:
            print(s, 'דולג:', e)
