# -*- coding: utf-8 -*-
import sys, re, zipfile, glob, os, difflib
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import word_apply as w
from word_apply import *
W = w.W; ns = w.ns
author = 'דבורה שירה פלג'
src = r'C:\Users\Owner\האחסון שלי\לאוקמי גירסא – תלמוד בבלי\- תיקונים שיננא סוכה שני טורים.docx'
main = glob.glob(os.path.join(os.path.expanduser('~'), 'Desktop', '*', '*סוכה שני*.docx'))[0]
sdoc = etree.fromstring(zipfile.ZipFile(src).read('word/document.xml'))
doc = etree.fromstring(zipfile.ZipFile(main).read('word/document.xml'))
HP = list(sdoc.find('w:body', ns).iter(W + 'p'))
MP = list(doc.find('w:body', ns).iter(W + 'p'))
groups, i = [], 0
while i < len(HP):
    j = i
    while j + 1 < len(HP) and w._pmark(HP[j])[0] == author:
        j += 1
    groups.append((i, j)); i = j + 1
key = lambda t: re.sub(r'\s+', '', (t or '').replace('\u00a0', ''))
her = [key(''.join(w._ptext(HP[k], author, 'A') for k in range(a, b + 1))) for a, b in groups]
mine = [key(w._ptext(p, author, 'X')) for p in MP]
sm = difflib.SequenceMatcher(None, her, mine, autojunk=False)
gmap = {}
for blk in sm.get_matching_blocks():
    for k in range(blk.size):
        gmap[blk.a + k] = blk.b + k
mine_set = {}
for n, t in enumerate(mine):
    mine_set.setdefault(t, []).append(n)
only = set(int(x) for x in sys.argv[1:])
out = 0
for gi, (a, b) in enumerate(groups):
    ps = HP[a:b + 1]
    if not any(w._touched(p, author) for p in ps):
        continue
    A = her[gi]
    Bfull = ''.join(w._ptext(p, author, 'X') for p in ps)
    B = key(Bfull)
    if A == B and len(ps) == 1 and w._pmark(ps[0]) == (None, None):
        continue
    m = gmap.get(gi)
    lo = max((x for x in gmap if x < gi), default=None)
    hi = min((x for x in gmap if x > gi), default=None)
    if m is None and lo is not None and hi is not None:
        cand = gmap[lo] + (gi - lo)
        if gmap[hi] - cand == hi - gi and cand < len(mine) and mine[cand] == A:
            m = cand
    if m is None and A and len(mine_set.get(A, [])) == 1:
        m = mine_set[A][0]
    if m is not None and w._others_sig(ps, author) == w._others_sig([MP[m]], author):
        continue
    if B and B in mine_set and m is None:
        continue
    out += 1
    if only and out not in only:
        continue
    print('=' * 70); print('#', out, 'gi', gi, 'm', m, 'lo/hi', lo, hi, 'paras', len(ps))
    print('  A(base):', w._ptext(ps[0], author, 'A')[:200] if len(ps) == 1 else '(group)')
    print('  B(his) :', Bfull[:300])
    if lo is not None: print('  prev   :', w._ptext(HP[groups[lo][1]], author, 'X')[:80], '-> main', gmap[lo])
    if gi > 0: print('  prevhis:', w._ptext(HP[groups[gi - 1][1]], author, 'X')[:100])
    if gi + 1 < len(groups): print('  nexthis:', w._ptext(HP[groups[gi + 1][0]], author, 'X')[:100])
    if m is not None: print('  MAIN   :', w._ptext(MP[m], author, 'X')[:300])
    elif lo is not None and hi is not None:
        c = gmap[lo] + (gi - lo)
        print('  cand main', c, ':', w._ptext(MP[c], author, 'X')[:200] if c < len(MP) else None)
print('total', out)
