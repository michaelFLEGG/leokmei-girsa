# -*- coding: utf-8 -*-
"""
לאוקמי גירסא - סבב ז'.
עיקרו: מנגנון חדש לזיהוי שמות אמוראים, ובנוסף תיקוני המחבר מסבב ו'.
    python3 run_round7.py <קלט.docx> <פלט.docx>
"""
import sys, re, time, collections
import laukmi_mech
from laukmi_mech import (Doc, run_replacements_pfx, run_raw, run_rx, style_names,
                         style_regex, unstyle_words, text_map, tracked_replace, make_anchor)
from laukmi_rules import *
import laukmi_anchors

laukmi_mech.AUTHOR = "Claude - סבב ז"

src = sys.argv[1] if len(sys.argv) > 1 else "hulin_f_acc.docx"
dst = sys.argv[2] if len(sys.argv) > 2 else "hulin_v7.docx"

t0 = time.time()
doc = Doc(src)
log = collections.Counter()

# --- א. עברות מתיקוני סבב ו' ---
l = {}; run_raw(doc, RAWS7, BODY | {ANCHOR}, l);      log["צירופים"] = sum(l.values())
l = {}; run_replacements_pfx(doc, WORDS7, BODY, l);   log["מילים"] = sum(l.values())

# --- ב. עוגנים: הרשימה המורחבת ---
laukmi_anchors.YICH_RX = re.compile(
    r"^\s*(?:" + "|".join(re.escape(x) for x in sorted(set(YICHUS + YICHUS6 + YICHUS7),
                                                       key=len, reverse=True)) + r")(?![א-ת])")
a = {}; laukmi_anchors.build(doc, a)
for k, v in a.items(): log["עוגן: " + k] = v
c = {}; laukmi_anchors.clean_anchors(doc, c)
for k, v in c.items(): log[k] = v

# --- ג. שמות אמוראים: ניקוי מה שאינו שם, ואז זיהוי מורחב ---
un = {}
for st in (AM_STYLE, "אמוראים תו"):
    unstyle_words(doc, NOT_NAME, BODY | {ANCHOR}, st, un)
log["סגנון שהוסר ממונחים"] = un.get("הוסר", 0)

am = {}
style_names(doc, SHEMOT, BODY, AM_STYLE, am)
style_regex(doc, NAME_RT, BODY, AM_STYLE, am)
log["שמות שסוגננו"] = am.get("מופעים", 0)

# הרשימה השחורה שוב, כי התבנית המורחבת עלולה לתפוס מונח שיש בו ר
un2 = {}
for st in (AM_STYLE, "אמוראים תו"):
    unstyle_words(doc, NOT_NAME, BODY | {ANCHOR}, st, un2)
log["ניקוי חוזר"] = un2.get("הוסר", 0)

doc.save(dst)
for k, v in log.items():
    if v: print(f"{k}: {v}")
print(f'סה"כ {sum(log.values())} שינויים · {time.time()-t0:.1f} שניות · נשמר ל-{dst}')
