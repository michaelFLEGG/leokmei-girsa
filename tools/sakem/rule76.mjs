/* כלל 30 של סכם - מילת המקף ו"והקשה" בכותרת הצד (פרומפט 76, 22.11.2026, הכרעת בעל הפרויקט).
   העיקרון: את מילת הפעולה של השורה מעלים לכותרת הצד, והשורה נשארת לתוכן. מי שקורא רק את המסילה רואה את שלד
   הסוגיא כסולם: «והקשה רב» / «- שאני» / «- דחי» / «תיובתא».

   סבב ממוקד בכלל הזה בלבד, דרך המנגנון של "סכם פרק": החבילה היא בדיוק מה שהכפתור בונה מן הנוסח החי (order),
   נרשמת דרך jobs-put, והסנכרון נותן לה מזהה ותור. הכלי אינו כותב ואינו מחשב את הפרק מהתחלה: הוא נוגע רק ביחידות
   שהכלל חל עליהן, וכל שינוי עולה כהצעה ב"סקור סכם" (out/<jid>.json, status ready) - אין החלה ישירה.

   שני שלבים, כמו בכלל (סייג 2 - "קודם מרימים, ורק אחר כך מוסיפים"):
   א. מכני, בקוד בלבד: מקף בלי מילה ושורה שפותחת באלא / שאני / כאן / ויקשה - המילה עוברת לכותרת ונמחקת מן השורה.
      כותרת צד של שם ושורה שפותחת בויקשה / והקשה / והרי - "והקשה X", והמילה נמחקת.
   ב. בינה מלאכותית, רק על השורות שנותרו (cands): מקף בלי מילה, ושורת קושיא ותירוץ בשורה אחת ("...! - תירוץ").
      הבחירה נכתבת לקובץ choices.json, ורק סוג ודאי. בספק - המקף נשאר לבדו (סייג 1).

   node tools/sakem/rule76.mjs cands <jid> [--json f]          השלב המכני + רשימת המועמדים לשלב ב
   node tools/sakem/rule76.mjs apply <jid> [choices.json] [--dry]  כותב את ההצעות ל-data/sakem/out/<jid>.json
   node tools/sakem/rule76.mjs learn                          הכרעות המנהל על סבבי הכלל -> data/sakem/learn/rule76.json
   node tools/sakem/rule76.mjs order <slug>[:1,2] ... | --all [--dry]
        חבילות מן הדף החי (דפדפן, כמבקר, כל בקשה שאינה GET נחסמת) -> data/sakem/jobs-put/<slug>-p<n>-p76.json.
        --all = כל המסכתות שכבר עברו סכם (יש להן out/<slug>-p<n>.json). זו הפקודה האחת להרחבה, אחרי הכרעות המנהל.
   מקור <jid> - data/sakem/queue/<jid>.json, או קובץ חבילה (גוף jobs-put) לבדיקה מקומית. */
import fs from 'fs';
import path from 'path';
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const SKC = require('../sakem_core.js');
const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..', '..');
const D = path.join(ROOT, 'data', 'sakem');
const NL = '\n';
const ARGV = process.argv.slice(2), FLAGS = new Set(ARGV.filter((x) => /^--/.test(x)));
const POS = ARGV.filter((x, i) => !/^--/.test(x) && ARGV[i - 1] !== '--json');
const optV = (k) => { const i = ARGV.indexOf(k); return i > -1 ? ARGV[i + 1] : null; };
const rd = (f) => JSON.parse(fs.readFileSync(f, 'utf8'));
const die = (m) => { console.error('עצירה: ' + m); process.exit(2); };

/* סוגי התירוץ של הכלל (סעיף א) */
const TYPES = { 'אלא': 'חוזר בו מן ההנחה, או מפרש אחרת', 'שאני': 'חילוק בין המקרים', 'מדובר': 'אוקימתא - העמדה במקרה מסוים',
  'כאן': 'שני מקורות סותרים, כל אחד במקרה אחר', 'דחי': 'הראיה נדחית', 'חסורי': 'הגהה בברייתא' };
const LIFT = ['אלא', 'שאני', 'כאן', 'ויקשה'];         /* מילים שעולות מן השורה לכותרת במקף - מכני */
const ASK = ['ויקשה', 'והקשה', 'והרי'];                /* פתיחת קושיא של הדובר שבכותרת */
const NAME = /^(?:ו?(?:רב|רבי|רבן|ר'|רבא|רבה|אביי|רבינא|שמואל|עולא|זעירי|לוי|חזקיה|ריש|מר|אמימר|רבנן|חכמים)(?:\s|$)|[א-ת]*"[א-ת]+$)/;
const plain = (s) => SKC.plainI(String(s || '')).replace(/\s+/g, ' ').trim();
const letters = (t) => String(t).split(NL).map((l) => (/^\[(?!צד:)/.test(l.trim()) ? l.trim() : SKC.plainI(l.replace(/^\[צד:(.*)\]$/, '$1').replace(/^\((?:תשובה|רווח|מעוין|נושא|דה|רקע|נקודה|משנה)\)\s*/, '')))).join('').replace(/[\s:]+/g, '');

function pkOf(j) {
  const q = path.join(D, 'queue', j + '.json');
  if (fs.existsSync(q)) { const p = rd(q); return Object.assign({ jid: j }, p.packet || p, { title: p.title || (p.job || {}).title, perek: p.perek || (p.job || {}).perek, slug: p.slug || (p.packet || {}).slug }); }
  if (fs.existsSync(j)) { const p = rd(j); return Object.assign({ jid: path.basename(j, '.json') }, p.packet || p, { title: p.title, perek: p.perek, slug: p.slug }); }
  die('אין עבודה כזו בתור: ' + j);
}
/* שורות היחידה: הפסקה הראשונה (אחרי כותרת הצד) - שם נמצאת מילת הפעולה */
function unitInter(u) { return SKC.toInter([u]).text; }
/* פתיחת שורה: סגנון בראש השורה ((רווח) וכדומה) נשמר, והמילה הראשונה נבדקת */
function lead(line) { const m = /^(\([^)]+\)\s*)?/.exec(line); return m[0]; }
function firstWord(line) {
  const L = lead(line), rest = line.slice(L.length), m = /^([א-ת"']+)([,:]?)(\s+|$)/.exec(rest);
  return m ? { w: m[1], len: m[0].length, L } : null;
}
/* מחיקת המילה הראשונה של השורה (עם פסיק או נקודתיים צמודים) */
function stripFirst(line) { const f = firstWord(line); return f ? f.L + line.slice(f.L.length + f.len) : line; }

/* ---- זיהוי: כל יחידה בפרק, אילו מן הכלל חלים בה ---- */
function scan(pk) {
  const R = [], learnt = learned();
  pk.units.forEach((u, ui) => {
    if (u.k !== 'u') return;
    const t = unitInter(u), L = t.split(NL);
    const si = L.findIndex((l) => /^\[צד:/.test(l)), body = L.findIndex((l, i) => i > si && !/^\[/.test(l));
    if (si > -1 && body === si + 1) {
      const title = L[si].slice(4, -1), tp = plain(title);
      /* א. מקף בלי מילה */
      if (/^-\s*$/.test(tp)) {
        const f = firstWord(L[body]), w = f && f.w.replace(/^ו(?=אלא|שאני|כאן)/, '');
        if (f && LIFT.includes(f.w)) R.push({ ui, id: u.id, kind: 'dash', mech: true, type: f.w === 'ויקשה' ? 'ויקשה' : f.w, strip: f.w, why: 'השורה פתחה במילה "' + f.w + '" - עלתה לכותרת (שלב מכני)' });
        else R.push({ ui, id: u.id, kind: 'dash', mech: false, line: plain(L[body]), w: w || '' });
      }
      /* ב. "והקשה X": כותרת של שם, והשורה פותחת בקושיא שלו */
      const nm = tp.replace(/:$/, '').trim();
      if (!/^-/.test(tp) && NAME.test(nm) && !/^(?:והקשה|ויקשה|וקשה|קשה|והך|והרי)/.test(nm)) {
        const f = firstWord(L[body]);
        if (f && ASK.includes(f.w)) {
          const words = nm.split(/\s+/), short = words.length === 1 ? nm : abbr(nm);
          R.push({ ui, id: u.id, kind: 'vehikshe', mech: !!short, type: 'והקשה', name: short || nm, strip: f.w, line: plain(L[body]),
            why: short ? 'כותרת של דובר והשורה פתחה ב"' + f.w + '" - "והקשה ' + short + '" (שלב מכני)' : 'שם של שתי מילים בלי ראשי תיבות ידועים - לשלב ב' });
        }
      }
    }
    /* ג. קושיא ותירוץ בשורה אחת: "...! - תירוץ" - המילה אחרי המקף שבתוך השורה, בסגנון אמוראים (סייג 6) */
    L.forEach((l, li) => {
      if (/^\[/.test(l)) return;
      const m = /[!?]\}?\s+-\s+/.exec(l); if (!m) return;
      const after = l.slice(m.index + m[0].length), f = /^([א-ת"']+)([,:]?)\s/.exec(SKC.plainI(after));
      if (/^\{אם:(?:אלא|שאני|מדובר|כאן|דחי|חסורי)\b/.test(after)) return;    /* כבר יש מילה */
      if (f && LIFT.slice(0, 3).includes(f[1]) && after.startsWith(f[1])) R.push({ ui, id: u.id, kind: 'inline', li, mech: true, type: f[1], strip: f[1], why: 'אחרי המקף שבתוך השורה פתחה המילה "' + f[1] + '" - לסגנון אמוראים (שלב מכני)' });
      else R.push({ ui, id: u.id, kind: 'inline', li, mech: false, line: plain(l) });
    });
  });
  /* מה שהמנהל דחה בעקביות (learn): סוג שנדחה ברוב הפעמים אינו מוצע עוד אוטומטית - עובר לספק */
  R.forEach((r) => { if (r.mech && learnt.off && learnt.off.includes(r.kind + ':' + r.type)) { r.mech = false; r.learntOff = true; } });
  return R;
}
/* ראשי תיבות לשם של שתי מילים (סייג 3): מן הרשימה של "שורה שהתארכה" ומן הקיצורים הקבועים */
function abbr(nm) {
  const FIX = { 'רבי יוחנן': 'רי"ו', 'רב פפא': 'ר"פ', 'רב נחמן': 'ר"נ', 'רב יוסף': 'ר"י', 'רבי יהודה': 'ר"י', 'רב ששת': 'ר"ש', 'רבי זירא': 'ר"ז', 'רבי אלעזר': 'ר"א', 'רבי אליעזר': 'ר"א', 'רב הונא': 'ר"ה', 'רב חסדא': 'ר"ח', 'רב אשי': 'ר"א', 'רבי מאיר': 'ר"מ', 'רבי שמעון': 'ר"ש', 'ריש לקיש': 'ר"ל' };
  if (FIX[nm]) return FIX[nm];
  try { const A = rd(path.join(ROOT, 'data', 'overflow', 'abbr.json')).items || []; const x = A.find((a) => a.long === nm); if (x) return x.short; } catch (e) {}
  return null;
}
function learned() { try { return rd(path.join(D, 'learn', 'rule76.json')); } catch (e) { return {}; } }

/* ---- ההחלה על יחידה אחת ---- */
function applyOne(u, cs) {
  const orig = unitInter(u); let L = orig.split(NL); const ch = [];
  for (const c of cs) {
    const si = L.findIndex((l) => /^\[צד:/.test(l)), body = L.findIndex((l, i) => i > si && !/^\[/.test(l));
    if (c.kind === 'dash') {
      if (!/^\[צד:-\s*\]$/.test(L[si])) throw new Error(u.id + ': אין כאן מקף בלי מילה');
      L[si] = '[צד:- ' + c.type + ']';
      if (c.strip) { if (!firstWord(L[body]) || firstWord(L[body]).w !== c.strip) throw new Error(u.id + ': השורה אינה פותחת ב"' + c.strip + '"'); L[body] = stripFirst(L[body]); }
      ch.push('מקף התירוץ: "- ' + c.type + '" (' + (TYPES[c.type] || 'מילת הפעולה') + ')' + (c.why ? ' - ' + c.why : ''));
    } else if (c.kind === 'vehikshe') {
      L[si] = '[צד:והקשה ' + c.name + ']';
      if (firstWord(L[body]).w !== c.strip) throw new Error(u.id + ': השורה אינה פותחת ב"' + c.strip + '"');
      L[body] = stripFirst(L[body]);
      ch.push('"והקשה ' + c.name + '" בכותרת, ו"' + c.strip + '" נמחק מן השורה' + (c.why ? ' - ' + c.why : ''));
    } else if (c.kind === 'inline') {
      const l = L[c.li], m = /[!?]\}?\s+-\s+/.exec(l); if (!m) throw new Error(u.id + ': אין מקף בתוך השורה');
      let after = l.slice(m.index + m[0].length);
      if (c.strip) { if (!after.startsWith(c.strip)) throw new Error(u.id + ': אחרי המקף אין "' + c.strip + '"'); after = after.slice(c.strip.length).replace(/^[,:]?\s*/, ''); }
      L[c.li] = l.slice(0, m.index + m[0].length) + '{אם:' + c.type + '} ' + after;
      ch.push('קושיא ותירוץ בשורה אחת: "' + c.type + '" אחרי המקף, בסגנון אמוראים (' + (TYPES[c.type] || '') + ')' + (c.why ? ' - ' + c.why : ''));
    }
  }
  const text = L.join(NL);
  /* שמירה על הנוסח: האותיות זהות למקור, חוץ ממילת הסוג שנוספה וממה שהורם (נבדק כרצף, לא כקבוצה) */
  const add = cs.map((c) => (c.kind === 'vehikshe' ? 'והקשה' + c.name : c.type).replace(/\s+/g, '')).join('');
  const rem = cs.map((c) => (c.kind === 'vehikshe' ? plain(c.oldTitle || '').replace(/[\s:]+/g, '') : '') + (c.strip || '')).join('');
  const a = letters(orig), b = letters(text);
  if (a.length - rem.length + add.length !== b.length) throw new Error(u.id + ': הכלי שינה אותיות בנוסח מעבר לכלל - נעצר');
  return { orig, text, changes: ch };
}

const cmd = POS[0];
if (cmd === 'cands') {
  const pk = pkOf(POS[1]), R = scan(pk);
  const mech = R.filter((r) => r.mech), ai = R.filter((r) => !r.mech);
  console.log('=== ' + (pk.title || pk.jid) + ' · ' + pk.units.length + ' יחידות ===');
  console.log('שלב מכני: ' + mech.length + ' · מועמדים לשלב הבינה המלאכותית: ' + ai.length);
  mech.forEach((r) => console.log('  [מכני] ' + r.id + ' ' + r.kind + ' ' + r.type + ' · ' + r.why));
  ai.forEach((r) => { const u = pk.units[r.ui], prev = pk.units.slice(Math.max(0, r.ui - 2), r.ui);
    console.log('\n-- [' + r.kind + '] יחידה ' + r.id + (r.daf ? '' : ' (' + (u.daf || '') + ')') + (r.learntOff ? ' (סוג שנדחה בעבר - לשקול)' : '') +
      '\nלפני:\n' + SKC.toInter(prev).text.split(NL).slice(-4).join(NL) + '\nהשורה:\n' + unitInter(u)); });
  const jf = optV('--json'); if (jf) fs.writeFileSync(jf, JSON.stringify(R.map((r) => ({ id: r.id, kind: r.kind, li: r.li, mech: r.mech, type: r.type || null, strip: r.strip || null, name: r.name, why: r.why || '', line: r.line })), null, 1));
} else if (cmd === 'apply') {
  const jid = POS[1], pk = pkOf(jid), R = scan(pk);
  const ch = POS[2] ? rd(POS[2]) : [];
  /* הבחירות של שלב ב: רק סוג מן הרשימה, ורק מועמד שהשלב המכני לא טיפל בו */
  for (const c of ch) {
    if (c.type === null || c.skip) continue;
    if (!TYPES[c.type]) die('סוג לא מוכר: ' + c.type + ' (' + c.id + ')');
    const r = R.find((x) => x.id === c.id && x.kind === c.kind && (c.kind !== 'inline' || x.li === c.li));
    if (!r) die('אין מועמד כזה: ' + c.id + ' ' + c.kind);
    if (r.mech) die('כבר בשלב המכני: ' + c.id);
    Object.assign(r, { type: c.type, strip: c.strip || null, why: c.why || '', ai: true, name: c.name || r.name });
  }
  const chosen = R.filter((r) => r.mech || r.ai), byU = new Map();
  chosen.forEach((r) => { if (!byU.has(r.ui)) byU.set(r.ui, []); byU.get(r.ui).push(r); });
  const items = [], tot = {};
  for (const [ui, cs] of [...byU.entries()].sort((a, b) => a[0] - b[0])) {
    const u = pk.units[ui];
    cs.forEach((c) => { if (c.kind === 'vehikshe') c.oldTitle = plain(unitInter(u).split(NL).find((l) => /^\[צד:/.test(l)).slice(4, -1)); });
    const r = applyOne(u, cs);
    const ctx = { before: SKC.toInter(pk.units.slice(Math.max(0, ui - 2), ui)).text, after: SKC.toInter(pk.units.slice(ui + 1, ui + 3)).text };
    const pre = new Set(SKC.check(r.orig, r.orig, ctx).errs), errs = SKC.check(r.orig, r.text, ctx).errs.filter((e) => !pre.has(e) && !/קצר מהמקור|ארוך מהמקור/.test(e));
    const pre2 = new Set(SKC.comply(r.orig, r.orig, {}).errs); SKC.comply(r.orig, r.text, { changes: r.changes }).errs.forEach((e) => { if (!pre2.has(e)) errs.push(e); });
    if (errs.length) die(u.id + ': השומר דחה: ' + errs.join(' · '));
    const short = r.text.split(NL).some((l, i) => { const o = r.orig.split(NL)[i]; return o && plain(l).length < plain(o).length && !/^\[/.test(l); });
    if (short) r.changes.push('השורה התקצרה - האיחוי האוטומטי של "שורה שהתארכה" רץ עליה אחרי הקבלה (סייג 8)');
    cs.forEach((c) => { const k = c.kind === 'vehikshe' ? 'והקשה' : c.type; tot[k] = (tot[k] || 0) + 1; });
    items.push({ iid: 'r76-' + u.id, kind: 'seg', seg: items.length, sugya: 0, ids: [u.id], orig: r.orig, text: r.text, point: 'כלל 30 (פרומפט 76): מילת הפעולה בכותרת הצד',
      changes: r.changes, layers: ['ליטוש'], skipped: '', adds: [], warn: [], read: [], round: 'p76', r76: cs.map((c) => ({ kind: c.kind, type: c.kind === 'vehikshe' ? 'והקשה' : c.type, mech: !!c.mech })), stat: SKC.comply(r.orig, r.text, { changes: r.changes }).stat });
  }
  const sum = Object.entries(tot).map(([k, v]) => v + ' "' + k + '"').join(', ');
  console.log('הצעות: ' + items.length + ' · ' + (sum || 'אין') + ' · מכני: ' + chosen.filter((r) => r.mech).length + ', בינה מלאכותית: ' + chosen.filter((r) => r.ai).length + ' · מועמדים שנשארו בלי מילה (ספק): ' + R.filter((r) => !r.mech && !r.ai).length);
  if (FLAGS.has('--dry')) { items.forEach((x) => console.log('\n-- ' + x.ids[0] + '\nלפני: ' + x.orig + '\nאחרי: ' + x.text + '\n' + x.changes.join(' | '))); process.exit(0); }
  const of = path.join(D, 'out', pk.jid + '.json');
  if (fs.existsSync(of)) { const o = rd(of); if (o.status === 'ready' && o.rev !== 'p76') die('כבר יש הצעות אחרות לעבודה הזאת: ' + of); }
  const out = { v: 1, jid: pk.jid, slug: pk.slug, title: pk.title, status: 'ready', plan: items.map((x) => ({ iid: x.iid })), total: items.length, done: items.length, items, t: Date.now(), rev: 'p76', counts: tot,
    summary: 'סבב כלל 30 (מילת המקף ו"והקשה"): ' + items.length + ' הצעות - ' + (sum || 'אין') + '. רק השורות שהכלל חל עליהן; שום שורה אחרת לא נגעה.' };
  fs.writeFileSync(of, JSON.stringify(out, null, 1));
  console.log('נכתב: ' + path.relative(ROOT, of));
} else if (cmd === 'learn') {
  /* הכרעות המנהל על הצעות הכלל (decisions/<jid>.json): לכל סוג - כמה התקבלו, נדחו, נערכו. סוג מכני שנדחה ברובו
     (לפחות 3 הכרעות, יותר ממחצית נדחו) - יוצא מן השלב המכני ועובר לספק; הלקח נכתב גם ל-docs/sakem-lessons.md ביד */
  const T = {}, outs = fs.readdirSync(path.join(D, 'out')).filter((f) => f.endsWith('.json'));
  for (const f of outs) {
    let o; try { o = rd(path.join(D, 'out', f)); } catch (e) { continue; } if (o.rev !== 'p76') continue;
    const df = path.join(D, 'decisions', f); if (!fs.existsSync(df)) continue;
    const dec = rd(df), DM = dec.dec || dec.items || dec;
    for (const it of o.items) { const d = DM[it.iid]; const v = (d && (d.v || d.d || d.act || d)) || null; if (!v || typeof v !== 'string') continue;
      for (const c of it.r76 || []) { const k = c.kind + ':' + c.type; T[k] = T[k] || { ok: 0, no: 0, ed: 0, mech: c.mech }; T[k][/^(?:acc|ok|קבל)/.test(v) ? 'ok' : /^(?:rej|no|דחה)/.test(v) ? 'no' : 'ed']++; } }
  }
  const off = Object.entries(T).filter(([, x]) => x.ok + x.no + x.ed >= 3 && x.no > (x.ok + x.no + x.ed) / 2).map(([k]) => k);
  fs.writeFileSync(path.join(D, 'learn', 'rule76.json'), JSON.stringify({ t: Date.now(), tally: T, off }, null, 1));
  console.log(JSON.stringify(T, null, 1) + '\nיוצאים מן השלב המכני: ' + (off.join(', ') || 'אין'));
} else if (cmd === 'order') {
  /* חבילות מן הדף החי, בדיוק כמו "סכם פרק" (window.skpAuto.enqueue) - הבקשה ל-/sakem/job נלכדת ואינה נשלחת */
  let want = POS.slice(1).map((x) => { const [s, p] = x.split(':'); return { slug: s, perakim: p ? p.split(',').map(Number) : null }; });
  if (FLAGS.has('--all')) {
    const M = {}; fs.readdirSync(path.join(D, 'out')).forEach((f) => { const m = /^([a-z-]+)-p(\d+)\.json$/.exec(f); if (m) (M[m[1]] = M[m[1]] || []).push(+m[2]); });
    want = Object.entries(M).map(([slug, p]) => ({ slug, perakim: p.sort((a, b) => a - b) }));
  }
  if (!want.length) die('אין מה להזמין');
  const { chromium } = require('playwright');
  const br = await chromium.launch();
  for (const w of want) {
    const pg = await br.newPage(), caps = [];
    await pg.route('**/*', (r) => { const q = r.request(); if (q.method() !== 'GET') { if (/sakem\/job/.test(q.url())) caps.push(q.postData()); return r.fulfill({ status: 200, contentType: 'application/json', body: '{"ok":true}' }); } return r.continue(); });
    await pg.goto('https://leokmei.com/' + w.slug + '.html', { waitUntil: 'networkidle', timeout: 180000 });
    await pg.waitForTimeout(12000);
    const secs = await pg.evaluate(() => (window.skpAuto ? window.skpAuto.sections() : null));
    if (!secs) { console.log(w.slug + ': הדף לא טען את סכם - דולג'); await pg.close(); continue; }
    for (const s of secs) {
      const n = s.si + 1; if (w.perakim && !w.perakim.includes(n)) continue;
      const k0 = caps.length;
      await pg.evaluate((si) => window.skpAuto.enqueue(si, window.skpAuto.title(si) + ' · מילת המקף ו"והקשה" (פרומפט 76)', 'seg'), s.si);
      if (caps.length === k0) { console.log(w.slug + ' פרק ' + n + ': לא נלכדה חבילה'); continue; }
      const f = path.join(D, 'jobs-put', w.slug + '-p' + n + '-p76.json');
      if (FLAGS.has('--dry')) console.log('(יבש) ' + path.relative(ROOT, f)); else { fs.writeFileSync(f, caps[caps.length - 1]); console.log('נכתב: ' + path.relative(ROOT, f)); }
    }
    await pg.close();
  }
  await br.close();
  console.log('הלאה: דחיפה; אחרי שהסנכרון נתן מזהים (sync-state.json, jobsPut) - cands ו-apply לכל עבודה.');
} else {
  console.log(fs.readFileSync(new URL(import.meta.url), 'utf8').split('*/')[0]);
}
