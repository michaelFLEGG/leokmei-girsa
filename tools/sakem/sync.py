# -*- coding: utf-8 -*-
"""סכם - סנכרון בין נקודת הקליטה (Worker) לריפו (פרומפט 15, 28.10.2026).

רץ בפעולת גיטהאב sakem-sync.yml (כל רבע שעה, ובכל דחיפה של הצעות). שלושה כיוונים:
  א. חבילות חדשות בתור  ← Worker   →  data/sakem/queue/<jid>.json
  ב. הצעות שהמשימה בענן כתבה        data/sakem/out/<jid>.json  →  Worker
  ג. הכרעות של פרק שנסקר עד סופו    ← Worker   →  data/sakem/decisions/<jid>.json
המשימה בענן עובדת רק מול הריפו (git), ולכן אינה צריכה רשת אל השרת ולא מפתח.

שימוש:  python tools/sakem/sync.py           (המפתח במשתנה LEOKMEI_ADMIN_KEY)
        python tools/sakem/sync.py --dry     (מדפיס בלבד)
"""
import hashlib, io, json, os, sys, urllib.request

API = os.environ.get('SAKEM_API') or 'https://leokmei-suggest.m7654301.workers.dev'
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
D = os.path.join(ROOT, 'data', 'sakem')
STATE = os.path.join(D, 'sync-state.json')
DRY = '--dry' in sys.argv


def call(path, body=None):
    key = os.environ.get('LEOKMEI_ADMIN_KEY', '')
    if not key:
        sys.exit('חסר LEOKMEI_ADMIN_KEY')
    data = None if body is None else json.dumps(body, ensure_ascii=False).encode('utf-8')
    rq = urllib.request.Request(API + path, data=data, method='POST' if body is not None else 'GET',
                                headers={'x-admin-key': key, 'content-type': 'application/json; charset=utf-8',
                                         'user-agent': 'leokmei-sakem-sync'})
    with urllib.request.urlopen(rq, timeout=60) as r:
        j = json.loads(r.read().decode('utf-8'))
    if not j.get('ok'):
        raise RuntimeError('%s: %s' % (path, j.get('error')))
    return j


def wjson(fp, obj):
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    tmp = fp + '.tmp'
    with io.open(tmp, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
        f.write('\n')
    os.replace(tmp, fp)


def main():
    st = {}
    if os.path.exists(STATE):
        st = json.load(io.open(STATE, encoding='utf-8'))
    imported = st.setdefault('imported', {})
    changed = 0

    # א. חבילות חדשות (וגם "נשלח" שאינו בריפו: סבב קודם סימן אותו ונכשל בדחיפה)
    srv0 = call('/sakem/jobs').get('items', [])
    lost = [x['jid'] for x in srv0 if x.get('st') == 'sent'
            and not os.path.exists(os.path.join(D, 'queue', x['jid'] + '.json'))]
    if lost:
        print('נשלחו ואינם בריפו - מורידים שוב:', ', '.join(lost))
    ex = call('/sakem/export' + ('?again=' + ','.join(lost) if lost else ''))['items']
    done = []
    for it in ex:
        jid = it['job']['jid']
        pk = it['packet']
        pk['job'] = it['job']
        pk['title'] = it['job'].get('title', '')
        fp = os.path.join(D, 'queue', jid + '.json')
        print('תור:', jid, it['job'].get('title', ''), len(pk.get('units', [])), 'יחידות')
        if not DRY:
            wjson(fp, pk)
            # עבודה שנכנסה מחדש (אותו פרק): ההצעות הישנות אינן תקפות
            old = os.path.join(D, 'out', jid + '.json')
            if os.path.exists(old):
                os.replace(old, os.path.join(D, 'out', jid + '.old.json'))
            imported.pop(jid, None)
        done.append(jid)
        changed += 1
    if done and not DRY:
        call('/sakem/exported', {'jids': done})

    # ב. הצעות מן הריפו לשרת (רק מה שהשתנה מאז הפעם הקודמת)
    # 29.10: רשימת העבודות בשרת היא רשומה אחת, ו"סכם" שנלחץ באותה שנייה דרס עדכון "מוכן לסקירה".
    # לכן בכל סבב משווים: עבודה שבריפו מתקדמת יותר מבשרת - מועלית שוב, גם כשהקובץ לא השתנה.
    srv = {x['jid']: x for x in call('/sakem/jobs').get('items', [])}
    od = os.path.join(D, 'out')
    for fn in sorted(os.listdir(od)) if os.path.isdir(od) else []:
        if not fn.endswith('.json') or fn.endswith('.old.json'):
            continue
        jid = fn[:-5]
        raw = io.open(os.path.join(od, fn), 'rb').read()
        hsh = hashlib.sha1(raw).hexdigest()[:16]
        if imported.get(jid) == hsh:
            j = srv.get(jid)
            if not j:
                continue
            o0 = json.loads(raw.decode('utf-8'))
            lag = (o0.get('status') == 'ready' and j.get('st') not in ('ready', 'done')) or \
                  (o0.get('status') != 'ready' and int(j.get('n') or 0) < int(o0.get('done') or 0))
            if not lag:
                continue
            print('  מצב שנדרס בשרת - מעלה שוב:', jid, j.get('st'), '->', o0.get('status'))
        out = json.loads(raw.decode('utf-8'))
        print('הצעות:', jid, out.get('status'), '%s/%s' % (out.get('done'), out.get('total')))
        if not DRY:
            r = call('/sakem/import', {'jid': jid, 'out': out})
            if r.get('skipped'):
                print('  (אין עבודה כזאת בשרת)')
        imported[jid] = hsh
        changed += 1

    # ג. הכרעות של פרקים שנסקרו
    dec = call('/sakem/decisions')['items']
    got = []
    for it in dec:
        jid = it['job']['jid']
        print('הכרעות:', jid, len(it.get('dec') or {}))
        if not DRY:
            wjson(os.path.join(D, 'decisions', jid + '.json'), it)
        got.append(jid)
        changed += 1
    if got and not DRY:
        call('/sakem/committed', {'jids': got})

    if not DRY:
        wjson(STATE, st)
    print('שינויים:', changed)


if __name__ == '__main__':
    main()
