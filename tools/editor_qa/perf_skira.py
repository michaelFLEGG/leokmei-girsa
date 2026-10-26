# -*- coding: utf-8 -*-
"""perf_skira.py - מכשיר מדידה קבוע לסקירה במצב מנהל אמיתי (פרומפט 8, 26.10.2026).

פותח דף מסכת בדפדפן Chromium עם פרופיל של מנהל (עותק של אחסון הדפדפן המזוהה),
חוסם כל כתיבה (כל בקשה שאינה GET אל Worker, אל GitHub ואל הגשר המקומי), ומודד:
  load    - מן הניווט ועד שהדף מגיב: סוף המשימה האחרונה שנמשכה 100 מ"ש ומעלה (load_quiet: עד שקט מלא של 2.5 שניות)
  dcl     - DOMContentLoaded
  idle    - כמה מ"ש מתוך 10 שניות בלי שום פעולה הדף תפוס במשימות ארוכות
  open    - פתיחת הסקירה עד שקט
  next    - מעבר להערה הבאה: עד שהכרטיס החדש מוצג, ועד שקט
  accept  - קבל ומעבר: עד שהכרטיס הבא מוצג, ועד שקט (רק עם --decide N; ההכרעות נחסמות ברשת)
  pending - ממצאים ממתינים בלי הצעה כתובה (op none) ומספר הממתינים

הקוד החדש נבדק לפני פרסום בהזרקה: --site <תיקיית site מקומית> מנתב את mas.js, lamed.js, mobile.js ו-<slug>.x.js
מהאתר החי אל הקבצים המקומיים. בלי --site נמדד האתר החי כפי שהוא.

הרצה:
  uv run --with playwright python tools/editor_qa/perf_skira.py --profile <פרופיל> --slug bekhorot --sq 1 --out docs/skira/perf-before-sq1.json
היעד (פרומפט 8): load<=2000, open<=300, next<=100, accept<=150. חריגה = לא מפרסמים.
"""
import argparse, json, os, re, statistics, sys, time
from playwright.sync_api import sync_playwright

TARGET = {'load': 2000, 'open': 300, 'next': 100, 'accept': 150}

INIT = r'''
(() => {
  window.__lt = [];
  try { new PerformanceObserver(l => { for (const e of l.getEntries()) window.__lt.push([e.startTime, e.duration]); }).observe({type: 'longtask', buffered: true}); } catch (e) {}
  /* שקט: מחכה עד שעברו ms מאז סוף המשימה הארוכה האחרונה, ומחזיר את סוף המשימה הארוכה האחרונה שאחרי from */
  window.__quiet = (from, ms, cap) => new Promise(res => {
    const t0 = performance.now();
    (function poll() {
      const lt = window.__lt.filter(x => x[0] + x[1] > from);
      const last = lt.length ? Math.max(...lt.map(x => x[0] + x[1])) : from;
      const now = performance.now();
      if (now - last >= ms || now - t0 > cap) return res({last: last, busy: lt.reduce((a, x) => a + x[1], 0), n: lt.length, capped: now - t0 > cap});
      setTimeout(poll, 100);
    })();
  });
  /* מחכה שכרטיס הסקירה יציג ממצא אחר מ-old (הכרטיס הצף או כרטיס המעבר) */
  window.__cardId = () => { const c = document.querySelector('#bkcard') || document.querySelector('#skpass [data-id]'); return c ? (c.dataset.id || '') : ''; };
  window.__waitCard = (old, cap) => new Promise(res => {
    const t0 = performance.now();
    (function f() { const id = window.__cardId(); if (id && id !== old) return res({t: performance.now(), id: id});
      if (performance.now() - t0 > cap) return res({t: null, id: id}); requestAnimationFrame(f); })();
  });
})();
'''


def guard_and_route(ctx, site, slug, blocked):
    def guard(route):
        r = route.request
        if r.method == 'PUT' and r.url.split('?')[0].endswith('/edits'):
            # סנכרון העריכות: נענה מקריאה (GET) של אותו מסמך בשרת, בלי לכתוב. כך הדף מקבל את כל עריכות המנהל כמו אצל המחבר
            blocked.append('PUT /edits (נענה מ-GET, בלי כתיבה)')
            resp = route.fetch(method='GET', url=r.url.split('?')[0] + '?slug=' + slug, post_data='')
            return route.fulfill(response=resp)
        if r.method not in ('GET', 'OPTIONS', 'HEAD'):
            blocked.append(r.method + ' ' + r.url[:100])
            return route.abort()
        route.continue_()
    ctx.route(re.compile(r'workers\.dev|api\.github\.com|127\.0\.0\.1|localhost'), guard)
    if not site:
        return

    def local(route):
        name = route.request.url.split('?')[0].rsplit('/', 1)[-1]
        f = os.path.join(site, name)
        if os.path.exists(f):
            ct = 'text/html; charset=utf-8' if name.endswith('.html') else 'application/javascript; charset=utf-8'
            route.fulfill(path=f, content_type=ct, headers={'cache-control': 'no-store'})
        else:
            route.continue_()
    ctx.route(re.compile(r'leokmei\.com/(mas\.js|lamed\.js|mobile\.js|%s\.x\.js)(\?|$)' % slug), local)   # הקוד בלבד: הנתונים והדף נשארים של האתר החי


def cpu_top(prof, n=25):
    """סיכום פרופיל CPU: זמן עצמי לכל פונקציה (שם:שורה), מן הגדול לקטן"""
    nodes = {x['id']: x for x in prof['nodes']}
    self_t = {}
    samples, deltas = prof.get('samples', []), prof.get('timeDeltas', [])
    for sid, dt in zip(samples, deltas):
        cf = nodes[sid]['callFrame']
        k = (cf.get('functionName') or '(anon)') + ':' + str(cf.get('lineNumber', 0) + 1) + ' ' + cf.get('url', '').rsplit('/', 1)[-1][:24]
        self_t[k] = self_t.get(k, 0) + dt / 1000.0
    top = [[k, round(v)] for k, v in sorted(self_t.items(), key=lambda x: -x[1])[:n]]
    # זמן כולל (הפונקציה וכל מה שהיא קוראת), כל פונקציה פעם אחת לכל מחסנית
    parent = {}
    for x in prof['nodes']:
        for c in x.get('children', []):
            parent[c] = x['id']
    incl = {}
    for sid, dt in zip(samples, deltas):
        seen, cur = set(), sid
        while cur in nodes:
            cf = nodes[cur]['callFrame']
            if cf.get('url'):
                k = (cf.get('functionName') or '(anon)') + ':' + str(cf.get('lineNumber', 0) + 1) + ' ' + cf.get('url', '').rsplit('/', 1)[-1][:12]
                if k not in seen:
                    seen.add(k); incl[k] = incl.get(k, 0) + dt / 1000.0
            cur = parent.get(cur)
    return {'self': top, 'incl': [[k, round(v)] for k, v in sorted(incl.items(), key=lambda x: -x[1])[:n]]}


class Cpu:
    def __init__(self, ctx, pg, on):
        self.on = on
        if on:
            self.c = ctx.new_cdp_session(pg); self.c.send('Profiler.enable'); self.c.send('Profiler.setSamplingInterval', {'interval': 200})
    def start(self):
        if self.on: self.c.send('Profiler.start')
    def stop(self):
        return cpu_top(self.c.send('Profiler.stop')['profile']) if self.on else None


def resp(lt, dcl):
    """הדף מגיב: סוף המשימה האחרונה שנמשכה 100 מ"ש ומעלה, ולא לפני DOMContentLoaded"""
    return max([x[0] + x[1] for x in lt if x[1] >= 100] + [dcl])


def med(a):
    a = [x for x in a if x is not None]
    return round(statistics.median(a)) if a else None


def run(a):
    out = {'slug': a.slug, 'sq': a.sq, 'vert': a.vert, 'site': a.site or 'live', 'when': time.strftime('%d.%m.%Y %H:%M')}
    blocked, errs = [], []
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(a.profile, headless=not a.headed, service_workers='block',
                                                   channel='chrome', viewport={'width': a.width, 'height': 950}, locale='he-IL')
        guard_and_route(ctx, a.site, a.slug, blocked)
        ctx.add_init_script(INIT)
        ctx.add_init_script("try{localStorage.setItem('lg-sq2','%s')}catch(e){}" % ('1' if a.sq == '1' else '0'))
        ctx.add_init_script("try{localStorage.setItem('lg-vert','%s')}catch(e){}" % ('1' if a.vert else ''))
        pg = ctx.pages[0] if ctx.pages else ctx.new_page()
        pg.on('pageerror', lambda e: errs.append(str(e)[:300]))
        pg.on('console', lambda c: errs.append(c.text[:300]) if c.type == 'error' else None)
        pg.on('response', lambda r: errs.append('%d %s' % (r.status, r.url[:120])) if r.status >= 400 else None)
        pg.on('requestfailed', lambda r: errs.append('נכשל ' + r.url[:120]) if 'workers.dev' not in r.url else None)
        url = a.base.rstrip('/') + '/' + a.slug + '.html' + (('#daf=' + a.daf) if a.daf else '')
        cpu = Cpu(ctx, pg, a.cpu)
        cpu.start()
        pg.goto(url, wait_until='domcontentloaded', timeout=120000)
        q = pg.evaluate('() => window.__quiet(0, 2500, 90000)')
        nav = pg.evaluate("() => { const n = performance.getEntriesByType('navigation')[0] || {}; return {dcl: Math.round(n.domContentLoadedEventEnd || 0)}; }")
        out['load'] = round(q['last']); out['dcl'] = nav['dcl']; out['load_capped'] = q['capped']
        lt1 = pg.evaluate('() => window.__lt.map(x => [Math.round(x[0]), Math.round(x[1])])')
        if a.warm:
            # כניסה שנייה באותו פרופיל: מה שנשמר במכשיר (איחוי, עריכות שכבר בבסיס) כבר בתוקף
            pg.wait_for_timeout(3000)
            out['cpu_load_first'] = cpu.stop(); cpu.start()
            pg.goto('about:blank'); pg.goto(url, wait_until='domcontentloaded', timeout=120000)
            q = pg.evaluate('() => window.__quiet(0, 2500, 90000)')
            nav = pg.evaluate("() => { const n = performance.getEntriesByType('navigation')[0] || {}; return {dcl: Math.round(n.domContentLoadedEventEnd || 0)}; }")
            out['load_first'] = resp(lt1, out['dcl']); out['load_quiet_first'] = out['load']; out['dcl_first'] = out['dcl']
            out['load'] = round(q['last']); out['dcl'] = nav['dcl']
        out['cpu_load'] = cpu.stop()
        out['lt_load'] = pg.evaluate('() => window.__lt.map(x => [Math.round(x[0]), Math.round(x[1])])')
        # מגיב: סוף המשימה הארוכה האחרונה שאורכה 100 מ"ש ומעלה (משימה קצרה מזה אינה מורגשת). load_quiet: עד שקט מלא
        out['load_quiet'] = out['load']; out['load'] = resp(out['lt_load'], out['dcl'])
        out['ed'] = pg.evaluate("() => { try { return {ed: ED.length, lost: ED.filter(e => e.lost).length, ap: ED.filter(e => e._ap).length, struct: ED.filter(e => e.op === 'struct').length, done: (typeof edDone === 'function') ? edDone().s.size : null}; } catch (e) { return String(e); } }")
        out['admin'] = pg.evaluate("() => localStorage.getItem('lg-admin')==='1'")
        # ממתינים לממצאי הסקירה (נטענים מן השרת)
        for _ in range(120):
            t = pg.evaluate("() => (document.getElementById('bkbtn2')||{}).textContent||''")
            if t and '…' not in t and 'שגיאה' not in t and pg.evaluate("() => typeof BK !== 'undefined' && BK.loaded"):
                break
            pg.wait_for_timeout(500)
        out['bkbtn'] = t
        t0 = pg.evaluate('() => performance.now()')
        pg.wait_for_timeout(10000)
        idle = pg.evaluate('(t0) => window.__lt.filter(x => x[0] >= t0).reduce((s, x) => s + x[1], 0)', t0)
        out['idle_busy_10s'] = round(idle)
        # פתיחת הסקירה
        cpu.start()
        r = pg.evaluate('''async () => { const t0 = performance.now(); bkToggle(); const s = performance.now() - t0;
            const q = await window.__quiet(t0, 1500, 60000); return {sync: s, quiet: Math.max(q.last - t0, s), busy: q.busy}; }''')
        out['open'] = round(r['quiet']); out['open_detail'] = r
        out['cpu_open'] = cpu.stop()
        cpu.start()
        out['stats'] = pg.evaluate("() => window.__skStats ? window.__skStats() : null")
        # מעבר להערה הבאה
        nx = []
        for i in range(a.n):
            r = pg.evaluate('''async () => { const old = window.__cardId(); const t0 = performance.now();
                document.dispatchEvent(new KeyboardEvent('keydown', {code: 'ArrowDown', key: 'ArrowDown', altKey: true, bubbles: true, cancelable: true}));
                const c = await window.__waitCard(old, 20000); const q = await window.__quiet(t0, 1200, 30000);
                return {card: c.t === null ? null : c.t - t0, quiet: Math.max(q.last - t0, c.t === null ? 0 : c.t - t0), id: c.id}; }''')
            nx.append(r)
        out['next_card'] = med([x['card'] for x in nx]); out['next_quiet'] = med([x['quiet'] for x in nx]); out['next'] = out['next_quiet']
        out['next_runs'] = nx
        out['cpu_next'] = cpu.stop()
        # קבל ומעבר (רק במפורש: ההכרעות נשמרות בעותק הפרופיל בלבד, והרשת חסומה)
        if a.decide:
            ac = []
            cpu.start()
            for i in range(a.decide):
                r = pg.evaluate('''async () => { const old = window.__cardId(); const t0 = performance.now();
                    document.dispatchEvent(new KeyboardEvent('keydown', {code: 'Enter', key: 'Enter', bubbles: true, cancelable: true}));
                    const c = await window.__waitCard(old, 20000); const q = await window.__quiet(t0, 1200, 30000);
                    return {card: c.t === null ? null : c.t - t0, quiet: Math.max(q.last - t0, c.t === null ? 0 : c.t - t0), id: old}; }''')
                ac.append(r)
            out['accept_card'] = med([x['card'] for x in ac]); out['accept_quiet'] = med([x['quiet'] for x in ac]); out['accept'] = out['accept_quiet']
            out['accept_runs'] = ac
            out['cpu_accept'] = cpu.stop()
        if a.shot:
            pg.screenshot(path=a.shot)
        out['errors'] = errs[:20]; out['blocked'] = blocked[:40]; out['blocked_n'] = len(blocked)
        ctx.close()
    out['pass'] = {k: (out.get(k) is not None and out[k] <= v) for k, v in TARGET.items() if out.get(k) is not None}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', default='https://leokmei.com')
    ap.add_argument('--slug', default='bekhorot')
    ap.add_argument('--daf', default='')
    ap.add_argument('--profile', required=True)
    ap.add_argument('--site', default='')
    ap.add_argument('--sq', default='0')
    ap.add_argument('--n', type=int, default=5)
    ap.add_argument('--decide', type=int, default=0)
    ap.add_argument('--width', type=int, default=1500)
    ap.add_argument('--headed', action='store_true')
    ap.add_argument('--shot', default='')
    ap.add_argument('--cpu', action='store_true')
    ap.add_argument('--warm', action='store_true')
    ap.add_argument('--vert', action='store_true', help='תצוגת רצף: כל המסכת בדף אחד, כמו אצל המחבר')
    ap.add_argument('--out', default='')
    a = ap.parse_args()
    o = run(a)
    s = json.dumps(o, ensure_ascii=False, indent=1)
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        open(a.out, 'w', encoding='utf-8').write(s)
    keys = ['load', 'load_quiet', 'dcl', 'load_first', 'dcl_first', 'ed', 'idle_busy_10s', 'open', 'next_card', 'next_quiet', 'accept_card', 'accept_quiet', 'admin', 'bkbtn', 'blocked_n', 'errors', 'pass']
    print(json.dumps({k: o.get(k) for k in keys}, ensure_ascii=False))


if __name__ == '__main__':
    main()
