# -*- coding: utf-8 -*-
"""m7_word.py - מנת 6.10.2026 (לווקר): גודל המשנה, תנאי המשנה, ד"ה משנה ופתיחת פרק.

מה נעשה בכל קובץ ורד, בהרצה אחת ובגיבוי אחד:
א. הגדרות הסגנון (לא עיצוב ישיר): המשנה גדלה בשתי נקודות, ד"ה משנה = משנה, תנאי המשנה =
   משנה פחות שתיים, הסבר במשנה = משנה פחות אחת (mishna_sizes.py). הסגנון "תנאים במשנה" נקרא
   מעתה "תנאי המשנה". הגדרת סגנון אינה נרשמת במעקב.
ב. כל מופע של "אמוראים" (או סגנון מקביל בשם אחר) בתוך פסקת משנה עובר ל"תנאי המשנה", כשינוי
   עיצוב במעקב. שינוי מעקב קיים של אדם אחר אינו נדרס: הריצה מדלגת עליו ומדווחת.
ג. עיצוב ישיר של גודל (sz/szCs) על ריצות בפסקאות משנה וד"ה מנטרל את הסגנון: מוסר, במעקב.
ד. שם פרק שיושב אחרי המשנה הראשונה של הפרק (בטעות סדר) עובר לפניה, כגוש עצמאי: מחיקה
   והוספה במעקב, בלי לגעת בטקסט. בקובצי הוורד נמצא מקרה כזה אחד בלבד (סוכה פרק ב).
ה. "תחילת פרק" נשאר עם הפסקה הבאה (keepNext בסגנון).

מחבר השינויים: Claude. גיבוי: _שומר\\גיבויים. אימות: המרה חוזרת והשוואה פסקה אחר פסקה.

    uv run --with lxml python tools/m7_word.py <חלק משם הקובץ> ... [--dry]
    uv run --with lxml python tools/m7_word.py --all [--dry]
"""
import os, sys, io, re, json, zipfile, datetime, argparse, collections, difflib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lxml import etree
import word_apply
from word_apply import (ns, W, DRIVE, Refused, convert, _paragraph_map, _rezip, _ensure_track, backup,
                        is_open_in_word, wait_free, _copy_no_change, _mark)
from styles_map import ROLE, CS, TANAI_NAME, TANAI_LEGACY
import mishna_sizes
from m6_word import _live, new_paragraph_before, delete_paragraph

AUTHOR = 'Claude'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AM_NAMES = {n for n, c in CS.items() if c == 'am'} - {TANAI_NAME, TANAI_NAME + ' תו', TANAI_LEGACY, TANAI_LEGACY + ' תו'}
KEEPNEXT_STYLES = ('תחילת פרק',)


def _names(styles_xml):
    root = etree.fromstring(styles_xml)
    sid2name, sid2type, name2char = {}, {}, {}
    for st in root.findall('w:style', ns):
        nm = st.find('w:name', ns)
        sid = st.get(W + 'styleId')
        n = nm.get(W + 'val') if nm is not None else ''
        sid2name[sid] = n
        sid2type[sid] = st.get(W + 'type')
        if st.get(W + 'type') == 'character':
            name2char[n] = sid
    return sid2name, sid2type, name2char


def add_keepnext(styles_xml):
    root = etree.fromstring(styles_xml)
    done = []
    for st in root.findall('w:style', ns):
        nm = st.find('w:name', ns)
        if st.get(W + 'type') != 'paragraph' or nm is None or nm.get(W + 'val') not in KEEPNEXT_STYLES:
            continue
        pPr = st.find('w:pPr', ns)
        if pPr is None:
            pPr = etree.Element(W + 'pPr')
            qf = st.find('w:qFormat', ns)
            st.insert(list(st).index(qf) + 1 if qf is not None else len(st), pPr)
        if pPr.find('w:keepNext', ns) is None:
            pPr.insert(0, etree.Element(W + 'keepNext'))
            done.append(nm.get(W + 'val'))
    return etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True), done


OWN_AUTHORS = ('Claude', 'קלוד')


def _own_change(rp):
    """שינוי עיצוב קיים שכתב אחד הכלים שלי (מנה קודמת): נשמר כמות שהוא (המצב שלפני),
    והשינוי שלי נוסף בתוך אותה ריצה."""
    ch = rp.find('w:rPrChange', ns) if rp is not None else None
    return ch is not None and ch.get(W + 'author') in OWN_AUTHORS


def _has_foreign_change(rp):
    if rp is None:
        return False
    ch = rp.find('w:rPrChange', ns)
    return ch is not None and ch.get(W + 'author') not in OWN_AUTHORS


def modify_run(r, new_sid, strip_size, author, when, nextid):
    """שינוי עיצוב ריצה במעקב: סגנון תו חדש ו/או הסרת גודל ישיר. מחזיר (restyled, stripped) או None אם דולג."""
    rp = r.find('w:rPr', ns)
    want_strip = strip_size and rp is not None and (rp.find('w:sz', ns) is not None or rp.find('w:szCs', ns) is not None)
    if not new_sid and not want_strip:
        return (0, 0)
    if _has_foreign_change(rp):
        return None
    if rp is None:
        rp = etree.Element(W + 'rPr')
        r.insert(0, rp)
    own = _own_change(rp)
    old = None if own else _copy_no_change(rp, 'rPrChange')
    restyled = stripped = 0
    if new_sid:
        cur = rp.find('w:rStyle', ns)
        if cur is None:
            cur = etree.Element(W + 'rStyle')
            rp.insert(0, cur)
        cur.set(W + 'val', new_sid)
        restyled = 1
    if want_strip:
        for tag in ('sz', 'szCs'):
            e = rp.find('w:' + tag, ns)
            if e is not None:
                rp.remove(e)
        stripped = 1
    if not own:
        ch = _mark(etree.Element(W + 'rPrChange'), author, when, nextid)
        ch.append(old)
        rp.append(ch)
    return (restyled, stripped)


def late_chapter_names(before):
    """שמות פרק שיושבים אחרי המשנה הראשונה של הפרק: [(אינדקס השם, אינדקס הפסקה שלפניה יוכנס)]."""
    out = []
    n = len(before)
    for i, b in enumerate(before):
        r = role_of_b(b)
        if r not in ('perek-num', 'perek-start') or not b['text'].strip():
            continue
        seen_m = None
        last_head = i
        for j in range(i + 1, min(n, i + 40)):
            bj = before[j]
            rj = role_of_b(bj)
            if rj in ('skip', 'daf', 'anchor') or not bj['text'].strip():
                continue
            if rj == 'mishna':
                if seen_m is None:
                    seen_m = j
                continue
            if rj in ('perek-name', 'perek-range', 'perek-start', 'perek-num'):
                if seen_m is None:
                    last_head = j
                    continue
                if rj == 'perek-name':
                    out.append((j, seen_m))
                if rj in ('perek-num', 'perek-start'):
                    break
                continue
            break
    return out


def role_of_b(b):
    from styles_map import role_of
    return role_of(b)


def process(path, slug, dry=False, log=print, only=None):
    only = only or {'styles', 'runs', 'sizes', 'chapters'}
    if is_open_in_word(path) and not wait_free(path, log=log):
        raise Refused('הקובץ פתוח בוורד ולא התפנה')
    mtime = os.path.getmtime(path)
    before = convert(path)
    pmap_last = dict(word_apply.convert.last)
    z = zipfile.ZipFile(path)
    doc = etree.fromstring(z.read('word/document.xml'))
    settings = z.read('word/settings.xml')
    styles = z.read('word/styles.xml')
    z.close()
    rep = collections.OrderedDict(file=os.path.basename(path))
    extra = {}
    if 'styles' in only:
        styles, srep = mishna_sizes.sync(styles, raise_once=True)
        styles, kn = add_keepnext(styles)
        rep['sizes'] = {k: srep[k] for k in ('M_old', 'M', 'tanai', 'hs', 'raised', 'renamed')}
        rep['sizes']['created'] = bool(srep.get('created'))
        rep['styles_changed'] = srep['changed']
        rep['keepnext'] = kn
        bad = mishna_sizes.nose_check(styles)
        if bad:
            rep['nose_bigger_than_mishna'] = bad
        extra['word/styles.xml'] = styles
    sid2name, sid2type, name2char = _names(styles)
    tn_sid = name2char.get(TANAI_NAME)
    if tn_sid is None:
        raise Refused('אין סגנון "%s" אחרי היישור' % TANAI_NAME)
    word_apply.convert.last = pmap_last
    xml_ps = _paragraph_map(doc, before)
    counter = [40000]

    def nextid():
        counter[0] += 1
        return counter[0]

    when = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    rep.update(restyled_tn=0, stripped_direct=0, skipped_foreign=0, moved_names=[])
    # --- ב + ג: ריצות בפסקאות משנה וד"ה
    if 'runs' in only or 'sizes' in only:
        for b in before:
            role = role_of_b(b)
            if role not in ('mishna', 'dh'):
                continue
            p = xml_ps.get(b['i'])
            if p is None:
                continue
            for r in list(p.iter(W + 'r')):
                if not _live(r):
                    continue
                rp = r.find('w:rPr', ns)
                new_sid = None
                if 'runs' in only and role == 'mishna' and rp is not None:
                    rs = rp.find('w:rStyle', ns)
                    if rs is not None:
                        sid = rs.get(W + 'val')
                        nm = sid2name.get(sid)
                        # אמוראים (או מקביל) בתוך משנה; וגם מזהה של סגנון פסקה ששימש כסגנון תו (יבמות)
                        if nm in AM_NAMES or (nm in (TANAI_NAME, TANAI_LEGACY) and sid != tn_sid
                                              or (sid2type.get(sid) == 'paragraph' and nm in (TANAI_LEGACY,))):
                            new_sid = tn_sid
                res = modify_run(r, new_sid, 'sizes' in only, AUTHOR, when, nextid)
                if res is None:
                    rep['skipped_foreign'] += 1
                    continue
                rep['restyled_tn'] += res[0]
                rep['stripped_direct'] += res[1]
    # --- ד: שם פרק שאחרי המשנה הראשונה
    moved = {}
    if 'chapters' in only:
        for j, target in late_chapter_names(before):
            bj = before[j]
            # היעד: לפני תווית "משנה בצד" (או ציון הדף) הצמודים למשנה הראשונה
            k = target
            while k - 1 >= 0 and role_of_b(before[k - 1]) in ('skip', 'daf', 'anchor') and k - 1 > 0 \
                    and before[k - 1]['style'] != before[j]['style']:
                k -= 1
            moved[j] = k
        for j, k in moved.items():
            bj = before[j]
            sid = {v: k2 for k2, v in sid2name.items() if sid2type.get(k2) == 'paragraph'}.get(bj['style'])
            if sid is None:
                rep['moved_names'].append(['לא הועבר: אין סגנון', bj['text'][:30]])
                continue
            new_paragraph_before(xml_ps[k], bj['text'].strip() + ' ' if bj['text'].endswith(' ') else bj['text'],
                                 sid, AUTHOR, when, nextid)
            delete_paragraph(xml_ps[j], AUTHOR, when, nextid)
            rep['moved_names'].append([bj['text'].strip(), 'לפני יחידה %d' % k])
    # --- צפוי
    exp = []
    for b in before:
        i = b['i']
        for j, k in moved.items():
            if k == i:
                exp.append((before[j]['style'], before[j]['text'].strip() + ' ' if before[j]['text'].endswith(' ') else before[j]['text']))
        if i in moved:
            continue
        exp.append((b['style'], b['text']))
    rep['expected_paragraphs'] = len(exp)
    changed = bool(rep['restyled_tn'] or rep['stripped_direct'] or moved or rep.get('styles_changed')
                   or rep.get('keepnext') or rep.get('sizes', {}).get('renamed') or rep.get('sizes', {}).get('created'))
    if dry:
        rep['dry'] = True
        return rep
    if not changed:
        rep['changed'] = False
        return rep
    if os.path.getmtime(path) != mtime:
        rep['stale'] = True
        return rep
    tmp = path + '.new'
    parts = dict(extra)
    parts['word/document.xml'] = etree.tostring(doc, xml_declaration=True, encoding='UTF-8', standalone=True)
    parts['word/settings.xml'] = _ensure_track(settings)[0]
    _rezip(path, tmp, parts)
    after = convert(tmp)
    got = [(a['style'], a['text']) for a in after]
    bad = []
    if got != exp:
        sm = difflib.SequenceMatcher(None, got, exp, autojunk=False)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag != 'equal':
                bad.append('%s: קיבלנו %r ציפינו %r' % (tag, got[i1:i2][:2], exp[j1:j2][:2]))
                if len(bad) >= 6:
                    break
    try:
        zz = zipfile.ZipFile(tmp)
        assert zz.testzip() is None
        for n in ('word/document.xml', 'word/styles.xml', 'word/settings.xml'):
            etree.fromstring(zz.read(n))
        # אימות הגדלים בפועל: M, ד"ה משנה, תנאי המשנה, נושא
        rootv = etree.fromstring(zz.read('word/styles.xml'))
        stv = mishna_sizes._styles(rootv)
        Mv = mishna_sizes.mishna_size(rootv)
        for sid, (st, nm) in stv.items():
            if st.get(W + 'type') == 'paragraph' and ROLE.get(nm) == 'dh':
                v = mishna_sizes.eff(stv, sid, 'szCs')
                if v != Mv:
                    bad.append('ד"ה משנה "%s": %s במקום %s' % (nm, v, Mv))
            if st.get(W + 'type') == 'character' and nm == TANAI_NAME:
                v = mishna_sizes.eff(stv, sid, 'szCs')
                if v != Mv - 4:
                    bad.append('תנאי המשנה: %s במקום %s' % (v, Mv - 4))
        zz.close()
    except Exception as e:
        bad.append('הקובץ החדש אינו תקין: %s' % e)
    if bad:
        os.remove(tmp)
        rep['verified'] = False
        rep['errors'] = bad
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
    only = set(a.only.split(',')) if a.only else None
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
