# -*- coding: utf-8 -*-
"""rules_ledger.py - פנקס הכללים: בדיקה לכל כלל, וסבב חוזר על כל המסכתות (פרומפט 97, 25.11.2026).

שורש התופעה שמיכאל מגלה שוב ושוב: כל כלל חדש נכנס לסכם "מעתה והלאה", ואין שום מנגנון שחוזר אחורה
על מסכתות שכבר עברו סכם. הפנקס (docs/rules-ledger.json) רושם כל כלל עם פונקציית בדיקה שמזהה הפרה שלו,
ובודק השלמות הלילי (tools/integrity_check.py) מריץ את כולן על כל המסכתות, בכל לילה:
  - כלל מכני (layer "מכני", apply true): הוודאיים נכתבים לשכבה מיד (חוץ מיחידה שמיכאל ערך ב-24 שעות).
  - כלל של בינה (layer "בינה"): רק מסומן - השורות נרשמות בדוח כתור לסבב חסכוני (רק השורות האלה, לא סכם מלא).
טבלת הכיסוי (data/fold/rules-coverage.json): לכל כלל ולכל מסכת - מספר הפרות, ומתי הוחל.

כלל חדש = שורה בפנקס + פונקציה כאן. בלי פונקציה - הכלל מופיע בדוח כ"אין בדיקה מכנית", כדי שהחוסר ייראה.

    python tools/rules_ledger.py --only kiddushin,bava-kamma        דוח (וטבלת כיסוי)
    python tools/rules_ledger.py --only kiddushin --apply           וגם החלת המכניים בשכבה
"""
import os, io, re, json, html as _html

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LEDGER = os.path.join(ROOT, 'docs', 'rules-ledger.json')
COVER = os.path.join(ROOT, 'data', 'fold', 'rules-coverage.json')
NIK = re.compile('[֑-ׇ]')


def plain(h):
    return _html.unescape(re.sub(r'<[^>]+>', '', h or '')).replace('\xa0', ' ').replace('⁠', '')


def units(pages):
    for pg in pages:
        for u in pg.get('units') or []:
            yield pg, u


def body_lines(pages):
    """(daf, ek, html, טקסט) לכל שורת גוף (לא משנה)."""
    for pg, u in units(pages):
        if u.get('k') != 'u':
            continue
        for n, l in enumerate(u.get('l') or []):
            h = l[1] if len(l) > 1 else ''
            yield pg.get('daf'), 'u%s.%d' % (u.get('id'), n + 1), h, NIK.sub('', plain(h))


def hit(daf, ek, t, extra=None):
    d = {'daf': daf, 'ek': ek, 't': (t or '')[:140]}
    if extra:
        d.update(extra)
    return d


# ------------------------------------------------------------------ פונקציות הבדיקה

def chk_speaker_side(pages, hot=()):
    import speaker_to_side as S
    out = []
    for r in S.scan(pages, hot):
        out.append(hit(r['daf'], 'u%s.1' % r['id'], r['line'], {'certain': r['certain'], 'why': r['why'] or ('נערך לאחרונה' if r['held'] else ''),
                                                               'side': r['side'], 'x': r['x'], '_r': r}))
    return out


LINKW = {'והא', 'ת"ש', 'והך', 'והרי', 'שהרי', 'מיתיבי', 'איתיביה', 'ורמינהו', 'ויקשה', 'וקשה', 'קשה', 'אלא', 'שאני'}


def chk_side_len(pages, hot=()):
    """כותרת צד = עוגן קצר, עד שתי מילים; שלוש רק דובר + מילת מהלך (9.11.2026). מקף, מספור ונקודתיים אינם נספרים."""
    out = []
    for pg, u in units(pages):
        if u.get('k') != 'u' or not u.get('a'):
            continue
        t = plain(u['a']).strip()
        t = re.sub(r'^[-־–]\s*', '', t)
        t = re.sub(r'^[א-י]\.\s*', '', t).rstrip(':').strip()
        w = t.split()
        if len(w) > 3 or (len(w) == 3 and not (set(w) & LINKW)):
            out.append(hit(pg.get('daf'), 'u%s.0' % u.get('id'), plain(u['a'])))
    return out


def rx_check(rx, skip=None):
    R = re.compile(rx)
    S = re.compile(skip) if skip else None

    def f(pages, hot=()):
        return [hit(d, ek, t) for d, ek, h, t in body_lines(pages) if R.search(t) and not (S and S.search(t))]
    return f


def chk_num_space(pages, hot=()):
    """כלל 49: אחרי אות מספור בסגנון אמוראים רווח אחד בדיוק ("ה. ר"ג", לא "ה.ר"ג")."""
    out = []
    for d, ek, h, t in body_lines(pages):
        for m in re.finditer(r'<i class="am">([^<]*)</i>', h):
            if re.match(r'^\s*[א-י]\.[א-ת]', plain(m.group(1))):
                out.append(hit(d, ek, t, {'certain': True, 'span': m.group(0)}))
    return out


def chk_lrt_colon(pages, hot=()):
    """לר"ת: עם נקודתיים (דובר בסגנון אמוראים לפני שיטתו)."""
    out = []
    for d, ek, h, t in body_lines(pages):
        for m in re.finditer(r'<i class="am">([^<]*)</i>', h):
            s = plain(m.group(1)).strip()
            if re.fullmatch(r'ו?לר"ת', s):
                out.append(hit(d, ek, t))
    return out


CHECKS = {
    'speaker_side': chk_speaker_side,
    'side_len': chk_side_len,
    'lashon_acher': rx_check(r'(^|[\s(\[])ו?ל?לשון אחרת(?=[\s:,.]|$)'),
    'nafkam': rx_check(r'(^|[\s(\[])(ו?יש ביניהם|ומה ביניהם|מה ביניהם)(?=[\s:,.?]|$)'),
    'tanan_sham': rx_check(r'(^|[\s(\[])ו?שנינו שם(?=[\s:,.]|$)'),
    'chalku': rx_check(r'(^|[\s(\[])(ו?פליגי|ופליג|פליג)(?=[\s:,.]|$)'),
    'shani_kan': rx_check(r'(^|[\s(\[])(ו?שאני הכא|ו?שאני התם)(?=[\s:,.]|$)'),
    'num_space': chk_num_space,
    'lrt_colon': chk_lrt_colon,
}


def ledger():
    return json.load(io.open(LEDGER, encoding='utf-8'))


def run(slug, pages, hot=()):
    """מחזיר {rule_id: [hits]} לכל כלל בפנקס שיש לו בדיקה."""
    res = {}
    for r in ledger()['rules']:
        f = CHECKS.get(r.get('check') or '')
        if not f:
            continue
        try:
            res[r['id']] = f(pages, hot)
        except Exception as e:
            res[r['id']] = [{'error': str(e)[:200]}]
    return res


def mech_edits(slug, res, t0):
    """העריכות של הכללים המכניים (הוודאיים בלבד)."""
    import speaker_to_side as S
    eds = []
    rules = {r['id']: r for r in ledger()['rules']}
    for rid, hits in res.items():
        r = rules.get(rid) or {}
        if not r.get('apply'):
            continue
        if r.get('check') == 'speaker_side':
            e = S.edits_for([h['_r'] for h in hits if h.get('certain')], t0 + len(eds) * 3 + 1)
            eds += e
    return eds


def cover_update(slug, res, applied):
    import datetime
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    cov = json.load(io.open(COVER, encoding='utf-8')) if os.path.exists(COVER) else {'rules': {}}
    for rid, hits in res.items():
        c = cov['rules'].setdefault(rid, {})
        old = c.get(slug) or {}
        c[slug] = {'when': now, 'violations': len([h for h in hits if not h.get('error')]),
                   'certain': len([h for h in hits if h.get('certain')]),
                   'applied': applied.get(rid, 0), 'last_applied': now if applied.get(rid) else old.get('last_applied'),
                   'first': old.get('first', len(hits))}
    cov['when'] = now
    os.makedirs(os.path.dirname(COVER), exist_ok=True)
    io.open(COVER, 'w', encoding='utf-8', newline='\n').write(json.dumps(cov, ensure_ascii=False, indent=1) + '\n')
    return cov


def strip_private(res):
    return {k: [{kk: vv for kk, vv in h.items() if not kk.startswith('_')} for h in v] for k, v in res.items()}


def main():
    import sys, argparse, time
    sys.path.insert(0, HERE)
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', default='')
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--pages', default='')
    a = ap.parse_args()
    import mishna_check as MC
    from dup_lines import hot_keys
    book = json.load(io.open(os.path.join(ROOT, 'data', 'book.json'), encoding='utf-8'))
    slugs = [s for s in book['slugs'] if not a.only or s in a.only.split(',')]
    repp = os.path.join(ROOT, 'data', 'fold', 'rules-ledger-hits.json')
    rep = json.load(io.open(repp, encoding='utf-8')) if os.path.exists(repp) else {'masechtot': {}}
    for s in slugs:
        try:
            if a.pages:
                import pickle
                pages = pickle.load(open(a.pages, 'rb'))
            else:
                pages = MC.pages_of(s, True)
        except Exception as e:
            print(s, 'שגיאה', e)
            continue
        import speaker_to_side as _S
        hot = _S.recent_hot(s, 24)
        res = run(s, pages, hot)
        applied = {}
        if a.apply:
            eds = mech_edits(s, res, int(time.time() * 1000))
            if eds:
                p = os.path.join(ROOT, 'data', 'edits', s + '.json')
                doc = json.load(io.open(p, encoding='utf-8')) if os.path.exists(p) else {'v': 1, 'slug': s, 'edits': []}
                have = {str(e.get('wasH')) + '|' + str(e.get('k', '')).split('~')[0] for e in doc.get('edits') or [] if e.get('p97')}
                new = [e for e in eds if e['wasH'] + '|' + e['k'].split('~')[0] not in have]
                doc['edits'] = (doc.get('edits') or []) + new
                io.open(p, 'w', encoding='utf-8', newline='\n').write(json.dumps(doc, ensure_ascii=False, indent=1))
                applied['speaker_side'] = len(new) // 2
        cover_update(s, res, applied)
        rep['masechtot'][s] = strip_private(res)
        print('%-14s %s' % (s, '  '.join('%s %d' % (k, len(v)) for k, v in res.items())), ('  הוחלו: %s' % applied) if applied else '')
    io.open(repp, 'w', encoding='utf-8', newline='\n').write(json.dumps(rep, ensure_ascii=False, indent=1) + '\n')


if __name__ == '__main__':
    main()
