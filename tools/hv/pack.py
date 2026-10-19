# -*- coding: utf-8 -*-
"""pack.py - שלב 1: יישור חברותא מול לאוקמי וחבילת ידע לכל עמוד (קוד בלבד, אפס טוקנים).

    uv run --with lxml python tools/hv/pack.py <מסכת בעברית|all> [--force]

לכל עמוד חברותא: מיישר (תכנות דינמי, סדר רציף) את שורות חברותא אל פסקאות לאוקמי של אותו דף (+שוליים משכנים),
ורושם לכל שורה פסקה וציון ביטחון. נכתב לריפו הפרטי: packs/<slug>/<עמוד>.json. מטמון: חותמת תוכן של פסקאות הדף
וקובץ חברותא - עמוד שלא השתנה אינו נבנה מחדש.
"""
import os, sys, json, hashlib, argparse, time, math
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hv_common as H
from hv_common import C

TAU = 0.12          # סף: שורה שציונה מתחתיו אינה "מותאמת"
MARGIN = 3          # פסקאות שוליים משני הדפים השכנים


def align(segs, paras):
    """יישור רציף: מחזיר ({אינדקס שורה: (אינדקס פסקה, ציון)}, מקסימום ציון לכל שורה)."""
    if not segs or not paras:
        return {}, [0] * len(segs)
    G = [H.grams(s['text']) for s in segs]
    P = [H.grams(p['text']) for p in paras]
    df = Counter()
    for g in G + P:
        for k in g:
            df[k] += 1
    N = len(G) + len(P)
    idf = {k: math.log(1 + N / v) for k, v in df.items()}
    S = [[H.cos(g, p, idf) for p in P] for g in G]
    n, m = len(G), len(P)
    dp = [[0.0] * (m + 1) for _ in range(n + 1)]
    ch = [[None] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            best, c = dp[i][j - 1], 'L'
            if dp[i - 1][j] > best:
                best, c = dp[i - 1][j], 'U'
            v = dp[i - 1][j] + S[i - 1][j - 1] - TAU
            if v > best:
                best, c = v, 'D'
            dp[i][j], ch[i][j] = best, c
    i, j, al = n, m, {}
    while i > 0 and j > 0:
        c = ch[i][j]
        if c == 'L':
            j -= 1
        elif c == 'U':
            i -= 1
        else:
            al[i - 1] = (j - 1, round(S[i - 1][j - 1], 3))
            i -= 1
    return al, [round(max(r), 3) if r else 0 for r in S]


def blocks_for(heb):
    """פסקאות הוורד של המסכת. קודם לפי status.json (docx_for); ואם אין, לפי כללי build_all (קובץ שתי מסכתות, איחוד שני קבצים)."""
    from ingest_edits import docx_for, DRIVE
    from docx2json import convert
    try:
        return convert(docx_for(heb))
    except BaseException:
        pass
    import build_all
    files = [f for f in os.listdir(DRIVE) if f.endswith('.docx') and not f.startswith('~$')]
    cands = []
    for f in files:
        sp = build_all.split_of(f)
        if sp and heb in sp:
            res = build_all.split_file(os.path.join(DRIVE, f), sp)
            if res:
                return dict(res)[heb]
        elif not sp and build_all.masechet_of(f) == heb:
            cands.append(f)
    if len(cands) == 1:
        return convert(os.path.join(DRIVE, cands[0]))
    if len(cands) > 1:
        return build_all.merge_masechet(heb, cands, DRIVE)[0]
    raise SystemExit('לא נמצא קובץ וורד למסכת ' + heb)


def build(heb, force=False):
    slug = H.heb_to_slug().get(heb)
    if not slug:
        raise SystemExit('עצירה: מסכת לא מוכרת: ' + heb)
    blocks = blocks_for(heb)
    by_key = {}
    for b in blocks:
        k = C.daf_key(b.get('daf'))
        if k is None or len(H.norm(b['text'])) < 2:
            continue
        by_key.setdefault(k, []).append(b)
    keys = sorted(by_key)
    src = H.jload(os.path.join(H.ROOT, 'data', 'sources', slug + '.json'), {}) or {}
    files = sorted(os.listdir(H.chav_json_dir(heb))) if os.path.isdir(H.chav_json_dir(heb)) else []
    outdir = os.path.join(H.CHAV, 'packs', slug)
    cov = {'slug': slug, 'heb': heb, 'chavruta_pages': 0, 'with_our_text': 0, 'without_our_text': [], 'built': 0, 'cached': 0,
           'sources_pages': len(src.get('pages') or {})}
    for fn in files:
        if not fn.endswith('.json'):
            continue
        lbl = H.daf_label_of_file(fn)
        k = C.daf_key(lbl)
        cov['chavruta_pages'] += 1
        ours = by_key.get(k)
        if not ours:
            cov['without_our_text'].append(lbl)
            continue
        cov['with_our_text'] += 1
        ch = H.jload(os.path.join(H.chav_json_dir(heb), fn), {})
        segs = [dict(s, k=n) for n, s in enumerate(ch.get('segments') or []) if (s.get('text') or '').strip()]
        sig = hashlib.sha1((json.dumps([b['text'] for b in ours], ensure_ascii=False) +
                            json.dumps([s['text'] for s in segs], ensure_ascii=False)).encode('utf-8')).hexdigest()[:14]
        outp = os.path.join(outdir, H.file_of_label(lbl) + '.json')
        old = H.jload(outp, None)
        if old and old.get('sig') == sig and not force:
            cov['cached'] += 1
            continue
        pos = keys.index(k)
        before = by_key[keys[pos - 1]][-MARGIN:] if pos > 0 else []
        after = by_key[keys[pos + 1]][:MARGIN] if pos + 1 < len(keys) else []
        cand = [dict(i=b['i'], style=b['style'], text=b['text'], ext=-1) for b in before] + \
               [dict(i=b['i'], style=b['style'], text=b['text'], ext=0) for b in ours] + \
               [dict(i=b['i'], style=b['style'], text=b['text'], ext=1) for b in after]
        al, mx = align(segs, cand)
        sg = []
        for n, s in enumerate(segs):
            a = al.get(n)
            sg.append({'k': s['k'], 'marker': s.get('marker'), 'gemara': s.get('gemara', ''), 'explain': s.get('explain', ''),
                       'refs': s.get('refs') or [], 'para': cand[a[0]]['i'] if a else None, 'sim': a[1] if a else None,
                       'best': mx[n], 'edge': cand[a[0]]['ext'] if a else None})
        pg = (src.get('pages') or {}).get(lbl) or {}
        pack = {'slug': slug, 'daf': lbl, 'sig': sig, 'source_url': ch.get('source_url'), 'intro': ch.get('intro') or [],
                'markers': ch.get('markers'), 'notes': ch.get('notes') or [], 'warnings': ch.get('warnings') or [],
                'paras': [{'i': c['i'], 'style': c['style'], 'text': c['text'], 'ext': c['ext']} for c in cand],
                'segs': sg, 'has_perush': bool(pg.get('perush')), 'n_gemara': len(pg.get('gemara') or [])}
        H.jsave(outp, pack)
        cov['built'] += 1
    return cov


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('masechet')
    ap.add_argument('--force', action='store_true')
    a = ap.parse_args()
    if not H.CHAV:
        raise SystemExit('עצירה: ריפו חברותא (leokmei-chavruta) לא נמצא. הגדר LK_CHAVRUTA.')
    names = [a.masechet] if a.masechet != 'all' else sorted(h for h in H.heb_to_slug() if os.path.isdir(H.chav_json_dir(h)))
    allc = []
    for h in names:
        t0 = time.time()
        try:
            c = build(h, a.force)
        except BaseException as e:             # מסכת בלי קובץ וורד וכד': נרשמת בדוח הכיסוי, לא נבלעת
            print('דילוג %s: %s' % (h, str(e)[:160]))
            c = {'heb': h, 'error': str(e)[:200]}
        allc.append(c)
        print(h, {k: v for k, v in c.items() if k != 'without_our_text'}, 'שניות %.0f' % (time.time() - t0))
    prev = [c for c in (H.jload(os.path.join(H.CHAV, 'coverage-hv.json'), []) or []) if c.get('heb') not in names]
    H.jsave(os.path.join(H.CHAV, 'coverage-hv.json'), prev + allc)


if __name__ == '__main__':
    main()
