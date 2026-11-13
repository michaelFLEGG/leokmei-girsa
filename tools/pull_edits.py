# -*- coding: utf-8 -*-
"""pull_edits.py - מושך מנקודת הקליטה את עריכות המנהל שטרם נקלטו בוורד,
וכותב אותן ל-data/edits/<מסכת>.json, שממנו הבנייה מחילה אותן על האתר.

שתי דרכי הרצה:
 א. בבנייה של השומר (fetch.py קורא לו): בלי שום סוד, מן הנקודה הציבורית
    /live (בלי שמות ובלי מחיקות). כך כל בנייה כוללת את העריכות.
 ב. במחשב של בעל הפרויקט (משימה מתוזמנת, tools/bake_edits.py): עם מפתח
    המנהל מן הקובץ המקומי, ביצוא מלא; ואם נכתב משהו - דוחף, והבנייה הקצרה
    (edits.yml) מפרסמת תוך דקות.

כללים:
 - רק עריכות שאינן מחיקה ושעדיין לא סומנו כנקלטות בוורד (ing).
 - הסדר הוא סדר הזמן, כי שינוי מבנה נשען על הנוסח שאחרי התיקון.
 - קובץ נכתב רק אם תוכנו השתנה (בלי שדה when), כדי שלא תיווצר דחיפה
   חדשה בכל הרצה.
 - מסכת שאינה בין מסכתות האתר מדולגת.
"""
import os, sys, io, json, datetime, urllib.request, urllib.error

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
API = 'https://leokmei-suggest.m7654301.workers.dev'
OUT = os.path.join(HERE, 'data', 'edits')
KEY_FILE = r'C:\Users\Owner\Documents\לאוקמי-מפתח-מנהל.txt'


def call(path, key=''):
    req = urllib.request.Request(API + path)
    req.add_header('user-agent', 'Mozilla/5.0 leokmei-pull/1.0')
    if key:
        req.add_header('x-admin-key', key)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode('utf-8'))


def find_key():
    key = os.environ.get('LEOKMEI_ADMIN_KEY', '').strip()
    if key or not os.path.exists(KEY_FILE):
        return key
    lines = [x.strip() for x in io.open(KEY_FILE, encoding='utf-8-sig').read().splitlines()]
    for l in reversed(lines):
        if len(l) >= 20 and all(ord(c) < 128 for c in l):
            return l
    return ''


def load_all(key, known):
    """עם מפתח: יצוא מלא. בלעדיו: /live לכל מסכת."""
    if key:
        return call('/export', key).get('edits') or {}
    out = {}
    for slug in sorted(known):
        try:
            d = call('/live?slug=' + slug).get('doc') or {}
        except Exception as e:
            print('אין תשובה מנקודת הקליטה עבור', slug, e)
            continue
        if d.get('edits'):
            out[slug] = d
    return out


def main(emit=True):
    key = find_key()
    import build_all
    known = set(build_all.SLUG.values())
    names = {v: k for k, v in build_all.SLUG.items()}
    allx = load_all(key, known)
    os.makedirs(OUT, exist_ok=True)
    changed = []
    cmp = lambda d: json.dumps({k: v for k, v in (d or {}).items() if k != 'when'},
                               ensure_ascii=False, sort_keys=True)
    for slug, doc in allx.items():
        if slug not in known:
            continue
        path = os.path.join(OUT, slug + '.json')
        old = None
        if os.path.exists(path):
            try:
                old = json.load(io.open(path, encoding='utf-8'))
            except Exception:
                old = None
        # 7.11.2026 - איחוד ולא דריסה. מאז 6.11 15:57 נקודת הקליטה אינה מקבלת פרסום, והעורך שבדף עובר
        # לדרך השלישית: דחיפת כל העריכות שבמכשיר לקובץ הזה במאגר. ההרצה הזאת דרסה את הקובץ בכל 5 דקות
        # בגרסה הישנה שבנקודת הקליטה, והעריכות נעלמו מן האתר ומן ההדפסה (נשארו רק במכשיר של המנהל).
        # עכשיו: כל עריכה שבקובץ או בנקודת הקליטה נשמרת, ולאותו מפתח - הגרסה החדשה יותר.
        # ועוד: מסכת שנבנית מצילום וורד מוצמד - עריכה שנקלטה לוורד החי (ing) נשארת, כי הצילום אינו מכיל אותה.
        _pinned = os.path.exists(os.path.join(HERE, 'data', 'word-pin', 'recovered-%s.json' % slug))
        _key = lambda e: e.get('k') or ('s%s' % e.get('t'))
        by = {}
        for e in doc.get('edits') or []:
            by[_key(e)] = e
        for e in (old or {}).get('edits') or []:
            o = by.get(_key(e))
            if o is None or (e.get('t') or 0) > (o.get('t') or 0):
                by[_key(e)] = e
        # 13.11.2026: עריכות שנקלטו לוורד בענן (data/word-pin/absorbed-<מסכת>.json) אינן חוזרות לקובץ
        _absp = os.path.join(HERE, 'data', 'word-pin', 'absorbed-%s.json' % slug)
        _abs = set()
        if os.path.exists(_absp):
            try:
                _abs = set(json.load(io.open(_absp, encoding='utf-8')).get('t') or [])
            except Exception as _e:
                print('אזהרה: רשימת העריכות שנקלטו של', slug, 'לא נקראה:', _e)
        edits = [e for e in by.values() if not e.get('del') and (_pinned or not e.get('ing'))
                 and e.get('t') not in _abs]
        edits.sort(key=lambda e: e.get('t') or 0)
        if not edits and not os.path.exists(path):
            continue
        new = {'v': 1, 'slug': slug, 'masechet': names.get(slug, ''), 'sty': doc.get('sty') or (old or {}).get('sty'),
               'edits': edits}
        if old is not None and cmp(old) == cmp(new):
            continue
        if not edits and old is not None and not (old.get('edits') or []):
            continue
        new['when'] = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        io.open(path, 'w', encoding='utf-8', newline='\n').write(
            json.dumps(new, ensure_ascii=False, indent=1))
        changed.append(slug)
        print('נכתב %s: %d עריכות' % (slug, len(edits)))
    print(('CHANGED=' if emit else 'נמשכו=') + ','.join(changed))
    return changed


if __name__ == '__main__':
    main()
