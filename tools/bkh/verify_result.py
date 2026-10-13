# -*- coding: utf-8 -*-
"""verify_result.py - בדיקת שלמות של קובץ הוורד שנוצר: מחוץ לטווח לא השתנה דבר, בתוכו אין שאריות, ומה נכתב בשם מי.

    uv run --with lxml python verify_result.py <מקור.docx> <תוצאה.docx>
"""
import sys, io, re, json, collections
from bkh_common import *


def seq(path):
    d = Doc(path)
    ps = list(d.paragraphs())
    lo, hi = find_range(d)
    rows = [(d.pstyle(p), text_map(p)[0]) for p in ps]
    return d, ps, rows, lo, hi


def main(src, dst):
    ds, ps0, r0, lo0, hi0 = seq(src)
    dd, ps1, r1, lo1, hi1 = seq(dst)
    bad = []
    # מחוץ לטווח: זהה (טקסט וסגנון)
    pre0, pre1 = r0[:lo0], r1[:lo1]
    post0, post1 = r0[hi0:], r1[hi1:]
    if pre0 != pre1:
        bad.append('לפני הטווח: שינוי (%d פסקאות מול %d)' % (len(pre0), len(pre1)))
    if post0 != post1:
        bad.append('אחרי הטווח: שינוי (%d פסקאות מול %d)' % (len(post0), len(post1)))
    # בתוך הטווח
    inr = r1[lo1:hi1]
    issues = collections.Counter()
    for st, t in inr:
        if any(c in t for c in LONG_DASH):
            issues['מקף ארוך'] += 1
        if '⟦' in t or '⟧' in t:
            issues['סימון הסבר שנשאר'] += 1
        if '#' in t:
            issues['#'] += 1
        if st == 'חלון 3' and len(t.strip()) > 20:
            issues['עוגן ארוך מ-20'] += 1
        if st in ('Normal', '0.1', '0.2', 'List Paragraph', 'רווח לפני') and not t.strip():
            issues['פסקה ריקה'] += 1
        if st == 'חלון 3' and re.match(r'^\s*[·•]', t):
            issues['בולט בעוגן'] += 1
    # עוגנים רצופים
    prev = None
    for st, t in inr:
        if st == 'חלון 3' and prev == 'חלון 3':
            issues['שני עוגנים רצופים'] += 1
        prev = st
    auth = collections.Counter()
    for el in dd.doc.iter(q('ins'), q('del'), q('pPrChange')):
        auth[(el.tag.split('}')[1], el.get(q('author')))] += 1
    labels = [t.strip() for st, t in inr if st == DAF_STYLE]
    print('פסקאות בטווח: %d -> %d' % (hi0 - lo0, hi1 - lo1))
    print('ציוני דף בטווח:', len(labels), 'כפולים:', [x for x, c in collections.Counter(labels).items() if c > 1])
    print('בעיות מבנה מחוץ לטווח:', bad or 'אין')
    print('שאריות בתוך הטווח:', dict(issues) or 'אין')
    print('מחברים במעקב:', {'%s:%s' % k: v for k, v in auth.items() if k[1] in OWN_AUTHORS + PENDING_AUTHORS})
    return 1 if bad else 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main(sys.argv[1], sys.argv[2]))
