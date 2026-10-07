"""build_all.py - ממיר כל קובץ וורד ב-input/docx לעמוד מסכת, בונה שער ומעתיק גופנים ל-site/"""
import os, sys, json, shutil, re, html, datetime, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from docx2json import convert
from build_site import build
import hagaha
import font_unicode
import style_spacing

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

# הגופנים שקובצי הוורד מבקשים, ושם הקובץ שהם מועתקים אליו באתר.
# ההתאמה נעשית לפי המפתח הארוך ביותר שנמצא בשם הקובץ, כדי ש"Franknatan" לא ייחשב "frank".
FONT_MAP = {'vilna-xb.otf': ['ExtraBold'], 'vilna-b.otf': ['Vilna-Bold', 'Vilna Bold'], 'vilna-m.ttf': ['Medium'],
            'vilna-r.otf': ['Vilna Regular', 'vilna-regular'], 'vilna-g.ttf': ['DBSVILNA'],
            'frank.ttf': ['frank.ttf', 'FrankRuehl'], 'franknatan.otf': ['Franknatan'], 'leukmey.otf': ['Leukmey'],
            # ההדגשה של פרנקריהל נעשית עד כה בידי הדפדפן, והיא קיצונית
            # ומכוערת. הגופן המודגש של PFT (ברישיון שבידי בעל הפרויקט)
            # בא במקומה. הוא גדול בהרבה ליחידת em, וגיליון הסגנונות
            # מקטין אותו ב-size-adjust לפי גובה האותיות שנמדד.
            # ‏PFT_Frank Regular אינו ממופה במתכוון: גוף הטקסט נשאר
            # פרנקריהל, שעליו כויל היחס הנעול של רוחב השורה.
            'frank-b.ttf': ['PFT_Frank Bold']}

GEM = {'א':1,'ב':2,'ג':3,'ד':4,'ה':5,'ו':6,'ז':7,'ח':8,'ט':9,'י':10,'כ':20,'ל':30,'מ':40,
       'נ':50,'ס':60,'ע':70,'פ':80,'צ':90,'ק':100,'ר':200,'ש':300,'ת':400}

def daf_key(d):
    """מפתח מספרי לציון דף: גימטריה כפול שתיים, ועוד אחד לעמוד ב. זהה לחישוב שב-build_site."""
    if not d: return None
    t = d.strip()
    amud = 1 if t.endswith(':') else 0
    t = t.rstrip('.:').replace('"', '').replace("'", '').replace('\u05f4', '').replace('\u05f3', '').strip()
    n = sum(GEM.get(c, 0) for c in t)
    return n * 2 + amud if n else None

# קיצורי מסכת כפי שהם מופיעים בשמות הקבצים
ABBR = {'בבא קמא': ["ב''ק", 'ב"ק', 'ב\u05f4ק'],
        'בבא מציעא': ["ב''מ", 'ב"מ', 'ב\u05f4מ'],
        'בבא בתרא': ["ב''ב", 'ב"ב', 'ב\u05f4ב'],
        'סנהדרין': ["סנה'", 'סנה\u05f3'],
        'עבודה זרה': ["ע''ז", 'ע"ז', 'ע\u05f4ז'],
        'ראש השנה': ["ר''ה", 'ר"ה', 'ר\u05f4ה'],
        'מועד קטן': ["מו''ק", 'מו"ק', 'מו\u05f4ק']}

# מסכת שנבנית משני קובצי מקור. לכל חלק: סימן זיהוי בשם הקובץ, ומאיזה מפתח דף עד איזה.
# סנהדרין: הקובץ הראשון מוגה עד סוף דף סח. (לפני פרק בן סורר), והשני נוטל משם ועד סוף המסכת.
MERGE = {'סנהדרין': [('עד בן סורר', None, 136),
                     ('עז.', 137, None)]}

# קובץ אחד הנושא שתי מסכתות. החיתוך נמדד ואינו מנוחש: הוא נעשה במקום היחיד
# שבו ציון הדף חוזר לתחילת המסכת. אם לא נמצאה נקודה כזאת, הקובץ נבנה כמסכת אחת.
SPLIT = {("ע''ז הוריות", 'ע"ז הוריות', 'ע״ז הוריות'): ['עבודה זרה', 'הוריות']}

def split_of(filename):
    """מחזיר את רשימת המסכתות שבקובץ, אם שמו מסמן קובץ שתי מסכתות."""
    for signs, ms in SPLIT.items():
        if any(k in filename for k in signs):
            return ms
    return None


def split_file(path, masechtot):
    """חותך קובץ שתי מסכתות במקום שבו ציון הדף חוזר לתחילת המסכת.
    מחזיר None אם מספר נקודות החיתוך אינו כמספר המסכתות פחות אחת."""
    blocks = convert(path)
    cuts, prev = [], None
    for b in blocks:
        k = daf_key(b['daf'])
        if k is None: continue
        if prev is not None and k <= 6 and prev - k > 20:
            cuts.append(b['i'])
        prev = k
    if len(cuts) != len(masechtot) - 1:
        return None
    bounds = [0] + cuts + [len(blocks)]
    return [(m, [dict(b, i=j) for j, b in enumerate(blocks[bounds[n]:bounds[n + 1]])])
            for n, m in enumerate(masechtot)]


def masechet_of(filename):
    name = filename.replace('.docx', '')
    hits = [m for m in sorted(ALL, key=len, reverse=True) if m in name]
    if hits:
        return hits[0]
    for m, keys in ABBR.items():
        if any(k in name for k in keys):
            return m
    return None

def merge_masechet(m, files, ddir):
    """מאחד כמה קובצי מקור למסכת אחת לפי טווחי הדפים שנקבעו ב-MERGE.
    בלי כלל איחוד אין ניחוש: נבנה הקובץ הגדול, והשאר מדווח בקול."""
    plan = MERGE.get(m)
    if not plan:
        big = max(files, key=lambda f: os.path.getsize(os.path.join(ddir, f)))
        print('אזהרה: יותר מקובץ אחד למסכת', m, 'ואין כלל איחוד. נבנה', big,
              '| לא נכללו:', ', '.join(f for f in files if f != big))
        return convert(os.path.join(ddir, big)), big
    out, used = [], []
    for sign, lo, hi in plan:
        match = [f for f in files if sign in f]
        if not match:
            print('אזהרה: כלל האיחוד של', m, 'מחפש', sign, 'ולא נמצא קובץ מתאים'); continue
        f = match[0]; used.append(f)
        blocks = convert(os.path.join(ddir, f))
        started, pending, last = False, [], None
        for b in blocks:
            k = daf_key(b['daf'])
            if k is not None: last = k
            k = k if k is not None else last   # ציון דף ריק יורש את מקומו, ואינו מפיל את מה שאחריו
            if k is None:
                keep = not out          # פתיח נלקח מן החלק הראשון בלבד
            else:
                keep = (lo is None or k >= lo) and (hi is None or k <= hi)
            if not keep:
                if b['style'] == 'פרק': pending = [b]
                elif b['style'] == 'פרק שם': pending.append(b)
                continue
            if not started:             # החזרת כותרת הפרק שנחתכה יחד עם הפתיח
                started = True
                for pb in pending: out.append(dict(pb, i=len(out)))
                pending = []
            out.append(dict(b, i=len(out)))
    for f in files:
        if f not in used:
            print('אזהרה: הקובץ', f, 'שייך למסכת', m, 'ואינו מכוסה בכלל האיחוד')
    return out, ' + '.join(used)

def main():
    # בנייה חלקית. בנייה מלאה של 26 מסכתות נמדדה ב-14 דקות, וזה זמן
    # שאי אפשר להמתין לו כשמתפרסם תיקון בודד מן האתר. עם --only נבנות
    # רק המסכתות שנמסרו, ושאר הרשומות לשער נקראות מ-status.json שכבר
    # יש באתר. אם אין שם, הבנייה החלקית עוצרת בקול: שער חסר מסכתות
    # גרוע מהמתנה.
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', action='append', default=[],
                    help='מזהה מסכת (slug) לבנייה. אפשר לחזור על הדגל')
    args = ap.parse_args()
    only = set()
    for v in args.only:
        only |= {x.strip() for x in v.split(',') if x.strip()}
    preconv = {}
    # fonts
    fdir = os.path.join(IN, 'fonts')
    # בבנייה חלקית אין טעם להטליא שוב את הגופנים: הם כבר באתר, והטלאה
    # חוזרת לקחה ארבעים שניות מתוך שבעים וחמש.
    if only and all(os.path.exists(os.path.join(SITE, 'fonts', t)) for t in FONT_MAP):
        fdir = None
    if fdir and os.path.isdir(fdir):
        for f in sorted(os.listdir(fdir)):
            if f.startswith('._'): continue
            best = None
            for target, keys in FONT_MAP.items():
                for k in keys:
                    if k.lower() in f.lower() and (best is None or len(k) > best[1]):
                        best = (target, len(k))
            if best:
                src = os.path.join(fdir, f); dst = os.path.join(SITE, 'fonts', best[0])
                # כל גופן נכנס דרך תיקון: (א) גופן עברי מן הדור הישן אינו
                # יודע יוניקוד ואותיותיו יושבות במשבצות לטיניות, ולכן
                # נוספת לו טבלת יוניקוד; (ב) רוחב פסיעה מופרך נחתך.
                # שני הדברים התגלו בסוכן סריקת התצוגה, ולא בעין.
                try:
                    note = font_unicode.repair(src, dst)
                    if note:
                        print('הגופן', best[0] + ':', note)
                except Exception as e:
                    print('אזהרה: תיקון הגופן', best[0], 'נכשל -', e)
                    shutil.copy(src, dst)
        absent = [t for t in FONT_MAP if not os.path.exists(os.path.join(SITE, 'fonts', t))]
        if absent: print('אזהרה: גופן חסר באתר:', ', '.join(absent))
    # masechtot
    built = {}
    if only:
        st = os.path.join(SITE, 'status.json')
        if not os.path.exists(st) or not os.path.exists(os.path.join(SITE, 'index.html')):
            raise SystemExit('עצירה: בנייה חלקית בלי אתר קיים. הרץ בנייה מלאה')
        built = json.load(open(st, encoding='utf-8')).get('built') or {}
        missing = [m for m in built if not os.path.exists(os.path.join(SITE, SLUG[m] + '.html'))]
        if missing:
            raise SystemExit('עצירה: חסרים דפים באתר הקיים (%s). הרץ בנייה מלאה'
                             % ', '.join(missing[:5]))
        for m in list(built):
            if SLUG.get(m) in only:
                built.pop(m)
    # בהרצה מקומית אפשר להצביע על תיקיית הדרייב עצמה, כדי לבנות מן
    # הקובץ החי בלי להמתין לשומר ובלי לגעת בעותק שבמאגר.
    ddir = os.environ.get('LG_DOCX') or os.path.join(IN, 'docx')
    # רשימת הקבצים שנמצאים כרגע בתיקיית הדרייב, כפי שרשם אותה fetch.py.
    # קובץ שהמנהל שינה את שמו נשאר כאן כגיבוי ואינו נמחק, אך אינו נבנה,
    # כדי שהאתר יבנה תמיד מן הקובץ החי ולא מעותק ישן שנושא שם שנעלם.
    live = None
    lp = os.path.join(IN, 'current-docx.json')
    if os.path.exists(lp):
        names = json.load(open(lp, encoding='utf-8'))
        if len(names) >= 5: live = set(names)
    groups = {}
    for f in sorted(os.listdir(ddir)):
        if not f.endswith('.docx') or f.startswith('~$'): continue
        if live is not None and f not in live:
            print('אינו עוד בתיקיית הדרייב, לא נבנה:', f); continue
        sp = split_of(f)
        if sp:
            parts = split_file(os.path.join(ddir, f), sp)
            if parts:
                for m, blocks in parts:
                    preconv[m] = (blocks, f)
                continue
            print('אזהרה: הקובץ', f, 'אמור לשאת את', ' ועוד '.join(sp),
                  'ולא נמצאה בו נקודת חיתוך ברורה. נבנה כמסכת אחת')
        m = masechet_of(f)
        if not m:
            print('לא זוהתה מסכת:', f); continue
        groups.setdefault(m, []).append(f)
    for m in sorted(set(groups) | set(preconv), key=ALL.index):
        files = groups.get(m, [])
        if only and SLUG.get(m) not in only:
            continue
        try:
            if m in preconv:
                blocks, f = preconv[m]
            elif len(files) == 1:
                blocks = convert(os.path.join(ddir, files[0])); f = files[0]
            else:
                blocks, f = merge_masechet(m, files, ddir)
            jp = os.path.join(SITE, SLUG[m] + '.json')
            json.dump(blocks, open(jp, 'w', encoding='utf-8'), ensure_ascii=False)
            # מסך הגהה נבנה רק למסכת שיש לה קובץ ממצאים ידני. בלעדיו אין
            # למגיה מה לעשות שם, והגלאים לבדם רק היו מציפים אותו.
            cur = os.path.join(ROOT, 'data', 'hagaha-' + SLUG[m] + '.json')
            has_hagaha = os.path.exists(cur)
            # הגמרא המנוקדת נמשכת ביד ב-fetch_sources ונשמרת במאגר.
            # השומר רק מעתיק אותה לאתר, ואינו פונה לספריא בכל בנייה.
            sp = os.path.join(ROOT, 'data', 'sources', SLUG[m] + '.json')
            sources = None
            if os.path.exists(sp):
                sources = json.load(open(sp, encoding='utf-8'))
                os.makedirs(os.path.join(SITE, 'sources'), exist_ok=True)
                shutil.copy(sp, os.path.join(SITE, 'sources', SLUG[m] + '.json'))
            # המרווחים האנכיים שבדף נגזרים מ-w:spacing שבסגנונות הקובץ
            # הזה, ולא ממספרים שנבחרו לעין. קובץ מאוחד: המרווחים נלקחים
            # מן החלק הראשון, שהוא הגדול.
            spacing = {}
            try:
                src_doc = os.path.join(ddir, f.split(' + ')[0])
                if os.path.exists(src_doc):
                    spacing, _ = style_spacing.read(src_doc)
            except Exception as e:
                print('   אזהרה: המרווחים לא נגזרו מן הוורד של', m, '-', e)
            r = build(jp, os.path.join(SITE, SLUG[m] + '.html'), m, hagaha=has_hagaha,
                      sources=sources, spacing=spacing)
            if has_hagaha:
                h = hagaha.build(blocks, os.path.join(SITE, SLUG[m] + '-hagaha.html'), m, SLUG[m], cur, f)
                print('   מסך הגהה:', h['findings'], 'ממצאים,', h['severe'], 'טעונים תיקון')
            os.remove(jp)
            built[m] = {'file': f, 'pages': r['pages'], 'toc': r['toc'], 'qa': len(r['qa']),
                        'meta': r.get('meta'),
                        'hagaha': has_hagaha, 'heavy': r.get('heavy', []),
                        'hatz': r.get('hatz'), 'joined': r.get('joined')}
            if r.get('heavy'):
                print('   טעון תשומת לב:', '; '.join(r['heavy'][:6]))
            print('נבנה', m, r['pages'], 'עמודים', len(r['qa']), 'חריגות')
        except Exception as e:
            print('נכשל', m, repr(e))
    # index
    now = datetime.datetime.now().strftime('%d.%m.%Y %H:%M')
    now_ts = int(datetime.datetime.now().timestamp() * 1000)   # התצוגה: תאריך עברי (hdate.js)
    rows = ''
    for seder, ms in SEDER:
        cells = ''
        for m in ms:
            if m in built:
                b = built[m]
                extra = f'<a class="hg" href="{SLUG[m]}-hagaha.html">הגהה</a>' if b.get('hagaha') else ''
                red = ' warn' if b.get('heavy') else ''
                tip = (' title="' + html.escape('סגנון שאינו ממופה ומופיע הרבה: '
                       + '; '.join(b['heavy'][:5])) + '"') if b.get('heavy') else ''
                body = (f'<a class="m on{red}" href="{SLUG[m]}.html"{tip}><b>{m}</b><small>{b["pages"]} עמודים · '
                        f'{b["toc"]} נושאים{" · " + str(b["qa"]) + " לבקרה" if b["qa"] else ""}</small></a>')
                cells += body + extra if not extra else f'<div class="mw">{body}{extra}</div>'
            else:
                cells += f'<span class="m"><b>{m}</b><small>בעריכה</small></span>'
        rows += f'<section><h2>סדר {seder}</h2><div class="grid">{cells}</div></section>'
    idx = f'''<!DOCTYPE html><html lang="he" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>לאוקמי גירסא · קיצור התלמוד הבבלי</title>
<link href="https://fonts.googleapis.com/css2?family=Frank+Ruhl+Libre:wght@400;500;700;900&display=swap" rel="stylesheet">
<style>@font-face{{font-family:'Vilna';src:url(fonts/vilna-xb.otf);font-weight:900}}@font-face{{font-family:'Frank';src:url(fonts/frank.ttf)}}@font-face{{font-family:'Leukmey';src:url(fonts/leukmey.otf)}}
body{{margin:0;background:#e9e4d8;color:#1d1a16;font-family:'Frank','Frank Ruhl Libre',serif}}
header{{background:#2b2620;color:#f1ead9;padding:34px 20px 26px;text-align:center}} header h1{{font-family:'Leukmey','Vilna','Frank Ruhl Libre',serif;font-weight:900;font-size:46px;margin:0;letter-spacing:.02em}} header p{{margin:8px 0 0;color:#cfc4ad;font-size:18px}}
#dy{{display:inline-block;margin-top:14px;background:#c9a24a;color:#2b2620;border:0;border-radius:6px;padding:9px 22px;font:700 18px 'Frank','Frank Ruhl Libre',serif;cursor:pointer}} #dy:hover{{background:#b8912f}}
.m.now{{border-color:#a83c2f;box-shadow:0 0 0 2px #c9a24a}} .now-tag{{display:block;color:#a83c2f;font-size:12px;font-weight:700;margin-bottom:2px}}
#nowrow{{margin:18px 0 0}} #nowrow .grid{{grid-template-columns:minmax(180px,260px)}}
main{{max-width:980px;margin:0 auto;padding:18px 16px 60px}} h2{{font-weight:500;font-size:20px;color:#5a5044;border-bottom:1px solid #c9bfa8;margin:26px 0 10px;padding-bottom:4px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px}}
.m{{display:block;background:#f3eee2;border-radius:6px;padding:12px 14px;text-decoration:none;color:#8a7d66;border:1px solid #e0d8c4}} .m.on{{background:#fbf8f1;color:#1d1a16;border-color:#c9a24a;box-shadow:0 1px 4px rgba(0,0,0,.08)}} .m.on:hover{{background:#fff}}
.m b{{display:block;font-size:19px;font-weight:700}} .m small{{font-size:12px;color:#8a7d66}}
.mw{{position:relative}} .mw .m{{padding-bottom:26px}}
.m.warn{{border-color:#a83c2f;box-shadow:inset 3px 0 0 #a83c2f}} .m.warn small{{color:#a83c2f}}
.hg{{position:absolute;bottom:7px;right:14px;font-size:12px;background:#c9a24a;color:#2b2620;border-radius:4px;padding:1px 9px;text-decoration:none;font-weight:700}}
.hg:hover{{background:#b8912f}}
footer{{text-align:center;color:#8a7d66;font-size:13px;padding:20px}}</style></head><body>
<header><h1>לאוקמי גירסא</h1><p>קיצור התלמוד הבבלי · שלד הסוגיה בלבד</p><button id="dy" type="button" style="display:none">הדף היומי</button></header>
<main>{rows}</main><script src="hdate.js"></script><script src="daf-yomi.js"></script><script>
(function(){{var BUILT={json.dumps([SLUG[m] for m in built])};var b=document.getElementById('dy');if(!window.LGDaf)return;var t=LGDaf.today();if(!t)return;
b.style.display='';
b.onclick=function(){{if(BUILT.indexOf(t.slug)>-1)location.href=t.slug+'.html#daf='+encodeURIComponent(t.daf);else alert('מסכת '+t.name+' עדיין אינה באתר')}};
var a=document.querySelector('a.m[href="'+t.slug+'.html"]');
if(a){{a.classList.add('now');var tag=document.createElement('span');tag.className='now-tag';tag.textContent='נלמדת עכשיו בדף היומי: '+t.daf;a.insertBefore(tag,a.firstChild);
 var row=document.createElement('section');row.id='nowrow';var h=document.createElement('h2');h.textContent='נלמדת עכשיו בדף היומי';var g=document.createElement('div');g.className='grid';
 var c=a.cloneNode(true);c.classList.remove('now');c.querySelector('.now-tag').textContent='הדף היום: '+t.daf;g.appendChild(c);row.appendChild(h);row.appendChild(g);var m=document.querySelector('main');m.insertBefore(row,m.firstChild)}}
}})();
</script><footer>עודכן <span id="upd" data-ts="{now_ts}"></span> · האתר נבנה אוטומטית מקובצי הוורד · <a href="mekorot.html" style="color:inherit">מקורות</a></footer><script>(function(){{var u=document.getElementById('upd');if(u&&window.HD)u.textContent=HD.dateTime(+u.getAttribute('data-ts'))}})()</script></body></html>'''
    # הלוח הישן (כל המסכתות, הגהה ובקרה) עבר ל-masechtot.html. השער החדש
    # (index.html) הוא דף הבית של מערכת הלומד.
    idx = idx.replace('<footer>', '<footer><a href="index.html" style="color:inherit">לדף הבית</a> · ', 1)
    open(os.path.join(SITE, 'masechtot.html'), 'w', encoding='utf-8').write(idx)
    shutil.copy(os.path.join(ROOT, 'tools', 'daf_yomi.js'), os.path.join(SITE, 'daf-yomi.js'))
    shutil.copy(os.path.join(ROOT, 'tools', 'hdate.js'), os.path.join(SITE, 'hdate.js'))
    import build_lamed
    build_lamed.build(SITE)
    # עמוד "מקורות": הייחוס הנדרש ברישיון, פעם אחת, בשורה שקטה. השם המקורי
    # של הפירוש מופיע רק כאן; בממשק עצמו הוא "פירוש הגמרא".
    open(os.path.join(SITE, 'mekorot.html'), 'w', encoding='utf-8').write(
        '<!DOCTYPE html><html lang="he" dir="rtl"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1"><title>מקורות · לאוקמי גירסא</title>'
        '<style>body{margin:0;background:#e9e4d8;color:#1d1a16;font-family:serif;line-height:1.7}'
        'main{max-width:640px;margin:0 auto;padding:30px 18px}h1{font-size:26px}a{color:#5a4a2a}</style></head><body><main>'
        '<h1>מקורות</h1>'
        '<p>הגמרא המנוקדת והפירוש המוצגים במגירת "מקור" נלקחו מספריא (Sefaria), '
        'ממהדורת William Davidson של התלמוד הבבלי בעריכת הרב עדין אבן־ישראל שטיינזלץ, '
        'ברישיון CC BY-NC 4.0. האתר חינמי ואינו מוכר דבר.</p>'
        '<p><a href="index.html">חזרה לשער</a></p></main></body></html>')
    json.dump({'built': built, 'time': now}, open(os.path.join(SITE, 'status.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    write_shas(built)
    import build_seo
    build_seo.run(SITE, built, SLUG)
    print(len(built), 'מסכתות נבנו')

def write_shas(built):
    """site/shas.json - מפת הש"ס למערכת הלומד: הסדרים, המסכתות, ולמסכת
    שעלתה לאתר - כל עמוד ואורכו במילים, ופתיחת כל פרק."""
    out = {'seder': [], 'time': datetime.datetime.now().isoformat(timespec='seconds')}
    for seder, ms in SEDER:
        row = []
        for m in ms:
            b = built.get(m) or {}
            meta = b.get('meta') or {}
            row.append({'name': m, 'slug': SLUG[m], 'built': m in built,
                        'dafim': meta.get('dafim') or [], 'perakim': meta.get('perakim') or []})
        out['seder'].append({'name': seder, 'masechtot': row})
    json.dump(out, open(os.path.join(SITE, 'shas.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    open(os.path.join(SITE, 'shas.js'), 'w', encoding='utf-8').write(
        'window.LGSHAS=' + json.dumps(out, ensure_ascii=False, separators=(',', ':')) + ';')


if __name__ == '__main__':
    main()
