# -*- coding: utf-8 -*-
"""מדידת מהירות האתר (פרומפט 79, 23.11.2026).

מודד בדפדפן אמיתי, על האתר שנבנה (שרת מקומי) או על האתר החי:
  פתיחת דף, זמן עד שאפשר לגלול, לחיצה על כפתור התוס', מעבר דף,
  כניסה ויציאה ממצב עריכה (כשאין מפתח מנהל: לא נמדד) ומצב דפוס,
  וזמן המעבד שנצרך ברקע בעשר שניות של מנוחה (כאן נראה ה-setInterval).
שני פרופילים: מחשב, וטלפון חלש (האטת מעבד פי 4; הרשת נמדדת בנפרד, לפי גודל ההורדה).

  python tools/qa/perf_measure.py --base http://localhost:8731 --path /shabbat.html --path /berakhot.html --out perf.json
"""
import argparse, json, time, sys

from playwright.sync_api import sync_playwright

JS_LONG = """() => { window.__lt = 0; window.__ltn = 0; try { new PerformanceObserver(l => { for (const e of l.getEntries()) { window.__lt += e.duration; window.__ltn++ } }).observe({type:'longtask', buffered:true}) } catch(e) {} }"""


def idle_ms(page, timeout=30000):
    """ממתין עד שהדף פנוי (שתי מסגרות ציור רצופות בלי עיכוב), ומחזיר את הזמן שעבר."""
    return page.evaluate("""(to) => new Promise(res => { const t0 = performance.now();
      function tick(){ const a = performance.now(); requestAnimationFrame(() => setTimeout(() => {
        const d = performance.now() - a; if (d < 60 || performance.now() - t0 > to) res(performance.now() - t0); else tick() }, 0)) }
      tick() })""", timeout)


def click_time(page, sel):
    """זמן מן הלחיצה ועד שהדף פנוי שוב."""
    ok = page.evaluate("(s) => !!document.querySelector(s)", sel)
    if not ok:
        return None
    t0 = time.perf_counter()
    page.evaluate("(s) => { const b = document.querySelector(s); b.click() }", sel)
    idle_ms(page)
    return round((time.perf_counter() - t0) * 1000)


def measure(pw, base, path, phone):
    import os
    br = pw.chromium.launch(executable_path=os.environ.get('PW_CHROME') or None)
    ctx = br.new_context(viewport={'width': 412, 'height': 860} if phone else {'width': 1440, 'height': 900},
                         device_scale_factor=1, is_mobile=phone, has_touch=phone,
                         user_agent=('Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Mobile Safari/537.36' if phone else None))
    page = ctx.new_page()
    errs = []
    page.on('pageerror', lambda e: errs.append(str(e)))
    cdp = ctx.new_cdp_session(page)
    if phone:
        cdp.send('Emulation.setCPUThrottlingRate', {'rate': 4})
    page.add_init_script(JS_LONG.join(['(', ')()']))
    r = {'path': path, 'profile': 'טלפון חלש' if phone else 'מחשב'}
    t0 = time.perf_counter()
    page.goto(base + path, wait_until='domcontentloaded', timeout=180000)
    r['dom_ms'] = round((time.perf_counter() - t0) * 1000)
    page.wait_for_selector('#flow .row', timeout=180000)
    r['text_ms'] = round((time.perf_counter() - t0) * 1000)
    idle_ms(page, 60000)
    r['scroll_ready_ms'] = round((time.perf_counter() - t0) * 1000)
    r['rows'] = page.evaluate("document.querySelectorAll('#flow .row').length")
    r['tsa'] = page.evaluate("document.querySelectorAll('#flow .tsa').length")
    def cpu():
        m = {x['name']: x['value'] for x in cdp.send('Performance.getMetrics')['metrics']}
        return (m['ScriptDuration'] + m['LayoutDuration'] + m['RecalcStyleDuration']) * 1000
    cdp.send('Performance.enable')
    page.wait_for_timeout(4000)
    c0 = cpu(); page.wait_for_timeout(10000)
    r['idle_cpu_ms_10s'] = round(cpu() - c0)
    # גלילה: זמן הציור של עשר גלילות
    t1 = time.perf_counter()
    for i in range(10):
        page.evaluate("""() => { const f = document.getElementById('flow');
          if (f.classList.contains('vert')) f.scrollBy(0, f.clientHeight * .8); else f.scrollBy(-f.clientWidth * .8, 0);
          window.scrollBy(0, innerHeight * .8) }""")
        idle_ms(page)
    r['scroll10_ms'] = round((time.perf_counter() - t1) * 1000)
    # לחיצה על כפתור התוס' (פעמיים: פתיחה וסגירה)
    def tos_toggle():
        t0 = time.perf_counter()
        page.evaluate("() => { const b = document.getElementById('tosbtn'); if (b) b.click(); else if (window.tosBtn) tosBtn() }")
        idle_ms(page)
        return round((time.perf_counter() - t0) * 1000)
    r['tos_on_ms'] = tos_toggle()
    r['tsa_on'] = page.evaluate("document.querySelectorAll('#flow .tsa').length")
    page.wait_for_timeout(2000)
    c0 = cpu(); page.wait_for_timeout(10000)
    r['idle_cpu_tos_on_ms_10s'] = round(cpu() - c0)
    t1 = time.perf_counter()
    for i in range(10):
        page.evaluate("""() => { const f = document.getElementById('flow');
          if (f.classList.contains('vert')) f.scrollBy(0, f.clientHeight * .8); else f.scrollBy(-f.clientWidth * .8, 0);
          window.scrollBy(0, innerHeight * .8) }""")
        idle_ms(page)
    r['scroll10_tos_on_ms'] = round((time.perf_counter() - t1) * 1000)
    r['tos_off_ms'] = tos_toggle()
    r['tos_on2_ms'] = tos_toggle()
    # מעבר דף (הדף הבא בבורר הדפים)
    t2 = time.perf_counter()
    page.evaluate("() => { if (typeof goDaf === 'function') goDaf(1) }")
    idle_ms(page)
    r['daf_next_ms'] = round((time.perf_counter() - t2) * 1000)
    # מעבר פרק
    t3 = time.perf_counter()
    page.evaluate("() => { const s = document.getElementById('peresel'); if (s && s.options.length > 1) { s.value = 1; s.onchange() } }")
    idle_ms(page)
    r['perek_next_ms'] = round((time.perf_counter() - t3) * 1000)
    # מצב דפוס: כניסה ויציאה
    for k, js in (('book_on_ms', "() => { if (typeof book === 'function') book() }"),
                  ('book_off_ms', "() => { if (typeof book === 'function') book() }")):
        t4 = time.perf_counter()
        page.evaluate(js)
        idle_ms(page, 60000)
        r[k] = round((time.perf_counter() - t4) * 1000)
    r['errors'] = errs[:5]
    br.close()
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', default='http://localhost:8731')
    ap.add_argument('--path', action='append', default=[])
    ap.add_argument('--out', default='')
    ap.add_argument('--phone-only', action='store_true')
    a = ap.parse_args()
    out = []
    with sync_playwright() as pw:
        for p in a.path or ['/shabbat.html']:
            for phone in ((True,) if a.phone_only else (False, True)):
                r = measure(pw, a.base, p, phone)
                print(json.dumps(r, ensure_ascii=False))
                sys.stdout.flush()
                out.append(r)
    if a.out:
        json.dump(out, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
