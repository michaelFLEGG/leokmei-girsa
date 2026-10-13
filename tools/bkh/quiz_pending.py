# -*- coding: utf-8 -*-
"""quiz_pending.py - מאחד את quiz-out.json של כל היחידות ל-data/quiz/pending-bekhorot.json (סטטוס "ממתין").

    uv run python quiz_pending.py <תיקיית-יחידות> <פלט.json>

השאלות אינן מוצגות ללומדים: הבנייה (quiz_build.run) מוציאה אותן לתור האישור של המנהל בלבד.
בדיקות מבניות קשיחות: 4 תשובות שונות, ראשונה נכונה, רמה 1-3, דף בתבנית 'כה ע"א', בלי מקף ארוך, בלי כפילות.
"""
import sys, io, os, re, json, glob, hashlib
DAF_RE = re.compile(r'^[א-ת]{1,3} ע"[אב]$')


def tid(s):
    return hashlib.sha1(s.encode('utf-8')).hexdigest()[:8]


def main(units, out):
    items, rej, seen = [], [], set()
    files = []
    for dd in sorted(glob.glob(os.path.join(units, 'd*'))):
        fin = os.path.join(dd, 'quiz-final.json')
        files.append(fin if os.path.exists(fin) else os.path.join(dd, 'quiz-out.json'))
    for f in files:
        if not os.path.exists(f):
            continue
        d = json.load(io.open(f, encoding='utf-8'))
        daf = d.get('daf') or ''
        for n, r in enumerate(d.get('q', [])):
            o = r.get('o') or []
            q = re.sub(r'\s+', ' ', str(r.get('q', ''))).strip()
            why = None
            if not (isinstance(o, list) and len(o) == 4 and len(set(x.strip() for x in o)) == 4 and all(isinstance(x, str) and x.strip() for x in o)):
                why = 'לא 4 תשובות שונות'
            elif r.get('lvl') not in (1, 2, 3):
                why = 'רמה לא תקינה'
            elif not DAF_RE.match(str(r.get('d', ''))):
                why = 'דף לא בתבנית'
            elif len(q) < 12:
                why = 'שאלה קצרה'
            elif any(c in (q + ' '.join(o) + str(r.get('x', ''))) for c in '–—―'):
                why = 'מקף ארוך'
            elif q in seen:
                why = 'כפילות'
            if why:
                rej.append((os.path.basename(os.path.dirname(f)), n, why)); continue
            seen.add(q)
            items.append({'i': 'r:bekhorot:' + tid(q), 'p': int(r.get('p') or 0), 'd': r['d'], 'daf': daf, 'lvl': r['lvl'], 'q': q,
                          'o': [x.strip() for x in o], 'a': 0, 'x': str(r.get('x', '')).strip(), 'st': 'ממתין'})
    json.dump({'slug': 'bekhorot', 'status': 'ממתין', 'style': 'claude-13.10.2026', 'items': items},
              io.open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    by = {}
    for x in items:
        by[x['daf']] = by.get(x['daf'], 0) + 1
    print('שאלות: %d | נפסלו: %d' % (len(items), len(rej)), by)
    for x in rej:
        print('נפסלה', x)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main(os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]))
