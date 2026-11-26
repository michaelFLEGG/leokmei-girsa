# -*- coding: utf-8 -*-
"""dump_pages.py - כלי עיון (26.11.2026): הדף כפי שהמנהל רואה אותו (הספר + השכבה שבשרת), כקובץ JSON - לניתוח מחוץ לדפדפן.
    python tools/dump_pages.py --only bava-batra --out _work/dump"""
import os, sys, io, json, argparse
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
ap = argparse.ArgumentParser()
ap.add_argument('--only', required=True)
ap.add_argument('--out', default='_work/dump')
ap.add_argument('--grep', default='', help='הדפסת היחידות סביב כל התאמה (ביומן ההרצה)')
a = ap.parse_args()
import mishna_check as MC, fold as F
os.makedirs(a.out, exist_ok=True)
for s in a.only.split(','):
    pages = MC.pages_of(s, True)
    io.open(os.path.join(a.out, s + '.pages.json'), 'w', encoding='utf-8').write(json.dumps(pages, ensure_ascii=False))
    srv = F.live_doc(s) or {}
    io.open(os.path.join(a.out, s + '.live.json'), 'w', encoding='utf-8').write(json.dumps(srv, ensure_ascii=False))
    print(s, len(pages), 'עמודים', len(srv.get('edits') or []), 'עריכות בשרת')
    if a.grep:
        import re
        U = [(pg.get('daf'), u) for pg in pages for u in pg.get('units') or []]
        txt = lambda u: (u.get('a') or '') + ' ' + ' '.join(str(l[1]) if len(l) > 1 else '' for l in u.get('l') or [])
        for i, (d, u) in enumerate(U):
            if re.search(a.grep, re.sub(r'<[^>]+>', '', txt(u))):
                print('==== דף', d)
                for d2, v in U[max(0, i - 2):i + 3]:
                    print(json.dumps({'id': v.get('id'), 'k': v.get('k'), 'a': v.get('a'), 'l': v.get('l'), 'mbw': v.get('mbw')}, ensure_ascii=False)[:900])
