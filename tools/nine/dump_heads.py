# -*- coding: utf-8 -*-
"""dump_heads.py <קובץ.docx> <תיקיית פלט> [גודל-חתיכה] - מפיק חתיכות טקסט לסוכן כותרות הנושא.
כל שורה: אינדקס|קוד|טקסט. קודים: g גוף, a עוגן(חלון 3), m משנה, d ד"ה משנה, n נושא, h חציצה, f ציון דף, p פתיחת פרק, r הדרן, o אחר.
החתיכות נחתכות בגבולות פרק, ובתוכו לכל היותר N פסקאות (ברירת מחדל 140), עם חפיפה של 6 פסקאות להקשר (מסומנות c)."""
import sys, os, io, json, hashlib
sys.path.insert(0, r'C:\Users\Owner\leokmei-girsa-nine\tools'); sys.path.insert(0, r'C:\Users\Owner\leokmei-girsa-nine\engine\laukmi-engine')
import laukmi_mech, masechet_fmt as mf
from laukmi_mech import Doc
CODE = {'חלון 3': 'a', 'משניות': 'm', "ד''ה משנה": 'd', 'נושא': 'n', 'חציצה': 'h', 'דף בצד': 'f', 'פתיחת פרק': 'p', 'פרק': 'p', 'פרק שם': 'p',
        'הדרן': 'r', 'הדרן עלך': 'r', 'דפים בפרק ב': 'o', 'מסכת': 'o', 'משנה בצד': 'o', 'Normal': 'g', 'פיסקת תשובה': 'g', 'List Paragraph': 'g', 'רווח לפני': 'g', 'הסבר': 'g'}
path, out = sys.argv[1], sys.argv[2]
N = int(sys.argv[3]) if len(sys.argv) > 3 else 140
os.makedirs(out, exist_ok=True)
doc = Doc(path)
rows = []
for i, p in enumerate(doc.paragraphs()):
    t = mf.live(p)
    st = doc.pstyle(p)
    c = CODE.get(st, 'g' if st.startswith('0.') else 'o')
    rows.append((i, c, t.replace('\n', ' ').strip(), hashlib.md5(t.encode()).hexdigest()[:10]))
json.dump({str(i): h for i, c, t, h in rows}, io.open(os.path.join(out, 'fingerprints.json'), 'w', encoding='utf-8'))
# גבולות פרק: פסקה בקוד p
chunks, cur = [], []
for r in rows:
    if r[1] == 'p' and cur and any(x[1] in 'gam' for x in cur):
        # פתיחה חדשה של פרק: סוגרים רק אם הפסקה הקודמת אינה גם היא פתיחה
        if cur[-1][1] != 'p':
            chunks.append(cur); cur = []
    cur.append(r)
if cur: chunks.append(cur)
files = []
k = 0
for ch in chunks:
    for s in range(0, len(ch), N):
        part = ch[s:s + N]
        ctx = ch[max(0, s - 6):s] if s else []
        k += 1
        fn = os.path.join(out, 'chunk-%03d.txt' % k)
        with io.open(fn, 'w', encoding='utf-8') as f:
            for r in ctx: f.write('%d|c|%s\n' % (r[0], r[2][:300]))
            for r in part:
                if r[2] or r[1] in 'dnhp': f.write('%d|%s|%s\n' % (r[0], r[1], r[2][:600]))
        files.append(fn)
print(len(rows), 'פסקאות', len(files), 'חתיכות')
