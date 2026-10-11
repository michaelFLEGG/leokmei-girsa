# -*- coding: utf-8 -*-
"""heading_insert_word.py - הוספת כותרות נושא (נוסח קלוד, חום #7B3F00) לפני פסקאות, בעקוב אחר שינויים (11.10.2026).

קלט: JSON של [{file, i, head, at_h}]: i - אינדקס הפסקה שלפניה תוכנס הכותרת; at_h - טביעת הפסקה (md5 של הטקסט החי, 10 תווים).
העיגון: אינדקס + טביעה. אם הפסקה השתנתה - לא נוגעים ורושמים. כל כתיבה בשם "קלוד", גיבוי, ואימות שהטקסט (חוץ מהכותרות) זהה.
    uv run --with lxml python tools/heading_insert_word.py heads.json [--אמת]
"""
import os, sys, json, shutil, tempfile, hashlib, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'engine', 'laukmi-engine'))
import word_apply as wa
import laukmi_mech, masechet_fmt as mf
from laukmi_mech import Doc, q
from lxml import etree
from docx2json import convert
from styles_map import role_of
laukmi_mech.AUTHOR = 'קלוד'
X = '{http://www.w3.org/XML/1998/namespace}space'


def fp(p):
    return hashlib.md5(mf.live(p).encode()).hexdigest()[:10]


def new_heading(doc, text, sid):
    p = etree.Element(q('p'))
    ppr = etree.SubElement(p, q('pPr'))
    ps = etree.SubElement(ppr, q('pStyle')); ps.set(q('val'), sid)
    rpr = etree.SubElement(ppr, q('rPr'))
    mark = etree.SubElement(rpr, q('ins'))
    mark.set(q('id'), doc.nid()); mark.set(q('author'), laukmi_mech.AUTHOR); mark.set(q('date'), laukmi_mech.DATE)
    ins = etree.SubElement(p, q('ins'))
    ins.set(q('id'), doc.nid()); ins.set(q('author'), laukmi_mech.AUTHOR); ins.set(q('date'), laukmi_mech.DATE)
    r = etree.SubElement(ins, q('r')); rp = etree.SubElement(r, q('rPr'))
    c = etree.SubElement(rp, q('color')); c.set(q('val'), '7B3F00')
    t = etree.SubElement(r, q('t')); t.text = text; t.set(X, 'preserve')
    return p


def run(path, items, real):
    name = os.path.basename(path)
    doc = Doc(path)
    sid = doc.name2id.get('נושא')
    if not sid:
        return name, 0, [], 'אין סגנון נושא בקובץ'
    ps = list(doc.paragraphs()); n = len(ps)
    done, skipped = 0, []
    for it in sorted(items, key=lambda x: -x['i']):
        i = it['i']
        if i >= n or fp(ps[i]) != it['at_h']:
            skipped.append((i, 'הפסקה השתנתה')); continue
        if len(it['head']) > 90 or '–' in it['head'] or '—' in it['head']:
            skipped.append((i, 'כותרת ארוכה מדי או מקף ארוך')); continue
        ps[i].addprevious(new_heading(doc, it['head'], sid)); done += 1
    if not done:
        doc.zin.close(); return name, 0, skipped, 'אין מה לכתוב'
    tmp = tempfile.mktemp(suffix='.docx'); doc.save(tmp); doc.zin.close()
    a, b = convert(path), convert(tmp)
    keep_a = [x['text'] for x in a]
    keep_b = [x['text'] for x in b]
    # הכותרות החדשות: סגנון נושא, חום. מוסרים אותן מן ההשוואה לפי הטקסט
    heads = collections.Counter(it['head'] for it in items if it['i'] < n)
    rest = []
    for t in keep_b:
        if heads.get(t, 0) > 0 and t not in keep_a:
            heads[t] -= 1
        else:
            rest.append(t)
    ok = rest == keep_a
    if not ok:
        os.remove(tmp); return name, done, skipped, 'האימות נכשל - לא נכתב'
    if not real:
        os.remove(tmp); return name, done, skipped, 'יבש, תקין'
    if wa.is_open_in_word(path):
        os.remove(tmp); return name, done, skipped, 'פתוח בוורד - דולג'
    wa.backup(path, 'כותרות ' + os.path.splitext(name)[0][:20])
    shutil.copy2(tmp, path + '.new'); os.replace(path + '.new', path); os.remove(tmp)
    return name, done, skipped, 'נכתב'


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    data = json.load(open(sys.argv[1], encoding='utf-8'))
    by = collections.defaultdict(list)
    for x in data:
        if x.get('head'): by[x['file']].append(x)
    for f, items in by.items():
        name, done, skipped, msg = run(os.path.join(wa.DRIVE, f), items, '--אמת' in sys.argv)
        print(name, done, 'דולגו', len(skipped), msg, flush=True)
        for s in skipped[:10]: print('   ', s)
