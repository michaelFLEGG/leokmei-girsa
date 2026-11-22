const { chromium } = require('playwright');
(async () => { const b = await chromium.launch(), pg = await b.newPage();
  await pg.route('**/*', (r) => r.request().method() !== 'GET' ? r.fulfill({ status: 200, body: '{}' }) : r.continue());
  await pg.goto('https://leokmei.com/berakhot.html', { waitUntil: 'networkidle', timeout: 120000 }); await pg.waitForTimeout(12000);
  const ids = [438, 1794916021185, 972, 986, 1025, 1050, 1085, 1089, 1122, 1176, 1183, 1198, 1204];
  const r = await pg.evaluate((ids) => { const fu = (typeof flatU==="function")?flatU():null; if (!fu) return "no flatU";
    return ids.map((id) => { const o = fu.find((x) => x.u.id === id); if (!o) return id + ': לא נמצא'; return id + ' | ' + (o.u.a || '') + ' | ' + JSON.stringify(o.u.l.map((l) => l[1])).replace(/<[^>]+>/g, '').slice(0, 110); }); }, ids);
  console.log(Array.isArray(r) ? r.join('\n') : r); await b.close(); })();
