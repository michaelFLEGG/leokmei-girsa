/* פרומפט 75 (מקרי קצה): דחה את כל השאר -> דחיית הכרטיס, "בטל" מחזיר לסקירה הפנימית עם ההכרעות, קבל את כל השאר -> קבלה רגילה.
   ואותה הרצה עם --conflict על כרטיס בהתנגשות. פרומפט 75: בדיקת "סקירה פנימית" בדפדפן אמיתי, על האתר החי (leokmei.com), כמנהל מדומה.
   כל כתיבה לשרת העריכות נלכדת ואינה נשלחת (כמו editor_qa). /sakem/jobs ו-/sakem/out מוגשים מן המאגר
   (data/sakem/out), כך שהכרטיס הוא הצעת סכם אמיתית על הנוסח החי.
   הרצה:  node tools/editor_qa/p75/run.mjs [--mas <mas.js מקומי להזרקה>] [--slug berakhot] [--jid ...] [--iid ...]
          [--w 1920 --h 1080] [--touch tab-portrait|tab-landscape] [--shots <תיקייה>]
   בלי --mas נבדק mas.js החי כפי שהוא (אחרי הפרסום). */
import fs from 'fs';
import path from 'path';
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
let pw; try { pw = require('playwright'); } catch (e) { pw = require('/opt/node22/lib/node_modules/playwright'); }
const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../../..');
const SKU = require(path.join(ROOT, 'tools/sakem_units_core.js'));
const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i > -1 ? process.argv[i + 1] : d; };
const MAS = arg('mas', ''), SLUG = arg('slug', 'berakhot'), SHOTS = arg('shots', '');
const TOUCH = arg('touch', ''), W = +arg('w', 1920), H = +arg('h', 1080);
const report = { checks: [], shots: [] };
const ok = (name, pass, info) => { report.checks.push({ name, pass: !!pass, info }); console.log((pass ? 'עבר  ' : 'נכשל ') + name + (info !== undefined ? ' - ' + (typeof info === 'string' ? info : JSON.stringify(info)) : '')); };

/* מועמדים: הצעות שנדחו (הנוסח החי עדיין המקורי), עם 10 עד 25 יחידות */
function candidates() {
  const out = [];
  const want = arg('jid', '');
  for (const f of fs.readdirSync(path.join(ROOT, 'data/sakem/decisions'))) {
    if (!f.startsWith(SLUG)) continue;
    const jid = f.replace(/\.json$/, '');
    if (want && jid !== want) continue;
    let d, o; try { d = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/sakem/decisions', f))); o = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/sakem/out', jid + '.json'))); } catch (e) { continue; }
    for (const it of o.items || []) {
      const dc = (d.dec || {})[it.iid];
      if (arg('iid', '') && it.iid !== arg('iid', '')) continue;
      if (!dc || !/reject|keep/.test(dc.act) || it.kind !== 'seg') continue;
      const n = SKU.units(it.orig, it.text).u.filter((u) => !u.quiet).length;
      if (n >= 10 && n <= 30) out.push({ jid, it, n, perek: (d.job && d.job.perek) || o.perek || 0 });
    }
  }
  return out;
}

const cands = candidates();
if (!cands.length) { console.log('אין מועמד'); process.exit(2); }
const br = await pw.chromium.launch();
const ctxOpt = TOUCH ? { viewport: TOUCH === 'tab-landscape' ? { width: 1340, height: 800 } : { width: 800, height: 1340 }, deviceScaleFactor: 1, hasTouch: true, isMobile: true,
  userAgent: 'Mozilla/5.0 (Linux; Android 11; SM-T500) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36' } : { viewport: { width: W, height: H } };
const ctx = await br.newContext(ctxOpt);
const writes = [], errs = [];
await ctx.addInitScript(() => { try { localStorage.setItem('lg-admin', '1'); localStorage.setItem('lg-adm', 'test-token-p75'); } catch (e) {} });
let cur = null;
await ctx.route(/workers\.dev|api\.github\.com/, async (route) => {
  const rq = route.request(), u = new URL(rq.url()), p = u.pathname;
  if (p === '/sakem/jobs') return route.fulfill({ json: { ok: true, items: cur ? [{ jid: cur.jid, slug: SLUG, kind: 'perek', perek: cur.perek, title: 'בדיקת פרומפט 75', t: 1, st: 'ready', shown: 1, dec: 0 }] : [] } });
  if (p === '/sakem/out') return route.fulfill({ json: { ok: true, out: { title: 'בדיקה', items: [cur.it] }, dec: {}, job: { jid: cur.jid, slug: SLUG, kind: 'perek', perek: cur.perek, st: 'ready', shown: 1, dec: 0 } } });
  if (rq.method() !== 'GET') { let b = rq.postData() || ''; writes.push({ p, b }); return route.fulfill({ json: { ok: true, job: null, jid: 'x-s1-a' } }); }
  return route.continue();
});
if (MAS) await ctx.route(/leokmei\.com\/mas\.js/, (route) => route.fulfill({ body: fs.readFileSync(MAS, 'utf8'), contentType: 'application/javascript' }));
const pg = await ctx.newPage();
pg.on('pageerror', (e) => errs.push(String(e)));
pg.on('console', (m) => { if (m.type() === 'error' && !/Failed to load resource|net::ERR/.test(m.text())) errs.push(m.text()); });

let opened = null;
for (const c of cands.slice(0, 40)) {
  cur = c;
  await pg.goto('https://leokmei.com/' + SLUG + '.html#p=' + Math.max(0, c.perek - 1), { waitUntil: 'load' });
  await pg.waitForTimeout(3500);
  const r = await pg.evaluate(async (jid) => {
    if (typeof setEdit === 'function' && !EDIT) setEdit(true);
    await new Promise((r) => setTimeout(r, 600));
    window.skpAuto.open(jid);
    for (let k = 0; k < 40 && !(SKP.rev && SKM.ghost); k++) await new Promise((r) => setTimeout(r, 250));
    return { rev: !!SKP.rev, ghost: !!SKM.ghost, conflict: SKP.rev ? !!SKP.rev.conflict : null };
  }, c.jid);
  if (r.rev && r.ghost && (!r.conflict || arg('conflict', ''))) { opened = c; console.log('כרטיס:', c.jid, c.it.iid, 'יחידות', c.n, r.conflict ? '(התנגשות)' : ''); break; }
}
ok('כרטיס עם 10+ שינויים נפתח בסקירה', !!opened, opened ? opened.jid + ' ' + opened.it.iid : 'לא נמצא כרטיס שמאותר בדף');
if (!opened) { await br.close(); process.exit(1); }

await pg.waitForTimeout(1200); await pg.keyboard.press('s'); await pg.waitForTimeout(400);
let st = await pg.evaluate(() => window.skiuTest.state());
ok('נכנסים לסקירה הפנימית', !!st, st && st.n);
await pg.keyboard.press('Enter'); await pg.waitForTimeout(80);
await pg.click('#skiubar [data-k="restR"]'); await pg.waitForTimeout(1200);
let decs = writes.filter((w) => w.p === '/sakem/dec').map((w) => JSON.parse(w.b));
let last = decs[decs.length - 1] || {};
const t1 = await pg.evaluate(() => (document.getElementById('skpalltoast') || {}).textContent || '');
ok('קבל אחד ודחה את כל השאר: הכרטיס הוחל כעריכה מעורבת', last.act === 'edit' && /התקבלו 1/.test(t1), { act: last.act, toast: t1 });
await pg.click('#skpalltoast button'); await pg.waitForTimeout(1500);
st = await pg.evaluate(() => window.skiuTest.state());
decs = writes.filter((w) => w.p === '/sakem/dec').map((w) => JSON.parse(w.b)); last = decs[decs.length - 1] || {};
ok('"בטל": הכרטיס חזר, ובסקירה הפנימית ההכרעות עדיין שם', st && st.done === st.n && last.act === 'undo', st && { done: st.done, n: st.n, lastAct: last.act });
/* משנים הכרעה: הכל דחה -> דחיית הכרטיס */
await pg.evaluate(() => { const S = window.skiuTest.state(); const k = S.units.findIndex((u) => S.dec[u.id] === 'a'); let g = 0; while (window.skiuTest.state().i !== k && g++ < 50) window.skiuTest.act('next'); window.skiuTest.act('r'); });
await pg.waitForTimeout(1200);
decs = writes.filter((w) => w.p === '/sakem/dec').map((w) => JSON.parse(w.b)); last = decs[decs.length - 1] || {};
ok('כל היחידות נדחו: נרשם כדחיית הכרטיס', /reject|keep/.test(last.act), { act: last.act });
await pg.click('#skpalltoast button').catch(() => {}); await pg.waitForTimeout(1500);
st = await pg.evaluate(() => window.skiuTest.state());
if (st) { await pg.click('#skiubar [data-k="exit"]'); await pg.waitForTimeout(300); }
/* קבל את כל השאר מיד בכניסה: קבלה רגילה */
await pg.evaluate(() => { try { localStorage.removeItem('lg-skiu'); } catch (e) {} });
await pg.evaluate(() => skpShow()); await pg.waitForTimeout(300);
await pg.keyboard.press('s'); await pg.waitForTimeout(300);
await pg.click('#skiubar [data-k="restA"]'); await pg.waitForTimeout(1500);
if (await pg.$('.skiuerr')) { console.log('אישור:', await pg.evaluate(() => document.querySelector('.skiuerr').textContent.slice(0, 80))); await pg.click('#skiubar [data-k="apply"]'); await pg.waitForTimeout(1500); }
decs = writes.filter((w) => w.p === '/sakem/dec').map((w) => JSON.parse(w.b)); last = decs[decs.length - 1] || {};
ok('קבל את כל השאר: נרשם כקבלת הכרטיס כפי שהוצע', last.act === 'accept', { act: last.act });
ok('אפס שגיאות בקונסול', !errs.length, errs.slice(0, 3));
await br.close();
process.exit(report.checks.every((c) => c.pass) ? 0 : 1);
