/* leokmei-print - הפקת קובצי PDF של לאוקמי גירסא (11.10.2026).
   נפרד מ-leokmei-suggest: אין בו הרשאות מנהל ואין בו כתיבה לתוכן. הוא רק פותח את דף המסכת במצב הדפסה
   (?print=1) בדפדפן אחד קבוע של Cloudflare (Browser Rendering), ומחזיר את ה-PDF שהמנוע חישב.
   כך התוצאה זהה בכל דפדפן ובכל מכשיר, כולל טלפון.

   GET /pdf?m=<מסכת>&from=<דף>&to=<דף>[&all=1]&tos=0|1&duplex=0|1&profile=a4
   המטמון: "מה שעומד פעם אחת בשלמות לא מעמדים שוב". המפתח נגזר מן הבקשה, מגרסת דף המסכת (ETag) ומחותמת
   הנוסחים שנבחרו; שינוי בוורד או בבחירת נוסח מייצר מפתח חדש, והישן פג מעצמו. */
import puppeteer from '@cloudflare/puppeteer';

const SITE = 'https://leokmei.com';
const SUGGEST = 'https://leokmei-suggest.m7654301.workers.dev';
const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
  'Access-Control-Allow-Headers': 'content-type, x-admin-key',
  'Access-Control-Expose-Headers': 'X-Cache,X-Pages,Content-Disposition',
  'Access-Control-Max-Age': '86400',
};
const ONE_MSG = 'ניתן להדפיס פרק אחד בכל פעם';
const SLUG_RE = /^[a-z][a-z-]{1,30}$/;
const DAF_RE = /^[א-ת]{1,3}[.:]$/;
const TTL = 60 * 60 * 24 * 14;
const KV_MAX = 24 * 1024 * 1024;

function json(o, status = 200) {
  return new Response(JSON.stringify(o), { status, headers: { 'content-type': 'application/json; charset=utf-8', ...CORS } });
}
async function sha(s) {
  const b = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(s));
  return [...new Uint8Array(b)].map((x) => x.toString(16).padStart(2, '0')).join('').slice(0, 40);
}
function ilDay() { return new Date().toISOString().slice(0, 10); }

async function logPrint(env, key) {
  if (!env.LSTATS) return;
  try {
    const db = env.LSTATS;
    await db.prepare('CREATE TABLE IF NOT EXISTS zs_c (day TEXT NOT NULL, f TEXT NOT NULL, k TEXT NOT NULL, n INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (day, f, k))').run();
    await db.prepare('INSERT INTO zs_c (day, f, k, n) VALUES (?1, ?2, ?3, 1) ON CONFLICT(day, f, k) DO UPDATE SET n = n + 1')
      .bind(ilDay(), 'print', key.slice(0, 120)).run();
  } catch (e) { /* הרישום אינו מעכב את ההפקה */ }
}

/* גבולות הפרקים: <מסכת>.prn.json שהבנייה כותבת ({pages:[[דף, מפתח-פרק],...]}).
   true = כל הדפים שבטווח באותו פרק; false = חוצה גבול או דף לא מוכר; null = הקובץ אינו זמין. */
async function oneChapter(m, from, to) {
  let d;
  try {
    const r = await fetch(`${SITE}/${m}.prn.json`, { cf: { cacheTtl: 300 } });
    if (!r.ok) return null;
    d = await r.json();
  } catch (e) { return null; }
  const pg = d && d.pages;
  if (!Array.isArray(pg) || !pg.length) return null;
  const a = pg.findIndex((x) => x[0] === from);
  const b = pg.findIndex((x) => x[0] === to);
  if (a < 0 || b < 0 || b < a) return false;
  for (let i = a + 1; i <= b; i++) if (pg[i][1] !== pg[a][1]) return false;
  return true;
}

async function pdf(req, env, ctx, url) {
  const q = url.searchParams;
  const m = q.get('m') || '';
  if (!SLUG_RE.test(m)) return json({ error: 'מסכת לא מוכרת' }, 400);
  const all = q.get('all') === '1';
  const from = q.get('from') || '';
  const to = q.get('to') || from;
  if (!all && (!DAF_RE.test(from) || !DAF_RE.test(to))) return json({ error: 'טווח לא תקין' }, 400);
  const tos = q.get('tos') === '1' ? '1' : '0';
  const duplex = q.get('duplex') === '1' ? '1' : '0';
  const profile = /^[a-z0-9]{2,8}$/.test(q.get('profile') || '') ? q.get('profile') : 'a4';

  /* הגבלת ההדפסה (13.10.2026): מבקר רגיל - פרק אחד לכל היותר בכל הפקה. מנהל (x-admin-key תקף) - בלי הגבלה.
     האכיפה כאן, ולא בממשק בלבד: בקשה ישירה לכתובת נבדקת כמו כל בקשה. הבדיקה קודמת למטמון, כדי ש-PDF
     רחב שהפיק מנהל לא יוגש למבקר. אם גבולות הפרקים אינם זמינים - נכשלים סגור. */
  if (!(await isAdmin(req))) {
    if (all) return json({ error: ONE_MSG }, 403);
    const one = await oneChapter(m, from, to);
    if (one === null) return json({ error: 'ההדפסה אינה זמינה כרגע, נסה שוב בעוד רגע' }, 503);
    if (!one) return json({ error: ONE_MSG }, 403);
  }

  /* גרסת התוכן: דף המסכת באתר, ונוסחי התוספות שנבחרו */
  let ver = '';
  try {
    const h = await fetch(`${SITE}/${m}.html`, { method: 'HEAD', cf: { cacheTtl: 60 } });
    if (!h.ok) return json({ error: 'המסכת אינה באתר' }, 404);
    ver = (h.headers.get('etag') || '') + '|' + (h.headers.get('last-modified') || '');
  } catch (e) { return json({ error: 'האתר אינו זמין כרגע' }, 502); }
  let pick = '';
  if (tos === '1') {
    try { const t = await (await fetch(`${SUGGEST}/tos?slug=${encodeURIComponent(m)}`, { cf: { cacheTtl: 30 } })).json(); pick = String(t && t.t || ''); } catch (e) { pick = 'x'; }
  }
  const key = 'print:v1:' + await sha(JSON.stringify([m, all, from, to, tos, duplex, profile, ver, pick]));
  const hn = { kiddushin: 'קידושין' }[m] || m;
  const dfile = (all ? `${hn}.pdf` : `${hn} ${from}${to !== from ? ' - ' + to : ''}.pdf`).replace(/:/g, '꞉');
  const inline = q.get('inline') === '1';
  const head = {
    'content-type': 'application/pdf',
    'content-disposition': `${inline ? 'inline' : 'attachment'}; filename="leokmei-${encodeURIComponent(m)}.pdf"; filename*=UTF-8''${encodeURIComponent('לאוקמי גירסא - ' + dfile)}`,
    'cache-control': 'private, max-age=300',
    ...CORS,
  };

  if (env.STORE) {
    const hit = await env.STORE.get(key, { type: 'arrayBuffer' });
    if (hit) { ctx.waitUntil(logPrint(env, `${m}|${all ? 'all' : 'range'}|tos${tos}|hit`)); return new Response(hit, { headers: { ...head, 'X-Cache': 'HIT' } }); }
  }

  const target = new URLSearchParams({ print: '1', tos, duplex, profile });
  if (all) target.set('all', '1'); else { target.set('from', from); target.set('to', to); }
  let browser;
  try {
    browser = await puppeteer.launch(env.BROWSER);
    const page = await browser.newPage();
    await page.setViewport({ width: 794, height: 1123 });
    await page.goto(`${SITE}/${m}.html?${target.toString()}`, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForFunction("window.__PRN && (window.__PRN.state==='done' || window.__PRN.state==='error')", { timeout: 150000 });
    const st = await page.evaluate('window.__PRN.state');
    if (st !== 'done') {
      const msg = await page.evaluate('window.__PRN.error');
      await browser.close();
      return json({ error: 'העימוד נכשל: ' + String(msg || '').slice(0, 200) }, 500);
    }
    const nPages = await page.evaluate('window.__PRN.report.pages.length');
    const issues = await page.evaluate('window.__PRN.report.issues || []');
    const warns = await page.evaluate('window.__PRN.report.warn || []');
    await page.evaluate('new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))');
    await new Promise((r) => setTimeout(r, 400));
    await page.emulateMediaType('print');
    const buf = await page.pdf({ preferCSSPageSize: true, printBackground: true });
    if (!buf || buf.byteLength < 20000 && !all) { /* קובץ קטן מדי: כנראה ריק */ }
    await browser.close();
    if (env.STORE && buf.byteLength < KV_MAX) {
      ctx.waitUntil(env.STORE.put(key, buf, { expirationTtl: TTL }));
    }
    ctx.waitUntil(logPrint(env, `${m}|${all ? 'all' : 'range'}|tos${tos}|new|${Math.ceil(buf.byteLength / 102400) * 100}KB`));
    if (env.STORE && (issues.length || warns.length)) ctx.waitUntil(saveIssues(env, { m, all, from, to, tos, duplex, profile }, issues, warns));
    return new Response(buf, { headers: { ...head, 'X-Cache': 'MISS', 'X-Pages': String(nPages) } });
  } catch (e) {
    try { if (browser) await browser.close(); } catch (x) { /* */ }
    const msg = String(e && e.message || e);
    if (/429|limit|rate|too many/i.test(msg)) return json({ error: 'השירות עמוס כרגע, נסה שוב בעוד דקה' }, 429);
    return json({ error: 'ההפקה נכשלה: ' + msg.slice(0, 160) }, 500);
  }
}

/* ---- לוח התקלות (למנהל בלבד): מה שהבדיקה האוטומטית של המנוע מצאה בכל הפקה חדשה ---- */
const ISSUES_KEY = 'print:issues:v1';
async function saveIssues(env, req, issues, warns) {
  try {
    const cur = JSON.parse((await env.STORE.get(ISSUES_KEY)) || '[]');
    const ts = Date.now();
    const rows = issues.map((x, i) => ({ id: ts + '-' + i, ts, ...req, ...x }))
      .concat(warns.map((w, i) => ({ id: ts + '-w' + i, ts, ...req, type: 'אזהרת מנוע', detail: String(w).slice(0, 200) })));
    // אותה תקלה באותו מקום אינה נרשמת שוב ושוב
    const seen = new Set(cur.map((x) => [x.m, x.type, x.page, x.daf, x.unit, x.detail].join('|')));
    const fresh = rows.filter((x) => !seen.has([x.m, x.type, x.page, x.daf, x.unit, x.detail].join('|')));
    if (!fresh.length) return;
    await env.STORE.put(ISSUES_KEY, JSON.stringify(fresh.concat(cur).slice(0, 300)));
  } catch (e) { /* */ }
}
async function isAdmin(req) {
  const k = req.headers.get('x-admin-key') || '';
  if (!k) return false;
  try {
    const r = await fetch(`${SUGGEST}/stats/summary?days=1`, { headers: { 'x-admin-key': k } });
    return r.ok;
  } catch (e) { return false; }
}
async function issues(req, env) {
  if (!(await isAdmin(req))) return json({ error: 'למנהל בלבד' }, 403);
  if (req.method === 'POST') {
    let b; try { b = await req.json(); } catch (e) { return json({ error: 'גוף הבקשה אינו JSON' }, 400); }
    const cur = JSON.parse((await env.STORE.get(ISSUES_KEY)) || '[]');
    const it = cur.find((x) => x.id === String(b.id || ''));
    if (!it) return json({ error: 'תקלה לא נמצאה' }, 404);
    if (typeof b.note === 'string') it.note = b.note.slice(0, 1000);
    if (typeof b.done === 'string') it.done = b.done.slice(0, 300);
    if (b.dismiss) it.dismissed = true;
    await env.STORE.put(ISSUES_KEY, JSON.stringify(cur));
    return json({ ok: true });
  }
  const cur = JSON.parse((await env.STORE.get(ISSUES_KEY)) || '[]');
  return json({ ok: true, issues: cur.filter((x) => !x.dismissed) });
}

export default {
  async fetch(req, env, ctx) {
    const url = new URL(req.url);
    if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers: CORS });
    if (url.pathname === '/pdf' && req.method === 'GET') return pdf(req, env, ctx, url);
    if (url.pathname === '/issues') return issues(req, env);
    if (url.pathname === '/health') return json({ ok: true });
    return json({ error: 'לא נמצא' }, 404);
  },
};
