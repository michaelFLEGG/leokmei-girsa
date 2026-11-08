# -*- coding: utf-8 -*-
"""כלי העזר של הכותב היומי (8.11.2026) - "הדף היומי בווטסאפ".

  python tools/daf_wa/writer.py need [ימים=10]   אילו דפים בימים הקרובים חסרים תוכן בדוק; כותב את הגמרא שלהם
                                                בלי ניקוד, ממוספרת בשורות, ל-_work/daf_src/<slug>_<עמוד>.txt
  python tools/daf_wa/writer.py gate [slug-n ...] שער מכני על קובצי התוכן: מבנה, 4-6 שורות, ans בטווח, ref תקין,
                                                בלי מקף ארוך. יוצא בקוד 1 על כל כשל (עצירה רועשת).

הכתיבה עצמה והבדיקה מול הגמרא - בידי הכותב והבודק הנפרד (_work/daf_wa_checker.md)."""
import datetime as dt
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import build  # noqa: E402

DATA = os.path.join(ROOT, 'data', 'daf-wa')
SRC = os.path.join(ROOT, '_work', 'daf_src')
NIKUD = re.compile(r'[֑-ׇ]')


def page_keys(n):
    t = build.letters(n)
    return [t + '.', t + ':']


def dump(slug, n):
    p = json.load(io.open(os.path.join(ROOT, 'data', 'sources', slug + '.json'), encoding='utf-8'))['pages']
    os.makedirs(SRC, exist_ok=True)
    out = []
    for k in page_keys(n):
        if k not in p:
            continue
        txt = '\n'.join('%d| %s' % (i + 1, NIKUD.sub('', re.sub(r'<[^>]+>', '', x))) for i, x in enumerate(p[k]['gemara']))
        f = os.path.join(SRC, '%s_%s.txt' % (slug, k.replace('.', 'a').replace(':', 'b')))
        io.open(f, 'w', encoding='utf-8').write(txt)
        out.append(os.path.relpath(f, ROOT))
    return out


def need(days=10):
    L = build.cycle()
    today = dt.date.today()
    seen, todo = set(), []
    for i in range(days + 3):
        name, slug, n, last = build.daf_of(today + dt.timedelta(days=i), L)
        key = '%s-%d' % (slug, n)
        if key in seen:
            continue
        seen.add(key)
        f = os.path.join(DATA, key + '.json')
        ok = False
        if os.path.exists(f):
            ok = bool(json.load(io.open(f, encoding='utf-8')).get('check', {}).get('ok'))
        if not ok:
            todo.append(dict(key=key, slug=slug, masechet=name, n=n, daf=build.gq(n), date=(today + dt.timedelta(days=i)).isoformat(),
                             last=last, src=dump(slug, n)))
    print(json.dumps(todo, ensure_ascii=False, indent=1))
    return todo


_ONE = r'[א-ת"\']+[.:](?: [\d, -]+)?(?: \([^)]*\))?'
REF = re.compile(r'^%s(?: · %s)*$' % (_ONE, _ONE))


def gate(keys):
    bad = []
    files = [k + '.json' for k in keys] if keys else sorted(f for f in os.listdir(DATA) if f.endswith('.json'))
    for f in files:
        c = json.load(io.open(os.path.join(DATA, f), encoding='utf-8'))
        e = []
        for fld in ('slug', 'masechet', 'n', 'daf', 'hook', 'alts', 'card', 'lines', 'check'):
            if fld not in c:
                e.append('חסר שדה ' + fld)
        lines = c.get('lines') or []
        if not 4 <= len(lines) <= 6:
            e.append('%d שורות (צריך 4-6)' % len(lines))
        for q in [c.get('hook') or {}] + list(c.get('alts') or []):
            if not q.get('q') or not isinstance(q.get('ans'), int) or not 0 <= q['ans'] < len(lines):
                e.append('שאלה בלי תשובה תקינה: %s' % q.get('q'))
        for i, x in enumerate(lines):
            if not x.get('t') or not x.get('ref'):
                e.append('שורה %d ריקה או בלי ref' % i)
            elif not REF.match(x['ref']):
                e.append('שורה %d: ref לא תקין "%s"' % (i, x['ref']))
        blob = json.dumps(c, ensure_ascii=False)
        if '–' in blob or '—' in blob:
            e.append('מקף ארוך')
        if NIKUD.search(blob):
            e.append('ניקוד בתוכן')
        if f[:-5] != '%s-%s' % (c.get('slug'), c.get('n')):
            e.append('שם הקובץ אינו תואם slug-n')
        if e:
            bad.append((f, e))
    for f, e in bad:
        print('!!!', f, '; '.join(e))
    print('השער: %d קבצים, %d נכשלו' % (len(files), len(bad)))
    return not bad


if __name__ == '__main__':
    a = sys.argv[1:]
    if not a or a[0] == 'need':
        need(int(a[1]) if len(a) > 1 else 10)
    elif a[0] == 'gate':
        sys.exit(0 if gate(a[1:]) else 1)
    else:
        raise SystemExit(__doc__)
