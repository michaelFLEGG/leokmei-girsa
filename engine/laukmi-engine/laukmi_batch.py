# -*- coding: utf-8 -*-
"""
לאוקמי גירסא - שלב ב': אצווה.
הסקריפט מוציא מועמדים -> המודל מכריע על כולם בקריאה אחת -> הסקריפט שותל.

    python3 laukmi_batch.py extract <קובץ.docx> <אצווה.json>
    python3 laukmi_batch.py apply   <קובץ.docx> <הכרעות.json> <פלט.docx>

מבנה ההכרעה (JSON): {"מזהה": {"סוג": "פסוק|משנה|לא", "ניקוד": "טקסט מנוקד או null"}}
"""
import sys, re, json, collections
from lxml import etree
import laukmi_mech
from laukmi_mech import Doc, text_map, tracked_replace, apply_char_style, q, W
from laukmi_rules import BODY, ANCHOR

NIK   = re.compile(r"[\u0591-\u05C7]")
QUOTE = re.compile(r"'([^']{2,200}?)'")
PS_STYLE = "פסוק תו"

# מילות הבאה שמעידות מה טיבו של הציטוט
MIKRA  = ["שנא'", "שנאמר", "דכתיב", "וכתיב", "כתיב", 'ת"ל', "תלמוד לומר", "אמר קרא",
          "דאמר קרא", "מדכתיב", "והכתיב", "דהכתיב", "נאמר", "מ'", "ד'", "קרא"]
MISHNA = ["דתנן", "תנן", "דתניא", "תניא", "קתני", "דקתני", "והתניא", "והתנן", "מתני'",
          "בברייתא", "ברייתא", "דת\"ר", 'ת"ר', "משנה"]


def styled_flags(p, sid):
    """לכל תו בפסקה - האם הוא נושא את סגנון התו הנתון."""
    flags, buf = [], []
    for r in p.iter(q("r")):
        rp = r.find(q("rPr")); st = None
        if rp is not None:
            rs = rp.find(q("rStyle"))
            if rs is not None: st = rs.get(q("val"))
        for t in r.iter(q("t")):
            anc, skip = t.getparent(), False
            while anc is not None and anc.tag != q("p"):
                if anc.tag == q("del"): skip = True; break
                anc = anc.getparent()
            if skip: continue
            s = t.text or ""
            buf.append(s); flags += [st == sid] * len(s)
    return "".join(buf), flags


def guess(before):
    """ניחוש מכני לפי מילת ההבאה שלפני הציטוט."""
    tail = before[-30:]
    for w in MIKRA:
        if tail.rstrip().endswith(w) or (w in tail and tail.rindex(w) > len(tail) - 12):
            return "פסוק"
    for w in MISHNA:
        if w in tail and tail.rindex(w) > len(tail) - 14:
            return "משנה"
    return "?"


def extract(path, out):
    doc = Doc(path)
    sid = doc.name2id.get(PS_STYLE)
    items = []
    for k, p in enumerate(doc.paragraphs()):
        st = doc.pstyle(p)
        if st not in BODY | {ANCHOR}: continue
        txt, flags = styled_flags(p, sid)
        for m in QUOTE.finditer(txt):
            seg = m.group(1)
            items.append({
                "id": f"{k}:{m.start(1)}",
                "טקסט": seg,
                "מנוקד": bool(NIK.search(seg)),
                "סגנון": bool(any(flags[m.start(1):m.end(1)])),
                "לפני": txt[max(0, m.start() - 45):m.start()],
                "אחרי": txt[m.end():m.end() + 25],
                "ניחוש": guess(txt[:m.start()]),
            })
    json.dump(items, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    c = collections.Counter((i["ניחוש"], i["מנוקד"], i["סגנון"]) for i in items)
    print(f"הופקו {len(items)} ציטוטים -> {out}")
    for k, v in c.most_common(): print("  ניחוש=%s מנוקד=%s סגנון=%s : %d" % (k[0], k[1], k[2], v))
    return items


def apply(path, decisions_file, out):
    laukmi_mech.AUTHOR = "Claude - שלב ב"
    doc = Doc(path)
    sid = doc.name2id.get(PS_STYLE)
    dec = json.load(open(decisions_file, encoding="utf-8"))
    paras = list(doc.paragraphs())
    log = collections.Counter()
    # מעבדים מהסוף להתחלה בכל פסקה, כדי שההיסטים לא יזוזו
    by_par = collections.defaultdict(list)
    for key, d in dec.items():
        k, off = key.split(":")
        by_par[int(k)].append((int(off), d))
    for k, lst in by_par.items():
        p = paras[k]
        for off, d in sorted(lst, reverse=True):
            txt, flags = styled_flags(p, sid)
            m = QUOTE.match(txt, off - 1) or QUOTE.search(txt, max(0, off - 3))
            if not m: log["לא נמצא"] += 1; continue
            a, b = m.start(1), m.end(1)
            nk = d.get("ניקוד")
            if nk and nk != txt[a:b]:
                if tracked_replace(doc, p, a, b, nk):
                    log["נוקד"] += 1
                    txt, flags = styled_flags(p, sid)
                    b = a + len(nk)
            if d.get("סוג") == "פסוק":
                if apply_char_style(doc, p, a, b, PS_STYLE): log["סגנון הוחל"] += 1
            elif d.get("סוג") in ("משנה", "לא"):
                if any(flags[a:b]):
                    if apply_char_style(doc, p, a, b, "Default Paragraph Font") or True:
                        log["סגנון הוסר"] += 1
    doc.save(out)
    for k, v in log.items(): print(f"{k}: {v}")
    return log


if __name__ == "__main__":
    if sys.argv[1] == "extract":
        extract(sys.argv[2], sys.argv[3])
    else:
        apply(sys.argv[2], sys.argv[3], sys.argv[4])
