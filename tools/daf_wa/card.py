# -*- coding: utf-8 -*-
"""כרטיס התצוגה המקדימה של כל דף (פרומפט 23): 1200x480 JPEG ל-og:image (8.11.2026: נמוך יותר, בלי ל', בגופן BA Vilna ועם היום והתאריך - לבקשת בעל הפרויקט).
פרומפט 30 (10.11.2026): לכל דף מצויר גם הכרטיס שנשלח כתמונה בווטסאפ - 1080x1080 (card-sq.html), ל-data/daf-wa/wa/<slug>-<n>.jpg.
ההודעה היומית היא תמונה עם כיתוב, ולכן בלי הכרטיס הזה ההודעה לא יוצאת (השרת והשולח בודקים). og:image של האתר לא השתנה.

רץ אצל מי שכותב את תוכן ההודעה (שיחה במחשב או משימה בענן), אחרי שהבודק אישר את התוכן,
ושומר ל-data/daf-wa/og/<slug>-<n>.jpg. הבנייה באתר רק מעתיקה (build.py) - כדי שבניית האתר
לא תהיה תלויה בדפדפן. כרטיס כללי ל-leokmei.com/daf: _general.jpg.
  uv run --no-project --with playwright python tools/daf_wa/card.py [--wa] [slug-n ...]   (בלי פרמטרים: כל מה שחסר או ישן; --wa: רק הריבועי)"""
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
WA = os.path.join(DATA, 'wa')   # פרומפט 30: הכרטיס הריבועי שנשלח כתמונה
# (תבנית, רוחב, גובה, תיקייה)
FORMATS = (('card.html', 1200, 480, OG), ('card-sq.html', 1080, 1080, WA))


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


def render(jobs, formats=FORMATS):
    from playwright.sync_api import sync_playwright
    fonts, gate = assets()
    ba = ba_fonts()
    if not ba:
        return
    bab, bar = ba
    with sync_playwright() as p:
        b = p.chromium.launch()
        for tname, W, Hh, outdir in formats:
            tpl = (io.open(os.path.join(HERE, tname), encoding='utf-8').read().replace('@@FONTS@@', fonts).replace('@@GATE@@', gate)
                   .replace('@@BA_B@@', bab).replace('@@BA_R@@', bar))
            os.makedirs(outdir, exist_ok=True)
            pg = b.new_page(viewport={'width': W, 'height': Hh}, device_scale_factor=1)
            for name, daf, line, iso in jobs:
                pg.set_content(tpl.replace('@@DAF@@', H.escape(daf)).replace('@@LINE@@', H.escape(line).replace('-', '<span class="hy">-</span>')).replace('@@DATE@@', iso), wait_until='load')
                pg.evaluate('document.fonts.ready.then(() => window.fit && window.fit())')
                pg.wait_for_timeout(150)
                out = os.path.join(outdir, name + '.jpg')
                pg.screenshot(path=out, type='jpeg', quality=88)
                if os.path.getsize(out) < 10000:   # עצירה רועשת: כרטיס ריק או שבור
                    raise SystemExit('עצירה: הכרטיס %s יצא קטן מדי (%d בתים)' % (out, os.path.getsize(out)))
                print(os.path.basename(outdir), name, os.path.getsize(out) // 1024, 'KB')
            pg.close()
        b.close()


def main(args):
    # --wa: רק הכרטיס הריבועי (בלי לצייר מחדש את כרטיסי og שכבר באתר)
    formats = FORMATS
    if '--wa' in args:
        args = [a for a in args if a != '--wa']
        formats = (FORMATS[1],)
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
        outs = [os.path.join(fm[3], name + '.jpg') for fm in formats]
        if not args and all(os.path.exists(o) and os.path.getmtime(o) >= os.path.getmtime(os.path.join(DATA, f)) for o in outs):
            continue
        iso = build.date_of(c['slug'], int(c['n']), today, L).isoformat()   # היום שבו הדף נלמד במחזור הקרוב
        jobs.append((name, '%s דף %s' % (c['masechet'], c['daf'].replace('"', '״')), c.get('card') or '', iso))
    if not args or '_general' in args:
        if args or not os.path.exists(os.path.join(OG, '_general.jpg')):
            jobs.append(('_general', 'קיצור הדף היומי', 'כל יום - הדף בקצרה, בתצוגה קלה לטלפון', ''))
    render(jobs, formats)


if __name__ == '__main__':
    main(sys.argv[1:])
