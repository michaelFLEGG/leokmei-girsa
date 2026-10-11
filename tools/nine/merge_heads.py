# -*- coding: utf-8 -*-
"""merge_heads.py <מסכת> - מאחד את heads-NNN.json לקובץ heads\<מסכת>\merged.json עבור heading_insert_word.py, עם אימות מקום וטביעה."""
import sys, os, io, json, glob, re
M = sys.argv[1]
D = os.path.join(r'C:\Users\Owner\leokmei-nine-work\heads', M)
fps = json.load(io.open(os.path.join(D, 'fingerprints.json'), encoding='utf-8'))
code = {}
for f in glob.glob(os.path.join(D, 'chunk-*.txt')):
    for line in io.open(f, encoding='utf-8'):
        p = line.rstrip('\n').split('|', 2)
        if len(p) == 3 and p[1] != 'c':
            code[int(p[0])] = p[1]
out, rej = [], {}
seen = set()
def rj(why): rej[why] = rej.get(why, 0) + 1
items = []
for f in sorted(glob.glob(os.path.join(D, 'heads-*.json'))):
    try:
        items += json.load(io.open(f, encoding='utf-8'))
    except Exception as e:
        print('קובץ פגום', f, e)
for it in sorted(items, key=lambda x: x.get('i', 0)):
    i = it.get('i'); h = (it.get('head') or '').strip()
    if not isinstance(i, int) or not h: rj('חסר'); continue
    if i in seen: rj('כפול'); continue
    if code.get(i) not in ('a', 'g'): rj('קוד פסקה לא מתאים (%s)' % code.get(i)); continue
    if len(h) > 60: rj('ארוכה'); continue
    if re.search('[\u2013\u2014\u2015]', h): rj('מקף ארוך'); continue
    if re.search(r'[a-zA-Z]', h): rj('לטינית'); continue
    near = [code.get(j) for j in range(i - 2, i)]
    if any(c in ('n', 'd', 'p') for c in near): rj('צמוד לכותרת'); continue
    if str(i) not in fps: rj('אין טביעה'); continue
    seen.add(i)
    out.append({'file': M + '.docx', 'i': i, 'head': h, 'at_h': fps[str(i)]})
json.dump(out, io.open(os.path.join(D, 'merged.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(M, 'כותרות תקינות:', len(out), '| נדחו:', rej)
