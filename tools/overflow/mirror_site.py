# -*- coding: utf-8 -*-
"""מראה של דף מסכת מן האתר החי, לתיקייה מקומית, בשביל מחולל "שורה שהתארכה" (פרומפט 41).

הבנייה המלאה של האתר צריכה את מפתח המנהל (פירוש הגמרא). המחולל צריך רק את הדף, הקוד המשותף, הנתונים והגופנים -
כפי שהגולש מקבל אותם - ולכן הוא טוען את הדף החי בדפדפן פעם אחת ושומר כל קובץ שהדף ביקש מן האתר.
  uv run --with playwright python tools/overflow/mirror_site.py --slug berakhot --out _work/site-mirror
"""
import argparse, os, sys, urllib.parse
from playwright.sync_api import sync_playwright

ap = argparse.ArgumentParser()
ap.add_argument('--slug', required=True)
ap.add_argument('--out', required=True)
ap.add_argument('--base', default='https://leokmei.com/')
a = ap.parse_args()
host = urllib.parse.urlparse(a.base).hostname
saved = []
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=os.environ.get('PRINT_CHROMIUM') or None)
    pg = b.new_page()

    def on(resp):
        u = urllib.parse.urlparse(resp.url)
        if u.hostname != host or resp.status != 200:
            return
        path = urllib.parse.unquote(u.path).lstrip('/') or 'index.html'
        try:
            body = resp.body()
        except Exception:
            return
        fp = os.path.join(a.out, path)
        os.makedirs(os.path.dirname(fp), exist_ok=True)
        open(fp, 'wb').write(body)
        saved.append(path)
    pg.on('response', on)
    q = urllib.parse.urlencode({'print': '1', 'from': 'ב.', 'to': 'ב.', 'profile': 'a4'})
    pg.goto(a.base + a.slug + '.html?' + q, wait_until='domcontentloaded', timeout=180000)
    pg.wait_for_function("window.__PRN && (window.__PRN.state==='done'||window.__PRN.state==='error')", timeout=300000)
    b.close()
need = [a.slug + '.html', 'mas.js', a.slug + '.data.js']
miss = [x for x in need if x not in saved]
if miss:
    sys.exit('עצירה: המראה חסרה קבצים: ' + ', '.join(miss))
print('נשמרו %d קבצים' % len(saved))
