/* סכם - מדידת עלות אמיתית לכל הרצה (פרומפט 70, 19.11.2026).
   קורא את תמלול השיחה של Claude Code (בכל הודעת מודל יש usage) ומסכם קלט, כתיבת מטמון, קריאת מטמון ופלט,
   לפי מודל (אופוס / סונט / הייקו), כולל סוכני-משנה. אין גישה לתמלול - מחזיר "לא נמדד" עם הסיבה, לעולם לא מספר מומצא.

   מיקום התמלול (נבדק 19.11.2026 בענן): <בית>/.claude/projects/<תיקיית העבודה, מקפים במקום לוכסנים>/<מזהה השיחה>.jsonl,
   וסוכני-משנה תחת <מזהה השיחה>/subagents/*.jsonl. מזהה השיחה: CLAUDE_CODE_SESSION_ID. במחשב (חלונות) - אותו מבנה
   תחת תיקיית המשתמש. CLAUDE_CONFIG_DIR גובר על <בית>/.claude. בלי מזהה - התמלול שהשתנה אחרון (עד עשר דקות).
   הודעה אחת נרשמת בתמלול כמה פעמים (קטעי זרימה) - נספרת פעם אחת לפי message.id, בנתוני ה-usage האחרונים שלה. */
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

/* דולר למיליון טוקנים. אופוס 5.5 - לפי המסמך של פרומפט 70. אפשר לדרוס ב-data/sakem/prices.json */
export const PRICES = {
  opus: { in: 4, out: 20, cr: 0.2, cw: 5 },
  sonnet: { in: 3, out: 15, cr: 0.3, cw: 3.75 },
  haiku: { in: 1, out: 5, cr: 0.1, cw: 1.25 },
  other: { in: 4, out: 20, cr: 0.2, cw: 5 },
};
export const famOf = (m) => (/opus/i.test(m || '') ? 'opus' : /sonnet/i.test(m || '') ? 'sonnet' : /haiku/i.test(m || '') ? 'haiku' : 'other');
export const FAM_HE = { opus: 'אופוס', sonnet: 'סונט', haiku: 'הייקו', other: 'אחר' };

export function prices(root) {
  try { return Object.assign({}, PRICES, JSON.parse(fs.readFileSync(path.join(root, 'data', 'sakem', 'prices.json'), 'utf8'))); } catch (e) { return PRICES; }
}

function projectsDir() {
  const base = process.env.CLAUDE_CONFIG_DIR || path.join(os.homedir(), '.claude');
  return path.join(base, 'projects');
}

/* מוצא את קובץ התמלול של השיחה הנוכחית (ואת תיקיית סוכני-המשנה שלה) */
export function findTranscript() {
  const P = projectsDir();
  if (!fs.existsSync(P)) return { err: 'אין תיקיית תמלולים (' + P + ')' };
  const dirs = fs.readdirSync(P).map((d) => path.join(P, d)).filter((d) => { try { return fs.statSync(d).isDirectory(); } catch (e) { return false; } });
  const sid = process.env.CLAUDE_CODE_SESSION_ID || process.env.CLAUDE_SESSION_ID || '';
  if (sid) for (const d of dirs) { const f = path.join(d, sid + '.jsonl'); if (fs.existsSync(f)) return { file: f, sub: path.join(d, sid), sid }; }
  let best = null;
  for (const d of dirs) for (const f of fs.readdirSync(d)) {
    if (!f.endsWith('.jsonl')) continue;
    const p = path.join(d, f), m = fs.statSync(p).mtimeMs;
    if (!best || m > best.m) best = { p, m, d, id: f.slice(0, -6) };
  }
  if (!best) return { err: 'אין קובץ תמלול בתיקייה ' + P };
  if (Date.now() - best.m > 10 * 60e3) return { err: 'התמלול האחרון ישן מעשר דקות - אינו של ההרצה הזאת' };
  return { file: best.p, sub: path.join(best.d, best.id), sid: best.id, guessed: true };
}

function listSub(dir) {
  const out = [];
  const walk = (d) => { if (!fs.existsSync(d)) return; for (const f of fs.readdirSync(d)) { const p = path.join(d, f); let s; try { s = fs.statSync(p); } catch (e) { continue; }
    if (s.isDirectory()) walk(p); else if (f.endsWith('.jsonl')) out.push(p); } };
  walk(dir);
  return out;
}

/* סיכום ה-usage בקובץ אחד, מ-since (מילישניות) ועד עכשיו */
function sumFile(f, since, acc, seen, sub) {
  let txt; try { txt = fs.readFileSync(f, 'utf8'); } catch (e) { return; }
  const last = new Map();
  for (const line of txt.split('\n')) {
    if (!line || line.indexOf('"usage"') < 0) continue;
    let o; try { o = JSON.parse(line); } catch (e) { continue; }
    const m = o.message; if (!m || !m.usage) continue;
    const t = Date.parse(o.timestamp || '') || 0;
    if (since && t && t < since) continue;
    last.set(m.id || (f + ':' + o.uuid), { model: m.model || '', u: m.usage });
  }
  for (const [id, x] of last) {
    if (seen.has(id)) continue; seen.add(id);
    if (x.model === '<synthetic>') continue;
    const fam = famOf(x.model), a = acc[fam] || (acc[fam] = { in: 0, cw: 0, cr: 0, out: 0, msgs: 0 });
    a.in += +x.u.input_tokens || 0; a.cw += +x.u.cache_creation_input_tokens || 0; a.cr += +x.u.cache_read_input_tokens || 0; a.out += +x.u.output_tokens || 0; a.msgs++;
    if (sub) a.sub = (a.sub || 0) + 1;
  }
}

/* מדידה: { tokens:{opus:{in,cw,cr,out,msgs}, ...}, total, usd, model, kind:'מדידה', session } או { kind:'לא נמדד', why } */
export function measure(root, since) {
  try {
    const T = findTranscript();
    if (T.err) return { kind: 'לא נמדד', why: T.err };
    const acc = {}, seen = new Set();
    sumFile(T.file, since, acc, seen, false);
    const subs = listSub(T.sub);
    subs.forEach((f) => sumFile(f, since, acc, seen, true));
    const P = prices(root);
    let usd = 0, total = 0, top = null;
    for (const k in acc) { const a = acc[k], p = P[k] || P.other;
      a.usd = Math.round(((a.in * p.in + a.out * p.out + a.cr * p.cr + a.cw * p.cw) / 1e6) * 100) / 100;
      a.total = a.in + a.cw + a.cr + a.out; usd += a.usd; total += a.total;
      if (!top || a.total > acc[top].total) top = k; }
    if (!total) return { kind: 'לא נמדד', why: 'בתמלול אין שום usage מאז תחילת ההרצה' };
    return { kind: 'מדידה', tokens: acc, total, usd: Math.round(usd * 100) / 100, model: FAM_HE[top] || top, session: T.sid, subFiles: subs.length, ...(T.guessed ? { guessed: true } : {}) };
  } catch (e) { return { kind: 'לא נמדד', why: 'שגיאה בקריאת התמלול: ' + e.message }; }
}

/* סוג הסבב, מתוך כותרת העבודה ומזהה העבודה */
export function roundOf(title, jid) {
  const t = title || '';
  if (/נוסח החי/.test(t)) return 'נוסח חי';
  if (/כללים חדשים|כללים אחרונים|פרומפט 6[2-9]/.test(t)) return 'כללים אחרונים';
  if (/סבב שני|סבב מבני|סבב מחודש|סבב כללים|סבב נוסף/.test(t)) return 'כללים מעודכנים';
  if (/-s\d/.test(jid || '')) return 'סבב קטעים';
  return 'ראשון';
}

if (process.argv[1] && process.argv[1].endsWith('cost.mjs')) {
  const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..', '..');
  const since = process.argv[2] ? Date.parse(process.argv[2]) : 0;
  console.log(JSON.stringify(measure(root, since), null, 1));
}
