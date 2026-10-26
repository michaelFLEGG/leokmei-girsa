# -*- coding: utf-8 -*-
"""convert.py - פרומפט 8 (26.10.2026): כל ממצא ממתין מקבל מטען כתוב, והטכני מסומן להחלה לבד.

שער התור בדף (bkReady) אינו מכניס לתור של המחבר ממצא בלי פעולה מוכנה. הכלי הזה ממלא את החסר:

  א. המרה בקוד של מה שכבר כתוב בשדה fix כפרוזה ("הוסף אחרי 'X': Y", "להוסיף כותרת: X", ...).
  ב. ניקוד פסוק מן המקרא המנוקד שבמאגר (data/tanakh-nikud.json, רק כשהרצף נמצא בפסוק אחד וניקודו ודאי).
  ג. סימון "auto" לסוגים הטכניים, רק כשההכרעה דטרמיניסטית ומאומתת בקוד:
       amor_miss  שם בסגנון אמוראים (הגלאי כבר מאמת את השם; ראשי תיבות דו-משמעיים - לא)
       psuk_nik   ניקוד מן המקרא (רצף ייחודי)
       psuk_miss  פסוק שלא סומן (הגלאי מצא את הפסוק במקרא)
       psuk_bad   סגנון פסוק על מה שאינו פסוק - רק כשגם התאמה מקלה (בלי קידומת, כתיב מלא/חסר) אינה מוצאת במקרא
       punct      פיסוק כפול / רווח לפני פסיק
       joined     מילים דבוקות - רק כשהמילה הדבוקה אינה במילון המסכתות ושני חלקיה בו
       aram       ארמית שנשארה - רק זוג (ארמית ⟵ עברית) שהמחבר כבר קיבל ולא דחה מעולם
     הדף מחיל את אלה לבד, רושם ב"תוקן אוטומטית" עם "בטל", ואינו מציג להם כרטיס.
  ד. מה שאינו ניתן בקוד נכתב ל-model-todo.json, למודל קטן שמחזיר op בלבד (merge).

    uv run python tools/bakara/convert.py --plan [--slug bekhorot]      תוכנית בלבד (לא נוגע בשרת)
    uv run python tools/bakara/convert.py --merge answers.json           תשובות המודל, מאומתות בקוד
    uv run python tools/bakara/convert.py --push                         גיבוי, ואז העלאת הפרקים שהשתנו
"""
import os, re, sys, json, argparse, collections, io, time, html

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, 'tools'))
OUT = os.path.join(ROOT, '_work', 'convert')
PLAN = os.path.join(OUT, 'convert-plan.json')
TODO = os.path.join(OUT, 'model-todo.json')
BACKUP = os.path.join(os.path.expanduser('~'), 'Downloads', 'לאוקמי-גירסא', 'גיבוי-בקרה')

import ops as OPS

HEB = re.compile(r'[א-ת][א-ת֑-ׇ]*')
NIK = re.compile(r'[֑-ׇ]')
Q = "['״“”\"׳‘’]"
AMB_NAMES = {'ר"ה', 'ר"ח', 'ר"ל', 'ר"ת'}      # ראש השנה / ראש חודש / רוצה לומר: לא לבד
EXEC = ('rep', 'ins', 'style', 'del', 'anchor', 'heading', 'nikud', 'split', 'join')


def strip_q(t):
    t = (t or '').strip()
    t = re.sub(r'^' + Q + r'+|' + Q + r'+$', '', t).strip()
    return t


def compact(t):
    return re.sub(r'[֑-ׇ\s​-‏‪-‮◄]', '', t or '')


# ------------------------------------------------------------ א. פרוזה למטען
def prose_op(f):
    fx = (f.get('fix') or '').strip()
    if not fx:
        return None
    mk = (f.get('mark') or '').strip()
    m = re.match(r'^(?:בשורה \d+ )?(?:להוסיף|הוסף|הוספה) (אחרי|לפני) ' + Q + r'(.+?)' + Q + r'\s*(?:להוסיף|הוסף)?\s*:\s*(.+)$', fx)
    if m:
        t = strip_q(m.group(3))
        if t and not re.search(r'(בסגנון|את הפירוש|פסקאות|בשורה או|ודחייתו)', t):
            return {'ins': {('after' if m.group(1) == 'אחרי' else 'before'): m.group(2), 'text': OPS._strip_text(t), 'cs': 'hs'}}
    m = re.match(r'^(?:להוסיף|הוסף) אחרי המשפט\s*:\s*(.+)$', fx)
    if m:
        return {'ins': {'after': mk, 'text': OPS._strip_text(m.group(1)), 'cs': 'hs'}}
    m = re.match(r'^(?:להוסיף|הוסף|הוספה|להשלים) בסוף הפסקה\s*:\s*(.+)$', fx)
    if m:
        return {'ins': {'end': True, 'text': OPS._strip_text(m.group(1)), 'cs': 'hs'}}
    m = re.match(r'^(?:להוסיף|הוסף)(?: לפני (?:פסקה|הפסקה)(?: \d+)?)? כותרת\s*:\s*(.+)$', fx)
    if m:
        t = strip_q(m.group(1))
        if 2 <= len(t.split()) <= 8:
            return {'heading': {'text': t}}
    m = re.match(r'^(?:להוסיף|הוסף) לפני הפסקה \(חלון 3\)\s*:\s*(.+)$', fx)
    if m:
        return {'anchor': {'text': strip_q(m.group(1))}}
    o = OPS.ins_from_fix(f)
    if o:
        return o
    return OPS.punct_op(f)


# ------------------------------------------------------------ ב. ניקוד מן המקרא
_PACK = []


def tanakh():
    if not _PACK:
        import nikud_mishna as NM
        _PACK.append((NM, NM.tanakh_pack()))
    return _PACK[0]


_DATA = {}


def site_data(slug):
    """נתוני הדף החי של מסכת (לשורה המלאה של ממצא שסימונו נחתך ב-50 תווים)"""
    if slug not in _DATA:
        import urllib.request
        path = os.path.join(OUT, 'data', slug + '.data.js')
        if not os.path.exists(path):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            req = urllib.request.Request('https://leokmei.com/%s.data.js' % slug, headers={'User-Agent': 'leokmei-convert/1.0'})
            open(path, 'wb').write(urllib.request.urlopen(req, timeout=60).read())
        t = open(path, encoding='utf-8').read()
        i = t.index('const DATA=') + len('const DATA=')
        _DATA[slug] = json.JSONDecoder().raw_decode(t[i:])[0]
    return _DATA[slug]


def ps_runs(slug):
    """כל קטעי הסגנון "פסוק" במסכת: טקסט פשוט"""
    D = site_data(slug)
    key = '_psr'
    if key not in D:
        out = []
        for p in D['pages']:
            for u in p['units']:
                for h in [u.get('a') or '', u.get('w') or ''] + [l[1] for l in (u.get('l') or [])]:
                    for m in re.finditer(r'<i class="ps">(.*?)</i>', h):
                        out.append(html.unescape(re.sub(r'<[^>]+>', '', m.group(1))))
        D[key] = out
    return D[key]


def full_mark(slug, f):
    """הסימון נחתך ב-50 תווים: הקטע המלא בסגנון פסוק שמתחיל בו, אם הוא יחיד"""
    mk = f.get('mark') or ''
    if len(mk) < 48:
        return mk
    c = [r for r in ps_runs(slug) if r.strip().startswith(mk.strip())]
    return c[0].strip() if len(set(x.strip() for x in c)) == 1 else mk


SKIPW = ('וגו', 'וכו', 'וגומר')
_TW = []


def tanakh_words():
    """כל המילים המנוקדות שבמקרא, כמות שהן"""
    if not _TW:
        rows = json.load(open(os.path.join(ROOT, 'data', 'tanakh-nikud.json'), encoding='utf-8'))
        _TW.append({w for r in rows for w in r[3]})
    return _TW[0]


def vocalize(ws):
    """ניקוד לרשימת מילים: רצפים של שתיים ומעלה מפסוק אחד (הארוך תחילה), ומילה בודדת רק מתוך
    פסוקים שכבר זוהו. אות בודדת (ה' של השם, ד' של ראיה) ו"וגו'" נשארות כמות שהן, ושוברות רצף.
    חסרה מילה אחת - אין ניקוד כלל (ניקוד חלקי אינו מוצע)"""
    NM, pack = tanakh()
    n, out, vis = len(ws), [None] * len(ws), set()
    skip = [len(w) == 1 or w in SKIPW for w in ws]
    i = 0
    while i < n:
        if skip[i]:
            out[i] = ws[i]
            i += 1
            continue
        e = i
        while e < n and not skip[e]:
            e += 1
        hit = None
        for j in range(e, i + 1, -1):
            r = NM.tanakh_run(ws[i:j], pack)
            if r and all(v is not None for v in r[0]):
                hit = (j, r)
                break
        if hit:
            j, (voc, vs) = hit
            out[i:j] = voc
            vis |= set(vs)
            i = j
        else:
            i += 1
    for k in range(n):
        if out[k] is None and vis:
            out[k] = NM.tanakh_word_in(ws[k], vis, pack)
    if not all(out) or all(skip[k] or False for k in range(n)):
        return None
    return out


def nikud_op(f, slug=None):
    if not tanakh()[1]:
        return None
    mk = full_mark(slug, f) if slug else (f.get('mark') or '')
    if "וגו" in mk or re.search(r"[א-ת]'[א-ת]", mk):     # קיצור בתוך הציטוט: אין ניקוד ודאי
        return None
    toks = [(m.start(), m.end(), m.group(0)) for m in HEB.finditer(mk)]
    if len(toks) < 2 or any(NIK.search(t[2]) for t in toks):
        return None
    words = [t[2] for t in toks]
    for cut in (0, 1, 2):                       # קידומת (ד', ו', מ') צמודה למילה הראשונה של הציטוט
        if cut and (len(words[0]) <= cut + 1 or not re.match(r'^[ודבלמהשכ]{%d}' % cut, words[0])):
            continue
        voc = vocalize([words[0][cut:]] + words[1:])
        if not voc:
            continue
        y, last = '', 0
        for j, (a, b, w0) in enumerate(toks):
            y += mk[last:a] + ((words[0][:cut] + voc[0]) if j == 0 and cut else voc[j])
            last = b
        y += mk[last:]
        if y != mk and compact(NIK.sub('', y)) == compact(mk):
            ex = not cut and all(len(v) == 1 or v in SKIPW or v in tanakh_words() for v in voc)
            o = {'nikud': {'x': mk, 'y': y}}
            if ex:
                o['nikud']['exact'] = 1        # כל מילה זהה למילה במקרא: מוחל לבד. אחרת - מוצע למחבר
            return o
    return None


# ------------------------------------------------------------ ג. החלה לבד
def verse_lenient(text):
    """האם רצף של שתי מילים מן הטקסט נמצא במקרא, גם בלי קידומת, עם קידומת שנוספה, ובכתיב מלא/חסר.
    מקל במתכוון: "נמצא" פירושו שאין להסיר את סגנון הפסוק לבד"""
    NM, pack = tanakh()
    if not pack:
        return True
    _, keys, idx = pack
    ws = [NIK.sub('', w) for w in HEB.findall(text)]
    PRE = ('', 'ו', 'ל', 'ול', 'ב', 'וב', 'ה', 'וה', 'מ', 'ומ', 'כ', 'וכ', 'ש', 'מה', 'וש')
    var = []
    for w in ws:
        base = {w}
        for c in (1, 2):
            if len(w) > c + 1 and re.match(r'^[ודבלמהשכ]{%d}' % c, w):
                base.add(w[c:])
        var.append({NM.skel(p + b) for b in base for p in PRE})
    for i in range(len(var) - 1):
        for a in var[i]:
            for vi, j in idx.get(a, []):
                if j + 1 < len(keys[vi]) and keys[vi][j + 1] in var[i + 1]:
                    return True
    return False


_CW = []


def cw():
    if not _CW:
        _CW.append(set(json.load(open(os.path.join(ROOT, 'data', 'common-words.json'), encoding='utf-8'))))
    return _CW[0]


def aram_pairs(all_rows):
    ok, no = collections.Counter(), collections.Counter()
    for f, d in all_rows:
        if f.get('det') != 'aram' or not d or d.get('d') in (None, 'pending'):
            continue
        fx = f.get('fix') or ''
        if '⟵' not in fx:
            continue
        x, y = [p.strip() for p in fx.split('⟵', 1)]
        y = re.sub(r'\s\?$', '', y)
        (ok if d.get('d') in ('ok', 'edit') else no)[(x, y)] += 1
    return {k for k in ok if not no.get(k)}


def auto_of(f, op, pairs):
    """מחזיר סיבה להחלה לבד, או None"""
    det = f.get('det')
    if not op:
        return None
    if det == 'amor_miss' and 'style' in op:
        m = (f.get('mark') or '').replace("''", '"').strip()
        core = re.sub(r'^[ודלכ]', '', m)
        if m in AMB_NAMES or core in AMB_NAMES:
            return None
        # ראשי תיבות עם גרשיים, או שם בן שתי מילים (ר' יהודה, רב אשי); שם בודד רק בלי קידומת כפולה
        # (נמדד: "שמרבה" נתפס כ-ש+מ+רבה)
        if re.search(r'["\']', m) or re.search(r'\s', m) or (core in ('אביי', 'רבא', 'רבה', 'רבינא', 'שמואל') and len(m) - len(core) <= 1):
            return 'שם בסגנון אמוראים'
        return None
    if det == 'psuk_nik' and 'nikud' in op:
        return 'ניקוד מן המקרא' if op['nikud'].get('exact') else None
    if det == 'psuk_miss' and 'style' in op:
        return 'פסוק מן המקרא בסגנון פסוק'
    if det == 'psuk_bad':
        # נמדד 26.10.2026: דרשות על מילים מן הפסוק ("טומאתו טומאתו", "תֶּחֱטָא תֶּחֱטָא") אינן רצף שבמקרא,
        # והמחבר דחה שלוש מתוך שבע. נשאר שאלה עם נוסח מוכן
        return None
    if det == 'punct' and 'rep' in op:
        x = op['rep']['x']
        # רווח לפני פסיק, ופיסוק כפול. טאב לפני פסיק - לא: הטאב הוא עימוד (טאב לשמאל)
        return 'פיסוק' if '\t' not in x and re.fullmatch(r' +,|[,.:]\s*[,.:]', x) else None
    if det == 'joined':
        # נמדד 26.10.2026: מילון המסכתות אינו אימות (שנתחללה, בכלכלתו, נשימתו נמצאו "דבוקות"). נשאר שאלה עם נוסח מוכן
        return None
    if det == 'aram' and 'rep' in op:
        return 'ארמית שהמחבר כבר קיבל' if (op['rep']['x'], op['rep']['y']) in pairs else None
    return None


def explicit_op(f):
    """המטען המפורש של ממצא (גם מה שהדף גוזר מ-fix), כדי שהבדיקה וההחלה יהיו על אותו מטען"""
    o = f.get('op') or {}
    if any(k in o for k in EXEC):
        return o
    fx = (f.get('fix') or '').strip()
    if fx.count('⟵') == 1 and ';' not in fx:
        x, y = [p.strip() for p in fx.split('⟵')]
        unsure = bool(re.search(r'\s\?$', y))
        y = re.sub(r'\s\?$', '', y).strip()
        if x and y and x != y:
            return {'rep': {'x': x, 'y': y, 'unsure': unsure}} if unsure else {'rep': {'x': x, 'y': y}}
    mk = f.get('mark') or ''
    if re.match(r'^להחיל סגנון אמוראים', fx):
        return {'style': {'range': mk, 'cs': 'am'}}
    if re.match(r'^להחיל סגנון פסוק', fx):
        return {'style': {'range': mk, 'cs': 'ps'}}
    if re.match(r'^להחזיר לסגנון רגיל', fx):
        return {'style': {'range': mk, 'cs': 'plain'}}
    return None


# ------------------------------------------------------------ ריצה
def fetch_all(slugs):
    import _api
    slugs = slugs or _api.call('/bakara/data').get('slugs', [])
    R = {}
    for s in slugs:
        R[s] = {'data': _api.call('/bakara/data?slug=' + s).get('doc') or {},
                'dec': (_api.call('/bakara/dec?slug=' + s).get('doc') or {}).get('dec') or {}}
    return R


def pending(f, dec):
    d = dec.get(f['id'])
    return not d or d.get('d') == 'pending'


def plan(slugs):
    R = fetch_all(slugs)
    os.makedirs(OUT, exist_ok=True)
    json.dump(R, open(os.path.join(OUT, 'snapshot.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    rows = [(f, R[s]['dec'].get(f['id'])) for s in R for p in (R[s]['data'].get('perakim') or {}).values() for f in p.get('findings', [])]
    pairs = aram_pairs(rows)
    changes, todo, st = {}, [], collections.Counter()
    for s in R:
        dec = R[s]['dec']
        for p, ch in (R[s]['data'].get('perakim') or {}).items():
            for f in ch.get('findings', []):
                if f.get('det') == 'dh_inline' or not pending(f, dec):
                    continue
                cur = f.get('op') or {}
                new, why = None, None
                op = explicit_op(f)
                if not op:
                    op = prose_op(f)
                    if op:
                        st['פרוזה הומרה למטען'] += 1
                if not op and f.get('det') == 'psuk_nik':
                    op = nikud_op(f, s)
                    st['ניקוד מן המקרא' if op else 'ניקוד: לא נמצא רצף ודאי'] += 1
                if op and op != cur:
                    new = op
                why = auto_of(f, op, pairs)
                if why:
                    st['לבד: ' + why] += 1
                if new or (why and f.get('auto') != 'tech'):
                    changes.setdefault(s, {}).setdefault(p, {})[f['id']] = {'op': op, 'auto': 'tech' if why else None, 'autoWhy': why}
                if not op or not any(k in op for k in EXEC):
                    if (f.get('det') in ('anchor', 'punct', 'orphan', 'nose_long', 'hash', 'abbr', 'sem_sty', 'sk_head')
                            or (f.get('det') or '').startswith(('sk_', 'sem_'))):
                        todo.append({'slug': s, 'perek': p, 'id': f['id'], 'det': f.get('det'), 'kind': f.get('kind'), 'u': f.get('u'),
                                     'daf': f.get('daf'), 'mark': f.get('mark'), 'fix': f.get('fix'), 'note': f.get('note'),
                                     'context': f.get('context') or f.get('text')})
                        st['למודל: ' + (f.get('kind') or f.get('det'))] += 1
                    else:
                        st['נשאר בלי מטען (חוזר להפקה): ' + (f.get('kind') or f.get('det'))] += 1
    json.dump(changes, open(PLAN, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    json.dump(todo, open(TODO, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    for k, v in sorted(st.items(), key=lambda x: -x[1]):
        print('%5d  %s' % (v, k))
    print('שינויים: %d ממצאים; למודל: %d' % (sum(len(x) for s in changes.values() for x in s.values()), len(todo)))


def valid_model_op(item, o, ctx):
    """בדיקת קוד לתשובת מודל: מבנה תקין, ולא נעלם ולא נברא טקסט במקום שאינו הוספה מפורשת"""
    if not isinstance(o, dict) or len(o) != 1:
        return 'מבנה'
    k = next(iter(o))
    v = o[k]
    if k not in EXEC:
        return 'סוג לא מוכר'
    if k == 'anchor':
        head = ctx.get('head') or ''
        t, r = (v.get('text') or '').strip(), (v.get('rest') or '').strip()
        if v.get('take'):
            return None if compact(v['take']) in compact(ctx.get('line') or '') else 'הדובר אינו בשורה'
        if not t or len(compact(t)) > 22:
            return 'כותרת ריקה או ארוכה'
        if head:
            words = lambda s: [w for w in re.findall(r'[א-ת"\']+', s)]
            if sorted(words(t + ' ' + r)) != sorted(words(head)) and compact(t + r) != compact(head):
                return 'מילים נוספו או נעלמו מן הכותרת'
        return None
    if k in ('rep', 'nikud'):
        if not v.get('x') or v.get('y') is None:
            return 'חסר x/y'
        if item.get('det') in ('punct', 'orphan') and re.sub(r'[\[\]\s]', '', v['x']) != re.sub(r'[\[\]\s]', '', v['y']):
            return 'בפיסוק מותר רק להוסיף או להסיר סוגר'
        if item.get('det') == 'abbr' and re.sub(r'[\'"״׳\s]', '', v['x']) != re.sub(r'[\'"״׳\s]', '', v['y']):
            return 'בסימני קיצור מותר רק לשנות גרש וגרשיים'
        if compact(v['x']) not in compact(ctx.get('line') or ctx.get('context') or '') and compact(v['x']) not in compact(item.get('context') or ''):
            return 'x אינו בשורה'
        return None
    if k == 'ins':
        if not v.get('text'):
            return 'אין טקסט'
        a = v.get('after') or v.get('before')
        if a and compact(a) not in compact((ctx.get('line') or '') + (item.get('context') or '')):
            return 'העוגן אינו בשורה'
        return None
    if k == 'heading':
        n = len((v.get('text') or '').split())
        return None if 2 <= n <= 6 else 'כותרת 2-6 מילים'
    return None


def merge(paths):
    changes = json.load(open(PLAN, encoding='utf-8')) if os.path.exists(PLAN) else {}
    todo = {t['id']: t for t in json.load(open(TODO, encoding='utf-8'))}
    st = collections.Counter()
    bad = []
    for p in paths:
        ans = json.load(open(p, encoding='utf-8'))
        for a in ans:
            it = todo.get(a.get('id'))
            if not it:
                st['מזהה לא מוכר'] += 1
                continue
            o = a.get('op')
            if not o and a.get('skip'):
                # אין שינוי: הממצא נשאר מחוץ לתור, והסיבה מוצגת בלשונית "ניהול"
                changes.setdefault(it['slug'], {}).setdefault(it['perek'], {})[it['id']] = {'op': {'none': 'נבדק: ' + str(a['skip'])[:200]}, 'auto': None, 'autoWhy': None, 'by': 'model'}
                st['נבדק בלי שינוי'] += 1
                continue
            if o and 'ask' in o:
                if it.get('det') == 'sk_q' or it.get('kind') == 'שאלה למחבר':
                    changes.setdefault(it['slug'], {}).setdefault(it['perek'], {})[it['id']] = {'op': o, 'auto': None, 'autoWhy': None, 'by': 'model'}
                    st['שאלה למחבר, מנוסחת'] += 1
                else:
                    st['נפסל: שאלה במקום מטען'] += 1
                continue
            ctx = a.get('ctx') or {'head': it.get('head', ''), 'line': it.get('line', '')}
            ctx.setdefault('head', it.get('head', ''))
            ctx.setdefault('line', it.get('line', ''))
            e = (None if a.get('trusted') and isinstance(o, dict) and len(o) == 1 and next(iter(o)) in EXEC else valid_model_op(it, o, ctx)) if o else 'אין מטען'
            if e:
                st['נפסל: ' + e] += 1
                bad.append({'id': it['id'], 'why': e, 'op': o})
                continue
            alts = [x for x in (a.get('alts') or [])[:2] if not valid_model_op(it, x, ctx)]
            ent = {'op': o, 'auto': None, 'autoWhy': None, 'by': 'model'}
            if alts:
                ent['alts'] = alts
            changes.setdefault(it['slug'], {}).setdefault(it['perek'], {})[it['id']] = ent
            st['התקבל: ' + (it.get('kind') or it.get('det'))] += 1
    json.dump(changes, open(PLAN, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    json.dump(bad, open(os.path.join(OUT, 'model-rejected.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    for k, v in sorted(st.items(), key=lambda x: -x[1]):
        print('%5d  %s' % (v, k))


def push(dry=False):
    import _api
    changes = json.load(open(PLAN, encoding='utf-8'))
    os.makedirs(BACKUP, exist_ok=True)
    stamp = time.strftime('%Y%m%d-%H%M%S')
    tot = 0
    for s, per in changes.items():
        d = _api.call('/bakara/data?slug=' + s).get('doc') or {}
        json.dump(d, open(os.path.join(BACKUP, '%s-%s.json' % (s, stamp)), 'w', encoding='utf-8'), ensure_ascii=False)
        dec = (_api.call('/bakara/dec?slug=' + s).get('doc') or {}).get('dec') or {}
        for p, items in per.items():
            ch = (d.get('perakim') or {}).get(p)
            if not ch:
                continue
            n = 0
            for f in ch.get('findings', []):
                c = items.get(f['id'])
                if not c or not pending(f, dec):
                    continue
                if c.get('op'):
                    f['op'] = c['op']
                if c.get('alts'):
                    f['alts'] = c['alts']
                if c.get('auto'):
                    f['auto'] = c['auto']
                    f['autoWhy'] = c.get('autoWhy')
                if c.get('by'):
                    f['opBy'] = c['by']
                n += 1
            if n and not dry:
                r = _api.call('/bakara/data', 'PUT', {'slug': s, 'perek': int(p), 'data': ch})
                print('הועלה', s, p, n, r.get('n'))
            tot += n
    print('סה"כ ממצאים שעודכנו:', tot, '(גיבוי ב-%s)' % BACKUP)




# ------------------------------------------------------------ הקשר למודל
def _plain(h):
    return html.unescape(re.sub(r'<[^>]+>', '', (h or '').replace('<br>', ' / ')))


def _units(slug):
    D = site_data(slug)
    if '_ux' not in D:
        L = []
        for pi, p in enumerate(D['pages']):
            for u in p['units']:
                if u.get('k') in ('u', 'm'):
                    L.append((u, p.get('daf')))
        D['_ux'] = L
    return D['_ux']


def enrich(chunk=180):
    """לכל פריט למודל: כותרת הצד, השורה שבה הסימון, והשורות שלפניה ואחריה - מנתוני הדף החי"""
    todo = json.load(open(TODO, encoding='utf-8'))
    miss = 0
    for it in todo:
        mk = compact(it.get('mark') or '')
        cx = compact((it.get('context') or '')[:60])
        best = None
        for u, daf in _units(it['slug']):
            head = _plain(u.get('a') if u.get('k') == 'u' else u.get('w'))
            lines = [_plain(l[1]) for l in u.get('l') or []]
            if it['det'] == 'anchor':
                if mk and mk in compact(head):
                    sc = (0 if u.get('id') == it.get('u') else 1)
                    if best is None or sc < best[0]:
                        best = (sc, head, lines[0] if lines else '', '', lines[1] if len(lines) > 1 else '', daf)
                continue
            for i, t in enumerate(lines):
                ct = compact(t)
                if (mk and mk in ct) or (cx and cx in ct):
                    sc = (0 if u.get('id') == it.get('u') else 1) + (0 if mk and mk in ct else 2)
                    if best is None or sc < best[0]:
                        best = (sc, head, t, lines[i - 1] if i else '', lines[i + 1] if i + 1 < len(lines) else '', daf)
        if best:
            it['head'], it['line'], it['prev'], it['next'] = best[1], best[2], best[3], best[4]
        else:
            miss += 1
    json.dump(todo, open(TODO, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    groups = collections.defaultdict(list)
    for it in todo:
        if it.get('line') is None and it.get('head') is None:
            continue
        g = 'anchor' if it['det'] == 'anchor' else ('abbr' if it['det'] == 'abbr' else ('punct' if it['det'] in ('punct', 'orphan') else 'content'))
        groups[g].append({k: it.get(k) for k in ('id', 'det', 'kind', 'daf', 'mark', 'fix', 'note', 'head', 'line', 'prev', 'next')})
    files = []
    for g, L in groups.items():
        for i in range(0, len(L), chunk):
            fn = os.path.join(OUT, 'chunk-%s-%02d.json' % (g, i // chunk))
            json.dump(L[i:i + chunk], open(fn, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
            files.append((fn, len(L[i:i + chunk])))
    print('לא נמצא הקשר:', miss)
    for fn, n in files:
        print(n, fn)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--plan', action='store_true')
    ap.add_argument('--merge', nargs='*')
    ap.add_argument('--push', action='store_true')
    ap.add_argument('--dry', action='store_true')
    ap.add_argument('--enrich', action='store_true')
    ap.add_argument('--slug', action='append', default=[])
    a = ap.parse_args()
    if a.plan:
        plan(a.slug)
    if a.enrich:
        enrich()
    if a.merge:
        merge(a.merge)
    if a.push:
        push(a.dry)


if __name__ == '__main__':
    main()
