# -*- coding: utf-8 -*-
"""פרומפט 87 - כמעט-כפולות לעיון: הצעת מחיקה בתור ההצעות באתר (כמו "הצע תיקון"), עם שתי השורות זו מול זו.
    python _work/p87/suggest.py [--send]
"""
import os, sys, json, io, time, random, string, urllib.request, urllib.error

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
API = 'https://leokmei-suggest.m7654301.workers.dev'
sys.path.insert(0, os.path.join(HERE, 'tools'))
import cloud_word as C

rnd = lambda n: ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(n))
plan = json.load(io.open(os.path.join(HERE, '_work', 'p87', 'out', 'plan.json'), encoding='utf-8'))
pid, pt = rnd(14), rnd(32)
SEND = '--send' in sys.argv
out = []
t = int(time.time() * 1000)
for slug, R in sorted(plan['report'].items()):
    grp = rnd(10)
    for x in R.get('near') or []:
        t += 1
        a_ek, a_t = x['a']
        b_ek, b_t = x['b']
        note = '[מחיקה] כמעט כפולה (%s). השורה הקודמת: «%s» · השורה הזאת: «%s»' % (x['why'], a_t[:140], b_t[:140])
        edit = {'k': '%s~%d' % (b_ek, t), 'bt': b_t, 'bh': x['bh'], 'was': b_t, 'wasH': x['bh'], 'now': '', 'nowH': '',
                'wasP': '', 'daf': x['daf'], 'ctx': x['ctx'], 't': t}
        rec = {'slug': slug, 'masechet': C.masechet_of_slug(slug), 'daf': x['daf'], 'uid': x['uid'], 'k': edit['k'],
               'ctx': x['ctx'], 'was': b_t[:200], 'note': note[:600], 'name': 'פרומפט 87 (ענן)', 'type': 'nusach', 'sk': 'text',
               'edit': edit, 'pid': pid, 'pt': pt, 'grp': grp, 'hp': '', 't': t, 'sent': 0, 'ek': edit['k']}
        out.append(rec)
print('הצעות:', len(out))
if SEND:
    ok = bad = 0
    for rec in out:
        for attempt in range(6):
            req = urllib.request.Request(API + '/suggest', data=json.dumps(rec, ensure_ascii=False).encode('utf-8'), method='POST',
                                         headers={'content-type': 'application/json; charset=utf-8', 'user-agent': 'Mozilla/5.0 leokmei-p87/1.0'})
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    j = json.loads(r.read().decode('utf-8'))
                if j.get('ok'):
                    rec['id'] = j.get('id'); ok += 1; break
                print('לא התקבל', rec['slug'], rec['daf'], j); bad += 1; break
            except urllib.error.HTTPError as e:
                body = e.read().decode('utf-8', 'replace')
                if 'מהירה' in body or e.code == 429:
                    time.sleep(4 + attempt * 3); continue
                print('HTTP', e.code, body[:200]); bad += 1; break
            except Exception as e:
                time.sleep(3); err = e
        time.sleep(1.2)
    print('נשלחו', ok, 'נכשלו', bad)
    io.open(os.path.join(HERE, '_work', 'p87', 'out', 'suggested.json'), 'w', encoding='utf-8').write(
        json.dumps([{'slug': r['slug'], 'daf': r['daf'], 'id': r.get('id'), 'note': r['note']} for r in out], ensure_ascii=False, indent=1))
