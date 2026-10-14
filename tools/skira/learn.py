# -*- coding: utf-8 -*-
"""learn.py - הלמידה של הסקירה מהכרעות המחבר (מנה 13.10.2026, סעיף 7).

    uv run python tools/skira/learn.py [--no-pull] [--no-push] [--slug sukkah]

מה הוא עושה, בסדר:
 א. מושך את ההכרעות (קבלה, דחייה עם סיבה, עריכה, שרשורי "שוחח") מנקודת הקליטה אל
    data/skira/decisions-<מסכת>.json, ומסנכרן את הקובץ שהסוקר מסנן לפיו (stats.py).
 ב. לומד מעריכות שלא עברו דרך הסקירה (7ה): תיקון שהמחבר פרסם בשורה שהיתה עליה הערה
    פתוחה נרשם כהכרעה (קבלה / עריכה) לפי ההשוואה. נכתב ל-data/skira/external-<מסכת>.json.
 ג. מחשב שיעורי קבלה לכל סוג ולכל גלאי, ושומר היסטוריה לפי הרצה (גרף ב"מה למדתי").
 ד. מפיק: data/skira/suppress.json ("לא להעיר על זה שוב", וסוגים מושתקים),
    data/skira/rules.json (הכללים), data/skira/distill-input.json (עריכות שהמחבר כתב
    בעצמו, לזיקוק בסוכן sonnet לפי prompts/distill.md), ואת tools/skira/review-rules.md
    ("חוקת הסקירה": החלק היציב שנקרא ממטמון, עד 12 אלף טוקנים).
 ה. כללי סגנון נכתבים גם לדף הכיול של בית החרושת (tools/bkh/prompts/calibration.md),
    בבלוק מסומן "מהסקירה <תאריך>".
 ו. מעלה את הכללים והשיעורים ל-/skira/learned (למסך "מה למדתי").

כלל נכנס רק משני מופעים ומעלה, או ממופע חד-משמעי שהמחבר ניסח במפורש בשרשור.
הזיקוק עצמו (ניסוח כלל מדוגמאות) נעשה בסוכן זול, לא באופוס: אין כאן קריאת מודל.
"""
import os, sys, re, json, argparse, datetime, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import skira_common as C

REJ_MUTE, REJ_MUTE_MIN = 0.80, 8      # סעיף 5ט: מעל 80% דחיות מתוך 8 לפחות: הסוג מושתק
REJ_DEMOTE, REJ_DEMOTE_MIN = 0.60, 8  # מעל 60%: ודאות "ספק" ומקופל
ACC_MECH, ACC_MECH_MIN = 0.95, 10     # מעל 95% מתוך 10: מועמד למנוע המכני
HARD_REASONS = {'no_err', 'my_way', 'unimp', 'not_get'}   # סיבות שהדפוס בהן לא חוזר
RULES_CAP = 24000                      # תווים (כ-12 אלף טוקנים)
RB, RE = '<!-- skira:begin -->', '<!-- skira:end -->'


def pull(slugs):
    import _api
    import stats
    stats.main()            # data/bakara/decisions-*.json + stats.json
    out = {}
    for s in slugs:
        doc = _api.call('/bakara/dec?slug=' + s).get('doc') or {}
        out[s] = doc.get('dec') or {}
        C.jsave(os.path.join(C.DATA, 'decisions-%s.json' % s), out[s])
        try:
            th = _api.call('/skira/threads?slug=' + s)
            C.jsave(os.path.join(C.DATA, 'threads-%s.json' % s), th.get('open') or {})
        except BaseException as e:      # נקודת קליטה שטרם עודכנה (404): ממשיכים בלי שרשורים
            print('אזהרה: שרשורים לא נמשכו:', str(e)[:80])
    return out


def local_decisions(slugs):
    out = {}
    for s in slugs:
        out[s] = C.jload(os.path.join(C.DATA, 'decisions-%s.json' % s)) or \
                 C.jload(os.path.join(C.BDATA, 'decisions-%s.json' % s), {})
    return out


def external(slug, decided):
    """7ה: תיקון שפורסם בשורה שהיתה עליה הערה פתוחה. מתוך data/edits/<מסכת>.json."""
    ed = C.jload(os.path.join(C.ROOT, 'data', 'edits', slug + '.json'), {}) or {}
    edits = ed.get('edits') or []
    prev = C.jload(os.path.join(C.DATA, 'external-%s.json' % slug), {}) or {}
    if not edits:
        return prev
    res = dict(prev)
    for _p, f in C.findings_of(slug):
        fid = f['id']
        if fid in decided or fid in res:
            continue
        mk = C.norm(f.get('mark', ''))
        cx = C.norm(f.get('context') or f.get('text') or '')
        if not mk or not cx:
            continue
        for e in edits:
            was, now = C.norm(e.get('was', '')), C.norm(e.get('now', ''))
            if cx in was and was != now:
                if mk in now:
                    break           # השורה שונתה במקום אחר; ההערה עדיין תקפה
                fx = f.get('fix') or ''
                y = C.norm(fx.split('⟵')[1].replace('?', '')) if '⟵' in fx else ''
                d = 'ok' if (y and y in now) else 'edit'
                res[fid] = {'d': d, 'det': f.get('det'), 'kind': f.get('kind'), 'now': '', 'txt': '',
                            'src': 'ext', 't': int(e.get('t') or 0)}
                break
    C.jsave(os.path.join(C.DATA, 'external-%s.json' % slug), res)
    return res


def collect(slugs, decs):
    rows = []
    for s in slugs:
        by = {f['id']: (p, f) for p, f in C.findings_of(s)}
        ext = external(s, decs.get(s, {}))
        for src, dd in (('web', decs.get(s, {})), ('ext', ext)):
            for fid, d in dd.items():
                if d.get('d') not in ('ok', 'todo', 'no', 'edit'):
                    continue
                p, f = by.get(fid, (0, {}))
                rows.append({'slug': s, 'id': fid, 'perek': p, 'src': src,
                             'det': d.get('det') or f.get('det') or '?', 'kind': d.get('kind') or f.get('kind') or '',
                             'typ': C.typ_of(f) if f else C.DET2TYP.get(d.get('det') or '', 'g'),
                             'd': d['d'], 'rs': d.get('rs') or '', 'why': d.get('txt') or '',
                             'now': d.get('now') or '', 'sug': d.get('sug') or '',
                             'mark': f.get('mark', ''), 'ctx': f.get('context') or f.get('text') or '',
                             'fix': f.get('fix', ''), 'note': f.get('note', ''), 't': d.get('t', 0)})
    return rows


def rates(rows):
    by_t = collections.defaultdict(lambda: {'ok': 0, 'no': 0, 'edit': 0})
    by_d = collections.defaultdict(lambda: {'ok': 0, 'no': 0, 'edit': 0, 'kind': ''})
    for r in rows:
        k = 'no' if r['d'] == 'no' else ('edit' if r['d'] == 'edit' else 'ok')
        by_t[r['typ']][k] += 1
        by_d[r['det']][k] += 1
        by_d[r['det']]['kind'] = r['kind']
    return by_t, by_d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--no-pull', action='store_true')
    ap.add_argument('--no-push', action='store_true')
    ap.add_argument('--slug')
    a = ap.parse_args()
    slugs = [a.slug] if a.slug else C.slugs_with_findings()
    decs = local_decisions(slugs) if a.no_pull else pull(slugs)
    rows = collect(slugs, decs)
    by_t, by_d = rates(rows)
    now = datetime.date.today().isoformat()

    # ---- דיכוי: דפוסים שנדחו, וסוגים מושתקים / מורדים ----
    patterns, muted, demoted, mech = set(), [], [], []
    for r in rows:
        if r['d'] == 'no' and r['rs'] in HARD_REASONS and r['mark']:
            patterns.add(r['det'] + '|' + C.norm(r['mark']))
    # דפוס שנדחה שוב ושוב (שני מופעים ומעלה, גם בלי סיבה): אינו חוזר
    rep = collections.Counter(r['det'] + '|' + C.norm(r['mark']) for r in rows if r['d'] == 'no' and r['mark'])
    okk = collections.Counter(r['det'] + '|' + C.norm(r['mark']) for r in rows if r['d'] != 'no' and r['mark'])
    for k, v in rep.items():
        if v >= 2 and okk.get(k, 0) == 0:
            patterns.add(k)
    for det, s in by_d.items():
        n = s['ok'] + s['no'] + s['edit']
        if n >= REJ_MUTE_MIN and s['no'] / n > REJ_MUTE and det.startswith(('sem_', 'sk_', 'cl_')):
            muted.append(det)       # רק סוגי מודל: סוג קוד אינו עולה טוקנים, והוא מורד ל"קל" ב-stats.py
        elif n >= REJ_DEMOTE_MIN and s['no'] / n > REJ_DEMOTE:
            demoted.append(det)
        if n >= ACC_MECH_MIN and (s['ok'] + s['edit']) / n >= ACC_MECH and det not in muted:
            mech.append('%s (%s): %d מתוך %d התקבלו' % (s['kind'] or det, det, s['ok'] + s['edit'], n))
    old = C.jload(os.path.join(C.DATA, 'suppress.json'), {}) or {}
    C.jsave(os.path.join(C.DATA, 'suppress.json'),
            {'when': now, 'patterns': sorted(patterns | set(old.get('patterns') or [])),
             'muted': sorted(set(muted) | set(old.get('muted_manual') or [])), 'muted_manual': old.get('muted_manual') or [],
             'demoted': sorted(demoted)})

    # ---- כללים: בקרה 6.10 + דפוסי דחייה (2 מופעים ומעלה) + מזוקק ----
    rules = []
    base = C.jload(os.path.join(C.BDATA, 'rules.json'), {}) or {}
    for r in base.get('rules', []):
        rules.append({'id': r['id'], 'typ': C.DET2TYP.get(r.get('det'), 'g'), 'det': r.get('det'), 'text': r.get('text', ''),
                      'n': r.get('n', 0), 'ex': r.get('example', ''), 'src': 'בקרה 6.10.2026'})
    rej = collections.defaultdict(list)
    for r in rows:
        if r['d'] == 'no':
            rej[r['det']].append(r)
    for det, L in sorted(rej.items()):
        if len(L) < 2 or any(x['id'] == 'S-' + det for x in rules):
            continue
        reasons = collections.Counter(R['rs'] or 'unspec' for R in L)
        why = ', '.join('%s x%d' % (C.REASONS.get(k, k), v) for k, v in reasons.most_common(3))
        ex = ' | '.join('"%s"' % x['mark'][:40] for x in L[:2])
        rules.append({'id': 'S-' + det, 'typ': C.DET2TYP.get(det, 'g'), 'det': det,
                      'text': 'הערות מסוג "%s" נדחו %d פעמים (%s). אל תעיר על דפוס דומה לדוגמאות.' % (L[0]['kind'] or det, len(L), why),
                      'n': len(L), 'ex': ex, 'src': 'סקירה'})
    dist = C.jload(os.path.join(C.DATA, 'distilled.json'), {}) or {}
    for i, r in enumerate(dist.get('rules', []), 1):
        rules.append({'id': r.get('id') or 'D%d' % i, 'typ': r.get('typ', 'e'), 'det': '', 'text': C.no_dash(r['text']),
                      'n': r.get('n', 0), 'ex': C.no_dash(' | '.join(r.get('ex', [])[:2])), 'src': 'סקירה (מזוקק)',
                      'style': bool(r.get('style'))})

    # ---- קלט לזיקוק: מה שהמחבר כתב בעצמו ----
    dist_in = []
    for r in rows:
        if r['d'] == 'edit' and r['now'] and r['now'].strip() != r['sug'].strip():
            dist_in.append({'id': r['id'], 'typ': r['typ'], 'kind': r['kind'], 'ctx': r['ctx'][:240], 'mark': r['mark'],
                            'suggested': r['sug'], 'author_wrote': r['now'][:400]})
        if r['d'] == 'no' and r['rs'] == 'my_way':
            dist_in.append({'id': r['id'], 'typ': r['typ'], 'kind': r['kind'], 'ctx': r['ctx'][:240], 'mark': r['mark'],
                            'suggested': r['sug'], 'author_wrote': '(דחה: "כך אני כותב")'})
    for s in slugs:
        for fid, msgs in (C.jload(os.path.join(C.DATA, 'threads-%s.json' % s), {}) or {}).items():
            dist_in.append({'id': fid, 'thread': [m['txt'] for m in msgs if m.get('who') == 'm'][-3:]})
    C.jsave(os.path.join(C.DATA, 'distill-input.json'), {'when': now, 'items': dist_in})

    # ---- שיעורי קבלה והיסטוריה ----
    ok_all = sum(s['ok'] + s['edit'] for s in by_t.values())
    n_all = sum(s['ok'] + s['edit'] + s['no'] for s in by_t.values())
    old_r = C.jload(os.path.join(C.DATA, 'rates.json'), {}) or {'runs': []}
    runs = old_r.get('runs', [])
    if not runs or runs[-1].get('n') != n_all:
        runs.append({'date': now, 'n': n_all, 'acc': (ok_all / n_all) if n_all else 0,
                     'by': {k: dict(v) for k, v in by_t.items()}})
    rates_doc = {'runs': runs[-30:], 'mech': mech, 'by_typ': {k: dict(v) for k, v in by_t.items()},
                 'by_det': {k: dict(v) for k, v in by_d.items()}}
    C.jsave(os.path.join(C.DATA, 'rates.json'), rates_doc)
    C.jsave(os.path.join(C.DATA, 'rules.json'), {'when': now, 'rules': rules})

    # ---- חוקת הסקירה ----
    L = ['# חוקת הסקירה (נבנה אוטומטית, %s)' % now, '',
         'מקור: %d הכרעות של המחבר. אל תערוך ביד: `tools/skira/learn.py` כותב מחדש.' % n_all, '',
         '## הסוגים (כל הערה שייכת לסוג אחד)', '']
    for k, v in C.TYP.items():
        if k in ('i',):
            continue
        s = by_t.get(k)
        rate = ' - קבלה %d%% מתוך %d' % (round(100 * (s['ok'] + s['edit']) / max(1, s['ok'] + s['edit'] + s['no'])), s['ok'] + s['edit'] + s['no']) \
            if s and (s['ok'] + s['edit'] + s['no']) >= 3 else ''
        L.append('- %s) %s%s' % (k, v, rate))
    if muted:
        L += ['', '## סוגים מושתקים (דחייה מעל 80%): אל תייצר', ''] + ['- ' + d for d in muted]
    if demoted:
        L += ['', '## סוגים שנדחים לרוב: ודאות "ספק" בלבד', ''] + ['- ' + d for d in demoted]
    L += ['', '## כללים שנלמדו', '']
    for r in rules:
        L.append('- [%s] %s%s' % (r['id'], r['text'], (' (דוגמאות: %s)' % r['ex']) if r.get('ex') else ''))
    if patterns:
        L += ['', '## דפוסים שנדחו שוב ושוב (%d): אינם חוזרים ממילא בקוד' % len(patterns)]
    txt = C.no_dash('\n'.join(L))
    if len(txt) > RULES_CAP:
        txt = txt[:RULES_CAP] + '\n...(נחתך בתקרת הגודל)'
    open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'review-rules.md'), 'w', encoding='utf-8').write(txt + '\n')

    # ---- דף הכיול של בית החרושת: כללי סגנון בלבד ----
    cal = os.path.join(C.TOOLS, 'bkh', 'prompts', 'calibration.md')
    style = [r for r in rules if r.get('style')]
    if os.path.exists(cal) and style:
        s = open(cal, encoding='utf-8').read()
        blk = RB + '\n## מהסקירה %s\n' % now + '\n'.join('- %s' % r['text'] for r in style) + '\n' + RE
        if RB in s and RE in s:
            s = s[:s.index(RB)] + blk + s[s.index(RE) + len(RE):]
        else:
            s = s.rstrip() + '\n\n' + blk + '\n'
        open(cal, 'w', encoding='utf-8').write(s)
    print('הכרעות: %d · כללים: %d · דפוסי דיכוי: %d · מושתקים: %s · מועמדים למנוע המכני: %d · לזיקוק: %d' % (
        n_all, len(rules), len(patterns), muted or '-', len(mech), len(dist_in)))
    for k, s in sorted(by_t.items()):
        n = s['ok'] + s['edit'] + s['no']
        print('  %s %-12s קבלה %3d%% (%d)' % (k, C.TYP[k], round(100 * (s['ok'] + s['edit']) / n), n))

    if not a.no_push:
        import _api
        _api.call('/skira/learned', 'PUT', {'rules': rules, 'rates': rates_doc})
        print('הכללים הועלו ל"מה למדתי"')


if __name__ == '__main__':
    main()
