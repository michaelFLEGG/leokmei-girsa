# -*- coding: utf-8 -*-
"""
לאוקמי גירסא - סבב ח'.
עיקרו: שכבת הארמית הוודאית, רוחבית ובלי טוקנים. המסופק יוצא לקובץ המתנה.
    python3 run_round8.py <קלט.docx> <פלט.docx>
"""
import sys, re, time, collections
import laukmi_mech
from laukmi_mech import (Doc, run_replacements_pfx, run_raw, run_rx, style_names,
                         style_regex, unstyle_words, text_map, tracked_replace)
from laukmi_rules import *
from laukmi_aramaic import LEXICON, PHRASES, MIGZAR
import laukmi_anchors, laukmi_aramaic

laukmi_mech.AUTHOR = "Claude - סבב ח"

src = sys.argv[1] if len(sys.argv) > 1 else "hulin_g_acc.docx"
dst = sys.argv[2] if len(sys.argv) > 2 else "hulin_v9.docx"

t0 = time.time()
doc = Doc(src)
log = collections.Counter()
ALL = BODY | {ANCHOR}

# --- א. רווחים שנבלעו ---
l = {}; run_raw(doc, SPACES, ALL, l);  log["רווח שנבלע"] = sum(l.values())
l = {}; run_rx(doc, SPACE_RX, ALL, l); log["רווח אחרי פיסוק"] = sum(l.values())

# --- ב. הארמית הוודאית: צירופים קודם, אחר כך מילים, אחר כך מורפולוגיה ---
l = {}; run_raw(doc, PHRASES, ALL, l);            log["צירופים ארמיים"] = sum(l.values())
l = {}; run_replacements_pfx(doc, LEXICON, ALL, l); log["מילים ארמיות"] = sum(l.values())
mig = [(r'(?<![א-ת"\'])(ו|ד|ל|ש|כ|ב)?למי' + re.escape(k) + r'(?![א-ת"\'])', r'\1' + v)
       for k, v in MIGZAR.items()]
l = {}; run_rx(doc, mig, ALL, l);                  log["מקור למי-"] = sum(l.values())

# --- ג. תיקוני סבב ז' הנוספים ---
l = {}; run_replacements_pfx(doc, {"חכים": "חכם"}, BODY, l); log["מילים"] = sum(l.values())

# --- ד. "אמר" בסוף העוגן ---
n = 0
for p in list(doc.paragraphs()):
    if doc.pstyle(p) != ANCHOR: continue
    txt, _ = text_map(p)
    m = AMAR_TAIL.search(txt)
    if m and len(txt[:m.start(1)].strip()) >= 2:
        if tracked_replace(doc, p, m.start(1), m.end(1), ""): n += 1
log['מחיקת "אמר" בסוף עוגן'] = n

# --- ה. עוגנים ---
laukmi_anchors.YICH_RX = re.compile(
    r"^\s*(?:" + "|".join(re.escape(x) for x in sorted(
        set(YICHUS + YICHUS6 + YICHUS7 + YICHUS8), key=len, reverse=True)) + r")(?![א-ת])")
a = {}; laukmi_anchors.build(doc, a)
for k, v in a.items(): log["עוגן: " + k] = v
c = {}; laukmi_anchors.clean_anchors(doc, c)
for k, v in c.items(): log[k] = v

# --- ו. שמות ---
un = {}
for st in (AM_STYLE, "אמוראים תו"): unstyle_words(doc, NOT_NAME, ALL, st, un)
log["סגנון שהוסר"] = un.get("הוסר", 0)
am = {}
style_names(doc, SHEMOT, BODY, AM_STYLE, am)
style_regex(doc, NAME_RT, BODY, AM_STYLE, am)
log["שמות"] = am.get("מופעים", 0)
un2 = {}
for st in (AM_STYLE, "אמוראים תו"): unstyle_words(doc, NOT_NAME, ALL, st, un2)
log["ניקוי חוזר"] = un2.get("הוסר", 0)

doc.save(dst)
for k, v in log.items():
    if v: print(f"{k}: {v}")
print(f'סה"כ {sum(log.values())} שינויים · {time.time()-t0:.1f} שניות · נשמר ל-{dst}')

# --- ז. המסופק: לא נוגעים, רק מדווחים ---
laukmi_aramaic.todo(dst, "aramaic_todo.md")
