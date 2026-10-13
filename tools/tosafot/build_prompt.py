# -*- coding: utf-8 -*-
"""build_prompt.py - מרכיב את הפרומפט הקבוע של הייצור: tosafot/תוס-פרומפט-ייצור.md

החלק הקבוע בלבד (כלומר מה שנכנס למטמון): חוקת התוספות (סעיפים ב ו-ג), כללי הזהב הוודאיים, דוגמאות הזהב לשורה, ודוגמאות הזהב
לשאלות (רשימת השאלות שהמנהל סיפק לברכות). החלק המשתנה (התוספות והקשרם) נבנה בקוד בכל בקשה.
כללים ב"פתוח" אינם נכנסים.

    uv run python tools/tosafot/build_prompt.py
"""
import os, sys, io, re, json
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
T = os.path.join(ROOT, 'tosafot')

QSTEMS = ['מדוע אין מברכים על בשמים של מתים', 'מדוע בית שמאי מקדימים ברכת היום', 'כיצד דחתה הגמרא את ההוכחה מהמשנה שמצוות צריכות כוונה',
          'מדוע השוכח ראש חודש בברכת המזון', 'כיצד מתיישב דין נחש שעל העקב', 'כיצד יישבו את "מעוות לא יוכל לתקון"',
          'מה מוסיף "כל שיש בו מחמשת המינים"', 'מדוע עדיף לבית הלל החשש לטומאת ידיים', 'מדוע רבי יוחנן יכול להסכים לרבי יוסי',
          'כיצד נחלקו אביי ורבא בהכרעת מעמד תפילת ערבית']


def section(md, title):
    m = re.search(r'^## ' + re.escape(title) + r'.*?\n(.*?)(?=^## |\Z)', md, re.S | re.M)
    if not m:
        raise SystemExit('עצירה: אין סעיף "%s"' % title)
    return m.group(1).strip()


def gold_questions():
    t = io.open(os.path.join(ROOT, 'data', 'quiz', 'berakhot.reviewed.txt'), encoding='utf-8').read()
    blocks = [b for b in t.split('\n\n') if b.startswith('@')]
    out = []
    for stem in QSTEMS:
        for b in blocks:
            q = re.search(r'^ש: (.+)$', b, re.M)
            if q and stem in q.group(1):
                a = re.search(r'^\+ (.+)$', b, re.M).group(1)
                x = re.search(r'^ה: (.+)$', b, re.M)
                out.append({'q': q.group(1).strip(), 'a': a.strip() + ('. ' + x.group(1).strip() if x else '')})
                break
    return out


def main():
    ch = io.open(os.path.join(T, 'תוס-חוקה.md'), encoding='utf-8').read()
    gold = io.open(os.path.join(T, 'תוס-כללי-זהב.md'), encoding='utf-8').read()
    ex = json.load(io.open(os.path.join(T, 'factory', 'gold-examples.json'), encoding='utf-8'))
    ex['questions'] = gold_questions()
    with io.open(os.path.join(T, 'factory', 'gold-examples.json'), 'w', encoding='utf-8') as f:
        json.dump(ex, f, ensure_ascii=False, indent=1)
    rules = section(gold, 'כללים ודאיים') + '\n\n' + section(gold, 'הכרעות בסתירות (לפי ניתוח הסבבים)')
    L = ['# הנחיה קבועה: בית החרושת לתוספות (נבנה בקוד מ-תוס-חוקה.md, תוס-כללי-זהב.md ו-gold-examples.json; אין לערוך ידנית)', '',
         'אתה כותב הערות שוליים לספר לימוד של הש"ס (לאוקמי גירסא, קיצור הגמרא). לכל דיבור המתחיל של תוספות שיוגש לך תכתוב שורת מסקנה, '
         'ובמקום שיש בו קושיא, חידוש או סברא של ממש גם שאלת תוכן אחת או שתיים. הדיבור המתחיל עצמו מוצג ללומד בנפרד, בבולט, לפני השורה שלך, '
         'ולכן אינו נכתב על ידך לעולם.', '',
         '## שורת מסקנה', '', section(ch, 'ב. שורת מסקנה').split('\n', 1)[1].strip() if section(ch, 'ב. שורת מסקנה').startswith('(') else section(ch, 'ב. שורת מסקנה'), '',
         '## כללי זהב (נלמדו מהכרעות המנהל, מחייבים)', '', rules, '',
         '## שאלות תוכן', '', section(ch, 'ג. שאלות תוכן').split('\n', 1)[1].strip() if section(ch, 'ג. שאלות תוכן').startswith('(') else section(ch, 'ג. שאלות תוכן'), '',
         'סוגי השאלות בשדה "t": קושיא, הכרח, נפק"מ, סברא, ממקום אחר, צ"ע. הרמה בשדה "lvl": קל, בינוני או קשה. ',
         'ללא שאלה: "q": null.', '',
         '### דוגמאות סגנון לשאלות (מרשימת השאלות שהמנהל סיפק לברכות; הסגנון בלבד, השאלות שלך נוגעות בקושי של התוספות עצמו)', '']
    for q in ex['questions']:
        L.append('שאלה: %s\nתשובה: %s\n' % (q['q'], q['a']))
    L += ['### תבניות לשאלה על קושי', '',
          'קושיא בלי תירוץ: "והא קיי"ל ש..., ואמאי הכא...?" (הקושיא במלואה, בלשון התוספות והגמרא, בלי התירוץ).', 'הכרח: "מה הכריח את התוספות לפרש כך ולא כפשוטו?".', '',
          '## פורמט הפלט', '',
          'JSON אחד בלבד, בלי גדרות קוד ובלי שום טקסט לפניו או אחריו. כל מזהה שהוגש חייב להופיע.', '',
          '## דוגמאות זהב לשורת מסקנה (פנים התוספות המלא, והשורה שבחר או כתב בעל הפרויקט)', '']
    for e in ex['tosafot']:
        L += ['פנים התוספות: "%s"' % e['text'], 'שורה: "%s"' % e['line'], '']
    # הקבצים עצמם: בלי מזהי מפתחות וללא כל סוד
    out = '\n'.join(L).rstrip() + '\n'
    assert '—' not in out and '–' not in out, 'קו ארוך בפרומפט'
    with io.open(os.path.join(T, 'תוס-פרומפט-ייצור.md'), 'w', encoding='utf-8') as f:
        f.write(out)
    print('נכתב tosafot/תוס-פרומפט-ייצור.md: %d תווים (כ-%d טוקנים), %d דוגמאות שורה, %d דוגמאות שאלה'
          % (len(out), len(out) // 2, len(ex['tosafot']), len(ex['questions'])))


if __name__ == '__main__':
    main()
