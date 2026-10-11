# -*- coding: utf-8 -*-
"""fetch_sources.py - מושך מספריא את הגמרא המנוקדת לכל מסכת.

מה נמשך: מהדורת William Davidson המנוקדת בארמית, ורק היא. שטיינזלץ
אינו נמשך ואינו מוצג (הכרעת בעל הפרויקט 7.9.2026: מקור עיון בלבד),
וזה גם חוסך כמחצית מן הנפח.

רישוי: הטקסט ב-CC BY-NC. האתר חינמי ואינו מוכר דבר, ולכן מותר לפרסם.
שורת הייחוס נכתבת בתחתית כל מגירה, ולעולם אינה נכנסת להדפסה.

הכלי הזה אינו רץ בשומר. הוא מורץ ביד, והתוצאה נשמרת במאגר; השומר רק
מעתיק אותה לאתר. כך אין משיכה מספריא בכל בנייה.

שימוש:
    uv run python tools/fetch_sources.py סוכה
    uv run python tools/fetch_sources.py --all
"""
import os, sys, json, re, io, time, argparse, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sefaria_map import SEFARIA, ref_to_heb

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'sources')
UA = {'User-Agent': 'leokmei-girsa/1.0 (torah study site; github.com/michaelFLEGG/leokmei-girsa)'}
API = 'https://www.sefaria.org/api/v3/texts/%s?version=hebrew'
CHUNK = 10            # אמודים בקריאה אחת. ספריא מחזירה טווח בבת אחת.
ATTRIB = 'הטקסט המנוקד: ספריא, William Davidson, ברישיון CC BY-NC'


def get(url, tries=4):
    """מחזיר None על 404 - הפניה פשוט אינה קיימת. כל כשל אחר מרים חריגה,
    כדי שתקלת רשת לא תיראה כמסכת שנגמרה."""
    last = None
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
                return json.loads(r.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            last = e
            time.sleep(2 + 3 * i)
        except Exception as e:
            last = e
            time.sleep(2 + 3 * i)
    raise RuntimeError('ספריא לא ענתה על %s: %r' % (url, last))


def flat(x, out):
    """מבנה ספריא מקונן. שיטוח רקורסיבי, כדי שלא ייבלע מקטע בשקט."""
    if isinstance(x, str):
        out.append(x)
    elif isinstance(x, list):
        for y in x:
            flat(y, out)
    elif x is not None:
        out.append(str(x))
    return out


TAG = re.compile(r'<[^>]+>')


def clean(h):
    """משאיר את הטקסט, ומדגיש את מה שספריא הדגישה. שאר התגיות יורדות.

    הסימון הזמני הוא {{B}} ולא תו בקרה: תו בקרה בתוך קוד המקור אובד
    בקלות בכל כלי שעובר על הקובץ, ואז ההדגשה נעלמת בשקט."""
    h = re.sub(r'<br\s*/?>', ' ', h)
    h = re.sub(r'<(?:big|strong|b)(?:\s[^>]*)?>', '{{B}}', h)
    h = re.sub(r'</(?:big|strong|b)>', '{{/B}}', h)
    h = TAG.sub('', h)
    h = (h.replace('&nbsp;', ' ').replace('&amp;', '&')
          .replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"'))
    h = re.sub(r'(?:\{\{B\}\})+', '<b>', h)
    h = re.sub(r'(?:\{\{/B\}\})+', '</b>', h)
    h = re.sub(r'<b>\s*</b>', '', h)
    return re.sub(r'\s+', ' ', h).strip()


def amudim(book):
    """רשימת האמודים של המסכת.

    האורך שבמפתח ספריא הוא גודל מרחב-הכתובות ולא מספר הדפים שיש בפועל,
    והוא גדול בדרך כלל באמוד או שניים. גם הדף הראשון אינו תמיד ב: תמיד
    פותחת בכ"ה:. לכן הדף הראשון נלקח מן ה-API, והסוף נקבע בפועל."""
    q = book.replace(' ', '%20')
    ix = get('https://www.sefaria.org/api/v2/raw/index/%s' % q)
    n = ((ix or {}).get('schema') or {}).get('lengths') or []
    total = n[0] if n else 0
    first = 2
    d0 = get(API % q)
    ref0 = (d0 or {}).get('firstAvailableSectionRef') or ''
    m = re.search(r'(\d+)([ab])$', ref0)
    start_b = False
    if m:
        first = int(m.group(1))
        start_b = m.group(2) == 'b'
    out = []
    d = first
    if start_b:
        out.append('%db' % d)
        d += 1
    while len(out) < total:
        out.append('%da' % d)
        if len(out) < total:
            out.append('%db' % d)
        d += 1
    return out


def fetch(masechet, log=print):
    book = SEFARIA.get(masechet)
    if not book:
        raise RuntimeError('אין שם ספריא למסכת %s' % masechet)
    q = book.replace(' ', '%20')
    refs = amudim(book)
    log('%s (%s): %d עמודים' % (masechet, book, len(refs)))
    pages, empty = {}, 0
    for i in range(0, len(refs), CHUNK):
        part = refs[i:i + CHUNK]
        rng = '%s.%s-%s' % (book.replace(' ', '%20'), part[0], part[-1])
        d = get(API % rng)
        if d is None:
            # אורך המסכת שבמפתח ספריא גדול לעתים מן הדפים שיש בה בפועל.
            # דפים שאינם קיימים בסוף המסכת אינם תקלה, והם נאמרים בקול.
            if pages:
                log('   %s ... %s אינם קיימים - סוף המסכת' % (part[0], part[-1]))
                break
            raise RuntimeError('ספריא אינה מכירה את %s' % rng)
        vs = d.get('versions') or []
        if not vs:
            log('   אין נוסח ל-%s' % rng)
            continue
        v = vs[0]
        txt = v.get('text')
        # טווח מחזיר רשימה לכל אמוד; אמוד בודד מחזיר רשימת מקטעים
        blocks = txt if (len(part) > 1 and isinstance(txt, list)
                         and txt and isinstance(txt[0], list)) else [txt]
        if len(blocks) > len(part):
            raise RuntimeError('ספריא החזירה %d עמודים במקום %d עבור %s - עוצר'
                               % (len(blocks), len(part), rng))
        short = len(blocks) < len(part)
        if short:
            # מנה קצרה מן המבוקש פירושה בדרך כלל שהמסכת נגמרה לפני מה
            # שהמפתח הבטיח. כדי לא להניח זאת בשקט, בודקים את האמוד
            # שאחרי מה שחזר: אם הוא קיים - זו תקלה של ממש ועוצרים.
            nxt = part[len(blocks)]
            if get(API % ('%s.%s' % (q, nxt))) is not None:
                raise RuntimeError('חסר %s באמצע %s - ספריא החזירה %d במקום %d'
                                   % (nxt, book, len(blocks), len(part)))
            log('   %s: המסכת נגמרת ב-%s (%d עמודים פחות מן המפתח)'
                % (book, part[len(blocks) - 1], len(part) - len(blocks)))
            part = part[:len(blocks)]
        for ref, blk in zip(part, blocks):
            segs = [clean(x) for x in flat(blk, [])]
            segs = [x for x in segs if x]
            if not segs:
                empty += 1
                continue
            pages[ref_to_heb(ref)] = {
                'daf': ref,
                'gemara': segs,
                'refs': ['%s.%s.%d' % (book.replace(' ', '_'), ref, n + 1)
                         for n in range(len(segs))],
            }
        log('   %s ... %s  (%d עמודים עד כה)' % (part[0], part[-1], len(pages)))
        if short:
            break
        time.sleep(0.4)
    if empty:
        log('   %d עמודים חזרו ריקים' % empty)
    data = {'schema_version': '1.0', 'tractate': book, 'masechet': masechet,
            'source': 'Sefaria', 'version': 'William Davidson Edition - Vocalized Aramaic',
            'license': 'CC-BY-NC', 'attribution': ATTRIB, 'pages': pages}
    return data


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('masechet', nargs='*')
    ap.add_argument('--all', action='store_true')
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from build_all import SLUG
    names = list(SLUG) if a.all else a.masechet
    if not names:
        print('ציין מסכת, או --all'); return
    total = 0
    for m in names:
        if m not in SLUG:
            print('לא מוכרת:', m); continue
        try:
            d = fetch(m)
        except Exception as e:
            print('נכשל', m, repr(e)); continue
        if not d['pages']:
            print('אין עמודים ל', m, '- לא נשמר'); continue
        p = os.path.join(OUT, SLUG[m] + '.json')
        io.open(p, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False))
        sz = os.path.getsize(p)
        total += sz
        print('נשמר %s: %d עמודים, %.1f מ"ב' % (SLUG[m], len(d['pages']), sz / 1e6))
    print('סך הכל %.1f מ"ב' % (total / 1e6))


if __name__ == '__main__':
    main()
