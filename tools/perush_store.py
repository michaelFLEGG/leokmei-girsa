# -*- coding: utf-8 -*-
"""perush_store.py - "פירוש הגמרא" מחוץ למאגר הציבורי ומחוץ לקובצי האתר (פרומפט 17, 2.11.2026).

הפירוש אינו יושב עוד ב-data/sources ולא בקובצי האתר. מקומו:
  א. במחסן של נקודת הקליטה (perush:<מסכת>), ומוגש רק עם הרשאת מנהל: GET /perush/masechet?slug=
  ב. בריפו הפרטי (leokmei-chavruta, בתיקייה perush), כעותק קבוע.
  ג. במטמון מקומי שאינו נשמר במאגר: data/perush/<מסכת>.json

הפתיחה לציבור היא מתג אחד: commentary_public שב-tools/site_settings.json. כשהוא דולק הבנייה מחזירה
את הפירוש לקובצי האתר, והדף מציג אותו לכל גולש בלי לפנות לנקודת הקליטה.

מבנה הקובץ: אובייקט JSON תקין {דף: [מקטעים]}, ובו כל עמוד בשורה משלו. נקודת הקליטה נעזרת בכך
כדי לשלוף עמוד אחד בלי לפענח את המסכת כולה (מגבלת זמן המעבד בתוכנית החינמית).

המפתח: LEOKMEI_ADMIN_KEY (סוד בפעולות גיטהאב), או LG_ADMIN_KEY, או קובץ המפתח המקומי. בלי גישה
הכלי עוצר ברעש: מספור קטעי המשנה בבנייה נגזר מן הפירוש, ובנייה בלעדיו היתה מוחקת אותו בשקט.
"""
import io, json, os, time, urllib.error, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, 'data', 'perush')
SETTINGS = os.path.join(ROOT, 'tools', 'site_settings.json')
API = os.environ.get('LG_API') or 'https://leokmei-suggest.m7654301.workers.dev'
KEY_FILE = r'C:\Users\Owner\Documents\לאוקמי-מפתח-מנהל.txt'
_mem = {}


class PerushUnavailable(SystemExit):
    """יורש מ-SystemExit בכוונה: לולאת הבנייה תופסת Exception ומדלגת על מסכת, וכאן צריך לעצור."""


def commentary_public():
    return bool(json.load(io.open(SETTINGS, encoding='utf-8')).get('commentary_public'))


def admin_key():
    for name in ('LEOKMEI_ADMIN_KEY', 'LG_ADMIN_KEY'):
        if os.environ.get(name):
            return os.environ[name]
    if os.path.exists(KEY_FILE):
        lines = [l.strip() for l in io.open(KEY_FILE, encoding='utf-8-sig').read().splitlines() if l.strip()]
        for l in reversed(lines):
            if l.isascii() and ' ' not in l and len(l) >= 16:
                return l
    return ''


def dumps(per):
    rows = [json.dumps(k, ensure_ascii=False) + ':' + json.dumps(v, ensure_ascii=False, separators=(',', ':'))
            for k, v in per.items()]
    return '{\n' + ',\n'.join(rows) + '\n}\n'


def _request(path, data=None):
    key = admin_key()
    if not key:
        raise PerushUnavailable('עצירה: פירוש הגמרא אינו נגיש כאן - חסר מפתח מנהל (LEOKMEI_ADMIN_KEY)')
    req = urllib.request.Request(API + path, data=data, method='POST' if data is not None else 'GET')
    req.add_header('x-admin-key', key)
    req.add_header('User-Agent', 'leokmei-perush/1.0')
    if data is not None:
        req.add_header('content-type', 'application/json; charset=utf-8')
    last = None
    for i in range(4):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return r.status, r.read().decode('utf-8')
        except urllib.error.HTTPError as e:
            if e.code < 500:
                return e.code, ''
            last = e
        except OSError as e:
            last = e
        time.sleep(3 * (i + 1))
    raise PerushUnavailable('עצירה: נקודת הקליטה אינה זמינה (%s): %s' % (path, last))


def load(slug, strict=True):
    """{דף: [מקטעים]} של מסכת. מסכת שאינה במחסן עוצרת, כדי שמפתח שגוי או מחסן ריק לא ימחקו את המספור בשקט.
    strict=False: כלי עזר שיכול להסתפק בלעדיו, ומקבל מילון ריק."""
    if slug in _mem:
        return _mem[slug]
    fp = os.path.join(CACHE, slug + '.json')
    if os.path.exists(fp):
        _mem[slug] = json.load(io.open(fp, encoding='utf-8'))
        return _mem[slug]
    try:
        code, txt = _request('/perush/masechet?slug=' + slug)
    except PerushUnavailable:
        if strict:
            raise
        return {}
    if code != 200:
        if strict:
            raise PerushUnavailable('עצירה: נקודת הקליטה החזירה %s על הפירוש של %s' % (code, slug))
        return {}
    per = json.loads(txt)
    os.makedirs(CACHE, exist_ok=True)
    io.open(fp, 'w', encoding='utf-8', newline='\n').write(txt)
    _mem[slug] = per
    return per


def attach(src, slug, strict=True):
    """מוסיף לעמודי קובץ המקורות (בזיכרון בלבד) את השדה perush. מחזיר כמה עמודים קיבלו פירוש."""
    n = 0
    pages = src.get('pages') or {}
    for k, segs in load(slug, strict).items():
        if k in pages:
            pages[k]['perush'] = segs
            n += 1
    return n


def private_dir():
    for p in (os.environ.get('LK_CHAVRUTA'), r'C:\leokmei-work\chavruta',
              os.path.join(os.path.dirname(ROOT), 'leokmei-chavruta'), os.path.join(os.path.dirname(ROOT), 'chavruta')):
        if p and os.path.isdir(p):
            return p
    return ''


def save(slug, per):
    """שומר במטמון ובריפו הפרטי, ומעלה למחסן. הדחיפה של הריפו הפרטי נעשית בנפרד."""
    txt = dumps(per)
    os.makedirs(CACHE, exist_ok=True)
    io.open(os.path.join(CACHE, slug + '.json'), 'w', encoding='utf-8', newline='\n').write(txt)
    priv = private_dir()
    if priv:
        os.makedirs(os.path.join(priv, 'perush'), exist_ok=True)
        io.open(os.path.join(priv, 'perush', slug + '.json'), 'w', encoding='utf-8', newline='\n').write(txt)
    else:
        print('אזהרה: הריפו הפרטי לא נמצא כאן, ולכן %s נשמר במחסן ובמטמון בלבד' % slug)
    code, _ = _request('/perush/put?slug=' + slug, txt.encode('utf-8'))
    if code != 200:
        raise PerushUnavailable('עצירה: העלאת הפירוש של %s נכשלה (%s)' % (slug, code))
    _mem[slug] = per
    return len(txt.encode('utf-8'))
