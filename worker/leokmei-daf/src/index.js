/* leokmei-daf - "הדף היומי בווטסאפ" של לאוקמי גירסא (פרומפט 23, 8.11.2026).
 *
 * הועתק מלוח "הזוהר היומי" של ממלכת הזוהר (functions/api/_lib/zyomi.js, functions/api/zyomi/[[path]].js,
 * zyomi-cron-worker, זוהר-דף-כלים/zyomi/ווטסאפ-עצמאי.mjs), שהועתק בשעתו מ"אמרת היום" של שפע יואל,
 * ושונו רק: מקור התוכן (הגמרא של הדף היומי, data/daf-wa באתר), מבנה ההודעה (טקסט בלי תמונה; הכרטיס
 * הוא התצוגה המקדימה של הקישור), היעד (קבוצת ההכרזות "לאוקמי גירסא - הדף היומי"), והשעה (06:00).
 * נפרד לגמרי מממלכת הזוהר: בלי קוד משותף בזמן ריצה ובלי נתונים משותפים.
 * פרומפט 30 (10.11.2026): ההודעה היא מעכשיו תמונה עם כיתוב - הכרטיס הריבועי (leokmei.com/daf/wa/<דף>.jpg) וכל הנוסח ככיתוב שלו -
 *   כי כרטיס של תצוגה מקדימה אינו עובר תמיד בהעברה. הרכבת הכיתוב ולוח השנה: core.js. תמונה חסרה או כיתוב מעל 1024 - לא שולחים, ומתריעים בלוח.
 *
 * כללים (סעיפים 2, 5, 8 בפרומפט):
 *  א. לעולם לא בשבת וביום טוב. בשישי ובערב חג - הדפים של הימים שאין בהם שליחה יוצאים יחד, בהודעה אחת.
 *  ב. תוכן שחסר, או שלא עבר את הבודק (check.ok) - אינו יוצא, ולעולם אין הודעת "בהכנה".
 *  ג. שלושת ימי השליחה הראשונים - רק אחרי "אשר" בלוח. מן הרביעי - אוטומטי בשעה שנקבעה (ברירת מחדל 06:00).
 *  ד. כל התערבות של המנהל (עריכה, בחירת "הידעת", עצירה, שעה, אישור) נרשמת ביומן הלמידה, שהכותב קורא לפני כל כתיבה.
 *  ה. מצב החיבור לווטסאפ (own:sess) אינו יוצא לעולם לדפדפן; רק לריצת השולח (OIDC של daf-wa.yml).
 */

import { TZ, CAP_MAX, DAY, ilKey, ilHM, dn, keyOf, addDays, dow, heb, letters, gq, dayMeta, L, dafOf, dafimFor, compose, toCaption, capLen } from './core.js';

const SITE = 'https://leokmei.com';
const DAYS_AHEAD = 10;
const SEND_HM = '06:00';
const SEND_UNTIL_H = 12;           // אחרי 12:00 לא שולחים הודעה של הבוקר
const APPROVE_FIRST = 3;           // שלושת הימים הראשונים - רק באישור
const LEARN_MAX = 400;

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
  'Access-Control-Allow-Headers': 'content-type, x-admin-key, x-board-oidc',
  'Access-Control-Max-Age': '86400',
};
const json = (o, status) => new Response(JSON.stringify(o), { status: status || 200, headers: Object.assign({ 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store, private' }, CORS) });
const bad = (m, s) => json({ ok: false, error: m }, s || 400);
async function jget(env, k, d) { try { const v = await env.DAF.get(k, 'json'); return v == null ? d : v; } catch (e) { return d; } }
const jput = (env, k, v, o) => env.DAF.put(k, JSON.stringify(v), o);

/* ---------- תוכן (נבנה באתר מ-data/daf-wa, אחרי הבודק) ---------- */
const memo = new Map();
async function content(slug, n) {
  const k = slug + '-' + n, hit = memo.get(k);
  if (hit && Date.now() - hit.t < 300000) return hit.v;
  let v = null;
  try { const r = await fetch(SITE + '/daf/data/' + k + '.json', { cf: { cacheTtl: 120 } }); if (r.ok) v = await r.json(); } catch (e) { v = null; }
  memo.set(k, { t: Date.now(), v });
  return v;
}
const hasOk = (c) => !!(c && c.check && c.check.ok && c.hook && c.hook.q && Array.isArray(c.lines) && c.lines.length >= 4);

/* ---------- התמונה שנשלחת (פרומפט 30): הכרטיס הריבועי של הדף הראשון בהודעה ---------- */
const imgUrl = (slug, n) => SITE + '/daf/wa/' + slug + '-' + n + '.jpg';
const imgMemo = new Map();
/** האם תמונת הכרטיס קיימת באתר ותקינה (תמונה, לא דף שגיאה, ולא קובץ ריק). חסרה או פגומה - ההודעה אינה יוצאת. */
async function imgOk(url) {
  const hit = imgMemo.get(url);
  if (hit && Date.now() - hit.t < 300000) return hit.v;
  let v = false;
  try {
    const r = await fetch(url, { method: 'HEAD', cf: { cacheTtl: 120 } });
    v = r.ok && /^image\/jpe?g/.test(r.headers.get('content-type') || '') && +(r.headers.get('content-length') || 20000) >= 10000;
  } catch (e) { v = false; }
  imgMemo.set(url, { t: Date.now(), v });
  return v;
}

/** כל מה שהלוח והשולח צריכים לדעת על יום אחד */
async function dayView(env, k, cfg) {
  const meta = dayMeta(k), rec = await jget(env, 'day:' + k, {}) || {};
  const dafim = dafimFor(k);
  const items = [];
  for (const x of dafim) items.push(Object.assign({}, x, { c: await content(x.slug, x.n) }));
  const missing = items.filter((x) => !hasOk(x.c)).map((x) => x.name + ' ' + gq(x.n));
  const auto = missing.length ? '' : compose(meta, items, rec, cfg.invite);
  // פרומפט 30: נוסח שנערך או נכתב בצורה הקודמת מוצג ונשלח בצורת הכיתוב - צורה בלבד, בלי לשנות מילה (toCaption).
  // הודעה שכבר נשלחה מוצגת כמו שנשלחה.
  const text = rec.sentAt ? (rec.text || auto) : ((rec.text || auto) ? toCaption(rec.text || auto, cfg.invite) : '');
  const img = imgUrl(dafim[0].slug, dafim[0].n);
  const hasImg = meta.noSend || rec.sentAt || missing.length ? true : await imgOk(img);
  const len = capLen(text);
  const sent = (cfg.sent || 0);
  const needApprove = sent < APPROVE_FIRST;
  let state;
  if (meta.noSend) state = 'holy';
  else if (rec.sentAt) state = 'sent';
  else if (rec.status === 'stopped') state = 'stopped';
  else if (missing.length) state = 'missing';
  else if (!hasImg) state = 'noimage';          // "חסר - לא שולחים": בלי תמונת הכרטיס אין הודעה
  else if (len > CAP_MAX) state = 'toolong';    // ווטסאפ: כיתוב של תמונה עד 1024 תווים. לא מפצלים להודעה שנייה לעולם
  else if (needApprove && rec.status !== 'approved') state = 'await';
  else state = rec.status === 'approved' ? 'approved' : 'auto';
  return {
    d: k, meta, state, text, auto, edited: !!rec.text, pick: Number.isInteger(rec.pick) ? rec.pick : null, time: rec.time || SEND_HM,
    sentAt: rec.sentAt || 0, err: rec.err || '', needApprove, missing, img, hasImg, len, capMax: CAP_MAX,
    dafim: items.map((x) => ({ slug: x.slug, n: x.n, label: x.name + ' ' + gq(x.n), url: SITE + '/daf/' + x.slug + '-' + x.n, og: SITE + '/daf/og/' + x.slug + '-' + x.n + '.jpg',
      hook: x.c && x.c.hook, alts: (x.c && x.c.alts) || [], card: x.c && x.c.card, checked: hasOk(x.c) })),
  };
}

/* ---------- מנהל: אותו מפתח כמו בשאר לוחות המנהל של האתר (נבדק ב-leokmei-suggest) ---------- */
const admMemo = new Map();
async function isAdmin(req, env) {
  const k = req.headers.get('x-admin-key') || '';
  if (!k || k.length > 120) return false;
  const hit = admMemo.get(k);
  if (hit && Date.now() - hit.t < 300000) return hit.v;
  let v = false;
  try { const r = await env.SUGGEST.fetch('https://suggest/whoami', { headers: { 'x-admin-key': k } }); v = !!(r.ok && (await r.json()).admin); } catch (e) { v = false; }
  admMemo.set(k, { t: Date.now(), v });
  return v;
}

/* ---------- השולח: OIDC של .github/workflows/daf-wa.yml בלבד (מועתק מ-zyomi-oidc.js) ---------- */
const ISS = 'https://token.actions.githubusercontent.com', AUD = 'leokmei-daf', REPO = 'michaelflegg/leokmei-girsa';
const WF = REPO + '/.github/workflows/daf-wa.yml@';
// 8.11.2026: ארבעת המכשירים המקושרים של בעל הפרויקט תפוסים, ולכן השליחה עוברת דרך המכשיר של הזוהר היומי -
// ריצת zyomi-wa.yml במאגר הזוהר (באותה קבוצת ריצה שלו, כך שלעולם אינן רצות יחד)
const SENDERS = [[REPO, WF], ['michaelflegg/zohar-nikud', 'michaelflegg/zohar-nikud/.github/workflows/zyomi-wa.yml@']];
const b64u = (s) => Uint8Array.from(atob(s.replace(/-/g, '+').replace(/_/g, '/')), (c) => c.charCodeAt(0));
const part = (s) => JSON.parse(new TextDecoder().decode(b64u(s)));
async function isSender(req) {
  try {
    const jwt = req.headers.get('x-board-oidc') || '';
    const [h, p, sig] = jwt.split('.');
    if (!sig) return false;
    const head = part(h), c = part(p), t = Date.now() / 1000;
    if (head.alg !== 'RS256' || c.iss !== ISS || c.aud !== AUD) return false;
    const repo = String(c.repository || '').toLowerCase(), wf = String(c.workflow_ref || '').toLowerCase();
    if (!SENDERS.some(([r, w]) => repo === r && wf.startsWith(w))) return false;
    if (!(c.exp > t) || (c.nbf && c.nbf > t + 60)) return false;
    const r = await fetch(ISS + '/.well-known/jwks', { cf: { cacheTtl: 3600, cacheEverything: true } });
    const jwk = ((await r.json()).keys || []).find((k) => k.kid === head.kid);
    if (!jwk) return false;
    const key = await crypto.subtle.importKey('jwk', jwk, { name: 'RSASSA-PKCS1-v1_5', hash: 'SHA-256' }, false, ['verify']);
    return await crypto.subtle.verify('RSASSA-PKCS1-v1_5', key, b64u(sig), new TextEncoder().encode(h + '.' + p));
  } catch (e) { return false; }
}

/* ---------- יומן הלמידה ---------- */
async function learn(env, ev) {
  const log = await jget(env, 'learn:log', []);
  log.push(Object.assign({ t: new Date().toISOString() }, ev));
  await jput(env, 'learn:log', log.slice(-LEARN_MAX));
}

/* ---------- מה יוצא עכשיו ---------- */
async function mark(env, d) {
  const rec = await jget(env, 'day:' + d, {}) || {};
  rec.tryAt = Date.now(); rec.tries = (rec.tries || 0) + 1;
  await jput(env, 'day:' + d, rec);
}
async function due(env, now) {
  const cfg = await jget(env, 'cfg', {});
  const cmd = await jget(env, 'cmd', null);
  if (cmd && Date.now() - (cmd.at || 0) < 30 * 60000) {
    if (cmd.taken && Date.now() - cmd.taken < 20 * 60000) return { cfg, busy: true };
    return { cmd, cfg };
  }
  const k = ilKey(now), v = await dayView(env, k, cfg);
  // פרומפט 30: הגיעה השעה, והתמונה חסרה או שהכיתוב ארוך מדי - לא שולחים, ומתריעים בלוח פעם אחת (שורה אדומה ביום, ו"הפעולה האחרונה")
  if (['noimage', 'toolong'].includes(v.state) && ilHM(now) >= v.time && +ilHM(now).slice(0, 2) < SEND_UNTIL_H) {
    const r0 = await jget(env, 'day:' + k, {}) || {};
    if (!r0.blockAt) {
      const why = v.state === 'noimage' ? 'לא נשלח: תמונת הכרטיס חסרה או פגומה באתר' : 'לא נשלח: הכיתוב ארוך מדי (' + v.len + ' תווים, המרבי ' + CAP_MAX + ')';
      r0.blockAt = Date.now(); r0.err = why; await jput(env, 'day:' + k, r0);
      await jput(env, 'last', { kind: 'send', ok: false, why, d: k, t: new Date().toISOString(), id: '' });
    }
    return { v, cfg };
  }
  if (!['auto', 'approved'].includes(v.state)) return { v, cfg };
  const rec = await jget(env, 'day:' + k, {}) || {};
  if ((rec.tries || 0) >= 3 || (rec.tryAt && Date.now() - rec.tryAt < 20 * 60000)) return { v, cfg };
  const hm = ilHM(now);
  if (hm >= v.time && +hm.slice(0, 2) < SEND_UNTIL_H) return { send: true, v, cfg };
  return { v, cfg };
}

async function handle(req, env, url) {
  const p = url.pathname.replace(/\/+$/, '') || '/';
  if (req.method === 'OPTIONS') return new Response(null, { headers: CORS });
  if (p === '/' || p === '/health') return json({ ok: true, service: 'leokmei-daf' });

  // ציבורי ובלי שום סוד: האם יש לשולח מה לעשות (ריצת גיטהאב שואלת לפני שהיא מתקינה את הספריות)
  if (p === '/poll') {
    const x = await due(env, Date.now());
    return json({ ok: true, go: !!(x.send || x.cmd), mode: x.cmd ? x.cmd.op : (x.send ? 'send' : (x.busy ? 'busy' : 'none')) });
  }
  // יומן הלמידה - קריאה בלבד, בשביל הכותב (אין בו פרט אישי: רק הנוסח שהמנהל העדיף)
  if (p === '/learn' && req.method === 'GET') return json({ ok: true, log: await jget(env, 'learn:log', []) });

  /* ---------- השולח ---------- */
  if (/^\/wa-/.test(p)) {
    if (!(await isSender(req))) return bad('אין הרשאה', 401);
    if (p === '/wa-job' && req.method === 'GET') {
      const x = await due(env, Date.now()), cfg = x.cfg, sess = (await env.DAF.get('own:sess')) || '';
      if (x.cmd) {
        const c = x.cmd;
        c.taken = Date.now(); await jput(env, 'cmd', c);
        if (c.op === 'send') {
          const v = await dayView(env, c.d, cfg);
          if (v.missing.length || v.state === 'holy') { await env.DAF.delete('cmd'); return json({ ok: true, mode: 'none', why: 'אין מה לשלוח ביום הזה' }); }
          if (!cfg.announce) { await env.DAF.delete('cmd'); return json({ ok: true, mode: 'none', why: 'קבוצת ההכרזות לא הוקמה' }); }
          if (!v.hasImg || v.len > CAP_MAX) {
            await env.DAF.delete('cmd');
            const why = !v.hasImg ? 'לא נשלח: תמונת הכרטיס חסרה או פגומה באתר' : 'לא נשלח: הכיתוב ארוך מדי (' + v.len + ' תווים, המרבי ' + CAP_MAX + ')';
            const r0 = await jget(env, 'day:' + c.d, {}) || {}; r0.err = why; await jput(env, 'day:' + c.d, r0);
            await jput(env, 'last', { kind: 'send', ok: false, why, d: c.d, t: new Date().toISOString(), id: '' });
            return json({ ok: true, mode: 'none', why });
          }
          await mark(env, c.d);
          return json({ ok: true, mode: 'send', d: c.d, group: cfg.announce, text: v.text, image: v.img, capMax: CAP_MAX, sess });
        }
        if (c.op === 'test') {
          const v = await dayView(env, c.d || ilKey(Date.now()), cfg);
          // פרומפט 30: הודעת הניסיון היא אותה תמונה עם אותו כיתוב, לטלפון של בעל הפרויקט בלבד.
          // fwd - אחרי השליחה השולח גם מעביר (Forward) אותה אליו, כדי לראות שהתמונה נשארת בהעברה.
          // cap - כיתוב לבדיקת מגבלת האורך (נקבע רק בפקודה ישירה ב-KV, לא מן הלוח).
          return json({ ok: true, mode: 'test', d: c.d || '', text: c.cap ? String(c.cap) : (v.text || 'בדיקה'), image: v.img, capMax: c.cap ? 65536 : CAP_MAX, fwd: !!c.fwd, sess });
        }
        return json({ ok: true, mode: c.op, name: c.name || '', sess });
      }
      if (!x.send) return json({ ok: true, mode: 'none', why: x.v ? x.v.state : '' });
      if (!cfg.announce) return json({ ok: true, mode: 'none', why: 'קבוצת ההכרזות לא הוקמה' });
      await mark(env, x.v.d);
      return json({ ok: true, mode: 'send', d: x.v.d, group: cfg.announce, text: x.v.text, image: x.v.img, capMax: CAP_MAX, sess });
    }
    let b = {};
    try { b = await req.json(); } catch (e) { return bad('גוף הבקשה אינו JSON'); }
    if (p === '/wa-sess') {
      if (b.shared) { await jput(env, 'own', { linked: true, shared: true, at: new Date().toISOString() }); return json({ ok: true }); }
      if (!b.sess) { await env.DAF.delete('own:sess'); await jput(env, 'own', { linked: false, at: new Date().toISOString(), why: 'הקישור בוטל' }); return json({ ok: true }); }
      await env.DAF.put('own:sess', String(b.sess));
      await jput(env, 'own', { linked: !!b.linked, at: new Date().toISOString(), me: String(b.me || '').replace(/\D/g, '').slice(-4) });
      return json({ ok: true });
    }
    if (p === '/wa-qr') {
      if (b.done || b.err) await env.DAF.delete('cmd');
      await jput(env, 'own:qr', { svg: b.svg ? String(b.svg).slice(0, 60000) : '', done: !!b.done, err: b.err || '', t: Date.now() }, { expirationTtl: 3600 });
      return json({ ok: true });
    }
    if (p === '/wa-setup') {
      const cfg = await jget(env, 'cfg', {});
      Object.assign(cfg, { community: String(b.community || cfg.community || ''), announce: String(b.announce || cfg.announce || ''), invite: String(b.invite || cfg.invite || ''), name: String(b.name || cfg.name || ''), setupAt: new Date().toISOString() });
      await jput(env, 'cfg', cfg);
      await env.DAF.delete('cmd');
      return json({ ok: true });
    }
    if (p === '/wa-result') {
      const cmd = await jget(env, 'cmd', null);
      if (cmd) await env.DAF.delete('cmd');
      const kind = String(b.kind || 'send');
      await jput(env, 'last', { kind, ok: !!b.ok, why: String(b.why || '').slice(0, 300), d: b.d || '', t: new Date().toISOString(), id: b.id || '' });
      if (kind === 'send' && b.d) {
        const rec = await jget(env, 'day:' + b.d, {}) || {};
        if (b.ok) {
          rec.sentAt = Date.now(); rec.err = b.why ? String(b.why).slice(0, 200) : ''; rec.msgId = String(b.id || '');
          const cfg = await jget(env, 'cfg', {}); cfg.sent = (cfg.sent || 0) + 1; await jput(env, 'cfg', cfg);
        } else { rec.err = String(b.why || 'השליחה נכשלה').slice(0, 300); delete rec.tryAt; }
        await jput(env, 'day:' + b.d, rec);
      }
      return json({ ok: true });
    }
    return bad('לא נמצא', 404);
  }

  /* ---------- הלוח (מנהל בלבד) ---------- */
  if (!(await isAdmin(req, env))) return bad('אין הרשאה', 401);
  if (p === '/days' && req.method === 'GET') {
    const cfg = await jget(env, 'cfg', {}), today = ilKey(Date.now());
    const days = [];
    for (let i = 0; i < DAYS_AHEAD; i++) days.push(await dayView(env, addDays(today, i), cfg));
    // הפיילוט (פרומפט 23): בכורות ל"ב עד ל"ח, להצגה ולאישור הנוסח, גם כשאינם בימים הקרובים
    let pilot = [];
    if (url.searchParams.get('pilot') !== '0') {
      for (let n = 32; n <= 38; n++) {
        const c = await content('bekhorot', n);
        const k = 'pilot-' + n, rec = await jget(env, 'day:' + k, {}) || {};
        const meta = { d: k, line: dayMeta(pilotDate(n)).line, heb: '', noSend: false };
        const it = { name: 'בכורות', slug: 'bekhorot', n, last: 61, c };
        const auto = hasOk(c) ? compose(meta, [it], rec, cfg.invite) : '', text = (rec.text || auto) ? toCaption(rec.text || auto, cfg.invite) : '';
        pilot.push({ d: k, meta, state: hasOk(c) ? (rec.status === 'approved' ? 'approved' : 'pilot') : 'missing', text, img: imgUrl('bekhorot', n), hasImg: true, len: capLen(text), capMax: CAP_MAX,
          auto, edited: !!rec.text, pick: Number.isInteger(rec.pick) ? rec.pick : null, time: SEND_HM, sentAt: 0, err: '', needApprove: true, missing: hasOk(c) ? [] : ['בכורות ' + gq(n)],
          dafim: [{ slug: 'bekhorot', n, label: 'בכורות ' + gq(n), url: SITE + '/daf/bekhorot-' + n, og: SITE + '/daf/og/bekhorot-' + n + '.jpg', hook: c && c.hook, alts: (c && c.alts) || [], card: c && c.card, checked: hasOk(c) }] });
      }
    }
    const own = await jget(env, 'own', { linked: false });
    const last = await jget(env, 'last', null);
    return json({ ok: true, today, days, pilot, own: { linked: !!own.linked, shared: !!own.shared, at: own.at || '', why: own.why || '' }, cfg: { announce: !!cfg.announce, name: cfg.name || '', invite: cfg.invite || '', sent: cfg.sent || 0, approveFirst: APPROVE_FIRST }, last, cmd: await jget(env, 'cmd', null) });
  }
  if (p === '/own' && req.method === 'GET') {
    const own = await jget(env, 'own', { linked: false }), qr = await jget(env, 'own:qr', null);
    return json({ ok: true, linked: !!own.linked, at: own.at || '', qr: qr && Date.now() - qr.t < 90000 ? qr : (qr && (qr.done || qr.err) ? qr : null), cmd: await jget(env, 'cmd', null) });
  }
  if (req.method !== 'POST') return bad('לא נמצא', 404);
  let b = {};
  try { b = await req.json(); } catch (e) { return bad('גוף הבקשה אינו JSON'); }
  const d = String(b.d || '');
  const okKey = /^\d{4}-\d{2}-\d{2}$/.test(d) || /^pilot-\d{2}$/.test(d);
  const rk = 'day:' + d;
  if (['/edit', '/restore', '/approve', '/stop', '/resume', '/pick', '/time', '/sendnow'].includes(p) && !okKey) return bad('יום לא תקין');
  const rec = okKey ? (await jget(env, rk, {}) || {}) : {};
  if (p === '/edit') {
    const t = String(b.text || '').trim();
    if (!t || t.length > 4000) return bad('נוסח ריק או ארוך מדי');
    if (/[—–]/.test(t)) return bad('בלי קווים ארוכים - רק מקף רגיל');
    // פרומפט 30: ההודעה היא תמונה עם כיתוב, וכיתוב של תמונה בווטסאפ מוגבל ל-1024 תווים. לא מפצלים לעולם - מקצרים.
    const cl = capLen(toCaption(t, (await jget(env, 'cfg', {})).invite));
    if (cl > CAP_MAX) return bad('הנוסח ארוך מדי לכיתוב של תמונה: ' + cl + ' תווים, והמרבי ' + CAP_MAX + '. קצר את "הדף בקצרה" ושמור שוב.');
    delete rec.blockAt; if (/^לא נשלח: הכיתוב ארוך/.test(rec.err || '')) delete rec.err;
    await learn(env, { kind: 'edit', d, before: String(b.before || rec.text || '').slice(0, 4000), after: t });
    rec.text = t; rec.editedAt = Date.now();
    await jput(env, rk, rec); return json({ ok: true });
  }
  if (p === '/restore') { await learn(env, { kind: 'restore', d }); delete rec.text; await jput(env, rk, rec); return json({ ok: true }); }
  if (p === '/approve') { rec.status = 'approved'; rec.approvedAt = Date.now(); await learn(env, { kind: 'approve', d, text: String(b.text || '').slice(0, 4000) }); await jput(env, rk, rec); return json({ ok: true }); }
  if (p === '/stop') { rec.status = 'stopped'; await learn(env, { kind: 'stop', d, why: String(b.why || '').slice(0, 300) }); await jput(env, rk, rec); return json({ ok: true }); }
  if (p === '/resume') { delete rec.status; await jput(env, rk, rec); return json({ ok: true }); }
  if (p === '/pick') {
    const i = b.i === null || b.i === '' || b.i === undefined ? null : +b.i;
    await learn(env, { kind: 'pick', d, i, q: String(b.q || '').slice(0, 300) });
    if (i === null || !Number.isInteger(i)) delete rec.pick; else rec.pick = i;
    delete rec.text;   // הנוסח נבנה מחדש עם "הידעת" שנבחר
    await jput(env, rk, rec); return json({ ok: true });
  }
  if (p === '/time') {
    const hm = String(b.hm || '');
    if (!/^([01]\d|2[0-3]):[0-5]\d$/.test(hm)) return bad('שעה לא תקינה');
    await learn(env, { kind: 'time', d, hm });
    rec.time = hm; await jput(env, rk, rec); return json({ ok: true });
  }
  if (p === '/sendnow') {
    if (/^pilot/.test(d)) return bad('דפי הפיילוט אינם נשלחים לקבוצה');
    const cfg = await jget(env, 'cfg', {}), v = await dayView(env, d, cfg);
    if (v.missing.length) return bad('חסר תוכן שנבדק - אין שליחה');
    if (v.state === 'holy') return bad('שבת או יום טוב - אין שליחה');
    if (v.sentAt) return bad('ההודעה של היום הזה כבר נשלחה');
    if (!cfg.announce) return bad('קבוצת ההכרזות עוד לא הוקמה');
    if (!v.hasImg) return bad('תמונת הכרטיס של הדף חסרה או פגומה באתר - אין שליחה');
    if (v.len > CAP_MAX) return bad('הכיתוב ארוך מדי (' + v.len + ' תווים, המרבי ' + CAP_MAX + ') - קצר את "הדף בקצרה"');
    rec.status = 'approved'; rec.approvedAt = Date.now(); delete rec.tries; delete rec.tryAt; await jput(env, rk, rec);
    await learn(env, { kind: 'sendnow', d });
    await jput(env, 'cmd', { op: 'send', d, at: Date.now() });
    return json({ ok: true });
  }
  if (p === '/link' && (await jget(env, 'own', {})).shared) return bad('הדף היומי משתמש במכשיר המקושר של הזוהר היומי - אין צורך לסרוק');
  if (p === '/link') { await env.DAF.delete('own:qr'); await jput(env, 'cmd', { op: 'link', at: Date.now() }); return json({ ok: true }); }
  if (p === '/setup') { await jput(env, 'cmd', { op: 'community', name: 'לאוקמי גירסא - הדף היומי', at: Date.now() }); return json({ ok: true }); }
  if (p === '/test') { await jput(env, 'cmd', { op: 'test', d: /^\d{4}-\d{2}-\d{2}$/.test(d) ? d : '', at: Date.now() }); return json({ ok: true }); }
  if (p === '/cancel') { await env.DAF.delete('cmd'); return json({ ok: true }); }
  return bad('לא נמצא', 404);
}

/** התאריך שבו נלמד דף הפיילוט במחזור הנוכחי (לשורת התאריך בתצוגה) */
function pilotDate(n) {
  let off = 0;
  for (const [, s, first, cnt] of L) { if (s === 'bekhorot') { off += n - first; break; } off += cnt; }
  const base = dn('2020-01-05') + off, k = Math.round((dn(ilKey(Date.now())) - base) / CYCLE);
  return keyOf(base + k * CYCLE);
}

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    try { return await handle(req, env, url); } catch (e) { return bad('תקלה בשרת: ' + String(e && e.message || e).slice(0, 200), 500); }
  },
};
