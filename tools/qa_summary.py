# -*- coding: utf-8 -*-
"""qa_summary.py - סיכום results.json של mobile_qa.py לקובץ טקסט (UTF-8). שימוש: python tools/qa_summary.py <dir>"""
import json, sys, io, os
d = sys.argv[1]
r = json.load(io.open(os.path.join(d, 'results.json'), encoding='utf-8'))
out = []
tot = {}
for dev, pg in r.items():
    for p, m in pg.items():
        if 'fatal' in m:
            out.append('%s %s FATAL %s' % (dev, p, m['fatal'][-120:])); tot['fatal'] = tot.get('fatal', 0) + 1; continue
        bad = [k for k in ('hscroll', 'rail', 'touch', 'clip', 'lastline') if not m[k]['ok']]
        for k in bad: tot[k] = tot.get(k, 0) + 1
        if m.get('errors'): out.append('%s %s ERRORS %s' % (dev, p, m['errors'])); tot['errors'] = tot.get('errors', 0) + 1
        if bad:
            out.append('%s | %s | %s' % (dev, p, ','.join(bad)))
            if 'hscroll' in bad: out.append('    hscroll: %s' % m['hscroll'])
            if 'rail' in bad: out.append('    rail: %s' % m['rail']['overlaps'][:3])
            if 'touch' in bad: out.append('    small(%d): %s | crowd(%d): %s' % (m['touch']['smallCount'], m['touch']['small'][:5], m['touch']['crowdCount'], m['touch']['crowd'][:3]))
            if 'clip' in bad: out.append('    clip: %s' % m['clip']['items'][:4])
            if 'lastline' in bad: out.append('    lastline: %s' % m['lastline'])
out.insert(0, 'TOTAL ' + json.dumps(tot, ensure_ascii=False))
io.open(os.path.join(d, 'summary.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('TOTAL', tot)
