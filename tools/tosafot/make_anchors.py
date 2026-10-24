# -*- coding: utf-8 -*-
"""make_anchors.py - עיגון כל תוספות בטקסט הלאוקמי גירסא שבדף (anchors-<פרק>.json).

מודל מציע קטע טקסט (2 עד 6 מילים רצופות מתוך שורות הלאוקמי) שהסימן יבוא אחריו. הקוד אינו סומך עליו:
הוא מנרמל את הקטע כמו הדפדפן (tosafot_ui.js: אותיות בלבד, מקף ורווח כרווח אחד), מוודא שהוא נמצא בדף,
ומחשב בעצמו את מספר המופע. קטע שאינו נמצא ← כלל 3: סוף שורת הלאוקמי שהמודל בחר (ואם גם היא אינה, עצירה).
הכללים: 1 המילה בטקסט, 2 מילה מקבילה, 3 סוף שורת הגמרא הקרובה (כמו בקידושין).

    uv run python tools/tosafot/make_anchors.py sukkah 3 42a 42b   # פרק 3, רק העמודים המצוינים
"""
import os, sys, re, json, io
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import llm
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'tosafot', 'handoff', 'kit'))
from gates import norm_idx, norm_ctx, find_occ   # 24.10.2026: מקור יחיד לנרמול (ערכת החשבון השני)
from build_count import heb_num, daf_key, daf_order
ROOT = os.path.dirname(os.path.dirname(HERE))
NIK = re.compile('[֑-ׇ]')
SYS = ('אתה עוזר לעיגון הערות שוליים בספר לימוד. ענה JSON בלבד, בלי הסבר ובלי גדרות קוד. '
       'אסור להשתמש בקו מפריד ארוך (em dash או en dash).')


def prompt_for(daf, ctxp, tos):
    lines = '\n'.join('%d. %s' % (i + 1, l) for i, l in enumerate(ctxp['lines']))
    gem = '\n'.join('%d. %s' % (i + 1, NIK.sub('', g)) for i, g in enumerate(ctxp['gemara']))
    ts = '\n\n'.join('תוספות מספר %d (על שורת גמרא %d)\nדיבור המתחיל: %s\nפתיחת הפנים: %s' % (r['n'], r['line'], r['dh'], r['text'][:420]) for r in tos)
    return ('להלן עמוד %s בלאוקמי גירסא (קיצור של הגמרא, שורות ממוספרות), שורות הגמרא המקוריות של אותו עמוד, ותוספות שעליהם צריך להניח סימן.\n\n'
            '## שורות הלאוקמי גירסא של העמוד\n%s\n\n## שורות הגמרא המקוריות\n%s\n\n## התוספות\n%s\n\n'
            'לכל תוספות בחר מקום אחד בשורות הלאוקמי שבו הסימן יבוא, מיד אחרי קטע של 2 עד 6 מילים רצופות. '
            'העדיפות: אם דברי הדיבור המתחיל (או מילותיו העיקריות) כתובים בשורות הלאוקמי, הקטע הוא סוף אותם דברים (rule=1). '
            'אם הדיבור אינו כתוב אך יש מקבילה ברורה לאותו עניין, הקטע הוא סוף המקבילה (rule=2). '
            'אם אין, הקטע הוא סוף שורת הלאוקמי הקרובה ביותר לעניין (rule=3). '
            'הקטע חייב להיות מועתק מילה במילה מתוך שורות הלאוקמי כפי שהן כתובות (כולל קיצורים). '
            'אל תכלול סימני פיסוק בקצה. החזר JSON אחד: {"<מספר תוספות>": {"line": <מספר שורת לאוקמי>, "t": "<הקטע>", "rule": 1|2|3, "why": "<משפט קצר>"}, ...}'
            % (daf, lines, gem, ts))


def main():
    slug, perek = sys.argv[1], int(sys.argv[2])
    only = set(sys.argv[3:])
    d = os.path.join(ROOT, 'tosafot', slug)
    count = json.load(io.open(os.path.join(d, 'count-%d.json' % perek), encoding='utf-8'))
    ctx = json.load(io.open(os.path.join(d, 'context.json'), encoding='utf-8'))
    ap = os.path.join(d, 'anchors-%d.json' % perek)
    anchors = json.load(io.open(ap, encoding='utf-8')) if os.path.exists(ap) else {'_comment': 'עוגן הסימן לכל תוספות: t = קטע טקסט כפי שהוא בדף האתר (אותיות בלבד, בלי ניקוד), occ = מספר המופע בדף, rule = 1 המילה בטקסט, 2 מילה מקבילה, 3 סוף שורת הגמרא הקרובה. העוגן אינו מספר תו.'}
    by = {}
    for r in count['items']:
        if only and r['daf'] not in only:
            continue
        by.setdefault(r['dafKey'], []).append(r)
    total = {'in': 0, 'out': 0}
    for dk, tos in by.items():
        if dk not in ctx:
            raise SystemExit('עצירה: אין הקשר לעמוד %s (הרץ extract_context.py)' % dk)
        idx = norm_idx(ctx[dk]['lines'])
        j = llm.call('claude-opus-5-5', SYS, prompt_for(dk, ctx[dk], tos))
        total['in'] += j['in']; total['out'] += j['out']
        txt = j['text'].strip()
        txt = re.sub(r'^```(?:json)?|```$', '', txt, flags=re.M).strip()
        got = json.loads(txt)
        for r in tos:
            a = got.get(str(r['n']))
            if not a:
                raise SystemExit('עצירה: המודל לא החזיר עוגן לתוספות %d (%s)' % (r['n'], dk))
            t, rule, why = a.get('t', '').strip(), int(a.get('rule', 3)), a.get('why', '')
            c = norm_ctx(t)
            occs = find_occ(idx, c) if c else []
            if not occs:
                # נסיגה: סוף השורה שהמודל בחר (כלל 3)
                ln = int(a.get('line', 0))
                lines = ctx[dk]['lines']
                if not (1 <= ln <= len(lines)):
                    raise SystemExit('עצירה: עוגן לא נמצא ושורה לא תקינה לתוספות %d: %r' % (r['n'], a))
                w = norm_ctx(lines[ln - 1]).split(' ')
                for k in (4, 3, 2, 1):
                    c = ' '.join(w[-k:])
                    occs = find_occ(idx, c)
                    if occs:
                        break
                if not occs:
                    raise SystemExit('עצירה: אין עוגן לתוספות %d' % r['n'])
                t, rule, why = c, 3, 'הקטע שהוצע לא נמצא בדף; סוף שורת הלאוקמי %d. (%s)' % (ln, why)
            # אם הקטע חוזר, בוחרים את המופע הקרוב ביותר לשורה שהמודל ציין
            occ = 1
            if len(occs) > 1:
                ln = int(a.get('line', 0))
                if 1 <= ln <= len(ctx[dk]['lines']):
                    pre = len(norm_idx(ctx[dk]['lines'][:ln - 1]))
                    occ = min(range(len(occs)), key=lambda i: abs(occs[i] - pre)) + 1
            anchors[str(r['n'])] = {'daf': dk, 't': c, 'occ': occ, 'rule': rule, 'why': why}
        print(dk, 'עוגנו', len(tos), '(טוקנים: %d/%d)' % (j['in'], j['out']))
    with io.open(ap, 'w', encoding='utf-8') as f:
        json.dump(anchors, f, ensure_ascii=False, indent=1)
    print('סה"כ טוקנים:', total)


if __name__ == '__main__':
    main()
