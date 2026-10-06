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
import os, sys, io, re, json, zipfile, datetime, argparse, collections, difflib, copy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lxml import etree
import word_apply
from word_apply import (ns, W, DRIVE, Refused, convert, _paragraph_map, _rezip, _ensure_track, backup,
                        is_open_in_word, wait_free, _copy_no_change, _mark)
from styles_map import ROLE, CS, TANAI_NAME, TANAI_LEGACY
import mishna_sizes
from m6_word import _live, delete_paragraph, direct_runs_only
from chapter_ord import chapter_ordinal

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
    """יחידות פתיחה של פרק שיושבות אחרי המשנה הראשונה שלו: [(אינדקס הפסקה, אינדקס המשנה הראשונה)].

    זו אותה מכונת מצבים של הבנייה (build_site, "פתיחת פרק לפני המשנה"): שם פרק, ו"תחילת פרק" שמספרה
    כמספר הפרק הפתוח, שיושבים אחרי המשנה הראשונה - עד ההדרן או הפתיחה של הפרק הבא. בוורד שם הפרק
    הוא מסגרת צפה, וכתוב לעתים הרחק אחרי המשנה (בבא מציעא: תשעה פרקים)."""
    out = []
    open_ = None
    for j, b in enumerate(before):
        r = role_of_b(b)
        t = b['text'].strip()
        if not t:
            continue
        if r == 'hadran':
            open_ = None
            continue
        if r in ('perek-num', 'perek-start'):
            if open_ is None or open_['first_m'] is None:
                if open_ is None:
                    open_ = {'ord': chapter_ordinal(b['text']), 'first_m': None}
                elif not open_['ord']:
                    open_['ord'] = chapter_ordinal(b['text'])
            elif r == 'perek-start' and open_['ord'] and chapter_ordinal(b['text']) == open_['ord']:
                out.append((j, open_['first_m']))
            else:
                open_ = {'ord': chapter_ordinal(b['text']), 'first_m': None}
            continue
        if open_ is None:
            continue
        if r == 'mishna':
            if open_['first_m'] is None:
                open_['first_m'] = j
        elif r == 'perek-name' and open_['first_m'] is not None:
            out.append((j, open_['first_m']))
    return out


def _mark_para_end(p, tag, author, when, nextid):
    """סימן הפסקה (ins/del) בתוך pPr/rPr, במקומו בסכימה (אחרי כל המאפיינים, לפני sectPr ו-pPrChange)."""
    pPr = p.find('w:pPr', ns)
    if pPr is None:
        pPr = etree.Element(W + 'pPr')
        p.insert(0, pPr)
    rPr = pPr.find('w:rPr', ns)
    if rPr is None:
        rPr = etree.Element(W + 'rPr')
        pos = len(pPr)
        for k, ch in enumerate(pPr):
            if etree.QName(ch).localname in ('sectPr', 'pPrChange'):
                pos = k
                break
        pPr.insert(pos, rPr)
    for t in ('ins', 'del'):
        for old in rPr.findall('w:' + t, ns):
            rPr.remove(old)
    rPr.insert(0, _mark(etree.Element(W + tag), author, when, nextid))


def copy_paragraph_before(src, dst, author, when, nextid):
    """עותק של פסקת src (אותם מאפייני פסקה, כולל מסגרת צפה, ואותן ריצות) לפני dst, כהוספה במעקב.
    המקור נמחק בנפרד. מחזיר None אם בפסקה יש שינוי מעקב של אדם אחר."""
    if not direct_runs_only(src):
        return None
    p2 = etree.Element(W + 'p')
    pPr = src.find('w:pPr', ns)
    if pPr is not None:
        pp = copy.deepcopy(pPr)
        for e in pp.findall('w:pPrChange', ns):
            pp.remove(e)
        rp = pp.find('w:rPr', ns)
        if rp is not None:
            for t in ('ins', 'del', 'moveFrom', 'moveTo'):
                for e in rp.findall('w:' + t, ns):
                    rp.remove(e)
        p2.append(pp)
    ins = _mark(etree.Element(W + 'ins'), author, when, nextid)
    for r in src.findall('w:r', ns):
        ins.append(copy.deepcopy(r))
    p2.append(ins)
    _mark_para_end(p2, 'ins', author, when, nextid)
    parent = dst.getparent()
    parent.insert(list(parent).index(dst), p2)
    return p2


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
        for j, k in list(moved.items()):
            bj = before[j]
            if copy_paragraph_before(xml_ps[j], xml_ps[k], AUTHOR, when, nextid) is None:
                rep['moved_names'].append(['לא הועבר: שינוי מעקב של אחר', bj['text'][:30]])
                del moved[j]
                continue
            delete_paragraph(xml_ps[j], AUTHOR, when, nextid)
            rep['moved_names'].append([bj['text'].strip(), bj['style'], 'לפני יחידה %d' % k])
    # --- צפוי
    exp = []
    for b in before:
        i = b['i']
        for j, k in moved.items():
            if k == i:
                exp.append((before[j]['style'], before[j]['text']))
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
