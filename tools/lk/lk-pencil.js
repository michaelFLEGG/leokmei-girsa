/* lk-pencil.js - עיפרון המנהל לעריכת טקסטי האתר (8.10.2026).
   נטען על ידי lk-core.js רק במכשיר שיש בו אסימון מנהל (lg-adm). הגולש הרגיל
   לא מקבל את הקובץ הזה בכלל, וגם אילו קיבל, השרת דוחה כל שמירה בלי מפתח תקף.
   עריכת טקסט בלבד. קיצור: Ctrl+Alt+P. ראו docs/TEXTS.md. */
(function () {
  'use strict';
  var LK = window.LK, D = document, W = window;
  if (!LK || window.LKP) return;
  var API = LK.cfg.api;
  var P = window.LKP = { on: false };
  function adm() { try { return localStorage.getItem('lg-adm') || ''; } catch (e) { return ''; } }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }

  var CSS = '' +
    '.lk-ui{font-family:Assistant,"Noto Sans Hebrew",system-ui,sans-serif;direction:rtl;box-sizing:border-box}' +
    '.lk-ui *{box-sizing:border-box}' +
    '#lk-fab{position:fixed;left:14px;bottom:84px;z-index:2147483000;display:flex;flex-direction:column;gap:8px;align-items:center}' +
    '#lk-fab button{width:46px;height:46px;border-radius:50%;border:2px solid #c9a24a;background:#0b1c2a;color:#e5c26b;cursor:pointer;display:flex;align-items:center;justify-content:center;box-shadow:0 4px 14px rgba(0,0,0,.35);padding:0;font-size:22px;line-height:1}' +
    '#lk-fab button.sm{width:34px;height:34px;font-size:18px}' +
    '#lk-fab button:hover{background:#13304a}' +
    '#lk-fab button.on{background:#c9a24a;color:#0b1c2a}' +
    '#lk-fab svg{width:22px;height:22px;fill:currentColor;pointer-events:none}' +
    '#lk-bar{position:fixed;top:0;left:0;right:0;z-index:2147483001;background:#c9a24a;color:#0b1c2a;text-align:center;font-weight:700;font-size:14px;padding:3px 8px;height:24px;line-height:18px}' +
    'body.lk-pencil{padding-top:0}' +
    '#lk-menu{position:fixed;left:68px;bottom:84px;z-index:2147483002;background:#0b1c2a;color:#f2e7c9;border:1px solid #c9a24a;border-radius:8px;padding:6px;min-width:210px;box-shadow:0 6px 22px rgba(0,0,0,.4)}' +
    '#lk-menu button,#lk-menu a{display:block;width:100%;text-align:right;background:none;border:0;color:inherit;font:inherit;font-size:15px;padding:8px 10px;cursor:pointer;border-radius:5px;text-decoration:none}' +
    '#lk-menu button:hover,#lk-menu a:hover{background:rgba(201,162,74,.22)}' +
    'body.lk-pencil .lk-hot{outline:1.5px dashed #c9a24a;outline-offset:2px;cursor:text;background:rgba(201,162,74,.10)}' +
    '.lk-ed{outline:2px solid #c9a24a;outline-offset:2px;background:#fff8dc!important;background-image:none!important;color:#111!important;-webkit-text-fill-color:#111!important;text-shadow:none!important;-webkit-background-clip:border-box!important;background-clip:border-box!important;border-radius:3px;padding:0 3px;min-width:1ch;white-space:pre-wrap;display:inline;cursor:text}' +
    '.lk-tok{display:inline-block;background:#d8d2c0;color:#555;border-radius:4px;padding:0 4px;margin:0 1px;user-select:none;font-size:.92em}' +
    '#lk-pop{position:absolute;z-index:2147483003;background:#0b1c2a;color:#f2e7c9;border:1px solid #c9a24a;border-radius:6px;padding:3px 6px;font-size:13px;display:flex;gap:8px;align-items:center;white-space:nowrap}' +
    '#lk-pop button{background:none;border:0;color:#e5c26b;cursor:pointer;font:inherit;font-size:13px;text-decoration:underline;padding:0}' +
    '#lk-toast{position:fixed;left:50%;transform:translateX(-50%);bottom:26px;z-index:2147483005;background:#0b1c2a;color:#f2e7c9;border:1px solid #c9a24a;border-radius:8px;padding:9px 16px;font-size:15px;max-width:90vw;text-align:center}' +
    '#lk-side{position:fixed;top:0;bottom:0;left:0;width:min(380px,92vw);z-index:2147483004;background:#fbf8f1;color:#222;border-right:2px solid #c9a24a;overflow:auto;padding:12px 14px 40px;box-shadow:4px 0 22px rgba(0,0,0,.3)}' +
    '#lk-side h3{margin:2px 0 8px;font-size:17px;color:#0b1c2a}' +
    '#lk-side .row{border-bottom:1px solid #e0d8c4;padding:8px 0}' +
    '#lk-side .lb{font-size:12px;color:#7a6a45;margin-bottom:3px}' +
    '#lk-side textarea{width:100%;min-height:54px;font:inherit;font-size:15px;border:1px solid #c9bfa8;border-radius:5px;padding:5px;background:#fff;color:#111;direction:rtl}' +
    '#lk-side .bt{display:flex;gap:6px;margin-top:4px}' +
    '#lk-side button{font:inherit;font-size:14px;border:1px solid #c9a24a;background:#0b1c2a;color:#e5c26b;border-radius:5px;padding:3px 10px;cursor:pointer}' +
    '#lk-side button.g{background:none;color:#0b1c2a}' +
    '#lk-side .x{position:absolute;top:8px;left:10px;border:0;background:none;font-size:22px;color:#0b1c2a;cursor:pointer}' +
    '@media (max-width:760px){#lk-fab{bottom:70px}#lk-menu{left:66px}}' +
    '@media print{.lk-ui{display:none!important}}';

  var ICON = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 17.25V21h3.75L17.8 9.94l-3.75-3.75L3 17.25zM20.7 7.04a1 1 0 0 0 0-1.41l-2.34-2.34a1 1 0 0 0-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/></svg>';

  var fab, bar, menu, side, pop, toastT;
  function toast(msg, ms) {
    var t = D.getElementById('lk-toast'); if (t) t.remove();
    t = D.createElement('div'); t.id = 'lk-toast'; t.className = 'lk-ui'; t.textContent = msg; D.documentElement.appendChild(t);
    clearTimeout(toastT); toastT = setTimeout(function () { t.remove(); }, ms || 3200);
  }
  function api(path, method, body) {
    return fetch(API + path, {
      method: method || 'GET', headers: { 'content-type': 'application/json', 'x-admin-key': adm() },
      body: body ? JSON.stringify(body) : undefined, cache: 'no-store'
    }).then(function (r) { return r.json().then(function (j) { j._status = r.status; return j; }); });
  }
  function refresh() {
    return fetch(API + '/tx?_=' + Date.now(), { cache: 'no-store' }).then(function (r) { return r.json(); })
      .then(function (d) { if (d && d.ok) LK.reapply(d.items, d.rev); });
  }

  /* ------------------------------------------------------------ חילוץ יחידות */
  function isContent(el) { try { return !!el.closest(LK.CONTENT); } catch (e) { return false; } }
  function skipEl(el) { try { return !!el.closest(LK.SKIP); } catch (e) { return true; } }
  /* ------------------------------------------------------------ הפעלה וכיבוי */
  function setOn(on) {
    if (on && D.body.classList.contains('ed')) { toast('סגור קודם את מצב עריכת הגמרא'); return; }
    P.on = on;
    D.body.classList.toggle('lk-pencil', on);
    fab.querySelector('#lk-pb').classList.toggle('on', on);
    if (on) {
      bar = D.createElement('div'); bar.id = 'lk-bar'; bar.className = 'lk-ui'; bar.textContent = 'מצב עריכת טקסטים, Esc ליציאה'; D.documentElement.appendChild(bar);
      D.addEventListener('mouseover', hover, true);
      D.addEventListener('click', clickBlock, true);
      D.addEventListener('auxclick', stopAll, true);
      D.addEventListener('submit', stopAll, true);
      closeMenu();
    } else {
      cancelEdit(); if (bar) bar.remove();
      D.removeEventListener('mouseover', hover, true);
      D.removeEventListener('click', clickBlock, true);
      D.removeEventListener('auxclick', stopAll, true);
      D.removeEventListener('submit', stopAll, true);
      clearHot();
    }
  }
  function stopAll(e) {
    if (e.target.closest && e.target.closest('.lk-ui')) return;
    e.preventDefault(); e.stopPropagation(); e.stopImmediatePropagation();
  }
  var hotEl = null;
  function clearHot() { if (hotEl) { hotEl.classList.remove('lk-hot'); hotEl = null; } }
  function textNodeAt(el, x, y) {
    /* הצומת הטקסטואלי הקרוב לנקודה, בתוך האלמנט */
    var best = null, tw = D.createTreeWalker(el, NodeFilter.SHOW_TEXT, null), n;
    while ((n = tw.nextNode())) {
      if (!/[א-ת]/.test(n.nodeValue)) continue;
      var r = D.createRange(); r.selectNodeContents(n);
      var rects = r.getClientRects();
      for (var i = 0; i < rects.length; i++) {
        var q = rects[i];
        if (x >= q.left - 2 && x <= q.right + 2 && y >= q.top - 2 && y <= q.bottom + 2) return n;
      }
      if (!best) best = n;
    }
    return best;
  }
  function targetOf(e) {
    var t = e.target; if (!t || t.nodeType !== 1) return null;
    if (t.closest('.lk-ui')) return null;
    return t;
  }
  function hover(e) {
    var t = targetOf(e); clearHot(); if (!t || editingNode) return;
    if (isContent(t) || skipEl(t)) return;
    var n = textNodeAt(t, e.clientX, e.clientY); if (!n || n.parentNode !== t && !t.contains(n)) return;
    hotEl = n.parentNode; hotEl.classList.add('lk-hot');
  }
  function clickBlock(e) {
    var t = targetOf(e); if (!t) return;
    if (e.target.closest && e.target.closest('.lk-ed,#lk-pop')) return;
    e.preventDefault(); e.stopPropagation(); e.stopImmediatePropagation();
    if (editingNode) { commit(); }
    var pt = LK.pageType().type;
    if (pt === 'admin' || pt === 'admin-texts') { toast('במסכי המנהל מוצגים נתוני משתמשים, ולכן הם אינם נערכים בעיפרון'); return; }
    if (isContent(t)) { toast(t.closest('.qz-card,.lm-shiur,.lm-sug') ? 'זה תוכן של שאלה או של משתמש, ואינו נערך כאן' : 'זה תוכן הגמרא, ערוך אותו במצב העריכה הרגיל'); return; }
    if (skipEl(t)) return;
    var n = textNodeAt(t, e.clientX, e.clientY);
    if (!n || !/[א-ת]/.test(n.nodeValue)) return;
    if (n.parentNode.closest('[data-lk-user]')) { toast('זה תוכן שכתב משתמש, ואינו נערך כאן'); return; }
    startEdit(n);
  }

  /* ------------------------------------------------------------ עריכה במקום */
  var editingNode = null, edSpan = null, edInfo = null;
  function toChips(text) {
    var out = '', last = 0, re = /\d+(?:[.,:]\d+)*/g, m;
    while ((m = re.exec(text))) {
      out += esc(text.slice(last, m.index)) + '<span class="lk-tok" contenteditable="false" data-n="' + esc(m[0]) + '">' + esc(m[0]) + '</span>';
      last = m.index + m[0].length;
    }
    return out + esc(text.slice(last));
  }
  function serialize(span) {
    var out = '';
    (function walk(n) {
      for (var c = n.firstChild; c; c = c.nextSibling) {
        if (c.nodeType === 3) out += c.nodeValue;
        else if (c.nodeType === 1) { if (c.classList.contains('lk-tok')) out += '{n}'; else if (c.tagName === 'BR') out += '\n'; else walk(c); }
      }
    })(span);
    return out;
  }
  function startEdit(tn) {
    cancelEdit();
    var rec = LK.appliedOf ? LK.appliedOf(tn) : null;
    var base = rec ? rec.orig : tn.nodeValue;
    var tk = LK.tokenize(base);
    var scope = LK.scopeOf(tn.parentNode);
    var key = LK.keyFor(scope, tk.t);
    var shown = tn.nodeValue;
    var long = shown.length > 70 || /\n/.test(shown);
    var span = D.createElement('span'); span.className = 'lk-ed lk-ui'; span.setAttribute('contenteditable', 'plaintext-only');
    if (span.contentEditable !== 'plaintext-only') span.setAttribute('contenteditable', 'true');
    span.innerHTML = toChips(shown.replace(/^\s+|\s+$/g, ''));
    var lead = (shown.match(/^\s+/) || [''])[0], trail = (shown.match(/\s+$/) || [''])[0];
    tn.parentNode.insertBefore(span, tn); tn.parentNode.removeChild(tn);
    editingNode = tn; edSpan = span; edInfo = { key: key, scope: scope, orig: tk.t, base: base, long: long, lead: lead, trail: trail, shown: shown };
    clearHot();
    span.addEventListener('keydown', function (ev) {
      ev.stopPropagation();
      if (ev.key === 'Escape') { ev.preventDefault(); cancelEdit(); }
      else if (ev.key === 'Enter') {
        if (ev.shiftKey && edInfo.long) return;
        ev.preventDefault(); commit();
      }
    });
    span.addEventListener('paste', function (ev) {
      ev.preventDefault();
      var t = (ev.clipboardData || W.clipboardData).getData('text').replace(/\s*\n\s*/g, ' ');
      D.execCommand('insertText', false, t);
    });
    span.focus();
    var rg = D.createRange(); rg.selectNodeContents(span); rg.collapse(false);
    var sel = W.getSelection(); sel.removeAllRanges(); sel.addRange(rg);
    showPop(span, key);
  }
  function showPop(span, key) {
    if (pop) pop.remove();
    var changed = LK.tx && LK.tx.items && LK.tx.items[key];
    if (!changed) return;
    pop = D.createElement('div'); pop.id = 'lk-pop'; pop.className = 'lk-ui';
    pop.innerHTML = '<span>שונה</span><button type="button">החזר לנוסח המקורי</button>';
    var r = span.getBoundingClientRect();
    pop.style.top = (W.scrollY + r.bottom + 4) + 'px'; pop.style.left = Math.max(6, W.scrollX + r.left) + 'px';
    D.documentElement.appendChild(pop);
    pop.querySelector('button').onclick = function (ev) { ev.stopPropagation(); revertKey(key); };
  }
  function restoreNode(text) {
    var tn = D.createTextNode(text);
    if (edSpan && edSpan.parentNode) { edSpan.parentNode.insertBefore(tn, edSpan); edSpan.parentNode.removeChild(edSpan); }
    if (pop) { pop.remove(); pop = null; }
    var info = edInfo; editingNode = null; edSpan = null; edInfo = null;
    return { node: tn, info: info };
  }
  function cancelEdit() {
    if (!editingNode) return;
    var shown = edInfo.shown;
    var r = restoreNode(shown);
    if (LK.registerApplied && r.info && r.info.base !== shown) LK.registerApplied(r.node, r.info.base, shown);
  }
  function commit() {
    if (!editingNode) return;
    var info = edInfo, raw = serialize(edSpan).replace(/ /g, ' ');
    var text = raw.replace(/[ \t]+\n/g, '\n').trim();
    function done(finalShown) {
      var r = restoreNode(info.lead + finalShown + info.trail);
      if (LK.registerApplied && info.base !== r.node.nodeValue) LK.registerApplied(r.node, info.base, r.node.nodeValue);
    }
    if (text === LK.norm(info.shown) || text === info.shown.trim()) { done(info.shown.trim()); return; }
    var hide = false;
    if (!text) {
      if (!W.confirm('להסתיר את הטקסט הזה?')) { done(info.shown.trim()); return; }
      hide = true;
    }
    var shownNow = info.shown.trim();
    done(shownNow);
    api('/tx/save', 'POST', { key: info.key, scope: info.scope, orig: info.orig, text: text, hide: hide, kind: 'text' }).then(function (j) {
      if (!j.ok) { toast(j.error || 'השמירה נכשלה'); return; }
      toast(j.cleaned ? 'נשמר. הטקסט נוקה מתגיות או ממקפים ארוכים' : (hide ? 'הטקסט הוסתר' : 'נשמר'));
      return refresh();
    }).catch(function () { toast('השמירה נכשלה: אין חיבור לשרת'); });
  }
  function revertKey(key) {
    cancelEdit();
    api('/tx/revert', 'POST', { key: key }).then(function (j) {
      if (!j.ok) { toast(j.error || 'ההחזרה נכשלה'); return; }
      toast('הוחזר לנוסח המקורי'); return refresh().then(function () { if (side) openSide(); });
    }).catch(function () { toast('ההחזרה נכשלה'); });
  }

  /* ------------------------------------------------------------ חלונית צד: טקסטים נסתרים */
  function gather() {
    var rows = [], seen = {};
    function add(scope, kind, shown, label) {
      var tk = LK.tokenize(shown); if (!tk.t || !/[א-ת]/.test(tk.t)) return;
      var rec = null;
      var k = LK.keyFor(scope, kind + ':' + tk.t);
      if (seen[k]) return; seen[k] = 1;
      rows.push({ key: k, scope: scope, kind: kind, shown: shown, orig: tk.t, label: label });
    }
    var cur = D.title, m = D.querySelector('meta[name="description"]');
    var pg = LK.pageType().type;
    var dt = (LK.metaOrig && LK.metaOrig.title) || D.title;
    add(pg, 'doctitle', dt, 'כותרת הדף (title)');
    if (m) add(pg, 'metadesc', (LK.metaOrig && LK.metaOrig.desc) || m.getAttribute('content') || '', 'תיאור הדף לגוגל');
    var attrs = { 'title': 'טקסט ריחוף', 'aria-label': 'תווית נגישות', 'placeholder': 'טקסט בשדה', 'alt': 'תיאור תמונה' };
    var els = D.querySelectorAll('[title],[aria-label],[placeholder],[alt]');
    for (var i = 0; i < els.length; i++) {
      var el = els[i]; if (el.closest('.lk-ui') || isContent(el)) continue;
      for (var a in attrs) {
        var v = el.getAttribute(a); if (!v) continue;
        var base = LK.attrOrig ? LK.attrOrig(el, a, v) : v;
        add(LK.scopeOf(el), a, base, attrs[a]);
      }
    }
    return rows;
  }
  function closeSide() { if (side) { side.remove(); side = null; } }
  function openSide() {
    closeSide(); closeMenu();
    side = D.createElement('div'); side.id = 'lk-side'; side.className = 'lk-ui';
    var rows = gather(), items = (LK.tx && LK.tx.items) || {};
    var h = '<button class="x" type="button" aria-label="סגירה">×</button><h3>טקסטים נסתרים בדף זה</h3><div class="lb">כותרת הדף, תיאור לגוגל וטקסטי ריחוף. לחץ שמור כדי לפרסם.</div>';
    rows.forEach(function (r, i) {
      var it = items[r.key]; var cur = it ? (it.h ? '' : it.t) : r.orig;
      h += '<div class="row" data-i="' + i + '"><div class="lb">' + esc(r.label) + (it ? ' · שונה' : '') + '</div>' +
        '<textarea>' + esc(it ? cur : r.shown) + '</textarea><div class="bt"><button type="button" class="sv">שמור</button>' +
        (it ? '<button type="button" class="g rv">החזר לנוסח המקורי</button>' : '') + '</div></div>';
    });
    if (!rows.length) h += '<div class="lb">אין כאן טקסטים נסתרים.</div>';
    side.innerHTML = h; D.documentElement.appendChild(side);
    side.querySelector('.x').onclick = closeSide;
    [].forEach.call(side.querySelectorAll('.row'), function (row) {
      var r = rows[+row.getAttribute('data-i')];
      row.querySelector('.sv').onclick = function () {
        var text = row.querySelector('textarea').value.trim();
        var hide = false;
        if (!text) { if (!W.confirm('להסתיר את הטקסט הזה?')) return; hide = true; }
        api('/tx/save', 'POST', { key: r.key, scope: r.scope, orig: r.orig, text: text, hide: hide, kind: r.kind }).then(function (j) {
          if (!j.ok) { toast(j.error || 'השמירה נכשלה'); return; }
          toast('נשמר'); return refresh().then(openSide);
        });
      };
      var rv = row.querySelector('.rv'); if (rv) rv.onclick = function () { revertKey(r.key); };
    });
  }

  /* ------------------------------------------------------------ תפריט */
  function closeMenu() { if (menu) { menu.remove(); menu = null; } }
  function openMenu() {
    if (menu) { closeMenu(); return; }
    menu = D.createElement('div'); menu.id = 'lk-menu'; menu.className = 'lk-ui';
    var cfg = LK.cfg;
    menu.innerHTML = '<button type="button" data-a="pencil">עריכת טקסטי האתר (Ctrl+Alt+P)</button>' +
      '<button type="button" data-a="hidden">טקסטים נסתרים בדף זה</button>' +
      '<a href="/admin-texts.html">טקסטים ששיניתי</a>' +
      '<button type="button" data-a="stats">נתוני גלישה</button>';
    D.documentElement.appendChild(menu);
    menu.onclick = function (e) {
      var b = e.target.closest('button'); if (!b) return;
      var a = b.getAttribute('data-a');
      if (a === 'pencil') setOn(!P.on);
      else if (a === 'hidden') openSide();
      else if (a === 'stats') { LK.openStats(); closeMenu(); }
    };
  }
  LK.openStats = function () {
    var c = LK.cfg;
    W.open(c.cfDash || 'https://dash.cloudflare.com/?to=/:account/web-analytics', '_blank', 'noopener');
    W.open(c.clarityDash || 'https://clarity.microsoft.com/', '_blank', 'noopener');
  };

  function build() {
    var st = D.createElement('style'); st.textContent = CSS; D.head.appendChild(st);
    fab = D.createElement('div'); fab.id = 'lk-fab'; fab.className = 'lk-ui';
    fab.innerHTML = '<button class="sm" id="lk-mb" type="button" title="תפריט המנהל: טקסטים ונתוני גלישה" aria-label="תפריט המנהל">⋯</button>' +
      '<button id="lk-pb" type="button" title="עריכת טקסטי האתר (Ctrl+Alt+P)" aria-label="עריכת טקסטי האתר">' + ICON + '</button>';
    D.documentElement.appendChild(fab);
    fab.querySelector('#lk-pb').onclick = function () { setOn(!P.on); };
    fab.querySelector('#lk-mb').onclick = function (e) { e.stopPropagation(); openMenu(); };
    D.addEventListener('click', function (e) { if (menu && !e.target.closest('#lk-menu,#lk-fab')) closeMenu(); });
    D.addEventListener('keydown', function (e) {
      if (e.ctrlKey && e.altKey && !e.shiftKey && e.code === 'KeyP') { e.preventDefault(); setOn(!P.on); return; }
      if (e.key === 'Escape' && !editingNode) { if (side) closeSide(); else if (P.on) setOn(false); }
    }, true);
    /* אם נכנסים למצב עריכת גמרא בזמן שהעיפרון פעיל, העיפרון נסגר */
    new MutationObserver(function () { if (P.on && D.body.classList.contains('ed')) setOn(false); }).observe(D.body, { attributes: true, attributeFilter: ['class'] });
  }
  if (D.body) build(); else D.addEventListener('DOMContentLoaded', build);
})();
