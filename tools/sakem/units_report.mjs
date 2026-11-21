/* units_report.mjs - למידה מן הסקירה הפנימית (פרומפט 75 ג, 21.11.2026).
   כל הכרעה על הצעת סכם נרשמת ביומן (/sakem/dec -> data/sakem/decisions/<jid>.json): מקור, הצעה, ונוסח סופי כשנערך.
   בסקירה הפנימית מיכאל מקבל חלק מן השינויים ודוחה חלק, והכרטיס נרשם "נערך" עם הנוסח המעורב. מכאן משוחזרת
   כל יחידה (SKU.classify, אותו מנוע שבדף): התקבלה / נדחתה / נערכה, עם סוג השינוי (החלפה, מחיקה, תוספת,
   כותרת צד, אמוראים, הדגשה, רווח לפני, איחוד שורות...). זה מידע עדין יותר מהכרעה על כרטיס שלם.
     node tools/sakem/units_report.mjs              הדוח: data/sakem/learn/units.json + units-report.md
     node tools/sakem/units_report.mjs --weekly     רק אם הדוח האחרון בן שבוע ומעלה (לפעולת הסנכרון)
     node tools/sakem/units_report.mjs --print      להדפסה בלבד (runner.mjs lessons)
   "נדחה בעקביות": לפחות 5 יחידות מאותו סוג שהוכרעו ביחידה (בכרטיס מעורב), ו-75% מהן ומעלה נדחו; וגם החלפה
   מסוימת (מילה -> מילה) שנדחתה 3 פעמים ומעלה. אלה מודפסים ב-lessons כחובה לכתוב מהם כלל ב-docs/sakem-lessons.md. */
import fs from 'fs';
import path from 'path';
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../..');
const SKU = require(path.join(ROOT, 'tools/sakem_units_core.js'));
const DEC = path.join(ROOT, 'data/sakem/decisions'), OUTJ = path.join(ROOT, 'data/sakem/learn/units.json'), OUTM = path.join(ROOT, 'data/sakem/learn/units-report.md');

export function analyze(since) {
  const K = {}, pairs = {}, cards = { mixed: 0, accept: 0, reject: 0, edit: 0 };
  const add = (k, w, d, l) => { K[k] = K[k] || { label: l || k, fine: { accept: 0, reject: 0, edit: 0 }, card: { accept: 0, reject: 0 } }; K[k][w][d]++; };
  for (const f of fs.existsSync(DEC) ? fs.readdirSync(DEC).filter((x) => x.endsWith('.json')) : []) {
    let d; try { d = JSON.parse(fs.readFileSync(path.join(DEC, f), 'utf8')); } catch (e) { continue; }
    const slug = ((d.job || {}).slug) || f.replace(/-(p\d+|s\d+.*)\.json$/, '');
    for (const x of d.log || []) {
      if ((x.t || 0) < (since || 0) || !x.orig || !x.prop || !/^(accept|reject|keep|edit)$/.test(x.act)) continue;
      if ((x.layers || []).includes('השלמה') && !/\{\+:/.test(x.prop)) continue;
      let U; try { U = x.act === 'edit' && x.final ? SKU.classify(x.orig, x.prop, x.final) : SKU.units(x.orig, x.prop).u.filter((u) => !u.quiet); } catch (e) { continue; }
      if (x.act === 'edit' && x.final) {
        const has = (v) => U.some((u) => u.dec === v);
        if (has('accept') && has('reject')) cards.mixed++; else cards.edit++;
        U.forEach((u) => {
          add(u.kind, 'fine', u.dec, u.label);
          if (u.dec === 'reject' && u.kind === 'החלפה' || u.kind === 'מחיקה' && u.dec === 'reject') {
            const key = u.a.trim() + ' -> ' + u.b.trim();
            if (key.length < 80) { pairs[key] = pairs[key] || { n: 0, slugs: new Set() }; pairs[key].n++; pairs[key].slugs.add(slug); }
          }
        });
      } else {
        const a = x.act === 'accept' ? 'accept' : 'reject';
        cards[a]++;
        U.forEach((u) => add(u.kind, 'card', a, u.label));
      }
    }
  }
  const consistent = Object.entries(K).map(([k, v]) => { const n = v.fine.accept + v.fine.reject + v.fine.edit; return { kind: k, label: v.label, n, reject: n ? v.fine.reject / n : 0, fine: v.fine, card: v.card }; })
    .filter((x) => x.n >= 5 && x.reject >= 0.75).sort((a, b) => b.reject - a.reject || b.n - a.n);
  const rpairs = Object.entries(pairs).filter(([, v]) => v.n >= 3).sort((a, b) => b[1].n - a[1].n).slice(0, 30).map(([k, v]) => ({ pair: k, n: v.n, slugs: [...v.slugs] }));
  return { t: Date.now(), cards, kinds: K, consistent, pairs: rpairs };
}
export function text(R) {
  const pc = (x) => Math.round(100 * x) + '%';
  const L = ['# סקירה פנימית: מה מיכאל מקבל ומה דוחה, לפי סוג השינוי', '',
    'נוצר אוטומטית (tools/sakem/units_report.mjs) מיומן ההכרעות. "ביחידה" - כרטיסים שהוכרעו שינוי-שינוי (סקירה פנימית או עריכה); "בכרטיס" - כרטיס שלם שהתקבל או נדחה.', '',
    'כרטיסים: מעורבים (קבל חלק, דחה חלק) ' + R.cards.mixed + ' · נערכו ' + R.cards.edit + ' · התקבלו שלמים ' + R.cards.accept + ' · נדחו שלמים ' + R.cards.reject, '',
    '| סוג השינוי | ביחידה: התקבל | נדחה | נערך | בכרטיס: התקבל | נדחה |', '|---|---|---|---|---|---|'];
  Object.entries(R.kinds).sort((a, b) => (b[1].fine.reject + b[1].fine.accept) - (a[1].fine.reject + a[1].fine.accept))
    .forEach(([k, v]) => L.push('| ' + (v.label || k) + ' | ' + v.fine.accept + ' | ' + v.fine.reject + ' | ' + v.fine.edit + ' | ' + v.card.accept + ' | ' + v.card.reject + ' |'));
  L.push('', '## נדחה בעקביות (5 יחידות ומעלה, 75% דחייה ומעלה)', '');
  if (!R.consistent.length) L.push('אין עדיין - צריך עוד הכרעות ביחידה.');
  R.consistent.forEach((c) => L.push('- **' + (c.label || c.kind) + '**: נדחו ' + pc(c.reject) + ' מתוך ' + c.n + ' שהוכרעו ביחידה'));
  L.push('', '## החלפות ומחיקות מסוימות שנדחו 3 פעמים ומעלה', '');
  if (!R.pairs.length) L.push('אין עדיין.');
  R.pairs.forEach((p) => L.push('- "' + p.pair + '" - ' + p.n + ' פעמים (' + p.slugs.join(', ') + ')'));
  return L.join('\n') + '\n';
}
if (process.argv[1] && process.argv[1].endsWith('units_report.mjs')) {
  const weekly = process.argv.includes('--weekly'), print = process.argv.includes('--print');
  if (weekly && fs.existsSync(OUTJ)) { try { const o = JSON.parse(fs.readFileSync(OUTJ, 'utf8')); if (Date.now() - (o.t || 0) < 7 * 864e5) { console.log('הדוח השבועי עדכני'); process.exit(0); } } catch (e) {} }
  const R = analyze(0);
  if (print) { console.log(text(R)); process.exit(0); }
  fs.mkdirSync(path.dirname(OUTJ), { recursive: true });
  fs.writeFileSync(OUTJ, JSON.stringify(R, null, 1));
  fs.writeFileSync(OUTM, text(R));
  console.log('נכתב:', path.relative(ROOT, OUTJ), path.relative(ROOT, OUTM), '· נדחה בעקביות:', R.consistent.map((c) => c.label || c.kind).join(', ') || 'אין');
}
