# -*- coding: utf-8 -*-
"""checks.py - שלב 2: הבדיקות שאינן דורשות בינה (קוד בלבד) מעל חבילות הידע.

    uv run --with lxml python tools/hv/checks.py <slug> [--from ל.] [--to מ:] [--out קובץ]

מפיק מועמדים בפורמט ה-sem של מערכת הבקרה (i, kind, mark, note, conf, sev, daf) + שדה hv עם הפניה לשורת חברותא.
הפלט נכתב לריפו הפרטי (candidates/<slug>.json) כי הוא מצביע על שורות חברותא; מועמד שעבר אימות יוצא לציבורי
רק אחרי שער הדלפה (tools/hv/leakgate.py).

מה נבדק:
  א. "תוכן שלא הובא": שורת חברותא עם הסבר ממשי שאין לה מקבילה בקיצור (ציון הדמיון הגבוה ביותר בדף נמוך).
     הבחנה: סימני מסקנה/דין/תירוץ (מסקנה, הלכה, ותירצו, ומבארינן...) = "חסר מהותי" (בינוני, ודאות בינונית);
     אחרת = "השמטה אפשרית" (קל, ודאות נמוכה). הכלל: מסקנה ודין לעולם לא חסרים.
  ב. מפת כיסוי יישור (כמה שורות מותאמות) - לדוח.
"""
import os, sys, re, json, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hv_common as H
from hv_common import C

MISS_BEST = 0.28            # שורה שהדמיון הטוב ביותר שלה בדף מתחת לסף = אין לה מקבילה
CONCL = re.compile(r'(מסקנ|הלכה|למעשה|ומסקינן|ותירצ|ומתרצינן|ומבארינן|תיובתא|תיקו|קמ"ל|קמ״ל|לפיכך|ולכן|אלא ש|הרי ש|'
                   r'ופסק|אסור|מותר|חייב|פטור|כשר|פסול|טמא|טהור)')
DIN = re.compile(r'(הלכה|למעשה|מסקנ|ומסקינן|תיובתא|תיקו)')
STOPQ = re.compile(r'^(מאי טעמא|מאי שנא|מנלן|מנא הני מילי|למה לי|מאי קאמר)\??[.,:\s]*$')


def seg_words(s):
    return len(H.words((s.get('gemara') or '') + ' ' + (s.get('explain') or '')))


def pack_candidates(pk, daf_key_lo=None, daf_key_hi=None):
    out = []
    paras = [p for p in pk['paras'] if p['ext'] == 0]
    if not paras:
        return out
    by_i = {p['i']: p for p in pk['paras']}
    segs = pk['segs']
    # הפסקה האחרונה שהותאמה לפני כל שורה (מקום ההוספה)
    prev_para = None
    for n, s in enumerate(segs):
        if s['para'] is not None:
            prev_para = s['para']
            continue
        txt = ((s.get('gemara') or '') + ' ' + (s.get('explain') or '')).strip()
        nw = seg_words(s)
        if s['best'] >= MISS_BEST or nw < 6 or STOPQ.match(H.norm(s.get('gemara') or '')) and not s.get('explain'):
            continue
        if not (s.get('explain') or '').strip():
            continue                                    # שורה בלי הסבר: אין מה להוסיף
        # שורה בקצה הדף שמתאימה יותר לדף השכן: אינה חסרה
        anchor = prev_para
        if anchor is None or by_i[anchor]['ext'] != 0:
            anchor = next((p['i'] for p in paras), None)
        if anchor is None:
            continue
        ptxt = by_i[anchor]['text']
        mark = ' '.join(ptxt.split()[-5:]) if len(ptxt.split()) > 5 else ptxt
        if mark not in ptxt:
            mark = ptxt[-40:]
        din = bool(DIN.search(txt))
        concl = bool(CONCL.search(txt))
        if din or (concl and nw >= 14):
            sev, conf, why = 'בינוני', 'בינוני', 'חסר מהותי אפשרי (מסקנה/דין/תירוץ)'
        elif nw >= 22:
            sev, conf, why = 'קל', 'נמוך', 'השמטה אפשרית (ייתכן שמכוונת)'
        else:
            continue
        out.append({'i': anchor, 'daf': pk['daf'], 'kind': 'חסר שלב', 'mark': mark, 'conf': conf, 'sev': sev,
                    'note': '%s: בביאור חברותא יש כאן קטע שאין לו מקבילה בקיצור (מקור: חברותא %s שורה %d).' % (why, pk['daf'], s['k']),
                    'hv': {'slug': pk['slug'], 'daf': pk['daf'], 'k': s['k'], 'rule': 'missing', 'words': nw,
                           'din': din, 'best': s['best']}})
    return out


def run(slug, lo=None, hi=None):
    d = os.path.join(H.CHAV, 'packs', slug)
    if not os.path.isdir(d):
        raise SystemExit('עצירה: אין חבילות ידע למסכת ' + slug + ' (הרץ pack.py)')
    k0 = C.daf_key(lo) if lo else None
    k1 = C.daf_key(hi) if hi else None
    cands, st = [], {'pages': 0, 'segs': 0, 'matched': 0}
    for fn in sorted(os.listdir(d)):
        pk = H.jload(os.path.join(d, fn))
        k = C.daf_key(pk['daf'])
        if (k0 is not None and k < k0) or (k1 is not None and k > k1):
            continue
        st['pages'] += 1
        st['segs'] += len(pk['segs'])
        st['matched'] += sum(1 for s in pk['segs'] if s['para'] is not None)
        cands += pack_candidates(pk)
    return cands, st


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('slug')
    ap.add_argument('--from', dest='lo')
    ap.add_argument('--to', dest='hi')
    ap.add_argument('--out')
    a = ap.parse_args()
    cands, st = run(a.slug, a.lo, a.hi)
    out = a.out or os.path.join(H.CHAV, 'candidates', a.slug + '.json')
    H.jsave(out, cands)
    print('עמודים %d · שורות חברותא %d · מותאמות %d (%.0f%%) · מועמדי חסר: %d (מהותי: %d)' % (
        st['pages'], st['segs'], st['matched'], 100.0 * st['matched'] / max(1, st['segs']), len(cands),
        sum(1 for c in cands if c['sev'] == 'בינוני')))
    print('נכתב:', out)


if __name__ == '__main__':
    main()
