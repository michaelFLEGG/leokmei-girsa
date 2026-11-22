# -*- coding: utf-8 -*-
"""perek_range.py - טווח הדפים ושם הפרק המלא לכל פרק (פרומפט 78 ותוספתו, 22.11.2026).

א. הטווח נגזר מן הקובץ עצמו: ציון הדף הראשון והאחרון שבתוך הפרק (העמודים שהבנייה שייכה לפרק), ומאומת מול
   חלוקת הפרקים בדפוס וילנא (tosafot/<slug>/chapters.json, ספריא). סתירה - מכריעים לפי וילנא, ונרשם.
ב. שם הפרק המלא: כששני פרקים באותה מסכת מתחילים באותן מילים בשם הקצר (תענית: "סדר תעניות" פעמיים), השם
   בכותרת הרצה הוא שם הפרק המלא לפי וילנא ("סדר תעניות כיצד" / "סדר תעניות אלו").
ג. הכתיב אחיד: "(ב. - כ:)" - סוגריים, רווח-מקף-רווח, נקודה/נקודתיים לעמוד.
"""
import os, re, json, io

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_L = [(400, 'ת'), (300, 'ש'), (200, 'ר'), (100, 'ק'), (90, 'צ'), (80, 'פ'), (70, 'ע'), (60, 'ס'), (50, 'נ'),
      (40, 'מ'), (30, 'ל'), (20, 'כ'), (10, 'י'), (9, 'ט'), (8, 'ח'), (7, 'ז'), (6, 'ו'), (5, 'ה'), (4, 'ד'),
      (3, 'ג'), (2, 'ב'), (1, 'א')]
V = {c: v for v, c in _L}


def heb(n):
    s, m = '', n
    for v, c in _L:
        while m >= v:
            if v == 10 and m in (15, 16):
                break
            s += c; m -= v
    return s


def amud_heb(a):
    """'15a' -> 'טו.'"""
    m = re.match(r'^(\d+)([ab])$', a or '')
    if not m:
        return None
    return heb(int(m.group(1))) + ('.' if m.group(2) == 'a' else ':')


def key(d):
    if not d:
        return None
    t = d.strip()
    n = sum(V.get(c, 0) for c in re.sub(r'[.:"\'׳״\s]', '', t))
    return n * 2 + (1 if t.endswith(':') else 0) if n else None


def fmt(a, b):
    return '(%s - %s)' % (a, b)


def chapters(slug):
    p = os.path.join(HERE, 'tosafot', slug, 'chapters.json')
    if not os.path.exists(p):
        return []
    return json.load(io.open(p, encoding='utf-8')).get('chapters') or []


def compute(slug, pages, ordinal):
    """{perek_label: {'n', 'range', 'file', 'vilna', 'name', 'full', 'note'}} - ordinal: פונקציה מכותרת למספר."""
    C = {c['n']: c for c in chapters(slug)}
    order, info = [], {}
    for p in pages:
        lab = p.get('perek') or ''
        if not lab or not p.get('daf'):
            continue
        if lab not in info:
            info[lab] = {'n': ordinal(lab), 'name': p.get('perekName') or '', 'first': p['daf'], 'last': p['daf']}
            order.append(lab)
        else:
            if key(p['daf']) and (key(info[lab]['last']) is None or key(p['daf']) >= key(info[lab]['last'])):
                info[lab]['last'] = p['daf']
    short = {}
    for lab in order:
        nm = ' '.join((info[lab]['name'] or '').split()[:2])
        short.setdefault(nm, []).append(lab)
    out = {}
    for lab in order:
        r = info[lab]
        f = fmt(r['first'], r['last'])
        c = C.get(r['n'])
        vil = fmt(amud_heb(c['from']), amud_heb(c['to'])) if c and amud_heb(c.get('from')) and amud_heb(c.get('to')) else None
        rng, note = f, ''
        if vil and vil != f:
            rng, note = vil, 'הקובץ נותן %s, וילנא %s - הוכרע לפי וילנא' % (f, vil)
        nm = ' '.join((r['name'] or '').split()[:2])
        full = r['name']
        if c and len(short.get(nm, [])) > 1 and c.get('name'):
            full = c['name']
        out[lab] = {'n': r['n'], 'range': rng, 'file': f, 'vilna': vil, 'name': r['name'], 'full': full, 'note': note}
    return out
