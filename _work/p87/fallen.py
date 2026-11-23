# שורת משנה שנפלה מן התיבה: יחידת גמרא (בלי כותרת צד) בין שני חלקי אותה תיבה, ושורותיה הן לשון המשנה
import sys, json, os, re
sys.path.insert(0, 'tools'); sys.path.insert(0, '_work/p87')
import mishna_gaps as MG, mishna_guard as G
import run_mishna as RM
dd = sys.argv[1]
out = {}
for f in sorted(os.listdir(dd)):
    slug = f[:-5]; d = json.load(open(os.path.join(dd, f))); r = d['rows']
    chs = MG.canon(slug)
    if not chs: continue
    allS = []
    for ch in chs:
        for m in ch:
            allS += RM.keys_of(re.sub(r'\([^)]*\)', '', m))
    big = set(zip(allS, allS[1:]))
    res = []
    for i, x in enumerate(r):
        if x.get('box') or x.get('k') not in ('u',):
            continue
        # התיבה שלפני והתיבה שאחרי (מדלגים על ד"ה)
        a = i - 1
        while a >= 0 and r[a].get('k') == 'dh': a -= 1
        b = i + 1
        while b < len(r) and r[b].get('k') == 'dh': b += 1
        if a < 0 or b >= len(r) or not r[a].get('box') or not r[b].get('box'):
            continue
        if r[a]['title'].split(',')[0] != r[b]['title'].split(',')[0]:
            continue
        if any(it.get('anchor') and MG.plain(it['h']).strip() for it in x['items']):
            continue
        for it in x['items']:
            t = MG.plain(it['h']).strip()
            k = RM.keys_of(t)
            if len(k) < 2: continue
            c = sum(1 for p in zip(k, k[1:]) if p in big) / float(len(k) - 1)
            res.append({'ek': it['ek'], 'daf': x['daf'], 'cov': round(c, 2), 't': t, 'prev': r[a]['id'], 'next': r[b]['id'], 'title': r[a]['title'], 'row': x['id']})
    if res:
        out[slug] = res
        for z in res: print(slug, z['daf'], z['ek'], z['cov'], z['title'], '|', z['t'][:90])
json.dump(out, open('_work/p87/out/fallen.json', 'w'), ensure_ascii=False, indent=1)
