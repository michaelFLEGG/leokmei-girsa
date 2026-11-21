// פרומפט 74: צילום מהיר של הסקירה בטאבלט (לעיון). node tools/editor_qa/p74/shot.js <base> <out.png> [w] [h]
const { chromium } = require('playwright');
const fs = require('fs');
const [base, out, W, Hh] = [process.argv[2], process.argv[3], +(process.argv[4] || 800), +(process.argv[5] || 1340)];
const REPO = __dirname + '/../../..';
const JID = process.env.JID || 'berakhot-p2';
const outJ = JSON.parse(fs.readFileSync(REPO + '/data/sakem/out/' + JID + '.json', 'utf8'));
const job = { jid: JID, slug: 'berakhot', kind: 'perek', perek: +JID.split('-p')[1], title: outJ.title || 'בדיקה', st: 'ready', n: outJ.items.length, shown: outJ.items.length, dec: 0 };
(async () => {
  const b = await chromium.launch();
  const c = await b.newContext({ viewport: { width: W, height: Hh }, hasTouch: true, isMobile: true, deviceScaleFactor: 1,
    userAgent: 'Mozilla/5.0 (Linux; Android 13; SM-T505) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36' });
  await c.route('**/*', r => {
    const u = r.request().url(), m = r.request().method();
    if (!/leokmei-suggest|localhost:8799/.test(u)) return r.continue();
    if (/\/sakem\/jobs/.test(u)) return r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ ok: true, items: [job] }) });
    if (/\/sakem\/out/.test(u)) return r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ ok: true, job, out: outJ, dec: {} }) });
    if (m !== 'GET') return r.fulfill({ status: 200, contentType: 'application/json', body: '{"ok":true}' });
    if (/\/whoami/.test(u)) return r.fulfill({ status: 200, contentType: 'application/json', body: '{"ok":true,"admin":true}' });
    return r.fulfill({ status: 200, contentType: 'application/json', body: '{"ok":true,"items":[],"edits":[],"doc":{}}' });
  });
  await c.addInitScript(() => { localStorage.setItem('lg-admin', '1'); localStorage.setItem('lg-adm', 'f'.repeat(64)); });
  const pg = await c.newPage(); const errs = []; pg.on('pageerror', e => errs.push(String(e)));
  pg.on('dialog', d => d.accept());
  await pg.goto(base + '/berakhot.html#skp=' + JID, { waitUntil: 'load', timeout: 120000 });
  await pg.waitForTimeout(9000);
  console.log(JSON.stringify(await pg.evaluate(() => ({ mode: window.lgTouch && lgTouch.mode(), tch: document.documentElement.className, bar: !!document.querySelector('#tchbar:not([hidden])'), skpbar: !!document.querySelector('#skpbar') }))));
  await pg.screenshot({ path: out });
  console.log('errors', errs.slice(0, 5));
  await b.close();
})();
