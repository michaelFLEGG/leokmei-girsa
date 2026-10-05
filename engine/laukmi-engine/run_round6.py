# -*- coding: utf-8 -*-
"""
לאוקמי גירסא - סבב ו'.
הרעיונות שנלמדו מתיקוני המחבר בסבב ה', מוחלים רוחבית, ועוד כמה שלא סומנו.
    python3 run_round6.py <קלט.docx> <פלט.docx>
"""
import sys, re, time, collections
import laukmi_mech
from laukmi_mech import (Doc, run_replacements_pfx, run_raw, run_rx,
                         style_names, style_regex, text_map, tracked_replace, make_anchor)
from laukmi_rules import *
import laukmi_anchors

laukmi_mech.AUTHOR = "Claude - סבב ו"

src = sys.argv[1] if len(sys.argv) > 1 else "hulin_e_acc.docx"
dst = sys.argv[2] if len(sys.argv) > 2 else "hulin_v6.docx"

t0 = time.time()
doc = Doc(src)
log = collections.Counter()
ALL = BODY | {ANCHOR}

# --- א. הגוי הוא נכרי, העבודה היא ע"ז ---
l = {}; run_raw(doc, AKUM_EZ, ALL | HEADS, l);     log['עכו"ם -> ע"ז'] = sum(l.values())
l = {}; run_replacements_pfx(doc, AKUM_NOCHRI, ALL | HEADS, l); log['עכו"ם -> נכרי'] = sum(l.values())

# --- ב. צירופים ומילים שהמחבר תיקן ---
l = {}; run_raw(doc, RAWS6, ALL, l);               log["צירופים"] = sum(l.values())
l = {}; run_replacements_pfx(doc, WORDS6, BODY, l); log["מילים"] = sum(l.values())

# --- ג. ניקוי תווים ---
l = {}; run_rx(doc, DOUBLE_GERESH, ALL | HEADS, l); log["גרש כפול -> גרשיים"] = sum(l.values())
l = {}; run_rx(doc, QUOTE_SPACE, ALL, l);           log["רווח אחרי גרש פותח"] = sum(l.values())
n = 0
for p in list(doc.paragraphs()):
    if doc.pstyle(p) not in BODY: continue
    txt, _ = text_map(p)
    m = LEAD_SPACE.match(txt)
    if m and txt.strip() and tracked_replace(doc, p, 0, m.end(), ""): n += 1
log["רווח מוביל"] = n

# --- ד. "אמר" פותח בעוגן, ו-א"ל בשורת גוף ---
n = 0
for p in list(doc.paragraphs()):
    if doc.pstyle(p) != ANCHOR: continue
    txt, _ = text_map(p)
    m = AMAR_HEAD.match(txt)
    if m and tracked_replace(doc, p, m.start(1), m.end(1), ""): n += 1
log['מחיקת "אמר" בעוגן'] = n

AL_BODY = re.compile(r'^\s*(?:•\s*)?(א"ל\s+)(?=\S+\s+ל\S)')
n = 0
for p in list(doc.paragraphs()):
    if doc.pstyle(p) not in BODY: continue
    txt, _ = text_map(p)
    m = AL_BODY.match(txt)
    if m:
        a = txt.index('א"ל')
        if tracked_replace(doc, p, a, a + len(m.group(1)), ""): n += 1
log['מחיקת א"ל בגוף'] = n

# --- ה. עוגנים חדשים: הרשימה המורחבת, ופתיח שנחתם בפסיק או במקף ---
laukmi_anchors.YICHUS_SET = set(YICHUS6)
YICH6_RX = re.compile(r"^(?:" + "|".join(re.escape(x) for x in sorted(YICHUS6, key=len, reverse=True)) + r")(?![א-ת])")
NAME_RX  = laukmi_anchors.NAME_RX

a = {}; laukmi_anchors.build(doc, a)
for k, v in a.items(): log["עוגן: " + k] = v

paras  = list(doc.paragraphs())
styles = [doc.pstyle(p) for p in paras]
for k, p in enumerate(paras):
    if styles[k] not in BODY: continue
    if k and styles[k - 1] == ANCHOR: continue
    txt, _ = text_map(p)
    cut, kind = None, None
    m = COMMA_HEAD.match(txt)
    if m:
        head = m.group(1).strip()
        if YICH6_RX.match(head) and len(txt[m.end(1) + 1:].strip()) >= 15:
            cut, kind = m.end(1) + 1, "פסיק"
    if cut is None:
        m = DASH_HEAD.match(txt)
        if m:
            head = m.group(1).strip()
            if NAME_RX.fullmatch(head) and len(txt[m.end():].strip()) >= 15:
                cut, kind = m.end(1), "מקף"
    if cut is None: continue
    if make_anchor(doc, p, cut, ANCHOR) is not None: log["עוגן: " + kind] += 1

c = {}; laukmi_anchors.clean_anchors(doc, c)
for k, v in c.items(): log[k] = v

# --- ו. סגנון אמוראים על מה שנוצר ---
am = {}
style_names(doc, SHEMOT, BODY, AM_STYLE, am)
style_regex(doc, [r'(?<![א-ת"\'])(?:ו|ד|ל|כ|מ|ש|וד|ול|וכ|כד|דל|אד)?(ר[יאשחנבהמצעכגפדזס]{0,3}"[א-ת]{1,2})(?![א-ת"\'])'],
            BODY, AM_STYLE, am)
log["אמוראים"] = am.get("מופעים", 0)

doc.save(dst)
for k, v in log.items():
    if v: print(f"{k}: {v}")
print(f'סה"כ {sum(log.values())} שינויים · {time.time()-t0:.1f} שניות · נשמר ל-{dst}')
