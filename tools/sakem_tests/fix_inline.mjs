/* בדיקת החזרת העוגנים שבתוך השורה אחרי עריכה ידנית (פרומפט 20, 5.11.2026).
   הרצה: node tools/sakem_tests/fix_inline.mjs  (בלי רשת ובלי מפתח). קוד יציאה 1 בכשל. */
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const SKC = require('../sakem_core.js');
const orig = ["[דף:כה.]", "[צד:{אם:רבא:}]", "אמר ה{הס:דין} כך[תוס':3] ועוד מילים רבות בשורה הזאת", "[מס:ב]שנייה עם[תוס':4] סוף", "שלישית בלי כלום[תוס':5]"].join('\n');
const cases = {
  'מחיקת מילות הד"ה עם העוגן': orig.replace("כך[תוס':3] ", '').replace("[תוס':4]", ''),
  'כל העוגנים נמחקו': orig.replace(/\[תוס':\d\]/g, '').replace('[מס:ב]', ''),
  'סדר עוגנים שונה': orig.replace("[תוס':3]", '').replace('סוף', "סוף[תוס':3]"),
  'הדבקה על פני עוגן': orig.replace("עם[תוס':4] סוף", 'עם טקסט שהודבק סוף'),
  'בלי שינוי': orig,
};
let bad = 0;
for (const [k, t] of Object.entries(cases)) {
  const r = SKC.fixInline(orig, t);
  const g = SKC.guard(orig, r.text, { edited: true }).filter((x) => /נעולים/.test(x));
  const ok = !g.length && (r.text.match(/\[(תוס'|מס):/g) || []).length === 4;
  if (!ok) bad++;
  console.log((ok ? 'עבר  ' : 'נכשל ') + k + (r.moved.length ? '  (הוחזר למקום משוער: ' + r.moved.join(', ') + ')' : ''));
}
/* צ'יפ העוגן בתצוגה חוזר לעוגן בקריאה חזרה */
const h = SKC.i2h("מילה[תוס':7] אחרת", true);
if (SKC.h2i(h) !== "מילה[תוס':7] אחרת") { bad++; console.log('נכשל  צ\'יפ העוגן אינו נקרא חזרה'); } else console.log('עבר  צ\'יפ העוגן נקרא חזרה');
if (/tzc/.test(SKC.i2h("מילה[תוס':7]", false))) { bad++; console.log('נכשל  העוגן נכתב לדף'); }
process.exit(bad ? 1 : 0);
