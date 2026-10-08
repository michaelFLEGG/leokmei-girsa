/* lamed - "בחן את עצמך": שדרוג 7.10.2026. שאלות מוגהות בלבד (data/quiz/<מסכת>.reviewed.txt),
   שני ממשקים (בחור / אברך), תגמול מיידי, רצף, צלילים ומסך סיום.
   כל תשובה נשמרת כאירוע (k:'qa') באותו מנגנון של מערכת הלומד: נשמרת במכשיר, ומסונכרנת
   בין מכשירים בקוד לומד, באותו שירות קיים. הניקוד נגזר מן האירועים.

   ניקוד (מיד, בכל תשובה נכונה בניסיון ראשון): קל 10, בינוני 20, קשה 30.
   בונוס רצף: מהתשובה הנכונה השלישית ברצף +5, ואז +10 ... עד +25 לכל תשובה. טעות מאפסת.
   החזרה המרווחת (SM-2 מצומצם) נשארת רק לקביעת "החזרות שלי להיום": היא אינה משפיעה על הניקוד.
   שאלה שנענתה לפני זמנה מסומנת pr ואינה משנה את מועד החזרה, אך מזכה בניקוד. */
(function () {
  'use strict';
  var LG = window.LAMED, UI = LG.ui, E = LG.esc, $ = UI.$, el = UI.el;
  var Q = LG.quiz = {};

  /* ---------------------------------------------------------- תארים */
  Q.T_ALL = [100, 600, 2000, 6000, 20000];
  Q.T_M = [60, 300, 1000, 3000, 8000];
  Q.TITLES_M = ['', 'לומד המסכת', 'תלמיד חכם', 'חכם', 'גאון', 'גאון עצום'];
  Q.TITLES_ALL = ['', 'לומד הש"ס', 'תלמיד חכם', 'חכם', 'גאון', 'גאון עצום'];
  Q.level = function (pts, T) { var l = 0; T.forEach(function (x, i) { if (pts >= x) l = i + 1; }); return l; };
  Q.LVL = { 1: { n: 'קל', pts: 10 }, 2: { n: 'בינוני', pts: 20 }, 3: { n: 'קשה', pts: 30 } };
  var ROUND = 10;
  var PEREK = ['', 'א', 'ב', 'ג', 'ד', 'ה', 'ו', 'ז', 'ח', 'ט', 'י', 'יא', 'יב', 'יג', 'יד', 'טו', 'טז', 'יז', 'יח', 'יט', 'כ', 'כא', 'כב', 'כג', 'כד'];

  function api() { return LG.sync; }
  function offline() { return window.__lmDemo || !LG.sync; }
  function shareOk() { return LG.settings().share !== false; }
  function reduced() { try { return window.matchMedia('(prefers-reduced-motion: reduce)').matches; } catch (e) { return false; } }

  /* הדף בקובץ המוגה הוא 'לה ע"א'; בשאר האתר (עוגנים, הדף היומי) 'לה.' ו'לה:' */
  function siteDaf(d) { return String(d).replace(/ ע"א$/, '.').replace(/ ע"ב$/, ':'); }

  /* ---------------------------------------------------------- בנק שאלות (מוגהות בלבד) */
  var banks = {};
  Q.bank = function (slug) {
    if (banks[slug]) return banks[slug];
    banks[slug] = fetch('quiz/' + slug + '.json').then(function (r) { if (!r.ok) throw 0; return r.json(); }).then(function (b) {
      var by = {}; b.q.forEach(function (q) { q.sd = siteDaf(q.d); by[q.i] = q; });
      return { slug: slug, name: b.name, q: b.q, by: by };
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
    /* רק שאלות מוגהות (מזהה r:...). אירועים ישנים משאלות מכניות נשארים בניקוד, לא בחזרות */
    LG.events().filter(function (e) { return e.k === 'qa' && !e.pr && String(e.q).indexOf('r:') === 0; }).sort(function (a, b) { return a.t - b.t; }).forEach(function (e) {
      var c = C[e.q] || (C[e.q] = { q: e.q, s: e.s, rep: 0, ease: 2.5, ivl: 0, n: 0, ok: 0, last: 0, lastOk: 0, due: '' });
      if (e.ok) { c.rep++; c.ok++; c.ivl = c.rep === 1 ? 1 : (c.rep === 2 ? 6 : Math.round(c.ivl * c.ease)); c.lastOk = e.t; }
      else { c.rep = 0; c.ivl = 1; c.ease = Math.max(1.3, c.ease - 0.2); }
      c.last = e.t; c.n++; c.due = LG.addDays(LG.ymd(e.t), c.ivl);
    });
    return C;
  };
  function weekStart(today) { var dow = new Date(LG.ymdToUTC(today) + 43200000).getUTCDay(); return LG.addDays(today, -dow); }
  Q.score = function () {
    var today = LG.ymd(Date.now()), wk = weekStart(today), days = {}, byM = {}, total = 0, wpts = 0, answered = 0, right = 0;
    LG.events().forEach(function (e) {
      if (e.k !== 'qa') return;
      answered++; if (e.ok) right++;
      if (!e.pts) return;
      var d = LG.ymd(e.t);
      days[d] = (days[d] || 0) + e.pts; byM[e.s] = (byM[e.s] || 0) + e.pts; total += e.pts;
      if (d >= wk) wpts += e.pts;
    });
    var ds = Object.keys(days).sort(), run = 0, prev = null, curRun = 0;
    ds.forEach(function (d) {
      run = (prev && LG.diffDays(prev, d) === 1) ? run + 1 : 1; prev = d;
      curRun = (d === today || LG.diffDays(d, today) === 1) ? run : 0;
    });
    return { total: total, base: total, bonus: 0, byM: byM, week: wpts, streak: curRun, answered: answered, right: right, today: days[today] || 0 };
  };
  Q.dueCount = function () {
    var C = Q.cards(), today = LG.ymd(Date.now()), n = 0;
    Object.keys(C).forEach(function (k) { if (C[k].due <= today) n++; });
    return n;
  };

  /* מתעד תשובה. pts כולל את בונוס הרצף (bn). המועד הבא של החזרה המרווחת נקבע בנפרד. */
  Q.record = function (q, ok, ms, pts, bn) {
    var C = Q.cards(), c = C[q.i], today = LG.ymd(Date.now());
    var isDue = !c || c.due <= today;
    var e = { k: 'qa', q: q.i, s: q.s, ok: ok ? 1 : 0, t: Date.now(), ms: Math.min(120000, ms || 0), lv: q.lvl };
    if (!isDue) e.pr = 1;
    if (pts) { e.pts = pts; if (bn) e.bn = bn; }
    LG.put(e);
    var c2 = Q.cards()[q.i];
    return { practice: !isDue, ivl: c2 ? c2.ivl : 0, due: c2 ? c2.due : '' };
  };

  /* ---------------------------------------------------------- בחירת סבב */
  function shuffle(a, seed) {
    var r = seed || Math.random, i, j, t;
    for (i = a.length - 1; i > 0; i--) { j = Math.floor(r() * (i + 1)); t = a[i]; a[i] = a[j]; a[j] = t; }
    return a;
  }
  /* mode: due / yomi / m. perek: 0 = כל המסכת. lvl: 1, 2, 3 או 0 = מעורב (מדורג מקל לקשה) */
  Q.queue = async function (mode, slug, perek, lvl) {
    var C = Q.cards(), today = LG.ymd(Date.now());
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
      return due.slice(0, ROUND).map(function (x) { return x.q; }).sort(function (a, b) { return a.lvl - b.lvl; });
    }
    var bank = await Q.bank(slug);
    if (!bank) return null;
    var pool = bank.q;
    if (mode === 'yomi') {
      var y = LGDaf.forStr(today), a0 = LG.dafLabel(y.n, 0), a1 = LG.dafLabel(y.n, 1), k0 = LG.dafKey(a0);
      var near = pool.filter(function (q) { return q.sd === a0 || q.sd === a1; });
      for (var w = 2; near.length < ROUND && w <= 12; w += 2) {
        near = pool.filter(function (q) { return Math.abs(LG.dafKey(q.sd) - k0) <= w; });
      }
      pool = near.length >= 3 ? near : pool;
    } else {
      if (perek) pool = pool.filter(function (q) { return q.p === perek; });
      if (lvl) pool = pool.filter(function (q) { return q.lvl === lvl; });
    }
    /* עדיפות: חזרות שהגיע זמנן, אחר כך חדשות, אחר כך השאר */
    var dueQ = [], newQ = [], restQ = [];
    pool.forEach(function (q) {
      var c = C[q.i], x = tag(bank, q);
      if (!c) newQ.push(x); else if (c.due <= today) dueQ.push(x); else restQ.push(x);
    });
    shuffle(dueQ); shuffle(newQ); shuffle(restQ);
    var ranked = dueQ.concat(newQ, restQ), out = [];
    if (lvl) { out = ranked.slice(0, ROUND); }
    else {
      /* מעורב: בערך 4 קלות, 3 בינוניות, 3 קשות (כשיש), והשאר ממלא */
      var quota = { 1: 4, 2: 3, 3: 3 }, left = ranked.slice();
      [1, 2, 3].forEach(function (L) {
        var n = 0;
        left = left.filter(function (q) { if (q.lvl === L && n < quota[L] && out.length < ROUND) { out.push(q); n++; return false; } return true; });
      });
      while (out.length < ROUND && left.length) out.push(left.shift());
    }
    /* מדורג מקל לקשה; בתוך רמה הסדר אקראי (מיון יציב) */
    out = out.map(function (q, i) { return [q, i]; }).sort(function (a, b) { return (a[0].lvl - b[0].lvl) || (a[1] - b[1]); }).map(function (x) { return x[0]; });
    return out;
  };

  /* ---------------------------------------------------------- צלילים (Web Audio, בלי קובצי שמע) */
  var AC = null;
  Q.sfxLog = [];
  function actx() {
    if (AC) return AC;
    var C = window.AudioContext || window.webkitAudioContext;
    if (!C) return null;
    try { AC = new C(); } catch (e) { AC = null; }
    return AC;
  }
  Q.unlockAudio = function () { var a = actx(); if (a && a.state === 'suspended') a.resume().catch(function () { }); };
  function persona() { return LG.settings().qzUi === 'avrech' ? 'avrech' : (LG.settings().qzUi === 'bahur' ? 'bahur' : ''); }
  Q.soundOn = function () {
    var s = LG.settings();
    if (s.qzSnd === true || s.qzSnd === false) return s.qzSnd;
    return s.qzUi === 'bahur';
  };
  function tone(freq, t0, dur, type, vol) {
    var a = AC; if (!a) return;
    var o = a.createOscillator(), g = a.createGain(), t = a.currentTime + t0;
    o.type = type || 'sine'; o.frequency.setValueAtTime(freq, t);
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(vol || 0.12, t + 0.015);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    o.connect(g); g.connect(a.destination); o.start(t); o.stop(t + dur + 0.05);
  }
  /* name: ok / bad / streak (גובה לפי אורך הרצף) / fan (תרועת סיום) / level (תואר חדש) */
  Q.sfx = function (name) {
    if (!Q.soundOn()) return;
    Q.sfxLog.push(name);
    if (!actx()) return;
    Q.unlockAudio();
    if (name === 'ok') { tone(784, 0, 0.18, 'sine', 0.11); tone(1175, 0.09, 0.26, 'sine', 0.1); }
    else if (name === 'bad') { tone(196, 0, 0.28, 'triangle', 0.1); tone(165, 0.12, 0.32, 'triangle', 0.08); }
    else if (name === 'streak') { [523, 659, 784, 1047].forEach(function (f, i) { tone(f, i * 0.07, 0.2, 'sine', 0.1); }); }
    else if (name === 'fan' || name === 'level') { [523, 659, 784, 1047, 784, 1047, 1319].forEach(function (f, i) { tone(f, i * 0.11, i > 5 ? 0.5 : 0.22, 'triangle', 0.1); }); }
  };

  /* ---------------------------------------------------------- אנימציות */
  function roll(node, from, to) {
    if (reduced() || from === to) { node.textContent = LG.nf(to); return; }
    var t0 = performance.now(), dur = 700;
    function step(t) {
      var k = Math.min(1, (t - t0) / dur);
      node.textContent = LG.nf(Math.round(from + (to - from) * (1 - Math.pow(1 - k, 3))));
      if (k < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }
  function fly(fromEl, text, toEl, gentle, done) {
    if (reduced() || !fromEl || !toEl || !fromEl.animate) return done();
    var f = el('div', 'qz-fly' + (gentle ? ' gentle' : ''), E(text)), a = fromEl.getBoundingClientRect(), b = toEl.getBoundingClientRect();
    f.style.left = (a.left + a.width / 2 - 20) + 'px'; f.style.top = (a.top + a.height / 2 - 14) + 'px';
    document.body.appendChild(f);
    var dx = b.left + b.width / 2 - (a.left + a.width / 2), dy = b.top + b.height / 2 - (a.top + a.height / 2);
    var an = f.animate(gentle ?
      [{ transform: 'translate(0,0)', opacity: 0 }, { transform: 'translate(0,-6px)', opacity: 1, offset: .25 }, { transform: 'translate(' + dx + 'px,' + dy + 'px)', opacity: 0 }] :
      [{ transform: 'translate(0,0) scale(1.5)', opacity: 1 }, { transform: 'translate(' + dx + 'px,' + dy + 'px) scale(.8)', opacity: .95 }],
      { duration: gentle ? 700 : 850, easing: 'cubic-bezier(.4,0,.2,1)' });
    an.onfinish = function () { f.remove(); done(); };
  }
  function confetti() {
    if (reduced()) return;
    var cols = ['#e53935', '#fb8c00', '#fdd835', '#43a047', '#1e88e5', '#8e24aa'], layer = el('div', 'qz-confetti');
    document.body.appendChild(layer);
    for (var i = 0; i < 70; i++) {
      var c = el('i'); c.style.background = cols[i % cols.length]; c.style.left = Math.random() * 100 + '%';
      layer.appendChild(c);
      if (c.animate) c.animate([{ transform: 'translate(0,-20px) rotate(0)', opacity: 1 }, { transform: 'translate(' + (Math.random() * 160 - 80) + 'px,' + (window.innerHeight + 40) + 'px) rotate(' + (Math.random() * 720) + 'deg)', opacity: .9 }],
        { duration: 1800 + Math.random() * 1400, delay: Math.random() * 500, easing: 'ease-in', fill: 'forwards' });
    }
    setTimeout(function () { layer.remove(); }, 4200);
  }

  /* ---------------------------------------------------------- סבב שאלות */
  var COLORS = ['', 'ok', 'mid', 'hard'];
  Q.run = function (host, queue, ctx, onEnd) {
    var pers = persona() || 'bahur';
    var n0 = queue.length, i = 0, res = { right: 0, wrong: 0, pts: 0, streak: 0, best: 0, missed: [], total0: Q.score().total, marks: [] };
    var retry = [], t0 = 0, locked = false, advanced = false, modalOpen = false, perm = [], ptsShown = res.total0;
    function end() { Q.syncScore(); document.removeEventListener('keydown', keys); onEnd(res); }
    function show() {
      if (i >= queue.length) return end();
      var q = queue[i], isRetry = !!q._retry, card = el('div', 'lm-card lm-qz qz-card qz-l' + q.lvl);
      locked = false; advanced = false; t0 = Date.now();
      perm = shuffle([0, 1, 2, 3]);               /* סדר התשובות מעורבב בכל הצגה; הנכונה היא o[0] */
      var correctAt = perm.indexOf(0);
      var track = '';
      for (var k = 0; k < n0; k++) track += '<li class="' + (res.marks[k] || (k === i ? 'cur' : '')) + '" aria-label="שאלה ' + (k + 1) + '">★</li>';
      var opts = perm.map(function (pi, k) { return '<button type="button" class="qz-opt qz-c' + k + '" data-k="' + k + '"><b>' + (k + 1) + '</b><span>' + E(q.o[pi]) + '</span></button>'; }).join('');
      card.innerHTML =
        '<div class="qz-hud"><div class="qz-pts" aria-live="off"><small>נקודות</small><b id="qz-pts">' + LG.nf(ptsShown) + '</b></div>' +
        '<div class="qz-str' + (res.streak >= 3 ? ' hot' : '') + '" id="qz-str"><small>רצף</small><b>' + res.streak + '</b></div></div>' +
        '<ol class="qz-track" aria-label="התקדמות בסבב">' + track + '</ol>' +
        '<div class="qz-meta"><span class="qz-chip qz-lv' + q.lvl + '">' + Q.LVL[q.lvl].n + ' · ' + Q.LVL[q.lvl].pts + ' נקודות</span>' +
        '<span class="lm-small">שאלה ' + Math.min(i + 1, queue.length) + ' מתוך ' + queue.length + ' · ' + E(LG.nameOf(q.s)) + ' פרק ' + E(PEREK[q.p] || q.p) + (isRetry ? ' · ניסיון חוזר (בלי ניקוד)' : '') + '</span></div>' +
        '<h3 class="lm-qq">' + E(q.q) + '</h3><div class="qz-opts" role="group" aria-label="תשובות">' + opts + '</div><div class="qz-fb" aria-live="polite"></div>';
      host.innerHTML = ''; host.appendChild(card);
      card.querySelectorAll('.qz-opt').forEach(function (b) { b.onclick = function () { pick(+b.getAttribute('data-k')); }; });
      card._pick = pick;
      function pick(k) {
        if (locked || modalOpen) return; locked = true;
        Q.unlockAudio();
        var ok = k === correctAt, btns = card.querySelectorAll('.qz-opt'), fb = $('.qz-fb', card);
        btns.forEach(function (b, n) { b.disabled = true; if (n === correctAt) b.classList.add('qz-right'); else if (n === k) b.classList.add('qz-wrong'); });
        var pts = 0, bn = 0, before = Q.score(), titleUp = null;
        if (!isRetry) {
          if (ok) {
            res.streak++; res.best = Math.max(res.best, res.streak); res.right++;
            bn = res.streak >= 3 ? Math.min(25, 5 * (res.streak - 2)) : 0;
            pts = Q.LVL[q.lvl].pts + bn;
          } else { res.streak = 0; res.wrong++; res.missed.push({ q: q, picked: q.o[perm[k]] }); }
          res.marks[Math.min(i, n0 - 1)] = ok ? 'ok' : 'bad';
          var r = Q.record(q, ok, Date.now() - t0, pts, bn);
          res.pts += pts;
          var after = Q.score();
          var lA = Q.level(before.total, Q.T_ALL), lB = Q.level(after.total, Q.T_ALL);
          var mA = Q.level(before.byM[q.s] || 0, Q.T_M), mB = Q.level(after.byM[q.s] || 0, Q.T_M);
          if (lB > lA) titleUp = { name: Q.TITLES_ALL[lB], scope: 'הכללי' };
          else if (mB > mA) titleUp = { name: Q.TITLES_M[mB], scope: 'במסכת ' + LG.nameOf(q.s) };
        }
        var track = card.querySelectorAll('.qz-track li');
        if (track[i] && !isRetry) { track[i].className = ok ? 'ok' : 'bad'; }
        var href = UI.readHref(q.s, q.sd);
        if (ok) {
          Q.sfx(res.streak === 3 || res.streak === 5 || res.streak === 10 ? 'streak' : 'ok');
          if (pts) {
            var from = ptsShown; ptsShown += pts;
            fly(btns[correctAt], '+' + pts, $('#qz-pts', card), pers === 'avrech', function () { roll($('#qz-pts', card) || document.createElement('b'), from, ptsShown); });
            $('#qz-str b', card).textContent = res.streak;
            $('#qz-str', card).classList.toggle('hot', res.streak >= 3);
          }
        } else {
          Q.sfx('bad');
          $('#qz-str b', card).textContent = 0; $('#qz-str', card).classList.remove('hot');
        }
        var msg = ok ? '<b class="lm-okt">נכון!</b>' + (pts ? ' +' + pts + ' נקודות' + (bn ? ' (כולל בונוס רצף ' + bn + '+)' : '') : '') :
          '<b class="lm-badt">לא נכון.</b> התשובה: <b>' + E(q.o[0]) + '</b>';
        fb.innerHTML = '<p class="qz-msg">' + msg + '</p>' +
          (q.x ? '<p class="qz-exp' + (ok ? ' small' : '') + '">' + E(q.x) + '</p>' : '') +
          (!ok && href ? '<p class="lm-note"><a href="' + href + '" target="_blank" rel="noopener">למקום בגמרא: ' + E(LG.nameOf(q.s)) + ' ' + E(q.d) + '</a></p>' : '') +
          '<div class="lm-row"><button type="button" class="lm-btn pri" id="qz-next">הבא</button></div>';
        if (!ok && !isRetry) retry.push(Object.assign({}, q, { _retry: 1 }));
        var nx = $('#qz-next', card);
        if (i + 1 >= queue.length && !retry.length) nx.textContent = 'לסיום';
        nx.focus({ preventScroll: true });
        nx.onclick = go;
        if (titleUp) {
          setTimeout(function () {
            modalOpen = true; Q.sfx('level');
            var m = UI.modal('<div class="qz-title-up">' + LG.brand.gate() + '<div class="qz-big">★</div><h3>תואר חדש!</h3><p>הגעת לתואר <b>' + E(titleUp.name) + '</b> (' + E(titleUp.scope) + ')</p><div class="lm-row"><button type="button" class="lm-btn pri" id="qz-tu">המשך</button></div></div>', function () { modalOpen = false; });
            if (pers === 'bahur') confetti();
            var b = m.querySelector('#qz-tu'); if (b) { b.onclick = function () { m.close(); }; b.focus(); }
          }, reduced() ? 100 : 900);
        }
      }
      function go() {
        if (advanced || modalOpen) return; advanced = true;
        i++;
        if (i >= queue.length && retry.length) { queue = queue.concat(retry); retry = []; }
        show();
      }
      card._go = go;
    }
    function keys(e) {
      if (!host.isConnected) { document.removeEventListener('keydown', keys); return; }
      var card = host.querySelector('.qz-card');
      if (!card || modalOpen || e.ctrlKey || e.metaKey || e.altKey) return;
      if (e.key >= '1' && e.key <= '4' && !locked) { e.preventDefault(); card._pick(+e.key - 1); }
      else if (e.key === 'Enter' && locked) { e.preventDefault(); card._go(); }
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
    var qs = new URLSearchParams(location.search), wrap = el('main', 'lm-wrap narrow qz');
    root.appendChild(wrap);
    var idx = await Q.index();
    var slugs = Object.keys(idx).filter(function (s) { var m = LG.masechet(s); return m && m.built && idx[s] > 0; });
    var bar = el('div', 'qz-bar'), host = el('div'), snd = el('button', 'qz-snd');
    snd.type = 'button';
    wrap.appendChild(bar); wrap.appendChild(host);
    wrap.appendChild(snd);
    var want = qs.get('m') || '';
    var cur = want && idx[want] ? want : '';
    if (!cur) { var l = LG.state().last.all; cur = l && idx[l.s] ? l.s : (slugs.indexOf('sukkah') > -1 ? 'sukkah' : slugs[0]); }
    var sel = { perek: 0, lvl: 0 };

    function applyPersona() {
      var p = persona();
      wrap.className = 'lm-wrap narrow qz' + (p ? ' qz-' + p : '');
      bar.innerHTML = p ? '<span class="lm-small">ממשק: <b>' + (p === 'bahur' ? 'בחור' : 'אברך') + '</b></span> <a href="javascript:void 0" id="qz-sw">החלף ממשק</a>' : '';
      var sw = $('#qz-sw', bar);
      if (sw) sw.onclick = function () {
        var np = persona() === 'bahur' ? 'avrech' : 'bahur';
        LG.setSetting('qzUi', np); LG.setSetting('qzSnd', np === 'bahur');
        applyPersona(); home();
      };
      drawSnd();
    }
    function drawSnd() {
      var on = Q.soundOn();
      snd.className = 'qz-snd' + (on ? ' on' : '');
      snd.setAttribute('aria-pressed', on ? 'true' : 'false');
      snd.setAttribute('aria-label', on ? 'כיבוי הצלילים' : 'הדלקת הצלילים');
      snd.title = on ? 'כיבוי הצלילים' : 'הדלקת הצלילים';
      snd.innerHTML = '<svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><path d="M4 9v6h4l5 4V5L8 9H4z" fill="currentColor"/>' +
        (on ? '<path d="M16 8.5a5 5 0 0 1 0 7M18.5 6a8.5 8.5 0 0 1 0 12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>' : '<path d="M16 9l5 6M21 9l-5 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>') + '</svg>';
    }
    snd.onclick = function () {
      LG.setSetting('qzSnd', !Q.soundOn()); drawSnd();
      if (Q.soundOn()) { Q.unlockAudio(); Q.sfx('ok'); }
    };

    /* ---- שתי הדלתות */
    function doors(next) {
      host.innerHTML = '';
      var c = el('div', 'lm-card qz-doors');
      c.innerHTML = '<h1 class="lm-t" style="margin:0 0 4px">בחן את עצמך</h1><p class="lm-sub">איך נוח לך ללמוד ולהיבחן? אותן שאלות ואותו ניקוד בשני הממשקים, ואפשר להחליף בכל עת.</p>' +
        '<div class="qz-door-row"><button type="button" class="qz-door bahur" data-p="bahur"><b>בחור</b><span>ממשק צבעוני, צלילים ואנימציות</span></button>' +
        '<button type="button" class="qz-door avrech" data-p="avrech"><b>אברך</b><span>ממשק שקט ומכובד, בלי צלילים</span></button></div>';
      host.appendChild(c);
      c.querySelectorAll('.qz-door').forEach(function (b) {
        b.onclick = function () {
          var p = b.getAttribute('data-p');
          LG.setSetting('qzUi', p); LG.setSetting('qzSnd', p === 'bahur');
          Q.unlockAudio(); applyPersona();
          if (p === 'bahur') Q.sfx('ok');
          next();
        };
      });
      $('.qz-door', c).focus({ preventScroll: true });
    }

    function seg(id, items, val) {
      return '<div class="qz-seg" id="' + id + '" role="radiogroup">' + items.map(function (x) {
        return '<button type="button" role="radio" aria-checked="' + (x[0] === val) + '" class="' + (x[0] === val ? 'on' : '') + '" data-v="' + x[0] + '">' + E(x[1]) + '</button>';
      }).join('') + '</div>';
    }

    async function home() {
      host.innerHTML = '';
      var sc = Q.score(), due = Q.dueCount(), set = LG.settings();
      var tl = titleLine(sc.total, Q.T_ALL, Q.TITLES_ALL);
      var head = el('div', 'lm-card');
      head.innerHTML = LG.brand.gate() + '<h1 class="lm-t" style="margin:0 0 4px;text-align:center">בחן את עצמך</h1>' +
        '<p class="lm-sub" style="margin:0 0 12px">שאלות מוגהות על הלימוד, עם ניקוד מיידי על כל תשובה נכונה.</p>' +
        '<div class="lm-stats"><div class="lm-stat"><b>' + LG.nf(sc.total) + '</b><span>נקודות</span></div>' +
        '<div class="lm-stat"><b>' + E(tl.name) + '</b><span>התואר הכללי' + (tl.next ? ' · עוד ' + LG.nf(tl.need) + ' ל' + E(tl.next) : '') + '</span></div>' +
        '<div class="lm-stat"><b>' + LG.nf(sc.week) + '</b><span>נקודות השבוע</span></div>' +
        (set.streak === false ? '' : '<div class="lm-stat"><b>' + LG.nf(sc.streak) + '</b><span>ימים ברצף תרגול</span></div>') + '</div>';
      host.appendChild(head);

      var modes = el('div', 'lm-card');
      var y = LGDaf.forStr(LG.ymd(Date.now())), yb = idx[y.slug] && LG.masechet(y.slug) && LG.masechet(y.slug).built;
      if (!slugs.length) {
        modes.innerHTML = '<p>השאלות בהכנה. עוד מעט יהיו כאן.</p>'; host.appendChild(modes); return;
      }
      var bank = await Q.bank(cur);
      var pereks = bank ? Array.from(new Set(bank.q.map(function (q) { return q.p; }))).sort(function (a, b) { return a - b; }) : [];
      if (sel.perek && pereks.indexOf(sel.perek) < 0) sel.perek = 0;
      var opts = slugs.map(function (s) { return '<option value="' + s + '"' + (s === cur ? ' selected' : '') + '>' + E(LG.nameOf(s)) + '</option>'; }).join('');
      var notice = want && !idx[want] ? '<p class="qz-soon">השאלות למסכת ' + E(LG.nameOf(want)) + ' בהכנה.</p>' : '';
      modes.innerHTML = notice + '<h3>סבב של ' + ROUND + ' שאלות</h3>' +
        '<div class="qz-field"><label for="lm-qsel">מסכת</label><select id="lm-qsel">' + opts + '</select></div>' +
        '<div class="qz-field"><label>פרק</label>' + seg('qz-pk', [[0, 'כל המסכת']].concat(pereks.map(function (p) { return [p, 'פרק ' + (PEREK[p] || p)]; })), sel.perek) + '</div>' +
        '<div class="qz-field"><label>רמה</label>' + seg('qz-lv', [[1, 'קל'], [2, 'בינוני'], [3, 'קשה'], [0, 'מעורב']], sel.lvl) + '</div>' +
        '<div class="lm-row" style="margin-top:14px"><button class="lm-btn pri qz-go" id="lm-qm-m" type="button">התחל סבב</button></div>' +
        '<h3 style="margin-top:22px">מסלולים</h3><div class="lm-row">' +
        '<button class="lm-btn" id="lm-qm-due" type="button"' + (due ? '' : ' disabled') + '>החזרות שלי להיום (' + LG.nf(due) + ')</button>' +
        (yb ? '<button class="lm-btn" id="lm-qm-yomi" type="button">הדף של היום: ' + E(y.name) + ' ' + E(LG.hebq(y.n)) + '</button>' :
          '<button class="lm-btn" id="lm-qm-yomi" type="button" disabled>הדף של היום: השאלות למסכת ' + E(y.name) + ' בהכנה</button>') + '</div>' +
        (due ? '' : '<p class="lm-note">אין היום חזרות שהגיע זמנן. אפשר להתחיל סבב חדש.</p>');
      host.appendChild(modes);
      $('#lm-qsel', modes).onchange = function () { cur = this.value; want = ''; sel.perek = 0; home(); };
      function bindSeg(id, key) {
        modes.querySelectorAll('#' + id + ' button').forEach(function (b) {
          b.onclick = function () {
            sel[key] = +b.getAttribute('data-v');
            modes.querySelectorAll('#' + id + ' button').forEach(function (x) { var on = x === b; x.classList.toggle('on', on); x.setAttribute('aria-checked', on); });
          };
        });
      }
      bindSeg('qz-pk', 'perek'); bindSeg('qz-lv', 'lvl');
      $('#lm-qm-due', modes).onclick = function () { start('due', '', 0, 0); };
      if (yb) $('#lm-qm-yomi', modes).onclick = function () { start('yomi', y.slug, 0, 0); };
      $('#lm-qm-m', modes).onclick = function () { start('m', cur, sel.perek, sel.lvl); };

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

    function endScreen(r, mode, slug, perek, lvl) {
      var total = r.right + r.wrong, pct = total ? Math.round(100 * r.right / total) : 0;
      var stars = pct >= 90 ? 3 : (pct >= 60 ? 2 : 1);
      var sc = Q.score(), tl = titleLine(sc.total, Q.T_ALL, Q.TITLES_ALL), pers = persona() || 'bahur';
      var c = el('div', 'lm-card qz-end');
      var st = ''; for (var k = 1; k <= 3; k++) st += '<span class="' + (k <= stars ? 'on' : '') + '">★</span>';
      var harder = pct >= 80 && lvl !== 3 && mode === 'm';
      c.innerHTML = '<h3>סיום הסבב</h3><div class="qz-stars" role="img" aria-label="' + stars + ' כוכבים מתוך 3">' + st + '</div>' +
        '<div class="lm-stats"><div class="lm-stat"><b>' + LG.nf(r.right) + '</b><span>נכונות מתוך ' + LG.nf(total) + ' (' + pct + '%)</span></div>' +
        '<div class="lm-stat"><b>' + LG.nf(r.pts) + '</b><span>נקודות הסבב</span></div>' +
        '<div class="lm-stat"><b>' + LG.nf(r.best) + '</b><span>רצף מרבי</span></div>' +
        '<div class="lm-stat"><b>' + LG.nf(sc.total) + '</b><span>סך הכול</span></div></div>' +
        '<p>התואר הכללי: <b>' + E(tl.name) + '</b>' + (tl.next ? ' · עוד ' + LG.nf(tl.need) + ' נקודות ל' + E(tl.next) : '') + '</p>' +
        (r.missed.length ? '<h4 style="margin:16px 0 6px">השאלות שטעית בהן</h4><div class="qz-missed">' + r.missed.map(function (m) {
          var q = m.q, href = UI.readHref(q.s, q.sd);
          return '<div class="qz-miss"><div class="qz-mq">' + E(q.q) + '</div><div class="qz-ma">התשובה: <b>' + E(q.o[0]) + '</b></div>' +
            (q.x ? '<div class="qz-exp small">' + E(q.x) + '</div>' : '') +
            (href ? '<a href="' + href + '" target="_blank" rel="noopener">למקום בגמרא: ' + E(LG.nameOf(q.s)) + ' ' + E(q.d) + '</a>' : '') + '</div>';
        }).join('') + '</div>' : '<p class="lm-note">לא טעית באף שאלה בסבב הזה.</p>') +
        '<div class="lm-row" style="margin-top:16px"><button class="lm-btn pri" id="lm-again" type="button">סבב נוסף</button>' +
        (harder ? '<button class="lm-btn" id="qz-harder" type="button">רמה קשה יותר</button>' : '') +
        '<button class="lm-btn ghost" id="lm-qhome" type="button">למסך הראשי</button></div>';
      host.innerHTML = ''; host.appendChild(c);
      $('#lm-again', c).onclick = function () { start(mode, slug, perek, lvl); };
      if (harder) $('#qz-harder', c).onclick = function () { var nl = lvl === 0 || lvl === 2 ? 3 : 2; sel.lvl = nl; start(mode, slug, perek, nl); };
      $('#lm-qhome', c).onclick = home;
      Q.sfx('fan');
      if (pct === 100 && total >= 3 && pers === 'bahur') confetti();
      $('#lm-again', c).focus({ preventScroll: true });
    }

    async function start(mode, slug, perek, lvl) {
      host.innerHTML = '<div class="lm-card">טוען שאלות...</div>';
      var q = await Q.queue(mode, slug, perek, lvl);
      if (!q || !q.length) { host.innerHTML = '<div class="lm-card"><p>' + (q ? 'אין כרגע שאלות לתרגול כאן.' : 'השאלות למסכת זו בהכנה.') + '</p><button class="lm-btn" id="lm-qb0" type="button">חזרה</button></div>'; $('#lm-qb0').onclick = home; return; }
      if (LG.sync && !offline()) LG.sync.heartbeat(slug || q[0].s);
      Q.run(host, q, {}, function (r) { endScreen(r, mode, slug, perek, lvl); });
    }

    function enter() {
      applyPersona();
      var md = qs.get('mode');
      if (md && md !== 'home' && slugs.length) {
        var y = LGDaf.forStr(LG.ymd(Date.now()));
        start(md, md === 'yomi' ? y.slug : cur, 0, 0);
      } else home();
    }
    drawSnd();
    if (!persona()) doors(enter); else enter();
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
