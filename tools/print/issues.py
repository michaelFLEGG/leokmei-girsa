# -*- coding: utf-8 -*-
"""קורא את הצעות המנהל מלוח תקלות ההדפסה (הכלל הקבוע: הוורקר קורא את ההצעות הפתוחות לפני עבודה על המנוע).
מפתח המנהל נקרא מקובץ המפתח המקומי דרך tools/bakara/_api.py בלבד (לעולם לא נכתב לקובץ במאגר).
הרצה: uv run python tools/print/issues.py            - רשימת תקלות פתוחות עם הצעות
      uv run python tools/print/issues.py --done <id> "מה נעשה"   - סימון "בוצע" (נשמר בלוח)"""
import json, os, sys, urllib.request

API = 'https://leokmei-print.m7654301.workers.dev'
HERE = os.path.dirname(os.path.abspath(__file__))


def admin_key():
    sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'bakara'))
    import _api  # noqa
    for n in ('admin_key', 'ADMIN_KEY', 'get_key', 'KEY'):
        v = getattr(_api, n, None)
        if callable(v):
            return v()
        if isinstance(v, str) and v:
            return v
    raise SystemExit('מפתח המנהל לא נמצא ב-tools/bakara/_api.py')


def call(path, body=None):
    req = urllib.request.Request(API + path, headers={'x-admin-key': admin_key(), 'content-type': 'application/json'},
                                 data=(json.dumps(body).encode('utf-8') if body is not None else None),
                                 method='POST' if body is not None else 'GET')
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode('utf-8'))


def main():
    a = sys.argv[1:]
    if a and a[0] == '--done' and len(a) >= 3:
        print(call('/issues', {'id': a[1], 'done': a[2]}))
        return
    j = call('/issues')
    for it in j.get('issues', []):
        print('%s | %s | %s | דף %s | עמוד %s | %s' % (it['id'], it['m'], it['type'], it.get('daf', ''), it.get('page', ''), it.get('detail', '')))
        if it.get('note'):
            print('    הצעת המנהל: ' + it['note'])
    print('סה"כ פתוחות: %d' % len(j.get('issues', [])))


if __name__ == '__main__':
    main()
