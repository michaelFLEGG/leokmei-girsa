# -*- coding: utf-8 -*-
"""סבב ד (ארכיון): הכללים שנלמדו מתיקוני המחבר. הטבלאות מיובאות מ-laukmi_rules.py."""
import re, time, collections
from laukmi_mech import *
from laukmi_rules import *
import laukmi_mech
laukmi_mech.AUTHOR = "Claude - כללים שנלמדו"

t0 = time.time()
doc = Doc("hulin_v3.docx")
log = collections.Counter()

l = {}; run_replacements_pfx(doc, WORDS, BODY, l); log["מילים"] = sum(l.values())
l = {}; run_raw(doc, RAWS, BODY | {ANCHOR}, l); log["רצפים"] = sum(l.values())
l = {}; run_rx(doc, RXS, BODY, l); log["דפוסים"] = sum(l.values())

# --- ב. ניקוי עוגנים: תבליט, ו-א"ל כשיש נמען מפורש ---
AL = re.compile(r'^\s*(?:•\s*)?(א"ל\s+)(?=\S+\s+ל\S)')
BUL = re.compile(r'^\s*(•\s*)')
for p in list(doc.paragraphs()):
    if doc.pstyle(p) != ANCHOR: continue
    txt, _ = text_map(p)
    m = AL.match(txt)
    if m:
        a = txt.index('א"ל')
        if tracked_replace(doc, p, a, a + len(m.group(1)), ""): log['מחיקת א"ל'] += 1
        txt, _ = text_map(p)
    m = BUL.match(txt)
    if m and tracked_replace(doc, p, m.start(1), m.end(1), ""): log["תבליט בעוגן"] += 1

# --- ג. עוגנים חדשים: מילות מסגרת בלי נקודתיים ---
FRAME = re.compile(r"^\s*(•\s*)?(והך ד|והך|הך|ויקשה|ויקשיא|וקשה|וקשיא|ולא אמרי'|ולא אמרינן|"
                   r"וצריכי|אלא אמר|אלא|וחלקו|ושאני|והיינו ד|והיינו|ושמא|ומשמע ש|ומשמע|וסיפא|ורישא|"
                   r"מכלל|וא\"א|ואין להקשות|ואין לחשוש|ואין להוכיח|ואין לומר|אין לומר|ולית|טעמא ד)(?=\s)")
DASH = re.compile(r"^\s*(–\s*)")
paras = list(doc.paragraphs()); styles = [doc.pstyle(p) for p in paras]
for k, p in enumerate(paras):
    if styles[k] not in BODY: continue
    txt, _ = text_map(p)
    m = DASH.match(txt)
    if m:
        tracked_replace(doc, p, m.start(1), m.end(1), ""); log["מקף פותח"] += 1
        txt, _ = text_map(p)
    if k and styles[k-1] == ANCHOR: continue
    m = FRAME.match(txt)
    if not m: continue
    rest = txt[m.end(2):]
    if len(rest.strip()) < 15: continue
    if m.group(1):
        b = txt.index("•")
        tracked_replace(doc, p, b, b + len(m.group(1)), "")
        txt, _ = text_map(p); m = FRAME.match(txt)
        if not m: continue
    if make_anchor(doc, p, m.end(2), ANCHOR) is not None: log["עוגני מסגרת"] += 1

# --- ד. סגנון אמוראים על מה שנוסף ---
src = open("run_full.py").read(); exec(src[:src.index("# ---------------- שלב א")])
am = {}
style_names(doc, SHEMOT, BODY, "אמוראים תו 2", am)
style_regex(doc, [r'(?<![א-ת"\'])(?:ו|ד|ל|כ|מ|ש|וד|ול|וכ|כד|דל|אד)?(ר[יאשחנבהמצעכגפדזס]{0,3}"[א-ת]{1,2})(?![א-ת"\'])'],
            BODY, "אמוראים תו 2", am)
log["אמוראים"] = am.get("מופעים", 0)

doc.save("hulin_v4.docx")
for k, v in log.items(): print(f"{k}: {v}")
print(f"סה\"כ {sum(log.values())} שינויים · {time.time()-t0:.1f} שניות")
