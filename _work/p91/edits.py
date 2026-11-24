# -*- coding: utf-8 -*-
"""פרומפט 91 - עריכות מכניות בשבת פרק ה (שדה p91), על הנוסח שבדף החי (נמשך בדפדפן, _work/p91/rowhtml.json).
עריכה חלה רק אם השורה עדיין בנוסח הזה (was), ולכן אינה דורסת עריכה של מיכאל.
    python _work/p91/edits.py [--write]"""
import os, sys, json, io, re, time, html
HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WRITE = '--write' in sys.argv
rows = {x['id']: x for x in json.load(io.open(os.path.join(HERE, '_work', 'p91', 'rowhtml.json'), encoding='utf-8'))}
plain = lambda h: re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', '', h or '')).replace('\xa0', ' ')).strip()


def inner(uid, ek):
    h = rows[uid]['html']
    m = re.search(r'data-ek="%s"[^>]*>(.*?)</(?:p|div)>' % re.escape(ek), h, re.S)
    return m.group(1)


T = [int(time.time() * 1000)]
out = []


def ed(uid, ek, daf, nowH, kind, why, ps=None, wasP=''):
    T[0] += 1
    wasH = inner(uid, ek)
    e = {'k': '%s~%d' % (ek, T[0]), 't': T[0], 'was': plain(wasH), 'now': plain(nowH), 'wasH': wasH, 'nowH': nowH,
         'daf': daf, 'wasP': wasP, 'ctx': {'b': '', 'a': ''}, 'p91': {'kind': kind, 'why': why}}
    if ps is not None:
        e['ps'] = ps
        e['psw'] = "ד''ה משנה" if ps == 'dh' else ''
    out.append(e)


# א. משנה ב (נב.) - שחזור התיבה כמו בספר עד 23.11 ובמשנה (data/mishna), בלי השורה הזרה
h0 = inner('3474', 'u3474.1').rstrip()
ed('3474', 'u3474.1', 'נב.', h0 + ' זכרים יוצאין לבובין, רחלות שחוזות כבולות וכבונות, ועזים צרורות. '
   'רבי יוסי: בכולן לא יוצאות, חוץ מן הרחלין הכבונות. רבי יהודה: עזים יוצאות צרורות ליבש, אבל לא לחלב.',
   'mishna', 'משנה ב שנקטעה בקיפול 24.11 (עריכות 23.11 17:50 סומנו תלושות) - שחזור התיבה המלאה')
ed('3475', 'u3475.1', 'נב.', '', 'mishna', 'לשון המשנה שיצאה מן התיבה - חזרה לתיבה בשורה הקודמת')
ed('3476', 'u3476.1', 'נב.', '', 'mishna', 'שורה זרה בתיבת משנה (שייכת לנג:, ושם היא כבר בדף)')
# ד.2 ד"ה משנה במקום כותרת נושא
ed('3455', 'u3455.0', 'נב.', '<i class="dm">ומזין עליהן וטובלן במקומן</i>', 'dh', 'פרומפט 91 ד.2: ד"ה משנה ולא כותרת נושא', ps='dh', wasP='nose')
ed('3462', 'u3462.0', 'נב.', '<i class="dm">וטובלן במקומן</i>', 'dh', 'פרומפט 91 ד.2: ד"ה משנה "וטובלן במקומן" (השאלה "והאיכא חציצה" - הצעה)', ps='dh', wasP='nose')
ed('3545', 'u3545.0', 'נג.', '<i class="dm">זכרים יוצאין לבובין</i>', 'dh', 'פרומפט 91 ד.2: ד"ה משנה במקום הכותרת "לבובין, שחוזות, כבולות וכבונות"', ps='dh', wasP='nose')
ed('3555', 'u3555.0', 'נג.', '<i class="dm">רחלים יוצאות כבולות</i>', 'dh', 'פרומפט 91 ד.2: ד"ה משנה במקום הכותרת "כבולות"', ps='dh', wasP='nose')
for e in out:
    print(e['k'], '|', e['was'][:60], '->', e['now'][:80], e.get('ps', ''))
if WRITE:
    p = os.path.join(HERE, 'data', 'edits', 'shabbat.json')
    d = json.load(io.open(p, encoding='utf-8'))
    have = {(x.get('k') or '').split('~')[0] for x in d['edits'] if x.get('p91')}
    add = [e for e in out if e['k'].split('~')[0] not in have]
    d['edits'] += add
    io.open(p, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=1) + '\n')
    print('נכתבו', len(add))
