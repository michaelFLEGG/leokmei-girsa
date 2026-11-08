/* פרומפט 27 (8.11.2026): מחיקת עיטור ליד כותרת - השומר מקבל רק עיטור שבקטע ושצמוד לכותרת נושא / ד"ה.
   וההצעה של סבב בבא בתרא פרק ה (data/sakem/out/bava-batra-s3799-p27r.json) עוברת את השומר כולה.
   הרצה: node tools/sakem_tests/guard_p27.mjs  (בלי רשת ובלי מודל) */
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
const require = createRequire(import.meta.url);
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const SKC = require(path.join(ROOT, 'tools', 'sakem_core.js'));
const NL = String.fromCharCode(10);
let fail = 0;
const ok = (c, m) => { console.log((c ? 'עבר  ' : 'נכשל ') + m); if (!c) fail++; };
const run = (orig, text) => { const h = SKC.hatzDel(orig, text); return { h, near: h.ids.map((id) => SKC.hatzNearHead(text, id)), errs: SKC.check(h.orig, h.text, {}).errs }; };
{ const r = run(['[קבוע:10]', '(נושא) המוכר את הספינה', 'שורה'].join(NL), ['[מחק-עיטור:10]', '(נושא) המוכר את הספינה', 'שורה'].join(NL));
  ok(!r.h.bad.length && r.near[0] && !r.errs.length, 'עיטור לפני כותרת נושא - נמחק'); }
{ const r = run(['(דה) המוכר', '[מקור:x]', '[קבוע:10]', 'שורה'].join(NL), ['(דה) המוכר', '[מקור:x]', '[מחק-עיטור:10]', 'שורה'].join(NL));
  ok(r.near[0] && !r.errs.length, 'עיטור אחרי כותרת ד"ה (בדילוג על מקור) - נמחק'); }
{ const r = run(['[קבוע:10]', '(נושא) כותרת', 'שורה'].join(NL), ['[מחק-עיטור:11]', '(נושא) כותרת', 'שורה'].join(NL));
  ok(r.h.bad.length === 1 && r.errs.length > 0, 'מחיקת עיטור שאינו בקטע - נדחית'); }
{ const r = run(['שורה א', '[קבוע:10]', 'שורה ב'].join(NL), ['שורה א', '[מחק-עיטור:10]', 'שורה ב'].join(NL));
  ok(!r.near[0], 'עיטור בין שתי שורות רגילות - אינו צמוד לכותרת'); }
{ const r = run(['[קבוע:10]', '(נושא) כותרת'].join(NL), ['(נושא) כותרת'].join(NL));
  ok(r.errs.length > 0, 'עיטור שנעלם בלי סימן מחיקה - נדחה'); }
const O = JSON.parse(fs.readFileSync(path.join(ROOT, 'data', 'sakem', 'out', 'bava-batra-s3799-p27r.json'), 'utf8'));
let bad = 0;
for (const it of O.items) { const h = SKC.hatzDel(it.orig, it.text); if (h.bad.length) bad++;
  const pre = new Set(SKC.check(h.orig, h.orig, {}).errs);
  const e = SKC.check(h.orig, h.text, {}).errs.filter((x) => !pre.has(x) && !/קצר מהמקור|ארוך מהמקור|מספור/.test(x)); if (e.length) { bad++; console.log('  ', it.iid, e.join(' · ')); } }
ok(!bad, 'סבב בבא בתרא פרק ה: כל ' + O.items.length + ' הקטעים עוברים את השומר');
console.log(fail ? 'נכשלו ' + fail : 'הכל עבר');
process.exit(fail ? 1 : 0);
