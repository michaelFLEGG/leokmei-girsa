"""גיבוי יומי של כל נתוני המשתמשים במחסן של נקודת הקליטה (leokmei-suggest).

נכתב אחרי התקלה של 7.10.2026: כל הנתונים נשמרים בקובץ עם חותמת זמן, ואף ערך
אינו נמחק או נכתב. מריצים: uv run python tools/backup_kv.py
נשמרים 21 הגיבויים האחרונים."""
import concurrent.futures as cf
import datetime
import json
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WDIR = os.path.join(ROOT, 'worker', 'leokmei-suggest')
NS = '94cebf3b2d294c3d903ee0be904f041c'
OUT = os.path.join(os.path.expanduser('~'), 'Documents', 'גיבוי-לאוקמי-יומי')
KEEP = 21


def wr(*args):
    r = subprocess.run(['npx', '--yes', 'wrangler', *args], capture_output=True, cwd=WDIR, shell=(os.name == 'nt'))
    return r.returncode, r.stdout.decode('utf-8', 'replace')


def main():
    code, out = wr('kv', 'key', 'list', '--namespace-id', NS, '--remote')
    if code:
        print('הרשימה לא נקראה', file=sys.stderr)
        return 1
    keys = json.loads(out)
    stamp = datetime.datetime.now().strftime('%Y-%m-%d_%H%M')
    os.makedirs(OUT, exist_ok=True)

    def get(k):
        c, v = wr('kv', 'key', 'get', k['name'], '--namespace-id', NS, '--remote')
        return k['name'], (v if c == 0 else None), k.get('metadata')

    vals = {}
    bad = []
    with cf.ThreadPoolExecutor(8) as ex:
        for name, v, meta in ex.map(get, keys):
            if v is None:
                bad.append(name)
            else:
                vals[name] = {'v': v, 'm': meta}
    if bad:                                   # עצירה רועשת: גיבוי חלקי אינו גיבוי
        print('נכשלה קריאת %d מפתחות: %s' % (len(bad), bad[:5]), file=sys.stderr)
        return 2
    path = os.path.join(OUT, 'kv-%s.json' % stamp)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump({'when': stamp, 'count': len(vals), 'keys': vals}, f, ensure_ascii=False)
    old = sorted(x for x in os.listdir(OUT) if x.startswith('kv-'))[:-KEEP]
    for x in old:
        os.remove(os.path.join(OUT, x))
    print('גובו %d מפתחות ל-%s' % (len(vals), path))
    return 0


if __name__ == '__main__':
    sys.exit(main())
