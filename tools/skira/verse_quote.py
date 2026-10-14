# -*- coding: utf-8 -*-
"""verse_quote.py - הכרעת "גרש בגמרא": פתיחת ציטוט של פסוק, או ראשי תיבות (14.10.2026).

הכלל (מנת "סקירה חכמה", חלק א): כל פסוק או חלק פסוק המצוטט בטקסט נעטף בגרש לפני
המילה הראשונה ובגרש אחרי המילה האחרונה. כשיש אות שימוש לפני הציטוט (ד, ו, ב, כ, ל,
מ, ש, ה) - הגרש הפותח בא אחריה: ד'כל חרם בישראל לך יהיה'.

ההכרעה היא קוד בלבד, בלי מודל: התאמה לנוסח המקרא (data/tanakh-ktiv.json, דרך
verses_check) של רצף שתי מילים לפחות, בשלד אותיות (בלי ניקוד, ו/י, סופיות, ה'=יהוה).

    classify(text, mark) -> dict:
      kind 'closed'      הציטוט שלם: פתיחה וסגירה. אין מה לתקן ואין להציג הערה.
      kind 'open_only'   יש גרש פותח לפסוק ואין סוגר. fix: הוספת גרש סוגר.
      kind 'close_only'  יש גרש סוגר על סוף פסוק ואין פותח. fix: הוספת גרש פותח.
      kind 'unknown'     לא פסוק ברצף מאומת: נשאר הערה רגילה.
"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)
import verses_check as VC

HEB = 'א-ת'
NIK = VC.NIK
USE = 'דובכלמשה'            # אותיות שימוש שיכולות לקדם ציטוט
MIN_LETTERS = 6              # רצף של שתי מילים נחשב רק מעל מספר אותיות זה
MIN_WORDS_FREE = 2


def apply(findings):
    """מעבד את רשימת הממצאים של פרק. מחזיר (ממצאים, יומן).
    ציטוט שלם: יוצא מהרשימה ונרשם ביומן. גרש חסר במקום מוכח: נשאר כממצא עם auto=1 והחלפה
    מפורשת (הממשק מחיל אותו לבד ורושם ביומן). כל השאר נשאר הערה רגילה."""
    kept, log = [], []
    for f in findings:
        if f.get('det') != 'abbr':
            kept.append(f)
            continue
        r = classify(f.get('text') or '', f.get('mark') or '')
        k = r['kind']
        if k == 'closed':
            log.append({'id': f.get('id'), 'det': 'abbr', 'what': 'ציטוט שלם', 'mark': f.get('mark', ''),
                        'daf': f.get('daf', ''), 'ctx': f.get('context', ''), 'basis': r.get('basis', 'verse')})
            continue
        if k in ('open_only', 'close_only') and r.get('sure'):
            f = dict(f)
            f['mark'] = r['x']
            f['fix'] = r['x'] + ' ⟵ ' + r['y']
            f['note'] = 'ציטוט פסוק ' + ('בלי גרש סוגר' if k == 'open_only' else 'בלי גרש פותח') + ': הגרש הושלם לפי נוסח המקרא'
            f['conf'] = 'גבוה'
            f['auto'] = 1
            try:
                import hagaha as HG
                f['context'] = HG.ctx_of(f.get('text') or '', r['x'])
            except Exception:
                pass
        kept.append(f)
    return kept, log


def _tok(text):
    return VC._tokens(text)


def _run_from(toks, i):
    """הרצף הארוך ביותר שמתחיל במילה i. מחזיר (אורך, אותיות, פסוק, מקום)."""
    k, vi, p = VC._longest(toks, i)
    if k < MIN_WORDS_FREE:
        return 0, 0, None, None
    letters = VC._letters(toks, i, k)
    if k == 2 and (letters < MIN_LETTERS + 2 or not VC._rare(toks, i)):
        return 0, 0, None, None
    if letters < MIN_LETTERS:
        return 0, 0, None, None
    return k, letters, vi, p


def _is_close_apos(text, q):
    """האם הגרש במקום q הוא גרש סוגר (אחרי אות, ולפני סוף מילה)."""
    if text[q] != "'":
        return False
    prv = text[q - 1:q]
    nxt = text[q + 1:q + 2]
    if not prv or not ('א' <= prv <= 'ת' or '֑' <= prv <= 'ׇ' or prv in '.,:;!?)'):
        return False
    return not nxt or not ('א' <= nxt <= 'ת')


def _is_open_apos(text, q):
    """גרש פותח: בראש הפסקה או אחרי רווח/פיסוק/סוגר, או אחרי אות שימוש בראש מילה."""
    if text[q] != "'":
        return False
    nxt = text[q + 1:q + 2]
    if not nxt or not ('א' <= nxt <= 'ת'):
        return False
    prv = text[q - 1:q]
    if not prv or prv in ' 	(-–:,;.[':
        return True
    if prv in USE and (q < 2 or text[q - 2] in ' 	(-–:,;.['):
        return True
    return False


BARRIER_SENT = re.compile(r'[.?!;]')
INTRO_BEFORE = re.compile(r"(?:^|[\s(\-–:])(?:ו|ד|מ|ש)?(?:שנא'|שנאמר|נאמר|כתיב|דכתיב|וכתיב|מדכתיב|אמר\s+קרא|דאמר\s+קרא|"
                          r"הכתוב|שכתוב|ת\"ל|תלמוד\s+לומר|ואומר|אומר|דאמר|אמר|תורה|רחמנא|קרא|כתוב)\s*[:\-–]?\s*$")


def _paired_close_after(text, ap, limit=14):
    """יש גרש סוגר אחרי הגרש הפותח באותו משפט (עד limit מילים, בלי גרש פותח חדש ביניהם)."""
    tail = text[ap + 1:ap + 1 + 12 * (limit + 4)]
    n = 0
    for m in re.finditer(r"[א-ת֑-ׇ\"]+|'|[.?!;]", tail):
        g = m.group(0)
        if g == "'":
            q = ap + 1 + m.start()
            return _is_close_apos(text, q) and n >= 1
        if g in '.?!;':
            return False
        n += 1
        if n > limit:
            return False
    return False


def _paired_open_before(text, q):
    """יש גרש פותח לפני הגרש הסוגר באותו משפט (עד 220 תווים)."""
    seg = text[max(0, q - 220):q]
    cut = max(seg.rfind(c) for c in '.?!;')
    base = max(0, q - 220) + (cut + 1 if cut >= 0 else 0)
    for x in range(base, q):
        if _is_open_apos(text, x):
            return True
    return False


def classify(text, mark):
    """text - טקסט הפסקה; mark - הסימון שהגלאי החזיר (כגון "ד'כל" או "מילה'").
    sure=True רק כשהמקום המדויק של הגרש החסר מוכח; אחרת נשארת הערה רגילה."""
    i0 = text.find(mark)
    if i0 < 0:
        return {'kind': 'unknown'}
    toks = _tok(text)
    if "'" in mark and not mark.endswith("'"):
        # אות שימוש + גרש + תחילת ציטוט: ד'כל
        ap = i0 + mark.index("'")
        letter = mark[mark.index("'") - 1:mark.index("'")]
        if letter not in USE or len(mark.split("'")[0]) != 1:
            return {'kind': 'unknown'}
        idx = [n for n, t in enumerate(toks) if t[0] >= ap + 1]
        if not idx or toks[idx[0]][0] != ap + 1:
            return {'kind': 'unknown'}
        i = idx[0]
        if _paired_close_after(text, ap):
            return {'kind': 'closed', 'basis': 'paired'}
        k, letters, vi, p = _run_from(toks, i)
        if not k:
            return {'kind': 'unknown'}
        end = toks[i + k - 1][1]
        # פסוק ארוך: הגרש הסוגר עשוי לבוא אחרי יותר מארבע עשרה מילים, או בדיוק בסוף הרצף שנמצא
        if text[end:end + 1] == "'" or _paired_close_after(text, ap, max(14, k + 8)):
            return {'kind': 'closed', 'basis': 'verse'}
        verses = VC.load()[0]
        at_verse_end = p + k == len(verses[vi][3])
        at_sentence_end = (i + k >= len(toks)) or toks[i + k][3]
        st = toks[max(i, i + k - 3)][0]
        last = text[st:end]
        sure = bool(at_verse_end or at_sentence_end)
        return {'kind': 'open_only', 'words': k, 'x': last, 'y': last + "'", 'at': end, 'sure': sure}
    if mark.endswith("'"):
        q = i0 + len(mark) - 1
        if _paired_open_before(text, q):
            return {'kind': 'closed', 'basis': 'paired'}
        j = [n for n, t in enumerate(toks) if t[1] == q]
        if not j:
            return {'kind': 'unknown'}
        j = j[0]
        best = None
        for s in range(max(0, j - 10), j):
            if any(toks[n][3] for n in range(s + 1, j + 1)):
                continue
            k, vi, p = VC._longest(toks, s)
            if k and s + k - 1 >= j and j - s + 1 >= 2 and VC._letters(toks, s, j - s + 1) >= MIN_LETTERS:
                best = (s, j - s + 1, 0)
                break
        if best is None:
            for s in range(max(0, j - 10), j):
                w = text[toks[s][0]:toks[s][1]]
                if len(w) < 3 or w[0] not in USE:
                    continue
                if any(toks[n][3] for n in range(s + 1, j + 1)):
                    continue
                t2 = list(toks)
                t2[s] = (toks[s][0] + 1, toks[s][1], VC.skel(w[1:]), toks[s][3])
                k, vi, p = VC._longest(t2, s)
                if k and s + k - 1 >= j and j - s + 1 >= 2 and VC._letters(t2, s, j - s + 1) >= MIN_LETTERS:
                    best = (s, j - s + 1, 1)
                    break
        if best is None:
            return {'kind': 'unknown'}
        s, n, pre = best
        a = toks[s][0]
        before = text[max(0, a - 60):a]
        # הרצף חייב להתחיל אחרי פתיחה ("שנאמר:") או בראש הפסקה או לאחר מקף/נקודתיים,
        # או להיות ארוך (ארבע מילים ומעלה); אחרת מקום הגרש הפותח אינו מוכח.
        sure = bool(INTRO_BEFORE.search(before)) or (a <= 1 and n >= 3) or bool(re.search(r'[:\-–]\s*$', before))
        e = toks[min(s + 1, j)][1]
        x = text[a:e]
        if pre:
            return {'kind': 'close_only', 'words': n, 'x': x, 'y': x[0] + "'" + x[1:], 'at': a + 1, 'sure': sure, 'prefix': 1}
        return {'kind': 'close_only', 'words': n, 'x': x, 'y': "'" + x, 'at': a, 'sure': sure}
    return {'kind': 'unknown'}


if __name__ == '__main__':
    import json, glob, collections
    root = os.path.dirname(TOOLS)
    c = collections.Counter()
    ex = collections.defaultdict(list)
    for fn in sorted(glob.glob(os.path.join(root, 'data', 'bakara', '*-*.json'))):
        if 'decisions' in fn or 'costs' in fn:
            continue
        d = json.load(open(fn, encoding='utf-8'))
        for f in d.get('findings') or []:
            if f.get('det') != 'abbr':
                continue
            r = classify(f.get('text') or '', f.get('mark') or '')
            r['kind'] = r['kind'] + ('+sure' if r.get('sure') else '')
            c[r['kind']] += 1
            if len(ex[r['kind']]) < 4:
                ex[r['kind']].append((f['mark'], (f.get('text') or '')[:90], r))
    print(dict(c))
    for k, v in ex.items():
        print('==', k)
        for m, t, r in v:
            print(' ', m, '|', t, '|', {a: b for a, b in r.items() if a != 'kind'})
