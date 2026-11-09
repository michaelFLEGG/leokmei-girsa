/* סכם - כלי העבודה של המשימה המתוזמנת בענן (פרומפט 15, 28.10.2026).
   ההוראות המלאות: docs/sakem-runner.md. הכלי אינו קורא לשום מודל: הוא מכין את החומר לקריאה,
   בודק כל הצעה בשומר של סכם (tools/sakem_core.js - אותו שומר שבדף), ושומר התקדמות אחרי כל קטע.

   node tools/sakem/runner.mjs status                    התור ומצב כל עבודה
   node tools/sakem/runner.mjs next [jid]                העבודה הבאה (או עבודה מסוימת) (או "התור ריק", קוד יציאה 3) והכנת חומר הקריאה
   node tools/sakem/runner.mjs rules                     כללי הניסוח, הדוגמאות והלקחים - לקרוא לפני הכתיבה
   node tools/sakem/runner.mjs orig  <jid> <from> <to>   נוסח הביניים של טווח יחידות (כפי שהדף יראה אותו)
   node tools/sakem/runner.mjs plan  <jid> <plan.json>   חלוקת הפרק לקטעים טבעיים (אחרי קריאת כל הסוגיה)
   node tools/sakem/runner.mjs put   <jid> <seg.json> [--push]   הצעה לקטע אחד, נבדקת ונשמרת מיד
   node tools/sakem/runner.mjs finish <jid> [--push]     סיום: "מוכן לסקירה" (בודק שאין חוסמות, כרטיס ציון, יומן ההרצות)
   node tools/sakem/runner.mjs pause  <jid> [--push]     סוף הרצה באמצע פרק (חצי ראשון של פרק ארוך) - שורה ביומן ההרצות
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

/* פרומפט 17: פירוש הגמרא וחברותא אינם בחבילה שבריפו הציבורי. הכלי מושך אותם בשעת העבודה אל _work/sakem,
   שאינו נשמר במאגר: במשימה בענן משכפול הריפו הפרטי (אין שם מפתח), ובמחשב במפתח המנהל.
   בלי אף אחד מהם - העבודה ממשיכה על לשון הגמרא, ונאמרת בקול. */
const API = process.env.LG_API || 'https://leokmei-suggest.m7654301.workers.dev';
function adminKey() {
  if (process.env.LEOKMEI_ADMIN_KEY) return process.env.LEOKMEI_ADMIN_KEY;
  if (process.env.LG_ADMIN_KEY) return process.env.LG_ADMIN_KEY;
  const f = 'C:\\Users\\Owner\\Documents\\לאוקמי-מפתח-מנהל.txt';
  if (!fs.existsSync(f)) return '';
  const ls2 = fs.readFileSync(f, 'utf8').replace(/^\uFEFF/, '').split(/\r?\n/).map((l) => l.trim()).filter((l) => /^[\x21-\x7e]{16,}$/.test(l));
  return ls2.length ? ls2[ls2.length - 1] : '';
}
const GEM = { א: 1, ב: 2, ג: 3, ד: 4, ה: 5, ו: 6, ז: 7, ח: 8, ט: 9, י: 10, כ: 20, ל: 30, מ: 40, נ: 50, ס: 60, ע: 70, פ: 80, צ: 90, ק: 100, ר: 200, ש: 300, ת: 400 };
const dafKey = (d) => { let n = 0; for (const c of String(d).replace(/[^א-ת]/g, '')) n += GEM[c] || 0; return n ? n * 2 + (/:\s*$/.test(d) ? 1 : 0) : null; };
const CHAV = [process.env.LK_CHAVRUTA, path.join(ROOT, '..', 'leokmei-chavruta')].find((d) => d && fs.existsSync(path.join(d, '.git')));
function chavShow(ref, p) {
  try { return execFileSync('git', ['-C', CHAV, 'show', ref + ':' + p], { encoding: 'utf8', maxBuffer: 1 << 29, stdio: ['ignore', 'pipe', 'ignore'] }); }
  catch (e) { return null; }
}
function chavCtx(pk) {
  const out = { per: {}, hv: {}, warn: '' };
  const txt = chavShow('origin/perush-store', 'perush/' + pk.slug + '.json');
  if (txt) out.per = JSON.parse(txt);
  else out.warn = 'פירוש הגמרא לא נמצא בריפו הפרטי (ענף perush-store).';
  for (const pg of pk.pages || []) {
    const name = String(pg.daf).replace(/[^א-ת]/g, '') + (/:\s*$/.test(pg.daf) ? 'ב' : 'א');
    const t = chavShow('origin/main', 'packs/' + pk.slug + '/' + name + '.json');
    if (!t) continue;
    const segs = JSON.parse(t).segs || [];
    out.hv[pg.daf] = segs.map((s) => ({ p: s.para, g: s.gemara || '', e: String(s.explain || '').replace(/\[\[הערה:\d+\]\]/g, '') }));
  }
  return out;
}
async function privateCtx(pk) {
  if (CHAV) return chavCtx(pk);
  const key = adminKey();
  if (!key) return { per: {}, hv: {}, warn: 'אין כאן גישה לריפו הפרטי ואין מפתח מנהל, ולכן פירוש הגמרא וחברותא לא נמשכו. העבודה נעשית על לשון הגמרא בלבד.' };
  const h = { 'x-admin-key': key };
  const out = { per: {}, hv: {}, warn: '' };
  try {
    const r = await fetch(API + '/perush/masechet?slug=' + pk.slug, { headers: h });
    if (r.ok) out.per = await r.json();
    else if (r.status !== 404) out.warn = 'פירוש הגמרא לא נמשך (' + r.status + ').';
    for (const pg of pk.pages || []) {
      const n = dafKey(pg.daf);
      if (n === null) continue;
      const q = await fetch(API + '/hv/page?slug=' + pk.slug + '&daf=' + encodeURIComponent(pg.daf) + '&c=' + Math.floor(n / 12), { headers: h });
      const j = q.ok ? await q.json() : null;
      if (j && j.page && j.page.segs) out.hv[pg.daf] = j.page.segs.map((s) => ({ p: s.p, g: s.g || '', e: String(s.e || '').replace(/\[\[הערה:\d+\]\]/g, '') }));
    }
  } catch (e) { out.warn = 'פירוש הגמרא וחברותא לא נמשכו: ' + e.message; }
  return out;
}

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
function mishnaOf(pk) {
  try {
    const f = path.join(ROOT, 'data', 'mishna', pk.slug + '.json');
    const m = rd(f), n = +((pk.job && pk.job.perek) || pk.perek || 0);
    const ch = (m.chapters || [])[n - 1];
    return ch ? ch.join(' ') : '';
  } catch (e) { return ''; }
}
function origOf(pk, from, to) {
  const a = pk.units.findIndex((u) => u.id === +from), b = pk.units.findIndex((u) => u.id === +to);
  if (a < 0 || b < 0 || b < a) die('טווח לא תקין: ' + from + '-' + to);
  return { text: SKC.toInter(pk.units.slice(a, b + 1)).text, ids: pk.units.slice(a, b + 1).map((u) => u.id), a, b };
}

/* ---- פרומפט 29 (9.11.2026): הקשר הקטע לבודק, הרצה פרק לפרק, ויומן העלות ----
   ctxOf: מזהי העיטורים בקטע, מזהי פתיחת הפרק (עיטור שצמוד להם נמחק), כמה יחידות בקטע נפתחות בלי כותרת
   (שם חובה (רווח)), והנוסח שלפני הקטע ואחריו (עיטור בקצה הקטע שהכותרת שלו בקטע הסמוך) */
function ctxOf(pk, r) {
  const U = pk.units, set = new Set(r.ids);
  const hatz = U.filter((u) => set.has(u.id) && u.k === 'hatz').map((u) => u.id);
  const heads = U.filter((u) => /^perek-(start|range)$/.test(u.k)).map((u) => u.id);
  let unitOpen = 0;
  U.forEach((u, i) => {
    if (!set.has(u.id) || u.k !== 'u' || SKC.bare(u.a || '').trim()) return;
    const p = U[i - 1]; if (!p || p.k !== 'u') return;
    /* יחידה שפותחת במספור או במקף (המשך רשימה, תירוץ) אינה פתיחה חדשה */
    const f = SKC.plainI(SKC.h2i(((u.l || [])[0] || [])[1] || '')).trim();
    if (/^-|^(?:[יכלמ]?[א-ט]|[יכלמ])\.\s/.test(f)) return;
    unitOpen++;
  });
  const before = SKC.toInter(U.slice(Math.max(0, r.a - 2), r.a)).text, after = SKC.toInter(U.slice(r.b + 1, r.b + 3)).text;
  return { hatz, heads, unitOpen, before, after };
}
/* פרק ארוך (מעל 30 קטעים) - שתי הרצות: החצי הראשון עד H (לא כולל) */
const HALF_MIN = 30;
const halfOf = (o) => (o && o.total > HALF_MIN ? Math.ceil(o.total / 2) : 0);
/* מצב ההרצה הנוכחית - מקומי בלבד (_work אינו במאגר): כל הרצה של המשימה היא שיחה חדשה ושכפול חדש */
const runF = (jid) => path.join(WORK, jid, 'run.json');
const runState = (jid) => (fs.existsSync(runF(jid)) ? rd(runF(jid)) : {});
const saveRun = (jid, s) => wr(runF(jid), s);
const RUNS = path.join(D, 'runs.jsonl');
/* סימון ההרצה (מקומי): על איזו עבודה ההרצה הזאת עובדת. כל הרצה של המשימה היא שכפול חדש, ולכן אין סימון.
   במחשב המקומי _work נשמר - סימון בן יותר משלוש שעות אינו נחשב, ו-next --new-run מאפס אותו */
const MARK = path.join(WORK, '.run.json');
const runMark = () => { try { const m = rd(MARK); return Date.now() - (m.t || 0) < 3 * 3600e3 ? m : null; } catch (e) { return null; } };
/* שורה ביומן ההרצות: פרק, חלק, קטעים, יחידות, אורך המקור, התחלה וסיום - להערכת העלות לפרק */
function logRun(jid, pk, o, how) {
  const rs = runState(jid);
  const units = pk.units.length, origLen = SKC.plainI(SKC.toInter(pk.units).text).replace(/\s+/g, '').length;
  const rec = { jid, slug: pk.slug, perek: +((pk.job && pk.job.perek) || pk.perek || 0) || null, title: pk.title || '', part: rs.part ? rs.part + '/2' : 'כולו',
    segs: o.total, segsThisRun: o.done - (rs.done0 || 0), units, origLen, start: rs.t0 ? new Date(rs.t0).toISOString() : null, end: new Date().toISOString(), how };
  if (rs.t0) rec.minutes = Math.round((Date.now() - rs.t0) / 6000) / 10;
  fs.mkdirSync(D, { recursive: true });
  fs.appendFileSync(RUNS, JSON.stringify(rec) + '\n');
  rs.logged = 1; saveRun(jid, rs);
  /* ההרצה הסתיימה (פרק אחד, או חצי) - next הבא באותה הרצה אומר "התור ריק" */
  const m = runMark(); if (m) { m.stopped = Date.now(); wr(MARK, m); }
  return rec;
}

const cmd = process.argv[2], A = process.argv.slice(3).filter((x) => !/^--/.test(x)), PUSH = process.argv.includes('--push'), DRY = process.argv.includes('--dry');

if (cmd === 'status') {
  const js = ls(Q);
  if (!js.length) die('התור ריק.', 0);
  js.forEach((f) => { const jid = f.slice(0, -5), pk = rd(path.join(Q, f)), o = outOf(jid);
    console.log(jid, '·', pk.title || '', '·', o ? (o.status === 'ready' ? 'מוכן לסקירה' : 'בעבודה ' + o.done + '/' + o.total) : 'ממתין'); });
} else if (cmd === 'next') {
  /* next <jid>: עבודה מסוימת (כמה עובדים במקביל, כל אחד על פרק אחר; 6.11.2026) */
  const jid = ls(Q).map((f) => f.slice(0, -5)).find((j) => { const o = outOf(j); return (!A[0] || j === A[0]) && (!o || o.status !== 'ready'); });
  if (!jid) die('התור ריק.', 3);
  /* פרומפט 29: פרק אחד בכל הרצה, בהקשר נקי */
  if (process.argv.includes('--new-run')) { try { fs.unlinkSync(MARK); } catch (e) {} }
  { const m = runMark();
    if (m && (m.stopped || m.jid !== jid)) die('התור ריק להרצה הזאת: כבר עובד בה ' + m.jid + (m.stopped ? ' (הסתיים או נעצר בסוף חצי)' : '') + '. פרק אחד בכל הרצה - צא; ההמשך בהרצה הבאה, בשיחה חדשה.', 3);
    if (!m) { wr(MARK, { jid, t: Date.now() }); try { fs.unlinkSync(runF(jid)); } catch (e) {} } }
  const pk = pkOf(jid), o = outOf(jid);
  const dir = path.join(WORK, jid);
  fs.mkdirSync(dir, { recursive: true });
  /* א. לשון הגמרא ופירוש הגמרא, לפי דפים */
  const prv = await privateCtx(pk);
  if (prv.warn) console.log('אזהרה: ' + prv.warn);
  let g = '# ' + (pk.title || jid) + ' - לשון הגמרא ופירוש הגמרא\n\n' + (prv.warn ? '(' + prv.warn + ')\n\n' : '');
  (pk.pages || []).forEach((pg) => {
    g += '## דף ' + pg.daf + '\n\n';
    (pg.g || []).forEach((x, i) => { g += '[' + pg.daf + ' ' + (i + 1) + (pg.refs && pg.refs[i] ? ' · ' + pg.refs[i] : '') + '] ' + strip(x) + '\n'; const ps = prv.per[pg.daf]; if (ps && ps[i]) g += '   פירוש: ' + strip(ps[i]) + '\n'; });
    g += '\n';
  });
  fs.writeFileSync(path.join(dir, 'gemara.md'), g);
  /* ב. חברותא, לפי הצורך */
  let hv = '';
  Object.keys(prv.hv).forEach((d) => { hv += '## דף ' + d + '\n' + prv.hv[d].map((s) => (s.g ? s.g + ' ' : '') + s.e).join('\n') + '\n\n'; });
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
  /* פרומפט 29: פרק אחד בכל הרצה; פרק מעל 30 קטעים - חצי בכל הרצה */
  if (!fs.existsSync(runF(jid))) saveRun(jid, { t0: Date.now(), done0: o ? o.done : 0 });
  const H = halfOf(o);
  if (H) { const nx = o.plan.findIndex((s, i) => !o.items.some((x) => x.seg === i));
    console.log('פרק ארוך (' + o.total + ' קטעים): בהרצה הזאת רק ' + (nx < H ? 'החצי הראשון - קטעים 1 עד ' + H : 'החצי השני - קטעים ' + (H + 1) + ' עד ' + o.total) + '. בסוף החצי: pause וצא.'); }
  console.log('פרק אחד בהרצה: אחרי finish (או pause בסוף חצי) - צא. הפרק הבא בהרצה הבאה, בשיחה חדשה.');
} else if (cmd === 'rules') {
  const src = fs.readFileSync(path.join(ROOT, 'worker', 'leokmei-suggest', 'src', 'sakem_prompt.js'), 'utf8');
  const sys = src.slice(src.indexOf('`') + 1, src.lastIndexOf('`')).replace(/\$\{SKC\.LINE\}/g, String(SKC.LINE)).replace(/\\\\n/g, '\\n');
  console.log('=== כללי הניסוח והמבנה של סכם (מקור: worker/leokmei-suggest/src/sakem_prompt.js) ===\n' + sys);
  const ex = rd(path.join(D, 'sakem-examples.json'));
  console.log('\n=== דוגמאות מתיקוני המחבר ===');
  (ex.pairs || []).forEach((p, i) => console.log('\n-- דוגמה ' + (i + 1) + ' (' + (p.kind || '') + ')\nלפני:\n' + p.before + '\nאחרי:\n' + p.after + (p.bad ? '\nפסול:\n' + p.bad : '') + '\nמה שיניתי: ' + (p.changes || []).join(' · ')));
  const L = path.join(ROOT, 'docs', 'sakem-lessons.md');
  if (fs.existsSync(L)) console.log('\n=== לקחים מהכרעות המנהל (גוברים על הכללים שלמעלה) ===\n' + fs.readFileSync(L, 'utf8'));
  /* המקליט (פרומפט 28): כללים שנלמדו מעריכות המנהל ומהערותיו; כלל שבוטל ב"מה סכם למד" אינו מוצג */
  const LR = path.join(D, 'learn', 'rules.json');
  if (fs.existsSync(LR)) { const on = (rd(LR).rules || []).filter((x) => !x.off);
    if (on.length) console.log('\n=== מה סכם למד מעריכות המנהל (' + on.length + ' כללים פעילים) ===\n' + on.map((x) => '- ' + x.text + (x.was && x.kind !== 'החלפת מילה' ? '\n  לפני: ' + x.was + '\n  אחרי: ' + x.now : '')).join('\n')); }
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
  /* פרומפט עבודה גרסה 2: לשון המשניות של הפרק (data/mishna), לבדיקת תיבת המשנה; ו"ללא שינוי" אינו מותר כשהנוסח הקיים פגום */
  const mishna = mishnaOf(pk);
  /* פרומפט 29: חצי פרק בכל הרצה (פרק מעל 30 קטעים) - קטע מן החצי האחר נדחה עד ההרצה הבאה */
  { const m = runMark(); if (m && m.jid !== jid) die('ההרצה הזאת עובדת על ' + m.jid + ' - פרק אחד בכל הרצה. צא.'); if (m && m.stopped) die('ההרצה הזאת כבר הסתיימה (finish / pause) - צא. ההמשך בהרצה הבאה.'); }
  const rs = runState(jid), H = halfOf(o);
  if (H) { const part = si < H ? 1 : 2; if (!rs.part) { rs.part = part; saveRun(jid, rs); }
    else if (rs.part !== part) die('הקטע ' + (si + 1) + ' שייך לחצי ' + (part === 1 ? 'הראשון' : 'השני') + ' של הפרק, וההרצה הזאת עובדת על החצי ' + (rs.part === 1 ? 'הראשון' : 'השני') + '.\nסיים את ההרצה (node tools/sakem/runner.mjs pause ' + jid + ' --push) וצא. החצי האחר - בהרצה הבאה, בשיחה חדשה.'); }
  const cx = ctxOf(pk, r);
  if (s.nochange) {
    const q0 = SKC.quality(r.text, { mishna });
    if (q0.length) die('אי אפשר "ללא שינוי": הנוסח הקיים פגום - ' + q0.slice(0, 6).join(' · ') + '\nתקן בהצעה.');
    /* פרומפט 28: גם "ללא שינוי" עובר את בודק הציות (משנה בלי הדגשת עיקר); פרומפט 29: במצב המשימה (עיטור, רווח, מקף) */
    const c0 = SKC.comply(r.text, r.text, Object.assign({ strict: true, keep: s.keep }, cx));
    if (c0.errs.length) die('אי אפשר "ללא שינוי": ' + c0.errs.join(' · ') + '\nתקן בהצעה.');
    if (DRY) { console.log('השומר: עבר (ללא שינוי). לא נשמר דבר (--dry).'); process.exit(0); }
    o.items.push({ iid: 's' + (si + 1), kind: 'seg', seg: si, sugya: seg.sugya, ids: r.ids, nochange: true, stat: c0.stat });
  } else {
    let text = String(s.text || '').replace(/\r/g, '').trim();
    if (!text) die('אין text');
    /* פרומפט 22: כותרת צד ארוכה וכפילות ברורה אחרי כותרת - תיקון אוטומטי לפני השומר */
    { const af = SKC.autofixTitles(text); if (af.changed) { text = af.text; s.changes = (s.changes || []).concat(af.notes.map((x) => 'אוטומטי: ' + x)); } }
    /* פרומפט 28 (9.11.2026): כללי צורה של בעל הפרויקט, בקוד ולא רק בהנחיה - דובר בפתח שורה לכותרת צד, אות ומילה
       נסמכות לשם בסגנון האמורא, רווח לפני גופא / ת"ר / אמר מר. אינם משנים מילה בנוסח */
    { const ff = SKC.autofixForm(text); if (ff.changed) { text = ff.text; s.changes = (s.changes || []).concat(ff.notes.map((x) => 'אוטומטי: ' + x)); } }
    const gem = (pk.pages || []).filter((p) => r.ids.some((id) => (pk.units.find((u) => u.id === id) || {}).daf === p.daf)).map((p) => (p.g || []).map(strip).join(' ')).join(' ');
    /* הקשר המספור (6.11.2026): רשימה שהתחילה לפני הקטע או נמשכת אחריו. בקטע הראשון של הפרק - הרשימה עשויה
       להתחיל בפרק הקודם (סוכה ה, "ב. ג." אחרי "א." של פרק ד): אז ההקשר הוא המספר שהנוסח המקורי פותח בו */
    let before = SKC.toInter(pk.units.slice(Math.max(0, r.a - 3), r.a)).text;
    const after = SKC.toInter(pk.units.slice(r.b + 1, r.b + 4)).text;
    const n0 = (SKC.nums(r.text) || [])[0] || 0;
    if (r.a === 0 && n0 > 1) before = 'אבגדהוזחטי'[n0 - 2] + '. ';
    /* פרומפט 27 (8.11.2026): עיטור צמוד לכותרת נמחק - [מחק-עיטור:<מזהה>] במקום [קבוע:<מזהה>]. רק עיטור, ורק ליד כותרת */
    const hd = SKC.hatzDel(r.text, text);
    if (hd.bad.length) die('עיטור למחיקה שאינו בקטע: ' + hd.bad.join(', '));
    for (const id of hd.ids) {
      const u = pk.units.find((x) => x.id === id);
      if (!u || u.k !== 'hatz') die('[מחק-עיטור:' + id + '] - מותר רק לעיטור (לא פתיחת פרק, לא הדרן)');
      if (!SKC.hatzNearHead([cx.before, text, cx.after].join('\n'), id, { heads: cx.heads, hatz: cx.hatz })) die('[מחק-עיטור:' + id + '] - מותר רק לעיטור שצמוד לכותרת נושא, ד"ה, משנה או פתיחת פרק');
    }
    const rT = hd.orig, tT = hd.text;
    /* מקף תירוץ שנמחק ביודעין (השורה כולה נמחקה) - רק כשנרשם ב-changes, עם הכותרת עצמה */
    const dropDash = SKC.dashLost(rT, tT).filter((x) => (s.changes || []).some((c) => /מקף/.test(c) && String(c).indexOf(x.replace(/^-\s*/, '')) > -1));
    const ck = SKC.check(rT, tT, { gemara: gem, mishna, before, after, dropDash });
    /* בודק הציות (פרומפט 28): הדגשת עיקר המשנה, הדגשה ומקף שלא נעלמו - חוסם.
       פרומפט 29 (strict): גם עיטור שמותר למחוק ולא נמחק, רווח חסר, מקף תירוץ חסר (אלא בנימוק ב-keep), שורה אלמנה,
       כותרת צד חדשה של יותר משתי מילים, ופתיחת ראשי תיבות שמאריכה כותרת או גולשת לשורה נוספת - חוסמים */
    const hatzIds = cx.hatz.filter((id) => !hd.ids.includes(id));
    const cp = SKC.comply(rT, tT, Object.assign({}, cx, { strict: true, keep: s.keep, changes: s.changes, hatz: hatzIds, hatzDel: hd.ids.length }));
    ck.errs = ck.errs.concat(cp.errs);
    ck.warns = (ck.warns || []).concat(cp.warns.map((x) => 'ציות: ' + x));
    /* אורך: בסכם פרק השלמה מהגמרא, גזע שנכתב או מספור עשויים להאריך - אזהרה למנהל, לא חסימה */
    const LEN = /קצר מהמקור|ארוך מהמקור/;
    ck.warns = (ck.warns || []).concat(ck.errs.filter((e) => LEN.test(e)));
    ck.errs = ck.errs.filter((e) => !LEN.test(e));
    if (ck.errs.length) die('השומר דחה: ' + ck.errs.join(' · ') + '\nתקן והרץ שוב.');
    /* פרומפט 26 (8.11.2026): הידוק יתר - קורא נפרד. שורה שקוצצה ביותר מחצי (או קטע שירד מתחת ל-65%) נשלחת
       לקורא שאינו רואה את המקור ולא את הגמרא (סוכן-משנה נפרד בהקשר נקי), והוא כותב במשפט מה השורה אומרת.
       seg.json: "read": [{"line": "<השורה כפי שבהצעה>", "said": "<מה הקורא הבין>", "ok": true|false}].
       ok=false (לא הבין, או הבין אחרת מן המקור) - כותבים את השורה מחדש בפחות הידוק. */
    const sq = SKC.squeeze(rT, tT);
    /* --dry (פרומפט 26): בדיקה בלבד, בלי לשמור - לכותבים שעובדים במקביל על קטעים של אותו פרק */
    if (DRY) {
      const nAdd0 = SKC.parse(text).reduce((n, k) => n + ((k.v || '').match(/\{\+:/g) || []).length, 0);
      console.log('השומר: עבר' + (ck.warns.length ? ' · אזהרות: ' + ck.warns.join(' · ') : ''));
      if (nAdd0 !== (Array.isArray(s.adds) ? s.adds.length : 0)) console.log('שגיאה: מספר {+:} (' + nAdd0 + ') אינו כמספר הפריטים ב-adds');
      console.log('אורך הגוף: ' + Math.round(sq.ratio * 100) + '% מן המקור' + (sq.flag ? ' · לקורא נפרד: ' + (sq.lines.length ? sq.lines.map((x) => x.r + '% ' + SKC.plainI(x.now).slice(0, 50)).join(' | ') : 'כל הקטע') : ''));
      console.log('ארמית חדשה: ' + (SKC.aramNew(r.text, text).join(', ') || 'אין'));
      process.exit(0);
    }
    let read = [];
    if (sq.flag) {
      const need = sq.lines.length ? sq.lines.map((x) => x.now) : SKC.rows(text).filter((x) => x.k === 'line').map((x) => x.v);
      const got = Array.isArray(s.read) ? s.read : [];
      const nk = (t) => SKC.qnorm(SKC.plainI(String(t || '')));
      const miss = need.filter((l) => !got.some((g) => nk(g.line) && (nk(g.line) === nk(l) || nk(l).indexOf(nk(g.line)) > -1 || nk(g.line).indexOf(nk(l)) > -1)));
      if (miss.length) {
        const rf = path.join(WORK, jid, 'read-' + (si + 1) + '.txt');
        fs.mkdirSync(path.dirname(rf), { recursive: true });
        fs.writeFileSync(rf, miss.map((l) => SKC.plainI(l)).join('\n') + '\n');
        die('הידוק יתר (' + (sq.seg ? 'הקטע ' + Math.round(sq.ratio * 100) + '% מאורכו' : sq.lines.map((x) => x.r + '%').join(', ')) + '): השורות האלה צריכות קורא נפרד.\n' +
            'תן את ' + path.relative(ROOT, rf) + ' לקורא שאינו רואה את המקור ולא את הגמרא, ובקש ממנו לכתוב לכל שורה במשפט אחד מה היא אומרת.\n' +
            'אחר כך הוסף ל-seg.json את "read": [{"line","said","ok"}] - ok=false כשלא הבין או הבין אחרת מן המקור, ואז כתוב את השורה בפחות הידוק.');
      }
      const bad = got.filter((g) => g.ok === false);
      if (bad.length) die('הקורא הנפרד לא הבין ' + bad.length + ' שורות: ' + bad.map((g) => SKC.plainI(g.line).slice(0, 50)).join(' · ') + '\nכתוב אותן בפחות הידוק והרץ שוב (השדה read מתעדכן לנוסח החדש).');
      read = got.map((g) => ({ line: String(g.line || '').slice(0, 600), said: String(g.said || '').slice(0, 600), ok: g.ok !== false }));
    }
    const adds = (Array.isArray(s.adds) ? s.adds : []).map((a) => ({ t: String(a.t || ''), gem: String(a.gem || '').slice(0, 600) }));
    const nAdd = SKC.parse(text).reduce((n, k) => n + ((k.v || '').match(/\{\+:/g) || []).length, 0);
    if (nAdd !== adds.length) die('מספר ההשלמות {+:...} בנוסח (' + nAdd + ') אינו כמספר הפריטים ב-adds (' + adds.length + '). לכל השלמה - לשון הגמרא שממנה נלקחה.');
    const layers = ['ליטוש'];
    if (s.skipped) layers.push('קיצור מרחבי');
    if (adds.length) layers.push('השלמה');
    o.items.push({ iid: 's' + (si + 1), kind: 'seg', seg: si, sugya: seg.sugya, ids: r.ids, orig: r.text, text, point: String(s.point || ''),
                   changes: (s.changes || []).map(String).slice(0, 24), layers, stat: cp.stat, skipped: String(s.skipped || ''), adds, warn: ck.warns || [], read,
                   keep: (Array.isArray(s.keep) ? s.keep : s.keep ? [s.keep] : []).map((x) => (typeof x === 'string' ? x : JSON.stringify(x)).slice(0, 300)) });
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
  /* פרומפט 29: סוף החצי הראשון של פרק ארוך - עוצרים כאן; החצי השני בשיחה חדשה, שקוראת את הכללים מחדש */
  if (H && rs.part === 1 && o.plan.slice(0, H).every((p, i) => o.items.some((x) => x.seg === i)))
    console.log('\nהחצי הראשון הושלם (' + H + ' קטעים). הרץ: node tools/sakem/runner.mjs pause ' + jid + ' --push, וצא. החצי השני - בהרצה הבאה.');
} else if (cmd === 'pause') {
  /* סוף הרצה באמצע פרק (חצי ראשון, או זמן שנגמר): שורה ביומן ההרצות, ויציאה */
  const [jid] = A;
  const pk = pkOf(jid), o = outOf(jid);
  if (!o) die('אין הצעות.');
  const rec = logRun(jid, pk, o, 'pause');
  console.log('נרשם ביומן ההרצות: ' + rec.segsThisRun + ' קטעים בהרצה הזאת, ' + o.done + ' מתוך ' + o.total + ' בסך הכול.');
  if (PUSH) push('סכם: ' + (pk.title || jid) + ' - סוף הרצה (' + o.done + ' מתוך ' + o.total + ')', [outF(jid), RUNS]);
} else if (cmd === 'finish') {
  const [jid] = A;
  const pk = pkOf(jid), o = outOf(jid);
  if (!o) die('אין הצעות.');
  if (o.done < o.total) die('נכתבו ' + o.done + ' מתוך ' + o.total + ' - אי אפשר לסיים.');
  /* פרומפט 29: אפס חוסמות בפרק. כל קטע נבדק שוב במצב המשימה - גם קטעים שנכתבו לפני שהכללים הוחמרו */
  const blockers = [];
  o.items.forEach((x) => { if (x.kind !== 'seg') return;
    const r = origOf(pk, pk.units.find((u) => u.id === x.ids[0]).id, x.ids[x.ids.length - 1]), cx = ctxOf(pk, r);
    const t = x.nochange ? r.text : x.text, hd = SKC.hatzDel(r.text, t);
    const c = SKC.comply(hd.orig, hd.text, Object.assign({}, cx, { strict: true, keep: x.keep, changes: x.changes, hatz: cx.hatz.filter((id) => !hd.ids.includes(id)), hatzDel: hd.ids.length }));
    if (c.errs.length) blockers.push('קטע ' + (x.seg + 1) + ': ' + c.errs.join(' · '));
    x.stat = c.stat; x.abs = SKC.absStat(hd.text); });
  if (blockers.length && !process.argv.includes('--allow-old')) die('בפרק נשארו ' + blockers.length + ' קטעים עם ליקוי חוסם - put מחדש לכל אחד מהם:\n' + blockers.join('\n'));
  /* בודק הציות בסיום הפרק (פרומפט 28): פרק שלם בלי שום רווח - נעצר ומבקש סבב רווחים; ושורת סיכום לראש הסקירה */
  const S = { bold: 0, space: 0, dash: 0, side: 0, hatz: 0 };
  o.items.forEach((x) => { if (x.kind !== 'seg') return;
    if (x.stat) for (const k in S) S[k] += +x.stat[k] || 0;
    else { const t = x.nochange ? SKC.toInter(pk.units.filter((u) => x.ids.includes(u.id))).text : x.text; const c = SKC.comply(t, t, {}); S.space += c.stat.space; S.dash += c.stat.dash; S.bold += c.stat.bold; } });
  if (!S.space && !process.argv.includes('--no-space-ok')) die('בפרק כולו אין אף (רווח). כלל קבוע של בעל הפרויקט: רווח לפני גופא / ת"ר / אמר מר ובפתיחת יחידה חדשה בלי כותרת.\nהוסף (רווח) בקטעים המתאימים (put מחדש לקטעים האלה) והרץ finish שוב. (--no-space-ok רק אם באמת אין שום מקום כזה בפרק.)');
  o.summary = 'בפרק: ' + S.bold + ' הדגשות במשנה, ' + S.space + ' רווחים, ' + S.dash + ' מקפי תירוץ, ' + S.side + ' כותרות צד חדשות, ' + S.hatz + ' עיטורים נמחקו';
  o.compliance = S;
  /* מה סכם למד מאז הפרק הקודם (המקליט, פרומפט 28) */
  try { const lr = rd(path.join(D, 'learn', 'rules.json')); const last = lr.lastFinish || 0; o.learnedNew = (lr.rules || []).filter((x) => !x.off && (x.t || 0) > last).length; lr.lastFinish = Date.now(); wr(path.join(D, 'learn', 'rules.json'), lr); } catch (e) { o.learnedNew = 0; }
  console.log(o.summary);
  /* פרומפט 29: כרטיס הציון בראש הסקירה, ולידו הדגם (בבא בתרא פרק ה, data/sakem/model-bb5.json) לכל קטע */
  { const segs = o.items.filter((x) => x.kind === 'seg'), n = segs.length || 1;
    const sum = (k) => segs.reduce((a, x) => a + (+(x.stat || {})[k] || 0), 0);
    const lenA = sum('lenA'), lenB = sum('lenB');
    const warnLeft = segs.reduce((a, x) => a + ((x.warn || []).length), 0);
    let model = null; try { model = rd(path.join(D, 'model-bb5.json')); } catch (e) {}
    o.score = { segs: segs.length, perSeg: SKC.absAvg(segs.map((x) => x.abs || {})),
      bold: S.bold, space: S.space, dash: S.dash, side: S.side, nose: sum('nose'), hatz: S.hatz, abbr: sum('abbr'),
      warnLeft, block: blockers.length, lenPct: lenA ? Math.round((lenB / lenA - 1) * 1000) / 10 : 0,
      model: model ? { segs: model.segs, perSeg: model.perSeg, lenPct: model.lenPct } : null };
    console.log('כרטיס הציון: ' + JSON.stringify(o.score)); }
  o.status = 'ready';
  o.t = Date.now();
  o.counts = { shown: o.items.filter((x) => !x.nochange).length, spatial: o.items.filter((x) => (x.layers || []).includes('קיצור מרחבי')).length,
               adds: o.items.reduce((n, x) => n + ((x.adds || []).length), 0), missing: o.items.filter((x) => x.kind === 'missing').length };
  wr(outF(jid), o);
  console.log('מוכן לסקירה:', JSON.stringify(o.counts));
  const rec = logRun(jid, pk, o, 'finish');
  console.log('נרשם ביומן ההרצות (data/sakem/runs.jsonl): ' + JSON.stringify(rec));
  console.log('פרק אחד בהרצה: צא עכשיו. הפרק הבא - בהרצה הבאה, בשיחה חדשה.');
  if (PUSH) push('סכם: ' + (pk.title || jid) + ' - מוכן לסקירה', [outF(jid), RUNS].concat(fs.existsSync(path.join(D, 'learn', 'rules.json')) ? [path.join(D, 'learn', 'rules.json')] : []));
} else if (cmd === 'lessons') {
  const stF = path.join(D, 'lessons-state.json'), st = fs.existsSync(stF) ? rd(stF) : { done: [] };
  /* 6.11.2026: סבב שני על אותו פרק (אותו jid) נשא הכרעות חדשות והן דולגו. המפתח הוא עכשיו jid@זמן העבודה */
  const dkey = (j) => j + '@' + (((rd(path.join(DEC, j + '.json')) || {}).job || {}).t || '');
  const todo = ls(DEC).map((f) => f.slice(0, -5)).filter((j) => st.done.indexOf(dkey(j)) < 0);
  /* המקליט (פרומפט 28): דפוסים חדשים מעריכות המנהל, הערות "הערה לקלוד" ושיחות לוח הסקירה שטרם נקראו */
  const since = st.learnT || 0, LRf = path.join(D, 'learn', 'rules.json'), PTf = path.join(D, 'learn', 'patterns.json');
  const nr = fs.existsSync(LRf) ? (rd(LRf).rules || []).filter((x) => (x.t || 0) > since) : [];
  if (nr.length) console.log('\n######## כללים חדשים שנקלטו מאז הפעם הקודמת (' + nr.length + ')\n' + nr.map((x) => '- ' + (x.off ? '[בוטל] ' : '') + x.text).join('\n'));
  if (fs.existsSync(PTf)) { const P = rd(PTf); console.log('\n######## עריכות המנהל: ' + P.total + ' · ' + JSON.stringify(P.cnt) + '\nצורה: ' + Object.entries(P.sub || {}).sort((a, b) => b[1].w - a[1].w).slice(0, 8).map(([k, v]) => k + ' ' + v.n).join(' · ')); }
  const AK = process.env.LEOKMEI_ADMIN_KEY || '';
  if (AK) {
    const H = { 'x-admin-key': AK }, API2 = process.env.SAKEM_API || 'https://leokmei-suggest.m7654301.workers.dev';
    try {
      const N = await (await fetch(API2 + '/notes', { headers: H })).json();
      const nn = (N.items || N.notes || []).filter((x) => !x.learned && (x.t || 0) > since);
      if (nn.length) console.log('\n######## הערות חדשות לקלוד (' + nn.length + ') - ללמוד מהן כלל כללי; בריפו הציבורי לא לצטט אותן\n' + nn.map((x) => '- [' + (x.slug || '') + ' ' + (x.daf || '') + '] ' + x.note + (x.was ? '\n  היה: ' + x.was + '\n  נעשה: ' + (x.now || '') : '')).join('\n'));
    } catch (e) { console.log('\n(הערות לקלוד: לא נקראו - ' + e.message + ')'); }
  } else console.log('\n(הערות לקלוד ולוח הסקירה: אין מפתח מנהל בסביבה - דלג; הן נקראות בשיחה המקומית)');
  if (!todo.length && !nr.length) die('אין הכרעות חדשות.', 0);
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
  const dk2 = (j) => { const f = path.join(DEC, j + '.json'); return fs.existsSync(f) ? j + '@' + ((rd(f).job || {}).t || '') : j; };
  st.done = [...new Set(st.done.concat(A.map(dk2)))];
  st.learnT = Date.now();
  wr(stF, st);
  console.log('סומן.');
  if (PUSH) push('סכם: לקחים מהכרעות המנהל', [stF, path.join(ROOT, 'docs', 'sakem-lessons.md')]);
} else {
  die('פקודה לא מוכרת. ראה docs/sakem-runner.md');
}
