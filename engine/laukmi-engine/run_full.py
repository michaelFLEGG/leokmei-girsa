# -*- coding: utf-8 -*-
"""סבב א-ג: ההחלפות המכניות, העוגנים וסגנון האמוראים.
   הטבלאות מיובאות מ-laukmi_rules.py - אין כאן עותק שני."""
import re, time, collections
from laukmi_mech import *
from laukmi_rules import *

# ---------------- שלב א: החלפות מכניות ----------------
t0 = time.time()
doc = Doc("hulin.docx")
logs = {}
for nm, tab, fn in [("קיצורים", KITZUR, run_replacements_pfx), ("עברות", IVRUT, run_replacements_pfx),
                    ("ארמית ב", ARAM2, run_replacements_pfx), ("צירופים", NOPFX, run_replacements), ("פיסוק", PUNCT, run_raw), ("צירופי רצף", RAW2, run_raw)]:
    l = {}; fn(doc, tab, BODY, l); logs[nm] = l
l={}; run_rx(doc, RX, BODY, l); logs["דפוסים"]=l
t1 = time.time()

# ---------------- שלב ב: עוגני חלון 3 ----------------
NAME_RX = re.compile("|".join(re.escape(x) for x in sorted(SHEMOT, key=len, reverse=True)))
YICH_RX = re.compile(r"^\s*(?:" + "|".join(re.escape(x) for x in sorted(YICHUS, key=len, reverse=True)) + r")\b")
OPEN = re.compile(r"^\s*(•\s*)?([^:]{2,20}):(\s|$)")
BAD = re.compile(r"[.!?׻׹]|'[^']*$")

def eligible(head, rest):
    if len(rest.strip()) < 15: return False
    if BAD.search(head): return False
    if head.count("'") % 2: return False
    return bool(NAME_RX.search(head) or YICH_RX.match(head))

made, skipped = 0, collections.Counter()
paras = list(doc.paragraphs())
styles = [doc.pstyle(p) for p in paras]
for k, p in enumerate(paras):
    if styles[k] not in BODY: continue
    if k and styles[k-1] == ANCHOR: skipped["קודמת עוגן"] += 1; continue
    txt, _ = text_map(p)
    m = OPEN.match(txt)
    if not m: continue
    head, rest = m.group(2).strip(), txt[m.end(2)+1:]
    if not eligible(head, rest): skipped["לא ברשימה"] += 1; continue
    if m.group(1):                      # התבליט שימש כסמן - עכשיו נמחק
        b = txt.index("•")
        tracked_replace(doc, p, b, b + len(m.group(1)), "")
        txt, _ = text_map(p)
    cut = txt.index(":") + 1
    if make_anchor(doc, p, cut, ANCHOR) is not None: made += 1
t2 = time.time()

# ---------------- שלב ג: סגנון אמוראים ----------------
am = {}
style_names(doc, SHEMOT, BODY, AM_STYLE, am)
NAME_PAT = [r'(?<![א-ת"\'])(?:ו|ד|ל|כ|מ|ש|וד|ול|וכ|כד|דל|אד)?(ר[יאשחנבהמצעכגפדזס]{0,3}"[א-ת]{1,2})(?![א-ת"\'])']
style_regex(doc, NAME_PAT, BODY, AM_STYLE, am)
t3 = time.time()

doc.save("hulin_full.docx")
for k, v in logs.items(): print(f"{k}: {sum(v.values())}")
print(f"עוגני חלון 3 שנוצרו: {made} | נדחו: {dict(skipped)}")
print(f"שמות שקיבלו סגנון אמוראים: {am.get('מופעים',0)}")
print(f"זמנים: החלפות {t1-t0:.1f}ש · עוגנים {t2-t1:.1f}ש · אמוראים {t3-t2:.1f}ש · סה\"כ {time.time()-t0:.1f} שניות")
