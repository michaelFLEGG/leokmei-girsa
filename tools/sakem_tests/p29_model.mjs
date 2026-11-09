/* פרומפט 29 (9.11.2026): הבודק החדש על הדגם - בבא בתרא פרק ה כפי שאושר.
   הנוסח המאושר לכל קטע: מן ההכרעות של סבב הצורה (data/sakem/decisions/bava-batra-s3799-p27r.json):
   קבל = ההצעה, ערוך = מה שהמנהל כתב, השאר / דחה = המקור. כל קטע נבדק כ"ללא שינוי" במצב המשימה (strict).
   אסור שייפסל שם דבר: אם נפסל - מתקנים את הבודק, לא את הדגם. קוד יציאה 1 אם נפסל.
   node tools/sakem_tests/p29_model.mjs [--write]   (--write: כותב את מדדי הדגם ל-data/sakem/model-bb5.json) */
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
const require = createRequire(import.meta.url);
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const SKC = require(path.join(ROOT, 'tools', 'sakem_core.js'));
const rd = (f) => JSON.parse(fs.readFileSync(path.join(ROOT, f), 'utf8'));
export function approvedBB5() {
  const d = rd('data/sakem/decisions/bava-batra-s3799-p27r.json');
  const o = rd('data/sakem/out/bava-batra-s3799-p27r.json');
  return o.items.filter((x) => x.kind === 'seg').map((it) => {
    const L = (d.log || []).filter((x) => x.iid === it.iid && x.act !== 'undo').pop() || {};
    let t = L.act === 'accept' ? (L.prop || it.text) : L.act === 'edit' ? (L.final || it.text) : (L.orig || it.orig);
    /* העיטורים שנמחקו בקבלה: [מחק-עיטור:N] יוצאים מן הנוסח המאושר, ומן המקור שמולו נבדק (כמו hatzDel ב-put) */
    const del = [...String(t || '').matchAll(/\[מחק-עיטור:(\d+)\]/g)].map((m) => m[1]);
    t = String(t || '').split('\n').filter((l) => !/^\s*\[מחק-עיטור:\d+\]\s*$/.test(l)).join('\n');
    const orig = String(it.orig || '').split('\n').filter((l) => { const m = /^\s*\[קבוע:(\d+)\]\s*$/.exec(l); return !m || !del.includes(m[1]); }).join('\n');
    return { iid: it.iid, act: L.act || "?", ids: it.ids, text: t, orig, changes: it.changes || [] };
  });
}
const pk = rd('data/sakem/queue/bava-batra-p5.json');
export function unitCtx(pk, ids) {
  const set = new Set(ids), U = pk.units;
  const hatz = U.filter((u) => set.has(u.id) && u.k === 'hatz').map((u) => u.id);
  const heads = U.filter((u) => /^perek-(start|range)$/.test(u.k)).map((u) => u.id);
  let unitOpen = 0;
  U.forEach((u, i) => { if (!set.has(u.id) || u.k !== 'u' || String(u.a || '').replace(/<[^>]*>/g, '').trim()) return; const p = U[i - 1]; if (!p || p.k !== 'u') return;
    /* יחידה שפותחת במספור או במקף (המשך רשימה או תירוץ) - אינה פתיחה חדשה */
    const f = SKC.plainI(SKC.h2i(((u.l || [])[0] || [])[1] || '')).trim();
    if (/^-|^(?:[יכלמ]?[א-ט]|[יכלמ])\.\s/.test(f)) return;
    unitOpen++; });
  return { hatz, heads, unitOpen };
}
if (process.argv[1] && process.argv[1].endsWith('p29_model.mjs')) {
  const segs = approvedBB5();
  let bad = 0; const A = [];
  segs.forEach((s) => {
    const c = unitCtx(pk, s.ids);
    /* עיטור שנשאר בדגם אחרי הקבלה ("השאר") - נבדק כמו בכל קטע */
    const cp = SKC.comply(s.orig, s.text, { strict: true, changes: s.changes, hatz: c.hatz, heads: c.heads, unitOpen: c.unitOpen });
    const ck = SKC.check(s.orig, s.text, { edited: true });
    A.push(SKC.absStat(s.text));
    const errs = cp.errs.concat(ck.errs);
    if (errs.length) { bad++; console.log('✗ ' + s.iid + ' (' + s.act + '): ' + errs.join(' · ')); }
  });
  /* מדדי הדגם לכל קטע (ממוצע), ושינוי האורך של סבב הסכם הראשי על הפרק (out/bava-batra-p5.json: מקור מול הצעה) */
  const main = rd('data/sakem/out/bava-batra-p5.json');
  let la = 0, lb = 0; main.items.filter((x) => x.kind === 'seg' && !x.nochange).forEach((x) => { const st = SKC.comply(x.orig, x.text, {}).stat; la += st.lenA; lb += st.lenB; });
  const model = { from: 'bava-batra-p5 + bava-batra-s3799-p27r', t: Date.now(), segs: segs.length, perSeg: SKC.absAvg(A), lenPct: Math.round((lb / la - 1) * 1000) / 10 };
  console.log('הדגם: ' + JSON.stringify(model));
  if (process.argv.includes('--write')) fs.writeFileSync(path.join(ROOT, 'data/sakem/model-bb5.json'), JSON.stringify(model, null, 1) + '\n');
  console.log(bad ? bad + ' מתוך ' + segs.length + ' קטעים נפסלו' : 'הדגם עובר: אף קטע מאושר לא נפסל (' + segs.length + ')');
  process.exit(bad ? 1 : 0);
}
