// פרומפט 30 (10.11.2026): שער האורך של הכיתוב - ההודעה היומית היא תמונה עם כיתוב, וכיתוב של תמונה בווטסאפ מוגבל ל-1024 תווים.
// מריץ בדיוק את קוד השרת (worker/leokmei-daf/src/core.js) על התוכן המקומי (data/daf-wa), לכל יום שליחה בימים הקרובים,
// כולל ימי שישי וערבי חג שבהם יוצאים כמה דפים יחד. חריגה - יציאה בקוד 1 (עצירה רועשת) עם הוראה לכותב:
// להוסיף לדפים של אותו יום שדה short - רשימת מספרי השורות (מתוך השורות שכבר נבדקו) שייכנסו להודעה המשותפת.
// לעולם לא מפצלים להודעה שנייה: בהעברה עוברת רק אחת מהן.
//   node tools/daf_wa/caplen.mjs [ימים=21]
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { CAP_MAX, ilKey, addDays, dayMeta, dafimFor, compose, capLen, gq, linesOf } from '../../worker/leokmei-daf/src/core.js';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const DATA = path.join(ROOT, 'data', 'daf-wa');
const days = +(process.argv[2] || 21);
const today = ilKey(Date.now());
let bad = 0, n = 0;
for (let i = 0; i < days; i++) {
  const k = addDays(today, i), meta = dayMeta(k);
  if (meta.noSend) continue;
  const items = dafimFor(k).map((x) => {
    const f = path.join(DATA, x.slug + '-' + x.n + '.json');
    return Object.assign({}, x, { c: fs.existsSync(f) ? JSON.parse(fs.readFileSync(f, 'utf-8')) : null });
  });
  const lack = items.filter((x) => !x.c || !(x.c.check && x.c.check.ok));
  if (lack.length) { console.log(k, '- אין עדיין תוכן בדוק:', lack.map((x) => x.name + ' ' + gq(x.n)).join(', ')); continue; }
  n++;
  // הדף שפותח את ההודעה: השאלה ("הידעת") וחלופותיה נלקחות ממנו, ולכן שורות התשובה שלהן חייבות להיות בהודעה
  const c0 = items[0].c, sh0 = linesOf(c0);
  const lost = [c0.hook].concat(c0.alts || []).filter((q) => q && Number.isInteger(q.ans) && !sh0.includes(q.ans));
  if (lost.length) { bad++; console.log('!!!', k, items[0].slug + '-' + items[0].n, '- ב-short חסרות שורות התשובה:', lost.map((q) => q.ans).join(', ')); }
  // הארוכה שבשאלות ("הידעת" שבברירת המחדל או אחת החלופות) - כדי שגם בחירה בלוח לא תחרוג
  const picks = [null].concat((items[0].c.alts || []).map((_, j) => j));
  const len = Math.max(...picks.map((p) => capLen(compose(meta, items, p === null ? {} : { pick: p }))));
  const label = items.map((x) => x.name + ' ' + gq(x.n)).join(' + ');
  if (len > CAP_MAX) {
    bad++;
    console.log('!!!', k, label, '-', len, 'תווים, המרבי', CAP_MAX,
      '- הוסף short (מספרי שורות מתוך הבדוקות, כולל שורות התשובה של השאלה ושל החלופות) לדפים: ' + items.map((x) => x.slug + '-' + x.n).join(', '));
  } else console.log(k, label, len + '/' + CAP_MAX);
}
console.log('שער האורך: %d ימי שליחה, %d חורגים', n, bad);
process.exit(bad ? 1 : 0);
