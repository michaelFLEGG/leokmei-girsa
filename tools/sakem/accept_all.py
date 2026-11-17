# -*- coding: utf-8 -*-
"""accept_all.py - "קבל את כל הנותרים בפרק" לכל עבודות סכם של מסכת, דרך הדף עצמו (פרומפט 56 ד1, 17.11.2026).

מיכאל: "לקבל את כל הצעות סקור סכם שממתינות בכל פרקי מסכת שבת".
אותו מסלול בדיוק של הכפתור במצב מנהל: הדף נפתח בדפדפן עם מפתח המנהל (LEOKMEI_ADMIN_KEY, רק בפעולת גיטהאב),
כל עבודה נפתחת לסקירה (skpOpen), "קבל את כל הנותרים בפרק" (skpAll) מחיל במנה אחת, ההכרעות נרשמות accept
(כמו בלחיצה, כדי שהלמידה תעבוד), והעריכות מתפרסמות לשכבה החיה (pubNow). קטע שנערך בינתיים או שאינו מתאים לנוסח
החי - לא מוחל ונרשם בדוח.

    python tools/sakem/accept_all.py --slug shabbat [--jobs shabbat-p1,shabbat-p2] [--dry] --out report.json
"""
import argparse, json, os, sys, time
from playwright.sync_api import sync_playwright

ap = argparse.ArgumentParser()
ap.add_argument('--slug', default='shabbat')
ap.add_argument('--jobs', default='', help='רשימה מופרדת בפסיקים. ריק = כל העבודות המוכנות של המסכת')
ap.add_argument('--dry', action='store_true', help='רק פתיחה וספירה, בלי קבלה')
ap.add_argument('--out', default='accept-report.json')
a = ap.parse_args()
KEY = os.environ.get('LEOKMEI_ADMIN_KEY', '')
if not KEY:
    sys.exit('עצירה: אין מפתח מנהל')
rep = {'slug': a.slug, 'jobs': [], 'started': time.strftime('%Y-%m-%d %H:%M')}
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=os.environ.get('PRINT_CHROMIUM') or None)
    c = b.new_context(viewport={'width': 1400, 'height': 900})
    c.add_init_script("localStorage.setItem('lg-admin','1');localStorage.setItem('lg-adm'," + json.dumps(KEY) + ");")
    pg = c.new_page()
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:200]))
    pg.on('dialog', lambda d: d.accept())
    pg.goto('https://leokmei.com/' + a.slug + '.html', wait_until='networkidle', timeout=180000)
    pg.wait_for_function("()=>window.skpAuto&&window.skpAuto.jobs().length>0", timeout=120000)
    jobs = pg.evaluate("()=>skpAuto.jobs()")
    want = [x for x in a.jobs.split(',') if x] or [j['jid'] for j in jobs if j['st'] in ('ready',)]
    print('עבודות:', want)
    for jid in want:
        r = {'jid': jid}
        try:
            pg.evaluate("j=>skpAuto.open(j)", jid)
            pg.wait_for_function("j=>{const s=skpAuto.state();return s&&s.jid===j}", arg=jid, timeout=180000)
            pg.wait_for_timeout(1500)
            st = pg.evaluate("()=>skpAuto.state()")
            r.update(st or {})
            if not a.dry and st and st.get('open'):
                res = pg.evaluate("()=>skpAuto.all()")
                r['result'] = res
                pg.wait_for_timeout(2500)
            pg.evaluate("async()=>{if(typeof pubPending==='function'&&pubPending())await pubNow(1)}")
            pg.wait_for_timeout(2000)
            r['pending_after'] = pg.evaluate("()=>typeof pubPending==='function'?pubPending():-1")
        except Exception as e:
            r['error'] = str(e)[:300]
        print(json.dumps(r, ensure_ascii=False))
        rep['jobs'].append(r)
    rep['errors'] = errs[:20]
    b.close()
json.dump(rep, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
tot = sum(((j.get('result') or {}).get('ok') or 0) for j in rep['jobs'])
skp = sum(((j.get('result') or {}).get('skip') or 0) for j in rep['jobs'])
print('סה"כ התקבלו %d, נשארו %d. שגיאות דף: %d' % (tot, skp, len(errs)))
bad = [j['jid'] for j in rep['jobs'] if j.get('error') or (j.get('pending_after') or 0) > 0]
if bad:
    sys.exit('עצירה: עבודות שלא הושלמו או שלא פורסמו: ' + ', '.join(bad))
