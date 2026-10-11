# -*- coding: utf-8 -*-
"""unify_styles.py - איחוד הסגנונות של קובץ ורד ישן להגדרות הקנוניות של דוגמת הזהב (11.10.2026).

מה נעשה:
 א. כל סגנון (פסקה או תו) שבקובץ מקבל את שמו הקנוני לפי טבלת NAME_MAP (שמות דומים כמו "0.1 משנה" / "0.3 משנה" /
    "משנה ד''ה", "0.1" / "0.2" / "0.4"...), לפי התפקיד שנקבע ב-styles_map.ROLE.
 ב. הגדרות הסגנון עצמן (גופן, גודל, מרווח, הזחה) נלקחות מקובץ הזהב, כך שכל המסכתות נראות אותו הדבר, ואין עוד
    "מרווח 240 מדויק" שנשאר מן הקובץ הישן. סגנון שאין לו מקבילה בקובץ הזהב נשמר כהגדרתו, עם מזהה חדש שאינו מתנגש.
 ג. הפניות הסגנון בגוף, בכותרות העליונות והתחתונות ובהערות מתעדכנות למזהים החדשים. הטקסט אינו משתנה.
 ד. סגנון יתום (שאינו בשימוש ואינו בקובץ הזהב) אינו מועבר.
הגדרת סגנון אינה שינוי טקסט ואינה נרשמת בעקוב אחר שינויים.

    uv run --with lxml python tools/unify_styles.py <קלט.docx> <זהב.docx> <פלט.docx> [--dry]
"""
import sys, os, io, re, zipfile, copy, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lxml import etree

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
q = lambda t: '{%s}%s' % (W, t)

# שם סגנון ישן -> שם קנוני
NAME_MAP = {
    # משנה
    '0.1 משנה': 'משניות', '0.2 משנה': 'משניות', '0.3 משנה': 'משניות', '0.4 משנה': 'משניות', '0.4משנה': 'משניות',
    'חלק משנה מודגש': 'משניות', 'חלק משנה מודגשת': 'משניות', 'תחילת משניות': 'משניות',
    'משנה ד\'\'ה': "ד''ה משנה", "ד''ה משנה מודגש אפור": "ד''ה משנה", 'משניות כותרת': "ד''ה משנה",
    # גוף
    '0.1': 'Normal', '0.2': 'Normal', '0.3': 'Normal', '0.4': 'Normal', 'No Spacing': 'Normal',
    'רגיל ללא רווח': 'Normal', 'לפני משנה': 'Normal', 'פרנקיל מודגש': 'Normal',
    'רגיל ורווח': 'רווח לפני', 'מרווח 3': 'רווח לפני', 'רווח אחרי': 'רווח לפני',
    # פרק
    'סוף פרק': 'הדרן עלך',
    # דף
    'דף בצד מעודכן': 'דף בצד',
    # סגנונות תו
    '0.1 משנה תו': 'משניות תו', '0.2 תו': 'משניות תו', '0.4משנה תו': 'משניות תו',
    'אמוראים תו': 'אמוראים תו 2', 'אמוראי משנה תו': 'אמוראים תו 2',
    'חלק משנה מודגש תו': 'משניות תו', 'חלק משנה מודגשת תו': 'משניות תו',
    "משנה ד''ה תו": "ד''ה משנה תו", "ד''ה משנה -2תו": "ד''ה משנה תו", "תנאים בד''ה משנה תו": "ד''ה משנה תו",
    'תנאי משנה תו': 'תנאי המשנה', 'תנאים במשנה': 'תנאי המשנה', 'תנאים במשנה תו': 'תנאי המשנה', 'תנאי המשנה תו': 'תנאי המשנה',
    'הסבר ורקע תו': 'הסבר', 'רקע והסבר תו': 'הסבר', 'הסבר תו': 'הסבר', 'הערה בתו': 'הסבר',
    'הפסוק תו': 'פסוק תו',
    'אות בודדת תו': 'נושא משנה', 'אות מוגדשת תו': 'נושא משנה', 'אות מודגשת תו': 'נושא משנה',
    'נושא תו': 'נושא משנה', 'נושא במשנה תו': 'נושא משנה',
    'כותרת 3 תו': 'חלון 3 תו', 'דף בצד תו': 'דף בצד תו',
    'דף בצד מעודכן תו': 'דף בצד תו',
}
# שמות ששמורים כמות שהם גם אם אינם בקובץ הזהב (מזהים עצמאיים)
KEEP = {'toc 1', 'toc 2', 'toc 3', 'toc 4', 'header', 'footer', 'footnote text', 'footnote reference',
        'Default Paragraph Font', 'Normal Table', 'No List', 'Table Grid', 'Hyperlink'}


def _read(z, name):
    return etree.fromstring(z.read(name)) if name in z.namelist() else None


def styles_by_name(root):
    out = collections.OrderedDict()
    for s in root.findall(q('style')):
        n = s.find(q('name'))
        if n is not None:
            out[n.get(q('val'))] = s
    return out


def canon(name, gold_names):
    """השם הקנוני: אם המפה קובעת - היא; אחרת אותו שם."""
    return NAME_MAP.get(name, name)


def plan(src_path, gold_path):
    zs, zg = zipfile.ZipFile(src_path), zipfile.ZipFile(gold_path)
    ss, gs = _read(zs, 'word/styles.xml'), _read(zg, 'word/styles.xml')
    sn, gn = styles_by_name(ss), styles_by_name(gs)
    zs.close(); zg.close()
    return ss, gs, sn, gn


def used_style_ids(z):
    used = collections.Counter()
    for part in z.namelist():
        if re.match(r'word/(document|header\d*|footer\d*|footnotes|endnotes|numbering)\.xml$', part):
            data = z.read(part)
            for m in re.finditer(rb'<w:(?:pStyle|rStyle|tblStyle) w:val="([^"]+)"', data):
                used[m.group(1).decode('utf-8')] += 1
    return used


def run(src, gold, out, dry=False):
    ss, gs, sn, gn = plan(src, gold)
    zin = zipfile.ZipFile(src)
    used = used_style_ids(zin)
    id2name = {s.get(q('styleId')): n for n, s in sn.items()}
    gold_ids = {s.get(q('styleId')) for s in gn.values()}
    # מזהה חדש לכל מזהה ישן
    idmap, carry, report = {}, [], collections.Counter()
    gid_by_name = {n: s.get(q('styleId')) for n, s in gn.items()}
    taken = set(gold_ids)
    for oid, oname in id2name.items():
        cname = canon(oname, gn)
        if cname in gid_by_name:
            idmap[oid] = gid_by_name[cname]
            if cname != oname: report['מוזג: %s -> %s' % (oname, cname)] += used.get(oid, 0)
        elif oname in gn:
            idmap[oid] = gid_by_name[oname]
        else:
            if used.get(oid, 0) == 0 and oname not in KEEP:
                continue                                  # יתום: לא מועבר
            nid = oid
            while nid in taken: nid = 'T' + nid
            taken.add(nid); idmap[oid] = nid; carry.append((oid, nid, oname))
            report['נשמר כהגדרתו: ' + oname] += used.get(oid, 0)
    if dry:
        return report, idmap, carry
    new = copy.deepcopy(gs)
    for oid, nid, oname in carry:
        el = copy.deepcopy(sn[oname])
        el.set(q('styleId'), nid)
        b = el.find(q('basedOn'))
        if b is not None:
            bv = b.get(q('val'))
            if bv in idmap: b.set(q('val'), idmap[bv])
            else: el.remove(b)
        nx = el.find(q('next'))
        if nx is not None:
            nv = nx.get(q('val'))
            if nv in idmap: nx.set(q('val'), idmap[nv])
            else: el.remove(nx)
        lk = el.find(q('link'))
        if lk is not None: el.remove(lk)
        new.append(el)
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as zo:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == 'word/styles.xml':
                data = etree.tostring(new, xml_declaration=True, encoding='UTF-8', standalone=True)
            elif re.match(r'word/(document|header\d*|footer\d*|footnotes|endnotes|numbering)\.xml$', item.filename):
                txt = data.decode('utf-8')
                def sub(m):
                    return '<w:%s w:val="%s"' % (m.group(1), idmap.get(m.group(2), m.group(2)))
                txt = re.sub(r'<w:(pStyle|rStyle|tblStyle) w:val="([^"]+)"', sub, txt)
                data = txt.encode('utf-8')
            zo.writestr(item, data)
    zin.close()
    return report, idmap, carry


if __name__ == '__main__':
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    rep, idmap, carry = run(a[0], a[1], a[2] if len(a) > 2 else None, dry='--dry' in sys.argv)
    for k, v in sorted(rep.items()):
        print('%6d  %s' % (v, k))
    print('מזהים:', len(idmap), 'מועברים:', len(carry))
