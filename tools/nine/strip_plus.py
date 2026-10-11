import sys, re, os
sys.path.insert(0,r'C:\Users\Owner\leokmei-girsa-nine\engine\laukmi-engine'); sys.path.insert(0,r'C:\Users\Owner\leokmei-girsa-nine\tools')
import laukmi_mech
from laukmi_mech import Doc, text_map, tracked_replace
laukmi_mech.AUTHOR='קלוד'
path, out, styles = sys.argv[1], sys.argv[2], sys.argv[3].split(',')
d=Doc(path); n=0
for p in list(d.paragraphs()):
    if d.pstyle(p) not in styles: continue
    for _ in range(10):
        t,_s=text_map(p)
        if t.count('+')==0 or re.search(r'\d\s*\+|\+\s*\d',t): break
        i=t.index('+')
        if not tracked_replace(d,p,i,i+1,''): break
        n+=1
d.save(out); print('הוסרו',n)
