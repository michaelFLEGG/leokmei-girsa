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
sys.path.insert(0, os.path.join(ROOT, 'tosafot', 'handoff', 'kit'))
import gates as G   # 24.10.2026: הנחיית המבקר V2 ובחירת הדוגמאות במקור יחיד (ערכת החשבון השני)
from gates import SYS_V2, fmt_example, user_block

def jload(p, d=None):
    return json.load(io.open(p, encoding='utf-8')) if os.path.exists(p) else d


def examples():
    return (jload(EX, {}) or {}).get('items', [])


def pick(text, line, exclude=None, k=6):
    """הדוגמאות הרלוונטיות (gates.pick_examples) מתוך מאגר ההכרעות."""
    return G.pick_examples(examples(), text, line, exclude, k)


def system_with_examples(blocks_text_line, exclude=None):
    """blocks_text_line: [(text, line)] של הקבוצה; מצרף את הדוגמאות הרלוונטיות להוראות."""
    return G.system_with_examples(examples(), blocks_text_line, exclude)


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
