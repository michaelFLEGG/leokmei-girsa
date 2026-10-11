# -*- coding: utf-8 -*-
import sys, zipfile, io, collections, json, os
from lxml import etree
sys.path.insert(0, r'C:\Users\Owner\leokmei-girsa-nine\tools')
from styles_map import ROLE, CS, ALIAS
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
q = lambda t: '{%s}%s' % (W, t)

def report(path):
    z = zipfile.ZipFile(path)
    root = etree.fromstring(z.read('word/document.xml'))
    st = etree.fromstring(z.read('word/styles.xml'))
    sid, stype, based = {}, {}, {}
    for s in st.findall(q('style')):
        n = s.find(q('name'))
        if n is None: continue
        sid[s.get(q('styleId'))] = n.get(q('val')); stype[n.get(q('val'))] = s.get(q('type'))
    pc, cc = collections.Counter(), collections.Counter()
    for p in root.iter(q('p')):
        ps = p.find(q('pPr') + '/' + q('pStyle'))
        nm = sid.get(ps.get(q('val')), ps.get(q('val'))) if ps is not None else 'Normal'
        pc[nm] += 1
    for r in root.iter(q('rStyle')):
        cc[sid.get(r.get(q('val')), r.get(q('val')))] += 1
    return pc, cc, set(stype)

if __name__ == '__main__':
    gold_p, gold_c, gold_defs = report(sys.argv[1])
    for f in sys.argv[2:]:
        pc, cc, defs = report(f)
        print('====', os.path.basename(f))
        print(' פסקה:', ', '.join('%s=%d%s' % (k, v, '' if (ALIAS.get(k, k) in ROLE) else '[?]') for k, v in pc.most_common()))
        print(' תו:', ', '.join('%s=%d%s' % (k, v, '' if k in CS else '[?]') for k, v in cc.most_common()))
        need = ['חלון 3', 'נושא', 'רווח לפני', 'רגיל ללא רווח', 'הסבר', 'אמוראים', 'אמוראים תו', 'אמוראים תו 2', 'פסוק', 'פסוק תו', 'חציצה', 'ד\'\'ה משנה', 'תנאי המשנה', 'הסבר במשנה',
                'פתיחת פרק', 'הדרן', 'מספר קטע', 'משנה בצד', 'נושא משנה', 'דף בצד', 'משניות']
        print(' חסרים בהגדרות:', [n for n in need if n not in defs])
