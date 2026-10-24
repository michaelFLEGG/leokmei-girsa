# -*- coding: utf-8 -*-
"""factory.py - בית החרושת לתוספות (13.10.2026): שורת מסקנה + שאלות תוכן לבנק, לכל מסכת, בענן.

הכול רץ ב-GitHub Actions (`.github/workflows/tosafot-factory.yml`). המחשב של בעל הפרויקט אינו חלק מהצנרת.
כל "פעימה" (tick) קצרה ואידמפוטנטית: היא בודקת באיזה שלב נמצא כל פרק, מקדמת שלב אחד, ושומרת את המצב בקבצים.
לכן אפשר להפסיק ולהמשיך בכל רגע, והשומר (heartbeat) פשוט מפעיל פעימה כל עשר דקות.

שלבי כל פרק (tosafot/factory/state-<מסכת>.json):
  pending -> writing -> reviewing -> rewriting -> rereviewing -> ready -> published
  * writing: בקשת Batch אחת (בקשה לכל עמוד גמרא או קבוצה קטנה ממנו), מטמון לפרומפט הקבוע
  * reviewing: מבקר זול (הייקו) לכל שורה ולכל שאלה, אחרי שערי קוד קשיחים
  * rewriting: מה שנכשל נכתב מחדש פעם אחת במנוע החזק
  * rereviewing: ביקורת חוזרת; נכשל שוב ← מסומן למנהל ואינו מתפרסם
  * ready/published: הרכבת styles/anchors/live-<פרק>.json, שאלות לתור האישור, קומיט ודחיפה, הודעה

עקרונות (חוקת התוס', tosafot/תוס-חוקה.md):
  א. הד"ה מועתק בקוד בלבד; מודל אינו כותב אותו ואינו מקצר אותו.
  ב. עצירה רועשת: כל כשל נרשם בקובץ המצב וביומן, ולעולם אינו נבלע.
  ג. שורות שהמנהל כבר הכריע בהן (decided.json) אינן נכתבות מחדש.
  ד. מפתח ה-API נקרא ממשתנה הסביבה בלבד (ANTHROPIC_API_KEY). אין לכתוב אותו בשום קובץ.

פקודות:
    uv run python tools/tosafot/factory.py status
    uv run python tools/tosafot/factory.py estimate sukkah
    uv run python tools/tosafot/factory.py tick            # פעימה אחת (בענן: כל עשר דקות)
    FACTORY_MOCK=1 uv run python tools/tosafot/factory.py tick --root <עץ-לניסוי>    # מצב ניסוי בלי מפתח
"""
import os, sys, re, json, io, time, math, random, hashlib, datetime, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, 'tosafot', 'handoff', 'kit'))
from make_anchors import norm_idx, norm_ctx, find_occ
# 24.10.2026: שערי הקוד עברו למקור יחיד, tosafot/handoff/kit/gates.py (ערכת מפעל התוס' בחשבון השני). כאן רק קוראים משם.
from gates import (NIK, DASH, WORDS, TIRUTZ, is_hard, REVIEW_SYS, REWRITE_NOTE, page_user_msg, BAN_PHRASES, BAN_Q_START, QTYPES,
                   LVLS, norm_type, check_line, check_q, check_page_variety, cap_questions, parse_json, resolve_anchor, similarity)
FDIR = 'factory'
MOCK = bool(os.environ.get('FACTORY_MOCK'))


# ---------------------------------------------------------------- קבצים
def jload(p, default=None):
    if not os.path.exists(p):
        return default
    with io.open(p, encoding='utf-8') as f:
        return json.load(f)


def jdump(p, o):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + '.tmp'
    with io.open(tmp, 'w', encoding='utf-8') as f:
        json.dump(o, f, ensure_ascii=False, indent=1)
    os.replace(tmp, p)


def fp(*a):
    return os.path.join(ROOT, 'tosafot', *a)


def log(msg):
    line = '[%s] %s' % (datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), msg)
    print(line, flush=True)
    p = fp(FDIR, 'יומן.log')
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with io.open(p, 'a', encoding='utf-8') as f:
        f.write(line + '\n')


def cfg():
    return jload(fp(FDIR, 'config.json'))


# סדר המסכתות בתוך האתר (כמו build_all.py), לתרגום שם עברי ל-slug ולשם בספריא
_HE = ['ברכות', 'שבת', 'עירובין', 'פסחים', 'שקלים', 'יומא', 'סוכה', 'ביצה', 'ראש השנה', 'תענית', 'מגילה', 'מועד קטן', 'חגיגה',
       'יבמות', 'כתובות', 'נדרים', 'נזיר', 'סוטה', 'גיטין', 'קידושין', 'בבא קמא', 'בבא מציעא', 'בבא בתרא', 'סנהדרין', 'מכות', 'שבועות',
       'עבודה זרה', 'הוריות', 'זבחים', 'מנחות', 'חולין', 'בכורות', 'ערכין', 'תמורה', 'כריתות', 'מעילה', 'תמיד', 'נדה']
_LAT = ['berakhot', 'shabbat', 'eruvin', 'pesachim', 'shekalim', 'yoma', 'sukkah', 'beitzah', 'rosh-hashanah', 'taanit', 'megillah', 'moed-katan',
        'chagigah', 'yevamot', 'ketubot', 'nedarim', 'nazir', 'sotah', 'gittin', 'kiddushin', 'bava-kamma', 'bava-metzia', 'bava-batra',
        'sanhedrin', 'makkot', 'shevuot', 'avodah-zarah', 'horayot', 'zevachim', 'menachot', 'chullin', 'bekhorot', 'arakhin', 'temurah',
        'keritot', 'meilah', 'tamid', 'niddah']
HE2SLUG = dict(zip(_HE, _LAT))
SLUG2HE = dict(zip(_LAT, _HE))


def queue():
    """סדר המסכתות לפי tosafot/תור-מסכתות.md (שורות "1. סוכה"); המנהל מוסיף שם מסכת בשורה חדשה. נסיגה: config.json."""
    p = fp('תור-מסכתות.md')
    out = []
    if os.path.exists(p):
        for ln in io.open(p, encoding='utf-8').read().split('\n'):
            m = re.match(r'^\s*\d+\.\s*(.+?)\s*(?:\(.*\))?\s*$', ln)
            if m and m.group(1).strip() in HE2SLUG:
                sl = HE2SLUG[m.group(1).strip()]
                if sl not in out:
                    out.append(sl)
    return out or cfg()['queue']


def state(slug):
    return jload(fp(FDIR, 'state-%s.json' % slug)) or {'slug': slug, 'perakim': {}, 'created': now_iso()}


def save_state(slug, st):
    """כותב רק כשיש שינוי של ממש (בלי חותמת הזמן), כדי שפעימות שקטות לא ייצרו קומיטים."""
    path = fp(FDIR, 'state-%s.json' % slug)
    cur = jload(path)
    if cur is not None and {k: v for k, v in cur.items() if k != 'updated'} == {k: v for k, v in st.items() if k != 'updated'}:
        return
    st['updated'] = now_iso()
    jdump(path, st)


def now_iso():
    return datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')


def ukey(perek, n):
    return perek * 1000 + n


# ---------------------------------------------------------------- מחירים ותקציב
def price(model, usage):
    """עלות בדולרים של שימוש אחד ב-Batch (50% הנחה כבר בטבלה). usage = {in, cw, cr, out}."""
    pr = None
    for k, v in cfg()['prices'].items():
        if k in model:
            pr = v
    if not pr:
        raise SystemExit('עצירה: אין מחיר למודל ' + model)
    return (usage.get('in', 0) * pr['in'] + usage.get('cw', 0) * pr['cw'] + usage.get('cr', 0) * pr['cr']
            + usage.get('out', 0) * pr['out']) / 1e6


def ledger():
    return jload(fp(FDIR, 'cost.json')) or {'total': 0.0, 'bySlug': {}, 'byPhase': {}, 'batches': [], 'tokens': {}}


def ledger_add(slug, perek, phase, model, usage, n_requests):
    L = ledger()
    c = price(model, usage)
    L['total'] = round(L['total'] + c, 6)
    L['bySlug'][slug] = round(L['bySlug'].get(slug, 0) + c, 6)
    L['byPhase'][phase] = round(L['byPhase'].get(phase, 0) + c, 6)
    t = L['tokens'].setdefault(slug, {'in': 0, 'cw': 0, 'cr': 0, 'out': 0})
    for k in ('in', 'cw', 'cr', 'out'):
        t[k] += usage.get(k, 0)
    L['batches'].append({'at': now_iso(), 'slug': slug, 'perek': perek, 'phase': phase, 'model': model, 'n': n_requests,
                         'usage': usage, 'cost': round(c, 6)})
    jdump(fp(FDIR, 'cost.json'), L)
    return c


def budget_left():
    b = cfg()['budget']
    return b['credit'] - b.get('reservedOther', 0) - ledger()['total']


def budget_ok(est_cost):
    """False אם אחרי הבקשה היתרה צפויה לרדת מתחת לרצפה. זו הסיבה היחידה לעצור ולפנות למנהל."""
    b = cfg()['budget']
    if datetime.date.today() > datetime.date.fromisoformat(b['expires']):
        return False, 'הקרדיט פג תוקף ב-%s' % b['expires']
    left = budget_left() - est_cost
    if left < b['floor']:
        need = round(b['floor'] - left + b.get('topup', 20), 0)
        return False, 'היתרה צפויה לרדת מתחת ל-%d דולר. צריך להוסיף כ-%d דולר' % (b['floor'], need)
    return True, ''


# ---------------------------------------------------------------- לקוח (אמיתי או ניסוי)
class Real:
    def __init__(self):
        import anthropic
        self.c = anthropic.Anthropic()

    def submit(self, reqs):
        return self.c.messages.batches.create(requests=reqs).id

    def status(self, bid):
        b = self.c.messages.batches.retrieve(bid)
        return b.processing_status, b.request_counts

    def results(self, bid):
        out = {}
        for r in self.c.messages.batches.results(bid):
            res = r.result
            if res.type != 'succeeded':
                out[r.custom_id] = {'ok': False, 'err': res.type}
                continue
            m = res.message
            text = ''.join(b.text for b in m.content if getattr(b, 'type', '') == 'text')
            u = m.usage
            out[r.custom_id] = {'ok': True, 'text': text, 'model': m.model,
                                'usage': {'in': u.input_tokens or 0, 'cw': getattr(u, 'cache_creation_input_tokens', 0) or 0,
                                          'cr': getattr(u, 'cache_read_input_tokens', 0) or 0, 'out': u.output_tokens or 0}}
        return out


class Mock:
    """לבדיקת הצנרת בלי מפתח: עונה לפי תוכן הבקשה, בלי מודל. אינו מייצג איכות."""

    def __init__(self):
        self.dir = fp(FDIR, '_mock')
        os.makedirs(self.dir, exist_ok=True)

    def submit(self, reqs):
        bid = 'mock-%s' % hashlib.sha1(json.dumps([r['custom_id'] for r in reqs]).encode()).hexdigest()[:10]
        jdump(os.path.join(self.dir, bid + '.json'), reqs)
        return bid

    def status(self, bid):
        return 'ended', {}

    def results(self, bid):
        reqs = jload(os.path.join(self.dir, bid + '.json'))
        return {r['custom_id']: mock_answer(r) for r in reqs}


def mock_answer(req):
    user = req['params']['messages'][0]['content']
    model = req['params']['model']
    cid = req['custom_id']
    u = {'in': len(user) // 2, 'cw': 0, 'cr': 0, 'out': 200}
    if cid.startswith('rv'):
        ids = re.findall(r'^### מזהה: (\S+)', user, re.M)
        out = {}
        for i in ids:
            if hash(i) % 5 == 0:
                out[i] = {'s': 'לא נמצא בתוספות', 'q': []}
        return {'ok': True, 'text': json.dumps(out, ensure_ascii=False), 'model': model, 'usage': u}
    ids = re.findall(r'^### מזהה: (\S+)', user, re.M)
    lines = re.findall(r'^(\d+)\. (.+)$', user.split('## התוספות')[0], re.M)
    out = {}
    for i in ids:
        blk = user.split('### מזהה: %s' % i, 1)[1].split('### מזהה:')[0]
        m = re.search(r'פנים התוספות:\n(.+)', blk, re.S)
        body = (m.group(1) if m else blk).strip().split(' - ', 1)[-1]
        words = body.split()
        s = ' '.join(words[:14]) + (' - ' if cid.startswith('wx') else ' ') + 'ובקיצור'
        ln = lines[0] if lines else ('1', '')
        w = ln[1].split()
        out[i] = {'s': s, 'a': {'line': int(ln[0]), 't': ' '.join(w[-3:]), 'rule': 3},
                  'q': [{'t': 'קושיא', 'lvl': 'בינוני', 'q': 'מה הקושי בדברי התוספות ומה נשאר בו בצ"ע?', 'a': ' '.join(words[:10])}]
                  if len(words) > 40 else None}
    return {'ok': True, 'text': json.dumps(out, ensure_ascii=False), 'model': model, 'usage': u}


class Local:
    """ניסוי חד-פעמי על תת-קבוצה קטנה (FACTORY_LOCAL=1), דרך `claude -p` בהתחברות המקומית: לא לייצור, ולא מחליף את הענן.
    משמש לאימות איכות הפרומפט והשערים כשאין מפתח API. כל בקשה רצה בנפרד, ללא כלים וללא הקשר (llm.py)."""

    def __init__(self):
        self.dir = fp(FDIR, '_local')
        os.makedirs(self.dir, exist_ok=True)

    def submit(self, reqs):
        import llm
        bid = 'local-%s' % hashlib.sha1(json.dumps([r['custom_id'] for r in reqs]).encode()).hexdigest()[:10]
        out = {}
        for r in reqs:
            p = r['params']
            sysT = ''.join(b['text'] for b in p['system'])
            try:
                j = llm.call(p['model'], sysT, p['messages'][0]['content'], thinking=0, effort='low')
                out[r['custom_id']] = {'ok': True, 'text': j['text'], 'model': p['model'],
                                       'usage': {'in': j['in'], 'cw': 0, 'cr': 0, 'out': j['out']}}
            except Exception as e:
                out[r['custom_id']] = {'ok': False, 'err': 'local:' + str(e)[:200]}
            print('  local', r['custom_id'], 'ok' if out[r['custom_id']]['ok'] else out[r['custom_id']]['err'], flush=True)
        jdump(os.path.join(self.dir, bid + '.json'), out)
        return bid

    def status(self, bid):
        return 'ended', {}

    def results(self, bid):
        return jload(os.path.join(self.dir, bid + '.json'))


def get_client():
    if os.environ.get('FACTORY_LOCAL'):
        return Local()
    if MOCK:
        return Mock()
    if not os.environ.get('ANTHROPIC_API_KEY'):
        return None
    return Real()


# ---------------------------------------------------------------- נתוני מסכת
def load_count(slug, perek):
    return jload(fp(slug, 'count-%d.json' % perek))


def chapters(slug):
    return jload(fp(slug, 'chapters.json'))['chapters']


def decided_map(slug):
    """key -> נוסח סופי של המנהל (בחירה או עריכה). אינו נכתב מחדש לעולם."""
    return (jload(fp(slug, 'decided.json')) or {}).get('items', {})


def all_decided():
    out = {}
    for sl in cfg()['queue']:
        for k, v in decided_map(sl).items():
            out['%s:%s' % (sl, k)] = v
    return out


def pages_of(slug, perek, skip_decided=True):
    """[(dafKey, daf, [רשומות...])] לפי סדר הדף, בלי מה שהמנהל כבר הכריע."""
    cnt = load_count(slug, perek)
    dec = decided_map(slug) if skip_decided else {}
    by, order = {}, []
    for r in cnt['items']:
        if str(ukey(perek, r['n'])) in dec:
            continue
        k = (r['dafKey'], r['daf'])
        if k not in by:
            by[k] = []
            order.append(k)
        by[k].append(r)
    return [(k[0], k[1], by[k]) for k in order]


def rid(perek, n):
    return '%d-%d' % (perek, n)


# ---------------------------------------------------------------- פרומפטים
def system_prompt():
    p = fp('תוס-פרומפט-ייצור.md')
    if not os.path.exists(p):
        raise SystemExit('עצירה: אין tosafot/תוס-פרומפט-ייצור.md (build_prompt.py)')
    return io.open(p, encoding='utf-8').read()


def sys_blocks(text):
    return [{'type': 'text', 'text': text, 'cache_control': {'type': 'ephemeral', 'ttl': '1h'}}]


def est_tokens(req):
    p = req['params']
    n = sum(len(b['text']) for b in p['system']) + sum(len(m['content']) for m in p['messages'])
    return int(n / 2.0)


def est_cost(reqs):
    c = cfg()
    tot = 0.0
    for r in reqs:
        m = r['params']['model']
        tin = est_tokens(r)
        tot += price(m, {'in': tin, 'out': r['params']['max_tokens'] * 0.45})
    return tot
