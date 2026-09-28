# -*- coding: utf-8 -*-
"""layout_audit.py - סוכן סריקת התצוגה.

טוען כל מסכת מן האתר הבנוי בדפדפן אמיתי (Chromium ללא ראש), בשלושה
מצבים - זרימה, תצוגת ספר והדפסה - ומודד את המלבנים בפועל. תשעת סוגי
הממצאים מוגדרים ב-docs/מנת-העבודה-הבאה.md, משימה א.

המדידה אינה מסתמכת על CSS ולא על הנחה: היא קוראת getBoundingClientRect
ו-getClientRects לכל שורת טקסט, ואת המרווחים המותרים היא גוזרת מ-w:spacing
שבסגנונות הוורד עצמו (tools/style_spacing.py).

הרצה:
  uv run --with playwright --with lxml --with fonttools python tools/layout_audit.py
  אפשר: --masechtot sukkah,beitzah  --modes flow,book,print  --label קו-בסיס
         --no-shots  --max-sections 3  --site <dir>

פלט: <דוחות>/סריקת-תצוגה-<תאריך>[-<תווית>].md ו-.json, וגם
      site/layout-audit.json שלוח הבקרה של כל מסכת קורא ממנו.
"""
import os, sys, re, json, argparse, datetime, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import style_spacing
from build_all import SLUG, masechet_of, split_of

CODES = {
    1: 'חלל-מסילה',
    2: 'שורה-לבנה',
    3: 'חלון-לא-בשורתו',
    4: 'חפיפה',
    5: 'חלון-קטוע',
    6: 'סימן-בלי-טעם',
    7: 'גלישה',
    8: 'יחס-כותרת',
    9: 'ניתוק-בעמוד',
    10: 'ניקוד-חופף',
    11: 'כוכבית-בשורה',      # מידע לבקרה בלבד (א6): כוכבית בתוך טקסט, לא נגעה
}
MODES = {'flow': 'זרימה', 'book': 'תצוגת ספר', 'print': 'הדפסה', 'phone': 'טלפון'}
# בטלפון המסילה יושבת מעל הטקסט ולא לצדו, ורשת השורות היא אחרת מטבעה
# (כל יחידה פותחת בשורת מסילה). לכן רק שני הסוגים שאינם תלויים בפריסה
# נבדקים שם: סימן בלי טעם, וגלישה - שהיא הפגם שהלומד מרגיש ראשון בטלפון.
PHONE_SKIP = {1, 2, 3, 4, 5, 8, 9}
# יחידה ריקה (ב) היא פגם בכל מצב, גם בטלפון, ולכן אינה מסוננת שם
def phone_keep(f):
    return f['code'] not in PHONE_SKIP or (f['code'] == 2 and str(f.get('msg', '')).startswith('יחידה ריקה'))

# שם משפחת הגופן ב-CSS ומשקלו, אל קובץ הגופן שבאתר. ההתאמה נדרשת
# לבדיקת הגליפים: אות שאינה ב-cmap של הגופן הראשון נופלת לגופן חלופי,
# והאות מוצגת בצורה אחרת מזו שהמחבר בחר.
FONT_FILE = {
    ('Frank', '400'): 'frank.ttf', ('Frank', '700'): 'frank.ttf',
    ('Frank', '500'): 'frank.ttf', ('Frank', '900'): 'frank.ttf',
    ('Vilna', '400'): 'vilna-r.otf', ('Vilna', '500'): 'vilna-m.ttf',
    ('Vilna', '700'): 'vilna-b.otf', ('Vilna', '900'): 'vilna-xb.otf',
    ('VilnaG', '400'): 'vilna-g.ttf', ('VilnaG', '700'): 'vilna-g.ttf',
    ('VilnaG', '900'): 'vilna-g.ttf', ('VilnaG', '500'): 'vilna-g.ttf',
    ('Franknatan', '400'): 'franknatan.otf', ('Franknatan', '700'): 'franknatan.otf',
    ('Franknatan', '900'): 'franknatan.otf',
    ('Leukmey', '400'): 'leukmey.otf', ('Leukmey', '700'): 'leukmey.otf',
}


def reports_dir():
    """תיקיית הדוחות: הדרייב כשהוא מחובר, ואחרת בתוך עותק העבודה."""
    env = os.environ.get('LG_REPORTS')
    if env:
        os.makedirs(env, exist_ok=True); return env
    drive = os.path.join(os.path.expanduser('~'), 'Desktop', 'שיננא לHTML', '_שומר', 'דוחות')
    if os.path.isdir(os.path.dirname(drive)):
        os.makedirs(drive, exist_ok=True); return drive
    d = os.path.join(ROOT, '_שומר', 'דוחות')
    os.makedirs(d, exist_ok=True); return d


def docx_for(masechet, ddir):
    """קובץ הוורד של המסכת, לצורך המרווחים שבסגנונות."""
    best, bsize = None, -1
    for f in sorted(os.listdir(ddir)):
        if not f.endswith('.docx') or f.startswith('~$'):
            continue
        sp = split_of(f)
        if sp and masechet in sp:
            return os.path.join(ddir, f)
        if masechet_of(f) == masechet:
            p = os.path.join(ddir, f); s = os.path.getsize(p)
            if s > bsize: best, bsize = p, s
    return best


def cmap_of(path, cache={}):
    if path in cache:
        return cache[path]
    try:
        from fontTools.ttLib import TTFont
        f = TTFont(path, fontNumber=0, lazy=True)
        chars = set()
        for t in f['cmap'].tables:
            chars |= set(t.cmap.keys())
        f.close()
    except Exception as e:
        chars = None
    cache[path] = chars
    return chars


HEB = re.compile(r'[֐-׿יִ-ﭏ]')


def glyph_findings(fonts, fdir):
    """אות עברית שאינה ב-cmap של הגופן שהוקצה לה: היא נצבעת בגופן חלופי,
    ולכן אינה נראית כמו שאר הטקסט. לא ניחוש - cmap בפועל."""
    out = []
    for key, chars in sorted(fonts.items()):
        fam, _, weight = key.partition('|')
        fn = FONT_FILE.get((fam, weight)) or FONT_FILE.get((fam, '400'))
        if not fn:
            continue
        p = os.path.join(fdir, fn)
        if not os.path.exists(p):
            out.append({'code': 6, 'unit': '', 'daf': '', 'kind': 'font',
                        'msg': 'הגופן %s (משקל %s) אינו באתר' % (fam, weight), 'num': None, 'rect': None})
            continue
        cm = cmap_of(p)
        if cm is None:
            continue
        miss = sorted({c for c in chars if HEB.match(c) and ord(c) not in cm})
        if miss:
            out.append({'code': 6, 'unit': '', 'daf': '', 'kind': 'font',
                        'msg': 'בגופן %s (משקל %s, %s) אין גליף ל-%d תווים עבריים: %s'
                               % (fam, weight, fn, len(miss), ' '.join(miss[:12])),
                        'num': {'missing': len(miss)}, 'rect': None})
    return out


PROBE = open(os.path.join(HERE, 'layout_probe.js'), encoding='utf-8').read()


def page_mm(html_path):
    """מידות העמוד המודפס, מן ה-@page שבדף עצמו."""
    try:
        txt = open(html_path, encoding='utf-8').read(400000)
    except Exception:
        return (170, 260)
    m = re.search(r'@page\s*\{[^}]*size:\s*(\d+(?:\.\d+)?)mm\s+(\d+(?:\.\d+)?)mm', txt)
    return (float(m.group(1)), float(m.group(2))) if m else (170, 260)


def run(args):
    from playwright.sync_api import sync_playwright

    site = args.site or os.path.join(ROOT, 'site')
    fdir = os.path.join(site, 'fonts')
    ddir = os.environ.get('LG_DOCX') or os.path.join(ROOT, 'input', 'docx')
    rev = {v: k for k, v in SLUG.items()}

    pages = sorted(f for f in os.listdir(site)
                   if f.endswith('.html') and f not in ('index.html',) and '-hagaha' not in f)
    slugs = [f[:-5] for f in pages]
    if args.masechtot and args.masechtot != 'all':
        want = [s.strip() for s in args.masechtot.split(',')]
        slugs = [s for s in slugs if s in want]
    modes = [m.strip() for m in args.modes.split(',')]

    stamp = datetime.datetime.now().strftime('%d.%m.%Y')
    label = ('-' + args.label) if args.label else ''
    rdir = reports_dir()
    shot_dir = os.path.join(rdir, 'סריקת-תצוגה-%s%s-צילומים' % (stamp, label))
    if args.shots:
        os.makedirs(shot_dir, exist_ok=True)

    result = {'stamp': datetime.datetime.now().isoformat(timespec='seconds'),
              'label': args.label or '', 'modes': modes, 'codes': CODES, 'masechtot': {}}

    # התוצאה לבקרה שבדף נכתבת אחרי כל מסכת ולא בסוף: בשומר יש תקרת זמן,
    # וריצה שנקטעה באמצע השאירה את הקובץ חסר - והדף ביקש אותו וקיבל 404.
    def write_brief():
        brief = {'stamp': result['stamp'], 'label': result['label'], 'codes': CODES,
                 'm': {sl: {'modes': {md: v['counts'] for md, v in r['modes'].items()}}
                       for sl, r in result['masechtot'].items()}}
        with open(os.path.join(site, 'layout-audit.json'), 'w', encoding='utf-8') as fh:
            json.dump(brief, fh, ensure_ascii=False)
    write_brief()

    with sync_playwright() as pw:
        br = pw.chromium.launch(channel=args.channel) if args.channel else pw.chromium.launch()
        for slug in slugs:
            mas = rev.get(slug, slug)
            html = os.path.join(site, slug + '.html')
            pmm = page_mm(html)
            spacing = {}
            dx = docx_for(mas, ddir)
            if dx:
                try:
                    _, spacing = style_spacing.read(dx)
                except Exception as e:
                    print('אזהרה: לא נקראו המרווחים מן הוורד של', mas, '-', e)
            else:
                print('אזהרה: לא נמצא קובץ וורד ל', mas, '- המרווחים המותרים לא נגזרו')
            rec = {'masechet': mas, 'docx': os.path.basename(dx) if dx else None,
                   'roleSpacing': spacing, 'pageMM': pmm, 'modes': {}}
            result['masechtot'][slug] = rec

            for mode in modes:
                vw, vh = (1400, 900)
                if mode == 'phone':
                    vw, vh = (375, 780)
                if mode == 'print':
                    vw = int(round(pmm[0] / 25.4 * 96))
                    vh = int(round(pmm[1] / 25.4 * 96))
                ctx = br.new_context(viewport={'width': vw, 'height': vh},
                                     device_scale_factor=2 if args.shots else 1)
                pg = ctx.new_page()
                errs = []
                pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
                pg.on('pageerror', lambda e: errs.append(str(e)))
                pg.goto('file:///' + html.replace('\\', '/'))
                pg.wait_for_timeout(700)
                pg.add_script_tag(content=PROBE)
                if mode == 'print':
                    pg.emulate_media(media='print')
                pg.evaluate('([m,s])=>__lgSetMode(m,s)', [mode, args.sheets])

                nsec = pg.evaluate('__lgSections()')
                sec_list = list(range(nsec))
                if args.max_sections:
                    sec_list = sec_list[:args.max_sections]

                counts = collections.Counter()
                examples = collections.defaultdict(list)
                every = []
                heads, lh = None, None
                fonts_all = {}
                for si in sec_list:
                    info = pg.evaluate('(i)=>__lgSecInfo(i)', si)
                    pg.evaluate('(i)=>__lgRender(i)', si)
                    pg.wait_for_timeout(250)
                    # האיחוי רץ במסגרות-ציור, ובמקטע של 700 פסקאות הוא
                    # נמשך שניות רבות בדפדפן ללא ראש. מדידה באמצעו תפסה
                    # פסקה שכבר אוחתה לפני שהמסילה שלה הותאמה (נמדד
                    # בפסחים קט.), ולכן ממתינים עד שיסתיים - עד 40 שניות.
                    for _ in range(320):
                        if pg.evaluate('__lgSqDone()'):
                            break
                        pg.wait_for_timeout(125)
                    pg.wait_for_timeout(150)
                    r = pg.evaluate('(c)=>__lgAudit(c)',
                                    {'roleSpacing': spacing, 'bodyPt': 9})
                    if mode == 'phone':
                        r['findings'] = [f for f in r['findings'] if phone_keep(f)]
                    if heads is None:
                        heads, lh = r.get('heads'), r.get('lh')
                    for f, chs in (r.get('fonts') or {}).items():
                        fonts_all.setdefault(f, set()).update(chs)
                    for f in r['findings']:
                        counts[f['code']] += 1
                        if args.all_findings:
                            every.append({'code': f['code'], 'unit': f.get('unit'),
                                          'daf': f.get('daf'), 'kind': f.get('kind'),
                                          'msg': f.get('msg'), 'sec': si})
                        ex = examples[f['code']]
                        if len(ex) < 3:
                            f = dict(f, perek=info.get('perek', ''), secDaf=info.get('daf', ''), sec=si)
                            if args.shots and f.get('unit'):
                                f['shot'] = shot(pg, shot_dir, slug, mode, f)
                            ex.append(f)

                gf = glyph_findings(fonts_all, fdir)
                for f in gf:
                    counts[6] += 1
                    if len(examples[6]) < 3:
                        examples[6].append(f)

                rec['modes'][mode] = {
                    'viewport': [vw, vh], 'sections': len(sec_list), 'ofSections': nsec,
                    'lh': lh, 'heads': heads,
                    'counts': {str(k): counts[k] for k in sorted(CODES)},
                    'examples': {str(k): examples[k] for k in sorted(examples)},
                    'console': errs[:10],
                }
                if args.all_findings:
                    rec['modes'][mode]['all'] = every
                write_brief()
                print('%-16s %-6s %s' % (slug, mode,
                      ' '.join('%d=%d' % (k, counts[k]) for k in sorted(CODES) if counts[k])) or 'נקי')
                ctx.close()
        br.close()

    jp = os.path.join(rdir, 'סריקת-תצוגה-%s%s.json' % (stamp, label))
    with open(jp, 'w', encoding='utf-8') as fh:
        json.dump(result, fh, ensure_ascii=False, indent=1)
    mp = os.path.join(rdir, 'סריקת-תצוגה-%s%s.md' % (stamp, label))
    with open(mp, 'w', encoding='utf-8') as fh:
        fh.write(markdown(result))
    print('\nהדוח:', mp)
    return result


def shot(pg, d, slug, mode, f):
    """צילום חתוך של הממצא, אחרי שהיחידה הובאה אל תוך המסגרת."""
    try:
        r = pg.evaluate('(u)=>__lgFocus(u)', f['unit'])
        if not r:
            return None
        vp = pg.viewport_size
        pad = 26
        x = max(0, r['x'] - pad); y = max(0, r['y'] - pad)
        w = min(vp['width'] - x, r['w'] + pad * 2)
        h = min(vp['height'] - y, r['h'] + pad * 2)
        if w < 8 or h < 8:
            return None
        name = '%s-%s-%d-u%s.png' % (slug, mode, f['code'], f['unit'])
        pg.screenshot(path=os.path.join(d, name),
                      clip={'x': x, 'y': y, 'width': w, 'height': h})
        return name
    except Exception:
        return None


def markdown(res):
    L = ['# סריקת תצוגה - לאוקמי גירסא', '',
         'נסרק ב-%s%s.' % (res['stamp'].replace('T', ' '),
                            (' תווית: ' + res['label']) if res['label'] else ''),
         '', 'המדידה בדפדפן אמיתי, על המלבנים בפועל. המרווחים המותרים נגזרו מ-w:spacing',
         'שבסגנונות הוורד של אותה מסכת.', '',
         '**הערה על סוג 9:** ניתוק בעמוד נמדד במקום שבו יש גיליונות מפורשים',
         '(תצוגת ספר, וההדפסה אחרי שתעבור למנוע הגיליונות). במצב הדפסה שאינו',
         'מגיליונות אין בדפדפן מבנה עמודים למדוד, והבדיקה נעשית על ה-PDF עצמו.', '']
    L += ['## המונים', '']
    hdr = '| מסכת | מצב | ' + ' | '.join('%d %s' % (k, CODES[k]) for k in sorted(CODES)) + ' |'
    L += [hdr, '|' + '---|' * (len(CODES) + 2)]
    for slug, r in res['masechtot'].items():
        for md, v in r['modes'].items():
            L.append('| %s | %s | %s |' % (r['masechet'], MODES.get(md, md),
                     ' | '.join(str(v['counts'].get(str(k), 0)) for k in sorted(CODES))))
    L += ['']
    for slug, r in res['masechtot'].items():
        L += ['## %s' % r['masechet'], '',
              'קובץ הוורד: %s · עמוד מודפס: %gx%g מ"מ' %
              (r['docx'] or 'לא נמצא', r['pageMM'][0], r['pageMM'][1]), '']
        for md, v in r['modes'].items():
            L += ['### %s (חלון %dx%d, %d מקטעים מתוך %d)' %
                  (MODES.get(md, md), v['viewport'][0], v['viewport'][1],
                   v['sections'], v['ofSections'])]
            if v.get('heads'):
                h = v['heads']
                L.append('גובה אותיות נמדד: ' + ' · '.join(
                    '%s %.1f (גופן %.1f, משקל %s)' % (k, h[k]['ink'], h[k]['fs'], h[k]['weight'])
                    for k in ('body', 'mishna', 'nose', 'dh') if h.get(k)))
                L.append('רשת שורת הגוף: %.2f פיקסל' % (v['lh'] or 0))
            if v.get('console'):
                L.append('**שגיאות קונסול:** ' + ' | '.join(v['console'][:3]))
            L.append('')
            for k in sorted(CODES):
                n = v['counts'].get(str(k), 0)
                if not n:
                    continue
                L.append('**%d %s - %d ממצאים.** שלוש הדוגמאות הראשונות:' % (k, CODES[k], n))
                for f in v['examples'].get(str(k), []):
                    line = '- דף %s, יחידה %s (%s): %s' % (
                        f.get('daf') or f.get('secDaf') or '?', f.get('unit') or '-',
                        f.get('kind') or '', f.get('msg'))
                    if f.get('shot'):
                        line += ' [צילום: %s]' % f['shot']
                    L.append(line)
                L.append('')
    return '\n'.join(L) + '\n'


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--masechtot', default='all')
    ap.add_argument('--modes', default='flow,book,print')
    ap.add_argument('--label', default='')
    ap.add_argument('--max-sections', type=int, default=0)
    ap.add_argument('--sheets', type=int, default=1)
    ap.add_argument('--site', default='')
    ap.add_argument('--channel', default='',
                    help="ערוץ דפדפן מותקן, למשל chrome - חוסך הורדת דפדפן בשומר")
    ap.add_argument('--shots', dest='shots', action='store_true', default=True)
    ap.add_argument('--no-shots', dest='shots', action='store_false')
    ap.add_argument('--all-findings', dest='all_findings', action='store_true',
                    help='שומר כל ממצא ב-json, לא רק שלוש דוגמאות')
    run(ap.parse_args())
