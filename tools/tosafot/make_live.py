# -*- coding: utf-8 -*-
"""make_live.py - מרכיב את tosafot/<slug>/live-<perek>.json: רק התוספות שנכתב להם סיכום ויש להם עוגן.

הבנייה של האתר (build_site.py) קוראת את הקובץ הזה בלבד. הספירה (count-N.json) קבועה ואינה משתנה כאן.
נוסח ברירת המחדל בדף הוא נוסח א (שורה אחת, לפי בחירת המנהל ב-11.10.2026) עד שהמנהל בוחר, והבחירה נמשכת מנקודת הקליטה.

    uv run python tools/tosafot/make_live.py kiddushin 1
"""
import os, sys, json, io
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    slug, perek = sys.argv[1], int(sys.argv[2])
    d = os.path.join(ROOT, 'tosafot', slug)
    count = json.load(io.open(os.path.join(d, 'count-%d.json' % perek), encoding='utf-8'))
    anchors = json.load(io.open(os.path.join(d, 'anchors-%d.json' % perek), encoding='utf-8'))
    styles = json.load(io.open(os.path.join(d, 'styles-%d.json' % perek), encoding='utf-8'))
    items, missing = [], []
    for r in count['items']:
        k = str(r['n'])
        if k not in styles:
            continue
        a = anchors.get(k)
        if not a:
            missing.append(k)
            continue
        if a['daf'] != r['dafKey']:
            raise SystemExit('עצירה: עוגן %s על עמוד %s אך התוספות בעמוד %s' % (k, a['daf'], r['dafKey']))
        s = styles[k]
        # page: העמוד באתר שבו יושב הטקסט (כשהוא שונה מעמוד התוספות; ראה anchors-N.json)
        items.append({'n': r['n'], 'hn': r['hn'], 'daf': a.get('page', r['dafKey']), 'dh': r['dh'], 'line': r['line'],
                      'ref': r['ref'], 'url': r['url'], 'text': r['text'],
                      'sum': s.get('a') or s['b'], 't': a['t'], 'occ': a.get('occ', 1), 'rule': a.get('rule', 1)})
    if missing:
        raise SystemExit('עצירה: אין עוגן לתוספות: %s' % ', '.join(missing))
    out = {'slug': slug, 'perek': perek, 'total': count['total'], 'items': items}
    with io.open(os.path.join(d, 'live-%d.json' % perek), 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print('live-%d.json: %d תוספות' % (perek, len(items)))


if __name__ == '__main__':
    main()
