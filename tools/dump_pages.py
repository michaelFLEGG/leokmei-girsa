# -*- coding: utf-8 -*-
"""dump_pages.py - כלי עיון (26.11.2026): הדף כפי שהמנהל רואה אותו (הספר + השכבה שבשרת), כקובץ JSON - לניתוח מחוץ לדפדפן.
    python tools/dump_pages.py --only bava-batra --out _work/dump"""
import os, sys, io, json, argparse
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
ap = argparse.ArgumentParser()
ap.add_argument('--only', required=True)
ap.add_argument('--out', default='_work/dump')
a = ap.parse_args()
import mishna_check as MC, fold as F
os.makedirs(a.out, exist_ok=True)
for s in a.only.split(','):
    pages = MC.pages_of(s, True)
    io.open(os.path.join(a.out, s + '.pages.json'), 'w', encoding='utf-8').write(json.dumps(pages, ensure_ascii=False))
    srv = F.live_doc(s) or {}
    io.open(os.path.join(a.out, s + '.live.json'), 'w', encoding='utf-8').write(json.dumps(srv, ensure_ascii=False))
    print(s, len(pages), 'עמודים', len(srv.get('edits') or []), 'עריכות בשרת')
