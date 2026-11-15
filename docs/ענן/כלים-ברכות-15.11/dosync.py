import sys, os, pickle, shutil, tempfile, json
sys.path.insert(0, '/home/user/leokmei-girsa/tools'); sys.path.insert(0, '/tmp/claude-0')
os.environ.setdefault('LG_DRIVE', tempfile.mkdtemp())
exec(open('/tmp/claude-0/convert_patch.py').read())
import word_apply as WA
from docx2json import convert
ranges = pickle.load(open('/tmp/claude-0/ranges.pkl', 'rb'))
PI = pickle.load(open('/tmp/claude-0/page_items.pkl', 'rb'))
src = '/home/user/leokmei-girsa/input/docx/ברכות בר מצוה יהודה.docx'
dst = '/tmp/claude-0/work/ברכות בר מצוה יהודה.docx'
os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.copyfile(src, dst)
try:
    rep = WA.sync_to_target(dst, 'ברכות', ranges)
    print(json.dumps({k: v for k, v in rep.items() if k != 'ranges'}, ensure_ascii=False)); sys.exit(0)
except WA.Refused as e:
    print('מעבר יחיד נכשל:', str(e)[:300])
# מעבר שני: כל טווח בנפרד, עמוד אחר עמוד, על הקובץ המתעדכן
shutil.copyfile(src, dst)
bad = []
for n, (daf, items) in enumerate(PI):
    b = convert(dst)
    dix = [k for k, x in enumerate(b) if x['style'] == 'דף בצד' and x['text'].strip()]
    lo = dix[n] + 1; hi = dix[n + 1] if n + 1 < len(dix) else len(b)
    have, hk, tk, ops = WA.sync_plan(b, lo, hi, items)
    if hk == tk: continue
    try:
        WA.sync_to_target(dst, 'ברכות', [(lo, hi, items)], log=lambda *a: None)
    except WA.Refused as e:
        bad.append((daf, str(e)[:200]))
print('עמוד אחר עמוד: נכשלו', len(bad)); [print('  ', x) for x in bad]
