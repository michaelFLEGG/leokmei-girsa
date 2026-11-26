# -*- coding: utf-8 -*-
"""החוקר - יומן הממצאים הקבוע.

ממזג את ההליכה (walk.json) לתוך data/chokker/findings.json, שבו כל ממצא נשאר לתמיד:
  פתוח -> תוקן (המוח תיקן) -> אומת (הליכה אחרי התיקון לא מצאה אותו) ; חזר = נסיגה, בעדיפות עליונה.
  "לבעלים" = שאלה אמיתית למיכאל (רק המוח מסמן כך, עם הצדדים). "הוכרע" = מיכאל ענה; ההכרעה נכנסת לכללים.
כל ממצא שתוקן הופך לבדיקת נסיגה קבועה: הכלל שלו נשאר ב-invariants.json לתמיד.

  python tools/chokker/ledger.py data/chokker/runs/2026-11-26
פלט: findings.json (מעודכן), <run>/summary.md (למוח), <run>/stats.json.
"""
import os, sys, io, json, hashlib, datetime, re, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DB = os.path.join(ROOT, 'data', 'chokker', 'findings.json')
INV = json.load(io.open(os.path.join(HERE, 'invariants.json'), encoding='utf-8'))
RULE = {r['id']: r for r in INV['rules']}
SITES = json.load(io.open(os.path.join(HERE, 'sites.json'), encoding='utf-8'))


def key(*parts):
    s = '|'.join(str(p) for p in parts)
    return hashlib.sha1(s.encode('utf-8')).hexdigest()[:12]


def norm(t):
    return re.sub(r'\d+', '#', (t or ''))[:90]


def collect(w):
    """ממצאים גולמיים מן ההליכה: (rule, site, page, scope, text, evidence)"""
    out = []
    for s in w['screens']:
        scope = '%s/%s' % (s.get('vp'), s.get('mode'))
        if s.get('fatal'):
            out.append(('E00-fatal', s['site'], s['page'], scope, s['fatal'][-200:], {}))
        for e in s.get('errors') or []:
            out.append(('E01-console', s['site'], s['page'], scope, e, {}))
        for v in (s.get('probe') or {}).get('v') or []:
            out.append((v['rule'], s['site'], s['page'], scope, v.get('text', ''), {k: v[k] for k in ('rect', 'daf', 'unit') if k in v}))
        if s.get('t_first_row') and s['t_first_row'] > (6 if s['vp'] in ('phone', 'tablet-p', 'tablet-l') else 4):
            out.append(('S01-slow-first', s['site'], s['page'], scope, 'השורה הראשונה הופיעה אחרי %.1f שניות' % s['t_first_row'], {}))
        if s.get('t_load') and s['t_load'] > 6:
            out.append(('S01-slow-first', s['site'], s['page'], scope, 'טעינה %.1f שניות' % s['t_load'], {}))
    for b in w.get('buttons', []):
        sc = '%s/btn' % b['vp']
        if b.get('fail'):
            out.append(('B01-btn-fail', b['site'], b['page'], sc, '%s: %s' % (b['btn'], b['fail'][:100]), {}))
        for e in b.get('errors') or []:
            out.append(('B02-btn-error', b['site'], b['page'], sc, '%s: %s' % (b['btn'], e), {}))
        for v in (b.get('probe') or {}).get('v') or []:
            if v['rule'].startswith('G'):
                out.append((v['rule'], b['site'], b['page'], sc + ':' + b['btn'], v.get('text', ''), {}))
    for p in w.get('print', []):
        sc = 'print/%s/%s' % (p['profile'], p['perek'])
        if p.get('fatal') or p.get('state') != 'done':
            out.append(('P01-print-fail', p['site'], p['page'], sc, 'מצב %s %s' % (p.get('state'), (p.get('report') or {}).get('error') or (p.get('fatal') or '')[-150:]), {}))
            continue
        m = p.get('measure') or {}
        if m.get('empty_pages'):
            out.append(('P02-empty-page', p['site'], p['page'], sc, 'עמודים ריקים: %s' % m['empty_pages'], {}))
        if m.get('em_dash') or m.get('en_dash'):
            out.append(('T01-em-dash', p['site'], p['page'], sc, 'בהדפסה: %d ארוכים, %d בינוניים' % (m['em_dash'], m['en_dash']), {}))
        if m.get('latin'):
            out.append(('P03-print-latin', p['site'], p['page'], sc, 'לועזית בהדפסה: %s' % m['latin'][:5], {}))
        for g in m.get('white_gaps') or []:
            out.append(('P04-white-gap', p['site'], p['page'], sc, 'חלל לבן של %s מ"מ בעמוד %s' % (g[1], g[0]), {'page': g[0]}))
        bl = m.get('balance_last')
        if bl and bl['diff_mm'] > 10:
            out.append(('P05-unbalanced-end', p['site'], p['page'], sc, 'סוף הפרק צולע: הפרש %s מ"מ בין הטורים' % bl['diff_mm'], {}))
        if p.get('t_layout', 0) > 60:
            out.append(('P06-print-slow', p['site'], p['page'], sc, 'העימוד נמשך %s שניות' % p['t_layout'], {}))
        for wv in ((p.get('report') or {}).get('warn') or [])[:15]:
            out.append(('P07-engine-warn', p['site'], p['page'], sc, wv, {}))
    kf = {}
    for s in SITES.values():
        kf.update(s.get('known_foreign', {}))
    for vp, n in (w.get('net') or {}).items():
        for host, c in n.get('foreign', {}).items():
            note = next((v for k, v in kf.items() if host.endswith(k)), '')
            out.append(('N01-foreign-domain', '*', '*', 'net', '%s (%d בקשות) %s' % (host, c, note), {}))
        for k, c in n.get('bad', {}).items():
            out.append(('N02-http-error', '*', '*', 'net', k, {}))
    for e in w.get('errors') or []:
        out.append(('E02-walk', '*', '*', 'walk', e, {}))
    return out


def main():
    run = sys.argv[1]
    w = json.load(io.open(os.path.join(run, 'walk.json'), encoding='utf-8'))
    db = json.load(io.open(DB, encoding='utf-8')) if os.path.exists(DB) else {'about': 'יומן הממצאים הקבוע של החוקר. לא מוחקים ממנו לעולם.', 'findings': {}}
    F = db['findings']
    today = os.path.basename(run.rstrip('/'))
    raw = collect(w)
    seen = set()
    scope_pages = {(s['site'], s['page']) for s in w['screens']} | {(p['site'], p['page']) for p in w.get('print', [])}
    newc, regr = 0, 0
    for rule, site, page, scope, text, ev in raw:
        k = key(rule, site, page, norm(text))
        if k in seen:
            F[k]['scopes'] = sorted(set(F[k].get('scopes', [])) | {scope})[:20]
            continue
        seen.add(k)
        r = RULE.get(rule, {})
        if k not in F:
            F[k] = {'rule': rule, 'site': site, 'page': page, 'text': text[:240], 'evidence': ev, 'first': today, 'status': 'פתוח',
                    'sev': r.get('sev', 'med'), 'title': r.get('text', rule), 'scopes': [scope], 'history': [[today, 'נמצא']]}
            newc += 1
        else:
            f = F[k]
            if f['status'] in ('אומת', 'תוקן'):
                f['status'] = 'חזר'
                f['history'].append([today, 'חזר - נסיגה'])
                regr += 1
            f['scopes'] = sorted(set(f.get('scopes', [])) | {scope})[:20]
        F[k]['last'] = today
        F[k]['nights'] = F[k].get('nights', 0) + 1
    gone = 0
    for k, f in F.items():
        if k in seen or (f['site'], f['page']) not in scope_pages and f['site'] != '*':
            continue
        if f['status'] in ('פתוח', 'תוקן', 'חזר'):
            f['status'] = 'אומת' if f['status'] in ('תוקן', 'חזר') else 'נעלם'
            f['history'].append([today, f['status']])
            gone += 1
    json.dump(db, io.open(DB, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    open_ = [f for f in F.values() if f['status'] in ('פתוח', 'חזר') and f.get('last') == today]
    by = collections.Counter((f['rule'], f['title']) for f in open_)
    sevc = collections.Counter(f['sev'] for f in open_)
    st = {'date': today, 'raw': len(raw), 'unique_tonight': len(seen), 'new': newc, 'regressed': regr, 'gone': gone,
          'open_by_sev': dict(sevc), 'screens': len(w['screens']), 'prints': len(w.get('print', [])), 'buttons': len(w.get('buttons', []))}
    json.dump(st, io.open(os.path.join(run, 'stats.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    L = ['# החוקר - סיכום הלילה %s' % today, '',
         'מסכים: %(screens)d · הדפסות: %(prints)d · כפתורים: %(buttons)d · ממצאים ייחודיים: %(unique_tonight)d · חדשים: %(new)d · נסיגות: %(regressed)d · נעלמו/אומתו: %(gone)d' % st, '',
         '## לפי כלל (פתוחים הלילה)', '']
    for (rid, title), c in by.most_common():
        L.append('- %s (%d) - %s' % (rid, c, title))
    L += ['', '## דוגמאות (עד 5 לכל כלל)', '']
    shown = collections.Counter()
    for k, f in sorted(F.items(), key=lambda x: ({'high': 0, 'med': 1, 'low': 2}.get(x[1]['sev'], 3), x[1]['rule'])):
        if f not in open_ or shown[f['rule']] >= 5:
            continue
        shown[f['rule']] += 1
        L.append('- `%s` [%s] %s %s · %s · %s' % (k, f['status'], f['rule'], f['page'], ','.join(f.get('scopes', [])[:3]), f['text'][:150]))
    io.open(os.path.join(run, 'summary.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    print(json.dumps(st, ensure_ascii=False))


if __name__ == '__main__':
    main()
