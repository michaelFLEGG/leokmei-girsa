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


def call(path, body=None, method=None):
    key = os.environ.get('LEOKMEI_ADMIN_KEY', '')
    if not key:
        sys.exit('חסר LEOKMEI_ADMIN_KEY')
    data = None if body is None else json.dumps(body, ensure_ascii=False).encode('utf-8')
    rq = urllib.request.Request(API + path, data=data, method=method or ('POST' if body is not None else 'GET'),
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
        # פרומפט 17: הקובץ הזה נכנס לריפו הציבורי. גם אם שרת ישן שלח פירוש או חברותא - הם אינם נכתבים
        pk.pop('hv', None)
        for pg in pk.get('pages', []):
            pg.pop('p', None)
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

    # ד. תיקוני מנהל שהוכנו בריפו (6.11.2026): data/sakem/edits-put/<מסכת>-<שם>.json = {slug, edits:[...]}
    #    נכנסים לנקודת הקליטה כמו עריכה מן הדף (PUT /edits), ומשם לאתר ולוורד בלילה. רשומה שמפתחה כבר
    #    קיים שם אינה נדרסת - נאמרת ומדולגת. הקובץ עובר ל-done/ אחרי ההעלאה.
    ep = os.path.join(D, 'edits-put')
    for fn in sorted(os.listdir(ep)) if os.path.isdir(ep) else []:
        if not fn.endswith('.json'):
            continue
        fp = os.path.join(ep, fn)
        req = json.load(io.open(fp, encoding='utf-8'))
        slug = req.get('slug', '')
        cur = {e.get('k') for e in (call('/edits?slug=' + slug).get('doc') or {}).get('edits', [])}
        new = [e for e in req.get('edits', []) if e.get('k') and e['k'] not in cur]
        for e in req.get('edits', []):
            if e.get('k') in cur:
                print('  תיקון מנהל: המפתח כבר קיים בנקודת הקליטה, מדולג:', slug, e.get('k'))
        print('תיקוני מנהל:', fn, len(new), 'רשומות')
        if not DRY:
            if new:
                call('/edits', {'slug': slug, 'edits': new}, method='PUT')
            os.makedirs(os.path.join(ep, 'done'), exist_ok=True)
            os.replace(fp, os.path.join(ep, 'done', fn))
        changed += 1

    # ה. המקליט (פרומפט 28, 9.11.2026): כל עריכה של המנהל ב-data/edits נשמרת ב-data/sakem/learn/<מסכת>.jsonl
    #    לפני שהקליטה לוורד מרוקנת אותה, נספרת לדפוסים, ורשימת הכללים עולה לשרת לדף "מה סכם למד".
    #    "בטל כלל" שנלחץ בדף יורד קודם ונרשם בריפו - כלל מבוטל אינו מוצג עוד לסכם.
    lr = os.path.join(D, 'learn', 'rules.json')
    try:
        srv = call('/sakem/learn')
    except Exception as e:  # השרת עדיין בלי הנתיב - ממשיכים בלי הביטולים
        print('מה סכם למד: השרת לא ענה -', e)
        srv = {}
    if os.path.exists(lr) and srv.get('off'):
        R = json.load(io.open(lr, encoding='utf-8'))
        n = 0
        for r in R.get('rules', []):
            o = srv['off'].get(r.get('id'))
            if o is not None and bool(o.get('off')) != bool(r.get('off')):
                r['off'] = bool(o.get('off'))
                n += 1
        if n and not DRY:
            wjson(lr, R)
            changed += 1
        print('מה סכם למד: ביטולים מן הדף:', n)
    import subprocess
    for a in ((['patterns'],) if DRY else (['record'], ['patterns'])):
        rc = subprocess.run(['node', os.path.join(ROOT, 'tools', 'sakem', 'learn.mjs')] + a + (['--dry'] if DRY and a[0] == 'patterns' else []), cwd=ROOT)
        if rc.returncode:
            raise SystemExit('עצירה: המקליט נכשל (' + a[0] + ')')
    if os.path.exists(lr) and not DRY and srv:
        R = json.load(io.open(lr, encoding='utf-8'))
        mine = sorted((r.get('id'), bool(r.get('off')), r.get('text')) for r in R.get('rules', []))
        theirs = sorted((r.get('id'), bool(r.get('off')), r.get('text')) for r in (srv.get('rules') or []))
        if mine != theirs:
            call('/sakem/learn/put', {'rules': R.get('rules', [])})
            print('מה סכם למד: הרשימה עלתה לשרת,', len(R.get('rules', [])), 'כללים')

    if not DRY:
        wjson(STATE, st)
    print('שינויים:', changed)


if __name__ == '__main__':
    main()
