/* סבב צורה על פרק שכבר נסקר (פרומפט 28, 9.11.2026; הכללה של round_p27.mjs). בונה עבודה רגילה של סכם
   מן הנוסח החי של הדף (base-live.json מ-tools/editor_qa/p28/s_p9_base.py), בלי לגעת בנוסח עצמו:
   א. הדגשת עיקר המשנה    rules.bold[iid]  = ["^מילים מפתח השורה", "מילים באמצע"]
   ב. רווח לפני            rules.space[iid] = ["תחילת השורה כפי שהיא"]
   ג. מקף תירוץ            rules.dash[iid]  = [{at:"תחילת השורה", title:"-" | "- רבא:", strip:"מה להסיר מפתח השורה"}]
   ד. החלפת שורה שלמה     rules.line[iid]  = [{from:"השורה כפי שהיא (תחילתה)", to:["שורה", "שורה"]}]  (להחזרת מקף שנמחק)
   ה. וכל תיקוני הצורה האוטומטיים (SKC.autofixForm): דובר לכותרת צד, אות נסמכת לשם, רווח לפני גופא/ת"ר.
   node tools/sakem/round_form.mjs <base-live.json> <rules.json> <jid> <slug> "<title>" [--out-stat f] */
import fs from 'fs';
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const SKC = require('../sakem_core.js');
const [baseF, rulesF, jid, slug, title] = process.argv.slice(2);
const B = JSON.parse(fs.readFileSync(baseF, 'utf8')), RU = JSON.parse(fs.readFileSync(rulesF, 'utf8'));
const NL = '\n', items = [], soft = [], tot = { bold: 0, space: 0, dash: 0, side: 0, auto: 0 };
const miss = (iid, m) => soft.push(iid + ': ' + m);
for (const b of B) {
  const orig = b.text; if (!orig) continue;
  let L = orig.split(NL);
  const ch = [];
  /* ד. החלפת שורה */
  for (const r of (RU.line || {})[b.iid] || []) {
    const i = L.findIndex((l) => l.startsWith(r.from));
    if (i < 0) { miss(b.iid, 'לא נמצאה שורה להחלפה: ' + r.from); continue; }
    L.splice(i, 1, ...r.to); tot.dash++; ch.push(r.note || ('הוחזר מקף התירוץ: ' + SKC.plainI(r.to[0])));
  }
  /* א. הדגשה במשנה */
  for (const r of (RU.bold || {})[b.iid] || []) {
    let inm = false, done = false;
    for (let i = 0; i < L.length && !done; i++) {
      if (/^\[משנה/.test(L[i])) { inm = true; continue; }
      if (/^\[(גמרא|כותרת-|קבוע)/.test(L[i])) { inm = false; continue; }
      if (!inm || /^\[/.test(L[i])) continue;
      const st = r[0] === '^', w = st ? r.slice(1) : r;
      const lead = (/^\(\S+\)\s*/.exec(L[i]) || [''])[0];
      const p = st ? (L[i].startsWith(w, lead.length) ? lead.length : -1) : L[i].indexOf(w);
      if (p < 0) continue;
      const before = L[i].slice(0, p);
      if (/\{ב:[^}]*$/.test(before)) { done = true; break; }
      L[i] = before + '{ב:' + w + '}' + L[i].slice(p + w.length); done = true; tot.bold++; ch.push('הודגש במשנה: ' + w);
    }
    if (!done) miss(b.iid, 'לא נמצא במשנה: ' + r);
  }
  /* ג. מקף תירוץ */
  for (const r of (RU.dash || {})[b.iid] || []) {
    const i = L.findIndex((l) => l.startsWith(r.at));
    if (i < 0) { miss(b.iid, 'לא נמצאה שורה למקף: ' + r.at); continue; }
    if (/^\[צד:/.test(L[i - 1] || '')) { miss(b.iid, 'כבר יש כותרת צד: ' + r.at); continue; }
    let line = L[i];
    if (r.strip) { const lead = (/^\(\S+\)\s*/.exec(line) || [''])[0]; if (!line.startsWith(r.strip, lead.length)) { miss(b.iid, 'אין מה להסיר: ' + r.strip); continue; } line = lead + line.slice(lead.length + r.strip.length).replace(/^\s+/, ''); }
    L.splice(i, 1, '[צד:' + r.title + ']', line); tot.dash++; ch.push('מקף תירוץ: [צד:' + r.title + ']');
  }
  /* ב. רווח לפני */
  for (const r of (RU.space || {})[b.iid] || []) {
    const i = L.findIndex((l) => l.startsWith(r));
    if (i < 0) { miss(b.iid, 'לא נמצאה שורה לרווח: ' + r); continue; }
    if (/^\(/.test(L[i])) { miss(b.iid, 'לשורה כבר יש סגנון: ' + r); continue; }
    L[i] = '(רווח) ' + L[i]; tot.space++; ch.push('רווח לפני: ' + SKC.plainI(r).slice(0, 40));
  }
  /* ה. התיקונים האוטומטיים */
  let text = L.join(NL);
  const ff = SKC.autofixForm(text);
  if (ff.changed) { text = ff.text; ff.notes.forEach((x) => { ch.push(x); tot.auto++; if (/^רווח/.test(x)) tot.space++; if (/^דובר/.test(x)) tot.side++; }); }
  if (text === orig) continue;
  const bi = B.indexOf(b), pv = (B[bi - 1] || {}).text || '', nx = (B[bi + 1] || {}).text || '';
  const ctx = { before: pv.split(NL).slice(-3).join(NL), after: nx.split(NL).slice(0, 3).join(NL) };
  const pre = new Set(SKC.check(orig, orig, ctx).errs);
  const errs = SKC.check(orig, text, ctx).errs.filter((e) => !/קצר מהמקור|ארוך מהמקור/.test(e) && !pre.has(e));
  const pre2 = new Set(SKC.comply(orig, orig, {}).errs);
  SKC.comply(orig, text, { changes: ch }).errs.forEach((e) => { if (!pre2.has(e)) errs.push(e); });
  if (errs.length) throw new Error(b.iid + ': השומר דחה: ' + errs.join(' · '));
  const cp = SKC.comply(orig, text, { changes: ch });
  items.push({ iid: b.iid, kind: 'seg', seg: B.indexOf(b), sugya: 0, ids: b.ids, orig, text, point: '', changes: ch, layers: ['ליטוש'], skipped: '', adds: [], warn: [], read: [], round: 'p28', stat: cp.stat });
}
const S = { bold: 0, space: 0, dash: 0, side: 0, hatz: 0 };
items.forEach((x) => { for (const k in S) S[k] += +x.stat[k] || 0; });
const out = { v: 1, jid, slug, title, status: 'ready', plan: B.map((b) => ({ iid: b.iid })), total: items.length, done: items.length, items, t: Date.now(), rev: 'p28', counts: {},
  summary: 'בסבב: ' + tot.bold + ' הדגשות במשנה, ' + tot.space + ' רווחים, ' + tot.dash + ' מקפי תירוץ, ' + tot.side + ' כותרות צד לדוברים', compliance: S };
fs.writeFileSync('data/sakem/out/' + jid + '.json', JSON.stringify(out, null, 1));
console.log('דולגו:', soft.length, soft.join(' | '));
console.log('קטעים עם שינוי:', items.length, 'מתוך', B.length, JSON.stringify(tot));
