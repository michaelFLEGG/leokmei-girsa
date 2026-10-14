# -*- coding: utf-8 -*-
"""ingest_docx.py - קליטת הכרעות מקובץ סקירה שיוצא מהדף ("ייצוא ההערות הפתוחות לוורד") וחזר מהדרייב.

    uv run python tools/skira/ingest_docx.py <קובץ.docx> <מסכת> [--dry]

הכללים (מנה 13.10.2026, סעיף 4י):
  * הערה שנמחקה בוורד  = דחייה (rs=word).
  * הערה שיש בטקסט הצמוד אליה שינוי בעקוב (הוספה או מחיקה) = קבלה (נרשמת "נערך" עם הנוסח).
  * הערה שנשארה כמות שהיא = ממתינה (לא נרשמת).
מזהה הממצא נקרא מתחילת טקסט ההערה: "[<מזהה>] ...".
"""
import os, sys, re, zipfile, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import skira_common as C

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('docx')
    ap.add_argument('slug')
    ap.add_argument('--dry', action='store_true')
    a = ap.parse_args()
    from lxml import etree
    z = zipfile.ZipFile(a.docx)
    doc = etree.fromstring(z.read('word/document.xml'))
    com = etree.fromstring(z.read('word/comments.xml')) if 'word/comments.xml' in z.namelist() else None
    present = {}
    if com is not None:
        for c in com.iter(W + 'comment'):
            t = ''.join(x.text or '' for x in c.iter(W + 't'))
            m = re.match(r'\s*\[([0-9a-f]{6,24})\]', t)
            if m:
                present[c.get(W + 'id')] = m.group(1)
    # רשימת ההערות שיצאו: פסקה נסתרת "SKIRA-IDS ..." בסוף הקובץ (הערה שנמחקה נעלמת, ולכן צריך את הרשימה)
    alltext = ' '.join(''.join(x.text or '' for x in p.iter(W + 't')) for p in doc.iter(W + 'p'))
    m = re.search(r'SKIRA-IDS ([0-9a-f ]+)', alltext)
    exported = set(m.group(1).split()) if m else set()
    items, seen = [], set()
    for ref in doc.iter(W + 'commentReference'):
        cid = ref.get(W + 'id')
        fid = present.get(cid)
        if not fid:
            continue
        seen.add(fid)
        # השינוי בעקוב בטווח ההערה
        start = next((s for s in doc.iter(W + 'commentRangeStart') if s.get(W + 'id') == cid), None)
        changed = False
        if start is not None:
            for sib in start.itersiblings():
                if sib.tag == W + 'commentRangeEnd' and sib.get(W + 'id') == cid:
                    break
                if sib.tag in (W + 'ins', W + 'del') or any(True for _ in sib.iter(W + 'ins', W + 'del')):
                    changed = True
        if changed:
            items.append({'id': fid, 'd': 'edit', 'rs': 'word', 'txt': 'שינוי בעקוב בוורד'})
    for fid in exported - seen:
        items.append({'id': fid, 'd': 'no', 'rs': 'word', 'txt': 'נמחקה בוורד'})
    print('הכרעות שנמצאו בוורד: %d (נערכו: %d, נמחקו: %d)' % (
        len(items), sum(1 for i in items if i['d'] == 'edit'), sum(1 for i in items if i['d'] == 'no')))
    if a.dry or not items:
        return
    import _api
    for i in items:
        i['t'] = int(__import__('time').time() * 1000)
    _api.call('/bakara/dec', 'POST', {'slug': a.slug, 'items': items})
    print('נרשמו.')


if __name__ == '__main__':
    main()
