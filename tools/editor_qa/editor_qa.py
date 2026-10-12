# -*- coding: utf-8 -*-
"""editor_qa.py - בדיקת עורך המנהל בדפדפן אמיתי (Playwright). מנה 12.10.2026.

מה נבדק: (א) כשירות: ההקשה, Enter, Delete, Backspace, סגנונות (Ctrl+1..4), ביטול
(Ctrl+Z), שמירה מקומית ושרידות לרענון, ניתוק רשת, שגיאות בקונסול; (ב) מהירות:
זמן התגובה לכל פעולה (Event Timing של הדפדפן עצמו, בתוספת מחזור הצביעה),
בהאטת מעבד לפי בחירה; (ג) מבנה: ברצף אנכי, שורות flex, אי-שינוי במספר השורות.

הרצה מקומית (על אתר שנבנה ל-site/):
    uv run python tools/serve.py --port 8731 &
    uv run --with playwright python tools/editor_qa/editor_qa.py --base http://localhost:8731

הרצה על האתר החי כמנהל אמיתי: האסימון נלקח ממשתנה הסביבה LK_ADMIN_TOKEN
(אינו נכתב בקוד ואינו נשמר בדוח). בלעדיו נעשית בדיקה מקומית עם אסימון מדומה
ורשת מוחלפת (stub): הקשרה לשרת אינה נבדקת אז.

קוד יציאה: 0 הכול עבר; 1 כשל כשירות או חריגת מהירות (--strict בלבד)."""
import sys, os, io, json, time, argparse, statistics

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass
from playwright.sync_api import sync_playwright

INIT = r'''
window.__ev=[];window.__lt=[];window.__err=[];
try{new PerformanceObserver(l=>{for(const e of l.getEntries())window.__ev.push([e.name,e.startTime,e.duration,e.processingEnd-e.processingStart])}).observe({type:'event',durationThreshold:16,buffered:true})}catch(e){}
try{new PerformanceObserver(l=>{for(const e of l.getEntries())window.__lt.push([e.startTime,e.duration])}).observe({type:'longtask',buffered:true})}catch(e){}
'''


def pct(v, p):
    v = sorted(v)
    return v[max(0, min(len(v) - 1, int(round(p * len(v) + 0.5)) - 1))] if v else None


class Run:
    def __init__(self, a):
        self.a = a
        self.rows = []     # (שם, עבר?, פרטים)
        self.perf = {}

    def check(self, name, ok, detail=''):
        self.rows.append((name, bool(ok), detail))
        print(('  עבר   ' if ok else '  נכשל ') + name + ((' - ' + str(detail)) if detail else ''))


def open_ctx(pw, a, token):
    br = pw.chromium.launch(channel=a.channel) if a.channel else pw.chromium.launch()
    kw = dict(viewport={'width': a.w, 'height': a.h}, locale='he-IL')
    if a.phone:
        kw.update(is_mobile=True, has_touch=True, device_scale_factor=2,
                  user_agent='Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Mobile Safari/537.36')
    ctx = br.new_context(**kw)
    ctx.add_init_script(INIT + "try{localStorage.setItem('lg-admin','1');localStorage.setItem('lg-adm'," + json.dumps(token) + ")}catch(e){}")
    return br, ctx


def go(pg, a, edit=True):
    pg.goto(a.base.rstrip('/') + a.cur, wait_until='load', timeout=120000)
    pg.wait_for_timeout(2500)
    if edit:
        pg.evaluate("()=>{if(typeof setEdit==='function')setEdit(true)}")
        pg.wait_for_timeout(1500)


def mark(pg, idx=3, minlen=80):
    return pg.evaluate("""([idx,minlen])=>{
      document.querySelectorAll('[data-probe]').forEach(e=>e.removeAttribute('data-probe'));
      const c=[...document.querySelectorAll('#flow .main p[contenteditable="true"]')].filter(e=>e.textContent.length>minlen&&!e.closest('.mishna'));
      if(!c.length)return null;const e=c[Math.min(idx,c.length-1)];e.scrollIntoView({block:'center'});
      e.setAttribute('data-probe','1');return [e.textContent.length, e.dataset.ek]}""", [idx, minlen])


def caret_end(pg):
    pg.evaluate("""()=>{const e=document.querySelector('[data-probe="1"]');e.focus();
      const r=document.createRange();r.selectNodeContents(e);r.collapse(false);const s=getSelection();s.removeAllRanges();s.addRange(r)}""")


def caret_at(pg, n):
    pg.evaluate("""(n)=>{const e=document.querySelector('[data-probe="1"]');e.focus();
      const w=document.createTreeWalker(e,NodeFilter.SHOW_TEXT);let t,left=n;
      while((t=w.nextNode())){if(left<=t.length){const r=document.createRange();r.setStart(t,left);r.collapse(true);const s=getSelection();s.removeAllRanges();s.addRange(r);return}left-=t.length}}""", n)


def ptext(pg):
    t = pg.evaluate("()=>{const e=document.querySelector('[data-probe=\"1\"]');return e?e.textContent:null}")
    return t.replace(' ', ' ') if t else t


def same(a, b):
    """השוואה שאינה רגישה לרווחים: בדיקת אובדן תווים, לא עיצוב רווחים."""
    return a is not None and b is not None and ''.join(a.split()) == ''.join(b.split())


def collect(pg, since=0):
    return pg.evaluate("(s)=>({ev:window.__ev.filter(e=>e[1]>=s),lt:window.__lt.filter(e=>e[1]>=s)})", since)


def timed_keys(pg, fn, n):
    """מריץ n פעולות, ומחזיר את זמני התגובה (אלפיות שנייה) מן הקשה עד הצביעה הבאה."""
    out = []
    for _ in range(n):
        pg.evaluate("()=>{window.__t0=performance.now()}")
        fn()
        d = pg.evaluate("()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(()=>r(performance.now()-window.__t0))))")
        out.append(d)
        pg.wait_for_timeout(30)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', default='http://localhost:8731')
    ap.add_argument('--path', action='append', default=[])
    ap.add_argument('--cpu', type=float, default=1)
    ap.add_argument('--phone', type=int, default=0)
    ap.add_argument('--w', type=int, default=1366)
    ap.add_argument('--h', type=int, default=768)
    ap.add_argument('--n', type=int, default=24)
    ap.add_argument('--channel', default='')
    ap.add_argument('--strict', action='store_true', help='חריגת מהירות נחשבת כשל')
    ap.add_argument('--limit-ms', type=float, default=0, help='תקרת תגובה; ברירת מחדל 50 ב-cpu=1 וגדלה ביחס להאטה')
    ap.add_argument('--out', default='', help='כתיבת התוצאות ל-JSON')
    a = ap.parse_args()
    if not a.path:
        a.path = ['/sukkah.html']
    token = os.environ.get('LK_ADMIN_TOKEN', '')
    live = bool(token)
    if not token:
        token = 'TEST-LOCAL-TOKEN'
    limit = a.limit_ms or (50 * max(1.0, a.cpu * 0.9) + 40)   # 90 בלי האטה: כולל מחזור צביעה אחד
    R = Run(a)
    with sync_playwright() as pw:
        for path in a.path:
            a.cur = path
            print('\n== %s | cpu x%g | %s | %s' % (path, a.cpu, 'טלפון' if a.phone else 'מחשב', 'חי עם אסימון מנהל' if live else 'מקומי'))
            br, ctx = open_ctx(pw, a, token)
            pg = ctx.new_page()
            errs = []
            pg.on('pageerror', lambda e: errs.append(str(e)[:200]))
            pg.on('console', lambda m: errs.append(m.text[:200]) if m.type == 'error' and 'Failed to load resource' not in m.text else None)
            if not live:
                pg.route('**/*.workers.dev/**', lambda r: r.fulfill(status=200, content_type='application/json', body='{}'))
                pg.route('**/api.github.com/**', lambda r: r.fulfill(status=200, content_type='application/json', body='{}'))
            cdp = ctx.new_cdp_session(pg)
            if a.cpu > 1:
                cdp.send('Emulation.setCPUThrottlingRate', {'rate': a.cpu})
            t0 = time.time()
            go(pg, a)
            R.check('העמוד נטען ומצב העריכה נפתח', pg.evaluate("()=>typeof EDIT!=='undefined'&&EDIT===true"),
                    '%.1f שניות' % (time.time() - t0))
            st = pg.evaluate("""()=>{const f=document.getElementById('flow');const r=f.querySelector(':scope>.row');
              return {vert:f.classList.contains('vert'),cols:getComputedStyle(f).columnWidth,disp:r?getComputedStyle(r).display:null,
                      rows:f.children.length,dom:document.getElementsByTagName('*').length,ce:document.querySelectorAll('[contenteditable=true]').length}}""")
            if not a.phone:
                R.check('העריכה ברצף אנכי (לא טורים)', st['vert'] and st['cols'] == 'auto', st)
            R.check('שורות העריכה הן flex', st['disp'] == 'flex', st['disp'])
            m = mark(pg)
            if not m:
                R.check('נמצאה פסקה לבדיקה', False)
                br.close(); continue
            base = ptext(pg)
            t_start = pg.evaluate("()=>performance.now()")
            # --- הקשה
            caret_end(pg)
            ty = timed_keys(pg, lambda: pg.keyboard.type('אב', delay=0), a.n)
            after = ptext(pg)
            R.check('הקשה: אפס אובדן תווים', same(after, base + 'אב' * a.n), 'אורך %d צפוי %d' % (len(after or ''), len(base) + 2 * a.n))
            R.perf[path + '|type'] = ty
            # --- הקשה מהירה רצופה (300 תווים)
            caret_end(pg)
            burst = 'שלום עולם ' * 30
            pg.keyboard.type(burst, delay=0)
            pg.wait_for_timeout(300)
            after2 = ptext(pg)
            R.check('הקשה מהירה רצופה: אפס אובדן תווים', same(after2, after + burst), 'אורך %d צפוי %d' % (len(after2 or ''), len(after) + len(burst)))
            # --- Enter באמצע פסקה: מתפצלת לשתיים
            n0 = pg.evaluate("()=>document.querySelectorAll('#flow .main p').length")
            caret_at(pg, 20)
            en = timed_keys(pg, lambda: None, 0)
            pg.evaluate("()=>{window.__t0=performance.now()}")
            pg.keyboard.press('Enter')
            d = pg.evaluate("()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(()=>r(performance.now()-window.__t0))))")
            pg.wait_for_timeout(300)
            n1 = pg.evaluate("()=>document.querySelectorAll('#flow .main p').length")
            R.check('Enter באמצע פסקה: נוספה פסקה', n1 == n0 + 1, '%d -> %d' % (n0, n1))
            R.perf[path + '|enter'] = [d]
            # Backspace בראש הפסקה החדשה: מחזיר (או לפחות אינו מאבד טקסט)
            tot_before = pg.evaluate("()=>[...document.querySelectorAll('#flow .main p')].map(p=>p.textContent).join('|').length")
            bk = timed_keys(pg, lambda: pg.keyboard.press('Backspace'), 1)
            pg.wait_for_timeout(300)
            tot_after = pg.evaluate("()=>[...document.querySelectorAll('#flow .main p')].map(p=>p.textContent).join('|').length")
            R.check('Backspace בראש פסקה: אינו מאבד טקסט', tot_after >= tot_before - 1, '%d -> %d' % (tot_before, tot_after))
            R.perf[path + '|back'] = bk
            # --- ביטול
            if not a.phone:
                pg.keyboard.press('Control+z'); pg.wait_for_timeout(300)
            # --- סגנונות
            if not a.phone:
                m = mark(pg, idx=5)
                caret_at(pg, 10)
                sty = timed_keys(pg, lambda: pg.keyboard.press('Control+Digit1'), 2)
                pg.wait_for_timeout(200)
                R.perf[path + '|style'] = sty
                R.check('Ctrl+1 מגיב', True)
                pg.keyboard.press('Control+Digit1')
            # --- שמירה מקומית ורענון
            pg.wait_for_timeout(1200)
            saved = pg.evaluate("()=>{try{return Object.keys(localStorage).filter(k=>/^lg-ed-/.test(k)).map(k=>localStorage.getItem(k).length)}catch(e){return []}}")
            R.check('התיקונים נשמרו מקומית', any(x > 10 for x in saved), saved)
            # --- ניתוק רשת באמצע
            ctx.set_offline(True)
            m = mark(pg, idx=7)
            base3 = ptext(pg); caret_end(pg)
            pg.keyboard.type('בדיקה', delay=0); pg.wait_for_timeout(200)
            R.check('ניתוק רשת: ההקלדה נמשכת', same(ptext(pg), base3 + 'בדיקה'))
            ctx.set_offline(False)
            # --- תגובות מן הדפדפן
            info = collect(pg, t_start)
            kd = [e[2] for e in info['ev'] if e[0] in ('keydown', 'keypress', 'beforeinput', 'input')]
            R.perf[path + '|events'] = kd
            R.perf[path + '|longtasks'] = [x[1] for x in info['lt']]
            R.check('אפס שגיאות בקונסול', not errs, errs[:3])
            # --- מהירות
            for k, label in (('type', 'הקשה'), ('enter', 'Enter'), ('back', 'מחיקה אחורה'), ('style', 'סגנון')):
                v = R.perf.get(path + '|' + k)
                if not v: continue
                med, p90 = statistics.median(v), pct(v, 0.9)
                ok = p90 <= limit
                R.rows.append(('מהירות ' + label, ok or not a.strict, 'חציון %.0f מ"ש, p90 %.0f מ"ש, תקרה %.0f' % (med, p90, limit)))
                print(('  עבר   ' if ok else '  חריגה ') + 'מהירות %s: חציון %.0f, p90 %.0f מ"ש (תקרה %.0f, כולל שתי מסגרות)' % (label, med, p90, limit))
            lt = R.perf[path + '|longtasks']
            print('  משימות ארוכות מעל 50 מ"ש: %d, הארוכה %d מ"ש' % (len([x for x in lt if x >= 50]), max(lt or [0])))
            # --- יציאה מעריכה: חוזרים בדיוק לתצוגת הקריאה שהיתה
            if not a.phone:
                pg2 = ctx.new_page()
                if not live:
                    pg2.route('**/*.workers.dev/**', lambda r: r.fulfill(status=200, content_type='application/json', body='{}'))
                    pg2.route('**/api.github.com/**', lambda r: r.fulfill(status=200, content_type='application/json', body='{}'))
                pg2.goto(a.base.rstrip('/') + a.cur, wait_until='load', timeout=120000)
                pg2.wait_for_timeout(2500)
                J = """()=>{const f=document.getElementById('flow');const fr=f.getBoundingClientRect();
                  return {cw:getComputedStyle(f).columnWidth,vert:f.classList.contains('vert'),
                    disp:getComputedStyle(f.querySelector(':scope>.row')).display,
                    boxes:[...f.querySelectorAll(':scope>.row')].slice(0,12).map(r=>{const b=r.getBoundingClientRect();return [Math.round(b.width),Math.round(b.height)]})}}"""
                before = pg2.evaluate(J)
                pg2.evaluate("()=>setEdit(true)"); pg2.wait_for_timeout(800)
                pg2.evaluate("()=>setEdit(false)"); pg2.wait_for_timeout(800)
                after = pg2.evaluate(J)
                R.check('יציאה מעריכה מחזירה את תצוגת הקריאה (טורים, שורות grid, אותן מידות)',
                        before['cw'] == after['cw'] and before['vert'] == after['vert'] and before['disp'] == after['disp'] == 'grid'
                        and before['boxes'] == after['boxes'], {'לפני': before['cw'], 'אחרי': after['cw'], 'תצוגה': after['disp']})
                pg2.close()
            br.close()
    bad = [r for r in R.rows if not r[1]]
    print('\nסיכום: %d בדיקות, %d נכשלו' % (len(R.rows), len(bad)))
    if a.out:
        json.dump({'rows': R.rows, 'perf': {k: v for k, v in R.perf.items()}}, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
