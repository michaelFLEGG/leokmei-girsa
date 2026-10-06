# -*- coding: utf-8 -*-
"""dh_missing.py - איתור ד"ה משנה חסרים (6.10.2026, חלק א).

פירוש הגמרא (ספריא) מסמן כל קטע שמפרש את המשנה במילה "משנה" ("ב משנה").
באתר ובוורד כל קטע כזה נפתח בד"ה משנה (כותרת המצטטת את פתיחת הקטע) או
ביחידת משנה. כאן נאתר קטעים שפתיחתם חסרה, ונציע ד"ה: מילות הפתיחה של
הקטע כפי שהן בגמרא, קצר, עם וכו' כשנחתך.

הכלל שמעלה הצעה (כולן חייבות להתקיים, ובספק - אין הצעה אלא רישום בדוח):
א. הקטע מסומן "משנה" בפירוש הגמרא, ויש לו מספר (אות).
ב. אין ד"ה ואין יחידת משנה באתר שדומים לפתיחת הקטע (חפיפת מילים).
ג. יש בוורד יחידת גוף שהוצמדה (ref) לאחד ממקטעי הגמרא שבתחום הקטע,
   והיחידה שלפניה אינה ד"ה, אינה יחידת משנה ואינה כותרת נושא.
ד. הפתיחה (בגמרא) כוללת לפחות שלוש מילים.
"""
import re, html, difflib, collections
import match_sources as MS
import mishna_numbers as MN

NIKUD = re.compile(r'[֑-ׇ]')


def _skel_words(t):
    t = re.sub(r'<[^>]+>', ' ', t or '')
    t = NIKUD.sub('', t)
    t = re.sub(r"[^א-ת\s]", ' ', t.replace('־', ' '))
    out = []
    for w in t.split():
        w = w.replace('י', '').replace('ו', '') or w
        out.append(w)
    return out


def _ratio(a, b):
    if not a or not b:
        return 0.0
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    return sum(m.size for m in sm.get_matching_blocks()) / float(min(len(a), len(b)))


def _plain_words(t):
    t = re.sub(r'<[^>]+>', ' ', t or '')
    t = NIKUD.sub('', t)
    t = t.replace('־', ' ')
    return [w for w in re.sub(r'[^א-ת"\'׳״\s]', ' ', t).split() if w]


def dh_text(gemara, maxw=6):
    """פתיחת הקטע כדיבור המתחיל: מילות הפתיחה בלי "מתני׳"/"גמ׳", עם וכו' כשנחתך."""
    ws = _plain_words(gemara)
    while ws and ws[0] in ('מתני׳', "מתני'", 'מתניתין', 'גמ׳', "גמ'", 'מתני'):
        ws = ws[1:]
    if len(ws) < 3:
        return None
    head = ws[:maxw]
    txt = ' '.join(head)
    txt = re.sub(r'[,:;.\-–—]+$', '', txt)
    if len(ws) > maxw:
        txt += " וכו'"
    return txt


def analyze(pages, src):
    spages = src.get('pages') or {}
    segs = MN.parse_segments(src)
    flat = []
    for pi, p in enumerate(pages):
        for ui, u in enumerate(p['units']):
            flat.append((pi, ui, u))
    pos_of_ref = collections.defaultdict(list)
    for k, (_, _, u) in enumerate(flat):
        if u.get('ref'):
            pos_of_ref[u['ref']].append(k)
    daf_units = collections.defaultdict(list)
    for k, (pi, _, u) in enumerate(flat):
        if u['k'] in ('dh', 'm'):
            daf_units[(pages[pi].get('daf') or '').strip()].append(k)
    dafs = [(p.get('daf') or '').strip() for p in pages]
    rep = {'labeled': 0, 'present': 0, 'no_content': 0, 'adjacent': 0, 'proposed': 0, 'short': 0}
    props, skipped = [], []
    # תחום כל קטע: מן הקטע עד התווית הבאה (לפי סדר הקריאה)
    for si, S in enumerate(segs):
        if S['kind'] != 'משנה' or not S['letter']:
            continue
        rep['labeled'] += 1
        sp = spages.get(S['daf'])
        if not sp or S['seg'] >= len(sp['gemara']):
            continue
        g = sp['gemara'][S['seg']]
        gw = _skel_words(g)
        gw = [w for w in gw if w not in ('מתני', 'גמ')][:10]
        # א. נוכחות: ד"ה או משנה דומים בדף, בקודם ובבא אחריו
        near = []
        if S['daf'] in dafs:
            di = dafs.index(S['daf'])
            for d in dafs[max(0, di - 1):di + 2]:
                near += daf_units.get(d, [])
        best = 0.0
        for k in set(near):
            u = flat[k][2]
            uw = _skel_words(u.get('a') if u['k'] == 'dh' else ' '.join(x[1] for x in (u.get('l') or [])[:2]))[:10]
            best = max(best, _ratio(gw[:8], uw[:8]))
        if best >= 0.6:
            rep['present'] += 1
            continue
        # ב. תחום הקטע: הרפים של מקטעי הגמרא עד התווית הבאה
        refs = []
        for x in segs[si:si + 400]:
            if x is not S and x['label']:
                break
            if x['ref']:
                refs.append(x['ref'])
        ks = sorted(k for r in refs for k in pos_of_ref.get(r, []))
        if not ks:
            rep['no_content'] += 1
            skipped.append([S['daf'], S['seg'], S['letter'], 'אין בוורד יחידה שהוצמדה לתחום הקטע'])
            continue
        f = ks[0]
        pi, ui, u = flat[f]
        if u['k'] != 'u':
            rep['adjacent'] += 1
            skipped.append([S['daf'], S['seg'], S['letter'], 'היחידה הראשונה בתחום אינה יחידת גוף (%s)' % u['k']])
            continue
        ftxt = html.unescape(re.sub(r'<[^>]+>', '', ((u.get('l') or [['', '']])[0][1])))
        ftxt = re.sub(r'^[א-ת]{1,2}\. ', '', NIKUD.sub('', ftxt)).strip()
        if re.match(r"^(מתני[׳'’]?|מתניתין|משנה)\s*[.:]?$", ftxt) or any(flat[g][2]['k'] == 'm' for g in range(f, min(f + 3, len(flat)))):
            rep['adjacent'] += 1
            skipped.append([S['daf'], S['seg'], S['letter'], 'יחידת המשנה עצמה יושבת בראש התחום'])
            continue
        prev = flat[f - 1][2] if f > 0 else None
        if prev is not None and prev['k'] in ('dh', 'm', 'nose'):
            rep['adjacent'] += 1
            skipped.append([S['daf'], S['seg'], S['letter'], 'לפני היחידה כבר יושבת כותרת (%s)' % prev['k']])
            continue
        txt = dh_text(g)
        if not txt:
            rep['short'] += 1
            skipped.append([S['daf'], S['seg'], S['letter'], 'פתיחת הקטע קצרה משלוש מילים'])
            continue
        p = pages[pi]
        first = (u.get('l') or [['', '']])[0][1]
        nxt = (u.get('l') or [['', ''], ['', '']])[1][1] if len(u.get('l') or []) > 1 else ''
        props.append({'daf': (p.get('daf') or '').strip(), 'seg_daf': S['daf'], 'seg': S['seg'], 'letter': S['letter'],
                      'dh': txt, 'before_id': u['id'],
                      'text': html.unescape(re.sub(r'<[^>]+>', '', first)), 'next': html.unescape(re.sub(r'<[^>]+>', '', nxt))})
        rep['proposed'] += 1
    return {'report': rep, 'proposals': props, 'skipped': skipped}
