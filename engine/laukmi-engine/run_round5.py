# -*- coding: utf-8 -*-
"""
לאוקמי גירסא - סבב ה'.
הרעיונות שנלמדו מתיקוני המחבר בסבב ד', מוחלים רוחבית על כל המסכת.
    python3 run_round5.py <קלט.docx> <פלט.docx>
"""
import sys, time, collections
import laukmi_mech
from laukmi_mech import (Doc, run_replacements_pfx, run_raw, run_rx,
                         style_names, style_regex, text_map, tracked_replace)
from laukmi_rules import *
import laukmi_anchors

laukmi_mech.AUTHOR = "Claude - סבב ה"

src = sys.argv[1] if len(sys.argv) > 1 else "hulin_d.docx"
dst = sys.argv[2] if len(sys.argv) > 2 else "hulin_v5.docx"

t0 = time.time()
doc = Doc(src)
log = collections.Counter()

# --- א. הסולמית היא גרש שנפל ---
l = {}; run_raw(doc, HASH_DUP, BODY | {ANCHOR} | HEADS, l); log["# כפול נמחק"] = sum(l.values())
l = {}; run_raw(doc, HASH_ONE, BODY | {ANCHOR} | HEADS, l); log["# -> גרש"] = sum(l.values())

# --- ב. גרש שנשתבש בתוך ראשי תיבות ---
l = {}; run_raw(doc, GERESH, BODY | {ANCHOR}, l); log["גרש -> גרשיים"] = sum(l.values())
l = {}; run_rx(doc, GERESH_RX, BODY | {ANCHOR}, l); log["גרשיים כפולים"] = sum(l.values())

# --- ג. מילים וראשי תיבות ארמיים ---
l = {}; run_replacements_pfx(doc, WORDS5, BODY, l); log["מילים"] = sum(l.values())
l = {}; run_rx(doc, KI_RX, BODY, l); log["כי + פועל -> כש"] = sum(l.values())

# --- ד. פיסוק, שוב, אחרי תיקוני הגרש ---
l = {}; run_raw(doc, RAWS, BODY | {ANCHOR}, l); log["פיסוק"] = sum(l.values())

# --- ה. עוגנים ---
a = {}; laukmi_anchors.build(doc, a)
for k, v in a.items(): log["עוגן: " + k] = v
c = {}; laukmi_anchors.clean_anchors(doc, c)
for k, v in c.items(): log[k] = v

# --- ו. סגנון אמוראים על כל מה שנוצר ---
am = {}
style_names(doc, SHEMOT, BODY, AM_STYLE, am)
style_regex(doc, [r'(?<![א-ת"\'])(?:ו|ד|ל|כ|מ|ש|וד|ול|וכ|כד|דל|אד)?(ר[יאשחנבהמצעכגפדזס]{0,3}"[א-ת]{1,2})(?![א-ת"\'])'],
            BODY, AM_STYLE, am)
log["אמוראים"] = am.get("מופעים", 0)

doc.save(dst)
for k, v in log.items():
    if v: print(f"{k}: {v}")
print(f'סה"כ {sum(log.values())} שינויים · {time.time()-t0:.1f} שניות · נשמר ל-{dst}')
