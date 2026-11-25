# -*- coding: utf-8 -*-
"""reanchor.py - עיגון מחדש של כל סימני התוס' במסכת, בעמוד הנכון ובסדר הנכון (פרומפט 96, 25.11.2026). מכני, בלי מודל.

למה: בקידושין העוגנים נקבעו בכמה סבבים (בית החרושת, פרומפטים 77 ו-92), וכל סבב תיקן רק חלק:
  - anchor_check.py העביר תוס' לעמוד השכן כשהד"ה הופיע פעמיים בעמוד הנכון (טו. נעשה יד:, נו: נעשה נו.);
  - "כלל 3" הצמיד תוס' לטקסט של התוס' שלפניו, גם כשזו רחוקה;
  - השדות daf ו-page בקובצי live-N.json התיישנו (daf="יד:" לכל פרק א), והעמוד שהאתר חיפש בו לא היה עמוד התוס'.
מה הכלי עושה, לכל פרק ולכל עמוד (העמוד נקבע תמיד מן ההפניה לספריא, לא משדה שנכתב קודם):
  1. מועמדים לכל תוס': רצפי מילים מן הד"ה שלה (הארוך ביותר קודם, מדויק ואחר כך מקורב) בטקסט הגמרא של העמוד, רק ביחידות
     של הפרק שלה. עוגן קיים (כלל 1/2) שנמצא בעמוד נשמר כמועמד מועדף.
  2. בחירה אחת לכל העמוד: הצירוף בעל הניקוד הגבוה ביותר שבו סדר הסימנים בטקסט = סדר התוס' (מספרן).
  3. תוס' בלי מקבילה: בסוף שורת הגמרא הקרובה בעמוד (לפי מספר השורה בספריא), בין התוס' שלפניה לזו שאחריה - לא ליד תוס' רחוקה (כלל 24.11).
  4. העוגן נכתב כקטע טקסט ייחודי בעמוד (מאריכים מילים עד שהוא יחיד) ונבדק בהדמיה של tosResolve שהוא נופל ביחידה שנבחרה.
כותב: anchors-N.json (t, occ, rule, why, page, daf) ו-live-N.json (t, occ, rule, why, page, daf). אינו נוגע בנוסח הדף ובסיכומים.

    uv run python tools/tosafot/dump_pages.py kiddushin                 (או: node tools/tosafot/dump_pages.js URL OUT)
    uv run python tools/tosafot/reanchor.py kiddushin --pages data/fold/pages-kiddushin.json [--write]
בלי --write: דוח בלבד.
"""
import os, sys, io, re, json, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import tos_anchor_lib as L


def load_pages(path):
    d = json.load(io.open(path, encoding='utf-8'))
    upk = {int(k): v for k, v in (d.get('upk') or {}).items()}
    return d['pages'], upk


def candidates(it, N, ids_ok, old_ok, pages=None, upk=None):
    """[(end, score, uid, ctx)] - מקומות שבהם הד"ה (או העוגן הקיים) נמצא בטקסט היחידות המותרות."""
    s, rg = N
    out = []

    def add(ctx, st, score):
        en = st + len(ctx)
        g = next((r for r in rg if r[1] <= en - 1 < r[2]), None)
        if not g or g[0] not in ids_ok or st < g[1]:
            return
        out.append((en, score, g[0], ctx))
    if old_ok:
        # העוגן הקיים, בדיוק כפי שהדפדפן פותר אותו (גם מופע שני ושלישי)
        c = L.norm_ctx(it.get('t') or '')
        r = L.resolve(it, pages, upk) if c else None
        g = next((x for x in rg if r and x[0] == r[0]), None)
        if g:
            loc = [o for o in L.occs(s[g[1]:g[2]], c)]
            if len(loc) >= r[1]:
                add(c, g[1] + loc[r[1] - 1], len(c.split()) + 2.5)
    for dh in (it.get('dh'), it.get('dhs')):
        ws = [w for w in L.norm_ctx(dh or '').split() if w not in ('מתני', 'גמ', 'גמרא', 'וכו', 'וגו')]
        if not ws:
            continue
        best = 0
        for ln in range(len(ws), 0, -1):
            if best and ln < best - 1:
                break
            for i in range(0, len(ws) - ln + 1):
                c = ' '.join(ws[i:i + ln])
                if len(c.replace(' ', '')) < (5 if ln > 1 else 4):
                    continue
                oc = L.occs(s, c)
                if ln == 1 and len(oc) > 2:
                    continue
                for o in oc:
                    add(c, o, ln + (0.6 if i == 0 else 0) + 0.3)
                if oc:
                    best = max(best, ln)
        if not best:
            # מקורב: אותו כלל כמו fzCtx בדפדפן (בלי אותיות שימוש, בלי ו/י באמצע), שתי מילים לפחות
            words = [(m.group(0), m.start(), m.end()) for m in re.finditer(r'\S+', s)]
            W = [L.fzw(w) for w, _, _ in words]
            for ln in range(len(ws), 1, -1):
                found = False
                for i in range(0, len(ws) - ln + 1):
                    q = [L.fzw(w) for w in ws[i:i + ln]]
                    for j in range(0, len(W) - ln + 1):
                        if W[j:j + ln] == q:
                            seg = s[words[j][1]:words[j + ln - 1][2]]
                            add(seg, words[j][1], ln - 0.4 + (0.6 if i == 0 else 0)); found = True
                if found:
                    break
    return out


def chain(items, cands):
    """תכנון דינמי על השרשרת לפי הסדר: מצב = המקום האחרון שנבחר. מחזיר לכל i (end, uid, ctx) או None."""
    states = {None: (0.0, [])}   # last_end -> (score, picks)
    for i in range(len(items)):
        nxt = {}
        for last, (sc, picks) in states.items():
            key = last
            v = (sc, picks + [None])
            if key not in nxt or nxt[key][0] < v[0]:
                nxt[key] = v
            for c in cands[i]:
                if last is not None and c[0] < last:
                    continue
                v = (sc + c[1], picks + [c])
                if c[0] not in nxt or nxt[c[0]][0] < v[0]:
                    nxt[c[0]] = v
        # גיזום: מצב שמקומו מאוחר יותר וניקודו נמוך אינו שימושי
        ks = sorted(nxt, key=lambda k: -1 if k is None else k)
        pr, bestsc = {}, -1
        for k in ks:
            if nxt[k][0] > bestsc:
                pr[k] = nxt[k]; bestsc = nxt[k][0]
        states = pr
    return max(states.values(), key=lambda v: v[0])[1]


def unique_ctx(text_u, end, full):
    """הקטע המסתיים ב-end בתוך טקסט היחידה, מאריכים מילים לאחור עד שהוא יחיד ב-full (טקסט כל עמודי התווית)."""
    pre = text_u[:end].rstrip()
    ws = pre.split()
    for ln in range(2, min(len(ws), 12) + 1):
        c = ' '.join(ws[-ln:])
        if len(L.occs(full, c)) == 1:
            return c
    return ' '.join(ws[-min(len(ws), 4):]) if ws else ''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('slug')
    ap.add_argument('--pages', required=True, help='דף הנתונים של האתר (pages + upk), מ-dump_pages')
    ap.add_argument('--write', action='store_true')
    ap.add_argument('--perek', default='')
    a = ap.parse_args()
    pages, upk = load_pages(a.pages)
    d = os.path.join(ROOT, 'tosafot', a.slug)
    uinfo = {}
    for q, p in enumerate(pages):
        for u in p.get('units') or []:
            uinfo[u['id']] = (q, u)
    rep = {'dh': 0, 'old': 0, 'line': 0, 'page_fixed': 0, 'fail': [], 'perakim': {}}
    for lp in sorted(f for f in os.listdir(d) if re.match(r'live-\d+\.json$', f)):
        perek = int(re.search(r'(\d+)', lp).group(1))
        if a.perek and str(perek) not in a.perek.split(','):
            continue
        LV = json.load(io.open(os.path.join(d, lp), encoding='utf-8'))
        ap_ = os.path.join(d, 'anchors-%d.json' % perek)
        A = json.load(io.open(ap_, encoding='utf-8'))
        items = LV['items']
        bypage = {}
        for it in items:
            td = L.ref_daf(it.get('ref')) or it.get('daf')
            bypage.setdefault(td, []).append(it)
        stats = {'dh': 0, 'old': 0, 'line': 0, 'fail': 0}
        for td, its in bypage.items():
            its.sort(key=lambda x: x['n'])
            qs = [q for q, p in enumerate(pages) if p.get('daf') == td]
            own = [uinfo[u['id']][1] for q in qs for u in pages[q]['units']
                   if upk.get(u['id']) == perek and u.get('k') != 'perek-range']
            if not own:
                # עמוד שאין בו טקסט מן הפרק (תוס' אחרונה של פרק על עמוד שפותח את הפרק הבא): העמוד הקרוב שיש בו
                k0 = L.dk(td)
                near = sorted({p['daf'] for p in pages if L.dk(p.get('daf')) is not None and abs(L.dk(p['daf']) - k0) <= 1
                               and any(upk.get(u['id']) == perek and u.get('k') not in L.NOTXT for u in p['units'])},
                              key=lambda x: abs(L.dk(x) - k0))
                if not near:
                    for it in its:
                        rep['fail'].append('%s %s: אין טקסט מן הפרק בעמוד ובסמוכים' % (td, it['n'])); stats['fail'] += 1
                    continue
                lab = near[0]
                qs = [q for q, p in enumerate(pages) if p.get('daf') == lab]
                own = [u for q in qs for u in pages[q]['units'] if upk.get(u['id']) == perek and u.get('k') != 'perek-range']
            else:
                lab = td
            N = L.units_norm(own)
            full = L.label_text(pages, lab)[0]
            txt = [u for u in own if u.get('k') not in L.NOTXT and (u.get('l') or [])]
            ids_ok = {u['id'] for u in txt}
            cands = []
            for it in its:
                old_ok = str(it.get('rule') or '1') in ('1', '2') and (it.get('page') or it.get('daf')) == lab
                cands.append(candidates(it, N, ids_ok, old_ok, pages, upk))
            picks = chain(its, cands)
            # מקומות נבחרים, למיקום התוס' שאין לה מקבילה בין שכנותיה
            ends = [p[0] if p else None for p in picks]
            rgmap = {r[0]: r for r in N[1]}
            for i, it in enumerate(its):
                p = picks[i]
                if p:
                    en, sc, uid, ctx = p
                    how = 'old' if sc >= len(ctx.split()) + 2.5 - 1e-9 and L.norm_ctx(it.get('t') or '') == ctx else 'dh'
                    rule, why = 1, ('פרומפט 96: העוגן הקיים נשמר (נמצא בעמוד ובסדר)' if how == 'old'
                                    else 'פרומפט 96: עוגן מן הד"ה, בעמוד %s ובסדר התוס\'' % td)
                else:
                    how = 'line'
                    prev_e = max([e for e in ends[:i] if e is not None], default=None)
                    next_e = min([e for e in ends[i + 1:] if e is not None], default=None)
                    ln = L.ref_line(it.get('ref'))
                    lined = [u for u in txt if L.unit_line(u)]
                    tgt = None
                    if lined:
                        le = [u for u in lined if L.unit_line(u) <= ln]
                        tgt = le[-1] if le else lined[0]
                    elif txt:
                        tgt = txt[min(len(txt) - 1, int(len(txt) * (ln / 40.0)))]
                    if tgt is None:
                        rep['fail'].append('%s %s: אין יחידת טקסט' % (td, it['n'])); stats['fail'] += 1; continue
                    en = rgmap[tgt['id']][2] - 1    # סוף היחידה (בלי הרווח האחרון)
                    if prev_e is not None and en < prev_e:
                        en = prev_e
                    if next_e is not None and en > next_e:
                        en = next_e
                    g = next(r for r in N[1] if r[1] <= en - 1 < r[2])
                    uid = g[0]
                    ctx = None
                    rule, why = 3, 'פרומפט 96: אין מקבילה לד"ה - סוף שורת הגמרא הקרובה בעמוד %s, בסדר התוס\'' % td
                    ends[i] = en
                # הקטע הייחודי בתוך היחידה, שמסתיים במקום הנבחר
                g = rgmap[uid]
                tu = N[0][g[1]:g[2]]
                t = unique_ctx(tu, en - g[1], full)
                if not t:
                    rep['fail'].append('%s %s: לא נמצא קטע' % (td, it['n'])); stats['fail'] += 1; continue
                occ = 1
                if len(L.occs(full, t)) > 1:
                    # לא יחיד גם אחרי הארכה: מספר המופע כמו בדפדפן - בעמוד הראשון שבתווית, ואם היחידה אינה שם -
                    # ברצף יחידות הפרק בכל עמודי התווית
                    loc = (en - g[1]) - len(t)
                    for NN in (L.first_page_norm(pages, lab),
                               L.units_norm([u for p_ in pages if p_.get('daf') == lab for u in p_['units']
                                             if upk.get(u['id']) == perek and u.get('k') != 'perek-range'])):
                        tr = next((r for r in NN[1] if r[0] == uid), None)
                        if tr:
                            oc = L.occs(NN[0], t)
                            if tr[1] + loc in oc:
                                occ = oc.index(tr[1] + loc) + 1
                            break
                new = dict(it, t=t, occ=occ, rule=rule, why=why, page=lab, daf=lab)
                r = L.resolve(new, pages, upk)
                if not r or r[0] != uid:
                    rep['fail'].append('%s %s: ההדמיה נפלה ביחידה אחרת (%s)' % (td, it['n'], r)); stats['fail'] += 1; continue
                if (it.get('page') or it.get('daf')) != lab:
                    rep['page_fixed'] += 1
                stats[how] += 1
                if a.write:
                    it.update(t=t, occ=occ, rule=rule, why=why, page=lab, daf=lab)
                    key = str(it['n'] if (a.slug == 'kiddushin' and perek == 1) else it['n'] - perek * 1000)   # מפתח הספירה (כמו make_live)
                    ak = A.get(key)
                    if isinstance(ak, dict):
                        ak.update(t=t, occ=occ, rule=rule, why=why, page=lab)
                        ak['daf'] = td    # עמוד התוס' (make_live בודק מול הספירה)
        rep['perakim'][perek] = stats
        for k in ('dh', 'old', 'line'):
            rep[k] += stats[k]
        if a.write:
            io.open(os.path.join(d, lp), 'w', encoding='utf-8', newline='\n').write(json.dumps(LV, ensure_ascii=False, indent=1) + '\n')
            io.open(ap_, 'w', encoding='utf-8', newline='\n').write(json.dumps(A, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps(rep, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
