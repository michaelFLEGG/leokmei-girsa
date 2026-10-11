# -*- coding: utf-8 -*-
"""fetch_tanakh.py - נוסח המקרא (כתיב בלבד, בלי ניקוד וטעמים) מספריא, לזיהוי פסוקים בגמרא.

המקור: "Miqra according to the Masorah", ספריא. הנתונים נשמרים ב-
data/tanakh-ktiv.json: לכל פסוק מראה מקום והמילים (כתיב בלבד). משמש רק
את בדיקת הפסוקים שלא סומנו (tools/verses_check.py); אינו מוצג באתר.

    uv run python tools/fetch_tanakh.py
"""
import os, sys, json, io, re, time, urllib.request, concurrent.futures as cf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'tanakh-ktiv.json')
BOOKS = ['Genesis','Exodus','Leviticus','Numbers','Deuteronomy','Joshua','Judges','I Samuel','II Samuel',
         'I Kings','II Kings','Isaiah','Jeremiah','Ezekiel','Hosea','Joel','Amos','Obadiah','Jonah','Micah',
         'Nahum','Habakkuk','Zephaniah','Haggai','Zechariah','Malachi','Psalms','Proverbs','Job',
         'Song of Songs','Ruth','Lamentations','Ecclesiastes','Esther','Daniel','Ezra','Nehemiah',
         'I Chronicles','II Chronicles']
API = 'https://www.sefaria.org/api/v3/texts/%s?version=hebrew%%7CMiqra%%20according%%20to%%20the%%20Masorah'


def strip(t):
    t = re.sub(r'<[^>]+>', '', t)
    t = t.replace('־', ' ').replace('׀', ' ').replace('׃', ' ')
    t = re.sub(r'[֑-ׇ]', '', t)
    t = re.sub(r'\{[^}]*\}', ' ', t)           # {פ} {ס}
    t = re.sub(r'[^א-ת ]', ' ', t)
    return t.split()


def get(url, tries=4):
    for i in range(tries):
        try:
            return json.loads(urllib.request.urlopen(url, timeout=60).read())
        except Exception as e:
            time.sleep(2 * (i + 1))
    return None


def book(name):
    d = get(API % name.replace(' ', '_'))
    if not d:
        raise SystemExit('עצירה: לא התקבל הספר ' + name)
    vs = d.get('versions') or []
    if not vs:
        raise SystemExit('עצירה: אין נוסח עברי לספר ' + name)
    txt = vs[0]['text']
    out = []
    for ci, ch in enumerate(txt, 1):
        for vi, v in enumerate(ch, 1):
            w = strip(v)
            if w:
                out.append([name, ci, vi, w])
    return out


def main():
    with cf.ThreadPoolExecutor(4) as ex:
        res = list(ex.map(book, BOOKS))
    rows = [r for b in res for r in b]
    io.open(OUT, 'w', encoding='utf-8').write(json.dumps(rows, ensure_ascii=False, separators=(',', ':')))
    print('פסוקים:', len(rows), 'מילים:', sum(len(r[3]) for r in rows))


if __name__ == '__main__':
    main()
