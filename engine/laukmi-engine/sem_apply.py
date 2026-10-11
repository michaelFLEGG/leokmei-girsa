# -*- coding: utf-8 -*-
"""שכבה סמנטית (ב4) - שתילה. מחיל את הכרעות האצוות (dec_*.json) במעקב
בשם "מנוע סמנטי": ניקוד פסוקים וסגנון פסוק, ותרגום ארמית מסופקת.

כלל הניקוד: הניקוד אינו משנה אותיות. הכרעה שיש בה אות שאינה במקור נפסלת
ונרשמת, ואינה מוחלת. הכרעה סותרת או לא נמצאה - נרשמת, ולא מוחלת."""
import sys, re, json, glob, collections
import laukmi_rules
laukmi_rules.BODY |= {"0.1", "0.2", "List Paragraph"}
import laukmi_mech, laukmi_batch
from laukmi_mech import Doc, text_map, tracked_replace, apply_char_style
from laukmi_batch import styled_flags, QUOTE, PS_STYLE
laukmi_mech.AUTHOR = "מנוע סמנטי"
NIK = re.compile(r"[֑-ׇ]")

src, decdir, dst, report = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
cit, aram = {}, {}
for f in sorted(glob.glob(decdir + '/dec_*.json')):
    d = json.load(open(f, encoding='utf-8'))
    cit.update(d.get('citations') or {})
    aram.update(d.get('aramaic') or {})
arm_src = {x['id']: x for x in json.load(open(decdir + '/aramaic.json', encoding='utf-8'))}
doc = Doc(src)
sid = doc.name2id.get(PS_STYLE)
paras = list(doc.paragraphs())
log, rej = collections.Counter(), []
by = collections.defaultdict(list)
for k, d in cit.items():
    a, off = k.split(':'); by[int(a)].append((int(off), 'c', d, k))
for k, d in aram.items():
    if not d or not d.get('תרגום'):
        log['ארמית נשארה בספק'] += 1; continue
    a, off = k.split(':'); by[int(a)].append((int(off), 'a', d, k))
for k, lst in by.items():
    p = paras[k]
    for off, kind, d, key in sorted(lst, key=lambda x: -x[0]):
        if kind == 'a':
            txt, _ = text_map(p)
            w = arm_src[key]['מילה']
            if txt[off:off + len(w)] != w:
                log['ארמית: לא נמצאה'] += 1; rej.append((key, 'ארמית לא נמצאה')); continue
            if tracked_replace(doc, p, off, off + len(w), d['תרגום']):
                log['ארמית תורגמה'] += 1
            continue
        txt, flags = styled_flags(p, sid)
        m = QUOTE.match(txt, off - 1) or QUOTE.search(txt, max(0, off - 3))
        if not m:
            log['ציטוט: לא נמצא'] += 1; rej.append((key, 'ציטוט לא נמצא')); continue
        a, b = m.start(1), m.end(1)
        nk = d.get('ניקוד')
        if nk and nk != txt[a:b]:
            if NIK.sub('', nk) != NIK.sub('', txt[a:b]):
                log['ניקוד נפסל (אות שונה)'] += 1; rej.append((key, 'ניקוד נפסל: ' + txt[a:b][:40]))
                nk = None
            elif tracked_replace(doc, p, a, b, nk):
                log['נוקד'] += 1
                txt, flags = styled_flags(p, sid); b = a + len(nk)
        if d.get('סוג') == 'פסוק':
            if apply_char_style(doc, p, a, b, PS_STYLE): log['סגנון פסוק הוחל'] += 1
        elif d.get('סוג') in ('משנה', 'לא') and any(flags[a:b]):
            apply_char_style(doc, p, a, b, 'Default Paragraph Font'); log['סגנון פסוק הוסר'] += 1
doc.save(dst)
with open(report, 'w', encoding='utf-8') as f:
    for k, v in log.items(): f.write('%s: %d\n' % (k, v))
    for k, w in rej: f.write('נדחה %s - %s\n' % (k, w))
for k, v in log.items(): print('  %s: %d' % (k, v))
print('נדחו:', len(rej))
