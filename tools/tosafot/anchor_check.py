# -*- coding: utf-8 -*-
"""anchor_check.py - בודק העוגנים של סימני התוס' (פרומפט 77, 22.11.2026). מכני, בלי מודל.

לכל מסכת שיש לה tosafot/<slug>/live-*.json: הטקסט של כל עמוד כפי שהאתר מציג אותו (הספר עם כל השכבה,
מאגר + שרת), ולכל סימן:
  1 / 2  - העוגן (t) נמצא בדיוק בעמוד שלו (המילה בטקסט / מקבילה).
  f      - העוגן המדויק אינו נמצא, אבל החיפוש המקורב (כמו findFuzzy בדפדפן, tools/tosafot_ui.js) מוצא
           התאמה אחת: הנוסח השתנה (סכם, עורך). עם --fix העוגן מתעדכן לנוסח החדש, כדי שלא יישבר שוב.
  3      - מוצמד לתוספות הקודם. עם --fix: חיפוש עוגן אמיתי מתוך הד"ה של התוספות עצמו (dh, ואחריו dhs)
           בטקסט העמוד, בהתאמה מקורבת. נמצא במקום אחד - מעוגן (כלל 1). אחרת נשאר כמו שהוא.
  m      - העוגן אינו נמצא כלל (הסימן נופל לסוף שורה). עם --fix: גם כאן חיפוש מן הד"ה.

    python tools/tosafot/anchor_check.py                    ספירה לכל המסכתות (טבלה + data/fold/anchor-check.json)
    python tools/tosafot/anchor_check.py --only shabbat --fix
    python tools/tosafot/anchor_check.py --live-dir DIR     קובצי /live שכבר נמשכו
--fix כותב רק ל-anchors-<פרק>.json ול-live-<פרק>.json (t, occ, rule, why), ורק התאמה יחידה.
"""
import os, sys, io, re, json, glob, argparse, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
sys.path.insert(0, os.path.join(ROOT, 'tosafot', 'handoff', 'kit'))
from gates import norm_idx, norm_ctx, find_occ

FIN = str.maketrans('ךםןףץ', 'כמנפצ')


def fzw(w):
    """כמו fzw בדפדפן: סופיות כרגילות, עד שתי אותיות שימוש בתחילת מילה, בלי ו/י באמצע."""
    w = w.translate(FIN)
    k = 0
    while k < 2 and len(w) > 3 and w[0] in 'שודהבלכמ':
        w = w[1:]; k += 1
    if len(w) > 3:
        w = w[0] + re.sub('[וי]', '', w[1:-1]) + w[-1]
    return w


def fuzzy(idx, ctx, min_words=2):
    """(הקטע כפי שהוא כתוב בעמוד, מספר המופע המדויק שלו) - רק בהתאמה יחידה. אחרת None."""
    words = [(m.group(0), m.start(), m.end()) for m in re.finditer(r'\S+', idx)]
    W = [fzw(w) for w, _, _ in words]
    cw = [fzw(w) for w in ctx.split()]
    tries = [cw]
    if len(cw) >= 3:
        tries += [cw[1:], cw[:-1]]
    for q in tries:
        if len(q) < min_words:
            continue
        hits = [i for i in range(len(W) - len(q) + 1) if W[i:i + len(q)] == q]
        if len(hits) == 1:
            i = hits[0]
            seg = idx[words[i][1]:words[i + len(q) - 1][2]]
            occ = find_occ(idx, seg)
            k = words[i][1]
            return seg, (occ.index(k) + 1) if k in occ else 1
    return None


def _plain(h):
    import html
    return html.unescape(re.sub(r'<[^>]+>', '', h or ''))


def page_texts(pages):
    """כמו pageNorm/unitsNorm במנוע ההדפסה (tools/print_engine.js, tosResolve): שורות כל היחידות של העמוד.
    first: daf -> העמוד הראשון שתוויתו daf (שם נבדק העוגן t). all: daf -> כל העמודים שתוויתם daf (שם נבדק הד"ה)."""
    first, allp = {}, {}
    for pg in pages:
        lines = []
        for u in pg.get('units') or []:
            for l in u.get('l') or []:
                lines.append(_plain(l[1] if isinstance(l, (list, tuple)) and len(l) > 1 else ''))
        t = norm_idx(lines)
        d = pg.get('daf')
        if d not in first:
            first[d] = t
        allp[d] = allp.get(d, '') + t
    return first, allp


def site_pages(slug, live_dir=None):
    sys.path.insert(0, os.path.join(ROOT, 'tools'))
    import mishna_check
    return mishna_check.pages_of(slug, True, live_dir)


def check(slug, pages, fix=False):
    T, TA = page_texts(pages)
    cnt = {'1': 0, '2': 0, '3': 0, 'f': 0, 'm': 0}
    fixed = {'f': 0, '3': 0, 'm': 0}
    samples = []
    for lp in sorted(glob.glob(os.path.join(ROOT, 'tosafot', slug, 'live-*.json'))):
        perek = re.search(r'live-(\d+)\.json$', lp).group(1)
        ap = os.path.join(ROOT, 'tosafot', slug, 'anchors-%s.json' % perek)
        L = json.load(io.open(lp, encoding='utf-8'))
        A = json.load(io.open(ap, encoding='utf-8')) if os.path.exists(ap) else {}
        chg = False
        for it in L.get('items') or []:
            rule = str(it.get('rule') or '1')
            page = it.get('page') or it.get('daf')
            idx = T.get(page) or T.get(it.get('daf')) or ''
            idxa = TA.get(page) or TA.get(it.get('daf')) or ''
            st = rule
            if rule in ('1', '2'):
                ctx = norm_ctx(it.get('t') or '')
                if not (ctx and find_occ(idx, ctx)):
                    st = 'm'
                    r = fuzzy(idx, ctx) if ctx else None
                    if r:
                        st = 'f'
                        if fix:
                            _set(it, A, r[0], r[1], rule, 'פרומפט 77: העוגן עודכן לנוסח שבדף (היה "%s")' % it.get('t'))
                            fixed['f'] += 1; chg = True
            if st in ('3', 'm') and fix:
                for dh in (it.get('dh'), it.get('dhs')):
                    c = norm_ctx(dh or '')
                    if len(c.split()) < 2:
                        continue
                    # הד"ה נבדק בעמוד הראשון (שם העוגן t תקף במנוע ההדפסה), ורק במקום יחיד
                    ex = find_occ(idx, c)
                    r = (c, 1) if len(ex) == 1 else (None if ex else fuzzy(idx, c))
                    if r:
                        _set(it, A, r[0], r[1], '1', 'פרומפט 77: עוגן מן הד"ה של התוספות עצמו')
                        fixed[st] += 1; chg = True
                        if len(samples) < 12:
                            samples.append('%s %s: %s' % (it.get('daf'), it.get('hn'), r[0]))
                        break
            cnt[st] += 1
        if chg:
            io.open(lp, 'w', encoding='utf-8', newline='\n').write(json.dumps(L, ensure_ascii=False, indent=1) + '\n')
            if A:
                io.open(ap, 'w', encoding='utf-8', newline='\n').write(json.dumps(A, ensure_ascii=False, indent=1) + '\n')
    return {'count': cnt, 'fixed': fixed, 'samples': samples}


def _set(it, A, t, occ, rule, why):
    it['t'] = t; it['occ'] = occ; it['rule'] = int(rule); it['why'] = why
    a = A.get(str(it.get('disp'))) if A else None
    if a is None and A:
        # anchors-<פרק>.json ממופה לפי מספר ההצגה בפרק (disp)
        a = A.get(str(it.get('n')))
    if isinstance(a, dict):
        a.update(t=t, occ=occ, rule=int(rule), why=why)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', default='')
    ap.add_argument('--live-dir', default='')
    ap.add_argument('--fix', action='store_true')
    ap.add_argument('--out', default='', help='קובץ הדוח (ברירת מחדל data/fold/anchor-check.json)')
    a = ap.parse_args()
    slugs = sorted(os.path.basename(os.path.dirname(p)) for p in glob.glob(os.path.join(ROOT, 'tosafot', '*', 'live-1.json')))
    if a.only:
        slugs = [s for s in slugs if s in a.only.split(',')]
    outp = a.out or os.path.join(ROOT, 'data', 'fold', 'anchor-check.json')
    res = json.load(io.open(outp, encoding='utf-8')) if os.path.exists(outp) else {'masechtot': {}}
    print('%-14s %6s %6s %6s %6s %6s | %s' % ('מסכת', '1', '2', '3', 'מקורב', 'm', 'תוקנו'))
    for s in slugs:
        try:
            r = check(s, site_pages(s, a.live_dir or None), a.fix)
        except Exception as e:
            print('%-14s שגיאה: %s' % (s, str(e)[:160])); continue
        c = r['count']
        prev = (res['masechtot'].get(s) or {}).get('count')
        res['masechtot'][s] = dict(r, when=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                                   prev=prev)
        print('%-14s %6d %6d %6d %6d %6d | %s' % (s, c['1'], c['2'], c['3'], c['f'], c['m'],
                                                 ' '.join('%s=%d' % kv for kv in r['fixed'].items()) if a.fix else ''))
        if prev and c['m'] > prev.get('m', 0):
            print('   אזהרה: מספר העוגנים שאבדו עלה מ-%d ל-%d' % (prev.get('m', 0), c['m']))
        sys.stdout.flush()
    io.open(outp, 'w', encoding='utf-8', newline='\n').write(json.dumps(res, ensure_ascii=False, indent=1) + '\n')


if __name__ == '__main__':
    main()
