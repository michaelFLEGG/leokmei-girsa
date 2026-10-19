# -*- coding: utf-8 -*-
"""hv_common.py - עזרים משותפים לשכבת "הסקירה המועשרת מהמאגר" (מנה 19.10.2026).

מאגר ביאור "חברותא" יושב בריפו הפרטי leokmei-chavruta בלבד. הקוד כאן (ציבורי) אינו מכיל אותו ואינו כותב אותו
לשום מקום ציבורי: כל התוצרים שיש בהם לשון חברותא (חבילות ידע, מועמדים) נכתבים לריפו הפרטי.
"""
import os, re, sys, json, math
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TOOLS = os.path.join(ROOT, 'tools')
for _p in (TOOLS, os.path.join(TOOLS, 'skira'), os.path.join(TOOLS, 'bakara')):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import skira_common as C          # noqa: E402

CHAV = os.environ.get('LK_CHAVRUTA') or next(
    (p for p in (r'C:\leokmei-work\chavruta', os.path.join(os.path.dirname(ROOT), 'leokmei-chavruta'),
                 os.path.join(os.path.dirname(ROOT), 'chavruta')) if os.path.isdir(p)), '')
TITLE_STYLES = {'נושא', '0.1', '0.2', '0.3', 'פתיחת פרק'}


def heb_to_slug():
    import build_all
    return dict(build_all.SLUG)


def chav_json_dir(heb):
    return os.path.join(CHAV, 'json', heb)


def daf_label_of_file(fn):
    """'לא.json' -> 'ל.' ; 'לב.json' -> 'ל:' (שם הקובץ: אותיות הדף ואות העמוד)."""
    b = os.path.basename(fn)[:-5]
    return b[:-1] + ('.' if b[-1] == 'א' else ':')


def file_of_label(lbl):
    return re.sub(r'[^א-ת]', '', lbl) + ('ב' if lbl.strip().endswith(':') else 'א')


def norm(t):
    return re.sub(r'\s+', ' ', C.NIK.sub('', re.sub(r'[^\u05d0-\u05ea\s]', ' ', t or ''))).strip()


def grams(t):
    out = Counter()
    for w in norm(t).split():
        w2 = '^' + w + '$'
        for k in range(len(w2) - 2):
            out[w2[k:k + 3]] += 1
    return out


def cos(a, b, idf):
    num = sum(a[k] * b[k] * idf.get(k, 1) ** 2 for k in a if k in b)
    na = math.sqrt(sum((v * idf.get(k, 1)) ** 2 for k, v in a.items()))
    nb = math.sqrt(sum((v * idf.get(k, 1)) ** 2 for k, v in b.items()))
    return num / (na * nb) if na and nb else 0.0


def words(t):
    return norm(t).split()


def ngram_overlap(a, b, n=6):
    """מספר רצפי n מילים משותפים: שער הדלפה (לשון חברותא אסורה בממצא ציבורי)."""
    wa, wb = words(a), words(b)
    if len(wa) < n or len(wb) < n:
        return 0
    sb = {tuple(wb[i:i + n]) for i in range(len(wb) - n + 1)}
    return sum(1 for i in range(len(wa) - n + 1) if tuple(wa[i:i + n]) in sb)


def jload(p, d=None):
    return C.jload(p, d)


def jsave(p, o):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(o, f, ensure_ascii=False, separators=(',', ':'))
    os.replace(tmp, p)
