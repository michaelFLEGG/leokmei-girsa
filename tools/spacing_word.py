# -*- coding: utf-8 -*-
"""רווח לפני כותרת נושא, ד"ה משנה ופתיחת משנה (8.10.2026, הכרעת בעל הפרויקט:
"כמה נקודות" לפני, למראה נקי). שש נקודות (120 טוויפס).
 א. בהגדרת הסגנונות "נושא" ו-"ד''ה משנה": spacing before >= 120 (אם קטן מכך).
 ב. הפסקה הראשונה של משנה (סגנון "משניות" שלפניה אין משנה ואין כותרת): רווח ישיר
    במעקב (pPrChange).  שום תו של טקסט אינו משתנה.
    uv run --with lxml python tools/spacing_word.py [--אמת]"""
import os, sys, glob, copy, shutil, tempfile, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'engine', 'laukmi-engine'))
import word_apply as wa, laukmi_mech, masechet_fmt as mf
from laukmi_mech import Doc, q
from lxml import etree
from docx2json import convert
laukmi_mech.AUTHOR = 'קלוד'
BEFORE = 120
STYLES = ('נושא', "ד''ה משנה")
SK = set(mf.TRANSPARENT) | {'חלון 3', 'משנה בצד', 'משנה בצד תו'}
MISH = {'משניות', 'תחילת משניות', '0.1 משנה', 'משניות כותרת'}
HEADS = set(mf.HEADINGS) | {"משנה ד''ה", 'נושא משנה', 'חלק משנה מודגשת'}

class D2(Doc):
    def save(self, out):
        with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
            for n in self.names:
                if n == 'word/document.xml':
                    z.writestr(n, etree.tostring(self.doc, xml_declaration=True, encoding='UTF-8', standalone=True))
                elif n == 'word/styles.xml':
                    z.writestr(n, etree.tostring(self.styles, xml_declaration=True, encoding='UTF-8', standalone=True))
                elif n == 'word/settings.xml':
                    z.writestr(n, self._settings_with_track())
                else:
                    z.writestr(n, self.zin.read(n))

def set_style_before(doc, name):
    sid = doc.name2id.get(name)
    if not sid: return 0
    for st in doc.styles.findall(q('style')):
        if st.get(q('styleId')) != sid: continue
        pPr = st.find(q('pPr'))
        if pPr is None:
            pPr = etree.Element(q('pPr')); st.find(q('name')).addnext(pPr)
        sp = pPr.find(q('spacing'))
        if sp is None:
            sp = etree.Element(q('spacing'))
            # spacing אחרי pStyle/keep*/pageBreakBefore/framePr/widowControl/numPr/suppress*/pBdr/shd/tabs
            after = [c for c in pPr if c.tag in [q(t) for t in ('keepNext','keepLines','pageBreakBefore','framePr','widowControl','numPr','suppressLineNumbers','pBdr','shd','tabs','suppressAutoHyphens','kinsoku','wordWrap','overflowPunct','topLinePunct','autoSpaceDE','autoSpaceDN','bidi','adjustRightInd','snapToGrid')]]
            if after: after[-1].addnext(sp)
            else: pPr.insert(0, sp)
        cur = int(sp.get(q('before')) or 0)
        if cur >= BEFORE: return 0
        sp.set(q('before'), str(BEFORE)); sp.attrib.pop(q('beforeAutospacing'), None)
        return 1
    return 0

def set_para_before(doc, p):
    pPr = p.find(q('pPr'))
    if pPr is None:
        pPr = etree.Element(q('pPr')); p.insert(0, pPr)
    sp = pPr.find(q('spacing'))
    if sp is not None and int(sp.get(q('before')) or 0) >= BEFORE: return 0
    old = etree.Element(q('pPr'))
    for ch in pPr:
        if ch.tag not in (q('rPr'), q('sectPr'), q('pPrChange')): old.append(copy.deepcopy(ch))
    if sp is None:
        sp = etree.Element(q('spacing'))
        anchor = None
        for t in ('pStyle','keepNext','keepLines','pageBreakBefore','framePr','widowControl','numPr','suppressLineNumbers','pBdr','shd','tabs','suppressAutoHyphens','bidi'):
            e = pPr.find(q(t))
            if e is not None: anchor = e
        if anchor is not None: anchor.addnext(sp)
        else: pPr.insert(0, sp)
    sp.set(q('before'), str(BEFORE))
    for e in pPr.findall(q('pPrChange')): pPr.remove(e)
    ch = etree.Element(q('pPrChange'))
    ch.set(q('id'), doc.nid()); ch.set(q('author'), laukmi_mech.AUTHOR); ch.set(q('date'), laukmi_mech.DATE)
    ch.append(old); pPr.append(ch)
    return 1

def safe_replace(tmp, path, tries=6):
    import time
    for _ in range(tries):
        try:
            shutil.copy2(tmp, path + '.new'); os.replace(path + '.new', path); os.remove(tmp); return True
        except PermissionError:
            try: os.remove(path + '.new')
            except OSError: pass
            time.sleep(10)
    return False

def run(path, real):
    name = os.path.basename(path)
    doc = D2(path); ps = list(doc.paragraphs()); n = len(ps); st = [doc.pstyle(p) for p in ps]
    ns = sum(set_style_before(doc, s) for s in STYLES)
    nm = 0
    for i in range(n):
        if st[i] != 'משניות' or mf.deleted(ps[i]): continue
        j = i - 1
        while j >= 0 and (mf.deleted(ps[j]) or mf.is_empty(ps[j]) or st[j] in SK): j -= 1
        if j >= 0 and (st[j] in MISH or st[j] in HEADS): continue
        nm += set_para_before(doc, ps[i])
    if not (ns or nm): return name, 0, 0, 'אין מה לשנות'
    tmp = tempfile.mktemp(suffix='.docx'); doc.save(tmp)
    if [b['text'] for b in convert(path)] != [b['text'] for b in convert(tmp)]:
        os.remove(tmp); return name, ns, nm, 'האימות נכשל - לא נכתב'
    if not real: os.remove(tmp); return name, ns, nm, 'יבש, תקין'
    if wa.is_open_in_word(path): os.remove(tmp); return name, ns, nm, 'פתוח בוורד - דולג'
    wa.backup(path, 'רווח ' + os.path.splitext(name)[0][:20])
    doc.zin.close()
    if not safe_replace(tmp, path): return name, 0, [], 'הקובץ נעול (דרייב או וורד) - דולג'
    return name, ns, nm, 'נכתב'

if __name__ == '__main__':
    real = '--אמת' in sys.argv
    for f in sorted(glob.glob(os.path.join(wa.DRIVE, '*.docx'))):
        b = os.path.basename(f)
        if 'בכורות' in b or 'סוכה' in b: print(b, '- דולג (פעיל)'); continue
        print(*run(f, real), sep=' | ', flush=True)
