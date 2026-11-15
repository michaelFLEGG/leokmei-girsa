import sys, os, pickle, json, tempfile
sys.path.insert(0, '/home/user/leokmei-girsa/tools'); sys.path.insert(0, '/tmp/claude-0')
os.environ.setdefault('LG_DRIVE', tempfile.mkdtemp())
import cloud_word as C, views, re
_n0 = C._norm_pages
def _fix(x):
    if isinstance(x, dict): return {k: _fix(v) for k, v in x.items()}
    if isinstance(x, list): return [_fix(v) for v in x]
    if isinstance(x, str):
        t = x
        for _ in range(3): t = re.sub(r'<i [^>]*>(\s*)</i>', r'\1', t)   # ריצה מעוצבת ריקה - אין לה ביטוי
        t = re.sub(r'  +', ' ', t)
        for _ in range(6): t = re.sub(r'<i class="([a-z]+)">([^<]*)</i>( ?)<i class="\1">', r'<i class="\1">\2\3', t)   # אותו עיצוב משני צדי רווח
        return t
    return x
def _np(pp):
    return json.dumps(_fix(json.loads(_n0(pp))), ensure_ascii=False, sort_keys=True)
C._norm_pages = _np
T = pickle.load(open('/tmp/claude-0/target_pages.pkl', 'rb'))
cap, blocks = views.pages(sys.argv[1], 'berakhot', 'ברכות', None)
pickle.dump({'cap': cap, 'blocks': blocks}, open('/tmp/claude-0/v_new.pkl', 'wb'))
N = cap['pages']
print('same:', C._norm_pages(T) == C._norm_pages(N), 'pages', len(T), len(N))
bad = 0
for k, (a, b) in enumerate(zip(T, N)):
    if C._norm_pages([a]) != C._norm_pages([b]):
        bad += 1
        if bad <= 6:
            ja, jb = json.loads(C._norm_pages([a]))[0]['units'], json.loads(C._norm_pages([b]))[0]['units']
            for i in range(max(len(ja), len(jb))):
                x = ja[i] if i < len(ja) else None; y = jb[i] if i < len(jb) else None
                if x != y:
                    print('PAGE', a['daf'], 'unit', i)
                    if x and y and x.get('l') and y.get('l'):
                        for q in range(max(len(x['l']), len(y['l']))):
                            lx = x['l'][q] if q < len(x['l']) else None; ly = y['l'][q] if q < len(y['l']) else None
                            if lx != ly: print('  T line:', lx); print('  N line:', ly); break
                        if {k: v for k, v in x.items() if k != 'l'} != {k: v for k, v in y.items() if k != 'l'}: print('  T:', {k: v for k, v in x.items() if k != 'l'}); print('  N:', {k: v for k, v in y.items() if k != 'l'})
                    else:
                        print('  T:', json.dumps(x, ensure_ascii=False)[:400]); print('  N:', json.dumps(y, ensure_ascii=False)[:400])
                    break
print('bad pages', bad)
print('adjacent dups in new word:', C.adjacent_dups(sys.argv[1]))
