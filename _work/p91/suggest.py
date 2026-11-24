# -*- coding: utf-8 -*-
"""פרומפט 91 - הצעות לעיון המנהל בשבת פרק ה (תור ההצעות באתר, "פרומפט 91 (ענן)"). לא מוחלות לבד.
    python _work/p91/suggest.py [--send]"""
import os, sys, json, io, re, time, html, random, string, urllib.request, urllib.error
HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
API = 'https://leokmei-suggest.m7654301.workers.dev'
rows = {x['id']: x for x in json.load(io.open(os.path.join(HERE, '_work', 'p91', 'rowhtml-sug.json'), encoding='utf-8'))}
plain = lambda h: re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', '', h or '')).replace('\xa0', ' ')).strip()
rnd = lambda n: ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(n))


def inner(ek):
    uid = ek[1:].split('.')[0]
    m = re.search(r'data-ek="%s"[^>]*>(.*?)</(?:p|div)>' % re.escape(ek), rows[uid]['html'], re.S)
    return m.group(1)


S = [  # (ek, daf, nowH או None=בלי שינוי, הערה)
 ('u1795446184772.1', 'נא:', 'הלכו בדרך וקדם חמורו לחמור רבה בר ר"ה, שאלו לפייסו: חמור שעסקיו רעים - מהו לצאת בפרומביא? והשיבו: כך אמר אביך משמואל: הלכה כחנניה.',
  'השאלה והתשובה נמחקו בעריכות 23.11 16:01 ונקלטו בקיפול 24.11 כתלושות. אם נמחקו בכוונה - לדחות.'),
 ('u3501.2', 'נג.', 'ופוקקין לה זוג בצווארה ומטיילת עמו בחצר [ולא ברה"ר].', 'בגמרא: "פוקקין לה זוג בצוארה ומטיילת עמו בחצר" (ולא "במוך פעמון" ולא "ברה"י").'),
 ('u1795283030181.1', 'נד.', 'הלכה כריב"ב, &nbsp;&nbsp;ר\' יוחנן: הלכה כת"ק, שמותר בשתיהן.', 'רש"י נד.: "כת"ק - דמתני\' דשרי בתרוייהו". העריכה מ-18.11 ("שליבש מותר") הפכה את הדין.'),
 ('u3569.1', 'נד.', 'כך הלכה, אבל קשה להבחין ביניהן, לכן שתיהן אסורות. [וא"ד: באפי נפשה: לרב - ליבש מותר ולא לחלב, ולשמואל - אחד זה ואחד זה אסור.]',
  'הלשון השנייה (ואיכא דמתני לה באפי נפשה) חסרה. עדיף כשורה נפרדת עם כותרת צד "וא"ד:" - ואז תוס\' 32 יעוגן אליה.'),
 ('u3670.1', 'נה:', 'רשב"נ: בני עלי לא חטאו, ד\'חפני ופנחס כהנים לה\'\' - מקיש חפני לפנחס: מה פנחס לא חטא - אף חפני לא חטא. ולרב: רק פנחס לא חטא, שהכתוב מייחס את בנו, ו\'ישכבן\', \'בני\', \'מעבירם\' - כתיב, ו\'בני בליעל\' - שהיה לו לפנחס למחות בחפני ולא מיחה, ומעלה עליו הכתוב כאילו חטא.',
  'המחלוקת בבני עלי נבלעה. מוצע בשלוש כותרות צד: "ב. רשב"נ:", "ומה", "ולרב:" (תוס\' נ"א: "פליג אר\' יונתן"). אחרי הקבלה - עוגן תוס\' 50 ל"מעבירם".'),
 ('u3576.2', 'נד.', 'עקוד - עקידת יד ורגל, כיצחק בן אברהם [כתנא אחד; ובברייתא: שתי ידיים ושתי רגליים, ובאחרת: או זה או זה].', 'פרומפט 91 ו.5'),
 ('u1795514589906.1', 'נא:', 'בחתול, שדי לו בחבל, והלכה כחנניה, דשמירה יתירה לא נחשבת משאוי.', 'רווחים כפולים ו"משא." במקום "משאוי".'),
 ('u3672.1', 'נה:', 'ד\'ישכבון את הנשים\' - מתוך ששהו קיניהן מלילך אצל בעליהן, מעלה עליהם הכתוב כאילו שכבום.', 'לשון הפסוק: "אשר ישכבון את הנשים".'),
 ('u3605.1', 'נד:', 'לשמואל לנוי - אסור, לשמר - מותר.', 'תו נסתר (U+2064) לפני "לשמואל". עדיף להעלות "לשמואל:" לכותרת צד.'),
 ('u3563.0', 'נד.', '<i class="dm">והעזים יוצאות צרורות</i>', 'פרומפט 91 ד.2: ד"ה משנה "והעזים יוצאות צרורות", ואחריו הכותרת "עזים צרורות - הלכה כמי" (שתי כותרות - צריך פיצול בעורך).'),
 ('u3607.0', 'נד:', None, 'פרומפט 91 ד.2: לפני הכותרת הזאת חסר ד"ה משנה "פרתו של ראב"ע" (השורה "פרתו של ראב"ע..." תחת הכותרת).'),
 ('u3463.1', 'נב:', 'והאיכא חציצה! - בשריתכן, &nbsp;&nbsp;ב. במתניתא: במחוללין.', 'פרומפט 91 ד.2: אחרי ד"ה "וטובלן במקומן" - השאלה "והאיכא חציצה!" (עדיף כשורה בפני עצמה לפני "א. רב אמי:").'),
]
pid, pt, grp = rnd(14), rnd(32), rnd(10)
t = int(time.time() * 1000)
out = []
for ek, daf, nowH, note in S:
    t += 1
    wasH = inner(ek)
    if nowH is None:
        nowH = wasH
    edit = {'k': '%s~%d' % (ek, t), 'bt': plain(wasH), 'bh': wasH, 'was': plain(wasH), 'wasH': wasH, 'now': plain(nowH), 'nowH': nowH,
            'wasP': '', 'daf': daf, 'ctx': {'b': '', 'a': ''}, 't': t}
    out.append({'slug': 'shabbat', 'masechet': 'שבת', 'daf': daf, 'uid': ek[1:].split('.')[0], 'k': edit['k'], 'ctx': edit['ctx'],
                'was': plain(wasH)[:200], 'note': note[:600], 'name': 'פרומפט 91 (ענן)', 'type': 'nusach', 'sk': 'text',
                'edit': edit, 'pid': pid, 'pt': pt, 'grp': grp, 'hp': '', 't': t, 'sent': 0, 'ek': edit['k']})
print('הצעות:', len(out))
if '--send' in sys.argv:
    ok = 0
    for rec in out:
        for attempt in range(6):
            req = urllib.request.Request(API + '/suggest', data=json.dumps(rec, ensure_ascii=False).encode('utf-8'), method='POST',
                                         headers={'content-type': 'application/json; charset=utf-8', 'user-agent': 'Mozilla/5.0 leokmei-p91/1.0'})
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    j = json.loads(r.read().decode('utf-8'))
                if j.get('ok'):
                    rec['id'] = j.get('id'); ok += 1
                else:
                    print('לא התקבל', rec['daf'], j)
                break
            except urllib.error.HTTPError as e:
                body = e.read().decode('utf-8', 'replace')
                if 'מהירה' in body or e.code == 429:
                    time.sleep(4 + attempt * 3); continue
                print('HTTP', e.code, body[:200]); break
            except Exception as e:
                time.sleep(3)
        time.sleep(1.2)
    print('נשלחו', ok)
    io.open(os.path.join(HERE, '_work', 'p91', 'suggested.json'), 'w', encoding='utf-8').write(
        json.dumps([{'daf': r['daf'], 'ek': r['ek'], 'id': r.get('id'), 'note': r['note']} for r in out], ensure_ascii=False, indent=1))
