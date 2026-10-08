/* lamed - סנכרון בין מכשירים, הצעות התיקון של הלומד, וסטטיסטיקה אנונימית למנהל.
   הכול אופציונלי ונכשל בשקט: הלימוד אינו תלוי ברשת. נקודת הקליטה היא אותה נקודה
   שמקבלת הצעות תיקון (leokmei-suggest), והנתונים יושבים במחסן הפרטי שלה
   ולא במאגר הציבורי. */
(function () {
  'use strict';
  var LG = window.LAMED, S = LG.sync = {};
  var API = 'https://leokmei-suggest.m7654301.workers.dev';
  try { API = localStorage.getItem('lg-lamed-api') || API; } catch (e) { }   /* בדיקות מול נקודה מקומית */

  function ls(k, v) { try { if (v === undefined) return localStorage.getItem(k); if (v === null) localStorage.removeItem(k); else localStorage.setItem(k, v); } catch (e) { } return null; }
  function rnd(n) { var a = new Uint8Array(n), s = ''; (window.crypto || window.msCrypto).getRandomValues(a); for (var i = 0; i < n; i++) s += 'abcdefghijklmnopqrstuvwxyz0123456789'[a[i] % 36]; return s; }
  S.identity = function () {
    var pid = ls('lg-pid') || '', pt = ls('lg-pt') || '';
    if (!pid || !pt) { pid = rnd(14); pt = rnd(32); ls('lg-pid', pid); ls('lg-pt', pt); }
    return { pid: pid, pt: pt };
  };
  function isBot() { return !!(navigator.webdriver) || /bot|crawl|spider|slurp|headless/i.test(navigator.userAgent || ''); }
  async function api(path, opt) {
    var o = Object.assign({ headers: {} }, opt || {});
    o.headers['content-type'] = 'application/json; charset=utf-8';
    var r = await fetch(API + path, o), j = null;
    try { j = await r.json(); } catch (e) { }
    if (!r.ok || !j || !j.ok) throw new Error((j && j.error) || ('שגיאה ' + r.status));
    return j;
  }
  S.base = API;
  function pApi(path, body) {
    var id = S.identity(), o = { method: body ? 'POST' : 'GET', headers: { 'x-proposer': id.pt } };
    if (body) o.body = JSON.stringify(Object.assign({ pid: id.pid }, body));
    return api(path + (body ? '' : (path.indexOf('?') > -1 ? '&' : '?') + 'pid=' + id.pid), o);
  }

  S.api = api; S.pApi = function (path, body) { return pApi(path, body); };

  /* ---------------- סנכרון: איחוד אירועים לפי מזהה, בלי דריסה ---------------- */
  S.linked = function () { return ls('lg-lamed-sync') === '1'; };
  S.pushPull = async function () {
    if (!S.linked() || window.__lmDemo) return 0;
    var ev = LG.events().filter(function (e) { return e.k !== 'ss' || (e.t1 && Date.now() - e.t1 > 60000) || true; });
    var j = await pApi('/ln/sync', { ev: JSON.parse(LG.exportJSON()).ev });
    var n = 0;
    (j.ev || []).forEach(function (e) { if (e && e.id) { var had = LG.events().some(function (x) { return x.id === e.id; }); if (!had) { LG.put(e, true); n++; } } });
    if (n) LG.notify();
    return n;
  };
  S.makeCode = async function () {
    ls('lg-lamed-sync', '1');
    await S.pushPull().catch(function () { });
    var j = await pApi('/ln/code', {});
    return j.code;
  };
  S.redeem = async function (code) {
    var j = await api('/ln/redeem', { method: 'POST', body: JSON.stringify({ code: String(code).trim().toUpperCase() }) });
    var mine = JSON.parse(LG.exportJSON()).ev;
    ls('lg-pid', j.pid); ls('lg-pt', j.pt); ls('lg-lamed-sync', '1');
    /* ההיסטוריה שכבר היתה במכשיר הזה מצטרפת לחשבון, ולא נמחקת */
    var n = 0;
    var r = await pApi('/ln/sync', { ev: mine });
    (r.ev || []).forEach(function (e) { if (e && e.id && !LG.events().some(function (x) { return x.id === e.id; })) { LG.put(e, true); n++; } });
    LG.notify();
    return n;
  };
  var syncT = null;
  S.auto = function () {
    if (!S.linked()) return;
    var go = function () { S.pushPull().catch(function () { }); };
    go();
    addEventListener('online', go);
    LG.onChange(function () { clearTimeout(syncT); syncT = setTimeout(go, 15000); });
  };

  /* ---------------- הצעות התיקון של הלומד (מתוך המערכת הקיימת, לא מאגר נפרד) ---------------- */
  S.loadSugg = async function () {
    try {
      var j = await pApi('/mine'), rows = j.rows || [];
      var s = { total: rows.length, pending: 0, approved: 0, refined: 0, rejected: 0, bySlug: {} };
      rows.forEach(function (r) {
        if (r.st === 'pending') s.pending++; else if (r.st === 'accepted') s.approved++; else if (r.st === 'edited') s.refined++; else if (r.st === 'rejected') s.rejected++;
        var b = s.bySlug[r.slug] || (s.bySlug[r.slug] = {});
        if (r.daf) b[r.daf] = (b[r.daf] || 0) + 1;
      });
      LG.sugg = s;
      LG.notify && LG.notify();
      return s;
    } catch (e) { return null; }
  };


  /* ---------------- "לומדים כעת": פעימה אנונימית (מזהה התקנה אקראי, בלי שם ובלי pid) ----------------
     נשלחת רק כשהלומד פעיל (קורא או מתרגל), לכל היותר אחת ב-150 שניות. */
  S.heartbeat = function (slug) {
    if (window.__lmDemo || isBot() || LG.settings().share === false) return;
    var aid = ls('lg-lamed-aid'); if (!aid) { aid = rnd(12); ls('lg-lamed-aid', aid); }
    api('/ln/online', { method: 'POST', body: JSON.stringify({ aid: aid, s: slug || '' }) }).catch(function () { });
  };
  S.online = function (slug) {
    return api('/ln/online' + (slug ? '?s=' + encodeURIComponent(slug) : ''), { method: 'GET' }).catch(function () { return null; });
  };

  /* ---------------- סטטיסטיקה אנונימית ומצטברת ---------------- */
  S.stat = function (o) {
    if (window.__lmDemo || isBot()) return;
    if (LG.settings().share === false) return;
    var aid = ls('lg-lamed-aid'); if (!aid) { aid = rnd(12); ls('lg-lamed-aid', aid); }
    try {
      var q = JSON.parse(ls('lg-lamed-statq') || '[]'); q.push(Object.assign({ aid: aid, t: Date.now() }, o)); ls('lg-lamed-statq', JSON.stringify(q.slice(-60)));
    } catch (e) { }
    clearTimeout(S._st); S._st = setTimeout(S.flushStats, 8000);
  };
  S.flushStats = async function () {
    var q = []; try { q = JSON.parse(ls('lg-lamed-statq') || '[]'); } catch (e) { }
    if (!q.length) return;
    try { await api('/ln/stat', { method: 'POST', body: JSON.stringify({ ev: q }) }); ls('lg-lamed-statq', '[]'); } catch (e) { /* ננסה בפעם הבאה */ }
  };
  S.stats = async function (key, demo) {
    if (demo) return demoStats();
    return api('/ln/stats', { method: 'GET', headers: { 'x-admin-key': key } }).then(function (j) { return j.data; });
  };
  function demoStats() {
    var ms = LG.masechtot().filter(function (m) { return m.built; });
    var byM = ms.map(function (m, i) { return { s: m.slug, reads: 900 - i * 31, ms: (900 - i * 31) * 420000 }; });
    var top = [], ab = [], slow = [];
    ms.slice(0, 6).forEach(function (m, i) { (m.dafim || []).slice(i * 3, i * 3 + 4).forEach(function (d, j) {
      top.push({ s: m.slug, d: d[0], reads: 140 - i * 9 - j * 7, unedited: !(m.slug === 'bekhorot' && i < 2) });
      ab.push({ s: m.slug, d: d[0], starts: 90 - i * 5, done: 60 - i * 6 - j * 3 });
      slow.push({ s: m.slug, d: d[0], avg: (11 + i + j) * 60000, n: 40 + j });
    }); });
    return { totals: { today: 23, week: 118, month: 346, finished: 9 }, byMasechet: byM, topPages: top, abandon: ab, slow: slow };
  }
})();
