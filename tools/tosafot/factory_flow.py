# -*- coding: utf-8 -*-
"""factory_flow.py - מכונת המצבים של בית החרושת לתוספות (ראו factory.py לתיאור). כאן: בקשות, קליטה, פרסום ופעימה."""
import os, sys, re, json, io, time, random, hashlib, datetime, subprocess, argparse
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import factory as F
import gates as G   # 24.10.2026: השכבות עצמן (קליטה, ביקורת, כתיבה מחדש, סיום) במקור יחיד, tosafot/handoff/kit/gates.py
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
    """בקשה אחת ל-Batch. החשיבה לפי תיעוד המודלים (13.10.2026): סונט 5.5 אינו מקבל thinking disabled (400), ולכן between_tools
    (חשיבה רק בין כלים: בלי כלים, אין חשיבה) בדרגת מאמץ low; הייקו 5.5: disabled מותר עד דרגה high; פייבל 5.1: החשיבה תמיד דולקת,
    מכוונים בדרגת מאמץ (medium), ומרחיבים את max_tokens כי החשיבה נספרת בו. אין temperature ואין tool_choice (נדחים ב-400)."""
    p = {'model': model, 'max_tokens': max_tokens, 'system': F.sys_blocks(system_text), 'messages': [{'role': 'user', 'content': user}]}
    if 'sonnet' in model:
        p['thinking'] = {'type': 'between_tools'}
        p['output_config'] = {'effort': 'low'}
    elif 'haiku' in model:
        p['thinking'] = {'type': 'disabled'}
        p['output_config'] = {'effort': 'low'}
    elif 'fable' in model:
        p['output_config'] = {'effort': 'medium'}
        p['max_tokens'] = max_tokens + 6000
    return {'custom_id': cid, 'params': p}


def make_rec(slug, perek, r, dafKey, daf):
    return {'rid': rid(perek, r['n']), 'key': ukey(perek, r['n']), 'n': r['n'], 'perek': perek, 'hn': r['hn'], 'dh': r['dh'],
            'daf': daf, 'dafKey': dafKey, 'line': r['line'], 'ref': r['ref'], 'url': r.get('url', ''), 'text': r['text'], 'tries': 1}


def ctx_page(ctxj, dafKey, daf, slug):
    if dafKey in ctxj:
        return ctxj[dafKey]
    src = jload(os.path.join(F.ROOT, 'data', 'sources', slug + '.json'), {}) or {}
    g = ((src.get('pages') or {}).get(daf) or {}).get('gemara') or []
    return {'daf': daf, 'gemara': g, 'lines': [], 'missing': True}


def counted_perakim(slug):
    if not jload(fp(slug, 'chapters.json')):
        return []
    return [ch['n'] for ch in F.chapters(slug) if os.path.exists(fp(slug, 'count-%d.json' % ch['n']))]


# ---------------------------------------------------------------- בקשות
def build_write(slug, perek, c, work):
    ctxj = ctx_of(slug)
    meta = {'masechet': masechet_name(slug)}
    sysT = F.system_prompt()
    reqs = []
    lim = int(os.environ.get('FACTORY_PILOT_PAGES', '0') or 0)     # ניסוי: מספר עמודים מוגבל
    for pi, (dafKey, daf, recs) in enumerate(F.pages_of(slug, perek)):
        if lim and pi >= lim:
            break
        # עמוד שאינו בקובץ הלאוקמי גירסא (context-missing.json): השורה נכתבת בכל זאת, ללא שורות לאוקמי; הסימן יונח לפי
        # השכנים (factory_place.py), בסוף השורה שלפני כן. אין עצירה ואין השמטה.
        ctxp = ctx_page(ctxj, dafKey, daf, slug)
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
    for sl in F.queue():
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


tidy_q = G.tidy_q
add_usage = G.add_usage
variety_pass = G.variety_pass
has_fail = G.has_fail
finalize = G.finalize_core     # אחרי כתיבה מחדש וביקורת חוזרת: מה שעדיין נכשל מסומן למנהל ואינו מתפרסם


def ingest_write(slug, perek, c, work, results):
    ctxj = ctx_of(slug)
    return G.ingest_write_core(work, results, c, lambda meta: ctx_page(ctxj, meta['dafKey'], meta.get('daf', ''), slug))


def build_review(slug, perek, c, work):
    """בקשות מבקר זול לכל התוספות שעברו שערי קוד בשורה ובעוגן; שאלות שנפסלו בקוד אינן נשלחות."""
    if c.get('reviewerV2'):
        # מבקר חדש (14.10.2026): שלוש דרגות ודוגמאות מהכרעות המנהל. פעיל רק כשהדגל reviewerV2 בהגדרות דלוק.
        import triage_reviewer as TR
        sysf = lambda g: TR.system_with_examples([(r['text'], r['s']) for r in g])
    else:
        sysf = lambda g: F.REVIEW_SYS
    work['rvreqs'] = {}
    reqs = []
    for cid, rsys, user, ids in G.review_groups(work, c, 'rv-%s-p%d' % (slug, perek), sysf, bool(c.get('reviewerV2'))):
        reqs.append(mk_req(cid, c['engines']['review'], rsys, user, c['maxTokens']['review']))
        work['rvreqs'][cid] = ids
    return reqs


def ingest_review(slug, perek, c, work, results):
    return G.ingest_review_core(work, results, c, work.get('rvreqs', {}))


def build_rewrite(slug, perek, c, work):
    ctxj = ctx_of(slug)
    sysT = F.system_prompt()
    reqs = []
    work['rwreqs'] = {}
    for cid, um, ids, dk in G.rewrite_groups(work, c, 'rw-%s-p%d' % (slug, perek), slug, perek, masechet_name(slug),
                                             lambda dk, daf: ctx_page(ctxj, dk, daf, slug)):
        reqs.append(mk_req(cid, c['engines']['rewrite'], sysT, um, c['maxTokens']['perTos'] * len(ids) + 800))
        work['rwreqs'][cid] = {'ids': ids, 'dafKey': dk}
    return reqs


def ingest_rewrite(slug, perek, c, work, results):
    ctxj = ctx_of(slug)
    return G.ingest_rewrite_core(work, results, c, work.get('rwreqs', {}), lambda dk, daf: ctx_page(ctxj, dk, daf, slug))


# ---------------------------------------------------------------- שמירה מפני סחיפה
def drift_check(slug, perek, c, work, st):
    sims = [x['sim'] for x in work['cal'] if 'err' not in x]
    if not sims:
        return
    mean = round(sum(sims) / len(sims), 3)
    hist = st.setdefault('calibration', [])
    prev = [h['mean'] for h in hist]
    hist.append({'perek': perek, 'mean': mean, 'n': len(sims), 'at': now_iso()})
    # 14.10: מדגם של 4 לפרק רועש מדי לעצירה בודדת; עוצרים רק על ירידה מתמשכת (ממוצע שלושת האחרונים מול כל הקודמים), לפחות 6 קודמים
    allm = [h['mean'] for h in hist]
    if len(allm) >= 9:
        recent = sum(allm[-3:]) / 3
        older = allm[:-3]
        base = sum(older) / len(older)
        if recent < base - c['calibration']['dropAlert']:
            raise Halt('סחיפה מתמשכת: ממוצע שלושת הפרקים האחרונים %.2f מול בסיס %.2f. האצווה נעצרה, ממתינה להכרעת מנהל' % (recent, base))
    elif prev and mean < sum(prev) / len(prev) - c['calibration']['dropAlert']:
        log('אזהרת כיול (לא עוצר, מדגם קטן): %s פרק %d ממוצע %.2f' % (slug, perek, mean))


# ---------------------------------------------------------------- פרסום פרק
def publish(slug, perek, c, work, flagged):
    d = fp(slug)
    count = F.load_count(slug, perek)
    dec = F.decided_map(slug)
    sp, ap = os.path.join(d, 'styles-%d.json' % perek), os.path.join(d, 'anchors-%d.json' % perek)
    styles = jload(sp) or {}
    anchors = jload(ap) or {'_comment': 'עוגן הסימן לכל תוספות: t = קטע טקסט, occ = מספר המופע בדף, rule = 1 המילה בטקסט, 2 מילה מקבילה, 3 סוף שורת הגמרא. העוגן אינו מספר תו.'}
    n_gen = n_dec = n_unc = 0
    qitems = []
    skipped = []
    for r in count['items']:
        k = str(r['n'])
        key = str(ukey(perek, r['n']))
        if key in dec:
            if dec[key].get('dh') and norm_ctx(dec[key]['dh']) != norm_ctx(r['dh']):
                skipped.append((k, 'הכרעת המנהל על ד"ה אחר (%s) מול הספירה (%s): לא מפורסם עד בדיקה' % (dec[key]['dh'], r['dh'])))
                continue
            if k not in anchors:      # אין עוגן: מונח לפי השכנים (factory_place.py)
                anchors[k] = {'daf': r['dafKey'], 't': '', 'occ': 1, 'rule': 3, 'why': 'ממתין להנחה לפי סדר המספרים'}
            st = styles.get(k, {})
            st.setdefault('dh', r['dh'])
            if not (st.get('a') or st.get('b')):
                st['a'] = dec[key]['text']
            st['dec'] = True
            styles[k] = st
            n_dec += 1
            continue
        w = work['recs'].get(rid(perek, r['n']))
        if w and w.get('status') != 'ok' and (w.get('s') or '').strip():
            # 14.10.2026, הוראת בעל הפרויקט: אין תוספות חסר. מה שנפסל מתפרסם בסימון "טרם נבדק" (unc) וממתין להכרעתו.
            if k in styles and not styles[k].get('gen_ok'):
                if styles[k].get('unc') or styles[k].get('dec'):
                    continue      # כבר מוצג (ריצה קודמת או הכרעת מנהל)
            line = re.sub(r'\s*;\s*$', '.', (w['s'] or '').strip())
            line = re.sub(r'\s*;\s*', '. ', line)
            styles[k] = {'dh': r['dh'], 'a': line, 'b': line, 'gen': True, 'engine': w.get('engine', ''), 'unc': True}
            a = dict(w['a']) if w.get('a') else {'t': '', 'occ': 1, 'rule': 3, 'why': 'ממתין להנחה לפי סדר המספרים'}
            a['daf'] = r['dafKey']
            anchors[k] = a
            n_unc += 1
            continue
        if not w or w.get('status') != 'ok':
            skipped.append((k, 'לא עבר ביקורת'))
            continue
        styles[k] = {'dh': r['dh'], 'a': w['s'], 'b': w['s'], 'gen': True, 'engine': w.get('engine', ''), 'tries': w.get('tries', 1)}
        a = dict(w['a']) if w.get('a') else {'t': '', 'occ': 1, 'rule': 3, 'why': 'ממתין להנחה לפי סדר המספרים'}
        a['daf'] = r['dafKey']
        anchors[k] = a
        n_gen += 1
        for qi, q in enumerate(w.get('q_keep') or []):
            qitems.append({'i': 't:%s:%s:%d' % (slug, key, qi), 'kind': 'o', 'tos': int(key), 'p': perek, 'n': r['n'], 'daf': r['dafKey'],
                           'd': r['dh'], 'type': q['t'], 'lvl': {'קל': 1, 'בינוני': 2, 'קשה': 3}.get(q['lvl'], 2), 'q': q['q'], 'a': q['a'],
                           'ref': r['ref'], 'st': 'מפורסם', 'ds': r.get('dhs') or r['dh'], 'rv': 0})
    jdump(sp, styles)
    jdump(ap, anchors)
    # הנחת כל הסימנים בסדר המספרים והשער (רציפות וסדר): כשל עוצר את הפרסום
    import factory_place
    rep = factory_place.place_masechet(slug)
    if not rep['ok']:
        raise Halt('שער הסדר נכשל: ' + '; '.join(rep['errors'][:5]))
    anchors = jload(ap) or anchors
    r = subprocess.run([sys.executable, os.path.join(HERE, 'make_live.py'), slug, str(perek)], capture_output=True, text=True, encoding='utf-8')
    if r.returncode != 0:
        raise Halt('make_live נכשל: ' + (r.stderr or r.stdout)[-400:])
    # שאלות (14.10.2026): קובץ אחד למסכת. שאלה שעברה את השערים והמבקר מתפרסמת מיד (סטטוס מפורסם), וההגהה בדיעבד:
    # rv=0 מסמן למנהל "לא הוגה עדיין". מיזוג לפי מזהה: שאלה שהמנהל ערך, הסתיר או מחק אינה נדרסת.
    qp = os.path.join(F.ROOT, 'data', 'quiz', 'tos-%s.json' % slug)
    qdoc = jload(qp) or {'slug': slug, 'kind': 'open', 'status': 'מפורסם', 'style': 'tosafot-factory', 'items': []}
    have = {x['i']: x for x in qdoc['items']}
    for x in qitems:
        if x['i'] in have:
            continue      # קיימת: אינה נדרסת (הגהת המנהל, הסתרה או עריכה)
        have[x['i']] = x
    qdoc['items'] = sorted(have.values(), key=lambda x: (x['p'], x['n'], x['i']))
    jdump(qp, qdoc)
    # יומן מלא של הפרק לביקורת (בלי הפנים: הם בקובץ הספירה)
    audit = {'slug': slug, 'perek': perek, 'at': now_iso(), 'generated': n_gen, 'decided': n_dec, 'flagged': flagged, 'skipped': skipped,
             'questions': len(qitems), 'calibration': work.get('cal', []),
             'recs': {k: {x: v for x, v in w.items() if x not in ('text',)} for k, w in work['recs'].items()}}
    jdump(fp(slug, 'factory-%d.json' % perek), audit)
    return {'generated': n_gen, 'decided': n_dec, 'unchecked': n_unc, 'flagged': len(flagged), 'questions': len(qitems), 'skipped': skipped}


def notify(slug, perek, res, c):
    name = masechet_name(slug)
    ch = [x for x in F.chapters(slug) if x['n'] == perek][0]
    base = c['siteBase']
    line = '- %s | %s פרק %d (%s): %d תוספות חדשות באתר, %d שאלות פורסמו, %d סומנו למנהל. קישור: %s/%s.html (בכניסת מנהל: תוס\' ← הערות שוליים; כל שורה מסומנת "לא הוגה").' % (
        datetime.datetime.utcnow().strftime('%d.%m.%Y %H:%M'), name, perek, ch['name'], res['generated'], res['questions'], res['flagged'], base, slug)
    p = os.path.join(F.ROOT, 'docs', 'ענן', 'תוס-הודעות.md')
    os.makedirs(os.path.dirname(p), exist_ok=True)
    if not os.path.exists(p):
        io.open(p, 'w', encoding='utf-8').write('# הודעות בית החרושת לתוספות\n\nכל שורה: פרק שהושלם, עבר ביקורת ופורסם. המנהל מעיין ומתקן בזמן שהעבודה ממשיכה.\n\n')
    with io.open(p, 'a', encoding='utf-8') as f:
        f.write(line + '\n')
    sp = os.path.join(F.ROOT, 'docs', 'ענן', 'STATUS.md')
    if not os.path.exists(sp):
        io.open(sp, 'w', encoding='utf-8').write('# מצב משימות הענן\n\n## בית החרושת לתוספות\n\n')
    with io.open(sp, 'a', encoding='utf-8') as f:
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
        if slug in ('sukkah', 'berakhot') or ps.get('unc_done'):
            return False
        # 14.10.2026: פרק שפורסם לפני שהפסולות נכנסו לפרסום (בסימון טרם נבדק): משלימים פעם אחת
        res = publish(slug, perek, c, work, finalize(work))
        ps['unc_done'] = True
        ps['result'] = {k: v for k, v in res.items() if k != 'skipped'}
        save_work(slug, perek, work)
        log('%s פרק %d: הושלם פרסום %d תוספות בסימון טרם נבדק' % (slug, perek, res.get('unchecked', 0)))
        return True
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
            c_rv = c
            if ps.get('retry'):
                import copy
                c_rv = copy.deepcopy(c)
                c_rv['engines']['review'] = ps['retry']['reviewer']
            reqs = build_review(slug, perek, c_rv, work)
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
        ps.pop('retry', None)
        ps['result'] = {k: v for k, v in res.items() if k != 'skipped'}
        save_work(slug, perek, work)
        notify(slug, perek, res, c)
        open(fp(FDIR, '.published-flag'), 'w').write(now_iso())
        return True
    return False


def apply_retry(client, slug, st, c):
    """14.10: סבב נוסף לתוספות שנפסלו (retry.json). dry = רק אומדן עלות, בלי שליחה."""
    import copy
    rt = jload(fp(FDIR, 'retry.json'))
    if not rt:
        return
    done = rt.setdefault('done', [])
    changed = False
    for item in rt.get('items', []):
        sl, p = item[0], int(item[1])
        key = '%s:%d' % (sl, p)
        if sl != slug or key in done:
            continue
        ps = st['perakim'].get(str(p))
        if not ps or ps.get('status') != 'published':
            continue
        c2 = copy.deepcopy(c)
        if rt.get('rewriter'):
            c2['engines']['rewrite'] = rt['rewriter']
        work = load_work(slug, p)
        n = 0
        for r in work['recs'].values():
            if r.get('status') == 'flagged':
                r['tries'] = 1
                n += 1
        reqs = build_rewrite(slug, p, c2, work)
        est = F.est_cost(reqs) if reqs else 0
        if rt.get('dry'):
            log('אומדן סבב נוסף %s פרק %d: %d תוספות פסולות, %d בקשות, כ-$%.2f' % (slug, p, n, len(reqs), est))
            done.append(key)
            changed = True
            continue
        if not reqs:
            done.append(key)
            changed = True
            continue
        submit_batch(client, slug, p, 'rewrite', reqs, work, ps)
        ps['status'] = 'rewriting'
        ps['retry'] = {'reviewer': rt.get('reviewer') or c['engines']['review']}
        save_work(slug, p, work)
        log('סבב נוסף %s פרק %d: %d תוספות, מנוע %s' % (slug, p, n, c2['engines']['rewrite']))
        done.append(key)
        changed = True
    if changed:
        jdump(fp(FDIR, 'retry.json'), rt)


def tick():
    c = cfg()
    if os.path.exists(fp(FDIR, 'עצור.flag')):
        log('קובץ "עצור" קיים: הפעימה מדלגת.')
        return 0
    client = F.get_client()
    # 14.10.2026: השלמת פרסום "טרם נבדק" לפרקים שפורסמו קודם. בלי מודל ובלי עלות, ולכן רץ גם כשהקרדיט נגמר.
    for slug0 in F.queue():
        if slug0 in ('sukkah', 'berakhot'):
            continue
        st0 = state(slug0)
        ch0 = False
        for pk0, ps0 in st0.get('perakim', {}).items():
            if ps0.get('status') == 'published' and not ps0.get('unc_done'):
                try:
                    step_perek(client, slug0, int(pk0), st0, c)
                    ch0 = True
                except Exception as e:
                    log('השלמת טרם-נבדק נכשלה %s פרק %s: %s' % (slug0, pk0, e))
        if ch0:
            save_state(slug0, st0)
    st_all = {}
    progressed = False
    summary = []
    all_done = True
    for slug in F.queue():
        st = state(slug)
        st_all[slug] = st
        if st.get('halt'):
            log('%s: עצור (%s)' % (slug, st['halt']))
            summary.append('%s: עצור - %s' % (slug, st['halt']))
            break      # הסדר בתור: לא ממשיכים למסכת הבאה מעל מסכת עצורה
        pers = counted_perakim(slug)
        if not pers:
            # מסכת חדשה בתור: מבקשים הכנה (הצעד האחרון של ה-workflow מפעיל את tosafot-prep). קוד בלבד, בלי עלות.
            open(fp(FDIR, '.need-prep'), 'w').write(slug)
            summary.append('%s: ממתין להכנה (ספירה והקשר)' % slug)
            break
        apply_retry(client, slug, st, c)
        todo = [p for p in pers if st['perakim'].get(str(p), {}).get('status') != 'published']
        if todo:
            all_done = False
        if not todo:
            if not st.get('done'):
                st['done'] = now_iso()
                write_report(slug)
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
        # 14.10: כל הפרקים הלא-מפורסמים מתקדמים במקביל (Batch נפרד לכל פרק); הדחיפות: לא מחכים לפרק הקודם
        halted = False
        for p in todo:
            try:
                for _ in range(3):
                    progressed |= step_perek(client, slug, p, st, c)
                    if st['perakim'][str(p)]['status'] not in ('ready',):
                        break
                summary.append('%s פרק %d: %s' % (slug, p, st['perakim'][str(p)]['status']))
            except Halt as e:
                st['halt'] = str(e)
                log('עצירה: %s %s' % (slug, e))
                summary.append('%s: עצור - %s' % (slug, e))
                halted = True
                break
        save_state(slug, st)
        if halted:
            break
        if any(v.get('status') in BATCH_PHASES for v in st['perakim'].values()):
            open(fp(FDIR, '.waiting'), 'w').write(now_iso())
    # שומר הדופק: נרשם כשיש התקדמות, כשהסיכום השתנה, או אחת לשעה (פעימות שקטות אינן מייצרות קומיט)
    bp = fp(FDIR, 'דופק.json')
    beat = jload(bp) or {'ticks': 0, 'stalls': 0, 'last': '', 'summary': []}
    if all_done and F.queue() and not any('עצור' in x or 'מפתח' in x or 'הכנה' in x for x in summary):
        if not beat.get('queueDone'):
            beat['queueDone'] = now_iso()
            sp = os.path.join(F.ROOT, 'docs', 'ענן', 'STATUS.md')
            os.makedirs(os.path.dirname(sp), exist_ok=True)
            with io.open(sp, 'a', encoding='utf-8') as f:
                f.write('- %s | בית החרושת לתוספות סיים את כל המסכתות שבתור (%s). להמשך: להוסיף שורה חדשה ל-tosafot/תור-מסכתות.md.\n'
                        % (datetime.datetime.utcnow().strftime('%d.%m.%Y %H:%M'), ', '.join(F.SLUG2HE[x] for x in F.queue())))
            log('התור הסתיים: ממתין להוראה על סדר המסכתות הבאות')
            progressed = True
    else:
        beat.pop('queueDone', None)
    beat['ticks'] = beat.get('ticks', 0) + 1
    beat['stalls'] = 0 if progressed else beat.get('stalls', 0) + 1
    old_age = 10 ** 9
    try:
        old_age = (datetime.datetime.utcnow() - datetime.datetime.strptime(beat.get('last', ''), '%Y-%m-%dT%H:%M:%SZ')).total_seconds()
    except Exception:
        pass
    if progressed or beat.get('summary') != summary or old_age > 3600:
        beat['summary'] = summary
        beat['last'] = now_iso()
        beat['spent'] = F.ledger()['total']
        beat['left'] = round(F.budget_left(), 2)
        jdump(bp, beat)
        # נעילת משימה לפי כלל הנעילה של הריפו (.locks), כשיש עבודה פעילה
        lk = os.path.join(F.ROOT, '.locks', 'tosafot-factory.lock')
        active = any(('ממתין' not in x) and ('הושלמה' not in x) and ('עצור' not in x) for x in summary)
        if active:
            os.makedirs(os.path.dirname(lk), exist_ok=True)
            io.open(lk, 'w', encoding='utf-8').write('ענן: tosafot-factory, %s\n' % now_iso())
        elif os.path.exists(lk):
            os.remove(lk)
    if beat['stalls'] >= 12:
        log('אזהרה: שתים עשרה פעימות רצופות בלי התקדמות. %s' % summary)
    print('סיכום פעימה:', summary)
    return 0


def write_report(slug):
    """דוח סיום מסכת (סעיף ז.ג של המנה): מספר התוספות, פסילות, שאלות, עלות, שמירה מפני סחיפה, ומה פתוח.
    נכתב ל-docs/ענן/דוח-בית-החרושת-<מסכת>.md; מהעותק הזה נכתב הדוח בדרייב."""
    st = state(slug)
    name = masechet_name(slug)
    L = F.ledger()
    toks = L['tokens'].get(slug, {})
    rows = []
    tot = {'gen': 0, 'dec': 0, 'flag': 0, 'q': 0}
    flagged_all, dropped_q = [], []
    for p in counted_perakim(slug):
        a = jload(fp(slug, 'factory-%d.json' % p))
        if not a:
            continue
        tot['gen'] += a['generated']
        tot['dec'] += a['decided']
        tot['flag'] += len(a['flagged'])
        tot['q'] += a['questions']
        flagged_all += [dict(x, perek=p) for x in a['flagged']]
        for r in a['recs'].values():
            for d in r.get('q_drop', []):
                dropped_q.append((p, r['rid'], r['dh'], d['why']))
        rows.append('- פרק %d: נכתבו %d, מוכרעים (נשארו כנוסח המנהל) %d, סומנו למנהל %d, שאלות %d' % (p, a['generated'], a['decided'], len(a['flagged']), a['questions']))
    cal = st.get('calibration') or []
    n_tos = tot['gen'] + tot['dec'] + tot['flag']
    cost = L['bySlug'].get(slug, 0)
    lines = ["# דוח - בית החרושת לתוס', %s (%s)" % (name, datetime.date.today().strftime('%d.%m.%Y')), '',
             '## מספרים', '',
             '- תוספות במסכת: %d (נכתבו בבית החרושת %d, כנוסח המנהל %d, סומנו למנהל ולא פורסמו %d)' % (n_tos, tot['gen'], tot['dec'], tot['flag']),
             '- שאלות תוכן שנכנסו לתור האישור: %d. שאלות שנפסלו ולא פורסמו: %d' % (tot['q'], len(dropped_q)), ''] + rows + ['',
             '## עלות', '',
             '- סך הוצאה על המסכת: $%.2f. עלות ממוצעת לתוספות: $%.4f' % (cost, cost / max(1, tot['gen'])),
             '- טוקנים: קלט %d, כתיבת מטמון %d, קריאת מטמון %d, פלט %d' % (toks.get('in', 0), toks.get('cw', 0), toks.get('cr', 0), toks.get('out', 0)),
             '- יתרת קרדיט מוערכת: $%.2f' % F.budget_left(), '',
             '## שמירה מפני סחיפה (כיול נסתר על תוספות שהמנהל הכריע בהן)', '']
    for c in cal:
        lines.append('- פרק %s: התאמה ממוצעת %.2f (%d תוספות)' % (c['perek'], c['mean'], c['n']))
    if not cal:
        lines.append('- לא נמדד')
    lines += ['', '## מה נפסל ולמה', '']
    for x in flagged_all[:80]:
        lines.append('- פרק %d, %s (%s): %s' % (x['perek'], x['rid'], x['dh'], '; '.join(str(y) for y in x['why'])))
    if not flagged_all:
        lines.append('- כלום')
    lines += ['', '## מה נשאר פתוח', '', '- המנהל מעיין בשורות המסומנות "לא הוגה" ובשאלות שבתור האישור.']
    p = os.path.join(F.ROOT, 'docs', 'ענן', 'דוח-בית-החרושת-%s.md' % slug)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    io.open(p, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
    log('נכתב דוח מסכת ' + p)


def status_cmd():
    c = cfg()
    L = F.ledger()
    print('תקציב: הוצאה $%.2f, יתרה מוערכת $%.2f (רצפה $%d, פג תוקף %s)' % (L['total'], F.budget_left(), c['budget']['floor'], c['budget']['expires']))
    for slug in F.queue():
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
    ap.add_argument('cmd', choices=['tick', 'status', 'estimate', 'reset-halt', 'report'])
    ap.add_argument('slug', nargs='?')
    a = ap.parse_args()
    if a.cmd == 'tick':
        sys.exit(tick())
    if a.cmd == 'status':
        status_cmd()
    if a.cmd == 'estimate':
        for s in ([a.slug] if a.slug else cfg()['queue']):
            estimate_cmd(s)
    if a.cmd == 'report':
        write_report(a.slug)
    if a.cmd == 'reset-halt':
        st = state(a.slug)
        st.pop('halt', None)
        save_state(a.slug, st)
        print('הוסר העצור של', a.slug)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
