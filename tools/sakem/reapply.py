# -*- coding: utf-8 -*-
"""reapply.py - החלה מחדש של קבלות סכם שנרשמו "התקבל" ואינן בנוסח החי (פרומפט 65, 19.11.2026).

הרשומות: data/sakem/decisions/<jid>.json (ההכרעה, ובעריכה - הנוסח הסופי) ו-data/sakem/out/<jid>.json (ההצעה).
לכל קטע נלקחת רק ההכרעה האחרונה על היחידות שלו: הכרעה מאוחרת יותר (באותה עבודה או בעבודה אחרת, כל סוג) גוברת,
וגם עריכה של המנהל בשכבה אחרי ההכרעה גוברת. לא ממציאים קבלה: רק accept / edit.
ההחלה עצמה בדף, במצב מנהל, באותו מסלול של "קבל" (skpAuto.reapply), ואחריה פרסום לשכבה החיה.

    python tools/sakem/reapply.py --slug sukkah [--dry] [--since 2026-11-01] --out report.json
"""
import argparse, glob, json, os, sys, time, datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
D = os.path.join(ROOT, 'data', 'sakem')
ap = argparse.ArgumentParser()
ap.add_argument('--slug', required=True)
ap.add_argument('--dry', action='store_true')
ap.add_argument('--since', default='2026-11-01', help='רק הכרעות מן התאריך הזה (שעון UTC)')
ap.add_argument('--out', default='reapply-report.json')
a = ap.parse_args()


def items_for(slug, since_ms):
    allx = []
    for f in sorted(glob.glob(os.path.join(D, 'decisions', slug + '-*.json'))):
        d = json.load(open(f, encoding='utf-8'))
        jid = d['job']['jid']
        of = os.path.join(D, 'out', jid + '.json')
        if not os.path.exists(of):
            continue
        O = {x['iid']: x for x in json.load(open(of, encoding='utf-8')).get('items', [])}
        log = {}
        for e in d.get('log', []):
            log[e['iid']] = e
        for iid, dc in d.get('dec', {}).items():
            it = O.get(iid)
            if not it or it.get('nochange'):
                continue
            text = it.get('text', '')
            if dc.get('act') == 'edit':
                text = (log.get(iid) or {}).get('final') or ''
            allx.append({'jid': jid, 'iid': iid, 'act': dc.get('act'), 't': dc.get('t') or 0, 'kind': it.get('kind', 'seg'),
                         'ids': it.get('ids') or [], 'orig': it.get('orig', ''), 'text': text,
                         'anchor': it.get('anchor'), 'gem': it.get('gem', ''), 'layers': it.get('layers') or [],
                         'title': d['job'].get('title', '')})
    out = []
    for x in allx:
        if x['act'] not in ('accept', 'edit') or x['t'] < since_ms or not x['text']:
            continue
        ids = set(x['ids'] + ([x['anchor']] if x.get('anchor') else []))
        later = [y for y in allx if y is not x and y['t'] > x['t'] and ids & set(y['ids'] + ([y['anchor']] if y.get('anchor') else []))]
        if later:
            continue
        out.append(x)
    return out


since = int(datetime.datetime.strptime(a.since, '%Y-%m-%d').replace(tzinfo=datetime.timezone.utc).timestamp() * 1000)
cand = items_for(a.slug, since)
print('מועמדים (הכרעה אחרונה, accept/edit):', len(cand))
rep = {'slug': a.slug, 'dry': a.dry, 'since': a.since, 'started': time.strftime('%Y-%m-%d %H:%M'), 'candidates': len(cand)}
if not cand:
    json.dump(rep, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1); sys.exit(0)
KEY = os.environ.get('LEOKMEI_ADMIN_KEY', '')
if not KEY:
    sys.exit('עצירה: אין מפתח מנהל')
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=os.environ.get('PRINT_CHROMIUM') or None)
    c = b.new_context(viewport={'width': 1400, 'height': 900})
    c.add_init_script("localStorage.setItem('lg-admin','1');localStorage.setItem('lg-adm'," + json.dumps(KEY) + ");")
    pg = c.new_page()
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:200]))
    pg.on('dialog', lambda d: d.accept())
    pg.goto('https://leokmei.com/' + a.slug + '.html', wait_until='networkidle', timeout=180000)
    pg.wait_for_function("()=>!!window.skpAuto&&!!skpAuto.reapply&&!!window.__LGSYNC", timeout=180000)
    pg.wait_for_timeout(2000)
    res = pg.evaluate("([l,d])=>skpAuto.reapply(l,d)", [cand, a.dry])
    if not a.dry:
        pg.wait_for_timeout(3000)
        # הפרסום שהקבלה המרוכזת מפעילה (pubNow) עשוי עוד לרוץ: מחכים עד שאין ממתינים (עד דקה וחצי)
        for _ in range(30):
            pg.evaluate("async()=>{if(typeof pubPending==='function'&&pubPending()&&!PUBBUSY)await pubNow(1)}")
            pg.wait_for_timeout(3000)
            if pg.evaluate("()=>typeof pubPending==='function'?pubPending():-1") == 0:
                break
        rep['pending_after'] = pg.evaluate("()=>typeof pubPending==='function'?pubPending():-1")
    by = {(x['jid'], x['iid']): x for x in cand}
    for r in res:
        x = by.get((r['jid'], r['iid'])) or {}
        r['when'] = datetime.datetime.utcfromtimestamp((x.get('t') or 0) / 1000).strftime('%d.%m %H:%M')
        r['title'] = x.get('title', '')
        if r['st'] in ('would', 'applied', 'changed', 'bad'):
            r['orig'] = x.get('orig', ''); r['text'] = x.get('text', '')
    rep['items'] = res
    cnt = {}
    for r in res:
        cnt[r['st']] = cnt.get(r['st'], 0) + 1
    rep['count'] = cnt
    rep['errors'] = errs[:20]
    b.close()
json.dump(rep, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ספירה:', json.dumps(rep.get('count'), ensure_ascii=False), ' שגיאות דף:', len(rep.get('errors', [])))
if not a.dry and (rep.get('pending_after') or 0) > 0:
    sys.exit('עצירה: העריכות לא פורסמו לשכבה החיה')
