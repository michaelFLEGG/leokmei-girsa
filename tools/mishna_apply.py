# -*- coding: utf-8 -*-
"""mishna_apply.py - כותב לוורד את מספרי קטעי המשנה שחושבו בבנייה.

הקלט: data/sections/<מסכת>.json (נכתב בבניית האתר, tools/mishna_numbers.py).
הפלט: בכל קובץ וורד, לפני כל ד"ה משנה (ולפני כל יחידת משנה או פסקה שמתחיל
בה קטע) מספר הקטע - "א. " בסגנון התו "מספר קטע" - כהוספה במעקב שינויים,
דרך word_apply בלבד: גיבוי, אימות, ואין נגיעה בשום דבר אחר. פסקה שכבר
ממוספרת מדולגת, ולכן הכלי אפשר להריץ שוב.

    uv run --with lxml python tools/mishna_apply.py bekhorot [--dry]
    uv run --with lxml python tools/mishna_apply.py --all [--dry]
"""
import os, sys, io, json, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import word_apply
from word_apply import apply_numbers, DRIVE, Refused

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUTHOR = 'מספור קטעי משנה'


def files_of(masechet):
    st = json.load(io.open(os.path.join(ROOT, 'site', 'status.json'), encoding='utf-8'))
    rec = (st.get('built') or {}).get(masechet)
    if not rec or not rec.get('file'):
        raise Refused('אין רשומת בנייה למסכת %s' % masechet)
    out = []
    for f in rec['file'].split(' + '):
        p = os.path.join(DRIVE, f)
        if not os.path.exists(p):
            raise Refused('הקובץ %s אינו בתיקיית הדרייב' % f)
        out.append(p)
    return out


def run(slug, dry=False, log=print):
    d = json.load(io.open(os.path.join(ROOT, 'data', 'sections', slug + '.json'), encoding='utf-8'))
    masechet = d['masechet']
    ops = [{'daf': o['daf'], 'context': o['text'], 'next': o.get('next', ''), 'i': o.get('i'),
            'letter': o['letter']} for o in d['ops'] if o.get('text')]
    # הכרעות סמנטיות (6.10.2026): שאריות שלא הותאמו מכנית ונבדקו ידנית מול הקשר הסוגיה
    xp = os.path.join(ROOT, 'data', 'm6', 'decisions', slug + '.json')
    if os.path.exists(xp):
        ops += [{'daf': o['daf'], 'context': o['text'], 'next': o.get('next', ''), 'i': o.get('i'),
                 'letter': o['letter']} for o in json.load(io.open(xp, encoding='utf-8'))]
    left = list(range(len(ops)))
    summary = {'masechet': masechet, 'ops': len(ops), 'applied': 0, 'skipped': 0, 'files': []}
    for path in files_of(masechet):
        batch = [ops[i] for i in left]
        r = apply_numbers(path, batch, AUTHOR, masechet, log=log, dry=dry)
        summary['files'].append({'file': os.path.basename(path), 'applied': r['applied'],
                                 'planned': r['planned'], 'skipped': r['skipped'],
                                 'verified': r['verified'], 'missed': len(r['missed'])})
        summary['applied'] += r['applied']
        summary['skipped'] += r['skipped']
        if r['verified'] is False:
            summary['failed'] = True
            break
        missed_ids = {id(o) for o, _ in r['missed']}
        left = [i for i in left if id(ops[i]) in missed_ids]
    summary['unplaced'] = len(left)
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('slugs', nargs='*')
    ap.add_argument('--all', action='store_true')
    ap.add_argument('--dry', action='store_true')
    a = ap.parse_args()
    slugs = a.slugs
    if a.all:
        slugs = sorted(f[:-5] for f in os.listdir(os.path.join(ROOT, 'data', 'sections')) if f.endswith('.json'))
    for s in slugs:
        try:
            print(json.dumps(run(s, a.dry), ensure_ascii=False))
        except Refused as e:
            print(s, 'דולג:', e)


if __name__ == '__main__':
    main()
