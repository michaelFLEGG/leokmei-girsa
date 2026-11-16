import sys, os, json, tempfile
sys.path.insert(0, '/home/user/leokmei-girsa/tools'); os.environ.setdefault('LG_DRIVE', tempfile.mkdtemp())
import cloud_word as C
p = '/home/user/leokmei-girsa/data/edits/shabbat.json'
rep = C.rjson(p); arch = C.rjson('/home/user/leokmei-girsa/data/word-cloud/ingested/shabbat.json')
done = {}
for e in arch['edits']: done[C.ekey(e)] = max(done.get(C.ekey(e), 0), e.get('t') or 0)
keep = [e for e in rep['edits'] if (e.get('t') or 0) > done.get(C.ekey(e), -1)]
print('data/edits shabbat:', len(rep['edits']), '->', len(keep))
rep['edits'] = keep; C.wjson(p, rep)
