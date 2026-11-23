# -*- coding: utf-8 -*-
"""פרומפט 87 - כתיבת התיקונים לשכבה (data/edits/<מסכת>.json), על הנוסח החי שנמשך מן הדפדפן.

    python _work/p87/apply.py DD_DIR [--write]
בלי --write: רק מדפיס ומכין _work/p87/out/plan.json.
"""
import os, sys, re, io, json, time, html
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(HERE, 'tools'))
import mishna_gaps as MG, dup_lines as DL

NIK = re.compile('[֑-ׇ]')
dd = sys.argv[1]
WRITE = '--write' in sys.argv
T = [int(time.time() * 1000)]

# ---- השלמות משנה שנבדקו ביד (מסכת, תחילת הטקסט החסר בלי ניקוד) ----
ACCEPT = [
    ('arakhin', 'אבל אינו נדר'), ('bava-batra', 'לשדה חברו, קוצץ'), ('bava-batra', 'במה דברים אמורים, בלח'),
    ('bava-kamma', 'ואם אין לאיש גאל'), ('beitzah', 'אם כן היה לו'), ('bekhorot', 'כמין בהמה חיה ועוף'),
    ('berakhot', 'שנאמר למען תזכר'), ('berakhot', 'על החלב ועל הגבינה'), ('chagigah', 'שהן מקרא מעט'),
    ('chagigah', 'של יין של'), ('keritot', 'כל העריות בנקבה'), ('nazir', 'מה מורה האמורה בשמשון'),
    ('nedarim', 'ואסורין בדבר של אותה העיר'), ('nedarim', 'בזה יפה כח האב'), ('sanhedrin', 'אחד מן הדינים'),
    ('sanhedrin', 'ואדם אחד רוכב'), ('sanhedrin', 'בן איש פלוני'), ('sotah', 'אלון מורה האמור'),
    ('temurah', 'מה שאין בקדשי מזבח'), ('yoma', 'אישי כהן גדול'),
]
TRIM_TAIL = {('nazir', 'מה מורה האמורה בשמשון'): ' אמר רבי'}


def rows_of(slug):
    return json.load(io.open(os.path.join(dd, slug + '.json'), encoding='utf-8'))['rows']


def item(rows, ek):
    uid = ek.split('.')[0]
    for ri, r in enumerate(rows):
        if r['id'] == uid:
            for it in r['items']:
                if it['ek'] == ek:
                    return ri, r, it
    return None, None, None


def ctx_of(rows, ek):
    """כמו ctxOf בדף: השורה שלפני ושאחרי בסדר הדף (כותרות צד, שורות, ד"ה, נושא)."""
    seq = []
    for r in rows:
        if r.get('k') in ('dh', 'nose'):
            seq += [it for it in r['items']]
        elif r.get('k') in ('u', 'm'):
            seq += [it for it in r['items'] if (not it.get('anchor')) or MG.was_of(it['h']).strip()]
    for i, it in enumerate(seq):
        if it['ek'] == ek:
            b = MG.was_of(seq[i - 1]['h'])[-40:] if i > 0 else ''
            a = MG.was_of(seq[i + 1]['h'])[:40] if i + 1 < len(seq) else ''
            return {'b': b, 'a': a}
    return {'b': '', 'a': ''}


def rec(slug, rows, ek, wasH, nowH, daf, why, kind, extra=None):
    T[0] += 1
    e = {'k': '%s~%d' % (ek, T[0]), 't': T[0], 'was': MG.was_of(wasH), 'now': MG.was_of(nowH), 'wasH': wasH, 'nowH': nowH,
         'daf': daf, 'wasP': '', 'ctx': ctx_of(rows, ek), 'p87': {'kind': kind, 'why': why}}
    if extra:
        e['p87'].update(extra)
    return e


plan = defaultdict(list)       # slug -> [edit]
touched = defaultdict(set)     # slug -> eks
report = defaultdict(lambda: {'mishna': [], 'dups': [], 'near': [], 'skip': []})
slugs = sorted(f[:-5] for f in os.listdir(dd) if f.endswith('.json'))

# ---------------------------------------------------------------- א. השלמות משנה (אוטומטי שנבדק)
for slug in slugs:
    rows = rows_of(slug)
    for x in MG.report(slug, rows):
        if x.get('decision') not in ('fix', 'move'):
            continue
        plainT = NIK.sub('', x['text'])
        acc = [a for a in ACCEPT if a[0] == slug and plainT.startswith(a[1])]
        if not acc:
            report[slug]['skip'].append({'daf': x['daf'], 'text': x['text'], 'why': 'נבדק ביד: אינו חוסר (ראשי תיבות, צמצום, או מקום לא ודאי)'})
            continue
        ri, r, it = item(rows, x['ek'])
        if it is None or it['h'] != x['wasH'] or x['ek'] in touched[slug]:
            report[slug]['skip'].append({'daf': x['daf'], 'text': x['text'], 'why': 'השורה השתנתה'})
            continue
        nowH = x['nowH']
        tt = TRIM_TAIL.get(acc[0])
        if tt:
            # זנב חלקי ("אמר רבי") שאינו שייך להשלמה - נחתך
            m = re.search(r',?\s*אָ?מַ?ר\s+רַ?בִּ?י\s*[.,]?\s*$', nowH.rstrip())
            m = m or re.search(r',?\s*אמר\s+רבי\s*[.,]?\s*$', NIK.sub('', nowH).rstrip()) and re.search(r'\s+\S+\s+\S+\s*$', nowH.rstrip())
            if m:
                nowH = nowH.rstrip()[:m.start()].rstrip(' ,.') + '.'
        plan[slug].append(rec(slug, rows, x['ek'], x['wasH'], nowH, r['daf'], 'השלמת משנה מן המקור הקנוני', 'mishna',
                              {'perek': x['perek'], 'mishna': x['mishna'], 'added': x['text']}))
        touched[slug].add(x['ek'])
        report[slug]['mishna'].append({'daf': r['daf'], 'perek': x['perek'], 'mishna': x['mishna'], 'added': x['text']})

# ---------------------------------------------------------------- ב. השלמות ביד
HAND = []


def hand(slug, ek, fn, why, kind='mishna', meta=None):
    rows = rows_of(slug)
    ri, r, it = item(rows, ek)
    if it is None:
        report[slug]['skip'].append({'ek': ek, 'why': 'השורה לא נמצאה'}); return None
    nowH = fn(it['h'])
    if nowH is None or nowH == it['h']:
        report[slug]['skip'].append({'ek': ek, 'why': 'הנוסח השתנה (כבר תוקן?)'}); return None
    if ek in touched[slug]:
        return None
    e = rec(slug, rows, ek, it['h'], nowH, r['daf'], why, kind, meta)
    plan[slug].append(e)
    touched[slug].add(ek)
    if kind == 'mishna':
        report[slug]['mishna'].append(dict(meta or {}, daf=r['daf']))
    return e


def prep(add):
    return lambda h: None if NIK.sub('', MG.was_of(add)).strip(' ,') in NIK.sub('', MG.was_of(h)) else add + ' ' + h


def app(add):
    return lambda h: None if NIK.sub('', MG.was_of(add)).strip(' ,.') in NIK.sub('', MG.was_of(h)) else h.rstrip() + ' ' + add


# שבת נא: - "יוצא הגמל באפסר ונאקה בחטם" לפני "לובדקים"
hand('shabbat', 'u3414.2', prep('<i class="ns">יוֹצֵא הַגָּמָל בְּאַפְסָר, וְנָאקָה בַחֲטָם,</i>'),
     'השלמת משנה מן המקור הקנוני', meta={'perek': 5, 'mishna': [1], 'added': 'יוֹצֵא הַגָּמָל בְּאַפְסָר, וְנָאקָה בַחֲטָם'})
# שבת נב. - "ליבש אבל לא לחלב" בסוף דברי רבי יהודה
hand('shabbat', 'u3476.2', lambda h: None if 'לחלב' in NIK.sub('', h) else h.rstrip() + ' לְיַבֵּשׁ, אֲבָל לֹא לְחָלָב.',
     'השלמת משנה מן המקור הקנוני', meta={'perek': 5, 'mishna': [2], 'added': 'לְיַבֵּשׁ, אֲבָל לֹא לְחָלָב'})
# כתובות יא. - "שלש שנים ויום אחד"
hand('ketubot', 'u494.1', lambda h: None if 'ויום אחד' in h else re.sub(r'(שלש)((?:</i>)?\s*-)', r'\1 שנים ויום אחד\2', h, 1),
     'השלמת משנה מן המקור הקנוני', meta={'perek': 1, 'mishna': [2], 'added': 'שָׁנִים וְיוֹם אֶחָד'})
# זבחים עה: - "ירעו עד שיסתאבו"
hand('zevachim', 'u4107.1', lambda h: None if 'שיסתאבו' in h else re.sub(r'\s*-?\s*$', '', h.rstrip()) + ' - ירעו עד שיסתאבו.',
     'השלמת משנה מן המקור הקנוני', meta={'perek': 8, 'mishna': [2], 'added': 'יִרְעוּ עַד שֶׁיִּסְתָּאֲבוּ'})


# בכורות מח. - שורות משנה שנפלו מן התיבה לשורת גמרא בין שני חלקיה: חוזרות לתיבה, והשורה שבחוץ נמחקת
def move(slug, src_eks, dst, mode, meta):
    rows = rows_of(slug)
    parts = []
    for s in src_eks:
        ri, r, it = item(rows, s)
        if it is None:
            report[slug]['skip'].append({'ek': s, 'why': 'השורה לא נמצאה'}); return
        parts.append(it['h'].strip())
    add = ' '.join(parts)
    fn = (lambda h: h.rstrip() + ' ' + add) if mode == 'after' else (lambda h: add + ' ' + h)
    e = hand(slug, dst, fn, 'שורת משנה שנפלה מן התיבה חזרה אליה', meta=meta)
    if not e:
        return
    for s in src_eks:
        ri, r, it = item(rows, s)
        plan[slug].append(rec(slug, rows, s, it['h'], '', r['daf'], 'השורה הוחזרה לתיבת המשנה (%s)' % dst, 'moved'))
        touched[slug].add(s)


move('bekhorot', ['u3550.1'], 'u3551.1', 'before', {'perek': 8, 'mishna': [3], 'added': 'מת האב והבנים קיימים (הוחזר לתיבה)'})
move('bekhorot', ['u3602.1'], 'u3597.5', 'after', {'perek': 8, 'mishna': [4], 'added': 'שתי נקבות וזכר... אין כאן לכהן כלום (הוחזר לתיבה)'})
move('bekhorot', ['u3609.1', 'u3609.2'], 'u3611.1', 'before', {'perek': 8, 'mishna': [5], 'added': 'שתי נשים של שני אנשים... (הוחזר לתיבה)'})

# ---------------------------------------------------------------- ג. שורות כפולות
ANT = [('אסור', 'מותר'), ('חייב', 'פטור'), ('למעלה', 'למטה'), ('בן', 'בת'), ('יש', 'אין'), ('טמא', 'טהור'),
       ('כשר', 'פסול'), ('לא', ''), ('אין', ''), ('ואין', 'ויש'), ('ראשון', 'שני'), ('יפה', 'רע')]


def contrast(a, b):
    wa, wb = a.split(), b.split()
    import difflib
    sm = difflib.SequenceMatcher(None, wa, wb, autojunk=False)
    diff = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag != 'equal':
            diff.append((' '.join(wa[i1:i2]), ' '.join(wb[j1:j2])))
    for x, y in diff:
        xs, ys = set(x.split()), set(y.split())
        for p, q in ANT:
            if (any(p in w for w in xs) and (not q or any(q in w for w in ys))) or (any(p in w for w in ys) and (not q or any(q in w for w in xs))):
                return True
        if re.search(r'\d|[א-ת]"[א-ת]', x + y):
            return True
    return False


for slug in slugs:
    rows = rows_of(slug)
    for x in DL.scan(rows):
        if x['kind'] in ('same', 'part'):
            d, k = x['drop'], x['keep']
            if d['ek'] in touched[slug] or k['ek'] in touched[slug]:
                continue
            why = 'שורה כפולה' if x['kind'] == 'same' else 'שארית פיצול (כלולה בשורה הסמוכה)'
            plan[slug].append(rec(slug, rows, d['ek'], d['h'], '', d['daf'], why, 'dup', {'keep': k['ek']}))
            touched[slug].add(d['ek'])
            if x.get('drop_anchor') and d.get('anchor_ek'):
                ri, r, it = item(rows, d['anchor_ek'])
                if it is not None and d['anchor_ek'] not in touched[slug]:
                    plan[slug].append(rec(slug, rows, d['anchor_ek'], it['h'], '', d['daf'],
                                          'כותרת צד שנשארה יתומה אחרי מחיקת שורה כפולה', 'dup', {'keep': k['ek']}))
                    touched[slug].add(d['anchor_ek'])
            report[slug]['dups'].append({'daf': d['daf'], 'kind': x['kind'], 'text': d['t'].strip(), 'anchor': bool(x.get('drop_anchor'))})
        elif x['kind'] == 'near':
            a, b = x['a'], x['b']
            s = DL._sim(a['nt'], b['nt'])
            if not (s >= 0.95 or 'כותרת' in x['why']) or contrast(a['nt'], b['nt']):
                continue
            report[slug]['near'].append({'daf': a['daf'], 'why': x['why'], 'a': [a['ek'], a['t'].strip()], 'b': [b['ek'], b['t'].strip()],
                                         'ctx': ctx_of(rows, b['ek']), 'bh': b['h'], 'uid': b['ek'].split('.')[0][1:]})

tot = Counter()
for slug in slugs:
    R = report[slug]
    tot['mishna'] += len(R['mishna']); tot['dups'] += len(R['dups']); tot['near'] += len(R['near']); tot['edits'] += len(plan[slug])
    if plan[slug] or R['near']:
        print('%-14s משנה %2d  כפולות %3d  לעיון %2d  עריכות %3d' % (slug, len(R['mishna']), len(R['dups']), len(R['near']), len(plan[slug])))
print(dict(tot))
io.open(os.path.join(HERE, '_work', 'p87', 'out', 'plan.json'), 'w', encoding='utf-8').write(
    json.dumps({'plan': plan, 'report': report}, ensure_ascii=False, indent=1))

if WRITE:
    import cloud_word as C
    for slug, eds in plan.items():
        if not eds:
            continue
        p = os.path.join(HERE, 'data', 'edits', slug + '.json')
        doc = json.load(io.open(p, encoding='utf-8')) if os.path.exists(p) else {'v': 1, 'slug': slug, 'masechet': C.masechet_of_slug(slug), 'edits': []}
        doc['edits'] = (doc.get('edits') or []) + eds
        io.open(p, 'w', encoding='utf-8', newline='\n').write(json.dumps(doc, ensure_ascii=False, indent=1))
    print('נכתב לשכבה')
