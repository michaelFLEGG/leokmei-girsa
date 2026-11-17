# -*- coding: utf-8 -*-
"""keep.py - "שורה שהתארכה": הכרעות שנשארות לתמיד (פרומפט 49 חלק 0, 17.11.2026).

הכלל של מיכאל (16.11.2026): שורה שהוא החזיר לשורה אחת בהדפסה (קיבל הצעה, ערך, איחה או חתך)
נשארת כך לתמיד - בתצוגה, במצב דפוס, בכל הדפסה ובוורד - ולא מחושבת מחדש כל פעם.

מה קרה ב-16.11: שתי הכרעות של הבוקר (ד: חיתוך, ח. "בפי ושט") נדרסו ב-17:38 ו-17:39 בקבלת הצעת "סכם"
שנכתבה על הנוסח שלפני ההכרעה. הדריסה נרשמה כעריכה רגילה, ולכן שום שער לא עצר אותה.

המרשם: data/overflow/keep/<מסכת>.json
  items   - כל הכרעה: daf, kind (text / split / join), lines = נוסח השורות שחייבות להיות כל אחת פסקה
            אחת ושורה אחת בהדפסה המוגדלת. מקור ומתי.
  restore - רשומות עריכה לשחזור דרך השכבה (כמו העורך), נשלחות לשרת ב-push.

    python tools/overflow/keep.py check --slug berakhot --report <דוח המנוע עם --lines>
        כל שורה במרשם: קיימת כפסקה, ובשורה אחת בדוח (n == 1). אחרת - קוד יציאה 1 (עוצר מסירה).
    python tools/overflow/keep.py sync --slug berakhot      (צריך LEOKMEI_ADMIN_KEY)
        הכרעות "קבל" ו"ערוך" מן השרת (bakara/dec, ov-<מסכת>) נכנסות למרשם. לא מוחק דבר.
    python tools/overflow/keep.py push --slug berakhot      (צריך LEOKMEI_ADMIN_KEY)
        רשומות restore נשלחות לשרת (PUT /edits, מיזוג לפי מפתח וזמן - אינו דורס עריכה חדשה יותר).
"""
import argparse, html, io, json, os, re, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
KEEP = os.path.join(ROOT, 'data', 'overflow', 'keep')
API = os.environ.get('LG_API') or 'https://leokmei-suggest.m7654301.workers.dev'


def norm(s):
    """אותיות וספרות בלבד: בלי ניקוד, פיסוק, רווחים, תגיות וסימני תוספות"""
    s = re.sub(r'<[^>]+>', '', s or '')
    s = html.unescape(s)
    s = re.sub(r'⁠\d+', '', s)
    return re.sub(r'[^א-ת0-9]', '', s)


def load(slug):
    fp = os.path.join(KEEP, slug + '.json')
    if not os.path.exists(fp):
        return fp, {'slug': slug, 'items': [], 'restore': []}
    return fp, json.load(io.open(fp, encoding='utf-8'))


def save(fp, doc):
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    io.open(fp, 'w', encoding='utf-8', newline='\n').write(json.dumps(doc, ensure_ascii=False, indent=1) + '\n')


def key():
    k = os.environ.get('LEOKMEI_ADMIN_KEY', '').strip()
    if not k:
        sys.exit('עצירה: אין מפתח מנהל (LEOKMEI_ADMIN_KEY)')
    return k


def call(method, path, body=None):
    data = json.dumps(body, ensure_ascii=False).encode('utf-8') if body is not None else None
    req = urllib.request.Request(API + path, data=data, method=method, headers={
        'content-type': 'application/json; charset=utf-8', 'x-admin-key': key(),
        'user-agent': 'Mozilla/5.0 leokmei-keep/1.0'})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode('utf-8'))


def items_of(slug):
    """המרשם, ועוד כל הכרעת "קבל"/"ערוך" שבקובץ ההכרעות שבמאגר (learn.py כותב אותו מן השרת)"""
    fp, doc = load(slug)
    items = list(doc.get('items') or [])
    have = {it.get('id') for it in items}
    dp = os.path.join(ROOT, 'data', 'overflow', 'decisions', slug + '.json')
    if os.path.exists(dp):
        for d in json.load(io.open(dp, encoding='utf-8')).get('items') or []:
            if d.get('d') not in ('ok', 'edit') or d.get('id') in have or not (d.get('now') or '').strip():
                continue
            lines = [x.strip() for x in d['now'].split(' / ')] if ':split' in (d.get('kind') or '') else [d['now'].strip()]
            it = {'id': d.get('id'), 'daf': '', 'kind': 'decision', 'lines': lines, 'src': 'הכרעה בשרת'}
            # פרומפט 53: איחוי (כלי 5) מאחד שתי שורות לפסקה אחת - היא בשתי שורות לכל היותר, לא באחת
            if ':join' in (d.get('kind') or ''):
                it['maxn'] = 2
            items.append(it)
    return items


def check(slug, report, partial=False):
    fp, doc = load(slug)
    doc = dict(doc, items=items_of(slug))
    R = json.load(io.open(report, encoding='utf-8'))
    pl = R.get('plines') or []
    if not pl:
        print('עצירה: בדוח אין plines (צריך להריץ את המנוע עם --lines)')
        return 1
    by = {}
    for p in pl:
        by.setdefault(norm(p.get('text')), []).append(p)
    bad = 0
    print('שורה שהתארכה - בדיקת ההכרעות הקבועות (%s, %d הכרעות)' % (slug, len(doc.get('items') or [])))
    for it in doc.get('items') or []:
        for ln in it.get('lines') or []:
            hits = by.get(norm(ln)) or []
            if not hits:
                # השורה אולי נכנסה לתוך פסקה ארוכה יותר (איחוי מאוחר של מיכאל) - אז היא אינה "שבורה" אלא בתוך פסקה
                # נכנסה לתוך פסקה אחרת: תקין רק אם הפסקה כולה בשורה אחת (חיתוך שאוחה בחזרה ונשבר = תקלה)
                inside = [p for p in pl if norm(ln) and norm(ln) in norm(p.get('text'))]
                st = 'חסרה' if not inside else 'בתוך פסקה אחרת (%s, %d שורות)' % (inside[0].get('daf'), inside[0].get('n'))
                okin = bool(inside) and min(p.get('n') or 0 for p in inside) <= (it.get('maxn') or 1)
                if partial and not inside:
                    print('  - %s | %s | מחוץ לטווח שהודפס' % (it.get('daf'), ln[:60]))
                    continue
                if not okin:
                    bad += 1
                print('  %s %s | %s | %s' % ('V' if okin else 'X', it.get('daf'), ln[:60], st))
                continue
            n = min(p.get('n') or 0 for p in hits)
            ok = n <= (it.get('maxn') or 1)
            if not ok:
                bad += 1
            print('  %s %s | %s | %s' % ('V' if ok else 'X', it.get('daf'), ln[:60], ('שורה אחת' if n == 1 else '%d שורות (איחוי)' % n) if ok else '%d שורות' % n))
    print('תקלות: %d' % bad)
    return 1 if bad else 0


def sync(slug):
    fp, doc = load(slug)
    j = call('GET', '/bakara/dec?slug=ov-' + slug)
    dec = ((j.get('doc') or {}).get('dec')) or {}
    have = {it.get('id') for it in doc.get('items') or []}
    n = 0
    for i, d in dec.items():
        if d.get('d') not in ('ok', 'edit') or i in have or not d.get('now'):
            continue
        lines = [x.strip() for x in d['now'].split(' / ')] if ':split' in (d.get('kind') or '') else [d['now'].strip()]
        doc.setdefault('items', []).append({'id': i, 'daf': '', 'kind': 'split' if len(lines) > 1 else 'text', 'lines': lines,
                                            'src': 'הכרעת המנהל בחלונית (%s), t=%s' % (d.get('d'), d.get('t'))})
        n += 1
    save(fp, doc)
    print('נוספו %d הכרעות למרשם (%s)' % (n, slug))
    return 0


def push(slug):
    fp, doc = load(slug)
    eds = doc.get('restore') or []
    if not eds:
        print('אין רשומות לשחזור (%s)' % slug)
        return 0
    d = call('PUT', '/edits', {'slug': slug, 'edits': eds})
    got = {(e.get('k'), e.get('t')) for e in ((d.get('doc') or {}).get('edits') or [])}
    miss = [e for e in eds if (e.get('k'), e.get('t')) not in got]
    print('%s: נשלחו %d, בשרת %d מהן' % (slug, len(eds), len(eds) - len(miss)))
    return 1 if miss else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['check', 'sync', 'push'])
    ap.add_argument('--slug', default='berakhot')
    ap.add_argument('--report', default='')
    ap.add_argument('--partial', action='store_true', help='הדפסה חלקית: שורה שאינה בטווח אינה תקלה')
    a = ap.parse_args()
    if a.cmd == 'check':
        return check(a.slug, a.report, a.partial)
    if a.cmd == 'sync':
        return sync(a.slug)
    return push(a.slug)


if __name__ == '__main__':
    sys.exit(main())
