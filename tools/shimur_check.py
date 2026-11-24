# -*- coding: utf-8 -*-
"""בדיקת שימור הטקסט (24.11.2026, אחרי משנה שנקטעה בשבת נא:-נב.).

השאלה: האם יש טקסט שעריכה כלשהי (של מיכאל, של סכם, של כלי) התכוונה להשאיר בדף - ואינו בדף.
כך נתפס כל כשל מכני בהחלת עריכות (שרשרת פיצול שנקטעה, עריכה שלא מצאה את מקומה וכו'),
בלי מודל ובלי לקרוא את התוכן.

לכל עריכה: הנוסח שהיא השאירה (now בעריכת טקסט; השורות שבסוף פיצול/איחוד/הזזה).
נוסח שעריכה מאוחרת יותר נגעה בו (was / texts שלה חופפים לו) - הוחלף בכוונה, ואינו נבדק.
כל נוסח אחר חייב להופיע בדף החי (הדף כפי שגולש רואה אותו, אחרי /live) סמוך לדף שלו;
כל רצף של 3 מילים ומעלה ממנו שאינו בדף - נרשם.

  uv run python -X utf8 tools/shimur_check.py <dump.json> [--out res.json]
<dump.json>: הפלט של semantic_io.py dump:<מסכת> אחרי פענוח ({rows, base, live}).
"""
import sys, re, json, html, argparse, collections

NIK = re.compile('[֑-ׇ]')
TAG = re.compile(r'<[^>]+>')
NONW = re.compile(r'[^א-ת0-9a-zA-Z\s]')
MINRUN = 3


def words(s):
    s = html.unescape(TAG.sub(' ', str(s or '')))
    s = NIK.sub('', s).replace('"', '').replace("'", '').replace('״', '').replace('׳', '')
    s = NONW.sub(' ', s)
    return [w for w in s.split() if w]


DAFN = {}


def dafkey(d):
    """נא: -> מספר רץ (נא. = 2*51, נא: = 2*51+1)"""
    if d in DAFN:
        return DAFN[d]
    m = re.match(r'^\s*([א-ת"\']+)\s*([.:])', str(d or ''))
    v = None
    if m:
        g = {'א': 1, 'ב': 2, 'ג': 3, 'ד': 4, 'ה': 5, 'ו': 6, 'ז': 7, 'ח': 8, 'ט': 9, 'י': 10, 'כ': 20, 'ל': 30, 'מ': 40,
             'נ': 50, 'ס': 60, 'ע': 70, 'פ': 80, 'צ': 90, 'ק': 100, 'ר': 200, 'ש': 300, 'ת': 400}
        n = sum(g.get(c, 0) for c in m.group(1))
        v = 2 * n + (1 if m.group(2) == ':' else 0)
    DAFN[d] = v
    return v


def intents(e):
    """הנוסחים שהעריכה השאירה בדף, ומה שהיא נשענה עליו (קלט)"""
    out, inp = [], []
    if e.get('op') == 'struct':
        inp = list(e.get('texts') or [])
        rt = e.get('resT')
        if rt:
            out = [x for x in rt if isinstance(x, str)]
        else:
            for r in e.get('res') or []:
                if isinstance(r, list) and len(r) >= 2 and isinstance(r[-1], str):
                    out.append(r[-1])
    else:
        if e.get('was') is not None:
            inp = [e.get('was')]
        if e.get('now') is not None:
            out = [e.get('nowH') if e.get('nowH') is not None else e.get('now')]
    return out, inp


def has_seq(hay, seq):
    """seq (רשימת מילים) מופיע ברצף בתוך hay (מחרוזת ' w1 w2 ... ')"""
    return (' ' + ' '.join(seq) + ' ') in hay


def missing_runs(ws, hay):
    """רצפים מקסימליים של מילים מ-ws שאינם בדף: מילה נחשבת 'בדף' אם היא חלק מצמד/שלישייה רציפה שבדף"""
    n = len(ws)
    ok = [False] * n
    for i in range(n):
        for L in (3, 2):
            for a in range(max(0, i - L + 1), min(i, n - L) + 1):
                if has_seq(hay, ws[a:a + L]):
                    ok[i] = True
                    break
            if ok[i]:
                break
        if not ok[i] and n < 3 and has_seq(hay, [ws[i]]):
            ok[i] = True
    runs, cur = [], []
    for i in range(n):
        if not ok[i]:
            cur.append(ws[i])
        else:
            if len(cur) >= MINRUN:
                runs.append(' '.join(cur))
            cur = []
    if len(cur) >= MINRUN:
        runs.append(' '.join(cur))
    return runs


def run(dump, near=3):
    rows = dump['rows']
    E = sorted(dump.get('live') or [], key=lambda e: e.get('t') or 0)
    # הדף החי: לכל דף - כל הטקסט שבו ברצף; וגם כל המסכת
    perdaf = collections.defaultdict(list)
    cur = None
    for r in rows:
        if r.get('daf'):
            cur = dafkey(r['daf'])
        perdaf[cur].append(' '.join(words(r.get('t') or r.get('h') or '')))
    allhay = ' ' + ' '.join(' '.join(v) for v in perdaf.values()) + ' '
    keys = sorted(k for k in perdaf if k is not None)
    cache = {}

    def hay_near(d):
        if d is None:
            return allhay
        if d not in cache:
            cache[d] = ' ' + ' '.join(' '.join(perdaf[k]) for k in keys if abs(k - d) <= near) + ' '
        return cache[d]

    # הקלט של כל עריכה (was / texts), ומפתח 3-מילים -> העריכות שהקלט שלהן מכיל אותו
    INP = []
    G = collections.defaultdict(list)
    for j, e in enumerate(E):
        _, inp = intents(e)
        xs = [' ' + ' '.join(words(x)) + ' ' for x in inp if words(x)]
        INP.append(xs)
        seen = set()
        for x in xs:
            w = x.split()
            for k in range(len(w) - 2):
                g = ' '.join(w[k:k + 3])
                if g not in seen:
                    seen.add(g); G[g].append(j)

    def seen_later(i, run):
        """עריכה מאוחרת יותר (j > i) שהקלט שלה מכיל את הרצף - כלומר מי שערך אחר כך ראה את המילים, והסרתן בכוונה"""
        w = run.split()
        g = ' '.join(w[:3])
        pat = ' ' + run + ' '
        for j in G.get(g, ()):
            if j > i and any(pat in x for x in INP[j]):
                return j
        return None

    res = []
    stat = collections.Counter()
    for i, e in enumerate(E):
        outs, _ = intents(e)
        for o in outs:
            ws = words(o)
            if len(ws) < MINRUN:
                continue
            stat['נבדקו'] += 1
            norm = ' ' + ' '.join(ws) + ' '
            d = dafkey(e.get('daf'))
            if norm in hay_near(d):
                stat['בדף'] += 1
                continue
            runs = missing_runs(ws, hay_near(d))
            if runs:
                runs = missing_runs(ws, allhay) and [r for r in runs if missing_runs(r.split(), allhay)]
            if not runs:
                stat['בדף (בשינוי שורות או בדף אחר)'] += 1
                continue
            lost = [r for r in runs if seen_later(i, r) is None]
            if not lost:
                stat['הוסר בכוונה בעריכה מאוחרת'] += 1
                continue
            stat['חסר'] += 1
            res.append({'k': e.get('k'), 'daf': e.get('daf'), 't': e.get('t'), 'op': e.get('op') or 'text', 'kind': e.get('kind'),
                        'text': ' '.join(ws), 'missing': lost})
    return res, stat


def _overlap(a, b):
    """חפיפה של רצף 4 מילים ומעלה בין שני נוסחים"""
    wa, wb = a.split(), b.split()
    if len(wa) < 4 or len(wb) < 4:
        return False
    sb = ' ' + b + ' '
    for k in range(len(wa) - 3):
        if (' ' + ' '.join(wa[k:k + 4]) + ' ') in sb:
            return True
    return False


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('dump')
    ap.add_argument('--out', default='')
    a = ap.parse_args()
    d = json.load(open(a.dump, encoding='utf-8'))
    res, stat = run(d)
    print(dict(stat))
    for x in res[:40]:
        print(x['daf'], x['k'], x['op'], x.get('kind') or '', '|', ' / '.join(x['missing'])[:160])
    if a.out:
        json.dump({'stat': dict(stat), 'res': res}, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
