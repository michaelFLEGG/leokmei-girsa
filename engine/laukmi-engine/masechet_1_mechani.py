# -*- coding: utf-8 -*-
"""
מנוע א - המנוע המכני המלא.

מריצים אותו על מסכת חדשה שלא עברה שום סבב, והוא מחיל בבת אחת את כל
הכללים שהצטברו בשמונת הסבבים של חולין. כשבע שניות למסכת שלמה.

    python3 masechet_1_mechani.py <קלט.docx> <פלט.docx>

הפלט הוא אותו קובץ עם כל התיקונים כעקוב-אחר-שינויים, תחת המחבר
"Claude - מנוע מכני". שום דבר אינו נמחק בלי שתראה אותו.

סדר הפעולות אינו שרירותי: צירופים לפני מילים בודדות (כדי ש"מפומיה ד"
יתפוס לפני "פומיה"), ניקוי תווים לפני העוגנים (כדי שגרש שבור לא יפסול
פתיח), והעוגנים לפני סגנון האמוראים (כדי שהשמות שעברו לעוגן ינוקו).
"""
import sys, re, time, collections
import laukmi_mech
from laukmi_mech import (Doc, run_replacements, run_replacements_pfx, run_raw, run_rx,
                         style_names, style_regex, unstyle_words, make_anchor,
                         text_map, tracked_replace)
from laukmi_rules import *
from laukmi_aramaic import LEXICON, PHRASES, MIGZAR
import laukmi_anchors, laukmi_aramaic

laukmi_mech.AUTHOR = "מנוע מכני"

if len(sys.argv) < 3:
    print(__doc__); sys.exit(1)
src, dst = sys.argv[1], sys.argv[2]

t0 = time.time()
doc = Doc(src)
log = collections.Counter()
ALL = BODY | {ANCHOR}


def run(name, fn, table, styles=BODY):
    l = {}
    fn(doc, table, styles, l)
    log[name] += sum(l.values())


# ===== 1. ניקוי תווים =====
run("# נעשה גרש", run_raw, HASH_DUP, ALL | HEADS)
run("# נעשה גרש", run_raw, HASH_ONE, ALL | HEADS)
run("גרש נעשה גרשיים", run_raw, GERESH, ALL)
run("גרש נעשה גרשיים", run_rx, GERESH_RX, ALL)
run("גרש כפול", run_rx, DOUBLE_GERESH, ALL | HEADS)
run("רווח אחרי גרש", run_rx, QUOTE_SPACE, ALL)
run("רווח שנבלע", run_raw, SPACES, ALL)
run("רווח אחרי פיסוק", run_rx, SPACE_RX, ALL)
n = 0
for p in list(doc.paragraphs()):
    if doc.pstyle(p) not in BODY: continue
    txt, _ = text_map(p)
    m = LEAD_SPACE.match(txt)
    if m and txt.strip() and tracked_replace(doc, p, 0, m.end(), ""): n += 1
log["רווח מוביל"] = n

# ===== 2. קיצורים, עברות, ארמית =====
run("קיצורים", run_replacements_pfx, KITZUR)
run("עברות", run_replacements_pfx, IVRUT)
run("ארמית", run_replacements_pfx, ARAM2)
run("צירופים", run_replacements, NOPFX)
run("פיסוק", run_raw, PUNCT)
run("צירופי רצף", run_raw, RAW2)
run("דפוסים", run_rx, RX)

run("מילים שנלמדו", run_replacements_pfx, WORDS)
run("צירופים שנלמדו", run_raw, RAWS)
run("דפוסים שנלמדו", run_rx, RXS)

run("מילים שנלמדו", run_replacements_pfx, WORDS5)
run("כי נעשה כש", run_rx, KI_RX)
run("מילים שנלמדו", run_replacements_pfx, WORDS6)
run("צירופים שנלמדו", run_raw, RAWS6)
run("מילים שנלמדו", run_replacements_pfx, WORDS7)
run("צירופים שנלמדו", run_raw, RAWS7)
run("מילים שנלמדו מהמנהל", run_replacements_pfx, WORDS_LEARNED)
run("צירופים שנלמדו מהמנהל", run_raw, RAWS_LEARNED)

# ===== 3. הגוי נכרי, העבודה ע"ז =====
run('עכו"ם נעשה ע"ז', run_raw, AKUM_EZ, ALL | HEADS)
run('עכו"ם נעשה נכרי', run_replacements_pfx, AKUM_NOCHRI, ALL | HEADS)

# ===== 4. שכבת הארמית הוודאית =====
run("צירופים ארמיים", run_raw, PHRASES, ALL)
run("מילים ארמיות", run_replacements_pfx, LEXICON, ALL)
mig = [(r'(?<![א-ת"\'])(ו|ד|ל|ש|כ|ב)?למי' + re.escape(k) + r'(?![א-ת"\'])', r'\1' + v)
       for k, v in MIGZAR.items()]
run("מקור למי-", run_rx, mig, ALL)

# ===== 5. עוגנים =====
laukmi_anchors.YICH_RX = re.compile(
    r"^\s*(?:" + "|".join(re.escape(x) for x in sorted(
        set(YICHUS + YICHUS6 + YICHUS7 + YICHUS8), key=len, reverse=True)) + r")(?![א-ת])")
a = {}
laukmi_anchors.build(doc, a)
log["עוגנים"] = sum(a.values())

paras  = list(doc.paragraphs())
styles = [doc.pstyle(p) for p in paras]
YICH6_RX = re.compile(r"^(?:" + "|".join(re.escape(x) for x in sorted(
    set(YICHUS6 + YICHUS7 + YICHUS8), key=len, reverse=True)) + r")(?![א-ת])")
for k, p in enumerate(paras):
    if styles[k] not in BODY: continue
    if k and styles[k - 1] == ANCHOR: continue
    txt, _ = text_map(p)
    cut = None
    m = COMMA_HEAD.match(txt)
    if m and YICH6_RX.match(m.group(1).strip()) and len(txt[m.end(1) + 1:].strip()) >= 15:
        cut = m.end(1) + 1
    if cut is None:
        m = DASH_HEAD.match(txt)
        if m and laukmi_anchors.NAME_RX.fullmatch(m.group(1).strip()) \
           and len(txt[m.end():].strip()) >= 15:
            cut = m.end(1)
    if cut is not None and make_anchor(doc, p, cut, ANCHOR) is not None:
        log["עוגנים"] += 1

# "אמר" פותח וחותם בעוגן
n = m2 = 0
for p in list(doc.paragraphs()):
    if doc.pstyle(p) != ANCHOR: continue
    txt, _ = text_map(p)
    h = AMAR_HEAD.match(txt)
    if h and tracked_replace(doc, p, h.start(1), h.end(1), ""):
        n += 1
        txt, _ = text_map(p)
    t = AMAR_TAIL.search(txt)
    if t and len(txt[:t.start(1)].strip()) >= 2 \
       and tracked_replace(doc, p, t.start(1), t.end(1), ""):
        m2 += 1
log['מחיקת "אמר" בעוגן'] = n + m2

AL_BODY = re.compile(r'^\s*(?:•\s*)?(א"ל\s+)(?=\S+\s+ל\S)')
n = 0
for p in list(doc.paragraphs()):
    if doc.pstyle(p) not in BODY: continue
    txt, _ = text_map(p)
    m = AL_BODY.match(txt)
    if m:
        a0 = txt.index('א"ל')
        if tracked_replace(doc, p, a0, a0 + len(m.group(1)), ""): n += 1
log['מחיקת א"ל בגוף'] = n

c = {}
laukmi_anchors.clean_anchors(doc, c)
log["ניקוי עוגנים"] = sum(c.values())

# ===== 6. שמות אמוראים =====
un = {}
for st in (AM_STYLE, "אמוראים תו"): unstyle_words(doc, NOT_NAME, ALL, st, un)
log["סגנון שהוסר ממונחים"] = un.get("הוסר", 0)
am = {}
style_names(doc, SHEMOT, BODY, AM_STYLE, am)
style_regex(doc, NAME_RT, BODY, AM_STYLE, am)
log["שמות שסוגננו"] = am.get("מופעים", 0)
un2 = {}
for st in (AM_STYLE, "אמוראים תו"): unstyle_words(doc, NOT_NAME, ALL, st, un2)
log["סגנון שהוסר ממונחים"] += un2.get("הוסר", 0)

doc.save(dst)
print("=" * 46)
for k, v in log.items():
    if v: print(f"  {k}: {v}")
print("=" * 46)
print(f'סה"כ {sum(log.values())} שינויים · {time.time()-t0:.1f} שניות · נשמר ל-{dst}')
print()
print("הצעד הבא: python3 masechet_2_otzva.py " + dst)
