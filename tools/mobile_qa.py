# -*- coding: utf-8 -*-
"""mobile_qa.py - צילומי מסך ובדיקות אוטומטיות בכל גדלי הטלפון, הטאבלט והמחשב.

הרצה:
  uv run --with playwright python tools/mobile_qa.py --base http://127.0.0.1:8731 --out docs/qa/2026-10-09/before
  (--base https://leokmei.com לסבב על האתר החי)

בכל צילום נמדדים חמישה דברים (מנה 9.10.2026, סעיף ג):
  1 hscroll    - אין גלילה אופקית בעמוד
  2 rail       - אף כותרת צד אינה חופפת לטקסט הרץ
  3 touch      - יעדי מגע לפחות 44x44, ומרווח 8 בין סמוכים
  4 clip       - שום טקסט ממשק אינו נחתך או גולש מכפתור
  5 lastline   - הקונסולה התחתונה אינה מסתירה את השורה האחרונה
הפלט: <out>/<מכשיר>-<כיוון>/<עמוד>.png ו-results.json
"""
import os, sys, json, argparse, io, traceback
from playwright.sync_api import sync_playwright

PHONES = [('p360x800', 360, 800, 3), ('p390x844', 390, 844, 3), ('p412x915', 412, 915, 2.6), ('p375x667', 375, 667, 2)]
TABLETS = [('t-tabA7', 800, 1334, 2), ('t768x1024', 768, 1024, 2), ('t820x1180', 820, 1180, 2), ('t1024x1366', 1024, 1366, 2)]
DESKTOPS = [('d1366x768', 1366, 768, 1), ('d1920x1080', 1920, 1080, 1)]

JS_METRICS = r'''(opts) => {
  const out = {};
  const de = document.documentElement;
  out.hscroll = {sw: Math.max(de.scrollWidth, document.body.scrollWidth), cw: de.clientWidth,
                 ok: Math.max(de.scrollWidth, document.body.scrollWidth) <= de.clientWidth + 1};
  const vis = e => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none' && cs.opacity !== '0'; };
  // 2. כותרות צד מול טקסט רץ
  const bad = [];
  const rows = [...document.querySelectorAll('.row')].filter(r => { const b = r.getBoundingClientRect(); return b.bottom > 0 && b.top < innerHeight; }).slice(0, 60);
  for (const row of rows) {
    const rail = row.querySelector(':scope > .rail'); const main = row.querySelector(':scope > .main');
    if (!rail || !main) continue;
    const kids = [...rail.children].filter(vis);
    const lines = [];
    const tw = document.createTreeWalker(main, NodeFilter.SHOW_TEXT);
    let n; while ((n = tw.nextNode())) { if (!n.nodeValue.trim()) continue; const rg = document.createRange(); rg.selectNodeContents(n);
      for (const q of rg.getClientRects()) if (q.width > 2 && q.height > 2) lines.push(q); }
    for (const k of kids) { const a = k.getBoundingClientRect();
      for (const q of lines) { const ox = Math.min(a.right, q.right) - Math.max(a.left, q.left), oy = Math.min(a.bottom, q.bottom) - Math.max(a.top, q.top);
        if (ox > 1.5 && oy > 3) { bad.push({rail: (k.className || k.tagName) + ':' + (k.textContent || '').trim().slice(0, 18), ox: Math.round(ox), oy: Math.round(oy)}); break; } } }
  }
  out.rail = {n: rows.length, overlaps: bad.slice(0, 6), count: bad.length, ok: bad.length === 0};
  // 3. יעדי מגע
  const sel = 'button, a[href], select, input:not([type=hidden]), [role=button], summary';
  const hit = e => { const r = e.getBoundingClientRect(); const x = Math.min(innerWidth - 1, Math.max(0, r.left + r.width / 2)), y = Math.min(innerHeight - 1, Math.max(0, r.top + r.height / 2));
    if (r.bottom < 0 || r.top > innerHeight) return true; const t = document.elementFromPoint(x, y); return !t || e.contains(t) || t.contains(e); };
  const ints = [...document.querySelectorAll(sel)].filter(e => vis(e) && !e.closest('.flow .main, .src .srcbody, .sheet, #flow .row, [hidden]') && hit(e));
  const small = [], crowd = [];
  const rects = ints.map(e => ({e, r: e.getBoundingClientRect()})).filter(o => o.r.bottom > 0 && o.r.top < innerHeight && o.r.right > 0 && o.r.left < innerWidth);
  for (const o of rects) if (o.r.width < 43.5 || o.r.height < 43.5)
    small.push((o.e.id ? '#' + o.e.id : (o.e.className && typeof o.e.className === 'string' ? '.' + o.e.className.split(' ')[0] : o.e.tagName)) + ' ' + Math.round(o.r.width) + 'x' + Math.round(o.r.height) + ' "' + (o.e.textContent || o.e.getAttribute('aria-label') || '').trim().slice(0, 14) + '"');
  for (let i = 0; i < rects.length; i++) for (let j = i + 1; j < rects.length; j++) {
    const a = rects[i].r, b = rects[j].r;
    if (rects[i].e.contains(rects[j].e) || rects[j].e.contains(rects[i].e)) continue;
    const gx = Math.max(a.left, b.left) - Math.min(a.right, b.right), gy = Math.max(a.top, b.top) - Math.min(a.bottom, b.bottom);
    const gap = Math.max(gx, gy);   // שלילי = חופפים בשני הצירים
    if (gx < 0 && gy < 0) { crowd.push('חפיפה ' + (rects[i].e.textContent || '').trim().slice(0, 10) + ' / ' + (rects[j].e.textContent || '').trim().slice(0, 10)); }
    else if (gap >= 0 && gap < 7.5 && (gx < 0 || gy < 0)) crowd.push('מרווח ' + Math.round(gap) + ' ' + (rects[i].e.textContent || '').trim().slice(0, 10) + ' / ' + (rects[j].e.textContent || '').trim().slice(0, 10));
  }
  if (!opts.mobile) { small.length = 0; crowd.length = 0; }
  out.touch = {n: rects.length, small: small.slice(0, 12), smallCount: small.length, crowd: crowd.slice(0, 8), crowdCount: crowd.length, ok: small.length === 0 && crowd.length === 0};
  // 4. טקסט חתוך
  const clip = [];
  for (const e of document.querySelectorAll('button, .lm-btn, .ddb, label, a.lm-btn, .seg button, h1, h2, h3, nav a')) {
    if (!vis(e) || e.closest('.flow, .sheet, #flow, #lm-layer') || e.clientWidth < 4) continue;
    const cs = getComputedStyle(e);
    if (e.scrollWidth > e.clientWidth + 2 && cs.display !== 'inline' && cs.overflowX !== 'visible' ) clip.push((e.textContent || '').trim().slice(0, 18) + ' ' + e.scrollWidth + '>' + e.clientWidth);
    const r = e.getBoundingClientRect();
    if (r.right > innerWidth + 1 || r.left < -1) { if (r.width > 0) clip.push('מחוץ למסך: ' + (e.textContent || '').trim().slice(0, 18)); }
  }
  out.clip = {items: clip.slice(0, 8), count: clip.length, ok: clip.length === 0};
  // 5. השורה האחרונה מול הקונסולה התחתונה
  const fl = document.querySelector('#flow');
  if (fl && opts.lastline) {
    const bb = document.querySelector('#mbot'); // הסרגל התחתון (אם קיים)
    fl.scrollTop = fl.scrollHeight; window.scrollTo(0, document.body.scrollHeight);
    const rws = [...fl.querySelectorAll('.row, .sheet')]; const last = rws[rws.length - 1];
    let obscured = false, info = '';
    if (last) { const r = last.getBoundingClientRect(); const pts = [[innerWidth / 2, Math.min(innerHeight - 2, r.bottom - 6)]];
      const el = document.elementFromPoint(pts[0][0], pts[0][1]);
      if (el && bb && bb.contains(el) && r.bottom > bb.getBoundingClientRect().top + 1) { obscured = true; }
      info = Math.round(r.bottom) + '/' + innerHeight; }
    out.lastline = {ok: !obscured, info};
  } else out.lastline = {ok: true, info: 'לא רלוונטי'};
  return out;
}'''

PAGES = [
    ('01-shaar', 'index.html', None),
    ('02-shas-map', 'shas.html', None),
    ('03-masechet-map', 'masechet.html?m=berakhot', None),
    ('04-daf-col', 'berakhot.html#daf=%D7%95%3A', 'col'),
    ('05-daf-book', 'berakhot.html#daf=%D7%95%3A', 'book'),
    ('06-perush', 'berakhot.html#daf=%D7%95%3A', 'perush'),
    ('06b-perush-full', 'berakhot.html#daf=%D7%95%3A', 'perushfull'),
    ('07-tzura', 'berakhot.html#daf=%D7%95%3A', 'tzura'),
    ('08-quiz-open', 'quiz.html', None),
    ('09-lamed', 'lamed.html', None),
    ('10-suggest', 'berakhot.html#daf=%D7%95%3A', 'suggest'),
]


def prep_daf(page, action, kind):
    page.wait_for_selector('#flow .row', timeout=30000)
    page.wait_for_timeout(500)
    if action == 'col':
        if kind == 'desk': page.evaluate("typeof setView==='function'&&setView('col')")
    elif action == 'book':
        if kind == 'tab':
            page.evaluate("if(window.LGMOBILE){localStorage.setItem('lg-mmode','book');LGMOBILE.applyMode(true)}else if(typeof setView==='function')setView('book')")
        elif kind == 'phone':
            page.evaluate("var b=document.querySelector('#mbot [data-a=more]');if(b)b.click();else if(typeof setView==='function')setView('book')")   # בטלפון אין ספר: מראים את גיליון "עוד"
        else:
            page.evaluate("typeof setView==='function'&&setView('book')")
    elif action == 'pick':
        page.evaluate("document.querySelector('#mttl')&&document.querySelector('#mttl').click()")
    elif action == 'perush':
        page.evaluate("typeof gemaraBtn==='function'&&gemaraBtn()")
    elif action == 'perushfull':
        page.evaluate("typeof gemaraBtn==='function'&&gemaraBtn()"); page.wait_for_timeout(700)
        page.evaluate("var h=document.querySelector('#msh');if(h){h.dispatchEvent(new PointerEvent('pointerdown',{clientY:300,pointerId:1}));h.dispatchEvent(new PointerEvent('pointerup',{clientY:300,pointerId:1}))}")
    elif action == 'tzura':
        page.evaluate("typeof tzBtn==='function'&&tzBtn()")
    elif action == 'suggest':
        page.evaluate("typeof suggest==='function'&&suggest()")
    page.wait_for_timeout(1100)


def run(base, out, only, orients, wk):
    results = {}
    devs = PHONES + TABLETS + DESKTOPS
    if only:
        devs = [d for d in devs if any(o in d[0] for o in only)]
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        for name, w, h, dpr in devs:
            mobile = not name.startswith('d')
            for ori in (orients if mobile else ['l']):
                vw, vh = (w, h) if ori == 'p' else (h, w)
                if not mobile: vw, vh = w, h
                key = '%s-%s' % (name, 'portrait' if ori == 'p' else 'landscape') if mobile else name
                ctx = br.new_context(viewport={'width': vw, 'height': vh}, device_scale_factor=dpr, is_mobile=mobile, has_touch=mobile,
                                     locale='he-IL', ignore_https_errors=True)
                d = os.path.join(out, key); os.makedirs(d, exist_ok=True)
                for pname, path, action in PAGES:
                    pg = ctx.new_page(); errs = []
                    pg.on('pageerror', lambda e, errs=errs: errs.append(str(e)[:120]))
                    try:
                        pg.goto(base.rstrip('/') + '/' + path, wait_until='domcontentloaded', timeout=45000)
                        if action is not None: prep_daf(pg, action, ('phone' if name.startswith('p') else 'tab' if name.startswith('t') else 'desk'))
                        else: pg.wait_for_timeout(1400)
                        pg.screenshot(path=os.path.join(d, pname + '.png'))
                        m = pg.evaluate(JS_METRICS, {'lastline': action in ('col', 'book'), 'mobile': mobile})
                        m['errors'] = errs
                    except Exception as e:
                        m = {'fatal': traceback.format_exc()[-300:]}
                    results.setdefault(key, {})[pname] = m
                    pg.close()
                ctx.close()
                print(key, 'done', flush=True)
        br.close()
    json.dump(results, io.open(os.path.join(out, 'results.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return results


def summarize(res):
    tot = {'hscroll': 0, 'rail': 0, 'touch': 0, 'clip': 0, 'lastline': 0, 'fatal': 0, 'errors': 0}
    for dev, pgs in res.items():
        for p, m in pgs.items():
            if 'fatal' in m: tot['fatal'] += 1; continue
            for k in ('hscroll', 'rail', 'touch', 'clip', 'lastline'):
                if not m[k]['ok']: tot[k] += 1
            if m.get('errors'): tot['errors'] += 1
    return tot


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--only', default=''); ap.add_argument('--orient', default='pl')
    a = ap.parse_args()
    r = run(a.base, a.out, [x for x in a.only.split(',') if x], list(a.orient), None)
    print(json.dumps(summarize(r), ensure_ascii=False))
