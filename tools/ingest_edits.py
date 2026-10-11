# -*- coding: utf-8 -*-
"""ingest_edits.py - קולט את קובץ התיקונים שירד מן האתר, ומכניס אותו לוורד.

הקובץ נוצר בכפתור "הורד את כל התיקונים" שבמצב העריכה, או ב"העתק ללוח".
בסופו בלוק JSON שנקרא כאן; החלק הקריא שמעליו הוא לבעל הפרויקט בלבד.

הכתיבה עצמה נעשית ב-word_apply.py, ורק בו: נעילה, גיבוי, מעקב, החלפה
מינימלית ואימות. כאן נעשית רק ההמרה מ"הנוסח שהיה" ו"הנוסח שיהיה"
להחלפה הקטנה ביותר שביניהם.

שימוש:
    uv run python tools/ingest_edits.py --file "<נתיב לקובץ>" [--dry]
בלי --file: מחפש את הקובץ האחרון שמתחיל ב"תיקוני-" בתיקיית ההורדות.
"""
import os, sys, json, re, io, argparse, glob

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import word_apply
from word_apply import apply, DRIVE, Refused

DOWNLOADS = r'C:\Users\Owner\Downloads'
MARK = '==== נתוני עיבוד'

# שם הקובץ בדרייב לכל מסכת נגזר מן המסכת שברשומה. הקובץ מזוהה לפי
# השם שבו נבנתה המסכת, כפי שרשם אותו build_all.
def docx_for(masechet):
    import build_all
    status = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          'site', 'status.json')
    if os.path.exists(status):
        st = json.load(io.open(status, encoding='utf-8'))
        rec = (st.get('built') or {}).get(masechet)
        if rec and rec.get('file'):
            f = rec['file'].split(' + ')[0]
            p = os.path.join(DRIVE, f)
            if os.path.exists(p):
                return p
    # נפילה לאחור: חיפוש לפי שם המסכת בתיקיית הדרייב
    hits = [f for f in os.listdir(DRIVE)
            if f.endswith('.docx') and not f.startswith('~$') and masechet in f]
    if len(hits) == 1:
        return os.path.join(DRIVE, hits[0])
    raise Refused('לא זוהה קובץ הוורד של מסכת %s (נמצאו %d)' % (masechet, len(hits)))


def minimal_span(was, now):
    """ההחלפה הקטנה ביותר שהופכת was ל-now.

    חותכים תחילית וסופית משותפות, ואז מרחיבים עד שהקטע אינו ריק והוא
    יחיד בפסקה. שני התנאים נחוצים: קטע ריק הוא תוספת טהורה שאין לה מה
    להחליף, וקטע שחוזר בפסקה היה נופל על המופע הלא נכון."""
    a, b = 0, 0
    while a < len(was) and a < len(now) and was[a] == now[a]:
        a += 1
    while (b < len(was) - a and b < len(now) - a
           and was[len(was) - 1 - b] == now[len(now) - 1 - b]):
        b += 1

    def span(a, b):
        return was[a:len(was) - b], now[a:len(now) - b]

    find, repl = span(a, b)
    while (not find or was.count(find) > 1) and (a > 0 or b > 0):
        if a > 0:
            a -= 1
        else:
            b -= 1
        find, repl = span(a, b)
    return find, repl


def parse(path):
    txt = io.open(path, encoding='utf-8-sig').read()
    k = txt.rfind(MARK)
    if k < 0:
        raise Refused('אין בקובץ בלוק נתוני עיבוד. ודא שהוא ירד מן האתר ולא נערך')
    blob = txt[k:].split('\n', 1)[1].strip()
    return json.loads(blob)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--file')
    ap.add_argument('--dry', action='store_true')
    a = ap.parse_args()
    path = a.file
    if not path:
        cands = sorted(glob.glob(os.path.join(DOWNLOADS, 'תיקוני-*.txt')),
                       key=os.path.getmtime, reverse=True)
        if not cands:
            raise Refused('לא נמצא קובץ "תיקוני-..." בתיקיית ההורדות')
        path = cands[0]
    print('קורא:', path)
    d = parse(path)
    masechet = d.get('masechet') or ''
    edits = d.get('edits') or []
    print('מסכת %s, %d תיקונים' % (masechet, len(edits)))
    ops, skipped = [], []
    for e in edits:
        if e.get('lost'):
            skipped.append((e, 'תלוש - הפסקה השתנתה בוורד'))
            continue
        find, repl = minimal_span(e['was'], e['now'])
        if not find and not repl:
            skipped.append((e, 'אין הבדל'))
            continue
        ops.append({'daf': e.get('daf', ''), 'context': e['was'], 'mark': find,
                    'find': find, 'replace': repl})
    print('מוכנים להכנסה: %d' % len(ops))
    for o in ops:
        print('   דף %-5s  %r  ⟵  %r' % (o['daf'], o['find'], o['replace']))
    for e, why in skipped:
        print('   דולג:', why, '|', e['was'][:50])
    if not ops:
        return
    doc = docx_for(masechet)
    print('קובץ הוורד:', doc)
    r = apply(doc, ops, 'עריכה מהאתר', masechet, dry=a.dry)
    print(json.dumps({k: v for k, v in r.items() if k != 'missed'}, ensure_ascii=False))
    for op, why in r['missed']:
        print('לא הוחל:', why, '|', op.get('find'))


if __name__ == '__main__':
    main()
