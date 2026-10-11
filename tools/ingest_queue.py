# -*- coding: utf-8 -*-
"""ingest_queue.py - הקליטה הלילית: מנקודת הקליטה אל הוורד, וגיבוי התור.

נקודת הקליטה (worker/leokmei-suggest) מחזיקה את עריכות המנהל ואת
ההצעות שהתקבלו, לכל מסכת. הכלי הזה רץ במחשב של בעל הפרויקט פעם בלילה:

א. מושך מכל מסכת את העריכות שטרם נכנסו לוורד (בלי סימון ing).
ב. מכניס אותן לקובץ הוורד שבדרייב דרך word_apply.py בלבד, בכל כלליו:
   נעילה, גיבוי, מעקב-אחר-שינויים, החלפה מינימלית ואימות. שם המחבר
   הוא של העריכה עצמה: "עריכה מהאתר" למנהל, ו"הצעה מהאתר - <שם>"
   להצעה שהתקבלה.
ג. קובץ שפתוח בוורד אינו נכתב; מנסים שוב בלילה הבא.
ד. מה שנכנס מסומן בנקודת הקליטה כנקלט, כדי שלא ייכנס פעמיים.
ה. יצוא מלא של התור והארכיון ל-C:\\leokmei-girsa-backup\\הצעות - מחוץ
   לריפו ומחוץ לדרייב המשותף, כי יש בהם שמות מציעים.

המפתח הסודי נקרא מ-C:\\Users\\Owner\\Documents\\לאוקמי-מפתח-מנהל.txt
בלבד, ואינו נכתב לשום מקום אחר.

שימוש:
    uv run --with lxml python tools/ingest_queue.py [--dry]
    uv run --with lxml python tools/ingest_queue.py --install-task
"""
import os, sys, io, json, argparse, subprocess, datetime, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import word_apply
from word_apply import apply, apply_struct, Refused
from ingest_edits import docx_for, minimal_span
from ingest_repo import ops_of

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = 'https://leokmei-suggest.m7654301.workers.dev'
KEY_FILE = r'C:\Users\Owner\Documents\לאוקמי-מפתח-מנהל.txt'
BACKUP = r'C:\leokmei-girsa-backup\הצעות'
TASK = 'לאוקמי גירסא - קליטה לילית של ההצעות'


def admin_key():
    if not os.path.exists(KEY_FILE):
        raise Refused('קובץ מפתח המנהל אינו קיים: ' + KEY_FILE)
    lines = [l.strip() for l in io.open(KEY_FILE, encoding='utf-8-sig').read().splitlines() if l.strip()]
    # השורה האחרונה שאינה עברית היא המפתח
    for l in reversed(lines):
        if all(ord(c) < 128 for c in l) and len(l) >= 20:
            return l
    raise Refused('לא נמצא מפתח בקובץ המפתח')


def call(path, method='GET', body=None, key=None):
    data = json.dumps(body, ensure_ascii=False).encode('utf-8') if body is not None else None
    req = urllib.request.Request(API + path, data=data, method=method)
    req.add_header('content-type', 'application/json; charset=utf-8')
    # בלי כותרת דפדפן קלאודפלייר משיב 403 (קוד 1010) לסוכן הפייתון הרגיל
    req.add_header('user-agent', 'Mozilla/5.0 leokmei-ingest/1.0')
    if key:
        req.add_header('x-admin-key', key)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        raise Refused('נקודת הקליטה השיבה %d על %s: %s' % (e.code, path, e.read().decode('utf-8', 'replace')[:200]))
    except Exception as e:
        raise Refused('אין חיבור לנקודת הקליטה: %s' % e)


def backup_export(exp):
    os.makedirs(BACKUP, exist_ok=True)
    stamp = datetime.datetime.now().strftime('%Y-%m-%d %H-%M')
    p = os.path.join(BACKUP, 'תור-ההצעות %s.json' % stamp)
    io.open(p, 'w', encoding='utf-8').write(json.dumps(exp, ensure_ascii=False, indent=1))
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry', action='store_true')
    ap.add_argument('--install-task', action='store_true')
    a = ap.parse_args()
    if a.install_task:
        install_task()
        return
    print('=== %s' % datetime.datetime.now().strftime('%d.%m.%Y %H:%M'))
    key = admin_key()
    exp = call('/export', key=key)
    bp = backup_export(exp)
    print('גיבוי התור:', bp, '(%d הצעות, %d מסכתות עם עריכות)'
          % (len(exp.get('suggestions') or []), len(exp.get('edits') or {})))
    for slug, doc in (exp.get('edits') or {}).items():
        edits = [e for e in doc.get('edits') or [] if not e.get('del') and not e.get('ing')]
        if not edits:
            continue
        masechet = doc.get('masechet') or ''
        if not masechet:
            # שם המסכת נלקח מן האתר הבנוי, לפי המזהה
            import build_all
            rev = {v: k for k, v in build_all.SLUG.items()}
            masechet = rev.get(slug, '')
        if not masechet:
            print('--- %s: לא זוהתה המסכת, מדלג' % slug)
            continue
        print('--- %s (%s): %d עריכות ממתינות לקליטה' % (masechet, slug, len(edits)))
        try:
            path = docx_for(masechet)
        except Refused as e:
            print('   ', e)
            continue
        if word_apply.is_open_in_word(path):
            print('   הקובץ פתוח בוורד. מדלג; ינוסה שוב בלילה הבא.')
            continue
        # מקבצים לפי שם המחבר: word_apply כותב מנה בשם אחד
        by_author = {}
        for e in edits:
            by_author.setdefault(e.get('by') or 'עריכה מהאתר', []).append(e)
        done_keys = []
        for author, group in by_author.items():
            ops, sops, mops, skipped = ops_of({'edits': group, 'sty': doc.get('sty')})
            for e, why in skipped:
                print('   דולג (%s): %s | %s' % (author, why, (e.get('was') or '')[:50]))
            for label, batch, fn in (('נוסח', ops, apply), ('סגנון', sops, apply),
                                     ('מבנה', mops, apply_struct)):
                if not batch:
                    continue
                r = fn(path, batch, author, masechet, dry=a.dry)
                print('   %s (%s):' % (label, author),
                      json.dumps({k: v for k, v in r.items() if k not in ('missed', 'plan')}, ensure_ascii=False))
                for op, why in r['missed']:
                    print('    לא הוחל (הוורד גובר):', why, '|', op.get('find') or op.get('style') or op.get('kind'))
                if r.get('verified') and r.get('applied') and not a.dry:
                    # רק עריכה שהנוסח שלה נכתב ואומת מסומנת כנקלטת
                    missed_find = {o.get('find') for o, _ in r['missed']}
                    missed_struct = {json.dumps(o.get('texts'), ensure_ascii=False) for o, _ in r['missed']}
                    for e in group:
                        if e.get('op') == 'struct':
                            if label == 'מבנה' and json.dumps(e.get('texts'), ensure_ascii=False) not in missed_struct:
                                done_keys.append(e['k'])
                            continue
                        if label != 'נוסח':
                            continue
                        f, _ = minimal_span(e.get('was', ''), e.get('now', ''))
                        if f and f not in missed_find:
                            done_keys.append(e['k'])
        if done_keys and not a.dry:
            r = call('/ingested', 'POST', {'slug': slug, 'keys': sorted(set(done_keys))}, key=key)
            print('   סומנו כנקלטות בנקודת הקליטה: %d' % r.get('marked', 0))


def install_task():
    """משימה מתוזמנת של חלונות, כל עשר דקות (קובץ שפתוח בוורד מדולג ונקלט בסבב הבא). בעל הפרויקט אינו מריץ דבר."""
    keep = os.path.join(HERE, '_שומר')
    os.makedirs(keep, exist_ok=True)
    bat = os.path.join(keep, 'קליטה-לילית.cmd')
    io.open(bat, 'w', encoding='utf-8-sig', newline='\r\n').write(
        '@echo off\r\n'
        'chcp 65001 > nul\r\n'
        'cd /d "%s"\r\n' % HERE +
        'uv run --with lxml python tools\\ingest_queue.py >> "%s" 2>&1\r\n'
        % os.path.join(keep, 'קליטה-לילית.log'))
    cmd = ['schtasks', '/Create', '/F', '/TN', TASK, '/SC', 'MINUTE', '/MO', '10',
           '/TR', '"%s"' % bat]
    r = subprocess.run(cmd, capture_output=True)
    out = (r.stdout + r.stderr).decode('cp862', 'replace')
    print(out.strip() or 'המשימה הוקמה')
    if r.returncode:
        raise SystemExit('הקמת המשימה נכשלה')


if __name__ == '__main__':
    main()
