# -*- coding: utf-8 -*-
"""make_lamed_icon.py - סמל האפליקציה: האות ל' בוילנא Title, זהב מלכותי על כחול קטיפה (14.10.2026).

הרצה (מתוך tools/brand/icon):
  uv run --with fonttools --with brotli --with pillow --with playwright python make_lamed_icon.py

הפלט:
  tools/brand/icon/  קובצי המקור: lamed-large.svg, lamed-small.svg, lamed-maskable.svg, lamed-mono.svg
  tools/brand/icons/ favicon.svg, favicon.ico (16/32/48), favicon-16/32/48.png, apple-touch-icon.png (180),
                     icon-192.png, icon-512.png, icon-maskable-512.png, mask-icon.svg, lamed-600.png, og-image.png
האות מומרת לקווי מתאר (outline) מתוך הגופן, כך שאין תלות בגופן שיטען.
מרכוז אופטי: אופקית לפי מרכז הכובד של הדיו (לצוואר הגבוה של הלמ"ד), אנכית לפי מסגרת הגבולות.
בגדלים 16-48: ל' בלבד, בלי מסגרת. מ-180 ומעלה: מסגרת זהב דקה כמו קורת השער."""
import os, io, json
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.statisticsPen import StatisticsPen
from fontTools.pens.transformPen import TransformPen
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
BRAND = os.path.dirname(HERE)
ICONS = os.path.join(BRAND, 'icons')
FONTS = os.path.join(BRAND, 'fonts')
os.makedirs(ICONS, exist_ok=True)

font = TTFont(os.path.join(FONTS, 'vilna-title.woff2'))
GS = font.getGlyphSet()
GNAME = font.getBestCmap()[0x05DC]
from fontTools.pens.recordingPen import DecomposingRecordingPen


class _Ink:
    """הגליף בלי קווי המתאר שהם תיבה ריקה (בגופן הכותרת יש לכל אות תיבת גבולות, שאינה נראית בדפדפן)."""
    def draw(self, pen):
        rec = DecomposingRecordingPen(GS); GS[GNAME].draw(rec)
        cons, cur = [], []
        for op, a in rec.value:
            cur.append((op, a))
            if op in ('closePath', 'endPath'):
                cons.append(cur); cur = []
        def box(c):
            pts = [pt for op, a in c for pt in a]
            return (min(x for x, y in pts), min(y for x, y in pts), max(x for x, y in pts), max(y for x, y in pts)), len(c)
        full = max((box(c)[0] for c in cons), key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))
        for c in cons:
            bb, n = box(c)
            if len(cons) > 1 and n <= 5 and bb == full:
                continue
            for op, a in c:
                getattr(pen, op)(*a)


INK = _Ink()
bp = BoundsPen(GS); INK.draw(bp)
XMIN, YMIN, XMAX, YMAX = bp.bounds
sp = StatisticsPen(glyphset=GS); INK.draw(sp)
CX = sp.meanX                      # מרכז הכובד האופקי, ביחידות הגופן
GW, GH = XMAX - XMIN, YMAX - YMIN


def lamed_path(S, height_frac, dy=0.0):
    """נתיב ה-SVG של הל' בקנה מידה של קנבס S, לפי חלק מהגובה. מחזיר (path, מידות)."""
    sc = S * height_frac / GH
    # אופקית: מרכז הכובד במרכז, אך לא יותר מאשר שהמסגרת תחרוג (מגבלה של 4% מהקנבס)
    tx = S / 2 - CX * sc
    left, right = tx + XMIN * sc, tx + XMAX * sc
    lim = S * 0.04
    if left < lim: tx += lim - left
    if right > S - lim: tx -= right - (S - lim)
    # אנכית: מרכז תיבת הגבולות במרכז הקנבס, ועוד הזזה זעירה
    ty = S / 2 + (YMIN + GH / 2) * sc + dy * S
    pen = SVGPathPen(GS, ntos=lambda v: ('%.2f' % v).rstrip('0').rstrip('.'))
    INK.draw(TransformPen(pen, (sc, 0, 0, -sc, tx, ty)))
    return pen.getCommands(), sc


GOLD = ('<linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fbe7a1"/><stop offset=".30" stop-color="#e6bd52"/>'
        '<stop offset=".55" stop-color="#c38f2a"/><stop offset=".75" stop-color="#efcf6b"/><stop offset="1" stop-color="#b07c1f"/></linearGradient>')
BG = ('<radialGradient id="b" cx=".5" cy=".28" r=".85"><stop offset="0" stop-color="#173a58"/><stop offset=".55" stop-color="#0b1c2a"/>'
      '<stop offset="1" stop-color="#060f18"/></radialGradient>')


def svg(S, kind):
    """kind: large (עם מסגרת) | small (ל' בלבד) | maskable (שוליים בטוחים) | mono (שחור על שקוף)"""
    if kind == 'mono':
        d, _ = lamed_path(S, 0.72)
        return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d"><path d="%s" fill="#000"/></svg>' % (S, S, d)
    if kind == 'large':
        d, sc = lamed_path(S, 0.56, 0.0)
        e = S * 0.012                      # הבלטה עדינה: עותק כהה מוזז מעט למטה
        m, w = S * 0.055, S * 0.011
        frame = ('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="none" stroke="url(#g)" stroke-width="%.1f"/>'
                 '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="none" stroke="url(#g)" stroke-width="%.1f" opacity=".7"/>') % (
            m, m, S - 2 * m, S - 2 * m, w, m * 1.9, m * 1.9, S - 3.8 * m, S - 3.8 * m, w * .55)
        rx = 0
    elif kind == 'maskable':
        d, sc = lamed_path(S, 0.46, 0.0)   # בתוך עיגול הבטוח (80%) של מסכת ה-maskable
        e = S * 0.010; frame = ''; rx = 0
    else:
        d, sc = lamed_path(S, 0.80, 0.0)
        e = S * 0.014; frame = ''; rx = S * 0.17
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d"><defs>%s%s</defs>'
            '<rect width="%d" height="%d" rx="%.1f" fill="url(#b)"/>%s'
            '<path d="%s" fill="#3a2606" transform="translate(0 %.2f)"/><path d="%s" fill="url(#g)"/></svg>') % (
        S, S, S, S, BG, GOLD, S, S, rx, frame, d, e, d)


# קובצי מקור (וקטור)
for kind in ('large', 'small', 'maskable', 'mono'):
    io.open(os.path.join(HERE, 'lamed-%s.svg' % kind), 'w', encoding='utf-8').write(svg(512, kind))
io.open(os.path.join(ICONS, 'favicon.svg'), 'w', encoding='utf-8').write(svg(512, 'small'))
io.open(os.path.join(ICONS, 'mask-icon.svg'), 'w', encoding='utf-8').write(svg(512, 'mono'))
io.open(os.path.join(ICONS, 'icon-maskable.svg'), 'w', encoding='utf-8').write(svg(512, 'maskable'))

from pathlib import Path
from playwright.sync_api import sync_playwright
U = lambda p: Path(os.path.abspath(p)).as_uri()


def raster(pw_page, svg_text, px, out):
    """מצייר SVG בגודל פיקסלים מדויק (צילום מסך של הדף)."""
    pw_page.set_viewport_size({'width': px, 'height': px})
    pw_page.set_content('<html><body style="margin:0;background:transparent"><div style="width:%dpx;height:%dpx">%s</div></body></html>' % (
        px, px, svg_text.replace('width="512" height="512"', 'width="%d" height="%d"' % (px, px))))
    pw_page.screenshot(path=out, omit_background=True)


with sync_playwright() as pw:
    b = pw.chromium.launch(channel='chrome'); pg = b.new_page(viewport={'width': 512, 'height': 512})
    small, large, mask = svg(512, 'small'), svg(512, 'large'), svg(512, 'maskable')
    for px in (16, 32, 48):
        raster(pg, small, px, os.path.join(ICONS, 'favicon-%d.png' % px))
    raster(pg, large, 180, os.path.join(ICONS, 'apple-touch-icon.png'))
    raster(pg, large, 192, os.path.join(ICONS, 'icon-192.png'))
    raster(pg, large, 512, os.path.join(ICONS, 'icon-512.png'))
    raster(pg, mask, 512, os.path.join(ICONS, 'icon-maskable-512.png'))
    raster(pg, large, 600, os.path.join(ICONS, 'lamed-600.png'))
    # תמונת שיתוף 1200x630
    d, _ = lamed_path(512, 0.80)
    html = ('<style>@font-face{font-family:XB;src:url(%s)}@font-face{font-family:BD;src:url(%s)}'
            'html,body{margin:0}body{width:1200px;height:630px;overflow:hidden;position:relative;background:radial-gradient(ellipse 80%% 70%% at 50%% 25%%,#173a58,#0b1c2a 58%%,#060f18)}'
            '.t{position:absolute;left:0;top:0;width:700px;height:630px;display:flex;flex-direction:column;align-items:center;justify-content:center;direction:rtl;text-align:center}'
            '.f{background:linear-gradient(170deg,#fbe7a1,#e6bd52 30%%,#c38f2a 55%%,#efcf6b 75%%,#b07c1f);-webkit-background-clip:text;background-clip:text;color:transparent;'
            'filter:drop-shadow(0 2px 0 rgba(0,0,0,.7)) drop-shadow(0 0 10px rgba(240,196,90,.4))}'
            'h1{font:400 128px/1.1 XB;margin:0}p{font:700 58px/1.3 BD;margin:14px 0 0}'
            '.r{width:460px;height:3px;margin:24px 0 0;background:linear-gradient(90deg,transparent,#d1a23a,transparent)}'
            '.i{position:absolute;right:70px;top:65px;width:500px;height:500px}'
            '.fr{position:absolute;inset:26px;border:3px solid #b8892a;box-shadow:inset 0 0 0 8px #0b1c2a,inset 0 0 0 10px rgba(209,162,58,.5)}</style>'
            '<div class="fr"></div><div class="i">%s</div>'
            '<div class="t"><h1 class="f">לאוקמי גירסא</h1><div class="r"></div><p class="f">קיצור התלמוד הבבלי</p></div>') % (
        U(os.path.join(FONTS, 'vilna-xb.woff2')), U(os.path.join(FONTS, 'vilna-bd.woff2')),
        __import__('re').sub(r'<rect width="512" height="512"[^>]*/>', '', svg(512, 'small')).replace('width="512" height="512"', 'width="500" height="500"'))
    pg.set_viewport_size({'width': 1200, 'height': 630})
    pg.set_content('<meta charset="utf-8">' + html); pg.wait_for_timeout(1200)
    pg.screenshot(path=os.path.join(ICONS, '_og.png'))
    b.close()

im = Image.open(os.path.join(ICONS, '_og.png')).convert('RGB')
im.save(os.path.join(ICONS, 'og-image.png'), optimize=True)
if os.path.getsize(os.path.join(ICONS, 'og-image.png')) > 150 * 1024:
    im.quantize(colors=96, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(os.path.join(ICONS, 'og-image.png'), optimize=True)
os.remove(os.path.join(ICONS, '_og.png'))
Image.open(os.path.join(ICONS, 'favicon-48.png')).save(os.path.join(ICONS, 'favicon.ico'), sizes=[(16, 16), (32, 32), (48, 48)])
for f in sorted(os.listdir(ICONS)):
    print('%-26s %7d' % (f, os.path.getsize(os.path.join(ICONS, f))))
