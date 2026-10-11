# -*- coding: utf-8 -*-
"""בדיקת חלון ההדפסה בדף המסכת (בלי שרת): נפתח, מחשב מספר עמודים, ואינו מייצר שגיאות קונסול.
הרצה: uv run --with playwright python tools/print/test_dialog.py --site <תיקיית האתר> --slug kiddushin"""
import argparse, json, mimetypes, os, sys, time, urllib.parse

HOST = 'print.local'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--site', required=True)
    ap.add_argument('--slug', required=True)
    ap.add_argument('--shot', default='')
    a = ap.parse_args()
    from playwright.sync_api import sync_playwright
    site = os.path.abspath(a.site)
    errs = []

    def handler(route):
        u = urllib.parse.urlparse(route.request.url)
        if u.hostname != HOST:
            return route.abort()
        fp = os.path.normpath(os.path.join(site, urllib.parse.unquote(u.path).lstrip('/')))
        if not fp.startswith(site) or not os.path.isfile(fp):
            errs.append('404: ' + u.path)
            return route.fulfill(status=404, body=b'')
        route.fulfill(status=200, headers={'content-type': mimetypes.guess_type(fp)[0] or 'application/octet-stream'},
                      body=open(fp, 'rb').read())

    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={'width': 1280, 'height': 800})
        ctx.route('**/*', handler)
        pg = ctx.new_page()
        pg.on('pageerror', lambda e: errs.append('pageerror: %s' % e))
        pg.on('console', lambda m: errs.append('console.%s: %s' % (m.type, m.text)) if m.type == 'error' and 'ERR_FAILED' not in m.text else None)
        pg.goto('http://%s/%s.html' % (HOST, a.slug), wait_until='domcontentloaded', timeout=120000)
        pg.wait_for_selector('#prbtn', timeout=60000)
        pg.wait_for_timeout(2500)
        pg.click('#prbtn')
        pg.wait_for_selector('#prnd.open', timeout=10000)
        out = {}
        out['title'] = pg.inner_text('#prnd h2')
        pg.check('input[name=prt][value=range]')
        pg.wait_for_timeout(300)
        out['count_after_open'] = None
        for _ in range(60):
            t = pg.inner_text('#prn-cnt')
            if 'מספר העמודים' in t:
                out['count_after_open'] = t
                break
            pg.wait_for_timeout(500)
        out['tosDisabled'] = pg.is_disabled('#prn-tos')
        out['tosNote'] = pg.inner_text('#prn-tn')
        pg.check('input[name=prt][value=all]')
        for _ in range(120):
            t = pg.inner_text('#prn-cnt')
            if 'מספר העמודים' in t and t != out['count_after_open']:
                out['count_all'] = t
                break
            pg.wait_for_timeout(500)
        if a.shot:
            pg.screenshot(path=a.shot)
        out['errors'] = errs[:10]
        print(json.dumps(out, ensure_ascii=False, indent=1))
        b.close()


if __name__ == '__main__':
    main()
