# -*- coding: utf-8 -*-
"""triage_reviewer.py - המבקר החדש לתוספות (שלב ד, 14.10.2026): שלוש דרגות, ודוגמאות מהכרעות המנהל.

דרגות:
  תקין      - התוכן נאמן. מותר תמצות, סידור לרש"י/לתוס', וקונטרס = רש"י.
  תיקון קל  - המבקר עצמו מוחק הפניה שאינה בתוספות או מילה עודפת (או מקצר), ומחזיר את השורה המתוקנת.
  פסול      - רק תוספת דין או מסקנה שאינה בתוספות, השמטת נימוק מכריע, ייחוס הפוך, או טעות עניינית.

מאגר הדוגמאות: tosafot/triage/examples.json (הכרעות המנהל, כולל העתידיות, נמשכות ב-triage_sync.py).
המבקר מצרף להוראותיו את הדוגמאות הרלוונטיות (דמיון מילים ללשון התוספות ולשורה, וגם איזון בין "נכון" ל"לא נכון").

שימוש (בדיקה על ההכרעות שבידי המנהל): uv run python tools/tosafot/triage_reviewer.py eval
"""
import os, sys, re, json, io, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
EX = os.path.join(ROOT, 'tosafot', 'triage', 'examples.json')
NIK = re.compile('[֑-ׇ]')

SYS_V2 = """אתה מבקר זהיר של שורת מסקנה (הערת שוליים) שנכתבה על תוספות בספר לימוד של הש"ס. לכל תוספות יוגשו: ד"ה, לשון התוספות המלאה, השורה שנכתבה, ושאלות (אם יש). בדוק מול לשון התוספות המלאה בלבד.

מונחים: "קונטרס" הוא רש"י. ר"ת הוא רבינו תם. ר"י הוא רבי יצחק (הזקן) מבעלי התוספות. ריב"א הוא רבי יצחק בן אשר. ר"ח הוא רבנו חננאל. הרשב"א, הרא"ש והר"ן הם ראשונים מאוחרים. "הא דקאמר" וכדומה הם לשון תוספות רגילה. ייחוס "לרש"י" שורה שהתוספות מכנים "בקונטרס" אינו שגוי.

שלוש דרגות. החזר לכל תוספות דרגה אחת:

1. "תקין": התוכן נאמן ללשון התוספות. מותר תמצות, קיצור וסידור (לרש"י... ולתוס'...). מותר מטבע לשון מוכר שאינו מפורש. אין לפסול על סגנון, על כך שהשורה "מכנית", על כך שאפשר היה לנסח אחרת, או על כך שלא הוסבר דבר שהתוספות עצמם לא הסבירו. אנו אינם מחויבים ליותר ממה שהתוספות כתבו.

2. "תיקון קל": התוכן נאמן, אך יש בשורה פגם קטן שאתה מתקן בעצמך: הפניה למקור או דף שאינם בלשון התוספות (מחק אותה), מילה עודפת, או שורה ארוכה שאפשר לקצר בלי לאבד נימוק. החזר בשדה "fix" את השורה המתוקנת במלואה. אל תוסיף דבר שאינו בתוספות.

3. "פסול": רק כשיש אחד מאלה: (א) תוספת דין או מסקנה שאינה בתוספות; (ב) השמטת נימוק מכריע, כך שהשורה מטעה או אינה מובנת; (ג) ייחוס הפוך (דעה לאדם הלא נכון); (ד) טעות עניינית. בשדה "s" כתוב את הסיבה הקצרה והמדויקת.

הפניה לתוספות אחר או למקום אחר ("כמו שכתבנו", "בד"ה ...") אינה פגם: אל תפסול עליה ואל תמחק אותה כשהיא בלשון התוספות. אם השורה מפנה למקום אחר ויש צורך שמודל חזק יבדוק אחר כך את היעד, סמן "star": true. אל תשנה מספור או הפניות פנימיות.

שאלות: כל שאלה נבדקת בנפרד. שאלה פגומה (התשובה אינה בתוספות, השאלה מסגירה את התשובה, בנאלית, כפולה) מקבלת סיבה קצרה ברשימה "q" במקומה; שאלה תקינה מקבלת מחרוזת ריקה.

החזר JSON אחד בלבד, בלי גדרות קוד, בלי טקסט נוסף, לכל מזהה שהוגש:
{"<מזהה>": {"d": "תקין" | "תיקון קל" | "פסול", "s": "<סיבה, רק בפסול>", "fix": "<השורה המתוקנת, רק בתיקון קל>", "star": false, "q": ["", ...]}}
אל תכתוב קו מפריד ארוך (em dash או en dash) ואל תכתוב את התו ; (נקודה-פסיק)."""


def jload(p, d=None):
    return json.load(io.open(p, encoding='utf-8')) if os.path.exists(p) else d


def words(s):
    return set(re.findall(r'[א-ת]{2,}', NIK.sub('', s or '')))


def examples():
    return (jload(EX, {}) or {}).get('items', [])


def pick(text, line, exclude=None, k=6):
    """הדוגמאות הרלוונטיות: דמיון מילים (ג'קארד) ללשון התוספות ולשורה, ואיזון: לפחות שתיים משני הכיוונים כשיש."""
    ex = [e for e in examples() if e.get('ans') in ('yes', 'no') and e.get('id') != exclude]
    q = words(text) | words(line)
    sc = []
    for e in ex:
        w = words(e.get('text')) | words(e.get('line'))
        sc.append((len(q & w) / float(len(q | w) or 1), e))
    sc.sort(key=lambda x: -x[0])
    out = [e for _, e in sc[:k]]
    for a in ('yes', 'no'):
        if sum(1 for e in out if e['ans'] == a) < 2:
            for _, e in sc:
                if e['ans'] == a and e not in out:
                    out.append(e)
                    if sum(1 for x in out if x['ans'] == a) >= 2:
                        break
    return out


def fmt_example(e):
    v = 'נכון (השורה תקינה, המבקר טעה אם פסל)' if e['ans'] == 'yes' else 'לא נכון (יש בשורה פגם אמיתי)'
    return ('### דוגמה מהכרעת המנהל\nד"ה: %s\nלשון התוספות: %s\nהשורה: %s\nנימוק המבקר הקודם: %s\nהכרעת המנהל: %s\nהערת המנהל: %s'
            % (e.get('dh', ''), ' '.join((e.get('text') or '').split()[:220]), e.get('line', ''), ' | '.join(e.get('why') or []) or '(לא פסל)', v, e.get('note') or '(אין)'))


def system_with_examples(blocks_text_line, exclude=None):
    """blocks_text_line: [(text, line)] של הקבוצה; מצרף את הדוגמאות הרלוונטיות להוראות."""
    seen, out = set(), []
    for t, l in blocks_text_line:
        for e in pick(t, l, exclude, 4):
            if e['id'] not in seen:
                seen.add(e['id'])
                out.append(e)
    if not out:
        return SYS_V2
    return SYS_V2 + '\n\n## דוגמאות מהכרעות המנהל (למד מהן את הרף)\n\n' + '\n\n'.join(fmt_example(e) for e in out[:8])


def user_block(rid, dh, text, line, qs):
    q = '\n'.join('  שאלה %d: %s | תשובה: %s' % (i + 1, x['q'], x['a']) for i, x in enumerate(qs or [])) or '  (אין שאלות)'
    return '### מזהה: %s\nדיבור המתחיל: %s\nלשון התוספות המלאה:\n%s\nהשורה שנכתבה: %s\nשאלות:\n%s' % (rid, dh, text, line, q)


def run_claude(system, user, model='sonnet'):
    """הרצה דרך claude -p (לבדיקות מקומיות). מחזיר (dict, cost)."""
    p = system + '\n\n---\n\n' + user
    o = subprocess.run(['claude', '-p', '--model', model, '--output-format', 'json'], input=p, capture_output=True, text=True, encoding='utf-8')
    j = json.loads(o.stdout)
    t = re.sub(r'^```(?:json)?|```$', '', j['result'].strip(), flags=re.M).strip()
    return json.loads(t), j.get('total_cost_usd', 0.0)


def evaluate(model='sonnet'):
    """מריץ את המבקר על הכרעות המנהל בלבד. דוגמאות: כל מה שבמאגר חוץ מהפריט עצמו (leave-one-out)."""
    items = [e for e in examples() if e.get('ans') in ('yes', 'no')]
    res, cost = [], 0.0
    for e in items:
        sysm = system_with_examples([(e['text'], e['line'])], exclude=e['id'])
        got, c = run_claude(sysm, user_block(e['id'], e['dh'], e['text'], e['line'], e.get('qs')), model)
        cost += c
        g = got.get(e['id']) or next(iter(got.values()))
        res.append({'id': e['id'], 'ans': e['ans'], 'd': g.get('d'), 's': g.get('s', ''), 'fix': g.get('fix', ''), 'star': g.get('star')})
    return res, cost


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'eval':
        r, c = evaluate(sys.argv[2] if len(sys.argv) > 2 else 'sonnet')
        print(json.dumps({'cost': c, 'res': r}, ensure_ascii=False, indent=1))
