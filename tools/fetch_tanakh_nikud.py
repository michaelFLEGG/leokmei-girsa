# -*- coding: utf-8 -*-
"""fetch_tanakh_nikud.py - נוסח המקרא מנוקד (בלי טעמים) מספריא, לניקוד פסוקים בגמרא.

המקור: "Miqra according to the Masorah", ספריא. נשמר ב-data/tanakh-nikud.json:
לכל פסוק [ספר, פרק, פסוק, [מילים מנוקדות]]. משמש רק את
nikud_mishna.apply_verses כמקור שני לפסוקים שאין להם רצף מנוקד בגמרא של
הדף. הטעמים מוסרים; הניקוד נשמר.

    uv run python tools/fetch_tanakh_nikud.py
"""
import os, sys, json, io, re, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fetch_tanakh as FT

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'tanakh-nikud.json')
CANT = re.compile('[֑-ֽֿ֯׀׃׆]')


def words(t):
    t = re.sub(r'<[^>]+>', '', t)
    t = re.sub(r'\{[^}]*\}', ' ', t)
    t = t.replace('־', ' ').replace('׀', ' ').replace('׃', ' ')
    t = CANT.sub('', t)
    return re.findall(r'[א-ת][א-תְ-ׇּׁׂ]*', t)


def book(name):
    d = FT.get(FT.API % name.replace(' ', '_'))
    if not d or not d.get('versions'):
        raise SystemExit('עצירה: לא התקבל הספר ' + name)
    out = []
    for ci, ch in enumerate(d['versions'][0]['text'], 1):
        for vi, v in enumerate(ch, 1):
            w = words(v)
            if w:
                out.append([name, ci, vi, w])
    return out


def main():
    with cf.ThreadPoolExecutor(4) as ex:
        res = list(ex.map(book, FT.BOOKS))
    rows = [r for b in res for r in b]
    io.open(OUT, 'w', encoding='utf-8').write(json.dumps(rows, ensure_ascii=False, separators=(',', ':')))
    print('פסוקים:', len(rows), 'מילים:', sum(len(r[3]) for r in rows))


if __name__ == '__main__':
    main()
