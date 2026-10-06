# -*- coding: utf-8 -*-
"""bakara.py - מערכת הבקרה של לאוקמי גירסא, גרסה 0 (6.10.2026).

רץ על פרק אחד בלבד, ומחזיר ממצאים ממוינים לפי סוג. כל גלאי מוגדר בקטלוג
DETECTORS עם שכבה (קוד / מודל), חומרה, ותיאור. השכבה הסמנטית (מודל)
אינה רצה כאן: הממצאים שלה נטענים מקובצי JSON שהפיקו סוכני הבדיקה.

    python3 bakara.py <repo> <מסכת.docx> <slug> <מספר פרק> <corpus_vocab.json> <out.json> [sem/*.json ...]
"""
import sys, os, re, json, collections, glob

REPO = sys.argv[1]
sys.path.insert(0, os.path.join(REPO, 'tools'))
sys.path.insert(0, os.path.join(REPO, 'engine', 'laukmi-engine'))
from docx2json import convert
from styles_map import CS, role_of
import gemara_checks as GC
import verses_check as VC
import laukmi_rules as R
import laukmi_aramaic as AR
import hagaha as HG

HEB = 'א-ת'
NIK = re.compile(r'[֑-ׇ]')
TOK = re.compile(r'[א-ת][א-ת"\']*[א-ת\']|[א-ת]')

# ------------------------------------------------------------------ הקטלוג
# (מזהה, כותרת הסוג, שכבה, חומרה ברירת מחדל, הסבר קצר למחבר)
CATALOG = [
    ('joined',   'מילים דבוקות',            'קוד',  'חמור',  'שתי מילים שנכתבו בלי רווח ביניהן'),
    ('split',    'מילה שנחצתה',              'קוד',  'חמור',  'מילה אחת שנחצתה ברווח'),
    ('dbl',      'אות כפולה',                'קוד',  'בינוני', 'אות שנכפלה בראש מילה'),
    ('typo',     'כתיב חשוד',                'קוד',  'קל',    'מילה שאינה בשום מסכת ולא בגמרא, ורחוקה אות אחת ממילה שבגמרא של הדף'),
    ('orphan',   'אות תלושה בסוף שורה',      'קוד',  'בינוני', 'השורה נגמרת באות בודדת - כנראה נקטע משהו'),
    ('punct',    'פיסוק וסוגריים',           'קוד',  'קל',    'סוגר בלי פותח, פיסוק כפול, רווח לפני פסיק'),
    ('abbr',     'סימני קיצור',              'קוד',  'קל',    'גרש במקום גרשיים, גרש סוגר בלי פותח (מן הגלאים הקיימים)'),
    ('amor_long','סגנון אמוראים על תוכן',    'קוד',  'בינוני', 'רצף ארוך בסגנון "אמוראים" המוקטן, שאינו שם ולא מסגרת'),
    ('amor_miss','שם בלי סגנון אמוראים',     'קוד',  'קל',    'ראשי תיבות של שם שאינם בסגנון "אמוראים"'),
    ('psuk_bad', 'סגנון פסוק על מה שאינו פסוק','קוד', 'קל',    'מילים בסגנון "פסוק" שאינן נמצאות במקרא'),
    ('psuk_nik', 'פסוק לא מנוקד',           'קוד',  'קל',    'ציטוט פסוק בסגנון "פסוק" בלי ניקוד'),
    ('psuk_miss','פסוק שלא סומן',            'קוד',  'בינוני', 'ציטוט מן המקרא שאינו בסגנון "פסוק"'),
    ('nose_long','כותרת ארוכה מדי',          'קוד',  'בינוני', 'פסקת "נושא" ארוכה מ-70 תווים - כנראה גוף הסוגיה ולא כותרת'),
    ('dh_inline','ד"ה משנה בתוך שורה',       'קוד',  'קל',    'ציטוט המשנה בסגנון תו בתוך שורת גוף, ולא בפסקה משלו'),
    ('anchor',   'עוגן חלון 3',              'קוד',  'קל',    'עוגן ארוך מ-20 תווים, או שני עוגנים רצופים'),
    ('attr',     'ייחוס מול הגמרא',          'קוד',  'בינוני', 'ראשי תיבות של שם שאף פירוש שלהם אינו בגמרא של הדף'),
    ('dafpos',   'מקום ציון הדף',            'קוד',  'קל',    'ציון הדף רחוק ממקום פתיחת העמוד בגמרא'),
    ('aram',     'ארמית שנשארה',             'קוד',  'קל',    'מילה ארמית שיש לה תרגום ודאי במילון המנוע'),
    ('sem_hav',  'שגיאת הבנה',               'מודל', 'חמור',  'השורה אומרת דבר שהגמרא אינה אומרת, או הפוך'),
    ('sem_yih',  'ייחוס שגוי',               'מודל', 'חמור',  'הדברים מיוחסים לתנא או לאמורא אחר'),
    ('sem_mil',  'מילה משובשת',              'מודל', 'בינוני', 'טעות כתיב שמשנה משמעות'),
    ('sem_hsr',  'חסר מהלך',                 'מודל', 'בינוני', 'חסרה מסקנה או תירוץ, והקורא יטעה'),
    ('sem_lo',   'לא מובן',                  'מודל', 'קל',    'חסרה מילה או שתיים כדי להבין'),
    ('sem_sty',  'סגנון שגוי',               'מודל', 'קל',    'סגנון שמשנה את ההבנה (תוכן בסגנון אמוראים, גוף בסגנון נושא)'),
]
CAT = {c[0]: c for c in CATALOG}
SEMKIND = {'שגיאת הבנה': 'sem_hav', 'ייחוס שגוי': 'sem_yih', 'מילה משובשת': 'sem_mil',
           'חסר מהלך': 'sem_hsr', 'לא מובן': 'sem_lo', 'סגנון שגוי': 'sem_sty'}


def main():
    docx, slug, perek, vocab_p, out_p = sys.argv[2:7]
    sem_files = sys.argv[7:]
    perek = int(perek)
    blocks = convert(docx)
    # --- תחום הפרק: מן ה"פרק" ה-n ועד "סוף פרק" שאחריו
    starts = [b['i'] for b in blocks if b['style'] == 'פרק']
    lo = starts[perek - 1]
    hi = next((b['i'] for b in blocks if b['i'] > lo and b['style'] in ('סוף פרק', 'הדרן עלך')),
              starts[perek] if perek < len(starts) else len(blocks))
    lo = max(0, lo - 1) if perek > 1 else 0
    P = [b for b in blocks if lo <= b['i'] <= hi]
    src = json.load(open(os.path.join(REPO, 'data', 'sources', slug + '.json'), encoding='utf-8'))
    names = json.load(open(os.path.join(REPO, 'data', 'names.json'), encoding='utf-8'))['expand']
    V = json.load(open(vocab_p, encoding='utf-8'))
    cnt, nf = V['cnt'], V['nf']
    gem_all = set()
    for p in src['pages'].values():
        for g in p['gemara']:
            gem_all.update(GC.gnorm(g).split())
    common = GC.common_words()

    PFX = ('ו', 'ד', 'ש', 'ל', 'ב', 'כ', 'מ', 'ה', 'וד', 'ול', 'וב', 'וכ', 'ומ', 'וש', 'דל', 'דב', 'דמ', 'שב', 'של', 'כש', 'וכש')

    def ccount(w):
        """מספר המופעים בספר, גם בלי אותיות השימוש."""
        w = w.replace("''", '"')
        n = cnt.get(w, 0)
        for p in PFX:
            if w.startswith(p) and len(w) - len(p) >= 3:
                n = max(n, cnt.get(w[len(p):], 0))
        return n

    def known(w, strong=False):
        """מילה מוכרת: בגמרא של המסכת, או בספר עצמו."""
        if not w:
            return False
        w = w.replace("''", '"')
        g = GC.gnorm(w).replace(' ', '')
        if g in gem_all or any(x in gem_all for x in GC.strip_pfx(g)):
            return True
        return ccount(w) >= (30 if strong else 3)

    out = []

    def add(det, b, mark, note, fix='', sev=None, **kw):
        c = CAT[det]
        out.append(dict(det=det, kind=c[1], layer=c[2], sev=sev or c[3], i=b['i'],
                        daf=(b.get('daf') or '').strip(), mark=mark, note=note, fix=fix,
                        text=b['text'], context=HG.ctx_of(b['text'], mark), **kw))

    body = [b for b in P if str(role_of(b)).startswith('body') or role_of(b) in ('mishna', 'anchor', 'nose', 'dh')]

    # ---------------- א. מילים דבוקות / נחצות / אות כפולה / כתיב
    for b in body:
        toks = [(m.group(0), m.start()) for m in TOK.finditer(b['text'])]
        for k, (w, s) in enumerate(toks):
            if known(w) or len(w) < 5 or ccount(w) >= 2:
                pass
            else:
                # דבוקות: פיצול לשתי מילים מוכרות
                best = None
                for j in range(2, len(w) - 1):
                    a, c = w[:j], w[j:]
                    if a.endswith(('"',)) or c.startswith(('"', "'")):
                        continue
                    ok_a = len(a) >= 3 or '"' in a
                    ok_c = len(c) >= 3 or c in ('או', 'אף', 'לא', 'זו', 'כן')
                    def strong(x):
                        x = x.replace("''", '"')
                        return cnt.get(x, 0) >= 10 or GC.gnorm(x).replace(' ', '') in gem_all
                    def weak(x):
                        x = x.replace("''", '"')
                        return cnt.get(x, 0) >= 3 or GC.gnorm(x).replace(' ', '') in gem_all
                    longw = len(w.replace('"', '')) >= 8
                    if ok_a and ok_c and (strong(a) and strong(c)) \
                            and (cnt.get(a, 0) >= 30 or cnt.get(c, 0) >= 30):
                        sc = min(cnt.get(a, 0), cnt.get(c, 0))
                        if best is None or sc > best[0]:
                            best = (sc, a, c)
                if best:
                    add('joined', b, w, '"%s" - נראה כשתי מילים שנדבקו: "%s" ו"%s"' % (w, best[1], best[2]),
                        '%s ⟵ %s %s' % (w, best[1], best[2]))
                    continue
            # גרש באמצע מילה ואחריו אות: ר'ירמיה, כו'שאסור
            m = re.match(r"^([א-ת]{1,3})'([א-ת]{2,})$", w)
            if m and m.group(1) in ('ר', 'כו', 'וגו', 'אפי', 'ואפי', 'מתני', 'גמ') and known(m.group(2)):
                add('joined', b, w, 'חסר רווח אחרי הקיצור "%s\'"' % m.group(1),
                    "%s ⟵ %s' %s" % (w, m.group(1), m.group(2)))
                continue
            # אות כפולה בראש מילה
            if len(w) >= 3 and w[0] == w[1] and not known(w) and known(w[1:], True) and w[0] not in 'וי':
                add('dbl', b, w, 'האות "%s" נכפלה בראש "%s"' % (w[0], w), '%s ⟵ %s' % (w, w[1:]))
                continue
            # מילה שנחצתה: שתי מילים לא מוכרות שחיבורן מוכר
            if k + 1 < len(toks):
                w2, s2 = toks[k + 1]
                if (not known(w) and not known(w2) and known(w + w2, True)
                        and b['text'][s + len(w):s2] == ' ' and len(w) >= 2 and len(w2) >= 2):
                    add('split', b, w + ' ' + w2, 'נראה כמילה אחת שנחצתה: "%s"' % (w + w2),
                        '%s %s ⟵ %s' % (w, w2, w + w2))
                    continue
            # כתיב: מילה שאינה בשום מקום, ורחוקה אות ממילה בגמרא של הדף
            if len(w) >= 4 and '"' not in w and "'" not in w and cnt.get(w, 0) <= 1 and not known(w):
                win = GC.daf_window(src, b.get('daf'))
                if win:
                    r = GC.near(GC.gnorm(w), win)
                    if r:
                        add('typo', b, w, '"%s" אינה בשום מסכת ולא בגמרא; בגמרא של הדף יש "%s"' % (w, r[0]),
                            '%s ⟵ %s ?' % (w, r[0]))
        # אות בודדת בסוף שורה (לא מספור)
        t = b['text'].rstrip(' \t,.')
        m = re.search(r'(?:^|\s)([ובלמשהכד])$', t)
        if m and role_of(b) != 'anchor':
            add('orphan', b, m.group(1), 'השורה נגמרת באות "%s" בודדת - נקטע משהו?' % m.group(1),
                'להשלים או למחוק')

    # ---------------- ב. פיסוק וסוגריים
    for b in body:
        t = b['text']
        for o, c in (('[', ']'), ('(', ')')):
            if t.count(o) != t.count(c):
                add('punct', b, o if t.count(o) > t.count(c) else c,
                    'סוגר "%s%s" שאינו מאוזן בשורה' % (o, c), 'להשלים או למחוק')
        for m in re.finditer(r'[,.:]\s*[,.]|\s+,', t):
            if m.group(0).strip() in ('..', '...'):
                continue
            add('punct', b, m.group(0), 'פיסוק כפול או רווח לפני פסיק', 'לנקות')
    for r in HG._auto(P):
        bb = next(x for x in P if x['i'] == r['i'])
        add('abbr', bb, r['mark'], r['note'], r['fix'], sev='קל')

    # ---------------- ג. סגנונות תו
    am = {k for k, v in CS.items() if v == 'am'}
    ps = {k for k, v in CS.items() if v == 'ps'}
    dh = {k for k, v in CS.items() if v == 'dm'}
    FRAME = re.compile(r'^[\s◄\-–:,.]*$')
    for b in body:
        if role_of(b) not in ('body', 'body-sp', 'body-nk', 'body-hr', 'body-in', 'mishna'):
            continue
        for r in b['runs']:
            if r.get('cs') in am:
                ws = TOK.findall(r['t'])
                # שם + פועל אמירה + מסגרת: עד ארבע מילים. מעל שש - זה תוכן.
                if len(ws) >= 6:
                    add('amor_long', b, r['t'].strip()[:60],
                        '%d מילים רצופות בסגנון "אמוראים" המוקטן - זה תוכן ולא שם' % len(ws),
                        'להחזיר לסגנון רגיל, ולהשאיר בסגנון אמוראים רק את השם')
            if r.get('cs') in dh and role_of(b).startswith('body'):
                add('dh_inline', b, r['t'].strip()[:50], 'ציטוט משנה בסגנון ד"ה בתוך שורת גוף',
                    'להוציא לפסקה משלו בסגנון ד\'\'ה משנה (חוקה 8.5)')
            if r.get('cs') in ps:
                ws = [VC.skel(w) for w in TOK.findall(NIK.sub('', r['t']).replace('"', ' '))]
                ws = [w for w in ws if w]
                if len(ws) >= 2:
                    verses, bi = VC.load()
                    if not any((ws[q], ws[q + 1]) in bi for q in range(len(ws) - 1)):
                        add('psuk_bad', b, r['t'].strip()[:50],
                            'המילים בסגנון "פסוק" אינן רצף שנמצא במקרא', 'להחזיר לסגנון רגיל, אם אינו פסוק')
                    elif not NIK.search(r['t']):
                        add('psuk_nik', b, r['t'].strip()[:50], 'פסוק שאינו מנוקד (חוקה 9.1)', 'לנקד ניקוד מלא')
    # שמות בלי סגנון אמוראים
    rx = re.compile(r'(?<![א-ת"\'])((?:[ודלכמשבהוא]{0,3})?[א-ת]{0,4}ר[א-ת]{0,4}(?:"|\'\'|״)[א-ת]{1,3})(?![א-ת"\'])')
    FULL = re.compile(r'(?<![א-ת"\'])((?:[ודלכמש]{0,2})(?:אביי|רבא|רבה|רבינא|שמואל|רב\s+[א-ת]{3,}|רבי\s+[א-ת]{3,}|ר\'\s?[א-ת]{3,}))(?![א-ת"\'])')
    notn = set(R.NOT_NAME)
    for b in body:
        if not str(role_of(b)).startswith('body'):
            continue
        fl = []
        for r in b['runs']:
            fl.extend([r.get('cs') in am] * len(r['t']))
        if len(fl) != len(b['text']):
            continue
        hits = list(rx.finditer(b['text'])) + list(FULL.finditer(b['text']))
        for m in hits:
            w = m.group(1)
            wn = w.replace("''", '"')
            core = wn.lstrip('ודלכמשבהוא')
            if wn in notn or core in notn or not (core.startswith('ר') or core.startswith(('אביי', 'שמואל'))):
                continue
            if not any(fl[m.start(1):m.end(1)]):
                add('amor_miss', b, w, 'השם "%s" אינו בסגנון "אמוראים"' % w, 'להחיל סגנון אמוראים')
    # פסוקים: שלא סומנו, וסומנו בלי שהם פסוק
    try:
        VC.load()
        for i, txt, s in VC.scan_blocks(P, role_of, ps):
            bb = next(x for x in P if x['i'] == i)
            add('psuk_miss', bb, txt[s['a']:s['b']], 'ציטוט מן המקרא (%s) שאינו בסגנון "פסוק"' % s['ref'],
                'להחיל סגנון פסוק, ולנקד')
        T = VC.load()
    except Exception as e:
        print('verses:', e)

    # ---------------- ד. מבנה
    for k, b in enumerate(P):
        r = role_of(b)
        t = b['text'].strip()
        if r == 'nose' and len(t) > 70:
            add('nose_long', b, t[:40], 'כותרת "נושא" של %d תווים (עד 70 בחוקה)' % len(t),
                'לקצר לחידוש בלבד, או להחזיר לסגנון גוף')
        if r == 'anchor':
            tt = t.replace('◄', '').strip()
            if len(tt) > 20:
                add('anchor', b, tt, 'עוגן של %d תווים (עד 20)' % len(tt), 'לקצר, או להעביר את ההמשך לשורה')
            if k + 1 < len(P) and role_of(P[k + 1]) == 'anchor':
                nx = P[k + 1]['text'].strip()
                if not re.match(r'^[א-י]\.', nx.replace('◄', '').strip()):
                    add('anchor', b, tt or '◄', 'שני עוגנים רצופים בלי שורה ביניהם', 'לאחד, או למחוק את הריק')
    for r in GC.attribution(P, src, names, severity='בינוני'):
        bb = next(x for x in P if x['i'] == r['i'])
        add('attr', bb, r['mark'], r['note'], r['fix'])
    for r in GC.daf_position(P, src, tol=3, severity='קל'):
        # daf_position מחזירה את מקום הפסקה ברשימה שקיבלה, ולא את מספר הפסקה;
        # בפרק א' השניים זהים, ומפרק ב' ואילך לא (נמצא בהרצה על סוכה פרק ב)
        bb = P[r['i']]
        add('dafpos', bb, r['mark'], r['note'], r['fix'])

    # ---------------- ה. ארמית שנשארה (מקובץ לפי מילה)
    lex = {}
    for d in (getattr(AR, 'LEXICON', {}), getattr(R, 'IVRUT', {}), getattr(R, 'ARAM2', {})):
        for k_, v in d.items():
            if ' ' not in k_ and k_ not in ('עליה', 'הני', 'אמרי'):   # עברית תקינה גם כן
                lex[k_] = v
    for b in body:
        if role_of(b) == 'anchor':
            continue
        fl = []
        for r in b['runs']:
            fl.extend([r.get('cs') in am] * len(r['t']))
        for m in TOK.finditer(b['text']):
            w = m.group(0)
            base = None
            for p in ('', 'ו', 'ד', 'וד'):
                if w.startswith(p) and w[len(p):] in lex:
                    base = (p, w[len(p):]); break
            if base and len(fl) == len(b['text']) and not any(fl[m.start():m.end()]):
                add('aram', b, w, 'ארמית: "%s" (במילון המנוע: %s)' % (w, lex[base[1]]),
                    '%s ⟵ %s%s' % (w, base[0], lex[base[1]]), group=base[1])

    # ---------------- ו. השכבה הסמנטית (ממצאי הסוכנים)
    for f in sem_files:
        tag = os.path.basename(f).replace('.json', '')
        for r in json.load(open(f, encoding='utf-8')):
            bb = next((x for x in P if x['i'] == r['i']), None)
            if bb is None:
                continue
            det = SEMKIND.get(r.get('kind'), 'sem_lo')
            sev = CAT[det][3]
            if r.get('conf') == 'נמוך':
                sev = 'קל'
            note = r.get('note', '')
            if r.get('evidence'):
                note += ' · בגמרא: ' + r['evidence']
            add(det, bb, r.get('mark', ''), note, r.get('fix', ''), sev=sev, conf=r.get('conf', ''), run=tag)

    # כפילויות: אותו מקום, אותו סימון. ממצא שהקוד והמודל מצאו שניהם -
    # נשאר אחד (של המודל, שנימוקו עשיר יותר), ומסומן "נמצא בשתי השכבות".
    seen, ded = set(), []
    for f in out:
        key = (f['i'], f['mark'], f['det'])
        if key in seen:
            continue
        seen.add(key)
        ded.append(f)
    sem = [f for f in ded if f['layer'] == 'מודל']
    drop = set()
    for c in ded:
        if c['layer'] != 'קוד':
            continue
        for m in sem:
            if m['i'] == c['i'] and c['mark'] and m['mark'] and (c['mark'] in m['mark'] or m['mark'] in c['mark']):
                m['both'] = True
                drop.add(id(c))
                break
    ded = [f for f in ded if id(f) not in drop]
    loc = HG._locate(blocks)
    for f in ded:
        f['u'] = loc.get(f['i'], (0, f['i']))[1]
    for f in ded:
        f['id'] = HG.fid(slug, f['det'], f['mark'], f['context'])
    # ---------------- הלמידה מהכרעות המחבר (stats.py)
    # ממצא שהוכרע (אושר / נדחה / נערך) אינו חוזר. סוג שנדחה לרוב יורד ל"קל" ומוצג
    # מקופל; סוג שאושר כמעט תמיד נרשם כמועמד למנוע המכני (אינו עובר מעצמו).
    bdir = os.path.join(REPO, 'data', 'bakara')
    dp = os.path.join(bdir, 'decisions-%s.json' % slug)
    if os.path.exists(dp):
        decided = json.load(open(dp, encoding='utf-8'))
        before = len(ded)
        ded = [f for f in ded if f['id'] not in decided]
        print('הוכרעו בעבר ואינם חוזרים:', before - len(ded))
    stp = os.path.join(bdir, 'stats.json')
    st = json.load(open(stp, encoding='utf-8')) if os.path.exists(stp) else {}
    demoted = set(st.get('demoted') or [])
    cat = []
    for c in CATALOG:
        c = list(c)
        if c[0] in demoted:
            c[3] = 'קל'
        c.append(c[0] in demoted)          # האיבר השישי: מקופל
        cat.append(c)
    for f in ded:
        if f['det'] in demoted:
            f['sev'] = 'קל'
    json.dump({'perek': perek, 'range': [lo, hi], 'n_blocks': len(P), 'catalog': cat,
               'candidates': st.get('candidates') or [], 'findings': ded},
              open(out_p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    c = collections.Counter((f['layer'], f['kind']) for f in ded)
    for k_, v in sorted(c.items()):
        print(v, *k_)
    print('סה"כ', len(ded))


main()
