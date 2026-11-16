# מעביר את ההמרה למאגר המקומי (בלי דחיפה): הוורד, ארכיון הקליטה (base), והרשימה
import sys, os, json, pickle, shutil, datetime, tempfile
sys.path.insert(0, '/home/user/leokmei-girsa/tools')
os.environ.setdefault('LG_DRIVE', tempfile.mkdtemp())
import cloud_word as C
R = '/home/user/leokmei-girsa'
F = pickle.load(open(sys.argv[1], 'rb'))
now = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
arch_p = os.path.join(R, 'data/word-cloud/ingested/shabbat.json')
arch = C.rjson(arch_p) or {'v': 1, 'slug': 'shabbat', 'masechet': 'שבת', 'edits': [], 'sty': None}
live = json.load(open('/tmp/claude-0/sh/live-shabbat.json'))['doc']
arch['sty'] = arch.get('sty') or live.get('sty')
have = {(C.ekey(e), e.get('t')) for e in arch['edits']}
n = 0
for e in F['taken']:
    if (C.ekey(e), e.get('t')) in have: continue
    x = dict(e); x['cw'] = now; x['base'] = 1; x.pop('by', None); x.pop('sg', None)
    arch['edits'].append(x); n += 1
C.wjson(arch_p, arch)
shutil.copyfile(sys.argv[2], os.path.join(R, 'input/docx/שבת.docx'))
print('archived', n, 'total', len(arch['edits']))
