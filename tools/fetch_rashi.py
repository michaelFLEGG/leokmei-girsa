# -*- coding: utf-8 -*-
"""fetch_rashi.py - רש"י מספריא לחבילת סכם (פרומפט 91 ה., מומש בפרומפט 92, 24.11.2026). מכני, בלי מודל.

לכל עמוד של המסכת (לפי data/sources/<מסכת>.json): Rashi on <Tractate>.<דף><a|b> מספריא, נשמר בריפו הפרטי
leokmei-chavruta (ענף main) בקובץ rashi/<מסכת>.json: {"pages": {"ב.": ["ד"ה - פירוש", ...]}}.
הריפו הציבורי אינו מחזיק את הטקסט. runner.mjs next קורא את הקובץ וכותב rashi.md לחבילה של כל קטע.

    python tools/fetch_rashi.py kiddushin bava-kamma      כותב ל-../leokmei-chavruta/rashi/
    python tools/fetch_rashi.py --all                     כל המסכתות שב-data/book.json
עמוד שלא נמשך (רשת, אין רש"י) נרשם ב-"missing" - עצירה רועשת בסוף, לא דילוג שקט.
"""
import os, sys, io, re, json, time, html, urllib.request, urllib.parse

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHAV = os.environ.get('LK_CHAVRUTA') or os.path.join(os.path.dirname(HERE), 'leokmei-chavruta')
V = {'א': 1, 'ב': 2, 'ג': 3, 'ד': 4, 'ה': 5, 'ו': 6, 'ז': 7, 'ח': 8, 'ט': 9, 'י': 10, 'כ': 20, 'ל': 30, 'מ': 40,
     'נ': 50, 'ס': 60, 'ע': 70, 'פ': 80, 'צ': 90, 'ק': 100, 'ר': 200, 'ש': 300, 'ת': 400}


def ref_of(lab):
    m = re.match(r'^\s*([א-ת"\'״׳]+)\s*([.:])\s*$', lab or '')
    if not m:
        return None
    n = sum(V.get(c, 0) for c in m.group(1))
    return '%d%s' % (n, 'a' if m.group(2) == '.' else 'b') if n else None


def flat(t):
    if isinstance(t, list):
        out = []
        for x in t:
            out += flat(x)
        return out
    t = html.unescape(re.sub(r'<[^>]+>', '', t or '')).strip()
    return [t] if t else []


def fetch(tractate, ref):
    url = 'https://www.sefaria.org/api/v3/texts/' + urllib.parse.quote('Rashi_on_%s.%s' % (tractate.replace(' ', '_'), ref))
    req = urllib.request.Request(url, headers={'user-agent': 'leokmei-sakem/1.0'})
    for i in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                d = json.loads(r.read().decode('utf-8'))
            for v in d.get('versions') or []:
                if v.get('language') == 'he':
                    return flat(v.get('text'))
            return []
        except Exception:
            time.sleep(2 * (i + 1))
    return None


def one(slug):
    src = json.load(io.open(os.path.join(HERE, 'data', 'sources', slug + '.json'), encoding='utf-8'))
    tr = src.get('tractate')
    out = {'v': 1, 'slug': slug, 'tractate': tr, 'source': 'Sefaria, Rashi on ' + str(tr) + ' (Vilna Edition)', 'pages': {}, 'missing': []}
    for lab in src.get('pages') or {}:
        ref = ref_of(lab)
        if not ref:
            continue
        t = fetch(tr, ref)
        if t is None:
            out['missing'].append(lab)
        elif t:
            out['pages'][lab] = t
        time.sleep(0.15)
    os.makedirs(os.path.join(CHAV, 'rashi'), exist_ok=True)
    p = os.path.join(CHAV, 'rashi', slug + '.json')
    io.open(p, 'w', encoding='utf-8').write(json.dumps(out, ensure_ascii=False, indent=1) + '\n')
    print('%-14s %4d עמודים עם רש"י, %d לא נמשכו' % (slug, len(out['pages']), len(out['missing'])))
    return len(out['missing'])


def main():
    a = sys.argv[1:]
    if '--all' in a:
        a = json.load(io.open(os.path.join(HERE, 'data', 'book.json'), encoding='utf-8'))['slugs']
    bad = sum(one(s) for s in a)
    if bad:
        print('אזהרה: %d עמודים לא נמשכו - להריץ שוב' % bad)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
