# -*- coding: utf-8 -*-
"""split_nine.py - פיצול ארבעת הקבצים המאוחדים של 2023 לקובץ אחד לכל מסכת.
חיתוך לפי ילדי הגוף (פסקאות). שאר חלקי הקובץ (סגנונות, גופנים, מספור, כותרות עליונות) נשמרים כמות שהם.
הרצה: uv run --with lxml python split_nine.py <תיקיית מקור> <תיקיית יעד>
"""
import sys, os, zipfile, io, re, json
from lxml import etree
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
q = lambda t: '{%s}%s' % (W, t)

SRC, DST = sys.argv[1], sys.argv[2]
os.makedirs(DST, exist_ok=True)

# (קובץ מקור, שם יעד, פסקה ראשונה, פסקה אחרונה לא כולל) - אינדקס בין ילדי הגוף
PLAN = [
    ('2שבת 194.docx', 'שבת.docx', 0, None),
    ('3עירובין 125.docx', 'עירובין.docx', 0, None),
    ('16זבחים מנחות חולין465.docx', 'זבחים.docx', 0, 5196),
    ('16זבחים מנחות חולין465.docx', 'מנחות.docx', 5196, 10660),
    ('17בכרורת ערכין     תמורה כריתות מעילה נדה 400.docx', 'ערכין.docx', 3304, 5340),
    ('17בכרורת ערכין     תמורה כריתות מעילה נדה 400.docx', 'תמורה.docx', 5340, 7225),
    ('17בכרורת ערכין     תמורה כריתות מעילה נדה 400.docx', 'כריתות.docx', 7225, 9203),
    ('17בכרורת ערכין     תמורה כריתות מעילה נדה 400.docx', 'מעילה.docx', 9203, 9964),
    ('17בכרורת ערכין     תמורה כריתות מעילה נדה 400.docx', 'נדה.docx', 9964, None),
]
# חלקים שנמחקים במכוון (באתר כבר יש גרסה מעודכנת): חולין שבקובץ 16 (10662-), בכורות שבקובץ 17 (0-3304)

def text(p):
    return ''.join(t.text or '' for t in p.iter(q('t')))

report = []
for src, dst, a, b in PLAN:
    zin = zipfile.ZipFile(os.path.join(SRC, src))
    root = etree.fromstring(zin.read('word/document.xml'))
    body = root.find(q('body'))
    kids = list(body)
    sect = kids[-1]
    assert sect.tag == q('sectPr'), 'אין sectPr סופי'
    paras = kids[:-1]
    n = len(paras)
    hi = n if b is None else b
    for i, p in enumerate(paras):
        if i < a or i >= hi:
            body.remove(p)
    kept = [p for p in body if p.tag == q('p')]
    first = next((text(p).strip() for p in kept if text(p).strip()), '')
    last = next((text(p).strip() for p in reversed(kept) if text(p).strip()), '')
    out = os.path.join(DST, dst)
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as zo:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == 'word/document.xml':
                data = etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True)
            zo.writestr(item, data)
    zin.close()
    report.append({'file': dst, 'from': src, 'paras': len(kept), 'first': first[:40], 'last': last[:60]})
    print(dst, len(kept), '|', first[:30], '|', last[:50])
json.dump(report, io.open(os.path.join(DST, 'split-report.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

