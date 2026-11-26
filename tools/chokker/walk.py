# -*- coding: utf-8 -*-
"""החוקר - ההליכה הלילית (החלק המכני, בלי טוקנים).

עובר כמו גולש על האתרים: כל מסכת, כל גודל מסך, תצוגת זרימה וספר, כל כפתור בסרגל, וכל פרופיל הדפסה,
ומריץ בכל מסך את בודק הכללים (probe.js). שומר צילומים, גיליונות-מגע (sheets.py) לעיון בעיניים, ודוח JSON.

  python tools/chokker/walk.py --site leokmei --only bava-batra --out data/chokker/runs/2026-11-26
  python tools/chokker/walk.py --site all            (כל האתרים, כל המסכתות - הסבב הלילי)
  --parts flow,buttons,print   --print-profiles a4lg,b5lg,book   --max-tiles 60

עדינות כלפי האתר: דפדפן אמיתי, בקשה אחת בכל פעם, השהיה בין דפים (חסימת Cloudflare חסמה בעבר את המשרד).
User-Agent מסומן LeokmeiChokker, כדי שמונה ההדפסות ונתוני הגלישה יוכלו לסנן את החוקר.
"""
import os, sys, io, json, time, re, argparse, datetime, random, subprocess, traceback
from urllib.parse import urlparse, urljoin

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PROBE = io.open(os.path.join(HERE, 'probe.js'), encoding='utf-8').read()
SITES = json.load(io.open(os.path.join(HERE, 'sites.json'), encoding='utf-8'))
UA_TAG = ' LeokmeiChokker/1.0'

VIEWPORTS = [  # שם, רוחב, גובה, צפיפות, נייד
    ('phone', 390, 844, 2, True),
    ('tablet-p', 820, 1180, 2, True),
    ('tablet-l', 1180, 820, 2, True),
    ('desktop', 1440, 900, 1, False),
    ('wide', 1920, 1080, 1, False),
]
SKIP_BTN = re.compile(r'מחק|פרסם|שלח|הצע|סכם|קבל|דחה|התנתק|יציאה|הורד|וורד|שתף|ווטסאפ|הדפס|print|delete|publish', re.I)


def dhash(path):
    """טביעת מראה קטנה (64 סיביות): המוח הלילי מסתכל בעיניים קודם על כל מסך שהמראה שלו השתנה מאתמול."""
    try:
        from PIL import Image
        im = Image.open(path).convert('L').resize((9, 8))
        px = list(im.getdata())
        return '%016x' % sum(1 << i for i in range(64) if px[(i // 8) * 9 + i % 8] > px[(i // 8) * 9 + i % 8 + 1])
    except Exception:
        return None


def log(*a):
    print(*a, flush=True)


class Run:
    def __init__(self, out, seed):
        self.out = out
        os.makedirs(out, exist_ok=True)
        self.res = {'started': datetime.datetime.utcnow().isoformat() + 'Z', 'screens': [], 'print': [], 'buttons': [], 'net': {}, 'errors': []}
        self.rng = random.Random(seed)

    def shot(self, pg, name, full=False):
        p = os.path.join(self.out, 'shots', name + '.jpg')
        os.makedirs(os.path.dirname(p), exist_ok=True)
        try:
            pg.screenshot(path=p, type='jpeg', quality=55, full_page=full)
            return os.path.relpath(p, self.out)
        except Exception as e:
            return None


def new_ctx(br, vp, run, allowed):
    name, w, h, dpr, mob = vp
    ctx = br.new_context(viewport={'width': w, 'height': h}, device_scale_factor=dpr, is_mobile=mob, has_touch=mob,
                         locale='he-IL', user_agent=None)
    ua = br.new_page().evaluate('navigator.userAgent') if False else None
    net = run.res['net'].setdefault(name, {'foreign': {}, 'bad': {}, 'requests': 0})

    def on_req(r):
        net['requests'] += 1
        host = urlparse(r.url).hostname or ''
        if r.url.startswith('data:') or r.url.startswith('blob:'):
            return
        if not any(host == a or host.endswith('.' + a) for a in allowed):
            net['foreign'][host] = net['foreign'].get(host, 0) + 1

    def on_resp(r):
        if r.status >= 400:
            k = '%d %s' % (r.status, r.url[:140])
            net['bad'][k] = net['bad'].get(k, 0) + 1
    ctx.on('request', on_req)
    ctx.on('response', on_resp)
    return ctx


def attach_console(pg, sink):
    pg.on('pageerror', lambda e: sink.append('pageerror: ' + str(e)[:200]))
    pg.on('console', lambda m: sink.append('console.' + m.type + ': ' + m.text[:200]) if m.type in ('error',) else None)


def reveal_all(pg, limit_s=90):
    """פורש את כל זנב הפרק (שורות lz) בגלילה עד הסוף."""
    t0 = time.time()
    last = -1
    while time.time() - t0 < limit_s:
        n = pg.evaluate("document.querySelectorAll('#flow .row.lz').length")
        if n == 0:
            break
        pg.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
        pg.wait_for_timeout(350)
        if n == last:
            pg.evaluate("typeof revealTail==='function'&&revealTail(1e9)")
            pg.wait_for_timeout(500)
        last = n
    pg.evaluate("window.scrollTo(0,0)")
    return round(time.time() - t0, 1)


def probe(pg, site, mobile):
    return pg.evaluate(PROBE + '({site:%s, mobile:%s})' % (json.dumps(site), 'true' if mobile else 'false'))


def tiles(pg, run, prefix, max_tiles, sample):
    """צילומי מסך לאורך כל הדף: הראשונים, ועוד מדגם מתחלף כל לילה (לפי זרע התאריך)."""
    H = pg.evaluate("document.documentElement.scrollHeight")
    vh = pg.evaluate("innerHeight")
    n = max(1, int(H / vh) + 1)
    idx = list(range(min(n, max_tiles)))
    if n > max_tiles:
        rest = list(range(max_tiles, n))
        idx += sorted(run.rng.sample(rest, min(sample, len(rest))))
    out = []
    for i in idx:
        pg.evaluate("window.scrollTo(0,%d)" % (i * vh))
        pg.wait_for_timeout(180)
        p = run.shot(pg, '%s-%04d' % (prefix, i))
        if p:
            out.append({'i': i, 'of': n, 'path': p, 'dh': dhash(os.path.join(run.out, p))})
    pg.evaluate("window.scrollTo(0,0)")
    return out


def leokmei_masechet(br, run, base, slug, parts, a):
    allowed = SITES['leokmei']['allowed']
    url = base.rstrip('/') + '/' + slug + '.html'
    perek_keys = []
    for vp in VIEWPORTS:
        name, w, h, dpr, mob = vp
        if a.viewports and name not in a.viewports.split(','):
            continue
        ctx = new_ctx(br, vp, run, allowed)
        pg = ctx.new_page()
        errs = []
        attach_console(pg, errs)
        rec = {'site': 'leokmei', 'page': slug, 'vp': name, 'mode': 'flow'}
        try:
            t0 = time.time()
            pg.goto(url, wait_until='domcontentloaded', timeout=90000)
            rec['t_dom'] = round(time.time() - t0, 2)
            pg.wait_for_selector('#flow .row', timeout=60000)
            rec['t_first_row'] = round(time.time() - t0, 2)
            rec['t_reveal'] = reveal_all(pg)
            if 'flow' in parts:
                rec['probe'] = probe(pg, 'leokmei', mob)
                rec['tiles'] = tiles(pg, run, '%s/%s/flow' % (slug, name), a.max_tiles if name in ('desktop', 'wide') else 6, a.sample)
            if not perek_keys:
                perek_keys = pg.evaluate("""()=>{try{if(typeof D!=='undefined'&&D.pages){var s=[],k={};D.pages.forEach(function(p){var x=(p.perek||'')+'|'+(p.perekName||'');if(p.perek&&!k[x]){k[x]=1;s.push(x)}});return s}}catch(e){}return []}""")
            rec['errors'] = errs[:]
            run.res['screens'].append(rec)
            # תצוגת ספר
            if 'flow' in parts and name != 'phone':
                errs.clear()
                pg.evaluate("typeof setView==='function'&&setView('book')")
                pg.wait_for_timeout(1500)
                reveal_all(pg, 40)
                rb = {'site': 'leokmei', 'page': slug, 'vp': name, 'mode': 'book', 'probe': probe(pg, 'leokmei', mob)}
                rb['tiles'] = tiles(pg, run, '%s/%s/book' % (slug, name), 8, max(4, a.sample // 3))
                rb['errors'] = errs[:]
                run.res['screens'].append(rb)
            # כל כפתור בסרגל (מבקר, בלי פעולות כותבות)
            if 'buttons' in parts and name in ('desktop', 'phone'):
                pg.evaluate("typeof setView==='function'&&setView('col')")
                pg.reload(wait_until='domcontentloaded'); pg.wait_for_selector('#flow .row', timeout=60000); pg.wait_for_timeout(800)
                btns = pg.evaluate("""()=>[].slice.call(document.querySelectorAll('button,[role=button],a.tbpill')).filter(b=>{var r=b.getBoundingClientRect();
                    return r.width>0&&r.height>0&&!b.closest('#flow')}).map((b,i)=>{b.setAttribute('data-chk',i);return {i:i,t:(b.title||b.getAttribute('aria-label')||b.innerText||'').trim().slice(0,40)}})""")
                for b in btns[:a.max_buttons]:
                    if SKIP_BTN.search(b['t'] or ''):
                        continue
                    errs.clear()
                    r = {'site': 'leokmei', 'page': slug, 'vp': name, 'btn': b['t'], 'i': b['i']}
                    try:
                        before = pg.evaluate("location.href")
                        pg.click('[data-chk="%d"]' % b['i'], timeout=4000)
                        pg.wait_for_timeout(900)
                        r['shot'] = run.shot(pg, '%s/%s/btn-%03d' % (slug, name, b['i']))
                        r['probe'] = probe(pg, 'leokmei', mob)
                        r['nav'] = pg.evaluate("location.href") != before
                        r['errors'] = errs[:]
                        if r['nav']:
                            pg.go_back(); pg.wait_for_timeout(1200)
                        pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
                        # ממשקים שנפתחו ולא נסגרו ב-Escape נסגרים בטעינה מחדש
                        if r.get('nav') or pg.evaluate("!!document.querySelector('.sheet:not([hidden]),.panel.open,dialog[open]')"):
                            pg.reload(wait_until='domcontentloaded'); pg.wait_for_selector('#flow .row', timeout=60000); pg.wait_for_timeout(600)
                            pg.evaluate("""()=>[].slice.call(document.querySelectorAll('button,[role=button],a.tbpill')).filter(b=>{var r=b.getBoundingClientRect();return r.width>0&&r.height>0&&!b.closest('#flow')}).forEach((b,i)=>b.setAttribute('data-chk',i))""")
                    except Exception as e:
                        r['fail'] = str(e)[:200]
                    run.res['buttons'].append(r)
        except Exception:
            rec['fatal'] = traceback.format_exc()[-600:]
            rec['errors'] = errs[:]
            run.res['screens'].append(rec)
        ctx.close()
        time.sleep(a.pause)
    if 'print' in parts:
        leokmei_print(br, run, base, slug, perek_keys, a)


def leokmei_print(br, run, base, slug, keys, a):
    """כל פרופיל הדפסה, לכל פרק: עימוד במנוע של האתר עצמו, PDF, ומדידה."""
    allowed = SITES['leokmei']['allowed']
    profs = a.print_profiles.split(',')
    if not keys:
        run.res['errors'].append('print: לא נמצאה מפת פרקים (D.pages) ב-%s' % slug)
        return
    for ki, key in enumerate(keys):
        for prof in profs:
            if prof == 'book' and ki > 0 and not a.all_booklets:
                continue
            q = {'print': '1', 'pk': key, 'tos': '1', 'duplex': '0', 'profile': 'a4lg' if prof == 'book' else prof}
            if prof == 'book':
                q['lay'] = 'book'
            from urllib.parse import urlencode
            url = base.rstrip('/') + '/' + slug + '.html?' + urlencode(q)
            ctx = new_ctx(br, ('desktop', 1400, 900, 1, False), run, allowed)
            pg = ctx.new_page(); errs = []; attach_console(pg, errs)
            rec = {'site': 'leokmei', 'page': slug, 'perek': key, 'profile': prof, 'url': url}
            try:
                t0 = time.time()
                pg.goto(url, wait_until='domcontentloaded', timeout=90000)
                st = None
                for _ in range(600):
                    st = pg.evaluate("window.__PRN&&window.__PRN.state")
                    if st in ('done', 'error', 'blocked'):
                        break
                    pg.wait_for_timeout(500)
                rec['state'] = st
                rec['t_layout'] = round(time.time() - t0, 1)
                rep = pg.evaluate("(()=>{var r=window.__PRN&&window.__PRN.report;if(!r)return null;return {warn:(r.warn||[]).slice(0,60),keys:Object.keys(r).slice(0,40),error:window.__PRN.error||null}})()")
                rec['report'] = rep
                if st == 'done':
                    pg.emulate_media(media='print')
                    pdf = os.path.join(run.out, 'print', '%s-%d-%s.pdf' % (slug, ki + 1, prof))
                    os.makedirs(os.path.dirname(pdf), exist_ok=True)
                    pg.pdf(path=pdf, prefer_css_page_size=True, print_background=True)
                    rec['pdf'] = os.path.relpath(pdf, run.out)
                    rec['measure'] = measure_pdf(pdf, run.out, '%s/print/%d-%s' % (slug, ki + 1, prof))
            except Exception:
                rec['fatal'] = traceback.format_exc()[-500:]
            rec['errors'] = errs[:20]
            run.res['print'].append(rec)
            log('print', slug, ki + 1, prof, rec.get('state'), rec.get('t_layout'))
            ctx.close()
            time.sleep(a.pause)


def measure_pdf(pdf, out, prefix):
    """מדידה על הקובץ שהופק בפועל: עמודים, גודל, תווים אסורים, חללים לבנים, איזון הטורים בעמוד האחרון."""
    import fitz
    from PIL import Image
    d = fitz.open(pdf)
    m = {'pages': len(d), 'size_mm': [round(d[0].rect.width / 72 * 25.4, 1), round(d[0].rect.height / 72 * 25.4, 1)] if len(d) else None,
         'empty_pages': [], 'em_dash': 0, 'en_dash': 0, 'latin': [], 'white_gaps': [], 'balance_last': None, 'fonts': {}, 'thumbs': []}
    latin_ok = re.compile(r'leokmei\.com|PDF|QR|B5|A4', re.I)
    for i, p in enumerate(d):
        t = p.get_text()
        if not t.strip():
            m['empty_pages'].append(i + 1)
        m['em_dash'] += t.count('—'); m['en_dash'] += t.count('–')
        for w in re.findall(r'[A-Za-z]{2,}[\w.]*', t):
            if not latin_ok.search(w) and len(m['latin']) < 20:
                m['latin'].append([i + 1, w])
        for f in p.get_fonts():
            m['fonts'][f[3]] = m['fonts'].get(f[3], 0) + 1
        pix = p.get_pixmap(dpi=50, colorspace=fitz.csGRAY)
        im = Image.frombytes('L', (pix.width, pix.height), pix.samples)
        W, H = im.size
        px = im.load()
        # שורות לבנות רצופות בתוך תחום הטקסט (בין 8% ל-92% מגובה העמוד)
        run_, best, best_at = 0, 0, 0
        for y in range(int(H * .08), int(H * .92)):
            white = all(px[x, y] > 235 for x in range(int(W * .08), int(W * .92), 3))
            run_ = run_ + 1 if white else 0
            if run_ > best:
                best, best_at = run_, y
        gap_mm = round(best / 50 * 25.4, 1)
        if gap_mm > 25 and i < len(d) - 1:
            m['white_gaps'].append([i + 1, gap_mm])
        if i == len(d) - 1:
            def ink(x0, x1):
                s = 0
                for y in range(0, H, 2):
                    for x in range(int(x0), int(x1), 3):
                        if px[x, y] < 128:
                            s = y  # השורה האחרונה שיש בה דיו
                            break
                return s
            r_, l_ = ink(W * .52, W * .95), ink(W * .05, W * .48)
            if r_ and l_:
                m['balance_last'] = {'right_bottom_mm': round(r_ / 50 * 25.4, 1), 'left_bottom_mm': round(l_ / 50 * 25.4, 1), 'diff_mm': round(abs(r_ - l_) / 50 * 25.4, 1)}
        if i < 40:
            tp = os.path.join(out, 'shots', '%s-p%03d.jpg' % (prefix, i + 1))
            os.makedirs(os.path.dirname(tp), exist_ok=True)
            p.get_pixmap(dpi=60).save(tp.replace('.jpg', '.png'))
            Image.open(tp.replace('.jpg', '.png')).convert('RGB').save(tp, quality=55)
            os.remove(tp.replace('.jpg', '.png'))
            m['thumbs'].append(os.path.relpath(tp, out))
    return m


def generic_site(br, run, key, a):
    """אתר כללי (ממלכת הזוהר, נ"ך המפורש, שפע יואל): זחילה מעמוד הבית, כל גודל מסך, כל הכללים הכלליים."""
    cfg = SITES[key]
    base = cfg['base']
    seen, queue, pages = set(), [base] + [urljoin(base, p) for p in cfg.get('seed', [])], []
    host = urlparse(base).hostname
    ctx = new_ctx(br, VIEWPORTS[3], run, cfg['allowed'])
    pg = ctx.new_page()
    while queue and len(pages) < cfg.get('max_pages', a.max_pages):
        u = queue.pop(0).split('#')[0]
        if u in seen:
            continue
        seen.add(u)
        try:
            pg.goto(u, wait_until='domcontentloaded', timeout=60000); pg.wait_for_timeout(1500)
            pages.append(u)
            for h in pg.evaluate("[].slice.call(document.querySelectorAll('a[href]')).map(a=>a.href)"):
                pu = urlparse(h)
                if pu.hostname == host and not re.search(r'\.(pdf|docx?|zip|jpg|png|mp3|mp4)$', pu.path, re.I) and h.split('#')[0] not in seen:
                    queue.append(h)
        except Exception as e:
            run.res['errors'].append('%s crawl %s: %s' % (key, u, str(e)[:120]))
        time.sleep(a.pause)
    ctx.close()
    for vp in VIEWPORTS:
        if a.viewports and vp[0] not in a.viewports.split(','):
            continue
        ctx = new_ctx(br, vp, run, cfg['allowed'])
        for i, u in enumerate(pages):
            pg = ctx.new_page(); errs = []; attach_console(pg, errs)
            rec = {'site': key, 'page': u, 'vp': vp[0], 'mode': 'page'}
            try:
                t0 = time.time(); pg.goto(u, wait_until='load', timeout=60000); rec['t_load'] = round(time.time() - t0, 2)
                pg.wait_for_timeout(1200)
                rec['probe'] = probe(pg, key, vp[4])
                rec['tiles'] = [{'i': 0, 'of': 1, 'path': run.shot(pg, '%s/%s/%03d' % (key, vp[0], i))}]
            except Exception:
                rec['fatal'] = traceback.format_exc()[-400:]
            rec['errors'] = errs[:20]
            run.res['screens'].append(rec)
            pg.close()
            time.sleep(a.pause / 2)
        ctx.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--site', default='leokmei')
    ap.add_argument('--only', default='')
    ap.add_argument('--out', default='')
    ap.add_argument('--parts', default='flow,buttons,print')
    ap.add_argument('--viewports', default='')
    ap.add_argument('--print-profiles', default='a4lg,b5lg,book')
    ap.add_argument('--all-booklets', action='store_true')
    ap.add_argument('--max-tiles', type=int, default=40)
    ap.add_argument('--sample', type=int, default=24)
    ap.add_argument('--max-buttons', type=int, default=60)
    ap.add_argument('--max-pages', type=int, default=40)
    ap.add_argument('--pause', type=float, default=1.5)
    ap.add_argument('--shard', default='', help='i/n - חלק מן המסכתות, להרצה מקבילה')
    a = ap.parse_args()
    day = datetime.date.today().isoformat()
    out = a.out or os.path.join(ROOT, 'data', 'chokker', 'runs', day)
    run = Run(out, seed=day)
    parts = a.parts.split(',')
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        br = pw.chromium.launch(args=['--font-render-hinting=none'])
        sites = list(SITES) if a.site == 'all' else a.site.split(',')
        for s in sites:
            if s == 'leokmei':
                slugs = a.only.split(',') if a.only else SITES['leokmei']['masechtot']
                if a.shard:
                    i, n = [int(x) for x in a.shard.split('/')]
                    slugs = slugs[i::n]
                for slug in slugs:
                    log('== leokmei', slug)
                    leokmei_masechet(br, run, SITES['leokmei']['base'], slug, parts, a)
            else:
                log('== site', s)
                generic_site(br, run, s, a)
        br.close()
    run.res['finished'] = datetime.datetime.utcnow().isoformat() + 'Z'
    run.res['args'] = vars(a)
    json.dump(run.res, io.open(os.path.join(out, 'walk.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    log('walk done:', out, len(run.res['screens']), 'screens', len(run.res['print']), 'prints', len(run.res['buttons']), 'buttons')


if __name__ == '__main__':
    main()
