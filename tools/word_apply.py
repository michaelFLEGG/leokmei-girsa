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


def _replace_in_paragraph(p, find, repl, author, when, nextid):
    """מחליף מופע אחד של find ב-repl, במעקב. מחזיר True אם הצליח.

    הסימון עשוי להתפרש על כמה קטעי-תו, מפני שוורד מפצל הרצות גם בלא
    שינוי עיצוב. לכן ההחלפה חותכת כל קטע שנוגע בסימון, מוחקת את החלק
    שבתוכו, ושותלת את הנוסח החדש במקום הראשון - בעיצוב שהיה שם.
    קטע שכבר יושב בתוך שינוי-מעקב קיים אינו נוגע, ומדווח."""
    runs = _runs_of(p)
    full = ''.join(t for _, t, _ in runs)
    k = full.find(find)
    if k < 0:
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
    plan, missed = [], []
    for op in ops:
        hit = hagaha.anchor(before, op)
        if hit is None:
            missed.append((op, 'לא אותרה הפסקה'))
            continue
        b, how = hit
        if op['find'] not in b['text']:
            missed.append((op, 'הטקסט להחלפה אינו בפסקה שאותרה'))
            continue
        plan.append((b['i'], op, how))
    if not plan:
        return {'applied': 0, 'missed': missed, 'backup': None, 'verified': True}
    if dry:
        return {'applied': len(plan), 'missed': missed, 'backup': None, 'verified': None,
                'plan': [(i, o['find'], o['replace']) for i, o, _ in plan]}

    if os.path.getmtime(path) != mtime:
        log('הקובץ השתנה על הדיסק בזמן התכנון. קורא מחדש')
        return apply(path, ops, author, masechet, log=log)

    bk = backup(path, masechet)
    log('גיבוי: ' + bk)

    z = zipfile.ZipFile(path)
    doc = etree.fromstring(z.read('word/document.xml'))
    settings = z.read('word/settings.xml')
    z.close()

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

    tmp = path + '.new'
    _rezip(path, tmp, {'word/document.xml':
                       etree.tostring(doc, xml_declaration=True, encoding='UTF-8', standalone=True),
                       'word/settings.xml': _ensure_track(settings)[0]})

    # --- אימות: להמיר מחדש ולהשוות ---
    after = convert(tmp)
    bad = _diff_check(before, after, expect)
    if bad:
        os.remove(tmp)
        log('האימות נכשל. הקובץ לא נגע:')
        for line in bad[:8]:
            log('   ' + line)
        return {'applied': 0, 'missed': missed, 'backup': bk, 'verified': False, 'errors': bad}

    os.replace(tmp, path)
    log('נכתבו %d תיקונים, ואומתו' % done)
    return {'applied': done, 'missed': missed, 'backup': bk, 'verified': True}


def _paragraph_map(doc, blocks):
    """מקשר בין מספר הפסקה שבהמרה ובין אלמנט w:p שבמסמך."""
    out, n = {}, 0
    carry = False
    for p in doc.find('w:body', ns).findall('w:p', ns):
        ps = p.find('w:pPr/w:pStyle', ns)
        sid = ps.get(W + 'val') if ps is not None else ''
        if sid and sid.startswith('toc'):
            continue
        mark_del = p.find('w:pPr/w:rPr/w:del', ns) is not None
        live = ''.join(t for _, t, _ in _runs_of(p))
        if mark_del and not live.strip():
            continue
        if carry:
            carry = False
        if mark_del:
            carry = True
            continue
        if not live.strip():
            # פסקה ריקה בסגנון Normal מדולגת בהמרה. נשענים על הטקסט
            # עצמו כדי לא לאבד סנכרון.
            if n < len(blocks) and blocks[n]['style'] == 'Normal' and not blocks[n]['text'].strip():
                pass
            else:
                continue
        if n >= len(blocks):
            break
        out[blocks[n]['i']] = p
        n += 1
    return out


def _diff_check(before, after, expect):
    """כל הבדל שאינו אחד התיקונים שאושרו הוא כישלון."""
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
        if b['style'] != a['style']:
            bad.append('פסקה %d: הסגנון השתנה' % b['i'])
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
