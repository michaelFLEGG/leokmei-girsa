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
const TYPES = ['nusach', 'style', 'struct', 'question', 'note', 'source'];
/* סוגי-משנה של הצעה מן העורך (מנה 2, 7.10.2026): נרשמת בהצעה כפעולה מדויקת */
const SKINDS = ['text', 'create', 'remove', 'replace', 'para', 'struct', 'mixed'];
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
/* זהויות שאוחדו (7.10.2026): מציע שעבר כתובת או מכשיר ונוצרה לו זהות חדשה.
   ברשומה pr:<החדש> השדה also מחזיק את הזהויות הישנות שלו. הצעות הזהויות
   הישנות נראות לו, ואף אחת לא נמחקת ולא נדרסת. */
async function pidSet(env, pid) {
  const v = await env.STORE.get('pr:' + pid, 'json');
  return new Set([pid].concat((v && Array.isArray(v.also)) ? v.also : []));
}
async function mergePid(req, env) {
  if (!(await isAdmin(req, env))) return bad('אין הרשאה', 401);
  let b;
  try { b = await req.json(); } catch (e) { return bad('גוף הבקשה אינו JSON'); }
  const from = str(b.from, 20), to = str(b.to, 20);
  const dst = await env.STORE.get('pr:' + to, 'json');
  if (!dst || !(await env.STORE.get('pr:' + from))) return bad('אחת הזהויות לא נמצאה', 404);
  dst.also = Array.from(new Set((dst.also || []).concat([from])));
  await env.STORE.put('pr:' + to, JSON.stringify(dst));
  return json({ ok: true, also: dst.also });
}
/* המטא-נתונים של המפתח נושאים תקציר של ההצעה: כך אפשר לרשום, לסנן ולמיין
   אלפי הצעות בקריאת רשימה אחת, בלי לקרוא כל הצעה בנפרד (בתוכנית החינמית
   מספר הקריאות לבקשה מוגבל). הגבול של KV הוא 1024 בתים. */
/* מיקום בתוך הדף: מספר הפסקה ואחריו המילה (מפתח הקטע u<פסקה>.<מילה>) */
function posOf(k) {
  const m = /^u(\d+)(?:\.(\d+))?/.exec(k || '');
  return m ? (+m[1]) * 1000 + (+m[2] || 0) : 0;
}
/* סדר הש"ס ושמות המסכתות, למיון לפי מסכת */
const SHAS = [['berakhot','ברכות'],['shabbat','שבת'],['eruvin','עירובין'],['pesachim','פסחים'],['shekalim','שקלים'],['yoma','יומא'],['sukkah','סוכה'],['beitzah','ביצה'],['rosh-hashanah','ראש השנה'],['taanit','תענית'],['megillah','מגילה'],['moed-katan','מועד קטן'],['chagigah','חגיגה'],['yevamot','יבמות'],['ketubot','כתובות'],['nedarim','נדרים'],['nazir','נזיר'],['sotah','סוטה'],['gittin','גיטין'],['kiddushin','קידושין'],['bava-kamma','בבא קמא'],['bava-metzia','בבא מציעא'],['bava-batra','בבא בתרא'],['sanhedrin','סנהדרין'],['makkot','מכות'],['shevuot','שבועות'],['avodah-zarah','עבודה זרה'],['horayot','הוריות'],['zevachim','זבחים'],['menachot','מנחות'],['chullin','חולין'],['bekhorot','בכורות'],['arakhin','ערכין'],['temurah','תמורה'],['keritot','כריתות'],['meilah','מעילה'],['tamid','תמיד'],['niddah','נדה']];
const SHAS_I = {}, HE_I = {};
SHAS.forEach((x, i) => { SHAS_I[x[0]] = i; });
SHAS.map((x) => x[1]).sort((a, b) => a.localeCompare(b, 'he')).forEach((n, i) => { HE_I[n] = i; });
const HE_OF = {}; SHAS.forEach((x) => { HE_OF[x[0]] = x[1]; });
/* ערך מספרי אמיתי של ציון דף (ב, ג ... י, יא ... ק, קא), ועמוד ב אחרי עמוד א */
function dafNum(d) {
  const V = { 'א': 1, 'ב': 2, 'ג': 3, 'ד': 4, 'ה': 5, 'ו': 6, 'ז': 7, 'ח': 8, 'ט': 9, 'י': 10, 'כ': 20, 'ל': 30, 'מ': 40, 'נ': 50, 'ס': 60, 'ע': 70, 'פ': 80, 'צ': 90, 'ק': 100, 'ר': 200, 'ש': 300, 'ת': 400 };
  const t = String(d || '').trim(); let n = 0;
  for (const c of t.replace(/[.:"'׳״]/g, '')) n += V[c] || 0;
  return n ? n * 2 + (t.endsWith(':') ? 1 : 0) : 0;
}
function locCmp(ord) {
  return (a, b) => {
    const ia = ord === 'shas' ? (SHAS_I[a.slug] ?? 99) : (HE_I[HE_OF[a.slug]] ?? 99);
    const ib = ord === 'shas' ? (SHAS_I[b.slug] ?? 99) : (HE_I[HE_OF[b.slug]] ?? 99);
    return (ia - ib) || ((dafNum(a.d) || 99999) - (dafNum(b.d) || 99999)) || ((a.po || 0) - (b.po || 0)) || (a.t - b.t);
  };
}
function sgMeta(rec) {
  const m = {
    st: rec.st, slug: rec.slug, pid: rec.pid || '', tr: rec.tr ? 1 : 0,
    d: rec.daf || '', ty: rec.type || 'nusach', up: rec.up ? 1 : 0, un: rec.seen === 0 ? 1 : 0,
    v: (rec.ver = (rec.ver || 0) + 1), nm: (rec.name || '').slice(0, 24),
    n: (rec.note || '').slice(0, 90), w: (rec.was || '').slice(0, 50), mn: rec.mnew ? 1 : 0,
    sk: rec.sk || '', po: posOf(rec.k),
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
  const rows = [], mine = await pidSet(env, pid);
  for (const k of await listAll(env, 'sg:')) {
    const m = k.metadata;
    if (!m || !mine.has(m.pid) || m.st === 'deleted') continue;
    rows.push({ id: k.name.slice(3), t: keyT(k.name), st: m.st, slug: m.slug, daf: m.d || '', type: m.ty || '',
                up: m.up || 0, un: m.un || 0, v: m.v || 0, n: m.n || '', w: m.w || '', mn: m.mn || 0, sk: m.sk || '' });
  }
  rows.sort((a, b) => b.t - a.t);
  return json({ ok: true, rows, unseen: rows.filter((x) => x.un).length });
}
async function mineBatch(req, env) {
  let b;
  try { b = await req.json(); } catch (e) { return bad('גוף הבקשה אינו JSON'); }
  const pid = str(b.pid, 20), pt = req.headers.get('x-proposer') || '';
  if (!(await proposerOk(env, pid, pt))) return bad('אין הרשאה', 401);
  const out = [], mine = await pidSet(env, pid);
  for (const id of (Array.isArray(b.ids) ? b.ids : []).slice(0, 40)) {
    const rec = await env.STORE.get('sg:' + str(id, 80), 'json');
    if (rec && mine.has(rec.pid)) out.push(rec);
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
  if (!rec || !(await pidSet(env, pid)).has(rec.pid)) return bad('ההצעה לא נמצאה', 404);
  /* מחיקה רכה: ההצעה נשמרת (ארכיון "נמחקו על ידי המציע" אצל המנהל), נעלמת מן
     התצוגות, וניתן לבטל. מחיקה חוזרת של הצעה שכבר נמחקה היא הצלחה, לא שגיאה. */
  if (what === 'undelete') {
    if (rec.st !== 'deleted') return json({ ok: true, rec });
    rec.st = 'pending'; delete rec.deletedAt;
    await putSg(env, rec);
    return json({ ok: true, rec });
  }
  if (what === 'delete' && rec.st === 'deleted') return json({ ok: true });
  if (what === 'reply') {
    const text = str(b.text, 600).trim();
    if (!text || LINK.test(text)) return bad('תשובה ריקה, או שיש בה קישור');
    rec.thread = (rec.thread || []).concat([{ from: 'p', txt: text, t: Date.now() }]).slice(-30);
    rec.mnew = 1;                      /* יש הודעה חדשה למנהל */
    await putSg(env, rec);
    return json({ ok: true, rec });
  }
  if (rec.st !== 'pending') return bad('אחרי שההצעה טופלה אי אפשר לשנות אותה. שלח הצעה חדשה');
  if (what === 'delete') { rec.st = 'deleted'; rec.deletedAt = Date.now(); await putSg(env, rec); return json({ ok: true }); }
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

/* שיעורי יוטיוב (מנה 4, 7.10.2026): קריאה פתוחה לכולם, כתיבה למנהל בלבד.
   כל שיעור משויך למסכת ולדף או לטווח דפים. הכותרת והתמונה נשלפות מ-oEmbed. */
function ytId(u) {
  const m = String(u || '').match(/(?:youtu\.be\/|v=|\/embed\/|\/shorts\/|\/live\/)([A-Za-z0-9_-]{11})/) || String(u || '').match(/^([A-Za-z0-9_-]{11})$/);
  return m ? m[1] : '';
}
async function lessons(req, env, method) {
  if (method === 'GET') {
    const out = [];
    for (const k of await listAll(env, 'ls:')) {
      const v = await env.STORE.get(k.name, 'json');
      if (v) out.push(v);
    }
    out.sort((a, b) => (a.slug + a.from).localeCompare(b.slug + b.from) || a.t - b.t);
    return json({ ok: true, items: out });
  }
  if (!(await isAdmin(req, env))) return bad('אין הרשאה', 401);
  let b;
  try { b = await req.json(); } catch (e) { return bad('גוף הבקשה אינו JSON'); }
  const op = str(b.op, 10);
  if (op === 'add') {
    const vid = ytId(b.url);
    if (!vid) return bad('הקישור אינו קישור יוטיוב תקין');
    const slug = str(b.slug, 30).trim();
    const from = str(b.from, 12).trim();
    if (!slug || !from) return bad('חסרה מסכת או דף');
    const to = str(b.to, 12).trim() || from;
    let title = str(b.title, 200).trim(), author = '', thumb = 'https://i.ytimg.com/vi/' + vid + '/hqdefault.jpg';
    try {
      const r = await fetch('https://www.youtube.com/oembed?format=json&url=' + encodeURIComponent('https://www.youtube.com/watch?v=' + vid));
      if (r.ok) {
        const j = await r.json();
        if (!title) title = str(j.title, 200);
        author = str(j.author_name, 80);
        if (j.thumbnail_url) thumb = str(j.thumbnail_url, 300);
      }
    } catch (e) { /* בלי כותרת אוטומטית - ממשיכים עם מה שיש */ }
    if (!title) title = 'שיעור על ' + slug + ' ' + from;
    const id = rid();
    const rec = { id, t: Date.now(), vid, title, author, thumb, slug, from, to, mas: str(b.mas, 40) };
    await env.STORE.put('ls:' + id, JSON.stringify(rec));
    return json({ ok: true, id, item: rec });
  }
  const id = str(b.id, 40);
  if (op === 'del') {
    if (!id) return bad('חסר מזהה');
    await env.STORE.delete('ls:' + id);
    return json({ ok: true });
  }
  return bad('פעולה לא מוכרת');
}

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
    k: str(b.k, 48), ctx: { b: str(b.ctx && b.ctx.b, 60), a: str(b.ctx && b.ctx.a, 60) },
    was: str(b.was), note, name: str(b.name, 80).trim(), t, st: 'pending',
    type, pid, thread: [], seen: 1, tr: (await isTrusted(env, pid)) ? 1 : 0,
  };
  if (from) rec.from = from;
  /* הצעה מן העורך: הפעולה המדויקת (איזה טווח, מאיזה סגנון לאיזה סגנון, או שינוי
     מבנה) נשמרת כרשומת עריכה ולא כטקסט חופשי, כדי שתחול אוטומטית באישור */
  if (b.edit && typeof b.edit === 'object' && (b.edit.k || b.edit.op === 'struct')) {
    rec.edit = cleanEdit(Object.assign({}, b.edit, { t: +b.edit.t || t }));
    rec.sk = SKINDS.indexOf(b.sk) > -1 ? b.sk : (rec.edit.op === 'struct' ? 'struct' : 'text');
    rec.mnew = 0;
  }
  /* עדכון של הצעה ממתינה של אותו מציע על אותו מקום (המציע המשיך לערוך באותה שורה):
     אותו פריט בתור, עם הגרסה הקודמת בהיסטוריה, ולא כפילות */
  if (pid && b.upd && rec.edit) {
    const old = await env.STORE.get('sg:' + str(b.upd, 80), 'json');
    if (old && old.pid === pid && old.st === 'pending' && old.edit) {
      old.vers = (old.vers || []).concat([{ note: old.note, type: old.type, t: old.edited || old.t }]).slice(-30);
      old.note = note; old.type = type; old.sk = rec.sk; old.edit = rec.edit; old.was = rec.was;
      old.ctx = rec.ctx; old.edited = t; old.up = 1;
      await putSg(env, old);
      return json({ ok: true, id: old.id, updated: 1 });
    }
  }
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
  const skF = q.get('sk') || '', upF = q.get('up') === '1', page = Math.max(0, parseInt(q.get('page') || '0', 10) || 0);
  const size = Math.min(40, Math.max(5, parseInt(q.get('size') || '30', 10) || 30));
  const keys = await listAll(env, 'sg:');
  const counts = {}, props = {};
  const want = [], legacy = [];
  if (q.get('deleted') === '1') {      /* ארכיון "נמחקו על ידי המציע" */
    const del = keys.filter((k) => k.metadata && k.metadata.st === 'deleted').sort((a, b) => keyT(b.name) - keyT(a.name)).slice(0, 60);
    const items = [];
    for (const k of del) { const v = await env.STORE.get(k.name, 'json'); if (v && v.st === 'deleted') items.push(v); }
    return json({ ok: true, items, total: del.length });
  }
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
    if (skF && m.sk !== skF) continue;
    if (upF && !m.up) continue;
    want.push({ name: k.name, tr: m.tr ? 1 : 0, t: keyT(k.name), slug: m.slug, d: m.d, po: m.po });
  }
  for (const name of legacy.slice(0, 30)) {
    const rec = await env.STORE.get(name, 'json');
    if (rec) await putSg(env, rec);
  }
  for (const name of legacy) want.push({ name, tr: 0, t: keyT(name) });
  const ord = q.get('ord') || '';
  if (ord === 'loc' || ord === 'shas') want.sort(locCmp(ord));
  else want.sort((a, b) => (b.tr - a.tr) || (a.t - b.t));
  const slice = want.slice(page * size, page * size + size);
  const items = [];
  for (const w of slice) {
    const v = await env.STORE.get(w.name, 'json');
    if (v && v.st === 'pending') items.push(v);     /* רשימת המפתחות מתעכבת עד דקה: הרשומה עצמה קובעת */
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
  for (const f of ['was', 'now', 'wasH', 'nowH', 'daf', 'ps', 'psw', 'wasP', 'by', 'sg', 'op', 'kind', 'ins', 'where', 'bt', 'bh', 'bp']) {
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
  out.proposers = {}; out.learning = {}; out.devices = {};
  for (const k of await listAll(env, 'pr:')) { const v = await env.STORE.get(k.name, 'json'); if (v) out.proposers[k.name.slice(3)] = v; }
  for (const k of await listAll(env, 'ln:')) { const v = await env.STORE.get(k.name, 'json'); if (v) out.learning[k.name.slice(3)] = v; }
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


/* ------------------------------------------------------------ בחן את עצמך, תארים ולוח מובילים (מנה 3, 7.10.2026)
   הניקוד מחושב במכשיר הלומד (חזרות מרווחות); כאן נשמר רק סיכום אנונימי לפי pid שהוא
   מזהה אקראי של המכשיר (בלי שם, בלי דוא"ל). לוח המובילים מציג כינוי בלבד, ורק למי שהסכים.
   סף התארים נרשם בחוקה ומשוכפל בלקוח (tools/lamed/quiz.js). */
const QZ_T_ALL = [500, 3000, 10000, 30000, 100000];
const QZ_T_M = [300, 1500, 5000, 15000, 40000];
const QZ_DAYCAP = 5000;                     /* תקרת ניקוד ליום: מונעת זיוף גס, אינה פוגעת בלומד אמיתי */
const nickOk = (v) => {
  let t = String(v || '').normalize('NFC').replace(/[^֐-׿a-zA-Z0-9 '"\-]/g, '').replace(/\s+/g, ' ').trim().slice(0, 16);
  if (/https?|www|@|\.com/i.test(String(v || ''))) t = '';
  return t;
};
function ilWeek(t) {                        /* יום ראשון של השבוע, לפי שעון ישראל */
  const d = new Date(ilDay(t) + 'T12:00:00Z');
  d.setUTCDate(d.getUTCDate() - d.getUTCDay());
  return d.toISOString().slice(0, 10);
}
async function qzScore(req, env) {
  let b;
  try { b = await req.json(); } catch (e) { return bad('גוף הבקשה אינו JSON'); }
  const pid = str(b.pid, 20), pt = req.headers.get('x-proposer') || '';
  if (!/^[a-z0-9]{8,20}$/.test(pid) || !pt) return bad('אין הרשאה', 401);
  if (!(await ensureProposer(env, pid, str(pt, 80), ''))) return bad('הזהות במכשיר אינה תואמת', 401);
  const ip = req.headers.get('cf-connecting-ip') || '0';
  if (burstHit(ip)) return bad('מהיר מדי. נסה שוב בעוד רגע', 429);
  const old = (await env.STORE.get('qz:' + pid, 'json')) || { t: 0, base: 0, day: '', wk: '', wp: 0 };
  const today = ilDay(Date.now()), wk = ilWeek(Date.now());
  const rec = { ...old };
  if (rec.day !== today) { rec.day = today; rec.base = old.t || 0; }
  if (rec.wk !== wk) { rec.wk = wk; rec.wp = 0; }
  let total = Math.max(0, Math.min(5000000, Math.round(+b.total || 0)));
  total = Math.min(total, rec.base + QZ_DAYCAP);       /* עלייה חדה ביום אחד נחתכת */
  total = Math.max(total, old.t || 0);                  /* הניקוד אינו יורד */
  const byM = {};
  for (const [k, v] of Object.entries(b.byM || {}).slice(0, 60)) if (slugOk(k)) byM[k] = Math.max(0, Math.min(2000000, Math.round(+v || 0)));
  rec.t = total; rec.m = byM;
  const wpIn = Math.max(0, Math.round(+b.wp || 0));
  rec.wp = Math.max(rec.wp, Math.min(wpIn, QZ_DAYCAP * 7));
  rec.o = b.optin ? 1 : 0;
  rec.n = rec.o ? (nickOk(b.nick) || '') : '';
  rec.u = Date.now();
  const mstr = Object.entries(byM).filter((x) => x[1] > 0).map((x) => x[0] + ':' + x[1]).join(',').slice(0, 700);
  await env.STORE.put('qz:' + pid, JSON.stringify(rec), { metadata: { t: rec.t, o: rec.o, n: rec.n, wk: rec.wk, wp: rec.wp, m: mstr, u: rec.u } });
  return json({ ok: true, total: rec.t, week: rec.wp });
}
const lvlOf = (pts, T) => { let l = 0; T.forEach((x, i) => { if (pts >= x) l = i + 1; }); return l; };
async function qzBoard(req, env, url) {
  const slug = slugOk(url.searchParams.get('s') || '') ? url.searchParams.get('s') : '';
  const pid = url.searchParams.get('pid') || '';
  const wk = ilWeek(Date.now());
  const keys = await listAll(env, 'qz:');
  const all = [], weekly = [];
  const cAll = [0, 0, 0, 0, 0, 0], cM = [0, 0, 0, 0, 0, 0];
  let me = null;
  let n = 0;
  for (const k of keys) {
    const m = k.metadata || {};
    if (!m.t) continue;
    n++;
    const id = k.name.slice(3);
    const l = lvlOf(m.t, QZ_T_ALL);
    for (let i = 1; i <= l; i++) cAll[i]++;
    let mp = 0;
    if (slug && m.m) { for (const part of String(m.m).split(',')) { const [s2, v] = part.split(':'); if (s2 === slug) mp = +v || 0; } }
    if (slug) { const lm = lvlOf(mp, QZ_T_M); for (let i = 1; i <= lm; i++) cM[i]++; }
    if (m.o) {
      const nm = m.n || ('לומד אנונימי ' + (parseInt(id.slice(0, 4), 36) % 9000 + 1000));
      all.push({ id, n: nm, p: m.t });
      if (m.wk === wk && m.wp > 0) weekly.push({ id, n: nm, p: m.wp });
    }
    if (pid && id === pid) me = { t: m.t, wp: m.wk === wk ? (m.wp || 0) : 0, mp, o: m.o ? 1 : 0, n: m.n || '' };
  }
  all.sort((a, b) => b.p - a.p); weekly.sort((a, b) => b.p - a.p);
  const pub = (x) => x.slice(0, 20).map((r) => ({ n: r.n, p: r.p, me: pid && r.id === pid ? 1 : 0 }));
  const rank = (arr) => (pid ? (arr.findIndex((r) => r.id === pid) + 1) || 0 : 0);
  return json({ ok: true, learners: n, week: pub(weekly), all: pub(all), counts: { all: cAll, m: cM }, rank: { week: rank(weekly), all: rank(all) }, me });
}

/* ---- תארי המציעים: לפי הצעות שאושרו, עם משקל לאיכות ---- */
const PR_VET = 15, PR_TOP5 = 40, PR_TOP3 = 80;
function prTitle(pts, rank) {
  if (rank > 0 && rank <= 3 && pts >= PR_TOP3) return 'משלושת המגיהים הגדולים';
  if (rank > 0 && rank <= 5 && pts >= PR_TOP5) return 'מחמשת המגיהים הגדולים';
  if (pts >= PR_VET) return 'מגיה ותיק';
  if (pts >= 1) return 'מגיה';
  return '';
}
async function qzProposers(req, env, url) {
  const pid = url.searchParams.get('pid') || '', pt = req.headers.get('x-proposer') || '';
  const mineOk = pid && pt && (await proposerOk(env, pid, pt));
  const agg = {}, first = {};
  for (const k of await listAll(env, 'sg:')) {
    const m = k.metadata || {};
    if (!m.pid) continue;
    const a = agg[m.pid] || (agg[m.pid] = { ok: 0, ed: 0, no: 0 });
    if (m.st === 'accepted') a.ok++;
    else if (m.st === 'edited') a.ed++;
    else if (m.st === 'rejected') a.no++;
    if ((m.st === 'accepted' || m.st === 'edited') && m.slug) {
      const t = keyT(k.name);
      if (!first[m.slug] || t < first[m.slug].t) first[m.slug] = { t, pid: m.pid };
    }
  }
  const pts = (a) => {
    const good = a.ok + a.ed * 0.8, dec = a.ok + a.ed + a.no;
    const rate = dec >= 5 ? (a.ok + a.ed) / dec : 1;
    return Math.round(good * (0.6 + 0.4 * rate) * 10) / 10;
  };
  const rows = Object.entries(agg).map(([id, a]) => ({ id, p: pts(a), a })).filter((r) => r.p > 0).sort((x, y) => y.p - x.p);
  const nicks = {};
  for (const k of await listAll(env, 'qz:')) { const m = k.metadata || {}; if (m.o && m.n) nicks[k.name.slice(3)] = m.n; }
  const nm = (id) => nicks[id] || 'מגיה אנונימי';
  rows.forEach((r, i) => { r.rank = i + 1; r.title = prTitle(r.p, r.rank); });
  const firsts = Object.entries(first).map(([s, v]) => ({ s, n: nm(v.pid), me: pid && v.pid === pid ? 1 : 0 }));
  let me = null;
  if (mineOk) {
    const a = agg[pid] || { ok: 0, ed: 0, no: 0 }, r = rows.find((x) => x.id === pid);
    const p = pts(a), rank = r ? r.rank : 0, title = prTitle(p, rank);
    let next = null;
    if (title === '') next = { title: 'מגיה', need: Math.max(0, 1 - p) };
    else if (title === 'מגיה') next = { title: 'מגיה ותיק', need: Math.round((PR_VET - p) * 10) / 10 };
    else if (title === 'מגיה ותיק') next = { title: 'מחמשת המגיהים הגדולים', need: Math.max(0, Math.round((PR_TOP5 - p) * 10) / 10), rank: 5 };
    else if (title === 'מחמשת המגיהים הגדולים') next = { title: 'משלושת המגיהים הגדולים', need: Math.max(0, Math.round((PR_TOP3 - p) * 10) / 10), rank: 3 };
    me = { p, rank, title, ok: a.ok, ed: a.ed, no: a.no, next, firstIn: firsts.filter((f) => f.me).map((f) => f.s) };
  }
  return json({ ok: true, top: rows.slice(0, 10).map((r) => ({ n: nm(r.id), p: r.p, title: r.title, me: pid && r.id === pid ? 1 : 0 })), firsts, me,
                rules: { vet: PR_VET, top5: PR_TOP5, top3: PR_TOP3 } });
}

/* ---- "לומדים כעת": ספירה אנונימית של מכשירים פעילים ב-6 הדקות האחרונות.
   מפתח אחד במחסן, וכתיבה אליו לא יותר מפעם ב-150 שניות (מגבלת הכתיבות בתוכנית החינמית:
   1000 ליום). פעימות שבין כתיבה לכתיבה נקלטות בכתיבה הבאה. אין שם, אין IP, אין pid. */
const ON_WIN = 6 * 60000, ON_GAP = 150000;
async function lnOnline(req, env, url) {
  const now = Date.now();
  const rec = (await env.STORE.get('on:all', 'json')) || { w: 0, a: {} };
  let s = '';
  if (req.method === 'POST') {
    if (BOT.test(req.headers.get('user-agent') || '')) return json({ ok: true, skipped: 1 });
    let b = {};
    try { b = await req.json(); } catch (e) { return bad('גוף הבקשה אינו JSON'); }
    s = slugOk(b.s || '') ? b.s : '';
    const aid = /^[a-z0-9]{8,16}$/.test(b.aid || '') ? b.aid : '';
    if (aid) {
      rec.a[aid] = [now, s];
      if (now - rec.w >= ON_GAP) {
        for (const k of Object.keys(rec.a)) if (now - rec.a[k][0] > ON_WIN) delete rec.a[k];
        const ks = Object.keys(rec.a);
        if (ks.length > 3000) for (const k of ks.slice(0, ks.length - 3000)) delete rec.a[k];
        rec.w = now;
        await env.STORE.put('on:all', JSON.stringify(rec), { expirationTtl: 3600 });
      }
    }
  } else s = slugOk(url.searchParams.get('s') || '') ? url.searchParams.get('s') : '';
  let n = 0, ns = 0;
  for (const v of Object.values(rec.a)) if (now - v[0] <= ON_WIN) { n++; if (s && v[1] === s) ns++; }
  return json({ ok: true, n, s: ns });
}

/* ---- שאלות טיוטה (שנוצרו במודל): הלומד רואה רק אחרי אישור המנהל ---- */
async function qzDec(req, env, url) {
  if (req.method === 'GET') {
    const slug = url.searchParams.get('s') || '';
    if (!slugOk(slug)) return bad('מסכת לא תקינה');
    const rec = (await env.STORE.get('qd:' + slug, 'json')) || {};
    const admin = await isAdmin(req, env);
    const out = {};
    for (const [id, v] of Object.entries(rec)) if (admin || v.st === 'ok') out[id] = admin ? v : { st: 'ok', e: v.e || null };
    return json({ ok: true, dec: out });
  }
  if (!(await isAdmin(req, env))) return bad('אין הרשאה', 401);
  let b;
  try { b = await req.json(); } catch (e) { return bad('גוף הבקשה אינו JSON'); }
  const slug = str(b.s, 30), id = str(b.id, 60), st = str(b.st, 4);
  if (!slugOk(slug) || !id || ['ok', 'no', ''].indexOf(st) < 0) return bad('הכרעה לא תקינה');
  const rec = (await env.STORE.get('qd:' + slug, 'json')) || {};
  if (!st) delete rec[id];
  else {
    const v = { st, t: Date.now() };
    if (st === 'ok' && b.e && Array.isArray(b.e.o) && b.e.o.length === 4) {
      v.e = { q: str(b.e.q, 400), o: b.e.o.map((x) => str(x, 120)), a: Math.max(0, Math.min(3, b.e.a | 0)) };
    }
    rec[id] = v;
  }
  await env.STORE.put('qd:' + slug, JSON.stringify(rec));
  return json({ ok: true });
}

/* ---- צורת הדף (8.10.2026): תמונות מוגנות מ-R2, בכתובת חתומה קצרת-תוקף ----
   /tz/tok מנפיק אסימון ל-5 דקות רק לדף שמגיע מאתר לאוקמי (Referer/Origin).
   /tz/img/<מסכת>/<צד>.<v|z>.webp מגיש את העמוד רק עם אסימון תקף ו-Referer מותר.
   אין נתיב להורדת ה-PDF המלא, ואין בו קוד כזה בכלל. נדרשים: קשירת R2 בשם TZURA והסוד TZ_SECRET. */
const TZ_HOSTS = ['leokmei.com', 'www.leokmei.com', 'localhost', '127.0.0.1'];
function tzHostOk(req) {
  const o = req.headers.get('origin') || req.headers.get('referer') || '';
  try { const h = new URL(o).hostname; return TZ_HOSTS.indexOf(h) >= 0 || /\.github\.io$/.test(h); } catch (e) { return false; }
}
async function tzSign(env, exp) {
  const k = await crypto.subtle.importKey('raw', new TextEncoder().encode(env.TZ_SECRET || ''), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  const sig = await crypto.subtle.sign('HMAC', k, new TextEncoder().encode('tz.' + exp));
  return exp + '.' + btoa(String.fromCharCode(...new Uint8Array(sig))).replace(/[+/=]/g, (c) => ({ '+': '-', '/': '_', '=': '' }[c]));
}
async function tzTok(req, env) {
  if (!env.TZ_SECRET) return bad('לא מוגדר', 503);
  if (!tzHostOk(req)) return bad('אסור', 403);
  return json({ ok: true, t: await tzSign(env, Math.floor(Date.now() / 1000) + 300) });
}
async function tzImg(req, env, url, p) {
  if (!env.TZ_SECRET || !env.TZURA) return bad('לא מוגדר', 503);
  const m = /^\/tz\/img\/([a-z-]{3,30})\/(\d{3}[ab])\.(v|z)\.webp$/.exec(p);
  if (!m) return bad('לא נמצא', 404);
  if (req.headers.get('referer') && !tzHostOk(req)) return bad('אסור', 403);
  const t = url.searchParams.get('t') || '';
  const exp = parseInt(t.split('.')[0], 10);
  if (!(exp > Date.now() / 1000) || (await tzSign(env, exp)) !== t) return bad('פג תוקף', 403);
  const o = await env.TZURA.get(m[1] + '/' + m[2] + '.' + m[3] + '.webp');
  if (!o) return bad('לא נמצא', 404);
  return new Response(o.body, { headers: { ...CORS, 'content-type': 'image/webp', 'cache-control': 'private, max-age=300', 'x-robots-tag': 'noindex' } });
}

/* ------------------------------------------------------------ טקסטי האתר (עיפרון המנהל, 8.10.2026)
   שכבת שינויים לטקסטים קבועים של המעטפת. נשמרת כאן, לא בקבצי האתר, ולכן
   מופיעה תוך דקה בלי בנייה ובלי פרסום. מחיקה רכה בלבד: כל שמירה נרשמת ביומן. */
const TX_CUR = 'tx:cur';
const TX_MAX = 600;
function txClean(v) {
  return String(v == null ? '' : v).normalize('NFC')
    .replace(/<[^>]*>/g, '')
    .replace(/[<>]/g, '')
    .replace(/[‒–—―−]/g, '-')
    .replace(/[‎‏‪-‮⁦-⁩]/g, '')
    .replace(/[ \t]+\n/g, '\n').replace(/\n{3,}/g, '\n\n')
    .trim().slice(0, TX_MAX);
}
const TX_KINDS = ['text', 'title', 'aria-label', 'placeholder', 'alt', 'doctitle', 'metadesc'];
const txKind = (k) => (TX_KINDS.indexOf(k) >= 0 ? k : 'text');
const txKeyOk = (k) => typeof k === 'string' && /^[A-Za-z0-9_.֐-׿-]{3,90}$/.test(k);
async function txLoad(env) {
  try { return JSON.parse((await env.STORE.get(TX_CUR)) || '') || { rev: 0, items: {} }; }
  catch (e) { return { rev: 0, items: {} }; }
}
async function txGet(req, env, url) {
  const cur = await txLoad(env);
  if (url.searchParams.get('full') === '1') {
    if (!(await isAdmin(req, env))) return bad('אין הרשאה', 401);
    const logs = [];
    for (const k of (await listAll(env, 'txlog:')).slice(-400)) {
      const r = await env.STORE.get(k.name);
      if (r) { try { logs.push(JSON.parse(r)); } catch (e) { /* דילוג */ } }
    }
    logs.sort((a, b) => b.ts - a.ts);
    return json({ ok: true, rev: cur.rev, items: cur.items, log: logs });
  }
  const pub = {};
  for (const [k, v] of Object.entries(cur.items)) pub[k] = v.h ? { h: 1, o: v.o, d: v.d || 'text' } : { t: v.t, o: v.o, d: v.d || 'text' };
  return new Response(JSON.stringify({ ok: true, rev: cur.rev, items: pub }), {
    headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'public, max-age=30', ...CORS },
  });
}
async function txSave(req, env) {
  if (!(await isAdmin(req, env))) return bad('אין הרשאה', 401);
  let b;
  try { b = await req.json(); } catch (e) { return bad('גוף הבקשה אינו JSON'); }
  if (!txKeyOk(b.key)) return bad('מפתח טקסט לא תקין');
  const orig = txClean(b.orig);
  const text = txClean(b.text);
  const hide = b.hide === true;
  if (!text && !hide) return bad('הטקסט ריק. כדי להסתיר אותו יש לאשר הסתרה', 422);
  const cur = await txLoad(env);
  const prev = cur.items[b.key] || null;
  const before = prev ? (prev.h ? '' : prev.t) : orig;
  if (!hide && text === (prev ? prev.o : orig)) {
    delete cur.items[b.key];
  } else {
    if (Object.keys(cur.items).length > 3000) return bad('יותר מדי שינויי טקסט', 413);
    cur.items[b.key] = { t: hide ? '' : text, h: hide ? 1 : 0, o: prev ? prev.o : orig, d: txKind(b.kind), s: str(b.scope, 40), ts: Date.now() };
  }
  cur.rev = (cur.rev || 0) + 1;
  await env.STORE.put(TX_CUR, JSON.stringify(cur));
  const ent = { id: rid(), ts: Date.now(), key: b.key, scope: str(b.scope, 40), before, after: hide ? '' : text, hide, orig: prev ? prev.o : orig, act: 'save' };
  await env.STORE.put('txlog:' + String(ent.ts).padStart(14, '0') + ':' + ent.id, JSON.stringify(ent));
  return json({ ok: true, rev: cur.rev, text: hide ? '' : text, cleaned: text !== String(b.text == null ? '' : b.text).trim() });
}
async function txRevert(req, env) {
  if (!(await isAdmin(req, env))) return bad('אין הרשאה', 401);
  let b;
  try { b = await req.json(); } catch (e) { return bad('גוף הבקשה אינו JSON'); }
  if (!txKeyOk(b.key)) return bad('מפתח טקסט לא תקין');
  const cur = await txLoad(env);
  const prev = cur.items[b.key];
  if (!prev) return json({ ok: true, rev: cur.rev, none: true });
  delete cur.items[b.key];
  cur.rev = (cur.rev || 0) + 1;
  await env.STORE.put(TX_CUR, JSON.stringify(cur));
  const ent = { id: rid(), ts: Date.now(), key: b.key, scope: prev.s || '', before: prev.h ? '' : prev.t, after: prev.o, hide: false, orig: prev.o, act: 'revert' };
  await env.STORE.put('txlog:' + String(ent.ts).padStart(14, '0') + ':' + ent.id, JSON.stringify(ent));
  return json({ ok: true, rev: cur.rev, orig: prev.o });
}

/* ------------------------------------------------------------ נתוני גלישה (מנה 9.10.2026)
   העתקה של מערכת הספירה האנונימית של ממלכת הזוהר (zstats/hit.js ו-summary.js) ללאוקמי גירסא.
   האחסון הוא D1 נפרד (leokmei-stats, בלי עלות): כל צפייה היא הגדלת מונה, ולא כתיבת רשומה שלמה ל-KV,
   שהמכסה היומית שלו קטנה. בלי כתובת, בלי דפדפן ובלי עוגייה: האיזור נלקח מ-req.cf וכתובת ה-IP אינה נשמרת.
   POST /stats/hit      ציבורי. גוף (text/plain עם JSON): {p, s, t, e, n, r, d}
   GET  /stats/summary  מנהל בלבד (x-admin-key): ?days=30, באותו מבנה של הזוהר. */
const ST_MAX = { pages: 200, entry: 200, geo: 300, refs: 100, hours: 24, dev: 4 };
const ST_MAX_SIDS = 4000;
let stReady = false;
async function stEnsure(db) {
  if (stReady) return;
  await db.batch([
    db.prepare('CREATE TABLE IF NOT EXISTS zs_c (day TEXT NOT NULL, f TEXT NOT NULL, k TEXT NOT NULL, n INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (day, f, k))'),
    db.prepare('CREATE TABLE IF NOT EXISTS zs_s (day TEXT NOT NULL, sid TEXT NOT NULL, PRIMARY KEY (day, sid))'),
  ]);
  stReady = true;
}
function stBump(db, day, f, k, delta = 1) {
  const cap = ST_MAX[f];
  if (!cap) return db.prepare('INSERT INTO zs_c (day, f, k, n) VALUES (?1, ?2, ?3, ?4) ON CONFLICT(day, f, k) DO UPDATE SET n = n + ?4').bind(day, f, k, delta);
  return db.prepare(
    'INSERT INTO zs_c (day, f, k, n) SELECT ?1, ?2, ?3, ?4 WHERE EXISTS (SELECT 1 FROM zs_c WHERE day = ?1 AND f = ?2 AND k = ?3) OR (SELECT COUNT(*) FROM zs_c WHERE day = ?1 AND f = ?2) < ?5 ' +
    'ON CONFLICT(day, f, k) DO UPDATE SET n = n + ?4'
  ).bind(day, f, k, delta, cap);
}
function stIlHour() {
  try {
    return parseInt(new Intl.DateTimeFormat('en-US', { timeZone: 'Asia/Jerusalem', hour: 'numeric', hour12: false }).format(new Date()), 10) % 24;
  } catch (e) { return (new Date().getUTCHours() + 3) % 24; }
}
async function statsHit(req, env) {
  if (!env.LSTATS) return json({ ok: false, error: 'no-db' }, 503);
  let b;
  try { b = JSON.parse(await req.text()); } catch (e) { return bad('גוף הבקשה אינו JSON'); }
  if (!b || typeof b !== 'object') return bad('גוף הבקשה אינו JSON');
  const page = String(b.p || '').slice(0, 80);
  const sid = String(b.s || '').replace(/[^A-Za-z0-9]/g, '').slice(0, 24);
  const secs = Math.max(0, Math.min(7200, parseInt(b.t, 10) || 0));
  if (!sid || !page) return bad('חסר');
  const db = env.LSTATS;
  await stEnsure(db);
  const day = new Date().toISOString().slice(0, 10);
  const st = [];
  if (secs) {
    st.push(stBump(db, day, 'secs', '', secs));
  } else {
    st.push(stBump(db, day, 'views', '', 1));
    st.push(db.prepare('INSERT OR IGNORE INTO zs_s (day, sid) SELECT ?1, ?2 WHERE (SELECT COUNT(*) FROM zs_s WHERE day = ?1) < ?3').bind(day, sid, ST_MAX_SIDS));
    st.push(stBump(db, day, 'pages', page));
    st.push(stBump(db, day, 'hours', String(stIlHour())));
    const cf = req.cf || {};
    const country = String(cf.country || '').slice(0, 2).toUpperCase();
    if (country) st.push(stBump(db, day, 'geo', (country === 'IL' && cf.city) ? 'IL:' + String(cf.city).slice(0, 40) : country));
    if (b.e) {
      if (b.n) st.push(stBump(db, day, 'newv', '', 1));
      if (b.d === 'm' || b.d === 'd') st.push(stBump(db, day, 'dev', b.d));
      const ref = String(b.r || '').toLowerCase().replace(/^www\./, '').replace(/[^a-z0-9.\-]/g, '').slice(0, 60);
      st.push(stBump(db, day, 'refs', ref || 'direct'));
      st.push(stBump(db, day, 'entry', page));
    }
  }
  await db.batch(st);
  return json({ ok: true });
}
async function statsSummary(req, env, url) {
  if (!(await isAdmin(req, env))) return json({ error: 'unauthorized' }, 403);
  if (!env.LSTATS) return json({ error: 'no-db' }, 503);
  const days = Math.max(1, Math.min(400, parseInt(url.searchParams.get('days'), 10) || 30));
  const db = env.LSTATS;
  await stEnsure(db);
  const list = [];
  const now = Date.now();
  for (let i = 0; i < days; i++) list.push(new Date(now - i * 86400000).toISOString().slice(0, 10));
  const since = list[list.length - 1];
  const rows = (await db.prepare('SELECT day, f, k, n FROM zs_c WHERE day >= ?1').bind(since).all()).results || [];
  const sids = (await db.prepare('SELECT day, COUNT(*) AS c FROM zs_s WHERE day >= ?1 GROUP BY day').bind(since).all()).results || [];
  const by = {};
  list.forEach((d) => { by[d] = { day: d, views: 0, visitors: 0, minutes: 0, pages: {}, newv: 0, geo: {}, hours: {}, dev: {}, refs: {}, entry: {}, _secs: 0 }; });
  rows.forEach((r) => {
    const o = by[r.day]; if (!o) return;
    if (r.f === 'views') o.views = r.n;
    else if (r.f === 'secs') o._secs = r.n;
    else if (r.f === 'newv') o.newv = r.n;
    else if (o[r.f] && typeof o[r.f] === 'object') o[r.f][r.k] = r.n;
  });
  sids.forEach((r) => { if (by[r.day]) by[r.day].visitors = r.c; });
  return json({ days: list.map((d) => { const o = by[d]; o.minutes = Math.round(o._secs / 60); delete o._secs; return o; }) });
}

/* ------------------------------------------------------------ נתוני הנבחנים (11.10.2026)
   בעל הפרויקט ביקש לדעת מי נבחן, על מה ואיך. כל סבב שהסתיים (או נקטע כשהלומד עזב)
   נרשם כשורה אחת במסד הגלישה (D1 LSTATS), ושאלה-שאלה בטבלה נפרדת. "מי" = מזהה
   המכשיר האקראי (pid) והכינוי שהלומד בחר בעצמו, אם בחר. אין שם, אין דוא"ל, אין IP.
   הקריאה: למנהל בלבד, בדף admin-quiz.html. */
let qzReady = false;
async function qzEnsure(db) {
  if (qzReady) return;
  await db.batch([
    db.prepare('CREATE TABLE IF NOT EXISTS qz_run (rid TEXT PRIMARY KEY, t INTEGER NOT NULL, day TEXT NOT NULL, pid TEXT NOT NULL, nick TEXT, persona TEXT, mode TEXT, slugs TEXT, pereks TEXT, n INTEGER, ok INTEGER, bad INTEGER, pts INTEGER, ms INTEGER, aids INTEGER, best INTEGER, done INTEGER, dev TEXT, city TEXT)'),
    db.prepare('CREATE INDEX IF NOT EXISTS qz_run_t ON qz_run (t)'),
    db.prepare('CREATE INDEX IF NOT EXISTS qz_run_pid ON qz_run (pid)'),
    db.prepare('CREATE TABLE IF NOT EXISTS qz_ans (rid TEXT NOT NULL, k INTEGER NOT NULL, qid TEXT NOT NULL, slug TEXT, lv INTEGER, ok INTEGER, ms INTEGER, t INTEGER, PRIMARY KEY (rid, k))'),
    db.prepare('CREATE INDEX IF NOT EXISTS qz_ans_q ON qz_ans (qid)'),
  ]);
  qzReady = true;
}
async function qzLog(req, env) {
  if (!env.LSTATS) return json({ ok: false, error: 'no-db' }, 503);
  if (BOT.test(req.headers.get('user-agent') || '')) return json({ ok: true, skipped: 1 });
  let b;
  try { b = JSON.parse(await req.text()); } catch (e) { return bad('גוף הבקשה אינו JSON'); }
  if (!b || typeof b !== 'object') return bad('גוף הבקשה אינו JSON');
  const ip = req.headers.get('cf-connecting-ip') || '0';
  if (burstHit(ip)) return bad('מהיר מדי', 429);
  const pid = str(b.pid, 20), rid0 = str(b.rid, 40);
  if (!/^[a-z0-9]{8,20}$/.test(pid) || !/^[a-z0-9-]{6,40}$/.test(rid0)) return bad('חסר מזהה');
  const rid = pid + ':' + rid0;
  const num = (v, hi) => Math.max(0, Math.min(hi, Math.round(+v || 0)));
  const ans = (Array.isArray(b.a) ? b.a : []).slice(0, 120).map((x, k) => ({
    k, qid: str(String(x && x.q != null ? x.q : ''), 40), slug: slugOk(x && x.s) ? x.s : '', lv: num(x && x.lv, 9), ok: x && x.ok ? 1 : 0, ms: num(x && x.ms, 600000), t: num(x && x.t, 4102444800000),
  })).filter((x) => x.qid);
  const slugs = [...new Set((Array.isArray(b.slugs) ? b.slugs : []).filter(slugOk).concat(ans.map((x) => x.slug).filter(Boolean)))].slice(0, 12).join(',');
  const pereks = (Array.isArray(b.pereks) ? b.pereks : []).map((x) => str(String(x), 12)).slice(0, 12).join(',');
  const okN = ans.filter((x) => x.ok).length;
  const cf = req.cf || {};
  const city = String(cf.country || '').slice(0, 2).toUpperCase() === 'IL' ? str(String(cf.city || ''), 40) : str(String(cf.country || ''), 2);
  const now = Date.now();
  const db = env.LSTATS;
  await qzEnsure(db);
  const st = [db.prepare(
    'INSERT INTO qz_run (rid, t, day, pid, nick, persona, mode, slugs, pereks, n, ok, bad, pts, ms, aids, best, done, dev, city) VALUES (?1,?2,?3,?4,?5,?6,?7,?8,?9,?10,?11,?12,?13,?14,?15,?16,?17,?18,?19) ' +
    'ON CONFLICT(rid) DO UPDATE SET t=?2, nick=?5, n=?10, ok=?11, bad=?12, pts=?13, ms=?14, aids=?15, best=?16, done=MAX(done, ?17), slugs=?8, pereks=?9'
  ).bind(rid, now, ilDay(now), pid, nickOk(b.nick) || '', /^(naar|bahur|avrech)$/.test(b.persona || '') ? b.persona : '', b.blitz ? 'blitz' : 'regular',
    slugs, pereks, ans.length, okN, ans.length - okN, num(b.pts, 100000), num(b.ms, 7200000), num(b.aids, 200), num(b.best, 200), b.done ? 1 : 0,
    b.dev === 'm' || b.dev === 't' || b.dev === 'd' ? b.dev : '', city)];
  for (const x of ans) st.push(db.prepare('INSERT OR REPLACE INTO qz_ans (rid, k, qid, slug, lv, ok, ms, t) VALUES (?1,?2,?3,?4,?5,?6,?7,?8)').bind(rid, x.k, x.qid, x.slug, x.lv, x.ok, x.ms, x.t || now));
  await db.batch(st);
  return json({ ok: true });
}
async function qzRuns(req, env, url) {
  if (!(await isAdmin(req, env))) return bad('אין הרשאה', 401);
  if (!env.LSTATS) return json({ ok: false, error: 'no-db' }, 503);
  const db = env.LSTATS;
  await qzEnsure(db);
  const days = Math.max(1, Math.min(400, parseInt(url.searchParams.get('days'), 10) || 30));
  const since = Date.now() - days * 86400000;
  const slug = slugOk(url.searchParams.get('s') || '') ? url.searchParams.get('s') : '';
  const pid = /^[a-z0-9]{8,20}$/.test(url.searchParams.get('pid') || '') ? url.searchParams.get('pid') : '';
  const w = 'WHERE r.t >= ?1' + (slug ? " AND (',' || r.slugs || ',') LIKE ?2" : ' AND ?2 = ?2') + (pid ? ' AND r.pid = ?3' : ' AND ?3 = ?3');
  const args = [since, slug ? '%,' + slug + ',%' : '', pid || ''];
  const q = (sql) => db.prepare(sql).bind(...args).all().then((x) => x.results || []);
  const [tot, people, runs, bySlug, byDay, hard] = await Promise.all([
    q('SELECT COUNT(*) AS runs, COUNT(DISTINCT r.pid) AS people, SUM(r.n) AS answers, SUM(r.ok) AS ok, SUM(r.ms) AS ms, SUM(r.done) AS done FROM qz_run r ' + w),
    q('SELECT r.pid, MAX(r.nick) AS nick, MAX(r.persona) AS persona, COUNT(*) AS runs, SUM(r.n) AS answers, SUM(r.ok) AS ok, SUM(r.pts) AS pts, SUM(r.ms) AS ms, MIN(r.t) AS first, MAX(r.t) AS last, GROUP_CONCAT(DISTINCT r.slugs) AS slugs, MAX(r.dev) AS dev, MAX(r.city) AS city FROM qz_run r ' + w + ' GROUP BY r.pid ORDER BY last DESC LIMIT 500'),
    q('SELECT r.rid, r.t, r.pid, r.nick, r.persona, r.mode, r.slugs, r.pereks, r.n, r.ok, r.pts, r.ms, r.aids, r.best, r.done, r.dev, r.city FROM qz_run r ' + w + ' ORDER BY r.t DESC LIMIT 400'),
    q("SELECT a.slug, COUNT(DISTINCT r.pid) AS people, COUNT(DISTINCT r.rid) AS runs, COUNT(*) AS answers, SUM(a.ok) AS ok FROM qz_ans a JOIN qz_run r ON r.rid = a.rid " + w + " AND a.slug != '' GROUP BY a.slug ORDER BY answers DESC"),
    q('SELECT r.day, COUNT(*) AS runs, COUNT(DISTINCT r.pid) AS people, SUM(r.n) AS answers, SUM(r.ok) AS ok FROM qz_run r ' + w + ' GROUP BY r.day ORDER BY r.day'),
    q('SELECT a.qid, MAX(a.slug) AS slug, MAX(a.lv) AS lv, COUNT(*) AS n, SUM(a.ok) AS ok, AVG(a.ms) AS ms FROM qz_ans a JOIN qz_run r ON r.rid = a.rid ' + w + ' GROUP BY a.qid HAVING COUNT(*) >= 3 ORDER BY (1.0 * SUM(a.ok) / COUNT(*)) ASC, n DESC LIMIT 60'),
  ]);
  let answers = [];
  if (pid) answers = (await db.prepare('SELECT a.rid, a.k, a.qid, a.slug, a.lv, a.ok, a.ms, a.t FROM qz_ans a JOIN qz_run r ON r.rid = a.rid WHERE r.pid = ?1 AND r.t >= ?2 ORDER BY a.t DESC LIMIT 1000').bind(pid, since).all()).results || [];
  return json({ ok: true, days, slug, pid, totals: tot[0] || {}, people, runs, bySlug, byDay, hard, answers });
}

export default {
  async fetch(req, env) {
    if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers: CORS });
    const url = new URL(req.url);
    const p = url.pathname.replace(/\/+$/, '') || '/';
    try {
      if (p === '/' || p === '/health') return json({ ok: true, service: 'leokmei-suggest' });
      if (p === '/tz/tok' && req.method === 'GET') return await tzTok(req, env);
      if (p.startsWith('/tz/img/') && req.method === 'GET') return await tzImg(req, env, url, p);
      if (p === '/stats/hit' && req.method === 'POST') return await statsHit(req, env);
      if (p === '/stats/summary' && req.method === 'GET') return await statsSummary(req, env, url);
      if (p === '/tx' && req.method === 'GET') return await txGet(req, env, url);
      if (p === '/tx/save' && req.method === 'POST') return await txSave(req, env);
      if (p === '/tx/revert' && req.method === 'POST') return await txRevert(req, env);
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
      if (p === '/mine/undelete' && req.method === 'POST') return await mineAct(req, env, 'undelete');
      if (p === '/merge-pid' && req.method === 'POST') return await mergePid(req, env);
      if (p === '/mine/reply' && req.method === 'POST') return await mineAct(req, env, 'reply');
      if (p === '/mine/seen' && req.method === 'POST') return await mineAct(req, env, 'seen');
      if (p === '/reply' && req.method === 'POST') return await adminReply(req, env);
      if (p === '/trust' && req.method === 'POST') return await trust(req, env);
      if (p === '/bulk' && req.method === 'POST') return await bulk(req, env);
      if (p === '/journal') return await journal(req, env, req.method);
      if (p === '/notes') return await notes(req, env, req.method);
      if (p === '/lessons') return await lessons(req, env, req.method);
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
      if (p === '/qz/score' && req.method === 'POST') return await qzScore(req, env);
      if (p === '/qz/log' && req.method === 'POST') return await qzLog(req, env);
      if (p === '/qz/runs' && req.method === 'GET') return await qzRuns(req, env, url);
      if (p === '/qz/board' && req.method === 'GET') return await qzBoard(req, env, url);
      if (p === '/qz/proposers' && req.method === 'GET') return await qzProposers(req, env, url);
      if (p === '/qz/dec') return await qzDec(req, env, url);
      if (p === '/ln/online') return await lnOnline(req, env, url);
      return bad('לא נמצא', 404);
    } catch (e) {
      return bad('שגיאה: ' + (e && e.message ? e.message : String(e)), 500);
    }
  },
};
