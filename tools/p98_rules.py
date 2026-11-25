# -*- coding: utf-8 -*-
"""p98_rules.py - כללים שנגזרו מ-174 ההגהות של מיכאל בקידושין ב.-יד. (פרומפט 98, 25.11.2026).

כל כלל כאן רשום בפנקס הכללים (docs/rules-ledger.json) עם check שמפנה לפונקציה כאן (נרשמות ב-CHECKS של
tools/rules_ledger.py). שני סוגים:
  מכני  - fix_<כלל>(html) מחזיר את השורה המתוקנת. מוחל בשכבה (apply true) רק אם עבר את מבחן העיוור (70%).
  בינה  - בדיקה בלבד: השורות נרשמות בתור (data/fold/rules-ledger-hits.json, data/fold/p98-queue/<מסכת>.json).

כלל הזהב: שורה שמיכאל ערך אינה נוגעת (hot - מפתחות ונוסחים מ-speaker_to_side.recent_hot). משנה אינה נוגעת
(רק יחידות k == 'u'). כלל הדובר הוא של פרומפט 97 (כלל 17) ואינו כפול כאן.

    python tools/p98_rules.py blind                     מבחן העיוור על ב.-יד. בקידושין
    python tools/p98_rules.py apply --only kiddushin    החלת המכניים שעברו בשכבה (בלי שורות שמיכאל ערך)
    python tools/p98_rules.py queue --only kiddushin    תור הבינה (בלי החלה)
"""
import os, io, re, json, html as _html

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
NIK = re.compile('[֑-ׇ]')
HEB = 'א-ת'


def plain(h):
    return _html.unescape(re.sub(r'<[^>]+>', '', h or '')).replace('\xa0', ' ').replace('⁠', '')


def _text_sub(h, rx, rep):
    """החלפה רק בטקסט שבין התגיות (לא בתוך תגית)."""
    parts = re.split(r'(<[^>]+>)', h)
    return ''.join(p if p.startswith('<') else rx.sub(rep, p) for p in parts)


# ------------------------------------------------------------------ כללים מכניים
# p98a: רווח אחרי פסיק. מיכאל הוסיף רווח אחרי פסיק צמוד בכל מקום שראה (13 מקרים, אף לא אחד הפוך).
RX_COMMA = re.compile(r'(?<=[%s"\'\)\]]),(?=[%s\'])' % (HEB, HEB))


def fix_comma_space(h):
    # גם פסיק בסוף קטע מעוצב שהמילה הבאה צמודה אליו אחרי התגית: ",</i>X"
    h2 = _text_sub(h, RX_COMMA, ', ')
    h2 = re.sub(r'(?<=[%s"\']),(</i>)(?=[%s\'])' % (HEB, HEB), r',\1 ', h2)
    return h2


# p98b: ראשי תיבות קבועים במקום המילים המלאות: "כל שכן" -> כ"ש, "אין צריך" -> א"צ.
ABBR = [(re.compile(r'(?<![%s])(ו?)כל שכן(?![%s])' % (HEB, HEB)), r'\1כ"ש'),
        (re.compile(r'(?<![%s])(ו?)אין צריך(?![%s])' % (HEB, HEB)), r'\1א"צ')]


def fix_abbr(h):
    for rx, rep in ABBR:
        h = _text_sub(h, rx, rep)
    return h


# p98c: "לא נצרך אלא ל..." -> "מיירי ל..." (2 מתוך 2).
RX_NITZRACH = re.compile(r'(?<![%s])(ו?)לא נצרך אלא ל' % HEB)


def fix_miyiri(h):
    return _text_sub(h, RX_NITZRACH, lambda m: ('ו' if m.group(1) else '') + 'מיירי ל')


# p98d: נוסחת מקור בלי סגנון אמוראים -> סגנון אמוראים (כדתניא:, מדתניא:, דתניא:, דתנן:, כדתנן:,
#        שהרי אמרו חכמים:). רק כשהנוסחה אינה כבר בתוך תגית.
SRC_FORM = r'(?:(?:למד (?:עוד )?)?ו?(?:כ|מ)?ד(?:תניא|תנן)|שהרי אמרו חכמים)'
RX_SRC = re.compile(r'(?<![%s"\'])(%s:)(?=\s)' % (HEB, SRC_FORM))


def fix_src_style(h):
    parts = re.split(r'(<[^>]+>)', h)
    out, depth = [], 0
    for p in parts:
        if p.startswith('<'):
            if p.startswith('</'):
                depth = max(0, depth - 1)
            elif not p.endswith('/>') and not p.startswith('<br'):
                depth += 1
            out.append(p)
            continue
        out.append(RX_SRC.sub(r'<i class="am">\1</i>', p) if depth == 0 else p)
    return ''.join(out)


MECH = {'p98a': fix_comma_space, 'p98b': fix_abbr, 'p98c': fix_miyiri, 'p98d': fix_src_style}

# ------------------------------------------------------------------ כללי בינה (בדיקה בלבד)
RX_KAL = re.compile(r'(לא כ"ש\s*\?|אינו דין ש[^?]*\?|לא כל שכן\s*\?)')
RX_TZRICH = re.compile(r'(אם השמיענו|הייתי אומר:[^.]*קמ"ל|^ו?אם רק )')
RX_HAIM = re.compile(r'(?<![%s])האם(?![%s])' % (HEB, HEB))
RX_MI = re.compile(r'^\S+(?: \S+)? מ(?:ר"|רב|רבי|ר\')\S*:$')
RX_CIT = re.compile(r'(?<![%s])[דמכ]\'[%s][^\'<]{1,40}\'' % (HEB, HEB))


def _unstyled(h, rx):
    """התאמה בטקסט שאינו בתוך תגית כלשהי."""
    parts = re.split(r'(<[^>]+>)', h)
    depth = 0
    for p in parts:
        if p.startswith('<'):
            if p.startswith('</'):
                depth = max(0, depth - 1)
            elif not p.startswith('<br'):
                depth += 1
            continue
        if depth == 0 and rx.search(p):
            return True
    return False


def side_of(u):
    return NIK.sub('', plain(u.get('a') or '')).strip()


def sem_hits(pages):
    """{rule_id: [hit]} לכללי הבינה."""
    out = {k: [] for k in ('p98e', 'p98f', 'p98g', 'p98h', 'p98i', 'p98j')}
    for pg in pages:
        us = [u for u in pg.get('units') or [] if u.get('k') == 'u']
        for u in us:
            daf = pg.get('daf')
            a = side_of(u)
            ls = u.get('l') or []
            if a in ('והרי', 'והרי:'):
                out['p98g'].append({'daf': daf, 'ek': 'u%s.0' % u.get('id'), 't': a + ' | ' + plain(ls[0][1] if ls else '')[:100]})
            if RX_HAIM.search(a):
                out['p98h'].append({'daf': daf, 'ek': 'u%s.0' % u.get('id'), 't': a})
            if RX_MI.match(a):
                out['p98i'].append({'daf': daf, 'ek': 'u%s.0' % u.get('id'), 't': a})
            for n, l in enumerate(ls):
                h = l[1] if len(l) > 1 else ''
                t = NIK.sub('', plain(h))
                ek = 'u%s.%d' % (u.get('id'), n + 1)
                if RX_KAL.search(t):
                    out['p98e'].append({'daf': daf, 'ek': ek, 't': t[:140]})
                if RX_TZRICH.search(t):
                    out['p98f'].append({'daf': daf, 'ek': ek, 't': t[:140]})
                if _unstyled(h, RX_CIT):
                    out['p98j'].append({'daf': daf, 'ek': ek, 't': t[:140]})
    return out


def mech_hits(pages, rid):
    f = MECH[rid]
    out = []
    for pg in pages:
        for u in pg.get('units') or []:
            if u.get('k') != 'u':
                continue
            for n, l in enumerate(u.get('l') or []):
                h = l[1] if len(l) > 1 else ''
                h2 = f(h)
                if h2 != h:
                    out.append({'daf': pg.get('daf'), 'ek': 'u%s.%d' % (u.get('id'), n + 1), 't': plain(h)[:140],
                                'certain': True, '_h': h, '_h2': h2})
    return out


def learned_fix(frm, to):
    rx = re.compile(r'(?<![%s])' % HEB + re.escape(frm) + r'(?![%s])' % HEB)
    return lambda h: _text_sub(h, rx, to.replace('\\', '\\\\'))


def learned_check(frm, to):
    """כלל שנלמד בלילה (tools/p98_learn.py): החלפת לשון קצרה."""
    f = learned_fix(frm, to)

    def chk(pages, hot=()):
        out = []
        for pg in pages:
            for u in pg.get('units') or []:
                if u.get('k') != 'u':
                    continue
                for n, l in enumerate(u.get('l') or []):
                    h = l[1] if len(l) > 1 else ''
                    if f(h) != h:
                        out.append({'daf': pg.get('daf'), 'ek': 'u%s.%d' % (u.get('id'), n + 1), 't': plain(h)[:140], 'certain': True})
        return out
    return chk


def check_for(rid):
    if rid in MECH:
        return lambda pages, hot=(): mech_hits(pages, rid)
    return lambda pages, hot=(): sem_hits(pages)[rid]


# ------------------------------------------------------------------ מבחן העיוור
DAF_ORDER = None


def _dnum(daf):
    import daf_check as D
    try:
        return D.dk(daf)
    except Exception:
        return None


def norm(s):
    return re.sub(r'\s+', ' ', NIK.sub('', plain(s))).strip()


def blind(pages, edits, lo='ב.', hi='יד:'):
    """לכל כלל מכני: בכמה מקומות הוא היה פועל על ב.-יד. (לפני העריכות של מיכאל), ובכמה מהם מיכאל עשה אותו דבר.
    שורה שמיכאל לא נגע בה (הוא עבר על כל ב.-יד.) - פעולה של הכלל עליה היא שגיאה (הוא ראה ולא שינה).
    לכללי בינה: כמה מן הסימונים נפלו על שורה שמיכאל אכן שינה (התאמה), וכמה מעריכותיו מסוג זה הכלל תופס."""
    k0, k1 = _dnum(lo), _dnum(hi)
    txt_eds = [e for e in edits if e.get('op') != 'struct' and (e.get('wasH') or e.get('was'))]
    # מצב "לפני": שורות הספר הנוכחי, ובמקום שורה שמיכאל ערך - ה-was של העריכה הראשונה שלו עליה.
    now2was = {}
    for e in sorted(txt_eds, key=lambda e: e['t'], reverse=True):
        n = norm(e.get('nowH') or e.get('now'))
        if n:
            w = e.get('wasH') or e.get('was') or ''
            now2was[n] = (w, e)
    # שרשור: was של עריכה מאוחרת יכול להיות now של קודמת
    lines = []
    for pg in pages:
        kd = _dnum(pg.get('daf'))
        if kd is None or not (k0 <= kd <= k1):
            continue
        for u in pg.get('units') or []:
            if u.get('k') != 'u':
                continue
            for n, l in enumerate(u.get('l') or []):
                h = l[1] if len(l) > 1 else ''
                key = norm(h)
                before, touched = h, False
                seen = 0
                while key in now2was and seen < 6:
                    before, _e = now2was[key]
                    touched = True
                    key = norm(before)
                    seen += 1
                lines.append((pg.get('daf'), before, h, touched))
    # גם עריכות שהשורה שלהן כבר אינה בספר (מוזגה) - was מול now
    res = {}
    for rid, f in MECH.items():
        fire = agree = 0
        ex_ok, ex_bad = [], []
        for daf, before, after, touched in lines:
            b2 = f(before)
            if b2 == before:
                continue
            fire += 1
            # הסכמה: מה שהכלל משנה מופיע גם אחרי העריכה של מיכאל (השינוי שלו מכיל את שינוי הכלל)
            ok = touched and _agrees(f, before, after)
            if ok:
                agree += 1
                ex_ok.append((daf, norm(before)[:90], norm(after)[:90]))
            else:
                ex_bad.append((daf, norm(before)[:90], norm(after)[:90], touched))
        # כיסוי: מתוך העריכות של מיכאל שהכלל היה עושה בהן משהו - כמה הוא תופס
        caught = sum(1 for e in txt_eds if f(e.get('wasH') or '') != (e.get('wasH') or '') and _agrees(f, e.get('wasH') or '', e.get('nowH') or ''))
        res[rid] = {'fire': fire, 'agree': agree, 'pct': round(100.0 * agree / fire, 1) if fire else None,
                    'caught_in_edits': caught, 'ok': ex_ok[:6], 'bad': ex_bad[:8]}
    # בינה
    sem_before = sem_hits([{'daf': d, 'units': [{'k': 'u', 'id': i, 'a': '', 'l': [['', b]]}]} for i, (d, b, a, t) in enumerate(lines)])
    for rid, hits in sem_before.items():
        if rid in ('p98g', 'p98h', 'p98i'):
            continue
        idx = [int(h['ek'][1:].split('.')[0]) for h in hits]
        agree = sum(1 for i in idx if lines[i][3] and norm(lines[i][1]) != norm(lines[i][2]))
        res[rid] = {'fire': len(idx), 'agree': agree, 'pct': round(100.0 * agree / len(idx), 1) if idx else None,
                    'bad': [(lines[i][0], norm(lines[i][1])[:90]) for i in idx if not lines[i][3]][:6]}
    # כותרות צד: was/now של עריכות .0
    side_eds = [e for e in txt_eds if str(e['k']).split('~')[0].endswith('.0')]
    for rid, rx in (('p98g', re.compile(r'^והרי:?$')), ('p98h', RX_HAIM), ('p98i', RX_MI)):
        hit = [e for e in side_eds if rx.search(norm(e.get('was') or ''))]
        changed = [e for e in hit if norm(e.get('now')) != norm(e.get('was'))]
        res[rid] = {'fire_in_edits': len(hit), 'changed': len(changed),
                    'ex': [(e['daf'], norm(e['was']), norm(e['now'])) for e in hit][:8]}
    return res


def _agrees(f, before, after):
    """הכלל מסכים עם מיכאל אם כל מה שהכלל משנה קיים גם בנוסח של מיכאל: מחשבים את 'אחרי' שהכלל היה מפיק,
    ובודקים שהחלק שהשתנה (בטקסט הנקי, בלי רווחים כפולים) מופיע בנוסח של מיכאל."""
    import difflib
    b, r, m = norm(before), norm(f(before)), norm(after)
    if f is fix_src_style:
        # עיצוב: בודקים שהנוסחה בסגנון אמוראים גם אצל מיכאל
        forms = [x.group(1) for x in RX_SRC.finditer(plain(before))]
        return all(re.search(r'<i class="am">[^<]*' + re.escape(x), after) for x in forms) and bool(forms)
    sm = difflib.SequenceMatcher(None, b, r, autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == 'equal':
            continue
        ctx = r[max(0, j1 - 6):j2 + 6]
        if ctx not in m:
            return False
    return True


# ------------------------------------------------------------------ החלה
def apply_edits(slug, pages, rids, hot, t0, tag='p98', skip=()):
    keys, texts = hot if isinstance(hot, tuple) else (set(hot), set())
    out, skipped = [], 0
    t = t0
    for pg in pages:
        for u in pg.get('units') or []:
            if u.get('k') != 'u':
                continue
            for n, l in enumerate(u.get('l') or []):
                h = l[1] if len(l) > 1 else ''
                h2 = h
                why = []
                for rid in rids:
                    x = MECH[rid](h2)
                    if x != h2:
                        why.append(rid)
                        h2 = x
                if h2 == h:
                    continue
                ek = 'u%s.%d' % (u.get('id'), n + 1)
                if ek in skip:
                    continue
                if ek in keys or ('u%s' % u.get('id')) in keys or re.sub(r'\s+', ' ', plain(h)).strip() in texts:
                    skipped += 1
                    continue
                t += 1
                out.append({'k': '%s~%d' % (ek, t), 't': t, 'was': plain(h), 'now': plain(h2), 'wasH': h, 'nowH': h2,
                            'daf': pg.get('daf') or '', 'wasP': '', tag: {'rules': why, 'why': 'כללי הגהות מיכאל (פרומפט 98)'}})
    return out, skipped


def main():
    import sys, argparse, time, pickle
    sys.path.insert(0, HERE)
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['blind', 'apply', 'queue'])
    ap.add_argument('--only', default='')
    ap.add_argument('--pages', default='')
    ap.add_argument('--edits', default='')
    ap.add_argument('--rules', default='')
    ap.add_argument('--dry', action='store_true')
    a = ap.parse_args()
    import mishna_check as MC
    book = json.load(io.open(os.path.join(ROOT, 'data', 'book.json'), encoding='utf-8'))
    slugs = [s for s in book['slugs'] if not a.only or s in a.only.split(',')]
    if a.cmd == 'blind':
        pages = pickle.load(open(a.pages, 'rb')) if a.pages else MC.pages_of('kiddushin', True)
        eds = json.load(io.open(a.edits, encoding='utf-8'))
        print(json.dumps(blind(pages, eds), ensure_ascii=False, indent=1))
        return
    led = json.load(io.open(os.path.join(ROOT, 'docs', 'rules-ledger.json'), encoding='utf-8'))
    rules = {r['id']: r for r in led['rules']}
    rids = a.rules.split(',') if a.rules else [k for k in MECH if (rules.get(k) or {}).get('apply')]
    import speaker_to_side as S
    summary = {}
    for s in slugs:
        try:
            pages = pickle.load(open(a.pages, 'rb')) if a.pages else MC.pages_of(s, True)
        except Exception as e:
            print(s, 'שגיאה', e)
            continue
        if a.cmd == 'queue':
            q = sem_hits(pages)
            p = os.path.join(ROOT, 'data', 'fold', 'p98-queue', s + '.json')
            os.makedirs(os.path.dirname(p), exist_ok=True)
            io.open(p, 'w', encoding='utf-8', newline='\n').write(json.dumps(
                {'slug': s, 'about': 'תור הצעות לכללי הבינה של פרומפט 98 (לסבב ממוקד, רק השורות האלה)',
                 'rules': {k: rules.get(k, {}).get('text', '') for k in q}, 'hits': q}, ensure_ascii=False, indent=1) + '\n')
            summary[s] = {k: len(v) for k, v in q.items()}
            print('%-14s %s' % (s, '  '.join('%s %d' % (k, len(v)) for k, v in q.items())))
            continue
        hot = S.recent_hot(s, 24 * 30)
        eds, skipped = apply_edits(s, pages, rids, hot, int(time.time() * 1000))
        summary[s] = {'edits': len(eds), 'skipped_hot': skipped}
        print('%-14s עריכות %d, דולגו (מיכאל ערך) %d' % (s, len(eds), skipped))
        if eds and not a.dry:
            p = os.path.join(ROOT, 'data', 'edits', s + '.json')
            doc = json.load(io.open(p, encoding='utf-8')) if os.path.exists(p) else {'v': 1, 'slug': s, 'edits': []}
            have = {S.sig(e) for e in doc.get('edits') or [] if e.get('p98')}
            new = [e for e in eds if S.sig(e) not in have]
            doc['edits'] = (doc.get('edits') or []) + new
            io.open(p, 'w', encoding='utf-8', newline='\n').write(json.dumps(doc, ensure_ascii=False, indent=1))
    rp = os.path.join(ROOT, 'data', 'fold', 'p98-%s.json' % a.cmd)
    old = json.load(io.open(rp, encoding='utf-8')) if os.path.exists(rp) else {}
    old.update(summary)
    io.open(rp, 'w', encoding='utf-8', newline='\n').write(json.dumps(old, ensure_ascii=False, indent=1) + '\n')


if __name__ == '__main__':
    main()
