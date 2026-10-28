// תחושת לחיצה: פעימה עדינה ורטט קצר בכל לחיצה על כפתור.
// הצליל מסונתז בדפדפן (Web Audio, בלי קובץ קול): פעימה עמוקה ורכה עם נגיעת פעמון זעירה מעליה.
// רטט: navigator.vibrate; באייפון (מערכת 18 ומעלה) דרך מתג מערכת נסתר, כי ספארי אינו תומך ב-vibrate.
// השתקה: סמל רמקול קטן בלי כיתוב, בקצה סרגל הכלים או בפינה התחתונה השמאלית; ההעדפה נשמרת בדפדפן.
// כפתור שאין להשמיע בו (למשל תשובות חידון שמשמיעות צליל משלהן): data-no-click-sound.
// בדיקה: window.__feel.count עולה בכל הפעלה.
(function () {
  'use strict';
  if (window.__feel) return;
  var TH = {
    key: 'lgFeelClick',
    bar: 'header.lm-top',
    fg: '#e9c35a',
    floatFg: '#d1a23a',
    z: 60
  };
  var KEY = TH.key || 'feelClick';
  var mem = null;
  function on() {
    try { var v = localStorage.getItem(KEY); if (v === 'off') return false; if (v === 'on') return true; } catch (e) { if (mem !== null) return mem; }
    return mem === null ? true : mem;
  }
  function setOn(v) { mem = v; try { localStorage.setItem(KEY, v ? 'on' : 'off'); } catch (e) {} }

  var api = window.__feel = { count: 0, last: null, on: on };

  // ---------- צליל ----------
  var ctx = null;
  function pulse() {
    try {
      var AC = window.AudioContext || window.webkitAudioContext; if (!AC) return;
      if (!ctx) ctx = new AC();
      if (ctx.state === 'suspended') ctx.resume();
      var t = ctx.currentTime;
      var out = ctx.createGain(); out.gain.value = 0.9; out.connect(ctx.destination);
      // הפעימה: צליל עמוק שיורד מעט, נכנס רך ודועך מהר
      var o = ctx.createOscillator(), g = ctx.createGain();
      o.type = 'sine';
      o.frequency.setValueAtTime(196, t);
      o.frequency.exponentialRampToValueAtTime(118, t + 0.09);
      g.gain.setValueAtTime(0.0001, t);
      g.gain.exponentialRampToValueAtTime(0.16, t + 0.008);
      g.gain.exponentialRampToValueAtTime(0.0001, t + 0.14);
      o.connect(g); g.connect(out); o.start(t); o.stop(t + 0.16);
      // הנגיעה הבהירה: פעמון זעיר וקצרצר
      var o2 = ctx.createOscillator(), g2 = ctx.createGain();
      o2.type = 'triangle';
      o2.frequency.setValueAtTime(1760, t);
      g2.gain.setValueAtTime(0.0001, t);
      g2.gain.exponentialRampToValueAtTime(0.025, t + 0.004);
      g2.gain.exponentialRampToValueAtTime(0.0001, t + 0.06);
      o2.connect(g2); g2.connect(out); o2.start(t); o2.stop(t + 0.07);
    } catch (e) {}
  }

  // ---------- רטט ----------
  var iosSwitch = null;
  function iosTick() {
    try {
      if (!iosSwitch) {
        var lb = document.createElement('label');
        lb.setAttribute('aria-hidden', 'true');
        lb.style.cssText = 'position:fixed;width:1px;height:1px;overflow:hidden;opacity:0;pointer-events:none;left:-9px;top:-9px;contain:strict';
        var inp = document.createElement('input'); inp.type = 'checkbox'; inp.setAttribute('switch', ''); inp.tabIndex = -1;
        inp.setAttribute('aria-hidden', 'true');
        lb.appendChild(inp); (document.body || document.documentElement).appendChild(lb); iosSwitch = lb;
      }
      iosSwitch.click();
    } catch (e) {}
  }
  var isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
  function buzz() {
    if (navigator.vibrate) { try { if (!navigator.userActivation || navigator.userActivation.hasBeenActive) navigator.vibrate(10); } catch (e) {} }
    else if (isIOS) iosTick();
  }

  // ---------- מה נחשב כפתור ----------
  var SEL = 'button,input[type="button"],input[type="submit"],input[type="reset"],input[type="checkbox"],input[type="radio"],' +
    '[role="button"],[role="tab"],[role="menuitem"],[role="menuitemcheckbox"],[role="menuitemradio"],[role="switch"],summary,select';
  var BTN_CLASS = /(^|[\s_-])(btn|button|chip|tab|tabs|pill|tile|icon|ico|nav|toggle|cta|tbtn|act)([\s_-]|$)/i;
  var EDIT = '[contenteditable=""],[contenteditable="true"],[contenteditable="plaintext-only"],textarea,input:not([type="button"]):not([type="submit"]):not([type="reset"]):not([type="checkbox"]):not([type="radio"]):not([type="range"])';

  function disabled(n) { return n.disabled === true || n.getAttribute('aria-disabled') === 'true'; }
  function anchorOk(n) {
    if (BTN_CLASS.test(n.getAttribute('class') || '')) return true;
    if (n.closest('nav,[role="navigation"],[role="toolbar"],[role="menu"],[role="menubar"],[role="tablist"],header,footer,.toolbar,.pn')) return true;
    var rel = n.getAttribute('rel') || '';
    if (/(prev|next)/.test(rel) || n.querySelector('img,svg,canvas')) return true;
    var tx = (n.textContent || '').trim();
    if (/^[‹›«»←→<>]|[‹›«»←→<>]$/.test(tx) || /^(הקודם|הבא|קודם|הבא)$/.test(tx.replace(/[‹›«»←→<>\s]/g, ''))) return true;
    var d = getComputedStyle(n).display;
    return d !== 'inline' && d !== 'contents';
  }
  function pick(t) {
    if (!t) return null;
    if (t.nodeType !== 1) t = t.parentElement;
    var n = t, depth = 0, body = document.body, root = document.documentElement;
    while (n && n !== body && n !== root && depth < 8) {
      if (n.hasAttribute('data-no-click-sound')) return null;
      if (n.id === 'feelToggle') return null;
      if (n.matches(SEL)) { return disabled(n) ? null : n; }
      if (n.tagName === 'A' && n.hasAttribute('href')) { if (anchorOk(n)) return disabled(n) ? null : n; }
      else if (n.tagName !== 'LABEL' || n.control) {
        // אלמנט לחיץ מעוצב ככפתור: סמן יד, ואינו בלוק טקסט ארוך
        var cs = getComputedStyle(n);
        if (cs.cursor === 'pointer' && !n.closest(EDIT)) {
          if (disabled(n)) return null;
          if (n.querySelector('img,svg,canvas') || (n.textContent || '').length <= 48 || BTN_CLASS.test(n.getAttribute('class') || '')) return n;
          return null;
        }
      }
      n = n.parentElement; depth++;
    }
    return null;
  }

  var last = 0;
  api.pick = pick;
  function fire(el) {
    if (!on()) return;
    var now = Date.now(); if (now - last < 50) return; last = now;
    api.count++; api.last = el;
    pulse(); buzz();
  }

  // ---------- מאזין אחד מואצל ----------
  var touch = null;
  document.addEventListener('pointerdown', function (ev) {
    if (!on()) return;
    if (ev.pointerType === 'touch' || ev.pointerType === 'pen') {
      if (ev.isPrimary === false) { touch = null; return; }
      var el0 = pick(ev.target);
      touch = el0 ? { el: el0, x: ev.clientX, y: ev.clientY, t: Date.now(), id: ev.pointerId } : null;
      return;
    }
    if (ev.button && ev.button !== 0) return;
    var el = pick(ev.target);
    if (el) fire(el);
  }, { capture: true, passive: true });
  // במגע: הצליל והרטט בעת ההרמה, ורק בהקשה קצרה במקום (לא בגלילה, בגרירה או בלחיצה ארוכה)
  document.addEventListener('pointerup', function (ev) {
    var s = touch; touch = null;
    if (!s || s.id !== ev.pointerId) return;
    if (Date.now() - s.t > 450) return;
    if (Math.abs(ev.clientX - s.x) > 10 || Math.abs(ev.clientY - s.y) > 10) return;
    fire(s.el);
  }, { capture: true, passive: true });
  document.addEventListener('pointercancel', function () { touch = null; }, { capture: true, passive: true });

  // מקלדת: אנטר או רווח על כפתור (צליל בלבד)
  document.addEventListener('keydown', function (ev) {
    if (ev.repeat || (ev.key !== 'Enter' && ev.key !== ' ') || !on()) return;
    var t = ev.target; if (!t || t.nodeType !== 1 || t.matches(EDIT)) return;
    var el = t.matches(SEL) ? t : null;
    if (!el || el.hasAttribute('data-no-click-sound') || el.closest('[data-no-click-sound]') || disabled(el)) return;
    api.count++; api.last = el; pulse();
  }, { capture: true, passive: true });

  // ---------- מתג השתקה: סמל רמקול קטן, בלי כיתוב ----------
  // פרומפט 1 כל האתרים (28.10.2026): התג "צליל לחיצה: פעיל" הוסר. במקומו סמל רמקול עמום בקצה סרגל הכלים העליון
  // (TH.bar), רק כשהסרגל נשאר בשורה אחת ואף כפתור בו אינו מתכווץ; אחרת בפינה התחתונה השמאלית, מעל כל כפתור צף שיושב שם.
  var CSS = '#feelToggle{all:unset;box-sizing:border-box;display:inline-flex;align-items:center;justify-content:center;' +
    'width:32px;height:32px;min-width:32px;flex:0 0 32px;margin:0;padding:0;border:0;border-radius:50%;background:none;box-shadow:none;' +
    'color:' + (TH.fg || 'currentColor') + ';opacity:.5;cursor:pointer;-webkit-tap-highlight-color:transparent;transition:opacity .2s}' +
    '#feelToggle:hover,#feelToggle:focus-visible{opacity:1}#feelToggle:focus-visible{outline:1px solid currentColor;outline-offset:-2px}' +
    '#feelToggle svg{display:block;width:17px;height:17px;flex:none;pointer-events:none}' +
    '#feelToggle.floating{position:fixed;left:calc(6px + env(safe-area-inset-left, 0px));bottom:calc(6px + env(safe-area-inset-bottom, 0px));' +
    'z-index:' + (TH.z || 60) + ';color:' + (TH.floatFg || TH.fg || 'currentColor') + '}' +
    '@media print{#feelToggle{display:none!important}}';
  var SVG_ON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M11 5 6 9H3v6h3l5 4z"/><path d="M15.5 8.5a5 5 0 0 1 0 7M18.5 5.5a9 9 0 0 1 0 13"/></svg>';
  var SVG_OFF = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M11 5 6 9H3v6h3l5 4z"/><path d="M3.5 3.5l17 17"/></svg>';

  function addToggle() {
    if (document.getElementById('feelToggle')) return;
    try { if (window.top !== window) return; } catch (e) { return; }
    var st = document.createElement('style'); st.id = 'feelStyle'; st.textContent = CSS;
    (document.head || document.documentElement).appendChild(st);
    var b = document.createElement('button');
    b.id = 'feelToggle'; b.type = 'button';
    b.setAttribute('data-no-zb', '');   // בלי הלוחית המוגבהת של שכבת הכפתורים
    function paint() {
      var tip = on() ? 'השתקת צליל הלחיצה' : 'הפעלת צליל הלחיצה';
      b.innerHTML = on() ? SVG_ON : SVG_OFF;
      b.title = tip; b.setAttribute('aria-label', tip);
    }
    b.addEventListener('click', function () { setOn(!on()); paint(); if (on()) { pulse(); buzz(); } });
    paint();

    function shown(el) { return !!el && el.getClientRects().length > 0 && !el.closest('[hidden]'); }
    // רוחב כל כפתור, קישור וסמל שבסרגל (מילוי גמיש כמו תפריט ניווט רשאי להצטמק; הפריטים שבתוכו לא)
    function widths(bar) {
      var w = [], els = bar.querySelectorAll('a,button,input,select,img,svg,[role="button"]');
      for (var i = 0; i < els.length && i < 120; i++) { if (els[i] === b || b.contains(els[i])) continue; var r = els[i].getBoundingClientRect(); w.push(r.height > 0 ? r.width : -1); }
      return w;
    }
    // בסרגל העליון: הפריט האחרון (הקצה השמאלי), ורק אם הסרגל לא נשבר לשורה שנייה, לא גלש ולא כיווץ כפתור אחר
    function tryBar() {
      var bar = null;
      try { bar = TH.bar ? document.querySelector(TH.bar) : null; } catch (e) {}
      if (!shown(bar)) return false;
      if (b.parentNode) b.parentNode.removeChild(b);
      var h0 = bar.getBoundingClientRect().height, sw0 = Math.max(bar.scrollWidth, bar.clientWidth), w0 = widths(bar);
      b.className = ''; b.style.bottom = ''; bar.appendChild(b);
      var r = bar.getBoundingClientRect(), q = b.getBoundingClientRect(), w1 = widths(bar), ok = q.width > 0 &&
        r.height <= h0 + 1 && bar.scrollWidth <= sw0 + 1 && q.left >= r.left - 1 && q.right <= r.right + 1;
      for (var i = 0; ok && i < w0.length; i++) if (w0[i] > 0 && w1[i] < w0[i] - 1) ok = false;
      if (!ok) bar.removeChild(b);
      return ok;
    }
    // כפתור צף אחר בפינה (חזרה למעלה, התקנה, נגן): הסמל עולה מעליו. מעטפת שמכסה את רוב המסך אינה מכשול.
    function obstacle(x, y) {
      var els = document.elementsFromPoint ? document.elementsFromPoint(x, y) : [];
      for (var i = 0; i < els.length; i++) {
        var e = els[i];
        if (e === b || b.contains(e) || e === document.body || e === document.documentElement) continue;
        for (var n = e; n && n !== document.body; n = n.parentElement) {
          var p = getComputedStyle(n).position;
          if (p === 'fixed' || p === 'sticky') {
            var r = n.getBoundingClientRect();
            if (r.height < innerHeight * 0.4) return r;
            break;
          }
        }
      }
      return null;
    }
    function dodge() {
      if (b.className !== 'floating') return;
      var y = 6;
      for (var k = 0; k < 4; k++) {
        var bot = innerHeight - y, top = bot - 32, hit = null;
        var pts = [[9, top + 3], [35, top + 3], [9, bot - 3], [35, bot - 3], [22, top + 16]];
        for (var i = 0; i < pts.length && !hit; i++) hit = obstacle(pts[i][0], pts[i][1]);
        if (!hit) break;
        y = innerHeight - hit.top + 6;
        if (y > innerHeight / 2) { y = 6; break; }
      }
      var v = y === 6 ? '' : 'calc(' + Math.round(y) + 'px + env(safe-area-inset-bottom, 0px))';
      if (b.style.bottom !== v) b.style.bottom = v;
    }
    // גוף דף עם transform או filter (למשל הנפשת כניסה) הופך את fixed ליחסי אליו - אז הסמל נתלה על השורש
    function floatHost() {
      var cs = getComputedStyle(document.body);
      return (cs.transform !== 'none' || cs.filter !== 'none' || cs.perspective !== 'none' || /paint|layout|strict|content/.test(cs.contain || '')) ? document.documentElement : document.body;
    }
    function place() {
      if (tryBar()) return true;
      var host = floatHost();
      if (b.parentNode !== host) { if (b.parentNode) b.parentNode.removeChild(b); host.appendChild(b); }
      b.className = 'floating'; dodge();
      return false;
    }
    // סרגל שנבנה מאוחר (בידי סקריפט של הדף) - נבדוק שוב עד שיופיע
    if (!place() && TH.bar) {
      var tries = 0, iv = setInterval(function () { if (place() || ++tries > 12) clearInterval(iv); }, 500);
    }
    var rt = 0, sc = 0;
    window.addEventListener('resize', function () { clearTimeout(rt); rt = setTimeout(place, 250); });
    window.addEventListener('load', function () { setTimeout(place, 300); });
    window.addEventListener('scroll', function () { if (!sc) sc = setTimeout(function () { sc = 0; dodge(); }, 400); }, { passive: true, capture: true });
    setTimeout(dodge, 2000);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', addToggle); else addToggle();
})();
