# -*- coding: utf-8 -*-
"""report.py - רישום עלות הבקרה ודוחות הכללים.

    uv run python tools/bakara/report.py cost <slug> <פרק> <מודל> <טוקנים> [--usd X] [--kind מדידה|הערכה] [--note "..."]
        מוסיף שורה ל-data/bakara/costs.json (החלפה אם כבר יש שורה לאותו פרק+מודל+סוג)
    uv run python tools/bakara/report.py render
        כותב את docs/בקרה-עלויות.md ואת docs/בקרה-כללים-נלמדים.md מתוך הקבצים ב-data/bakara
        (rules.json, costs.json). אותם קבצים נטענים ל-Worker ע"י push.py ומוצגים באזור המנהל.
    uv run python tools/bakara/report.py sakem
        (פרומפט 70) עלות סכם לכל פרק מתוך data/sakem/runs.jsonl: הרצה שנמדדה מתמלול השיחה - "מדידה";
        הרצה ישנה - "הערכה" לפי הדקות, במקדם שמכויל מול ההרצות שנמדדו. כותב את costs.json (מפתח sakem),
        את data/sakem/costs.json (לדף המנהל "עלות לכל פרק") ואת הפרק "סכם" ב-docs/בקרה-עלויות.md.
"""
import os, sys, json, argparse

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
D = os.path.join(ROOT, 'data', 'bakara')
DOCS = os.path.join(ROOT, 'docs')


def _load(name, default):
    p = os.path.join(D, name)
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else default


def add_cost(a):
    c = _load('costs.json', {'v': 1, 'rows': []})
    row = {'slug': a.slug, 'perek': a.perek, 'model': a.model, 'tokens': a.tokens,
           'usd': a.usd, 'kind': a.kind, 'note': a.note}
    c['rows'] = [r for r in c['rows'] if not (r['slug'] == a.slug and r['perek'] == a.perek
                                              and r['model'] == a.model and r['kind'] == a.kind)]
    c['rows'].append(row)
    c['rows'].sort(key=lambda r: (r['slug'], r['perek'], r['model']))
    json.dump(c, open(os.path.join(D, 'costs.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


# ---- פרומפט 70: עלות סכם לכל פרק ----
TOK_PER_MIN0 = 1_000_000   # נקודת פתיחה: דקת סכם = כמיליון טוקנים מעובדים
USD_PER_MIN0 = 0.4         # וכ-0.4 דולר (אופוס 5.5, 95% קריאה מהמטמון)
CUTOFF = '2026-11-20'      # מכאן והלאה - "אחרי החיסכון" רק להרצות שסומנו lean


def _median(xs):
    xs = sorted(xs)
    return xs[len(xs) // 2] if xs else None


def sakem_costs(write=True):
    runs_f = os.path.join(ROOT, 'data', 'sakem', 'runs.jsonl')
    runs = []
    for line in open(runs_f, encoding='utf-8'):
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        if r.get('how') in ('finish', 'pause'):
            runs.append(r)
    meas = [r for r in runs if r.get('cost') == 'מדידה' and r.get('minutes')]
    tpm = _median([r['tokTotal'] / r['minutes'] for r in meas if r['minutes'] >= 2]) or TOK_PER_MIN0
    upm = _median([r['usd'] / r['minutes'] for r in meas if r['minutes'] >= 2]) or USD_PER_MIN0
    calib = {'tokPerMin': round(tpm), 'usdPerMin': round(upm, 3), 'basedOn': len(meas),
             'note': ('מכויל מול %d הרצות שנמדדו (חציון)' % len(meas)) if meas else 'טרם נמדדה הרצה - נקודת הפתיחה של פרומפט 70'}
    rows = []
    for r in runs:
        mins = r.get('minutes') or 0
        x = {'jid': r.get('jid'), 'slug': r.get('slug'), 'perek': r.get('perek'), 'title': r.get('title', ''),
             'round': r.get('round') or _round(r), 'how': r.get('how'), 'part': r.get('part'), 'end': r.get('end'),
             'minutes': mins, 'segs': r.get('segsThisRun'), 'station': r.get('station', ''), 'lean': bool(r.get('lean'))}
        if r.get('cost') == 'מדידה':
            x.update(kind='מדידה', tokens=r['tokTotal'], usd=r['usd'], model=r.get('model', ''),
                     byModel={k: {'tokens': v.get('total', 0), 'usd': v.get('usd', 0)} for k, v in (r.get('tokens') or {}).items()})
        else:
            x.update(kind='הערכה', tokens=int(mins * tpm), usd=round(mins * upm, 2), model='אופוס (משוער)',
                     why=r.get('costWhy', 'לא נרשם בזמנו'))
        rows.append(x)
    per = {}
    for x in rows:
        k = (x['slug'] or '?', x['perek'] or 0)
        p = per.setdefault(k, {'slug': k[0], 'perek': k[1], 'title': '', 'runs': 0, 'minutes': 0, 'tokens': 0, 'usd': 0,
                               'measured': 0, 'byRound': {}, 'byModel': {}, 'before': {'usd': 0, 'runs': 0}, 'after': {'usd': 0, 'runs': 0}})
        if not p['title']:
            p['title'] = (x['title'] or '').split(' · ')[0].split(' - ')[0]
        p['runs'] += 1; p['minutes'] += x['minutes']; p['tokens'] += x['tokens']; p['usd'] += x['usd']
        p['measured'] += x['kind'] == 'מדידה'
        b = p['byRound'].setdefault(x['round'], {'runs': 0, 'usd': 0, 'tokens': 0})
        b['runs'] += 1; b['usd'] += x['usd']; b['tokens'] += x['tokens']
        for m, v in (x.get('byModel') or {('opus' if x['kind'] == 'הערכה' else '?'): {'tokens': x['tokens'], 'usd': x['usd']}}).items():
            bm = p['byModel'].setdefault(m, {'tokens': 0, 'usd': 0})
            bm['tokens'] += v['tokens']; bm['usd'] += v['usd']
        side = 'after' if x['lean'] else 'before'
        p[side]['usd'] += x['usd']; p[side]['runs'] += 1
    perek = sorted(per.values(), key=lambda p: (p['slug'], p['perek']))
    for p in perek:
        p['usd'] = round(p['usd'], 2); p['minutes'] = round(p['minutes'], 1)
        for d in list(p['byRound'].values()) + list(p['byModel'].values()) + [p['before'], p['after']]:
            d['usd'] = round(d['usd'], 2)
    out = {'v': 1, 'generated': __import__('datetime').datetime.utcnow().strftime('%Y-%m-%dT%H:%MZ'),
           'calib': calib, 'perek': perek, 'runs': rows[-400:]}
    if not write:
        return out
    c = _load('costs.json', {'v': 1, 'rows': []})
    c['sakem'] = {'calib': calib, 'perek': perek, 'generated': out['generated']}
    json.dump(c, open(os.path.join(D, 'costs.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    json.dump(out, open(os.path.join(ROOT, 'data', 'sakem', 'costs.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return out


def _round(r):
    t, j = r.get('title', ''), r.get('jid', '')
    if 'נוסח החי' in t:
        return 'נוסח חי'
    import re
    if re.search(r'כללים חדשים|כללים אחרונים|פרומפט 6[2-9]', t):
        return 'כללים אחרונים'
    if re.search(r'סבב שני|סבב מבני|סבב מחודש|סבב כללים|סבב נוסף', t):
        return 'כללים מעודכנים'
    if re.search(r'-s\d', j):
        return 'סבב קטעים'
    return 'ראשון'


def render():
    c = _load('costs.json', {'rows': []})
    L = ['# בקרה: עלות לכל פרק', '',
         'נוצר מ-`data/bakara/costs.json` ע"י `tools/bakara/report.py render`. "הערכה" = לא נרשם בזמנו, והמספר נגזר.',
         'טוקנים = סך הקלט והפלט יחד כפי שדווחו לסוכן (כמעט כולם קלט: קריאת הגמרא וההנחיות).', '',
         '| מסכת | פרק | מודל | טוקנים | עלות משוערת ($) | סוג | הערה |', '|---|---|---|---|---|---|---|']
    for r in c['rows']:
        L.append('| %s | %s | %s | %s | %s | %s | %s |' % (
            r['slug'], r['perek'], r['model'], format(r['tokens'], ','),
            ('%.2f' % r['usd']) if r.get('usd') is not None else '-', r['kind'], r.get('note', '')))
    sk = c.get('sakem')
    if sk:
        cb = sk['calib']
        L += ['', '## סכם: עלות לכל פרק (פרומפט 70)', '',
              '"מדידה" = נקרא מתמלול השיחה של ההרצה (usage לכל הודעה, כולל סוכני-משנה). "הערכה" = הרצה ישנה, לפי הדקות: '
              '%s טוקנים ו-%s דולר לדקה (%s).' % (format(cb['tokPerMin'], ','), cb['usdPerMin'], cb['note']), '',
              '| מסכת | פרק | הרצות | נמדדו | דקות | טוקנים | שווי ($) | לפני החיסכון ($) | אחרי החיסכון ($) |', '|---|---|---|---|---|---|---|---|---|']
        tot = {}
        for p in sk['perek']:
            L.append('| %s | %s | %d | %d | %s | %s | %.2f | %.2f | %s |' % (p['slug'], p['perek'], p['runs'], p['measured'], p['minutes'],
                     format(p['tokens'], ','), p['usd'], p['before']['usd'], ('%.2f' % p['after']['usd']) if p['after']['runs'] else '-'))
            t = tot.setdefault(p['slug'], [0, 0])
            t[0] += p['usd']; t[1] += p['runs']
        L += ['', '| מסכת | הרצות | שווי ($) |', '|---|---|---|'] + ['| %s | %d | %.2f |' % (k, v[1], v[0]) for k, v in sorted(tot.items())]
    open(os.path.join(DOCS, 'בקרה-עלויות.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')

    r_ = _load('rules.json', {'rules': []})
    L = ['# בקרה: כללים שנלמדו מהכרעות המנהל (מצטבר)', '',
         'נוצר מ-`data/bakara/rules.json`. בסיס: ' + r_.get('basis', ''), '', r_.get('threshold', ''), '']
    for x in r_['rules']:
        cn = x['counts']
        L += ['## %s · %s · %s (%d הכרעות)' % (x['id'], x['det'], x['status'], x['n']),
              ' · '.join('%s %s' % (k, v) for k, v in cn.items()), '',
              x['text'], '', '- דוגמה: ' + x['example'], '- השפעה על המנוע: ' + x['effect'], '']
    open(os.path.join(DOCS, 'בקרה-כללים-נלמדים.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest='cmd', required=True)
    c = sp.add_parser('cost')
    c.add_argument('slug'); c.add_argument('perek', type=int); c.add_argument('model')
    c.add_argument('tokens', type=int)
    c.add_argument('--usd', type=float, default=None)
    c.add_argument('--kind', default='מדידה')
    c.add_argument('--note', default='')
    sp.add_parser('render')
    sp.add_parser('sakem')
    a = ap.parse_args()
    if a.cmd == 'cost':
        add_cost(a)
    if a.cmd == 'sakem':
        o = sakem_costs()
        print('סכם: %d הרצות, %d פרקים, מקדם %s' % (len(o['runs']), len(o['perek']), o['calib']))
    render()
