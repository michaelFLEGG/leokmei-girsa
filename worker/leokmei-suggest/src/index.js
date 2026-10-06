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
     GET/POST /notes     הערות המנהל לקלוד (פרטיות מוחלטת: מנהל בלבד)

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

/* אין מכסה: לא ליום, לא בסך הכל, ולא למספר הצעות ממתינות. המנהל רוצה שיגיהו
   כמה שיותר. התקרה לאורך הצעה בודדת קיימת רק כדי שמחסן הנתונים לא יתפוצץ
   (עשרים אלף תווים, הרבה מעבר לכל הצעה אמיתית). ההגנה היחידה מבוטים היא
   שדה מלכודת נסתר וקצב שאדם אינו יכול להגיע אליו: יותר משלושים שליחות
   בעשר שניות מאותה כתובת (בזיכרון הנקודה, בלי כתיבה למחסן). */
const MAX_LEN = 20000;
const BURST_N = 30, BURST_MS = 10000;
const burst = new Map();
function burstHit(ip) {
  const now = Date.now();
  const a = (burst.get(ip) || []).filter((t) => now - t < BURST_MS);
  a.push(now);
  burst.set(ip, a);
  if (burst.size > 500) for (const [k, v] of burst) if (!v.length || now - v[v.length - 1] > BURST_MS) burst.delete(k);
  return a.length > BURST_N;
}
const TYPES = ['nusach', 'style', 'question', 'note', 'source'];
const LINK = /(https?:\/\/|www\.|\.(com|net|org|il|co|info|ru|xyz|top|io)\b)/i;

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET,POST,PUT,OPTIONS',
  'Access-Control-Allow-Headers': 'content-type, x-admin-key, x-proposer',
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
/* ------------------------------------------------------------ מסכת בעיבוד
   דגל חד-סבבי: בזמן שמנועי העריכה רצים על קובץ הוורד של מסכת, האתר אומר
   ללומד-העורך שאפשר להמשיך לערוך (העריכות נשמרות בתור ומוחלות אחרי
   העיבוד). הדגל פג מעצמו אחרי שש שעות, כדי שלא יישאר דלוק בטעות. */
async function procGet(req, env, url) {
  const slug = url.searchParams.get('slug') || '';
  if (!slugOk(slug)) return bad('מסכת לא תקינה');
  const v = await env.STORE.get('proc:' + slug, 'json');
  return json({ ok: true, on: !!(v && v.on), since: v ? v.since : 0 });
}
async function procSet(req, env) {
  if (!(await isAdmin(req, env))) return bad('אין הרשאה', 401);
  let b;
  try { b = await req.json(); } catch (e) { return bad('גוף הבקשה אינו JSON'); }
  const slug = str(b.slug, 30);
  if (!slugOk(slug)) return bad('מסכת לא תקינה');
  if (b.on) await env.STORE.put('proc:' + slug, JSON.stringify({ on: 1, since: Date.now() }), { expirationTtl: 21600 });
  else await env.STORE.delete('proc:' + slug);
  return json({ ok: true });
}
async function whoami(req, env) {
  return json({ ok: true, admin: await isAdmin(req, env) });
}

/* ------------------------------------------------------------ מציעים
   כל מציע מזוהה במכשיר שלו: pid אקראי ואסימון סודי pt שנוצרים בדפדפן.
   במחסן נשמרת רק טביעת ה-SHA-256 של האסימון. אין חשבון ואין סיסמה. */
async function ensureProposer(env, pid, pt, name) {
  const h = await sha256hex(pt);
  const old = await env.STORE.get('pr:' + pid, 'json');
  if (old) return sameKey(old.h, h);
  await env.STORE.put('pr:' + pid, JSON.stringify({ pid, h, name, created: Date.now(), trusted: 0 }));
  return true;
}
async function isTrusted(env, pid) {
  if (!pid) return false;
  const v = await env.STORE.get('pr:' + pid, 'json');
  return !!(v && v.trusted);
}
async function proposerOk(env, pid, pt) {
  if (!/^[a-z0-9]{8,20}$/.test(pid || '') || !pt) return false;
  const v = await env.STORE.get('pr:' + pid, 'json');
  return !!(v && sameKey(v.h, await sha256hex(String(pt))));
}
/* המטא-נתונים של המפתח נושאים תקציר של ההצעה: כך אפשר לרשום, לסנן ולמיין
   אלפי הצעות בקריאת רשימה אחת, בלי לקרוא כל הצעה בנפרד (בתוכנית החינמית
   מספר הקריאות לבקשה מוגבל). הגבול של KV הוא 1024 בתים. */
function sgMeta(rec) {
  const m = {
    st: rec.st, slug: rec.slug, pid: rec.pid || '', tr: rec.tr ? 1 : 0,
    d: rec.daf || '', ty: rec.type || 'nusach', up: rec.up ? 1 : 0, un: rec.seen === 0 ? 1 : 0,
    v: (rec.ver = (rec.ver || 0) + 1), nm: (rec.name || '').slice(0, 24),
    n: (rec.note || '').slice(0, 90), w: (rec.was || '').slice(0, 50), mn: rec.mnew ? 1 : 0,
  };
  const size = () => new TextEncoder().encode(JSON.stringify(m)).length;
  while (size() > 950 && m.n.length > 10) { m.n = m.n.slice(0, Math.floor(m.n.length * 0.8)); m.w = m.w.slice(0, Math.floor(m.w.length * 0.8)); }
  while (size() > 950 && m.nm.length > 0) m.nm = m.nm.slice(0, -4);
  return m;
}
async function putSg(env, rec) {
  const meta = sgMeta(rec);
  await env.STORE.put('sg:' + rec.id, JSON.stringify(rec), { metadata: meta });
}
/* זמן ההצעה נלקח משם המפתח (sg:<מסכת>:<זמן>:<מזהה>) */
function keyT(name) { const p = name.split(':'); return +p[2] || 0; }
/* "ההצעות שלי": שורות תקציר מן המטא-נתונים (קריאת רשימה בלבד). את ההצעה
   המלאה הדפדפן מביא בצרורות (mine/batch) ושומר אצלו לפי הגרסה, כך שגם מציע
   עם מאות הצעות לא עובר את מגבלות הבקשה. */
async function mine(req, env, url) {
  const pid = url.searchParams.get('pid') || '', pt = req.headers.get('x-proposer') || '';
  /* מכשיר שמעולם לא שלח הצעה אינו רשום: אין לו הצעות, וזו אינה שגיאה (בלי 401 בקונסול) */
  if (/^[a-z0-9]{8,20}$/.test(pid) && !(await env.STORE.get('pr:' + pid))) return json({ ok: true, rows: [], unseen: 0 });
  if (!(await proposerOk(env, pid, pt))) return bad('אין הרשאה', 401);
  const rows = [];
  for (const k of await listAll(env, 'sg:')) {
    const m = k.metadata;
    if (!m || m.pid !== pid) continue;
    rows.push({ id: k.name.slice(3), t: keyT(k.name), st: m.st, slug: m.slug, daf: m.d || '', type: m.ty || '',
                up: m.up || 0, un: m.un || 0, v: m.v || 0, n: m.n || '', w: m.w || '', mn: m.mn || 0 });
  }
  rows.sort((a, b) => b.t - a.t);
  return json({ ok: true, rows, unseen: rows.filter((x) => x.un).length });
}
async function mineBatch(req, env) {
  let b;
  try { b = await req.json(); } catch (e) { return bad('גוף הבקשה אינו JSON'); }
  const pid = str(b.pid, 20), pt = req.headers.get('x-proposer') || '';
  if (!(await proposerOk(env, pid, pt))) return bad('אין הרשאה', 401);
  const out = [];
  for (const id of (Array.isArray(b.ids) ? b.ids : []).slice(0, 40)) {
    const rec = await env.STORE.get('sg:' + str(id, 80), 'json');
    if (rec && rec.pid === pid) out.push(rec);
  }
  return json({ ok: true, items: out });
}
async function mineAct(req, env, what) {
  let b;
  try { b = await req.json(); } catch (e) { return bad('גוף הבקשה אינו JSON'); }
  const pid = str(b.pid, 20), pt = req.headers.get('x-proposer') || '';
  if (!(await proposerOk(env, pid, pt))) return bad('אין הרשאה', 401);
  if (what === 'seen') {
    let n = 0;
    for (const k of await listAll(env, 'sg:')) {
      if (!k.metadata || k.metadata.pid !== pid || !k.metadata.un) continue;
      if (n >= 30) break;                 /* עד שלושים בבקשה; הבקשה הבאה תמשיך */
      const v = await env.STORE.get(k.name, 'json');
      if (v && v.seen === 0) { v.seen = 1; await putSg(env, v); n++; }
    }
    return json({ ok: true });
  }
  const rec = await env.STORE.get('sg:' + str(b.id, 80), 'json');
  if (!rec || rec.pid !== pid) return bad('ההצעה לא נמצאה', 404);
  if (what === 'reply') {
    const text = str(b.text, 600).trim();
    if (!text || LINK.test(text)) return bad('תשובה ריקה, או שיש בה קישור');
    rec.thread = (rec.thread || []).concat([{ from: 'p', txt: text, t: Date.now() }]).slice(-30);
    rec.mnew = 1;                      /* יש הודעה חדשה למנהל */
    await putSg(env, rec);
    return json({ ok: true, rec });
  }
  if (rec.st !== 'pending') return bad('אחרי שההצעה טופלה אי אפשר לשנות אותה. שלח הצעה חדשה');
  if (what === 'delete') { await env.STORE.delete('sg:' + rec.id); return json({ ok: true }); }
  if (what === 'edit') {
    const note = str(b.note).trim();
    if (!note) return bad('אין הצעה');
    if (LINK.test(note)) return bad('הצעה שיש בה קישור נדחית', 422);
    if (note.length >= MAX_LEN) return bad('ההצעה ארוכה מדי');
    if (note === rec.note && (TYPES.indexOf(b.type) < 0 || b.type === rec.type)) return json({ ok: true, rec });
    /* הגרסה הקודמת נשמרת: המציע והמנהל רואים את ההיסטוריה. העדכון הוא אותו
       פריט בתור (לא כפילות), מסומן "עודכנה". */
    rec.vers = (rec.vers || []).concat([{ note: rec.note, type: rec.type, t: rec.edited || rec.t }]).slice(-30);
    rec.note = note;
    if (TYPES.indexOf(b.type) > -1) rec.type = b.type;
    rec.edited = Date.now();
    rec.up = 1;
    await putSg(env, rec);
    return json({ ok: true, rec });
  }
  return bad('לא נמצא', 404);
}
/* תשובת המנהל בשרשור, בלי להכריע */
async function adminReply(req, env) {
  if (!(await isAdmin(req, env))) return bad('אין הרשאה', 401);
  let b;
  try { b = await req.json(); } catch (e) { return bad('גוף הבקשה אינו JSON'); }
  const rec = await env.STORE.get('sg:' + str(b.id, 80), 'json');
  if (!rec) return bad('ההצעה לא נמצאה', 404);
  const text = str(b.text, 600).trim();
  if (!text) return bad('תשובה ריקה');
  rec.thread = (rec.thread || []).concat([{ from: 'm', txt: text, t: Date.now() }]).slice(-30);
  rec.seen = 0; rec.mnew = 0;
  await putSg(env, rec);
  return json({ ok: true, rec });
}
/* מציע מהימן: הצעותיו ראשונות בתור. אין אישור אוטומטי - ההכרעה תמיד של המנהל. */
async function trust(req, env) {
  if (!(await isAdmin(req, env))) return bad('אין הרשאה', 401);
  let b;
  try { b = await req.json(); } catch (e) { return bad('גוף הבקשה אינו JSON'); }
  const pid = str(b.pid, 20);
  const v = await env.STORE.get('pr:' + pid, 'json');
  if (!v) return bad('המציע לא נמצא', 404);
  v.trusted = b.on ? 1 : 0;
  await env.STORE.put('pr:' + pid, JSON.stringify(v));
  for (const k of await listAll(env, 'sg:')) {
    if (k.metadata && k.metadata.pid === pid && k.metadata.st === 'pending') {
      const r = await env.STORE.get(k.name, 'json');
      if (r) { r.tr = v.trusted; await putSg(env, r); }
    }
  }
  return json({ ok: true, trusted: v.trusted });
}
/* סיכום הלמידה לדף הניהול, וכללים שהמנהל ביטל. הלומד (tools/learn_corrections.py) כותב
   את הסיכום; המנהל קורא אותו ומבטל כלל בלחיצה. הביטול נקלט בריצה הבאה של הלומד. */
async function learn(req, env, method) {
  if (!(await isAdmin(req, env))) return bad('אין הרשאה', 401);
  if (method === 'GET') {
    const sum = await env.STORE.get('ln:last', 'json');
    const off = (await env.STORE.get('ln:off', 'json')) || [];
    return json({ ok: true, summary: sum, off });
  }
  let b;
  try { b = await req.json(); } catch (e) { return bad('גוף הבקשה אינו JSON'); }
  if (b.off !== undefined) {                     /* ביטול או החזרה של כלל */
    const id = str(b.off, 20);
    let off = (await env.STORE.get('ln:off', 'json')) || [];
    off = off.filter((x) => x !== id);
    if (b.on === false || b.on === undefined) off.push(id);
    await env.STORE.put('ln:off', JSON.stringify(off));
    return json({ ok: true, off });
  }
  await env.STORE.put('ln:last', JSON.stringify(b).slice(0, 60000));
  return json({ ok: true });
}

/* הערות המנהל לקלוד (6.10.2026, פרטיות מוחלטת): הסבר קצר לרעיון שמאחורי תיקון.
   נשמרות במחסן הפרטי תחת המפתח nt: ונקראות רק במסלול של מנהל (מפתח או מכשיר מוכר).
   אינן נכנסות ל-/live, ל-/export הציבורי (הוא עצמו מנהל בלבד), לריפו או לבנייה.
   הלומד (tools/learn_corrections.py) קורא אותן בכל סבב למידה, קודם לכל דבר, ומסמן "נלמד". */
async function notes(req, env, method) {
  if (!(await isAdmin(req, env))) return bad('אין הרשאה', 401);
  if (method === 'GET') {
    const out = [];
    for (const k of await listAll(env, 'nt:')) {
      const v = await env.STORE.get(k.name, 'json');
      if (v) out.push(v);
    }
    out.sort((a, b) => b.t - a.t);
    return json({ ok: true, items: out });
  }
  let b;
  try { b = await req.json(); } catch (e) { return bad('גוף הבקשה אינו JSON'); }
  const op = str(b.op, 10);
  if (op === 'add') {
    const note = str(b.note, 2000).trim();
    if (!note) return bad('ההערה ריקה');
    const id = rid();
    const rec = {
      id, t: Date.now(), slug: str(b.slug, 30), masechet: str(b.masechet, 30), daf: str(b.daf, 12),
      sel: str(b.sel, 4000), was: str(b.was, 4000), now: str(b.now, 4000), k: str(b.k, 48),
      note, learned: 0,
    };
    await env.STORE.put('nt:' + id, JSON.stringify(rec));
    return json({ ok: true, id, item: rec });
  }
  const id = str(b.id, 40);
  if (op === 'learned') {                         /* סימון "נלמד" לרשימת מזהים */
    const ids = Array.isArray(b.ids) ? b.ids.slice(0, 200) : (id ? [id] : []);
    let n = 0;
    for (const x of ids) {
      const rec = await env.STORE.get('nt:' + str(x, 40), 'json');
      if (!rec) continue;
      rec.learned = b.on === false ? 0 : Date.now();
      await env.STORE.put('nt:' + rec.id, JSON.stringify(rec));
      n++;
    }
    return json({ ok: true, n });
  }
  const rec = id ? await env.STORE.get('nt:' + id, 'json') : null;
  if (!rec) return bad('ההערה לא נמצאה', 404);
  if (op === 'edit') {
    const note = str(b.note, 2000).trim();
    if (!note) return bad('ההערה ריקה');
    rec.note = note;
    rec.t2 = Date.now();
    rec.learned = 0;                              /* הערה שנערכה נקראת שוב בסבב הבא */
    await env.STORE.put('nt:' + id, JSON.stringify(rec));
    return json({ ok: true, item: rec });
  }
  if (op === 'del') {
    await env.STORE.delete('nt:' + id);
    return json({ ok: true });
  }
  return bad('פעולה לא מוכרת');
}

/* יומן התיקונים (פרטי, למנהל בלבד): חומר הלמידה. נכתב מן הדף, ונקרא בידי הלומד. */
async function journal(req, env, method) {
  if (!(await isAdmin(req, env))) return bad('אין הרשאה', 401);
  if (method === 'GET') {
    const out = [];
    for (const k of await listAll(env, 'jr:')) {
      const v = await env.STORE.get(k.name, 'json');
      if (v) out.push(v);
    }
    out.sort((a, b) => a.t - b.t);
    return json({ ok: true, items: out });
  }
  let b;
  try { b = await req.json(); } catch (e) { return bad('גוף הבקשה אינו JSON'); }
  const list = Array.isArray(b.items) ? b.items.slice(0, 50) : [];
  for (const it of list) {
    const id = str(it.id, 80) || rid();
    const rec = {
      id, t: +it.t || Date.now(), slug: str(it.slug, 30), daf: str(it.daf, 12), k: str(it.k, 48),
      src: str(it.src, 12),                       /* site / suggest / word */
      was: str(it.was, 4000), now: str(it.now, 4000), wasP: str(it.wasP, 40), ps: str(it.ps, 40),
      ctx: it.ctx ? { b: str(it.ctx.b, 200), a: str(it.ctx.a, 200) } : null,
      neg: it.neg ? 1 : 0,                        /* הצעה שנדחתה: דוגמה שלילית */
      why: str(it.why, 300),
    };
    await env.STORE.put('jr:' + id, JSON.stringify(rec));
  }
  return json({ ok: true, n: list.length });
}
/* הכרעה בצרור: דחייה או התיישנות של כמה הצעות (למשל כל הצעות מציע אחד) */
async function bulk(req, env) {
  if (!(await isAdmin(req, env))) return bad('אין הרשאה', 401);
  let b;
  try { b = await req.json(); } catch (e) { return bad('גוף הבקשה אינו JSON'); }
  const st = str(b.st, 12);
  if (['rejected', 'stale', 'pending'].indexOf(st) < 0) return bad('הכרעה לא תקינה');
  let n = 0;
  for (const id of (Array.isArray(b.ids) ? b.ids : []).slice(0, 25)) {
    const rec = await env.STORE.get('sg:' + str(id, 80), 'json');
    if (!rec) continue;
    rec.st = st; rec.decided = Date.now(); rec.reason = str(b.reason, 200); rec.seen = 0;
    await putSg(env, rec); n++;
  }
  return json({ ok: true, n });
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
  if (note.length >= MAX_LEN || str(b.was).length >= MAX_LEN) return bad('ההצעה ארוכה מדי');
  if (LINK.test(note) || LINK.test(str(b.name, 80))) return bad('הצעה שיש בה קישור נדחית', 422);
  const ip = req.headers.get('cf-connecting-ip') || '0';
  if (burstHit(ip)) return bad('השליחה מהירה מדי. נסה שוב בעוד רגע', 429);
  const t = Date.now();
  const id = slug + ':' + t + ':' + rid();
  const pid = /^[a-z0-9]{8,20}$/.test(b.pid || '') ? b.pid : '';
  const type = TYPES.indexOf(b.type) > -1 ? b.type : 'nusach';
  if (pid && b.pt && !(await ensureProposer(env, pid, str(b.pt, 80), str(b.name, 80).trim()))) return bad('הזהות במכשיר אינה תואמת', 401);
  /* הצעה שנולדה מהצעה קודמת (חידוד אחרי דחייה, או ליטוש אחרי אישור) */
  let from = '';
  if (pid && b.from) {
    const old = await env.STORE.get('sg:' + str(b.from, 80), 'json');
    if (old && old.pid === pid) {
      from = old.id;
      old.next = (old.next || []).concat([id]).slice(-10);
      await putSg(env, old);
    }
  }
  const rec = {
    id, slug, masechet: str(b.masechet, 40), daf: str(b.daf, 12), uid: str(b.uid, 12),
    k: str(b.k, 24), ctx: { b: str(b.ctx && b.ctx.b, 60), a: str(b.ctx && b.ctx.a, 60) },
    was: str(b.was), note, name: str(b.name, 80).trim(), t, st: 'pending',
    type, pid, thread: [], seen: 1, tr: (await isTrusted(env, pid)) ? 1 : 0,
  };
  if (from) rec.from = from;
  await putSg(env, rec);
  return json({ ok: true, id });
}

/* תור המנהל: דף אחד בכל פעם, עם סינון לפי מציע / דף / סוג / "עודכנה". הספירות
   והמיון נעשים מן המטא-נתונים, וההצעות המלאות נקראות רק לדף המבוקש.
   הצעות ישנות שאין להן תקציר במטא-נתונים משודרגות בדרך (עד שלושים בבקשה). */
async function queue(req, env, url) {
  if (!(await isAdmin(req, env))) return bad('אין הרשאה', 401);
  const q = url.searchParams;
  const slug = q.get('slug') || '', pidF = q.get('pid') || '', dafF = q.get('daf') || '', tyF = q.get('ty') || '';
  const upF = q.get('up') === '1', page = Math.max(0, parseInt(q.get('page') || '0', 10) || 0);
  const size = Math.min(40, Math.max(5, parseInt(q.get('size') || '30', 10) || 30));
  const keys = await listAll(env, 'sg:');
  const counts = {}, props = {};
  const want = [], legacy = [];
  for (const k of keys) {
    const m = k.metadata || {};
    if (m.st !== 'pending') continue;
    counts[m.slug] = (counts[m.slug] || 0) + 1;
    if (slug && m.slug !== slug) continue;
    if (m.v === undefined) { legacy.push(k.name); continue; }
    if (m.pid) { const p = props[m.pid] || (props[m.pid] = { pid: m.pid, name: '', n: 0 }); p.n++; if (m.nm) p.name = m.nm; }
    if (pidF && m.pid !== pidF) continue;
    if (dafF && m.d !== dafF) continue;
    if (tyF && m.ty !== tyF) continue;
    if (upF && !m.up) continue;
    want.push({ name: k.name, tr: m.tr ? 1 : 0, t: keyT(k.name) });
  }
  for (const name of legacy.slice(0, 30)) {
    const rec = await env.STORE.get(name, 'json');
    if (rec) await putSg(env, rec);
  }
  for (const name of legacy) want.push({ name, tr: 0, t: keyT(name) });
  want.sort((a, b) => (b.tr - a.tr) || (a.t - b.t));
  const slice = want.slice(page * size, page * size + size);
  const items = [];
  for (const w of slice) {
    const v = await env.STORE.get(w.name, 'json');
    if (v) items.push(v);
  }
  return json({ ok: true, items, counts, total: Object.values(counts).reduce((a, b) => a + b, 0),
                matched: want.length, page, size, proposers: Object.values(props).sort((a, b) => b.n - a.n).slice(0, 60) });
}

async function decide(req, env) {
  if (!(await isAdmin(req, env))) return bad('אין הרשאה', 401);
  let b;
  try { b = await req.json(); } catch (e) { return bad('גוף הבקשה אינו JSON'); }
  const id = str(b.id, 80);
  const st = str(b.st, 12);
  if (!id || ['accepted', 'edited', 'rejected', 'stale', 'pending'].indexOf(st) < 0) return bad('הכרעה לא תקינה');
  const rec = await env.STORE.get('sg:' + id, 'json');
  if (!rec) return bad('ההצעה לא נמצאה', 404);
  rec.st = st; rec.decided = Date.now(); rec.up = 0;
  rec.reason = (st === 'rejected' || st === 'stale') ? str(b.reason, 200) : '';
  rec.seen = st === 'pending' ? 1 : 0;      /* התראה למציע: ההצעה טופלה */
  if (st === 'accepted' || st === 'edited') rec.now = str(b.now);
  await putSg(env, rec);
  /* הצעה שהתקבלה נעשית עריכת מנהל רגילה, באותו תור שבו יושבות
     העריכות שלו - ומשם היא נקלטת לוורד בשם המציע. */
  if ((st === 'accepted' || st === 'edited') && b.edit && b.edit.k) {
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

/* כל תיקון של המנהל נרשם ביומן התיקונים (פרטי), כחומר למידה. הרישום נעשה כאן,
   בנקודת המיזוג, ולכן הוא שלם בלי לעצור את המנהל ובלי תלות בדפדפן. */
async function jrFromEdit(env, slug, e) {
  try {
    const struct = e.op === 'struct';
    const id = 'ed-' + slug + '-' + e.k + '-' + (e.t || 0);
    const rec = {
      id, t: e.t || Date.now(), slug, daf: str(e.daf, 12), k: e.k,
      src: e.sg ? 'suggest' : (e.by ? 'word' : 'site'),
      kind: struct ? str(e.kind, 12) : 'text',
      was: struct ? str((e.texts || []).join(' | '), 4000) : str(e.was, 4000),
      now: struct ? str((e.resT || []).join(' | '), 4000) : str(e.now, 4000),
      wasH: struct ? '' : str(e.wasH, 6000), nowH: struct ? '' : str(e.nowH, 6000),
      wasP: str(e.wasP, 40), ps: str(e.ps, 40),
      ctx: e.ctx ? { b: str(e.ctx.b, 200), a: str(e.ctx.a, 200) } : null, neg: 0, why: '',
    };
    await env.STORE.put('jr:' + id, JSON.stringify(rec));
  } catch (err) { /* היומן אינו עוצר את העריכה */ }
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
      if (!old || (e.t || 0) > (old.t || 0)) await jrFromEdit(env, slug, e);
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

/* ------------------------------------------------------------ בקרת תוכן (6.10.2026)
   ממצאי הבקרה והכרעות המחבר. הכול למנהל בלבד: הממצאים אינם נשלחים ללומד
   ואינם בקובצי האתר, אלא נטענים מכאן אחרי שהמכשיר הוכר.
     PUT  /bakara/data   העלאת קובץ ממצאים של פרק (slug, perek, data)
     GET  /bakara/data   כל הפרקים של מסכת (slug), או רשימת המסכתות (בלי slug)
     GET  /bakara/dec    ההכרעות של מסכת (slug)
     POST /bakara/dec    רישום הכרעות: {slug, items:[{id,d,txt,det,kind,t}]}
     GET  /bakara/stats  סיכום לפי סוג גלאי: אושרו / נדחו / נערכו
   ההכרעה: ok = אושר והוחל, todo = אושר לביצוע, no = נדחה, edit = נערך,
   pending = ביטול ההכרעה (חוזר לתור). המאגר הוא מסמך אחד לכל מסכת, והחדש
   ביותר (t) גובר, כמו בעריכות. */
const BK_D = ['ok', 'todo', 'no', 'edit', 'pending'];
async function bkData(req, env, url, method) {
  if (!(await isAdmin(req, env))) return bad('אין הרשאה', 401);
  if (method === 'GET') {
    const slug = url.searchParams.get('slug') || '';
    if (!slug) {
      const out = [];
      for (const k of await listAll(env, 'bk:d:')) out.push(k.name.slice(5));
      return json({ ok: true, slugs: out });
    }
    if (!slugOk(slug)) return bad('מסכת לא תקינה');
    const doc = (await env.STORE.get('bk:d:' + slug, 'json')) || { slug, perakim: {} };
    return json({ ok: true, doc });
  }
  let b;
  try { b = await req.json(); } catch (e) { return bad('גוף הבקשה אינו JSON'); }
  const slug = str(b.slug, 30), perek = String(+b.perek || 0);
  if (!slugOk(slug) || perek === '0') return bad('מסכת או פרק לא תקינים');
  if (!b.data || !Array.isArray(b.data.findings)) return bad('אין ממצאים');
  const doc = (await env.STORE.get('bk:d:' + slug, 'json')) || { slug, perakim: {} };
  doc.perakim[perek] = b.data;
  doc.t = Date.now();
  await env.STORE.put('bk:d:' + slug, JSON.stringify(doc));
  return json({ ok: true, perek, n: b.data.findings.length });
}
async function bkDec(req, env, url, method) {
  if (!(await isAdmin(req, env))) return bad('אין הרשאה', 401);
  if (method === 'GET') {
    const slug = url.searchParams.get('slug') || '';
    if (!slugOk(slug)) return bad('מסכת לא תקינה');
    const doc = (await env.STORE.get('bk:c:' + slug, 'json')) || { slug, dec: {} };
    return json({ ok: true, doc });
  }
  let b;
  try { b = await req.json(); } catch (e) { return bad('גוף הבקשה אינו JSON'); }
  const slug = str(b.slug, 30);
  if (!slugOk(slug)) return bad('מסכת לא תקינה');
  const doc = (await env.STORE.get('bk:c:' + slug, 'json')) || { slug, dec: {} };
  let n = 0;
  for (const it of (Array.isArray(b.items) ? b.items : []).slice(0, 300)) {
    const id = str(it.id, 24);
    if (!/^[0-9a-f]{6,24}$/.test(id) || BK_D.indexOf(it.d) < 0) continue;
    const t = +it.t || Date.now();
    const old = doc.dec[id];
    if (old && (old.t || 0) > t) continue;
    if (it.d === 'pending') { delete doc.dec[id]; n++; continue; }
    doc.dec[id] = { d: it.d, txt: str(it.txt, 1000), det: str(it.det, 20), kind: str(it.kind, 40),
                    now: str(it.now, 1000), t };
    n++;
  }
  doc.t = Date.now();
  await env.STORE.put('bk:c:' + slug, JSON.stringify(doc));
  return json({ ok: true, n, doc });
}
async function bkStats(req, env) {
  if (!(await isAdmin(req, env))) return bad('אין הרשאה', 401);
  const by = {};
  let total = 0;
  for (const k of await listAll(env, 'bk:c:')) {
    const doc = await env.STORE.get(k.name, 'json');
    for (const id in ((doc && doc.dec) || {})) {
      const x = doc.dec[id];
      const s = by[x.det || '?'] || (by[x.det || '?'] = { ok: 0, no: 0, edit: 0 });
      if (x.d === 'ok' || x.d === 'todo') s.ok++; else if (x.d === 'no') s.no++; else if (x.d === 'edit') s.edit++;
      total++;
    }
  }
  return json({ ok: true, total, by });
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
  out.bakara = {};
  for (const k of await listAll(env, 'bk:c:')) {
    const v = await env.STORE.get(k.name, 'json');
    if (v) out.bakara[k.name.slice(5)] = v;
  }
  return json(out);
}

/* ------------------------------------------------------------ מערכת הלומד (6.10.2026)
   סנכרון בין מכשירים בקוד זמני, וסטטיסטיקה אנונימית ומצטברת למנהל.
   נתוני הלומד יושבים כאן, במחסן הפרטי, ולא במאגר הציבורי. הזהות היא אותה
   זהות מכשיר של המציעים (pid + אסימון). */
const LN_CAP = 30000;
function lnCompact(list) {
  const lastPs = {}, lastCf = {}, out = [];
  for (const e of list) {
    if (e.k === 'ps') { const k = e.s || '*'; if (!lastPs[k] || lastPs[k].t < e.t) lastPs[k] = e; }
    else if (e.k === 'cf') { if (!lastCf[e.key] || lastCf[e.key].t < e.t) lastCf[e.key] = e; }
  }
  for (const e of list) {
    if (e.k === 'ps') { if (lastPs[e.s || '*'] === e) out.push(e); }
    else if (e.k === 'cf') { if (lastCf[e.key] === e) out.push(e); }
    else out.push(e);
  }
  return out;
}
async function lnSync(req, env) {
  let b;
  try { b = await req.json(); } catch (e) { return bad('גוף הבקשה אינו JSON'); }
  const pid = str(b.pid, 20), pt = req.headers.get('x-proposer') || '';
  if (!/^[a-z0-9]{8,20}$/.test(pid) || !pt) return bad('אין הרשאה', 401);
  if (!(await ensureProposer(env, pid, str(pt, 80), ''))) return bad('הזהות במכשיר אינה תואמת', 401);
  const ip = req.headers.get('cf-connecting-ip') || '0';
  if (burstHit(ip)) return bad('מהיר מדי. נסה שוב בעוד רגע', 429);
  const have = (await env.STORE.get('ln:' + pid, 'json')) || { ev: [] };
  const byId = {};
  for (const e of have.ev) if (e && e.id) byId[e.id] = e;
  for (const e of (Array.isArray(b.ev) ? b.ev : []).slice(0, 8000)) {
    if (!e || typeof e.id !== 'string' || e.id.length > 60 || typeof e.k !== 'string') continue;
    /* ישיבה פתוחה מתעדכנת: אותו מזהה, הגרסה האחרונה (לפי t1) */
    const old = byId[e.id];
    if (!old || (e.t1 || e.t || 0) >= (old.t1 || old.t || 0)) byId[e.id] = e;
  }
  let ev = lnCompact(Object.values(byId).sort((a, c) => (a.t || 0) - (c.t || 0)));
  if (ev.length > LN_CAP) ev = ev.slice(-LN_CAP);
  await env.STORE.put('ln:' + pid, JSON.stringify({ ev, t: Date.now() }));
  return json({ ok: true, ev });
}
const CODE_ALPHA = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
async function lnCode(req, env) {
  let b;
  try { b = await req.json(); } catch (e) { return bad('גוף הבקשה אינו JSON'); }
  const pid = str(b.pid, 20), pt = req.headers.get('x-proposer') || '';
  if (!(await proposerOk(env, pid, pt))) return bad('אין הרשאה', 401);
  let code = '';
  const r = crypto.getRandomValues(new Uint8Array(8));
  for (const x of r) code += CODE_ALPHA[x % CODE_ALPHA.length];
  /* תקף עשר דקות ונמחק אחרי מימוש: האסימון עובר רק בקוד קצר-חיים */
  await env.STORE.put('lc:' + code, JSON.stringify({ pid, pt }), { expirationTtl: 600 });
  return json({ ok: true, code });
}
async function lnRedeem(req, env) {
  let b;
  try { b = await req.json(); } catch (e) { return bad('גוף הבקשה אינו JSON'); }
  const code = str(b.code, 12).toUpperCase().replace(/[^A-Z0-9]/g, '');
  if (code.length !== 8) return bad('הקוד אינו תקין');
  const ip = req.headers.get('cf-connecting-ip') || '0';
  if (burstHit(ip)) return bad('מהיר מדי. נסה שוב בעוד רגע', 429);
  const rec = await env.STORE.get('lc:' + code, 'json');
  if (!rec) return bad('הקוד אינו תקף או שפג תוקפו', 404);
  await env.STORE.delete('lc:' + code);
  return json({ ok: true, pid: rec.pid, pt: rec.pt });
}
/* סטטיסטיקה אנונימית: מונים מצטברים לפי יום. בלי שם ובלי זהות; מזהה אקראי
   של התקנה משמש רק לספירת לומדים ייחודיים, ואינו קשור ל-pid של המציעים. */
const BOT = /bot|crawl|spider|slurp|headless|lighthouse/i;
function ilDay(t) { return new Date(t).toLocaleDateString('en-CA', { timeZone: 'Asia/Jerusalem' }); }
async function lnStat(req, env) {
  if (BOT.test(req.headers.get('user-agent') || '')) return json({ ok: true, skipped: 1 });
  let b;
  try { b = await req.json(); } catch (e) { return bad('גוף הבקשה אינו JSON'); }
  const ip = req.headers.get('cf-connecting-ip') || '0';
  if (burstHit(ip)) return bad('מהיר מדי', 429);
  const byDay = {};
  for (const e of (Array.isArray(b.ev) ? b.ev : []).slice(0, 60)) {
    if (!e || !/^[a-z0-9]{8,16}$/.test(e.aid || '') || !slugOk(e.s || '')) continue;
    const t = Math.min(Date.now(), Math.max(Date.now() - 3 * 86400000, +e.t || Date.now()));
    (byDay[ilDay(t)] = byDay[ilDay(t)] || []).push(e);
  }
  for (const day of Object.keys(byDay)) {
    const key = 'st:' + day;
    const rec = (await env.STORE.get(key, 'json')) || { aids: {}, pages: {}, fin: {}, by: {} };
    for (const e of byDay[day]) {
      if (Object.keys(rec.aids).length < 6000) rec.aids[e.aid] = 1;
      const d = str(e.d, 10);
      const k = e.s + '|' + d;
      const pg = rec.pages[k] || (rec.pages[k] = { r: 0, s: 0, d: 0, ms: 0, rm: 0 });
      if (e.start) pg.s++;
      if (e.done) { pg.d++; pg.r++; pg.rm += Math.min(7200000, +e.ms || 0); }
      const m = rec.by[e.s] || (rec.by[e.s] = { r: 0, ms: 0 });
      if (e.done) m.r++;
      m.ms += Math.min(3600000, Math.max(0, +e.ms || 0));
      if (e.fin) rec.fin[e.s] = (rec.fin[e.s] || 0) + 1;
    }
    await env.STORE.put(key, JSON.stringify(rec), { expirationTtl: 86400 * 400 });
  }
  return json({ ok: true });
}
async function lnStats(req, env) {
  if (!(await isAdmin(req, env))) return bad('אין הרשאה', 401);
  const today = new Date();
  const days = [];
  for (let i = 0; i < 35; i++) days.push(ilDay(today.getTime() - i * 86400000));
  const recs = await Promise.all(days.map((d) => env.STORE.get('st:' + d, 'json')));
  const uniq = (from) => { const s = new Set(); for (let i = 0; i < from; i++) if (recs[i]) for (const a of Object.keys(recs[i].aids)) s.add(a); return s.size; };
  const pages = {}, by = {}, fin = {};
  recs.forEach((r) => {
    if (!r) return;
    for (const [k, v] of Object.entries(r.pages)) { const p = pages[k] || (pages[k] = { r: 0, s: 0, d: 0, rm: 0 }); p.r += v.r; p.s += v.s; p.d += v.d; p.rm += v.rm; }
    for (const [k, v] of Object.entries(r.by)) { const m = by[k] || (by[k] = { r: 0, ms: 0 }); m.r += v.r; m.ms += v.ms; }
    for (const [k, v] of Object.entries(r.fin)) fin[k] = (fin[k] || 0) + v;
  });
  const rows = Object.entries(pages).map(([k, v]) => { const [s, d] = k.split('|'); return { s, d, reads: v.r, starts: v.s, done: v.d, avg: v.d ? v.rm / v.d : 0 }; });
  return json({
    ok: true,
    data: {
      totals: { today: uniq(1), week: uniq(7), month: uniq(30), finished: Object.values(fin).reduce((a, b) => a + b, 0) },
      byMasechet: Object.entries(by).map(([s, v]) => ({ s, reads: v.r, ms: v.ms })).sort((a, b) => b.reads - a.reads),
      topPages: rows.slice().sort((a, b) => b.reads - a.reads).slice(0, 40).map((x) => ({ s: x.s, d: x.d, reads: x.reads })),
      abandon: rows.filter((x) => x.starts >= 5).map((x) => ({ s: x.s, d: x.d, starts: x.starts, done: x.done })).sort((a, b) => (a.done / a.starts) - (b.done / b.starts)).slice(0, 30),
      slow: rows.filter((x) => x.done >= 5).map((x) => ({ s: x.s, d: x.d, avg: x.avg, n: x.done })).sort((a, b) => b.avg - a.avg).slice(0, 30),
    },
  });
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
      if (p === '/proc' && req.method === 'GET') return await procGet(req, env, url);
      if (p === '/proc' && req.method === 'POST') return await procSet(req, env);
      if (p === '/whoami' && req.method === 'GET') return await whoami(req, env);
      if (p === '/devices' && req.method === 'GET') return await devices(req, env);
      if (p === '/devices/revoke' && req.method === 'POST') return await revoke(req, env);
      if (p === '/mine' && req.method === 'GET') return await mine(req, env, url);
      if (p === '/mine/batch' && req.method === 'POST') return await mineBatch(req, env);
      if (p === '/mine/edit' && req.method === 'POST') return await mineAct(req, env, 'edit');
      if (p === '/mine/delete' && req.method === 'POST') return await mineAct(req, env, 'delete');
      if (p === '/mine/reply' && req.method === 'POST') return await mineAct(req, env, 'reply');
      if (p === '/mine/seen' && req.method === 'POST') return await mineAct(req, env, 'seen');
      if (p === '/reply' && req.method === 'POST') return await adminReply(req, env);
      if (p === '/trust' && req.method === 'POST') return await trust(req, env);
      if (p === '/bulk' && req.method === 'POST') return await bulk(req, env);
      if (p === '/journal') return await journal(req, env, req.method);
      if (p === '/notes') return await notes(req, env, req.method);
      if (p === '/learn') return await learn(req, env, req.method);
      if (p === '/queue' && req.method === 'GET') return await queue(req, env, url);
      if (p === '/decide' && req.method === 'POST') return await decide(req, env);
      if (p === '/edits' && req.method === 'GET') return await getEdits(req, env, url, false);
      if (p === '/live' && req.method === 'GET') return await getEdits(req, env, url, true);
      if (p === '/edits' && req.method === 'PUT') return await putEdits(req, env);
      if (p === '/ingested' && req.method === 'POST') return await ingested(req, env);
      if (p === '/bakara/data' && (req.method === 'GET' || req.method === 'PUT')) return await bkData(req, env, url, req.method);
      if (p === '/bakara/dec' && (req.method === 'GET' || req.method === 'POST')) return await bkDec(req, env, url, req.method);
      if (p === '/bakara/stats' && req.method === 'GET') return await bkStats(req, env);
      if (p === '/export' && req.method === 'GET') return await exportAll(req, env);
      if (p === '/ln/sync' && req.method === 'POST') return await lnSync(req, env);
      if (p === '/ln/code' && req.method === 'POST') return await lnCode(req, env);
      if (p === '/ln/redeem' && req.method === 'POST') return await lnRedeem(req, env);
      if (p === '/ln/stat' && req.method === 'POST') return await lnStat(req, env);
      if (p === '/ln/stats' && req.method === 'GET') return await lnStats(req, env);
      return bad('לא נמצא', 404);
    } catch (e) {
      return bad('שגיאה: ' + (e && e.message ? e.message : String(e)), 500);
    }
  },
};
