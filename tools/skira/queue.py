# -*- coding: utf-8 -*-
"""queue.py - תור בקשות הסקירה ("בקש סקירה" מתוך הדף).

    uv run python tools/skira/queue.py list              בקשות ממתינות
    uv run python tools/skira/queue.py claim <מזהה>      סימון "רצה"
    uv run python tools/skira/queue.py done <מזהה> "תוצאה"
    uv run python tools/skira/queue.py fail <מזהה> "סיבה"
    uv run python tools/skira/queue.py replies           שרשורי "שוחח" שהמחבר כתב בהם אחרון
    uv run python tools/skira/queue.py prefetch <מסכת> [מספר-דפים]
                                                         מזמין מראש סקירה רגילה (כולל ביאור חברותא) לדפים שאחרי מה שנסקר לאחרונה (הכנה מראש)
    uv run python tools/skira/queue.py progress <מזהה> <הושלמו> <סה"כ> [דף-הבא] [דקות]
                                                         מעדכן את פס המצב שבדף ("הושלמו 3 דפים מתוך 11")

הפקודה בווקר "הרץ סקירות ממתינות" מבצעת את docs/skira/הפעלה.md, שמתחיל כאן.
"""
import os, sys, json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import skira_common as C
import _api


def items():
    return (_api.call('/skira/queue').get('doc') or {}).get('items') or []


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'list'
    if cmd == 'list':
        for it in items():
            if it.get('status') == 'pending':
                print('%s | %s %s עד %s | %s | אומדן %s | %s' % (it['id'], it['slug'], it['from'], it['to'], it['depth'],
                                                               it.get('est'), it.get('note', '')))
        return
    if cmd in ('claim', 'done', 'fail'):
        st = {'claim': 'running', 'done': 'done', 'fail': 'failed'}[cmd]
        res = sys.argv[3] if len(sys.argv) > 3 else ''
        r = _api.call('/skira/queue/update', 'POST', {'id': sys.argv[2], 'status': st, 'result': res})
        print('עודכן:', st)
        return
    if cmd == 'prefetch':
        slug = sys.argv[2]
        n = int(sys.argv[3]) if len(sys.argv) > 3 else 6
        src = C.jload(os.path.join(C.ROOT, 'data', 'sources', slug + '.json'), {})
        pages = list((src.get('pages') or {}).keys())
        done = [x for x in items() if x.get('slug') == slug and x.get('status') in ('done', 'pending', 'running')]
        last = done[-1]['to'] if done else None
        i = pages.index(last) + 1 if last in pages else 0
        rng = pages[i:i + n]
        if not rng:
            print('אין דפים להכנה מראש.')
            return
        r = _api.call('/skira/queue', 'POST', {'slug': slug, 'from': rng[0], 'to': rng[-1], 'depth': 'reg',
                                               'note': 'הכנה מראש (רגילה, כולל ביאור חברותא)', 'est': 19000 * len(rng), 'prio': 'prefetch'})
        print('נרשמה הכנה מראש:', slug, rng[0], 'עד', rng[-1], r['item']['id'])
        return
    if cmd == 'progress':
        i = sys.argv[2]
        done, total = int(sys.argv[3]), int(sys.argv[4])
        nxt = sys.argv[5] if len(sys.argv) > 5 else ''
        eta = int(sys.argv[6]) if len(sys.argv) > 6 else 0
        _api.call('/skira/queue/update', 'POST', {'id': i, 'status': 'running',
                                                  'prog': {'done': done, 'total': total, 'next': nxt, 'eta': eta}})
        print('התקדמות עודכנה: %d/%d' % (done, total))
        return
    if cmd == 'replies':
        for s in C.slugs_with_findings():
            r = _api.call('/skira/threads?slug=' + s)
            for fid, msgs in (r.get('open') or {}).items():
                print(s, fid, '|', msgs[-1]['txt'][:200])
        return
    print(__doc__)


if __name__ == '__main__':
    main()
