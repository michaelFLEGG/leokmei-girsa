#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
לאוקמי גירסא - סבב אפס: לימוד המסמך.
אינו נוגע בקובץ. קורא אותו ומפיק דוח מלא + טבלת מועמדים לשכבות הבאות.
    python3 laukmi_scan.py <קובץ.docx> [תיקיית_פלט]
"""
import sys, os, re, json, zipfile, collections
from lxml import etree

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
def q(t): return f"{{{W}}}{t}"
NIKUD = re.compile(r"[\u0591-\u05C7]")


def load(path):
    z = zipfile.ZipFile(path)
    doc = etree.fromstring(z.read("word/document.xml"))
    styles = etree.fromstring(z.read("word/styles.xml"))
    id2name = {}
    for st in styles.findall(q("style")):
        nm = st.find(q("name"))
        id2name[st.get(q("styleId"))] = nm.get(q("val")) if nm is not None else st.get(q("styleId"))
    return z, doc, id2name


def para_style(p, id2name):
    pPr = p.find(q("pPr"))
    if pPr is None: return "Normal"
    ps = pPr.find(q("pStyle"))
    if ps is None: return "Normal"
    return id2name.get(ps.get(q("val")), ps.get(q("val")))


def live_text(p):
    """הטקסט החי: בלי מה שנמחק במעקב, עם טאבים כתו \t."""
    buf = []
    for el in p.iter():
        if el.tag == q("t") or el.tag == q("tab"):
            anc, skip = el.getparent(), False
            while anc is not None and anc.tag != q("p"):
                if anc.tag == q("del"): skip = True; break
                anc = anc.getparent()
            if skip: continue
            buf.append("\t" if el.tag == q("tab") else (el.text or ""))
    return "".join(buf)


def scan(path, outdir="."):
    z, doc, id2name = load(path)
    paras = list(doc.iter(q("p")))
    R = {"קובץ": os.path.basename(path), "פסקאות": len(paras)}

    # --- א. מצב מעקב השינויים ---
    xml = z.read("word/document.xml").decode("utf-8", "ignore")
    authors = collections.Counter(re.findall(r'w:author="([^"]*)"', xml))
    R["מעקב"] = {"הוספות ממתינות": xml.count("<w:ins "), "מחיקות ממתינות": xml.count("<w:del "),
                 "מחברים": dict(authors)}
    try:
        st = z.read("word/settings.xml").decode("utf-8", "ignore")
        R["מעקב"]["דלוק בקובץ"] = "<w:trackChanges" in st
    except KeyError:
        R["מעקב"]["דלוק בקובץ"] = False

    # --- ב. מפת הסגנונות בפועל ---
    by_style = collections.Counter()
    samples = collections.defaultdict(list)
    rows = []
    for i, p in enumerate(paras):
        s = para_style(p, id2name)
        t = live_text(p)
        by_style[s] += 1
        if len(samples[s]) < 3 and t.strip(): samples[s].append(t[:90])
        rows.append((i, s, t))
    R["סגנונות"] = {s: {"פסקאות": n, "דוגמאות": samples[s]} for s, n in by_style.most_common()}

    # --- ג. סגנונות תו בשימוש ---
    cstyles = collections.Counter()
    for rs in doc.iter(q("rStyle")):
        cstyles[id2name.get(rs.get(q("val")), rs.get(q("val")))] += 1
    R["סגנונות תו"] = dict(cstyles.most_common())

    # --- ד. טאבים: איפה, ומה בא אחריהם (המידע שאסור לאבד) ---
    tabs = {"בתחילת פסקה": collections.Counter(), "באמצע פסקה": collections.Counter()}
    tab_ctx = []
    for i, s, t in rows:
        if "\t" not in t: continue
        if t.startswith("\t") or t.lstrip(" ").startswith("\t"):
            tabs["בתחילת פסקה"][s] += 1
        for m in re.finditer(r"\t", t):
            if m.start() > 0:
                tabs["באמצע פסקה"][s] += 1
                before = t[max(0, m.start()-25):m.start()]
                after = t[m.end():m.end()+25]
                tab_ctx.append({"פסקה": i, "סגנון": s, "לפני": before, "אחרי": after})
    R["טאבים"] = {k: dict(v) for k, v in tabs.items()}
    R["טאבים_דוגמאות"] = tab_ctx[:40]

    # --- ה. מועמדי "חלון 3": פתיח קצר בתחילת שורת גוף ---
    OPEN = re.compile(r"^\s*([^:]{1,22}):\s")
    cand = []
    body = {"Normal", "רגיל", "רווח לפני", "פיסקת תשובה"}
    for i, s, t in rows:
        if s not in body or not t.strip(): continue
        m = OPEN.match(t)
        if m:
            cand.append({"פסקה": i, "פתיח": m.group(1).strip(), "המשך": t[m.end():m.end()+60]})
    R["מועמדי_חלון3"] = {"סה\"כ": len(cand), "דוגמאות": cand[:40]}
    R["פתיחים_שכיחים"] = dict(collections.Counter(c["פתיח"] for c in cand).most_common(30))

    # --- ו. פסוקים: גרש בודד, מנוקד מול לא מנוקד ---
    QUOTE = re.compile(r"'([^']{3,200}?)'")
    nik, plain = [], []
    for i, s, t in rows:
        for m in QUOTE.finditer(t):
            (nik if NIKUD.search(m.group(1)) else plain).append({"פסקה": i, "טקסט": m.group(1)[:70]})
    R["פסוקים"] = {"מנוקדים": len(nik), "לא מנוקדים": len(plain),
                   "דוגמאות לא מנוקדים": plain[:30]}

    # --- ז. שאריות ארמית וסימנים ---
    ARAMIT = ["התם","הכא","נמי","כולהו","לאו","ליתא","דהא","איכא","ליכא","פליגי","מיעוטא","רובא",
              "בעינן","אזלינן","אמרינן","טובא","מילתא","תרוייהו","בהדדי","אלמא","קסבר","והדר","היכא"]
    left = collections.Counter()
    for i, s, t in rows:
        if s not in body: continue
        for w in ARAMIT:
            n = len(re.findall(r"(?<![א-ת\"'])" + w + r"(?![א-ת\"'])", t))
            if n: left[w] += n
    R["ארמית_שנותרה"] = dict(left.most_common())
    R["סימנים"] = {"תבליט •": sum(t.count("•") for _, _, t in rows),
                   "מקף ארוך –": sum(t.count("–") for _, _, t in rows),
                   "נקודה-פסיק ;": sum(t.count(";") for _, _, t in rows),
                   "רווח כפול": sum(len(re.findall(r"  +", t)) for _, _, t in rows)}

    # --- ח. הפרות שערי הבדיקה ---
    anchor, heads = "חלון 3", {"נושא", "ד''ה משנה", "משניות", "דף בצד", "כותר פנימי פ"}
    long_anchor = [(i, t) for i, s, t in rows if s == anchor and len(t.strip()) > 20]
    twin = [i for k, (i, s, t) in enumerate(rows)
            if s == anchor and k + 1 < len(rows) and rows[k+1][1] == anchor]
    long_body = [(i, len(t)) for i, s, t in rows if s in body and len(t) > 120]
    sep = [i for k, (i, s, t) in enumerate(rows)
           if (not t.strip() or t.strip() in "׻׹") and k + 1 < len(rows) and rows[k+1][1] in heads]
    R["שערים"] = {"חלון 3 מעל 20 תווים": len(long_anchor), "דוגמאות": long_anchor[:10],
                  "שתי שורות חלון 3 רצופות": len(twin),
                  "שורות גוף מעל 120 תווים": len(long_body),
                  "מפריד לפני כותרת": len(sep)}

    os.makedirs(outdir, exist_ok=True)
    base = os.path.splitext(os.path.basename(path))[0]
    with open(os.path.join(outdir, base + "-דוח.json"), "w", encoding="utf-8") as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    return R


def brief(R):
    out = [f"== {R['קובץ']} · {R['פסקאות']} פסקאות ==",
           f"מעקב: דלוק={R['מעקב']['דלוק בקובץ']} · ממתינות {R['מעקב']['הוספות ממתינות']} הוספות ו-{R['מעקב']['מחיקות ממתינות']} מחיקות · מחברים {R['מעקב']['מחברים']}",
           "סגנונות: " + ", ".join(f"{k}={v['פסקאות']}" for k, v in list(R["סגנונות"].items())[:12]),
           "סגנונות תו: " + str(R["סגנונות תו"]),
           "טאבים: " + str(R["טאבים"]),
           f"מועמדי חלון 3: {R['מועמדי_חלון3']['סה\"כ']} · פתיחים שכיחים: " + ", ".join(list(R["פתיחים_שכיחים"])[:12]),
           f"פסוקים: {R['פסוקים']['מנוקדים']} מנוקדים, {R['פסוקים']['לא מנוקדים']} לא מנוקדים",
           "ארמית שנותרה: " + str(R["ארמית_שנותרה"]),
           "סימנים: " + str(R["סימנים"]),
           "שערים: " + str({k: v for k, v in R["שערים"].items() if k != "דוגמאות"})]
    return "\n".join(out)


if __name__ == "__main__":
    R = scan(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else ".")
    print(brief(R))
