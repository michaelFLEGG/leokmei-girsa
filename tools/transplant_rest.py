# -*- coding: utf-8 -*-
"""transplant_rest.py - סבב שני להשתלת הגהות מחבר: מה שהסבב הראשון (apply_transplant)
לא הצליח לעגן.

עיקרון: עיגון רק לפי סדר הפסקאות. קבוצה של הכותב שאין לה פסקה זהה בקובץ הראשי
מעוגנת לפי שתי שכנות מותאמות (לפניה ואחריה):
  א. נוסח בסיס לא ריק, ומספר הפסקאות בין שתי השכנות זהה בשני הקבצים - החלפות
     מינימליות על הפסקה המקבילה, בהשוואה מקלה (דמיון 0.6).
  ב. נוסח בסיס ריק (פסקה חדשה שלו) - הפסקה מוכנסת בשלמותה, במעקב בשמו,
     מיד לפני הפסקה שהותאמה לקבוצה הבאה.
כל השאר (מחיקות שלמות, קבוצות שאין להן שכנה) אינו מוחל ומדווח.
כל שינוי הוא מעקב-שינויים בשם הכותב: בעל הפרויקט יכול לקבל או לדחות.
"""
import sys, re, os, zipfile, difflib, datetime
from copy import deepcopy
import word_apply as w
from word_apply import (W, ns, etree, _pmark, _ptext, _touched, _others_sig, _runs_of,
                        _normalize_ins, _clean_ins_text, _fuzzy_spans, _replace_in_paragraph,
                        _mark_para, backup, _rezip, _ensure_track, convert, is_open_in_word,
                        wait_free, Refused)


def run(path, src, author, masechet, log=print, dry=False, ratio=0.6, only=None, manual=None):
    manual = manual or {}
    if not dry and is_open_in_word(path) and not wait_free(path, log=log):
        raise Refused('הקובץ פתוח בוורד ולא התפנה')
    zs = zipfile.ZipFile(src)
    sdoc = etree.fromstring(zs.read('word/document.xml')); zs.close()
    z = zipfile.ZipFile(path)
    doc = etree.fromstring(z.read('word/document.xml'))
    settings = z.read('word/settings.xml'); z.close()
    HP = list(sdoc.find('w:body', ns).iter(W + 'p'))
    MP = list(doc.find('w:body', ns).iter(W + 'p'))
    groups, i = [], 0
    while i < len(HP):
        j = i
        while j + 1 < len(HP) and _pmark(HP[j])[0] == author:
            j += 1
        groups.append((i, j)); i = j + 1
    key = lambda t: re.sub(r'\s+', '', (t or '').replace('\u00a0', ''))
    norm = lambda t: re.sub(r'\s+', ' ', (t or '').replace('\u00a0', ' ')).strip()
    her = [key(''.join(_ptext(HP[k], author, 'A') for k in range(a, b + 1))) for a, b in groups]
    mine = [key(_ptext(p, author, 'X')) for p in MP]
    sm = difflib.SequenceMatcher(None, her, mine, autojunk=False)
    gmap = {}
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            gmap[blk.a + k] = blk.b + k
    mine_set = {}
    for n, t in enumerate(mine):
        mine_set.setdefault(t, []).append(n)

    todo = []   # (gi, kind, detail)
    skipped = []
    for gi, (a, b) in enumerate(groups):
        ps = HP[a:b + 1]
        if not any(_touched(p, author) for p in ps):
            continue
        A = her[gi]
        Bfull = ''.join(_ptext(p, author, 'X') for p in ps)
        B = key(Bfull)
        if A == B and len(ps) == 1 and _pmark(ps[0]) == (None, None):
            continue
        m = gmap.get(gi)
        lo = max((x for x in gmap if x < gi), default=None)
        hi = min((x for x in gmap if x > gi), default=None)
        if m is None and lo is not None and hi is not None:
            cand = gmap[lo] + (gi - lo)
            if gmap[hi] - cand == hi - gi and cand < len(mine) and mine[cand] == A:
                m = cand
        if m is None and A and len(mine_set.get(A, [])) == 1:
            m = mine_set[A][0]
        if m is not None and _others_sig(ps, author) == _others_sig([MP[m]], author):
            continue            # יטופל בסבב הראשון
        if B and B in mine_set and m is None:
            continue            # כבר מתוקן
        info = (gi, A, Bfull)
        if not B:
            skipped.append(info + ('מחיקה שלמה של פסקה - לא מוחלת',)); continue
        if m is not None:
            skipped.append(info + ('סימון מחבר אחר שונה',)); continue
        if lo is None or hi is None:
            skipped.append(info + ('אין שכנה מותאמת',)); continue
        if not A:
            todo.append((gi, 'insert', (a, b, hi)))
            continue
        cand = gmap[lo] + (gi - lo)
        if gmap[hi] - cand != hi - gi or cand >= len(MP) or len(ps) != 1:
            skipped.append(info + ('מספר הפסקאות בין השכנות אינו זהה',)); continue
        Mfull = ''.join(t for _, t, _ in _runs_of(MP[cand]))
        if difflib.SequenceMatcher(None, key(_ptext(ps[0], author, 'A')), key(Mfull),
                                   autojunk=False).ratio() < ratio:
            skipped.append(info + ('הפסקה הסמוכה אינה דומה דיה',)); continue
        todo.append((gi, 'fuzzy', (cand, _ptext(ps[0], author, 'A'), Bfull)))
    rep = {'todo': [(g, k) for g, k, _ in todo], 'detail': [(g, k, d) for g, k, d in todo], 'MP': MP, 'HP': HP, 'gmap': gmap, 'skipped': skipped, 'applied': [], 'failed': []}
    if dry:
        return rep
    if not todo:
        return rep
    bk = backup(path, masechet); log('גיבוי: ' + bk)
    mx = [int(x) for x in re.findall(r'w:id="(\d+)"', etree.tostring(doc).decode('utf8'))]
    counter = [max(mx + [9000]) + 1000]

    def nextid():
        counter[0] += 1
        return counter[0]
    when = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    expect = [norm(_ptext(p, author, 'X')) for p in MP]
    el_before = list(MP)
    inserts = {}   # אינדקס פסקה ראשי -> רשימת פסקאות חדשות לפניה
    for gi, kind, d in todo:
        if only and gi not in only:
            continue
        if kind == 'fuzzy':
            cand, A, Bfull = d
            M = MP[cand]
            full = ''.join(t for _, t, _ in _runs_of(M))
            spans = _fuzzy_spans(A, _clean_ins_text(Bfull), full)
            if gi in manual:
                anc, txt = manual[gi]
                n = full.find(anc)
                spans = [(n + len(anc),) * 2 + (txt,)] if n >= 0 and full.count(anc) == 1 else None
            if not spans:
                rep['failed'].append((gi, 'לא חושבו החלפות')); continue
            snap = deepcopy(M); ok = True
            for lo, hi, repl in sorted(spans, reverse=True):
                if lo == hi:
                    if lo > 0:
                        find, r2, at = full[lo - 1:lo], full[lo - 1:lo] + repl, lo - 1
                    else:
                        find, r2, at = full[:1], repl + full[:1], 0
                else:
                    find, r2, at = full[lo:hi], repl, lo
                if not find or not _replace_in_paragraph(M, find, r2, author, when, nextid, at=at):
                    ok = False; break
            if not ok:
                M.getparent().replace(M, snap); MP[cand] = snap
                rep['failed'].append((gi, 'ההחלפה נכשלה')); continue
            expect[cand] = norm(_ptext(M, author, 'X'))
            rep['applied'].append((gi, 'fuzzy', Bfull[:60]))
        else:
            a, b, hi = d
            news = []
            for k in range(a, b + 1):
                c = deepcopy(HP[k])
                ppr = c.find('w:pPr', ns)
                if ppr is not None:
                    for ch in ppr.findall('w:pPrChange', ns):
                        ppr.remove(ch)
                if _pmark(HP[k])[0] != author:
                    _mark_para(c, 'ins', author, when, nextid)
                _normalize_ins(c, author)
                for el in c.iter(W + 'ins', W + 'del', W + 'rPrChange', W + 'pPrChange'):
                    el.set(W + 'id', str(nextid()))
                for el in list(c.iter(W + 'bookmarkStart', W + 'bookmarkEnd')):
                    el.getparent().remove(el)
                news.append(c)
            inserts.setdefault(gmap[hi], []).extend(news)
            rep['applied'].append((gi, 'insert', ''.join(_ptext(c, author, 'X') for c in news)[:60]))
    for at_idx in sorted(inserts, reverse=True):
        tgt = el_before[at_idx]
        parent = tgt.getparent(); pos = list(parent).index(tgt)
        for n, c in enumerate(inserts[at_idx]):
            parent.insert(pos + n, c)
        expect[at_idx:at_idx] = [norm(_ptext(c, author, 'X')) for c in inserts[at_idx]]
    tmp = path + '.new'
    _rezip(path, tmp, {'word/document.xml':
                       etree.tostring(doc, xml_declaration=True, encoding='UTF-8', standalone=True),
                       'word/settings.xml': _ensure_track(settings)[0]})
    z2 = zipfile.ZipFile(tmp)
    d2 = etree.fromstring(z2.read('word/document.xml')); z2.close()
    got = [norm(_ptext(p, author, 'X')) for p in d2.find('w:body', ns).iter(W + 'p')]
    ok = got == expect
    if not ok:
        bad = next((n for n in range(min(len(got), len(expect))) if got[n] != expect[n]), None)
        log('סטייה בפסקה %s: ציפינו %r קיבלנו %r' % (bad, (expect[bad] if bad is not None else '')[:70],
                                                        (got[bad] if bad is not None else '')[:70]))
    try:
        convert(tmp)
    except Exception as e:
        ok = False; log('ההמרה נכשלה: %s' % e)
    if not ok:
        os.remove(tmp); log('האימות נכשל. הקובץ לא נגע.')
        rep['verified'] = False; rep['backup'] = bk
        return rep
    os.replace(tmp, path)
    rep['verified'] = True; rep['backup'] = bk
    return rep


if __name__ == '__main__':
    import glob
    sys.stdout.reconfigure(encoding='utf-8')
    author = 'דבורה שירה פלג'
    src = r'C:\Users\Owner\האחסון שלי\לאוקמי גירסא – תלמוד בבלי\- תיקונים שיננא סוכה שני טורים.docx'
    main = glob.glob(os.path.join(os.path.expanduser('~'), 'Desktop', '*', '*סוכה שני*.docx'))[0]
    dry = '--apply' not in sys.argv
    only = set(int(x) for x in sys.argv[sys.argv.index('--only') + 1:]) if '--only' in sys.argv else None
    MAN = {108: ("הכפורת'", ' ואין פנים פחות מטפח'),
           259: ('דחלון בבית,', ' ובית אאף שלא גבוה עשרה דלא גרע מקינופות'),
           640: ('תחתונה למטה מי"ט', " אלמא כשלמעלה מי' ולמטה מכ' אף שאין בה טפח ורחוק שלושה")}
    r = run(main, src, author, 'סוכה', dry=dry, only=only, manual=MAN)
    print('לביצוע:', len(r['todo']))
    for g, k, d in r['detail']:
        print('---', g, k)
        if k == 'fuzzy':
            print('  בסיסו :', d[1][:120]); print('  שלו   :', d[2][:160]); print('  ראשי  :', w._ptext(r['MP'][d[0]], author, 'X')[:160])
        else:
            hi = d[2]; print('  חדש   :', ''.join(w._ptext(r['HP'][k2], author, 'X') for k2 in range(d[0], d[1] + 1))[:120]); print('  לפני  :', w._ptext(r['MP'][r['gmap'][hi]], author, 'X')[:100])
    for s in r['skipped']:
        print('דולג', s[0], '|', s[3], '|', s[2][:70])
    for k in ('applied', 'failed', 'verified', 'backup'):
        if k in r: print(k, r[k])
