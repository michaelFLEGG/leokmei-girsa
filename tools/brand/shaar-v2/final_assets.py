from PIL import Image, ImageFilter
import numpy as np
S0=Image.open('sym.png')
def make(width,glowr):
    h=round(2408*width/1600)
    S=S0.resize((width,h),Image.LANCZOS)
    a=np.array(S)[:,:,3].astype(float)/255; H,W=a.shape
    yy,xx=np.mgrid[0:H,0:W]; t=(xx/W)*.35+(yy/H)*.65
    stops=[(0,'#fbe7a1'),(.3,'#e6bd52'),(.55,'#c38f2a'),(.75,'#efcf6b'),(1,'#b07c1f')]
    pos=np.array([p for p,_ in stops]); cols=np.array([[int(c[i:i+2],16) for i in (1,3,5)] for _,c in stops],float)
    rgb=np.dstack([np.interp(t,pos,cols[:,k]) for k in range(3)])
    b=np.array(Image.fromarray((a*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.1*width/560))).astype(float)/255
    gy,gx=np.gradient(b); L=(-gx*.7-gy*.7)*2.2*(width/560)
    rgb=np.clip(rgb*(1+np.clip(L,-.6,.9))[:,:,None]+np.clip(L,0,1)[:,:,None]*90,0,255)
    im=Image.fromarray(np.dstack([rgb,a*255]).astype(np.uint8),'RGBA')
    gl=Image.fromarray((a*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(glowr))
    g=Image.new('RGBA',im.size,(240,196,90,0)); g.putalpha(gl.point(lambda v:int(v*.4)))
    base=Image.new('RGBA',im.size,(0,0,0,0)); base.alpha_composite(g); base.alpha_composite(im); return base
import os; os.makedirs('final',exist_ok=True)
for w in (560,1120):
    make(w,3.2*w/560).save(f'final/shaar-zohar-{w}.webp',quality=90,method=6)
make(1600,9).save('final/shaar-zohar-1600.webp',quality=88,method=6)
S0.save('final/shaar-symmetri-master.png',optimize=True)
