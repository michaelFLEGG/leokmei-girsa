# -*- coding: utf-8 -*-
"""mishna_gaps.py - חוסר חלקי בתיבות המשנה (פרומפט 87, 23.11.2026). מכני, בלי בינה מלאכותית.

לכל פרק: כל תיבות המשנה שלו (לפי הסדר) מול המשניות של הפרק במקור הקנוני (data/mishna/<slug>.json),
מילה מול מילה, אחרי נרמול: בלי ניקוד ופיסוק, בלי ו' וי', ראשי תיבות נפתחים (ב"ש, ר', רבי...),
בלי "אומר/אומרים" (בתיבה הם נכתבים בנקודתיים), ובלי [ביאור בסוגריים מרובעים].

ממצא:
  gap  - רצף של 3 מילים ומעלה מן המשנה שאין לו מקבילה בתיבות (ייתכן שהוא ישב מחוץ לתיבה).
  word - מילה מהותית אחת או שתיים שחסרות (בלי ניסוח אחר במקומן) - לעיון בלבד, לא מתוקן אוטומטית.

    from mishna_gaps import analyze     analyze(slug, rows) -> רשימת ממצאים
rows: שורות הדף כפי שהדפדפן מציג אותן (id, box, title, daf, items[{ek, h, t}]), או מבנה דומה מן הבנייה.
"""
import re, difflib, html as _html
import mishna_guard as G

NIK = re.compile('[֑-ׇ]')
FIN = str.maketrans('םןץךף', 'מנצכפ')
SKIP = {'אמר', 'אמר', 'אמרמ', 'אמרת', 'אמרנ'}      # "אומר/אומרים/אומרת" אחרי הסרת ו' וי'
LET = {c: i + 1 for i, c in enumerate('אבגדהוזחט')}
LET.update({'י': 10, 'כ': 20, 'ל': 30, 'מ': 40, 'נ': 50})
STOP = {'את', 'של', 'על', 'אם', 'לא', 'כל', 'מן', 'אל', 'זה', 'הוא', 'היא', 'אף', 'או', 'כן', 'אבל', 'אלא', 'שהוא',
        'אין', 'יש', 'עד', 'בה', 'בו', 'לו', 'לה', 'הם', 'הן', 'בין', 'אחד', 'אחת', 'רבי'}


def letters_num(s):
    return sum(LET.get(c, 0) for c in s)


XABBR = dict(G.ABBR)
XABBR.update({
    'רשבג': 'רבן שמעון בן גמליאל', 'ראבע': 'רבי אלעזר בן עזריה', 'ראבי': 'רבי אליעזר בן יעקב',
    'ריבב': 'רבי יהודה בן בתירא', 'רשבא': 'רבי שמעון בן אלעזר', 'רשבנ': 'רבי שמעון בן ננס',
    'ריהג': 'רבי יוסי הגלילי', 'רי': 'רבי יהודה', 'רע': 'רבי עקיבא', 'רא': 'רבי אליעזר', 'ריב': 'רבי יהודה בן',
    'יוט': 'יום טוב', 'יט': 'יום טוב', 'קש': 'קריאת שמע', 'וחכא': 'וחכמים אומרים', 'חכא': 'חכמים אומרים',
    'שנ': 'שנאמר', 'שנא': 'שנאמר', 'בדא': 'במה דברים אמורים', 'הז': 'הרי זה', 'הד': 'הא כיצד',
    'דר': 'דברי רבי', 'כש': 'כל שהוא', 'עמ': 'על מנת', 'בד': 'בית דין', 'כהג': 'כהן גדול', 'עה': 'עם הארץ',
    'אי': 'ארץ ישראל', 'בהמ': 'בית המקדש', 'הק': 'הקדש', 'רג': 'רבן גמליאל', 'עכם': 'עובדי כוכבים',
    'עכום': 'עובדי כוכבים', 'עז': 'עבודה זרה', 'כג': 'כיוצא בו', 'וכו': 'וכולי', 'כו': 'וכולי',
    'א': 'אחד', 'ב': 'שתי', 'ג': 'שלש', 'ז': 'שבע', 'ח': 'שמונה', 'ט': 'תשע',
})
# מספרים: מפתח אחיד לכל צורות המספר (שני/שתי/שנים/שתים, ב')
NUM = {}
for _n, _ws in ((1, 'אחד אחת'), (2, 'שנים שתים שני שתי שניהם'), (3, 'שלש שלשה שלשת שלוש שלושה'),
                (4, 'ארבע ארבעה ארבעת'), (5, 'חמש חמשה חמשת'), (6, 'שש ששה ששת'), (7, 'שבע שבעה שבעת'),
                (8, 'שמנה שמונה שמונת שמנת'), (9, 'תשע תשעה תשעת'), (10, 'עשר עשרה עשרת')):
    for _w in _ws.split():
        NUM[re.sub('[וי]', '', _w).translate(FIN)] = '#%d' % _n


def key(w):
    w = NIK.sub('', w).replace('״', '"').replace('׳', "'")
    w = re.sub('[^א-ת]', '', w)
    w = re.sub('[וי]', '', w).translate(FIN)
    return NUM.get(w, w)


def words_of(text, paren=False):
    """[(מילה, התחלה, סוף, בתוך סוגריים?)] לפי תווים בטקסט הגלוי. paren: גם (...) נחשב סוגריים (מראה מקום במקור)."""
    out = []
    depth = 0
    pat = r'[\[\]()]|[^\s\[\]()]+' if paren else r'\[|\]|[^\s\[\]]+'
    for m in re.finditer(pat, text):
        t = m.group(0)
        if t in '[(' and len(t) == 1:
            depth += 1; continue
        if t in '])' and len(t) == 1:
            depth = max(0, depth - 1); continue
        out.append((t, m.start(), m.end(), depth > 0))
    return out


def expand(tok):
    """מילה בתיבה -> רשימת מפתחות (ראשי תיבות נפתחים)."""
    t = NIK.sub('', tok).replace('״', '"').replace('׳', "'")
    t = re.sub('[^א-ת"\']', '', t)
    if not t:
        return []
    if '"' in t or "'" in t:
        k = t.replace('"', '').replace("'", '')
        if k in XABBR:
            return [key(x) for x in XABBR[k].split()]
        if len(k) > 2 and k[0] in 'ובכלמהש' and k[1:] in XABBR:
            return [key(x) for x in XABBR[k[1:]].split()]
    k = key(t)
    return [k] if k else []


def sim(a, b):
    if a == b:
        return 1.0
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()


def fuzzy_align(S, B):
    """יישור DP קטן בתוך בלוק replace: [(i or None, j or None)]."""
    n, m = len(S), len(B)
    INF = 10 ** 9
    D = [[0.0] * (m + 1) for _ in range(n + 1)]
    P = [[None] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        D[i][0] = D[i - 1][0] - 1; P[i][0] = 'u'
    for j in range(1, m + 1):
        D[0][j] = D[0][j - 1] - 1; P[0][j] = 'l'
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            s = sim(S[i - 1], B[j - 1])
            best, bp = D[i - 1][j] - 1, 'u'
            if D[i][j - 1] - 1 > best:
                best, bp = D[i][j - 1] - 1, 'l'
            if s >= 0.6 and D[i - 1][j - 1] + 2 * s > best:
                best, bp = D[i - 1][j - 1] + 2 * s, 'd'
            D[i][j], P[i][j] = best, bp
    i, j, out = n, m, []
    while i or j:
        p = P[i][j]
        if p == 'd':
            out.append((i - 1, j - 1)); i -= 1; j -= 1
        elif p == 'u':
            out.append((i - 1, None)); i -= 1
        else:
            out.append((None, j - 1)); j -= 1
    return out[::-1]


def plain(h):
    return _html.unescape(re.sub(r'<[^>]+>', '', h or '')).replace('\xa0', ' ')


def perek_boxes(rows):
    """{מספר פרק: [(row index, row)]} לפי תווית התיבה ('פרק ה, משנה ב')."""
    out = {}
    last = None
    for i, r in enumerate(rows):
        if not r.get('box'):
            continue
        m = re.match(r'פרק ([א-ת]+)', r.get('title') or '')
        pn = letters_num(m.group(1)) if m else last
        if pn is None:
            continue
        last = pn
        # פתיחת המשנה כתובה לפעמים בד"ה משנה שלפני התיבה (כתובות: "המדיר את אשתו..." ובתיבה " - יוציא")
        j = i - 1
        while j >= 0 and rows[j].get('k') in ('perek-start', 'perek-range'):
            j -= 1
        if j >= 0 and rows[j].get('k') == 'dh' and not _auto(rows[j]):
            out.setdefault(pn, []).append((j, rows[j]))
        out.setdefault(pn, []).append((i, r))
    return out


def _auto(r):
    """ד"ה משנה שנוצר אוטומטית מן הגמרא (מזהה 700000 ומעלה) אינו חלק מן התיבה."""
    try:
        return int(str(r.get('uid') or r.get('id', 'u0')).lstrip('u')) >= 700000
    except ValueError:
        return False


def canon(slug):
    import json, io, os
    p = os.path.join(G.MDIR, slug + '.json')
    if not os.path.exists(p):
        return None
    return json.load(io.open(p, encoding='utf-8')).get('chapters') or []


def analyze(slug, rows, chapters=None):
    chs = chapters if chapters is not None else canon(slug)
    if not chs:
        return []
    found = []
    PB = perek_boxes(rows)
    for pn, bxs in sorted(PB.items()):
        # מילות התיבות
        B = []          # {k, row, item, ws(start,end in t), line}
        for ri, r in bxs:
            for ii, it in enumerate(r['items']):
                if it.get('anchor') and r.get('k') != 'dh':
                    continue
                t = plain(it['h']) if it.get('h') is not None else it['t']
                for (w, a, b, br) in words_of(t):
                    if br:
                        continue
                    for k in expand(w):
                        if k in SKIP or not k:
                            continue
                        B.append({'k': k, 'ri': ri, 'ii': ii, 'a': a, 'b': b})
        if len(B) < 3:
            continue
        # הפרק הקנוני: לפי המספר, ואם הכיסוי נמוך - הפרק המכוסה ביותר
        bk = [x['k'] for x in B]
        bset = set(zip(bk, bk[1:]))

        def S_of(ci):
            S = []
            for mi, m in enumerate(chs[ci]):
                for wi, (w, a, b, br) in enumerate(words_of(m, paren=True)):
                    if br:
                        continue
                    for k in expand(w):
                        if k in SKIP or not k:
                            continue
                        S.append({'k': k, 'm': mi + 1, 'w': w, 'wi': wi, 'mi': mi, 'a': a, 'b': b})
            return S

        def cov(ci):
            S = S_of(ci)
            sk = [x['k'] for x in S]
            sb = set(zip(sk, sk[1:]))
            return len(sb & bset) / float(max(1, len(bset)))
        ci = pn - 1 if 0 < pn <= len(chs) else None
        if ci is None or cov(ci) < 0.5:
            best = max(range(len(chs)), key=cov)
            if ci is None or cov(best) > cov(ci) + 0.15:
                ci = best
        S = S_of(ci)
        sk = [x['k'] for x in S]
        # תיבות שמכסות רק חלק מן הפרק (הבבלי חותך פרקים אחרת): היישור רק בטווח שבין המשנה הראשונה לאחרונה שנמצאו
        sm = difflib.SequenceMatcher(None, sk, bk, autojunk=False)
        ops = sm.get_opcodes()
        # רשימת זוגות (i, j)
        pairs = []
        for tag, i1, i2, j1, j2 in ops:
            if tag == 'equal':
                pairs += [(i1 + d, j1 + d) for d in range(i2 - i1)]
            elif tag == 'delete':
                pairs += [(i, None) for i in range(i1, i2)]
            elif tag == 'insert':
                pairs += [(None, j) for j in range(j1, j2)]
            else:
                for a, b in fuzzy_align(sk[i1:i2], bk[j1:j2]):
                    pairs.append((None if a is None else i1 + a, None if b is None else j1 + b))
        matched = [p for p in pairs if p[0] is not None and p[1] is not None]
        if not matched:
            continue
        mi_first = S[matched[0][0]]['mi']
        mi_last = S[matched[-1][0]]['mi']
        # מקטעים בין עוגנים (זוגות מותאמים): מה שחסר בתיבה ומה שנוסף בה באותו מקום
        mpos = [n for n, (a, b) in enumerate(pairs) if a is not None and b is not None]
        mlen = {s: len(chs[ci][s]) for s in range(len(chs[ci]))}

        def strength(n, step):
            """כמה זוגות מותאמים רצופים מן העוגן (כולל) בכיוון step."""
            c = 0
            while 0 <= n < len(pairs) and pairs[n][0] is not None and pairs[n][1] is not None:
                c += 1; n += step
            return c
        # נאמנות כל תיבה למקור: תיבה מלאה (לשון המשנה) מול תיבה מקוצרת (לשון השיננא)
        rst = {}
        for a, b in pairs:
            if b is None:
                continue
            st = rst.setdefault(B[b]['ri'], {'nb': 0, 'nm': 0, 'S': []})
            st['nb'] += 1
            if a is not None:
                st['nm'] += 1; st['S'].append(a)

        def fid(ri, gapn):
            st = rst.get(ri)
            if not st or not st['S']:
                return 0.0, 1.0
            rng = max(st['S']) - min(st['S']) + 1
            inside = sum(1 for i in gapset if min(st['S']) < i < max(st['S']))
            return st['nm'] / float(max(1, rng - inside)), (st['nb'] - st['nm']) / float(max(1, st['nb']))
        bounds = [-1] + mpos + [len(pairs)]
        for x, y in zip(bounds, bounds[1:]):
            seg = pairs[x + 1:y]
            miss = [a for a, b in seg if a is not None and b is None]
            extra = [b for a, b in seg if a is None and b is not None]
            if not miss:
                continue
            ss = [S[i] for i in miss if mi_first <= S[i]['mi'] <= mi_last]
            if not ss:
                continue
            n = len(ss)
            sub = [w for w in ss if w['k'] not in STOP and len(w['k']) >= 3 and not w['k'].startswith('#')]
            if n >= 3:
                kind = 'gap'
            elif sub and not extra:
                kind = 'word'
            else:
                continue
            gapset = set(miss)
            prevj = pairs[x][1] if x >= 0 else None
            nextj = pairs[y][1] if y < len(pairs) else None
            # משנה שלמה בתוך החוסר (מתחילתה ועד סופה)
            whole = []
            for mi in sorted({w['mi'] for w in ss}):
                have = [w for w in ss if w['mi'] == mi]
                tot = sum(1 for w in S if w['mi'] == mi)
                if len(have) >= tot:
                    whole.append(mi + 1)
            found.append({'perek': pn, 'chapter': ci + 1, 'kind': kind, 'S': ss, 'extra': [B[j] for j in extra],
                          'prev': B[prevj] if prevj is not None else None,
                          'next': B[nextj] if nextj is not None else None,
                          'sp': strength(x, -1) if x >= 0 else 0, 'sn': strength(y, 1) if y < len(pairs) else 0,
                          'whole': whole, 'start': ss[0]['wi'] == 0,
                          'end': ss[-1]['wi'] == len(words_of(chs[ci][ss[-1]['mi']], paren=True)) - 1 or
                                 all(w2['mi'] != ss[-1]['mi'] or w2['wi'] <= ss[-1]['wi'] for w2 in S),
                          'fid': [fid(B[j]['ri'], n) for j in (prevj, nextj) if j is not None],
                          'rows': bxs, 'replaced': len(extra)})
    return found


# ---------------------------------------------------------------- החלטה לכל חוסר (פרומפט 87)
# fix / move - חוסר אמיתי בתיבה שהיא לשון המשנה, עם מקום ודאי; outside / box / rephrase / weak / summary / style /
# abbr / condensed / word - לעיון או אינו חוסר. ל-fix ו-move מוחזרת גם ההשלמה המוצעת (wasH/nowH).


def was_of(h):
    return _html.unescape(re.sub(r'<[^>]+>', '', h or ''))


def html_pos(h, pos):
    """אינדקס ב-HTML שבו מתחיל התו ה-pos של הטקסט הגלוי, אחרי תגיות סוגרות."""
    i, c = 0, 0
    n = len(h)
    while i < n and c < pos:
        if h[i] == '<':
            j = h.find('>', i)
            i = n if j < 0 else j + 1
            continue
        if h[i] == '&':
            m = re.match(r'&[#a-zA-Z0-9]+;', h[i:])
            if m:
                i += len(m.group(0)); c += 1; continue
        i += 1; c += 1
    while i < n and h.startswith('</', i):
        i = h.find('>', i) + 1
    return i


def voweled(t):
    ws = [w for w in t.split() if re.search('[א-ת]', w)]
    if not ws:
        return False
    return sum(1 for w in ws if NIK.search(w)) / float(len(ws)) >= 0.5


def gap_text(chs, ci, ss):
    parts = []
    for mi in sorted({w['mi'] for w in ss}):
        ws = [w for w in ss if w['mi'] == mi]
        parts.append(chs[ci][mi][ws[0]['a']:ws[-1]['b']])
    t = ' '.join(parts)
    t = re.sub(r'\s*\([^)]*\)', '', t)
    return ' '.join(t.split())


def keys_of(t):
    out = []
    for (w, a, b, br) in words_of(t):
        if br:
            continue
        out += [k for k in expand(w) if k and k not in SKIP]
    return out


def cov(G, L):
    """כמה מן G נמצא ב-L לפי הסדר."""
    if not G:
        return 0.0
    sm = difflib.SequenceMatcher(None, G, L, autojunk=False)
    return sum(b.size for b in sm.get_matching_blocks()) / float(len(G))


def decide(slug, rows, f, chs):
    pv, nx = f['prev'], f['next']
    ss = f['S']
    n = len(ss)
    G = [w['k'] for w in ss]
    out = {'perek': f['perek'], 'chapter': f['chapter'], 'mishna': sorted({w['m'] for w in ss}), 'n': n,
           'text': gap_text(chs, f['chapter'] - 1, ss)}
    anc = pv or nx
    out['daf'] = rows[anc['ri']]['daf'] if anc else ''
    if f['kind'] != 'gap':
        out['decision'] = 'word'
        return out
    # השורות שמחוץ לתיבות בטווח: בין העוגנים, או עד 40 יחידות אחרי העוגן
    lo = (pv['ri'] if pv else nx['ri'] - 40)
    hi = (nx['ri'] if nx else pv['ri'] + 40)
    if hi - lo > 80:
        hi = lo + 80 if pv else hi
        lo = hi - 80 if not pv else lo
    hits = []
    for ri in range(max(0, lo - 2), min(len(rows), hi + 3)):
        r = rows[ri]
        if r.get('box'):
            continue
        for it in r['items']:
            if it.get('anchor'):
                continue
            L = keys_of(plain(it['h']))
            if len(L) < 2:
                continue
            c = cov(G, L)
            own = cov(L, G)
            if c >= 0.6 or (own >= 0.85 and len(L) >= 3):
                hits.append({'ri': ri, 'ek': it['ek'], 'cov': round(c, 2), 'own': round(own, 2), 't': plain(it['h'])[:120]})
    out['outside'] = hits
    # תיבה מקוצרת (לשון השיננא) אינה משלימים בה: רק תיבה שהיא לשון המשנה (90% ומעלה)
    fids = f.get('fid') or []
    out['fid'] = [round(a, 2) for a, b in fids]
    if not fids or min(a for a, b in fids) < 0.9 or max(b for a, b in fids) > 0.2:
        out['decision'] = 'summary'; out['why'] = 'תיבה מקוצרת (נאמנות %s)' % out['fid']
        return out
    # מילות מסגרת וייחוס אינן תוכן חסר: "דברי רבי מאיר" כשהשם כבר בתיבה, "אמר להם", "שנאמר"
    boxkeys = set()
    for ri in {b['ri'] for b in (pv, nx) if b}:
        for it in rows[ri]['items']:
            if not it.get('anchor'):
                boxkeys |= set(keys_of(plain(it['h'])))
    FRAME = {key(w) for w in 'דברי רבי רבן אמר אמרו לו להם לה שנאמר ונאמר אומר אומרים והלא שנאמר אמר ליה'.split()}
    content = [w for w in ss if w['k'] not in FRAME and not (w['k'] in boxkeys and len(w['k']) >= 3 and
               any(w['k'] == key(x) for x in 'מאיר יהודה יוסי שמעון אליעזר עקיבא ישמעאל טרפון גמליאל יהושע אלעזר שמאי הלל חכמים'.split()))]
    out['content'] = len(content)
    if len(content) < 3:
        out['decision'] = 'style'; out['why'] = 'מילות מסגרת וייחוס בלבד'
        return out
    # שם תנא במקום שבתיבה כתוב בראשי תיבות שלא נפתחו (ראב"ש, רחב"א): אינו חוסר
    NAMES = {key(x) for x in 'רבי רבן בן ברבי מאיר יהודה יוסי שמעון אליעזר עקיבא ישמעאל טרפון גמליאל יהושע אלעזר חנינא יוחנן ברוקה אנטיגנוס בתירא עזריה דוסא חנניה יעקב נחוניא הקנה זכאי'.split()}
    near = ''
    for b in (pv, nx):
        if b:
            near += plain(rows[b['ri']]['items'][b['ii']]['h'])[max(0, b['a'] - 25):b['b'] + 25]
    if sum(1 for w in content if w['k'] in NAMES) * 2 >= len(content) and re.search('["\'״׳]', near):
        out['decision'] = 'abbr'; out['why'] = 'שם בראשי תיבות'
        return out
    # צמצום של המחבר: תוכן החסר כבר כתוב באותה תיבה (משפט מקביל שנכתב פעם אחת)
    ck = [w['k'] for w in content]
    if sum(1 for k in ck if k in boxkeys) >= 0.7 * len(ck):
        out['decision'] = 'condensed'; out['why'] = 'התוכן כבר בתיבה (צמצום)'
        return out
    if f['whole']:
        out['decision'] = 'box'; out['why'] = 'משנה שלמה חסרה (%s)' % ','.join(map(str, f['whole']))
        return out
    if f['replaced'] and f['replaced'] * 3 >= n:
        out['decision'] = 'rephrase'; out['why'] = 'בתיבה ניסוח אחר (%d מילים) במקום החסר' % f['replaced']
        out['extra'] = ' '.join(plain(rows[b['ri']]['items'][b['ii']]['h'])[b['a']:b['b']] for b in f['extra'])[:120]
        return out
    if (pv and f['sp'] < 2) or (nx and f['sn'] < 2) or not anc:
        # עוגן חלש מותר רק בקצה שורה (תחילת או סוף פסקה)
        okp = pv is None or f['sp'] >= 2 or plain(rows[pv['ri']]['items'][pv['ii']]['h'])[pv['b']:].strip(' ,.:;-') == ''
        okn = nx is None or f['sn'] >= 2 or plain(rows[nx['ri']]['items'][nx['ii']]['h'])[:nx['a']].strip(' ,.:;-') == ''
        if not (okp and okn) or not anc:
            out['decision'] = 'weak'; out['why'] = 'עוגן חלש'
            return out
    same_line = pv and nx and pv['ri'] == nx['ri'] and pv['ii'] == nx['ii']
    # בקצה תיבה (בין שתי תיבות, או אחרי האחרונה): חוסר ארוך הוא כנראה תיבה שלמה של הבבלי שחסרה
    if not same_line:
        if pv and nx and pv['ri'] != nx['ri']:
            between = [ri for ri in range(pv['ri'] + 1, nx['ri']) if rows[ri].get('box')]
            if between or nx['ri'] - pv['ri'] > 8 or rows[pv['ri']]['daf'] != rows[nx['ri']]['daf'] and n >= 12:
                out['decision'] = 'box'; out['why'] = 'החוסר בין תיבות רחוקות - כנראה תיבה של הבבלי שחסרה'
                return out
        if n >= 15:
            out['decision'] = 'box'; out['why'] = 'חוסר ארוך בקצה התיבה (%d מילים) - כנראה תיבה של הבבלי שחסרה' % n
            return out
    move = []
    if hits:
        if pv and nx and pv['ri'] != nx['ri'] and nx['ri'] - pv['ri'] <= 8:
            move = [h for h in hits if pv['ri'] < h['ri'] < nx['ri'] and h['own'] >= 0.8]
        if not move:
            out['decision'] = 'outside'; out['why'] = 'החסר נמצא כשורה מחוץ לתיבה'
            return out
    # מקום ההכנסה
    if same_line:
        tgt, mode = nx, 'before'
    elif pv and not (f['start'] and nx):
        tgt, mode = pv, 'after'
    elif nx:
        tgt, mode = nx, 'before'
    else:
        tgt, mode = pv, 'after'
    r = rows[tgt['ri']]
    it = r['items'][tgt['ii']]
    h = it['h']
    pt = plain(h)
    vow = voweled(pt)
    g = out['text']
    if not vow:
        g = NIK.sub('', g)
    g = g.replace('׃', ':')
    g = re.sub(r':(?=\s)', '.', g)          # סוף משנה בספריא (נקודתיים) באמצע ההשלמה - נקודה
    if mode == 'after':
        tail = pt[tgt['b']:]
        at_end = True     # העוגן הבא אינו באותה שורה: ההשלמה בסוף השורה (אחרי תוספת של המחבר)
        if at_end:
            g2 = re.sub(r'[:.]$', '.', g)
            core = h.rstrip()
            # סימן סוף הפסקה (נקודה) נעשה פסיק לפני ההשלמה
            m = re.search(r'\.((?:</[^>]+>|\s)*)$', core)
            if m:
                core = core[:m.start()] + ',' + m.group(1)
            elif not re.search(r'[,;:](?:</[^>]+>|\s)*$', core):
                core = core + ','
            newh = core + ' ' + g2
        else:
            g2 = re.sub(r'[:.]$', ',', g)
            i = html_pos(h, tgt['b'])
            # אחרי סימן פיסוק שצמוד למילה
            while i < len(h) and h[i] in ',.;:':
                i += 1
            newh = h[:i] + ' ' + g2 + h[i:]
    else:
        g2 = re.sub(r'[:.]$', ',', g)
        if not g2.endswith(','):
            g2 = g2 + ''
        i = html_pos(h, tgt['a'])
        newh = h[:i] + g2 + ' ' + h[i:]
    newh = re.sub(r'  +', ' ', newh)
    out.update({'decision': 'move' if move else 'fix', 'ek': it['ek'], 'mode': mode, 'wasH': h, 'nowH': newh,
                'was': was_of(h), 'now': was_of(newh), 'move': move, 'row': r['id']})
    return out




def rows_from_pages(pages):
    """נתוני הדף (pages מן הבנייה / fold.view) -> rows כמו בנתונים שבדפדפן."""
    out = []
    for pg in pages:
        for u in pg.get('units') or []:
            mp, mn = u.get('mp'), u.get('mbn') or u.get('mb')
            R = {'id': 'u%s' % u.get('id'), 'uid': u.get('id'), 'k': u.get('k'), 'daf': pg.get('daf'),
                 'box': u.get('k') == 'm', 'items': [],
                 'title': ('פרק %s%s' % (_letters(mp), (', משנה ' + _letters(mn)) if mn else '')) if u.get('k') == 'm' and mp else ''}
            if u.get('a'):
                R['items'].append({'ek': 'u%s.0' % u.get('id'), 'h': u.get('a'), 'anchor': True})
            for n, l in enumerate(u.get('l') or []):
                R['items'].append({'ek': 'u%s.%d' % (u.get('id'), n + 1), 'h': l[1] if len(l) > 1 else ''})
            out.append(R)
    return out


def _letters(n):
    a = 'אבגדהוזחטיכלמנ'
    try:
        n = int(n)
    except (TypeError, ValueError):
        return ''
    if n <= 0:
        return ''
    if n <= 10:
        return a[n - 1]
    if n < 20:
        return 'י' + a[n - 11]
    if n == 20:
        return 'כ'
    return 'כ' + a[n - 21]


def report(slug, rows):
    """כל ההחלטות למסכת."""
    chs = canon(slug)
    if not chs:
        return []
    return [decide(slug, rows, f, chs) for f in analyze(slug, rows, chs)]


def sig(x):
    """חתימה יציבה של ממצא (לרשימת מה שכבר נבדק): פרק, משניות, והטקסט החסר בלי ניקוד."""
    return '%s|%s|%s' % (x.get('chapter'), ','.join(map(str, x.get('mishna') or [])), NIK.sub('', x.get('text') or '')[:60])
