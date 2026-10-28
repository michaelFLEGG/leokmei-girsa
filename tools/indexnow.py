# -*- coding: utf-8 -*-
"""indexnow.py - הודעה לבינג (ולשאר מנועי IndexNow) על דפים חדשים או שהשתנו (פרומפט 10, 28.10.2026).

IndexNow הוא פרוטוקול פתוח וחינמי: האתר מחזיק קובץ מפתח בשורש (KEY.txt, נכתב בבנייה
ב-build_seo), ושולח רשימת כתובות. אין צורך בחשבון ובסיסמה. המפתח ציבורי מעצם הגדרתו.

  uv run python tools/indexnow.py --all        כל כתובות מפת האתר (פעם אחת, אחרי פרסום גדול)
  uv run python tools/indexnow.py --changed    רק הדפים שתוכנם השתנה בבנייה הזאת (site/seo-report.json)

כשל בשליחה מודפס בקול, אך אינו מחזיר קוד כשל: הפרסום עצמו כבר עלה.
"""
import os, io, re, sys, json, urllib.request

KEY = '8a22630c80ffab9161c97a2f7527fd61'
HOST = 'leokmei.com'
BASE = 'https://' + HOST
SITE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'site')


def sitemap_urls():
    out = []
    idx = io.open(os.path.join(SITE, 'sitemap.xml'), encoding='utf-8').read()
    for loc in re.findall(r'<loc>([^<]+)</loc>', idx):
        p = os.path.join(SITE, loc.rsplit('/', 1)[-1])
        if loc.endswith('.xml') and os.path.exists(p):
            out += re.findall(r'<loc>([^<]+)</loc>', io.open(p, encoding='utf-8').read())
    return out


def changed_urls():
    rep = json.load(io.open(os.path.join(SITE, 'seo-report.json'), encoding='utf-8'))
    return [BASE + '/' + p for p in rep.get('changed', [])]


def submit(urls):
    for i in range(0, len(urls), 9000):
        part = urls[i:i + 9000]
        body = json.dumps({'host': HOST, 'key': KEY, 'keyLocation': '%s/%s.txt' % (BASE, KEY), 'urlList': part}).encode('utf-8')
        req = urllib.request.Request('https://api.indexnow.org/indexnow', data=body, method='POST',
                                     headers={'Content-Type': 'application/json; charset=utf-8', 'User-Agent': 'leokmei-build/1.0'})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                print('IndexNow: נשלחו %d כתובות, תשובה %s' % (len(part), r.status))
        except urllib.error.HTTPError as e:
            print('IndexNow: כשל %s - %s' % (e.code, e.read()[:300].decode('utf-8', 'replace')))
        except Exception as e:
            print('IndexNow: כשל -', e)


if __name__ == '__main__':
    urls = sitemap_urls() if '--all' in sys.argv else changed_urls()
    if urls:
        submit(urls)
    else:
        print('IndexNow: אין כתובות חדשות לשליחה')
