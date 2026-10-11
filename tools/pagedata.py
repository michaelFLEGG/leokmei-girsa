# -*- coding: utf-8 -*-
"""pagedata.py - קריאת דף מסכת בנוי יחד עם קובץ הנתונים שלו.
מ-11.10.2026 `const DATA=` אינו מוטבע בדף אלא בקובץ <מסכת>.data.js שבצדו (נשמר במטמון, והדף קל).
הכלים שקוראים את הנתונים מן הדף הבנוי עוברים כאן: הפונקציה מחזירה את ה-HTML ואחריו את קובץ הנתונים,
כך שחיפוש `const DATA=` עובד כמו קודם (וגם בדף ישן שהנתונים מוטבעים בו)."""
import io, os, re


def read_html(path):
    h = io.open(path, encoding='utf-8').read()
    if 'const DATA=' in h:
        return h
    m = re.search(r'<script src="([^"?]+\.data\.js)(?:\?[^"]*)?"', h)
    if m:
        fp = os.path.join(os.path.dirname(os.path.abspath(path)), m.group(1))
        h += '\n' + io.open(fp, encoding='utf-8').read()
    return h
