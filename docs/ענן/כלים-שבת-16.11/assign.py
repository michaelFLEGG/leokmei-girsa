import sys, os, pickle, json, tempfile, re, copy, io, shutil, collections
sys.path.insert(0, '/home/user/leokmei-girsa/tools'); sys.path.insert(0, '/tmp/claude-0/sh')
os.environ.setdefault('LG_DRIVE', tempfile.mkdtemp())
import cloud_word as C, build_site as B
from docx2json import convert
live = json.load(open('live-shabbat.json'))['doc']
rep, d, gone, raw = C.layer('shabbat', 'שבת', live)
def build(docx, doc):
    T = tempfile.mkdtemp(); C.wjson(os.path.join(T, 'shabbat.json'), doc)
    blocks = convert(docx); bj = os.path.join(T, 'b.json'); json.dump(blocks, open(bj, 'w'), ensure_ascii=False)
    cap = {}
    rt, ra, old = B._side_tidy, B._apply_site_edits, B.EDITS_DIR
    def tidy(p, qa): r = rt(p, qa); cap['pages'] = copy.deepcopy(p); return r
    def ase(pages, *a, **k):
        r = ra(pages, *a, **k)
        # מיקום כל עריכה שהוחלה: העמוד שבו יחידת המפתח
        uid2p = {}
        for pi, pg in enumerate(pages):
            for u in pg['units']: uid2p[str(u.get('id'))] = pi
        cap['where'] = {}
        for p in B.PLAN:
            e = p[1]; k = str(e.get('k') or '')
            m = re.match(r'[a-z]*(\d+)', k)
            cap['where'][(C.ekey(e), e.get('t'))] = uid2p.get(m.group(1)) if m else None
        cap['plan_n'] = len(B.PLAN)
        return r
    B._side_tidy, B._apply_site_edits, B.EDITS_DIR = tidy, ase, T
    try: B.build(bj, os.path.join(T, 'shabbat.html'), 'שבת', hagaha=False, sources=None, spacing={})
    finally: B._side_tidy, B._apply_site_edits, B.EDITS_DIR = rt, ra, old
    shutil.rmtree(T, ignore_errors=True)
    return cap
cap = build('shabbat-orig.docx', raw)
w = cap['where']
print('applied', cap['plan_n'], 'located', sum(1 for v in w.values() if v is not None))
pickle.dump(w, open('where.pkl', 'wb'))
