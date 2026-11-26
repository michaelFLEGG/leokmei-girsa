# -*- coding: utf-8 -*-
"""החוקר - איחוד ההליכות המקבילות (חלקי המסכתות והאתרים) להליכה אחת.

  python tools/chokker/merge.py <תיקיית-יעד> <תיקייה1> <תיקייה2> ...
מעתיק גם את הצילומים, כדי שגיליונות המגע ייבנו מכל החלקים.
"""
import os, sys, io, json, shutil

dst = sys.argv[1]
os.makedirs(dst, exist_ok=True)
M = {'screens': [], 'print': [], 'buttons': [], 'net': {}, 'errors': [], 'parts': []}
for src in sys.argv[2:]:
    f = os.path.join(src, 'walk.json')
    if not os.path.exists(f):
        M['errors'].append('חלק חסר: %s' % os.path.basename(src))
        continue
    w = json.load(io.open(f, encoding='utf-8'))
    for k in ('screens', 'print', 'buttons', 'errors'):
        M[k] += w.get(k, [])
    for vp, n in (w.get('net') or {}).items():
        t = M['net'].setdefault(vp, {'foreign': {}, 'bad': {}, 'requests': 0})
        t['requests'] += n.get('requests', 0)
        for kk in ('foreign', 'bad'):
            for h, c in n.get(kk, {}).items():
                t[kk][h] = t[kk].get(h, 0) + c
    M['parts'].append({'src': os.path.basename(src), 'started': w.get('started'), 'finished': w.get('finished')})
    for sub in ('shots', 'print'):
        s = os.path.join(src, sub)
        if os.path.isdir(s):
            shutil.copytree(s, os.path.join(dst, sub), dirs_exist_ok=True)
json.dump(M, io.open(os.path.join(dst, 'walk.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('merged', len(M['screens']), 'screens', len(M['print']), 'prints', len(M['buttons']), 'buttons', len(M['errors']), 'errors')
