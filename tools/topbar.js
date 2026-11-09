/* topbar.js - ההתנהגות של הסרגל העליון בדף המסכת (פרומפט 28, 9.11.2026).
   נטען אחרי קוד הדף (defer), ומשתמש בפונקציות שלו: isAdmin, toast, barH, ddClose, D, SLUG.
   א. כלי המנהל שנוספים לסרגל אחרי הטעינה ("סכם פרק", "סכם (N)", "סכם קטע") עוברים לאזור המנהל בקצה.
   ב. הכפתורים הצפים של המנהל: אחד בלבד (העיפרון). תפריט הטקסטים ו"בדיקת תוספות" עוברים לתפריט "כלים" של המנהל.
   ג. הצטרפות לקיצור הדף היומי: מי שכבר לחץ - הכפתור מצטמצם לסמל (זכירה במכשיר).
   ד. מי שמגיע מן הווטסאפ (?src=wa): רצועה דקה מעל הדף, עם כפתור הצטרפות וסגירה.
   ה. הסרגל נעלם בגלילה למטה וחוזר בגלילה קלה למעלה (מחשב; בטלפון - mobile.js).
   ו. "הזוהר על הסוגיא" ו"עזרה" בתפריט "עוד".
   אינו נוגע בעיצוב דף התוכן ואינו משנה טקסט. */
(function () {
  'use strict';
  var W = window, Dc = document, H = Dc.documentElement, B = Dc.body;
  if (!Dc.getElementById('bar') || W.__topbar) return;
  W.__topbar = 1;
  var WA = 'https://chat.whatsapp.com/DkkfNQeCumeI3cIOXdY73e', JK = 'lg-wa-joined';
  var $ = function (s, r) { return (r || Dc).querySelector(s); };
  function lsGet(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function lsSet(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* פרטי או חסום - ממשיכים בלי זכירה */ } }
  function adm() { try { return typeof isAdmin === 'function' && isAdmin(); } catch (e) { return false; } }
  function say(m, ms) { try { if (typeof toast === 'function') toast(m, ms || 3200); } catch (e) { /* */ } }
  function ic(n) { return '<svg class="ic" aria-hidden="true"><use href="#i-' + n + '"/></svg>'; }
  function remeasure() { try { if (typeof barH === 'function') barH(); } catch (e) { /* */ } }

  /* ------------------------------------------------ ג. הצטרפות */
  if (lsGet(JK) === '1') H.classList.add('wa-joined');
  Dc.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('#wajoin,#mwajoin,.wsj,[data-join]');
    if (!a) return;
    lsSet(JK, '1'); H.classList.add('wa-joined');
    try { if (W.LK && LK.event) LK.event('הצטרפות לווטסאפ'); } catch (x) { /* */ }
  }, true);
  /* טלפון: סמל ווטסאפ זהוב בסרגל המצומצם, לפני החיפוש */
  (function () {
    var mt = Dc.getElementById('mtop'); if (!mt || $('#mwajoin', mt)) return;
    var a = Dc.createElement('a'); a.id = 'mwajoin'; a.className = 'mwa'; a.href = WA; a.target = '_blank'; a.rel = 'noopener';
    a.title = 'הצטרפות לקיצור הדף היומי'; a.setAttribute('aria-label', 'הצטרפות לקיצור הדף היומי בווטסאפ'); a.setAttribute('data-join', 'mtop');
    a.innerHTML = ic('wa');
    mt.insertBefore(a, $('.msr', mt));
  })();

  /* ------------------------------------------------ א. אזור המנהל */
  var slot = Dc.getElementById('admslot'), bar = Dc.getElementById('bar');
  function gather() {
    if (!slot) return;
    ['#skpbtn', '#skmtop', '#skptag'].forEach(function (s) {
      var el = $(s, bar); if (el && el.parentNode !== slot) slot.appendChild(el);
    });
    var stray = bar.querySelectorAll('.skpbtn'); for (var i = 0; i < stray.length; i++) if (!slot.contains(stray[i])) slot.appendChild(stray[i]);
  }
  var gT = 0;
  if (W.MutationObserver && bar) new MutationObserver(function () { clearTimeout(gT); gT = setTimeout(gather, 30); }).observe(bar, { childList: true, subtree: true });
  gather();
  /* כיתוב הריחוף של "עריכה" לפי התפקיד: לגולש זו הצעת תיקון */
  function edTitle() { var b = Dc.getElementById('edbtn'); if (b) b.title = adm() ? 'עריכה (Ctrl+Alt+E)' : 'הצעת תיקון'; }
  edTitle(); setTimeout(edTitle, 1500);

  /* ------------------------------------------------ ב. כפתור צף אחד למנהל */
  var X = Dc.getElementById('admx');
  function adminExtras() {
    if (!X || !adm()) return;
    var fab = Dc.getElementById('lk-fab');
    if (fab && !Dc.getElementById('admtexts')) {
      H.classList.add('tb-onefab');
      var t = Dc.createElement('button'); t.id = 'admtexts'; t.type = 'button'; t.innerHTML = ic('pencil') + 'טקסטי האתר ונתוני גלישה';
      t.title = 'תפריט המנהל של האתר';
      t.onclick = function (e) { e.stopPropagation(); try { ddClose(); } catch (x) { /* */ } var m = Dc.getElementById('lk-mb'); if (m) m.click(); };
      X.appendChild(t);
    }
    var tf = Dc.getElementById('tostrifab'), mine = Dc.getElementById('admtri');
    if (tf) {
      tf.classList.add('tb-moved');
      if (!mine) { mine = Dc.createElement('button'); mine.id = 'admtri'; mine.type = 'button'; mine.onclick = function () { try { tosTriOpen(); } catch (x) { tf.click(); } }; X.insertBefore(mine, X.firstChild); }
      mine.textContent = tf.textContent;
    } else if (mine) mine.remove();
    if (!Dc.getElementById('admboard')) {
      var bd = Dc.createElement('button'); bd.id = 'admboard'; bd.type = 'button'; bd.innerHTML = ic('cal') + 'לוח הדף היומי בווטסאפ';
      bd.onclick = function () { location.href = 'daf-board.html'; };
      X.appendChild(bd);
    }
  }
  var xT = 0;
  if (W.MutationObserver) {
    new MutationObserver(function () { clearTimeout(xT); xT = setTimeout(adminExtras, 60); }).observe(B, { childList: true });
    new MutationObserver(function () { clearTimeout(xT); xT = setTimeout(adminExtras, 60); }).observe(H, { childList: true });
  }
  adminExtras(); setTimeout(adminExtras, 1200); setTimeout(adminExtras, 4000);

  /* ------------------------------------------------ ד. רצועת הנחיתה מן הווטסאפ */
  function gq(lbl) {
    var s = String(lbl || '').replace(/[.:׳״'"\s]/g, '');
    if (!s) return '';
    return s.length > 1 ? s.slice(0, -1) + '"' + s.slice(-1) : s + '׳';
  }
  function curDaf() {
    try { var ds = Dc.getElementById('dafsel'), p = ds && D.pages[+ds.value || 0]; return p ? (p.label || p.daf) : ''; } catch (e) { return ''; }
  }
  function strip() {
    var q = new URLSearchParams(location.search);
    if (q.get('src') !== 'wa') return;
    /* הסימן יוצא מן הכתובת מיד, כדי ששיתוף מכאן לא יישא אותו הלאה */
    try { q.delete('src'); var qs = q.toString(); history.replaceState(history.state, '', location.pathname + (qs ? '?' + qs : '') + location.hash); } catch (e) { /* */ }
    try { if (W.LK && LK.event) LK.event('נחיתה מווטסאפ'); } catch (e) { /* */ }
    setTimeout(function () {
      if (Dc.getElementById('wastrip')) return;
      var s = Dc.createElement('div'); s.id = 'wastrip'; s.setAttribute('role', 'region'); s.setAttribute('aria-label', 'קיצור הדף היומי');
      var mas = (typeof D !== 'undefined' && D.masechet) || '';
      s.innerHTML = '<span class="wst"><span class="wsl">קיצור הדף היומי</span><span class="wsd">·</span><b>' + mas + ' ' + gq(curDaf()) + '</b></span>' +
        '<a class="wsj" href="' + WA + '" target="_blank" rel="noopener" data-join="strip">' + ic('wa') + 'הצטרפות לקבלה יומית בווטסאפ</a>' +
        '<button type="button" class="wsx" aria-label="סגירה" title="סגירה">×</button>';
      s.querySelector('.wsx').onclick = function () { s.remove(); B.classList.remove('wastrip'); remeasure(); };
      var b = Dc.getElementById('bar');
      if (b && b.parentNode === B) b.after(s); else B.insertBefore(s, B.firstChild);
      B.classList.add('wastrip'); remeasure();
    }, 450);
  }
  strip();

  /* ------------------------------------------------ ה. הסתרה בגלילה (מחשב) */
  (function () {
    var f = Dc.getElementById('flow'); if (!f) return;
    var last = 0, acc = 0, user = 0;
    /* רק גלילה של הלומד עצמו (גלגלת, מגע, מקשים) מסתירה; קפיצה לדף או לתוצאת חיפוש אינה מסתירה */
    function mark() { user = Date.now(); }
    ['wheel', 'touchmove', 'pointerdown'].forEach(function (ev) { f.addEventListener(ev, mark, { passive: true }); });
    Dc.addEventListener('keydown', function (e) { if (/^(PageDown|PageUp|ArrowDown|ArrowUp| |End|Home)$/.test(e.key)) mark(); });
    function busy() {
      if (Date.now() - user > 900) return true;
      return B.classList.contains('ed') || !!$('.bar .dd.open') || Dc.activeElement === Dc.getElementById('q') ||
        !H.classList.contains('dev-desk') || !f.classList.contains('vert') || f.classList.contains('book');
    }
    function show() { if (B.classList.contains('tbhide')) { B.classList.remove('tbhide'); } }
    f.addEventListener('scroll', function () {
      var t = f.scrollTop, d = t - last; last = t;
      if (busy()) { if (Date.now() - user <= 900) show(); acc = 0; return; }
      if (t < 40) { show(); acc = 0; return; }
      acc = (d > 0) === (acc > 0) ? acc + d : d;
      if (acc > 60) { B.classList.add('tbhide'); acc = 0; try { ddClose(); } catch (e) { /* */ } }
      else if (acc < -10) { show(); acc = 0; }
    }, { passive: true });
    /* העכבר בראש המסך מחזיר את הסרגל מיד */
    Dc.addEventListener('mousemove', function (e) { if (e.clientY < 14) show(); }, { passive: true });
    Dc.addEventListener('focusin', function (e) { if (e.target.closest && e.target.closest('#bar')) show(); });
    Dc.addEventListener('keydown', function (e) { if (e.key === 'Escape' || (e.altKey && !e.ctrlKey)) show(); });
  })();

  /* ------------------------------------------------ ו. הזוהר על הסוגיא, עזרה */
  W.zgOpen = function () {
    var d = '';
    try { var ds = Dc.getElementById('dafsel'); d = D.pages[+ds.value || 0].daf; } catch (e) { /* */ }
    var mk = d && Dc.querySelector('#flow .dafmark[data-daf="' + (W.CSS && CSS.escape ? CSS.escape(d) : d) + '"]');
    var z = mk && mk.parentElement && mk.parentElement.querySelector('.rs-zg');
    if (!z) {
      /* העמוד השני של אותו דף (ע"ב) */
      var all = Dc.querySelectorAll('#flow .rs-zg'), fr = Dc.getElementById('flow').getBoundingClientRect();
      for (var i = 0; i < all.length && !z; i++) { var r = all[i].getBoundingClientRect(); if (r.bottom > fr.top && r.top < fr.bottom) z = all[i]; }
    }
    if (z) z.click(); else say('אין ציוני זוהר על הדף הזה');
  };
  W.helpCard = function () {
    var old = Dc.getElementById('tbhelp'); if (old) { old.remove(); return; }
    var m = Dc.createElement('div'); m.className = 'modal'; m.id = 'tbhelp';
    var rows = [['היכן אני', 'בצד ימין: מסכת · פרק · דף. לחיצה על כל חלק פותחת את הבורר שלו'],
      ['Ctrl+חץ', 'דף הבא או הקודם'], ['Ctrl+פלוס / מינוס', 'הגדלה והקטנה של הגופן'], ['PageDown / רווח', 'מסך הבא'],
      ['מ', 'הגמרא בצד הדף (מקור)'], ['תוס׳', 'לחיצה מדליקה ומכבה; החץ - אופן התצוגה'], ['תצוגה', 'טור אחד או ספר, גודל הגופן, ניקוד וניגודיות'],
      ['הצע תיקון', 'סמן טקסט בדף, או לחץ על "הצע תיקון" בקצה הסרגל']];
    m.innerHTML = '<div class="box"><h3>עזרה</h3><dl>' + rows.map(function (r) { return '<dt>' + r[0] + '</dt><dd>' + r[1] + '</dd>'; }).join('') +
      '</dl><div class="btns"><button type="button" class="primary">סגירה</button></div></div>';
    m.addEventListener('click', function (e) { if (e.target === m || e.target.closest('button')) m.remove(); });
    Dc.addEventListener('keydown', function esc(e) { if (e.key === 'Escape') { m.remove(); Dc.removeEventListener('keydown', esc); } });
    B.appendChild(m);
  };

  /* מדידה מחדש אחרי שהגופנים נטענו (רוחב הבורר משתנה) */
  if (Dc.fonts && Dc.fonts.ready) Dc.fonts.ready.then(remeasure);
})();
