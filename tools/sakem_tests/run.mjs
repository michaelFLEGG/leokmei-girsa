/* המבחן החוזר של "סכם" (פרומפט 7, 26.10.2026).
   הרצה: node tools/sakem_tests/run.mjs [--label שם] [--only 2,3]
   שולח את ארבעת קטעי המבחן (tests.json) לנקודת הקליטה, POST /sakem/test - אותה הנחיה, אותן
   דוגמאות ואותו שומר כמו הכפתור עצמו, על המפתח של "לאוקמי - סכם" (סנטים בודדים לסבב) -
   ובודק בקוד את התכונות הנדרשות מכל פלט. לא נוסח מדויק: מספור שלם, בלי ואב"א, פסוקים
   אות-באות, שמות שלא איבדו סגנון, ותכונה מיוחדת לכל מבחן.
   מפתח המנהל: LEOKMEI_ADMIN_KEY, או קובץ המפתח המקומי (כמו הקליטה הלילית).
   התוצאות נכתבות ל-tools/sakem_tests/results/. קוד יציאה 1 אם מבחן נכשל.
   להריץ אחרי כל שינוי בהנחיה, בדוגמאות או בשומר. */
import fs from 'fs';
import path from 'path';
import { createRequire } from 'module';
import { fileURLToPath } from 'url';

const require = createRequire(import.meta.url);
const DIR = path.dirname(fileURLToPath(import.meta.url));
const SKC = require('../sakem_core.js');
const API = process.env.LEOKMEI_API || 'https://leokmei-suggest.m7654301.workers.dev';
const KEY_FILE = 'C:\\Users\\Owner\\Documents\\לאוקמי-מפתח-מנהל.txt';

function adminKey() {
  if (process.env.LEOKMEI_ADMIN_KEY) return process.env.LEOKMEI_ADMIN_KEY.trim();
  const lines = fs.readFileSync(KEY_FILE, 'utf8').replace(/^\uFEFF/, '').split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
  for (const l of lines.reverse()) if (/^[\x20-\x7e]{20,}$/.test(l)) return l;
  throw new Error('לא נמצא מפתח מנהל');
}

/* ---- כלי עזר על פורמט הביניים ---- */
const HV = { 'א': 1, 'ב': 2, 'ג': 3, 'ד': 4, 'ה': 5, 'ו': 6, 'ז': 7, 'ח': 8, 'ט': 9, 'י': 10 };
const NIK = /[\u0591-\u05c7]/g;
const ALT = /^(ו?אב"א|ו?איבעית אימא|ו?א"נ|ו?אי נמי)(?=[\s:,]|$)/;
const items = (t) => SKC.parse(t).filter((k) => k.t === 'line' || k.t === 'title').map((k) => ({ k: k.t, v: k.v, p: SKC.plainI(k.v).replace(/\s+/g, ' ').trim() }));
const numOf = (p) => { const m = /^([א-י])\.(?:\s|$)/.exec(p); return m ? HV[m[1]] : 0; };
const afterNum = (p) => p.replace(/^[א-י]\.\s*/, '');
function runs(t) {
  const out = [], errs = [];
  let cur = null;
  items(t).forEach((it) => {
    const n = numOf(it.p);
    if (!n) return;
    if (n === 1) { cur = [1]; out.push(cur); return; }
    if (cur && n === cur[cur.length - 1] + 1) { cur.push(n); return; }
    errs.push('מספור לא רציף: ' + it.p.slice(0, 20));
    cur = [n]; out.push(cur);
  });
  out.forEach((r) => { if (r.length < 2) errs.push('רשימה של פריט אחד (' + r.join(',') + ')'); });
  return { runs: out, errs };
}
function spans(s, tag) {
  const out = [], open = '{' + tag + ':';
  let i = s.indexOf(open);
  while (i > -1) {
    let d = 0, j = i;
    for (; j < s.length; j++) { if (s[j] === '{') d++; else if (s[j] === '}') { d--; if (!d) break; } }
    out.push({ a: i, b: j + 1, v: s.slice(i + open.length, j) });
    i = s.indexOf(open, j + 1);
  }
  return out;
}
const cut = (s, sp) => { let o = '', at = 0; sp.forEach((x) => { o += s.slice(at, x.a); at = x.b; }); return o + s.slice(at); };
const base = (w) => {
  w = w.replace(NIK, '').replace(/[:,.;!?()[\]]/g, '').trim();
  let k = 0;
  while (k < 2 && /^[ודלבהמשכ]/.test(w) && w.length > 3) { w = w.slice(1); k++; }
  return w;
};
const nameOk = (b) => b.length >= 3 || /["']/.test(b);
function plainNames(t) {
  const c = new Map();
  items(t).filter((x) => x.k === 'line').forEach((x) => {
    SKC.plainI(cut(x.v, spans(x.v, 'אם'))).split(/[\s\-]+/).forEach((w) => { const b = base(w); if (b) c.set(b, (c.get(b) || 0) + 1); });
  });
  return c;
}
const pnorm = (s) => String(s).normalize('NFC').replace(/['׳]/g, '').replace(/\s+/g, ' ').trim().replace(/^[\s,.:;!?\-]+|[\s,.:;!?\-]+$/g, '');

/* ---- התכונות ---- */
function common(orig, out) {
  const f = [];
  f.push(...runs(out).errs);
  if (items(orig).some((x) => ALT.test(afterNum(x.p))) && items(out).some((x) => ALT.test(afterNum(x.p)))) f.push('ואב"א / א"נ נשאר במקום מספור');
  const src = pnorm(SKC.plainI(SKC.parse(orig).map((k) => k.v || '').join(' ')));
  SKC.parse(out).forEach((k) => { if (!k.v) return; spans(k.v, 'פס').forEach((x) => { const v = pnorm(SKC.plainI(x.v)); if (v && src.indexOf(v) < 0) f.push('פסוק שונה: ' + v.slice(0, 30)); }); });
  const am = new Set();
  items(orig).forEach((x) => spans(x.v, 'אם').forEach((s) => { const b = base(SKC.plainI(s.v)); if (nameOk(b)) am.add(b); }));
  const po = plainNames(orig), pn = plainNames(out);
  am.forEach((b) => { if ((pn.get(b) || 0) > (po.get(b) || 0)) f.push('שם אמורא איבד סגנון: ' + b); });
  return f;
}
const PROPS = {
  common: (o, t) => common(o, t),
  list: (o, t, n) => (runs(t).runs.some((r) => r.length >= +n) ? [] : ['אין רשימה ממוספרת א. עד ' + Object.keys(HV)[+n - 1] + '.']),
  explain: (o, t, a) => {
    const [name, word] = a.split(':');
    const L = items(t).filter((x) => x.k === 'line' && x.p.indexOf(word) > -1 && x.p.replace(NIK, '').indexOf(name) > -1);
    const titled = items(t).some((x) => x.k === 'title' && x.p.indexOf(name) > -1);
    const lines = L.length ? L : (titled ? items(t).filter((x) => x.k === 'line' && x.p.indexOf(word) > -1).slice(-1) : []);
    if (!lines.length) return ['השורה של ' + name + ' לא נמצאה'];
    return lines.every((x) => /\{הס:/.test(x.v) || /אסור/.test(x.p)) ? [] : ['השורה של ' + name + ' סתומה, בלי הסבר: ' + lines[0].p.slice(0, 50)];
  },
  stem: (o, t, word) => {
    const it = items(t);
    const i = it.findIndex((x) => x.k === 'line' && x.p.indexOf(word) > -1);
    if (i < 0) return ['הקושיה לא נמצאה'];
    const prev = it[i - 1];
    return numOf(it[i].p) || (prev && prev.k === 'title' && numOf(prev.p)) ? ['הקושיה ממוספרת'] : [];
  },
  same: (o, t, a) => {
    const [x, y] = a.split('|');
    const form = (n) => {
      const it = items(t);
      if (it.some((z) => z.k === 'title' && afterNum(z.p).replace(NIK, '').indexOf(n) > -1)) return 'צד';
      if (it.some((z) => z.k === 'line' && spans(z.v, 'אם').some((s) => SKC.plainI(s.v).indexOf(n) > -1))) return 'שורה';
      return '?';
    };
    const fx = form(x), fy = form(y);
    return fx === fy && fx !== '?' ? [] : ['הצלעות אינן באותה צורה (' + x + ': ' + fx + ', ' + y + ': ' + fy + ')'];
  },
};

/* ---- ההרצה ---- */
const argv = process.argv.slice(2);
const opt = (k) => { const i = argv.indexOf(k); return i > -1 ? argv[i + 1] : ''; };
const label = opt('--label') || 'run';
const only = opt('--only') ? opt('--only').split(',').map(Number) : null;
const T = JSON.parse(fs.readFileSync(path.join(DIR, 'tests.json'), 'utf8')).tests.filter((x) => !only || only.includes(x.id));
const key = adminKey();
let usd = 0, failed = 0;
const res = [];
for (const t of T) {
  let j = null, err = '';
  try {
    const r = await fetch(API + '/sakem/test', {
      method: 'POST',
      headers: { 'content-type': 'application/json; charset=utf-8', 'x-admin-key': key, 'user-agent': 'Mozilla/5.0 leokmei-sakem-tests/1.0' },
      body: JSON.stringify({ slug: 'bekhorot', text: t.text }),
    });
    j = await r.json().catch(() => null);
    if (!r.ok || !j || !j.ok) err = (j && (j.error || j.err)) || ('שגיאה ' + r.status);
  } catch (e) { err = String(e.message || e); }
  let fails = [];
  if (err) fails = ['לא התקבלה הצעה: ' + err];
  else {
    usd += j.usd || 0;
    t.props.forEach((p) => { const [k, ...a] = p.split(':'); fails.push(...PROPS[k](t.text, j.text, a.join(':'))); });
  }
  if (fails.length) failed++;
  res.push({ id: t.id, name: t.name, pass: !fails.length, fails, text: j && j.text, point: j && j.point, changes: j && j.changes, warn: j && j.warn, notes: j && j.notes, usd: j && j.usd });
  console.log('\n=== מבחן ' + t.id + ' (' + t.daf + '): ' + t.name + ' - ' + (fails.length ? 'נכשל' : 'עבר'));
  if (j && j.text) console.log(j.text);
  if (j && j.point) console.log('השלד: ' + j.point);
  if (j && j.changes) console.log('מה שיניתי: ' + j.changes.join(' · '));
  if (j && j.warn && j.warn.length) console.log('שומר: ' + j.warn.join(' · '));
  if (j && j.notes && j.notes.length) console.log('אזהרות: ' + j.notes.join(' · '));
  fails.forEach((f) => console.log('  ✗ ' + f));
}
fs.mkdirSync(path.join(DIR, 'results'), { recursive: true });
const stamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
fs.writeFileSync(path.join(DIR, 'results', stamp + '-' + label + '.json'), JSON.stringify({ label, t: Date.now(), usd, failed, res }, null, 1));
console.log('\nעברו ' + (T.length - failed) + ' מתוך ' + T.length + ' · עלות $' + usd.toFixed(3));
process.exit(failed ? 1 : 0);
