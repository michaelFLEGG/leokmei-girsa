# אילו עריכות הוחלו / נקלטו / נתלשו בבנייה של "מה שהמנהל רואה" (הוורד הישן + כל השכבה)
import sys, json, os, io, copy, tempfile, shutil, pickle
sys.path.insert(0, '/home/user/leokmei-girsa/tools'); sys.path.insert(0, '/tmp/claude-0')
os.environ.setdefault('LG_DRIVE', tempfile.mkdtemp())
import cloud_word as C
import build_site as B
from docx2json import convert
slug, masechet = 'berakhot', 'ברכות'
docx = sys.argv[1]; doc_only = sys.argv[2] if len(sys.argv) > 2 else None
live = json.load(open('/tmp/claude-0/live-berakhot.json'))['doc']
rep, d, gone, raw = C.layer(slug, masechet, live)
doc = raw if not doc_only else json.load(open(doc_only))
T = tempfile.mkdtemp()
C.wjson(os.path.join(T, slug + '.json'), doc)
blocks = convert(docx); bj = os.path.join(T, slug + '_blocks.json'); json.dump(blocks, open(bj, 'w'), ensure_ascii=False)
cap = {}
real_tidy, real_ase, old = B._side_tidy, B._apply_site_edits, B.EDITS_DIR
def tidy(p, qa): r = real_tidy(p, qa); cap['norm'] = C._norm_pages(p); return r
def ase(*a, **k): r = real_ase(*a, **k); cap['plan'] = list(B.PLAN); cap['stat'] = r; return r
B._side_tidy, B._apply_site_edits, B.EDITS_DIR = tidy, ase, T
try: B.build(bj, os.path.join(T, slug + '.html'), masechet, hagaha=False, sources=None, spacing={})
finally: B._side_tidy, B._apply_site_edits, B.EDITS_DIR = real_tidy, real_ase, old
keep = (C.rjson(os.path.join(T, slug + '.json')) or {}).get('edits') or []
sig = lambda e: (C.ekey(e), e.get('t'))
applied = {sig(p[1]) for p in cap['plan']}
keepS = {sig(e) for e in keep}
allE = doc['edits']
taken = [e for e in allE if sig(e) not in keepS]
done = [e for e in allE if sig(e) in applied and sig(e) in keepS]
lost = [e for e in allE if sig(e) in keepS and sig(e) not in applied]
print(json.dumps({'all': len(allE), 'taken': len(taken), 'applied_kept': len(done), 'lost': len(lost), 'stat': cap.get('stat') and {k: cap['stat'].get(k) for k in ('n','done','taken','lost')}, 'plan': len(cap.get('plan') or [])}, ensure_ascii=False))
pickle.dump({'taken': taken, 'done': done, 'lost': lost, 'norm': cap['norm'], 'doc': doc}, open(sys.argv[3] if len(sys.argv) > 3 else '/tmp/claude-0/classes.pkl', 'wb'))
