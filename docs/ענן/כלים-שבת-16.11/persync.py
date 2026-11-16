# המרה עמוד אחר עמוד עם שער לכל עמוד: עמוד שאחרי הכתיבה אינו זהה ליעד - חוזר לוורד המקורי
import sys, os, pickle, shutil, tempfile, json, re
sys.path.insert(0, '/home/user/leokmei-girsa/tools'); sys.path.insert(0, '/tmp/claude-0/sh')
os.environ.setdefault('LG_DRIVE', tempfile.mkdtemp())
exec(open('/tmp/claude-0/sh/convert_patch.py').read())
import word_apply as WA, cloud_word as C, views
from docx2json import convert
_n0 = C._norm_pages
def _fix(x):
    if isinstance(x, dict): return {k: _fix(v) for k, v in x.items()}
    if isinstance(x, list): return [_fix(v) for v in x]
    if isinstance(x, str):
        t = x
        for _ in range(3): t = re.sub(r'<i [^>]*>(\s*)</i>', r'\1', t)
        t = re.sub(r'  +', ' ', t)
        for _ in range(6): t = re.sub(r'<i class="([a-z]+)">([^<]*)</i>( ?)<i class="\1">', r'<i class="\1">\2\3', t)
        return t
    return x
norm = lambda pp: json.dumps(_fix(json.loads(_n0(pp))), ensure_ascii=False, sort_keys=True)
T = pickle.load(open('target_pages.pkl', 'rb'))
PI = pickle.load(open('page_items.pkl', 'rb'))
src = sys.argv[1]; dst = sys.argv[2]
shutil.copyfile(src, dst)
ok, bad = [], []
SKIP = set(json.loads(os.environ.get('SKIP','[]')))
for n, (daf, items) in enumerate(PI):
    b = convert(dst)
    dix = [k for k, x in enumerate(b) if x['style'] == 'דף בצד' and x['text'].strip()]
    lo = dix[n] + 1; hi = dix[n + 1] if n + 1 < len(dix) else len(b)
    have, hk, tk, ops = WA.sync_plan(b, lo, hi, items)
    if hk == tk or n in SKIP: continue
    bak = dst + '.bak'; shutil.copyfile(dst, bak)
    try:
        WA.sync_to_target(dst, 'שבת', [(lo, hi, items)], log=lambda *a: None)
    except WA.Refused as e:
        bad.append((n, daf, 'sync: ' + str(e)[:150])); shutil.copyfile(bak, dst); continue
    cap, _ = views.pages(dst, 'shabbat', 'שבת', None)
    N = cap['pages']
    if len(N) != len(T) or norm([N[n]]) != norm([T[n]]):
        bad.append((n, daf, 'gate')); shutil.copyfile(bak, dst); continue
    # עמודים אחרים לא השתנו?
    ok.append((n, daf))
    print('ok', n, daf, flush=True)
print('converted', len(ok), [d for _, d in ok]); print('reverted', len(bad))
for x in bad: print('  ', x)
pickle.dump({'ok': ok, 'bad': bad}, open(os.environ.get('OUT','persync.pkl'), 'wb'))
