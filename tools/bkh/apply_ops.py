# -*- coding: utf-8 -*-
"""apply_ops.py - שתילת תוצרי הסוכנים בקובץ הוורד, בעקוב אחר שינויים, בשם מנוע נפרד.

    uv run --with lxml python apply_ops.py b <קלט.docx> <פלט.docx> <b-out.json ...> [--dry]
        מנוע ב: restyle (רווח לפני), anchor (חיתוך עוגן מראש פסקה).   מחבר: "קלוד - סמנטי"
    uv run --with lxml python apply_ops.py c <קלט.docx> <פלט.docx> <c-out.json ...> [--dry] [--alts alts.json]
        מנוע ג: changes (ניסוח; ⟦⟧ = סגנון הסבר), heads (כותרות נושא חומות).   מחבר: "קלוד - ניסוח"

זיהוי הפסקה: לפי הטקסט המדויק (לא לפי אינדקס): האינדקס הוא רמז בלבד, ולכן שורד שינוי מבנה בין השלבים.
כל שינוי עובר אימות: הטקסט הסופי של הפסקה זהה לנוסח המבוקש; אחרת הפסקה מוחזרת כפי שהייתה.
"""
import sys, io, os, re, json, copy, collections, difflib
from bkh_common import *
from lxml import etree
import adv_apply as AA   # parse_new, plan_edit
from laukmi_mech import tracked_replace, apply_char_style, make_anchor
X = '{http://www.w3.org/XML/1998/namespace}space'
EXPL = 'הסבר'
FOREIGN_OK = set(OWN_AUTHORS) | set(PENDING_AUTHORS)


def live(p):
    return text_map(p)[0]


def foreign_tracking(p):
    for el in p.iter(q('ins'), q('del'), q('pPrChange'), q('rPrChange')):
        a = el.get(q('author')) or ''
        if a not in FOREIGN_OK:
            return True
    return False


class Index:
    """אינדקס פסקאות הטווח לפי טקסט מנורמל; מתעדכן אחרי שינויים."""
    def __init__(self, doc):
        self.doc = doc
        self.rebuild()

    def rebuild(self):
        self.ps = list(self.doc.paragraphs())
        self.by = collections.defaultdict(list)
        self.pos = {}
        for k, p in enumerate(self.ps):
            self.by[norm(live(p))].append(p)
            self.pos[id(p)] = k

    def find(self, text, hint=None, used=None):
        c = [p for p in self.by.get(norm(text.replace(TAB_MARK, ' ')), []) if used is None or id(p) not in used]
        if not c:
            return None
        if len(c) == 1 or hint is None:
            return c[0]
        return min(c, key=lambda p: abs(self.pos.get(id(p), 0) - hint))

    def find_prefix(self, prefix, hint=None, used=None):
        pre = norm(prefix.replace(TAB_MARK, ' '))
        c = [p for p in self.ps if norm(live(p)).startswith(pre) and (used is None or id(p) not in used)]
        if not c:
            return None
        if len(c) == 1 or hint is None:
            return c[0]
        return min(c, key=lambda p: abs(self.pos.get(id(p), 0) - hint))


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


def strip_tabs(p):
    n = 0
    for tab in list(p.iter(q('tab'))):
        par = tab.getparent()
        if par is not None and par.tag == q('r'):
            par.remove(tab); n += 1
    return n


def load(paths, key):
    items = []
    for f in paths:
        d = json.load(io.open(f, encoding='utf-8'))
        if isinstance(d, dict):
            items += [dict(x, _src=os.path.basename(os.path.dirname(f))) for x in d.get(key, [])]
        elif isinstance(d, list):
            items += d
    return items


def apply_b(src, dst, paths, dry):
    laukmi_mech.AUTHOR = AUTH_SEM
    doc = Doc(src); lo, hi = patch_range(doc)
    ix = Index(doc)
    ops = load(paths, 'ops')
    log = collections.Counter(); prob = []
    used = set()
    for op in sorted(ops, key=lambda o: (o.get('i', 0), o.get('op') == 'anchor')):
        kind = op.get('op'); i = op.get('i'); old = op.get('old') or ''
        p = ix.find_prefix(old, i) if old else None
        if p is None:
            log['לא נמצאה פסקה'] += 1; prob.append((i, kind, 'לא נמצאה פסקה', old[:40])); continue
        st = doc.pstyle(p)
        if foreign_tracking(p):
            log['שינוי מעקב של אחר'] += 1; prob.append((i, kind, 'שינוי מעקב של אחר', old[:40])); continue
        if kind == 'restyle':
            to = op.get('to')
            if to != 'רווח לפני' or st not in ('Normal', 'רגיל', '0.1', '0.2', 'List Paragraph'):
                log['restyle נדחה'] += 1; prob.append((i, kind, 'סגנון לא מותר (%s ← %s)' % (st, to), old[:40])); continue
            if not dry:
                mf.set_pstyle_tracked(doc, p, to)
            log['רווח לפני'] += 1
        elif kind == 'anchor':
            a = (op.get('anchor') or '').replace(TAB_MARK, '').strip()
            a = re.sub(r'^[·•∙]\s*', '', a)
            txt = live(p)
            m0 = re.match(r'^\s*[·•∙]\s*', txt)
            if m0 and not dry:
                # הבולט בוטל בחוקה (חלק 5.5): נמחק לפני החיתוך
                tracked_replace(doc, p, 0, m0.end(), '')
                txt = live(p)
            elif m0:
                txt = txt[m0.end():]
            lead = len(txt) - len(txt.lstrip())
            if not a or len(a.strip()) > 20 or not txt.lstrip().startswith(a):
                log['עוגן נדחה'] += 1; prob.append((i, kind, 'העוגן אינו קידומת או ארוך מ-20', a)); continue
            if st not in ('Normal', 'רגיל', '0.1', '0.2', 'List Paragraph', 'רווח לפני'):
                log['עוגן נדחה'] += 1; prob.append((i, kind, 'סגנון פסקה (%s)' % st, a)); continue
            cut = lead + len(a)
            if len(txt[cut:].strip()) < 15:
                log['עוגן נדחה'] += 1; prob.append((i, kind, 'נשאר פחות מ-15 תווים', a)); continue
            if not dry:
                if make_anchor(doc, p, cut, 'חלון 3') is None:
                    log['עוגן נדחה'] += 1; prob.append((i, kind, 'make_anchor נכשל', a)); continue
                ix.rebuild()
            log['עוגן'] += 1
        else:
            log['פעולה לא מוכרת'] += 1
    if not dry:
        doc.save(dst)
    return log, prob


def apply_c(src, dst, paths, dry, alts_path=None):
    laukmi_mech.AUTHOR = AUTH_FORM
    AA.laukmi_mech.AUTHOR = AUTH_FORM
    doc = Doc(src); lo, hi = patch_range(doc)
    ix = Index(doc)
    locked = set()
    changes = load(paths, 'changes')
    heads = load(paths, 'heads')
    log = collections.Counter(); prob = []; alts_out = []
    used = set()
    applied = []   # (נוסח ישן מנורמל, פסקה): לאיתור כותרות שעוגנו בנוסח הישן
    for it in sorted(changes, key=lambda x: x.get('i', 0)):
        i = it.get('i'); old = it.get('old'); new = it.get('new')
        if not isinstance(old, str) or not isinstance(new, str):
            log['פורמט'] += 1; continue
        p = ix.find(old, i, used)
        if p is None:
            log['הנוסח השתנה'] += 1; prob.append((i, 'הנוסח השתנה', old[:50])); continue
        used.add(id(p))
        cur = live(p)
        # ⟦⟧ יחסי לטקסט אחרי הסרת ⇥ ורווחי קצה
        plain, expl = AA.parse_new(new.replace(TAB_MARK, ''))
        lead = len(plain) - len(plain.lstrip())
        plain2 = plain.strip()
        expl = [(max(a - lead, 0), min(b - lead, len(plain2))) for a, b in expl if b - lead > 0 and a - lead < len(plain2)]
        plain = plain2
        if norm(plain) == norm(cur):
            log['ללא שינוי'] += 1
            if it.get('alts') and not any(c in plain for c in LONG_DASH):
                alts_out.append({'i': i, 'unit': it.get('_src', ''), 'old': cur, 'published': plain, 'published_m': new.replace(TAB_MARK, '').strip(), 'ptag': it.get('ptag') or '',
                                 'alts': it['alts'], 'expl': [plain[a:b] for a, b in expl]})
            continue
        if any(c in plain for c in LONG_DASH):
            log['מקף ארוך'] += 1; prob.append((i, 'מקף ארוך', plain[:50])); continue
        if not plain or len(plain) > 3.6 * max(len(cur), 24):
            log['אורך חריג'] += 1; prob.append((i, 'אורך חריג', plain[:50])); continue
        if '⟦' in plain or '⟧' in plain or ('#' in plain and '#' not in cur):
            log['סימון שנשאר'] += 1; prob.append((i, 'סימון שנשאר', plain[:50])); continue
        if foreign_tracking(p):
            log['שינוי מעקב של אחר'] += 1; prob.append((i, 'שינוי מעקב של אחר', cur[:50])); continue
        ops = AA.plan_edit(cur, plain, expl)
        if dry:
            log['יתוכנן'] += 1
        else:
            backup = copy.deepcopy(p)
            pristine = copy.deepcopy(p)
            ok = True
            for a, b, txt, rel in sorted(ops, key=lambda x: -x[0]):
                if not tracked_replace(doc, p, a, b, txt):
                    ok = False; break
                for x, y in rel:
                    if y > x:
                        apply_char_style(doc, p, a + x, a + y, EXPL)
            final = live(p)
            if not ok or final != plain:
                # נסיון שני: החלפה אחת של כל הפסקה (פחות עדינה, אך עקבית)
                p.getparent().replace(p, backup)
                p = backup
                ix.rebuild()
                ok = tracked_replace(doc, p, 0, len(cur), plain)
                if ok:
                    for x, y in expl:
                        if y > x:
                            apply_char_style(doc, p, x, y, EXPL)
                final = live(p)
                if ok and final == plain:
                    log['הוחל בהחלפה מלאה'] += 1
                    if TAB_MARK not in new and strip_tabs(p):
                        log['טאבים הוסרו'] += 1
                    applied.append((norm(old), p))
                    if it.get('alts'):
                        alts_out.append({'i': i, 'unit': it.get('_src', ''), 'old': cur, 'published': plain, 'published_m': new.replace(TAB_MARK, '').strip(),
                                         'ptag': it.get('ptag') or '', 'alts': it['alts'], 'expl': [plain[a:b] for a, b in expl]})
                    if expl:
                        log['מילות הסבר'] += len(expl)
                    continue
                p.getparent().replace(p, pristine)
                ix.rebuild()
                log['אימות נכשל (הוחזר)'] += 1; prob.append((i, 'אימות נכשל', plain[:60], 'בפועל:', final[:60], 'מקור:', cur[:60]))
                continue
            if TAB_MARK not in new and strip_tabs(p):
                log['טאבים הוסרו'] += 1
            log['הוחל'] += 1
            applied.append((norm(old), p))
        if it.get('alts'):
            alts_out.append({'i': i, 'unit': it.get('_src', ''), 'old': cur, 'published': plain, 'published_m': new.replace(TAB_MARK, '').strip(), 'ptag': it.get('ptag') or '', 'alts': it['alts'],
                             'expl': [plain[a:b] for a, b in expl]})
        if expl:
            log['מילות הסבר'] += len(expl)
    # כותרות
    ix.rebuild()
    sid = doc.name2id.get('נושא')
    for h in sorted(heads, key=lambda x: -x.get('i', 0)):
        text = (h.get('head') or '').strip()
        p = ix.find_prefix(h.get('old') or '', h.get('i'))
        if p is None:
            ho = norm((h.get('old') or '').replace(TAB_MARK, ' '))
            for onorm, pe in applied:
                if ho and onorm.startswith(ho):
                    p = pe; break
        if not sid:
            log['אין סגנון נושא'] += 1; continue
        if p is None:
            log['כותרת: לא נמצאה פסקה'] += 1; prob.append((h.get('i'), 'כותרת: לא נמצאה פסקה', text)); continue
        if not text or len(text) > 60 or any(c in text for c in LONG_DASH) or re.search('[a-zA-Z]', text):
            log['כותרת נדחתה'] += 1; prob.append((h.get('i'), 'כותרת נדחתה', text)); continue
        prev = p.getprevious()
        while prev is not None and (not live(prev).strip()) and doc.pstyle(prev) not in ('דף בצד',):
            prev = prev.getprevious()
        if prev is not None and doc.pstyle(prev) in ('נושא', "ד''ה משנה", 'דף בצד', 'פתיחת פרק', 'הדרן', 'הדרן עלך'):
            log['כותרת נדחתה'] += 1; prob.append((h.get('i'), 'כותרת אחרי כותרת/ד"ה/ציון דף', text)); continue
        if not dry:
            # חוקה 8.4: הכותרת מחליפה את המפריד - חציצה שלפניה נמחקת (במעקב)
            if prev is not None and doc.pstyle(prev) == 'חציצה' and mf.is_sep(prev) and not mf.deleted(prev):
                mf.delete_paragraph(doc, prev)
                log['חציצה לפני כותרת נמחקה'] += 1
            p.addprevious(new_heading(doc, text, sid))
        log['כותרות'] += 1
    if not dry:
        doc.save(dst)
    if alts_path:
        old_alts = []
        if os.path.exists(alts_path):
            old_alts = json.load(io.open(alts_path, encoding='utf-8'))
        json.dump(old_alts + alts_out, io.open(alts_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return log, prob


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    mode = sys.argv[1]
    args = [a for a in sys.argv[2:] if not a.startswith('--')]
    dry = '--dry' in sys.argv
    alts = None
    if '--alts' in sys.argv:
        alts = sys.argv[sys.argv.index('--alts') + 1]
        args = [a for a in args if a != alts]
    src, dst, files = os.path.abspath(args[0]), os.path.abspath(args[1]), [os.path.abspath(a) for a in args[2:]]
    if mode == 'b':
        log, prob = apply_b(src, dst, files, dry)
    else:
        log, prob = apply_c(src, dst, files, dry, alts)
    for k, v in sorted(log.items()):
        print('%s: %d' % (k, v))
    if prob:
        print('--- בעיות ---')
        for x in prob[:80]:
            print(x)
    json.dump({'log': dict(log), 'problems': prob}, io.open(dst + '.apply.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
