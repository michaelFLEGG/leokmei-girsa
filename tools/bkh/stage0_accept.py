# -*- coding: utf-8 -*-
"""stage0_accept.py - שלב 0: חילוץ למידה מן השינויים הממתינים בטווח כה.-לה: וקבלתם.

    uv run --with lxml python stage0_accept.py <קלט.docx> <פלט.docx> <למידה.json>

הלמידה נכתבת לפני הקבלה (זוגות לפני/אחרי לכל פסקה שנגעו בה בעלי השינויים הממתינים).
קבלה = ins נפרש, del נמחק, שינוי סגנון (pPrChange/rPrChange) נסגר; פסקה שסימנה נמחק במלואו - מוסרת.
שינוי של מחבר שאינו ברשימת הממתינים - לא נוגעים בו.
"""
import sys, io, json, copy
from bkh_common import *
from lxml import etree


def para_pairs(p, authors):
    before, after = [], []
    touched = set()
    def walk(el, mode=None, au=None):
        for ch in el:
            tag = ch.tag.split('}')[1]
            if tag in ('ins', 'del'):
                walk(ch, tag, ch.get(q('author')))
            elif tag in ('r', 'hyperlink', 'smartTag', 'sdt', 'sdtContent'):
                walk(ch, mode, au)
            elif tag in ('t', 'delText'):
                txt = ch.text or ''
                m = mode if tag == 't' else 'del'
                if m is None:
                    before.append(txt); after.append(txt)
                elif au in authors:
                    touched.add(au)
                    (before if m == 'del' else after).append(txt)
                else:
                    if m == 'ins':
                        before.append(txt); after.append(txt)
    walk(p)
    return ''.join(before), ''.join(after), sorted(touched)


def accept_para(p, authors):
    n = 0
    for el in list(p.iter(q('rPrChange'), q('pPrChange'))):
        if el.get(q('author')) in authors:
            el.getparent().remove(el); n += 1
    for el in list(p.iter(q('del'))):
        if el.getparent() is not None and el.getparent().tag == q('rPr'):
            continue  # סימן פסקה, בנפרד
        if el.get(q('author')) in authors:
            el.getparent().remove(el); n += 1
    for el in list(p.iter(q('ins'))):
        if el.getparent() is not None and el.getparent().tag == q('rPr'):
            continue
        if el.get(q('author')) in authors:
            par = el.getparent()
            idx = par.index(el)
            for k, ch in enumerate(list(el)):
                par.insert(idx + k, ch)
            par.remove(el); n += 1
    ppr = p.find(q('pPr'))
    gone = False
    if ppr is not None:
        rpr = ppr.find(q('rPr'))
        if rpr is not None:
            for el in list(rpr.findall(q('ins'))):
                if el.get(q('author')) in authors:
                    rpr.remove(el); n += 1
            for el in list(rpr.findall(q('del'))):
                if el.get(q('author')) in authors:
                    rpr.remove(el); n += 1
                    gone = True
    return n, gone


def main(src, dst, learn_path):
    doc = Doc(src)
    lo, hi = patch_range(doc)
    authors = set(PENDING_AUTHORS)
    pairs, total, removed = [], 0, 0
    ps = list(doc.paragraphs())
    for p in ps:
        b, a, who = para_pairs(p, authors)
        if who and b != a:
            pairs.append({'style': doc.pstyle(p), 'before': b, 'after': a, 'authors': who})
    for p in ps:
        n, gone = accept_para(p, authors)
        total += n
        if gone and not mf.live(p).strip():
            p.getparent().remove(p); removed += 1
    doc.save(dst)
    json.dump(pairs, io.open(learn_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('טווח פסקאות %d-%d | שינויים שהתקבלו: %d | פסקאות שהוסרו: %d | זוגות למידה: %d' % (lo, hi, total, removed, len(pairs)))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main(sys.argv[1], sys.argv[2], sys.argv[3])
