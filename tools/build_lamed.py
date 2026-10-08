# -*- coding: utf-8 -*-
"""build_lamed.py - בונה את מערכת הלומד לתוך site/ (6.10.2026).

מרכיב את lamed.js מחלקיו (tools/lamed/*.js), מפצל את הגיליון לגיליון הדפים
החדשים ולגיליון הקטן של דף הלימוד (שמוטמע בו), וכותב את הדפים: בית, מפת הש"ס,
דף מסכת, הלימוד שלי, הדף היומי, הגדרות, סיום מסכת, תמונת הלומדים.
"""
import os, io, re, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'lamed')
PARTS = ['core', 'tracker', 'brand', 'ui', 'ui2', 'shiurim', 'sync', 'quiz', 'boot']
MARK = '/* ---- בדף הלימוד'

PAGES = [
    ('index.html', 'home', 'לאוקמי גירסא · קיצור התלמוד הבבלי'),
    ('shas.html', 'shas', 'מפת הש"ס · לאוקמי גירסא'),
    ('masechet.html', 'masechet', 'מסכת · לאוקמי גירסא'),
    ('lamed.html', 'lamed', 'הלימוד שלי · לאוקמי גירסא'),
    ('yomi.html', 'yomi', 'הדף היומי · לאוקמי גירסא'),
    ('shiurim.html', 'shiurim', 'שיעורים · לאוקמי גירסא'),
    ('quiz.html', 'quiz', 'בחן את עצמך · לאוקמי גירסא'),
    ('settings.html', 'settings', 'הגדרות · לאוקמי גירסא'),
    ('done.html', 'done', 'הדרן עלך מסכת · לאוקמי גירסא'),
    ('admin-lamdim.html', 'admin', 'תמונת הלומדים · לאוקמי גירסא'),
]


def read(p):
    return io.open(p, encoding='utf-8').read()


def reader_css():
    css = read(os.path.join(SRC, 'lamed.css'))
    i = css.index(MARK)
    return css[i:]


def brand(site):
    """מעתיק את מוטיב השער, החלקים, הגופנים והסמלילים (tools/brand) אל site/brand,
    ואת ה-favicon וה-manifest אל שורש האתר (8.10.2026)."""
    import shutil, json
    src = os.path.join(HERE, 'brand'); dst = os.path.join(site, 'brand')
    os.makedirs(dst, exist_ok=True)
    for f in ('shaar-zahav.svg', 'shaar-currentColor.svg', 'shaar-zahav-96.webp', 'shaar-zahav-240.webp', 'shaar-zahav-960.webp'):
        shutil.copy(os.path.join(src, f), os.path.join(dst, f))
    v2 = os.path.join(dst, 'shaar-v2'); os.makedirs(v2, exist_ok=True)
    for f in os.listdir(os.path.join(src, 'shaar-v2')):
        if f.endswith('.webp'):
            shutil.copy(os.path.join(src, 'shaar-v2', f), os.path.join(v2, f))
    for sub in ('parts', 'fonts', 'icons', 'about'):
        d = os.path.join(dst, sub); os.makedirs(d, exist_ok=True)
        for f in os.listdir(os.path.join(src, sub)):
            shutil.copy(os.path.join(src, sub, f), os.path.join(d, f))
    shutil.copy(os.path.join(src, 'icons', 'og-image.png'), os.path.join(dst, 'og-image.png'))
    shutil.copy(os.path.join(src, 'icons', 'favicon.ico'), os.path.join(site, 'favicon.ico'))
    io.open(os.path.join(site, 'manifest.webmanifest'), 'w', encoding='utf-8').write(json.dumps({
        'name': 'לאוקמי גירסא - קיצור התלמוד הבבלי', 'short_name': 'לאוקמי גירסא', 'lang': 'he', 'dir': 'rtl',
        'start_url': '/', 'display': 'standalone', 'background_color': '#0b1c2a', 'theme_color': '#0b1c2a',
        'icons': [{'src': '/brand/icons/icon-192.png', 'sizes': '192x192', 'type': 'image/png'},
                  {'src': '/brand/icons/icon-512.png', 'sizes': '512x512', 'type': 'image/png'}]}, ensure_ascii=False, indent=1))


def build(site):
    brand(site)
    js = read(os.path.join(HERE, 'hdate.js')) + '\n' + '\n'.join(read(os.path.join(SRC, p + '.js')) for p in PARTS)
    io.open(os.path.join(site, 'lamed.js'), 'w', encoding='utf-8').write(js)
    css = read(os.path.join(SRC, 'lamed.css'))
    io.open(os.path.join(site, 'lamed.css'), 'w', encoding='utf-8').write(css)
    ui = read(os.path.join(HERE, 'ui.css'))
    io.open(os.path.join(site, 'ui.css'), 'w', encoding='utf-8').write(ui)
    uiv = hashlib.md5(ui.encode('utf-8')).hexdigest()[:8]
    sprite = read(os.path.join(HERE, 'ui-icons.svg'))
    ep = os.path.join(os.path.dirname(HERE), 'data', 'edited-pages.json')
    if os.path.exists(ep):
        io.open(os.path.join(site, 'edited-pages.json'), 'w', encoding='utf-8').write(read(ep))
    gallery(site)
    for fn, page, title in PAGES:
        html = ('<!DOCTYPE html><html lang="he" dir="rtl"><head><meta charset="utf-8">'
                '<meta name="viewport" content="width=device-width,initial-scale=1">'
                '<meta name="color-scheme" content="light dark"><title>%s</title>'
                '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
                '<link href="https://fonts.googleapis.com/css2?family=Assistant:wght@400;500;600;700;800&family=Noto+Sans+Hebrew:wght@400;600;700&family=Noto+Rashi+Hebrew:wght@400;700&display=swap" rel="stylesheet">'
                '<script>try{var t=localStorage.getItem("lg-theme");document.documentElement.setAttribute("data-theme",t==="dark"||t==="auto"?t:"light")}catch(e){document.documentElement.setAttribute("data-theme","light")}</script>'
                '<link rel="stylesheet" href="ui.css?v=%s"><link rel="stylesheet" href="lamed.css?v=%s"></head>'
                '<body class="lm" data-page="%s">%s<div id="lm-app"></div>'
                '<script src="daf-yomi.js"></script><script src="shas.js"></script>'
                '<script src="lamed.js"></script></body></html>') % (title, uiv, hashlib.md5(css.encode('utf-8')).hexdigest()[:8], page, sprite)
        io.open(os.path.join(site, fn), 'w', encoding='utf-8').write(html)


DEMO_NAMES = {'casual': 'מבקר מזדמן', 'regular': 'לומד קבוע בברכות', 'yomi': 'לומד הדף היומי בבכורות',
              'scholar': 'תלמיד חכם: חזרות על סוכה', 'suggester': 'מציע תיקונים'}
PAGE_NAMES = [('home', 'בית'), ('shas', 'מפת הש"ס'), ('masechet', 'דף מסכת'), ('lamed', 'הלימוד שלי'),
              ('yomi', 'הדף היומי'), ('settings', 'הגדרות'), ('done', 'סיום מסכת'), ('admin', 'תמונת הלומדים (מנהל)')]


def gallery(site):
    """דף גלריה פנימי (galeria-lamed.html): כל צילומי המסך של מערכת הלומד במקום
    אחד. אינו מקושר מן האתר הציבורי. התמונות נשמרות במאגר, ב-gallery-lamed/."""
    src = os.path.join(os.path.dirname(HERE), 'gallery-lamed')
    if not os.path.isdir(src):
        return
    import shutil
    dst = os.path.join(site, 'galeria-lamed')
    os.makedirs(dst, exist_ok=True)
    files = sorted(os.listdir(src))
    for f in files:
        shutil.copy(os.path.join(src, f), os.path.join(dst, f))
    h = ['<!DOCTYPE html><html lang="he" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
         '<meta name="robots" content="noindex"><title>גלריית מערכת הלומד (פנימי)</title><style>',
         'body{margin:0;background:#efe9d9;color:#1d1a16;font:17px/1.5 serif}main{max-width:1200px;margin:0 auto;padding:18px}',
         'h1{font-size:30px}h2{border-bottom:1px solid #c9bfa8;margin-top:36px}h3{margin:18px 0 6px;font-size:18px}',
         '.row{display:flex;gap:10px;flex-wrap:wrap}.row figure{margin:0;width:calc(25% - 8px);min-width:140px}',
         '.row img{width:100%;border:1px solid #c9bfa8;border-radius:4px;background:#fff}figcaption{font-size:13px;color:#6a5f4d}',
         '.ph img{max-height:380px;object-fit:cover;object-position:top}</style></head><body><main>',
         '<h1>גלריית מערכת הלומד</h1><p>צילומי מסך של כל הדפים החדשים, לכל אחד מחמשת הלומדים הבדויים: מחשב (1440) וטלפון (390), במצב בהיר וכהה. לחיצה על תמונה פותחת אותה בגודל מלא. קישורי ההדגמה: <code>index.html?demo=casual</code> (או regular, yomi, scholar, suggester).</p>']
    for d, dn in DEMO_NAMES.items():
        h.append('<h2>%s</h2>' % dn)
        for p, pn in PAGE_NAMES:
            figs = []
            for tag, tn in (('pc', 'מחשב'), ('ph', 'טלפון')):
                for th, thn in (('light', 'בהיר'), ('dark', 'כהה')):
                    fn = '%s-%s-%s-%s.webp' % (d, p, tag, th)
                    if fn in files:
                        figs.append('<figure class="%s"><a href="galeria-lamed/%s"><img loading="lazy" src="galeria-lamed/%s" alt="%s"></a><figcaption>%s, %s</figcaption></figure>' % (tag, fn, fn, pn, tn, thn))
            if figs:
                h.append('<h3>%s</h3><div class="row">%s</div>' % (pn, ''.join(figs)))
    extra = [f for f in files if not any(f.startswith(d + '-') for d in DEMO_NAMES)]
    if extra:
        h.append('<h2>צילומים נוספים</h2><div class="row">')
        for f in extra:
            h.append('<figure><a href="galeria-lamed/%s"><img loading="lazy" src="galeria-lamed/%s" alt=""></a><figcaption>%s</figcaption></figure>' % (f, f, f[:-5]))
        h.append('</div>')
    h.append('</main></body></html>')
    io.open(os.path.join(site, 'galeria-lamed.html'), 'w', encoding='utf-8').write(''.join(h))


if __name__ == '__main__':
    build(os.path.join(os.path.dirname(HERE), 'site'))
