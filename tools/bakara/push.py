# -*- coding: utf-8 -*-
"""push.py - מעלה את קובצי הממצאים (data/bakara/<מסכת>-<פרק>.json) לנקודת הקליטה.

הממצאים אינם נכנסים לאתר הציבורי: האתר מושך אותם מנקודת הקליטה רק אחרי
שהמכשיר הוכר כמנהל. כל העלאה מחליפה את הפרק, ואינה נוגעת בהכרעות.

    uv run python tools/bakara/push.py [slug-perek ...]    (בלי ארגומנטים: כולם)
"""
import os, sys, re, json, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _api

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def push(path):
    m = re.match(r'^([a-z-]+)-(\d+)\.json$', os.path.basename(path))
    if not m:
        return False
    d = json.load(open(path, encoding='utf-8'))
    r = _api.call('/bakara/data', 'PUT', {'slug': m.group(1), 'perek': int(m.group(2)), 'data': d})
    print('הועלה', os.path.basename(path), '-', r.get('n'), 'ממצאים')
    return True


if __name__ == '__main__':
    files = [os.path.join(ROOT, 'data', 'bakara', a + ('' if a.endswith('.json') else '.json')) for a in sys.argv[1:]] \
        or sorted(glob.glob(os.path.join(ROOT, 'data', 'bakara', '*-[0-9]*.json')))
    n = sum(1 for f in files if push(f))
    print(n, 'קבצים')
