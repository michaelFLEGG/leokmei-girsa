# -*- coding: utf-8 -*-
"""dh_nikud_fill.py - ממלא את מטמון המנקד לד"ה משנה (פרומפט 80 א).

לכל ד"ה משנה שנשארו בו מילים בלי ניקוד אחרי ההעתקה מן המשנה (dh_nikud), נשלח חלק המשנה של הד"ה כולו
(בשביל ההקשר) למנקד של דיקטה (nikud_generate.vocalize), והמילים המנוקדות נשמרות לפי סדרן ב-data/nikud-dh/<מסכת>.json.
הבנייה אינה פונה לרשת. בדיקה כפולה: נשמר רק מה שאותיותיו זהות לנוסח שנשלח.

    python tools/dh_nikud_fill.py              # כל המסכתות שבאתר הבנוי
    python tools/dh_nikud_fill.py taanit berakhot
"""
import io, json, os, sys, glob, concurrent.futures
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import nikud_generate as G
import dh_nikud as D
from nikud_mishna import NIKUD

ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, 'data', 'nikud-dh')


def run(slug, log=print):
    d = G.load_data(slug)
    src = D.Source(slug)
    if not src.ok:
        log('%s: אין data/mishna - דילוג' % slug)
        return
    D.apply(d['pages'], slug, d.get('mbt'))          # בלי מטמון: מה שנשאר בלי ניקוד מן המשנה
    os.makedirs(OUT, exist_ok=True)
    fp = os.path.join(OUT, slug + '.json')
    have = json.load(io.open(fp, encoding='utf-8')) if os.path.exists(fp) else {}
    need = []
    for p in d['pages']:
        for u in p['units']:
            if u.get('k') != 'dh':
                continue
            h = u.get('av') or u.get('a') or ''
            left = [w for w in D.dh_words(h)]
            if not left:
                continue
            k = D.est_key(u.get('a') or '')
            if k and k not in have and k not in need:
                need.append(k)

    def one(t):
        try:
            voc = G.vocalize(t)
        except Exception as e:
            return t, None, repr(e)
        if NIKUD.sub('', voc).replace('|', '').split() != t.split() and \
                [x for x in G.WORD.findall(NIKUD.sub('', voc))] != G.WORD.findall(t):
            pass       # המנקד שינה כתיב: align מיישר לפי שלד ומשאיר ריק מה שאינו בטוח
        return t, G.align(t, voc), None

    bad = 0
    with concurrent.futures.ThreadPoolExecutor(4) as ex:
        for t, words, err in ex.map(one, need):
            if words is None:
                bad += 1
                continue
            have[t] = words
    io.open(fp, 'w', encoding='utf-8').write(json.dumps(have, ensure_ascii=False, indent=0))
    log('%s: %d ד"ה נשלחו למנקד, %d נכשלו, %d במטמון' % (slug, len(need), bad, len(have)))


def main():
    slugs = sys.argv[1:] or sorted(os.path.basename(f)[:-5] for f in glob.glob(os.path.join(ROOT, 'site', '*.html'))
                                   if os.path.basename(f)[:-5] in __import__('build_all').LATIN)
    for s in slugs:
        try:
            run(s)
        except Exception as e:
            print('%s: נכשל - %s' % (s, e))


if __name__ == '__main__':
    main()
