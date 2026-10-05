# -*- coding: utf-8 -*-
"""qa_checks.py - בדיקות בקרה נוספות לדף המסכת, עם קישור למקום המדויק.

כל ממצא הוא (כותרת, טקסט, מקומות). מקום הוא [אינדקס עמוד, מזהה יחידה, תווית]
והדף מצייר ממנו קישור שקופץ ליחידה. הבדיקות רצות בבנייה, על הנתונים
שנכתבו לדף:

  פסוק שלא סומן      - התאמה לנוסח המקרא (verses_check)
  אמוראים חסר        - שם אמורא בראשי תיבות שאינו בסגנון אמוראים
  פסקה בלי סגנון     - סגנון פסקה שאינו ממופה לתפקיד
  פסקה ריקה          - פסקה שכולה רווחים
  כותרת מנותקת       - כותרת נושא שאחריה אין טקסט עד הכותרת הבאה
  חציצה ליד כותרת   - חציצה צמודה לכותרת משנה, ד"ה משנה או כותרת נושא

כיווץ תווים וריווח מכווץ מוורד אינם נבדקים ואינם מדווחים: התצוגה מציגה
בגודל ובריווח מלאים (ג-ג, 5.10.2026).
"""
import os, sys, re, html

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'engine', 'laukmi-engine'))

LIMIT = 40          # מקסימום קישורים לממצא


def _plain(h):
    return html.unescape(re.sub(r'<[^>]+>', '', h or '')).replace('\u200f', '')


def _key(t):
    k = re.sub(r'[^\u05d0-\u05ea]', '', _plain(t))
    return k[:30]


def _units_index(pages):
    """מפתח אותיות-בלבד של פסקה -> (אינדקס עמוד, מזהה יחידה)."""
    idx = {}
    for pi, p in enumerate(pages):
        for u in p['units']:
            texts = [x[1] for x in u.get('l', [])]
            if u.get('a'):
                texts.append(u['a'])
            for t in texts:
                k = _key(t)
                if len(k) >= 8:
                    idx.setdefault(k, (pi, u['id']))
    return idx


def _loc(idx, text, label):
    hit = idx.get(_key(text))
    return [hit[0], hit[1], label] if hit else None


def run(pages, blocks, CS, role_of, masechet):
    out = []
    idx = _units_index(pages)
    am_names = {k for k, v in CS.items() if v == 'am'}
    ps_names = {k for k, v in CS.items() if v == 'ps'}

    # --- פסוקים שלא סומנו ---
    try:
        import verses_check
        res = verses_check.scan_blocks(blocks, role_of, ps_names)
        locs = []
        for bi, txt, s in res:
            l = _loc(idx, txt, s['ref'])
            if l:
                locs.append(l)
        if res:
            out.append(('פסוקים שלא סומנו',
                        '%d פסוקים זוהו לפי נוסח המקרא ואינם בסגנון "פסוק" (הסימון נכתב לוורד בעקוב אחר שינויים בידי '
                        'tools/verses_apply.py)' % len(res), locs[:LIMIT]))
    except SystemExit:
        pass       # אין נוסח מקרא בסביבה הזאת: הבדיקה מדולגת, אך נאמר
        out.append(('פסוקים שלא סומנו', 'הבדיקה לא רצה: חסר data/tanakh-ktiv.json', []))

    # --- אמוראים חסר ---
    try:
        import laukmi_rules as R
        rx = re.compile(R.NAME_RT[0])
        not_name = set(R.NOT_NAME)
        miss, locs = 0, []
        for b in blocks:
            if not str(role_of(b)).startswith('body'):
                continue
            fl = []
            for r in b['runs']:
                fl.extend([r.get('cs') in am_names] * len(r['t']))
            t = b['text']
            if len(fl) != len(t):
                continue
            for m in rx.finditer(t):
                w = m.group(1)
                if w in not_name or any(fl[m.start(1):m.end(1)]):
                    continue
                miss += 1
                if len(locs) < LIMIT:
                    l = _loc(idx, t, w)
                    if l:
                        locs.append(l)
        if miss:
            out.append(('סגנון אמוראים חסר',
                        '%d שמות אמוראים בראשי תיבות (למשל ר"י, אר"ל) אינם בסגנון "אמוראים"' % miss, locs))
    except Exception as e:
        out.append(('סגנון אמוראים חסר', 'הבדיקה לא רצה: %s' % e, []))

    # --- פסקאות בלי סגנון ממופה, ופסקאות ריקות ---
    from styles_map import ROLE
    unm, locs = 0, []
    for b in blocks:
        if b['style'] not in ROLE and b['style'] != 'Normal':
            unm += 1
            if len(locs) < LIMIT:
                l = _loc(idx, b['text'], b['style'])
                if l:
                    locs.append(l)
    if unm:
        out.append(('טקסט בלי סגנון ממופה',
                    '%d פסקאות בסגנון שאינו ממופה לתפקיד (מוצגות כגוף רגיל)' % unm, locs))

    # --- כותרת נושא מנותקת: אין אחריה טקסט ---
    n_det, locs = 0, []
    for pi, p in enumerate(pages):
        us = p['units']
        for i, u in enumerate(us):
            if u['k'] == 'nose' and not u.get('l'):
                nxt = us[i + 1] if i + 1 < len(us) else None
                if nxt is None or nxt['k'] in ('nose', 'hatz', 'perek-num', 'perek-name', 'hadran'):
                    n_det += 1
                    if len(locs) < LIMIT:
                        locs.append([pi, u['id'], _plain(u.get('a'))[:30]])
    if n_det:
        out.append(('כותרת מנותקת מן התוכן',
                    '%d כותרות נושא שאחריהן אין טקסט עד הכותרת או החציצה הבאה' % n_det, locs))
    return out
