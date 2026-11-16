import sys, os, pickle, json, tempfile, re
sys.path.insert(0, '/home/user/leokmei-girsa/tools'); sys.path.insert(0, '/tmp/claude-0/sh')
os.environ.setdefault('LG_DRIVE', tempfile.mkdtemp())
exec(open('final2.py').read().split("live = json.load")[0])
live = json.load(open('live-shabbat.json'))['doc']
rep, d, gone, raw = C.layer('shabbat', 'שבת', live)
PS = pickle.load(open(sys.argv[2] if len(sys.argv) > 2 else 'persync.pkl', 'rb')); PI = pickle.load(open('page_items.pkl', 'rb'))
newdocx = sys.argv[1]
conv = {n for n, _ in PS['ok']}
alld = [x for x, _ in PI]
rev_daf = {alld[i] for i in range(len(alld)) if i not in conv}
W = pickle.load(open('where.pkl', 'rb'))
CL = pickle.load(open('cls-640d2cbb.pkl', 'rb'))
sig = lambda e: (C.ekey(e), e.get('t'))
lostA = {sig(e) for e in CL['lost']}
remain, taken = [], []
for e in raw['edits']:
    s = sig(e)
    if s in lostA: remain.append(e); continue
    if s in W and W[s] is not None:
        (taken if (W[s] in conv and e.get('daf') not in rev_daf) else remain).append(e); continue
    (remain if e.get('daf') in rev_daf else taken).append(e)
print('remain', len(remain), 'taken', len(taken))
A = pickle.load(open('AB.pkl', 'rb'))['A']; T = pickle.load(open('target_pages.pkl', 'rb'))
Bc, _ = views.pages(newdocx, 'shabbat', 'שבת', dict(raw, edits=remain)); Bp = Bc['pages']
badT = [(i, T[i]['daf'], 'conv' if i in conv else 'rev') for i in range(len(T)) if norm([T[i]]) != norm([Bp[i]])]
badA = [(i, A[i]['daf']) for i in range(len(A)) if norm([A[i]]) != norm([Bp[i]])]
print('vs target', len(badT), badT); print('vs admin', len(badA))
print('stat', {k: Bc.get('stat', {}).get(k) for k in ('n','done','taken','lost')})
pickle.dump({'remain': remain, 'taken': taken, 'badT': badT, 'badA': badA, 'B': Bp}, open('final3.pkl', 'wb'))
