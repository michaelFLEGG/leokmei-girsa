/* sw.js - Service Worker של לאוקמי גירסא (9.10.2026).
   מטרה: מהביקור השני הכול נפתח מיד, גם ברשת חלשה: המעטפת, הגופנים, השער ומפת הש"ס נשמרים במכשיר.
   אסטרטגיה: גופנים, תמונות וקבצים עם גרסה בכתובת (?v=) - מהמטמון מיד. דפים וקובצי נתונים - מהמטמון מיד ועדכון ברקע
   (stale-while-revalidate), כך שתיקון שפורסם מופיע בכניסה הבאה. בקשות לשרת ההצעות וההרשאות אינן נשמרות. */
const V = 'lg-__SWV__';
const SHELL = ['./', 'index.html', 'shas.html', 'masechet.html', 'lamed.html', 'quiz.html', 'ui.css', 'lamed.css', 'lamed.js', 'shas.js', 'shas.json',
  'daf-yomi.js', 'hdate.js', 'manifest.webmanifest', 'brand/shaar-v2/shaar-zohar-96.webp', 'brand/shaar-v2/shaar-zohar-560.webp',
  'brand/fonts/vilna-xb.woff2', 'brand/fonts/vilna-rg.woff2', 'brand/fonts/vilna-bd.woff2', 'brand/fonts/vilna-md.woff2', 'brand/fonts/vilna-lt.woff2'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(V).then(c => Promise.all(SHELL.map(u => c.add(new Request(u, { cache: 'reload' })).catch(() => { })))).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k.indexOf('lg-') === 0 && k !== V).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});

function swr(req, cache) {
  return cache.match(req).then(hit => {
    const net = fetch(req).then(res => { if (res && res.ok && res.type === 'basic') cache.put(req, res.clone()); return res; }).catch(() => hit);
    return hit || net;
  });
}
function cacheFirst(req, cache) {
  return cache.match(req).then(hit => hit || fetch(req).then(res => { if (res && res.ok && res.type === 'basic') cache.put(req, res.clone()); return res; }));
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
  e.respondWith(caches.open(V).then(c => stat ? cacheFirst(req, c) : swr(req, c)).catch(() => fetch(req)));
});
