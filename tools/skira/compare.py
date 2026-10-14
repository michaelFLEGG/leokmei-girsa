# -*- coding: utf-8 -*-
"""compare.py - השוואת מודלי המיון (שכבה 1) מול מה שהסוקר החזק מצא (שכבה 2).

    uv run python tools/skira/compare.py <מסכת> <מדף> <עד דף>

לכל מודל מיון: כמה פסקאות סימן, כמה מהן אישר הסוקר (דיוק), וכמה מהפסקאות שהסוקר מצא
בהן ממצא אמיתי הוא סימן (כיסוי). בנוסף: אומדן ההחטאה של המיון לפי מדגם ה-10%.
שאלות למחבר אינן נספרות כממצא.
"""
import os, sys, json, glob

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import skira_common as C
import engine


def main():
    slug, d_from, d_to = sys.argv[1:4]
    w = engine.workdir(slug, d_from, d_to)
    meta = C.jload(os.path.join(w, 'meta.json'))
    l2 = meta['layer2']
    allp = {int(i) for g in meta['groups'] for i in g['paragraphs']}
    sample = set()
    # המדגם נקבע ב-prep2 מתוך הפסקאות שלא סומנו: משוחזר מקובץ הקלט (תווית "מדגם")
    for line in open(l2['input'], encoding='utf-8'):
        parts = line.split(' | ')
        if len(parts) > 4 and parts[3].startswith('מדגם'):
            sample.add(int(parts[0]))
    found = {}
    for fn in glob.glob(os.path.join(w, 'review-out', '*.json')):
        for r in C.jload_loose(fn, []):
            if r.get('kind') == 'שאלה למחבר':
                continue
            found.setdefault(int(r['i']), []).append(r)
    res = {'paragraphs': len(allp), 'opus_paragraphs_with_findings': len(found), 'models': {}}
    for fn in sorted(glob.glob(os.path.join(w, 'triage-out', 'T_*.json'))):
        m = os.path.basename(fn)[2:-5]
        fl = {int(r['i']) for r in C.jload_loose(fn, [])}
        hit = fl & set(found)
        res['models'][m] = {'flagged': len(fl), 'confirmed_by_opus': len(hit),
                            'precision': round(len(hit) / len(fl), 2) if fl else None,
                            'recall': round(len(hit) / len(found), 2) if found else None}
    union = set()
    for fn in glob.glob(os.path.join(w, 'triage-out', 'T_*.json')):
        union |= {int(r['i']) for r in C.jload_loose(fn, [])}
    miss = [i for i in sample if i in found]
    res['sample'] = {'size': len(sample), 'with_findings': len(miss),
                     'est_miss_rate': round(len(miss) / len(sample), 3) if sample else None,
                     'est_total_missed_paragraphs': round(len(miss) / len(sample) * (len(allp) - len(union))) if sample else None}
    by_t = {}
    for rows in found.values():
        for r in rows:
            k = r.get('kind', '?')
            by_t[k] = by_t.get(k, 0) + 1
    res['opus_findings_by_kind'] = by_t
    C.jsave(os.path.join(w, 'compare.json'), res)
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
