# -*- coding: utf-8 -*-
"""shas_links.py - "תנן התם" שמוביל למקום (פרומפט 82, 23.11.2026).

כשהגמרא מביאה משנה או ברייתא ממקום אחר בש"ס (תנן התם, דתנן, כדתניא, והתניא, תנא...), היחידה מקבלת קישור
לאותו מקום בלאוקמי גירסא של המסכת השנייה. רץ בסוף הבנייה (build_all), אחרי שכל דפי המסכתות נכתבו,
כמו רשת המקומות (rashut_links.py). אינו נוגע בטקסט ובקובצי הוורד: כותב קובץ נתונים קטן לכל מסכת,
site/rashut/shas-<slug>.json, ושכבת הקישורים (site/rashut.js) מסמנת בדפדפן.

הקישור ודאי בלבד. שלושה תנאים, וכולם חייבים להתקיים:
  א. ביחידה יש לשון הבאה (תנן, תניא, תנא, שנינו וכד').
  ב. טבלת הקישורים של ספריא (data/shaslinks/sefaria-shas.json, fetch_shas_links.py) מקשרת את הסעיף של היחידה
     למשנה (ומשם, דרך "משנה שבגמרא" של ספריא, למקומה בבבלי) או לסעיף בבלי במקום אחר.
     מסלול נוסף ללשון "תנן"/"שנינו" שאין לה מועמד בספריא: רצף של שש מילים לפחות שנמצא ביחידת משנה אחת בלבד
     בכל המסכתות שבאתר (כמו "נוסח ייחודי" ברשת המקומות). אותו נוסח בשתי משניות - בלי קישור.
  ג. הנוסח: רצף של ארבע מילים לפחות (בשלד, בלי ניקוד ואמות קריאה) משותף ליחידה המביאה וליחידות היעד באתר,
     ובהבאה קצרה - כל מילותיה.
יעד שהוא המשנה של הסוגיא עצמה, יעד באותו עמוד, ומסכת שאינה באתר - בלי קישור. נספר בדוח."""
import html as H, io, json, os, re, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SEF = os.path.join(ROOT, 'data', 'shaslinks', 'sefaria-shas.json')
TAG = re.compile(r'<[^>]+>')
NIK = re.compile(r'[֑-ׇ]')
FIN = str.maketrans('ךםןףץ', 'כמנפצ')
# לשון הבאה של משנה או ברייתא. בלי "תנאי"/"תנאים" (מחלוקת תנאים אינה הבאה)
MARK = re.compile(r'(?<![א-ת])(?:ו?(?:ה|כ|וכ|וה)?ד?(?:תנן|תניא|תנינא)|ו?תנא(?=[\s:,.]|$)|ו?(?:ה|כ)?(?:שנינו|ששנינו)|(?:ו)?תנו רבנן|ת"ר)(?![א-ת])')
REF = re.compile(r'^(.+)\.(\d+[ab])\.(\d+)(?:-(\d+))?')
SEG = re.compile(r'^(.+?) (\d+[ab]):(\d+)$')
MREF = re.compile(r'^Mishnah (.+?) (\d+):(\d+)(?:-(\d+))?$')
MIN_RUN = 4
UNI_RUN = 6


def plain(h):
    return re.sub(r'\s+', ' ', H.unescape(TAG.sub(' ', h or ''))).strip()


def words(t):
    out = []
    for w in re.findall(r'[א-ת"\'׳״]+', NIK.sub('', t)):
        if re.search(r'["״][א-ת]', w):
            out.append(w.replace('״', '"'))     # ראשי תיבות נשמרים כמילה
            continue
        w = w.replace("'", '').replace('׳', '').translate(FIN)
        s = re.sub('[וי]', '', w)
        if w:
            out.append(s or w)
    return out


HEAD_SLACK = 3   # הרצף חייב להתחיל בתוך שלוש המילים הראשונות שאחרי לשון ההבאה (מה שמובא, לא דיון הגמרא שאחריו)


def best_run(a, b, slack=None):
    """הרצף הארוך ביותר של מילים זהות ברצף בין שתי רשימות (תכנות דינמי).
    slack: רק רצף שמתחיל ב-a בתוך slack המילים הראשונות."""
    if not a or not b:
        return 0
    prev = [0] * (len(b) + 1)
    best = 0
    for i, x in enumerate(a):
        cur = [0] * (len(b) + 1)
        for j, y in enumerate(b, 1):
            if x == y:
                cur[j] = prev[j - 1] + 1
                if cur[j] > best and (slack is None or i - cur[j] + 1 <= slack):
                    best = cur[j]
        prev = cur
    return best


def daf_key(d):
    m = re.match(r'(\d+)([ab])', d)
    return (int(m.group(1)), m.group(2)) if m else (0, '')


def load_data(site, slug):
    p = os.path.join(site, slug + '.data.js')
    if not os.path.exists(p):
        return None
    s = io.open(p, encoding='utf-8').read()
    return json.loads(s[s.index('{'):s.rindex('}') + 1])


class Mas:
    """מסכת בנויה: יחידות לפי הסדר, עם מראה המקום האפקטיבי (יחידה בלי ref יורשת את הקודמת)."""
    def __init__(self, slug, D, tractate):
        self.slug, self.he, self.tr = slug, D.get('masechet') or slug, tractate
        self.units = []           # (uid, daf_label, kind, head, lines, (amud, seg))
        self.by_seg = collections.defaultdict(list)
        last = None
        for pg in D['pages']:
            for u in pg.get('units') or []:
                m = REF.match(u.get('ref') or '')
                if m:
                    last = (m.group(2), int(m.group(3)))
                rec = (u['id'], pg.get('daf') or '', u.get('k'), u.get('a') or '',
                       [l[1] for l in (u.get('l') or []) if isinstance(l, list) and len(l) > 1], last)
                self.units.append(rec)
                if last:
                    self.by_seg[last].append(len(self.units) - 1)
        self.pos = {r[0]: i for i, r in enumerate(self.units)}

    def text_of(self, idxs):
        return ' '.join(plain(self.units[i][3]) + ' ' + ' '.join(plain(l) for l in self.units[i][4]) for i in idxs)

    def seg_units(self, amud, a, b):
        out = []
        for s in range(a, b + 1):
            out.extend(self.by_seg.get((amud, s), []))
        return sorted(set(out))


def find_marker(rec):
    """המקום של לשון ההבאה: ['a', טקסט] בראש היחידה, או [מספר שורה, טקסט]. ומה שאחריה (מילים)."""
    head = plain(rec[3])
    m = MARK.search(head)
    if m:
        rest = head[m.end():] + ' ' + ' '.join(plain(l) for l in rec[4])
        return ['a', m.group(0)], words(rest)
    for i, l in enumerate(rec[4]):
        t = plain(l)
        m = MARK.search(t)
        if m:
            rest = t[m.end():] + ' ' + ' '.join(plain(x) for x in rec[4][i + 1:])
            return [i + 1, m.group(0)], words(rest)
    return None, None


def snippet(M, i):
    r = M.units[i]
    t = (plain(r[3]) + ' ' + ' '.join(plain(l) for l in r[4])).strip()
    return t[:170] + ('…' if len(t) > 170 else '')


def run(site, built=None, slug_of=None):
    if not os.path.exists(SEF):
        raise SystemExit('עצירה: חסר data/shaslinks/sefaria-shas.json ("תנן התם" שמוביל למקום). להריץ tools/fetch_shas_links.py')
    sef = json.load(io.open(SEF, encoding='utf-8'))
    tr_of = {}
    for f in os.listdir(os.path.join(ROOT, 'data', 'sources')):
        if f.endswith('.json'):
            tr_of[f[:-5]] = json.load(io.open(os.path.join(ROOT, 'data', 'sources', f), encoding='utf-8')).get('tractate')
    slug_tr = {v: k for k, v in tr_of.items() if v}
    MS = {}
    for f in sorted(os.listdir(site)):
        if f.endswith('.data.js'):
            slug = f[:-8]
            D = load_data(site, slug)
            if D and slug in tr_of:
                MS[slug] = Mas(slug, D, tr_of[slug])
    if not MS:
        raise SystemExit('עצירה: "תנן התם" לא מצא אף מסכת בנויה')
    missing = sorted(s for s in MS if s not in sef)
    if missing:
        raise SystemExit('עצירה: טבלת ספריא חסרה למסכתות %s - להריץ tools/fetch_shas_links.py %s' % (missing, ' '.join(missing)))
    # משנה -> מקומה בבבלי (משנה שבגמרא)
    mloc = {}
    starts = collections.defaultdict(list)
    for slug, rows in sef.items():
        for k, lst in rows.items():
            for ref, typ in lst:
                if typ != 'mishnah in talmud':
                    continue
                mm = MREF.match(ref or '')
                km = re.match(r'^(\d+[ab]):(\d+)(?:-(?:(\d+[ab]):)?(\d+))?$', k)
                if not mm or not km:
                    continue
                amud, a = km.group(1), int(km.group(2))
                b = int(km.group(4)) if km.group(4) and not km.group(3) else (a + 40 if km.group(3) else a)
                loc = (slug, amud, a, b)
                for n in range(int(mm.group(3)), int(mm.group(4) or mm.group(3)) + 1):
                    mloc.setdefault('%s %s:%d' % (mm.group(1), mm.group(2), n), loc)
                starts[slug].append((daf_key(amud), a, loc))
    for s in starts:
        starts[s].sort()

    def local_mishna(slug, amud, seg):
        cur = None
        for kk, a, loc in starts.get(slug, []):
            if (kk, a) <= (daf_key(amud), seg):
                cur = loc
            else:
                break
        return cur

    # מסלול ב: נוסח ייחודי במשניות שבאתר (רק ללשון "תנן"/"שנינו"): רצף של UNI_RUN מילים שנמצא ביחידת משנה אחת בלבד
    tri = collections.defaultdict(set)
    mwords = {}
    for ts, T in MS.items():
        for j, r in enumerate(T.units):
            if r[2] != 'm':
                continue
            ws = words(T.text_of([j]))
            mwords[(ts, j)] = ws
            for a in range(len(ws) - 2):
                tri[tuple(ws[a:a + 3])].add((ts, j))

    def unique_mishna(q, slug, here):
        cnt = collections.Counter()
        for a in range(min(len(q), 30) - 2):
            for h in tri.get(tuple(q[a:a + 3]), ()):
                cnt[h] += 1
        hits = []
        for h, n in cnt.most_common(12):
            if n < UNI_RUN - 2:
                break
            r = best_run(q[:30], mwords[h], HEAD_SLACK)
            if r >= UNI_RUN:
                hits.append((r, h))
        hits = [x for x in hits if not (x[1][0] == slug and x[1][1] <= here)] if False else hits
        if not hits:
            return None
        top = max(r for r, _ in hits)
        best = [h for r, h in hits if r == top]
        places = {(h[0], MS[h[0]].units[h[1]][1]) for h in best}
        if len(places) != 1:
            return None          # אותו נוסח בשתי משניות - לא מקשרים
        return best[0], top

    stats = collections.Counter()
    per = collections.Counter()
    samples = []
    for slug, M in MS.items():
        rows = sef.get(slug, {})
        out = {}
        for i, rec in enumerate(M.units):
            if rec[2] not in ('u', 'm', 'dh') or not rec[5]:
                continue
            pos, rest = find_marker(rec)
            if not pos:
                continue
            stats['marker'] += 1
            amud, seg = rec[5]
            cands = {}
            for ref, typ in rows.get('%s:%d' % (amud, seg), []):
                if typ == 'mishnah in talmud':
                    continue
                mm = MREF.match(ref or '')
                if mm:
                    for n in range(int(mm.group(3)), int(mm.group(4) or mm.group(3)) + 1):
                        loc = mloc.get('%s %s:%d' % (mm.group(1), mm.group(2), n))
                        if not loc or loc[0] not in MS:
                            stats['m_nosite'] += 1 if not loc or loc[0] not in MS else 0
                            continue
                        if loc == local_mishna(slug, amud, seg):
                            stats['m_local'] += 1
                            continue
                        T = MS[loc[0]]
                        idx = T.seg_units(loc[1], loc[2], loc[3])
                        if idx:
                            cands[(loc[0], idx[0])] = ('m', idx[:8])
                    continue
                sm = SEG.match(ref or '')
                if sm and sm.group(1) in slug_tr:
                    ts = slug_tr[sm.group(1)]
                    if ts not in MS:
                        stats['b_nosite'] += 1
                        continue
                    if ts == slug and sm.group(2) == amud:
                        continue
                    T = MS[ts]
                    idx = T.seg_units(sm.group(2), int(sm.group(3)), int(sm.group(3)))
                    if idx:
                        cands.setdefault((ts, idx[0]), ('b', idx[:4]))
            q = rest[:40]
            uni = None
            if not cands and re.search('תנן|שנינו|תנינא', pos[1]):
                got = unique_mishna(q, slug, i)
                if got:
                    (ts, j), r = got
                    lm = local_mishna(slug, amud, seg)
                    T = MS[ts]
                    tseg = T.units[j][5]
                    same_local = lm and ts == lm[0] and tseg and tseg[0] == lm[1] and lm[2] <= tseg[1] <= lm[3]
                    if same_local or (ts == slug and abs(T.pos[T.units[j][0]] - i) < 40):
                        stats['m_local'] += 1
                    else:
                        cands[(ts, j)] = ('m', [j])
                        uni = 1
            if not cands:
                stats['nocand'] += 1
                continue
            ok = []
            for (ts, i0), (kind, idx) in cands.items():
                T = MS[ts]
                tw = words(T.text_of(idx))
                r = best_run(q, tw, HEAD_SLACK)
                need = MIN_RUN if len(q) >= MIN_RUN else max(3, len(q))
                if r >= need:
                    ok.append((r, kind == 'm', ts, i0, kind))
            if not ok:
                stats['nomatch'] += 1
                continue
            ok.sort(key=lambda x: (-x[0], not x[1], daf_key(MS[x[2]].units[x[3]][1] or '') if False else 0))
            seen, tg = set(), []
            for r, _, ts, i0, kind in ok:
                T = MS[ts]
                if (ts, T.units[i0][1]) in seen:
                    continue
                seen.add((ts, T.units[i0][1]))
                tg.append([ts, T.he, T.units[i0][1], T.units[i0][0], kind, snippet(T, i0)])
                if len(tg) == 3:
                    break
            out[str(rec[0])] = [pos[0], pos[1], ''.join(words(pos[1])), tg]
            stats['linked'] += 1
            if uni:
                stats['unique'] += 1
            stats['to_m' if tg[0][4] == 'm' else 'to_b'] += 1
            per[slug] += 1
            if len(samples) < 40 and tg[0][0] != slug:
                samples.append([M.he, rec[1], pos[1], tg[0][1], tg[0][2], tg[0][5][:80]])
        os.makedirs(os.path.join(site, 'rashut'), exist_ok=True)
        with io.open(os.path.join(site, 'rashut', 'shas-' + slug + '.json'), 'w', encoding='utf-8', newline='\n') as f:
            json.dump({'v': 1, 'u': out}, f, ensure_ascii=False, separators=(',', ':'))
    rep = {'stats': dict(stats), 'per': {MS[s].he: n for s, n in sorted(per.items())}, 'samples': samples}
    with io.open(os.path.join(site, 'rashut', 'shas-stats.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(rep, f, ensure_ascii=False, indent=0)
    print('"תנן התם": %d מסכתות; לשון הבאה ב-%d יחידות - קושרו %d (למשנה %d, לברייתא/סוגיא %d); '
          'מהם בנוסח ייחודי במשניות %d; בלי מועמד %d, נוסח לא תאם %d, משנת הסוגיא עצמה %d'
          % (len(MS), stats['marker'], stats['linked'], stats['to_m'], stats['to_b'], stats['unique'], stats['nocand'], stats['nomatch'], stats['m_local']))
    return rep


if __name__ == '__main__':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    run(os.path.join(ROOT, 'site'))
