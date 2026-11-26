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
    # בדיקה: הצעות סכם שהוכרעו "קבל"/"ערוך" - האם הנוסח החדש נמצא בדף (26.11.2026)
    import glob, re
    NIK = re.compile('[\u0591-\u05C7]')
    def N(t):
        t = re.sub(r'<[^>]+>', '', str(t)); t = NIK.sub('', t)
        t = re.sub(r'\{[^{}:\s]{1,4}:|\}', '', t); t = re.sub(r'\[[^\]]*\]', ' ', t)
        t = re.sub('["\'״׳]|&quot;|&#x27;', '', t)
        return re.sub(r'\s+', ' ', t).strip()
    import html as _h
    plain = ' | '.join(N(_h.unescape(str(l[1]))) for pg in pages for u in pg.get('units') or [] for l in (u.get('l') or []) if len(l) > 1)
    for f in sorted(glob.glob(os.path.join(here, '..', 'data', 'sakem', 'decisions', s + '-p*.json'))):
        D = json.load(io.open(f, encoding='utf-8'))
        jid = os.path.basename(f)[:-5]
        try:
            O = json.load(io.open(os.path.join(here, '..', 'data', 'sakem', 'out', jid + '.json'), encoding='utf-8'))
        except Exception:
            continue
        items = {x['iid']: x for x in O.get('items') or []}
        ok = miss = 0; ms = []
        for iid, d in (D.get('dec') or {}).items():
            act = d.get('act') if isinstance(d, dict) else d
            if act not in ('accept', 'edit') or iid not in items:
                continue
            it = items[iid]; txt = (d.get('final') if isinstance(d, dict) else '') or it.get('text') or ''
            ol = {N(x) for x in str(it.get('orig') or '').split('\n')}
            cand = [N(x) for x in txt.split('\n') if not x.startswith('[')]
            cand = [x for x in cand if len(x) > 20 and x not in ol][:4]
            if not cand:
                continue
            hit = sum(1 for x in cand if x in plain)
            if hit * 2 >= len(cand): ok += 1
            else: miss += 1; ms.append(iid)
        print('בדיקת החלה', jid, 'בדף', ok, 'חסר', miss, ' '.join(ms))
    if a.grep:
        import re
        U = [(pg.get('daf'), u) for pg in pages for u in pg.get('units') or []]
        txt = lambda u: (u.get('a') or '') + ' ' + ' '.join(str(l[1]) if len(l) > 1 else '' for l in u.get('l') or [])
        for i, (d, u) in enumerate(U):
            if re.search(a.grep, re.sub(r'<[^>]+>', '', txt(u))):
                print('==== דף', d)
                for d2, v in U[max(0, i - 2):i + 3]:
                    print(json.dumps({'id': v.get('id'), 'k': v.get('k'), 'a': v.get('a'), 'l': v.get('l'), 'mbw': v.get('mbw')}, ensure_ascii=False)[:900])
