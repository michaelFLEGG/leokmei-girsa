# בניית "מה שהמנהל רואה" ו"הוורד לבדו" לברכות, בלי נרמול (עם מזהים), לצורך ההמרה
import sys, json, os, io, copy, tempfile, shutil, pickle
sys.path.insert(0, '/home/user/leokmei-girsa/tools')
os.environ.setdefault('LG_DRIVE', tempfile.mkdtemp())
import cloud_word as C

def pages(docx, slug, masechet, doc):
    import build_site as B
    from docx2json import convert
    T = tempfile.mkdtemp(prefix='lg-v-')
    if doc is not None:
        C.wjson(os.path.join(T, slug + '.json'), doc)
    blocks = convert(docx)
    bj = os.path.join(T, slug + '_blocks.json')
    json.dump(blocks, io.open(bj, 'w', encoding='utf-8'), ensure_ascii=False)
    cap = {}
    real_tidy, old_dir = B._side_tidy, B.EDITS_DIR
    def tidy(p, qa):
        r = real_tidy(p, qa); cap['pages'] = copy.deepcopy(p); cap['norm'] = C._norm_pages(p); return r
    real_ase = B._apply_site_edits
    def ase(*a, **k):
        r = real_ase(*a, **k); cap['stat'] = dict(r or {}); return r
    B._side_tidy, B.EDITS_DIR, B._apply_site_edits = tidy, T, ase
    try:
        B.build(bj, os.path.join(T, slug + '.html'), masechet, hagaha=False, sources=None, spacing={})
    finally:
        B._side_tidy, B.EDITS_DIR, B._apply_site_edits = real_tidy, old_dir, real_ase
    shutil.rmtree(T, ignore_errors=True)
    return cap, blocks

if __name__ == '__main__':
    slug, which, docx, out = sys.argv[1:5]
    masechet = C.masechet_of_slug(slug)
    doc = None
    if which == 'admin':
        live = json.load(open('/tmp/claude-0/live-%s.json' % slug))['doc']
        rep, d, gone, raw = C.layer(slug, masechet, live)
        doc = raw
    cap, blocks = pages(docx, slug, masechet, doc)
    pickle.dump({'cap': cap, 'blocks': blocks}, open(out, 'wb'))
    print(which, json.dumps({k: cap.get('stat', {}).get(k) for k in ('n', 'done', 'taken', 'lost')}), len(cap['pages']))
