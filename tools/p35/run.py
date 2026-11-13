"""פרומפט 35 (13.11.2026): ייצוא ההצעות הממתינות (בלי שם המציע ובלי מזהה המכשיר)
והחלת סגירות (stale/rejected בלבד - לעולם לא אישור) מתוך _work/p35/decide.json."""
import io, json, os, sys, urllib.request
API = 'https://leokmei-suggest.m7654301.workers.dev'
OUT = os.path.join('_work', 'p35')

def call(path, body=None):
    key = os.environ.get('LEOKMEI_ADMIN_KEY', '')
    if not key: sys.exit('חסר LEOKMEI_ADMIN_KEY')
    data = None if body is None else json.dumps(body, ensure_ascii=False).encode('utf-8')
    rq = urllib.request.Request(API + path, data=data, method='POST' if body is not None else 'GET',
        headers={'x-admin-key': key, 'content-type': 'application/json; charset=utf-8', 'user-agent': 'leokmei-p35'})
    with urllib.request.urlopen(rq, timeout=60) as r:
        j = json.loads(r.read().decode('utf-8'))
    if not j.get('ok'): raise RuntimeError('%s: %s' % (path, j.get('error')))
    return j

def strip(v):
    v = dict(v)
    for f in ('name', 'pid', 'ip', 'pt', 'dev'): v.pop(f, None)
    v['thread'] = [{'t': x.get('t'), 'txt': x.get('txt') or x.get('text') or x.get('m'), 'adm': x.get('adm') or x.get('a')}
                   for x in (v.get('thread') or []) if isinstance(x, dict)]
    return v

def main():
    log = []
    dp = os.path.join(OUT, 'decide.json')
    if os.path.exists(dp):
        dec = json.load(io.open(dp, encoding='utf-8'))
        done_p = os.path.join(OUT, 'decided.json')
        done = json.load(io.open(done_p, encoding='utf-8')) if os.path.exists(done_p) else {}
        for d in dec:
            if d['id'] in done: continue
            if d['st'] not in ('stale', 'rejected'): raise SystemExit('הכרעה אסורה: ' + d['st'])
            try:
                call('/decide', {'id': d['id'], 'st': d['st'], 'reason': d['reason'][:200]})
                done[d['id']] = d['st']
            except Exception as e:
                log.append('נכשל %s: %s' % (d['id'], e))
        json.dump(done, io.open(done_p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    allv, counts = [], None
    for slug in ('sukkah', 'bekhorot', 'berakhot', 'bava-batra'):
        page = 0
        while True:
            j = call('/queue?slug=%s&size=40&page=%d&ord=loc' % (slug, page))
            counts = j.get('counts')
            allv += [strip(v) for v in j['items']]
            if (page + 1) * 40 >= j.get('matched', 0): break
            page += 1
    json.dump({'counts': counts, 'n': len(allv), 'log': log, 'items': allv},
              io.open(os.path.join(OUT, 'pending.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('ממתינות:', counts, 'יוצאו', len(allv), log)

main()
