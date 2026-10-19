// תחושת לחיצה: פעימה עדינה ורטט קצר בכל לחיצה על כפתור.
// הצליל מסונתז בדפדפן (Web Audio, בלי קובץ קול): פעימה עמוקה ורכה עם נגיעת פעמון זעירה מעליה.
// רטט: navigator.vibrate; באייפון (מערכת 18 ומעלה) דרך מתג מערכת נסתר, כי ספארי אינו תומך ב-vibrate.
// מתג השתקה בתחתית הדף ("צליל לחיצה: פעיל / כבוי"); ההעדפה נשמרת בדפדפן.
// כפתור שאין להשמיע בו (למשל תשובות חידון שמשמיעות צליל משלהן): data-no-click-sound.
// בדיקה: window.__feel.count עולה בכל הפעלה.
(function () {
  'use strict';
  if (window.__feel) return;
  var TH = {
    key: 'lgFeelClick',
    host: '.lm-foot',
    font: "700 13px/1.3 var(--ui, 'Assistant', system-ui, sans-serif)",
    size: '13px',
    fg: '#e9c35a',
    bg: 'transparent',
    border: 'rgba(209,162,58,.6)',
    hoverBg: 'rgba(233,195,90,.15)',
    floatBg: '#0f263b',
    margin: '12px auto 0'
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

  // ---------- מתג השתקה ----------
  var CSS = '#feelToggle{display:inline-flex;align-items:center;gap:.4em;margin:' + (TH.margin || '.6em auto') + ';padding:.3em .85em;' +
    'font:' + (TH.font || 'inherit') + ';font-size:' + (TH.size || '.8rem') + ';line-height:1.3;letter-spacing:.01em;cursor:pointer;' +
    'color:' + (TH.fg || 'inherit') + ';background:' + (TH.bg || 'transparent') + ';border:1px solid ' + (TH.border || 'currentColor') + ';' +
    'border-radius:' + (TH.radius || '999px') + ';opacity:.78;-webkit-tap-highlight-color:transparent;transition:opacity .2s,background .2s}' +
    '#feelToggle:hover,#feelToggle:focus-visible{opacity:1;' + (TH.hoverBg ? 'background:' + TH.hoverBg + ';' : '') + '}' +
    '#feelToggle svg{width:1.05em;height:1.05em;flex:none}' +
    '#feelToggle.floating{position:fixed;inset-block-end:6px;left:50%;transform:translateX(-50%);z-index:' + (TH.z || 60) + ';margin:0;' +
    'background:' + (TH.floatBg || TH.bg || 'rgba(255,255,255,.9)') + ';box-shadow:0 1px 6px rgba(0,0,0,.18)}' +
    '.feel-wrap{text-align:center}' +
    '@media print{#feelToggle,.feel-wrap{display:none!important}}';
  var SVG_ON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M11 5 6 9H3v6h3l5 4z"/><path d="M15.5 8.5a5 5 0 0 1 0 7M18.5 5.5a9 9 0 0 1 0 13"/></svg>';
  var SVG_OFF = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M11 5 6 9H3v6h3l5 4z"/><path d="m16 9 5 6m0-6-5 6"/></svg>';

  function addToggle() {
    if (document.getElementById('feelToggle')) return;
    try { if (window.top !== window) return; } catch (e) { return; }
    var st = document.createElement('style'); st.id = 'feelStyle'; st.textContent = CSS;
    (document.head || document.documentElement).appendChild(st);
    var b = document.createElement('button');
    b.id = 'feelToggle'; b.type = 'button';
    function paint() {
      var v = on();
      b.innerHTML = (v ? SVG_ON : SVG_OFF) + '<span>' + (v ? 'צליל לחיצה: פעיל' : 'צליל לחיצה: כבוי') + '</span>';
      b.setAttribute('aria-pressed', v ? 'true' : 'false');
      b.title = v ? 'לחצו להשתקת צליל הלחיצה' : 'לחצו להפעלת צליל הלחיצה';
    }
    b.addEventListener('click', function () { setOn(!on()); paint(); if (on()) { pulse(); buzz(); } });
    paint();
    function place() {
      var host = null;
      try {
        var cand = document.querySelectorAll(TH.host || 'footer');
        for (var i = cand.length - 1; i >= 0; i--) {
          if (cand[i].offsetParent !== null && !cand[i].closest('[hidden]') && cand[i].getBoundingClientRect().height > 8) { host = cand[i]; break; }
        }
      } catch (e) {}
      if (host) {
        if (b.parentNode && b.parentNode.className === 'feel-wrap' && host.contains(b)) return true;
        var w = document.createElement('div'); w.className = 'feel-wrap'; w.appendChild(b);
        b.className = ''; host.appendChild(w); return true;
      }
      if (!b.parentNode) { b.className = 'floating'; document.body.appendChild(b); }
      return false;
    }
    // תחתית שנבנית מאוחר (בידי סקריפט של הדף) - נבדוק שוב עד שתופיע
    if (!place()) {
      var tries = 0, iv = setInterval(function () { if (place() || ++tries > 12) clearInterval(iv); }, 500);
    }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', addToggle); else addToggle();
})();
