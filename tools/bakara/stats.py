# -*- coding: utf-8 -*-
"""stats.py - הלמידה של מערכת הבקרה מהכרעות המחבר.

מושך מנקודת הקליטה את ההכרעות של כל מסכת שיש לה קובץ ממצאים, וכותב:
  data/bakara/decisions-<מסכת>.json   מזהה -> הכרעה (ממצא שהוכרע אינו חוזר בהרצה הבאה)
  data/bakara/stats.json              לכל סוג: אושרו / נדחו / נערכו, ועוד:
      demoted     סוג שנדחה ביותר מ-60% (ולפחות 5 הכרעות): יורד ל"קל" ומוצג מקופל
      candidates  סוג שאושר ב-95% ומעלה (ולפחות 10): מועמד למנוע המכני.
                  נרשם בלבד. המעבר למנוע המכני הוא החלטה של בעל הפרויקט.

    uv run python tools/bakara/stats.py
"""
import os, sys, re, json, glob, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _api

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
D = os.path.join(ROOT, 'data', 'bakara')
REJ, REJ_MIN = 0.60, 5
APP, APP_MIN = 0.95, 10


def compute(by):
    out = {}
    demoted, cands = [], []
    for det, s in sorted(by.items()):
        n = s['ok'] + s['no'] + s['edit']
        out[det] = {'ok': s['ok'], 'no': s['no'], 'edit': s['edit'], 'n': n}
        if n >= REJ_MIN and s['no'] / n > REJ:
            demoted.append(det)
        if n >= APP_MIN and s['ok'] / n >= APP:
            cands.append(det)
    return out, demoted, cands


def main():
    slugs = sorted({re.match(r'^([a-z-]+)-\d+\.json$', os.path.basename(f)).group(1)
                    for f in glob.glob(os.path.join(D, '*-[0-9]*.json')) if re.match(r'^([a-z-]+)-\d+\.json$', os.path.basename(f))})
    by = {}
    total = 0
    for slug in slugs:
        doc = _api.call('/bakara/dec?slug=' + slug).get('doc') or {}
        dec = doc.get('dec') or {}
        json.dump(dec, open(os.path.join(D, 'decisions-%s.json' % slug), 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=1, sort_keys=True)
        for x in dec.values():
            s = by.setdefault(x.get('det') or '?', {'ok': 0, 'no': 0, 'edit': 0})
            d = x.get('d')
            if d in ('ok', 'todo'):
                s['ok'] += 1
            elif d == 'no':
                s['no'] += 1
            elif d == 'edit':
                s['edit'] += 1
            total += 1
    out, demoted, cands = compute(by)
    json.dump({'when': datetime.datetime.now().isoformat(timespec='seconds'), 'total': total,
               'by': out, 'demoted': demoted, 'candidates': cands},
              open(os.path.join(D, 'stats.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('הכרעות:', total)
    for det, s in out.items():
        print(' ', det, s)
    if demoted:
        print('יורדים ל"קל" ומקופלים:', ', '.join(demoted))
    if cands:
        print('מועמדים למנוע המכני (רק רישום):', ', '.join(cands))


if __name__ == '__main__':
    main()
