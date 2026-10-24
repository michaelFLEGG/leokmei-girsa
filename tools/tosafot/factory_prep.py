# -*- coding: utf-8 -*-
"""factory_prep.py - שלב ההכנה של בית החרושת לתוספות: קוד בלבד, בלי מודל ובלי מפתח.

לכל מסכת:
  1. גבולות הפרקים מספריא (alt_struct "Chapters") -> tosafot/<מסכת>/chapters.json (משמר שדות קיימים, כמו verifiedThrough)
  2. כל תוספות המסכת מספריא (מהדורת וילנא) -> tosafot/raw/<מסכת>.json. עמוד שאין לו תוספות בספריא (404) נרשם, לא נבלע.
  3. מקור שני: ויקיטקסט, קטע ת של כל עמוד -> tosafot/raw/_wikisource-<מסכת>.json (כשהוא נגיש; אחרת נרשם גלוי "לא מאומת")
  4. הספירה הקבועה לכל פרק (build_count.py): הסרת כפילויות ברישום, מספור רציף לפי הפרק, אימות הד"ה מול המקור השני
  5. הקשר הלאוקמי גירסא לכל עמוד (extract_context.py, דורש בנייה של האתר: site/<מסכת>.data.js)

    uv run python tools/tosafot/factory_prep.py sukkah --fetch      # שלבים 1 עד 4
    uv run python tools/tosafot/factory_prep.py sukkah --context    # שלב 5, אחרי בנייה
    --keep-counts: ספירה של פרק שכבר קיימת אינה נבנית מחדש (קידושין פרק א, וכל פרק שכבר פורסם)
"""
import os, sys, re, json, io, time, subprocess, urllib.request, urllib.parse, urllib.error
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
ROOT = os.path.dirname(os.path.dirname(HERE))
from build_count import heb_num, daf_key, daf_order
from fetch_tosafot import dafim
from fetch_sources import get

KEEP = False
import factory as _F
from sefaria_map import SEFARIA as _SEF
# מכל מסכת בתור: שם עברי ושם בספריא (לפי מפת המסכתות של האתר)
BOOKS = {sl: (he, _SEF[he]) for sl, he in _F.SLUG2HE.items() if he in _SEF}
UA = {'User-Agent': 'leokmei-girsa/1.0 (torah study site; github.com/michaelFLEGG/leokmei-girsa)'}


def jload(p, d=None):
    return json.load(io.open(p, encoding='utf-8')) if os.path.exists(p) else d


def jdump(p, o):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with io.open(p, 'w', encoding='utf-8') as f:
        json.dump(o, f, ensure_ascii=False, indent=1)


def parse_ref(ref):
    """'Berakhot 2a:1-13a:15' -> ('2a', 1, '13a', 15)"""
    m = re.search(r'(\d+[ab]):(\d+)-(\d+[ab]):(\d+)$', ref)
    if not m:
        raise SystemExit('עצירה: wholeRef לא מוכר: ' + ref)
    return m.group(1), int(m.group(2)), m.group(3), int(m.group(4))


def chapters_from_index(slug):
    he, book = BOOKS[slug]
    j = get('https://www.sefaria.org/api/v2/raw/index/%s' % book.replace(' ', '_'))
    nodes = j['alt_structs']['Chapters']['nodes']
    out = []
    for i, nd in enumerate(nodes, 1):
        a, al, b, bl = parse_ref(nd['wholeRef'])
        name = ''
        for t in nd.get('titles', []):
            if t.get('lang') == 'he' and t.get('primary'):
                name = t['text']
        out.append({'n': i, 'name': name, 'from': a, 'fromLine': al, 'to': b, 'toLine': bl})
    return out


def fetch_raw(slug, first, last):
    he, book = BOOKS[slug]
    old = jload(os.path.join(ROOT, 'tosafot', 'raw', slug + '.json'), {'items': []})
    have = {}
    for it in old.get('items', []):
        have.setdefault(it['daf'], []).append(it)
    items, missing = [], []
    for d in dafim(first, last):
        j = get('https://www.sefaria.org/api/v3/texts/Tosafot_on_%s.%s?version=hebrew' % (book.replace(' ', '_'), d))
        vs = (j or {}).get('versions') or []
        if not vs:
            missing.append(d)
            continue
        k = 0
        for li, line in enumerate(vs[0]['text']):
            segs = line if isinstance(line, list) else ([line] if line else [])
            for si, s in enumerate(segs):
                if not s or not str(s).strip():
                    continue
                k += 1
                items.append({'daf': d, 'line': li + 1, 'seg': si + 1, 'ref': 'Tosafot on %s %s:%d:%d' % (book, d, li + 1, si + 1), 'html': s})
        print(d, k, file=sys.stderr)
    out = {'slug': slug, 'from': first, 'to': last, 'source': 'Sefaria, Tosafot on %s, Vilna Edition' % book, 'items': items, 'missingDafim': missing}
    jdump(os.path.join(ROOT, 'tosafot', 'raw', slug + '.json'), out)
    return items, missing


def heb_daf_title(he, d):
    n, side = int(d[:-1]), d[-1]
    return '%s %s %s' % (he, heb_num(n).replace('"', '').replace("'", ''), 'א' if side == 'a' else 'ב')


def wiki_api(**p):
    p['format'] = 'json'
    u = 'https://he.wikisource.org/w/api.php?' + urllib.parse.urlencode(p)
    for i in range(5):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60))
        except urllib.error.HTTPError as e:
            if e.code == 429:       # הגבלת קצב: ממתינים ומנסים שוב, בקצב איטי
                time.sleep(20 * (i + 1))
            else:
                time.sleep(3 + 3 * i)
        except Exception:
            time.sleep(3 + 3 * i)
    return None


def fetch_wiki(slug, first, last):
    he, book = BOOKS[slug]
    ds = dafim(first, last)
    path = os.path.join(ROOT, 'tosafot', 'raw', '_wikisource-%s.json' % slug)
    got = jload(path, {})
    todo = [d for d in ds if d not in got]
    for i in range(0, len(todo), 5):
        time.sleep(1.5)
        grp = todo[i:i + 5]
        titles = '|'.join(heb_daf_title(he, d) for d in grp)
        j = wiki_api(action='query', titles=titles, prop='revisions', rvprop='content', rvslots='main')
        if not j:
            print('ויקיטקסט לא נגיש (נשמר מה שנמשך עד כה)', file=sys.stderr)
            jdump(path, got)
            return None
        norm = {n['to']: n['from'] for n in j['query'].get('normalized', [])}
        by = {}
        for pg in j['query']['pages'].values():
            t = pg.get('title')
            if 'revisions' in pg:
                by[t] = pg['revisions'][0]['slots']['main']['*']
        for d in grp:
            t = heb_daf_title(he, d)
            txt = by.get(t)
            if txt is None:
                continue
            m = re.search(r'<קטע התחלה=ת/>(.*?)<קטע סוף=ת/>', txt, re.S)
            if m:
                got[d] = m.group(1).strip()
    jdump(path, got)
    return got


def run_count(slug, perek):
    r = subprocess.run([sys.executable, os.path.join(HERE, 'build_count.py'), slug, str(perek)], capture_output=True, text=True, encoding='utf-8')
    print(r.stdout.strip())
    if r.returncode != 0:
        raise SystemExit('עצירה: build_count נכשל לפרק %d: %s' % (perek, (r.stderr or r.stdout)[-500:]))


def do_fetch(slug):
    chs = chapters_from_index(slug)
    first, last = '2a', chs[-1]['to']
    items, missing = fetch_raw(slug, first, last)
    print('נמשכו %d דיבורים, עמודים בלי תוספות בספריא: %s' % (len(items), missing))
    wiki = fetch_wiki(slug, first, last)
    cpath = os.path.join(ROOT, 'tosafot', slug, 'chapters.json')
    old = jload(cpath, {'masechet': BOOKS[slug][0], 'chapters': []})
    oldby = {c['n']: c for c in old.get('chapters', [])}
    merged = []
    for c in chs:
        o = oldby.get(c['n'], {})
        row = {'n': c['n'], 'name': o.get('name') or c['name'], 'from': c['from'], 'fromLine': c['fromLine'], 'to': c['to'], 'toLine': c['toLine'],
               'countedThrough': c['to']}
        if o.get('verifiedThrough'):
            row['verifiedThrough'] = o['verifiedThrough']
        merged.append(row)
    old['chapters'] = merged
    old['masechet'] = BOOKS[slug][0]
    old['note'] = 'גבולות הפרקים לפי ספריא (Chapters, מהדורת וילנא). countedThrough: עד איזה עמוד נמשכו התוספות (13.10.2026: כל המסכת). עמודים שאין להם תוספות בספריא: ' + (', '.join(missing) or 'אין') + '.'
    jdump(cpath, old)
    for c in merged:
        # 24.10.2026: ספירה קיימת אינה נבנית מחדש (--keep-counts): המספור שלה כבר פורסם ומוכרע. רק פרק חדש נספר.
        if KEEP and os.path.exists(os.path.join(ROOT, 'tosafot', slug, 'count-%d.json' % c['n'])):
            print('פרק %d: ספירה קיימת נשמרת' % c['n'])
            continue
        run_count(slug, c['n'])
    print('נבנתה ספירה ל-%d פרקים' % len(merged))


def do_context(slug):
    raw = jload(os.path.join(ROOT, 'tosafot', 'raw', slug + '.json'))
    keys = []
    for d in dafim('2a', raw['to']):
        k = daf_key(d)
        if k not in keys:
            keys.append(k)
    r = subprocess.run([sys.executable, os.path.join(HERE, 'extract_context.py'), slug, '--tolerant'] + keys, capture_output=True, text=True, encoding='utf-8')
    print(r.stdout[-1500:])
    if r.returncode != 0:
        raise SystemExit('עצירה: extract_context נכשל: ' + (r.stderr or '')[-600:])


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    slug = sys.argv[1]
    KEEP = '--keep-counts' in sys.argv
    if '--fetch' in sys.argv:
        do_fetch(slug)
    if '--context' in sys.argv:
        do_context(slug)
