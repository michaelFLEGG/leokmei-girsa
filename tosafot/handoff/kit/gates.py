# -*- coding: utf-8 -*-
"""gates.py - ערכת הכלים של מפעל התוס' בחשבון השני (24.10.2026). פייתון 3, ספרייה סטנדרטית בלבד.

זהו המקור היחיד של שערי הקוד של בית החרושת לתוספות: factory.py, factory_flow.py, make_anchors.py ו-triage_reviewer.py
קוראים מכאן, כדי שלא יהיו שתי גרסאות של אותם כללים. כאן אין מודל ואין רשת: רק קבצים.

השרשרת לכל יחידה (tosafot/handoff/units/<id>.json), כפי שבהוראות הקבועות (kit/INSTRUCTIONS.md, סעיף ג.2):
    python3 kit/gates.py write-jobs units/<id>.json work/<id>/     -> job-*.md   (MODEL: sonnet / fable)
    python3 kit/gates.py ingest-write work/<id>/                   <- ans-job-*.txt
    python3 kit/gates.py review-jobs work/<id>/                    -> rv-*.md    (MODEL: haiku)
    python3 kit/gates.py ingest-review work/<id>/                  <- ans-rv-*.txt
    python3 kit/gates.py rewrite-jobs work/<id>/                   -> rw-*.md    (MODEL: fable)
    python3 kit/gates.py ingest-rewrite work/<id>/                 <- ans-rw-*.txt
    python3 kit/gates.py rereview-jobs work/<id>/                  -> rr-*.md    (MODEL: sonnet)
    python3 kit/gates.py ingest-rereview work/<id>/                <- ans-rr-*.txt
    python3 kit/gates.py finalize work/<id>/ out-<id>.json

קובץ תשובה: ans-<שם קובץ העבודה>.txt (מתקבל גם בלי הסיומת .md וגם איתה). כל פקודת jobs שאין לה מה לשלוח מדפיסה
"אין מה לשלוח" ויוצאת בקוד 0. תשובה חסרה אינה נבלעת: התוספות נכנס לכתיבה מחדש עם הסיבה "חסר בפלט".
"""
import os, sys, re, json, io, glob, random, datetime

VERSION = '2026-10-24.1'
KIT = os.path.dirname(os.path.abspath(__file__))

NIK = re.compile('[֑-ׇ]')
DASH = re.compile('[–—―]')
WORDS = re.compile(r'\S+')
TIRUTZ = re.compile(r'וי"ל|ויש לומר|ותירץ|תי\'|ועוד י"ל|וי״ל|ואומר ר"י|וי"מ|ואם תאמר|וא"ת|וקשה')


# ---------------------------------------------------------------- נרמול ועוגן (כמו buildIndex בדפדפן)
def norm_idx(lines):
    """אותו נרמול כמו buildIndex בדפדפן: אותיות בלבד, מקף/רווח כרווח יחיד, שורות מופרדות ברווח."""
    s = ''
    for ln in lines:
        for c in NIK.sub('', ln):
            if 'א' <= c <= 'ת':
                s += c
            elif c.isspace() or c in '-־':
                if s and s[-1] != ' ':
                    s += ' '
        if s and s[-1] != ' ':
            s += ' '
    return s


def norm_ctx(t):
    return norm_idx([t]).strip()


def find_occ(idx, ctx):
    """רשימת המופעים (שלמי מילים) של ctx ב-idx; מחזיר כמה יש."""
    out, frm = [], 0
    while True:
        k = idx.find(ctx, frm)
        if k < 0:
            return out
        if (k == 0 or idx[k - 1] == ' ') and (k + len(ctx) >= len(idx) or idx[k + len(ctx)] == ' '):
            out.append(k)
        frm = k + 1


def is_hard(r, c):
    n = len(WORDS.findall(r['text']))
    t = len(TIRUTZ.findall(r['text']))
    return n >= c['hard']['words'] or t >= c['hard']['markers']


# ---------------------------------------------------------------- פרומפטים
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

SYS_V2 = """אתה מבקר זהיר של שורת מסקנה (הערת שוליים) שנכתבה על תוספות בספר לימוד של הש"ס. לכל תוספות יוגשו: ד"ה, לשון התוספות המלאה, השורה שנכתבה, ושאלות (אם יש). בדוק מול לשון התוספות המלאה בלבד.

מונחים: "קונטרס" הוא רש"י. ר"ת הוא רבינו תם. ר"י הוא רבי יצחק (הזקן) מבעלי התוספות. ריב"א הוא רבי יצחק בן אשר. ר"ח הוא רבנו חננאל. הרשב"א, הרא"ש והר"ן הם ראשונים מאוחרים. "הא דקאמר" וכדומה הם לשון תוספות רגילה. ייחוס "לרש"י" שורה שהתוספות מכנים "בקונטרס" אינו שגוי.

שלוש דרגות. החזר לכל תוספות דרגה אחת:

1. "תקין": התוכן נאמן ללשון התוספות. מותר תמצות, קיצור וסידור (לרש"י... ולתוס'...). מותר מטבע לשון מוכר שאינו מפורש. אין לפסול על סגנון, על כך שהשורה "מכנית", על כך שאפשר היה לנסח אחרת, או על כך שלא הוסבר דבר שהתוספות עצמם לא הסבירו. אנו אינם מחויבים ליותר ממה שהתוספות כתבו.

2. "תיקון קל": התוכן נאמן, אך יש בשורה פגם קטן שאתה מתקן בעצמך: הפניה למקור או דף שאינם בלשון התוספות (מחק אותה), מילה עודפת, או שורה ארוכה שאפשר לקצר בלי לאבד נימוק. החזר בשדה "fix" את השורה המתוקנת במלואה. אל תוסיף דבר שאינו בתוספות.

3. "פסול": רק כשיש אחד מאלה: (א) תוספת דין או מסקנה שאינה בתוספות; (ב) השמטת נימוק מכריע, כך שהשורה מטעה או אינה מובנת; (ג) ייחוס הפוך (דעה לאדם הלא נכון); (ד) טעות עניינית. בשדה "s" כתוב את הסיבה הקצרה והמדויקת.

הפניה לתוספות אחר או למקום אחר ("כמו שכתבנו", "בד"ה ...") אינה פגם: אל תפסול עליה ואל תמחק אותה כשהיא בלשון התוספות. אם השורה מפנה למקום אחר ויש צורך שמודל חזק יבדוק אחר כך את היעד, סמן "star": true. אל תשנה מספור או הפניות פנימיות.

שאלות: כל שאלה נבדקת בנפרד. שאלה פגומה (התשובה אינה בתוספות, השאלה מסגירה את התשובה, בנאלית, כפולה) מקבלת סיבה קצרה ברשימה "q" במקומה; שאלה תקינה מקבלת מחרוזת ריקה.

החזר JSON אחד בלבד, בלי גדרות קוד, בלי טקסט נוסף, לכל מזהה שהוגש:
{"<מזהה>": {"d": "תקין" | "תיקון קל" | "פסול", "s": "<סיבה, רק בפסול>", "fix": "<השורה המתוקנת, רק בתיקון קל>", "star": false, "q": ["", ...]}}
אל תכתוב קו מפריד ארוך (em dash או en dash) ואל תכתוב את התו ; (נקודה-פסיק)."""


def page_user_msg(slug, perek, dafKey, ctx, recs, ctxp, extra=''):
    lines = '\n'.join('%d. %s' % (i + 1, l) for i, l in enumerate(ctxp['lines'])) or '(אין שורות לאוקמי גירסא לעמוד זה. החזר "a": null.)'
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


def _words(s):
    return set(re.findall(r'[א-ת]{2,}', NIK.sub('', s or '')))


def pick_examples(examples, text, line, exclude=None, k=6):
    """הדוגמאות הרלוונטיות מהכרעות המנהל: דמיון מילים (ז'קארד) ללשון התוספות ולשורה, ואיזון: לפחות שתיים משני הכיוונים כשיש."""
    ex = [e for e in examples if e.get('ans') in ('yes', 'no') and e.get('id') != exclude]
    q = _words(text) | _words(line)
    sc = []
    for e in ex:
        w = _words(e.get('text')) | _words(e.get('line'))
        sc.append((len(q & w) / float(len(q | w) or 1), e))
    sc.sort(key=lambda x: -x[0])
    out = [e for _, e in sc[:k]]
    for a in ('yes', 'no'):
        if sum(1 for e in out if e['ans'] == a) < 2:
            for _, e in sc:
                if e['ans'] == a and e not in out:
                    out.append(e)
                    if sum(1 for x in out if x['ans'] == a) >= 2:
                        break
    return out


def fmt_example(e):
    v = 'נכון (השורה תקינה, המבקר טעה אם פסל)' if e['ans'] == 'yes' else 'לא נכון (יש בשורה פגם אמיתי)'
    return ('### דוגמה מהכרעת המנהל\nד"ה: %s\nלשון התוספות: %s\nהשורה: %s\nנימוק המבקר הקודם: %s\nהכרעת המנהל: %s\nהערת המנהל: %s'
            % (e.get('dh', ''), ' '.join((e.get('text') or '').split()[:220]), e.get('line', ''), ' | '.join(e.get('why') or []) or '(לא פסל)', v, e.get('note') or '(אין)'))


def system_with_examples(examples, blocks_text_line, exclude=None):
    """blocks_text_line: [(text, line)] של הקבוצה; מצרף את הדוגמאות הרלוונטיות להוראות המבקר V2."""
    seen, out = set(), []
    for t, l in blocks_text_line:
        for e in pick_examples(examples, t, l, exclude, 4):
            if e['id'] not in seen:
                seen.add(e['id'])
                out.append(e)
    if not out:
        return SYS_V2
    return SYS_V2 + '\n\n## דוגמאות מהכרעות המנהל (למד מהן את הרף)\n\n' + '\n\n'.join(fmt_example(e) for e in out[:8])


def user_block(rid, dh, text, line, qs):
    q = '\n'.join('  שאלה %d: %s | תשובה: %s' % (i + 1, x['q'], x['a']) for i, x in enumerate(qs or [])) or '  (אין שאלות)'
    return '### מזהה: %s\nדיבור המתחיל: %s\nלשון התוספות המלאה:\n%s\nהשורה שנכתבה: %s\nשאלות:\n%s' % (rid, dh, text, line, q)


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
    if ';' in s:
        bad.append('תו ; (כלל 14.10.2026: נקודה)')
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
    if ';' in qq or ';' in aa:
        bad.append('תו ; (כלל 14.10.2026: נקודה)')
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


def repair_quotes(t):
    """מתקן מרכאות שלא הוברחו בתוך מחרוזת (ש"ס, רש"י, "מה לי"), תקלה שנמדדה ב-24.10.2026 בכתיבה דרך תת-סוכן.
    מרכאה בתוך מחרוזת נחשבת סוגרת רק כשאחריה (אחרי רווחים) בא : } ] , או פסיק שאחריו פותח ערך או מפתח חדש."""
    out, i, n, ins = [], 0, len(t), False
    while i < n:
        ch = t[i]
        if not ins:
            out.append(ch)
            if ch == '"':
                ins = True
            i += 1
            continue
        if ch == '\\' and i + 1 < n:
            out.append(t[i:i + 2])
            i += 2
            continue
        if ch == '"':
            j = i + 1
            while j < n and t[j] in ' \t\r\n':
                j += 1
            nxt = t[j] if j < n else ''
            close = nxt in ('', ':', '}', ']')
            if nxt == ',':
                k = j + 1
                while k < n and t[k] in ' \t\r\n':
                    k += 1
                close = k >= n or t[k] in '"{[-0123456789ntf'
            if close:
                out.append(ch)
                ins = False
            else:
                out.append('\\"')
            i += 1
            continue
        if ch == '\n':
            out.append('\\n')
            i += 1
            continue
        out.append(ch)
        i += 1
    return ''.join(out)


def parse_json(t):
    t = (t or '').strip()
    t = re.sub(r'^```(?:json)?|```$', '', t, flags=re.M).strip()
    try:
        return json.loads(t)
    except Exception:
        pass
    # תת-סוכן שתיקן את עצמו מחזיר לפעמים שני אובייקטים ("Wait... Corrected:"): קודם האחרון שבתחילת שורה, אחר כך הראשון
    starts = [m.start() for m in re.finditer(r'(?:^|\n)\s*\{', t)]
    cands = []
    for s0 in reversed(starts):
        s0 = t.index('{', s0)
        e0 = t.find('\n}', s0)
        j = t.rfind('}')
        cands.append(t[s0:j + 1])
        k = t.find('}\n', s0)
        if k > 0:
            cands.append(t[s0:k + 1])
    i, j = t.find('{'), t.rfind('}')
    if 0 <= i < j:
        cands.append(t[i:j + 1])
    for cand in cands:
        for f in (lambda x: x, repair_quotes):
            try:
                return json.loads(f(cand))
            except Exception:
                continue
    raise ValueError('פלט לא JSON')


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


# ---------------------------------------------------------------- השכבות (משותף ל-factory_flow.py ולערכה)
def tidy_q(q):
    if not isinstance(q, dict):
        return {'t': '', 'lvl': '', 'q': '', 'a': ''}
    return {'t': norm_type(q.get('t')), 'lvl': q.get('lvl'), 'q': str(q.get('q', '')).strip(), 'a': str(q.get('a', '')).strip()}


def add_usage(acc, res):
    u = acc.setdefault(res.get('model', ''), {'in': 0, 'cw': 0, 'cr': 0, 'out': 0, 'n': 0})
    for k in ('in', 'cw', 'cr', 'out'):
        u[k] += (res.get('usage') or {}).get(k, 0)
    u['n'] += 1


def variety_pass(work):
    by_daf = {}
    for r in work['recs'].values():
        if r.get('q'):
            by_daf.setdefault(r['dafKey'], []).append(r)
    for dk, rs in by_daf.items():
        rs.sort(key=lambda x: x['n'])
        for ri, qi in check_page_variety(rs):
            r = work['recs'][ri]
            r.setdefault('bad_q', {}).setdefault(str(qi), [])
            if 'גיוון' not in r['bad_q'][str(qi)]:
                r['bad_q'][str(qi)].append('גיוון')


def ingest_write_core(work, results, c, page_of):
    """קליטת הכתיבה. results: {cid: {ok, text, model[, usage]}}. page_of(meta) -> ctxp (שורות הלאוקמי והגמרא של העמוד).
    כיול: נשמרת השורה כמות שהיא (cal_out); חישוב הדמיון בידי מי שמחזיק את נוסח המנהל."""
    idxs = {}
    stats = {'ok': 0, 'bad': 0, 'api': 0}
    usage = {}
    for cid, res in results.items():
        meta = work['reqs'].get(cid)
        if not meta:
            continue
        if res.get('ok'):
            add_usage(usage, res)
        if meta.get('cal'):
            s = ''
            err = None
            if res.get('ok'):
                try:
                    got = parse_json(res['text'])
                    s = str((got.get(meta['ids'][0]) or list(got.values())[0]).get('s', ''))
                except Exception:
                    err = 'parse'
            else:
                err = 'missing'
            row = {'key': meta['ids'][0], 's': s}
            if meta.get('final') is not None:
                row['sim'] = round(similarity(s, meta['final']), 3) if not err else 0.0
            if err:
                row['err'] = err
            work.setdefault('cal_out', []).append(row)
            if 'sim' in row:
                work['cal'].append({k: v for k, v in row.items() if k != 's'})
            continue
        if not res.get('ok'):
            for i in meta['ids']:
                work['recs'][i].update({'bad_s': ['api:' + str(res.get('err'))], 'bad_a': True, 'q': [], 'bad_q': {}})
                stats['api'] += 1
            continue
        try:
            got = parse_json(res['text'])
            if not isinstance(got, dict):
                raise ValueError('not a dict')
        except Exception:
            for i in meta['ids']:
                work['recs'][i].update({'bad_s': ['פלט לא JSON'], 'bad_a': True, 'q': [], 'bad_q': {}})
                stats['bad'] += 1
            continue
        ctxp = page_of(meta)
        idx = idxs.setdefault(meta['dafKey'], norm_idx(ctxp['lines']))
        for i in meta['ids']:
            rec = work['recs'][i]
            g = got.get(i)
            if not isinstance(g, dict):
                rec.update({'bad_s': ['חסר בפלט'], 'bad_a': True, 'q': [], 'bad_q': {}})
                stats['bad'] += 1
                continue
            rec['s'] = str(g.get('s', '')).strip()
            rec['bad_s'] = check_line(rec['s'], rec, c)
            rec['a'] = resolve_anchor(g.get('a'), ctxp, idx)
            rec['bad_a'] = False          # עוגן שלא נמצא אינו כשל: הסימן יונח לפי השכנים (factory_place.py)
            qs = g.get('q')
            rec['q'] = [tidy_q(q) for q in qs] if isinstance(qs, list) else []
            rec['q'] = cap_questions(rec['q'], rec, c)
            rec['bad_q'] = {str(k): check_q(q, rec, c) for k, q in enumerate(rec['q'])}
            stats['bad' if (rec['bad_s'] or rec['bad_a']) else 'ok'] += 1
    variety_pass(work)
    return usage, stats


def has_fail(rec):
    if rec.get('bad_s') or rec.get('bad_a') or rec.get('rv_s') or rec.get('s') is None:
        return True
    return any(v for v in (rec.get('bad_q') or {}).values()) or any((rec.get('rv_q') or {}).values())


def review_groups(work, c, label, system_of, v2=True):
    """[(cid, system, user, ids)] לכל התוספות שעברו שערי קוד בשורה ובעוגן; שאלות שנפסלו בקוד אינן נשלחות.
    label: 'rv-<מסכת>-p<פרק>' ; system_of(group) -> הנחיית המבקר."""
    out = []
    byd = {}
    for r in work['recs'].values():
        if r.get('cal') or r.get('s') is None or r.get('bad_s') or r.get('bad_a') or r.get('rv_done'):
            continue
        byd.setdefault(r['dafKey'], []).append(r)
    per = c['maxPerRequest']
    for dk, rs in byd.items():
        rs.sort(key=lambda x: x['n'])
        for gi in range(0, len(rs), per):
            g = rs[gi:gi + per]
            if v2:
                blocks = [user_block(r['rid'], r['dh'], r['text'], r['s'],
                                     [q for i, q in enumerate(r['q']) if not (r.get('bad_q') or {}).get(str(i))]) for r in g]
            else:
                blocks = []
                for r in g:
                    qs = '\n'.join('  שאלה %d: %s | תשובה: %s' % (i + 1, q['q'], q['a']) for i, q in enumerate(r['q'])
                                   if not (r.get('bad_q') or {}).get(str(i))) or '  (אין שאלות)'
                    blocks.append('### מזהה: %s\nדיבור המתחיל: %s\nפנים התוספות:\n%s\nשורת מסקנה: %s\nשאלות:\n%s'
                                  % (r['rid'], r['dh'], r['text'], r['s'], qs))
            cid = '%s-%s-%d' % (label, g[0]['daf'], gi // per)
            out.append((cid, system_of(g), '\n\n'.join(blocks), [r['rid'] for r in g]))
    return out


def ingest_review_core(work, results, c, reqmap):
    """reqmap: {cid: [rid...]}. פורמט V2: תקין / תיקון קל (עם fix) / פסול / star. כשל בביקורת אינו אישור."""
    usage = {}
    for cid, res in results.items():
        ids = reqmap.get(cid)
        if ids is None:
            continue
        if not res.get('ok'):
            for i in ids:
                work['recs'][i]['rv_s'] = 'ביקורת נכשלה: ' + str(res.get('err'))
                work['recs'][i]['rv_done'] = True
            continue
        add_usage(usage, res)
        try:
            got = parse_json(res['text'])
        except Exception:
            for i in ids:
                work['recs'][i]['rv_s'] = 'פלט ביקורת לא JSON'
                work['recs'][i]['rv_done'] = True
            continue
        if isinstance(got, list):   # 14.10: המבקר החדש מחזיר לפעמים רשימה במקום מילון
            m = {}
            for pos, x in enumerate(got):
                if not isinstance(x, dict):
                    continue
                k = x.get('id') or x.get('rid') or x.get('מזהה')
                if k is None and len(x) == 1 and isinstance(next(iter(x.values())), dict):
                    m.update(x)
                elif k is not None:
                    m[str(k)] = x
                elif pos < len(ids):
                    m[ids[pos]] = x
            got = m
        if not isinstance(got, dict):
            got = {}
        for i in ids:
            rec = work['recs'][i]
            rec['rv_s'], rec['rv_q'], rec['rv_done'] = '', {}, True
            g = got.get(i)
            if isinstance(g, dict) and g.get('d'):
                if g['d'] == 'תיקון קל' and str(g.get('fix') or '').strip():
                    fixed = str(g['fix']).strip().replace(';', '.')
                    if not check_line(fixed, rec, c):
                        rec['s'], rec['bad_s'], rec['rv_fix'] = fixed, [], True
                if g['d'] == 'פסול':
                    rec['rv_s'] = str(g.get('s') or 'פסול')
                if g.get('star'):
                    rec['star'] = True
                for k, why in enumerate(g.get('q') or []):
                    if why:
                        rec['rv_q'][str(k)] = str(why)
            elif isinstance(g, dict):
                rec['rv_s'] = str(g.get('s') or '')
                qs = g.get('q') or []
                if isinstance(qs, list):
                    for k, why in enumerate(qs):
                        if why:
                            rec['rv_q'][str(k)] = str(why)
    return usage


def rewrite_groups(work, c, label, slug, perek, masechet, page_of_dk):
    """[(cid, user, ids, dafKey)] רק למה שנפסל (בקוד או במבקר), פעם אחת לכל תוספות, עם הסיבות והגרסה הקודמת."""
    byd = {}
    for r in work['recs'].values():
        if r.get('cal') or r.get('tries', 1) >= 2 or not has_fail(r):
            continue
        byd.setdefault(r['dafKey'], []).append(r)
    out = []
    per = max(1, c['maxPerRequest'] // 2)
    for dk, rs in byd.items():
        rs.sort(key=lambda x: x['n'])
        for gi in range(0, len(rs), per):
            g = rs[gi:gi + per]
            notes = []
            for r in g:
                why = []
                if r.get('bad_s'):
                    why.append('שורה: ' + ', '.join(r['bad_s']))
                if r.get('rv_s'):
                    why.append('שורה (מבקר): ' + r['rv_s'])
                if r.get('bad_a'):
                    why.append('עוגן: הקטע לא נמצא בשורות הלאוקמי')
                for k, v in (r.get('bad_q') or {}).items():
                    if v:
                        why.append('שאלה %d: %s' % (int(k) + 1, ', '.join(v)))
                for k, v in (r.get('rv_q') or {}).items():
                    why.append('שאלה %d (מבקר): %s' % (int(k) + 1, v))
                prev = {'s': r.get('s'), 'q': r.get('q')}
                notes.append('מזהה %s - נפסל: %s\nהגרסה הקודמת: %s' % (r['rid'], '; '.join(why) or 'כללי', json.dumps(prev, ensure_ascii=False)))
            um = page_user_msg(slug, perek, dk, {'masechet': masechet}, g, page_of_dk(dk, g[0]['daf']), REWRITE_NOTE + '\n\n' + '\n\n'.join(notes))
            cid = '%s-%s-%d' % (label, g[0]['daf'], gi // per)
            out.append((cid, um, [r['rid'] for r in g], dk))
    return out


def ingest_rewrite_core(work, results, c, reqmap, page_of_dk):
    """reqmap: {cid: {ids, dafKey}}. מחליף רק את מה שנפסל (שורה / עוגן / שאלות)."""
    usage = {}
    for cid, res in results.items():
        meta = reqmap.get(cid)
        if not meta:
            continue
        for i in meta['ids']:
            work['recs'][i]['tries'] = 2
            work['recs'][i]['rv_done'] = False
        if not res.get('ok'):
            continue
        add_usage(usage, res)
        try:
            got = parse_json(res['text'])
            if not isinstance(got, dict):
                raise ValueError('not a dict')
        except Exception:
            continue
        ctxp = page_of_dk(meta['dafKey'], work['recs'][meta['ids'][0]]['daf'])
        idx = norm_idx(ctxp['lines'])
        for i in meta['ids']:
            rec = work['recs'][i]
            g = got.get(i)
            if not isinstance(g, dict):
                continue
            s_failed = bool(rec.get('bad_s') or rec.get('rv_s') or rec.get('s') is None)
            a_failed = bool(rec.get('bad_a'))
            q_failed = any(v for v in (rec.get('bad_q') or {}).values()) or any((rec.get('rv_q') or {}).values())
            if s_failed:
                rec['s'] = str(g.get('s', '')).strip()
                rec['bad_s'] = check_line(rec['s'], rec, c)
                rec['rv_s'] = ''
            if a_failed or rec.get('a') is None:
                rec['a'] = resolve_anchor(g.get('a'), ctxp, idx)
            rec['bad_a'] = False
            if q_failed:
                qs = g.get('q')
                rec['q'] = cap_questions([tidy_q(q) for q in qs] if isinstance(qs, list) else [], rec, c)
                rec['bad_q'] = {str(k): check_q(q, rec, c) for k, q in enumerate(rec['q'])}
                rec['rv_q'] = {}
    variety_pass(work)
    return usage


def finalize_core(work):
    """אחרי כתיבה מחדש וביקורת חוזרת: מה שעדיין נכשל מסומן (flagged, "לעיון המנהל") ואינו נמחק."""
    flagged = []
    for r in work['recs'].values():
        if r.get('cal'):
            continue
        s_bad = bool(r.get('bad_s') or r.get('rv_s') or r.get('s') is None)
        r['status'] = 'flagged' if s_bad else 'ok'
        keep, drop = [], []
        for k, q in enumerate(r.get('q') or []):
            bq = (r.get('bad_q') or {}).get(str(k))
            rq = (r.get('rv_q') or {}).get(str(k))
            if bq or rq:
                drop.append({'q': q, 'why': bq or [rq]})
            else:
                keep.append(q)
        r['q_keep'], r['q_drop'] = keep, drop
        if s_bad:
            flagged.append({'rid': r['rid'], 'dh': r['dh'], 'daf': r['daf'],
                            'why': list(r.get('bad_s') or []) + ([r['rv_s']] if r.get('rv_s') else [])})
    return flagged


# ---------------------------------------------------------------- הערכה: קבצים
def jload(p, default=None):
    if not os.path.exists(p):
        return default
    with io.open(p, encoding='utf-8') as f:
        return json.load(f)


def jdump(p, o):
    d = os.path.dirname(os.path.abspath(p))
    os.makedirs(d, exist_ok=True)
    tmp = p + '.tmp'
    with io.open(tmp, 'w', encoding='utf-8') as f:
        json.dump(o, f, ensure_ascii=False, indent=1)
    os.replace(tmp, p)


def system_write():
    p = os.path.join(KIT, 'system-write.md')
    if not os.path.exists(p):
        raise SystemExit('עצירה: אין system-write.md ליד gates.py')
    return io.open(p, encoding='utf-8').read()


MODELS = ('sonnet', 'fable', 'haiku', 'opus')


def short_model(m):
    m = str(m or '').lower()
    for k in MODELS:
        if k in m:
            return k
    return m


def job_text(model, system, user):
    return ('MODEL: %s\n\n# הנחיה קבועה\n\n%s\n\n# הבקשה\n\n%s\n' % (short_model(model), system.strip(), user.strip()))


def write_job(wd, name, model, system, user):
    io.open(os.path.join(wd, name), 'w', encoding='utf-8', newline='\n').write(job_text(model, system, user))


def ans_map(wd, prefix):
    """{שם קובץ עבודה בלי .md: תוכן התשובה} לכל ans-<prefix>*.txt."""
    out = {}
    for p in glob.glob(os.path.join(wd, 'ans-%s*' % prefix)):
        b = os.path.basename(p)
        if not b.endswith('.txt'):
            continue
        name = b[len('ans-'):-len('.txt')]
        if name.endswith('.md'):
            name = name[:-3]
        out[name] = io.open(p, encoding='utf-8', errors='replace').read()
    return out


def results_from(wd, prefix, cids):
    """{cid: {ok, text, model}} לכל בקשה, מקובצי התשובה. תשובה חסרה = ok False (נרשם, אינו נבלע)."""
    got = ans_map(wd, prefix)
    res = {}
    missing = []
    for cid, model in cids.items():
        t = got.get('%s%s' % (prefix, cid)) if not cid.startswith(prefix) else got.get(cid)
        if t is None or not t.strip():
            res[cid] = {'ok': False, 'err': 'אין קובץ תשובה'}
            missing.append(cid)
        else:
            res[cid] = {'ok': True, 'text': t, 'model': model}
    return res, missing


def load_wd(wd):
    unit = jload(os.path.join(wd, 'unit.json'))
    work = jload(os.path.join(wd, 'work.json'))
    if not unit or not work:
        raise SystemExit('עצירה: אין unit.json / work.json בתיקייה %s (להריץ קודם write-jobs)' % wd)
    return unit, work


def save_work(wd, work):
    jdump(os.path.join(wd, 'work.json'), work)


def page_fn(unit):
    def by_dk(dk, daf=''):
        p = (unit.get('pages') or {}).get(dk)
        if p:
            return p
        return {'daf': daf, 'gemara': [], 'lines': [], 'missing': True}
    return by_dk


def log_line(wd, msg):
    with io.open(os.path.join(wd, 'gates.log'), 'a', encoding='utf-8') as f:
        f.write('[%s] %s\n' % (datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S'), msg))


def nothing():
    print('אין מה לשלוח')
    return 0


def cmd_write_jobs(unit_path, wd):
    unit = jload(unit_path)
    if not unit or 'write' not in unit:
        raise SystemExit('עצירה: קובץ יחידה לא תקין: %s' % unit_path)
    os.makedirs(wd, exist_ok=True)
    jdump(os.path.join(wd, 'unit.json'), unit)
    work = jload(os.path.join(wd, 'work.json'))
    if not work or work.get('unit') != unit['id']:
        work = {'unit': unit['id'], 'gates': VERSION, 'reqs': {}, 'recs': {}, 'cal': [], 'cal_out': [], 'engines': {}}
        for rid, r in unit['recs'].items():
            rec = dict(r)
            rec['rid'] = rid
            rec.setdefault('tries', 1)
            work['recs'][rid] = rec
        for w in unit['write']:
            meta = {'ids': w['ids'], 'dafKey': w.get('dafKey'), 'daf': w.get('daf'), 'model': w['model']}
            if w.get('cal'):
                meta['cal'] = True
            work['reqs'][w['cid']] = meta
            for i in w['ids']:
                work['recs'][i]['engine'] = w['model']
        save_work(wd, work)
    sysT = system_write()
    pre = unit.get('prewritten') or {}
    n = 0
    for w in unit['write']:
        if w['cid'] in pre:
            continue
        write_job(wd, 'job-%s.md' % w['cid'], w['model'], sysT, w['user'])
        n += 1
    log_line(wd, 'write-jobs: %d קובצי עבודה, %d מוכנים מראש' % (n, len(pre)))
    if not n:
        return nothing()
    print('נכתבו %d קובצי עבודה (job-*.md)' % n)
    return 0


def cmd_ingest_write(wd):
    unit, work = load_wd(wd)
    c = unit['cfg']
    pre = unit.get('prewritten') or {}
    cids = {w['cid']: w['model'] for w in unit['write'] if w['cid'] not in pre}
    res, missing = results_from(wd, 'job-', cids)
    for cid, p in pre.items():
        res[cid] = {'ok': bool(p.get('text')), 'text': p.get('text', ''), 'model': p.get('model', ''), 'err': 'prewritten ריק'}
    page = page_fn(unit)
    usage, stats = ingest_write_core(work, res, c, lambda meta: page(meta['dafKey'], meta.get('daf', '')))
    eng = work.setdefault('engines', {})
    eng['write'] = sorted(set(short_model(m) for cid, m in cids.items() if cid not in missing))
    if pre:
        eng['prewritten'] = sorted(set(short_model(p.get('model')) for p in pre.values()))
    work['raw'] = work.get('raw') or {}
    for cid, r in res.items():
        if r.get('ok'):
            work['raw']['w:' + cid] = r['text']
    save_work(wd, work)
    msg = 'ingest-write: %s, חסרות תשובות: %d' % (stats, len(missing))
    log_line(wd, msg + ((' (%s)' % ', '.join(missing)) if missing else ''))
    print(msg)
    for m in missing:
        print('  חסרה תשובה:', m)
    return 0


def _review_jobs(wd, prefix, model, phase):
    unit, work = load_wd(wd)
    c = unit['cfg']
    rsys = unit.get('review_system') or SYS_V2
    groups = review_groups(work, c, prefix.rstrip('-'), lambda g: rsys)
    work[phase + 'reqs'] = {cid: ids for cid, _, _, ids in groups}
    work.setdefault('engines', {})[phase] = short_model(model) if groups else None
    save_work(wd, work)
    for cid, s, u, ids in groups:
        write_job(wd, '%s.md' % cid, model, s, u)
    log_line(wd, '%s-jobs: %d קובצי עבודה' % (phase, len(groups)))
    if not groups:
        return nothing()
    print('נכתבו %d קובצי עבודה (%s*.md), מודל %s' % (len(groups), prefix, model))
    return 0


def _ingest_review(wd, prefix, phase):
    unit, work = load_wd(wd)
    c = unit['cfg']
    reqmap = work.get(phase + 'reqs') or {}
    res, missing = results_from(wd, prefix, {cid: work['engines'].get(phase) for cid in reqmap})
    ingest_review_core(work, res, c, reqmap)
    for cid, r in res.items():
        if r.get('ok'):
            work.setdefault('raw', {})[phase + ':' + cid] = r['text']
    save_work(wd, work)
    n_bad = sum(1 for r in work['recs'].values() if not r.get('cal') and r.get('rv_s'))
    msg = 'ingest-%s: %d בקשות, חסרות תשובות %d, נפסלו במבקר %d' % (phase, len(reqmap), len(missing), n_bad)
    log_line(wd, msg)
    print(msg)
    for m in missing:
        print('  חסרה תשובה:', m)
    return 0


def cmd_rewrite_jobs(wd):
    unit, work = load_wd(wd)
    c = unit['cfg']
    page = page_fn(unit)
    groups = rewrite_groups(work, c, 'rw', unit['slug'], unit['perek'], unit['masechet'], page)
    work['rwreqs'] = {cid: {'ids': ids, 'dafKey': dk} for cid, _, ids, dk in groups}
    work.setdefault('engines', {})['rewrite'] = 'fable' if groups else None
    save_work(wd, work)
    sysT = system_write()
    for cid, um, ids, dk in groups:
        write_job(wd, '%s.md' % cid, 'fable', sysT, um)
    log_line(wd, 'rewrite-jobs: %d קובצי עבודה' % len(groups))
    if not groups:
        return nothing()
    print('נכתבו %d קובצי עבודה (rw-*.md), מודל fable' % len(groups))
    return 0


def cmd_ingest_rewrite(wd):
    unit, work = load_wd(wd)
    c = unit['cfg']
    reqmap = work.get('rwreqs') or {}
    res, missing = results_from(wd, 'rw-', {cid: 'fable' for cid in reqmap})
    ingest_rewrite_core(work, res, c, reqmap, page_fn(unit))
    for cid, r in res.items():
        if r.get('ok'):
            work.setdefault('raw', {})['rw:' + cid] = r['text']
    save_work(wd, work)
    msg = 'ingest-rewrite: %d בקשות, חסרות תשובות %d' % (len(reqmap), len(missing))
    log_line(wd, msg)
    print(msg)
    for m in missing:
        print('  חסרה תשובה:', m)
    return 0


def cmd_finalize(wd, outp):
    unit, work = load_wd(wd)
    flagged = finalize_core(work)
    save_work(wd, work)
    recs = {}
    for rid, r in work['recs'].items():
        if r.get('cal'):
            continue
        recs[rid] = {'s': r.get('s'), 'a': r.get('a'), 'q_keep': r.get('q_keep', []), 'q_drop': r.get('q_drop', []),
                     'status': 'ok' if r.get('status') == 'ok' else 'לעיון המנהל', 'why': next((f['why'] for f in flagged if f['rid'] == rid), []),
                     'tries': r.get('tries', 1), 'rv_fix': bool(r.get('rv_fix')), 'star': bool(r.get('star')),
                     'engine': short_model(r.get('engine')) if r.get('tries', 1) < 2 else 'fable',
                     'dh': r.get('dh'), 'text': r.get('text')}
    cal = []
    for x in work.get('cal_out', []):
        src = (unit['recs'].get(x['key']) or {}).get('cal') or {}
        cal.append(dict(x, src=src))
    eng = {k: v for k, v in (work.get('engines') or {}).items() if v}
    out = {'id': unit['id'], 'slug': unit['slug'], 'perek': unit['perek'], 'gates': VERSION,
           'done_at': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
           'engines': eng, 'ntos': len(recs), 'flagged': len(flagged), 'recs': recs, 'cal': cal,
           'raw': work.get('raw', {})}
    # ריפוד: קובץ תוצר קטן מ-110 אלף בתים מורחב ברווחים, כדי שהקולט יוכל להוריד אותו מהדרייב ישר לדיסק (תוצאה גדולה נשמרת
    # לקובץ) ולא יצטרך להעתיק אותו ביד. הריפוד אינו נקרא ואינו משפיע על התוכן.
    size = len(json.dumps(out, ensure_ascii=False, indent=1).encode('utf-8'))
    if size < 110000:
        out['_pad'] = ' ' * (110000 - size)
    jdump(outp, out)
    msg = 'finalize: %d תוספות, %d לעיון המנהל, %d כיול -> %s' % (len(recs), len(flagged), len(cal), outp)
    log_line(wd, msg)
    print(msg)
    return 0


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 1
    cmd = argv[1]
    if cmd == 'write-jobs' and len(argv) >= 4:
        return cmd_write_jobs(argv[2], argv[3])
    if cmd == 'ingest-write':
        return cmd_ingest_write(argv[2])
    if cmd == 'review-jobs':
        return _review_jobs(argv[2], 'rv-', 'haiku', 'rv')
    if cmd == 'ingest-review':
        return _ingest_review(argv[2], 'rv-', 'rv')
    if cmd == 'rewrite-jobs':
        return cmd_rewrite_jobs(argv[2])
    if cmd == 'ingest-rewrite':
        return cmd_ingest_rewrite(argv[2])
    if cmd == 'rereview-jobs':
        return _review_jobs(argv[2], 'rr-', 'sonnet', 'rr')
    if cmd == 'ingest-rereview':
        return _ingest_review(argv[2], 'rr-', 'rr')
    if cmd == 'finalize' and len(argv) >= 4:
        return cmd_finalize(argv[2], argv[3])
    if cmd == 'version':
        print(VERSION)
        return 0
    print('פקודה לא מוכרת: %s\n%s' % (cmd, __doc__))
    return 1


if __name__ == '__main__':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    sys.exit(main(sys.argv))
