/* leokmei-daf - "הדף היומי בווטסאפ" של לאוקמי גירסא (פרומפט 23, 8.11.2026).
 *
 * הועתק מלוח "הזוהר היומי" של ממלכת הזוהר (functions/api/_lib/zyomi.js, functions/api/zyomi/[[path]].js,
 * zyomi-cron-worker, זוהר-דף-כלים/zyomi/ווטסאפ-עצמאי.mjs), שהועתק בשעתו מ"אמרת היום" של שפע יואל,
 * ושונו רק: מקור התוכן (הגמרא של הדף היומי, data/daf-wa באתר), מבנה ההודעה (טקסט בלי תמונה; הכרטיס
 * הוא התצוגה המקדימה של הקישור), היעד (קבוצת ההכרזות "לאוקמי גירסא - הדף היומי"), והשעה (06:00).
 * נפרד לגמרי מממלכת הזוהר: בלי קוד משותף בזמן ריצה ובלי נתונים משותפים.
 *
 * כללים (סעיפים 2, 5, 8 בפרומפט):
 *  א. לעולם לא בשבת וביום טוב. בשישי ובערב חג - הדפים של הימים שאין בהם שליחה יוצאים יחד, בהודעה אחת.
 *  ב. תוכן שחסר, או שלא עבר את הבודק (check.ok) - אינו יוצא, ולעולם אין הודעת "בהכנה".
 *  ג. שלושת ימי השליחה הראשונים - רק אחרי "אשר" בלוח. מן הרביעי - אוטומטי בשעה שנקבעה (ברירת מחדל 06:00).
 *  ד. כל התערבות של המנהל (עריכה, בחירת "הידעת", עצירה, שעה, אישור) נרשמת ביומן הלמידה, שהכותב קורא לפני כל כתיבה.
 *  ה. מצב החיבור לווטסאפ (own:sess) אינו יוצא לעולם לדפדפן; רק לריצת השולח (OIDC של daf-wa.yml).
 */

const SITE = 'https://leokmei.com';
const TZ = 'Asia/Jerusalem';
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

/* ---------- זמן ותאריך עברי (Intl, כמו zyomi-cal) ---------- */
const DAY = 86400000;
let fmtD = null, fmtT = null, fmtH = null;
const ilKey = (ms) => (fmtD = fmtD || new Intl.DateTimeFormat('en-CA', { timeZone: TZ, year: 'numeric', month: '2-digit', day: '2-digit' })).format(new Date(ms));
function ilHM(ms) { fmtT = fmtT || new Intl.DateTimeFormat('en-GB', { timeZone: TZ, hour: '2-digit', minute: '2-digit', hour12: false }); return fmtT.format(new Date(ms)).replace(/^24/, '00'); }
const dn = (k) => Math.floor(Date.UTC(+k.slice(0, 4), +k.slice(5, 7) - 1, +k.slice(8, 10)) / DAY);
const keyOf = (n) => new Date(n * DAY).toISOString().slice(0, 10);
const addDays = (k, i) => keyOf(dn(k) + i);
const dow = (k) => ((dn(k) % 7) + 11) % 7;   // 0 ראשון ... 6 שבת
function heb(k) {
  fmtH = fmtH || new Intl.DateTimeFormat('en-u-ca-hebrew', { timeZone: 'UTC', day: 'numeric', month: 'long', year: 'numeric' });
  const o = { d: 0, mn: '', y: 0 };
  fmtH.formatToParts(new Date(dn(k) * DAY + 43200000)).forEach((p) => { if (p.type === 'day') o.d = +p.value; else if (p.type === 'month') o.mn = p.value; else if (p.type === 'year') o.y = +p.value; });
  return o;
}
const L1 = [[400, 'ת'], [300, 'ש'], [200, 'ר'], [100, 'ק'], [90, 'צ'], [80, 'פ'], [70, 'ע'], [60, 'ס'], [50, 'נ'], [40, 'מ'], [30, 'ל'], [20, 'כ'], [10, 'י'], [9, 'ט'], [8, 'ח'], [7, 'ז'], [6, 'ו'], [5, 'ה'], [4, 'ד'], [3, 'ג'], [2, 'ב'], [1, 'א']];
function letters(n) { if (n === 15) return 'טו'; if (n === 16) return 'טז'; let t = ''; for (const [v, c] of L1) while (n >= v) { t += c; n -= v; } return t.replace(/יה$/, 'טו').replace(/יו$/, 'טז'); }
const gq = (n) => { const t = letters(n); return t.length > 1 ? t.slice(0, -1) + '"' + t.slice(-1) : t + "'"; };
const MONTH_B = { Tishri: 'בתשרי', Heshvan: 'בחשון', Kislev: 'בכסלו', Tevet: 'בטבת', Shevat: 'בשבט', Adar: 'באדר', 'Adar I': "באדר א'", 'Adar II': "באדר ב'",
  Nisan: 'בניסן', Iyar: 'באייר', Sivan: 'בסיון', Tamuz: 'בתמוז', Av: 'באב', Elul: 'באלול' };
const DOW = ['יום ראשון', 'יום שני', 'יום שלישי', 'יום רביעי', 'יום חמישי', 'יום שישי', 'שבת קודש'];
// ימים טובים (לוח ארץ ישראל) - אין שליחה. מועתק מ-zyomi.js
const YT = [['Tishri', 1, 'ראש השנה'], ['Tishri', 2, 'ראש השנה'], ['Tishri', 10, 'יום הכיפורים'], ['Tishri', 15, 'סוכות'],
  ['Tishri', 22, 'שמיני עצרת'], ['Nisan', 15, 'פסח'], ['Nisan', 21, 'שביעי של פסח'], ['Sivan', 6, 'שבועות']];
function dayMeta(k) {
  const h = heb(k), w = dow(k);
  const yt = YT.filter(([m, d]) => m === h.mn && d === h.d).map((x) => x[2]);
  const holy = w === 6 || yt.length > 0;
  const hebStr = gq(h.d) + ' ' + (MONTH_B[h.mn] || h.mn) + ' ה' + gq(h.y % 1000);
  return { d: k, dow: w, heb: hebStr, line: (w === 6 ? 'שבת קודש' : DOW[w]) + ' ' + hebStr, noSend: holy, why: w === 6 ? 'שבת' : (yt[0] || '') };
}

/* ---------- הדף היומי (אותו חישוב כמו daf-yomi.js באתר) ---------- */
const L = [['ברכות', 'berakhot', 2, 63], ['שבת', 'shabbat', 2, 156], ['עירובין', 'eruvin', 2, 104], ['פסחים', 'pesachim', 2, 120],
  ['שקלים', 'shekalim', 2, 21], ['יומא', 'yoma', 2, 87], ['סוכה', 'sukkah', 2, 55], ['ביצה', 'beitzah', 2, 39],
  ['ראש השנה', 'rosh-hashanah', 2, 34], ['תענית', 'taanit', 2, 30], ['מגילה', 'megillah', 2, 31], ['מועד קטן', 'moed-katan', 2, 28],
  ['חגיגה', 'chagigah', 2, 26], ['יבמות', 'yevamot', 2, 121], ['כתובות', 'ketubot', 2, 111], ['נדרים', 'nedarim', 2, 90],
  ['נזיר', 'nazir', 2, 65], ['סוטה', 'sotah', 2, 48], ['גיטין', 'gittin', 2, 89], ['קידושין', 'kiddushin', 2, 81],
  ['בבא קמא', 'bava-kamma', 2, 118], ['בבא מציעא', 'bava-metzia', 2, 118], ['בבא בתרא', 'bava-batra', 2, 175],
  ['סנהדרין', 'sanhedrin', 2, 112], ['מכות', 'makkot', 2, 23], ['שבועות', 'shevuot', 2, 48], ['עבודה זרה', 'avodah-zarah', 2, 75],
  ['הוריות', 'horayot', 2, 13], ['זבחים', 'zevachim', 2, 119], ['מנחות', 'menachot', 2, 109], ['חולין', 'chullin', 2, 141],
  ['בכורות', 'bekhorot', 2, 60], ['ערכין', 'arakhin', 2, 33], ['תמורה', 'temurah', 2, 33], ['כריתות', 'keritot', 2, 27],
  ['מעילה', 'meilah', 2, 21], ['קינים', 'kinnim', 23, 3], ['תמיד', 'tamid', 26, 8], ['מדות', 'middot', 34, 5], ['נדה', 'niddah', 3, 71]];
const CYCLE = L.reduce((a, x) => a + x[3], 0);
function dafOf(k) {
  let i = ((dn(k) - dn('2020-01-05')) % CYCLE + CYCLE) % CYCLE;
  for (const [name, slug, first, cnt] of L) { if (i < cnt) return { name, slug, n: first + i, last: first + cnt - 1 }; i -= cnt; }
}

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

/** הדפים שיוצאים בהודעה של יום k: הדף של היום, ואחריו הדפים של הימים הבאים שאין בהם שליחה (שבת, יום טוב) */
function dafimFor(k) {
  const out = [dafOf(k)];
  for (let i = 1; i < 4; i++) { const m = dayMeta(addDays(k, i)); if (!m.noSend) break; out.push(dafOf(m.d)); }
  return out;
}

/* ---------- הרכבת ההודעה (סעיף 2) ---------- */
const lineOf = (c, i, bold) => '◂ ' + (bold ? '*' + c.lines[i].t.replace(/\*/g, '') + '*' : c.lines[i].t);
function compose(meta, items, rec) {
  const first = items[0], c0 = first.c;
  const pick = rec && Number.isInteger(rec.pick) && c0.alts && c0.alts[rec.pick] ? c0.alts[rec.pick] : null;
  const hook = pick || c0.hook;
  const same = items.every((x) => x.slug === first.slug);
  const labels = items.map((x) => gq(x.n));
  const title = '*הדף היומי · ' + first.name + ' ' + (same ? labels.join('-') : labels[0]) + (same ? '' : ' ועוד') + '*';
  const out = ['leokmei.com/daf/' + first.slug + '-' + first.n, title, meta.line, '', '*הידעת?*', hook.q, ''];
  items.forEach((x, j) => {
    out.push(items.length > 1 ? '*' + x.name + ' ' + gq(x.n) + ' בקצרה*' : '*הדף בקצרה*');
    x.c.lines.forEach((_, i) => out.push(lineOf(x.c, i, j === 0 && i === hook.ans)));
    if (j > 0) out.push('לדף המלא: leokmei.com/daf/' + x.slug + '-' + x.n);
    out.push('');
  });
  const last = items[items.length - 1], left = last.last - last.n;
  out.push(left > 0 ? 'עוד ' + left + (left === 1 ? ' דף' : ' דפים') + ' לסיום ' + last.name : 'היום מסיימים את מסכת ' + last.name);
  return out.join('\n');
}

/** כל מה שהלוח והשולח צריכים לדעת על יום אחד */
async function dayView(env, k, cfg) {
  const meta = dayMeta(k), rec = await jget(env, 'day:' + k, {}) || {};
  const dafim = dafimFor(k);
  const items = [];
  for (const x of dafim) items.push(Object.assign({}, x, { c: await content(x.slug, x.n) }));
  const missing = items.filter((x) => !hasOk(x.c)).map((x) => x.name + ' ' + gq(x.n));
  const auto = missing.length ? '' : compose(meta, items, rec);
  const text = rec.text || auto;
  const sent = (cfg.sent || 0);
  const needApprove = sent < APPROVE_FIRST;
  let state;
  if (meta.noSend) state = 'holy';
  else if (rec.sentAt) state = 'sent';
  else if (rec.status === 'stopped') state = 'stopped';
  else if (missing.length) state = 'missing';
  else if (needApprove && rec.status !== 'approved') state = 'await';
  else state = rec.status === 'approved' ? 'approved' : 'auto';
  return {
    d: k, meta, state, text, auto, edited: !!rec.text, pick: Number.isInteger(rec.pick) ? rec.pick : null, time: rec.time || SEND_HM,
    sentAt: rec.sentAt || 0, err: rec.err || '', needApprove, missing,
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
const b64u = (s) => Uint8Array.from(atob(s.replace(/-/g, '+').replace(/_/g, '/')), (c) => c.charCodeAt(0));
const part = (s) => JSON.parse(new TextDecoder().decode(b64u(s)));
async function isSender(req) {
  try {
    const jwt = req.headers.get('x-board-oidc') || '';
    const [h, p, sig] = jwt.split('.');
    if (!sig) return false;
    const head = part(h), c = part(p), t = Date.now() / 1000;
    if (head.alg !== 'RS256' || c.iss !== ISS || c.aud !== AUD) return false;
    if (String(c.repository || '').toLowerCase() !== REPO) return false;
    if (!String(c.workflow_ref || '').toLowerCase().startsWith(WF)) return false;
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
          await mark(env, c.d);
          return json({ ok: true, mode: 'send', d: c.d, group: cfg.announce, text: v.text, sess });
        }
        if (c.op === 'test') {
          const v = await dayView(env, c.d || ilKey(Date.now()), cfg);
          return json({ ok: true, mode: 'test', d: c.d || '', text: v.text || 'בדיקה', sess });
        }
        return json({ ok: true, mode: c.op, name: c.name || '', sess });
      }
      if (!x.send) return json({ ok: true, mode: 'none', why: x.v ? x.v.state : '' });
      if (!cfg.announce) return json({ ok: true, mode: 'none', why: 'קבוצת ההכרזות לא הוקמה' });
      await mark(env, x.v.d);
      return json({ ok: true, mode: 'send', d: x.v.d, group: cfg.announce, text: x.v.text, sess });
    }
    let b = {};
    try { b = await req.json(); } catch (e) { return bad('גוף הבקשה אינו JSON'); }
    if (p === '/wa-sess') {
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
        pilot.push({ d: k, meta, state: hasOk(c) ? (rec.status === 'approved' ? 'approved' : 'pilot') : 'missing', text: rec.text || (hasOk(c) ? compose(meta, [it], rec) : ''),
          auto: hasOk(c) ? compose(meta, [it], rec) : '', edited: !!rec.text, pick: Number.isInteger(rec.pick) ? rec.pick : null, time: SEND_HM, sentAt: 0, err: '', needApprove: true, missing: hasOk(c) ? [] : ['בכורות ' + gq(n)],
          dafim: [{ slug: 'bekhorot', n, label: 'בכורות ' + gq(n), url: SITE + '/daf/bekhorot-' + n, og: SITE + '/daf/og/bekhorot-' + n + '.jpg', hook: c && c.hook, alts: (c && c.alts) || [], card: c && c.card, checked: hasOk(c) }] });
      }
    }
    const own = await jget(env, 'own', { linked: false });
    const last = await jget(env, 'last', null);
    return json({ ok: true, today, days, pilot, own: { linked: !!own.linked, at: own.at || '', why: own.why || '' }, cfg: { announce: !!cfg.announce, name: cfg.name || '', invite: cfg.invite || '', sent: cfg.sent || 0, approveFirst: APPROVE_FIRST }, last, cmd: await jget(env, 'cmd', null) });
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
    rec.status = 'approved'; rec.approvedAt = Date.now(); delete rec.tries; delete rec.tryAt; await jput(env, rk, rec);
    await learn(env, { kind: 'sendnow', d });
    await jput(env, 'cmd', { op: 'send', d, at: Date.now() });
    return json({ ok: true });
  }
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
