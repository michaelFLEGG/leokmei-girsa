# -*- coding: utf-8 -*-
"""adv_apply.py - שתילת תוצר המנוע המתקדם (הידוק משפטים ושילוב הסבר) בקובץ ורד, בעקוב אחר שינויים בשם "קלוד".

    python adv_apply.py <קובץ.docx> <תיקיית-תוצרים> <פלט.docx> [--dry]

תוצר: קובצי adv-NN.json, כל אחד רשימה של {"i": <אינדקס פסקה>, "old": "<הנוסח הנוכחי המדויק>", "new": "<נוסח חדש>", "why": "..."}.
ב-"new" מילות הסבר שנוספו (שאינן מחליפות מילה בנוסח) מוקפות ב-⟦ ⟧ ומקבלות את סגנון התו "הסבר"; כל השאר בסגנון הקיים.
כל שינוי נעשה בהחלפה מינימלית ברמת המילה (difflib), כדי שהמחבר יראה בדיוק מה השתנה. פסקה ש"old" שלה אינו זהה לנוסח הנוכחי - מדולגת ומדווחת.
כללים: בלי מקף ארוך (נדחה), פסקה לא מתרוקנת, אורך חדש אינו עולה על פי 2.2 מן הישן (חריג: נדחה לבדיקה), אין שינוי בפסקה שכבר נושאת שינוי מעקב של אדם אחר.
"""
import sys, os, re, json, glob, difflib, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import laukmi_mech
from laukmi_mech import Doc, text_map, tracked_replace, apply_char_style, q

laukmi_mech.AUTHOR = 'קלוד'
EXPL = 'הסבר'
LONG_DASH = ('–', '—', '―')
TOK = re.compile(r'\s+|\S+')


def parse_new(s):
    """-> (טקסט נקי, [(a, b)] טווחי הסבר בטקסט הנקי)"""
    plain, ranges, pos = [], [], 0
    for part in re.split(r'(⟦[^⟧]*⟧)', s):
        if part.startswith('⟦') and part.endswith('⟧'):
            t = part[1:-1]
            if t:
                ranges.append((pos, pos + len(t)))
            plain.append(t); pos += len(t)
        else:
            plain.append(part); pos += len(part)
    return ''.join(plain), ranges


def has_foreign_tracking(p):
    for el in p.iter(q('ins'), q('del')):
        a = el.get(q('author')) or ''
        if a not in ('קלוד', 'Claude', 'מנוע מכני', 'מנוע עיצוב', 'Claude - סבב מכני', 'Claude - שלב ב', 'Claude - סמנטי',
                     'מנוע אמוראים', 'מנוע פסוקים', 'מספור קטעי משנה'):
            return True
    return False


def plan_edit(old, new_plain, expl):
    """רשימת החלפות [(a, b, טקסט חדש, [טווחי הסבר יחסיים])] על הטקסט הישן, בהיסטים של הישן."""
    ot, nt = TOK.findall(old), TOK.findall(new_plain)
    sm = difflib.SequenceMatcher(None, ot, nt, autojunk=False)
    # היסטים בטקסט החדש
    opos, npos = [0], [0]
    for t in ot: opos.append(opos[-1] + len(t))
    for t in nt: npos.append(npos[-1] + len(t))
    ops = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            continue
        # הרחבה לטוקן שכן כשזו הוספה או מחיקה טהורה, כדי שתהיה החלפה
        if i1 == i2:                       # הוספה
            if i1 > 0:
                i1 -= 1; j1 -= 1
            elif i2 < len(ot):
                i2 += 1; j2 += 1
        elif j1 == j2:                     # מחיקה
            if i1 > 0:
                i1 -= 1; j1 -= 1; j2 = j1 + 1 if False else j2
                j1 = j2 - 1 if j2 > 0 else j1
            elif i2 < len(ot):
                i2 += 1; j2 += 1
        a, b = opos[i1], opos[i2]
        ns, ne = npos[j1], npos[j2]
        rel = [(max(x, ns) - ns, min(y, ne) - ns) for x, y in expl if x < ne and y > ns]
        ops.append((a, b, new_plain[ns:ne], rel))
    # מיזוג החלפות חופפות או צמודות
    merged = []
    for op in ops:
        if merged and op[0] <= merged[-1][1]:
            pa, pb, pt, pr = merged[-1]
            merged[-1] = (pa, max(pb, op[1]), pt + op[2], pr)   # נדיר; הסבר בחלק הממוזג מוחל מחדש לפי הטקסט
        else:
            merged.append(op)
    return merged


def apply(path, decdir, out, dry=False):
    doc = Doc(path)
    paras = list(doc.paragraphs())
    items = []
    for f in sorted(glob.glob(os.path.join(decdir, 'adv-*.json'))):
        try:
            items += json.load(open(f, encoding='utf-8'))
        except Exception as e:
            print('קובץ פגום', f, e)
    log = collections.Counter()
    problems = []
    seen = set()
    for it in sorted(items, key=lambda x: x.get('i', -1)):
        i = it.get('i'); old = it.get('old'); new = it.get('new')
        if not isinstance(i, int) or i >= len(paras) or not isinstance(new, str) or not isinstance(old, str):
            log['פורמט'] += 1; continue
        if i in seen:
            log['כפילות'] += 1; continue
        seen.add(i)
        p = paras[i]
        cur, _ = text_map(p)
        if cur != old:
            log['הנוסח השתנה'] += 1; problems.append((i, 'הנוסח השתנה', old[:60])); continue
        plain, expl = parse_new(new)
        if plain == cur:
            log['ללא שינוי'] += 1; continue
        if any(c in plain for c in LONG_DASH):
            log['מקף ארוך'] += 1; problems.append((i, 'מקף ארוך', plain[:60])); continue
        if not plain.strip() or len(plain) > 2.2 * max(len(cur), 20):
            log['אורך חריג'] += 1; problems.append((i, 'אורך חריג', plain[:60])); continue
        if has_foreign_tracking(p):
            log['שינוי מעקב של אחר'] += 1; problems.append((i, 'שינוי מעקב של אחר', cur[:60])); continue
        ops = plan_edit(cur, plain, expl)
        if dry:
            log['יתוכנן'] += 1; continue
        ok = True
        for a, b, txt, rel in sorted(ops, key=lambda x: -x[0]):
            if not tracked_replace(doc, p, a, b, txt):
                ok = False; break
            for x, y in rel:
                if y > x:
                    apply_char_style(doc, p, a + x, a + y, EXPL)
        final, _ = text_map(p)
        if not ok or final != plain:
            log['אימות נכשל'] += 1; problems.append((i, 'אימות נכשל', plain[:60]))
        else:
            log['הוחל'] += 1
    if not dry:
        doc.save(out)
    for k, v in sorted(log.items()):
        print('%s: %d' % (k, v))
    json.dump(problems, open(os.path.join(decdir, 'adv-problems.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return log


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    apply(a[0], a[1], a[2] if len(a) > 2 else None, dry='--dry' in sys.argv)
