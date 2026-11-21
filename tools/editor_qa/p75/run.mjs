/* פרומפט 75: בדיקת "סקירה פנימית" בדפדפן אמיתי, על האתר החי (leokmei.com), כמנהל מדומה.
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
const shot = async (n) => { if (!SHOTS) return; fs.mkdirSync(SHOTS, { recursive: true }); const f = path.join(SHOTS, (TOUCH || W) + '-' + n + '.png'); await pg.screenshot({ path: f }); report.shots.push(f); };
await shot('0-card');

/* הכפתור ליד העיפרון (במחשב) / בסרגל התחתון (במגע) */
const btn = await pg.evaluate(() => {
  const side = document.querySelector('.skmghost .skpside'), b = side && side.querySelector('.skiubtn'), ed = side && side.querySelector('[data-a="edit"]');
  const t = document.querySelector('.skmghost .skiuin');
  const vis = (e) => !!e && e.offsetParent !== null && getComputedStyle(e).display !== 'none';
  return { side: vis(b), afterEdit: !!(b && ed && ed.nextElementSibling === b), touch: vis(t), title: b ? b.title : (t ? t.title : '') };
});
ok('כפתור "סקירה פנימית" ' + (TOUCH ? 'בתחתית הכרטיס (במגע)' : 'מיד אחרי העיפרון'), TOUCH ? btn.touch : (btn.side && btn.afterEdit), btn);

/* כניסה: במחשב בקיצור S, במגע בנגיעה */
if (TOUCH) await pg.tap('.skmghost .skiuin'); else await pg.keyboard.press('s');
await pg.waitForTimeout(400);
let st = await pg.evaluate(() => window.skiuTest.state());
ok('מצב סקירה פנימית נפתח', !!st && st.n >= 10, st && { n: st.n, i: st.i });
await shot('1-inner');

/* תוכנית: קבל, דחה, ערוך אחד, וחוזר. יציאה באמצע וחזרה */
const N = st.n, plan = [];
for (let k = 0; k < N; k++) plan.push(k === 2 ? 'e' : k % 3 === 1 ? 'r' : 'a');
const press = async (a) => {
  if (TOUCH) { await pg.tap('#skiubar [data-k="' + a + '"]'); return; }
  await pg.keyboard.press(a === 'a' ? 'Enter' : a === 'r' ? "'" : 'e');
};
const times = [];
const half = Math.floor(N / 2);
let editedVal = '';
for (let k = 0; k < half; k++) {
  const t0 = Date.now();
  if (plan[k] === 'e') {
    await press('e'); await pg.waitForTimeout(150);
    const f = await pg.$('.skiufld');
    ok('עריכת יחידה: שדה נפתח במקום', !!f);
    if (f) {
      const v = await f.inputValue();
      editedVal = v.replace(/([א-ת]+)\s*$/, '$1 בדיקה');
      if (editedVal === v) editedVal = v + ' בדיקה';
      await f.fill(editedVal); await f.press('Enter');
    }
  } else await press(plan[k]);
  await pg.waitForTimeout(60);
  const s2 = await pg.evaluate(() => window.skiuTest.state());
  times.push(s2 ? s2.ms : -1);
  if (Date.now() - t0 > 2000) console.log('איטי', k);
}
st = await pg.evaluate(() => window.skiuTest.state());
ok('הכרעות ביחידות נרשמות ומעבר אוטומטי לבאה', st && st.done === half && st.i === half, st && { done: st.done, i: st.i });
ok('משוב חזותי מיידי (ציור מחדש של הכרטיס)', times.every((x) => x >= 0 && x < 100), 'מקסימום ' + Math.max(...times) + ' אלפיות');
const midText = st.text;
await shot('2-half');
/* אף כפתור אינו מכסה טקסט: הסרגל מתחת לכל שורת טקסט גלויה, והכפתורים שבצד אינם על הנוסח */
const cover = await pg.evaluate(() => {
  const bar = document.querySelector('#skiubar.fix') || document.querySelector('#skpbar'), br = bar.getBoundingClientRect();
  const cur = document.querySelector('.skiu.cur'), cr = cur ? cur.getBoundingClientRect() : null;
  const body = document.querySelector('.skmghost .skmbody').getBoundingClientRect();
  const side = [...document.querySelectorAll('.skmghost .skpside button')].filter((b) => b.offsetParent).map((b) => b.getBoundingClientRect());
  const overlapBody = side.some((r) => r.left < body.right && r.right > body.left && r.top < body.bottom && r.bottom > body.top);
  const padOk = parseFloat(getComputedStyle(document.body).paddingBottom) >= br.height;
  return { curAbove: cr ? cr.bottom <= br.top + 1 : null, overlapBody, padOk, bar: Math.round(br.height) };
});
ok('אף כפתור אינו מכסה טקסט', cover.curAbove !== false && !cover.overlapBody && cover.padOk, cover);

/* יציאה באמצע (Esc / הכפתור) וחזרה */
if (TOUCH) await pg.tap('#skiubar [data-k="exit"]'); else await pg.keyboard.press('Escape');
await pg.waitForTimeout(400);
const off = await pg.evaluate(() => ({ st: window.skiuTest.state(), badge: (document.querySelector('.skiuin .skiubdg') || {}).textContent || '' }));
ok('יציאה באמצע: חוזרים לכרטיס הרגיל', off.st === null);
if (TOUCH) { await pg.waitForTimeout(600); const b74 = await pg.evaluate(() => { const b = document.getElementById('tchbar'); return !!b && getComputedStyle(b).display !== 'none' && !b.hidden && [...b.querySelectorAll('button')].map((x) => x.dataset.a).join(','); }); ok('במגע: אחרי היציאה הסרגל של 74 חוזר כמו שהיה', !!b74, b74); }
if (TOUCH) await pg.tap('.skmghost .skiuin'); else await pg.keyboard.press('s');
await pg.waitForTimeout(400);
st = await pg.evaluate(() => window.skiuTest.state());
ok('חזרה: ההכרעות נשמרו וממשיכים מאותו מקום', st && st.done === half && st.text === midText && st.i === half, st && { done: st.done, i: st.i });
/* גם אחרי רענון הדף (טיוטה במכשיר) */
await pg.reload({ waitUntil: 'load' }); await pg.waitForTimeout(3500);
await pg.evaluate(async (jid) => { if (!EDIT) setEdit(true); await new Promise((r) => setTimeout(r, 600)); window.skpAuto.open(jid); for (let k = 0; k < 40 && !(SKP.rev && SKM.ghost); k++) await new Promise((r) => setTimeout(r, 250)); }, opened.jid);
if (TOUCH) await pg.tap('.skmghost .skiuin'); else await pg.keyboard.press('s');
await pg.waitForTimeout(400);
st = await pg.evaluate(() => window.skiuTest.state());
ok('אחרי רענון הדף: הטיוטה נשמרה', st && st.done === half && st.text === midText, st && { done: st.done });

/* הקודם/הבא לא מכריעים */
if (!TOUCH) { await pg.keyboard.press('ArrowRight'); await pg.keyboard.press('ArrowLeft'); }
st = await pg.evaluate(() => window.skiuTest.state());
ok('הקודם/הבא אינם מכריעים', st.done === half && st.i === half, { i: st.i });
if (TOUCH) {
  const t74 = await pg.evaluate(() => { const b = document.getElementById('tchbar'); return { hidden74: !b || getComputedStyle(b).display === 'none', mine: !!document.querySelector('#skiubar.fix') }; });
  ok('במגע: הסרגל של 74 מתחלף בסרגל היחידות', t74.hidden74 && t74.mine, t74);
  const cdp = await ctx.newCDPSession(pg);
  const sw = async (x0, x1, y) => { await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: x0, y }] }); for (let k = 1; k <= 6; k++) await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: x0 + (x1 - x0) * k / 6, y }] }); await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] }); await pg.waitForTimeout(250); };
  const vp = pg.viewportSize(); const y = Math.round(vp.height * 0.4);
  const before = (await pg.evaluate(() => window.skiuTest.state())).i;
  await sw(200, 450, y);
  const a1 = await pg.evaluate(() => ({ s: window.skiuTest.state(), rev: SKP.rev ? SKP.rev.i : -1 }));
  await sw(450, 200, y);
  const a2 = await pg.evaluate(() => window.skiuTest.state());
  ok('במגע: החלקה עוברת יחידה (לא כרטיס) ואינה מכריעה', a1.s && a1.s.i === (before + 1) % a1.s.n && a2.i === before && a2.done === half, { before, after: a1.s && a1.s.i, back: a2.i });
}
/* Delete אינו דוחה */
if (!TOUCH) { await pg.keyboard.press('Delete'); st = await pg.evaluate(() => window.skiuTest.state()); ok('Delete אינו דוחה', st.done === half); }

/* השאר: לפי התוכנית, האחרונה מחילה את הכרטיס */
const wantDec = {};
for (let k = half; k < N; k++) {
  if (plan[k] === 'e') { await press('e'); const f = await pg.$('.skiufld'); const v = await f.inputValue(); editedVal = v + ' בדיקה'; await f.fill(editedVal); await f.press('Enter'); }
  else await press(plan[k]);
  await pg.waitForTimeout(80);
  if (k === N - 2) { const s3 = await pg.evaluate(() => window.skiuTest.state()); if (s3) Object.assign(wantDec, s3); }
}
await pg.waitForTimeout(1500);
/* אישור שורה שננעלה בהדפסה ("לחץ שוב") - כמו בקבלה הרגילה */
if (await pg.evaluate(() => /לחץ שוב/.test((document.querySelector('.skiuerr') || {}).textContent || ''))) { console.log('אישור נעילת הדפסה'); if (TOUCH) await pg.tap('#skiubar [data-k="apply"]'); else await pg.click('#skiubar [data-k="apply"]'); await pg.waitForTimeout(1500); }
const fin = await pg.evaluate(() => ({ st: window.skiuTest.state(), rev: SKP.rev ? { i: SKP.rev.i, cnt: SKP.rev.cnt } : null, toast: (document.getElementById('skpalltoast') || {}).textContent || '', err: (document.querySelector('.skiuerr') || {}).textContent || '', flash: (document.getElementById('flash') || document.querySelector('.flash') || {}).textContent || '' }));
ok('אחרי ההכרעה האחרונה הכרטיס הוחל כהכרעה אחת, עם "בטל"', fin.st === null && /בטל/.test(fin.toast), fin.toast || fin.err);
await shot('3-applied');
/* הנוסח בדף (ובשכבת העריכות) = התוצאה המעורבת בדיוק */
const decs = writes.filter((w) => w.p === '/sakem/dec').map((w) => JSON.parse(w.b));
const last = decs[decs.length - 1] || {};
const expect = (() => { const M = SKU.units(opened.it.orig, opened.it.text); const V = M.u.filter((u) => !u.quiet); const d = {}; V.forEach((u, k) => { d[u.id] = plan[k] === 'e' ? null : plan[k]; }); return { M, V, d }; })();
ok('ההכרעה נשלחה לשרת כעריכה (נוסח מעורב) ונרשמת ליומן הלמידה', last.act === 'edit' && last.final && last.final !== last.prop, { act: last.act, iid: last.iid });
if (last.final) {
  const C = SKU.classify(opened.it.orig, opened.it.text, last.final);
  const got = C.map((c) => c.dec[0]).join(''), want = expect.V.map((u, k) => plan[k] === 'e' ? 'e' : plan[k]).join('');
  ok('שחזור ההכרעות ליחידות מן היומן (הלמידה)', got === want, { got, want });
}
const page = await pg.evaluate(() => flatU().map((o) => { try { return skmInter([o]); } catch (e) { return ''; } }).join('\n'));
const norm = (s) => SKC_norm(s);
function SKC_norm(s) { return String(s || '').replace(/\[(דף|משנה|גמרא|קבוע|מקור)[^\]]*\]/g, '').replace(/[^א-ת\n]/g, ''); }
const flat = (x) => norm(x).replace(/\n/g, '');
const wasOrig = flat(page).includes(flat(opened.it.orig)), wasProp = flat(page).includes(flat(opened.it.text));
ok('הנוסח בדף הוא התוצאה המעורבת (לא המקור ולא ההצעה)', last.final && flat(page).includes(flat(last.final)) && !wasProp, { inPage: flat(page).includes(flat(last.final)), orig: wasOrig, prop: wasProp });
const edPub = await pg.evaluate(() => { try { return (typeof ED !== 'undefined' ? ED : []).filter((e) => e.t > Date.now() - 600000).length; } catch (e) { return -1; } });
ok('העריכה נרשמה בשכבת העריכות (לפרסום ולוורד)', edPub > 0, { recs: edPub });
ok('אפס שגיאות בקונסול', !errs.length, errs.slice(0, 3));
fs.writeFileSync(path.join(SHOTS || '/tmp', 'p75-' + (TOUCH || W) + '.json'), JSON.stringify({ report, card: { jid: opened.jid, iid: opened.it.iid, n: N }, writes: writes.length }, null, 1));
await br.close();
process.exit(report.checks.every((c) => c.pass) ? 0 : 1);
