# -*- coding: utf-8 -*-
"""bkh_common.py - תשתית משותפת למנת "מנוע הניסוח": בכורות כה. עד לה: (13.10.2026).

כל הכלים כאן עובדים על עותק של קובץ הוורד (לעולם לא על הקובץ בדרייב) ורק בטווח הפסקאות של כה. עד לה:.
הטווח נקבע לפי ציוני "דף בצד" (לא לפי אינדקס קבוע), ולכן שורד שינויי מספר פסקאות.
"""
import os, sys, io, re, json, glob, hashlib
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'tools'))
sys.path.insert(0, os.path.join(REPO, 'engine', 'laukmi-engine'))
import laukmi_mech
import masechet_fmt as mf
from laukmi_mech import Doc, q, text_map

WORK = os.environ.get('BKH_WORK', r'C:\Users\Owner\leokmei-bkh-work')
DRIVE = r'C:\Users\Owner\Desktop\שיננא לHTML'
DRIVE_FILE = os.path.join(DRIVE, 'בכורות מעודכן 2.docx')
FIRST_DAF = 'כה.'      # תחילת הטווח (כולל)
STOP_DAF = 'לו.'       # סוף הטווח (לא כולל)
DAF_STYLE = 'דף בצד'

AUTH_MECH = 'קלוד - מכני'
AUTH_SEM = 'קלוד - סמנטי'
AUTH_FORM = 'קלוד - ניסוח'
PENDING_AUTHORS = ('michael flegg', 'עריכה מהאתר', 'דבורה שירה פלג', 'הצעה מהאתר - יהודה')
OWN_AUTHORS = (AUTH_MECH, AUTH_SEM, AUTH_FORM)

TAB_MARK = '⇥'
LONG_DASH = ('–', '—', '―')


def daf_markers(doc, paras=None):
    paras = paras if paras is not None else list(doc.paragraphs())
    out = []
    for i, p in enumerate(paras):
        if doc.pstyle(p) == DAF_STYLE:
            out.append((i, mf.live(p).strip()))
    return out


def find_range(doc):
    """(אינדקס התחלה, אינדקס סוף לא כולל) בפסקאות הקובץ."""
    paras = list(doc.paragraphs())
    lo = hi = None
    for i, t in daf_markers(doc, paras):
        if t == FIRST_DAF and lo is None:
            lo = i
        if t == STOP_DAF and hi is None:
            hi = i
    if lo is None or hi is None or hi <= lo:
        raise SystemExit('לא נמצא טווח %s עד %s' % (FIRST_DAF, STOP_DAF))
    return lo, hi


def patch_range(doc):
    """מגביל את Doc.paragraphs() של המופע לטווח (לפי אלמנטים, כך שפסקאות שנוספו בתוכו נכללות)."""
    if getattr(doc, '_range', None):
        return doc._range
    paras = list(doc.paragraphs())
    lo, hi = find_range(doc)
    start, stop = paras[lo], paras[hi]
    root = doc.doc

    def ranged():
        on = False
        for p in root.iter(q('p')):
            if p is start:
                on = True
            if p is stop:
                return
            if on:
                yield p
    doc.paragraphs = ranged
    doc._range = (lo, hi)
    return lo, hi


def fp(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()[:10]


def norm(s):
    """נרמול להשוואה: טאבים וסמני טאב, רווחים כפולים."""
    return re.sub(r'\s+', ' ', s.replace(TAB_MARK, ' ')).strip()


def mark_tabs(s):
    """הטאבים לסמן ⇥ (ריצה אחת לסמן אחד), כדי שיעברו שלמים בסוכני הניסוח."""
    return re.sub(r'\t+', TAB_MARK, s)


def unmark_tabs(s):
    return s.replace(TAB_MARK, '\t')


def sources():
    d = json.load(io.open(os.path.join(REPO, 'data', 'sources', 'bekhorot.json'), encoding='utf-8'))
    return d['pages']


# ---- נקודת ביקורת ודופק (נוהל שומר הדופק, 9.10.2026) ----
import time as _time, datetime as _dt
STATE_PATHS = [os.path.join(WORK, 'state.json'), os.path.join(DRIVE, '_שומר', 'מצב-בכורות-כה-לה.json')]


def beat(unit=None, stage=None, status=None, note=None):
    """מעדכן את קובץ המצב (איזה דף הושלם באיזה מנוע) ואת הדופק. נקרא אחרי כל צעד."""
    st = {}
    try:
        st = json.load(io.open(STATE_PATHS[0], encoding='utf-8'))
    except Exception:
        st = {'units': {}, 'log': []}
    now = _dt.datetime.now().isoformat(timespec='seconds')
    st['heartbeat'] = now
    st['run'] = 'מנוע הניסוח: בכורות כה.-לה: (13.10.2026)'
    if unit and stage:
        st['units'].setdefault(unit, {})[stage] = status or 'בוצע'
    if note:
        st['log'].append({'t': now, 'unit': unit, 'stage': stage, 'note': note})
        st['log'] = st['log'][-300:]
    for p in STATE_PATHS:
        try:
            os.makedirs(os.path.dirname(p), exist_ok=True)
            json.dump(st, io.open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        except Exception:
            pass
    return st
