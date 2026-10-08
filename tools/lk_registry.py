# -*- coding: utf-8 -*-
"""lk_registry.py - מרשם מפתחות הטקסט (8.10.2026).

קולט את תוצר הקציר (tools/lk/harvest.js, שרץ בדפדפן על האתר המקומי), ומעדכן:
  tools/lk/texts-registry.json  - "היקף|סוג|טקסט מקורי" -> מפתח (נטען לאתר כ-lk-texts.json)
  docs/TEXTS.md                 - הרשימה לקריאה, לפי היקף ודף
המרשם רק גדל: מפתח שכבר נרשם אינו נמחק גם אם הרכיב נעלם, וכך שינוי שנשמר עבורו
יוצג בדף "טקסטים ששיניתי" כיתום ולא ייעלם בשקט.

שימוש: uv run python tools/lk_registry.py <קובץ-קציר.json> [<עוד קציר.json> ...]"""
import io, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REG = os.path.join(HERE, 'lk', 'texts-registry.json')
MD = os.path.join(ROOT, 'docs', 'TEXTS.md')
SCOPE_HE = {'home': 'בית', 'shas': 'מפת הש"ס', 'masechtot': 'רשימת מסכתות', 'yomi': 'הדף היומי', 'lamed': 'המקום שלי', 'quiz': 'בחן את עצמך',
            'shiurim': 'שיעורים', 'about': 'אודות', 'settings': 'הגדרות', 'done': 'סיום מסכת', 'mekorot': 'מקורות', 'privacy': 'פרטיות',
            'gemara': 'דף גמרא (סרגל הכלים והחלוניות)', 'daf-static': 'דף גמרא סטטי (לגוגל)', 'site': 'כל הדפים (כותרת עליונה ותחתית)'}
KIND_HE = {'text': 'טקסט', 'title': 'טקסט ריחוף', 'aria-label': 'תווית נגישות', 'placeholder': 'טקסט בשדה', 'alt': 'תיאור תמונה',
           'doctitle': 'כותרת הדף', 'metadesc': 'תיאור לגוגל'}


def main(files):
    reg = json.load(io.open(REG, encoding='utf-8')) if os.path.exists(REG) else {}
    pages = {}
    for f in files:
        d = json.load(io.open(f, encoding='utf-8'))
        for k, v in d.items():
            if k.startswith('ERR|'):
                raise SystemExit('עצירה: שגיאת קציר: %s %s' % (k, v))
            reg[k] = v['key']
            pages.setdefault(k, set()).add(v['page'])
    with io.open(REG, 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(dict(sorted(reg.items())), fh, ensure_ascii=False, indent=0)
    by = {}
    for k, key in reg.items():
        sc, kind, tok = k.split('|', 2)
        by.setdefault(sc, []).append((kind, key, tok))
    out = ['# מפתחות הטקסט של האתר (נוצר על ידי tools/lk_registry.py, 8.10.2026)', '',
           'כל טקסט קבוע של מעטפת האתר מזוהה במפתח יציב: **היקף.מילים-ראשונות.גיבוב**. ההיקף הוא סוג הדף (או "site" לכותרת ולתחתית המשותפות), '
           'והגיבוב נגזר מהנוסח המקורי (כשמספרים בו מוחלפים ב-`{n}`), ולא ממיקומו בדף. ',
           'עיפרון המנהל שומר שינוי תחת המפתח הזה בשרת. **הכלל:** כל שינוי עיצוב עתידי חייב לשמור על הנוסח המקורי של הטקסטים שנשארים, '
           'ולכן המפתח נשמר. רכיב שהוסר או שנוסחו המקורי שונה בקוד: השינוי שלו נשמר בארכיון ומופיע בעמוד "טקסטים ששיניתי" כ"יתום". '
           'טקסט חדש שנוסף למעטפת מקבל מפתח מיד, והמרשם מתעדכן בהרצת `lk_registry.py` אחרי קציר.', '',
           'לא נכלל: תוכן הגמרא, פירוש הגמרא, המשניות, כותרות הצד, שאלות "בחן את עצמך", שיעורים, הצעות וכינויים של משתמשים.', '']
    for sc in sorted(by, key=lambda s: (s not in SCOPE_HE, s)):
        out.append('## %s (%s) - %d' % (SCOPE_HE.get(sc, sc), sc, len(by[sc])))
        out.append('')
        for kind, key, tok in sorted(by[sc], key=lambda x: (x[0] != 'text', x[0], x[2])):
            out.append('- `%s` · %s · %s' % (key, KIND_HE.get(kind, kind), tok.replace('\n', ' ')[:110]))
        out.append('')
    with io.open(MD, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('\n'.join(out))
    print('מרשם: %d מפתחות, %d היקפים' % (len(reg), len(by)))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    main(sys.argv[1:])
