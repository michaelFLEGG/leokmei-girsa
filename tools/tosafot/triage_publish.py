# -*- coding: utf-8 -*-
"""triage_publish.py - פרסום מדורג של התוספות שנפסלו (הוראת בעל הפרויקט, 14.10.2026).

כללים:
  * סוגי כשל טכני / שער אוטומטי / בהירות / מסגור / תוספת דין / השמטת נימוק / לא ברור: מתפרסמים עם סימון "טרם נבדק".
  * סוג "הפניה שאינה בלשון התוספות": ההפניה נמחקת בקוד, והשאר מתפרסם.
  * סוגי "טעות עניינית" ו"ייחוס שגוי": נכנסים לקובץ הנתונים אך מוסתרים (h=1) עד הכרעת המנהל במסך הבדיקה.
  * תיקון בקוד בלבד (בלי מודל): ; לנקודה, קו ארוך לפסיק, ניקוד, שורות.
  * הנימוק נשמר ב-tosafot/triage/seed-<מסכת>.json (נשלח לשרת, ל-/tri) ואינו נכנס לדף.
הרצה: uv run python tools/tosafot/triage_publish.py [--dry]
"""
import os, sys, re, json, io, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.dirname(os.path.dirname(HERE))
TRI = os.path.join(ROOT, 'tosafot', 'triage')
HELD = ('D', 'F')
NIK = re.compile('[֑-ׇ]')
Q = re.compile(r'[\'"“”]([^\'"“”]{3,40})[\'"“”]')


def jload(p, d=None):
    return json.load(io.open(p, encoding='utf-8')) if os.path.exists(p) else d


def jdump(p, o):
    with io.open(p, 'w', encoding='utf-8') as f:
        json.dump(o, f, ensure_ascii=False, indent=1)


def flat(s):
    s = NIK.sub('', s or '')
    return re.sub(r'[\s"\'׳״“”‘’.,:;()\[\]\-–—?!]', '', s)


def sanitize(s):
    s = (s or '').strip()
    s = NIK.sub('', s)
    s = re.sub(r'\s*[–—―]\s*', ', ', s)
    s = re.sub(r'\s*;\s*$', '.', s)
    s = re.sub(r'\s*;\s*', '. ', s)
    s = re.sub(r'\s*\n+\s*', ' ', s)
    s = re.sub(r'\(\s*\)', '', s)
    s = re.sub(r'\s+([,.])', r'\1', s)
    s = re.sub(r'\s{2,}', ' ', s).strip()
    return s


def strip_refs(s, tos_text, reason):
    """מוחק הפניות שאינן בלשון התוספות: סוגריים שתוכנם אינו בתוספות, ומחרוזת מצוטטת בנימוק המבקר שנמצאת בשורה."""
    ft = flat(tos_text)
    removed = []

    def rep(m):
        inner = m.group(1)
        if flat(inner) and flat(inner) not in ft:
            removed.append(m.group(0))
            return ''
        return m.group(0)
    out = re.sub(r'\(([^()]*)\)', rep, s)
    for q in Q.findall(reason or ''):
        q = q.strip()
        if q and q in out and flat(q) not in ft and re.search(r'[.:]', q) and len(q.split()) <= 4:
            out = out.replace(q, '')
            removed.append(q)
    out = re.sub(r'\s+([,.])', r'\1', out)
    out = re.sub(r',\s*([,.])', r'\1', out)
    out = re.sub(r'\s{2,}', ' ', out).strip()
    return out, removed


def main():
    dry = '--dry' in sys.argv
    classes = jload(os.path.join(TRI, 'classes.json'))
    import factory_place
    from factory import ukey
    report = {}
    for slug in ('sukkah', 'berakhot'):
        base = os.path.join(ROOT, 'tosafot', slug)
        seed = {'slug': slug, 'items': {}}
        dec = (jload(os.path.join(base, 'decided.json'), {}) or {}).get('items', {})
        for perek in factory_place.perakim(slug):
            wp = os.path.join(ROOT, 'tosafot', 'factory', 'work-%s-%d.json' % (slug, perek))
            w = jload(wp)
            if not w:
                continue
            count = jload(os.path.join(base, 'count-%d.json' % perek))
            sp, ap = os.path.join(base, 'styles-%d.json' % perek), os.path.join(base, 'anchors-%d.json' % perek)
            styles, anchors = jload(sp, {}), jload(ap, {'_comment': ''})
            touched = False
            for r in count['items']:
                key = '%d-%d' % (perek, r['n'])
                rec = w['recs'].get(key)
                if not rec or rec.get('status') != 'flagged' or str(ukey(perek, r['n'])) in dec:
                    continue
                k = str(r['n'])
                if k in styles and not styles[k].get('unc'):
                    continue            # כבר מוצג (הכרעת מנהל או ריצה קודמת)
                c = classes.get('%s:%s' % (slug, key))
                if c is None:
                    raise SystemExit('עצירה: אין סיווג לתוספות %s:%s' % (slug, key))
                why = []
                if rec.get('rv_s'):
                    why.append('על השורה: ' + rec['rv_s'])
                for qi, v in (rec.get('rv_q') or {}).items():
                    why.append('על שאלה %d: %s' % (int(qi) + 1, v))
                for v in (rec.get('bad_s') or []):
                    why.append('שער אוטומטי: ' + v)
                line0 = rec.get('s') or ''
                line = sanitize(line0)
                removed = []
                if c == 'B':
                    cand, removed = strip_refs(line, r['text'], rec.get('rv_s'))
                    cand = sanitize(cand)
                    if len(cand.split()) >= 4:
                        line = cand
                    else:
                        removed = []
                held = c in HELD
                st = {'dh': r['dh'], 'a': line, 'b': line, 'gen': True, 'engine': rec.get('engine', ''), 'unc': True, 'cls': c}
                if held:
                    st['held'] = True
                styles[k] = st
                a = dict(rec['a']) if rec.get('a') else {'t': '', 'occ': 1, 'rule': 3, 'why': 'ממתין להנחה לפי סדר המספרים'}
                a['daf'] = r['dafKey']
                anchors[k] = a
                seed['items']['%d' % ukey(perek, r['n'])] = {
                    'perek': perek, 'n': r['n'], 'daf': r['daf'], 'dh': r['dh'], 'text': r['text'], 'line': line,
                    'orig': line0 if line0 != line else '', 'removed': removed, 'why': why, 'cls': c, 'held': held}
                touched = True
            if touched and not dry:
                jdump(sp, styles)
                jdump(ap, anchors)
        report[slug] = {'items': len(seed['items']), 'held': sum(1 for x in seed['items'].values() if x['held']),
                        'refs_removed': sum(1 for x in seed['items'].values() if x['removed'])}
        if dry:
            jdump(os.path.join(TRI, 'dry-%s.json' % slug), seed)
            continue
        jdump(os.path.join(TRI, 'seed-%s.json' % slug), seed)
        rep = factory_place.place_masechet(slug)
        if not rep['ok']:
            raise SystemExit('שער הסדר נכשל: ' + '; '.join(rep['errors'][:6]))
        for perek in factory_place.perakim(slug):
            r = subprocess.run([sys.executable, os.path.join(HERE, 'make_live.py'), slug, str(perek)], capture_output=True, text=True, encoding='utf-8')
            if r.returncode:
                raise SystemExit('make_live נכשל: ' + (r.stderr or r.stdout)[-400:])
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
