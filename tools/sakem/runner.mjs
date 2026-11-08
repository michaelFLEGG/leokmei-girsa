/* סכם - כלי העבודה של המשימה המתוזמנת בענן (פרומפט 15, 28.10.2026).
   ההוראות המלאות: docs/sakem-runner.md. הכלי אינו קורא לשום מודל: הוא מכין את החומר לקריאה,
   בודק כל הצעה בשומר של סכם (tools/sakem_core.js - אותו שומר שבדף), ושומר התקדמות אחרי כל קטע.

   node tools/sakem/runner.mjs status                    התור ומצב כל עבודה
   node tools/sakem/runner.mjs next [jid]                העבודה הבאה (או עבודה מסוימת) (או "התור ריק", קוד יציאה 3) והכנת חומר הקריאה
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

const cmd = process.argv[2], A = process.argv.slice(3).filter((x) => x !== '--push' && x !== '--dry'), PUSH = process.argv.includes('--push'), DRY = process.argv.includes('--dry');

if (cmd === 'status') {
  const js = ls(Q);
  if (!js.length) die('התור ריק.', 0);
  js.forEach((f) => { const jid = f.slice(0, -5), pk = rd(path.join(Q, f)), o = outOf(jid);
    console.log(jid, '·', pk.title || '', '·', o ? (o.status === 'ready' ? 'מוכן לסקירה' : 'בעבודה ' + o.done + '/' + o.total) : 'ממתין'); });
} else if (cmd === 'next') {
  /* next <jid>: עבודה מסוימת (כמה עובדים במקביל, כל אחד על פרק אחר; 6.11.2026) */
  const jid = ls(Q).map((f) => f.slice(0, -5)).find((j) => { const o = outOf(j); return (!A[0] || j === A[0]) && (!o || o.status !== 'ready'); });
  if (!jid) die('התור ריק.', 3);
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
  /* פרומפט עבודה גרסה 2: לשון המשניות של הפרק (data/mishna), לבדיקת תיבת המשנה; ו"ללא שינוי" אינו מותר כשהנוסח הקיים פגום */
  const mishna = mishnaOf(pk);
  if (s.nochange) {
    const q0 = SKC.quality(r.text, { mishna });
    if (q0.length) die('אי אפשר "ללא שינוי": הנוסח הקיים פגום - ' + q0.slice(0, 6).join(' · ') + '\nתקן בהצעה.');
    o.items.push({ iid: 's' + (si + 1), kind: 'seg', seg: si, sugya: seg.sugya, ids: r.ids, nochange: true });
  } else {
    let text = String(s.text || '').replace(/\r/g, '').trim();
    if (!text) die('אין text');
    /* פרומפט 22: כותרת צד ארוכה וכפילות ברורה אחרי כותרת - תיקון אוטומטי לפני השומר */
    { const af = SKC.autofixTitles(text); if (af.changed) { text = af.text; s.changes = (s.changes || []).concat(af.notes.map((x) => 'אוטומטי: ' + x)); } }
    const gem = (pk.pages || []).filter((p) => r.ids.some((id) => (pk.units.find((u) => u.id === id) || {}).daf === p.daf)).map((p) => (p.g || []).map(strip).join(' ')).join(' ');
    /* הקשר המספור (6.11.2026): רשימה שהתחילה לפני הקטע או נמשכת אחריו. בקטע הראשון של הפרק - הרשימה עשויה
       להתחיל בפרק הקודם (סוכה ה, "ב. ג." אחרי "א." של פרק ד): אז ההקשר הוא המספר שהנוסח המקורי פותח בו */
    let before = SKC.toInter(pk.units.slice(Math.max(0, r.a - 3), r.a)).text;
    const after = SKC.toInter(pk.units.slice(r.b + 1, r.b + 4)).text;
    const n0 = (SKC.nums(r.text) || [])[0] || 0;
    if (r.a === 0 && n0 > 1) before = 'אבגדהוזחטי'[n0 - 2] + '. ';
    const ck = SKC.check(r.text, text, { gemara: gem, mishna, before, after });
    /* אורך: בסכם פרק השלמה מהגמרא, גזע שנכתב או מספור עשויים להאריך - אזהרה למנהל, לא חסימה */
    const LEN = /קצר מהמקור|ארוך מהמקור/;
    ck.warns = (ck.warns || []).concat(ck.errs.filter((e) => LEN.test(e)));
    ck.errs = ck.errs.filter((e) => !LEN.test(e));
    if (ck.errs.length) die('השומר דחה: ' + ck.errs.join(' · ') + '\nתקן והרץ שוב.');
    /* פרומפט 26 (8.11.2026): הידוק יתר - קורא נפרד. שורה שקוצצה ביותר מחצי (או קטע שירד מתחת ל-65%) נשלחת
       לקורא שאינו רואה את המקור ולא את הגמרא (סוכן-משנה נפרד בהקשר נקי), והוא כותב במשפט מה השורה אומרת.
       seg.json: "read": [{"line": "<השורה כפי שבהצעה>", "said": "<מה הקורא הבין>", "ok": true|false}].
       ok=false (לא הבין, או הבין אחרת מן המקור) - כותבים את השורה מחדש בפחות הידוק. */
    const sq = SKC.squeeze(r.text, text);
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
                   changes: (s.changes || []).map(String).slice(0, 6), layers, skipped: String(s.skipped || ''), adds, warn: ck.warns || [], read });
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
  /* 6.11.2026: סבב שני על אותו פרק (אותו jid) נשא הכרעות חדשות והן דולגו. המפתח הוא עכשיו jid@זמן העבודה */
  const dkey = (j) => j + '@' + (((rd(path.join(DEC, j + '.json')) || {}).job || {}).t || '');
  const todo = ls(DEC).map((f) => f.slice(0, -5)).filter((j) => st.done.indexOf(dkey(j)) < 0);
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
  const dk2 = (j) => { const f = path.join(DEC, j + '.json'); return fs.existsSync(f) ? j + '@' + ((rd(f).job || {}).t || '') : j; };
  st.done = [...new Set(st.done.concat(A.map(dk2)))];
  wr(stF, st);
  console.log('סומן.');
  if (PUSH) push('סכם: לקחים מהכרעות המנהל', [stF, path.join(ROOT, 'docs', 'sakem-lessons.md')]);
} else {
  die('פקודה לא מוכרת. ראה docs/sakem-runner.md');
}
