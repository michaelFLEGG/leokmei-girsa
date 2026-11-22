import json,re,sys
caps=json.load(open('caps.json'))
def clean(s): return re.sub(r'[֑-ׇ]','',re.sub('<[^>]+>','',s))
def g(k,daf,pat,w=260):
    for p in caps[k]['packet']['pages']:
        if p['daf']!=daf: continue
        t=clean(' '.join(p['g']))
        for m in re.finditer(pat,t):
            print(f'[{daf} /{pat}/]', t[max(0,m.start()-w):m.end()+w]); print()
for a in sys.argv[1:]:
    k,d,pat=a.split('|',2); g(int(k),d,pat)
