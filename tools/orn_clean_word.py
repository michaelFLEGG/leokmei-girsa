# -*- coding: utf-8 -*-
"""ניקוי עיטורים בקובצי הוורד (8.10.2026): חציצה/עיטור הצמודים לכותרת נמחקים במעקב
(חוקה 8.4). רק החלק הזה של שכבת העיצוב; שום תו של טקסט אינו משתנה.
    uv run --with lxml python tools/orn_clean_word.py [--אמת] [שם-קובץ ...]
בלי --אמת: הרצת יבש על עותק זמני. עם --אמת: גיבוי, כתיבה, ואימות שהטקסט זהה."""
import os, sys, glob, shutil, tempfile, io, contextlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'engine', 'laukmi-engine'))
import word_apply as wa
from docx2json import convert
from styles_map import role_of
import masechet_fmt

SKIP_ACTIVE = ('בכורות', 'סוכה')   # נקלטות עכשיו מנקודת הקליטה

def texts(path):
    return [b['text'] for b in convert(path) if role_of(b) != 'hatz']

def run(path, real):
    name = os.path.basename(path)
    tmp = tempfile.mktemp(suffix='.docx')
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        masechet_fmt.main(path, tmp, only_adjacent=True)
    n = sum(int(l.split(':')[1]) for l in buf.getvalue().splitlines() if 'נמחקה' in l)
    if not n:
        os.remove(tmp); return name, 0, 'אין מה לנקות'
    if texts(path) != texts(tmp):
        os.remove(tmp); return name, n, 'האימות נכשל - לא נכתב'
    if not real:
        os.remove(tmp); return name, n, 'יבש, תקין'
    if wa.is_open_in_word(path):
        os.remove(tmp); return name, n, 'פתוח בוורד - דולג'
    bk = wa.backup(path, 'עיטורים ' + os.path.splitext(name)[0][:20])
    shutil.copy2(tmp, path + '.new'); os.replace(path + '.new', path); os.remove(tmp)
    return name, n, 'נכתב; גיבוי: ' + os.path.basename(bk)

if __name__ == '__main__':
    real = '--אמת' in sys.argv
    only = [a for a in sys.argv[1:] if not a.startswith('--')]
    for f in sorted(glob.glob(os.path.join(wa.DRIVE, '*.docx'))):
        b = os.path.basename(f)
        if only and b not in only: continue
        if any(s in b for s in SKIP_ACTIVE) or 'מעודכן' in b: print(b, '- דולג (פעיל)'); continue
        print(*run(f, real), sep=' | ', flush=True)
