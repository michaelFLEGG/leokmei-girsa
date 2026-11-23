# -*- coding: utf-8 -*-
"""פרומפט 87 - השלמת חוסר חלקי בתיבות המשנה, על הנוסח החי (מצב הנתונים בדפדפן אחרי /live).

    python _work/p87/run_mishna.py DD_DIR [slug ...]     -> _work/p87/out/mishna-<slug>.json
DD_DIR: קובצי {rows} שנמשכו מן הדפדפן (dumpd.js).
החלטה לכל חוסר:
  fix      - חוסר של 3 מילים ומעלה בתוך תיבה, עם עוגן חזק משני צדדיו (או בקצה התיבה), בלי ניסוח אחר במקומו
  move     - כמו fix, והחסר יושב כשורת גמרא בין שני חלקי אותה תיבה: מושלם בתיבה, והשורה הכפולה בחוץ נמחקת
  outside  - החסר נמצא כשורת גמרא סמוכה (התיבה הפכה לגמרא?) - לעיון, לא נוגעים
  box      - חסרה משנה שלמה (או תיבה שלמה של הבבלי) - לעיון
  rephrase - בתיבה ניסוח אחר במקום החסר - לעיון
  weak     - העוגן חלש (מילה בודדת) - לעיון
"""
import os, sys, re, json, io, html, difflib, time

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(HERE, 'tools'))
import mishna_gaps as MG
from mishna_gaps import decide, plain

NIK = re.compile('[֑-ׇ]')
T0 = [int(time.time() * 1000)]


def tnext():
    T0[0] += 1
    return T0[0]


def run(slug, dd):
    d = json.load(io.open(os.path.join(dd, slug + '.json'), encoding='utf-8'))
    rows = d['rows']
    chs = MG.canon(slug)
    if not chs:
        return {'slug': slug, 'skip': 'אין משניות'}
    F = MG.analyze(slug, rows, chs)
    res = [decide(slug, rows, f, chs) for f in F]
    return {'slug': slug, 'when': d.get('when'), 'items': res}


if __name__ == '__main__':
    dd = sys.argv[1]
    slugs = sys.argv[2:] or sorted(f[:-5] for f in os.listdir(dd) if f.endswith('.json'))
    od = os.path.join(HERE, '_work', 'p87', 'out')
    os.makedirs(od, exist_ok=True)
    for s in slugs:
        r = run(s, dd)
        io.open(os.path.join(od, 'mishna-%s.json' % s), 'w', encoding='utf-8').write(json.dumps(r, ensure_ascii=False, indent=1))
        from collections import Counter
        print(s, dict(Counter(x['decision'] for x in r.get('items') or [])))
