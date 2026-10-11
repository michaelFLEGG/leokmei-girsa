# -*- coding: utf-8 -*-
"""make_icons.py - favicon, אייקון לטלפון ותמונת שיתוף מהשער הסימטרי (8.10.2026).
המקור: shaar-v2/shaar-symmetri-master.png (שקוף, סימטרי עד הפיקסל). הרצה: uv run --with pillow --with playwright python make_icons.py (מתוך tools/brand)."""
import os
from PIL import Image
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
M = Image.open('shaar-v2/shaar-symmetri-master.png').convert('RGBA')
NAVY = (11, 28, 42, 255)

def tile(px, fill=0.88, bg=NAVY, radius=0):
    t = Image.new('RGBA', (px, px), bg if bg else (0, 0, 0, 0))
    h = round(px * fill); w = round(h * M.width / M.height)
    g = M.resize((w, h), Image.LANCZOS)
    t.alpha_composite(g, ((px - w) // 2, (px - h) // 2))
    return t

os.makedirs('icons', exist_ok=True)
tile(16, .96, None).save('icons/favicon-16.png')
tile(32, .96, None).save('icons/favicon-32.png')
tile(48, .96, None).save('icons/favicon-48.png')
tile(180, .86).save('icons/apple-touch-icon.png')
tile(192, .86).save('icons/icon-192.png')
tile(512, .88).save('icons/icon-512.png')
Image.open('icons/favicon-48.png').save('icons/favicon.ico', sizes=[(16, 16), (32, 32), (48, 48)])

from pathlib import Path
U = lambda p: Path(os.path.abspath(p)).as_uri()
html = '''<style>@font-face{font-family:XB;src:url(%s)}@font-face{font-family:BD;src:url(%s)}
html,body{margin:0}body{width:1200px;height:630px;overflow:hidden;position:relative;background:radial-gradient(ellipse 80%% 60%% at 50%% 20%%,#102a42,#091827 55%%,#060f18)}
img{position:absolute;left:70px;top:40px;height:550px}
.t{position:absolute;right:50px;top:0;bottom:0;width:640px;display:flex;flex-direction:column;align-items:center;justify-content:center;direction:rtl;text-align:center}
.f{background:linear-gradient(170deg,#fbe7a1,#e6bd52 30%%,#c38f2a 55%%,#efcf6b 75%%,#b07c1f);-webkit-background-clip:text;background-clip:text;color:transparent;filter:drop-shadow(0 2px 0 rgba(0,0,0,.7)) drop-shadow(0 0 10px rgba(240,196,90,.45))}
h1{font:400 118px/1.1 XB;margin:0}p{font:700 54px/1.3 BD;margin:14px 0 0}
.r{width:420px;height:3px;margin:22px 0 0;background:linear-gradient(90deg,transparent,#d1a23a,transparent)}</style>
<img src="%s"><div class="t"><h1 class="f">לאוקמי גירסא</h1><div class="r"></div><p class="f">קיצור התלמוד הבבלי</p></div>''' % (
    U('fonts/vilna-xb.woff2'), U('fonts/vilna-bd.woff2'),
    U('shaar-v2/shaar-zohar-1120.webp'))
open('icons/_og.html', 'w', encoding='utf-8').write('<meta charset="utf-8">' + html)
with sync_playwright() as pw:
    b = pw.chromium.launch(channel='chrome'); pg = b.new_page(viewport={'width': 1200, 'height': 630})
    pg.goto(U('icons/_og.html')); pg.wait_for_timeout(1500)
    pg.screenshot(path='icons/og-image.png'); b.close()
os.remove('icons/_og.html')
print('ok')
