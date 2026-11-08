# -*- coding: utf-8 -*-
"""דפדפן בדיקה לפרומפט 27: האתר החי לקריאה בלבד, mas.js מקומי, כל כתיבה חסומה ונרשמת.
אותו עיקרון כמו p24/probe.py, ובנוסף:
  - דף לבחירה (--page bava-batra.html)
  - תשובות מדומות לנתיבי ה-Worker (--fake '/sakem/out=קובץ.json' ...), כדי לפתוח סקירה בלי לגעת בשרת
  - "וו" לבדיקה: הפונקציות הפנימיות של סכם נחשפות ב-window.__p27 (רק בעותק הבדיקה, לא בקוד המקור)
probe.py <mas.js> <width> <scenario.py> [--page P] [--fake path=file ...] [--h H]"""
import sys, io, json, os, argparse
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
ap = argparse.ArgumentParser()
ap.add_argument('mas'); ap.add_argument('width', type=int); ap.add_argument('scenario')
ap.add_argument('--page', default='bava-batra.html'); ap.add_argument('--hash', default='')
ap.add_argument('--fake', action='append', default=[]); ap.add_argument('--h', type=int, default=800)
ap.add_argument('--mobile', action='store_true'); ap.add_argument('--css', default='')
a = ap.parse_args()
BLOCKED = []
FAKE = {}
for f in a.fake:
    k, v = f.split('=', 1); FAKE[k] = io.open(v, encoding='utf-8').read()
HOOK = ("window.__p27={get SKP(){return SKP},get SKM(){return SKM},skpOpen:(...a)=>skpOpen(...a),skpAccept:(...a)=>skpAccept(...a),"
        "skpEditOn:()=>skpEditOn(),skpApplyOne:(...a)=>skpApplyOne(...a),skmApply:(...a)=>skmApply(...a),skmSame:(...a)=>skmSame(...a),"
        "skmUnits:(...a)=>skmUnits(...a),skmReadBack:(g)=>skmReadBack(g),skpShow:()=>skpShow(),skpMove:(d)=>skpMove(d),"
        "skpPacket:(...a)=>skpPacket(...a),skmInter:(...a)=>skmInter(...a),get SEC(){return SEC},get ED(){return ED},get D(){return D},render:(n)=>render(n),flatU:()=>flatU()};")
def seal(route):
    rq = route.request
    for k, v in FAKE.items():
        # "PUT:<נתיב>" - כתיבה שנחסמת אך מחזירה תשובה מדומה (למשל סנכרון העריכות של המנהל, שמחזיר את המסמך)
        if k.startswith('PUT:') and k[4:] in rq.url and rq.method.upper() == 'PUT':
            BLOCKED.append('PUT ' + rq.url.split('?')[0] + ' (faked)')
            return route.fulfill(status=200, content_type='application/json; charset=utf-8', body=v)
        if k in rq.url and rq.method.upper() == 'GET':
            return route.fulfill(status=200, content_type='application/json; charset=utf-8', body=v)
    if rq.method.upper() not in ('GET', 'HEAD', 'OPTIONS'):
        BLOCKED.append(rq.method + ' ' + rq.url.split('?')[0])
        return route.fulfill(status=200, content_type='application/json', body='{"ok":true,"doc":{"edits":[]}}')
    if '127.0.0.1:8760' in rq.url or 'localhost:8760' in rq.url:
        BLOCKED.append('bridge ' + rq.url); return route.fulfill(status=200, body='{}')
    if '.workers.dev' in rq.url:
        return route.fulfill(status=200, content_type='application/json', body='{}')
    return route.continue_()
with sync_playwright() as pw:
    br = pw.chromium.launch()
    kw = dict(viewport={'width': a.width, 'height': a.h}, locale='he-IL', service_workers='block')
    if a.mobile:
        kw.update(is_mobile=True, has_touch=True, device_scale_factor=2)
    ctx = br.new_context(**kw)
    ctx.route('**/*', seal)
    if a.mas != '-':
        body = io.open(a.mas, encoding='utf-8').read()
        # הוו נכנס מיד אחרי הגדרת skpPanel הגלובלית - באותו תחום שבו חיות פונקציות סכם
        assert 'window.skpPanel=skpPanel;' in body, 'hook anchor missing'
        body = body.replace('window.skpPanel=skpPanel;', 'window.skpPanel=skpPanel;' + HOOK, 1).encode('utf-8')
        ctx.route('**/mas.js*', lambda r: r.fulfill(status=200, content_type='application/javascript; charset=utf-8', body=body))
    ctx.add_init_script("try{localStorage.setItem('lg-admin','1');localStorage.setItem('lg-adm','TEST-LOCAL-TOKEN')}catch(e){}")
    pg = ctx.new_page()
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:300]))
    pg.goto('https://leokmei.com/' + a.page + ('#' + a.hash if a.hash else ''), wait_until='load', timeout=120000)
    pg.wait_for_timeout(2500)
    if a.css:
        pg.add_style_tag(content=io.open(a.css, encoding='utf-8').read())
    ns = {'pg': pg, 'json': json, 'print': print, 'io': io, 'os': os}
    exec(io.open(a.scenario, encoding='utf-8').read(), ns)
    print('ERRORS', errs)
    print('BLOCKED', BLOCKED)
    br.close()
