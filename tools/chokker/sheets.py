# -*- coding: utf-8 -*-
"""החוקר - גיליונות מגע לעיון בעיניים.

מצרף את צילומי ההליכה לגיליונות (6 מסכים או 8 עמודי הדפסה בגיליון) עם תווית לכל תמונה, כדי שהמוח הלילי
יראה הרבה מסכים בקריאה אחת. --changed: רק מסכים שהמראה שלהם השתנה מן ההרצה הקודמת (לפי dh), ועוד כל
מסך שיש בו ממצא.

  python tools/chokker/sheets.py data/chokker/runs/2026-11-26 [--changed data/chokker/runs/2026-11-25] [--max 60]
"""
import os, sys, io, json, argparse
from PIL import Image, ImageDraw, ImageFont


def font(sz):
    for f in ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/usr/share/fonts/truetype/freefont/FreeSans.ttf'):
        if os.path.exists(f):
            return ImageFont.truetype(f, sz)
    return ImageFont.load_default()


def grid(items, out, cols, cellw, cellh, title):
    F = font(15)
    W, H = cols * cellw, ((len(items) + cols - 1) // cols) * (cellh + 22) + 26
    sh = Image.new('RGB', (W, H), 'white')
    d = ImageDraw.Draw(sh)
    d.text((6, 4), title, fill='black', font=F)
    for k, (path, label) in enumerate(items):
        x, y = (k % cols) * cellw, 26 + (k // cols) * (cellh + 22)
        try:
            im = Image.open(path).convert('RGB')
            im.thumbnail((cellw - 6, cellh))
            sh.paste(im, (x + 3, y + 20))
            d.rectangle([x + 3, y + 20, x + 3 + im.width, y + 20 + im.height], outline='#999')
        except Exception:
            d.text((x + 6, y + 40), 'missing', fill='red', font=F)
        d.text((x + 4, y + 2), label[:60], fill='#003', font=F)
    sh.save(out, quality=62)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('run')
    ap.add_argument('--changed', default='')
    ap.add_argument('--max', type=int, default=80)
    a = ap.parse_args()
    w = json.load(io.open(os.path.join(a.run, 'walk.json'), encoding='utf-8'))
    old = {}
    if a.changed and os.path.exists(os.path.join(a.changed, 'walk.json')):
        for s in json.load(io.open(os.path.join(a.changed, 'walk.json'), encoding='utf-8'))['screens']:
            for t in s.get('tiles') or []:
                old[t['path']] = t.get('dh')
    od = os.path.join(a.run, 'sheets')
    os.makedirs(od, exist_ok=True)
    screens, prints = [], []
    for s in w['screens']:
        flagged = bool((s.get('probe') or {}).get('v')) or s.get('fatal')
        for t in s.get('tiles') or []:
            if not t.get('path'):
                continue
            if a.changed and old.get(t['path']) == t.get('dh') and not flagged:
                continue
            screens.append((os.path.join(a.run, t['path']), '%s %s %s %d/%d' % (os.path.basename(str(s['page']))[:22], s['vp'], s['mode'], t['i'] + 1, t['of'])))
    for b in w.get('buttons', []):
        if b.get('shot'):
            screens.append((os.path.join(a.run, b['shot']), 'btn %s: %s' % (b['vp'], b['btn'])))
    for p in w.get('print', []):
        for t in ((p.get('measure') or {}).get('thumbs') or []):
            prints.append((os.path.join(a.run, t), '%s %s %s' % (p['page'], p['profile'], os.path.basename(t)[-8:-4])))
    n = 0
    for i in range(0, min(len(screens), a.max * 6), 6):
        grid(screens[i:i + 6], os.path.join(od, 'screens-%03d.jpg' % (i // 6)), 3, 640, 430, 'screens %d-%d / %d' % (i + 1, min(i + 6, len(screens)), len(screens)))
        n += 1
    for i in range(0, min(len(prints), a.max * 8), 8):
        grid(prints[i:i + 8], os.path.join(od, 'print-%03d.jpg' % (i // 8)), 4, 420, 600, 'print %d-%d / %d' % (i + 1, min(i + 8, len(prints)), len(prints)))
        n += 1
    print('sheets:', n, 'screens', len(screens), 'print pages', len(prints))


if __name__ == '__main__':
    main()
