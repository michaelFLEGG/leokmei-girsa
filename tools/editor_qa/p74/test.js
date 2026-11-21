// פרומפט 74 - בדיקה בדפדפן אמיתי: קישור כניסה אישי, וסקירה במגע (טאבלט/טלפון) מול מחשב.
// הרצה: NODE_PATH=$(npm root -g) node tools/editor_qa/p74/test.js <site-base> <worker-base> <admin-key-of-local-worker>
// האתר מוגש מקומית (tools/serve.py), ושרת העריכות רץ מקומית (wrangler dev) עם מפתח בדיקה. נתוני סכם מן המאגר.
const { chromium, devices } = require('playwright');
const fs = require('fs');
const [SITE, WK, KEY] = process.argv.slice(2);
const REPO = __dirname + '/../../..';
const res = []; let fails = 0;
const ok = (name, cond, det) => { res.push((cond ? 'עבר   ' : 'נכשל  ') + name + (det !== undefined ? ' - ' + JSON.stringify(det) : '')); if (!cond) fails++; };
const TAB_UA = 'Mozilla/5.0 (Linux; Android 13; SM-T505) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36';
const tabCtx = (b, w, h, extra) => b.newContext(Object.assign({ viewport: { width: w, height: h }, hasTouch: true, isMobile: true, deviceScaleFactor: 1, userAgent: TAB_UA }, extra || {}));
async function wk(path, body, key) {
  const r = await fetch(WK + path, { method: body ? 'POST' : 'GET', headers: Object.assign({ 'content-type': 'application/json' }, key ? { 'x-admin-key': key } : {}), body: body ? JSON.stringify(body) : undefined });
  return r.json();
}

/* ---------------------------------------------------------------- א. קישור הכניסה */
async function loginTests(b) {
  const L = await wk('/link/new', { label: 'הטאבלט של מיכאל' }, KEY);
  const T = L.token;
  const init = c => c.addInitScript(w => { try { localStorage.setItem('lg-api', w); } catch (e) {} }, WK);
  const c1 = await tabCtx(b, 800, 1340); await init(c1);
  const p1 = await c1.newPage();
  await p1.goto(SITE + '/k.html#' + T); await p1.waitForTimeout(2000);
  const s1 = await p1.evaluate(() => ({ href: location.href, txt: document.body.innerText, k: localStorage.getItem('lg-adm') || '', a: localStorage.getItem('lg-admin') }));
  ok('כניסה בקישור: המכשיר מוכר כמנהל', /מוכר מעכשיו כמנהל/.test(s1.txt) && s1.a === '1' && s1.k.length === 64);
  ok('האסימון נמחק משורת הכתובת', s1.href.indexOf(T) < 0 && !/#/.test(s1.href), s1.href.replace(/[0-9a-f]{20,}/g, '<...>'));
  ok('אסימון המכשיר שונה מאסימון הקישור', s1.k !== T);
  // יציאה וחזרה: דף חדש באותו מכשיר
  await p1.close(); const p1b = await c1.newPage();
  await p1b.goto(SITE + '/k.html'); await p1b.waitForTimeout(2000);
  const t1b = await p1b.evaluate(() => document.body.innerText);
  ok('יציאה וחזרה: עדיין מנהל (בלי מילה ובלי מפתח)', /מוכר כמנהל/.test(t1b) && /הטאבלט של מיכאל/.test(t1b));
  ok('מסך הניהול: רשימת מכשירים עם סוג ושימוש אחרון', /טאבלט/.test(t1b) && /שימוש אחרון/.test(t1b));
  const w1 = await p1b.evaluate(async w => { const r = await fetch(w + '/whoami', { headers: { 'x-admin-key': localStorage.getItem('lg-adm') } }); return r.json(); }, WK);
  ok('השרת מזהה את המכשיר כמנהל', w1.admin === true);
  await p1b.goto(SITE + '/berakhot.html'); await p1b.waitForTimeout(6000);
  ok('דף מסכת: מצב מנהל פעיל', await p1b.evaluate(() => document.body.classList.contains('adm') || localStorage.getItem('lg-admin') === '1'));
  // מכשיר שני עם אותו קישור
  const c2 = await tabCtx(b, 412, 915); await init(c2); const p2 = await c2.newPage();
  await p2.goto(SITE + '/k.html#' + T); await p2.waitForTimeout(2000);
  const s2 = await p2.evaluate(() => ({ txt: document.body.innerText, k: localStorage.getItem('lg-adm') || '' }));
  ok('קישור שנשרף אינו עובד במכשיר שני', /אינו בתוקף/.test(s2.txt) && !s2.k);
  // קישור שבוטל
  const L2 = await wk('/link/new', { label: 'לביטול' }, KEY);
  await wk('/links/revoke', { id: L2.id }, KEY);
  const c3 = await tabCtx(b, 800, 1340); await init(c3); const p3 = await c3.newPage();
  await p3.goto(SITE + '/k.html#' + L2.token); await p3.waitForTimeout(2000);
  ok('קישור שבוטל אינו עובד', /אינו בתוקף/.test(await p3.evaluate(() => document.body.innerText)) && !(await p3.evaluate(() => localStorage.getItem('lg-adm'))));
  // גולש רגיל
  const c4 = await tabCtx(b, 800, 1340); await init(c4); const p4 = await c4.newPage();
  await p4.goto(SITE + '/k.html'); await p4.waitForTimeout(1500);
  ok('גולש רגיל: אינו מוכר כמנהל', /אינו מוכר כמנהל/.test(await p4.evaluate(() => document.body.innerText)));
  const anon = await wk('/devices'); const anonL = await wk('/links'); const anonN = await wk('/link/new', {});
  ok('גולש רגיל: אין לו שום הרשאה בשרת', anon.ok === false && anonL.ok === false && anonN.ok === false);
  const bad = await wk('/link/redeem', { t: 'a'.repeat(64) });
  ok('אסימון מנוחש נדחה', bad.ok === false);
  // ביטול המכשיר
  const devs = await wk('/devices', null, KEY); const d = devs.devices.find(x => x.label && x.label.indexOf('הטאבלט של מיכאל') === 0);
  await wk('/devices/revoke', { id: d.id }, KEY);
  const w2 = await wk('/whoami', null, s1.k);
  ok('מכשיר שבוטל מאבד את ההרשאה', w2.admin === false);
  await Promise.all([c1, c2, c3, c4].map(c => c.close()));
}

/* ---------------------------------------------------------------- ב. הסקירה במגע */
const JID = 'berakhot-p2';
const outJ = JSON.parse(fs.readFileSync(REPO + '/data/sakem/out/' + JID + '.json', 'utf8'));
const job = { jid: JID, slug: 'berakhot', kind: 'perek', perek: 2, title: outJ.title || 'בדיקה', st: 'ready', n: outJ.items.length, shown: outJ.items.length, dec: 0 };
async function mock(c, writes) {
  await c.route('**/*', r => {
    const u = r.request().url(), m = r.request().method();
    if (/raw\.githubusercontent\.com/.test(u)) return r.fulfill({ status: 404, body: '' });
    if (!/leokmei-suggest|localhost:8799/.test(u)) return r.continue();
    if (/\/sakem\/jobs/.test(u)) return r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ ok: true, items: [job] }) });
    if (/\/sakem\/out/.test(u)) return r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ ok: true, job, out: outJ, dec: {} }) });
    if (m !== 'GET') { writes.push(u.split('?')[0].replace(/^https?:\/\/[^/]+/, '')); return r.fulfill({ status: 200, contentType: 'application/json', body: '{"ok":true}' }); }
    if (/\/whoami/.test(u)) return r.fulfill({ status: 200, contentType: 'application/json', body: '{"ok":true,"admin":true}' });
    return r.fulfill({ status: 200, contentType: 'application/json', body: '{"ok":true,"items":[],"edits":[],"doc":{}}' });
  });
  await c.addInitScript(() => { localStorage.setItem('lg-admin', '1'); localStorage.setItem('lg-adm', 'f'.repeat(64)); });
}
const pos = pg => pg.evaluate(() => { const m = /קטע (\d+) מתוך (\d+)/.exec((document.querySelector('#skpbar') || {}).textContent || ''); return m ? +m[1] : -1; });
const cnt = pg => pg.evaluate(() => { const m = /התקבלו (\d+) · נדחו (\d+) · נערכו (\d+)/.exec((document.querySelector('#skpbar') || {}).textContent || ''); return m ? [+m[1], +m[2], +m[3]] : null; });
/* חפיפת מלבנים: שום כפתור או אלמנט צף אינו מכסה טקסט של הקטע הנסקר או את השורה האחרונה */
const overlap = pg => pg.evaluate(() => {
  const bar = document.querySelector('#tchbar'); const br = bar.getBoundingClientRect();
  const vis = e => { const s = getComputedStyle(e); return s.display !== 'none' && s.visibility !== 'hidden' && +s.opacity !== 0 && e.offsetWidth > 0 && e.offsetHeight > 0; };
  let fixed = [...document.querySelectorAll('body *')].filter(e => { const s = getComputedStyle(e); return (s.position === 'fixed' || s.position === 'sticky') && vis(e) && !e.closest('#bar,#mtop,#mprog,#topbar'); });
  /* שכבה שקופה שאינה תופסת מגע (pointer-events:none) אינה מכסה דבר בעצמה: נבדקים הילדים הנראים שלה */
  fixed = fixed.flatMap(e => getComputedStyle(e).pointerEvents === 'none' ? [...e.querySelectorAll('*')].filter(x => vis(x) && getComputedStyle(x).pointerEvents !== 'none') : [e]);
  const g = document.querySelector('.skmghost');
  const lines = g ? [...g.querySelectorAll('.skmmain p')].map(p => p.getBoundingClientRect()).filter(r => r.height > 0 && r.bottom > 60 && r.top < innerHeight) : [];
  const hit = [];
  for (const f of fixed) { const fr = f.getBoundingClientRect();
    for (const r of lines) if (r.left < fr.right && r.right > fr.left && r.top < fr.bottom && r.bottom > fr.top) { hit.push((f.id || f.className || f.tagName) + ''); break; } }
  return { hit, lines: lines.length, barTop: Math.round(br.top), barH: Math.round(br.height), minBtn: Math.min(...[...bar.querySelectorAll('button')].map(b => Math.min(b.offsetHeight, b.offsetWidth))), btns: [...bar.querySelectorAll('button span')].map(s => s.textContent) };
});
const lastLine = pg => pg.evaluate(async () => {
  const f = document.querySelector('#flow'); const se = document.scrollingElement;
  se.scrollTop = se.scrollHeight; if (f) f.scrollTop = f.scrollHeight; await new Promise(r => setTimeout(r, 400));
  const rows = [...document.querySelectorAll('#flow .main p, #flow .main')].filter(e => e.offsetHeight > 0);
  const last = rows[rows.length - 1].getBoundingClientRect(); const bt = document.querySelector('#tchbar').getBoundingClientRect().top;
  return { lastBottom: Math.round(last.bottom), barTop: Math.round(bt), hscroll: se.scrollWidth > innerWidth + 2 };
});
async function swipe(pg, cdp, x0, x1, y) {
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: x0, y }] });
  for (let i = 1; i <= 6; i++) await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: x0 + (x1 - x0) * i / 6, y }] });
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
  await pg.waitForTimeout(600);
}
async function reviewTests(b, label, ctxP) {
  const writes = []; const c = await ctxP; await mock(c, writes);
  const pg = await c.newPage(); const errs = []; pg.on('pageerror', e => errs.push(String(e)));
  pg.on('dialog', d => d.accept());
  await pg.goto(SITE + '/berakhot.html#skp=' + JID, { waitUntil: 'load', timeout: 120000 });
  await pg.waitForFunction(() => window.lgTouch && lgTouch.mode() === 'skp', null, { timeout: 30000 }).catch(() => {});
  await pg.waitForTimeout(1500);
  ok(label + ': סרגל המגע פעיל בסקירת סכם', await pg.evaluate(() => window.lgTouch && lgTouch.mode() === 'skp' && !document.querySelector('#tchbar').hidden));
  const ov = await overlap(pg);
  ok(label + ': חמשת הכפתורים בסרגל, בעברית', ['הקודם', 'הבא בתור', 'ערוך', 'פרטים'].every(t => ov.btns.includes(t)) && ov.btns.some(t => /קבל/.test(t)) && ov.btns.some(t => /דחה|השאר/.test(t)), ov.btns);
  ok(label + ': כפתורים בגודל 48 פיקסלים לפחות', ov.minBtn >= 48, ov.minBtn);
  ok(label + ': שום אלמנט צף אינו מכסה את טקסט הקטע', ov.lines > 0 && ov.hit.length === 0, ov.hit);
  ok(label + ': סרגל סכם המקורי וסרגל הניווט מוסתרים בסקירה', await pg.evaluate(() => getComputedStyle(document.querySelector('#skpbar')).display === 'none' && (!document.querySelector('#mbot') || getComputedStyle(document.querySelector('#mbot')).display === 'none')));
  const tap = async a => { await pg.tap('#tchbar button[data-a="' + a + '"]'); await pg.waitForTimeout(700); };
  const i0 = await pos(pg);
  // משוב חזותי מיידי
  const fb = await pg.evaluate(() => { const bt = document.querySelector('#tchbar button[data-a="next"]'); const t = performance.now(); bt.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true })); const has = bt.classList.contains('tap'); const dt = performance.now() - t; bt.dispatchEvent(new PointerEvent('pointerup', { bubbles: true })); return { has, dt }; });
  ok(label + ': משוב חזותי מיידי (פחות מ-100 אלפיות)', fb.has && fb.dt < 100, Math.round(fb.dt * 10) / 10);
  const tn = await pg.evaluate(async () => { const bt = document.querySelector('#tchbar button[data-a="next"]'); const g0 = document.querySelector('.skmghost'); const t = performance.now(); bt.click(); const ms = performance.now() - t; await new Promise(r => setTimeout(r, 300)); return { ms, changed: document.querySelector('.skmghost') !== g0 }; });
  ok(label + ': "הבא בתור" עובר לקטע הבא', tn.changed && (await pos(pg)) > i0, { ms: Math.round(tn.ms), i: await pos(pg) });
  await tap('prev');
  ok(label + ': "הקודם" חוזר', (await pos(pg)) === i0, await pos(pg));
  const c0 = await cnt(pg);
  await tap('ok');
  const c1 = await cnt(pg);
  ok(label + ': "קבל" מחיל ועובר לבא בתור', c1 && c1[0] === c0[0] + 1 && (await pos(pg)) !== i0, { before: c0, after: c1, i: await pos(pg) });
  ok(label + ': "בטל" קטן מוצג אחרי קבלה', await pg.evaluate(() => !!document.querySelector('#tchundo.on')));
  await pg.tap('#tchundo button'); await pg.waitForTimeout(800);
  const c2 = await cnt(pg);
  ok(label + ': "בטל" מחזיר את ההכרעה', c2 && c2[0] === c0[0], c2);
  const i1 = await pos(pg);
  await tap('no');
  const c3 = await cnt(pg);
  ok(label + ': "דחה" מחיל ועובר לבא בתור', c3 && c3[1] === c0[1] + 1 && (await pos(pg)) !== i1, c3);
  // החלקה = ניווט בלבד
  const before = await cnt(pg), ib = await pos(pg); const daf0 = await pg.evaluate(() => location.hash);
  const cdp = await c.newCDPSession(pg);
  const vw = pg.viewportSize(); const gy = await pg.evaluate(() => { const r = document.querySelector('.skmghost').getBoundingClientRect(); return Math.round(Math.max(120, Math.min(innerHeight - 200, r.top + 60))); });
  await swipe(pg, cdp, vw.width * 0.25, vw.width * 0.75, gy);   // ימינה = הבא
  const ia = await pos(pg);
  await swipe(pg, cdp, vw.width * 0.75, vw.width * 0.25, gy);   // שמאלה = הקודם
  const ic = await pos(pg); const after = await cnt(pg);
  ok(label + ': החלקה ימינה/שמאלה מנווטת בלבד (בלי הכרעה, בלי מעבר דף)', ia !== ib && ic === ib && JSON.stringify(before) === JSON.stringify(after), { ib, ia, ic });
  // הקשה כפולה = עריכה; מקלדת וירטואלית מדומה
  let segOk = await pg.evaluate(() => !!document.querySelector('#tchbar button[data-a="edit"]'));
  for (let k = 0; k < 8 && !segOk; k++) { await tap('next'); segOk = await pg.evaluate(() => !!document.querySelector('#tchbar button[data-a="edit"]')); }
  const pt = await pg.evaluate(() => { const p = document.querySelector('.skmghost .skmmain p') || document.querySelector('.skmghost .skmbody p') || document.querySelector('.skmghost .skmbody'); p.scrollIntoView({ block: 'center' }); const r = p.getBoundingClientRect(); return { x: Math.round(r.left + r.width / 2), y: Math.round(r.top + r.height / 2) }; });
  await pg.waitForTimeout(300);
  await pg.touchscreen.tap(pt.x, pt.y); await pg.waitForTimeout(90); await pg.touchscreen.tap(pt.x, pt.y); await pg.waitForTimeout(600);
  ok(label + ': הקשה כפולה על הקטע פותחת עריכה', await pg.evaluate(() => !!document.querySelector('.skmghost.edit')));
  await pg.evaluate(() => { const H = innerHeight, fake = new EventTarget(); fake.height = Math.round(H * 0.55); fake.offsetTop = 0; fake.width = innerWidth; Object.defineProperty(window, 'visualViewport', { value: fake, configurable: true }); lgTouch.kb(); });
  await pg.waitForTimeout(300);
  const kbS = await pg.evaluate(() => { const b = document.querySelector('#tchbar').getBoundingClientRect(); const vv = visualViewport.height; const sel = getSelection(); const r = sel.rangeCount ? sel.getRangeAt(0).getBoundingClientRect() : null;
    return { barBottom: Math.round(b.bottom), vv, btns: [...document.querySelectorAll('#tchbar button span')].map(s => s.textContent), caret: r ? Math.round(r.bottom) : null, barTop: Math.round(b.top) }; });
  ok(label + ': מקלדת פתוחה - הסרגל עולה מעליה ומתקצר לסיים/בטל', Math.abs(kbS.barBottom - kbS.vv) <= 2 && kbS.btns.join(',') === 'בטל עריכה,סיים וקבל', kbS);
  ok(label + ': מקלדת פתוחה - שדה העריכה אינו מתחת לסרגל', kbS.caret === null || kbS.caret <= kbS.barTop, kbS);
  const ca = await cnt(pg);
  await pg.tap('#tchbar button[data-a="kbok"]'); await pg.waitForTimeout(800);
  const cb = await cnt(pg);
  ok(label + ': "סיים וקבל" מקבל את העריכה', cb && cb[0] + cb[2] > ca[0] + ca[2] && !(await pg.evaluate(() => !!document.querySelector('.skmghost.edit'))), { ca, cb });
  await pg.evaluate(() => { const fake = new EventTarget(); fake.height = innerHeight; fake.offsetTop = 0; Object.defineProperty(window, 'visualViewport', { value: fake, configurable: true }); lgTouch.kb(); });
  // פרטים בחלון תחתון
  await tap('more');
  const sh = await pg.evaluate(() => ({ open: document.documentElement.classList.contains('tchsheet'), bar: !!document.querySelector('#tchsheet #skpbar'), vis: getComputedStyle(document.querySelector('#tchsheet')).transform }));
  ok(label + ': "פרטים" פותח חלון תחתון עם המונים והכפתורים הנוספים', sh.open && sh.bar, sh);
  const sr = await pg.evaluate(() => { const r = document.querySelector('#tchsheet .tchgrip').getBoundingClientRect(); return { x: Math.round(r.left + r.width / 2), y: Math.round(r.top + 3) }; });
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: sr.x, y: sr.y }] });
  for (let i = 1; i <= 5; i++) await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: sr.x, y: sr.y + i * 30 }] });
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] }); await pg.waitForTimeout(500);
  ok(label + ': החלון התחתון נסגר בהחלקה למטה', !(await pg.evaluate(() => document.documentElement.classList.contains('tchsheet'))));
  // השורה האחרונה, וגלילה צדדית
  const ll = await lastLine(pg);
  ok(label + ': השורה האחרונה אינה מוסתרת בסרגל', ll.lastBottom <= ll.barTop, ll);
  ok(label + ': בלי גלילה צדדית', !ll.hscroll);
  ok(label + ': השמירה יוצאת לשרת ברקע (הכרעות נשלחו)', writes.filter(w => /sakem/.test(w)).length >= 3, writes.length);
  ok(label + ': אפס שגיאות בקונסול', errs.length === 0, errs.slice(0, 3));
  await pg.screenshot({ path: process.env.SHOTS ? process.env.SHOTS + '/' + label.replace(/[^\w]+/g, '_') + '.png' : '/dev/null' }).catch(() => {});
  await c.close();
}

/* ---------------------------------------------------------------- ג. מחשב: הכל כמו קודם */
async function desktopTests(b) {
  const writes = []; const c = await b.newContext({ viewport: { width: 1920, height: 1080 } }); await mock(c, writes);
  const pg = await c.newPage(); const errs = []; pg.on('pageerror', e => errs.push(String(e)));
  await pg.goto(SITE + '/berakhot.html#skp=' + JID, { waitUntil: 'load', timeout: 120000 });
  await pg.waitForFunction(() => !!document.querySelector('#skpbar'), null, { timeout: 30000 }).catch(() => {});
  await pg.waitForTimeout(1500);
  const s = await pg.evaluate(() => ({ tch: document.documentElement.classList.contains('tch'), bar: !!document.querySelector('#tchbar'), lg: !!window.lgTouch, nav: !!document.querySelector('#skpbar .skpnav'), side: !!document.querySelector('.skpside'), disp: getComputedStyle(document.querySelector('#skpbar')).display }));
  ok('מחשב 1920: אין סרגל מגע ואין שינוי במראה', !s.tch && !s.bar && !s.lg && s.nav && s.side && s.disp !== 'none', s);
  const i0 = await pos(pg); await pg.keyboard.press('ArrowDown'); await pg.waitForTimeout(500); const i1 = await pos(pg);
  await pg.keyboard.press('ArrowUp'); await pg.waitForTimeout(500); const i2 = await pos(pg);
  const c0 = await cnt(pg); await pg.keyboard.press('Enter'); await pg.waitForTimeout(700); const c1 = await cnt(pg);
  await pg.keyboard.press('Control+z'); await pg.waitForTimeout(700); const c2 = await cnt(pg);
  const i3 = await pos(pg); await pg.evaluate(() => document.activeElement && document.activeElement.blur && 0);
  await pg.keyboard.press("'"); await pg.waitForTimeout(700); const c3 = await cnt(pg);
  await pg.keyboard.press('e'); await pg.waitForTimeout(500); const ed = await pg.evaluate(() => !!document.querySelector('.skmghost.edit'));
  await pg.keyboard.press('Escape'); await pg.waitForTimeout(300);
  ok("מחשב 1920: הקיצורים עובדים (חצים, Enter, Ctrl+ז, גרש, E)", i1 > i0 && i2 === i0 && c1[0] === c0[0] + 1 && c2[0] === c0[0] && c3[1] === c2[1] + 1 && ed, { i0, i1, i2, c0, c1, c2, c3, ed });
  ok('מחשב 1920: אפס שגיאות בקונסול', errs.length === 0, errs.slice(0, 3));
  await c.close();
}

(async () => {
  const b = await chromium.launch();
  const only = process.env.ONLY || '';
  if (!only || only === 'login') await loginTests(b);
  if (!only || only === 'review') {
    for (const [l, cp] of [['Galaxy Tab A7 לאורך 800', () => tabCtx(b, 800, 1340)], ['Galaxy Tab A7 לרוחב 1340', () => tabCtx(b, 1340, 800)], ['טלפון', () => b.newContext(devices['Pixel 7'])]])
      try { await reviewTests(b, l, cp()); } catch (e) { ok(l + ': הבדיקה רצה עד הסוף', false, String(e).slice(0, 200)); }
  }
  if (!only || only === 'desk') await desktopTests(b);
  await b.close();
  console.log(res.join('\n'));
  console.log('\nסיכום: ' + res.length + ' בדיקות, ' + fails + ' נכשלו');
  process.exit(fails ? 1 : 0);
})();
