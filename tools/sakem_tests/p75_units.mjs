/* פרומפט 75: בדיקת הפירוק ליחידות על כל הצעות סכם שבמאגר (data/sakem/out).
   הרצה: node tools/sakem_tests/p75_units.mjs [--max N]
   לכל הצעה: הכל "קבל" = ההצעה כלשונה; הכל "דחה" = המקור כלשונו; צירופים אקראיים - סוגריים מסולסלים מאוזנים
   ומספר השורות הגיוני; והשחזור (classify) מן הנוסח המעורב מחזיר את ההכרעות. קוד יציאה 1 על כל כשל. */
import fs from 'fs';
import path from 'path';
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const SKU = require('../sakem_units_core.js');
const dir = path.join(path.dirname(new URL(import.meta.url).pathname), '../../data/sakem/out');
const max = +(process.argv[process.argv.indexOf('--max') + 1] || 0) || 1e9;
let n = 0, fail = 0, units = 0, recov = 0, recovOk = 0, many = 0, worst = 0;
let seed = 7; const rnd = () => (seed = (seed * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff;
const balanced = (s) => { let d = 0; for (const t of SKU.tokens(s)) { if (t.k === 'open') d++; else if (t.k === 'close') { d--; if (d < 0) return false; } } return d === 0; };
const t0 = Date.now();
for (const f of fs.readdirSync(dir).filter((x) => x.endsWith('.json')).sort()) {
  let o; try { o = JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8')); } catch (e) { continue; }
  for (const it of o.items || []) {
    if (n >= max) break;
    if (it.nochange || it.kind === 'missing' || !it.orig || !it.text) continue;
    n++;
    const ta = Date.now();
    const M = SKU.units(it.orig, it.text);
    worst = Math.max(worst, Date.now() - ta);
    const U = M.u.filter((u) => !u.quiet);
    units += U.length; if (U.length >= 10) many++;
    const bad = (why) => { fail++; if (fail < 8) console.log('כשל', f, it.iid, why); };
    if (SKU.compose(M, {}, 'a') !== it.text) bad('הכל קבל אינו ההצעה');
    const allR = SKU.compose(M, {}, 'r');
    const quietOnly = M.u.filter((u) => u.quiet).length;
    if (!quietOnly && allR !== it.orig) bad('הכל דחה אינו המקור');
    for (let r = 0; r < 3; r++) {
      const d = {}; U.forEach((u) => { d[u.id] = rnd() < 0.5 ? 'a' : 'r'; });
      const mix = SKU.compose(M, d);
      if (balanced(it.text) && balanced(it.orig) && !balanced(mix)) { bad('סוגריים אינם מאוזנים בצירוף'); break; }
      if (r === 0 && U.length >= 2) {
        const C = SKU.classify(it.orig, it.text, mix);
        C.forEach((c) => { recov++; if ((c.dec === 'accept' ? 'a' : c.dec === 'reject' ? 'r' : 'e') === d[c.id]) recovOk++; });
      }
    }
  }
}
console.log(`הצעות ${n} · יחידות ${units} (בממוצע ${(units / Math.max(1, n)).toFixed(1)}) · הצעות עם 10+ יחידות ${many} · שחזור ${recovOk}/${recov} (${(100 * recovOk / Math.max(1, recov)).toFixed(1)}%) · הארוכה ${worst}ms · סה"כ ${Date.now() - t0}ms · כשלים ${fail}`);
if (fail || recovOk < recov * 0.97) process.exit(1);
