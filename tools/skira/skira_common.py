# -*- coding: utf-8 -*-
"""skira_common.py - קבועים ועזרים משותפים לכלי הסקירה (13.10.2026).

הסקירה היא שדרוג של מערכת הבקרה (tools/bakara), לא מערכת מקבילה: אותם קובצי
ממצאים (data/bakara/<מסכת>-<פרק>.json), אותה נקודת קליטה, אותו ממשק. כאן יושבים
רק הדברים החדשים: סוג ההערה, טביעת הטקסט, והנתיבים.
"""
import os, re, sys, json, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TOOLS = os.path.join(ROOT, 'tools')
BAK = os.path.join(TOOLS, 'bakara')
for p in (TOOLS, BAK):
    if p not in sys.path:
        sys.path.insert(0, p)

DATA = os.path.join(ROOT, 'data', 'skira')
BDATA = os.path.join(ROOT, 'data', 'bakara')
WORK = os.path.join(ROOT, '_work', 'skira')
os.makedirs(DATA, exist_ok=True)

# סוגי ההערות הקבועים (מנה 13.10.2026, סעיף 3). המקור המקביל בממשק: SKT/SKMAP ב-tools/bakara_ui.js.
TYP = {'a': 'טעות בפשט', 'b': 'חסר שלב', 'c': 'לא מובן', 'd': 'כותרת', 'e': 'ניסוח',
       'f': 'מבנה', 'g': 'מכני', 'h': 'שאלה למחבר', 'i': 'בחר נוסח'}
DET2TYP = {
    'sem_hav': 'a', 'sem_yih': 'a', 'sem_hsr': 'b', 'sem_lo': 'c', 'cl_head': 'd', 'nose_long': 'd',
    'aram': 'e', 'cl_aram': 'e', 'sem_hash': 'e', 'hash': 'e', 'amor_long': 'e', 'cl_adv': 'e',
    'cl_mnum': 'f', 'cl_hdr': 'f', 'anchor': 'f', 'cl_src': 'f', 'cl_daf': 'f', 'dafpos': 'f',
    'joined': 'g', 'split': 'g', 'dbl': 'g', 'typo': 'g', 'orphan': 'g', 'punct': 'g', 'abbr': 'g',
    'amor_miss': 'g', 'psuk_bad': 'g', 'psuk_nik': 'g', 'psuk_miss': 'g', 'sem_mil': 'g', 'sem_sty': 'g',
    'cl_sty': 'g', 'cl_cit': 'g', 'cl_txt': 'g', 'cl_bug': 'g', 'alt': 'i',
}
# סוגים שמותר לאשר בגורף
BULK_OK = {'f', 'g'}
# סוגי ממצא חדשים שהסוקר החזק כותב (kind -> det). נרשמים גם בקטלוג של bakara.py.
SKIRA_KINDS = {
    'טעות בפשט': ('sk_pshat', 'a', 'חמור'), 'חסר שלב': ('sk_step', 'b', 'בינוני'),
    'לא מובן': ('sk_lo', 'c', 'קל'), 'כותרת': ('sk_head', 'd', 'קל'),
    'ניסוח': ('sk_word', 'e', 'קל'), 'מבנה': ('sk_struct', 'f', 'קל'),
    'מכני': ('sk_mech', 'g', 'קל'), 'שאלה למחבר': ('sk_q', 'h', 'קל'),
}
for _k, (_d, _t, _s) in SKIRA_KINDS.items():
    DET2TYP[_d] = _t

REASONS = {'no_err': 'לא טעות', 'my_way': 'כך אני כותב', 'unimp': 'לא חשוב',
           'not_get': 'קלוד לא הבין את הסוגיה', 'not_here': 'נכון אבל לא כאן', 'free': 'סיבה חופשית',
           'unspec': 'ללא סיבה'}

NIK = re.compile(r'[֑-ׇ]')
SP = re.compile(r'[\s​-‏‪-‮◄]+')
DASH = re.compile('[–—]')


def typ_of(f):
    t = f.get('typ')
    if t in TYP:
        return t
    return DET2TYP.get(f.get('det') or '', 'g')


def norm(t):
    """נרמול לטביעת טקסט: בלי ניקוד, בלי רווחים וסימוני עימוד."""
    return SP.sub('', NIK.sub('', t or ''))


def thash(t):
    return hashlib.sha1(norm(t).encode('utf-8')).hexdigest()[:12]


def no_dash(t):
    """מקף ארוך אסור בכל מקום (חוקה): מוחלף ב-"-"."""
    return DASH.sub('-', t or '')


def jload(p, default=None):
    if not os.path.exists(p):
        return default
    with open(p, encoding='utf-8') as f:
        return json.load(f)


def jsave(p, obj):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=1, sort_keys=True)
    os.replace(tmp, p)


def slugs_with_findings():
    out = set()
    for fn in os.listdir(BDATA):
        m = re.match(r'^([a-z-]+)-\d+\.json$', fn)
        if m:
            out.add(m.group(1))
    return sorted(out)


def findings_of(slug):
    """כל הממצאים של מסכת, מכל הפרקים: [(perek, finding)]."""
    out = []
    for fn in sorted(os.listdir(BDATA)):
        m = re.match(r'^%s-(\d+)\.json$' % re.escape(slug), fn)
        if not m:
            continue
        d = jload(os.path.join(BDATA, fn), {})
        for f in d.get('findings', []):
            out.append((int(m.group(1)), f))
    return out


# ---- מפתח דף: "ב." < "ב:" < "ג." ----
_G = {'א': 1, 'ב': 2, 'ג': 3, 'ד': 4, 'ה': 5, 'ו': 6, 'ז': 7, 'ח': 8, 'ט': 9, 'י': 10, 'כ': 20, 'ל': 30,
      'מ': 40, 'נ': 50, 'ס': 60, 'ע': 70, 'פ': 80, 'צ': 90, 'ק': 100, 'ר': 200, 'ש': 300, 'ת': 400}


def daf_key(d):
    d = (d or '').strip()
    side = 1 if d.endswith(':') else 0
    s = re.sub(r'[^א-ת]', '', d)
    if not s:
        return None
    n = sum(_G.get(c, 0) for c in s)
    return n * 2 + side


def jload_loose(p, default=None):
    """טעינת פלט של סוכן. גרשיים (") בתוך מחרוזת (ר"י, דאר"מ) שוברים JSON; כאן מתקנים שורה-שורה:
    שורה שאינה נטענת מפורקת לפי שמות השדות הידועים, והגרשיים הפנימיים נמלטים."""
    if not os.path.exists(p):
        return default
    raw = open(p, encoding='utf-8').read()
    try:
        return json.loads(raw)
    except ValueError:
        pass
    keys = r'(?:i|typ|why|conf|daf|kind|mark|note|evidence|fix|sev|alts)'
    out = []
    for ln in raw.splitlines():
        t = ln.strip().rstrip(',')
        if not t.startswith('{'):
            continue
        try:
            out.append(json.loads(t))
            continue
        except ValueError:
            pass
        body = t[1:-1] if t.endswith('}') else t[1:]
        parts = re.split(r'(?:^|,\s*)"(' + keys + r')":\s*', body)
        d = {}
        for j in range(1, len(parts) - 1, 2):
            k, v = parts[j], parts[j + 1].strip().rstrip(',').strip()
            if v.startswith('"') and v.endswith('"') and len(v) >= 2:
                d[k] = v[1:-1].replace('\\"', '"')
            elif v.startswith('['):
                try:
                    d[k] = json.loads(v)
                except ValueError:
                    d[k] = [v]
            else:
                try:
                    d[k] = int(v)
                except ValueError:
                    d[k] = v
        if 'i' in d:
            out.append(d)
    return out
