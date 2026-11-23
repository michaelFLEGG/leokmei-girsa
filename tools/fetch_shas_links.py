# -*- coding: utf-8 -*-
"""fetch_shas_links.py - הורדת טבלת הקישורים הציבורית של ספריא בין דפי הבבלי לבין עצמם ולמשניות (פרומפט 82, 23.11.2026).

לכל מסכת שיש לה data/sources/<slug>.json: קישורי Talmud ו-Mishnah של כל סעיף, מן ה-API הציבורי של ספריא
(api/links, בלי טקסט). נשמר קובץ אחד קטן: data/shaslinks/sefaria-shas.json
  {slug: {"2a:3": [[ref, type], ...]}}
הקובץ הוא חומר גלם בלבד. הקישור הוודאי נקבע ב-shas_links.py, שמאמת כל קישור מול נוסח הגמרא שבאתר.
שימוש: python tools/fetch_shas_links.py [slug ...]"""
import io, json, os, re, sys, time, urllib.request, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.environ.get('SHAS_OUT') or os.path.join(ROOT, 'data', 'shaslinks', 'sefaria-shas.json')
SEG = re.compile(r'^(.+?) (\d+[ab]):(\d+)$')
RNG = re.compile(r'^(.+?) (\d+[ab]):(\d+)-(\d+[ab]:)?(\d+)$')   # טווח: רק למשנה שבגמרא (mishnah in talmud)


def daf_key(d):
    m = re.match(r'(\d+)([ab])', d)
    return (int(m.group(1)), m.group(2))


def get(url):
    for i in range(5):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                return json.loads(r.read().decode('utf-8'))
        except Exception as e:
            print('  ניסיון %d נכשל: %s' % (i + 1, e))
            time.sleep(5 * (i + 1))
    raise SystemExit('עצירה: ספריא לא ענתה על ' + url)


def fetch(slug):
    src = json.load(io.open(os.path.join(ROOT, 'data', 'sources', slug + '.json'), encoding='utf-8'))
    tr = src['tractate']
    amudim = sorted((v['daf'] for v in src['pages'].values() if v.get('daf')), key=daf_key)
    out = {}
    for i in range(0, len(amudim), 6):
        a, b = amudim[i], amudim[min(i + 5, len(amudim) - 1)]
        url = 'https://www.sefaria.org/api/links/%s?with_text=0' % urllib.parse.quote('%s.%s-%s' % (tr.replace(' ', '_'), a, b))
        for x in get(url):
            if x.get('category') not in ('Talmud', 'Mishnah'):
                continue
            m = SEG.match(x.get('anchorRef') or '')
            if m and m.group(1) == tr:
                k = '%s:%s' % (m.group(2), m.group(3))
            else:
                r = RNG.match(x.get('anchorRef') or '')
                if not r or r.group(1) != tr or x.get('type') != 'mishnah in talmud':
                    continue
                k = '%s:%s-%s%s' % (r.group(2), r.group(3), r.group(4) or '', r.group(5))
            row = [x.get('ref'), x.get('type') or '']
            lst = out.setdefault(k, [])
            if row not in lst:
                lst.append(row)
    return tr, out


def main(slugs):
    data = json.load(io.open(OUT, encoding='utf-8')) if os.path.exists(OUT) else {}
    if not slugs:
        slugs = sorted(f[:-5] for f in os.listdir(os.path.join(ROOT, 'data', 'sources')) if f.endswith('.json'))
    for s in slugs:
        if s in data and '--again' not in sys.argv:
            continue
        tr, out = fetch(s)
        data[s] = out
        print('%s (%s): %d סעיפים עם קישורים, %d קישורים' % (s, tr, len(out), sum(len(v) for v in out.values())))
        with io.open(OUT, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(data, f, ensure_ascii=False, separators=(',', ':'), sort_keys=True)


if __name__ == '__main__':
    main([a for a in sys.argv[1:] if not a.startswith('--')])
