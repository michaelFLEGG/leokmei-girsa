# -*- coding: utf-8 -*-
"""עיטור שאין לידו כותרת או משנה הופך לכותרת נושא (8.10.2026, הכרעת בעל הפרויקט).
קלט: JSON של [{file,i,next_h,head}]. העיטור נמחק במעקב, הכותרת נכתבת במקומו במעקב,
בצבע חום (כותרת שנוסחה בידי קלוד, חוקה 8.3), סגנון "נושא". העיגון: אינדקס הפסקה
+ טביעת הפסקה שאחריה; אם השתנה - לא נוגעים.
    uv run --with lxml python tools/orn_to_heading_word.py heads.json [--אמת]"""
import os, sys, json, shutil, tempfile, hashlib, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'engine', 'laukmi-engine'))
import word_apply as wa
import laukmi_mech, masechet_fmt as mf
from laukmi_mech import Doc, q
from lxml import etree
from docx2json import convert
laukmi_mech.AUTHOR = 'קלוד'
X = "{http://www.w3.org/XML/1998/namespace}space"
SK = set(mf.TRANSPARENT) | {'חלון 3', 'משנה בצד', 'משנה בצד תו'}

def replace_with_heading(doc, p, text):
    for ch in list(p):
        if ch.tag == q('r'):
            for t in ch.findall(q('t')):
                t.tag = q('delText'); t.set(X, 'preserve')
            d = etree.Element(q('del'))
            d.set(q('id'), doc.nid()); d.set(q('author'), laukmi_mech.AUTHOR); d.set(q('date'), laukmi_mech.DATE)
            ch.addprevious(d); d.append(ch)
    ins = etree.SubElement(p, q('ins'))
    ins.set(q('id'), doc.nid()); ins.set(q('author'), laukmi_mech.AUTHOR); ins.set(q('date'), laukmi_mech.DATE)
    r = etree.SubElement(ins, q('r')); rpr = etree.SubElement(r, q('rPr'))
    c = etree.SubElement(rpr, q('color')); c.set(q('val'), '7B3F00')
    t = etree.SubElement(r, q('t')); t.text = text; t.set(X, 'preserve')
    mf.set_pstyle_tracked(doc, p, 'נושא')

def texts(path):
    return [b['text'] for b in convert(path)]

def safe_replace(tmp, path, tries=6):
    import time
    for _ in range(tries):
        try:
            shutil.copy2(tmp, path + '.new'); os.replace(path + '.new', path); os.remove(tmp); return True
        except PermissionError:
            try: os.remove(path + '.new')
            except OSError: pass
            time.sleep(10)
    return False

def run(path, items, real):
    name = os.path.basename(path)
    doc = Doc(path); ps = list(doc.paragraphs()); n = len(ps)
    st = [doc.pstyle(p) for p in ps]
    done = 0; skipped = []
    for it in sorted(items, key=lambda x: -x['i']):
        i = it['i']
        if i >= n or mf.deleted(ps[i]) or not mf.is_sep(ps[i]) or st[i] not in mf.BODYISH | {'חציצה'}:
            skipped.append((i, 'העיטור השתנה')); continue
        j = i + 1
        while j < n and (mf.deleted(ps[j]) or mf.is_empty(ps[j]) or st[j] in SK): j += 1
        if j >= n or hashlib.md5(mf.live(ps[j]).encode()).hexdigest()[:10] != it['next_h']:
            skipped.append((i, 'הפסקה שאחריו השתנתה')); continue
        replace_with_heading(doc, ps[i], it['head']); done += 1
    if not done: return name, 0, skipped, 'אין מה לכתוב'
    tmp = tempfile.mktemp(suffix='.docx'); doc.save(tmp)
    a = [b for b in convert(path)]; b2 = [b for b in convert(tmp)]
    from styles_map import role_of
    keep = lambda L: [x['text'] for x in L if role_of(x) not in ('hatz', 'nose')]
    ok = keep(a) == keep(b2) and sum(1 for x in b2 if role_of(x) == 'nose') >= sum(1 for x in a if role_of(x) == 'nose') + done - 0
    if not ok:
        os.remove(tmp); return name, done, skipped, 'האימות נכשל - לא נכתב'
    if not real:
        os.remove(tmp); return name, done, skipped, 'יבש, תקין'
    if wa.is_open_in_word(path):
        os.remove(tmp); return name, done, skipped, 'פתוח בוורד - דולג'
    bk = wa.backup(path, 'כותרות ' + os.path.splitext(name)[0][:20])
    doc.zin.close()
    if not safe_replace(tmp, path): return name, 0, [], 'הקובץ נעול (דרייב או וורד) - דולג'
    return name, done, skipped, 'נכתב'

if __name__ == '__main__':
    data = json.load(open(sys.argv[1], encoding='utf-8'))
    by = collections.defaultdict(list)
    for x in data:
        if x.get('head'): by[x['file']].append(x)
    for f, items in by.items():
        name, done, skipped, msg = run(os.path.join(wa.DRIVE, f), items, '--אמת' in sys.argv)
        print(name, done, 'דולגו', len(skipped), msg, flush=True)
