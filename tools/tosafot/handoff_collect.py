# -*- coding: utf-8 -*-
"""handoff_collect.py - הקולט של מפעל התוס' בחשבון השני (24.10.2026). קוד בלבד, בלי מודל, ספרייה סטנדרטית בלבד.

החשבון השני כותב (תת-סוכנים במודלים הקבועים) ושומר תוצר לכל יחידה, out-<id>.json, בתיקייה המשותפת בדרייב
"מפעל התוס' - תוצרים / יחידות". ההורדה עצמה נעשית בידי המשימה המתוזמנת "קולט התוס' מהחשבון השני" בחשבון הזה (מחבר הדרייב),
שמניחה את הקבצים ב-tosafot/handoff/inbox/. כל השאר כאן, בקוד, באותה צנרת שכבר קיימת:

  א. בדיקת תוצר: JSON תקין, יחידה מוכרת, כל התוספות קיימים, הד"ה והפנים זהים ליחידה, מודלים לפי הקבוע (או החלופה המותרת).
     תוצר פגום נכנס ל-redo ב-index.json, והחשבון השני חוזר עליו לבד.
  ב. איחוד לקובץ העבודה הקיים (tosafot/factory/work-<מסכת>-<פרק>.json), כיול (דמיון לנוסח המנהל) ושמירה מפני סחיפה.
  ג. פרק שכל יחידותיו הגיעו: finalize ← publish ← notify, ו-state = published, בדיוק כמו בבית החרושת. "לעיון המנהל" מתפרסם
     בסימון "טרם נבדק" (גלוי למנהל בלבד), כמו בסוכה ובברכות. יחידת השלמה (fill) מפרסמת רק את התוספות שבה.
  ד. דואר יוצא (outbox.json): רק סיום מסכת שלמה והתראת סחיפה. לוח המצב (board.md) לשורת התוס' בלוח בתי החרושת.

    python3 tools/tosafot/handoff_collect.py need                          # מה המשימה צריכה: מזהה התיקייה, ומה כבר נקלט
    python3 tools/tosafot/handoff_collect.py connect <folder> <units> <מייל> # מתוך מייל החיבור
    python3 tools/tosafot/handoff_collect.py waiting                       # מייל החיבור עוד לא הגיע: נרשם "ממתין לחיבור"
    python3 tools/tosafot/handoff_collect.py save <קובץ-תוצאת-הורדה> [id=<מזהה>] [modified=<זמן>]   # הורדה מהדרייב ל-inbox/
    python3 tools/tosafot/handoff_collect.py collect                       # קליטה, פרסום, דואר ולוח
    python3 tools/tosafot/handoff_collect.py sent <מזהה>                   # סימון מייל שנשלח
"""
import os, sys, re, json, io, glob, base64, datetime, copy
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import factory as F
import factory_flow as FF
import gates as G
from factory import fp, jload, jdump, ukey, rid, now_iso

HO = fp('handoff')
INBOX = os.path.join(HO, 'inbox')
ALLOWED = {'write': {'sonnet', 'fable', 'opus'}, 'prewritten': {'sonnet', 'fable'}, 'rv': {'haiku', 'sonnet'},
           'rewrite': {'fable', 'opus'}, 'rr': {'sonnet'}}
MODEL_ID = {'sonnet': 'claude-sonnet-5-5', 'fable': 'claude-fable-5-1', 'haiku': 'claude-haiku-5-5', 'opus': 'claude-opus-5-5'}
FALLBACK = {'opus', }          # fable -> opus, haiku -> sonnet (הוראות קבועות, ג.3.ה): מותר, נרשם בלוח


def log(msg):
    line = '[%s] %s' % (datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None).strftime('%Y-%m-%d %H:%M:%S'), msg)
    print(line, flush=True)
    with io.open(os.path.join(HO, 'יומן-קולט.log'), 'a', encoding='utf-8') as f:
        f.write(line + '\n')


def index():
    return jload(os.path.join(HO, 'index.json')) or {'version': 1, 'units': [], 'redo': []}


def collected():
    return jload(os.path.join(HO, 'collected.json')) or {'units': {}, 'files': {}}


def outbox():
    return jload(os.path.join(HO, 'outbox.json')) or {'items': []}


def mail(kind, subject, body):
    ob = outbox()
    mid = '%s-%s' % (kind, datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None).strftime('%Y%m%d%H%M%S%f'))
    ob['items'].append({'id': mid, 'at': now_iso(), 'to': 'm7654301@gmail.com', 'subject': "[מפעל התוס'] " + subject, 'body': body, 'sent': False})
    jdump(os.path.join(HO, 'outbox.json'), ob)


# ---------------------------------------------------------------- פקודות התחבורה
def cmd_need():
    ib = jload(os.path.join(HO, 'inbox.json')) or {}
    col = collected()
    print(json.dumps({'connected': bool(ib.get('units')), 'folder': ib.get('folder'), 'units': ib.get('units'), 'account': ib.get('account'),
                      'files': col.get('files', {}), 'mail_unsent': [x for x in outbox()['items'] if not x['sent']]}, ensure_ascii=False, indent=1))


def cmd_connect(folder, units, account):
    jdump(os.path.join(HO, 'inbox.json'), {'folder': folder, 'units': units, 'account': account, 'connected': now_iso(),
                                           'note': 'מתוך מייל החיבור "[מפעל התוס\'] חיבור" מהחשבון השני. התיקייה משותפת עם m7654301@gmail.com בלבד, לא בקישור ציבורי.'})
    log('חובר: תיקייה %s, יחידות %s, חשבון %s' % (folder, units, account))


def cmd_waiting():
    ib = jload(os.path.join(HO, 'inbox.json')) or {}
    if ib.get('units'):
        return
    ib['waiting'] = now_iso()
    jdump(os.path.join(HO, 'inbox.json'), ib)
    write_board('ממתין לחיבור (מייל החיבור מהחשבון השני טרם הגיע)')
    log('ממתין לחיבור')


def cmd_save(path, name=None, file_id=None, modified=None):
    """מפענח תוצאת הורדה מהדרייב: קובץ JSON עם content ב-base64 (כפי שהכלי שומר תוצאה גדולה), או base64 גולמי, או JSON התוצר עצמו."""
    raw = io.open(path, encoding='utf-8', errors='replace').read().strip()
    data = None
    try:
        j = json.loads(raw)
        if isinstance(j, dict) and isinstance(j.get('content'), str):
            data = base64.b64decode(j['content'])
            name = name or j.get('title')
            file_id = file_id or j.get('id')
        elif isinstance(j, list) and j and isinstance(j[0], dict) and 'text' in j[0]:
            inner = json.loads(j[0]['text'])
            data = base64.b64decode(inner['content'])
            name = name or inner.get('title')
            file_id = file_id or inner.get('id')
        elif isinstance(j, dict) and 'recs' in j and 'id' in j:
            data = raw.encode('utf-8')
    except Exception:
        pass
    if data is None:
        data = base64.b64decode(re.sub(r'\s+', '', raw))
    out = json.loads(data.decode('utf-8'))
    uid = out.get('id')
    if not uid or not re.match(r'^[a-z-]+-p\d\d-u\d\d$', uid):
        raise SystemExit('עצירה: אין מזהה יחידה תקין בקובץ %s' % path)
    os.makedirs(INBOX, exist_ok=True)
    dst = os.path.join(INBOX, 'out-%s.json' % uid)
    io.open(dst, 'wb').write(data)
    if file_id or modified:
        col = collected()
        col['files'][name or ('out-%s.json' % uid)] = {'id': file_id, 'modified': modified, 'saved': now_iso(), 'done_at': out.get('done_at')}
        jdump(os.path.join(HO, 'collected.json'), col)
    print('נשמר', dst, out.get('done_at'))


def cmd_sent(mid):
    ob = outbox()
    for x in ob['items']:
        if x['id'] == mid:
            x['sent'] = now_iso()
    jdump(os.path.join(HO, 'outbox.json'), ob)


# ---------------------------------------------------------------- בדיקת תוצר
def check_out(out, unit):
    bad = []
    if out.get('id') != unit['id']:
        bad.append('מזהה לא תואם')
    real = {k: v for k, v in unit['recs'].items() if not v.get('cal')}
    recs = out.get('recs') or {}
    miss = [k for k in real if k not in recs]
    if miss:
        bad.append('חסרים תוספות: %s' % ', '.join(miss[:8]))
    extra = [k for k in recs if k not in real]
    if extra:
        bad.append('תוספות שאינם ביחידה: %s' % ', '.join(extra[:8]))
    for k, r in recs.items():
        u = real.get(k)
        if not u:
            continue
        if r.get('dh') is not None and r.get('dh') != u['dh']:
            bad.append('ד"ה שונה ב-%s' % k)
        if r.get('text') is not None and r.get('text') != u['text']:
            bad.append('פנים שונה ב-%s' % k)
        if r.get('status') not in ('ok', 'לעיון המנהל'):
            bad.append('סטטוס לא מוכר ב-%s' % k)
        if r.get('status') == 'ok' and not (r.get('s') or '').strip():
            bad.append('שורה ריקה ב-%s' % k)
    eng = out.get('engines') or {}
    for ph, ms in eng.items():
        if ph not in ALLOWED:
            continue
        for m in (ms if isinstance(ms, list) else [ms]):
            if m and G.short_model(m) not in ALLOWED[ph]:
                bad.append('מודל %s בשלב %s אינו לפי הקבוע' % (m, ph))
    if not eng.get('write') and not unit.get('prewritten'):
        bad.append('אין רישום מודל כתיבה')
    return bad


def to_work_rec(unit_rec, rid_, o):
    """רשומת עבודה בפורמט של factory_flow, כך ש-finalize מחזיר בדיוק את מה שהחשבון השני הכריע."""
    keep = list(o.get('q_keep') or [])
    drop = list(o.get('q_drop') or [])
    q = keep + [d.get('q') for d in drop]
    bad_q = {str(len(keep) + i): (d.get('why') if isinstance(d.get('why'), list) else [str(d.get('why'))]) for i, d in enumerate(drop)}
    flagged = o.get('status') != 'ok'
    rec = {'rid': rid_, 'key': unit_rec['key'], 'n': unit_rec['n'], 'perek': unit_rec['perek'], 'hn': unit_rec['hn'], 'dh': unit_rec['dh'],
           'daf': unit_rec['daf'], 'dafKey': unit_rec['dafKey'], 'line': unit_rec['line'], 'ref': unit_rec['ref'], 'url': unit_rec.get('url', ''),
           'text': unit_rec['text'], 'tries': int(o.get('tries') or 1), 'engine': MODEL_ID.get(o.get('engine') or ('fable' if unit_rec.get('hard') else 'sonnet'), str(o.get('engine'))),
           's': (o.get('s') or '').strip() or None, 'a': o.get('a'), 'bad_a': False, 'q': q, 'bad_q': bad_q, 'rv_q': {},
           'bad_s': [str(x) for x in (o.get('why') or ['לעיון המנהל'])] if flagged else [], 'rv_s': '',
           'rv_fix': bool(o.get('rv_fix')), 'handoff': unit_rec.get('unit')}
    if o.get('star'):
        rec['star'] = True
    if flagged and rec['s'] is None:
        rec['s'] = None
    return rec


# ---------------------------------------------------------------- קליטה
def backup_old_work(slug, perek):
    p = FF.work_path(slug, perek)
    w = jload(p)
    if w and not w.get('handoff'):
        b = p.replace('.json', '.api-14.10.json')
        if not os.path.exists(b):
            os.replace(p, b)
            log('קובץ העבודה הישן (API) נשמר בצד: %s' % os.path.basename(b))
        return True
    return False


def cmd_collect():
    c = F.cfg()
    idx = index()
    col = collected()
    units_by = {u['id']: u for u in idx['units']}
    redo = set(idx.get('redo') or [])
    changed_pk = set()
    alerts = []
    files = sorted(glob.glob(os.path.join(INBOX, 'out-*.json')))
    n_new = n_bad = 0
    for p in files:
        uid = os.path.basename(p)[4:-5]
        try:
            out = jload(p)
        except Exception as e:
            log('תוצר שבור %s: %s' % (uid, e))
            if uid in units_by:
                redo.add(uid)
                col['units'][uid] = {'rejected': 'JSON שבור', 'at': now_iso()}
            n_bad += 1
            continue
        prev = col['units'].get(uid) or {}
        if prev.get('done_at') == out.get('done_at') and (prev.get('ok') or prev.get('rejected')):
            continue
        if uid not in units_by:
            log('תוצר ליחידה לא מוכרת: %s' % uid)
            col['units'][uid] = {'rejected': 'יחידה לא מוכרת', 'done_at': out.get('done_at'), 'at': now_iso()}
            continue
        unit = jload(os.path.join(HO, 'units', uid + '.json'))
        bad = check_out(out, unit)
        if bad:
            log('תוצר פגום %s: %s' % (uid, '; '.join(bad)))
            redo.add(uid)
            col['units'][uid] = {'rejected': '; '.join(bad)[:500], 'done_at': out.get('done_at'), 'at': now_iso()}
            n_bad += 1
            continue
        slug, perek = unit['slug'], unit['perek']
        wp = FF.work_path(slug, perek)
        if not units_by[uid].get('fill'):
            backup_old_work(slug, perek)     # פרק חדש: קובץ העבודה של ה-API (14.10) נשמר בצד. השלמה: נכנסת לקובץ הקיים
        work = jload(wp) or {'reqs': {}, 'recs': {}, 'cal': [], 'batches': {}, 'handoff': True, 'units': {}}
        work['handoff'] = True
        work.setdefault('units', {})
        for k, o in out['recs'].items():
            ur = dict(unit['recs'][k], unit=uid)
            work['recs'][k] = to_work_rec(ur, k, o)
        # כיול: דמיון לנוסח המנהל
        sims = []
        for x in out.get('cal') or []:
            src = x.get('src') or (unit['recs'].get(x.get('key')) or {}).get('cal') or {}
            dec = F.decided_map(src.get('slug', '')) if src else {}
            final = (dec.get(str(src.get('key'))) or {}).get('text') if src else None
            if not final:
                continue
            sim = round(G.similarity(x.get('s') or '', final), 3) if not x.get('err') else 0.0
            work['cal'] = [y for y in work.get('cal', []) if not (y.get('key') == x.get('key') and y.get('unit') == uid)]
            work['cal'].append({'key': x.get('key'), 'sim': sim, 'unit': uid, **({'err': x['err']} if x.get('err') else {})})
            if not x.get('err'):
                sims.append(sim)
        work['units'][uid] = {'done_at': out.get('done_at'), 'engines': out.get('engines'), 'flagged': out.get('flagged'), 'at': now_iso()}
        jdump(wp, work)
        fb = [m for ms in (out.get('engines') or {}).values() for m in (ms if isinstance(ms, list) else [ms]) if m and G.short_model(m) in FALLBACK]
        col['units'][uid] = {'ok': True, 'done_at': out.get('done_at'), 'at': now_iso(), 'ntos': out.get('ntos'), 'flagged': out.get('flagged'),
                             'cal': round(sum(sims) / len(sims), 3) if sims else None, **({'fallback': fb} if fb else {})}
        redo.discard(uid)
        changed_pk.add((slug, perek, bool(units_by[uid].get('fill'))))
        n_new += 1
        log('נקלט %s: %d תוספות, %s לעיון המנהל, כיול %s' % (uid, out.get('ntos', 0), out.get('flagged'), col['units'][uid]['cal']))
    idx['redo'] = sorted(redo)
    jdump(os.path.join(HO, 'index.json'), idx)
    jdump(os.path.join(HO, 'collected.json'), col)
    published_any = False
    for slug, perek, fill in sorted(changed_pk):
        try:
            published_any |= maybe_publish(slug, perek, fill, c, idx, col, alerts)
        except FF.Halt as e:
            st = F.state(slug)
            st['halt'] = str(e)
            F.save_state(slug, st)
            alerts.append('%s פרק %d: %s' % (F.SLUG2HE.get(slug, slug), perek, e))
            log('עצירה: %s פרק %d: %s' % (slug, perek, e))
    for a in alerts:
        mail('alert', 'התראת כיול או עצירה', a + '\n\nהפרק לא פורסם וממתין להכרעתך במסך המנהל. שאר העבודה ממשיכה.')
    if published_any:
        open(fp(F.FDIR, '.published-flag'), 'w').write(now_iso())
    write_board()
    print('קליטה: %d תוצרים חדשים, %d פגומים (ל-redo), %d פרקים שהשתנו' % (n_new, n_bad, len(changed_pk)))


def maybe_publish(slug, perek, fill, c, idx, col, alerts):
    mine = [u for u in idx['units'] if u['slug'] == slug and u['perek'] == perek]
    work = jload(FF.work_path(slug, perek))
    if fill:
        # יחידת השלמה: מפרסמים רק את התוספות שבה, ושאר הפרק (שכבר חי) אינו נוגע
        fills = [u['id'] for u in mine if u.get('fill') and (col['units'].get(u['id']) or {}).get('ok') and not (col['units'][u['id']].get('published'))]
        for uid in fills:
            only = {k for k, r in work['recs'].items() if r.get('handoff') == uid}
            w2 = copy.deepcopy(work)
            flagged = FF.finalize(w2)
            res = FF.publish(slug, perek, c, w2, flagged, only=only)
            col['units'][uid]['published'] = now_iso()
            log('השלמה פורסמה %s: %s' % (uid, {k: v for k, v in res.items() if k != 'skipped'}))
        jdump(os.path.join(HO, 'collected.json'), col)
        return bool(fills)
    regular = [u['id'] for u in mine if not u.get('fill')]
    if not all((col['units'].get(u) or {}).get('ok') for u in regular):
        return False
    st = F.state(slug)
    ps = st['perakim'].setdefault(str(perek), {'status': 'pending'})
    if ps.get('status') == 'published' and ps.get('handoff_units') == sorted(regular) and not any(u in (idx.get('redo') or []) for u in regular):
        # כבר פורסם; תוצר מחודש (redo) מפורסם שוב
        if all(col['units'][u].get('published') for u in regular):
            return False
    FF.drift_check(slug, perek, c, work, st)
    flagged = FF.finalize(work)
    res = FF.publish(slug, perek, c, work, flagged)
    jdump(FF.work_path(slug, perek), work)
    st.pop('halt', None)
    st.pop('blocked', None)
    for k in ('batch', 'batchPhase', 'submitted', 'nreq', 'retry'):
        ps.pop(k, None)
    ps.update({'status': 'published', 'published': now_iso(), 'unc_done': True, 'handoff_units': sorted(regular),
               'result': {k: v for k, v in res.items() if k != 'skipped'}})
    for u in regular:
        col['units'][u]['published'] = now_iso()
    jdump(os.path.join(HO, 'collected.json'), col)
    FF.notify(slug, perek, res, c)
    log('%s פרק %d פורסם: %s' % (slug, perek, ps['result']))
    pers = FF.counted_perakim(slug)
    if all((st['perakim'].get(str(p)) or {}).get('status') == 'published' for p in pers) and not st.get('done'):
        st['done'] = now_iso()
        F.save_state(slug, st)
        try:
            FF.write_report(slug)
        except Exception as e:
            log('דוח מסכת נכשל %s: %s' % (slug, e))
        mail('done', 'מסכת %s פורסמה' % F.SLUG2HE.get(slug, slug),
             'מסכת %s פורסמה במלואה באתר: %s/%s.html' % (F.SLUG2HE.get(slug, slug), c['siteBase'], slug))
    F.save_state(slug, st)
    return True


# ---------------------------------------------------------------- לוח המצב
def write_board(state_line=None):
    idx = index()
    col = collected()
    units = idx['units']
    tot_u = len(units)
    ok_u = sum(1 for u in units if (col['units'].get(u['id']) or {}).get('ok'))
    tot_t = sum(u['ntos'] for u in units)
    ok_t = sum(u['ntos'] for u in units if (col['units'].get(u['id']) or {}).get('ok'))
    flagged = sum((col['units'].get(u['id']) or {}).get('flagged') or 0 for u in units)
    ib = jload(os.path.join(HO, 'inbox.json')) or {}
    if state_line is None:
        state_line = 'מחובר לחשבון השני' if ib.get('units') else 'ממתין לחיבור (מייל החיבור מהחשבון השני טרם הגיע)'
    by = {}
    for u in units:
        b = by.setdefault(u['slug'], [0, 0, 0])
        b[1] += 1
        if (col['units'].get(u['id']) or {}).get('ok'):
            b[0] += 1
            b[2] += (col['units'][u['id']].get('flagged') or 0)
    # קצב: יחידות שנקלטו בשבעת הימים האחרונים
    now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    week = 0
    for v in col['units'].values():
        try:
            if v.get('ok') and (now - datetime.datetime.strptime(v['at'], '%Y-%m-%dT%H:%M:%SZ')).days < 7:
                week += 1
        except Exception:
            pass
    rate = week / 7.0
    eta = ('כ-%d ימים' % round((tot_u - ok_u) / rate)) if rate > 0 else 'לא ידוע עדיין'
    cals = [v['cal'] for v in col['units'].values() if v.get('cal') is not None]
    lines = ["## מפעל התוס' (לאוקמי גירסא, החשבון השני)", '',
             '- עודכן: %s UTC' % now.strftime('%d.%m.%Y %H:%M'),
             '- מצב: %s' % state_line,
             '- התקדמות: %d מתוך %d יחידות (%.1f%%), %d מתוך %d תוס\'' % (ok_u, tot_u, 100.0 * ok_u / max(1, tot_u), ok_t, tot_t),
             '- לעיון המנהל: %d תוס\'' % flagged,
             '- ממתינים לחזרה (redo): %d' % len(idx.get('redo') or []),
             '- קצב: %.1f יחידות ביום בשבוע האחרון; סיום צפוי: %s' % (rate, eta),
             '- כיול (דמיון לנוסח המנהל): %s' % ('%.2f בממוצע על %d יחידות' % (sum(cals) / len(cals), len(cals)) if cals else 'טרם נמדד'), '',
             '| מסכת | יחידות שהושלמו | סה"כ | לעיון המנהל |', '| :-: | :-: | :-: | :-: |']
    for slug, (a, b, f) in by.items():
        lines.append('| %s | %d | %d | %d |' % (F.SLUG2HE.get(slug, slug), a, b, f))
    io.open(os.path.join(HO, 'board.md'), 'w', encoding='utf-8', newline='\n').write('\n'.join(lines) + '\n')


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 1
    cmd = argv[1]
    if cmd == 'need':
        cmd_need()
    elif cmd == 'connect':
        cmd_connect(argv[2], argv[3], argv[4] if len(argv) > 4 else '')
    elif cmd == 'waiting':
        cmd_waiting()
    elif cmd == 'save':
        kv = dict(a.split('=', 1) for a in argv[3:] if '=' in a)
        cmd_save(argv[2], kv.get('name'), kv.get('id'), kv.get('modified'))
    elif cmd == 'collect':
        cmd_collect()
    elif cmd == 'sent':
        cmd_sent(argv[2])
    elif cmd == 'board':
        write_board()
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main(sys.argv))
