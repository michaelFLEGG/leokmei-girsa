/* lamed - "בחן את עצמך": חזרה מרווחת, ניקוד, תארים ולוח מובילים (מנה 3 מתוך 3, 7.10.2026).
   כל תשובה נשמרת כאירוע (k:'qa') באותו מנגנון של מערכת הלומד: נשמרת במכשיר, ומסונכרנת
   בין מכשירים בקוד לומד, באותו שירות קיים. מצב הכרטיסיות והניקוד נגזרים מן האירועים.

   שיטת החזרה (SM-2 מצומצם, בלי סולם איכות): תשובה נכונה מרחיקה את המועד הבא
   (יום, שישה ימים, ואז כפול הגורם 2.5 בכל פעם: שבוע, חודש, ארבעה חודשים, חצי שנה...);
   טעות מחזירה את הכרטיסייה ליום המחרת ומקטינה את הגורם.

   ניקוד: רק על תשובה נכונה שהכרטיסייה "הגיעה זמנה" (או חדשה). הניקוד גדל עם הפער שבין
   הפעם הקודמת להיום: 10 × (1 + log2(1 + ימים)). חזרה מוקדמת, או חזרה מיידית על אותה שאלה,
   היא תרגול בלי ניקוד, ואינה משנה את המועד. בונוס רצף: 5 נקודות × ימי הרצף (עד 20) ליום. */
(function () {
  'use strict';
  var LG = window.LAMED, UI = LG.ui, E = LG.esc, $ = UI.$, el = UI.el;
  var Q = LG.quiz = {};

  /* ---------------------------------------------------------- תארים */
  Q.T_ALL = [500, 3000, 10000, 30000, 100000];
  Q.T_M = [300, 1500, 5000, 15000, 40000];
  Q.TITLES_M = ['', 'לומד המסכת', 'תלמיד חכם', 'חכם', 'גאון', 'גאון עצום'];
  Q.TITLES_ALL = ['', 'לומד הש"ס', 'תלמיד חכם', 'חכם', 'גאון', 'גאון עצום'];
  Q.level = function (pts, T) { var l = 0; T.forEach(function (x, i) { if (pts >= x) l = i + 1; }); return l; };
  Q.TYPES = { w: 'איפה כתוב', m: 'מי אמר', c: 'השלם את המשנה', d: 'שאלת הבנה' };
  var ROUND = 10;

  function api() { return LG.sync; }
  function offline() { return window.__lmDemo || !LG.sync; }
  function shareOk() { return LG.settings().share !== false; }

  /* ---------------------------------------------------------- בנק שאלות */
  var banks = {}, decs = {};
  function decisions(slug) {
    if (!decs[slug]) decs[slug] = fetch(api().base + '/qz/dec?s=' + encodeURIComponent(slug)).then(function (r) { return r.json(); })
      .then(function (j) { return (j && j.dec) || {}; }).catch(function () { return {}; });
    return decs[slug];
  }
  Q.bank = function (slug) {
    if (banks[slug]) return banks[slug];
    banks[slug] = fetch('quiz/' + slug + '.json').then(function (r) { if (!r.ok) throw 0; return r.json(); }).then(async function (b) {
      var qs = b.q.slice();
      /* שאלות הבנה שנוצרו במודל: טיוטה. מוצגות ללומד רק אחרי שהמנהל אישר (אשר / ערוך) */
      try {
        if (!Q._drafts) Q._drafts = fetch('quiz/drafts.json').then(function (r) { return r.ok ? r.json() : {}; }).catch(function () { return {}; });
        var dr = (await Q._drafts)[slug] && !offline() ? await fetch('quiz/' + slug + '-draft.json') : null;
        if (dr && dr.ok) {
          var d = await dr.json(), dec = await decisions(slug);
          (d.q || []).forEach(function (q) {
            var v = dec[q.i];
            if (v && v.st === 'ok') qs.push(Object.assign({}, q, v.e || {}, { t: 'd' }));
          });
        }
      } catch (e) { }
      var by = {}; qs.forEach(function (q) { by[q.i] = q; });
      return { slug: slug, name: b.name, q: qs, by: by };
    }).catch(function () { return null; });
    return banks[slug];
  };
  Q.index = function () {
    if (!Q._idx) Q._idx = fetch('quiz/index.json').then(function (r) { return r.json(); }).catch(function () { return {}; });
    return Q._idx;
  };

  /* ---------------------------------------------------------- כרטיסיות (חזרה מרווחת) */
  Q.cards = function () {
    var C = {};
    LG.events().filter(function (e) { return e.k === 'qa' && !e.pr; }).sort(function (a, b) { return a.t - b.t; }).forEach(function (e) {
      var c = C[e.q] || (C[e.q] = { q: e.q, s: e.s, rep: 0, ease: 2.5, ivl: 0, n: 0, ok: 0, last: 0, lastOk: 0, due: '' });
      if (e.ok) { c.rep++; c.ok++; c.ivl = c.rep === 1 ? 1 : (c.rep === 2 ? 6 : Math.round(c.ivl * c.ease)); c.lastOk = e.t; }
      else { c.rep = 0; c.ivl = 1; c.ease = Math.max(1.3, c.ease - 0.2); }
      c.last = e.t; c.n++; c.due = LG.addDays(LG.ymd(e.t), c.ivl);
    });
    return C;
  };
  function weekStart(today) { var dow = new Date(LG.ymdToUTC(today) + 43200000).getUTCDay(); return LG.addDays(today, -dow); }
  Q.score = function () {
    var today = LG.ymd(Date.now()), wk = weekStart(today), days = {}, byM = {}, base = 0, wpts = 0, answered = 0, right = 0;
    LG.events().forEach(function (e) {
      if (e.k !== 'qa') return;
      answered++; if (e.ok) right++;
      if (!e.pts) return;
      var d = LG.ymd(e.t);
      days[d] = (days[d] || 0) + e.pts; byM[e.s] = (byM[e.s] || 0) + e.pts; base += e.pts;
      if (d >= wk) wpts += e.pts;
    });
    var ds = Object.keys(days).sort(), run = 0, prev = null, bonus = 0, wbonus = 0, curRun = 0;
    ds.forEach(function (d) {
      run = (prev && LG.diffDays(prev, d) === 1) ? run + 1 : 1; prev = d;
      var b = 5 * Math.min(run, 20); bonus += b; if (d >= wk) wbonus += b;
      curRun = (d === today || LG.diffDays(d, today) === 1) ? run : 0;
    });
    return { total: base + bonus, base: base, bonus: bonus, byM: byM, week: wpts + wbonus, streak: curRun, answered: answered, right: right, today: days[today] || 0 };
  };
  Q.dueCount = function () {
    var C = Q.cards(), today = LG.ymd(Date.now()), n = 0;
    Object.keys(C).forEach(function (k) { if (C[k].due <= today) n++; });
    return n;
  };

  /* מתעד תשובה ומחזיר מה קרה: ניקוד, והמועד הבא */
  Q.record = function (q, ok, ms) {
    var C = Q.cards(), c = C[q.i], today = LG.ymd(Date.now());
    var isDue = !c || c.due <= today;
    var e = { k: 'qa', q: q.i, s: q.s, ok: ok ? 1 : 0, t: Date.now(), ms: Math.min(120000, ms || 0) };
    var pts = 0;
    if (!isDue) e.pr = 1;
    else if (ok) {
      var gap = c ? Math.max(1, LG.diffDays(LG.ymd(c.lastOk || c.last), today)) : 0;
      pts = Math.round(10 * (1 + Math.log(1 + Math.min(gap, 365)) / Math.LN2));
      e.pts = pts;
    }
    LG.put(e);
    var c2 = Q.cards()[q.i];
    return { pts: pts, practice: !isDue, ivl: c2 ? c2.ivl : 0, due: c2 ? c2.due : '' };
  };

  /* ---------------------------------------------------------- סבב שאלות */
  function shuffle(a, seed) {
    var r = seed || Math.random, i, j, t;
    for (i = a.length - 1; i > 0; i--) { j = Math.floor(r() * (i + 1)); t = a[i]; a[i] = a[j]; a[j] = t; }
    return a;
  }
  Q.queue = async function (mode, slug) {
    var C = Q.cards(), today = LG.ymd(Date.now()), list = [], idx = await Q.index();
    function tag(b, q) { var o = Object.assign({}, q); o.s = b.slug; return o; }
    if (mode === 'due') {
      var slugs = {};
      Object.keys(C).forEach(function (k) { if (C[k].due <= today) slugs[C[k].s] = 1; });
      var due = [];
      for (var s in slugs) {
        var b = await Q.bank(s);
        if (b) Object.keys(C).forEach(function (k) { if (C[k].s === s && C[k].due <= today && b.by[k]) due.push({ q: tag(b, b.by[k]), due: C[k].due }); });
      }
      due.sort(function (a, b) { return a.due < b.due ? -1 : 1; });
      return due.slice(0, ROUND).map(function (x) { return x.q; });
    }
    var bank = await Q.bank(slug);
    if (!bank) return null;
    var pool = bank.q;
    if (mode === 'yomi') {
      var y = LGDaf.forStr(today), a0 = LG.dafLabel(y.n, 0), a1 = LG.dafLabel(y.n, 1), k0 = LG.dafKey(a0);
      var near = pool.filter(function (q) { return q.d === a0 || q.d === a1; });
      for (var w = 2; near.length < ROUND && w <= 12; w += 2) {
        near = pool.filter(function (q) { return Math.abs(LG.dafKey(q.d) - k0) <= w; });
      }
      pool = near.length >= 3 ? near : pool;
    }
    var dueQ = [], newQ = [], restQ = [];
    pool.forEach(function (q) {
      var c = C[q.i], x = tag(bank, q);
      if (!c) newQ.push(x); else if (c.due <= today) dueQ.push({ q: x, due: c.due }); else restQ.push(x);
    });
    dueQ.sort(function (a, b) { return a.due < b.due ? -1 : 1; });
    shuffle(newQ); shuffle(restQ);
    /* סוגי השאלות מעורבבים: לא עשר שאלות מאותו סוג ברצף */
    var out = dueQ.map(function (x) { return x.q; }).slice(0, ROUND);
    var byT = {};
    newQ.forEach(function (q) { (byT[q.t] = byT[q.t] || []).push(q); });
    var ts = Object.keys(byT), ti = 0, guard = 0;
    while (out.length < ROUND && ts.length && guard++ < 400) {
      var t = ts[ti % ts.length], arr = byT[t];
      if (arr.length) out.push(arr.shift()); else { ts.splice(ti % ts.length, 1); continue; }
      ti++;
    }
    restQ.forEach(function (q) { if (out.length < ROUND) out.push(q); });
    return shuffle(out.slice(), null);
  };

  function dayWord(n) { return n === 1 ? 'מחר' : (n === 6 ? 'בעוד שבוע' : (n < 14 ? 'בעוד ' + n + ' ימים' : (n < 60 ? 'בעוד ' + Math.round(n / 7) + ' שבועות' : 'בעוד ' + Math.round(n / 30) + ' חודשים'))); }

  Q.run = function (host, queue, onEnd) {
    var i = 0, res = { right: 0, wrong: 0, pts: 0 }, retry = [], t0 = 0, locked = false;
    function end() {
      Q.syncScore();
      onEnd(res);
    }
    function show() {
      if (i >= queue.length) return end();
      var q = queue[i], card = el('div', 'lm-card lm-qz');
      var isRetry = !!q._retry;
      locked = false; t0 = Date.now();
      var opts = q.o.map(function (o, k) { return '<button type="button" class="lm-btn ghost lm-qo" data-k="' + k + '"><b>' + (k + 1) + '</b> ' + E(o) + '</button>'; }).join('');
      card.innerHTML = '<div class="lm-small">שאלה ' + (Math.min(i + 1, queue.length)) + ' מתוך ' + queue.length + ' · ' + E(Q.TYPES[q.t] || '') + ' · ' + E(LG.nameOf(q.s)) +
        (isRetry ? ' · ניסיון חוזר (בלי ניקוד)' : '') + '</div>' +
        '<div class="lm-bar"><i style="width:' + Math.round(100 * i / queue.length) + '%"></i></div>' +
        '<h3 class="lm-qq">' + E(q.q) + '</h3><div class="lm-qopts">' + opts + '</div><div class="lm-qfb" aria-live="polite"></div>';
      host.innerHTML = ''; host.appendChild(card);
      function pick(k) {
        if (locked) return; locked = true;
        var ok = k === q.a, fb = $('.lm-qfb', card), btns = card.querySelectorAll('.lm-qo');
        btns.forEach(function (b, n) { b.disabled = true; if (n === q.a) b.classList.add('lm-ok'); else if (n === k) b.classList.add('lm-bad'); });
        var r = isRetry ? { pts: 0, practice: true, ivl: 0 } : Q.record(q, ok, Date.now() - t0);
        if (!isRetry) { if (ok) res.right++; else res.wrong++; }
        res.pts += r.pts;
        var href = UI.readHref(q.s, q.d);
        var msg = ok ? '<b class="lm-okt">נכון!</b>' + (r.pts ? ' +' + r.pts + ' נקודות' : '') : '<b class="lm-badt">לא נכון.</b> התשובה: <b>' + E(q.o[q.a]) + '</b>';
        var when = isRetry ? '' : (r.practice ? 'תרגול מוקדם: בלי ניקוד, והמועד הבא לא השתנה.' :
          (ok ? 'תישאל שוב ' + dayWord(r.ivl) + '.' : 'תישאל שוב מחר.'));
        fb.innerHTML = '<p>' + msg + '</p>' + (when ? '<p class="lm-note">' + E(when) + '</p>' : '') +
          (href ? '<p class="lm-note">המקום בטקסט: <a href="' + href + '">' + E(LG.nameOf(q.s)) + ' ' + E(q.d) + '</a></p>' : '') +
          '<div class="lm-row"><button type="button" class="lm-btn" id="lm-qn">' + (i + 1 >= queue.length && !(!ok && !isRetry) ? 'לסיום' : 'הבא') + '</button></div>';
        if (!ok && !isRetry) retry.push(Object.assign({}, q, { _retry: 1 }));
        var nx = $('#lm-qn', card);
        nx.focus();
        nx.onclick = function () {
          i++;
          if (i >= queue.length && retry.length) { queue = queue.concat(retry); retry = []; }
          show();
        };
      }
      card.querySelectorAll('.lm-qo').forEach(function (b) { b.onclick = function () { pick(+b.getAttribute('data-k')); }; });
      card._pick = pick;
    }
    function keys(e) {
      if (!host.isConnected) { document.removeEventListener('keydown', keys); return; }
      var card = host.querySelector('.lm-qz');
      if (!card) return;
      if (e.key >= '1' && e.key <= '4' && !locked) { card._pick(+e.key - 1); }
      else if (e.key === 'Enter') { var n = $('#lm-qn', card); if (n && locked) n.click(); }
    }
    document.addEventListener('keydown', keys);
    show();
  };

  /* ---------------------------------------------------------- סנכרון הניקוד ולוח המובילים */
  var lastSync = 0;
  Q.syncScore = function () {
    if (offline() || !shareOk()) return Promise.resolve(null);
    var sc = Q.score(); if (!sc.base) return Promise.resolve(null);
    var set = LG.settings();
    lastSync = Date.now();
    return LG.sync.pApi('/qz/score', { total: sc.total, byM: sc.byM, wp: sc.week, optin: !!set.qzOpt, nick: set.qzNick || '' }).catch(function () { return null; });
  };
  Q.board = function (slug) {
    if (offline() || !shareOk()) return Promise.resolve(null);
    var id = LG.sync.identity();
    return LG.sync.api('/qz/board?s=' + encodeURIComponent(slug || '') + '&pid=' + id.pid, { method: 'GET' }).catch(function () { return null; });
  };
  Q.proposers = function () {
    if (offline()) return Promise.resolve(null);
    var id = LG.sync.identity();
    return LG.sync.api('/qz/proposers?pid=' + id.pid, { method: 'GET', headers: { 'x-proposer': id.pt } }).catch(function () { return null; });
  };

  /* ---------------------------------------------------------- מסך "בחן את עצמך" */
  function titleLine(pts, T, names) {
    var l = Q.level(pts, T), nx = T[l];
    return { l: l, name: names[l] || 'עוד בלי תואר', next: nx ? names[l + 1] : '', need: nx ? nx - pts : 0 };
  }
  function ladder(pts, T, names, counts, mine) {
    var h = '<ol class="lm-ladder">';
    for (var i = 1; i <= 5; i++) {
      var got = pts >= T[i - 1];
      var c = counts && counts[i] != null ? Math.max(0, counts[i] - (got ? 1 : 0)) : null;
      h += '<li class="' + (got ? 'on' : '') + '"><b>' + E(names[i]) + '</b> <span>' + LG.nf(T[i - 1]) + ' נקודות</span>' +
        (c != null ? '<em>' + (got ? 'עוד ' : '') + LG.nf(c) + ' ' + (c === 1 ? 'לומד' : 'לומדים') + (got ? ' הגיעו' : ' הגיעו') + ' לדרגה זו</em>' : '') + '</li>';
    }
    return h + '</ol>';
  }

  UI.quiz = async function (root) {
    var qs = new URLSearchParams(location.search), wrap = el('main', 'lm-wrap narrow');
    root.appendChild(wrap);
    var idx = await Q.index();
    var slugs = Object.keys(idx).filter(function (s) { var m = LG.masechet(s); return m && m.built; });
    var host = el('div'); wrap.appendChild(host);
    var cur = qs.get('m') || '';
    if (!cur) { var l = LG.state().last.all; cur = l && idx[l.s] ? l.s : (idx.berakhot ? 'berakhot' : slugs[0]); }

    function home() {
      host.innerHTML = '';
      var sc = Q.score(), due = Q.dueCount(), set = LG.settings();
      var tl = titleLine(sc.total, Q.T_ALL, Q.TITLES_ALL);
      var head = el('div', 'lm-card');
      head.innerHTML = '<h1 class="lm-t" style="margin:0 0 4px">בחן את עצמך</h1>' +
        '<p class="lm-sub" style="margin:0 0 12px">חזרה מרווחת: מה שזכרת מתרחק, ומה שטעית בו חוזר מוקדם.</p>' +
        '<div class="lm-stats"><div class="lm-stat"><b>' + LG.nf(sc.total) + '</b><span>נקודות</span></div>' +
        '<div class="lm-stat"><b>' + E(tl.name) + '</b><span>התואר הכללי' + (tl.next ? ' · עוד ' + LG.nf(tl.need) + ' ל' + E(tl.next) : '') + '</span></div>' +
        '<div class="lm-stat"><b>' + LG.nf(sc.week) + '</b><span>נקודות השבוע</span></div>' +
        (set.streak === false ? '' : '<div class="lm-stat"><b>' + LG.nf(sc.streak) + '</b><span>ימים ברצף תרגול</span></div>') + '</div>';
      host.appendChild(head);

      var modes = el('div', 'lm-card');
      var y = LGDaf.forStr(LG.ymd(Date.now())), yb = idx[y.slug] && LG.masechet(y.slug) && LG.masechet(y.slug).built;
      var opts = slugs.map(function (s) { return '<option value="' + s + '"' + (s === cur ? ' selected' : '') + '>' + E(LG.nameOf(s)) + '</option>'; }).join('');
      modes.innerHTML = '<h3>במה נתרגל?</h3><div class="lm-row">' +
        '<button class="lm-btn" id="lm-qm-due" type="button"' + (due ? '' : ' disabled') + '>החזרות שלי להיום (' + LG.nf(due) + ')</button>' +
        '<button class="lm-btn" id="lm-qm-yomi" type="button"' + (yb ? '' : ' disabled') + '>הדף של היום: ' + E(y.name) + ' ' + E(LG.hebq(y.n)) + '</button></div>' +
        '<div class="lm-row" style="margin-top:12px"><label for="lm-qsel" class="lm-small">המסכת:</label><select id="lm-qsel">' + opts + '</select>' +
        '<button class="lm-btn" id="lm-qm-m" type="button">שאלות על המסכת</button></div>' +
        (due ? '' : '<p class="lm-note">אין היום חזרות שהגיע זמנן. אפשר להתחיל שאלות חדשות.</p>');
      host.appendChild(modes);
      $('#lm-qsel', modes).onchange = function () { cur = this.value; board(); };
      $('#lm-qm-due', modes).onclick = function () { start('due', ''); };
      $('#lm-qm-yomi', modes).onclick = function () { start('yomi', y.slug); };
      $('#lm-qm-m', modes).onclick = function () { start('m', $('#lm-qsel', modes).value); };

      if (!offline() && !LG.sync.linked() && sc.answered >= 3) {
        var tip = el('div', 'lm-hint', 'ההתקדמות שלך שמורה במכשיר הזה בלבד. כדי שלא תאבד אותה (החלפת מכשיר, ניקוי הדפדפן) אפשר <a href="javascript:void 0" id="lm-qsave">לשמור אותה בקוד לומד</a>, בלי שם ובלי סיסמה.');
        tip.style.margin = '0 0 16px'; host.appendChild(tip);
        $('#lm-qsave', tip).onclick = async function () {
          try {
            var code = await LG.sync.makeCode();
            UI.modal('<h3>קוד הלומד שלך</h3><p style="font-size:30px;letter-spacing:4px;text-align:center"><b>' + E(code) + '</b></p><p class="lm-note">ההתקדמות נשמרת מעכשיו גם בשרת, ללא שם. בכל מכשיר אחר: הגדרות, סנכרון, הזנת קוד (תקף עשר דקות).</p>');
          } catch (e) { UI.toast('לא ניתן כרגע: ' + e.message); }
        };
      }
      var bx = el('div'); bx.id = 'lm-qb'; host.appendChild(bx);
      board();
    }

    async function board() {
      var bx = $('#lm-qb'); if (!bx) return;
      var sc = Q.score(), set = LG.settings();
      var mp = sc.byM[cur] || 0, tm = titleLine(mp, Q.T_M, Q.TITLES_M), ta = titleLine(sc.total, Q.T_ALL, Q.TITLES_ALL);
      bx.innerHTML = '<div class="lm-card"><h3>התארים שלך</h3>' +
        '<p><b>כללי:</b> ' + E(ta.name) + ' · <b>' + E(LG.nameOf(cur)) + ':</b> ' + E(tm.name) + (tm.next ? ' (עוד ' + LG.nf(tm.need) + ' נקודות ל' + E(tm.next) + ')' : '') + '</p>' +
        '<div id="lm-lad"></div></div><div id="lm-lb"></div>';
      var data = await Q.board(cur);
      $('#lm-lad', bx).innerHTML = '<h4 style="margin:6px 0">' + E(LG.nameOf(cur)) + '</h4>' + ladder(mp, Q.T_M, Q.TITLES_M, data && data.counts.m) +
        '<h4 style="margin:12px 0 6px">כללי</h4>' + ladder(sc.total, Q.T_ALL, Q.TITLES_ALL, data && data.counts.all);
      var lb = $('#lm-lb', bx), c = el('div', 'lm-card');
      c.innerHTML = '<h3>לוח המובילים</h3>';
      if (!data) { c.innerHTML += '<p class="lm-note">' + (offline() ? 'הלוח אינו זמין במצב הדגמה.' : 'הלוח אינו זמין כרגע.') + '</p>'; lb.appendChild(c); return; }
      var opt = !!set.qzOpt;
      c.innerHTML += '<div class="lm-row"><button class="lm-btn small" id="lm-lbw" type="button">השבוע</button><button class="lm-btn small ghost" id="lm-lba" type="button">כללי</button></div><div id="lm-lbl"></div>' +
        '<div style="margin-top:14px;border-top:1px solid var(--line);padding-top:12px"><label><input type="checkbox" id="lm-lbo"' + (opt ? ' checked' : '') + '> הצג אותי בלוח המובילים</label>' +
        '<div class="lm-row" id="lm-lbn" style="margin-top:8px;' + (opt ? '' : 'display:none') + '"><input id="lm-nick" maxlength="16" placeholder="כינוי (אפשר להשאיר ריק)" value="' + E(set.qzNick || '') + '" style="max-width:220px"><button class="lm-btn small" id="lm-nsave" type="button">שמור כינוי</button></div>' +
        '<p class="lm-note">ההשתתפות בהסכמה בלבד. בלוח מוצג כינוי בלבד (ללא כינוי: "לומד אנונימי" עם מספר), ושום פרט מזהה אינו נחשף.' +
        (data.rank && data.rank.all ? ' מקומך הכללי: ' + LG.nf(data.rank.all) + '.' : '') + '</p></div>';
      lb.appendChild(c);
      function draw(kind) {
        var rows = kind === 'week' ? data.week : data.all;
        $('#lm-lbl', c).innerHTML = rows.length ? '<ol class="lm-lb">' + rows.map(function (r) { return '<li' + (r.me ? ' class="me"' : '') + '><span class="lm-grow">' + E(r.n) + (r.me ? ' (אתה)' : '') + '</span><b>' + LG.nf(r.p) + '</b></li>'; }).join('') + '</ol>' : '<p class="lm-note">עוד אין מי שבחר להופיע בלוח. אפשר להיות הראשון.</p>';
        $('#lm-lbw', c).classList.toggle('ghost', kind !== 'week'); $('#lm-lba', c).classList.toggle('ghost', kind === 'week');
      }
      draw('week');
      $('#lm-lbw', c).onclick = function () { draw('week'); }; $('#lm-lba', c).onclick = function () { draw('all'); };
      $('#lm-lbo', c).onchange = function () { LG.setSetting('qzOpt', this.checked); $('#lm-lbn', c).style.display = this.checked ? '' : 'none'; Q.syncScore().then(function () { UI.toast(opt ? 'הוסרת מהלוח' : 'מעכשיו תופיע בלוח'); }); };
      $('#lm-nsave', c).onclick = function () { LG.setSetting('qzNick', $('#lm-nick', c).value.trim().slice(0, 16)); Q.syncScore().then(function () { UI.toast('הכינוי נשמר'); board(); }); };
    }

    async function start(mode, slug) {
      host.innerHTML = '<div class="lm-card">טוען שאלות...</div>';
      var q = await Q.queue(mode, slug);
      if (!q || !q.length) { host.innerHTML = '<div class="lm-card"><p>' + (q ? 'אין כרגע שאלות לתרגול כאן.' : 'מאגר השאלות של המסכת הזאת עדיין אינו זמין.') + '</p><button class="lm-btn" id="lm-qb0" type="button">חזרה</button></div>'; $('#lm-qb0').onclick = home; return; }
      if (LG.sync && !offline()) LG.sync.heartbeat(slug || q[0].s);
      Q.run(host, q, function (r) {
        var sc = Q.score(), tl = titleLine(sc.total, Q.T_ALL, Q.TITLES_ALL);
        var c = el('div', 'lm-card');
        c.innerHTML = '<h3>סיום הסבב</h3><div class="lm-stats"><div class="lm-stat"><b>' + LG.nf(r.right) + '</b><span>נכונות מתוך ' + LG.nf(r.right + r.wrong) + '</span></div>' +
          '<div class="lm-stat"><b>' + LG.nf(r.pts) + '</b><span>נקודות בסבב</span></div><div class="lm-stat"><b>' + LG.nf(sc.total) + '</b><span>סך הכול</span></div></div>' +
          '<p>התואר הכללי: <b>' + E(tl.name) + '</b>' + (tl.next ? ' · עוד ' + LG.nf(tl.need) + ' נקודות ל' + E(tl.next) : '') + '</p>' +
          '<div class="lm-row"><button class="lm-btn" id="lm-again" type="button">סבב נוסף</button><button class="lm-btn ghost" id="lm-qhome" type="button">למסך הראשי</button></div>';
        host.innerHTML = ''; host.appendChild(c);
        $('#lm-again', c).onclick = function () { start(mode, slug); };
        $('#lm-qhome', c).onclick = home;
      });
    }

    if (qs.get('mode') && qs.get('mode') !== 'home') start(qs.get('mode'), cur); else home();
  };


  /* ---------------------------------------------------------- אישור שאלות טיוטה (מנהל) */
  Q.adminDrafts = async function (box, key) {
    var drafts = {};
    try { drafts = await fetch('quiz/drafts.json').then(function (r) { return r.json(); }); } catch (e) { }
    var slugs = Object.keys(drafts);
    var card = el('div', 'lm-card'); card.id = 'lm-qd';
    card.innerHTML = '<h3>שאלות הבנה בטיוטה</h3><p class="lm-note">נוצרו במודל קל, ומוצגות ללומדים רק אחרי אישורך. "אשר" מפרסם מיד (בלי בנייה מחדש), "ערוך" מאפשר לתקן ניסוח או תשובה.</p><div id="lm-qdl">טוען...</div>';
    box.appendChild(card);
    var list = $('#lm-qdl', card);
    if (!slugs.length) { list.innerHTML = '<p class="lm-note">אין כרגע שאלות טיוטה.</p>'; return; }
    var all = [], decs = {};
    for (var si = 0; si < slugs.length; si++) {
      var s = slugs[si];
      try {
        var d = await fetch('quiz/' + s + '-draft.json').then(function (r) { return r.json(); });
        var dc = await LG.sync.api('/qz/dec?s=' + s, { method: 'GET', headers: { 'x-admin-key': key } });
        decs[s] = dc.dec || {};
        (d.q || []).forEach(function (q) { q.s = s; all.push(q); });
      } catch (e) { }
    }
    function stat() { var ok = 0, no = 0, pend = 0; all.forEach(function (q) { var v = decs[q.s][q.i]; if (!v) pend++; else if (v.st === 'ok') ok++; else no++; }); return { ok: ok, no: no, pend: pend }; }
    function draw() {
      var st = stat(), pend = all.filter(function (q) { return !decs[q.s][q.i]; });
      var h = '<p><b>' + LG.nf(st.pend) + '</b> ממתינות · ' + LG.nf(st.ok) + ' אושרו · ' + LG.nf(st.no) + ' נדחו</p>';
      pend.slice(0, 8).forEach(function (q, n) {
        h += '<div class="lm-qdi" data-n="' + n + '" style="border-top:1px solid var(--line);padding:10px 0"><div class="lm-small">' + E(LG.nameOf(q.s)) + ' · עמוד ' + E(q.d) + '</div>' +
          '<div><b>' + E(q.q) + '</b></div><ol style="margin:6px 0">' + q.o.map(function (o, k) { return '<li' + (k === q.a ? ' style="color:var(--green);font-weight:700"' : '') + '>' + E(o) + '</li>'; }).join('') + '</ol>' +
          '<div class="lm-row"><button class="lm-btn small" data-a="ok" type="button">אשר</button><button class="lm-btn small ghost" data-a="edit" type="button">ערוך</button><button class="lm-btn small ghost" data-a="no" type="button">דחה</button></div></div>';
      });
      if (pend.length > 8) h += '<p class="lm-note">ועוד ' + LG.nf(pend.length - 8) + ' בהמשך.</p>';
      if (!pend.length) h += '<p class="lm-note">אין שאלות ממתינות.</p>';
      list.innerHTML = h;
      list.querySelectorAll('.lm-qdi').forEach(function (row) {
        var q = pend[+row.getAttribute('data-n')];
        function save(st, e) {
          LG.sync.api('/qz/dec', { method: 'POST', headers: { 'x-admin-key': key }, body: JSON.stringify({ s: q.s, id: q.i, st: st, e: e || null }) })
            .then(function () { decs[q.s][q.i] = { st: st, e: e || null }; draw(); }).catch(function (er) { UI.toast('לא נשמר: ' + er.message); });
        }
        row.querySelector('[data-a=ok]').onclick = function () { save('ok'); };
        row.querySelector('[data-a=no]').onclick = function () { save('no'); };
        row.querySelector('[data-a=edit]').onclick = function () {
          var f = el('div'); f.style.marginTop = '8px';
          f.innerHTML = '<textarea rows="2" style="width:100%" id="eq">' + E(q.q) + '</textarea>' + q.o.map(function (o, k) { return '<div><label><input type="radio" name="ea" value="' + k + '"' + (k === q.a ? ' checked' : '') + '> </label><input class="eo" value="' + E(o) + '" style="width:85%"></div>'; }).join('') +
            '<div class="lm-row"><button class="lm-btn small" id="esv" type="button">שמור ואשר</button></div>';
          row.appendChild(f);
          f.querySelector('#esv').onclick = function () {
            save('ok', { q: f.querySelector('#eq').value.trim(), o: [].map.call(f.querySelectorAll('.eo'), function (i) { return i.value.trim(); }), a: +f.querySelector('input[name=ea]:checked').value });
          };
        };
      });
    }
    draw();
  };

  /* ---------------------------------------------------------- כרטיס מעמד המגיה ושורת "לומדים כעת" */
  Q.proposerCard = async function () {
    var d = await Q.proposers();
    if (!d || !d.me) return null;
    var m = d.me, c = el('div', 'lm-card');
    if (!m.ok && !m.ed && !m.no) return null;
    var h = '<h3>מעמד המגיה שלך</h3><div class="lm-stats"><div class="lm-stat"><b>' + E(m.title || 'עוד בלי תואר') + '</b><span>התואר</span></div>' +
      '<div class="lm-stat"><b>' + LG.nf(m.p) + '</b><span>נקודות הגהה</span></div>' +
      '<div class="lm-stat"><b>' + LG.nf(m.ok + m.ed) + '</b><span>הצעות שאושרו</span></div>' +
      (m.rank ? '<div class="lm-stat"><b>' + LG.nf(m.rank) + '</b><span>מקום בדירוג</span></div>' : '') + '</div>';
    if (m.next) {
      h += '<p>לדרגה הבאה, <b>' + E(m.next.title) + '</b>: חסרות ' + LG.nf(m.next.need) + ' נקודות' + (m.next.rank ? ', ובנוסף מקום ' + m.next.rank + ' או גבוה יותר בדירוג' : '') + '.</p>';
    } else if (m.title) h += '<p>זו הדרגה הגבוהה ביותר. יישר כוחך.</p>';
    if (m.firstIn && m.firstIn.length) h += '<p>אות הוקרה: הראשון להגיה במסכתות ' + m.firstIn.map(function (s) { return E(LG.nameOf(s)); }).join(', ') + '.</p>';
    h += '<p class="lm-note">הניקוד: הצעה שאושרה = נקודה, הצעה שאושרה בעריכה = 0.8, ועם משקל לאיכות (שיעור ההצעות שאושרו מתוך אלה שהוכרעו). הצעה שממתינה אינה נספרת.</p>';
    if (d.top && d.top.length) h += '<details><summary>המגיהים המובילים</summary><ol class="lm-lb">' + d.top.slice(0, 10).map(function (r) { return '<li' + (r.me ? ' class="me"' : '') + '><span class="lm-grow">' + E(r.n) + (r.title ? ' · ' + E(r.title) : '') + '</span><b>' + LG.nf(r.p) + '</b></li>'; }).join('') + '</ol></details>';
    c.innerHTML = h;
    return c;
  };
  /* "כעת לומדים באתר: X" - מונה אנונימי ומכובד; מוסתר אם אין נתון אמין */
  Q.liveLine = function (slug) {
    var s = el('p', 'lm-live'); s.style.cssText = 'margin:8px 0 0;font-size:14px;text-align:center';
    if (offline()) return s;
    if (LG.sync) LG.sync.heartbeat(slug || '');
    var go = function () {
      LG.sync.online(slug).then(function (j) {
        if (!j || !j.ok || !j.n || j.n < 20) { s.textContent = ''; return; }
        s.textContent = 'כעת לומדים באתר: ' + LG.nf(j.n) + (slug && j.s ? ' · במסכת זו: ' + LG.nf(j.s) : '');
      });
    };
    setTimeout(go, 1200);
    var t = setInterval(function () { if (!s.isConnected) return clearInterval(t); if (document.visibilityState === 'visible') { LG.sync.heartbeat(slug || ''); go(); } }, 150000);
    return s;
  };
})();
