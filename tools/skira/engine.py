# -*- coding: utf-8 -*-
"""engine.py - מנוע הסקירה: שכבות לפי משקל, בחיסכון מרבי (מנה 13.10.2026, סעיף 5).

    uv run --with lxml python tools/skira/engine.py prep   <מסכת> <מדף> <עד דף> [--depth fast|full] [--pages 10]
    uv run --with lxml python tools/skira/engine.py prep2  <מסכת> <מדף> <עד דף>
    uv run --with lxml python tools/skira/engine.py merge  <מסכת> <מדף> <עד דף> [--no-push]
    uv run python tools/skira/engine.py cost <מסכת> <מדף> <עד דף>

שכבה 0 (קוד, חינם): כל בדיקות bakara.py + הכללים החדשים. סוגים ז ו-ו נגמרים כאן ברובם.
שכבה 1 (מיון זול, haiku או sonnet): קורא לאוקמי וגמרא בלבד (בלי פירוש), מסמן פסקאות
    חשודות בסוגים א-ה. לא כותב תיקונים. קבצי הפלט: <עבודה>/triage-out/*.json.
שכבה 2 (סוקר חזק, opus): רק על הפסקאות שסומנו ועל מדגם 10% מהשאר; קורא פירוש הגמרא רק להן.
    קבצי הפלט: <עבודה>/review-out/*.json (בפורמט sem של bakara.py, עם typ).

כללי חיסכון שנאכפים כאן:
 * טביעת טקסט לכל פסקה (data/skira/reviewed-<מסכת>.json): פסקה שלא השתנתה מאז הסקירה
   האחרונה אינה נשלחת למודל.
 * פסקה נעולה (המחבר ערך אותה בשבועיים האחרונים, או שיש עליה שינוי ממתין): נסקרת רק
   בסוגים א-ב (טעות וחסר), ומסומנת "יש עליה עריכה ממתינה".
 * תקרת טוקנים להרצה (ברירת מחדל 40 אלף לדף בממוצע): חריגה צפויה עוצרת ומדווחת.
 * עיגון לפי טקסט ולא לפי אינדקס: כל ממצא נושא mark+context; אם הטקסט השתנה הוא "לא בתוקף".
"""
import os, sys, re, json, glob, random, argparse, subprocess, datetime, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import skira_common as C

TOKEN_CAP_PER_PAGE = 40000
SAMPLE = 0.10
LOCK_DAYS = 14
# הערכות לפי המדידות של 6.10.2026 (סוכה ב-ג) והקבועים: טוקנים לדף לפי עומק ושכבה
EST = {'l1_per_page': 6000, 'l1_fixed': 12000, 'l2_per_flag': 1800, 'l2_fixed': 12000, 'perush_per_page': 5000}


def tok(s):
    return max(1, len(s) // 3)          # הערכה גסה לעברית ולארמית מנוקדת


def load_blocks(slug):
    import build_all
    rev = {v: k for k, v in build_all.SLUG.items()}
    if slug not in rev:
        raise SystemExit('עצירה: מסכת לא מוכרת: ' + slug)
    from ingest_edits import docx_for
    from docx2json import convert
    docx = docx_for(rev[slug])
    return docx, convert(docx)


def perakim(blocks):
    starts = [b['i'] for b in blocks if b['style'] == 'פתיחת פרק'] or [b['i'] for b in blocks if b['style'] == 'פרק']
    return starts


def range_blocks(blocks, d_from, d_to):
    k0, k1 = C.daf_key(d_from), C.daf_key(d_to)
    if k0 is None or k1 is None or k1 < k0:
        raise SystemExit('עצירה: טווח דפים לא תקין: %s עד %s' % (d_from, d_to))
    out = []
    for b in blocks:
        k = C.daf_key(b.get('daf'))
        if k is not None and k0 <= k <= k1:
            out.append(b)
    if not out:
        raise SystemExit('עצירה: אין פסקאות בטווח %s עד %s' % (d_from, d_to))
    return out


def para_text(b):
    from styles_map import CS
    t = ''
    for r in b['runs']:
        t += ('⟦%s:%s⟧' % (CS[r['cs']], r['t'])) if r.get('cs') in CS and r['t'].strip() else r['t']
    return t.replace('\n', ' ')


def workdir(slug, d_from, d_to):
    w = os.path.join(C.WORK, '%s_%s_%s' % (slug, re.sub(r'[^א-ת]', '', d_from) + ('b' if d_from.endswith(':') else 'a'),
                                           re.sub(r'[^א-ת]', '', d_to) + ('b' if d_to.endswith(':') else 'a')))
    for sub in ('triage-out', 'review-out'):
        os.makedirs(os.path.join(w, sub), exist_ok=True)
    return w


def locked_texts(slug):
    """פסקאות נעולות: עריכות מנהל בשבועיים האחרונים (data/edits) - לפי טביעת טקסט."""
    ed = C.jload(os.path.join(C.ROOT, 'data', 'edits', slug + '.json'), {}) or {}
    lim = (time.time() - LOCK_DAYS * 86400) * 1000
    out = set()
    for e in ed.get('edits') or []:
        if (e.get('t') or 0) >= lim or not e.get('t'):
            out.add(C.thash(e.get('was', '')))
            out.add(C.thash(e.get('now', '')))
    return out


def load_cache(slug):
    return C.jload(os.path.join(C.DATA, 'reviewed-%s.json' % slug), {}) or {}


def prep(a):
    docx, blocks = load_blocks(a.slug)
    P = range_blocks(blocks, a.d_from, a.d_to)
    w = workdir(a.slug, a.d_from, a.d_to)
    cache, lock = load_cache(a.slug), locked_texts(a.slug)
    src = C.jload(os.path.join(C.ROOT, 'data', 'sources', a.slug + '.json'), {})
    tag = re.compile(r'<[^>]+>')
    items, skipped, locked = [], 0, 0
    for b in P:
        t = para_text(b)
        # שורות דובר קצרות (חלון 3: "ר"נ:") נשארות: בלעדיהן המיון חושב שדובר חסר (נמדד 14.10.2026)
        if len(C.norm(t)) < 2 or b['style'] in ('פתיחת פרק', 'פרק', 'הדרן עלך', 'הדרן'):
            continue
        h = C.thash(t)
        if h in cache and not a.force:
            skipped += 1
            continue
        lk = h in lock
        locked += lk
        items.append({'i': b['i'], 'daf': (b.get('daf') or '').strip(), 'style': b['style'], 'text': t, 'h': h, 'locked': lk})
    pages = []
    for it in items:
        if not pages or pages[-1][0] != it['daf']:
            pages.append((it['daf'], []))
        pages[-1][1].append(it)
    groups = [pages[i:i + a.pages] for i in range(0, len(pages), a.pages)]
    est1 = sum(EST['l1_fixed'] + EST['l1_per_page'] * len(g) for g in groups)
    n_pages = max(1, len({b.get('daf') for b in P}))
    meta = {'slug': a.slug, 'from': a.d_from, 'to': a.d_to, 'depth': a.depth, 'when': datetime.datetime.now().isoformat(timespec='seconds'),
            'n_paragraphs': len(items), 'skipped_unchanged': skipped, 'locked': locked, 'groups': [], 'docx': os.path.basename(docx),
            'pages': n_pages}
    for n, g in enumerate(groups):
        rng = '%s-%s' % (g[0][0], g[-1][0])
        inp = os.path.join(w, 'l1-%d.txt' % n)
        with open(inp, 'w', encoding='utf-8') as f:
            for d, its in g:
                for it in its:
                    f.write('%d | %s | %s%s | %s\n' % (it['i'], d, it['style'], ' | נעולה' if it['locked'] else '', it['text']))
        gem = os.path.join(w, 'l1-gem-%d.md' % n)
        with open(gem, 'w', encoding='utf-8') as f:
            for d, _ in g:
                pg = (src.get('pages') or {}).get(d)
                f.write('## %s\n%s\n\n' % (d, '\n'.join(tag.sub('', x) for x in pg.get('gemara', [])) if pg else '(אין במקורות)'))
        meta['groups'].append({'n': n, 'range': rng, 'input': inp, 'gemara': gem,
                               'out': os.path.join(w, 'triage-out', 'T_%d.json' % n),
                               'paragraphs': [it['i'] for _d, its in g for it in its]})
    meta['hashes'] = {str(it['i']): it['h'] for it in items}
    meta['est_tokens'] = {'layer1': est1, 'layer2_max': EST['l2_fixed'] + int(len(items) * (0.25 + SAMPLE)) * EST['l2_per_flag']}
    meta['cap'] = TOKEN_CAP_PER_PAGE * n_pages
    C.jsave(os.path.join(w, 'meta.json'), meta)
    # שכבה 0: קוד, לכל פרק שהטווח נוגע בו (קובץ ממצאים קיים עם ממצאי מודל אינו נדרס)
    starts = perakim(blocks)
    touched = set()
    for b in P:
        for k, s in enumerate(starts):
            nxt = starts[k + 1] if k + 1 < len(starts) else 10 ** 9
            if s <= b['i'] < nxt:
                touched.add(k + 1)
    meta['perakim'] = sorted(touched)
    C.jsave(os.path.join(w, 'meta.json'), meta)
    print('פסקאות לסקירה: %d · לא השתנו מאז הסקירה הקודמת (לא נשלחות): %d · נעולות: %d' % (len(items), skipped, locked))
    print('קבוצות לשכבה 1: %d · אומדן שכבה 1: %s טוקנים · תקרה להרצה: %s' % (len(groups), format(est1, ','), format(meta['cap'], ',')))
    print('פרקים שהטווח נוגע בהם:', meta['perakim'])
    if est1 > meta['cap']:
        print('אזהרה: האומדן חורג מהתקרה. עצור ודווח; המשך רק בבקשת המחבר.')
    w_task = os.path.join(w, 'tasks.md')
    with open(w_task, 'w', encoding='utf-8') as f:
        f.write('# משימות שכבה 1 (מיון) - %s %s עד %s\n\n' % (a.slug, a.d_from, a.d_to))
        f.write('לכל קבוצה סוכן אחד (haiku או sonnet), לפי `tools/skira/prompts/triage.md`. רק הקלט והגמרא, בלי פירוש.\n\n')
        for g in meta['groups']:
            f.write('- קבוצה %d (%s): קלט `%s`, גמרא `%s`, פלט `%s`\n' % (g['n'], g['range'], g['input'], g['gemara'], g['out']))
    print('נכתב:', w_task)
    return w


def prep2(a):
    w = workdir(a.slug, a.d_from, a.d_to)
    meta = C.jload(os.path.join(w, 'meta.json'))
    if not meta:
        raise SystemExit('עצירה: אין meta.json. הרץ prep קודם.')
    flagged = {}
    for fn in sorted(glob.glob(os.path.join(w, 'triage-out', '*.json'))):
        mdl = os.path.basename(fn).replace('T_', '').replace('.json', '')
        for r in C.jload_loose(fn, []):
            x = flagged.setdefault(int(r['i']), dict(r, models=[]))
            if mdl not in x['models']:
                x['models'].append(mdl)
    allp = [int(i) for g in meta['groups'] for i in g['paragraphs']]
    rnd = random.Random(a.slug + a.d_from)          # מדגם קבוע: אותה הרצה נותנת אותו מדגם
    rest = [i for i in allp if i not in flagged]
    sample = set(rnd.sample(rest, max(0, int(round(len(rest) * SAMPLE))))) if rest else set()
    pick = sorted(set(flagged) | sample)
    docx, blocks = load_blocks(a.slug)
    by_i = {b['i']: b for b in blocks}
    src = C.jload(os.path.join(C.ROOT, 'data', 'sources', a.slug + '.json'), {})
    tag = re.compile(r'<[^>]+>')
    lock = locked_texts(a.slug)
    inp = os.path.join(w, 'l2-in.txt')
    pages_needed = []
    with open(inp, 'w', encoding='utf-8') as f:
        for i in pick:
            b = by_i[i]
            t = para_text(b)
            hint = flagged.get(i, {})
            lk = C.thash(t) in lock
            f.write('%d | %s | %s | %s%s | רמז: %s | %s\n' % (
                i, (b.get('daf') or '').strip(), b['style'], 'מדגם' if i in sample and i not in flagged else 'סומנה',
                ' | נעולה (רק סוגים א-ב)' if lk else '', hint.get('why', ''), t))
            d = (b.get('daf') or '').strip()
            if d not in pages_needed:
                pages_needed.append(d)
    flagged_pages = {(by_i[i].get('daf') or '').strip() for i in flagged if i in by_i}
    gem = os.path.join(w, 'l2-src.md')
    with open(gem, 'w', encoding='utf-8') as f:
        for d in pages_needed:
            pg = (src.get('pages') or {}).get(d)
            if not pg:
                continue
            # חיסכון (14.10.2026): פירוש הגמרא רק לדפים שיש בהם פסקה שסומנה; דפי מדגם בלבד מקבלים גמרא בלבד
            per = d in flagged_pages
            f.write('## %s\n### גמרא\n%s\n\n%s' % (
                d, '\n'.join(tag.sub('', x) for x in pg.get('gemara', [])),
                ('### פירוש הגמרא\n%s\n\n' % '\n'.join(tag.sub('', x) for x in pg.get('perush', []))) if per else ''))
    # הערות פרטיות של המנהל לקלוד (ערוץ ההתכתבות הקיים) נקראות ע"י הסוקר
    notes = os.path.join(w, 'admin-notes.json')
    try:
        import _api
        C.jsave(notes, [n for n in (_api.call('/notes').get('items') or []) if n.get('slug') in ('', a.slug)])
    except BaseException as e:      # אין חיבור או אין מפתח: ממשיכים בלי, ומדווחים
        print('אזהרה: הערות המנהל לא נמשכו (%s)' % str(e)[:80])
    meta['layer2'] = {'flagged': len(flagged), 'sample': len(sample), 'paragraphs': len(pick),
                      'input': inp, 'source': gem, 'out': os.path.join(w, 'review-out', 'R_0.json'),
                      'est_tokens': EST['l2_fixed'] + EST['perush_per_page'] * len(pages_needed) + EST['l2_per_flag'] * len(pick)}
    C.jsave(os.path.join(w, 'meta.json'), meta)
    print('שכבה 2: %d פסקאות (סומנו %d + מדגם %d) · אומדן %s טוקנים' % (len(pick), len(flagged), len(sample), format(meta['layer2']['est_tokens'], ',')))
    print('קלט:', inp, '\nמקור:', gem, '\nפלט:', meta['layer2']['out'])


def merge(a):
    """איחוד: ממצאי שכבה 2 + ממצאי שכבה 0 אל data/bakara/<מסכת>-<פרק>.json, ועדכון מטמון הטביעות."""
    w = workdir(a.slug, a.d_from, a.d_to)
    meta = C.jload(os.path.join(w, 'meta.json'))
    if not meta:
        raise SystemExit('עצירה: אין meta.json.')
    outs = sorted(glob.glob(os.path.join(w, 'review-out', '*.json')))
    if not outs:
        raise SystemExit('עצירה: אין קובצי פלט של שכבה 2 ב-' + os.path.join(w, 'review-out'))
    # נרמול הפלט: kind עברי של הסוג הקבוע, ובלי מקף ארוך
    nr = 0
    for fn in outs:
        rows = C.jload_loose(fn, [])
        for r in rows:
            for k in ('note', 'fix', 'evidence', 'mark'):
                if k in r:
                    r[k] = C.no_dash(str(r[k]))
            _op = r.get('op')   # מטען להחלה (19.10.2026): ההשלמה עצמה, בלי מקף ארוך
            if isinstance(_op, dict) and isinstance(_op.get('ins'), dict) and 'text' in _op['ins']:
                _op['ins']['text'] = C.no_dash(str(_op['ins']['text']))
            if r.get('kind') not in C.SKIRA_KINDS and r.get('kind') not in ('שגיאת הבנה', 'ייחוס שגוי', 'מילה משובשת', 'חסר מהלך', 'לא מובן', 'סגנון שגוי', 'קיצור לפי #'):
                r['kind'] = 'לא מובן'
            nr += 1
        C.jsave(fn, rows)
    print('ממצאי סוקר שנקלטו:', nr)
    for pk in meta.get('perakim', []):
        sem_dir = os.path.join(C.ROOT, '_work', 'bakara', '%s-%d' % (a.slug, pk), 'sem')
        os.makedirs(sem_dir, exist_ok=True)
        for fn in outs:
            tgt = os.path.join(sem_dir, 'SK_%s_%s' % (os.path.basename(w), os.path.basename(fn)))
            with open(fn, encoding='utf-8') as s, open(tgt, 'w', encoding='utf-8') as d:
                d.write(s.read())
        # bakara.py קורא את כל sem/*.json של הפרק (כולל ישנים) ומאחד. run.py שולח אותו לנקודת הקליטה.
        cmd = [sys.executable, os.path.join(C.BAK, 'run.py'), a.slug, str(pk), '--no-sync']
        if a.no_push:
            cmd.append('--no-push')
        print('איחוד פרק', pk)
        subprocess.run(['uv', 'run', '--with', 'lxml', 'python', cmd[1]] + cmd[2:], check=True, cwd=C.ROOT)
    # מטמון טביעות: כל פסקה שנשלחה לשכבה 1 נסקרה
    cache = load_cache(a.slug)
    today = datetime.date.today().isoformat()
    for h in meta['hashes'].values():
        cache[h] = {'d': today}
    C.jsave(os.path.join(C.DATA, 'reviewed-%s.json' % a.slug), cache)
    print('טביעות שנרשמו כנסקרו:', len(meta['hashes']), '(סה"כ במטמון: %d)' % len(cache))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['prep', 'prep2', 'merge', 'cost'])
    ap.add_argument('slug')
    ap.add_argument('d_from')
    ap.add_argument('d_to')
    ap.add_argument('--depth', default='fast', choices=['fast', 'full'])
    ap.add_argument('--pages', type=int, default=10)
    ap.add_argument('--force', action='store_true', help='התעלם ממטמון הטביעות')
    ap.add_argument('--no-push', action='store_true')
    a = ap.parse_args()
    {'prep': prep, 'prep2': prep2, 'merge': merge}.get(a.cmd, lambda x: None)(a)


if __name__ == '__main__':
    main()
