# -*- coding: utf-8 -*-
"""factory_place.py - הנחת כל הסימנים של תוספות במסכת בסדר המספרים (הוראת בעל הפרויקט, 13.10.2026).

הכלל: כל תוספות שמוצג באתר מונח, בלי יוצא מן הכלל, ומסודר לפי סדר המספרים לאורך כל המסכת:
  א. תוספות שעוגנו אינו נמצא (או שהעמוד שלו אינו בקובץ הלאוקמי גירסא) מונח בין התוספות שלפניו לשלאחריו, בצמוד הכי קרוב:
     בסוף השורה שבה מונח התוספות הקודם, ואם זה יסטה אחרי התוספות הבא, באותו עוגן של הקודם.
  ב. סדר: המיקום (עמוד, מקום בעמוד) של תוספות מספר n אינו לפני המיקום של n-1. כשיש התנגשות, שומרים את הקבוצה הגדולה ביותר
     (משקל כפול לתוספות שהמנהל הכריע בהם) ואת היתר מזיזים לפי כלל א. הזזה נרשמת (rule 3, why) ואינה שקטה.
  ג. שער: אחרי ההנחה נבדקת רציפות המספור (1 עד N בלי חור וכפילות בכל פרק) והסדר. כשל עוצר את הפרסום.
העוגן נשמר כקטע טקסט ומספר מופע (כמו בדפדפן, tosafot_ui.js), ולא כמיקום תו.

    uv run python tools/tosafot/factory_place.py berakhot
"""
import os, sys, re, json, io
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from make_anchors import norm_idx, norm_ctx, find_occ
from build_count import daf_order

ROOT = os.path.dirname(os.path.dirname(HERE))


def jload(p, d=None):
    return json.load(io.open(p, encoding='utf-8')) if os.path.exists(p) else d


def jdump(p, o):
    with io.open(p, 'w', encoding='utf-8') as f:
        json.dump(o, f, ensure_ascii=False, indent=1)


def perakim(slug):
    out = []
    for ch in jload(os.path.join(ROOT, 'tosafot', slug, 'chapters.json'))['chapters']:
        if os.path.exists(os.path.join(ROOT, 'tosafot', slug, 'count-%d.json' % ch['n'])):
            out.append(ch['n'])
    return out


def line_ends(lines):
    """סוף כל שורת לאוקמי באינדקס המנורמל של העמוד (המיקום אחרי המילה האחרונה)."""
    ends, acc = [], []
    for ln in lines:
        acc.append(ln)
        ends.append(len(norm_idx(acc)) - 1)
    return ends


def place_masechet(slug, write=True):
    base = os.path.join(ROOT, 'tosafot', slug)
    ctx = jload(os.path.join(base, 'context.json'), {})
    dec = (jload(os.path.join(base, 'decided.json'), {}) or {}).get('items', {})
    idxs, ends = {}, {}
    for dk, c in ctx.items():
        idxs[dk] = norm_idx(c['lines'])
        ends[dk] = line_ends(c['lines'])
    order_of = {}                                  # dafKey -> סדר העמוד במסכת
    items = []
    files = {}
    for p in perakim(slug):
        cnt = jload(os.path.join(base, 'count-%d.json' % p))
        sty = jload(os.path.join(base, 'styles-%d.json' % p), {})
        anc = jload(os.path.join(base, 'anchors-%d.json' % p), {'_comment': ''})
        files[p] = anc
        for r in cnt['items']:
            order_of[r['dafKey']] = daf_order(r['daf'])
            k = str(r['n'])
            st = sty.get(k)
            if not st or not (st.get('a') or st.get('b')):
                continue                           # לא מוצג באתר: אינו חלק מהסדר
            a = anc.get(k) or {}
            items.append({'perek': p, 'n': r['n'], 'k': k, 'dafKey': r['dafKey'], 'a': a, 'w': 2 if str(p * 1000 + r['n']) in dec else 1})
    # מיקום נוכחי לכל תוספות (או None)
    for it in items:
        a = it['a']
        page = a.get('page') or it['dafKey']
        it['page'] = page
        it['pos'] = None
        if a.get('t') and page in idxs:
            c = norm_ctx(a['t'])
            occs = find_occ(idxs[page], c) if c else []
            o = int(a.get('occ', 1))
            if 1 <= o <= len(occs):
                it['pos'] = (order_of.get(page, daf_order('2a')), occs[o - 1] + len(c))
    # הקבוצה הגדולה ביותר שאינה יורדת (לפי משקל): LIS משוקלל
    res = [it for it in items if it['pos'] is not None]
    best, prev = [], []
    for i, it in enumerate(res):
        b, pj = it['w'], -1
        for j in range(i):
            if res[j]['pos'] <= it['pos'] and best[j] + it['w'] > b:
                b, pj = best[j] + it['w'], j
        best.append(b)
        prev.append(pj)
    keep = set()
    if res:
        i = max(range(len(res)), key=lambda x: best[x])
        while i >= 0:
            keep.add(id(res[i]))
            i = prev[i]
    for it in items:
        if id(it) not in keep:
            it['pos'] = None                       # לא עוגן, או סותר את הסדר: יונח לפי השכנים
    moved = []
    last = None                                    # התוספות האחרון שהונח בסופו של דבר (פריט)
    for idx, it in enumerate(items):
        if it['pos'] is not None:
            last = it
            continue
        nxt = next((x for x in items[idx + 1:] if x['pos'] is not None), None)
        na = None
        if last is not None:
            lp = last['page']
            off = last['pos'][1]
            na = {'page': lp, 'pos': last['pos'], 't': last['a']['t'] if last['a'].get('t') else None, 'occ': last['a'].get('occ', 1)}
            # סוף השורה שבה מונח הקודם
            if lp in ends:
                e = next((x for x in ends[lp] if x >= off), None)
                if e is not None:
                    words = idxs[lp][:e + 1].split(' ')
                    for kk in (4, 3, 2, 1):
                        cand = ' '.join(words[-kk:]).strip()
                        occs = find_occ(idxs[lp], cand) if cand else []
                        hit = [i for i, o in enumerate(occs) if o + len(cand) == e + 1]
                        if hit:
                            newpos = (order_of.get(lp, 0), e + 1)
                            if nxt is None or newpos <= nxt['pos']:
                                na = {'page': lp, 'pos': newpos, 't': cand, 'occ': hit[0] + 1}
                            break
        elif nxt is not None:
            # אין קודם: תחילת העמוד של הבא (סוף השורה הראשונה שלו), ואם זה אחרי הבא, באותו עוגן של הבא
            np_ = nxt['page']
            na = {'page': np_, 'pos': nxt['pos'], 't': nxt['a'].get('t'), 'occ': nxt['a'].get('occ', 1)}
            if np_ in ends and ends[np_]:
                e = ends[np_][0]
                words = idxs[np_][:e + 1].split(' ')
                for kk in (4, 3, 2, 1):
                    cand = ' '.join(words[-kk:]).strip()
                    occs = find_occ(idxs[np_], cand) if cand else []
                    hit = [i for i, o in enumerate(occs) if o + len(cand) == e + 1]
                    if hit:
                        newpos = (order_of.get(np_, 0), e + 1)
                        if newpos <= nxt['pos']:
                            na = {'page': np_, 'pos': newpos, 't': cand, 'occ': hit[0] + 1}
                        break
        if na is None or not na.get('t'):
            raise SystemExit('עצירה: אי אפשר להניח את תוספות %d-%d (אין שכן עם הקשר בעמוד)' % (it['perek'], it['n']))
        it['pos'] = na['pos']
        it['page'] = na['page']
        old = dict(it['a']) if it['a'] else None
        anc = files[it['perek']]
        newa = {'daf': it['dafKey'], 't': na['t'], 'occ': na['occ'], 'rule': 3,
                'why': 'הוצמד בצמוד לתוספות הקודם (בסוף שורתו), לפי סדר המספרים'}
        if na['page'] != it['dafKey']:
            newa['page'] = na['page']
        anc[it['k']] = newa
        it['a'] = newa
        moved.append({'perek': it['perek'], 'n': it['n'], 'to': na['page'], 'was': (old or {}).get('t', '')})
        last = it
    # שער: סדר ורציפות
    errs = []
    prevpos = None
    for it in items:
        if prevpos is not None and it['pos'] < prevpos:
            errs.append('הסדר נשבר בתוספות %d-%d' % (it['perek'], it['n']))
        prevpos = it['pos']
    for p in perakim(slug):
        cnt = jload(os.path.join(base, 'count-%d.json' % p))
        ns = [r['n'] for r in cnt['items']]
        if ns != list(range(1, len(ns) + 1)):
            errs.append('המספור בפרק %d אינו רציף 1 עד %d' % (p, len(ns)))
        if len(set(r['hn'] for r in cnt['items'])) != len(ns):
            errs.append('כפילות בציון האותיות בפרק %d' % p)
    rep = {'slug': slug, 'shown': len(items), 'moved': moved, 'errors': errs, 'ok': not errs}
    if write:
        for p, anc in files.items():
            jdump(os.path.join(base, 'anchors-%d.json' % p), anc)
        jdump(os.path.join(base, 'order-check.json'), rep)
    return rep


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    r = place_masechet(sys.argv[1], write='--dry' not in sys.argv)
    print('מוצגים %d, הוזזו או הונחו לפי שכנים %d, שגיאות %d' % (r['shown'], len(r['moved']), len(r['errors'])))
    for e in r['errors']:
        print('שגיאה:', e)
    for m in r['moved'][:40]:
        print('  ', m)
