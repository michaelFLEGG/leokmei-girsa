# -*- coding: utf-8 -*-
"""build_seo.py - כתובת קנונית והופעה בגוגל (מנה 4, 7.10.2026).

רץ בסוף הבנייה על site/ המוכן: מזריק לכל דף קנוני, תיאור, תגי שיתוף ונתונים
מובנים; כותב sitemap.xml, robots.txt, CNAME ודף "אודות". הכתובת הקנונית
היחידה היא BASE, בלי www. דפי עבודה (הגהה, מנהל, הגדרות) מסומנים noindex.
"""
import os, io, re, json, datetime, urllib.request

BASE = 'https://leokmei.com'
NAME = 'לאוקמי גירסא'
HOME_TITLE = 'לאוקמי גירסא · קיצור התלמוד הבבלי, קיצור הדף היומי וקיצור הש"ס'
HOME_DESC = ('לאוקמי גירסא - קיצור התלמוד הבבלי, דף אחר דף. '
             'קיצור הדף היומי, קיצור הש"ס, ומערכת לימוד אישית. חינם.')
API = 'https://leokmei-suggest.m7654301.workers.dev'
NOINDEX = ('lamed.html', 'settings.html', 'done.html', 'admin-lamdim.html', 'masechet.html', 'quiz.html')

ICONS = ('<meta property="og:image" content="%s/brand/og-image.png"><meta property="og:image:width" content="1200">'
         '<meta property="og:image:height" content="630"><meta property="og:image:alt" content="שער לאוקמי גירסא">'
         '<meta name="twitter:card" content="summary_large_image">'
         '<link rel="icon" href="/favicon.ico" sizes="any"><link rel="icon" type="image/png" sizes="32x32" href="/brand/icons/favicon-32.png">'
         '<link rel="apple-touch-icon" href="/brand/icons/apple-touch-icon.png"><link rel="manifest" href="/manifest.webmanifest">'
         '<meta name="theme-color" content="#0b1c2a">') % BASE

# מעטפת קטנה לדפי טקסט פשוטים (אודות, מקורות): סרגל כחול עם השער הקטן
MINI_STYLE = ('@font-face{font-family:LGVilnaXB;src:url(brand/fonts/vilna-xb.woff2) format("woff2");font-display:swap}'
              'html{background:#060f18}body{margin:0;min-height:100vh;display:flex;flex-direction:column;background:radial-gradient(ellipse 80% 60% at 50% 20%,#102a42,#091827 55%,#060f18);color:#f5edd6;font-family:serif;line-height:1.8}'
              'header.mh{background:#0b1c2a;border-bottom:1px solid #8f6a1e;padding:8px 18px}'
              'header.mh a{display:inline-flex;align-items:center;gap:10px;text-decoration:none;font:400 25px/1.1 LGVilnaXB,serif;background:linear-gradient(170deg,#fbe7a1,#e6bd52 30%,#c38f2a 55%,#efcf6b 75%,#b07c1f);-webkit-background-clip:text;background-clip:text;color:transparent;filter:drop-shadow(0 1px 0 rgba(0,0,0,.7)) drop-shadow(0 0 6px rgba(240,196,90,.45))}'
              'header.mh img{height:34px;width:auto}main{flex:1 0 auto;box-sizing:border-box;width:100%;max-width:640px;margin:0 auto;padding:30px 18px}h1{font-size:28px;color:#f9e08a}a{color:#e9c35a}')
# דף אודות מחוץ למשימת השער הסימטרי (הנחיה נפרדת ממתינה לעריכת המנהל): נשאר בעיצובו הקודם
ABOUT_STYLE = ('@font-face{font-family:LGVilnaTitle;src:url(brand/fonts/vilna-title.woff2) format("woff2");font-display:swap}'
               'body{margin:0;background:#f7f3ea;color:#1b1b1b;font-family:serif;line-height:1.8}'
               'header.mh{background:#0b1c2a;border-bottom:1px solid #8f6a1e;padding:8px 18px}'
               'header.mh a{display:inline-flex;align-items:center;gap:10px;color:#f9e08a;text-decoration:none;font:400 24px LGVilnaTitle,serif}'
               'header.mh img{height:32px;width:auto}main{max-width:640px;margin:0 auto;padding:30px 18px}h1{font-size:28px}a{color:#8f6a1e}')
MINI_HEADER = '<header class="mh"><a href="index.html"><img src="brand/shaar-v2/shaar-zohar-96.webp" alt="">לאוקמי גירסא</a></header>'


ABOUT = ('<!DOCTYPE html><html lang="he" dir="rtl"><head><meta charset="utf-8">'
         '<meta name="viewport" content="width=device-width,initial-scale=1"><title>אודות · לאוקמי גירסא</title>'
         '<style>' + ABOUT_STYLE + '</style></head><body>' + MINI_HEADER + '<main>'
         '<h1>אודות לאוקמי גירסא</h1>'
         '<p>לאוקמי גירסא הוא קיצור של התלמוד הבבלי, דף אחר דף, כך שאפשר לראות את מהלך הגמרא '
         'ואת הכרעתה בלי לאבד את החוט. האתר מיועד ללומדי הדף היומי, ללומדי מסכת ולכל מי שרוצה לחזור על הש"ס.</p>'
         '<p>הקיצור נערך בידי הרב מיכאל פלג, ונבנה אוטומטית מקובצי העריכה. כל מסכת שמסתיימת עולה לאתר. '
         'הגמרא המנוקדת והפירוש מוצגים ברישיון ומפורטים בעמוד <a href="mekorot.html">מקורות</a>.</p>'
         '<p>האתר חינמי ואינו מוכר דבר. מצאת טעות? אפשר להציע תיקון ישירות בדף הגמרא.</p>'
         '<p><a href="index.html">חזרה לשער</a> · <a href="yomi.html">הדף היומי היום</a></p>'
         '</main></body></html>')

NOSCRIPT = ('<noscript><main style="max-width:640px;margin:20px auto;padding:0 18px;font-family:serif;line-height:1.8">'
            '<h1>לאוקמי גירסא - קיצור התלמוד הבבלי</h1>'
            '<p>קיצור הדף היומי וקיצור הש"ס, דף אחר דף. האתר פועל עם JavaScript.</p>'
            '<p><a href="masechtot.html">כל המסכתות</a> · <a href="yomi.html">הדף היומי היום</a> · '
            '<a href="about.html">אודות</a></p></main></noscript>')


def esc(s):
    return s.replace('&', '&amp;').replace('"', '&quot;').replace('<', '&lt;')


def head_block(path, title, desc, noindex, ld=None):
    url = BASE + ('/' if path == 'index.html' else '/' + path)
    h = ['<link rel="canonical" href="%s">' % url,
         '<meta name="description" content="%s">' % esc(desc),
         '<meta property="og:type" content="website"><meta property="og:locale" content="he_IL">',
         '<meta property="og:site_name" content="%s">' % NAME,
         '<meta property="og:title" content="%s">' % esc(title),
         '<meta property="og:description" content="%s">' % esc(desc),
         '<meta property="og:url" content="%s">' % url,
         ICONS]
    if noindex:
        h.append('<meta name="robots" content="noindex,follow">')
    if ld:
        h.append('<script type="application/ld+json">%s</script>' % json.dumps(ld, ensure_ascii=False))
    return ''.join(h)


def rewrite(site, fn, title, desc, noindex=False, ld=None, body_extra=None):
    p = os.path.join(site, fn)
    if not os.path.exists(p):
        return False
    h = io.open(p, encoding='utf-8').read()
    if 'rel="canonical"' in h:
        h = re.sub(r'<link rel="canonical"[^>]*>', '', h)
    h = re.sub(r'<title>.*?</title>', '<title>%s</title>' % esc(title), h, count=1, flags=re.S)
    h = h.replace('</head>', head_block(fn, title, desc, noindex, ld) + '</head>', 1)
    if body_extra:
        h = re.sub(r'(<body[^>]*>)', lambda m: m.group(1) + body_extra, h, count=1)
    io.open(p, 'w', encoding='utf-8').write(h)
    return True



def lessons_static():
    """שיעורי היוטיוב מן השרת (קריאה פתוחה), לנתונים מובנים ולטקסט סטטי בדף השיעורים.
    כשל בקריאה אינו מפיל את הבנייה, אך נרשם בקול: הדף יעלה בלי הרשימה הסטטית."""
    try:
        req = urllib.request.Request(API + '/lessons', headers={'User-Agent': 'leokmei-build/1.0'})
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode('utf-8')).get('items', [])
    except Exception as e:
        print('אזהרה SEO: קריאת השיעורים נכשלה, דף השיעורים ללא רשימה סטטית:', e)
        return []

def run(site, built, slug):
    now = datetime.date.today().isoformat()
    io.open(os.path.join(site, 'about.html'), 'w', encoding='utf-8').write(ABOUT)
    io.open(os.path.join(site, 'CNAME'), 'w', encoding='utf-8').write('leokmei.com\n')
    io.open(os.path.join(site, 'robots.txt'), 'w', encoding='utf-8').write(
        'User-agent: *\nAllow: /\nDisallow: /galeria-lamed/\n\nSitemap: %s/sitemap.xml\n' % BASE)
    ld_home = [{'@context': 'https://schema.org', '@type': 'WebSite', 'name': NAME, 'url': BASE + '/',
                'inLanguage': 'he', 'alternateName': ['קיצור התלמוד הבבלי', 'קיצור הדף היומי', 'קיצור הש"ס']},
               {'@context': 'https://schema.org', '@type': 'Organization', 'name': NAME, 'url': BASE + '/'}]
    urls = [('index.html', '1.0'), ('yomi.html', '0.9'), ('masechtot.html', '0.8'), ('shas.html', '0.7'),
            ('about.html', '0.4'), ('mekorot.html', '0.3')]
    rewrite(site, 'index.html', HOME_TITLE, HOME_DESC, ld=ld_home, body_extra=NOSCRIPT)
    rewrite(site, 'yomi.html', 'הדף היומי היום בקיצור · ' + NAME,
            'הדף היומי של היום בקיצור: הדף שלומדים היום בעולם. מתעדכן מדי יום.')
    rewrite(site, 'masechtot.html', 'כל מסכתות הש"ס בקיצור · ' + NAME,
            'רשימת כל מסכתות התלמוד הבבלי, עם המסכתות שכבר עלו לאתר בקיצור לאוקמי גירסא.')
    rewrite(site, 'shas.html', 'מפת הש"ס · ' + NAME, 'מפת הש"ס לפי סדרים ומסכתות, עם התקדמות הלימוד.')
    rewrite(site, 'about.html', 'אודות · ' + NAME, 'על לאוקמי גירסא: קיצור התלמוד הבבלי, מי עורך אותו ואיך הוא נבנה.')
    rewrite(site, 'mekorot.html', 'מקורות · ' + NAME, 'המקורות והרישיונות של הגמרא והפירוש המוצגים באתר.')
    items = lessons_static()
    ld_v = [{'@context': 'https://schema.org', '@type': 'VideoObject', 'name': l['title'],
             'description': 'שיעור על %s %s' % (l['slug'], l['from']), 'thumbnailUrl': l['thumb'],
             'uploadDate': datetime.date.fromtimestamp(l['t'] / 1000).isoformat(),
             'embedUrl': 'https://www.youtube-nocookie.com/embed/' + l['vid'],
             'contentUrl': 'https://www.youtube.com/watch?v=' + l['vid']} for l in items]
    ns = '<noscript><main style="max-width:640px;margin:20px auto;padding:0 18px;font-family:serif"><h1>שיעורים</h1><ul>' + ''.join(
        '<li><a href="https://www.youtube.com/watch?v=%s">%s</a></li>' % (l['vid'], esc(l['title'])) for l in items) + '</ul></main></noscript>'
    rewrite(site, 'shiurim.html', 'שיעורי גמרא בקיצור · ' + NAME,
            'שיעורי וידאו על הדף לפי מסכת ודף, ללומדי הדף היומי והש"ס, בצמוד לקיצור לאוקמי גירסא.',
            ld=ld_v or None, body_extra=ns)
    urls.append(('shiurim.html', '0.6'))
    for fn in NOINDEX:
        rewrite(site, fn, NAME, NAME, noindex=True)
    for m in built:
        fn = slug[m] + '.html'
        desc = ('מסכת %s בקיצור, דף אחר דף, מתוך קיצור התלמוד הבבלי של לאוקמי גירסא.' % m)
        ld = {'@context': 'https://schema.org', '@type': 'Book', 'name': 'מסכת %s בקיצור' % m,
              'inLanguage': 'he', 'url': BASE + '/' + fn, 'isPartOf': {'@type': 'WebSite', 'name': NAME, 'url': BASE + '/'}}
        hub = ('<noscript><main style="max-width:640px;margin:20px auto;padding:0 18px;font-family:serif"><h1>מסכת %s בקיצור</h1>'
               '<p><a href="%s/">רשימת כל דפי המסכת</a></p></main></noscript>') % (esc(m), slug[m])
        if rewrite(site, fn, 'מסכת %s בקיצור · %s' % (m, NAME), desc, ld=ld, body_extra=hub):
            urls.append((fn, '0.8'))
    import build_static
    urls += build_static.run(site, built, slug)
    sm = ['<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for fn, pr in urls:
        loc = BASE + '/' if fn == 'index.html' else BASE + '/' + fn
        sm.append('<url><loc>%s</loc><lastmod>%s</lastmod><priority>%s</priority></url>' % (loc, now, pr))
    sm.append('</urlset>')
    io.open(os.path.join(site, 'sitemap.xml'), 'w', encoding='utf-8').write('\n'.join(sm))
    print('SEO: %d כתובות במפת האתר' % len(urls))
