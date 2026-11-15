# -*- coding: utf-8 -*-
"""למידה מהכרעות "שורה שהתארכה" (פרומפט 41).

כל הכרעה של בעל הפרויקט בדף (קבל, ערוך, הצעה אחרת, השאר) נשמרת בשרת (bakara/dec, מסכת "ov-<מסכת>").
הכלי מושך אותן ושומר במאגר:
  א. data/overflow/decisions/<מסכת>.json - חומר הלמידה לעובד שכותב את הצעות כלים 3-5 (כמו sakem-examples).
  ב. data/overflow/approved-abbr.json - ראשי תיבות שבעל הפרויקט כתב או אישר (בעריכה או בקבלה), ונכנסים לרשימת כלי 2.
הרצה: uv run python tools/overflow/learn.py --slug berakhot   (צריך LEOKMEI_ADMIN_KEY)
"""
import argparse, io, json, os, re, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
ODIR = os.path.join(ROOT, 'data', 'overflow')


def fetch(slug):
    import perush_store as PS
    key = PS.admin_key()
    if not key:
        sys.exit('עצירה: אין מפתח מנהל (LEOKMEI_ADMIN_KEY)')
    req = urllib.request.Request(PS.API + '/bakara/dec?slug=ov-' + slug, headers={'x-admin-key': key, 'User-Agent': 'leokmei-overflow/1.0'})
    with urllib.request.urlopen(req, timeout=60) as r:
        j = json.loads(r.read().decode('utf-8'))
    if not j.get('ok'):
        sys.exit('עצירה: השרת לא החזיר את ההכרעות')
    return (j.get('doc') or {}).get('dec') or {}


def abbr_pairs(was, now):
    """ראשי תיבות שנוספו: מילה אחת עם גרשיים במקום 2-4 מילים רצופות שהאותיות הראשונות שלהן תואמות"""
    A, B = was.split(), now.split()
    out = []
    for w in B:
        m = re.fullmatch(r'([א-ת]+)"([א-ת])', w)
        if not m or w in A:
            continue
        letters = (m.group(1) + m.group(2))
        for n in (2, 3, 4):
            for i in range(len(A) - n + 1):
                seq = A[i:i + n]
                if ''.join(x[0] for x in seq) == letters and ' '.join(seq) not in now:
                    out.append((' '.join(seq), w))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--slug', default='berakhot')
    a = ap.parse_args()
    dec = fetch(a.slug)
    os.makedirs(os.path.join(ODIR, 'decisions'), exist_ok=True)
    rows = sorted(({'id': k, **v} for k, v in dec.items()), key=lambda x: x.get('t', 0))
    io.open(os.path.join(ODIR, 'decisions', a.slug + '.json'), 'w', encoding='utf-8').write(
        json.dumps({'slug': a.slug, 'made': time.strftime('%Y-%m-%d %H:%M'), 'n': len(rows), 'items': rows}, ensure_ascii=False, indent=1))
    ap_fp = os.path.join(ODIR, 'approved-abbr.json')
    cur = json.load(io.open(ap_fp, encoding='utf-8')) if os.path.exists(ap_fp) else {'items': []}
    have = {(x['long'], x['short']) for x in cur['items']}
    added = 0
    for r in rows:
        if r.get('d') in ('ok', 'edit') and r.get('now') and r.get('txt'):
            for lg, sh in abbr_pairs(r['txt'], r['now']):
                if (lg, sh) not in have:
                    cur['items'].append({'long': lg, 'short': sh, 'from': r['id']})
                    have.add((lg, sh))
                    added += 1
    io.open(ap_fp, 'w', encoding='utf-8').write(json.dumps(cur, ensure_ascii=False, indent=1))
    print('הכרעות: %d | ראשי תיבות חדשים: %d' % (len(rows), added))


if __name__ == '__main__':
    main()
