# -*- coding: utf-8 -*-
"""verses_apply.py - מסמן בוורד, בעקוב אחר שינויים, פסוקים שלא סומנו.

הזיהוי: tools/verses_check.py (התאמה לנוסח המקרא). הכתיבה: word_apply.apply,
שמגבה, מוודא שהקובץ אינו פתוח בוורד, רושם את העיצוב הקודם ב-w:rPrChange
ומאמת אחרי הכתיבה שהטקסט לא השתנה. כל סימון בשם "מנוע פסוקים".

    uv run python tools/verses_apply.py <קובץ.docx> <שם מסכת> [--dry]
"""
import os, sys, io, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from docx2json import convert
from styles_map import CS, role_of
import verses_check, word_apply

AUTHOR = 'מנוע פסוקים'
STYLE = 'פסוק תו'


def plan(path):
    ps = {k for k, v in CS.items() if v == 'ps'}
    blocks = convert(path)
    res = verses_check.scan_blocks(blocks, role_of, ps)
    ops, skipped = [], []
    for bi, txt, s in res:
        find = txt[s['a']:s['b']]
        b = blocks[bi]
        ops.append({'id': 'v%d_%d' % (bi, s['a']), 'kind': 'cstyle', 'style': STYLE,
                    'context': txt, 'find': find, 'at': s['a'], 'daf': b.get('daf'), 'ref': s['ref']})
    return ops, skipped


def main():
    path, mas = sys.argv[1], sys.argv[2]
    dry = '--dry' in sys.argv
    ops, skipped = plan(path)
    print('מועמדים:', len(ops), 'מדולגים:', len(skipped))
    for r, f, why in skipped:
        print('  דילוג', r, f[:40], why)
    if dry:
        for o in ops:
            print('  ', o['ref'], o['find'][:60])
        return
    rep = word_apply.apply(path, ops, AUTHOR, mas)
    print('הוחלו:', rep['applied'], 'אומת:', rep.get('verified'), 'גיבוי:', rep.get('backup'))
    for op, why in rep['missed']:
        print('  לא הוחל', op.get('ref'), op['find'][:40], '-', why)


if __name__ == '__main__':
    main()
