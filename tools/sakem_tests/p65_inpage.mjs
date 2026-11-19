/* פרומפט 65 (19.11.2026): "ההצעה כבר בנוסח" - הבדיקה שהכלים האוטומטיים (closeAll, verify) עושים לפני שהם רושמים "התקבל"
   בלי להחיל. נקראת הפונקציה עצמה מתוך tools/sakem_perek.js (לא העתק).
   המקרים מן האתר: סוכה מב: (19.11.2026) - הצעה ששינתה רק "אפי'" ל"אף" נרשמה "התקבל" ולא הוחלה, ואיחוד שורות
   (האותיות זהות) נחשב "כבר בנוסח" כי הדף חובר למחרוזת אחת.
   הרצה: node tools/sakem_tests/p65_inpage.mjs  (קוד יציאה 1 בכישלון) */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
const DIR = path.dirname(fileURLToPath(import.meta.url));
const src = fs.readFileSync(path.join(DIR, '..', 'sakem_perek.js'), 'utf8');
const a = src.indexOf('  const skpLet='), b = src.indexOf('  window.skpInPageTest');
if (a < 0 || b < 0) { console.error('הפונקציות לא נמצאו ב-sakem_perek.js'); process.exit(1); }
const T = new Function(src.slice(a, b) + '\nreturn {skpLet,skpChanged,skpInPage};')();
/* דף מדומה: אותו פורמט שהקוד בונה (skpPageLines) - שורה לכל שורת נוסח, אותיות בלבד */
const page = (lines) => '\n' + lines.map(T.skpLet).filter(Boolean).join('\n') + '\n';
const P = page([
  '[דף:מב:]',
  "{דה:מקבלת אשה מבנה ובעלה:} אפי' שאינה בת חיוב.",
  '(רווח) {דה:קטן היודע לנענע:} חייב, {כב:להתעטף} - בציצית,',
  '{כב:לשמור תפלין} - אביו לוקח לו תפלין,',
  '[צד:ויקשה:]',
  'והרי פיל - פלא נעשה לו!',
  '[צד:-]',
  'כאן - כשעליו אוכף, וכאן - כשאין עליו.',
]);
const orig1 = "{דה:מקבלת אשה מבנה ובעלה:} אפי' שאינה בת חיוב.\n(רווח) {דה:קטן היודע לנענע:} חייב, {כב:להתעטף} - בציצית,\n{כב:לשמור תפלין} - אביו לוקח לו תפלין,";
const cases = [
  ['שורה אחת שונתה (אפי\' -> אף), השאר זהות: אינה בנוסח', { orig: orig1, text: orig1.replace("אפי'", 'אף') }, false],
  ['איחוד שתי שורות (אותיות זהות): אינו בנוסח', { orig: '[צד:ויקשה:]\nוהרי פיל - פלא נעשה לו!\n[צד:-]\nכאן - כשעליו אוכף, וכאן - כשאין עליו.',
    text: '[צד:והרי]\nפיל - פלא נעשה לו! - כאן - כשעליו אוכף, וכאן - כשאין עליו.' }, false],
  ['הצעה שכבר הוחלה: בנוסח', { orig: 'שורה ישנה לגמרי אחרת כאן', text: "{דה:מקבלת אשה מבנה ובעלה:} אפי' שאינה בת חיוב." }, true],
  ['הצעה בלי שום שינוי בשורות: בנוסח', { orig: orig1, text: orig1 }, true],
  ['שינוי סימון בלבד (אותיות זהות, אותה שורה): בנוסח', { orig: orig1, text: orig1.replace('{כב:לשמור תפלין}', '{ב:לשמור תפלין}') }, true],
];
let bad = 0;
for (const [name, x, want] of cases) {
  const got = T.skpInPage(x, P);
  console.log((got === want ? 'עבר  ' : 'נכשל ') + name);
  if (got !== want) bad++;
}
process.exit(bad ? 1 : 0);
