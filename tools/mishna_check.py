# -*- coding: utf-8 -*-
"""mishna_check.py - בודק המשניות (פרומפט 77, 22.11.2026). מכני, בלי בינה מלאכותית.

לכל תיבת משנה בכל מסכת - בספר (הוורד הקנוני) ובאתר (הספר עם כל השכבה, מאגר + שרת) - משווה את הטקסט
למשניות של אותו פרק (data/mishna/<slug>.json, ספריא), אחרי נרמול (בלי ניקוד, ראשי תיבות נפוצים נפתחים,
כתיב מלא/חסר מקורב: tools/mishna_guard.py).

ממצאים:
  זרה   - תיבה שהטקסט שלה אינו נמצא במשניות הפרק (כיסוי זוגות מילים נמוך מ-COV).
  נבלעה - משנה שקיימת במשניות הפרק ואין תיבה שמכסה אותה.
  כפולה - שתי תיבות בטקסט זהה.
  חלקי  - (פרומפט 87) רצף של 3 מילים ומעלה מן המשנה שחסר בתוך תיבה שהיא לשון המשנה (tools/mishna_gaps.py):
          "יוצא הגמל באפסר ונאקה בחטם" שנשמט משבת נא: בעריכת פיצול. ממצא שכבר נבדק ונמצא שאינו חוסר
          (ראשי תיבות, צמצום של המחבר) רשום ב-data/fold/mishna-partial-known.json ואינו מתריע שוב.

    python tools/mishna_check.py                 כל המסכתות שב-data/book.json (ספר ואתר)
    python tools/mishna_check.py --only shabbat
    python tools/mishna_check.py --live-dir DIR  קובצי /live שכבר נמשכו (DIR/<slug>.json)
הפלט: data/fold/mishna-check.json וטבלה בהדפסה.
"""
import os, sys, io, json, argparse, datetime, urllib.request

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mishna_guard as G
import mishna_gaps as MG
import chapter_ord

KNOWN = os.path.join(HERE, 'data', 'fold', 'mishna-partial-known.json')


def partial(slug, pages):
    """חוסר חלקי בתיבות (פרומפט 87): רק fix/move/outside - חוסר של ממש בתיבה שהיא לשון המשנה."""
    try:
        known = set((json.load(io.open(KNOWN, encoding='utf-8')).get(slug) or {}).keys())
    except Exception:
        known = set()
    out = []
    for x in MG.report(slug, MG.rows_from_pages(pages)):
        if x.get('decision') not in ('fix', 'move', 'outside'):
            continue
        if MG.sig(x) in known:
            continue
        out.append({'daf': x.get('daf'), 'perek': x.get('perek'), 'mishna': x.get('mishna'), 'decision': x['decision'],
                    'text': x.get('text'), 'ek': x.get('ek'), 'sig': MG.sig(x)})
    return out

COV = 0.3            # תיבה זרה: פחות מזה מן הזוגות שלה נמצאים במשניות הפרק (ברייתא בשבת ק.: 0.07)
SWALLOW = 0.35       # משנה נבלעה: פחות מזה מזוגותיה נמצאים בתיבות הפרק


def _plain(h):
    import re, html
    return html.unescape(re.sub(r'<[^>]+>', '', h or ''))


def boxes(pages):
    """[(daf, perek_no, key, text)] לכל שורת תיבת משנה, וגם התיבה כולה."""
    out = []
    for pg in pages:
        pn = chapter_ord.chapter_ordinal(pg.get('perek') or '')
        for u in pg.get('units') or []:
            if u.get('k') != 'm':
                continue
            txt = ' '.join(_plain(l[1]) for l in u.get('l') or [])
            out.append({'daf': pg.get('daf'), 'perek': pn, 'k': 'u%s' % u.get('id'), 'text': txt.strip(),
                        'mb': _plain(u.get('mbw') or '') or u.get('mbn')})
    return out


def check(slug, pages):
    M = G.load(slug)
    if M is None:
        return {'slug': slug, 'skip': 'אין משניות למסכת (data/mishna)'}
    bx = [b for b in boxes(pages) if b['text']]
    alien, dup = [], []
    seen = {}
    for b in bx:
        c = G.coverage(slug, b['text'], b['perek'])
        call = G.coverage(slug, b['text'])
        b['cov'] = round(c, 2)
        if c < COV and call < COV:
            alien.append(dict(b, cov_all=round(call, 2)))
        key = ' '.join(G.norm_words(b['text']))
        if key in seen and len(key) > 12:
            dup.append({'daf': b['daf'], 'k': b['k'], 'same_as': seen[key], 'text': b['text'][:80]})
        else:
            seen[key] = (b['daf'], b['k'])
    # נבלעה: משנה בפרק שאין תיבה שמכסה אותה
    swallowed = []
    byp = {}
    for b in bx:
        byp.setdefault(b['perek'], set()).update(zip(G.norm_words(b['text']), G.norm_words(b['text'])[1:]))
    for pi, ms in enumerate(M['chapters']):
        S = byp.get(pi + 1)
        if not S:
            continue                  # פרק שאינו בספר (או בלי מספר פרק)
        for mi, w in enumerate(ms):
            big = list(zip(w, w[1:]))
            if len(big) < 4:
                continue
            c = sum(1 for x in big if x in S) / float(len(big))
            if c < SWALLOW:
                swallowed.append({'perek': pi + 1, 'mishna': mi + 1, 'cov': round(c, 2), 'text': ' '.join(w[:12])})
    try:
        part = partial(slug, pages)
    except Exception as e:
        part = [{'error': str(e)[:200]}]
    return {'slug': slug, 'boxes': len(bx), 'alien': alien, 'swallowed': swallowed, 'dup': dup,
            'certain': certain(slug, pages), 'partial': part}


def certain(slug, pages):
    """ודאי: שורה בתיבת משנה שאינה במשניות, והנוסח שלה הוא בדיוק נוסח של שורת גמרא באותו דף או בדף שליד
    (כמו שבת ק.: ברייתא 'מבוי ששוה' שהועתקה לתוך משנה ג). זה סימן ל'מחוץ לאחד' ולא לניסוח של המנהל."""
    gem = {}
    for i, pg in enumerate(pages):
        for u in pg.get('units') or []:
            if u.get('k') == 'u':
                for l in u.get('l') or []:
                    k = ' '.join(G.norm_words(_plain(l[1])))
                    if len(k) > 15:
                        gem.setdefault(k, set()).add(i)
    out = []
    for i, pg in enumerate(pages):
        pn = chapter_ord.chapter_ordinal(pg.get('perek') or '')
        for u in pg.get('units') or []:
            if u.get('k') != 'm':
                continue
            for n, l in enumerate(u.get('l') or []):
                t = _plain(l[1])
                k = ' '.join(G.norm_words(t))
                where = gem.get(k)
                if not where or not any(abs(j - i) <= 1 for j in where):
                    continue
                c = G.coverage(slug, t, pn)
                ca = G.coverage(slug, t)      # גם בכל המסכת (סדר הפרקים בבבלי שונה לפעמים מן המשניות)
                if c is not None and c < COV and ca < COV:
                    out.append({'daf': pg.get('daf'), 'k': 'u%s.%d' % (u.get('id'), n + 1), 'cov': round(c, 2), 'text': t[:100]})
    return out


def pages_of(slug, with_layer, live_dir=None):
    import fold as F, cloud_word as C
    m = C.masechet_of_slug(slug)
    parts = (json.load(io.open(os.path.join(HERE, 'data', 'book.json'), encoding='utf-8')).get('parts') or {}).get(slug)
    blocks = F.whole_blocks(slug, m, parts, {}) if parts else None
    docx = None if parts else C.docx_of(m)
    doc = None
    if with_layer:
        srv = None
        if live_dir and os.path.exists(os.path.join(live_dir, slug + '.json')):
            srv = json.load(io.open(os.path.join(live_dir, slug + '.json'), encoding='utf-8')).get('doc')
        if srv is None:
            srv = F.live_doc(slug)
        _, _, _, doc = C.layer(slug, m, srv)
    pages, _ = F.view(docx, slug, m, doc, blocks=blocks)
    return pages


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', default='')
    ap.add_argument('--live-dir', default='')
    ap.add_argument('--book-only', action='store_true')
    a = ap.parse_args()
    book = json.load(io.open(os.path.join(HERE, 'data', 'book.json'), encoding='utf-8'))
    slugs = [s for s in book['slugs'] if not a.only or s in a.only.split(',')]
    res = {'when': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'masechtot': {}}
    print('%-14s %6s | %-16s | %-16s' % ('מסכת', 'תיבות', 'ספר: ודאי/זרה/נבלעה/כפולה/חלקי', 'אתר: ודאי/זרה/נבלעה/כפולה/חלקי'))
    for s in slugs:
        row = {}
        for tag, wl in (('book', False), ('site', True)):
            if wl and a.book_only:
                continue
            try:
                row[tag] = check(s, pages_of(s, wl, a.live_dir or None))
            except Exception as e:
                row[tag] = {'slug': s, 'error': str(e)[:200]}
        res['masechtot'][s] = row
        f = lambda r: ('-' if not r else r.get('error') and 'שגיאה' or r.get('skip') and 'אין משניות'
                       or '%d/%d/%d/%d/%d' % (len(r.get('certain') or []), len(r['alien']), len(r['swallowed']), len(r['dup']),
                                             len(r.get('partial') or [])))
        print('%-14s %6s | %-16s | %-16s' % (s, (row.get('book') or {}).get('boxes', ''), f(row.get('book')), f(row.get('site'))))
        sys.stdout.flush()
    out = os.path.join(HERE, 'data', 'fold', 'mishna-check.json')
    io.open(out, 'w', encoding='utf-8', newline='\n').write(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    print('נכתב:', out)


if __name__ == '__main__':
    main()
