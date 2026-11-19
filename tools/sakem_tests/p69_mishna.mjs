/* פרומפט 69 (19.11.2026): תיבת המשנה - שם תנא בלי {אם:} (חוסם), סוגריים בלי {הס:} (חוסם, גם במשנה), ושורת דין בלי הדגשה
   (אזהרה); ומנוע סבב הצורה (round_form.mjs --auto-tanna --auto-brackets, כללי bold לשורה) - בלי לשנות אות.
   הרצה: node tools/sakem_tests/p69_mishna.mjs  (קוד יציאה 1 בכישלון) */
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const S = createRequire(import.meta.url)(path.join(ROOT, 'tools', 'sakem_core.js'));
const M = (lines) => '[משנה:א]\n' + lines.join('\n') + '\n[גמרא]\nגמרא.';
const C = (t, keep) => S.comply(t, t, { strict: true, keep });
const has = (arr, re) => arr.some((x) => re.test(x));
let bad = 0;
const ok = (name, cond) => { console.log((cond ? 'עבר  ' : 'נכשל ') + name); if (!cond) bad++; };

/* (1) שם תנא בתיבת המשנה */
ok('תנא בסגנון "משנה" {מש:רבי יוסי:} - נעצר', has(C(M(['{ב:שלא להספיד} - לפניו אסור.', '{מש:רבי יוסי:} לפניו ואחריו אסור.'])).errs, /שם תנא/));
ok('תנא בלי סגנון ("ולא הודו לו חכמים") - נעצר', has(C(M(['{אם:ר"י:} מחייב {ב:בכפיית המטה}, ולא הודו לו חכמים.'])).errs, /שם תנא.*חכמים/));
ok('תנא בתוך ההדגשה - נעצר (בסגנון אמורא גם בתוך ההדגשה)', has(C(M(['{ב:רשב"ג אומר:} ישנה.'])).errs, /שם תנא/));
ok('תנא ב-{אם:} - עובר', !has(C(M(['{אם:רבי יוסי:} לפניו ואחריו {ב:אסור}.', 'ולא הודו לו {אם:חכמים}.'])).errs.concat(C(M(['{אם:רבי יוסי:} לפניו ואחריו {ב:אסור}.'])).warns), /שם תנא/));
ok('ר"ח כסליו (ראש חודש) - לא שם, אינו נעצר ואינו מוזהר', !has(C(M(['{ב:הגיע ר"ח כסליו} ולא ירדו גשמים.'])).errs.concat(C(M(['{ב:הגיע ר"ח כסליו} ולא ירדו גשמים.'])).warns), /שם תנא/));
ok('ב"ד גוזרין - אינו שם', !has(C(M(['{ב:ב"ד גוזרין} ג\' תעניות.'])).errs, /שם תנא/));
{ const c = C(M(['נמנו ורבו ב"ש על ב"ה, {ב:וי"ח דברים} גזרו.'])); ok('ב"ש / ב"ה בלי נקודתיים - ספק: אזהרה ולא חסימה', !has(c.errs, /שם תנא/) && has(c.warns, /שם תנא.*ספק/)); }
ok('וב"ה אומרים: - נעצר', has(C(M(['{ב:ב"ש} אוסרין, וב"ה אומרים: מותר.'])).errs, /שם תנא.*ב"ה/));
ok('שם תנא מחוץ לתיבת המשנה - אינו נבדק בכלל הזה', !has(C('[גמרא]\nולא הודו לו חכמים.').errs, /שם תנא בתיבת/));
ok('פטור בנימוק ב-keep', !has(C(M(['{ב:שלא להספיד} - לפניו אסור.', '{מש:רבי יוסי:} לפניו ואחריו אסור.']), ['רבי יוסי לפניו - לשון המשנה כפי שהיא בוורד, נשאר במכוון']).errs, /שם תנא/));
/* (4) סוגריים בתיבת המשנה */
ok('סוגריים בתיבת המשנה בסגנון רגיל ({מש:[עננו]}) - נעצר', has(C(M(['על אלו מתריעין {מש:[עננו]} {ב:בשבת}:'])).errs, /סוגריים/));
ok('סוגריים בתיבת המשנה בלי סגנון - נעצר', has(C(M(['על אלו מתריעין {ב:בכל מקום} [מכה מהלכת]'])).errs, /סוגריים/));
ok('{הס:[...]} בתיבת המשנה - עובר', !has(C(M(['על אלו מתריעין {ב:בכל מקום} {הס:[מכה מהלכת]}'])).errs, /סוגריים/));
ok('עוגן [תוס\':N] בתיבת המשנה - עובר', !has(C(M(['{ב:מאימתי}[תוס\':1001] מזכירין גבורות גשמים?'])).errs, /סוגריים/));
/* (2) דין בלי הדגשה - אזהרה בלבד */
{ const c = C(M(['{ב:ראשונות} - משמר מתענין,', 'שניות - משמר רק מתענין, ובית אב לא מתענין כלל,'])); ok('שורת משנה עם דין בלי הדגשה - אזהרה, לא חסימה', has(c.warns, /דין בלי הדגשה/) && !has(c.errs, /דין בלי הדגשה/)); }
ok('שורת משנה עם דין ועם הדגשה - בלי אזהרה', !has(C(M(['{ב:שניות} - משמר רק מתענין.'])).warns, /דין בלי הדגשה/));
ok('שורת סיפור בלי דין - בלי אזהרה', !has(C(M(['{ב:תקעו} הכהנים.', 'עג עוגה ועמד בתוכה.'])).warns, /דין בלי הדגשה/));

/* המנוע: round_form.mjs */
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'p69-'));
const base = [{ iid: 's1', ids: [1, 2], text: M(['{ב:שלא להספיד} - לפניו אסור, אחריו מותר.', '{מש: רבי יוסי:} לפניו ואחריו אסור.', 'שניות - משמר רק מתענין, ובית אב לא מתענין כלל,',
  'על אלו מתריעין {מש:[עננו]} בשבת, ולא הודו לו {מש:חכמים.}', '{ב:הגיע ר"ח כסליו} ולא ירדו גשמים [סימן קללה].', 'ובית אב לא, ובית אב כן.']) }];
fs.writeFileSync(path.join(tmp, 'base.json'), JSON.stringify(base));
fs.writeFileSync(path.join(tmp, 'rules.json'), JSON.stringify({ bold: { s1: [{ i: 3, w: 'שניות' }, { i: 3, w: 'משמר רק מתענין' }, { i: 6, w: 'ובית אב', n: 2 }, { i: 1, w: 'שלא להספיד' }] } }));
const run = (extra) => execFileSync('node', [path.join(ROOT, 'tools', 'sakem', 'round_form.mjs'), path.join(tmp, 'base.json'), path.join(tmp, 'rules.json'), 'test-s1-x', 'test', 'T', ...extra], { cwd: ROOT, encoding: 'utf8' });
const so = run(['--auto-tanna', '--auto-brackets', '--seg-dir', path.join(tmp, 'seg')]);
const got = JSON.parse(fs.readFileSync(path.join(tmp, 'seg', 'seg-1.json'), 'utf8')).text;
const lt = (t) => S.plainI(t).replace(/\s+/g, '');
ok('המנוע: האותיות זהות למקור', lt(got) === lt(base[0].text));
ok('המנוע: {מש: רבי יוסי:} - {אם: רבי יוסי:}', got.includes('{אם: רבי יוסי:} לפניו'));
ok('המנוע: {מש:חכמים.} - {אם:חכמים}. (הנקודה מחוץ לסגנון)', got.includes('{אם:חכמים}.'));
ok('המנוע: {מש:[עננו]} - {הס:[עננו]}, ו[סימן קללה] - {הס:[סימן קללה]}', got.includes('{הס:[עננו]}') && got.includes('{הס:[סימן קללה]}'));
ok('המנוע: ר"ח כסליו לא נעטף', got.includes('{ב:הגיע ר"ח כסליו}') && /הוחרג/.test(so));
ok('המנוע: כמה הדגשות לאותה שורה', got.includes('{ב:שניות} - {ב:משמר רק מתענין}, ובית אב'));
ok('המנוע: הדגשה במופע השני (n)', got.includes('ובית אב לא, {ב:ובית אב} כן.'));
ok('המנוע: אין הדגשה כפולה (מילים שכבר מודגשות - מדווח)', !got.includes('{ב:{ב:') && /כבר מודגש: שלא להספיד/.test(so));
ok('המנוע: בלי הדגלים - ללא שינוי בתנאים ובסוגריים', !fs.existsSync(path.join(tmp, 'seg2')) && (run(['--seg-dir', path.join(tmp, 'seg2')]), JSON.parse(fs.readFileSync(path.join(tmp, 'seg2', 'seg-1.json'), 'utf8')).text.includes('{מש: רבי יוסי:}')));
fs.rmSync(tmp, { recursive: true, force: true });
process.exit(bad ? 1 : 0);
