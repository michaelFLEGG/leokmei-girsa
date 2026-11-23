# -*- coding: utf-8 -*-
"""dh_nikud.py - ניקוד ד"ה משנה (פרומפט 80 א, 23.11.2026).

כל ד"ה משנה (יחידה k='dh') מנוקד בשכבה נפרדת u['av'], בדיוק כמו שכבת הניקוד של המשנה (u['lv']):
נוסח הוורד (u['a']) אינו משתנה, ואליו חוזרים במצב עריכה ובחיפוש.

מקור הניקוד, לפי הסדר:
  א. המשנה עצמה - data/mishna/<מסכת>.json (משניות ספריא, Torat Emet). מילות הד"ה מיושרות לרצף המילים
     של המשנה: קודם המשנה שהד"ה שייך לה (לפי טבלת המשניות), ואם אין שם התאמה טובה - כל משניות הפרק,
     ואחר כך כל המסכת. מילה מקבלת ניקוד רק כשאותיותיה זהות לזו שמולה, או כשההבדל הוא כתיב מלא/חסר
     בלבד (nikud_mishna.transfer). לא מנקדים מן הזיכרון.
  ב. מילה שאינה במשנה - ניקוד המנקד (דיקטה), מן המטמון data/nikud-dh/<מסכת>.json שנבנה ב-tools/dh_nikud_fill.py.
     כל מילה כזאת עטופה ב-span.nks (קו תחתי אפור למנהל בלבד), לבדיקה.
  ג. מה שנשאר - בלי ניקוד (ראשי תיבות, קיצורים, אות מספור).

רק החלק של מילות המשנה מנוקד: מה שאחרי מקף מפריד (" - נושא") הוא כותרת של בעל הפרויקט ואינו נוגע.
"""
import io, json, os, re, difflib

from nikud_mishna import WORD, NIKUD, TAGS, letters, skel, transfer, has_nikud

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUOTE_TAIL = re.compile(r'(&quot;|&#x27;|&#39;|&apos;|["\'׳״])$')
QUOTE_HEAD = re.compile(r'^(&quot;|&#x27;|&#39;|&apos;|["\'׳״])')
SEP = re.compile(r'(?<=[^\s-])\s*[-–‐](?:\s|$)|^\s*[-–‐]\s')


def _tokens(h):
    out, i = [], 0
    for m in TAGS.finditer(h or ''):
        if m.start() > i:
            out.append(['txt', h[i:m.start()]])
        out.append(['tag', m.group(0)])
        i = m.end()
    if i < len(h or ''):
        out.append(['txt', h[i:]])
    return out


def mishna_part(h):
    """הטווח (במונחי מיקום בטקסט הגלוי, אחרי הסרת תגיות) של מילות המשנה: עד המקף המפריד הראשון."""
    plain = TAGS.sub('', h or '')
    m = SEP.search(plain)
    return len(plain) if not m else m.start()


def dh_words(h):
    """המילים שמותר לנקד בד"ה: (אינדקס-טוקן, התחלה, סוף, מילה). בלי אות מספור, בלי ראשי תיבות, בלי סוגריים, ורק
    בחלק המשנה (לפני המקף)."""
    lim = mishna_part(h)
    out, pos, depth_par, depth_sq = [], 0, 0, 0
    for ti, (kind, s) in enumerate(_tokens(h)):
        if kind != 'txt':
            continue
        for m in WORD.finditer(s):
            gpos = pos + m.start()
            if gpos >= lim:
                break
            w = m.group(0)
            pre, post = s[:m.start()], s[m.end():]
            # סוגריים: ציון מקור - לא מנקדים
            before = TAGS.sub('', h)[:gpos]
            if before.count('(') > before.count(')') or before.count('[') > before.count(']'):
                continue
            if has_nikud(w) or len(letters(w)) < 2:
                continue
            if QUOTE_TAIL.search(pre) and not pre.endswith(' ') or QUOTE_HEAD.search(post):
                continue          # ראשי תיבות או קיצור (ר"י, וכו')
            out.append((ti, m.start(), m.end(), w))
        pos += len(s)
    return out


class Source(object):
    """מילות המשנה המנוקדות של המסכת, לפי פרק ומשנה."""

    def __init__(self, slug):
        fp = os.path.join(ROOT, 'data', 'mishna', slug + '.json')
        self.ok = os.path.exists(fp)
        self.ch = []
        if self.ok:
            d = json.load(io.open(fp, encoding='utf-8'))
            for c in d.get('chapters') or []:
                self.ch.append([WORD.findall(TAGS.sub(' ', m or '')) for m in c])
        self.all = [w for c in self.ch for m in c for w in m]

    def candidates(self, p, n):
        """רצפי מקור לפי סדר עדיפות: המשנה (ושתי שכנותיה), הפרק, המסכת."""
        out = []
        if p and 1 <= p <= len(self.ch):
            c = self.ch[p - 1]
            if n and 1 <= n <= len(c):
                lo, hi = max(0, n - 2), min(len(c), n + 1)
                out.append([w for m in c[lo:hi] for w in m])
            out.append([w for m in c for w in m])
        out.append(self.all)
        return out


def _best_window(keys, src):
    """המקום הטוב ביותר במקור לרצף המילים (לפי שלד): [(i_dh, j_src)] של מילים תואמות."""
    if not keys or not src:
        return []
    sk = [skel(w) for w in src]
    idx = {}
    for j, k in enumerate(sk):
        idx.setdefault(k, []).append(j)
    best, best_pairs = 0, []
    starts = set()
    for i, k in enumerate(keys[:4]):
        for j in idx.get(k, [])[:400]:
            starts.add(max(0, j - i))
    for s0 in starts:
        win = sk[s0:s0 + len(keys) + 4]
        sm = difflib.SequenceMatcher(None, keys, win, autojunk=False)
        pairs = []
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == 'equal':
                pairs += [(i1 + t, s0 + j1 + t) for t in range(i2 - i1)]
        if len(pairs) > best:
            best, best_pairs = len(pairs), pairs
    return best_pairs


def vocalize(h, src, p=None, n=None, est=None):
    """מחזיר (html מנוקד או None, מונה). est: {טקסט-המשנה-שבד"ה: [מילים מנוקדות]} מן המנקד."""
    words = dh_words(h)
    st = {'words': len(words), 'mishna': 0, 'est': 0, 'left': 0}
    if not words:
        return None, st
    keys = [skel(w[3]) for w in words]
    got = [None] * len(words)
    for seq in src.candidates(p, n):
        pairs = _best_window(keys, seq)
        # התאמה טובה: רוב המילים, או לפחות שתיים ברצף קצר
        if len(pairs) >= max(2, (len(words) + 1) // 2) or (len(words) == 1 and pairs):
            for i, j in pairs:
                w, s = words[i][3], seq[j]
                if not has_nikud(s):
                    continue
                if letters(w) == letters(s):
                    got[i] = s
                else:
                    t = transfer(w, s)
                    if t is not None and letters(t) == letters(w):
                        got[i] = t
            break
    st['mishna'] = sum(1 for g in got if g)
    ev = (est or {}).get(est_key(h)) or []
    evw = {}
    if ev:
        # המטמון: כל מילות חלק המשנה לפי סדרן (nikud_generate.align). ההתאמה למילים הכשרות - לפי סדר ואותיות זהות
        q = 0
        for i, w in enumerate(words):
            for q2 in range(q, len(ev)):
                if ev[q2] and letters(ev[q2]) == letters(w[3]):
                    if has_nikud(ev[q2]):
                        evw[i] = ev[q2]
                    q = q2 + 1
                    break
    tok = _tokens(h)
    by_tok = {}
    for i, (ti, a, b, w) in enumerate(words):
        by_tok.setdefault(ti, []).append((a, b, i))
    for ti, lst in by_tok.items():
        s = tok[ti][1]
        out, pos = [], 0
        for a, b, i in lst:
            if got[i]:
                out.append(s[pos:a] + got[i])
            elif i in evw:
                out.append(s[pos:a] + '<span class="nks">' + evw[i] + '</span>')
                st['est'] += 1
            else:
                out.append(s[pos:b])
                st['left'] += 1
            pos = b
        tok[ti][1] = ''.join(out) + s[pos:]
    new = ''.join(x[1] for x in tok)
    return (new if new != h else None), st


def est_key(h):
    """מפתח המטמון: טקסט חלק המשנה של הד"ה, בלי תגיות."""
    import html as _h
    plain = TAGS.sub('', h or '')
    return _h.unescape(plain[:mishna_part(h)]).strip()


def load_est(slug):
    fp = os.path.join(ROOT, 'data', 'nikud-dh', slug + '.json')
    return json.load(io.open(fp, encoding='utf-8')) if os.path.exists(fp) else {}


def apply(pages, slug, mbt=None):
    """מוסיף u['av'] לכל ד"ה משנה. מחזיר מונה לבקרה."""
    src = Source(slug)
    st = {'dh': 0, 'voc': 0, 'words': 0, 'mishna': 0, 'est': 0, 'left': 0, 'nosrc': not src.ok}
    if not src.ok:
        return st
    est = load_est(slug)
    mid = {}
    for r in (mbt or []):
        try:
            mid[int(r['id'])] = (int(r['p']), int(r['n']))
        except Exception:
            pass
    cur = (None, None)
    for pg in pages:
        for u in pg['units']:
            try:
                uid = int(u.get('id'))
            except Exception:
                uid = None
            if u.get('k') == 'm' and uid in mid:
                cur = mid[uid]
            if u.get('k') != 'dh':
                continue
            u.pop('av', None)
            st['dh'] += 1
            new, s = vocalize(u.get('a') or '', src, cur[0], cur[1], est)
            for k in ('words', 'mishna', 'est', 'left'):
                st[k] += s[k]
            if new:
                u['av'] = new
                st['voc'] += 1
    return st
