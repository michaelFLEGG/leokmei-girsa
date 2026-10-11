# -*- coding: utf-8 -*-
"""dedupe_ins_paras.py - מסיר פסקאות כפולות שהכלי הוסיף שוב ושוב לוורד.

באג (11.10.2026): קליטת "פסקה חדשה" רצה כל עשר דקות והוסיפה לוורד אותה כותרת
בכל הרצה. הכלי הזה משאיר מכל רצף כזה פסקה אחת בלבד: פסקאות עוקבות, באותו נוסח,
שכולן הוספה במעקב של "עריכה מהאתר". הוא אינו נוגע בשום פסקה אחרת, מגבה לפני
הכתיבה, ומאמת אחרי: מספר הפסקאות יורד בדיוק במספר המוסר, והשאר זהה.

    uv run --with lxml python tools/dedupe_ins_paras.py <קובץ.docx> [--apply]
בלי --apply: רק מדווח מה היה מוסר."""
import os, sys, zipfile
from lxml import etree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import word_apply as w
from docx2json import convert

W, ns = w.W, w.ns
AUTHOR = 'עריכה מהאתר'


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
    z.close()
    drop = plan(doc)
    before = convert(path)
    print('פסקאות בקובץ: %d; כפולות להסרה: %d' % (len(before), len(drop)))
    for p in drop[:3]:
        print('   לדוגמה:', repr(''.join(x.text or '' for x in p.iter(W + 't'))))
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
