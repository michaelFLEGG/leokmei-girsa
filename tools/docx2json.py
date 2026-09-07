import sys, json, zipfile, re, collections
from lxml import etree
ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
W = '{%s}' % ns['w']

# שמות סגנון חלופיים שמשמעותם זהה. "דף בצד מעודכן" מופיע בקובץ סוכה בלבד.
STYLE_ALIAS = {'דף בצד מעודכן': 'דף בצד'}

def convert(path):
    z = zipfile.ZipFile(path)
    doc = etree.fromstring(z.read('word/document.xml'))
    sty = etree.fromstring(z.read('word/styles.xml'))
    names = {}
    for s in sty.findall('.//w:style', ns):
        n = s.find('w:name', ns)
        if n is not None:
            names[s.get(W + 'styleId')] = n.get(W + 'val')
    blocks = []
    cur_daf = None; cur_perek = None
    for p in doc.find('w:body', ns).findall('w:p', ns):
        ps = p.find('w:pPr/w:pStyle', ns)
        style = names.get(ps.get(W + 'val'), ps.get(W + 'val')) if ps is not None else 'Normal'
        style = STYLE_ALIAS.get(style, style)
        if style.startswith('toc'):
            continue
        runs = []
        for r in p.iter(W + 'r'):
            # skip deleted text
            if r.getparent().tag == W + 'del':
                continue
            txt = ''.join((t.text or '') if t.tag == W + 't' else ('\t' if t.tag == W + 'tab' else '') for t in r if t.tag in (W + 't', W + 'tab'))
            if not txt:
                continue
            rp = r.find('w:rPr', ns)
            rs = None; b = False
            if rp is not None:
                st = rp.find('w:rStyle', ns)
                if st is not None:
                    rs = names.get(st.get(W + 'val'), st.get(W + 'val'))
                if rp.find('w:b', ns) is not None and rp.find('w:b', ns).get(W + 'val') not in ('0', 'false'):
                    b = True
            runs.append({'t': txt, 'cs': rs, 'b': b})
        # merge adjacent identical runs
        merged = []
        for r in runs:
            if merged and merged[-1]['cs'] == r['cs'] and merged[-1]['b'] == r['b']:
                merged[-1]['t'] += r['t']
            else:
                merged.append(dict(r))
        text = ''.join(r['t'] for r in merged)
        if not text.strip() and style == 'Normal':
            continue
        if style == 'דף בצד':
            cur_daf = text.strip()
        if style == 'פרק':
            cur_perek = text.strip()
        blocks.append({'i': len(blocks), 'style': style, 'daf': cur_daf, 'perek': cur_perek, 'text': text, 'runs': merged})
    return blocks

if __name__ == '__main__':
    blocks = convert(sys.argv[1])
    json.dump(blocks, open(sys.argv[2], 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    c = collections.Counter(b['style'] for b in blocks)
    print(len(blocks), 'blocks'); print(c.most_common())
