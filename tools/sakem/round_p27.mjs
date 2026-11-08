/* סבב ממוקד על פרק שכבר נסקר (פרומפט 27, 8.11.2026): ארבעה דברים בלבד, בלי לגעת בנוסח.
   א. עיטור צמוד לכותרת - נמחק ([מחק-עיטור:<מזהה>]).
   ב. עיקר המשנה מודגש ({ב:...}) - מתוך לשון המשנה עצמה, לפי רשימה שנקבעה ביד לכל משנה.
   ג. כותרות צד שחסרו - עוגן קצר (דובר / מילת מהלך / מספור), לפי רשימה שנקבעה ביד.
   ד. "רווח לפני" ((רווח)) בפתיחת יחידה חדשה שאין לה כותרת - לפי רשימה שנקבעה ביד.
   הקלט: _work/p27/base.json (הנוסח הנוכחי לכל קטע: ההצעה שהתקבלה / הנוסח הערוך / המקור).
   הפלט: data/sakem/out/<jid>.json - עבודה רגילה של סכם, נסקרת באותו מסלול.
   node tools/sakem/round_p27.mjs <base.json> data/sakem/rounds/bava-batra-p5-p27-rules.json <jid> <title> <hatz-ids.json> */
import fs from 'fs';
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const SKC = require('../sakem_core.js');
const [baseF, rulesF, jid, title, hatzF] = process.argv.slice(2);
const B = JSON.parse(fs.readFileSync(baseF, 'utf8'));
const RU = JSON.parse(fs.readFileSync(rulesF, 'utf8'));
const HZ = new Set(JSON.parse(fs.readFileSync(hatzF, 'utf8')));
const plainHead = (s) => SKC.plainI(String(s).replace(/^\((נושא|דה)\)\s*/, '').replace(/^\[כותרת-(נושא|דה):/, '').replace(/\]$/, '')).trim();
const items = [], stat = [];
for (const b of B) {
  const orig = b.text; if (!orig) continue;
  let L = orig.split('\n');
  const ch = [], cnt = { hatz: 0, bold: 0, side: 0, space: 0 };
  /* א. עיטור */
  for (let i = 0; i < L.length; i++) {
    const m = /^\[קבוע:(\d+)\]$/.exec(L[i].trim());
    if (!m || !HZ.has(+m[1])) continue;
    const T = L.slice(); T[i] = '[מחק-עיטור:' + m[1] + ']';
    /* הכותרת עשויה להיות בראש הקטע הבא, כשהעיטור הוא השורה האחרונה בקטע (ולהפך) */
    const bi0 = B.indexOf(b), NX = ((B[bi0 + 1] || {}).text || '').split('\n').slice(0, 4), PV = ((B[bi0 - 1] || {}).text || '').split('\n').slice(-3);
    const W = PV.concat(T, NX), wi = PV.length + i;
    if (!SKC.hatzNearHead(W.join('\n'), +m[1])) continue;
    L = T; cnt.hatz++;
    let near = ''; for (let k = wi + 1; k < W.length; k++) { if (SKC.isHeadLine(W[k])) { near = plainHead(W[k]); break } if (!/^\[(מקור|דף|צד)/.test(W[k])) break }
    if (!near) for (let k = wi - 1; k >= 0; k--) { if (SKC.isHeadLine(W[k])) { near = plainHead(W[k]); break } if (!/^\[(מקור|דף|צד)/.test(W[k])) break }
    ch.push('נמחק עיטור לפני: ' + near);
  }
  /* ב. הדגשה במשנה */
  for (const r of (RU.bold[b.iid] || [])) {
    let inm = false, done = false;
    for (let i = 0; i < L.length && !done; i++) {
      if (/^\[משנה/.test(L[i])) { inm = true; continue }
      if (/^\[(גמרא|כותרת-דה)/.test(L[i])) { inm = false; continue }
      if (!inm || /^\[/.test(L[i])) continue;
      /* "^" בראש הכלל: רק בפתח השורה (אחרי סימן סגנון), כדי לא לתפוס "לא מכר את..." באמצע */
      const st = r[0] === '^', w = st ? r.slice(1) : r;
      const lead = (/^\(\S+\)\s*/.exec(L[i]) || [''])[0];
      const p = st ? (L[i].startsWith(w, lead.length) ? lead.length : -1) : L[i].indexOf(w);
      if (p < 0) continue;
      const before = L[i].slice(0, p);
      if (/\{ב:[^}]*$/.test(before)) { done = true; break }
      L[i] = before + '{ב:' + w + '}' + L[i].slice(p + w.length); done = true; cnt.bold++; ch.push('הודגש במשנה: ' + w);
    }
    if (!done) throw new Error(b.iid + ': לא נמצא במשנה: ' + r);
  }
  /* ג. כותרת צד: {from: תחילת השורה כפי שהיא, title: הכותרת, rest: תחילת השורה החדשה} */
  for (const r of (RU.side[b.iid] || [])) {
    const i = L.findIndex((l) => l.startsWith(r.from));
    if (i < 0) throw new Error(b.iid + ': לא נמצאה שורה לכותרת צד: ' + r.from);
    L.splice(i, 1, '[צד:' + r.title + ']', r.rest + L[i].slice(r.from.length));
    cnt.side++; ch.push('כותרת צד: ' + r.title);
  }
  /* ד. רווח לפני */
  for (const r of (RU.space[b.iid] || [])) {
    const i = L.findIndex((l) => l.startsWith(r));
    if (i < 0) throw new Error(b.iid + ': לא נמצאה שורה לרווח: ' + r);
    L[i] = '(רווח) ' + L[i]; cnt.space++; ch.push('רווח לפני: ' + SKC.plainI(r).slice(0, 40));
  }
  const text = L.join('\n');
  stat.push({ iid: b.iid, daf: (/\[דף:([^\]]+)\]/.exec(orig) || [])[1] || '', ...cnt });
  if (text === orig) continue;
  /* השומר: כמו put של המשימה, על הנוסח בלי סימני מחיקת העיטור */
  const hd = SKC.hatzDel(orig, text), NL = String.fromCharCode(10);
  /* הקשר המספור: סוף הקטע הקודם ותחילת הבא (כמו put) */
  const bi = B.indexOf(b), pv = (B[bi - 1] || {}).text || '', nx = (B[bi + 1] || {}).text || '';
  const ck = SKC.check(hd.orig, hd.text, { before: pv.split(NL).slice(-3).join(NL), after: nx.split(NL).slice(0, 3).join(NL) });
  /* מה שנכשל כבר בנוסח הקיים אינו של הסבב הזה (הסבב אינו נוגע בנוסח) */
  const ctx = { before: pv.split(NL).slice(-3).join(NL), after: nx.split(NL).slice(0, 3).join(NL) };
  const pre = new Set(SKC.check(hd.orig, hd.orig, ctx).errs);
  const errs = ck.errs.filter((e) => !/קצר מהמקור|ארוך מהמקור/.test(e) && !pre.has(e));
  if (errs.length) throw new Error(b.iid + ': השומר דחה: ' + errs.join(' · '));
  /* מספר היחידות שבקטע אחרי ההכרעות (לאיתור מחדש לפי התוכן בדף): קבוע + כותרות + יחידות טקסט */
  const toks = SKC.parse(orig);
  let n = toks.filter((k) => k.t === 'lock' && (k.kind === 'קבוע' || /^כותרת/.test(k.kind))).length;
  SKC.segments(toks).forEach((s, si) => { n += s.units.length; if (si === 0 && s.units[0] && !s.units[0].titles.length && b.lead) n--; });
  const ids = Array.from({ length: n }, (_, k) => b.ids[0] + k);
  items.push({ iid: b.iid, kind: 'seg', seg: b.seg, sugya: b.sugya, ids, orig, text, point: '', changes: ch, layers: ['ליטוש'], skipped: '', adds: [], warn: [], read: [], round: 'p27' });
}
const out = { v: 1, jid, slug: 'bava-batra', title, status: 'ready', plan: B.map((b) => ({ iid: b.iid })), total: items.length, done: items.length, items, t: Date.now(), rev: 'p27', counts: {} };
fs.writeFileSync('data/sakem/out/' + jid + '.json', JSON.stringify(out, null, 1));
fs.writeFileSync('_work/p27/round-stat.json', JSON.stringify(stat, null, 1));
const tot = stat.reduce((a, s) => { for (const k of ['hatz', 'bold', 'side', 'space']) a[k] = (a[k] || 0) + s[k]; return a }, {});
console.log('קטעים עם שינוי:', items.length, 'מתוך', B.length, JSON.stringify(tot));
