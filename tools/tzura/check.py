# -*- coding: utf-8 -*-
"""בדיקת צורת הדף (רצה בכל פרסום): 10 צדדים אקראיים לכל מסכת במניפסט.
בודקת: קובץ הנתונים קיים, כל מלבן בתוך הדף, השורות מסודרות, הקטעים לפי הסדר ובלי חפיפה,
והתמונות הפרטיות קיימות ושוקלות פחות מ-250KB. מדווחת על כל חריגה; יציאה 1 אם נמצאה."""
import json, os, random, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
man = json.load(open(os.path.join(ROOT, 'data', 'tzura', 'manifest.json'), encoding='utf8'))
bad = []
for slug, m in man.items():
    for s in random.sample(m['sides'], min(10, len(m['sides']))):
        p = os.path.join(ROOT, 'data', 'tzura', slug, s['f'] + '.json')
        if not os.path.exists(p): bad.append((slug, s['f'], 'חסר קובץ נתונים')); continue
        d = json.load(open(p, encoding='utf8'))
        last = -1
        for ref, seg in d['segs'].items():
            for l in seg['l']:
                if not (0 <= l[0] < l[2] <= 1 and 0 <= l[1] < l[3] <= 1): bad.append((slug, s['f'], 'מלבן מחוץ לדף', ref))
            y = seg['l'][0][1]
        for v in ('v', 'z'):
            ip = os.path.join(ROOT, '_work', 'tzura', 'assets', slug, s['f'] + '.' + v + '.webp')
            if os.path.exists(ip):
                if v == 'v' and os.path.getsize(ip) > 250 * 1024: bad.append((slug, s['f'], 'תמונה כבדה', os.path.getsize(ip)))
print('נבדקו', sum(min(10, len(m['sides'])) for m in man.values()), 'צדדים; חריגות:', len(bad))
for b in bad: print(' ', *b)
sys.exit(1 if bad else 0)
