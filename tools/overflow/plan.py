# -*- coding: utf-8 -*-
"""plan.py - אילו מסכתות צריכות סבב "שורה שהתארכה" עכשיו (פרומפט 55, 17.11.2026).

מיכאל (17.11.2026): "האיחוי האוטומטי צריך לעבוד כמנגנון באתר בלי שום קשר לאיזה מסכת. בכל האתר בכל המסכתות."

א. ההיקף: data/overflow/config.json. "slugs": "all" = כל מסכת שיש לה דף באתר (רשימת LATIN של build_all.py).
   "first" = מסכתות שרצות ראשונות (שבת, שמיכאל עובד עליה עכשיו).
ב. רק מה שהשתנה: לכל מסכת נשמרת חותמת (data/overflow/stamps/<מסכת>.txt) - טביעה של דף הנתונים החי (<מסכת>.data.js)
   ושל שכבת העריכות החיה (/live). מסכת שאף אחד מהשניים לא השתנה בה מאז הסבב הקודם - מדולגת.
   בתוך מסכת: המחולל מודד את כולה (המנוע מעמד את כל המסכת), אבל ההחלה נוגעת רק בשורות שעוד לא הוחלו,
   והנעילה רק מוסיפה או משחררת שורות שהשתנו.
ג. הפלט: מערך JSON של מסכתות (לשורת matrix), ובמצב --stamp <מסכת> - כתיבת החותמת אחרי סבב שעבר.

    python tools/overflow/plan.py                 -> ["shabbat","berakhot",...]
    python tools/overflow/plan.py --all           -> כל המסכתות, בלי בדיקת שינוי
    python tools/overflow/plan.py --now shabbat                 -> החותמת לפני הסבב
    python tools/overflow/plan.py --stamp shabbat --value <חותמת>  -> נכתבת אחרי סבב שעבר
"""
import argparse, hashlib, io, json, os, re, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
ODIR = os.path.join(ROOT, 'data', 'overflow')
SITE = os.environ.get('LG_SITE') or 'https://leokmei.com/'
API = os.environ.get('LG_API') or 'https://leokmei-suggest.m7654301.workers.dev'
UA = {'User-Agent': 'leokmei-overflow/1.0'}


def all_slugs():
    src = io.open(os.path.join(ROOT, 'tools', 'build_all.py'), encoding='utf-8').read()
    m = re.search(r'^LATIN = \[(.*?)\]', src, re.S | re.M)
    return re.findall(r"'([a-z-]+)'", m.group(1))


def scope():
    cfg = json.load(io.open(os.path.join(ODIR, 'config.json'), encoding='utf-8'))
    s = cfg.get('slugs')
    lst = all_slugs() if s == 'all' else list(s)
    first = [x for x in cfg.get('first') or [] if x in lst]
    return first + [x for x in lst if x not in first]


def get(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, b''


def stamp_of(slug):
    """None = אין למסכת דף באתר"""
    st, body = get(SITE + slug + '.data.js')
    if st != 200 or len(body) < 1000:
        return None
    _, live = get(API + '/live?slug=' + slug)
    t = ''
    try:
        t = str(((json.loads(live.decode('utf-8')) or {}).get('doc') or {}).get('t') or '')
    except Exception:
        t = hashlib.sha1(live).hexdigest()[:12]
    return hashlib.sha1(body).hexdigest()[:16] + ':' + t


def stamp_fp(slug):
    # קובץ לכל מסכת: העבודות רצות במקביל, וכל אחת כותבת רק את שלה (בלי התנגשות בדחיפה)
    return os.path.join(ODIR, 'stamps', slug + '.txt')


def old_stamp(slug):
    fp = stamp_fp(slug)
    return io.open(fp, encoding='utf-8').read().strip() if os.path.exists(fp) else ''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--all', action='store_true')
    ap.add_argument('--stamp', default='')
    ap.add_argument('--value', default='', help='--stamp: החותמת שנמדדה בתחילת הסבב (--now)')
    ap.add_argument('--now', default='', help='מדפיס את החותמת הנוכחית של מסכת')
    a = ap.parse_args()
    if a.now:
        print(stamp_of(a.now) or '')
        return 0
    if a.stamp:
        s = a.value or stamp_of(a.stamp)
        if s:
            # החותמת נקבעת מן המצב שלפני ההחלה של הסבב: ההחלה עצמה משנה את /live, ולכן בסבב הבא המסכת תיבדק שוב פעם אחת,
            # תמצא שאין מה להחיל, ותיחתם. כך אין לולאה ואין דילוג על שינוי אמיתי
            os.makedirs(os.path.dirname(stamp_fp(a.stamp)), exist_ok=True)
            io.open(stamp_fp(a.stamp), 'w', encoding='utf-8', newline='\n').write(s + '\n')
            print('חותמת %s: %s' % (a.stamp, s))
        return 0
    out, skip, nopage = [], [], []
    for slug in scope():
        s = stamp_of(slug)
        if s is None:
            nopage.append(slug)
        elif a.all or old_stamp(slug) != s:
            out.append(slug)
        else:
            skip.append(slug)
    print('לסבב: %s' % ' '.join(out), file=sys.stderr)
    print('לא השתנו (מדולגות): %s' % ' '.join(skip), file=sys.stderr)
    if nopage:
        print('אין דף באתר: %s' % ' '.join(nopage), file=sys.stderr)
    print(json.dumps(out))
    return 0


if __name__ == '__main__':
    sys.exit(main())
