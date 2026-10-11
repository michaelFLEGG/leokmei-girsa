# -*- coding: utf-8 -*-
"""מקף ארוך או בינוני (– —) בגוף הוורד הופך ל"-" רגיל, במעקב, בשם "מנוע מכני".
כלל קבוע של בעל הפרויקט: בלי מקף ארוך או בינוני בשום מקום."""
import sys, re
import laukmi_mech
from laukmi_mech import Doc, text_map, tracked_replace
laukmi_mech.AUTHOR = "מנוע מכני"
doc = Doc(sys.argv[1]); n = 0
for p in list(doc.paragraphs()):
    for _ in range(50):
        t, _s = text_map(p)
        m = re.search('[–—]', t)
        if not m: break
        if not tracked_replace(doc, p, m.start(), m.end(), '-'): break
        n += 1
doc.save(sys.argv[2]); print('מקפים ארוכים שהוחלפו:', n)
