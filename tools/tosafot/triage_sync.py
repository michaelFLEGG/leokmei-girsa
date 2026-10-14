# -*- coding: utf-8 -*-
"""triage_sync.py - סנכרון מסך בדיקת התוספות (/tri בנקודת הקליטה) עם המאגר.

    uv run python tools/tosafot/triage_sync.py seed   # שולח את seed-<מסכת>.json לשרת (מה שנפסל, הנימוקים)
    uv run python tools/tosafot/triage_sync.py pull   # מושך את הכרעות המנהל אל tosafot/triage/examples.json (מאגר הדוגמאות)

המפתח: משתנה סביבה TRIAGE_ADMIN_KEY, ואחרת הקובץ המקומי של בעל הפרויקט (שורה 2). אינו נשמר במאגר.
"""
import os, sys, json, io, urllib.request, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TRI = os.path.join(ROOT, 'tosafot', 'triage')
API = os.environ.get('TRIAGE_API', 'https://leokmei-suggest.m7654301.workers.dev')
SLUGS = ('sukkah', 'berakhot')


def key():
    k = os.environ.get('TRIAGE_ADMIN_KEY')
    if k:
        return k.strip()
    p = os.path.expanduser('~/Documents/לאוקמי-מפתח-מנהל.txt')
    return io.open(p, encoding='utf-8').read().splitlines()[1].strip()


def call(path, body=None):
    req = urllib.request.Request(API + path, data=(json.dumps(body).encode('utf-8') if body is not None else None),
                                 headers={'x-admin-key': key(), 'Content-Type': 'application/json', 'User-Agent': 'tosafot-triage/1'})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode('utf-8'))


def seed():
    for sl in SLUGS:
        d = json.load(io.open(os.path.join(TRI, 'seed-%s.json' % sl), encoding='utf-8'))
        items = d['items']
        keys = list(items)
        for i in range(0, len(keys), 60):
            part = {k: items[k] for k in keys[i:i + 60]}
            j = call('/tri', {'op': 'seed', 'slug': sl, 'items': part})
            print(sl, i, j)


def pull():
    p = os.path.join(TRI, 'examples.json')
    doc = json.load(io.open(p, encoding='utf-8'))
    have = {e['id']: e for e in doc['items']}
    added = 0
    for sl in SLUGS:
        j = call('/tri?slug=' + sl)
        d = j['doc']
        for n, dec in (d.get('dec') or {}).items():
            it = (d.get('items') or {}).get(n)
            if not it or dec.get('ans') not in ('yes', 'no'):
                continue
            eid = '%s:%d-%d' % (sl, it['perek'], it['n'])
            e = {'id': eid, 'slug': sl, 'where': '%s, פרק %d, דף %s' % ('סוכה' if sl == 'sukkah' else 'ברכות', it['perek'], it['daf']),
                 'dh': it['dh'], 'text': it['text'], 'line': it['line'], 'qs': [], 'why': it.get('why') or [], 'ans': dec['ans'],
                 'note': dec.get('note') or '', 'at': '2026-10-14', 'src': 'מסך בדיקת תוספות'}
            if eid not in have:
                added += 1
            have[eid] = e
    doc['items'] = list(have.values())
    io.open(p, 'w', encoding='utf-8').write(json.dumps(doc, ensure_ascii=False, indent=1))
    print('examples:', len(doc['items']), 'new:', added)


if __name__ == '__main__':
    {'seed': seed, 'pull': pull}[sys.argv[1]]()
