# -*- coding: utf-8 -*-
"""mishna_semantics.py - כללי הסמנטיקה של המשנה בבנייה (מנת מנוע ההדפסה, 14.10.2026, סעיפים ט, י, יא).

חל על האתר ועל ההדפסה (שניהם נבנים מאותן יחידות). כל שינוי מדווח בבקרה, ולעולם אינו שקט:

ט. אחרי כל סוף משנה חובה ד"ה משנה. חסר - נוסף אוטומטית מתוך מילות המשנה (המילים הראשונות של
   הקטע), ומסומן (המחלקה dhauto) כדי שהמנהל יבחין בינו לבין ד"ה שנכתב בוורד.
י. ד"ה משנה זהה (אחרי נרמול ם/ן ואותיות אהו"י) החוזר באותה משנה - הראשון נשאר ד"ה, השני הופך
   לכותרת נושא (הטקסט נשמר, מוסרת רק אות הקטע). אות קטע יורדת שאינה כפילות - מדווחת ואינה משתנה
   (אין דרך בטוחה לדעת לאיזה קטע היא שייכת).
יא. בתוך משנה, שם התנא (ר"א, חכ"א, ר"ג, ב"ש, ב"ה, ר"ט, ת"ק, רי"ה...) בסגנון "תנאי המשנה" (am):
   סגנון תו קיים (tn) על שם תנא מומר; שם ללא סגנון, בתחילת משפט או אחרי פסיק, מקבל את הסגנון;
   מופע באמצע משפט מדווח כמסופק ואינו משתנה.
"""
import re, html

Q = r'(?:&quot;|"|״|״)'
# רשימת ראשי התיבות של תנאים. סגורה במתכוון: ראשי תיבות של אמוראים וקיצורים אחרים אינם נוגעים.
_ABBR = [r'ר%s[אעימשגטחנז]' % Q, r'רי%s[הבחט]' % Q, r'רש%s[אג]' % Q, r'רא%s[בש]' % Q, r'רע%s[קא]' % Q,
         r'ב%s[שה]' % Q, r'ת%s[קר]' % Q, r'חכ%s[אם]' % Q]
NAME = r'(?:%s)' % '|'.join(_ABBR)
# מופע בתחילת משפט: תחילת הפסקה, או אחרי , . ; : ! ? - ( ] [ . קידומת (ו/ל/ד/ש/מ/כ/ב) מותרת.
NAME_RE = re.compile(r'(?<![א-ת])(?P<pre>[ולדשמכב]?)(?P<n>%s)(?P<col>:?)(?=[\s,.;:!?)\]‏-]|$)' % NAME)
_NAME_ONLY = re.compile(r'^\s*[ולדשמכב]?(?:%s):?\s*$' % NAME)
_BOUND = re.compile(r'(?:^|[,.;:!?(\[\]\-–—])\s*$')

_LET = {c: i + 1 for i, c in enumerate('אבגדהוזחטיכלמנסעפצקרשת')}
_FIN = str.maketrans('םןךףץ', 'ממכפצ')
_MK = re.compile(r'^\s*<i class="mk"[^>]*>\s*([א-ת]{1,3})\.?\s*</i>\s*', re.S)
_TAG = re.compile(r'<[^>]+>')
_NIK = re.compile(r'[֑-ׇ]')
_UNIT_LIMIT = 4


def _plain(h):
    return html.unescape(_TAG.sub('', h or '')).replace('‏', '').replace('‎', '')


def _norm(h):
    t = _NIK.sub('', _plain(_MK.sub('', h or '')))
    t = re.sub(r'[^א-ת\s]', '', t).translate(_FIN)
    t = re.sub(r'[אהוי]', '', t)
    return re.sub(r'\s+', ' ', t).strip()


def _letter(h):
    m = _MK.match(h or '')
    return (m.group(1), _LET.get(m.group(1), 0)) if m else (None, 0)


def style_tanaim(htm, stat, doubt, ctx=''):
    """מחזיר את ה-HTML של פסקת משנה עם שמות התנאים בסגנון am."""
    # tn קיים על שם תנא (בלבד) הופך ל-am
    def tn_fix(m):
        if _NAME_ONLY.match(_plain(m.group(2))):
            stat['tn'] = stat.get('tn', 0) + 1
            return '<i class="am">%s</i>' % m.group(2)
        return m.group(0)
    htm = re.sub(r'<i class="(tn)">(.*?)</i>', tn_fix, htm, flags=re.S)
    parts = re.split(r'(<[^>]+>)', htm)
    out = []
    depth = 0
    for k, seg in enumerate(parts):
        if seg.startswith('<'):
            if re.match(r'<(i|b|span|u)\b', seg):
                depth += 1
            elif re.match(r'</(i|b|span|u)>', seg):
                depth = max(0, depth - 1)
            out.append(seg)
            continue
        if depth > 0 or not seg.strip():
            out.append(seg)
            continue
        # טקסט גלוי ללא סגנון: מחפשים שמות תנאים
        pos = 0
        buf = ''
        before_all = ''.join(parts[:k])   # להכרעת תחילת משפט צריך גם את מה שלפני הקטע
        prev_visible = html.unescape(_TAG.sub('', before_all))
        for m in NAME_RE.finditer(seg):
            pre_txt = prev_visible + html.unescape(seg[:m.start()])
            # הקידומת (ו/ל...) שייכת למילה; תחילת משפט נבדקת לפניה
            boundary = (not pre_txt.strip()) or bool(_BOUND.search(pre_txt))
            if boundary:
                buf += seg[pos:m.start()] + '<i class="am">' + m.group(0) + '</i>'
                stat['new'] = stat.get('new', 0) + 1
            else:
                doubt.append((ctx, html.unescape(m.group(0)), _plain(seg)[max(0, m.start() - 12):m.end() + 12]))
                buf += seg[pos:m.start()] + m.group(0)
            pos = m.end()
        buf += seg[pos:]
        out.append(buf)
    return ''.join(out)


def _first_words(u, n=_UNIT_LIMIT):
    """המילים הראשונות של המשנה, בלי שם התנא שבפתח הפסקה."""
    for ln in u.get('l', []):
        t = _plain(ln[1]).strip()
        t = re.sub(r'^[ולדשמכב]?(?:%s):?\s*' % NAME, '', t)
        t = _NIK.sub('', t)
        w = []
        for tok in t.split():
            w.append(tok)
            if re.search(r'[,.:;!?]$', tok) or len(w) >= n:
                break
        txt = ' '.join(w).rstrip(',.:;!?- ')
        if len(txt) >= 3:
            return txt
    return ''


def apply(pages, toc, qa):
    st = {'tn': 0, 'new': 0, 'dh_added': 0, 'dh_dup': 0, 'letter_down': 0}
    doubt = []
    desc = []
    # יא: סגנון תנאי המשנה בכל פסקאות המשנה
    for pg in pages:
        for u in pg['units']:
            if u.get('k') != 'm':
                continue
            for ln in u['l']:
                if ln[0] == 'hatz':
                    continue
                ln[1] = style_tanaim(ln[1], st, doubt, '%s %s' % (pg.get('daf', ''), u.get('id')))
    # ט, י: לכל משנה - ד"ה שאחריה
    flat = [(pg, u) for pg in pages for u in pg['units']]
    n_syn = 0
    i = 0
    ins = []
    while i < len(flat):
        pg, u = flat[i]
        if u.get('k') != 'm':
            i += 1
            continue
        j = i + 1
        seen = {}
        last_letter = 0
        has_dh = False
        # עד המשנה הבאה, פתיחת הפרק הבא או סיום המסכת
        while j < len(flat) and flat[j][1].get('k') not in ('m', 'perek-start', 'perek-num', 'perek-range', 'hadran'):
            q = flat[j][1]
            if q.get('k') == 'dh':
                has_dh = True
                ltr, num = _letter(q.get('a', ''))
                key = _norm(q.get('a', ''))
                if key and key in seen:
                    # י1: אותו דיבור באותה משנה - כותרת נושא (הטקסט נשמר)
                    q['k'] = 'nose'
                    q['a'] = _MK.sub('', q['a'])
                    q['s'] = (q.get('s', '') + ' dhdup').strip()
                    for e in toc:
                        if len(e) > 3 and e[1] == q.get('id'):
                            e[3] = 'nose'
                    st['dh_dup'] += 1
                else:
                    seen[key] = 1
                    if num and last_letter and num < last_letter:
                        st['letter_down'] += 1
                        desc.append((flat[j][0].get('daf', ''), q.get('id'), ltr, _plain(q.get('a', ''))[:30]))
                    if num:
                        last_letter = max(last_letter, num)
            j += 1
        # ט: משנה שאין אחריה ד"ה (אחרי כותרות נושא/חציצה בלבד, ולפני גוף הגמרא)
        k = i + 1
        while k < len(flat) and flat[k][1].get('k') in ('nose', 'hatz'):
            k += 1
        nxt = flat[k][1] if k < len(flat) else None
        if (not has_dh and nxt is not None and nxt.get('k') == 'u') or \
           (has_dh is False and nxt is not None and nxt.get('k') in ('nose',) and False):
            w = _first_words(u)
            if w:
                n_syn += 1
                nu = {'k': 'dh', 'a': '<i class="mk">א. </i>' + html.escape(w, quote=False) + ' ', 'l': [],
                      'id': 700000 + n_syn, 's': 'b1 a0 dhauto', 'syn': 1}
                ins.append((pg, u, nu))
                st['dh_added'] += 1
        i = j if j > i else i + 1
    for pg, after, nu in ins:
        pg['units'].insert([id(x) for x in pg['units']].index(id(after)) + 1, nu)
    if st['tn'] or st['new']:
        qa.append(('טופל בתצוגה: תנאי המשנה',
                   '%d שמות תנאים בסגנון "תו" הומרו לסגנון "תנאי המשנה", ו-%d שמות שלא סומנו קיבלו את הסגנון '
                   '(בתחילת משפט או אחרי פסיק). %d מופעים באמצע משפט לא שונו (מסופקים)'
                   % (st['tn'], st['new'], len(doubt))))
    if doubt:
        qa.append(('תנאי המשנה: מסופקים', '; '.join('%s: %s (...%s...)' % d for d in doubt[:12])))
    if st['dh_added']:
        qa.append(('טופל בתצוגה: ד"ה משנה שנוסף',
                   '%d משניות שאין אחריהן ד"ה קיבלו ד"ה אוטומטי מתוך מילות המשנה (מסומן בנקודות)' % st['dh_added']))
    if st['dh_dup']:
        qa.append(('טופל בתצוגה: ד"ה משנה כפול',
                   '%d ד"ה משנה זהים באותה משנה הוצגו ככותרת נושא (הטקסט נשמר)' % st['dh_dup']))
    if desc:
        qa.append(('ד"ה משנה: אות קטע יורדת',
                   '%d אותיות קטע יורדות שאינן כפילות (לא שונו): ' % len(desc) +
                   '; '.join('%s #%s %s %s' % d for d in desc[:12])))
    return st


_GV = {'א': 1, 'ב': 2, 'ג': 3, 'ד': 4, 'ה': 5, 'ו': 6, 'ז': 7, 'ח': 8, 'ט': 9, 'י': 10, 'כ': 20, 'ך': 20, 'ל': 30,
       'מ': 40, 'ם': 40, 'נ': 50, 'ן': 50, 'ס': 60, 'ע': 70, 'פ': 80, 'ף': 80, 'צ': 90, 'ץ': 90, 'ק': 100,
       'ר': 200, 'ש': 300, 'ת': 400}


def daf_value(d):
    """ציון דף (למשל 'יא:') -> מספר חצאי דף, או None."""
    m = re.match(r"^\s*([א-ת\"׳״']+)\s*([.:])\s*$", d or '')
    if not m:
        return None
    n = sum(_GV.get(c, 0) for c in m.group(1))
    return 2 * n + (1 if m.group(2) == ':' else 0)


def check_daf_order(pages, qa):
    """טז (14.10.2026): ציוני דף שאינם עוקבים (למשל 'יב.' אחרי 'יא.' ואחריו 'יב:' ושוב 'יא.') - מדווח, אינו משתנה.
    ציון שגוי מונע הדפסת טווח ("עד יא:") ומטעה את התוכן והקישורים."""
    prev = None
    bad = []
    for i, pg in enumerate(pages):
        if not pg.get('units'):
            continue
        v = daf_value(pg.get('daf'))
        if v is None:
            continue
        if prev is not None and v not in (prev[0], prev[0] + 1) and not (v > prev[0] and pg.get('label')):
            bad.append('%s אחרי %s' % (pg.get('daf'), prev[1]))
        prev = (v, pg.get('daf'))
    if bad:
        qa.append(('ציוני דף שאינם עוקבים',
                   '%d מקומות: %s%s' % (len(bad), '; '.join(bad[:12]), ' ...' if len(bad) > 12 else '')))
    return bad
