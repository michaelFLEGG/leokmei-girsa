# -*- coding: utf-8 -*-
"""כרטיס התצוגה המקדימה של כל דף (פרומפט 23): 1200x480 JPEG ל-og:image (8.11.2026: נמוך יותר, בלי ל', בגופן BA Vilna ועם היום והתאריך - לבקשת בעל הפרויקט).

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


def ba_fonts():
    """גופן וילנא של בית אלף (BA Vilna) - של בעל הפרויקט, ברישיון שלו. אינו נשמר במאגר (המאגר ציבורי): במחשב שלו נלקח מן הגופנים
    המותקנים, ובבנייה בענן - מסוד (LEOKMEI_BA_FONTS: תיקייה עם ba-vilna-b.otf ו-ba-vilna-r.otf). אין גופן - עצירה רועשת, לא כרטיס בגופן אחר."""
    import base64
    cands = []
    if os.environ.get('LEOKMEI_BA_FONTS'):
        d = os.environ['LEOKMEI_BA_FONTS']
        cands.append((os.path.join(d, 'ba-vilna-b.otf'), os.path.join(d, 'ba-vilna-r.otf')))
    d = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'Windows', 'Fonts')
    cands.append((os.path.join(d, 'BA Vilna Bold.otf'), os.path.join(d, 'BA Vilna Regular.otf')))
    for b, r in cands:
        if os.path.exists(b) and os.path.exists(r):
            u = lambda f: 'data:font/otf;base64,' + base64.b64encode(open(f, 'rb').read()).decode()
            return u(b), u(r)
    msg = 'גופן BA Vilna לא נמצא (לא במחשב ולא בסוד LEOKMEI_BA_FONTS) - הכרטיסים לא צוירו'
    if os.environ.get('CI'):
        # בבנייה בענן: התראה רועשת ביומן הבנייה, בלי להפיל את פרסום האתר כולו. הדף יוצא בלי כרטיס משלו (build.py רושם אותו כחסר).
        print('::error::' + msg)
        return None
    raise SystemExit('עצירה: ' + msg)


def render(jobs):
    from playwright.sync_api import sync_playwright
    fonts, gate = assets()
    ba = ba_fonts()
    if not ba:
        return
    bab, bar = ba
    tpl = (io.open(os.path.join(HERE, 'card.html'), encoding='utf-8').read().replace('@@FONTS@@', fonts).replace('@@GATE@@', gate)
           .replace('@@BA_B@@', bab).replace('@@BA_R@@', bar))
    os.makedirs(OG, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={'width': 1200, 'height': 480}, device_scale_factor=1)
        for name, daf, line, iso in jobs:
            pg.set_content(tpl.replace('@@DAF@@', H.escape(daf)).replace('@@LINE@@', H.escape(line).replace('-', '<span class="hy">-</span>')).replace('@@DATE@@', iso), wait_until='load')
            pg.evaluate('document.fonts.ready.then(() => window.fit && window.fit())')
            pg.wait_for_timeout(150)
            out = os.path.join(OG, name + '.jpg')
            pg.screenshot(path=out, type='jpeg', quality=88)
            print(name, os.path.getsize(out) // 1024, 'KB')
        b.close()


def main(args):
    import datetime as dt
    sys.path.insert(0, HERE)
    import build
    L, today = build.cycle(), dt.date.today()
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
        iso = build.date_of(c['slug'], int(c['n']), today, L).isoformat()   # היום שבו הדף נלמד במחזור הקרוב
        jobs.append((name, '%s דף %s' % (c['masechet'], c['daf'].replace('"', '״')), c.get('card') or '', iso))
    if not args or '_general' in args:
        if args or not os.path.exists(os.path.join(OG, '_general.jpg')):
            jobs.append(('_general', 'קיצור הדף היומי', 'כל יום - הדף בקצרה, בתצוגה קלה לטלפון', ''))
    render(jobs)


if __name__ == '__main__':
    main(sys.argv[1:])
