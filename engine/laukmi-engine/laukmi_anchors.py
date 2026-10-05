# -*- coding: utf-8 -*-
"""
לאוקמי גירסא - שכבת העוגנים (חלון 3), מרוכזת במקום אחד.
עודכן בסבב ה' לפי העוגנים שהמחבר יצר בעצמו בסבב ד'.
"""
import re
from laukmi_mech import text_map, tracked_replace, make_anchor
from laukmi_rules import SHEMOT, YICHUS, FRAME, BODY, ANCHOR

# קידומת שאינה חלק מהפתיח: מקף, תבליט, מספור באות
PRE = re.compile(r"^\s*(?:([-–])\s*)?(?:(•)\s*)?(?:[אבגדהוזחטי]\.\s*)?")

OPEN  = re.compile(r"^([^:]{2,26}):(\s|$)")          # פתיח ואחריו נקודתיים
QMARK = re.compile(r"^([^?:]{2,20})\?(\s|$)")        # פתיח-שאלה קצר (ואידך? למה? מני?)

NAME_RX = re.compile("|".join(re.escape(x) for x in sorted(SHEMOT, key=len, reverse=True)))
YICH_RX = re.compile(r"^\s*(?:" + "|".join(re.escape(x) for x in sorted(YICHUS, key=len, reverse=True)) + r")(?![א-ת])")

BAD = re.compile(r"[.׻׹]")                            # נקודה או מפריד = סוף משפט, לא פתיח


def open_quote(h):
    """גרש-ציטוט פתוח שלא נסגר. גרש של קיצור (ר' · וכו') אינו נספר."""
    opens  = len(re.findall(r"'(?=[א-ת\u0591-\u05C7])", h))
    closes = len(re.findall(r"(?<=[א-ת\u0591-\u05C7])'(?![א-ת\u0591-\u05C7])", h))
    return opens > closes


def eligible(head, rest, min_rest=10):
    """האם הפתיח ראוי לעוגן."""
    body = head.strip()
    if not body or BAD.search(body):
        return False
    if open_quote(body):
        return False
    named = bool(NAME_RX.search(body))
    if len(rest.strip()) < (6 if named else min_rest):
        return False
    return named or bool(YICH_RX.match(body))


def build(doc, log):
    """יוצר עוגנים בכל הקובץ. מחזיר מונה סיבות."""
    paras  = list(doc.paragraphs())
    styles = [doc.pstyle(p) for p in paras]
    for k, p in enumerate(paras):
        if styles[k] not in BODY:
            continue
        if k and styles[k - 1] == ANCHOR:            # כבר יש עוגן צמוד
            continue
        txt, _ = text_map(p)
        pre = PRE.match(txt)
        off = pre.end() if pre else 0
        tail = txt[off:]

        cut = None
        m = OPEN.match(tail)
        if m and eligible(m.group(1), tail[m.end(1) + 1:]):
            cut = off + m.end(1) + 1
            kind = "נקודתיים"
        if cut is None:
            m = QMARK.match(tail)
            if m and eligible(m.group(1), tail[m.end(1) + 1:]):
                cut = off + m.end(1) + 1
                kind = "שאלה"
        if cut is None:
            m = FRAME.match(txt)
            if m and len(txt[m.end(1):].strip()) >= 15:
                cut = m.end(1)
                kind = "מסגרת"
        if cut is None:
            continue

        # התבליט שימש כסמן ומיצה את תפקידו
        if pre and pre.group(2):
            b = txt.index("•")
            if tracked_replace(doc, p, b, b + 1, ""):
                cut -= 1
                txt, _ = text_map(p)
                while cut < len(txt) and txt[cut - 1] == " " and txt[cut] == " ":
                    tracked_replace(doc, p, cut - 1, cut, "")
                    cut -= 1
                    txt, _ = text_map(p)
        if make_anchor(doc, p, cut, ANCHOR) is not None:
            log[kind] = log.get(kind, 0) + 1
    return log


AL  = re.compile(r'^\s*(?:•\s*)?(א"ל\s+)(?=\S+\s+ל\S)')
BUL = re.compile(r'^\s*(•\s*)')


def clean_anchors(doc, log):
    """ניקוי בתוך פסקאות העוגן: א\"ל כשיש נמען מפורש, ותבליט שנשאר."""
    for p in list(doc.paragraphs()):
        if doc.pstyle(p) != ANCHOR:
            continue
        txt, _ = text_map(p)
        m = AL.match(txt)
        if m:
            a = txt.index('א"ל')
            if tracked_replace(doc, p, a, a + len(m.group(1)), ""):
                log['מחיקת א"ל'] = log.get('מחיקת א"ל', 0) + 1
            txt, _ = text_map(p)
        m = BUL.match(txt)
        if m and txt[m.end(1):].strip() and tracked_replace(doc, p, m.start(1), m.end(1), ""):
            log["תבליט בעוגן"] = log.get("תבליט בעוגן", 0) + 1
    return log
