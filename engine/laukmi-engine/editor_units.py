# -*- coding: utf-8 -*-
"""מפיק את יחידות העבודה של העורך המתקדם (ב5): שני דפים (ארבעה צדדים) לכל
יחידה, בפרקים א ו-ב של בכורות, לפי כותרות הפרק שבקובץ עצמו. לכל יחידה:
פסקאות לאוקמי גירסא (אינדקס, סגנון, טקסט חי), הגמרא ופירוש הגמרא של אותם
דפים."""
import sys, re, json, io
sys.stdout.reconfigure(encoding='utf-8')
import laukmi_mech as m, masechet_daf as D
src = sys.argv[1]; out = sys.argv[2]
d = m.Doc(src); ps = list(d.paragraphs())
st = [d.pstyle(p) for p in ps]; tx = [m.text_map(p)[0] for p in ps]
def find(style, startswith):
    for i in range(len(ps)):
        if st[i] == style and tx[i].strip().startswith(startswith): return i
c1 = find('פרק', 'פרק ראשון'); c3 = find('פרק', 'פרק שלישי')
assert c1 is not None and c3 is not None, (c1, c3)
marks = [(i, D.side(tx[i])) for i in range(len(ps)) if st[i] == 'דף בצד' and tx[i].strip() and c1 <= i < c3]
first = marks[0][1]; last = marks[-1][1]
src_pages = json.load(open('C:/leokmei-girsa/data/sources/bekhorot.json', encoding='utf-8'))['pages']
by = {v['daf']: v for v in src_pages.values()}
def clean(h): return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', h or '')).strip()
def ref_daf(side):
    n, b = divmod(side, 2); return '%d%s' % (n, 'b' if b else 'a')
units = []
s = first
while s <= last:
    sides = list(range(s, min(s + 4, last + 1)))
    startp = next(i for i, sd in marks if sd == sides[0])
    nxt = [i for i, sd in marks if sd == sides[-1] + 1]
    endp = nxt[0] if nxt else c3
    paras = [{'i': i, 'style': st[i], 'text': tx[i]} for i in range(startp, endp) if tx[i].strip()]
    pages = []
    for sd in sides:
        v = by.get(ref_daf(sd))
        if v: pages.append({'daf': ref_daf(sd), 'gemara': [clean(g) for g in v['gemara']],
                            'perush': [clean(x) for x in (v.get('perush') or [])]})
    units.append({'name': '%s-%s' % (D.label_of(sides[0]), D.label_of(sides[-1])), 'paras': paras, 'pages': pages})
    s += 4
json.dump(units, open(out, 'w', encoding='utf-8'), ensure_ascii=False)
print(len(units), 'יחידות;', [(u['name'], len(u['paras'])) for u in units], 'פרק א-ב: פסקאות', c1, '-', c3)
