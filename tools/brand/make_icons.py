import os
from playwright.sync_api import sync_playwright
from PIL import Image
stops,filt=open('foil_parts.txt').read().split('\n',1)
velvet="url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='220' height='220'><filter id='v'><feTurbulence type='fractalNoise' baseFrequency='1.4 .6' numOctaves='3' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 .55  0 0 0 0 .7  0 0 0 0 .85  0 0 0 .09 0'/></filter><rect width='100%' height='100%' filter='url(%23v)'/></svg>\")"
base=('<style>@font-face{font-family:T;src:url(vilna-title.ttf)}@font-face{font-family:VB;src:url(vilna-bd.otf)}'
 'html,body{margin:0}body{background:%s,radial-gradient(ellipse 80%% 70%% at 50%% 40%%,#163a58,#0f263b 55%%,#0b1c2a)}</style>'%velvet)
def svgtxt(w,h,inner,blur,scale):
    f=filt.replace('id="tfoil"','id="f"').replace('stdDeviation="2.2"','stdDeviation="%s"'%blur).replace('surfaceScale="5"','surfaceScale="%s"'%scale)
    return '<svg width="%d" height="%d" viewBox="0 0 %d %d" xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="g" x1="0" y1="0" x2=".35" y2="1">%s</linearGradient>%s</defs><g filter="url(#f)" fill="url(#g)">%s</g></svg>'%(w,h,w,h,stops,f,inner)
og=base+('<div style="width:1200px;height:630px;position:relative;overflow:hidden">'
 '<img src="shaar-zahav.svg" style="position:absolute;left:60px;top:40px;height:550px">'
 '<div style="position:absolute;right:40px;top:0;bottom:0;width:700px;display:flex;align-items:center;justify-content:center">'+
 svgtxt(700,440,'<text x="350" y="200" font-family="T" font-size="96" text-anchor="middle" direction="rtl">לאוקמי גירסא</text>'
 '<path d="M80 266 H312 V270 H80Z M388 266 H620 V270 H388Z"/><path d="M350 256 l12 12 -12 12 -12 -12z"/>'
 '<text x="350" y="352" font-family="VB" font-size="56" text-anchor="middle" direction="rtl">קיצור התלמוד הבבלי</text>',2.4,6)+'</div></div>')
def tile(px,blur,scale,rad):
    inner='<text x="%s" y="%s" font-family="T" font-size="%s" text-anchor="middle">ל</text>'%(px/2,px*0.80,px*0.86)
    return base+'<div style="width:%dpx;height:%dpx;border-radius:%dpx;overflow:hidden;display:flex;align-items:center;justify-content:center">%s</div>'%(px,px,rad,svgtxt(px,px,inner,blur,scale))
gate=lambda px: base+'<div style="width:%dpx;height:%dpx;display:flex;align-items:center;justify-content:center"><img src="shaar-zahav.svg" style="height:%dpx"></div>'%(px,px,px*0.86)
jobs={'og-image.png':(og,1200,630),'favicon-16.png':(tile(16,.3,.8,3),16),'favicon-32.png':(tile(32,.5,1.2,6),32),'favicon-48.png':(tile(48,.7,1.6,8),48),
 'apple-touch-icon.png':(tile(180,2.0,4,0),180),'icon-192.png':(tile(192,2.0,4,0),192),'icon-512.png':(gate(512),512)}
with sync_playwright() as pw:
    b=pw.chromium.launch()
    for name,v in jobs.items():
        html,w=v[0],v[1]; h=630 if name=='og-image.png' else w
        open('icons/_t.html','w',encoding='utf8').write(html)
        pg=b.new_page(viewport={'width':w,'height':h})
        pg.goto('file://'+os.path.abspath('icons/_t.html')); pg.wait_for_timeout(2500)
        pg.screenshot(path='icons/'+name,clip={'x':0,'y':0,'width':w,'height':h},omit_background=name.startswith('favicon')); pg.close()
    b.close()
Image.open('icons/favicon-48.png').save('icons/favicon.ico',sizes=[(16,16),(32,32),(48,48)])
im=Image.new('RGBA',(300,120),(255,255,255,255))
for i,(n,x) in enumerate((('favicon-16.png',10),('favicon-32.png',40),('favicon-48.png',90),('apple-touch-icon.png',150))):
    t=Image.open('icons/'+n); 
    if n.startswith('apple'): t=t.resize((110,110))
    im.paste(t,(x,5),t if t.mode=='RGBA' else None)
im.save('icons_preview.png')
