/* mobile.js - קונסולת הניווט של הטלפון והטאבלט בדף המסכת (מנה 9.10.2026).
   נטען אחרי סקריפט הדף, ולכן משתמש בפונקציות שלו: goDaf, toDaf, setView, gemaraBtn, tzBtn,
   quizDaf, suggest, setFs, search. אינו משנה את עיצוב תוכן הדף. במחשב אינו עושה דבר. */
(function () {
  'use strict';
  if (!document.getElementById('flow') || typeof D === 'undefined') return;
  var H = document.documentElement, B = document.body;
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var NS = 'http://www.w3.org/2000/svg';
  function ic(n) { return '<svg class="ic" aria-hidden="true"><use href="#i-' + n + '"/></svg>'; }
  function lsGet(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function lsSet(k, v) { try { localStorage.setItem(k, v); } catch (e) { } }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function buzz(ms) { try { if (navigator.vibrate) navigator.vibrate(ms || 12); } catch (e) { } }
  function dev() { return H.classList.contains('dev-phone') ? 'phone' : H.classList.contains('dev-tab') ? 'tab' : 'desk'; }
  function flow() { return $('#flow'); }

  /* ------------------------------------------------------------------ בניית הממשק */
  /* הסרגלים כבר בקוד ה-HTML (כדי שטקסט יצויר מיד, לפני שהנתונים הגיעו). אם אינם שם - בונים אותם */
  if (!document.getElementById('mtop')) {
    var t0 = document.createElement('div'); t0.id = 'mtop';
    t0.innerHTML = '<button type="button" class="mhome" aria-label="לדף הבית"><img src="brand/shaar-v2/shaar-zohar-96.webp" alt="" width="20" height="30"></button>' +
      '<button type="button" class="mttl" id="mttl" aria-label="בחירת פרק ודף"><span>' + esc(D.masechet || '') + '</span><span class="mdf" id="mdf"></span>' + ic('down') + '</button>' +
      '<button type="button" class="msr" id="msr" aria-label="חיפוש">' + ic('search') + '</button>';
    var p0 = document.createElement('div'); p0.id = 'mprog'; p0.innerHTML = '<i></i>';
    var b0 = document.createElement('nav'); b0.id = 'mbot'; b0.setAttribute('aria-label', 'ניווט');
    var BTN0 = [['shas', 'home', 'הש"ס'], ['prev', 'right', 'דף קודם'], ['next', 'left', 'דף הבא'], ['perush', 'book', 'פירוש'], ['more', 'dots', 'עוד']];
    b0.innerHTML = BTN0.map(function (b) { return '<button type="button" data-a="' + b[0] + '">' + ic(b[1]) + '<span>' + b[2] + '</span></button>'; }).join('');
    var s0 = document.createElement('div'); s0.id = 'mscrim';
    var h0 = document.createElement('div'); h0.id = 'msheet'; h0.setAttribute('role', 'dialog'); h0.setAttribute('aria-modal', 'true');
    B.appendChild(t0); B.appendChild(p0); B.appendChild(b0); B.appendChild(s0); B.appendChild(h0);
  }
  var top = document.getElementById('mtop'), prog = document.getElementById('mprog'), bot = document.getElementById('mbot'), scrim = document.getElementById('mscrim'), sheet = document.getElementById('msheet');

  function flash(el) { el.classList.remove('flash'); void el.offsetWidth; el.classList.add('flash'); buzz(10); }

  /* ------------------------------------------------------------------ סוג המכשיר (מתעדכן בסיבוב) */
  function classify() {
    var w = innerWidth, h = innerHeight, mn = Math.min(w, h), mx = Math.max(w, h);
    var co = matchMedia('(pointer:coarse)').matches;
    var ph = w < 768 || (co && mn < 500);
    var tb = !ph && co && mn >= 500 && mx <= 1400;
    H.classList.toggle('dev-phone', ph); H.classList.toggle('dev-tab', tb); H.classList.toggle('dev-desk', !ph && !tb);
    H.classList.toggle('land', w > h); H.classList.toggle('port', w <= h);
    var bar = $('#bar'), d = ph ? 46 : 52;
    H.style.setProperty('--mtop', d + 'px');
    return ph ? 'phone' : tb ? 'tab' : 'desk';
  }

  /* ------------------------------------------------------------------ עוגן קריאה: לא מאבדים מקום בסיבוב ובהחלפת מצב */
  function readAnchor() {
    var f = flow(); if (!f) return null;
    var fr = f.getBoundingClientRect(), rows = f.querySelectorAll('[id^="u"]');
    for (var i = 0; i < rows.length; i++) {
      var r = rows[i].getBoundingClientRect();
      if (r.bottom > fr.top + 60 && r.right > 0 && r.left < innerWidth && r.top < fr.bottom) return rows[i].id;
    }
    return null;
  }
  var quiet = 0;
  function restoreAnchor(id) {
    if (!id) return;
    var e = document.getElementById(id); if (!e) return;
    quiet = Date.now() + 600;
    try { e.scrollIntoView({ block: 'start', inline: 'center' }); } catch (x) { e.scrollIntoView(true); }
    B.classList.remove('mhide');
  }

  /* ------------------------------------------------------------------ מצבי תצוגה לפי סוג המסך */
  function wantMode() {
    var d = dev();
    if (d === 'phone') return 'one';
    if (d === 'tab') { var s = lsGet('lg-mmode'); if (s === 'one' || s === 'book') return s; return innerWidth > innerHeight ? 'book' : 'one'; }
    return null;
  }
  function curMode() { var f = flow(); return f.classList.contains('book') ? 'book' : f.classList.contains('vert') ? 'vert' : 'col'; }
  function fitBook() {
    if (dev() !== 'tab') { H.style.removeProperty('--mfs'); return; }
    var top = parseInt(getComputedStyle(H).getPropertyValue('--mtop')) || 52;
    var bh = H.classList.contains('land') ? 12 : (parseInt(getComputedStyle(H).getPropertyValue('--mbot')) || 72) + 10;
    var availH = innerHeight - top - bh - 14, side = H.classList.contains('land') ? 78 : 0, availW = innerWidth - side - 14;
    var best = 0, bn = 1;
    [1, 2].forEach(function (n) { var fsW = (availW - 12) / (31.125 * n + 1.2 * (n - 1) + 1.6), fsH = availH / 44.979, f = Math.min(fsW, fsH); if (f > best + 0.01) { best = f; bn = n; } });
    H.style.setProperty('--mfs', Math.max(9, Math.floor(best * 100) / 100) + 'px'); H.style.setProperty('--mn', bn);
  }
  /* רוחב הטור הנקי קבוע: 20.75em, כמו בעמוד הספר (60 מ"מ), בכל טלפון וטאבלט.
     המסך הגדול או הקטן משנה רק את גודל האות (הגדלה יחסית של הטור כולו), ולעולם
     לא את מקום שבירת השורות. הסכום בטלפון: 20.75 + מסילה 3.1 + רווח .35 + שוליים 1.4 em.
     בטאבלט הגודל הנקוב 18 הוא כ-6 ס"מ ל-1/160 אינץ' לפיקסל (אנדרואיד); באייפד גדול
     (132 נקודות לאינץ') הפיקסל גדול יותר, ולכן 15. הגודל שבחר הלומד בכפתורי הגופן גובר. */
  var autoFs = false, ftm = 0, lastFs = 0;
  function refit() { clearTimeout(ftm); ftm = setTimeout(function () { try { setDafW(); fitAnchors(); } catch (e) { } }, 90); }
  function fitCol() {
    var d = dev(), f = flow();
    var off = d === 'desk' || !f || f.classList.contains('book') || lsGet('lg-fs');
    if (off) { if (autoFs) { H.style.removeProperty('--fs'); autoFs = false; refit(); } return; }
    var fs;
    if (d === 'phone') fs = Math.min(18, Math.max(12, Math.floor(H.clientWidth / 25.6 * 10) / 10));
    else {
      var ipad = /iPad/.test(navigator.userAgent) || (/Macintosh/.test(navigator.userAgent) && navigator.maxTouchPoints > 1);
      fs = ipad && Math.min(screen.width, screen.height) >= 810 ? 15 : 18;
    }
    /* בגודל הרגיל (18) אין מה לקבוע: כתיבת --fs מבטלת את כל חישובי הסגנון של הדף (נמדד: 19 שניות בטאבלט) */
    if (fs === 18) { if (autoFs) { H.style.removeProperty('--fs'); autoFs = false; refit(); } return; }
    if (autoFs && lastFs === fs) return;
    lastFs = fs; autoFs = true;
    H.style.setProperty('--fs', fs + 'px');
    refit();
  }
  var applying = false;
  function applyMode(keep) {
    if (applying) return; applying = true;
    fitCol();
    var anchor = keep ? readAnchor() : null;
    var want = wantMode(), cur = curMode(), changed = false;
    try {
      if (want === 'one') {
        if (cur !== 'col') { setView('col'); changed = true; }
      } else if (want === 'book' && cur !== 'book') { setView('book'); changed = true; }
      fitBook();
    } catch (e) { }
    setTimeout(function () { fitCol(); if (changed || keep) restoreAnchor(anchor); applying = false; }, 60);
  }

  /* ------------------------------------------------------------------ כותרת עליונה והתקדמות */
  var lastDaf = '';
  function curLabel() { var ds = $('#dafsel'); if (!ds || !ds.options.length) return ''; var o = ds.options[ds.selectedIndex]; return o ? o.text : ''; }
  function updTop() {
    var l = ($('#curdaf') && $('#curdaf').textContent.trim()) || curLabel();
    if (l !== lastDaf) { lastDaf = l; $('#mdf').textContent = l; }
    var ds = $('#dafsel'), n = (D.pages || []).length || 1, i = ds ? (+ds.value || 0) : 0;
    var f = flow(), part = 0;
    if (f && f.scrollHeight > f.clientHeight + 40 && curMode() !== 'book') part = Math.min(1, f.scrollTop / (f.scrollHeight - f.clientHeight));
    var ratio = Math.min(1, (i + (curMode() === 'vert' ? 0 : part * 0)) / n + (1 / n) * part * (curMode() === 'vert' ? 0 : 1));
    if (curMode() === 'vert') ratio = Math.min(1, (i + 1) / n);
    prog.firstChild.style.width = Math.round(ratio * 1000) / 10 + '%';
  }

  /* ------------------------------------------------------------------ גיליונות */
  var sheetOpen = false;
  function openSheet(html) {
    sheet.innerHTML = '<div class="grip" id="mgrip"></div>' + html;
    sheetOpen = true; scrim.classList.add('on'); sheet.classList.add('on'); B.classList.add('msheet-open'); buzz(8);
    sheet.scrollTop = 0;
  }
  function closeSheet() { if (!sheetOpen) return; sheetOpen = false; scrim.classList.remove('on'); sheet.classList.remove('on'); B.classList.remove('msheet-open'); }
  scrim.addEventListener('click', closeSheet);
  /* גרירת הידית כלפי מטה סוגרת */
  (function () {
    var y0 = null;
    sheet.addEventListener('touchstart', function (e) { if (e.target.id === 'mgrip' || sheet.scrollTop <= 0) y0 = e.touches[0].clientY; else y0 = null; }, { passive: true });
    sheet.addEventListener('touchend', function (e) { if (y0 == null) return; var dy = (e.changedTouches[0].clientY - y0); y0 = null; if (dy > 90) closeSheet(); }, { passive: true });
  })();
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeSheet(); });

  function fsNow() { return parseFloat(getComputedStyle(H).getPropertyValue('--fs')) || 18; }
  function fsSizes() { return dev() === 'phone' ? [[17, 'קטן'], [20, 'רגיל'], [25, 'גדול']] : [[16, 'קטן'], [19, 'רגיל'], [24, 'גדול']]; }
  function moreSheet() {
    var cur = null; try { cur = LAMED && LAMED.track && LAMED.track.cur && LAMED.track.cur(); } catch (e) { }
    var items = [];
    if ($('#tzbtn')) items.push(['tz', 'page', 'צורת הדף']);
    items.push(['quiz', 'quiz', 'בחן את עצמך']);
    items.push(['done', 'check', 'סמן כנלמד']);
    items.push(['sug', 'flag', 'הצע תיקון']);
    items.push(['search', 'search', 'חיפוש']);
    items.push(['my', 'clock', 'המקום שלי וההספק']);
    items.push(['share', 'upload', 'שיתוף הדף']);
    items.push(['toc', 'list', 'תוכן עניינים']);
    items.push(['full', 'gear', 'כלים מתקדמים']);
    var h = '<h3>עוד</h3><div class="mgrid">' + items.map(function (i) { return '<button type="button" class="mi" data-m="' + i[0] + '">' + ic(i[1]) + '<span>' + i[2] + '</span></button>'; }).join('') + '</div>';
    h += '<div class="mlbl">גודל הגופן</div><div class="mrow">' + fsSizes().map(function (s) { return '<button type="button" data-fs="' + s[0] + '" class="' + (Math.abs(fsNow() - s[0]) < 1.5 ? 'on' : '') + '">' + s[1] + '</button>'; }).join('') + '</div>';
    if (dev() === 'tab') {
      var m = curMode() === 'book' ? 'book' : 'one';
      h += '<div class="mlbl">מצב תצוגה</div><div class="mrow"><button type="button" data-mode="one" class="' + (m === 'one' ? 'on' : '') + '">טור אחד</button><button type="button" data-mode="book" class="' + (m === 'book' ? 'on' : '') + '">ספר</button></div>';
    }
    openSheet(h);
  }
  function pickSheet() {
    var ps = $('#peresel'), ds = $('#dafsel');
    var h = '<h3>מעבר מהיר</h3><div class="mlbl">פרק</div><select id="mper" aria-label="פרק">' + (ps ? ps.innerHTML : '') + '</select>' +
      '<div class="mlbl">דף</div><select id="mdaf" aria-label="דף">' + (ds ? ds.innerHTML : '') + '</select><button type="button" class="mbtn" id="mgo">פתח את הדף</button>';
    openSheet(h);
    var per = $('#mper'), df = $('#mdaf');
    if (ps) per.value = ps.value; if (ds) df.value = ds.value;
    per.onchange = function () {   /* פרק: קופצים לדף הראשון שלו */
      var si = +per.value, first = -1;
      D.pages.forEach(function (p, i) { if (first < 0 && typeof secOf === 'function' && secOf(i) === si) first = i; });
      if (first > -1) df.value = first;
    };
    $('#mgo').onclick = function () { closeSheet(); toDaf(+df.value); };
  }
  sheet.addEventListener('click', function (e) {
    var t = e.target.closest('button'); if (!t) return;
    if (t.dataset.fs) { setFs(+t.dataset.fs); sheet.querySelectorAll('[data-fs]').forEach(function (b) { b.classList.toggle('on', b === t); }); buzz(8); return; }
    if (t.dataset.mode) { lsSet('lg-mmode', t.dataset.mode); closeSheet(); applyMode(true); return; }
    var m = t.dataset.m; if (!m) return;
    closeSheet();
    setTimeout(function () {
      var cur = null; try { cur = LAMED.track.cur(); } catch (x) { }
      if (m === 'tz') tzBtn();
      else if (m === 'quiz') quizDaf();
      else if (m === 'done') { if (cur) { LAMED.track.markDone(SLUG, cur.d, 'manual'); } }
      else if (m === 'sug') suggest();
      else if (m === 'search') openSearch();
      else if (m === 'my') location.href = 'lamed.html';
      else if (m === 'share') share();
      else if (m === 'toc') panel('toc');
      else if (m === 'full') { B.classList.toggle('showbar'); H.style.setProperty('--mtop', '0px'); try { barFit(); } catch (x) { } }
    }, 120);
  });
  function share() {
    var d = ($('#mdf') && $('#mdf').textContent) || '', url = location.href.split('#')[0] + '#daf=' + encodeURIComponent(d);
    var data = { title: 'לאוקמי גירסא · ' + (D.masechet || '') + ' ' + d, url: url };
    if (navigator.share) navigator.share(data).catch(function () { });
    else if (navigator.clipboard) navigator.clipboard.writeText(url).then(function () { try { LAMED.track.toast('הקישור הועתק'); } catch (e) { } });
  }
  function openSearch() {
    var p = $('#search'); if (!p) return;
    var inp = $('#msq');
    if (!inp) {
      inp = document.createElement('input'); inp.type = 'search'; inp.id = 'msq'; inp.setAttribute('aria-label', 'חיפוש ב' + (D.masechet || ''));
      inp.placeholder = 'חיפוש ב' + (D.masechet || '');
      inp.style.cssText = 'width:100%;min-height:48px;font:600 18px var(--ui,serif);padding:6px 12px;margin:6px 0 10px;border:1px solid #c9a24a;border-radius:12px;background:#fff;color:#1b1b1b';
      inp.oninput = function () { search(inp.value); };
      var s = $('#sres'); s.parentNode.insertBefore(inp, s);
    }
    if (!p.classList.contains('open')) panel('search');
    setTimeout(function () { inp.focus(); }, 150);
  }

  /* ------------------------------------------------------------------ כפתורי הסרגל */
  bot.addEventListener('click', function (e) {
    var b = e.target.closest('button'); if (!b) return; flash(b);
    var a = b.dataset.a;
    if (a === 'shas') location.href = 'masechet.html?m=' + SLUG;
    else if (a === 'prev') goDaf(-1);
    else if (a === 'next') goDaf(1);
    else if (a === 'perush') { gemaraBtn(); setTimeout(syncPerush, 120); }
    else if (a === 'more') moreSheet();
  });
  top.addEventListener('click', function (e) {
    var b = e.target.closest('button'); if (!b) return; flash(b);
    if (b.classList.contains('mhome')) location.href = 'index.html';
    else if (b.id === 'mttl') pickSheet();
    else if (b.id === 'msr') openSearch();
  });
  function syncPerush() { B.classList.toggle('msrcopen', !!$('#srcx')); var b = $('#mbot [data-a="perush"]'); if (b) b.classList.toggle('on', !!$('#srcx')); }

  /* ------------------------------------------------------------------ מגירת הפירוש: שלושה מצבים עם ידית */
  var SNAP = [0.34, 0.58, 0.92];
  function availH() { return innerHeight - (parseInt(getComputedStyle(H).getPropertyValue('--mtop')) || 46) - (H.classList.contains('land') && dev() === 'tab' ? 0 : (parseInt(getComputedStyle(H).getPropertyValue('--mbot')) || 72)) - 4; }
  function setSnap(box, i) { box.dataset.snap = i; box.style.setProperty('--msh', Math.round(availH() * SNAP[i]) + 'px'); }
  function wireHandle(box) {
    if ($('#msh', box)) return;
    var h = document.createElement('div'); h.id = 'msh'; h.setAttribute('role', 'button'); h.setAttribute('aria-label', 'גודל המגירה');
    box.insertBefore(h, box.firstChild);
    /* במסך מלא: לשוניות עליונות למעבר מהיר בין גמרא, פירוש וצורת הדף, בלי לאבד מקום */
    var tabs = document.createElement('div'); tabs.id = 'mtabs'; tabs.setAttribute('role', 'tablist');
    tabs.innerHTML = '<button type="button" data-t="gem" role="tab">גמרא</button><button type="button" data-t="per" role="tab">פירוש</button>' + ($('#tzbtn') ? '<button type="button" data-t="tz" role="tab">צורת הדף</button>' : '');
    box.insertBefore(tabs, h.nextSibling);
    function tabsUi() { var v = (typeof SRCVIEW !== 'undefined') ? SRCVIEW : 'both'; tabs.querySelectorAll('[data-t]').forEach(function (b) { b.classList.toggle('on', b.dataset.t === v); b.setAttribute('aria-selected', b.dataset.t === v ? 'true' : 'false'); }); }
    tabs.addEventListener('click', function (e) {
      var b = e.target.closest('button'); if (!b) return; buzz(8);
      if (b.dataset.t === 'tz') { tzBtn(); return; }
      var pb = box.querySelector('#smpop [data-v="' + b.dataset.t + '"]'); if (pb) { pb.click(); setTimeout(tabsUi, 60); }
    });
    tabsUi();
    setSnap(box, +(box.dataset.snap || 1));
    var y0 = 0, hh = 0, drag = false;
    h.addEventListener('pointerdown', function (e) { drag = true; y0 = e.clientY; hh = box.getBoundingClientRect().height; h.setPointerCapture(e.pointerId); box.style.transition = 'none'; });
    h.addEventListener('pointermove', function (e) { if (!drag) return; var nh = Math.max(120, Math.min(availH(), hh + (y0 - e.clientY))); box.style.setProperty('--msh', nh + 'px'); });
    h.addEventListener('pointerup', function (e) {
      if (!drag) return; drag = false; box.style.transition = '';
      var cur = box.getBoundingClientRect().height / availH(), moved = Math.abs(e.clientY - y0) > 6;
      if (!moved) { setSnap(box, ((+box.dataset.snap || 1) + 1) % 3); buzz(8); return; }
      var bi = 0, bd = 9; SNAP.forEach(function (s, i) { if (Math.abs(s - cur) < bd) { bd = Math.abs(s - cur); bi = i; } });
      setSnap(box, bi); buzz(8);
    });
  }
  new MutationObserver(function () {
    var box = $('#srcx');
    if (box && dev() !== 'desk') wireHandle(box);
    syncPerush();
  }).observe(B, { childList: true });

  /* ------------------------------------------------------------------ הסתרה בגלילה והחלקה בין דפים */
  (function () {
    var f = flow(), last = 0, acc = 0;
    f.addEventListener('scroll', function () {
      if (dev() === 'desk') return;
      var t = f.scrollTop, d = t - last; last = t;
      if (curMode() === 'book' || Date.now() < quiet) return;
      if (t < 30) { B.classList.remove('mhide'); acc = 0; }
      else { acc = (d > 0) === (acc > 0) ? acc + d : d; if (acc > 24) { B.classList.add('mhide'); acc = 0; } else if (acc < -14) { B.classList.remove('mhide'); acc = 0; } }
      updTop();
    }, { passive: true });
    f.addEventListener('click', function (e) {
      if (dev() === 'desk' || e.target.closest('button,a,input,select,textarea,.mlabel,.srcb') || (getSelection() && !getSelection().isCollapsed)) return;
      B.classList.toggle('mhide');
    });
    var x0, y0, t0, tgt;
    f.addEventListener('touchstart', function (e) { if (e.touches.length !== 1) { x0 = null; return; } x0 = e.touches[0].clientX; y0 = e.touches[0].clientY; t0 = Date.now(); tgt = e.target; }, { passive: true });
    f.addEventListener('touchend', function (e) {
      if (x0 == null || dev() === 'desk' || curMode() === 'book') return;
      var dx = e.changedTouches[0].clientX - x0, dy = e.changedTouches[0].clientY - y0; x0 = null;
      if (Date.now() - t0 > 650 || Math.abs(dx) < 90 || Math.abs(dy) > 45 || Math.abs(dx) < 2.2 * Math.abs(dy)) return;
      if (getSelection() && !getSelection().isCollapsed) return;
      if (tgt && tgt.closest && tgt.closest('#srcx,.tzbody,.panel,#msheet')) return;
      goDaf(dx > 0 ? 1 : -1); buzz(10);   /* בכיוון עברי: החלקה ימינה = הדף הבא */
    }, { passive: true });
  })();
  /* צורת הדף: החלקה מחליפה עמוד א'/ב', הקשה כפולה מגדילה או מחזירה להתאמה לרוחב */
  (function () {
    var x0 = null, y0 = 0, t0 = 0, last = 0;
    document.addEventListener('touchstart', function (e) { var b = e.target.closest && e.target.closest('.tzbody'); if (!b || e.touches.length !== 1) { x0 = null; return; } x0 = e.touches[0].clientX; y0 = e.touches[0].clientY; t0 = Date.now(); }, { passive: true });
    document.addEventListener('touchend', function (e) {
      if (x0 == null) return;
      var b = e.target.closest && e.target.closest('.tzbody'); if (!b) { x0 = null; return; }
      var dx = e.changedTouches[0].clientX - x0, dy = e.changedTouches[0].clientY - y0, dt = Date.now() - t0; x0 = null;
      if (dt < 600 && Math.abs(dx) > 90 && Math.abs(dy) < 45 && Math.abs(dx) > 2.2 * Math.abs(dy) && b.scrollWidth <= b.clientWidth + 3) {
        var btn = document.getElementById(dx > 0 ? 'tznx' : 'tzpv'); if (btn) { btn.click(); buzz(10); }   /* עברית: החלקה ימינה = הבא */
        return;
      }
      if (dt < 250 && Math.abs(dx) < 12 && Math.abs(dy) < 12) {   /* הקשה; שתיים ברצף = הגדלה */
        var n = Date.now();
        if (n - last < 340) { var fit = b.scrollWidth <= b.clientWidth + 3; var z = document.getElementById(fit ? 'tzzi' : 'tzz1'); if (z) { z.click(); if (fit && z) { z.click(); } buzz(10); } last = 0; } else last = n;
      }
    }, { passive: true });
  })();
  /* ספר בטאבלט: הקשה כפולה על גיליון מגדילה אותו (ומחזירה) */
  (function () {
    var last = 0;
    flow().addEventListener('touchend', function (e) {
      if (dev() !== 'tab' || curMode() !== 'book' || e.touches.length) return;
      var n = Date.now(); if (n - last < 340) { flow().classList.toggle('bkz'); buzz(10); last = 0; } else last = n;
    }, { passive: true });
    flow().addEventListener('dblclick', function () { if (dev() === 'tab' && curMode() === 'book') flow().classList.toggle('bkz'); });
  })();
  /* הסרגלים חוזרים כשפותחים דף או כשהמסך מתחלף */
  ['hashchange', 'orientationchange'].forEach(function (ev) { addEventListener(ev, function () { B.classList.remove('mhide'); }); });

  /* בטלפון ובטאבלט הקטע גולל לאורך: toEl של הדף מניח טורים שגוללים הצידה */
  var _toEl = window.toEl;
  window.toEl = function (e) {
    var f = flow();
    if (dev() !== 'desk' && f && !f.classList.contains('book')) { e.scrollIntoView({ block: 'start' }); return; }
    if (dev() !== 'desk' && f && f.classList.contains('book')) { var sh = e.closest('.sheet'); if (sh) sh.scrollIntoView({ inline: 'center', block: 'nearest' }); return; }
    return _toEl(e);
  };

  /* קפיצה יזומה (בורר הדפים, הקישור, החיפוש) אינה גלילה של הלומד: הסרגלים נשארים */
  ['toDaf', 'jump', 'render'].forEach(function (fn) {
    var o = window[fn]; if (typeof o !== 'function') return;
    window[fn] = function () { quiet = Date.now() + 1100; B.classList.remove('mhide'); return o.apply(this, arguments); };
  });
  quiet = Date.now() + 1500;

  /* ------------------------------------------------------------------ הפעלה וסיבוב מסך */
  var rt = 0;
  function onResize() {
    clearTimeout(rt);
    rt = setTimeout(function () {
      var before = dev(); classify();
      var a = readAnchor();
      applyMode(false); setTimeout(function () { restoreAnchor(a); }, 120);
      var bx = $('#srcx'); if (bx && dev() !== 'desk') setSnap(bx, +(bx.dataset.snap || 1));
      updTop();
    }, 120);
  }
  addEventListener('resize', onResize); addEventListener('orientationchange', onResize);
  classify(); applyMode(false); updTop();
  setInterval(updTop, 700);
  window.LGMOBILE = { classify: classify, applyMode: applyMode, dev: dev };
})();
