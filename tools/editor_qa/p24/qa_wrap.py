# -*- coding: utf-8 -*-
"""מריץ את editor_qa על האתר החי כשקוד העורך (mas.js) מוגש מקובץ מקומי, וכל כתיבה חסומה.
שימוש: qa_wrap.py <mas.js מקומי או "-" לחי> <args של editor_qa...>"""
import sys, os, io
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'editor_qa'))
import editor_qa as Q
mas = sys.argv[1]; sys.argv = [sys.argv[0]] + sys.argv[2:]
_open = Q.open_ctx
def open_ctx(pw, a, token):
    br, ctx = _open(pw, a, token)
    if mas != '-':
        body = io.open(mas, 'rb').read()
        ctx.route('**/mas.js*', lambda r: r.fulfill(status=200, content_type='application/javascript; charset=utf-8', body=body))
    ctx.route('**/sw.js*', lambda r: r.fulfill(status=200, content_type='application/javascript', body=''))
    return br, ctx
Q.open_ctx = open_ctx
Q.main()
