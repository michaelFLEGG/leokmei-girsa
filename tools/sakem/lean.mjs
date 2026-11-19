/* סכם - דיאטת כללים (פרומפט 70, 19.11.2026). הצינור החסכוני (--lean) קורא ליבה קומפקטית + קבצי נושא לפי הצורך,
   במקום כל docs/sakem-lessons.md וכל data/sakem/learn/rules.json.

   המבנה (docs/sakem-lean/):
     core.md            ליבת סכם: כללי בעל הפרויקט הקבועים והגדרות ברכות פרק א - כלשונם (ראש sakem-lessons.md עד הסימון),
                        כללי העימוד הנלמדים (docs/כללי-עימוד-נלמדים.md) כלשונם, והלקחים שזוקקו לנושא "ליבה"
     topic-<נושא>.md    משנה / אגדתא / כותרות / עימוד / מחלוקות / השלמות / תהליך / מסכת-<slug>
     distilled.json     הכללים המזוקקים: {text, src:[מזהי מקור], topic, code, pairs} ו-{cancelled:[...], by, why}
     map.json           כל לקח מקורי (מזהה יציב לפי תוכן) -> core / topic:<נושא> / code / cancelled (ובמי)
   המקור המלא לא נמחק: sakem-lessons.md ו-rules.json נשארים כמות שהם (והעתק בארכיון docs/sakem-lean/archive/).

   אפס אובדן: `check` מוודא שכל לקח מקורי ממופה. לקח שנוסף אחרי הזיקוק (הלמידה ממשיכה לכתוב ל-sakem-lessons.md
   ול-rules.json) אינו הולך לאיבוד: `rules --lean` מדפיס אותו כלשונו תחת "לקחים חדשים שטרם זוקקו", עד הדחיסה הבאה.

   node tools/sakem/lean.mjs units            מפיק את רשימת הלקחים עם מזהים (לזיקוק)
   node tools/sakem/lean.mjs build <out*.json>  בונה את docs/sakem-lean מתוצאות הזיקוק ובודק אפס אובדן
   node tools/sakem/lean.mjs check            בודק שכל לקח ממופה (קוד יציאה 2 אם חסר; חדשים - רק אזהרה) */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const LESS = path.join(ROOT, 'docs', 'sakem-lessons.md');
const LRULES = path.join(ROOT, 'data', 'sakem', 'learn', 'rules.json');
const PAGIN = path.join(ROOT, 'docs', 'כללי-עימוד-נלמדים.md');
export const LD = path.join(ROOT, 'docs', 'sakem-lean');
/* הסימון בסוף החלק הקבוע של sakem-lessons.md: הכותרת הראשונה של לקחים שנלמדו מעריכות (מכאן - מזוקק) */
const FIXED_END = /^## מעריכות המנהל אחרי סכם בשבת פרקים ב-ג/;
export const TOPICS = { 'ליבה': 'core', 'משנה': 'mishna', 'אגדתא': 'aggada', 'כותרות': 'titles', 'עימוד': 'layout', 'מחלוקות': 'disputes', 'השלמות': 'adds', 'תהליך': 'process' };

const norm = (t) => String(t || '').replace(/[֑-ׇ]/g, '').replace(/[*`_~]/g, '').replace(/\s+/g, ' ').trim();
export const hid = (pre, t) => pre + crypto.createHash('sha1').update(norm(t)).digest('hex').slice(0, 10);

/* כל הלקחים הניתנים לזיקוק: יחידות sakem-lessons.md אחרי החלק הקבוע, וכללי rules.json הפעילים */
export function units() {
  const L = fs.readFileSync(LESS, 'utf8').split('\n');
  let i0 = L.findIndex((s) => FIXED_END.test(s)); if (i0 < 0) i0 = L.length;
  const out = []; let sec = '', cur = null;
  for (let i = i0; i < L.length; i++) { const s = L[i];
    if (/^## /.test(s)) { sec = s.slice(3); cur = null; continue; }
    if (!s.trim()) { cur = null; continue; }
    if (/^- /.test(s) || !cur) { cur = { line: i + 1, sec, text: s }; out.push(cur); } else cur.text += '\n' + s; }
  out.forEach((u) => { u.id = hid('L', u.text); });
  let R = []; try { R = JSON.parse(fs.readFileSync(LRULES, 'utf8')).rules || []; } catch (e) {}
  R.forEach((x, i) => { if (x.off) return; const text = x.text + (x.was && x.kind !== 'החלפת מילה' ? '\n  לפני: ' + x.was + '\n  אחרי: ' + x.now : '');
    out.push({ ri: i, sec: 'rules.json: ' + x.kind, text, id: hid('R', x.id || x.text), kind: x.kind }); });
  return { units: out, fixed: L.slice(0, i0).join('\n') };
}

function topicKey(t) {
  t = String(t || 'ליבה').trim();
  if (/^מסכת:/.test(t)) return 'masechet-' + t.slice(5).trim().toLowerCase().replace(/[^a-z-]/g, '');
  return TOPICS[t] || 'core';
}

export function loadMap() { try { return JSON.parse(fs.readFileSync(path.join(LD, 'map.json'), 'utf8')); } catch (e) { return null; } }

/* בדיקת אפס אובדן: כל לקח מקורי ממופה. מחזיר {missing:[...לקחים שאינם במפה], ok} */
export function check() {
  const M = loadMap();
  if (!M) return { ok: false, missing: [], why: 'אין docs/sakem-lean/map.json - טרם נבנה' };
  const { units: U } = units();
  const missing = U.filter((u) => !M.map[u.id]);
  return { ok: true, missing, total: U.length, mapped: U.length - missing.length };
}

function build(files) {
  const { units: U, fixed } = units();
  const byOld = {}; /* מזהי הזיקוק (L<שורה> / R<אינדקס>) -> המזהה היציב */
  const snap = (() => { try { return JSON.parse(fs.readFileSync(path.join(LD, 'units-snapshot.json'), 'utf8')); } catch (e) { return null; } })();
  (snap || U).forEach((u) => { byOld[u.ri !== undefined ? 'R' + u.ri : 'L' + u.line] = u.id; });
  const D = []; files.forEach((f) => { D.push(...JSON.parse(fs.readFileSync(f, 'utf8'))); });
  const map = {}, dup = [], unknown = [];
  const put = (old, dest) => { const id = byOld[old] || (U.some((u) => u.id === old) ? old : null); if (!id) { unknown.push(old); return null; } if (map[id]) dup.push(old); map[id] = dest; return id; };
  const rules = [];
  D.forEach((x) => {
    if (x.cancelled) { const by = byOld[x.by] || x.by; (x.cancelled || []).forEach((o) => put(o, { to: 'cancelled', by, why: x.why || '' })); return; }
    const tk = x.code ? 'code' : topicKey(x.topic);
    const src = (x.src || []).map((o) => put(o, x.code ? { to: 'code', topic: topicKey(x.topic) } : { to: tk === 'core' ? 'core' : 'topic:' + tk })).filter(Boolean);
    rules.push({ text: String(x.text || '').trim(), src, topic: x.topic || 'ליבה', key: tk, code: !!x.code, pairs: x.pairs || undefined });
  });
  /* חסר = לקח שהיה לפני הזיקוק ולא מופה (עצירה). לקח שנוסף אחרי צילום הזיקוק - "חדש", מודפס כלשונו עד הדחיסה הבאה */
  const base = snap || U, inSnap = new Set(base.map((u) => u.id));
  const missing = base.filter((u) => !map[u.id]);
  const fresh = U.filter((u) => !inSnap.has(u.id) && !map[u.id]);
  if (fresh.length) console.log('לקחים שנוספו אחרי צילום הזיקוק (' + fresh.length + ') - יודפסו כלשונם ב-rules --lean עד הדחיסה הבאה.');
  fs.mkdirSync(path.join(LD, 'archive'), { recursive: true });
  const stamp = new Date().toISOString().slice(0, 10);
  fs.copyFileSync(LESS, path.join(LD, 'archive', 'sakem-lessons-' + stamp + '.md'));
  fs.copyFileSync(LRULES, path.join(LD, 'archive', 'learn-rules-' + stamp + '.json'));
  if (!snap) fs.writeFileSync(path.join(LD, 'units-snapshot.json'), JSON.stringify(U.map((u) => ({ id: u.id, line: u.line, ri: u.ri, sec: u.sec, text: u.text })), null, 0));
  fs.writeFileSync(path.join(LD, 'distilled.json'), JSON.stringify(rules, null, 1));
  fs.writeFileSync(path.join(LD, 'map.json'), JSON.stringify({ v: 1, built: new Date().toISOString(), units: U.length, map }, null, 0));
  /* הקבצים לקריאה */
  const by = {}; rules.forEach((r) => { (by[r.key] = by[r.key] || []).push(r); });
  const HE = Object.fromEntries(Object.entries(TOPICS).map(([a, b]) => [b, a]));
  const lines = (arr) => arr.map((r) => '- ' + r.text).join('\n');
  let core = '# ליבת סכם (פרומפט 70) - נבנה מ-sakem-lessons.md ומ-learn/rules.json ב-' + stamp + ' (tools/sakem/lean.mjs)\n' +
    'כל לקח מקורי ממופה לכאן, לקובץ נושא, לבדיקה בקוד או לביטול (docs/sakem-lean/map.json). **לקח כאן גובר על הכללים הכלליים, והמאוחר גובר.**\n\n' +
    '## א. כללי בעל הפרויקט הקבועים והגדרות ברכות פרק א - כלשונם\n' + fixed.replace(/^# .*\n/, '') + '\n\n';
  if (fs.existsSync(PAGIN)) core += '## ב. כללי העימוד שנלמדו ממיכאל במצב דפוס - כלשונם\n' + fs.readFileSync(PAGIN, 'utf8').replace(/^# .*\n/, '') + '\n\n';
  core += '## ג. לקחים מעריכות המנהל - מזוקקים\n' + lines(by.core || []) + '\n';
  fs.writeFileSync(path.join(LD, 'core.md'), core);
  Object.keys(by).filter((k) => k !== 'core' && k !== 'code').forEach((k) => {
    fs.writeFileSync(path.join(LD, 'topic-' + k + '.md'), '# ' + (HE[k] || k.replace('masechet-', 'מסכת ')) + ' - לקחים מזוקקים (פרומפט 70)\n\n' + lines(by[k]) + '\n'); });
  const code = by.code || [];
  fs.writeFileSync(path.join(LD, 'code.md'), '# נאכף אוטומטית בקוד - אינו נקרא בידי הכותב, רק שמו מופיע ב-rules --lean\n\n' + code.map((r) => '- ' + r.text + (r.pairs ? '\n  ' + r.pairs.map((p) => p[0] + '->' + p[1]).join(', ') : '')).join('\n') + '\n');
  const sz = (f) => fs.statSync(path.join(LD, f)).size;
  console.log('נבנה: ' + rules.length + ' כללים מזוקקים מ-' + U.length + ' לקחים. core.md ' + sz('core.md') + ' בתים; ' +
    fs.readdirSync(LD).filter((f) => /^topic-/.test(f)).map((f) => f + ' ' + sz(f)).join(', '));
  if (unknown.length) console.log('מזהים שאינם קיימים במקור (התעלמתי): ' + unknown.join(' '));
  if (dup.length) console.log('מזהים שמופו פעמיים (נשאר האחרון): ' + dup.join(' '));
  if (missing.length) { console.log('עצירה: ' + missing.length + ' לקחים לא מופו: ' + missing.map((u) => (u.line ? 'L' + u.line : 'R' + u.ri) + ' ' + u.text.slice(0, 60).replace(/\n/g, ' ')).join(' | ')); process.exit(2); }
  console.log('אפס אובדן: כל ' + base.length + ' הלקחים שזוקקו ממופים.');
}

/* פלט rules --lean: ליבה + קבצי הנושא שהעבודה צריכה + לקחים חדשים שטרם זוקקו (כלשונם) */
export function leanText(pk, opts) {
  const o = opts || {};
  const M = loadMap(); if (!M) return null;
  const parts = [fs.readFileSync(path.join(LD, 'core.md'), 'utf8')];
  const units0 = (pk && pk.units) || [];
  const hasMishna = !units0.length || units0.some((u) => u.k === 'm' || /\[משנה|מתני/.test(u.t || u.text || ''));
  const want = ['titles', 'layout', 'disputes', 'aggada', 'adds'];
  if (hasMishna) want.unshift('mishna');
  if (o.process !== false) want.push('process');
  if (pk && pk.slug) want.push('masechet-' + pk.slug);
  const got = [];
  want.forEach((k) => { const f = path.join(LD, 'topic-' + k + '.md'); if (fs.existsSync(f)) { parts.push(fs.readFileSync(f, 'utf8')); got.push(k); } });
  /* נאכף בקוד - שם הכלל בלבד */
  try { const code = JSON.parse(fs.readFileSync(path.join(LD, 'distilled.json'), 'utf8')).filter((r) => r.code);
    if (code.length) parts.push('# נאכף אוטומטית (השומר בודק ומזהיר או עוצר; אין צורך לזכור את הפירוט)\n' + code.map((r) => '- ' + r.text.split(/[.:]/)[0].slice(0, 90) + (r.pairs ? ' (' + r.pairs.map((p) => p[0] + '->' + p[1]).join(', ') + ')' : '')).join('\n')); } catch (e) {}
  const { units: U } = units();
  const fresh = U.filter((u) => !M.map[u.id]);
  if (fresh.length) parts.push('# לקחים חדשים שטרם זוקקו (' + fresh.length + ') - כלשונם, גוברים על מה שלמעלה\n' + fresh.map((u) => u.text).join('\n'));
  return { text: parts.join('\n\n'), topics: got, fresh: fresh.length };
}

if (process.argv[1] && fileURLToPath(import.meta.url) === path.resolve(process.argv[1])) {
  const c = process.argv[2];
  if (c === 'units') { const { units: U } = units(); console.log(JSON.stringify(U)); }
  else if (c === 'build') build(process.argv.slice(3));
  else if (c === 'check') { const r = check(); if (!r.ok) { console.log(r.why); process.exit(2); }
    console.log('ממופים ' + r.mapped + ' מתוך ' + r.total + (r.missing.length ? ' · ' + r.missing.length + ' חדשים שטרם זוקקו (מוצגים כלשונם ב-rules --lean)' : ' · אפס אובדן')); }
  else console.log('units | build <out.json...> | check');
}
