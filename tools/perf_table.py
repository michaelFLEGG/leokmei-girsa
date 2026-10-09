# -*- coding: utf-8 -*-
"""perf_table.py - טבלת לפני/אחרי מקובצי perf_probe.py. שימוש: python tools/perf_table.py before.json after.json table.md"""
import json, sys, io
b = json.load(io.open(sys.argv[1], encoding='utf-8')); a = json.load(io.open(sys.argv[2], encoding='utf-8'))
def f(v, unit=''):
    return '-' if v is None else ('%s%s' % (v, unit))
def kb(v): return '-' if v is None else '%d' % round(v / 1024)
rows = ['| מסך ודף | מדד | לפני | אחרי |', '|---|---|---:|---:|']
for k in b:
    x, y = b[k], a.get(k, {})
    mode, page = k.split(' | ')
    mode = 'טלפון (4G איטי)' if mode == 'mobile' else 'מחשב'
    for lab, key, fn in [('FCP (מילישניות)', 'fcp', f), ('LCP (מילישניות)', 'lcp', f), ('TBT (מילישניות)', 'tbt', f), ('CLS', 'cls', f),
                         ('משקל כולל (KB, דחוס)', 'transfer', kb), ('בקשות', 'requests', f), ('כניסה שנייה: FCP', 'warm_fcp', f), ('כניסה שנייה: LCP', 'warm_lcp', f)]:
        rows.append('| %s · %s | %s | %s | %s |' % (mode, page, lab, fn(x.get(key)), fn(y.get(key))))
io.open(sys.argv[3], 'w', encoding='utf-8').write('\n'.join(rows))
