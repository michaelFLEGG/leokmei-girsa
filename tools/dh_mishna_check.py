# -*- coding: utf-8 -*-
"""dh_mishna_check.py - ד"ה משנה קודם לכותרת. פרומפט 91 ד.3 (24.11.2026). מכני, בלי מודל.

הכלל (פרומפט 91 ד.1): כל מקום שהגמרא פותחת בלשון המשנה (דיבור המתחיל) - בלאוקמי יש ד"ה משנה. מותר להוסיף אחריו
כותרת נושא או ביאור באותה שורה; לעולם לא למחוק אותו ולשים כותרת במקומו.

לכל עמוד גמרא (data/sources/<מסכת>.json): שורות שנפתחות ב-2 עד 4 מילים מלשון המשנה של אותו פרק (data/mishna,
אחרי נרמול: בלי ניקוד, אותיות שימוש ו/י באמצע), חוץ מן המשנה עצמה. מולן - ד"ה המשנה שבלאוקמי באותו עמוד ובעמוד
שלפניו ושאחריו (יחידת dh, שורה במחלקת dh, או קטע במחלקת dm). ממצא:
  dh_ok      - יש ד"ה משנה שמכיל את המילים.
  topic      - אין ד"ה, אבל כותרת נושא באותו טווח מכילה את המילים: כותרת במקום הד"ה (ודאי - להמיר).
  missing    - אין ד"ה ואין כותרת (ספק: הלאוקמי מסכם לפעמים בלי ד"ה; לסקור סכם).
  history    - בהיסטוריית העריכות (data/word-cloud/ingested, data/edits): ד"ה משנה שהוסב לכותרת או נמחק.

    python tools/dh_mishna_check.py                 כל המסכתות (הספר)
    python tools/dh_mishna_check.py --only shabbat --rows FILE   עמודים מן הדפדפן
פלט: data/dh-check/<מסכת>.json וטבלה.
"""
import os, sys, io, re, json, html, argparse, datetime, collections

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'tools'))
from daf_check import dk, label, words, plain, load_rows, SKIPK

OUT = os.path.join(HERE, 'data', 'dh-check')
ORD = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי', 'שישי', 'שביעי', 'שמיני', 'תשיעי', 'עשירי', 'אחד עשר', 'שנים עשר',
       'שלושה עשר', 'ארבעה עשר', 'חמישה עשר', 'שישה עשר', 'שבעה עשר', 'שמונה עשר', 'תשעה עשר', 'עשרים', 'עשרים ואחד',
       'עשרים ושנים', 'עשרים ושלושה', 'עשרים וארבעה']


def perek_no(t):
    t = (t or '').replace('פרק', '').strip()
    t2 = t.replace('ששי', 'שישי').replace('שלשה', 'שלושה')
    for i, o in enumerate(ORD):
        if t2 == o:
            return i + 1
    return None


def seqs(ws, lo=2, hi=4):
    s = set()
    for L in range(lo, hi + 1):
        for i in range(len(ws) - L + 1):
            s.add(tuple(ws[i:i + L]))
    return s


def contains(ws, g):
    L = len(g)
    return any(tuple(ws[i:i + L]) == g for i in range(len(ws) - L + 1))


def history(slug):
    out = []
    for p in (os.path.join(HERE, 'data', 'word-cloud', 'ingested', slug + '.json'), os.path.join(HERE, 'data', 'edits', slug + '.json')):
        if not os.path.exists(p):
            continue
        for e in json.load(io.open(p, encoding='utf-8')).get('edits') or []:
            if e.get('op'):
                continue
            wasdm = 'class="dm"' in (e.get('wasH') or '') or (e.get('wasP') or '') == 'dh'
            if not wasdm:
                continue
            nowdm = 'class="dm"' in (e.get('nowH') or '') or (e.get('ps') == 'dh')
            if (e.get('now') or '').strip() == '' or (e.get('ps') == 'nose') or not nowdm:
                out.append({'k': e.get('k'), 't': e.get('t'), 'daf': e.get('daf'), 'was': (e.get('was') or '')[:80],
                            'now': (e.get('now') or '')[:80], 'how': 'נמחק' if not (e.get('now') or '').strip() else 'הוסב לכותרת/גוף'})
    return out


def check(slug, pages):
    src = json.load(io.open(os.path.join(HERE, 'data', 'sources', slug + '.json'), encoding='utf-8'))['pages']
    mp = os.path.join(HERE, 'data', 'mishna', slug + '.json')
    if not os.path.exists(mp):
        return None
    chap = json.load(io.open(mp, encoding='utf-8')).get('chapters') or []
    mseq = [seqs(words(' '.join(c))) for c in chap]
    # הלאוקמי: לכל עמוד - ד"ה וכותרות
    lk = collections.defaultdict(lambda: {'dh': [], 'nose': [], 'perek': None})
    for p in pages:
        k = dk(p.get('daf'))
        if k is None:
            continue
        rec = lk[k]
        rec['perek'] = rec['perek'] or perek_no(p.get('perek'))
        for u in p.get('units') or []:
            kk = u.get('k')
            if kk == 'dh':
                rec['dh'].append(words(u.get('a')))
            elif kk == 'nose':
                rec['nose'].append((words(u.get('a')), plain(u.get('a'))))
            for x in u.get('l') or []:
                cls, h = (x[0], x[1]) if isinstance(x, list) else ('', x)
                if 'dh' in (cls or '').split():
                    rec['dh'].append(words(h))
                for m in re.finditer(r'<i class="dm">(.*?)</i>', h or ''):
                    rec['dh'].append(words(m.group(1)))
            if 'dm' in (u.get('a') or '') and kk == 'nose':
                rec['dh'].append(words(u.get('a')))
    res = []
    perek_of = {}
    last = None
    for k in sorted(lk):
        if lk[k]['perek']:
            last = lk[k]['perek']
        perek_of[k] = last
    inm = False     # בתוך המשנה שבספריא (מ"מתני'" עד "גמ'"), גם על פני כמה שורות ועמודים
    for lab, v in sorted(src.items(), key=lambda kv: dk(kv[0]) or 0):
        k = dk(lab)
        for li, line in enumerate(v.get('gemara') or []):
            t = re.sub('[֑-ׇ]', '', plain(line))
            if re.match(r"^\s*מתני", t):
                inm = True
            mg = re.search(r"(?:^|\s)גמ['׳]", t)
            if inm and not mg:
                continue
            if mg:
                inm = False
                t = t[mg.end():]
                if not t.strip():
                    continue
            if k is None or k not in perek_of or not perek_of[k] or perek_of[k] > len(chap):
                continue
            pn = perek_of[k]
            S = mseq[pn - 1]
            ws = words(t)[:6]
            g = None
            for L in (4, 3, 2):
                if len(ws) >= L and tuple(ws[:L]) in S and sum(len(w) for w in ws[:L]) >= 6:
                    g = tuple(ws[:L]); break
            if not g:
                continue
            dhs = [w for kk in (k - 1, k, k + 1) for w in lk.get(kk, {'dh': []})['dh']]
            g2 = g[:2]
            if any(contains(w, g2) for w in dhs):
                st = 'dh_ok'; nose = ''
            else:
                ns = [n for kk in (k - 1, k, k + 1) for n in lk.get(kk, {'nose': []})['nose'] if contains(n[0], g2)]
                st = 'topic' if ns else 'missing'
                nose = ns[0][1] if ns else ''
            res.append({'daf': lab, 'line': li + 1, 'dh': ' '.join(g), 'gemara': re.sub('[֑-ׇ]', '', t)[:70],
                        'perek': pn, 'st': st, 'nose': nose})
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', default='')
    ap.add_argument('--rows', default='')
    a = ap.parse_args()
    book = json.load(io.open(os.path.join(HERE, 'data', 'book.json'), encoding='utf-8'))
    slugs = [s for s in book['slugs'] if not a.only or s in a.only.split(',')]
    os.makedirs(OUT, exist_ok=True)
    tot = collections.Counter()
    for s in slugs:
        try:
            pages = load_rows(s, 'book', a.rows or None)
            res = check(s, pages)
        except Exception as e:
            print('%-14s שגיאה: %s' % (s, str(e)[:120])); continue
        if res is None:
            continue
        hist = history(s)
        c = collections.Counter(r['st'] for r in res)
        tot.update(c); tot['history'] += len(hist)
        json.dump({'slug': s, 'when': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                   'count': dict(c), 'items': [r for r in res if r['st'] != 'dh_ok'], 'history': hist},
                  io.open(os.path.join(OUT, s + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('%-14s ד"ה קיים %4d | כותרת במקומו %3d | חסר %4d | בהיסטוריה %3d'
              % (s, c['dh_ok'], c['topic'], c['missing'], len(hist)))
    print('סה"כ: ד"ה קיים %d, כותרת במקומו %d, חסר %d, בהיסטוריה %d' % (tot['dh_ok'], tot['topic'], tot['missing'], tot['history']))


if __name__ == '__main__':
    main()
