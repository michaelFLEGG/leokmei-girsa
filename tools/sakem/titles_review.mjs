/* הצעות הכותרות לסקירה שבדף המסכת (השלמת פרומפט 22, 8.11.2026).
   הרצה: node tools/sakem/titles_review.mjs <תיקיית קובצי הנתונים, *.data.js של הבנייה המלאה>
   קורא את data/sakem/titles-scan/<מסכת>.json (פלט scan_titles.mjs על אותם קבצים) וכותב
   data/sakem/titles-review/<מסכת>.json: ממצאי סקירה מסוג "כותרת צד ארוכה / כפילות" (typ k), לפי פרק.
   כל ממצא מעוגן ביחידה שבה הכותרת יושבת בפועל (לא במספר פסקה), ונושא פעולה מוכנה:
     ארוכה:  {multi:[{heading:{text,above:1}}, {anchor:{text:<צד קצרה>}} | {anchor:{clear:1}}]}
     כפילות: {rep:{x:<הפתח הכפול>, y:''}}
     ידני:   {ask:...}  - מוצג להכרעה בלי הצעה מוכנה.
   אינו נוגע בוורד ובנתונים. ההכנסה לשרת נעשית בדף, במפתח המנהל (ראו docs/מצב-העבודה.md). */
import fs from 'fs';
import path from 'path';
import crypto from 'crypto';
import { fileURLToPath } from 'url';

const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const SCAN = path.join(ROOT, 'data', 'sakem', 'titles-scan');
const OUT = path.join(ROOT, 'data', 'sakem', 'titles-review');
const dir = process.argv[2];
if (!dir) { console.error('עצירה: חסרה תיקיית קובצי הנתונים'); process.exit(2); }
fs.mkdirSync(OUT, { recursive: true });

const ENT = { '&quot;': '"', '&#x27;': "'", '&#39;': "'", '&amp;': '&', '&lt;': '<', '&gt;': '>', '&nbsp;': ' ' };
const plain = (h) => String(h || '').replace(/<br\s*\/?>/g, ' ').replace(/<[^>]+>/g, '').replace(/&(quot|#x27|#39|amp|lt|gt|nbsp);/g, (m) => ENT[m]).replace(/ /g, ' ');
/* השוואה: בלי ניקוד, בלי רווחים, וגרש כפול ('' / ") כגרשיים */
const cmp = (t) => String(t || '').replace(/[֑-ׇ]/g, '').replace(/''/g, '"').replace(/[״]/g, '"').replace(/[׳’]/g, "'").replace(/[\s​-‏]/g, '');
const hid = (s) => crypto.createHash('sha1').update(s).digest('hex').slice(0, 12);
const words = (t) => plain(t).replace(/[֑-ׇ]/g, '').trim().split(/\s+/).filter(Boolean).length;

const order = ['bekhorot', 'berakhot', 'sukkah', 'ketubot', 'shabbat'];
const scans = fs.readdirSync(SCAN).filter((f) => f.endsWith('.json')).map((f) => f.slice(0, -5))
  .sort((a, b) => ((order.indexOf(a) + 1) || 99) - ((order.indexOf(b) + 1) || 99) || a.localeCompare(b));
const total = [];
for (const slug of scans) {
  const fp = path.join(dir, slug + '.data.js');
  if (!fs.existsSync(fp)) { console.error('עצירה: אין קובץ נתונים ל-' + slug); process.exit(3); }
  const D = JSON.parse(fs.readFileSync(fp, 'utf8').replace(/^const DATA=/, '').replace(/,SLUG="[^"]*"(?:,[A-Z_]+=[^;]*)?;\s*$/, ''));
  const scan = JSON.parse(fs.readFileSync(path.join(SCAN, slug + '.json'), 'utf8'));
  /* מספר הפרק לפי סדר הופעתו */
  const pn = [], perekOf = {};
  D.pages.forEach((p) => { if (pn.indexOf(p.perek) < 0) pn.push(p.perek); perekOf[p.daf] = pn.indexOf(p.perek) + 1; });
  const pagesOf = (daf) => D.pages.map((p, pi) => [p, pi]).filter(([p]) => p.daf === daf);
  const used = new Set();
  /* היחידה שלפני כל יחידה (לכותרת נושא מעל): כותרת קיימת / פסקת גמרא / אחר (משנה, הדרן) */
  const seqU = []; D.pages.forEach((p) => p.units.forEach((u) => seqU.push(u)));
  const posU = new Map(seqU.map((u, i) => [u.id, i]));
  const above = (u) => { const pv = seqU[posU.get(u.id) - 1];
    if (!pv) return { k: 'none' };
    if (pv.k === 'nose' || pv.k === 'dh') return { k: 'head', t: plain(pv.a) };
    if (pv.k !== 'u' || !pv.l || !pv.l.length) return { k: 'other' };
    const r = pv.l[pv.l.length - 1]; return /(^|\s)nose(\s|$)/.test(r[0] || '') ? { k: 'head', t: plain(r[1]) } : { k: 'ok' }; };
  const findings = {}; const miss = [];
  const add = (perek, f) => { (findings[perek] = findings[perek] || []).push(f); };
  for (const it of scan.items) {
    const pages = pagesOf(it.daf);
    if (!pages.length) { miss.push([it.kind, it.daf, it.title, 'דף']); continue; }
    const perek = perekOf[it.daf];
    const base = { kind: 'כותרת צד ארוכה / כפילות', layer: 'קוד', typ: 'k', daf: it.daf, perek };
    if (it.kind === 'long') {
      const want = cmp(it.title);
      let hit = null;
      for (const [p] of pages) for (const u of p.units) {
        if (hit || !u.a || u.id == null) continue;
        const key = slug + '|' + u.id;
        if (!used.has(key) && cmp(plain(u.a)).indexOf(want) > -1) { hit = u; used.add(key); }
      }
      if (!hit) { miss.push([it.kind, it.daf, it.title, 'יחידה']); continue; }
      const f = Object.assign({}, base, {
        det: 'side_long', sev: 'בינוני', i: hit.id, u: hit.id, mark: it.title, context: it.title, text: it.title,
        id: hid('tt|' + slug + '|long|' + it.daf + '|' + hit.id + '|' + it.title),
        note: 'כותרת צד של ' + words(it.title) + ' מילים. הכרעת בעל הפרויקט (8.11.2026): כותרת צד היא עוגן קצר בלבד (דובר, מילת מהלך, מספור), עד שתי מילים ושלוש בחריג; הנושא עובר לכותרת נושא.' });
      if (it.manual) {
        f.fix = ''; f.op = { ask: 'אין פיצול ברור לכותרת נושא + כותרת צד: להכריע ידנית (E לעריכה)' };
      } else {
        const ab = above(hit);
        if (ab.k === 'other' || ab.k === 'none') {
          /* מעל היחידה משנה או הדרן: אין מקום לכותרת נושא בלי עריכה */
          f.fix = 'הצעה: כותרת נושא: ' + it.heading + (it.side ? ' | כותרת צד: ' + it.side : '');
          f.op = { ask: 'מעל היחידה אין פסקת גמרא (משנה או הדרן): להכריע ידנית (E לעריכה)' };
        } else if (ab.k === 'head') {
          /* כבר יושבת כותרת נושא מיד מעל: רק כותרת הצד מתקצרת; בלי עוגן קצר - להכרעה, כדי שלא יאבד תוכן */
          f.note += ' מעל היחידה כבר כותרת נושא: «' + ab.t.trim() + '».';
          if (it.side) { f.fix = 'כותרת צד: ' + it.side + ' (המשך הכותרת, «' + it.heading + '», יוצא ממנה)'; f.op = { anchor: { text: it.side } }; }
          else { f.fix = ''; f.op = { ask: 'כבר יש כותרת נושא מעל, ולכותרת הצד אין עוגן קצר: להכריע ידנית (E לעריכה)' }; }
        } else {
          f.fix = 'כותרת נושא: ' + it.heading + (it.side ? ' | כותרת צד: ' + it.side : ' | כותרת הצד נמחקת');
          f.op = { multi: [{ heading: { text: it.heading, above: 1 } }, it.side ? { anchor: { text: it.side } } : { anchor: { clear: 1 } }] };
        }
      }
      add(perek, f);
    } else {
      /* כפילות: השורה שאחרי הכותרת, לפי פתחה */
      const lc = cmp(it.line), head = lc.slice(0, Math.min(lc.length, 30));
      let hit = null;
      for (const [p] of pages) for (const u of p.units) {
        if (hit || u.id == null || !u.l) continue;
        u.l.forEach((r, i) => { if (!hit && cmp(plain(r[1])).startsWith(head)) hit = { u, i, t: plain(r[1]) }; });
      }
      if (!hit) { miss.push([it.kind, it.daf, it.title, 'שורה']); continue; }
      const t = hit.t.replace(/\s+/g, ' ').trim();
      const f = Object.assign({}, base, {
        det: 'title_dup', sev: 'קל', i: hit.u.id, u: hit.u.id, text: t, context: t.slice(0, 60),
        id: hid('tt|' + slug + '|dup|' + it.daf + '|' + hit.u.id + '|' + it.title + '|' + it.line),
        note: 'הכותרת "' + it.title + '" חוזרת בפתח השורה שאחריה. הכרעת בעל הפרויקט (8.11.2026): מה שכתוב בכותרת אינו נכפל בשורה, והשורה מתחילה ישר בחידוש.' });
      if (it.manual || !it.fixed) {
        f.mark = ''; f.fix = ''; f.op = { ask: 'הכפילות אינה נפתרת במחיקה פשוטה: להכריע ידנית (E לעריכה)' };
      } else {
        /* הפתח הכפול: מה שבין תחילת השורה לנוסח המתוקן (סיומת משותפת) */
        const a = String(it.line), b = String(it.fixed);
        let k = 0; while (k < a.length && k < b.length && a[a.length - 1 - k] === b[b.length - 1 - k]) k++;
        const x = a.slice(0, a.length - k), y = b.slice(0, b.length - k);
        if (!x.trim() || y.trim()) { f.mark = ''; f.fix = ''; f.op = { ask: 'הכפילות אינה נפתרת במחיקה פשוטה: להכריע ידנית (E לעריכה)' }; }
        else { f.mark = x.trim(); f.fix = x.trim() + ' ⟵ (נמחק)'; f.op = { rep: { x: x.replace(/^\s+/, ''), y: '' } }; } /* עם הרווח שאחריו, שהשורה לא תיפתח ברווח */
      }
      add(perek, f);
    }
  }
  const n = Object.values(findings).reduce((s, a) => s + a.length, 0);
  const ready = Object.values(findings).reduce((s, a) => s + a.filter((f) => !f.op.ask).length, 0);
  fs.writeFileSync(path.join(OUT, slug + '.json'), JSON.stringify({ slug, generated: '2026-11-08', perakim: pn, n, ready, miss, findings }, null, 1));
  total.push([slug, n, ready, miss.length]);
  console.log(slug, 'ממצאים', n, 'מוכנים', ready, 'להכרעה', n - ready, 'לא אותרו', miss.length);
}
console.log('סה"כ', total.reduce((s, r) => s + r[1], 0), 'מוכנים', total.reduce((s, r) => s + r[2], 0), 'לא אותרו', total.reduce((s, r) => s + r[3], 0));
