# המרה חד פעמית של ברכות: הוורד אל "מה שהמנהל רואה" אחרי ניקוי הכפילויות (פרומפט 38)
import sys, os, re, json, pickle, copy, shutil, tempfile
sys.path.insert(0, '/home/user/leokmei-girsa/tools'); sys.path.insert(0, '/tmp/claude-0')
os.environ.setdefault('LG_DRIVE', tempfile.mkdtemp())
import word_apply as WA
from target import items_of_page, flat_lines, plain
# סגנונות ברכות: חלון הכותרת הוא "חלון 3", ד"ה משנה גם "משנה ד''ה", ושורת "נקודה"
WA.SYNC_TYPE['חלון 3'] = 'S'; WA.SYNC_TYPE["משנה ד''ה"] = 'D'
WA.SYNC_NEW_STYLE['S'] = 'חלון 3'
WA.SYNC_PS = WA.SYNC_PS + ('נקודה',)
import target as TG
_ps0 = TG.ps_of
TG.ps_of = lambda cls: 'נקודה' if 'nk' in (cls or '').split() else _ps0(cls)

A = pickle.load(open('/tmp/claude-0/v_admin.pkl', 'rb'))['cap']['pages']
W = pickle.load(open('/tmp/claude-0/v_word.pkl', 'rb'))
WP, blocks = W['cap']['pages'], W['blocks']
T = copy.deepcopy(A)
log = []
# א2. כוונת העריכות שלא נקלטו (ראו הדוח): במקום שורה כפולה - מה שהמנהל כתב בה
def find(daf, text, kind='u'):
    for pg in T:
        if pg['daf'] != daf: continue
        for ui, u in enumerate(pg['units']):
            for li, (c, h) in enumerate(u.get('l') or []):
                if (u.get('k') == kind) and plain(h).startswith(text): return pg, ui, li
    raise LookupError('לא נמצא: %s %s' % (daf, text))
def split_at(pg, ui, li, new_unit):
    """מחליף את השורה li ביחידה חדשה (או יחידות), והשורות שאחריה עוברות ליחידה החדשה האחרונה"""
    u = pg['units'][ui]; rest = u['l'][li+1:]; u['l'] = u['l'][:li]
    if rest:
        if new_unit[-1].get('k') == 'u': new_unit[-1]['l'] += rest
        else: new_unit.append({'k': 'u', 'a': '', 'l': rest})
    pg['units'][ui+1:ui+1] = new_unit
# ב.: המשנה "מעשה בבני ר"ג..." פוצלה לשתי שורות (15.11 11:48)
try:
    pg, ui, li = find('ב.', 'מעשה בבני ר"ג שבאו', 'm')
    _u = pg['units'][ui]
    while li + 1 < len(_u['l']) and plain(_u['l'][li+1][1]) == plain(_u['l'][li][1]): del _u['l'][li+1]
    h = pg['units'][ui]['l'][li][1]; k = h.index('<i class="am">וא')
    pg['units'][ui]['l'][li:li+1] = [[pg['units'][ui]['l'][li][0], h[:k].rstrip()], [pg['units'][ui]['l'][li][0], h[k:]]]
    log.append('ב. · מעשה בבני ר"ג: שלוש פעמים, ונשארה פעם אחת, מפוצלת לשתי שורות כפי שהמנהל פיצל')
except (LookupError, AssertionError, ValueError, IndexError) as _e:
    log.append('דילוג (כבר תוקן בידי המנהל?): ' + 'ב.: המשנה "מעשה בבני ר"ג..." פוצלה לשתי שורות (15.11 11:48)' + ' - ' + str(_e))

# כה: השורה הכפולה "ומי רגלים עצמן" נכתבה מחדש: "ותניא: גרף של רעי ועביט..." (15.11 12:47)
try:
    pg, ui, li = find('כה:', 'ומי רגלים עצמן - עד שיטיל')
    u = pg['units'][ui]; assert plain(u['l'][li+1][1]) == plain(u['l'][li][1]); rest = u['l'][li+2:]; u['l'] = u['l'][:li+1]
    pg['units'][ui+1:ui+1] = [{'k': 'u', 'a': 'ותניא:', 'l': [['sp b1 a0', 'גרף של רעי ועביט של מי רגלים - אסור לקרות קר"ש כנגדן, אף שאין בהן כלום, בין לפני המטה בין לאחר המטה,']] + rest}]
    log.append('כה: · ומי רגלים עצמן: השורה הכפולה הוחלפה במה שהמנהל כתב בה ("ותניא: גרף של רעי ועביט...")')
except (LookupError, AssertionError, ValueError, IndexError) as _e:
    log.append('דילוג (כבר תוקן בידי המנהל?): ' + 'כה: השורה הכפולה "ומי רגלים עצמן" נכתבה מחדש: "ותניא: גרף של רעי ועב' + ' - ' + str(_e))

# לה: "ולר"י:" השני - "שלר' ינאי: ..." (9.11)
try:
    pg, ui, li = find('לה:', 'ולר"י:')
    u = pg['units'][ui]; assert plain(u['l'][li+1][1]) == 'ולר"י:'
    u['l'][li+1] = [u['l'][li+1][0], "שלר' ינאי: אין הטבל מתחייב במעשר עד שיראה פני הבית, ד'בערתי הקדש מן הבית'."]
    del u['l'][li]   # "ולר"י:" שלפניה - המנהל מחק אותה (15.11 08:39)
    log.append('לה: · ולר"י: הראשונה נמחקה כפי שהמנהל מחק, והשנייה היא מה שהמנהל כתב בה ("שלר\' ינאי: אין הטבל מתחייב...")')
except (LookupError, AssertionError, ValueError, IndexError) as _e:
    log.append('דילוג (כבר תוקן בידי המנהל?): ' + 'לה: "ולר"י:" השני - "שלר\' ינאי: ..." (9.11)' + ' - ' + str(_e))

# לה: "ולרי"ו:" ו"אפילו חצר קובעת..." אוחדו לשורה אחת (15.11 08:39)
try:
    pg, ui, li = find('לה:', 'ולרי"ו:')
    u = pg['units'][ui]; assert plain(u['l'][li+1][1]).startswith('אפילו חצר קובעת')
    u['l'][li:li+2] = [[u['l'][li][0], u['l'][li][1].rstrip() + ' ' + u['l'][li+1][1].lstrip()]]
    log.append('לה: · ולרי"ו: + אפילו חצר קובעת - אוחדו לשורה אחת כפי שהמנהל איחד')
except (LookupError, AssertionError, ValueError, IndexError) as _e:
    log.append('דילוג (כבר תוקן בידי המנהל?): ' + 'לה: "ולרי"ו:" ו"אפילו חצר קובעת..." אוחדו לשורה אחת (15.11 08:39)' + ' - ' + str(_e))

# מא.: "והברייתא כך" - כותרת צד "חסורי מחסרא:" והשורה "וה"ק: צנון וזית..." (9.11)
try:
    pg, ui, li = find('מא.', 'והברייתא כך: צנון')
    u = pg['units'][ui]; assert plain(u['l'][li+1][1]).startswith('והברייתא כך: צנון')
    h = u['l'][li+1][1].replace('והברייתא כך', 'וה"ק', 1)
    rest = u['l'][li+2:]; u['l'] = u['l'][:li]
    pg['units'][ui+1:ui+1] = [{'k': 'u', 'a': 'חסורי מחסרא:', 'l': [[u['l'][0][0] if u['l'] else 'b0 a0', h]] + rest}]
    log.append('מא. · והברייתא כך: פעמיים - שורה אחת, בכותרת הצד "חסורי מחסרא:" ובנוסח "וה"ק: צנון וזית..." כפי שהמנהל כתב')
except (LookupError, AssertionError, ValueError, IndexError) as _e:
    log.append('דילוג (כבר תוקן בידי המנהל?): ' + 'מא.: "והברייתא כך" - כותרת צד "חסורי מחסרא:" והשורה "וה"ק: צנון וזית' + ' - ' + str(_e))

# מב: "ור"כ ורב ששת..." פעמיים - פעם אחת
try:
    pg, ui, li = find('מב:', 'ור"כ ורב ששת')
    u = pg['units'][ui]; assert plain(u['l'][li+1][1]) == plain(u['l'][li][1]); del u['l'][li+1]
    log.append('מב: · ור"כ ורב ששת, ר"ה ור"י וכל תלמידי רב: אינו פוטר - פעמיים, נשארה אחת')
except (LookupError, AssertionError, ValueError, IndexError) as _e:
    log.append('דילוג (כבר תוקן בידי המנהל?): ' + 'מב: "ור"כ ורב ששת..." פעמיים - פעם אחת' + ' - ' + str(_e))

# מז.: "רבב"ח שידך" - כותרת צד "רבב"ח" (15.11 10:19)
try:
    pg, ui, li = find('מז.', 'רבב"ח שידך')
    u = pg['units'][ui]; assert plain(u['l'][li+1][1]) == plain(u['l'][li][1])
    h = u['l'][li][1]; h2 = h[h.index('שידך'):]; cls = u['l'][li][0]
    rest = u['l'][li+2:]; u['l'] = u['l'][:li]
    pg['units'][ui+1:ui+1] = [{'k': 'u', 'a': 'רבב"ח', 'l': [[cls, h2]] + rest}]
    log.append('מז. · רבב"ח שידך את בנו: פעמיים - שורה אחת, ו"רבב"ח" בכותרת צד כפי שהמנהל עשה')
except (LookupError, AssertionError, ValueError, IndexError) as _e:
    log.append('דילוג (כבר תוקן בידי המנהל?): ' + 'מז.: "רבב"ח שידך" - כותרת צד "רבב"ח" (15.11 10:19)' + ' - ' + str(_e))

# כללים כלליים לכפילות (אחרי התיקונים המפורשים):
# ר1: רצף של 1 עד 8 פריטים (שורות, כותרות צד, כותרות) שחוזר מיד פעם נוספת - העותק השני יוצא
# ר2: שורת גוף שכולה שם דובר ("רב:") ומיד אחריה כותרת צד זהה - השורה יוצאת
# ר3: ד"ה שמיד אחריו תיבת משנה שפותחת באותן מילים בדיוק - הד"ה יוצא (בכל ברכות ד"ה בא אחרי התיבה)
def items_seq():
    out = []
    for pi, pg in enumerate(T):
        for ui, u in enumerate(pg['units']):
            k = u.get('k')
            if k in ('u', 'm'):
                if u.get('a') or u.get('w'): out.append(((pi, ui, 'a'), 'side', plain(u.get('a') or u.get('w'))))
                for li, (c, h) in enumerate(u.get('l') or []): out.append(((pi, ui, li), k, plain(h)))
            elif k in ('dh', 'nose'):
                out.append(((pi, ui, None), k, plain(u.get('a'))))
            else:
                out.append(((pi, ui, None), k, '\x00' + str(pi) + ':' + str(ui)))   # מחיצה: עיטור, פתיחת פרק וכו'
    return out
def drop(refs):
    for pi, ui, li in sorted(refs, key=lambda r: (r[0], r[1], -1 if r[2] in (None, 'a') else r[2]), reverse=True):
        u = T[pi]['units'][ui]
        if li is None: del T[pi]['units'][ui]
        elif li == 'a':
            u['a'] = ''
            if 'w' in u: u['w'] = ''
        else: del u['l'][li]
changed = True; guard = 0
while changed and guard < 50:
    changed = False; guard += 1
    S = items_seq()
    for i in range(len(S)):
        hit = None
        for n in range(8, 0, -1):
            if i + 2 * n > len(S): continue
            a, b = S[i:i+n], S[i+n:i+2*n]
            if all(x[1] == y[1] and x[2] == y[2] and x[2] and not x[2].startswith('\x00') for x, y in zip(a, b)) and sum(len(x[2]) for x in a) > 3:
                hit = (n, b); break
        if hit:
            n, b = hit
            log.append('%s · ר1 (%d פריטים חוזרים): %s' % (T[b[0][0][0]]['daf'], n, ' | '.join(x[2][:40] for x in b)))
            drop([x[0] for x in b]); changed = True; break
        if i + 1 < len(S) and S[i][1] == 'u' and S[i+1][1] == 'side' and S[i][2] == S[i+1][2] and S[i][2].endswith(':') and len(S[i][2]) <= 25:
            log.append('%s · ר2: %s (שורה, ומיד אחריה כותרת צד זהה)' % (T[S[i][0][0]]['daf'], S[i][2]))
            drop([S[i][0]]); changed = True; break
        if i + 1 < len(S) and S[i][1] == 'dh' and S[i+1][1] == 'm' and S[i][2] == S[i+1][2]:
            log.append('%s · ר3: ד"ה לפני המשנה: %s' % (T[S[i][0][0]]['daf'], S[i][2]))
            drop([S[i][0]]); changed = True; break
# ר4: שורת גוף שכולה "-" (מקף תירוץ שהמנהל העביר לכותרת צד, והפיצול לא נקלט) - כותרת הצד של השורות שאחריה
for pg in T:
    U = []
    for u in pg['units']:
        if u.get('k') == 'u' and any(plain(h) == '-' for c, h in u.get('l') or []):
            cur = dict(u, l=[])
            for c, h in u['l']:
                if plain(h) == '-':
                    if cur['l'] or cur.get('a'): U.append(cur)
                    cur = {'k': 'u', 'a': '-', 'l': []}
                    log.append('%s · ר4: שורת "-" הפכה לכותרת צד' % pg['daf'])
                else: cur['l'].append([c, h])
            if cur['l'] or cur.get('a'): U.append(cur)
        else: U.append(u)
    pg['units'] = U
# יחידה שנשארה בלי חלון ובלי שורות - יוצאת
for pg in T:
    pg['units'] = [u for u in pg['units'] if not (u.get('k') in ('u',) and not u.get('a') and not u.get('l'))]
# מד:: פתיחת "כרוב למזון ותרדין לרפואה - היינו כרוב אף למזון," חוזרת בראש השורה שאחרי "דתניא:"
for pg in T:
    for u in pg['units']:
        if u.get('k') == 'u' and plain(u.get('a')) == 'דתניא:' and u['l'] and plain(u['l'][0][1]).startswith('כרוב למזון ותרדין לרפואה') and 'ששה דברים' in u['l'][0][1]:
            h = u['l'][0][1]; u['l'][0][1] = h[h.index('ששה דברים'):]
            log.append('%s · כרוב למזון ותרדין לרפואה - היינו כרוב אף למזון (פתיחה כפולה לפני דתניא)' % pg['daf'])

# ד. צורה קנונית: שורת "נושא" שבתוך קבוצת שורות היא כותרת נושא משלה (כך הוורד בונה אותה), והשורות שאחריה - קבוצה חדשה
nn = 0
for pg in T:
    U = []
    for u in pg['units']:
        if u.get('k') != 'u' or not any((c or '').split()[:1] in (['nose'], ['dh']) for c, h in u.get('l') or []):
            U.append(u); continue
        cur = dict(u, l=[])
        for c, h in u['l']:
            if (c or '').split()[:1] in (['nose'], ['dh']):
                if cur['l'] or cur.get('a'): U.append(cur)
                U.append({'k': (c or '').split()[0], 'a': h, 'l': [], 's': ' '.join((c or '').split()[1:])}); nn += 1
                cur = {'k': 'u', 'a': '', 'l': []}
            else:
                cur['l'].append([c, h])
        if cur['l'] or cur.get('a'): U.append(cur)
    # קבוצת שורות בלי חלון שבאה מיד אחרי קבוצת שורות - בוורד אלה פסקאות רצופות, וקבוצה אחת
    V = []
    for u in U:
        if V and u.get('k') == 'u' and not u.get('a') and V[-1].get('k') == 'u' and set(u) <= {'k', 'a', 'l', 'id', 's'}:
            V[-1] = dict(V[-1], l=V[-1]['l'] + u['l']); nn += 1; continue
        V.append(u)
    # רווח לפני שורה בתוך תיבת משנה (מב: "ברך על הפת") - אין לו ביטוי בוורד (פסקת משנה אינה "רווח לפני"); היעד בלעדיו
    for u in V:
        if u.get('k') == 'm':
            for ln in u.get('l') or []:
                if 'sp' in (ln[0] or '').split(): ln[0] = ' '.join(x for x in ln[0].split() if x != 'sp').replace('b1', 'b0'); nn += 1
    V = [u for u in V if not (u.get('k') == 'u' and not u.get('l') and not u.get('a'))]   # קבוצה שהתרוקנה
    # חלון כותרת בלי שורות, ומיד אחריו כותרת נושא או ד"ה - בוורד הוא החלון של הכותרת
    W2 = []
    for x in V:
        if W2 and x.get('k') in ('nose', 'dh') and not x.get('w') and W2[-1].get('k') == 'u' and W2[-1].get('a') and not W2[-1].get('l'):
            x = dict(x, w=W2.pop()['a'])
        W2.append(x)
    V = W2
    for u in V:
        if u.get('k') in ('nose', 'dh', 'hatz') and not u.get('s'): u['s'] = 'b0 a0'
    pg['units'] = V
print('שורות נושא שבתוך קבוצה הפכו לכותרת נושא:', nn)
print('נוקו %d:' % len(log)); [print('  ', x) for x in log]
json.dump(log, open('/tmp/claude-0/dups_log.json', 'w'), ensure_ascii=False)
pickle.dump(T, open('/tmp/claude-0/target_pages.pkl', 'wb'))

# טווחי הוורד לכל עמוד: מאחרי פסקת "דף בצד" ועד הבאה
dix = [k for k, b in enumerate(blocks) if b['style'] == 'דף בצד' and b['text'].strip()]
assert len(dix) == len(T) == len(WP), (len(dix), len(T), len(WP))
ranges = []
key = lambda it: WA.sync_key(WA.sync_type(it), ''.join(s for s, _ in WA.sync_runs(it['m'])), it.get('ps'))
chg = []
for n, pg in enumerate(T):
    assert blocks[dix[n]]['text'].strip() == WP[n]['daf'] == pg['daf'], (n, blocks[dix[n]]['text'], pg['daf'])
    tgt, cur = items_of_page(pg), items_of_page(WP[n])
    chg.append([key(x) for x in tgt] != [key(x) for x in cur] or [x['m'] for x in tgt] != [x['m'] for x in cur])
# עמודים רצופים שהשתנו - טווח אחד, וציון הדף שביניהם בתוך היעד
n = 0
while n < len(T):
    if not chg[n]: n += 1; continue
    m = n
    # רצף שינויים; פער של עד שני עמודים שלא השתנו נבלע בתוכו (ציוני דף כפולים, כמו "מה." פעמיים, מבלבלים את בדיקת הגבולות)
    while True:
        if m + 1 < len(T) and chg[m + 1]: m += 1; continue
        break
    lo = dix[n] + 1; hi = dix[m + 1] if m + 1 < len(dix) else len(blocks)
    tgt = []
    for k in range(n, m + 1):
        if k > n: tgt.append({'t': 'P', 'm': blocks[dix[k]]['text'].strip()})
        tgt += items_of_page(T[k])
    ranges.append((lo, hi, tgt)); n = m + 1
print('עמודים לסנכרון:', len(ranges), 'מתוך', len(T))
pickle.dump(ranges, open('/tmp/claude-0/ranges.pkl', 'wb'))
pickle.dump([(pg['daf'], items_of_page(pg)) for pg in T], open('/tmp/claude-0/page_items.pkl', 'wb'))
