# -*- coding: utf-8 -*-
"""mishna_numbers.py - מספור קטעי המשנה באותיות (6.10.2026).

פירוש הגמרא (ספריא, Steinsaltz) ממספר את הקטעים של כל סוגיה באותיות
(א, ב, ג...), ואת הקטעים שמפרשים את המשנה עצמה הוא מסמן גם במילה
"משנה". הכלי הזה מעתיק את המספרים האלה אל האתר, ואינו ממספר מחדש
כלל: האות היא האות שבפירוש.

מבנה הפירוש: כל מקטע (שורה ב-perush) ש"נפתח" בתווית <b>א</b> או
<b>ב גמרא</b> או <b>ג משנה</b> פותח קטע חדש; מקטעים שאחריו, בלי תווית,
שייכים אליו - גם אם הם בדף הבא. לכן "האות של מקטע" היא האות של
התווית האחרונה שעד אליו (בסדר הקריאה).

הצמדה לאתר:
א. ד"ה משנה: האות של המקטע שבו הוא נמצא. מקטע הגמרא נקבע לפי ה-ref של
   היחידה (match_sources), ובהעדרו לפי ה-ref של היחידה הבאה אחריו בדף;
   ובהעדרו - התאמת מילים מול הטקסט המודגש בפירוש, באותו דף.
ב. קטע שמסומן "משנה" בפירוש ואין לו ד"ה באתר: האות נתלית ביחידה
   שהיא ה-ref שלו (בדרך כלל יחידת המשנה עצמה).

כל מה שלא הותאם נרשם בדוח, ואינו מנוחש.
"""
import re, io, os, json, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import match_sources as MS

# תווית אמיתית: אות או שתיים שהן מספר תקין (א-כ, כולל טו וטז), ואחריה רווח.
# "ו" או "ב" מודגשות שהן אות היחס של מילה מצוטטת אינן תווית: אחריהן אין רווח.
NUMERAL = r'(?:[א-ט]|י[א-טח]?|כ)'
LABEL = re.compile(r'^\s*<b>(%s)(?:\s+(משנה|גמרא))?</b>(?=\s|$)' % NUMERAL)
LETTERS = 'אבגדהוזחטיכלמנסעפצקרשת'
GEM = {c: i + 1 for i, c in enumerate('אבגדהוזחט')}
GEM.update({'י': 10, 'כ': 20, 'ל': 30, 'מ': 40, 'נ': 50, 'ס': 60, 'ע': 70, 'פ': 80, 'צ': 90,
            'ק': 100, 'ר': 200, 'ש': 300, 'ת': 400})


def num_of(letters):
    return sum(GEM.get(c, 0) for c in letters)


def parse_segments(src):
    """רשימת כל מקטעי הפירוש בסדר הקריאה: daf, seg, ref, label, kind, letter."""
    out = []
    pages = src.get('pages') or {}
    for k, p in pages.items():
        per = p.get('perush') or []
        refs = p.get('refs') or []
        for i, s in enumerate(per):
            m = LABEL.match(s or '')
            out.append({'daf': k.strip(), 'seg': i,
                        'ref': refs[i] if i < len(refs) else '',
                        'label': m.group(1) if m else '',
                        'kind': (m.group(2) or '') if m else '',
                        'text': s or ''})
    cur = ''
    for x in out:
        if x['label']:
            cur = x['label']
        x['letter'] = cur
    return out


def _bold_words(s):
    """המילים המודגשות בפירוש (ציטוט הגמרא והמשנה), מנורמלות."""
    t = ' '.join(re.findall(r'<b>(.*?)</b>', LABEL.sub('', s, count=1), re.S))
    return MS.norm(t).split()


def _dh_words(a):
    t = MS.norm(a)
    t = re.sub(r'\bוכו\b', ' ', t)
    return [w for w in t.split() if w]


def _contains_seq(hay, needle):
    """needle (רשימת מילים) מופיעה ברצף (עם דילוגים קטנים) ב-hay."""
    if not needle:
        return False
    i = 0
    miss = 0
    for w in hay:
        if w == needle[i]:
            i += 1
            miss = 0
            if i == len(needle):
                return True
        else:
            miss += 1
            if i and miss > 3:
                i = 1 if w == needle[0] else 0
                miss = 0
    return False


def _prev_daf(d):
    """הדף שלפני d (ג. -> ב:, ב: -> ב.)."""
    t = d.strip()
    if t.endswith(':'):
        return t.rstrip(':') + '.'
    core = t.rstrip('.:')
    n = num_of(core.replace('"', '').replace("'", ''))
    if n <= 2:
        return ''
    n -= 1
    out = ''
    rem = n
    for v, c in ((400, 'ת'), (300, 'ש'), (200, 'ר'), (100, 'ק'), (90, 'צ'), (80, 'פ'), (70, 'ע'),
                 (60, 'ס'), (50, 'נ'), (40, 'מ'), (30, 'ל'), (20, 'כ'), (10, 'י'), (9, 'ט'), (8, 'ח'),
                 (7, 'ז'), (6, 'ו'), (5, 'ה'), (4, 'ד'), (3, 'ג'), (2, 'ב'), (1, 'א')):
        while rem >= v:
            if rem == 15:
                out += 'טו'; rem = 0
                break
            if rem == 16:
                out += 'טז'; rem = 0
                break
            out += c
            rem -= v
    return out + ':'


def _next_daf(d):
    """הדף שאחרי d (ב. -> ב:, ב: -> ג.), לפי מספר הדף בגימטריה."""
    t = d.strip()
    am = t.endswith(':')
    core = t.rstrip('.:')
    n = num_of(core.replace('"', '').replace("'", ''))
    if not n:
        return ''
    if not am:
        return core + ':'
    n += 1
    out = ''
    for v, c in ((400, 'ת'), (300, 'ש'), (200, 'ר'), (100, 'ק'), (90, 'צ'), (80, 'פ'), (70, 'ע'),
                 (60, 'ס'), (50, 'נ'), (40, 'מ'), (30, 'ל'), (20, 'כ'), (10, 'י'), (9, 'ט'), (8, 'ח'),
                 (7, 'ז'), (6, 'ו'), (5, 'ה'), (4, 'ד'), (3, 'ג'), (2, 'ב'), (1, 'א')):
        while n >= v:
            if n == 15:
                out += 'טו'; n = 0
                break
            if n == 16:
                out += 'טז'; n = 0
                break
            out += c
            n -= v
    return out + '.'


NIKUD = re.compile(r'[֑-ׇ]')


def _skel(t):
    """מילים בשלד עיצורי (בלי ניקוד, בלי י/ו, בלי אות יחס בראש מילה ארוכה): להתאמה רפה."""
    t = re.sub(r'<[^>]+>', ' ', t or '')
    t = NIKUD.sub('', t).replace('־', ' ')
    t = re.sub(r"[^א-ת\s]", ' ', t)
    out = []
    for w in t.split():
        w = w.replace('י', '').replace('ו', '') or w
        if len(w) > 3 and w[0] in 'הבלמשכד':
            w = w[1:]
        out.append(w)
    return out


def _ratio(a, b):
    """סכום הקטעים המשותפים (לפי סדר) חלקי אורך הקצר מבין השניים."""
    import difflib
    if not a or not b:
        return 0.0
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    return sum(m.size for m in sm.get_matching_blocks()) / float(min(len(a), len(b)))


def _has_mn(u):
    """הטקסט הראשון של היחידה כבר נפתח בסגנון התו "מספר קטע" (בא מן הוורד)."""
    h = (u.get('a') if u.get('k') == 'dh' else ((u.get('l') or [['', '']])[0][1])) or ''
    return h.lstrip().startswith('<i class="mk">')


def _wl(u):
    """אות הקטע שכתובה בוורד בתחילת היחידה (סגנון "מספר קטע"), או ''."""
    h = (u.get('a') if u.get('k') == 'dh' else ((u.get('l') or [['', '']])[0][1])) or ''
    m = re.match(r'\s*<i class="mk">([^<]*)</i>', h)
    return m.group(1).strip().rstrip('.').strip() if m else ''


def assign(pages, src, masechet=''):
    """מציב u['mn'] (האות) על ד"ה משנה ועל יחידות המשנה. מחזיר דוח."""
    segs = parse_segments(src)
    by_ref = {x['ref']: x for x in segs if x['ref']}
    by_daf = {}
    for x in segs:
        by_daf.setdefault(x['daf'], []).append(x)
    rep = {'seg_letters': {x['ref']: x['letter'] for x in segs if x['kind'] == 'משנה' and x['ref']},
           'dh': 0, 'dh_ref': 0, 'dh_words': 0, 'dh_none': 0, 'm_labeled': 0, 'm_placed': 0,
           'm_missing': [], 'dh_unmatched': [], 'jumps': [], 'dups': [], 'total_segs': len(segs),
           'no_perush_pages': 0}
    used = set()
    for pi, p in enumerate(pages):
        us = p['units']
        daf = (p.get('daf') or '').strip()
        # רצף המקטעים של הדף: הדף הנוכחי תחילה, ואחריו מילים בלבד באותו דף
        cand = by_daf.get(daf, [])
        last_idx = -1
        for ui, u in enumerate(us):
            if u['k'] != 'dh':
                continue
            rep['dh'] += 1
            if _has_mn(u):          # המספר כבר בוורד, כסגנון התו "מספר קטע"
                rep['dh_in_word'] = rep.get('dh_in_word', 0) + 1
                continue
            seg = None
            # ref של היחידה, או של הבאה אחריה
            for v in [u] + us[ui + 1:ui + 4]:
                r = v.get('ref')
                if r and r in by_ref:
                    seg = by_ref[r]
                    how = 'ref'
                    break
            if seg is None:
                dw = _dh_words(u.get('a'))
                hit = None
                for x in cand:
                    if x['seg'] < last_idx:
                        continue
                    if _contains_seq(_bold_words(x['text']) or MS.norm(x['text']).split(), dw):
                        hit = x
                        break
                if hit:
                    seg, how = hit, 'words'
            if seg is None:
                # שלב שלישי: התאמה רפה בשלד עיצורי מול הציטוט המודגש ומול נוסח הגמרא של
                # הקטע, בדף ובשכנים. אות היחס, י/ו, ניקוד וגרשיים אינם שוברים אותה.
                dwk = _skel(re.sub(r"וכו[׳']?", ' ', u.get('a') or ''))
                if dwk:
                    spg = (src.get('pages') or {}).get(daf) or {}
                    best, hit = 0.0, None
                    for dd in (daf, _prev_daf(daf), _next_daf(daf)):
                        for x in by_daf.get(dd, []):
                            if not x['letter']:
                                continue
                            gtxt = ((src.get('pages') or {}).get(dd) or {}).get('gemara') or []
                            cands = [_skel(' '.join(re.findall(r'<b>(.*?)</b>', LABEL.sub('', x['text'], count=1), re.S)))]
                            if x['seg'] < len(gtxt):
                                cands.append(_skel(gtxt[x['seg']]))
                            for cw in cands:
                                r = _ratio(dwk[:8], cw[:14])
                                if r > best:
                                    best, hit = r, x
                    need = 0.65 if len(dwk) >= 3 else 0.99
                    if hit is not None and best >= need:
                        seg, how = hit, 'fuzzy'
                        u['mnr'] = round(best, 2)
            if seg is None or not seg['letter']:
                rep['dh_none'] += 1
                if len(rep['dh_unmatched']) < 400:
                    import html as _h
                    _nx = us[ui + 1] if ui + 1 < len(us) else None
                    _nt = ''
                    if _nx is not None:
                        _nt = _h.unescape(re.sub(r'<[^>]+>', '', (_nx.get('a') if _nx['k'] != 'u' and _nx.get('a') and not _nx.get('l') else ((_nx.get('l') or [['', '']])[0][1])) or ''))
                    rep['dh_unmatched'].append([daf, u['id'], MS.norm(u.get('a'))[:40],
                                                _h.unescape(re.sub(r'<[^>]+>', '', u.get('a') or '')), _nt])
                continue
            last_idx = seg['seg'] if seg['daf'] == daf else last_idx
            u['mn'] = seg['letter']
            u['mns'] = [seg['daf'], seg['seg']]
            u['mnh'] = how
            rep['dh_' + how] = rep.get('dh_' + how, 0) + 1
            used.add((seg['daf'], seg['seg']))
    # קטעי משנה שמסומנים כך בפירוש: יחידת המשנה (u.k == 'm') באותו דף
    # שמילותיה הן הציטוט המודגש של הקטע. ה-ref של יחידת משנה אינו אמין
    # (הוא עלול להיתפס במקטע שכן), ולכן ההצמדה כאן במילים.
    page_of = {}
    for p in pages:
        page_of.setdefault((p.get('daf') or '').strip(), []).append(p)
    taken = set()
    for x in segs:
        if x['kind'] != 'משנה':
            continue
        rep['m_labeled'] += 1
        qw = set(_bold_words(x['text']))
        best, bu = 0.0, None
        for p in page_of.get(x['daf'], []):
            for u in p['units']:
                if u['k'] != 'm' or id(u) in taken:
                    continue
                uw = set(MS.norm(' '.join(l[1] for l in u['l'])).split())
                if not uw or not qw:
                    continue
                sc = len(uw & qw) / float(len(uw))
                if sc > best:
                    best, bu = sc, u
        if bu is not None and best >= 0.3:
            taken.add(id(bu))
            if _has_mn(bu):
                rep['m_in_word'] = rep.get('m_in_word', 0) + 1
            else:
                bu['mn'] = x['letter']
                bu['mnh'] = 'm'
            rep['m_placed'] += 1
            continue
        # אין יחידת משנה מתאימה: הפסקה שבה מתחיל הדיון בקטע, לפי ה-ref
        tgt = None
        for p in page_of.get(x['daf'], []) + page_of.get(_next_daf(x['daf']), []):
            for u in p['units']:
                if (u.get('ref') == x['ref'] and u['k'] in ('u', 'm') and not u.get('mn')
                        and id(u) not in taken and not _has_mn(u)):
                    tgt = u
                    break
            if tgt:
                break
        if tgt is not None:
            tgt['mn'] = x['letter']
            tgt['mnh'] = 'r'
            taken.add(id(tgt))
            rep['m_placed_ref'] = rep.get('m_placed_ref', 0) + 1
        else:
            # שלב רפה: נוסח הגמרא של הקטע מול פתיחת כל יחידת משנה בדף ובשכנים
            gtxt = ((src.get('pages') or {}).get(x['daf']) or {}).get('gemara') or []
            gw = _skel(gtxt[x['seg']] if x['seg'] < len(gtxt) else '')[:12]
            fb, fu = 0.0, None
            for dd in (x['daf'], _prev_daf(x['daf']), _next_daf(x['daf'])):
                for p in page_of.get(dd, []):
                    for u in p['units']:
                        if u['k'] != 'm' or id(u) in taken or u.get('mn'):
                            continue
                        if _has_mn(u) and _wl(u) != x['letter']:
                            continue
                        uw = _skel(' '.join(l[1] for l in (u.get('l') or [])[:2]))[:12]
                        r = _ratio(gw, uw)
                        if r > fb:
                            fb, fu = r, u
            if fu is not None and fb >= 0.65:
                taken.add(id(fu))
                if _has_mn(fu):
                    rep['m_in_word'] = rep.get('m_in_word', 0) + 1     # כבר ממוספרת בוורד באותה אות
                else:
                    fu['mn'] = x['letter']
                    fu['mnh'] = 'fuzzy'
                    fu['mnr'] = round(fb, 2)
                    fu['mns'] = [x['daf'], x['seg']]
                    rep['m_fuzzy'] = rep.get('m_fuzzy', 0) + 1
            else:
                rep['m_missing'].append([x['daf'], x['seg'], x['letter'], round(max(best, fb), 2)])
    # רציפות הסימון של פירוש הגמרא עצמו
    prev = None
    for x in segs:
        if not x['label']:
            continue
        n = num_of(x['label'])
        if prev is not None and n != 1:
            if n == prev:
                rep['dups'].append([x['daf'], x['seg'], x['label']])
            elif n != prev + 1:
                rep['jumps'].append([x['daf'], x['seg'], x['label'], 'אחרי %s' % LETTERS[prev - 1] if 0 < prev <= len(LETTERS) else prev])
        prev = n
    return rep
