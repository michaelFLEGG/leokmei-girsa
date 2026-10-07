/* lamed - מעקב בדף הלימוד: מקום אחרון, זמן פעיל, סיום עמוד, שעון וסמן התקדמות.
   נטען אחרי הטקסט ואינו עוצר את הצגתו. אינו נוגע בשורות של הדף: הכול בשכבה
   צפה מחוץ ל-#flow (כמו כפתור "מקור"), ולכן אינו מזיז שורה ואינו מסתיר טקסט. */
(function () {
  'use strict';
  var LG = window.LAMED;
  var T = LG.track = {};
  var IDLE = 180000;           /* שלוש דקות בלי פעילות: השעון נעצר */
  var DONE_RATIO = 0.30;       /* סף הסיום האוטומטי: 30% מזמן הקריאה הצפוי לעמוד באורכו */
  var G = {};                  /* מצב פנימי */

  function $(s) { return document.querySelector(s); }
  function inReader() { return typeof D !== 'undefined' && typeof SLUG !== 'undefined' && $('#flow'); }

  /* ---------------------------------------------------------- מיפוי יחידות */
  function build() {
    G.unit2pi = {}; G.words = []; G.lastUnit = [];
    D.pages.forEach(function (p, pi) {
      var n = 0, last = null;
      p.units.forEach(function (u) {
        G.unit2pi[u.id] = pi;
        if (u.k === 'u' || u.k === 'm' || u.k === 'dh' || u.k === 'nose') { n += 1; last = u.id; }
      });
      G.lastUnit[pi] = last;
      G.words[pi] = p.units.reduce(function (s, u) {
        function w(h) { return String(h || '').replace(/<[^>]+>/g, ' ').split(/\s+/).filter(Boolean).length; }
        return s + w(u.a) + (u.l || []).reduce(function (a, l) { return a + w(l[1]); }, 0);
      }, 0);
    });
  }
  function dafOfPi(pi) { return (D.pages[pi] && D.pages[pi].daf || '').trim(); }
  function piOfDaf(d) { for (var i = 0; i < D.pages.length; i++) if ((D.pages[i].daf || '').trim() === d) return i; return -1; }

  /* ---------------------------------------------------------- שורות גלויות */
  function observe() {
    if (!window.IntersectionObserver) return;
    if (G.io) G.io.disconnect();
    G.vis = new Map();
    G.io = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) G.vis.set(e.target, e.intersectionRatio); else G.vis.delete(e.target); });
      G.dirty = true;
    }, { root: $('#flow'), threshold: [0, 0.3, 0.7, 1] });
    $('#flow').querySelectorAll('.row').forEach(function (r) { G.io.observe(r); });
  }
  function firstVisible() {
    var best = null;
    G.vis.forEach(function (ratio, el) {
      if (ratio < 0.2 && G.vis.size > 1) return;
      if (!best || (best.compareDocumentPosition(el) & Node.DOCUMENT_POSITION_PRECEDING)) best = el;
    });
    return best;
  }
  function visibleIds() {
    var s = {};
    G.vis.forEach(function (r, el) { var id = +(el.id || '').slice(1); if (id) s[id] = 1; });
    return s;
  }
  function rowText(row) {
    var p = row.querySelector('.main p, .main');
    return p ? p.textContent : '';
  }

  /* ---------------------------------------------------------- מקום אחרון */
  function readPos() {
    var row = G.vis && firstVisible();
    if (!row) return null;
    var id = +(row.id || '').slice(1), pi = G.unit2pi[id];
    if (pi === undefined) return null;
    return { s: SLUG, d: dafOfPi(pi), pid: id, fp: LG.fpOf(rowText(row)), pi: pi };
  }
  T.cur = function () { return G.cur || readPos(); };
  T.savePos = function () {
    var p = readPos();
    if (!p || window.__lmDemo) return;
    var key = p.pid + '|' + p.fp;
    if (G.lastPosKey === key) return;
    G.lastPosKey = key;
    G.cur = p;
    LG.put({ k: 'ps', id: 'ps-' + SLUG, s: SLUG, d: p.d, pid: p.pid, fp: p.fp, t: Date.now() }, true);
    try { localStorage.setItem('lg-lamed-last', JSON.stringify({ s: SLUG, d: p.d, pid: p.pid, fp: p.fp, t: Date.now() })); } catch (e) { }
  };
  /* חזרה למקום: מזהה הפסקה, אחר כך טביעת הטקסט, ובכישלון - ראש העמוד הנכון.
     לעולם לא ראש המסכת בטעות. */
  T.gotoPos = function (pos) {
    if (!pos) return false;
    var pi = piOfDaf(pos.d);
    var row = null, how = '';
    if (pos.pid && G.unit2pi[pos.pid] !== undefined) {
      var pi2 = G.unit2pi[pos.pid];
      var u = D.pages[pi2].units.filter(function (x) { return x.id === pos.pid; })[0];
      var txt = LG.fpOf(String(u && ((u.a || '') + ' ' + ((u.l && u.l[0] && u.l[0][1]) || ''))).replace(/<[^>]+>/g, ' '));
      if (!pos.fp || txt.indexOf(pos.fp.slice(0, 12)) > -1 || LG.fpOf(u && u.a || '') === pos.fp.slice(0, LG.fpOf(u && u.a || '').length)) { pi = pi2; how = 'id'; }
    }
    if (!how && pos.fp) {
      /* דמיון טקסט: הפסקה שנפתחת בטביעה, באותו עמוד או בסביבתו */
      var key = pos.fp.slice(0, 16), cand = null, best = 1e9;
      D.pages.forEach(function (p, i) {
        p.units.forEach(function (u) {
          var hs = [u.a || ''].concat((u.l || []).map(function (l) { return l[1]; }));
          for (var k = 0; k < hs.length; k++) {
            if (LG.fpOf(hs[k].replace(/<[^>]+>/g, ' ')).indexOf(key) === 0) {
              var dist = Math.abs(i - (pi < 0 ? i : pi));
              if (dist < best) { best = dist; cand = { id: u.id, pi: i }; }
            }
          }
        });
      });
      if (cand) { pi = cand.pi; pos = { s: pos.s, d: pos.d, pid: cand.id, fp: pos.fp }; how = 'fp'; }
    }
    if (pi < 0) return false;
    try { toDaf(pi); } catch (e) { return false; }
    if (how) {
      setTimeout(function () {
        var el = document.getElementById('u' + pos.pid);
        if (!el) return;
        try { toEl(el); } catch (e) { el.scrollIntoView({ block: 'center' }); }
        var tgt = el.querySelector('.main p, .main') || el;
        tgt.classList.add('lm-hl');
        setTimeout(function () { tgt.classList.remove('lm-hl'); }, 2300);
      }, 120);
    }
    return true;
  };

  /* ---------------------------------------------------------- זמן פעיל */
  function leader() {
    /* עמוד אחד נספר פעם אחת: רק הלשונית הפעילה (גלויה וממוקדת) */
    try {
      var raw = localStorage.getItem('lg-lamed-act'), o = raw ? JSON.parse(raw) : null, now = Date.now();
      if (o && o.tab !== G.tab && now - o.t < 7000) return false;
      localStorage.setItem('lg-lamed-act', JSON.stringify({ tab: G.tab, t: now }));
    } catch (e) { }
    return true;
  }
  function act() { G.act = Date.now(); if (G.idleShown) hideIdle(); }
  function curKey() { var p = G.cur || readPos(); return p ? SLUG + '|' + p.d : null; }

  function session() {
    var now = Date.now();
    if (!G.ses || now - G.ses.t1 > 1800000) {
      G.ses = { id: LG.uid(), k: 'ss', t: now, t0: now, t1: now, ms: 0, s: SLUG, per: {} };
    }
    return G.ses;
  }
  function flush(final) {
    var s = G.ses;
    if ((!s || !s.ms) && !(G.editMs > 1000)) return;
    if (window.__lmDemo) return;
    if (!s) { LG.put({ id: 'ed-' + G.tab, k: 'ed', t: G.t0 || (G.t0 = Date.now()), ms: Math.round(G.editMs) }, true); return; }
    var e = { id: s.id, k: 'ss', t: s.t0, t0: s.t0, t1: s.t1, ms: Math.round(s.ms), s: s.s, per: {} };
    Object.keys(s.per).forEach(function (k) { e.per[k] = Math.round(s.per[k]); });
    if (final) {
      /* בסגירת הלשונית אין זמן לכתיבה אסינכרונית: גיבוי סינכרוני */
      try {
        var pend = JSON.parse(localStorage.getItem('lg-lamed-pend') || '[]');
        pend = pend.filter(function (x) { return x.id !== e.id; }); pend.push(e);
        localStorage.setItem('lg-lamed-pend', JSON.stringify(pend));
      } catch (er) { }
    }
    LG.put(e, true);
    if (G.editMs > 1000) LG.put({ id: 'ed-' + G.tab, k: 'ed', t: G.t0 || (G.t0 = Date.now()), ms: Math.round(G.editMs) }, true);
  }
  function tick() {
    var now = Date.now(), dt = now - (G.lastTick || now);
    G.lastTick = now;
    if (dt > 15000 || dt < 0) return;        /* שינה של המחשב או השהיית טיימר: הזמן אינו נספר */
    var vis = document.visibilityState === 'visible', foc = document.hasFocus ? document.hasFocus() : true;
    if (!vis || !foc) return;
    if (now - G.act > IDLE) { if (!G.idleShown && now - G.act < IDLE + 8000) showIdle(); return; }
    if (!leader()) return;
    if (typeof EDIT !== 'undefined' && EDIT) {
      /* זמן עריכה נרשם בנפרד, ואינו מנפח את זמן הלימוד */
      G.editMs = (G.editMs || 0) + dt;
      return;
    }
    if (G.paused) return;
    G.dirty && updateCur();
    var k = curKey();
    if (!k) return;
    var s = session();
    if (!G.started[k] && G.cur && LG.sync) { G.started[k] = 1; LG.sync.stat({ s: SLUG, d: G.cur.d, start: 1 }); }
    s.ms += dt; s.t1 = now; s.per[k] = (s.per[k] || 0) + dt;
    G.pageMs[k] = (G.pageMs[k] || 0) + dt;
    G.sinceFlush = (G.sinceFlush || 0) + dt;
    if (G.sinceFlush > 20000) { G.sinceFlush = 0; flush(); }
    checkDone();
  }
  function updateCur() {
    G.dirty = false;
    var p = readPos();
    if (p) { G.cur = p; T.savePos(); }
    /* עמודים שהגעת לסופם: היחידה האחרונה של העמוד נראתה */
    var ids = visibleIds();
    D.pages.forEach(function (pg, pi) {
      var last = G.lastUnit[pi];
      if (last && ids[last]) G.reached[pi] = true;
      /* התקדמות בעמוד: המיקום היחסי של היחידה הגלויה האחרונה */
      var idx = -1, n = pg.units.length;
      for (var i = 0; i < n; i++) if (ids[pg.units[i].id]) idx = i;
      if (idx >= 0) G.seen[pi] = Math.max(G.seen[pi] || 0, (idx + 1) / n);
    });
    drawPbar();
  }
  function checkDone() {
    var p = G.cur;
    if (!p) return;
    var pi = p.pi;
    if (!G.reached[pi]) return;
    var key = SLUG + '|' + p.d;
    var info = LG.amudInfo(SLUG, p.d);
    var today = LG.ymd(Date.now());
    var a = info.a;
    if (a && a.dates.indexOf(today) > -1) return;        /* כבר נספר היום */
    if (info.st === 'done' && a && a.last && LG.ymd(a.last) === today) return;
    var need = (G.words[pi] || LG.avgWords()) * LG.pace(SLUG).perWord * DONE_RATIO;
    var have = (G.pageMs[key] || 0);
    if (have >= need) { T.markDone(SLUG, p.d, 'auto', have); }
    drawFin();
  }
  T.markDone = function (slug, daf, how, ms) {
    if (window.__lmDemo) return;
    var cycBefore = LG.cycles(slug);
    LG.put({ k: 'dn', s: slug, d: daf, how: how || 'manual', ms: Math.round(ms || (G.pageMs && G.pageMs[slug + '|' + daf]) || 0), t: Date.now() });
    toast('עמוד ' + daf + ' נרשם כנלמד');
    var msx = Math.round(ms || (G.pageMs && G.pageMs[slug + '|' + daf]) || 0);
    if (LG.sync) {
      LG.sync.stat({ s: slug, d: daf, done: 1, ms: msx });
      if (LG.amudim(slug).length && LG.cycles(slug) > cycBefore) {
        LG.sync.stat({ s: slug, d: daf, fin: 1 });
        setTimeout(function () {
          var b = document.createElement('div'); b.className = 'lm-toast'; b.style.bottom = '100px';
          b.innerHTML = '<span>סיימת את המסכת</span> <a href="done.html?m=' + slug + '" style="color:#2b2620;background:#c9a24a;border-radius:5px;padding:2px 10px;text-decoration:none;margin-right:10px">הדרן עלך</a>';
          document.body.appendChild(b); setTimeout(function () { b.remove(); }, 12000);
        }, 1600);
      }
    }
  };
  T.unmark = function (slug, daf) { LG.put({ k: 'un', s: slug, d: daf, t: Date.now() }); };

  /* ---------------------------------------------------------- "עדיין לומד?" */
  function showIdle() {
    G.idleShown = true;
    var b = document.createElement('div');
    b.id = 'lm-idle'; b.className = 'lm-toast';
    b.innerHTML = '<span>עדיין לומד?</span> <button type="button">כן, ממשיך</button>';
    b.querySelector('button').onclick = function () {
      /* נגיעה אחת מחזירה את הדקות שנעצרו */
      var s = session(), k = curKey();
      if (k) { s.ms += IDLE; s.per[k] = (s.per[k] || 0) + IDLE; G.pageMs[k] = (G.pageMs[k] || 0) + IDLE; }
      G.act = Date.now(); hideIdle();
    };
    document.body.appendChild(b);
  }
  function hideIdle() { G.idleShown = false; var b = $('#lm-idle'); if (b) b.remove(); }
  function toast(t) {
    var b = document.createElement('div'); b.className = 'lm-toast lm-t2'; b.textContent = t;
    document.body.appendChild(b); setTimeout(function () { b.remove(); }, 2200);
  }
  T.toast = toast;

  /* ---------------------------------------------------------- שכבה צפה: סמן התקדמות, שעון, "סיימתי" */
  function ensureLayer() {
    if ($('#lm-layer')) return;
    var l = document.createElement('div'); l.id = 'lm-layer'; l.setAttribute('aria-hidden', 'false');
    l.innerHTML = '<div id="lm-pbar"><i></i></div><div id="lm-fin" style="display:none"><button type="button"></button></div>';
    document.body.appendChild(l);
    l.querySelector('#lm-fin button').onclick = function () {
      var p = G.cur; if (p) { T.markDone(SLUG, p.d, 'manual'); drawFin(); }
    };
  }
  function drawPbar() {
    var s = LG.settings(), bar = $('#lm-pbar');
    if (!bar) return;
    bar.style.display = s.bar === false ? 'none' : '';
    var p = G.cur; if (!p) return;
    var f = Math.min(1, G.seen[p.pi] || 0);
    bar.firstChild.style.width = Math.round(f * 100) + '%';
  }
  function drawFin() {
    var box = $('#lm-fin'), p = G.cur;
    if (!box || !p) return;
    var pi = p.pi, last = G.lastUnit[pi], row = last && document.getElementById('u' + last);
    var done = LG.amudInfo(SLUG, p.d).st === 'done' && (LG.amudInfo(SLUG, p.d).a.dates.indexOf(LG.ymd(Date.now())) > -1);
    if (!row || !G.vis.has(row) || done) { box.style.display = 'none'; return; }
    var rail = row.querySelector('.rail'), fr = $('#flow').getBoundingClientRect();
    var r = (rail || row).getBoundingClientRect();
    box.style.display = '';
    box.firstChild.textContent = 'סיימתי את העמוד';
    var top = Math.max(fr.top + 4, Math.min(fr.bottom - 30, r.bottom - 28));
    box.style.top = Math.round(top) + 'px';
    box.style.left = Math.round(Math.max(fr.left + 4, r.left)) + 'px';
  }
  function drawClock() {
    var s = LG.settings(), c = $('#lm-clock');
    if (!c) return;
    c.style.display = s.clock === false ? 'none' : '';
    if (s.clock === false) return;
    var ses = G.ses, ms = ses ? ses.ms : 0, k = curKey(), pm = G.pageMs[k] || 0;
    var now = new Date(), p = LG.parts(now.getTime());
    var hh = (p.h < 10 ? '0' : '') + p.h + ':' + (p.mi < 10 ? '0' : '') + p.mi;
    var mm = Math.floor(ms / 60000), short = mm < 60 ? mm + ' ד׳' : Math.floor(mm / 60) + ':' + (mm % 60 < 10 ? '0' : '') + (mm % 60) + ' ש׳';
    c.querySelector('.lm-c1').textContent = (G.paused ? 'מושהה ' : '') + short;
    c.querySelector('.lm-c2').textContent = hh;
    c.title = 'זמן הלימוד בישיבה הנוכחית: ' + LG.dur(ms) + (k ? ' · בעמוד הזה: ' + LG.dur(pm) : '') + ' · לחיצה: עצירה והמשך';
  }
  function injectBar() {
    var bar = $('#bar');
    if (!bar || $('#lm-clock')) return;
    var g = document.createElement('div');
    g.className = 'bg'; g.id = 'lm-clock'; g.setAttribute('data-pri', '1');
    g.innerHTML = '<button type="button" class="lm-clk"><span class="lm-c1">0 ד׳</span><span class="lm-c2"></span></button>';
    g.querySelector('button').onclick = function () { G.paused = !G.paused; drawClock(); };
    var more = $('#morebg');
    bar.insertBefore(g, more || null);
    var g2 = document.createElement('div');
    g2.className = 'bg'; g2.id = 'lm-links'; g2.setAttribute('data-pri', '2');
    g2.innerHTML = '<a class="lm-a" href="lamed.html">הלימוד שלי</a><a class="lm-a" href="shas.html">מפת הש"ס</a>';
    bar.insertBefore(g2, g);
    if (typeof barFit === 'function') setTimeout(barFit, 50);
  }

  /* ---------------------------------------------------------- כרטיס "המשך" בטעינה */
  function resumeFromHash() {
    /* קישור עם #lm=<מזהה>.<טביעה> */
    var h = (typeof ME_HASH !== 'undefined' ? ME_HASH : location.hash) || '', m = /lm=([^&]+)/.exec(h);
    if (m) {
      try {
        var o = JSON.parse(decodeURIComponent(m[1]));
        /* הדף מצייר את עצמו מחדש מיד אחרי הטעינה (שכבת הניקוד, גופנים) ומחזיר את הגלילה
           לראש. לכן המקום מוחל, ואחר כך נבדק במועדים קבועים, וחוזר אם נדרש */
        T.gotoPos(o);
        [1300, 2600, 4200, 6500].forEach(function (ms) {
          setTimeout(function () {
            G.dirty = true; updateCur();
            var c = G.cur;
            if (!c || c.d !== o.d) T.gotoPos(o);
          }, ms);
        });
      } catch (e) { }
    }
  }

  T.init = async function () {
    if (!inReader()) return;
    await LG.ready();
    G.tab = LG.uid(); G.act = Date.now(); G.pageMs = {}; G.reached = {}; G.seen = {}; G.started = {};
    build();
    observe();
    ensureLayer();
    injectBar();
    var mo = new MutationObserver(function () { clearTimeout(G.moT); G.moT = setTimeout(function () { observe(); G.dirty = true; }, 120); });
    mo.observe($('#flow'), { childList: true });
    ['scroll', 'wheel', 'keydown', 'mousemove', 'touchstart', 'click', 'pointerdown'].forEach(function (ev) {
      var t = ev === 'scroll' ? $('#flow') : document;
      t.addEventListener(ev, act, { passive: true, capture: true });
    });
    $('#flow').addEventListener('scroll', function () { G.dirty = true; drawFin(); }, { passive: true });
    document.addEventListener('visibilitychange', function () {
      if (document.visibilityState === 'hidden') { T.savePos(); flush(true); }
      else { G.lastTick = Date.now(); G.act = Date.now(); }
    });
    addEventListener('pagehide', function () { T.savePos(); flush(true); });
    addEventListener('resize', function () { G.dirty = true; });
    setInterval(tick, 1000);
    setInterval(function () { if (G.dirty) updateCur(); drawClock(); drawFin(); }, 1500);
    G.lastTick = Date.now();
    setTimeout(function () { updateCur(); resumeFromHash(); drawClock(); setTimeout(function () { G.dirty = true; }, 600); }, 400);
    LG.onChange(function () { drawClock(); drawPbar(); });
  };
  /* בדיקות ודוחות */
  T._state = function () { return G; };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', function () { setTimeout(T.init, 0); });
  else setTimeout(T.init, 0);
})();
