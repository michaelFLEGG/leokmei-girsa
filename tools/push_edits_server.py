# -*- coding: utf-8 -*-
"""push_edits_server.py - מעלה לנקודת הקליטה את העריכות שנשמרו רק במאגר
(data/edits/<מסכת>.json), ב-PUT /edits. השרת מאחד לפי מפתח וזמן (החדש גובר),
ולכן ההעלאה בטוחה ואינה דורסת עריכה חדשה יותר שבשרת.
נוסף 7.11.2026, כשהשרת הפסיק לקבל פרסום מן הדף (docs/דחוף-שרת-העריכות-...).
מדפיס את תשובת השרת המלאה בכישלון, כדי שהשגיאה המדויקת תירשם ביומן.
הרצה: SLUGS="sukkah ketubot" python tools/push_edits_server.py
"""
import os, sys, json, time, urllib.request, urllib.error

API = 'https://leokmei-suggest.m7654301.workers.dev'
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    key = os.environ.get('LEOKMEI_ADMIN_KEY', '').strip()
    if not key:
        sys.exit('אין מפתח מנהל (LEOKMEI_ADMIN_KEY)')
    slugs = (os.environ.get('SLUGS') or '').split()
    if not slugs:
        slugs = sorted(f[:-5] for f in os.listdir(os.path.join(HERE, 'data', 'edits')) if f.endswith('.json'))
    bad = 0
    for slug in slugs:
        rep = json.load(open(os.path.join(HERE, 'data', 'edits', slug + '.json'), encoding='utf-8'))
        body = json.dumps({'slug': slug, 'edits': rep.get('edits') or [], 'sty': rep.get('sty')},
                          ensure_ascii=False).encode('utf-8')
        req = urllib.request.Request(API + '/edits', data=body, method='PUT', headers={
            'content-type': 'application/json; charset=utf-8', 'x-admin-key': key,
            'user-agent': 'Mozilla/5.0 leokmei-push/1.0'})
        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                d = json.loads(r.read().decode('utf-8'))
            doc = d.get('doc') or {}
            print(slug, 'OK', 'sent', len(rep.get('edits') or []), 'server', len(doc.get('edits') or []),
                  'doc.t', doc.get('t'), 'bytes', len(body), 'sec', round(time.time() - t0, 1))
        except urllib.error.HTTPError as e:
            bad += 1
            print(slug, 'HTTP', e.code, e.read().decode('utf-8', 'replace')[:2000], 'bytes', len(body),
                  'sec', round(time.time() - t0, 1))
        except Exception as e:
            bad += 1
            print(slug, 'FAIL', type(e).__name__, e, 'sec', round(time.time() - t0, 1))
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
