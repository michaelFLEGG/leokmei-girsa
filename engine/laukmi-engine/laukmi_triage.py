# -*- coding: utf-8 -*-
"""
לאוקמי גירסא - מיון תיקונים (triage).

מקבל קובץ docx שהמחבר הגיה, מחלץ כל תיקון שלו, ומחליט לאיזו שכבה הוא שייך:

  מכני   - חוק קבוע. אותה החלפה בכל מקום, בלי תלות בהקשר.
           יוצא כשורת טבלה מוכנה להדבקה ב-laukmi_rules.py.
  סמנטי  - ההחלפה תלויה בהקשר: אותו מקור מתורגם אחרת במקומות שונים,
           או שנדרש ידע חיצוני (ניקוד פסוק, מי כאן אמורא, איזה תירוץ ראשון).
           יוצא כאצווה: הסקריפט מוציא מועמדים, המודל מכריע, הסקריפט שותל.
  פייבל  - שיקול דעת מלא. ניסוח מחדש, פיצול טענה, תוספת תוכן, מופע יחידאי.
           לא ניתן להכללה. יוצא כרשימה לעבודה ידנית או בשיחה.

    python3 laukmi_triage.py <קובץ-מוגה.docx> [דוח.md]
"""
import sys, re, json, collections
from laukmi_scan import load, para_style, live_text, q
import laukmi_learn as L

NIK  = re.compile(r"[\u0591-\u05C7]")
HEB  = re.compile(r"[א-ת]")
PFX  = "ודלכמשבהוא"


def corrections(path):
    """כל תיקוני המחבר: (מקור, חלופה, סגנון-פסקה, טקסט-הפסקה).

    מחיקות והוספות סמוכות מזווגות לתיקון אחד; טקסט שלא נגעו בו סוגר את הזוג.
    בלי הזיווג הזה, שני תיקונים נפרדים באותה פסקה מתמזגים לצירוף מלאכותי
    ומסווגים בטעות כניסוח מחדש.
    """
    z, doc, i2n = load(path)
    out = []
    for p in doc.iter(q("p")):
        st = para_style(p, i2n)
        full = live_text(p)
        cur_d, cur_i, pairs = [], [], []
        def flush():
            if cur_d or cur_i:
                pairs.append(("".join(cur_d).strip(), "".join(cur_i).strip()))
            cur_d.clear(); cur_i.clear()
        for t in p.iter(q("t"), q("delText")):
            anc, kind = t.getparent(), ""
            while anc is not None and anc.tag != q("p"):
                if anc.tag == q("del"): kind = "d"; break
                if anc.tag == q("ins"): kind = "i"; break
                anc = anc.getparent()
            s = t.text or ""
            if kind == "d": cur_d.append(s)
            elif kind == "i": cur_i.append(s)
            elif s.strip(): flush()
        flush()
        if not pairs and p.find(q("pPr")) is not None:
            rpr = p.find(q("pPr")).find(q("rPr"))
            if rpr is not None and (rpr.find(q("ins")) is not None or rpr.find(q("del")) is not None):
                pairs = [("", "")]
        for old, new in pairs:
            out.append((old, new, st, full))
    return out


def corpus(path):
    z, doc, i2n = load(path)
    return "\n".join(live_text(p) for p in doc.iter(q("p")))


def overlap(a, b):
    """שיעור האותיות המשותפות - מבחין בין תיקון צורה לניסוח מחדש."""
    A, B = collections.Counter(HEB.findall(a)), collections.Counter(HEB.findall(b))
    if not A or not B: return 0.0
    return sum((A & B).values()) / max(sum(A.values()), sum(B.values()))


def classify(old, new, style, para, text, all_fixes):
    """מחזיר (שכבה, נימוק)."""
    # מבנה: פסקה חדשה או ריקה = שכבת העוגנים, מכנית
    if not old and not new:
        return "מכני", "יצירת עוגן או פיצול פסקה"
    if not old:
        if len(new) <= 3 and not HEB.search(new):
            return "מכני", "הוספת סימן פיסוק או גרש"
        if len(new) <= 12 and any(new.strip().startswith(w) for w in ("ד", "ש", "ל", "ה", "-", "•")):
            return "סמנטי", "תוספת מילית קישור - תלויה בהקשר"
        return "פייבל", "תוספת תוכן"
    if not new:
        if len(old) <= 4 and not HEB.search(old):
            return "מכני", "מחיקת סימן מיותר"
        return "סמנטי", "מחיקה תלוית הקשר"

    # ניקוד: אותן אותיות, נוסף ניקוד
    if NIK.sub("", new) == NIK.sub("", old) and NIK.search(new):
        return "סמנטי", "ניקוד - נדרש מקור מקראי"

    # ניסוח מחדש
    if overlap(old, new) < 0.4 and len(old.split()) >= 3:
        return "פייבל", "ניסוח מחדש - אין חפיפת לשון"
    if len(new) > len(old) * 2.5 + 6:
        return "פייבל", "הרחבה - נוסף תוכן שלא היה"

    # ספירת מופעים בקובץ
    n = text.count(old)
    if n <= 1:
        return "פייבל", "מופע יחידאי - אין מה להכליל"

    # האם המחבר תיקן את אותו מקור לשתי חלופות שונות?
    alts = {b for a, b, *_ in all_fixes if a == old}
    if len(alts) > 1:
        return "סמנטי", "אותו מקור תוקן לשתי חלופות - תלוי הקשר"

    # האם המקור מופיע גם בהקשרים שהמחבר לא נגע בהם, ובמספר גדול?
    if n >= 12:
        return "סמנטי", f"{n} מופעים בקובץ - צריך לבדוק כל אחד בהקשרו"
    return "מכני", f"{n} מופעים, החלפה אחידה"


def report(path, out=None):
    fixes = corrections(path)
    acc = path.replace(".docx", "__acc.docx")
    L.accept_all(path, acc)
    text = corpus(acc)
    buckets = collections.OrderedDict([("מכני", []), ("סמנטי", []), ("פייבל", [])])
    for old, new, style, para in fixes:
        layer, why = classify(old, new, style, para, text, fixes)
        buckets[layer].append((old, new, why, style, para))

    lines = ["# מיון תיקוני המחבר", ""]
    lines.append(f"סך הכל {len(fixes)} תיקונים: "
                 + " · ".join(f"{k} {len(v)}" for k, v in buckets.items()))
    lines.append("")
    lines.append("## מכני - להוסיף לטבלאות ולהריץ")
    lines.append("```python")
    for old, new, why, st, para in buckets["מכני"]:
        if old and new: lines.append(f'    {json.dumps(old, ensure_ascii=False)}: {json.dumps(new, ensure_ascii=False)},  # {why}')
    lines.append("```")
    for old, new, why, st, para in buckets["מכני"]:
        if not (old and new): lines.append(f"- [{st}] {why}: {para[:60]}")
    lines.append("")
    lines.append("## סמנטי - להוציא כאצווה ולהכריע מופע-מופע")
    for old, new, why, st, para in buckets["סמנטי"]:
        lines.append(f"- `{old}` -> `{new}`  ({why})")
        lines.append(f"    - {para[:90]}")
    lines.append("")
    lines.append("## פייבל - שיקול דעת, אין מה להכליל")
    for old, new, why, st, para in buckets["פייבל"]:
        lines.append(f"- `{old}` -> `{new}`  ({why})")
        lines.append(f"    - {para[:90]}")
    txt = "\n".join(lines)
    if out:
        open(out, "w", encoding="utf-8").write(txt)
        print(f"נכתב ל-{out}")
    print(f"{len(fixes)} תיקונים: " + " · ".join(f"{k} {len(v)}" for k, v in buckets.items()))
    return buckets


if __name__ == "__main__":
    report(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
