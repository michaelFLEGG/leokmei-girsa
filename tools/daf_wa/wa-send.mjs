// פרומפט 23 (8.11.2026): השולח של "הדף היומי בווטסאפ" של לאוקמי גירסא.
// הועתק כמו שהוא מן השולח העצמאי של "הזוהר היומי" (ממלכת הזוהר, זוהר-דף-כלים/zyomi/ווטסאפ-עצמאי.mjs, פרומפט 44 ב):
// הווטסאפ של בעל הפרויקט מקושר (פעם אחת, בסריקה בטלפון) כמכשיר נוסף. הקוד רץ בריצת גיטהאב (daf-wa.yml), מתחבר, שולח ומתנתק.
// אין כאן שום סוד: ההרשאה מול השרת היא אסימון OIDC של קובץ ההרצה הזה בלבד (קהל leokmei-daf), ומצב החיבור נשמר בשרת
// (leokmei-daf, own:sess) ולעולם אינו נכתב ליומן הריצה. מכשיר מקושר נפרד מזה של הזוהר היומי - אין נגיעה בשליחה שלו.
// 10.11.2026: השולח הפעיל הוא זוהר-דף-כלים/zyomi/לאוקמי-דף-יומי.mjs במאגר zohar-nikud (המכשיר המקושר של הזוהר היומי); קובץ זה רדום,
// ומעודכן איתו יחד. פרומפט 30: ההודעה היא תמונה עם כיתוב (doSend), לא טקסט עם תצוגה מקדימה.
// מה שונה מן המקור: היעד וההודעה, ושני מצבים נוספים:
//   community - מקים את הקהילה "לאוקמי גירסא - הדף היומי" ואת קבוצת ההכרזות שלה, ומחזיר לשרת את מזהיהן וקישור ההצטרפות
//   test      - שולח את ההודעה של היום (או נוסח בדיקה) לטלפון של בעל הפרויקט בלבד
// והפקודה עצמה נקבעת בשרת (wa-job), לא בקובץ ההרצה: הריצה המתוזמנת שואלת "יש מה לעשות?" ורק אז מתחברת.
import * as B from '@whiskeysockets/baileys';
const pick = (k) => (B[k] !== undefined ? B[k] : B.default && B.default[k]);
const makeWASocket = typeof B.default === 'function' ? B.default : B.default && typeof B.default.default === 'function' ? B.default.default : B.makeWASocket;
const initAuthCreds = pick('initAuthCreds'), BufferJSON = pick('BufferJSON'), DisconnectReason = pick('DisconnectReason'), Browsers = pick('Browsers'),
  fetchLatestBaileysVersion = pick('fetchLatestBaileysVersion'), jidNormalizedUser = pick('jidNormalizedUser');
import QRCode from 'qrcode';
import pino from 'pino';

const API = 'https://leokmei-daf.m7654301.workers.dev';
const SITE = 'https://leokmei.com';
const logger = pino({ level: 'silent' });

async function oidc() {
  const u = process.env.ACTIONS_ID_TOKEN_REQUEST_URL, t = process.env.ACTIONS_ID_TOKEN_REQUEST_TOKEN;
  if (!u || !t) throw new Error('אין אסימון OIDC (רק בריצת גיטהאב עם id-token: write)');
  const r = await fetch(u + '&audience=leokmei-daf', { headers: { authorization: 'bearer ' + t } });
  return (await r.json()).value;
}
async function api(p, body) {
  const tok = await oidc();
  const r = await fetch(API + '/' + p, {
    method: body ? 'POST' : 'GET',
    headers: Object.assign({ 'x-board-oidc': tok, 'user-agent': 'leokmei-daf-cloud' }, body ? { 'content-type': 'application/json' } : {}),
    body: body ? JSON.stringify(body) : undefined,
  });
  let j = null; try { j = await r.json(); } catch (e) { j = { ok: false, error: 'תשובה שאינה JSON (' + r.status + ')' }; }
  return Object.assign({ status: r.status }, j);
}

function authFrom(raw) {
  const data = raw ? JSON.parse(raw, BufferJSON.reviver) : { creds: initAuthCreds(), keys: {} };
  data.keys = data.keys || {};
  let dirty = false;
  const state = {
    creds: data.creds,
    keys: {
      get: async (type, ids) => { const o = {}; for (const id of ids) { const v = (data.keys[type] || {})[id]; if (v !== undefined) o[id] = v; } return o; },
      set: async (d) => { for (const type of Object.keys(d)) { data.keys[type] = data.keys[type] || {}; for (const id of Object.keys(d[type])) { if (d[type][id] == null) delete data.keys[type][id]; else data.keys[type][id] = d[type][id]; } } dirty = true; },
    },
  };
  const dump = () => JSON.stringify({ creds: state.creds, keys: data.keys }, BufferJSON.replacer);
  return { state, dump, touch: () => { dirty = true; }, isDirty: () => dirty, clean: () => { dirty = false; } };
}
async function save(auth, linked, me) {
  const r = await api('wa-sess', { sess: auth.dump(), linked: !!linked, me: me || '' });
  if (!r.ok) throw new Error('שמירת מצב החיבור נכשלה: ' + (r.error || r.status));
  auth.clean();
}

function connect(auth, onQr) {
  return new Promise(async (resolve, reject) => {
    const { version } = await Promise.race([fetchLatestBaileysVersion().catch(() => ({ version: undefined })), new Promise((r) => setTimeout(() => r({ version: undefined }), 8000))]);
    let sock;
    try { sock = makeWASocket({ version, auth: auth.state, logger, printQRInTerminal: false, browser: Browsers.ubuntu('Leokmei Daf'), markOnlineOnConnect: false, syncFullHistory: false }); } catch (e) { reject(e); return; }
    sock.ev.on('creds.update', () => auth.touch());
    sock.ev.on('connection.update', async (u) => {
      if (u.connection || u.qr) console.log('חיבור:', u.connection || '', u.qr ? 'ריבוע' : '');
      if (u.qr && onQr) await onQr(u.qr).catch((e) => console.error('הריבוע לא נשלח ללוח:', String(e && e.message || e)));
      if (u.connection === 'open') resolve({ sock, open: true });
      if (u.connection === 'close') {
        const code = u.lastDisconnect && u.lastDisconnect.error && u.lastDisconnect.error.output && u.lastDisconnect.error.output.statusCode;
        resolve({ sock, open: false, code, restart: code === DisconnectReason.restartRequired, loggedOut: code === DisconnectReason.loggedOut });
      }
    });
  });
}

async function link() {
  const auth = authFrom(null);
  const t0 = Date.now();
  for (let round = 0; round < 12 && Date.now() - t0 < 10 * 60000; round++) {
    const c = await connect(auth, async (qr) => { const r = await api('wa-qr', { svg: await QRCode.toString(qr, { type: 'svg', margin: 1, width: 260 }) }); console.log('ריבוע נשלח ללוח:', r.status, r.ok); });
    if (c.open) {
      await save(auth, true);
      await api('wa-qr', { done: true });
      await new Promise((r) => setTimeout(r, 4000));
      if (auth.isDirty()) await save(auth, true);
      c.sock.end(undefined);
      console.log('מחובר');
      return 0;
    }
    if (c.restart) { if (auth.isDirty()) await save(auth, false); continue; }
    if (c.loggedOut) break;
  }
  await api('wa-qr', { err: 'הזמן לסריקה עבר. לחץ שוב "חבר את הווטסאפ".' });
  console.log('לא נסרק');
  return 1;
}

/** התחברות במצב שמור. מחזיר את החיבור, או מדווח לשרת ומחזיר null */
async function open(job, kind) {
  if (!job.sess) { await api('wa-result', { kind, d: job.d || '', ok: false, why: 'הווטסאפ אינו מחובר' }); return null; }
  const auth = authFrom(job.sess);
  let c = await connect(auth);
  if (!c.open && c.restart) c = await connect(auth);
  if (!c.open) {
    const why = c.loggedOut ? 'הקישור לווטסאפ בוטל בטלפון - צריך לחבר מחדש' : 'החיבור לווטסאפ נכשל (' + (c.code || '?') + ')';
    if (c.loggedOut) await api('wa-sess', { sess: '', linked: false });
    await api('wa-result', { kind, d: job.d || '', ok: false, why });
    console.error(why); return null;
  }
  return { auth, sock: c.sock };
}
async function close(cn) {
  await new Promise((r) => setTimeout(r, 3000));
  if (cn.auth.isDirty()) await save(cn.auth, true).catch(() => null);
  cn.sock.end(undefined);
}

/* פרומפט 30 של לאוקמי (10.11.2026): ההודעה היא תמונה עם כיתוב, לא טקסט עם כרטיס של תצוגה מקדימה.
 * הסיבה: כרטיס התצוגה המקדימה של קישור אינו עובר תמיד כשמעבירים את ההודעה (Forward), ובמיוחד מקבוצת ההכרזות של קהילה -
 * והעברה היא בדיוק הדרך שבה ההודעה מגיעה לאנשים חדשים. תמונה עם כיתוב עוברת תמיד, בשלמותה, כהודעה אחת.
 * התמונה: הכרטיס הריבועי של הדף (leokmei.com/daf/wa/<דף>.jpg), שהשרת מוסר ב-job.image. הכיתוב: job.text כמו שהוא בלוח.
 * הכלל "חסר - לא שולחים": תמונה חסרה או פגומה, או כיתוב מעל המגבלה - לא שולחים כלום, ומדווחים לשרת (שורה אדומה בלוח).
 * לעולם לא נופלים לשליחת טקסט בלי תמונה, ולעולם לא מפצלים לשתי הודעות. */
const CAP_MAX = 1024;   // ווטסאפ: כיתוב של תמונה. השרת שולח גם הוא capMax, והקטן מביניהם קובע

/** מידות JPEG מתוך כותרת SOF - בלי ספרייה */
function jpegSize(b) {
  if (b.length < 4 || b[0] !== 0xff || b[1] !== 0xd8) return null;
  let i = 2;
  while (i + 9 < b.length) {
    if (b[i] !== 0xff) { i++; continue; }
    const m = b[i + 1], len = b.readUInt16BE(i + 2);
    if (m >= 0xc0 && m <= 0xcf && m !== 0xc4 && m !== 0xc8 && m !== 0xcc) return { h: b.readUInt16BE(i + 5), w: b.readUInt16BE(i + 7) };
    i += 2 + len;
  }
  return null;
}
/** מוריד את תמונת הכרטיס ובודק שהיא באמת תמונה שלמה. כל פגם - זורק, והשליחה נעצרת */
async function cardImage(url) {
  if (!/^https:\/\/leokmei\.com\/daf\/wa\/[a-z-]+-\d+\.jpg$/.test(String(url || ''))) throw new Error('לא נשלח: חסרה כתובת תמונת הכרטיס');
  let r;
  try { r = await fetch(url, { headers: { 'user-agent': 'leokmei-daf-cloud' } }); } catch (e) { throw new Error('לא נשלח: תמונת הכרטיס לא הורדה'); }
  if (!r.ok) throw new Error('לא נשלח: תמונת הכרטיס חסרה באתר (' + r.status + ')');
  if (!/^image\/jpe?g/.test(r.headers.get('content-type') || '')) throw new Error('לא נשלח: מה שהתקבל במקום תמונת הכרטיס אינו תמונה');
  const img = Buffer.from(await r.arrayBuffer());
  const sz = jpegSize(img);
  if (img.length < 10000 || !sz || sz.w < 600 || sz.h < 600) throw new Error('לא נשלח: תמונת הכרטיס פגומה (' + img.length + ' בתים' + (sz ? ', ' + sz.w + 'x' + sz.h : '') + ')');
  return { img, w: sz.w, h: sz.h };
}
// רשת ביטחון (9.11.2026): לעולם לא נקודה-פסיק ולא מקף ארוך בהודעה
const tidy = (x) => String(x || '').replace(/\s*;\s*/g, '. ').replace(/[\u2013\u2014]/g, '-');

/** הכנת ההודעה: התמונה והכיתוב, אחרי כל הבדיקות. נכשל - זורק, ושום דבר לא נשלח */
async function prepare(job) {
  const caption = tidy(job.text);
  const max = Math.min(CAP_MAX, +job.capMax || CAP_MAX) || CAP_MAX;
  const n = [...caption].length;
  if (!caption.trim()) throw new Error('לא נשלח: הכיתוב ריק');
  if (n > max && !(job.capMax > CAP_MAX)) throw new Error('לא נשלח: הכיתוב ארוך מדי (' + n + ' תווים, המרבי ' + max + ')');
  const c = await cardImage(job.image);
  return { caption, n, c };
}
async function sendCard(sock, to, m) {
  const out = await sock.sendMessage(to, { image: m.c.img, caption: m.caption, width: m.c.w, height: m.c.h, mimetype: 'image/jpeg' });
  return out;
}

async function doSend(job) {
  // הבדיקות לפני ההתחברות: חסר - לא מתחברים ולא שולחים
  let m;
  try { m = await prepare(job); } catch (e) {
    const res = { kind: 'send', d: job.d, ok: false, why: String(e && e.message || e).slice(0, 200) };
    await api('wa-result', res); console.error(res.why); return 1;
  }
  const cn = await open(job, 'send'); if (!cn) return 1;
  let res;
  try { const out = await sendCard(cn.sock, job.group, m); res = { kind: 'send', d: job.d, ok: true, id: out && out.key && out.key.id || '', why: '' }; }
  catch (e) { res = { kind: 'send', d: job.d, ok: false, why: 'השליחה נכשלה: ' + String(e && e.message || e).slice(0, 160) }; }
  await close(cn);
  await api('wa-result', res);
  console.log(res.ok ? 'נשלח (תמונה עם כיתוב, ' + m.n + ' תווים)' : res.why);
  return res.ok ? 0 : 1;
}

/** הודעת ניסיון: אותה תמונה ואותו כיתוב, לטלפון של בעל הפרויקט בלבד (הצ'אט שלו עם עצמו).
 *  job.fwd - אחרי השליחה מעבירים (Forward) את אותה הודעה אליו שוב, ובודקים שבהודעה המועברת יש תמונה וכיתוב. */
async function doTest(job) {
  let m;
  try { m = await prepare(job); } catch (e) {
    const res = { kind: 'test', d: job.d || '', ok: false, why: String(e && e.message || e).slice(0, 200) };
    await api('wa-result', res); console.error(res.why); return 1;
  }
  const cn = await open(job, 'test'); if (!cn) return 1;
  let res;
  try {
    const me = jidNormalizedUser(cn.sock.user && cn.sock.user.id);
    if (!me) throw new Error('המספר של המכשיר לא זוהה');
    const out = await sendCard(cn.sock, me, m);
    let why = 'נשלח אליך: תמונה עם כיתוב, ' + m.n + ' תווים';
    if (job.fwd && out) {
      await new Promise((r) => setTimeout(r, 2500));
      const f = await cn.sock.sendMessage(me, { forward: out });
      const im = f && f.message && f.message.imageMessage;
      const ok = !!(im && im.caption && im.contextInfo && im.contextInfo.isForwarded);
      why += ok ? '. והועברה (Forward) אליך שוב: ההודעה המועברת היא תמונה עם אותו כיתוב (' + [...im.caption].length + ' תווים)' : '. ההעברה נעשתה, אבל בהודעה המועברת לא נמצאו תמונה וכיתוב';
      console.log('העברה:', ok ? 'תמונה+כיתוב, מסומנת כמועברת' : JSON.stringify(Object.keys((f && f.message) || {})));
    }
    res = { kind: 'test', d: job.d || '', ok: true, id: out && out.key && out.key.id || '', why };
  } catch (e) { res = { kind: 'test', d: job.d || '', ok: false, why: 'הודעת הניסיון נכשלה: ' + String(e && e.message || e).slice(0, 160) }; }
  await close(cn);
  await api('wa-result', res);
  console.log(res.ok ? res.why : res.why);
  return res.ok ? 0 : 1;
}

/** הקמת הקהילה. ספריית החיבור (6.7.9, כמו בזוהר היומי) אינה מכירה קהילות - הבקשה נבנית כאן, באותה צורה שהאפליקציה שולחת.
 *  לא הצליח - מקימים קבוצת הכרזות רגילה באותו שם, ומדווחים בקול (הלוח מציג את מה שקרה). */
async function doCommunity(job) {
  const cn = await open(job, 'community'); if (!cn) return 1;
  const sock = cn.sock, name = job.name || 'לאוקמי גירסא - הדף היומי';
  const desc = 'קיצור הדף היומי מאת לאוקמי גירסא - הודעה אחת בכל בוקר, עם קישור לדף בתצוגה קלה לטלפון. leokmei.com/daf';
  let res, community = '', announce = '', how = '';
  try {
    try {
      const r = await sock.query({ tag: 'iq', attrs: { type: 'set', xmlns: 'w:g2', to: '@g.us' }, content: [{ tag: 'create', attrs: { subject: name }, content: [
        { tag: 'description', attrs: { id: Math.random().toString(16).slice(2, 12).toUpperCase() }, content: [{ tag: 'body', attrs: {}, content: Buffer.from(desc, 'utf-8') }] },
        { tag: 'parent', attrs: { default_membership_approval_mode: 'request_required' } },
        { tag: 'allow_non_admin_sub_group_creation', attrs: {} }] }] });   // בלי create_general_chat: קבוצה אחת בלבד (בעל הפרויקט, 8.11)
      const g = (r.content || []).find((n) => n.tag === 'group');
      if (!g || !g.attrs || !g.attrs.id) throw new Error('הקהילה לא הוחזרה');
      community = g.attrs.id.includes('@') ? g.attrs.id : g.attrs.id + '@g.us';
      await new Promise((r2) => setTimeout(r2, 3000));
      // קבוצת ההכרזות של הקהילה: המשנית שמסומנת כברירת המחדל
      const q = await sock.query({ tag: 'iq', attrs: { type: 'get', xmlns: 'w:g2', to: community }, content: [{ tag: 'sub_groups', attrs: {} }] });
      const subs = (((q.content || []).find((n) => n.tag === 'sub_groups') || {}).content || []).filter((n) => n.tag === 'group');
      const def = subs.find((n) => (n.content || []).some((c) => c.tag === 'default_sub_group') || n.attrs.default_sub_group === 'true') || subs.find((n) => /הכרזות|announce/i.test(n.attrs.subject || ''));
      if (def) announce = def.attrs.id.includes('@') ? def.attrs.id : def.attrs.id + '@g.us';
      how = 'קהילה';
      if (!announce) throw new Error('קבוצת ההכרזות של הקהילה לא נמצאה (' + subs.length + ' קבוצות)');
    } catch (e) {
      if (community && !announce) throw e;   // הקהילה קמה, ורק ההכרזות לא נמצאו - לא מקימים כפולה
      console.error('הקמת הקהילה נכשלה, מקים קבוצת הכרזות:', String(e && e.message || e).slice(0, 160));
      const g = await sock.groupCreate(name, []);
      announce = g.id;
      await sock.groupSettingUpdate(announce, 'announcement');
      await sock.groupUpdateDescription(announce, desc).catch(() => null);
      how = 'קבוצת הכרזות (הקהילה לא קמה: ' + String(e && e.message || e).slice(0, 80) + ')';
    }
    let invite = '';
    try { invite = 'https://chat.whatsapp.com/' + await sock.groupInviteCode(community || announce); } catch (e) { invite = ''; }
    const s = await api('wa-setup', { community, announce, invite, name });
    res = { kind: 'community', ok: !!s.ok, why: how + (s.ok ? '' : ' - השמירה בשרת נכשלה') };
  } catch (e) { res = { kind: 'community', ok: false, why: 'ההקמה נכשלה: ' + String(e && e.message || e).slice(0, 160) }; }
  await close(cn);
  await api('wa-result', res);
  console.log(res.ok ? 'הוקם: ' + res.why : res.why);
  return res.ok ? 0 : 1;
}

async function main() {
  const job = await api('wa-job');
  if (!job.ok) { console.error('השרת סירב:', job.status, job.error); return 1; }
  console.log('מצב:', job.mode, job.why || '');
  if (job.mode === 'link') return link();
  if (job.mode === 'send') return doSend(job);
  if (job.mode === 'test') return doTest(job);
  if (job.mode === 'community') return doCommunity(job);
  return 0;
}

const code = await main().catch(async (e) => {
  const msg = String(e && e.message || e);
  console.error(msg);
  await api('wa-result', { kind: 'error', ok: false, why: 'השולח נכשל: ' + msg.slice(0, 120) }).catch(() => null);
  await api('wa-qr', { err: 'נכשל: ' + msg.slice(0, 120) }).catch(() => null);
  return 1;
});
process.exit(code);
