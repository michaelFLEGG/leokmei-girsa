# -*- coding: utf-8 -*-
"""פרומפט 48 (16.11.2026): בדיקת B5 מול ה-A4 שממנו נגזר. כישלון אם שורה אחת שונה.
  uv run --with pymupdf python tools/print/b5_compare.py <a4.pdf> <b5.pdf> <profiles/b5.json> [--front 3] [--json out.json]
--front: מספר עמודי הפתיחה (שער, עמוד 2, תוכן) שהוקטנו כעמוד שלם; במסכת שלמה 3.
בודק: אותו מספר עמודים, ובכל עמוד אותן שורות טקסט באותו סדר (שורה = רצף מילים באותו קו בסיס, לפי pymupdf),
כל מילה בדף ה-B5 מוחזרת לקואורדינטות ה-A4 ונבדק שהיא באותו מקום בדיוק (סבולת 0.8 מ"מ), ומודד בדף ה-B5 את מלבן הדיו (שוליים בפועל במ"מ) ואת גודל האות הקטן והנפוץ בפועל (בנקודות).
קוד יציאה 0 = זהה, 4 = שורה שונה או מספר עמודים שונה, 5 = שוליים קטנים מהמותר (ימין 10, שאר 7).
"""
import sys, json, collections
import pymupdf as fitz

MM = 72 / 25.4


def words(page):
    return [w for w in page.get_text('words') if w[4].strip()]


def to_a4(w, tf):
    s, tx, ty = tf
    return ((w[0] / MM - tx) / s, (w[1] / MM - ty) / s, (w[2] / MM - tx) / s, (w[3] / MM - ty) / s)


def ink(page):
    """מלבן הדיו הנראה בפועל (מעובד לתמונה): טקסט חבוי בחלונות החיתוך אינו נספר"""
    pm = page.get_pixmap(dpi=100, colorspace=fitz.csGRAY)
    W, H, st, buf = pm.width, pm.height, pm.stride, pm.samples
    x0, y0, x1, y1 = W, H, -1, -1
    for y in range(H):
        row = buf[y * st:y * st + W]
        if min(row) < 200:
            xs = [i for i, v in enumerate(row) if v < 200]
            x0, x1 = min(x0, xs[0]), max(x1, xs[-1])
            y0 = min(y0, y)
            y1 = y
    if x1 < 0:
        return None
    k = 25.4 / 100
    return (x0 * k, y0 * k, (x1 + 1) * k, (y1 + 1) * k)


def main():
    a4, b5, prof = sys.argv[1], sys.argv[2], sys.argv[3]
    nfront = int(sys.argv[sys.argv.index('--front') + 1]) if '--front' in sys.argv else 0
    jo = sys.argv[sys.argv.index('--json') + 1] if '--json' in sys.argv else ''
    A, B = fitz.open(a4), fitz.open(b5)
    res = {'pages_a4': len(A), 'pages_b5': len(B), 'diff': [], 'margins': {}, 'sizes': {}}
    if len(A) != len(B):
        res['diff'].append({'why': 'מספר עמודים שונה'})
    # המרה: מיקום מילה ב-B5 בחזרה לקואורדינטות ה-A4, לפי הפרופיל. מילה שזזה ביותר מ-0.8 מ"מ = שבירה אחרת
    pr = json.load(open(prof, encoding='utf-8'))['shrink']
    s = pr['scale']
    body = (s, pr['page']['w'] - pr['right'] - pr['src']['x1'] * s, pr['top'] - pr['src']['y0'] * s)
    fs = pr.get('frontScale') or min(pr['page']['w'] / 210, pr['page']['h'] / 297)
    front = (fs, (pr['page']['w'] - 210 * fs) / 2, (pr['page']['h'] - 297 * fs) / 2)
    nl = 0
    for i in range(min(len(A), len(B))):
        tf = front if i < nfront else body
        wa = words(A[i])
        wb = [(to_a4(w, tf), w[4]) for w in words(B[i])]
        nl += len(wa)
        idx = collections.defaultdict(list)
        for r, t in wb:
            idx[t].append(r)
        miss = []
        for w in wa:
            c = idx.get(w[4]) or []
            ok = any(abs(r[0] - w[0] / MM) < .8 and abs(r[1] - w[1] / MM) < .8 for r in c)
            if not ok:
                miss.append((round(w[0] / MM, 1), round(w[1] / MM, 1), w[4]))
        if miss or len(wa) != len(wb):
            res['diff'].append({'page': i + 1, 'words_a4': len(wa), 'words_b5': len(wb), 'moved': miss[:6], 'n_moved': len(miss)})
    res['lines'] = nl
    W, H = B[0].rect.width / MM, B[0].rect.height / MM
    res['b5_page_mm'] = [round(W, 1), round(H, 1)]
    mins = {'right': 99, 'left': 99, 'top': 99, 'bottom': 99}
    sz = collections.Counter()
    for i, p in enumerate(B):
        r = ink(p)
        if r is None:
            continue
        m = {'right': W - r[2], 'left': r[0], 'top': r[1], 'bottom': H - r[3]}
        for k in mins:
            if m[k] < mins[k]:
                mins[k] = m[k]
        if i >= 3:
            for b in p.get_text('dict')['blocks']:
                for l in b.get('lines', []):
                    for s in l['spans']:
                        sz[round(s['size'], 2)] += len(s['text'])
    res['margins'] = {k: round(v, 2) for k, v in mins.items()}
    res['sizes'] = [[s, c] for s, c in sz.most_common(8)]
    bad_m = mins['right'] < 10 or min(mins['left'], mins['top'], mins['bottom']) < 7
    print('עמודים: A4=%d B5=%d  מילים שנבדקו=%d  עמודים עם מילה שזזה=%d' % (len(A), len(B), nl, len(res['diff'])))
    print('שוליים בפועל ב-B5 (מינימום, מ"מ):', res['margins'])
    print('גדלי אות נפוצים ב-B5 (נק\', תווים):', res['sizes'][:6])
    for d in res['diff'][:10]:
        print('  שונה:', d)
    if jo:
        json.dump(res, open(jo, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    if res['diff']:
        sys.exit(4)
    if bad_m:
        sys.exit(5)


if __name__ == '__main__':
    main()
