# -*- coding: utf-8 -*-
"""דפדפן בדיקה: האתר החי לקריאה בלבד, mas.js מקומי, כל כתיבה חסומה ונרשמת.
probe.py <mas.js> <width> <js-file-to-eval-after-load>"""
import sys, io, json
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
mas, W, js = sys.argv[1], int(sys.argv[2]), sys.argv[3]
BLOCKED = []
def seal(route):
    rq = route.request
    if rq.method.upper() not in ('GET', 'HEAD', 'OPTIONS'):
        BLOCKED.append(rq.method + ' ' + rq.url.split('?')[0])
        return route.fulfill(status=200, content_type='application/json', body='{"ok":true,"doc":{"edits":[]}}')
    if '127.0.0.1:8760' in rq.url or 'localhost:8760' in rq.url:
        BLOCKED.append('bridge ' + rq.url); return route.fulfill(status=200, body='{}')
    return route.continue_()
with sync_playwright() as pw:
    br = pw.chromium.launch()
    ctx = br.new_context(viewport={'width': W, 'height': 800}, locale='he-IL', service_workers='block')
    ctx.route('**/*', seal)
    if mas != '-':   # "-" = קוד העורך החי כפי שהוא (בדיקה אחרי פרסום)
        body = io.open(mas, 'rb').read()
        ctx.route('**/mas.js*', lambda r: r.fulfill(status=200, content_type='application/javascript; charset=utf-8', body=body))
    ctx.route('**/*.workers.dev/**', lambda r: (BLOCKED.append(r.request.method+' '+r.request.url.split('?')[0]) if r.request.method!='GET' else None, r.fulfill(status=200, content_type='application/json', body='{}'))[1])
    ctx.add_init_script("try{localStorage.setItem('lg-admin','1');localStorage.setItem('lg-adm','TEST-LOCAL-TOKEN')}catch(e){}")
    pg = ctx.new_page()
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:200]))
    pg.goto('https://leokmei.com/bekhorot.html#p=' + (sys.argv[4] if len(sys.argv) > 4 else ''), wait_until='load', timeout=120000)
    pg.wait_for_timeout(2500)
    import os
    if os.environ.get('P24CSS'):
        pg.add_style_tag(content=io.open(os.environ['P24CSS'],encoding='utf-8').read())
    pg.evaluate("()=>{if(typeof setEdit==='function')setEdit(true)}")
    pg.wait_for_timeout(1500)
    ns = {'pg': pg, 'json': json, 'print': print}
    exec(io.open(js, encoding='utf-8').read(), ns)
    print('ERRORS', errs)
    print('BLOCKED', BLOCKED)
    br.close()
