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
  /* השער הגדול הסימטרי (זהב זוהר) עם הסימן בפתחו, ואור חם בפתח */
  B.hero = function () {
    var s = document.createElement('section'); s.className = 'gate-hero'; s.setAttribute('aria-label', 'פתיחה');
    s.innerHTML = '<h1 class="sr-only">לאוקמי גירסא - קיצור התלמוד הבבלי</h1><img class="gate-img" src="brand/shaar-v2/shaar-zohar-960.webp" srcset="brand/shaar-v2/shaar-zohar-960.webp 1x, brand/shaar-v2/shaar-zohar-1600.webp 2x" alt="שער לאוקמי גירסא" width="560" height="843" decoding="async">' +
      '<div class="opening">' + B.mark() + '</div>';
    B.arm(s);
    return s;
  };
  /* שער קטן קישוטי (alt ריק): מסכי פתיחה וסיום, הישגים */
  B.gate = function (cls) { return '<img class="gate-sm ' + (cls || '') + '" src="brand/shaar-v2/shaar-zohar-96.webp" alt="" width="64" height="96" loading="lazy" decoding="async">'; };
  /* מפריד: קו זהב נמוג ובמרכזו שער קטן */
  B.divider = function () { var d = document.createElement('div'); d.className = 'divider'; d.setAttribute('role', 'presentation'); d.innerHTML = '<img src="brand/shaar-v2/shaar-zohar-96.webp" alt="" loading="lazy" decoding="async">'; return d; };
  /* כרטיס-שער: השער הסימטרי השלם כתמונה אחת, והכיתוב בתוך הפתח (8.10.2026) */
  B.card = function (href, title, bodyHtml, extra) {
    var a = document.createElement('a'); a.className = 'gcard'; a.href = href;
    a.innerHTML = '<img class="gimg" src="brand/shaar-v2/shaar-zohar-560.webp" srcset="brand/shaar-v2/shaar-zohar-560.webp 1x, brand/shaar-v2/shaar-zohar-1120.webp 2x" width="560" height="843" alt="" loading="lazy" decoding="async">' +
      '<div class="gbody"><h3 class="foil">' + LG.esc(title) + '</h3>' + bodyHtml + '</div>';
    return a;
  };
  /* כותרת תחתונה: כחול, שער קטן וקישורים (השורה "תנועת לאוקמי גירסא" הוסרה 8.10.2026) */
  B.footer = function () {
    var f = document.createElement('footer'); f.className = 'lm-foot';
    f.innerHTML = '<div class="lm-foot-in"><img src="brand/shaar-v2/shaar-zohar-96.webp" alt="" width="23" height="34"><span class="nm">לאוקמי גירסא</span></div>' +
      '<div style="margin-top:8px"><a href="shas.html">מפת הש"ס</a><a href="mekorot.html">מקורות</a><a href="about.html">אודות</a></div>';
    return f;
  };
})();
