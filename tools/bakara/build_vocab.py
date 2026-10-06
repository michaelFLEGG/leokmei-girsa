# -*- coding: utf-8 -*-
"""build_vocab.py - אוצר המילים של הספר עצמו (כל קובצי הוורד), לשכבת הקוד של הבקרה.

    python3 tools/bakara/build_vocab.py <תיקיית ה-docx> <out.json>

הפלט אינו נשמר במאגר (כ-3MB): הוא נבנה מחדש לפני כל הרצה, בכחצי דקה.
"""
import sys, os, re, json, glob, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE)))
from docx2json import convert
W = re.compile(r'[א-ת][א-ת"\']*[א-ת\']|[א-ת]')
cnt = collections.Counter(); per = collections.defaultdict(set)
for f in glob.glob(os.path.join(sys.argv[1], '*.docx')):
    for b in convert(f):
        for w in W.findall(b['text']):
            cnt[w] += 1; per[w].add(os.path.basename(f))
json.dump({'cnt': cnt, 'nf': {w: len(s) for w, s in per.items()}}, open(sys.argv[2], 'w', encoding='utf-8'), ensure_ascii=False)
print(len(cnt), 'מילים')
