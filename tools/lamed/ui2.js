/* lamed - מסכים נוספים: הלימוד שלי, הדף היומי, הגדרות ופרטיות, סיום מסכת, תמונת הלומדים. */
(function () {
  'use strict';
  var LG = window.LAMED, E = LG.esc, UI = LG.ui, $ = UI.$, el = UI.el;

  var ONE = 86400000;
  function noonOf(ymd) { return LG.ymdToUTC(ymd) + 12 * 3600000; }

  /* ---------------------------------------------------------- הלימוד שלי */
  function daysSeries(n) {
    var S = LG.state(), today = LG.ymd(Date.now()), out = [];
    for (var i = n - 1; i >= 0; i--) {
      var d = LG.addDays(today, -i), o = S.days[d] || { ms: 0, done: 0 };
      out.push({ ymd: d, ms: o.ms, done: o.done });
    }
    return out;
  }
  function barChart(series, label) {
    var W = 640, H = 170, pad = 22, max = Math.max.apply(null, series.map(function (x) { return x.ms; }).concat([60000]));
    var n = series.length, bw = (W - 2 * pad) / n;
    var bars = series.map(function (x, i) {
      var h = Math.round((H - 2 * pad) * x.ms / max);
      var xx = W - pad - (i + 1) * bw;            /* ימין לשמאל: הישן ביותר מימין */
      var t = (n <= 14 || i % Math.ceil(n / 10) === 0) ? '<text x="' + (xx + bw / 2) + '" y="' + (H - 5) + '" text-anchor="middle">' + HD.ymdShort(x.ymd) + '</text>' : '';
      return '<rect class="bar" x="' + (xx + 2).toFixed(1) + '" y="' + (H - pad - h) + '" width="' + Math.max(2, bw - 4).toFixed(1) + '" height="' + h + '" rx="2"><title>' +
        E(HD.long(noonOf(x.ymd)) + ': ' + LG.dur(x.ms)) + '</title></rect>' + t;
    }).join('');
    var yl = [0, .5, 1].map(function (f) { return '<text x="' + (W - 2) + '" y="' + (H - pad - (H - 2 * pad) * f + 4) + '" text-anchor="end">' + (f ? LG.nf(Math.round(max * f / 60000)) + ' דק׳' : '0') + '</text>'; }).join('');
    return '<svg class="lm-chart" viewBox="0 0 ' + W + ' ' + H + '" role="img" aria-label="' + E(label) + '">' + bars + yl + '</svg>';
  }
  function heatYear() {
    var S = LG.state(), today = LG.ymd(Date.now());
    var wd0 = new Date(LG.ymdToUTC(today)).getUTCDay();
    /* מסיימים בשבת הנוכחית: 53 שבועות אחורה */
    var endSat = LG.addDays(today, 6 - wd0), weeks = 53, cells = [], labels = [];
    var max = 1;
    Object.keys(S.days).forEach(function (k) { max = Math.max(max, S.days[k].ms); });
    var html = '', lastMonth = '';
    for (var w = weeks - 1; w >= 0; w--) {
      for (var d = 0; d < 7; d++) {
        var day = LG.addDays(endSat, -(w * 7) + (d - 6));
        var o = S.days[day], f = o ? o.ms / max : 0;
        var cls = !o ? '' : f > .75 ? 'h4' : f > .45 ? 'h3' : f > .2 ? 'h2' : 'h1';
        if (day > today) cls = 'f';
        html += '<i class="' + cls + '" title="' + E(HD.long(noonOf(day)) + (o ? ': ' + LG.dur(o.ms) : '')) + '"' + (cls === 'f' ? ' style="visibility:hidden"' : '') + '></i>';
      }
    }
    /* שורת חודשים עבריים */
    var mlabels = '';
    for (var w2 = weeks - 1; w2 >= 0; w2--) {
      var sun = LG.addDays(endSat, -(w2 * 7) - 6);
      var mon = LG.hebDateShort(noonOf(sun)).split(' ').slice(1).join(' ');
      mlabels += '<span style="font-size:11px;color:var(--ink3);white-space:nowrap;overflow:visible">' + (mon !== lastMonth ? E(mon) : '') + '</span>';
      lastMonth = mon;
    }
    return '<div style="overflow-x:auto"><div style="min-width:640px"><div style="display:grid;grid-template-columns:repeat(' + weeks + ',1fr);gap:3px;direction:rtl;margin-bottom:3px">' + mlabels + '</div>' +
      '<div class="lm-heat" style="grid-template-columns:repeat(' + weeks + ',1fr)">' + html + '</div></div></div>';
  }
  function whenCard() {
    var S = LG.state(), byWd = [0, 0, 0, 0, 0, 0, 0], byH = []; for (var i = 0; i < 24; i++) byH.push(0);
    S.sessions.forEach(function (s) {
      var p = LG.parts(s.t0); byWd[p.wd] += s.ms; byH[p.h] += s.ms;
    });
    var total = byWd.reduce(function (a, b) { return a + b; }, 0);
    if (!total) return '<p class="lm-note">עוד אין מספיק לימוד כדי להראות מתי אתה לומד.</p>';
    var maxW = Math.max.apply(null, byWd), maxH = Math.max.apply(null, byH);
    var pw = byWd.indexOf(maxW);
    /* שעת השיא: חלון של שעה עם הכי הרבה זמן */
    var ph = byH.indexOf(maxH);
    function hh(x) { return (x < 10 ? '0' : '') + x + ':00'; }
    var dw = '<div class="lm-dist">' + byWd.map(function (v, i) { return '<div><b style="height:' + Math.round(100 * v / (maxW || 1)) + '%" title="' + E(LG.dur(v)) + '"></b>' + LG.WD[i].slice(0, 3) + '</div>'; }).join('') + '</div>';
    var dh = '<div class="lm-dist">' + byH.map(function (v, i) { return '<div><b style="height:' + Math.round(100 * v / (maxH || 1)) + '%" title="' + E(LG.dur(v)) + '"></b>' + (i % 3 === 0 ? i : '') + '</div>'; }).join('') + '</div>';
    return '<p>רוב לימודך בין ' + hh(ph) + ' ל-' + hh((ph + 1) % 24) + ', וביום ' + LG.WD[pw] + ' הכי הרבה.</p>' +
      '<div class="lm-grid2"><div><div class="lm-small">לפי ימי השבוע</div>' + dw + '</div><div><div class="lm-small">לפי שעות היום</div>' + dh + '</div></div>';
  }
  function milestones() {
    var S = LG.state(), out = [];
    var hours = S.totalMs / 3600000;
    [[1, 'שעת לימוד ראשונה'], [10, '10 שעות לימוד'], [50, '50 שעות לימוד'], [100, '100 שעות לימוד'], [250, '250 שעות לימוד'], [500, '500 שעות לימוד']].forEach(function (m) {
      if (hours >= m[0]) out.push(m[1]);
    });
    LG.masechtot().filter(function (m) { return m.built; }).forEach(function (m) {
      var st = LG.masechetStats(m.slug);
      if (!st.total) return;
      if (st.ratio >= 1) out.push('סיום מסכת ' + m.name);
      else if (st.ratio >= .5) out.push('חצי מסכת ' + m.name);
      var p0 = (m.perakim || [])[0], p1 = (m.perakim || [])[1];
      if (p0 && p1) {
        var k1 = LG.dafKey(p0[2]), k2 = LG.dafKey(p1[2]), all = true, any = false;
        LG.amudim(m.slug).forEach(function (a) { var k = LG.dafKey(a.daf); if (k >= k1 && k < k2) { any = true; var x = LG.amudInfo(m.slug, a.daf); if (x.st !== 'done' && x.st !== 'ext') all = false; } });
        if (any && all) out.push('פרק ראשון במסכת ' + m.name);
      }
    });
    return out;
  }
  UI.lamed = function (root) {
    var S = LG.state(), set = S.settings, wrap = el('main', 'lm-wrap');
    var types = set.types || [], now = Date.now();
    wrap.innerHTML = '<h1 class="lm-t">הלימוד שלי</h1><p class="lm-sub">הנתונים נשמרים במכשיר שלך בלבד, אלא אם ביקשת סנכרון.</p>';
    /* כרטיסי סיכום */
    var sumDafim = 0, sumAmudim = 0, reps = 0, active = [];
    LG.masechtot().forEach(function (m) {
      if (!m.built) return; var st = LG.masechetStats(m.slug);
      sumDafim += st.dafimDone; sumAmudim += st.learned;
      var A = S.amud[m.slug] || {}; Object.keys(A).forEach(function (d) { if (A[d].n > 1) reps += A[d].n - 1; });
      if (st.learned || st.ms) active.push(m);
    });
    var c1 = el('div', 'lm-card');
    c1.innerHTML = '<div class="lm-stats">' +
      '<div class="lm-stat"><b>' + E(LG.dur(S.totalMs)) + '</b><span>סך זמן לימוד</span></div>' +
      '<div class="lm-stat"><b>' + LG.nf(sumDafim) + '</b><span>דפים נלמדו</span></div>' +
      '<div class="lm-stat"><b>' + LG.nf(active.length) + '</b><span>מסכתות פעילות</span></div>' +
      '<div class="lm-stat"><b>' + LG.nf(reps) + '</b><span>חזרות</span></div>' +
      (set.streak === false ? '' : '<div class="lm-stat"><b>' + LG.nf(LG.streak()) + '</b><span>ימים ברצף</span></div>') +
      (LG.sugg ? '<div class="lm-stat"><b>' + LG.nf(LG.sugg.total) + '</b><span>הצעות תיקון</span></div>' : '') + '</div>';
    wrap.appendChild(c1);
    var rc = UI.resumeCard(); if (rc) wrap.appendChild(rc);
    var qsum = LG.quiz.score(), qc = el('div', 'lm-card lm-hero');
    qc.innerHTML = '<div class="lm-txt"><div class="lm-small">בחן את עצמך</div><div class="lm-big">' + LG.nf(qsum.total) + ' נקודות</div><div class="lm-small">' + (qsum.answered ? E(LG.quiz.TITLES_ALL[LG.quiz.level(qsum.total, LG.quiz.T_ALL)] || 'עוד בלי תואר') + ' · ' + LG.nf(LG.quiz.dueCount()) + ' חזרות להיום' : 'שאלות חזרה על מה שלמדת') + '</div></div><a class="lm-btn" href="quiz.html">בחן את עצמך</a>';
    wrap.appendChild(qc);
    LG.quiz.proposerCard().then(function (pc) { if (pc) wrap.insertBefore(pc, qc.nextSibling); });
    /* הודעה עדינה, פעם אחת: אם ההיסטוריה נמחקת (מטמון, החלפת מכשיר) אפשר לא לאבד אותה */
    var tipSeen = false; try { tipSeen = localStorage.getItem('lg-lamed-tip') === '1'; } catch (e) { }
    if (!tipSeen && !window.__lmDemo && S.sessions.length >= 3 && !(LG.sync && LG.sync.linked())) {
      var tip = el('div', 'lm-hint', 'כדי לא לאבד את התקדמותך אם הדפדפן יימחק את הנתונים, אפשר לשמור קוד לומד או לייצא גיבוי: <a href="settings.html#sync">לפרטיות וסנכרון</a> · <a href="javascript:void 0" id="lm-tipx">הבנתי</a>');
      tip.style.margin = '0 0 16px'; wrap.appendChild(tip);
      setTimeout(function () { var x = $('#lm-tipx'); if (x) x.onclick = function () { try { localStorage.setItem('lg-lamed-tip', '1'); } catch (e) { } tip.remove(); }; }, 0);
    }

    /* לוח חודש עברי: נקודה בכל יום לימוד, העוצמה לפי דקות. מתג שבוע/חודש קטן בתכלת */
    var c2 = el('div', 'lm-card');
    c2.innerHTML = '<div class="lm-row" style="justify-content:space-between;margin-bottom:10px"><h3 style="margin:0" id="lm-ct"></h3>' +
      '<div class="lm-seg" role="group" aria-label="תצוגה"><button type="button" id="lm-g7">שבוע</button><button type="button" id="lm-g30" class="on">חודש</button></div></div><div id="lm-gc"></div>';
    wrap.appendChild(c2);
    var c3 = el('div', 'lm-card'); c3.innerHTML = '<h3>השנה האחרונה</h3>' + heatYear() + '<div class="lm-legend"><span>פחות</span><span><em style="background:var(--c0)"></em></span><span><em style="background:var(--c1)"></em></span><span><em style="background:var(--c2)"></em></span><span><em style="background:var(--c3)"></em></span><span><em style="background:var(--c4)"></em></span><span>יותר</span></div>';
    wrap.appendChild(c3);
    var c4 = el('div', 'lm-card'); c4.innerHTML = '<h3>מתי אתה לומד</h3>' + whenCard(); wrap.appendChild(c4);

    /* תחזיות לכל מסכת פעילה */
    var mine = (set.my || []).map(function (s) { return LG.masechet(s); }).filter(Boolean);
    active.forEach(function (m) { if (!mine.some(function (x) { return x.slug === m.slug; })) mine.push(m); });
    if (mine.length) {
      var c5 = el('div', 'lm-card'); c5.innerHTML = '<h3>המסכתות שלי</h3>';
      mine.forEach(function (m) {
        var st = LG.masechetStats(m.slug), rem = LG.remainingMs(m.slug), daily = LG.dailyMs(), pace = LG.pace(m.slug);
        var fd = LG.finishDate(rem, daily, set.skipDays);
        var r = el('div', 'lm-hero'); r.style.margin = '10px 0 16px';
        r.innerHTML = UI.ring(st.ratio, null, 'sm') + '<div class="lm-txt"><a href="masechet.html?m=' + m.slug + '"><b class="lm-h" style="font-size:20px">' + E(m.name) + '</b></a>' +
          '<div class="lm-small">נלמדו ' + LG.nf(st.dafimDone) + ' מתוך ' + LG.nf(st.dafimTotal) + ' דפים' + (st.cycle ? ' · מחזור ' + E(LG.hebq(st.cycle + 1)) : '') + '</div>' +
          (rem > 0 ? '<div>' + (daily >= 60000 ? 'בקצב שלך נשארו כ-' + E(LG.dur(rem, true)) + (fd ? ', סיום בערך ב-' + E(LG.gDateShort(fd.ymd)) : '') : 'נשארו כ-' + E(LG.dur(rem, true)) + ' (הערכה ראשונית)') + '</div>' : '<div>המסכת נשלמה במחזור הנוכחי.</div>') + '</div>';
        c5.appendChild(r);
      });
      wrap.appendChild(c5);
    }
    var ms = milestones();
    var c6 = el('div', 'lm-card'); c6.innerHTML = '<h3>ציוני דרך</h3>' + (ms.length ? '<div class="lm-row">' + ms.map(function (x) { return '<span class="lm-tag ok" style="font-size:15px;padding:2px 12px">' + E(x) + '</span>'; }).join('') + '</div>' : '<p class="lm-note">ציוני הדרך יופיעו כאן עם הלימוד: שעה ראשונה, פרק, חצי מסכת, סיום.</p>');
    wrap.appendChild(c6);

    if (types.indexOf('scholar') > -1) wrap.appendChild(scholarCard());
    if (types.indexOf('regular') > -1 || (set.goals && Object.keys(set.goals).length)) wrap.appendChild(goalsCard());
    wrap.appendChild(suggCard());
    /* יומן ישיבות */
    var c7 = el('div', 'lm-card'); c7.innerHTML = '<h3>יומן ישיבות הלימוד</h3>';
    var ses = S.sessions.slice().sort(function (a, b) { return b.t0 - a.t0; }).slice(0, 40);
    if (!ses.length) c7.innerHTML += '<p class="lm-note">עוד אין ישיבות לימוד.</p>';
    else c7.innerHTML += '<ul class="lm-list">' + ses.map(function (s) {
      var p = LG.parts(s.t0), pages = {}; Object.keys(s.per).forEach(function (k) { var sp = k.split('|'); (pages[sp[0]] = pages[sp[0]] || []).push(sp[1]); });
      var txt = Object.keys(pages).map(function (sl) { return LG.nameOf(sl) + ' ' + pages[sl].slice(0, 6).join(', ') + (pages[sl].length > 6 ? '…' : ''); }).join(' · ');
      return '<li><span class="lm-grow"><b>' + E(HD.long(s.t0)) + '</b> · ' + (p.h < 10 ? '0' : '') + p.h + ':' + (p.mi < 10 ? '0' : '') + p.mi + '</span><span>' + E(LG.dur(s.ms)) + '</span><span class="lm-small">' + E(txt) + '</span></li>';
    }).join('') + '</ul>';
    wrap.appendChild(c7);
    root.appendChild(wrap);
    function monthCal() {
      var today = LG.ymd(Date.now()), T0 = noonOf(today);
      function hkey(x) { var pp = HD.parts(x); return pp.y + '|' + pp.m; }
      var hk = hkey(T0), fT = T0, lT = T0;
      while (hkey(fT - ONE) === hk) fT -= ONE;
      while (hkey(lT + ONE) === hk) lT += ONE;
      var wd = new Date(fT).getUTCDay(), dim = Math.round((lT - fT) / ONE) + 1, max = 60000;
      Object.keys(S.days).forEach(function (k) { max = Math.max(max, S.days[k].ms); });
      var h = '<div class="lm-mcal">' + LG.WD.map(function (w) { return '<div class="wd">' + w.slice(0, 3) + '</div>'; }).join('');
      for (var i = 0; i < wd; i++) h += '<div></div>';
      for (var d = 0; d < dim; d++) {
        var tt = fT + d * ONE, ds = LG.ymd(tt), o = S.days[ds], f = o ? o.ms / max : 0;
        var cls = !o || !o.ms ? '' : f > .66 ? 'h3' : f > .33 ? 'h2' : 'h1';
        h += '<div class="d' + (ds === today ? ' today' : '') + (ds > today ? ' f' : '') + '" title="' + E(HD.long(tt) + (o && o.ms ? ': ' + LG.dur(o.ms) : '')) + '"><span>' + E(HD.q(HD.parts(tt).d)) + '</span><i class="' + cls + '"></i></div>';
      }
      var hp = HD.parts(fT);
      $('#lm-ct').textContent = hp.m + ' ' + HD.q(hp.y % 1000);
      return h + '</div>';
    }
    function drawG(n) {
      $('#lm-gc').innerHTML = n === 7 ? barChart(daysSeries(7), 'שבוע אחרון') : monthCal();
      if (n === 7) $('#lm-ct').textContent = 'דקות לימוד ביום, בשבוע האחרון';
      $('#lm-g7').classList.toggle('on', n === 7); $('#lm-g30').classList.toggle('on', n !== 7);
    }
    $('#lm-g7').onclick = function () { drawG(7); }; $('#lm-g30').onclick = function () { drawG(30); }; drawG(30);
  };

  function suggCard() {
    var c = el('div', 'lm-card'), s = LG.sugg;
    c.innerHTML = '<h3>הצעות התיקון שלי</h3>';
    if (!s || !s.total) { c.innerHTML += '<p class="lm-note">עוד לא שלחת הצעות תיקון. סמן טקסט בדף הלימוד ובחר "הצע תיקון".</p>'; return c; }
    var ok = s.approved + s.refined;
    c.innerHTML += '<div class="lm-stats"><div class="lm-stat"><b>' + LG.nf(s.total) + '</b><span>נשלחו</span></div><div class="lm-stat"><b>' + LG.nf(s.pending) + '</b><span>ממתינות</span></div>' +
      '<div class="lm-stat"><b>' + LG.nf(s.approved) + '</b><span>אושרו</span></div><div class="lm-stat"><b>' + LG.nf(s.refined) + '</b><span>אושרו בשינוי</span></div><div class="lm-stat"><b>' + LG.nf(s.rejected) + '</b><span>נדחו</span></div>' +
      '<div class="lm-stat"><b>' + LG.pct(s.total ? ok / s.total : 0) + '</b><span>אחוז שאושר</span></div></div>' +
      '<p class="lm-note" style="margin:10px 0 0">את ההצעות עצמן אפשר לפתוח בדף הלימוד, בכפתור "ההצעות שלי".</p>';
    return c;
  }
  function goalsCard() {
    var S = LG.state(), set = S.settings, c = el('div', 'lm-card');
    c.innerHTML = '<h3>יעדים</h3>';
    var any = false;
    Object.keys(set.goals || {}).forEach(function (slug) {
      var g = set.goals[slug]; if (!g) return; any = true;
      var st = LG.masechetStats(slug), left = st.total - st.learned;
      var line = '<li><span class="lm-grow"><b>' + E(LG.nameOf(slug)) + '</b></span><span>';
      if (g.end) { var d = LG.diffDays(LG.ymd(Date.now()), g.end); line += d > 0 ? 'עד ' + LG.gDateShort(g.end) + ': כ-' + (Math.round(left / 2 / d * 10) / 10) + ' דפים ביום' : 'יעד התאריך עבר'; }
      if (g.minutes) line += ' · ' + g.minutes + ' דקות ביום';
      if (g.perWeek) line += ' · ' + g.perWeek + ' דפים בשבוע';
      c.innerHTML += '<ul class="lm-list">' + line + '</span></li></ul>';
    });
    if (!any) c.innerHTML += '<p class="lm-note">אפשר להגדיר יעד למסכת בהגדרות: תאריך סיום, זמן יומי או דפים בשבוע.</p>';
    c.innerHTML += '<p style="margin:6px 0 0"><a href="settings.html#goals">להגדרת יעדים</a></p>';
    return c;
  }
  function scholarCard() {
    var S = LG.state(), c = el('div', 'lm-card'), set = S.settings;
    c.innerHTML = '<h3>חזרות</h3><p class="lm-note">"אינו דומה שונה פרקו מאה פעמים לשונה פרקו מאה ואחד" (חגיגה ט:)</p>';
    var tgt = (set.target && set.target[0]) || 10;
    var tg = '<div class="lm-row" style="margin:8px 0">יעד חזרות לכל עמוד: ' + [4, 10, 40, 101].map(function (n) { return '<button type="button" class="lm-btn small ' + (tgt === n ? '' : 'ghost') + '" data-tg="' + n + '">' + n + '</button>'; }).join('') + '</div>';
    c.innerHTML += tg;
    /* מסכת עם הכי הרבה חזרות */
    var rows = [], due = [], speeds = [];
    LG.masechtot().forEach(function (m) {
      if (!m.built) return; var A = S.amud[m.slug] || {};
      var best = 0, tot = 0, reached = 0, count = 0;
      Object.keys(A).forEach(function (d) {
        var a = A[d]; if (!a.n) return; best = Math.max(best, a.n); tot += a.n; count++; if (a.n >= tgt) reached++;
        var iv = [7, 21, 60, 150, 365][Math.min(a.n - 1, 4)], dueDay = LG.addDays(a.dates[a.dates.length - 1], iv), today = LG.ymd(Date.now());
        if (dueDay <= today) due.push({ s: m.slug, d: d, over: LG.diffDays(dueDay, today), n: a.n });
        if (a.ms.length > 1 && a.ms[0] > 60000 && a.ms[a.ms.length - 1] > 30000) speeds.push({ first: a.ms[0], last: a.ms[a.ms.length - 1] });
      });
      if (count) rows.push({ m: m, best: best, count: count, reached: reached });
    });
    rows.sort(function (a, b) { return b.best - a.best; });
    c.innerHTML += rows.length ? '<ul class="lm-list">' + rows.slice(0, 6).map(function (r) {
      return '<li><span class="lm-grow"><a href="masechet.html?m=' + r.m.slug + '"><b>' + E(r.m.name) + '</b></a></span><span>עד ' + LG.nf(r.best) + ' חזרות · ' + LG.nf(r.reached) + ' עמודים הגיעו ליעד</span></li>';
    }).join('') + '</ul>' : '<p class="lm-note">עוד אין חזרות.</p>';
    due.sort(function (a, b) { return b.over - a.over; });
    c.innerHTML += '<h3 style="margin-top:14px">דפים שהגיע זמנם לחזרה</h3>' + (due.length ? '<ul class="lm-list">' + due.slice(0, 8).map(function (d) {
      return '<li><span class="lm-grow">' + E(LG.nameOf(d.s)) + ' ' + E(d.d) + '</span><span class="lm-small">נלמד ' + d.n + ' פעמים · חלף הזמן לפני ' + LG.days(d.over) + '</span><a class="lm-btn small ghost" href="' + (UI.readHref(d.s, d.d) || '#') + '">לחזור</a></li>';
    }).join('') + '</ul>' : '<p class="lm-note">אין כרגע דפים שממתינים לחזרה.</p>');
    if (speeds.length) {
      var f = speeds.reduce(function (a, b) { return a + b.first; }, 0) / speeds.length, l = speeds.reduce(function (a, b) { return a + b.last; }, 0) / speeds.length;
      c.innerHTML += '<p style="margin:10px 0 0">זמן ממוצע לעמוד: בחזרה הראשונה ' + E(LG.dur(f)) + ', באחרונה ' + E(LG.dur(l)) + '.</p>';
    }
    c.addEventListener('click', function (e) { var b = e.target.closest('[data-tg]'); if (b) { LG.setSetting('target', { 0: +b.dataset.tg }); location.reload(); } });
    return c;
  }

  /* ---------------------------------------------------------- הדף היומי */
  function dayStatus(info, ymd) {
    /* דף יומי = שני עמודי הדף; נלמד אם שניהם נלמדו (באתר או בספר) */
    var A = LG.state().amud[info.slug] || {}, a1 = LG.dafLabel(info.n, 0), a2 = LG.dafLabel(info.n, 1);
    var i1 = LG.amudInfo(info.slug, a1), i2 = LG.amudInfo(info.slug, a2);
    var ok = function (i) { return i.st === 'done' || i.st === 'ext'; };
    return ok(i1) && ok(i2) ? 'done' : (ok(i1) || ok(i2) || i1.st === 'prog' || i2.st === 'prog' ? 'part' : 'none');
  }
  UI.yomi = function (root) {
    var S = LG.state(), set = S.settings, now = Date.now(), today = LG.ymd(now), wrap = el('main', 'lm-wrap');
    var y = LGDaf.forStr(today), m = LG.masechet(y.slug), built = m && m.built;
    wrap.innerHTML = '<h1 class="lm-t">הדף היומי</h1>';
    var c1 = el('div', 'lm-card lm-hero');
    c1.innerHTML = '<div class="lm-txt"><div class="lm-small">' + E(HD.long(now)) + '</div><div class="lm-big">' + E(y.name) + ' ' + E(LG.hebq(y.n)) + '</div>' +
      '<div class="lm-small">מחזור ' + E(LG.hebq(y.cycle)) + (built ? '' : ' · מסכת זו עדיין בהכנה באתר') + '</div></div>' +
      (built ? '<div class="lm-row"><a class="lm-btn" href="' + UI.readHref(y.slug, LG.dafLabel(y.n, 0)) + '">ללמוד את הדף של היום</a><a class="lm-btn" href="quiz.html?mode=yomi">בחן את עצמך על הדף</a><a class="lm-btn ghost" href="' + UI.readHref(y.slug, LG.dafLabel(y.n, 1)) + '">עמוד ב</a></div>' : '') +
      '<div class="lm-row"><button class="lm-btn ghost" id="lm-yb" type="button">למדתי בספר</button></div>';
    wrap.appendChild(c1);

    /* התקדמות במחזור */
    var start = LGDaf.START, cycLen = LGDaf.cycle;
    var startDate = new Date(start + (y.cycle - 14) * cycLen * ONE).toISOString().slice(0, 10);
    var doneN = 0, idx = 0, thisIdx = y.index;
    var missing = [];
    for (var k = 0; k <= thisIdx; k++) {
      var d = LG.addDays(startDate, k), inf = LGDaf.forStr(d);
      var st = dayStatus(inf, d);
      if (st === 'done') doneN++; else if (k < thisIdx && d >= LG.addDays(today, -30)) missing.push({ ymd: d, inf: inf });
    }
    var c2 = el('div', 'lm-card');
    c2.innerHTML = '<h3>מחזור ' + E(LG.hebq(y.cycle)) + '</h3>' + UI.bar(doneN, 0, cycLen) + '<p>נלמדו ' + LG.nf(doneN) + ' מתוך ' + LG.nf(cycLen) + ' דפים. היום הוא היום ה-' + LG.nf(thisIdx + 1) + ' במחזור.</p>';
    wrap.appendChild(c2);

    /* לוח חודשי - חודש עברי (6.10.2026). hd = יום כלשהו בתוך החודש; הוא מזהה פנימי
       בלבד ואינו מוצג. ימי החודש מסומנים באותיות. */
    var anchor = new URLSearchParams(location.search).get('hd') || today;
    var T0 = noonOf(anchor);
    function hkey(t) { var pp = HD.parts(t); return pp.y + '|' + pp.m; }
    var hk = hkey(T0), fT = T0, lT = T0;
    while (hkey(fT - ONE) === hk) fT -= ONE;
    while (hkey(lT + ONE) === hk) lT += ONE;
    var wd = new Date(fT).getUTCDay();
    var dim = Math.round((lT - fT) / ONE) + 1;
    var cal = '<div style="display:grid;grid-template-columns:repeat(7,1fr);gap:4px;direction:rtl">' + LG.WD.map(function (w) { return '<div class="lm-small" style="text-align:center">' + w.slice(0, 3) + '</div>'; }).join('');
    for (var i = 0; i < wd; i++) cal += '<div></div>';
    for (var dday = 0; dday < dim; dday++) {
      var tt = fT + dday * ONE, ds = LG.ymd(tt), inf = LGDaf.forStr(ds), st2 = ds > today ? 'future' : dayStatus(inf, ds);
      var bg = st2 === 'done' ? 'var(--c2)' : st2 === 'part' ? 'var(--prog)' : st2 === 'future' ? 'transparent' : 'var(--card2)';
      var fg = st2 === 'done' ? '#fff' : 'var(--ink)';
      cal += '<button type="button" class="lm-cal" data-d="' + ds + '" style="background:' + bg + ';color:' + fg + ';border:1px solid ' + (ds === today ? 'var(--red)' : 'var(--line)') + ';border-radius:6px;padding:4px 2px;font:inherit;font-size:13px;cursor:pointer;line-height:1.25">' +
        '<b style="font-size:14px">' + E(HD.q(HD.parts(tt).d)) + '</b><br><span style="font-size:11px">' + E(inf.name.slice(0, 7)) + ' ' + E(LG.hebq(inf.n)) + '</span></button>';
    }
    cal += '</div>';
    var prev = LG.ymd(fT - ONE), next = LG.ymd(lT + ONE), hpm = HD.parts(fT);
    var c3 = el('div', 'lm-card');
    c3.innerHTML = '<div class="lm-row" style="justify-content:space-between"><h3 style="margin:0">' + E(hpm.m + ' ' + HD.q(hpm.y % 1000)) + '</h3><span><a href="?hd=' + prev + '">‹ הקודם</a> · <a href="?hd=' + next + '">הבא ›</a></span></div>' + cal +
      '<div class="lm-legend"><span><em style="background:var(--c2)"></em>נלמד</span><span><em style="background:var(--prog)"></em>חלקי</span><span><em style="background:var(--card2)"></em>חסר</span></div>';
    wrap.appendChild(c3);

    /* השלמת פערים */
    var c4 = el('div', 'lm-card');
    if (missing.length) {
      var names = missing.slice(-6).map(function (x) { return x.inf.name + ' ' + LG.hebq(x.inf.n); }).join(', ');
      c4.innerHTML = '<h3>השלמת פערים</h3><p>חסרים לך ' + LG.nf(missing.length) + ' ' + (missing.length === 1 ? 'דף' : 'דפים') + ' מ-30 הימים האחרונים: ' + E(names) + (missing.length > 6 ? '…' : '') + '.</p>' +
        '<p class="lm-note">הצעה רכה: לפרוס אותם על ' + (missing.length > 4 ? 'שבת וערב שבת, וקצת בכל יום' : 'הימים הקרובים') + ' - כדף אחד נוסף ביום, בלי למהר.</p>' +
        '<ul class="lm-list">' + missing.slice(-8).map(function (x) {
          var mm = LG.masechet(x.inf.slug), has = mm && mm.built;
          return '<li><span class="lm-grow">' + E(HD.ymdShort(x.ymd)) + ' · ' + E(x.inf.name) + ' ' + E(LG.hebq(x.inf.n)) + '</span>' + (has ? '<a class="lm-btn small ghost" href="' + UI.readHref(x.inf.slug, LG.dafLabel(x.inf.n, 0)) + '">ללמוד</a>' : '') +
            '<button class="lm-btn small ghost" type="button" data-bk="' + x.ymd + '">למדתי בספר</button></li>';
        }).join('') + '</ul>';
    } else c4.innerHTML = '<h3>השלמת פערים</h3><p>אין פערים ב-30 הימים האחרונים.</p>';
    wrap.appendChild(c4);

    /* תזכורת */
    var c5 = el('div', 'lm-card');
    c5.innerHTML = '<h3>תזכורת יומית</h3><p class="lm-note">כבויה כברירת מחדל. אפשר לקבל קובץ יומן עם הדף של כל יום בשנה, או התראת דפדפן בשעה שתבחר.</p>' +
      '<div class="lm-row"><button class="lm-btn ghost" id="lm-ics" type="button">הורדת קובץ יומן לשנה</button><button class="lm-btn ghost" id="lm-ntf" type="button">התראת דפדפן</button></div>';
    wrap.appendChild(c5);
    root.appendChild(wrap);
    function markBook(ds) {
      var inf = LGDaf.forStr(ds);
      LG.put({ k: 'ex', s: inf.slug, from: LG.dafLabel(inf.n, 0), to: LG.dafLabel(inf.n, 1), t: LG.ymdToUTC(ds) + 12 * 3600000 });
    }
    $('#lm-yb').onclick = function () { markBook(today); location.reload(); };
    wrap.addEventListener('click', function (e) {
      var b = e.target.closest('[data-bk]'); if (b) { markBook(b.dataset.bk); location.reload(); }
      var c = e.target.closest('.lm-cal'); if (c) {
        var ds = c.dataset.d, inf = LGDaf.forStr(ds), mm = LG.masechet(inf.slug);
        var mod = UI.modal('<h3>' + E(HD.long(LG.ymdToUTC(ds) + 43200000)) + '</h3><p><b>' + E(inf.name) + ' ' + E(LG.hebq(inf.n)) + '</b></p><div class="lm-row">' +
          (mm && mm.built ? '<a class="lm-btn" href="' + UI.readHref(inf.slug, LG.dafLabel(inf.n, 0)) + '">ללמוד</a>' : '<span class="lm-note">מסכת זו עדיין בהכנה באתר.</span>') + '<button class="lm-btn ghost" id="lm-cb" type="button">למדתי בספר</button></div>');
        $('#lm-cb', mod).onclick = function () { markBook(ds); mod.close(); location.reload(); };
      }
    });
    $('#lm-ics').onclick = function () {
      var lines = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//leokmei-girsa//daf-yomi//HE', 'CALSCALE:GREGORIAN'];
      var t = set.remind && set.remind.time || '06:00', hh = t.slice(0, 2), mi = t.slice(3, 5);
      for (var i = 0; i < 366; i++) {
        var ds = LG.addDays(today, i), inf = LGDaf.forStr(ds), cs = ds.replace(/-/g, '');
        lines.push('BEGIN:VEVENT', 'UID:dy-' + cs + '@leokmei', 'DTSTAMP:' + today.replace(/-/g, '') + 'T000000Z', 'DTSTART;TZID=' + LG.tz() + ':' + cs + 'T' + hh + mi + '00', 'DTEND;TZID=' + LG.tz() + ':' + cs + 'T' + hh + mi + '00',
          'SUMMARY:הדף היומי: ' + inf.name + ' ' + inf.daf, 'END:VEVENT');
      }
      lines.push('END:VCALENDAR');
      var blob = new Blob([lines.join('\r\n')], { type: 'text/calendar;charset=utf-8' }), a = document.createElement('a');
      a.href = URL.createObjectURL(blob); a.download = 'daf-yomi.ics'; document.body.appendChild(a); a.click(); a.remove();
    };
    $('#lm-ntf').onclick = function () {
      if (!('Notification' in window)) { UI.toast('הדפדפן אינו תומך בהתראות'); return; }
      Notification.requestPermission().then(function (p) { if (p === 'granted') { LG.setSetting('remind', Object.assign({}, set.remind, { on: true, browser: true })); UI.toast('ההתראה הופעלה. היא תופיע בפתיחת האתר בשעה שנבחרה'); } else UI.toast('ההתראה לא אושרה'); });
    };
  };

  /* ---------------------------------------------------------- הגדרות ופרטיות */
  UI.settings = function (root) {
    var S = LG.state(), set = S.settings, wrap = el('main', 'lm-wrap narrow');
    wrap.innerHTML = '<h1 class="lm-t">הגדרות</h1>';
    var types = el('div', 'lm-card'); types.innerHTML = '<h3>איך אני לומד</h3><div class="lm-cards4" id="lm-ty"></div>';
    wrap.appendChild(types);
    var TY = [['visitor', 'מבקר', 'נכנס מדי פעם'], ['regular', 'לומד קבוע', 'מסכת אישית ויעד'], ['yomi', 'לומד הדף היומי', 'הדף של היום והשלמת פערים'], ['scholar', 'חוזר על תלמודו', 'חזרות ויעדי חזרה']];
    var tg = $('#lm-ty', types);
    TY.forEach(function (t) {
      var b = el('button', 'lm-pick' + ((set.types || []).indexOf(t[0]) > -1 ? ' on' : ''), '<b>' + t[1] + '</b><span>' + t[2] + '</span>'); b.type = 'button';
      b.onclick = function () { var cur = (LG.settings().types || []).slice(), i = cur.indexOf(t[0]); if (i > -1) cur.splice(i, 1); else cur.push(t[0]); if (!cur.length) cur = ['visitor']; LG.setSetting('types', cur); b.classList.toggle('on'); };
      tg.appendChild(b);
    });
    /* יעדים */
    var goals = el('div', 'lm-card'); goals.id = 'goals';
    goals.innerHTML = '<h3>המסכתות שלי ויעדים</h3><div class="lm-field"><label for="lm-gm">מסכת</label><select id="lm-gm"></select></div>' +
      '<div class="lm-field"><label for="lm-ge">תאריך סיום רצוי</label><select id="lm-ge"></select></div>' +
      '<div class="lm-field"><label for="lm-gt">זמן יומי (דקות)</label><input id="lm-gt" type="number" min="0" max="600" step="5"></div>' +
      '<div class="lm-field"><label for="lm-gp">דפים בשבוע</label><input id="lm-gp" type="number" min="0" max="100"></div>' +
      '<div class="lm-row"><button class="lm-btn" id="lm-gs" type="button">שמור יעד</button><button class="lm-btn ghost" id="lm-gd" type="button">הסר יעד</button></div>';
    wrap.appendChild(goals);
    var gm = $('#lm-gm', goals);
    LG.masechtot().filter(function (m) { return m.built; }).forEach(function (m) { gm.appendChild(el('option', '', E(m.name))); gm.lastChild.value = m.slug; });
    /* תאריך היעד: רשימה של הימים הבאים בתאריך עברי (ערך פנימי: yyyy-mm-dd) */
    function goalDates(cur) {
      var sel = $('#lm-ge', goals), t0 = LG.ymd(Date.now()), h = '<option value="">ללא יעד</option>', seen = {};
      for (var k = 1; k <= 400; k++) { var d = LG.addDays(t0, k); seen[d] = 1; h += '<option value="' + d + '">' + E(HD.ymdLong(d)) + '</option>'; }
      if (cur && !seen[cur]) h += '<option value="' + E(cur) + '">' + E(HD.ymdLong(cur)) + '</option>';
      sel.innerHTML = h;
    }
    function fillGoal() { var g = (LG.settings().goals || {})[gm.value] || {}; goalDates(g.end); $('#lm-ge', goals).value = g.end || ''; $('#lm-gt', goals).value = g.minutes || ''; $('#lm-gp', goals).value = g.perWeek || ''; }
    gm.onchange = fillGoal; fillGoal();
    $('#lm-gs', goals).onclick = function () {
      var all = Object.assign({}, LG.settings().goals || {}), my = (LG.settings().my || []).slice();
      all[gm.value] = { end: $('#lm-ge', goals).value || '', minutes: +$('#lm-gt', goals).value || 0, perWeek: +$('#lm-gp', goals).value || 0 };
      if (my.indexOf(gm.value) < 0) my.push(gm.value);
      LG.setSetting('goals', all); LG.setSetting('my', my); UI.toast('היעד נשמר');
    };
    $('#lm-gd', goals).onclick = function () { var all = Object.assign({}, LG.settings().goals || {}); delete all[gm.value]; LG.setSetting('goals', all); fillGoal(); UI.toast('היעד הוסר'); };
    /* תצוגה */
    var disp = el('div', 'lm-card');
    disp.innerHTML = '<h3>תצוגה</h3>' +
      chk('clock', 'שעון קטן בסרגל הלימוד', set.clock !== false) + chk('bar', 'סמן התקדמות דק בראש הדף', set.bar !== false) + chk('streak', 'רצף ימי לימוד', set.streak !== false) +
      '<div class="lm-field"><label for="lm-dk">מצב תצוגה</label><select id="lm-dk"><option value="light">בהיר</option><option value="dark">כהה</option><option value="auto">לפי המכשיר</option></select></div>' +
      '<div class="lm-field"><label for="lm-tz">אזור זמן</label><select id="lm-tz"><option value="Asia/Jerusalem">שעון ישראל</option><option value="Europe/London">לונדון</option><option value="America/New_York">ניו יורק</option><option value="America/Los_Angeles">לוס אנג׳לס</option><option value="Europe/Paris">פריז</option></select></div>' +
      '<div class="lm-field"><label for="lm-rt">שעת תזכורת</label><input id="lm-rt" type="time" value="' + E((set.remind && set.remind.time) || '06:00') + '"></div>';
    wrap.appendChild(disp);
    function chk(key, label, on) { return '<label class="lm-check"><input type="checkbox" data-cf="' + key + '"' + (on ? ' checked' : '') + '><span>' + label + '</span></label>'; }
    $('#lm-dk', disp).value = set.dark || 'light'; $('#lm-tz', disp).value = set.tz || 'Asia/Jerusalem';
    disp.addEventListener('change', function (e) {
      var t = e.target;
      if (t.dataset.cf) { LG.setSetting(t.dataset.cf, t.checked); }
      else if (t.id === 'lm-dk') { LG.setSetting('dark', t.value); UI.applyTheme(); }
      else if (t.id === 'lm-tz') { LG.setSetting('tz', t.value); LG.setTZ(t.value); }
      else if (t.id === 'lm-rt') { LG.setSetting('remind', Object.assign({}, LG.settings().remind, { time: t.value })); }
    });
    /* פרטיות וסנכרון */
    var priv = el('div', 'lm-card'); priv.id = 'sync';
    priv.innerHTML = '<h3>פרטיות וסנכרון</h3>' + chk('share', 'שיתוף נתונים אנונימיים ומצטברים בלבד עם מנהל האתר (בלי שם, בלי זהות)', set.share !== false) +
      '<p class="lm-note">הנתונים שלך נשמרים במכשיר שלך. ברירת המחדל היא בלי חשבון ובלי הרשמה. סנכרון בין מכשירים אפשרי בקוד לומד זמני:</p>' +
      '<div class="lm-row"><button class="lm-btn ghost" id="lm-code" type="button">הפקת קוד לומד</button><input id="lm-codein" type="text" placeholder="קוד מהמכשיר השני" style="max-width:200px" autocomplete="off"><button class="lm-btn ghost" id="lm-redeem" type="button">חיבור בקוד</button></div>' +
      '<div class="lm-note" id="lm-syncmsg" style="margin-top:8px"></div>' +
      '<hr style="border:0;border-top:1px solid var(--line);margin:16px 0"><div class="lm-row"><button class="lm-btn ghost" id="lm-exp" type="button">ייצוא לקובץ</button><button class="lm-btn ghost" id="lm-imp" type="button">ייבוא מקובץ</button><button class="lm-btn ghost" id="lm-wipe" type="button" style="color:var(--red);border-color:var(--red)">מחיקת כל הנתונים</button></div><input id="lm-file" type="file" accept=".json" style="display:none">';
    wrap.appendChild(priv);
    priv.addEventListener('change', function (e) { var t = e.target; if (t.dataset.cf) LG.setSetting(t.dataset.cf, t.checked); });
    root.appendChild(wrap);
    $('#lm-exp').onclick = function () {
      var blob = new Blob([LG.exportJSON()], { type: 'application/json' }), a = document.createElement('a');
      a.href = URL.createObjectURL(blob); a.download = 'lamed-' + LG.ymd(Date.now()) + '.json'; document.body.appendChild(a); a.click(); a.remove();
    };
    $('#lm-imp').onclick = function () { $('#lm-file').click(); };
    $('#lm-file').onchange = function (e) {
      var f = e.target.files[0]; if (!f) return;
      var r = new FileReader(); r.onload = function () { try { var n = LG.importJSON(r.result); UI.toast('נקלטו ' + LG.nf(n) + ' אירועים'); } catch (er) { UI.toast(er.message); } }; r.readAsText(f);
    };
    $('#lm-wipe').onclick = function () {
      var m = UI.modal('<h3>מחיקת כל הנתונים</h3><p>כל ההיסטוריה, ההגדרות והמקום האחרון יימחקו ממכשיר זה, ואי אפשר יהיה לשחזר אותם (אלא מקובץ גיבוי). להמשיך?</p><div class="lm-row"><button class="lm-btn" id="lm-w1" type="button" style="background:var(--red);color:#fff">מחק הכול</button><button class="lm-btn ghost" id="lm-w2" type="button">ביטול</button></div>');
      $('#lm-w2', m).onclick = function () { m.close(); };
      $('#lm-w1', m).onclick = async function () { await LG.wipeAll(); m.close(); UI.toast('הנתונים נמחקו'); setTimeout(function () { location.reload(); }, 600); };
    };
    $('#lm-code').onclick = async function () {
      var msg = $('#lm-syncmsg');
      try { var c = await LG.sync.makeCode(); msg.innerHTML = 'הקוד שלך: <b class="lm-num" style="font-size:24px;letter-spacing:.1em" dir="ltr">' + E(c) + '</b> (תקף עשר דקות). הקלד אותו במכשיר השני.'; }
      catch (er) { msg.textContent = 'לא ניתן להפיק קוד כרגע: ' + er.message; }
    };
    $('#lm-redeem').onclick = async function () {
      var msg = $('#lm-syncmsg'), c = $('#lm-codein').value.trim();
      if (!c) return;
      try { var n = await LG.sync.redeem(c); msg.textContent = 'המכשיר חובר. אוחדו ' + LG.nf(n) + ' אירועים.'; }
      catch (er) { msg.textContent = 'החיבור נכשל: ' + er.message; }
    };
  };

  /* ---------------------------------------------------------- סיום מסכת */
  var HADRAN = 'הדרן עלך מסכת %s והדרך עלן. דעתן עלך מסכת %s ודעתך עלן. לא נתנשי מינך מסכת %s ולא תתנשי מינן. לא בעלמא הדין ולא בעלמא דאתי.';
  UI.done = function (root) {
    var slug = new URLSearchParams(location.search).get('m') || 'berakhot', m = LG.masechet(slug), wrap = el('main', 'lm-wrap narrow');
    if (!m) { wrap.innerHTML = '<h1 class="lm-t">מסכת לא נמצאה</h1>'; root.appendChild(wrap); return; }
    var S = LG.state(), st = LG.masechetStats(slug), A = S.amud[slug] || {};
    var firstT = Infinity, lastT = 0;
    Object.keys(A).forEach(function (d) { (A[d].dates || []).forEach(function (x) { var t = LG.ymdToUTC(x); firstT = Math.min(firstT, t); lastT = Math.max(lastT, t); }); });
    var daysN = firstT < Infinity ? LG.diffDays(new Date(firstT).toISOString().slice(0, 10), new Date(lastT).toISOString().slice(0, 10)) + 1 : 0;
    var name = S.settings.name || '';
    wrap.innerHTML = '<div class="lm-card" style="text-align:center"><div class="lm-small">מסכת ' + E(m.name) + '</div><h1 class="lm-t" style="font-size:40px">הדרן עלך מסכת ' + E(m.name) + '</h1>' +
      '<p style="font-size:20px;line-height:1.9">' + E(HADRAN.replace(/%s/g, m.name)) + '</p><p class="lm-note">את שאר נוסח ההדרן ראו בסידור.</p></div>' +
      '<div class="lm-card"><h3>סיכום הלימוד</h3><div class="lm-stats"><div class="lm-stat"><b>' + E(LG.dur(st.ms)) + '</b><span>זמן לימוד</span></div><div class="lm-stat"><b>' + LG.nf(daysN) + '</b><span>ימים מתחילה ועד סיום</span></div>' +
      '<div class="lm-stat"><b>' + (firstT < Infinity ? E(HD.date(firstT + 43200000)) : '-') + '</b><span>התחלה</span></div><div class="lm-stat"><b>' + (lastT ? E(HD.date(lastT + 43200000)) : '-') + '</b><span>סיום</span></div></div></div>' +
      '<div class="lm-card"><h3>תעודת סיום</h3><div class="lm-field"><label for="lm-nm">שם (לא חובה)</label><input id="lm-nm" type="text" value="' + E(name) + '" autocomplete="off"></div><div class="lm-row"><button class="lm-btn" id="lm-cert" type="button">הדפסה או שמירה כ-PDF</button></div></div>' +
      '<div class="lm-card"><h3>ומה הלאה</h3><div class="lm-row"><a class="lm-btn" href="masechet.html?m=' + slug + '">מחזור חזרה</a><a class="lm-btn ghost" href="shas.html">המסכת הבאה</a></div></div>';
    root.appendChild(wrap);
    $('#lm-cert').onclick = function () {
      var nm = $('#lm-nm').value.trim(); LG.setSetting('name', nm);
      var w = window.open('', '_blank');
      if (!w) { UI.toast('החלון נחסם. אשר חלונות קופצים ונסה שוב'); return; }
      w.document.write('<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8"><title>תעודת סיום</title><style>@page{size:A4 landscape;margin:0}' +
        '@font-face{font-family:Vilna;src:url(' + location.origin + location.pathname.replace(/[^\/]*$/, '') + 'fonts/vilna-b.otf);font-weight:700}@font-face{font-family:Leukmey;src:url(' + location.origin + location.pathname.replace(/[^\/]*$/, '') + 'fonts/leukmey.otf)}' +
        'body{margin:0;font-family:Vilna,serif;color:#2b2620;background:#fbf8f1}.c{margin:14mm;border:3px double #7a5a14;height:calc(210mm - 28mm - 6px);display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:10mm;box-sizing:border-box}' +
        'h1{font-family:Leukmey,Vilna;font-size:46pt;margin:0 0 6mm}h2{font-size:34pt;margin:0 0 8mm}p{font-size:18pt;margin:3mm 0}</style></head><body><div class="c"><h1>לאוקמי גירסא</h1><h2>הדרן עלך מסכת ' + E(m.name) + '</h2>' +
        (nm ? '<p>סיים את המסכת: <b>' + E(nm) + '</b></p>' : '<p>תעודת סיום מסכת</p>') + '<p>' + E(LG.dur(st.ms)) + ' לימוד · מ-' + (firstT < Infinity ? E(HD.date(firstT + 43200000)) : '') + ' עד ' + (lastT ? E(HD.date(lastT + 43200000)) : '') + '</p>' +
        '<p style="font-size:14pt">' + E(HD.long(Date.now())) + '</p></div><script>setTimeout(function(){print()},400)<\/script></body></html>');
      w.document.close();
    };
  };

  /* ---------------------------------------------------------- תמונת הלומדים (מנהל) */
  UI.admin = async function (root) {
    var wrap = el('main', 'lm-wrap'); wrap.innerHTML = '<h1 class="lm-t">תמונת הלומדים</h1><p class="lm-sub">מצטבר ואנונימי בלבד. בלי שמות ובלי זהות.</p><div id="lm-ad">טוען...</div>';
    root.appendChild(wrap);
    var box = $('#lm-ad');
    var key = ''; try { key = localStorage.getItem('lg-adm') || ''; } catch (e) { }
    function login(msg) {
      box.innerHTML = '<div class="lm-card"><p>דף זה למנהל בלבד. הקלד את מילת המנהל (אותה מילה שמקלידים בעריכה באתר; המכשיר יזוהה ולא תצטרך להקליד שוב):</p>' + (msg ? '<p style="color:var(--red)">' + E(msg) + '</p>' : '') +
        '<div class="lm-row"><input id="lm-ak" type="password" autocomplete="off" style="max-width:300px"><button class="lm-btn" id="lm-akb" type="button">כניסה</button></div></div>';
      var go = async function () {
        var w = $('#lm-ak').value.trim(); if (!w) return;
        try {
          var r = await LG.sync.api('/auth', { method: 'POST', body: JSON.stringify({ word: w, label: 'מסך הלומדים · ' + HD.date(Date.now()) }) });
          try { localStorage.setItem('lg-adm', r.token); localStorage.setItem('lg-admin', '1'); } catch (e) { }
          location.reload();
        } catch (e) { login(e.message); }
      };
      $('#lm-akb').onclick = go; $('#lm-ak').onkeydown = function (e) { if (e.key === 'Enter') go(); };
    }
    if (!key) { login(''); return; }
    var data;
    try { data = await LG.sync.stats(key, window.__lmDemo); } catch (e) {
      if (/הרשאה/.test(e.message || '')) { try { localStorage.removeItem('lg-adm'); } catch (x) { } login('המפתח השמור אינו תקף במכשיר הזה. הקלד את מילת המנהל.'); return; }
      box.innerHTML = '<div class="lm-card"><p>לא ניתן לטעון כרגע: ' + E(e.message) + '</p></div>'; return; }
    /* עמודים שכבר נערכו בעריכה המתקדמת (data/edited-pages.json): כל השאר "טרם נערכו" */
    var edm = {};
    try { edm = await fetch('edited-pages.json').then(function (r) { return r.json(); }); } catch (e) { }
    function isEdited(s, d) {
      var rule = edm[s], m = LG.masechet(s);
      if (!rule || !m) return false;
      var p = (m.perakim || [])[rule.chapters];
      return LG.dafKey(d) < (p ? LG.dafKey(p[2]) : 1e9);
    }
    if (!window.__lmDemo) data.topPages.forEach(function (x) { x.unedited = !isEdited(x.s, x.d); });
    var t = data.totals, html = '<div class="lm-card"><div class="lm-stats">' +
      '<div class="lm-stat"><b>' + LG.nf(t.today) + '</b><span>לומדים פעילים היום</span></div><div class="lm-stat"><b>' + LG.nf(t.week) + '</b><span>בשבוע</span></div><div class="lm-stat"><b>' + LG.nf(t.month) + '</b><span>בחודש</span></div>' +
      '<div class="lm-stat"><b>' + LG.nf(t.finished) + '</b><span>סיימו מסכת</span></div></div></div>';
    function table(title, rows, cols) {
      return '<div class="lm-card"><h3>' + title + '</h3>' + (rows.length ? '<ul class="lm-list">' + rows.map(function (r) { return '<li><span class="lm-grow">' + E(r.l) + '</span><span>' + E(r.v) + '</span></li>'; }).join('') + '</ul>' : '<p class="lm-note">עוד אין נתונים.</p>') + '</div>';
    }
    html += table('מסכתות שנלמדות הכי הרבה', data.byMasechet.slice(0, 10).map(function (x) { return { l: LG.nameOf(x.s), v: LG.nf(x.reads) + ' קריאות · ' + LG.dur(x.ms) }; }));
    html += table('דפים נלמדים הכי הרבה', data.topPages.slice(0, 15).map(function (x) { return { l: LG.nameOf(x.s) + ' ' + x.d + (x.unedited ? ' · טרם נערך בעריכה המתקדמת' : ''), v: LG.nf(x.reads) + ' קריאות' }; }));
    html += table('איפה לומדים נוטשים (מתחילים ולא מסיימים)', data.abandon.slice(0, 12).map(function (x) { return { l: LG.nameOf(x.s) + ' ' + x.d, v: LG.nf(x.starts) + ' התחילו · ' + LG.pct(x.starts ? x.done / x.starts : 0) + ' סיימו' }; }));
    html += table('זמן ממוצע לעמוד (הארוכים ביותר: מועמדים להידוק)', data.slow.slice(0, 12).map(function (x) { return { l: LG.nameOf(x.s) + ' ' + x.d, v: LG.dur(x.avg) + ' (' + LG.nf(x.n) + ' קריאות)' }; }));
    html += table('עדיפויות עריכה: נלמדים הרבה וטרם נערכו', data.topPages.filter(function (x) { return x.unedited; }).slice(0, 12).map(function (x) { return { l: LG.nameOf(x.s) + ' ' + x.d, v: LG.nf(x.reads) + ' קריאות' }; }));
    box.innerHTML = html;
    if (!window.__lmDemo && LG.quiz && LG.quiz.adminDrafts) LG.quiz.adminDrafts(box, key);
  };
})();
