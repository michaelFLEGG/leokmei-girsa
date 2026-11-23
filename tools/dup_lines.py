# -*- coding: utf-8 -*-
"""dup_lines.py - שורות כפולות בדף (פרומפט 87, 23.11.2026; ממשיך את פרומפט 42 ו-44). מכני, בלי בינה מלאכותית.

הכלל הקבוע של בעל הפרויקט: שורה כפולה היא "ודאי טעות", ומוחקים אותה בלי לשאול.

  same     - שורה זהה (אחרי נרמול ניקוד, רווחים ופיסוק) שחוזרת באותה יחידה או בטווח של עד WIN שורות גוף.
             נמחק המופע שאינו משתלב ברצף: אם אחד מהם עומד בראש יחידה תחת כותרת צד משלו והשני לא - נשאר
             זה שתחת הכותרת. אחרת נשאר הראשון. שורה יחידה תחת כותרת צד אינה נמחקת אלא אם גם לשנייה אותה כותרת
             (ואז נמחקת גם הכותרת, כדי שלא תישאר יתומה).
  part     - שארית פיצול: שורה שהיא בדיוק סוף השורה שלפניה, או בדיוק תחילת השורה שאחריה, באותה יחידה.
             נמחקת, כי התוכן כולו בשנייה.
  near     - כמעט זהות (דמיון 0.9 ומעלה, עד 2 שורות זו מזו, לא הכלה) - לעיון בלבד, לא נמחקת.
לא נבדקים: שורה בתיבת משנה מול שורת גמרא (הגמרא מצטטת את המשנה), כותרות, ד"ה, ושורה של פחות מ-3 מילים.

    from dup_lines import scan     scan(rows) -> [ממצא]
rows: [{id, k, box, daf, items:[{ek, h, anchor}]}] (מבנה הנתונים בדף, כמו בבודק המשניות).
"""
import re, html as _html, difflib

WIN = 12
NIK = re.compile('[֑-ׇ]')


def plain(h):
    return _html.unescape(re.sub(r'<[^>]+>', '', h or '')).replace('\xa0', ' ')


def norm(t):
    t = NIK.sub('', t or '')
    t = re.sub('[^א-ת0-9 ]', ' ', t)
    return ' '.join(t.split())


def lines_of(rows):
    out = []
    for ri, r in enumerate(rows):
        if r.get('k') not in ('u', 'm'):
            continue
        anc = [it for it in r['items'] if it.get('anchor')]
        body = [it for it in r['items'] if not it.get('anchor')]
        a = norm(plain(anc[0]['h'])) if anc else ''
        for n, it in enumerate(body):
            t = plain(it['h'])
            out.append({'ri': ri, 'ek': it['ek'], 'k': r.get('k'), 'n': n, 'nb': len(body), 'anchor': a,
                        'anchor_ek': anc[0]['ek'] if anc else '', 'h': it['h'], 't': t, 'nt': norm(t),
                        'daf': r.get('daf'), 'row': r.get('id')})
    return out


def _sim(a, b):
    return difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()


def scan(rows):
    L = lines_of(rows)
    found = []
    gone = set()
    for i, x in enumerate(L):
        if len(x['nt'].split()) < 3 or x['ek'] in gone:
            continue
        for j in range(i + 1, len(L)):
            y = L[j]
            same_unit = y['ri'] == x['ri']
            if j - i > WIN and not (same_unit and j - i <= 30):
                break
            if y['ek'] in gone or x['k'] != y['k'] or len(y['nt'].split()) < 3:
                continue
            if x['nt'] == y['nt'] and (len(x['nt'].split()) < 4 or len(x['nt']) < 18):
                continue            # שורה קצרה שחוזרת (פזמון בגמרא: "תיקו", "ואני אומר: אינה גנובה") - לא נוגעים
            if x['nt'] == y['nt'] and j - i > 1 and (x['k'] == 'm' or (NIK.search(x['t']) and NIK.search(y['t']))):
                continue            # משנה (בתיבה או מצוטטת בניקוד) חוזרת על לשונה במבנה מקביל (שבועות מט:, שבת סז:)
            if x['nt'] == y['nt']:
                # איזה מופע נשאר
                xa = x['n'] == 0 and x['anchor'] and x['nb'] == 1
                ya = y['n'] == 0 and y['anchor'] and y['nb'] == 1
                xh = x['n'] == 0 and bool(x['anchor'])
                yh = y['n'] == 0 and bool(y['anchor'])
                if yh and not xh:
                    drop, keep = x, y
                elif xh and not yh:
                    drop, keep = y, x
                else:
                    drop, keep = y, x
                orphan = drop['n'] == 0 and drop['nb'] == 1 and bool(drop['anchor'])
                if orphan and drop['anchor'] != keep['anchor']:
                    # השורה היחידה תחת כותרת צד שונה: לא מוחקים בלי עיון
                    found.append({'kind': 'near', 'why': 'שורה זהה, כל אחת תחת כותרת צד אחרת', 'a': x, 'b': y})
                    continue
                found.append({'kind': 'same', 'drop': drop, 'keep': keep, 'drop_anchor': orphan})
                gone.add(drop['ek'])
                if drop is x:
                    break
                continue
            if j - i <= 2:
                # שארית פיצול: הקטע הוא בדיוק סוף השורה שלפניו, או בדיוק תחילת השורה שאחריו, באותה יחידה
                if j - i == 1 and same_unit and len(x['nt']) != len(y['nt']):
                    if len(y['nt'].split()) >= 3 and len(y['nt']) < len(x['nt']) and x['nt'].endswith(' ' + y['nt']):
                        found.append({'kind': 'part', 'drop': y, 'keep': x, 'drop_anchor': False})
                        gone.add(y['ek'])
                        continue
                    if len(x['nt'].split()) >= 3 and len(x['nt']) < len(y['nt']) and y['nt'].startswith(x['nt'] + ' '):
                        found.append({'kind': 'part', 'drop': x, 'keep': y, 'drop_anchor': False})
                        gone.add(x['ek'])
                        break
                if j - i <= 2 and min(len(x['nt']), len(y['nt'])) >= 15 and _sim(x['nt'], y['nt']) >= 0.9 \
                        and not (NIK.search(x['t']) and NIK.search(y['t'])):
                    found.append({'kind': 'near', 'why': 'כמעט זהות', 'a': x, 'b': y})
    return found


# ---------------------------------------------------------------- הרצה לילית (bodkim.yml)

def edits_for(slug, rows, found, t0, tag='p87dup'):
    """רשומות עריכה רגילות בשכבה: מחיקת המופע המיותר (וכותרת הצד שנשארה יתומה), מפתח קפוא."""
    out = []
    t = [t0]

    def rec(it, daf, why, extra=None):
        t[0] += 1
        e = {'k': '%s~%d' % (it['ek'], t[0]), 't': t[0], 'was': _html.unescape(re.sub(r'<[^>]+>', '', it['h'])),
             'now': '', 'wasH': it['h'], 'nowH': '', 'daf': daf or '', 'wasP': '', tag: {'why': why}}
        if extra:
            e[tag].update(extra)
        return e
    for x in found:
        if x['kind'] not in ('same', 'part'):
            continue
        d, k = x['drop'], x['keep']
        why = 'שורה כפולה' if x['kind'] == 'same' else 'שארית פיצול (כלולה בשורה הסמוכה)'
        out.append(rec({'ek': d['ek'], 'h': d['h']}, d['daf'], why, {'keep': k['ek']}))
        if x.get('drop_anchor') and d.get('anchor_ek'):
            r = rows[d['ri']]
            a = [it for it in r['items'] if it.get('anchor')]
            if a:
                out.append(rec(a[0], d['daf'], 'כותרת צד שנשארה יתומה אחרי מחיקת שורה כפולה', {'keep': k['ek']}))
    return out


def hot_keys(slug, live_dir=None, hours=12):
    """מפתחות (uN.M) ויחידות (uN) שנערכו בשרת בשעות האחרונות."""
    import os, io, json, time
    try:
        if live_dir and os.path.exists(os.path.join(live_dir, slug + '.json')):
            srv = json.load(io.open(os.path.join(live_dir, slug + '.json'), encoding='utf-8')).get('doc') or {}
        else:
            import fold as F
            srv = F.live_doc(slug)
    except Exception:
        return set()
    since = int(time.time() * 1000) - hours * 3600 * 1000
    out = set()
    for e in srv.get('edits') or []:
        if (e.get('t') or 0) >= since:
            k = str(e.get('k') or '').split('~')[0]
            if k:
                out.add(k); out.add(k.split('.')[0])
    return out


def main():
    import os, sys, io, json, argparse, time, datetime
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    sys.path.insert(0, here)
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', default='')
    ap.add_argument('--apply', action='store_true', help='לכתוב את המחיקות לשכבה (data/edits/<מסכת>.json)')
    ap.add_argument('--live-dir', default='')
    a = ap.parse_args()
    import mishna_check as MC, mishna_gaps as MG
    book = json.load(io.open(os.path.join(root, 'data', 'book.json'), encoding='utf-8'))
    slugs = [s for s in book['slugs'] if not a.only or s in a.only.split(',')]
    rep = {'when': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'masechtot': {}}
    t0 = int(time.time() * 1000)
    total = 0
    for s in slugs:
        try:
            rows = MG.rows_from_pages(MC.pages_of(s, True, a.live_dir or None))
        except Exception as e:
            rep['masechtot'][s] = {'error': str(e)[:200]}
            print(s, 'שגיאה', e)
            continue
        found = scan(rows)
        eds = edits_for(s, rows, found, t0)
        # שורה שמיכאל ערך ב-12 השעות האחרונות (או ביחידה שנוצרה בהן) - לא נוגעים: ייתכן שהוא באמצע עבודה עליה
        hot = hot_keys(s, a.live_dir or None)
        held = [e for e in eds if e['k'].split('~')[0] in hot or e['k'].split('.')[0] in hot]
        eds = [e for e in eds if e not in held]
        t0 += len(eds) + 10
        near = [{'daf': x['a']['daf'], 'why': x['why'], 'a': [x['a']['ek'], x['a']['t']], 'b': [x['b']['ek'], x['b']['t']]}
                for x in found if x['kind'] == 'near']
        near += [{'daf': e['daf'], 'why': 'שורה כפולה שמיכאל ערך היום - לא נמחקה', 'a': [e['k'].split('~')[0], e['was']], 'b': ['', '']}
                 for e in held]
        rep['masechtot'][s] = {'removed': [{'daf': e['daf'], 'k': e['k'], 'was': e['was'], 'why': e['p87dup']['why']} for e in eds],
                               'near': near}
        print('%-14s נמחקו %3d  לעיון %3d' % (s, len(eds), len(near)))
        if a.apply and eds:
            p = os.path.join(root, 'data', 'edits', s + '.json')
            doc = json.load(io.open(p, encoding='utf-8')) if os.path.exists(p) else {'v': 1, 'slug': s, 'edits': []}
            have = {e.get('was') + '|' + str(e.get('k', '')).split('~')[0] for e in doc.get('edits') or [] if e.get('p87dup')}
            new = [e for e in eds if e['was'] + '|' + e['k'].split('~')[0] not in have]
            doc['edits'] = (doc.get('edits') or []) + new
            io.open(p, 'w', encoding='utf-8', newline='\n').write(json.dumps(doc, ensure_ascii=False, indent=1))
            total += len(new)
    io.open(os.path.join(root, 'data', 'fold', 'dups.json'), 'w', encoding='utf-8', newline='\n').write(
        json.dumps(rep, ensure_ascii=False, indent=1) + '\n')
    print('נכתבו לשכבה:', total)


if __name__ == '__main__':
    main()
