/* lamed - הרצה ומצב הדגמה.
   מצב הדגמה (?demo=casual|regular|yomi|scholar|suggester) טוען לומד בדוי עם היסטוריה
   של 90 יום, בזיכרון בלבד: אינו נוגע בנתונים אמיתיים ואינו נשמר. */
(function () {
  'use strict';
  var LG = window.LAMED, UI = LG.ui;

  function mulberry(a) { return function () { a |= 0; a = a + 0x6D2B79F5 | 0; var t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }

  var DEMOS = {
    casual: 'מבקר מזדמן', regular: 'לומד קבוע בברכות', yomi: 'לומד הדף היומי בבכורות', scholar: 'תלמיד חכם: חזרות על סוכה', suggester: 'מציע עם 40 הצעות'
  };
  LG.demoNames = DEMOS;

  function day(off) { return LG.addDays(LG.ymd(Date.now()), -off); }
  function at(ymd, h, mi) { return LG.ymdToUTC(ymd) + (h * 60 + mi) * 60000 - 2 * 3600000; }   /* קירוב לשעון ישראל */

  function gen(name) {
    var r = mulberry(name.split('').reduce(function (a, c) { return a * 31 + c.charCodeAt(0); }, 7));
    var ev = [], id = 0;
    function E(o) { o.id = 'd' + name + (id++); ev.push(o); }
    function session(ymd, h, mi, mins, slug, dafs) {
      var per = {}, each = Math.round(mins * 60000 / dafs.length);
      dafs.forEach(function (d) { per[slug + '|' + d] = each; });
      var t0 = at(ymd, h, mi);
      E({ k: 'ss', t: t0, t0: t0, t1: t0 + mins * 60000, ms: each * dafs.length, s: slug, per: per });
    }
    function done(ymd, h, mi, slug, d, mins) { E({ k: 'dn', t: at(ymd, h, mi) + 1000, s: slug, d: d, ms: Math.round(mins * 60000), how: 'auto' }); }
    function amudList(slug) { return LG.amudim(slug).map(function (a) { return a.daf; }); }
    var built = LG.masechtot().filter(function (m) { return m.built; }).map(function (m) { return m.slug; });
    function has(s) { return built.indexOf(s) > -1 ? s : built[0]; }
    function place(slug, daf, ago) {
      var pg = null;
      E({ k: 'ps', id: 'ps-' + slug, s: slug, d: daf, pid: 0, fp: '', t: Date.now() - ago * 86400000 });
    }
    if (name === 'casual') {
      var s = has('berakhot'), L = amudList(s);
      [80, 61, 40, 33, 20, 12, 9, 4, 2].forEach(function (a, i) { session(day(a), 20 + (i % 3), 10, 8 + Math.round(r() * 10), s, [L[i], L[i + 1]]); if (i % 3 === 0) done(day(a), 20, 30, s, L[i], 7); });
      place(s, L[8], 2);
      E({ k: 'cf', key: 'types', val: ['visitor'], t: Date.now() - 90 * 86400000 });
    } else if (name === 'regular') {
      var s2 = has('berakhot'), L2 = amudList(s2), n = Math.round(L2.length * 0.6);
      for (var i = 0; i < 90; i++) {
        if (r() < 0.12) continue;
        var idx = Math.min(n - 2, Math.floor(i / 90 * n)), m = 18 + Math.round(r() * 22);
        var a = 90 - i - 1;
        session(day(a), 5, 30 + Math.round(r() * 25), m, s2, [L2[idx], L2[idx + 1]]);
      }
      for (var k = 0; k < n; k++) done(day(Math.max(0, 90 - Math.floor(k / n * 89) - 1)), 6, 10, s2, L2[k], 8 + r() * 8);
      place(s2, L2[n], 0);
      E({ k: 'cf', key: 'types', val: ['regular'], t: Date.now() - 90 * 86400000 });
      E({ k: 'cf', key: 'my', val: [s2], t: Date.now() - 90 * 86400000 });
      var end = LG.addDays(LG.ymd(Date.now()), 120), g = {}; g[s2] = { end: end, minutes: 25, perWeek: 0 };
      E({ k: 'cf', key: 'goals', val: g, t: Date.now() - 80 * 86400000 });
    } else if (name === 'yomi') {
      var sb = has('bekhorot'), Lb = amudList(sb), t = LGDaf.forStr(LG.ymd(Date.now()));
      var skip = [1, 2, 3];       /* פער של שלושה ימים */
      for (var j = 60; j >= 0; j--) {
        if (skip.indexOf(j) > -1) continue;
        var ds = day(j), inf = LGDaf.forStr(ds);
        if (inf.slug === sb) {
          var a1 = LG.dafLabel(inf.n, 0), a2 = LG.dafLabel(inf.n, 1);
          session(ds, 6, 0, 22, sb, [a1, a2]); done(ds, 6, 20, sb, a1, 10); done(ds, 6, 22, sb, a2, 11);
        } else if (r() < 0.8) {
          E({ k: 'ex', s: inf.slug, from: LG.dafLabel(inf.n, 0), to: LG.dafLabel(inf.n, 1), t: at(ds, 7, 0) });
        }
      }
      place(sb, LG.dafLabel(t.n - 4, 1), 4);
      E({ k: 'cf', key: 'types', val: ['yomi'], t: Date.now() - 90 * 86400000 });
    } else if (name === 'scholar') {
      var ss = has('sukkah'), Ls = amudList(ss);
      Ls.forEach(function (d, i) {
        var reps = 4 + Math.floor(r() * 9), last = 3 + Math.floor(r() * 80);
        for (var q = 0; q < reps; q++) done(day(Math.min(89, last + q * 7)), 9, 0, ss, d, Math.max(3, 14 - q * 0.9));
      });
      for (var z = 0; z < 60; z++) session(day(z + 1), 9, 0, 20 + Math.round(r() * 30), ss, [Ls[z % Ls.length], Ls[(z + 1) % Ls.length]]);
      place(ss, Ls[10], 1);
      E({ k: 'cf', key: 'types', val: ['scholar'], t: Date.now() - 90 * 86400000 });
      E({ k: 'cf', key: 'target', val: { 0: 10 }, t: Date.now() - 90 * 86400000 });
    } else if (name === 'suggester') {
      var sg = has('bekhorot'), Lg = amudList(sg);
      for (var y = 0; y < 30; y++) session(day(y * 3), 21, 0, 15 + Math.round(r() * 20), sg, [Lg[y % Lg.length], Lg[(y + 1) % Lg.length]]);
      for (var w = 0; w < 14; w++) done(day(w * 6), 21, 20, sg, Lg[w], 9);
      place(sg, Lg[14], 1);
      var by = {}, tot = { total: 40, pending: 9, approved: 17, refined: 8, rejected: 6, bySlug: {} };
      tot.bySlug[sg] = {};
      for (var u = 0; u < 40; u++) { var dd = Lg[(u * 3) % Lg.length]; tot.bySlug[sg][dd] = (tot.bySlug[sg][dd] || 0) + 1; }
      LG.sugg = tot;
      E({ k: 'cf', key: 'types', val: ['regular'], t: Date.now() - 90 * 86400000 });
    }
    return ev;
  }
  LG.demo = function (name) {
    window.__lmDemo = name;
    LG._demoEv = gen(name);
  };

  /* ---------------------------------------------------------- הרצה לפי עמוד */
  LG.suggFor = function (slug) { return (LG.sugg && LG.sugg.bySlug && LG.sugg.bySlug[slug]) || {}; };

  async function boot() {
    var page = document.body.getAttribute('data-page');
    if (!page) return;
    var q = new URLSearchParams(location.search), demo = q.get('demo');
    try {
      if (demo === 'off') sessionStorage.removeItem('lg-demo');
      else if (demo) sessionStorage.setItem('lg-demo', demo);
      demo = demo === 'off' ? null : (demo || sessionStorage.getItem('lg-demo'));
    } catch (e) { }
    document.body.classList.add('lm');
    if (demo && DEMOS[demo]) {
      LG.demo(demo);
      await LG.ready();
      LG._demoEv.forEach(function (e) { LG.put(e, true); });
    } else {
      await LG.ready();
    }
    UI.applyTheme();
    var root = document.body;
    UI.header(page);
    if (window.__lmDemo) {
      var b = UI.el('div', 'lm-hint', 'מצב הדגמה: ' + LG.demoNames[window.__lmDemo] + ' · נתונים בדויים בזיכרון בלבד · <a href="?demo=off">יציאה מההדגמה</a>');
      b.style.cssText = 'text-align:center;border-radius:0';
      document.body.insertBefore(b, document.body.children[1]);
    } else if (LG.sync) {
      LG.sync.auto();
      if (page === 'lamed' || page === 'masechet') LG.sync.loadSugg().then(function () { if (LG.sugg && !LG._suggDrawn) { LG._suggDrawn = 1; document.getElementById('lm-app').innerHTML = ''; draw(page); } });
    }
    var app = document.getElementById('lm-app') || (function () { var a = document.createElement('div'); a.id = 'lm-app'; document.body.appendChild(a); return a; })();
    draw(page);
    document.body.appendChild(LG.brand.footer());
    function draw(p) {
      var host = document.getElementById('lm-app');
      var f = { home: UI.home, shas: UI.shas, masechet: UI.masechet, lamed: UI.lamed, yomi: UI.yomi, settings: UI.settings, done: UI.done, admin: UI.admin, nivhanim: UI.nivhanim, shiurim: UI.shiurim, quiz: UI.quiz }[p];
      if (f) f(host);
    }
    /* תזכורת דפדפן: בפתיחת האתר, אם הופעלה ועבר זמנה והדף היומי טרם נלמד */
    try {
      var rm = LG.settings().remind;
      if (rm && rm.on && rm.browser && 'Notification' in window && Notification.permission === 'granted' && !window.__lmDemo) {
        var y = LGDaf.forStr(LG.ymd(Date.now())), p0 = LG.parts(Date.now());
        if (LG.ymd(Date.now()) !== localStorage.getItem('lg-lamed-ntf') && (p0.h * 60 + p0.mi) >= (+rm.time.slice(0, 2) * 60 + +rm.time.slice(3, 5))) {
          new Notification('הדף היומי: ' + y.name + ' ' + y.daf);
          localStorage.setItem('lg-lamed-ntf', LG.ymd(Date.now()));
        }
      }
    } catch (e) { }
  }
  if (document.body && document.body.getAttribute('data-page')) {
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
  }
})();
