# -*- coding: utf-8 -*-
"""run.py - הרצת הבקרה על פרק חדש, בפקודה אחת.

    uv run --with lxml python tools/bakara/run.py <slug> <פרק> [--gemara-only] [--pages 5]
                                                  [--no-sync] [--no-push] [--force-code-only]

מה הוא עושה, בסדר:
 א. מושך את ההכרעות של המחבר (stats.py), כדי שממצא שהוכרע לא יחזור, ושסוג
    שנדחה לרוב ירד ל"קל". נכשל - עוצר בקול (אפשר --no-sync).
 ב. בונה את אוצר המילים של הספר (נשמר בתיקיית הזמניים, לא במאגר).
 ג. מריץ את שכבת הקוד ומאחד אליה את ממצאי שכבת המודל שכבר נכתבו ב-
    _work/bakara/<slug>-<פרק>/sem/*.json, אל data/bakara/<slug>-<פרק>.json.
 ד. מכין לשכבת המודל קבצי קלט לפי טווחי דפים (כ-5 עמודים לסוכן): קיצור + גמרא +
    פירוש, ובמצב --gemara-only הגמרא בלי הפירוש (לבדיקה אם הדיוק נשמר ונחסך
    כמחצית). שכבת המודל עצמה רצה בסוכני אופוס (ראה tasks.md שנכתב לצד הקלט);
    אחרי שכתבו את sem/*.json - מריצים שוב את אותה פקודה והכל מתאחד.
 ה. מעלה את הקובץ לנקודת הקליטה (push.py), אלא אם --no-push.

הגנה: קובץ ממצאים קיים שיש בו ממצאי מודל אינו נדרס בקובץ של שכבת הקוד בלבד
(זה היה מוחק עבודה של 600 אלף טוקנים). רק --force-code-only עוקף.
"""
import os, sys, re, json, glob, argparse, subprocess, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
sys.path.insert(0, HERE)


def vocab_path(ddir):
    p = os.path.join(tempfile.gettempdir(), 'lg-bakara-vocab.json')
    if os.path.exists(p) and time.time() - os.path.getmtime(p) < 86400:
        return p
    print('בונה אוצר מילים של הספר...')
    subprocess.run([sys.executable, os.path.join(HERE, 'build_vocab.py'), ddir, p], check=True)
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('slug')
    ap.add_argument('perek', type=int)
    ap.add_argument('--gemara-only', action='store_true')
    ap.add_argument('--pages', type=int, default=5)
    ap.add_argument('--no-sync', action='store_true')
    ap.add_argument('--no-push', action='store_true')
    ap.add_argument('--force-code-only', action='store_true')
    a = ap.parse_args()

    import build_all
    rev = {v: k for k, v in build_all.SLUG.items()}
    if a.slug not in rev:
        raise SystemExit('עצירה: מסכת לא מוכרת: ' + a.slug)
    from ingest_edits import docx_for
    docx = docx_for(rev[a.slug])
    ddir = os.path.dirname(docx)
    out = os.path.join(ROOT, 'data', 'bakara', '%s-%d.json' % (a.slug, a.perek))
    work = os.path.join(ROOT, '_work', 'bakara', '%s-%d' % (a.slug, a.perek))
    os.makedirs(os.path.join(work, 'sem'), exist_ok=True)

    # א. הכרעות
    if not a.no_sync:
        import stats
        stats.main()
    # ב. אוצר מילים
    vp = vocab_path(ddir)
    # ג. שכבת הקוד + ממצאי המודל שכבר נכתבו
    sem = sorted(glob.glob(os.path.join(work, 'sem', '*.json')))
    if os.path.exists(out) and not sem and not a.force_code_only:
        prev = json.load(open(out, encoding='utf-8'))
        if any(f.get('layer') == 'מודל' for f in prev.get('findings', [])):
            raise SystemExit('עצירה: %s כבר מחזיק ממצאי מודל, ואין ב-%s קובצי מודל. '
                             'הרצה כזאת היתה מוחקת אותם. (--force-code-only לעקיפה)' % (out, os.path.join(work, 'sem')))
    tmp = out + '.tmp'
    subprocess.run([sys.executable, os.path.join(HERE, 'bakara.py'), ROOT, docx, a.slug, str(a.perek), vp, tmp] + sem, check=True)
    os.replace(tmp, out)
    res = json.load(open(out, encoding='utf-8'))
    print('נכתב', out, '-', len(res['findings']), 'ממצאים (מודל:', len(sem), 'קבצים)')

    # ד. קלט לשכבת המודל
    from docx2json import convert
    from styles_map import CS, role_of
    blocks = convert(docx)
    lo, hi = res['range']
    P = [b for b in blocks if lo <= b['i'] <= hi]
    src = json.load(open(os.path.join(ROOT, 'data', 'sources', a.slug + '.json'), encoding='utf-8'))
    pages = []                       # [(daf, [blocks])]
    for b in P:
        d = (b.get('daf') or '').strip()
        if not pages or pages[-1][0] != d:
            pages.append((d, []))
        pages[-1][1].append(b)
    tag = re.compile(r'<[^>]+>')
    groups = [pages[i:i + a.pages] for i in range(0, len(pages), a.pages)]
    tasks = ['# משימות שכבת המודל - %s פרק %d' % (a.slug, a.perek), '',
             'לכל קבוצה: סוכה אחד על אופוס, לפי `tools/bakara/prompt-model.md`. כל הסוכנים במקביל.', '']
    for n, g in enumerate(groups):
        rng = '%s-%s' % (g[0][0], g[-1][0])
        inp = os.path.join(work, 'in-%d.txt' % n)
        with open(inp, 'w', encoding='utf-8') as f:
            for d, bl in g:
                for b in bl:
                    t = ''
                    for r in b['runs']:
                        t += ('⟦%s:%s⟧' % (CS[r['cs']], r['t'])) if r.get('cs') in CS and r['t'].strip() else r['t']
                    f.write('%d | %s | %s | %s\n' % (b['i'], d, b['style'], t.replace('\n', ' ')))
        gem = os.path.join(work, 'gem-%d%s.md' % (n, '-g' if a.gemara_only else ''))
        with open(gem, 'w', encoding='utf-8') as f:
            for d, _ in g:
                pg = src['pages'].get(d)
                if not pg:
                    f.write('## %s\n(אין במקורות)\n\n' % d)
                    continue
                f.write('## %s\n### גמרא\n%s\n\n' % (d, '\n'.join(tag.sub('', x) for x in pg.get('gemara', []))))
                if not a.gemara_only:
                    f.write('### פירוש הגמרא\n%s\n\n' % '\n'.join(tag.sub('', x) for x in pg.get('perush', [])))
        tasks.append('- קבוצה %d (%s): קלט `%s`, מקור `%s`, פלט `%s`' % (
            n, rng, inp, gem, os.path.join(work, 'sem', '%s_%d.json' % ('G' if a.gemara_only else 'B', n))))
    open(os.path.join(work, 'tasks.md'), 'w', encoding='utf-8').write('\n'.join(tasks) + '\n')
    print('הוכנו', len(groups), 'קבוצות לשכבת המודל:', os.path.join(work, 'tasks.md'))

    # ה. העלאה
    if not a.no_push:
        import push
        push.push(out)


if __name__ == '__main__':
    main()
