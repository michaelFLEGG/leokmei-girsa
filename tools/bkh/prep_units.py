# -*- coding: utf-8 -*-
"""prep_units.py - הכנת יחידות עבודה (דף אחד = שני עמודים) לסוכני הניסוח.

    uv run --with lxml python prep_units.py <קובץ.docx> <תיקיית-יחידות>

לכל דף בטווח: in.txt (אינדקס|קוד|טקסט, טאב = ⇥), src.md (גמרא, פירוש הגמרא, תוספות), meta.json (טביעות).
האינדקס הוא אינדקס הפסקה בקובץ כולו (רמז בלבד); הזיהוי בפועל הוא לפי הטקסט המדויק והטביעה.
"""
import sys, io, os, re, json, html, glob
from bkh_common import *

CODE = {'חלון 3': 'a', 'משניות': 'm', "ד''ה משנה": 'd', 'נושא': 'n', 'חציצה': 'h', 'דף בצד': 'f', 'פתיחת פרק': 'p', 'פרק': 'p',
        'פרק שם': 'p', 'הדרן': 'r', 'הדרן עלך': 'r', 'דפים בפרק ב': 'o', 'מסכת': 'o', 'משנה בצד': 'o',
        'Normal': 'g', 'פיסקת תשובה': 'g', 'List Paragraph': 'g', 'רווח לפני': 'g', 'הסבר': 'g',
        '0.1': 'g', '0.2': 'g', '0.3': 'g', '0.1 משנה': 'm', '0.2 משנה': 'm', '0.3 משנה': 'm'}
TAG = re.compile(r'<[^>]+>')


def live_tabs(p):
    """הטקסט החי של הפסקה כשכל w:tab מסומן ⇥ (טאבים רצופים = סמן אחד)."""
    out = []
    def walk(el, deleted=False):
        for ch in el:
            tag = ch.tag
            if tag == q('del'):
                continue
            if tag == q('pPr'):
                continue
            if tag == q('t'):
                out.append(ch.text or '')
            elif tag == q('tab'):
                if not (out and out[-1] == TAB_MARK):
                    out.append(TAB_MARK)
            elif tag in (q('r'), q('ins'), q('hyperlink'), q('smartTag'), q('sdt'), q('sdtContent')):
                walk(ch)
    walk(p)
    return ''.join(out)


def gem(h):
    v = {'א': 1, 'ב': 2, 'ג': 3, 'ד': 4, 'ה': 5, 'ו': 6, 'ז': 7, 'ח': 8, 'ט': 9, 'י': 10, 'כ': 20, 'ל': 30, 'מ': 40, 'נ': 50, 'ס': 60}
    return sum(v.get(c, 0) for c in h)


def daf_of_label(lbl):
    return re.sub(r'[.:\s]', '', lbl)


def tosafot_by_daf():
    path = os.path.join(REPO, 'tosafot', 'raw', 'bekhorot.json')
    if not os.path.exists(path):
        return {}
    d = json.load(io.open(path, encoding='utf-8'))
    items = d if isinstance(d, list) else d.get('items') or d.get('segments') or []
    out = {}
    for it in items:
        out.setdefault(it['daf'], []).append(html.unescape(TAG.sub('', it['html'])).strip())
    return out


def locked_texts():
    """נוסחי 'אחרי' של עריכות המחבר עצמו (גיבוי 12.10 + ממתינים שהתקבלו): פסקאות שאין לגעת בהן."""
    out = set()
    for name in ('gold.json', 'learn_pending.json'):
        pth = os.path.join(WORK, name)
        if os.path.exists(pth):
            for x in json.load(io.open(pth, encoding='utf-8')):
                a = norm(x.get('after', ''))
                if len(a) >= 15:
                    out.add(a)
    return out


def main(path, outdir):
    doc = Doc(path)
    lock = locked_texts()
    ps = list(doc.paragraphs())
    lo, hi = find_range(doc)
    pages = sources()
    tos = tosafot_by_daf()
    os.makedirs(outdir, exist_ok=True)
    # חלוקה לדפים לפי ציוני "דף בצד"
    units, cur, curname = [], None, None
    for i in range(lo, hi):
        p = ps[i]
        st = doc.pstyle(p)
        if st == DAF_STYLE:
            lbl = mf.live(p).strip()
            name = re.sub(r'[.:]', '', lbl)
            if name != curname:
                cur = {'daf': name, 'amudim': [], 'rows': []}
                units.append(cur); curname = name
            cur['amudim'].append(lbl)
        if cur is None:
            continue
        t = live_tabs(p).strip('\n')
        if mf.deleted(p):
            continue
        if not t.strip() and st not in ('דף בצד',):
            continue
        c = CODE.get(st, 'g' if st.startswith('0.') else 'o')
        cur['rows'].append((i, c, t))
    manifest = []
    for n, u in enumerate(units, 1):
        d = os.path.join(outdir, 'd%02d' % n)
        os.makedirs(d, exist_ok=True)
        with io.open(os.path.join(d, 'in.txt'), 'w', encoding='utf-8') as f:
            for i, c, t in u['rows']:
                f.write('%d|%s|%s\n' % (i, c, t))
        meta = {'unit': n, 'daf': u['daf'], 'amudim': u['amudim'], 'rows': [{'i': i, 'c': c, 'h': fp(norm(t))} for i, c, t in u['rows']]}
        json.dump(meta, io.open(os.path.join(d, 'meta.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        with io.open(os.path.join(d, 'locked.txt'), 'w', encoding='utf-8') as f:
            for i, c, t in u['rows']:
                if c in ('g', 'a') and norm(t.replace(TAB_MARK, ' ')) in lock:
                    f.write('%d\n' % i)
        with io.open(os.path.join(d, 'src.md'), 'w', encoding='utf-8') as f:
            for lbl in u['amudim']:
                pg = pages.get(lbl) or pages.get(lbl.strip())
                f.write('## עמוד %s\n' % lbl)
                if not pg:
                    f.write('(אין במקורות)\n\n'); continue
                f.write('### גמרא\n%s\n\n' % '\n'.join(html.unescape(TAG.sub('', x)) for x in pg.get('gemara', [])))
                f.write('### פירוש הגמרא\n%s\n\n' % '\n'.join(html.unescape(TAG.sub('', x)) for x in pg.get('perush', [])))
            f.write('### תוספות (להבנת המהלך בלבד, לא להעתקה)\n')
            for lbl in u['amudim']:
                key = '%d%s' % (gem(lbl.strip()[:-1]), 'a' if lbl.strip().endswith('.') else 'b')
                f.write('#### %s\n' % lbl)
                for k, t in enumerate(tos.get(key, []), 1):
                    f.write('%d. %s\n' % (k, t))
                f.write('\n')
        manifest.append({'unit': n, 'daf': u['daf'], 'amudim': u['amudim'], 'rows': len(u['rows'])})
    json.dump(manifest, io.open(os.path.join(outdir, 'manifest.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('יחידות:', len(units), [m['daf'] + ':' + str(m['rows']) for m in manifest])


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main(os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]))
