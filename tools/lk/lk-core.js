/* lk-core.js - נתוני גלישה וטקסטי האתר (8.10.2026).
   נטען פעם אחת בכל דף ציבורי, באופן אסינכרוני (defer). שני תפקידים:
   א. נתוני גלישה: Cloudflare Web Analytics ו-Microsoft Clarity, בלי עוגיות.
      Clarity אינו נטען אצל מנהל, ונעצר בכל מצב עריכה. ראו docs/נתוני-גלישה.md.
   ב. טקסטי האתר: שכבת שינויים מן השרת מוחלת על טקסטי המעטפת (לא על תוכן
      הגמרא). קוד העיפרון (lk-pencil.js) נטען רק במכשיר של מנהל. ראו docs/TEXTS.md. */
(function () {
  'use strict';
  if (window.LK && window.LK.v) return;
  var CFG = /*LK_CFG*/{"clarity": "", "cf": "", "api": "https://leokmei-suggest.m7654301.workers.dev", "v": "dev"}/*END_CFG*/;
  var W = window, D = document;
  var LK = W.LK = { v: CFG.v, cfg: CFG };

  function ls(k, v) {
    try { if (v === undefined) return localStorage.getItem(k); if (v === null) localStorage.removeItem(k); else localStorage.setItem(k, v); } catch (e) { }
    return null;
  }
  LK.isAdminDevice = function () { return !!ls('lg-adm'); };
  var ADMIN = LK.isAdminDevice() || ls('lg-admin') === '1';

  /* ---------------------------------------------------------------- סוג הדף */
  var SLUGS = /^(avodah-zarah|bava-batra|bava-kamma|bava-metzia|beitzah|bekhorot|berakhot|chagigah|chullin|eruvin|gittin|horayot|ketubot|kiddushin|makkot|megillah|moed-katan|nazir|nedarim|niddah|pesachim|rosh-hashanah|sanhedrin|shabbat|shevuot|sotah|sukkah|taanit|temurah|yevamot|yoma|zevachim|meilah|keritot|arakhin|tamid|kinnim|midot|menachot|temura)$/;
  var TYPES = { '': 'home', 'index': 'home', 'shas': 'shas', 'masechtot': 'masechtot', 'yomi': 'yomi', 'hadaf-hayomi': 'yomi-static', 'lamed': 'lamed',
    'quiz': 'quiz', 'shiurim': 'shiurim', 'about': 'about', 'settings': 'settings', 'done': 'done', 'admin-lamdim': 'admin', 'mekorot': 'mekorot',
    'masechet': 'masechet-shell', 'admin-texts': 'admin-texts', 'privacy': 'privacy' };
  var TYPE_HE = { home: 'בית', shas: 'מפת הש"ס', masechtot: 'רשימת מסכתות', yomi: 'הדף היומי', 'yomi-static': 'הדף היומי (סטטי)', lamed: 'המקום שלי', quiz: 'בחן את עצמך',
    shiurim: 'שיעורים', about: 'אודות', settings: 'הגדרות', done: 'סיום מסכת', admin: 'מנהל', mekorot: 'מקורות', 'masechet-shell': 'מסכת', gemara: 'דף גמרא', 'daf-static': 'דף גמרא (סטטי)',
    privacy: 'פרטיות', other: 'אחר' };
  LK.pageType = function () {
    var p = decodeURIComponent(location.pathname || '/').replace(/^\/+|\/+$/g, '');
    var parts = p.split('/'), last = parts[parts.length - 1].replace(/\.html$/, '');
    var out = { type: 'other', masechet: '', daf: '' };
    if (parts.length >= 2 && SLUGS.test(parts[parts.length - 2])) { out.type = 'daf-static'; out.masechet = parts[parts.length - 2]; out.daf = last; return out; }
    if (parts.length === 1 && SLUGS.test(last)) { out.type = 'gemara'; out.masechet = last; return out; }
    if (parts.length === 1 && last.indexOf('sukkah-') === 0) { out.type = 'gemara'; out.masechet = 'sukkah'; return out; }
    if (parts.length === 1 && Object.prototype.hasOwnProperty.call(TYPES, last)) out.type = TYPES[last];
    return out;
  };
  LK.typeHe = function (t) { return TYPE_HE[t] || t; };
  var PT = LK.pageType();
  LK.scopeOf = function (el) {
    return (el && el.closest && el.closest('.lm-top,footer,.lm-foot,#lk-priv')) ? 'site' : PT.type;
  };

  /* ---------------------------------------------------------------- מצב עריכה */
  function editing() {
    var b = D.body;
    return !!(b && (b.classList.contains('ed') || b.classList.contains('lk-pencil')));
  }
  LK.editing = editing;

  /* ================================================================
     א. נתוני גלישה
     ================================================================ */
  var clarityOn = false, cfOn = false;
  function loadScript(src, attrs) {
    var s = D.createElement('script'); s.async = true; s.src = src;
    for (var k in (attrs || {})) s.setAttribute(k, attrs[k]);
    (D.head || D.documentElement).appendChild(s); return s;
  }
  function startCF() {
    if (cfOn || !CFG.cf || ADMIN) return; cfOn = true;
    loadScript('https://static.cloudflareinsights.com/beacon.min.js', { defer: '', 'data-cf-beacon': JSON.stringify({ token: CFG.cf, spa: true }) });
  }
  function clarityStop() {
    if (!clarityOn) return;
    try { W.clarity('stop'); } catch (e) { }
    clarityOn = false; LK.clarityStopped = true;
  }
  function startClarity() {
    if (clarityOn || LK.clarityStopped || !CFG.clarity || ADMIN || editing()) return;
    clarityOn = true;
    (function (c, l, a, r, i, t, y) {
      c[a] = c[a] || function () { (c[a].q = c[a].q || []).push(arguments); };
      t = l.createElement(r); t.async = 1; t.src = 'https://www.clarity.ms/tag/' + i;
      y = l.getElementsByTagName(r)[0]; if (y) y.parentNode.insertBefore(t, y); else l.head.appendChild(t);
    })(W, D, 'clarity', 'script', CFG.clarity);
    try { W.clarity('consent', false); } catch (e) { }   /* בלי עוגיות */
    tagView();
  }
  function modeNow() {
    var b = D.body; if (!b) return '';
    if (b.classList.contains('splitsrc')) return 'מסך מפוצל';
    var m = (b.getAttribute('data-mode') || D.documentElement.getAttribute('data-mode') || '');
    if (m) return m;
    if (PT.type === 'gemara') { var v = D.getElementById('vbtn'); return v && v.getAttribute('aria-pressed') === 'true' ? 'טור אחד' : 'טורים'; }
    return '';
  }
  function dafNow() {
    var o = D.querySelector('#dafsel option:checked'); if (o && o.textContent) return o.textContent.trim().slice(0, 12);
    var m = /[#&]p=(\d+)/.exec(location.hash || ''); return m ? 'p' + m[1] : (PT.daf || '');
  }
  function tagView() {
    if (!clarityOn || !W.clarity) return;
    try {
      var t = PT.type;
      W.clarity('set', 'סוג_דף', LK.typeHe(t));
      W.clarity('set', 'page_type', t);
      if (PT.masechet) W.clarity('set', 'מסכת', PT.masechet);
      var d = dafNow(); if (d) W.clarity('set', 'דף', d);
      var md = modeNow(); if (md) W.clarity('set', 'מצב_תצוגה', md);
      W.clarity('set', 'התקן', (W.matchMedia && W.matchMedia('(max-width:760px)').matches) ? 'טלפון' : 'מחשב');
    } catch (e) { }
  }
  LK.event = function (name) { if (clarityOn) { try { W.clarity('event', name); } catch (e) { } } };

  /* אירועים מותאמים: לפי מזהה, או לפי תווית הכפתור. הרשימה כולה כאן, במקום אחד. */
  var EVENTS = [
    ['מקור', '#gmbtn,[onclick*="gemaraBtn"],[onclick*="openSrc"]'],
    ['צורת הדף', '#tzbtn,[onclick*="tzBtn"]'],
    ['הצע תיקון', '#edbtn,[onclick*="suggest()"],[onclick*="editBtn"]'],
    ['בחן את עצמך', 'a[href*="quiz.html"],[onclick*="quizDaf"]'],
    ['המקום שלי', 'a[href*="lamed.html"]'],
    ['הדפסה', '[onclick*="printPerek"],[onclick*="toPdf"]'],
    ['שיעור יוטיוב', '.lm-shiur-play'],
    ['דף הבא', '[onclick*="goDaf(1)"],#sp-next,#ss-next'],
    ['דף קודם', '[onclick*="goDaf(-1)"],#sp-prev,#ss-prev'],
    ['הדף היומי', '#dybtn,a[href*="yomi.html"]'],
    ['ניווט', '#navbtn']
  ];

  function onClick(e) {
    if (!clarityOn) return;
    var t = e.target; if (!t || !t.closest) return;
    for (var i = 0; i < EVENTS.length; i++) {
      var hit = null; try { hit = t.closest(EVENTS[i][1]); } catch (x) { }
      if (hit) { LK.event(EVENTS[i][0]); break; }
    }
  }
  function maskInputs(root) {
    var els = (root || D).querySelectorAll('input,textarea,select,[contenteditable="true"],[contenteditable="plaintext-only"]');
    for (var i = 0; i < els.length; i++) els[i].setAttribute('data-clarity-mask', 'true');
  }
  var lastKey = '';
  function viewChanged() {
    var k = location.pathname + location.hash; if (k === lastKey) return; lastKey = k;
    setTimeout(tagView, 450);
  }
  function startAnalytics() {
    lastKey = location.pathname + location.hash;
    if (ADMIN) return;                       /* מנהל: אין אף כלי ניתוח */
    startCF();
    if (!editing()) startClarity();
    maskInputs();
    D.addEventListener('focusin', function (e) { var t = e.target; if (t && t.matches && t.matches('input,textarea,select,[contenteditable]')) t.setAttribute('data-clarity-mask', 'true'); }, true);
    D.addEventListener('click', onClick, true);
    W.addEventListener('hashchange', viewChanged);
    W.addEventListener('popstate', viewChanged);
    var ps = history.pushState; history.pushState = function () { var r = ps.apply(this, arguments); viewChanged(); return r; };
    /* מצב עריכה (מנהל או מציע): עוצרים מיד כשהגוף מקבל את המצב */
    var mo = new MutationObserver(function () { if (editing()) { clarityStop(); } });
    mo.observe(D.body, { attributes: true, attributeFilter: ['class'] });
    if (editing()) clarityStop();
  }

  /* ================================================================
     ב. טקסטי האתר
     ================================================================ */
  var NONCONTENT_SKIP = 'script,style,noscript,textarea,input,select,option,svg,code,pre,.lk-ui,[data-lk-skip]';
  var CONTENT = '#flow,#srcl,.src,.flow,.panel,[data-lid],.qz-card,.lm-shiur,.lm-sug,[data-lk-user]';
  LK.CONTENT = CONTENT; LK.SKIP = NONCONTENT_SKIP;
  var TX = { rev: 0, items: {}, byKey: {}, byOrig: {} };
  var applied = new WeakMap();   /* צומת -> {orig, shown} */
  var attrApplied = new WeakMap();

  LK.appliedOf = function (tn) { var r = applied.get(tn); return r && tn.nodeValue === r.shown ? r : null; };
  LK.registerApplied = function (tn, orig, shown) { applied.set(tn, { orig: orig, shown: shown }); };
  LK.attrOrig = function (el, a, v) { var r = attrApplied.get(el); return r && r[a] && r[a].shown === v ? r[a].orig : v; };
  Object.defineProperty(LK, 'metaOrig', { get: function () { return { title: metaApplied.title && metaApplied.title.orig, desc: metaApplied.desc && metaApplied.desc.orig }; } });
  LK.norm = function (s) { return String(s || '').replace(/[‎‏]/g, '').replace(/\s+/g, ' ').trim(); };
  /* מספרים בתוך טקסט הם משתנים: {n}. שומרים את הערכים בסדר. */
  LK.tokenize = function (s) {
    var nums = [];
    var t = LK.norm(s).replace(/\d+(?:[.,:]\d+)*/g, function (m) { nums.push(m); return '{n}'; });
    return { t: t, nums: nums };
  };
  function h32(s) {
    var h = 2166136261;
    for (var i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); }
    return (h >>> 0).toString(36);
  }
  LK.slug = function (t) {
    return String(t).replace(/^[a-z-]+:/, '').replace(/[^א-תA-Za-z\s]/g, '').trim().split(/\s+/).slice(0, 3).join('-').slice(0, 24) || 'txt';
  };
  /* מפתח יציב: היקף + מילים ראשונות + גיבוב הטקסט המקורי (עם משתנים). לא תלוי במיקום. */
  LK.keyFor = function (scope, origTok) { return scope + '.' + LK.slug(origTok) + '.' + h32(origTok); };

  function fill(tpl, nums) { var i = 0; return String(tpl).replace(/\{n\}/g, function () { return i < nums.length ? nums[i++] : '{n}'; }); }
  function indexTx(items) {
    TX.items = items || {}; TX.byKey = {}; TX.byOrig = {};
    for (var k in TX.items) {
      var it = TX.items[k]; if (!it) continue;
      var sc = k.split('.')[0];
      var o = it.o; if (o == null) continue;
      TX.byOrig[sc + '|' + (it.d || 'text') + '|' + LK.tokenize(o).t] = { k: k, it: it };
    }
  }
  function insideContent(el) { try { return !!el.closest(CONTENT); } catch (e) { return false; } }
  function applyNode(tn) {
    var par = tn.parentNode; if (!par || par.nodeType !== 1) return;
    if (par.closest && (par.closest(NONCONTENT_SKIP) || insideContent(par))) return;
    var rec = applied.get(tn);
    var raw = tn.nodeValue;
    var base = rec && raw === rec.shown ? rec.orig : raw;
    if (!/[א-ת]/.test(base)) return;
    var tk = LK.tokenize(base);
    var hit = TX.byOrig[LK.scopeOf(par) + '|text|' + tk.t];
    if (hit) {
      var out = hit.it.h ? '' : fill(hit.it.t, tk.nums);
      if (hit.it.h) { par.setAttribute('data-lk-hidden', '1'); }
      if (raw !== out) { applied.set(tn, { orig: base, shown: out }); tn.nodeValue = out; }
    } else if (rec && raw === rec.shown) {
      tn.nodeValue = rec.orig; applied.delete(tn);
      if (par.removeAttribute) par.removeAttribute('data-lk-hidden');
    }
  }
  var ATTRS = ['title', 'aria-label', 'placeholder', 'alt'];
  function applyAttrs(el) {
    if (!el.getAttribute || (el.closest && (el.closest('.lk-ui') || insideContent(el)))) return;
    for (var i = 0; i < ATTRS.length; i++) {
      var a = ATTRS[i], v = el.getAttribute(a); if (!v || !/[א-ת]/.test(v)) continue;
      var rec = attrApplied.get(el), key = a;
      var base = rec && rec[key] && v === rec[key].shown ? rec[key].orig : v;
      var tk = LK.tokenize(base);
      var hit = TX.byOrig[LK.scopeOf(el) + '|' + a + '|' + tk.t];
      if (hit && !hit.it.h) {
        var out = fill(hit.it.t, tk.nums);
        if (out !== v) { rec = rec || {}; rec[key] = { orig: base, shown: out }; attrApplied.set(el, rec); el.setAttribute(a, out); }
      }
    }
  }
  function applyAll(root) {
    if (!Object.keys(TX.byOrig).length && !hasApplied) return;
    root = root || D.body; if (!root) return;
    if (root.nodeType === 1 && (insideContent(root) || (root.closest && root.closest(NONCONTENT_SKIP)))) return;
    /* תוכן הגמרא אינו נסרק כלל: המסנן דוחה את כל התת-עץ שלו */
    var tw = D.createTreeWalker(root, NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT, {
      acceptNode: function (x) {
        if (x.nodeType === 3) return NodeFilter.FILTER_ACCEPT;
        if (x.matches && (x.matches(CONTENT) || x.matches(NONCONTENT_SKIP))) return NodeFilter.FILTER_REJECT;
        return NodeFilter.FILTER_SKIP;
      }
    }), n, list = [];
    while ((n = tw.nextNode())) list.push(n);
    for (var i = 0; i < list.length; i++) applyNode(list[i]);
    var els = root.querySelectorAll ? root.querySelectorAll('[title],[aria-label],[placeholder],[alt]') : [];
    if (root.nodeType === 1 && root.matches && root.matches('[title],[aria-label],[placeholder],[alt]')) applyAttrs(root);
    for (var j = 0; j < els.length; j++) applyAttrs(els[j]);
    applyMeta();
  }
  var metaApplied = {};
  function applyMeta() {
    var t = LK.tokenize(metaApplied.title ? metaApplied.title.orig : D.title).t;
    var hit = TX.byOrig[PT.type + '|doctitle|' + t];
    if (hit && !hit.it.h) { if (!metaApplied.title) metaApplied.title = { orig: D.title }; D.title = hit.it.t; }
    else if (metaApplied.title) { D.title = metaApplied.title.orig; delete metaApplied.title; }
    var m = D.querySelector('meta[name="description"]');
    if (m) {
      var cur = metaApplied.desc ? metaApplied.desc.orig : m.getAttribute('content');
      var h2 = TX.byOrig[PT.type + '|metadesc|' + LK.tokenize(cur).t];
      if (h2 && !h2.it.h) { if (!metaApplied.desc) metaApplied.desc = { orig: cur }; m.setAttribute('content', h2.it.t); }
      else if (metaApplied.desc) { m.setAttribute('content', metaApplied.desc.orig); delete metaApplied.desc; }
    }
  }
  var hasApplied = false, obs = null, pend = false, queue = [];
  function flush() {
    pend = false; var q = queue; queue = [];
    for (var i = 0; i < q.length; i++) { var n = q[i]; if (n.isConnected === false) continue; if (n.nodeType === 3) applyNode(n); else if (n.nodeType === 1) applyAll(n); }
  }
  function watch() {
    if (obs || !D.body) return;
    obs = new MutationObserver(function (ms) {
      if ((!Object.keys(TX.byOrig).length && !hasApplied) || editing()) return;
      for (var i = 0; i < ms.length; i++) {
        var m = ms[i];
        if (m.type === 'characterData') queue.push(m.target);
        else for (var j = 0; j < m.addedNodes.length; j++) {
          var a = m.addedNodes[j]; if (a.nodeType === 1 && a.closest && a.closest('.lk-ui')) continue; queue.push(a);
        }
      }
      if (!pend) { pend = true; Promise.resolve().then(flush); }   /* לפני הציור הראשון */
    });
    obs.observe(D.body, { childList: true, subtree: true, characterData: true });
  }
  function setTx(d) {
    if (!d || !d.items) return;
    var any = Object.keys(d.items).length > 0;
    TX.rev = d.rev || 0; indexTx(d.items);
    if (any) hasApplied = true;
    applyAll();
    LK.tx = TX;
    D.dispatchEvent(new CustomEvent('lk:tx', { detail: TX }));
  }
  function loadTx() {
    var cached = null;
    try { cached = JSON.parse(ls('lk-tx') || 'null'); } catch (e) { }
    var hasCache = cached && cached.items;
    if (hasCache) setTx(cached);
    else {
      /* גולש חדש: מסתירים את הגוף עד שהטקסטים מגיעים, לכל היותר 600 מילישניות */
      var st = D.createElement('style'); st.id = 'lk-wait'; st.textContent = 'body{visibility:hidden!important}';
      (D.head || D.documentElement).appendChild(st);
      setTimeout(function () { var s = D.getElementById('lk-wait'); if (s) s.remove(); }, 600);
    }
    var xhr = new XMLHttpRequest();
    xhr.open('GET', CFG.api + '/tx'); xhr.timeout = 4000;
    xhr.onload = function () {
      var s = D.getElementById('lk-wait');
      try {
        var d = JSON.parse(xhr.responseText);
        if (d && d.ok) {
          ls('lk-tx', JSON.stringify({ rev: d.rev, items: d.items }));
          if (!hasCache || (cached && cached.rev !== d.rev)) setTx(d);
        }
      } catch (e) { }
      if (s) s.remove();
    };
    xhr.onerror = xhr.ontimeout = function () { var s = D.getElementById('lk-wait'); if (s) s.remove(); };
    xhr.send();
  }
  LK.reapply = function (items, rev) { ls('lk-tx', JSON.stringify({ rev: rev, items: items })); setTx({ rev: rev, items: items }); };

  /* ---------------------------------------------------------------- העיפרון: רק למנהל */
  function adminTools() {
    if (!LK.isAdminDevice()) return;
    var s = D.createElement('script'); s.src = '/lk-pencil.js?v=' + CFG.v; s.async = true;
    D.head.appendChild(s);
  }

  function boot() {
    watch(); loadTx(); startAnalytics(); adminTools();
  }
  if (D.readyState === 'loading') D.addEventListener('DOMContentLoaded', boot); else boot();
})();
