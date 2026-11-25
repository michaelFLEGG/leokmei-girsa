# -*- coding: utf-8 -*-
"""speaker_to_side.py - דובר בפתח השורה עולה לכותרת הצד (פרומפט 97, 25.11.2026). מכני, בלי בינה מלאכותית.

הכשל שנמצא: הכלל "דובר בפתח שורה - לכותרת צד" (כלל 17, 26.10; ונאכף בקוד מ-9.11 ב-sakem_core.speakerOut)
דילג על כל שורה שכבר יש לה כותרת צד - גם כשהכותרת היא מילת קישור אחת ("והא", "ת"ש", "והך", מקף).
ולכן נשארו "[צד:והא] {אם:דתנן:} 'בשבעה דרכים...'" במקום "[צד:והא דתנן:] 'בשבעה דרכים...'".
ועוד: סכם על קידושין רץ לפני שהכלל חודד (21.11), ואין מנגנון שחוזר אחורה. הכלי הזה הוא החלק המכני,
והוא נקרא גם מבודק השלמות הלילי (tools/integrity_check.py, פנקס הכללים docs/rules-ledger.json).

התנאי (יחידת גוף, השורה הראשונה):
  א. השורה נפתחת ב-<i class="am">X:</i> - דובר או נוסחת ייחוס, X עד שתי מילים, מסתיים בנקודתיים.
  ב. כותרת הצד: מקף, מילה אחת, או אות מספור (+ מילה אחת). (כותרת ריקה - אין לה מקום עריכה; לעיון.)
  ג. הצירוף "כותרת + X" עד שתי מילים; שלוש רק כשהראשונה מילת קישור קצרה (והא, ת"ש, והך, והרי, שהרי,
     מיתיבי ועוד). מקף ואות מספור אינם נספרים.
  ד. לא חל: צלע מקבילה בתוך השורה (דובר נוסף {אם:..:} באותה שורה - כלל 17ג), שורת משנה, ומימרא קצרה
     מאוד (פחות מ-20 תווים, כמו ב-speakerOut).
הפעולה: X עובר לכותרת הצד (המקף נשאר לפניו - "מקף קיים לעולם אינו נמחק", 9.11; אות מספור/מילה - לפני X),
הנקודתיים בסוף הכותרת, ו-X נמחק מתחילת השורה.
ודאי - נכתב לשכבה (data/edits/<מסכת>.json) כשתי עריכות: u<id>.0 (הכותרת) ו-u<id>.1 (השורה).
ספק - נרשם לעיון בדוח (data/fold/p97-speaker.json).
יחידה שמיכאל ערך ב-24 השעות האחרונות - לא נוגעים (נרשמת לעיון).

    python tools/speaker_to_side.py --only kiddushin            דוח בלבד
    python tools/speaker_to_side.py --only kiddushin --apply    וגם כתיבה לשכבה
"""
import re, html as _html

LINK = {'והא', 'ת"ש', 'והך', 'והרי', 'שהרי', 'מיתיבי', 'איתיביה', 'ורמינהו', 'והתניא', 'והתנן', 'ומיתיבי',
        'ותניא', 'ותנן', 'וקשה', 'ויקשה', 'קשה', 'והקשה', 'ותירץ', 'ואמנם', 'ועוד', 'וכן', 'אלא', 'שאני'}
NUM = re.compile(r'^([א-י]\.)\s*')
DASH = ('-', '־', '–')
AM_HEAD = re.compile(r'^(\s*)<i class="am">([^<]*)</i>')


def plain(h):
    return _html.unescape(re.sub(r'<[^>]+>', '', h or '')).replace('\xa0', ' ').replace('⁠', '')


def words(t):
    return [w for w in re.split(r'\s+', t.strip()) if w]


def side_parts(a):
    """(מקף, אות מספור, מילים) של כותרת הצד הנוכחית, או None כשאינה מתאימה."""
    t = plain(a).strip()
    dash = ''
    if t[:1] in DASH:
        dash, t = '-', t[1:].strip()
    num = ''
    m = NUM.match(t)
    if m:
        num, t = m.group(1), t[m.end():].strip()
    t = t.rstrip(':').strip()
    w = words(t)
    if len(w) > 1:
        return None
    return dash, num, w


def judge(u, hot=()):
    """מחזיר None או {'certain', 'why', 'a_new', 'l_new', ...} ליחידה אחת."""
    if u.get('k') != 'u' or not u.get('l'):
        return None
    empty = not plain(u.get('a') or '').strip()
    sty, h = u['l'][0][0], u['l'][0][1]
    m = AM_HEAD.match(h)
    if not m:
        return None
    x = plain(m.group(2)).strip()
    if not x.endswith(':'):
        return None
    xw = words(x.rstrip(':'))
    if not xw or len(xw) > 2 or NUM.match(x) or x[:1] in DASH:
        return None
    sp = side_parts(u['a'])
    if sp is None:
        return None
    dash, num, aw = sp
    rest_h = h[m.end():]
    rest = plain(rest_h).strip()
    tot = len(aw) + len(xw)
    ok_len = tot <= 2 or (tot == 3 and aw and aw[0] in LINK)
    reasons = []
    if empty:
        reasons.append('כותרת צד ריקה - אין לה מקום עריכה בשכבה (שינוי מבנה)')
    if not ok_len:
        reasons.append('הצירוף ארוך משתי מילים')
    if re.search(r'<i class="am">[^<]*:\s*</i>', rest_h):
        reasons.append('דובר נוסף בתוך השורה (צלע מקבילה)')
    if len(rest) < 20 and len(u['l']) == 1:
        reasons.append('מימרא קצרה מאוד')
    if 'mi' in sty.split() or 'nose' in sty.split():
        reasons.append('שורה בסגנון מיוחד')
    uid = 'u%s' % u['id']
    is_hot = uid in hot or (uid + '.0') in hot or (uid + '.1') in hot
    new_a = ' '.join(p for p in [dash, num, ' '.join(aw + xw)] if p) + ':'
    new_a = new_a.replace(' :', ':')
    # השורה: X נמחק עם הרווח שאחריו; סימון ריק שנותר יורד
    nh = m.group(1) + re.sub(r'^\s+', '', rest_h)
    nh = re.sub(r'^(\s*)<i class="[^"]*">\s*</i>\s*', r'\1', nh)
    if plain(nh).strip() != rest:
        reasons.append('הסרה מן השורה אינה נקייה')
    return {'certain': not reasons and not is_hot, 'held': is_hot, 'why': '; '.join(reasons),
            'id': u['id'], 'a_was': u['a'], 'a_new': _html.escape(new_a, quote=False), 'l_was': h, 'l_new': nh,
            'x': x, 'side': plain(u['a']).strip(), 'line': plain(h)}


def scan(pages, hot=()):
    out = []
    for pg in pages:
        for u in pg.get('units') or []:
            r = judge(u, hot)
            if r:
                r['daf'] = pg.get('daf')
                out.append(r)
    return out


def edits_for(found, t0, tag='p97'):
    out = []
    t = t0
    for r in found:
        if not r['certain']:
            continue
        for kk, was, now in (('.0', r['a_was'], r['a_new']), ('.1', r['l_was'], r['l_new'])):
            t += 1
            ek = 'u%s%s' % (r['id'], kk)
            out.append({'k': '%s~%d' % (ek, t), 't': t, 'was': plain(was), 'now': plain(now), 'wasH': was, 'nowH': now,
                        'daf': r['daf'] or '', 'wasP': '', tag: {'why': 'דובר בפתח השורה עלה לכותרת הצד (כלל 17, פרומפט 97)'}})
    return out


def main():
    import os, sys, io, json, argparse, time, datetime
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    sys.path.insert(0, here)
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', default='')
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--pages', default='')
    ap.add_argument('--hours', type=int, default=24)
    a = ap.parse_args()
    import mishna_check as MC
    from dup_lines import hot_keys
    book = json.load(io.open(os.path.join(root, 'data', 'book.json'), encoding='utf-8'))
    slugs = [s for s in book['slugs'] if not a.only or s in a.only.split(',')]
    repp = os.path.join(root, 'data', 'fold', 'p97-speaker.json')
    rep = json.load(io.open(repp, encoding='utf-8')) if os.path.exists(repp) else {'masechtot': {}}
    rep['when'] = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    total = 0
    for s in slugs:
        try:
            if a.pages:
                import pickle
                pages = pickle.load(open(a.pages, 'rb'))
            else:
                pages = MC.pages_of(s, True)
        except Exception as e:
            print(s, 'שגיאה', e)
            rep['masechtot'][s] = {'error': str(e)[:200]}
            continue
        hot = hot_keys(s, None, a.hours)
        found = scan(pages, hot)
        eds = edits_for(found, int(time.time() * 1000))
        cert = [r for r in found if r['certain']]
        rep['masechtot'][s] = {'certain': len(cert), 'review': [
            {'daf': r['daf'], 'id': r['id'], 'side': r['side'], 'x': r['x'], 'line': r['line'][:120],
             'why': r['why'] or ('נערך בידי המנהל ב-%d השעות האחרונות' % a.hours if r['held'] else '')}
            for r in found if not r['certain']],
            'fixed': [{'daf': r['daf'], 'id': r['id'], 'side': r['side'], 'new': plain(r['a_new']), 'line': r['line'][:80]} for r in cert]}
        print('%-14s ודאי %3d  לעיון %3d (מתוכם נערכו לאחרונה %d)' % (s, len(cert), len(found) - len(cert), sum(1 for r in found if r['held'])))
        if a.apply and eds:
            p = os.path.join(root, 'data', 'edits', s + '.json')
            doc = json.load(io.open(p, encoding='utf-8')) if os.path.exists(p) else {'v': 1, 'slug': s, 'edits': []}
            have = {str(e.get('wasH')) + '|' + str(e.get('k', '')).split('~')[0] for e in doc.get('edits') or [] if e.get('p97')}
            new = [e for e in eds if e['wasH'] + '|' + e['k'].split('~')[0] not in have]
            doc['edits'] = (doc.get('edits') or []) + new
            io.open(p, 'w', encoding='utf-8', newline='\n').write(json.dumps(doc, ensure_ascii=False, indent=1))
            total += len(new)
    os.makedirs(os.path.dirname(repp), exist_ok=True)
    io.open(repp, 'w', encoding='utf-8', newline='\n').write(json.dumps(rep, ensure_ascii=False, indent=1) + '\n')
    print('נכתבו לשכבה:', total)


if __name__ == '__main__':
    main()
