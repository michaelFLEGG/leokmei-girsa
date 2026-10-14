# -*- coding: utf-8 -*-
"""dh_apply.py - מחיל על כל התוספות שבמאגר את תיקון הפיצול והקיצור המוצג של הד"ה (14.10.2026).

  א. ד"ה שנחתך אחרי מקף צמוד למילה ("וכו' -בירושלמי") מתוקן בספירה (count-N.json). שדה dhOld שומר את הקודם.
  ב. ד"ה ש"נקודה ארוכה (לבדיקה)" או "ארבע מילים (לבדיקה)" ועדיין ארוך מ-8 מילים: נחתך לגבול טבעי (וכו' / שש מילים)
     ומסומן dhFix, כדי שיופיע בדוח לעיון.
  ג. שדה dhs (הד"ה המקוצר) נוסף לספירה ולקובצי live, וגם לשאלות (data/quiz/tos-*.json) שדה ds.
הספירה (המספרים והסדר) אינה משתנה: הכלי עוצר אם מספר השורות או הסדר השתנו.
    uv run python tools/tosafot/dh_apply.py [--dry]
"""
import os, sys, io, json, glob, re
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dhshort as S
ROOT = os.path.dirname(os.path.dirname(HERE))


def jl(p):
    return json.load(io.open(p, encoding='utf-8'))


def jd(p, o):
    with io.open(p, 'w', encoding='utf-8') as f:
        json.dump(o, f, ensure_ascii=False, indent=1)


def semi(s):
    """אין ; בסיכומים ובשאלות (14.10.2026): נקודה במקומו."""
    s2 = re.sub(r';\s*$', '.', s)
    s2 = re.sub(r'\s*;\s*', '. ', s2)
    return re.sub(r'\.\s*\.', '.', s2).strip() if s2 != s else s


def main():
    dry = '--dry' in sys.argv
    rep = {'tight': [], 'cut': [], 'long': 0, 'rows': 0}
    shorts = {}   # (slug, n_ukey) -> dhs
    for cf in sorted(glob.glob(os.path.join(ROOT, 'tosafot', '*', 'count-*.json'))):
        slug = os.path.basename(os.path.dirname(cf))
        d = jl(cf)
        order = [r['n'] for r in d['items']]
        for r in d['items']:
            rep['rows'] += 1
            new, rule = S.fix_dh_split(r['text'], r['dh'])
            if new and new != r['dh']:
                r.setdefault('dhOld', r['dh'])
                rep['tight'].append((slug, d['perek'], r['n'], r['dh'][:40], new))
                r['dh'], r['dhRule'] = new, rule
            if 'לבדיקה' in r.get('dhRule', '') and len(r['dh'].split()) > 8:
                w = r['dh'].split()
                cut = None
                for i, x in enumerate(w[:12]):
                    if x in ("וכו'", 'וכו׳'):
                        cut = i + 1
                        break
                cut = cut or 6
                r.setdefault('dhOld', r['dh'])
                r['dh'] = ' '.join(w[:cut])
                r['dhFix'] = 'נחתך למילים הראשונות (היה ארוך ושבור)'
                rep['cut'].append((slug, d['perek'], r['n'], r['dhOld'][:40], r['dh']))
            if len(r['dh'].split()) > 8:
                rep['long'] += 1
        assert order == [r['n'] for r in d['items']]
        un = S.unique_shorts(d['items'], key=lambda it: it['dafKey'])
        for r in d['items']:
            r['dhs'] = un[id(r)]
            shorts[(slug, d['perek'], r['n'])] = r
        if not dry:
            jd(cf, d)
    for lf in sorted(glob.glob(os.path.join(ROOT, 'tosafot', '*', 'live-*.json'))):
        slug = os.path.basename(os.path.dirname(lf))
        d = jl(lf)
        for it in d['items']:
            r = shorts.get((slug, d['perek'], it.get('disp', it['n'])))
            if r:
                it['dh'] = r['dh']
                it['dhs'] = r['dhs']
            if ';' in it.get('sum', ''):
                it['sum'] = semi(it['sum'])
        if not dry:
            jd(lf, d)
    for sf in sorted(glob.glob(os.path.join(ROOT, 'tosafot', '*', 'styles-*.json'))):
        slug = os.path.basename(os.path.dirname(sf))
        perek = int(re.search(r'styles-(\d+)', sf).group(1))
        d = jl(sf)
        ch = False
        for k, v in d.items():
            r = shorts.get((slug, perek, int(k))) if k.isdigit() else None
            if r and isinstance(v, dict) and v.get('dh') != r['dh']:
                v['dh'] = r['dh']
                ch = True
            if isinstance(v, dict):
                for st in 'abcde':
                    if isinstance(v.get(st), str) and ';' in v[st]:
                        v[st] = semi(v[st])
                        ch = True
        if ch and not dry:
            jd(sf, d)
    nq = 0
    for qf in sorted(glob.glob(os.path.join(ROOT, 'data', 'quiz', 'tos-*.json'))):
        d = jl(qf)
        slug = d.get('slug') or os.path.basename(qf)[4:-5]
        for x in d['items']:
            r = shorts.get((slug, x['p'], x['n']))
            if r:
                x['d'] = r['dh']
                x['ds'] = r['dhs']
                nq += 1
            for k in ('q', 'a'):
                if ';' in x.get(k, ''):
                    x[k] = semi(x[k])
            if x.get('st') == 'ממתין':      # שאלות תוספות מתפרסמות מיד, ההגהה בדיעבד
                x['st'] = 'מפורסם'
                x['rv'] = 0
        d['status'] = 'מפורסם'
        if not dry:
            jd(qf, d)
    print('שורות:', rep['rows'], '| תוקנו במקף צמוד:', len(rep['tight']), '| נחתכו:', len(rep['cut']), '| עדיין ארוכים מ-8:', rep['long'], '| שאלות עודכנו:', nq)
    for x in rep['tight']:
        print('  מקף:', x)
    for x in rep['cut']:
        print('  חתוך:', x)


if __name__ == '__main__':
    main()
