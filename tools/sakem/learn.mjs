/* המקליט של סכם (פרומפט 28, 9.11.2026). כל עריכה של המנהל ב-data/edits נשמרת כאן לפני שהיא נמחקת
   (הקליטה הלילית לוורד מרוקנת את הקובץ), ממוינת, ונספרת - כדי שסכם ילמד ממנה בפעם הבאה.

   node tools/sakem/learn.mjs record [--backfill]   קליטה: data/edits הנוכחי (ועם --backfill - כל היסטוריית גיט מ-28.10.2026)
                                                    אל data/sakem/learn/<מסכת>.jsonl; רשומה שכבר נקלטה אינה נכפלת.
   node tools/sakem/learn.mjs patterns [--json]     הדפוסים החוזרים (צורה / החלפת מילה / תוכן מקומי) וקבלה אוטומטית לרשימת הכללים.
   node tools/sakem/learn.mjs reclass [--dry]       (פרומפט 32) תיקון "אחרי סכם" / "של סכם" ברשומות שכבר נקלטו - ראה sakemRel.

   מיון כל עריכה:
     צורה    - הטקסט הנקי זהה ורק הסימון השתנה (הדגשה, אמורא, כותרת, סגנון), או שינוי מבנה (פיצול, איחוד, כותרת צד),
               או שינוי בפיסוק ובגרשיים בלבד.
     החלפה   - עד שלוש מילים הוחלפו במילים אחרות (זוגות "היה -> נעשה").
     תוכן    - כל השאר: תיקון מקומי שאינו כלל.
   משקל: עריכה ביחידה שעברה סכם, אחרי שהצעות סכם נכתבו, שוקלת כפול (זו הערה על סכם עצמו).
   עריכה שהיא בדיוק הצעת סכם שהתקבלה אינה נלמדת (היא כבר שלו) ומסומנת src:'סכם'.

   קבלה אוטומטית לכללים (data/sakem/learn/rules.json): החלפה שחזרה פעמיים ומעלה (במשקל), או דפוס צורה שחזר
   פעמיים אחרי סכם. כלל צורה לעולם אינו משנה מילים. כלל שהמנהל ביטל ("בטל כלל" בדף) נשאר כבוי. */
import fs from 'fs';
import path from 'path';
import { execFileSync } from 'child_process';
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const SKC = require('../sakem_core.js');

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1')), '..', '..');
const ED = path.join(ROOT, 'data', 'edits'), LD = path.join(ROOT, 'data', 'sakem', 'learn'), OUT = path.join(ROOT, 'data', 'sakem', 'out');
const DEC = path.join(ROOT, 'data', 'sakem', 'decisions');
const RULES = path.join(LD, 'rules.json');
const SINCE = '2026-10-28';
const [cmd, ...args] = process.argv.slice(2);
const has = (f) => args.includes(f);
fs.mkdirSync(LD, { recursive: true });

/* ---- סכם: אילו יחידות עברו סכם, מתי, ומה הוצע להן ---- */
function sakemUnits() {
  const M = {};  /* slug -> [{lo, hi, ids:Set, t, lines:Set}] */
  if (!fs.existsSync(OUT)) return M;
  for (const f of fs.readdirSync(OUT)) {
    if (!f.endsWith('.json') || f.endsWith('.old.json')) continue;
    let o; try { o = JSON.parse(fs.readFileSync(path.join(OUT, f), 'utf8')); } catch (e) { continue; }
    const slug = o.slug || f.replace(/-(p\d+|s\d+.*)\.json$/, '');
    /* פרומפט 32: זמני הקבלה של כל קטע (מן ההכרעות) - עריכה שנרשמה ברגע הקבלה היא ההחלה של סכם עצמו, לא תיקון */
    const acc = {};
    try { const d = JSON.parse(fs.readFileSync(path.join(DEC, f), 'utf8')); (d.log || []).forEach((x) => { if (x.act === 'accept' || x.act === 'edit') (acc[x.iid] = acc[x.iid] || []).push(+x.t || 0); }); } catch (e) { /* לא נסקר */ }
    let daf = '';
    for (const it of o.items || []) {
      const ids = (it.ids || []).map(Number).filter(Boolean);
      /* הדפים של הקטע - לשינויי מבנה, שאין להם מזהה יחידה */
      const dafs = new Set(daf ? [daf] : []);
      for (const m of String(it.orig || '').matchAll(/\[דף:([^\]]+)\]/g)) { daf = m[1].trim(); dafs.add(daf); }
      if (!ids.length) continue;
      const lines = new Set(String(it.text || '').split('\n').map((l) => plain(l)).filter((l) => l.length > 3));
      (M[slug] = M[slug] || []).push({ lo: Math.min(...ids), hi: Math.max(...ids), t: +o.t || 0, lines, dafs, acc: acc[it.iid] || [] });
    }
  }
  return M;
}
function plain(s) {
  return SKC.plainI(String(s || '').replace(/^\[[^\]]*\]$/, '').replace(/^\([^)]*\)\s*/, '')).replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim();
}
const unitOf = (k) => +((/^u(\d+)/.exec(k || '') || [])[1] || 0);

/* ---- מיון ---- */
const letters = (s) => String(s || '').replace(/["'״׳]/g, '').replace(/[^א-ת\s]/g, ' ').replace(/\s+/g, ' ').trim();
function wordDiff(a, b) {
  const A = a.split(' ').filter(Boolean), B = b.split(' ').filter(Boolean);
  const n = A.length, m = B.length;
  if (n * m > 40000) return null;
  const L = Array.from({ length: n + 1 }, () => new Int16Array(m + 1));
  for (let i = n - 1; i >= 0; i--) for (let j = m - 1; j >= 0; j--) L[i][j] = A[i] === B[j] ? L[i + 1][j + 1] + 1 : Math.max(L[i + 1][j], L[i][j + 1]);
  const runs = []; let i = 0, j = 0, cur = null;
  const flush = () => { if (cur) { runs.push(cur); cur = null; } };
  while (i < n || j < m) {
    if (i < n && j < m && A[i] === B[j]) { flush(); i++; j++; continue; }
    cur = cur || { was: [], now: [] };
    if (j < m && (i >= n || L[i][j + 1] >= L[i + 1][j])) cur.now.push(B[j++]); else cur.was.push(A[i++]);
  }
  flush();
  return runs.map((r) => ({ was: r.was.join(' '), now: r.now.join(' ') }));
}
function classify(e) {
  if (e.op === 'struct') return { cls: 'צורה', sub: 'מבנה:' + (e.kind || '?') };
  const was = String(e.was || ''), now = String(e.now || '');
  if (was === now) return { cls: 'צורה', sub: (e.wasH || '') !== (e.nowH || '') ? 'סימון' : (e.psw || e.ps ? 'סגנון' : 'סימון') };
  if (letters(was) === letters(now)) return { cls: 'צורה', sub: 'פיסוק' };
  const runs = wordDiff(letters(was), letters(now));
  if (runs && runs.length && runs.length <= 3 && runs.every((r) => r.was && r.now && r.was.split(' ').length <= 3 && r.now.split(' ').length <= 3))
    return { cls: 'החלפה', sub: '', pairs: runs };
  return { cls: 'תוכן', sub: '' };
}

/* האם העריכה אחרי סכם, והאם היא ההחלה של סכם עצמו (פרומפט 32, 12.11.2026):
   א. שינוי מבנה (פיצול, כותרת צד, מחיקת עיטור) אין לו מזהה יחידה - משויך לקטע לפי הדף. בלי זה אף כותרת צד
      שהמנהל הוסיף אחרי סכם לא נספרה כ"אחרי סכם", ולא הוצגה בשלב הלקחים.
   ב. עריכה שנרשמה עד 3 שניות מקבלת קטע (באותה מסכת) - זו החלת ההצעה בלחיצת "קבל", ולא תיקון של המנהל.
      בשבת פרק ד נספרו כך כמאה עריכות של קבלה כאילו הן תיקוני המנהל. */
function sakemRel(SU, slug, e) {
  const u = unitOf(e.k), struct = e.op === 'struct';
  const segs = (SU[slug] || []).filter((s) => (u && u >= s.lo && u <= s.hi) || (!u && struct && e.daf && s.dafs.has(e.daf)));
  const post = segs.some((s) => +e.t > s.t);
  /* בכל קטעי המסכת: קבלה מחילה גם על יחידות סמוכות שאינן ברשימת המזהים של הפריט (שבת מז., u2752 בקבלת s1) */
  const accept = (SU[slug] || []).some((s) => s.acc.some((a) => +e.t >= a - 3000 && +e.t <= a + 3000));
  const fromSakem = accept || (!struct && segs.some((s) => s.lines.has(plain(e.now))));
  return { post, fromSakem };
}

/* ---- קליטה ---- */
function loadSeen(slug) {
  const f = path.join(LD, slug + '.jsonl'), S = new Set();
  if (fs.existsSync(f)) for (const l of fs.readFileSync(f, 'utf8').split('\n')) { if (!l) continue; try { const r = JSON.parse(l); S.add(r.k + '@' + r.t); } catch (e) { /* שורה פגומה - מדולגת */ } }
  return S;
}
function record() {
  const SU = sakemUnits(), seen = {}, add = {};
  const take = (slug, doc, from) => {
    const E = Array.isArray(doc) ? doc : (doc && doc.edits) || [];
    seen[slug] = seen[slug] || loadSeen(slug);
    for (const e of E) {
      if (!e || !e.k || !e.t) continue;
      const key = e.k + '@' + e.t;
      if (seen[slug].has(key)) continue;
      seen[slug].add(key);
      const { post, fromSakem } = sakemRel(SU, slug, e);
      const c = classify(e);
      const r = { k: e.k, t: +e.t, daf: e.daf || '', cls: c.cls, sub: c.sub, w: post && !fromSakem ? 2 : 1, post: post ? 1 : 0, from };
      if (fromSakem) r.src = 'סכם';
      if (e.by) r.by = e.by;
      if (e.op === 'struct') { r.op = 'struct'; r.kind = e.kind || ''; r.texts = clip(e.texts); r.resT = clip(e.resT); if (e.psw) r.psw = e.psw; }
      else { r.was = String(e.was || '').slice(0, 400); r.now = String(e.now || '').slice(0, 400); if ((e.wasH || '') !== (e.nowH || '')) { r.wasH = String(e.wasH || '').slice(0, 600); r.nowH = String(e.nowH || '').slice(0, 600); } }
      if (c.pairs) r.pairs = c.pairs;
      (add[slug] = add[slug] || []).push(r);
    }
  };
  for (const f of fs.readdirSync(ED)) {
    if (!f.endsWith('.json')) continue;
    try { take(f.replace(/\.json$/, ''), JSON.parse(fs.readFileSync(path.join(ED, f), 'utf8')), 'now'); } catch (e) { console.error('עצירה: קובץ עריכות פגום', f, e.message); process.exit(1); }
  }
  /* --since-last (9.11.2026): גם כל קומיט של data/edits מאז ההקלטה הקודמת - כדי שעריכה שנקלטה לוורד ונמחקה
     מן הקובץ בין שתי הרצות לא תאבד. נקודת ההתחלה נשמרת ב-data/sakem/learn/state.json */
  const stF = path.join(LD, 'state.json');
  let st = {}; try { st = JSON.parse(fs.readFileSync(stF, 'utf8')); } catch (e) { /* ראשונה */ }
  const head = (() => { try { return execFileSync('git', ['rev-parse', 'HEAD'], { cwd: ROOT, encoding: 'utf8' }).trim(); } catch (e) { return ''; } })();
  let range = null;
  if (has('--since-last') && st.commit) {
    try { execFileSync('git', ['cat-file', '-e', st.commit + '^{commit}'], { cwd: ROOT, stdio: 'ignore' }); range = st.commit + '..HEAD'; }
    catch (e) { console.error('עצירה: נקודת ההקלטה הקודמת', st.commit, 'אינה בהיסטוריה שנמשכה (fetch-depth קצר?) - לא ממשיכים בשקט'); process.exit(1); }
  }
  if (has('--backfill') || range) {
    const log = execFileSync('git', range ? ['log', range, '--format=@%H', '--name-only', '--', 'data/edits/'] : ['log', '--since=' + SINCE, '--format=@%H', '--name-only', '--', 'data/edits/'], { cwd: ROOT, encoding: 'utf8', maxBuffer: 64e6 });
    let h = '', n = 0;
    for (const l of log.split('\n')) {
      if (l.startsWith('@')) { h = l.slice(1); n++; continue; }
      if (!/^data\/edits\/[a-z-]+\.json$/.test(l)) continue;
      for (const ref of [h, h + '^']) {
        let txt; try { txt = execFileSync('git', ['show', ref + ':' + l], { cwd: ROOT, encoding: 'utf8', maxBuffer: 64e6, stdio: ['ignore', 'pipe', 'ignore'] }); } catch (e) { continue; }
        try { take(path.basename(l, '.json'), JSON.parse(txt), 'git'); } catch (e) { /* גרסה פגומה בהיסטוריה - מדולגת */ }
      }
    }
    console.log('היסטוריה: עברו', n, 'קומיטים ' + (range ? 'מאז ההקלטה הקודמת' : 'מ-' + SINCE));
  }
  if (head) { st.commit = head; st.t = Date.now(); fs.writeFileSync(stF, JSON.stringify(st, null, 1)); }
  let tot = 0;
  for (const slug in add) {
    add[slug].sort((a, b) => a.t - b.t);
    fs.appendFileSync(path.join(LD, slug + '.jsonl'), add[slug].map((r) => JSON.stringify(r)).join('\n') + '\n');
    const C = {}; add[slug].forEach((r) => { C[r.cls] = (C[r.cls] || 0) + 1; });
    console.log(slug + ':', add[slug].length, 'עריכות חדשות', JSON.stringify(C));
    tot += add[slug].length;
  }
  console.log('נקלטו:', tot);
}

/* המילים כפי שנכתבו (עם גרשיים), לפי צורתן באותיות בלבד */
function origWords(src, target) {
  const T = String(src || '').split(/\s+/).filter(Boolean), k = target.split(' ').length;
  for (let i = 0; i + k <= T.length; i++) { const w = T.slice(i, i + k).join(' '); if (letters(w) === target) return w.replace(/^[^א-ת]+|[^א-ת"'׳״]+$/g, ''); }
  return target;
}

/* ---- דפוסים וקבלה אוטומטית ---- */
function readAll() {
  const R = [];
  for (const f of fs.readdirSync(LD)) if (f.endsWith('.jsonl')) for (const l of fs.readFileSync(path.join(LD, f), 'utf8').split('\n')) { if (!l) continue; try { const r = JSON.parse(l); r.slug = f.replace(/\.jsonl$/, ''); R.push(r); } catch (e) { /* */ } }
  return R;
}
export function loadRules() { try { return JSON.parse(fs.readFileSync(RULES, 'utf8')); } catch (e) { return { rules: [] }; } }
export function saveRules(R) { fs.writeFileSync(RULES, JSON.stringify(R, null, 1)); }
function patterns() {
  const R = readAll().filter((r) => r.src !== 'סכם');
  const cnt = { צורה: 0, החלפה: 0, תוכן: 0 }, sub = {}, pairs = {};
  for (const r of R) {
    cnt[r.cls] = (cnt[r.cls] || 0) + 1;
    if (r.cls === 'צורה') { const k = r.sub; sub[k] = sub[k] || { n: 0, w: 0, post: 0, ex: null }; sub[k].n++; sub[k].w += r.w; sub[k].post += r.post; if (!sub[k].ex && r.was) sub[k].ex = r; }
    for (const p of r.pairs || []) {
      const k = p.was + ' -> ' + p.now;
      /* אותה עריכה נשמרת שוב ושוב (בכל קומיט, ובמזהה יחידה חדש אחרי בנייה) - סופרים משפטים שונים, לא רשומות */
      const ctx = r.slug + '|' + letters(r.was).replace(p.was, '').slice(0, 60);
      pairs[k] = pairs[k] || { was: p.was, now: p.now, n: 0, w: 0, units: new Set(), post: 0, ex: r };
      if (pairs[k].units.has(ctx)) continue;
      pairs[k].n++; pairs[k].w += r.w; pairs[k].post += r.post; pairs[k].units.add(ctx);
    }
  }
  /* זוג חוזר = לפחות שתי יחידות שונות, או משקל 2 ומעלה ביחידה שעברה סכם */
  const rep = Object.values(pairs).filter((p) => p.units.size >= 2).sort((a, b) => b.w - a.w);
  const RL = loadRules(), have = new Set(RL.rules.map((x) => x.id));
  const now = Date.now(), added = [];
  const outs = {}; rep.forEach((p) => { (outs[p.was] = outs[p.was] || new Set()).add(p.now); });
  for (const p of rep) {
    /* מילה שמוחלפת פעם כך ופעם אחרת (ר"א = רב אשי / ר' אלעזר) - תלוית הקשר, אינה כלל; וכן קיצור בן שתי אותיות */
    if (outs[p.was].size > 1 || p.was.replace(/ /g, '').length <= 2 || p.now.replace(/ /g, '').length <= 1) continue;
    /* קבלה אוטומטית: שלושה משפטים שונים ומעלה, או שניים כשאחד מהם אחרי סכם (משקל כפול) */
    if (!(p.units.size >= 3 || (p.units.size >= 2 && p.post))) continue;
    const id = 'pair:' + p.was + '>' + p.now;
    if (have.has(id)) { const x = RL.rules.find((y) => y.id === id); x.n = p.w; continue; }
    const ow = origWords(p.ex.was, p.was), on = origWords(p.ex.now, p.now);
    const r = { id, t: now, kind: 'החלפת מילה', target: 'לקחים', n: p.w, src: 'עריכות המנהל',
      text: 'בעל הפרויקט מחליף "' + ow + '" ב"' + on + '" (' + p.units.size + ' מקומות). בניסוח חדש - כך; בנוסח המקור אין לשנות מעצמך.',
      was: SKC.plainI(p.ex.was || ''), now: SKC.plainI(p.ex.now || '') };
    RL.rules.push(r); added.push(r);
  }
  if (added.length && !has('--dry')) saveRules(RL);
  const out = { t: now, total: R.length, cnt, sub, repeated: rep.slice(0, 60).map((p) => ({ was: p.was, now: p.now, n: p.n, w: p.w, units: p.units.size, ex: { k: p.ex.k, slug: p.ex.slug, was: p.ex.was, now: p.ex.now } })), added: added.map((r) => r.id) };
  if (!has('--dry')) fs.writeFileSync(path.join(LD, 'patterns.json'), JSON.stringify(out, null, 1));
  if (has('--json')) { console.log(JSON.stringify(out)); return; }
  console.log('עריכות שנלמדו:', R.length, JSON.stringify(cnt));
  console.log('צורה:', Object.entries(sub).sort((a, b) => b[1].w - a[1].w).map(([k, v]) => k + ' ' + v.n + (v.post ? ' (אחרי סכם ' + v.post + ')' : '')).join(' · '));
  console.log('החלפות חוזרות:', rep.length); rep.slice(0, 25).forEach((p) => console.log('  ' + p.was + ' -> ' + p.now + '   ×' + p.n + ' ביחידות ' + p.units.size));
  console.log('כללים חדשים שנקלטו אוטומטית:', added.length);
}

/* ---- תיקון סיווג ברשומות קיימות (פרומפט 32): post / src / w לפי sakemRel, ופרטי מבנה מן data/edits אם יש ---- */
function clip(a) { return (a || []).map((x) => String(x || '').slice(0, 200)); }
function reclass() {
  const SU = sakemUnits();
  let ch = 0;
  for (const f of fs.readdirSync(LD).filter((x) => x.endsWith('.jsonl'))) {
    const slug = f.replace(/\.jsonl$/, ''), F = path.join(LD, f), src = {};
    try { for (const e of (JSON.parse(fs.readFileSync(path.join(ED, slug + '.json'), 'utf8')).edits || [])) if (e.op === 'struct') src[e.k + '@' + e.t] = e; } catch (e) { /* אין קובץ */ }
    const out = fs.readFileSync(F, 'utf8').split('\n').map((l) => {
      if (!l) return l;
      let r; try { r = JSON.parse(l); } catch (e) { return l; }
      const { post, fromSakem } = sakemRel(SU, slug, r);
      const was = JSON.stringify([r.post, r.src, r.w, r.texts]);
      /* רק מוסיפים מידע: קובצי ההצעות נכתבים מחדש בסבבים מאוחרים, ולכן סיווג קודם של "אחרי סכם" / "של סכם" אינו מבוטל */
      if (post) r.post = 1;
      if (fromSakem) r.src = 'סכם';
      r.w = r.post && r.src !== 'סכם' ? 2 : 1;
      const s = r.op === 'struct' && !r.texts && src[r.k + '@' + r.t];
      if (s) { r.texts = clip(s.texts); r.resT = clip(s.resT); }
      if (JSON.stringify([r.post, r.src, r.w, r.texts]) !== was) ch++;
      return JSON.stringify(r);
    });
    if (!has('--dry')) fs.writeFileSync(F, out.join('\n'));
  }
  console.log('רשומות שסיווגן תוקן:', ch);
}

const MAIN = /learn\.mjs$/.test(process.argv[1] || '');
if (!MAIN) { /* יובא כספרייה */ }
else if (cmd === 'record') record();
else if (cmd === 'patterns') patterns();
else if (cmd === 'reclass') reclass();
else if (cmd) { console.error('פקודה לא מוכרת:', cmd); process.exit(1); }
