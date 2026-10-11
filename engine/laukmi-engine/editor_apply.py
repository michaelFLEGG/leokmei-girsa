# -*- coding: utf-8 -*-
"""העורך המתקדם (ב5) - שתילה במעקב, בשם "עורך - פרקים א-ב".

קלט: ed_*.json  (changes / headings / anchors, ראה editor_units.py והפרומפט)
  changes : {par, old, new} - new מכיל מילות הסבר בתוך ⟦ ⟧. ההחלפה מחושבת
            ברמת מילה (הבדל מינימלי), כך שכל תיקון נראה בוורד כחילוף נקודתי.
            מילה חדשה שבתוך ⟦ ⟧ מקבלת סגנון התו "הסבר"; מילה עברית שבאה
            במקום ארמית נשארת בסגנון הרגיל.
  headings: {before, text} - פסקת "נושא" חדשה (בצבע חום #7B3F00, כמו בכל
            כותרת שמנוסחת בידי העורך) לפני פסקה.
  anchors : {par, head} - המילים הפותחות את הפסקה (head) יוצאות לחלון 3.
כלל: old חייב להיות זהה לטקסט החי של הפסקה כרגע; אחרת הפריט מדולג ונרשם.
סגנונות שאין נוגעים בהם: משניות, דף בצד, פרק, פרק שם, הדרן עלך, חציצה.
"""
import sys, re, json, glob, difflib, collections, copy
from lxml import etree
import laukmi_mech
from laukmi_mech import Doc, q, text_map, tracked_replace, apply_char_style, isolate, split_run_at, mk_run_like, make_anchor
laukmi_mech.AUTHOR = "עורך - פרקים א-ב"
FROZEN = {"משניות", "דף בצד", "פרק", "פרק שם", "הדרן עלך", "חציצה", "דפים בפרק ב", "תחילת פרק", "סוף פרק"}
X = "{http://www.w3.org/XML/1998/namespace}space"
LONG = re.compile('[–—]')


def tracked_insert(doc, p, pos, text):
    """הוספת טקסט בנקודה pos של הפסקה, כהוספה במעקב."""
    t, spans = text_map(p)
    pos = max(0, min(pos, len(t)))
    for tt, a, b in spans:
        if a < pos < b:
            split_run_at(tt, pos - a)
            break
    t, spans = text_map(p)
    ref = None
    for tt, a, b in spans:
        if a >= pos:
            ref = tt.getparent(); break
    model = None
    for tt, a, b in reversed(spans):
        if b <= pos:
            model = tt.getparent(); break
    if model is None and spans:
        model = spans[0][0].getparent()
    ins = etree.Element(q("ins"))
    ins.set(q("id"), doc.nid()); ins.set(q("author"), laukmi_mech.AUTHOR); ins.set(q("date"), laukmi_mech.DATE)
    ins.append(mk_run_like(model, text))
    if ref is not None:
        # הרץ עשוי לשבת בתוך w:ins/w:del קיים - מצמידים ברמת הפסקה
        top = ref
        while top.getparent() is not p:
            top = top.getparent()
        top.addprevious(ins)
    else:
        p.append(ins)
    return True


def tokens(s):
    return re.findall(r'\s+|[^\s]+', s)


def edit_par(doc, p, old, new_marked, log):
    spans = []                       # (start, end) של מילות הסבר ב-new
    plain, k = [], 0
    for part in re.split('(⟦|⟧)', new_marked):
        if part == '⟦': spans.append([k, None]); continue
        if part == '⟧':
            if spans and spans[-1][1] is None: spans[-1][1] = k
            continue
        plain.append(part); k += len(part)
    new = ''.join(plain)
    cur, _ = text_map(p)
    if cur.strip() != old.strip():
        log['דולג: הנוסח הוחלף'] += 1; return
    if LONG.search(new):
        new = LONG.sub('-', new)
    if new == cur:
        return
    A, B = tokens(cur), tokens(new)
    sm = difflib.SequenceMatcher(None, A, B, autojunk=False)
    # מיקומי תחילת אסימונים
    ap = [0]
    for t in A: ap.append(ap[-1] + len(t))
    bp = [0]
    for t in B: bp.append(bp[-1] + len(t))
    ops = [o for o in sm.get_opcodes() if o[0] != 'equal']
    for tag, i1, i2, j1, j2 in reversed(ops):
        a, b = ap[i1], ap[i2]
        seg_new = new[bp[j1]:bp[j2]]
        if tag == 'delete':
            tracked_replace(doc, p, a, b, '')
            log['מחיקה'] += 1
        elif tag == 'insert':
            tracked_insert(doc, p, a, seg_new)
            log['הוספה'] += 1
            ls, le = a, a + len(seg_new)
            _style_expl(doc, p, ls, bp[j1], seg_new, spans, log)
        else:
            tracked_replace(doc, p, a, b, seg_new)
            log['החלפה'] += 1
            _style_expl(doc, p, a, bp[j1], seg_new, spans, log)


def _style_expl(doc, p, live_start, new_start, seg, spans, log):
    """מחיל סגנון "הסבר" על חלקי המקטע שבתוך ⟦ ⟧."""
    for s, e in spans:
        if e is None: continue
        lo, hi = max(s, new_start), min(e, new_start + len(seg))
        if lo < hi:
            a = live_start + (lo - new_start); b = live_start + (hi - new_start)
            if apply_char_style(doc, p, a, b, "הסבר"): log['מילות הסבר'] += 1


def new_heading(doc, model_p, text):
    sid = doc.name2id["נושא"]
    p = etree.Element(q("p"))
    pPr = etree.SubElement(p, q("pPr"))
    ps = etree.SubElement(pPr, q("pStyle")); ps.set(q("val"), sid)
    rPr = etree.SubElement(pPr, q("rPr"))
    ins = etree.SubElement(rPr, q("ins"))
    ins.set(q("id"), doc.nid()); ins.set(q("author"), laukmi_mech.AUTHOR); ins.set(q("date"), laukmi_mech.DATE)
    w = etree.SubElement(p, q("ins"))
    w.set(q("id"), doc.nid()); w.set(q("author"), laukmi_mech.AUTHOR); w.set(q("date"), laukmi_mech.DATE)
    r = etree.SubElement(w, q("r"))
    rp = etree.SubElement(r, q("rPr"))
    col = etree.SubElement(rp, q("color")); col.set(q("val"), "7B3F00")
    t = etree.SubElement(r, q("t")); t.text = text; t.set(X, "preserve")
    return p


def main(src, edir, dst, report):
    doc = Doc(src)
    ps = list(doc.paragraphs())
    st = [doc.pstyle(p) for p in ps]
    log = collections.Counter(); rej = []
    chg, heads, anchors = [], [], []
    for f in sorted(glob.glob(edir + '/ed_*.json')):
        d = json.load(open(f, encoding='utf-8'))
        chg += d.get('changes') or []; heads += d.get('headings') or []; anchors += d.get('anchors') or []
    seen = set()
    for c in chg:
        i = int(c['par'])
        if st[i] in FROZEN or i in seen:
            log['דולג: סגנון קבוע או פסקה כפולה'] += 1; continue
        seen.add(i)
        edit_par(doc, ps[i], c['old'], c['new'], log)
    for a in anchors:
        i = int(a['par'])
        if st[i] in FROZEN: continue
        t, _ = text_map(ps[i]); h = a['head']
        if t.startswith(h) and 0 < len(h) <= 22 and make_anchor(doc, ps[i], len(h), "חלון 3") is not None:
            log['חלון צד נוסף'] += 1
        else:
            rej.append(('עוגן לא הוחל', i, h))
    for h in heads:
        i = int(h['before'])
        if st[i] in ('דף בצד', 'חציצה'):
            rej.append(('כותרת: הפסקה אינה גוף', i, h['text'])); continue
        txt = LONG.sub('-', h['text'])
        ps[i].addprevious(new_heading(doc, ps[i], txt)); log['כותרת נוספה'] += 1
    doc.save(dst)
    with open(report, 'w', encoding='utf-8') as f:
        for k, v in log.items(): f.write('%s: %d\n' % (k, v))
        for r in rej: f.write('%s\n' % (r,))
    for k, v in log.items(): print('  %s: %d' % (k, v))
    print('נדחו:', len(rej))


if __name__ == '__main__':
    main(*sys.argv[1:5])
