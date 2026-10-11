# -*- coding: utf-8 -*-
"""sem_batches.py - השכבה הסמנטית (אצוות לסוכנים) למסכת חדשה (11.10.2026).

    python sem_batches.py prep  <קובץ.docx> <תיקיית-פלט> [גודל-אצווה]
        מפיק: cit-NN.json (ציטוטים בגרשיים) ו-aram-NN.json (מופעי ארמית מסופקת, עם מזהה מקום).
    python sem_batches.py apply <קובץ.docx> <תיקיית-הכרעות> <פלט.docx>
        שותל את cit-dec-NN.json ו-aram-dec-NN.json שבתיקייה, במעקב, ואימות אותיות.

מזהה מקום: "<אינדקס פסקה>:<היסט בטקסט החי>". החלפת ארמית: {"id": {"תרגום": "מילה עברית"}} (המילה כולה, כולל אותיות החיבור).
ציטוט: {"id": {"סוג": "פסוק|משנה|לא", "ניקוד": "..."|null}}. ניקוד שאינו שומר את האותיות נדחה.
"""
import sys, os, re, json, collections, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import laukmi_mech
from laukmi_mech import Doc, text_map, tracked_replace, apply_char_style, q
from laukmi_rules import BODY, ANCHOR
import laukmi_batch as LB
import laukmi_aramaic as AR

NIK = re.compile(r'[֑-ׇ]')
HEB = re.compile(r'[א-ת]{3,}')
LONG_DASH = ('–', '—', '―')


def aram_occurrences(doc):
    rx = [re.compile(s) for s in AR.SIGNS]
    known = set(AR.LEXICON) | AR.KEEP
    out = []
    for k, p in enumerate(doc.paragraphs()):
        if doc.pstyle(p) not in BODY | {ANCHOR}:
            continue
        txt, _ = text_map(p)
        masked = re.sub(r"'[^']{0,200}'", lambda m: ' ' * len(m.group(0)), txt)
        for m in HEB.finditer(masked):
            w = m.group(0)
            if w in known: continue
            base = re.sub(r'^(ו|ד|ל|כ|מ|ש|ב|ה|וד|ול|וכ|דל)', '', w)
            if base in known: continue
            if any(r.search(w) for r in rx):
                out.append({'id': '%d:%d' % (k, m.start()), 'מילה': w,
                            'לפני': txt[max(0, m.start() - 70):m.start()], 'אחרי': txt[m.end():m.end() + 50]})
    return out


def prep(path, outdir, size=100):
    os.makedirs(outdir, exist_ok=True)
    tmp = os.path.join(outdir, '_cit.json')
    cits = LB.extract(path, tmp)
    os.remove(tmp)
    doc = Doc(path)
    ar = aram_occurrences(doc)
    for i in range(0, len(cits), size):
        json.dump(cits[i:i + size], open(os.path.join(outdir, 'cit-%02d.json' % (i // size + 1)), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    for i in range(0, len(ar), size):
        json.dump(ar[i:i + size], open(os.path.join(outdir, 'aram-%02d.json' % (i // size + 1)), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('ציטוטים', len(cits), 'אצוות', (len(cits) + size - 1) // size, '| ארמית', len(ar), 'אצוות', (len(ar) + size - 1) // size)


def apply(path, decdir, out):
    laukmi_mech.AUTHOR = 'Claude - סמנטי'
    doc = Doc(path)
    paras = list(doc.paragraphs())
    cdec, adec = {}, {}
    for f in sorted(glob.glob(os.path.join(decdir, 'cit-dec-*.json'))):
        cdec.update(json.load(open(f, encoding='utf-8')))
    for f in sorted(glob.glob(os.path.join(decdir, 'aram-dec-*.json'))):
        adec.update(json.load(open(f, encoding='utf-8')))
    log = collections.Counter()
    # ארמית: מהסוף להתחלה בכל פסקה
    by = collections.defaultdict(list)
    for key, d in adec.items():
        k, off = key.split(':'); by[int(k)].append((int(off), d, 'a'))
    for key, d in cdec.items():
        k, off = key.split(':'); by[int(k)].append((int(off), d, 'c'))
    for k, lst in by.items():
        p = paras[k]
        for off, d, kind in sorted(lst, key=lambda x: -x[0]):
            if kind == 'a':
                new = (d.get('תרגום') or '').strip()
                if not new: log['ארמית: ללא תרגום'] += 1; continue
                if any(c in new for c in LONG_DASH) or len(new.split()) > 3 or NIK.search(new):
                    log['ארמית: נדחה (פורמט)'] += 1; continue
                txt, _ = text_map(p)
                m = HEB.match(txt, off)
                if not m: log['ארמית: לא נמצא'] += 1; continue
                if tracked_replace(doc, p, m.start(), m.end(), new): log['ארמית: הוחלפה'] += 1
            else:
                sid = doc.name2id.get(LB.PS_STYLE)
                txt, flags = LB.styled_flags(p, sid)
                m = LB.QUOTE.match(txt, off - 1) or LB.QUOTE.search(txt, max(0, off - 3))
                if not m: log['ציטוט: לא נמצא'] += 1; continue
                a, b = m.start(1), m.end(1)
                nk = d.get('ניקוד')
                if nk and nk != txt[a:b]:
                    if NIK.sub('', nk) != NIK.sub('', txt[a:b]):
                        log['ניקוד: נדחה (אותיות שונות)'] += 1
                    elif tracked_replace(doc, p, a, b, nk):
                        log['ניקוד: נוקד'] += 1
                        txt, flags = LB.styled_flags(p, sid); b = a + len(nk)
                if d.get('סוג') == 'פסוק':
                    if apply_char_style(doc, p, a, b, LB.PS_STYLE): log['פסוק: סגנון הוחל'] += 1
    doc.save(out)
    for k, v in sorted(log.items()): print('%s: %d' % (k, v))
    return log


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    if sys.argv[1] == 'prep':
        prep(sys.argv[2], sys.argv[3], int(sys.argv[4]) if len(sys.argv) > 4 else 100)
    else:
        apply(sys.argv[2], sys.argv[3], sys.argv[4])
