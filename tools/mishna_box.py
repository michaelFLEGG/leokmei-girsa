# -*- coding: utf-8 -*-
"""mishna_box.py - מספור המשנה ("משנה ג" בפרק ב) לכל יחידת משנה (6.10.2026).

מסגרת הצד "משנה" מחליפה את המילה "מתני'" ונושאת פרק ומשנה באותיות.
המספר נקבע לפי המשנה עצמה: נוסח המשנה (ספריא, tools/fetch_mishna.py)
מושווה לנוסח יחידת המשנה שבוורד, בתוך הפרק שבו היא יושבת, ונבחרת
המשנה שיש בה הרצף הארוך ביותר של מילים משותפות. הבנייה אינה מנחשת:
יחידה שלא עברה את הסף נרשמת ואין לה מספר.

החלוקה היא של הבבלי עצמו: כל יחידת משנה שבגמרא (קטע שנפתח בציטוט משנה)
מקבלת מסגרת, ושתי יחידות של אותה משנה (כשהגמרא חותכת אותה לכמה קטעים)
נושאות אותו מספר. היכן שהבבלי מחלק אחרת מן המשנה המקובלת - זה נספר
ונרשם בבקרה (`split_notes`).

המספור שכבר כתוב בוורד ("משנה ג" בסגנון "משנה בצד") גובר על החישוב.
"""
import re, os, io, json, difflib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
NIKUD = re.compile(r'[֑-ׇ]')
LETTERS = 'אבגדהוזחטיכלמנסעפצקרשת'
GEM = {c: i + 1 for i, c in enumerate('אבגדהוזחט')}
GEM.update({'י': 10, 'כ': 20, 'ל': 30, 'מ': 40, 'נ': 50, 'ס': 60, 'ע': 70, 'פ': 80, 'צ': 90,
            'ק': 100, 'ר': 200, 'ש': 300, 'ת': 400})
MBW = re.compile(r'^\s*משנה\s+([א-ת"׳\'״]{1,4})\s*[.:]?\s*$')


def heb(n):
    """מספר באותיות, בלי גרשיים (ג, יב, טו)."""
    if n == 15:
        return 'טו'
    if n == 16:
        return 'טז'
    out = ''
    for v, c in ((400, 'ת'), (300, 'ש'), (200, 'ר'), (100, 'ק'), (90, 'צ'), (80, 'פ'), (70, 'ע'),
                 (60, 'ס'), (50, 'נ'), (40, 'מ'), (30, 'ל'), (20, 'כ'), (10, 'י'), (9, 'ט'), (8, 'ח'),
                 (7, 'ז'), (6, 'ו'), (5, 'ה'), (4, 'ד'), (3, 'ג'), (2, 'ב'), (1, 'א')):
        while n >= v:
            out += c
            n -= v
    return out


def num(letters):
    t = re.sub(r'["׳\'״]', '', letters or '')
    return sum(GEM.get(c, 0) for c in t)


def skel(w):
    """שלד עיצורי: בלי ניקוד, ובלי י/ו (כתיב מלא וחסר)."""
    w = NIKUD.sub('', w)
    w = re.sub(r'[^א-ת]', '', w)
    return w.replace('י', '').replace('ו', '') or w


def words(text):
    t = re.sub(r'<[^>]+>', ' ', text or '')
    t = t.replace('&nbsp;', ' ').replace('־', ' ').replace('-', ' ').replace('‏', ' ')
    return [x for x in (skel(w) for w in t.split()) if x]


def load(slug):
    p = os.path.join(ROOT, 'data', 'mishna', slug + '.json')
    if not os.path.exists(p):
        return None
    d = json.load(io.open(p, encoding='utf-8'))
    return [[words(m) for m in ch] for ch in d['chapters']]


def _first_text(u):
    """נוסח פתיחת יחידת המשנה: הפסקאות הראשונות שלה, בלי מספר הקטע."""
    ls = u.get('l') or []
    t = ' '.join(re.sub(r'<i class="mk">.*?</i>', '', x[1]) for x in ls[:3])
    return words(t)[:14]


def _best(uw, chap, floor):
    best, bi = 0, None
    for i, mw in enumerate(chap):
        if i < floor:
            continue
        sm = difflib.SequenceMatcher(None, uw, mw, autojunk=False)
        # סכום הקטעים המשותפים (לא הרצף הארוך בלבד): פער של מילה (כמו "את")
        # אינו שובר את ההתאמה
        sc = sum(m.size for m in sm.get_matching_blocks())
        if sc > best:
            best, bi = sc, i
    return best, bi


def _units_of(pages, chap_of):
    """כל יחידות המשנה בסדר, עם מספר הפרק בבבלי (לפי chap_of, או לפי שם הפרק שבעמוד)."""
    out = []
    perek, last = 0, None
    for p in pages:
        pk = (p.get('perek') or '').strip()
        if chap_of is None and pk and pk != last:
            perek += 1
            last = pk
        for u in p['units']:
            if u['k'] != 'm':
                continue
            c = chap_of(u['id']) if chap_of is not None else perek
            out.append((p, u, c))
    return out


def _chapter_map(units, chapters):
    """סדר הפרקים בבבלי אינו תמיד סדר המשנה (מגילה: בבבלי "הקורא עומד" שלישי ו"בני העיר" רביעי).
    לכל פרק בבבלי נבחר פרק המשנה שרוב יחידותיו מתאימות לו בנוסח (הצבעה, לפחות שתיים ולפחות חצי)."""
    votes = {}
    for p, u, c in units:
        uw = _first_text(u)
        if len(uw) < 4:
            continue
        best, bci = 0, None
        for ci, chap in enumerate(chapters):
            sc, bi = _best(uw, chap, 0)
            if bi is not None and sc > best:
                best, bci = sc, ci
        if bci is not None and best >= 4:
            votes.setdefault(c, {}).setdefault(bci, 0)
            votes[c][bci] += 1
    mp = {}
    for c, v in votes.items():
        ci, n = max(v.items(), key=lambda kv: kv[1])
        if n >= 2 and n * 2 >= sum(v.values()):
            mp[c] = ci
    return mp


def assign(pages, slug, chap_of=None, display_by_text=False):
    """מציב על כל יחידת משנה: u['mp'] (פרק בבבלי), u['mb'] (מספר המשנה בפרק), u['mbh'] (איך נקבע),
    u['mbc'] (המספר שחושב מן הנוסח, גם כשבוורד כבר יש מספר). מחזיר דוח. אין מנוחש: מה שלא עבר סף -
    בלי מספר. סתירה בין מספר שבוורד למספר שחושב נרשמת ב-mismatch, והוורד גובר."""
    chapters = load(slug)
    rep = {'units': 0, 'matched': 0, 'from_word': 0, 'unmatched': [], 'no_data': chapters is None,
           'chap_count': len(chapters) if chapters else 0, 'perakim_in_file': 0, 'split_notes': [],
           'mismatch': [], 'order_notes': []}
    units = _units_of(pages, chap_of)
    cmap = _chapter_map(units, chapters) if chapters else {}
    for c, ci in sorted(cmap.items()):
        if ci != c - 1:
            rep['order_notes'].append('פרק %d בבבלי הוא פרק %d במשנה' % (c, ci + 1))
    prev = (0, 0)
    perek = 0
    for p, u, c in units:
        if c != perek:
            perek = c
            prev = (perek, 0)
        rep['units'] += 1
        u['mp'] = perek
        ci = cmap.get(perek, perek - 1)
        if display_by_text:
            # מספור הפרקים בקובץ אינו אמין (כותרות כפולות, חסרות או בלי הדרנים): מספר הפרק המוצג הוא פרק
            # המשנה שנוסחה מתאים (סדר הפרקים בבבלי הוא כסדר המשנה). נרשם בבקרה.
            u['mp'] = ci + 1
        # המספר שנגזר מנוסח המשנה (גם כשבוורד כבר כתוב)
        comp = None
        if chapters is not None and 0 <= ci < len(chapters):
            uw = _first_text(u)
            if len(uw) >= 2:
                floor = prev[1] - 1 if prev[0] == perek and prev[1] > 0 else 0
                sc, bi = _best(uw, chapters[ci], max(0, floor))
                need = min(3, len(uw))
                if bi is None or sc < need:
                    sc, bi = _best(uw, chapters[ci], 0)
                if bi is not None and sc >= need:
                    comp = bi + 1
        u['mbc'] = comp
        w = MBW.match(u.get('mbw') or '')
        if w and num(w.group(1)):
            u['mb'] = num(w.group(1))
            u['mbh'] = 'word'
            rep['from_word'] += 1
            if comp and comp != u['mb']:
                rep['mismatch'].append([next((x.get('daf') for x in [p]), ''), u['id'], u['mb'], comp])
            prev = (perek, u['mb'])
            continue
        if comp is None:
            why = 'אין נתוני משנה לפרק %d' % perek if (chapters is None or not (0 <= ci < len(chapters))) else                 ('יחידה קצרה מדי' if len(_first_text(u)) < 2 else ' '.join(_first_text(u)[:5]))
            rep['unmatched'].append([p.get('daf'), u['id'], why])
            continue
        u['mb'] = comp
        u['mbh'] = 'text'
        rep['matched'] += 1
        if prev[0] == perek and u['mb'] < prev[1]:
            rep['split_notes'].append([p.get('daf'), u['id'], 'המספר חוזר אחורה: %d אחרי %d' % (u['mb'], prev[1])])
        prev = (perek, u['mb'])
    rep['perakim_in_file'] = perek
    return rep


def table(pages):
    """מבנה נתונים לכל משנה (ראשונה בכל מספר): מוכן לתוכן עניינים ולמערכת הלומד.
    {perek, n, daf, id, anchor, name}. אין בנייה של תוכן העניינים עצמו."""
    out, seen = [], set()
    for p in pages:
        name = ''
        for u in p['units']:
            if u['k'] != 'm' or not u.get('mb'):
                continue
            key = (u.get('mp'), u['mb'])
            if key in seen:
                continue
            seen.add(key)
            m = re.search(r'<i class="ns">(.*?)</i>', ' '.join(x[1] for x in u.get('l') or []))
            nm = re.sub(r'<[^>]+>', '', m.group(1)).strip() if m else ''
            out.append({'p': u.get('mp'), 'n': u['mb'], 'daf': (p.get('daf') or '').strip(), 'id': u['id'],
                        'a': 'mn-%d-%d' % (u.get('mp') or 0, u['mb']), 'name': nm})
    return out
