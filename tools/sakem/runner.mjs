/* סכם - כלי העבודה של המשימה המתוזמנת בענן (פרומפט 15, 28.10.2026).
   ההוראות המלאות: docs/sakem-runner.md. הכלי אינו קורא לשום מודל: הוא מכין את החומר לקריאה,
   בודק כל הצעה בשומר של סכם (tools/sakem_core.js - אותו שומר שבדף), ושומר התקדמות אחרי כל קטע.

   node tools/sakem/runner.mjs status                    התור ומצב כל עבודה
   node tools/sakem/runner.mjs next                      העבודה הבאה (או "התור ריק", קוד יציאה 3) והכנת חומר הקריאה
   node tools/sakem/runner.mjs rules                     כללי הניסוח, הדוגמאות והלקחים - לקרוא לפני הכתיבה
   node tools/sakem/runner.mjs orig  <jid> <from> <to>   נוסח הביניים של טווח יחידות (כפי שהדף יראה אותו)
   node tools/sakem/runner.mjs plan  <jid> <plan.json>   חלוקת הפרק לקטעים טבעיים (אחרי קריאת כל הסוגיה)
   node tools/sakem/runner.mjs put   <jid> <seg.json> [--push]   הצעה לקטע אחד, נבדקת ונשמרת מיד
   node tools/sakem/runner.mjs finish <jid> [--push]     סיום: "מוכן לסקירה"
   node tools/sakem/runner.mjs lessons                   הכרעות המנהל שטרם הופקו מהן לקחים
   node tools/sakem/runner.mjs lessons-done <jid>...     סימון שהלקחים מהן נכתבו ל-docs/sakem-lessons.md */
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const SKC = require(path.join(ROOT, 'tools', 'sakem_core.js'));
const D = path.join(ROOT, 'data', 'sakem');
const Q = path.join(D, 'queue'), O = path.join(D, 'out'), DEC = path.join(D, 'decisions');
const WORK = path.join(ROOT, '_work', 'sakem');
const rd = (f) => JSON.parse(fs.readFileSync(f, 'utf8'));
const wr = (f, o) => { fs.mkdirSync(path.dirname(f), { recursive: true }); fs.writeFileSync(f + '.tmp', JSON.stringify(o, null, 1) + '\n'); fs.renameSync(f + '.tmp', f); };
const die = (m, c = 1) => { console.log(m); process.exit(c); };
const strip = (h) => SKC.bare(h).replace(/[֑-ׇ]/g, '').replace(/\s+/g, ' ').trim();
const ls = (d) => (fs.existsSync(d) ? fs.readdirSync(d).filter((f) => f.endsWith('.json') && !f.endsWith('.old.json')).sort() : []);
const pkOf = (jid) => { const f = path.join(Q, jid + '.json'); if (!fs.existsSync(f)) die('אין עבודה כזאת בתור: ' + jid); return rd(f); };
const outF = (jid) => path.join(O, jid + '.json');
const outOf = (jid) => (fs.existsSync(outF(jid)) ? rd(outF(jid)) : null);
const TEXTK = (u) => u.k === 'u' || u.k === 'm';

function push(msg, files) {
  try {
    execFileSync('git', ['add', ...files], { cwd: ROOT, stdio: 'inherit' });
    execFileSync('git', ['commit', '-q', '-m', msg], { cwd: ROOT, stdio: 'inherit' });
  } catch (e) { console.log('(אין מה לשמור)'); return; }
  for (let i = 0; i < 4; i++) {
    // תמיד אל main במפורש: משימה בענן רצה לעתים על ענף צדדי, ואז ההצעות לא היו מגיעות לסנכרון.
    try { execFileSync('git', ['pull', '--rebase', '-q', 'origin', 'main'], { cwd: ROOT, stdio: 'inherit' }); execFileSync('git', ['push', '-q', 'origin', 'HEAD:main'], { cwd: ROOT, stdio: 'inherit' }); console.log('נשמר ונדחף.'); return; }
    catch (e) { try { execFileSync('git', ['rebase', '--abort'], { cwd: ROOT, stdio: 'ignore' }); } catch (_) {} console.log('דחיפה נכשלה, ניסיון חוזר…'); }
  }
  die('הדחיפה נכשלה ארבע פעמים - עצור, ההתקדמות שמורה במחשב בלבד.');
}

/* נוסח הביניים של כל יחידה, בהקשר הרצף (ציון דף, [גמרא] אחרי משנה, הפניה לגמרא) - כמו בדף */
function perUnit(units) {
  const out = [];
  let prev = 0;
  for (let i = 0; i < units.length; i++) {
    const L = SKC.toInter(units.slice(0, i + 1)).text.split('\n');
    out.push(L.slice(prev).join('\n'));
    prev = L.length;
  }
  return out;
}
function origOf(pk, from, to) {
  const a = pk.units.findIndex((u) => u.id === +from), b = pk.units.findIndex((u) => u.id === +to);
  if (a < 0 || b < 0 || b < a) die('טווח לא תקין: ' + from + '-' + to);
  return { text: SKC.toInter(pk.units.slice(a, b + 1)).text, ids: pk.units.slice(a, b + 1).map((u) => u.id), a, b };
}

const cmd = process.argv[2], A = process.argv.slice(3).filter((x) => x !== '--push'), PUSH = process.argv.includes('--push');

if (cmd === 'status') {
  const js = ls(Q);
  if (!js.length) die('התור ריק.', 0);
  js.forEach((f) => { const jid = f.slice(0, -5), pk = rd(path.join(Q, f)), o = outOf(jid);
    console.log(jid, '·', pk.title || '', '·', o ? (o.status === 'ready' ? 'מוכן לסקירה' : 'בעבודה ' + o.done + '/' + o.total) : 'ממתין'); });
} else if (cmd === 'next') {
  const jid = ls(Q).map((f) => f.slice(0, -5)).find((j) => { const o = outOf(j); return !o || o.status !== 'ready'; });
  if (!jid) die('התור ריק.', 3);
  const pk = pkOf(jid), o = outOf(jid);
  const dir = path.join(WORK, jid);
  fs.mkdirSync(dir, { recursive: true });
  /* א. לשון הגמרא ופירוש הגמרא, לפי דפים */
  let g = '# ' + (pk.title || jid) + ' - לשון הגמרא ופירוש הגמרא\n\n';
  (pk.pages || []).forEach((pg) => {
    g += '## דף ' + pg.daf + '\n\n';
    (pg.g || []).forEach((x, i) => { g += '[' + pg.daf + ' ' + (i + 1) + (pg.refs && pg.refs[i] ? ' · ' + pg.refs[i] : '') + '] ' + strip(x) + '\n'; if (pg.p && pg.p[i]) g += '   פירוש: ' + strip(pg.p[i]) + '\n'; });
    g += '\n';
  });
  fs.writeFileSync(path.join(dir, 'gemara.md'), g);
  /* ב. חברותא, לפי הצורך */
  let hv = '';
  Object.keys(pk.hv || {}).forEach((d) => { hv += '## דף ' + d + '\n' + pk.hv[d].map((s) => (s.g ? s.g + ' ' : '') + s.e).join('\n') + '\n\n'; });
  if (hv) fs.writeFileSync(path.join(dir, 'chavruta.md'), '# חברותא\n\n' + hv);
  /* ג. הלאוקמי גירסא של הפרק, יחידה-יחידה עם המזהה */
  const pu = perUnit(pk.units);
  let l = '# ' + (pk.title || jid) + ' - לאוקמי גירסא (פורמט הביניים)\n# כל יחידה פותחת ב-⟦מזהה⟧. החלוקה לקטעים (plan) היא לפי המזהים האלה.\n\n';
  pk.units.forEach((u, i) => { l += '⟦' + u.id + '⟧' + (TEXTK(u) ? '' : ' (כותרת / עיטור)') + '\n' + pu[i] + '\n'; });
  fs.writeFileSync(path.join(dir, 'leokmei.md'), l);
  console.log('העבודה:', jid, '·', pk.title || '');
  console.log('יחידות:', pk.units.length, '· דפים:', (pk.pages || []).map((p) => p.daf).join(' '));
  console.log('לקריאה:', path.relative(ROOT, dir) + '/{gemara.md, leokmei.md' + (hv ? ', chavruta.md' : '') + '}');
  if (o) console.log('המשך מהרצה קודמת: ' + o.done + ' מתוך ' + o.total + ' קטעים כבר נכתבו. הקטע הבא: ' + (o.plan.findIndex((s, i) => !o.items.some((x) => x.seg === i)) + 1));
  else console.log('טרם נכתבה חלוקה (plan).');
} else if (cmd === 'rules') {
  const src = fs.readFileSync(path.join(ROOT, 'worker', 'leokmei-suggest', 'src', 'sakem_prompt.js'), 'utf8');
  const sys = src.slice(src.indexOf('`') + 1, src.lastIndexOf('`')).replace(/\$\{SKC\.LINE\}/g, String(SKC.LINE)).replace(/\\\\n/g, '\\n');
  console.log('=== כללי הניסוח והמבנה של סכם (מקור: worker/leokmei-suggest/src/sakem_prompt.js) ===\n' + sys);
  const ex = rd(path.join(D, 'sakem-examples.json'));
  console.log('\n=== דוגמאות מתיקוני המחבר ===');
  (ex.pairs || []).forEach((p, i) => console.log('\n-- דוגמה ' + (i + 1) + ' (' + (p.kind || '') + ')\nלפני:\n' + p.before + '\nאחרי:\n' + p.after + (p.bad ? '\nפסול:\n' + p.bad : '') + '\nמה שיניתי: ' + (p.changes || []).join(' · ')));
  const L = path.join(ROOT, 'docs', 'sakem-lessons.md');
  if (fs.existsSync(L)) console.log('\n=== לקחים מהכרעות המנהל (גוברים על הכללים שלמעלה) ===\n' + fs.readFileSync(L, 'utf8'));
} else if (cmd === 'orig') {
  const [jid, from, to] = A;
  console.log(origOf(pkOf(jid), from, to).text);
} else if (cmd === 'plan') {
  const [jid, f] = A;
  const pk = pkOf(jid), plan = rd(f);
  if (!Array.isArray(plan) || !plan.length) die('plan צריך להיות מערך של {from,to,sugya,title}');
  /* כיסוי מלא ורציף של כל יחידות הטקסט, בלי חפיפה */
  let next = 0;
  const segs = plan.map((s, i) => {
    const r = origOf(pk, s.from, s.to);
    if (r.a !== next) die('קטע ' + (i + 1) + ' אינו מתחיל מיד אחרי הקודם (צפוי ⟦' + (pk.units[next] || {}).id + '⟧)');
    next = r.b + 1;
    return { from: +s.from, to: +s.to, sugya: +s.sugya || 0, title: String(s.title || '').slice(0, 80) };
  });
  if (next !== pk.units.length) die('החלוקה אינה מגיעה עד סוף הפרק (חסר מ-⟦' + pk.units[next].id + '⟧)');
  const old = outOf(jid);
  if (old && old.items.length) die('לעבודה הזאת כבר נכתבו קטעים - אין לשנות את החלוקה באמצע.');
  wr(outF(jid), { v: 1, jid, slug: pk.slug, title: pk.title || '', status: 'work', plan: segs, total: segs.length, done: 0, items: [], t: Date.now() });
  console.log('החלוקה נשמרה:', segs.length, 'קטעים.');
  if (PUSH) push('סכם: חלוקת ' + (pk.title || jid) + ' לקטעים', [outF(jid)]);
} else if (cmd === 'put') {
  const [jid, f] = A;
  const pk = pkOf(jid), o = outOf(jid), s = rd(f);
  if (!o) die('קודם plan.');
  const si = (+s.seg || 0) - 1, seg = o.plan[si];
  if (!seg) die('מספר קטע לא תקין (1 עד ' + o.plan.length + ')');
  const r = origOf(pk, seg.from, seg.to);
  o.items = o.items.filter((x) => x.seg !== si);
  if (s.nochange) {
    o.items.push({ iid: 's' + (si + 1), kind: 'seg', seg: si, sugya: seg.sugya, ids: r.ids, nochange: true });
  } else {
    const text = String(s.text || '').replace(/\r/g, '').trim();
    if (!text) die('אין text');
    const gem = (pk.pages || []).filter((p) => r.ids.some((id) => (pk.units.find((u) => u.id === id) || {}).daf === p.daf)).map((p) => (p.g || []).map(strip).join(' ')).join(' ');
    const ck = SKC.check(r.text, text, { gemara: gem });
    /* אורך: בסכם פרק השלמה מהגמרא, גזע שנכתב או מספור עשויים להאריך - אזהרה למנהל, לא חסימה */
    const LEN = /קצר מהמקור|ארוך מהמקור/;
    ck.warns = (ck.warns || []).concat(ck.errs.filter((e) => LEN.test(e)));
    ck.errs = ck.errs.filter((e) => !LEN.test(e));
    if (ck.errs.length) die('השומר דחה: ' + ck.errs.join(' · ') + '\nתקן והרץ שוב.');
    const adds = (Array.isArray(s.adds) ? s.adds : []).map((a) => ({ t: String(a.t || ''), gem: String(a.gem || '').slice(0, 600) }));
    const nAdd = SKC.parse(text).reduce((n, k) => n + ((k.v || '').match(/\{\+:/g) || []).length, 0);
    if (nAdd !== adds.length) die('מספר ההשלמות {+:...} בנוסח (' + nAdd + ') אינו כמספר הפריטים ב-adds (' + adds.length + '). לכל השלמה - לשון הגמרא שממנה נלקחה.');
    const layers = ['ליטוש'];
    if (s.skipped) layers.push('קיצור מרחבי');
    if (adds.length) layers.push('השלמה');
    o.items.push({ iid: 's' + (si + 1), kind: 'seg', seg: si, sugya: seg.sugya, ids: r.ids, orig: r.text, text, point: String(s.point || ''),
                   changes: (s.changes || []).map(String).slice(0, 6), layers, skipped: String(s.skipped || ''), adds, warn: ck.warns || [] });
  }
  /* חסר גדול מן הגמרא: פריט נפרד במקומו, אחרי הקטע */
  (Array.isArray(s.missing) ? s.missing : []).forEach((m, k) => {
    const anchor = +m.after || r.ids[r.ids.length - 1];
    if (r.ids.indexOf(anchor) < 0) die('missing.after חייב להיות מזהה בתוך הקטע');
    const text = String(m.text || '').replace(/\r/g, '').trim();
    const bad = []; SKC.parse(text).forEach((t) => { if (t.t === 'lock') bad.push('[' + t.kind + ']'); else SKC.i2h(t.v, true, bad); });
    if (!text || bad.length) die('חסר מהגמרא: נוסח לא תקין ' + bad.join(' '));
    o.items.push({ iid: 'm' + (si + 1) + '-' + (k + 1), kind: 'missing', seg: si, sugya: seg.sugya, ids: r.ids, anchor, gem: String(m.gem || '').slice(0, 1500), text, why: String(m.why || '') });
  });
  o.items.sort((a, b) => a.seg - b.seg || (a.kind === 'seg' ? -1 : 1));
  o.done = new Set(o.items.map((x) => x.seg)).size;
  o.t = Date.now();
  wr(outF(jid), o);
  const it = o.items.find((x) => x.seg === si && x.kind === 'seg');
  console.log('קטע ' + (si + 1) + ' נשמר' + (it.nochange ? ' (ללא שינוי)' : ' · ' + it.layers.join(', ') + (it.warn.length ? ' · אזהרות: ' + it.warn.join(' · ') : '')) + ' · ' + o.done + ' מתוך ' + o.total);
  if (PUSH) push('סכם: ' + (pk.title || jid) + ' - קטע ' + (si + 1) + ' מתוך ' + o.total, [outF(jid)]);
} else if (cmd === 'finish') {
  const [jid] = A;
  const pk = pkOf(jid), o = outOf(jid);
  if (!o) die('אין הצעות.');
  if (o.done < o.total) die('נכתבו ' + o.done + ' מתוך ' + o.total + ' - אי אפשר לסיים.');
  o.status = 'ready';
  o.t = Date.now();
  o.counts = { shown: o.items.filter((x) => !x.nochange).length, spatial: o.items.filter((x) => (x.layers || []).includes('קיצור מרחבי')).length,
               adds: o.items.reduce((n, x) => n + ((x.adds || []).length), 0), missing: o.items.filter((x) => x.kind === 'missing').length };
  wr(outF(jid), o);
  console.log('מוכן לסקירה:', JSON.stringify(o.counts));
  if (PUSH) push('סכם: ' + (pk.title || jid) + ' - מוכן לסקירה', [outF(jid)]);
} else if (cmd === 'lessons') {
  const stF = path.join(D, 'lessons-state.json'), st = fs.existsSync(stF) ? rd(stF) : { done: [] };
  const todo = ls(DEC).map((f) => f.slice(0, -5)).filter((j) => st.done.indexOf(j) < 0);
  if (!todo.length) die('אין הכרעות חדשות.', 0);
  todo.forEach((jid) => {
    const d = rd(path.join(DEC, jid + '.json'));
    const c = {}; (d.log || []).forEach((x) => { if (x.act === 'undo') return; (x.layers || ['?']).forEach((L) => { c[L] = c[L] || {}; c[L][x.act] = (c[L][x.act] || 0) + 1; }); });
    console.log('\n######## ' + jid + ' · ' + ((d.job || {}).title || '') + '\nסיכום לפי שכבה: ' + JSON.stringify(c));
    (d.log || []).filter((x) => x.act === 'reject' || x.act === 'edit').forEach((x) => {
      console.log('\n--- ' + x.iid + ' · ' + (x.act === 'edit' ? 'נערך' : 'נדחה') + ' · ' + (x.layers || []).join(', ') + '\nמקור:\n' + x.orig + '\nהצעה:\n' + x.prop + (x.final ? '\nמה שהמנהל כתב:\n' + x.final : '') + (x.gem ? '\nלשון הגמרא: ' + x.gem : ''));
    });
  });
  console.log('\nאחרי שכתבת את הלקחים: node tools/sakem/runner.mjs lessons-done ' + todo.join(' '));
} else if (cmd === 'lessons-done') {
  const stF = path.join(D, 'lessons-state.json'), st = fs.existsSync(stF) ? rd(stF) : { done: [] };
  st.done = [...new Set(st.done.concat(A))];
  wr(stF, st);
  console.log('סומן.');
  if (PUSH) push('סכם: לקחים מהכרעות המנהל', [stF, path.join(ROOT, 'docs', 'sakem-lessons.md')]);
} else {
  die('פקודה לא מוכרת. ראה docs/sakem-runner.md');
}
