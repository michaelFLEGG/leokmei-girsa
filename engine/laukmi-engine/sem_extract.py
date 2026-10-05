# -*- coding: utf-8 -*-
"""שכבה סמנטית (ב4) - הפקה. מפיק שני קבצים מכונתיים:
 citations.json - כל הציטוטים בגרש בודד (id = פסקה:היסט), כפי שמפיק laukmi_batch.
 aramaic.json   - כל מופע של מילה שנראית ארמית ואינה במילון הוודאי (id = פסקה:היסט),
                  עם הקשר רחב. ההיסט הוא בטקסט החי של הפסקה (ללא מחוק).
סגנונות הגוף בבכורות כוללים 0.1, 0.2 ו-List Paragraph (גוף מוזח)."""
import sys, re, json, collections
import laukmi_rules
laukmi_rules.BODY |= {"0.1", "0.2", "List Paragraph"}
import laukmi_batch, laukmi_aramaic as A
from laukmi_mech import Doc, text_map

src, outc, outa = sys.argv[1], sys.argv[2], sys.argv[3]
laukmi_batch.extract(src, outc)
doc = Doc(src)
rx = [re.compile(s) for s in A.SIGNS]
known = set(A.LEXICON) | A.KEEP
BODYS = laukmi_rules.BODY | {"חלון 3"}
items = []
for k, p in enumerate(doc.paragraphs()):
    if doc.pstyle(p) not in BODYS: continue
    raw, _ = text_map(p)
    masked = re.sub(r"'[^']{0,200}'", lambda m: " " * len(m.group(0)), raw)   # ציטוטים אינם ארמית
    for m in re.finditer(r"[א-ת]{3,}", masked):
        w = m.group(0)
        if w in known: continue
        base = re.sub(r'^(ו|ד|ל|כ|מ|ש|ב|ה|וד|ול|וכ|דל)', '', w)
        if base in known: continue
        if any(r.search(w) for r in rx):
            items.append({"id": "%d:%d" % (k, m.start()), "מילה": w,
                          "לפני": raw[max(0, m.start() - 90):m.start()],
                          "אחרי": raw[m.end():m.end() + 60]})
json.dump(items, open(outa, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("%d מופעי ארמית מסופקת -> %s" % (len(items), outa))
