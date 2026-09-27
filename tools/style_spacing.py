# -*- coding: utf-8 -*-
"""style_spacing.py - המרווחים האנכיים שוורד עצמו מגדיר לכל סגנון.

סוכן סריקת התצוגה צריך לדעת מתי רווח אנכי בדף הוא פגם ומתי הוא נאמנות
למקור. התשובה אינה ניחוש: היא יושבת ב-w:spacing שבתוך word/styles.xml -
before, after ו-line - ונמדדת כאן בנקודות.

הפלט מקובץ לפי התפקיד (ROLE) ולא לפי שם הסגנון, מפני שבדף יש class אחד
לכל תפקיד. לכל תפקיד נלקח המרווח הגדול שנמצא באחד מסגנונותיו, כדי שהסוכן
לא יסמן כפגם רווח שקיים בספר.

ירושה: w:docDefaults ואחריו basedOn, כמו בוורד.
"""
import os, sys, zipfile, collections
from lxml import etree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from styles_map import ROLE, ALIAS

ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
W = '{%s}' % ns['w']


def _spacing_of(el):
    """before/after/line בנקודות מתוך w:pPr, או None לכל שדה שאינו מוגדר."""
    out = {}
    if el is None:
        return out
    sp = el.find('w:spacing', ns)
    if sp is None:
        return out
    for attr, key in (('before', 'before'), ('after', 'after')):
        v = sp.get(W + attr)
        if v is not None:
            try: out[key] = int(v) / 20.0      # twips לנקודות
            except ValueError: pass
    v = sp.get(W + 'line')
    if v is not None:
        try:
            rule = sp.get(W + 'lineRule') or 'auto'
            out['line'] = int(v) / 20.0 if rule in ('exact', 'atLeast') else None
            out['lineRule'] = rule
        except ValueError: pass
    return out


def read(path):
    """מחזיר (per_style, per_role). המידות בנקודות."""
    z = zipfile.ZipFile(path)
    sty = etree.fromstring(z.read('word/styles.xml'))

    dflt = _spacing_of(sty.find('w:docDefaults/w:pPrDefault/w:pPr', ns))

    by_id, name_of, based = {}, {}, {}
    for s in sty.findall('w:style', ns):
        if s.get(W + 'type') != 'paragraph':
            continue
        sid = s.get(W + 'styleId')
        n = s.find('w:name', ns)
        name_of[sid] = ALIAS.get(n.get(W + 'val'), n.get(W + 'val')) if n is not None else sid
        b = s.find('w:basedOn', ns)
        based[sid] = b.get(W + 'val') if b is not None else None
        by_id[sid] = _spacing_of(s.find('w:pPr', ns))

    def resolved(sid, seen=()):
        """ירושה: ברירת המחדל, אחר כך basedOn, ולבסוף הסגנון עצמו."""
        if sid in seen or sid not in by_id:
            return dict(dflt)
        out = resolved(based[sid], seen + (sid,)) if based.get(sid) else dict(dflt)
        out.update({k: v for k, v in by_id[sid].items() if v is not None})
        return out

    per_style = {}
    for sid in by_id:
        per_style[name_of[sid]] = resolved(sid)

    per_role = collections.defaultdict(lambda: {'before': 0.0, 'after': 0.0, 'line': None})
    for name, sp in per_style.items():
        r = ROLE.get(name)
        if not r:
            continue
        t = per_role[r]
        t['before'] = max(t['before'], sp.get('before') or 0.0)
        t['after'] = max(t['after'], sp.get('after') or 0.0)
        if sp.get('line'):
            t['line'] = max(t['line'] or 0.0, sp['line'])
    return per_style, dict(per_role)


if __name__ == '__main__':
    import json
    ps, pr = read(sys.argv[1])
    print(json.dumps({'roles': pr}, ensure_ascii=False, indent=1))
