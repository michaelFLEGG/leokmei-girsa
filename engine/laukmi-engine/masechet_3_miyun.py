# -*- coding: utf-8 -*-
"""
מנוע ג - מיון התיקונים.

מריצים אותו על קובץ שהגהת, והוא מחליט לבד לאיזו שכבה שייך כל תיקון שלך:

    python3 masechet_3_miyun.py <קובץ-מוגה.docx> [דוח.md]

  מכני   - חוק קבוע. יוצא כשורת טבלה מוכנה להדבקה ב-laukmi_rules.py.
  סמנטי  - תלוי הקשר או דורש ידע. יוצא כאצווה למנוע ב.
  פייבל  - שיקול דעת מלא. אין מה להכליל; לעבודה ידנית או בשיחה.

הוא מזהה גם דחיות: תיקון שלי שהחזרת למקורו. דחייה שווה בערכה לתיקון,
כי היא מלמדת שכלל שנראה בטוח אינו בטוח.
"""
import sys, difflib, collections
import laukmi_triage

if len(sys.argv) < 2:
    print(__doc__); sys.exit(1)
laukmi_triage.report(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "triage.md")


def rejections(sent, returned):
    """הבדלים בין מה שנשלח למה שחזר - כלומר מה שנדחה."""
    from laukmi_scan import load, live_text, q
    def txt(f):
        z, doc, i = load(f)
        return " ".join(live_text(p) for p in doc.iter(q("p"))).split()
    A, B = txt(sent), txt(returned)
    out = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, A, B, autojunk=False).get_opcodes():
        if tag != "equal":
            out.append((" ".join(A[i1:i2]), " ".join(B[j1:j2])))
    return out
