# -*- coding: utf-8 -*-
"""qa_blind_ui.py - בדיקת דפדפן (Playwright) למבחן המנועים העיוור ולהערות התוספות, מול בנייה מקומית ושרת /tos מדומה.

מרים את site/ על localhost ואת mock_tos_server, נכנס כמנהל מדומה, ובודק: שהסימנים הונחו במקומם (ללא "עוגן זז"), שאין שגיאות קונסול,
שהכרטיסים נפתחים באותיות בלבד בלי שם מנוע, בחירה בעכבר ובמקלדת, זוג, "אף אחת", עריכה, והנוסח הנבחר מתפרסם מיד לגולש רגיל,
וחשיפת התוצאות. צילומי מסך נשמרים בתיקיית הפלט.

    uv run --with playwright python tools/tosafot/qa_blind_ui.py sukkah <תיקיית-פלט>
"""
import sys, os, json, time, subprocess, threading, http.server, socketserver, functools
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
from playwright.sync_api import sync_playwright

slug = sys.argv[1]
out = sys.argv[2]
os.makedirs(out, exist_ok=True)
PORT, API = 8765, 8788

mock = subprocess.Popen([sys.executable, os.path.join(HERE, 'mock_tos_server.py'), str(API)])
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a, **k):
        pass


Handler = functools.partial(Quiet, directory=os.path.join(ROOT, 'site'))
socketserver.TCPServer.allow_reuse_address = True
srv = socketserver.TCPServer(('127.0.0.1', PORT), Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
time.sleep(1)
fails, notes = [], []


def check(ok, msg):
    (notes if ok else fails).append(('OK ' if ok else 'FAIL ') + msg)
    print(('OK   ' if ok else 'FAIL ') + msg)


try:
    with sync_playwright() as p:
        br = p.chromium.launch()
        for label, vp, mobile in (('desktop', {'width': 1280, 'height': 900}, False), ('phone', {'width': 390, 'height': 800}, True)):
            ctx = br.new_context(viewport=vp, is_mobile=mobile, has_touch=mobile, locale='he-IL')
            ctx.add_init_script("localStorage.setItem('lg-api','http://127.0.0.1:%d');localStorage.setItem('lg-admin','1');localStorage.setItem('lg-adm','test-key');localStorage.setItem('lg-tos-mode','foot')" % API)
            pg = ctx.new_page()
            errs = []
            pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
            pg.on('pageerror', lambda e: errs.append('PAGEERROR ' + str(e)))
            pg.goto('http://localhost:%d/%s.html' % (PORT, slug), wait_until='networkidle')
            pg.wait_for_timeout(1500)
            opts = pg.evaluate("[...document.querySelectorAll('#dafsel option')].map(o=>o.textContent+'|'+o.value)")
            target = [o for o in opts if o.startswith('מג') and ('.' in o.split('|')[0])]
            idx = int(target[0].split('|')[1]) if target else None
            check(idx is not None, '%s: נמצא עמוד מג. בבורר הדפים' % label)
            pg.evaluate("v=>{const s=document.getElementById('dafsel');s.value=v;s.dispatchEvent(new Event('change',{bubbles:true}))}", str(idx))
            pg.wait_for_timeout(1500)
            marks = pg.evaluate("document.querySelectorAll('#flow .tsa').length")
            moved = pg.evaluate("document.querySelectorAll('#flow .tsa[data-r=\"m\"]').length")
            check(marks > 0, '%s: סימני תוספות בעמוד מג.: %d' % (label, marks))
            check(moved == 0, '%s: אין עוגן שזז: %d' % (label, moved))
            foot = pg.evaluate("[...document.querySelectorAll('.tsfoot .tsn')].map(n=>n.textContent.slice(0,90))")
            check(len(foot) == marks, '%s: מספר ההערות בתחתית (%d) שווה למספר הסימנים (%d)' % (label, len(foot), marks))
            pg.screenshot(path=os.path.join(out, '%s-1-footnotes.png' % label))
            # פותחים את המבחן
            pg.evaluate("tosTestOpen()")
            pg.wait_for_selector('#tostest .ttc', timeout=8000)
            txt = pg.inner_text('#tostest')
            check(all(n not in txt for n in ('fable', 'opus', 'sonnet', 'haiku', 'פייבל', 'אופוס', 'סונט', 'הייקו')), '%s: אין שם מנוע בכרטיס' % label)
            check(all(L in txt for L in 'אבגדה'), '%s: חמש האופציות באותיות א-ה' % label)
            pg.screenshot(path=os.path.join(out, '%s-2-card.png' % label), full_page=False)
            total = pg.evaluate("document.querySelector('#tostest .tth h2').textContent")
            print('   ', total)
            # בחירה במקש 2
            pg.keyboard.press('2')
            pg.wait_for_timeout(600)
            doc = json.loads(pg.evaluate("fetch('http://127.0.0.1:%d/tos?slug=%s&adm=1').then(r=>r.text())" % (API, slug)))['doc']
            check(len(doc['picks']) >= 1, '%s: הבחירה נשמרה בשרת מיד (%d)' % (label, len(doc['picks'])))
            # עריכה חופשית
            pg.click('#tostest [data-a=edit][data-l=c]')
            pg.fill('#ttedit', 'נוסח לבדיקה שנערך')
            pg.click('#tostest [data-a=saveedit]')
            pg.wait_for_timeout(600)
            # מעבר, "אף אחת"
            pg.keyboard.press('ArrowLeft')
            pg.wait_for_timeout(300)
            pg.click('#tostest [data-a=none]')
            pg.wait_for_timeout(600)
            # זוג
            pg.keyboard.press('ArrowLeft')
            pg.wait_for_timeout(300)
            pg.click('#tostest [data-a=pair]')
            pg.click('#tostest [data-a=pick][data-l=a]')
            pg.click('#tostest [data-a=pick][data-l=d]')
            pg.wait_for_timeout(600)
            pg.screenshot(path=os.path.join(out, '%s-3-after.png' % label))
            doc = json.loads(pg.evaluate("fetch('http://127.0.0.1:%d/tos?slug=%s&adm=1').then(r=>r.text())" % (API, slug)))['doc']
            kinds = [v['t'][:40] for v in doc['notes'].values()]
            check(any(t.startswith('[שתיים: א,ד]') for t in kinds), '%s: זוג נשמר בהערה' % label)
            check(any(t.startswith('[אף אחת]') for t in kinds), '%s: "אף אחת" נשמר בהערה' % label)
            check(any(v['p'] == 'custom' for v in doc['picks'].values()), '%s: עריכה חופשית נשמרה' % label)
            # חשיפה
            pg.once('dialog', lambda d: d.accept())
            pg.click('#tostest [data-a=reveal]')
            pg.wait_for_selector('#tostest .ttr table', timeout=8000)
            rtxt = pg.inner_text('#tostest')
            check('כמה פעמים נבחר' in rtxt and 'המלצה' in rtxt, '%s: מסך התוצאות מוצג' % label)
            pg.screenshot(path=os.path.join(out, '%s-4-results.png' % label), full_page=True)
            # גולש רגיל רואה את הנוסח הנבחר
            pg.evaluate("document.getElementById('tostest').classList.remove('open')")
            ctx2 = br.new_context(viewport=vp, locale='he-IL')
            ctx2.add_init_script("localStorage.setItem('lg-api','http://127.0.0.1:%d');localStorage.setItem('lg-tos-mode','foot')" % API)
            p2 = ctx2.new_page()
            p2.goto('http://localhost:%d/%s.html' % (PORT, slug), wait_until='networkidle')
            p2.wait_for_timeout(800)
            first = [o for o in opts if o.startswith('מב') and ('.' in o.split('|')[0])]
            p2.evaluate("v=>{const s=document.getElementById('dafsel');s.value=v;s.dispatchEvent(new Event('change',{bubbles:true}))}", first[0].split('|')[1])
            p2.wait_for_timeout(1500)
            pub = p2.evaluate("[...document.querySelectorAll('.tsfoot .tsn')].map(n=>n.textContent)")
            check(any('נוסח לבדיקה שנערך' in t for t in pub), '%s: גולש רגיל רואה מיד את הנוסח שנבחר/נערך' % label)
            check(not p2.evaluate("!!document.getElementById('tostest')&&document.getElementById('tostest').classList.contains('open')"), '%s: גולש רגיל לא רואה את המבחן' % label)
            real_errs = [e for e in errs if 'favicon' not in e and 'Failed to load resource' not in e]
            check(not real_errs, '%s: אין שגיאות קונסול %s' % (label, real_errs[:3]))
            ctx.close(); ctx2.close()
        br.close()
finally:
    srv.shutdown(); mock.terminate()
print('\nנכשלו:', len(fails))
sys.exit(1 if fails else 0)
