# -*- coding: utf-8 -*-
"""insert_adds.py - השלמת קטעי גמרא חסרים בנוסח החי (פרומפט 63, 18.11.2026).

מיכאל (ערכין): "היכן שחסר קטע לשיטתך מהגמרא - פשוט תוסיף ותייצר סיכום של לאוקמי גירסא".
הרישום: data/sakem/adds/<מסכת>.json - רשימה, לכל הוספה: id (<מסכת>-p<פרק>-add-<n>), perek, daf, after (מזהה היחידה
שאחריה), anchor (נוסח היחידה כשנכתבה ההוספה), gem (לשון הגמרא בקצרה), why, text (בפורמט הביניים).
הדף נפתח במצב מנהל (LEOKMEI_ADMIN_KEY, רק בפעולת גיטהאב), skpAuto.insert מחיל במסלול ההשלמה של סכם, והעריכות
מתפרסמות לשכבה החיה. הוספה שכבר בדף מדולגת. הרישום נשאר: אפשר לבטל הוספה אחת, וסכם לומד ממנה.

    python tools/sakem/insert_adds.py --slug arakhin [--only arakhin-p3-add-1,...] [--dry] --out report.json
"""
import argparse, json, os, sys, time
from playwright.sync_api import sync_playwright

ap = argparse.ArgumentParser()
ap.add_argument('--slug', required=True)
ap.add_argument('--only', default='')
ap.add_argument('--dry', action='store_true')
ap.add_argument('--out', default='adds-report.json')
a = ap.parse_args()
KEY = os.environ.get('LEOKMEI_ADMIN_KEY', '')
if not KEY:
    sys.exit('עצירה: אין מפתח מנהל')
src = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'sakem', 'adds', a.slug + '.json')
adds = json.load(open(src, encoding='utf-8'))
if a.only:
    want = set(a.only.split(','))
    adds = [x for x in adds if x['id'] in want]
rep = {'slug': a.slug, 'n': len(adds), 'started': time.strftime('%Y-%m-%d %H:%M')}
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=os.environ.get('PRINT_CHROMIUM') or None)
    c = b.new_context(viewport={'width': 1400, 'height': 900})
    c.add_init_script("localStorage.setItem('lg-admin','1');localStorage.setItem('lg-adm'," + json.dumps(KEY) + ");")
    pg = c.new_page()
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:200]))
    pg.on('dialog', lambda d: d.accept())
    pg.goto('https://leokmei.com/' + a.slug + '.html', wait_until='networkidle', timeout=180000)
    pg.wait_for_function("()=>!!window.skpAuto&&!!skpAuto.insert", timeout=120000)
    for k in range(30):
        if pg.evaluate("()=>!!window.__LGSYNC"):
            break
        pg.wait_for_timeout(2000)
    if a.dry:
        rep['res'] = [{'id': x['id'], 'dry': 1} for x in adds]
    else:
        rep['res'] = pg.evaluate("l=>skpAuto.insert(l)", adds)
        rep['pending_after'] = pg.evaluate("""async()=>{if(typeof pubPending!=='function')return -1;
          for(let k=0;k<40&&pubPending();k++){try{await pubNow(1)}catch(e){}if(pubPending())await new Promise(r=>setTimeout(r,3000))}
          return pubPending()}""")
    rep['errors'] = errs[:20]
    b.close()
json.dump(rep, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for r in rep['res']:
    print(json.dumps(r, ensure_ascii=False))
bad = [r['id'] for r in rep['res'] if r.get('st') == 'bad']
print('הוחלו %d, כבר בדף %d, לא הוחלו %d, ממתין לפרסום %s' % (sum(r.get('st') == 'ok' for r in rep['res']),
      sum(r.get('st') == 'already' for r in rep['res']), len(bad), rep.get('pending_after')))
if bad or (rep.get('pending_after') or 0) > 0:
    sys.exit('עצירה: ' + ', '.join(bad))
