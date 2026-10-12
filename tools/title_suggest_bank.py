# -*- coding: utf-8 -*-
"""title_suggest_bank.py - הרכבת שכבת ההצעות המוכנות (12.10.2026).

קורא את תוצאות ההרצה המרוכזת (out/cNN.json, מפתחות i) ואת מפות החבילות (chunks/cNN.map.json)
וכותב data/titlesug/<מסכת>.json: {מפתח-מקום: [שש הצעות]}. כל הצעה עוברת ניקוי ובדיקה:
  - מקף ארוך (U+2013/U+2014) הופך למקף רגיל; ניקוד נמחק; רווחים מכווצים; נקודה בסוף נמחקת;
  - הצעה ריקה, או ארוכה מ-8 מילים, או כפולה - נזרקת ונרשמת בדוח.
אם נותרו פחות משלוש הצעות תקינות לפריט - הפריט אינו נכנס לשכבה (השכבה החיה תענה).
    uv run python tools/title_suggest_bank.py --work _work/titlesug --out data/titlesug
"""
import os, re, io, sys, json, glob, argparse

NIKUD = re.compile(r'[֑-ׇ]')


def clean(t):
    t = str(t or '')
    t = t.replace('–', '-').replace('—', '-').replace('־', '-')
    t = NIKUD.sub('', t)
    t = t.replace('״', '"').replace('׳', "'")      # גרשיים עבריים -> ASCII, כמו בכותרות הקיימות
    t = re.sub(r'\s+', ' ', t).strip()
    t = re.sub(r'[.:;,]+$', '', t).strip()
    return t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--work', required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    banks, rep = {}, {'items': 0, 'kept': 0, 'short': 0, 'dropped_sugs': 0, 'missing': 0, 'chunks': 0}
    for mp in sorted(glob.glob(os.path.join(a.work, 'chunks', 'c??.map.json'))):
        cid = os.path.basename(mp)[:3]
        op = os.path.join(a.work, 'out', cid + '.json')
        m = json.load(io.open(mp, encoding='utf-8'))
        if not os.path.exists(op):
            rep['missing'] += len(m)
            print('חסרה תוצאה לחבילה', cid, '(%d פריטים)' % len(m))
            continue
        o = json.load(io.open(op, encoding='utf-8'))
        cx = json.load(io.open(os.path.join(a.work, 'chunks', cid + '.json'), encoding='utf-8'))
        ctxlen = {it['i']: len(it['ctx']) for it in cx['items']}
        rep['chunks'] += 1
        for i, ent in enumerate(m):
            rep['items'] += 1
            if ctxlen.get(i, 0) < 40:       # קטע קצר מדי (למשל ציון דף בלבד): אין על מה להציע, השכבה החיה תענה
                rep['tiny'] = rep.get('tiny', 0) + 1
                continue
            sug = o.get(str(i)) or []
            seen, good = set(), []
            for s in sug:
                c = clean(s)
                if not c or len(c.split()) > 8 or c in seen:
                    rep['dropped_sugs'] += 1
                    continue
                seen.add(c)
                good.append(c)
            if len(good) < 3:
                rep['short'] += 1
                continue
            banks.setdefault(ent['slug'], {})[ent['key']] = good[:6]
            rep['kept'] += 1
    for slug, b in banks.items():
        io.open(os.path.join(a.out, slug + '.json'), 'w', encoding='utf-8').write(
            json.dumps(b, ensure_ascii=False, separators=(',', ':')))
    print(json.dumps(rep, ensure_ascii=False))
    print('מסכתות:', len(banks))


if __name__ == '__main__':
    main()
