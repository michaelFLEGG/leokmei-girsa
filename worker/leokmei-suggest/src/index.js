/* leokmei-suggest - נקודת הקליטה של לאוקמי גירסא.

   האתר סטטי, ולכן הצעת תיקון של לומד לא היתה מגיעה לשום מקום: היא
   נשמרה בדפדפן של המציע בלבד. כאן יושב תור ההצעות ותור עריכות המנהל,
   במחסן KV אחד, בתוכנית החינמית של Cloudflare. נפרד לגמרי מממלכת
   הזוהר.

   מה יש כאן:
     POST /suggest       הצעה חדשה מן האתר (פתוח לכל, עם הגנה מזבל)
     GET  /queue         תור ההצעות הממתינות (מנהל)
     POST /decide        קבל / ערוך וקבל / דחה (מנהל)
     GET  /edits         עריכות המנהל של מסכת (מנהל; מסונכרן בין מכשירים)
     PUT  /edits         מיזוג עריכות מן המכשיר אל המחסן (מנהל)
     GET  /live          העריכות והתיקונים שהתקבלו, לכל לומד (בלי שמות)
     POST /ingested      סימון עריכות שכבר נכנסו לוורד (הקליטה הלילית)
     GET  /export        יצוא מלא לגיבוי (מנהל)

     POST /auth          מילת המנהל -> אסימון מכשיר ארוך-טווח (ראה למטה)
     GET  /devices       רשימת המכשירים המוכרים (מנהל)
     POST /devices/revoke ביטול מכשיר (מנהל)

   המפתח הסודי של המנהל יושב ב-secret בשם ADMIN_KEY בלבד. הקוד ציבורי.

   זיהוי המנהל הוא "מכשיר מוכר", ולא כתובת IP (כתובת ביתית מתחלפת אצל
   הספקית ומשותפת לכל בני הבית). מילת המנהל (secret בשם ADMIN_WORD,
   לעולם לא בקוד הציבורי) מוקלדת פעם אחת בכל מכשיר, והנקודה מנפיקה
   אסימון אקראי; במחסן נשמרת רק טביעת ה-SHA-256 שלו. מאז המכשיר מזוהה
   תמיד, בלי שאלה נוספת, ואפשר לבטל אותו. כתובת ה-IP נרשמת ביומן המכשיר
   כמידע בלבד.
   דחייה אינה מחיקה: הצעה שנדחתה נשארת במחסן בסטטוס 'rejected'. */

const MAX_LEN = 2000;
const RATE_PER_DAY = 20;
const LINK = /(https?:\/\/|www\.|\.(com|net|org|il|co|info|ru|xyz|top|io)\b)/i;

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET,POST,PUT,OPTIONS',
  'Access-Control-Allow-Headers': 'content-type, x-admin-key',
  'Access-Control-Max-Age': '86400',
};

function json(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store', ...CORS },
  });
}
function bad(msg, status = 400) { return json({ ok: false, error: msg }, status); }

/* השוואה בזמן קבוע, כדי שלא יהיה ניחוש לפי משך התשובה */
function sameKey(a, b) {
  if (typeof a !== 'string' || typeof b !== 'string' || !a || !b) return false;
  const enc = new TextEncoder();
  const x = enc.encode(a), y = enc.encode(b);
  if (x.length !== y.length) return false;
  let d = 0;
  for (let i = 0; i < x.length; i++) d |= x[i] ^ y[i];
  return d === 0;
}
async function sha256hex(t) {
  const d = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(t));
  return [...new Uint8Array(d)].map((b) => b.toString(16).padStart(2, '0')).join('');
}
/* מנהל = המפתח הסודי (הקליטה הלילית), או אסימון של מכשיר מוכר */
async function isAdmin(req, env) {
  const k = req.headers.get('x-admin-key') || '';
  if (sameKey(k, env.ADMIN_KEY || '')) return true;
  if (k.length < 32 || k.length > 100) return false;
  const h = await sha256hex(k);
  return !!(await env.STORE.get('dev:' + h));
}
const normWord = (w) => String(w || '').normalize('NFC')
  .replace(/[֑-ׇ]/g, '').replace(/[\s"'׳״“”‘’.\-]/g, '');

const str = (v, n = MAX_LEN) => (typeof v === 'string' ? v : '').slice(0, n);
const slugOk = (s) => /^[a-z-]{2,30}$/.test(s || '');
const rid = () => Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 8);

async function listAll(env, prefix) {
  const out = [];
  let cursor;
  do {
    const r = await env.STORE.list({ prefix, cursor, limit: 1000 });
    for (const k of r.keys) out.push(k);
    cursor = r.list_complete ? null : r.cursor;
  } while (cursor);
  return out;
}


/* ------------------------------------------------------------ מכשירים */
async function auth(req, env) {
  let b;
  try { b = await req.json(); } catch (e) { return bad('גוף הבקשה אינו JSON'); }
  const ip = req.headers.get('cf-connecting-ip') || '0';
  const hour = new Date().toISOString().slice(0, 13);
  const rk = 'arl:' + ip + ':' + hour;
  const n = parseInt((await env.STORE.get(rk)) || '0', 10);
  if (n >= 8) return bad('יותר מדי ניסיונות. נסה שוב בעוד שעה', 429);
  const w = normWord(b.word), want = normWord(env.ADMIN_WORD || '');
  if (!want || !w || !sameKey(w, want)) {
    await env.STORE.put(rk, String(n + 1), { expirationTtl: 4000 });
    return bad('המילה אינה נכונה', 401);
  }
  const raw = crypto.getRandomValues(new Uint8Array(32));
  const token = [...raw].map((x) => x.toString(16).padStart(2, '0')).join('');
  const h = await sha256hex(token);
  const rec = { id: h.slice(0, 10), label: str(b.label, 60), ua: str(req.headers.get('user-agent'), 160),
                ip, created: Date.now() };
  await env.STORE.put('dev:' + h, JSON.stringify(rec), { metadata: { id: rec.id, label: rec.label, created: rec.created } });
  return json({ ok: true, token, id: rec.id });
}
async function devices(req, env) {
  if (!(await isAdmin(req, env))) return bad('אין הרשאה', 401);
  const out = [];
  for (const k of await listAll(env, 'dev:')) {
    const v = await env.STORE.get(k.name, 'json');
    if (v) out.push(v);
  }
  out.sort((a, c) => c.created - a.created);
  return json({ ok: true, devices: out });
}
async function revoke(req, env) {
  if (!(await isAdmin(req, env))) return bad('אין הרשאה', 401);
  let b;
  try { b = await req.json(); } catch (e) { return bad('גוף הבקשה אינו JSON'); }
  const id = str(b.id, 20);
  if (!id) return bad('חסר מזהה');
  for (const k of await listAll(env, 'dev:')) {
    if (k.metadata && k.metadata.id === id) { await env.STORE.delete(k.name); return json({ ok: true }); }
  }
  return bad('המכשיר לא נמצא', 404);
}
async function whoami(req, env) {
  return json({ ok: true, admin: await isAdmin(req, env) });
}

/* ------------------------------------------------------------ הצעות */
async function suggest(req, env) {
  let b;
  try { b = await req.json(); } catch (e) { return bad('גוף הבקשה אינו JSON'); }
  /* שדה מלכודת: רובוט ממלא אותו, אדם אינו רואה אותו */
  if (b.hp) return bad('נדחה', 422);
  const slug = str(b.slug, 30);
  if (!slugOk(slug)) return bad('מסכת לא תקינה');
  const note = str(b.note).trim();
  if (!note) return bad('אין הצעה');
  if (note.length >= MAX_LEN || str(b.was).length >= MAX_LEN) return bad('ההצעה ארוכה מדי (עד 2,000 תווים)');
  if (LINK.test(note) || LINK.test(str(b.name, 80))) return bad('הצעה שיש בה קישור נדחית', 422);
  const ip = req.headers.get('cf-connecting-ip') || '0';
  const day = new Date().toISOString().slice(0, 10);
  const rk = 'rl:' + ip + ':' + day;
  const n = parseInt((await env.STORE.get(rk)) || '0', 10);
  if (n >= RATE_PER_DAY) return bad('יותר מדי הצעות מכתובת אחת ביום אחד. נסה מחר', 429);
  await env.STORE.put(rk, String(n + 1), { expirationTtl: 90000 });
  const t = Date.now();
  const id = slug + ':' + t + ':' + rid();
  const rec = {
    id, slug, masechet: str(b.masechet, 40), daf: str(b.daf, 12), uid: str(b.uid, 12),
    k: str(b.k, 24), ctx: { b: str(b.ctx && b.ctx.b, 60), a: str(b.ctx && b.ctx.a, 60) },
    was: str(b.was), note, name: str(b.name, 80).trim(), t, st: 'pending',
  };
  await env.STORE.put('sg:' + id, JSON.stringify(rec), { metadata: { st: 'pending', slug } });
  return json({ ok: true, id });
}

async function queue(req, env, url) {
  if (!(await isAdmin(req, env))) return bad('אין הרשאה', 401);
  const slug = url.searchParams.get('slug') || '';
  const keys = await listAll(env, 'sg:');
  const counts = {};
  const want = [];
  for (const k of keys) {
    const m = k.metadata || {};
    if (m.st !== 'pending') continue;
    counts[m.slug] = (counts[m.slug] || 0) + 1;
    if (!slug || m.slug === slug) want.push(k.name);
  }
  const items = [];
  for (const name of want) {
    const v = await env.STORE.get(name, 'json');
    if (v) items.push(v);
  }
  items.sort((a, b) => a.t - b.t);
  return json({ ok: true, items, counts, total: Object.values(counts).reduce((a, b) => a + b, 0) });
}

async function decide(req, env) {
  if (!(await isAdmin(req, env))) return bad('אין הרשאה', 401);
  let b;
  try { b = await req.json(); } catch (e) { return bad('גוף הבקשה אינו JSON'); }
  const id = str(b.id, 80);
  const st = str(b.st, 12);
  if (!id || ['accepted', 'edited', 'rejected'].indexOf(st) < 0) return bad('הכרעה לא תקינה');
  const rec = await env.STORE.get('sg:' + id, 'json');
  if (!rec) return bad('ההצעה לא נמצאה', 404);
  rec.st = st; rec.decided = Date.now();
  if (st !== 'rejected') rec.now = str(b.now);
  await env.STORE.put('sg:' + id, JSON.stringify(rec), { metadata: { st, slug: rec.slug } });
  /* הצעה שהתקבלה נעשית עריכת מנהל רגילה, באותו תור שבו יושבות
     העריכות שלו - ומשם היא נקלטת לוורד בשם המציע. */
  if (st !== 'rejected' && b.edit && b.edit.k) {
    const e = cleanEdit(b.edit);
    e.by = 'הצעה מהאתר' + (rec.name ? ' - ' + rec.name : '');
    e.sg = id;
    await mergeEdits(env, rec.slug, [e], b.sty);
  }
  return json({ ok: true });
}

/* ------------------------------------------------------------ עריכות */
function cleanEdit(e) {
  /* שינוי מבנה (פיצול או איחוי פסקה) אין לו מפתח מקום; מפתחו נגזר מזמנו */
  const k = str(e.k, 48) || (e.op === 'struct' ? 's' + (+e.t || 0) : '');
  const out = { k, t: +e.t || Date.now() };
  if (e.del) { out.del = 1; return out; }
  for (const f of ['was', 'now', 'wasH', 'nowH', 'daf', 'ps', 'psw', 'wasP', 'by', 'sg', 'op', 'kind']) {
    if (e[f] !== undefined && e[f] !== null) out[f] = typeof e[f] === 'string' ? e[f].slice(0, 8000) : e[f];
  }
  for (const f of ['texts', 'res', 'resT']) {
    if (Array.isArray(e[f])) out[f] = JSON.parse(JSON.stringify(e[f]).slice(0, 40000));
  }
  if (e.ctx) out.ctx = { b: str(e.ctx.b, 60), a: str(e.ctx.a, 60) };
  if (e.ing) out.ing = e.ing;
  return out;
}

/* מיזוג לפי מפתח המקום: החדש ביותר (t) גובר; מחיקה היא רשומה עם del,
   כדי שמכשיר אחר לא יחזיר עריכה שבוטלה. סימון 'נקלט בוורד' (ing)
   נשמר גם כשמגיעה גרסה ישנה יותר מן המכשיר. */
async function mergeEdits(env, slug, edits, sty) {
  const key = 'ed:' + slug;
  const doc = (await env.STORE.get(key, 'json')) || { slug, edits: [], sty: null };
  const by = {};
  for (const e of doc.edits) by[e.k] = e;
  for (const raw of edits) {
    const e = cleanEdit(raw);
    if (!e.k) continue;
    const old = by[e.k];
    if (!old || (e.t || 0) >= (old.t || 0)) {
      if (old && old.ing && !e.ing) e.ing = old.ing;
      if (old && old.by && !e.by) e.by = old.by;
      if (old && old.sg && !e.sg) e.sg = old.sg;
      by[e.k] = e;
    }
  }
  doc.edits = Object.values(by).sort((a, b) => (a.t || 0) - (b.t || 0));
  if (sty) doc.sty = sty;
  doc.t = Date.now();
  await env.STORE.put(key, JSON.stringify(doc));
  return doc;
}

async function getEdits(req, env, url, pub) {
  if (!pub && !(await isAdmin(req, env))) return bad('אין הרשאה', 401);
  const slug = url.searchParams.get('slug') || '';
  if (!slugOk(slug)) return bad('מסכת לא תקינה');
  const doc = (await env.STORE.get('ed:' + slug, 'json')) || { slug, edits: [], sty: null };
  if (pub) {
    /* ללומד: רק מה שמוחל, בלי שמות ובלי מחיקות */
    doc.edits = doc.edits.filter((e) => !e.del).map((e) => {
      const c = Object.assign({}, e); delete c.by; delete c.sg; return c;
    });
  }
  return json({ ok: true, doc });
}

async function putEdits(req, env) {
  if (!(await isAdmin(req, env))) return bad('אין הרשאה', 401);
  let b;
  try { b = await req.json(); } catch (e) { return bad('גוף הבקשה אינו JSON'); }
  const slug = str(b.slug, 30);
  if (!slugOk(slug)) return bad('מסכת לא תקינה');
  const doc = await mergeEdits(env, slug, Array.isArray(b.edits) ? b.edits : [], b.sty);
  return json({ ok: true, doc });
}

async function ingested(req, env) {
  if (!(await isAdmin(req, env))) return bad('אין הרשאה', 401);
  let b;
  try { b = await req.json(); } catch (e) { return bad('גוף הבקשה אינו JSON'); }
  const slug = str(b.slug, 30);
  if (!slugOk(slug)) return bad('מסכת לא תקינה');
  const keys = new Set(Array.isArray(b.keys) ? b.keys : []);
  const key = 'ed:' + slug;
  const doc = (await env.STORE.get(key, 'json')) || { slug, edits: [] };
  let n = 0;
  const when = Date.now();
  for (const e of doc.edits) if (keys.has(e.k) && !e.ing) { e.ing = when; n++; }
  doc.t = when;
  await env.STORE.put(key, JSON.stringify(doc));
  return json({ ok: true, marked: n });
}

async function exportAll(req, env) {
  if (!(await isAdmin(req, env))) return bad('אין הרשאה', 401);
  const out = { when: new Date().toISOString(), suggestions: [], edits: {} };
  for (const k of await listAll(env, 'sg:')) {
    const v = await env.STORE.get(k.name, 'json');
    if (v) out.suggestions.push(v);
  }
  for (const k of await listAll(env, 'ed:')) {
    const v = await env.STORE.get(k.name, 'json');
    if (v) out.edits[k.name.slice(3)] = v;
  }
  return json(out);
}

export default {
  async fetch(req, env) {
    if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers: CORS });
    const url = new URL(req.url);
    const p = url.pathname.replace(/\/+$/, '') || '/';
    try {
      if (p === '/' || p === '/health') return json({ ok: true, service: 'leokmei-suggest' });
      if (p === '/suggest' && req.method === 'POST') return await suggest(req, env);
      if (p === '/auth' && req.method === 'POST') return await auth(req, env);
      if (p === '/whoami' && req.method === 'GET') return await whoami(req, env);
      if (p === '/devices' && req.method === 'GET') return await devices(req, env);
      if (p === '/devices/revoke' && req.method === 'POST') return await revoke(req, env);
      if (p === '/queue' && req.method === 'GET') return await queue(req, env, url);
      if (p === '/decide' && req.method === 'POST') return await decide(req, env);
      if (p === '/edits' && req.method === 'GET') return await getEdits(req, env, url, false);
      if (p === '/live' && req.method === 'GET') return await getEdits(req, env, url, true);
      if (p === '/edits' && req.method === 'PUT') return await putEdits(req, env);
      if (p === '/ingested' && req.method === 'POST') return await ingested(req, env);
      if (p === '/export' && req.method === 'GET') return await exportAll(req, env);
      return bad('לא נמצא', 404);
    } catch (e) {
      return bad('שגיאה: ' + (e && e.message ? e.message : String(e)), 500);
    }
  },
};
