# -*- coding: utf-8 -*-
"""word_apply.py - השער היחיד לכתיבה לקובצי הוורד.

כל מה שנכנס לוורד עובר דרך כאן בלבד: אישורי הגהה, עריכות שנעשו באתר,
ובעתיד הצעות שאושרו. הסיבה פשוטה: קובץ הוורד הוא מקור האמת של בעל
הפרויקט, וכל נגיעה בו חייבת להיות הפיכה, מסומנת במעקב, ומאומתת.

מה הכלי מבטיח:
א. קובץ שפתוח בוורד (יש לידו קובץ נעילה ~$) אינו נכתב. הכלי ממתין,
   ואם לא התפנה - מדלג ורושם. לעולם לא כותב על קובץ פתוח.
ב. גיבוי מלא לפני כל נגיעה, ב-_שומר\\גיבויים (ולא בשורש תיקיית הדרייב,
   שם הוא היה נבנה כמסכת נוספת באתר).
ג. הקובץ מקבל w:trackRevisions, כדי שגם עריכה של בעל הפרויקט עצמו
   תסומן מעתה.
ד. החלפה מינימלית בלבד: רק המילים שהשתנו נמחקות ונוספות, במעקב, בשם
   המחבר שנמסר. שאר הפסקה אינה נוגעת.
ה. אחרי הכתיבה הקובץ מומר שוב ומושווה למה שהיה. אם השתנה משהו שלא
   אושר, או שמספר השינויים אינו כמספר התיקונים - הקובץ מוחזר מן
   הגיבוי, והכישלון נאמר בקול.
ו. אם הקובץ השתנה על הדיסק מאז שנקרא, הוא נקרא מחדש והתיקונים נבנים
   מחדש עליו.

אין כאן שום מחיקה ממשית, ואין קבלה או דחייה של שינוי קיים.
"""
import os, sys, json, shutil, time, zipfile, datetime, argparse, io

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lxml import etree
from docx2json import convert
import hagaha

NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
ns = {'w': NS}
W = '{%s}' % NS

DRIVE = r'C:\Users\Owner\Desktop\שיננא לHTML'
BACKUPS = os.path.join(DRIVE, '_שומר', 'גיבויים')


class Refused(Exception):
    """הכלי סירב לכתוב. תמיד בקול, לעולם לא בשקט."""


# ---------------------------------------------------------------- נעילה

def lock_path(path):
    d, n = os.path.split(path)
    # וורד קוצץ את שם קובץ הנעילה בשני תווים כשהשם ארוך
    return [os.path.join(d, '~$' + n), os.path.join(d, '~$' + n[2:])]


def is_open_in_word(path):
    return any(os.path.exists(p) for p in lock_path(path))


def wait_free(path, minutes=60, step=600, log=print):
    """ממתין עד שהקובץ ייסגר בוורד. מחזיר True אם התפנה."""
    waited = 0
    while is_open_in_word(path):
        if waited >= minutes * 60:
            log('הקובץ עדיין פתוח בוורד אחרי %d דקות - מדלג' % minutes)
            return False
        log('הקובץ פתוח בוורד. ממתין %d שניות' % step)
        time.sleep(step)
        waited += step
    return True


# ---------------------------------------------------------------- גיבוי

def backup(path, masechet):
    os.makedirs(BACKUPS, exist_ok=True)
    stamp = datetime.datetime.now().strftime('%d.%m.%Y %H-%M-%S')
    dst = os.path.join(BACKUPS, '%s %s.docx' % (masechet, stamp))
    shutil.copy2(path, dst)
    return dst


# ------------------------------------------------------ עריכת ה-XML

def _rpr(run):
    rp = run.find('w:rPr', ns)
    return etree.fromstring(etree.tostring(rp)) if rp is not None else None


def _mkrun(text, rpr, deleted=False):
    r = etree.SubElement(etree.Element('x'), W + 'r')
    if rpr is not None:
        r.append(etree.fromstring(etree.tostring(rpr)))
    t = etree.SubElement(r, W + ('delText' if deleted else 't'))
    t.text = text
    t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
    return r


def _runs_of(p):
    """הרצות החיות של הפסקה, ומיקום כל אחת בתוך הטקסט המלא."""
    out, pos = [], 0
    for r in p.iter(W + 'r'):
        el, dead = r.getparent(), False
        while el is not None and el.tag != W + 'p':
            if el.tag in (W + 'del', W + 'moveFrom'):
                dead = True
                break
            el = el.getparent()
        if dead:
            continue
        txt = ''.join((t.text or '') if t.tag == W + 't' else ('\t' if t.tag == W + 'tab' else '')
                      for t in r if t.tag in (W + 't', W + 'tab'))
        if not txt:
            continue
        out.append((pos, txt, r))
        pos += len(txt)
    return out


def _replace_in_paragraph(p, find, repl, author, when, nextid, at=None):
    """מחליף מופע אחד של find ב-repl, במעקב. מחזיר True אם הצליח.

    הסימון עשוי להתפרש על כמה קטעי-תו, מפני שוורד מפצל הרצות גם בלא
    שינוי עיצוב. לכן ההחלפה חותכת כל קטע שנוגע בסימון, מוחקת את החלק
    שבתוכו, ושותלת את הנוסח החדש במקום הראשון - בעיצוב שהיה שם.
    קטע שכבר יושב בתוך שינוי-מעקב קיים אינו נוגע, ומדווח."""
    runs = _runs_of(p)
    full = ''.join(t for _, t, _ in runs)
    k = full.find(find) if at is None else at
    if k < 0 or full[k:k + len(find)] != find:
        return False
    lo, hi = k, k + len(find)
    touched = [(pos, txt, r) for pos, txt, r in runs if pos < hi and pos + len(txt) > lo]
    if not touched:
        return False
    # קטע שיושב בתוך w:ins או w:del קיים - לא נוגעים, כדי שלא לשנות
    # שינוי שבעל הפרויקט טרם קיבל או דחה.
    for _, _, r in touched:
        if r.getparent().tag != W + 'p':
            return False
    first = True
    for pos, txt, r in touched:
        a = max(lo - pos, 0)
        b = min(hi - pos, len(txt))
        rpr = _rpr(r)
        parent = r.getparent()
        idx = list(parent).index(r)
        new = []
        if txt[:a]:
            new.append(_mkrun(txt[:a], rpr))
        d = etree.Element(W + 'del')
        d.set(W + 'id', str(nextid()))
        d.set(W + 'author', author)
        d.set(W + 'date', when)
        d.append(_mkrun(txt[a:b], rpr, deleted=True))
        new.append(d)
        if first and repl:
            i = etree.Element(W + 'ins')
            i.set(W + 'id', str(nextid()))
            i.set(W + 'author', author)
            i.set(W + 'date', when)
            i.append(_mkrun(repl, rpr))
            new.append(i)
        first = False
        if txt[b:]:
            new.append(_mkrun(txt[b:], rpr))
        parent.remove(r)
        for n, el in enumerate(new):
            parent.insert(idx + n, el)
    return True


def _ensure_track(settings_xml):
    """מוסיף w:trackRevisions להגדרות הקובץ, אם אינו שם."""
    root = etree.fromstring(settings_xml)
    if root.find('w:trackRevisions', ns) is not None:
        return settings_xml, False
    el = etree.Element(W + 'trackRevisions')
    # הסדר בסכימה מחייב: trackRevisions בא אחרי proofState/documentProtection
    after = ['zoom', 'proofState', 'defaultTabStop', 'documentProtection']
    pos = 0
    for n, child in enumerate(root):
        if etree.QName(child).localname in after:
            pos = n + 1
    root.insert(pos, el)
    return etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True), True


def _rezip(src, dst, replace):
    """כותב עותק של הקובץ, ובו רק החלקים שהוחלפו שונים."""
    zin = zipfile.ZipFile(src)
    with zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = replace.get(item.filename, zin.read(item.filename))
            zout.writestr(item, data)
    zin.close()


# ------------------------------------------------------ סגנונות (ו3ד)

def _style_ids(styles_xml):
    """מפה משם הסגנון כפי שבעל הפרויקט רואה אותו בוורד אל ה-styleId.

    הסגנונות נבחרים באתר לפי השם השכיח בקובץ הזה עצמו, ולכן שם שאינו
    כאן פירושו שמשהו זז - ואין להמציא סגנון חדש. מדווחים ומדלגים."""
    root = etree.fromstring(styles_xml)
    out = {}
    for st in root.findall('w:style', ns):
        nm = st.find('w:name', ns)
        sid = st.get(W + 'styleId')
        if nm is not None and sid:
            out[nm.get(W + 'val')] = (sid, st.get(W + 'type') or 'paragraph')
        if sid:
            out.setdefault(sid, (sid, st.get(W + 'type') or 'paragraph'))
    return out


def _copy_no_change(el, tag):
    """עותק של pPr/rPr בלי רישום שינוי קודם שבתוכו."""
    c = etree.fromstring(etree.tostring(el))
    for ch in c.findall('w:' + tag, ns):
        c.remove(ch)
    return c


def _mark(el, author, when, nextid):
    el.set(W + 'id', str(nextid()))
    el.set(W + 'author', author)
    el.set(W + 'date', when)
    return el


def _set_pstyle(p, sid, author, when, nextid):
    """מחליף את סגנון הפסקה ורושם את הקודם ב-w:pPrChange."""
    pPr = p.find('w:pPr', ns)
    if pPr is None:
        pPr = etree.Element(W + 'pPr')
        p.insert(0, pPr)
    old = _copy_no_change(pPr, 'pPrChange')
    cur = pPr.find('w:pStyle', ns)
    if cur is not None and cur.get(W + 'val') == sid:
        return False
    for ch in pPr.findall('w:pPrChange', ns):
        pPr.remove(ch)
    if cur is None:
        cur = etree.Element(W + 'pStyle')
        pPr.insert(0, cur)
    cur.set(W + 'val', sid)
    ch = _mark(etree.Element(W + 'pPrChange'), author, when, nextid)
    ch.append(old)
    pPr.append(ch)
    return True


def _set_cstyle(p, find, sid, author, when, nextid):
    """מחיל סגנון תו על קטע טקסט, ורושם את העיצוב הקודם ב-w:rPrChange.

    sid ריק פירושו הסרת הסגנון. הטקסט עצמו אינו נוגע כלל."""
    runs = _runs_of(p)
    full = ''.join(t for _, t, _ in runs)
    k = full.find(find)
    if k < 0 or full.count(find) > 1:
        return False
    lo, hi = k, k + len(find)
    touched = [(pos, txt, r) for pos, txt, r in runs if pos < hi and pos + len(txt) > lo]
    if not touched:
        return False
    for _, _, r in touched:
        if r.getparent().tag != W + 'p':
            return False
    for pos, txt, r in touched:
        a = max(lo - pos, 0)
        b = min(hi - pos, len(txt))
        rpr = _rpr(r)
        parent = r.getparent()
        idx = list(parent).index(r)
        new = []
        if txt[:a]:
            new.append(_mkrun(txt[:a], rpr))
        mid = _mkrun(txt[a:b], rpr)
        mp = mid.find('w:rPr', ns)
        if mp is None:
            mp = etree.Element(W + 'rPr')
            mid.insert(0, mp)
        old = _copy_no_change(mp, 'rPrChange')
        for ch in mp.findall('w:rPrChange', ns):
            mp.remove(ch)
        cur = mp.find('w:rStyle', ns)
        if sid:
            if cur is None:
                cur = etree.Element(W + 'rStyle')
                mp.insert(0, cur)
            cur.set(W + 'val', sid)
        elif cur is not None:
            mp.remove(cur)
        ch = _mark(etree.Element(W + 'rPrChange'), author, when, nextid)
        ch.append(old)
        mp.append(ch)
        new.append(mid)
        if txt[b:]:
            new.append(_mkrun(txt[b:], rpr))
        parent.remove(r)
        for n, el in enumerate(new):
            parent.insert(idx + n, el)
    return True


def _anchor_one(blocks, op):
    """עוגן לשינוי סגנון: התאמה אחת ויחידה של הפסקה כולה. שינוי סגנון
    אינו משנה טקסט, ולכן אין לו "מה להחליף" שיאמת אותו - והדרך היחידה
    שלא ליפול על פסקה זרה היא לדרוש ייחוד."""
    ctx = op.get('context') or ''
    if not ctx:
        return None
    hits = [b for b in blocks if b['text'] == ctx]
    if len(hits) != 1:
        hits = [b for b in blocks if ctx in b['text']]
    return hits[0] if len(hits) == 1 else None


# ---------------------------------------------------------------- הראשי

def apply(path, ops, author, masechet, log=print, dry=False):
    """מחיל רשימת תיקונים על קובץ וורד. כל תיקון: {id, daf, context, find, replace}.

    מחזיר דוח. אינו מרים חריגה על תיקון שלא אותר - הוא נספר ומדווח,
    כי דילוג שקט הוא האויב."""
    if is_open_in_word(path) and not wait_free(path, log=log):
        raise Refused('הקובץ פתוח בוורד ולא התפנה')
    mtime = os.path.getmtime(path)
    before = convert(path)

    # איתור כל תיקון בפסקה שלו, לפי ההקשר ולא לפי מספר פסקה
    plan, splan, missed = [], [], []
    for op in ops:
        kind = op.get('kind') or 'text'
        if kind in ('pstyle', 'cstyle'):
            b = _anchor_one(before, op)
            if b is None:
                missed.append((op, 'לא אותרה פסקה יחידה לשינוי הסגנון'))
                continue
            if kind == 'cstyle' and (op.get('find') or '') not in b['text']:
                missed.append((op, 'הטקסט לסגנון אינו בפסקה שאותרה'))
                continue
            splan.append((b['i'], op))
            continue
        hit = hagaha.anchor(before, op)
        if hit is None:
            missed.append((op, 'לא אותרה הפסקה'))
            continue
        b, how = hit
        if op['find'] not in b['text']:
            missed.append((op, 'הטקסט להחלפה אינו בפסקה שאותרה'))
            continue
        plan.append((b['i'], op, how))
    if not plan and not splan:
        return {'applied': 0, 'missed': missed, 'backup': None, 'verified': True}
    if dry:
        return {'applied': len(plan) + len(splan), 'missed': missed, 'backup': None,
                'verified': None,
                'plan': [(i, o['find'], o['replace']) for i, o, _ in plan]
                        + [(i, o.get('kind'), o.get('style')) for i, o in splan]}

    if os.path.getmtime(path) != mtime:
        log('הקובץ השתנה על הדיסק בזמן התכנון. קורא מחדש')
        return apply(path, ops, author, masechet, log=log)

    bk = backup(path, masechet)
    log('גיבוי: ' + bk)

    z = zipfile.ZipFile(path)
    doc = etree.fromstring(z.read('word/document.xml'))
    settings = z.read('word/settings.xml')
    styles = z.read('word/styles.xml')
    z.close()
    sids = _style_ids(styles)

    counter = [9000]

    def nextid():
        counter[0] += 1
        return counter[0]

    when = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    # מיפוי אינדקס-הפסקה שבהמרה אל אלמנט ה-XML. ההמרה מדלגת על toc
    # ועל פסקאות שנמחקו כליל, ולכן המיפוי נבנה באותו סדר בדיוק.
    xml_ps = _paragraph_map(doc, before)
    done, expect = 0, {}
    for i, op, how in plan:
        p = xml_ps.get(i)
        if p is None:
            missed.append((op, 'הפסקה לא נמצאה ב-XML'))
            continue
        if _replace_in_paragraph(p, op['find'], op['replace'], author, when, nextid):
            done += 1
            expect.setdefault(i, []).append((op['find'], op['replace']))
        else:
            missed.append((op, 'הסימון פרוש על כמה קטעי-תו ולא הוחלף'))

    # --- שינויי סגנון ---
    want_style = {}
    for i, op in splan:
        p = xml_ps.get(i)
        if p is None:
            missed.append((op, 'הפסקה לא נמצאה ב-XML'))
            continue
        name = op.get('style') or ''
        sid = ''
        if name:
            if name not in sids:
                missed.append((op, 'הסגנון %r אינו קיים בקובץ הזה' % name))
                continue
            sid = sids[name][0]
        if op['kind'] == 'pstyle':
            if not name:
                missed.append((op, 'סגנון פסקה ריק - אין לאן להחזיר'))
                continue
            if _set_pstyle(p, sid, author, when, nextid):
                want_style[i] = name
                done += 1
            else:
                missed.append((op, 'הפסקה כבר בסגנון הזה'))
        else:
            if _set_cstyle(p, op.get('find') or '', sid, author, when, nextid):
                done += 1
            else:
                missed.append((op, 'הקטע אינו יחיד בפסקה, או שהוא בתוך שינוי-מעקב'))

    tmp = path + '.new'
    _rezip(path, tmp, {'word/document.xml':
                       etree.tostring(doc, xml_declaration=True, encoding='UTF-8', standalone=True),
                       'word/settings.xml': _ensure_track(settings)[0]})

    # --- אימות: להמיר מחדש ולהשוות ---
    after = convert(tmp)
    bad = _diff_check(before, after, expect, want_style)
    if bad:
        os.remove(tmp)
        log('האימות נכשל. הקובץ לא נגע:')
        for line in bad[:8]:
            log('   ' + line)
        return {'applied': 0, 'missed': missed, 'backup': bk, 'verified': False, 'errors': bad}

    os.replace(tmp, path)
    log('נכתבו %d תיקונים, ואומתו' % done)
    return {'applied': done, 'missed': missed, 'backup': bk, 'verified': True}


# ------------------------------------------- מבנה: פיצול פסקה ואיחויה (ו2ו)

def _mark_para(p, tag, author, when, nextid):
    """מסמן את סימן-הפסקה עצמו כמוסף (ins) או כנמחק (del).

    זו הדרך שבה וורד עצמו רושם פיצול ואיחוי במעקב-שינויים: הסימן יושב
    ב-pPr/rPr של הפסקה הראשונה, ובעל הפרויקט יכול לקבל או לדחות אותו
    ככל שינוי אחר."""
    pPr = p.find('w:pPr', ns)
    if pPr is None:
        pPr = etree.Element(W + 'pPr')
        p.insert(0, pPr)
    rPr = pPr.find('w:rPr', ns)
    if rPr is None:
        rPr = etree.Element(W + 'rPr')
        # בסכימה rPr בא אחרי pStyle ולפני שאר המאפיינים
        after = pPr.find('w:pStyle', ns)
        pPr.insert(list(pPr).index(after) + 1 if after is not None else 0, rPr)
    for t in ('ins', 'del'):
        for old in rPr.findall('w:' + t, ns):
            rPr.remove(old)
    el = _mark(etree.Element(W + tag), author, when, nextid)
    rPr.insert(0, el)


def _split_paragraph(p, at, author, when, nextid):
    """מפצל פסקה בנקודה at (מספר תווים מתחילתה) לשתי פסקאות.

    הפסקה הראשונה מקבלת סימן-פסקה חדש המסומן כמוסף; השנייה יורשת את
    הסימן המקורי ואת כל מאפייני הפסקה."""
    runs = _runs_of(p)
    full = ''.join(t for _, t, _ in runs)
    if at <= 0 or at >= len(full):
        return None
    parent = p.getparent()
    idx = list(parent).index(p)
    p2 = etree.Element(W + 'p')
    pPr = p.find('w:pPr', ns)
    if pPr is not None:
        p2.append(etree.fromstring(etree.tostring(pPr)))
    moved = False
    for pos, txt, r in runs:
        if r.getparent().tag != W + 'p':
            return None                  # יושב בתוך שינוי-מעקב קיים
        if pos >= at:
            p.remove(r)
            p2.append(r)
            moved = True
        elif pos < at < pos + len(txt):
            k = at - pos
            rpr = _rpr(r)
            head = _mkrun(txt[:k], rpr)
            tail = _mkrun(txt[k:], rpr)
            i = list(p).index(r)
            p.remove(r)
            p.insert(i, head)
            p2.append(tail)
            moved = True
    if not moved:
        return None
    _mark_para(p, 'ins', author, when, nextid)
    parent.insert(idx + 1, p2)
    return p2


def _norm_map(raw):
    """הטקסט המנורמל, ולצדו מיקומו של כל תו בטקסט הגולמי.

    האתר מציג את הטקסט אחרי שרווחים כפולים וטאבים כווצו לרווח אחד,
    והוורד שומר אותם כמות שהם. בלי הנרמול הזה שום פסקה לא היתה
    מאותרת - נמדד: "פסולה,    לר\"י" בוורד מול "פסולה,  לר\"י" באתר."""
    out, idx, prev = [], [], ' '
    for i, ch in enumerate(raw or ''):
        if ch == '‏':
            continue
        c = ' ' if ch.isspace() else ch
        if c == ' ' and prev == ' ':
            continue
        out.append(c)
        idx.append(i)
        prev = c
    s = ''.join(out)
    t = s.rstrip()
    return t, idx[:len(t)]


def _nw(t):
    return _norm_map(t)[0]


def _apply_split_merge(path, ops, author, masechet, log=print, dry=False):
    """מחיל פיצול פסקה ואיחויה. נפרד מ-apply מפני שכאן מספר הפסקאות
    משתנה, והאימות הוא השוואה מלאה של רשימת הנוסחים לרשימה הצפויה.

    כל אופ: {kind: psplit|pmerge, texts: [...], res: [...]}"""
    if is_open_in_word(path) and not wait_free(path, log=log):
        raise Refused('הקובץ פתוח בוורד ולא התפנה')
    before = convert(path)
    texts_before = [b['text'] for b in before]
    norm_before = [_nw(t) for t in texts_before]

    plan, missed = [], []
    for op in ops:
        want = [_nw(x) for x in (op.get('texts') or [])]
        res = op.get('res') or []
        hits = [i for i in range(len(before) - len(want) + 1)
                if norm_before[i:i + len(want)] == want]
        if len(hits) != 1:
            # מקרה שכיח ומובן: באתר שתי הפסקאות סמוכות, ובוורד יושבת
            # ביניהן פסקה שהאתר אינו מציג - חלון צד או סמן פריסה.
            # איחוי כזה היה מוחק תוכן של בעל הפרויקט, ולכן אינו נכתב.
            why = 'לא אותר רצף פסקאות יחיד (%d מועמדים)' % len(hits)
            if len(want) == 2 and not hits:
                at = [n for n, t in enumerate(norm_before) if t == want[0]]
                for n in at:
                    nxt = [m for m in range(n + 1, min(n + 4, len(before)))
                           if norm_before[m] == want[1]]
                    if nxt:
                        mid = [before[m]['style'] for m in range(n + 1, nxt[0])]
                        why = ('בוורד יושבת בין שתי הפסקאות פסקה שאינה מוצגת '
                               'באתר (%s). האיחוי מוצג באתר ואינו נכתב לוורד, '
                               'כדי שלא יימחק תוכן' % ', '.join(mid))
                        break
            missed.append((op, why))
            continue
        plan.append((hits[0], op, res))
    if not plan:
        return {'applied': 0, 'missed': missed, 'backup': None, 'verified': True}

    # הנוסחים הצפויים אחרי הפעולה. ההמרה מכבדת סימן-פסקה שנמחק במעקב
    # ומאחדת את שתי הפסקאות כבר עתה - נמדד. לכן איחוי גורע פסקה בדיוק
    # כשם שפיצול מוסיף אחת, והאתר יראה את השינוי מיד.
    want_after = list(norm_before)
    for i, op, res in sorted(plan, key=lambda x: -x[0]):
        want_after[i:i + len(op.get('texts') or [])] = [_nw(x) for x in res]
    if dry:
        return {'applied': len(plan), 'missed': missed, 'backup': None,
                'verified': None,
                'plan': [(i, o['kind']) for i, o, _ in plan]}

    bk = backup(path, masechet)
    log('גיבוי: ' + bk)
    z = zipfile.ZipFile(path)
    doc = etree.fromstring(z.read('word/document.xml'))
    settings = z.read('word/settings.xml')
    z.close()
    counter = [9500]

    def nextid():
        counter[0] += 1
        return counter[0]

    when = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    xml_ps = _paragraph_map(doc, before)
    done = 0
    # מן הסוף להתחלה: פיצול מוסיף פסקה ומזיז את כל מה שאחריה.
    for i, op, res in sorted(plan, key=lambda x: -x[0]):
        p = xml_ps.get(before[i]['i'])
        if p is None:
            missed.append((op, 'הפסקה לא נמצאה ב-XML'))
            continue
        if op['kind'] == 'psplit':
            # נקודת החיתוך נמדדת על הטקסט המנורמל, ומתורגמת למקומה
            # בטקסט הגולמי שבוורד.
            nm, idx = _norm_map(before[i]['text'])
            k = len(_nw(res[0]))
            at = idx[k] if k < len(idx) else len(before[i]['text'])
            if _split_paragraph(p, at, author, when, nextid) is None:
                missed.append((op, 'לא ניתן לפצל כאן'))
                continue
        else:
            _mark_para(p, 'del', author, when, nextid)
        done += 1

    tmp = path + '.new'
    _rezip(path, tmp, {'word/document.xml':
                       etree.tostring(doc, xml_declaration=True, encoding='UTF-8',
                                      standalone=True),
                       'word/settings.xml': _ensure_track(settings)[0]})
    after = convert(tmp)
    got = [_nw(b['text']) for b in after]
    if got != want_after:
        os.remove(tmp)
        bad = next((n for n in range(min(len(got), len(want_after)))
                    if got[n] != want_after[n]), min(len(got), len(want_after)))
        log('האימות נכשל. הקובץ לא נגע.')
        log('   ציפינו: %r' % (want_after[bad:bad + 1],))
        log('   קיבלנו: %r' % (got[bad:bad + 1],))
        return {'applied': 0, 'missed': missed, 'backup': bk, 'verified': False}
    os.replace(tmp, path)
    log('נכתבו %d שינויי מבנה, ואומתו' % done)
    return {'applied': done, 'missed': missed, 'backup': bk, 'verified': True}


# ------------------------------------- כותרת צד: Ctrl+נקודה (pside / punside)

def apply_struct(path, ops, author, masechet, log=print, dry=False):
    """מפצל לפי סוג: פיצול ואיחוי בפונקציה הישנה, כותרת צד בחדשה.
    סוג לא מוכר אינו נופל לאיחוי - הוא נספר כלא-הוחל."""
    old = [o for o in ops if o.get('kind') in ('psplit', 'pmerge')]
    side = [o for o in ops if o.get('kind') in ('pside', 'punside')]
    rest = [o for o in ops if o not in old and o not in side]
    out = {'applied': 0, 'missed': [(o, 'סוג שינוי מבנה לא מוכר') for o in rest],
           'backup': None, 'verified': True}
    for fn, batch in ((_apply_split_merge, old), (_apply_side, side)):
        if not batch:
            continue
        r = fn(path, batch, author, masechet, log=log, dry=dry)
        out['applied'] += r.get('applied') or 0
        out['missed'] += r.get('missed') or []
        out['backup'] = out['backup'] or r.get('backup')
        if r.get('verified') is False:
            out['verified'] = False
        if 'plan' in r:
            out.setdefault('plan', []).extend(r['plan'])
    return out


def _common_style(blocks, pred):
    from collections import Counter
    c = Counter(b['style'] for b in blocks if pred(b['style']))
    return c.most_common(1)[0][0] if c else None


def _apply_side(path, ops, author, masechet, log=print, dry=False):
    """כותרת צד. pside: res=[נוסח הגוף, נוסח החלון], cut=[היסט, אורך] בתוך
    הנוסח שהיה. פסקה שכולה הופכת לחלון בשינוי סגנון; אחרת נוספת פסקת חלון
    לפניה, והמילה נמחקת מן הגוף - הכול במעקב. punside: חלון חוזר לגוף
    בשינוי סגנון."""
    from styles_map import ROLE
    if is_open_in_word(path) and not wait_free(path, log=log):
        raise Refused('הקובץ פתוח בוורד ולא התפנה')
    before = convert(path)
    norm_before = [_nw(b['text']) for b in before]
    win_style = _common_style(before, lambda s: ROLE.get(s) == 'anchor' and s == 'חלון 3') \
        or _common_style(before, lambda s: ROLE.get(s) == 'anchor')
    body_default = _common_style(before, lambda s: ROLE.get(s, 'body') == 'body') or 'Normal'
    plan, missed = [], []
    for op in ops:
        want = [_nw(x) for x in (op.get('texts') or [])]
        res = op.get('res') or []
        if not want or not res:
            missed.append((op, 'רשומה חסרה'))
            continue
        if op['kind'] == 'pside':
            hits = [i for i in range(len(before)) if norm_before[i] == want[0]
                    and ROLE.get(before[i]['style'], 'body').startswith('body')]
            if len(hits) != 1:
                missed.append((op, 'לא אותרה פסקה יחידה (%d מועמדים)' % len(hits)))
                continue
            if not win_style:
                missed.append((op, 'אין בקובץ סגנון חלון'))
                continue
            plan.append((hits[0], op))
        else:
            nxt = want[1] if len(want) > 1 else ''
            hits = [i for i in range(len(before) - 1)
                    if norm_before[i] == want[0] and ROLE.get(before[i]['style']) == 'anchor'
                    and (not nxt or norm_before[i + 1] == nxt)]
            if len(hits) != 1:
                missed.append((op, 'לא אותר חלון יחיד (%d מועמדים)' % len(hits)))
                continue
            plan.append((hits[0], op))
    if not plan:
        return {'applied': 0, 'missed': missed, 'backup': None, 'verified': True}

    want_after = list(norm_before)
    want_style = {}
    for i, op in sorted(plan, key=lambda x: -x[0]):
        res = op.get('res') or []
        if op['kind'] == 'pside':
            body_t, win_t = _nw(res[0]), _nw(res[1])
            if body_t:
                want_after[i:i + 1] = [win_t, body_t]
            else:
                want_style[i] = win_style
        else:
            nxt_i = i + 1
            want_style[i] = (before[nxt_i]['style']
                             if ROLE.get(before[nxt_i]['style'], 'body').startswith('body')
                             else body_default)
    if dry:
        return {'applied': len(plan), 'missed': missed, 'backup': None, 'verified': None,
                'plan': [(i, o['kind']) for i, o in plan]}

    bk = backup(path, masechet)
    log('גיבוי: ' + bk)
    z = zipfile.ZipFile(path)
    doc = etree.fromstring(z.read('word/document.xml'))
    settings = z.read('word/settings.xml')
    sids = _style_ids(z.read('word/styles.xml'))
    z.close()
    counter = [9800]

    def nextid():
        counter[0] += 1
        return counter[0]

    when = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    xml_ps = _paragraph_map(doc, before)
    done = 0
    for i, op in sorted(plan, key=lambda x: -x[0]):
        p = xml_ps.get(before[i]['i'])
        if p is None:
            missed.append((op, 'הפסקה לא נמצאה ב-XML'))
            continue
        res = op.get('res') or []
        if op['kind'] == 'punside':
            sid = sids.get(want_style[i])
            if not sid or not _set_pstyle(p, sid[0], author, when, nextid):
                missed.append((op, 'לא ניתן להחליף סגנון'))
                continue
            done += 1
            continue
        sid = sids.get(win_style)
        if not sid:
            missed.append((op, 'סגנון החלון חסר בקובץ'))
            continue
        if not _nw(res[0]):
            if not _set_pstyle(p, sid[0], author, when, nextid):
                missed.append((op, 'לא ניתן להחליף סגנון'))
                continue
            done += 1
            continue
        cut = op.get('cut') or [0, 0]
        if cut[1]:
            nm, idx = _norm_map(before[i]['text'])
            if cut[0] + cut[1] > len(idx):
                missed.append((op, 'חיתוך מחוץ לפסקה'))
                continue
            lo, hi = idx[cut[0]], idx[cut[0] + cut[1] - 1] + 1
            runs = _runs_of(p)
            full = ''.join(t for _, t, _ in runs)
            if full != before[i]['text'] or not _replace_in_paragraph(
                    p, full[lo:hi], '', author, when, nextid, at=lo):
                missed.append((op, 'לא ניתן למחוק את המילה במעקב'))
                continue
        np_ = etree.Element(W + 'p')
        ppr = etree.SubElement(np_, W + 'pPr')
        ps_ = etree.SubElement(ppr, W + 'pStyle')
        ps_.set(W + 'val', sid[0])
        _mark_para(np_, 'ins', author, when, nextid)
        ins = _mark(etree.Element(W + 'ins'), author, when, nextid)
        ins.append(_mkrun(op['res'][1], None))
        np_.append(ins)
        p.addprevious(np_)
        done += 1

    tmp = path + '.new'
    _rezip(path, tmp, {'word/document.xml':
                       etree.tostring(doc, xml_declaration=True, encoding='UTF-8', standalone=True),
                       'word/settings.xml': _ensure_track(settings)[0]})
    after = convert(tmp)
    got = [_nw(b['text']) for b in after]
    bad = None
    if got != want_after:
        bad = 'נוסח'
    else:
        for i, st in want_style.items():
            # אינדקס הפסקה בקובץ החדש: זז רק בפסקאות שנוספו לפניה
            shift = sum(1 for j, o in plan if j < i and o['kind'] == 'pside' and _nw((o.get('res') or [''])[0]))
            if after[i + shift]['style'] != st:
                bad = 'סגנון'
                break
    if bad:
        os.remove(tmp)
        log('האימות נכשל (%s). הקובץ לא נגע.' % bad)
        return {'applied': 0, 'missed': missed, 'backup': bk, 'verified': False}
    os.replace(tmp, path)
    log('נכתבו %d שינויי כותרת-צד, ואומתו' % done)
    return {'applied': done, 'missed': missed, 'backup': bk, 'verified': True}


def _paragraph_map(doc, blocks):
    """מקשר בין מספר הפסקה שבהמרה ובין אלמנט w:p שבמסמך.

    המפה נבנית בידי ההמרה עצמה ולא משוחזרת כאן מחדש. שחזור היה מחייב
    להעתיק את כללי הדילוג, וכל שינוי בהם היה מזיז את הכתיבה בשקט
    לפסקה שכנה."""
    ps = doc.find('w:body', ns).findall('w:p', ns)
    pmap = convert.last.get('pmap') or {}
    if len(pmap) != len(blocks):
        raise Refused('מפת הפסקאות אינה תואמת את ההמרה (%d מול %d)' % (len(pmap), len(blocks)))
    return {i: ps[n] for i, n in pmap.items() if n < len(ps)}


def _diff_check(before, after, expect, want_style=None):
    """כל הבדל שאינו אחד התיקונים שאושרו הוא כישלון."""
    want_style = want_style or {}
    bad = []
    if len(before) != len(after):
        bad.append('מספר הפסקאות השתנה: %d ⟵ %d' % (len(before), len(after)))
        return bad
    for b, a in zip(before, after):
        want = b['text']
        for find, repl in expect.get(b['i'], []):
            if find not in want:
                bad.append('פסקה %d: "%s" לא נמצא בטקסט המקורי' % (b['i'], find))
                continue
            want = want.replace(find, repl, 1)
        if a['text'] != want:
            bad.append('פסקה %d שונה ממה שאושר:\n     ציפינו: %r\n     קיבלנו: %r'
                       % (b['i'], want[:90], a['text'][:90]))
        if b['style'] != a['style'] and want_style.get(b['i']) != a['style']:
            bad.append('פסקה %d: הסגנון השתנה ולא אושר (%s ⟵ %s)'
                       % (b['i'], b['style'], a['style']))
        if b['i'] in want_style and a['style'] != want_style[b['i']]:
            bad.append('פסקה %d: הסגנון לא הוחל (ציפינו %s, יש %s)'
                       % (b['i'], want_style[b['i']], a['style']))
    n_changed = sum(1 for b, a in zip(before, after) if b['text'] != a['text'])
    if n_changed != len(expect):
        bad.append('מספר הפסקאות ששונו (%d) אינו כמספר הפסקאות שאושרו (%d)'
                   % (n_changed, len(expect)))
    return bad


def turn_on_tracking(path, masechet, log=print):
    """מוסיף w:trackRevisions בלבד, בלי שום שינוי בטקסט."""
    if is_open_in_word(path) and not wait_free(path, log=log):
        raise Refused('הקובץ פתוח בוורד ולא התפנה')
    z = zipfile.ZipFile(path)
    settings = z.read('word/settings.xml')
    z.close()
    new, changed = _ensure_track(settings)
    if not changed:
        log('מעקב-אחר-שינויים כבר פעיל')
        return False
    bk = backup(path, masechet)
    before = convert(path)
    tmp = path + '.new'
    _rezip(path, tmp, {'word/settings.xml': new})
    after = convert(tmp)
    if [b['text'] for b in before] != [a['text'] for a in after]:
        os.remove(tmp)
        raise Refused('הפעלת המעקב שינתה טקסט. הקובץ לא נגע')
    os.replace(tmp, path)
    log('מעקב-אחר-שינויים הופעל. גיבוי: ' + bk)
    return True


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--file', required=True)
    ap.add_argument('--masechet', required=True)
    ap.add_argument('--author', default='עריכה מהאתר')
    ap.add_argument('--ops')
    ap.add_argument('--track-only', action='store_true')
    ap.add_argument('--dry', action='store_true')
    a = ap.parse_args()
    if a.track_only:
        turn_on_tracking(a.file, a.masechet)
        sys.exit(0)
    ops = json.load(io.open(a.ops, encoding='utf-8'))
    r = apply(a.file, ops, a.author, a.masechet, dry=a.dry)
    print(json.dumps({k: v for k, v in r.items() if k != 'missed'}, ensure_ascii=False))
    for op, why in r['missed']:
        print('לא הוחל:', why, '|', op.get('find'))
