# -*- coding: utf-8 -*-
"""מדידה בלתי-תלויה של דיוק ההדגשה (צורת הדף): לכל קטע שמוצמד, האם המילים שבמלבנים שנשמרו הן באמת מילי הקטע.

  uv run --with pymupdf python tools/tzura/verify.py <slug> [--pdf נתיב]

שיטה: קוראים את קובץ הנתונים הציבורי (קואורדינטות בלבד), אוספים מה-PDF את מילות גופן הגמרא שמרכזן בתוך
המלבנים, ומשווים לשלד העיצורי של הקטע. הכיסוי = חלק מילות הקטע שנמצאות במלבנים. קטע ודאי ('ok')
שכיסויו נמוך מהסף נספר כנחיתה שגויה. בנוסף: סדר הקטעים בעמוד חייב להיות עולה (לפי y) כפי שבנוסח.
"""
import sys, os, json, collections, argparse
sys.path.insert(0, os.path.dirname(__file__))
from lib import *

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
THRESH = 0.7


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('slug')
    ap.add_argument('--pdf')
    a = ap.parse_args()
    src = json.load(open(os.path.join(ROOT, 'data', 'sources', a.slug + '.json'), encoding='utf8'))
    pdf = a.pdf or find_pdf(src)
    d = fitz.open(pdf)
    keys = list(src['pages'].keys())
    man = json.load(open(os.path.join(ROOT, 'data', 'tzura', 'manifest.json'), encoding='utf8'))[a.slug]
    n_ok = n_bad = n_int = n_int_bad = n_order = 0
    bad = []
    for s in man['sides']:
        pn = keys.index(s['k'])
        pg = d[pn]
        if tuple(pg.cropbox) != tuple(pg.mediabox):
            pg.set_cropbox(pg.mediabox)
        W, H = pg.rect.width, pg.rect.height
        data = json.load(open(os.path.join(ROOT, 'data', 'tzura', a.slug, s['f'] + '.json'), encoding='utf8'))
        words = page_words(pg)
        page = src['pages'][s['k']]
        own = dict(zip(page['refs'], page['gemara']))
        prev_y = -1
        for ref, seg in data['segs'].items():
            if ref not in own:
                continue
            want = ''.join(skel(w) for w in seg_words(own[ref]))
            if not want:
                continue
            hit = []
            for w in words:
                cx = (w[1] + w[3]) / 2 / W
                cy = (w[2] + w[4]) / 2 / H
                if any(l[0] <= cx <= l[2] and l[1] <= cy <= l[3] for l in seg['l']):
                    hit.append(w)
            hit.sort(key=lambda w: (round(w[2] / 4), -w[3]))
            got = ''.join(skel(w[0]) for w in hit)
            sm = difflib.SequenceMatcher(None, want, got, autojunk=False)
            cov = sum(b.size for b in sm.get_matching_blocks()) / len(want)
            if seg['c'] == 'ok':
                n_ok += 1
                if cov < THRESH:
                    n_bad += 1
                    bad.append((s['k'], ref, round(cov, 2)))
            elif seg['c'] == 'int':
                n_int += 1
                if cov < THRESH:
                    n_int_bad += 1
            y = seg['l'][0][1]
            if y + 0.01 < prev_y:
                n_order += 1
            prev_y = max(prev_y, y)
    print('%s: ודאיים %d, מהם כיסוי נמוך (נחיתה חשודה) %d | משוערים %d, כיסוי נמוך %d | חריגות סדר %d' % (
        a.slug, n_ok, n_bad, n_int, n_int_bad, n_order))
    for b in bad[:15]:
        print('  חשוד:', *b)


main()
