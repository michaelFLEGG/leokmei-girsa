const { chromium } = require('playwright');
(async () => { const b = await chromium.launch(), pg = await b.newPage();
  await pg.route('**/*', (r) => r.request().method() !== 'GET' ? r.fulfill({ status: 200, body: '{}' }) : r.continue());
  await pg.goto('https://leokmei.com/berakhot.html', { waitUntil: 'networkidle', timeout: 120000 }); await pg.waitForTimeout(6000);
  const r = await pg.evaluate(() => { const T = window.skpInPageTest; if (!T) return 'אין';
    const x = { orig: '[צד:-]\nשם - טרדת רשות.', text: '[צד:- שאני]\nשם - טרדת רשות.' };
    return JSON.stringify(T.skpChanged(x)) + ' בדף? ' + T.skpInPage(x, '\nצד\nשםטרדתרשות\n'); });
  console.log(r); await b.close(); })();
