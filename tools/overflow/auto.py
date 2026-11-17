# -*- coding: utf-8 -*-
"""auto.py - "שורה שהתארכה" אוטומטית: מה שנכנס לשורה אחת נשאר כך (פרומפט 53, 17.11.2026).

מיכאל (17.11.2026): "אני לא מעוניין לאשר פיזית איחויים. זה צריך להיות אוטומטית. אם זה נכנס - שיישאר כך."

שלושה חלקים:

א. נעילה אוטומטית (lock): כל פסקה שבהדפסה המוגדלת (a4-large, בסיס B5 מוגדל) ובהדפסה הרגילה (a4) תופסת שורה
   אחת נרשמת במרשם data/overflow/keep/<מסכת>.auto.json לפי נוסחה (אותיות וספרות בלבד, כמו keep.norm).
   המזהה הוא הנוסח עצמו ולא מקום (u<יחידה>.<שורה>), כדי שבנייה מחדש, פיצול או הזזה לא ינתקו אותו.
   - נוסח נעול שקיים בדף ותופס יותר משורה = שבירה. הבודק (check) עוצר את ההפקה (render_pdf.py, קוד 3).
   - נוסח נעול שאינו עוד בדף = נערך (עריכה של מיכאל גוברת תמיד). יוצא מן המרשם ונרשם ב-released,
     והנוסח החדש ננעל אם הוא בשורה אחת. מיכאל אינו מאשר ואינו מנקה דבר.
   - קבלת הצעת "סכם" שנכתבה על נוסח ישן נחסמת בדף (sakem_ui.js, skmApply) בשורות שבמרשם.

ב. החלה אוטומטית (pick): מן הקובץ של המחולל (data/overflow/<מסכת>.json, הצעות שכבר נבדקו במנוע בשני הגדלים)
   נבחרת לכל שורה גולשת שהייתה שורה אחת ב-a4 ההצעה הקטנה ביותר שמספיקה:
     כלי 2 - ראשי תיבות מן הרשימה (צורה שמיכאל עצמו כתב 5 פעמים ומעלה) או רווח מיותר; שורה אחת בשני הגדלים.
     כלי 4 - חיתוך לשתי שורות במקום טבעי, בלי שינוי מילה; כל חלק בשורה אחת בשני הגדלים.
     כלי 3 - רק שינוי מזערי של מילה אחת (החלפה, השמטה, קיצור), בלי פסוק, מירכאות, שמות, מספרים והפניות.
   שורה שמיכאל השאיר (הכרעת "השאר") או שביטל ביומן - אינה מוחלת. ניסוח רחב וכלי 5 נשארים הצעה בסימון הקיים.
   הרשומות נבנות בדיוק כמו בעורך (תיקון טקסט / פיצול), ונשלחות לשכבה החיה (PUT /edits) - משם /live והקיפול הלילי.

ג. היומן (data/overflow/auto/<מסכת>.json): לכל החלה - דף, לפני, אחרי, כלי, מפתח הרשומה. "בטל" בדף מחזיר את הנוסח
   ונרשם בשרת (bakara/dec, ov-<מסכת>, d='undo'); learn.py מושך אותו, ו-pick לא יחיל שוב.

    python tools/overflow/auto.py pick  --slug berakhot --gen data/overflow/berakhot.json --site <מראה> [--apply-file x.json]
    python tools/overflow/auto.py lock  --slug berakhot --large <דוח a4-large> --a4 <דוח a4>
    python tools/overflow/auto.py check --slug berakhot --report <דוח עם --lines>
    python tools/overflow/auto.py push  --slug berakhot            (צריך LEOKMEI_ADMIN_KEY)
"""
import argparse, hashlib, html as H, io, json, os, re, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
ODIR = os.path.join(ROOT, 'data', 'overflow')
sys.path.insert(0, HERE)
import keep as KEEP  # noqa: E402

BY = 'איחוי אוטומטי (פרומפט 53)'
NIK = re.compile(r'[֑-ׇ⁠]')


def now_s():
    return time.strftime('%Y-%m-%d %H:%M', time.localtime())


def h16(s):
    return hashlib.sha1(s.encode('utf-8')).hexdigest()[:16]


def jload(fp, dflt):
    return json.load(io.open(fp, encoding='utf-8')) if os.path.exists(fp) else dflt


def jsave(fp, doc):
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    io.open(fp, 'w', encoding='utf-8', newline='\n').write(json.dumps(doc, ensure_ascii=False, indent=1) + '\n')


def plain(h):
    return H.unescape(re.sub(r'<[^>]+>', '', h or ''))


def words(h):
    return NIK.sub('', plain(h)).replace(' ', ' ').split()


def lock_fp(slug):
    return os.path.join(ODIR, 'keep', slug + '.auto.json')


def log_fp(slug):
    return os.path.join(ODIR, 'auto', slug + '.json')


# ---------------- א. נעילה ----------------
def lock(slug, large, a4):
    """מעדכן את המרשם האוטומטי מתוך שני דוחות המנוע (עם --lines). מחזיר 0, או 1 אם נמצאה שבירה של שורה נעולה"""
    L = jload(large, {}).get('plines') or []
    A = jload(a4, {}).get('plines') or []
    if not L or not A:
        sys.exit('עצירה: בדוחות אין plines (צריך להריץ את המנוע עם --lines)')
    nA = {}
    for p in A:
        k = KEEP.norm(p.get('text'))
        nA[k] = max(nA.get(k, 0), p.get('n') or 0)
    cur = {}
    for p in L:
        k = KEEP.norm(p.get('text'))
        if not k:
            continue
        c = cur.setdefault(k, {'n': 0, 'daf': p.get('daf') or ''})
        c['n'] = max(c['n'], p.get('n') or 0)
    fp = lock_fp(slug)
    doc = jload(fp, {'slug': slug, 'items': {}, 'released': []})
    items = doc.setdefault('items', {})
    rel = doc.setdefault('released', [])
    t = now_s()
    broken, added, gone = [], 0, 0
    for h, it in list(items.items()):
        k = it.get('k') or ''
        c = cur.get(k)
        if c is None:
            # הנוסח אינו עוד בדף: נערך. עריכה גוברת - יוצא מן המרשם, ונרשם
            rel.append({'k': k[:80], 'daf': it.get('daf'), 'since': it.get('since'), 'out': t, 'why': 'הנוסח נערך'})
            del items[h]
            gone += 1
        elif c['n'] > 1 or nA.get(k, 1) > 1:
            broken.append((it.get('daf'), it.get('s') or k[:40], c['n']))
    for k, c in cur.items():
        if c['n'] == 1 and nA.get(k) == 1:
            h = h16(k)
            if h not in items:
                items[h] = {'k': k, 'daf': c['daf'], 'since': t}
                added += 1
    doc['made'] = t
    doc['count'] = len(items)
    doc['released'] = rel[-400:]
    jsave(fp, doc)
    print('נעילה אוטומטית (%s): %d שורות נעולות, נוספו %d, יצאו (נערכו) %d, נשברו %d' % (slug, len(items), added, gone, len(broken)))
    for d, s, n in broken[:30]:
        print('  X %s | %s | %d שורות' % (d, s, n))
    return 1 if broken else 0


def check(slug, report, partial=False):
    """הבודק: כל שורה נעולה שמופיעה בדוח - בשורה אחת. שורה שאינה בדוח (נערכה, או מחוץ לטווח) אינה תקלה"""
    doc = jload(lock_fp(slug), None)
    if not doc or not doc.get('items'):
        return 0
    pl = jload(report, {}).get('plines') or []
    if not pl:
        print('עצירה: בדוח אין plines (צריך להריץ את המנוע עם --lines)')
        return 1
    n = {}
    for p in pl:
        k = KEEP.norm(p.get('text'))
        n[k] = max(n.get(k, 0), p.get('n') or 0)
    bad = [(it.get('daf'), it['k'][:40], n[it['k']]) for it in doc['items'].values() if n.get(it['k'], 1) > 1]
    print('נעילה אוטומטית - בדיקה (%s): %d נעולות, %d נשברו' % (slug, len(doc['items']), len(bad)))
    for d, s, m in bad[:30]:
        print('  X %s | %s | %d שורות' % (d, s, m))
    return 1 if bad else 0


# ---------------- ב. בחירה והחלה ----------------
NAME_PRE = ('ר\'', 'רבי', 'רב', 'בן', 'בר', 'בית', 'רבן', 'מר', 'ורבי', 'ור\'', 'ורב', 'אבי', 'בני')


def minimal3(it, s):
    """כלי 3 מוחל אוטומטית רק בשינוי של מילה אחת, שאינו נוגע בפסוק, במירכאות, בשמות, במספרים ובהפניות"""
    if s.get('kind') != 'replace':
        return False, 'אינו החלפת נוסח'
    if re.search(r'<i class="ps"|<sup', s.get('html', '')) and plain(s['html']).count('"') != plain(it['html']).count('"'):
        return False, 'נוגע בפסוק או בהפניה'
    A, B = words(it['html']), words(s['html'])
    i = 0
    while i < min(len(A), len(B)) and A[i] == B[i]:
        i += 1
    j = 0
    while j < min(len(A), len(B)) - i and A[-1 - j] == B[-1 - j]:
        j += 1
    da, db = A[i:len(A) - j], B[i:len(B) - j]
    if len(da) != 1 or len(db) > 1:
        return False, 'יותר ממילה אחת (%d -> %d)' % (len(da), len(db))
    w = da[0]
    if re.search(r'["\'״׳0-9()\[\]]', w + ''.join(db)):
        return False, 'מירכאות, ראשי תיבות, מספר או סוגריים'
    if db and len(db[0]) >= len(w):
        return False, 'אינו קיצור'
    prev = A[i - 1] if i else ''
    if prev in NAME_PRE or w in NAME_PRE:
        return False, 'שם'
    # המילה אינה בתוך פסוק (<i class="ps">) - כאן נבדק על ה-HTML המקורי
    for m in re.finditer(r'<i class="ps">(.*?)</i>', it['html']):
        if w in NIK.sub('', plain(m.group(1))).split():
            return False, 'בתוך פסוק'
    return True, '%s -> %s' % (w, db[0] if db else '(הושמט)')


def choose(it, skip_ids):
    """הקטן ביותר שמספיק. מחזיר (הצעה, סיבה) או (None, סיבה)"""
    if it.get('head'):
        return None, 'כותרת: נשארת הצעה'
    if it.get('nA4') != 1 and not it.get('tail'):
        return None, 'פסקה ארוכה (יותר משורה ב-A4)'
    if it['id'] in skip_ids:
        return None, 'מיכאל השאיר או ביטל'
    sug = it.get('sug') or []
    one = lambda s: s.get('ok') and all(n == 1 for n in s['ok'].get('large', [])) and all(n == 1 for n in s['ok'].get('a4', []))
    if it.get('tail'):
        # זנב קצר (17.11.2026): חוסכת שורה בגודל הרגיל, ורק כלי 2 או שינוי מזערי של כלי 3
        one = lambda s: s.get('ok') and s['ok'].get('large', [99])[0] <= it['nLarge'] - 1 and s['ok'].get('a4', [99])[0] <= it['nA4']
    t2 = [s for s in sug if s['tool'] == 2 and s.get('kind') == 'replace' and one(s)]
    t2 = sorted(t2, key=lambda s: (s.get('type') == 'multi', len(plain(s['html']))), reverse=False)
    if t2:
        return t2[0], 'כלי 2'
    t4 = [s for s in sug if s['tool'] == 4 and s.get('kind') == 'split' and len(s.get('parts') or []) == 2 and one(s) and not s.get('side')]
    if t4:
        return t4[0], 'כלי 4'
    for s in sug:
        if s['tool'] == 3 and one(s):
            ok, why = minimal3(it, s)
            if ok:
                s = dict(s, why3=why)
                return s, 'כלי 3'
    return None, 'אין הצעה שעומדת בכללים'


def skip_ids(slug):
    """שורות שמיכאל השאיר (no) או שביטל ביומן (undo), מקובץ ההכרעות ומן היומן"""
    out = set()
    dp = os.path.join(ODIR, 'decisions', slug + '.json')
    for d in jload(dp, {}).get('items') or []:
        if d.get('d') in ('no', 'undo'):
            out.add(d.get('id'))
    for e in jload(log_fp(slug), {}).get('log') or []:
        if e.get('undone'):
            out.add(e.get('id'))
    return out


def site_data(site, slug):
    txt = io.open(os.path.join(site, slug + '.data.js'), encoding='utf-8').read()
    D = json.loads(txt[txt.index('{'):txt.rindex('}') + 1])
    pcls = [x[0] for x in ((D.get('sty') or {}).get('p') or []) if x and x[0]]
    lines, order = {}, []
    for pg in D.get('pages', []):
        for u in pg.get('units', []):
            for li, l in enumerate(u.get('l') or [], 1):
                lines[(u['id'], li)] = l
                order.append((u['id'], li))
    return lines, order, pcls


def domh(h):
    """ה-HTML כפי שהעורך כותב אותו (innerHTML של הדפדפן): גרש ומירכאות בטקסט כתווים ולא כישויות"""
    return (h or '').replace('&#x27;', "'").replace('&#39;', "'").replace('&quot;', '"')


def records(it, s, lines, order, pcls, t):
    """הרשומות כמו בעורך: תיקון טקסט (k=u<יחידה>.<שורה>) או פיצול (op=struct, kind=split)"""
    key = (it['u'], it['li'])
    cur = lines.get(key)
    if not cur:
        raise ValueError('השורה אינה בנתונים: ' + it['key'])
    if KEEP.norm(cur[1]) != KEEP.norm(it['html']):
        raise ValueError('הנוסח השתנה מאז המחולל: ' + it['key'])
    cls = cur[0]
    wasP = ' '.join(c for c in str(cls or '').split() if c in pcls)
    if s['kind'] == 'split':
        p1, p2 = domh(s['parts'][0]), domh(s['parts'][1])
        return [{'op': 'struct', 'kind': 'split', 'texts': [plain(cur[1])], 'res': [[cls, p1], [cls, p2]],
                 'resT': [plain(p1), plain(p2)], 'daf': it.get('daf') or '', 't': t, 'by': BY}]
    ix = order.index(key)
    b = plain(lines[order[ix - 1]][1])[-40:] if ix > 0 else ''
    a = plain(lines[order[ix + 1]][1])[:40] if ix + 1 < len(order) else ''
    return [{'k': it['key'], 'was': plain(cur[1]), 'now': plain(s['html']), 'wasH': cur[1], 'nowH': domh(s['html']),
             'wasP': wasP, 'daf': it.get('daf') or '', 'ctx': {'b': b, 'a': a}, 't': t, 'by': BY}]


def pick(slug, gen, site, apply_file):
    G = jload(gen, None)
    if not G:
        sys.exit('עצירה: אין קובץ מחולל ' + gen)
    lines, order, pcls = site_data(site, slug)
    sk = skip_ids(slug)
    lg = jload(log_fp(slug), {'slug': slug, 'log': [], 'pending': []})
    done = {e['id'] for e in lg.get('log') or [] if not e.get('undone')}
    t = int(time.time() * 1000)
    chosen, why, apply_items, units = [], {}, [], set()
    for it in G.get('items') or []:
        if it['id'] in done:
            why['כבר הוחל'] = why.get('כבר הוחל', 0) + 1
            continue
        s, r = choose(it, sk)
        if s and it['u'] in units:
            # שינוי אחד ליחידה בכל סבב: פיצול מזיז את מספרי השורות שאחריו. השאר בסבב הבא
            s, r = None, 'יחידה שכבר שונתה בסבב הזה (בסבב הבא)'
        if not s:
            why[r] = why.get(r, 0) + 1
            continue
        try:
            recs = records(it, s, lines, order, pcls, t)
        except ValueError as e:
            why[str(e).split(':')[0]] = why.get(str(e).split(':')[0], 0) + 1
            continue
        t += 1 + len(recs)
        units.add(it['u'])
        tool = 'כלי %d' % s['tool']
        after = ' / '.join(plain(x) for x in s['parts']) if s['kind'] == 'split' else plain(s['html'])
        chosen.append({'id': it['id'], 'key': it['key'], 'daf': it.get('daf') or '', 'tool': s['tool'], 'toolName': tool,
                       'why': s.get('why3') or s.get('why') or '', 'before': plain(it['html']), 'after': after,
                       'kind': s['kind'], 'beforeH': it['html'],
                       'afterH': [domh(x) for x in s['parts']] if s['kind'] == 'split' else domh(s['html']), 'cls': lines[(it['u'], it['li'])][0],
                       'recs': recs, 'at': now_s()})
        apply_items.append(dict(it, sug=[s]))
    if apply_file:
        jsave(apply_file, {'items': apply_items})
    print('החלה אוטומטית (%s): %d שורות נבחרו %s' % (slug, len(chosen), {k: sum(1 for c in chosen if c['tool'] == k) for k in (2, 3, 4)}))
    for k, v in sorted(why.items(), key=lambda x: -x[1]):
        print('  לא הוחל: %s - %d' % (k, v))
    return chosen


def commit(slug, chosen):
    """היומן: כל החלה נכנסת ל-log, והרשומות ל-pending (נשלחות ב-push)"""
    fp = log_fp(slug)
    lg = jload(fp, {'slug': slug, 'log': [], 'pending': []})
    for c in chosen:
        lg['log'].append({k: v for k, v in c.items() if k != 'recs'} | {'recK': [r.get('k') or 's%d' % r['t'] for r in c['recs']]})
        lg['pending'].extend(c['recs'])
    lg['made'] = now_s()
    lg['count'] = sum(1 for e in lg['log'] if not e.get('undone'))
    jsave(fp, lg)
    # מה שהוחל נבדק במנוע בשני הגדלים (שורה אחת) - ננעל מיד, בלי לחכות לסבב הבא
    lp = lock_fp(slug)
    ld = jload(lp, {'slug': slug, 'items': {}, 'released': []})
    for c in chosen:
        for part in (c['afterH'] if c['kind'] == 'split' else [c['afterH']]):
            k = KEEP.norm(part)
            if k and h16(k) not in ld['items']:
                ld['items'][h16(k)] = {'k': k, 'daf': c['daf'], 'since': now_s(), 'src': 'auto'}
    ld['count'] = len(ld['items'])
    jsave(lp, ld)
    print('נרשמו ביומן %d החלות, %d רשומות ממתינות לשליחה' % (len(chosen), len(lg['pending'])))


def push(slug):
    fp = log_fp(slug)
    lg = jload(fp, None)
    if not lg or not lg.get('pending'):
        print('אין רשומות ממתינות (%s)' % slug)
        return 0
    eds = lg['pending']
    d = KEEP.call('PUT', '/edits', {'slug': slug, 'edits': eds})
    got = {(e.get('k'), e.get('t')) for e in ((d.get('doc') or {}).get('edits') or [])}
    kk = lambda e: e.get('k') or ('s%d' % e['t'])
    miss = [e for e in eds if (kk(e), e.get('t')) not in got]
    print('%s: נשלחו %d, בשרת %d מהן' % (slug, len(eds), len(eds) - len(miss)))
    if miss:
        for e in miss[:10]:
            print('  חסרה: %s %s' % (kk(e), e.get('daf')))
        return 1
    lg['pending'] = []
    lg['pushed'] = now_s()
    jsave(fp, lg)
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['pick', 'lock', 'check', 'push'])
    ap.add_argument('--slug', default='berakhot')
    ap.add_argument('--gen', default='')
    ap.add_argument('--site', default='')
    ap.add_argument('--apply-file', default='')
    ap.add_argument('--commit', action='store_true', help='pick: לרשום ביומן ולהכין לשליחה')
    ap.add_argument('--large', default='')
    ap.add_argument('--a4', default='')
    ap.add_argument('--report', default='')
    ap.add_argument('--partial', action='store_true')
    a = ap.parse_args()
    if a.cmd == 'pick':
        ch = pick(a.slug, a.gen or os.path.join(ODIR, a.slug + '.json'), a.site, a.apply_file)
        if a.commit:
            commit(a.slug, ch)
        return 0
    if a.cmd == 'lock':
        return lock(a.slug, a.large, a.a4)
    if a.cmd == 'check':
        return check(a.slug, a.report, a.partial)
    return push(a.slug)


if __name__ == '__main__':
    sys.exit(main())
