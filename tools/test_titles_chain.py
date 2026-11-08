# -*- coding: utf-8 -*-
"""בדיקת השרשרת "קבל" בסקירת הכותרות -> וורד (8.11.2026).

קבלה של הצעת "כותרת צד ארוכה / כפילות" (סוג k) רושמת באתר שתי עריכות:
  א. struct split ins:1 where:'after' בסגנון נושא, על הפסקה שלפני היחידה;
  ב. עריכת טקסט של חלון הכותרת (u<N>.0): נוסח מקוצר, או ריק = מחיקת הכותרת.
הבדיקה מחילה את שתיהן דרך ingest_repo._apply_one על עותק זמני של בכורות
(הקובץ החי אינו נוגע) ובודקת: כותרת הנושא נכנסה לפני מסגרת הצד ובסגנון "נושא";
כותרת צד מקוצרת; כותרת צד שנמחקה נעלמה כולה (pdelwin) ולא נשארה מסגרת ריקה.

    uv run --with lxml python tools/test_titles_chain.py
"""
import os, sys, shutil, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.chdir(os.path.dirname(HERE))
import word_apply, ingest_repo
from docx2json import convert
from styles_map import role_of

SRC = os.path.join('input', 'docx', 'בכורות מעודכן 2.docx')
H = 'קשה הלכתא על ההלכה!'
HEAD = 'הלכתא על ההלכה!'
A = 'הלכתא ברגיא, וכמה? שלושה זוזים, רגיל כאן ורגיל כאן.'
B = 'לא קשה, כאן - בבא לימלך, כאן - בעושה מעצמו.'


def run(now):
    T = tempfile.mkdtemp(prefix='lg-titles-')
    p = os.path.join(T, 'bekhorot.docx')
    shutil.copy(SRC, p)
    e1 = {'op': 'struct', 'kind': 'split', 'ins': 1, 'where': 'after', 'texts': [A],
          'resT': [A, HEAD], 'psw': 'נושא', 'daf': 'יא.', 't': 1, 'pub': 0}
    e2 = {'k': 'u655.0~2', 'was': H, 'now': now, 'wasH': H, 'nowH': now, 'daf': 'יא.',
          'ctx': {'b': A[-40:], 'a': B[:40]}, 't': 2, 'pub': 0}
    for e in (e1, e2):
        r = ingest_repo._apply_one(p, e, {'sty': None}, 'בכורות', None, lambda *a: None, False)
        assert r['applied'] == 1 and not r.get('failed'), (e.get('kind') or 'text', r)
    out = convert(p)
    shutil.rmtree(T, ignore_errors=True)
    ia = [i for i, b in enumerate(out) if b['text'].strip() == A]
    assert len(ia) == 1, 'פסקת A'
    return out[ia[0] + 1:ia[0] + 4]


def main():
    if not os.path.exists(SRC):
        print('דילוג: אין עותק בכורות ב-input/docx (תיקיית קוד בלבד)')
        return 0
    word_apply.backup = lambda path, m: '(עותק בדיקה)'
    n = 0
    # א. כותרת נושא + כותרת צד מקוצרת
    nx = run('קשה')
    assert nx[0]['text'].strip() == HEAD and nx[0]['style'] == 'נושא', nx[0]
    assert role_of(nx[1]) == 'anchor' and nx[1]['text'].strip() == 'קשה', nx[1]
    assert nx[2]['text'].strip() == B, nx[2]
    n += 1
    # ב. כותרת נושא + מחיקת כותרת הצד: אין מסגרת, השורה מיד אחרי כותרת הנושא
    nx = run('')
    assert nx[0]['text'].strip() == HEAD and nx[0]['style'] == 'נושא', nx[0]
    assert nx[1]['text'].strip() == B and role_of(nx[1]) == 'body', nx[1]
    n += 1
    # ג. המיפוי: מחיקה מלאה של חלון -> pdelwin; קיצור -> תיקון טקסט; גוף שהתרוקן -> לא pdelwin
    ops, _, mops, _ = ingest_repo.ops_of({'edits': [{'k': 'u9.0~5', 'was': H, 'now': ''}]})
    assert not ops and mops and mops[0]['kind'] == 'pdelwin', (ops, mops)
    ops, _, mops, _ = ingest_repo.ops_of({'edits': [{'k': 'u9.w', 'was': H, 'now': 'קשה'}]})
    assert ops and not mops
    ops, _, mops, _ = ingest_repo.ops_of({'edits': [{'k': 'u9.1', 'was': B, 'now': ''}]})
    assert not mops
    n += 1
    print('עברו %d בדיקות השרשרת (כותרת נושא, כותרת צד מקוצרת, כותרת צד שנמחקה)' % n)
    return 0


if __name__ == '__main__':
    sys.exit(main())
