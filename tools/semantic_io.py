# -*- coding: utf-8 -*-
"""semantic_io.py - קלט/פלט לתיקון הסמנטי הבסיסי (21.11.2026, בקשת מיכאל על שבת).

שני מצבים, דרך push-edits-server.yml (שם יש מפתח המנהל ורשת):
  dump:<slug>   טוען את הדף החי בדפדפן (כמו כל גולש, אחרי /live), וכותב ליומן את מצב כל השורות
                כפי שהן על המסך (מפתח, סגנון פסקה, HTML, טקסט, כותרת הצד של השורה) - דחוס, בין סמנים.
  file:<path>   מעלה לנקודת הקליטה רק את העריכות שבקובץ (PUT /edits, מיזוג לפי מפתח וזמן).
"""
import os, sys, json, gzip, base64, time, subprocess, urllib.request

API = 'https://leokmei-suggest.m7654301.workers.dev'
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

JS = r"""
() => {
  const out = [];
  const rows = [...document.querySelectorAll('#flow .row')];
  rows.forEach((r, ri) => {
    const anc = r.querySelector('.anchor');
    const side = anc ? anc.textContent : '';
    const dm = r.querySelector('.dafmark');
    const ps = [...r.querySelectorAll('.main p')];
    if (!ps.length) out.push({ri, rc: r.className, side, t: r.textContent.trim(), daf: dm ? (dm.dataset.daf || dm.textContent) : ''});
    ps.forEach((p, pi) => out.push({ri, pi, rc: r.className, side: pi === 0 ? side : '', ek: p.dataset.ek || '',
      c: p.className, h: p.innerHTML, t: p.textContent, daf: dm ? (dm.dataset.daf || dm.textContent) : ''}));
  });
  return out;
}
"""


def dump(slug):
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', 'playwright'], check=True)
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        try:
            b = pw.chromium.launch(channel='chrome')
        except Exception:
            subprocess.run([sys.executable, '-m', 'playwright', 'install', 'chromium'], check=True)
            b = pw.chromium.launch()
        pg = b.new_page(viewport={'width': 1400, 'height': 900})
        pg.goto('https://leokmei.com/' + slug, wait_until='networkidle', timeout=180000)
        last = -1
        for _ in range(40):
            time.sleep(3)
            n = pg.evaluate("() => document.querySelectorAll('#flow .main p').length + '|' + document.querySelectorAll('#flow .row').length")
            if n == last:
                break
            last = n
        time.sleep(8)
        data = pg.evaluate(JS)
        b.close()
    live = json.loads(urllib.request.urlopen(urllib.request.Request(API + '/live?slug=' + slug,
                      headers={'user-agent': 'Mozilla/5.0 leokmei-sem/1.0'}), timeout=120).read().decode('utf-8'))
    blob = base64.b64encode(gzip.compress(json.dumps({'rows': data, 'live': live.get('doc', {}).get('edits', [])},
                                                     ensure_ascii=False).encode('utf-8'))).decode('ascii')
    print('lines', len(data), 'live', len(live.get('doc', {}).get('edits', [])))
    print('=====SEMDUMP-BEGIN=====')
    for i in range(0, len(blob), 4000):
        print(blob[i:i + 4000])
    print('=====SEMDUMP-END=====')


def put_file(path):
    key = os.environ.get('LEOKMEI_ADMIN_KEY', '').strip()
    if not key:
        sys.exit('אין מפתח מנהל')
    req = json.load(open(os.path.join(HERE, path), encoding='utf-8'))
    body = json.dumps({'slug': req['slug'], 'edits': req['edits']}, ensure_ascii=False).encode('utf-8')
    r = urllib.request.Request(API + '/edits', data=body, method='PUT', headers={
        'content-type': 'application/json; charset=utf-8', 'x-admin-key': key, 'user-agent': 'Mozilla/5.0 leokmei-sem/1.0'})
    with urllib.request.urlopen(r, timeout=180) as resp:
        d = json.loads(resp.read().decode('utf-8'))
    print('OK sent', len(req['edits']), 'server', len((d.get('doc') or {}).get('edits') or []))


if __name__ == '__main__':
    a = sys.argv[1]
    if a.startswith('dump:'):
        dump(a[5:])
    elif a.startswith('file:'):
        put_file(a[5:])
