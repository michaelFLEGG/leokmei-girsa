/* פרומפט 33 (12.11.2026): "סכם חייב לציית" - הבדיקות שעוצרות את put על כללים שהמנהל תיקן ביד יותר מפעם אחת.
   הרצה: node tools/sakem_tests/guard_p33.mjs */
import fs from 'node:fs'; import path from 'node:path'; import { createRequire } from 'node:module'; import { fileURLToPath } from 'node:url';
const require = createRequire(import.meta.url);
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const SKC = require(path.join(ROOT, 'tools', 'sakem_core.js'));
let bad = 0; const ok = (name, c) => { console.log((c ? 'עבר  ' : 'נכשל ') + name); if (!c) bad++; };
const E = (t, o) => SKC.comply(t, t, Object.assign({ strict: true }, o || {})).errs;
const has = (a, re) => a.some((x) => re.test(x));
ok('סוגריים מרובעים בלי {הס:} - חוסם', has(E('שלחין [של עור] מותר.'), /סוגריים מרובעים/));
ok('סוגריים בתוך {הס:} - עובר', !has(E('שלחין {הס:[של עור]} מותר.'), /סוגריים מרובעים/));
ok('עוגן תוס\' אינו סוגריים', !has(E("שלחין מותר[תוס':12]."), /סוגריים מרובעים/));
ok('ציון מקור עם נימוק ב-keep - עובר', !has(E('כמו ששנה [פ"ז] המוציא.', { keep: ['כמו ששנה פז - ציון מקור, לא ביאור'] }), /סוגריים מרובעים/));
ok('תבליט • - חוסם', has(E('{ב:• }קומקום ע"ג קומקום - מותר.'), /תבליט/));
ok('תבליט · - חוסם', has(E('· רבא: כך.'), /תבליט/));
ok('{ב:.} יתום - חוסם', has(E('וצונן ע"ג קומקום - אסור, שמוליד{ב:.}'), /הדגשה יתומה/));
ok('ארמית שנלמדה (אפי\') - חוסם', has(E("אפי' אומן אינו מקפיד."), /ארמית שהמנהל/));
ok('ארמית בתוך {כב:} - עובר', !has(E("{כב:אפי' אומן}."), /ארמית שהמנהל/));
ok('"ואם פתח חייב" בלי מקף - חוסם', has(E('ואם פתח חייב, ואינו דומה למגופת חבית.'), /מקף בין המקרה לדין/));
ok('"ואם פתח - חייב" - עובר', !has(E('ואם פתח - חייב, ואינו דומה למגופת חבית.'), /מקף בין המקרה לדין/));
ok('"ושל אומן אסור, שמקפיד" (לשון המנהל) - עובר', !has(E('של בעה"ב מותר, ושל אומן אסור, שמקפיד.'), /מקף/));
ok('מילת מהלך בפתח שורה בלי כותרת - חוסם', has(E('וכתנאי: {אם:לת"ק} אסור.'), /מילת מהלך/));
ok('שם ארוך עם בן בפתח שורה - חוסם', has(E('{אם:ר\' יונתן בן אלעזר:} של בעה"ב מותר.'), /שם ארוך/));
ok('מספור בהדגשה {ב:א.} - חוסם', has(E('{ב:א.} שאפשר להטמין בצונן.'), /מספור בהדגשה/));
ok('בשרת (בלי strict) - אזהרה בלבד', SKC.comply('אפי\' כך.', 'אפי\' כך.', {}).errs.length === 0);
ok('רשימת הבדיקה העצמית: חסר - מוחזר', SKC.selfCheckMissing({}).length === SKC.SELF_CHECK.length);
ok('רשימת הבדיקה העצמית: מלאה - עוברת', SKC.selfCheckMissing(Object.fromEntries(SKC.SELF_CHECK.map((x) => [x[0], true]))).length === 0);
/* המדד המעשי: נוסח המנהל אחרי תיקוניו (שבת ד) כמעט נקי, והצעות סכם הישנות נעצרות במה שהמנהל תיקן */
const q = JSON.parse(fs.readFileSync(path.join(ROOT, 'data', 'sakem', 'queue', 'shabbat-p4.json'), 'utf8'));
const fin = SKC.obey(SKC.toInter(q.units).text, {}).filter((x) => x[0] !== '~');
ok('נוסח המנהל בשבת ד: עד 5 עצירות (נמצאו ' + fin.length + ')', fin.length <= 5);
const oldF = path.join(ROOT, 'data', 'sakem', 'out', 'shabbat-p4.old.json');
if (fs.existsSync(oldF)) { let n = 0; JSON.parse(fs.readFileSync(oldF, 'utf8')).items.forEach((it) => { if (it.text) n += SKC.obey(it.text, {}).filter((x) => x[0] !== '~').length; });
  ok('הצעות סכם הישנות בשבת ד נעצרות (' + n + ' עצירות, לפחות 15)', n >= 15); }
console.log(bad ? bad + ' נכשלו' : 'הכל עבר'); process.exit(bad ? 1 : 0);
