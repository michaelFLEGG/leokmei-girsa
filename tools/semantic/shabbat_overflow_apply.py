import json, re, html, time, sys
sys.path.insert(0, '/home/claude/sem')
from ov_spec import R
D = json.load(open('/home/claude/dl/dump.json'))
ROWS = D['rows']
for r in ROWS:
    if 'h' in r: r['h'] = re.sub(r'<span class="bkx[^"]*"[^>]*></span>', '', r['h'])
LIVE = {}
for e in D['live']:
    if e.get('op') != 'struct' and e.get('k'):
        o = LIVE.get(e['k'])
        if not o or e.get('t', 0) > o.get('t', 0): LIVE[e['k']] = e
ov = json.load(open('/home/claude/leokmei-girsa/data/overflow/shabbat.json'))
T = [i for i in ov['items'] if i.get('nA4') == 1 and i.get('nLarge') == 2]
NIK = re.compile(r'[֑-ׇ]')
norm = lambda t: re.sub(r'[^א-ת0-9]', '', NIK.sub('', t or ''))
byn = {}
for r in ROWS:
    if r.get('ek') and 'h' in r: byn.setdefault(norm(r['t']), []).append(r)
KEEPC = re.compile(r'^(?:b\d|a\d|sp|in|nose|dh|hr|mu)$')
dcls = lambda c: ' '.join(x for x in c.split() if KEEPC.match(x))
plain = lambda h: html.unescape(re.sub(r'<[^>]+>', '', h))
daf = ''
for r in ROWS:
    if r.get('daf'): daf = r['daf']
    r['_daf'] = daf
t0 = int(time.time() * 1000); n = [0]
def T_(): n[0] += 1; return t0 + n[0]
E, miss = [], []
def text_edit(r, h2):
    old = LIVE.get(r['ek'])
    if old:
        was, wasH = old['was'], old.get('wasH') if old.get('wasH') is not None else html.escape(old['was'], quote=False)
        wasP = old.get('wasP') if old.get('wasP') is not None else dcls(r['c'])
    else:
        was, wasH, wasP = r['t'], r['h'], dcls(r['c'])
    e = {'k': r['ek'], 'was': was, 'now': plain(h2), 'wasH': wasH, 'nowH': h2, 'wasP': wasP, 'daf': r['_daf'], 'ctx': (old or {}).get('ctx', ''), 't': T_()}
    if old and old.get('ps'): e['ps'] = old['ps']; e['psw'] = old.get('psw', '')
    E.append(e)
def stack_at(h, pos):
    st = []
    for m in re.finditer(r'<(/?)(\w+)([^>]*)>', h[:pos]):
        if m.group(1): st and st.pop()
        else: st.append(m.group(0))
    return st
for i, it in enumerate(T):
    spec = R.get(i)
    if spec is None: continue
    cand = byn.get(norm(it['text']), [])
    if len(cand) != 1: miss.append((i, 'row?', len(cand), it['text'][:40])); continue
    r = cand[0]; h = r['h']
    if isinstance(spec, str):
        mk = spec[6:]
        p = h.find(mk)
        if p < 0: miss.append((i, 'split-mark', mk)); continue
        cut = p + len(mk)
        st = stack_at(h, cut)
        h1 = h[:cut].rstrip() + ''.join('</%s>' % re.match(r'<(\w+)', s).group(1) for s in reversed(st))
        h2 = ''.join(st) + h[cut:]
        h1 = re.sub(r'<i class="[^"]*">\s*</i>', '', h1); h2 = re.sub(r'<i class="[^"]*">\s*</i>', '', h2)
        if plain(h1).strip() + ' ' + plain(h2).strip() != ' '.join(r['t'].split()) and norm(plain(h1) + plain(h2)) != norm(r['t']):
            miss.append((i, 'split-text')); continue
        tt = T_(); cl = dcls(r['c'])
        E.append({'k': 's' + str(tt), 't': tt, 'op': 'struct', 'kind': 'split', 'texts': [r['t']],
                  'res': [[cl, h1], [cl, h2]], 'resT': [plain(h1), plain(h2)], 'daf': r['_daf']})
        continue
    h2 = h; ok = True
    for item in spec:
        if item[0] == 'RAW':
            if item[1] in h2: h2 = h2.replace(item[1], item[2], 1); continue
            ok = False; miss.append((i, 'raw')); break
        f, rep = item
        segs = re.split(r'(<[^>]+>)', h2)
        done = False
        for k, s in enumerate(segs):
            if s.startswith('<'): continue
            if f in s:
                segs[k] = s.replace(f, rep, 1); done = True; break
        if not done:
            ok = False; miss.append((i, 'find', f)); break
        h2 = ''.join(segs)
    if ok: text_edit(r, h2)
# שורה נעולה במשנה שנשברה בגלל "נושא משנה" (משקל 900): חוזרת להדגשה הרגילה
for r in ROWS:
    if r.get('ek') == 'u7709.1':
        text_edit(r, r['h'].replace('<i class="ns">', '<i class="b">'))
print('edits', len(E), 'miss', miss)
json.dump({'slug': 'shabbat', 'edits': E}, open('/home/claude/leokmei-girsa/data/semantic/shabbat-21.11-ov.json', 'w'), ensure_ascii=False)
