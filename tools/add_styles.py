# -*- coding: utf-8 -*-
"""add_styles.py - מוסיף לקובץ וורד סגנונות שחסרים בו, בהעתקה מקובץ מקור.

מסכת שלא עברה את המנועים (בכורות) חסרים בה סגנונות שהמנועים נשענים
עליהם (חלון 3, אמוראים תו 2, הסבר, נושא, חציצה, פסוק תו, אמוראים תו).
בלעדיהם make_anchor מחזיר None בשקט, והעוגנים אינם נוצרים. הכלי מעתיק את
הגדרות הסגנונות מקובץ חולין, לפי השם, ואינו נוגע בגוף המסמך.
הוספת הגדרת סגנון אינה שינוי טקסט ואינה במעקב.

    python add_styles.py <יעד.docx> <מקור.docx> <פלט.docx> שם1 שם2 ...
"""
import sys, io, zipfile, copy
from lxml import etree

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
q = lambda t: '{%s}%s' % (W, t)


def styles_of(path):
    z = zipfile.ZipFile(path)
    return z, etree.fromstring(z.read('word/styles.xml'))


def by_name(root):
    out = {}
    for st in root.findall(q('style')):
        n = st.find(q('name'))
        if n is not None:
            out[n.get(q('val'))] = st
    return out


def add(dst, src, out, names):
    zd, rd = styles_of(dst)
    zs, rs = styles_of(src)
    dn, sn = by_name(rd), by_name(rs)
    ids = {st.get(q('styleId')) for st in rd.findall(q('style'))}
    sid2st = {st.get(q('styleId')): st for st in rs.findall(q('style'))}
    added, remap = [], {}

    def ensure(name):
        if name in dn:
            return dn[name].get(q('styleId'))
        st = sn.get(name)
        if st is None:
            raise SystemExit('הסגנון "%s" אינו במקור' % name)
        new = copy.deepcopy(st)
        sid = new.get(q('styleId'))
        if sid in ids:                      # אותו מזהה לשם אחר: מזהה חדש
            k = 1
            while 'z%d%s' % (k, sid) in ids:
                k += 1
            sid = 'z%d%s' % (k, sid)
            new.set(q('styleId'), sid)
        ids.add(sid)
        rd.append(new)
        dn[name] = new
        added.append(name)
        for tag in ('basedOn', 'link', 'next'):
            e = new.find(q(tag))
            if e is not None:
                ref = sid2st.get(e.get(q('val')))
                if ref is None:
                    new.remove(e)
                    continue
                rn = ref.find(q('name')).get(q('val'))
                e.set(q('val'), ensure(rn))
        return sid

    for n in names:
        ensure(n)
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for nme in zd.namelist():
            if nme == 'word/styles.xml':
                z.writestr(nme, etree.tostring(rd, xml_declaration=True, encoding='UTF-8', standalone=True))
            else:
                z.writestr(nme, zd.read(nme))
    return added


if __name__ == '__main__':
    a = add(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:])
    print('נוספו:', ', '.join(a) if a else 'כלום')
