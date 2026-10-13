# -*- coding: utf-8 -*-
"""factory_flow.py - מכונת המצבים של בית החרושת לתוספות (ראו factory.py לתיאור). כאן: בקשות, קליטה, פרסום ופעימה."""
import os, sys, re, json, io, time, random, hashlib, datetime, subprocess, argparse
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import factory as F
from factory import (fp, jload, jdump, log, cfg, state, save_state, now_iso, ukey, rid, FDIR, norm_idx, norm_ctx, find_occ, NIK)


class Halt(Exception):
    """עצירה רועשת: נרשמת בקובץ המצב וביומן, והפעימה מסתיימת."""


# ---------------------------------------------------------------- קבצי עבודה של פרק
def work_path(slug, perek):
    return fp(FDIR, 'work-%s-%d.json' % (slug, perek))


def load_work(slug, perek):
    return jload(work_path(slug, perek)) or {'reqs': {}, 'recs': {}, 'cal': [], 'batches': {}}


def save_work(slug, perek, w):
    jdump(work_path(slug, perek), w)


def ctx_of(slug):
    j = jload(fp(slug, 'context.json'))
    if not j:
        raise Halt('אין context.json למסכת %s (להריץ את שלב ההכנה, tosafot-prep)' % slug)
    return j


def masechet_name(slug):
    return jload(fp(slug, 'chapters.json'))['masechet']


def mk_req(cid, model, system_text, user, max_tokens):
    return {'custom_id': cid, 'params': {'model': model, 'max_tokens': max_tokens, 'system': F.sys_blocks(system_text),
                                         'messages': [{'role': 'user', 'content': user}]}}


def make_rec(slug, perek, r, dafKey, daf):
    return {'rid': rid(perek, r['n']), 'key': ukey(perek, r['n']), 'n': r['n'], 'perek': perek, 'hn': r['hn'], 'dh': r['dh'],
            'daf': daf, 'dafKey': dafKey, 'line': r['line'], 'ref': r['ref'], 'url': r.get('url', ''), 'text': r['text'], 'tries': 1}


def counted_perakim(slug):
    return [ch['n'] for ch in F.chapters(slug) if os.path.exists(fp(slug, 'count-%d.json' % ch['n']))]


# ---------------------------------------------------------------- בקשות
def build_write(slug, perek, c, work):
    ctxj = ctx_of(slug)
    meta = {'masechet': masechet_name(slug)}
    sysT = F.system_prompt()
    reqs = []
    for dafKey, daf, recs in F.pages_of(slug, perek):
        if dafKey not in ctxj:
            raise Halt('אין הקשר לעמוד %s (%s) בקובץ ההקשר' % (dafKey, slug))
        ctxp = ctxj[dafKey]
        normal, hard = [], []
        for r in recs:
            rr = make_rec(slug, perek, r, dafKey, daf)
            work['recs'][rr['rid']] = rr
            (hard if F.is_hard(r, c) else normal).append(rr)
        groups = [(normal[i:i + c['maxPerRequest']], c['engines']['write']) for i in range(0, len(normal), c['maxPerRequest'])]
        groups += [([h], c['engines']['hard']) for h in hard]
        for gi, (g, model) in enumerate(groups):
            cid = 'w-%s-p%d-%s-%d' % (slug, perek, daf, gi)
            um = F.page_user_msg(slug, perek, dafKey, meta, g, ctxp)
            reqs.append(mk_req(cid, model, sysT, um, c['maxTokens']['perTos'] * max(1, len(g)) + 800))
            work['reqs'][cid] = {'ids': [x['rid'] for x in g], 'dafKey': dafKey, 'daf': daf, 'model': model}
            for x in g:
                work['recs'][x['rid']]['engine'] = model
    reqs += build_calibration(slug, perek, c, work, sysT)
    return reqs


def build_calibration(slug, perek, c, work, sysT):
    """שמירה מפני סחיפה: 3 עד 5 תוספות שהמנהל כבר הכריע בהם נכתבות מחדש בכל אצווה (כיול נסתר)."""
    pool = []
    for sl in c['queue']:
        dec = F.decided_map(sl)
        if not dec:
            continue
        for p in counted_perakim(sl):
            for r in F.load_count(sl, p)['items']:
                k = str(ukey(p, r['n']))
                if k in dec and dec[k].get('text'):
                    pool.append((sl, p, r, dec[k]['text']))
    if not pool:
        return []
    rnd = random.Random('cal-%s-%d' % (slug, perek))
    pick = rnd.sample(pool, min(c['calibration']['perBatch'], len(pool)))
    reqs = []
    for i, (sl, p, r, final) in enumerate(pick):
        ctxj = ctx_of(sl)
        if r['dafKey'] not in ctxj:
            continue
        rr = make_rec(sl, p, r, r['dafKey'], r['daf'])
        cid = 'cal-%s-p%d-%d' % (slug, perek, i)
        um = F.page_user_msg(sl, p, r['dafKey'], {'masechet': masechet_name(sl)}, [rr], ctxj[r['dafKey']])
        reqs.append(mk_req(cid, c['engines']['write'], sysT, um, c['maxTokens']['perTos'] + 800))
        work['reqs'][cid] = {'ids': [rr['rid']], 'cal': True, 'slug': sl, 'perek': p, 'final': final, 'dafKey': r['dafKey']}
    return reqs


def tidy_q(q):
    if not isinstance(q, dict):
        return {'t': '', 'lvl': '', 'q': '', 'a': ''}
    return {'t': F.norm_type(q.get('t')), 'lvl': q.get('lvl'), 'q': str(q.get('q', '')).strip(), 'a': str(q.get('a', '')).strip()}


def add_usage(acc, res):
    u = acc.setdefault(res['model'], {'in': 0, 'cw': 0, 'cr': 0, 'out': 0, 'n': 0})
    for k in ('in', 'cw', 'cr', 'out'):
        u[k] += res['usage'][k]
    u['n'] += 1


def variety_pass(work):
    by_daf = {}
    for r in work['recs'].values():
        if r.get('q'):
            by_daf.setdefault(r['dafKey'], []).append(r)
    for dk, rs in by_daf.items():
        rs.sort(key=lambda x: x['n'])
        for ri, qi in F.check_page_variety(rs):
            r = work['recs'][ri]
            r.setdefault('bad_q', {}).setdefault(str(qi), [])
            if 'גיוון' not in r['bad_q'][str(qi)]:
                r['bad_q'][str(qi)].append('גיוון')


def ingest_write(slug, perek, c, work, results):
    ctxj = ctx_of(slug)
    idxs = {}
    stats = {'ok': 0, 'bad': 0, 'api': 0}
    usage = {}
    for cid, res in results.items():
        meta = work['reqs'].get(cid)
        if not meta:
            continue
        if res.get('ok'):
            add_usage(usage, res)
        if meta.get('cal'):
            if res.get('ok'):
                try:
                    got = F.parse_json(res['text'])
                    s = list(got.values())[0].get('s', '')
                    work['cal'].append({'key': meta['ids'][0], 'sim': round(F.similarity(s, meta['final']), 3)})
                except Exception:
                    work['cal'].append({'key': meta['ids'][0], 'sim': 0.0, 'err': 'parse'})
            continue
        if not res.get('ok'):
            for i in meta['ids']:
                work['recs'][i].update({'bad_s': ['api:' + str(res.get('err'))], 'bad_a': True, 'q': [], 'bad_q': {}})
                stats['api'] += 1
            continue
        try:
            got = F.parse_json(res['text'])
        except Exception:
            for i in meta['ids']:
                work['recs'][i].update({'bad_s': ['פלט לא JSON'], 'bad_a': True, 'q': [], 'bad_q': {}})
                stats['bad'] += 1
            continue
        ctxp = ctxj[meta['dafKey']]
        idx = idxs.setdefault(meta['dafKey'], norm_idx(ctxp['lines']))
        for i in meta['ids']:
            rec = work['recs'][i]
            g = got.get(i)
            if not isinstance(g, dict):
                rec.update({'bad_s': ['חסר בפלט'], 'bad_a': True, 'q': [], 'bad_q': {}})
                stats['bad'] += 1
                continue
            rec['s'] = str(g.get('s', '')).strip()
            rec['bad_s'] = F.check_line(rec['s'], rec, c)
            rec['a'] = F.resolve_anchor(g.get('a'), ctxp, idx)
            rec['bad_a'] = rec['a'] is None
            qs = g.get('q')
            rec['q'] = [tidy_q(q) for q in qs] if isinstance(qs, list) else []
            rec['q'] = F.cap_questions(rec['q'], rec, c)
            rec['bad_q'] = {str(k): F.check_q(q, rec, c) for k, q in enumerate(rec['q'])}
            stats['bad' if (rec['bad_s'] or rec['bad_a']) else 'ok'] += 1
    variety_pass(work)
    return usage, stats


def has_fail(rec):
    if rec.get('bad_s') or rec.get('bad_a') or rec.get('rv_s') or rec.get('s') is None:
        return True
    return any(v for v in (rec.get('bad_q') or {}).values()) or any((rec.get('rv_q') or {}).values())


def build_review(slug, perek, c, work):
    """בקשות מבקר זול לכל התוספות שעברו שערי קוד בשורה ובעוגן; שאלות שנפסלו בקוד אינן נשלחות."""
    reqs = []
    byd = {}
    for r in work['recs'].values():
        if r.get('s') is None or r.get('bad_s') or r.get('bad_a') or r.get('rv_done'):
            continue
        byd.setdefault(r['dafKey'], []).append(r)
    per = c['maxPerRequest']
    work['rvreqs'] = {}
    for dk, rs in byd.items():
        rs.sort(key=lambda x: x['n'])
        for gi in range(0, len(rs), per):
            g = rs[gi:gi + per]
            blocks = []
            for r in g:
                qs = '\n'.join('  שאלה %d: %s | תשובה: %s' % (i + 1, q['q'], q['a']) for i, q in enumerate(r['q'])
                               if not (r.get('bad_q') or {}).get(str(i))) or '  (אין שאלות)'
                blocks.append('### מזהה: %s\nדיבור המתחיל: %s\nפנים התוספות:\n%s\nשורת מסקנה: %s\nשאלות:\n%s'
                              % (r['rid'], r['dh'], r['text'], r['s'], qs))
            cid = 'rv-%s-p%d-%s-%d' % (slug, perek, g[0]['daf'], gi // per)
            reqs.append(mk_req(cid, c['engines']['review'], F.REVIEW_SYS, '\n\n'.join(blocks), c['maxTokens']['review']))
            work['rvreqs'][cid] = [r['rid'] for r in g]
    return reqs


def ingest_review(slug, perek, c, work, results):
    usage = {}
    for cid, res in results.items():
        ids = work.get('rvreqs', {}).get(cid)
        if ids is None:
            continue
        if not res.get('ok'):
            for i in ids:     # כשל בביקורת אינו אישור
                work['recs'][i]['rv_s'] = 'ביקורת נכשלה: ' + str(res.get('err'))
                work['recs'][i]['rv_done'] = True
            continue
        add_usage(usage, res)
        try:
            got = F.parse_json(res['text'])
        except Exception:
            for i in ids:
                work['recs'][i]['rv_s'] = 'פלט ביקורת לא JSON'
                work['recs'][i]['rv_done'] = True
            continue
        for i in ids:
            rec = work['recs'][i]
            rec['rv_s'], rec['rv_q'], rec['rv_done'] = '', {}, True
            g = got.get(i)
            if isinstance(g, dict):
                rec['rv_s'] = str(g.get('s') or '')
                qs = g.get('q') or []
                if isinstance(qs, list):
                    for k, why in enumerate(qs):
                        if why:
                            rec['rv_q'][str(k)] = str(why)
    return usage


def build_rewrite(slug, perek, c, work):
    ctxj = ctx_of(slug)
    sysT = F.system_prompt()
    byd = {}
    for r in work['recs'].values():
        if r.get('tries', 1) >= 2 or not has_fail(r):
            continue
        byd.setdefault(r['dafKey'], []).append(r)
    reqs = []
    work['rwreqs'] = {}
    per = max(1, c['maxPerRequest'] // 2)
    for dk, rs in byd.items():
        rs.sort(key=lambda x: x['n'])
        for gi in range(0, len(rs), per):
            g = rs[gi:gi + per]
            notes = []
            for r in g:
                why = []
                if r.get('bad_s'):
                    why.append('שורה: ' + ', '.join(r['bad_s']))
                if r.get('rv_s'):
                    why.append('שורה (מבקר): ' + r['rv_s'])
                if r.get('bad_a'):
                    why.append('עוגן: הקטע לא נמצא בשורות הלאוקמי')
                for k, v in (r.get('bad_q') or {}).items():
                    if v:
                        why.append('שאלה %d: %s' % (int(k) + 1, ', '.join(v)))
                for k, v in (r.get('rv_q') or {}).items():
                    why.append('שאלה %d (מבקר): %s' % (int(k) + 1, v))
                prev = {'s': r.get('s'), 'q': r.get('q')}
                notes.append('מזהה %s - נפסל: %s\nהגרסה הקודמת: %s' % (r['rid'], '; '.join(why) or 'כללי', json.dumps(prev, ensure_ascii=False)))
            um = F.page_user_msg(slug, perek, dk, {'masechet': masechet_name(slug)}, g, ctxj[dk], F.REWRITE_NOTE + '\n\n' + '\n\n'.join(notes))
            cid = 'rw-%s-p%d-%s-%d' % (slug, perek, g[0]['daf'], gi // per)
            reqs.append(mk_req(cid, c['engines']['rewrite'], sysT, um, c['maxTokens']['perTos'] * len(g) + 800))
            work['rwreqs'][cid] = {'ids': [r['rid'] for r in g], 'dafKey': dk}
    return reqs


def ingest_rewrite(slug, perek, c, work, results):
    ctxj = ctx_of(slug)
    usage = {}
    for cid, res in results.items():
        meta = work.get('rwreqs', {}).get(cid)
        if not meta:
            continue
        for i in meta['ids']:
            work['recs'][i]['tries'] = 2
            work['recs'][i]['rv_done'] = False
        if not res.get('ok'):
            continue
        add_usage(usage, res)
        try:
            got = F.parse_json(res['text'])
        except Exception:
            continue
        ctxp = ctxj[meta['dafKey']]
        idx = norm_idx(ctxp['lines'])
        for i in meta['ids']:
            rec = work['recs'][i]
            g = got.get(i)
            if not isinstance(g, dict):
                continue
            s_failed = bool(rec.get('bad_s') or rec.get('rv_s') or rec.get('s') is None)
            a_failed = bool(rec.get('bad_a'))
            q_failed = any(v for v in (rec.get('bad_q') or {}).values()) or any((rec.get('rv_q') or {}).values())
            if s_failed:
                rec['s'] = str(g.get('s', '')).strip()
                rec['bad_s'] = F.check_line(rec['s'], rec, c)
                rec['rv_s'] = ''
            if a_failed:
                rec['a'] = F.resolve_anchor(g.get('a'), ctxp, idx)
                rec['bad_a'] = rec['a'] is None
            if q_failed:
                qs = g.get('q')
                rec['q'] = F.cap_questions([tidy_q(q) for q in qs] if isinstance(qs, list) else [], rec, c)
                rec['bad_q'] = {str(k): F.check_q(q, rec, c) for k, q in enumerate(rec['q'])}
                rec['rv_q'] = {}
    variety_pass(work)
    return usage


def finalize(work):
    """אחרי כתיבה מחדש וביקורת חוזרת: מה שעדיין נכשל מסומן למנהל ואינו מתפרסם."""
    flagged = []
    for r in work['recs'].values():
        s_bad = bool(r.get('bad_s') or r.get('rv_s') or r.get('bad_a') or r.get('s') is None)
        r['status'] = 'flagged' if s_bad else 'ok'
        keep, drop = [], []
        for k, q in enumerate(r.get('q') or []):
            bq = (r.get('bad_q') or {}).get(str(k))
            rq = (r.get('rv_q') or {}).get(str(k))
            if bq or rq:
                drop.append({'q': q, 'why': bq or [rq]})
            else:
                keep.append(q)
        r['q_keep'], r['q_drop'] = keep, drop
        if s_bad:
            flagged.append({'rid': r['rid'], 'dh': r['dh'], 'daf': r['daf'],
                            'why': list(r.get('bad_s') or []) + ([r['rv_s']] if r.get('rv_s') else []) + (['עוגן'] if r.get('bad_a') else [])})
    return flagged


# ---------------------------------------------------------------- שמירה מפני סחיפה
def drift_check(slug, perek, c, work, st):
    sims = [x['sim'] for x in work['cal'] if 'err' not in x]
    if not sims:
        return
    mean = round(sum(sims) / len(sims), 3)
    hist = st.setdefault('calibration', [])
    prev = [h['mean'] for h in hist]
    hist.append({'perek': perek, 'mean': mean, 'n': len(sims), 'at': now_iso()})
    if prev:
        base = sum(prev) / len(prev)
        if mean < base - c['calibration']['dropAlert']:
            raise Halt('סחיפה: התאמת הכיול לנוסח המנהל ירדה ל-%.2f (בסיס %.2f). האצווה נעצרה, ממתינה להכרעת מנהל' % (mean, base))


# ---------------------------------------------------------------- פרסום פרק
def publish(slug, perek, c, work, flagged):
    d = fp(slug)
    count = F.load_count(slug, perek)
    dec = F.decided_map(slug)
    sp, ap = os.path.join(d, 'styles-%d.json' % perek), os.path.join(d, 'anchors-%d.json' % perek)
    styles = jload(sp) or {}
    anchors = jload(ap) or {'_comment': 'עוגן הסימן לכל תוספות: t = קטע טקסט, occ = מספר המופע בדף, rule = 1 המילה בטקסט, 2 מילה מקבילה, 3 סוף שורת הגמרא. העוגן אינו מספר תו.'}
    n_gen = n_dec = 0
    qitems = []
    skipped = []
    for r in count['items']:
        k = str(r['n'])
        key = str(ukey(perek, r['n']))
        if key in dec:
            if dec[key].get('dh') and norm_ctx(dec[key]['dh']) != norm_ctx(r['dh']):
                skipped.append((k, 'הכרעת המנהל על ד"ה אחר (%s) מול הספירה (%s): לא מפורסם עד בדיקה' % (dec[key]['dh'], r['dh'])))
                continue
            if k not in anchors:
                skipped.append((k, 'מוכרע ללא עוגן'))
                continue
            st = styles.get(k, {})
            st.setdefault('dh', r['dh'])
            if not (st.get('a') or st.get('b')):
                st['a'] = dec[key]['text']
            st['dec'] = True
            styles[k] = st
            n_dec += 1
            continue
        w = work['recs'].get(rid(perek, r['n']))
        if not w or w.get('status') != 'ok':
            skipped.append((k, 'לא עבר ביקורת'))
            continue
        styles[k] = {'dh': r['dh'], 'a': w['s'], 'b': w['s'], 'gen': True, 'engine': w.get('engine', ''), 'tries': w.get('tries', 1)}
        a = dict(w['a'])
        a['daf'] = r['dafKey']
        anchors[k] = a
        n_gen += 1
        for qi, q in enumerate(w.get('q_keep') or []):
            qitems.append({'i': 't:%s:%s:%d' % (slug, key, qi), 'kind': 'o', 'tos': int(key), 'p': perek, 'n': r['n'], 'daf': r['dafKey'],
                           'd': r['dh'], 'type': q['t'], 'lvl': {'קל': 1, 'בינוני': 2, 'קשה': 3}.get(q['lvl'], 2), 'q': q['q'], 'a': q['a'],
                           'ref': r['ref'], 'st': 'ממתין'})
    jdump(sp, styles)
    jdump(ap, anchors)
    r = subprocess.run([sys.executable, os.path.join(HERE, 'make_live.py'), slug, str(perek)], capture_output=True, text=True, encoding='utf-8')
    if r.returncode != 0:
        raise Halt('make_live נכשל: ' + (r.stderr or r.stdout)[-400:])
    # שאלות: קובץ אחד למסכת, בתור האישור של המנהל (סטטוס ממתין). מיזוג לפי מזהה: שאלה שהמנהל ערך אינה נדרסת.
    qp = os.path.join(F.ROOT, 'data', 'quiz', 'tos-%s.json' % slug)
    qdoc = jload(qp) or {'slug': slug, 'kind': 'open', 'status': 'ממתין', 'style': 'tosafot-factory', 'items': []}
    have = {x['i']: x for x in qdoc['items']}
    for x in qitems:
        if x['i'] in have and have[x['i']].get('st') != 'ממתין':
            continue
        have[x['i']] = x
    qdoc['items'] = sorted(have.values(), key=lambda x: (x['p'], x['n'], x['i']))
    jdump(qp, qdoc)
    # יומן מלא של הפרק לביקורת (בלי הפנים: הם בקובץ הספירה)
    audit = {'slug': slug, 'perek': perek, 'at': now_iso(), 'generated': n_gen, 'decided': n_dec, 'flagged': flagged, 'skipped': skipped,
             'questions': len(qitems), 'calibration': work.get('cal', []),
             'recs': {k: {x: v for x, v in w.items() if x not in ('text',)} for k, w in work['recs'].items()}}
    jdump(fp(slug, 'factory-%d.json' % perek), audit)
    return {'generated': n_gen, 'decided': n_dec, 'flagged': len(flagged), 'questions': len(qitems), 'skipped': skipped}


def notify(slug, perek, res, c):
    name = masechet_name(slug)
    ch = [x for x in F.chapters(slug) if x['n'] == perek][0]
    base = c['siteBase']
    line = '- %s | %s פרק %d (%s): %d תוספות חדשות באתר, %d שאלות ממתינות, %d סומנו למנהל. קישור: %s/%s.html (בכניסת מנהל: תוס\' ← הערות שוליים; כל שורה מסומנת "לא הוגה").' % (
        datetime.datetime.utcnow().strftime('%d.%m.%Y %H:%M'), name, perek, ch['name'], res['generated'], res['questions'], res['flagged'], base, slug)
    p = os.path.join(F.ROOT, 'docs', 'ענן', 'תוס-הודעות.md')
    os.makedirs(os.path.dirname(p), exist_ok=True)
    if not os.path.exists(p):
        io.open(p, 'w', encoding='utf-8').write('# הודעות בית החרושת לתוספות\n\nכל שורה: פרק שהושלם, עבר ביקורת ופורסם. המנהל מעיין ומתקן בזמן שהעבודה ממשיכה.\n\n')
    with io.open(p, 'a', encoding='utf-8') as f:
        f.write(line + '\n')
    log('הודעה: ' + line)


# ---------------------------------------------------------------- פעימה
BATCH_PHASES = {'writing': 'write', 'reviewing': 'review', 'rewriting': 'rewrite', 'rereviewing': 'rereview'}


def submit_batch(client, slug, perek, phase, reqs, work, ps):
    if not reqs:
        return None
    ok, why = F.budget_ok(F.est_cost(reqs))
    if not ok:
        raise Halt('תקציב: ' + why)
    bid = client.submit(reqs)
    ps['batch'] = bid
    ps['batchPhase'] = phase
    ps['submitted'] = now_iso()
    ps['nreq'] = len(reqs)
    log('נשלח Batch %s (%s) %s פרק %d: %d בקשות' % (bid, phase, slug, perek, len(reqs)))
    return bid


def step_perek(client, slug, perek, st, c):
    """מקדם פרק אחד שלב אחד. מחזיר True אם התקדם (כדי שהפעימה תמשיך לפרק הבא רק כשאין המתנה)."""
    ps = st['perakim'].setdefault(str(perek), {'status': 'pending'})
    work = load_work(slug, perek)
    status = ps['status']
    if status == 'published':
        return False
    if status == 'pending':
        reqs = build_write(slug, perek, c, work)
        if not reqs:
            ps['status'] = 'ready'
            save_work(slug, perek, work)
            return True
        submit_batch(client, slug, perek, 'write', reqs, work, ps)
        ps['status'] = 'writing'
        save_work(slug, perek, work)
        return True
    if status in BATCH_PHASES:
        proc, cnt = client.status(ps['batch'])
        if proc != 'ended':
            print('%s פרק %d: %s ממתין (Batch %s, %s)' % (slug, perek, status, ps['batch'], proc))
            return False
        results = client.results(ps['batch'])
        phase = ps['batchPhase']
        if phase == 'write':
            usage, stats = ingest_write(slug, perek, c, work, results)
            cost = sum(F.ledger_add(slug, perek, 'write', m, u, u['n']) for m, u in usage.items())
            log('%s פרק %d: כתיבה הסתיימה %s, עלות $%.3f' % (slug, perek, stats, cost))
            drift_check(slug, perek, c, work, st)
            reqs = build_review(slug, perek, c, work)
            nxt = 'reviewing'
        elif phase == 'review':
            usage = ingest_review(slug, perek, c, work, results)
            cost = sum(F.ledger_add(slug, perek, 'review', m, u, u['n']) for m, u in usage.items())
            reqs = build_rewrite(slug, perek, c, work)
            nxt = 'rewriting'
            log('%s פרק %d: ביקורת הסתיימה, עלות $%.3f, לכתיבה מחדש: %d בקשות' % (slug, perek, cost, len(reqs)))
        elif phase == 'rewrite':
            usage = ingest_rewrite(slug, perek, c, work, results)
            cost = sum(F.ledger_add(slug, perek, 'rewrite', m, u, u['n']) for m, u in usage.items())
            reqs = build_review(slug, perek, c, work)
            nxt = 'rereviewing'
            log('%s פרק %d: כתיבה מחדש הסתיימה, עלות $%.3f' % (slug, perek, cost))
        else:   # rereview
            usage = ingest_review(slug, perek, c, work, results)
            cost = sum(F.ledger_add(slug, perek, 'rereview', m, u, u['n']) for m, u in usage.items())
            reqs = []
            nxt = 'ready'
            log('%s פרק %d: ביקורת חוזרת הסתיימה, עלות $%.3f' % (slug, perek, cost))
        ps.pop('batch', None)
        ps['status'] = nxt
        if reqs and nxt in ('reviewing', 'rewriting', 'rereviewing'):
            pn = {'reviewing': 'review', 'rewriting': 'rewrite', 'rereviewing': 'rereview'}[nxt]
            submit_batch(client, slug, perek, pn, reqs, work, ps)
        elif nxt in ('reviewing', 'rewriting', 'rereviewing'):
            # אין מה לשלוח בשלב הזה: מדלגים אליו קדימה
            ps['status'] = {'reviewing': 'rewriting', 'rewriting': 'ready', 'rereviewing': 'ready'}[nxt]
            if ps['status'] == 'rewriting':
                rw = build_rewrite(slug, perek, c, work)
                if rw:
                    submit_batch(client, slug, perek, 'rewrite', rw, work, ps)
                else:
                    ps['status'] = 'ready'
        save_work(slug, perek, work)
        return True
    if status == 'ready':
        flagged = finalize(work)
        res = publish(slug, perek, c, work, flagged)
        ps['status'] = 'published'
        ps['published'] = now_iso()
        ps['result'] = {k: v for k, v in res.items() if k != 'skipped'}
        save_work(slug, perek, work)
        notify(slug, perek, res, c)
        open(fp(FDIR, '.published-flag'), 'w').write(now_iso())
        return True
    return False


def tick():
    c = cfg()
    if os.path.exists(fp(FDIR, 'עצור.flag')):
        log('קובץ "עצור" קיים: הפעימה מדלגת.')
        return 0
    client = F.get_client()
    st_all = {}
    progressed = False
    summary = []
    for slug in c['queue']:
        st = state(slug)
        st_all[slug] = st
        if st.get('halt'):
            log('%s: עצור (%s)' % (slug, st['halt']))
            summary.append('%s: עצור - %s' % (slug, st['halt']))
            break      # הסדר בתור: לא ממשיכים למסכת הבאה מעל מסכת עצורה
        pers = counted_perakim(slug)
        if not pers:
            summary.append('%s: אין ספירה (שלב ההכנה טרם רץ)' % slug)
            break
        todo = [p for p in pers if st['perakim'].get(str(p), {}).get('status') != 'published']
        if not todo:
            st['done'] = now_iso()
            save_state(slug, st)
            summary.append('%s: הושלמה' % slug)
            continue
        if client is None:
            if not st.get('blocked'):
                log('%s: חסר מפתח ANTHROPIC_API_KEY. הצנרת מוכנה וממתינה.' % slug)
            st['blocked'] = 'חסר מפתח ANTHROPIC_API_KEY (Secret בריפו)'
            save_state(slug, st)
            summary.append('%s: ממתין למפתח' % slug)
            break
        st.pop('blocked', None)
        # פרק אחד פעיל בכל רגע (התקדמות בסדר הפרקים), כדי שהפרסום יהיה פרק אחר פרק
        p = todo[0]
        try:
            progressed |= step_perek(client, slug, p, st, c)
            summary.append('%s פרק %d: %s' % (slug, p, st['perakim'][str(p)]['status']))
        except Halt as e:
            st['halt'] = str(e)
            log('עצירה: %s %s' % (slug, e))
            summary.append('%s: עצור - %s' % (slug, e))
        save_state(slug, st)
        break
    beat = jload(fp(FDIR, 'דופק.json')) or {'ticks': 0, 'stalls': 0}
    beat['ticks'] += 1
    beat['last'] = now_iso()
    beat['summary'] = summary
    beat['spent'] = F.ledger()['total']
    beat['left'] = round(F.budget_left(), 2)
    beat['stalls'] = 0 if progressed else beat.get('stalls', 0) + 1
    jdump(fp(FDIR, 'דופק.json'), beat)
    # נעילת משימה לפי כלל הנעילה של הריפו (.locks): מתחדשת בכל פעימה
    lk = os.path.join(F.ROOT, '.locks', 'tosafot-factory.lock')
    os.makedirs(os.path.dirname(lk), exist_ok=True)
    io.open(lk, 'w', encoding='utf-8').write('ענן: tosafot-factory, %s\n' % now_iso())
    print('סיכום פעימה:', summary)
    return 0


def status_cmd():
    c = cfg()
    L = F.ledger()
    print('תקציב: הוצאה $%.2f, יתרה מוערכת $%.2f (רצפה $%d, פג תוקף %s)' % (L['total'], F.budget_left(), c['budget']['floor'], c['budget']['expires']))
    for slug in c['queue']:
        st = state(slug)
        pers = counted_perakim(slug)
        print('%s: פרקים בספירה %s' % (slug, pers), '| עצור:', st.get('halt'), '| חסום:', st.get('blocked'))
        for p, ps in sorted(st['perakim'].items(), key=lambda x: int(x[0])):
            print('   פרק', p, ps.get('status'), ps.get('result', ''))


def estimate_cmd(slug):
    c = cfg()
    tos = 0
    hard = 0
    chars = 0
    for p in counted_perakim(slug):
        dec = F.decided_map(slug)
        for r in F.load_count(slug, p)['items']:
            if str(ukey(p, r['n'])) in dec:
                continue
            tos += 1
            chars += len(r['text'])
            hard += 1 if F.is_hard(r, c) else 0
    sysn = len(F.system_prompt()) // 2
    pages = max(1, tos // 3)
    per_page_ctx = 1500   # שורות לאוקמי וגמרא לעמוד, בטוקנים (מדוד: כ-1,100 עד 1,800)
    in_tok = tos * (chars // max(1, tos)) // 2 + pages * per_page_ctx
    out_tok = tos * c['maxTokens']['expectOut']
    pw, ph, pr = c['engines']['write'], c['engines']['hard'], c['engines']['review']
    cw = F.price(pw, {'in': in_tok, 'out': out_tok, 'cr': pages * sysn})
    ch = F.price(ph, {'in': hard * 1800, 'out': hard * c['maxTokens']['expectOut'], 'cr': hard * sysn})
    cr = F.price(pr, {'in': in_tok * 0.5 + tos * 150, 'out': tos * 60})
    rewrite = 0.12 * F.price(ph, {'in': tos * 2500 * 0.12, 'out': tos * 400 * 0.12}) / 0.12 if tos else 0
    print('%s: %d תוספות (קשים: %d) | כתיבה $%.2f | קשים $%.2f | מבקר $%.2f | כתיבה מחדש (כ-12%%) $%.2f | סך $%.2f'
          % (slug, tos, hard, cw, ch, cr, rewrite, cw + ch + cr + rewrite))
    return cw + ch + cr + rewrite


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['tick', 'status', 'estimate', 'reset-halt'])
    ap.add_argument('slug', nargs='?')
    a = ap.parse_args()
    if a.cmd == 'tick':
        sys.exit(tick())
    if a.cmd == 'status':
        status_cmd()
    if a.cmd == 'estimate':
        for s in ([a.slug] if a.slug else cfg()['queue']):
            estimate_cmd(s)
    if a.cmd == 'reset-halt':
        st = state(a.slug)
        st.pop('halt', None)
        save_state(a.slug, st)
        print('הוסר העצור של', a.slug)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
