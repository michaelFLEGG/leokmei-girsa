# -*- coding: utf-8 -*-
"""docx2json.py - ממיר קובץ וורד לרשימת פסקאות.

מחיקה במעקב-אחר-שינויים נקראת כאן כפי שוורד עצמו קורא אותה:
- טקסט שבתוך w:del אינו קיים.
- פסקה שגם תוכנה וגם סימן הפסקה שלה מחוקים - אינה קיימת כלל, ואינה
  משאירה שורה ריקה בדף.
- פסקה שרק סימן הפסקה שלה מחוק מתאחדת עם הפסקה שאחריה, כמו בוורד.
- w:moveFrom הוא מחיקה, w:moveTo הוא טקסט חי.

בלי הקריאה הזאת, מחיקת פסקה בוורד השאירה באתר שורה ריקה, ובעל הפרויקט
נאלץ למחוק מחיקה ממשית - וזו אינה הפיכה.
"""
import sys, json, zipfile, collections
from lxml import etree

sys.path.insert(0, __file__.rsplit('\\', 1)[0].rsplit('/', 1)[0])
from styles_map import ALIAS

ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
W = '{%s}' % ns['w']

# עטיפות שכל טקסט שבתוכן נחשב מחוק
DEAD = (W + 'del', W + 'moveFrom')


def _is_dead(run):
    """האם ההרצה יושבת בתוך מחיקה במעקב (בכל עומק)."""
    el = run.getparent()
    while el is not None and el.tag != W + 'p':
        if el.tag in DEAD:
            return True
        el = el.getparent()
    return False


def _run_text(r):
    """טקסט הריצה: w:t, טאב רגיל, ו-w:ptab ביישור שמאל (טאב-לשמאל של האתר, U+2063).
    ptab ביישור ימין (309 בקבצים הקיימים) אינו חלק מן הטקסט, כמו תמיד."""
    out = []
    for t in r:
        if t.tag == W + 't':
            out.append(t.text or '')
        elif t.tag == W + 'tab':
            out.append('\t')
        elif t.tag == W + 'ptab' and t.get(W + 'alignment') == 'left':
            out.append('\u2063')
    return ''.join(out)


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
    cur_daf = None
    cur_perek = None
    carry = None      # פסקה שסימנה נמחק, וממתינה להתאחד עם הבאה
    dropped = 0       # פסקאות שנמחקו כליל במעקב
    joined = 0        # פסקאות שאוחו עם הבאה אחריהן
    empty = 0         # פסקאות ריקות שאינן נכתבות
    pmap = {}         # מספר הפסקה שכאן, אל מקומה ברשימת ה-w:p שבמסמך
    for pn, p in enumerate(doc.find('w:body', ns).findall('w:p', ns)):
        ps = p.find('w:pPr/w:pStyle', ns)
        style = names.get(ps.get(W + 'val'), ps.get(W + 'val')) if ps is not None else 'Normal'
        style = ALIAS.get(style, style)
        if style.startswith('toc'):
            continue
        # סימן הפסקה עצמו: מחוק, או מוכנס
        mark_del = p.find('w:pPr/w:rPr/w:del', ns) is not None
        runs = []
        for r in p.iter(W + 'r'):
            if _is_dead(r):
                continue
            txt = _run_text(r)
            if not txt:
                continue
            rp = r.find('w:rPr', ns)
            rs = None
            b = False
            if rp is not None:
                st = rp.find('w:rStyle', ns)
                if st is not None:
                    rs = names.get(st.get(W + 'val'), st.get(W + 'val'))
                if rp.find('w:b', ns) is not None and rp.find('w:b', ns).get(W + 'val') not in ('0', 'false'):
                    b = True
            runs.append({'t': txt, 'cs': rs, 'b': b})
        # פסקה שגם תוכנה וגם סימנה מחוקים - אינה קיימת. אין שורה ריקה,
        # ואין צורך במחיקה ממשית מן הקובץ.
        if mark_del and not ''.join(r['t'] for r in runs).strip():
            dropped += 1
            continue
        if carry is not None:
            # הסגנון של הפסקה הקולטת גובר, כמו בוורד כשמוחקים סימן פסקה.
            runs = carry + runs
            carry = None
        if mark_del:
            carry = runs
            joined += 1
            continue
        # merge adjacent identical runs
        merged = []
        for r in runs:
            if merged and merged[-1]['cs'] == r['cs'] and merged[-1]['b'] == r['b']:
                merged[-1]['t'] += r['t']
            else:
                merged.append(dict(r))
        text = ''.join(r['t'] for r in merged)
        # פסקה ריקה אינה נכתבת בשום סגנון, מפני שבדף היא נפתחת כשורה
        # ריקה. היוצא מן הכלל הוא ציון דף ריק: הוא ממצא הגהה של ממש,
        # ולכן הוא נשמר ומדווח.
        if not text.strip() and style != 'דף בצד':
            empty += 1
            continue
        if style == 'דף בצד':
            cur_daf = text.strip()
        if style == 'פרק':
            cur_perek = text.strip()
        pmap[len(blocks)] = pn
        blocks.append({'i': len(blocks), 'style': style, 'daf': cur_daf, 'perek': cur_perek,
                       'text': text, 'runs': merged})
    if carry:
        # סימן הפסקה האחרונה בקובץ נמחק ואין למי להתאחד. אין דילוג שקט:
        # התוכן נשמר בפסקה משלו.
        merged = []
        for r in carry:
            if merged and merged[-1]['cs'] == r['cs'] and merged[-1]['b'] == r['b']:
                merged[-1]['t'] += r['t']
            else:
                merged.append(dict(r))
        blocks.append({'i': len(blocks), 'style': 'Normal', 'daf': cur_daf, 'perek': cur_perek,
                       'text': ''.join(r['t'] for r in merged), 'runs': merged})
    convert.last = {'dropped': dropped, 'joined': joined, 'empty': empty, 'pmap': pmap}
    return blocks


convert.last = {'dropped': 0, 'joined': 0, 'empty': 0, 'pmap': {}}

if __name__ == '__main__':
    blocks = convert(sys.argv[1])
    json.dump(blocks, open(sys.argv[2], 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    c = collections.Counter(b['style'] for b in blocks)
    print(len(blocks), 'blocks', {k: v for k, v in convert.last.items() if k != 'pmap'})
    print(c.most_common())
