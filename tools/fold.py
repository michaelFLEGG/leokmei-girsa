# -*- coding: utf-8 -*-
"""fold.py - הקיפול הלילי (פרומפט 51, 16.11.2026).

העיקרון: עורכים רק באתר. העריכות נשמרות בשרת ומוגשות לכל גולש ב-/live מיד. פעם בלילה
(ובכפתור "קפל עכשיו" למנהל) השכבה נכנסת לספר (הוורד הקנוני שבמאגר, input/docx), והשכבה
מתרוקנת. אין כותב אחר לספר: לא אדם, לא המחשב, לא הדרייב.

השיטה היא זו שהוכחה בהמרות של ברכות ושבת (docs/ענן/כלים-ברכות-15.11, כלים-שבת-16.11):
א. A = מה שהמנהל רואה: הבנייה מן הספר עם כל השכבה (מאגר + שרת).
ב. כל עמוד שבו A שונה מן הספר לבדו מסונכרן אל A (word_apply.sync_to_target).
ג. בנייה מן הספר החדש לבדו. עמוד שעדיין שונה מ-A חוזר לנוסח הקודם שלו, ועריכותיו נשארות
   בשכבה (עד הלילה הבא, ובקול ביומן).
ד. השער: הספר החדש עם מה שנשאר בשכבה זהה ל-A בכל עמוד, ואין יותר פסקאות צמודות כפולות.
   נכשל - שום דבר אינו נשמר, והכלי יוצא בקוד שגיאה.
ה. עברו: הספר נשמר, השכבה שבמאגר = מה שנשאר, כל השאר עובר לארכיון (data/word-cloud/ingested,
   ממנו נכתבות המצבות בשרת אחרי הדחיפה: --tombstones). עריכה תלושה (אינה נראית היום בדף)
   אינה מוחלת, ונרשמת לעיון ב-data/fold/tlushot/<slug>.json.

    python tools/fold.py --only berakhot --dry
    python tools/fold.py                       כל המסכתות שב-data/book.json
    python tools/fold.py --tombstones          מצבות בשרת (אחרי הדחיפה)
"""
import os, sys, io, re, json, copy, shutil, tempfile, zipfile, argparse, datetime, urllib.request

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cloud_word as C            # מגדיר LG_DRIVE לתיקייה זמנית
import word_apply as WA
from docx2json import convert
from lxml import etree

CFG = os.path.join(HERE, 'data', 'book.json')
DEBUG = {}
FOLD = os.path.join(HERE, 'data', 'fold')
LOG = os.path.join(FOLD, 'log.jsonl')
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

# ---------------------------------------------------------------- התאמות הסגנונות (כמו בהמרות 15-16.11)
import styles_map as SM
import difflib
WA.SYNC_TYPE['חלון 3'] = 'S'; WA.SYNC_TYPE["משנה ד''ה"] = 'D'
WA.SYNC_NEW_STYLE['S'] = 'חלון 3'
if 'נקודה' not in WA.SYNC_PS:
    WA.SYNC_PS = WA.SYNC_PS + ('נקודה',)
_CS_BASE = {'hs': 'הסבר', 'kt': 'כותרת 3 תו', 'ot': 'אות בודדת תו', 'tn': 'תנאי משנה תו'}
_DM0 = WA._SYNC_CS.get('dm')
_CS_BY_SLUG = {'berakhot': {'dm': "משנה ד''ה תו"}}
ARROW = '→'


def _sig(pairs):
    ch = []
    for t, c in pairs:
        t = (t or '').replace('\xa0', ' ').replace('\t', ' ').replace(ARROW, ' ')
        for x in t:
            ch.append((x, None if x == ' ' else c))
    out = []
    for x, c in ch:
        if x == ' ' and out and out[-1][0] == ' ':
            continue
        out.append((x, c))
    s, cur = '', None
    for x, c in out:
        if c != cur:
            if cur: s += '}'
            if c: s += '{' + c + ':'
            cur = c
        s += x
    if cur: s += '}'
    return s


def _bsig(b):
    pairs = []
    for r in b['runs']:
        if r.get('cs') == WA.NUMBER_STYLE: continue
        c = SM.CS.get(r.get('cs'))
        if r.get('b') and not c: c = 'b'
        pairs.append((r['t'], c))
    ws = any(c and not (t or '').strip() for t, c in pairs)
    return _sig(pairs) + ('\x01' if ws else '')


def sync_plan(blocks, lo, hi, target):
    have = [(b['i'], WA._sync_block_type(b)) for b in blocks[lo:hi]]
    have = [(i, t) for i, t in have if t]
    hk = ['X:חציצה' if t == 'X:חציצה' else WA.sync_key(t, WA._sync_block_text(blocks[i]), blocks[i]['style']) + '\x00' + _bsig(blocks[i]) for i, t in have]
    tk = ['X:חציצה' if x['t'] == 'X:חציצה' else WA.sync_key(WA.sync_type(x), ''.join(s for s, _ in WA.sync_runs(x['m'])), x.get('ps')) + '\x00' + _sig(WA.sync_runs(x['m'])) for x in target]
    sm = difflib.SequenceMatcher(None, hk, tk, autojunk=False)
    return have, hk, tk, sm.get_opcodes()


WA.sync_plan = sync_plan
WA.NUMBER_STYLE = '__none__'
WA._SYNC_T2C['מק'] = 'mk'
WA._SYNC_CS['mk'] = 'מספר קטע'
import mishna_box as _MB
XST = ('חציצה', 'משנה בצד', 'דפים בפרק ב', 'פתיחת פרק', 'הדרן')
_bt0 = WA._sync_block_type


def _sync_block_type(b):
    st = b['style']
    if st in XST:
        if st == 'משנה בצד' and not _MB.MBW.match(b['text']): return None
        if not b['text'].strip(): return None
        return 'X:' + st
    return _bt0(b)


WA._sync_block_type = _sync_block_type


def set_slug_styles(slug):
    WA._SYNC_CS.update(_CS_BASE)
    WA._SYNC_CS['dm'] = _DM0
    WA._SYNC_CS.update(_CS_BY_SLUG.get(slug, {}))

# ---------------------------------------------------------------- היעד מתוך הדף (target.py של ההמרות)
import html as _html
INV = {'mk': 'מק', 'am': 'אם', 'hs': 'הס', 'ps': 'פס', 'dm': 'דה', 'ns': 'נש', 'mf': 'מפ', 'b': 'ב', 'tn': 'מש', 'kt': 'כב', 'ot': 'אות'}


def to_inter(h):
    def rep(m):
        c = m.group(1).split()[0] if m.group(1) else ''
        t = m.group(2)
        if not _html.unescape(re.sub(r'<[^>]+>', '', t)).strip(): return t
        tag = INV.get(c)
        return '{%s:%s}' % (tag, t) if tag else t
    s = re.sub(r'<i class="([^"]*)">(.*?)</i>', rep, h or '', flags=re.S)
    s = re.sub(r'<br\s*/?>', ' ', s)
    s = re.sub(r'<[^>]+>', '', s)
    return _html.unescape(s).replace('‏', '')


def plain(h):
    return re.sub(r'\s+', ' ', _html.unescape(re.sub(r'<[^>]+>', ' ', h or '')).replace('\xa0', ' ')).strip()


def ps_of(cls):
    t = (cls or '').split()
    if 'nk' in t: return 'נקודה'
    if 'hr' in t: return 'רקע והסבר'
    if 'in' in t: return 'פיסקת תשובה'
    if 'sp' in t: return 'רווח לפני'
    return None


def items_of_page(pg):
    out = []

    def side(a):
        for part in re.split(r'<br\s*/?>', a or ''):
            if plain(part):
                out.append({'t': 'S', 'm': to_inter(part)})
    for u in pg['units']:
        k = u.get('k')
        if k == 'u':
            side(u.get('a'))
            for li, (cls, h) in enumerate(u.get('l') or []):
                if cls == 'hatz':
                    # חציצה (***) שהבנייה שמה בתוך היחידה - בוורד היא פסקת חציצה, כמו יחידת חציצה
                    if plain(h): out.append({'t': 'X:חציצה', 'm': to_inter(h), 'ps': 'חציצה'})
                    continue
                cl = (cls or '').split()
                # שורה שהמנהל עשה לה "כותרת נושא" / "כותרת ד"ה משנה" בעורך: בוורד היא פסקת כותרת
                if 'nose' in cl or 'dh' in cl:
                    out.append({'t': 'H' if 'nose' in cl else 'D', 'm': to_inter(h)})
                    continue
                if not plain(h):
                    continue            # שורה ריקה לגמרי: אין לה פסקה בוורד
                # פרומפט 53 (17.11.2026): מעוין - בוורד חלון שכל תוכנו ◆ לפני הפסקה (הבנייה מחזירה אותו למחלקה mu).
                # פסקה ראשונה של יחידה שיש לה כותרת צד: הכותרת במקום המעוין
                if 'mu' in cl and not (li == 0 and plain(u.get('a'))):
                    out.append({'t': 'S', 'm': '\u25c6'})
                it = {'t': 'L', 'm': to_inter(h)}
                p = ps_of(cls)
                if p: it['ps'] = p
                out.append(it)
        elif k == 'm':
            if u.get('mbw') and u.get('mbh') == 'word':
                out.append({'t': 'X:משנה בצד', 'm': u['mbw'], 'ps': 'משנה בצד'})
            side(u.get('w'))
            for cls, h in u.get('l') or []:
                if cls == 'hatz':
                    if plain(h): out.append({'t': 'X:חציצה', 'm': to_inter(h), 'ps': 'חציצה'})
                    continue
                out.append({'t': 'L', 'm': to_inter(h), 'ps': 'משניות'})
        elif k in ('hatz', 'perek-range', 'perek-start', 'hadran'):
            st = {'hatz': 'חציצה', 'perek-range': 'דפים בפרק ב', 'perek-start': 'פתיחת פרק', 'hadran': 'הדרן'}[k]
            out.append({'t': 'X:' + st, 'm': to_inter(u.get('a')), 'ps': st})
        elif k in ('dh', 'nose'):
            side(u.get('w'))
            out.append({'t': 'D' if k == 'dh' else 'H', 'm': to_inter(u.get('a'))})
    return out

# ---------------------------------------------------------------- בנייה ונרמול


def view(docx, slug, masechet, doc):
    """הבנייה כמו באתר: (עמודים גולמיים, סיכום ההחלה). doc=None - הספר לבדו."""
    import build_site as B
    T = tempfile.mkdtemp(prefix='lg-fold-', dir=C.WORK)
    if doc is not None:
        C.wjson(os.path.join(T, slug + '.json'), doc)
    blocks = convert(docx)
    bj = os.path.join(T, slug + '_blocks.json')
    json.dump(blocks, io.open(bj, 'w', encoding='utf-8'), ensure_ascii=False)
    cap = {}
    real_tidy, real_ase, old_dir = B._side_tidy, B._apply_site_edits, B.EDITS_DIR

    def tidy(p, qa):
        r = real_tidy(p, qa); cap['pages'] = copy.deepcopy(p); return r

    def ase(*a, **k):
        r = real_ase(*a, **k); cap['stat'] = dict(r or {}); return r
    B._side_tidy, B._apply_site_edits, B.EDITS_DIR = tidy, ase, T
    try:
        B.build(bj, os.path.join(T, slug + '.html'), masechet, hagaha=False, sources=None, spacing={})
    finally:
        B._side_tidy, B._apply_site_edits, B.EDITS_DIR = real_tidy, real_ase, old_dir
    st = cap.get('stat') or {}
    # העריכות שהבנייה השאירה בקובץ: כל מה שלא נמצא כבר בוורד ("נקלט")
    st['keep'] = [e for e in ((C.rjson(os.path.join(T, slug + '.json'), {}) or {}).get('edits') or []) if not e.get('del')] if doc is not None else []
    shutil.rmtree(T, ignore_errors=True)
    return cap['pages'], st


def _fix(x):
    if isinstance(x, dict): return {k: _fix(v) for k, v in x.items()}
    if isinstance(x, list): return [_fix(v) for v in x]
    if isinstance(x, str):
        t = x
        for _ in range(3): t = re.sub(r'<i [^>]*>(\s*)</i>', r'\1', t)
        t = re.sub(r'  +', ' ', t)
        for _ in range(6): t = re.sub(r'<i class="([a-z]+)">([^<]*)</i>( ?)<i class="\1">', r'<i class="\1">\2\3', t)
        return t
    return x


def norm(pages):
    return json.dumps(_fix(json.loads(C._norm_pages(pages))), ensure_ascii=False, sort_keys=True)


def _wsn(t):
    t = (t or '').replace('\xa0', ' ').replace('\u200f', '')
    for _ in range(3): t = re.sub(r'\{[^:{}]+:(\s*)\}', r'\1', t)            # קטע מעוצב ריק
    t = re.sub(r'\s+', ' ', t)
    # רווח בקצה הפנימי של קטע מעוצב שקול לרווח שמחוצה לו (אין לו ביטוי בדף)
    for _ in range(3):
        t = re.sub(r'\{([^:{}]+):([^{}]*?) \}', r'{\1:\2} ', t)
        t = re.sub(r'\{([^:{}]+): ([^{}]*)\}', r' {\1:\2}', t)
    t = re.sub(r' +', ' ', t).strip()
    for _ in range(6): t = re.sub(r'\{([^:{}]+):([^{}]*)\}( ?)\{\1:', r'{\1:\2\3', t)   # אותו עיצוב משני צדי רווח
    return t


def page_sig(pg):
    """מה שהוורד נושא מן העמוד: כל שורה, לפי הסדר, עם סוגה, נוסחה, סגנונות התו וסגנון הפסקה.
    החלוקה ליחידות (בלי כותרת צד) נגזרת בבנייה מן הוורד עצמו, ולכן אינה חלק מן ההשוואה."""
    return json.dumps([(x['t'], _wsn(x['m']), x.get('ps') or '') for x in items_of_page(pg)], ensure_ascii=False)


def same_page(a, b):
    return page_sig(a) == page_sig(b)


def _page_plain(pg):
    out = []
    for u in pg.get('units') or []:
        for k in ('a', 'w', 'mbw'):
            if isinstance(u.get(k), str): out.append(plain(u[k]))
        for l in u.get('l') or []:
            out.append(plain(l[1]))
    return ' \n '.join(out)


def markers(blocks):
    return [k for k, x in enumerate(blocks) if x['style'] == 'דף בצד' and x['text'].strip()]


def revert_pages(src, dst, pages):
    """העמודים שנמסרו חוזרים בספר החדש (dst) לנוסח שלהם בספר הקודם (src), פסקה בפסקה."""
    if not pages:
        return
    bs = convert(src); pms = dict(convert.last.get('pmap') or {})
    ms = [pms[i] for i in markers(bs)]
    bd = convert(dst); pmd = dict(convert.last.get('pmap') or {})
    md = [pmd[i] for i in markers(bd)]
    if len(ms) != len(md):
        raise RuntimeError('מספר ציוני הדף שונה בין הספר הקודם לחדש')
    z = zipfile.ZipFile(src); ds = etree.fromstring(z.read('word/document.xml')); z.close()
    z = zipfile.ZipFile(dst); dd = etree.fromstring(z.read('word/document.xml')); z.close()
    ps = ds.find(W + 'body').findall(W + 'p')
    body = dd.find(W + 'body')
    for n in sorted(pages, reverse=True):
        pd = body.findall(W + 'p')
        s_lo, s_hi = ms[n] + 1, (ms[n + 1] if n + 1 < len(ms) else len(ps))
        d_lo, d_hi = md[n] + 1, (md[n + 1] if n + 1 < len(md) else len(pd))
        anchor = pd[d_lo - 1]
        for p in pd[d_lo:d_hi]:
            body.remove(p)
        for p in reversed(ps[s_lo:s_hi]):
            anchor.addnext(copy.deepcopy(p))
    tmp = dst + '.rev'
    zin = zipfile.ZipFile(dst); zout = zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED)
    for it in zin.infolist():
        data = zin.read(it.filename)
        if it.filename == 'word/document.xml':
            data = etree.tostring(dd, xml_declaration=True, encoding='UTF-8', standalone=True)
        zout.writestr(it, data)
    zin.close(); zout.close()
    os.replace(tmp, dst)

# ---------------------------------------------------------------- השכבה


def live_doc(slug):
    """המסמך שבשרת: עם מפתח המנהל (כולל מצבות), ובלעדיו /live הציבורי."""
    if C.admin_key():
        return C.server_doc(slug)
    req = urllib.request.Request(C.API + '/live?slug=' + slug, headers={'user-agent': 'Mozilla/5.0 leokmei-fold/1.0'})
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read().decode('utf-8')).get('doc') or {'edits': []}


def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def log_rec(rec):
    os.makedirs(FOLD, exist_ok=True)
    io.open(LOG, 'a', encoding='utf-8', newline='\n').write(json.dumps(rec, ensure_ascii=False) + '\n')


# ---------------------------------------------------------------- קיפול מסכת אחת

def fold_one(slug, dry=False, log=print, srv=None):
    import time
    t0 = time.time()
    m = C.masechet_of_slug(slug)
    set_slug_styles(slug)
    docx = C.docx_of(m)
    if srv is None:
        srv = live_doc(slug)
    rep, doc, gone, raw = C.layer(slug, m, srv)
    rec = {'when': now_iso(), 'slug': slug, 'file': os.path.basename(docx), 'layer': len(raw['edits'])}
    if not raw['edits']:
        log('%s: השכבה ריקה, אין מה לקפל' % m)
        rec['result'] = 'ריק'
        return rec
    A, ast = view(docx, slug, m, raw)
    W0, _ = view(docx, slug, m, None)
    b0 = convert(docx)
    mk = markers(b0)
    if len(A) != len(W0) or len(A) != len(mk):
        rec.update(result='נכשל', why='מספר העמודים שונה (מה שהמנהל רואה %d, הספר %d, ציוני דף %d)' % (len(A), len(W0), len(mk)))
        log('%s: %s' % (m, rec['why']))
        return rec
    changed = [n for n in range(len(A)) if not same_page(A[n], W0[n])]
    rec['changed_pages'] = len(changed)
    log('%s: שכבה %d עריכות, %d עמודים שונים מן הספר' % (m, len(raw['edits']), len(changed)))
    work = os.path.join(C.WORK, 'fold-' + slug + '.docx')
    shutil.copyfile(docx, work)
    DEBUG.update(A=A, W0=W0, work=work, raw=raw, ast=ast)
    failed_sync = []
    if DEBUG.get('work_in') and os.path.exists(DEBUG['work_in']):
        shutil.copyfile(DEBUG['work_in'], work); changed_sync = []
    else:
        changed_sync = changed
    for n in changed_sync:
        b = convert(work)
        dix = markers(b)
        lo = dix[n] + 1
        hi = dix[n + 1] if n + 1 < len(dix) else len(b)
        try:
            WA.sync_to_target(work, m, [(lo, hi, items_of_page(A[n]))], log=lambda *a: None)
        except WA.Refused as e:
            failed_sync.append((n, A[n]['daf'], str(e)[:160]))
    if failed_sync:
        log('%s: %d עמודים לא סונכרנו: %s' % (m, len(failed_sync), ', '.join(d for _, d, _ in failed_sync[:20])))
    if DEBUG.get('work_out'):
        shutil.copyfile(work, DEBUG['work_out'])
    reverted = set(n for n, _, _ in failed_sync)
    for _round in range(4):
        N, _ = view(work, slug, m, None)
        if len(N) != len(A):
            rec.update(result='נכשל', why='אחרי הסנכרון מספר העמודים השתנה (%d מול %d)' % (len(N), len(A)))
            log('%s: %s' % (m, rec['why']))
            return rec
        bad = [n for n in range(len(A)) if n not in reverted and not same_page(N[n], A[n])]
        DEBUG.setdefault('N', N)
        if DEBUG.get('stop_after_sync'):
            import pickle; shutil.copyfile(work, DEBUG['stop_after_sync'] + '.docx')
            pickle.dump({k: v for k, v in DEBUG.items() if k != 'stop_after_sync'}, open(DEBUG['stop_after_sync'] + '.pkl', 'wb'))
            raise SystemExit('נעצר לבדיקה')
        if not bad:
            break
        bad = sorted({j for n in bad for j in (n - 1, n, n + 1) if 0 <= j < len(A)} - reverted)
        log('%s: %d עמודים (עם שכניהם) אינם זהים אחרי הסנכרון וחוזרים: %s' % (m, len(bad), ', '.join(A[n]['daf'] for n in bad[:20])))
        revert_pages(docx, work, bad)
        reverted |= set(bad)
    else:
        rec.update(result='נכשל', why='עמודים שאינם מתייצבים אחרי ארבעה סבבים')
        return rec
    # השכבה שנשארת: העריכות שנעשו בעמודים שחזרו לנוסחם הקודם. עמוד שהשער מוצא שונה ממה שהמנהל רואה
    # חוזר גם הוא, יחד עם שכניו (העיגון בטקסט מחפש עמוד לכל צד), ושוב - עד שהשער עובר, או שישה סבבים.
    # (נבדק 16.11: החלת כל השכבה על הספר החדש מכפילה עריכות מבנה, ולכן לא.)
    baked = set(ast.get('b') or [])
    lost = [e for e in raw['edits'] if e.get('t') not in baked and not e.get('del')]
    lost_t = {e.get('t') for e in lost}
    diff, remain = [], []
    for _round in range(9):
        rdaf = {A[n]['daf'] for n in reverted}
        remain0 = [e for e in raw['edits'] if e.get('daf') in rdaf and e.get('t') not in lost_t]
        # מספרי היחידות זזים בספר החדש. בעמודים שחזרו הנוסח זהה, ולכן היחידות מתאימות לפי מקומן בעמוד:
        # מפתח העריכה עובר למספר החדש, כדי שתמצא את מקומה בדיוק כמו קודם (ולא בחיפוש לפי טקסט).
        W1, _ = view(work, slug, m, None)
        idmap = {}
        for n in reverted:
            ua, ub = W0[n]['units'], W1[n]['units']
            if len(ua) == len(ub) and all(x.get('k') == y.get('k') for x, y in zip(ua, ub)):
                for x, y in zip(ua, ub):
                    if x.get('id') is not None and y.get('id') is not None:
                        idmap[str(x['id'])] = str(y['id'])
            else:
                log('%s: בעמוד %s שחזר היחידות אינן מתאימות (%d מול %d) - העריכות שבו נשארות במפתח הישן' % (m, A[n]['daf'], len(ua), len(ub)))
        remain, rekeyed = [], []
        for e in remain0:
            mm = re.match(r'^u(\d+)(\..*)$', e.get('k') or '')
            if mm and idmap.get(mm.group(1)) and idmap[mm.group(1)] != mm.group(1):
                ne = dict(e, k='u' + idmap[mm.group(1)] + mm.group(2))
                remain.append(ne); rekeyed.append((e, ne))
            else:
                remain.append(e)
        V, _ = view(work, slug, m, dict(raw, edits=remain))
        if len(V) != len(A):
            diff = ['מספר העמודים']; break
        badn = [n for n in range(len(A)) if not same_page(V[n], A[n])]
        diff = [A[n]['daf'] for n in badn]
        if not badn:
            break
        newb = []
        for rad in (1,):
            newb = sorted({j for n in badn for j in range(n - rad, n + rad + 1) if 0 <= j < len(A)} - reverted)
            if newb:
                break
        log('%s: השער מצא %d עמודים שונים (%s)%s' % (m, len(badn), ', '.join(diff[:12]), ', חוזרים עם שכניהם' if newb else ''))
        if not newb:
            break
        revert_pages(docx, work, newb)
        reverted |= set(newb)
    rdaf = {A[n]['daf'] for n in reverted}
    if diff and len(V) == len(A):
        for n in [n for n in range(len(A)) if not same_page(V[n], A[n])][:6]:
            a_, b_ = json.loads(page_sig(A[n])), json.loads(page_sig(V[n]))
            for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, [json.dumps(x, ensure_ascii=False) for x in a_], [json.dumps(x, ensure_ascii=False) for x in b_], autojunk=False).get_opcodes():
                if op != 'equal':
                    log('   %s %s | המנהל רואה: %s | הספר נותן: %s' % (A[n]['daf'], op, json.dumps(a_[i1:i2][:2], ensure_ascii=False)[:300], json.dumps(b_[j1:j2][:2], ensure_ascii=False)[:300]))
                    break
    if diff:
        rec.update(result='נכשל', why='השער: %d עמודים שונים ממה שהמנהל רואה (%s)' % (len(diff), ', '.join(diff[:12])))
        log('%s: %s' % (m, rec['why']))
        return rec
    d0, d1 = C.adjacent_dups(docx), C.adjacent_dups(work)
    if d1 > d0:
        rec.update(result='נכשל', why='פסקאות צמודות כפולות: %d לפני, %d אחרי' % (d0, d1))
        log('%s: %s' % (m, rec['why']))
        return rec
    keep_k = {(C.ekey(e), e.get('t')) for e in remain}
    # עריכה שמפתחה הוחלף יוצאת במפתח הישן (מצבה), ונכתבת לשרת במפתח החדש (--tombstones)
    retired = [e for e in raw['edits'] if (C.ekey(e), e.get('t')) not in keep_k]
    rec['rekeyed'] = len(rekeyed)
    rec.update(result='עבר', reverted=sorted(rdaf), remain=len(remain), retired=len(retired), tlushot=len(lost),
               dups=[d0, d1], secs=int(time.time() - t0))
    log('%s: השער עבר. %d עמודים נכנסו לספר, %d חזרו, %d עריכות יצאו מן השכבה, %d נשארו, %d תלושות לעיון'
        % (m, len(changed) - len(reverted), len(reverted), len(retired), len(remain), len(lost)))
    if dry:
        rec['dry'] = True
        return rec
    # שמירה
    shutil.copyfile(work, docx)
    C.wjson(os.path.join(C.EDITS, slug + '.json'),
            dict(rep, edits=sorted(remain, key=lambda e: e.get('t') or 0), when=now_iso()))
    ap = os.path.join(C.ARCH, slug + '.json')
    arch = C.rjson(ap) or {'v': 1, 'slug': slug, 'masechet': m, 'edits': []}
    arch['sty'] = raw.get('sty') or arch.get('sty')
    have = {(C.ekey(e), e.get('t')) for e in arch['edits']}
    for e in retired:
        if (C.ekey(e), e.get('t')) not in have:
            arch['edits'].append(dict(e, cw=now_iso(), fold=1))
    arch['edits'].sort(key=lambda e: e.get('t') or 0)
    C.wjson(ap, arch)
    if rekeyed:
        C.wjson(os.path.join(FOLD, 'rekey', slug + '.json'),
                {'v': 1, 'slug': slug, 'when': now_iso(), 'edits': [ne for _, ne in rekeyed], 'sty': raw.get('sty')})
    if lost:
        tp = os.path.join(FOLD, 'tlushot', slug + '.json')
        old = C.rjson(tp) or {'v': 1, 'slug': slug, 'masechet': m, 'edits': []}
        seen = {(C.ekey(e), e.get('t')) for e in old['edits']}
        for e in lost:
            if (C.ekey(e), e.get('t')) not in seen:
                old['edits'].append(dict(e, folded=now_iso()))
        C.wjson(tp, old)
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', default='')
    ap.add_argument('--dry', action='store_true')
    ap.add_argument('--tombstones', action='store_true')
    a = ap.parse_args()
    cfg = C.rjson(CFG, {}) or {}
    slugs = [s for s in (a.only.split(',') if a.only else cfg.get('slugs') or []) if s]
    if a.tombstones:
        bad = 0
        for s_ in slugs:
            rp = os.path.join(FOLD, 'rekey', s_ + '.json')
            rk = C.rjson(rp) or {}
            if rk.get('edits') and not rk.get('pushed'):
                try:
                    C.call('PUT', '/edits', {'slug': s_, 'edits': rk['edits'], 'sty': rk.get('sty')})
                    rk['pushed'] = now_iso(); C.wjson(rp, rk)
                    print('%s: %d עריכות נכתבו לשרת במפתח החדש' % (s_, len(rk['edits'])))
                except Exception as e:
                    print('%s: העריכות במפתח החדש לא נכתבו (%s). המצבות לא נכתבות' % (s_, e)); bad = 1
                    slugs = [x for x in slugs if x != s_]
        return C.tombstones(slugs) or bad
    bad = 0
    for s in slugs:
        try:
            rec = fold_one(s, dry=a.dry)
        except Exception as e:
            import traceback; traceback.print_exc()
            rec = {'when': now_iso(), 'slug': s, 'result': 'שגיאה', 'why': str(e)[:300]}
        if not a.dry:
            log_rec(rec)
        print(json.dumps(rec, ensure_ascii=False))
        if rec.get('result') in ('נכשל', 'שגיאה'):
            bad += 1
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
