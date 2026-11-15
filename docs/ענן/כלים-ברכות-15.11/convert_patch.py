import re, difflib
import word_apply as WA
import styles_map as SM
WA.SYNC_TYPE['חלון 3'] = 'S'; WA.SYNC_TYPE["משנה ד''ה"] = 'D'
WA.SYNC_NEW_STYLE['S'] = 'חלון 3'
if 'נקודה' not in WA.SYNC_PS: WA.SYNC_PS = WA.SYNC_PS + ('נקודה',)
# סגנונות התו של ברכות (אין בה "רקע והסבר תו" ו"ד''ה משנה תו")
WA._SYNC_CS.update({'hs': 'הסבר', 'kt': 'כותרת 3 תו', 'ot': 'אות בודדת תו', 'dm': "משנה ד''ה תו", 'tn': 'תנאי משנה תו'})
ARROW = '→'
def _sig(pairs):
    ch = []
    for t, c in pairs:
        t = (t or '').replace('\xa0', ' ').replace('\t', ' ').replace(ARROW, ' ')
        for x in t:
            ch.append((x, None if x == ' ' else c))
    out, prev = [], None
    for x, c in ch:
        if x == ' ' and out and out[-1][0] == ' ': continue
        out.append((x, c))
    s, cur = '', None
    for x, c in out:
        if c != cur:
            if cur: s += '}'
            if c: s += '{' + c + ':'
            cur = c
        s += x
    if cur: s += '}'
    return s
def _bsig(b):
    pairs = []
    for r in b['runs']:
        if r.get('cs') == WA.NUMBER_STYLE: continue
        c = SM.CS.get(r.get('cs'))
        if r.get('b') and not c: c = 'b'
        pairs.append((r['t'], c))
    # ריצה מעוצבת שכולה רווח (בדף: <i class="kt"> </i>) - הפסקה נכתבת מחדש, כדי שלא תישאר ריצה ריקה
    ws = any(c and not (t or '').strip() for t, c in pairs)
    return _sig(pairs) + ('\x01' if ws else '')
def sync_plan(blocks, lo, hi, target):
    have = [(b['i'], WA._sync_block_type(b)) for b in blocks[lo:hi]]
    have = [(i, t) for i, t in have if t]
    hk = ['X:חציצה' if t == 'X:חציצה' else WA.sync_key(t, WA._sync_block_text(blocks[i]), blocks[i]['style']) + '\x00' + _bsig(blocks[i]) for i, t in have]
    tk = ['X:חציצה' if x['t'] == 'X:חציצה' else WA.sync_key(WA.sync_type(x), ''.join(s for s, _ in WA.sync_runs(x['m'])), x.get('ps')) + '\x00' + _sig(WA.sync_runs(x['m'])) for x in target]
    sm = difflib.SequenceMatcher(None, hk, tk, autojunk=False)
    return have, hk, tk, sm.get_opcodes()
WA.sync_plan = sync_plan

# מספר הקטע (ג.) נכתב כריצה בסגנון "מספר קטע" מתוך היעד עצמו, ולא נשמר מן הפסקה הישנה (שאז היה נכפל)
WA.NUMBER_STYLE = '__none__'
WA._SYNC_T2C['מק'] = 'mk'
WA._SYNC_CS['mk'] = 'מספר קטע'

# סימני מבנה (חציצה, תווית משנה, פתיחת פרק, טווח דפים, הדרן) נכנסים להשוואה, כדי שיזוזו יחד עם הטקסט
import mishna_box as _MB
XST = ('חציצה', 'משנה בצד', 'דפים בפרק ב', 'פתיחת פרק', 'הדרן')
_bt0 = WA._sync_block_type
def _sync_block_type(b):
    st = b['style']
    if st in XST:
        if st == 'משנה בצד' and not _MB.MBW.match(b['text']): return None
        if not b['text'].strip(): return None
        return 'X:' + st
    return _bt0(b)
WA._sync_block_type = _sync_block_type
