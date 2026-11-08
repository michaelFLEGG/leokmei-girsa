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
            kind = e.get('kind')
            if e.get('ins'):
                # פסקה חדשה מ-Enter: res = נוסח שתי הפסקאות לפי סדרן, where = איזו חדשה
                mops.append({'kind': 'pins', 'texts': e.get('texts') or [],
                             'res': e.get('resT') or [], 'where': e.get('where') or 'after',
                             'style': e.get('psw') or '', 'daf': e.get('daf', '')})
            elif kind in ('split', 'merge'):
                mops.append({'kind': 'psplit' if kind == 'split' else 'pmerge',
                             'texts': e.get('texts') or [], 'res': e.get('resT') or []})
            elif kind == 'hsplit':
                # כותרת בשתיים: פיצול הפסקה, ואחריו הפסקה השנייה מקבלת את סגנון הגוף
                mops.append({'kind': 'phsplit', 'texts': e.get('texts') or [],
                             'res': e.get('resT') or [], 'style': e.get('psw') or '',
                             'daf': e.get('daf', '')})
            elif kind == 'hmerge':
                mops.append({'kind': 'pmerge', 'texts': e.get('texts') or [],
                             'res': e.get('resT') or []})
            elif kind in ('hdel', 'hrep'):
                # עיטור (***): מחיקה, או החלפה בכותרת (נושא / ד"ה משנה) שנכתב בה טקסט.
                # texts=[הפסקה שלפני, הפסקה שאחרי]; res=נוסח הכותרת החדשה; style=שם הסגנון בוורד
                mops.append({'kind': 'pdel' if kind == 'hdel' else 'prep',
                             'texts': e.get('texts') or [], 'res': e.get('resT') or [],
                             'style': e.get('psw') or '', 'daf': e.get('daf', '')})
            elif kind in ('side', 'unside'):
                # כותרת צד (Ctrl+נקודה): res[0]=[סגנון, גוף], res[1]=[חלון],
                # res[2]=[היסט החיתוך, אורכו] בתוך הנוסח שהיה.
                mops.append({'kind': 'pside' if kind == 'side' else 'punside',
                             'texts': e.get('texts') or [], 'res': e.get('resT') or [],
                             'cut': (e.get('res') or [None, None, None])[2] if kind == 'side' else None})
            elif kind == 'unside-merge':
                # Delete על שורה שיש לה כותרת צד: texts=[עליונה, תחתונה, ...כותרות שנמחקו],
                # res[2]=[up|down] - לאן עובר מה שמוגן (ציון דף, משנה בצד, גופא)
                t = e.get('texts') or []
                mops.append({'kind': 'pusm', 'texts': t[:2], 'side': t[2:], 'res': e.get('resT') or [],
                             'where': ((e.get('res') or [None, None, ['up']])[2:] or [['up']])[0][0],
                             'daf': e.get('daf', '')})
            else:
                # סוג מבנה לא מוכר: לעולם לא נופל לאיחוי. נאמר ומדולג.
                skipped.append((e, 'סוג שינוי מבנה לא מוכר: %r' % kind))
            continue
        was, now = e.get('was', ''), e.get('now', '')
        # ---- כותרת צד שנמחקה כולה (8.11.2026): מחיקת הפסקה, לא ריקון טקסט ----
        # ריקון כתיקון טקסט נכשל תמיד באימות (הפסקה הריקה נעלמת מן ההמרה).
        if re.match(r'^u\d+\.(0|w)(~|$)', e.get('k') or '') and was.strip() and not now.strip():
            mops.append({'kind': 'pdelwin', 'texts': [was], 'daf': e.get('daf', ''),
                         'after': (e.get('ctx') or {}).get('a', '')})
            continue
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


def replay_plan(masechet, doc, docx_path):
    """מריץ את אותה הרצה שהאתר מריץ בכל בנייה (build_site._apply_site_edits) על קובץ
    הוורד כפי שהוא עכשיו, ומחזיר את התוכנית האפקטיבית: לכל תיקון - מה הוחל בפועל,
    ובאיזה נוסח פסקה (ולא נוסח המקור שרשם הדפדפן, שאינו תקף אחרי פיצולים וחיתוכים).
    בלי זה כל שרשרת פיצולים הפילה את אימות האצווה כולה, ושום תיקון לא הגיע לוורד."""
    import tempfile
    import build_site as B
    import build_all
    from docx2json import convert
    slug = build_all.SLUG[masechet]
    T = tempfile.mkdtemp(prefix='lg-replay-')
    io.open(os.path.join(T, slug + '.json'), 'w', encoding='utf-8').write(
        json.dumps(doc, ensure_ascii=False))
    blocks = convert(docx_path)
    bj = os.path.join(T, slug + '_blocks.json')
    json.dump(blocks, io.open(bj, 'w', encoding='utf-8'), ensure_ascii=False)
    sp = os.path.join(HERE, 'data', 'sources', slug + '.json')
    sources = json.load(io.open(sp, encoding='utf-8')) if os.path.exists(sp) else None
    if sources:
        import perush_store
        perush_store.attach(sources, slug)
    # הבנייה כותבת לכמה תיקיות נתונים במאגר (sections, mbox, dhmiss, nikud-nakdan).  
    # הן נגזרות ואינן חלק מהקליטה: אם נקיות לפני, מחזירים אותן אחרי, כדי שלא יישאר עץ מלוכלך
    # שיכשיל את ה-pull של הקולט המתוזמן.
    derived = ['data/sections', 'data/mbox', 'data/dhmiss', 'data/nikud-nakdan']
    _c, dirty_before, _e = git(HERE, 'status', '--porcelain', '--', *derived)
    was_clean = not dirty_before.strip()
    old = B.EDITS_DIR
    B.EDITS_DIR = T
    real_ase = B._apply_site_edits
    got = {}

    def ase(*a, **k):
        r = real_ase(*a, **k)
        got['r'] = r
        return r
    B._apply_site_edits = ase
    try:
        B.build(bj, os.path.join(T, slug + '.html'), masechet, hagaha=False,
                sources=sources, spacing={})
        plan = list(B.PLAN)
    finally:
        B.EDITS_DIR = old
        B._apply_site_edits = real_ase
        shutil.rmtree(T, ignore_errors=True)
        if was_clean:
            git(HERE, 'checkout', '--', *derived)
    # התיקונים שהבנייה מצאה (הוחלו או "כבר בוורד") - לפי זמן הרישום. השאר תלושים.
    LAST['found'] = set((got.get('r') or {}).get('b') or [])
    return plan


LAST = {'found': set()}


def _apply_one(path, e, doc, masechet, bk, log, dry):
    """תיקון אחד לוורד, באותו סדר שבו הוא נעשה. כישלון בו אינו עוצר את האחרים."""
    ops, sops, mops, skipped = ops_of({'sty': doc.get('sty'), 'edits': [e]})
    res = {'applied': 0, 'missed': [(o, why) for o, why in [(x[0], x[1]) for x in skipped]]}
    for batch, fn in ((ops, apply), (sops, apply), (mops, apply_struct)):
        if not batch:
            continue
        r = fn(path, batch, 'עריכה מהאתר', masechet, log=log, dry=dry)
        res['applied'] += r.get('applied') or 0
        res['missed'] += r.get('missed') or []
        if r.get('verified') is False:
            res['failed'] = True
    return res


# ---------------------------------------------------------------- יומן הקליטה (7.11.2026)
# הבאג (6.11.2026, כתובות וסוכה): הבנייה מריצה את כל היסטוריית התיקונים מעל הוורד
# הנוכחי, ומחליטה לכל תיקון בנפרד אם הוא "כבר בוורד". כשתיקון מאוחר מבטל את מראהו של
# תיקון מוקדם (כותרת צד, ואחריה unside ואיחוי, ואחריה כותרת צד חדשה), המוקדם נראה
# "לא נעשה" - והקולט כתב אותו לוורד שוב בכל סבב של עשר דקות. התוצאה: כותרות צד כפולות,
# "כותרת ואותה שורה בגוף", ותיקוני נוסח שנכתבו שוב על נוסח מתוקן.
# התיקון: הקולט זוכר מה כבר הכניס לכל קובץ חי. תיקון שכבר נקלט (הוחל, או נבדק ולא
# הוחל) אינו נכתב שוב לעולם. אם בעל הפרויקט דחה אותו בוורד - הוורד גובר.
# היומן יושב ב-_שומר שליד הקבצים החיים (לא במאגר). שחזור הקובץ החי מצילום מאפס אותו:
#     uv run --with lxml python tools/ingest_repo.py --restore-from <צילום.docx> --only <מסכת>

def ledger_path(path):
    d = os.path.join(word_apply.DRIVE, '_שומר', 'יומן קליטה')
    return os.path.join(d, os.path.splitext(os.path.basename(path))[0] + '.json')


def edit_key(e):
    """מפתח יציב לתיקון: זמן הרישום ותוכנו (לא השדות שהבנייה מוסיפה לו)."""
    import hashlib
    core = {k: e.get(k) for k in ('t', 'op', 'kind', 'was', 'now', 'wasH', 'nowH',
                                  'texts', 'resT', 'res', 'ps', 'psw', 'ins', 'where')}
    h = hashlib.sha1(json.dumps(core, ensure_ascii=False, sort_keys=True).encode('utf-8')).hexdigest()[:16]
    return '%s:%s' % (e.get('t'), h)


def _sha(path):
    import hashlib
    with open(path, 'rb') as f:
        return hashlib.sha1(f.read()).hexdigest()


def load_ledger(path):
    """done: נקלטו (נכתבו, נבדקו, או נמצאו כבר בוורד) - לעולם אינם נכתבים שוב.
    lost: היו תלושים. מנוסים שוב רק אם הקובץ החי השתנה מאז הסבב האחרון שלא בידי
    הקולט (בעל הפרויקט ערך בוורד) - שינוי של הקולט עצמו אינו "מגלה" להם עוגן חדש."""
    try:
        d = json.load(io.open(ledger_path(path), encoding='utf-8'))
    except (OSError, ValueError):
        d = {}
    return set(d.get('done') or []), set(d.get('lost') or []), d.get('sha')


def save_ledger(path, done, lost=(), sha=None):
    lp = ledger_path(path)
    os.makedirs(os.path.dirname(lp), exist_ok=True)
    tmp = lp + '.%d.tmp' % os.getpid()
    io.open(tmp, 'w', encoding='utf-8').write(json.dumps(
        {'file': os.path.basename(path), 'sha': sha, 'done': sorted(done),
         'lost': sorted(set(lost) - set(done))}, ensure_ascii=False, indent=0))
    os.replace(tmp, lp)


def adjacent_dups(path):
    """מספר הפסקאות הצמודות בעלות נוסח זהה (כל סגנון: כותרת-כותרת, כותרת-גוף, גוף-גוף)."""
    from docx2json import convert
    v = [word_apply._nw(b['text']) for b in convert(path)]
    return sum(1 for a, b in zip(v, v[1:]) if a and a == b)


def restore_from(src, masechet, log=print):
    """שלבים ג-ד של 6.11.2026: מחליף את הקובץ החי בצילום, אחרי גיבוי, ומאפס את היומן."""
    path = docx_for(masechet)
    if word_apply.is_open_in_word(path):
        raise Refused('הקובץ פתוח בוורד. יש לסגור אותו ולהריץ שוב.')
    # נקרא מתוך main, שכבר רץ בתוך word_apply.writer_lock()
    bk = word_apply.backup(path, masechet)
    log('גיבוי של הקובץ החי: ' + bk)
    tmp = word_apply.tmp_path(path)
    shutil.copyfile(src, tmp)
    word_apply.swap(tmp, path)
    try:
        os.remove(ledger_path(path))
    except OSError:
        pass
    log('הקובץ החי הוחלף בתוכן של %s, ויומן הקליטה אופס.' % src)


def ingest_replay(masechet, doc, path, dry, log=print):
    """קליטה לפי ההרצה: תיקון אחר תיקון, לפי הסדר. גיבוי אחד לפני הכתיבה הראשונה.
    תיקון שכבר רשום ביומן הקליטה של הקובץ אינו נכתב שוב; וכתיבה שהיתה יוצרת פסקאות
    צמודות זהות מבוטלת ונאמרת."""
    plan = replay_plan(masechet, doc, path)
    done_keys, lost_keys, sha = load_ledger(path)
    touched_outside = sha is not None and sha != _sha(path)
    skip = done_keys | (set() if touched_outside else lost_keys)
    full = len(plan)
    plan = [x for x in plan if edit_key(x[1]) not in skip]
    log('   תוכנית: %d תיקונים שהאתר מחיל בפועל; %d מהם כבר נקלטו בעבר ומדולגים'
        % (full, full - len(plan)))
    # מה שהבנייה מצאה כבר בוורד ואינו בתוכנית - נרשם כנקלט עכשיו, לפני הכתיבה: אחרי
    # שתיקון מאוחר יותר ייכתב, הוא עלול להיראות "לא נעשה" ולהיכתב שוב (לפני רבי:, ה"ק:)
    in_plan = {edit_key(x[1]) for x in plan}
    found = LAST.get('found') or set()
    for e in doc.get('edits') or []:
        k = edit_key(e)
        if k in in_plan:
            continue
        if e.get('t') in found:
            done_keys.add(k)
        else:
            lost_keys.add(k)
    if not dry:
        save_ledger(path, done_keys, lost_keys, _sha(path))
    state = {'bk': None}
    real_backup = word_apply.backup

    def one_backup(p, m):
        if state['bk'] is None:
            state['bk'] = real_backup(p, m)
        return state['bk']

    word_apply.backup = one_backup
    ok = bad = dup = 0
    dups = None if dry else adjacent_dups(path)
    keep = word_apply.tmp_path(path) + '.before'
    try:
        for item in plan:
            if item[0] == 'struct':
                e = item[1]
            else:
                e = dict(item[1], was=item[2]['was'], wasH=item[2]['wasH'])
            if not dry:
                shutil.copyfile(path, keep)
            try:
                r = _apply_one(path, e, doc, masechet, None, lambda *a: None, dry)
            except Refused as x:
                log('   נעצר: %s' % x)
                break
            if not dry:
                # בדיקת ביטחון: כתיבה שהוסיפה פסקאות צמודות זהות - מוחזרת, ונאמרת
                now_d = adjacent_dups(path)
                if now_d > dups:
                    word_apply.swap(keep, path)
                    dup += 1
                    log('    לא נכתב (היה יוצר פסקה כפולה): %s'
                        % ((e.get('now') or ' | '.join(e.get('resT') or []))[:60]))
                    r = {'applied': 0, 'missed': [(e, 'כפילות')]}
                else:
                    dups = now_d
                done_keys.add(edit_key(item[1]))
                save_ledger(path, done_keys, lost_keys, _sha(path))
            if r.get('failed') or (r['applied'] == 0 and r['missed']):
                bad += 1
                for o, why in r['missed'][:2]:
                    log('    לא הוחל (הוורד גובר): %s | %s' % (
                        why, (o.get('find') or o.get('style') or o.get('kind') or '')[:40]))
            else:
                ok += r['applied'] and 1 or 0
    finally:
        word_apply.backup = real_backup
        try:
            os.remove(keep)
        except OSError:
            pass
    log('   הוחלו %d תיקונים, %d לא (מהם %d שהיו יוצרים כפילות)' % (ok, bad, dup))
    return ok, bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', default=HERE)
    ap.add_argument('--dry', action='store_true')
    ap.add_argument('--only', default=None, help='שם מסכת בלבד')
    ap.add_argument('--legacy', action='store_true', help='הקליטה הישנה, אצווה אחת')
    ap.add_argument('--docx', default=None, help='קובץ וורד לבדיקה (במקום זה שבדרייב)')
    ap.add_argument('--install-task', action='store_true')
    ap.add_argument('--restore-from', default=None,
                    help='צילום docx שמחליף את הקובץ החי של --only (גיבוי לפני, ואיפוס יומן הקליטה)')
    a = ap.parse_args()
    if a.install_task:
        install_task(a.repo)
        return
    if a.restore_from:
        if not a.only:
            raise SystemExit('--restore-from דורש --only <מסכת>')
        restore_from(a.restore_from, a.only)
        return
    docs = remote_edits(a.repo)
    if not docs:
        print('אין תיקונים ממתינים במאגר')
        return
    for fname, doc in docs:
        masechet = doc.get('masechet') or ''
        if a.only and masechet != a.only:
            continue
        ops, sops, mops, skipped = ops_of(doc)
        print('--- %s: %d תיקוני נוסח, %d שינויי סגנון, %d שינויי מבנה'
              % (masechet, len(ops), len(sops), len(mops)))
        for e, why in skipped:
            print('   דולג:', why, '|', (e.get('was') or '')[:50])
        if not ops and not sops and not mops:
            continue
        try:
            path = a.docx or docx_for(masechet)
        except Refused as e:
            print('   ', e)
            continue
        if word_apply.is_open_in_word(path):
            print('   הקובץ פתוח בוורד. מדלג, והתיקונים ימשיכו להיות מוצגים באתר.')
            continue
        if not a.legacy:
            ingest_replay(masechet, doc, path, a.dry)
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
    # כותב אחד לוורד בכל רגע: קליטת ההצעות רצה גם היא כל עשר דקות
    try:
        with word_apply.writer_lock():
            main()
    except Refused as e:
        raise SystemExit(str(e))
