# -*- coding: utf-8 -*-
"""alts_build.py - בונה את data/alts/<slug>.json (נוסחאות חלופיות למנהל) מתוצר apply_ops.py c --alts.

    uv run python alts_build.py <alts-raw.json> <manifest.json> <פלט: data/alts/bekhorot.json>

כל נקודה: {id, daf, pub, variants:[{k, tag, text}]}. הנוסח המפורסם הוא תמיד אחד מהנוסחים (k=pub).
בדיקות: 2-4 נוסחים, כל נוסח שונה באמת מהאחרים (מרחק מילים), בלי מקף ארוך, בלי נוסח ריק.
"""
import sys, io, json, hashlib, re, difflib


def words(s):
    return re.findall(r'[א-ת0-9]+', re.sub(r'[֑-ׇ]', '', s.replace('⟦', '').replace('⟧', '')))


def distinct(a, b):
    """שונה באמת: לפחות 3 מילים שונות (לא החלפת מילה או שתיים)."""
    wa, wb = words(a), words(b)
    if not wa or not wb:
        return False
    sm = difflib.SequenceMatcher(None, wa, wb, autojunk=False)
    diff = 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag != 'equal':
            diff += max(i2 - i1, j2 - j1)
    return diff >= 3


def main(raw, manifest, out):
    items = json.load(io.open(raw, encoding='utf-8'))
    mf = {('d%02d' % m['unit']): m['daf'] for m in json.load(io.open(manifest, encoding='utf-8'))}
    res, rej = [], []
    seen = set()
    for it in items:
        pub = it.get('published_m') or it.get('published') or ''
        vs = [{'k': 'a', 'tag': it.get('ptag') or 'כפי שפורסם', 'text': pub}]
        for a in it.get('alts', []):
            t = (a.get('text') or '').strip()
            if not t or any(c in t for c in '–—―'):
                continue
            if all(distinct(t, v['text']) for v in vs):
                vs.append({'k': chr(ord('a') + len(vs)), 'tag': (a.get('tag') or '').strip() or 'חלופה', 'text': t})
        if len(vs) < 2:
            rej.append((it.get('i'), 'אין חלופה שונה באמת'))
            continue
        pid = 'b' + hashlib.md5(re.sub(r'\s+', ' ', it.get('published', '')).encode('utf-8')).hexdigest()[:8]
        if pid in seen:
            continue
        seen.add(pid)
        res.append({'id': pid, 'daf': mf.get(it.get('unit'), ''), 'pub0': 'a', 'variants': vs[:4], 'i': it.get('i')})
    res.sort(key=lambda x: x['i'] or 0)
    for r in res:
        r.pop('i', None)
    json.dump({'masechet': 'בכורות', 'range': 'כה. עד לה:', 'items': res}, io.open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('נקודות: %d | נדחו: %d' % (len(res), len(rej)))
    for x in rej[:20]:
        print(x)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main(*sys.argv[1:4])
