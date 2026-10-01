# -*- coding: utf-8 -*-
"""fetch_perush.py - מוסיף לקובצי הגמרא שב-data/sources את "פירוש הגמרא".

המקור: ספריא, "Steinsaltz on <מסכת>" במהדורת William Davidson (עברית),
מקטע מול מקטע של הגמרא המנוקדת. הרישיון: CC-BY-NC, כמו הגמרא עצמה.
באתר הפירוש נקרא "פירוש הגמרא" בלבד; השם המקורי מופיע פעם אחת בעמוד
"מקורות", כחובת הייחוס.

דף שמספר מקטעי הפירוש בו שונה ממספר מקטעי הגמרא אינו נשמר, והוא נאמר
בקול: התאמה בניחוש היתה מצמידה פירוש למקטע זר.

    uv run python tools/fetch_perush.py --all
    uv run python tools/fetch_perush.py סוכה
"""
import os, sys, json, io, time, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_sources import get, flat, clean, OUT
from sefaria_map import SEFARIA

API = 'https://www.sefaria.org/api/v3/texts/%s?version=hebrew'
CHUNK = 10
ATTRIB2 = 'פירוש הגמרא: ספריא, William Davidson, ברישיון CC BY-NC'


def run(masechet, slug, log=print):
    p = os.path.join(OUT, slug + '.json')
    if not os.path.exists(p):
        log('אין קובץ גמרא ל%s - דילוג' % masechet)
        return None
    data = json.load(io.open(p, encoding='utf-8'))
    book = 'Steinsaltz on ' + SEFARIA[masechet]
    q = book.replace(' ', '_')
    pages = data['pages']
    items = [(k, v['daf']) for k, v in pages.items()]
    got = bad = nodata = 0
    for i in range(0, len(items), CHUNK):
        part = items[i:i + CHUNK]
        rng = '%s.%s-%s' % (q, part[0][1], part[-1][1]) if len(part) > 1 else '%s.%s' % (q, part[0][1])
        d = get(API % rng)
        if d is None:
            nodata += len(part)
            continue
        vs = d.get('versions') or []
        if not vs:
            nodata += len(part)
            continue
        txt = vs[0].get('text')
        blocks = txt if (len(part) > 1 and isinstance(txt, list) and txt and isinstance(txt[0], list)) else [txt]
        if len(blocks) != len(part):
            # ספריא החזירה מנה שונה: כל דף נמשך לבדו, כדי לא להצמיד בניחוש
            blocks = []
            for _, daf in part:
                dd = get(API % ('%s.%s' % (q, daf)))
                vv = (dd or {}).get('versions') or []
                blocks.append(vv[0].get('text') if vv else None)
        for (k, daf), blk in zip(part, blocks):
            segs = [clean(x) for x in flat(blk, [])] if blk is not None else None
            if segs is None or not any(segs):
                nodata += 1
                continue
            if len(segs) != len(pages[k]['gemara']):
                bad += 1
                log('   %s %s: %d מקטעי פירוש מול %d של גמרא - לא נשמר' % (masechet, k, len(segs), len(pages[k]['gemara'])))
                continue
            pages[k]['perush'] = segs
            got += 1
        time.sleep(0.3)
    data['perush_source'] = 'Sefaria, ' + book + ', William Davidson Edition - Hebrew'
    data['perush_license'] = 'CC-BY-NC'
    data['attribution'] = data.get('attribution', '').split(' | ')[0] + ' | ' + ATTRIB2
    io.open(p, 'w', encoding='utf-8').write(json.dumps(data, ensure_ascii=False))
    log('%s: פירוש ל-%d דפים, %d ללא התאמה, %d ללא פירוש; %.1f מ"ב' % (slug, got, bad, nodata, os.path.getsize(p) / 1e6))
    return got, bad, nodata


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('masechet', nargs='*')
    ap.add_argument('--all', action='store_true')
    a = ap.parse_args()
    from build_all import SLUG
    names = list(SLUG) if a.all else a.masechet
    tot = [0, 0, 0]
    for m in names:
        if m not in SLUG or m not in SEFARIA:
            print('לא מוכרת:', m)
            continue
        try:
            r = run(m, SLUG[m])
        except Exception as e:
            print('נכשל', m, repr(e))
            continue
        if r:
            tot = [x + y for x, y in zip(tot, r)]
    print('סך הכל: %d דפים עם פירוש, %d ללא התאמה, %d ללא פירוש' % tuple(tot))


if __name__ == '__main__':
    main()
