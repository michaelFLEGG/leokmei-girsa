// פרומפט 23 (8.11.2026): השולח של "הדף היומי בווטסאפ" של לאוקמי גירסא.
// הועתק כמו שהוא מן השולח העצמאי של "הזוהר היומי" (ממלכת הזוהר, זוהר-דף-כלים/zyomi/ווטסאפ-עצמאי.mjs, פרומפט 44 ב):
// הווטסאפ של בעל הפרויקט מקושר (פעם אחת, בסריקה בטלפון) כמכשיר נוסף. הקוד רץ בריצת גיטהאב (daf-wa.yml), מתחבר, שולח ומתנתק.
// אין כאן שום סוד: ההרשאה מול השרת היא אסימון OIDC של קובץ ההרצה הזה בלבד (קהל leokmei-daf), ומצב החיבור נשמר בשרת
// (leokmei-daf, own:sess) ולעולם אינו נכתב ליומן הריצה. מכשיר מקושר נפרד מזה של הזוהר היומי - אין נגיעה בשליחה שלו.
// מה שונה מן המקור: היעד וההודעה (טקסט שבראשו קישור; הכרטיס הגדול הוא התצוגה המקדימה של הקישור), ושני מצבים נוספים:
//   community - מקים את הקהילה "לאוקמי גירסא - הדף היומי" ואת קבוצת ההכרזות שלה, ומחזיר לשרת את מזהיהן וקישור ההצטרפות
//   test      - שולח את ההודעה של היום (או נוסח בדיקה) לטלפון של בעל הפרויקט בלבד
// והפקודה עצמה נקבעת בשרת (wa-job), לא בקובץ ההרצה: הריצה המתוזמנת שואלת "יש מה לעשות?" ורק אז מתחברת.
import * as B from '@whiskeysockets/baileys';
const pick = (k) => (B[k] !== undefined ? B[k] : B.default && B.default[k]);
const makeWASocket = typeof B.default === 'function' ? B.default : B.default && typeof B.default.default === 'function' ? B.default.default : B.makeWASocket;
const initAuthCreds = pick('initAuthCreds'), BufferJSON = pick('BufferJSON'), DisconnectReason = pick('DisconnectReason'), Browsers = pick('Browsers'),
  fetchLatestBaileysVersion = pick('fetchLatestBaileysVersion'), prepareWAMessageMedia = pick('prepareWAMessageMedia'), jidNormalizedUser = pick('jidNormalizedUser');
import QRCode from 'qrcode';
import pino from 'pino';

const API = 'https://leokmei-daf.m7654301.workers.dev';
const SITE = 'https://leokmei.com';
const CARD_TITLE = 'לאוקמי גירסא - קיצור הדף היומי';
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

/** הכרטיס הגדול: התצוגה המקדימה של הקישור שבשורה הראשונה, בנויה מן הכרטיס של הדף (1200x480) - בלי לגרד את הדף */
async function linkPreview(sock, text) {
  const m = String(text).match(/^(?:https?:\/\/)?(leokmei\.com\/daf\/([a-z-]+-\d+))\s*$/m);
  if (!m) return undefined;
  const url = SITE + '/daf/' + m[2];
  let desc = '';
  try { const r = await fetch(SITE + '/daf/data/' + m[2] + '.json'); if (r.ok) { const c = await r.json(); desc = c.card || ''; } } catch (e) { desc = ''; }
  let img = null;
  try { const r = await fetch(SITE + '/daf/og/' + m[2] + '.jpg'); if (r.ok && /image/.test(r.headers.get('content-type') || '')) img = Buffer.from(await r.arrayBuffer()); } catch (e) { img = null; }
  const lp = { 'canonical-url': url, 'matched-text': m[1], title: CARD_TITLE, description: desc };
  if (img) {
    try {
      const { imageMessage } = await prepareWAMessageMedia({ image: img }, { upload: sock.waUploadToServer, mediaTypeOverride: 'thumbnail-link', logger });
      if (imageMessage) { imageMessage.width = imageMessage.width || 1200; imageMessage.height = imageMessage.height || 480; lp.highQualityThumbnail = imageMessage; }
      lp.jpegThumbnail = imageMessage && imageMessage.jpegThumbnail ? Buffer.from(imageMessage.jpegThumbnail) : img;
    } catch (e) { console.error('העלאת הכרטיס נכשלה, יוצא כרטיס קטן:', String(e && e.message || e).slice(0, 120)); lp.jpegThumbnail = img; }
  }
  return lp;
}

async function sendText(sock, to, text) {
  const lp = await linkPreview(sock, text);
  const out = await sock.sendMessage(to, lp ? { text, linkPreview: lp } : { text });
  return { id: out && out.key && out.key.id || '', card: !!(lp && lp.highQualityThumbnail) };
}

async function doSend(job) {
  const cn = await open(job, 'send'); if (!cn) return 1;
  let res;
  try { const o = await sendText(cn.sock, job.group, job.text); res = { kind: 'send', d: job.d, ok: true, id: o.id, why: o.card ? '' : 'יצא בלי כרטיס גדול' }; }
  catch (e) { res = { kind: 'send', d: job.d, ok: false, why: 'השליחה נכשלה: ' + String(e && e.message || e).slice(0, 160) }; }
  await close(cn);
  await api('wa-result', res);
  console.log(res.ok ? 'נשלח' : res.why);
  return res.ok ? 0 : 1;
}

async function doTest(job) {
  const cn = await open(job, 'test'); if (!cn) return 1;
  let res;
  try {
    const me = jidNormalizedUser(cn.sock.user && cn.sock.user.id);
    if (!me) throw new Error('המספר של המכשיר לא זוהה');
    const o = await sendText(cn.sock, me, job.text);
    res = { kind: 'test', d: job.d || '', ok: true, id: o.id, why: o.card ? 'נשלח אליך, עם כרטיס גדול' : 'נשלח אליך, בלי כרטיס גדול' };
  } catch (e) { res = { kind: 'test', d: job.d || '', ok: false, why: 'הודעת הניסיון נכשלה: ' + String(e && e.message || e).slice(0, 160) }; }
  await close(cn);
  await api('wa-result', res);
  console.log(res.ok ? 'נשלחה הודעת ניסיון' : res.why);
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
