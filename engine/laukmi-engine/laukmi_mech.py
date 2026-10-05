#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
לאוקמי גירסא - מנוע הסבב המכני
עובד ישירות על קובץ ה-docx (XML), בלי וורד ובלי Office.js.
כל החלפה נרשמת כ"עקוב אחר שינויים" (w:del + w:ins) בשם המחבר "Claude - סבב מכני".
"""
import re, sys, json, shutil, zipfile, datetime
from lxml import etree

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W}
def q(t): return f"{{{W}}}{t}"

AUTHOR = "Claude - סבב מכני"
DATE = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

# ---------- תשתית ----------

class Doc:
    def __init__(self, path):
        self.path = path
        self.zin = zipfile.ZipFile(path)
        self.names = self.zin.namelist()
        self.doc = etree.fromstring(self.zin.read("word/document.xml"))
        self.styles = etree.fromstring(self.zin.read("word/styles.xml"))
        self._id = 90000
        self.name2id, self.id2name = {}, {}
        for st in self.styles.findall(q("style")):
            sid = st.get(q("styleId"))
            nm = st.find(q("name"))
            nm = nm.get(q("val")) if nm is not None else sid
            self.name2id[nm] = sid
            self.id2name[sid] = nm

    def nid(self):
        self._id += 1
        return str(self._id)

    def paragraphs(self):
        return self.doc.iter(q("p"))

    def pstyle(self, p):
        """שם התצוגה של סגנון הפסקה (לא ה-styleId)."""
        pPr = p.find(q("pPr"))
        if pPr is None: return "Normal"
        ps = pPr.find(q("pStyle"))
        if ps is None: return "Normal"
        return self.id2name.get(ps.get(q("val")), ps.get(q("val")))

    def save(self, out):
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for n in self.names:
                if n == "word/document.xml":
                    z.writestr(n, etree.tostring(self.doc, xml_declaration=True,
                                                 encoding="UTF-8", standalone=True))
                elif n == "word/settings.xml":
                    z.writestr(n, self._settings_with_track())
                else:
                    z.writestr(n, self.zin.read(n))

    def _settings_with_track(self):
        s = etree.fromstring(self.zin.read("word/settings.xml"))
        if s.find(q("trackChanges")) is None:
            s.insert(0, etree.SubElement(s, q("trackChanges")))
        return etree.tostring(s, xml_declaration=True, encoding="UTF-8", standalone=True)


# ---------- מפת הטקסט של פסקה ----------
# בונים מחרוזת אחת מכל ה-w:t שאינם בתוך w:del, עם מיפוי חזרה לרצים.

def text_map(p):
    """מחזיר (טקסט, [(w:t element, offset_start, offset_end)])"""
    buf, spans, pos = [], [], 0
    for t in p.iter(q("t")):
        # דילוג על טקסט שכבר מחוק במעקב, ועל טקסט בתוך שדות
        anc = t.getparent()
        skip = False
        while anc is not None and anc.tag != q("p"):
            if anc.tag == q("del"):
                skip = True; break
            anc = anc.getparent()
        if skip: continue
        s = t.text or ""
        buf.append(s)
        spans.append((t, pos, pos + len(s)))
        pos += len(s)
    return "".join(buf), spans


def split_run_at(t_el, offset):
    """מפצל את הרץ שמכיל את w:t בנקודה offset (יחסית ל-w:t). מחזיר את הרץ השני."""
    r = t_el.getparent()
    txt = t_el.text or ""
    if offset <= 0: return r, None
    if offset >= len(txt): return None, r
    r2 = etree.fromstring(etree.tostring(r))
    t_el.text = txt[:offset]
    t_el.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    t2 = r2.find(q("t"))
    t2.text = txt[offset:]
    t2.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    r.addnext(r2)
    return r, r2


def isolate(p, start, end):
    """מבודד את הטווח [start,end) לרצים נפרדים. מחזיר רשימת רצים המכסים בדיוק את הטווח."""
    txt, spans = text_map(p)
    # פיצול בקצה הימני קודם כדי לא להזיז את השמאלי
    for t, a, b in reversed(spans):
        if a < end < b:
            split_run_at(t, end - a)
    txt, spans = text_map(p)
    for t, a, b in reversed(spans):
        if a < start < b:
            split_run_at(t, start - a)
    txt, spans = text_map(p)
    return [t.getparent() for t, a, b in spans if a >= start and b <= end and b > a]


def mk_run_like(model, text):
    r = etree.Element(q("r"))
    rPr = model.find(q("rPr")) if model is not None else None
    if rPr is not None:
        r.append(etree.fromstring(etree.tostring(rPr)))
    t = etree.SubElement(r, q("t"))
    t.text = text
    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    return r


def tracked_replace(doc, p, start, end, new_text):
    """מוחק את הטווח (w:del) ומכניס טקסט חדש (w:ins) במקומו."""
    runs = isolate(p, start, end)
    if not runs: return False
    first = runs[0]
    # w:ins עם הטקסט החדש - לפני המחיקה
    if new_text:
        ins = etree.Element(q("ins"))
        ins.set(q("id"), doc.nid()); ins.set(q("author"), AUTHOR); ins.set(q("date"), DATE)
        ins.append(mk_run_like(first, new_text))
        first.addprevious(ins)
    # עטיפת הרצים הישנים ב-w:del והמרת w:t ל-w:delText
    dele = etree.Element(q("del"))
    dele.set(q("id"), doc.nid()); dele.set(q("author"), AUTHOR); dele.set(q("date"), DATE)
    runs[0].addprevious(dele)
    for r in runs:
        for t in r.findall(q("t")):
            t.tag = q("delText")
            t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        dele.append(r)
    return True


def apply_char_style(doc, p, start, end, style_name):
    """מחיל סגנון תו על טווח (בלי מעקב - שינוי עיצוב בלבד)."""
    sid = doc.name2id.get(style_name)
    if not sid: return False
    runs = isolate(p, start, end)
    if runs and all((r.find(q("rPr")) is not None and r.find(q("rPr")).find(q("rStyle")) is not None
                     and r.find(q("rPr")).find(q("rStyle")).get(q("val")) == sid) for r in runs):
        return False
    for r in runs:
        rPr = r.find(q("rPr"))
        if rPr is None:
            rPr = etree.Element(q("rPr")); r.insert(0, rPr)
        for old in rPr.findall(q("rStyle")): rPr.remove(old)
        rs = etree.Element(q("rStyle")); rs.set(q("val"), sid); rPr.insert(0, rs)
    return bool(runs)


# ---------- כללים ----------

PREFIX = "(?:ו|ד|ל|כ|מ|ש|וד|ול|וכ|כד|דל|אד|לכד|וכד)?"
# גבול מילה עברי: לא אות עברית, לא גרש/גרשיים צמודים
LB = r"(?<![א-ת\"'׳״])"
RB = r"(?![א-ת\"'׳״])"

def word_re(w):
    return LB + re.escape(w) + RB

def name_re(w):
    return LB + PREFIX + re.escape(w) + RB


def run_replacements(doc, table, allowed_styles, log):
    """טבלת {ישן: חדש}, ארוך לפני קצר, על פסקאות בסגנונות המותרים."""
    keys = sorted(table.keys(), key=len, reverse=True)
    pats = [(re.compile(word_re(k)), k, table[k]) for k in keys]
    for p in list(doc.paragraphs()):
        if doc.pstyle(p) not in allowed_styles: continue
        changed = True
        guard = 0
        while changed and guard < 50:
            changed = False; guard += 1
            txt, _ = text_map(p)
            for rx, old, new in pats:
                m = rx.search(txt)
                if m:
                    if tracked_replace(doc, p, m.start(), m.end(), new):
                        log[old] = log.get(old, 0) + 1
                        changed = True
                    break


def style_names(doc, names, allowed_styles, style_name, log):
    """סגנון תו לשמות אמוראים + אותיות קישור. ארוך לפני קצר."""
    ordered = sorted(names, key=len, reverse=True)
    pats = [re.compile(name_re(n)) for n in ordered]
    for p in list(doc.paragraphs()):
        if doc.pstyle(p) not in allowed_styles: continue
        txt, _ = text_map(p)
        hits = []
        for rx in pats:
            for m in rx.finditer(txt):
                if not any(a < m.end() and m.start() < b for a, b in hits):
                    hits.append((m.start(), m.end()))
        for a, b in sorted(hits, reverse=True):
            if apply_char_style(doc, p, a, b, style_name):
                log["מופעים"] = log.get("מופעים", 0) + 1


def delete_chars(doc, chars, allowed_styles, log):
    for p in list(doc.paragraphs()):
        if doc.pstyle(p) not in allowed_styles: continue
        for ch in chars:
            while True:
                txt, _ = text_map(p)
                i = txt.find(ch)
                if i < 0: break
                if not tracked_replace(doc, p, i, i + len(ch), ""): break
                log[ch] = log.get(ch, 0) + 1


def run_replacements_pfx(doc, table, allowed_styles, log):
    """כמו run_replacements, אבל שומר אותיות קישור צמודות: 'ולרבי יוחנן' -> 'ולרי\"ו'."""
    table = {k: v for k, v in table.items() if k != v}
    keys = sorted(table.keys(), key=len, reverse=True)
    pats = [(re.compile(LB + "(" + PREFIX + ")" + re.escape(k) + RB), k, table[k]) for k in keys]
    for p in list(doc.paragraphs()):
        if doc.pstyle(p) not in allowed_styles: continue
        changed, guard = True, 0
        while changed and guard < 60:
            changed = False; guard += 1
            txt, _ = text_map(p)
            for rx, old, new in pats:
                m = rx.search(txt)
                if m:
                    if tracked_replace(doc, p, m.start(), m.end(), m.group(1) + new):
                        log[old] = log.get(old, 0) + 1
                        changed = True
                    break


def final_text(path):
    """טקסט הקובץ כפי שייראה לאחר קבלת כל השינויים - לאימות."""
    z = zipfile.ZipFile(path)
    doc = etree.fromstring(z.read("word/document.xml"))
    out = []
    for p in doc.iter(q("p")):
        buf = []
        for t in p.iter(q("t")):
            anc, skip = t.getparent(), False
            while anc is not None and anc.tag != q("p"):
                if anc.tag == q("del"): skip = True; break
                anc = anc.getparent()
            if not skip: buf.append(t.text or "")
        out.append("".join(buf))
    return out


# ---------- שכבת העוגנים: פיצול פסקה ליצירת "חלון 3" ----------

def _live_len(el):
    n = 0
    for t in el.iter(q("t")):
        anc, skip = t.getparent(), False
        while anc is not None and anc.tag != q("p"):
            if anc.tag == q("del"): skip = True; break
            anc = anc.getparent()
        if not skip: n += len(t.text or "")
    return n


def make_anchor(doc, p, cut, style_name="חלון 3"):
    """מפצל את הפסקה בנקודה cut; החלק הראשון הופך לפסקת עוגן בסגנון הנתון.
       סימן הפסקה החדש נרשם כהוספה במעקב."""
    sid = doc.name2id.get(style_name)
    if not sid or cut <= 0: return None
    isolate(p, 0, cut)
    newp = etree.Element(q("p"))
    pPr = etree.SubElement(newp, q("pPr"))
    ps = etree.SubElement(pPr, q("pStyle")); ps.set(q("val"), sid)
    rPr = etree.SubElement(pPr, q("rPr"))
    ins = etree.SubElement(rPr, q("ins"))
    ins.set(q("id"), doc.nid()); ins.set(q("author"), AUTHOR); ins.set(q("date"), DATE)
    pos, moved = 0, []
    for child in list(p):
        if child.tag == q("pPr"): continue
        n = _live_len(child)
        if pos + n <= cut and not (n == 0 and pos >= cut):
            moved.append(child); pos += n
        else:
            break
    if not moved: return None
    for c in moved: newp.append(c)
    # ניקוי עיצוב-רצים בעוגן: שאריות סגנון תו וגופן נגררות
    for r in newp.iter(q("r")):
        rp = r.find(q("rPr"))
        if rp is not None: r.remove(rp)
    p.addprevious(newp)
    # מחיקת רווח מוביל שנשאר בשארית
    txt, spans = text_map(p)
    k = len(txt) - len(txt.lstrip(" \t"))
    if k: tracked_replace(doc, p, 0, k, "")
    return newp


def run_raw(doc, table, allowed_styles, log):
    """החלפה בלי גבולות מילה - לסימני פיסוק ורווחים."""
    for p in list(doc.paragraphs()):
        if doc.pstyle(p) not in allowed_styles: continue
        for old, new in table.items():
            guard = 0
            while guard < 200:
                guard += 1
                txt, _ = text_map(p)
                i = txt.find(old)
                if i < 0: break
                if not tracked_replace(doc, p, i, i + len(old), new): break
                log[old] = log.get(old, 0) + 1


def style_regex(doc, patterns, allowed_styles, style_name, log, group=1):
    """סגנון תו לפי תבניות רוחביות (regex) ולא לפי רשימה סגורה."""
    rxs = [re.compile(p) for p in patterns]
    for p in list(doc.paragraphs()):
        if doc.pstyle(p) not in allowed_styles: continue
        txt, _ = text_map(p)
        hits = []
        for rx in rxs:
            for m in rx.finditer(txt):
                a, b = m.span(group) if group <= (rx.groups or 0) else m.span()
                a = m.start()          # כולל אותיות קישור
                if not any(x < b and a < y for x, y in hits): hits.append((a, b))
        for a, b in sorted(hits, reverse=True):
            if apply_char_style(doc, p, a, b, style_name):
                log["מופעים"] = log.get("מופעים", 0) + 1


def run_rx(doc, pairs, allowed_styles, log):
    """החלפות לפי regex עם קבוצות לכידה (\\1 בהחלפה)."""
    cps = [(re.compile(p), r) for p, r in pairs]
    for p in list(doc.paragraphs()):
        if doc.pstyle(p) not in allowed_styles: continue
        for rx, rep in cps:
            guard = 0
            while guard < 100:
                guard += 1
                txt, _ = text_map(p)
                m = rx.search(txt)
                if not m: break
                new = m.expand(rep).replace("None", "")
                if new == m.group(0): break
                if not tracked_replace(doc, p, m.start(), m.end(), new): break
                log[rx.pattern[:12]] = log.get(rx.pattern[:12], 0) + 1


def remove_char_style(doc, p, start, end, style_name):
    """מסיר סגנון תו מטווח, אם הוא מוחל עליו."""
    sid = doc.name2id.get(style_name)
    if not sid: return False
    runs = isolate(p, start, end)
    hit = False
    for r in runs:
        rPr = r.find(q("rPr"))
        if rPr is None: continue
        for old in rPr.findall(q("rStyle")):
            if old.get(q("val")) == sid:
                rPr.remove(old); hit = True
    return hit


def unstyle_words(doc, words, allowed_styles, style_name, log):
    """מסיר סגנון תו ממילים שאינן שייכות לו (רשימה שחורה)."""
    pats = [re.compile(LB + re.escape(w) + RB) for w in words]
    for p in list(doc.paragraphs()):
        if doc.pstyle(p) not in allowed_styles: continue
        txt, _ = text_map(p)
        hits = []
        for rx in pats:
            for m in rx.finditer(txt):
                hits.append((m.start(), m.end()))
        for a, b in sorted(set(hits), reverse=True):
            if remove_char_style(doc, p, a, b, style_name):
                log["הוסר"] = log.get("הוסר", 0) + 1
