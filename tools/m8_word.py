# -*- coding: utf-8 -*-
"""m8_word.py - מנה 1 מתוך 3 של 7.10.2026 (לווקר), בקובצי הוורד.

מה נעשה בכל קובץ, בהרצה אחת ובגיבוי אחד (כל שינוי תוכן ועיצוב בעקוב אחר שינויים, מחבר Claude):
א. סגנונות (בהגדרת הסגנון, לא בעיצוב ישיר): "הסבר במשנה" = M פחות שלוש נקודות (היה אחת);
   סגנון הפסקה החדש "פתיחת פרק" (וילנא אקסטרא בולד, שחור, ממורכז, שמור עם הבא).
ב. "הסבר" ו"רקע והסבר" (סגנון תו) בתוך פסקת משנה עוברים ל"הסבר במשנה".
ג. תנאי המשנה: שמות תנאים מרשימה סגורה שטרם סומנו, והנקודתיים שאחרי שם התנא (גם אחרי "אומר").
ד. אין רווח לפני נקודתיים: בכל הפסקאות.
ה. ציוני מספור בתחילת פסקת משנה ("א. ") מוסרים. מספר הקטע נשאר לפני ד"ה משנה בלבד.
ו. פתיחת פרק: "פרק" ו"פרק שם" (מסגרות צפות) מאוחדים לפסקה אחת בסגנון "פתיחת פרק", לפני המשנה
   הראשונה, בנוסח "פרק ראשון - מאמתי". אין מחיקת טקסט: המילים עוברות לפסקה החדשה.
   "תחילת פרק" שכבר מכילה את אותו פרק הופכת בעצמה ל"פתיחת פרק".

אימות: המרה חוזרת והשוואה פסקה אחר פסקה למצופה. גיבוי לפני כתיבה. קובץ פתוח בוורד אינו נכתב.

    uv run --with lxml python tools/m8_word.py <חלק משם הקובץ> ... [--dry] [--only a,b]
    uv run --with lxml python tools/m8_word.py --all [--dry]
"""
import os, sys, io, re, json, zipfile, datetime, argparse, collections, copy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lxml import etree
import word_apply
from word_apply import (ns, W, DRIVE, Refused, convert, _paragraph_map, _rezip, _ensure_track, backup,
                        is_open_in_word, wait_free, _copy_no_change, _mark, _runs_of, _rpr, _mkrun, _set_pstyle,
                        _style_ids)
from styles_map import ROLE, CS, TANAI_NAME, role_of
import mishna_sizes
import m6_word
from m6_word import _live, delete_paragraph, direct_runs_only, restyle_run, _rstyle_name, delete_text
from m7_word import _mark_para_end
from chapter_ord import chapter_ordinal

AUTHOR = 'Claude'
OWN_INS = ('Claude', 'קלוד', 'מספור קטעי משנה')
OPEN_STYLE = 'פתיחת פרק'
ALL_OPS = ('styles', 'hs', 'tanai', 'colonsp', 'numbers', 'chapters')
HS_NAMES = {n for n, c in CS.items() if c == 'hs' and n not in ('הסבר במשנה', 'הסבר במשנה תו')}
AM_NAMES = {n for n, c in CS.items() if c == 'am'
            and n not in (TANAI_NAME, TANAI_NAME + ' תו', 'תנאים במשנה', 'תנאים במשנה תו')}
LEAD_NUM = re.compile(r'^\s*(?:[א-ת]["״׳\'][א-ת]|[א-ת]{1,2}|\d{1,2})[\.\)]\s+')
SP_COLON = re.compile(r'(?<=[^\s:])([ \t ‎‏]+)(?=:)')
AFTER_NAME_COLON = re.compile(r'^\s*(?:(?:אומר|אומרים|אומרת)\s*)?:')
RANGE_LIKE = re.compile(r'^[\(\s]*[א-ת]{1,3}[\.:][\s\-–]+[א-ת]{1,3}[\.:][\)\s]*$')
ORD_WORDS = (r'(?:ראשון|שני|שלישי|רביעי|חמישי|שישי|שביעי|שמיני|תשיעי|עשירי|אחד עשר|שנים עשר|שלושה עשר|'
             r'ארבעה עשר|חמישה עשר|שישה עשר|י["״׳\']?[א-ו])')
OPEN_SEP = re.compile(r'^(\s*פרק\s+' + ORD_WORDS + r')([\s:·.]+)(\S.*?)\s*$')
# רשימת התנאים של 6.10.2026 (m6_word.TANNA), מורחבת (7.10.2026): כתיב ר'/ר׳ בלי "רבי", ציטוט כפול ('') וגרשיים
# אחרים בראשי תיבות, וכמה תנאים ודאיים נוספים. הרשימה נשארת סגורה: אין ניחוש.
_EXTRA = ['רבי צדוק', 'רבי ישבב', 'רבי יוחנן בן נורי', 'רבי חנניא בן גמליאל', 'רבי חנינא סגן הכהנים', 'רבי חנניא',
          'רבי חלפתא', 'רבי יהודה הנשיא', 'רבי שמעון בן אלעזר', 'רבי אלעזר בן עזריה', 'רבי יוסי הגלילי',
          'רבי שמעון שזורי', 'רבי אלעזר בן שמוע', 'רבי יהודה בן בתירא', 'רבי יוחנן הסנדלר']
_Q2 = "(?:[\"'׳״”“]{1,2})"
_names2 = set()
for _t in list(m6_word.TANNA) + _EXTRA:
    _names2.add(_t)
    if _t.startswith('רבי '):
        _names2.add("ר' " + _t[4:])
_names2 = sorted(_names2, key=len, reverse=True)
def _pat(t):
    out = ''
    for ch in t:
        out += _Q2 if ch in "\"'׳״" else re.escape(ch)
    return out
TANNA_RE2 = re.compile(r'(?<![א-ת])(?:[והלש]?)(' + '|'.join(_pat(t) for t in _names2) + r')(?![א-ת])')
NIKUD = re.compile('[֑-ׇ]')


# ---------------------------------------------------------------- סגנונות

def add_open_style(styles_xml):
    """מוסיף את סגנון הפסקה "פתיחת פרק" אם אינו קיים. מחזיר (xml, נוסף)."""
    root = etree.fromstring(styles_xml)
    for st in root.findall('w:style', ns):
        nm = st.find('w:name', ns)
        if nm is not None and nm.get(W + 'val') == OPEN_STYLE:
            return styles_xml, False
    base = None
    for st in root.findall('w:style', ns):
        if st.get(W + 'type') == 'paragraph' and st.get(W + 'default') == '1':
            base = st.get(W + 'styleId')
    m = mishna_sizes.mishna_size(root)
    ids = {st.get(W + 'styleId') for st in root.findall('w:style', ns)}
    sid, n = 'PetichatPerek', 1
    while sid in ids:
        n += 1
        sid = 'PetichatPerek%d' % n
    st = etree.SubElement(root, W + 'style')
    st.set(W + 'type', 'paragraph')
    st.set(W + 'customStyle', '1')
    st.set(W + 'styleId', sid)
    etree.SubElement(st, W + 'name').set(W + 'val', OPEN_STYLE)
    if base:
        etree.SubElement(st, W + 'basedOn').set(W + 'val', base)
        etree.SubElement(st, W + 'next').set(W + 'val', base)
    etree.SubElement(st, W + 'qFormat')
    pPr = etree.SubElement(st, W + 'pPr')
    etree.SubElement(pPr, W + 'keepNext')
    etree.SubElement(pPr, W + 'keepLines')
    etree.SubElement(pPr, W + 'jc').set(W + 'val', 'center')
    rPr = etree.SubElement(st, W + 'rPr')
    rf = etree.SubElement(rPr, W + 'rFonts')
    rf.set(W + 'ascii', 'BA Fontov Regular')
    rf.set(W + 'hAnsi', 'BA Fontov Regular')
    rf.set(W + 'cs', 'BA TM • Vilna Extra-Bold')
    etree.SubElement(rPr, W + 'color').set(W + 'val', '000000')
    etree.SubElement(rPr, W + 'spacing').set(W + 'val', '4')
    etree.SubElement(rPr, W + 'sz').set(W + 'val', str(m))
    etree.SubElement(rPr, W + 'szCs').set(W + 'val', str(m))
    return etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True), True


# ---------------------------------------------------------------- מנוע ריצות

def _run_style_name(r, sid2name):
    rp = r.find('w:rPr', ns)
    if rp is None:
        return None
    s = rp.find('w:rStyle', ns)
    return sid2name.get(s.get(W + 'val')) if s is not None else None


def _remove_run(r):
    par = r.getparent()
    par.remove(r)
    if par.tag == W + 'ins' and not len(par):
        par.getparent().remove(par)


def remove_leading_number(p, sid2name, author, when, nextid, rep):
    """מסיר את ציון המספור שבתחילת פסקת משנה: סגנון התו "מספר קטע", ואחריו ציון שהוקלד ("ב. ")."""
    removed = 0
    for _ in range(3):
        runs = _runs_of(p)
        if not runs:
            break
        pos, txt, r = runs[0]
        if _run_style_name(r, sid2name) in m6_word.NUMBER_STYLES and LEAD_NUM.match(txt):
            par = r.getparent()
            if par.tag == W + 'p':
                if not delete_text(p, 0, len(txt), author, when, nextid):
                    rep['number_skipped'] += 1
                    break
            elif par.tag == W + 'ins' and par.get(W + 'author') in OWN_INS:
                _remove_run(r)
            else:
                rep['number_skipped'] += 1
                break
            removed += 1
            continue
        full = ''.join(t for _, t, _ in runs)
        m = LEAD_NUM.match(full)
        if m:
            if delete_text(p, 0, m.end(), author, when, nextid):
                removed += 1
                continue
            rep['number_skipped'] += 1
        break
    return removed


def space_before_colon(p, author, when, nextid, rep):
    """מוחק רווח (טאב, רווח קשיח) שלפני נקודתיים. מחזיר מספר מחיקות."""
    full = ''.join(t for _, t, _ in _runs_of(p))
    spans = [(m.start(1), m.end(1)) for m in SP_COLON.finditer(full)]
    n = 0
    for lo, hi in reversed(spans):
        if delete_text(p, lo, hi, author, when, nextid):
            n += 1
        else:
            rep['colonsp_skipped'] += 1
    return n


def mark_ranges(p, ranges, tn_sid, author, when, nextid):
    """מסמן טווחי תווים (לפי הטקסט החי) בסגנון "תנאי המשנה". רק ריצות ישירות בפסקה ובלי סגנון תו."""
    n = 0
    for lo, hi in sorted(set(ranges), reverse=True):
        runs = _runs_of(p)
        touched = [(pos, txt, r) for pos, txt, r in runs if pos < hi and pos + len(txt) > lo]
        ok = bool(touched)
        for _, _, r in touched:
            rp = r.find('w:rPr', ns)
            if r.getparent().tag != W + 'p' or (rp is not None and rp.find('w:rStyle', ns) is not None):
                ok = False
        if not ok:
            continue
        for pos, txt, r in touched:
            a = max(lo - pos, 0)
            b = min(hi - pos, len(txt))
            rpr = _rpr(r)
            parent = r.getparent()
            i0 = list(parent).index(r)
            new = []
            if txt[:a]:
                new.append(_mkrun(txt[:a], rpr))
            mid = _mkrun(txt[a:b], rpr)
            restyle_run(mid, tn_sid, author, when, nextid)
            new.append(mid)
            if txt[b:]:
                new.append(_mkrun(txt[b:], rpr))
            parent.remove(r)
            for k, el in enumerate(new):
                parent.insert(i0 + k, el)
        n += 1
    return n


def tanai_ranges(p, sid2name, tn_sid):
    """(שמות שטרם סומנו, נקודתיים שטרם סומנו) לפי הרשימה הסגורה, ולפי שמות שכבר מסומנים."""
    runs = _runs_of(p)
    full = ''.join(t for _, t, _ in runs)
    if not full:
        return [], []
    styled = [False] * len(full)
    for pos, txt, r in runs:
        rp = r.find('w:rPr', ns)
        s = rp.find('w:rStyle', ns) if rp is not None else None
        if s is not None and s.get(W + 'val') == tn_sid:
            for k in range(pos, pos + len(txt)):
                styled[k] = True
    pl, idx = m6_word.plain_map(full)
    names, colons = [], []
    name_ends = []                       # אינדקס בטקסט המלא שאחרי סוף שם תנא
    for m in TANNA_RE2.finditer(pl):
        a, b = m.start(1), m.end(1)
        lo, hi = idx[a], idx[b - 1] + 1
        if not any(styled[lo:hi]):
            names.append((lo, hi))
        name_ends.append(hi)
    k = 0
    while k < len(full):                 # סוף רצף מסומן: גם הוא שם תנא
        if styled[k]:
            e = k
            while e < len(full) and styled[e]:
                e += 1
            name_ends.append(e)
            k = e
        else:
            k += 1
    for e in set(name_ends):
        m = AFTER_NAME_COLON.match(full[e:])
        if m:
            c = e + m.end() - 1
            if not styled[c]:
                colons.append((c, c + 1))
    return names, colons


def edit_own_ins(p, lo, hi, repl):
    """החלפת טקסט בתוך הוספה במעקב שלי (מהרצה קודמת, עדיין לא התקבלה): עריכה במקום. אין שינוי של אחר."""
    for pos, txt, r in _runs_of(p):
        if pos <= lo and hi <= pos + len(txt):
            par = r.getparent()
            if par.tag == W + 'ins' and par.get(W + 'author') in OWN_INS:
                ts = [t for t in r if t.tag == W + 't']
                if len(ts) == 1:
                    ts[0].text = txt[:lo - pos] + repl + txt[hi - pos:]
                    ts[0].set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
                    return True
    return False


def sim_numbers(b):
    """הטקסט המצופה אחרי הסרת ציוני המספור משורת פסקת משנה (מן הנתונים שלפני, לא מן התוצאה)."""
    t = b['text']
    runs = b.get('runs') or []
    for _ in range(3):
        if runs and (runs[0].get('cs') or '') in m6_word.NUMBER_STYLES and LEAD_NUM.match(runs[0]['t']):
            t = t[len(runs[0]['t']):]
            runs = runs[1:]
            continue
        m = LEAD_NUM.match(t)
        if m:
            t = t[m.end():]
            runs = []
            continue
        break
    return t


# ---------------------------------------------------------------- פתיחת פרק

def plan_chapters(before):
    """תכנית איחוד: [{mode, num, name(s), start, text}] ורשימת חריגות. אינדקסים לפי מקום ברשימה."""
    roles = [role_of(b) for b in before]
    live = lambda i: bool(before[i]['text'].strip())
    isnum = lambda i: bool(chapter_ordinal(before[i]['text'])) or before[i]['text'].strip().startswith('פרק')
    rnglike = lambda i: bool(RANGE_LIKE.match(before[i]['text'].strip()))
    N = [i for i, r in enumerate(roles) if r in ('perek-num', 'perek-name') and live(i) and isnum(i)]
    S = [i for i, r in enumerate(roles) if r == 'perek-start' and live(i)]
    # פסקה בסגנון "פרק" שנוסחה אינו "פרק ..." היא שם פרק שסומן בסגנון הלא נכון
    M = [i for i, r in enumerate(roles) if r in ('perek-num', 'perek-name') and live(i) and not isnum(i)
         and not rnglike(i)]
    notes = []
    plans = []
    used_n, used_m = set(), set()
    # תחילת פרק שמכילה פרק שהוא גם בכותרות: היא עצמה הפתיחה
    for s in S:
        o = chapter_ordinal(before[s]['text'])
        near = [n for n in N if o and chapter_ordinal(before[n]['text']) == o and abs(n - s) <= 14 and n not in used_n]
        if near:
            nn = min(near, key=lambda n: abs(n - s))
            used_n.add(nn)
            used_m.update(m_ for m_ in M if abs(m_ - nn) <= 6)
        if before[s]['style'] != OPEN_STYLE:
            plans.append({'mode': 'start', 'start': s, 'text': before[s]['text'].strip()})
    bounds = sorted({i for i, r in enumerate(roles) if live(i) and (
        r == 'hadran' or (not r.startswith('perek') and 'הדרן עלך' in NIKUD.sub('', before[i]['text'])[:14]))})
    # פרק שכבר נפתח בפסקת "פתיחת פרק" (גם מהרצה קודמת): מסגרת "פרק" שנשארה לו היא כפילות, ואין לאחד אותה שוב
    opened = {chapter_ordinal(before[s]['text']) for s in S if before[s]['style'] == OPEN_STYLE}
    opened.discard(None)
    for n in N:
        if chapter_ordinal(before[n]['text']) in opened and n not in used_n:
            used_n.add(n)
            notes.append('מסגרת "%s" (פסקה %d) חוזרת על פתיחת פרק קיימת - לא נגעתי' % (before[n]['text'].strip(), n))
    rest = [n for n in N if n not in used_n]
    # מסגרת כפולה: אותו פרק פעמיים ברצף, בלי הדרן ביניהם - הראשונה היא הפתיחה והשנייה נשארת כמות שהיא
    dedup = []
    for n in rest:
        o = chapter_ordinal(before[n]['text'])
        if dedup and o and chapter_ordinal(before[dedup[-1]]['text']) == o                 and not any(dedup[-1] < b < n for b in bounds):
            notes.append('מסגרת "%s" כפולה (פסקה %d) - לא נגעתי' % (before[n]['text'].strip(), n))
            continue
        dedup.append(n)
    rest = dedup
    M = [m_ for m_ in M if m_ not in used_m]
    dm = []
    for m_ in M:
        if len(M) > len(rest) and dm and before[m_]['text'].strip() == before[dm[-1]]['text'].strip() and m_ - dm[-1] <= 6:
            notes.append('שם פרק כפול "%s" (פסקה %d) - לא נגעתי' % (before[m_]['text'].strip()[:30], m_))
            continue
        dm.append(m_)
    M = dm
    if len(rest) == len(M) and rest:
        pairs = list(zip(rest, M))
        how = 'לפי הסדר'
    else:
        # יישור שומר סדר (כמו יישור רצפים): שם אל מספר שלפי הסדר, במינימום מרחק; דילוג יקר
        C = 500
        a, b = len(rest), len(M)
        cost = [[0] * (b + 1) for _ in range(a + 1)]
        back = [[None] * (b + 1) for _ in range(a + 1)]
        for i in range(a + 1):
            for j in range(b + 1):
                if i == 0 and j == 0:
                    continue
                opts = []
                if i and j:
                    opts.append((cost[i - 1][j - 1] + abs(rest[i - 1] - M[j - 1]), 'm'))
                if i:
                    opts.append((cost[i - 1][j] + C, 'n'))
                if j:
                    opts.append((cost[i][j - 1] + C, 'k'))
                cost[i][j], back[i][j] = min(opts)
        pairs = []
        i, j = a, b
        while i or j:
            t = back[i][j]
            if t == 'm':
                pairs.append((rest[i - 1], M[j - 1]))
                i -= 1
                j -= 1
            elif t == 'n':
                pairs.append((rest[i - 1], None))
                i -= 1
            else:
                j -= 1
        pairs.sort()
        how = 'יישור לפי הסדר והקרבה'
    paired_m = {m_ for _, m_ in pairs if m_ is not None}
    for n, m_ in pairs:
        nt = before[n]['text'].strip()
        mt = before[m_]['text'].strip() if m_ is not None else ''
        plans.append({'mode': 'merge', 'num': n, 'name': m_, 'text': nt + (' - ' + mt if mt else ''), 'how': how})
        if m_ is None:
            notes.append('פרק בלי שם: "%s" (פסקה %d)' % (nt, n))
    for m_ in M:
        if m_ not in paired_m:
            notes.append('שם פרק בלי מספר: "%s" (פסקה %d) - לא נגעתי' % (before[m_]['text'].strip()[:30], m_))
    plans.sort(key=lambda x: x.get('num', x.get('start')))
    # מקום ההכנסה: לפני המשנה הראשונה של הפרק (אחרי ההדרן הקודם), לפני תווית "משנה בצד" וחלון הכותרת
    # הצמודים לה, ואחרי ציון הדף. מסגרות הפרק בוורד צפות ויושבות לעתים הרחק מתחילת הפרק.
    def first_mishna_after(a):
        for k in range(a + 1, len(before)):
            if roles[k] == 'mishna' and live(k) and k not in bounds:
                return k
        return None
    taken = collections.Counter()
    last_t = -1
    for pl in plans:
        if pl['mode'] != 'merge':
            continue
        P = pl['num']                  # מיקום המספר אמין; שם הפרק נודד לעתים הרחק מפרקו
        prev = max([b for b in bounds if b < P], default=-1)
        k = first_mishna_after(prev)
        if k is None or k <= last_t:                 # אין הדרן שמפריד מן הפרק הקודם: המשנה הראשונה אחרי המסגרת
            k = first_mishna_after(P)
        if k is not None:
            last_t = k
        if k is not None:
            while k - 1 >= 0 and roles[k - 1] in ('skip', 'anchor') and live(k - 1) is not None:
                if roles[k - 1] == 'skip' and before[k - 1]['style'] not in ('משנה בצד',):
                    break
                k -= 1
        pl['target'] = k
        if k is not None:
            taken[k] += 1
    for t_, cnt_ in list(taken.items()):
        if cnt_ > 1:
            group = [pl for pl in plans if pl['mode'] == 'merge' and pl.get('target') == t_]
            keep = min(group, key=lambda g: (g['num'] > t_, abs(t_ - g['num'])))
            for pl in group:
                if pl is not keep:
                    pl['skip'] = True
                    notes.append('שני פרקים נפלו על אותה משנה ראשונה: "%s" נשארה כמות שהיא (לא אוחדה)' % pl['text'][:30])
    return plans, notes, how if N else ''


# ---------------------------------------------------------------- הראשי

def process(path, slug, dry=False, log=print, only=None):
    only = set(only) if only else set(ALL_OPS)
    if is_open_in_word(path) and not wait_free(path, log=log):
        raise Refused('הקובץ פתוח בוורד ולא התפנה')
    mtime = os.path.getmtime(path)
    before = convert(path)
    for k, b in enumerate(before):
        if b['i'] != k:
            raise Refused('אינדקס הפסקאות אינו רציף (%d מול %d)' % (b['i'], k))
    pmap_last = dict(word_apply.convert.last)
    z = zipfile.ZipFile(path)
    doc = etree.fromstring(z.read('word/document.xml'))
    settings = z.read('word/settings.xml')
    styles = z.read('word/styles.xml')
    z.close()
    rep = collections.OrderedDict(file=os.path.basename(path))
    rep.update(hs_restyled=0, am_restyled=0, tanai_names=0, tanai_colons=0, colonsp=0, colonsp_skipped=0,
               numbers=0, number_skipped=0, chapters_merged=0, chapters_restyled=0, notes=[])
    extra = {}
    if 'styles' in only:
        styles, srep = mishna_sizes.sync(styles)
        styles, added = add_open_style(styles)
        rep['sizes'] = {k: srep[k] for k in ('M', 'tanai', 'hs')}
        rep['open_style_added'] = added
        rep['sizes_changed'] = bool(srep['changed'])
        extra['word/styles.xml'] = styles
    ids = _style_ids(styles)
    sid2name = {}
    for st in etree.fromstring(styles).findall('w:style', ns):
        nm = st.find('w:name', ns)
        if nm is not None:
            sid2name[st.get(W + 'styleId')] = nm.get(W + 'val')
    tn_sid = ids[TANAI_NAME][0]
    hs_sid = ids['הסבר במשנה'][0]
    open_sid = ids[OPEN_STYLE][0] if OPEN_STYLE in ids else None
    word_apply.convert.last = pmap_last
    xml_ps = _paragraph_map(doc, before)
    mx = 0
    for el in doc.iter():
        v = el.get(W + 'id')
        if v and v.isdigit():
            mx = max(mx, int(v))
    counter = [mx + 1000]

    def nextid():
        counter[0] += 1
        return counter[0]

    when = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    exp_text = {b['i']: b['text'] for b in before}
    live_text = lambda p: ''.join(t for _, t, _ in _runs_of(p))
    exp_style = {b['i']: b['style'] for b in before}
    roles = {b['i']: role_of(b) for b in before}

    deleted = set()
    # --- ב, ה, ד, ג: פסקה אחר פסקה
    for b in before:
        p = xml_ps.get(b['i'])
        if p is None:
            continue
        mishna = roles[b['i']] == 'mishna'
        if mishna and 'hs' in only:
            for r in list(p.iter(W + 'r')):
                if not _live(r):
                    continue
                nm = _rstyle_name(r, sid2name)
                if nm in HS_NAMES:
                    restyle_run(r, hs_sid, AUTHOR, when, nextid)
                    rep['hs_restyled'] += 1
                elif nm in AM_NAMES:
                    restyle_run(r, tn_sid, AUTHOR, when, nextid)
                    rep['am_restyled'] += 1
        skips0 = rep['number_skipped'] + rep['colonsp_skipped']
        want = b['text']
        if mishna and 'numbers' in only:
            k = remove_leading_number(p, sid2name, AUTHOR, when, nextid, rep)
            if k:
                rep['numbers'] += k
                want = sim_numbers(b)
        if 'colonsp' in only and b['text'].strip():
            k = space_before_colon(p, AUTHOR, when, nextid, rep)
            if k:
                rep['colonsp'] += k
                want = SP_COLON.sub('', want)
        if rep['number_skipped'] + rep['colonsp_skipped'] != skips0:
            want = live_text(p)          # דילוג על שינוי מעקב של אחר: המצופה הוא מה שנשאר
        exp_text[b['i']] = want
        if mishna and b['text'].strip() and not want.strip() and 'numbers' in only:
            # פסקה שכולה ציון מספור: אחרי ההסרה נשארה ריקה, ולכן נמחקת כולה (במעקב)
            if direct_runs_only(p) or not live_text(p).strip():
                delete_paragraph(p, AUTHOR, when, nextid)
                deleted.add(b['i'])
                rep['numbers_orphan_paragraphs'] = rep.get('numbers_orphan_paragraphs', 0) + 1
        if mishna and 'tanai' in only:
            names, colons = tanai_ranges(p, sid2name, tn_sid)
            rep['tanai_names'] += mark_ranges(p, names, tn_sid, AUTHOR, when, nextid)
            names2, colons = tanai_ranges(p, sid2name, tn_sid)
            rep['tanai_colons'] += mark_ranges(p, colons, tn_sid, AUTHOR, when, nextid)

    # --- ו: פתיחת פרק
    new_paras = {}                 # אינדקס פסקה -> נוסח הפסקה החדשה שלפניה
    if 'chapters' in only:
        if open_sid is None:
            raise Refused('אין סגנון "%s" (הרץ עם styles)' % OPEN_STYLE)
        plans, notes, how = plan_chapters(before)
        rep['notes'] += notes
        rep['pairing'] = how
        rep['chapters'] = []
        for pl in plans:
            if pl.get('skip'):
                continue
            if pl['mode'] == 'start':
                p = xml_ps[pl['start']]
                if _set_pstyle(p, open_sid, AUTHOR, when, nextid) is False:
                    continue
                pPr = p.find('w:pPr', ns)
                fr = pPr.find('w:framePr', ns)
                if fr is not None:
                    pPr.remove(fr)
                exp_style[pl['start']] = OPEN_STYLE
                rep['chapters_restyled'] += 1
                rep['chapters'].append(['תחילת פרק <- פתיחת פרק', pl['text']])
                continue
            n, m_ = pl['num'], pl['name']
            pn = xml_ps[n]
            pm = xml_ps[m_] if m_ is not None else None
            if not direct_runs_only(pn) or (pm is not None and not direct_runs_only(pm)):
                rep['notes'].append('לא אוחד: שינוי מעקב של אחר בפרק "%s"' % pl['text'][:30])
                continue
            runs_n = [r for r in pn.iter(W + 'r') if _live(r)]
            rpr_n = _rpr(runs_n[0]) if runs_n else None
            spec = [(before[n]['text'].strip(), rpr_n)]
            if m_ is not None:
                runs_m = [r for r in pm.iter(W + 'r') if _live(r)]
                rpr_m = _rpr(runs_m[0]) if runs_m else None
                spec += [(' - ', rpr_n), (before[m_]['text'].strip(), rpr_m)]
            p2 = etree.Element(W + 'p')
            pPr2 = etree.SubElement(p2, W + 'pPr')
            etree.SubElement(pPr2, W + 'pStyle').set(W + 'val', open_sid)
            ins = _mark(etree.Element(W + 'ins'), AUTHOR, when, nextid)
            for t, rp in spec:
                ins.append(_mkrun(t, rp))
            p2.append(ins)
            _mark_para_end(p2, 'ins', AUTHOR, when, nextid)
            tgt = pl.get('target')
            at = xml_ps[tgt] if tgt is not None and tgt in xml_ps else pn
            at.getparent().insert(list(at.getparent()).index(at), p2)
            delete_paragraph(pn, AUTHOR, when, nextid)
            deleted.add(n)
            if pm is not None:
                delete_paragraph(pm, AUTHOR, when, nextid)
                deleted.add(m_)
            new_paras[tgt if tgt is not None and tgt in xml_ps else n] = pl['text']
            rep['chapters_merged'] += 1
            rep['chapters'].append(['איחוד', pl['text']])

    # מסגרות "פרק" ו"שם פרק" שנשארו וכל תוכנן כבר בפתיחת פרק: כפילות מדויקת, נמחקות במעקב (המילים נשמרות בפתיחה)
    if 'chapters' in only:
        def _pk(t):
            return re.sub(r'[^א-ת]', '', NIKUD.sub('', t or ''))
        open_txt = [new_paras[k] for k in new_paras]
        open_txt += [exp_text[i] for i in exp_text if exp_style[i] == OPEN_STYLE and i not in deleted]
        open_pk = [_pk(t) for t in open_txt]
        open_ord = {chapter_ordinal(t) for t in open_txt}
        open_ord.discard(None)
        skipped_txt = ' '.join(pl['text'] for pl in plans if pl.get('skip'))
        for b in before:
            i = b['i']
            if i in deleted or i not in xml_ps or not b['text'].strip():
                continue
            if b['style'] not in ('פרק', 'פרק שם'):
                continue
            t = b['text']
            if chapter_ordinal(t) or t.strip().startswith('פרק'):
                dup = chapter_ordinal(t) in open_ord and t.strip() not in skipped_txt
            else:
                k = _pk(t)
                dup = len(k) >= 4 and any(k in o for o in open_pk) and t.strip() not in skipped_txt
            if dup and direct_runs_only(xml_ps[i]):
                delete_paragraph(xml_ps[i], AUTHOR, when, nextid)
                deleted.add(i)
                rep['dup_tags_deleted'] = rep.get('dup_tags_deleted', 0) + 1
    # הנוסח האחיד של פתיחת פרק: "פרק ראשון - מאמתי" (במקום רווח, נקודתיים או נקודה אמצעית שבין המספר לשם)
    if 'chapters' in only:
        for b in before:
            i = b['i']
            if exp_style[i] != OPEN_STYLE or i in deleted or i not in xml_ps:
                continue
            p = xml_ps[i]
            full = live_text(p)
            m = OPEN_SEP.match(full)
            if m and '-' not in m.group(2) and not re.match(r'[-–]', m.group(3)):
                lo, hi = m.start(2), m.end(2)
                if word_apply._replace_in_paragraph(p, full[lo:hi], ' - ', AUTHOR, when, nextid, at=lo)                         or edit_own_ins(p, lo, hi, ' - '):
                    exp_text[i] = full[:lo] + ' - ' + full[hi:]
                    rep['open_sep_fixed'] = rep.get('open_sep_fixed', 0) + 1
                else:
                    rep['notes'].append('לא נוסח באחידות (שינוי מעקב של אחר): "%s"' % full.strip()[:30])
    exp = []
    for b in before:
        i = b['i']
        if i in new_paras:
            exp.append((OPEN_STYLE, new_paras[i]))
        if i in deleted:
            continue
        exp.append((exp_style[i], exp_text[i]))
    rep['expected_paragraphs'] = len(exp)
    changed = bool(rep['hs_restyled'] or rep['am_restyled'] or rep['tanai_names'] or rep['tanai_colons']
                   or rep['colonsp'] or rep['numbers'] or rep['chapters_merged'] or rep['chapters_restyled'] or rep.get('open_sep_fixed') or rep.get('dup_tags_deleted')
                   or rep.get('open_style_added') or rep.get('sizes_changed'))
    if not changed:
        rep['changed'] = False
        return rep
    if os.path.getmtime(path) != mtime:
        rep['stale'] = True
        return rep
    tmp = path + ('.dry' if dry else '.new')
    parts = dict(extra)
    parts['word/document.xml'] = etree.tostring(doc, xml_declaration=True, encoding='UTF-8', standalone=True)
    parts['word/settings.xml'] = _ensure_track(settings)[0]
    _rezip(path, tmp, parts)
    after = convert(tmp)
    got = [(a['style'], a['text']) for a in after]
    bad = []
    if got != exp:
        import difflib
        sm = difflib.SequenceMatcher(None, got, exp, autojunk=False)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag != 'equal':
                bad.append('%s: קיבלנו %r ציפינו %r' % (tag, got[i1:i2][:2], exp[j1:j2][:2]))
                if len(bad) >= 6:
                    break
    try:
        zz = zipfile.ZipFile(tmp)
        assert zz.testzip() is None
        for n_ in ('word/document.xml', 'word/styles.xml', 'word/settings.xml'):
            etree.fromstring(zz.read(n_))
        zz.close()
    except Exception as e:
        bad.append('הקובץ החדש אינו תקין: %s' % e)
    if bad:
        os.remove(tmp)
        rep['verified'] = False
        rep['errors'] = bad
        return rep
    if dry:
        os.remove(tmp)
        rep['dry'] = True
        rep['verified'] = True
        return rep
    if os.path.getmtime(path) != mtime or is_open_in_word(path):
        os.remove(tmp)
        rep['stale'] = True
        return rep
    bk = backup(path, slug) if os.path.abspath(os.path.dirname(path)) == os.path.abspath(DRIVE) else None
    os.replace(tmp, path)
    rep['verified'] = True
    rep['backup'] = bk
    return rep


def files(pattern=None):
    out = []
    for f in sorted(os.listdir(DRIVE)):
        if f.lower().endswith('.docx') and not f.startswith('~$'):
            if not pattern or any(p in f for p in pattern):
                out.append(os.path.join(DRIVE, f))
    return out


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    ap = argparse.ArgumentParser()
    ap.add_argument('names', nargs='*')
    ap.add_argument('--all', action='store_true')
    ap.add_argument('--dry', action='store_true')
    ap.add_argument('--only')
    ap.add_argument('--out', help='קובץ JSON לדוח')
    a = ap.parse_args()
    only = a.only.split(',') if a.only else None
    reps = []
    for path in files(None if a.all else a.names):
        slug = os.path.splitext(os.path.basename(path))[0]
        r = None
        for attempt in range(3):
            try:
                r = process(path, slug, dry=a.dry, only=only)
            except Refused as e:
                r = {'file': os.path.basename(path), 'refused': str(e)}
            if not r.get('stale'):
                break
            print('הקובץ השתנה בזמן העיבוד, מנסה שוב', attempt + 1)
        print(json.dumps(r, ensure_ascii=False))
        reps.append(r)
    if a.out:
        io.open(a.out, 'w', encoding='utf-8').write(json.dumps(reps, ensure_ascii=False, indent=1))
