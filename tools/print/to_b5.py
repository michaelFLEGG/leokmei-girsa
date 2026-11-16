# פרומפט 48 (16.11.2026): הקטנה וקטורית של קובץ A4 ל-B5 (176x250) כגוש אחד, אותה שבירת שורות. יחס אחד לכל העמודים לפי מלבן הדיו המשותף של עמודי הגוף; ימין 10 מ"מ לפחות (בפועל 55% מהמרווח), למעלה ולמטה 9. שימוש: to_b5.py <a4.pdf> <b5.pdf> [כותרת]
import pymupdf as fitz, sys, json
MM=72/25.4
src_path,out_path=sys.argv[1],sys.argv[2]
src=fitz.open(src_path)
def ink(p):
    dpi=100; pm=p.get_pixmap(dpi=dpi,colorspace=fitz.csGRAY); w,h=pm.width,pm.height; b=pm.samples
    xs=[];ys=[]
    rows=[y for y in range(h) if min(b[y*w:(y+1)*w])<240]
    if not rows: return fitz.Rect()
    cols=[x for x in range(w) if min(b[x::w])<240]
    k=72/dpi
    return fitz.Rect(cols[0]*k,rows[0]*k,(cols[-1]+1)*k,(rows[-1]+1)*k)
U=fitz.Rect()
for i in range(3,src.page_count):
    U|=ink(src[i])
W,H=176*MM,250*MM
s=min((W-18*MM)/U.width,(H-18*MM)/U.height)
free=W-s*U.width; right=max(10*MM,free*0.55); left=free-right
top=(H-s*U.height)/2
out=fitz.open()
for i in range(src.page_count):
    pg=out.new_page(width=W,height=H)
    pr=src[i].rect
    x0=left-(U.x0)*s; y0=top-(U.y0)*s
    pg.show_pdf_page(fitz.Rect(x0,y0,x0+pr.width*s,y0+pr.height*s),src,i)
out.set_metadata({**{k:v for k,v in src.metadata.items() if v}, 'title':sys.argv[3] if len(sys.argv)>3 else ''})
out.save(out_path,garbage=3,deflate=True)
info={'ratio':round(s,4),'margins_mm':{'right':round(right/MM,1),'left':round(left/MM,1),'top':round(top/MM,1),'bottom':round((H-top-s*U.height)/MM,1)},'pages':out.page_count}
info['ink_mm_on_a4']=[round(v/MM,1) for v in U]
print(json.dumps(info,ensure_ascii=False))
