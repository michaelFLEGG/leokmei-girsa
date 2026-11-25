# -*- coding: utf-8 -*-
"""tos_anchor_lib.py - כלים משותפים לעיגון סימני התוס' (פרומפט 96, 25.11.2026). מכני, בלי מודל.

אותו נרמול ואותו שיוך כמו בדפדפן (tools/print_engine.js: unitsNorm, hitUnit, tosResolve), כדי שעוגן שנקבע כאן
יימצא בדיוק באותה יחידה באתר ובהדפסה. משמש את reanchor.py (תיקון) ואת tools/integrity_check.py (שלוש בדיקות קבועות).
"""
import os, re, sys, html

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, 'tools'))

NIK = re.compile('[֑-ׇ]')
FIN = str.maketrans('ךםןףץ', 'כמנפצ')
# יחידות שאינן טקסט גמרא (כותרות, טווח, הדרן): לא מעגנים בהן סימן
NOTXT = {'perek-range', 'perek-start', 'perek-num', 'perek-name', 'hadran', 'hatz', 'nose', 'dh'}
HEB = {'א': 1, 'ב': 2, 'ג': 3, 'ד': 4, 'ה': 5, 'ו': 6, 'ז': 7, 'ח': 8, 'ט': 9, 'י': 10, 'כ': 20, 'ל': 30, 'מ': 40,
       'נ': 50, 'ס': 60, 'ע': 70, 'פ': 80, 'צ': 90, 'ק': 100, 'ר': 200, 'ש': 300, 'ת': 400}


def plain(h):
    h = re.sub(r'<[^>]+>', '', h or '')
    return html.unescape(h) if '&' in h else h


def norm_add(s, t):
    """normAdd של הדפדפן: אותיות בלבד, רווח/מקף כרווח יחיד, רווח בסוף כל שורה."""
    for c in NIK.sub('', t):
        if 'א' <= c <= 'ת':
            s += c
        elif c.isspace() or c in '-־':
            if s and s[-1] != ' ':
                s += ' '
    if s and s[-1] != ' ':
        s += ' '
    return s


def norm_ctx(t):
    return norm_add('', plain(t)).strip()


def line_text(l):
    return l[1] if isinstance(l, (list, tuple)) and len(l) > 1 else (l if isinstance(l, str) else '')


def units_norm(units):
    """{s, rg:[(id, a, b)]} - כמו unitsNorm."""
    s, rg = '', []
    for u in units:
        a = len(s)
        for l in u.get('l') or []:
            s = norm_add(s, plain(line_text(l)))
        rg.append((u['id'], a, len(s)))
    return s, rg


def occs(s, ctx):
    out, frm = [], 0
    if not ctx:
        return out
    while True:
        k = s.find(ctx, frm)
        if k < 0:
            return out
        if (k == 0 or s[k - 1] == ' ') and (k + len(ctx) >= len(s) or s[k + len(ctx)] == ' '):
            out.append(k)
        frm = k + 1


def hit_unit(N, ctx, occ):
    """כמו hitUnit: לאיזו יחידה שייך המופע ה-occ, ומספרו בתוך היחידה."""
    s, rg = N
    oc = occs(s, ctx)
    if occ > len(oc):
        return None
    st = oc[occ - 1]
    en = st + len(ctx) - 1
    g = next((r for r in rg if r[1] <= en < r[2]), None)
    if not g:
        return None
    k = sum(1 for o in oc if g[1] <= o <= st)
    return g[0], max(1, k)


def fzw(w):
    w = w.translate(FIN)
    k = 0
    while k < 2 and len(w) > 3 and w[0] in 'שודהבלכמ':
        w = w[1:]; k += 1
    if len(w) > 3:
        w = w[0] + re.sub('[וי]', '', w[1:-1]) + w[-1]
    return w


def dk(d):
    m = re.match(r'^([א-ת]+)\s*([.:])$', (d or '').strip())
    if not m:
        return None
    n = sum(HEB.get(c, 0) for c in m.group(1))
    return n * 2 + (1 if m.group(2) == ':' else 0) if n else None


def ref_daf(ref):
    """העמוד האמיתי של התוס' מן ההפניה לספריא ("Tosafot on Kiddushin 58b:12:1" -> "נח:")."""
    from daf_check import heb
    m = re.search(r' (\d+)([ab]):', ref or '')
    if not m:
        return None
    return heb(int(m.group(1))) + ('.' if m.group(2) == 'a' else ':')


def ref_line(ref):
    m = re.search(r' \d+[ab]:(\d+)', ref or '')
    return int(m.group(1)) if m else 0


def unit_line(u):
    m = re.search(r'\.(\d+)$', u.get('ref') or '')
    return int(m.group(1)) if m else 0


def label_text(pages, lab):
    """הטקסט המנורמל של כל העמודים שתוויתם lab (בלי סינון פרק) - שם נבדקת ייחודיות העוגן."""
    us = [u for p in pages if p.get('daf') == lab for u in (p.get('units') or [])]
    return units_norm(us)


def first_page_norm(pages, lab):
    for p in pages:
        if p.get('daf') == lab:
            return units_norm(p.get('units') or [])
    return None


def resolve(it, pages, upk):
    """הדמיה של tosResolve (שלב העוגן המדויק, וחיפוש בכל העמודים שבאותה תווית).
    משמש לאימות: עוגן שנקבע בכלי חייב להיפתר כאן ליחידה שנבחרה. מחזיר (uid, k) - k מספר המופע בתוך היחידה."""
    lab = it.get('page') or it.get('daf')
    pk = int(it.get('perek') or 0)
    ctx = norm_ctx(it.get('t') or '')
    occ = it.get('occ') or 1
    N0 = first_page_norm(pages, lab)
    if N0 is None or not ctx:
        return None
    h = hit_unit(N0, ctx, occ)
    if h:
        if (not pk or upk.get(h[0]) == pk):
            return h
    same = [u for p in pages if p.get('daf') == lab for u in (p.get('units') or [])
            if (not pk or upk.get(u['id']) == pk) and u.get('k') != 'perek-range']
    return hit_unit(units_norm(same), ctx, occ) if same else None


def anchor_pos(it, pages, upk):
    """(מקום היחידה ברצף המסכת, מקום סוף העוגן בתוך היחידה) - לבדיקת סדר. None אם לא נמצא."""
    r = resolve(it, pages, upk)
    if r is None:
        return None
    uid, k = r
    flat = {}
    i = 0
    for p in pages:
        for u in p.get('units') or []:
            flat[u['id']] = (i, u); i += 1
    if uid not in flat:
        return None
    gi, u = flat[uid]
    s, _ = units_norm([u])
    ctx = norm_ctx(it.get('t') or '')
    oc = occs(s, ctx)
    return (gi, (oc[k - 1] + len(ctx)) if len(oc) >= k else len(s))


def fz_ctx(s, ctx):
    """כמו fzCtx בדפדפן: התאמה מקורבת יחידה של העוגן (או בלי המילה הראשונה/האחרונה). מחזיר את הקטע או None."""
    words = [(m.group(0), m.start(), m.end()) for m in re.finditer(r'\S+', s)]
    W = [fzw(w) for w, _, _ in words]
    cw = [fzw(w) for w in ctx.split()]
    tries = [cw] + ([cw[1:], cw[:-1]] if len(cw) >= 3 else [])
    for q in tries:
        if len(q) < 2:
            continue
        hits = [i for i in range(len(W) - len(q) + 1) if W[i:i + len(q)] == q]
        if len(hits) == 1:
            return s[words[hits[0]][1]:words[hits[0] + len(q) - 1][2]]
    return None


def tos_check(slug, pages):
    """שלוש הבדיקות הקבועות של פרומפט 96 על tosafot/<slug>/live-*.json מול הדף כפי שהאתר מציג אותו:
      noanchor - העוגן אינו נמצא בעמוד (גם לא במקורב): הסימן נופל לסוף שורה או לא מוצג.
      wrongpage - העמוד שהאתר מחפש בו (page/daf) שונה מעמוד התוס' לפי ספריא. ודאי כשהעוגן או הד"ה נמצאים
                  בעמוד הנכון (אפשר לתקן במקום); ספק כשאין להם זכר שם (גבול עמוד באתר שונה מוילנא).
      order    - שני סימנים סמוכים באותו עמוד שסדרם בטקסט הפוך ממספרם.
    בלי שיוך לפרק (אינו זמין כאן בלי הדפדפן); השיוך נבדק בדפדפן (reanchor.py ו-tools/tosafot/verify)."""
    import glob, io, json
    out = {'items': 0, 'noanchor': [], 'wrongpage_certain': [], 'wrongpage_doubt': [], 'order': []}
    files = sorted(glob.glob(os.path.join(ROOT, 'tosafot', slug, 'live-*.json')))
    if not files:
        return None
    flat = {}
    i = 0
    for p in pages:
        for u in p.get('units') or []:
            flat[u['id']] = (i, u); i += 1
    labs = {}
    for p in pages:
        labs.setdefault(p.get('daf'), []).extend(p.get('units') or [])
    lab_norm = {}

    def LN(lab):
        if lab not in lab_norm:
            lab_norm[lab] = units_norm(labs.get(lab) or [])
        return lab_norm[lab]
    bypage = {}
    for f in files:
        for it in json.load(io.open(f, encoding='utf-8')).get('items') or []:
            out['items'] += 1
            td = ref_daf(it.get('ref'))
            lab = it.get('page') or it.get('daf')
            tag = '%s %s' % (it.get('daf'), it.get('hn') or it.get('n'))
            ctx = norm_ctx(it.get('t') or '')
            q = dict(it, perek=0)
            r = resolve(q, pages, {}) if ctx else None
            if not r and ctx and (it.get('occ') or 1) == 1 and lab in labs:
                f2 = fz_ctx(LN(lab)[0], ctx)
                if f2:
                    r = resolve(dict(q, t=f2, occ=1), pages, {})
            if not r:
                out['noanchor'].append({'n': it.get('n'), 'daf': lab, 'ref_daf': td, 't': it.get('t')})
            if td and lab != td:
                s_td = LN(td)[0] if td in labs else ''
                dh = norm_ctx(it.get('dh') or '')
                present = bool(s_td) and ((ctx and occs(s_td, ctx)) or (len(dh.split()) >= 2 and occs(s_td, dh)))
                (out['wrongpage_certain'] if present else out['wrongpage_doubt']).append(
                    {'n': it.get('n'), 'page': lab, 'ref_daf': td, 't': it.get('t')})
            if r and r[0] in flat:
                gi, u = flat[r[0]]
                s_u = units_norm([u])[0]
                oc = occs(s_u, ctx) if ctx else []
                pos = (gi, (oc[r[1] - 1] + len(ctx)) if len(oc) >= r[1] else len(s_u))
                bypage.setdefault(td or lab, []).append((it.get('n'), pos))
    for d, l in bypage.items():
        l.sort(key=lambda x: x[0])
        for a, b in zip(l, l[1:]):
            if b[1] < a[1]:
                out['order'].append({'daf': d, 'a': a[0], 'b': b[0]})
    return out
