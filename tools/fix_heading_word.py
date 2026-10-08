# -*- coding: utf-8 -*-
"""תיקון כותרות חומות של קלוד (8.10.2026): מחליף את הנוסח בתוך ההוספה של קלוד עצמו.
קלט: JSON של [{file,i,old,new}]. רק כותרת שעדיין חומה ושהוספת קלוד, ושנוסחה זהה ל-old."""
import os, sys, json, shutil, tempfile, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'engine', 'laukmi-engine'))
import word_apply as wa, masechet_fmt as mf, laukmi_mech
from laukmi_mech import Doc, q
from docx2json import convert
from orn_to_heading_word import safe_replace

def run(path, items, real):
    name = os.path.basename(path)
    doc = Doc(path); ps = list(doc.paragraphs()); n = len(ps); done = 0; skipped = 0
    for it in items:
        i = it['i']
        if i >= n: skipped += 1; continue
        p = ps[i]
        runs = [r for r in p.iter(q('r')) if r.getparent().tag == q('ins') and r.getparent().get(q('author')) == 'קלוד']
        if (doc.pstyle(p) != 'נושא' or not runs or mf.live(p).strip() != it['old']
                or not all((r.find(q('rPr') + '/' + q('color')) is not None) for r in runs)):
            skipped += 1; continue
        ts = [t for r in runs for t in r.findall(q('t'))]
        ts[0].text = it['new']
        for t in ts[1:]: t.text = ''
        done += 1
    if not done: doc.zin.close(); return name, 0, skipped, 'אין מה לכתוב'
    tmp = tempfile.mktemp(suffix='.docx'); doc.save(tmp); doc.zin.close()
    from styles_map import role_of
    keep = lambda L: [x['text'] for x in L if role_of(x) not in ('hatz', 'nose')]
    if keep(convert(path)) != keep(convert(tmp)):
        os.remove(tmp); return name, done, skipped, 'האימות נכשל - לא נכתב'
    if not real: os.remove(tmp); return name, done, skipped, 'יבש, תקין'
    if wa.is_open_in_word(path): os.remove(tmp); return name, done, skipped, 'פתוח בוורד - דולג'
    wa.backup(path, 'תיקון כותרות ' + os.path.splitext(name)[0][:16])
    if not safe_replace(tmp, path): return name, 0, skipped, 'הקובץ נעול - דולג'
    return name, done, skipped, 'נכתב'

if __name__ == '__main__':
    by = collections.defaultdict(list)
    for x in json.load(open(sys.argv[1], encoding='utf-8')): by[x['file']].append(x)
    for f, items in by.items():
        print(*run(os.path.join(wa.DRIVE, f), items, '--אמת' in sys.argv), sep=' | ', flush=True)
