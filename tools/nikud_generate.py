# -*- coding: utf-8 -*-
"""nikud_generate.py - ניקוד משוער למילים במשנה שאין להן מקבילה במקור.

הניקוד מן הגמרא (nikud_mishna) מכסה את רוב המשנה. מה שנשאר - מילים
שאין להן מקבילה (קיצור של בעל הפרויקט, כתיב שונה מאוד, משנה שאינה
מצוטטת בגמרא) - מנוקד כאן בידי מנקד הקוד הפתוח והחינמי של דיקטה
(nakdan, ז'אנר "rabbinic"), פסקה שלמה בכל פעם, כדי שהניקוד ייבחר לפי
ההקשר ולא לפי המילה לבדה.

הפלט נשמר במאגר: data/nikud-nakdan/<מסכת>.json, מפתח = נוסח הפסקה (טקסט
בלבד), ערך = רשימת המילים המנוקדות לפי סדרן. הבנייה אינה פונה לרשת.
התוצאה נבדקת פעמיים: אם הנוסח אחרי הסרת הניקוד אינו זהה לנוסח שנשלח -
הפסקה אינה נשמרת, ונאמרת. הבנייה מוסיפה ניקוד רק למילה שאותיותיה זהות,
וכל מילה כזאת מסומנת "משוער" (קו תחתי אפור למנהל בלבד).

מורצים מחדש כשהנוסח בוורד משתנה: פסקה ששונתה אינה נמצאת במפתח, ונשארת
בלי ניקוד משוער עד הריצה הבאה.

    uv run python tools/nikud_generate.py            # כל המסכתות, מן האתר הבנוי
    uv run python tools/nikud_generate.py sukkah
"""
import os, sys, re, json, glob, time, io, urllib.request, concurrent.futures

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from nikud_mishna import WORD, NIKUD, TAGS

OUT = os.path.join(ROOT, 'data', 'nikud-nakdan')
URLS = ['https://nakdan-4-0.loadbalancer.dicta.org.il/api',
        'https://nakdan-3-0.loadbalancer.dicta.org.il/api']


def plain(h):
    import html as _h
    return _h.unescape(TAGS.sub('', h or ''))


def bare_words_in(text):
    """אינדקסים של מילים בלי ניקוד שמותר לנקד: לא ראשי תיבות, לא בסוגריים."""
    t = re.sub(r'\([^)]*\)', lambda m: ' ' * len(m.group(0)), text)
    t = re.sub(r'\[[^\]]*\]', lambda m: ' ' * len(m.group(0)), t)
    out = []
    for i, m in enumerate(WORD.finditer(text)):
        pre = t[m.start() - 1:m.start()] if m.start() else ''
        post = t[m.end():m.end() + 1]
        if (pre and pre in '"\'׳״') or (post and post in '"\'׳״'):
            continue
        if t[m.start():m.end()].strip() == '':
            continue
        out.append(i)
    return out


def call(text):
    body = json.dumps({'task': 'nakdan', 'data': text, 'genre': 'rabbinic', 'addmorph': True,
                       'keepmetagim': False, 'matchpartial': True, 'keepqq': False,
                       'apiKey': '', 'useTokenization': True}).encode()
    last = None
    for n in range(5):
        for u in URLS:
            try:
                r = urllib.request.urlopen(urllib.request.Request(
                    u, body, {'Content-Type': 'text/plain;charset=utf-8', 'User-Agent': 'Mozilla/5.0'}), timeout=60)
                return json.loads(r.read())
            except Exception as e:
                last = e
                time.sleep(1 + n)
    raise RuntimeError(repr(last))


def vocalize(text):
    d = call(text)
    out = []
    for it in d.get('data') or []:
        nk = it.get('nakdan') if isinstance(it, dict) else None
        if nk is None:
            out.append(it.get('sep', '') if isinstance(it, dict) else '')
            continue
        opts = nk.get('options') or []
        w = opts[0]['w'] if opts else nk.get('word', '')
        if isinstance(w, list):
            w = w[0]
        out.append(w.replace('|', ''))
    return ''.join(out)


def align(text, voc):
    """המילים המנוקדות לפי סדר מילות הנוסח שלו. המנקד מתקן לעתים כתיב
    (סוכה -> סכה), ולכן היישור הוא לפי שלד האותיות, והניקוד עובר לכתיב
    שלו בלבד (nikud_mishna.transfer). מילה שלא נמצאה לה התאמה בטוחה
    נשארת ריקה, ולעולם אינה מנוחשת."""
    import difflib
    from nikud_mishna import skel, transfer, letters
    mine = WORD.findall(text)
    theirs = WORD.findall(voc)
    sm = difflib.SequenceMatcher(None, [skel(w) for w in mine], [skel(w) for w in theirs],
                                 autojunk=False)
    out = [''] * len(mine)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag != 'equal':
            continue
        for k in range(i2 - i1):
            w, s = mine[i1 + k], theirs[j1 + k]
            if NIKUD.search(w) or not NIKUD.search(s):
                continue
            if letters(w) == letters(s):
                out[i1 + k] = s
            else:
                t = transfer(w, s)
                if t is not None and letters(t) == letters(w):
                    out[i1 + k] = t
    return out


def load_data(slug):
    s = io.open(os.path.join(ROOT, 'site', slug + '.html'), encoding='utf-8').read()
    i = s.find('const DATA=')
    d, _ = json.JSONDecoder().raw_decode(s[i + 11:])
    return d


def run(slug, log=print):
    d = load_data(slug)
    todo = {}
    for p in d['pages']:
        for u in p['units']:
            if u.get('k') != 'm':
                continue
            lv = u.get('lv') or u['l']
            for (c, h), (c0, h0) in zip(lv, u['l']):
                if bare_words_in(plain(h)) and any(
                        not NIKUD.search(w) for w in WORD.findall(plain(h))):
                    todo[plain(h0)] = 1
    path = os.path.join(OUT, slug + '.json')
    have = json.load(io.open(path, encoding='utf-8')) if os.path.exists(path) else {}
    todo = [t for t in todo if t not in have]
    log('%s: %d פסקאות לניקוד (%d כבר במאגר)' % (slug, len(todo), len(have)))
    bad = 0

    def one(t):
        return t, align(t, vocalize(t))

    with concurrent.futures.ThreadPoolExecutor(5) as ex:
        for t, words in ex.map(one, todo):
            if words is None:
                bad += 1
                continue
            have[t] = words
    os.makedirs(OUT, exist_ok=True)
    io.open(path, 'w', encoding='utf-8').write(json.dumps(have, ensure_ascii=False))
    log('   נשמרו %d פסקאות; %d לא נשמרו (הנוסח חזר שונה)' % (len(have), bad))
    return len(have), bad


def main():
    names = sys.argv[1:] or sorted(os.path.basename(f)[:-5] for f in glob.glob(os.path.join(ROOT, 'site', '*.html'))
                                   if not f.endswith(('-hagaha.html', 'index.html', 'mekorot.html')))
    tb = 0
    for n in names:
        try:
            tb += run(n)[1]
        except Exception as e:
            print('נכשל', n, repr(e))
    print('סך הכל פסקאות שלא נשמרו:', tb)


if __name__ == '__main__':
    main()
