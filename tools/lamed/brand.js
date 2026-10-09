/* lamed - מוטיב השער וסימן המותג (8.10.2026, docs/עיצוב - כחול קטיפה, זהב מלכותי ומוטיב השער).
   רכיבים: סימן המותג (SVG מוטבע, כדי שיקבל את גופן וילנא), השער הגדול, מפריד, כרטיס-שער, שער קטן, כותרת תחתונה.
   הסימן הוא העתק של "svg class=brand" מ-tools/brand/tetzuga-kivun.html (התצוגה שאושרה), בלי שינוי. */
(function () {
  'use strict';
  var LG = window.LAMED, B = LG.brand = {};
  var n = 0;
  /* סימן המותג. מזהים ייחודיים לכל הופעה, כדי ששני סימנים בדף לא יתנגשו */
  B.mark = function (opts) {
    opts = opts || {};
    var k = 'bm' + (++n), still = !!opts.still;
    return '<svg class="brand-mark" viewBox="0 0 300 400" role="img" aria-labelledby="' + k + 't"><title id="' + k + 't">לאוקמי גירסא - קיצור התלמוד הבבלי</title><defs>' +
      '<linearGradient id="' + k + 'g" x1="0" y1="0" x2=".35" y2="1"><stop offset="0" stop-color="#f9e08a"/><stop offset=".28" stop-color="#e2b847"/><stop offset=".5" stop-color="#c8942c"/><stop offset=".68" stop-color="#eccb63"/><stop offset=".85" stop-color="#b98522"/><stop offset="1" stop-color="#e9c35a"/></linearGradient>' +
      '<radialGradient id="' + k + 'w" cx=".5" cy=".46" r=".55"><stop offset="0" stop-color="#f3cf6a" stop-opacity=".28"/><stop offset=".55" stop-color="#d9a73a" stop-opacity=".08"/><stop offset="1" stop-color="#d9a73a" stop-opacity="0"/></radialGradient>' +
      '<filter id="' + k + 'f" x="-10%" y="-10%" width="120%" height="125%" color-interpolation-filters="sRGB">' +
      '<feGaussianBlur in="SourceAlpha" stdDeviation="2.2" result="b"/>' +
      '<feSpecularLighting in="b" surfaceScale="5" specularConstant="1.05" specularExponent="18" lighting-color="#fff4cf" result="s"><feDistantLight azimuth="225" elevation="42">' +
      (still ? '' : '<animate id="' + k + 's" attributeName="azimuth" values="140;265;225" keyTimes="0;.7;1" dur="2.6s" begin="0.5s" fill="freeze"/>') +
      '</feDistantLight></feSpecularLighting>' +
      '<feComposite in="s" in2="SourceAlpha" operator="in" result="si"/><feComposite in="SourceGraphic" in2="si" operator="arithmetic" k2="1" k3=".85" result="lit"/>' +
      '<feOffset in="SourceAlpha" dx="1.98" dy="2.86" result="o"/><feGaussianBlur in="o" stdDeviation="1.76" result="ob"/><feFlood flood-color="#02070d" flood-opacity=".85"/><feComposite in2="ob" operator="in" result="sh"/>' +
      '<feMerge><feMergeNode in="sh"/><feMergeNode in="lit"/></feMerge></filter></defs>' +
      '<ellipse cx="150" cy="185" rx="165" ry="190" fill="url(#' + k + 'w)"/>' +
      '<g filter="url(#' + k + 'f)" fill="url(#' + k + 'g)" font-family="LGVilnaXB, Vilna, serif" text-anchor="middle" direction="rtl">' +
      '<text x="150" y="150" font-size="104">לאוקמי</text><text x="150" y="262" font-size="104">גירסא</text>' +
      '<g font-family="LGVilna, Vilna, serif" font-weight="700"><text x="150" y="338" font-size="30" letter-spacing="1">קיצור התלמוד הבבלי</text></g>' +
      '<path d="M34 294.5 H130 V297.5 H34Z M170 294.5 H266 V297.5 H170Z"/><path d="M150 288 l7 8 -7 8 -7 -8z M136 296 l3 -3 3 3 -3 3z M158 296 l3 -3 3 3 -3 3z"/></g></svg>';
  };
  /* "אור שתופס את הזהב": בריחוף שוב. בלי תנועה כשהמשתמש ביקש להפחית תנועה (גם ב-CSS) */
  B.arm = function (root) {
    var sv = root.querySelector('svg.brand-mark'); if (!sv) return;
    var a = sv.querySelector('animate');
    try { if (matchMedia('(prefers-reduced-motion: reduce)').matches) { if (a) a.parentNode.removeChild(a); return; } } catch (e) { }
    if (a) sv.addEventListener('mouseenter', function () { try { a.beginElement(); } catch (e) { } });
  };
  /* תמונת השער: הגרסה המתאימה לרוחב המסך (טלפון אינו מוריד גרסת מחשב). עד שהיא מגיעה - תמונה מטושטשת זעירה מוטמעת */
  B.gateImg = function () {
    return '<img class="gate-img" src="brand/shaar-v2/shaar-zohar-360.avif" data-hi="brand/shaar-v2/shaar-zohar-960.avif" data-hi2="brand/shaar-v2/shaar-zohar-1600.avif" alt="שער לאוקמי גירסא" width="560" height="843" decoding="async" fetchpriority="high" onload="var h=this.closest(\'.gate-hero\');this.classList.add(\'ld\');if(h)setTimeout(function(){h.style.backgroundImage=\'none\'},520)" onerror="if(!this.getAttribute(\'data-fb\')){this.setAttribute(\'data-fb\',1);this.src=\'brand/shaar-v2/shaar-zohar-360.webp\'}">';
  };
  /* שלב ב': אחרי שהדף נטען והדפדפן בטל, מחליפים את השער הקל בגרסה המתאימה לרוחב המסך ולרשת (רק ברשת מהירה וכשלא ביקשו חיסכון) */
  B.upgrade = function (img) {
    if (!img || img.getAttribute('data-up')) return; img.setAttribute('data-up', '1');
    var c = navigator.connection || {}, slow = c.saveData || /(^|-)2g|3g/.test(c.effectiveType || '');
    if (slow) return;
    var w = img.clientWidth * (window.devicePixelRatio || 1), url = w > 1000 && img.getAttribute('data-hi2') ? img.getAttribute('data-hi2') : img.getAttribute('data-hi');
    if (!url) return;
    var i = new Image(); i.onload = function () { img.src = url; };
    i.onerror = function () { var f = url.replace('.avif', '.webp'); if (f !== url) { var j = new Image(); j.onload = function () { img.src = f; }; j.src = f; } };
    i.src = url;
  };
  B.upgradeAll = function () {
    function go() { var im = document.querySelector('.gate-hero .gate-img'); if (im) B.upgrade(im); B.loadCards(); }
    var run = function () { if (window.requestIdleCallback) requestIdleCallback(go, { timeout: 3000 }); else setTimeout(go, 800); };
    if (document.readyState === 'complete') run(); else window.addEventListener('load', run, { once: true });
  };
  /* תמונות כרטיסי השער נטענות אחרי השער עצמו, כדי שלא יתחרו בו על הרשת */
  B.loadCards = function () {
    document.querySelectorAll('img.gimg[data-src]').forEach(function (im) { im.src = im.getAttribute('data-src'); if (im.getAttribute('data-srcset')) im.srcset = im.getAttribute('data-srcset'); im.removeAttribute('data-src'); im.removeAttribute('data-srcset'); });
  };
  /* השער הגדול הסימטרי (זהב זוהר) עם הסימן בפתחו, ואור חם בפתח */
  B.hero = function (adopt) {
    if (adopt) {   /* שער סטטי קיים: מוסיפים לו רק את הסימן בפתח */
      if (!adopt.querySelector('.opening')) { var op = document.createElement('div'); op.className = 'opening'; op.innerHTML = B.mark(); (adopt.querySelector('.gate-link') || adopt).appendChild(op); B.arm(adopt); }
      var im = adopt.querySelector('.gate-img'); if (im && im.complete) { im.classList.add('ld'); setTimeout(function () { adopt.style.backgroundImage = 'none'; }, 520); }
      B.upgradeAll();
      return adopt;
    }
    var s = document.createElement('section'); s.className = 'gate-hero'; s.setAttribute('aria-label', 'פתיחה');
    /* כניסה מיידית: לחיצה על כל אזור בשער מובילה ישר למפת הש"ס, בלי מסך ביניים */
    s.innerHTML = '<h1 class="sr-only">לאוקמי גירסא - קיצור התלמוד הבבלי</h1><a class="gate-link" href="shas.html" aria-label="כניסה למפת הש&quot;ס">' + B.gateImg() +
      '<div class="opening">' + B.mark() + '</div></a>';
    B.arm(s); B.upgradeAll();
    return s;
  };
  /* שער קטן קישוטי (alt ריק): מסכי פתיחה וסיום, הישגים */
  B.gate = function (cls) { return '<img class="gate-sm ' + (cls || '') + '" src="brand/shaar-v2/shaar-zohar-96.webp" alt="" width="64" height="96" loading="lazy" decoding="async">'; };
  /* מפריד: קו זהב נמוג ובמרכזו שער קטן */
  B.divider = function () { var d = document.createElement('div'); d.className = 'divider'; d.setAttribute('role', 'presentation'); d.innerHTML = '<img src="brand/shaar-v2/shaar-zohar-96.webp" alt="" loading="lazy" decoding="async">'; return d; };
  /* כרטיס-שער: השער הסימטרי השלם כתמונה אחת, והכיתוב בתוך הפתח (8.10.2026) */
  B.card = function (href, title, bodyHtml, extra) {
    var a = document.createElement('a'); a.className = 'gcard'; a.href = href;
    a.innerHTML = '<img class="gimg" src="data:image/gif;base64,R0lGODlhAQABAAAAACw=" data-src="brand/shaar-v2/shaar-zohar-560.avif" data-srcset="brand/shaar-v2/shaar-zohar-560.avif 560w, brand/shaar-v2/shaar-zohar-1120.avif 1120w" onerror="if(!this.getAttribute(\'data-fb\')){this.setAttribute(\'data-fb\',1);this.srcset=\'brand/shaar-v2/shaar-zohar-560.webp 560w, brand/shaar-v2/shaar-zohar-1120.webp 1120w\';this.src=\'brand/shaar-v2/shaar-zohar-560.webp\'}" sizes="(max-width:700px) 44vw, 300px" width="560" height="843" alt="" decoding="async">' +
      '<div class="gbody"><h3 class="foil">' + LG.esc(title) + '</h3>' + bodyHtml + '</div>';
    B.upgradeAll();
    return a;
  };
  /* כותרת תחתונה: כחול, שער קטן וקישורים (השורה "תנועת לאוקמי גירסא" הוסרה 8.10.2026) */
  B.footer = function () {
    var f = document.createElement('footer'); f.className = 'lm-foot';
    f.innerHTML = '<div class="lm-foot-in"><img src="brand/shaar-v2/shaar-zohar-96.webp" alt="" width="23" height="34"><span class="nm">לאוקמי גירסא</span></div>' +
      '<div style="margin-top:8px"><a href="shas.html">מפת הש"ס</a><a href="mekorot.html">מקורות</a><a href="about.html">אודות</a><a href="privacy.html">פרטיות</a></div>';
    return f;
  };
})();
