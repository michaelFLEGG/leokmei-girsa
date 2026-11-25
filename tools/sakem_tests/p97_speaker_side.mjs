// פרומפט 97: דובר בפתח שורה מצטרף לכותרת צד קצרה קיימת (והא / ת"ש / מקף)
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const S = require('../sakem_core.js');
const cases = [
  ['[צד:והא]\n{אם:דתנן:} \'בשבעה דרכים בודקין את הזב\' ולא \'דברים\'', '[צד:והא דתנן:]'],
  ['[צד:-]\n{אם:אביי:} לא להשחתה, שלמד פאת פאת מבני אהרן.', '[צד:- אביי:]'],
  ['[צד:ת"ש:]\n{אם:דתניא:} האומר חרופה ביהודה - מקודשת, שכך קורין', '[צד:ת"ש דתניא:]'],
];
const keep = ['[צד:ופשטו אחת:]\n{אם:דתניא:} האומר לקוחתי - מקודשת, דכי יקח איש',
  '[צד:ת"ר:]\n{אם:נאמר:} כבד את אביך ואת אמך {אם:ונאמר:} כבד את ה\' מהונך'];
let bad = 0;
for (const [t, want] of cases) { const r = S.speakerOut(t).text.split('\n')[0]; if (r !== want) { bad++; console.log('נכשל:', r, '!=', want); } }
for (const t of keep) { if (S.speakerOut(t).text !== t) { bad++; console.log('שונה בטעות:', t); } }
console.log(bad ? 'כשלים ' + bad : 'p97 תקין');
process.exit(bad ? 1 : 0);
