# -*- coding: utf-8 -*-
"""סיכום קובץ פרופיל מעבד (cpuprofile של CDP): זמן עצמי וזמן כולל לכל פונקציה (שם:שורה)."""
import json, sys, collections
p = json.load(open(sys.argv[1]))
nodes = {n['id']: n for n in p['nodes']}
parent = {}
for n in p['nodes']:
    for c in n.get('children', []):
        parent[c] = n['id']
dt = collections.Counter()
samples, deltas = p['samples'], p['timeDeltas']
for s, d in zip(samples, deltas):
    dt[s] += d
def key(n):
    cf = n['callFrame']
    u = cf['url'].rsplit('/', 1)[-1].split('?')[0]
    return '%s %s:%d' % (cf['functionName'] or '(anon)', u, cf['lineNumber'] + 1)
self_t = collections.Counter(); tot_t = collections.Counter()
for nid, t in dt.items():
    self_t[key(nodes[nid])] += t
    seen = set(); x = nid
    while x is not None:
        k = key(nodes[x])
        if k not in seen:
            tot_t[k] += t; seen.add(k)
        x = parent.get(x)
N = int(sys.argv[2]) if len(sys.argv) > 2 else 30
print('== self (ms)')
for k, t in self_t.most_common(N): print('%8.0f  %s' % (t / 1000, k))
print('== total (ms)')
for k, t in tot_t.most_common(N): print('%8.0f  %s' % (t / 1000, k))
