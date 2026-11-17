# -*- coding: utf-8 -*-
"""enum_am.py - אות מספור של שיטה/דעה (א. ב. ג. ...) בתוך שורה: בסגנון התו "אמוראים" (פרומפט 60 ד, 17.11.2026).

מיכאל (17.11.2026): "כלל לכל הלאוקמי: אות של מספור שיטה/דעה (א. ב. ג. ...) בתוך שורה - בסגנון התו אמוראים, לא רגיל."

הכלל (משותף לאתר, למנוע המכני ולסכם - ראה docs/sakem-lessons.md):
  - אות מספור = אות עברית אחת (א-ט, י, כ) או שתיים בצורת מספר (יא-יט, טו, טז, כא-כט), ונקודה,
    בתחילת השורה או אחרי פסיק/רווח, ואחריה (ברווח או צמוד) מילה עברית - שם או קביעה.
  - אינה בתוך תגית קיימת (סגנון תו אחר, פסוק, הערה), אינה אחרי "(" או "דף" (ציון דף), ואינה חלק ממילה.
  - אות שאינה בתחילת שורה נחשבת מספור רק כשיש באותה יחידה (או ביחידה שלפניה/אחריה) אות מספור סמוכה (n-1 או n+1).
    בתחילת שורה - גם לבדה (כמו "ג. צריכה אף צורת הפתח" בסוכה ז., שקודמותיה ביחידות אחרות), עד ט.
  - לא נוגעים: בכותרת צד (u.a), בתוך מסגרת משנה (k='m' / מסגרת ממוספרת), בהערות התוס' (אינן בשורות), ובכותרות.
  - הרווח אחרי האות: רווח רגיל אחד בדיוק ("ה.ר"ג" -> "ה. ר"ג") - חלק מן הכלל של רשימה סימטרית (פרומפט 60 ה).

ההחלה: דרך שכבת העריכות (PUT /edits), כמו כל עריכה של המנהל, כדי שהקיפול הלילי יכניס לספר. שורה שיש לה עריכה חיה
(של מיכאל או של כל אחד) - לא נוגעים בה בסבב הזה (אחרי הקיפול היא בספר, והסבב הבא מטפל בה).

    python tools/overflow/enum_am.py --slug sukkah --site <מראה> [--examples 5]      (ספירה ודוגמאות, בלי לשלוח)
    בפעולה overflow.yml: auto.py enum --slug <מסכת> --site <מראה> --commit, ואחריו auto.py push
"""
import html as H, json, os, re, sys

NUM1 = 'אבגדהוזחטיכ'
NUM2 = ['י' + c for c in 'אבגדהוזחט' if c not in 'הו'] + ['טו', 'טז'] + ['כ' + c for c in 'אבגדהוזחט']
GEM = {c: i + 1 for i, c in enumerate('אבגדהוזחט')}
GEM.update({'י': 10, 'כ': 20})


def val(t):
    if len(t) == 1:
        return GEM.get(t)
    if t == 'טו':
        return 15
    if t == 'טז':
        return 16
    return GEM.get(t[0], 0) + GEM.get(t[1], 0)


def valid(t):
    return (len(t) == 1 and t in NUM1) or t in NUM2


# מועמד בתוך קטע טקסט ברמה העליונה של השורה (לא בתוך תגית)
TOK = re.compile(r'(?<![א-ת"\'׳״\w(])([א-ת]{1,2})\.(?=( ?)(?:[א-ת]|["\'׳]|&quot;|<))')


def top_segments(h):
    """קטעי הטקסט שברמה העליונה (עומק תגיות 0): [(התחלה, סוף)] ב-HTML"""
    out, depth, i, n, start = [], 0, 0, len(h), 0
    while i < n:
        if h[i] == '<':
            if depth == 0 and i > start:
                out.append((start, i))
            j = h.find('>', i)
            if j < 0:
                break
            tag = h[i:j + 1]
            if tag.startswith('</'):
                depth = max(0, depth - 1)
            elif not tag.endswith('/>') and not re.match(r'<(br|img|wbr)\b', tag):
                depth += 1
            i = j + 1
            start = i
            continue
        i += 1
    if depth == 0 and start < n:
        out.append((start, n))
    return out


def cands(h):
    """מועמדים בשורה: [(מקום ב-HTML, אות, בתחילת שורה, רווח אחרי)]"""
    res = []
    lead = len(re.match(r'^(?:\s|&nbsp;| |(?:<[^>]+>)*)*', h).group(0)) if h else 0
    segs = top_segments(h)
    for m in TOK.finditer(h):
        t = m.group(1)
        pos = m.start(1)
        if not valid(t) or not any(a <= pos and pos + len(t) + 1 <= b for a, b in segs):
            continue
        if True:
            before = H.unescape(re.sub(r'<[^>]+>', '', h[:pos])).rstrip()
            if re.search(r'(?:^|\s)(?:ב?דף|עמוד|לעיל|להלן)$', before) or before.endswith('('):
                continue
            at_start = not before.strip()
            if not at_start and not (before.endswith(',') or before.endswith('،') or h[pos - 1:pos] in (' ', ' ') or h[max(0, pos - 6):pos] == '&nbsp;'):
                continue
            res.append((pos, t, at_start, m.group(2)))
    return res


def plan_unit(u, nb_vals):
    """השורות שישתנו ביחידה: {מספר שורה: html חדש}"""
    if u.get('k') != 'u':
        return {}
    L = u.get('l') or []
    C = [(li, c) for li, (cls, h) in enumerate(L) for c in cands(h or '')]
    vals = {val(c[1]) for _, c in C} | nb_vals
    ok = {}
    for li, c in C:
        v = val(c[1])
        near = (v - 1 in vals) or (v + 1 in vals)
        if near or (c[2] and v <= 9):
            ok.setdefault(li, []).append(c)
    out = {}
    for li, cs in ok.items():
        h = L[li][1]
        for pos, t, st, sp in sorted(cs, key=lambda x: -x[0]):
            end = pos + len(t) + 1
            rest = h[end:]
            # רווח רגיל אחד בדיוק אחרי האות (רשימה סימטרית, פרומפט 60 ה)
            rest = re.sub(r'^(?:\s|&nbsp;| )*', ' ', rest, count=1)
            h = h[:pos] + '<i class="am">' + t + '.</i>' + rest
        if h != L[li][1]:
            out[li] = h
    return out


def unit_vals(u):
    if u.get('k') != 'u':
        return set()
    return {val(c[1]) for cls, h in (u.get('l') or []) for c in cands(h or '')}


def plan_all(D):
    """[(יחידה, מספר שורה (מ-1), לפני, אחרי, דף)]"""
    seq = [(pg.get('daf') or '', u) for pg in D.get('pages', []) for u in pg.get('units', [])]
    V = [unit_vals(u) for _, u in seq]
    res = []
    for i, (daf, u) in enumerate(seq):
        nb = (V[i - 1] if i else set()) | (V[i + 1] if i + 1 < len(seq) else set())
        for li, nh in plan_unit(u, nb).items():
            res.append((u, li + 1, u['l'][li][1], nh, daf))
    return res


def load(site, slug):
    txt = open(os.path.join(site, slug + '.data.js'), encoding='utf-8').read()
    return json.loads(txt[txt.index('{'):txt.rindex('}') + 1])


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--slug', required=True)
    ap.add_argument('--site', required=True)
    ap.add_argument('--examples', type=int, default=5)
    a = ap.parse_args()
    P = plan_all(load(a.site, a.slug))
    print('%s: %d שורות' % (a.slug, len(P)))
    strip = lambda s: H.unescape(re.sub(r'<(?!/?i class="am")[^>]+>', '', s))
    for u, li, b, n, daf in P[:a.examples]:
        print(' ', daf, 'u%s.%s' % (u['id'], li), '|', strip(b)[:90], '=>', strip(n)[:110])
