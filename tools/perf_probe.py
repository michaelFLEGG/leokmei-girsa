# -*- coding: utf-8 -*-
"""perf_probe.py - מדידת מהירות טעינה בדפדפן אמיתי (Chromium + CDP): FCP, LCP, TBT (משוער מהמשימות הארוכות), CLS, משקל כולל וקבצים גדולים.
מצב טלפון: 390x844, רשת 4G איטית (1.6Mbps, 150ms), מעבד פי 4 איטי (כמו Lighthouse). מצב מחשב: 1366x768 בלי חנק.
הרצה: uv run --with playwright python tools/perf_probe.py --base https://leokmei.com --out docs/qa/2026-10-09/perf-before.json [--runs 3] [--warm]
--warm: מודד גם כניסה שנייה (אותו הקשר, מטמון חם).
(Lighthouse עצמו לא הורד כדי לא להתקין כלי חיצוני; המדדים זהים בהגדרתם: web-vitals מ-PerformanceObserver.)"""
import json, sys, argparse, statistics, io
from playwright.sync_api import sync_playwright

INIT = r'''
(() => {
  window.__pf = {fcp: null, lcp: null, cls: 0, lt: [], nav: null};
  try { new PerformanceObserver(l => { for (const e of l.getEntries()) if (e.name === 'first-contentful-paint') window.__pf.fcp = e.startTime; }).observe({type: 'paint', buffered: true}); } catch (e) {}
  try { new PerformanceObserver(l => { for (const e of l.getEntries()) window.__pf.lcp = e.startTime; }).observe({type: 'largest-contentful-paint', buffered: true}); } catch (e) {}
  try { new PerformanceObserver(l => { for (const e of l.getEntries()) if (!e.hadRecentInput) window.__pf.cls += e.value; }).observe({type: 'layout-shift', buffered: true}); } catch (e) {}
  try { new PerformanceObserver(l => { for (const e of l.getEntries()) window.__pf.lt.push([e.startTime, e.duration]); }).observe({type: 'longtask', buffered: true}); } catch (e) {}
})();
'''
COLLECT = r'''() => {
  const p = window.__pf, r = performance.getEntriesByType('resource');
  const tot = r.reduce((a, e) => a + (e.transferSize || 0), 0), dec = r.reduce((a, e) => a + (e.decodedBodySize || 0), 0);
  const nav = performance.getEntriesByType('navigation')[0] || {};
  const tbt = p.lt.filter(x => p.fcp == null || x[0] >= p.fcp).reduce((a, x) => a + Math.max(0, x[1] - 50), 0);
  const big = r.map(e => [e.name.replace(location.origin, '').slice(0, 70), e.transferSize || 0, e.decodedBodySize || 0]).sort((a, b) => b[2] - a[2]).slice(0, 8);
  return {fcp: p.fcp, lcp: p.lcp, cls: Math.round(p.cls * 1000) / 1000, tbt: Math.round(tbt), requests: r.length + 1,
          transfer: tot + (nav.transferSize || 0), decoded: dec + (nav.decodedBodySize || 0), dom: Math.round(nav.domContentLoadedEventEnd || 0), load: Math.round(nav.loadEventEnd || 0), big: big};
}'''
PAGES = [('בית', '/'), ('מפת הש"ס', '/shas.html'), ('דף גמרא', '/berakhot.html#daf=%D7%95%3A')]


def med(xs):
    xs = [x for x in xs if x is not None]
    return round(statistics.median(xs)) if xs else None


def measure(pw, base, path, mobile, warm, runs):
    out = []
    br = pw.chromium.launch()
    for _ in range(runs):
        if mobile:
            ctx = br.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=3, is_mobile=True, has_touch=True, locale='he-IL')
        else:
            ctx = br.new_context(viewport={'width': 1366, 'height': 768}, locale='he-IL')
        ctx.add_init_script(INIT)
        pg = ctx.new_page()
        cdp = ctx.new_cdp_session(pg)
        if mobile:
            cdp.send('Network.enable')
            cdp.send('Network.emulateNetworkConditions', {'offline': False, 'latency': 150, 'downloadThroughput': 1.6 * 1024 * 1024 / 8, 'uploadThroughput': 750 * 1024 / 8})
            cdp.send('Emulation.setCPUThrottlingRate', {'rate': 4})
        try:
            pg.goto(base.rstrip('/') + path, wait_until='load', timeout=120000)
            pg.wait_for_timeout(2500)
            m = pg.evaluate(COLLECT)
            if warm:
                pg.goto('about:blank'); pg.wait_for_timeout(300)
                pg.goto(base.rstrip('/') + path, wait_until='load', timeout=120000); pg.wait_for_timeout(2000)
                w = pg.evaluate(COLLECT); m['warm_fcp'] = w['fcp']; m['warm_lcp'] = w['lcp']; m['warm_transfer'] = w['transfer']
            out.append(m)
        except Exception as e:
            out.append({'error': str(e)[:150]})
        ctx.close()
    br.close()
    good = [o for o in out if 'error' not in o]
    if not good: return {'error': out[0].get('error')}
    r = {k: med([g.get(k) for g in good]) for k in ('fcp', 'lcp', 'tbt', 'requests', 'transfer', 'decoded', 'dom', 'load', 'warm_fcp', 'warm_lcp', 'warm_transfer')}
    r['cls'] = round(statistics.median([g['cls'] for g in good]), 3); r['big'] = good[0]['big']
    return r


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--base', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--runs', type=int, default=3); ap.add_argument('--warm', action='store_true')
    a = ap.parse_args(); res = {}
    with sync_playwright() as pw:
        for mode in ('mobile', 'desktop'):
            for name, path in PAGES:
                res['%s | %s' % (mode, name)] = measure(pw, a.base, path, mode == 'mobile', a.warm, a.runs)
                print(mode, name, json.dumps({k: v for k, v in res['%s | %s' % (mode, name)].items() if k != 'big'}, ensure_ascii=False), flush=True)
    io.open(a.out, 'w', encoding='utf-8').write(json.dumps(res, ensure_ascii=False, indent=1))
