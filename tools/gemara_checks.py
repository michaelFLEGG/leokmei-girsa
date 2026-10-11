# -*- coding: utf-8 -*-
"""gemara_checks.py - גלאי הגהה שנשענים על הגמרא המנוקדת (ט4).

הספר מקצר ומתרגם את הגמרא, ולכן כמעט כל מילה שבו אמורה להימצא גם
בגמרא של אותו דף. מכאן שלושה גלאים:

א. כתיב   - מילה שאינה בגמרא של הדף ועמוד לכל צד, אך רחוקה אות אחת
            ממילה שיש שם. אותיות דומות (ה/ח, ב/כ, ד/ר, ו/ז, ס/ם, ט/ת)
            מעלות את החומרה.
ב. ייחוס  - ראשי תיבות של תנא או אמורא שאף פירוש שלהם אינו בגמרא של
            הדף ועמוד לכל צד.
ג. מקום ציון הדף - שש המילים הראשונות של העמוד בספריא, מול המקום שבו
            יושב ציון הדף בקובץ.

מה שאינו ודאי אינו מוצג כוודאי: גלאי שיותר ממחצית ממצאיו שווא יורד
לדרגה "קל" ומנוסח כשאלה. המדידה נעשתה על גיבוי סוכה שלפני ההגהה,
והמספרים רשומים ב-_שומר\\דוחות.
"""
import os, sys, json, io, re, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sefaria_map import heb_to_num
from match_sources import norm as _norm_match, NIKUD, PUNCT, TAGS


def gnorm(t):
    """נרמול לגלאי הכתיב. בשונה מנרמול ההצמדה, הוא **אינו** מאחד יי/וו:
    כפל אות הוא בדיוק אחת השגיאות שאנחנו מחפשים, ואיחוד היה מוחק אותה."""
    import unicodedata
    t = TAGS.sub(' ', t or '')
    t = unicodedata.normalize('NFKD', t)
    t = NIKUD.sub('', t)
    t = PUNCT.sub(' ', t).replace('	', ' ')
    t = t.translate(str.maketrans('ךםןףץ', 'כמנפצ'))
    return re.sub(r'\s+', ' ', t).strip()

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEB = re.compile(r'^[א-ת]{3,}$')
SIMILAR = [('ה', 'ח'), ('ב', 'כ'), ('ד', 'ר'), ('ו', 'ז'), ('ס', 'ם'), ('ט', 'ת'),
           ('י', 'ו'), ('נ', 'ג'), ('כ', 'פ'), ('ש', 'ם')]
SIMSET = {frozenset(p) for p in SIMILAR}

# תחיליות שהספר מוסיף ומורידות מן הזיהוי
PREFIX = ('ומ', 'וש', 'ול', 'וב', 'וכ', 'וד', 'ומד', 'דמ', 'דל', 'דב', 'דכ', 'שב', 'שמ',
          'ו', 'ד', 'ש', 'ה', 'ב', 'ל', 'כ', 'מ')


def strip_pfx(w):
    out = {w}
    for p in PREFIX:
        if w.startswith(p) and len(w) - len(p) >= 3:
            out.add(w[len(p):])
    return out


def daf_window(src, daf, span=1):
    """אוצר המילים של הגמרא בדף הזה ובעמוד אחד לכל צד."""
    pages = src.get('pages') or {}
    k = heb_to_num(daf)
    if k is None:
        return None
    amud = 1 if (daf or '').strip().endswith(':') else 0
    key = k * 2 + amud
    out = set()
    found = False
    for heb, p in pages.items():
        kk = heb_to_num(heb)
        if kk is None:
            continue
        kk = kk * 2 + (1 if heb.strip().endswith(':') else 0)
        if abs(kk - key) <= span:
            found = True
            # התחיליות נפרקות גם בצד הגמרא. בלעדי זה כל הבדל בתחילית
            # נראה כשגיאת כתיב, וזה היה רוב הרעש במדידה הראשונה.
            for g in p['gemara']:
                for w in gnorm(g).split():
                    out.update(strip_pfx(w))
    return out if found else None


def near(w, vocab):
    """מחזיר (מילה קרובה, סוג ההבדל) רק לשלושת הסוגים שהם באמת שגיאת
    כתיב: החלפת אות דומה, כפל אות או חסרונו, והיפוך שתי אותיות סמוכות.
    הבדל אחר - בעיקר תחילית או סופית - אינו ממצא, וממנו בא כל הרעש."""
    n = len(w)
    for v in vocab:
        m = len(v)
        if v == w or abs(n - m) > 1:
            continue
        if n == m:
            diff = [i for i in range(n) if w[i] != v[i]]
            if len(diff) == 1:
                i = diff[0]
                if frozenset((w[i], v[i])) in SIMSET:
                    return v, 'דומה'
            elif (len(diff) == 2 and diff[1] == diff[0] + 1
                  and w[diff[0]] == v[diff[1]] and w[diff[1]] == v[diff[0]]):
                return v, 'היפוך'
        else:
            a, b = (w, v) if n > m else (v, w)
            i = 0
            while i < len(b) and a[i] == b[i]:
                i += 1
            if a[i + 1:] != b[i:]:
                continue
            if (i > 0 and a[i] == a[i - 1]) or (i + 1 < len(a) and a[i] == a[i + 1]):
                return v, 'כפל'
    return None


def common_words(path=None):
    """מילים שכיחות בספר עצמו. מילה שחוזרת בהרבה מסכתות היא לשון המחבר
    ולא שגיאה, גם כשאינה בגמרא - הספר מתרגם ארמית לעברית."""
    path = path or os.path.join(ROOT, 'data', 'common-words.json')
    if os.path.exists(path):
        return set(json.load(io.open(path, encoding='utf-8')))
    return set()


def build_common(out=None, min_tractates=3, log=print):
    """בונה את רשימת המילים השכיחות מכל קובצי הוורד יחד."""
    from docx2json import convert
    from build_all import SLUG
    DRIVE = r'C:\Users\Owner\Desktop\שיננא לHTML'
    roster = json.load(io.open(os.path.join(ROOT, 'input', 'current-docx.json'), encoding='utf-8'))
    seen = collections.Counter()
    files = [f for f in sorted(os.listdir(DRIVE)) if f.endswith('.docx') and f in roster]
    for f in files:
        try:
            blocks = convert(os.path.join(DRIVE, f))
        except Exception as e:
            log('דילוג', f, repr(e)); continue
        ws = set()
        for b in blocks:
            ws.update(norm(b['text']).split())
        for w in ws:
            seen[w] += 1
        log('  %s: %d מילים שונות' % (f[:28], len(ws)))
    common = sorted(w for w, c in seen.items() if c >= min_tractates)
    out = out or os.path.join(ROOT, 'data', 'common-words.json')
    io.open(out, 'w', encoding='utf-8').write(json.dumps(common, ensure_ascii=False))
    log('נשמרו %d מילים שכיחות (מופיעות בלפחות %d מסכתות)' % (len(common), min_tractates))
    return set(common)


# ---------------------------------------------------------------- הגלאים

def spelling(blocks, src, common, severity='בינוני'):
    out = []
    cache = {}
    for b in blocks:
        daf = (b.get('daf') or '').strip()
        if daf not in cache:
            cache[daf] = daf_window(src, daf)
        vocab = cache[daf]
        if not vocab:
            continue
        for w in gnorm(b['text']).split():
            if not HEB.match(w) or w in common:
                continue
            if any(f in vocab for f in strip_pfx(w)):
                continue
            hit = near(w, vocab)
            if not hit:
                continue
            v, how = hit
            out.append({'sev': severity, 'kind': 'כתיב מול הגמרא', 'how': how,
                        'i': b['i'], 'daf': daf, 'mark': w,
                        'note': 'המילה "%s" אינה בגמרא של הדף, ושם כתוב "%s" (%s)'
                                % (w, v, {'דומה': 'אותיות דומות', 'כפל': 'כפל אות',
                                          'היפוך': 'היפוך אותיות'}[how]),
                        'fix': '%s ⟵ %s' % (w, v)})
    return out


def attribution(blocks, src, expand, severity='קל'):
    out = []
    cache = {}
    rx = re.compile(r'(?<![א-ת])((?:ר|ת)["\u05f4][א-ת]{1,3})(?![א-ת])')
    for b in blocks:
        daf = (b.get('daf') or '').strip()
        if daf not in cache:
            cache[daf] = daf_window(src, daf)
        vocab = cache[daf]
        if not vocab:
            continue
        for m in rx.finditer(b['text']):
            ab = m.group(1).replace('\u05f4', '"')
            names = expand.get(ab)
            if not names:
                continue
            if any(all(p in vocab for p in gnorm(nm).split()) for nm in names):
                continue
            out.append({'sev': severity, 'kind': 'ייחוס מול הגמרא', 'i': b['i'], 'daf': daf,
                        'mark': m.group(1),
                        'note': 'בגמרא של דף %s אין אף אחד מן השמות ש"%s" עשוי לציין (%s)'
                                % (daf, ab, ', '.join(names[:4])),
                        'fix': 'לבדוק את ראשי התיבות'})
    return out


def daf_position(blocks, src, tol=2, severity='בינוני'):
    """שש המילים הראשונות של העמוד בספריא, מול מקום ציון הדף בקובץ."""
    out = []
    pages = src.get('pages') or {}
    idx = {}
    for n, b in enumerate(blocks):
        if b['style'] == 'דף בצד' and b['text'].strip():
            idx[b['text'].strip()] = n
    for heb, p in pages.items():
        if heb not in idx:
            continue
        head = gnorm(p['gemara'][0]).split()[:6]
        if len(head) < 4:
            continue
        at = idx[heb]
        # מחפשים היכן בקובץ מתחילות אותן מילים
        best, bn = 0, None
        for n in range(max(0, at - 12), min(len(blocks), at + 13)):
            ws = set(gnorm(blocks[n]['text']).split())
            sc = sum(1 for w in head if w in ws)
            if sc > best:
                best, bn = sc, n
        if bn is None or best < 3:
            continue
        if abs(bn - at) > tol:
            out.append({'sev': severity, 'kind': 'מקום ציון הדף', 'i': at, 'daf': heb,
                        'mark': heb,
                        'note': 'פתיחת דף %s בגמרא ("%s") נמצאת אצלנו %d פסקאות %s מציון הדף'
                                % (heb, ' '.join(head[:5]), abs(bn - at),
                                   'אחרי' if bn > at else 'לפני'),
                        'fix': 'לבדוק אם ציון הדף במקומו'})
    return out
