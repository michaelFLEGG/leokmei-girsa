/* בדיקת פורמט הביניים של "סכם" (26.10.2026): קטע -> ביניים -> קטע בלי שינוי חייב להחזיר HTML זהה.
   הרצה: node tools/sakem_test.js site/bekhorot.data.js [עוד קובצי data.js]
   עובר על כל יחידות המסכת, ממיר כל עמוד לביניים ובחזרה, ומשווה כל שורה וכל כותרת צד
   (אחרי נרמול ישויות, רווחים ותגיות ריקות). בודק גם שהשומר אינו נכשל על הקטע עצמו
   (מלבד "אינו קצר מהמקור"), ושאלמנט נעול שהוזז נתפס. יוצא בקוד 1 על כל כשל. */
const fs = require('fs');
const SKC = require('./sakem_core.js');
const dec = (s) => SKC.bare(s);
function canon(h) {
  return String(h || '')
    .replace(/<span class="ltab">([^<]*)<\/span>/g, '$1').replace(/<b>/g, '<i class="b">').replace(/<\/b>/g, '</i>')
    .replace(/<(i|b)( class="[a-z]+")?><\/\1>/g, '').replace(/<(i|b)( class="[a-z]+")?>(\s|&nbsp;)+<\/\1>/g, ' ')
    .replace(/(<[^>]+>)|([^<]+)/g, (m, tag, txt) => tag ? tag : dec(txt).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'))
    .replace(/\s+/g, ' ').trim();
}
let fail = 0, lines = 0, pages = 0, bad = 0;
for (const f of process.argv.slice(2)) {
  let s = fs.readFileSync(f, 'utf8').replace(/^const DATA=/, '').replace(/,SLUG="[^"]*";\s*$/, '');
  const D = JSON.parse(s);
  D.pages.forEach((p, pi) => {
    pages++;
    const units = p.units.map((u, i) => Object.assign({}, u, { daf: p.daf, first: i === 0 }));
    const r = SKC.toInter(units);
    bad += r.bad.length;
    const segs = SKC.segments(SKC.parse(r.text));
    // הסדר: כל יחידת u/m בעמוד, לפי סדר הקטעים
    const flat = [];
    segs.forEach((sg) => sg.units.forEach((u) => flat.push(u)));
    const want = units.filter((u) => (u.k === 'u' || u.k === 'm') && (u.l.length || u.a || u.w));
    // יחידה בלי כותרת שאינה ראשונה בקטע מתמזגת לקודמת בפורמט - משווים את רשימת השורות והכותרות
    const gotL = [], wantL = [], gotT = [], wantT = [];
    flat.forEach((u) => { u.titles.forEach((t) => gotT.push(canon(SKC.i2h(t)))); u.lines.forEach((l) => gotL.push([l.sty, canon(SKC.i2h(l.v))])); });
    want.forEach((u) => {
      String((u.k === 'u' ? u.a : u.w) || '').split(/<br\s*\/?>/i).forEach((x) => { if (SKC.bare(x).trim()) wantT.push(canon(x)); });
      u.l.forEach((l) => wantL.push([String(l[0]).split(' ').filter((c) => SKC.P2T[c])[0] || '', canon(l[1])]));
    });
    if (gotT.join('|') !== wantT.join('|')) { fail++; if (fail < 6) console.log('כותרות שונות', p.daf, gotT.find((x, i) => x !== wantT[i]), '<>', wantT.find((x, i) => x !== gotT[i])); }
    wantL.forEach((w, i) => {
      lines++;
      const g = gotL[i] || ['', ''];
      if (g[0] !== w[0] || g[1] !== w[1]) { fail++; if (fail < 6) console.log('שורה שונה', p.daf, JSON.stringify(w).slice(0, 160), '\n      ', JSON.stringify(g).slice(0, 160)); }
    });
    const e = SKC.guard(r.text, r.text).filter((x) => x !== 'אינו קצר מהמקור' && x !== 'מקף ארוך');
    if (e.length) { fail++; if (fail < 6) console.log('השומר נכשל על הקטע עצמו', p.daf, e); }
  });
}
// אלמנט נעול שהוזז / נמחק - נתפס
const base = '[דף:כה.]\n[צד:איתמר]\nשורה א {אם:רב}\n[מקור:25a.2]\n[צד:והך]\nשורה ב';
const moved = '[מקור:25a.2]\n[דף:כה.]\n[צד:איתמר]\nשורה {אם:רב}\nב';
const dropped = '[דף:כה.]\n[צד:איתמר]\nשורה {אם:רב}';
const t1 = SKC.guard(base, moved).some((x) => /נעולים/.test(x));
const t2 = SKC.guard(base, dropped).some((x) => /נעולים/.test(x));
const t3 = SKC.guard(base, '[דף:כה.]\n[צד:איתמר]\nשורה {אם:שמואל}\n[מקור:25a.2]\nב').some((x) => /אמורא/.test(x));
const t4 = SKC.guard(base, '[דף:כה.]\n[צד:איתמר]\nשורה — {אם:רב}\n[מקור:25a.2]\nב').some((x) => /מקף/.test(x));
if (!(t1 && t2 && t3 && t4)) { fail++; console.log('השומר לא תפס', { t1, t2, t3, t4 }); }
console.log(`עמודים ${pages}, שורות ${lines}, תגיות לא מוכרות ${bad}, כשלים ${fail}`);
process.exit(fail ? 1 : 0);
