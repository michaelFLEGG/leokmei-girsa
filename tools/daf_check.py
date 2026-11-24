# -*- coding: utf-8 -*-
"""daf_check.py - בודק ציוני הדף ("דף בצד") של כל מסכת. פרומפט 91 (24.11.2026). מכני, בלי מודל.

שני מבחנים:
  א. רצף: ציוני הדף עוברים עמוד אחר עמוד - בלי חסר, בלי כפול ובלי חזרה אחורה.
  ב. מקום: לכל עמוד בספריא (data/sources/<מסכת>.json) - איפה בלאוקמי הוא מתחיל. כל יחידה בדף (כותרת צד
     ושורותיה) מקבלת ציון דמיון לכל עמוד גמרא סמוך (מילים משותפות במשקל נדירות, ורצפי שתי מילים), ושיוך
     מונוטוני (תכנון דינמי) קובע לכל יחידה את העמוד שלה. תחילת העמוד = היחידה הראשונה ששויכה אליו.
     שתי מילות פתיחה של העמוד בספריא שנמצאות ביחידה עצמה מחזקות את הקביעה.

מה יוצא:
  - data/daf-check/<מסכת>.json: הספירה (חסרים, כפולים, חזרות, ציונים שזזו), והצעות תיקון.
  - הצעה ודאית (ok=1) נכתבת עם --write אל data/daf-fix/<מסכת>.json, והקיפול הלילי (tools/fold.py) מחיל
    אותה על הספר: מוסיף פסקת "דף בצד" לפני היחידה, או מתקן ציון שגוי (נב. -> נב:). ספק - נשאר ברשימה למנהל.

    python tools/daf_check.py                         כל המסכתות, מן הספר (input/docx) בלבד
    python tools/daf_check.py --only shabbat --live   הספר עם השכבה החיה (/live), כמו שהמנהל רואה
    python tools/daf_check.py --only shabbat --rows FILE   עמודים שנמשכו מן הדפדפן (D.pages)
    python tools/daf_check.py --only shabbat --write  כותב את ההצעות הוודאיות לקיפול
    python tools/daf_check.py --gate                  לקיפול: נכשל אם מספר החסרים/הכפולים עלה על הבסיס
"""
import os, sys, io, re, json, math, html, argparse, datetime, collections

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'tools'))
OUT = os.path.join(HERE, 'data', 'daf-check')
FIX = os.path.join(HERE, 'data', 'daf-fix')
BASE = os.path.join(OUT, '_base.json')

V = {'א': 1, 'ב': 2, 'ג': 3, 'ד': 4, 'ה': 5, 'ו': 6, 'ז': 7, 'ח': 8, 'ט': 9, 'י': 10, 'כ': 20, 'ל': 30, 'מ': 40,
     'נ': 50, 'ס': 60, 'ע': 70, 'פ': 80, 'צ': 90, 'ק': 100, 'ר': 200, 'ש': 300, 'ת': 400}
NIK = re.compile('[֑-ׇ]')
FIN = str.maketrans('ךםןףץ', 'כמנפצ')
SKIPK = ('perek-range', 'perek-start', 'perek-num', 'perek-name', 'hadran', 'hatz')


def dk(d):
    """'נב:' -> מספר העמוד (דף*2 + 1 לעמוד ב). אחרת None."""
    m = re.match(r'^\s*([א-ת"\'״׳]+)\s*([.:])\s*$', d or '')
    if not m:
        return None
    n = sum(V.get(c, 0) for c in m.group(1))
    return n * 2 + (1 if m.group(2) == ':' else 0) if n else None


def heb(n):
    out = ''
    for v, c in ((400, 'ת'), (300, 'ש'), (200, 'ר'), (100, 'ק')):
        while n >= v:
            out += c; n -= v
    if n == 15:
        return out + 'טו'
    if n == 16:
        return out + 'טז'
    for v, c in ((90, 'צ'), (80, 'פ'), (70, 'ע'), (60, 'ס'), (50, 'נ'), (40, 'מ'), (30, 'ל'), (20, 'כ'), (10, 'י'),
                 (9, 'ט'), (8, 'ח'), (7, 'ז'), (6, 'ו'), (5, 'ה'), (4, 'ד'), (3, 'ג'), (2, 'ב'), (1, 'א')):
        while n >= v:
            out += c; n -= v
    return out


def label(k):
    return heb(k // 2) + ('.' if k % 2 == 0 else ':')


def plain(h):
    return html.unescape(re.sub(r'<[^>]+>', ' ', h or '')).replace('\xa0', ' ')


def words(t):
    t = NIK.sub('', plain(t)).translate(FIN)
    t = re.sub(r'[^א-ת\s]', ' ', t)
    out = []
    for w in t.split():
        k = 0
        while k < 2 and len(w) > 3 and w[0] in 'ודהבלכמש':
            w = w[1:]; k += 1
        if len(w) > 3:
            w = w[0] + re.sub('[וי]', '', w[1:-1]) + w[-1]
        if len(w) >= 2:
            out.append(w)
    return out


# ---------------------------------------------------------------- מקורות

def load_rows(slug, mode, rows_file=None):
    """העמודים: [{daf, perek, units:[{k,id,a,l}]}]"""
    if rows_file:
        r = json.load(io.open(rows_file, encoding='utf-8'))
        return r['pages'] if isinstance(r, dict) else r
    import mishna_check as M
    return M.pages_of(slug, mode == 'live', None)


def sefaria(slug):
    p = os.path.join(HERE, 'data', 'sources', slug + '.json')
    if not os.path.exists(p):
        return None
    d = json.load(io.open(p, encoding='utf-8'))
    out = {}
    for lab, v in (d.get('pages') or {}).items():
        k = dk(lab)
        if k is not None:
            out[k] = ' '.join(v.get('gemara') or [])
    return out


# ---------------------------------------------------------------- הבדיקה

def items_of(pages):
    """יחידות הדף ברצף: (מספר העמוד באתר, תווית העמוד, היחידה, מילים)."""
    it = []
    for pi, p in enumerate(pages):
        for ui, u in enumerate(p.get('units') or []):
            if u.get('k') in SKIPK:
                continue
            t = (u.get('a') or '') + ' ' + ' '.join((x[1] if isinstance(x, list) else str(x)) for x in (u.get('l') or []))
            ws = words(t)
            if not ws:
                continue
            it.append({'pi': pi, 'daf': p.get('daf'), 'u': u, 'ui': ui, 'w': ws, 'first': ui == 0 or all(
                (y.get('k') in SKIPK) for y in p['units'][:ui])})
    return it


def check(slug, pages, src):
    labels = [(pi, p.get('daf'), dk(p.get('daf'))) for pi, p in enumerate(pages)]
    seq = {'missing': [], 'dup': [], 'back': [], 'bad': []}
    seen = collections.Counter()
    prev = None
    for pi, lab, k in labels:
        if k is None:
            seq['bad'].append(lab); continue
        if prev is not None and k - prev > 20:
            seq['bad'].append(lab); continue      # קפיצה של יותר מעשרה דפים - תווית שגויה (נזיר: "שצה:"), לא רצף
        seen[k] += 1
        if seen[k] > 1:
            seq['dup'].append({'pi': pi, 'daf': lab})
        if prev is not None:
            if k < prev:
                seq['back'].append({'pi': pi, 'daf': lab, 'after': label(prev)})
            elif k > prev + 1:
                seq['missing'] += [label(x) for x in range(prev + 1, k) if not seen[x]]
        prev = k
    ks = [k for _, _, k in labels if k is not None]
    res = {'slug': slug, 'pages': len(pages), 'first': label(min(ks)) if ks else '', 'last': label(max(ks)) if ks else '',
           'missing': sorted(set(seq['missing']), key=dk), 'dup': seq['dup'], 'back': seq['back'], 'badlabel': seq['bad']}
    # missing גם מן הסוף אינו נספר: הטווח הוא מן הראשון עד האחרון שבאתר
    res['n_missing'] = len(res['missing']); res['n_dup'] = len(res['dup']); res['n_back'] = len(res['back'])
    if not src:
        res['place'] = 'אין מקור ספריא'
        return res, []
    return res, place(slug, pages, src, res)


def place(slug, pages, src, res):
    items = items_of(pages)
    if not items:
        return []
    K = sorted(k for k in src if (dk(res['first']) or 0) - 1 <= k <= (dk(res['last']) or 10 ** 6) + 1)
    if not K:
        return []
    kix = {k: i for i, k in enumerate(K)}
    aw = {k: words(src[k]) for k in K}
    df = collections.Counter()
    for k in K:
        df.update(set(aw[k]))
    N = len(K)
    idf = {w: math.log((N + 1) / (c + 0.5)) for w, c in df.items()}
    aset = {k: set(aw[k]) for k in K}
    abig = {k: set(zip(aw[k], aw[k][1:])) for k in K}
    W = 8   # חלון: עד 8 עמודים מן התווית

    def lab_k(x):
        k = dk(x['daf'])
        return k if k is not None else None

    # ציון לכל יחידה מול כל עמוד בחלון
    S = []
    for x in items:
        k0 = lab_k(x)
        ws = x['w']; st = set(ws); bg = set(zip(ws, ws[1:]))
        norm = math.sqrt(len(st)) + 1
        row = {}
        for k in K:
            if k0 is not None and abs(k - k0) > W:
                continue
            sc = sum(idf.get(w, 0) for w in st & aset[k]) / norm + 1.5 * len(bg & abig[k]) / norm
            if k == k0:
                sc += 0.6          # הנחה: רוב הציונים נכונים
            row[k] = sc
        S.append(row)
    # שיוך מונוטוני: dp[i][j] = הציון הטוב ביותר כשיחידה i בעמוד K[j]
    n, m = len(items), len(K)
    NEG = -1e18
    prev = [NEG] * m
    back = []
    for i in range(n):
        row = S[i]
        cur = [NEG] * m
        bk = [0] * m
        best, bj = NEG, 0
        for j in range(m):
            if i == 0:
                cand, cj = 0.0, j
            else:
                if prev[j] > best:
                    best, bj = prev[j], j
                cand, cj = best, bj
            sc = row.get(K[j])
            if sc is None:
                sc = -3.0     # מחוץ לחלון
            # קפיצה של יותר מעמוד אחד עולה מעט (דילוג על עמוד שאין לו תוכן בלאוקמי)
            jump = max(0, j - cj - 1) * 0.8 if i else 0
            cur[j] = cand + sc - jump
            bk[j] = cj
        back.append(bk)
        prev = cur
    j = max(range(m), key=lambda t: prev[t])
    asg = [0] * n
    for i in range(n - 1, -1, -1):
        asg[i] = j
        j = back[i][j]
    starts = {}
    for i, a in enumerate(asg):
        starts.setdefault(K[a], i)
    # ההצעות
    props = []
    have = collections.defaultdict(list)   # k -> [pi]
    for pi, p in enumerate(pages):
        k = dk(p.get('daf'))
        if k is not None:
            have[k].append(pi)
    first_item_of_page = {}
    for i, x in enumerate(items):
        first_item_of_page.setdefault(x['pi'], i)

    def opening_hit(k, i):
        """שלוש/שתי מילות הפתיחה של העמוד בספריא ביחידה i (או השכנה)."""
        ow = aw[k][:6]
        for L in (3, 2):
            for s0 in range(0, max(1, len(ow) - L + 1)):
                g = ow[s0:s0 + L]
                if len(g) < L or sum(len(w) for w in g) < 6:
                    continue
                for ii in (i, i - 1, i + 1):
                    if 0 <= ii < n:
                        ws = items[ii]['w']
                        for t in range(len(ws) - L + 1):
                            if ws[t:t + L] == g:
                                return ii, ' '.join(g)
        return None, None

    for k in K:
        if k not in starts:
            continue
        i = starts[k]
        x = items[i]
        lab = label(k)
        if k in have and len(have[k]) == 1:
            pi = have[k][0]
            fi = first_item_of_page.get(pi)
            if fi is None or fi == i:
                continue
            # הציון קיים אבל במקום אחר מן החזוי
            props.append({'op': 'moved', 'daf': lab, 'now_at': items[fi]['u'].get('id'), 'pred_at': x['u'].get('id'),
                          'shift_units': i - fi, 'ok': 0, 'why': 'הציון קיים, והחזוי במרחק %d יחידות' % (i - fi)})
            continue
        if k in have and len(have[k]) > 1:
            continue
        # חסר: מקום מוצע
        oi, og = opening_hit(k, i)
        at = oi if oi is not None else i
        y = items[at]
        # השורה שבה מילות הפתיחה (הציון נכנס לפני השורה הזאת; שורה ראשונה של יחידה - לפני כותרת הצד)
        lines = [' '.join(plain(x[1] if isinstance(x, list) else x).split()) for x in (y['u'].get('l') or [])]
        li, mid = 0, False
        if og:
            g = og.split()
            for q, ln in enumerate(lines):
                lw = words(ln)
                pos = next((t for t in range(len(lw) - len(g) + 1) if lw[t:t + len(g)] == g), None)
                if pos is not None:
                    li, mid = q, pos > 3
                    break
        # העוגן הוא שורת הגוף עצמה (כותרת צד קצרה מדי לזיהוי יחיד; tools/daf_fix.py מכניס את הציון לפני הכותרת)
        anchor = lines[li] if lines else ' '.join(plain(y['u'].get('a') or '').split())
        if y['u'].get('k') in ('nose', 'dh'):
            anchor = ' '.join(plain(y['u'].get('a') or '').split())
        # ודאות: מילות הפתיחה נמצאו בתחילת שורה (לא באמצע), והתווית הנוכחית קודמת לעמוד בעד שלושה עמודים
        prevlab = y['daf']
        pk = dk(prevlab)
        ok = 1 if (og and not mid and pk is not None and pk < k and k - pk <= 3) else 0
        props.append({'op': 'add', 'daf': lab, 'before_id': y['u'].get('id'), 'page': prevlab,
                      'text': anchor[:60], 'line': li, 'mid': int(mid),
                      'kind': y['u'].get('k'), 'opening': og or '', 'ok': ok,
                      'why': ('מילות הפתיחה "%s"%s' % (og, ' באמצע שורה' if mid else '')) if og else 'לפי השיוך בלבד (בלי מילות פתיחה)'})
    # כפולים: התווית השנייה - לאיזה עמוד שויכה רוב היחידות שבה
    for d in res['dup']:
        pi = d['pi']
        ii = [i for i, x in enumerate(items) if x['pi'] == pi]
        if not ii:
            continue
        cnt = collections.Counter(K[asg[i]] for i in ii)
        kk, c = cnt.most_common(1)[0]
        k0 = dk(d['daf'])
        if kk != k0 and len(have.get(kk, [])) == 0 and c >= max(1, len(ii) // 2):
            props.append({'op': 'fix', 'daf_from': d['daf'], 'daf': label(kk), 'page_index_from': pi,
                          'after_id': items[ii[0]]['u'].get('id'),
                          'text': ' '.join(plain(items[ii[0]]['u'].get('a') or '').split())[:40] or
                                  ' '.join(plain((items[ii[0]]['u'].get('l') or [['', '']])[0][1]).split())[:60],
                          'ok': 1 if (abs(kk - k0) == 1 and c >= 3 and c >= 0.85 * len(ii)) else 0,
                          'why': '%d מתוך %d יחידות שויכו ל-%s' % (c, len(ii), label(kk))})
    # תיקון (fix) ותוספת (add) לאותו עמוד: התיקון גובר, והתוספת (אם ודאית) נותנת לו את המקום המדויק
    fixes = {p['daf']: p for p in props if p['op'] == 'fix'}
    out = []
    for p in props:
        if p['op'] == 'add' and p['daf'] in fixes:
            f = fixes[p['daf']]
            if p.get('ok') and p.get('text'):
                f['move_before'] = p['text']
                f['ok'] = 1 if abs(dk(f['daf']) - dk(f['daf_from'])) == 1 else 0   # מילות הפתיחה מאשרות את המקום
            continue
        out.append(p)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', default='')
    ap.add_argument('--live', action='store_true')
    ap.add_argument('--rows', default='')
    ap.add_argument('--write', action='store_true')
    ap.add_argument('--gate', action='store_true')
    ap.add_argument('--base', action='store_true', help='שמור את הספירה הנוכחית כבסיס לשער')
    a = ap.parse_args()
    book = json.load(io.open(os.path.join(HERE, 'data', 'book.json'), encoding='utf-8'))
    slugs = [s for s in book['slugs'] if not a.only or s in a.only.split(',')]
    os.makedirs(OUT, exist_ok=True)
    tot = collections.Counter()
    summary = {}
    for s in slugs:
        try:
            pages = load_rows(s, 'live' if a.live else 'book', a.rows or None)
        except Exception as e:
            print('%-14s שגיאה: %s' % (s, str(e)[:120])); continue
        res, props = check(s, pages, sefaria(s))
        res['when'] = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        res['mode'] = 'rows' if a.rows else ('live' if a.live else 'book')
        res['props'] = props
        okn = sum(1 for p in props if p.get('ok') and p['op'] in ('add', 'fix'))
        res['n_sure'] = okn
        res['n_doubt'] = sum(1 for p in props if not p.get('ok'))
        json.dump(res, io.open(os.path.join(OUT, s + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        summary[s] = {'missing': res['n_missing'], 'dup': res['n_dup'], 'back': res['n_back'], 'sure': okn, 'doubt': res['n_doubt']}
        tot.update({'missing': res['n_missing'], 'dup': res['n_dup'], 'back': res['n_back'], 'sure': okn})
        print('%-14s עמודים %4d | חסרים %3d כפולים %3d חזרות %2d | ודאי לתיקון %3d, ספק %3d'
              % (s, res['pages'], res['n_missing'], res['n_dup'], res['n_back'], okn, res['n_doubt']))
        if a.write and okn:
            write_fix(s, [p for p in props if p.get('ok') and p['op'] in ('add', 'fix')])
    print('סה"כ: חסרים %(missing)d, כפולים %(dup)d, חזרות %(back)d, ודאי לתיקון %(sure)d' % tot)
    if a.base:
        json.dump(summary, io.open(BASE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    if a.gate:
        base = json.load(io.open(BASE, encoding='utf-8')) if os.path.exists(BASE) else {}
        worse = [s for s, v in summary.items() if s in base and
                 (v['missing'] > base[s]['missing'] or v['dup'] > base[s]['dup'] or v['back'] > base[s]['back'])]
        if worse:
            print('שער ציוני הדף נכשל: עלייה בחסרים/כפולים/חזרות ב-' + ', '.join(worse))
            return 1
        # שיפור מעדכן את הבסיס כלפי מטה
        for s, v in summary.items():
            if s in base:
                base[s] = {kk: min(v[kk], base[s][kk]) for kk in ('missing', 'dup', 'back')}
            else:
                base[s] = {kk: v[kk] for kk in ('missing', 'dup', 'back')}
        json.dump(base, io.open(BASE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return 0


def write_fix(slug, props):
    """מוסיף ל-data/daf-fix/<מסכת>.json את ההצעות הוודאיות שאינן שם כבר (לפי הדף)."""
    os.makedirs(FIX, exist_ok=True)
    p = os.path.join(FIX, slug + '.json')
    cur = json.load(io.open(p, encoding='utf-8')) if os.path.exists(p) else {'v': 1, 'slug': slug, 'ops': []}
    have = {(o['op'], o['daf']) for o in cur['ops']}
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    n = 0
    for pr in props:
        if (pr['op'], pr['daf']) in have:
            continue
        o = {'op': pr['op'], 'daf': pr['daf'], 'src': 'daf_check', 'when': now, 'why': pr.get('why', '')}
        if pr['op'] == 'add':
            o.update(page=pr['page'], text=pr['text'], kind=pr.get('kind'))
        else:
            o.update(daf_from=pr['daf_from'], text=pr['text'])
            if pr.get('move_before'):
                o['move_before'] = pr['move_before']
        cur['ops'].append(o); n += 1
    json.dump(cur, io.open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('  %s: %d הצעות ודאיות נכתבו לקיפול' % (slug, n))


if __name__ == '__main__':
    sys.exit(main())
