#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
שני כלים:
  accept_all(in, out)  - מקבל את כל השינויים שבמעקב ומשאיר את המעקב דלוק
  extract(path)        - מחלץ את תיקוני המחבר מהמעקב ומקבץ אותם לדפוסים
"""
import re, sys, zipfile, collections
from lxml import etree
from laukmi_scan import load, para_style, live_text, q, W


def accept_all(src, dst):
    z = zipfile.ZipFile(src)
    doc = etree.fromstring(z.read("word/document.xml"))
    ins = dele = 0
    for el in list(doc.iter(q("del"))):          # מחיקה שהתקבלה - יורדת
        par = el.getparent()
        if par is not None: par.remove(el); dele += 1
    for el in list(doc.iter(q("ins"))):          # הוספה שהתקבלה - העטיפה יורדת
        par = el.getparent()
        if par is None: continue
        if par.tag == q("rPr"):                  # סימן פסקה שהוזן
            par.remove(el); ins += 1; continue
        i = list(par).index(el)
        for k, child in enumerate(list(el)): par.insert(i + k, child)
        par.remove(el); ins += 1
    for tag in ("rPrChange", "pPrChange", "moveFrom", "moveTo"):
        for el in list(doc.iter(q(tag))):
            p = el.getparent()
            if p is not None: p.remove(el)
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as out:
        for n in z.namelist():
            if n == "word/document.xml":
                out.writestr(n, etree.tostring(doc, xml_declaration=True, encoding="UTF-8", standalone=True))
            elif n == "word/settings.xml":
                s = etree.fromstring(z.read(n))
                if s.find(q("trackChanges")) is None:
                    e = etree.Element(q("trackChanges")); s.insert(0, e)
                out.writestr(n, etree.tostring(s, xml_declaration=True, encoding="UTF-8", standalone=True))
            else:
                out.writestr(n, z.read(n))
    return ins, dele


def _txt(el, tags=("t", "delText")):
    return "".join((x.text or "") for x in el.iter(*[q(t) for t in tags]))


def extract(path, author=None):
    """מחלץ כל שינוי במעקב, מזווג מחיקה עם ההוספה הצמודה לה, ומקבץ לדפוסים."""
    z, doc, id2name = load(path)
    edits = []
    for p in doc.iter(q("p")):
        style = para_style(p, id2name)
        kids = [c for c in p if c.tag in (q("ins"), q("del"), q("r"))]
        i = 0
        while i < len(kids):
            c = kids[i]
            if c.tag == q("del"):
                old = _txt(c)
                new = ""
                if i + 1 < len(kids) and kids[i+1].tag == q("ins"):
                    new = _txt(kids[i+1]); i += 1
                elif i and kids[i-1].tag == q("ins"):
                    new = _txt(kids[i-1])
                a = c.get(q("author"))
                if not author or a == author:
                    edits.append((old.strip(), new.strip(), style, a))
            elif c.tag == q("ins"):
                prev = kids[i-1] if i else None
                if prev is None or prev.tag != q("del"):
                    a = c.get(q("author"))
                    if not author or a == author:
                        edits.append(("", _txt(c).strip(), style, a))
            i += 1
    return edits


def classify(edits):
    """מכני = זוג (ישן,חדש) שחוזר, או החלפת מילה בודדת. אחר = שיקול דעת."""
    pairs = collections.Counter((o, n) for o, n, s, a in edits if o and n)
    dels = collections.Counter(o for o, n, s, a in edits if o and not n)
    adds = collections.Counter(n for o, n, s, a in edits if n and not o)
    word = re.compile(r"^[א-ת\"'\-–]{1,14}$")
    mech = {k: v for k, v in pairs.items() if v >= 2 or (word.match(k[0]) and word.match(k[1]))}
    judg = {k: v for k, v in pairs.items() if k not in mech}
    return mech, judg, dels, adds


if __name__ == "__main__":
    if sys.argv[1] == "accept":
        print("התקבלו: %d הוספות, %d מחיקות" % accept_all(sys.argv[2], sys.argv[3]))
    else:
        ed = extract(sys.argv[2])
        m, j, d, a = classify(ed)
        print(f"סה\"כ שינויים: {len(ed)} | מחברים: {collections.Counter(x[3] for x in ed)}")
        print(f"\n== כללים מכניים ({len(m)} דפוסים, {sum(m.values())} מופעים) ==")
        for (o, n), c in sorted(m.items(), key=lambda x: -x[1])[:60]: print(f"  {c:3d}  {o}  ->  {n}")
        print(f"\n== מחיקות חוזרות ==")
        for o, c in d.most_common(30): print(f"  {c:3d}  מחק: {o[:60]}")
        print(f"\n== הוספות חוזרות ==")
        for n, c in a.most_common(30): print(f"  {c:3d}  הוסף: {n[:60]}")
        print(f"\n== דורש שיקול דעת ({len(j)}) - 25 דוגמאות ==")
        for (o, n), c in list(j.items())[:25]: print(f"       {o[:55]}  ->  {n[:55]}")
