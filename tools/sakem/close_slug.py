# -*- coding: utf-8 -*-
"""close_slug.py - סגירת כל הצעות סכם של מסכת עד הסוף (פרומפט 63, 18.11.2026).

מיכאל (ערכין): "ביקשתי שפשוט תקבל את כל ההצעות בערכין, וממילא שזה לא יופיע לי במוכן לסקירה".
לכל עבודה של המסכת שיש לה הצעות (מוכנה, נסקרה חלקית, או שהדף מסמן "הכל הוכרע" והשרת לא): skpAuto.closeAll -
כבר בנוסח: accept · אינו מאותר: stale · המנהל ערך אחריו: keep (עריכתו גוברת) · השאר: מוחל ונרשם accept.
העריכות מתפרסמות לשכבה החיה (pubNow). עבודה שעדיין ממתינה לסכם (wait) - נסגרת בהרצה הבאה, אחרי שהצעותיה עולות.
מסכתות שב-data/sakem/auto-accept.json נסגרות כך אוטומטית בכל סנכרון (sakem-sync.yml).

    python tools/sakem/close_slug.py --slug arakhin [--dry] --out report.json
"""
import argparse, json, os, sys, time
from playwright.sync_api import sync_playwright

ap = argparse.ArgumentParser()
ap.add_argument('--slug', required=True)
ap.add_argument('--dry', action='store_true', help='רק ספירה')
ap.add_argument('--out', default='close-report.json')
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
    pg.wait_for_function("()=>!!window.skpAuto&&!!skpAuto.closeAll", timeout=120000)
    for k in range(30):
        if pg.evaluate("()=>!!window.__LGSYNC"):
            break
        pg.wait_for_timeout(2000)
    jobs = pg.evaluate("""async()=>{const r=await fetch(SUGGEST_API+'/sakem/jobs?slug='+SLUG,{headers:{'x-admin-key':localStorage.getItem('lg-adm')}});
      const j=await r.json();return (j.items||[])}""")
    rep['all'] = [x['jid'] + ':' + x['st'] + ':' + str(x.get('dec', 0)) + '/' + str(x.get('shown', 0)) for x in jobs]
    print('עבודות:', rep['all'])
    todo = [x['jid'] for x in jobs if x['st'] != 'wait' and (x['st'] == 'ready' or (x.get('dec') or 0) < (x.get('shown') or 0))]
    for jid in todo:
        r = {'jid': jid}
        try:
            if a.dry:
                r['dry'] = pg.evaluate("""async j=>{const o=await (await fetch(SUGGEST_API+'/sakem/out?jid='+encodeURIComponent(j),{headers:{'x-admin-key':localStorage.getItem('lg-adm')}})).json();const d=o.dec||{};
                  return (o.out.items||[]).filter(x=>!x.nochange&&!d[x.iid]).length}""", jid)
            else:
                r.update(pg.evaluate("j=>skpAuto.closeAll(j)", jid))
                pg.evaluate("async()=>{if(typeof pubPending==='function'&&pubPending())await pubNow(1)}")
                pg.wait_for_timeout(1500)
                r['pending_after'] = pg.evaluate("()=>typeof pubPending==='function'?pubPending():-1")
        except Exception as e:
            r['error'] = str(e)[:300]
        print(json.dumps(r, ensure_ascii=False))
        rep['jobs'].append(r)
    jobs2 = pg.evaluate("""async()=>{const r=await fetch(SUGGEST_API+'/sakem/jobs?slug='+SLUG,{headers:{'x-admin-key':localStorage.getItem('lg-adm')}});
      const j=await r.json();return (j.items||[])}""")
    rep['after'] = [x['jid'] + ':' + x['st'] + ':' + str(x.get('dec', 0)) + '/' + str(x.get('shown', 0)) for x in jobs2]
    rep['ready_after'] = [x['jid'] for x in jobs2 if x['st'] == 'ready']
    print('אחרי:', rep['after'])
    rep['errors'] = errs[:20]
    b.close()
json.dump(rep, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
bad = [j['jid'] for j in rep['jobs'] if j.get('error') or (j.get('after') or 0) != 0 or (j.get('pending_after') or 0) > 0]
if bad and not a.dry:
    sys.exit('עצירה: עבודות שלא נסגרו עד הסוף: ' + ', '.join(bad))
print('נסגרו %d עבודות. מוכנות לסקירה שנשארו: %s' % (len(rep['jobs']), rep['ready_after'] or 'אין'))
