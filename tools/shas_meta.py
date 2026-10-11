# -*- coding: utf-8 -*-
"""shas_meta.py - משלים את נתוני העזר של מערכת הלומד (אורך עמודים, פרקים) מדפי
המסכתות שכבר נבנו, בלי בנייה מחדש. בנייה חלקית (--only) משאירה בסטטוס מסכתות
בלי נתונים כאלה; הכלי הזה ממלא אותם ומרענן את shas.json ו-shas.js."""
import os, io, re, json, html, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
SITE = os.path.join(ROOT, 'site')


def words(h):
    return len(html.unescape(re.sub(r'<[^>]+>', ' ', h or '')).split())


def meta_of(path):
    h = io.open(path, encoding='utf-8').read()
    i = h.index('const DATA=') + len('const DATA=')
    d = json.JSONDecoder().raw_decode(h[i:])[0]
    dafim, perakim, last = [], [], None
    for p in d['pages']:
        n = 0
        for u in p['units']:
            if u['k'] in ('u', 'm', 'dh', 'nose'):
                n += words(u.get('a')) + sum(words(x[1]) for x in u.get('l', []))
        dafim.append([(p.get('daf') or '').strip(), n])
        key = (p.get('perek') or '') + '|' + (p.get('perekName') or '')
        if key != last:
            perakim.append([(p.get('perek') or '').strip(), (p.get('perekName') or '').strip(), (p.get('daf') or '').strip()])
            last = key
    return {'dafim': dafim, 'perakim': perakim}


def main():
    import build_all
    st = json.load(io.open(os.path.join(SITE, 'status.json'), encoding='utf-8'))
    for m, rec in st['built'].items():
        slug = build_all.SLUG[m]
        p = os.path.join(SITE, slug + '.html')
        if os.path.exists(p):
            rec['meta'] = meta_of(p)
    json.dump(st, io.open(os.path.join(SITE, 'status.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    build_all.write_shas(st['built'])
    print('נתוני עזר ל-%d מסכתות' % len(st['built']))


if __name__ == '__main__':
    main()
