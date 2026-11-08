# -*- coding: utf-8 -*-
"""titles_push.py - הכנסת הצעות הכותרות (סוג k) לסקירה שבדף המסכת (8.11.2026).

הקלט: data/sakem/titles-review/<slug>.json (הפלט של titles_review.mjs):
    {slug, findings: {"<פרק>": [ממצא, ...]}, ...}
לכל מסכת: GET /bakara/data?slug= (כל הפרקים), ולכל פרק שיש בו הצעות חדשות או ממצאי
כותרות ישנים: הסרת הממצאים עם det side_long / title_dup, הוספת החדשים, ו-PUT
{slug, perek, data}. שאר הממצאים של הפרק (שאר סוגי הסקירה) נשארים כמות שהם, ולכן
הכנסה חוזרת בטוחה: היא מחליפה רק את ממצאי הכותרות. ההכרעות שכבר נעשו (bk:c) אינן
נוגעות כלל; ממצא שמזההו לא השתנה ממשיך להיות מוכרע.

KV מתיר כתיבה אחת בשנייה לאותו מפתח (כל פרקי המסכת במפתח אחד), ולכן בין PUT ל-PUT
יש המתנה של 1.3 שניות, ועל 429 / 5xx - נסיון חוזר בהמתנה גדלה. כשל שנשאר: עצירה רועשת.

המפתח: משתנה הסביבה LEOKMEI_ADMIN_KEY (או LG_ADMIN_KEY), ובמחשב המקומי גם קובץ
המפתח שבתיקיית המסמכים (מחוץ למאגר). לעולם לא בקובץ שבמאגר.

    uv run python tools/sakem/titles_push.py              כל המסכתות שיש להן קובץ
    uv run python tools/sakem/titles_push.py bekhorot     מסכת אחת או כמה
    uv run python tools/sakem/titles_push.py --dry        מדפיס מה ישתנה, בלי לכתוב
"""
import io, json, os, sys, time, urllib.error, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.dirname(HERE))
import perush_store

API = os.environ.get('LG_API') or 'https://leokmei-suggest.m7654301.workers.dev'
SRC = os.path.join(ROOT, 'data', 'sakem', 'titles-review')
DETS = ('side_long', 'title_dup')
GAP = 1.3


def call(path, body=None, method='GET'):
    key = perush_store.admin_key()
    if not key:
        sys.exit('עצירה: חסר מפתח מנהל (LEOKMEI_ADMIN_KEY)')
    data = None if body is None else json.dumps(body, ensure_ascii=False).encode('utf-8')
    wait = 2.0
    for n in range(6):
        rq = urllib.request.Request(API + path, data=data, method=method,
                                    headers={'x-admin-key': key, 'User-Agent': 'leokmei-titles-push/1.0',
                                             'content-type': 'application/json; charset=utf-8'})
        try:
            with urllib.request.urlopen(rq, timeout=90) as r:
                return json.loads(r.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            if e.code == 429 or e.code >= 500:
                print('   %s על %s, נסיון חוזר בעוד %.0f שניות' % (e.code, path.split('?')[0], wait))
                time.sleep(wait)
                wait *= 2
                continue
            sys.exit('עצירה: %s על %s: %s' % (e.code, path, e.read().decode('utf-8', 'replace')[:200]))
        except urllib.error.URLError as e:
            print('   שגיאת רשת (%s), נסיון חוזר' % e.reason)
            time.sleep(wait)
            wait *= 2
    sys.exit('עצירה: %s נכשל שש פעמים' % path.split('?')[0])


def push(slug, dry):
    p = os.path.join(SRC, slug + '.json')
    new = json.load(io.open(p, encoding='utf-8')).get('findings') or {}
    doc = (call('/bakara/data?slug=' + slug) or {}).get('doc') or {'perakim': {}}
    have = doc.get('perakim') or {}
    perakim = sorted(set(new) | set(have), key=lambda x: int(x))
    put = added = removed = 0
    for pk in perakim:
        cur = have.get(pk) or {}
        old = cur.get('findings') or []
        keep = [f for f in old if f.get('det') not in DETS]
        gone = len(old) - len(keep)
        add = new.get(pk) or []
        if not add and not gone:
            continue
        if not cur and not add:
            continue
        ids = {f.get('id') for f in add}
        merged = [f for f in keep if f.get('id') not in ids] + add
        data = dict(cur, findings=merged) if cur else {'findings': merged}
        removed += gone
        added += len(add)
        if dry:
            print('   %s פרק %s: %d נשארים, %d ממצאי כותרות ישנים יוסרו, %d חדשים'
                  % (slug, pk, len(keep), gone, len(add)))
            continue
        if put:
            time.sleep(GAP)
        r = call('/bakara/data', {'slug': slug, 'perek': int(pk), 'data': data}, 'PUT')
        if not r.get('ok') or r.get('n') != len(merged):
            sys.exit('עצירה: %s פרק %s - השרת החזיר %r (ציפינו ל-%d ממצאים)' % (slug, pk, r, len(merged)))
        put += 1
    print('%s: %d פרקים נכתבו, %d הצעות כותרות (במקום %d ישנות)' % (slug, put, added, removed))
    return put


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    dry = '--dry' in sys.argv
    slugs = args or sorted(f[:-5] for f in os.listdir(SRC) if f.endswith('.json'))
    total = 0
    for i, s in enumerate(slugs):
        if not os.path.exists(os.path.join(SRC, s + '.json')):
            sys.exit('עצירה: אין קובץ הצעות למסכת ' + s)
        if i and not dry:
            time.sleep(GAP)
        total += push(s, dry)
    print('סה"כ: %d פרקים ב-%d מסכתות' % (total, len(slugs)))


if __name__ == '__main__':
    main()
