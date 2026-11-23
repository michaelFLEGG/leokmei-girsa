/* sw.js - Service Worker של לאוקמי גירסא (9.10.2026).
   מטרה: מהביקור השני הכול נפתח מיד, גם ברשת חלשה: המעטפת, הגופנים, השער ומפת הש"ס נשמרים במכשיר.
   אסטרטגיה: גופנים, תמונות וקבצים עם גרסה בכתובת (?v=) - מהמטמון מיד. דפים וקובצי נתונים - מהמטמון מיד ועדכון ברקע
   (stale-while-revalidate), כך שתיקון שפורסם מופיע בכניסה הבאה. בקשות לשרת ההצעות וההרשאות אינן נשמרות.
   פרומפט 79: מסכתות שנשמרו ללימוד בלי חיבור (ראה למטה). */
const V = 'lg-__SWV__';
const SHELL = ['./', 'index.html', 'shas.html', 'masechet.html', 'lamed.html', 'quiz.html', 'ui.css', 'lamed.css', 'lamed.js', 'shas.js', 'shas.json',
  'daf-yomi.js', 'hdate.js', 'manifest.webmanifest', 'brand/shaar-v2/shaar-zohar-96.webp', 'brand/shaar-v2/shaar-zohar-560.webp',
  'fonts/vilna-xb.woff2', 'fonts/vilna-r.woff2', 'fonts/vilna-b.woff2', 'fonts/vilna-m.woff2', 'fonts/frank.woff2', 'fonts/frank-b.woff2', 'brand/fonts/vilna-lt.woff2'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(V).then(c => Promise.all(SHELL.map(u => c.add(new Request(u, { cache: 'reload' })).catch(() => { })))).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k.indexOf('lg-') === 0 && k !== V).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});

/* פרומפט 79 (23.11.2026): לימוד בלי חיבור. מסכת שהלומד שמר יושבת במטמון משלה (lgs-<מסכת>), שאינו נמחק בעדכון
   גרסה (רק מטמוני lg- נמחקים ב-activate). כשאין רשת, כל בקשה שלא נמצאה במטמון הרגיל נענית מן המסכתות השמורות. */
const SAVED = 'lgs-';
function anyMatch(req) {
  return caches.match(req).then(hit => hit || (req.mode === 'navigate' ? caches.match(req, { ignoreSearch: true }) : undefined))
    .then(hit => hit || Response.error());
}
function savedMatch(req) {
  return caches.keys().then(ks => {
    const sv = ks.filter(k => k.indexOf(SAVED) === 0);
    return sv.reduce((p, k) => p.then(hit => hit || caches.open(k).then(c => c.match(req))), Promise.resolve(undefined));
  });
}
function swr(req, cache) {
  return cache.match(req).then(hit => {
    const net = fetch(req).then(res => { if (res && res.ok && res.type === 'basic') cache.put(req, res.clone()); return res; })
      .catch(() => hit || anyMatch(req));
    return hit || net;
  });
}
function cacheFirst(req, cache) {
  return cache.match(req).then(hit => hit || savedMatch(req).then(sv => sv ||
    fetch(req).then(res => { if (res && res.ok && res.type === 'basic') cache.put(req, res.clone()); return res; }).catch(() => anyMatch(req))));
}
self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const u = new URL(req.url);
  if (u.origin !== location.origin) return;
  if (u.pathname.indexOf('/api') === 0 || u.pathname.endsWith('edited-pages.json') || u.pathname.endsWith('status.json')) return;
  if (req.headers.get('range')) return;
  const p = u.pathname;
  const stat = /\/(fonts|brand)\//.test(p) || /\.(woff2?|otf|ttf|webp|png|svg|ico)$/.test(p) || (u.search.indexOf('v=') > -1 && /\.(css|js)$/.test(p));
  e.respondWith(caches.open(V).then(c => stat ? cacheFirst(req, c) : swr(req, c)).catch(() => fetch(req).catch(() => anyMatch(req))));
});

/* שמירת מסכת: הדף שולח את רשימת הקבצים. קובץ שגרסתו בכתובת (?v=) וכבר שמור - אינו יורד שוב. שאר הקבצים נבדקים
   מול השרת (no-cache: תשובת 304 כשלא השתנו). רק אחרי שהכול ירד, נמחקים מן השמירה קבצים שאינם ברשימה (גרסאות ישנות). */
async function saveSet(slug, urls) {
  const c = await caches.open(SAVED + slug);
  const have = new Set((await c.keys()).map(r => new URL(r.url).pathname + new URL(r.url).search));
  let n = 0, bytes = 0, failed = 0, skipped = 0;
  const want = new Set();
  const one = async path => {
    const url = new URL(path, self.registration.scope);
    const key = url.pathname + url.search;
    want.add(key);
    try {
      if (url.search.indexOf('v=') > -1 && have.has(key)) {
        const r0 = await c.match(url.href); if (r0) { n++; bytes += +(r0.headers.get('content-length') || 0); return; }
      }
      const res = await fetch(url.href, { cache: 'no-cache', credentials: 'same-origin' });
      /* קובץ שאינו קיים (4xx) אינו מכשיל את השמירה: הוא פשוט אינו נשמר. רק תקלת רשת או שרת מכשילה */
      if (!res.ok || res.type !== 'basic') { if (res.status >= 400 && res.status < 500) skipped++; else failed++; return; }
      const b = await res.clone().blob();
      await c.put(url.href, res);
      n++; bytes += b.size;
    } catch (e) { failed++; }
  };
  const list = urls.slice();
  const workers = Array.from({ length: 4 }, async () => { while (list.length) await one(list.shift()); });
  await Promise.all(workers);
  if (failed) return { ok: false, n, bytes, failed, skipped };
  for (const r of await c.keys()) { const u = new URL(r.url); if (!want.has(u.pathname + u.search)) await c.delete(r); }
  return { ok: true, n, bytes, failed, skipped };
}
self.addEventListener('message', e => {
  const d = e.data || {}, port = e.ports && e.ports[0];
  const reply = x => { if (port) port.postMessage(x); };
  if (d.type === 'lg-save' && d.slug && Array.isArray(d.urls)) e.waitUntil(saveSet(String(d.slug), d.urls).then(reply, () => reply({ ok: false })));
  else if (d.type === 'lg-remove' && d.slug) e.waitUntil(caches.delete(SAVED + d.slug).then(() => reply({ ok: true })));
  else if (d.type === 'lg-list') e.waitUntil(caches.keys().then(ks => reply({ ok: true, saved: ks.filter(k => k.indexOf(SAVED) === 0).map(k => k.slice(SAVED.length)) })));
});
