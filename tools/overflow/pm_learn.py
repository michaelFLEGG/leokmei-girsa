# -*- coding: utf-8 -*-
"""הכרעות העימוד של מיכאל במצב דפוס (17.11.2026, "צא לדרך").

כל פעולה במצב דפוס נשמרת בשרת (bakara/dec, מסכת "pm-<מסכת>") עם מצב השורות לפני ואחרי (tools/print_mode.js, pmLog):
  txt = הנוסח לפני, now = אחרי, det = הפעולה (type, Enter, Delete, Ctrl+., Ctrl+0, ok, auto2 ...),
  kind = מצב השורות "שורות:מילוי[!=מילה בודדת] > ...", sug = הקשר (JSON: השורה שמעל ושמתחת, העמוד, הממצא).
הכלי מושך אותן אל data/overflow/pm/<מסכת>.json. מהן נכתבים "כללי העימוד שנלמדו" (docs/כללי-עימוד-נלמדים.md)
בידי המשימה המתוזמנת של הלימוד, ומשם הם חלק מן ההוראות של סכם ושל הצעות האיחוי.
הרצה: python tools/overflow/pm_learn.py --slug berakhot   (צריך LEOKMEI_ADMIN_KEY)
"""
import argparse, io, json, os, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
ODIR = os.path.join(ROOT, 'data', 'overflow', 'pm')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--slug', default='berakhot')
    a = ap.parse_args()
    import perush_store as PS
    key = PS.admin_key()
    if not key:
        sys.exit('עצירה: אין מפתח מנהל (LEOKMEI_ADMIN_KEY)')
    req = urllib.request.Request(PS.API + '/bakara/dec?slug=pm-' + a.slug, headers={'x-admin-key': key, 'User-Agent': 'leokmei-pm/1.0'})
    with urllib.request.urlopen(req, timeout=60) as r:
        j = json.loads(r.read().decode('utf-8'))
    if not j.get('ok'):
        sys.exit('עצירה: השרת לא החזיר את ההכרעות')
    dec = (j.get('doc') or {}).get('dec') or {}
    if not dec:
        print('מצב דפוס (%s): אין הכרעות' % a.slug)
        return
    rows = []
    for k, v in dec.items():
        x = {'id': k, **v}
        try:
            x['ctx'] = json.loads(x.pop('sug', '') or '{}')
        except Exception:
            x['ctx'] = {}
        rows.append(x)
    rows.sort(key=lambda x: x.get('t', 0))
    os.makedirs(ODIR, exist_ok=True)
    io.open(os.path.join(ODIR, a.slug + '.json'), 'w', encoding='utf-8', newline='\n').write(
        json.dumps({'slug': a.slug, 'made': time.strftime('%Y-%m-%d %H:%M'), 'n': len(rows), 'items': rows}, ensure_ascii=False, indent=1) + '\n')
    by = {}
    for x in rows:
        by[x.get('det') or '?'] = by.get(x.get('det') or '?', 0) + 1
    print('מצב דפוס (%s): %d הכרעות %s' % (a.slug, len(rows), by))


if __name__ == '__main__':
    main()
