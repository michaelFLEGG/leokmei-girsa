# -*- coding: utf-8 -*-
"""qa_compare.py - בונה קובץ השוואה אחד (HTML פשוט): לפני ואחרי זה לצד זה, לכל מכשיר ולכל עמוד, עם תוצאות הבדיקות.
שימוש: python tools/qa_compare.py docs/qa/2026-10-09"""
import os, sys, io, json, html
root = sys.argv[1]
BN = sys.argv[2] if len(sys.argv) > 2 else 'before'; AN = sys.argv[3] if len(sys.argv) > 3 else 'after'; OUT = sys.argv[4] if len(sys.argv) > 4 else 'compare.html'
B, A = os.path.join(root, BN), os.path.join(root, AN)
def res(d):
    p = os.path.join(d, 'results.json')
    return json.load(io.open(p, encoding='utf-8')) if os.path.exists(p) else {}
rb, ra = res(B), res(A)
def badge(m):
    if not m or 'fatal' in m: return '<b class="x">שגיאה</b>'
    bad = [k for k in ('hscroll', 'rail', 'touch', 'clip', 'lastline') if not m[k]['ok']]
    return '<b class="ok">עבר</b>' if not bad else '<b class="x">נכשל: %s</b>' % ','.join(bad)
out = ['<!DOCTYPE html><html lang="he" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>השוואת צילומים: לפני ואחרי (9.10.2026)</title>',
       '<style>body{font:16px/1.5 system-ui,Arial;margin:0;background:#f3efe4;color:#1b1b1b}main{max-width:1600px;margin:0 auto;padding:16px}h1{font-size:28px}h2{margin:30px 0 8px;border-bottom:2px solid #c9a24a}h3{margin:14px 0 4px}',
       '.pair{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:0 0 18px}.pair figure{margin:0;background:#fff;border:1px solid #d9cfb6;border-radius:8px;padding:6px}.pair img{width:100%;height:auto;display:block}',
       'figcaption{font-size:14px;padding:4px}.ok{color:#1d6b3a}.x{color:#a6322a}.row{display:grid;grid-template-columns:repeat(auto-fill,minmax(420px,1fr));gap:10px}</style></head><body><main>',
       '<h1>לפני ואחרי: מובייל, טאבלט וטעינה</h1><p>"לפני" נבנה מהקוד שהיה חי (main לפני המנה) ו"אחרי" מהקוד החדש. בכל צילום נבדקו: גלילה אופקית, חפיפת כותרות צד, יעדי מגע (44 פיקסלים, מרווח 8), טקסט חתוך, והשורה האחרונה מול הקונסולה.</p>']
devs = sorted(d for d in os.listdir(A) if os.path.isdir(os.path.join(A, d)))
for d in devs:
    out.append('<h2>%s</h2><div class="row">' % html.escape(d))
    pages = sorted(f for f in os.listdir(os.path.join(A, d)) if f.endswith(('.jpg', '.png')))
    for f in pages:
        name = f.rsplit('.', 1)[0]
        bf = os.path.join(B, d, f)
        bimg = ('<img src="%s/%s/%s" loading="lazy">' % (BN, d, f)) if os.path.exists(bf) else '<i>אין</i>'
        aimg = '<img src="%s/%s/%s" loading="lazy">' % (AN, d, f)
        out.append('<div><h3>%s</h3><div class="pair"><figure>%s<figcaption>לפני · %s</figcaption></figure><figure>%s<figcaption>אחרי · %s</figcaption></figure></div></div>' % (
            html.escape(name), bimg, badge(rb.get(d, {}).get(name)), aimg, badge(ra.get(d, {}).get(name))))
    out.append('</div>')
out.append('</main></body></html>')
io.open(os.path.join(root, OUT), 'w', encoding='utf-8').write('\n'.join(out))
print('compare.html', len(devs), 'devices')
