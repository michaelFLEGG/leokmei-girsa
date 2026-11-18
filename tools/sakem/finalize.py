# -*- coding: utf-8 -*-
"""finalize.py - אימות וסגירת התור של סקור סכם (18.11.2026).
מיכאל: "תוודא שהכל מתקבל עם הגירסא האחרונה ורק אחרי שאתה רואה שהכל התקבל תעדכן את התור".
לכל עבודה מוכנה במסכת: כל הצעה פתוחה נבדקת מול הנוסח החי. הצעה שכבר יושבת בנוסח - ההכרעה accept נרשמת בשרת
(אחת אחת, עם ניסיון חוזר). הצעה שאינה בנוסח - נשארת פתוחה ונרשמת בדוח. בנוסף: שורות כפולות סמוכות בדף.
    python tools/sakem/finalize.py --slug shabbat [--dry] --out report.json
"""
import argparse, json, os, sys, time
from playwright.sync_api import sync_playwright
ap = argparse.ArgumentParser()
ap.add_argument('--slug', default='shabbat')
ap.add_argument('--dry', action='store_true')
ap.add_argument('--out', default='finalize-report.json')
a = ap.parse_args()
KEY = os.environ.get('LEOKMEI_ADMIN_KEY', '')
if not KEY:
    sys.exit('עצירה: אין מפתח מנהל')
rep = {'slug': a.slug, 'jobs': [], 'started': time.strftime('%Y-%m-%d %H:%M')}
with sync_playwright() as p:
    b = p.chromium.launch()
    c = b.new_context(viewport={'width': 1400, 'height': 900})
    c.add_init_script("localStorage.setItem('lg-admin','1');localStorage.setItem('lg-adm'," + json.dumps(KEY) + ");")
    pg = c.new_page()
    pg.on('dialog', lambda d: d.accept())
    pg.goto('https://leokmei.com/' + a.slug + '.html', wait_until='networkidle', timeout=180000)
    pg.wait_for_function("()=>!!window.skpAuto&&!!skpAuto.verify", timeout=120000)
    try:
        pg.wait_for_function("()=>window.skpAuto.jobs().length>0", timeout=60000)
    except Exception:
        pass
    rep['dups'] = pg.evaluate("()=>skpAuto.dups()")
    print('כפולות:', json.dumps(rep['dups'], ensure_ascii=False))
    jobs = [j['jid'] for j in pg.evaluate("()=>skpAuto.jobs()") if j['st'] == 'ready']
    print('עבודות:', jobs)
    tot_in = tot_out = 0
    for jid in jobs:
        r = {'jid': jid}
        try:
            pg.evaluate("j=>skpAuto.open(j)", jid)
            pg.wait_for_function("j=>{const s=skpAuto.state();return s&&s.jid===j}", arg=jid, timeout=180000)
            pg.wait_for_timeout(1500)
            v = pg.evaluate("()=>skpAuto.verify()") or []
            ins = [x['iid'] for x in v if x['in']]
            outs = [x for x in v if not x['in']]
            r['open'] = len(v); r['in'] = len(ins); r['not_in'] = outs
            tot_in += len(ins); tot_out += len(outs)
            if ins and not a.dry:
                r['close'] = pg.evaluate("ids=>skpAuto.close(ids)", ins)
            r['open_after'] = pg.evaluate("()=>skpAuto.state().open")
        except Exception as e:
            r['error'] = str(e)[:300]
        print(json.dumps(r, ensure_ascii=False))
        rep['jobs'].append(r)
    print('סה"כ כבר בנוסח ונסגרו: %d, אינן בנוסח: %d, כפולות: %d' % (tot_in, tot_out, len(rep['dups'])))
    b.close()
json.dump(rep, open(a.out, 'w'), ensure_ascii=False, indent=1)
