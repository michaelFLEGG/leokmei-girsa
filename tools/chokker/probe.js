/* החוקר - בודק הכללים בתוך הדף (פרומפט "החוקר", 26.11.2026).
   מוזרק לכל מסך שהחוקר פותח. מחזיר רשימת הפרות: {rule, sev, where, text, rect}.
   כל בדיקה כאן היא כלל מ-tools/chokker/invariants.json (השדה probe). בדיקה חדשה = פונקציה חדשה כאן ושורה שם.
   הבדיקות קוראות את הדף כפי שהגולש רואה אותו (getBoundingClientRect, getComputedStyle), לא את ה-CSS. */
(function (opts) {
  opts = opts || {};
  var V = [], MAXPER = opts.maxPer || 25, cnt = {};
  function add(rule, sev, el, text, extra) {
    cnt[rule] = (cnt[rule] || 0) + 1;
    if (cnt[rule] > MAXPER) return;
    var r = el && el.getBoundingClientRect ? el.getBoundingClientRect() : null;
    var o = { rule: rule, sev: sev, text: (text || '').slice(0, 160) };
    if (r) o.rect = [Math.round(r.left), Math.round(r.top + scrollY), Math.round(r.width), Math.round(r.height)];
    if (el && el.closest) {
      var row = el.closest('.row'); var dm = null, p = row;
      while (p && !dm) { dm = p.querySelector && p.querySelector('.dafmark'); p = p.previousElementSibling; }
      if (dm) o.daf = dm.textContent.trim();
      var u = el.closest('[data-u],[data-id]'); if (u) o.unit = u.getAttribute('data-u') || u.getAttribute('data-id');
    }
    if (extra) for (var k in extra) o[k] = extra[k];
    V.push(o);
  }
  function vis(el) { var s = getComputedStyle(el); if (s.display === 'none' || s.visibility === 'hidden') return false; var r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; }
  function txt(el) { return (el.innerText || el.textContent || '').replace(/\s+/g, ' ').trim(); }
  var site = opts.site || 'leokmei';
  var flow = document.querySelector('#flow') || document.querySelector('main') || document.body;
  var rows = [].slice.call(document.querySelectorAll('#flow .row')).filter(vis);

  /* ---------- א. כללי טקסט (כל האתרים) ---------- */
  var T = txt(flow);
  var TEXTRULES = [
    ['T01-em-dash', 'high', /—/g, 'מקף ארוך אסור בכל מקום'],
    ['T02-en-dash', 'high', /–/g, 'מקף בינוני אסור בכל מקום'],
    ['T03-latin', 'med', /[A-Za-z]{2,}/g, 'אותיות לועזיות בגוף הטקסט'],
    ['T04-steinsaltz', 'high', /שטיינזלץ/g, 'אין לכתוב "שטיינזלץ"'],
    ['T05-shlad', 'high', /שלד הסוגיה/g, 'אין לכתוב "שלד הסוגיה"'],
    ['T06-gregorian', 'med', /\b(19|20)\d\d\b|ינואר|פברואר|מרץ|אפריל|יוני|יולי|אוגוסט|ספטמבר|אוקטובר|נובמבר|דצמבר/g, 'תאריך לועזי (רק תאריכים עבריים)'],
    ['T07-double-space', 'low', /[^\s] {2,}[^\s]/g, 'רווח כפול'],
    ['T08-space-before-punct', 'low', /[א-ת"'] [.,:](?=\s|$)/g, 'רווח לפני סימן פיסוק'],
    ['T09-entity', 'high', /&(amp|nbsp|quot|lt|gt|#\d+);/g, 'ישות HTML גלויה'],
    ['T10-replacement-char', 'high', /�/g, 'תו פגום (�)'],
    ['T11-final-letter-mid', 'med', /[ךםןףץ][א-ת]/g, 'אות סופית באמצע מילה'],
    ['T12-orphan-nikud', 'med', /(^|[\s.,:])[ְ-ׇּׁׂ]/g, 'ניקוד יתום']
  ];
  if (site === 'leokmei') TEXTRULES = TEXTRULES.concat([
    ['L01-lashon-acher', 'med', /לשון אחרת/g, '"איכא דאמרי" ולא "לשון אחרת"'],
    ['L02-shone-kan', 'med', /שונה כאן/g, '"שאני כאן" ולא "שונה כאן"'],
    ['L03-yesh-beineihem', 'med', /יש ביניהם/g, '"נפק"מ" ולא "יש ביניהם"'],
    ['L04-shaninu-sham', 'med', /שנינו שם/g, '"תנן שם"/"תנא שם" ולא "שנינו שם"'],
    ['L05-peliga', 'med', /(^|\s)(פליגא|פלגו|פליגי|פליג)(?=[\s.,:]|$)/g, '"חלקו/חולק" במקום פליגא/פלגו'],
    ['L06-arbab', 'low', /ארבב"ח אמר רי"ו/g, '"מרי"ו" במקום "ארבב"ח אמר רי"ו"'],
    ['L07-semicolon', 'med', /;/g, 'נקודה-פסיק - לעולם לא, אלא נקודה'],
    ['L08-mishna-letter', 'low', /(^|\s)[אבגדה]\.\s*ד"ה/g, 'מספור קטע משנה באות לפני ד"ה (הוקפא - לא להציג)']
  ]);
  /* כל יחידת טקסט בנפרד, כדי שהממצא יישא את מקומו (דף, יחידה, מלבן) */
  var UNITS = rows.length ? rows : [].slice.call(flow.querySelectorAll('p,li,h1,h2,h3,h4,td,blockquote,figcaption')).filter(vis);
  if (!UNITS.length) UNITS = [flow];
  UNITS.forEach(function (el) {
    var t = txt(el); if (!t) return;
    TEXTRULES.forEach(function (r) {
      var re = r[2]; re.lastIndex = 0; var m = re.exec(t);
      if (m) add(r[0], r[1], el, r[3] + ': …' + t.slice(Math.max(0, m.index - 30), m.index + 30) + '…');
    });
  });

  /* ---------- ב. גיאומטריה (כל האתרים) ---------- */
  var de = document.documentElement;
  if (de.scrollWidth > innerWidth + 2) add('G01-hscroll', 'high', null, 'גלילה אופקית: רוחב הדף ' + de.scrollWidth + ' מול ' + innerWidth);
  [].slice.call(document.querySelectorAll('body *')).slice(0, 6000).forEach(function (el) {
    if (!vis(el)) return; var r = el.getBoundingClientRect();
    if (r.right > innerWidth + 3 || r.left < -3) { if (getComputedStyle(el).position !== 'fixed' && !el.closest('[hidden],.lz')) add('G02-offscreen', 'med', el, 'אלמנט חורג מרוחב המסך: ' + (el.className || el.tagName)); }
  });
  [].slice.call(document.querySelectorAll('img')).forEach(function (im) { if (im.complete && im.naturalWidth === 0 && vis(im)) add('G03-broken-img', 'high', im, 'תמונה שבורה: ' + (im.getAttribute('src') || '').slice(0, 80)); });
  if (opts.mobile) [].slice.call(document.querySelectorAll('button,a,[role=button],input,select')).forEach(function (b) {
    if (!vis(b)) return; var r = b.getBoundingClientRect(); if (r.top > innerHeight * 3) return;
    if (r.width < 28 || r.height < 28) add('G04-tap-small', 'low', b, 'כפתור קטן מדי למגע (' + Math.round(r.width) + 'x' + Math.round(r.height) + '): ' + (b.title || txt(b)).slice(0, 30));
  });
  /* גופן חלופי: הגופן הראשון ברשימה לא נטען, והדפדפן צייר בגופן מערכת */
  var fams = {};
  [].slice.call(flow.querySelectorAll('p,span,b,div,h1,h2,h3,button')).slice(0, 3000).forEach(function (el) {
    if (!el.firstChild || el.firstChild.nodeType !== 3 || !el.firstChild.nodeValue.trim()) return;
    var f = getComputedStyle(el).fontFamily.split(',')[0].replace(/["']/g, '').trim(); fams[f] = (fams[f] || 0) + 1;
  });
  Object.keys(fams).forEach(function (f) {
    try { if (document.fonts && !document.fonts.check('12px "' + f + '"', 'אב')) add('G05-font-fallback', 'high', null, 'גופן לא נטען: ' + f + ' (' + fams[f] + ' רכיבים)'); } catch (e) {}
    if (site === 'leokmei' && !/vilna|frank|ptf|לאוקמי|leokmei|david/i.test(f) && fams[f] > 3) add('G06-font-foreign', 'med', null, 'גופן מחוץ למשפחות האתר: ' + f + ' (' + fams[f] + ')');
  });

  /* ---------- ג. לאוקמי - מבנה הדף ---------- */
  if (site === 'leokmei' && rows.length) {
    var prev = null, prevTxt = '', blankRun = 0;
    rows.forEach(function (row, i) {
      var main = row.querySelector('.main'), rail = row.querySelector('.rail');
      var t = main ? txt(main) : '';
      var r = row.getBoundingClientRect();
      /* שורה ריקה ברצף */
      if (!t && !row.matches('.hatz,.perek-num,.perek-name') && !row.querySelector('.dafmark')) { blankRun++; if (blankRun >= 2) add('L10-blank-run', 'high', row, 'שתי שורות ריקות ברצף'); } else blankRun = 0;
      /* שורה כפולה */
      if (t && t.length > 12 && t === prevTxt) add('L11-dup-row', 'high', row, 'שורה כפולה: ' + t.slice(0, 60));
      /* חפיפה בין שורות באותו טור */
      if (prev) { var pr = prev.getBoundingClientRect(); if (Math.abs(pr.left - r.left) < 4 && r.top < pr.bottom - 3 && r.bottom > pr.top + 3 && t) add('L12-overlap', 'high', row, 'שורות חופפות: ' + t.slice(0, 50)); }
      /* כותרת צד */
      if (rail) [].slice.call(rail.querySelectorAll('.anchor')).forEach(function (a) {
        var at = txt(a).replace(/[.:]+$/, ''); if (!at) return;
        var words = at.split(/\s+/).filter(function (w) { return w && !/^[-–]$/.test(w); });
        if (words.length > 3) add('L13-side-long', 'med', a, 'כותרת צד ארוכה מ-3 מילים: ' + at);
        var ar = a.getBoundingClientRect();
        if (main) { var mr = main.getBoundingClientRect(); if (ar.left < mr.right - 2 && ar.right > mr.left + 2 && ar.top < mr.bottom && ar.bottom > mr.top) add('L14-side-in-text', 'high', a, 'כותרת צד נכנסת לשדה הטקסט: ' + at); }
        if (a.scrollHeight > a.clientHeight + 3 || ar.height > parseFloat(getComputedStyle(row).lineHeight || 20) * 1.9) add('L15-side-two-lines', 'med', a, 'כותרת צד נשברת לשתי שורות: ' + at);
        var first = t.split(/\s+/).slice(0, words.length).join(' ').replace(/[.:]+$/, '');
        if (words.length && first && first === at) add('L16-side-repeat', 'med', a, 'הטקסט חוזר על כותרת הצד: ' + at);
        if (/\*/.test(at)) add('L17-side-star', 'low', a, 'כוכבית בכותרת צד (להחליף במעוין)');
      });
      /* כותרת נושא בלי רווח לפני */
      if (main && main.querySelector('p.nose') && prev && prevTxt) {
        var gap = r.top - prev.getBoundingClientRect().bottom; if (gap < 2 && Math.abs(prev.getBoundingClientRect().left - r.left) < 4) add('L18-heading-no-space', 'med', row, 'כותרת בלי רווח לפניה: ' + t.slice(0, 40));
      }
      /* הדרן כהערת תוס' / סליקו */
      if (/סליקו|כאן נשלמו דברי/.test(t)) add('L19-sliku', 'high', row, '"סליקו/כאן נשלמו" מוצג: ' + t.slice(0, 50));
      /* פסוק בצבע */
      [].slice.call(row.querySelectorAll('.ps,.pasuk,[data-s="פסוק"]')).forEach(function (p) { var c = getComputedStyle(p).color; if (!/rgb\(0, 0, 0\)|rgb\(17, 17, 17\)|rgb\(34, 34, 34\)/.test(c)) add('L20-pasuk-color', 'low', p, 'פסוק לא בשחור: ' + c); });
      prev = row; prevTxt = t;
    });
    /* ציוני הדף: רצף בלי קפיצות */
    var dafs = [].slice.call(document.querySelectorAll('#flow .dafmark')).map(function (d) { return txt(d); }).filter(Boolean);
    function dafNum(s) { var g = { 'א': 1, 'ב': 2, 'ג': 3, 'ד': 4, 'ה': 5, 'ו': 6, 'ז': 7, 'ח': 8, 'ט': 9, 'י': 10, 'כ': 20, 'ל': 30, 'מ': 40, 'נ': 50, 'ס': 60, 'ע': 70, 'פ': 80, 'צ': 90, 'ק': 100, 'ר': 200, 'ש': 300, 'ת': 400 }; var n = 0, side = /:/.test(s) ? 1 : 0; s.replace(/[א-ת]/g, function (c) { n += g[c] || 0; }); return n * 2 + side; }
    for (var di = 1; di < dafs.length; di++) { var a0 = dafNum(dafs[di - 1]), a1 = dafNum(dafs[di]); if (a1 && a0 && (a1 < a0 || a1 - a0 > 2)) add('L21-daf-jump', 'high', null, 'רצף ציוני הדף נשבר: ' + dafs[di - 1] + ' ← ' + dafs[di]); }
    /* פרקים: כל פרק נגמר בהדרן */
    var pn = [].slice.call(document.querySelectorAll('#flow .row.perek-name')).length;
    var hadran = (T.match(/הדרן עלך/g) || []).length;
    if (pn && hadran < pn) add('L22-hadran-missing', 'high', null, 'פרקים: ' + pn + ', שורות "הדרן עלך": ' + hadran);
    /* כותרת לפני ילדיה בסוף טור (תצוגת ספר/טורים) */
    if (document.querySelector('#flow.book,.flow.book,.flow.cols')) rows.forEach(function (row, i) {
      var main = row.querySelector('.main'); if (!main || !main.querySelector('p.nose,p.dh')) return; var nx = rows[i + 1]; if (!nx) return;
      if (Math.abs(nx.getBoundingClientRect().left - row.getBoundingClientRect().left) > 30) add('L23-heading-orphan', 'high', row, 'כותרת נותקה מילדיה בסוף טור: ' + txt(main).slice(0, 40));
    });
    /* זנב הפרק שלא נפרס */
    var lz = document.querySelectorAll('#flow .row.lz').length; if (lz) add('L24-lazy-left', 'info', null, 'שורות שלא נפרסו בסוף הסריקה: ' + lz);
  }
  return { v: V, counts: cnt, rows: rows.length, fonts: fams, url: location.href, w: innerWidth, h: innerHeight };
})
