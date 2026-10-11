# -*- coding: utf-8 -*-
"""build_count.py - בונה את קובץ הספירה הקבוע של תוספות לפרק: מספר סידורי לכל דיבור.

קלט:  tosafot/raw/<slug>.json            (ספריא, מהדורת וילנא; fetch_tosafot.py)
      tosafot/raw/_wikisource-<slug>.json (מקור שני לאימות, ויקיטקסט: קטע ת של כל עמוד)
      tosafot/<slug>/chapters.json         (גבולות הפרק לפי עימוד האתר)
פלט:  tosafot/<slug>/count-<perek>.json    (הספירה הקבועה)
      tosafot/<slug>/verification-<perek>.md (מה נמדד מול המקור השני)

כללים:
  א. דיבור שהוא העתק מילולי של דיבור אחר באותו דף (ספריא מקשרת אותו לשתי שורות גמרא) נספר פעם אחת.
     כל הסרה נרשמת בקובץ הספירה בשדה removed, ולעולם אינה שקטה.
  ב. הספירה היא לפי סדר הדף: שורת הגמרא, ואז סדר הקטע.
  ג. לא מאחדים ולא מדלגים. דיבור קצר נספר כמו ארוך.

    uv run python tools/tosafot/build_count.py kiddushin 1
"""
import os, sys, re, json, io
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

NIK = re.compile('[֑-ׇ]')


def heb_num(n):
    """מספור באותיות עם גרשיים: קל"ו; טו וטז נכתבים ט"ו ו-ט"ז."""
    units = [(400, 'ת'), (300, 'ש'), (200, 'ר'), (100, 'ק'), (90, 'צ'), (80, 'פ'), (70, 'ע'), (60, 'ס'), (50, 'נ'),
             (40, 'מ'), (30, 'ל'), (20, 'כ'), (10, 'י'), (9, 'ט'), (8, 'ח'), (7, 'ז'), (6, 'ו'), (5, 'ה'), (4, 'ד'),
             (3, 'ג'), (2, 'ב'), (1, 'א')]
    s = ''
    m = n
    for v, c in units:
        while m >= v:
            if v == 10 and m in (15, 16):
                break
            s += c
            m -= v
    if m in (15, 16):
        s += 'ט' + ('ו' if m == 15 else 'ז')
        m = 0
    if len(s) == 1:
        return s + "'"
    return s[:-1] + '"' + s[-1]


def daf_key(d):
    """2a -> 'ב.' ; 14b -> 'יד:' (מפתח העמוד באתר)"""
    n, side = int(d[:-1]), d[-1]
    return heb_num(n).replace('"', '').replace("'", '') + ('.' if side == 'a' else ':')


def daf_order(d):
    return int(d[:-1]) * 2 + (0 if d[-1] == 'a' else 1)


def clean(h):
    t = re.sub(r'<[^>]+>', '', h)
    t = t.replace('–', '-').replace('—', '-').replace(' ', ' ')
    return re.sub(r'[ \t]+', ' ', t).strip()


def norm(t):
    t = NIK.sub('', t)
    t = re.sub(r'[^א-ת ]', '', t)
    return re.sub(r'\s+', ' ', t).strip()


def split_dh(t):
    """דיבור המתחיל: עד ' - ' בתוך ארבע עשרה המילים הראשונות; אחרת עד הנקודה או הנקודתיים הראשונים."""
    words = t.split(' ')
    m = re.search(r' - ', t)
    if m and len(t[:m.start()].split(' ')) <= 14:
        return t[:m.start()].strip(), t[m.end():].strip(), 'מקף'
    m = re.search(r'[.:]\s', t)
    if m and len(t[:m.start()].split(' ')) <= 10:
        return t[:m.start()].strip(), t[m.end():].strip(), 'נקודה'
    return ' '.join(words[:4]), t, 'ארבע מילים (לבדיקה)'


def main():
    slug, perek = sys.argv[1], int(sys.argv[2])
    base = os.path.join(ROOT, 'tosafot')
    raw = json.load(io.open(os.path.join(base, 'raw', slug + '.json'), encoding='utf-8'))
    wiki = json.load(io.open(os.path.join(base, 'raw', '_wikisource-' + slug + '.json'), encoding='utf-8'))
    chap = json.load(io.open(os.path.join(base, slug, 'chapters.json'), encoding='utf-8'))
    ch = [c for c in chap['chapters'] if c['n'] == perek][0]
    lo, hi = daf_order(ch['from']), daf_order(ch['to'])
    items = [i for i in raw['items'] if lo <= daf_order(i['daf']) <= hi]
    items.sort(key=lambda i: (daf_order(i['daf']), i['line'], i['seg']))
    kept, removed, seen = [], [], {}
    for it in items:
        t = clean(it['html'])
        key = (it['daf'], norm(t))
        if key in seen:
            removed.append({'daf': it['daf'], 'line': it['line'], 'seg': it['seg'], 'ref': it['ref'],
                            'reason': 'העתק מילולי של %s (אותו דף), קושר בספריא לשורת גמרא שנייה' % seen[key]['ref'],
                            'dh': t[:60]})
            continue
        dh, body, rule = split_dh(t)
        row = {'daf': it['daf'], 'line': it['line'], 'seg': it['seg'], 'ref': it['ref'], 'text': t, 'dh': dh,
               'dhRule': rule}
        seen[key] = row
        kept.append(row)
    vt = daf_order(ch['verifiedThrough']) if ch.get('verifiedThrough') else 0
    for n, r in enumerate(kept, 1):
        r['verified'] = daf_order(r['daf']) <= vt
        r['n'] = n
        r['hn'] = heb_num(n)
        r['dafKey'] = daf_key(r['daf'])
        r['url'] = 'https://www.sefaria.org/' + r['ref'].replace(' ', '_').replace(':', '.')
    out = {'slug': slug, 'masechet': chap['masechet'], 'perek': perek, 'perekName': ch['name'],
           'from': ch['from'], 'to': ch['to'], 'verifiedThrough': ch.get('verifiedThrough', ''),
           'source': raw['source'], 'total': len(kept),
           'removed': removed,
           'note': 'הספירה קבועה: אין לחשב מחדש בכל טעינה. שינוי בה נעשה רק בכלי הזה, עם רישום ב-removed.',
           'items': kept}
    d = os.path.join(base, slug)
    with io.open(os.path.join(d, 'count-%d.json' % perek), 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    # אימות מול המקור השני
    def paras(w):
        return [norm(re.sub(r"\{\{[^}]*\}\}|\[\[|\]\]|'''|''", '', p)) for p in re.split(r'\n\s*\n', (w or '').strip()) if p.strip()]
    lines = ['# אימות ספירת תוספות - %s פרק %d (%s עד %s)' % (chap['masechet'], perek, ch['from'], ch['to']), '',
             'מקור הספירה: ' + raw['source'] + '.',
             'מקור שני לבדיקה: ויקיטקסט, "תוספות על הש"ס", קטע ת של כל עמוד (נוסח וילנא מוקלד).',
             'סך הכול אחרי הסרת כפילויות: **%d**. הוסרו: %d.' % (len(kept), len(removed)), '']
    if removed:
        lines += ['## הוסרו (כפילות מילולית בספריא)', '']
        for r in removed:
            lines.append('- %s (שורת גמרא %d): %s... - %s' % (r['daf'], r['line'], r['dh'], r['reason']))
        lines.append('')
    lines += ['', '## השוואה לפי עמוד', '',
              'כל דיבור של ספריא מאותר בטקסט הוויקיטקסט של אותו עמוד (שלוש המילים הראשונות, לפי הסדר). פסקה בוויקיטקסט',
              'שאינה פותחת דיבור של ספריא היא או המשך מהעמוד הקודם או דיבור שחסר בספריא: האחרון מסומן לבדיקה.', '',
              '| עמוד | ספריא | פסקאות בוויקיטקסט | לא נמצא בוויקיטקסט | פסקאות ללא דיבור | הערה |', '|---|---|---|---|---|---|']
    flagged = []
    for d_ in sorted({i['daf'] for i in kept}, key=daf_order):
        mine = [r for r in kept if r['daf'] == d_]
        wp = paras(wiki.get(d_))
        pos, notfound, seen_paras = 0, [], {}
        for r in mine:
            w3 = norm(r['text']).split()
            hit = -1
            for k in (3, 2):
                key = ' '.join(w3[:k])
                for pi in range(len(wp)):
                    if pi >= 0 and key and key in wp[pi]:
                        hit = pi
                        break
                if hit >= 0:
                    break
            if hit < 0:
                notfound.append(r['hn'])
            else:
                seen_paras.setdefault(hit, []).append(r['hn'])
        orphan = [pi for pi in range(len(wp)) if pi not in seen_paras]
        carry = [pi for pi in orphan if pi == 0]
        bad_orphans = [pi for pi in orphan if pi != 0]
        merged = sum(len(v) - 1 for v in seen_paras.values() if len(v) > 1)
        notes = []
        if carry:
            notes.append('פסקה ראשונה = המשך מהעמוד הקודם')
        if merged:
            notes.append('ויקיטקסט מאחד %d (בספריא הם נפרדים)' % merged)
        if notfound or bad_orphans:
            flagged.append(d_)
            notes.append('לבדיקה')
        lines.append('| %s | %d | %d | %s | %s | %s |' % (d_, len(mine), len(wp), ','.join(notfound) or '-',
                     ','.join(str(x + 1) for x in bad_orphans) or '-', '; '.join(notes) or 'תואם'))
    lines += ['', 'עמודים לבדיקה: %d (%s).' % (len(flagged), ', '.join(flagged) or 'אין')]
    unexplained = flagged
    hand = os.path.join(d, 'verification-notes-%d.md' % perek)
    if os.path.exists(hand):
        lines += ['', io.open(hand, encoding='utf-8').read().rstrip()]
    with io.open(os.path.join(d, 'verification-%d.md' % perek), 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    print('נבנה: %d דיבורים, הוסרו %d, עמודים עם פער לא מוסבר: %d %s' % (len(kept), len(removed), len(unexplained), unexplained))


if __name__ == '__main__':
    main()
