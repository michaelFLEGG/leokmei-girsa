# -*- coding: utf-8 -*-
"""
שכבת העיצוב (ב3) - בכורות, חוקה סעיף 8.4 ו-6.6.

    python masechet_fmt.py <קלט.docx> <פלט.docx>

 א. פסקת חציצה (***, • • •, או עיטור BA בטווח U+05F5-U+05FF) הצמודה לפסקת
    כותרת - פרק, פרק שם, ד"ה משנה, נושא, כותר פנימי פ, הדרן - לפניה או
    אחריה, גם כשביניהן פסקה ריקה או ציון דף - נמחקת במעקב. הכותרת עצמה
    היא ההפרדה.
 ב. שאר פסקאות החציצה מאוחדות לסגנון "חציצה", כמו בסוכה (שינוי סגנון
    פסקה במעקב).
 ג. פסקה ריקה שנשארה מן המקור (גוף רגיל, בלי תוכן) נמחקת במעקב.
כל הכתיבה בשם "מנוע עיצוב"; שום תו של טקסט אינו משתנה.
"""
import sys, re, copy, collections
from lxml import etree
import laukmi_mech
from laukmi_mech import Doc, q, text_map
laukmi_mech.AUTHOR = "מנוע עיצוב"

HEADINGS = {"פרק", "פרק שם", "דפים בפרק ב", "תחילת פרק", "ד''ה משנה", "נושא",
            "כותר פנימי פ", "הדרן עלך", "סוף פרק"}
TRANSPARENT = {"דף בצד", "דף בצד מעודכן"}
BODYISH = {"Normal", "רגיל", "0.1", "0.2", "List Paragraph", "רווח לפני"}
SEP_RX = re.compile(r'^[\s.‏‎]*(?:[•·∙◦・]\s*){2,}[\s.]*$|^[\s.]*\*{3,}[\s.]*$|^[\s׵-׿]+$')
X = "{http://www.w3.org/XML/1998/namespace}space"


def live(p):
    return text_map(p)[0]


def is_empty(p):
    if live(p).strip():
        return False
    for t in p.iter(q("drawing"), q("pict"), q("sectPr"), q("fldChar"), q("object")):
        return False
    for br in p.iter(q("br")):
        if br.get(q("type")) in ("page", "column"):
            return False
    return True


def is_sep(p):
    t = live(p)
    return bool(t.strip()) and bool(SEP_RX.match(t))


def delete_paragraph(doc, p):
    """מחיקת פסקה כולה במעקב: הרצים נעטפים ב-w:del וסימן הפסקה מסומן כמחוק."""
    for ch in list(p):
        if ch.tag in (q("pPr"), q("del")):
            continue
        if ch.tag == q("r"):
            for t in ch.findall(q("t")):
                t.tag = q("delText"); t.set(X, "preserve")
            d = etree.Element(q("del"))
            d.set(q("id"), doc.nid()); d.set(q("author"), laukmi_mech.AUTHOR); d.set(q("date"), laukmi_mech.DATE)
            ch.addprevious(d); d.append(ch)
    pPr = p.find(q("pPr"))
    if pPr is None:
        pPr = etree.Element(q("pPr")); p.insert(0, pPr)
    rPr = pPr.find(q("rPr"))
    if rPr is None:
        rPr = etree.Element(q("rPr"))
        # rPr יושב לפני sectPr/pPrChange בסכמה
        anchor = None
        for tag in ("sectPr", "pPrChange"):
            anchor = pPr.find(q(tag))
            if anchor is not None:
                break
        if anchor is not None:
            anchor.addprevious(rPr)
        else:
            pPr.append(rPr)
    d = etree.Element(q("del"))
    d.set(q("id"), doc.nid()); d.set(q("author"), laukmi_mech.AUTHOR); d.set(q("date"), laukmi_mech.DATE)
    rPr.insert(0, d)


def set_pstyle_tracked(doc, p, style_name):
    sid = doc.name2id.get(style_name)
    if not sid:
        raise SystemExit('הסגנון "%s" אינו בקובץ - הוסף אותו קודם (add_styles.py)' % style_name)
    pPr = p.find(q("pPr"))
    if pPr is None:
        pPr = etree.Element(q("pPr")); p.insert(0, pPr)
    old = etree.Element(q("pPr"))
    for ch in pPr:
        if ch.tag not in (q("rPr"), q("sectPr"), q("pPrChange")):
            old.append(copy.deepcopy(ch))
    ps = pPr.find(q("pStyle"))
    if ps is None:
        ps = etree.Element(q("pStyle")); pPr.insert(0, ps)
    ps.set(q("val"), sid)
    ch = etree.Element(q("pPrChange"))
    ch.set(q("id"), doc.nid()); ch.set(q("author"), laukmi_mech.AUTHOR); ch.set(q("date"), laukmi_mech.DATE)
    ch.append(old)
    for e in pPr.findall(q("pPrChange")):
        pPr.remove(e)
    pPr.append(ch)


def deleted(p):
    pPr = p.find(q("pPr"))
    if pPr is None:
        return False
    rPr = pPr.find(q("rPr"))
    return rPr is not None and rPr.find(q("del")) is not None


def main(src, dst):
    doc = Doc(src)
    log = collections.Counter()
    ps = list(doc.paragraphs())
    st = [doc.pstyle(p) for p in ps]
    n = len(ps)

    def neighbor(i, step):
        """הפסקה הלא-ריקה הקרובה בכיוון, דרך ריקות וציוני דף"""
        j = i + step
        while 0 <= j < n:
            if deleted(ps[j]):
                j += step; continue
            if is_empty(ps[j]) or st[j] in TRANSPARENT:
                j += step; continue
            return j
        return None

    seps = [i for i in range(n) if (st[i] in BODYISH or st[i] == "חציצה") and is_sep(ps[i]) and not deleted(ps[i])]
    dels = set()
    for i in seps:
        a, b = neighbor(i, -1), neighbor(i, 1)
        if (a is not None and st[a] in HEADINGS) or (b is not None and st[b] in HEADINGS):
            dels.add(i)
    for i in sorted(dels):
        delete_paragraph(doc, ps[i]); log["חציצה צמודה לכותרת נמחקה"] += 1
    for i in seps:
        if i in dels:
            continue
        if st[i] != "חציצה":
            set_pstyle_tracked(doc, ps[i], "חציצה"); log["חציצה אוחדה לסגנון חציצה"] += 1
    for i in range(n):
        if i in dels or deleted(ps[i]):
            continue
        if st[i] in ("Normal", "רגיל", "0.1", "0.2", "List Paragraph") and is_empty(ps[i]):
            delete_paragraph(doc, ps[i]); log["פסקה ריקה נמחקה"] += 1
    doc.save(dst)
    for k, v in log.items():
        print('  %s: %d' % (k, v))
    print('נשמר', dst)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
