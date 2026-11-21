/* פרומפט 75 ה: הסקירה הפנימית בשורה אחת - "שורה שהתארכה" והצעת מציע מן העורך. על האתר החי, כמנהל מדומה,
   כל כתיבה נלכדת. הרצה: node tools/editor_qa/p75/lines.mjs [--mas <mas.js מוזרק>] */
import fs from 'fs';
import path from 'path';
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
let pw; try { pw = require('playwright'); } catch (e) { pw = require('/opt/node22/lib/node_modules/playwright'); }
const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i > -1 ? process.argv[i + 1] : d; };
const MAS = arg('mas', ''), SLUG = arg('slug', 'arakhin'), OVID = arg('ov', 'b30c25ffa3f59d12');
const res = []; const ok = (n, p, i) => { res.push(p); console.log((p ? 'עבר  ' : 'נכשל ') + n + (i !== undefined ? ' - ' + JSON.stringify(i) : '')); };
const br = await pw.chromium.launch();
const ctx = await br.newContext({ viewport: { width: 1920, height: 1080 } });
const writes = [], errs = [];
await ctx.addInitScript(() => { try { localStorage.setItem('lg-admin', '1'); localStorage.setItem('lg-adm', 'test-token-p75'); } catch (e) {} });
await ctx.route(/workers\.dev|api\.github\.com/, (route) => { const rq = route.request(); if (rq.method() !== 'GET') { writes.push({ p: new URL(rq.url()).pathname, b: rq.postData() || '' }); return route.fulfill({ json: { ok: true, rec: {} } }); } return route.continue(); });
if (MAS) await ctx.route(/leokmei\.com\/mas\.js/, (r) => r.fulfill({ body: fs.readFileSync(MAS, 'utf8'), contentType: 'application/javascript' }));
const pg = await ctx.newPage();
pg.on('pageerror', (e) => errs.push(String(e)));
await pg.goto('https://leokmei.com/' + SLUG + '.html', { waitUntil: 'load' });
await pg.waitForTimeout(4000);

/* --- שורה שהתארכה --- */
const o1 = await pg.evaluate(async (id) => {
  if (!EDIT) setEdit(true);
  for (let k = 0; k < 30 && !OVS.items.length; k++) await new Promise((r) => setTimeout(r, 300));
  const it = OVS.items.find((x) => x.id === id); if (!it) return { err: 'no item ' + OVS.items.length };
  const pi = D.pages.findIndex((p) => (p.units || []).some((u) => u.id === it.u)); render(secOf(pi)); await new Promise((r) => setTimeout(r, 800));
  ovMark(); await new Promise((r) => setTimeout(r, 300));
  if (!it._p) return { err: 'no para' };
  ovOpen(it); OVS.alt = 0; ovDraw();
  const b = document.querySelector('#ovpop .skiuov'); return { btn: !!b, before: it.html.replace(/<[^>]+>/g, '') };
}, OVID);
ok('שורה שהתארכה: כפתור "כל שינוי" בהצעה עם כמה שינויים', o1.btn, o1.err || '');
if (o1.btn) {
  await pg.click('#ovpop .skiuov'); await pg.waitForTimeout(200);
  let st = await pg.evaluate(() => window.skimTest.state());
  ok('נפתחה סקירה פנימית בשורה', st && st.n >= 2, st);
  await pg.keyboard.press('Enter'); await pg.keyboard.press("'");
  st = await pg.evaluate(() => window.skimTest.state());
  const plan = ['a', 'r']; for (let k = 2; k < (st ? st.n : 0); k++) { await pg.keyboard.press(k % 2 ? "'" : 'Enter'); plan.push(k % 2 ? 'r' : 'a'); }
  await pg.waitForTimeout(800);
  const after = await pg.evaluate((id) => { const d = OVS.dec[id]; return { dec: d && d.d, now: d && d.now, pop: !!OVS.pop, cur: OVS.cur && OVS.cur.id, ed: ED.filter((e) => e.t > Date.now() - 120000).length }; }, OVID);
  ok('שורה שהתארכה: התוצאה המעורבת הוחלה ונרשמה (bakara/dec)', after.dec === 'edit' && after.ed > 0, after);
}

/* --- הצעת מציע מן העורך, שלושה שינויים בשורה אחת --- */
const o2 = await pg.evaluate(() => {
  const S = slotsFull(); const s = S.find((x) => x.t && x.t.split(' ').length > 12 && !/<i class="(mk|tzc)"/.test(x.h)); if (!s) return { err: 'no slot' };
  const w = s.t.split(' '); const n = w.slice(); n[2] = n[2] + 'X'; n.splice(6, 1); n[9] = 'בדיקה ' + n[9];
  const now = n.join(' ');
  const g = { id: 'p75t', type: 'nusach', daf: s.daf, t: Date.now(), name: 'בדיקה', was: s.t, note: now, edit: { k: s.k, bt: s.t, was: s.t, now, daf: s.daf } };
  QQ.unshift(g);
  let box = document.getElementById('sgqb'); if (!box) { box = document.createElement('div'); box.id = 'sgqb'; document.body.appendChild(box); }
  box.innerHTML = sqRow(g, s, 0);
  return { k: s.k, btn: !!box.querySelector('.skiusq'), plain: s.t };
});
ok('הצעת מציע: כפתור "כל שינוי" בהצעה עם כמה שינויים', o2.btn, o2.err || '');
if (o2.btn) {
  await pg.evaluate(() => document.querySelector('#sgqb .skiusq').click()); await pg.waitForTimeout(200);
  const st = await pg.evaluate(() => window.skimTest.state());
  ok('נפתחה סקירה פנימית בהצעה', st && st.n >= 3, st);
  await pg.keyboard.press('Enter'); await pg.keyboard.press("'"); for (let k = 2; k < st.n; k++) await pg.keyboard.press('Enter');
  await pg.waitForTimeout(1200);
  const r = await pg.evaluate((k) => { const e = ED.filter((x) => x.sg === 'p75t').pop(); return { now: e && e.now, left: QQ.some((x) => x.id === 'p75t') }; }, o2.k);
  const dec = writes.filter((w) => w.p === '/decide').map((w) => JSON.parse(w.b)).pop() || {};
  const w = o2.plain.split(' '); const want = w.slice(); want[2] = want[2] + 'X';
  /* קבל את הראשון (X), דחה את השני (המחיקה), קבל את השלישי */
  want[10] = 'בדיקה ' + want[10];
  ok('הצעת מציע: הוחלה התוצאה המעורבת (קבל, דחה, קבל)', r.now && !r.left && r.now.replace(/\s+/g, ' ').trim() === want.join(' ').replace(/\s+/g, ' ').trim(), { now: (r.now || '').slice(0, 80), want: want.join(' ').slice(0, 80), st: dec.st });
}
ok('אפס שגיאות בקונסול', !errs.length, errs.slice(0, 3));
await br.close();
process.exit(res.every(Boolean) ? 0 : 1);
