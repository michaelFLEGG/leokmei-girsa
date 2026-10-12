# -*- coding: utf-8 -*-
"""verify_vs_daf.py - מקור שני לספירת התוספות: טקסט צורת הדף (ה-PDF המקומי הפרטי) מול ספריא.

לכל צד: (א) כל תוספות שנספר נמצא בטקסט המודפס של הצד (תחילת הדיבור המתחיל); (ב) כיסוי: כל מילה בגוף הדף
(גופן רש"י/תוספות) נבדקת מול טקסט רש"י ותוספות של ספריא (הצד והשכנים). רצף ארוך של מילים שאינן מכוסות
הוא חשד לתוספות חסר בספירה (או לרש"י שחסר במקור). הרש"י נמשך מספריא לצורך הכיסוי בלבד ואינו נשמר במאגר.
הפלט: דוח markdown, ו-JSON של התוצאות. לא נכתב דבר לאתר.

    uv run --with pymupdf python tools/tosafot/verify_vs_daf.py sukkah 1 2a 6b <קובץ-דוח>
"""
import os, sys, re, json, io, glob
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'tzura'))
import fitz
from lib import skel, page_words, find_pdf
from fetch_tosafot import dafim
from fetch_sources import get
from sefaria_map import SEFARIA
ROOT = os.path.dirname(os.path.dirname(HERE))
TAGS = re.compile(r'<[^>]+>')


def sk_words(t):
    t = TAGS.sub(' ', t or '')
    t = t.replace('־', ' ').replace('&nbsp;', ' ').replace('&thinsp;', ' ')
    return [s for s in (skel(w) for w in t.split()) if s]


def rashi_words(book, d):
    j = get('https://www.sefaria.org/api/v3/texts/Rashi_on_%s.%s?version=hebrew' % (book, d))
    if j is None or not j.get('versions'):
        return None
    out = []
    def walk(x):
        if isinstance(x, str):
            out.extend(sk_words(x))
        elif isinstance(x, list):
            for y in x:
                walk(y)
    walk(j['versions'][0]['text'])
    return out


def main():
    slug, perek, a, b = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
    rep = sys.argv[5] if len(sys.argv) > 5 else None
    he = [k for k, v in __import__('build_all').SLUG.items() if v == slug][0]
    book = SEFARIA[he].replace(' ', '_')
    src = json.load(io.open(os.path.join(ROOT, 'data', 'sources', slug + '.json'), encoding='utf-8'))
    pdf = find_pdf(src)
    if not pdf:
        raise SystemExit('עצירה: אין קובץ צורת הדף למסכת')
    doc = fitz.open(pdf)
    allp = dafim('2a', b)
    cnt = json.load(io.open(os.path.join(ROOT, 'tosafot', slug, 'count-%d.json' % perek), encoding='utf-8'))['items']
    raw = json.load(io.open(os.path.join(ROOT, 'tosafot', 'raw', slug + '.json'), encoding='utf-8'))['items']
    tos_by, ras_by = {}, {}
    for r in raw:
        tos_by.setdefault(r['daf'], []).extend(sk_words(r['html']))
    for d in allp:
        ras_by[d] = rashi_words(book, d)
        if ras_by[d] is None:
            raise SystemExit('עצירה: אין רש"י בספריא לדף ' + d)
    lines = ['# אימות מול צורת הדף: %s פרק %d, %s עד %s' % (slug, perek, a, b), '']
    summary = {}
    for d in dafim(a, b):
        i = allp.index(d)
        pg = doc[i]
        if tuple(pg.cropbox) != tuple(pg.mediabox):
            pg.set_cropbox(pg.mediabox)
        ws = page_words(pg)
        body = [w for w in ws if ((('Rashi' in w[6] or 'VTY' in w[6]) and w[5] >= 9.5) or ('Ivri' in w[6] and 'Bold' in w[6] and w[5] >= 8))]
        pw = [(skel(w[0]), w) for w in body if skel(w[0])]
        page_txt = ' '.join(s for s, _ in pw)
        nb = [x for x in allp if abs(allp.index(x) - i) <= 1]
        srcw = []
        for x in nb:
            srcw += ras_by[x] + tos_by.get(x, [])
        bg = set(zip(srcw, srcw[1:]))
        cov = []
        for k, (s, w) in enumerate(pw):
            c = (k > 0 and (pw[k - 1][0], s) in bg) or (k + 1 < len(pw) and (s, pw[k + 1][0]) in bg)
            cov.append(c)
        # רצפים לא מכוסים
        gaps, cur = [], []
        for k, c in enumerate(cov):
            if not c:
                cur.append(k)
            else:
                if len(cur) >= 10:
                    gaps.append(cur)
                cur = []
        if len(cur) >= 10:
            gaps.append(cur)
        mine = [r for r in cnt if r['daf'] == d]
        found, notfound = 0, []
        for r in mine:
            dw = [s for s in (skel(x) for x in r['dh'].split()) if s]
            ok = False
            for L in (3, 2, 1):
                if len(dw) >= L and ' '.join(dw[:L]) in page_txt:
                    ok = True
                    break
            if ok:
                found += 1
            else:
                notfound.append(r)
        tw = tos_by.get(d, [])
        mytxt = sum(len(sk_words(r['text'])) for r in mine)
        covp = 100.0 * sum(cov) / max(1, len(cov))
        lines.append('## %s: ספירה %d | נמצא בדף המודפס %d | כיסוי גוף הדף %.1f%% | רצפים לא מכוסים (10+ מילים): %d' % (d, len(mine), found, covp, len(gaps)))
        for r in notfound:
            lines.append('- לא נמצאה תחילת הדיבור בדף: %d (%s)' % (r['n'], r['dh']))
        for g in gaps:
            x0, y0 = pw[g[0]][1][1], pw[g[0]][1][2]
            lines.append('- רצף לא מכוסה של %d מילים, x=%d y=%d: %s' % (len(g), x0, y0, ' '.join(pw[k][1][0] for k in g[:14])))
        summary[d] = {'count': len(mine), 'found': found, 'notfound': [r['n'] for r in notfound], 'coverage': round(covp, 1), 'gaps': len(gaps)}
        print(d, summary[d], file=sys.stderr)
    if rep:
        io.open(rep, 'w', encoding='utf-8').write('\n'.join(lines))
        json.dump(summary, io.open(rep + '.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
