/* פרומפט 65 (19.11.2026): "והך" בכותרת צד מותר בשומר הלשון (כלל 21), ובגוף השורה - נשאר אסור.
   הרצה: node tools/sakem_tests/p65_vehach.mjs  (קוד יציאה 1 בכישלון) */
import { createRequire } from 'module';
const S = createRequire(import.meta.url)('../sakem_core.js');
const aram = (t) => S.obey(t, {}).filter((x) => /ארמית/.test(x) && /והך/.test(x)).length;
const cases = [
  ['[צד:והך:] בכותרת צד', '[צד:והך:]\nוהרי בשנים אין מזיקין! - במקומן חוששים.', 0],
  ['[צד:והך דתניא:] בכותרת צד', '[צד:והך דתניא:]\nהכורע בהודאה - הרי זה מגונה! - בברהמ"ז.', 0],
  ['[צד:והך דר"י] בכותרת צד', '[צד:והך דר"י]\nשהכשיר נסרי ארז! - בהדס.', 0],
  ['והך בגוף השורה - נשאר אסור', '[צד:רבא:]\nוהך שאמר רבי - כך.', 1],
  ['כותרת צד ארוכה שפותחת בוהך - נשארת אסורה', '[צד:והך שאמר רבי עכשיו:]\nכך.', 1],
];
let bad = 0;
for (const [name, t, want] of cases) { const got = aram(t); console.log((got === want ? 'עבר  ' : 'נכשל ') + name); if (got !== want) bad++; }
process.exit(bad ? 1 : 0);
