# -*- coding: utf-8 -*-
"""build_static.py - עמודים סטטיים לגוגל (מנה 3 מתוך 3, סעיף ה, 7.10.2026).

הבעיה שנמדדה: הטקסט של דף המסכת נטען ב-JavaScript בלבד (המשתנה DATA), ולכן גוגל
שאינו מריץ את הסקריפט במלואו רואה דף כמעט ריק. כאן נכתב לכל עמוד גמרא עמוד HTML
סטטי ובו הטקסט עצמו, בכתובת קבועה וקריאה (leokmei.com/berakhot/2a.html), ולכל מסכת
עמוד אינדקס (leokmei.com/berakhot/). נוסף דף "קיצור הדף היומי" בכתובת קבועה.

הטקסט הסטטי הוא אותו טקסט שבדף האינטראקטיבי (בלי ניקוד ובלי עיצוב), והעמוד מפנה
אל הדף האינטראקטיבי המלא. הנתונים נקראים מ-site/<מסכת>.html, כך שאין מקור שני לאמת.

פרומפט 10 (28.10.2026) - גוגל:
א. עמוד שנחתך בוורד לשני חלקים רצופים (15b ואחריו שוב 15b) מתאחד לדף אחד בכתובת
   הנקייה. הכתובת הישנה 15b-2.html נשארת כדף מפנה (קנוני + רענון מיידי), כי GitHub
   Pages אינו יודע 301. חזרה שאינה רצופה (אותו עמוד שמופיע שוב בהמשך המסכת, למשל
   סנהדרין שנבנית משני קבצים חופפים) נשארת בכתובת -N עם קנוני לדף הראשי, ומחוץ
   למפת האתר ולניווט.
ב. דף שיש בו פחות מ-MIN_TEXT תווי טקסט מסומן noindex ואינו נכנס למפת האתר.
ג. lastmod אמיתי: מרשם data/seo/lastmod.json שומר לכל דף טביעת תוכן ותאריך; התאריך
   מתחלף רק כשהתוכן עצמו השתנה. השומר בענן דוחף את המרשם אחרי כל בנייה.
ד. קישורים רגילים בכל דף: קודם, הבא, דפים קרובים, המסכת, מפת הש"ס, הבית, קיצור הדף
   היומי, ובתחתית נ"ך המפורש וממלכת הזוהר.
"""
import os, io, re, json, html, hashlib, datetime

BASE = 'https://leokmei.com'
NAME = 'לאוקמי גירסא'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(ROOT, 'data', 'seo', 'lastmod.json')
MIN_TEXT = 300          # פחות מזה - דף חלש: noindex ומחוץ למפת האתר
NEAR = 5                # "דפים קרובים": חמישה לפני וחמישה אחרי
DAF_YOMI = 'hadaf-hayomi.html'
AUTHOR = {'@type': 'Person', 'name': 'הרב מיכאל פלעג'}
PUBLISHER = {'@type': 'Organization', 'name': 'מכון לאוקמי גירסא', 'url': BASE + '/',
             'logo': {'@type': 'ImageObject', 'url': BASE + '/brand/icons/lamed-600.png'}}
NACH = 'https://nach.leokmei.com/'
ZOHAR = 'https://xn--8dbacdxfna0hp.com/'
TAG = re.compile(r'<[^>]+>')
GEM = {'א': 1, 'ב': 2, 'ג': 3, 'ד': 4, 'ה': 5, 'ו': 6, 'ז': 7, 'ח': 8, 'ט': 9, 'י': 10, 'כ': 20, 'ל': 30, 'מ': 40,
       'נ': 50, 'ס': 60, 'ע': 70, 'פ': 80, 'צ': 90, 'ק': 100, 'ר': 200, 'ש': 300, 'ת': 400}

CSS = ('@font-face{font-family:LGVilnaXB;src:url(/fonts/vilna-xb.woff2) format("woff2");font-display:swap}'
       ':root{--foil:linear-gradient(170deg,#fbe7a1,#e6bd52 30%,#c38f2a 55%,#efcf6b 75%,#b07c1f);--glow:drop-shadow(0 1px 0 rgba(0,0,0,.7)) drop-shadow(0 0 6px rgba(240,196,90,.45))}'
       'html{background:#060f18}body{margin:0;min-height:100vh;display:flex;flex-direction:column;color:#1d1a16;font:19px/1.75 "Frank Ruhl Libre",Frank,serif;'
       'background:radial-gradient(ellipse 80% 60% at 50% 20%,#102a42,#091827 55%,#060f18);background-color:#060f18}'
       'header{background:#0b1c2a;border-bottom:1px solid #8f6a1e;box-shadow:0 4px 14px rgba(0,0,0,.28);color:#e9c35a;padding:8px 18px;display:flex;align-items:center;gap:18px;flex-wrap:wrap}'
       'header a{color:#e9c35a;text-decoration:none;font-weight:700;font-size:17px}header a.lg{display:inline-flex;align-items:center;gap:8px;font:400 25px/1.1 LGVilnaXB,serif;'
       'background:var(--foil);-webkit-background-clip:text;background-clip:text;color:transparent;filter:var(--glow)}header a.lg img{height:34px;width:auto;-webkit-text-fill-color:initial}'
       'main{flex:1 0 auto;box-sizing:border-box;width:100%;max-width:760px;margin:22px auto 30px;padding:22px 24px 40px;background:#f7f3ea;border-radius:6px;'
       'box-shadow:0 0 0 1px #8f6a1e,0 0 0 5px #0f263b,0 0 0 6px rgba(209,162,58,.55),0 10px 26px rgba(0,0,0,.5)}'
       'h1{font-size:30px;margin:.2em 0}h2{font-size:23px;margin:1.4em 0 .3em;border-bottom:1px solid #c9bfa8}'
       'h3{font-size:19px;margin:1em 0 .2em;color:#5a4a2a}p{margin:.35em 0}p strong{color:#7a5a14}a{color:#7a5a14}'
       'nav.crumbs,nav.pn{font-size:16px;margin:8px 0}nav.pn{display:flex;justify-content:space-between;margin-top:28px}'
       '.cta{display:inline-block;background:linear-gradient(180deg,#fbe9a6,#eccb63 38%,#c8942c 62%,#b98522);color:#2a1c04;border:1px solid #6e4f12;padding:8px 18px;border-radius:7px;font-weight:700;text-decoration:none;margin:6px 0;'
       'box-shadow:inset 0 1px 0 rgba(255,250,225,.9),0 3px 0 #5c410d}'
       '.note{font-size:15px;color:#6a5f4d}ul.dafs{columns:3;list-style:none;padding:0}ul.dafs a{display:block;padding:2px 0}'
       'nav.near{margin-top:22px;padding-top:10px;border-top:1px solid #c9bfa8;font-size:16px}nav.near h2{font-size:17px;border:0;margin:0 0 4px;color:#5a4a2a}'
       'nav.near ul{list-style:none;padding:0;margin:0;display:flex;flex-wrap:wrap;gap:4px 14px}nav.near b{color:#1d1a16}'
       'nav.more{font-size:15px;margin-top:14px;color:#6a5f4d}'
       '.today{background:#efe6cf;border-right:4px solid #b98522;padding:8px 14px;margin:10px 0;border-radius:4px}'
       'footer.sf{text-align:center;color:#c9bd98;font-size:15px;padding:16px 18px 22px;border-top:1px solid #8f6a1e}footer.sf a{color:#e9c35a}'
       '@media(max-width:560px){main{margin:14px 10px 24px;width:auto;padding:16px 14px 30px}ul.dafs{columns:2}}')

FOOTER = ('<footer class="sf"><a href="/">%s - קיצור התלמוד הבבלי</a> · <a href="/%s">קיצור הדף היומי</a> · '
          '<a href="/shas.html">מפת הש"ס</a> · <a href="/about.html">אודות</a><br>'
          'אתרים נוספים של המכון: <a href="%s">נ״ך המפורש</a> · <a href="%s">ממלכת הזוהר</a></footer>') % (NAME, DAF_YOMI, NACH, ZOHAR)


def esc(s):
    return html.escape(s, quote=True)


def plain(s):
    return re.sub(r'\s+', ' ', html.unescape(TAG.sub('', s or ''))).strip()


def gem(t):
    return sum(GEM.get(c, 0) for c in re.sub(r'[^א-ת]', '', t))


def daf_path(daf):
    """'ב.' -> '2a', 'ב:' -> '2b' ; מחזיר None אם אין ציון תקין."""
    n = gem(daf)
    if not n:
        return None
    return '%d%s' % (n, 'b' if daf.strip().endswith(':') else 'a')


def daf_words(daf):
    """'ב.' -> 'דף ב עמוד א' ; 'ב:' -> 'דף ב עמוד ב'."""
    t = re.sub(r'[.:\s]', '', daf)
    return 'דף %s עמוד %s' % (t, 'ב' if daf.strip().endswith(':') else 'א')


def heb_num(n):
    t = ''
    for v, c in ((400, 'ת'), (300, 'ש'), (200, 'ר'), (100, 'ק'), (90, 'צ'), (80, 'פ'), (70, 'ע'), (60, 'ס'), (50, 'נ'),
                 (40, 'מ'), (30, 'ל'), (20, 'כ'), (10, 'י'), (9, 'ט'), (8, 'ח'), (7, 'ז'), (6, 'ו'), (5, 'ה'), (4, 'ד'),
                 (3, 'ג'), (2, 'ב'), (1, 'א')):
        while n >= v:
            t += c
            n -= v
    return t.replace('יה', 'טו').replace('יו', 'טז')


def heb_q(n):
    """מספר באותיות עם גרש או גרשיים, כמו HD.q בדפדפן: ג', י"ז, תשפ"ז."""
    t = heb_num(n)
    return t[:-1] + '"' + t[-1] if len(t) > 1 else t + "'"


# ------------------------------------------------------------ תאריך עברי
# חשבון הלוח העברי (דרשוביץ-ריינגולד). נבדק מול Intl של הדפדפן על אלף וחמש מאות
# תאריכים (2019-2030). שמות החודשים - כמו ב-Intl, כדי שהדף הסטטי והדפדפן יסכימו.
_EPOCH = -1373427   # א' תשרי שנה א, במניין הימים של date.toordinal()


def _leap(y):
    return (7 * y + 1) % 19 < 7


def _elapsed(y):
    months = (235 * y - 234) // 19
    parts = 12084 + 13753 * months
    day = months * 29 + parts // 25920
    return day + 1 if (3 * (day + 1)) % 7 < 3 else day


def _new_year(y):
    ny0, ny1, ny2 = _elapsed(y - 1), _elapsed(y), _elapsed(y + 1)
    corr = 2 if ny2 - ny1 == 356 else (1 if ny1 - ny0 == 382 else 0)
    return _EPOCH + ny1 + corr


def _month_len(m, y):
    days = _new_year(y + 1) - _new_year(y)
    if m in (2, 4, 6, 10, 13) or (m == 12 and not _leap(y)):
        return 29
    if m == 8 and days % 10 != 5:       # חשוון מלא רק בשנה שלמה (355/385)
        return 29
    if m == 9 and days % 10 == 3:       # כסלו חסר בשנה חסרה (353/383)
        return 29
    return 30


def heb_parts(d):
    """date -> (יום, שם החודש, שנה)."""
    fixed = d.toordinal()
    y = (fixed - _EPOCH) * 98496 // 35975351 - 1
    while _new_year(y + 1) <= fixed:
        y += 1
    order = [7, 8, 9, 10, 11, 12] + ([13] if _leap(y) else []) + [1, 2, 3, 4, 5, 6]
    left = fixed - _new_year(y)
    for m in order:
        ml = _month_len(m, y)
        if left < ml:
            break
        left -= ml
    names = {7: 'תשרי', 8: 'חשוון', 9: 'כסלו', 10: 'טבת', 11: 'שבט', 12: 'אדר', 13: 'אדר ב׳', 1: 'ניסן',
             2: 'אייר', 3: 'סיוון', 4: 'תמוז', 5: 'אב', 6: 'אלול'}
    name = names[m]
    if m == 12 and _leap(y):
        name = 'אדר א׳'
    return left + 1, name, y


def heb_date(d):
    day, month, year = heb_parts(d)
    return '%s %s %s' % (heb_q(day), month, heb_q(year % 1000))


def il_today():
    """התאריך בישראל. הבנייה רצה בענן לפי שעון UTC, והדף היומי מתחלף בחצות ירושלים."""
    try:
        from zoneinfo import ZoneInfo
        return datetime.datetime.now(ZoneInfo('Asia/Jerusalem')).date()
    except Exception:
        return (datetime.datetime.utcnow() + datetime.timedelta(hours=2)).date()


# ------------------------------------------------------------ נתונים

def load_data(path):
    import pagedata
    h = pagedata.read_html(path)
    i = h.find('const DATA=')
    if i < 0:
        return None
    D, _ = json.JSONDecoder().raw_decode(h[i + len('const DATA='):])
    return D


def page_groups(D):
    """מחלק את עמודי המסכת לדפים באינטרנט.

    מחזיר (mains, alts, stubs):
    mains - [{'dp','daf','idx':[...]}] לפי סדר המסכת; כל רצף צמוד של אותו עמוד מתאחד.
    alts  - [{'name','dp','daf','idx':[...]}] חזרה שאינה צמודה: נשארת בשמה הישן, קנונית לראשי.
    stubs - [(name, dp)] כתובות -N ישנות של חלק שאוחד: דף מפנה לראשי.
    השמות הישנים נשמרים כפי שנקבעו עד היום (מונה ההופעות של אותו עמוד), כדי
    שכל כתובת שגוגל כבר מכיר תמשיך להוביל למקום הנכון."""
    mains, alts, stubs = [], [], []
    by_dp, count = {}, {}
    cur, prev = None, None
    for i, p in enumerate(D['pages']):
        dp = daf_path(p.get('daf', ''))
        if not dp:
            continue
        count[dp] = count.get(dp, 0) + 1
        old = dp if count[dp] == 1 else '%s-%d' % (dp, count[dp])
        if dp == prev and cur is not None:
            cur['idx'].append(i)
            stubs.append((old, dp))
        elif dp in by_dp:
            cur = {'name': old, 'dp': dp, 'daf': p['daf'], 'idx': [i]}
            alts.append(cur)
        else:
            cur = {'dp': dp, 'daf': p['daf'], 'idx': [i]}
            by_dp[dp] = cur
            mains.append(cur)
        prev = dp
    return mains, alts, stubs


def amud_body(page):
    """הטקסט של עמוד אחד, כסדרו: כותרות פרק, ד"ה, נושא, ופסקאות עם תווית הדובר."""
    out = []
    for u in page['units']:
        k = u['k']
        a = plain(u.get('a', '')).strip()
        lines = [plain(l[1]) for l in u.get('l', [])]
        lines = [x for x in lines if x]
        if k == 'perek-start':
            out.append('<h2>%s</h2>' % esc(a))
        elif k == 'perek-range' or k == 'hadran':
            continue
        elif k == 'dh':
            out.append('<h3>%s</h3>' % esc(a))
        elif k == 'nose':
            out.append('<h3>%s</h3>' % esc(a or ' '.join(lines)))
        elif k == 'hatz':
            continue
        else:
            if a and a not in ('-', '°'):
                if lines:
                    lines[0] = '<strong>%s</strong> %s' % (esc(a), esc(lines[0]))
                    out.append('<p>%s</p>' % lines[0])
                    out.extend('<p>%s</p>' % esc(x) for x in lines[1:])
                else:
                    out.append('<p><strong>%s</strong></p>' % esc(a))
            else:
                out.extend('<p>%s</p>' % esc(x) for x in lines)
    return '\n'.join(out)


def amud_text(page):
    t = []
    for u in page['units']:
        if u['k'] in ('perek-range', 'hadran', 'hatz'):
            continue
        t.append(plain(u.get('a', '')))
        t.extend(plain(l[1]) for l in u.get('l', []))
    return re.sub(r'\s+', ' ', ' '.join(x for x in t if x)).strip()


def group_body(D, g):
    return '\n'.join(amud_body(D['pages'][i]) for i in g['idx'])


def group_text(D, g):
    return ' '.join(amud_text(D['pages'][i]) for i in g['idx']).strip()


def content_hash(body):
    return hashlib.sha1(body.encode('utf-8')).hexdigest()[:16]


# ------------------------------------------------------------ מרשם התאריכים

def load_ledger():
    try:
        return json.load(io.open(LEDGER, encoding='utf-8'))
    except Exception:
        return {}


def save_ledger(led):
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    tmp = LEDGER + '.tmp'
    with io.open(tmp, 'w', encoding='utf-8') as f:
        json.dump(led, f, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
        f.write('\n')
    os.replace(tmp, LEDGER)


CHANGED = []    # דפים שתוכנם השתנה בבנייה הזאת - נשלחים לבינג (tools/indexnow.py --changed)


def stamp(led, key, h, today):
    """מחזיר (שונה-לאחרונה, פורסם-לראשונה). התאריך מתחלף רק כשטביעת התוכן השתנתה."""
    rec = led.get(key)
    if not rec:
        led[key] = [h, today, today]
        CHANGED.append(key + '.html')
    elif rec[0] != h:
        led[key] = [h, today, rec[2] if len(rec) > 2 else rec[1]]
        CHANGED.append(key + '.html')
    rec = led[key]
    return rec[1], rec[2] if len(rec) > 2 else rec[1]


# ------------------------------------------------------------ תבנית הדף

def head(title, desc, url, ld, robots=None, canonical=None, og_type='article'):
    return ('<!DOCTYPE html><html lang="he" dir="rtl"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>%s</title><meta name="description" content="%s">'
            '<link rel="canonical" href="%s">%s'
            '<meta property="og:type" content="%s"><meta property="og:locale" content="he_IL">'
            '<meta property="og:site_name" content="%s"><meta property="og:title" content="%s">'
            '<meta property="og:description" content="%s"><meta property="og:url" content="%s">'
            '<meta property="og:image" content="https://leokmei.com/brand/og-image.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">'
            '<meta property="og:image:alt" content="לאוקמי גירסא - קיצור התלמוד הבבלי"><meta name="twitter:card" content="summary_large_image">'
            '<link rel="icon" href="/favicon.ico" sizes="any"><link rel="icon" type="image/png" sizes="32x32" href="/brand/icons/favicon-32.png">'
            '<link rel="icon" type="image/svg+xml" href="/brand/icons/favicon.svg"><link rel="mask-icon" href="/brand/icons/mask-icon.svg" color="#0b1c2a">'
            '<link rel="apple-touch-icon" href="/brand/icons/apple-touch-icon.png"><link rel="manifest" href="/manifest.webmanifest"><meta name="theme-color" content="#0b1c2a">'
            '<script>(function(){var h=location.hash;if(h.slice(0,3)!=="#go")return;'
            'document.addEventListener("DOMContentLoaded",function(){var a=document.querySelector("a.cta");if(a)location.replace(a.getAttribute("href")+h.slice(3))})})()</script>'
            '<script type="application/ld+json">%s</script><style>%s</style></head><body>'
            '<header><a class="lg" href="/"><img src="/brand/shaar-v2/shaar-zohar-96.webp" alt="">%s</a><a href="/%s">קיצור הדף היומי</a>'
            '<a href="/masechtot.html">כל המסכתות</a><a href="/shas.html">מפת הש"ס</a></header>'
            % (esc(title), esc(desc), canonical or url,
               ('<meta name="robots" content="%s">' % robots) if robots else '',
               og_type, NAME, esc(title), esc(desc), url, json.dumps(ld, ensure_ascii=False), CSS, NAME, DAF_YOMI))


def redirect_page(target, title):
    """דף מפנה לכתובת -N של חלק שאוחד. GitHub Pages אינו יודע 301; רענון מיידי עם
    קנוני הוא הדרך שגוגל מתייחס אליה כהפניה קבועה."""
    return ('<!DOCTYPE html><html lang="he" dir="rtl"><head><meta charset="utf-8"><title>%s</title>'
            '<link rel="canonical" href="%s%s"><meta http-equiv="refresh" content="0; url=%s">'
            '<script>location.replace("%s"+location.hash)</script></head><body>'
            '<p>העמוד אוחד: <a href="%s">%s</a></p></body></html>') % (esc(title), BASE, target, target, target, target, esc(title))


def crumbs_ld(items):
    return {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': n + 1, 'name': nm, 'item': it} for n, (nm, it) in enumerate(items)]}


def first_line(txt, n=150):
    t = txt[:n]
    if len(txt) > n:
        t = t.rsplit(' ', 1)[0] + '…'
    return t


# ------------------------------------------------------------ הדף היומי

def daf_yomi_rows(site):
    """הלוח נקרא מ-daf-yomi.js עצמו, כדי שלא יהיה מקור שני."""
    src = io.open(os.path.join(site, 'daf-yomi.js'), encoding='utf-8').read()
    return [(nm, sl, int(st), int(ln)) for nm, sl, st, ln in re.findall(r"\['([^']+)','([a-z\-]+)',(\d+),(\d+)\]", src)]


def daf_for(rows, d):
    cyc = sum(r[3] for r in rows)
    k = (d - datetime.date(2020, 1, 5)).days % cyc
    for nm, sl, st, ln in rows:
        if k < ln:
            return nm, sl, st + k
        k -= ln
    return None


def write_daf_yomi(site, pages_by_slug, today):
    """דף "קיצור הדף היומי": כתובת קבועה, מתחלף בכל בנייה (השומר בונה כל חצי שעה).
    בדפדפן הסקריפט מתקן לדף של היום לפי השעון המקומי, אם הבנייה קדמה לחצות."""
    rows = daf_yomi_rows(site)
    pick = daf_for(rows, today)
    if not pick:
        return None
    nm, sl, n = pick
    have = pages_by_slug.get(sl, {})
    url = BASE + '/' + DAF_YOMI
    hd = heb_date(today)
    amudim = [('%da' % n, heb_num(n) + '.'), ('%db' % n, heb_num(n) + ':')]
    body_html, line, links = '', '', []
    for dp, daf in amudim:
        g = have.get(dp)
        if not g:
            continue
        links.append('<a href="/%s/%s.html">%s %s</a>' % (sl, dp, esc(nm), esc(daf_words(daf))))
        body_html += '<h2><a href="/%s/%s.html">%s %s</a></h2>%s' % (sl, dp, esc(nm), esc(daf_words(daf)), g['body'])
        if not line:
            line = first_line(g['text'])
    week = []
    for back in range(1, 8):
        d = today - datetime.timedelta(days=back)
        p = daf_for(rows, d)
        if not p:
            continue
        wn, ws, wd = p
        lab = '%s - %s דף %s' % (heb_date(d), wn, heb_num(wd))
        if '%da' % wd in pages_by_slug.get(ws, {}):
            week.append('<li><a href="/%s/%da.html">%s</a></li>' % (ws, wd, esc(lab)))
        else:
            week.append('<li>%s <span class="note">(עדיין אינו באתר)</span></li>' % esc(lab))
    title = 'קיצור הדף היומי - %s דף %s | %s' % (nm, heb_num(n), NAME)
    desc = ('קיצור הדף היומי של היום, %s: מסכת %s דף %s בקיצור. %s' % (hd, nm, heb_num(n), line))[:250]
    ld = [{'@context': 'https://schema.org', '@type': 'WebPage', 'name': 'קיצור הדף היומי', 'headline': title, 'url': url,
           'inLanguage': 'he', 'dateModified': today.isoformat(), 'description': desc, 'author': AUTHOR, 'publisher': PUBLISHER,
           'isPartOf': {'@type': 'WebSite', 'name': NAME, 'url': BASE + '/'}},
          crumbs_ld([(NAME, BASE + '/'), ('קיצור הדף היומי', url)])]
    today_box = ('<div class="today" id="hy-top"><p>היום, <b id="hy-date">%s</b>: <b>מסכת %s דף %s</b></p>'
                 '<p id="hy-links">%s</p>%s</div>') % (
        esc(hd), esc(nm), esc(heb_num(n)),
        ' · '.join(links) if links else 'הדף של היום עדיין אינו באתר בקיצור. <a href="/masechtot.html">לכל המסכתות</a>',
        ('<p id="hy-line" class="note">״%s״</p>' % esc(line)) if line else '')
    page = head(title, desc, url, ld, og_type='website') + (
        '<main><nav class="crumbs"><a href="/">%s</a> › קיצור הדף היומי</nav>'
        '<h1>קיצור הדף היומי</h1>%s'
        '<p class="note">הדף היומי בקיצור לאוקמי גירסא - קיצור התלמוד הבבלי, דף אחר דף. הכתובת קבועה, והדף מתחלף מדי יום.</p>'
        '<div id="hy">%s</div>'
        '<nav class="near"><h2>השבוע האחרון בדף היומי</h2><ul style="display:block">%s</ul></nav>'
        '<nav class="more"><a href="/%s/">מסכת %s בקיצור - כל הדפים</a> · <a href="/masechtot.html">כל המסכתות</a> · '
        '<a href="/shas.html">מפת הש"ס</a> · <a href="/yomi.html">לוח הדף היומי ומעקב לימוד</a></nav></main>'
        '%s<script src="/hdate.js"></script><script src="/daf-yomi.js"></script><script>(function(){try{'
        'var now=new Date();var p=window.HD&&HD.parts?HD.parts(now):null;var ymd=new Intl.DateTimeFormat("en-CA",{timeZone:"Asia/Jerusalem"}).format(now);'
        'var t=LGDaf.forStr(ymd);if(window.HD)document.getElementById("hy-date").textContent=HD.date(now);'
        'if(!t||(t.slug==="%s"&&t.n===%d))return;'
        'var A=[[t.n+"a",LGDaf.heb(t.n)+"."],[t.n+"b",LGDaf.heb(t.n)+":"]];'
        'Promise.all(A.map(function(x){return fetch("/"+t.slug+"/"+x[0]+".html").then(function(r){return r.ok?r.text():""})})).then(function(H){'
        'var out="",ln=[];H.forEach(function(h,i){var m=h.match(/<h1>(.*?)<\\/h1>([\\s\\S]*?)<p class="note">קיצור/);if(!m)return;'
        'var u="/"+t.slug+"/"+A[i][0]+".html";ln.push("<a href=\\""+u+"\\">"+m[1]+"</a>");'
        'out+="<h2><a href=\\""+u+"\\">"+m[1]+"</a></h2>"+m[2].replace(/<p><a class="cta"[\\s\\S]*?<\\/p>/,"")});'
        'document.getElementById("hy").innerHTML=out;var l=document.getElementById("hy-line");if(l)l.remove();'
        'document.getElementById("hy-links").innerHTML=ln.join(" · ")||"הדף של היום ("+t.name+" "+t.daf+") עדיין אינו באתר בקיצור.";'
        'document.title="קיצור הדף היומי - "+t.name+" דף "+t.label+" | %s"})}catch(e){}})();</script></body></html>'
    ) % (NAME, today_box, body_html or '', ''.join(week), sl, esc(nm), FOOTER, sl, n, NAME)
    io.open(os.path.join(site, DAF_YOMI), 'w', encoding='utf-8').write(page)
    return nm, sl, n


# ------------------------------------------------------------ הבנייה

def run(site, built, slug):
    """כותב את העמודים הסטטיים ומחזיר רשימת כתובות למפת האתר:
    [(נתיב, עדיפות, lastmod או None, קבוצה)] - הקבוצה היא slug המסכת או 'main'."""
    urls = []
    today = il_today()
    tiso = today.isoformat()
    led = load_ledger()
    led_before = json.dumps(led, sort_keys=True)
    total = merged = weak_n = alt_n = 0
    weak, report = [], {'merged': [], 'alts': [], 'weak': []}
    pages_by_slug = {}
    masechet_lastmod = {}
    for m in built:
        sl = slug[m]
        D = load_data(os.path.join(site, sl + '.html'))
        if not D or 'pages' not in D:
            print('אזהרה: למסכת %s אין נתונים, לא נבנו עמודים סטטיים' % m)
            continue
        d = os.path.join(site, sl)
        os.makedirs(d, exist_ok=True)
        mains, alts, stubs = page_groups(D)
        mc = 'מסכת ' + m
        mc_url = '%s/%s/' % (BASE, sl)
        for g in mains:
            g['body'] = group_body(D, g)
            g['text'] = group_text(D, g)
        pages_by_slug[sl] = {g['dp']: g for g in mains}
        dates = []
        for n, g in enumerate(mains):
            dp, daf = g['dp'], g['daf']
            p = D['pages'][g['idx'][0]]
            title = '%s - %s %s בקיצור - קיצור הדף היומי' % (NAME, m, daf_words(daf))
            txt = g['text']
            desc = ('%s %s בקיצור: %s' % (m, daf_words(daf), first_line(txt, 130))).strip()
            url = '%s/%s/%s.html' % (BASE, sl, dp)
            lm, pub = stamp(led, '%s/%s' % (sl, dp), content_hash(g['body']), tiso)
            dates.append(lm)
            is_weak = len(txt) < MIN_TEXT
            perek = p.get('perek', '')
            ld = [{'@context': 'https://schema.org', '@type': ['Article', 'LearningResource'],
                   'headline': '%s %s בקיצור' % (m, daf_words(daf)), 'name': title, 'inLanguage': 'he', 'url': url,
                   'mainEntityOfPage': url, 'datePublished': pub, 'dateModified': lm, 'description': desc[:200],
                   'image': BASE + '/brand/og-image.png', 'learningResourceType': 'סיכום',
                   'about': 'תלמוד בבלי, %s, %s' % (mc, daf_words(daf)),
                   'isPartOf': {'@type': 'Book', 'name': mc + ' בקיצור', 'url': mc_url},
                   'author': AUTHOR, 'publisher': PUBLISHER},
                  crumbs_ld([(NAME, BASE + '/'), (mc, mc_url), (daf_words(daf), url)])]
            prv = mains[n - 1] if n else None
            nxt = mains[n + 1] if n + 1 < len(mains) else None
            pn = '<nav class="pn"><span>%s</span><span>%s</span></nav>' % (
                ('<a href="/%s/%s.html" rel="next">%s ›</a>' % (sl, nxt['dp'], esc(daf_words(nxt['daf'])))) if nxt else '',
                ('<a href="/%s/%s.html" rel="prev">‹ %s</a>' % (sl, prv['dp'], esc(daf_words(prv['daf'])))) if prv else '')
            near = []
            for k in range(max(0, n - NEAR), min(len(mains), n + NEAR + 1)):
                o = mains[k]
                lab = esc(daf_words(o['daf']))
                near.append('<li><b>%s</b></li>' % lab if k == n else '<li><a href="/%s/%s.html">%s</a></li>' % (sl, o['dp'], lab))
            body = ('<main><nav class="crumbs"><a href="/">%s</a> › <a href="/%s/">%s</a> › %s</nav>'
                    '<h1>%s %s</h1>%s'
                    '<p><a class="cta" href="/%s.html#daf=%s">ללימוד אינטראקטיבי של הדף</a></p>'
                    '%s'
                    '<p class="note">קיצור התלמוד הבבלי, דף אחר דף. '
                    '<a href="/quiz.html?m=%s">בחן את עצמך על %s</a> · <a href="/%s">קיצור הדף היומי</a></p>%s'
                    '<nav class="near"><h2>דפים קרובים ב%s</h2><ul>%s</ul></nav>'
                    '<nav class="more"><a href="/%s/">%s בקיצור - כל הדפים</a> · <a href="/shas.html">מפת הש"ס</a> · '
                    '<a href="/">דף הבית</a></nav></main>%s</body></html>') % (
                NAME, sl, esc(mc), esc(daf_words(daf)), esc(m), esc(daf_words(daf)),
                ('<p class="note">%s</p>' % esc(perek)) if perek else '',
                sl, esc(daf), g['body'], sl, esc(mc), DAF_YOMI, pn,
                esc(mc), ''.join(near), sl, esc(mc), FOOTER)
            io.open(os.path.join(d, dp + '.html'), 'w', encoding='utf-8').write(
                head(title, desc, url, ld, robots='noindex,follow' if is_weak else None) + body)
            total += 1
            if is_weak:
                weak_n += 1
                report['weak'].append([sl + '/' + dp + '.html', len(txt)])
            else:
                urls.append(('%s/%s.html' % (sl, dp), '0.6', lm, sl))
            if len(g['idx']) > 1:
                merged += len(g['idx']) - 1
        # חזרה שאינה צמודה: הדף נשאר בשמו, קנוני לראשי, מחוץ למפה ולניווט
        main_by = {g['dp']: g for g in mains}
        for a in alts:
            g = main_by[a['dp']]
            body = group_body(D, a)
            url_main = '%s/%s/%s.html' % (BASE, sl, a['dp'])
            title = '%s - %s %s בקיצור - קיצור הדף היומי' % (NAME, m, daf_words(a['daf']))
            desc = ('%s %s בקיצור: %s' % (m, daf_words(a['daf']), first_line(group_text(D, a), 130))).strip()
            html_ = head(title, desc, '%s/%s/%s.html' % (BASE, sl, a['name']), crumbs_ld([(NAME, BASE + '/'), (mc, mc_url), (daf_words(a['daf']), url_main)]),
                         canonical=url_main) + (
                '<main><nav class="crumbs"><a href="/">%s</a> › <a href="/%s/">%s</a> › <a href="/%s/%s.html">%s</a></nav>'
                '<h1>%s %s</h1><p class="note">נוסח נוסף של העמוד. <a href="/%s/%s.html">לדף הראשי</a></p>%s'
                '<nav class="more"><a href="/%s/">%s בקיצור - כל הדפים</a> · <a href="/">דף הבית</a></nav></main>%s</body></html>') % (
                NAME, sl, esc(mc), sl, a['dp'], esc(daf_words(a['daf'])), esc(m), esc(daf_words(a['daf'])),
                sl, a['dp'], body, sl, esc(mc), FOOTER)
            io.open(os.path.join(d, a['name'] + '.html'), 'w', encoding='utf-8').write(html_)
            alt_n += 1
            report['alts'].append(sl + '/' + a['name'] + '.html')
        for name, dp in stubs:
            io.open(os.path.join(d, name + '.html'), 'w', encoding='utf-8').write(
                redirect_page('/%s/%s.html' % (sl, dp), '%s %s' % (m, daf_words(main_by[dp]['daf']))))
            report['merged'].append(sl + '/' + name + '.html')
        # אינדקס המסכת: רשימת כל העמודים, מקובצת לפי פרק
        groups = []
        for g in mains:
            pk = D['pages'][g['idx'][0]].get('perek', '') or 'כל המסכת'
            if not groups or groups[-1][0] != pk:
                groups.append((pk, []))
            groups[-1][1].append((g['dp'], g['daf']))
        title = '%s בקיצור - כל הדפים | %s' % (mc, NAME)
        desc = '%s בקיצור (קיצור התלמוד הבבלי): כל דפי המסכת, דף אחר דף, מקובצים לפי פרקים. קיצור הדף היומי ולימוד אינטראקטיבי.' % mc
        mlm = max(dates) if dates else tiso
        masechet_lastmod[sl] = mlm
        ld = [{'@context': 'https://schema.org', '@type': 'CollectionPage', 'name': title, 'url': mc_url, 'inLanguage': 'he',
               'dateModified': mlm, 'author': AUTHOR, 'publisher': PUBLISHER,
               'isPartOf': {'@type': 'WebSite', 'name': NAME, 'url': BASE + '/'}},
              crumbs_ld([(NAME, BASE + '/'), (mc, mc_url)])]
        body = ('<main><nav class="crumbs"><a href="/">%s</a> › %s</nav><h1>%s בקיצור</h1>'
                '<p>קיצור התלמוד הבבלי, דף אחר דף. <a class="cta" href="/%s.html">ללימוד האינטראקטיבי</a></p>') % (NAME, esc(mc), esc(mc), sl)
        for pk, ds in groups:
            body += '<h2>%s</h2><ul class="dafs">%s</ul>' % (esc(pk), ''.join('<li><a href="/%s/%s.html">%s</a></li>' % (sl, dp, esc(daf_words(df))) for dp, df in ds))
        body += ('<nav class="more"><a href="/%s">קיצור הדף היומי</a> · <a href="/masechtot.html">כל המסכתות</a> · '
                 '<a href="/shas.html">מפת הש"ס</a> · <a href="/">דף הבית</a></nav></main>%s</body></html>') % (DAF_YOMI, FOOTER)
        io.open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(head(title, desc, mc_url, ld, og_type='website') + body)
        urls.append((sl + '/', '0.7', mlm, sl))
    try:
        r = write_daf_yomi(site, pages_by_slug, today)
        if r:
            urls.append((DAF_YOMI, '0.9', tiso, 'main'))
    except Exception as e:
        print('אזהרה: דף "קיצור הדף היומי" לא נבנה:', e)
    if json.dumps(led, sort_keys=True) != led_before:
        save_ledger(led)
    report['changed'] = CHANGED + ([DAF_YOMI] if any(u[0] == DAF_YOMI for u in urls) else [])
    report.update({'time': tiso, 'pages': total, 'merged_parts': merged, 'alt_pages': alt_n, 'weak_pages': weak_n,
                   'min_text': MIN_TEXT})
    io.open(os.path.join(site, 'seo-report.json'), 'w', encoding='utf-8').write(json.dumps(report, ensure_ascii=False, indent=0))
    print('עמודים סטטיים: %d עמודי גמרא, %d מסכתות; אוחדו %d חלקים, %d נוסחים נוספים (קנוני), %d דפים חלשים (noindex)'
          % (total, len(built), merged, alt_n, weak_n))
    return urls, masechet_lastmod
