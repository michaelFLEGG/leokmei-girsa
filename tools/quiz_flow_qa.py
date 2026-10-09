# -*- coding: utf-8 -*-
"""quiz_flow_qa.py - מסלול מלא של "בחן את עצמך" בדפדפן: פתיחה, שאלה, משוב, רצף, סיום (צילומים), ובדיקות הצלילים.
הרצה: uv run --with playwright python tools/quiz_flow_qa.py --base http://127.0.0.1:8790 --out <dir> [--only p390,t-tabA7]
כל נכונה נבחרת לפי בנק השאלות (התשובה הנכונה היא o[0]); כל שגויה - האפשרות הראשונה שאינה נכונה."""
import os, sys, json, argparse, io
from playwright.sync_api import sync_playwright

DEVS = [('p360x800', 360, 800, 3, True), ('p390x844', 390, 844, 3, True), ('p412x915', 412, 915, 2.6, True), ('p375x667', 375, 667, 2, True),
        ('t-tabA7', 800, 1334, 2, True), ('t768x1024', 768, 1024, 2, True), ('t820x1180', 820, 1180, 2, True), ('t1024x1366', 1024, 1366, 2, True),
        ('d1366x768', 1366, 768, 1, False), ('d1920x1080', 1920, 1080, 1, False)]

PICK = r'''async (want) => {
  const card = document.querySelector('.qz-card'); if (!card) return {err: 'no-card'};
  const qtext = card.querySelector('.lm-qq').textContent.trim();
  if (!window.__bank) window.__bank = await fetch('quiz/berakhot.json').then(r => r.json());
  const q = window.__bank.q.find(x => x.q.trim() === qtext);
  const btns = [...card.querySelectorAll('.qz-opt')];
  let idx = -1;
  if (q) idx = btns.findIndex(b => b.querySelector('span').textContent.trim() === q.o[0].trim());
  if (idx < 0) idx = 0;
  const pickIdx = want ? idx : (idx === 0 ? 1 : 0);
  btns[pickIdx].click();
  return {ok: want, q: qtext.slice(0, 20)};
}'''


def run(base, out, only):
    res = {}
    with sync_playwright() as pw:
        br = pw.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
        for name, w, h, dpr, mob in DEVS:
            if only and not any(o in name for o in only): continue
            for ori in (['portrait', 'landscape'] if mob else ['desktop']):
                vw, vh = (w, h) if ori != 'landscape' else (h, w)
                ctx = br.new_context(viewport={'width': vw, 'height': vh}, device_scale_factor=dpr, is_mobile=mob, has_touch=mob, locale='he-IL')
                d = os.path.join(out, '%s-%s' % (name, ori)); os.makedirs(d, exist_ok=True)
                pg = ctx.new_page(); errs = []
                pg.on('pageerror', lambda e, errs=errs: errs.append(str(e)[:150]))
                pg.on('console', lambda m, errs=errs: errs.append('console:' + m.text[:120]) if m.type == 'error' else None)
                info = {}
                try:
                    pg.goto(base.rstrip('/') + '/quiz.html?m=berakhot', wait_until='domcontentloaded', timeout=45000)
                    pg.wait_for_selector('.qz-door', timeout=20000); pg.wait_for_timeout(600)
                    pg.screenshot(path=os.path.join(d, 'q1-opening.png'))
                    pg.click('.qz-door.bahur'); pg.wait_for_selector('#lm-qm-m', timeout=20000); pg.wait_for_timeout(500)
                    info['door_label'] = pg.inner_text('.qz-door.bahur b') if pg.query_selector('.qz-door.bahur b') else ''
                    pg.screenshot(path=os.path.join(d, 'q2-home.png'))
                    pg.click('#lm-qm-m'); pg.wait_for_selector('.qz-card', timeout=20000); pg.wait_for_timeout(500)
                    pg.screenshot(path=os.path.join(d, 'q3-question.png'))
                    # שלוש נכונות רצופות, ואז שגויה
                    for k, want in enumerate([True, True, True, False]):
                        pg.evaluate(PICK, want); pg.wait_for_timeout(1300)
                        if k == 2: pg.screenshot(path=os.path.join(d, 'q4-feedback-streak.png'))
                        if k == 3: pg.screenshot(path=os.path.join(d, 'q5-feedback-wrong.png'))
                        pg.wait_for_timeout(1100); pg.evaluate("document.querySelector('#qz-tu')&&document.querySelector('#qz-tu').click()"); pg.evaluate("document.querySelector('#qz-next')&&document.querySelector('#qz-next').click()"); pg.wait_for_timeout(500)
                    # שאר הסבב: כולן נכונות
                    for k in range(20):
                        if pg.query_selector('.qz-end'): break
                        pg.evaluate("document.querySelector('#qz-tu')&&document.querySelector('#qz-tu').click()")
                        if not pg.query_selector('.qz-opt:not([disabled])'):
                            pg.evaluate("document.querySelector('#qz-next')&&document.querySelector('#qz-next').click()"); pg.wait_for_timeout(300); continue
                        pg.evaluate(PICK, True); pg.wait_for_timeout(1700)
                        pg.evaluate("document.querySelector('#qz-tu')&&document.querySelector('#qz-tu').click()")
                        pg.evaluate("document.querySelector('#qz-next')&&document.querySelector('#qz-next').click()"); pg.wait_for_timeout(350)
                    pg.wait_for_selector('.qz-end', timeout=30000); pg.wait_for_timeout(900)
                    pg.screenshot(path=os.path.join(d, 'q6-finish.png'))
                    info['sfx'] = pg.evaluate("window.LAMED && LAMED.quiz && LAMED.quiz.sfxLog ? LAMED.quiz.sfxLog.join(',') : 'n/a'")
                    info['hscroll'] = pg.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1")
                    info['best'] = pg.evaluate("(document.querySelector('.qz-best')||{}).textContent||''")
                except Exception as e:
                    info['fatal'] = str(e)[:200]
                    try:
                        pg.screenshot(path=os.path.join(d, 'fail.png')); info['text'] = pg.inner_text('main')[:300]
                    except Exception: pass
                info['errors'] = errs[:5]
                res['%s-%s' % (name, ori)] = info
                ctx.close(); print(name, ori, json.dumps(info, ensure_ascii=False)[:160], flush=True)
        br.close()
    io.open(os.path.join(out, 'quiz-results.json'), 'w', encoding='utf-8').write(json.dumps(res, ensure_ascii=False, indent=1))
    return res


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--base', required=True); ap.add_argument('--out', required=True); ap.add_argument('--only', default='')
    a = ap.parse_args(); run(a.base, a.out, [x for x in a.only.split(',') if x])
