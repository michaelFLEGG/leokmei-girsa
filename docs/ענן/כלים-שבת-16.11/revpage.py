import sys, os, zipfile, shutil, tempfile
sys.path.insert(0, '/home/user/leokmei-girsa/tools')
os.environ.setdefault('LG_DRIVE', tempfile.mkdtemp())
from lxml import etree
from docx2json import convert
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
def markers(path):
    b = convert(path); pm = dict(convert.last.get('pmap') or {})
    return [pm[x['i']] for x in b if x['style'] == 'דף בצד' and x['text'].strip()]
def load(path):
    z = zipfile.ZipFile(path); d = etree.fromstring(z.read('word/document.xml')); z.close(); return d
src, dst, out = sys.argv[1], sys.argv[2], sys.argv[3]; pages = [int(x) for x in sys.argv[4].split(',')]
ms, md = markers(src), markers(dst)
ds, dd = load(src), load(dst)
ps = ds.find(W + 'body').findall(W + 'p'); pd = dd.find(W + 'body').findall(W + 'p')
for n in sorted(pages, reverse=True):
    s_lo, s_hi = ms[n] + 1, ms[n + 1]
    d_lo, d_hi = md[n] + 1, md[n + 1]
    body = dd.find(W + 'body')
    anchor = pd[d_lo - 1]   # פסקת ציון הדף
    for p in pd[d_lo:d_hi]: body.remove(p)
    from copy import deepcopy
    for p in reversed(ps[s_lo:s_hi]): anchor.addnext(deepcopy(p))
    pd = body.findall(W + 'p')
zin = zipfile.ZipFile(dst); zout = zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED)
for it in zin.infolist():
    data = zin.read(it.filename)
    if it.filename == 'word/document.xml': data = etree.tostring(dd, xml_declaration=True, encoding='UTF-8', standalone=True)
    zout.writestr(it, data)
zout.close(); print('ok', pages)
