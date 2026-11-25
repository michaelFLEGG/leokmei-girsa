# -*- coding: utf-8 -*-
"""p98_learn.py - לימוד לילי מסבב הגהות של מיכאל (פרומפט 98, 25.11.2026).

בכל לילה (bodkim.yml, לפני בודק השלמות): לכל מסכת שבה מיכאל ערך יותר מ-30 עריכות ב-30 השעות האחרונות,
כל עריכה מסווגת באותה שיטה שבה נותחו 174 ההגהות של קידושין ב.-יד.:
  רווח/פיסוק, ראשי תיבות, הוספת סגנון (אמוראים/פסוק/הדגשה), דובר לכותרת הצד, החלפת לשון, מבנה (איחוד/פיצול...), ניסוח.
ולכל עריכה - האם כלל קיים בפנקס כבר מסביר אותה (כיסוי).

החלפת לשון קצרה (עד 3 מילים) שחוזרת 3 פעמים ומעלה באותו יום - נכנסת לפנקס הכללים כ"כלל נלמד" (check learned_sub),
והבודק הלילי מריץ אותה מעתה על כל המסכתות (הסבב החוזר). שכבה: בינה (הצעה בתור). מוחלת לבד רק אם במבחן העיוור על
אותם דפים מיכאל עשה את ההחלפה בכל מקום שראה (90% ומעלה) ובחמישה מקומות לפחות.

דוח: data/fold/learn/<מסכת>.json (רשומה לכל לילה), ושורה ב-docs/rules-learned-log.md.

    python tools/p98_learn.py                       כל המסכתות
    python tools/p98_learn.py --only kiddushin --hours 30 --min 30
"""
import os, io, re, json, time, datetime, difflib, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
NIK = re.compile('[֑-ׇ]')
TAGS = ('p97', 'p98', 'p94int', 'by', 'dup', 'p96', 'p53')


def plain(h):
    import html as _h
    return _h.unescape(re.sub(r'<[^>]+>', '', h or '')).replace('\xa0', ' ').replace('⁠', '')


def norm(s):
    return re.sub(r'\s+', ' ', NIK.sub('', plain(s))).strip()


def michael_edits(slug, since):
    seen = {}
    for sub in (('word-cloud', 'ingested'), ('edits',)):
        p = os.path.join(ROOT, 'data', *sub, slug + '.json')
        try:
            d = json.load(io.open(p, encoding='utf-8'))
        except Exception:
            continue
        for e in d.get('edits') or []:
            if (e.get('t') or 0) < since or any(e.get(t) for t in TAGS) or str(e.get('by') or ''):
                continue
            seen[(e.get('k'), e.get('t'))] = e
    return sorted(seen.values(), key=lambda e: e['t'])


def classify(e):
    if e.get('op') == 'struct':
        return 'מבנה:' + str(e.get('kind'))
    w, n = e.get('wasH') or e.get('was') or '', e.get('nowH') or e.get('now') or ''
    pw, pn = norm(w), norm(n)
    k = str(e.get('k', '')).split('~')[0]
    if pw == pn:
        cw = set(re.findall(r'class="(\w+)"', w))
        cn = set(re.findall(r'class="(\w+)"', n))
        if re.sub(r'\s+', '', plain(w)) == re.sub(r'\s+', '', plain(n)) and plain(w) != plain(n):
            return 'רווח/פיסוק'
        return 'סגנון:' + ','.join(sorted(cn - cw) or ['שינוי'])
    if re.sub(r'[\s,.;:]', '', pw) == re.sub(r'[\s,.;:]', '', pn):
        return 'רווח/פיסוק'
    if k.endswith('.0'):
        return 'כותרת צד'
    if not pn:
        return 'מחיקה'
    if '"' in pn and len(pn) < len(pw) and re.sub(r'[^א-ת]', '', pn) and _is_abbr(pw, pn):
        return 'ראשי תיבות'
    return 'החלפת לשון' if len(subs(pw, pn)) else 'ניסוח'


def _is_abbr(a, b):
    sm = difflib.SequenceMatcher(None, a.split(), b.split(), autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == 'replace':
            frm, to = a.split()[i1:i2], b.split()[j1:j2]
            if len(to) == 1 and '"' in to[0] and len(frm) >= 2:
                return True
    return False


def subs(a, b):
    """החלפות קצרות (עד 3 מילים בכל צד) בין שני נוסחים."""
    A, B = a.split(), b.split()
    out = []
    sm = difflib.SequenceMatcher(None, A, B, autojunk=False)
    ops = sm.get_opcodes()
    if sum(1 for o in ops if o[0] != 'equal') > 3:
        return []
    for op, i1, i2, j1, j2 in ops:
        if op == 'replace' and i2 - i1 <= 3 and j2 - j1 <= 3:
            out.append((' '.join(A[i1:i2]).strip(',.:;!?'), ' '.join(B[j1:j2]).strip(',.:;!?')))
    return [x for x in out if x[0] and x[1] and x[0] != x[1]]


def covered(e, led_mech):
    w, n = e.get('wasH') or '', e.get('nowH') or ''
    if not w:
        return None
    import p98_rules as R
    for rid, f in led_mech.items():
        if f(w) != w and R._agrees(f, w, n):
            return rid
    return None


def blind_sub(pages_daf, frm, to):
    """בכמה מן השורות שבדפים שמיכאל ערך עדיין מופיע frm (כלומר ראה ולא החליף)."""
    rx = re.compile(r'(?<![א-ת])' + re.escape(frm) + r'(?![א-ת])')
    return sum(1 for t in pages_daf if rx.search(t))


def main():
    import sys, argparse
    sys.path.insert(0, HERE)
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', default='')
    ap.add_argument('--hours', type=int, default=30)
    ap.add_argument('--min', type=int, default=30)
    ap.add_argument('--dry', action='store_true')
    a = ap.parse_args()
    import p98_rules as R
    book = json.load(io.open(os.path.join(ROOT, 'data', 'book.json'), encoding='utf-8'))
    slugs = [s for s in book['slugs'] if not a.only or s in a.only.split(',')]
    since = int(time.time() * 1000) - a.hours * 3600 * 1000
    ledp = os.path.join(ROOT, 'docs', 'rules-ledger.json')
    led = json.load(io.open(ledp, encoding='utf-8'))
    mech = {r['id']: R.MECH[r['id']] for r in led['rules'] if r['id'] in R.MECH}
    today = datetime.date.today().isoformat()
    new_rules = []
    for s in slugs:
        eds = michael_edits(s, since)
        if len(eds) <= a.min:
            continue
        cls = collections.Counter()
        cov = collections.Counter()
        pairs = collections.Counter()
        exs = {}
        for e in eds:
            c = classify(e)
            cls[c] += 1
            r = covered(e, mech)
            if r:
                cov[r] += 1
            if c in ('החלפת לשון', 'ראשי תיבות'):
                for fr, to in subs(norm(e.get('was')), norm(e.get('now'))):
                    pairs[(fr, to)] += 1
                    exs.setdefault((fr, to), (e.get('daf'), norm(e.get('was'))[:100], norm(e.get('now'))[:100]))
        cand = []
        known = {(r.get('from'), r.get('to')) for r in led['rules'] if r.get('check') == 'learned_sub'}
        dafs = sorted({e.get('daf') for e in eds if e.get('daf')})
        lines = []
        try:
            import mishna_check as MC
            pages = MC.pages_of(s, True)
            for pg in pages:
                if pg.get('daf') in dafs:
                    for u in pg.get('units') or []:
                        if u.get('k') == 'u':
                            lines += [norm(l[1]) for l in u.get('l') or [] if len(l) > 1]
        except Exception as ex:
            print(s, 'אין דפים לעיוור:', ex)
        for (fr, to), n in pairs.most_common():
            if n < 3 or (fr, to) in known or len(fr) < 2:
                continue
            left = blind_sub(lines, fr, to) if lines else None
            pct = round(100.0 * n / (n + left), 1) if left is not None else None
            ap_ = bool(pct is not None and pct >= 90 and n >= 5)
            rid = 'L%s-%s-%d' % (today.replace('-', ''), s[:6], len(cand) + 1)
            cand.append({'id': rid, 'from': fr, 'to': to, 'n': n, 'left_unchanged': left, 'pct': pct, 'apply': ap_, 'ex': exs[(fr, to)]})
            new_rules.append({'id': rid, 'date': today, 'check': 'learned_sub', 'layer': 'מכני' if ap_ else 'בינה', 'apply': ap_,
                              'src': 'לימוד לילי מהגהות מיכאל ב-%s (%d עריכות)' % (s, len(eds)), 'from': fr, 'to': to,
                              'text': '"%s" -> "%s" (מיכאל החליף %d פעמים, השאיר %s; %s%%)' % (fr, to, n, left, pct)})
        rec = {'when': today, 'edits': len(eds), 'dafs': dafs, 'classes': dict(cls), 'covered_by_rules': dict(cov),
               'candidates': cand}
        p = os.path.join(ROOT, 'data', 'fold', 'learn', s + '.json')
        os.makedirs(os.path.dirname(p), exist_ok=True)
        doc = json.load(io.open(p, encoding='utf-8')) if os.path.exists(p) else {'slug': s, 'runs': []}
        doc['runs'] = [x for x in doc['runs'] if x.get('when') != today] + [rec]
        if not a.dry:
            io.open(p, 'w', encoding='utf-8', newline='\n').write(json.dumps(doc, ensure_ascii=False, indent=1) + '\n')
        print('%-14s %d עריכות, כיסוי כללים %d, כללים חדשים %d  %s' % (s, len(eds), sum(cov.values()), len(cand), dict(cls)))
        logp = os.path.join(ROOT, 'docs', 'rules-learned-log.md')
        if not a.dry:
            with io.open(logp, 'a', encoding='utf-8', newline='\n') as f:
                f.write('- %s %s: %d עריכות של מיכאל; %s; כללים חדשים: %s\n' % (
                    today, s, len(eds), ', '.join('%s %d' % kv for kv in cls.most_common(6)),
                    '; '.join('"%s"->"%s" (%d)' % (c['from'], c['to'], c['n']) for c in cand) or 'אין'))
    if new_rules and not a.dry:
        s_ = io.open(ledp, encoding='utf-8').read().rstrip()
        body = s_.rstrip('}').rstrip().rstrip(']').rstrip()
        s_ = body + ',\n' + ',\n'.join('  ' + json.dumps(r, ensure_ascii=False) for r in new_rules) + '\n ]\n}\n'
        json.loads(s_)
        io.open(ledp, 'w', encoding='utf-8', newline='\n').write(s_)


if __name__ == '__main__':
    main()
