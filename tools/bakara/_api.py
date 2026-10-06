# -*- coding: utf-8 -*-
"""_api.py - קריאה לנקודת הקליטה בשם המנהל, לכלי הבקרה.

המפתח נקרא מקובץ המפתח המקומי בלבד (כמו ingest_queue.py), או ממשתנה הסביבה
LG_ADMIN_KEY (לבדיקה מול נקודת קליטה מקומית). הכתובת: LG_API, ובברירת מחדל
נקודת הקליטה החיה."""
import os, io, json, urllib.request, urllib.error

API = os.environ.get('LG_API') or 'https://leokmei-suggest.m7654301.workers.dev'
KEY_FILE = r'C:\Users\Owner\Documents\לאוקמי-מפתח-מנהל.txt'


def admin_key():
    k = os.environ.get('LG_ADMIN_KEY')
    if k:
        return k
    if not os.path.exists(KEY_FILE):
        raise SystemExit('עצירה: קובץ מפתח המנהל אינו קיים: ' + KEY_FILE)
    lines = [l.strip() for l in io.open(KEY_FILE, encoding='utf-8-sig').read().splitlines() if l.strip()]
    for l in reversed(lines):
        if l.isascii() and ' ' not in l and len(l) >= 16:
            return l
    raise SystemExit('עצירה: לא נמצא מפתח בקובץ המפתח')


def call(path, method='GET', body=None):
    data = json.dumps(body, ensure_ascii=False).encode('utf-8') if body is not None else None
    req = urllib.request.Request(API + path, data=data, method=method)
    req.add_header('x-admin-key', admin_key())
    req.add_header('User-Agent', 'leokmei-bakara/1.0')
    if data is not None:
        req.add_header('content-type', 'application/json; charset=utf-8')
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        raise SystemExit('עצירה: נקודת הקליטה החזירה %s על %s: %s' % (e.code, path, e.read().decode('utf-8', 'replace')[:200]))
