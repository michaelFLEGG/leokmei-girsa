/* פרומפט 26 (8.11.2026): בדיקות השומר על ההצעות שבעל הפרויקט דחה או תיקן בבכורות ובבבא בתרא.
   כל הצעה ישנה חייבת להיכשל: ארמית במקום לשון הקודש (שגיאה), או הידוק יתר (דגל לקורא הנפרד).
   ומנגד: הדוגמאות הטובות (sakem-examples.json, לפני -> אחרי) אינן נכשלות בארמית.
   הרצה: node tools/sakem_tests/guard_p26.mjs  (בלי רשת ובלי מודל) */
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
const require = createRequire(import.meta.url);
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const SKC = require(path.join(ROOT, 'tools', 'sakem_core.js'));
const D = JSON.parse(fs.readFileSync(path.join(ROOT, 'data', 'sakem', 'decisions', 'bekhorot-review-8.11.json'), 'utf8'));
const byId = (id, i = 0) => D.items.filter((x) => x.id === id)[i];
const alt = (id) => { const x = byId(id); return x; };
const T = [];
const aram = (name, keep, bad) => T.push({ name, kind: 'ארמית', orig: keep, prop: bad });
const sq = (name, orig, prop) => T.push({ name, kind: 'הידוק', orig, prop });
// ארמית במקום לשון הקודש שכבר כתובה (או שהמנהל כתב)
{ const x = alt('bf484adda'); aram('בכורות כז: שקלה בריש מסא', x.variants.find((v) => /עברית|בהיר/.test(v.tag)).text, x.variants.find((v) => /ארמית/.test(v.tag)).text); }
{ const x = alt('bbec0d710'); aram('בכורות כו: איפכא', x.final, x.variants[1].text); }
{ const x = alt('b75731cd0'); aram('בכורות כט: חדא', x.final, x.variants[0].text); }
{ const x = alt('b53902e38'); aram('בכורות לה: תלינן', x.final, x.variants[1].text); }
{ const x = alt('b6da746c8'); aram('בכורות לה: כוותיה', x.final, x.variants[1].text.replace('דריב"ק,', 'דריב"ק ות"ק כוותיה,')); }
{ const x = byId('bekhorot-p8:s36', 3); aram('בכורות נב: לאיתויי', x.final, x.prop); }
{ const x = alt('be9b1ed6d'); aram('בכורות לב: מר כי אתריה', x.final, x.variants[1].text); }
aram('בבא בתרא עג: טייעא במקום סוחר', 'והיה עובר תחתיו הסוחר רכוב על גמל', 'ונכנס טייעא תחתיה');
// הידוק עד אי הבנה (שתי ההצעות שבוטלו)
D.items.filter((x) => x.src === 'סכם קטע - בוטל').forEach((x) => sq('בוטל: ' + x.id, x.orig, x.prop));
let fail = 0;
T.forEach((t) => {
  const ck = SKC.check(t.orig, t.prop, {});
  const s = SKC.squeeze(t.orig, t.prop);
  const hit = t.kind === 'ארמית' ? ck.errs.some((e) => /ארמית במקום לשון הקודש/.test(e)) : s.flag;
  if (!hit) fail++;
  console.log((hit ? 'עבר ' : 'נכשל') + ' · ' + t.kind + ' · ' + t.name + (t.kind === 'הידוק' ? ' (' + Math.round(s.ratio * 100) + '%)' : ' (' + SKC.aramNew(t.orig, t.prop).join(', ') + ')'));
});
// הדוגמאות הטובות אינן נכשלות בארמית
const EX = JSON.parse(fs.readFileSync(path.join(ROOT, 'data', 'sakem', 'sakem-examples.json'), 'utf8')).pairs;
EX.forEach((p, i) => { const a = SKC.aramNew(p.before, p.after); if (a.length) { fail++; console.log('נכשל · דוגמה טובה ' + (i + 1) + ' (' + p.kind + ') נתפסה כארמית: ' + a.join(', ')); }
  if (p.bad && /ארמית|שכבר כתובה|תרגום/.test(p.kind)) { const b = SKC.aramNew(p.after, p.bad); if (!b.length) { fail++; console.log('נכשל · הפסול בדוגמה ' + (i + 1) + ' לא נתפס'); } } });
console.log(fail ? '\n' + fail + ' כשלים' : '\nכל ' + T.length + ' ההצעות הפסולות נכשלו בשומר, והדוגמאות הטובות עברו.');
process.exit(fail ? 1 : 0);
