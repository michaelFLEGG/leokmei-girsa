"""fetch.py - מוריד את קובצי הוורד והגופנים מתיקיות הדרייב המשותפות.
עובד בלי מפתחות: התיקיות משותפות "לכל מי שיש לו את הקישור".
1. מנסה לקרוא את רשימת הקבצים מדף התיקייה הציבורי (embeddedfolderview).
2. אם נכשל, משתמש ברשימת הגיבוי שב-sources.json.
"""
import json, re, sys, os, hashlib, urllib.request, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = json.load(open(os.path.join(ROOT, 'sources.json'), encoding='utf-8'))
UA = {'User-Agent': 'Mozilla/5.0 (leokmei-girsa watcher)'}

def get(url, binary=True):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=120) as r:
        data = r.read()
    return data if binary else data.decode('utf-8', 'replace')

def list_folder(folder_id):
    """מחזיר {שם: id} מתוך דף התיקייה הציבורי; None אם נכשל."""
    try:
        page = get(f'https://drive.google.com/embeddedfolderview?id={folder_id}#list', binary=False)
    except Exception as e:
        print('list failed:', e); return None
    out = {}
    for m in re.finditer(r'id="entry-([\w-]+)".*?flip-entry-title">(.*?)</div>', page, re.S):
        out[html.unescape(m.group(2)).strip()] = m.group(1)
    return out or None

def download(file_id):
    url = f'https://drive.google.com/uc?export=download&id={file_id}'
    data = get(url)
    if data[:15].lower().startswith(b'<!doctype html') or b'<html' in data[:300].lower():
        # large-file confirmation page
        m = re.search(rb'confirm=([\w-]+)', data)
        if m:
            data = get(url + '&confirm=' + m.group(1).decode())
    return data

def sync(folder_id, fallback, dest, exts, roster=None):
    os.makedirs(dest, exist_ok=True)
    listed = list_folder(folder_id)
    files = listed or fallback
    changed = False
    if listed and roster:
        # רשימת השמות שבתיקייה עכשיו. קובץ שהמנהל שינה את שמו נשאר כגיבוי
        # ואינו נמחק, אך הבנייה תדע להתעלם ממנו ולבנות מן הקובץ החי.
        names = sorted(n for n in listed if n.lower().endswith(exts) and not n.startswith('._'))
        if len(names) >= 5:
            json.dump(names, open(roster, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    for name, fid in files.items():
        if not name.lower().endswith(exts) or name.startswith('._'):
            continue
        path = os.path.join(dest, name)
        try:
            data = download(fid)
        except Exception as e:
            print('download failed', name, e); continue
        old = open(path, 'rb').read() if os.path.exists(path) else b''
        if hashlib.md5(old).digest() != hashlib.md5(data).digest():
            open(path, 'wb').write(data); changed = True
            print('updated', name, len(data))
    return changed

if __name__ == '__main__':
    c1 = sync(SRC['docx_folder'], SRC['fallback_files'], os.path.join(ROOT, 'input', 'docx'), ('.docx',),
              roster=os.path.join(ROOT, 'input', 'current-docx.json'))
    c2 = sync(SRC['fonts_folder'], SRC['fallback_fonts'], os.path.join(ROOT, 'input', 'fonts'), ('.otf', '.ttf'))
    print('CHANGED' if (c1 or c2) else 'NOCHANGE')
