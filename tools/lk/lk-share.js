/* lk-share.js - חלונית השיתוף של לאוקמי גירסא (14.10.2026).
   רכיב אחד לכל האתר: אתר, דף ועמוד, תוספות, תוצאת מבחן. נטען פעם אחת בכל דף ציבורי (defer), בהזרקה של lk_inject.py.
   כללי המנהל: בלי רשתות חברתיות, בלי חלונית השיתוף המובנית של המכשיר (navigator.share), בלי סקריפטים של צד שלישי.
   הקישורים הם קישורים פשוטים. קוד ה-QR נוצר בדפדפן. הספירה אנונימית: ערוץ ומה שותף בלבד.
   API: LKShare.site(), LKShare.page(), LKShare.tos(item), LKShare.quiz(info), LKShare.open({kind,text,url}). */
(function () {
  'use strict';
  var W = window, D = document;
  if (W.LKShare) return;
  var BASE = 'https://leokmei.com';
  var NAME = 'לאוקמי גירסא', TAG = 'קיצור התלמוד הבבלי';
  var LAMED_D = /*LAMED_D*/'M186.15 233.72H287.02Q328.45 233.44 328.74 285.44Q331.02 322.88 268.87 352.74Q206.72 382.6 208.72 421.75Q209.58 440.32 225.87 440.32Q247.59 440.03 249.59 408.6Q246.73 383.74 290.73 356.02Q334.74 328.31 345.88 301.3Q357.03 274.3 352.46 211.15Q347.88 148 287.88 148.28H206.44Q193.58 148 192.29 133.71Q191.01 119.42 202.01 111.85Q213.01 104.28 226.44 105.85Q239.87 107.42 249.44 113.14Q259.02 118.85 278.02 128.28Q297.02 137.71 314.45 110.28Q319.59 103.13 325.02 104.14Q330.45 105.14 332.17 103.42Q333.88 101.71 333.31 98.56Q329.02 87.99 317.31 79.27Q305.59 70.56 293.45 71.85Q281.3 73.13 267.59 93.99Q264.45 98.56 257.87 95.13Q239.87 87.42 211.72 89.28Q183.58 91.13 168.15 107.99Q152.72 124.85 151.86 163.43V192.86Q153 233.44 186.15 233.72Z'/*END_LAMED_D*/;
  /* טבלת בלוקי תיקון השגיאות של QR (גרסאות 1-14, רמות L M Q H), נגזרת מהספרייה qrcode בבנייה */
  var RS = /*RS_TABLE*/[[[1,26,19],[1,26,16],[1,26,13],[1,26,9]],[[1,44,34],[1,44,28],[1,44,22],[1,44,16]],[[1,70,55],[1,70,44],[2,35,17],[2,35,13]],[[1,100,80],[2,50,32],[2,50,24],[4,25,9]],[[1,134,108],[2,67,43],[2,33,15,2,34,16],[2,33,11,2,34,12]],[[2,86,68],[4,43,27],[4,43,19],[4,43,15]],[[2,98,78],[4,49,31],[2,32,14,4,33,15],[4,39,13,1,40,14]],[[2,121,97],[2,60,38,2,61,39],[4,40,18,2,41,19],[4,40,14,2,41,15]],[[2,146,116],[3,58,36,2,59,37],[4,36,16,4,37,17],[4,36,12,4,37,13]],[[2,86,68,2,87,69],[4,69,43,1,70,44],[6,43,19,2,44,20],[6,43,15,2,44,16]],[[4,101,81],[1,80,50,4,81,51],[4,50,22,4,51,23],[3,36,12,8,37,13]],[[2,116,92,2,117,93],[6,58,36,2,59,37],[4,46,20,6,47,21],[7,42,14,4,43,15]],[[4,133,107],[8,59,37,1,60,38],[8,44,20,4,45,21],[12,33,11,4,34,12]],[[3,145,115,1,146,116],[4,64,40,5,65,41],[11,36,16,5,37,17],[11,36,12,5,37,13]]]/*END_RS_TABLE*/;

  var GEM = { 'א': 1, 'ב': 2, 'ג': 3, 'ד': 4, 'ה': 5, 'ו': 6, 'ז': 7, 'ח': 8, 'ט': 9, 'י': 10, 'כ': 20, 'ל': 30, 'מ': 40, 'נ': 50, 'ס': 60, 'ע': 70, 'פ': 80, 'צ': 90, 'ק': 100, 'ר': 200, 'ש': 300, 'ת': 400 };
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }

  /* ---------------------------------------------------------------- הקשר הדף */
  function dafPath(daf) {
    var t = String(daf || ''), n = 0;
    t.replace(/[^א-ת]/g, '').split('').forEach(function (c) { n += GEM[c] || 0; });
    if (!n) return '';
    return n + (/:\s*$/.test(t) ? 'b' : 'a');
  }
  function slugNow() {
    try { if (typeof SLUG !== 'undefined' && SLUG) return SLUG; } catch (e) { }
    try { if (W.LK && LK.pageType) return LK.pageType().masechet || ''; } catch (e) { }
    return '';
  }
  function masechetName() {
    try { if (typeof DATA !== 'undefined' && DATA && DATA.masechet) return DATA.masechet; } catch (e) { }
    var t = D.querySelector('#mttl .mmn'); return t ? t.textContent.trim() : '';
  }
  function dafNow() {
    var o = D.querySelector('#dafsel option:checked');
    if (o && o.textContent.trim()) return o.textContent.trim().slice(0, 12);
    var m = D.getElementById('mdf'); if (m && m.textContent.trim()) return m.textContent.trim().slice(0, 12);
    var q = /[#&]daf=([^&]+)/.exec(location.hash || ''); if (q) { try { return decodeURIComponent(q[1]); } catch (e) { } }
    return '';
  }
  function dafUrl(slug, daf, extra) {
    var dp = dafPath(daf);
    return dp && slug ? BASE + '/' + slug + '/' + dp + '.html#go' + (extra || '') : (slug ? BASE + '/' + slug + '.html' : BASE + '/');
  }
  function dafLabel(daf) { return String(daf || '').trim(); }

  /* ---------------------------------------------------------------- נוסחי ההודעות */
  var API = {};
  API.site = function () { return { kind: 'אתר', title: 'שיתוף האתר', text: NAME + ' - ' + TAG, url: BASE + '/' }; };
  API.page = function () {
    var s = slugNow(), m = masechetName(), d = dafNow();
    if (!s || !d) return API.site();
    return { kind: 'דף', title: 'שיתוף הדף', text: NAME + ' - ' + TAG + ' | ' + m + ' ' + dafLabel(d), url: dafUrl(s, d) };
  };
  function firstSentence(t, max) {
    t = String(t || '').replace(/\s+/g, ' ').trim();
    var i = t.search(/[.!?:]\s/); if (i > 20) t = t.slice(0, i + 1);
    if (t.length > max) { t = t.slice(0, max); t = t.replace(/\s+\S*$/, '') + '...'; }
    return t;
  }
  function dhShort(t) {
    var w = String(t || '').replace(/[.:]+$/, '').trim().split(/\s+/);
    return w.slice(0, 5).join(' ') + (w.length > 5 ? '...' : '');
  }
  API.tos = function (o) {
    var s = slugNow(), m = masechetName(), d = o.daf || dafNow();
    var line = 'תוס\' ' + m + ' ' + dafLabel(d).replace(/[.:]+$/, '') + ' ד"ה ' + dhShort(o.dh) + (o.sum ? ': ' + firstSentence(o.sum, 120) : '');
    return { kind: 'תוס\'', title: 'שיתוף התוספות', text: line, url: dafUrl(s, d, '&tos=' + encodeURIComponent(o.n)) };
  };
  API.quiz = function (o) {
    var s = o.slug || slugNow();
    var line = 'ענית נכון על ' + o.right + ' מתוך ' + o.total + (o.masechet ? ' ב' + o.masechet : '') + ' - נסה גם אתה';
    return { kind: 'מבחן', title: 'שיתוף התוצאה', text: line, url: BASE + '/quiz.html' + (s ? '?m=' + encodeURIComponent(s) : '') };
  };

  /* ---------------------------------------------------------------- ספירה אנונימית */
  function sid() {
    try { return sessionStorage.getItem('lsid') || ('s' + Math.random().toString(36).slice(2, 12)); } catch (e) { return 'anon'; }
  }
  function count(channel, what) {
    try {
      var name = channel + '|' + what;
      if (W.LK && LK.event) LK.event('שיתוף ' + channel + ' ' + what);
      if (W.LK && LK.isAdminDevice && LK.isAdminDevice()) return;
      if (!/(^|\.)leokmei\.com$/.test(location.hostname)) return;
      var api = (W.LK && LK.cfg && LK.cfg.api) || ''; if (!api) return;
      var body = JSON.stringify({ ev: name, s: sid() }), url = api + '/stats/hit';
      if (navigator.sendBeacon) navigator.sendBeacon(url, new Blob([body], { type: 'text/plain;charset=UTF-8' }));
      else fetch(url, { method: 'POST', body: body, keepalive: true, headers: { 'content-type': 'text/plain;charset=UTF-8' } });
    } catch (e) { }
  }

  /* ---------------------------------------------------------------- התקנה כאפליקציה */
  var deferredInstall = null;
  W.addEventListener('beforeinstallprompt', function (e) { e.preventDefault(); deferredInstall = e; });
  W.addEventListener('appinstalled', function () { count('התקנה', 'אפליקציה'); deferredInstall = null; });
  function standalone() {
    try { return (W.matchMedia && W.matchMedia('(display-mode: standalone)').matches) || navigator.standalone === true; } catch (e) { return false; }
  }
  function isIos() { return /iPhone|iPad|iPod/i.test(navigator.userAgent) || (/Macintosh/.test(navigator.userAgent) && navigator.maxTouchPoints > 1); }
  function isMobile() { return /Android|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent) || (/Macintosh/.test(navigator.userAgent) && navigator.maxTouchPoints > 1); }

  /* ---------------------------------------------------------------- מקודד QR (גרסאות 1-14, מצב בתים) */
  var QR = (function () {
    var FMT = [1, 0, 3, 2];              /* L M Q H */
    function utf8(s) { return unescape(encodeURIComponent(s)).split('').map(function (c) { return c.charCodeAt(0); }); }
    function mul(x, y) { var z = 0; for (var i = 7; i >= 0; i--) { z = (z << 1) ^ ((z >>> 7) * 0x11D); z ^= ((y >>> i) & 1) * x; } return z; }
    function rsDiv(deg) {
      var r = []; for (var i = 0; i < deg; i++) r.push(0); r[deg - 1] = 1; var root = 1;
      for (i = 0; i < deg; i++) { for (var j = 0; j < deg; j++) { r[j] = mul(r[j], root); if (j + 1 < deg) r[j] ^= r[j + 1]; } root = mul(root, 2); }
      return r;
    }
    function rsRem(data, div) {
      var res = div.map(function () { return 0; });
      data.forEach(function (b) { var f = b ^ res.shift(); res.push(0); div.forEach(function (c, i) { res[i] ^= mul(c, f); }); });
      return res;
    }
    function groups(ver, lvl) {
      var row = RS[ver - 1][lvl], g = [];
      for (var i = 0; i < row.length; i += 3) g.push({ n: row[i], total: row[i + 1], data: row[i + 2] });
      return g;
    }
    function capBytes(ver, lvl) { var c = 0; groups(ver, lvl).forEach(function (g) { c += g.n * g.data; }); return c; }
    function pick(len) {
      var fb = null;
      for (var lvl = 3; lvl >= 0; lvl--) {
        for (var ver = 1; ver <= RS.length; ver++) {
          if (4 + (ver < 10 ? 8 : 16) + 8 * len <= capBytes(ver, lvl) * 8) { var r = { ver: ver, lvl: lvl }; if (ver <= 8) return r; fb = r; break; }
        }
      }
      return fb;
    }
    function alignPos(ver) {
      if (ver === 1) return [];
      var n = Math.floor(ver / 7) + 2, size = ver * 4 + 17;
      var step = ver === 32 ? 26 : Math.ceil((ver * 4 + 4) / (n * 2 - 2)) * 2, res = [6];
      for (var p = size - 7; res.length < n; p -= step) res.splice(1, 0, p);
      return res;
    }
    function encode(text) {
      var bytes = utf8(text), pk = pick(bytes.length);
      if (!pk) return null;
      var ver = pk.ver, lvl = pk.lvl, gs = groups(ver, lvl), dataCap = capBytes(ver, lvl), bits = [];
      function put(v, n) { for (var i = n - 1; i >= 0; i--) bits.push((v >>> i) & 1); }
      put(4, 4); put(bytes.length, ver < 10 ? 8 : 16); bytes.forEach(function (b) { put(b, 8); });
      put(0, Math.min(4, dataCap * 8 - bits.length));
      while (bits.length % 8) bits.push(0);
      for (var pad = 0xEC; bits.length < dataCap * 8; pad ^= 0xEC ^ 0x11) put(pad, 8);
      var cw = []; for (var i = 0; i < bits.length; i += 8) { var v = 0; for (var j = 0; j < 8; j++) v = (v << 1) | bits[i + j]; cw.push(v); }
      var blocks = [], pos = 0, ecLen = gs[0].total - gs[0].data;
      gs.forEach(function (g) { for (var b = 0; b < g.n; b++) { var d = cw.slice(pos, pos + g.data); pos += g.data; blocks.push({ d: d, e: rsRem(d, rsDiv(g.total - g.data)) }); } });
      var all = [], maxD = Math.max.apply(null, blocks.map(function (b) { return b.d.length; }));
      for (i = 0; i < maxD; i++) blocks.forEach(function (b) { if (i < b.d.length) all.push(b.d[i]); });
      for (i = 0; i < ecLen; i++) blocks.forEach(function (b) { all.push(b.e[i]); });
      var size = ver * 4 + 17, M = [], F = [];
      for (var y = 0; y < size; y++) { M.push([]); F.push([]); for (var x = 0; x < size; x++) { M[y].push(false); F[y].push(false); } }
      function set(x, y, d) { if (x < 0 || y < 0 || x >= size || y >= size) return; M[y][x] = !!d; F[y][x] = true; }
      for (i = 0; i < size; i++) { set(6, i, i % 2 === 0); set(i, 6, i % 2 === 0); }
      function finder(cx, cy) { for (var dy = -4; dy <= 4; dy++) for (var dx = -4; dx <= 4; dx++) { var d = Math.max(Math.abs(dx), Math.abs(dy)); set(cx + dx, cy + dy, d !== 2 && d !== 4); } }
      finder(3, 3); finder(size - 4, 3); finder(3, size - 4);
      var ap = alignPos(ver), last = ap.length - 1;
      for (i = 0; i <= last; i++) for (j = 0; j <= last; j++) {
        if ((i === 0 && j === 0) || (i === 0 && j === last) || (i === last && j === 0)) continue;
        for (dy = -2; dy <= 2; dy++) for (dx = -2; dx <= 2; dx++) set(ap[i] + dx, ap[j] + dy, Math.max(Math.abs(dx), Math.abs(dy)) !== 1);
      }
      var dy, dx, j;
      function drawFormat(mask) {
        var data = (FMT[lvl] << 3) | mask, rem = data;
        for (var k = 0; k < 10; k++) rem = (rem << 1) ^ ((rem >>> 9) * 0x537);
        var b = ((data << 10) | rem) ^ 0x5412, bit = function (n) { return (b >>> n) & 1; };
        for (k = 0; k <= 5; k++) set(8, k, bit(k));
        set(8, 7, bit(6)); set(8, 8, bit(7)); set(7, 8, bit(8));
        for (k = 9; k < 15; k++) set(14 - k, 8, bit(k));
        for (k = 0; k < 8; k++) set(size - 1 - k, 8, bit(k));
        for (k = 8; k < 15; k++) set(8, size - 15 + k, bit(k));
        set(8, size - 8, true);
      }
      drawFormat(0);
      if (ver >= 7) {
        var r = ver; for (i = 0; i < 12; i++) r = (r << 1) ^ ((r >>> 11) * 0x1F25);
        var vb = (ver << 12) | r;
        for (i = 0; i < 18; i++) { var bt = (vb >>> i) & 1, a = size - 11 + (i % 3), c = Math.floor(i / 3); set(a, c, bt); set(c, a, bt); }
      }
      var k2 = 0;
      for (var right = size - 1; right >= 1; right -= 2) {
        if (right === 6) right = 5;
        for (var vert = 0; vert < size; vert++) for (var jj = 0; jj < 2; jj++) {
          var xx = right - jj, up = ((right + 1) & 2) === 0, yy = up ? size - 1 - vert : vert;
          if (!F[yy][xx] && k2 < all.length * 8) { M[yy][xx] = ((all[k2 >>> 3] >>> (7 - (k2 & 7))) & 1) !== 0; k2++; }
        }
      }
      function inv(m, x, y) {
        switch (m) {
          case 0: return (x + y) % 2 === 0; case 1: return y % 2 === 0; case 2: return x % 3 === 0; case 3: return (x + y) % 3 === 0;
          case 4: return (Math.floor(x / 3) + Math.floor(y / 2)) % 2 === 0; case 5: return x * y % 2 + x * y % 3 === 0;
          case 6: return (x * y % 2 + x * y % 3) % 2 === 0; default: return ((x + y) % 2 + x * y % 3) % 2 === 0;
        }
      }
      function applyMask(m) { for (var y = 0; y < size; y++) for (var x = 0; x < size; x++) if (!F[y][x] && inv(m, x, y)) M[y][x] = !M[y][x]; }
      function penalty() {
        var p = 0, dark = 0, x, y, run, line;
        for (y = 0; y < size; y++) {
          run = 1; for (x = 1; x < size; x++) { if (M[y][x] === M[y][x - 1]) { run++; if (run === 5) p += 3; else if (run > 5) p++; } else run = 1; }
          run = 1; for (x = 1; x < size; x++) { if (M[x][y] === M[x - 1][y]) { run++; if (run === 5) p += 3; else if (run > 5) p++; } else run = 1; }
        }
        for (y = 0; y < size - 1; y++) for (x = 0; x < size - 1; x++) { var c = M[y][x]; if (c === M[y][x + 1] && c === M[y + 1][x] && c === M[y + 1][x + 1]) p += 3; }
        var pat = [1, 0, 1, 1, 1, 0, 1];
        for (y = 0; y < size; y++) for (x = 0; x <= size - 7; x++) {
          var okh = true, okv = true;
          for (var q = 0; q < 7; q++) { if ((M[y][x + q] ? 1 : 0) !== pat[q]) okh = false; if ((M[x + q][y] ? 1 : 0) !== pat[q]) okv = false; }
          if (okh) p += 40; if (okv) p += 40;
        }
        for (y = 0; y < size; y++) for (x = 0; x < size; x++) if (M[y][x]) dark++;
        p += Math.floor(Math.abs(dark * 20 - size * size * 10) / (size * size)) * 10;
        return p;
      }
      var bestM = 0, bestP = Infinity;
      for (var m = 0; m < 8; m++) { applyMask(m); drawFormat(m); var pp = penalty(); if (pp < bestP) { bestP = pp; bestM = m; } applyMask(m); }
      applyMask(bestM); drawFormat(bestM);
      return { size: size, mod: M, lvl: lvl, ver: ver };
    }
    return { encode: encode };
  })();

  /* מצייר את ה-QR על קנבס: כחול קטיפה על לבן, עם הל' הזהובה במרכז (רק כשיש מספיק תיקון שגיאות) */
  function drawQr(canvas, url, px) {
    var q = QR.encode(url); if (!q) return false;
    var quiet = 4, n = q.size + quiet * 2, sc = Math.max(2, Math.floor(px / n)), W0 = sc * n;
    canvas.width = canvas.height = W0;
    var c = canvas.getContext('2d');
    c.fillStyle = '#fff'; c.fillRect(0, 0, W0, W0);
    c.fillStyle = '#0b1c2a';
    for (var y = 0; y < q.size; y++) for (var x = 0; x < q.size; x++) if (q.mod[y][x]) c.fillRect((x + quiet) * sc, (y + quiet) * sc, sc, sc);
    if (q.lvl >= 2 && LAMED_D && W.Path2D) {
      var box = Math.round(q.size * 0.22) * sc, bx = Math.round((W0 - box) / 2), pad = sc;
      c.fillStyle = '#fff'; c.fillRect(bx - pad, bx - pad, box + 2 * pad, box + 2 * pad);
      c.fillStyle = '#0b1c2a'; c.fillRect(bx, bx, box, box);
      c.save(); c.translate(bx, bx); c.scale(box / 512, box / 512);
      var g = c.createLinearGradient(0, 120, 0, 400); g.addColorStop(0, '#fbe7a1'); g.addColorStop(.5, '#d9a93c'); g.addColorStop(1, '#b07c1f');
      c.fillStyle = g; c.fill(new Path2D(LAMED_D)); c.restore();
    }
    return true;
  }

  /* ---------------------------------------------------------------- החלונית */
  var CSS = '.lksh{position:fixed;inset:0;z-index:2147483000;display:flex;align-items:center;justify-content:center;background:rgba(3,10,16,.62);padding:12px;direction:rtl}' +
    '.lksh *{box-sizing:border-box}' +
    '.lksh-box{width:min(420px,100%);max-height:calc(100vh - 24px);overflow:auto;background:radial-gradient(ellipse 90% 60% at 50% 0,#173a58,#0b1c2a 62%,#081624);color:#f5edd6;' +
    'border:1px solid #b8892a;border-radius:6px;box-shadow:0 0 0 4px #0b1c2a,0 0 0 5px rgba(209,162,58,.55),0 18px 48px rgba(0,0,0,.6);padding:16px 18px 14px;font:16px/1.5 "Frank Ruhl Libre",Frank,serif;outline:0}' +
    '.lksh-h{display:flex;align-items:center;justify-content:space-between;gap:10px}' +
    '.lksh-h h2{margin:0;font:400 26px/1.2 LGVilnaXB,"Frank Ruhl Libre",serif;background:linear-gradient(170deg,#fbe7a1,#e6bd52 35%,#c38f2a 60%,#efcf6b);-webkit-background-clip:text;background-clip:text;color:transparent}' +
    '.lksh-x{background:none;border:0;color:#e9c35a;font-size:28px;line-height:1;cursor:pointer;padding:2px 8px;min-width:44px;min-height:44px}' +
    '.lksh-msg{margin:8px 0 12px;padding:8px 10px;border:1px solid rgba(209,162,58,.4);border-radius:4px;background:rgba(0,0,0,.25);font-size:15px;color:#e8dfc4;word-break:break-word}' +
    '.lksh-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}' +
    '.lksh-b{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:6px;min-height:76px;padding:8px 4px;border:1px solid #8f6a1e;border-radius:6px;background:rgba(16,42,66,.7);' +
    'color:#f9e08a;text-decoration:none;font:600 15px/1.2 "Frank Ruhl Libre",Frank,serif;cursor:pointer}' +
    '.lksh-b:hover,.lksh-b:focus-visible{background:#173a58;border-color:#e9c35a;outline:0;box-shadow:0 0 0 2px rgba(233,195,90,.45)}' +
    '.lksh-b svg{width:26px;height:26px;fill:none;stroke:#e9c35a;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round}' +
    '.lksh-ok{color:#9be3a5!important;border-color:#4e9b5a!important}' +
    '.lksh-qr{text-align:center;margin-top:12px}.lksh-qr canvas{width:min(260px,100%);height:auto;background:#fff;border-radius:4px;padding:0}' +
    '.lksh-row{display:flex;gap:8px;justify-content:center;margin-top:10px;flex-wrap:wrap}' +
    '.lksh-btn{min-height:44px;padding:8px 16px;border-radius:6px;border:1px solid #8f6a1e;background:linear-gradient(180deg,#fbe9a6,#eccb63 38%,#c8942c 62%,#b98522);color:#2a1c04;font:700 15px "Frank Ruhl Libre",Frank,serif;cursor:pointer}' +
    '.lksh-btn.g{background:transparent;color:#f9e08a}' +
    '.lksh-inst{margin-top:12px;padding-top:10px;border-top:1px solid rgba(209,162,58,.35);font-size:14px;color:#d8cfb3}' +
    '.lksh-inst button{background:none;border:0;color:#f9e08a;font:700 15px "Frank Ruhl Libre",Frank,serif;text-decoration:underline;cursor:pointer;padding:6px 0;min-height:36px}' +
    '.lk-sh-btn{cursor:pointer}' +
    '@media print{.lksh,.lk-sh-btn,#lkshbtn{display:none!important}}body.ed #lkshbtn{display:none!important}';
  function injectCss() {
    if (D.getElementById('lksh-css')) return;
    var s = D.createElement('style'); s.id = 'lksh-css'; s.textContent = CSS; (D.head || D.documentElement).appendChild(s);
  }
  var ICON = {
    wa: '<path d="M4 20l1.3-4.2A8 8 0 1 1 8.4 18.8z"/><path d="M9 9.5c.4 2.2 2.3 4.1 4.5 4.6l1.4-1.2-1.8-1-.8.7c-.8-.3-1.700-1.200-2-2l.7-.8-1-1.800z"/>',
    sms: '<path d="M4 5h16v11H9l-5 4z"/><path d="M8.500 10h.01M12 10h.01M15.500 10h.01"/>',
    mail: '<rect x="3.500" y="5.500" width="17" height="13" rx="1.500"/><path d="M4 7l8 6 8-6"/>',
    tg: '<path d="M20.500 4L3.500 11l5.500 2 2 6 3-4 4.500 3z"/><path d="M9 13l8-6"/>',
    copy: '<rect x="8" y="8" width="11" height="12" rx="1.500"/><path d="M5 15V5a1 1 0 0 1 1-1h9"/>',
    qr: '<rect x="4" y="4" width="6" height="6"/><rect x="14" y="4" width="6" height="6"/><rect x="4" y="14" width="6" height="6"/><path d="M14 14h2.500v2.500H14zM19 14v6M14 19.500h2.500"/>'
  };
  function ic(n) { return '<svg viewBox="0 0 24 24" aria-hidden="true">' + ICON[n] + '</svg>'; }

  var openEl = null, lastFocus = null;
  function close() {
    if (!openEl) return;
    D.removeEventListener('keydown', onKey, true);
    openEl.remove(); openEl = null;
    try { if (lastFocus && lastFocus.focus) lastFocus.focus(); } catch (e) { }
  }
  function onKey(e) {
    if (!openEl) return;
    if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); close(); return; }
    if (e.key === 'Tab') {
      var f = [].slice.call(openEl.querySelectorAll('a[href],button:not([hidden])')).filter(function (x) { return x.offsetParent !== null; });
      if (!f.length) return;
      var first = f[0], last = f[f.length - 1];
      if (e.shiftKey && D.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && D.activeElement === last) { e.preventDefault(); first.focus(); }
    }
  }
  function copyText(t) {
    if (navigator.clipboard && W.isSecureContext) return navigator.clipboard.writeText(t);
    return new Promise(function (res, rej) {
      try {
        var a = D.createElement('textarea'); a.value = t; a.setAttribute('readonly', ''); a.style.cssText = 'position:fixed;top:-999px;opacity:0';
        D.body.appendChild(a); a.select(); var ok = D.execCommand('copy'); a.remove(); ok ? res() : rej();
      } catch (e) { rej(e); }
    });
  }

  function open(o) {
    injectCss(); close();
    lastFocus = D.activeElement;
    var url = o.url, text = o.text, kind = o.kind || 'אתר', body = text + '\n' + url;
    var enc = encodeURIComponent;
    var links = [
      { ch: 'ווטסאפ', ic: 'wa', href: 'https://wa.me/?text=' + enc(body), ext: true },
      isMobile() ? { ch: 'הודעה', ic: 'sms', href: 'sms:?&body=' + enc(body) } : null,
      { ch: 'מייל', ic: 'mail', href: 'mailto:?subject=' + enc(text.slice(0, 120)) + '&body=' + enc(body) },
      { ch: 'טלגרם', ic: 'tg', href: 'https://t.me/share/url?url=' + enc(url) + '&text=' + enc(text), ext: true }
    ].filter(Boolean);
    var wrap = D.createElement('div'); wrap.className = 'lksh'; wrap.id = 'lksh';
    wrap.innerHTML = '<div class="lksh-box" role="dialog" aria-modal="true" aria-labelledby="lksh-t" tabindex="-1">' +
      '<div class="lksh-h"><h2 id="lksh-t">' + esc(o.title || 'שיתוף') + '</h2><button type="button" class="lksh-x" aria-label="סגור">×</button></div>' +
      '<p class="lksh-msg" dir="rtl">' + esc(text) + '</p>' +
      '<div class="lksh-grid">' +
      links.map(function (l) { return '<a class="lksh-b" data-ch="' + esc(l.ch) + '" href="' + esc(l.href) + '"' + (l.ext ? ' target="_blank" rel="noopener noreferrer"' : '') + '>' + ic(l.ic) + '<span>' + l.ch + '</span></a>'; }).join('') +
      '<button type="button" class="lksh-b" data-ch="העתקה">' + ic('copy') + '<span>העתק קישור</span></button>' +
      '<button type="button" class="lksh-b" data-ch="QR">' + ic('qr') + '<span>קוד QR</span></button>' +
      '</div>' +
      '<div class="lksh-qr" hidden><canvas width="10" height="10" role="img" aria-label="קוד QR של הקישור"></canvas>' +
      '<div class="lksh-row"><button type="button" class="lksh-btn" data-a="dl">הורד כתמונה</button><button type="button" class="lksh-btn g" data-a="back">חזרה</button></div></div>' +
      '<div class="lksh-inst" hidden></div>' +
      '<div class="lksh-row"><button type="button" class="lksh-btn g" data-a="close">סגור</button></div></div>';
    D.body.appendChild(wrap); openEl = wrap;
    var box = wrap.querySelector('.lksh-box');
    wrap.addEventListener('mousedown', function (e) { if (e.target === wrap) close(); });
    wrap.addEventListener('click', function (e) {
      var t = e.target.closest('[data-ch],[data-a],.lksh-x'); if (!t) return;
      if (t.classList.contains('lksh-x') || t.getAttribute('data-a') === 'close') { close(); return; }
      var ch = t.getAttribute('data-ch'), a = t.getAttribute('data-a');
      if (a === 'back') { wrap.querySelector('.lksh-qr').hidden = true; wrap.querySelector('.lksh-grid').hidden = false; return; }
      if (a === 'dl') {
        var cv = wrap.querySelector('canvas'); drawQr(cv, url, 1024);
        cv.toBlob(function (b) {
          if (!b) return;
          var u = URL.createObjectURL(b), l = D.createElement('a'); l.href = u; l.download = 'leokmei-qr.png'; D.body.appendChild(l); l.click();
          setTimeout(function () { URL.revokeObjectURL(u); l.remove(); drawQr(cv, url, 520); }, 800);
        }, 'image/png');
        count('הורדת QR', kind); return;
      }
      if (ch === 'העתקה') {
        copyText(url).then(function () {
          var s = t.querySelector('span'); t.classList.add('lksh-ok'); s.textContent = 'הקישור הועתק';
          setTimeout(function () { t.classList.remove('lksh-ok'); s.textContent = 'העתק קישור'; }, 1800);
        }, function () { var s = t.querySelector('span'); s.textContent = 'ההעתקה נחסמה'; });
        count('העתקה', kind); return;
      }
      if (ch === 'QR') {
        var qr = wrap.querySelector('.lksh-qr');
        if (!drawQr(qr.querySelector('canvas'), url, 520)) { t.querySelector('span').textContent = 'הקישור ארוך מדי'; return; }
        wrap.querySelector('.lksh-grid').hidden = true; qr.hidden = false; count('QR', kind);
        qr.querySelector('button').focus(); return;
      }
      if (ch) count(ch, kind);          /* קישור פשוט: ממשיך לפתוח את היעד */
    });
    var inst = wrap.querySelector('.lksh-inst');
    if (!standalone()) {
      if (deferredInstall) {
        inst.hidden = false; inst.innerHTML = '<button type="button" data-a="inst">התקן כאפליקציה</button>';
        inst.querySelector('button').onclick = function () {
          var d = deferredInstall; if (!d) return;
          d.prompt(); d.userChoice.then(function () { deferredInstall = null; close(); }, function () { });
        };
      } else if (isIos()) {
        inst.hidden = false; inst.innerHTML = 'להתקנה כאפליקציה: לחץ על כפתור השיתוף של ספארי ובחר \'הוסף למסך הבית\'.';
      }
    }
    D.addEventListener('keydown', onKey, true);
    var f = box.querySelector('.lksh-b'); (f || box).focus();
    return wrap;
  }

  W.LKShare = {
    open: open, close: close,
    site: function () { return open(API.site()); },
    page: function () { return open(API.page()); },
    tos: function (o) { return open(API.tos(o)); },
    quiz: function (o) { return open(API.quiz(o)); },
    qr: { encode: QR.encode, draw: drawQr },
    dafPath: dafPath
  };
})();
