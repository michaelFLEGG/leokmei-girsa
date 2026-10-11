# -*- coding: utf-8 -*-
"""adv_prep.py - הכנת יחידות עבודה (שני דפים = ארבעה עמודים) למנוע המתקדם על שבת.
קלט: שבת.docx מתיקיית prod, ומקורות שבת. פלט: יחידות adv/unit-NN: in.txt ו-src.md."""
import sys, os, re, io, json, html
sys.path.insert(0, r'C:\Users\Owner\leokmei-girsa-nine\tools'); sys.path.insert(0, r'C:\Users\Owner\leokmei-girsa-nine\engine\laukmi-engine')
import laukmi_mech, masechet_fmt as mf
from laukmi_mech import Doc
OUT = r'C:\Users\Owner\leokmei-nine-work\adv'
os.makedirs(OUT, exist_ok=True)
DOC = r'C:\Users\Owner\leokmei-nine-work\prod\שבת.docx'
SRC = r'C:\Users\Owner\leokmei-girsa-nine\data\sources\shabbat.json'
CODE = {'חלון 3': 'a', 'משניות': 'm', "ד''ה משנה": 'd', 'נושא': 'n', 'חציצה': 'h', 'דף בצד': 'f', 'פתיחת פרק': 'p', 'פרק': 'p', 'פרק שם': 'p',
        'הדרן': 'r', 'הדרן עלך': 'r', 'דפים בפרק ב': 'o', 'מסכת': 'o', 'משנה בצד': 'o', 'Normal': 'g', 'פיסקת תשובה': 'g', 'List Paragraph': 'g', 'רווח לפני': 'g', 'הסבר': 'g'}
doc = Doc(DOC)
rows = []
daf = None
dafs = []
for i, p in enumerate(doc.paragraphs()):
    st = doc.pstyle(p); t = mf.live(p).replace('\n', ' ').strip()
    c = CODE.get(st, 'g' if st.startswith('0.') else 'o')
    if c == 'f' and t:
        daf = t.strip()
        if daf not in dafs: dafs.append(daf)
        rows.append((i, c, daf, t)); continue
    rows.append((i, c, daf, t))
print('עמודים', len(dafs), dafs[:6], dafs[-3:])
# יחידות של 4 עמודים
units = [dafs[k:k + 4] for k in range(0, len(dafs), 4)]
src = json.load(io.open(SRC, encoding='utf-8'))
pages = src['pages']
TAG = re.compile(r'<[^>]+>')
manifest = []
for n, ds in enumerate(units, 1):
    d = os.path.join(OUT, 'unit-%02d' % n); os.makedirs(d, exist_ok=True)
    dset = set(ds)
    with io.open(os.path.join(d, 'in.txt'), 'w', encoding='utf-8') as f:
        for i, c, dd, t in rows:
            if dd in dset and (t or c in 'dnh'):
                f.write('%d|%s|%s\n' % (i, c, t))
    with io.open(os.path.join(d, 'src.md'), 'w', encoding='utf-8') as f:
        for dd in ds:
            pg = pages.get(dd) or pages.get(dd.strip())
            f.write('## %s\n' % dd)
            if not pg: f.write('(אין במקורות)\n\n'); continue
            f.write('### גמרא\n%s\n\n' % '\n'.join(html.unescape(TAG.sub('', x)) for x in pg.get('gemara', [])))
            f.write('### פירוש הגמרא\n%s\n\n' % '\n'.join(html.unescape(TAG.sub('', x)) for x in pg.get('perush', [])))
    manifest.append({'unit': n, 'dafim': ds})
json.dump(manifest, io.open(os.path.join(OUT, 'manifest.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('יחידות', len(units))

