const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(); const pg = await b.newPage();
  const caps = [];
  await pg.route('**/*', (r) => { const q = r.request();
    if (q.method() !== 'GET') { if (/sakem\/job/.test(q.url())) caps.push(q.postData()); return r.fulfill({ status: 200, contentType: 'application/json', body: '{"ok":true,"jid":"x"}' }); }
    return r.continue(); });
  const errs = []; pg.on('pageerror', (e) => errs.push(e.message));
  await pg.goto('https://leokmei.com/berakhot.html', { waitUntil: 'networkidle', timeout: 120000 });
  await pg.waitForTimeout(12000);
  const info = await pg.evaluate(() => ({ auto: !!window.skpAuto, secs: window.skpAuto ? window.skpAuto.sections() : null }));
  console.log(JSON.stringify(info).slice(0, 600));
  for (const si of [0, 1]) {
    try { await pg.evaluate((si) => window.skpAuto.enqueue(si, window.skpAuto.title(si) + ' · מילת המקף ו"והקשה" (פרומפט 76)', 'seg'), si); } catch (e) { console.log('ERR', si, e.message); }
  }
  require('fs').writeFileSync(process.argv[2], JSON.stringify(caps.map((x) => JSON.parse(x))));
  console.log('captured', caps.length, 'pageerrors', errs.slice(0, 3));
  await b.close();
})();
