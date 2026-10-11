import re,sys
MX=296.3  # ציר המראה בין האריה השמאלי לימני
def bbox(nums):
    xs=nums[0::2]; ys=nums[1::2]; return min(xs),min(ys),max(xs),max(ys)
def near(bb,t,eps=.15): return all(abs(a-b)<eps for a,b in zip(bb,t))
def mirror_bb(t): return (MX-t[2],t[1],MX-t[0],t[3])
# עיוותים בקואורדינטות האריה השמאלי; לימני - במראה
def w_mouth(x,y):   # קצה הפה העולה (החיוך) יורד ומתיישר, ומעט למטה - פה סגור ונחוש
    if x>63.6:
        t=min(1,(x-62.8)/3.3); y+=1.05*t**1.6
    return x,y
def w_nose(x,y):    # אף רחב וכבד יותר בתחתיתו
    if y>64.3:
        t=min(1,(y-64.3)/1.8); x=62.05+(x-62.05)*(1+0.16*t); y+=0.12*t
    return x,y
def w_lip(x,y):     # שפה עליונה מעט מטה יחד עם האף
    return x,y+0.12
def w_brow_in(x,y): # קצה העפעף הפנימי יורד מעט - מבט חמור
    if x>61.6: y+=0.38*min(1,(x-61.6)/1.6)
    return x,y
def w_brow_out(x,y):
    if x>59.2: y+=0.30*min(1,(x-59.2)/0.9)
    return x,y
targets={ (58.8,64.7,66.1,68.2):w_mouth, (60.1,62.6,64.0,66.1):w_nose,
          (59.8,66.1,63.1,67.1):w_lip, (62.2,60.0,67.0,62.5):w_brow_in, (57.8,60.0,60.1,61.8):w_brow_out }
def apply(svgtext):
    out=[];n=0
    def fix(m):
        nonlocal n
        d=m.group(2); nums=[float(v) for v in re.findall(r'-?\d+\.?\d*',d)]
        if len(nums)<4 or len(nums)%2: return m.group(0)
        bb=bbox(nums)
        for t,f in targets.items():
            for side in ('L','R'):
                tt=t if side=='L' else mirror_bb(t)
                if near(bb,tt):
                    n+=1
                    it=iter(re.split(r'(-?\d+\.?\d*)',d)); parts=re.split(r'(-?\d+\.?\d*)',d)
                    vals=[float(p) for p in parts[1::2]]
                    nv=[]
                    for i in range(0,len(vals),2):
                        x,y=vals[i],vals[i+1]
                        if side=='R': x=MX-x
                        x,y=f(x,y)
                        if side=='R': x=MX-x
                        nv+= [x,y]
                    parts[1::2]=['%.2f'%v for v in nv]
                    return m.group(1)+''.join(parts)+m.group(3)
        return m.group(0)
    res=re.sub(r'(<path fill-rule="nonzero"[^>]*? d=")([^"]*)(")',fix,svgtext)
    return res,n
for src,dst in [('gate_clean.svg','gate_lions.svg'),('shaar-zahav.svg','shaar-zahav-lions.svg'),('shaar-currentColor.svg','shaar-currentColor-lions.svg')]:
    s=open(src,encoding='utf8').read(); r,n=apply(s); open(dst,'w',encoding='utf8').write(r); print(dst,n)
