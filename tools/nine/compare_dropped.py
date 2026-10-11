# -*- coding: utf-8 -*-
"""compare_dropped.py - השוואת חלק שנמחק (חולין בקובץ 16, בכורות בקובץ 17) מול הקובץ המעודכן שבאתר.
ברמת הדף: אילו דפים חסרים בקובץ המעודכן, ובאילו דפים אורך הטקסט המעודכן קטן מאוד מן הישן.
הרצה: uv run --with lxml python compare_dropped.py <ישן.docx> <התחלה> <סוף> <חדש.docx> <פלט.json>
"""
import sys, zipfile, re, io, json, collections
from lxml import etree
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
q = lambda t: '{%s}%s' % (W, t)
GEM = {'א':1,'ב':2,'ג':3,'ד':4,'ה':5,'ו':6,'ז':7,'ח':8,'ט':9,'י':10,'כ':20,'ל':30,'מ':40,'נ':50,'ס':60,'ע':70,'פ':80,'צ':90,'ק':100,'ר':200,'ש':300,'ת':400}
NIK = re.compile(r'[֑-ׇ]')

def load(path, lo=0, hi=None):
    z = zipfile.ZipFile(path)
    root = etree.fromstring(z.read('word/document.xml'))
    st = etree.fromstring(z.read('word/styles.xml'))
    sid = {s.get(q('styleId')): s.find(q('name')).get(q('val')) for s in st.findall(q('style')) if s.find(q('name')) is not None}
    body = root.find(q('body'))
    ps = [p for p in body if p.tag == q('p')]
    hi = len(ps) if hi is None else hi
    out = []
    for p in ps[lo:hi]:
        # טקסט חי בלבד: בלי delText
        t = ''.join(x.text or '' for x in p.iter(q('t')))
        pst = p.find(q('pPr') + '/' + q('pStyle'))
        sname = sid.get(pst.get(q('val')), pst.get(q('val'))) if pst is not None else ''
        out.append((sname, t))
    return out

def daf_key(t):
    t = t.strip()
    am = 1 if t.endswith(':') else 0
    t = re.sub(r"[.:\"'׳״\s\-–()]", '', t)
    n = sum(GEM.get(c, 0) for c in t)
    return (n * 2 + am) if n else None

def by_daf(paras):
    cur = None; d = collections.OrderedDict()
    for s, t in paras:
        if s.startswith('דף בצד'):
            k = daf_key(t)
            if k is not None: cur = k; d.setdefault(cur, [])
            continue
        if cur is None or not t.strip(): continue
        d[cur].append(t)
    return d

def words(texts):
    return re.findall(r'[א-ת]+', NIK.sub('', ' '.join(texts)))

old = by_daf(load(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]) if sys.argv[3] != '-' else None))
new = by_daf(load(sys.argv[4]))
rep = {'old_dapim': len(old), 'new_dapim': len(new), 'missing_in_new': [], 'much_shorter': [], 'ok': 0}
for k, texts in old.items():
    wo = words(texts)
    if k not in new:
        rep['missing_in_new'].append({'daf_key': k, 'words': len(wo), 'text': ' '.join(texts)[:400]})
        continue
    wn = words(new[k])
    if len(wo) >= 25 and len(wn) < 0.35 * len(wo):
        rep['much_shorter'].append({'daf_key': k, 'old_words': len(wo), 'new_words': len(wn)})
    else:
        rep['ok'] += 1
json.dump(rep, io.open(sys.argv[5], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print({k: (v if not isinstance(v, list) else len(v)) for k, v in rep.items()})
