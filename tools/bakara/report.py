# -*- coding: utf-8 -*-
"""report.py - רישום עלות הבקרה ודוחות הכללים.

    uv run python tools/bakara/report.py cost <slug> <פרק> <מודל> <טוקנים> [--usd X] [--kind מדידה|הערכה] [--note "..."]
        מוסיף שורה ל-data/bakara/costs.json (החלפה אם כבר יש שורה לאותו פרק+מודל+סוג)
    uv run python tools/bakara/report.py render
        כותב את docs/בקרה-עלויות.md ואת docs/בקרה-כללים-נלמדים.md מתוך הקבצים ב-data/bakara
        (rules.json, costs.json). אותם קבצים נטענים ל-Worker ע"י push.py ומוצגים באזור המנהל.
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
    a = ap.parse_args()
    if a.cmd == 'cost':
        add_cost(a)
    render()
