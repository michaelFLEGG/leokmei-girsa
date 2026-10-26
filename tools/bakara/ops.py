# -*- coding: utf-8 -*-
"""ops.py - מטען ההחלה של ממצאי הבקרה (19.10.2026).

כל ממצא חייב לשאת f.op: פעולה מוכנה, ש"קבל" בדף מחיל כמו שהיא (אין עוד "אושר לביצוע").
מבנה (מדויק, בלי טקסט חופשי):
  {"rep": {"x": ישן, "y": חדש}}                       החלפה (גם מחיקה: y ריק)
  {"ins": {"after"|"before": עוגן, "end": true, "text": ..., "cs": "hs"}}   הוספה בסגנון "הסבר", בסוגריים מרובעים
  {"style": {"range": ..., "cs": "am"|"ps"|"plain"}}  החלת/הסרת סגנון תו
  {"anchor": {...}} | {"heading": {...}} | {"nikud": {x,y}} | {"split": {at}} | {"join": 1}   (26.10.2026, ראה convert.py)
  {"ask": "..."}                                       בדיקה/שאלה: אין מה להחיל; "קבל" = נבדק, בלי שינוי
  {"none": "..."}                                      אין עדיין מטען: הדף מבקש הצעה ועובר הלאה
החלפה "ישן ⟵ חדש" וסגנון ("להחיל סגנון ...") נגזרים בדף עצמו מתוך fix, ולכן כאן אינם נכתבים שוב.

המקורות, לפי סדר: op שהמנוע/הסוקר כתבו; data/bakara/ops.json (מטען שנוסח ביד, לפי מזהה ממצא);
גזירה מכנית מתוך fix (להלן). ממצא שאין לו מטען מקבל none - ולא יסומן "אושר" לעולם.

    uv run python tools/bakara/ops.py --live [--slug bekhorot] [--dry]   מושך מהשרת, מוסיף מטען, מעלה בחזרה
"""
import os, re, sys, json, argparse, glob

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OPS_FILE = os.path.join(ROOT, 'data', 'bakara', 'ops.json')

IMPERATIVE = re.compile(r'^(ל[א-ת]{2,}|אם |או |אחרי|בדוק|האם|לבדוק|הוספה)')
CHECK_FIX = re.compile(r'^(אם ציטוט|אם ראשי תיבות|לבדוק|אם )')


def _strip_text(t):
    t = (t or '').strip()
    t = re.sub(r'^\[+|\]+$', '', t).strip()
    if len(t) > 2 and t[0] == "'" and t[-1] == "'":
        t = t[1:-1].strip()
    t = re.sub(r'[.\s]+$', '', t)
    return t


def ins_from_fix(f):
    """הוספה מתוך נוסח ההוראה. מחזיר {'ins': {...}} או None."""
    fx = (f.get('fix') or '').strip()
    if not fx or f.get('layer') == 'קוד' and f.get('det') not in ('sk_step', 'sk_miss'):
        pass
    Q = "['״“\"]"
    m = re.match(r"^(?:להוסיף |הוסף )?אחרי " + Q + r"(.+?)" + Q + r"(?: להוסיף| הוסף)?: (.+)$", fx)
    if m:
        return {'ins': {'after': m.group(1), 'text': _strip_text(m.group(2)), 'cs': 'hs'}}
    m = re.match(r"^(?:להוסיף |הוסף |הוספה )לפני " + Q + r"(.+?)" + Q + r": (.+)$", fx)
    if m:
        return {'ins': {'before': m.group(1), 'text': _strip_text(m.group(2)), 'cs': 'hs'}}
    m = re.match(r"^(?:להוסיף|להשלים|הוספה) אחריה: (.+)$", fx)
    if m:
        return {'ins': {'after': f.get('mark') or '', 'text': _strip_text(m.group(1)), 'cs': 'hs'}}
    m = re.match(r"^(?:להוסיף|הוספה|להשלים) בסוף הפסקה: (.+)$", fx)
    if m:
        return {'ins': {'end': True, 'text': _strip_text(m.group(1)), 'cs': 'hs'}}
    m = re.match(r"^אחרי ([^:']{2,40}): (.+)$", fx)
    if m:
        return {'ins': {'after': m.group(1).strip(), 'text': _strip_text(m.group(2)), 'cs': 'hs'}}
    m = re.match(r"^(?:להוסיף|להשלים|הוספה): (.+)$", fx)
    if m:
        return {'ins': {'after': f.get('mark') or '', 'text': _strip_text(m.group(1)), 'cs': 'hs'}}
    # משפט תוכן (לא פועל ציווי) בממצא "חסר שלב" / "תוכן שלא הובא": הוא ההשלמה עצמה, אחרי הקטע המסומן
    if f.get('det') in ('sk_step', 'sk_miss', 'sem_hsr') and f.get('typ') != 'h' and not IMPERATIVE.match(fx) and len(fx) >= 8:
        mk = (f.get('mark') or '').strip()
        base = re.sub(r'[\s,.:;?!-]+$', '', mk)
        t = fx
        if base and t.startswith(base):
            t = re.sub(r'^[\s,.:;-]+', '', t[len(base):])
        return {'ins': {'after': mk, 'text': _strip_text(t), 'cs': 'hs'}}
    return None


PUNCT2 = {',.': '.', '.,': '.', ':,': ':', ',:': ':', '.:': ':', ':.': ':', ',,': ',', '..': '.', '::': ':'}


def punct_op(f):
    """פיסוק כפול או רווח לפני פסיק: החלפה מכנית. פיסוק כפול בין שני סימנים שונים - החזק מביניהם."""
    if f.get('det') != 'punct' or (f.get('fix') or '').strip() != 'לנקות':
        return None
    mk = f.get('mark') or ''
    if re.fullmatch(r'\s+,', mk):
        return {'rep': {'x': mk, 'y': ','}}
    m = re.fullmatch(r'([,.:])\s*([,.:])', mk)
    if m and m.group(0).strip() not in ('..', '...'):
        k = m.group(1) + m.group(2)
        if k in PUNCT2:
            return {'rep': {'x': mk, 'y': PUNCT2[k]}}
    return None


def derive(f, hand=None):
    """המטען של ממצא אחד (לא נוגע בממצא)."""
    ex = f.get('op')
    if ex and any(k in ex for k in ('rep', 'ins', 'style', 'del', 'anchor', 'heading', 'nikud', 'split', 'join')):   # מטען אמיתי נשמר; none / ask נגזרים מחדש
        return ex
    if hand and f.get('id') in hand:
        return hand[f['id']]
    fx = (f.get('fix') or '').strip()
    # החלפה וסגנון נגזרים בדף עצמו
    if fx.count('⟵') == 1 and ';' not in fx:
        return None
    if re.match(r'^(להחיל סגנון (אמוראים|פסוק)|להחזיר לסגנון רגיל)', fx):
        return None
    o = ins_from_fix(f) or punct_op(f)
    if o:
        return o
    if f.get('typ') == 'h' or f.get('det') == 'sk_q':
        return {'ask': 'שאלה למחבר'}
    if f.get('det', '').startswith('cl_') and not fx:
        return {'ask': 'הכרעת המנוע: אין שינוי אוטומטי בטקסט'}
    if f.get('det') in ('dafpos', 'attr') or CHECK_FIX.match(fx):
        return {'ask': 'בדיקה: אין שינוי אוטומטי בטקסט'}
    return {'none': 'אין עדיין הצעה מוכנה'}


def load_hand():
    if os.path.exists(OPS_FILE):
        return json.load(open(OPS_FILE, encoding='utf-8'))
    return {}


def annotate(findings):
    """מוסיף f.op לכל ממצא שאין לו. מחזיר ספירה לפי סוג המטען."""
    hand = load_hand()
    cnt = {}
    for f in findings:
        o = derive(f, hand)
        if o is not None:
            f['op'] = o
        k = next(iter(o)) if o else 'derived-in-page'
        cnt[k] = cnt.get(k, 0) + 1
    return cnt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--live', action='store_true')
    ap.add_argument('--slug', action='append', default=[])
    ap.add_argument('--dry', action='store_true')
    a = ap.parse_args()
    sys.path.insert(0, HERE)
    import _api
    slugs = a.slug or _api.call('/bakara/data').get('slugs', [])
    tot = {}
    for s in slugs:
        d = _api.call('/bakara/data?slug=' + s).get('doc') or {}
        for p, v in (d.get('perakim') or {}).items():
            c = annotate(v.get('findings', []))
            for k, n in c.items():
                tot[k] = tot.get(k, 0) + n
            if not a.dry:
                r = _api.call('/bakara/data', 'PUT', {'slug': s, 'perek': int(p), 'data': v})
                print('הועלה', s, p, '-', r.get('n'))
    print('מטען לפי סוג:', tot)


if __name__ == '__main__':
    main()
