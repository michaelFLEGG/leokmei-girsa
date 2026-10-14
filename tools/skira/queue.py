# -*- coding: utf-8 -*-
"""queue.py - תור בקשות הסקירה ("בקש סקירה" מתוך הדף).

    uv run python tools/skira/queue.py list              בקשות ממתינות
    uv run python tools/skira/queue.py claim <מזהה>      סימון "רצה"
    uv run python tools/skira/queue.py done <מזהה> "תוצאה"
    uv run python tools/skira/queue.py fail <מזהה> "סיבה"
    uv run python tools/skira/queue.py replies           שרשורי "שוחח" שהמחבר כתב בהם אחרון

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
    if cmd == 'replies':
        for s in C.slugs_with_findings():
            r = _api.call('/skira/threads?slug=' + s)
            for fid, msgs in (r.get('open') or {}).items():
                print(s, fid, '|', msgs[-1]['txt'][:200])
        return
    print(__doc__)


if __name__ == '__main__':
    main()
