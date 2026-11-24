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
    # 21.11.2026: התיקון הסמנטי (tools/semantic_io.py) - "dump:<מסכת>" או "file:<נתיב>"
    sem = [s for s in slugs if s.startswith('dump:') or s.startswith('file:')]
    if sem:
        import subprocess
        for s in sem:
            subprocess.run([sys.executable, os.path.join(HERE, 'tools', 'semantic_io.py'), s], check=True)
        sys.exit(0)
    if not slugs:
        slugs = sorted(f[:-5] for f in os.listdir(os.path.join(HERE, 'data', 'edits')) if f.endswith('.json'))
    bad = 0
    # פרומפט 49 חלק 0 (17.11.2026): "keep:<מסכת>" - רק רשומות השחזור של מרשם "שורה שהתארכה"
    # (data/overflow/keep/<מסכת>.json), בלי שאר המאגר: שכבת המאגר עשויה להחזיק עריכות שנמחקו בשרת בכוונה.
    # פרומפט 53: "auto:<מסכת>" - רשומות האיחוי האוטומטי שממתינות (data/overflow/auto/<מסכת>.json)
    autos = [s[5:] for s in slugs if s.startswith('auto:')]
    if autos:
        sys.path.insert(0, os.path.join(HERE, 'tools', 'overflow'))
        import auto as AUTO
        for slug in autos:
            bad += AUTO.push(slug)
        slugs = [s for s in slugs if not s.startswith('auto:')]
        if not slugs:
            sys.exit(1 if bad else 0)
    # פרומפט 87 (23.11.2026): "p87:<מסכת>" - רק רשומות פרומפט 87 שבמאגר (שדה p87), כעריכות מנהל רגילות.
    # רשומה על שורה שנוצרה בפיצול בשרת אינה נמצאת בבנייה, ולכן חייבת להגיע ל-/live. מפתחותיהן קפואים וחדשים - אינן דורסות דבר.
    # פרומפט 91 (24.11.2026): אותו מסלול לכל תג פרומפט ("p91:<מסכת>" - רק רשומות עם שדה p91)
    import re as _re
    p87s = [(m.group(1), m.group(2)) for m in (_re.match(r'^(p\d+):(.+)$', s) for s in slugs) if m]
    slugs = [s for s in slugs if not _re.match(r'^p\d+:', s)]
    if p87s:
        for tag, slug in p87s:
            rep = json.load(open(os.path.join(HERE, 'data', 'edits', slug + '.json'), encoding='utf-8'))
            eds = [e for e in rep.get('edits') or [] if e.get(tag)]
            if not eds:
                continue
            body = json.dumps({'slug': slug, 'edits': eds, 'sty': rep.get('sty')}, ensure_ascii=False).encode('utf-8')
            req = urllib.request.Request(API + '/edits', data=body, method='PUT', headers={
                'content-type': 'application/json; charset=utf-8', 'x-admin-key': key,
                'user-agent': 'Mozilla/5.0 leokmei-push/1.0'})
            try:
                with urllib.request.urlopen(req, timeout=180) as r:
                    d = json.loads(r.read().decode('utf-8'))
                print(slug, tag, 'OK', 'sent', len(eds), 'server', len((d.get('doc') or {}).get('edits') or []))
            except urllib.error.HTTPError as e:
                bad += 1
                print(slug, tag, 'HTTP', e.code, e.read().decode('utf-8', 'replace')[:1000])
            except Exception as e:
                bad += 1
                print(slug, tag, 'FAIL', type(e).__name__, e)
        slugs = [s for s in slugs if not s.startswith('p87:')]
        if not slugs:
            sys.exit(1 if bad else 0)
    keeps = [s[5:] for s in slugs if s.startswith('keep:')]
    if keeps:
        sys.path.insert(0, os.path.join(HERE, 'tools', 'overflow'))
        import keep as KEEP
        for slug in keeps:
            bad += KEEP.push(slug)
        slugs = [s for s in slugs if not s.startswith('keep:')]
        if not slugs:
            sys.exit(1 if bad else 0)
    for slug in slugs:
        rep = json.load(open(os.path.join(HERE, 'data', 'edits', slug + '.json'), encoding='utf-8'))
        eds = rep.get('edits') or []
        # עריכת מבנה (פיצול/איחוד) נשמרת במאגר בלי מפתח, והשרת מדלג על עריכה בלי מפתח.
        # המפתח זהה לזה שהעורך נותן לה (edKeys בדף): 's' + הזמן.
        for e in eds:
            if not e.get('k') and e.get('op') == 'struct' and e.get('t'):
                e['k'] = 's' + str(e['t'])
        body = json.dumps({'slug': slug, 'edits': eds, 'sty': rep.get('sty')},
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
