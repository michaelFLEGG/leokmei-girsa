/* lamed - מסכי המערכת: ראש הדף וניווט, בית, מפת הש"ס, דף מסכת.
   כל הטקסטים בעברית; מספרי עמודים באותיות; כמויות בספרות מופרדות בפסיק. */
(function () {
  'use strict';
  var LG = window.LAMED, E = LG.esc;
  var UI = LG.ui = {};

  function $(s, r) { return (r || document).querySelector(s); }
  function el(tag, cls, html) { var e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; }
  UI.$ = $; UI.el = el;

  /* ---------------------------------------------------------- ערכת נושא */
  UI.applyTheme = function () {
    var d = LG.settings().dark;
    var r = document.documentElement;
    if (d === 'light' || d === 'dark') r.setAttribute('data-theme', d); else r.removeAttribute('data-theme');
  };

  /* ---------------------------------------------------------- ראש הדף והניווט */
  var ICONS = {
    home: '<svg viewBox="0 0 24 24"><path d="M3 11l9-8 9 8M5 10v10h5v-6h4v6h5V10"/></svg>',
    map: '<svg viewBox="0 0 24 24"><path d="M4 5h16v14H4zM9 5v14M15 5v14"/></svg>',
    me: '<svg viewBox="0 0 24 24"><circle cx="12" cy="8" r="4"/><path d="M4 21c1-5 15-5 16 0"/></svg>',
    yomi: '<svg viewBox="0 0 24 24"><rect x="4" y="5" width="16" height="15" rx="2"/><path d="M4 10h16M9 3v4M15 3v4"/></svg>'
  };
  UI.header = function (page) {
    var now = Date.now();
    var top = el('header', 'lm-top');
    top.innerHTML = '<a class="lm-brand" href="index.html">לאוקמי גירסא</a>' +
      '<nav>' + [['home', 'index.html', 'בית'], ['shas', 'shas.html', 'מפת הש"ס'], ['lamed', 'lamed.html', 'הלימוד שלי'], ['yomi', 'yomi.html', 'הדף היומי'], ['settings', 'settings.html', 'הגדרות']]
        .map(function (a) { return '<a href="' + a[1] + '"' + (page === a[0] ? ' class="on"' : '') + '>' + a[2] + '</a>'; }).join('') + '</nav>' +
      '<span class="lm-date">' + E(LG.hebDate(now)) + ' · ' + E(LG.gDate(now)) + '</span>';
    document.body.insertBefore(top, document.body.firstChild);
    var nav = el('nav', 'lm-bnav');
    nav.setAttribute('aria-label', 'ניווט ראשי');
    nav.innerHTML = [['home', 'index.html', 'בית', ICONS.home], ['shas', 'shas.html', 'מפה', ICONS.map], ['lamed', 'lamed.html', 'הלימוד שלי', ICONS.me], ['yomi', 'yomi.html', 'דף יומי', ICONS.yomi]]
      .map(function (a) { return '<a href="' + a[1] + '"' + (page === a[0] ? ' class="on"' : '') + '>' + a[3] + '<span>' + a[2] + '</span></a>'; }).join('');
    document.body.appendChild(nav);
    /* נעלם בקריאה (גלילה למטה) וחוזר בגלילה למעלה */
    var lastY = scrollY;
    addEventListener('scroll', function () {
      var y = scrollY;
      if (y > lastY + 8 && y > 120) nav.classList.add('hide'); else if (y < lastY - 8) nav.classList.remove('hide');
      lastY = y;
    }, { passive: true });
  };

  /* ---------------------------------------------------------- רכיבים */
  UI.ring = function (ratio, label, cls, extRatio) {
    var R = 40, C = 2 * Math.PI * R, v = Math.max(0, Math.min(1, ratio || 0)), x = Math.max(0, Math.min(1 - v, extRatio || 0));
    return '<div class="lm-ring ' + (cls || '') + '" role="img" aria-label="התקדמות: ' + LG.pct(v) + '"><svg viewBox="0 0 100 100" aria-hidden="true"><circle class="bg" cx="50" cy="50" r="' + R + '" fill="none" stroke-width="10"/>' +
      '<circle class="fg" cx="50" cy="50" r="' + R + '" fill="none" stroke-width="10" stroke-linecap="round" stroke-dasharray="' + (C * v).toFixed(1) + ' ' + C.toFixed(1) + '"/>' +
      (x ? '<circle class="ext" cx="50" cy="50" r="' + R + '" fill="none" stroke-width="10" stroke-dasharray="' + (C * x).toFixed(1) + ' ' + C.toFixed(1) + '" stroke-dashoffset="' + (-C * v).toFixed(1) + '"/>' : '') +
      '</svg><span>' + (label != null ? label : LG.pct(v)) + '</span></div>';
  };
  UI.bar = function (done, ext, total) {
    if (!total) return '<div class="lm-bar"></div>';
    return '<div class="lm-bar"><i style="width:' + (100 * done / total).toFixed(1) + '%"></i><i class="ext" style="width:' + (100 * ext / total).toFixed(1) + '%"></i></div>';
  };
  UI.modal = function (html, onClose) {
    var m = el('div', 'lm-modal'), b = el('div', 'lm-box', html);
    m.appendChild(b); document.body.appendChild(m);
    function close() { m.remove(); if (onClose) onClose(); }
    m.addEventListener('click', function (e) { if (e.target === m) close(); });
    document.addEventListener('keydown', function esc(e) { if (e.key === 'Escape') { close(); document.removeEventListener('keydown', esc); } });
    m.close = close;
    return m;
  };
  UI.toast = function (t) {
    var b = el('div', 'lm-toast', E(t)); document.body.appendChild(b); setTimeout(function () { b.remove(); }, 2600);
  };
  /* קישור לעמוד במסכת, ואם היא טרם עלתה - הודעה */
  UI.readHref = function (slug, daf, pos) {
    var m = LG.masechet(slug);
    if (!m || !m.built) return null;
    if (pos) return slug + '.html#lm=' + encodeURIComponent(JSON.stringify({ s: slug, d: daf, pid: pos.pid, fp: pos.fp }));
    return slug + '.html#daf=' + encodeURIComponent(daf);
  };

  /* ---------------------------------------------------------- כרטיס "המשך" */
  UI.resumeCard = function () {
    var S = LG.state(), l = S.last.all;
    if (!l) return null;
    var m = LG.masechet(l.s);
    var today = LG.ymd(Date.now());
    var when = LG.relDay(LG.ymd(l.t), today);
    var href = UI.readHref(l.s, l.d, l);
    if (!href) return null;
    var c = el('div', 'lm-card lm-hero');
    c.id = 'lm-resume';
    var snip = l.fp ? '…' + E(l.fp.slice(0, 30)) : '';
    c.innerHTML = '<div class="lm-txt"><div class="lm-small">המשך מהמקום שעצרת</div>' +
      '<div class="lm-big">' + E(LG.nameOf(l.s)) + ' · עמוד ' + E(l.d) + '</div>' +
      '<div class="lm-small">' + (snip ? snip + ' · ' : '') + when + '</div></div>' +
      '<a class="lm-btn" href="' + href + '">המשך ללמוד</a>';
    return c;
  };

  /* ---------------------------------------------------------- סיום ראשוני: "איך תרצה ללמוד?" */
  var TYPES = [
    ['visitor', 'מבקר', 'נכנס מדי פעם. האתר יחזיר אותי למקום שעצרתי.'],
    ['regular', 'לומד קבוע', 'מסכת אישית עם יעד, התקדמות ותחזית סיום.'],
    ['yomi', 'לומד הדף היומי', 'הדף של היום, לוח חודשי והשלמת פערים.'],
    ['scholar', 'חוזר על תלמודו', 'מפת חזרות, יעדי חזרה ורשימת דפים לחזרה.']
  ];
  UI.onboard = function (after) {
    var sel = {};
    var m = UI.modal('<h3>איך תרצה ללמוד?</h3><p class="lm-sub">אפשר לבחור יותר מאחד, ולשנות בכל עת בהגדרות.</p>' +
      '<div class="lm-cards4" id="lm-ob">' + TYPES.map(function (t) {
        return '<button type="button" class="lm-pick" data-t="' + t[0] + '"><b>' + t[1] + '</b><span>' + t[2] + '</span></button>';
      }).join('') + '</div><div class="lm-row" style="margin-top:16px"><button class="lm-btn" id="lm-ob-ok" type="button">בחירה</button><button class="lm-btn ghost" id="lm-ob-skip" type="button">דלג</button></div>');
    m.querySelectorAll('.lm-pick').forEach(function (b) {
      b.onclick = function () { sel[b.dataset.t] = !sel[b.dataset.t]; b.classList.toggle('on', !!sel[b.dataset.t]); };
    });
    function fin(skip) {
      var types = skip ? ['visitor'] : Object.keys(sel).filter(function (k) { return sel[k]; });
      if (!types.length) types = ['visitor'];
      LG.setSetting('types', types);
      try { localStorage.setItem('lg-lamed-ob', '1'); } catch (e) { }
      m.close(); if (after) after();
    }
    $('#lm-ob-ok', m).onclick = function () { fin(false); };
    $('#lm-ob-skip', m).onclick = function () { fin(true); };
  };
  UI.maybeOnboard = function () {
    if (window.__lmDemo) return;
    var done = false; try { done = localStorage.getItem('lg-lamed-ob') === '1'; } catch (e) { }
    if (!done && !LG.settings().types.length) UI.onboard(function () { LG.onChange && 0; location.reload(); });
  };

  /* ---------------------------------------------------------- תמצית שבועית */
  UI.weekSummary = function () {
    var S = LG.state(), today = LG.ymd(Date.now()), ms = 0, pages = 0;
    for (var i = 0; i < 7; i++) { var d = S.days[LG.addDays(today, -i)]; if (d) { ms += d.ms; pages += d.done; } }
    return { ms: ms, pages: pages, streak: LG.streak() };
  };

  /* ---------------------------------------------------------- דף הבית */
  UI.home = function (root) {
    var S = LG.state(), set = S.settings, now = Date.now();
    var wrap = el('main', 'lm-wrap');
    var types = set.types || [];
    var hero = el('div', 'lm-card');
    hero.style.textAlign = 'center';
    hero.innerHTML = '<div class="lm-small">' + E(LG.hebDate(now)) + '</div>' +
      '<h1 class="lm-t" style="font-family:Leukmey,Vilna,serif;font-weight:900;font-size:46px;margin:6px 0">לאוקמי גירסא</h1>' +
      '<div class="lm-small" style="font-size:17px">"לעולם ליגרס איניש" (שבת סג.) · קיצור התלמוד הבבלי, שלד הסוגיה בלבד</div>';
    wrap.appendChild(hero);

    var rc = UI.resumeCard();
    if (rc) wrap.appendChild(rc);
    else {
      var first = el('div', 'lm-card lm-hero');
      var t = window.LGDaf && LGDaf.forStr(LG.ymd(now));
      var mm = t && LG.masechet(t.slug);
      first.innerHTML = '<div class="lm-txt"><div class="lm-small">ללומד חדש</div><div class="lm-big">התחל ללמוד</div>' +
        '<div class="lm-small">הדף היומי של היום, או מסכת ברכות מן ההתחלה.</div></div>' +
        '<div class="lm-row">' + (mm && mm.built ? '<a class="lm-btn" href="' + UI.readHref(t.slug, t.daf) + '">הדף היומי: ' + E(t.name) + ' ' + E(t.daf) + '</a>' : '') +
        '<a class="lm-btn ghost" href="berakhot.html">מסכת ברכות</a></div>';
      wrap.appendChild(first);
    }
    /* כרטיס הדף היומי */
    var y = window.LGDaf && LGDaf.forStr(LG.ymd(now));
    if (y) {
      var ym = LG.masechet(y.slug), has = ym && ym.built;
      var dc = el('div', 'lm-card lm-hero');
      dc.innerHTML = '<div class="lm-txt"><div class="lm-small">הדף היומי · ' + E(LG.hebDateShort(now)) + ' · ' + E(LG.gDate(now)) + '</div>' +
        '<div class="lm-big">' + E(y.name) + ' ' + E(LG.hebq(y.n)) + '</div>' +
        (has ? '' : '<div class="lm-small">מסכת זו עדיין בהכנה באתר. אפשר לסמן "למדתי בספר".</div>') + '</div>' +
        (has ? '<a class="lm-btn" href="' + UI.readHref(y.slug, LG.dafLabel(y.n, 0)) + '">ללמוד את הדף של היום</a>' : '<a class="lm-btn ghost" href="yomi.html">לדף היומי</a>');
      wrap.appendChild(dc);
    }
    /* לומד חוזר: תמצית */
    if (S.sessions.length || S.doneEvents.length) {
      var w = UI.weekSummary();
      var sc = el('div', 'lm-card');
      var my = (set.my || [])[0] || (S.last.all && S.last.all.s);
      var fc = '';
      if (my) {
        var rem = LG.remainingMs(my), daily = LG.dailyMs(), fd = LG.finishDate(rem, daily, set.skipDays);
        if (fd && rem > 0) fc = '<div class="lm-stat"><b>' + E(LG.gDateShort(fd.ymd)) + '</b><span>סיום ' + E(LG.nameOf(my)) + ' בקצב הנוכחי</span></div>';
      }
      sc.innerHTML = '<h3>השבוע שלך</h3><div class="lm-stats">' +
        '<div class="lm-stat"><b>' + E(LG.dur(w.ms)) + '</b><span>זמן לימוד</span></div>' +
        '<div class="lm-stat"><b>' + LG.nf(w.pages) + '</b><span>עמודים נלמדו</span></div>' +
        (set.streak === false ? '' : '<div class="lm-stat"><b>' + LG.nf(w.streak) + '</b><span>ימים ברצף</span></div>') + fc + '</div>' +
        '<p style="margin:12px 0 0"><a href="lamed.html">לכל הלימוד שלי</a></p>';
      wrap.appendChild(sc);
    }
    var nav = el('div', 'lm-card');
    nav.innerHTML = '<h3>כניסות</h3><div class="lm-row"><a class="lm-btn" href="shas.html">מפת הש"ס</a><a class="lm-btn ghost" href="lamed.html">הלימוד שלי</a><a class="lm-btn ghost" href="yomi.html">הדף היומי</a></div>' +
      '<p class="lm-note" style="margin:12px 0 0">לאוקמי גירסא הוא קיצור התלמוד הבבלי: שלד הסוגיה בלבד, עם המקור המנוקד מוצמד לכל קטע ו"פירוש הגמרא" לצדו.</p>';
    wrap.appendChild(nav);
    root.appendChild(wrap);
    UI.maybeOnboard();
  };

  /* ---------------------------------------------------------- מפת הש"ס */
  UI.shas = function (root) {
    var wrap = el('main', 'lm-wrap');
    wrap.innerHTML = '<h1 class="lm-t">מפת הש"ס</h1><p class="lm-sub">ששת הסדרים. מסכת שעדיין אינה באתר מוצגת עמומה, עם "בהכנה".</p>' +
      '<div class="lm-card"><div class="lm-field" style="margin:0"><label for="lm-jump">קפיצה מהירה (למשל "חולין מב" או "בכורות יח:")</label>' +
      '<div class="lm-row"><input id="lm-jump" type="text" placeholder="מסכת ודף" autocomplete="off"><button class="lm-btn" id="lm-jgo" type="button">קפוץ</button></div><div class="lm-note" id="lm-jmsg"></div></div></div>';
    LG.shas().seder.forEach(function (s) {
      var sec = el('section', 'lm-seder'); sec.innerHTML = '<h2 class="lm-t2">סדר ' + E(s.name) + '</h2>';
      var g = el('div', 'lm-vols');
      s.masechtot.forEach(function (m) {
        var n = el(m.built ? 'a' : 'div', 'lm-vol' + (m.built ? '' : ' off'));
        if (m.built) {
          var st = LG.masechetStats(m.slug);
          n.href = 'masechet.html?m=' + m.slug;
          n.innerHTML = '<b>' + E(m.name) + '</b><small>' + LG.nf(st.dafimTotal) + ' דפים</small>' +
            UI.ring(st.ratio, st.ratio ? LG.pct(st.ratio) : '', 'sm', 0) + UI.bar(st.done, st.ext, st.total) +
            (st.cycle ? '<small>מחזור ' + E(LG.hebq(st.cycle + 1)) + '</small>' : '');
        } else n.innerHTML = '<b>' + E(m.name) + '</b><small>בהכנה</small>';
        g.appendChild(n);
      });
      sec.appendChild(g); wrap.appendChild(sec);
    });
    root.appendChild(wrap);
    /* חיפוש מהיר */
    function go() {
      var q = $('#lm-jump').value.trim(), msg = $('#lm-jmsg');
      if (!q) return;
      var all = LG.masechtot().sort(function (a, b) { return b.name.length - a.name.length; });
      var m = all.filter(function (x) { return q.indexOf(x.name) === 0 || x.name.indexOf(q.split(' ')[0]) === 0; })[0];
      if (!m) { msg.textContent = 'לא נמצאה מסכת בשם הזה.'; return; }
      var rest = q.slice(q.indexOf(m.name) === 0 ? m.name.length : q.split(' ')[0].length).trim();
      if (!m.built) { msg.textContent = 'מסכת ' + m.name + ' עדיין בהכנה באתר.'; return; }
      var num = LG.gem(rest.replace(/[.:]/g, '')), amud = /:$/.test(rest) ? 1 : 0;
      if (!rest || !num) { location.href = 'masechet.html?m=' + m.slug; return; }
      var daf = LG.dafLabel(num, amud);
      var has = (m.dafim || []).some(function (d) { return d[0] === daf; });
      if (!has) { msg.textContent = 'העמוד ' + daf + ' אינו במסכת ' + m.name + '.'; return; }
      location.href = UI.readHref(m.slug, daf);
    }
    $('#lm-jgo').onclick = go;
    $('#lm-jump').addEventListener('keydown', function (e) { if (e.key === 'Enter') go(); });
  };

  /* ---------------------------------------------------------- דף מסכת */
  function tileClass(info) {
    var c = 'lm-tile';
    if (info.st === 'done') {
      var k = info.n - info.cyc;      /* חזרות במחזור הנוכחי: 1, 2-3, 4-9, 10+ */
      var n = info.n;
      c += n >= 10 ? ' r4' : n >= 4 ? ' r3' : n >= 2 ? ' r2' : ' r1';
    } else if (info.st === 'ext') c += ' ext';
    else if (info.st === 'prog') c += ' prog';
    return c;
  }
  UI.masechet = function (root) {
    var slug = new URLSearchParams(location.search).get('m') || 'berakhot';
    var m = LG.masechet(slug);
    var wrap = el('main', 'lm-wrap');
    if (!m) { wrap.innerHTML = '<h1 class="lm-t">מסכת לא נמצאה</h1><p><a href="shas.html">חזרה למפה</a></p>'; root.appendChild(wrap); return; }
    var S = LG.state(), set = S.settings, st = LG.masechetStats(slug), my = (set.my || []).indexOf(slug) > -1;
    var last = S.last.by[slug];
    var perakim = m.perakim || [], amudim = LG.amudim(slug);
    var head = el('div', 'lm-card lm-hero');
    var rem = LG.remainingMs(slug), daily = LG.dailyMs(), pace = LG.pace(slug), fd = LG.finishDate(rem, daily, set.skipDays);
    head.innerHTML = UI.ring(st.ratio, null, '', st.ratio ? 0 : 0) + '<div class="lm-txt"><h1 class="lm-t" style="margin:0">מסכת ' + E(m.name) + '</h1>' +
      '<div class="lm-small">' + LG.nf(perakim.length) + ' פרקים · ' + LG.nf(st.dafimTotal) + ' דפים · ' + LG.nf(st.total) + ' עמודים</div>' +
      '<div style="margin-top:6px">נלמדו ' + LG.nf(st.dafimDone) + ' מתוך ' + LG.nf(st.dafimTotal) + ' דפים' + (st.cycle ? ' · מחזור ' + E(LG.hebq(st.cycle + 1)) : '') + '</div></div>' +
      '<div class="lm-row"><a class="lm-btn" href="' + (UI.readHref(slug, amudim[0] ? amudim[0].daf : 'ב.', last) || '#') + '">' + (last ? 'המשך ללמוד' : 'התחל ללמוד') + '</a>' +
      '<button class="lm-btn ghost" id="lm-my" type="button">' + (my ? 'הסר מ"המסכתות שלי"' : 'הוסף ל"המסכתות שלי"') + '</button></div>';
    wrap.appendChild(head);

    /* תחזית */
    var fc = el('div', 'lm-card');
    var perPage = (LG.avgWords() * pace.perWord);
    var goal = (set.goals || {})[slug] || {};
    var dm = goal.minutes || Math.round(daily / 60000) || 20;
    var fHtml = '<h3>תחזית סיום</h3>';
    if (st.learned >= st.total && st.total) fHtml += '<p>המסכת נשלמה במחזור הנוכחי.</p>';
    else {
      fHtml += '<p id="lm-fc"></p><div class="lm-field"><label for="lm-sl">אם אלמד כך בכל יום: <b id="lm-slv">' + dm + '</b> דקות</label>' +
        '<input id="lm-sl" type="range" min="5" max="180" step="5" value="' + dm + '"></div>' +
        '<p class="lm-note" id="lm-fcn"></p>';
    }
    fc.innerHTML = fHtml; wrap.appendChild(fc);
    function drawFc() {
      var out = $('#lm-fc', fc); if (!out) return;
      var mins = +$('#lm-sl', fc).value; $('#lm-slv', fc).textContent = mins;
      var r2 = LG.finishDate(rem, mins * 60000, set.skipDays);
      var base = daily >= 60000 ? 'בקצב שלך (כ-' + LG.nf(Math.round(perPage / 60000)) + ' דקות לעמוד ממוצע) נשארו לך ' + LG.dur(rem, true) + ' לסיום המסכת. ' : 'נשארו לך ' + LG.dur(rem, true) + ' לסיום המסכת (הערכה ראשונית). ';
      out.textContent = base + (r2 ? 'אם תלמד ' + mins + ' דקות ביום - תסיים ביום ' + LG.WD[new Date(LG.ymdToUTC(r2.ymd)).getUTCDay()] + ' ' + LG.hebDateShort(LG.ymdToUTC(r2.ymd) + 43200000) + ' (' + LG.gDateShort(r2.ymd) + '.' + r2.ymd.slice(0, 4) + ').' : '');
      var g = (set.goals || {})[slug];
      var note = $('#lm-fcn', fc);
      if (g && g.end && r2) {
        var days = LG.diffDays(LG.ymd(Date.now()), g.end), pagesLeft = st.total - st.learned;
        if (days > 0) {
          var perDay = pagesLeft / 2 / days;
          note.textContent = 'כדי לסיים עד ' + LG.gDateShort(g.end) + ' - כ-' + (Math.round(perDay * 10) / 10) + ' דפים ביום.' +
            (r2.ymd <= g.end ? ' בקצב הזה תקדים - כל הכבוד.' : ' עוד ' + Math.max(5, Math.ceil((rem / Math.max(1, days) - mins * 60000) / 60000 / 5) * 5) + ' דקות ביום יחזירו אותך ליעד.');
        }
      }
    }
    if ($('#lm-sl', fc)) { $('#lm-sl', fc).oninput = drawFc; drawFc(); }

    /* מפת עמודים לפי פרקים */
    var mapC = el('div', 'lm-card'); mapC.innerHTML = '<h3>עמודי המסכת</h3>' +
      '<div class="lm-legend"><span><em style="background:var(--c0)"></em>לא נלמד</span><span><em style="background:var(--prog)"></em>בתהליך</span><span><em style="background:var(--c1)"></em>נלמד</span><span><em style="background:var(--c2)"></em>פעמיים</span><span><em style="background:var(--c3)"></em>4+</span><span><em style="background:var(--c4)"></em>10+</span><span><em style="background:var(--ext)"></em>בשיעור או בספר</span></div>';
    var chap = [];
    perakim.forEach(function (p, i) { chap.push({ name: (p[0] || '') + (p[1] ? ': ' + p[1] : ''), from: LG.dafKey(p[2]) }); });
    if (!chap.length) chap.push({ name: '', from: 0 });
    var sugg = LG.suggFor ? LG.suggFor(slug) : {};
    chap.forEach(function (c, ci) {
      var to = ci + 1 < chap.length ? chap[ci + 1].from - 1 : 1e9;
      var tiles = amudim.filter(function (a) { var k = LG.dafKey(a.daf); return k >= c.from && k <= to; });
      if (!tiles.length) return;
      var box = el('div', 'lm-pk'); box.innerHTML = '<h4>' + E(c.name || 'כל המסכת') + '</h4>';
      var tl = el('div', 'lm-tiles');
      tiles.forEach(function (a) {
        var info = LG.amudInfo(slug, a.daf), t = el('div', tileClass(info));
        t.dataset.daf = a.daf; t.tabIndex = 0; t.setAttribute('role', 'button');
        t.innerHTML = E(a.daf) + (info.n > 1 ? '<i>' + LG.nf(info.n) + '</i>' : '') + (sugg[a.daf] ? '<u title="הצעת תיקון שלך"></u>' : '');
        if (info.st === 'prog' && info.a) t.style.setProperty('--p', Math.round(100 * Math.min(.95, info.a.prog || .3)) + '%');
        if (last && last.d === a.daf) t.classList.add('now');
        t.onclick = function () { UI.tileInfo(slug, a.daf); };
        t.onkeydown = function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); UI.tileInfo(slug, a.daf); } };
        tl.appendChild(t);
      });
      box.appendChild(tl); mapC.appendChild(box);
    });
    wrap.appendChild(mapC);

    var rg = el('div', 'lm-card');
    rg.innerHTML = '<h3>למדתי מחוץ לאתר</h3><p class="lm-note">שיעור או ספר: מסומן בצבע נפרד ואינו נספר בזמן.</p><button class="lm-btn ghost" id="lm-rng" type="button">סמן טווח כנלמד</button>';
    wrap.appendChild(rg);
    root.appendChild(wrap);
    $('#lm-my', wrap).onclick = function () {
      var cur = (LG.settings().my || []).slice(), i = cur.indexOf(slug);
      if (i > -1) cur.splice(i, 1); else cur.push(slug);
      LG.setSetting('my', cur); location.reload();
    };
    $('#lm-rng', wrap).onclick = function () { UI.rangeModal(slug); };
  };
  UI.tileInfo = function (slug, daf) {
    var info = LG.amudInfo(slug, daf), a = info.a, m = LG.masechet(slug);
    var rows = '';
    if (a && a.dates.length) rows = '<ul class="lm-list">' + a.dates.map(function (d, i) {
      return '<li><span class="lm-grow">' + E(LG.gDate(LG.ymdToUTC(d) + 43200000)) + ' · ' + E(LG.hebDateShort(LG.ymdToUTC(d) + 43200000)) + '</span><span>' + (a.ms[i] ? E(LG.dur(a.ms[i])) : 'ללא מדידה') + '</span></li>';
    }).join('') + '</ul>';
    var first = a && a.ms.length > 1 && a.ms[0] && a.ms[a.ms.length - 1] ? '<p class="lm-note">זמן בחזרה הראשונה: ' + LG.dur(a.ms[0]) + ' · באחרונה: ' + LG.dur(a.ms[a.ms.length - 1]) + '</p>' : '';
    var href = UI.readHref(slug, daf);
    var mod = UI.modal('<h3>' + E(LG.nameOf(slug)) + ' · עמוד ' + E(daf) + '</h3>' +
      '<p>' + (info.st === 'done' ? 'נלמד ' + LG.nf(info.n) + ' פעמים' : info.st === 'ext' ? 'נלמד מחוץ לאתר' : info.st === 'prog' ? 'בתהליך' : 'טרם נלמד') + '</p>' + rows + first +
      '<div class="lm-row" style="margin-top:12px">' + (href ? '<a class="lm-btn" href="' + href + '">פתח את העמוד</a>' : '') +
      '<button class="lm-btn ghost" id="lm-mk" type="button">סמן כנלמד</button>' +
      (info.st !== 'none' ? '<button class="lm-btn ghost" id="lm-un" type="button">בטל סימון</button>' : '') + '</div>');
    $('#lm-mk', mod).onclick = function () { LG.track.markDone(slug, daf, 'manual', 0); mod.close(); location.reload(); };
    var un = $('#lm-un', mod); if (un) un.onclick = function () { LG.track.unmark(slug, daf); mod.close(); location.reload(); };
  };
  UI.rangeModal = function (slug) {
    var list = LG.amudim(slug).map(function (a) { return a.daf; });
    var opts = list.map(function (d) { return '<option>' + E(d) + '</option>'; }).join('');
    var mod = UI.modal('<h3>סימון טווח כנלמד</h3><div class="lm-field"><label>מעמוד</label><select id="lm-r1">' + opts + '</select></div>' +
      '<div class="lm-field"><label>עד עמוד</label><select id="lm-r2">' + opts + '</select></div>' +
      '<p class="lm-note">מסומן "בשיעור או בספר", בלי זמן.</p><div class="lm-row"><button class="lm-btn" id="lm-rok" type="button">סמן</button><button class="lm-btn ghost" id="lm-rno" type="button">ביטול</button></div>');
    $('#lm-r2', mod).selectedIndex = Math.min(1, list.length - 1);
    $('#lm-rno', mod).onclick = function () { mod.close(); };
    $('#lm-rok', mod).onclick = function () {
      LG.put({ k: 'ex', s: slug, from: $('#lm-r1', mod).value, to: $('#lm-r2', mod).value, t: Date.now() });
      mod.close(); location.reload();
    };
  };
})();
