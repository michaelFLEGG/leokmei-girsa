"""פיסוק אחיד בכל האתר (6.11.2026, בעל הפרויקט).

אין נקודה-פסיק: נקודה רגילה במקומה. אין מקף ארוך (– או —): מקף רגיל.
אין רווח לפני נקודה. חל על הטקסט שבתוך HTML בלבד: תגיות וישויות
(&quot; וכדומה) אינן נוגעות. הרווח נמחק גם כשתגית מפרידה בינו לבין הנקודה.
"""
import re

_TOK = re.compile(r'(<[^>]*>|&#?[A-Za-z0-9]+;)')
_SP = '  ‏‎'
_MAP = {'–': '-', '—': '-', ';': '.'}


def html(s):
    if not s or not isinstance(s, str):
        return s
    parts = _TOK.split(s)
    # שלב א: החלפת תווים בטקסט בלבד (חלקים זוגיים)
    for i in range(0, len(parts), 2):
        if parts[i]:
            parts[i] = ''.join(_MAP.get(c, c) for c in parts[i])
    # שלב ב: מחיקת רווח שאחריו (אולי אחרי תגיות ורווחים נוספים) בא נקודה
    flat = []                      # (מספר חלק, מיקום) לכל תו טקסט
    for i in range(0, len(parts), 2):
        for j in range(len(parts[i])):
            flat.append((i, j))
    kill = set()
    nxt_nonsp = None
    for (i, j) in reversed(flat):
        c = parts[i][j]
        if c in _SP:
            if nxt_nonsp == '.':
                kill.add((i, j))
        else:
            nxt_nonsp = c
    if kill:
        for i in range(0, len(parts), 2):
            parts[i] = ''.join(c for j, c in enumerate(parts[i]) if (i, j) not in kill)
    return ''.join(parts)


def text(s):
    if not s or not isinstance(s, str):
        return s
    s = ''.join(_MAP.get(c, c) for c in s)
    return re.sub('[' + _SP + ']+(?=\\.)', '', s)


def pages(pgs):
    """מחיל על כל יחידות הדפים. מחזיר כמה מחרוזות השתנו."""
    n = 0
    for pg in pgs:
        for u in pg.get('units') or []:
            for k in ('a', 'w'):
                if isinstance(u.get(k), str):
                    v = html(u[k])
                    if v != u[k]:
                        u[k] = v; n += 1
            for ln in u.get('l') or []:
                if isinstance(ln, list) and len(ln) > 1 and isinstance(ln[1], str):
                    v = html(ln[1])
                    if v != ln[1]:
                        ln[1] = v; n += 1
    return n
