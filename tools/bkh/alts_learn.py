# -*- coding: utf-8 -*-
"""alts_learn.py - שולף את יומן ההכרעות של "בחר נוסח" מנקודת הקליטה וכותב אותו לריפו ולדרייב.

    uv run python alts_learn.py bekhorot

כותב: data/alts/decisions-<slug>.json (בריפו) ו-_שומר\למידה\נוסחאות-<slug>.md (בדרייב), עם: הקטע, החלופות,
התגים, מה נבחר, והאם נערך. אחרי כל 10 הכרעות - לסכם כללים ל"כללים-שנלמדו.md" ולדף הכיול (ידנית או במנוע הלמידה).
המפתח: Documents\לאוקמי-מפתח-מנהל.txt (שורה 2), כמו שאר כלי הקליטה. דורש כותרת x-admin-key ו-User-Agent.
"""
import sys, io, os, json, urllib.request
API = 'https://leokmei-suggest.m7654301.workers.dev'
KEY = os.path.join(os.path.expanduser('~'), 'Documents', 'לאוקמי-מפתח-מנהל.txt')
DRIVE = os.path.join(os.path.expanduser('~'), 'Desktop', 'שיננא לHTML', '_שומר', 'למידה')
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))


def main(slug):
    key = io.open(KEY, encoding='utf-8').read().split('\n')[1].strip()
    rq = urllib.request.Request(API + '/alt?slug=' + slug, headers={'x-admin-key': key, 'User-Agent': 'leokmei-alts-learn/1'})
    doc = json.load(urllib.request.urlopen(rq, timeout=30))['doc']
    out = os.path.join(REPO, 'data', 'alts', 'decisions-%s.json' % slug)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(doc, io.open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    os.makedirs(DRIVE, exist_ok=True)
    md = ['# הכרעות "בחר נוסח" - %s' % slug, '', 'נקודות שהוכרעו: %d' % len(doc.get('picks', {})), '']
    for r in doc.get('log', []):
        md.append('## %s (דף %s)' % (r.get('id'), r.get('daf', '')))
        for i, v in enumerate(r.get('variants', [])):
            md.append('- %s%s: %s' % ('**נבחר** ' if i == r.get('v') else '', v.get('t', ''), v.get('x', '')))
        if r.get('v', -1) < 0 or r.get('edited'):
            md.append('- **נערך בידי המנהל**: %s' % r.get('txt', ''))
        md.append('')
    io.open(os.path.join(DRIVE, 'נוסחאות-%s.md' % slug), 'w', encoding='utf-8').write('\n'.join(md))
    print('הכרעות ביומן: %d' % len(doc.get('log', [])))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main(sys.argv[1] if len(sys.argv) > 1 else 'bekhorot')
