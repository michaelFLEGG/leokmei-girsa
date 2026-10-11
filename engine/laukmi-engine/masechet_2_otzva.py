# -*- coding: utf-8 -*-
"""
מנוע ב - האצווה.

אחרי המנוע המכני נשאר מה שדורש הכרעה ולא חוק. המנוע הזה אינו מכריע דבר:
הוא מוציא את כל המועמדים עם ההקשר שלהם, ואתה או קלוד מכריעים עליהם
בבת אחת, בקריאה אחת, ואז הסקריפט שותל בחזרה.

    python3 masechet_2_otzva.py <קובץ.docx>            # הפקה
    python3 masechet_2_otzva.py <קובץ.docx> <הכרעות.json> <פלט.docx>   # שתילה

ההפקה יוצרת שני קבצים:
    citations.json     - כל הציטוטים, עם סימון מי מנוקד ומי נושא סגנון פסוק
    aramaic_todo.md    - כל המילה שנראית ארמית ואינה במילון הוודאי

קובץ ההכרעות שמוזן בחזרה נראה כך:
    {"1234:56": {"סוג": "פסוק", "ניקוד": "אַחֲרֵי רַבִּים לְהַטֹּת"}}
הסוג הוא "פסוק" / "משנה" / "לא"; הניקוד אפשר שיהיה null.
"""
import sys
import laukmi_batch, laukmi_aramaic, laukmi_learn

if len(sys.argv) < 2:
    print(__doc__); sys.exit(1)

if len(sys.argv) >= 4:
    laukmi_batch.apply(sys.argv[1], sys.argv[2], sys.argv[3])
    print(f"נשתל ל-{sys.argv[3]}")
else:
    src = sys.argv[1]
    acc = src.replace(".docx", "__accepted.docx")
    laukmi_learn.accept_all(src, acc)
    laukmi_batch.extract(src, "citations.json")
    laukmi_aramaic.todo(acc, "aramaic_todo.md")
    print()
    print("הכרע על מה שבקבצים, ואז:")
    print(f"  python3 masechet_2_otzva.py {src} <הכרעות.json> <פלט.docx>")
