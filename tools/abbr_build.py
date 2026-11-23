# -*- coding: utf-8 -*-
"""abbr_build.py - מילון ראשי תיבות מכל המסכתות (פרומפט 80 ד, 23.11.2026).

מקור הפתיחה: הגמרא שבספריא (data/sources/<מסכת>.json, William Davidson), לא הזיכרון. לכל ראשי תיבות בטקסט של האתר
(בגרשיים: ר"י, קמ"ל, קר"ש...) מחפשים בקטע הגמרא שהיחידה הוצמדה אליו (ref, ושני הקטעים שלידו), ואם אין - בכל הדף,
רצף מילים רצוף שהאותיות הראשונות שלהן (אות עד שלוש מכל מילה) הן בדיוק אותיות ראשי התיבות.

  - פתיחה במקום מסוים (לנגיעה באתר, פרומפט 81): רק כשבהקשר של אותה סוגיה נמצאה פתיחה אחת בלבד. אחרת - אינה נפתחת.
  - במפתח הכללי: כל הפתיחות שנמצאו, לפי השכיחות. פתיחה שנמצאה פעם אחת בלבד בכל הש"ס ואינה ודאית בשום מקום - אינה נכנסת.
  - אות שימוש בראש (ו, ד, ש, ב, ל, כ, מ, ה): "דר"י" נרשם תחת ר"י כשגם ר"י לבדו קיים, והפתיחה בלי האות.

פלט: data/abbr/<מסכת>.json ({"abbr": {ר"ת: {פתיחה: מספר}}, "at": {מזהה-יחידה: [[ר"ת כפי שכתוב, מופע, פתיחה]]}}),
ו-data/abbr/all.json - המילון הכללי. הבנייה מעתיקה את קובץ המסכת לאתר (site/abbr/) לעמוד המפתח בהדפסה.

    python tools/abbr_build.py              # כל המסכתות שבאתר הבנוי
    python tools/abbr_build.py taanit
"""
import io, json, os, re, sys, glob, html as _html
from collections import defaultdict, Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

NIK = re.compile(r'[֑-ׇ]')
TAG = re.compile(r'<[^>]+>')
ABBR = re.compile(r'(?<![א-ת"\'׳״])([א-ת]{1,4})["״]([א-ת]{1,2})(?![א-ת"\'׳״])')
PFX = 'ודשבלכמה'
GEM = {'א': 1, 'ב': 2, 'ג': 3, 'ד': 4, 'ה': 5, 'ו': 6, 'ז': 7, 'ח': 8, 'ט': 9, 'י': 10, 'כ': 20, 'ל': 30, 'מ': 40, 'נ': 50,
       'ס': 60, 'ע': 70, 'פ': 80, 'צ': 90, 'ק': 100, 'ר': 200, 'ש': 300, 'ת': 400}
FIN = str.maketrans('ךםןףץ', 'כמנפצ')


def plain(h):
    return _html.unescape(TAG.sub(' ', h or ''))


def words_of(t):
    t = NIK.sub('', t or '')
    return [w for w in re.findall(r'[א-ת]+', t)]


def is_number(a):
    """ראשי תיבות שהם מספר (י"ח, תרי"ג, כ"ד) - אינם נפתחים."""
    s = a.replace('"', '')
    try:
        v = [GEM[c.translate(FIN)] for c in s]
    except KeyError:
        return False
    return all(v[i] >= v[i + 1] for i in range(len(v) - 1)) and len(s) <= 4


def match_at(letters, ws, i):
    """פתיחות שמתחילות במילה i: כל מילה תורמת 1-3 אותיות מראשה, לפחות שתי מילים, כל האותיות נצרכות."""
    out = []

    def rec(pos, j, acc):
        if pos == len(letters):
            if len(acc) >= 2:
                out.append(tuple(acc))
            return
        if j >= len(ws) or len(acc) >= 5:
            return
        w = ws[j].translate(FIN)
        for n in (1, 2, 3):
            if pos + n <= len(letters) and len(w) >= n and w[:n] == letters[pos:pos + n]:
                # מילה שתורמת יותר מאות אחת: רק המילה הראשונה (קר"ש, אע"פ) או מילה קצרה כולה
                if n > 1 and acc and n != len(w):
                    continue
                rec(pos + n, j + 1, acc + [ws[j]])
    rec(0, i, [])
    return out


def expansions(abbr, ws):
    letters = abbr.replace('"', '').translate(FIN)
    res = set()
    for i in range(len(ws)):
        if ws[i][:1].translate(FIN) != letters[:1]:
            continue
        for m in match_at(letters, ws, i):
            res.add(' '.join(m))
    return res


def daf2sef(daf):
    m = re.match(r'^([א-ת]+)([.:])$', (daf or '').strip())
    if not m:
        return None
    n = sum(GEM.get(c, 0) for c in m.group(1).replace('טו', 'טו'))
    return '%d%s' % (n, 'a' if m.group(2) == '.' else 'b')


def load_site(slug):
    import pagedata
    s = pagedata.read_html(os.path.join(ROOT, 'site', slug + '.html'))
    i = s.find('const DATA=')
    d, _ = json.JSONDecoder().raw_decode(s[i + 11:])
    return d


def unit_texts(u):
    out = []
    for k in ('a', 'w'):
        if isinstance(u.get(k), str):
            out.append(u[k])
    for l in u.get('l') or []:
        if len(l) > 1:
            out.append(l[1])
    return plain(' '.join(out))


def run(slug):
    sp = os.path.join(ROOT, 'data', 'sources', slug + '.json')
    if not os.path.exists(sp):
        return None
    src = json.load(io.open(sp, encoding='utf-8'))
    segs = {}
    P = src.get('pages') or []
    for p in (P.values() if isinstance(P, dict) else P):
        segs[p['daf']] = [words_of(g) for g in p.get('gemara') or []]
    d = load_site(slug)
    cnt = defaultdict(Counter)       # ר"ת -> פתיחות (מכל המופעים שנמצאה בהם התאמה)
    sure = defaultdict(Counter)      # רק מופעים שבהם נמצאה פתיחה אחת בהקשר
    nsure = defaultdict(Counter)     # ...ובהקשר הצר (קטע הגמרא של היחידה, לא כל הדף)
    places = defaultdict(lambda: defaultdict(set))   # באילו קטעי גמרא שונים נמצאה הפתיחה
    seen = Counter()
    at = {}
    for pg in d['pages']:
        sdaf = daf2sef(pg.get('daf'))
        for u in pg['units']:
            t = unit_texts(u)
            hits = list(ABBR.finditer(t))
            if not hits:
                continue
            ctx = []
            ref = u.get('ref') or ''
            m = re.match(r'^[^.]+\.(\d+[ab])\.(\d+)', ref)
            if m and m.group(1) in segs:
                sg, k = segs[m.group(1)], int(m.group(2)) - 1
                for q in range(max(0, k - 1), min(len(sg), k + 2)):
                    ctx += sg[q]
            wide = [w for g in segs.get(sdaf or '', []) for w in g]
            occ = Counter()
            for h in hits:
                a = h.group(1) + '"' + h.group(2)
                n = occ[a]
                occ[a] += 1
                # מספר (י"ח, כ"ד) אינו נפסל מראש: ר"י הוא גם 210. הוא פשוט לא יימצא כרצף מילים בגמרא
                seen[a] += 1
                ex = expansions(a, ctx) if ctx else set()
                narrow = bool(ex)
                if not ex:
                    ex = expansions(a, wide)
                # כל הדף כהקשר: רק כשנמצאה בו פתיחה אחת (אחרת רעש של צירופים מקריים, א"ל = "אי לא"...)
                if narrow or len(ex) == 1:
                    for e in ex:
                        cnt[a][e] += 1
                        places[a][e].add(ref or pg.get('daf'))
                if len(ex) == 1:
                    e = next(iter(ex))
                    sure[a][e] += 1
                    if narrow:
                        nsure[a][e] += 1
                    at.setdefault(str(u['id']), []).append([a, n, e])
    # אות שימוש בראש: דר"י -> ר"י כשר"י קיים לבדו
    # אות שימוש מקופלת רק כשהפתיחה בלי האות נמצאה גם לר"ת בלי האות (דרבי יוחנן -> רבי יוחנן, כשר"י נפתח לרבי יוחנן).
    # אחרת (הר"ז = הרי זה) - נשאר ר"ת בפני עצמו
    base = {a: set(cnt[a]) for a in cnt}
    def fold(c, pl=False):
        for a in list(c):
            if a[0] in PFX and len(a.replace('"', '')) >= 3:
                b = a[1:]
                if b not in base:
                    continue
                moved = []
                for e in list(c[a].keys() if not pl else c[a].keys()):
                    if e[0] == a[0] and len(e) > 1 and e[1] == b[0] and e[1:] in base[b]:
                        moved.append(e)
                for e in moved:
                    if pl:
                        c[b][e[1:]] |= c[a][e]
                    else:
                        c[b][e[1:]] += c[a][e]
                    del c[a][e]
                if not c[a]:
                    del c[a]
    fold(cnt)
    fold(sure)
    fold(nsure)
    fold(places, True)
    TENS, UNITS = 'יכלמנסעפצ', 'אבגדהוזחט'
    out = {}
    for a in sorted(cnt):
        top = cnt[a].most_common(1)[0][1] if cnt[a] else 0
        # נכנס למפתח: פתיחה ודאית בהקשר הצר, או שכיחה (3 ומעלה). פתיחה יחידה מול פתיחה שולטת (5 ומעלה) - רעש
        numlike = len(a) == 3 and a[0] in TENS and a[2] in UNITS          # י"ב, כ"ד: אולי מספר - רק בוודאות כפולה
        keep = {e: v for e, v in cnt[a].most_common()
                if ((nsure[a].get(e, 0) >= (2 if numlike else 1)) or (not numlike and len(places[a][e]) >= 3))
                and not (v == 1 and top >= 5)}
        if keep:
            out[a] = keep
    return {'masechet': d.get('masechet'), 'abbr': out, 'at': at,
            'stat': {'kinds': len(seen), 'occ': sum(seen.values()), 'opened': len(out),
                     'sure_occ': sum(len(v) for v in at.values())}}


def main():
    import build_all
    slugs = sys.argv[1:] or [s for s in build_all.LATIN if os.path.exists(os.path.join(ROOT, 'site', s + '.html'))]
    od = os.path.join(ROOT, 'data', 'abbr')
    os.makedirs(od, exist_ok=True)
    allc = defaultdict(Counter)
    for s in slugs:
        r = run(s)
        if not r:
            print('%s: אין מקור' % s)
            continue
        io.open(os.path.join(od, s + '.json'), 'w', encoding='utf-8').write(json.dumps(r, ensure_ascii=False, indent=0))
        for a, ex in r['abbr'].items():
            for e, v in ex.items():
                allc[a][e] += v
        # המופעים הוודאיים - רק פתיחה שנכנסה למפתח
        r['at'] = {k: [x for x in v if x[2] in (r['abbr'].get(x[0]) or {})] for k, v in r['at'].items()}
        r['at'] = {k: v for k, v in r['at'].items() if v}
        io.open(os.path.join(od, s + '.json'), 'w', encoding='utf-8').write(json.dumps(r, ensure_ascii=False, indent=0))
        print('%s: %d סוגי ר"ת, %d מופעים, %d נפתחו במפתח, %d מופעים ודאיים' % (s, r['stat']['kinds'], r['stat']['occ'], r['stat']['opened'], r['stat']['sure_occ']))
    if not sys.argv[1:]:
        allo = {a: dict(allc[a].most_common()) for a in sorted(allc)}
        io.open(os.path.join(od, 'all.json'), 'w', encoding='utf-8').write(json.dumps(
            {'note': 'מילון ראשי תיבות מכל המסכתות (פרומפט 80 ד). פתיחה = רצף מילים בגמרא שבספריא שבהקשר היחידה. מספר = מופעים.',
             'abbr': allo}, ensure_ascii=False, indent=0))
        print('all: %d ר"ת' % len(allo))


if __name__ == '__main__':
    main()
