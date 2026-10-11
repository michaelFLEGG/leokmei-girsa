# -*- coding: utf-8 -*-
"""תיקון ציוני דף בבכורות - לבקשת בעל הפרויקט (5.10.2026): להשלים ציוני דף
חסרים, לתקן ציון שגוי, ולתקן מיקום. כל שינוי במעקב, בשם "עורך - ציוני דף".

הרצף: ב. עד סא. - לכל צד (א/ב) ציון אחד, בסדר. הכלי עובר על פסקאות "דף בצד"
ומשווה לרצף הצפוי:
 - ציון כפול בצמידות: הנכון נקבע לפי השכנים (הציון שאחריו הוא ההמשך הצפוי).
 - ציון חסר: נוספת פסקת "דף בצד" במקום שנקבע מראש לכל חסר (INSERTS), לפי
   אילוצי הטקסט: סימון [דף יח עמוד ב] בגוף הפסקה, או גבול ההפניות לגמרא.
 - ציון כפול בראש המסמך (לפני כותרת הפרק ואחריה): הראשון נמחק.
"""
import sys, re, copy
from lxml import etree
import laukmi_mech
from laukmi_mech import Doc, q, text_map, tracked_replace, isolate
import masechet_fmt as F
laukmi_mech.AUTHOR = "עורך - ציוני דף"   # אחרי הייבוא: masechet_fmt קובע שם משלו
X = "{http://www.w3.org/XML/1998/namespace}space"
V = {'א':1,'ב':2,'ג':3,'ד':4,'ה':5,'ו':6,'ז':7,'ח':8,'ט':9,'י':10,'כ':20,'ל':30,'מ':40,'נ':50,'ס':60,'ע':70,'פ':80,'צ':90,'ק':100}
DAF = "דף בצד"


def side(label):
    t = label.strip()
    n = sum(V.get(c, 0) for c in re.sub(r'[.:"\'׳״ ]', '', t))
    return n * 2 + (1 if t.endswith(':') else 0) if n else None


def label_of(s):
    n, b = divmod(s, 2)
    # בניית האותיות
    out, k = '', n
    for v, c in [(100,'ק'),(90,'צ'),(80,'פ'),(70,'ע'),(60,'ס'),(50,'נ'),(40,'מ'),(30,'ל'),(20,'כ'),(10,'י'),
                 (9,'ט'),(8,'ח'),(7,'ז'),(6,'ו'),(5,'ה'),(4,'ד'),(3,'ג'),(2,'ב'),(1,'א')]:
        while k >= v:
            out += c; k -= v
    out = out.replace('יה', 'טו').replace('יו', 'טז')
    return out + (':' if b else '.')


def new_para_like(doc, model_p, text, style_name):
    """פסקה חדשה בסגנון נתון, כהוספה במעקב, עם עיצוב הרצים של פסקה לדוגמה."""
    sid = doc.name2id[style_name]
    p = etree.Element(q("p"))
    pPr = etree.SubElement(p, q("pPr"))
    ps = etree.SubElement(pPr, q("pStyle")); ps.set(q("val"), sid)
    rPr = etree.SubElement(pPr, q("rPr"))
    ins = etree.SubElement(rPr, q("ins"))
    ins.set(q("id"), doc.nid()); ins.set(q("author"), laukmi_mech.AUTHOR); ins.set(q("date"), laukmi_mech.DATE)
    w = etree.SubElement(p, q("ins"))
    w.set(q("id"), doc.nid()); w.set(q("author"), laukmi_mech.AUTHOR); w.set(q("date"), laukmi_mech.DATE)
    model_r = None
    if model_p is not None:
        for r in model_p.iter(q("r")):
            if r.find(q("t")) is not None:
                model_r = r; break
    r = laukmi_mech.mk_run_like(model_r, text)
    w.append(r)
    return p


def split_before(doc, p, cut):
    """מפצל פסקה בנקודה cut: החלק הראשון יוצא לפסקה חדשה (באותו סגנון)
    שלפניה, בהוספה במעקב. מחזיר את הפסקה החדשה."""
    isolate(p, 0, cut)
    newp = etree.Element(q("p"))
    pPr0 = p.find(q("pPr"))
    pPr = copy.deepcopy(pPr0) if pPr0 is not None else etree.Element(q("pPr"))
    for e in pPr.findall(q("pPrChange")): pPr.remove(e)
    rPr = pPr.find(q("rPr"))
    if rPr is None:
        rPr = etree.SubElement(pPr, q("rPr"))
    for e in rPr.findall(q("ins")): rPr.remove(e)
    ins = etree.Element(q("ins"))
    ins.set(q("id"), doc.nid()); ins.set(q("author"), laukmi_mech.AUTHOR); ins.set(q("date"), laukmi_mech.DATE)
    rPr.insert(0, ins)
    newp.append(pPr)
    pos, moved = 0, []
    for child in list(p):
        if child.tag == q("pPr"): continue
        n = laukmi_mech._live_len(child)
        if pos + n <= cut and not (n == 0 and pos >= cut):
            moved.append(child); pos += n
        else:
            break
    for c in moved: newp.append(c)
    p.addprevious(newp)
    return newp


def main(src, dst, inserts):
    doc = Doc(src)
    ps = list(doc.paragraphs())
    st = [doc.pstyle(p) for p in ps]
    live = [text_map(p)[0] for p in ps]
    marks = [i for i in range(len(ps)) if st[i] == DAF and live[i].strip()]
    log = []
    sides = [side(live[i]) for i in marks]
    model = ps[marks[1]]
    # א. ציון כפול בראש המסמך
    if len(marks) > 1 and sides[0] == sides[1] and marks[0] < 10:
        F.delete_paragraph(doc, ps[marks[0]]); log.append('נמחק ציון כפול בראש: ' + live[marks[0]].strip())
        marks, sides = marks[1:], sides[1:]
    # ב. שגוי וכפול
    exp = sides[0]
    todo_ins = []
    for k, i in enumerate(marks):
        s = sides[k]
        if s == exp:
            exp += 1; continue
        if s > exp:
            nxt = sides[k + 1] if k + 1 < len(sides) else None
            if nxt == s and s - exp == 1:          # הציון הנוכחי שגוי: הבא אחריו הוא הנכון
                new = label_of(exp)
                tracked_replace(doc, ps[i], 0, len(live[i].rstrip()), new)
                log.append('תוקן ציון: %s -> %s' % (live[i].strip(), new)); exp += 1; continue
            for miss in range(exp, s):
                todo_ins.append((i, miss))
            exp = s + 1; continue
        if s == exp - 1:                            # כפול: הנוכחי הוא ההמשך
            new = label_of(exp)
            tracked_replace(doc, ps[i], 0, len(live[i].rstrip()), new)
            log.append('תוקן ציון כפול: %s -> %s' % (live[i].strip(), new)); exp += 1; continue
        log.append('ציון חריג שלא טופל: %s בפסקה %d' % (live[i].strip(), i))
    # ג. הוספת ציונים חסרים
    for before_mark_idx, miss in todo_ins:
        spec = inserts.get(label_of(miss))
        if not spec:
            log.append('חסר ציון %s ואין הוראת מיקום - לא נוסף' % label_of(miss)); continue
        # spec: {"before_text": טקסט שפסקה מתחילה בו, "after": מילת-מקום בפסקה, "split_at": מחרוזת בגוף הפסקה}
        lo = marks[0]
        if spec.get('after_mark'):
            am = side(spec['after_mark'])
            lo = next((i for i, sd in zip(marks, sides) if sd == am), marks[0])
        if spec.get('contains'):
            cand = [j for j in range(len(ps)) if j > lo and spec['contains'] in live[j]]
        else:
            cand = [j for j in range(len(ps)) if j > lo and live[j].strip().startswith(spec['before_text'])]
            if spec.get('after_mark'):
                cand = cand[:1]
        if len(cand) != 1:
            log.append('חסר ציון %s: נמצאו %d מועמדות למיקום - לא נוסף' % (label_of(miss), len(cand))); continue
        j = cand[0]
        target = ps[j]
        if spec.get('split_at'):
            t = live[j]; at = t.index(spec['split_at'])
            cutlen = at
            newp = split_before(doc, target, cutlen)
            # הסרת הסימון הפנימי [דף ... עמוד ב]
            t2, _ = text_map(target)
            mm = re.search(r'\s*\[דף[^\]]*\]\s*', t2)
            if mm: tracked_replace(doc, target, mm.start(), mm.end(), ' ' if False else '')
        mark = new_para_like(doc, model, label_of(miss), DAF)
        target.addprevious(mark)
        log.append('נוסף ציון %s לפני: %s' % (label_of(miss), live[j][:40]))
    doc.save(dst)
    for l in log: print(' ', l)
    print('נשמר', dst)


if __name__ == '__main__':
    import json
    main(sys.argv[1], sys.argv[2], json.load(open(sys.argv[3], encoding='utf-8')))
