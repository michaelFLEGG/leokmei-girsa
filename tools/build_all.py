"""build_all.py - ממיר כל קובץ וורד ב-input/docx לעמוד מסכת, בונה שער ומעתיק גופנים ל-site/"""
import os, sys, json, shutil, re, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from docx2json import convert
from build_site import build

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IN = os.path.join(ROOT, 'input'); SITE = os.path.join(ROOT, 'site')
os.makedirs(os.path.join(SITE, 'fonts'), exist_ok=True)

SEDER = [('זרעים', ['ברכות']),
         ('מועד', ['שבת', 'עירובין', 'פסחים', 'שקלים', 'יומא', 'סוכה', 'ביצה', 'ראש השנה', 'תענית', 'מגילה', 'מועד קטן', 'חגיגה']),
         ('נשים', ['יבמות', 'כתובות', 'נדרים', 'נזיר', 'סוטה', 'גיטין', 'קידושין']),
         ('נזיקין', ['בבא קמא', 'בבא מציעא', 'בבא בתרא', 'סנהדרין', 'מכות', 'שבועות', 'עבודה זרה', 'הוריות']),
         ('קדשים', ['זבחים', 'מנחות', 'חולין', 'בכורות', 'ערכין', 'תמורה', 'כריתות', 'מעילה', 'תמיד']),
         ('טהרות', ['נדה'])]
ALL = [m for _, ms in SEDER for m in ms]
LATIN = ['berakhot','shabbat','eruvin','pesachim','shekalim','yoma','sukkah','beitzah','rosh-hashanah','taanit','megillah','moed-katan','chagigah',
         'yevamot','ketubot','nedarim','nazir','sotah','gittin','kiddushin','bava-kamma','bava-metzia','bava-batra','sanhedrin','makkot','shevuot','avodah-zarah','horayot',
         'zevachim','menachot','chullin','bekhorot','arakhin','temurah','keritot','meilah','tamid','niddah']
SLUG = dict(zip(ALL, LATIN))

FONT_MAP = {'vilna-xb.otf': ['ExtraBold'], 'vilna-b.otf': ['Vilna-Bold', 'Vilna Bold'], 'vilna-m.ttf': ['Medium'],
            'vilna-r.otf': ['Vilna Regular', 'vilna-regular'], 'frank.ttf': ['frank'], 'franknatan.otf': ['Franknatan'], 'leukmey.otf': ['Leukmey']}

def masechet_of(filename):
    name = filename.replace('.docx', '')
    hits = [m for m in sorted(ALL, key=len, reverse=True) if m in name]
    return hits[0] if hits else None

def main():
    # fonts
    fdir = os.path.join(IN, 'fonts')
    if os.path.isdir(fdir):
        for f in os.listdir(fdir):
            for target, keys in FONT_MAP.items():
                if any(k.lower() in f.lower() for k in keys) and not f.startswith('._'):
                    shutil.copy(os.path.join(fdir, f), os.path.join(SITE, 'fonts', target))
    # masechtot
    built = {}
    ddir = os.path.join(IN, 'docx')
    for f in sorted(os.listdir(ddir)):
        if not f.endswith('.docx') or f.startswith('~$'): continue
        m = masechet_of(f)
        if not m:
            print('לא זוהתה מסכת:', f); continue
        try:
            blocks = convert(os.path.join(ddir, f))
            jp = os.path.join(SITE, SLUG[m] + '.json')
            json.dump(blocks, open(jp, 'w', encoding='utf-8'), ensure_ascii=False)
            r = build(jp, os.path.join(SITE, SLUG[m] + '.html'), m)
            os.remove(jp)
            built[m] = {'file': f, 'pages': r['pages'], 'toc': r['toc'], 'qa': len(r['qa'])}
            print('נבנה', m, r['pages'], 'עמודים', len(r['qa']), 'חריגות')
        except Exception as e:
            print('נכשל', f, repr(e))
    # index
    now = datetime.datetime.now().strftime('%d.%m.%Y %H:%M')
    rows = ''
    for seder, ms in SEDER:
        cells = ''
        for m in ms:
            if m in built:
                b = built[m]
                cells += f'<a class="m on" href="{SLUG[m]}.html"><b>{m}</b><small>{b["pages"]} עמודים · {b["toc"]} נושאים{" · " + str(b["qa"]) + " לבקרה" if b["qa"] else ""}</small></a>'
            else:
                cells += f'<span class="m"><b>{m}</b><small>בעריכה</small></span>'
        rows += f'<section><h2>סדר {seder}</h2><div class="grid">{cells}</div></section>'
    idx = f'''<!DOCTYPE html><html lang="he" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>לאוקמי גירסא · קיצור התלמוד הבבלי</title>
<link href="https://fonts.googleapis.com/css2?family=Frank+Ruhl+Libre:wght@400;500;700;900&display=swap" rel="stylesheet">
<style>@font-face{{font-family:'Vilna';src:url(fonts/vilna-xb.otf);font-weight:900}}@font-face{{font-family:'Frank';src:url(fonts/frank.ttf)}}
body{{margin:0;background:#e9e4d8;color:#1d1a16;font-family:'Frank','Frank Ruhl Libre',serif}}
header{{background:#2b2620;color:#f1ead9;padding:34px 20px 26px;text-align:center}} header h1{{font-family:'Vilna','Frank Ruhl Libre',serif;font-weight:900;font-size:44px;margin:0;letter-spacing:.02em}} header p{{margin:8px 0 0;color:#cfc4ad;font-size:18px}}
main{{max-width:980px;margin:0 auto;padding:18px 16px 60px}} h2{{font-weight:500;font-size:20px;color:#5a5044;border-bottom:1px solid #c9bfa8;margin:26px 0 10px;padding-bottom:4px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px}}
.m{{display:block;background:#f3eee2;border-radius:6px;padding:12px 14px;text-decoration:none;color:#8a7d66;border:1px solid #e0d8c4}} .m.on{{background:#fbf8f1;color:#1d1a16;border-color:#c9a24a;box-shadow:0 1px 4px rgba(0,0,0,.08)}} .m.on:hover{{background:#fff}}
.m b{{display:block;font-size:19px;font-weight:700}} .m small{{font-size:12px;color:#8a7d66}}
footer{{text-align:center;color:#8a7d66;font-size:13px;padding:20px}}</style></head><body>
<header><h1>לאוקמי גירסא</h1><p>קיצור התלמוד הבבלי · שלד הסוגיה בלבד</p></header>
<main>{rows}</main><footer>עודכן {now} · האתר נבנה אוטומטית מקובצי הוורד</footer></body></html>'''
    open(os.path.join(SITE, 'index.html'), 'w', encoding='utf-8').write(idx)
    json.dump({'built': built, 'time': now}, open(os.path.join(SITE, 'status.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(len(built), 'מסכתות נבנו')

if __name__ == '__main__':
    main()
