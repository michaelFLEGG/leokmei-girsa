# -*- coding: utf-8 -*-
"""shma.py - "שמע" ליד כל יחידה (פרומפט 83, 23.11.2026).

ליד כל כותרת נושא (וכותרת ד"ה) בדף הגמרא כפתור קטן שמפעיל את השיעור של מיכאל
על אותו דף, מהדקה של הקטע הזה. הכלי הזה בונה את הנתונים, ואינו נוגע בטקסט.

מקורות ההקלטות (כל הקלטה חדשה נכנסת לבד):
  א. רשימת השיעורים של האתר (מסך "שיעורים", שרת leokmei-suggest, /lessons): כל שיעור
     יוטיוב שהמנהל קשר למסכת ולדף.
  ב. data/shma/sources.json: רשימה ידנית או אוטומטית של הקלטות, לכל אחת מסכת ודף
     וכתובת (קובץ שמע ישיר, קישור דרייב ציבורי, או יוטיוב).
  ג. קובץ שמע שהונח ב-input/shma/<slug>/<daf>.<סיומת> (למשל input/shma/shabbat/2a.mp3).

השמע עצמו מתארח באתר (leokmei.com/audio/...), כי יוטיוב חסום אצל רבים בנטפרי.
יוטיוב נשאר כאפשרות נוספת למי שיכול.

שלבים (כל אחד מדלג על מה שכבר נעשה):
  fetch       - הורדת השמע של מקור שעוד אין לו קובץ, ודחיסה ל-mp3 מונו קל (ffmpeg)
  transcribe  - תמלול (faster-whisper, מודל עברי) של כל קובץ שאין לו תמלול
  align       - התאמת התמלול ליחידות הדף, וכתיבת data/shma/<slug>.json
  build SITE  - העתקת הנתונים והשמע לאתר (נקרא מ-build_all)

כלל הבטיחות (סעיף 3 בפרומפט): יחידה שההתאמה בה אינה ודאית מקבלת s=null, והכפתור
מתחיל מתחילת הדף ולא ממקום שגוי.

הרצה:  python tools/shma.py all        (או fetch / transcribe / align)
"""
import os, io, re, sys, json, math, glob, shutil, hashlib, subprocess, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data', 'shma')
INBOX = os.path.join(ROOT, 'input', 'shma')
AUDIO = os.path.join(ROOT, 'audio')            # השמע המתארח (נכנס לאתר כמו שהוא)
TR = os.path.join(DATA, 'tr')                  # תמלולים: tr/<slug>/<key>.json
API = 'https://leokmei-suggest.m7654301.workers.dev/lessons'
MODEL = os.environ.get('SHMA_MODEL', 'ivrit-ai/whisper-large-v3-turbo-ct2')
BITRATE = '32k'                                # מונו 32 קילוביט: כ-14 מגה לשעה

GEM = {'א': 1, 'ב': 2, 'ג': 3, 'ד': 4, 'ה': 5, 'ו': 6, 'ז': 7, 'ח': 8, 'ט': 9, 'י': 10, 'כ': 20, 'ך': 20, 'ל': 30,
       'מ': 40, 'ם': 40, 'נ': 50, 'ן': 50, 'ס': 60, 'ע': 70, 'פ': 80, 'ף': 80, 'צ': 90, 'ץ': 90, 'ק': 100, 'ר': 200,
       'ש': 300, 'ת': 400}


def rd(p, d=None):
    try:
        return json.load(io.open(p, encoding='utf-8'))
    except Exception:
        return d


def wr(p, obj):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    io.open(p, 'w', encoding='utf-8').write(json.dumps(obj, ensure_ascii=False, indent=1) + '\n')


# ---------------------------------------------------------------- דפים
def daf_path(daf):
    """'ב.' -> '2a', 'ב:' -> '2b', '2b' -> '2b'."""
    s = str(daf or '').strip()
    m = re.match(r'^(\d+)([ab])$', s)
    if m:
        return s
    n = sum(GEM.get(c, 0) for c in s)
    if not n:
        return ''
    return '%d%s' % (n, 'b' if s.endswith(':') else 'a')


def heb_daf(p):
    """'2b' -> 'ב:' (כמו D.pages[].daf בדף)."""
    m = re.match(r'^(\d+)([ab])$', p or '')
    if not m:
        return p
    n, out = int(m.group(1)), ''
    for v, c in ((400, 'ת'), (300, 'ש'), (200, 'ר'), (100, 'ק'), (90, 'צ'), (80, 'פ'), (70, 'ע'), (60, 'ס'), (50, 'נ'),
                 (40, 'מ'), (30, 'ל'), (20, 'כ'), (10, 'י'), (9, 'ט'), (8, 'ח'), (7, 'ז'), (6, 'ו'), (5, 'ה'), (4, 'ד'),
                 (3, 'ג'), (2, 'ב'), (1, 'א')):
        while n >= v:
            if n in (15, 16):
                out += 'ט' + ('ו' if n == 15 else 'ז'); n = 0; break
            out += c; n -= v
    return out + ('.' if m.group(2) == 'a' else ':')


def dafs_between(a, b):
    """רשימת עמודים מ-a עד b (כולל), בצורה 2a."""
    a, b = daf_path(a), daf_path(b or a)
    if not a:
        return []
    if not b:
        b = a
    na, nb = int(a[:-1]) * 2 + (a[-1] == 'b'), int(b[:-1]) * 2 + (b[-1] == 'b')
    return ['%d%s' % (k // 2, 'b' if k % 2 else 'a') for k in range(na, max(na, nb) + 1)]


# ---------------------------------------------------------------- מקורות
def sources():
    """כל ההקלטות הידועות, כל אחת: key, slug, dafs, kind (audio/yt), url/vid, title."""
    out = []
    for s in rd(os.path.join(DATA, 'sources.json'), []) or []:
        dafs = dafs_between(s.get('from') or s.get('daf'), s.get('to'))
        if not s.get('slug') or not dafs:
            print('שמע: מקור בלי מסכת או דף, מדולג -', s); continue
        vid = s.get('vid') or yt_id(s.get('url', ''))
        out.append({'key': s.get('key') or key_of(s['slug'], dafs, s.get('url') or vid), 'slug': s['slug'], 'dafs': dafs,
                    'kind': 'yt' if vid else 'audio', 'url': s.get('url', ''), 'vid': vid or '',
                    'title': s.get('title', '')})
    try:
        req = urllib.request.Request(API, headers={'User-Agent': 'leokmei-build/1.0'})
        items = json.loads(urllib.request.urlopen(req, timeout=20).read().decode('utf-8')).get('items', [])
    except Exception as e:
        items = None
        print('שמע: רשימת השיעורים של האתר לא נקראה -', str(e)[:80])
    for l in items or []:
        dafs = dafs_between(l.get('from'), l.get('to'))
        if l.get('slug') and dafs and l.get('vid'):
            out.append({'key': 'yt-' + l['vid'], 'slug': l['slug'], 'dafs': dafs, 'kind': 'yt', 'url': '',
                        'vid': l['vid'], 'title': l.get('title', '')})
    for p in sorted(glob.glob(os.path.join(INBOX, '*', '*.*'))):
        slug = os.path.basename(os.path.dirname(p))
        stem = os.path.splitext(os.path.basename(p))[0]
        parts = stem.split('-')
        dafs = dafs_between(parts[0], parts[1] if len(parts) > 1 else None)
        if not dafs:
            print('שמע: לא זוהה דף בשם הקובץ, מדולג -', p); continue
        out.append({'key': key_of(slug, dafs, 'inbox'), 'slug': slug, 'dafs': dafs, 'kind': 'audio', 'url': '',
                    'vid': '', 'title': '', 'inbox': p})
    seen, uniq = set(), []
    for s in out:
        if s['key'] not in seen:
            seen.add(s['key']); uniq.append(s)
    return uniq


def yt_id(u):
    m = re.search(r'(?:youtu\.be/|v=|/embed/|/shorts/|/live/)([A-Za-z0-9_-]{11})', u or '')
    return m.group(1) if m else ''


def key_of(slug, dafs, tag):
    h = hashlib.sha1((tag or '').encode('utf-8')).hexdigest()[:6]
    return '%s-%s%s-%s' % (slug, dafs[0], ('-' + dafs[-1]) if len(dafs) > 1 else '', h)


def audio_rel(s):
    return 'audio/%s/%s.mp3' % (s['slug'], s['key'])


# ---------------------------------------------------------------- fetch
def ffmpeg_mp3(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-vn', '-ac', '1', '-ar', '22050', '-b:a', BITRATE, dst],
                   check=True)


def fetch(srcs):
    tmp = os.path.join(ROOT, '_work', 'shma-dl')
    os.makedirs(tmp, exist_ok=True)
    n = 0
    for s in srcs:
        dst = os.path.join(ROOT, audio_rel(s))
        if os.path.exists(dst):
            continue
        try:
            if s.get('inbox'):
                raw = s['inbox']
            elif s['kind'] == 'yt':
                raw = os.path.join(tmp, s['key'] + '.%(ext)s')
                subprocess.run([sys.executable, '-m', 'yt_dlp', '-q', '-f', 'bestaudio', '-o', raw,
                                'https://www.youtube.com/watch?v=' + s['vid']], check=True, timeout=1800)
                raw = (glob.glob(os.path.join(tmp, s['key'] + '.*')) or [None])[0]
            else:
                u = s['url']
                m = re.search(r'drive\.google\.com/(?:file/d/|open\?id=|uc\?id=)([A-Za-z0-9_-]+)', u)
                if m:
                    u = 'https://drive.usercontent.google.com/download?export=download&confirm=t&id=' + m.group(1)
                raw = os.path.join(tmp, s['key'] + '.src')
                req = urllib.request.Request(u, headers={'User-Agent': 'leokmei-build/1.0'})
                with urllib.request.urlopen(req, timeout=600) as r, open(raw, 'wb') as f:
                    shutil.copyfileobj(r, f)
            if not raw or not os.path.exists(raw):
                raise RuntimeError('הקובץ לא הורד')
            ffmpeg_mp3(raw, dst)
            n += 1
            print('שמע: נקלט', audio_rel(s), '%.1f מגה' % (os.path.getsize(dst) / 1e6))
        except Exception as e:
            # יוטיוב חוסם לעתים הורדה משרתי גיטהאב. השיעור נשאר עם כפתור יוטיוב מתחילת הדף.
            print('שמע: הורדה נכשלה (יישאר בלי שמע מתארח) -', s['key'], str(e)[:120])
    return n


# ---------------------------------------------------------------- transcribe
def tr_path(s):
    return os.path.join(TR, s['slug'], s['key'] + '.json')


def transcribe(srcs):
    todo = [s for s in srcs if os.path.exists(os.path.join(ROOT, audio_rel(s))) and not os.path.exists(tr_path(s))]
    if not todo:
        return 0
    from faster_whisper import WhisperModel
    model = WhisperModel(MODEL, device='cpu', compute_type='int8')
    for s in todo:
        segs, info = model.transcribe(os.path.join(ROOT, audio_rel(s)), language='he', vad_filter=True, beam_size=1)
        out = [{'s': round(g.start, 2), 'e': round(g.end, 2), 't': g.text.strip()} for g in segs]
        wr(tr_path(s), {'model': MODEL, 'dur': round(info.duration, 1), 'segs': out})
        print('שמע: תומלל', s['key'], len(out), 'קטעים')
    return len(todo)


# ---------------------------------------------------------------- align
NIK = re.compile('[֑-ׇ]')
PFX = ('וה', 'וש', 'וד', 'וב', 'ול', 'ומ', 'וכ', 'שה', 'דה', 'מה', 'בה', 'לה', 'כה', 'ו', 'ה', 'ש', 'ד', 'ב', 'ל', 'מ', 'כ')
FIN = str.maketrans('ךםןףץ', 'כמנפצ')


def norm_words(t):
    t = NIK.sub('', re.sub(r'<[^>]+>', ' ', t or ''))
    t = re.sub(r'[^א-ת\s]', ' ', t).translate(FIN)
    out = []
    for w in t.split():
        for p in PFX:
            if w.startswith(p) and len(w) - len(p) >= 3:
                w = w[len(p):]; break
        if len(w) >= 3:
            out.append(w)
    return out


def sk_page(slug, dp):
    """יחידות של עמוד אחד: site/sk/<slug>/<n>.json שהבנייה כותבת, ואם אין בנייה מקומית - מן האתר החי."""
    n = int(dp[:-1]) * 2 + (dp[-1] == 'b')
    p = os.path.join(ROOT, 'site', 'sk', slug, '%d.json' % n)
    j = rd(p)
    if j is None:
        try:
            req = urllib.request.Request('https://leokmei.com/sk/%s/%d.json' % (slug, n), headers={'User-Agent': 'leokmei-build/1.0'})
            j = json.loads(urllib.request.urlopen(req, timeout=20).read().decode('utf-8'))
        except Exception:
            j = None
    return j


def page_units(slug, dafs):
    """לכל עמוד: רשימת היחידות (כותרת, וכל הטקסט עד הכותרת הבאה)."""
    out = {}
    for dp in dafs:
        j = sk_page(slug, dp)
        if not j:
            continue
        us = []
        for u in j.get('units', []):
            body = (u.get('a') or '') + ' ' + ' '.join(l[1] for l in (u.get('l') or []) if len(l) > 1)
            if u.get('k') in ('nose', 'dh'):
                us.append({'t': head_text(u.get('a')), 'w': norm_words(body)})
            elif us:
                us[-1]['w'] += norm_words(body)
            else:
                us.append({'t': '', 'w': norm_words(body), 'pre': 1})
        out[dp] = us
    return out


def head_text(h):
    return re.sub(r'\s+', ' ', NIK.sub('', re.sub(r'<[^>]+>', '', h or ''))).strip()[:60]


def align_one(units, segs, t0=0.0, t1=None):
    """התאמה מונוטונית של יחידות לחלונות בתמלול. מחזיר לכל יחידה זמן או None (לא ודאי)."""
    if t1 is None:
        t1 = segs[-1]['e'] if segs else 0
    win = [g for g in segs if t0 <= g['s'] < t1]
    if not win or not units:
        return [None] * len(units)
    # חלונות של כ-45 שניות בצעד של 15
    W, ST, i, wins = 45.0, 15.0, 0, []
    t = win[0]['s']
    while t < win[-1]['e']:
        ws = [w for g in win if t <= g['s'] < t + W for w in norm_words(g['t'])]
        wins.append((t, ws))
        t += ST
    df = {}
    for u in units:
        for w in set(u['w']):
            df[w] = df.get(w, 0) + 1
    N = len(units)
    sc = []
    for u in units:
        uw = {}
        for w in u['w']:
            uw[w] = math.log(1 + N / df[w])
        row = []
        for t, ws in wins:
            hit = set(ws) & set(uw)
            row.append(sum(uw[w] for w in hit) / (1 + math.sqrt(len(uw))))
        sc.append(row)
    # תכנון דינמי: יחידה k בחלון j, j לא יורד
    M, INF = len(wins), -1e9
    best = [[INF] * M for _ in range(N)]
    back = [[0] * M for _ in range(N)]
    for j in range(M):
        best[0][j] = sc[0][j]
    for k in range(1, N):
        run, arg = INF, 0
        for j in range(M):
            if best[k - 1][j] > run:
                run, arg = best[k - 1][j], j
            best[k][j] = run + sc[k][j]; back[k][j] = arg
    j = max(range(M), key=lambda x: best[N - 1][x])
    pick = [0] * N
    for k in range(N - 1, -1, -1):
        pick[k] = j; j = back[k][j]
    out = []
    for k in range(N):
        row = sorted(sc[k], reverse=True)
        top, med = sc[k][pick[k]], row[len(row) // 2] if row else 0
        # ודאות: שלוש מילים ייחודיות לפחות, ובולט פי שניים מן החציון
        sure = len(units[k]['w']) >= 6 and top >= 1.2 and top >= 2 * med + 0.3
        out.append(round(wins[pick[k]][0], 1) if sure else None)
    # שמירה על סדר: זמן ודאי שקטן מקודמו הוודאי - בטל
    last = -1
    for k in range(N):
        if out[k] is not None:
            if out[k] < last:
                out[k] = None
            else:
                last = out[k]
    return out


def align(srcs):
    by_slug = {}
    for s in srcs:
        by_slug.setdefault(s['slug'], []).append(s)
    os.makedirs(DATA, exist_ok=True)
    tot = {'dafs': 0, 'units': 0, 'sure': 0}
    for slug, ss in by_slug.items():
        pages = page_units(slug, sorted({d for s in ss for d in s['dafs']}))
        res = {}
        for s in ss:
            has_audio = os.path.exists(os.path.join(ROOT, audio_rel(s)))
            tr = rd(tr_path(s))
            segs = (tr or {}).get('segs') or []
            for dp in s['dafs']:
                units = (pages or {}).get(dp)
                ent = {'title': s['title'], 'from': 0}
                if has_audio:
                    ent['audio'] = '/' + audio_rel(s)
                if s.get('vid'):
                    ent['yt'] = s['vid']
                if not has_audio and not s.get('vid'):
                    continue
                if units and segs:
                    # שיעור על כמה דפים: קודם מוצאים איפה מתחיל כל דף (כיחידה אחת לכל דף)
                    t0, t1 = 0.0, None
                    if len(s['dafs']) > 1:
                        big = [{'w': sum((u['w'] for u in pages.get(d, [])), [])} for d in s['dafs']]
                        st = align_one(big, segs)
                        k = s['dafs'].index(dp)
                        t0 = st[k] if st[k] is not None else 0.0
                        nxt = [x for x in st[k + 1:] if x is not None]
                        t1 = nxt[0] if nxt else None
                        ent['from'] = st[k] or 0
                    times = align_one(units, segs, t0, t1)
                    ent['u'] = [{'t': u['t'], 's': x} for u, x in zip(units, times) if not u.get('pre')]
                    tot['sure'] += sum(1 for x in ent['u'] if x['s'] is not None)
                    tot['units'] += len(ent['u'])
                res.setdefault(heb_daf(dp), []).append(ent)
                tot['dafs'] += 1
        wr(os.path.join(DATA, slug + '.json'), res)
    idx = sorted(os.path.splitext(os.path.basename(p))[0] for p in glob.glob(os.path.join(DATA, '*.json'))
                 if not p.endswith('sources.json'))
    wr(os.path.join(DATA, 'index.json'), idx)
    print('שמע: %d עמודים עם שמע, %d יחידות, %d מהן עם נקודת התחלה ודאית' % (tot['dafs'], tot['units'], tot['sure']))
    return tot


# ---------------------------------------------------------------- build (מ-build_all)
def build(site):
    """מעתיק לאתר את נתוני השמע (site/shma/<slug>.json) ואת השמע המתארח (site/audio/)."""
    idx = rd(os.path.join(DATA, 'index.json'), []) or []
    os.makedirs(os.path.join(site, 'shma'), exist_ok=True)
    for slug in idx:
        p = os.path.join(DATA, slug + '.json')
        if os.path.exists(p):
            shutil.copy(p, os.path.join(site, 'shma', slug + '.json'))
    if os.path.isdir(AUDIO):
        shutil.copytree(AUDIO, os.path.join(site, 'audio'), dirs_exist_ok=True)
    return idx


def slugs():
    """המסכתות שיש להן שמע (מוטמע ב-lamed.js, כדי שדף בלי שמע לא יבקש דבר)."""
    return rd(os.path.join(DATA, 'index.json'), []) or []


if __name__ == '__main__':
    what = (sys.argv[1:] or ['all'])[0]
    S = sources()
    print('שמע: %d הקלטות ידועות' % len(S))
    if what in ('fetch', 'all'):
        fetch(S)
    if what in ('transcribe', 'all'):
        transcribe(S)
    if what in ('align', 'all'):
        align(S)
