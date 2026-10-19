# -*- coding: utf-8 -*-
"""review.py - שלב 3: הבדיקות הדורשות בינה, מעל חבילות הידע (מודל קטן לכל עמוד, מאמת חזק לחומרה גבוהה).

    uv run --with lxml python tools/hv/review.py <slug> <מדף> <עד דף> [--depth regular|deep] [--cap-usd 3] [--no-verify] [--tag X]

קלט: חבילות הידע שבריפו הפרטי (pack.py) + מועמדי הקוד (checks.py) + פירוש הגמרא (data/sources).
פלט: <ריפו פרטי>/review/<slug>/<תג>.json (ממצאים מלאים, בפורמט sem של מערכת הבקרה) ו-hv/public-<תג>.json: הממצאים
שעברו את שער ההדלפה בלבד, שמותר להעלות לציבורי. אין כאן שום כתיבה לתיקיות הציבוריות.

עקרונות:
 * חברותא הוא חומר עיון: הצעת תיקון תמיד בנוסח שלנו, שינוי מינימלי, לעולם לא העתקה מלשון חברותא (נאכף בשער ההדלפה).
 * "מחלוקת מפרשים": רק כשחברותא ופירוש הגמרא מבינים אחרת באמת, עם שתי ההבנות ובאיזו הולך הנוסח שלנו.
 * מטמון: עמוד שלא השתנה (חבילה, פסקאות, גרסת הנחיה) אינו נשלח שוב.
 * מאמת (Sonnet): רק לחומרה "חמור" ולממצא "בינוני" בודאות גבוהה. ממצא שנדחה אינו נמחק: יורד ל"לבדיקה" עם הנימוק.
"""
import os, sys, re, json, argparse, time, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hv_common as H
from hv_common import C
sys.path.insert(0, os.path.join(H.TOOLS, 'tosafot'))

PROMPT_VER = 'hv1'
MODELS = {'small': 'haiku', 'strong': 'sonnet'}
KINDS = ['טעות בפשט', 'חסר שלב', 'תוכן שלא הובא', 'לא מובן', 'כותרת', 'המפרשים חלוקים', 'שאלה למחבר']
TAG = re.compile(r'<[^>]+>')

SYSTEM = """אתה סוקר את הקיצור "לאוקמי גירסא": קיצור התלמוד הבבלי שכתב המחבר, שלד הסוגיה בלשון דחוסה.
אתה מציע הערות שהמחבר יאשר או ידחה בלחיצה, ולכן כל הערה חייבת להיות נכונה, קצרה, ועם הצעה שאפשר ליישם. הערה שגויה עולה לו זמן.
אינך משכתב ואינך משפר סגנון.

## מה יש לפניך לכל עמוד
1. הפסקאות של הקיצור: `מספר | סגנון | טקסט`. מותר להעיר רק על פסקאות שבחלק "הקיצור".
2. פירוש הגמרא (הפירוש הרשמי שהמחבר נשען עליו).
3. ביאור "חברותא" (חומר עיון פרטי): לכל שורה `[k] →פסקה (דמיון) | גמרא: ... | הסבר: ...`, והערות שוליים ממוספרות עם שם המקור.
   "→-" פירושו: לא נמצאה לה פסקה מקבילה בקיצור. הדמיון הוא מדד קוד גס ויכול לטעות.
4. מועמדי קוד: שורות שהקוד חשד שחסרות. אתה מכריע אם הן באמת חסרות.

## מה מחפשים (כל הערה שייכת לסוג אחד)
- טעות בפשט: הפיכת דין, ייחוס לאמורא אחר, הבנה הפוכה של הסוגיה (לפי פירוש הגמרא ולפי חברותא יחד). חמור.
- חסר שלב: קושיא בלי תירוץ, תירוץ בלי קושיא, מהלך שבלעדיו הסוגיה לא מובנת.
- תוכן שלא הובא: מסקנה, דין או תירוץ סופי שיש בחברותא ובפירוש הגמרא ואין להם מקבילה בקיצור. הכלל: מסקנה ודין לעולם לא חסרים.
  שקלא וטריא צדדית, פרטים והרחבות שהקיצור מקצר בכוונה: לא להעיר.
- לא מובן: קיצור סתום או כינוי בלי נושא, כשחברותא מראה מה חסר. מה שחסר הוא מילה או שתיים, לא פסקה.
- כותרת: רצף ארוך בלי כותרת נושא, או מקום שחברותא פותח בו נושא חדש: הצע כותרת של 2 עד 6 מילים בלשון תורנית מהודקת.
- המפרשים חלוקים: רק כשפירוש הגמרא וחברותא מבינים אחרת באמת. בהערה: שתי ההבנות במשפט אחד כל אחת, ובאיזו הולך הנוסח שלנו.
- שאלה למחבר: כשאינך בטוח ואינך מציע תיקון.

## כללים קשיחים
- דיוק עדיף על כיסוי. "אולי" אינו סיבה. אם אין ממצא אמיתי, החזר מערך ריק. לעולם אל תמציא ממצא.
- חברותא הוא חומר עיון בלבד. אסור לצטט ממנו או להעתיק את לשונו: בשדות note, fix, alts אסור רצף של חמש מילים מלשון ההסבר או ההערות של חברותא.
  נסח הכול במילותיך ובסגנון הקיצור.
  הפניה למקור: כתוב בשדה src בלבד, בצורה `חברותא <דף> שורה <k>` או `חברותא <דף> הערה <n>` או `פירוש הגמרא`.
- הצעת התיקון (fix): בנוסח הקיצור ובסגנונו, שינוי מינימלי, בצורה `ישן ⟵ חדש` כשזו החלפה, אחרת הוראה קצרה. לא פסקה חדשה.
- mark: המילים המדויקות מתוך הפסקה, בדיוק כפי שהן כתובות בה (ללא ⟦⟧). בהערת "תוכן שלא הובא" או "כותרת": המילים האחרונות של הפסקה שאחריה יוכנס/תיכנס התוספת.
- בתוך ערכי טקסט אל תשתמש בגרשיים כפולים ASCII (") כי הם שוברים JSON: כתוב ר״י, דאר״מ עם ״ (U+05F4), או בלי גרשיים.
- בלי מקף ארוך (– או —). רק "-".
- ציטוט פסוק נכתב בגרש לפני המילה הראשונה ובגרש אחרי האחרונה (הקוד בודק); אל תעיר על כך.
- פסקה שמסומנת "נעולה" (המחבר ערך אותה לאחרונה): רק סוגים טעות בפשט וחסר שלב.
- אל תחזור על מה שנדחה בעבר: חוקת הסקירה מצורפת.

## פלט
מערך JSON בלבד, בלי הסברים לפניו או אחריו. לכל הערה:
{"i": מספר הפסקה, "daf": "ל.", "kind": "אחד מהסוגים", "mark": "...", "note": "משפט או שניים: מה הבעיה ולמה, בלי לצטט את חברותא",
 "fix": "...", "src": ["חברותא ל. שורה 7", "פירוש הגמרא"], "conf": "גבוה|בינוני|נמוך", "sev": "חמור|בינוני|קל", "alts": []}
"""

VERIFY_SYSTEM = """אתה מאמת ממצא בסקירת "לאוקמי גירסא". קיבלת ממצא (הערה ל מחבר), הפסקה שעליה הוא נסמך, פירוש הגמרא ושורות חברותא רלוונטיות.
החלט אם הממצא נכון ושווה את זמנו של המחבר. החזר JSON בלבד: {"ok": true|false, "why": "משפט אחד בלי לצטט את חברותא", "fix": "הצעת תיקון מתוקנת בנוסח הקיצור, או ריק"}.
דחה אם: ההערה נשענת על קריאה שגויה, הקיצור מקצר בכוונה, ההבדל הוא סגנון בלבד, או שהתיקון מעתיק את לשון חברותא. בלי מקף ארוך."""


API_MODELS = {'haiku': 'claude-haiku-5-5', 'sonnet': 'claude-sonnet-5-5'}
# מחיר לפי מיליון טוקנים (כניסה, יציאה), להערכת עלות בהרצת ענן; הרצה מקומית דרך claude -p מדווחת עלות בעצמה
PRICE = {'haiku': (1.0, 5.0), 'sonnet': (3.0, 15.0)}


def call_llm(model, system, user):
    """בענן (GitHub Actions) עם ANTHROPIC_API_KEY: ה-API ישירות. מקומית: claude -p (tools/tosafot/llm.py)."""
    if os.environ.get('ANTHROPIC_API_KEY'):
        try:
            import anthropic
        except ImportError:
            anthropic = None
        if anthropic:
            t0 = time.time()
            cl = anthropic.Anthropic()
            r = cl.messages.create(model=API_MODELS[model], max_tokens=8000, system=system,
                                   messages=[{'role': 'user', 'content': user}])
            tin, tout = r.usage.input_tokens, r.usage.output_tokens
            pi, po = PRICE[model]
            return {'text': ''.join(b.text for b in r.content if getattr(b, 'type', '') == 'text'), 'in': tin, 'out': tout,
                    'ms': int((time.time() - t0) * 1000), 'cost': (tin * pi + tout * po) / 1e6, 'model': model}
    import llm
    return llm.call(model, system, user, thinking=0, effort='low')


def extract_json(txt):
    a, b = txt.find('['), txt.rfind(']')
    if a < 0 or b < a:
        a, b = txt.find('{'), txt.rfind('}')
        return json.loads(txt[a:b + 1]) if a >= 0 and b > a else []
    raw = txt[a:b + 1]
    try:
        return json.loads(raw)
    except ValueError:
        tmp = os.path.join(os.environ.get('TEMP', '.'), 'hv_loose.json')
        open(tmp, 'w', encoding='utf-8').write(raw.replace('},{', '},\n{'))
        return C.jload_loose(tmp, [])


def page_prompt(pk, cands, perush, locked, with_hv=True):
    L = ['=== דף %s ===' % pk['daf'], '## הקיצור']
    for p in pk['paras']:
        if p['ext'] == 0:
            L.append('%d | %s | %s%s' % (p['i'], p['style'], p['text'].replace('\n', ' '), ' | נעולה' if p['i'] in locked else ''))
    L.append('## פירוש הגמרא\n' + (perush or '(אין)'))
    if not with_hv:
        return chr(10).join(L)
    L.append('## חברותא (חומר עיון פרטי)')
    for s in pk['segs']:
        tgt = '→%d (%.2f)' % (s['para'], s['sim']) if s['para'] is not None else '→- (הטוב ביותר %.2f)' % s['best']
        g = s['gemara'].strip()
        e = s['explain'].strip()
        L.append('[%d] %s | גמרא: %s | הסבר: %s' % (s['k'], tgt, g[:200], e[:700]))
    notes = [n for n in pk['notes'] if len(n['text']) > 40][:10]
    if notes:
        L.append('## הערות חברותא')
        for n in notes:
            L.append('(%d) [%s] %s' % (n['n'], ', '.join(n['sources']) or 'ללא מקור מזוהה', n['text'][:450]))
    if cands:
        L.append('## מועמדי קוד (שורות שחשודות כחסרות)')
        for c in cands:
            L.append('- שורה %d, אחרי פסקה %d: %s' % (c['hv']['k'], c['i'], c['why_short'] if 'why_short' in c else c['note'][:70]))
    return '\n'.join(L)


def chav_text_of(pk):
    """לשון חברותא שאסור להעתיק (ההסבר וההערות; הגמרא המודגשת היא נוסח הגמרא עצמו ומותרת)."""
    return ' '.join([s['explain'] for s in pk['segs']] + [n['text'] for n in pk['notes']] + [str(x) for x in pk['intro']])


def normalize(rows, pk, locked):
    paras = {p['i']: p for p in pk['paras'] if p['ext'] == 0}
    out, dropped = [], {}
    for r in rows if isinstance(rows, list) else []:
        try:
            i = int(r.get('i'))
        except (TypeError, ValueError):
            dropped['מספר פסקה'] = dropped.get('מספר פסקה', 0) + 1
            continue
        if i not in paras:
            dropped['פסקה מחוץ לדף'] = dropped.get('פסקה מחוץ לדף', 0) + 1
            continue
        kind = r.get('kind')
        if kind not in KINDS:
            dropped['סוג'] = dropped.get('סוג', 0) + 1
            continue
        if i in locked and kind not in ('טעות בפשט', 'חסר שלב', 'תוכן שלא הובא'):
            dropped['נעולה'] = dropped.get('נעולה', 0) + 1
            continue
        txt = re.sub(r'⟦[^:⟧]*:|⟧', '', paras[i]['text'])
        mark = C.no_dash(str(r.get('mark') or ''))
        if not mark or mark not in txt:
            # תיקון קל: סימון שאינו מופיע בדיוק - נפילה לסוף הפסקה (למיקום), ורישום
            if kind in ('תוכן שלא הובא', 'כותרת') and txt.strip():
                mark = ' '.join(txt.split()[-5:])
                if mark not in txt:
                    mark = txt[-40:]
            else:
                dropped['סימון לא נמצא'] = dropped.get('סימון לא נמצא', 0) + 1
                continue
        src = [C.no_dash(str(x)) for x in (r.get('src') or [])][:4]
        row = {'i': i, 'daf': pk['daf'], 'kind': kind, 'mark': mark, 'note': C.no_dash(str(r.get('note') or '')),
               'fix': C.no_dash(str(r.get('fix') or '')), 'alts': [C.no_dash(str(a)) for a in (r.get('alts') or [])][:2],
               'conf': r.get('conf') if r.get('conf') in ('גבוה', 'בינוני', 'נמוך') else 'בינוני',
               'sev': r.get('sev') if r.get('sev') in ('חמור', 'בינוני', 'קל') else 'קל', 'src': src, 'evidence': ''}
        if src:
            row['note'] += ' [' + '; '.join(src) + ']'
        out.append(row)
    return out, dropped


def leak(rows, pk):
    """שער הדלפה: ממצא שכותב ברצף חמש מילים מלשון חברותא נחסם (לא מועלה לציבורי)."""
    bad = []
    ch = chav_text_of(pk)
    ok = []
    for r in rows:
        body = ' '.join([r['note'], r['fix']] + r['alts'])
        n = H.ngram_overlap(body, ch, 5)
        (bad if n else ok).append(r)
    return ok, bad


def usd(r):
    return float(r.get('cost') or 0)


def run(a):
    sys.path.insert(0, os.path.join(H.TOOLS, 'skira'))
    d = os.path.join(H.CHAV, 'packs', a.slug)
    k0, k1 = C.daf_key(a.d_from), C.daf_key(a.d_to)
    src = H.jload(os.path.join(H.ROOT, 'data', 'sources', a.slug + '.json'), {}) or {}
    cand_all = H.jload(os.path.join(H.CHAV, 'candidates', a.slug + '.json'), []) or []
    import engine
    lock = engine.locked_texts(a.slug)
    cache_dir = os.path.join(H.CHAV, 'hvcache', a.slug)
    tag = a.tag or ('%s_%s' % (re.sub(r'[^א-ת]', '', a.d_from), re.sub(r'[^א-ת]', '', a.d_to)))
    rows_all, spent, st = [], 0.0, {'pages': 0, 'cached': 0, 'calls': 0, 'tin': 0, 'tout': 0, 'dropped': {}, 'leak_blocked': 0,
                                      'verified': 0, 'rejected': 0, 'by_model': {}}
    files = sorted(os.listdir(d), key=lambda f: C.daf_key(H.jload(os.path.join(d, f))['daf']))
    for fn in files:
        pk = H.jload(os.path.join(d, fn))
        k = C.daf_key(pk['daf'])
        if k < k0 or k > k1:
            continue
        st['pages'] += 1
        locked = {p['i'] for p in pk['paras'] if p['ext'] == 0 and C.thash(p['text']) in lock}
        cands = [c for c in cand_all if c['daf'] == pk['daf']]
        sig = hashlib.sha1((pk['sig'] + PROMPT_VER + a.depth + str(a.no_hv) + str(sorted(locked)) + str(len(cands))).encode()).hexdigest()[:14]
        cp = os.path.join(cache_dir + ('-nohv' if a.no_hv else ''), H.file_of_label(pk['daf']) + '.json')
        old = H.jload(cp, None)
        if old and old.get('sig') == sig and not a.force:
            rows_all += old['rows']
            st['cached'] += 1
            continue
        if spent > a.cap_usd:
            print('עצירה: חריגה מתקרת העלות (%.2f$). עמוד %s ואילך לא נסרקו.' % (spent, pk['daf']))
            st['stopped_at'] = pk['daf']
            break
        pg = (src.get('pages') or {}).get(pk['daf']) or {}
        perush = '\n'.join(TAG.sub('', x) for x in pg.get('perush', []))[:6000]
        user = page_prompt(pk, cands, perush, locked, not a.no_hv)
        if a.no_hv:
            cands = []
        rules = open(os.path.join(H.TOOLS, 'skira', 'review-rules.md'), encoding='utf-8').read()
        r = call_llm(MODELS['small'], SYSTEM + '\n\n# חוקת הסקירה (מחייבת)\n' + rules, user)
        st['calls'] += 1
        st['tin'] += r['in']
        st['tout'] += r['out']
        spent += usd(r)
        st['by_model'][r['model']] = st['by_model'].get(r['model'], 0) + usd(r)
        try:
            rows = extract_json(r['text'])
        except Exception as e:
            print('אזהרה: פלט לא תקין בדף %s (%s)' % (pk['daf'], str(e)[:60]))
            rows = []
        rows, dr = normalize(rows, pk, locked)
        for kk, v in dr.items():
            st['dropped'][kk] = st['dropped'].get(kk, 0) + v
        if a.depth == 'deep' and not a.no_verify:
            for row in rows:
                if row['sev'] == 'חמור' or (row['sev'] == 'בינוני' and row['conf'] == 'גבוה'):
                    para = next(p for p in pk['paras'] if p['i'] == row['i'])
                    vu = 'ממצא: %s\n\nהפסקה: %s\n\nפירוש הגמרא:\n%s\n\nשורות חברותא רלוונטיות:\n%s' % (
                        json.dumps(row, ensure_ascii=False), para['text'], perush[:3000],
                        '\n'.join('[%d] %s | %s' % (s['k'], s['gemara'][:150], s['explain'][:500]) for s in pk['segs']
                                  if s['para'] == row['i'] or any(('שורה %d' % s['k']) in x for x in row['src'])))
                    v = call_llm(MODELS['strong'], VERIFY_SYSTEM, vu)
                    spent += usd(v)
                    st['by_model'][v['model']] = st['by_model'].get(v['model'], 0) + usd(v)
                    st['tin'] += v['in']
                    st['tout'] += v['out']
                    st['verified'] += 1
                    try:
                        j = extract_json(v['text'])
                        j = j[0] if isinstance(j, list) and j else j
                        ok = bool(j.get('ok'))
                        row['verified'] = ok
                        row['vwhy'] = C.no_dash(str(j.get('why') or ''))
                        if not ok:
                            st['rejected'] += 1
                            row['sev'], row['conf'] = 'קל', 'נמוך'
                            row['note'] = 'לבדיקה (המאמת דחה: %s) · %s' % (row['vwhy'], row['note'])
                        elif j.get('fix'):
                            row['fix'] = C.no_dash(str(j['fix']))
                    except Exception:
                        row['verified'] = None
        ok, bad = leak(rows, pk)
        st['leak_blocked'] += len(bad)
        for b in bad:
            b['blocked'] = 'הדלפה'
        rows_all_page = ok + bad
        H.jsave(cp, {'sig': sig, 'rows': rows_all_page})
        rows_all += rows_all_page
        print('%s: הערות %d (נחסמו בשער ההדלפה %d) · עלות מצטברת %.3f$' % (pk['daf'], len(ok), len(bad), spent))
    outp = os.path.join(H.CHAV, 'review', a.slug, tag + '.json')
    H.jsave(outp, rows_all)
    pub = [r for r in rows_all if not r.get('blocked')]
    pubp = os.path.join(H.CHAV, 'review', a.slug, 'public-' + tag + '.json')
    H.jsave(pubp, [{k: v for k, v in r.items() if k in ('i', 'daf', 'kind', 'mark', 'note', 'fix', 'alts', 'conf', 'sev', 'evidence')}
                   for r in pub])
    st['spent_usd'] = round(spent, 4)
    st['findings'] = len(pub)
    st['by_kind'] = {}
    for r in pub:
        st['by_kind'][r['kind']] = st['by_kind'].get(r['kind'], 0) + 1
    H.jsave(os.path.join(H.CHAV, 'review', a.slug, 'stats-' + tag + '.json'), st)
    print(json.dumps(st, ensure_ascii=False))
    print('נכתב:', outp, '|', pubp)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('slug')
    ap.add_argument('d_from')
    ap.add_argument('d_to')
    ap.add_argument('--depth', default='regular', choices=['regular', 'deep'])
    ap.add_argument('--cap-usd', type=float, default=3.0)
    ap.add_argument('--no-verify', action='store_true')
    ap.add_argument('--force', action='store_true')
    ap.add_argument('--tag')
    ap.add_argument('--no-hv', action='store_true', help='בסיס להשוואה: בלי חברותא')
    run(ap.parse_args())


if __name__ == '__main__':
    main()
