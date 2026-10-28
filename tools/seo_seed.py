# -*- coding: utf-8 -*-
"""seo_seed.py - זריעה חד-פעמית של מרשם התאריכים data/seo/lastmod.json (פרומפט 10, 28.10.2026).

לכל דף נרשמת טביעת התוכן שלו ותאריך אמיתי: הפעם האחרונה שקובץ הוורד של המסכת או
קובץ התיקונים שלה השתנו במאגר (git log). מכאן ואילך build_static מעדכן את התאריך
רק לדף שתוכנו השתנה. מורץ מקומית על אתר בנוי:  uv run python tools/seo_seed.py
"""
import os, sys, json, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_static as B
from build_all import SLUG, ROOT, SITE, masechet_of, split_of


def git_date(paths):
    if not paths:
        return None
    r = subprocess.run(['git', 'log', '-1', '--format=%cs', '--'] + paths, cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
    return r.stdout.strip() or None


def main():
    built = json.load(open(os.path.join(SITE, 'status.json'), encoding='utf-8'))['built']
    docx = os.listdir(os.path.join(ROOT, 'input', 'docx'))
    live = os.path.join(ROOT, 'input', 'current-docx.json')
    if os.path.exists(live):        # רק הקבצים שבתיקיית הדרייב כרגע, כמו בבנייה עצמה
        names = set(json.load(open(live, encoding='utf-8')))
        docx = [f for f in docx if f in names]
    led, today = B.load_ledger(), B.il_today().isoformat()
    for m in built:
        sl = SLUG[m]
        files = ['input/docx/' + f for f in docx if masechet_of(f) == m or m in (split_of(f) or [])]
        ed = 'data/edits/%s.json' % sl
        dates = [d for d in (git_date(files), git_date([ed]) if os.path.exists(os.path.join(ROOT, ed)) else None) if d]
        date = max(dates) if dates else today
        D = B.load_data(os.path.join(SITE, sl + '.html'))
        mains, _, _ = B.page_groups(D)
        for g in mains:
            key = '%s/%s' % (sl, g['dp'])
            if key not in led:
                led[key] = [B.content_hash(B.group_body(D, g)), date, date]
        print(m, len(mains), date, len(files), 'קבצים')
    B.save_ledger(led)
    print('נרשמו', len(led), 'דפים')


if __name__ == '__main__':
    main()
