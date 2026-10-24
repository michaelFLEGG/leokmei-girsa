# -*- coding: utf-8 -*-
"""handoff_prep.py - הכנת הקלט של מפעל התוס' בחשבון השני (24.10.2026): קוד בלבד, בלי מודל.

לכל פרק שיש לו ספירה (count-<פרק>.json) והקשר (context.json) ושלא פורסם עדיין, נבנות "יחידות" של כ-24 תוספות לפי סדר הדף,
בלי לפצל עמוד באמצע כשאפשר. כל יחידה עצמאית לגמרי: הפנים, הד"ה, שורות הלאוקמי והגמרא של כל עמוד, בקשות הכתיבה מורכבות
כבר (page_user_msg), הנחיית המבקר V2 עם הדוגמאות הרלוונטיות, ו-1 עד 2 תוספות כיול נסתר שהמנהל כבר הכריע בהם.
מה שהמנהל הכריע (decided.json) אינו נכנס. תשובות כתיבה ששולמו ונשלפו מ-Batch (tosafot/handoff/salvage/) נכנסות כ-prewritten.

פלט: tosafot/handoff/units/<id>.json, tosafot/handoff/index.json, tosafot/handoff/prep-report.json
יחידות קיימות אינן נבנות מחדש (המזהים יציבים; החשבון השני כבר עובד עליהן). --force בונה מחדש פרק שעוד אין לו תוצר.

    uv run python tools/tosafot/handoff_prep.py            # כל מה שמוכן
    uv run python tools/tosafot/handoff_prep.py --dry      # רק דוח, בלי כתיבה
"""
import os, sys, re, json, io, random, datetime, argparse
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import factory as F
import factory_flow as FF
import gates as G
from factory import fp, jload, jdump, ukey, rid

HO = fp('handoff')
UNIT_TARGET = 24
UNIT_MAX = 30          # עמוד שלם נכנס ליחידה כל עוד היא אינה עוברת 30; עמוד גדול מ-30 מתפצל
NO_WORD = ('shekalim', 'tamid')   # אין קובץ וורד באתר: בסוף הסדר


def cfg_snapshot(c):
    return {k: c[k] for k in ('line', 'question', 'hard', 'maxPerRequest')}


def published(slug, perek):
    st = F.state(slug)
    return (st.get('perakim', {}).get(str(perek)) or {}).get('status') == 'published'


def live_keys(slug, perek):
    sp = fp(slug, 'styles-%d.json' % perek)
    return set(k for k in (jload(sp) or {}) if not k.startswith('_'))


def salvage_answers(slug, perek):
    """{rid: (תשובה, מודל)} מתוך תשובות Batch ששולמו. המיפוי cid -> מזהים מקובץ העבודה הישן."""
    sv = jload(os.path.join(HO, 'salvage', '%s-%d.json' % (slug, perek)))
    if not sv:
        return {}
    work = jload(fp(F.FDIR, 'work-%s-%d.json' % (slug, perek))) or {}
    out = {}
    for cid, res in sv['results'].items():
        meta = (work.get('reqs') or {}).get(cid)
        if not meta or meta.get('cal') or not res.get('ok'):
            continue
        try:
            got = G.parse_json(res['text'])
        except Exception:
            continue
        if not isinstance(got, dict):
            continue
        for i in meta['ids']:
            if isinstance(got.get(i), dict):
                out[i] = (got[i], res.get('model') or meta.get('model'))
    return out


def cal_pool():
    pool = []
    for sl in F.queue():
        dec = F.decided_map(sl)
        if not dec:
            continue
        ctxj = jload(fp(sl, 'context.json')) or {}
        for p in FF.counted_perakim(sl):
            for r in F.load_count(sl, p)['items']:
                k = str(ukey(p, r['n']))
                if k in dec and dec[k].get('text') and r['dafKey'] in ctxj:
                    pool.append((sl, p, r))
    return pool


def split_units(pages):
    """[(dafKey, daf, [recs])] -> רשימת יחידות, כל אחת רשימת עמודים (עמוד גדול מ-UNIT_MAX מתפצל)."""
    units, cur, n = [], [], 0
    for dk, daf, recs in pages:
        chunks = [recs[i:i + UNIT_TARGET] for i in range(0, len(recs), UNIT_TARGET)] if len(recs) > UNIT_MAX else [recs]
        for ch in chunks:
            if cur and n + len(ch) > UNIT_MAX:
                units.append(cur)
                cur, n = [], 0
            cur.append((dk, daf, ch))
            n += len(ch)
            if n >= UNIT_TARGET:
                units.append(cur)
                cur, n = [], 0
    if cur:
        units.append(cur)
    return units


def build_unit(uid, slug, perek, order, upages, c, ctxj, salv, pool, examples, sysT_len):
    meta = {'masechet': FF.masechet_name(slug)}
    recs, pages, write, pre = {}, {}, [], {}
    for dk, daf, rs in upages:
        ctxp = FF.ctx_page(ctxj, dk, daf, slug)
        pages[dk] = {'daf': daf, 'lines': ctxp['lines'], 'gemara': ctxp['gemara'], 'missing': bool(ctxp.get('missing'))}
        normal, hard = [], []
        for r in rs:
            rr = FF.make_rec(slug, perek, r, dk, daf)
            h = F.is_hard(r, c)
            recs[rr['rid']] = {'n': r['n'], 'perek': perek, 'key': rr['key'], 'hn': r['hn'], 'dh': r['dh'], 'text': r['text'], 'daf': daf,
                               'dafKey': dk, 'line': r['line'], 'ref': r['ref'], 'url': r.get('url', ''), 'hard': h}
            (hard if h else normal).append(rr)
        groups = [(normal[i:i + c['maxPerRequest']], 'sonnet') for i in range(0, len(normal), c['maxPerRequest'])]
        groups += [([h], 'fable') for h in hard]
        for gi, (g, model) in enumerate(groups):
            cid = 'w-%s-p%d-%s-%d' % (slug, perek, daf, gi)
            ids = [x['rid'] for x in g]
            write.append({'cid': cid, 'model': model, 'ids': ids, 'dafKey': dk, 'daf': daf,
                          'user': G.page_user_msg(slug, perek, dk, meta, g, ctxp)})
            if ids and all(i in salv for i in ids):
                pre[cid] = {'model': salv[ids[0]][1], 'text': json.dumps({i: salv[i][0] for i in ids}, ensure_ascii=False)}
    # כיול נסתר: 1 עד 2 תוספות שהמנהל הכריע בהם, בבקשה רגילה בפני עצמה (מזהה שאינו מסגיר שהוא כיול)
    rnd = random.Random('cal-' + uid)
    want = 2 if len(recs) >= 18 else 1
    cand = [x for x in pool if rid(x[1], x[2]['n']) not in recs]
    for k, (sl, p, r) in enumerate(rnd.sample(cand, min(want, len(cand)))):
        cctx = jload(fp(sl, 'context.json'))[r['dafKey']]
        rr = FF.make_rec(sl, p, r, r['dafKey'], r['daf'])
        recs[rr['rid']] = {'n': r['n'], 'perek': p, 'key': rr['key'], 'hn': r['hn'], 'dh': r['dh'], 'text': r['text'], 'daf': r['daf'],
                           'dafKey': r['dafKey'], 'line': r['line'], 'ref': r['ref'], 'url': r.get('url', ''), 'hard': False,
                           'cal': {'slug': sl, 'perek': p, 'n': r['n'], 'key': str(ukey(p, r['n']))}}
        write.append({'cid': 'w-%s-p%d-%s-%d' % (sl, p, r['daf'], 9 + k), 'model': 'sonnet', 'ids': [rr['rid']], 'dafKey': r['dafKey'],
                      'daf': r['daf'], 'cal': True, 'user': G.page_user_msg(sl, p, r['dafKey'], {'masechet': FF.masechet_name(sl)}, [rr], cctx)})
    real = [(v['text'], '') for v in recs.values() if not v.get('cal')]
    unit = {'id': uid, 'slug': slug, 'perek': perek, 'masechet': meta['masechet'], 'order': order, 'version': 1,
            'created': F.now_iso(), 'cfg': cfg_snapshot(c), 'ntos': len(real), 'recs': recs, 'pages': pages, 'write': write,
            'review_system': G.system_with_examples(examples, real)}
    if pre:
        unit['prewritten'] = pre
    return unit


def plan():
    """סדר העבודה: (slug, [פרקים], סוג). קודם השלמת שלמות, אחר כך כתובות ומכות, קידושין ב עד ד, ואז התור מסנהדרין ואילך."""
    q = F.queue()
    first = ['ketubot', 'makkot', 'kiddushin']
    rest = [s for s in q[q.index('sanhedrin'):] if s not in first] if 'sanhedrin' in q else []
    rest = [s for s in rest if s not in NO_WORD] + [s for s in rest if s in NO_WORD]
    done = [s for s in q if s not in first and s not in rest]
    return done, first + rest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry', action='store_true')
    ap.add_argument('--only', default='')
    a = ap.parse_args()
    c = F.cfg()
    examples = (jload(fp('triage', 'examples.json')) or {}).get('items', [])
    pool = cal_pool()
    idx_path = os.path.join(HO, 'index.json')
    index = jload(idx_path) or {'version': 1, 'created': F.now_iso(), 'units': [], 'redo': []}
    have = {u['id'] for u in index['units']}
    have_pk = {(u['slug'], u['perek']) for u in index['units'] if not u.get('fill')}
    done_slugs, todo_slugs = plan()
    only = set(x for x in a.only.split(',') if x)
    rep = {'at': F.now_iso(), 'completeness': [], 'units': 0, 'tos': 0, 'by': {}, 'skipped': [], 'prewritten': 0}
    new_units = []

    def add(u):
        new_units.append(u)
        rep['units'] += 1
        rep['tos'] += u['ntos']
        rep['by'].setdefault(u['slug'], [0, 0])
        rep['by'][u['slug']][0] += 1
        rep['by'][u['slug']][1] += u['ntos']
        rep['prewritten'] += len(u.get('prewritten') or {})

    # א. בדיקת שלמות בפרקים שפורסמו: תוספות בספירה שאין לו שורה חיה (מוכרע / תקין / מסומן)
    for slug in done_slugs + todo_slugs:      # כל פרק שפורסם, גם במסכת שעוד לא הושלמה (קידושין פרק א)
        if only and slug not in only:
            continue
        ctxj = jload(fp(slug, 'context.json')) or {}
        dec = F.decided_map(slug)
        for p in FF.counted_perakim(slug):
            if not published(slug, p):
                continue
            lk = live_keys(slug, p)
            miss = [r for r in F.load_count(slug, p)['items'] if str(r['n']) not in lk and str(ukey(p, r['n'])) not in dec]
            if not miss:
                continue
            rep['completeness'].append({'slug': slug, 'perek': p, 'missing': [r['n'] for r in miss]})
            uid = '%s-p%02d-u90' % (slug, p)
            if uid in have:
                continue
            by, odr = {}, []
            for r in miss:
                k = (r['dafKey'], r['daf'])
                if k not in by:
                    by[k] = []
                    odr.append(k)
                by[k].append(r)
            pages = [(k[0], k[1], by[k]) for k in odr]
            u = build_unit(uid, slug, p, 0, pages, c, ctxj, {}, pool, examples, 0)
            u['fill'] = True
            add(u)
    # ב. הפרקים שלא פורסמו, לפי הסדר
    for slug in todo_slugs:
        if only and slug not in only:
            continue
        pers = FF.counted_perakim(slug)
        ctxj = jload(fp(slug, 'context.json'))
        if not pers or not ctxj:
            rep['skipped'].append({'slug': slug, 'why': 'אין ספירה או הקשר (ההכנה טרם הסתיימה)'})
            continue
        for p in pers:
            if published(slug, p) or (slug, p) in have_pk:
                continue
            pages = F.pages_of(slug, p)
            if not pages:
                continue
            salv = salvage_answers(slug, p)
            for ui, upages in enumerate(split_units(pages), 1):
                uid = '%s-p%02d-u%02d' % (slug, p, ui)
                add(build_unit(uid, slug, p, 0, upages, c, ctxj, salv, pool, examples, 0))
    # הסדר (שדה order): יחידות השלמה בראש, אחריהן לפי סדר התוכנית (מסכת, פרק, יחידה). ממוספר מחדש בכל הרצה, כדי שמסכת
    # שההכנה שלה הסתיימה מאוחר תיכנס במקומה בתור ולא בסופו. המזהים אינם משתנים.
    rank = {s_: i for i, s_ in enumerate(done_slugs + todo_slugs)}

    def key(u):
        return (0 if u.get('fill') else 1, rank.get(u['slug'], 999), u['perek'], u['id'])
    if a.dry:
        print(json.dumps({k: v for k, v in rep.items()}, ensure_ascii=False, indent=1))
        return
    for u in new_units:
        index['units'].append({'id': u['id'], 'slug': u['slug'], 'perek': u['perek'], 'order': 0, 'ntos': u['ntos'],
                               **({'fill': True} if u.get('fill') else {})})
    index['units'].sort(key=key)
    orders = {}
    for i, u in enumerate(index['units'], 1):
        u['order'] = i
        orders[u['id']] = i
    for u in new_units:
        u['order'] = orders[u['id']]
        jdump(os.path.join(HO, 'units', u['id'] + '.json'), u)
    index['updated'] = F.now_iso()
    index.setdefault('redo', [])
    jdump(idx_path, index)
    rep['total_units'] = len(index['units'])
    rep['total_tos'] = sum(u['ntos'] for u in index['units'])
    jdump(os.path.join(HO, 'prep-report.json'), rep)
    print('נבנו %d יחידות חדשות (%d תוספות, %d בקשות כתיבה מוכנות מראש). באינדקס: %d יחידות, %d תוספות.'
          % (rep['units'], rep['tos'], rep['prewritten'], rep['total_units'], rep['total_tos']))
    for x in rep['completeness']:
        print('  השלמה: %s פרק %d: %d תוספות בלי שורה חיה' % (x['slug'], x['perek'], len(x['missing'])))
    for x in rep['skipped']:
        print('  דילוג: %s (%s)' % (x['slug'], x['why']))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
