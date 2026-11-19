/* סבב צורה על פרק שכבר נסקר (פרומפט 28, 9.11.2026; הכללה של round_p27.mjs). בונה עבודה רגילה של סכם
   מן הנוסח החי של הדף (base-live.json מ-tools/editor_qa/p28/s_p9_base.py), בלי לגעת בנוסח עצמו:
   א. הדגשת עיקר המשנה    rules.bold[iid]  = ["^מילים מפתח השורה", "מילים באמצע"]
   ב. רווח לפני            rules.space[iid] = ["תחילת השורה כפי שהיא"]
   ג. מקף תירוץ            rules.dash[iid]  = [{at:"תחילת השורה", title:"-" | "- רבא:", strip:"מה להסיר מפתח השורה"}]
   ד. החלפת שורה שלמה     rules.line[iid]  = [{from:"השורה כפי שהיא (תחילתה)", to:["שורה", "שורה"]}]  (להחזרת מקף שנמחק)
   ה. וכל תיקוני הצורה האוטומטיים (SKC.autofixForm): דובר לכותרת צד, אות נסמכת לשם, רווח לפני גופא/ת"ר.
   node tools/sakem/round_form.mjs <base-live.json> <rules.json> <jid> <slug> "<title>" [--out-stat f]

   פרומפט 69 (19.11.2026, תענית): הרחבה. ברירת המחדל - כמו קודם; כל תוספת בדגל:
   --auto-tanna     שם תנא בתוך תיבת המשנה בלי {אם:} - נעטף ב-{אם:...} עם אותיות החיבור, "אומר" והנקודתיים
                    ({מש:רבי יוסי:} - {אם:רבי יוסי:}; "ולא הודו לו חכמים." - "ולא הודו לו {אם:חכמים}."). הזיהוי: SKC.tannaScan.
                    ספק (ר"ח כסליו, ב"ה בלי נקודתיים, שם באמצע {מש:} ארוך) - אינו נעטף ומדווח.
   --auto-brackets  [סוגריים] בגוף השורה שאינם בתוך {הס:} / {כב:} / {פס:} - {הס:[...]}, גם בתיבת המשנה (כלל 6א). העוגנים
                    הנעולים ([תוס':..], [מס:..]) אינם נוגעים, ואין משנים תו בתוך הסוגריים. {מש:[x]} - הסגנון מוחלף ל-{הס:}.
                    סוגריים בתוך סגנון אחר ({ב:}, {אם:}) - אינם נעטפים ומדווחים.
   rules.bold[iid] - גם כמה כללים לאותה שורה (הכלל הוא "לכל דין העיקר שלו"): כלל הוא מחרוזת (המופע הראשון בתיבת המשנה,
                    כמו קודם) או {i:<מספר השורה ב-base>, w:"מילים", n:<מופע, מ-1>} - בשורה מסוימת. מילים שכבר מודגשות, או שהן
                    בתוך סגנון אחר ({אם:}, {פס:}, {הס:}) - אינן מודגשות ומדווחות.
   שמירה על הנוסח: אחרי כל השינויים האותיות (SKC.plainI, בלי רווחים) זהות למקור, חוץ מ-rules.line - אחרת הכלי נעצר.
   --from-out       ה-base הוא קובץ הצעות (data/sakem/out/<jid>.json) ולא base-live: הנוסח של כל פריט הוא ההצעה (text).
   --seg-dir <תיקייה>  במקום לכתוב עבודה חדשה ל-out: seg.json לכל קטע שהשתנה, ל-put על ההצעות (פרק שטרם נסקר). השדות
                    של הפריט (adds, skipped, point, read, keep, missing) עוברים כמות שהם, ו-changes מצטרף.
   --dry            מדפיס בלבד, בלי לכתוב. */
import fs from 'fs';
import path from 'path';
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const SKC = require('../sakem_core.js');
const ARGV = process.argv.slice(2), FLAGS = new Set(ARGV.filter((x) => /^--/.test(x)));
const optV = (k) => { const i = ARGV.indexOf(k); return i > -1 ? ARGV[i + 1] : null; };
const POS = ARGV.filter((x, i) => !/^--/.test(x) && !['--out-stat', '--seg-dir'].includes(ARGV[i - 1]));
const [baseF, rulesF, jid, slug, title] = POS;
const AUTO_T = FLAGS.has('--auto-tanna'), AUTO_B = FLAGS.has('--auto-brackets'), FROM_OUT = FLAGS.has('--from-out'), DRY = FLAGS.has('--dry');
const SEG_DIR = optV('--seg-dir');
const B0 = JSON.parse(fs.readFileSync(baseF, 'utf8')), RU = JSON.parse(fs.readFileSync(rulesF, 'utf8'));
/* --from-out: פריטי ההצעות (seg בלבד) הם ה-base; הקטעים "ללא שינוי" - הנוסח המקורי שלהם הוא הנוסח */
const B = FROM_OUT ? B0.items.filter((x) => x.kind === 'seg').map((x) => Object.assign({}, x, { text: x.nochange ? null : x.text, _item: x })) : B0;
const NL = '\n', items = [], soft = [], tot = { bold: 0, space: 0, dash: 0, side: 0, auto: 0, tanna: 0, brackets: 0, vehach: 0 };
const doubt = [];
const miss = (iid, m) => soft.push(iid + ': ' + m);
/* האותיות של הנוסח, בלי סימני סגנון ובלי רווחים (שורות נעולות כמות שהן) */
const letters = (t) => String(t).split(NL).map((l) => (/^\[(?!צד:)/.test(l.trim()) ? l.trim() : SKC.plainI(l.replace(/^\[צד:(.*)\]$/, '$1').replace(/^\((?:תשובה|רווח|מעוין|נושא|דה|רקע|נקודה|משנה)\)\s*/, '')))).join('').replace(/\s+/g, '');
const SAY = /(?:אומרים|אומרת|אומר|אמרו|אמרי|אמר)/g;
/* שורות תיבת המשנה (מספרי שורות) */
const mishLines = (L) => { const r = []; let inm = false;
  L.forEach((l, i) => { const t = l.trim(); if (/^\[משנה/.test(t)) { inm = true; return; } if (/^\[(גמרא|כותרת-|קבוע)/.test(t)) { inm = false; return; }
    if (inm && !/^\[/.test(t)) r.push(i); }); return r; };
/* (1) תנא בתיבת המשנה */
function tannaFix(line, iid) {
  const F = SKC.tannaScan(line).slice().sort((a, b) => b.a - a.a), notes = [];
  let s = line;
  for (const x of F) {
    if (!x.sure) { doubt.push(iid + (x.rosh ? ': הוחרג (אינו שם) - ' : ': תנא בספק - ') + x.why + ' · "' + SKC.plainI(line).slice(0, 50) + '"'); continue; }
    if (x.kind === 'ms') {
      const inner = s.slice(x.a + 4, x.b - 1);
      if (x.punct) { const m = /^(.*?)([.,])(\s*)$/.exec(inner); s = s.slice(0, x.a) + '{אם:' + m[1] + '}' + m[2] + m[3] + s.slice(x.b); }
      else s = s.slice(0, x.a) + '{אם:' + inner + '}' + s.slice(x.b);
    } else s = s.slice(0, x.a) + '{אם:' + s.slice(x.a, x.b) + '}' + s.slice(x.b);
    notes.push('שם תנא במשנה - בסגנון אמורא: ' + x.name);
  }
  return { s, notes: notes.reverse() };
}
/* (4) סוגריים מרובעים בגוף השורה */
function bracketFix(line, iid) {
  const notes = []; let s = line;
  for (let guard = 0; guard < 20; guard++) {
    let hit = null; const re = /\[([^\[\]\n]{1,120})\]/g; let m;
    while ((m = re.exec(s))) {
      if (/^(?:תוס'|מס|מקור|דף|צד|קבוע|מחק-עיטור):/.test(m[1])) continue;
      const st = SKC.stackAt(s, m.index);
      if (st.some((t) => t === 'הס' || t === 'כב')) continue;
      if (st.some((t) => t === 'פס')) { doubt.push(iid + ': סוגריים בתוך פסוק (לא נעטפו): ' + m[0]); continue; }
      if (st.length === 1 && st[0] === 'מש') {
        /* {מש:[x]} שכולו הסוגריים - הסגנון מוחלף */
        const sp = SKC.spans(s, 'מש').find((x) => x.a < m.index && x.b > m.index);
        if (sp && sp.v.trim() === m[0]) { hit = { a: sp.a, b: sp.b, to: '{הס:' + sp.v + '}', w: m[0] }; break; }
        doubt.push(iid + ': סוגריים בתוך {מש:} ארוך (לא נעטפו): ' + m[0]); continue;
      }
      if (st.length) { doubt.push(iid + ': סוגריים בתוך {' + st.join('/') + ':} (לא נעטפו): ' + m[0]); continue; }
      hit = { a: m.index, b: m.index + m[0].length, to: '{הס:' + m[0] + '}', w: m[0] }; break;
    }
    if (!hit) break;
    s = s.slice(0, hit.a) + hit.to + s.slice(hit.b); notes.push('סגנון הסבר לסוגריים: ' + hit.w);
  }
  return { s, notes };
}
for (const b of B) {
  const orig = b.text; if (!orig) continue;
  let L = orig.split(NL);
  const ch = [], idx = L.map((_, i) => i);
  /* ד. החלפת שורה */
  for (const r of (RU.line || {})[b.iid] || []) {
    const i = L.findIndex((l) => l.startsWith(r.from));
    if (i < 0) { miss(b.iid, 'לא נמצאה שורה להחלפה: ' + r.from); continue; }
    L.splice(i, 1, ...r.to); if (!r.note || /מקף/.test(r.note)) tot.dash++; if (/והך/.test(r.note || '')) tot.vehach++; ch.push(r.note || ('הוחזר מקף התירוץ: ' + SKC.plainI(r.to[0])));
    for (let k = 0; k < idx.length; k++) { if (idx[k] === i) idx[k] = -1; else if (idx[k] > i) idx[k] += r.to.length - 1; }
  }
  const ref = L.join(NL);
  /* פרומפט 69: (1) תנא בתיבת המשנה, (4) סוגריים */
  if (AUTO_T) for (const i of mishLines(L)) { const f = tannaFix(L[i], b.iid); if (f.notes.length) { L[i] = f.s; ch.push(...f.notes); tot.tanna += f.notes.length; } }
  if (AUTO_B) L.forEach((l, i) => { const t = l.trim(); if (!t || /^\[/.test(t)) return; const f = bracketFix(l, b.iid); if (f.notes.length) { L[i] = f.s; ch.push(...f.notes); tot.brackets += f.notes.length; } });
  /* א. הדגשה במשנה */
  for (const r of (RU.bold || {})[b.iid] || []) {
    if (r && typeof r === 'object') {
      /* פרומפט 69: כלל לשורה מסוימת - {i, w, n} */
      const i = idx[r.i];
      if (i === undefined || i < 0 || !mishLines(L).includes(i)) { miss(b.iid, 'שורה ' + r.i + ' אינה שורת משנה: ' + r.w); continue; }
      let p = -1, from = 0; for (let n = 0; n < (r.n || 1); n++) { p = L[i].indexOf(r.w, from); if (p < 0) break; from = p + 1; }
      if (p < 0) { miss(b.iid, 'לא נמצא בשורה ' + r.i + ': ' + r.w); continue; }
      const st = SKC.stackAt(L[i], p), st2 = SKC.stackAt(L[i], p + r.w.length);
      if (st.includes('ב') || st.includes('נש')) { miss(b.iid, 'כבר מודגש: ' + r.w); continue; }
      if (st.length || st2.length || /[{}]/.test(r.w)) { miss(b.iid, 'בתוך סגנון אחר: ' + r.w); continue; }
      L[i] = L[i].slice(0, p) + '{ב:' + r.w + '}' + L[i].slice(p + r.w.length); tot.bold++; ch.push('הודגש במשנה: ' + r.w);
      continue;
    }
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
  /* פרומפט 69: שמירה על הנוסח - לפני התיקונים האוטומטיים: האותיות זהות למקור (חוץ מ-rules.line) */
  let text = L.join(NL);
  if (letters(text) !== letters(ref)) throw new Error(b.iid + ': המנוע שינה אותיות בנוסח - נעצר (פרומפט 69, שמירה על הנוסח)');
  /* ה. התיקונים האוטומטיים */
  const ff = SKC.autofixForm(text);
  if (ff.changed) { text = ff.text; ff.notes.forEach((x) => { ch.push(x); tot.auto++; if (/^רווח/.test(x)) tot.space++; if (/^דובר/.test(x)) tot.side++; }); }
  /* ואחריהם: autofixForm רשאי רק להוציא "אומר" / "אמר" עם הדובר לכותרת צד */
  if (letters(text) !== letters(ref) && letters(text).replace(SAY, '') !== letters(ref).replace(SAY, '')) throw new Error(b.iid + ': התיקונים האוטומטיים שינו אותיות בנוסח - נעצר');
  if (text === orig) continue;
  const bi = B.indexOf(b), pv = (B[bi - 1] || {}).text || '', nx = (B[bi + 1] || {}).text || '';
  const ctx = { before: pv.split(NL).slice(-3).join(NL), after: nx.split(NL).slice(0, 3).join(NL) };
  const pre = new Set(SKC.check(orig, orig, ctx).errs);
  const errs = SKC.check(orig, text, ctx).errs.filter((e) => !/קצר מהמקור|ארוך מהמקור/.test(e) && !pre.has(e));
  const pre2 = new Set(SKC.comply(orig, orig, {}).errs);
  SKC.comply(orig, text, { changes: ch }).errs.forEach((e) => { if (!pre2.has(e)) errs.push(e); });
  if (errs.length) throw new Error(b.iid + ': השומר דחה: ' + errs.join(' · '));
  const cp = SKC.comply(orig, text, { changes: ch });
  items.push({ iid: b.iid, kind: 'seg', seg: FROM_OUT ? b.seg : B.indexOf(b), sugya: FROM_OUT ? b.sugya : 0, ids: b.ids, orig, text, point: '', changes: ch, layers: ['ליטוש'], skipped: '', adds: [], warn: [], read: [], round: 'p28', stat: cp.stat, _b: b });
}
console.log('דולגו:', soft.length, soft.join(' | '));
if (doubt.length) console.log('ספק (לא תוקן):', doubt.length, '\n  ' + doubt.join('\n  '));
console.log('קטעים עם שינוי:', items.length, 'מתוך', B.length, JSON.stringify(tot));
if (DRY) process.exit(0);
if (SEG_DIR) {
  /* פרומפט 69: seg.json ל-put על הצעות שטרם נסקרו - הפריט כמות שהוא, והנוסח והשינויים החדשים */
  fs.mkdirSync(SEG_DIR, { recursive: true });
  const missing = FROM_OUT ? B0.items.filter((x) => x.kind === 'missing') : [];
  for (const x of items) {
    const it = x._b._item || {};
    const seg = { seg: x.seg + 1, text: x.text, changes: (it.changes || []).concat(x.changes), point: it.point || '', skipped: it.skipped || '', adds: it.adds || [], read: it.read || [], keep: it.keep || [],
      missing: missing.filter((m) => m.seg === x.seg).map((m) => ({ after: m.anchor, text: m.text, gem: m.gem, why: m.why })),
      check: Object.fromEntries(SKC.SELF_CHECK.map((c) => [c[0], true])) };
    fs.writeFileSync(path.join(SEG_DIR, 'seg-' + (x.seg + 1) + '.json'), JSON.stringify(seg, null, 1));
  }
  console.log('נכתבו', items.length, 'קבצי seg.json ל-' + SEG_DIR);
  process.exit(0);
}
items.forEach((x) => delete x._b);
const S = { bold: 0, space: 0, dash: 0, side: 0, hatz: 0 };
items.forEach((x) => { for (const k in S) S[k] += +x.stat[k] || 0; });
const out = { v: 1, jid, slug, title, status: 'ready', plan: B.map((b) => ({ iid: b.iid })), total: items.length, done: items.length, items, t: Date.now(), rev: 'p28', counts: {},
  summary: 'בסבב: ' + tot.bold + ' הדגשות במשנה, ' + tot.space + ' רווחים, ' + tot.dash + ' מקפי תירוץ, ' + tot.side + ' כותרות צד לדוברים' +
    (AUTO_T || AUTO_B || tot.vehach ? ', ' + tot.tanna + ' שמות תנאים במשנה בסגנון אמורא, ' + tot.brackets + ' סוגריים בסגנון הסבר' + (tot.vehach ? ', ' + tot.vehach + ' "והך"' : '') : ''), compliance: S };
fs.writeFileSync('data/sakem/out/' + jid + '.json', JSON.stringify(out, null, 1));
console.log('נכתב: data/sakem/out/' + jid + '.json');
