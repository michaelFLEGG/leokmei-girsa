# -*- coding: utf-8 -*-
"""publish.py - מעביר ממצאים שעברו את שער ההדלפה אל מערכת הבקרה הקיימת (engine.py merge), ולא יותר.

    uv run --with lxml python tools/hv/publish.py <slug> <מדף> <עד דף> [--tag T] [--code-only] [--push]

 * --tag: תג הרצה של review.py (קובץ public-<תג>.json). בלעדיו: רק מועמדי הקוד המהותיים (עומק "מהירה").
 * ברירת מחדל: בלי דחיפה לנקודת הקליטה (--no-push של engine.merge). --push: שולח, והממצאים מופיעים למנהל באתר.
 * בדיקה אחרונה לפני הכתיבה: שער הדלפה שני מול כל חבילות הדפים בטווח (חמש מילים רצופות מלשון חברותא = עצירה).
 * מונע כתיבה לציבורי של כל מה שלא עבר: ממצא חסום נשאר בריפו הפרטי.
"""
import os, sys, re, json, argparse, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hv_common as H
from hv_common import C
sys.path.insert(0, os.path.join(H.TOOLS, 'skira'))
import engine


def second_gate(rows, slug):
    ch = {}
    d = os.path.join(H.CHAV, 'packs', slug)
    ok, bad = [], []
    for r in rows:
        if r['daf'] not in ch:
            pk = H.jload(os.path.join(d, H.file_of_label(r['daf']) + '.json'), {})
            ch[r['daf']] = ' '.join([s['explain'] for s in pk.get('segs', [])] + [n['text'] for n in pk.get('notes', [])])
        body = ' '.join([r.get('note', ''), r.get('fix', '')] + list(r.get('alts') or []))
        (bad if H.ngram_overlap(body, ch[r['daf']], 5) else ok).append(r)
    return ok, bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('slug')
    ap.add_argument('d_from')
    ap.add_argument('d_to')
    ap.add_argument('--tag')
    ap.add_argument('--code-only', action='store_true')
    ap.add_argument('--push', action='store_true')
    a = ap.parse_args()
    rows = []
    if a.tag:
        rows += H.jload(os.path.join(H.CHAV, 'review', a.slug, 'public-' + a.tag + '.json'), []) or []
    k0, k1 = C.daf_key(a.d_from), C.daf_key(a.d_to)
    if a.code_only or not a.tag:
        for c in H.jload(os.path.join(H.CHAV, 'candidates', a.slug + '.json'), []) or []:
            if c['sev'] == 'בינוני' and k0 <= C.daf_key(c['daf']) <= k1:
                rows.append({k: v for k, v in c.items() if k != 'hv'})
    ok, bad = second_gate(rows, a.slug)
    if bad:
        print('נחסמו בשער ההדלפה השני: %d (לא יועלו)' % len(bad))
    ns = type('A', (), {'slug': a.slug, 'd_from': a.d_from, 'd_to': a.d_to, 'depth': 'fast', 'pages': 10, 'force': False,
                        'no_push': not a.push})()
    w = engine.workdir(a.slug, a.d_from, a.d_to)
    if not os.path.exists(os.path.join(w, 'meta.json')):
        engine.prep(ns)
    for old in os.listdir(os.path.join(w, 'review-out')):
        if old.startswith('R_hv'):
            os.remove(os.path.join(w, 'review-out', old))
    outp = os.path.join(w, 'review-out', 'R_hv_%s.json' % (a.tag or 'code'))
    H.jsave(outp, [{k: v for k, v in r.items() if k in ('i', 'daf', 'kind', 'mark', 'note', 'fix', 'alts', 'conf', 'sev', 'evidence')}
                   for r in ok])
    print('ממצאים שנכנסו למיזוג: %d · קובץ: %s' % (len(ok), outp))
    # engine.merge רושם טביעות "נסקרו" לכל פסקאות הטווח; כאן הורצה רק שכבת חברותא, לא המיון הרגיל,
    # ולכן מחזירים את המטמון כפי שהיה (אחרת הסקירה הרגילה תדלג על פסקאות שלא נסקרו).
    cache_path = os.path.join(C.DATA, 'reviewed-%s.json' % a.slug)
    before = open(cache_path, 'rb').read() if os.path.exists(cache_path) else None
    try:
        engine.merge(ns)
    finally:
        if before is None:
            if os.path.exists(cache_path):
                os.remove(cache_path)
        else:
            open(cache_path, 'wb').write(before)


if __name__ == '__main__':
    main()
