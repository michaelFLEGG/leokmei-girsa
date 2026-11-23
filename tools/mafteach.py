# -*- coding: utf-8 -*-
"""mafteach.py - מפתח מושגים לכל הש"ס (פרומפט 82, 23.11.2026).

המקור: כותרות הנושא (יחידות nose) בכל המסכתות הבנויות. אין בו טקסט חדש ואין בו ניחוש:
  א. כל כותרת היא ערך. כותרות שנוסחן זהה בשלד (כתיב מלא וחסר, פיסוק, ו' בראש) מאוחדות לערך אחד.
     כותרות שנוסחן שונה אינן מאוחדות, גם כשהן קרובות.
  ב. "ראש נושא": החלק שלפני " - " בכותרת ("חציצין - מה חוצץ בטבילה"), כשהוא ראשן של שתי כותרות שונות
     לפחות - הוא ערך משלו, שמאגד את כל הכותרות שהוא פותח.
  ג. כותרות כלליות שאינן מושג ("פסק ההלכה", "המקור לכך", "ועד כמה?") אינן ערכים.
התוצר באתר (נטפרי: הכל תחת leokmei.com, בכתובות לטיניות, בלי סקריפט או גופן חיצוני):
  /mafteach/index.html            - חיפוש, ואותיות
  /mafteach/l-<n>.html            - כל הערכים שבאות אחת (n = מיקום האות באלף-בית)
  /mafteach/k/<id>.html           - עמוד לכל ערך שיש לו שני מקומות או יותר: כל מקומותיו בש"ס, עם קישור לדף הסטטי
                                    ולמקום בלאוקמי גירסא. ערך של מקום אחד מקשר ישר לדף הסטטי (עמוד משלו היה משכפל אותו)
  /mafteach/data.json             - לחיפוש (נטען רק בהקלדה הראשונה)
  /mafteach/m/<slug>.json         - מפתח העניינים של מסכת אחת, להדפסה (מנוע ההדפסה מצרף אותו בסוף המסכת)
מחזיר את רשימת הכתובות למפת האתר (רק ערכים שיש להם שני מקומות או יותר; ערך יחיד נשאר מחוץ למפה)."""
import hashlib, html, io, json, os, re, shutil, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_static as BS
import shas_links as SL

ABC = 'אבגדהוזחטיכלמנסעפצקרשת'
FIN = str.maketrans('ךםןףץ', 'כמנפצ')
GENERIC = {'פסק ההלכה', 'פסק הלכה', 'המקור לכך', 'דעות נוספות', 'צריכותא', 'טעם המחלוקת', 'טעמי המחלוקת', 'ועד כמה',
           'בחזקת מי', 'מקור הדין', 'הלכה', 'המקור', 'מקור', 'סיכום', 'קושיא', 'תירוץ', 'עוד', 'ועוד', 'שאלה', 'מעשה',
           'מעשים', 'דרשות', 'הסבר', 'ביאור', 'סיום', 'הקדמה', 'שיטות', 'בירור', 'הבהרה', 'סייג', 'הוכחה', 'ראיה', 'דין', 'דינים'}
SITE_BASE = 'https://leokmei.com'


def clean(t):
    t = SL.plain(t)
    t = re.sub(r'\s*[,.;:?!]+\s*$', '', t).strip()
    t = re.sub(r'\s+([,.;:?!])', r'\1', t)
    return t


def key_of(t):
    ws = SL.words(t)
    if ws and len(ws[0]) > 1 and ws[0].startswith('ו'):
        ws[0] = ws[0][1:]
    return ' '.join(ws)


def letter_of(t):
    for ch in SL.NIK.sub('', t):
        if 'א' <= ch <= 'ת':
            ch = ch.translate(FIN)
            return ch
    return ''


def sort_key(t):
    s = SL.NIK.sub('', t).translate(FIN)
    s = re.sub(r'^ו(?=[א-ת]{2})', '', s)
    return re.sub(r'[^א-ת ]', '', s)


def generic(t):
    k = re.sub(r'[^א-ת ]', '', SL.NIK.sub('', t)).strip()
    return k in GENERIC or not k


def kid(k):
    return hashlib.sha1(k.encode('utf-8')).hexdigest()[:10]


def collect(site):
    """כל כותרות הנושא: [(slug, he, daf, uid, כותרת, ההמשך)] לפי סדר הש"ס כפי שבנוי."""
    out = []
    order = json.load(io.open(os.path.join(HERE, '..', 'data', 'book.json'), encoding='utf-8')).get('slugs') or []
    slugs = sorted((f[:-8] for f in os.listdir(site) if f.endswith('.data.js')), key=lambda s: (order.index(s) if s in order else 999, s))
    for slug in slugs:
        D = SL.load_data(site, slug)
        if not D:
            continue
        he = D.get('masechet') or slug
        units = [(pg.get('daf') or '', u) for pg in D['pages'] for u in (pg.get('units') or [])]
        for i, (daf, u) in enumerate(units):
            if u.get('k') != 'nose':
                continue
            t = clean(u.get('a'))
            if not t:
                continue
            nxt = ''
            for d2, u2 in units[i + 1:i + 4]:
                if u2.get('k') in ('u', 'm', 'dh'):
                    nxt = (SL.plain(u2.get('a')) + ' ' + ' '.join(SL.plain(l[1]) for l in (u2.get('l') or []) if isinstance(l, list) and len(l) > 1)).strip()
                    break
            out.append((slug, he, daf, u['id'], t, nxt))
    return out, slugs


def build_entries(rows):
    by = collections.OrderedDict()
    for r in rows:
        if generic(r[4]):
            continue
        k = key_of(r[4])
        if not k:
            continue
        e = by.setdefault(k, {'k': k, 'forms': collections.Counter(), 'places': [], 'sub': []})
        e['forms'][r[4]] += 1
        e['places'].append(r)
    heads = collections.defaultdict(list)
    for k, e in by.items():
        t = e['forms'].most_common(1)[0][0]
        if ' - ' in t:
            h = t.split(' - ', 1)[0].strip()
            if len(SL.words(h)) >= 1 and not generic(h):
                heads[key_of(h)].append((h, k))
    for hk, lst in heads.items():
        if len({k for _, k in lst}) < 2:
            continue
        if hk in by:
            e = by[hk]
        else:
            e = by.setdefault(hk, {'k': hk, 'forms': collections.Counter(), 'places': [], 'sub': []})
        for h, k in lst:
            e['forms'][h] += 0
            if k != hk:
                e['sub'].append(k)
        if not e['forms'] or sum(e['forms'].values()) == 0:
            e['forms'][collections.Counter(h for h, _ in lst).most_common(1)[0][0]] += 1
    ents = []
    for k, e in by.items():
        title = e['forms'].most_common(1)[0][0]
        places = list(e['places'])
        for sk in e['sub']:
            places.extend(by[sk]['places'])
        seen, uniq = set(), []
        for p in places:
            if (p[0], p[3]) not in seen:
                seen.add((p[0], p[3]))
                uniq.append(p)
        ents.append({'id': kid(k), 'k': k, 't': title, 'places': uniq, 'sub': [by[s]['forms'].most_common(1)[0][0] for s in e['sub']],
                     'variants': sorted(f for f in e['forms'] if f != title and e['forms'][f] > 0)})
    ents.sort(key=lambda e: sort_key(e['t']))
    return ents


def esc(s):
    return html.escape(s or '', quote=True)


def go_url(p):
    return '/%s.html#u=%d&daf=%s' % (p[0], p[3], esc(p[2]))


def static_url(site, p):
    dp = BS.daf_path(p[2])
    if dp and os.path.exists(os.path.join(site, p[0], dp + '.html')):
        return '/%s/%s.html' % (p[0], dp)
    return None


EXTRA_CSS = ('.mf-s{width:100%;box-sizing:border-box;font:inherit;font-size:19px;padding:9px 12px;border:1px solid #8f6a1e;border-radius:8px;background:#fffdf8;margin:6px 0 4px}'
             'nav.abc{display:flex;flex-wrap:wrap;gap:4px 6px;margin:10px 0 4px}nav.abc a{display:inline-block;min-width:30px;text-align:center;padding:3px 6px;border:1px solid #c9bfa8;border-radius:6px;text-decoration:none;font-weight:700}'
             'nav.abc a:hover,nav.abc a.on{background:#0f263b;color:#f5e3a8;border-color:#0f263b}'
             'ul.mf{list-style:none;padding:0;margin:8px 0}ul.mf li{padding:4px 0;border-bottom:1px solid #e6dcc6}ul.mf li small{color:#6a5f4d;font-size:15px;margin-inline-start:6px}'
             'ol.pl{padding-inline-start:22px}ol.pl li{margin:10px 0}ol.pl .ctx{display:block;font-size:16px;color:#4a4236}ol.pl .lk{font-size:15px}'
             '#mfr:empty{display:none}')


def page(title, desc, path, body, ld, robots=None):
    url = SITE_BASE + path
    return (BS.head(title, desc, url, ld, robots=robots, og_type='website').replace('</style>', EXTRA_CSS + '</style>', 1)
            + '<main>' + body + '</main>' + BS.FOOTER + '</body></html>')


SEARCH_JS = r'''<script>(function(){var q=document.getElementById('mfq'),out=document.getElementById('mfr'),D=null,ld=0;
function sk(s){return s.replace(/[֑-ׇ]/g,'').replace(/[ךםןףץ]/g,function(c){return {'ך':'כ','ם':'מ','ן':'נ','ף':'פ','ץ':'צ'}[c]}).replace(/["'׳״]/g,'').replace(/[וי]/g,'')}
function esc(s){return s.replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
function nk(s){return s.replace(/[\u0591-\u05C7]/g,'')}
function show(){var raw=nk(q.value.trim()),v=sk(raw);if(!v||!D){out.innerHTML='';return}var ws=v.split(/\s+/),rw=raw.split(/\s+/),r=[];
for(var i=0;i<D.length;i++){var s=D[i][3];if(!ws.every(function(w){return s.indexOf(w)>-1}))continue;
var t=D[i][4],sc=rw.every(function(w){return t.indexOf(w)>-1})?2:1;if(sc===2&&rw.some(function(w){return new RegExp('(^|[^\u05d0-\u05ea])[והבלמשכ]?'+w.replace(/[.*+?^${}()|[\]\\]/g,'')+'($|[^\u05d0-\u05ea])').test(t)}))sc=3;r.push([sc,D[i]])}
r.sort(function(a,b){return b[0]-a[0]||((typeof b[1][2]==='number'?b[1][2]:1)-(typeof a[1][2]==='number'?a[1][2]:1))});r=r.slice(0,120).map(function(x){return x[1]});
out.innerHTML=r.length?'<ul class="mf">'+r.map(function(e){return '<li><a href="'+esc(e[0])+'">'+esc(e[1])+'</a><small>'+(typeof e[2]==='number'?e[2]+' מקומות':esc(e[2]))+'</small></li>'}).join('')+'</ul>':'<p class="note">לא נמצא מושג כזה. אפשר לנסות מילה אחת.</p>'}
q.addEventListener('input',function(){if(D)return show();if(ld)return;ld=1;fetch('data.json').then(function(r){return r.json()}).then(function(j){D=j.e.map(function(e){return [e[0],e[1],e[2],sk(e[1]+' '+(e[3]||'')),nk(e[1]+' '+(e[3]||''))]});show()})});
})()</script>'''


def run(site, built=None, slug=None):
    rows, slugs = collect(site)
    ents = build_entries(rows)
    root = os.path.join(site, 'mafteach')
    if os.path.isdir(root):
        shutil.rmtree(root)
    os.makedirs(os.path.join(root, 'k'))
    os.makedirs(os.path.join(root, 'm'))
    he_of = {}
    for r in rows:
        he_of[r[0]] = r[1]
    by_letter = collections.OrderedDict((c, []) for c in ABC)
    urls = []
    for e in ents:
        c = letter_of(sort_key(e['t'])) or letter_of(e['t'])
        by_letter.setdefault(c, []).append(e)
        n = len(e['places'])
        if n < 2:
            # ערך שיש לו מקום אחד: בלי עמוד משלו (היה משכפל את הדף הסטטי), הקישור הולך ישר למקום
            p = e['places'][0]
            e['href'] = static_url(site, p) or go_url(p)
            continue
        e['href'] = '/mafteach/k/%s.html' % e['id']
        mas = []
        for p in e['places']:
            if p[1] not in mas:
                mas.append(p[1])
        title = '%s - מפתח מושגים בש"ס | לאוקמי גירסא' % e['t']
        desc = ('%s בתלמוד הבבלי: %s, בקיצור לאוקמי גירסא.' % (e['t'], ', '.join('%s %s' % (p[1], p[2]) for p in e['places'][:6]) + ('…' if n > 6 else '')))
        items = []
        for p in e['places']:
            st = static_url(site, p)
            ctx = p[5][:220] + ('…' if len(p[5]) > 220 else '')
            items.append('<li><strong>מסכת %s %s</strong> · %s<span class="ctx">%s</span><span class="lk"><a href="%s">ללמוד במקום בלאוקמי גירסא</a>%s</span></li>'
                         % (esc(p[1]), esc(BS.daf_words(p[2]) if p[2] else ''), esc(p[4]), esc(ctx), go_url(p),
                            (' · <a href="%s">דף %s בקיצור</a>' % (st, esc(p[2]))) if st else ''))
        sub = ''
        if e['sub']:
            sub = '<p class="note">מאגד את הכותרות: ' + ' · '.join(esc(s) for s in e['sub'][:30]) + '</p>'
        var = ''
        if e['variants']:
            var = '<p class="note">נוסחים נוספים של אותה כותרת: ' + ' · '.join(esc(v) for v in e['variants']) + '</p>'
        li = ABC.index(c) + 1 if c in ABC else 0
        body = ('<nav class="crumbs"><a href="/">לאוקמי גירסא</a> › <a href="/mafteach/">מפתח מושגים</a> › <a href="/mafteach/l-%d.html">%s</a></nav>'
                '<h1>%s</h1><p>%s בש"ס: %d %s, ב%s %s.</p>%s%s<ol class="pl">%s</ol>'
                % (li, esc(c), esc(e['t']), esc(e['t']), n, 'מקומות' if n != 1 else 'מקום', 'מסכתות' if len(mas) > 1 else 'מסכת', esc(', '.join(mas)), sub, var, ''.join(items)))
        ld = [BS.crumbs_ld([('לאוקמי גירסא', SITE_BASE + '/'), ('מפתח מושגים', SITE_BASE + '/mafteach/'), (e['t'], SITE_BASE + '/mafteach/k/%s.html' % e['id'])]),
              {'@context': 'https://schema.org', '@type': 'DefinedTerm', 'name': e['t'], 'inDefinedTermSet': SITE_BASE + '/mafteach/',
               'url': SITE_BASE + '/mafteach/k/%s.html' % e['id']}]
        with io.open(os.path.join(root, 'k', e['id'] + '.html'), 'w', encoding='utf-8', newline='\n') as f:
            f.write(page(title, desc, '/mafteach/k/%s.html' % e['id'], body, ld))
        urls.append(('mafteach/k/%s.html' % e['id'], '0.5', None, 'mafteach'))
    abc_nav = lambda on=None: '<nav class="abc">' + ''.join(
        '<a href="/mafteach/l-%d.html"%s>%s</a>' % (i + 1, ' class="on"' if c == on else '', c) for i, c in enumerate(ABC) if by_letter.get(c)) + '</nav>'
    for i, c in enumerate(ABC):
        lst = by_letter.get(c) or []
        if not lst:
            continue
        body = ('<nav class="crumbs"><a href="/">לאוקמי גירסא</a> › <a href="/mafteach/">מפתח מושגים</a></nav><h1>מפתח מושגים - אות %s</h1>%s'
                '<ul class="mf">%s</ul>' % (c, abc_nav(c), ''.join('<li><a href="%s">%s</a><small>%s</small></li>'
                                                              % (e['href'], esc(e['t']), ', '.join(sorted({'%s %s' % (p[1], p[2]) if len(e['places']) == 1 else p[1] for p in e['places']}))) for e in lst)))
        ld = BS.crumbs_ld([('לאוקמי גירסא', SITE_BASE + '/'), ('מפתח מושגים', SITE_BASE + '/mafteach/'), ('אות ' + c, SITE_BASE + '/mafteach/l-%d.html' % (i + 1))])
        with io.open(os.path.join(root, 'l-%d.html' % (i + 1)), 'w', encoding='utf-8', newline='\n') as f:
            f.write(page('מפתח מושגים בש"ס - אות %s | לאוקמי גירסא' % c, 'מושגים ונושאים בתלמוד הבבלי באות %s, וכל מקומותיהם בש"ס, מתוך לאוקמי גירסא.' % c,
                         '/mafteach/l-%d.html' % (i + 1), body, ld))
        urls.append(('mafteach/l-%d.html' % (i + 1), '0.5', None, 'mafteach'))
    body = ('<nav class="crumbs"><a href="/">לאוקמי גירסא</a> › מפתח מושגים</nav><h1>מפתח מושגים לכל הש"ס</h1>'
            '<p>כל נושאי הסוגיות שבלאוקמי גירסא, מכל המסכתות שבאתר, וכל מושג מוביל לכל מקומותיו בש"ס.</p>'
            '<input id="mfq" class="mf-s" type="search" placeholder="חיפוש מושג, למשל: מחיצות" aria-label="חיפוש מושג" autocomplete="off">'
            '<div id="mfr"></div>%s<p class="note">%d מושגים מתוך %d כותרות נושא, ב-%d מסכתות.</p>%s'
            % (abc_nav(), len(ents), len(rows), len(slugs), SEARCH_JS))
    ld = [BS.crumbs_ld([('לאוקמי גירסא', SITE_BASE + '/'), ('מפתח מושגים', SITE_BASE + '/mafteach/')]),
          {'@context': 'https://schema.org', '@type': 'DefinedTermSet', 'name': 'מפתח מושגים לכל הש"ס', 'url': SITE_BASE + '/mafteach/'}]
    with io.open(os.path.join(root, 'index.html'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(page('מפתח מושגים לכל הש"ס - נושאי הסוגיות בתלמוד הבבלי | לאוקמי גירסא',
                     'מפתח מושגים ונושאים לכל התלמוד הבבלי: חיפוש, חלוקה לפי אותיות, וכל מושג מוביל לכל מקומותיו בש"ס.',
                     '/mafteach/', body, ld))
    urls.insert(0, ('mafteach/', '0.6', None, 'mafteach'))
    with io.open(os.path.join(root, 'data.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump({'v': 1, 'e': [[e['href'], e['t'], len(e['places']) if len(e['places']) > 1 else '%s %s' % (e['places'][0][1], e['places'][0][2]),
                                ' '.join(e['variants'] + e['sub'])[:300]] for e in ents]},
                  f, ensure_ascii=False, separators=(',', ':'))
    # מפתח העניינים של כל מסכת, להדפסה: כותרות הנושא שלה לפי האלף-בית, עם הדף
    per = collections.defaultdict(list)
    for e in ents:
        for p in e['places']:
            per[p[0]].append([e['t'] if not e['sub'] else p[4], p[2]])
    for s, lst in per.items():
        agg = collections.OrderedDict()
        for t, d in sorted(lst, key=lambda x: sort_key(x[0])):
            agg.setdefault(t, [])
            if d not in agg[t]:
                agg[t].append(d)
        with io.open(os.path.join(root, 'm', s + '.json'), 'w', encoding='utf-8', newline='\n') as f:
            json.dump({'v': 1, 'masechet': he_of.get(s, s), 'e': [[t, ds] for t, ds in agg.items()]}, f, ensure_ascii=False, separators=(',', ':'))
    multi = sum(1 for e in ents if len(e['places']) > 1)
    print('מפתח מושגים: %d כותרות נושא, %d ערכים (%d בשני מקומות ומעלה, %d ראשי נושא), %d מסכתות; %d כתובות למפת האתר'
          % (len(rows), len(ents), multi, sum(1 for e in ents if e['sub']), len(per), len(urls)))
    return urls


if __name__ == '__main__':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    run(os.path.join(os.path.dirname(HERE), 'site'))
