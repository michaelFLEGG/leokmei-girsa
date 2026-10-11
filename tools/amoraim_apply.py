# -*- coding: utf-8 -*-
"""amoraim_apply.py - מסמן בוורד, בעקוב אחר שינויים, שמות אמוראים שאינם בסגנון "אמוראים".

הזיהוי הוא כלל ר"ת של המנוע המכני (laukmi_rules.NAME_RT פחות NOT_NAME), אותו כלל
שהריץ את בכורות. הכתיבה: word_apply.apply, בשם "מנוע אמוראים". שם הסגנון נלקח
מן הקובץ עצמו (הסגנון השכיח ביותר בתפקיד "אמוראים").

    uv run python tools/amoraim_apply.py <קובץ.docx> <שם מסכת> [--dry]
"""
import os, sys, re, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'engine', 'laukmi-engine'))
from docx2json import convert
from styles_map import CS, role_of
import laukmi_rules as R
import word_apply

AUTHOR = 'מנוע אמוראים'


def plan(path):
    blocks = convert(path)
    am_names = {k for k, v in CS.items() if v == 'am'}
    cnt = collections.Counter(r['cs'] for b in blocks for r in b['runs'] if r.get('cs') in am_names)
    if not cnt:
        return [], None
    style = cnt.most_common(1)[0][0]
    rx = re.compile(R.NAME_RT[0])
    ops = []
    for b in blocks:
        if not str(role_of(b)).startswith('body'):
            continue
        t = b['text']
        fl = []
        for r in b['runs']:
            fl.extend([r.get('cs') in am_names] * len(r['t']))
        if len(fl) != len(t):
            continue
        for m in rx.finditer(t):
            w = m.group(1)
            if w in R.NOT_NAME or any(fl[m.start(1):m.end(1)]) :
                continue
            ops.append({'id': 'a%d_%d' % (b['i'], m.start(1)), 'kind': 'cstyle', 'style': style,
                        'context': t, 'find': w, 'at': m.start(1), 'daf': b.get('daf')})
    return ops, style


if __name__ == '__main__':
    path, mas = sys.argv[1], sys.argv[2]
    ops, style = plan(path)
    print('סגנון:', style, 'מועמדים:', len(ops))
    if '--dry' in sys.argv or not ops:
        sys.exit(0)
    rep = word_apply.apply(path, ops, AUTHOR, mas)
    print('הוחלו:', rep['applied'], 'אומת:', rep.get('verified'))
