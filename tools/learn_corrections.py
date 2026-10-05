# -*- coding: utf-8 -*-
"""learn_corrections.py - לומד התיקונים: למידה שקטה מכל תיקון שהמנהל מפרסם.

העיקרון: כל תיקון של המנהל הוא הוראה ללמוד. אין בקשת אישור ואין שאלה אחרי
תיקון. הלומד רץ באצווה ברקע; בלי תיקונים חדשים אינו עושה דבר ואינו עולה דבר.

מקורות (היומן): עריכה באתר ותיקון שאושר מתור ההצעות (נרשמים בצד השרת בנקודת
המיזוג, ראה worker/leokmei-suggest jrFromEdit), הצעה שנדחתה (דוגמה שלילית),
ותיקוני וורד בעקוב אחר שינויים של המחבר (--word, בריצת הלילה).

היומן פרטי: ‏Documents\\לאוקמי-יומן-תיקונים (מקומי), לא בריפו הציבורי ולא בדרייב.
הכללים והמסמך "כללים-שנלמדו.md" נשמרים ב-_שומר שבדרייב; הם כוללים כל אחד רק דוגמה
אחת לפני-אחרי.

קצב: פעם ביום בלילה (שעה 03), או מוקדם יותר כשמצטברים 30 תיקונים חדשים, המוקדם
מביניהם. בלי תיקונים חדשים - לא רץ דבר.

מיון כל תיקון לשכבה:
  mech  מכני      - רווחים, סימנים, גרשיים, כוכביות, החלפת מילה בודדת שחוזרת.
                    יעד: laukmi_rules (RAWS_LEARNED) ומשם המנוע המכני. בלי מודל בזמן ריצה.
  sem   סמנטי     - החלפה קצרה שדורשת הבנה (מילת הסבר, סגנון פסוק או אמורא).
                    יעד: מועמדים לפרומפט השכבה הסמנטית. מודל קל, רק בהרצת השכבה.
  deep  עמוק      - שכתוב משפט. יעד: מועמדים לפרומפט ההידוק. מודל חזק, רק על טווח
                    שהמנהל מבקש.
  once  חד-פעמי  - תיקון תוכן נקודתי. נרשם ואינו הופך לכלל.

מתיקון לכלל (ההגנות):
  א. כלל נוצר כשאותו דפוס חוזר פעמיים לפחות, או כשהוא חד וחסר ספק (סימן/רווח/כוכביות).
  ב. כל כלל נבדק מול כל היומן לפני הכנסה: חייב לשחזר את תיקוני המנהל שממנו נולד,
     ולא לשנות אף נוסח שהמנהל כבר אישר, ולא לייצר הצעה שנדחתה.
  ג. כלל שמנהל תיקן נגדו מאוחר יותר - התיקון המאוחר גובר והכלל מבוטל.
  ד. הכללים בגרסאות (rules/vNNN.json) עם חזרה לאחור: --rollback N.
  ה. הכללים חלים רק על ריצות עתידיות של המנועים. הלומד אינו נוגע בשום קובץ וורד.

עלות: הלומד אינו קורא למודל. תקרת עלות יומית למודל = MODEL_CAP_USD (ברירת מחדל 0;
העלאתה מותרת רק בהחלטת בעל הפרויקט).

    uv run python tools/learn_corrections.py            # ריצה רגילה (נבדקים התנאים)
    uv run python tools/learn_corrections.py --force    # בלי תנאי הקצב
    uv run python tools/learn_corrections.py --word     # גם תיקוני וורד
    uv run python tools/learn_corrections.py --rebuild --force  # בונה את הכללים מחדש מכל היומן
    uv run python tools/learn_corrections.py --rollback 3
"""
import os, sys, re, io, json, time, hashlib, difflib, datetime, urllib.request, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, 'engine', 'laukmi-engine'))

API = 'https://leokmei-suggest.m7654301.workers.dev'
KEYFILE = r'C:\Users\Owner\Documents\לאוקמי-מפתח-מנהל.txt'
PRIV = r'C:\Users\Owner\Documents\לאוקמי-יומן-תיקונים'
DRIVE = r'C:\Users\Owner\Desktop\שיננא לHTML'
OUT = os.path.join(DRIVE, '_שומר', 'למידה')
MD = os.path.join(DRIVE, '_שומר', 'כללים-שנלמדו.md')
BATCH_MAX = 30
NIGHT_HOUR = 3
MODEL_CAP_USD = 0.0
KNOWN = set('berakhot shabbat eruvin pesachim shekalim yoma sukkah beitzah rosh-hashanah taanit megillah moed-katan '
            'chagigah yevamot ketubot nedarim nazir sotah gittin kiddushin bava-kamma bava-metzia bava-batra sanhedrin '
            'makkot shevuot avodah-zarah horayot zevachim menachot chullin bekhorot arakhin temurah keritot meilah tamid niddah'.split())
ENGINE_AUTHORS = ('Claude', 'מנוע', 'הצעה מהאתר', 'עריכה באתר')

HEB = re.compile(r'^[א-ת]{2,14}$')    # מילה עברית טהורה: בלי גרשיים, מקף או סימן
NOISE = re.compile(r'[\s.,:;!?\'"״׳\-–—*()\[\]]')
STRIP_HTML = re.compile(r'<[^>]+>')


def admin_key():
    t = io.open(KEYFILE, encoding='utf-8').read()
    m = re.findall(r'[A-Za-z0-9_\-]{30,}', t)
    if not m:
        raise SystemExit('עצירה: אין מפתח מנהל בקובץ המפתח')
    return m[0]


def call(path, body=None):
    hd = {'x-admin-key': admin_key(), 'content-type': 'application/json; charset=utf-8', 'User-Agent': 'Mozilla/5.0'}
    req = urllib.request.Request(API + path, data=json.dumps(body).encode('utf-8') if body is not None else None,
                                 headers=hd, method='POST' if body is not None else 'GET')
    return json.loads(urllib.request.urlopen(req, timeout=60).read())


def plain(h):
    import html
    return html.unescape(STRIP_HTML.sub('', h or ''))


# ------------------------------------------------------------ יומן
def load_journal():
    os.makedirs(PRIV, exist_ok=True)
    p = os.path.join(PRIV, 'journal.jsonl')
    by = {}
    if os.path.exists(p):
        for line in io.open(p, encoding='utf-8'):
            if line.strip():
                e = json.loads(line)
                by[e['id']] = e
    return by, p


def save_journal(by, p):
    tmp = p + '.tmp'
    with io.open(tmp, 'w', encoding='utf-8') as f:
        for e in sorted(by.values(), key=lambda x: x['t']):
            f.write(json.dumps(e, ensure_ascii=False) + '\n')
    os.replace(tmp, p)


def pull(by):
    n = 0
    for e in call('/journal').get('items', []):
        if e['slug'] not in KNOWN:
            continue                      # רשומות בדיקה של ממשק ההצעות אינן חומר למידה
        if e['id'] not in by:
            by[e['id']] = e
            n += 1
    return n


def pull_word(by):
    """תיקוני וורד בעקוב אחר שינויים של המחבר (לא של המנועים)."""
    import glob
    from laukmi_learn import extract
    n = 0
    for f in sorted(glob.glob(os.path.join(DRIVE, '*.docx'))):
        if os.path.basename(f).startswith('~$'):
            continue
        try:
            ed = extract(f)
        except Exception:
            continue
        slug = os.path.basename(f)
        for old, new, style, author in ed:
            if not author or author.startswith(ENGINE_AUTHORS) or (not old and not new):
                continue
            i = 'wd-' + hashlib.sha1(('%s|%s|%s|%s' % (slug, old, new, style)).encode('utf-8')).hexdigest()[:16]
            if i not in by:
                by[i] = {'id': i, 't': int(time.time() * 1000), 'slug': 'word', 'daf': '', 'k': '', 'src': 'word',
                         'kind': 'text', 'was': old, 'now': new, 'wasP': style, 'ps': style, 'ctx': None,
                         'neg': 0, 'why': '', 'file': slug}
                n += 1
    return n


# ------------------------------------------------------------ מיון
def word_tokens(t):
    return t.split()


def fragments(was, now):
    """זוגות (ישן, חדש) ברמת מילה, מתוך ההבדלים בין שני הנוסחים."""
    a, b = word_tokens(was), word_tokens(now)
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    out = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag != 'equal':
            out.append((' '.join(a[i1:i2]), ' '.join(b[j1:j2]), tag, (i1, i2)))
    return out, sm.ratio()


def classify(e):
    """שכבה לתיקון אחד: (שכבה, זוגות מכניים)."""
    if e.get('kind') in ('split', 'merge', 'side', 'unside'):
        return 'once', []                                  # שינוי מבנה: נרשם, אינו כלל
    was, now = plain(e.get('was')), plain(e.get('now'))
    if was == now:
        # שינוי סגנון בלבד: סמנטי (דורש הבנת התפקיד)
        if (e.get('wasH') or '') != (e.get('nowH') or '') or e.get('wasP') != e.get('ps'):
            return 'sem', []
        return 'once', []
    frs, ratio = fragments(was, now)
    if not frs:
        return 'once', []
    if len(was) > 60 and ratio < 0.6:
        return 'deep', []
    mech = []
    for a, b, tag, pos in frs:
        if NOISE.sub('', a) == NOISE.sub('', b) or (not NOISE.sub('', a) and not NOISE.sub('', b)):
            mech.append((a, b, 'sharp'))                   # סימנים, רווחים, גרשיים, כוכביות
        elif a and b and len(a.split()) == 1 and len(b.split()) == 1 and HEB.match(a) and HEB.match(b):
            mech.append((a, b, 'word'))
    if mech and len(mech) == len(frs):
        return 'mech', mech
    if all(len(a.split()) <= 3 and len(b.split()) <= 4 for a, b, _, _ in frs):
        hs = '<i class="hs">' in (e.get('nowH') or '')
        return 'sem', [(a, b, 'sem') for a, b, _, _ in frs if (a or b)] if not hs else []
    return 'once', []


# ------------------------------------------------------------ כללים
def wb(s):
    return r'(?<![א-ת"\'])' + re.escape(s) + r'(?![א-ת"\'])'


def apply_rule(rule, text):
    a, b = rule['find'], rule['repl']
    if not a or rule['kind'] == 'ctx':
        return text
    return re.sub(wb(a) if rule['kind'] == 'word' else re.escape(a), b.replace('\\', '\\\\'), text)


def build_rules(journal, off):
    entries = sorted(journal.values(), key=lambda x: x['t'])
    cls = {e['id']: classify(e) for e in entries}
    support = collections.defaultdict(list)
    for e in entries:
        layer, pairs = cls[e['id']]
        if layer != 'mech' or e.get('neg'):
            continue
        for a, b, kind in pairs:
            support[(a, b, kind)].append(e)
    approved = [plain(e.get('now')) for e in entries if not e.get('neg') and e.get('now')]
    rejected = [(plain(e.get('was')), plain(e.get('now'))) for e in entries if e.get('neg')]
    repls = collections.defaultdict(set)
    for (a, b, kind) in support:
        if kind == 'word':
            repls[a].add(b)
    rules, held = [], []
    for (a, b, kind), sup in support.items():
        if kind == 'word' and len(repls[a]) > 1:
            held.append((a, b, 'כמה תרגומים שונים - תלוי הקשר, לא כלל מכני'))
            continue
        ids = sorted({e['id'] for e in sup})
        sharp = kind == 'sharp'
        if len(ids) < 2 and not sharp:
            held.append((a, b, 'ממתין לחזרה נוספת'))
            continue
        if not a:
            held.append((a, b, 'הוספה בלי ישן: אינה כלל מכני'))
            continue
        rid = 'r-' + hashlib.sha1(('%s>%s' % (a, b)).encode('utf-8')).hexdigest()[:8]
        rule = {'id': rid, 'find': a, 'repl': b, 'kind': 'word' if kind == 'word' else 'raw',
                'support': len(ids), 'src': ids[:5], 'last': max(e['t'] for e in sup),
                'example': {'was': plain(sup[-1].get('was'))[:160], 'now': plain(sup[-1].get('now'))[:160],
                            'where': (sup[-1].get('slug') or '') + ' ' + (sup[-1].get('daf') or '')},
                'status': 'on'}
        # כוכביות ותו בודד אינם כלל גלובלי: הם תלויי מקום (חציצה, כותרת). נרשמים ואינם נטענים במנוע.
        if kind == 'sharp':
            rule['kind'] = 'ctx'      # סימנים, רווחים וכוכביות תלויי מקום: נרשמים בלבד, אינם נטענים במנוע
        if rid in off:
            rule['status'] = 'off'
            rule['why'] = 'בוטל בידי המנהל'
        # ג: תיקון מאוחר שמתנגד
        rev = [e for e in entries if e['t'] > rule['last'] and not e.get('neg')
               and any(x == b and y == a for x, y, *_ in fragments(plain(e.get('was')), plain(e.get('now')))[0])]
        if rev:
            rule['status'] = 'off'
            rule['why'] = 'המנהל תיקן נגדו מאוחר יותר'
        if rule['kind'] == 'ctx':
            rule['why'] = rule.get('why') or 'תלוי מקום: נרשם בלבד, אינו נטען במנוע'
            rules.append(rule)
            continue
        # ב: מחזיר את התיקונים? לא משנה נוסח מאושר? לא מייצר הצעה שנדחתה?
        if rule['status'] == 'on':
            for e in sup:
                w, n = plain(e.get('was')), plain(e.get('now'))
                if len(fragments(apply_rule(rule, w), n)[0]) >= len(fragments(w, n)[0]):
                    rule['status'] = 'off'
                    rule['why'] = 'אינו משחזר את התיקון שממנו נולד'
                    break
        if rule['status'] == 'on':
            for t in approved:
                if apply_rule(rule, t) != t:
                    rule['status'] = 'off'
                    rule['why'] = 'היה משנה נוסח שהמנהל כבר אישר'
                    break
        if rule['status'] == 'on':
            for w, n in rejected:
                if apply_rule(rule, w) == n and w != n:
                    rule['status'] = 'off'
                    rule['why'] = 'היה מייצר הצעה שנדחתה'
                    break
        rules.append(rule)
    return rules, held, cls


# ------------------------------------------------------------ פלט
def write_outputs(rules, held, cls, journal, new_ids, ver):
    os.makedirs(os.path.join(OUT, 'rules'), exist_ok=True)
    cur = os.path.join(OUT, 'current.json')
    prev = json.load(io.open(cur, encoding='utf-8')) if os.path.exists(cur) else {'version': 0, 'rules': []}
    key = lambda rs: sorted((r['id'], r['status']) for r in rs)
    changed = key(rules) != key(prev['rules'])
    if changed:
        ver = prev['version'] + 1
        doc = {'version': ver, 'when': datetime.datetime.now().isoformat(timespec='seconds'), 'rules': rules}
        io.open(os.path.join(OUT, 'rules', 'v%03d.json' % ver), 'w', encoding='utf-8').write(
            json.dumps(doc, ensure_ascii=False, indent=1))
        io.open(cur, 'w', encoding='utf-8').write(json.dumps(doc, ensure_ascii=False, indent=1))
    else:
        ver = prev['version']
    ctx = [r for r in rules if r['kind'] == 'ctx']
    on = [r for r in rules if r['status'] == 'on' and r['kind'] != 'ctx']
    L = ['# כללים שנלמדו', '',
         'מתעדכן אוטומטית בידי tools/learn_corrections.py. גרסה %d. לכל כלל דוגמה אחת לפני-אחרי ומקום המקור.' % ver, '',
         '| כלל | חזר | דוגמה (לפני ← אחרי) | מקור |', '|---|---|---|---|']
    for r in sorted(on, key=lambda x: -x['support']):
        L.append('| `%s` ← `%s` | %d | %s ← %s | %s |' % (r['find'], r['repl'], r['support'],
                                                           r['example']['was'][:70].replace('|', '/'),
                                                           r['example']['now'][:70].replace('|', '/'), r['example']['where']))
    off = [r for r in rules if r['status'] == 'off']
    if ctx:
        L += ['', '## תיקוני סימנים ורווחים (תלויי מקום, נרשמו ואינם נטענים במנוע)', '', 'נרשמו %d תיקונים כאלה ביומן.' % len(ctx)]
    if off:
        L += ['', '## כללים שלא נכנסו או בוטלו', '']
        for r in off:
            L.append('- `%s` ← `%s`: %s' % (r['find'], r['repl'], r.get('why', '')))
    io.open(MD, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    sem = [(a, b) for e in journal.values() if cls[e['id']][0] == 'sem' for a, b, _ in cls[e['id']][1]]
    sc = collections.Counter(sem)
    io.open(os.path.join(OUT, 'מועמדים-לפרומפט-סמנטי.md'), 'w', encoding='utf-8').write(
        '# מועמדי שיפור לשכבה הסמנטית (מודל קל)\n\nמצטבר מן היומן. נכנס לפרומפט רק בהרצת השכבה, ואחרי בדיקה מול היומן.\n\n' +
        '\n'.join('- %dx `%s` ← `%s`' % (c, a, b) for (a, b), c in sc.most_common(80)) + '\n')
    deep = [e for e in journal.values() if cls[e['id']][0] == 'deep']
    io.open(os.path.join(OUT, 'מועמדים-לפרומפט-הידוק.md'), 'w', encoding='utf-8').write(
        '# מועמדי שיפור למנוע ההידוק (מודל חזק, רק על טווח שהמנהל מבקש)\n\n' +
        '\n'.join('- %s %s\n  - לפני: %s\n  - אחרי: %s' % (e.get('slug'), e.get('daf'), plain(e.get('was'))[:160], plain(e.get('now'))[:160])
                  for e in deep[-40:]) + '\n')
    return ver, changed, on, off


def summary(cls, new_ids, rules, held, ver, changed):
    cnt = collections.Counter(cls[i][0] for i in new_ids if i in cls)
    on = [r for r in rules if r['status'] == 'on' and r['kind'] != 'ctx']
    return {'when': datetime.datetime.now().isoformat(timespec='seconds'), 'ver': ver, 'new': len(new_ids),
            'mech': cnt['mech'], 'sem': cnt['sem'], 'deep': cnt['deep'], 'once': cnt['once'],
            'pending': len(held), 'rules': [{'id': r['id'], 'find': r['find'], 'repl': r['repl'], 'n': r['support'],
                                               'ex': r['example']['was'][:90] + ' ← ' + r['example']['now'][:90]} for r in on][:40],
            'held': [{'find': a, 'repl': b, 'why': w} for a, b, w in held][:20]}


def main():
    force = '--force' in sys.argv
    if '--rollback' in sys.argv:
        n = int(sys.argv[sys.argv.index('--rollback') + 1])
        src = os.path.join(OUT, 'rules', 'v%03d.json' % n)
        if not os.path.exists(src):
            raise SystemExit('אין גרסה %d' % n)
        io.open(os.path.join(OUT, 'current.json'), 'w', encoding='utf-8').write(io.open(src, encoding='utf-8').read())
        print('הכללים הוחזרו לגרסה', n)
        return
    by, p = load_journal()
    state_p = os.path.join(PRIV, 'state.json')
    state = json.load(io.open(state_p, encoding='utf-8')) if os.path.exists(state_p) else {'done': []}
    got = pull(by)
    night = datetime.datetime.now().hour == NIGHT_HOUR
    if '--word' in sys.argv or night:
        got += pull_word(by)
    save_journal(by, p)
    new = [i for i in by if i not in set(state['done'])] if '--rebuild' not in sys.argv else list(by)
    if not new:
        return                                           # אין תיקונים חדשים: לא רץ דבר, אין עלות
    if len(new) < BATCH_MAX and not night and not force:
        return                                           # ממתינים ללילה או ל-30 תיקונים
    try:
        off = set((call('/learn').get('off') or []))
    except Exception:
        off = set()
    rules, held, cls = build_rules(by, off)
    cur_p = os.path.join(OUT, 'current.json')
    prev_ids = {r['id'] for r in json.load(io.open(cur_p, encoding='utf-8'))['rules'] if r['status'] == 'on' and r['kind'] != 'ctx'} if os.path.exists(cur_p) else set()
    ver, changed, on, offr = write_outputs(rules, held, cls, by, new, 0)
    state['done'] = sorted(set(state['done']) | set(new))
    state['last'] = datetime.datetime.now().isoformat(timespec='seconds')
    io.open(state_p, 'w', encoding='utf-8').write(json.dumps(state))
    sm = summary(cls, new, rules, held, ver, changed)
    sm['newRules'] = len([r for r in rules if r['status'] == 'on' and r['kind'] != 'ctx' and r['id'] not in prev_ids])
    try:
        call('/learn', sm)
    except Exception as e:
        print('הסיכום לא נשלח לדף הניהול:', e)
    print('למידה: %d תיקונים חדשים; מכני %d, סמנטי %d, עמוק %d, חד-פעמי %d; כללים פעילים %d; גרסה %d' %
          (len(new), sm['mech'], sm['sem'], sm['deep'], sm['once'], len(on), ver))


if __name__ == '__main__':
    main()
