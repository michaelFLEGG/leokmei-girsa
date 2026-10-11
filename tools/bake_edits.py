# -*- coding: utf-8 -*-
"""bake_edits.py - אפיית עריכות המנהל לנתוני האתר, ממחשב בעל הפרויקט.

משימה מתוזמנת כל חמש דקות: עובד על עותק נפרד של המאגר
(C:\leokmei-girsa-bake) כדי לא לגעת בעותק-העבודה; מושך את העריכות
מנקודת הקליטה (pull_edits.py, עם מפתח המנהל המקומי); ואם נכתב קובץ
תיקונים - דוחף. דחיפה ל-data/edits מפעילה את הבנייה הקצרה (edits.yml)
שבונה רק את המסכתות שהשתנו ומפרסמת, תוך דקות.

הסיבה שזה כאן ולא ב-GitHub Actions: ההרשאה שבמחשב אינה מאפשרת הוספת
קובץ עבודה (workflow) לענן, והדחיפה הרגילה מותרת. כשהמחשב כבוי, השומר
(בנייה כל חצי שעה) אופה את אותן עריכות מן הנקודה הציבורית.

    uv run python tools/bake_edits.py            (הרצה אחת)
    uv run python tools/bake_edits.py --install  (מקים את המשימה)
"""
import os, sys, subprocess, io

CLONE = r'C:\leokmei-girsa-bake'
URL = 'https://github.com/michaelFLEGG/leokmei-girsa.git'
TASK = 'לאוקמי גירסא - אפיית עריכות לאתר'


def git(*a, check=True):
    r = subprocess.run(['git', '-C', CLONE] + list(a), capture_output=True)
    out = (r.stdout + r.stderr).decode('utf-8', 'replace')
    if check and r.returncode:
        raise SystemExit('git %s נכשל: %s' % (' '.join(a), out[:300]))
    return out


def run():
    if not os.path.isdir(os.path.join(CLONE, '.git')):
        subprocess.run(['git', 'clone', '-q', URL, CLONE], check=True)
        git('config', 'user.name', 'leokmei-bake')
        git('config', 'user.email', 'bake@users.noreply.github.com')
    git('fetch', '-q', 'origin')
    git('reset', '-q', '--hard', 'origin/main')
    sys.path.insert(0, os.path.join(CLONE, 'tools'))
    import pull_edits
    changed = pull_edits.main(emit=False)
    if not changed:
        print('אין עריכות חדשות')
        return
    git('add', '-A', 'data/edits')
    git('commit', '-q', '-m', 'עריכות מנקודת הקליטה: ' + ', '.join(changed))
    git('push', '-q', 'origin', 'main')
    print('נדחף:', ', '.join(changed))


def install():
    keep = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_שומר')
    os.makedirs(keep, exist_ok=True)
    bat = os.path.join(keep, 'אפיית-עריכות.cmd')
    here = os.path.dirname(os.path.abspath(__file__))
    io.open(bat, 'w', encoding='utf-8-sig', newline='\r\n').write(
        '@echo off\r\nchcp 65001 > nul\r\ncd /d "%s"\r\n'
        'uv run python tools\bake_edits.py >> "%s" 2>&1\r\n'
        % (os.path.dirname(here), os.path.join(keep, 'אפיית-עריכות.log')))
    r = subprocess.run(['schtasks', '/Create', '/F', '/TN', TASK, '/SC', 'MINUTE', '/MO', '5',
                        '/TR', '"%s"' % bat], capture_output=True)
    print((r.stdout + r.stderr).decode('cp862', 'replace').strip())


if __name__ == '__main__':
    if '--install' in sys.argv:
        install()
    else:
        run()
