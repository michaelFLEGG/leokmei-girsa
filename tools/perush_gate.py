# -*- coding: utf-8 -*-
"""perush_gate.py - שער לפני פרסום: פירוש הגמרא אינו בקובצי האתר (פרומפט 17, 2.11.2026).

    python tools/perush_gate.py [תיקיית האתר, ברירת מחדל site] [--samples 400]

שתי בדיקות, וכשל בכל אחת עוצר את הפרסום:
  א. מבנה: אין שדה perush בקובצי המקורות, ואין p בקובצי העמודים של "סכם".
  ב. תוכן: מדגם מלשון הפירוש עצמו (לא הציטוט המודגש, שהוא לשון הגמרא) מחופש בכל קובץ טקסט באתר.
     הבדיקה הזאת רצה רק כשהפירוש זמין כאן במטמון, כלומר אחרי בנייה. בלעדיו היא נאמרת בקול ומדולגת.

כשהמתג commentary_public דולק השער אינו חל.
"""
import glob, io, json, os, random, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import perush_store as PS

TAG = re.compile(r'<[^>]+>')
BOLD = re.compile(r'<b>.*?</b>', re.S)
NIKUD = re.compile(r'[֑-ׇ]')
TEXT = re.compile(r'\.(html|js|json|txt|xml|css|md)$', re.I)


def norm(s):
    return re.sub(r'\s+', ' ', NIKUD.sub('', TAG.sub(' ', s))).strip()


def structure(site):
    bad = []
    for fp in glob.glob(os.path.join(site, 'sources', '*.json')):
        d = json.load(io.open(fp, encoding='utf-8'))
        n = sum(1 for p in (d.get('pages') or {}).values() if p.get('perush'))
        if n or d.get('perush_source'):
            bad.append('%s: %d עמודים עם פירוש' % (os.path.relpath(fp, site), n))
    for fp in glob.glob(os.path.join(site, 'sk', '*', '*.json')):
        if json.load(io.open(fp, encoding='utf-8')).get('p'):
            bad.append(os.path.relpath(fp, site))
    return bad


def phrases(samples):
    """קטעים של 80 תווים מלשון הפירוש שבמטמון המקומי. ציטוטי הגמרא והפסוקים מודגשים ואינם נכללים."""
    pool = []
    for fp in glob.glob(os.path.join(PS.CACHE, '*.json')):
        for segs in json.load(io.open(fp, encoding='utf-8')).values():
            for s in segs:
                for part in BOLD.split(s or ''):
                    t = norm(part)
                    if len(t) >= 120:
                        pool.append(t[20:100])
    random.seed(17)
    random.shuffle(pool)
    return pool[:samples]


def content(site, samples):
    want = phrases(samples)
    if not want:
        print('שער הפירוש: אין כאן מטמון פירוש, ובדיקת התוכן דולגה')
        return []
    bad = []
    n = 0
    for base, _, files in os.walk(site):
        for f in files:
            fp = os.path.join(base, f)
            if not TEXT.search(f) or os.path.getsize(fp) > 60_000_000:
                continue
            t = norm(io.open(fp, encoding='utf-8', errors='ignore').read().replace('\\n', ' ').replace('\\"', '"'))
            n += 1
            for w in want:
                if w in t:
                    bad.append('%s: %s' % (os.path.relpath(fp, site), w))
                    break
    print('שער הפירוש: %d קטעים נבדקו מול %d קבצים' % (len(want), n))
    return bad


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    site = args[0] if args else os.path.join(PS.ROOT, 'site')
    samples = int(sys.argv[sys.argv.index('--samples') + 1]) if '--samples' in sys.argv else 400
    args = [a for a in args if a != str(samples)]
    site = args[0] if args else os.path.join(PS.ROOT, 'site')
    if PS.commentary_public():
        print('שער הפירוש: המתג commentary_public דולק, והשער אינו חל')
        return
    bad = structure(site)
    if not bad:
        bad = content(site, samples)
    if bad:
        print('עצירה: פירוש הגמרא נמצא בקובצי האתר, והפרסום נעצר:')
        for x in bad[:40]:
            print('  ', x)
        sys.exit(1)
    print('שער הפירוש: נקי')


if __name__ == '__main__':
    main()
