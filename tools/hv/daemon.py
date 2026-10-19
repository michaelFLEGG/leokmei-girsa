# -*- coding: utf-8 -*-
"""daemon.py - מריץ בקשות סקירה מן האתר אוטומטית, מהמחשב של המחבר, ממכסת המנוי (claude -p) ולא מחשבון ה-API.

    uv run --with lxml python tools/hv/daemon.py            (לולאה אינסופית; מופעל בכניסה למחשב)
    uv run --with lxml python tools/hv/daemon.py --once     (מעבר אחד, לבדיקה)

כל כמה שניות: בודק את תור הסקירה בנקודת הקליטה; בקשה ממתינה (קודם "עכשיו", אחר כך רגילה, ורק בסוף הכנה מראש) נתפסת, ואז:
  מהירה : בדיקות הקוד של שכבת חברותא + קליטת המועמדים המהותיים (חינם, מיידי).
  רגילה : יישור מרוענן + מודל קטן עם חברותא + קליטה.
  מעמיקה: כנ"ל + מאמת חזק.
הממצאים נקלטים באתר ומופיעים בלוח ההערות; הבקשה מסומנת "הושלמה" עם תקציר. כישלון נרשם כ"נכשלה" עם הסיבה (לא נבלע).
המחשב צריך להיות דלוק ומחובר ל-Claude. כשהוא כבוי הבקשות ממתינות בתור ויורצו כשיידלק.
"""
import os, sys, time, subprocess, json, argparse, traceback, datetime
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import hv_common as H
sys.path.insert(0, os.path.join(H.TOOLS, 'bakara'))
import _api

UV = ['uv', 'run', '--with', 'lxml', 'python']
LOG = os.path.join(H.ROOT, '_work', 'hv-daemon.log')


def log(msg):
    line = '%s %s' % (datetime.datetime.now().strftime('%d.%m %H:%M:%S'), msg)
    print(line, flush=True)
    try:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        with open(LOG, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except OSError:
        pass


def run(args, timeout=7200):
    r = subprocess.run(UV + args, cwd=H.ROOT, capture_output=True, text=True, encoding='utf-8', timeout=timeout,
                       env=dict(os.environ, PYTHONIOENCODING='utf-8', LK_CHAVRUTA=H.CHAV))
    return r.returncode, (r.stdout or '') + (r.stderr or '')


def pending():
    items = (_api.call('/skira/queue').get('doc') or {}).get('items') or []
    p = [x for x in items if x.get('status') == 'pending']
    prio = {'now': 0, None: 1, 'prefetch': 2}
    p.sort(key=lambda x: (prio.get(x.get('prio'), 1), x.get('t', 0)))
    return p, items


def upd(i, status, result=None, prog=None):
    b = {'id': i, 'status': status}
    if result:
        b['result'] = result
    if prog:
        b['prog'] = prog
    _api.call('/skira/queue/update', 'POST', b)


def handle(it):
    slug, d0, d1, depth = it['slug'], it['from'], it['to'], it.get('depth', 'fast')
    heb = {v: k for k, v in H.heb_to_slug().items()}.get(slug)
    if not heb:
        raise RuntimeError('מסכת לא מוכרת: ' + slug)
    upd(it['id'], 'running', prog={'done': 0, 'total': 1, 'next': d0, 'eta': 0})
    log('מתחיל %s %s עד %s (%s)' % (slug, d0, d1, depth))
    rc, out = run(['tools/hv/pack.py', heb])
    if rc:
        raise RuntimeError('יישור נכשל: ' + out[-300:])
    rc, out = run(['tools/hv/checks.py', slug])
    if rc:
        raise RuntimeError('בדיקות קוד נכשלו: ' + out[-300:])
    tag = None
    if depth in ('reg', 'full'):
        tag = 'q' + it['id']
        rc, out = run(['tools/hv/review.py', slug, d0, d1, '--depth', 'deep' if depth == 'full' else 'regular',
                       '--cap-usd', '50', '--tag', tag])
        if rc:
            raise RuntimeError('סקירת המודל נכשלה: ' + out[-300:])
    args = ['tools/hv/publish.py', slug, d0, d1, '--push']
    if tag:
        args += ['--tag', tag]
    rc, out = run(args)
    if rc:
        raise RuntimeError('קליטה נכשלה: ' + out[-300:])
    n = 0
    for ln in out.splitlines():
        if 'ממצאים שנכנסו למיזוג' in ln:
            n = ln.split(':')[1].split('·')[0].strip()
    subprocess.run(['git', 'checkout', '--', 'data'], cwd=H.ROOT, capture_output=True)
    upd(it['id'], 'done', result='נקלטו %s הערות מהמאגר. הן מופיעות בלוח ההערות.' % n)
    log('הושלם %s %s עד %s: %s הערות' % (slug, d0, d1, n))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--once', action='store_true')
    a = ap.parse_args()
    log('השומר הופעל')
    while True:
        try:
            p, items = pending()
            real = [x for x in p if x.get('prio') != 'prefetch']
            todo = real or p
            if todo and todo[0].get('depth') in ('fast', 'reg', 'full'):
                it = todo[0]
                try:
                    handle(it)
                except BaseException as e:
                    log('נכשל: %s' % str(e)[:300])
                    traceback.print_exc()
                    try:
                        upd(it['id'], 'failed', result='נכשלה: ' + str(e)[:300])
                    except BaseException:
                        pass
                continue_now = True
            else:
                continue_now = False
        except BaseException as e:
            log('שגיאת רשת או תור: %s' % str(e)[:200])
            continue_now = False
        if a.once:
            return
        if not continue_now:
            time.sleep(30)


if __name__ == '__main__':
    main()
