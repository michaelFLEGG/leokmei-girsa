# -*- coding: utf-8 -*-
"""m9_hadran.py - "הדרן עלך [שם הפרק]" בסוף כל פרק, בקובצי הוורד (8.10.2026).

מה נעשה בכל קובץ, בהרצה אחת ובגיבוי אחד (הכול בעקוב אחר שינויים, מחבר Claude):
א. סגנון הפסקה החדש "הדרן": וילנא, ממורכז, שחור, קטן מעט משם הפרק ("פתיחת פרק").
ב. שורת "הדרן עלך ..." שכבר קיימת (בכל סגנון: הדרן עלך, נושא, ד"ה משנה, חציצה, רגיל) מקבלת את
   הסגנון "הדרן". אם שם הפרק בה שונה מן השם שבשורת הפתיחה - השם מתוקן (רק הקטע שהשתנה); "הדרך"->"הדרן".
   שורה שהשם שבה הוא שם של פרק אחר בקובץ אינה משתנה במילים - רק בסגנון, ומדווחת.
ג. פרק שאין לו שורה כזאת - נוספת פסקה "הדרן עלך [שם]" בסוף הפרק (לפני פתיחת הפרק הבא, ובפרק האחרון -
   אחרי הפסקה האחרונה של הטקסט). שם הפרק נלקח משורת הפתיחה עצמה ("פרק ראשון - מאמתי" ->
   "מאמתי"), בלי "+" ובלי פיסוק סופי.

מה שאינו נעשה: פרק שאין בשורת הפתיחה שלו שם - מדווח ואינו נכתב. שינוי מעקב של אחר (בני) אינו
נגע ואינו מאושר: ההחלפה מסרבת לגעת בטקסט שיושב בתוך שינוי כזה.

אימות: המרה חוזרת והשוואה פסקה אחר פסקה למצופה. גיבוי לפני כתיבה. קובץ פתוח בוורד אינו נכתב.

    uv run --with lxml python tools/m9_hadran.py <חלק משם הקובץ> ... [--dry]
    uv run --with lxml python tools/m9_hadran.py --all [--dry]
"""
import os, sys, io, re, json, zipfile, datetime, argparse, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lxml import etree
import word_apply
from word_apply import (ns, W, DRIVE, Refused, convert, _paragraph_map, _rezip, _ensure_track, backup,
                        is_open_in_word, wait_free, _mark, _runs_of, _mkrun, _set_pstyle, _style_ids,
                        _replace_in_paragraph)
from styles_map import role_of
import mishna_sizes
from m6_word import direct_runs_only
from m7_word import _mark_para_end
from chapter_ord import chapter_ordinal

AUTHOR = 'Claude'
HAD_STYLE = 'הדרן'
OPEN_STYLE = 'פתיחת פרק'
NIKUD = re.compile('[֑-ׇ]')
HAD_RE = re.compile(r'^[^א-ת]*(הדר[ןך])\s+עלך(?=\s|$)')
OPEN_NAME = re.compile(r'^\s*[-–]?\s*פרק\s+[^-–:]*?\s*[-–:]\s*(.+?)\s*$')
HEADERISH = ('perek-range', 'perek-num', 'perek-name')
NOT_BODY = ('daf', 'anchor', 'skip', 'nose', 'dh', 'hatz', 'perek-num', 'perek-name', 'perek-range',
            'perek-start', 'hadran')


def add_had_style(styles_xml):
    """מוסיף את סגנון הפסקה "הדרן" אם אינו קיים. מחזיר (xml, נוסף)."""
    root = etree.fromstring(styles_xml)
    for st in root.findall('w:style', ns):
        nm = st.find('w:name', ns)
        if nm is not None and nm.get(W + 'val') == HAD_STYLE:
            return styles_xml, False
    base = None
    for st in root.findall('w:style', ns):
        if st.get(W + 'type') == 'paragraph' and st.get(W + 'default') == '1':
            base = st.get(W + 'styleId')
    m = mishna_sizes.mishna_size(root)
    sz = max(16, int(m) - 2)         # קטן מעט משם הפרק (פתיחת פרק = גודל המשנה)
    ids = {st.get(W + 'styleId') for st in root.findall('w:style', ns)}
    sid, n = 'Hadran', 1
    while sid in ids:
        n += 1
        sid = 'Hadran%d' % n
    st = etree.SubElement(root, W + 'style')
    st.set(W + 'type', 'paragraph')
    st.set(W + 'customStyle', '1')
    st.set(W + 'styleId', sid)
    etree.SubElement(st, W + 'name').set(W + 'val', HAD_STYLE)
    if base:
        etree.SubElement(st, W + 'basedOn').set(W + 'val', base)
        etree.SubElement(st, W + 'next').set(W + 'val', base)
    etree.SubElement(st, W + 'qFormat')
    pPr = etree.SubElement(st, W + 'pPr')
    etree.SubElement(pPr, W + 'keepLines')
    sp = etree.SubElement(pPr, W + 'spacing')
    sp.set(W + 'before', '120')
    sp.set(W + 'after', '120')
    ind = etree.SubElement(pPr, W + 'ind')
    ind.set(W + 'left', '0')
    ind.set(W + 'hanging', '0')
    etree.SubElement(pPr, W + 'jc').set(W + 'val', 'center')
    rPr = etree.SubElement(st, W + 'rPr')
    rf = etree.SubElement(rPr, W + 'rFonts')
    rf.set(W + 'ascii', 'BA Fontov Regular')
    rf.set(W + 'hAnsi', 'BA Fontov Regular')
    rf.set(W + 'cs', 'BA TM • Vilna Extra-Bold')
    etree.SubElement(rPr, W + 'color').set(W + 'val', '000000')
    etree.SubElement(rPr, W + 'spacing').set(W + 'val', '4')
    etree.SubElement(rPr, W + 'sz').set(W + 'val', str(sz))
    etree.SubElement(rPr, W + 'szCs').set(W + 'val', str(sz))
    return etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True), True


def _pk(t):
    return re.sub(r'[^א-ת]', '', NIKUD.sub('', t or ''))


def clean_name(t):
    t = NIKUD.sub('', t or '')
    t = t.replace('+', '')
    t = re.sub(r'\s+', ' ', t).strip()
    return t.strip('-–:. ,;').strip()


def opening_name(text):
    m = OPEN_NAME.match(text or '')
    return clean_name(m.group(1)) if m else ''


def is_had_text(text):
    t = NIKUD.sub('', text or '')
    t = re.sub(r'\s+', ' ', t).strip()
    return bool(HAD_RE.match(t)) and 'מסכת' not in t[:14]


def split_had(text):
    """(היסט תחילת שם הפרק, היסט סופו, היסט המילה הראשונה, סופה) בטקסט החי, או None."""
    m = re.match(r'^([^א-ת]*)(הדר[ןך])(\s+)(עלך)(\s+)(.*)$', text, re.S)
    if not m:
        return None
    start = m.start(6)
    rest = m.group(6)
    cut = re.search(r'\s+ו?סליק', rest)
    core = rest[:cut.start()] if cut else rest
    core_end = len(core.rstrip('.,:; ‏‎'))
    return (start, start + core_end, m.start(2), m.end(2))


_ORD_PH = {'ראשון': 1, 'שני': 2, 'שלישי': 3, 'רביעי': 4, 'חמישי': 5, 'שישי': 6, 'שביעי': 7, 'שמיני': 8,
           'תשיעי': 9, 'עשירי': 10, 'אחד עשר': 11, 'שנים עשר': 12, 'שנים עשרה': 12, 'שלושה עשר': 13, 'שלשה עשר': 13,
           'ארבעה עשר': 14, 'חמישה עשר': 15, 'חמשה עשר': 15, 'שישה עשר': 16, 'ששה עשר': 16, 'שבעה עשר': 17}
_ORD_LET = {'י"א': 11, 'י"ב': 12, 'י"ג': 13, 'י"ד': 14, 'ט"ו': 15, 'ט"ז': 16, 'י"ז': 17}


def ordinal(text):
    t = NIKUD.sub('', text or '')
    t = re.sub("['\"״׳`]+", '"', t)
    t = re.sub(r'[-–:]', ' - ', t)
    m = re.search(r'פרק\s+(.+?)(?:\s+-\s+|\s*$)', t)
    if m:
        ph = re.sub(r'\s+', ' ', m.group(1)).strip()
        if ph in _ORD_PH:
            return _ORD_PH[ph]
        if ph in _ORD_LET:
            return _ORD_LET[ph]
    return chapter_ordinal(text)


def plan(before):
    """תכנית: (פרקים, הערות). כל פרק: {i, name, ord, next_open, had(אינדקס או None)}."""
    notes = []
    roles = [role_of(b) for b in before]
    live = lambda i: bool(before[i]['text'].strip())
    raw_open = [i for i, b in enumerate(before) if b['style'] == OPEN_STYLE and live(i)]
    # סינון: סדר עולה; כפילות של פרק שכבר עבר (אותו שם) נזרקת; חזרה ל"ראשון" עם שם אחר מחליפה את מה שלפניה
    acc = []
    for i in raw_open:
        t = before[i]['text']
        o = ordinal(t)
        nm = opening_name(t)
        if o is None:
            notes.append('פתיחת פרק בלי מספר מזוהה (פסקה %d): "%s" - לא נגעתי' % (i, t.strip()[:30]))
            continue
        if acc and o <= acc[-1]['ord']:
            same = [a for a in acc if a['ord'] == o and _pk(a['name']) == _pk(nm)]
            seg_masechet = any(is_had_text(before[k]['text']) is False and 'מסכת' in NIKUD.sub('', before[k]['text'])[:14]
                               and role_of(before[k]) == 'hadran'
                               for k in range(acc[-1]['i'], i))
            if o == acc[-1]['ord'] and _pk(nm) == _pk(acc[-1]['name']):
                notes.append('פתיחת פרק כפולה (פסקה %d): "%s" - דולגה' % (i, t.strip()[:30]))
                continue
            if same:
                notes.append('פתיחת פרק שחוזרת על פרק קודם (פסקה %d): "%s" - דולגה' % (i, t.strip()[:30]))
                continue
            if o == 1 and not seg_masechet:
                notes.append('חזרה ל"פרק ראשון" בלי סיום מסכת (פסקה %d): הפתיחות שלפניה (%d) נחשבות שאריות ואינן מקבלות הדרן'
                             % (i, len(acc)))
                acc = []
            elif o == 1 and seg_masechet:
                pass      # מסכת חדשה בקובץ (עבודה זרה והוריות)
            else:
                notes.append('פתיחת פרק שמספרה אינו עולה (פסקה %d): "%s" - דולגה' % (i, t.strip()[:30]))
                continue
        acc.append({'i': i, 'ord': o, 'name': nm})
    chapters = []
    for n, a in enumerate(acc):
        nxt = next((x for x in raw_open if x > a['i']), len(before))
        a['next_open'] = nxt if nxt < len(before) else None
        a['end'] = nxt
        had = [k for k in range(a['i'] + 1, nxt) if live(k) and is_had_text(before[k]['text'])]
        a['had'] = had[-1] if had else None
        chapters.append(a)
    return chapters, notes, roles


def process(path, slug, dry=False, log=print):
    if is_open_in_word(path) and not wait_free(path, minutes=5, step=60, log=log):
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
    rep = collections.OrderedDict(file=os.path.basename(path), added=0, restyled=0, renamed=0, typo=0,
                                  kept_name=0, no_name=0, notes=[], chapters=[])
    styles, added_style = add_had_style(styles)
    rep['style_added'] = added_style
    ids = _style_ids(styles)
    if HAD_STYLE not in ids:
        raise Refused('אין סגנון "%s"' % HAD_STYLE)
    had_sid = ids[HAD_STYLE][0]
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
    chapters, notes, roles = plan(before)
    rep['notes'] += notes
    all_names = {_pk(c['name']) for c in chapters if c['name']}
    exp_style = {b['i']: b['style'] for b in before}
    exp_text = {b['i']: b['text'] for b in before}
    inserts = collections.defaultdict(list)        # אינדקס פסקה -> [(מצב, טקסט)]: לפניה ('b') או אחריה ('a')
    live_text = lambda p: ''.join(t for _, t, _ in _runs_of(p))
    NBODY = set(NOT_BODY)
    last_body = None
    for i in range(len(before) - 1, -1, -1):
        if before[i]['text'].strip() and roles[i] not in NBODY:
            last_body = i
            break
    for ci, c in enumerate(chapters):
        name = c['name']
        label = 'פרק %d %s' % (c['ord'], name)
        if c['had'] is not None:
            h = c['had']
            p = xml_ps.get(h)
            if p is None:
                continue
            action = []
            sp = split_had(before[h]['text'])
            fix = None
            if sp and name:
                s0, s1, w0, w1 = sp
                ex = before[h]['text'][s0:s1]
                exk = _pk(ex)
                if exk.startswith('פרק') and len(exk) > 4:
                    exk = exk[3:]
                ek = _pk(name)
                generic = bool(re.match(r'^(?:פרק)?(?:ראשון|שני|שלישי|רביעי|חמישי|שישי|שביעי|שמיני|תשיעי|עשירי)$', exk))
                if exk != ek and not exk.startswith(ek) and not ek.startswith(exk):
                    if not generic:
                        # שם שונה מזה שבפתיחה אינו מתוקן מעצמו: לעתים הפתיחה היא הטועה או חסרה (פרק שאין לו פתיחה
                        # בקובץ), וכתיב מסורתי גובר. מדווח בלבד.
                        rep['kept_name'] += 1
                        rep['notes'].append('שם בשורת הדרן שונה מן הפתיחה, לא שונה: "%s" מול פתיחה "%s" (%s)'
                                            % (before[h]['text'].strip()[:40], name, label))
                    elif exk in all_names:
                        rep['kept_name'] += 1
                        rep['notes'].append('שורת הדרן "%s" נושאת שם של פרק אחר - הטקסט לא שונה (%s)'
                                            % (before[h]['text'].strip()[:40], label))
                    elif direct_runs_only(p) and not NIKUD.search(before[h]['text']):
                        fix = (s0, s1, ex, name)
                    else:
                        rep['notes'].append('לא תוקן שם בשורת הדרן (שינוי מעקב של אחר או ניקוד): "%s"'
                                            % before[h]['text'].strip()[:40])
            elif sp and not name:
                rep['no_name'] += 1
                rep['notes'].append('אין שם בשורת הפתיחה, שורת ההדרן לא נבדקה: %s' % label)
            # הסגנון
            if before[h]['style'] != HAD_STYLE:
                if _set_pstyle(p, had_sid, AUTHOR, when, nextid) is not False:
                    exp_style[h] = HAD_STYLE
                    rep['restyled'] += 1
                    action.append('סגנון')
            # תיקון "הדרך"
            if sp and before[h]['text'][sp[2]:sp[3]] == 'הדרך' and direct_runs_only(p):
                full = live_text(p)
                if full[sp[2]:sp[3]] == 'הדרך' and _replace_in_paragraph(p, 'הדרך', 'הדרן', AUTHOR, when, nextid, at=sp[2]):
                    t0 = exp_text[h]
                    exp_text[h] = t0[:sp[2]] + 'הדרן' + t0[sp[3]:]
                    rep['typo'] += 1
                    action.append('הדרך->הדרן')
                    if fix:
                        # היסטים אחרי התיקון זהים (אותו אורך)
                        pass
            if fix:
                s0, s1, ex, new = fix
                full = live_text(p)
                if full[s0:s1] == ex and _replace_in_paragraph(p, ex, new, AUTHOR, when, nextid, at=s0):
                    t0 = exp_text[h]
                    exp_text[h] = t0[:s0] + new + t0[s1:]
                    rep['renamed'] += 1
                    action.append('שם: "%s" -> "%s"' % (ex, new))
                else:
                    rep['notes'].append('לא תוקן שם (ההחלפה סירבה): "%s"' % ex)
            rep['chapters'].append([label, 'קיימת' + (' (' + ', '.join(action) + ')' if action else '')])
            continue
        # אין שורת הדרן בפרק
        if not name:
            rep['no_name'] += 1
            rep['notes'].append('פרק בלי שם בשורת הפתיחה - לא נוספה שורת הדרן: %s' % label)
            rep['chapters'].append([label, 'חסרה: אין שם'])
            continue
        text = 'הדרן עלך ' + name
        if c['next_open'] is not None:
            k = c['next_open']
            while k - 1 > c['i'] and roles[k - 1] in HEADERISH and before[k - 1]['text'].strip():
                k -= 1
            if k not in xml_ps:
                rep['notes'].append('לא נוספה (אין פסקה במקום ההכנסה): %s' % label)
                continue
            inserts[k].append(('b', text))
        else:
            if last_body is None or last_body <= c['i'] or last_body not in xml_ps:
                rep['notes'].append('לא נוספה (אין סוף טקסט ברור לפרק האחרון): %s' % label)
                continue
            inserts[last_body].append(('a', text))
        rep['added'] += 1
        rep['chapters'].append([label, 'נוספה: ' + text])
    # כתיבה של הפסקאות החדשות
    for k, lst in inserts.items():
        at = xml_ps[k]
        par = at.getparent()
        for mode, text in lst:
            p2 = etree.Element(W + 'p')
            pPr2 = etree.SubElement(p2, W + 'pPr')
            etree.SubElement(pPr2, W + 'pStyle').set(W + 'val', had_sid)
            ins = _mark(etree.Element(W + 'ins'), AUTHOR, when, nextid)
            rp = etree.Element(W + 'rPr')
            etree.SubElement(rp, W + 'rFonts').set(W + 'hint', 'cs')
            etree.SubElement(rp, W + 'rtl')
            ins.append(_mkrun(text, rp))
            p2.append(ins)
            _mark_para_end(p2, 'ins', AUTHOR, when, nextid)
            idx = list(par).index(at)
            par.insert(idx if mode == 'b' else idx + 1, p2)
    exp = []
    for b in before:
        i = b['i']
        for mode, text in inserts.get(i, []):
            if mode == 'b':
                exp.append((HAD_STYLE, text))
        exp.append((exp_style[i], exp_text[i]))
        for mode, text in inserts.get(i, []):
            if mode == 'a':
                exp.append((HAD_STYLE, text))
    rep['expected_paragraphs'] = len(exp)
    changed = bool(rep['added'] or rep['restyled'] or rep['renamed'] or rep['typo'] or added_style)
    if not changed:
        rep['changed'] = False
        return rep
    if os.path.getmtime(path) != mtime:
        rep['stale'] = True
        return rep
    tmp = path + ('.dry' if dry else '.new')
    parts = {'word/styles.xml': styles,
             'word/document.xml': etree.tostring(doc, xml_declaration=True, encoding='UTF-8', standalone=True),
             'word/settings.xml': _ensure_track(settings)[0]}
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
    import time, shutil
    try:
        os.replace(tmp, path)
    except OSError:
        # הקובץ (או קובץ הביניים) נתפס בידי תהליך אחר, למשל סנכרון הדרייב. כתיבה במקום, מתוך עותק בתיקייה
        # זמנית, ואימות מיידי; אם נכשל - חוזרים מן הגיבוי.
        scratch = os.path.join(os.environ.get('TEMP', '.'), 'm9-' + os.path.basename(path))
        _rezip(path, scratch, parts)
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass
        if os.path.getmtime(path) != mtime or is_open_in_word(path):
            os.remove(scratch)
            rep['stale'] = True
            return rep
        shutil.copyfile(scratch, path)
        os.remove(scratch)
        chk = [(a['style'], a['text']) for a in convert(path)]
        if chk != exp:
            if bk:
                shutil.copyfile(bk, path)
            rep['verified'] = False
            rep['errors'] = ['אימות אחרי כתיבה במקום נכשל; הקובץ הוחזר מן הגיבוי']
            return rep
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
    ap.add_argument('--out', help='קובץ JSON לדוח')
    a = ap.parse_args()
    reps = []
    for path in files(None if a.all else a.names):
        slug = os.path.splitext(os.path.basename(path))[0]
        r = None
        for attempt in range(3):
            try:
                r = process(path, slug, dry=a.dry)
            except Refused as e:
                r = {'file': os.path.basename(path), 'refused': str(e)}
            except OSError as e:
                for x in (path + '.new', path + '.dry'):
                    if os.path.exists(x):
                        try:
                            os.remove(x)
                        except OSError:
                            pass
                r = {'file': os.path.basename(path), 'refused': 'הקובץ נעול (%s) - לא נכתב' % e}
            if not r.get('stale'):
                break
            print('הקובץ השתנה בזמן העיבוד, מנסה שוב', attempt + 1)
        print(json.dumps(r, ensure_ascii=False))
        reps.append(r)
    if a.out:
        io.open(a.out, 'w', encoding='utf-8').write(json.dumps(reps, ensure_ascii=False, indent=1))
