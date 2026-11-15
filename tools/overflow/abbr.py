# -*- coding: utf-8 -*-
"""כלי 2 של "שורה שהתארכה" (פרומפט 41): רשימת הקיצורים המכניים, נבנית מכתיבתו של בעל הפרויקט.

מותרת רק צורה מקוצרת שמופיעה בכל קובצי הוורד לפחות 5 פעמים (וגם הצורה המלאה מופיעה). הרשימה המועמדת
כאן קבועה וזהירה: אין שמות (כלל # בחוקה: שם שנכתב במלואו נשאר), ואין קיצור דו-משמעי (ב"ה, ע"כ).
ראשי תיבות שבעל הפרויקט אישר בממשק נוספים מקובץ ההכרעות (data/overflow/approved-abbr.json).

הרצה (מקומית, כשקובצי הוורד במאגר):
  uv run python tools/overflow/abbr.py
הפלט: data/overflow/abbr.json
"""
import glob, io, json, os, re, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, 'data', 'overflow', 'abbr.json')
APPROVED = os.path.join(ROOT, 'data', 'overflow', 'approved-abbr.json')
MIN = 5

# (מלא, מקוצר). סדר: הארוך קודם, כדי ש"ואחר כך" לא ייתפס כ"אחר כך"
PAIRS = [
    ('הקדוש ברוך הוא', 'הקב"ה'), ('להקדוש ברוך הוא', 'להקב"ה'),
    ('ואף על פי', 'ואע"פ'), ('אף על פי', 'אע"פ'), ('אף על גב', 'אע"ג'),
    ('ואחר כך', 'ואח"כ'), ('אחר כך', 'אח"כ'),
    ('אמר לו', 'א"ל'), ('שמע מינה', 'ש"מ'), ('דברי תורה', 'ד"ת'),
    ('בבית הכנסת', 'בביהכנ"ס'), ('לבית הכנסת', 'לביהכנ"ס'), ('בית הכנסת', 'ביהכנ"ס'),
    ('לעולם הבא', 'לעוה"ב'), ('העולם הבא', 'העוה"ב'), ('עולם הבא', 'עוה"ב'),
    ('על ידי', 'ע"י'), ('כל שכן', 'כ"ש'), ('אם כן', 'א"כ'), ('צאת הכוכבים', 'צה"כ'),
    ('תלמידי חכמים', 'ת"ח'), ('תלמיד חכם', 'ת"ח'), ('בית המקדש', 'ביהמ"ק'), ('בית המדרש', 'ביהמ"ד'),
    ('בית דין', 'ב"ד'), ('ראש השנה', 'ר"ה'), ('יום טוב', 'יו"ט'), ('ארץ ישראל', 'א"י'),
    ('שליח ציבור', 'ש"ץ'), ('קריאת שמע', 'ק"ש'), ('תלמוד לומר', 'ת"ל'), ('מכל מקום', 'מ"מ'),
    ('יצר הרע', 'יצה"ר'), ('עבודה זרה', 'ע"ז'), ('הלכה למשה מסיני', 'הלמ"מ'), ('ספר תורה', 'ס"ת'),
    ('בני אדם', 'בנ"א'), ('קל וחומר', 'ק"ו'), ('גזירה שוה', 'ג"ש'), ('בעל הבית', 'בעה"ב'),
    ('יום הכפורים', 'יוה"כ'), ('ערב שבת', 'ע"ש'), ('מוצאי שבת', 'מוצ"ש'), ('שם שמים', 'ש"ש'),
    ('לשון הרע', 'לה"ר'), ('דבר אחר', 'ד"א'), ('מצות עשה', 'מ"ע'), ('לא תעשה', 'ל"ת'),
    ('תלמוד תורה', 'ת"ת'), ('אין צריך לומר', 'א"צ לומר'),
]
# מספר במילים לאות עם גרש, רק לפני מילה (שלש פעמים -> ג' פעמים). בלי "שני" (שני = השני), "שש", "שבע", "עשר"
NUMS = [('שתי', "ב'"), ('שלש', "ג'"), ('שלשה', "ג'"), ('שלושה', "ג'"), ('ארבע', "ד'"), ('ארבעה', "ד'"),
        ('חמש', "ה'"), ('חמשה', "ה'"), ('ששה', "ו'"), ('שבעה', "ז'"), ('שמונה', "ח'"), ('תשעה', "ט'"), ('עשרה', "י'")]


def corpus():
    out = []
    for f in sorted(glob.glob(os.path.join(ROOT, 'input', 'docx', '*.docx'))):
        try:
            x = zipfile.ZipFile(f).read('word/document.xml').decode('utf-8')
        except Exception:
            continue
        for p in re.findall(r'<w:p[ >].*?</w:p>', x, flags=re.S):
            t = ''.join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>', p))
            if t.strip():
                out.append(t.replace('&quot;', '"').replace('&apos;', "'").replace('&amp;', '&'))
    return '\n'.join(out)


def count(T, s):
    return len(re.findall(r'(?<![א-ת"\'])' + re.escape(s) + r'(?![א-ת"])', T))


def main():
    T = corpus()
    items = []
    for a, b in PAIRS:
        ca, cb = count(T, a), count(T, b)
        if cb >= MIN and ca >= 1:
            items.append({'long': a, 'short': b, 'nLong': ca, 'nShort': cb, 'kind': 'abbr'})
    for a, b in NUMS:
        cb = len(re.findall(r'(?<![א-ת])' + re.escape(b) + r' [א-ת]', T))
        ca = count(T, a)
        if cb >= MIN and ca >= 1:
            items.append({'long': a, 'short': b, 'nLong': ca, 'nShort': cb, 'kind': 'num'})
    if os.path.exists(APPROVED):
        have = {(x['long'], x['short']) for x in items}
        for x in json.load(io.open(APPROVED, encoding='utf-8')).get('items', []):
            if (x['long'], x['short']) not in have:
                items.append({'long': x['long'], 'short': x['short'], 'kind': 'approved', 'nShort': x.get('n', 0)})
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    doc = {'_הערה': 'כלי 2 של שורה שהתארכה: רק צורה שמופיעה בקובצי הוורד לפחות %d פעמים. נבנה ב-tools/overflow/abbr.py' % MIN,
           'min': MIN, 'items': items}
    io.open(OUT, 'w', encoding='utf-8').write(json.dumps(doc, ensure_ascii=False, indent=1))
    print('קיצורים:', len(items))


if __name__ == '__main__':
    main()
