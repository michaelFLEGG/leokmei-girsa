# -*- coding: utf-8 -*-
"""alts_build.py - בונה את data/alts/<slug>.json (נוסחאות חלופיות למנהל) מתוצר apply_ops.py c --alts.

    uv run python alts_build.py <alts-raw.json> <manifest.json> <פלט: data/alts/bekhorot.json>

כל נקודה: {id, daf, pub, variants:[{k, tag, text}]}. הנוסח המפורסם הוא תמיד אחד מהנוסחים (k=pub).
בדיקות: 2-4 נוסחים, כל נוסח שונה באמת מהאחרים (מרחק מילים), בלי מקף ארוך, בלי נוסח ריק.
פרומפט 26 (8.11.2026, הכרעת המחבר): חלופה שמוסיפה ארמית על פני הנוסח המפורסם - מוסרת (לעולם לא ארמית במקום
לשון הקודש). החלופות מוצגות כשהבהירה קודמת למהודקת. ונוסח מפורסם "מהודק ביותר" כשיש חלופה בהירה - עצירה רועשת:
ברירת המחדל היא הבהיר, ואת הנוסח המפורסם קובע המנוע (engine-c.md), לא כאן.
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


# אותה רשימה כמו SKC.aramNew (tools/sakem_core.js): מילים ארמיות במילות הקישור וההסבר
ARAM = set('''איכא ליכא הוי הואי נמי הכי היכי מיהו דהא תרי תרתי קמא שקיל שקלה שקלי שדי שדיא שדו אמאי מאי היכא לאו אית ליה ביה בהו
להו להון דידיה נפשיה איהו איהי הוה הות קאמר קתני טייעא גמלא מסא בריש תנורא זימנא זימני השתא מיבעיא איפכא כוותיה כוותייהו
תלינן חדא לאיתויי אתי אתא אזל אזיל הכא התם אמינא ניהו מיניה מינה גביה בהדי כוליה טובא פורתא מנלן ומפרשא אתריה אתרא'''.split())


def aram_count(s):
    c = {}
    for w in words(s):
        k = w if w in ARAM else (w[1:] if len(w) > 2 and w[0] in 'ודשהבלכ' and w[1:] in ARAM else None)
        if k:
            c[k] = c.get(k, 0) + 1
    return c


def adds_aram(base, t):
    a, b = aram_count(base), aram_count(t)
    return [k for k in b if b[k] > a.get(k, 0)]


CLEAR = re.compile('בהיר|מפורש|עם הסבר|עם הצעדים|עברית')
TIGHT = re.compile('^מהודק')


def main(raw, manifest, out):
    items = json.load(io.open(raw, encoding='utf-8'))
    mf = {('d%02d' % m['unit']): m['daf'] for m in json.load(io.open(manifest, encoding='utf-8'))}
    res, rej, loud = [], [], []
    seen = set()
    for it in items:
        pub = it.get('published_m') or it.get('published') or ''
        vs = [{'k': 'a', 'tag': it.get('ptag') or 'כפי שפורסם', 'text': pub}]
        for a in it.get('alts', []):
            t = (a.get('text') or '').strip()
            if not t or any(c in t for c in '–—―'):
                continue
            if adds_aram(pub, t) or re.search('ארמית', a.get('tag') or ''):
                rej.append((it.get('i'), 'חלופה ארמית במקום לשון הקודש הוסרה: ' + ', '.join(adds_aram(pub, t))))
                continue
            if all(distinct(t, v['text']) for v in vs):
                vs.append({'k': chr(ord('a') + len(vs)), 'tag': (a.get('tag') or '').strip() or 'חלופה', 'text': t})
        # הבהירה קודמת למהודקת בתצוגה (הנוסח המפורסם נשאר a)
        vs = vs[:1] + sorted(vs[1:], key=lambda v: 0 if CLEAR.search(v['tag']) else (2 if TIGHT.search(v['tag']) else 1))
        for i, v in enumerate(vs):
            v['k'] = chr(ord('a') + i)
        if TIGHT.search(vs[0]['tag']) and any(CLEAR.search(v['tag']) for v in vs[1:]):
            loud.append((it.get('i'), 'הנוסח המפורסם מהודק כשיש חלופה בהירה - ברירת המחדל צריכה להיות הבהירה'))
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
    if loud:
        print('עצירה (הקובץ לא נכתב): %d נקודות שבהן פורסם המהודק במקום הבהיר:' % len(loud))
        for x in loud[:20]:
            print(x)
        sys.exit(2)
    json.dump({'masechet': 'בכורות', 'range': 'כה. עד לה:', 'items': res}, io.open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('נקודות: %d | נדחו: %d' % (len(res), len(rej)))
    for x in rej[:20]:
        print(x)



if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main(*sys.argv[1:4])
