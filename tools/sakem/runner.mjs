/* סכם - כלי העבודה של המשימה המתוזמנת בענן (פרומפט 15, 28.10.2026).
   ההוראות המלאות: docs/sakem-runner.md. הכלי אינו קורא לשום מודל: הוא מכין את החומר לקריאה,
   בודק כל הצעה בשומר של סכם (tools/sakem_core.js - אותו שומר שבדף), ושומר התקדמות אחרי כל קטע.

   node tools/sakem/runner.mjs status                    התור ומצב כל עבודה
   node tools/sakem/runner.mjs next [jid]                העבודה הבאה (או עבודה מסוימת) (או "התור ריק", קוד יציאה 3) והכנת חומר הקריאה
                                                         נועל .locks/sakem-<jid>.lock ודוחף (פרומפט 69); --station=<שם>, --no-lock
   node tools/sakem/runner.mjs rules                     כללי הניסוח, הדוגמאות והלקחים - לקרוא לפני הכתיבה
   node tools/sakem/runner.mjs orig  <jid> <from> <to>   נוסח הביניים של טווח יחידות (כפי שהדף יראה אותו)
   node tools/sakem/runner.mjs plan  <jid> <plan.json>   חלוקת הפרק לקטעים טבעיים (אחרי קריאת כל הסוגיה)
   node tools/sakem/runner.mjs put   <jid> <seg.json> [--push]   הצעה לקטע אחד, נבדקת ונשמרת מיד
   node tools/sakem/runner.mjs finish <jid> [--push]     סיום: "מוכן לסקירה" (בודק שאין חוסמות, כרטיס ציון, יומן ההרצות)
   node tools/sakem/runner.mjs pause  <jid> [--reason=..] [--push]   סוף הרצה באמצע פרק (סוף חלק / זמן / הקשר / שגיאה) - שורה ביומן ההרצות עם הסיבה (פרומפט 71)
   node tools/sakem/runner.mjs lessons                   הכרעות המנהל שטרם הופקו מהן לקחים
   node tools/sakem/runner.mjs lessons-done <jid>... [--post=<מסכת>:<מספר>,...] [--rules=<קובץ>]
                                                         סימון שהלקחים מהן נכתבו ל-docs/sakem-lessons.md; --post - עד איפה
                                                         נותחו עריכות המנהל אחרי סכם; --rules - כללים לרשימה ולדף "מה סכם למד" */
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import * as COST from './cost.mjs';

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
/* סדר מסכתות (בקשת מיכאל 19.11.2026): data/sakem/hold.json = {"<מסכת ממתינה>": "<מסכת שקודמת לה>"}.
   עבודות של מסכת ממתינה אינן מוצגות ב-status ואינן נלקחות ב-next (בלי מזהה), כל עוד יש במסכת הקודמת עבודה שאינה "מוכן לסקירה". */
const HOLD = (() => { try { return JSON.parse(fs.readFileSync(path.join(ROOT, 'data', 'sakem', 'hold.json'), 'utf8')); } catch (e) { return {}; } })();
const slugOfFile = (f) => { try { return (rd(path.join(Q, f)).slug) || f.replace(/-(p|s)\d.*$/, ''); } catch (e) { return f.replace(/-(p|s)\d.*$/, ''); } };
const heldSlugs = (() => { const files = ls(Q); const open = new Set(); files.forEach((f) => { const o = outOf(f.slice(0, -5)); if (!o || o.status !== 'ready') open.add(slugOfFile(f)); }); return new Set(Object.keys(HOLD).filter((w) => open.has(HOLD[w]))); })();
const qFiles = () => ls(Q).filter((f) => !heldSlugs.has(slugOfFile(f)));
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
/* הכרעת בעל הפרויקט 15.11.2026: פירוש הגמרא וחברותא חייבים להיות לפני הכותב, תמיד.
   לכן הכלי מושך בעצמו את שני הענפים של הריפו הפרטי (גם בשכפול שנעשה בענף אחד),
   ודף שאין לו חברותא בחבילה (packs) נלקח מן העיבוד המלא (json/<מסכת>/). */
function chavFetch() {
  for (const b of ['main', 'perush-store']) {
    try { execFileSync('git', ['-C', CHAV, 'fetch', '-q', 'origin', '+refs/heads/' + b + ':refs/remotes/origin/' + b], { stdio: ['ignore', 'ignore', 'ignore'], timeout: 180000 }); }
    catch (e) { /* בלי רשת - נשתמש במה שכבר נמשך; אם חסר, הבדיקה למטה עוצרת */ }
  }
}
function chavCtx(pk) {
  chavFetch();
  const out = { per: {}, hv: {}, warn: '' };
  const txt = chavShow('origin/perush-store', 'perush/' + pk.slug + '.json');
  if (txt) out.per = JSON.parse(txt);
  else out.warn = 'פירוש הגמרא לא נמצא בריפו הפרטי (ענף perush-store).';
  for (const pg of pk.pages || []) {
    const name = String(pg.daf).replace(/[^א-ת]/g, '') + (/:\s*$/.test(pg.daf) ? 'ב' : 'א');
    const t = chavShow('origin/main', 'packs/' + pk.slug + '/' + name + '.json');
    if (t) {
      const segs = JSON.parse(t).segs || [];
      out.hv[pg.daf] = segs.map((s) => ({ p: s.para, g: s.gemara || '', e: String(s.explain || '').replace(/\[\[הערה:\d+\]\]/g, '') }));
      continue;
    }
    const j = pk.masechet && chavShow('origin/main', 'json/' + pk.masechet + '/' + name + '.json');
    if (j) out.hv[pg.daf] = (JSON.parse(j).segments || []).map((s) => ({ g: s.gemara || '', e: String(s.explain || '').replace(/\[\[הערה:\d+\]\]/g, '') }));
  }
  return out;
}
/* דפים שבאמצע הפרק ואינם בחבילה (למשל ברכות כח. בפרק ד, 15.11.2026) - לשון הגמרא מ-data/sources */
function fillPages(pk) {
  const pages = pk.pages || [];
  const keys = pages.map((p) => dafKey(p.daf)).filter((n) => n !== null);
  if (!keys.length) return [];
  let src = null;
  try { src = rd(path.join(ROOT, 'data', 'sources', pk.slug + '.json')).pages || null; } catch (e) {}
  const have = new Set(keys), added = [];
  const all = [];
  for (let n = Math.min(...keys); n <= Math.max(...keys); n++) {
    const p = pages.find((x) => dafKey(x.daf) === n);
    if (p) { all.push(p); continue; }
    if (have.has(n)) continue;
    const daf = Object.keys(src || {}).find((d) => dafKey(d) === n);
    if (daf && src[daf] && (src[daf].gemara || []).length) { all.push({ daf, g: src[daf].gemara, refs: src[daf].refs || [], filled: true }); added.push(daf); }
  }
  pk.pages = all;
  return added;
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
    execFileSync('git', ['add', '-A', '--', ...files], { cwd: ROOT, stdio: 'inherit' });
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
    /* הפרק הקודם, הנוכחי והבא: טווח הדפים של פרק נפתח לפעמים במשנה האחרונה של הפרק הקודם
       (שבת פרק ב בדף יט: - "אין צולין"), ובלי זה כל הצעה לקטע הראשון נחסמה כ"טקסט שאינו מן המשנה" */
    const C = m.chapters || [];
    return [C[n - 2], C[n - 1], C[n]].filter(Boolean).map((ch) => ch.join(' ')).join(' ');
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
/* פרק ארוך (מעל 30 קטעים) - שתי הרצות: החצי הראשון עד H (לא כולל). נשאר רק להרצות שהתחילו לפני פרומפט 71 */
const HALF_MIN = 30;
const halfOf = (o) => (o && o.total > HALF_MIN ? Math.ceil(o.total / 2) : 0);
/* פרומפט 71 (19.11.2026): פרק ארוך מתחלק לפי גודל ולא רק לשני חצאים - מעל 30 קטעים, חלקים של עד כ-16 קטעים
   (קידושין פרק א, 62 קטעים: ארבעה חלקים). הגבולות: מערך אינדקסים [0, ..., total]; חלק p = קטעים bounds[p] עד bounds[p+1]-1.
   הרצה שהתחילה בכלי הישן (run.json בלי bounds) ממשיכה בחצאים - תואם לאחור. */
const PART_MAX = 16;
const boundsOf = (o) => {
  if (!o || o.total <= HALF_MIN) return null;
  const n = Math.ceil(o.total / PART_MAX), b = [];
  for (let i = 0; i <= n; i++) b.push(Math.round((i * o.total) / n));
  return b;
};
/* הגבולות של ההרצה הזאת: מה שנשמר ב-run.json, ובהרצה ישנה (part בלי bounds) - החצאים */
const runBounds = (rs, o) => (rs && rs.bounds) || (rs && rs.part && halfOf(o) ? [0, halfOf(o), o.total] : boundsOf(o));
const partIx = (b, si) => { for (let p = 0; p < b.length - 1; p++) if (si < b[p + 1]) return p; return b.length - 2; };
/* פרומפט 71: נעילה מתה אחרי 40 דקות בלי put (הרצה תקינה דוחפת אחרי כל קטע) - במקום שלוש שעות */
const LOCK_IDLE = 40 * 60e3;
/* מצב ההרצה הנוכחית - מקומי בלבד (_work אינו במאגר): כל הרצה של המשימה היא שיחה חדשה ושכפול חדש */
const runF = (jid) => path.join(WORK, jid, 'run.json');
const runState = (jid) => (fs.existsSync(runF(jid)) ? rd(runF(jid)) : {});
const saveRun = (jid, s) => wr(runF(jid), s);
const RUNS = path.join(D, 'runs.jsonl');
/* סימון ההרצה (מקומי): על איזו עבודה ההרצה הזאת עובדת. כל הרצה של המשימה היא שכפול חדש, ולכן אין סימון.
   במחשב המקומי _work נשמר - סימון בן יותר משלוש שעות אינו נחשב, ו-next --new-run מאפס אותו */
/* פרומפט 61: כמה עובדים במקביל באותו מחשב - כל אחד בסימון משלו (SAKEM_MARK) */
const MARK = process.env.SAKEM_MARK ? path.resolve(process.env.SAKEM_MARK) : path.join(WORK, '.run.json');
const runMark = () => { try { const m = rd(MARK); return Date.now() - (m.t || 0) < 3 * 3600e3 ? m : null; } catch (e) { return null; } };
/* שורה ביומן ההרצות: פרק, חלק, קטעים, יחידות, אורך המקור, התחלה וסיום - להערכת העלות לפרק */
function logRun(jid, pk, o, how, extra) {
  const rs = runState(jid);
  const units = pk.units.length, origLen = SKC.plainI(SKC.toInter(pk.units).text).replace(/\s+/g, '').length;
  const rb = rs.part ? runBounds(rs, o) : null;
  const rec = { jid, slug: pk.slug, perek: +((pk.job && pk.job.perek) || pk.perek || 0) || null, title: pk.title || '', part: rs.part ? rs.part + '/' + (rb ? rb.length - 1 : 2) : 'כולו',
    segs: o.total, segsThisRun: o.done - (rs.done0 || 0), putsThisRun: rs.puts || 0, units, origLen, start: rs.t0 ? new Date(rs.t0).toISOString() : null, end: new Date().toISOString(), how, ...(extra || {}) };
  if (rs.t0) rec.minutes = Math.round((Date.now() - rs.t0) / 6000) / 10;
  /* פרומפט 70: עלות אמיתית מתמלול השיחה (כל השיחה, כולל lessons וסוכני-משנה; אם כבר נרשמה שורה באותה שיחה - מאז אותה שורה).
     אין תמלול - "לא נמדד" עם הסיבה, בלי מספר */
  rec.station = STATION; rec.round = COST.roundOf(pk.title, jid); if (LEAN) rec.lean = 1;
  { const m0 = runMark(); const since = (m0 && m0.costAt) || 0;
    const ms = COST.measure(ROOT, since);
    if (ms.kind === 'מדידה') { rec.tokens = ms.tokens; rec.tokTotal = ms.total; rec.usd = ms.usd; rec.model = ms.model; rec.session = ms.session; rec.cost = 'מדידה'; }
    else { rec.cost = 'לא נמדד'; rec.costWhy = ms.why; }
    if (m0) { m0.costAt = Date.now(); wr(MARK, m0); } }
  fs.mkdirSync(D, { recursive: true });
  fs.appendFileSync(RUNS, JSON.stringify(rec) + '\n');
  rs.logged = 1; saveRun(jid, rs);
  /* ההרצה הסתיימה (פרק אחד, או חצי) - next הבא באותה הרצה אומר "התור ריק" */
  const m = runMark(); if (m) { m.stopped = Date.now(); wr(MARK, m); }
  return rec;
}

const cmd = process.argv[2], A = process.argv.slice(3).filter((x) => !/^--/.test(x)), PUSH = process.argv.includes('--push'), DRY = process.argv.includes('--dry');
/* פרומפט 70: הצינור החסכוני (--lean או SAKEM_LEAN=1) - מאחורי דגל עד שעבר את מבחן האיכות */
const LEAN = process.argv.includes('--lean') || process.env.SAKEM_LEAN === '1';

/* פרומפט 69 (19.11.2026): נעילה לכל עבודה - שני עובדים (החשבון הראשון והשני) בלי התנגשות.
   לפני עבודה: .locks/sakem-<jid>.lock (שם העמדה, השעה, אסימון ההרצה) ודחיפה מיד. הנעילה כבר קיימת או שהדחיפה
   נדחתה - העבודה של עובד אחר, לוקחים את הבאה. נעילה בת יותר משלוש שעות - מתה. finish/pause משחררים ודוחפים.
   שם העמדה: SAKEM_STATION או --station=<שם>. --no-lock (במחשב, בלי רשת) - בלי נעילה. */
const LOCKS = path.join(ROOT, '.locks');
const lockF = (jid) => path.join(LOCKS, 'sakem-' + jid + '.lock');
const STATION = ((process.argv.find((x) => /^--station=/.test(x)) || '').slice(10)) || process.env.SAKEM_STATION || 'עובד סכם';
const NOLOCK = process.argv.includes('--no-lock');
function lockInfo(jid) {
  const f = lockF(jid);
  if (!fs.existsSync(f)) return null;
  const txt = fs.readFileSync(f, 'utf8');
  const m = txt.match(/\d{4}-\d\d-\d\dT[\d:.]+Z/), tok = (txt.match(/^token=(\S+)/m) || [])[1] || '';
  let t = m ? Date.parse(m[0]) : NaN;
  if (isNaN(t)) { try { t = 1000 * +execFileSync('git', ['log', '-1', '--format=%ct', '--', f], { cwd: ROOT, encoding: 'utf8' }).trim(); } catch (e) { t = 0; } }
  /* פרומפט 71: פעילות אחרונה = הנעילה עצמה או הדחיפה האחרונה של ההצעות (put / plan / pause), המאוחרת שבהן.
     40 דקות בלי שום דחיפה - הנעילה מתה (נלקחה פעם בהרצה שנתקעה בקריאת פרק ענק, והחזיקה את העבודה שלוש שעות) */
  let act = t || 0;
  try { const c = 1000 * +execFileSync('git', ['log', '-1', '--format=%ct', '--', path.join(O, jid + '.json')], { cwd: ROOT, encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim(); if (c > act) act = c; } catch (e) {}
  const idle = Date.now() - act;
  return { t: t || 0, tok, act, idle, dead: idle > LOCK_IDLE, txt: txt.trim() };
}
const lockMine = (jid, tok) => { const l = lockInfo(jid); return !!(l && tok && l.tok === tok); };
const lockBusy = (jid, tok) => { const l = lockInfo(jid); return !!(l && !l.dead && !(tok && l.tok === tok)); };
const gitQ = (args) => execFileSync('git', args, { cwd: ROOT, stdio: ['ignore', 'ignore', 'ignore'], timeout: 180000 });
/* תפיסת עבודה: pull, בדיקה, כתיבה, דחיפה אחת. true - שלנו; false - של עובד אחר */
function gitPull() { try { gitQ(['pull', '--rebase', '--autostash', '-q', 'origin', 'main']); } catch (e) { try { gitQ(['rebase', '--abort']); } catch (_) {} } }
function lockTake(jid, tok) {
  for (let i = 0; i < 3; i++) {
    if (i) gitPull();
    if (lockBusy(jid, tok)) return false;
    /* פרומפט 71: לקיחת נעילה מתה - נרשמת בהודעת הדחיפה וביומן ההרצות */
    const old = lockInfo(jid), files = [lockF(jid)];
    let note = '';
    if (old && old.dead && !(tok && old.tok === tok)) {
      const who = old.txt.split('\n')[0], mins = Math.round(old.idle / 60e3);
      note = ' - נלקחה מנעילה מתה של ' + who + ' (אין דחיפה ' + mins + ' דקות, מאז ' + new Date(old.act).toISOString().slice(11, 16) + ' UTC)';
      fs.mkdirSync(D, { recursive: true });
      fs.appendFileSync(RUNS, JSON.stringify({ jid, how: 'takeover', from: who, idleMin: mins, by: STATION, at: new Date().toISOString() }) + '\n');
      files.push(RUNS);
      console.log('נעילה מתה' + note.slice(2));
    }
    fs.mkdirSync(LOCKS, { recursive: true });
    fs.writeFileSync(lockF(jid), STATION + ' · ' + new Date().toISOString() + '\ntoken=' + tok + '\n');
    try { gitQ(['add', '--', ...files]); gitQ(['commit', '-q', '-m', 'סכם: נעילה ' + jid + ' (' + STATION + ')' + note]); }
    catch (e) { return lockMine(jid, tok); }
    try { gitQ(['push', '-q', 'origin', 'HEAD:main']); return true; }
    catch (e) {
      /* הדחיפה נדחתה - מבטלים את הנעילה המקומית, מושכים, ובודקים שוב: עובד אחר נעל - הלאה; דחיפה אחרת (סנכרון) - ניסיון חוזר */
      try { gitQ(['reset', '-q', '--soft', 'HEAD~1']); } catch (_) {}
      /* פרומפט 71: נעילה מתה שהייתה במאגר - חוזרת לנוסח שב-HEAD (ולא נמחקת), ושורת הלקיחה ביומן מתבטלת */
      for (const f of files) { try { gitQ(['reset', '-q', '--', f]); gitQ(['checkout', '-q', 'HEAD', '--', f]); } catch (_) { try { fs.unlinkSync(f); } catch (__) {} } }
    }
  }
  return false;
}
/* שחרור: מוחקים את הנעילה (רק אם היא שלנו, או מתה) ומחזירים את הנתיב לדחיפה */
function lockFree(jid) {
  if (NOLOCK) return [];
  const l = lockInfo(jid);
  if (!l) return [];
  const m = runMark();
  if (!l.dead && l.tok && !(m && m.tok === l.tok)) { console.log('הנעילה של ' + jid + ' אינה של ההרצה הזאת (' + l.txt.split('\n')[0] + ') - לא משוחררת.'); return []; }
  fs.unlinkSync(lockF(jid));
  return [lockF(jid)];
}

/* פרומפט 71: עצירה אחרי שנלקחה נעילה - משחררים אותה ודוחפים, כדי שהעבודה לא תיחסם עד שהנעילה תמות */
function dieFree(jid, m, c = 1) {
  const f = NOLOCK ? [] : lockFree(jid);
  if (f.length) { console.log('הנעילה של ' + jid + ' שוחררה (העבודה לא התחילה).'); push('סכם: שחרור נעילה ' + jid + ' - העובד נעצר לפני הכתיבה (' + STATION + ')', f); }
  die(m, c);
}
if (cmd === 'status') {
  const js = qFiles();
  if (heldSlugs.size) console.log('ממתינות לפי סדר (data/sakem/hold.json): ' + [...heldSlugs].join(' '));
  if (!js.length) die('התור ריק.', 0);
  js.forEach((f) => { const jid = f.slice(0, -5), pk = rd(path.join(Q, f)), o = outOf(jid);
    console.log(jid, '·', pk.title || '', '·', o ? (o.status === 'ready' ? 'מוכן לסקירה' : 'בעבודה ' + o.done + '/' + o.total) : 'ממתין'); });
} else if (cmd === 'next') {
  /* next <jid>: עבודה מסוימת (כמה עובדים במקביל, כל אחד על פרק אחר; 6.11.2026) */
  /* פרומפט 51 (16.11.2026): מסכת בהגירה נעולה ב-.locks/p51-<slug>.lock - העובד מדלג עליה */
  const p51Locked = (j) => { try { const s = pkOf(j).slug; return !!s && fs.existsSync(path.join(ROOT, '.locks', 'p51-' + s + '.lock')); } catch (e) { return false; } };
  /* פרומפט 59 (17.11.2026): עבודות "סבב מבני" נעשות בשיחה ייעודית (.locks/p59-<slug>.lock) - next בלי מזהה מדלג עליהן כל עוד הנעילה קיימת */
  const p59Mine = (j) => { try { const k = pkOf(j); return /סבב מבני/.test(k.title || '') && fs.existsSync(path.join(ROOT, '.locks', 'p59-' + k.slug + '.lock')); } catch (e) { return false; } };
  /* פרומפט 61 (18.11.2026): "סכם מלא" על מסכת שלמה (ערכין) נעשה בשיחה ייעודית (.locks/p61-<slug>.lock) - next בלי מזהה מדלג */
  const p61Mine = (j) => { try { const k = pkOf(j); return /סכם מלא/.test(k.title || '') && fs.existsSync(path.join(ROOT, '.locks', 'p61-' + k.slug + '.lock')); } catch (e) { return false; } };
  /* פרומפט 29: פרק אחד בכל הרצה, בהקשר נקי */
  if (process.argv.includes('--new-run')) { try { fs.unlinkSync(MARK); } catch (e) {} }
  const m0 = runMark();
  if (m0 && m0.stopped) die('התור ריק להרצה הזאת: כבר עובד בה ' + m0.jid + ' (הסתיים או נעצר בסוף חצי). פרק אחד בכל הרצה - צא; ההמשך בהרצה הבאה, בשיחה חדשה.', 3);
  const tok = (m0 && m0.tok) || (Date.now().toString(36) + Math.random().toString(36).slice(2, 8));
  if (!NOLOCK) gitPull(); /* פרומפט 69: הנעילות והתור כפי שהם עכשיו ב-main */
  /* פרומפט 69 (19.11.2026): מסכת שלמה בשיחה ייעודית (.locks/p69-<slug>.lock) - next בלי מזהה מדלג על כל עבודותיה */
  const p69Mine = (j) => { try { const s = pkOf(j).slug; return !!s && fs.existsSync(path.join(ROOT, '.locks', 'p69-' + s + '.lock')); } catch (e) { return false; } };
  const cands = (A[0] ? ls(Q) : qFiles()).map((f) => f.slice(0, -5)).filter((j) => { const o = outOf(j); return (!A[0] || j === A[0]) && (!o || o.status !== 'ready') && !p51Locked(j) && (A[0] || (!p59Mine(j) && !p61Mine(j) && !p69Mine(j))); });
  /* ההרצה כבר עובדת על עבודה - ממשיכים בה (גם אם לפניה בתור התפנתה עבודה אחרת) */
  if (m0 && !A[0]) { if (!cands.includes(m0.jid)) die('התור ריק להרצה הזאת: כבר עובד בה ' + m0.jid + '. פרק אחד בכל הרצה - צא.', 3); cands.splice(0, cands.length, m0.jid); }
  if (m0 && A[0] && m0.jid !== A[0]) die('התור ריק להרצה הזאת: כבר עובד בה ' + m0.jid + '. פרק אחד בכל הרצה - צא; ההמשך בהרצה הבאה, בשיחה חדשה.', 3);
  /* פרומפט 69: נעילה לכל עבודה (.locks/sakem-<jid>.lock) */
  /* פרומפט 71: עובד בלי הריפו הפרטי (ובלי מפתח) נעל עבודה, נעצר בבדיקת החומר והשאיר את הנעילה - חמש פעמים ב-19.11
     ("עובד סכם", 11:51-15:25, אף קטע). לכן בודקים זאת לפני הנעילה, ועצירה אחרי נעילה משחררת אותה */
  if (!CHAV && !adminKey() && !process.argv.includes('--allow-missing')) die('אין גישה לריפו הפרטי (leokmei-chavruta לא שוכפל ליד הריפו הזה) ואין מפתח מנהל - לא נלקחה שום עבודה ולא נעלתי דבר.\nשכפל: git clone --filter=blob:none --no-checkout <כתובת leokmei-chavruta> ../leokmei-chavruta (בלי --depth ובלי --single-branch), והרץ שוב.', 4);
  let jid = null, skipped = [];
  /* פרומפט 71: עמדה שנעילותיה על עבודה מתו פעמיים בלי שום דחיפה (שורות takeover ביומן, שש השעות האחרונות) - אינה לוקחת אותה שוב,
     כדי שלא תחסום אותה 40 דקות בכל שעה (19.11: "עובד סכם" נעל את קידושין פרק א שש פעמים ולא כתב אף קטע) */
  const failed = (j) => { if (A[0]) return false; try { return fs.readFileSync(RUNS, 'utf8').split('\n').filter((x) => x.includes('"takeover"') && x.includes('"jid":"' + j + '"')).map((x) => JSON.parse(x))
    .filter((r) => String(r.from || '').startsWith(STATION + ' ·') && Date.now() - Date.parse(r.at) < 6 * 3600e3).length >= 2; } catch (e) { return false; } };
  for (const j of cands) {
    if (failed(j)) { console.log('דילוג על ' + j + ': הנעילות של ' + STATION + ' עליה מתו פעמיים בלי כתיבה - עובד אחר ייקח אותה.'); continue; }
    if (NOLOCK || lockMine(j, tok)) { jid = j; break; }
    if (lockBusy(j, tok)) { skipped.push(j); continue; }
    if (lockTake(j, tok)) { jid = j; break; }
    skipped.push(j);
  }
  if (skipped.length) console.log('נעולות בידי עובד אחר (דולגו): ' + skipped.join(' '));
  if (!jid) die(cands.length ? 'התור ריק לעובד הזה: כל העבודות שנותרו נעולות בידי עובד אחר.' : 'התור ריק.', 3);
  if (!m0) { wr(MARK, { jid, t: Date.now(), tok }); try { fs.unlinkSync(runF(jid)); } catch (e) {} }
  if (!NOLOCK) console.log('נעילה: .locks/sakem-' + jid + '.lock (' + STATION + ') - finish/pause --push משחררים אותה.');
  const pk = pkOf(jid), o = outOf(jid);
  const dir = path.join(WORK, jid);
  fs.mkdirSync(dir, { recursive: true });
  /* א. לשון הגמרא ופירוש הגמרא, לפי דפים */
  const filled = fillPages(pk);
  if (filled.length) console.log('דפים שלא היו בחבילה ונוספו מלשון הגמרא שבמאגר: ' + filled.join(' '));
  const prv = await privateCtx(pk);
  if (prv.warn) console.log('אזהרה: ' + prv.warn);
  /* פרומפט 71: פרק ארוך בחלקים - החומר של ההרצה הוא רק טווח החלק (ואם החלק מתחיל או נגמר באמצע סוגיה - כל הסוגיה),
     ועוד תקציר מהלך הפרק (context.md) מן החלוקה ומן ה-point של הקטעים שנכתבו. כך הקריאה המרחבית נשמרת בלי לקרוא פרק ענק כולו
     (קידושין פרק א: 2.4 מיליון תווים של חומר - ההרצות נעצרו אחרי 3 ואחרי 16 קטעים, והשלישית שתקה) */
  const rsN = fs.existsSync(runF(jid)) ? runState(jid) : { t0: Date.now(), done0: o ? o.done : 0, bounds: boundsOf(o) || undefined };
  const B = o ? runBounds(rsN, o) : null;
  let part = null; /* { p, s0, s1 (קטעים בחלק), a, b (אינדקסי יחידות בחומר), dafs } */
  if (B && o.plan) {
    const nx = o.plan.findIndex((s, i) => !o.items.some((x) => x.seg === i));
    const p = partIx(B, nx < 0 ? o.total - 1 : nx), s0 = B[p], s1 = B[p + 1] - 1;
    let e0 = s0, e1 = s1;
    const sg0 = o.plan[s0].sugya, sg1 = o.plan[s1].sugya;
    if (sg0) while (e0 > 0 && o.plan[e0 - 1].sugya === sg0) e0--;
    if (sg1) while (e1 < o.total - 1 && o.plan[e1 + 1].sugya === sg1) e1++;
    const a = pk.units.findIndex((u) => u.id === String(o.plan[e0].from) || +u.id === +o.plan[e0].from);
    const b = pk.units.findIndex((u) => u.id === String(o.plan[e1].to) || +u.id === +o.plan[e1].to);
    const dk = new Set(pk.units.slice(a, b + 1).map((u) => dafKey(u.daf)).filter((n) => n !== null));
    /* דף אחד לפני ואחרי - הגמרא של קצה הסוגיה יושבת לעתים בדף הסמוך */
    const ks = [...dk]; if (ks.length) { dk.add(Math.min(...ks) - 1); dk.add(Math.max(...ks) + 1); }
    part = { p, n: B.length - 1, s0, s1, e0, e1, a, b, dafs: dk };
    pk.pages = (pk.pages || []).filter((pg) => dk.has(dafKey(pg.daf)));
    Object.keys(prv.hv).forEach((d) => { if (!dk.has(dafKey(d))) delete prv.hv[d]; });
  }
  /* חובה (הכרעת בעל הפרויקט 15.11.2026): פירוש וחברותא לכל דף. חסר - עצירה רועשת, לא המשך שקט. */
  { const noPer = (pk.pages || []).filter((pg) => !(prv.per[pg.daf] || []).length).map((pg) => pg.daf);
    const noHv = (pk.pages || []).filter((pg) => !(prv.hv[pg.daf] || []).length).map((pg) => pg.daf);
    if (noPer.length || noHv.length) {
      let msg = 'חסר חומר מן הריפו הפרטי. פירוש הגמרא חסר בדפים: ' + (noPer.join(' ') || '-') + ' · חברותא חסרה בדפים: ' + (noHv.join(' ') || '-') + '.';
      /* 15.11.2026: כשהריפו הפרטי נגיש ורק דפים בודדים חסרים בו - לומר זאת במפורש, כדי שהעובד לא יחשוב שאין גישה */
      const allP = (pk.pages || []).length;
      if (CHAV && !prv.warn && noPer.length < allP && noHv.length < allP) msg += '\nהריפו הפרטי נגיש (' + CHAV + ') ושני הענפים נמשכו. הדפים שלמעלה פשוט אינם קיימים בו - זה המקרה של --allow-missing.';
      if (!process.argv.includes('--allow-missing')) dieFree(jid, msg + '\nאין לכתוב בלי פירוש וחברותא. שכפל את leokmei-chavruta ליד הריפו הזה (git clone --filter=blob:none --no-checkout, בלי --depth ובלי --single-branch) והרץ שוב. רק כשהדף באמת אינו קיים במאגר הפרטי - הוסף --allow-missing וכתוב זאת בסיכום.', 4);
      console.log('אזהרה חמורה: ' + msg + ' (--allow-missing) - לכתוב זאת בסיכום ההרצה.');
    } }
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
  if (part) l += '# פרק ארוך - כאן רק טווח החלק ' + (part.p + 1) + ' מתוך ' + part.n + ' (קטעים ' + (part.e0 + 1) + '-' + (part.e1 + 1) + ' של החלוקה, כולל הסוגיה השלמה בקצוות). מהלך שאר הפרק: context.md\n\n';
  pk.units.forEach((u, i) => { if (part && (i < part.a || i > part.b)) return; l += '⟦' + u.id + '⟧' + (TEXTK(u) ? '' : ' (כותרת / עיטור)') + '\n' + pu[i] + '\n'; });
  fs.writeFileSync(path.join(dir, 'leokmei.md'), l);
  /* פרומפט 71: תקציר מהלך הפרק - כל קטעי החלוקה, וה-point של מה שכבר נכתב */
  if (part) {
    let c = '# ' + (pk.title || jid) + ' - מהלך הפרק (לקריאה מרחבית; החומר המלא של החלק הזה ב-leokmei.md וב-gemara.md)\n\n';
    c += 'החלק של ההרצה הזאת: ' + (part.p + 1) + ' מתוך ' + part.n + ' - קטעים ' + (part.s0 + 1) + ' עד ' + (part.s1 + 1) + '.\n\n';
    o.plan.forEach((sg, i) => {
      const it = o.items.find((x) => x.seg === i && x.kind === 'seg');
      const mark = i >= part.s0 && i <= part.s1 ? '▶ ' : '';
      c += mark + (i + 1) + '. [סוגיה ' + (sg.sugya || '-') + '] ' + sg.title + (it ? (it.nochange ? ' · ללא שינוי' : (it.point ? ' · ' + it.point : '')) : '') + '\n';
    });
    fs.writeFileSync(path.join(dir, 'context.md'), c);
  } else { try { fs.unlinkSync(path.join(dir, 'context.md')); } catch (e) {} }
  console.log('העבודה:', jid, '·', pk.title || '');
  /* פרומפט 56 ד3: עבודת "סבב שני" - ההנחיה המיוחדת (docs/sakem-round-56.md), כמו שדה note/focus */
  if (/סבב שני/.test(pk.title || '')) { const RF = path.join(ROOT, 'docs', 'sakem-round-56.md');
    if (fs.existsSync(RF)) console.log('\n######## הנחיית הסבב השני (גוברת על כלל כללי)\n' + fs.readFileSync(RF, 'utf8')); }
  /* פרומפט 59 (17.11.2026): "סבב מבני" לפי עריכות מיכאל בברכות פרק א - ההנחיה והדוגמאות */
  if (/סבב מבני/.test(pk.title || '')) ['הנחיה.md', 'דוגמאות.md'].forEach((n) => { const F = path.join(ROOT, 'docs', 'פרומפט-59', n);
    if (fs.existsSync(F)) console.log('\n######## פרומפט 59 - ' + n + ' (גובר על כלל כללי)\n' + fs.readFileSync(F, 'utf8')); });
  /* פרומפט 61 (18.11.2026): "סכם מלא" על ערכין - ההנחיה המיוחדת (מסכת דלה: הסבר וגמרא חסרה, לצד קיצור וסגנונות) */
  if (/סכם מלא/.test(pk.title || '')) { const F = path.join(ROOT, 'docs', 'פרומפט-61', 'הנחיה.md');
    if (fs.existsSync(F)) console.log('\n######## פרומפט 61 - הנחיה (גוברת על כלל כללי)\n' + fs.readFileSync(F, 'utf8')); }
  /* פרומפט 62 המשך (18.11.2026): "סבב כללים חדשים" - קטעים קטנים שבהם מחילים רק את הכללים שנלמדו מעריכות מיכאל בערכין */
  if (/סבב כללים חדשים/.test(pk.title || '')) { const F = path.join(ROOT, 'docs', 'פרומפט-62', 'סבב-כללים.md');
    if (fs.existsSync(F)) console.log('\n######## פרומפט 62 - סבב כללים חדשים (גובר על כלל כללי)\n' + fs.readFileSync(F, 'utf8')); }
  console.log('יחידות:', pk.units.length, '· דפים:', (pk.pages || []).map((p) => p.daf).join(' '));
  console.log('לקריאה:', path.relative(ROOT, dir) + '/{' + (part ? 'context.md, ' : '') + 'gemara.md, leokmei.md' + (hv ? ', chavruta.md' : '') + '}');
  /* פרומפט 71: פרק ענק שטרם חולק - ההרצה הזאת כותבת את החלוקה בלבד, ועוצרת */
  if (!o && pk.units.length > 600) console.log('פרק ענק (' + pk.units.length + ' יחידות): בהרצה הזאת רק החלוקה (plan --push), לפי leokmei.md (קרא בחלקים) והגמרא לפי הצורך. אחריה: pause ' + jid + ' --reason=סוף-חלק --push, וצא. הכתיבה - בחלקים, בהרצות הבאות.');
  if (o) console.log('המשך מהרצה קודמת: ' + o.done + ' מתוך ' + o.total + ' קטעים כבר נכתבו. הקטע הבא: ' + (o.plan.findIndex((s, i) => !o.items.some((x) => x.seg === i)) + 1));
  /* פרומפט 70: כל הקטעים כבר נכתבו (ההרצה הקודמת נעצרה לפני finish) - finish מיד, לפני rules וקריאת החומר.
     רק אם finish מצא קטעים חוסמים - rules, וקריאת החומר של הקטעים האלה בלבד (orig --segs). כך לא נקראים כל הכללים לחינם */
  if (o && o.done === o.total) console.log('######## כל ' + o.total + ' הקטעים כבר נכתבו: הרץ מיד node tools/sakem/runner.mjs finish ' + jid + ' --push - לפני rules ולפני קריאת החומר. רק אם finish מצא קטעים חוסמים: rules, ואז orig --segs=<מספר> לקטעים האלה בלבד, put, ו-finish שוב.');
  else console.log('טרם נכתבה חלוקה (plan).');
  /* פרומפט 29: פרק אחד בכל הרצה; פרק מעל 30 קטעים - חצי בכל הרצה */
  if (!fs.existsSync(runF(jid))) saveRun(jid, rsN);
  if (part) console.log('פרק ארוך (' + o.total + ' קטעים, ' + part.n + ' חלקים): בהרצה הזאת רק החלק ' + (part.p + 1) + ' - קטעים ' + (part.s0 + 1) + ' עד ' + (part.s1 + 1) + '. החומר לקריאה הוא של החלק בלבד (והסוגיה השלמה בקצוות), ו-context.md נותן את מהלך הפרק כולו. בסוף החלק: pause --reason=סוף-חלק --push, וצא.');
  console.log('פרק אחד בהרצה: אחרי finish (או pause בסוף חלק) - צא. הפרק הבא בהרצה הבאה, בשיחה חדשה.');
  console.log('עצירה לפני סוף החלק (זמן / הקשר / שגיאה): pause ' + jid + ' --reason=<זמן|הקשר|שגיאה|אחר> --push - הסיבה נרשמת ביומן ההרצות.');
} else if (cmd === 'rules') {
  /* פרומפט 69 (19.11.2026): בתענית הכותבים קראו רק חלק מן הלקחים (שורות 1-170), ושלושה כללי צורה שמחוץ לטווח לא הוחלו.
     לכן בראש הפלט - חובות הצורה שהקוד אינו אוכף (או אוכף רק בחלקן), כדי שגם קריאה חלקית תראה אותן */
  console.log('=== חובות צורה שאינן נאכפות בקוד (או נאכפות רק בחלקן) - לכל קטע, לפני put (פרומפט 69) ===\n' + [
    'הדגשה לכל דין במשנה: 2-5 מילים מלשון המשנה לכל דין (מה חייב ומה פטור, מה מותר ומה אסור), מילות המקרה בלבד - לא הדגשה אחת למשנה כולה. הקוד חוסם רק משנה בלי שום הדגשה, ומזהיר על שורת דין בלי הדגשה.',
    '"והך": קושיה (ויקשה / וקשה / והא) ותירוץ קצר שנכנסים יחד בשורה אחת - שורה אחת תחת [צד:והך:] ("הקושיה! - התירוץ"; כלל 21). כשאינם נכנסים בשורה אחת - כותרת הקושיה ומקף התירוץ [צד:-], ולא "והך".',
    'סוגריים מרובעים בגוף השורה, גם בתיבת המשנה - {הס:[...]} (כלל 6א), הסוגריים והמילים כמות שהם. נשארים בלי {הס:} רק לשון הגמרא וציון מקור (נימוק ב-keep).',
    'שם תנא בתיבת המשנה - {אם:...} עם אותיות החיבור, "אומר:" והנקודתיים, גם בתוך ההדגשה ובמקום {מש:} ("{אם:רבי יוסי:}", "ולא הודו לו {אם:חכמים}."; כלל 4). ר"ח כסליו הוא ראש חודש, ב"ד אינו שם.',
    'קוראים את פלט rules ואת docs/sakem-lessons.md במלואם - בלי טווח שורות. מי שמתדרך סוכן - מפנה לקובץ כולו.'
  ].map((x, i) => (i + 1) + '. ' + x).join('\n') + '\n');
  const src = fs.readFileSync(path.join(ROOT, 'worker', 'leokmei-suggest', 'src', 'sakem_prompt.js'), 'utf8');
  const sys = src.slice(src.indexOf('`') + 1, src.lastIndexOf('`')).replace(/\$\{SKC\.LINE\}/g, String(SKC.LINE)).replace(/\\\\n/g, '\\n');
  console.log('=== כללי הניסוח והמבנה של סכם (מקור: worker/leokmei-suggest/src/sakem_prompt.js) ===\n' + sys);
  const ex = rd(path.join(D, 'sakem-examples.json'));
  console.log('\n=== דוגמאות מתיקוני המחבר ===');
  (ex.pairs || []).forEach((p, i) => console.log('\n-- דוגמה ' + (i + 1) + ' (' + (p.kind || '') + ')\nלפני:\n' + p.before + '\nאחרי:\n' + p.after + (p.bad ? '\nפסול:\n' + p.bad : '') + '\nמה שיניתי: ' + (p.changes || []).join(' · ')));
  console.log('\n=== רשימת הבדיקה העצמית (פרומפט 33) - לכל קטע, לפני put, ולאשר בשדה check ===\n' + SKC.SELF_CHECK.map((x) => '- ' + x[0] + ': ' + x[1]).join('\n'));
  console.log('\n=== נבדק בקוד ועוצר את put (פרומפט 33) ===\n- סוגריים מרובעים בגוף השורה בלי {הס:}, גם בתיבת המשנה (פטור לציון מקור / לשון הגמרא - נימוק ב-keep)\n- שם תנא בתיבת המשנה בלי {אם:} (פרומפט 69; ספק - אזהרה)\n- תבליט "•" / "·" והדגשה יתומה {ב:.}\n- ארמית מרשימת ההחלפות שהמנהל כבר עשה: ' + Object.keys(SKC.OBEY_ARAM).map((k) => k + ' - ' + SKC.OBEY_ARAM[k]).join(', ') + '\n- "אם / הא / כש... <מקרה> <דין>" בלי מקף לפני הדין\n- עיטור צמוד לכותרת שלא נמחק (מפרומפט 29)');
  /* פרומפט 70: הצינור החסכוני - ליבה קומפקטית + קבצי הנושא שהעבודה צריכה, במקום כל הלקחים וכל rules.json.
     אף לקח אינו אובד: כל לקח מקורי ממופה (docs/sakem-lean/map.json), ולקח חדש שטרם זוקק מודפס כלשונו */
  if (LEAN) {
    let pkL = null; try { const jj = A[0] || ((runMark() || {}).jid); if (jj) pkL = pkOf(jj); } catch (e) {}
    const LT = await import('./lean.mjs');
    const lt = LT.leanText(pkL);
    if (lt) { console.log('\n=== לקחים מהכרעות המנהל - ליבה ונושאים (הצינור החסכוני, פרומפט 70; גוברים על הכללים שלמעלה) ===\nנושאים שנטענו: ' + lt.topics.join(', ') + (lt.fresh ? ' · לקחים חדשים שטרם זוקקו: ' + lt.fresh : '') + '\n\n' + lt.text);
      process.exit(0); }
    console.log('(הצינור החסכוני: docs/sakem-lean טרם נבנה - מדפיס את הכללים המלאים)');
  }
  const L = path.join(ROOT, 'docs', 'sakem-lessons.md');
  if (fs.existsSync(L)) console.log('\n=== לקחים מהכרעות המנהל (גוברים על הכללים שלמעלה) ===\n' + fs.readFileSync(L, 'utf8'));
  /* המקליט (פרומפט 28): כללים שנלמדו מעריכות המנהל ומהערותיו; כלל שבוטל ב"מה סכם למד" אינו מוצג */
  const LR = path.join(D, 'learn', 'rules.json');
  if (fs.existsSync(LR)) { const on = (rd(LR).rules || []).filter((x) => !x.off);
    if (on.length) console.log('\n=== מה סכם למד מעריכות המנהל (' + on.length + ' כללים פעילים) ===\n' + on.map((x) => '- ' + x.text + (x.was && x.kind !== 'החלפת מילה' ? '\n  לפני: ' + x.was + '\n  אחרי: ' + x.now : '')).join('\n')); }
} else if (cmd === 'orig') {
  /* פרומפט 70: כמה טווחים בבת אחת (orig <jid> <from> <to> <from> <to> ...) או קטעי חלוקה (--segs=3-6), כל אחד בכותרת */
  const jid = A[0], pk = pkOf(jid), sg = (process.argv.find((x) => /^--segs=/.test(x)) || '').slice(7);
  if (sg) { const o = outOf(jid); if (!o) die('קודם plan.'); const [a, b] = sg.split('-').map((x) => +x); 
    for (let i = a; i <= (b || a); i++) { const p = o.plan[i - 1]; if (!p) break; console.log('=== קטע ' + i + ' (⟦' + p.from + '⟧-⟦' + p.to + '⟧) ' + p.title + ' ===\n' + origOf(pk, p.from, p.to).text + '\n'); } }
  else if (A.length > 3) { for (let k = 1; k + 1 < A.length; k += 2) console.log('=== ⟦' + A[k] + '⟧-⟦' + A[k + 1] + '⟧ ===\n' + origOf(pk, A[k], A[k + 1]).text + '\n'); }
  else console.log(origOf(pk, A[1], A[2]).text);
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
} else if (cmd === 'put' && Array.isArray(rd(A[1]))) {
  /* פרומפט 70: put לכמה קטעים בבת אחת (מערך של seg.json) - הכותב כותב רצף ושולח פעם אחת. כל קטע נבדק בשומר כרגיל
     (בתהליך נפרד, בדיוק כמו put יחיד), הקטעים שעברו נשמרים, והליקויים של כל השאר מוחזרים יחד. דחיפה אחת בסוף. */
  const [jid, f] = A, arr = rd(f);
  const flags = process.argv.slice(3).filter((x) => /^--/.test(x) && x !== '--push');
  const ok = [], bad = [];
  arr.forEach((one, k) => {
    const tf = path.join(WORK, jid, 'batch-' + process.pid + '-' + k + '.json');
    fs.mkdirSync(path.dirname(tf), { recursive: true }); fs.writeFileSync(tf, JSON.stringify(one));
    try { const out = execFileSync(process.execPath, [fileURLToPath(import.meta.url), 'put', jid, tf, ...flags], { cwd: ROOT, encoding: 'utf8', env: process.env });
      ok.push(one.seg); console.log('--- קטע ' + one.seg + ' ---\n' + out.trim()); }
    catch (e) { bad.push(one.seg); console.log('--- קטע ' + one.seg + ' (לא נשמר) ---\n' + String(e.stdout || e.message).trim()); }
    try { fs.unlinkSync(tf); } catch (_) {}
  });
  console.log('\nבסך הכול: ' + ok.length + ' נשמרו' + (ok.length ? ' (' + ok.join(', ') + ')' : '') + (bad.length ? ', ' + bad.length + ' נדחו (' + bad.join(', ') + ') - תקן רק אותם ושלח שוב.' : '.'));
  if (PUSH && ok.length && !DRY) { const pk = pkOf(jid), o = outOf(jid); push('סכם: ' + (pk.title || jid) + ' - קטעים ' + ok.join(', ') + ' (' + o.done + ' מתוך ' + o.total + ')', [outF(jid)]); }
  if (bad.length) process.exit(1);
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
  /* פרומפט 71: העבודה נלקחה בידי עובד אחר (הנעילה של ההרצה הזאת מתה ונלקחה) - לא כותבים עליו */
  if (!NOLOCK) { const m = runMark(), l = lockInfo(jid); if (m && m.tok && l && l.tok && l.tok !== m.tok && !l.dead) die('העבודה ' + jid + ' נלקחה בידי עובד אחר (' + l.txt.split('\n')[0] + ') אחרי שההרצה הזאת לא דחפה 40 דקות. אל תכתוב עליה - צא.'); }
  const rs = runState(jid), PB = runBounds(rs, o);
  if (PB) { const part = partIx(PB, si) + 1; if (!rs.part) { rs.part = part; saveRun(jid, rs); }
    else if (rs.part !== part) die('הקטע ' + (si + 1) + ' שייך לחלק ' + part + ' מתוך ' + (PB.length - 1) + ' של הפרק, וההרצה הזאת עובדת על החלק ' + rs.part + ' (קטעים ' + (PB[rs.part - 1] + 1) + ' עד ' + PB[rs.part] + ').\nסיים את ההרצה (node tools/sakem/runner.mjs pause ' + jid + ' --reason=סוף-חלק --push) וצא. החלק האחר - בהרצה הבאה, בשיחה חדשה.'); }
  const cx = ctxOf(pk, r);
  /* פרומפט 33 (12.11.2026): רשימת הבדיקה העצמית - מה שאי אפשר לבדוק בקוד. הכותב עובר עליה בכל קטע (גם "ללא שינוי")
     ומאשר כל סעיף בשדה check של seg.json. סעיף שחסר - put נעצר */
  { const miss = SKC.selfCheckMissing(s.check);
    if (miss.length) die('רשימת הבדיקה העצמית לא אושרה (פרומפט 33). עבור על כל סעיף בקטע הזה, תקן מה שצריך, והוסף ל-seg.json:\n"check": {' + SKC.SELF_CHECK.map((x) => '"' + x[0] + '": true').join(', ') + '}\nהסעיפים שחסרים:\n' + miss.map((x) => '- ' + x[0] + ': ' + x[1]).join('\n')); }
  if (s.nochange) {
    const q0 = SKC.quality(r.text, { mishna });
    if (q0.length) die('אי אפשר "ללא שינוי": הנוסח הקיים פגום - ' + q0.slice(0, 6).join(' · ') + '\nתקן בהצעה.');
    /* פרומפט 28: גם "ללא שינוי" עובר את בודק הציות (משנה בלי הדגשת עיקר); פרומפט 29: במצב המשימה (עיטור, רווח, מקף) */
    const c0 = SKC.comply(r.text, r.text, Object.assign({ strict: true, keep: s.keep }, cx));
    if (c0.errs.length) die('אי אפשר "ללא שינוי": ' + c0.errs.join(' · ') + '\nתקן בהצעה.');
    if (DRY) { console.log('השומר: עבר (ללא שינוי). לא נשמר דבר (--dry).'); process.exit(0); }
    o.items.push({ iid: 's' + (si + 1), kind: 'seg', seg: si, sugya: seg.sugya, ids: r.ids, nochange: true, keep: s.keep || [], stat: c0.stat }); /* פרומפט 58: הנימוק נשמר, כדי ש-finish לא ייעצר על מה שכבר נומק */
  } else {
    let text = String(s.text || '').replace(/\r/g, '').trim();
    if (!text) die('אין text');
    /* פרומפט 22: כותרת צד ארוכה וכפילות ברורה אחרי כותרת - תיקון אוטומטי לפני השומר */
    { const af = SKC.autofixTitles(text); if (af.changed) { text = af.text; s.changes = (s.changes || []).concat(af.notes.map((x) => 'אוטומטי: ' + x)); } }
    /* פרומפט 28 (9.11.2026): כללי צורה של בעל הפרויקט, בקוד ולא רק בהנחיה - דובר בפתח שורה לכותרת צד, אות ומילה
       נסמכות לשם בסגנון האמורא, רווח לפני גופא / ת"ר / אמר מר. אינם משנים מילה בנוסח */
    { const ff = SKC.autofixForm(text, { orig: r.text }); if (ff.changed) { text = ff.text; s.changes = (s.changes || []).concat(ff.notes.map((x) => 'אוטומטי: ' + x)); } }
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
    /* פרומפט 38 (15.11.2026): אותה בדיקה שהדף מריץ ב"קבל" (SKC.acceptPrep + SKC.acceptErrs) - הצעה שהדף ידחה אינה נמסרת */
    { const ac = SKC.acceptErrs(rT, SKC.acceptPrep(rT, tT).text).filter((x) => ck.errs.indexOf(x) < 0); if (ac.length) ck.errs = ck.errs.concat(ac.map((x) => 'הדף ידחה בקבלה: ' + x)); }
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
  rs.puts = (rs.puts || 0) + 1; saveRun(jid, rs); /* פרומפט 70: גם put חוזר (תיקון) נספר - "0 קטעים" ביומן אינו בהכרח הרצה ריקה */
  const it = o.items.find((x) => x.seg === si && x.kind === 'seg');
  console.log('קטע ' + (si + 1) + ' נשמר' + (it.nochange ? ' (ללא שינוי)' : ' · ' + it.layers.join(', ') + (it.warn.length ? ' · אזהרות: ' + it.warn.join(' · ') : '')) + ' · ' + o.done + ' מתוך ' + o.total);
  if (PUSH) push('סכם: ' + (pk.title || jid) + ' - קטע ' + (si + 1) + ' מתוך ' + o.total, [outF(jid)]);
  /* פרומפט 29: סוף החצי הראשון של פרק ארוך - עוצרים כאן; החצי השני בשיחה חדשה, שקוראת את הכללים מחדש */
  if (PB && rs.part < PB.length - 1 && o.plan.slice(PB[rs.part - 1], PB[rs.part]).every((p, i) => o.items.some((x) => x.seg === PB[rs.part - 1] + i)))
    console.log('\nהחלק ' + rs.part + ' מתוך ' + (PB.length - 1) + ' הושלם (קטעים ' + (PB[rs.part - 1] + 1) + ' עד ' + PB[rs.part] + '). הרץ: node tools/sakem/runner.mjs pause ' + jid + ' --reason=סוף-חלק --push, וצא. החלק הבא - בהרצה הבאה.');
} else if (cmd === 'pause') {
  /* סוף הרצה באמצע פרק (חצי ראשון, או זמן שנגמר): שורה ביומן ההרצות, ויציאה */
  const [jid] = A;
  const pk = pkOf(jid), o = outOf(jid);
  if (!o) die('אין הצעות.');
  /* פרומפט 71: כל pause רושם את הסיבה - סוף חלק / זמן / הקשר / שגיאה / אחר - כדי שהרצה שעוצרת מוקדם תתגלה מיד */
  const rs = runState(jid), PB = runBounds(rs, o);
  const partDone = !!(PB && rs.part && o.plan.slice(PB[rs.part - 1], PB[rs.part]).every((p, i) => o.items.some((x) => x.seg === PB[rs.part - 1] + i)));
  const R = { 'סוף-חלק': 'סוף חלק', 'זמן': 'זמן', 'הקשר': 'הקשר', 'שגיאה': 'שגיאה', 'אחר': 'אחר' };
  let reason = ((process.argv.find((x) => /^--reason=/.test(x)) || '').slice(9)).trim();
  if (!reason) reason = partDone ? 'סוף-חלק' : '';
  const why = R[reason] || (reason ? 'אחר: ' + reason : 'לא צוין');
  if (!reason) console.log('אזהרה: pause באמצע חלק בלי --reason=<זמן|הקשר|שגיאה|אחר>. נרשם "לא צוין" - ציין בפעם הבאה.');
  const early = !partDone && o.done < o.total;
  const rec = logRun(jid, pk, o, 'pause', { reason: why, early });
  console.log('נרשם ביומן ההרצות: ' + rec.segsThisRun + ' קטעים בהרצה הזאת, ' + o.done + ' מתוך ' + o.total + ' בסך הכול · סיבה: ' + why + (early ? ' (עצירה לפני סוף החלק)' : '') + '.');
  if (PUSH) push('סכם: ' + (pk.title || jid) + ' - סוף הרצה (' + o.done + ' מתוך ' + o.total + ', ' + why + ')', [outF(jid), RUNS, ...lockFree(jid)]);
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
    /* פרומפט 56 ד5: בסבב השני - כמה איחודים, כמה כותרות חדשות, כמה מטבעות לשון תוקנו, כמה שורות גולשות נשארו (היעד 0) */
    { const COIN = /שונה כאן|לשון אחרת|(?:^|\s)ו?יש ביניהם|מה ביניהם|שנינו שם/;
      let merges = 0, newTitles = 0, coins = 0, over = 0;
      segs.forEach((x) => { if (x.nochange) return;
        const r = origOf(pk, x.ids[0], x.ids[x.ids.length - 1]);
        const L = (t) => String(t || '').split('\n').filter((l) => l.trim() && !/^\[/.test(l.trim()));
        const a = L(r.text), b = L(x.text);
        if (b.length < a.length) merges += a.length - b.length;
        newTitles += Math.max(0, b.filter((l) => /^\(נושא\)/.test(l)).length - a.filter((l) => /^\(נושא\)/.test(l)).length);
        coins += Math.max(0, a.filter((l) => COIN.test(SKC.plainI(l))).length - b.filter((l) => COIN.test(SKC.plainI(l))).length);
        over += b.filter((l) => !/^\(נושא\)/.test(l) && SKC.plainI(l).length > (SKC.LINE_BIG || 52)).length; });
      o.score.round2 = { merges, newTitles, coins, overLeft: over };
      console.log('סבב שני: ' + JSON.stringify(o.score.round2)); }
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
  if (PUSH) push('סכם: ' + (pk.title || jid) + ' - מוכן לסקירה', [outF(jid), RUNS].concat(fs.existsSync(path.join(D, 'learn', 'rules.json')) ? [path.join(D, 'learn', 'rules.json')] : []).concat(lockFree(jid)));
  /* פרומפט 56 ד6: כשהעבודה האחרונה של שבת בסבב השני מגיעה ל"מוכן לסקירה" - התראה אחת למיכאל (ווטסאפ לעצמו, מייל, דחיפה).
     ווטסאפ: notify-me.sh של zohar-nikud (תור ההתראות). המייל והדחיפה - בידי העובד, לפי ההודעה שמודפסת כאן */
  if (/סבב שני/.test(pk.title || '') && pk.slug === 'shabbat') {
    const all = fs.readdirSync(path.join(D, 'out')).filter((f) => f.endsWith('.json') && !f.endsWith('.old.json')).map((f) => { try { return rd(path.join(D, 'out', f)); } catch (e) { return null; } })
      .filter((x) => x && x.slug === 'shabbat' && /סבב שני/.test(x.title || ''));
    const q = fs.existsSync(path.join(D, 'queue')) ? fs.readdirSync(path.join(D, 'queue')).filter((f) => f.endsWith('.json')).map((f) => { try { return rd(path.join(D, 'queue', f)); } catch (e) { return null; } })
      .filter((x) => x && x.slug === 'shabbat' && /סבב שני/.test(x.title || '')) : [];
    const open = q.filter((p0) => { const ox = all.find((x) => x.jid === ((p0.job || {}).jid)); return !ox || ox.status !== 'ready'; });
    if (!open.length && all.length) {
      const props = all.reduce((n, x) => n + (x.items || []).filter((i) => !i.nochange).length, 0);
      const msg = 'שבת מוכנה לסקירה: ' + all.length + ' פרקים, ' + props + ' הצעות\nhttps://leokmei.com/shabbat.html';
      const NS = '/home/user/zohar-nikud/זוהר-דף-כלים/notify-me.sh';
      try { if (fs.existsSync(NS)) execFileSync('bash', [NS, msg], { stdio: 'inherit' }); } catch (e) { console.log('הווטסאפ לא נשלח: ' + e.message); }
      console.log('\n######## התראה למיכאל (פרומפט 56 ד6) - שלח גם מייל ל-m7654301@gmail.com והודעת דחיפה, ואז הפעל zyomi-wa.yml במצב notify:\n' + msg);
    }
  }
} else if (cmd === 'lessons') {
  const stF = path.join(D, 'lessons-state.json'), st = fs.existsSync(stF) ? rd(stF) : { done: [] };
  /* 6.11.2026: סבב שני על אותו פרק (אותו jid) נשא הכרעות חדשות והן דולגו. המפתח הוא עכשיו jid@זמן העבודה */
  const dkey = (j) => j + '@' + (((rd(path.join(DEC, j + '.json')) || {}).job || {}).t || '');
  const todo = ls(DEC).map((f) => f.slice(0, -5)).filter((j) => st.done.indexOf(dkey(j)) < 0);
  /* המקליט (פרומפט 28): דפוסים חדשים מעריכות המנהל, הערות "הערה לקלוד" ושיחות לוח הסקירה שטרם נקראו */
  const since = st.learnT || 0, LRf = path.join(D, 'learn', 'rules.json'), PTf = path.join(D, 'learn', 'patterns.json');
  const nr = fs.existsSync(LRf) ? (rd(LRf).rules || []).filter((x) => (x.t || 0) > since) : [];
  if (nr.length) console.log('\n######## כללים חדשים שנקלטו מאז הפעם הקודמת (' + nr.length + ')\n' + nr.map((x) => '- ' + (x.off ? '[בוטל] ' : '') + x.text).join('\n'));
  /* 10.11.2026: כל עריכה של המנהל אחרי סכם (בדף עצמו, מחוץ לחלון הסקירה) - אחת אחת, ולא רק כמניין.
     עריכה שאינה חוזרת אינה נעשית כלל אוטומטי, ולכן היא מוצגת כאן כדי שתנותח ותיכתב ממנה לקח.
     פרומפט 32 (12.11.2026): "נותח עד" לכל מסכת לפי מספר הרשומות בקובץ המקליט (st.post), ולא לפי זמן העריכה -
     עריכה שנקלטה אחרי lessons-done אבל נעשתה לפניו דולגה. ושינויי מבנה (כותרת צד, פיצול, מחיקת עיטור) מוצגים
     עם הנוסח, לא רק כסוג. "היה" הוא מה שסכם השאיר בדף (אחרי הקבלה), "נעשה" - התיקון של המנהל. */
  const ER = [], NOW = {}, LDIR = path.join(D, 'learn'), PST = st.post || {};
  if (fs.existsSync(LDIR)) for (const f of fs.readdirSync(LDIR).filter((x) => x.endsWith('.jsonl'))) {
    const slug = f.replace(/\.jsonl$/, ''), L = fs.readFileSync(path.join(LDIR, f), 'utf8').split('\n');
    NOW[slug] = L.filter(Boolean).length;
    const from = PST[slug], seen = new Set();
    let n = 0;
    for (const l of L) { if (!l) continue; n++; let r; try { r = JSON.parse(l); } catch (e) { continue; }
      if (from !== undefined ? n <= from : (r.t || 0) <= since) continue;
      if (!r.post || r.src) continue;
      const key = [r.k, r.t, r.was, r.now, r.kind].join('|');
      if (seen.has(key)) continue; seen.add(key);
      ER.push(Object.assign({ slug, _n: n }, r)); }
  }
  const q = (x) => '"' + String(x || '').trim().slice(0, 90) + '"';
  const structTxt = (r) => { const t = r.texts || [], R = r.resT || [];
    if (!t.length && !R.length) return ' מבנה: ' + (r.kind || '') + ' (בלי נוסח - רשומה ישנה)';
    if (r.kind === 'side') return ' כותרת צד חדשה ' + q(R[1]) + ' בראש ' + q(R[0]);
    if (r.kind === 'unside') return ' כותרת צד הוחזרה לגוף: ' + q(R[0]);
    if (r.kind === 'hdel') return ' עיטור נמחק, בין ' + q(t[0]) + ' ובין ' + q(t[1]);
    if (r.kind === 'hrep') return ' עיטור הוחלף בכותרת ' + q(R[0]);
    if (r.kind === 'split' || r.kind === 'hsplit') return ' ' + (r.ins ? 'שורה חדשה' : 'פיצול שורה') + ': ' + q(R[0]) + ' | ' + q(R[1]);
    if (r.kind === 'merge' || r.kind === 'hmerge' || r.kind === 'unside-merge') return ' איחוי שורות: ' + t.map(q).join(' + ');
    return ' מבנה: ' + (r.kind || '') + ' ' + t.map(q).join(' | '); };
  if (ER.length) {
    ER.sort((a, b) => a.t - b.t);
    const by = {}; ER.forEach((r) => { by[r.slug] = (by[r.slug] || 0) + 1; });
    console.log('\n######## עריכות המנהל אחרי סכם, מחוץ לסקירה (' + ER.length + ': ' + Object.entries(by).map(([k, v]) => k + ' ' + v).join(', ') + ') - חובה לנתח (פרומפט 32).\nכל אחת היא הערה על סכם: מה סכם היה צריך לעשות ולא עשה. השווה "היה" (מה שסכם השאיר) ל"נעשה" (המנהל), וכתוב ל-docs/sakem-lessons.md כלל מותנה קצר לכל מה שאינו תיקון מקומי - עם סיבה ותאריך, בלי כפילות. כותרות נושא וכותרות צד, מקף תירוץ, הדגשה, רווח, ארמית מול לשון הקודש, הידוק שהוחזר.');
    ER.slice(0, 400).forEach((r) => console.log('\n- [' + r.slug + ' ' + (r.daf || '') + '] ' + (r.op === 'struct' ? structTxt(r) : r.cls + (r.sub ? '/' + r.sub : '') + '\n  היה: ' + (r.wasH || r.was || '') + '\n  נעשה: ' + (r.nowH || r.now || ''))));
    if (ER.length > 400) console.log('\n(ועוד ' + (ER.length - 400) + ' - בהרצה הבאה)');
  }
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
  if (!todo.length && !nr.length && !ER.length) die('אין הכרעות חדשות.', 0);
  todo.forEach((jid) => {
    const d = rd(path.join(DEC, jid + '.json'));
    const c = {}; (d.log || []).forEach((x) => { if (x.act === 'undo') return; (x.layers || ['?']).forEach((L) => { c[L] = c[L] || {}; c[L][x.act] = (c[L][x.act] || 0) + 1; }); });
    console.log('\n######## ' + jid + ' · ' + ((d.job || {}).title || '') + '\nסיכום לפי שכבה: ' + JSON.stringify(c));
    (d.log || []).filter((x) => x.act === 'reject' || x.act === 'edit').forEach((x) => {
      console.log('\n--- ' + x.iid + ' · ' + (x.act === 'edit' ? 'נערך' : 'נדחה') + ' · ' + (x.layers || []).join(', ') + '\nמקור:\n' + x.orig + '\nהצעה:\n' + x.prop + (x.final ? '\nמה שהמנהל כתב:\n' + x.final : '') + (x.gem ? '\nלשון הגמרא: ' + x.gem : ''));
    });
  });
  /* --post: עד איפה נותחו עריכות המנהל בכל מסכת (מספר הרשומות כפי שהוצגו עכשיו).
     15.11.2026: כשיש יותר מ-400, רק הראשונות הוצגו. בלי --post היה lessons-done מסמן הכל עד סוף הקובץ,
     והעריכות שלא הוצגו נחשבו כאילו נותחו. לכן תמיד --post: במסכת שיש בה עריכה שלא הוצגה - עד השורה
     שלפני הראשונה שלא הוצגה (כך אף אחת אינה מדולגת), ובשאר המסכתות - עד סוף הקובץ. */
  const POST = Object.assign({}, NOW);
  ER.slice(400).forEach((r) => { POST[r.slug] = Math.min(POST[r.slug], r._n - 1); });
  const postArg = ' --post=' + Object.entries(POST).map(([k, v]) => k + ':' + v).join(',');
  console.log('\nאחרי שכתבת את הלקחים: node tools/sakem/runner.mjs lessons-done ' + todo.join(' ') + postArg + ' --push' +
    '\nכלל שנלמד מעריכות המנהל מגיע גם לדף "מה סכם למד": כתוב אותו גם בקובץ JSON [{"text":"...","was":"...","now":"..."}] והוסף --rules=<הקובץ>.');
} else if (cmd === 'lessons-done') {
  const stF = path.join(D, 'lessons-state.json'), st = fs.existsSync(stF) ? rd(stF) : { done: [] };
  const dk2 = (j) => { const f = path.join(DEC, j + '.json'); return fs.existsSync(f) ? j + '@' + ((rd(f).job || {}).t || '') : j; };
  st.done = [...new Set(st.done.concat(A.map(dk2)))];
  st.learnT = Date.now();
  /* פרומפט 32: "נותח עד" לעריכות המנהל אחרי סכם, לכל מסכת. בלי --post - עד סוף הקבצים עכשיו */
  const pa = (process.argv.find((x) => x.startsWith('--post=')) || '').slice(7);
  const LDIR = path.join(D, 'learn');
  st.post = st.post || {};
  if (pa) pa.split(',').filter(Boolean).forEach((x) => { const [k, v] = x.split(':'); if (k && +v >= 0) st.post[k] = +v; });
  else if (fs.existsSync(LDIR)) fs.readdirSync(LDIR).filter((x) => x.endsWith('.jsonl')).forEach((f) => { st.post[f.replace(/\.jsonl$/, '')] = fs.readFileSync(path.join(LDIR, f), 'utf8').split('\n').filter(Boolean).length; });
  /* כללים שנלמדו מעריכות המנהל - אל רשימת הכללים (data/sakem/learn/rules.json): כך הם מוצגים לסכם ב-rules,
     ועולים בסנכרון לדף המנהל "מה סכם למד" (עם "בטל כלל") */
  const ra = (process.argv.find((x) => x.startsWith('--rules=')) || '').slice(8), LRf = path.join(LDIR, 'rules.json'), extra = [];
  if (ra) {
    const NR = rd(path.resolve(ra)), RL = fs.existsSync(LRf) ? rd(LRf) : { rules: [] }, have = new Set(RL.rules.map((x) => x.id));
    let k = 0;
    for (const x of Array.isArray(NR) ? NR : []) {
      if (!x || !String(x.text || '').trim()) continue;
      const id = 'post:' + String(x.text).replace(/\s+/g, ' ').trim().slice(0, 60);
      if (have.has(id)) continue;
      RL.rules.push({ id, t: Date.now(), kind: 'לקח מעריכות המנהל', target: 'לקחים', n: 1, src: 'עריכות המנהל אחרי סכם', text: String(x.text).trim(), was: String(x.was || ''), now: String(x.now || '') });
      have.add(id); k++;
    }
    wr(LRf, RL); extra.push(LRf);
    console.log('נוספו לרשימת הכללים (ולדף "מה סכם למד"):', k);
  }
  wr(stF, st);
  console.log('סומן.');
  if (PUSH) push('סכם: לקחים מהכרעות המנהל', [stF, path.join(ROOT, 'docs', 'sakem-lessons.md')].concat(extra));
} else {
  die('פקודה לא מוכרת. ראה docs/sakem-runner.md');
}
