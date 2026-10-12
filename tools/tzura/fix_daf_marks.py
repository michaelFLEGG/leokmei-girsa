# -*- coding: utf-8 -*-
"""תיקון סימני "דף בצד" בקובץ וורד (ביצה, 12.10.2026), כל שינוי כשינוי במעקב (מחבר "Claude"), הפיך בוורד.

  uv run --with lxml python tools/tzura/fix_daf_marks.py <קובץ.docx> <פלט.docx>

הוראות התיקון (מספרי פסקה = אינדקס בלוק כפי ש-docx2json נותן, מטבלת ההצמדה לספריא):
  insert: סימן חסר, נכנס כפסקה חדשה לפני הבלוק
  relabel: סימן שנוסחו שגוי
  delete: סימן כפול באמצע צד
"""
import sys, copy, zipfile, datetime
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.dirname(__file__)))
from lxml import etree
import docx2json

WNS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
W = '{%s}' % WNS
XML = '{http://www.w3.org/XML/1998/namespace}'
AUTHOR = 'Claude'
DATE = '2026-10-12T12:00:00Z'

INSERT = [(0, 'ב.'), (20, 'ב:'), (327, 'ח:'), (959, 'יז:'), (1011, 'יח:'), (1262, 'כב:'), (1454, 'כה:'),
          (1999, 'לד.'), (2111, 'לו.'), (2182, 'לז.'), (2242, 'לח.')]
RELABEL = [(1083, 'כ.'), (1663, 'כח:')]
DELETE = [221, 725, 2089]


def main(src, dst):
    blocks = docx2json.convert(src)
    pmap = docx2json.convert.last['pmap']
    z = zipfile.ZipFile(src)
    doc = etree.fromstring(z.read('word/document.xml'))
    body = doc.find(W + 'body')
    paras = body.findall(W + 'p')
    ids = [int(e.get(W + 'id')) for e in doc.iter() if e.get(W + 'id', '').isdigit()]
    nid = [max(ids + [0]) + 1000]

    def rev(tag):
        e = etree.Element(W + tag)
        e.set(W + 'id', str(nid[0])); nid[0] += 1
        e.set(W + 'author', AUTHOR); e.set(W + 'date', DATE)
        return e

    def para_of(bi):
        return paras[pmap[bi]]

    def mark_text(p):
        return ''.join(t.text or '' for t in p.iter(W + 't')).strip()

    def new_run(text):
        r = etree.Element(W + 'r')
        rp = etree.SubElement(r, W + 'rPr')
        rf = etree.SubElement(rp, W + 'rFonts'); rf.set(W + 'hint', 'cs')
        etree.SubElement(rp, W + 'rtl')
        t = etree.SubElement(r, W + 't'); t.text = text
        return r

    def kill_runs(p):
        """עוטף כל ריצה חיה במחיקה במעקב."""
        for r in list(p.findall(W + 'r')):
            for t in r.findall(W + 't'):
                t.tag = W + 'delText'
                t.set(XML + 'space', 'preserve')
            d = rev('del')
            r.addprevious(d)
            d.append(r)

    def mark_para_rpr(p, tag):
        ppr = p.find(W + 'pPr')
        if ppr is None:
            ppr = etree.Element(W + 'pPr'); p.insert(0, ppr)
        rpr = ppr.find(W + 'rPr')
        if rpr is None:
            rpr = etree.SubElement(ppr, W + 'rPr')
        rpr.insert(0, rev(tag))

    # תבנית: הסימן הראשון הקיים
    tmpl = None
    for b in blocks:
        if b['style'] == 'דף בצד' and b['text'].strip():
            tmpl = para_of(b['i']); break
    log = []
    # שינויים על פסקאות קיימות (לפני ההכנסות, כדי שהאינדקסים יישארו תקפים)
    for bi in DELETE:
        p = para_of(bi); old = mark_text(p)
        kill_runs(p); mark_para_rpr(p, 'del')
        log.append('נמחק סימן כפול "%s" (בלוק %d)' % (old, bi))
    for bi, new in RELABEL:
        p = para_of(bi); old = mark_text(p)
        kill_runs(p)
        ins = rev('ins'); ins.append(new_run(new)); p.append(ins)
        log.append('סימן "%s" שונה ל-"%s" (בלוק %d)' % (old, new, bi))
    for bi, label in INSERT:
        anchor = para_of(bi)
        p = copy.deepcopy(tmpl)
        for ch in list(p):
            if ch.tag != W + 'pPr':
                p.remove(ch)
        for a in list(p.attrib):
            if a.startswith(W + 'rsid'):
                del p.attrib[a]
        # סימן הפסקה עצמו נכנס במעקב
        ppr = p.find(W + 'pPr'); rpr = ppr.find(W + 'rPr')
        if rpr is None:
            rpr = etree.SubElement(ppr, W + 'rPr')
        rpr.insert(0, rev('ins'))
        ins = rev('ins'); ins.append(new_run(label)); p.append(ins)
        anchor.addprevious(p)
        log.append('נוסף סימן "%s" לפני בלוק %d' % (label, bi))
    out = etree.tostring(doc, xml_declaration=True, encoding='UTF-8', standalone=True)
    zo = zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED)
    for it in z.infolist():
        zo.writestr(it, out if it.filename == 'word/document.xml' else z.read(it.filename))
    zo.close()
    print('\n'.join(log))


main(sys.argv[1], sys.argv[2])
