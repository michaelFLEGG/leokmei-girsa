# -*- coding: utf-8 -*-
"""שותל את תג feel.js (צליל לחיצה ורטט קל) בכל דפי האתר. אידמפוטנטי; מרענן את חותמת התוכן.
הרצה:  python tools/add_feel.py   (נקרא גם בסוף build_all)"""
import io, os, re, hashlib, sys

SITE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "site")
TAG_RE = re.compile(r'<script src="/feel\.js(?:\?v=[0-9a-f]+)?" defer></script>')


def run(site=SITE):
    h = hashlib.md5(io.open(os.path.join(site, 'feel.js'), 'rb').read()).hexdigest()[:8]
    tag = '<script src="/feel.js?v=%s" defer></script>' % h
    added = refreshed = 0
    for root, dirs, files in os.walk(site):
        for f in files:
            if not f.endswith('.html'):
                continue
            p = os.path.join(root, f)
            s = io.open(p, encoding='utf-8').read()
            if TAG_RE.search(s):
                n = TAG_RE.sub(tag, s, count=1)
                if n != s:
                    io.open(p, 'w', encoding='utf-8', newline='').write(n); refreshed += 1
                continue
            for needle in ('</body>', '</head>'):
                i = s.rfind(needle)
                if i >= 0:
                    s = s[:i] + tag + s[i:]
                    break
            else:
                s = s + tag
            io.open(p, 'w', encoding='utf-8', newline='').write(s); added += 1
    print('feel.js: נשתל ב-%d דפים, רוענן ב-%d' % (added, refreshed))


if __name__ == '__main__':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    run()
