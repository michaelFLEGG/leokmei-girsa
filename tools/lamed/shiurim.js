/* lamed - שיעורי יוטיוב (מנה 4, 7.10.2026): מדור "שיעורים", כפתור "שיעור על הדף"
   בדף הגמרא, והוספת שיעור בידי המנהל. הנתונים בשרת ההצעות (/lessons); הקריאה פתוחה
   והכתיבה למנהל בלבד. נגן מוטמע בלי עוגיות (youtube-nocookie). צפייה בשיעור נרשמת
   כלימוד של כל הדפים שהוא מכסה. */
(function () {
  'use strict';
  var LG = window.LAMED, UI = LG.ui, E = LG.esc;
  var API = 'https://leokmei-suggest.m7654301.workers.dev';
  var CACHE = null;

  function $(s, r) { return (r || document).querySelector(s); }
  function el(tag, cls, html) { var e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; }
  function adminKey() { try { return localStorage.getItem('lg-adm') || ''; } catch (e) { return ''; } }

  function load(fresh) {
    if (!CACHE || fresh) {
      CACHE = fetch(API + '/lessons').then(function (r) { return r.json(); })
        .then(function (j) { return j.items || []; }).catch(function () { return []; });
    }
    return CACHE;
  }
  function forDaf(items, slug, daf) {
    return items.filter(function (l) { return l.slug === slug && LG.range(slug, l.from, l.to).indexOf(daf) > -1; });
  }
  function where(l) {
    return LG.nameOf(l.slug) + ' ' + l.from + (l.to && l.to !== l.from ? ' - ' + l.to : '');
  }
  function mark(l) {
    var k = 'lg-shiur-' + l.id + '-' + LG.ymd(Date.now());
    try { if (sessionStorage.getItem(k)) return; sessionStorage.setItem(k, '1'); } catch (e) { }
    LG.range(l.slug, l.from, l.to).forEach(function (d) {
      LG.put({ k: 'dn', s: l.slug, d: d, how: 'shiur', ms: 0, t: Date.now() });
    });
  }
  function card(l, admin, onDel) {
    var c = el('div', 'lm-card lm-shiur');
    c.innerHTML = '<div class="lm-shiur-v"><button type="button" class="lm-shiur-play" aria-label="נגן את השיעור">' +
      '<img src="' + E(l.thumb) + '" alt="" loading="lazy"><span>&#9654;</span></button></div>' +
      '<h3>' + E(l.title) + '</h3><p class="lm-sub">' + E(where(l)) + (l.author ? ' · ' + E(l.author) : '') + '</p>';
    $('.lm-shiur-play', c).onclick = function () {
      $('.lm-shiur-v', c).innerHTML = '<iframe src="https://www.youtube-nocookie.com/embed/' + E(l.vid) + '?rel=0&autoplay=1" title="' + E(l.title) +
        '" allow="autoplay; encrypted-media; picture-in-picture; fullscreen" allowfullscreen></iframe>';
      mark(l);
    };
    if (admin) {
      var d = el('button', 'lm-btn ghost', 'מחק שיעור'); d.type = 'button';
      d.onclick = function () { if (confirm('למחוק את השיעור?')) onDel(l); };
      c.appendChild(d);
    }
    return c;
  }
  function post(body) {
    return fetch(API + '/lessons', { method: 'POST', headers: { 'content-type': 'application/json', 'x-admin-key': adminKey() }, body: JSON.stringify(body) })
      .then(function (r) { return r.json(); });
  }
  function ldInject(items) {
    var old = $('#lm-ld'); if (old) old.remove();
    var s = el('script'); s.id = 'lm-ld'; s.type = 'application/ld+json';
    s.textContent = JSON.stringify(items.map(function (l) {
      return { '@context': 'https://schema.org', '@type': 'VideoObject', name: l.title, description: 'שיעור על ' + where(l),
        thumbnailUrl: l.thumb, uploadDate: new Date(l.t).toISOString().slice(0, 10),
        embedUrl: 'https://www.youtube-nocookie.com/embed/' + l.vid, contentUrl: 'https://www.youtube.com/watch?v=' + l.vid };
    }));
    document.head.appendChild(s);
  }

  /* ---------------------------------------------------------- מדור השיעורים */
  UI.shiurim = function (root) {
    var wrap = el('main', 'lm-wrap');
    wrap.innerHTML = '<h1 class="lm-t">שיעורים</h1><p class="lm-sub">שיעורי וידאו על הדף, לפי מסכת ודף. צפייה בשיעור נרשמת כלימוד של הדפים שהוא מכסה.</p><div id="lm-sh-add"></div><div id="lm-sh-list"></div>';
    root.appendChild(wrap);
    var admin = !!adminKey();
    function draw() {
      load().then(function (items) {
        var box = $('#lm-sh-list'); box.innerHTML = '';
        if (!items.length) { box.innerHTML = '<div class="lm-card">עדיין לא נוספו שיעורים.</div>'; return; }
        ldInject(items);
        var by = {};
        items.forEach(function (l) { (by[l.slug] = by[l.slug] || []).push(l); });
        LG.masechtot().forEach(function (m) {
          if (!by[m.slug]) return;
          box.appendChild(el('h2', 'lm-t2h', E(m.name)));
          by[m.slug].forEach(function (l) {
            box.appendChild(card(l, admin, function (x) { post({ op: 'del', id: x.id }).then(function () { load(true); draw(); }); }));
          });
        });
      });
    }
    if (admin) {
      var f = $('#lm-sh-add');
      var opts = LG.masechtot().filter(function (m) { return m.built; }).map(function (m) { return '<option value="' + E(m.slug) + '">' + E(m.name) + '</option>'; }).join('');
      f.innerHTML = '<div class="lm-card"><h3>הוסף שיעור</h3>' +
        '<div class="lm-row"><input id="sh-url" placeholder="הדבק כאן קישור יוטיוב" style="min-width:260px"></div>' +
        '<div class="lm-row"><select id="sh-m">' + opts + '</select><select id="sh-f" aria-label="מדף"></select><select id="sh-t" aria-label="עד דף (לא חובה)"></select></div>' +
        '<div class="lm-row"><button class="lm-btn" id="sh-save" type="button">שמור</button><span id="sh-msg" class="lm-sub"></span></div></div>';
      var fill = function () {
        var L = LG.amudim($('#sh-m').value).map(function (a) { return '<option>' + E(a.daf) + '</option>'; }).join('');
        $('#sh-f').innerHTML = L; $('#sh-t').innerHTML = '<option value="">עד דף: אותו דף</option>' + L;
      };
      $('#sh-m').onchange = fill; fill();
      $('#sh-save').onclick = function () {
        $('#sh-msg').textContent = 'שומר...';
        post({ op: 'add', url: $('#sh-url').value, slug: $('#sh-m').value, from: $('#sh-f').value, to: $('#sh-t').value })
          .then(function (j) {
            if (!j.ok) { $('#sh-msg').textContent = j.error || 'השמירה נכשלה'; return; }
            $('#sh-msg').textContent = 'נשמר'; $('#sh-url').value = ''; load(true); draw();
          }).catch(function () { $('#sh-msg').textContent = 'השמירה נכשלה'; });
      };
    }
    draw();
  };

  /* ---------------------------------------------------------- כפתור בדף הגמרא */
  function readerInit() {
    if (typeof SLUG === 'undefined' || !document.getElementById('flow') || !LG.track || !LG.track.cur) return;
    load().then(function (items) {
      var mine = items.filter(function (l) { return l.slug === SLUG; });
      if (!mine.length) return;
      var btn = el('button', 'lm-shiur-btn', 'שיעור על הדף'); btn.type = 'button'; btn.hidden = true;
      document.body.appendChild(btn);
      var cur = [];
      setInterval(function () {
        var p = LG.track.cur(), d = p && p.d;
        cur = d ? forDaf(mine, SLUG, d) : [];
        btn.hidden = !cur.length;
      }, 1500);
      btn.onclick = function () {
        var ov = el('div', 'lm-shiur-ov'), box = el('div', 'lm-shiur-box');
        var x = el('button', 'lm-shiur-x', '&times;'); x.type = 'button'; x.setAttribute('aria-label', 'סגור');
        x.onclick = function () { ov.remove(); };
        ov.onclick = function (e) { if (e.target === ov) ov.remove(); };
        box.appendChild(x);
        cur.forEach(function (l) { box.appendChild(card(l, false)); });
        ov.appendChild(box); document.body.appendChild(ov);
      };
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', function () { setTimeout(readerInit, 800); });
  else setTimeout(readerInit, 800);
})();
