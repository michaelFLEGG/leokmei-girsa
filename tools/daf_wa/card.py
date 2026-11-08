# -*- coding: utf-8 -*-
"""כרטיס התצוגה המקדימה של כל דף (פרומפט 23): 1200x480 JPEG ל-og:image (8.11.2026: נמוך יותר, לבקשת בעל הפרויקט).

רץ אצל מי שכותב את תוכן ההודעה (שיחה במחשב או משימה בענן), אחרי שהבודק אישר את התוכן,
ושומר ל-data/daf-wa/og/<slug>-<n>.jpg. הבנייה באתר רק מעתיקה (build.py) - כדי שבניית האתר
לא תהיה תלויה בדפדפן. כרטיס כללי ל-leokmei.com/daf: _general.jpg.
  uv run --no-project --with playwright python tools/daf_wa/card.py [slug-n ...]   (בלי פרמטרים: כל מה שחסר או ישן)"""
import html as H
import io
import json
import os
import pathlib
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DATA = os.path.join(ROOT, 'data', 'daf-wa')
OG = os.path.join(DATA, 'og')


def assets():
    """הגופנים ושער הזהב: מן האתר הבנוי אם קיים, אחרת מן העותק הראשי"""
    for base in (os.path.join(ROOT, 'site'), r'C:\Users\Owner\leokmei-girsa\site'):
        if os.path.exists(os.path.join(base, 'fonts', 'vilna-b.woff2')):
            import base64
            g = base64.b64encode(open(os.path.join(base, 'brand', 'shaar-zahav-240.webp'), 'rb').read()).decode()
            return pathlib.Path(base, 'fonts').as_uri(), 'data:image/webp;base64,' + g
    raise SystemExit('עצירה: לא נמצאו גופני האתר')


def render(jobs):
    from playwright.sync_api import sync_playwright
    fonts, gate = assets()
    tpl = io.open(os.path.join(HERE, 'card.html'), encoding='utf-8').read().replace('@@FONTS@@', fonts).replace('@@GATE@@', gate)
    os.makedirs(OG, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={'width': 1200, 'height': 480}, device_scale_factor=1)
        for name, daf, line in jobs:
            pg.set_content(tpl.replace('@@DAF@@', H.escape(daf)).replace('@@LINE@@', H.escape(line)), wait_until='load')
            pg.evaluate('document.fonts.ready')
            pg.wait_for_timeout(150)
            out = os.path.join(OG, name + '.jpg')
            pg.screenshot(path=out, type='jpeg', quality=88)
            print(name, os.path.getsize(out) // 1024, 'KB')
        b.close()


def main(args):
    jobs = []
    for f in sorted(os.listdir(DATA)):
        if not f.endswith('.json'):
            continue
        name = f[:-5]
        if args and name not in args:
            continue
        c = json.load(io.open(os.path.join(DATA, f), encoding='utf-8'))
        out = os.path.join(OG, name + '.jpg')
        if not args and os.path.exists(out) and os.path.getmtime(out) >= os.path.getmtime(os.path.join(DATA, f)):
            continue
        jobs.append((name, '%s דף %s' % (c['masechet'], c['daf'].replace('"', '״')), c.get('card') or ''))
    if not args or '_general' in args:
        if args or not os.path.exists(os.path.join(OG, '_general.jpg')):
            jobs.append(('_general', 'קיצור הדף היומי', 'כל יום - הדף בקצרה, בתצוגה קלה לטלפון'))
    render(jobs)


if __name__ == '__main__':
    main(sys.argv[1:])
