# -*- coding: utf-8 -*-
"""title_suggest_prep.py - הכנת חומר להצעות כותרת (12.10.2026, מנת "הצע כותרת").

קורא את דפי המסכתות שבאתר ומפיק לכל מסכת רשימת מקומות שבהם המנהל עשוי לבקש כותרת:
  א. עיטור (***) שהוא יחידה משלו;
  ב. פסקת גמרא ראשונה אחרי משנה, כשאין לפניה כותרת (פתיחת סוגיה בלי כותרת).
לכל מקום נשמרים: מפתח (נוסח הפסקה הראשונה שאחריו, מנורמל), ההקשר (הקטע שאחרי המקום עד הכותרת
או החציצה הבאה), ודוגמאות מתוך כותרות הנושא הקיימות באותה מסכת (ללמידת הסגנון).

מפתח זהה בדיוק למה שמחשב הדפדפן (suggest_title.js: tsKey). שימוש:
    uv run python tools/title_suggest_prep.py --site C:/Users/Owner/leokmei-girsa/site --out _work/titlesug
"""
import os, re, sys, json, html, argparse, io

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pagedata

HEB = re.compile(r'[^\u05d0-\u05ea ]')
BOUNDARY = ('nose', 'dh', 'hatz', 'perek-start', 'perek-num', 'perek-name', 'perek-range', 'hadran')


def plain(h):
    return html.unescape(re.sub(r'<[^>]+>', '', h or ''))


def key_of(t):
    """אותיות עבריות ורווחים בלבד, רווחים מכווצים, 40 תווים ראשונים. זהה ל-tsKey בדפדפן."""
    s = HEB.sub(' ', plain(t))
    s = re.sub(r'\s+', ' ', s).strip()
    return s[:40]


def paras(u):
    k = u['k']
    if k in ('u', 'm'):
        return [(x[0], plain(x[1])) for x in u.get('l', []) if x[0] != 'hatz']
    return [('', plain(u.get('a') or ''))]


def extract(slug, d, ctx_chars=900):
    units = []
    for p in d['pages']:
        for u in p['units']:
            units.append((p.get('daf'), u))
    ex = []
    for daf, u in units:
        if u['k'] == 'nose':
            t = re.sub(r'\s+', ' ', plain(u.get('a'))).strip()
            if 2 <= len(t.split()) <= 8:
                ex.append(t)
    items = []
    for i, (daf, u) in enumerate(units):
        cand = None
        if u['k'] == 'hatz':
            cand = ('deco', i + 1)
        elif u['k'] == 'u' and i > 0 and units[i - 1][1]['k'] == 'm':
            cand = ('open', i)
        if not cand:
            continue
        kind, start = cand
        text, first = [], None
        j = start
        while j < len(units) and len(' '.join(text)) < ctx_chars:
            uk = units[j][1]
            if uk['k'] in BOUNDARY and j > start:
                break
            if uk['k'] == 'hatz' and j == start:
                j += 1
                continue
            for _, t in paras(uk):
                t = re.sub(r'\s+', ' ', t).strip()
                if not t:
                    continue
                if first is None:
                    first = t
                text.append(t)
            j += 1
        if first is None:
            continue
        items.append({'key': key_of(first), 'kind': kind, 'daf': daf, 'ctx': ' '.join(text)[:ctx_chars]})
    return items, ex


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--site', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--only', action='append', default=[])
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    st = json.load(io.open(os.path.join(a.site, 'status.json'), encoding='utf-8'))
    total = 0
    sys.path.insert(0, HERE)
    import build_all
    for m, rec in st['built'].items():
        slug = build_all.SLUG[m]
        if a.only and slug not in a.only:
            continue
        path = os.path.join(a.site, slug + '.html')
        if not os.path.exists(path):
            print('דילוג, אין דף:', slug)
            continue
        h = pagedata.read_html(path)
        i = h.index('const DATA=') + len('const DATA=')
        d = json.JSONDecoder().raw_decode(h[i:])[0]
        items, ex = extract(slug, d)
        # מפתח כפול: הראשון נשאר (ההקשר זהה בדרך כלל); נרשם בדוח
        seen, uniq, dup = set(), [], 0
        for it in items:
            if it['key'] in seen:
                dup += 1
                continue
            seen.add(it['key'])
            uniq.append(it)
        io.open(os.path.join(a.out, slug + '-items.json'), 'w', encoding='utf-8').write(
            json.dumps({'slug': slug, 'masechet': m, 'examples': ex[:40], 'items': uniq}, ensure_ascii=False, indent=1))
        total += len(uniq)
        print('%s: %d מקומות (%d עיטורים, %d פתיחות), %d דוגמאות, %d מפתחות כפולים' % (
            slug, len(uniq), sum(1 for x in uniq if x['kind'] == 'deco'), sum(1 for x in uniq if x['kind'] == 'open'), len(ex), dup))
    print('סה"כ', total)


if __name__ == '__main__':
    main()
