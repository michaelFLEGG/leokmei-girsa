/* lamed - "שמע" ליד כל יחידה (פרומפט 83, 23.11.2026). ליד כל כותרת נושא (ו-ד"ה) בדף שיש לו
   שיעור מוקלט, כפתור קטן שמפעיל את השיעור מהדקה של הקטע הזה. הנתונים בונים tools/shma.py
   (shma/<slug>.json). השמע מתארח באתר עצמו, כי יוטיוב חסום אצל רבים; יוטיוב נשאר אפשרות נוספת.
   כלל הבטיחות: יחידה בלי נקודה ודאית, או שכותרתה השתנתה מאז ההתאמה, מתחילה מתחילת הדף.
   הכפתור יושב מעל השורה (position:absolute) ואינו מזיז שום טקסט. הכיתוב שלו ב-CSS בלבד,
   כדי שלא ייכנס להעתקה, לוורד או להדפסה. במצב דפוס ובהדפסה הוא מוסתר. */
(function () {
  'use strict';
  var LG = window.LAMED, E = LG.esc;
  var SL = window.LG_SHMA || [];
  var NIK = /[֑-ׇ]/g;

  function ht(h) { return String(h || '').replace(/<[^>]+>/g, '').replace(NIK, '').replace(/\s+/g, ' ').trim().slice(0, 60); }
  function same(a, b) { a = ht(a).slice(0, 20); b = ht(b).slice(0, 20); return !!a && a === b; }
  function el(tag, cls, html) { var e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; }
  function mmss(s) { s = Math.max(0, Math.round(s || 0)); var h = Math.floor(s / 3600), m = Math.floor(s % 3600 / 60), x = s % 60;
    return (h ? h + ':' + (m < 10 ? '0' : '') : '') + m + ':' + (x < 10 ? '0' : '') + x; }

  /* ---------------------------------------------------------- הנגן */
  var BAR = null;
  function close() { if (BAR) { var a = BAR.querySelector('audio'); if (a) a.pause(); BAR.remove(); BAR = null; } }
  function ytBox(vid, s, title) {
    var ov = el('div', 'lm-shiur-ov'), box = el('div', 'lm-shiur-box');
    var x = el('button', 'lm-shiur-x', '&times;'); x.type = 'button'; x.setAttribute('aria-label', 'סגור');
    x.onclick = function () { ov.remove(); };
    ov.onclick = function (e) { if (e.target === ov) ov.remove(); };
    box.innerHTML = '<div class="lm-shiur-v"><iframe src="https://www.youtube-nocookie.com/embed/' + E(vid) + '?rel=0&autoplay=1&start=' + Math.floor(s || 0) +
      '" title="' + E(title || 'שיעור') + '" allow="autoplay; encrypted-media; picture-in-picture; fullscreen" allowfullscreen></iframe></div>';
    box.insertBefore(x, box.firstChild); ov.appendChild(box); document.body.appendChild(ov);
  }
  function play(ent, s, where) {
    close();
    if (!ent.audio) { ytBox(ent.yt, s, ent.title); return; }
    BAR = el('div', 'lm-shma-bar');
    BAR.setAttribute('role', 'region'); BAR.setAttribute('aria-label', 'נגן השיעור');
    BAR.innerHTML = '<div class="lm-shma-t">' + E(where) + (s ? ' · מדקה ' + mmss(s) : ' · מתחילת הדף') + '</div>' +
      '<audio controls preload="auto" src="' + E(ent.audio) + '"></audio>' +
      (ent.yt ? '<button type="button" class="lm-shma-yt">ביוטיוב</button>' : '') +
      '<button type="button" class="lm-shma-x" aria-label="סגור את הנגן">&times;</button>';
    document.body.appendChild(BAR);
    var a = BAR.querySelector('audio');
    var go = function () { try { a.currentTime = s || 0; } catch (e) { } var p = a.play(); if (p && p.catch) p.catch(function () { }); };
    if (a.readyState >= 1) go(); else a.addEventListener('loadedmetadata', go, { once: true });
    BAR.querySelector('.lm-shma-x').onclick = close;
    var y = BAR.querySelector('.lm-shma-yt');
    if (y) y.onclick = function () { var t = a.currentTime; close(); ytBox(ent.yt, t, ent.title); };
  }

  /* ---------------------------------------------------------- הכפתורים */
  function init(data) {
    var plan = [];                       /* [unitId, ent, s, daf] */
    D.pages.forEach(function (p) {
      var d = (p.daf || '').trim(), ents = data[d];
      if (!ents || !ents.length) return;
      var ent = ents.filter(function (e) { return e.audio; })[0] || ents[0];
      var k = 0;
      p.units.forEach(function (u) {
        if (u.k !== 'nose' && u.k !== 'dh') return;
        var m = ent.u && ent.u[k], s = ent.from || 0;
        if (m && m.s != null && same(m.t, u.a)) s = m.s;
        plan.push([u.id, ent, s, d]); k += 1;
      });
    });
    if (!plan.length) return;
    function scan() {
      plan.forEach(function (x) {
        var row = document.getElementById('u' + x[0]);
        if (!row || row.querySelector(':scope > .lm-shma')) return;
        var b = el('button', 'lm-shma'); b.type = 'button';
        b.setAttribute('aria-label', 'שמע את השיעור מכאן'); b.title = 'שמע את השיעור על הקטע הזה';
        b.onclick = function (e) { e.preventDefault(); e.stopPropagation(); play(x[1], x[2], LG.nameOf ? LG.nameOf(SLUG) + ' ' + x[3] : x[3]); };
        b.onmousedown = function (e) { e.stopPropagation(); };
        row.appendChild(b);
      });
    }
    scan(); setInterval(scan, 1500);
  }

  function start() {
    if (typeof SLUG === 'undefined' || typeof D === 'undefined' || !document.getElementById('flow')) return;
    if (SL.indexOf(SLUG) < 0) return;    /* מסכת בלי שמע: אין שום בקשה לשרת */
    fetch('/shma/' + SLUG + '.json').then(function (r) { return r.ok ? r.json() : {}; }).then(init).catch(function () { });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', function () { setTimeout(start, 900); });
  else setTimeout(start, 900);
})();
