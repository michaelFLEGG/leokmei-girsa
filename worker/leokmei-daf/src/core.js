/* leokmei-daf - הליבה המשותפת (פרומפט 30, 10.11.2026): לוח השנה, הדף היומי והרכבת הכיתוב.
 * הועברה לכאן מ-index.js בלי שינוי בלוח השנה, כדי שבדיקת האורך של הכותב (tools/daf_wa/caplen.mjs) תריץ בדיוק את אותו קוד
 * כמו השרת. בלי fetch ובלי KV - קוד טהור בלבד.
 *
 * ההודעה היומית היא מעכשיו תמונה עם כיתוב (הכרעת בעל הפרויקט, 10.11.2026): תמונה עם כיתוב עוברת בהעברה (Forward) בשלמותה,
 * יחד עם הטקסט, כהודעה אחת - ואילו כרטיס התצוגה המקדימה של קישור אינו עובר תמיד. לכן:
 *  א. הכיתוב הוא כל הנוסח שאושר, באותו סדר וסגנון; הקישור לדף בסוף ("לדף המלא: ..."), ואחריו שורת ההצטרפות לקהילה.
 *  ב. ווטסאפ מגביל כיתוב של תמונה ל-1024 תווים (CAP_MAX). חורג - לא שולחים, ולעולם לא מפצלים להודעה שנייה.
 *     דף שהכיתוב שלו ארוך (ובעיקר שישי וערב חג, כשיוצאים כמה דפים יחד) - נלקחות רק השורות שבשדה short שלו (בחירה מתוך הבדוקות).
 */

export const TZ = 'Asia/Jerusalem';
export const CAP_MAX = 1024;
export const JOIN_URL = 'https://chat.whatsapp.com/DkkfNQeCumeI3cIOXdY73e';
export const JOIN_TEXT = 'לקבלת הדף היומי כל בוקר: ';
const NL = String.fromCharCode(10);

/* ---------- זמן ותאריך עברי (Intl, כמו zyomi-cal) ---------- */
export const DAY = 86400000;
let fmtD = null, fmtT = null, fmtH = null;
export const ilKey = (ms) => (fmtD = fmtD || new Intl.DateTimeFormat('en-CA', { timeZone: TZ, year: 'numeric', month: '2-digit', day: '2-digit' })).format(new Date(ms));
export function ilHM(ms) { fmtT = fmtT || new Intl.DateTimeFormat('en-GB', { timeZone: TZ, hour: '2-digit', minute: '2-digit', hour12: false }); return fmtT.format(new Date(ms)).replace(/^24/, '00'); }
export const dn = (k) => Math.floor(Date.UTC(+k.slice(0, 4), +k.slice(5, 7) - 1, +k.slice(8, 10)) / DAY);
export const keyOf = (n) => new Date(n * DAY).toISOString().slice(0, 10);
export const addDays = (k, i) => keyOf(dn(k) + i);
export const dow = (k) => ((dn(k) % 7) + 11) % 7;   // 0 ראשון ... 6 שבת
export function heb(k) {
  fmtH = fmtH || new Intl.DateTimeFormat('en-u-ca-hebrew', { timeZone: 'UTC', day: 'numeric', month: 'long', year: 'numeric' });
  const o = { d: 0, mn: '', y: 0 };
  fmtH.formatToParts(new Date(dn(k) * DAY + 43200000)).forEach((p) => { if (p.type === 'day') o.d = +p.value; else if (p.type === 'month') o.mn = p.value; else if (p.type === 'year') o.y = +p.value; });
  return o;
}
const L1 = [[400, 'ת'], [300, 'ש'], [200, 'ר'], [100, 'ק'], [90, 'צ'], [80, 'פ'], [70, 'ע'], [60, 'ס'], [50, 'נ'], [40, 'מ'], [30, 'ל'], [20, 'כ'], [10, 'י'], [9, 'ט'], [8, 'ח'], [7, 'ז'], [6, 'ו'], [5, 'ה'], [4, 'ד'], [3, 'ג'], [2, 'ב'], [1, 'א']];
export function letters(n) { if (n === 15) return 'טו'; if (n === 16) return 'טז'; let t = ''; for (const [v, c] of L1) while (n >= v) { t += c; n -= v; } return t.replace(/יה$/, 'טו').replace(/יו$/, 'טז'); }
export const gq = (n) => { const t = letters(n); return t.length > 1 ? t.slice(0, -1) + '"' + t.slice(-1) : t + "'"; };
const MONTH_B = { Tishri: 'בתשרי', Heshvan: 'בחשון', Kislev: 'בכסלו', Tevet: 'בטבת', Shevat: 'בשבט', Adar: 'באדר', 'Adar I': "באדר א'", 'Adar II': "באדר ב'",
  Nisan: 'בניסן', Iyar: 'באייר', Sivan: 'בסיון', Tamuz: 'בתמוז', Av: 'באב', Elul: 'באלול' };
const DOW = ['יום ראשון', 'יום שני', 'יום שלישי', 'יום רביעי', 'יום חמישי', 'יום שישי', 'שבת קודש'];
// ימים טובים (לוח ארץ ישראל) - אין שליחה. מועתק מ-zyomi.js
const YT = [['Tishri', 1, 'ראש השנה'], ['Tishri', 2, 'ראש השנה'], ['Tishri', 10, 'יום הכיפורים'], ['Tishri', 15, 'סוכות'],
  ['Tishri', 22, 'שמיני עצרת'], ['Nisan', 15, 'פסח'], ['Nisan', 21, 'שביעי של פסח'], ['Sivan', 6, 'שבועות']];
export function dayMeta(k) {
  const h = heb(k), w = dow(k);
  const yt = YT.filter(([m, d]) => m === h.mn && d === h.d).map((x) => x[2]);
  const holy = w === 6 || yt.length > 0;
  const hebStr = gq(h.d) + ' ' + (MONTH_B[h.mn] || h.mn) + ' ה' + gq(h.y % 1000);
  return { d: k, dow: w, heb: hebStr, line: (w === 6 ? 'שבת קודש' : DOW[w]) + ' ' + hebStr, noSend: holy, why: w === 6 ? 'שבת' : (yt[0] || '') };
}

/* ---------- הדף היומי (אותו חישוב כמו daf-yomi.js באתר) ---------- */
export const L = [['ברכות', 'berakhot', 2, 63], ['שבת', 'shabbat', 2, 156], ['עירובין', 'eruvin', 2, 104], ['פסחים', 'pesachim', 2, 120],
  ['שקלים', 'shekalim', 2, 21], ['יומא', 'yoma', 2, 87], ['סוכה', 'sukkah', 2, 55], ['ביצה', 'beitzah', 2, 39],
  ['ראש השנה', 'rosh-hashanah', 2, 34], ['תענית', 'taanit', 2, 30], ['מגילה', 'megillah', 2, 31], ['מועד קטן', 'moed-katan', 2, 28],
  ['חגיגה', 'chagigah', 2, 26], ['יבמות', 'yevamot', 2, 121], ['כתובות', 'ketubot', 2, 111], ['נדרים', 'nedarim', 2, 90],
  ['נזיר', 'nazir', 2, 65], ['סוטה', 'sotah', 2, 48], ['גיטין', 'gittin', 2, 89], ['קידושין', 'kiddushin', 2, 81],
  ['בבא קמא', 'bava-kamma', 2, 118], ['בבא מציעא', 'bava-metzia', 2, 118], ['בבא בתרא', 'bava-batra', 2, 175],
  ['סנהדרין', 'sanhedrin', 2, 112], ['מכות', 'makkot', 2, 23], ['שבועות', 'shevuot', 2, 48], ['עבודה זרה', 'avodah-zarah', 2, 75],
  ['הוריות', 'horayot', 2, 13], ['זבחים', 'zevachim', 2, 119], ['מנחות', 'menachot', 2, 109], ['חולין', 'chullin', 2, 141],
  ['בכורות', 'bekhorot', 2, 60], ['ערכין', 'arakhin', 2, 33], ['תמורה', 'temurah', 2, 33], ['כריתות', 'keritot', 2, 27],
  ['מעילה', 'meilah', 2, 21], ['קינים', 'kinnim', 23, 3], ['תמיד', 'tamid', 26, 8], ['מדות', 'middot', 34, 5], ['נדה', 'niddah', 3, 71]];
export const CYCLE = L.reduce((a, x) => a + x[3], 0);
export function dafOf(k) {
  let i = ((dn(k) - dn('2020-01-05')) % CYCLE + CYCLE) % CYCLE;
  for (const [name, slug, first, cnt] of L) { if (i < cnt) return { name, slug, n: first + i, last: first + cnt - 1 }; i -= cnt; }
}

/** הדפים שיוצאים בהודעה של יום k: הדף של היום, ואחריו הדפים של הימים הבאים שאין בהם שליחה (שבת, יום טוב) */
export function dafimFor(k) {
  const out = [dafOf(k)];
  for (let i = 1; i < 4; i++) { const m = dayMeta(addDays(k, i)); if (!m.noSend) break; out.push(dafOf(m.d)); }
  return out;
}

/* ---------- הרכבת הכיתוב (סעיף 2 בפרומפט 23, וצורת התמונה עם כיתוב בפרומפט 30) ---------- */
const lineOf = (c, i) => '◂ ' + c.lines[i].t.replace(/\*/g, '');
export const joinLine = (invite) => JOIN_TEXT + (invite || JOIN_URL);
export const capLen = (t) => [...String(t || '')].length;
/** השורות של דף בהודעה: כולן; ואם הכותב קבע שדה short - רק השורות שבו (בחירה מתוך השורות שכבר נבדקו, בלי ניסוח חדש),
 *  כדי שהכיתוב לא יעבור את 1024 התווים - בעיקר בשישי ובערב חג, כשיוצאים כמה דפים יחד. דף האתר מציג תמיד את כל השורות. */
export function linesOf(c) {
  const all = c.lines.map((_, i) => i);
  if (!Array.isArray(c.short) || !c.short.length) return all;
  return c.short.filter((i) => Number.isInteger(i) && i >= 0 && i < c.lines.length);
}
/* מבנה ההודעה (הכרעת בעל הפרויקט, 8.11.2026 ערב, ובפרומפט 30 - תמונה עם כיתוב):
   השאלה ראשונה ומודגשת (בלי הכותרת "הידעת?"); שם הדף, היום והתאריך - בתמונה, לא בשורות הכיתוב;
   "הדף בקצרה" מודגש; "עוד X דפים" בגופן קוד של ווטסאפ; הקישור לדף בסוף, צמוד לשורה שלפניו; ואחריו שורת ההצטרפות. */
export function compose(meta, items, rec, invite) {
  const first = items[0], c0 = first.c, multi = items.length > 1;
  const pick = rec && Number.isInteger(rec.pick) && c0.alts && c0.alts[rec.pick] ? c0.alts[rec.pick] : null;
  const hook = pick || c0.hook;
  const out = ['*' + String(hook.q).replace(/\*/g, '') + '*', ''];
  items.forEach((x) => {
    out.push('*' + (multi ? x.name + ' ' + gq(x.n) + ' בקצרה' : 'הדף בקצרה') + '*');
    linesOf(x.c).forEach((i) => out.push(lineOf(x.c, i)));
    if (multi) out.push('לדף המלא: leokmei.com/daf/' + x.slug + '-' + x.n);
    out.push('');
  });
  const last = items[items.length - 1], left = last.last - last.n;
  out.push('```' + (left > 0 ? 'עוד ' + left + (left === 1 ? ' דף' : ' דפים') + ' לסיום ' + last.name : 'היום מסיימים את מסכת ' + last.name) + '```');
  if (!multi) out.push('לדף המלא: leokmei.com/daf/' + first.slug + '-' + first.n);
  out.push(joinLine(invite));
  return out.join(NL);
}
/** צורת הכיתוב לנוסח שנכתב או נערך בצורה הקודמת (טקסט עם קישור חשוף בסוף): משנה צורה בלבד, לא מילה מן התוכן.
 *  קישור חשוף לדף - "לדף המלא: <קישור>"; כותרת "...בקצרה" - מודגשת; ושורת ההצטרפות בסוף, אם חסרה. פעולה שאינה משנה דבר בפעם השנייה. */
export function toCaption(text, invite) {
  const rows = String(text || '').split(String.fromCharCode(13)).join('').split(NL).map((x) => {
    const t = x.trim();
    const m = t.match(/^(?:https?:\/\/)?(leokmei\.com\/daf\/[a-z-]+-\d+)$/);
    if (m) return 'לדף המלא: ' + m[1];
    if (/^[^*`◂].*בקצרה$/.test(t)) return '*' + t + '*';
    return x;
  });
  while (rows.length && !rows[rows.length - 1].trim()) rows.pop();
  if (!/chat\.whatsapp\.com\//.test(rows.join(NL))) rows.push(joinLine(invite));
  return rows.join(NL);
}
