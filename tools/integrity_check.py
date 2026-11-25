# -*- coding: utf-8 -*-
"""integrity_check.py - בודק השלמות (פרומפט 94, 25.11.2026). מכני, בלי בינה מלאכותית.

נולד משבת פרק הבונה: "קבל הכל" בכפייה (18.11.2026) החיל הצעות סכם שנכתבו על נוסח אחר, שורה לפי מספר שורה,
ונוצרו ארבעה דפוסים. הבודק מחפש אותם בכל מסכת, בדף כפי שהמנהל רואה אותו (הספר + השכבה):

  head_line   - כותרת (נושא/ד"ה, או כותרת הצד של היחידה הבאה) שמופיעה גם כשורה שלמה מיד לפניה.  ודאי: השורה נמחקת.
  head_tail   - שורה שמסתיימת במילות הכותרת שאחריה ("שחייב משום / הקודח כל שהוא").            ספק: לעיון.
  side_repeat - כותרת צד שחוזרת בתחילת השורה שתחתיה ("בני רחבה:" / "בני רחבה: א"כ...").      ודאי כשהכותרת 2 מילים ומעלה ומסתיימת בנקודתיים: הכפילות נמחקת מן השורה.
  bracket_dup - שתי שורות סמוכות שזהות אחרי הסרת [סוגריים] ("מטיף לתוכו אבר [עופרת]." / "מטיף לתוכו אבר.").  ודאי: הקצרה נמחקת.
  far_dup     - שורה של 6 מילים ומעלה שזהה לשורה במרחק 16 יחידות ומעלה (שורה תלושה), שאינה "גופא", משנה או ציטוט מנוקד.  ספק: לעיון.
  empty_side  - כותרת צד ריקה (רק רווח או סימן).                                                  ספק: לעיון.
(שורה כפולה רגילה ושארית פיצול - tools/dup_lines.py, שרץ באותו לילה. עוגני תוס' - tools/tosafot/anchor_check.py.)

ובנוסף, בכל מסכת שיש לה תוס' (פרומפט 96, 25.11.2026; tools/tosafot/tos_anchor_lib.tos_check):
  tos noanchor  - תוס' שהעוגן שלה אינו נמצא בעמוד (גם לא במקורב).                       ודאי: לתקן ב-reanchor.py.
  tos wrongpage - העמוד שהאתר מחפש בו שונה מעמוד התוס' לפי ספריא. ודאי כשהעוגן/הד"ה נמצאים בעמוד הנכון, אחרת ספק.
  tos order     - שני סימנים סמוכים באותו עמוד שסדרם בטקסט הפוך ממספרם.                ודאי: לתקן ב-reanchor.py.
התיקון עצמו (tools/tosafot/reanchor.py) צריך את שיוך היחידות לפרק מן הדפדפן, ולכן אינו רץ כאן בלילה: הבודק רושם,
והדוח (data/fold/integrity.json, המפתח tos) מראה מה לתקן.

שורה או יחידה שמיכאל ערך ב-12 השעות האחרונות - לא נוגעים (ייתכן שהוא באמצע), נרשמת לעיון.

    python tools/integrity_check.py --only shabbat             דוח בלבד (data/fold/integrity.json)
    python tools/integrity_check.py --apply                    וגם הוודאיים נכתבים לשכבה (data/edits/<מסכת>.json)
"""
import re, html as _html

NIK = re.compile('[֑-ׇ]')


def plain(h):
    return _html.unescape(re.sub(r'<[^>]+>', '', h or '')).replace('\xa0', ' ').replace('⁠', '')


def norm(t):
    t = NIK.sub('', t or '')
    t = re.sub(r'[^א-ת0-9 ]', ' ', t)
    return ' '.join(t.split())


def nobr(t):
    return norm(re.sub(r'\[[^\]]*\]', ' ', NIK.sub('', t or '')))


HEAD_K = ('nose', 'dh', 'kotar', 'h', 'h2', 'h3')


def flat(pages):
    """רשימה שטוחה של יחידות: {pi, daf, id, k, a, lines:[(ek, h, t, n)]}"""
    out = []
    for pi, pg in enumerate(pages):
        for u in pg.get('units') or []:
            ls = [('u%s.%d' % (u.get('id'), n + 1), l[1] if len(l) > 1 else '') for n, l in enumerate(u.get('l') or [])]
            out.append({'pi': pi, 'daf': pg.get('daf'), 'id': u.get('id'), 'k': u.get('k'), 'a': u.get('a') or '',
                        'lines': [(ek, h, plain(h), norm(plain(h))) for ek, h in ls]})
    return out


def scan(pages):
    F = flat(pages)
    found = []
    body = [x for x in F if x['k'] in ('u',)]
    for i, u in enumerate(F):
        if u['k'] not in ('u',):
            continue
        a = norm(plain(u['a']))
        # side_repeat / empty_side
        if u['a'] and u['lines']:
            ek, h, t, n = u['lines'][0]
            if a and len(a) >= 3 and (n == a or n.startswith(a + ' ')):
                at = plain(u['a']).strip()
                after = t.strip()[len(at):] if t.strip().startswith(at) else ''
                certain = n != a and t.strip().startswith(at) and ((len(a.split()) >= 2 and at.endswith(':')) or re.match(r'^\s*[-־:]\s', after or 'x') is not None)
                found.append({'kind': 'side_repeat', 'certain': certain, 'daf': u['daf'], 'ek': ek, 'anchor_ek': 'u%s.0' % u['id'],
                              'anchor': at, 'h': h, 't': t})
        if u['a'] and not re.search('[א-ת]', plain(u['a'])) and plain(u['a']).strip() not in ('-', '־', '–'):
            found.append({'kind': 'empty_side', 'certain': False, 'daf': u['daf'], 'ek': 'u%s.0' % u['id'], 't': plain(u['a'])})
        # head_line / head_tail: הכותרת שאחרי היחידה
        nxt = F[i + 1] if i + 1 < len(F) else None
        if nxt and u['lines']:
            heads = []
            if nxt['k'] in HEAD_K and nxt['a']:
                heads.append(('heading', 'u%s.0' % nxt['id'], norm(plain(nxt['a']))))
            elif nxt['k'] == 'u' and nxt['a']:
                heads.append(('side', 'u%s.0' % nxt['id'], norm(plain(nxt['a']))))
            ek, h, t, n = u['lines'][-1]
            for kind, hek, hn in heads:
                if len(hn.split()) < 2:
                    continue
                if n == hn:
                    found.append({'kind': 'head_line', 'certain': kind == 'heading' and len(u['lines']) > 1, 'daf': u['daf'], 'ek': ek,
                                  'head_ek': hek, 'h': h, 't': t})
                elif kind == 'heading' and n.endswith(' ' + hn) and len(hn.split()) >= 2:
                    found.append({'kind': 'head_tail', 'certain': False, 'daf': u['daf'], 'ek': ek, 'head_ek': hek, 'h': h, 't': t})
        # tail_dup: שורה שהיא בדיוק סוף השורה שלפניה, באותה יחידה (גם 2 מילים - dup_lines דורש 3) - לעיון
        for l1, l2 in zip(u['lines'], u['lines'][1:]):
            if len(l2[3].split()) >= 2 and l1[3] != l2[3] and l1[3].endswith(' ' + l2[3]) and len(l2[3].split()) < 3:
                found.append({'kind': 'tail_dup', 'certain': False, 'daf': u['daf'], 'ek': l2[0], 'h': l2[1], 't': l2[2]})
        # missing_space: פסיק או נקודה צמודים לאות שאחריהם - שארית איחוי שורות (Delete בסוף שורה, merge בסכם)
        for ek, h, t, n in u['lines']:
            if re.search(r'[א-ת][,.][א-ת]', t) and not re.search(r'[א-ת][,.][א-ת][\"\'׳״]', t):
                found.append({'kind': 'missing_space', 'certain': True, 'daf': u['daf'], 'ek': ek, 'h': h, 't': t})
        # bracket_dup: בתוך היחידה ובין יחידות סמוכות
        seq = [(u, l) for l in u['lines']]
        if nxt and nxt['k'] == 'u' and nxt['lines'] and not nxt['a']:
            seq.append((nxt, nxt['lines'][0]))
        for (u1, l1), (u2, l2) in zip(seq, seq[1:]):
            b1, b2 = nobr(l1[2]), nobr(l2[2])
            if len(b1.split()) >= 3 and b1 == b2 and l1[3] != l2[3]:
                drop = l1 if len(l1[3]) < len(l2[3]) else l2
                keep = l2 if drop is l1 else l1
                found.append({'kind': 'bracket_dup', 'certain': True, 'daf': u['daf'], 'ek': drop[0], 'keep': keep[0], 'h': drop[1], 't': drop[2]})
    # far_dup
    pos = {}
    for ui, u in enumerate(body):
        for ek, h, t, n in u['lines']:
            if len(n.split()) < 6 or NIK.search(t) or re.match(r'^(גופא|תנן|תניא|ותנן|והתנן)', n):
                continue
            pos.setdefault(n, []).append((ui, u, ek, h, t))
    for n, L in pos.items():
        if len(L) < 2:
            continue
        for (i1, u1, ek1, h1, t1), (i2, u2, ek2, h2, t2) in zip(L, L[1:]):
            if i2 - i1 >= 16:
                found.append({'kind': 'far_dup', 'certain': False, 'daf': u2['daf'], 'ek': ek2, 'other': ek1, 'other_daf': u1['daf'],
                              'h': h2, 't': t2})
    return found


def lost_text(x, recs, pages_text):
    """עריכה (סגנון נושא/ד"ה) שכתבה את נוסח הכותרת על שורת גוף אחרת - נוסח השורה שנדרסה, אם אינו בדף עוד."""
    tn = norm(x['t'])
    for r in sorted(recs or [], key=lambda r: -(r.get('t') or 0)):
        if r.get('op') == 'struct' or r.get('ps') not in ('nose', 'dh', 'kotar'):
            continue
        w = norm(r.get('was') or '')
        if norm(r.get('now') or '') != tn or not w or len(w.split()) < 2 or w == tn or tn in w \
                or plain(r.get('was') or '').strip().endswith(':'):     # נוסח של כותרת צד - לא משחזרים כשורה
            continue
        if w in pages_text:
            return None          # הנוסח עדיין בדף - אין מה לשחזר, מוחקים את הכפילות
        return r
    return None


def edits_for(found, t0, tag='p94int', recs=None, pages_text=''):
    out = []
    t = [t0]

    def rec(ek, h, now_h, daf, why, extra=None):
        t[0] += 1
        e = {'k': '%s~%d' % (ek, t[0]), 't': t[0], 'was': plain(h), 'now': plain(now_h), 'wasH': h, 'nowH': now_h,
             'daf': daf or '', 'wasP': '', tag: {'why': why}}
        if extra:
            e[tag].update(extra)
        return e
    for x in found:
        if not x.get('certain'):
            continue
        if x['kind'] == 'head_line':
            r = lost_text(x, recs, pages_text)
            if r:
                out.append(rec(x['ek'], x['h'], r.get('wasH') or _html.escape(r.get('was') or '', quote=False), x['daf'],
                               'כותרת שנכתבה על שורה - השורה שנדרסה הוחזרה', {'keep': x.get('head_ek'), 'from': r.get('k'), 'from_t': r.get('t')}))
            else:
                out.append(rec(x['ek'], x['h'], '', x['daf'], 'כותרת שהועתקה לשורה שלפניה', {'keep': x.get('head_ek')}))
        elif x['kind'] == 'missing_space':
            nh = re.sub(r'(?<=[א-ת])([,.])(?=(?:<[^>]+>)*[א-ת])', r'\1 ', x['h'])
            if nh != x['h'] and norm(plain(nh)) == norm(x['t']):
                out.append(rec(x['ek'], x['h'], nh, x['daf'], 'רווח חסר אחרי פסיק (שארית איחוי שורות)'))
        elif x['kind'] == 'bracket_dup':
            out.append(rec(x['ek'], x['h'], '', x['daf'], 'שורה כפולה (זהה בלי הסוגריים)', {'keep': x.get('keep')}))
        elif x['kind'] == 'side_repeat':
            h = x['h']
            # מסירים את הכפילות מתחילת השורה, עם הסימון שעליה
            txt = plain(h)
            rest = re.sub(r'^[\s\-־:]+', '', txt.strip()[len(x['anchor']):])
            m = re.match(r'^(\s*(?:<[^>]+>\s*)*)' + re.escape(_html.escape(x['anchor'], quote=False)).replace('\\"', '(?:"|&quot;)'), h)
            if m:
                nh = h[:len(m.group(1))] + h[m.end():]
                nh = re.sub(r'^((?:<[^>]+>)*)[\s\-־:]+', r'\1', re.sub(r'<i class="[^"]*">\s*</i>', '', nh))
            else:
                nh = _html.escape(rest, quote=False)
            if norm(plain(nh)) != norm(rest):
                continue
            out.append(rec(x['ek'], h, nh, x['daf'], 'כותרת צד שחוזרת בתחילת השורה'))
    return out


def main():
    import os, sys, io, json, argparse, time, datetime
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    sys.path.insert(0, here)
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', default='')
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--live-dir', default='')
    ap.add_argument('--pages', default='', help='קובץ pickle של pages (לבדיקה)')
    a = ap.parse_args()
    import mishna_check as MC
    from dup_lines import hot_keys
    book = json.load(io.open(os.path.join(root, 'data', 'book.json'), encoding='utf-8'))
    slugs = [s for s in book['slugs'] if not a.only or s in a.only.split(',')]
    repp = os.path.join(root, 'data', 'fold', 'integrity.json')
    rep = {'when': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'masechtot': {}}
    if a.only and os.path.exists(repp):
        try:
            old = json.load(io.open(repp, encoding='utf-8'))
            rep['masechtot'] = {k: v for k, v in (old.get('masechtot') or {}).items() if k not in slugs}
        except ValueError:
            pass
    t0 = int(time.time() * 1000)
    total = 0
    for s in slugs:
        try:
            if a.pages:
                import pickle
                pages = pickle.load(open(a.pages, 'rb'))
            else:
                pages = MC.pages_of(s, True, a.live_dir or None)
        except Exception as e:
            rep['masechtot'][s] = {'error': str(e)[:200]}
            print(s, 'שגיאה', e)
            continue
        found = scan(pages)
        try:
            if a.live_dir and os.path.exists(os.path.join(a.live_dir, s + '.json')):
                srv = json.load(io.open(os.path.join(a.live_dir, s + '.json'), encoding='utf-8')).get('doc') or {}
            else:
                import fold as F
                srv = F.live_doc(s) or {}
        except Exception:
            srv = {}
        ptxt = ' | '.join(l[3] for u in flat(pages) for l in u['lines'])
        eds = edits_for(found, t0, recs=srv.get('edits') or [], pages_text=ptxt)
        hot = hot_keys(s, a.live_dir or None)
        held = [e for e in eds if e['k'].split('~')[0] in hot or e['k'].split('.')[0] in hot]
        eds = [e for e in eds if e not in held]
        t0 += len(eds) + 10
        fixed = {e['k'].split('~')[0] for e in eds}
        review = [{'kind': x['kind'], 'daf': x['daf'], 'ek': x['ek'], 't': x['t'][:200],
                   'other': x.get('other'), 'other_daf': x.get('other_daf'), 'held': x['ek'] in {e['k'].split('~')[0] for e in held}}
                  for x in found if x['ek'] not in fixed]
        from collections import Counter
        try:
            sys.path.insert(0, os.path.join(here, 'tosafot'))
            import tos_anchor_lib as TAL
            tos = TAL.tos_check(s, pages)
        except Exception as e:
            tos = {'error': str(e)[:200]}
        rep['masechtot'][s] = {'tos': tos, 'count': dict(Counter(x['kind'] for x in found)),
                               'fixed': [{'daf': e['daf'], 'k': e['k'], 'was': e['was'][:200], 'now': e['now'][:200], 'why': e['p94int']['why']} for e in eds],
                               'review': review}
        print('%-14s תוקנו %3d  לעיון %3d  %s' % (s, len(eds), len(review), dict(Counter(x['kind'] for x in found))))
        if tos and 'error' not in tos:
            print('%-14s תוס\' %4d: בלי עוגן %d, עמוד שגוי %d ודאי + %d ספק, סדר הפוך %d' % (
                '', tos['items'], len(tos['noanchor']), len(tos['wrongpage_certain']), len(tos['wrongpage_doubt']), len(tos['order'])))
        elif tos:
            print('   תוס\': שגיאה', tos['error'])
        # רשומת השרת שכתבה את הכותרת על השורה - נכנסת לארכיון הקליטה כמצבה (dup), כדי שהקיפול יכתוב לה מצבה בשרת
        # (cloud_word.tombstones). בלי זה היא חוזרת וחלה על הספר אחרי כל קיפול, והשורה נדרסת שוב (נמדד 25.11, שבת קד:)
        srcs = [(e['p94int'].get('from'), e['p94int'].get('from_t')) for e in eds if e['p94int'].get('from')]
        if a.apply and srcs:
            ap_ = os.path.join(root, 'data', 'word-cloud', 'ingested', s + '.json')
            arch = json.load(io.open(ap_, encoding='utf-8')) if os.path.exists(ap_) else {'v': 1, 'slug': s, 'edits': []}
            have_ = {(x.get('k'), x.get('t')) for x in arch.get('edits') or []}
            for k_, t_ in srcs:
                if (k_, t_) not in have_:
                    arch.setdefault('edits', []).append({'k': k_, 't': t_, 'dup': 1, 'p94int': 'כותרת שנכתבה על שורה בקבלה כפויה - מצבה'})
            arch['edits'].sort(key=lambda x: x.get('t') or 0)
            io.open(ap_, 'w', encoding='utf-8', newline='\n').write(json.dumps(arch, ensure_ascii=False, indent=1) + '\n')
        if a.apply and eds:
            p = os.path.join(root, 'data', 'edits', s + '.json')
            doc = json.load(io.open(p, encoding='utf-8')) if os.path.exists(p) else {'v': 1, 'slug': s, 'edits': []}
            have = {str(e.get('was')) + '|' + str(e.get('k', '')).split('~')[0] for e in doc.get('edits') or [] if e.get('p94int')}
            new = [e for e in eds if e['was'] + '|' + e['k'].split('~')[0] not in have]
            doc['edits'] = (doc.get('edits') or []) + new
            io.open(p, 'w', encoding='utf-8', newline='\n').write(json.dumps(doc, ensure_ascii=False, indent=1))
            total += len(new)
    os.makedirs(os.path.dirname(repp), exist_ok=True)
    io.open(repp, 'w', encoding='utf-8', newline='\n').write(json.dumps(rep, ensure_ascii=False, indent=1) + '\n')
    print('נכתבו לשכבה:', total)


if __name__ == '__main__':
    main()
