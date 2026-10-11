# -*- coding: utf-8 -*-
"""make_fonts.py - גופני הממשק של לאוקמי גירסא (8.10.2026): וילנא בלבד, תת-קבוצה עברית.
מריצים פעם אחת כשמחליפים גופן: uv run --with fonttools --with brotli python tools/brand/make_fonts.py
התוצרים (tools/brand/fonts/*.woff2 או .woff) נשמרים במאגר, כדי שהבנייה בשרת לא תצטרך brotli.
BAVilna-Medium.ttf נכשל בהמרה ל-woff2, ולכן נשמר ב-woff."""
import os, sys
from fontTools import subset
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(os.path.dirname(os.path.dirname(HERE)), 'input', 'fonts')
OUT = os.path.join(HERE, 'fonts')
os.makedirs(OUT, exist_ok=True)
# שם קובץ מקור -> שם תוצר
JOBS = [('BATM•Vilna-ExtraBold.otf', 'vilna-xb'), ('BAWVilna-Bold.otf', 'vilna-bd'),
        ('BA Vilna Regular.otf', 'vilna-rg'), ('BA•Vilna-Light.otf', 'vilna-lt'),
        ('BAVilna-Title.ttf', 'vilna-title'), ('BAVilna-Medium.ttf', 'vilna-md')]
UNI = list(range(0x20, 0x7F)) + [0xA0, 0xD7] + list(range(0x590, 0x600)) + list(range(0xFB1D, 0xFB50)) + \
      list(range(0x2010, 0x2030)) + [0x25C4, 0x25BA, 0x2022, 0x2026, 0x2190, 0x2192, 0x00B7]

for src, name in JOBS:
    p = os.path.join(FONTS, src)
    if not os.path.exists(p):
        print('חסר:', src); sys.exit(1)
    opt = subset.Options(); opt.layout_features = ['*']; opt.notdef_outline = True; opt.name_IDs = [1, 2]
    opt.hinting = False
    done = None
    for flavor in ('woff2', 'woff'):
        try:
            opt.flavor = flavor
            f = TTFont(p)
            s = subset.Subsetter(opt); s.populate(unicodes=UNI); s.subset(f)
            out = os.path.join(OUT, '%s.%s' % (name, flavor))
            f.flavor = flavor; f.save(out); done = out; break
        except Exception as e:
            print('כשל', flavor, src, repr(e)[:100])
    print(os.path.basename(done), os.path.getsize(done) // 1024, 'KB')
