# -*- coding: utf-8 -*-
"""cloud_word.py - עריכות האתר נכתבות לקובץ הוורד שבמאגר, בענן (13.11.2026).

הכרעת בעל הפרויקט, 13.11.2026: כל תיקון שהמנהל עורך או מקבל באתר, וכל סכם פרק
שאישר, נכנס לקובץ הוורד מיד. יש וורד אחד, בלי עקוב אחר שינויים, והאתר נבנה ממנו.
התכנון המלא: docs/וורד-אחד-בענן.md.

למסכת שרשומה ב-data/word-cloud.json, העותק שבמאגר (input/docx) הוא המקור. כאן:
א. השכבה = העריכות שבמאגר (data/edits/<slug>.json) ועוד מה שבשרת וטרם הגיע למאגר.
   רשומות זהות באותו רגע (אותו t ואותו תוכן, תחת שני מזהי מקום) - נשארת אחת.
ב. הקליטה עצמה היא זו של הקולט (ingest_repo.ingest_replay, דרך word_apply ו-finalize):
   טקסט סופי, בלי עקוב אחר שינויים, ותאריך העדכון של הקובץ נכתב.
ג. השער, לפני כל שמירה: הבנייה מן הוורד החדש עם מה שנשאר בשכבה זהה לבנייה מן הוורד
   הישן עם כל השכבה (מה שהמנהל רואה), ואין יותר פסקאות צמודות כפולות מקודם.
   כשל - שום דבר אינו נשמר, והכישלון נאמר ביומן ובקוד היציאה.
ד. עריכה שבוורד יוצאת מן השכבה: נמחקת מ-data/edits, נרשמת בארכיון הקליטה
   (data/word-cloud/ingested/<slug>.json, ממנו הקולט שבמחשב מעתיק לקובץ החי), ובשרת
   נכתבת לה מצבה (--tombstones, אחרי שהמאגר נדחף), כך ש-/live מפסיק להגיש אותה.

הכלי אינו דוחף ואינו כותב לשרת בהרצה הרגילה. הדחיפה בפעולת גיטהאב (word-cloud.yml),
והמצבות אחריה, כדי שעריכה לעולם לא תימחק מן השרת לפני שהוורד שנושא אותה נשמר.

    python tools/cloud_word.py                 קליטה לכל המסכתות שבענן
    python tools/cloud_word.py --only kiddushin
    python tools/cloud_word.py --dry           בלי לשמור דבר (השער רץ)
    python tools/cloud_word.py --tombstones    מצבות בשרת לכל מה שבארכיון ועדיין חי שם
    python tools/cloud_word.py --dedup <slug>... ניקוי כפילויות בלבד (מאגר; ומצבות עם --tombstones)
"""
import os, sys, io, re, html, json, copy, shutil, tempfile, hashlib, datetime, argparse, urllib.request, urllib.error

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = tempfile.mkdtemp(prefix='lg-cloud-')
# הגיבויים ויומן הקליטה של word_apply נכתבים לתיקייה זמנית: הגיבוי האמיתי הוא היסטוריית המאגר.
os.environ['LG_DRIVE'] = WORK
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

API = 'https://leokmei-suggest.m7654301.workers.dev'
CFG = os.path.join(HERE, 'data', 'word-cloud.json')
ARCH = os.path.join(HERE, 'data', 'word-cloud', 'ingested')
LOG = os.path.join(HERE, 'data', 'word-cloud', 'log.jsonl')
EDITS = os.path.join(HERE, 'data', 'edits')
DERIVED = ['data/sections', 'data/mbox', 'data/dhmiss', 'data/nikud-nakdan']
KEEP_DAYS = 14     # ארכיון הקליטה: די זמן שהקובץ החי שבמחשב והשרת ישיגו
SIG_FIELDS = ('op', 'kind', 'was', 'now', 'wasH', 'nowH', 'texts', 'resT', 'res', 'ps', 'psw', 'ins', 'where')


def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def sha(path):
    with open(path, 'rb') as f:
        return hashlib.sha1(f.read()).hexdigest()


def rjson(p, dflt=None):
    try:
        return json.load(io.open(p, encoding='utf-8'))
    except (OSError, ValueError):
        return dflt


def wjson(p, obj):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    io.open(p, 'w', encoding='utf-8', newline='\n').write(json.dumps(obj, ensure_ascii=False, indent=1) + '\n')


# ---------------------------------------------------------------- כפילויות (13.11.2026)

def ekey(e):
    return e.get('k') or ('s%s' % e.get('t') if e.get('op') == 'struct' else '')


def esig(e):
    """אותה עריכה = אותו רגע ואותו תוכן. המזהה (k) אינו חלק מן החתימה: הוא שזז."""
    return '%s|%s' % (e.get('t') or 0, json.dumps([e.get(f) for f in SIG_FIELDS], ensure_ascii=False, sort_keys=True))


def dedup(edits):
    """רשומה אחת לכל מפתח (החדשה), ואחת לכל רגע-ותוכן (האחרונה). מחזיר (נשארו, הוסרו).
    רשומות שונות באותו רגע נשמרות (נמדד: איחוי ומחיקה באותה פעולה)."""
    by_k = {}
    for e in edits:
        k = ekey(e)
        o = by_k.get(k)
        if o is None or (e.get('t') or 0) >= (o.get('t') or 0):
            by_k[k] = e
    kept_k = sorted(by_k.values(), key=lambda e: e.get('t') or 0)
    seen, out = {}, []
    for e in kept_k:
        s = esig(e)
        if s in seen:
            out[seen[s]] = e          # האחרונה גוברת
            continue
        seen[s] = len(out)
        out.append(e)
    keep_ids = {id(e) for e in out}
    gone = [e for e in edits if id(e) not in keep_ids]
    return out, gone


# ---------------------------------------------------------------- שרת

def admin_key():
    return os.environ.get('LEOKMEI_ADMIN_KEY', '').strip()


def call(method, path, body=None):
    data = json.dumps(body, ensure_ascii=False).encode('utf-8') if body is not None else None
    req = urllib.request.Request(API + path, data=data, method=method, headers={
        'content-type': 'application/json; charset=utf-8', 'x-admin-key': admin_key(),
        'user-agent': 'Mozilla/5.0 leokmei-cloud-word/1.0'})
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read().decode('utf-8'))


def server_doc(slug):
    """המסמך המלא שבשרת (כולל מצבות), או None כשאין מפתח."""
    if not admin_key():
        return None
    return (call('GET', '/edits?slug=' + slug).get('doc')) or {'edits': []}


# ---------------------------------------------------------------- מסכת וקובץ

def masechet_of_slug(slug):
    import build_all
    m = {v: k for k, v in build_all.SLUG.items()}.get(slug)
    if not m:
        raise SystemExit('עצירה: מסכת לא מוכרת: %s' % slug)
    return m


def docx_of(masechet):
    """קובץ הוורד שהבנייה בונה ממנו. מסכת מוצמדת לצילום, מפוצלת או מאוחדת - אינה נקלטת כאן."""
    import build_all
    d = os.path.join(HERE, 'input', 'docx')
    live = rjson(os.path.join(HERE, 'input', 'current-docx.json'))
    files = [f for f in sorted(os.listdir(d)) if f.endswith('.docx') and not f.startswith('~$')
             and build_all.masechet_of(f) == masechet and (not live or len(live) < 5 or f in live)]
    if len(files) != 1:
        raise RuntimeError('לקובץ הוורד של %s נמצאו %d קבצים (%s). לא נקלט.' % (masechet, len(files), ', '.join(files)))
    f = files[0]
    pins = rjson(os.path.join(HERE, 'data', 'word-pin', 'pins.json'), {}) or {}
    if f in pins:
        raise RuntimeError('%s מוצמד לצילום (%s). לא נקלט עד שההצמדה תשוחרר.' % (f, pins[f]))
    if build_all.split_of(f):
        raise RuntimeError('%s נושא כמה מסכתות. לא נקלט.' % f)
    return os.path.join(d, f)


# ---------------------------------------------------------------- הבנייה כפי שהמנהל רואה

_SP_IN_CLOSE = re.compile(r'(\s+)(</i>)')
_SP_IN_OPEN = re.compile(r'(<i [^>]*>)(\s+)')
_SP = re.compile(r'\s{2,}')


_EMPTY_I = re.compile(r'<i [^>]*></i>')


def _norm_html(t):
    """מה שנראה בדף אותו דבר נחשב אותו דבר: קטע מעוצב ריק, תו מקודד (&quot; מול "), רווח
    קשיח מול רווח, ורווח בקצה הפנימי של קטע מעוצב (<i class="am">ר"נ: </i>) מול רווח שמחוצה
    לו - לכל אלה אין ביטוי בוורד. כל אות, סימן וסגנון נשארים כמות שהם."""
    t = html.unescape(_EMPTY_I.sub('', t)).replace('\xa0', ' ')
    t = _SP_IN_CLOSE.sub(r'\2 ', t)
    t = _SP_IN_OPEN.sub(r' \1', t)
    return _SP.sub(' ', t)


def _norm_pages(pages):
    """הנתונים בלי מספרי היחידות, שזזים בין קובץ לקובץ כשפסקה נוספת או מתאחדת."""
    def strip(x):
        if isinstance(x, dict):
            return {k: strip(v) for k, v in x.items() if k not in ('id', 'mbi')}
        if isinstance(x, list):
            return [strip(v) for v in x]
        if isinstance(x, str):
            return _norm_html(x)
        return x
    return json.dumps(strip(pages), ensure_ascii=False, sort_keys=True)


def view(docx, slug, masechet, doc):
    """בונה את המסכת מן הוורד ועליו השכבה (doc; None = הוורד לבדו), כמו בבנייה של האתר.
    מחזיר (נתונים מנורמלים, סיכום ההחלה, העריכות שנשארו בשכבה)."""
    import build_site as B
    from docx2json import convert
    T = tempfile.mkdtemp(prefix='lg-view-', dir=WORK)
    if doc is not None:
        wjson(os.path.join(T, slug + '.json'), doc)
    blocks = convert(docx)
    bj = os.path.join(T, slug + '_blocks.json')
    json.dump(blocks, io.open(bj, 'w', encoding='utf-8'), ensure_ascii=False)
    cap = {}
    real_tidy, real_ase, old_dir = B._side_tidy, B._apply_site_edits, B.EDITS_DIR

    def tidy(pages, qa):
        r = real_tidy(pages, qa)
        cap['pages'] = _norm_pages(pages)
        return r

    def ase(*a, **k):
        r = real_ase(*a, **k)
        cap['stat'] = dict(r or {}, plan=copy.deepcopy(B.PLAN))
        return r
    B._side_tidy, B._apply_site_edits, B.EDITS_DIR = tidy, ase, T
    try:
        B.build(bj, os.path.join(T, slug + '.html'), masechet, hagaha=False, sources=None, spacing={})
    finally:
        B._side_tidy, B._apply_site_edits, B.EDITS_DIR = real_tidy, real_ase, old_dir
    keep = (rjson(os.path.join(T, slug + '.json'), {}) or {}).get('edits') if doc is not None else []
    shutil.rmtree(T, ignore_errors=True)
    return cap.get('pages'), cap.get('stat') or {}, keep or []


def adjacent_dups(path):
    import ingest_repo
    return ingest_repo.adjacent_dups(path)


# ---------------------------------------------------------------- קליטה של מסכת אחת

def layer(slug, masechet, srv):
    """השכבה: המאגר ועוד השרת, בלי מה שכבר בארכיון הקליטה, ובלי כפילויות."""
    rep = rjson(os.path.join(EDITS, slug + '.json')) or {'v': 1, 'slug': slug, 'masechet': masechet, 'edits': []}
    arch = rjson(os.path.join(ARCH, slug + '.json')) or {}
    done = {}
    for e in arch.get('edits') or []:
        done[ekey(e)] = max(done.get(ekey(e), 0), e.get('t') or 0)
    by = {}
    for e in (rep.get('edits') or []) + ((srv or {}).get('edits') or []):
        k = ekey(e)
        if not k:
            continue
        o = by.get(k)
        if o is None or (e.get('t') or 0) > (o.get('t') or 0):
            by[k] = e
    edits = [e for e in by.values() if not e.get('del') and (e.get('t') or 0) > done.get(ekey(e), -1)]
    for e in edits:
        if e.get('op') == 'struct' and not e.get('k'):
            e['k'] = ekey(e)
    edits.sort(key=lambda e: e.get('t') or 0)
    edits, gone = dedup(edits)
    sty = rep.get('sty') or (srv or {}).get('sty')
    doc = {'v': 1, 'slug': slug, 'masechet': masechet, 'sty': sty, 'edits': edits}
    raw = dict(doc, edits=sorted(edits + gone, key=lambda e: e.get('t') or 0))
    return rep, doc, gone, raw


def ingest_one(slug, dry, log=print):
    import ingest_repo
    masechet = masechet_of_slug(slug)
    path = docx_of(masechet)
    srv = server_doc(slug)
    rep, doc, gone, raw = layer(slug, masechet, srv)
    rec = {'when': now_iso(), 'slug': slug, 'file': os.path.basename(path), 'layer': len(doc['edits']),
           'dups': len(gone), 'server': srv is not None}
    if not doc['edits'] and not gone:
        log('%s: אין עריכות ממתינות' % masechet)
        return rec
    log('--- %s: %d עריכות בשכבה (%d כפולות הוסרו), %s' % (
        masechet, len(doc['edits']), len(gone), 'עם השרת' if srv is not None else 'בלי השרת (אין מפתח)'))
    old_sha = sha(path)
    # מה שהמנהל רואה - עם הכפילויות, כפי שהן באמת (13.11.2026: בברכות, סוכה ושבת הסרתן
    # משנה את הדף, ולכן השער משווה תמיד אל השכבה כפי שהיא, ולא אל השכבה המנוקה)
    pa, sa_raw, _ = view(path, slug, masechet, raw)
    sa = view(path, slug, masechet, doc)[1] if gone else sa_raw
    log('   מה שהמנהל רואה: %s' % json.dumps({k: sa.get(k) for k in ('n', 'done', 'taken', 'lost')}, ensure_ascii=False))
    work = os.path.join(WORK, os.path.basename(path))
    shutil.copyfile(path, work)
    dups0 = adjacent_dups(work)
    ok, bad = (0, 0)
    if sa.get('done'):
        ok, bad = ingest_repo.ingest_replay(masechet, doc, work, False, log=log)
    changed = sha(work) != old_sha
    _, sb, keep = view(work, slug, masechet, doc)
    # עריכה שאין לה שום ביטוי בוורד (למשל רווח שעבר לתוך קטע מעוצב, ראו _norm_html): אינה
    # "תלושה" ואינה ממתינה. היא יוצאת מן השכבה, והשער שלמטה מוכיח שהדף לא השתנה בגללה.
    noop = []
    for item in sb.get('plan') or []:
        if item[0] != 'text':
            continue
        # הנוסח שבוורד עכשיו (ולא זה שרשם הדפדפן): מה שעוד חסר בוורד הוא ההפרש ממנו
        e2 = dict(item[1], was=item[2]['was'], wasH=item[2]['wasH'])
        o, so, mo, sk = ingest_repo.ops_of({'sty': doc.get('sty'), 'edits': [e2]})
        if not (o or so or mo or sk):
            noop.append(item[1])
    noop_k = {(ekey(e), e.get('t')) for e in noop}
    keep = [e for e in keep if (ekey(e), e.get('t')) not in noop_k]
    final = dict(doc, edits=keep)
    pb, sf, _ = view(work, slug, masechet, final)
    pc, sc, _ = view(work, slug, masechet, None)
    dups1 = adjacent_dups(work)
    if os.environ.get('CW_DUMP'):
        D = os.environ['CW_DUMP']
        os.makedirs(D, exist_ok=True)
        shutil.copyfile(work, os.path.join(D, slug + '.docx'))
        pfull, _, _ = view(work, slug, masechet, doc)
        for n, v in (('a', pa), ('b', pb), ('full', pfull), ('c', pc)):
            io.open(os.path.join(D, n + '.json'), 'w', encoding='utf-8').write(v or '')
        wjson(os.path.join(D, 'noop.json'), noop)
        wjson(os.path.join(D, 'doc.json'), doc)
    rec.update({'wrote': ok, 'failed': bad, 'changed': changed, 'dups_before': dups0, 'dups_after': dups1,
                'noop': len(noop), 'after': {k: sf.get(k) for k in ('n', 'done', 'taken', 'lost')},
                'same_as_admin': pb == pa, 'word_alone_same': pc == pa})
    log('   אחרי הכתיבה: %s; %d בלי ביטוי בוורד; זהה למה שהמנהל רואה: %s; הוורד לבדו זהה: %s; כפילויות צמודות %d -> %d' % (
        json.dumps(rec['after'], ensure_ascii=False), len(noop), 'כן' if pb == pa else 'לא',
        'כן' if pc == pa else 'לא', dups0, dups1))
    if pb != pa or dups1 > dups0:
        rec['gate'] = 'נכשל'
        log('   השער נכשל: הוורד לא נשמר והשכבה לא נגעה.')
        return rec
    rec['gate'] = 'עבר'
    keep_k = {(ekey(e), e.get('t')) for e in keep}
    taken = [e for e in doc['edits'] if (ekey(e), e.get('t')) not in keep_k]
    rec['removed'] = len(taken)
    if dry:
        log('   (בדיקה בלבד) היו נכתבים: הוורד %s, %d עריכות יוצאות מן השכבה, %d נשארות'
            % ('השתנה' if changed else 'לא השתנה', len(taken), len(keep)))
        return rec
    if changed:
        shutil.copyfile(work, path)
    if taken or gone or len(keep) != len(rep.get('edits') or []):
        out = dict(rep, slug=slug, masechet=masechet, sty=doc.get('sty'), edits=keep, when=now_iso())
        wjson(os.path.join(EDITS, slug + '.json'), out)
    if taken or gone:
        ap = os.path.join(ARCH, slug + '.json')
        arch = rjson(ap) or {'v': 1, 'slug': slug, 'masechet': masechet, 'edits': []}
        arch['sty'] = doc.get('sty')
        have = {(ekey(e), e.get('t')) for e in arch['edits']}
        for e in taken:
            if (ekey(e), e.get('t')) not in have:
                x = dict(e, cw=rec['when'])
                if (ekey(e), e.get('t')) in noop_k:
                    x['noop'] = 1     # אין לה ביטוי בוורד: אינה נבדקת בהשגת הדרייב ואינה נקלטת במחשב
                arch['edits'].append(x)
        # כפילות שהוסרה נרשמת כמצבה בלבד (ok=0): היא לעולם אינה נכתבת לוורד.
        for e in gone:
            if (ekey(e), e.get('t')) not in have:
                arch['edits'].append({'k': ekey(e), 't': e.get('t'), 'dup': 1, 'cw': rec['when']})
        old = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=KEEP_DAYS)).strftime('%Y-%m-%dT%H:%M:%SZ')
        arch['edits'] = [e for e in arch['edits'] if (e.get('cw') or rec['when']) >= old]
        arch['edits'].sort(key=lambda e: e.get('t') or 0)
        arch['when'] = rec['when']
        wjson(ap, arch)
    log('   נשמר: הוורד %s, %d עריכות יצאו מן השכבה, %d נשארו בה' % (
        'עודכן' if changed else 'לא השתנה', len(taken), len(keep)))
    return rec


# ---------------------------------------------------------------- מצבות בשרת

def tombstones(slugs, log=print):
    """לכל רשומה בארכיון שעדיין חיה בשרת: מצבה (del) בזמן t+1. אידמפוטנטי."""
    if not admin_key():
        log('אין מפתח מנהל: המצבות לא נכתבו')
        return 1
    bad = 0
    for slug in slugs:
        arch = rjson(os.path.join(ARCH, slug + '.json')) or {}
        if not arch.get('edits'):
            continue
        try:
            srv = server_doc(slug)
        except Exception as e:
            log('%s: השרת לא ענה (%s)' % (slug, e)); bad += 1; continue
        live = {}
        for e in srv.get('edits') or []:
            live[ekey(e)] = e
        out = []
        for a in arch['edits']:
            s = live.get(ekey(a))
            if s is not None and not s.get('del') and (s.get('t') or 0) <= (a.get('t') or 0):
                out.append({'k': ekey(a), 'del': 1, 't': (a.get('t') or 0) + 1})
        if not out:
            continue
        try:
            call('PUT', '/edits', {'slug': slug, 'edits': out})
            log('%s: %d מצבות נכתבו בשרת' % (slug, len(out)))
        except Exception as e:
            bad += 1
            log('%s: המצבות לא נכתבו (%s). ינוסה שוב בסבב הבא' % (slug, e))
    return 1 if bad else 0


def archived():
    return sorted(f[:-5] for f in os.listdir(ARCH) if f.endswith('.json')) if os.path.isdir(ARCH) else []


# ---------------------------------------------------------------- הדרייב משיג את המאגר

def drive_caught_up(fname, data, log=print):
    """השומר (fetch.py) הוריד מהדרייב קובץ ששונה מן העותק שבמאגר, של מסכת שבענן. הוא נלקח
    רק אם הוא כבר נושא כל עריכה שהענן כתב (ארכיון הקליטה, בלי כפילויות ובלי עריכות שאין להן
    ביטוי בוורד): אז הוא "השיג" את המאגר, ושינוי שבעל הפרויקט עשה בוורד עצמו נכנס, והארכיון
    מתרוקן. אחרת הוא מפגר ונשאר בחוץ, בקול. עריכה שבעל הפרויקט שינה את הפסקה שלה בוורד אינה
    נחשבת חסרה (הוורד גובר)."""
    import build_all
    m = build_all.masechet_of(fname)
    slug = build_all.SLUG.get(m or '')
    if slug not in ((rjson(CFG, {}) or {}).get('slugs') or []):
        return True
    ap = os.path.join(ARCH, slug + '.json')
    arch = rjson(ap) or {}
    eds = [e for e in arch.get('edits') or [] if not e.get('dup') and not e.get('noop')]
    if eds:
        tmp = os.path.join(WORK, 'drive-' + slug + '.docx')
        open(tmp, 'wb').write(data)
        _, st, _ = view(tmp, slug, m, {'v': 1, 'slug': slug, 'masechet': m, 'sty': arch.get('sty'), 'edits': eds})
        if st.get('done'):
            log('הוורד של %s בדרייב מפגר אחרי המאגר: %d עריכות שנכתבו בענן עוד אינן בו. '
                'הוורד שבמאגר נשמר, והאתר נבנה ממנו.' % (m, st['done']))
            return False
    # הארכיון אינו נכתב כאן (השומר שומר במאגר רק את input); הוא מתקצר בקליטה, לפי גיל (KEEP_DAYS).
    log('הוורד של %s בדרייב השיג את המאגר ונלקח (%d עריכות מן הענן כבר בו).' % (m, len(eds)))
    return True


# ---------------------------------------------------------------- ניקוי כפילויות בלבד

def dedup_only(slugs, log=print):
    """מסכת שעוד אינה בענן: רק מסירה כפילויות מקובץ העריכות שבמאגר, ורושמת אותן
    בארכיון כמצבות בלבד (dup), כדי ש---tombstones ינקה גם את השרת."""
    for slug in slugs:
        p = os.path.join(EDITS, slug + '.json')
        rep = rjson(p)
        if not rep:
            continue
        keep, gone = dedup(rep.get('edits') or [])
        if not gone:
            log('%s: אין כפילויות' % slug)
            continue
        wjson(p, dict(rep, edits=keep, when=now_iso()))
        ap = os.path.join(ARCH, slug + '.json')
        arch = rjson(ap) or {'v': 1, 'slug': slug, 'masechet': rep.get('masechet'), 'edits': []}
        have = {(ekey(e), e.get('t')) for e in arch['edits']}
        for e in gone:
            if (ekey(e), e.get('t')) not in have:
                arch['edits'].append({'k': ekey(e), 't': e.get('t'), 'dup': 1, 'cw': now_iso()})
        arch['edits'].sort(key=lambda e: e.get('t') or 0)
        wjson(ap, arch)
        log('%s: %d כפולות הוסרו, %d נשארו' % (slug, len(gone), len(keep)))


def log_rec(rec):
    """יומן הקליטה במאגר: שורה לכל סבב שכתב משהו, ולכל כישלון חדש. סבב שאין בו דבר
    (רק עריכות תלושות שממתינות) אינו נרשם, כדי שלא תיווצר דחיפה בכל עשר דקות."""
    wrote = rec.get('changed') or rec.get('removed') or rec.get('dups')
    if not wrote and rec.get('gate') not in ('נכשל', 'שגיאה'):
        return
    core = lambda r: json.dumps({k: v for k, v in r.items() if k != 'when'}, ensure_ascii=False, sort_keys=True)
    last = None
    try:
        for line in io.open(LOG, encoding='utf-8'):
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get('slug') == rec.get('slug'):
                last = r
    except OSError:
        pass
    if not wrote and last is not None and core(last) == core(rec):
        return            # אותו כישלון בדיוק כבר רשום
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    io.open(LOG, 'a', encoding='utf-8', newline='\n').write(json.dumps(rec, ensure_ascii=False) + '\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', default='')
    ap.add_argument('--dry', action='store_true')
    ap.add_argument('--tombstones', action='store_true')
    ap.add_argument('--dedup', nargs='*')
    a = ap.parse_args()
    cfg = rjson(CFG, {}) or {}
    slugs = [s for s in (a.only.split(',') if a.only else cfg.get('slugs') or []) if s]
    if a.dedup is not None:
        dedup_only(a.dedup)
        if a.tombstones:
            sys.exit(tombstones(a.dedup))
        return
    if a.tombstones:
        sys.exit(tombstones(archived()))
    if not slugs:
        print('אין מסכת בענן (data/word-cloud.json)')
        return
    if not admin_key():
        # בלי מפתח (הרצה מקומית לבדיקה) אין גישה לפירוש שבמחסן; מספור קטעי המשנה בתוכנית
        # הקליטה נבנה בלעדיו. בפעולת גיטהאב המפתח קיים, והתוכנית זהה לבנייה של האתר.
        import perush_store
        _att = perush_store.attach
        perush_store.attach = lambda src, slug, strict=True: _att(src, slug, strict=False)
    if admin_key():
        tombstones(archived())     # שאריות מסבב קודם שהדחיפה שלו הצליחה והמצבות לא
    fail = 0
    for slug in slugs:
        try:
            rec = ingest_one(slug, a.dry)
        except Exception as e:
            import traceback
            traceback.print_exc()
            rec = {'when': now_iso(), 'slug': slug, 'gate': 'שגיאה', 'error': str(e)[:300]}
            print('%s: נעצר - %s' % (slug, e))
        if rec.get('gate') in ('נכשל', 'שגיאה'):
            fail += 1
        if not a.dry:
            log_rec(rec)
    shutil.rmtree(WORK, ignore_errors=True)
    sys.exit(1 if fail else 0)


if __name__ == '__main__':
    main()
