# -*- coding: utf-8 -*-
"""push.py - מעלה את חבילות חברותא של מסכת לנקודת הקליטה (מנהל בלבד), במקטעים של כ-6 דפים.

    uv run python tools/hv/push.py <slug> [--from ל.] [--to מ:]

הנתונים נכתבים ל-KV של ה-Worker בלבד (hv:<מסכת>:<מקטע>), מוגשים רק עם מפתח מנהל, ואינם נכנסים לקובצי האתר ולא לריפו הציבורי.
מכל חבילה נשלחים רק מה שהמסך המפוצל צריך: שורות חברותא, ההערות, וההתאמה לפסקאות (בלי טקסט הפסקאות שלנו).
"""
import os, sys, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hv_common as H
from hv_common import C
import _api

CHUNK = 12          # מפתח דף = 2 * מספר הדף + עמוד, כלומר 6 דפים (12 עמודים) למקטע


def chunk_of(label):
    return C.daf_key(label) // CHUNK


def slim(pk):
    return {'daf': pk['daf'], 'url': pk.get('source_url'), 'raw': bool(pk.get('raw')),
            'segs': [{'k': s['k'], 'g': s['gemara'], 'e': s['explain'], 'p': s['para'], 's': s['sim']} for s in pk['segs']],
            'notes': [{'n': n['n'], 'src': n['sources'], 't': n['text']} for n in pk['notes']]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('slug')
    ap.add_argument('--from', dest='lo')
    ap.add_argument('--to', dest='hi')
    a = ap.parse_args()
    d = os.path.join(H.CHAV, 'packs', a.slug)
    k0 = C.daf_key(a.lo) if a.lo else None
    k1 = C.daf_key(a.hi) if a.hi else None
    chunks = {}
    for fn in sorted(os.listdir(d)):
        pk = H.jload(os.path.join(d, fn))
        k = C.daf_key(pk['daf'])
        if (k0 is not None and k < k0) or (k1 is not None and k > k1):
            continue
        chunks.setdefault(chunk_of(pk['daf']), {})[pk['daf']] = slim(pk)
    tot = 0
    for c, pages in sorted(chunks.items()):
        r = _api.call('/hv/put', 'POST', {'slug': a.slug, 'c': c, 'pages': pages})
        tot += r.get('bytes', 0)
        print('מקטע %d: %d עמודים, %d בתים' % (c, len(pages), r.get('bytes', 0)))
    print('הועלו %d מקטעים, %.1f מגה' % (len(chunks), tot / 1e6))


if __name__ == '__main__':
    main()
