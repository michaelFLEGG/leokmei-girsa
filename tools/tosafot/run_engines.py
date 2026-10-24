# -*- coding: utf-8 -*-
"""run_engines.py - מריץ את מנועי "תוספות בשורה אחת" על טווח עמודים, ובונה את קובץ המבחן העיוור.

כל מנוע מקבל בדיוק את אותה הנחיה קבועה (tosafot/תוס-פרומפט-שורה-אחת.md) ואת אותה בקשה: בקשה אחת לכל עמוד גמרא, עם כל
התוספות של העמוד, שורת הלאוקמי שבה כל אחד מעוגן וקטע הגמרא שעליו הוא נסוב. קריאה ישירה וחד-פעמית (llm.py): בלי כלים,
בלי גישה לריפו ובלי הקשר שיחה. ההגדרות (מנועים, טווח, מצב) ב-tosafot/run-config-*.json: שינוי הגדרה בלבד מעביר ל-Batch API
(mode=batch מכין קובץ בקשות בפורמט ה-Batch ואינו שולח דבר) ולמסכת אחרת.

    uv run python tools/tosafot/run_engines.py tosafot/run-config-sukkah-test.json run       # כתיבה (חמשת המנועים)
    uv run python tools/tosafot/run_engines.py tosafot/run-config-sukkah-test.json review    # המבקר
    uv run python tools/tosafot/run_engines.py tosafot/run-config-sukkah-test.json pack      # קובץ המבחן העיוור

תוצרים בתיקיית tosafot/<מסכת>/engines/: <מנוע>--<עמוד>.json (פלט גולמי + ספירת טוקנים), review--<עמוד>.json (המבקר).
"""
import os, sys, re, json, io, random, concurrent.futures as cf
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import llm
from make_anchors import norm_idx, norm_ctx, find_occ
ROOT = os.path.dirname(os.path.dirname(HERE))
NIK = re.compile('[֑-ׇ]')
BATCH_DISCOUNT = 0.5


def jload(p):
    return json.load(io.open(p, encoding='utf-8'))


def jdump(p, o):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with io.open(p, 'w', encoding='utf-8') as f:
        json.dump(o, f, ensure_ascii=False, indent=1)


def collect(cfg):
    """[(slug, dafKey, [tosafot...])] לפי ה-scope. tosafot = שורות הספירה, עם הפרק והעוגן."""
    pages = {}
    for sc in cfg['scope']:
        d = os.path.join(ROOT, 'tosafot', sc['slug'])
        count = jload(os.path.join(d, 'count-%d.json' % sc['perek']))
        anchors = jload(os.path.join(d, 'anchors-%d.json' % sc['perek']))
        ctx = jload(os.path.join(d, 'context.json'))
        for r in count['items']:
            if r['daf'] not in sc['dafs']:
                continue
            a = anchors.get(str(r['n']))
            if not a:
                raise SystemExit('עצירה: אין עוגן לתוספות %s/%d' % (sc['slug'], r['n']))
            row = dict(r)
            row['slug'] = sc['slug']
            row['examplesFrom'] = sc.get('examplesFrom')
            row['perek'] = sc['perek']
            row['id'] = '%d-%d' % (sc['perek'], r['n'])
            row['anchor'] = a
            c = ctx[r['dafKey']]
            idx_c = norm_ctx(a['t'])
            line_txt = ''
            for ln in c['lines']:
                if find_occ(norm_idx([ln]), idx_c):
                    line_txt = ln
                    break
            row['laukmi'] = line_txt
            row['gemara'] = NIK.sub('', c['gemara'][r['line'] - 1]) if 0 < r['line'] <= len(c['gemara']) else ''
            pages.setdefault((sc['slug'], r['daf']), []).append(row)
    # המפתח הוא ציון הדף הלטיני (14b), כדי ששמות הקבצים יהיו חוקיים בכל מערכת (בלי נקודתיים)
    return [(k[0], k[1], sorted(v, key=lambda x: (x['perek'], x['n']))) for k, v in sorted(pages.items())]


def system_text(base, tos):
    """ההנחיה הקבועה. חריג יחיד: כשהעמוד הנבדק הוא עצמו מקור הדוגמאות (קידושין יד:), הדוגמאות מוחלפות באחרות מאותה מסכת,
    אחרת המנועים מעתיקים את בחירות המנהל מילה במילה (נמדד ב-12.10.2026: פייבל ואופוס החזירו את הדוגמאות כלשונן)."""
    ex = tos[0].get('examplesFrom')
    if not ex:
        return base
    slug, perek = tos[0]['slug'], tos[0]['perek']
    d = os.path.join(ROOT, 'tosafot', slug)
    cnt = {r['n']: r for r in jload(os.path.join(d, 'count-%d.json' % perek))['items']}
    st = jload(os.path.join(d, 'styles-%d.json' % perek))
    blocks = ['פנים התוספות: "%s"\nשורה: %s' % (cnt[n]['text'], st[str(n)]['a']) for n in ex]
    i, j = base.index('## דוגמאות'), base.index('## מבנה הבקשה')
    return base[:i] + '## דוגמאות (פנים התוספות המלא, והשורה הרצויה)\n\n' + '\n\n'.join(blocks) + '\n\n' + base[j:]


def user_msg(daf, tos):
    parts = ['עמוד %s. להלן התוספות שבעמוד.' % tos[0]['dafKey']]
    for r in tos:
        parts.append('### מזהה: %s\nשורת הלאוקמי גירסא שבה התוספות מעוגן: %s\nקטע הגמרא שעליו הוא נסוב: %s\nפנים התוספות:\n%s'
                     % (r['id'], r['laukmi'] or '(לא נמצאה)', r['gemara'], r['text']))
    parts.append('כתוב שורה אחת לכל תוספות, בפורמט שבהנחיה (JSON בלבד).')
    return '\n\n'.join(parts)


def parse_json(t):
    t = t.strip()
    t = re.sub(r'^```(?:json)?\s*|\s*```$', '', t).strip()
    return json.loads(t)


def usage_log_path():
    return os.path.join(ROOT, 'tosafot', 'engines-usage.json')


def spent():
    p = usage_log_path()
    return jload(p) if os.path.exists(p) else {'total': 0, 'calls': []}


def record(u, kind, engine, slug, daf, j):
    n = j['in'] + j['out']
    u['total'] += n
    u['calls'].append({'kind': kind, 'engine': engine, 'slug': slug, 'daf': daf, 'in': j['in'], 'out': j['out'],
                       'think': j['think'], 'ms': j['ms'], 'cost': j['cost']})
    jdump(usage_log_path(), u)


def do_run(cfg):
    system = io.open(os.path.join(ROOT, cfg['prompt']), encoding='utf-8').read()
    eprompt = {e['id']: io.open(os.path.join(ROOT, e.get('prompt', cfg['prompt'])), encoding='utf-8').read() for e in cfg['engines']}
    pages = collect(cfg)
    if cfg.get('mode') == 'batch':
        out = []
        for slug, daf, tos in pages:
            for e in cfg['engines']:
                out.append({'custom_id': '%s--%s--%s' % (e['id'], slug, daf), 'params': {
                    'model': e['model'], 'max_tokens': 4000,
                    'system': [{'type': 'text', 'text': system_text(eprompt[e['id']], tos), 'cache_control': {'type': 'ephemeral'}}],
                    'messages': [{'role': 'user', 'content': user_msg(daf, tos)}]}})
        p = os.path.join(ROOT, 'tosafot', 'batch-requests.jsonl')
        with io.open(p, 'w', encoding='utf-8') as f:
            for o in out:
                f.write(json.dumps(o, ensure_ascii=False) + '\n')
        print('הוכן קובץ בקשות ל-Batch API (לא נשלח):', p, len(out), 'בקשות')
        return
    u = spent()
    jobs = []
    for slug, daf, tos in pages:
        for e in cfg['engines']:
            fp = os.path.join(ROOT, 'tosafot', slug, 'engines', '%s--%s.json' % (e['id'], daf))
            if os.path.exists(fp) and not os.environ.get('RERUN'):
                continue
            jobs.append((slug, daf, tos, e, fp))
    print('קריאות לביצוע:', len(jobs))

    def one(job):
        slug, daf, tos, e, fp = job
        if u['total'] > cfg['budgetTokens']:
            raise SystemExit('עצירה: עברנו את תקציב הטוקנים (%d)' % cfg['budgetTokens'])
        want = [r['id'] for r in tos]
        tries = []
        for attempt in (1, 2):
            j = llm.call(e['model'], system_text(eprompt[e['id']], tos), user_msg(daf, tos), thinking=e['thinking'], effort=e.get('effort'))
            tries.append({k: j[k] for k in ('in', 'out', 'think', 'ms', 'cost')})
            try:
                got = parse_json(j['text'])
                miss = [i for i in want if i not in got or not str(got[i]).strip()]
                if not miss:
                    break
            except Exception as ex:
                got, miss = None, want
        else:
            raise SystemExit('עצירה: המנוע %s לא החזיר פלט תקין לעמוד %s: %s' % (e['id'], daf, j['text'][:200]))
        res = {'engine': e['id'], 'model': e['model'], 'thinkingBudget': e['thinking'], 'daf': daf, 'slug': slug,
               'tries': tries, 'ntos': len(tos), 'out': {i: str(got[i]).strip() for i in want}}
        jdump(fp, res)
        return slug, daf, e['id'], tries

    with cf.ThreadPoolExecutor(4) as ex:
        for slug, daf, eid, tries in ex.map(one, jobs):
            for t in tries:
                record(u, 'write', eid, slug, daf, t)
            print(slug, daf, eid, 'טוקנים:', sum(t['in'] + t['out'] for t in tries), 'חשיבה:', sum(t['think'] for t in tries))
    print('סך הצריכה המצטבר:', spent()['total'])


REVIEW_SYS = ('אתה מבקר זהיר של הערות שוליים על תוספות. לכל תוספות יינתנו פנים התוספות המלא וכמה אופציות שורה-אחת. '
              'בדוק כל אופציה בנפרד מול הפנים בלבד, וסמן רק בעיות ממשיות מן הסוגים: "השמטת תירוץ", "הוספה שאינה בתוס\'", '
              '"הבנה הפוכה", "ניסוח עמום". אל תכתוב מחדש ואל תציע נוסח. אם אין בעיה, החזר רשימה ריקה. '
              'החזר JSON בלבד: {"<מזהה>": {"<אות האופציה>": [{"סוג": "...", "נימוק": "משפט קצר"}]}}. אסור קו מפריד ארוך.')


def pack_tables(cfg):
    """לכל תוספות: האופציות לפי מנוע (מכל קובצי engines)."""
    pages = collect(cfg)
    byid, opts = {}, {}
    for slug, daf, tos in pages:
        for r in tos:
            byid[(slug, r['id'])] = r
            opts[(slug, r['id'])] = {}
        for e in cfg['engines']:
            fp = os.path.join(ROOT, 'tosafot', slug, 'engines', '%s--%s.json' % (e['id'], daf))
            if not os.path.exists(fp):
                raise SystemExit('עצירה: חסר פלט של %s לעמוד %s (הרץ run)' % (e['id'], daf))
            res = jload(fp)
            for r in tos:
                opts[(slug, r['id'])][e['id']] = res['out'][r['id']]
    return pages, byid, opts


def shuffled(slug, rid, engines):
    rnd = random.Random('tos-blind-%s-%s' % (slug, rid))
    ids = [e['id'] for e in engines]
    rnd.shuffle(ids)
    return {'abcde'[i]: eid for i, eid in enumerate(ids)}   # כמה אופציות: כמספר המנועים


def do_review(cfg):
    pages, byid, opts = pack_tables(cfg)
    u = spent()

    def one(page):
        slug, daf, tos = page
        fp = os.path.join(ROOT, 'tosafot', slug, 'engines', 'review--%s.json' % daf)
        if os.path.exists(fp) and not os.environ.get('RERUN'):
            return None
        blocks, maps = [], {}
        for r in tos:
            m = shuffled(slug, r['id'], cfg['engines'])
            maps[r['id']] = m
            blocks.append('### מזהה: %s\nפנים התוספות:\n%s\n\nאופציות:\n%s' % (
                r['id'], r['text'], '\n'.join('%s. %s' % (k, opts[(slug, r['id'])][m[k]]) for k in 'abcde'[:len(cfg['engines'])])))
        j = llm.call(cfg['reviewer']['model'], REVIEW_SYS, '\n\n'.join(blocks), thinking=cfg['reviewer']['thinking'])
        got = parse_json(j['text'])
        out = {}
        for r in tos:
            g = got.get(r['id'], {})
            m = maps[r['id']]
            out[r['id']] = {m[k]: g.get(k, []) for k in 'abcde'[:len(cfg['engines'])]}      # מפתח = מנוע (המיפוי נשאר פנימי)
        jdump(fp, {'daf': daf, 'slug': slug, 'tries': [{k: j[k] for k in ('in', 'out', 'think', 'ms', 'cost')}], 'ntos': len(tos), 'flags': out})
        return slug, daf, j

    with cf.ThreadPoolExecutor(3) as ex:
        for r in ex.map(one, pages):
            if r:
                record(u, 'review', 'haiku', r[0], r[1], r[2])
                print('נבדק', r[0], r[1], 'טוקנים:', r[2]['in'] + r[2]['out'])
    print('סך הצריכה המצטבר:', spent()['total'])


def do_pack(cfg):
    """בונה את קובץ המבחן הציבורי-לאתר (בלי שמות מנועים) ואת קובץ החשיפה (מיפוי, טוקנים, סימוני המבקר)."""
    pages, byid, opts = pack_tables(cfg)
    by_slug = {}
    for slug, daf, tos in pages:
        for r in tos:
            m = shuffled(slug, r['id'], cfg['engines'])
            key = r['n'] if (slug == 'kiddushin' and r['perek'] == 1) else r['perek'] * 1000 + r['n']      # זהה ל-make_live.ukey
            pub = {'key': key, 'n': r['n'], 'perek': r['perek'], 'hn': r['hn'], 'daf': r['dafKey'], 'dh': r['dh'], 'text': r['text'], 'url': r['url'],
                   'laukmi': r['laukmi'], 'options': {k: opts[(slug, r['id'])][m[k]] for k in 'abcde'[:len(cfg['engines'])]}}
            by_slug.setdefault(slug, {'items': {}, 'map': {}, 'tokens': {}, 'review': {}})
            by_slug[slug]['items'][r['id']] = pub
            by_slug[slug]['map'][r['id']] = m
    for slug, o in by_slug.items():
        # אומדן טוקנים לכל מנוע: סכום הקריאות / מספר התוספות (בתוך הסלאג)
        tok = {e['id']: {'in': 0, 'out': 0, 'think': 0, 'ms': 0, 'cost': 0.0, 'ntos': 0, 'model': e['model'], 'label': e['label']} for e in cfg['engines']}
        for e in cfg['engines']:
            for s2, daf, tos in pages:
                if s2 != slug:
                    continue
                res = jload(os.path.join(ROOT, 'tosafot', slug, 'engines', '%s--%s.json' % (e['id'], daf)))
                for t in res['tries']:
                    for k in ('in', 'out', 'think', 'ms'):
                        tok[e['id']][k] += t[k]
                    tok[e['id']]['cost'] += t['cost'] or 0
                tok[e['id']]['ntos'] += len(tos)
        rev = {}
        for s2, daf, tos in pages:
            if s2 != slug:
                continue
            fp = os.path.join(ROOT, 'tosafot', slug, 'engines', 'review--%s.json' % daf)
            if os.path.exists(fp):
                rev.update(jload(fp)['flags'])
        d = os.path.join(ROOT, 'tosafot', slug)
        # since: בחירות והערות שנשמרו לפני רגע האריזה (למשל בחירות הנוסח הישנות בקידושין) אינן נחשבות בחירה במבחן
        import time
        suf = cfg.get('packSuffix', '')
        jdump(os.path.join(d, 'test-options%s.json' % suf), {'slug': slug, 'since': int(time.time() * 1000), 'label': cfg.get('roundLabel', ''), 'items': o['items'], 'engines': [chr(97 + i) for i in range(len(cfg['engines']))]})
        jdump(os.path.join(d, 'test-reveal%s.json' % suf), {'slug': slug, 'map': o['map'], 'tokens': tok, 'review': rev, 'prices': cfg.get('prices', {}),
                                                   'pricesChecked': cfg.get('pricesChecked', ''), 'pricesNote': cfg.get('pricesNote', ''), 'verify': cfg.get('verify'), 'shas': cfg.get('shas', 27000)})
        print(slug, 'נכתבו test-options.json ו-test-reveal.json:', len(o['items']), 'תוספות')
        # נוסח ברירת המחדל ללומד עד שהמנהל בוחר: אופציית פייבל (styles-<פרק>.json, שממנו make_live בונה את live). לא בקידושין:
        # שם הבחירות הקיימות של המנהל כבר מוצגות, וקובץ ה-live הקיים אינו נכתב מחדש.
        if slug != 'kiddushin' and not suf:
            per = {}
            for rid, it in o['items'].items():
                eng = o['map'][rid]
                fable_letter = [k for k, v in eng.items() if v == 'fable'][0]
                per.setdefault(it['perek'], {})[str(it['n'])] = {'a': it['options'][fable_letter]}
            for perek, st in per.items():
                jdump(os.path.join(ROOT, 'tosafot', slug, 'styles-%d.json' % perek), st)
                print('נכתב styles-%d.json (נוסח ברירת המחדל: פייבל): %d' % (perek, len(st)))


if __name__ == '__main__':
    cfg = jload(sys.argv[1])
    {'run': do_run, 'review': do_review, 'pack': do_pack}[sys.argv[2]](cfg)
