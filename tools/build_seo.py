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
HOME_DESC = ('לאוקמי גירסא - קיצור התלמוד הבבלי: שלד הסוגיה בלבד, דף אחר דף. '
             'קיצור הדף היומי, קיצור הש"ס, ומערכת לימוד אישית. חינם.')
API = 'https://leokmei-suggest.m7654301.workers.dev'
NOINDEX = ('lamed.html', 'settings.html', 'done.html', 'admin-lamdim.html', 'masechet.html')

ABOUT = ('<!DOCTYPE html><html lang="he" dir="rtl"><head><meta charset="utf-8">'
         '<meta name="viewport" content="width=device-width,initial-scale=1"><title>אודות · לאוקמי גירסא</title>'
         '<style>body{margin:0;background:#e9e4d8;color:#1d1a16;font-family:serif;line-height:1.8}'
         'main{max-width:640px;margin:0 auto;padding:30px 18px}h1{font-size:28px}a{color:#5a4a2a}</style></head><body><main>'
         '<h1>אודות לאוקמי גירסא</h1>'
         '<p>לאוקמי גירסא הוא קיצור של התלמוד הבבלי: שלד הסוגיה בלבד, דף אחר דף, כך שאפשר לראות את מהלך הגמרא '
         'ואת הכרעתה בלי לאבד את החוט. האתר מיועד ללומדי הדף היומי, ללומדי מסכת ולכל מי שרוצה לחזור על הש"ס.</p>'
         '<p>הקיצור נערך בידי הרב מיכאל פלג, ונבנה אוטומטית מקובצי העריכה. כל מסכת שמסתיימת עולה לאתר. '
         'הגמרא המנוקדת והפירוש מוצגים ברישיון ומפורטים בעמוד <a href="mekorot.html">מקורות</a>.</p>'
         '<p>האתר חינמי ואינו מוכר דבר. מצאת טעות? אפשר להציע תיקון ישירות בדף הגמרא.</p>'
         '<p><a href="index.html">חזרה לשער</a> · <a href="yomi.html">הדף היומי היום</a></p>'
         '</main></body></html>')

NOSCRIPT = ('<noscript><main style="max-width:640px;margin:20px auto;padding:0 18px;font-family:serif;line-height:1.8">'
            '<h1>לאוקמי גירסא - קיצור התלמוד הבבלי</h1>'
            '<p>קיצור הדף היומי וקיצור הש"ס: שלד הסוגיה בלבד, דף אחר דף. האתר פועל עם JavaScript.</p>'
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
         '<meta property="og:url" content="%s">' % url]
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
        with urllib.request.urlopen(API + '/lessons', timeout=20) as r:
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
            'הדף היומי של היום בקיצור: שלד הסוגיה של הדף שלומדים היום בעולם. מתעדכן מדי יום.')
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
        desc = ('מסכת %s בקיצור: שלד הסוגיה בלבד, דף אחר דף, מתוך קיצור התלמוד הבבלי של לאוקמי גירסא.' % m)
        ld = {'@context': 'https://schema.org', '@type': 'Book', 'name': 'מסכת %s בקיצור' % m,
              'inLanguage': 'he', 'url': BASE + '/' + fn, 'isPartOf': {'@type': 'WebSite', 'name': NAME, 'url': BASE + '/'}}
        if rewrite(site, fn, 'מסכת %s בקיצור · %s' % (m, NAME), desc, ld=ld):
            urls.append((fn, '0.8'))
    sm = ['<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for fn, pr in urls:
        loc = BASE + '/' if fn == 'index.html' else BASE + '/' + fn
        sm.append('<url><loc>%s</loc><lastmod>%s</lastmod><priority>%s</priority></url>' % (loc, now, pr))
    sm.append('</urlset>')
    io.open(os.path.join(site, 'sitemap.xml'), 'w', encoding='utf-8').write('\n'.join(sm))
    print('SEO: %d כתובות במפת האתר' % len(urls))
