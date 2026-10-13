# -*- coding: utf-8 -*-
"""stage1_mech.py - מנוע א (מכני, קוד בלבד) על טווח כה.-לה: בלבד, בשם "קלוד - מכני", בעקוב אחר שינויים.

    uv run --with lxml python stage1_mech.py <קלט.docx> <פלט.docx> <יומן.json>

מריץ את המנוע המכני המלא של חולין/מסכתות (engine/laukmi-engine/masechet_1_mechani.py) כשהוא מוגבל לטווח,
ואחריו מחיקת חציצה (***, • • •) הצמודה לכותרת. טאבים אינם נמחקים (הם סמן לשלב הניסוח).
בסוף - בדיקת בריאות: דפים חסרים או כפולים, וציוני הדף ברצף.
"""
import sys, io, os, re, json, runpy, collections
from bkh_common import *
import laukmi_rules
laukmi_rules.BODY |= {"0.1", "0.2", "List Paragraph"}

_orig_init = Doc.__init__
def _init(self, path):
    _orig_init(self, path)
    try:
        patch_range(self)
    except SystemExit:
        pass
Doc.__init__ = _init


def tab_stats(path):
    d = Doc(path)
    patch_range(d)
    n = 0; para = 0
    for p in d.paragraphs():
        t = text_map(p)[0]
        c = t.count('\t')
        n += c; para += 1 if c else 0
    return n, para


def health(path):
    d = Doc(path)
    patch_range(d)
    ps = list(d.paragraphs())
    labels = []
    empty_blocks = []
    cur = None; cnt = 0
    for p in ps:
        st = d.pstyle(p)
        if st == DAF_STYLE:
            if cur is not None and cnt == 0:
                empty_blocks.append(cur)
            cur = mf.live(p).strip(); cnt = 0
            labels.append(cur)
        elif mf.live(p).strip():
            cnt += 1
    exp = []
    letters = ['כה', 'כו', 'כז', 'כח', 'כט', 'ל', 'לא', 'לב', 'לג', 'לד', 'לה']
    for l in letters:
        exp += [l + '.', l + ':']
    dup = [x for x, c in collections.Counter(labels).items() if c > 1]
    return {'labels': labels, 'missing': [x for x in exp if x not in labels], 'extra': [x for x in labels if x not in exp],
            'dup': dup, 'empty_blocks': empty_blocks, 'paragraphs': len(ps)}


def main(src, dst, logp):
    t0, p0 = tab_stats(src)
    code = io.open(os.path.join(REPO, 'engine', 'laukmi-engine', 'masechet_1_mechani.py'), encoding='utf-8').read()
    assert 'laukmi_mech.AUTHOR = "מנוע מכני"' in code
    code = code.replace('laukmi_mech.AUTHOR = "מנוע מכני"', 'laukmi_mech.AUTHOR = %r' % AUTH_MECH)
    tmp = dst + '.m1.docx'
    sys.argv = ['masechet_1_mechani.py', src, tmp]
    os.chdir(os.path.join(REPO, 'engine', 'laukmi-engine'))
    import io as _io, contextlib
    buf = _io.StringIO()
    with contextlib.redirect_stdout(buf):
        exec(compile(code, 'masechet_1_mechani.py', 'exec'), {'__name__': '__main__'})
    mech_out = buf.getvalue()
    # הפרדות צמודות לכותרת
    laukmi_mech.AUTHOR = AUTH_MECH
    buf2 = _io.StringIO()
    with contextlib.redirect_stdout(buf2):
        mf.main(tmp, dst, only_adjacent=True)
    os.remove(tmp)
    t1, p1 = tab_stats(dst)
    h = health(dst)
    out = {'mech': mech_out, 'fmt': buf2.getvalue(), 'tabs_before': t0, 'tabs_after': t1,
           'tab_paras_before': p0, 'tab_paras_after': p1, 'health': h}
    json.dump(out, io.open(logp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(mech_out)
    print(buf2.getvalue())
    print('טאבים: %d (%d פסקאות) -> %d (%d פסקאות)' % (t0, p0, t1, p1))
    print('בריאות:', json.dumps({k: v for k, v in h.items() if k != 'labels'}, ensure_ascii=False))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main(os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]), os.path.abspath(sys.argv[3]))
