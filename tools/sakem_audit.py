# -*- coding: utf-8 -*-
"""ביקורת קבלות סכם (פרומפט 43, 15.11.2026).

לכל הכרעת סכם שהתקבלה (data/sakem/decisions/*.json, "קבל" או "ערוך"), משווה את מה שבעל הפרויקט אישר
(prop, או final כשערך) למה שיש בפועל באותו מקום בדף כפי שהמנהל רואה אותו (הנתונים אחרי שכבת העריכות):
  שארית    - כותרת צד של orig שאינה ב-prop ונשארה (כשורה רגילה "והך:", או ככותרת בלי שורה), או שורה ישנה שנשארה.
  חסר      - שורה של prop שאינה בדף, ואין בדף שורה דומה לה.
  זרה      - שורה שאינה ב-orig ואינה ב-prop (בדרך כלל עריכה מאוחרת של בעל הפרויקט; לעיון בלבד).
ובנוסף בדיקה כללית לכל מסכת: כותרת צד בלי שורה, ופסקה רגילה שכולה מילת דובר ונקודתיים.

הקלט: קובץ הנתונים של הדף (tools/sakem_audit.py --live <slug>=<json>), כפי ש-D נראה בדף אחרי השכבה.
הפלט: data/sakem/audit/<slug>.json ורשימה מסוכמת.
"""
import argparse, difflib, glob, html, io, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NIK = re.compile(r'[֑-ׇ ⁠]')
LOCK = re.compile(r'^\[(מקור|דף|גמרא|משנה|קבוע|כותרת-נושא|כותרת-דה)(:[^\]]*)?\]$')
STY = re.compile(r'^\((תשובה|רווח|נושא|דה|רקע|נקודה|משנה)\)\s*')


def norm(t):
    t = html.unescape(re.sub(r'<[^>]+>', '', t or ''))
    t = NIK.sub('', t).replace('״', '"').replace("''", '"').replace('׳', "'")
    return re.sub(r'\s+', ' ', t).strip()


def inter_plain(x):
    """שורת ביניים -> טקסט נקי: {סוג:..} נפתח, [מס/תוס'] יורדים"""
    x = re.sub(r"\[(מס|תוס'):[^\]]*\]", '', x)
    x = x.replace('{טאב}', ' ')
    while True:
        y = re.sub(r'\{[^{}:]+:([^{}]*)\}', r'\1', x)
        if y == x:
            break
        x = y
    return norm(x)


def inter_tokens(text):
    out = []
    for raw in (text or '').split('\n'):
        s = raw.strip()
        mh = re.match(r'^\[כותרת-(?:נושא|דה):(.*)\]$', s)
        if mh:
            t = inter_plain(mh.group(1))
            if t:
                out.append(('H', t))
            continue
        if not s or LOCK.match(s):
            continue
        m = re.match(r'^\[צד:(.*)\]$', s)
        if m:
            t = inter_plain(m.group(1))
            if t:
                out.append(('S', t))
            continue
        t = inter_plain(STY.sub('', s))
        if t and t != 'ריק':
            out.append(('L', t))
    return out


def live_tokens(units):
    """רצף הדף: לכל יחידת גמרא/משנה - כותרות הצד שלה ואחריהן השורות"""
    out = []
    for u in units:
        if u['k'] not in ('u', 'm'):
            if u['k'] in ('nose', 'dh'):
                out.append(('H', norm(u.get('a')), u['daf'], u['id'], -1))
            continue
        w = u.get('a') if u['k'] == 'u' else u.get('w')
        for t in re.split(r'<br\s*/?>', w or '', flags=re.I):
            t = norm(t)
            if t:
                out.append(('S', t, u['daf'], u['id'], 0))
        for j, l in enumerate(u.get('l') or []):
            out.append(('L', norm(l[1]), u['daf'], u['id'], j + 1))
    return out


SPEAKER = re.compile(r'^[^ ]{1,14}(?: [^ ]{1,12}){0,3}:$')


def audit(slug, units, decisions):
    T = live_tokens(units)
    by_text = {}
    for i, t in enumerate(T):
        by_text.setdefault((t[0], t[1]), []).append(i)
    found = []
    stats = {'decisions': 0, 'located': 0, 'notfound': 0}
    for fp, d in decisions:
        last = {}
        for e in d.get('log') or []:
            if e.get('act') in ('accept', 'edit') and e.get('orig'):
                last[e['iid']] = e
            elif e.get('iid') in last and e.get('act') in ('undo', 'cancel', 'reject'):
                last.pop(e['iid'], None)
        for iid, e in last.items():
            stats['decisions'] += 1
            appr = e.get('final') or e.get('prop') or ''
            O, A = inter_tokens(e['orig']), inter_tokens(appr)
            Aset, Oset = set(A), set(O)
            pos = []
            for k, t in A:
                if k == 'L' and len(t) >= 8:
                    pos += by_text.get((k, t), [])
            if not pos:
                stats['notfound'] += 1
                continue
            pos.sort()
            # האשכול הגדול ביותר של התאמות רצופות
            best, cur = [pos[0]], [pos[0]]
            for p in pos[1:]:
                if p - cur[-1] <= 25:
                    cur.append(p)
                else:
                    cur = [p]
                if len(cur) > len(best):
                    best = cur[:]
            a, b = max(0, best[0] - 3), min(len(T), best[-1] + 4)
            stats['located'] += 1
            W = T[a:b]
            Wset = {(t[0], t[1]) for t in W}
            Ohead = {t for k, t in O if k == 'S'}
            Ahead = {t for k, t in A if k == 'S'}
            Aall = {t for k, t in A}
            for i in range(a, b):
                k, t, daf, uid, li = T[i]
                if k == 'L' and t in Ohead and t not in Ahead and t not in {x for kk, x in A if kk == 'L'}:
                    found.append({'slug': slug, 'daf': daf, 'type': 'שארית: כותרת צד ישנה כשורה', 'text': t, 'unit': uid, 'li': li,
                                  'dec': os.path.basename(fp), 'iid': iid, 'prev': T[i - 1][1] if i else '', 'next': T[i + 1][1] if i + 1 < len(T) else ''})
                elif k == 'S' and t in Ohead and t not in Ahead and (i + 1 >= len(T) or T[i + 1][0] != 'L' or T[i + 1][3] != uid):
                    found.append({'slug': slug, 'daf': daf, 'type': 'שארית: כותרת צד בלי שורה', 'text': t, 'unit': uid, 'li': li,
                                  'dec': os.path.basename(fp), 'iid': iid})
                elif k == 'L' and (k, t) in Oset and t not in Aall and len(t) >= 8:
                    found.append({'slug': slug, 'daf': daf, 'type': 'שארית: שורה ישנה', 'text': t, 'unit': uid, 'li': li,
                                  'dec': os.path.basename(fp), 'iid': iid})
            Wl = [t[1] for t in W]
            Wt = {t[1] for t in W}
            for k, t in A:
                if k not in ('L', 'H') or len(t) < 6 or t in Wt:
                    continue
                sim = max([difflib.SequenceMatcher(None, t, x).ratio() for x in Wl] or [0])
                if sim < 0.8:
                    found.append({'slug': slug, 'daf': T[best[0]][2], 'type': 'חסר: שורה שאושרה ואינה בדף', 'text': t,
                                  'dec': os.path.basename(fp), 'iid': iid, 'sim': round(sim, 2)})
    # בדיקה כללית
    gen = []
    for i, (k, t, daf, uid, li) in enumerate(T):
        nxt = T[i + 1] if i + 1 < len(T) else None
        if k == 'S' and (not nxt or nxt[3] != uid or nxt[0] != 'L' or not nxt[1]):
            gen.append({'slug': slug, 'daf': daf, 'type': 'כללי: כותרת צד בלי שורה', 'text': t, 'unit': uid})
        if k == 'L' and SPEAKER.match(t) and len(t) <= 26 and (not nxt or nxt[0] == 'S' or nxt[3] != uid):
            gen.append({'slug': slug, 'daf': daf, 'type': 'כללי: שורה שכולה דובר ונקודתיים, בסוף יחידה', 'text': t, 'unit': uid, 'li': li,
                        'next': (nxt[1] if nxt else '')})
    return found, gen, stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--live', action='append', default=[], help='<slug>=<קובץ JSON של יחידות הדף>')
    ap.add_argument('--out', default=os.path.join(ROOT, 'data', 'sakem', 'audit'))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    total = {}
    for spec in a.live:
        slug, fp = spec.split('=', 1)
        units = json.load(io.open(fp, encoding='utf-8'))['units']
        decs = [(f, json.load(io.open(f, encoding='utf-8'))) for f in sorted(glob.glob(os.path.join(ROOT, 'data', 'sakem', 'decisions', slug + '-*.json')))]
        found, gen, st = audit(slug, units, decs)
        doc = {'slug': slug, 'stats': st, 'found': found, 'general': gen}
        io.open(os.path.join(a.out, slug + '.json'), 'w', encoding='utf-8').write(json.dumps(doc, ensure_ascii=False, indent=1))
        c = {}
        for x in found + gen:
            c[x['type']] = c.get(x['type'], 0) + 1
        total[slug] = (st, c)
        print(slug, st, json.dumps(c, ensure_ascii=False))


if __name__ == '__main__':
    main()
