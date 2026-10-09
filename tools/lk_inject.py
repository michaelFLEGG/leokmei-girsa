# -*- coding: utf-8 -*-
"""lk_inject.py - מזריק את נתוני הגלישה ואת שכבת טקסטי האתר לכל דף (8.10.2026).

רץ בסוף כל בנייה (build_all.main), ובכל הרצה חוזרת אינו משנה דבר שכבר הוזרק.
  א. כותב site/lk-core.js (עם ההגדרות מ-tools/lk/config.json) ו-site/lk-pencil.js.
  ב. מוסיף שורת script אחת (defer) לכל קובץ html באתר. אסינכרוני: אינו מעכב ציור.
  ג. כותב את דף המנהל "טקסטים ששיניתי" (admin-texts.html).
  ד. מחיל על כותרות ותיאורי הדפים הסטטיים את שינויי העיפרון (לגוגל), כשהשרת זמין.
אינו נוגע בתוכן הגמרא, בקובצי הוורד ובנתוני המשתמשים."""
import hashlib, html as H, io, json, os, re, shutil, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
LK = os.path.join(HERE, 'lk')
MARK = 'lk-core.js'
SKIPDIRS = ('fonts', 'brand', 'galeria-lamed', 'tzura')


def _read(p):
    return io.open(p, encoding='utf-8').read()


def _write(p, t):
    with io.open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)


def config():
    c = json.loads(_read(os.path.join(LK, 'config.json')))
    if os.environ.get('LK_API'):          # רק לבדיקות מקומיות מול Worker מקומי
        c['api'] = os.environ['LK_API']
    if os.environ.get('LK_CLARITY'):
        c['clarity'] = os.environ['LK_CLARITY']
    if os.environ.get('LK_CF'):
        c['cf'] = os.environ['LK_CF']
    return c


def build_assets(site):
    cfg = config()
    core = _read(os.path.join(LK, 'lk-core.js'))
    pencil = _read(os.path.join(LK, 'lk-pencil.js'))
    v = hashlib.md5((core + pencil + json.dumps(cfg, sort_keys=True)).encode('utf-8')).hexdigest()[:8]
    cfg = dict(cfg, v=v)
    m = re.search(r'/\*LK_CFG\*/.*?/\*END_CFG\*/', core, re.S)
    if not m:
        raise SystemExit('עצירה: lk-core.js ללא סימון ההגדרות')
    core = core[:m.start()] + '/*LK_CFG*/' + json.dumps(cfg, ensure_ascii=False) + '/*END_CFG*/' + core[m.end():]
    _write(os.path.join(site, 'lk-core.js'), core)
    _write(os.path.join(site, 'lk-pencil.js'), pencil)
    _write(os.path.join(site, 'admin-texts.html'), _read(os.path.join(LK, 'admin-texts.html')))
    _write(os.path.join(site, 'admin-stats.html'), _read(os.path.join(LK, 'admin-stats.html')))
    reg = os.path.join(LK, 'texts-registry.json')
    if os.path.exists(reg):
        shutil.copy(reg, os.path.join(site, 'lk-texts.json'))
    return v


def inject_pages(site, v):
    tag = '<script defer src="/lk-core.js?v=%s"></script>' % v
    n = same = 0
    for root, dirs, files in os.walk(site):
        dirs[:] = [d for d in dirs if d not in SKIPDIRS]
        for f in files:
            if not f.endswith('.html'):
                continue
            p = os.path.join(root, f)
            t = _read(p)
            if MARK in t:
                new = re.sub(r'<script defer src="/lk-core\.js\?v=[^"]*"></script>', lambda _m: tag, t)
                if new != t:
                    _write(p, new); n += 1
                else:
                    same += 1
                continue
            if '</head>' in t:
                t = t.replace('</head>', tag + '</head>', 1)
            elif '</body>' in t:
                t = t.replace('</body>', tag + '</body>', 1)
            else:
                print('אזהרה: אין head או body, לא הוזרק:', p)
                continue
            _write(p, t); n += 1
    return n, same


def _ptype(rel):
    """סוג הדף לפי הנתיב, כמו LK.pageType בדפדפן."""
    parts = rel.replace('\\', '/').strip('/').split('/')
    last = re.sub(r'\.html$', '', parts[-1])
    T = {'index': 'home', 'shas': 'shas', 'masechtot': 'masechtot', 'yomi': 'yomi', 'lamed': 'lamed', 'quiz': 'quiz', 'shiurim': 'shiurim',
         'about': 'about', 'settings': 'settings', 'done': 'done', 'admin-lamdim': 'admin', 'mekorot': 'mekorot', 'masechet': 'masechet-shell',
         'privacy': 'privacy'}
    if len(parts) >= 2:
        return 'daf-static'
    return T.get(last, 'gemara')


def bake_meta(site, cfg):
    """שינויי כותרת ותיאור (מהעיפרון) נאפים גם בדפים הסטטיים, כדי שגוגל יראה אותם.
    כשל ברשת אינו עוצר את הבנייה: השינויים עדיין חיים בדפדפן."""
    try:
        with urllib.request.urlopen(urllib.request.Request(cfg['api'] + '/tx', headers={'User-Agent': 'leokmei-build/1.0'}), timeout=10) as r:
            d = json.loads(r.read().decode('utf-8'))
    except Exception as e:
        print('הערה: שינויי הכותרות לא נאפו (%s); הם חיים בדפדפן' % e)
        return 0
    wanted = {}
    for k, it in (d.get('items') or {}).items():
        kind = it.get('d') or 'text'
        if kind in ('doctitle', 'metadesc') and not it.get('h'):
            wanted[(k.split('.')[0], kind, re.sub(r'\s+', ' ', it.get('o', '')).strip())] = it.get('t', '')
    if not wanted:
        return 0
    cnt = 0
    for root, dirs, files in os.walk(site):
        dirs[:] = [x for x in dirs if x not in SKIPDIRS]
        for f in files:
            if not f.endswith('.html'):
                continue
            p = os.path.join(root, f)
            sc = _ptype(os.path.relpath(p, site))
            t0 = t = _read(p)
            for (wsc, kind, orig), new in wanted.items():
                if wsc != sc and wsc != 'site':
                    continue
                if kind == 'doctitle':
                    mm = re.search(r'<title>([^<]*)</title>', t)
                    if mm and re.sub(r'\s+', ' ', H.unescape(mm.group(1))).strip() == orig:
                        t = t[:mm.start()] + '<title>' + H.escape(new, quote=False) + '</title>' + t[mm.end():]
                else:
                    mm = re.search(r'(<meta name="description" content=")([^"]*)(")', t)
                    if mm and re.sub(r'\s+', ' ', H.unescape(mm.group(2))).strip() == orig:
                        t = t[:mm.start()] + mm.group(1) + H.escape(new) + mm.group(3) + t[mm.end():]
            if t != t0:
                _write(p, t); cnt += 1
    return cnt


def run(site):
    v = build_assets(site)
    n, same = inject_pages(site, v)
    b = bake_meta(site, config())
    print('lk: גרסה %s, הוזרק ב-%d דפים (%d ללא שינוי), דפים עם כותרת שנאפתה: %d' % (v, n, same, b))
    return v


if __name__ == '__main__':
    run(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(HERE), 'site'))
