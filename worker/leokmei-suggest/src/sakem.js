/* ===== סכם: הידוק ותיקון של קטע נבחר, מנהל בלבד (26.10.2026) =====
   POST /sakem          {slug, units, before, after, queue?}  הצעה חדשה (queue=1: לתור הסולמיות)
   POST /sakem/more     {slug, id}                            "קצר עוד" על הצעה קיימת
   POST /sakem/done     {slug, id, act, final}                 קבל / ערוך / בטל - ליומן הלמידה
   GET  /sakem/stat     ?slug                                  מפתח קיים?, עלות יומית וחודשית, למידה, תור
   POST /sakem/key      {key}                                  הדבקת המפתח פעם אחת (נכתב מוצפן, אינו מוחזר לעולם)
   POST /sakem/examples {act:'apply'}                          עדכון דוגמאות הסכם מזוגות הלמידה
   GET  /sakem/queue    ?slug                                  תור הסולמיות של המסכת

   הדפדפן שולח את יחידות הקטע כפי שהן בנתונים. אין כאן טקסט חופשי: כל שורה וכל כותרת חייבות
   להימצא בקובץ העמוד שבאתר (sk/<מסכת>/<דף>.json) או בעריכות המנהל שבשרת (ed:<מסכת>), אחרת
   הבקשה נדחית. לשון הגמרא ופירוש הגמרא נשלפים מקובץ העמוד, ביאור חברותא מן המחסן.

   המפתח: SAKEM_API_KEY כסוד ב-Worker, ואם אינו מוגדר - המפתח שהודבק בחלונית הניהול, שמור
   במחסן מוצפן (AES-GCM, מפתח ההצפנה נגזר מ-ADMIN_KEY ואינו במחסן). לעולם לא מפתח אחר.
   תקרה פנימית: 9 דולר לחודש (מתחת לתקרת הסביבה "לאוקמי - סכם" בקונסול, 10 דולר). */
import SKC from '../../../tools/sakem_core.js';
import EXAMPLES from '../../../data/sakem/sakem-examples.json';
import { SAKEM_SYSTEM } from './sakem_prompt.js';

const MODEL = 'claude-opus-5-5';
/* מחירון רשמי לקלוד אופוס 5.5, דולר למיליון אסימונים: קלט 4, פלט 20, כתיבה למטמון (5 דקות) 5, קריאה ממנו 0.20 */
const PRICE = { in: 4, out: 20, cw: 5, cr: 0.2 };
const CAP_USD = 9;
const SITE = 'https://leokmei.com';
const CAP_MSG = 'הגעת לתקרת החודש, הכפתור יחזור ב-1 לחודש';
const HVG = { 'א': 1, 'ב': 2, 'ג': 3, 'ד': 4, 'ה': 5, 'ו': 6, 'ז': 7, 'ח': 8, 'ט': 9, 'י': 10, 'כ': 20, 'ל': 30, 'מ': 40, 'נ': 50, 'ס': 60, 'ע': 70, 'פ': 80, 'צ': 90, 'ק': 100, 'ר': 200, 'ש': 300, 'ת': 400 };
function dafNum(d) {
  d = String(d || '').trim();
  let n = 0;
  for (const c of d.replace(/[^א-ת]/g, '')) n += HVG[c] || 0;
  return n ? n * 2 + (/:$/.test(d) ? 1 : 0) : null;
}
const norm = (t) => SKC.bare(t).replace(/[֑-ׇ]/g, '').replace(/[\s ]+/g, ' ').trim();
const rid = () => Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
const month = () => new Date().toISOString().slice(0, 7);
const day = () => new Date().toISOString().slice(8, 10);

/* ---- המפתח ---- */
async function aesKey(env) {
  const raw = await crypto.subtle.digest('SHA-256', new TextEncoder().encode('sakem|' + (env.ADMIN_KEY || '')));
  return crypto.subtle.importKey('raw', raw, 'AES-GCM', false, ['encrypt', 'decrypt']);
}
const b64 = (u8) => btoa(String.fromCharCode(...u8));
const unb64 = (s) => Uint8Array.from(atob(s), (c) => c.charCodeAt(0));
async function getKey(env) {
  if (env.SAKEM_API_KEY) return env.SAKEM_API_KEY;
  const v = await env.STORE.get('skm:key', 'json');
  if (!v || !env.ADMIN_KEY) return '';
  try {
    const pt = await crypto.subtle.decrypt({ name: 'AES-GCM', iv: unb64(v.iv) }, await aesKey(env), unb64(v.ct));
    return new TextDecoder().decode(pt);
  } catch (e) { return ''; }
}
async function putKey(env, key) {
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const ct = new Uint8Array(await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, await aesKey(env), new TextEncoder().encode(key)));
  await env.STORE.put('skm:key', JSON.stringify({ iv: b64(iv), ct: b64(ct), t: Date.now() }));
}

/* ---- עלות ---- */
async function costDoc(env) { return (await env.STORE.get('skm:cost:' + month(), 'json')) || { usd: 0, n: 0, days: {} }; }
function usdOf(u) {
  u = u || {};
  return ((u.input_tokens || 0) * PRICE.in + (u.output_tokens || 0) * PRICE.out +
          (u.cache_creation_input_tokens || 0) * PRICE.cw + (u.cache_read_input_tokens || 0) * PRICE.cr) / 1e6;
}
async function addCost(env, usd) {
  const c = await costDoc(env);
  c.usd = (c.usd || 0) + usd; c.n = (c.n || 0) + 1;
  c.days[day()] = (c.days[day()] || 0) + usd;
  await env.STORE.put('skm:cost:' + month(), JSON.stringify(c));
  return c;
}

/* ---- הדוגמאות (קובץ הריפו, ואם המנהל עדכן - המחסן גובר) ---- */
async function examples(env) {
  const kv = await env.STORE.get('skm:ex', 'json');
  return (kv && Array.isArray(kv.pairs) && kv.pairs.length) ? kv.pairs : EXAMPLES.pairs;
}
function systemText(pairs) {
  const ex = pairs.map((p, i) => `דוגמה ${i + 1} (${p.kind || ''}):\nלפני:\n${p.before}\nאחרי:\n${p.after}\nמה שיניתי: ${(p.changes || []).join(' · ')}`).join('\n\n');
  return SAKEM_SYSTEM + '\n\nדוגמאות מתיקוני המחבר עצמו (לפני / אחרי):\n\n' + ex;
}

/* ---- אימות המקור: כל טקסט שנשלח קיים באתר או בעריכות המנהל ---- */
function unitTexts(u) {
  const out = [];
  const w = u.k === 'u' ? u.a : (u.k === 'm' ? u.w : '');
  String(w || '').split(/<br\s*\/?>/i).forEach((x) => { const t = norm(x); if (t) out.push(t); });
  if (u.k === 'nose' || u.k === 'dh') { const t = norm(u.a); if (t) out.push(t); }
  (u.l || []).forEach((l) => { const t = norm(l && l[1]); if (t) out.push(t); });
  if (u.mbw) { const t = norm(u.mbw); if (t) out.push(t); }
  return out;
}
async function pageFile(env, slug, daf) {
  const n = dafNum(daf);
  if (n === null) return null;
  const r = await fetch((env.SK_SITE || SITE) + '/sk/' + slug + '/' + n + '.json', { cf: { cacheTtl: 120 } });
  if (!r.ok) return null;
  try { return await r.json(); } catch (e) { return null; }
}
async function provenance(env, slug, units, pages) {
  const known = new Set();
  for (const pg of pages) if (pg) for (const u of pg.units || []) unitTexts(u).forEach((t) => known.add(t));
  const want = [];
  units.forEach((u) => unitTexts(u).forEach((t) => want.push(t)));
  let miss = want.filter((t) => !known.has(t));
  if (miss.length) {
    const doc = (await env.STORE.get('ed:' + slug, 'json')) || { edits: [] };
    for (const e of doc.edits || []) {
      if (e.del) continue;
      [e.now, e.nowH].forEach((x) => { if (x) known.add(norm(x)); });
      (e.resT || []).forEach((x) => known.add(norm(x)));
      (e.res || []).forEach((r) => { if (Array.isArray(r)) r.forEach((x) => { if (typeof x === 'string') { known.add(norm(x)); String(x).split(/<br\s*\/?>/i).forEach((y) => known.add(norm(y))); } }); });
      (e.texts || []).forEach((x) => known.add(norm(x)));
    }
    miss = miss.filter((t) => !known.has(t));
  }
  return miss;
}

/* ---- ההקשר: פירוש הגמרא ולשון הגמרא לקטעים המקבילים, וחברותא לאותו עמוד ---- */
function segRange(units, refs) {
  const keys = units.map((u) => refs.indexOf(u.ref)).filter((i) => i > -1);
  if (!keys.length) return null;
  return [Math.max(0, Math.min(...keys) - 0), Math.min(refs.length - 1, Math.max(...keys) + 1)];
}
const strip = (h) => SKC.bare(h).replace(/[֑-ׇ]/g, '').replace(/\s+/g, ' ').trim();
async function context(env, slug, units, pages) {
  let gem = '', per = '', hv = '';
  for (const pg of pages) {
    if (!pg) continue;
    const mine = units.filter((u) => u.daf === pg.daf);
    const rg = segRange(mine, pg.refs || []) || (pg.g && pg.g.length ? [0, pg.g.length - 1] : null);
    if (!rg) continue;
    for (let i = rg[0]; i <= rg[1]; i++) {
      if (pg.g && pg.g[i]) gem += '[' + pg.daf + ' ' + (i + 1) + '] ' + strip(pg.g[i]) + '\n';
      if (pg.p && pg.p[i]) per += '[' + pg.daf + ' ' + (i + 1) + '] ' + strip(pg.p[i]) + '\n';
    }
    /* חברותא: חבילת העמוד, ורק השורות שמיושרות ליחידות הקטע (ושכנותיהן) */
    const n = dafNum(pg.daf);
    if (n !== null) {
      try {
        const chunk = await env.STORE.get('hv:' + slug + ':' + Math.floor(n / 12), 'json');
        const hp = chunk && chunk[pg.daf];
        const segs = (hp && hp.segs) || [];
        const ids = new Set(mine.map((u) => u.id));
        let idx = segs.map((s, i) => (ids.has(s.p) ? i : -1)).filter((i) => i > -1);
        if (!idx.length && segs.length) idx = [];
        const pick = new Set();
        idx.forEach((i) => { pick.add(i - 1); pick.add(i); pick.add(i + 1); });
        segs.forEach((s, i) => { if (pick.has(i)) hv += (s.g ? s.g + ' ' : '') + String(s.e || '').replace(/\[\[הערה:\d+\]\]/g, '') + '\n'; });
      } catch (e) { /* בלי חברותא */ }
    }
  }
  const cut = (s, n) => (s.length > n ? s.slice(0, n) + ' …' : s);
  return { gem: cut(gem, 7000), per: cut(per, 9000), hv: cut(hv, 6000) };
}

/* ---- המודל ---- */
const SCHEMA = {
  type: 'object', additionalProperties: false, required: ['point', 'text', 'changes'],
  properties: { point: { type: 'string' }, text: { type: 'string' }, changes: { type: 'array', items: { type: 'string' } } },
};
async function callModel(env, key, sys, messages) {
  const base = { model: MODEL, max_tokens: 16000, system: [{ type: 'text', text: sys, cache_control: { type: 'ephemeral' } }], messages };
  /* הבקשה המלאה: מאמץ בינוני, פלט JSON במבנה קבוע, וגיבוי אוטומטי בסירוב. אם השרת דוחה פרמטר
     (400) - פעם אחת בלי הגיבוי ובלי המבנה, וההנחיה עצמה דורשת JSON. */
  const tries = [
    { body: Object.assign({}, base, { output_config: { effort: 'medium', format: { type: 'json_schema', schema: SCHEMA } }, fallbacks: 'default' }), beta: 'server-side-fallback-2026-07-01' },
    { body: Object.assign({}, base, { output_config: { effort: 'medium' } }), beta: '' },
  ];
  let last = null;
  for (const t of tries) {
    const h = { 'content-type': 'application/json', 'x-api-key': key, 'anthropic-version': '2023-06-01' };
    if (t.beta) h['anthropic-beta'] = t.beta;
    let r;
    try { r = await fetch('https://api.anthropic.com/v1/messages', { method: 'POST', headers: h, body: JSON.stringify(t.body) }); }
    catch (e) { return { err: 'שירות המודל אינו זמין כרגע' }; }
    let j = null;
    try { j = await r.json(); } catch (e) { /* ריק */ }
    if (r.ok && j) return { j };
    const msg = (j && j.error && j.error.message) || '';
    if (/usage limit|spend limit|credit balance|billing/i.test(msg)) return { err: CAP_MSG, cap: true };
    if (r.status === 401 || r.status === 403) return { err: 'המפתח נדחה בידי שירות המודל. הדבק מפתח חדש מן הסביבה "לאוקמי - סכם"' };
    last = { err: 'שירות המודל החזיר שגיאה (' + r.status + ')' };
    if (r.status !== 400) return last;
  }
  return last;
}
function parseOut(j) {
  if (j.stop_reason === 'refusal') return { err: 'המודל סירב לבקשה' };
  const txt = (j.content || []).filter((c) => c.type === 'text').map((c) => c.text).join('');
  let o = null;
  try { o = JSON.parse(txt); } catch (e) {
    const a = txt.indexOf('{'), b = txt.lastIndexOf('}');
    try { o = JSON.parse(txt.slice(a, b + 1)); } catch (e2) { o = null; }
  }
  if (!o || typeof o.text !== 'string') return { err: 'תשובת המודל אינה בפורמט הצפוי', raw: txt };
  return { point: String(o.point || ''), text: o.text.replace(/\r/g, '').trim(), changes: (Array.isArray(o.changes) ? o.changes : []).map(String).slice(0, 3), raw: txt };
}
/* קריאה, שומר, וקריאה חוזרת אחת עם ציון הכשל */
async function generate(env, key, sys, msgs, orig, gemara) {
  let usd = 0, out = null, errs = [];
  for (let round = 0; round < 2; round++) {
    const c = await callModel(env, key, sys, msgs);
    if (c.err) return { err: c.err, cap: c.cap, usd };
    usd += usdOf(c.j.usage);
    const p = parseOut(c.j);
    if (p.err) { errs = [p.err]; out = null; if (round === 0) { msgs = msgs.concat([{ role: 'assistant', content: p.raw || '{}' }, { role: 'user', content: 'התשובה אינה JSON תקין בשלושת השדות. החזר JSON בלבד.' }]); continue; } break; }
    out = p;
    errs = SKC.guard(orig, p.text, { gemara });
    if (!errs.length) break;
    if (round === 0) msgs = msgs.concat([{ role: 'assistant', content: p.raw }, { role: 'user', content: 'השומר שבקוד מצא בתשובה: ' + errs.join(' · ') + '. תקן והחזר את כל ה-JSON מחדש.' }]);
  }
  if (!out) return { err: errs[0] || 'לא התקבלה הצעה', usd };
  return { out, warn: errs, usd, msgs };
}

function userText(orig, before, after, ctx) {
  return [
    'הקטע המסומן לעריכה:\n<קטע>\n' + orig + '\n</קטע>',
    before ? 'שלוש שורות לפני (לקריאה בלבד, לא לשנות):\n<לפני>\n' + before + '\n</לפני>' : '',
    after ? 'שלוש שורות אחרי (לקריאה בלבד, לא לשנות):\n<אחרי>\n' + after + '\n</אחרי>' : '',
    ctx.gem ? 'לשון הגמרא (וילנא) של הקטע:\n<גמרא>\n' + ctx.gem + '</גמרא>' : '',
    ctx.per ? 'פירוש הגמרא לשורות המקבילות:\n<פירוש>\n' + ctx.per + '</פירוש>' : '',
    ctx.hv ? 'ביאור חברותא לאותו מקום:\n<חברותא>\n' + ctx.hv + '</חברותא>' : '',
    'הפירוש, החברותא ולשון הגמרא הם להבנת הפשט ולבדיקת שלמות בלבד - לא למילוי. ' +
    'החזר את הקטע המסומן מהודק באמת (יעד: לפחות כשליש פחות תווים), כתוב מחדש מתוך שלד הסוגיה ולא כהחלפת מילים, ומתוקן - כ-JSON.',
  ].filter(Boolean).join('\n\n');
}

const UK = ['u', 'm', 'nose', 'dh', 'hatz', 'perek-start', 'perek-num', 'hadran', 'perek', 'pname', 'chap'];
function cleanUnits(arr, max) {
  if (!Array.isArray(arr)) return [];
  const s = (v, n) => (typeof v === 'string' ? v : '').slice(0, n);
  return arr.slice(0, max).map((u) => ({
    id: +u.id || 0, k: s(u.k, 16), a: s(u.a, 400), w: s(u.w, 400), mbw: s(u.mbw, 60), ref: s(u.ref, 60), daf: s(u.daf, 12), first: !!u.first,
    l: Array.isArray(u.l) ? u.l.slice(0, 40).map((l) => [s(l && l[0], 40), s(l && l[1], 4000)]) : [],
    tos: Array.isArray(u.tos) ? u.tos.slice(0, 40).map((z) => ({ n: s(z.n, 12), t: s(z.t, 120) })) : [],
  })).filter((u) => u.id > 0 && u.k);
}

export async function sakemApi(req, env, url, p, h) {
  const { isAdmin, json, bad, slugOk } = h;
  if (!(await isAdmin(req, env))) return bad('אין הרשאה', 401);
  let b = {};
  if (req.method === 'POST') { try { b = await req.json(); } catch (e) { return bad('גוף הבקשה אינו JSON'); } }

  if (p === '/sakem/stat') {
    const c = await costDoc(env);
    const lg = (await env.STORE.get('skm:lg', 'json')) || { pairs: [], rejects: 0, applied: 0 };
    const fresh = lg.pairs.filter((x) => x.t > (lg.applied || 0));
    const slug = url.searchParams.get('slug') || '';
    const q = slugOk(slug) ? ((await env.STORE.get('skm:hq:' + slug, 'json')) || { items: [] }).items.filter((x) => !x.d).length : 0;
    return json({ ok: true, hasKey: !!(await getKey(env)), day: c.days[day()] || 0, month: c.usd || 0, n: c.n || 0, cap: CAP_USD,
                  capped: (c.usd || 0) >= CAP_USD, pairs: lg.pairs.length, fresh: fresh.length, rejects: lg.rejects || 0,
                  learned: !!(await env.STORE.get('skm:ex')),
                  suggest: fresh.length >= 24 ? fresh.slice(-6).map((x) => x.id) : [], queue: q });
  }
  if (p === '/sakem/key') {
    const k = String(b.key || '').trim();
    if (!/^sk-ant-[A-Za-z0-9_\-]{20,300}$/.test(k)) return bad('זה אינו נראה כמפתח של Anthropic (מתחיל ב-sk-ant-)');
    if (!env.ADMIN_KEY) return bad('חסר בשרת סוד ההצפנה');
    await putKey(env, k);
    return json({ ok: true });
  }
  if (p === '/sakem/queue') {
    const slug = url.searchParams.get('slug') || '';
    if (!slugOk(slug)) return bad('מסכת לא תקינה');
    const q = (await env.STORE.get('skm:hq:' + slug, 'json')) || { items: [] };
    return json({ ok: true, items: q.items.filter((x) => !x.d) });
  }
  if (p === '/sakem/done') {
    const slug = String(b.slug || ''), id = String(b.id || '').slice(0, 40), act = String(b.act || '');
    const pr = await env.STORE.get('skm:p:' + id, 'json');
    if (pr) {
      const lg = (await env.STORE.get('skm:lg', 'json')) || { pairs: [], rejects: 0, applied: 0, rj: [] };
      const fin = String(b.final || '').slice(0, 20000);
      if ((act === 'accept' || act === 'edit') && fin && norm(fin) !== norm(pr.text)) {
        lg.pairs.push({ id, slug, t: Date.now(), orig: pr.orig, prop: pr.text, final: fin });
        if (lg.pairs.length > 300) lg.pairs = lg.pairs.slice(-300);
      }
      if (act === 'cancel') { lg.rejects = (lg.rejects || 0) + 1; lg.rj = (lg.rj || []).concat([{ id, slug, t: Date.now(), orig: pr.orig.slice(0, 3000), prop: pr.text.slice(0, 3000) }]).slice(-200); }
      await env.STORE.put('skm:lg', JSON.stringify(lg));
      if (slugOk(slug)) {
        const qk = 'skm:hq:' + slug, q = await env.STORE.get(qk, 'json');
        if (q && q.items.some((x) => x.id === id && !x.d)) { q.items.forEach((x) => { if (x.id === id) x.d = act || 'done'; }); await env.STORE.put(qk, JSON.stringify(q)); }
      }
    }
    return json({ ok: true });
  }
  if (p === '/sakem/examples') {
    const lg = (await env.STORE.get('skm:lg', 'json')) || { pairs: [] };
    const fresh = lg.pairs.filter((x) => x.t > (lg.applied || 0)).filter((x) => x.orig.length < 1500);
    /* המובהקים: הזוגות שבהם הנוסח הסופי רחוק ביותר מן ההצעה */
    const dist = (a, c) => { const A = new Set(norm(a).split(' ')), C = new Set(norm(c).split(' ')); let x = 0; A.forEach((w) => { if (!C.has(w)) x++; }); C.forEach((w) => { if (!A.has(w)) x++; }); return x / Math.max(1, A.size + C.size); };
    const pick = fresh.map((x) => [dist(x.prop, x.final), x]).sort((a, c) => c[0] - a[0]).slice(0, 6).map((z) => z[1]);
    const base = EXAMPLES.pairs.slice(0, 8);
    const pairs = base.concat(pick.map((x) => ({ kind: 'נלמד מעריכת המנהל', before: x.orig, after: x.final, changes: ['נלמד מן הנוסח שהמנהל קיבל'] })));
    await env.STORE.put('skm:ex', JSON.stringify({ pairs, t: Date.now() }));
    lg.applied = Date.now();
    await env.STORE.put('skm:lg', JSON.stringify(lg));
    return json({ ok: true, n: pick.length });
  }

  /* ---- הצעה חדשה / קצר עוד ---- */
  const key = await getKey(env);
  if (!key) return bad('ממתין למפתח: הדבק את מפתח הסכם בחלונית הניהול', 409);
  const cost = await costDoc(env);
  if ((cost.usd || 0) >= CAP_USD) return bad(CAP_MSG, 429);
  const slug = String(b.slug || '');
  if (!slugOk(slug)) return bad('מסכת לא תקינה');

  if (p === '/sakem/more') {
    const pr = await env.STORE.get('skm:p:' + String(b.id || '').slice(0, 40), 'json');
    if (!pr) return bad('ההצעה לא נמצאה (פגה)', 404);
    const msgs = (pr.msgs || []).concat([{ role: 'assistant', content: JSON.stringify({ point: pr.point || '', text: pr.text, changes: pr.changes || [] }) },
      { role: 'user', content: 'קצר עוד: אותו קטע, בערך שליש פחות מן ההצעה שלך, וברור באותה מידה - בלי לאבד שלב בסוגיה, דעה או מסקנה. השאלה נכללת בתשובה, ושורות שאומרות דבר אחד מתאחדות. החזר JSON.' }]);
    const g = await generate(env, key, systemText(await examples(env)), msgs, pr.orig, pr.gemara || '');
    if (g.usd) await addCost(env, g.usd);
    if (g.err) return bad(g.err, g.cap ? 429 : 502);
    const id = rid();
    const rec = { id, slug, ids: pr.ids, orig: pr.orig, gemara: pr.gemara, text: g.out.text, point: g.out.point, changes: g.out.changes, warn: g.warn, msgs: g.msgs.slice(0, 1), parent: pr.id, t: Date.now(), usd: g.usd };
    await env.STORE.put('skm:p:' + id, JSON.stringify(rec), { expirationTtl: 14 * 86400 });
    return json({ ok: true, id, text: rec.text, changes: rec.changes, warn: rec.warn, usd: g.usd });
  }

  if (p !== '/sakem') return bad('נתיב לא מוכר', 404);
  const units = cleanUnits(b.units, 120);
  if (!units.length) return bad('לא נשלח קטע');
  const dafs = [...new Set(units.map((u) => u.daf).filter(Boolean))];
  if (dafs.length > 2) return bad('הקטע ארוך מדי, נא לסמן עד דף אחד');
  const pages = await Promise.all(dafs.map((d) => pageFile(env, slug, d)));
  if (pages.some((x) => !x)) return bad('קובץ העמוד לא נמצא באתר (המסכת טרם נבנתה מחדש עם סכם)', 409);
  const miss = await provenance(env, slug, units, pages);
  if (miss.length) return bad('בקטע יש שורה שלא נמצאה באתר ובעריכות שבשרת - כנראה עריכה שטרם פורסמו לשרת: "' + miss[0].slice(0, 50) + '"', 409);
  const orig = SKC.toInter(units).text;
  const before = SKC.toInter(cleanUnits(b.before, 3)).text, after = SKC.toInter(cleanUnits(b.after, 3)).text;
  const ctx = await context(env, slug, units, pages);
  const msgs = [{ role: 'user', content: userText(orig, before, after, ctx) }];
  const g = await generate(env, key, systemText(await examples(env)), msgs, orig, ctx.gem);
  if (g.usd) await addCost(env, g.usd);
  if (g.err) return bad(g.err, g.cap ? 429 : 502);
  const id = rid();
  const rec = { id, slug, ids: units.map((u) => u.id), orig, gemara: ctx.gem, text: g.out.text, point: g.out.point, changes: g.out.changes, warn: g.warn, msgs: msgs, t: Date.now(), usd: g.usd };
  await env.STORE.put('skm:p:' + id, JSON.stringify(rec), { expirationTtl: 14 * 86400 });
  if (b.queue) {
    const qk = 'skm:hq:' + slug, q = (await env.STORE.get(qk, 'json')) || { items: [] };
    q.items = q.items.filter((x) => !x.d).concat([{ id, ids: rec.ids, orig, text: rec.text, changes: rec.changes, warn: rec.warn, t: rec.t }]).slice(-500);
    await env.STORE.put(qk, JSON.stringify(q));
  }
  return json({ ok: true, id, text: rec.text, changes: rec.changes, warn: rec.warn, usd: g.usd });
}
