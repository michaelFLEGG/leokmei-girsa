# -*- coding: utf-8 -*-
"""ingest_repo.py - מוריד את תיקוני האתר מן המאגר ומכניס אותם לוורד.

מצב העריכה שבדף דוחף כל תיקון ל-data/edits/<מסכת>.json שבמאגר. הכלי
הזה רץ במחשב של בעל הפרויקט כל עשר דקות, קורא את הקובץ הזה מן הענף
המרוחק בלי לגעת בעותק העבודה, ומכניס את התיקונים לקובץ הוורד שבדרייב
- דרך word_apply.py בלבד, במעקב-אחר-שינויים, עם גיבוי ואימות.

מה הוא לעולם אינו עושה:
א. אינו כותב לקובץ שפתוח בוורד. הוא מדלג, והתיקון ממשיך להיות מוצג
   באתר עד שהקובץ ייסגר.
ב. אינו דורס. אם הפסקה שונתה בוורד עצמו, העוגן אינו נמצא, התיקון
   מדווח כתלוש ונשאר בקובץ - הוורד גובר תמיד.
ג. אינו מוחק תיקון מן המאגר. הניקוי נעשה בבנייה, כשהנוסח החדש כבר
   נמצא בקובץ הוורד.

שימוש:
    uv run python tools/ingest_repo.py [--dry] [--repo <נתיב>]
    uv run python tools/ingest_repo.py --install-task   (מקים משימה מתוזמנת)
"""
import os, sys, io, re, html, json, shutil, argparse, subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import word_apply
from word_apply import apply, apply_struct, DRIVE, Refused
from ingest_edits import minimal_span, docx_for

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REMOTE = 'origin/main'
TASK = 'לאוקמי גירסא - קליטת תיקוני האתר'


def git(repo, *args):
    r = subprocess.run(['git', '-C', repo] + list(args),
                       capture_output=True)
    return r.returncode, r.stdout.decode('utf-8', 'replace'), r.stderr.decode('utf-8', 'replace')


def remote_edits(repo):
    """קורא את קובצי התיקונים מן הענף המרוחק, בלי לגעת בעותק העבודה."""
    code, _, err = git(repo, 'fetch', '--quiet', 'origin', 'main')
    if code:
        raise Refused('לא ניתן למשוך מן המאגר: ' + err.strip()[:200])
    code, out, _ = git(repo, 'ls-tree', '--name-only', REMOTE, 'data/edits/')
    if code:
        return []
    files = [l.strip() for l in out.splitlines() if l.strip().endswith('.json')]
    docs = []
    for f in files:
        code, out, _ = git(repo, 'show', REMOTE + ':' + f)
        if code:
            continue
        try:
            docs.append((f, json.loads(out)))
        except Exception as e:
            print('אזהרה: קובץ תיקונים פגום -', f, e)
    return docs


SPAN = re.compile(r'<i class="([a-z]+)">(.*?)</i>', re.S)


def _spans(h):
    """קטעי-התו שבנוסח: (שם המחלקה, הטקסט). ההשוואה ביניהם היא שמגלה
    איזה סגנון הוחל ואיזה הוסר."""
    out = []
    for m in SPAN.finditer(h or ''):
        t = html.unescape(re.sub('<[^>]+>', '', m.group(2))).strip()
        if t:
            out.append((m.group(1), t))
    return out


def ops_of(doc):
    """מפריד בין תיקוני נוסח ובין שינויי סגנון, ומחזיר שתי רשימות.

    הסדר חשוב: הנוסח נכתב תחילה, והסגנון אחריו - מפני שסגנון עשוי
    לחול על מילה שנוספה זה עתה, ובקובץ שלפני התיקון היא עדיין אינה."""
    wmap = {c[0]: c[2] for c in ((doc.get('sty') or {}).get('c') or [])}
    ops, sops, mops, skipped = [], [], [], []
    for e in doc.get('edits') or []:
        # ---- שינוי מבנה: פיצול פסקה או איחוי שתיים ----
        if e.get('op') == 'struct':
            mops.append({'kind': 'psplit' if e.get('kind') == 'split' else 'pmerge',
                         'texts': e.get('texts') or [], 'res': e.get('resT') or []})
            continue
        was, now = e.get('was', ''), e.get('now', '')
        if was != now:
            find, repl = minimal_span(was, now)
            if find or repl:
                ops.append({'daf': e.get('daf', ''), 'context': was, 'mark': find,
                            'find': find, 'replace': repl})
            else:
                skipped.append((e, 'אין הבדל'))
        # ---- סגנון פסקה ----
        if e.get('ps') is not None:
            name = e.get('psw') or ''
            if not name:
                skipped.append((e, 'שינוי סגנון פסקה בלי שם סגנון בוורד'))
            else:
                sops.append({'kind': 'pstyle', 'daf': e.get('daf', ''),
                             'context': now, 'style': name})
        # ---- סגנונות תו ----
        old_sp, new_sp = _spans(e.get('wasH')), _spans(e.get('nowH'))
        for cls, t in new_sp:
            if (cls, t) in old_sp:
                continue
            if cls == 'b':
                skipped.append((e, 'הדגשה ישירה על %r אינה סגנון בוורד' % t[:20]))
                continue
            name = wmap.get(cls)
            if not name:
                skipped.append((e, 'אין שם וורד לסגנון התו %r' % cls))
                continue
            sops.append({'kind': 'cstyle', 'daf': e.get('daf', ''), 'context': now,
                         'find': t, 'style': name})
        for cls, t in old_sp:
            if (cls, t) not in new_sp and not any(t == x[1] for x in new_sp):
                sops.append({'kind': 'cstyle', 'daf': e.get('daf', ''), 'context': now,
                             'find': t, 'style': ''})
    return ops, sops, mops, skipped


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', default=HERE)
    ap.add_argument('--dry', action='store_true')
    ap.add_argument('--install-task', action='store_true')
    a = ap.parse_args()
    if a.install_task:
        install_task(a.repo)
        return
    docs = remote_edits(a.repo)
    if not docs:
        print('אין תיקונים ממתינים במאגר')
        return
    for fname, doc in docs:
        masechet = doc.get('masechet') or ''
        ops, sops, mops, skipped = ops_of(doc)
        print('--- %s: %d תיקוני נוסח, %d שינויי סגנון, %d שינויי מבנה'
              % (masechet, len(ops), len(sops), len(mops)))
        for e, why in skipped:
            print('   דולג:', why, '|', (e.get('was') or '')[:50])
        if not ops and not sops and not mops:
            continue
        try:
            path = docx_for(masechet)
        except Refused as e:
            print('   ', e)
            continue
        if word_apply.is_open_in_word(path):
            print('   הקובץ פתוח בוורד. מדלג, והתיקונים ימשיכו להיות מוצגים באתר.')
            continue
        # שני מעברים: הנוסח תחילה, ואחריו הסגנון - שכן הסגנון עשוי לחול
        # על מילה שנוספה במעבר הראשון.
        for label, batch, fn in (('נוסח', ops, apply), ('סגנון', sops, apply),
                                 ('מבנה', mops, apply_struct)):
            if not batch:
                continue
            r = fn(path, batch, 'עריכה מהאתר', masechet, dry=a.dry)
            print('   %s:' % label,
                  json.dumps({k: v for k, v in r.items() if k != 'missed'},
                             ensure_ascii=False))
            for op, why in r['missed']:
                print('    לא הוחל (הוורד גובר):', why, '|',
                      op.get('find') or op.get('style') or op.get('kind'))


def install_task(repo):
    """מקים משימה מתוזמנת של חלונות, כל עשר דקות. בעל הפרויקט אינו
    מריץ דבר: הכלי מקים אותה בעצמו."""
    # הקובץ יושב ב-_שומר, שאינו נשמר במאגר. בתוך tools הוא היה מופיע
    # בכל `git status` של כל שיחה שעובדת כאן.
    keep = os.path.join(repo, '_שומר')
    os.makedirs(keep, exist_ok=True)
    bat = os.path.join(keep, 'קליטת-תיקונים.cmd')
    io.open(bat, 'w', encoding='utf-8-sig', newline='').write(
        '@echo off\r\n'
        'chcp 65001 > nul\r\n'
        'cd /d "%s"\r\n' % repo +
        # נתיב מלא ל-uv: ב-PATH של משימה מתוזמנת הוא אינו מוכר, והמשימה
        # היתה נכשלת בשקט ומדווחת הצלחה. נמדד בגשר.
        '"' + (shutil.which('uv') or os.path.join(
            os.path.expanduser('~'), '.local', 'bin', 'uv.exe')) +
        '" run --with lxml python tools\\ingest_repo.py >> "%s" 2>&1\r\n'
        % os.path.join(keep, 'קליטת-תיקונים.log'))
    cmd = ['schtasks', '/Create', '/F', '/TN', TASK, '/SC', 'MINUTE', '/MO', '10',
           '/TR', '"%s"' % bat]
    r = subprocess.run(cmd, capture_output=True)
    out = (r.stdout + r.stderr).decode('cp862', 'replace')
    print(out.strip() or 'המשימה הוקמה')
    if r.returncode:
        raise SystemExit('הקמת המשימה נכשלה')


if __name__ == '__main__':
    main()
