# מן "מה שהמנהל רואה" אל רשימת יעד לכל עמוד, וזיהוי שורות כפולות
import sys, re, json, html, pickle
sys.path.insert(0, '/home/user/leokmei-girsa/tools')
INV = {'mk': 'מק', 'am': 'אם', 'hs': 'הס', 'ps': 'פס', 'dm': 'דה', 'ns': 'נש', 'mf': 'מפ', 'b': 'ב', 'tn': 'מש', 'kt': 'כב', 'ot': 'אות'}

def to_inter(h):
    def rep(m):
        c = m.group(1).split()[0] if m.group(1) else ''
        t = m.group(2)
        if not html.unescape(re.sub(r'<[^>]+>', '', t)).strip(): return t   # ריצה מעוצבת שכולה רווח - רווח פשוט
        tag = INV.get(c)
        return '{%s:%s}' % (tag, t) if tag else t
    s = re.sub(r'<i class="([^"]*)">(.*?)</i>', rep, h or '', flags=re.S)
    s = re.sub(r'<br\s*/?>', ' ', s)
    s = re.sub(r'<[^>]+>', '', s)
    return html.unescape(s).replace('‏', '')

def plain(h):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', h or '')).replace('\xa0', ' ')).strip()

def ps_of(cls):
    t = (cls or '').split()
    if 'hr' in t: return 'רקע והסבר'
    if 'in' in t: return 'פיסקת תשובה'
    if 'sp' in t: return 'רווח לפני'
    return None

def items_of_page(pg):
    """פריטי היעד של עמוד, לפי סדר הפסקאות בוורד"""
    out = []
    def side(a):
        for part in re.split(r'<br\s*/?>', a or ''):
            if plain(part):
                out.append({'t': 'S', 'm': to_inter(part)})
    for u in pg['units']:
        k = u.get('k')
        if k == 'u':
            side(u.get('a'))
            for cls, h in u.get('l') or []:
                if cls == 'hatz': continue
                it = {'t': 'L', 'm': to_inter(h)}
                p = ps_of(cls)
                if p: it['ps'] = p
                out.append(it)
        elif k == 'm':
            if u.get('mbw') and u.get('mbh') == 'word':
                out.append({'t': 'X:משנה בצד', 'm': u['mbw'], 'ps': 'משנה בצד'})
            side(u.get('w'))
            for cls, h in u.get('l') or []:
                if cls == 'hatz': continue
                out.append({'t': 'L', 'm': to_inter(h), 'ps': 'משניות'})
        elif k in ('hatz', 'perek-range', 'perek-start', 'hadran'):
            st = {'hatz': 'חציצה', 'perek-range': 'דפים בפרק ב', 'perek-start': 'פתיחת פרק', 'hadran': 'הדרן'}[k]
            out.append({'t': 'X:' + st, 'm': to_inter(u.get('a')), 'ps': st})
        elif k in ('dh', 'nose'):
            side(u.get('w'))
            out.append({'t': 'D' if k == 'dh' else 'H', 'm': to_inter(u.get('a'))})
    return out

def flat_lines(pages):
    """כל השורות לפי הסדר: (עמוד, יחידה, מספר שורה או None לכותרת, סוג, טקסט)"""
    L = []
    for pi, pg in enumerate(pages):
        for ui, u in enumerate(pg['units']):
            k = u.get('k')
            if k in ('dh', 'nose', 'hatz') or k.startswith('perek') or k == 'hadran':
                L.append((pi, ui, None, k, plain(u.get('a'))))
            if k in ('u', 'm'):
                if u.get('a') or u.get('w'): L.append((pi, ui, 'a', 'side', plain(u.get('a') or u.get('w'))))
                for li, (cls, h) in enumerate(u.get('l') or []):
                    L.append((pi, ui, li, 'm' if k == 'm' else 'u', plain(h)))
    return L
