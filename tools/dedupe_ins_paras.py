# -*- coding: utf-8 -*-
"""dedupe_ins_paras.py - מסיר פסקאות כפולות שהכלי הוסיף שוב ושוב לוורד.

באג (11.10.2026): קליטת "פסקה חדשה" רצה כל עשר דקות והוסיפה לוורד אותה כותרת
בכל הרצה. הכלי הזה משאיר מכל רצף כזה פסקה אחת בלבד: פסקאות עוקבות, באותו נוסח,
שכולן הוספה במעקב של "עריכה מהאתר". הוא אינו נוגע בשום פסקה אחרת, מגבה לפני
הכתיבה, ומאמת אחרי: מספר הפסקאות יורד בדיוק במספר המוסר, והשאר זהה.

הרחבה (7.11.2026, הכפלת תיקונים בוורד): גם זוג "כותרת צד ואותה שורה בגוף" -
פסקת חלון (תפקיד anchor), ומיד אחריה פסקת גוף באותו נוסח. נוצר כש-unside החזיר
כותרת לגוף והקליטה החוזרת הוסיפה אותה שוב. מוסרת רק שורת הגוף, וגם זה רק כשהיא
כולה הוספה במעקב של "עריכה מהאתר" - כמו שהאתר מציג (_side_tidy ב-build_site).
זוג ששורת הגוף בו אינה הוספה שלנו נשאר, ומדווח.

    uv run --with lxml python tools/dedupe_ins_paras.py <קובץ.docx> [--apply] [--list]
בלי --apply: רק מדווח מה היה מוסר."""
import os, sys, zipfile
from lxml import etree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import word_apply as w
from docx2json import convert

W, ns = w.W, w.ns
AUTHOR = 'עריכה מהאתר'


def _roles(styles_xml):
    """styleId -> תפקיד הסגנון (styles_map.ROLE), דרך שם הסגנון."""
    from styles_map import ROLE, ALIAS
    out = {}
    for name, (sid, kind) in w._style_ids(styles_xml).items():
        r = ROLE.get(ALIAS.get(name, name))
        if r and sid not in out:
            out[sid] = r
    return out


def _ptxt(p):
    return ''.join(x.text or '' for x in p.iter(W + 't')).replace('\xa0', ' ').strip()


def _role(p, roles):
    ps = p.find('w:pPr/w:pStyle', ns)
    return roles.get(ps.get(W + 'val'), 'body') if ps is not None else 'body'


def side_pairs(doc, roles):
    """זוגות של כותרת צד ומיד אחריה שורת גוף באותו נוסח. מחזיר (להסרה, נשארים לדיווח)."""
    ps = [p for p in doc.find('w:body', ns) if p.tag == W + 'p']
    drop, kept = [], []
    for a, b in zip(ps, ps[1:]):
        t = _ptxt(a)
        if not t or _ptxt(b) != t:
            continue
        if _role(a, roles) != 'anchor' or not _role(b, roles).startswith('body'):
            continue
        ins = b.findall('w:ins', ns)
        mine = bool(ins) and all(i.get(W + 'author') == AUTHOR for i in ins) and not b.findall('w:r', ns)
        (drop if mine else kept).append(b)
    return drop, kept


def plan(doc):
    body = doc.find('w:body', ns)
    ps = list(body)
    def info(p):
        if p.tag != W + 'p':
            return None
        t = ''.join(x.text or '' for x in p.iter(W + 't')).replace('\xa0', ' ').strip()
        ins = p.findall('w:ins', ns)
        mine = bool(ins) and all(i.get(W + 'author') == AUTHOR for i in ins)
        direct_runs = p.findall('w:r', ns)
        return (t, mine and not direct_runs)
    drop, i = [], 0
    while i < len(ps):
        a = info(ps[i])
        if a and a[1] and a[0]:
            j = i
            while j + 1 < len(ps) and info(ps[j + 1]) == a:
                j += 1
            if j > i:
                drop.extend(ps[i:j])        # נשארת האחרונה: סימן-הפסקה שלה לא הוסף שוב
            i = j + 1
        else:
            i += 1
    return drop


def main():
    path = sys.argv[1]
    do = '--apply' in sys.argv
    if w.is_open_in_word(path):
        print('הקובץ פתוח בוורד. לא נוגע.'); return 2
    z = zipfile.ZipFile(path)
    doc = etree.fromstring(z.read('word/document.xml'))
    roles = _roles(z.read('word/styles.xml'))
    z.close()
    drop = plan(doc)
    sdrop, skept = side_pairs(doc, roles)
    sdrop = [p for p in sdrop if p not in drop]
    before = convert(path)
    print('פסקאות בקובץ: %d; כפולות צמודות להסרה: %d; שורות גוף שחוזרות על כותרת הצד שמעליהן: %d (ועוד %d שאינן הוספה שלנו - נשארות)'
          % (len(before), len(drop), len(sdrop), len(skept)))
    for p in drop[:5]:
        print('   כפולה:', repr(_ptxt(p)[:70]))
    for p in sdrop[:5]:
        print('   כותרת וגוף:', repr(_ptxt(p)[:70]))
    for p in skept[:5]:
        print('   נשארת (לא שלנו):', repr(_ptxt(p)[:70]))
    if '--list' in sys.argv:
        for p in drop + sdrop:
            print('   *', repr(_ptxt(p)))
    drop = drop + sdrop
    if not do or not drop:
        return 0
    bk = w.backup(path, 'dedupe')
    print('גיבוי:', bk)
    for p in drop:
        p.getparent().remove(p)
    tmp = path + '.new'
    w._rezip(path, tmp, {'word/document.xml': etree.tostring(
        doc, xml_declaration=True, encoding='UTF-8', standalone=True)})
    after = convert(tmp)
    if len(after) != len(before) - len(drop):
        os.remove(tmp); print('האימות נכשל (ספירה). הקובץ לא נגע.'); return 1
    from collections import Counter
    exp = Counter(b['text'] for b in before)
    for p in drop:
        exp[''.join(x.text or '' for x in p.iter(W + 't'))] -= 1
    if +Counter(b['text'] for b in after) != +exp:
        os.remove(tmp); print('האימות נכשל (תוכן). הקובץ לא נגע.'); return 1
    os.replace(tmp, path)
    print('נכתב. פסקאות עכשיו: %d' % len(after))
    return 0


if __name__ == '__main__':
    sys.exit(main())
