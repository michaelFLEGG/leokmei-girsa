# -*- coding: utf-8 -*-
"""auto_verse.py - ניקוי לאחור של הערות "גרש / ציטוט / ראשי תיבות" (מנת סקירה חכמה, 14.10.2026, חלק א ה).

עובר על כל קובצי הממצאים (data/bakara/<מסכת>-<פרק>.json), ולכל ממצא סוג "סימני קיצור"
שטרם הוכרע בידי המחבר מפעיל את הכרעת הפסוקים (verse_quote). ממצא שכבר הוכרע בידי המחבר
אינו נוגע בו (הוא חומר למידה).

    uv run --with lxml python tools/skira/auto_verse.py            דוח בלבד
    uv run --with lxml python tools/skira/auto_verse.py --write    כותב את הקבצים ומעלה לנקודת הקליטה
    ... --write --push-all                                          מעלה את כל הפרקים (גם שלא השתנו), כדי ליישר את השרת
"""
import os, sys, json, glob, re, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'bakara'))
sys.path.insert(0, HERE)
import verse_quote as VQ


def decided_ids(slug):
    p = os.path.join(ROOT, '_work', 'skira', 'server-decisions.json')
    try:
        return set((json.load(open(p, encoding='utf-8')).get(slug) or {}).keys())
    except Exception:
        return set()


def pull_decisions():
    import _api
    slugs = sorted({re.match(r'^([a-z-]+)-\d+\.json$', os.path.basename(f)).group(1)
                    for f in glob.glob(os.path.join(ROOT, 'data', 'bakara', '*-[0-9]*.json'))})
    out = {}
    for s in slugs:
        out[s] = ((_api.call('/bakara/dec?slug=' + s).get('doc') or {}).get('dec')) or {}
    os.makedirs(os.path.join(ROOT, '_work', 'skira'), exist_ok=True)
    json.dump(out, open(os.path.join(ROOT, '_work', 'skira', 'server-decisions.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    return out


def main():
    write = '--write' in sys.argv
    decs = pull_decisions()
    tot = collections.Counter()
    changed = []
    for fn in sorted(glob.glob(os.path.join(ROOT, 'data', 'bakara', '*-[0-9]*.json'))):
        m = re.match(r'^([a-z-]+)-(\d+)\.json$', os.path.basename(fn))
        slug = m.group(1)
        done = set(decs.get(slug, {}).keys())
        d = json.load(open(fn, encoding='utf-8'))
        fl = d.get('findings') or []
        keep_decided = [f for f in fl if f.get('id') in done]
        todo = [f for f in fl if f.get('id') not in done]
        new, log = VQ.apply(todo)
        # יומן קיים נשמר (לא נכתב מחדש): ממצא שכבר ביומן אינו נספר שוב
        old_log = d.get('auto') or []
        have = {x.get('id') for x in old_log}
        add = [x for x in log if x.get('id') not in have]
        n_fix = sum(1 for f in new if f.get('auto'))
        tot['closed'] += len(log)
        tot['fix'] += n_fix
        tot['abbr_left'] += sum(1 for f in new if f.get('det') == 'abbr' and not f.get('auto'))
        if log or n_fix:
            changed.append(os.path.basename(fn))
        if write and (log or n_fix):
            # שמירת הסדר המקורי של הממצאים
            order = {f['id']: n for n, f in enumerate(fl)}
            allf = sorted(keep_decided + new, key=lambda f: order.get(f.get('id'), 10 ** 9))
            d['findings'] = allf
            d['auto'] = old_log + add
            json.dump(d, open(fn + '.tmp', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
            os.replace(fn + '.tmp', fn)
    print(dict(tot), 'קבצים שהשתנו:', len(changed))
    if write and ('--push-all' in sys.argv or changed):
        import push
        names = sorted(os.path.basename(f) for f in glob.glob(os.path.join(ROOT, 'data', 'bakara', '*-[0-9]*.json')))             if '--push-all' in sys.argv else changed
        for fn in names:
            push.push(os.path.join(ROOT, 'data', 'bakara', fn))


if __name__ == '__main__':
    main()
