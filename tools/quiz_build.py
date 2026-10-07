# -*- coding: utf-8 -*-
"""quiz_build.py - מאגר השאלות של "בחן את עצמך" (מנה 3 מתוך 3, 7.10.2026).

קורא את הנתונים שכבר נבנו בדף כל מסכת (site/<מסכת>.html, המשתנה DATA) ומייצר
site/quiz/<מסכת>.json. שלושה סוגי שאלות נוצרים מכנית, בקוד בלבד, בלי מודל:

  w  "איפה כתוב"      - באיזה עמוד נאמר הקטע
  m  "מי אמר"         - איזה תנא (מתוך תנאי המשנה) או אמורא (מתוך כותרות הדיבור) אמר
  c  "השלם את המשנה"  - מילה חסרה בקטע משנה

סוג רביעי, d "שאלת הבנה", נוצר בידי מודל קל ונשמר ב-data/quiz/draft-<מסכת>.json
בסימון טיוטה; הוא מועתק ל-site/quiz/<מסכת>-draft.json ומוצג ללומדים רק אחרי שהמנהל אישר.

דטרמיניזם: אותה קלט נותן אותו פלט (זרע לפי מזהה השאלה), כדי שמזהי השאלות והסדר
לא ישתנו בין בניות, וההתקדמות של לומד לא תתנתק. המזהה כולל טביעה של הטקסט:
קטע שהשתנה בעריכה יוצר שאלה חדשה, ואינו מציג ללומד שאלה על נוסח ישן.
"""
import os, io, re, json, html, random, hashlib, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
NIKUD = re.compile('[֑-ׇ]')
TAG = re.compile(r'<[^>]+>')

# כמה שאלות לכל סוג בכל מסכת: מספיק לחזרה מרווחת, בלי לנפח את הקובץ
CAP = {'w': 160, 'm': 140, 'c': 120}


def plain(s):
    s = html.unescape(TAG.sub('', s or ''))
    return re.sub(r'\s+', ' ', s).strip()


def bare(s):
    return NIKUD.sub('', s)


def tid(*parts):
    return hashlib.sha1('|'.join(parts).encode('utf-8')).hexdigest()[:8]


def load_data(path):
    h = io.open(path, encoding='utf-8').read()
    i = h.find('const DATA=')
    if i < 0:
        return None
    D, _ = json.JSONDecoder().raw_decode(h[i + len('const DATA='):])
    return D


# שם תנא או אמורא בכותרת דיבור: ר"א, ר' יוחנן, רבי, רבא, אביי, שמואל, רב אשי
NAMES = {'רבא', 'אביי', 'שמואל', 'רב', 'רבי', 'עולא', 'רבה', 'רבין', 'רבינא', 'רבנן', 'רבנא', 'מרימר', 'חכמים', 'בית שמאי', 'בית הלל'}
ABBR = re.compile(r'^ר[א-ת]{0,5}"[א-ת]{1,2}$')
TWO = re.compile(r"^(ר'|רבי|רב|רבן) [א-ת]{2,10}$")
LEAD = re.compile(r'^[ולמדש]')


def norm_q(t):
    return (t.replace("’", "'").replace("׳", "'").replace("''", '"')
             .replace('״', '"').replace('”', '"'))


def person(label):
    """שם אדם נקי מכותרת דיבור, או '' אם הכותרת אינה שם (והך, א"ל, פסקה...)."""
    t = norm_q(plain(label)).strip().rstrip(':').strip()
    if not t or len(t) > 14 or ':' in t or '.' in t or '(' in t:
        return ''
    for c in (t, LEAD.sub('', t, count=1)):
        if c in NAMES or ABBR.match(c) or TWO.match(c):
            return c
    return ''


def amud_label(p):
    return p.get('daf', '')


def words_of(s):
    return [w for w in re.split(r'\s+', s) if w]


def pick_distractors(rng, pool, correct, n=3, key=lambda x: x):
    seen = {key(correct)}
    cand = []
    for x in pool:
        k = key(x)
        if k in seen:
            continue
        seen.add(k)
        cand.append(x)
    rng.shuffle(cand)
    return cand[:n]


def build_masechet(slug, D):
    pages = D['pages']
    name = D.get('masechet', slug)
    out = {'w': [], 'm': [], 'c': []}
    amudim = []
    for p in pages:
        d = amud_label(p)
        if d and d not in amudim:
            amudim.append(d)
    perek_of = {}
    for p in pages:
        perek_of.setdefault(p.get('daf'), p.get('perek', ''))

    # --- איפה כתוב ---
    cand_w = []
    for p in pages:
        d = amud_label(p)
        for u in p['units']:
            if u['k'] not in ('u', 'm'):
                continue
            lines = [plain(l[1]) for l in u.get('l', [])]
            txt = ' '.join(x for x in lines if x)
            lab = plain(u.get('a', '')).rstrip(':').strip()
            ws = words_of(txt)
            if len(ws) < 9:
                continue
            snippet = ' '.join(ws[:16]) + (' ...' if len(ws) > 16 else '')
            if lab and len(lab) < 16 and lab not in ('-', '°'):
                snippet = lab + ': ' + snippet
            cand_w.append((p, d, u, snippet))
    rng0 = random.Random('w' + slug)
    rng0.shuffle(cand_w)
    # לכל עמוד לכל היותר שאלה אחת, כדי שהכיסוי יהיה רחב
    used = set()
    for p, d, u, snippet in cand_w:
        if d in used or len(out['w']) >= CAP['w']:
            continue
        used.add(d)
        qid = 'w:%s:%s:%s' % (slug, u['id'], tid(snippet))
        rng = random.Random(qid)
        same = [x for x in amudim if x != d and perek_of.get(x) == p.get('perek')]
        other = [x for x in amudim if x != d]
        ds = pick_distractors(rng, same, d)
        if len(ds) < 3:
            ds += pick_distractors(rng, [x for x in other if x not in ds], d, 3 - len(ds))
        if len(ds) < 3:
            continue
        opts = ds[:3] + [d]
        rng.shuffle(opts)
        out['w'].append({'i': qid, 't': 'w', 'q': 'באיזה עמוד נאמר: «%s»?' % snippet,
                         'o': opts, 'a': opts.index(d), 'd': d, 'u': u['id']})

    # --- מי אמר ---
    names_pool = []
    cand_m = []
    for p in pages:
        d = amud_label(p)
        for u in p['units']:
            if u['k'] == 'u':
                nm = person(u.get('a', ''))
                lines = [plain(l[1]) for l in u.get('l', [])]
                txt = ' '.join(x for x in lines if x)
                if nm:
                    names_pool.append(nm)
                    if len(words_of(txt)) >= 6:
                        cand_m.append((d, u, nm, txt, ''))
            elif u['k'] == 'm':
                first = plain(u['l'][0][1]) if u.get('l') else ''
                ctx = ' '.join(words_of(first)[:7])
                for l in u.get('l', []):
                    m = re.search(r'<i class="tn">([^<]{1,22}?)</i>\s*(.*)$', l[1])
                    if m:
                        nm = person(plain(m.group(1)))
                        txt = plain(m.group(2))
                        if nm and len(words_of(txt)) >= 3:
                            names_pool.append(nm)
                            cand_m.append((d, u, nm, txt, ctx))
    pool_names = sorted(set(names_pool))
    rng0 = random.Random('m' + slug)
    rng0.shuffle(cand_m)
    seen_txt = set()
    for d, u, nm, txt, ctx in cand_m:
        if len(out['m']) >= CAP['m']:
            break
        key = (u['id'], nm)
        if key in seen_txt:
            continue
        seen_txt.add(key)
        qid = 'm:%s:%s:%s' % (slug, u['id'], tid(nm, txt))
        rng = random.Random(qid)
        ds = pick_distractors(rng, pool_names, nm)
        if len(ds) < 3:
            continue
        opts = ds[:3] + [nm]
        rng.shuffle(opts)
        short = ' '.join(words_of(txt)[:18]) + (' ...' if len(words_of(txt)) > 18 else '')
        q = 'מי אמר: «%s»?' % short
        if ctx:
            q = 'במשנה «%s ...» - %s' % (ctx, q)
        out['m'].append({'i': qid, 't': 'm', 'q': q, 'o': opts, 'a': opts.index(nm), 'd': d, 'u': u['id']})

    # --- השלם את המשנה ---
    mwords = []
    mcand = []
    for p in pages:
        d = amud_label(p)
        for u in p['units']:
            if u['k'] != 'm':
                continue
            txt = ' '.join(plain(l[1]) for l in u.get('l', []))
            for sent in re.split(r'(?<=[,.:;])\s+', txt):
                ws = words_of(sent)
                if 6 <= len(ws) <= 22:
                    mcand.append((d, u, sent, ws))
                for w in ws:
                    cw = re.sub(r'["\'״׳,.:;!?()\[\]\-]', '', bare(w))
                    if 4 <= len(cw) <= 9 and re.fullmatch('[א-ת]+', cw):
                        mwords.append(cw)
    mwords = sorted(set(mwords))
    rng0 = random.Random('c' + slug)
    rng0.shuffle(mcand)
    seen_u = {}
    for d, u, sent, ws in mcand:
        if len(out['c']) >= CAP['c']:
            break
        if seen_u.get(u['id'], 0) >= 2:
            continue
        idxs = []
        for k, w in enumerate(ws):
            cw = re.sub(r'["\'״׳,.:;!?()\[\]\-]', '', bare(w))
            if 4 <= len(cw) <= 9 and re.fullmatch('[א-ת]+', cw) and 0 < k < len(ws) - 1:
                idxs.append((k, cw))
        if not idxs:
            continue
        qid0 = 'c:%s:%s:%s' % (slug, u['id'], tid(sent))
        rng = random.Random(qid0)
        k, cw = idxs[rng.randrange(len(idxs))]
        close = [x for x in mwords if abs(len(x) - len(cw)) <= 1 and x != cw]
        ds = pick_distractors(rng, close, cw)
        if len(ds) < 3:
            continue
        shown = list(ws)
        shown[k] = '_____'
        opts = ds[:3] + [cw]
        rng.shuffle(opts)
        seen_u[u['id']] = seen_u.get(u['id'], 0) + 1
        out['c'].append({'i': qid0, 't': 'c', 'q': 'השלם: «%s»' % ' '.join(shown),
                         'o': opts, 'a': opts.index(cw), 'd': d, 'u': u['id']})
    qs = out['w'] + out['m'] + out['c']
    return {'slug': slug, 'name': name, 'n': len(qs), 'by': {k: len(v) for k, v in out.items()}, 'q': qs}


def clean_drafts(slug, D, raw):
    """שאלות הבנה שנוצרו במודל: בדיקה מבנית קשיחה לפני שהן נכנסות לתור האישור.
    שאלה פגומה (לא ארבע תשובות שונות, אינדקס לא תקין, יחידה שאינה קיימת) נזרקת בקול."""
    units = {u['id']: p.get('daf', '') for p in D['pages'] for u in p['units']}
    out, bad = [], 0
    for r in raw.get('q', []):
        o = r.get('o') or []
        ok = (isinstance(o, list) and len(o) == 4 and len(set(o)) == 4 and all(isinstance(x, str) and x.strip() for x in o)
              and isinstance(r.get('a'), int) and 0 <= r['a'] <= 3 and isinstance(r.get('q'), str) and len(r['q']) > 12
              and r.get('unit') in units)
        if not ok:
            bad += 1
            continue
        out.append({'i': 'd:%s:%s:%s' % (slug, r['unit'], tid(r['q'])), 't': 'd', 'q': r['q'].strip(), 'o': [x.strip() for x in o],
                    'a': r['a'], 'd': units[r['unit']] or r.get('d', ''), 'u': r['unit']})
    if bad:
        print('אזהרה: %d טיוטות של %s נפסלו במבנה' % (bad, slug))
    return out


def run(site):
    qdir = os.path.join(site, 'quiz')
    os.makedirs(qdir, exist_ok=True)
    total = 0
    summary = []
    drafts = {}
    for fn in sorted(os.listdir(site)):
        if not fn.endswith('.html'):
            continue
        slug = fn[:-5]
        p = os.path.join(site, fn)
        if os.path.getsize(p) < 200000:
            continue
        D = load_data(p)
        if not D or 'pages' not in D or not D.get('masechet'):
            continue
        res = build_masechet(slug, D)
        if not res['q']:
            print('אזהרה: למסכת %s לא נוצרה אף שאלה' % slug)
            continue
        io.open(os.path.join(qdir, slug + '.json'), 'w', encoding='utf-8').write(
            json.dumps(res, ensure_ascii=False, separators=(',', ':')))
        dr = os.path.join(ROOT, 'data', 'quiz', 'draft-%s.json' % slug)
        if os.path.exists(dr):
            dq = clean_drafts(slug, D, json.load(io.open(dr, encoding='utf-8')))
            io.open(os.path.join(qdir, slug + '-draft.json'), 'w', encoding='utf-8').write(
                json.dumps({'slug': slug, 'status': 'draft', 'q': dq}, ensure_ascii=False, separators=(',', ':')))
            drafts[slug] = len(dq)
            print('  טיוטות %s: %d שאלות הבנה (ממתינות לאישור המנהל)' % (slug, len(dq)))
        total += res['n']
        summary.append((slug, res['n'], res['by']))
    # רשימת המסכתות שיש להן שאלות: הלקוח קורא אותה כדי לדעת מה להציע
    idx = {s: n for s, n, _ in summary}
    io.open(os.path.join(qdir, 'index.json'), 'w', encoding='utf-8').write(json.dumps(idx, ensure_ascii=False))
    io.open(os.path.join(qdir, 'drafts.json'), 'w', encoding='utf-8').write(json.dumps(drafts, ensure_ascii=False))
    print('שאלות: %d מסכתות, %d שאלות מכניות' % (len(summary), total))
    return summary


if __name__ == '__main__':
    run(os.path.join(ROOT, 'site'))
