/* סריקת כותרות צד ארוכות וכפילויות אחרי כותרת (פרומפט 22, 8.11.2026).
   הרצה: node tools/sakem/scan_titles.mjs site/*.data.js   (כותב data/sakem/titles-scan/<slug>.json ומדפיס סיכום)
   אינו משנה את הוורד ואת הנתונים: רק מכין הצעות מוכנות (כותרת נושא + כותרת צד קצרה, או מחיקת הכפילות). */
import fs from 'fs';
import path from 'path';
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const SKC = require('../sakem_core.js');
const OUT = path.join(path.dirname(new URL(import.meta.url).pathname), '..', '..', 'data', 'sakem', 'titles-scan');
fs.mkdirSync(OUT, { recursive: true });
const order = ['bekhorot', 'berakhot', 'sukkah', 'ketubot', 'shabbat'];
const files = process.argv.slice(2).sort((a, b) => {
  const f = (x) => { const i = order.indexOf(path.basename(x).replace('.data.js', '')); return i < 0 ? 99 : i; };
  return f(a) - f(b);
});
const total = {};
for (const f of files) {
  let s = fs.readFileSync(f, 'utf8').replace(/^const DATA=/, '').replace(/,SLUG="[^"]*"(?:,[A-Z_]+=[^;]*)?;\s*$/, '');
  const D = JSON.parse(s), slug = path.basename(f).replace('.data.js', '');
  const items = []; let nLong = 0, nDup = 0;
  D.pages.forEach((p) => {
    const units = p.units.map((u, i) => Object.assign({}, u, { daf: p.daf, first: i === 0 }));
    const text = SKC.toInter(units).text;
    const fixed = SKC.autofixTitles(text);
    if (!fixed.items.length) return;
    const ids = units.filter((u) => u.id != null).map((u) => u.id);
    fixed.items.forEach((it) => { if (it.kind === 'long') nLong++; else nDup++; items.push(Object.assign({ daf: p.daf, unit: ids[0] }, it)); });
  });
  fs.writeFileSync(path.join(OUT, slug + '.json'), JSON.stringify({ slug, generated: '2026-11-08', long: nLong, dup: nDup, items }, null, 1));
  total[slug] = { long: nLong, dup: nDup, manual: items.filter((x) => x.manual).length };
}
const rows = Object.entries(total);
rows.forEach(([k, v]) => console.log(k, 'ארוכות', v.long, 'כפילויות', v.dup, 'ידני', v.manual));
console.log('סה"כ ארוכות', rows.reduce((a, [, v]) => a + v.long, 0), 'כפילויות', rows.reduce((a, [, v]) => a + v.dup, 0));
