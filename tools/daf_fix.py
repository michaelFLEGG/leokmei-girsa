# -*- coding: utf-8 -*-
"""daf_fix.py - החלת תיקוני ציוני הדף על הספר. פרומפט 91 (24.11.2026).

רק הקיפול הלילי (tools/fold.py) קורא לכלי הזה, ולכן הספר עדיין נכתב רק בקיפול (CLAUDE.md סעיף א).
המקור: data/daf-fix/<מסכת>.json, שנכתב בידי tools/daf_check.py (הצעות ודאיות) או ביד (הכרעת המנהל):

  {"op": "add", "daf": "נג:", "text": "קמיע - אסור אף במומחה", "page": "נג."}
        פסקת "דף בצד" חדשה לפני הפסקה שמתחילה ב-text (בלי ניקוד ופיסוק), בתוך העמוד שתוויתו page.
        אם לפני הפסקה כותרת צד ("חלון 3") או "משנה בצד" - הציון נכנס לפני הכותרת, כדי שהיחידה לא תיחתך.
  {"op": "fix", "daf_from": "נב.", "daf": "נב:", "text": "ומזין עליהן", "move_before": "וצריך ליזהר", "occ": 2}
        ציון "דף בצד" שתוכנו daf_from והפסקה הראשונה אחריו מתחילה ב-text - מקבל את התוכן daf.
        occ (רשות): כשיש כמה ציונים זהים (תווית כפולה) - הציון ה-occ ביניהם (text ריק).
        move_before (רשות): הציון עובר אל לפני הפסקה הזאת (עד 12 פסקאות לפניו או אחריו).
  {"op": "drop", "daf": "יז.", "occ": 2, "text": "כיצד הרגל"}
        פרומפט 92: ציון כפול מיותר (אותה תווית פעמיים, והשני אינו תחילת עמוד) יוצא מן הספר. רק כשהתווית עדיין
        כפולה (ולכן בטוח לחזרה), ורק אם הפסקה שאחריו מתחילה ב-text (כשניתן). התוכן אינו משתנה.

כל פעולה בודדת בטוחה לחזרה: ציון שכבר קיים (add) או שכבר תוקן (fix) - מדולג. פעולה שלא נמצא לה מקום יחיד -
מדולגת ונרשמת (עצירה רועשת: מופיעה בדוח של הקיפול, לא נבלעת).
השער: אחרי ההחלה, כל פסקה שאינה ציון דף זהה בטקסט ובסדר לספר שלפני, ומספר ציוני הדף גדל בדיוק במספר ההוספות.
"""
import os, sys, io, re, json, copy, zipfile, datetime

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIX = os.path.join(HERE, 'data', 'daf-fix')
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
NIK = re.compile('[֑-ׇ]')


def nz(t):
    t = NIK.sub('', t or '').replace('\xa0', ' ')
    return re.sub(r'[^א-ת0-9]', '', t)


def _dk(d):
    V = {'א': 1, 'ב': 2, 'ג': 3, 'ד': 4, 'ה': 5, 'ו': 6, 'ז': 7, 'ח': 8, 'ט': 9, 'י': 10, 'כ': 20, 'ל': 30, 'מ': 40,
         'נ': 50, 'ס': 60, 'ע': 70, 'פ': 80, 'צ': 90, 'ק': 100, 'ר': 200, 'ש': 300, 'ת': 400}
    m = re.match(r'^\s*([א-ת]+)\s*([.:])\s*$', d or '')
    if not m:
        return None
    n = sum(V.get(c, 0) for c in m.group(1))
    return n * 2 + (1 if m.group(2) == ':' else 0) if n else None


def ops_of(slug):
    p = os.path.join(FIX, slug + '.json')
    if not os.path.exists(p):
        return []
    d = json.load(io.open(p, encoding='utf-8'))
    return [o for o in d.get('ops') or [] if not o.get('off')]


def _ptext(p):
    return ''.join(t.text or '' for t in p.iter(W + 't'))


def _pstyle(p, smap):
    ps = p.find(W + 'pPr/' + W + 'pStyle')
    sid = ps.get(W + 'val') if ps is not None else ''
    return smap.get(sid, sid)


def _style_map(z):
    try:
        st = __import__('lxml.etree', fromlist=['etree']).fromstring(z.read('word/styles.xml'))
    except KeyError:
        return {}, {}
    m, inv = {}, {}
    for s in st.iter(W + 'style'):
        sid = s.get(W + 'styleId')
        nm = s.find(W + 'name')
        name = nm.get(W + 'val') if nm is not None else sid
        m[sid] = name
        inv.setdefault(name, sid)
    return m, inv


def apply(slug, src, dst, log=print):
    """מחיל את התיקונים על src וכותב dst. מחזיר (מספר שהוחל, רשימת דילוגים). אין תיקון - (0, []) ו-dst אינו נכתב."""
    from lxml import etree
    ops = ops_of(slug)
    if not ops:
        return 0, []
    z = zipfile.ZipFile(src)
    doc = etree.fromstring(z.read('word/document.xml'))
    smap, _ = _style_map(z)
    z.close()
    body = doc.find(W + 'body')
    DAF = 'דף בצד'
    ALIAS = ('דף בצד', 'דף בצד מעודכן')

    def paras():
        return body.findall(W + 'p')

    def is_daf(p):
        return _pstyle(p, smap) in ALIAS and _ptext(p).strip()

    def page_ranges(ps):
        """[(תווית, אינדקס הציון, התחלה, סוף)]"""
        mk = [i for i, p in enumerate(ps) if is_daf(p)]
        out = []
        for j, i in enumerate(mk):
            out.append((_ptext(ps[i]).strip(), i, i + 1, mk[j + 1] if j + 1 < len(mk) else len(ps)))
        return out

    before_texts = [(_ptext(p)) for p in paras() if not is_daf(p)]
    n_daf0 = sum(1 for p in paras() if is_daf(p))
    done, skipped, adds, drops = 0, [], 0, 0
    for o in ops:
        ps = paras()
        labels = [(_ptext(ps[i]).strip()) for i in range(len(ps)) if is_daf(ps[i])]
        if o['op'] == 'add':
            if o['daf'] in labels:
                continue                       # כבר קיים
            want = nz(o.get('text'))
            if len(want) < 6:
                skipped.append((o, 'טקסט עוגן קצר מדי')); continue
            cand = []
            kd = _dk(o['daf'])
            for lab, mi, a, b in page_ranges(ps):
                # העמוד שלפני הציון החדש: תווית שקודמת לו בעד שלושה עמודים (כמה ציונים חסרים ברצף משנים את
                # התווית בזמן ההחלה, ולכן לא תווית מדויקת)
                kl = _dk(lab)
                if kd is not None and (kl is None or not (kd - 3 <= kl < kd)):
                    continue
                for i in range(a, b):
                    if nz(_ptext(ps[i])).startswith(want):
                        cand.append(i)
            if len(cand) > 1 and o.get('prev'):
                # פרומפט 92: עוגן שחוזר בעמוד - הפסקה שלפניו מכריעה
                pv = nz(o['prev'])
                cand = [i for i in cand if i > 0 and nz(_ptext(ps[i - 1])).startswith(pv)]
            if len(cand) != 1:
                skipped.append((o, 'נמצאו %d מקומות' % len(cand))); continue
            i = cand[0]
            # כותרת צד / משנה בצד שלפני הפסקה - הציון לפניהן
            while i > 0 and _pstyle(ps[i - 1], smap) in ('חלון 3', 'משנה בצד', 'דף בצד תוכן') and not is_daf(ps[i - 1]):
                i -= 1
            tmpl = next((p for p in ps if is_daf(p)), None)
            if tmpl is None:
                skipped.append((o, 'אין בקובץ פסקת דף בצד לדוגמה')); continue
            np_ = copy.deepcopy(tmpl)
            ts = list(np_.iter(W + 't'))
            ts[0].text = o['daf']
            for t in ts[1:]:
                t.text = ''
            ps[i].addprevious(np_)
            done += 1; adds += 1
            log('  %s: נוסף ציון %s לפני "%s"' % (slug, o['daf'], _ptext(ps[i])[:40]))
        elif o['op'] == 'drop':
            if labels.count(o['daf']) < 2:
                continue                       # כבר אינו כפול
            mks = [mi for lab, mi, a, b in page_ranges(ps) if lab == o['daf']]
            occ = int(o.get('occ') or 2)
            if occ > len(mks):
                skipped.append((o, 'אין ציון %s במקום %d' % (o['daf'], occ))); continue
            mi = mks[occ - 1]
            want = nz(o.get('text'))
            nxt = [x for x in ps[mi + 1:mi + 4] if nz(_ptext(x))][:3]
            if want and not any(nz(_ptext(x)).startswith(want) for x in nxt):
                skipped.append((o, 'הפסקה שאחרי הציון אינה מתחילה בעוגן')); continue
            body.remove(ps[mi])
            done += 1; drops += 1
            log('  %s: ציון כפול %s (מקום %d) הוסר' % (slug, o['daf'], occ))
        elif o['op'] == 'fix':
            if o['daf'] in labels and o['daf_from'] != o['daf'] and labels.count(o['daf_from']) <= 1 and not o.get('move_before'):
                continue                       # כבר תוקן
            want = nz(o.get('text'))
            cand = []
            for lab, mi, a, b in page_ranges(ps):
                if lab != o['daf_from']:
                    continue
                nxt = [ps[i] for i in range(a, b) if nz(_ptext(ps[i]))][:3]    # עד שלוש פסקאות (משנה בצד, כותרת צד)
                if nxt and (not want or any(nz(_ptext(x)).startswith(want) for x in nxt)):
                    cand.append(mi)
            if o.get('occ') and len(cand) >= o['occ'] and o['daf'] not in labels:
                cand = [cand[o['occ'] - 1]]       # הציון ה-occ מבין הזהים (תווית כפולה)
            if len(cand) != 1:
                if o['daf'] in labels:
                    continue
                skipped.append((o, 'נמצאו %d ציונים מתאימים' % len(cand))); continue
            mi = cand[0]
            p = ps[mi]
            ts = list(p.iter(W + 't'))
            ts[0].text = o['daf']
            for t in ts[1:]:
                t.text = ''
            if o.get('move_before'):
                mb = nz(o['move_before'])
                near = [i for i in range(max(0, mi - 12), min(len(ps), mi + 13)) if i != mi and nz(_ptext(ps[i])).startswith(mb)]
                if len(near) == 1:
                    tgt = ps[near[0]]
                    k = near[0]
                    while k > 0 and _pstyle(ps[k - 1], smap) in ('חלון 3', 'משנה בצד') and not is_daf(ps[k - 1]):
                        k -= 1
                    tgt = ps[k]
                    if tgt is not p:
                        body.remove(p)
                        tgt.addprevious(p)
                else:
                    skipped.append((o, 'move_before: נמצאו %d מקומות - הציון תוקן במקומו' % len(near)))
            done += 1
            log('  %s: ציון %s תוקן ל-%s' % (slug, o['daf_from'], o['daf']))
    if not done:
        return 0, skipped
    # השער
    after_texts = [(_ptext(p)) for p in paras() if not is_daf(p)]
    n_daf1 = sum(1 for p in paras() if is_daf(p))
    if after_texts != before_texts or n_daf1 != n_daf0 + adds - drops:
        raise RuntimeError('daf_fix: השער נכשל (פסקאות התוכן השתנו, או מספר הציונים %d->%d ולא %+d)' % (n_daf0, n_daf1, adds - drops))
    tmp = dst + '.tmp'
    zin = zipfile.ZipFile(src)
    zout = zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED)
    for it in zin.infolist():
        data = zin.read(it.filename)
        if it.filename == 'word/document.xml':
            data = etree.tostring(doc, xml_declaration=True, encoding='UTF-8', standalone=True)
        zout.writestr(it, data)
    zin.close(); zout.close()
    os.replace(tmp, dst)
    return done, skipped


def record(slug, n, skipped):
    """רישום ההחלה ב-data/daf-fix/<מסכת>.json (applied / skipped), לדוח ולמנהל."""
    p = os.path.join(FIX, slug + '.json')
    if not os.path.exists(p):
        return
    d = json.load(io.open(p, encoding='utf-8'))
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    d.setdefault('runs', []).append({'when': now, 'applied': n, 'skipped': [{'op': o['op'], 'daf': o['daf'], 'why': w} for o, w in skipped]})
    d['runs'] = d['runs'][-20:]
    json.dump(d, io.open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    # בדיקה יבשה: python tools/daf_fix.py shabbat  -> מחיל על עותק ב-_work ומדפיס
    import shutil, tempfile
    sys.path.insert(0, os.path.join(HERE, 'tools'))
    import cloud_word as C
    slug = sys.argv[1]
    src = C.docx_of(C.masechet_of_slug(slug))
    out = os.path.join(tempfile.mkdtemp(), 'daf-fix-' + slug + '.docx')
    n, sk = apply(slug, src, out)
    print('הוחלו', n, 'דולגו', len(sk))
    for o, w in sk:
        print('  דילוג:', o['op'], o['daf'], '-', w)
    print(out if n else '')
