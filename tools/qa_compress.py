# -*- coding: utf-8 -*-
"""qa_compress.py - מקטין את צילומי ה-QA (PNG בגודל מלא) ל-JPEG קל, ומוחק את המקור. שימוש: uv run --with pillow python tools/qa_compress.py <dir>"""
import os, sys
from PIL import Image
d = sys.argv[1]; n = 0
for root, _, files in os.walk(d):
    for f in files:
        if not f.endswith('.png'): continue
        p = os.path.join(root, f)
        im = Image.open(p).convert('RGB')
        w = 640 if im.width < im.height * 1.2 else 1000
        if im.width > w: im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
        im.save(p[:-4] + '.jpg', 'JPEG', quality=70, optimize=True); os.remove(p); n += 1
print('converted', n)
