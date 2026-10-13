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
from make_anchors import norm_idx, norm_ctx, find_occ

NIK = re.compile('[֑-ׇ]')
DASH = re.compile('[–—―]')
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


def get_client():
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


WORDS = re.compile(r'\S+')
TIRUTZ = re.compile(r'וי"ל|ויש לומר|ותירץ|תי\'|ועוד י"ל|וי״ל|ואומר ר"י|וי"מ|ואם תאמר|וא"ת|וקשה')


def is_hard(r, c):
    n = len(WORDS.findall(r['text']))
    t = len(TIRUTZ.findall(r['text']))
    return n >= c['hard']['words'] or t >= c['hard']['markers']


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


REVIEW_SYS = (
    'אתה מבקר זהיר של הערות שוליים לתוספות בספר לימוד של הש"ס. לכל תוספות יוגשו: פנים התוספות, שורת מסקנה, ושאלות (אם יש). '
    'בדוק מול לשון התוספות בלבד: '
    '(1) המסקנה אומרת רק מה שבתוספות, בלי הוספה, בלי פירוש משלך ובלי החלפת דעה (למשל ייחוס לר"ת מה שאינו שלו); '
    '(2) המסקנה ברורה לבן ישיבה ואינה חוזרת על הדיבור המתחיל ואינה בלשון מכונה או תרגום; '
    '(3) כל שאלה: התשובה נמצאת בתוספות עצמו, השאלה אינה מסגירה את התשובה, אינה בנאלית ("מה שאל התוס\'", "מה תירץ התוס\'"), '
    'אינה בלשון מכונה ("מה ההסבר ל", "כיצד מתמודדים עם", "בהתאם ל", "נשאלת השאלה", "יש לציין"), ואינה כפולה לשאלה אחרת באותה בקשה. '
    'החזר JSON אחד בלבד, בלי גדרות קוד: אובייקט שהמפתחות בו מזהי התוספות שיש בהם בעיה בלבד. '
    'לכל כזה: {"s": "<סיבה קצרה, או ריק אם השורה תקינה>", "q": ["<סיבה לשאלה 1 או ריק>", ...]}. '
    'תוספות תקין אינו מופיע. אל תכתוב קו מפריד ארוך (em dash או en dash).')

REWRITE_NOTE = ('\n\n## תיקון\nהגרסה הקודמת נפסלה. הסיבות מצוינות לכל תוספות. כתוב מחדש אך ורק את מה שנפסל, '
                'בהתאם לכללי ההנחיה הקבועה, והחזר את אותו פורמט JSON עבור המזהים שלהלן בלבד.')


def page_user_msg(slug, perek, dafKey, ctx, recs, ctxp, extra=''):
    lines = '\n'.join('%d. %s' % (i + 1, l) for i, l in enumerate(ctxp['lines']))
    gem = '\n'.join('%d. %s' % (i + 1, NIK.sub('', g)) for i, g in enumerate(ctxp['gemara']))
    blocks = []
    for r in recs:
        blocks.append('### מזהה: %s\nעל שורת גמרא: %d\nדיבור המתחיל (מוצג ללומד בנפרד, אל תחזור עליו): %s\nפנים התוספות:\n%s'
                      % (r['rid'], r['line'], r['dh'], r['text']))
    return ('מסכת %s, פרק %d, עמוד %s.\n\n## שורות הלאוקמי גירסא של העמוד (ממוספרות)\n%s\n\n## שורות הגמרא המקוריות של העמוד\n%s\n\n'
            '## התוספות\n%s%s\n\n'
            'החזר JSON אחד בלבד, בלי גדרות קוד ובלי טקסט נוסף: {"<מזהה>": {"s": "<שורת מסקנה>", '
            '"a": {"line": <מספר שורת לאוקמי>, "t": "<2 עד 6 מילים רצופות מתוך שורות הלאוקמי>", "rule": 1|2|3}, '
            '"q": null או [{"t": "<סוג>", "lvl": "קל|בינוני|קשה", "q": "<שאלה>", "a": "<תשובה>"}]}}.'
            % (ctx['masechet'], perek, dafKey, lines, gem, '\n\n'.join(blocks), extra))


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


# ---------------------------------------------------------------- שערי קוד
BAN_PHRASES = ['מה ההסבר ל', 'כיצד מתמודדים עם', 'מהי הסוגיה המרכזית', 'בהתאם ל', 'נשאלת השאלה', 'יש לציין',
               'התוספות שואל', "התוס' שואל", 'התוספות מקשה', 'בנוסף לכך', 'כמו כן']
BAN_Q_START = [re.compile(p) for p in (r'^מה שאל התוס', r'^מה תירץ התוס', r'^מה (?:שואל|מקשה|מתרץ|אומר) (?:ה)?תוס', r'^מה כתב התוס')]
QTYPES = ['קושיא', 'הכרח', 'נפק"מ', 'סברא', 'ממקום אחר', 'צ"ע']
LVLS = ['קל', 'בינוני', 'קשה']


def norm_type(t):
    t = (t or '').strip().replace('״', '"').replace('׳', "'")
    m = {'קושיה': 'קושיא', 'קושיא בלי תירוץ': 'קושיא', 'נפקא מינה': 'נפק"מ', 'נפק״מ': 'נפק"מ', 'נפקא מינא': 'נפק"מ',
         'השלם את הסברא': 'סברא', 'השלמת סברא': 'סברא', 'צריך עיון': 'צ"ע', 'צע': 'צ"ע', 'הכרח': 'הכרח'}
    return m.get(t, t)


def check_line(s, rec, c):
    """רשימת קודי כשל לשורת המסקנה. ריקה = עברה."""
    bad = []
    if not isinstance(s, str) or not s.strip():
        return ['ריקה']
    if DASH.search(s):
        bad.append('קו ארוך')
    if NIK.search(s):
        bad.append('ניקוד')
    if '\n' in s.strip():
        bad.append('כמה שורות')
    w = len(WORDS.findall(s))
    mx = c['line']['maxWords'] + (c['line']['longExtra'] if len(WORDS.findall(rec['text'])) >= 180 else 0)
    if w < c['line']['minWords']:
        bad.append('קצרה מדי (%d)' % w)
    if w > mx:
        bad.append('ארוכה מדי (%d>%d)' % (w, mx))
    for ph in BAN_PHRASES:
        if ph in s:
            bad.append('ביטוי אסור: ' + ph)
    dhw = norm_ctx(rec['dh']).split()
    sw = norm_ctx(s).split()
    if len(dhw) >= 3 and sw[:3] == dhw[:3]:
        bad.append('חוזרת על הד"ה')
    if re.search(r'[A-Za-z]{3,}', s):
        bad.append('אותיות לטיניות')
    return bad


def check_q(q, rec, c):
    bad = []
    if not isinstance(q, dict):
        return ['לא אובייקט']
    qq, aa = str(q.get('q', '')).strip(), str(q.get('a', '')).strip()
    if len(qq) < 12:
        bad.append('שאלה קצרה')
    if not aa:
        bad.append('אין תשובה')
    if len(aa.split()) > c['question']['maxAnswerWords']:
        bad.append('תשובה ארוכה')
    for txt in (qq, aa):
        if DASH.search(txt):
            bad.append('קו ארוך')
            break
    for ph in BAN_PHRASES:
        if ph in qq:
            bad.append('ביטוי אסור: ' + ph)
    for rx in BAN_Q_START:
        if rx.search(qq):
            bad.append('שאלה בנאלית')
    if norm_type(q.get('t')) not in QTYPES:
        bad.append('סוג לא מוכר')
    if q.get('lvl') not in LVLS:
        bad.append('רמה לא תקינה')
    # השאלה אינה מסגירה את התשובה: רוב מילות התשובה כבר בשאלה
    aw = set(norm_ctx(aa).split())
    qw = set(norm_ctx(qq).split())
    if len(aw) >= 4 and len(aw & qw) / float(len(aw)) > 0.8:
        bad.append('מסגירה את התשובה')
    if qq.count('?') > 1:
        bad.append('כמה שאלות')
    return bad


def check_page_variety(recs):
    """כללי הגיוון (תוספת 13.10, ג): אין שתי שאלות רצופות מאותו סוג בעמוד, ואין יותר משתיים הפותחות באותה מילה.
    מחזיר מזהי תוספות שחורגים. הקוד מחזיר לתיקון, אינו מוחק."""
    flat = []
    for r in recs:
        for i, q in enumerate(r.get('q') or []):
            flat.append((r['rid'], i, norm_type(q.get('t')), (str(q.get('q', '')).split() or [''])[0]))
    bad = set()
    for a, b in zip(flat, flat[1:]):
        if a[2] and a[2] == b[2]:
            bad.add((b[0], b[1]))
    first = {}
    for x in flat:
        first.setdefault(x[3], []).append(x)
    for w, xs in first.items():
        if len(xs) > 2:
            for x in xs[2:]:
                bad.add((x[0], x[1]))
    return bad


def cap_questions(qs, rec, c):
    """כללי הכמות (תוספת 13.10, ו): תוספות קצר או הפניה בלבד אינו מקבל שאלה; לכל היותר אחת, ושתיים בתוספות ארוך."""
    n = len(WORDS.findall(rec['text']))
    if n < c['question'].get('minTosWords', 30):
        return []
    return qs[:2 if n >= 180 else 1]


def parse_json(t):
    t = (t or '').strip()
    t = re.sub(r'^```(?:json)?|```$', '', t, flags=re.M).strip()
    try:
        return json.loads(t)
    except Exception:
        i, j = t.find('{'), t.rfind('}')
        if 0 <= i < j:
            return json.loads(t[i:j + 1])
        raise


def resolve_anchor(a, ctxp, idx):
    """הקוד אינו סומך על המודל: הקטע חייב להימצא בדף. כשל ← כלל 3 (סוף שורת הלאוקמי שנבחרה). None אם גם זה נכשל."""
    if not isinstance(a, dict):
        return None
    t = str(a.get('t', '')).strip()
    ln = a.get('line')
    c = norm_ctx(t) if t else ''
    occs = find_occ(idx, c) if c else []
    rule = a.get('rule') if a.get('rule') in (1, 2, 3) else 3
    why = ''
    if not occs:
        try:
            ln = int(ln)
        except Exception:
            return None
        lines = ctxp['lines']
        if not (1 <= ln <= len(lines)):
            return None
        w = norm_ctx(lines[ln - 1]).split(' ')
        occs = []
        for k in (4, 3, 2, 1):
            c = ' '.join(w[-k:])
            occs = find_occ(idx, c)
            if occs:
                break
        if not occs:
            return None
        rule, why = 3, 'הקטע שהוצע לא נמצא בדף; סוף שורת הלאוקמי %d' % ln
    occ = 1
    if len(occs) > 1:
        try:
            lnn = int(ln)
            pre = len(norm_idx(ctxp['lines'][:lnn - 1]))
            occ = min(range(len(occs)), key=lambda i: abs(occs[i] - pre)) + 1
        except Exception:
            occ = 1
    return {'t': c, 'occ': occ, 'rule': rule, 'why': why}


def similarity(a, b):
    """דמיון מילים (ז'קארד על שורשי מילים) בין שתי שורות, לשמירה מפני סחיפה."""
    sa, sb = set(norm_ctx(a).split()), set(norm_ctx(b).split())
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / float(len(sa | sb))
