# -*- coding: utf-8 -*-
"""fetch_mishna.py - מוריד מספריא את נוסח המשנה לכל מסכת (פרק -> משניות).

המקור: ספריא, "Mishnah <מסכת>", Torat Emet 357 (עברית). משמש רק למספור
קטעי המשנה שבגמרא ("משנה ג" בפרק ב): הנוסח עצמו אינו מוצג באתר.

    uv run python tools/fetch_mishna.py [slug ...]
"""
import os, sys, json, io, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_sources import get, flat, clean
from sefaria_map import SEFARIA
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'mishna')
API = 'https://www.sefaria.org/api/v3/texts/%s?version=hebrew'


def run(masechet, slug, log=print):
    book = 'Mishnah ' + SEFARIA[masechet]
    q = book.replace(' ', '_')
    chapters = []
    for c in range(1, 40):
        d = get(API % ('%s.%d' % (q, c)))
        vs = (d or {}).get('versions') or []
        if not vs or not vs[0].get('text'):
            break
        txt = vs[0]['text']
        chapters.append([clean(x) for x in (txt if isinstance(txt, list) else [txt])])
        time.sleep(0.25)
    log('%s: %d פרקים, %d משניות' % (masechet, len(chapters), sum(len(c) for c in chapters)))
    os.makedirs(OUT, exist_ok=True)
    io.open(os.path.join(OUT, slug + '.json'), 'w', encoding='utf-8').write(
        json.dumps({'masechet': masechet, 'source': 'ספריא, Mishnah, Torat Emet 357', 'chapters': chapters},
                   ensure_ascii=False))
    return chapters


if __name__ == '__main__':
    from build_all import SLUG
    want = set(sys.argv[1:])
    for m, slug in SLUG.items():
        if want and slug not in want:
            continue
        if os.path.exists(os.path.join(ROOT, 'data', 'sources', slug + '.json')):
            run(m, slug)
