# -*- coding: utf-8 -*-
"""החוקר - רישום ידני ביומן הממצאים (בשימוש המוח הלילי).

  python tools/chokker/note.py add  --rule V01-vision --site leokmei --page bava-batra --text "..." [--sev high] [--ev sheet=print-003.jpg]
  python tools/chokker/note.py set  <מזהה> --status תוקן --why "commit abc123: ..."
  python tools/chokker/note.py ask  <מזהה> --q "השאלה" --a "צד א" --b "צד ב" --rec "ההמלצה שלי ולמה"
  python tools/chokker/note.py false <מזהה> --why "למה זה אינו תקלה; הבדיקה תוקנה ב-..."
מצבים: פתוח, תוקן, אומת, חזר, נעלם, לבעלים, הוכרע, כוזב.
"""
import os, sys, io, json, argparse, datetime, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(os.path.dirname(os.path.dirname(HERE)), 'data', 'chokker', 'findings.json')


def load():
    return json.load(io.open(DB, encoding='utf-8')) if os.path.exists(DB) else {'about': 'יומן הממצאים הקבוע של החוקר. לא מוחקים ממנו לעולם.', 'findings': {}}


def save(db):
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    json.dump(db, io.open(DB, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd')
    ap.add_argument('id', nargs='?')
    for k in ('rule', 'site', 'page', 'text', 'sev', 'ev', 'status', 'why', 'q', 'a', 'b', 'rec'):
        ap.add_argument('--' + k, default='')
    x = ap.parse_args()
    db = load(); F = db['findings']
    today = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=2))).date().isoformat()
    if x.cmd == 'add':
        k = hashlib.sha1(('%s|%s|%s|%s' % (x.rule, x.site, x.page, x.text[:90])).encode('utf-8')).hexdigest()[:12]
        F.setdefault(k, {'rule': x.rule, 'site': x.site, 'page': x.page, 'text': x.text[:300], 'first': today, 'status': 'פתוח',
                         'sev': x.sev or 'med', 'evidence': dict(e.split('=', 1) for e in x.ev.split(',') if '=' in e), 'scopes': ['מבט'],
                         'history': [[today, 'נמצא (מבט/מוח)']]})
        F[k]['last'] = today
        print(k)
    else:
        f = F[x.id]
        if x.cmd == 'set':
            f['status'] = x.status; f['history'].append([today, x.status + (': ' + x.why if x.why else '')])
        elif x.cmd == 'ask':
            f['status'] = 'לבעלים'; f['question'] = {'q': x.q, 'a': x.a, 'b': x.b, 'rec': x.rec, 'asked': today}
            f['history'].append([today, 'נשאל מיכאל'])
        elif x.cmd == 'false':
            f['status'] = 'כוזב'; f['history'].append([today, 'כוזב: ' + x.why])
        print(x.id, f['status'])
    save(db)


if __name__ == '__main__':
    main()
