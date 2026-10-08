# -*- coding: utf-8 -*-
"""build_static.py - עמודים סטטיים לגוגל (מנה 3 מתוך 3, סעיף ה, 7.10.2026).

הבעיה שנמדדה: הטקסט של דף המסכת נטען ב-JavaScript בלבד (המשתנה DATA), ולכן גוגל
שאינו מריץ את הסקריפט במלואו רואה דף כמעט ריק. כאן נכתב לכל עמוד גמרא עמוד HTML
סטטי ובו הטקסט עצמו, בכתובת קבועה וקריאה (leokmei.com/berakhot/2a.html), ולכל מסכת
עמוד אינדקס (leokmei.com/berakhot/). נוסף דף "הדף היומי היום" בכתובת קבועה.

הטקסט הסטטי הוא אותו טקסט שבדף האינטראקטיבי (בלי ניקוד ובלי עיצוב), והעמוד מפנה
אל הדף האינטראקטיבי המלא. הנתונים נקראים מ-site/<מסכת>.html, כך שאין מקור שני לאמת.
"""
import os, io, re, json, html, datetime

BASE = 'https://leokmei.com'
NAME = 'לאוקמי גירסא'
TAG = re.compile(r'<[^>]+>')
GEM = {'א': 1, 'ב': 2, 'ג': 3, 'ד': 4, 'ה': 5, 'ו': 6, 'ז': 7, 'ח': 8, 'ט': 9, 'י': 10, 'כ': 20, 'ל': 30, 'מ': 40,
       'נ': 50, 'ס': 60, 'ע': 70, 'פ': 80, 'צ': 90, 'ק': 100, 'ר': 200, 'ש': 300, 'ת': 400}

CSS = ('body{margin:0;background:#efe9d9;color:#1d1a16;font:19px/1.75 "Frank Ruhl Libre",Frank,serif}'
       'header{background:#0b1c2a;border-bottom:1px solid #8f6a1e;color:#e9c35a;padding:8px 18px;display:flex;align-items:center;gap:18px;flex-wrap:wrap}header a{color:#e9c35a;text-decoration:none;font-weight:700;font-size:17px}header a.lg{display:inline-flex;align-items:center;gap:8px;color:#f9e08a;font-size:22px}header a.lg img{height:30px;width:auto}'
       '@font-face{font-family:LGVilnaTitle;src:url(/brand/fonts/vilna-title.woff2) format("woff2");font-display:swap}header a.lg{font-family:LGVilnaTitle,serif;font-weight:400}'
       'main{max-width:760px;margin:0 auto;padding:22px 18px 60px}h1{font-size:30px;margin:.2em 0}h2{font-size:23px;margin:1.4em 0 .3em;border-bottom:1px solid #c9bfa8}'
       'h3{font-size:19px;margin:1em 0 .2em;color:#5a4a2a}p{margin:.35em 0}p strong{color:#7a5a14}a{color:#7a5a14}'
       'nav.crumbs,nav.pn{font-size:16px;margin:8px 0}nav.pn{display:flex;justify-content:space-between;margin-top:28px}'
       '.cta{display:inline-block;background:#c9a24a;color:#2b2620;padding:8px 18px;border-radius:8px;font-weight:700;text-decoration:none;margin:6px 0}'
       '.note{font-size:15px;color:#6a5f4d}ul.dafs{columns:3;list-style:none;padding:0}ul.dafs a{display:block;padding:2px 0}')


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


def load_data(path):
    h = io.open(path, encoding='utf-8').read()
    i = h.find('const DATA=')
    if i < 0:
        return None
    D, _ = json.JSONDecoder().raw_decode(h[i + len('const DATA='):])
    return D


def head(title, desc, url, ld):
    return ('<!DOCTYPE html><html lang="he" dir="rtl"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>%s</title><meta name="description" content="%s">'
            '<link rel="canonical" href="%s">'
            '<meta property="og:type" content="article"><meta property="og:locale" content="he_IL">'
            '<meta property="og:site_name" content="%s"><meta property="og:title" content="%s">'
            '<meta property="og:description" content="%s"><meta property="og:url" content="%s">'
            '<meta name="twitter:card" content="summary_large_image"><meta property="og:image" content="https://leokmei.com/brand/og-image.png">'
            '<link rel="icon" href="/favicon.ico" sizes="any"><link rel="icon" type="image/png" sizes="32x32" href="/brand/icons/favicon-32.png">'
            '<link rel="apple-touch-icon" href="/brand/icons/apple-touch-icon.png"><link rel="manifest" href="/manifest.webmanifest"><meta name="theme-color" content="#0b1c2a">'
            '<script type="application/ld+json">%s</script><style>%s</style></head><body>'
            '<header><a class="lg" href="/"><img src="/brand/shaar-zahav-96.webp" alt="">%s</a><a href="/yomi.html">הדף היומי</a><a href="/masechtot.html">כל המסכתות</a></header>'
            % (esc(title), esc(desc), url, NAME, esc(title), esc(desc), url, json.dumps(ld, ensure_ascii=False), CSS, NAME))


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


def run(site, built, slug):
    urls = []
    today = datetime.date.today().isoformat()
    total = 0
    for m in built:
        sl = slug[m]
        D = load_data(os.path.join(site, sl + '.html'))
        if not D or 'pages' not in D:
            print('אזהרה: למסכת %s אין נתונים, לא נבנו עמודים סטטיים' % m)
            continue
        d = os.path.join(site, sl)
        os.makedirs(d, exist_ok=True)
        entries = []     # (path, daf, page_index)
        seen = {}
        for i, p in enumerate(D['pages']):
            dp = daf_path(p.get('daf', ''))
            if not dp:
                continue
            seen[dp] = seen.get(dp, 0) + 1
            if seen[dp] > 1:
                dp = '%s-%d' % (dp, seen[dp])
            entries.append((dp, p['daf'], i))
        for n, (dp, daf, i) in enumerate(entries):
            p = D['pages'][i]
            title = '%s - %s %s - קיצור הדף היומי' % (NAME, m, daf_words(daf))
            txt = amud_text(p)
            desc = ('%s %s בקיצור: %s' % (m, daf_words(daf), txt[:130])).strip()
            url = '%s/%s/%s.html' % (BASE, sl, dp)
            perek = p.get('perek', '')
            ld = [{'@context': 'https://schema.org', '@type': 'Article', 'headline': '%s %s' % (m, daf_words(daf)),
                   'name': title, 'inLanguage': 'he', 'url': url, 'dateModified': today,
                   'description': desc[:200],
                   'isPartOf': {'@type': 'Book', 'name': 'מסכת %s בקיצור' % m, 'url': '%s/%s.html' % (BASE, sl)},
                   'author': {'@type': 'Organization', 'name': NAME}, 'publisher': {'@type': 'Organization', 'name': NAME, 'url': BASE + '/'}},
                  {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
                      {'@type': 'ListItem', 'position': 1, 'name': NAME, 'item': BASE + '/'},
                      {'@type': 'ListItem', 'position': 2, 'name': 'מסכת ' + m, 'item': '%s/%s/' % (BASE, sl)},
                      {'@type': 'ListItem', 'position': 3, 'name': daf_words(daf), 'item': url}]}]
            prv = entries[n - 1] if n else None
            nxt = entries[n + 1] if n + 1 < len(entries) else None
            pn = '<nav class="pn"><span>%s</span><span>%s</span></nav>' % (
                ('<a href="/%s/%s.html">%s ›</a>' % (sl, nxt[0], esc(daf_words(nxt[1])))) if nxt else '',
                ('<a href="/%s/%s.html">‹ %s</a>' % (sl, prv[0], esc(daf_words(prv[1])))) if prv else '')
            body = ('<main><nav class="crumbs"><a href="/">%s</a> › <a href="/%s/">מסכת %s</a> › %s</nav>'
                    '<h1>%s %s</h1>%s'
                    '<p><a class="cta" href="/%s.html#daf=%s">ללימוד אינטראקטיבי של הדף</a></p>'
                    '%s'
                    '<p class="note">קיצור התלמוד הבבלי, דף אחר דף. '
                    '<a href="/quiz.html?m=%s">בחן את עצמך על מסכת %s</a> · <a href="/yomi.html">הדף היומי היום</a></p>%s</main></body></html>') % (
                NAME, sl, esc(m), esc(daf_words(daf)), esc(m), esc(daf_words(daf)),
                ('<p class="note">%s</p>' % esc(perek)) if perek else '',
                sl, esc(daf), amud_body(p), sl, esc(m), pn)
            io.open(os.path.join(d, dp + '.html'), 'w', encoding='utf-8').write(head(title, desc, url, ld) + body)
            urls.append(('%s/%s.html' % (sl, dp), '0.6'))
            total += 1
        # אינדקס המסכת: רשימת כל העמודים, מקובצת לפי פרק
        groups = []
        for dp, daf, i in entries:
            pk = D['pages'][i].get('perek', '') or 'כל המסכת'
            if not groups or groups[-1][0] != pk:
                groups.append((pk, []))
            groups[-1][1].append((dp, daf))
        title = 'מסכת %s בקיצור - רשימת כל הדפים · %s' % (m, NAME)
        desc = 'מסכת %s בקיצור (קיצור התלמוד הבבלי): כל דפי המסכת, דף אחר דף, מקובצים לפי פרקים.' % m
        url = '%s/%s/' % (BASE, sl)
        ld = {'@context': 'https://schema.org', '@type': 'CollectionPage', 'name': title, 'url': url, 'inLanguage': 'he',
              'isPartOf': {'@type': 'WebSite', 'name': NAME, 'url': BASE + '/'}}
        body = '<main><h1>מסכת %s בקיצור</h1><p>קיצור התלמוד הבבלי, דף אחר דף. <a class="cta" href="/%s.html">ללימוד האינטראקטיבי</a></p>' % (esc(m), sl)
        for pk, ds in groups:
            body += '<h2>%s</h2><ul class="dafs">%s</ul>' % (esc(pk), ''.join('<li><a href="/%s/%s.html">%s</a></li>' % (sl, dp, esc(daf_words(df))) for dp, df in ds))
        body += '</main></body></html>'
        io.open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(head(title, desc, url, ld) + body)
        urls.append((sl + '/', '0.7'))
    # "הדף היומי היום": כתובת קבועה. בבנייה נכתב בה הדף של יום הבנייה (מה שגוגל רואה);
    # בדפדפן הסקריפט מחליף אותו בדף של היום לפי לוח הדף היומי, ללא רשת מעבר לשליפת העמוד.
    try:
        import importlib.util
        # הלוח חושב ב-daf-yomi.js; כאן נגזר מאותו נתון בפייתון, כדי שלא יהיה מקור שני: נקרא מן הקובץ
        src = io.open(os.path.join(site, 'daf-yomi.js'), encoding='utf-8').read()
        rows = re.findall(r"\['([^']+)','([a-z\-]+)',(\d+),(\d+)\]", src)
        cyc = sum(int(r[3]) for r in rows)
        days = (datetime.date.today() - datetime.date(2020, 1, 5)).days % cyc
        pick = None
        for nm, sl, start, ln in rows:
            if days < int(ln):
                pick = (nm, sl, int(start) + days)
                break
            days -= int(ln)
        if pick:
            nm, sl, n = pick
            letters = None
            body_html = ''
            path_a = os.path.join(site, sl, '%da.html' % n)
            mm = ''
            if os.path.exists(path_a):
                for f in ('%da.html' % n, '%db.html' % n):
                    pp = os.path.join(site, sl, f)
                    if os.path.exists(pp):
                        h = io.open(pp, encoding='utf-8').read()
                        mt = re.search(r'<h1>(.*?)</h1>(.*?)<p class="note">קיצור', h, re.S)
                        if mt:
                            body_html += '<h2>%s</h2>%s' % (mt.group(1), re.sub(r'<p><a class="cta".*?</p>', '', mt.group(2), flags=re.S))
            title = 'הדף היומי היום בקיצור - %s דף %d · %s' % (nm, n, NAME)
            desc = 'הדף היומי של היום בקיצור (%s דף %d). הכתובת קבועה והדף מתעדכן מדי יום.' % (nm, n)
            url = BASE + '/hadaf-hayomi.html'
            ld = {'@context': 'https://schema.org', '@type': 'WebPage', 'name': title, 'url': url, 'inLanguage': 'he', 'dateModified': today}
            page = head(title, desc, url, ld) + (
                '<main><h1>הדף היומי היום בקיצור</h1><p id="hy-top" class="note">היום: %s דף %d (תאריך הבנייה %s)</p>'
                '<div id="hy">%s</div></main>'
                '<script src="/daf-yomi.js"></script><script>(function(){try{var t=LGDaf.forStr(new Date().toISOString().slice(0,10));'
                'if(!t||(t.slug==="%s"&&t.n===%d))return;var a=t.n+"a",b=t.n+"b";'
                'Promise.all([a,b].map(function(f){return fetch("/"+t.slug+"/"+f+".html").then(function(r){return r.ok?r.text():""})})).then(function(x){'
                'var out="";x.forEach(function(h){var m=h.match(/<h1>(.*?)<\\/h1>([\\s\\S]*?)<p class="note">קיצור/);if(m)out+="<h2>"+m[1]+"</h2>"+m[2].replace(/<p><a class="cta"[\\s\\S]*?<\\/p>/,"")});'
                'document.getElementById("hy").innerHTML=out||"<p>הדף של היום (\\u200f"+t.name+" "+t.daf+") עדיין אינו באתר בקיצור. <a href=\\"/yomi.html\\">לדף היומי</a></p>";'
                'document.getElementById("hy-top").textContent="היום: "+t.name+" "+t.daf;document.title="הדף היומי היום בקיצור - "+t.name+" "+t.daf})}catch(e){}})();</script></body></html>'
            ) % (esc(nm), n, today, body_html or '<p>הדף של היום עדיין אינו באתר בקיצור. <a href="/yomi.html">לדף היומי</a></p>', sl, n)
            io.open(os.path.join(site, 'hadaf-hayomi.html'), 'w', encoding='utf-8').write(page)
            urls.append(('hadaf-hayomi.html', '0.9'))
    except Exception as e:
        print('אזהרה: דף "הדף היומי היום" לא נבנה:', e)
    print('עמודים סטטיים: %d עמודי גמרא, %d מסכתות' % (total, len(built)))
    return urls
