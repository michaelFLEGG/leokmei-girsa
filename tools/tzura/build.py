# -*- coding: utf-8 -*-
"""צורת הדף: בנייה למסכת אחת.

  uv run --with pymupdf --with pillow python tools/tzura/build.py <slug> [--pdf נתיב] [--only 2a,2b] [--noimg]

קלט:  התיקייה הקבועה  Desktop\\שיננא לHTML\\צורת הדף\\<מסכת>\\צורת הדף NN-<מסכת>.pdf
      ו-data/sources/<slug>.json (נוסח הגמרא וה-ref של כל קטע)
פלט ציבורי (קואורדינטות בלבד, בלי טקסט):  data/tzura/<slug>/<f>.json  ו-data/tzura/manifest.json (build_all מעתיק ל-site/tzura)
פלט פרטי (לא במאגר):  _work/tzura/assets/<slug>/<f>.v.webp (תצוגה) ו-<f>.z.webp (זום)

עקרון: שכבת הטקסט שב-PDF אינה מוגשת לעולם. היא משמשת כאן בלבד ליישור קטעי ספריא אל השורות בעמוד.
"""
import sys, os, re, json, glob, io, difflib, collections, argparse
sys.path.insert(0, os.path.dirname(__file__))
from lib import *
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
HOME = r'C:\Users\Owner\Desktop\שיננא לHTML\צורת הדף'


def find_pdf(slug, src):
    heb = src.get('masechet') or ''
    for d in glob.glob(os.path.join(HOME, '*')):
        if os.path.isdir(d) and os.path.basename(d).strip() == heb.strip():
            fs = sorted(glob.glob(os.path.join(d, 'צורת הדף*.pdf')))
            if fs:
                return fs[0]
    return None


def head_label(words):
    top = [w for w in words if w[2] < 12 and w[5] > 20]
    for p in top:
        if p[0] in ('.', ':'):
            best = None
            for w in top:
                t = NIK.sub('', w[0])
                if w is p or not re.fullmatch(r'[א-ת]{1,3}', t) or t == 'פרק':
                    continue
                gap = min(abs(w[1] - p[3]), abs(p[1] - w[3]))
                if gap < 6 and (best is None or gap < best[0]):
                    best = (gap, t)
            if best:
                return best[1] + p[0]
    return None


def lines_of(gw, tol=3.0):
    gw = sorted(gw, key=lambda w: (w[2] + w[4]) / 2)
    L = []
    for w in gw:
        cy = (w[2] + w[4]) / 2
        if L and abs(cy - L[-1]['cy']) <= tol + 0.35 * (w[4] - w[2]):
            L[-1]['w'].append(w)
            n = len(L[-1]['w'])
            L[-1]['cy'] = (L[-1]['cy'] * (n - 1) + cy) / n
        else:
            L.append({'cy': cy, 'w': [w]})
    for l in L:
        l['w'].sort(key=lambda w: -w[3])
    return L


def fid(daf):  # 2a -> 002a
    m = re.fullmatch(r'(\d+)([ab])', daf)
    return '%03d%s' % (int(m.group(1)), m.group(2))


def poster(im, levels=4):
    step = 256 // levels
    return im.point(lambda v: min(255, (v // step) * step + step // 2) if v < 250 else 255)


def save_webp(page, dpi, path):
    pix = page.get_pixmap(dpi=dpi, colorspace=fitz.csGRAY)
    im = poster(Image.frombytes('L', (pix.width, pix.height), pix.samples))
    b = io.BytesIO()
    im.save(b, 'WEBP', lossless=True, method=6)
    open(path, 'wb').write(b.getvalue())
    return len(b.getvalue())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('slug')
    ap.add_argument('--pdf')
    ap.add_argument('--only')
    ap.add_argument('--noimg', action='store_true')
    a = ap.parse_args()
    src = json.load(open(os.path.join(ROOT, 'data', 'sources', a.slug + '.json'), encoding='utf8'))
    pdf = a.pdf or find_pdf(a.slug, src)
    if not pdf:
        sys.exit('לא נמצא קובץ צורת הדף למסכת ' + a.slug)
    d = fitz.open(pdf)
    keys = list(src['pages'].keys())
    pub = os.path.join(ROOT, 'data', 'tzura', a.slug)
    os.makedirs(pub, exist_ok=True)
    priv = os.path.join(ROOT, '_work', 'tzura', 'assets', a.slug)
    os.makedirs(priv, exist_ok=True)
    only = set(a.only.split(',')) if a.only else None
    nside = min(len(d), len(keys))
    sides = []
    report = {}
    problems = []
    for pn in range(nside):
        exp = keys[pn]
        pg = src['pages'][exp]
        daf = pg['daf']
        f = fid(daf)
        if only and daf not in only:
            continue
        page = d[pn]
        W, H = page.rect.width, page.rect.height
        words = page_words(page)
        lab = head_label(words)
        if lab != exp:  # אימות נגד סימן הדף שבעמוד: לא סומכים על ספירה סדרתית בלבד
            problems.append('סימן הדף בעמוד %d הוא %r והצפוי %r' % (pn + 1, lab, exp))
            continue
        Sset = set(skel(w) for g in pg['gemara'] for w in seg_words(g))
        by = collections.defaultdict(lambda: [0, 0])
        for w in words:
            k = skel(w[0])
            if k:
                z = round(w[5], 1)
                by[z][0] += 1
                by[z][1] += (k in Sset)
        cand = [(m, z) for z, (n, m) in by.items() if n >= 25 and m / n > 0.7]
        if not cand:
            problems.append('לא זוהה גופן הגמרא בצד ' + exp)
            continue
        zg = max(cand)[1]
        gw = [w for w in words if abs(w[5] - zg) < 0.16 and skel(w[0])]
        Ls = lines_of(gw)
        seq = [(skel(w[0]), li, wi) for li, l in enumerate(Ls) for wi, w in enumerate(l['w'])]
        refs_here = pg['refs']
        S = []
        if pn > 0 and src['pages'][keys[pn - 1]]['gemara']:
            pp = src['pages'][keys[pn - 1]]
            n = len(pp['gemara']) - 1
            for w in seg_words(pp['gemara'][n]):
                S.append((skel(w), pp['refs'][n]))
        for i, g in enumerate(pg['gemara']):
            for w in seg_words(g):
                S.append((skel(w), refs_here[i]))
        if pn + 1 < len(keys) and src['pages'][keys[pn + 1]]['gemara']:
            nn = src['pages'][keys[pn + 1]]
            for w in seg_words(nn['gemara'][0]):
                S.append((skel(w), nn['refs'][0]))
        A = []
        Am = []
        for k, m in S:
            if k:
                A.extend(k)
                Am.extend([m] * len(k))
        B = []
        Bw = []
        for wi, (k, li, wj) in enumerate(seq):
            B.extend(k)
            Bw.extend([wi] * len(k))
        sm = difflib.SequenceMatcher(None, A, B, autojunk=False)
        pos = {}
        for a_, b_, n_ in sm.get_matching_blocks():
            for t in range(n_):
                pos[a_ + t] = b_ + t
        segr = {}
        for ai, m in enumerate(Am):
            if ai in pos:
                wi = Bw[pos[ai]]
                r = segr.setdefault(m, [wi, wi, 0])
                r[0] = min(r[0], wi)
                r[1] = max(r[1], wi)
                r[2] += 1
        tot = collections.Counter(Am)
        order = []  # הקטעים כסדרם בנוסח
        for m in Am:
            if not order or order[-1] != m:
                order.append(m)
        rec = {}
        ownrefs = set(refs_here)
        for m in order:
            if m in segr:
                a0, b0, c = segr[m]
                span = sum(len(seq[t][0]) for t in range(a0, b0 + 1))
                dens = c / max(1, span)
                edge = m not in ownrefs or m == refs_here[0] or m == refs_here[-1]
                cv = c / tot[m]
                ok = dens >= 0.7 and cv >= (0.3 if edge else 0.6)
                rec[m] = {'a': a0, 'b': b0, 'c': 'ok' if ok else 'weak'}
        # קטע חסר או חלש בין שני שכנים מאומתים: טווח השורות שביניהם (אינו יכול לצאת מהם)
        for idx, m in enumerate(order):
            if m in rec and rec[m]['c'] == 'ok':
                continue
            if m not in ownrefs:
                continue
            lo = next((rec[order[j]]['b'] for j in range(idx - 1, -1, -1) if order[j] in rec and rec[order[j]]['c'] == 'ok'), None)
            hi = next((rec[order[j]]['a'] for j in range(idx + 1, len(order)) if order[j] in rec and rec[order[j]]['c'] == 'ok'), None)
            if lo is not None and hi is not None and 1 < hi - lo <= 120:
                rec[m] = {'a': lo + 1, 'b': hi - 1, 'c': 'int'}
            else:
                rec.pop(m, None)
        out = {}
        for m, r in rec.items():
            if m not in ownrefs and r['c'] != 'ok':
                continue
            lines = {}
            for t in range(r['a'], r['b'] + 1):
                _, li, wi = seq[t]
                w = Ls[li]['w'][wi]
                e = lines.setdefault(li, [w[1], w[2], w[3], w[4]])
                e[0] = min(e[0], w[1]); e[1] = min(e[1], w[2]); e[2] = max(e[2], w[3]); e[3] = max(e[3], w[4])
            out[m] = {'c': r['c'], 'l': [[round(v / s, 4) for v, s in zip(lines[li], (W, H, W, H))] for li in sorted(lines)]}
        colx0 = min(w[1] for w in gw); colx1 = max(w[3] for w in gw)
        coly0 = min(w[2] for w in gw); coly1 = max(w[4] for w in gw)
        data = {'side': exp, 'daf': daf, 'ar': round(W / H, 5),
                'col': [round(colx0 / W, 4), round(coly0 / H, 4), round(colx1 / W, 4), round(coly1 / H, 4)], 'segs': out}
        json.dump(data, open(os.path.join(pub, f + '.json'), 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
        report[daf] = {'label': exp, 'own': len(refs_here),
                       'ok': sum(1 for r in refs_here if r in out and out[r]['c'] == 'ok'),
                       'int': sum(1 for r in refs_here if r in out and out[r]['c'] == 'int'),
                       'weak': sum(1 for r in refs_here if r in out and out[r]['c'] == 'weak'),
                       'none': [i for i, r in enumerate(refs_here) if r not in out]}
        if not a.noimg:
            report[daf]['kb_v'] = save_webp(page, 150, os.path.join(priv, f + '.v.webp')) // 1024
            report[daf]['kb_z'] = save_webp(page, 300, os.path.join(priv, f + '.z.webp')) // 1024
        sides.append({'k': exp, 'f': f, 'daf': daf})
    # מניפסט: מסכת שיש בו = הכפתור מופיע. מסכת בלי צורת הדף אינה מופיעה בו כלל.
    mp = os.path.join(ROOT, 'data', 'tzura', 'manifest.json')
    man = json.load(open(mp, encoding='utf8')) if os.path.exists(mp) else {}
    if not only:
        man[a.slug] = {'name': src.get('masechet', ''), 'sides': sides, 'total_sides': len(keys), 'have_sides': len(sides)}
        json.dump(man, open(mp, 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
    json.dump({'problems': problems, 'sides': report},
              open(os.path.join(ROOT, '_work', 'tzura', 'report-%s.json' % a.slug), 'w', encoding='utf8'), ensure_ascii=False, indent=1)
    own = sum(v['own'] for v in report.values())
    print('צדדים %d מתוך %d' % (len(sides), len(keys)), '| קטעים', own,
          '| מאומתים', sum(v['ok'] for v in report.values()),
          '| משוערים בין שכנים', sum(v['int'] for v in report.values()),
          '| חלשים', sum(v['weak'] for v in report.values()),
          '| בלי מיקום', sum(len(v['none']) for v in report.values()))
    if problems:
        print('בעיות:', problems[:5])
    if not a.noimg and report:
        kb = [v['kb_v'] for v in report.values()]
        print('משקל צד בתצוגה: ממוצע %d KB, מקסימום %d KB' % (sum(kb) // len(kb), max(kb)))


main()
