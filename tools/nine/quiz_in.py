import json, io, re, html
t=io.open(r'C:\Users\Owner\leokmei-girsa-nine\site\arakhin.html',encoding='utf-8').read()
i=t.index('const DATA=')+11
D=json.JSONDecoder().raw_decode(t[i:])[0]
TAG=re.compile(r'<[^>]+>')
out=io.open(r'C:\Users\Owner\leokmei-nine-work\quiz-in-arakhin-1.txt','w',encoding='utf-8')
n=0
for p in D['pages']:
    if (p.get('perek') or '').strip() and 'ראשון' not in (p.get('perek') or ''): 
        if n>5: break
    # פרק א = העמודים עד תחילת פרק שני
    pk=(p.get('perek') or '')
    if 'שני' in pk: break
    out.write('## %s\n' % p.get('daf'))
    for u in p['units']:
        if u.get('k') in ('u','m','dh','nose'):
            txt=html.unescape(TAG.sub('',u.get('a') or ''))
            for l in u.get('l',[]) or []:
                txt+=' '+html.unescape(TAG.sub('',l[1] if len(l)>1 else ''))
            if txt.strip(): out.write('%s|%s|%s\n' % (u.get('id'),u.get('k'),txt.strip()[:400]))
            n+=1
out.close(); print('units',n)
