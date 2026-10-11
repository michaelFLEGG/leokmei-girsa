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
  'Access-Control-Allow-Methods': 'GET,OPTIONS',
  'Access-Control-Allow-Headers': 'content-type',
  'Access-Control-Expose-Headers': 'X-Cache,X-Pages,Content-Disposition',
  'Access-Control-Max-Age': '86400',
};
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
  const dfile = all ? `${m}.pdf` : `${m}-${from}-${to}.pdf`;
  const head = {
    'content-type': 'application/pdf',
    'content-disposition': `attachment; filename="leokmei-${encodeURIComponent(m)}.pdf"; filename*=UTF-8''${encodeURIComponent('לאוקמי גירסא - ' + dfile)}`,
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
    const buf = await page.pdf({ preferCSSPageSize: true, printBackground: true });
    await browser.close();
    if (env.STORE && buf.byteLength < KV_MAX) {
      ctx.waitUntil(env.STORE.put(key, buf, { expirationTtl: TTL }));
    }
    ctx.waitUntil(logPrint(env, `${m}|${all ? 'all' : 'range'}|tos${tos}|new|${Math.ceil(buf.byteLength / 102400) * 100}KB`));
    return new Response(buf, { headers: { ...head, 'X-Cache': 'MISS', 'X-Pages': String(nPages) } });
  } catch (e) {
    try { if (browser) await browser.close(); } catch (x) { /* */ }
    const msg = String(e && e.message || e);
    if (/429|limit|rate|too many/i.test(msg)) return json({ error: 'השירות עמוס כרגע, נסה שוב בעוד דקה' }, 429);
    return json({ error: 'ההפקה נכשלה: ' + msg.slice(0, 160) }, 500);
  }
}

export default {
  async fetch(req, env, ctx) {
    const url = new URL(req.url);
    if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers: CORS });
    if (url.pathname === '/pdf' && req.method === 'GET') return pdf(req, env, ctx, url);
    if (url.pathname === '/health') return json({ ok: true });
    return json({ error: 'לא נמצא' }, 404);
  },
};
