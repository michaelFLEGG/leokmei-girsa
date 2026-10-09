# -*- coding: utf-8 -*-
"""quick_site.py - עדכון מהיר של נכסי המעטפת באתר המקומי (בלי לבנות מסכתות): ui.css, mobile.*, lamed.js/css.
שימוש: uv run python tools/quick_site.py"""
import os, sys, shutil
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
SITE = os.path.join(os.path.dirname(HERE), 'site')
import build_lamed
build_lamed.build(SITE)
for f in ('mobile.css', 'mobile.js'):
    shutil.copy(os.path.join(HERE, f), os.path.join(SITE, f))
print('ok')
