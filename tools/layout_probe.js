/* layout_probe.js - שכבת המדידה של סוכן סריקת התצוגה.
   נטענת לתוך הדף הבנוי, ומודדת בדפדפן את המלבנים האמיתיים. אינה משנה
   דבר בדף: כל הקריאות בלבד.

   תשעת סוגי הממצאים מוגדרים ב-docs/מנת-העבודה-הבאה.md, משימה א.
   כל ממצא נושא code, מזהה יחידה, ציון דף, ומספרים שנמדדו - כדי
   שהתיקון ייבדק מול מדידה ולא מול תחושה. */
(function () {
  'use strict';

  var SAMPLE = 'אבגדהוזחטיכךלמםנןסעפףצץקרשת';
  /* מחרוזת מנוקדת מייצגת: חולם וחיריק למעלה, קובוץ ושווא למטה, ודגש */
  var SAMPLE_NK = 'סוּכָּה שֶׁהִיא גְּבוֹהָה לְמַעְלָה מֵעֶשְׂרִים אַמָּה פְּסוּלָה';
  /* חצים וידיים מצביעות: סמני פריסה של וורד שאין להם טעם בדף */
  var ARROWS = ['◄', '►', '▶', '◀', '←', '→',
                '☚', '☛', '☜', '☝', '☞', '☟',
                '➡', '➔', '➜', '⬅', '⮕'];
  var ENT = /&(?:amp|lt|gt|quot|apos|nbsp|#x?[0-9a-fA-F]+);/;
  var PUNCT_ONLY = /^[\s.,;:!?\-'"()\[\]{}׳״–—·°]+$/;

  var cv = document.createElement('canvas');
  var ctx = cv.getContext('2d');

  function fam(s) {
    return (s.fontFamily || '').split(',')[0].replace(/["']/g, '').trim();
  }

  /* גובה הדיו נמדד בגודל גדול ומוקטן בחזרה: actualBoundingBox חוזר
     מעוגל לפיקסל שלם, ובגודל האמיתי הוא מעגל 16.5 ל-17 ו-16.6 ל-18,
     והיחס שנבדק חסר מובן. בארבע מאות פיקסל השגיאה היא רבע אחוז. */
  var REF = 400;
  function metrics(el) {
    var s = getComputedStyle(el);
    var fs = parseFloat(s.fontSize) || 16;
    ctx.font = s.fontStyle + ' ' + s.fontWeight + ' ' + REF + 'px ' + s.fontFamily;
    var big = ctx.measureText(SAMPLE);
    var inkBig = (big.actualBoundingBoxAscent || 0) + (big.actualBoundingBoxDescent || 0);
    ctx.font = s.fontStyle + ' ' + s.fontWeight + ' ' + s.fontSize + ' ' + s.fontFamily;
    var m = ctx.measureText(SAMPLE);
    return {
      ink: inkBig / REF * fs,
      asc: m.fontBoundingBoxAscent || m.actualBoundingBoxAscent || 0,
      desc: m.fontBoundingBoxDescent || m.actualBoundingBoxDescent || 0,
      fs: parseFloat(s.fontSize) || 0,
      weight: s.fontWeight,
      family: fam(s)
    };
  }

  /* קו הבסיס של מלבן-שורה: המלבן הוא תיבת השורה, וקו הבסיס יושב בתוכה
     לפי מדדי הגופן עצמו. בלי זה השוואה בין שני גדלי גופן חסרת מובן. */
  function baseline(rect, m) {
    var box = m.asc + m.desc;
    var h = rect.bottom - rect.top;
    return rect.top + (h - box) / 2 + m.asc;
  }

  function rectOf(el) {
    var r = el.getClientRects();
    return r.length ? r[0] : null;
  }

  function textNodes(el) {
    var w = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, null, false);
    var out = [], n;
    while ((n = w.nextNode())) if (n.nodeValue && n.nodeValue.trim()) out.push(n);
    return out;
  }

  /* מלבני השורות של אלמנט: כל קטעי-התו נמדדים, ואז מאוחדים לשורות.
     האיחוד אינו לפי top בלבד - בטורים יש שורות באותו גובה בטורים שונים,
     ואיחודן היה מוליד "שורה" ברוחב העמוד. */
  function lineBoxes(el) {
    var ns = textNodes(el), r = document.createRange(), raw = [], i, j, b, bs;
    for (i = 0; i < ns.length; i++) {
      r.selectNodeContents(ns[i]);
      bs = r.getClientRects();
      for (j = 0; j < bs.length; j++) {
        b = bs[j];
        if (b.height > 0.5 && b.width > 0.05)
          raw.push({ top: b.top, bottom: b.bottom, left: b.left, right: b.right });
      }
    }
    raw.sort(function (a, c) { return (a.top - c.top) || (a.left - c.left); });
    var lines = [], L;
    for (i = 0; i < raw.length; i++) {
      b = raw[i]; L = lines[lines.length - 1];
      var h = b.bottom - b.top;
      if (L && Math.abs(b.top - L.top) <= Math.max(2, L.h * 0.4) &&
          b.left < L.right + L.h * 3 && b.right > L.left - L.h * 3) {
        L.top = Math.min(L.top, b.top); L.bottom = Math.max(L.bottom, b.bottom);
        L.left = Math.min(L.left, b.left); L.right = Math.max(L.right, b.right);
        L.h = L.bottom - L.top;
      } else lines.push({ top: b.top, bottom: b.bottom, left: b.left, right: b.right, h: h });
    }
    return lines;
  }

  var HEAD_CLS = ['perek-num', 'perek-name', 'perek-range', 'perek-start', 'hadran', 'dh', 'nose'];
  var PEREK = ['perek-num', 'perek-name', 'perek-range', 'perek-start', 'hadran'];

  function kindOf(row) {
    for (var i = 0; i < HEAD_CLS.length; i++)
      if (row.classList.contains(HEAD_CLS[i])) return HEAD_CLS[i];
    if (row.querySelector('.main.hatz')) return 'hatz';
    if (row.querySelector('.main.mishna')) return 'mishna';
    return 'body';
  }

  /* המרווח שהבנייה התכוונה לו, בחצאי שורה. המחלקות b0-b4 ו-a0-a4
     נגזרו מ-w:spacing שבסגנון הוורד ועוגלו לחצאי שורה, ולכן הן
     המידה הנכונה להשוות אליה - לא הנקודות הגולמיות. */
  function halves(el, which) {
    var re = new RegExp('(?:^| )' + which + '([0-4])(?: |$)'), n = null, e = el;
    while (e && !n) {
      var m = re.exec(e.className || '');
      if (m) n = +m[1];
      if (e.classList && e.classList.contains('row')) break;
      e = e.parentElement;
    }
    return n || 0;
  }

  /* תפקיד הפסקה כפי שהוא בוורד, לצורך המרווח המותר */
  function roleOfPara(p, rowKind) {
    if (rowKind !== 'body' && rowKind !== 'mishna') return rowKind;
    if (rowKind === 'mishna') return 'mishna';
    var c = (p.className || '').trim();
    if (c === 'sp') return 'body-sp';
    if (c === 'nk') return 'body-nk';
    if (c === 'hr') return 'body-hr';
    if (c === 'in') return 'body-in';
    return 'body';
  }

  function unitOf(el) {
    var r = el.closest ? el.closest('.row') : null;
    return r && r.id ? r.id.replace(/^u/, '') : '';
  }

  function dafOf(row) {
    /* ציון הדף האחרון שנכתב לפני היחידה הזאת, לצורך הדיווח */
    var n = row, d;
    while (n) {
      d = n.querySelector && n.querySelector('.dafmark');
      if (d && d.textContent.trim()) return d.textContent.trim();
      n = n.previousElementSibling;
    }
    var sh = row.closest ? row.closest('.sheet') : null;
    if (sh) { var x = sh.querySelector('.shhd .df'); if (x) return x.textContent.trim(); }
    return '';
  }

  function inter(a, b) {
    var w = Math.min(a.right, b.right) - Math.max(a.left, b.left);
    var h = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
    return (w > 0.5 && h > 0.5) ? { w: w, h: h } : null;
  }

  function railKids(rail) {
    var out = [], k = rail.children, i, r;
    for (i = 0; i < k.length; i++) {
      r = rectOf(k[i]);
      if (!r || r.height < 0.5) continue;
      if (!k[i].textContent.trim() && r.width < 0.5) continue;
      out.push({ el: k[i], rect: r, cls: k[i].className || k[i].tagName.toLowerCase() });
    }
    return out;
  }

  /* ================= הסריקה ================= */
  window.__lgAudit = function (cfg) {
    cfg = cfg || {};
    var RS = cfg.roleSpacing || {};
    var bodyPt = cfg.bodyPt || 9;
    var flow = document.getElementById('flow');
    var F = [], fonts = {};
    function add(code, row, msg, num) {
      F.push({ code: code, unit: row ? unitOf(row) : '', daf: row ? dafOf(row) : '',
               kind: row ? kindOf(row) : '', msg: msg, num: num || null,
               rect: row ? (function (r) {
                 return { x: r.left, y: r.top, w: r.width, h: r.height };
               })(row.getBoundingClientRect()) : null });
    }

    /* --- הגוף: גודל, שורה, ומכפיל נקודה-לפיקסל --- */
    /* פסקת גוף אמיתית: ללא class משלה, ובתוך .main שאין לו class נוסף.
       בלעדי התנאי השני נבחרה פסקת משנה - שגופנה וילנא מודגש - והיחס
       שנמדד מול הכותרות היה חסר מובן. */
    var ps = flow.querySelectorAll('.main p'), bodyP = null, i, j, k;
    for (i = 0; i < ps.length; i++)
      if (!ps[i].className && (ps[i].parentElement.className || '').trim() === 'main' &&
          ps[i].textContent.trim().length > 20) { bodyP = ps[i]; break; }
    if (!bodyP)
      for (i = 0; i < ps.length; i++)
        if ((ps[i].parentElement.className || '').trim() === 'main') { bodyP = ps[i]; break; }
    if (!bodyP) bodyP = ps[0] || flow.querySelector('.main');
    if (!bodyP) return { lh: 0, findings: [], heads: {}, fonts: {}, rows: 0, note: 'אין תוכן' };
    var bs = getComputedStyle(bodyP);
    var bodyFs = parseFloat(bs.fontSize) || 16;
    var LH = parseFloat(bs.lineHeight);
    if (!LH || isNaN(LH)) LH = bodyFs * 1.15;
    var PPP = bodyFs / bodyPt;            /* פיקסל לנקודה */
    function px(pt) { return (pt || 0) * PPP; }

    /* --- 8. יחס הכותרות: גובה האותיות הנראה בפועל --- */
    var heads = {};
    function measureCls(sel, name) {
      var el = flow.querySelector(sel);
      if (!el) return;
      var m = metrics(el);
      heads[name] = { ink: m.ink, fs: m.fs, weight: m.weight, family: m.family,
                      lh: parseFloat(getComputedStyle(el).lineHeight) || 0 };
    }
    heads.body = (function () {
      var m = metrics(bodyP);
      return { ink: m.ink, fs: m.fs, weight: m.weight, family: m.family, lh: LH };
    })();
    measureCls('.main.nose', 'nose');
    measureCls('.main.dh', 'dh');
    measureCls('.main.mishna', 'mishna');
    var TOL = 1.02;
    /* היחסים הקבועים (הכרעת 6.10.2026): משנה = גוף ביחס 11/9 (הועלתה בשתי נקודות),
       ד"ה משנה = משנה, ונושא אינו גדול מד"ה משנה. */
    if (heads.nose && heads.dh && heads.nose.ink > heads.dh.ink * TOL)
      F.push({ code: 8, unit: '', daf: '', kind: 'nose',
               msg: 'גובה האותיות של נושא ' + heads.nose.ink.toFixed(1) +
                    ' מול ד"ה משנה ' + heads.dh.ink.toFixed(1) + ' (נושא אינו גדול מד"ה משנה)',
               num: { ink: heads.nose.ink, max: heads.dh.ink }, rect: null });
    if (heads.dh && heads.mishna && Math.abs(heads.dh.ink - heads.mishna.ink) > heads.mishna.ink * 0.03)
      F.push({ code: 8, unit: '', daf: '', kind: 'dh',
               msg: 'גובה האותיות של ד"ה משנה ' + heads.dh.ink.toFixed(1) +
                    ' מול משנה ' + heads.mishna.ink.toFixed(1) + ' (ד"ה משנה זהה למשנה)',
               num: { ink: heads.dh.ink, max: heads.mishna.ink }, rect: null });
    if (heads.mishna && Math.abs(heads.mishna.ink - heads.body.ink * 11 / 9) > heads.body.ink * 11 / 9 * 0.03)
      F.push({ code: 8, unit: '', daf: '', kind: 'mishna',
               msg: 'גובה האותיות של משנה ' + heads.mishna.ink.toFixed(1) +
                    ' מול גוף ' + heads.body.ink.toFixed(1) + ' (המשנה אמורה להיות גדולה בשתי נקודות: ' +
                    (heads.body.ink * 11 / 9).toFixed(1) + ')',
               num: { ink: heads.mishna.ink, max: heads.body.ink * 11 / 9 }, rect: null });
    var tnEl = flow.querySelector('.main.mishna .am');
    if (tnEl && heads.mishna) {
      var tm = metrics(tnEl), want = heads.mishna.ink * 9 / 11;
      if (Math.abs(tm.ink - want) > want * 0.04)
        F.push({ code: 8, unit: '', daf: '', kind: 'mishna',
                 msg: 'תנאי המשנה ' + tm.ink.toFixed(1) + ' מול משנה ' + heads.mishna.ink.toFixed(1) +
                      ' (אמור להיות קטן בשתי נקודות: ' + want.toFixed(1) + ')',
                 num: { ink: tm.ink, max: want }, rect: null });
    }
    /* line-height שאינו של רשת הגוף - שורש השורות הלבנות המדומות */
    ['nose', 'dh', 'mishna'].forEach(function (n) {
      /* משנה וד"ה משנה בזרימה על המסך מקבלות שורה גבוהה מרשת הגוף, בכוונה (ניקוד גדול
         מתיבת השורה); רק שורה נמוכה מרשת הגוף, או גבוהה מ-1.3 ממנה, היא ממצא */
      var tallOk = (n === 'mishna' || n === 'dh') && heads[n].lh >= LH - 0.6 && heads[n].lh <= LH * 1.3;
      if (heads[n] && heads[n].lh && !tallOk && Math.abs(heads[n].lh - LH) > 0.6)
        F.push({ code: 8, unit: '', daf: '', kind: n,
                 msg: 'מרווח השורה של ' + n + ' הוא ' + heads[n].lh.toFixed(2) +
                      ' ואינו רשת הגוף ' + LH.toFixed(2),
                 num: { lh: heads[n].lh, body: LH }, rect: null });
    });

    /* --- מעבר על כל היחידות --- */
    var rows = flow.querySelectorAll('.row');
    var ordered = [];       /* כל שורות הטקסט בדף, בסדר המסמך, לסוג 2 */
    for (i = 0; i < rows.length; i++) {
      var row = rows[i];
      var rail = row.querySelector(':scope > .rail');
      var main = row.querySelector(':scope > .main');
      if (!main) continue;
      var kind = kindOf(row);
      var mrect = main.getBoundingClientRect();
      var mlines = lineBoxes(main);
      var kids = rail ? railKids(rail) : [];

      /* 1. חלל-מסילה
         גובה הטקסט נמדד משורות הטקסט עצמן ולא מן האלמנט: בגריד פריטי
         השורה נמתחים לגובה הגבוה שביניהם, ולכן .main תמיד בגובה המסילה
         והבדיקה היתה מחזירה אפס גם כשהעין רואה חלל. */
      if (kids.length && mlines.length) {
        var rt = Infinity, rb = -Infinity;
        for (j = 0; j < kids.length; j++) {
          rt = Math.min(rt, kids[j].rect.top); rb = Math.max(rb, kids[j].rect.bottom);
        }
        var railH = rb - rt;
        /* גובה הטקסט הוא מספר שורותיו ברשת, ולא מרווח הדיו שלהן: פסקה
           שיש בה קטע קטן יותר נותנת תיבות נמוכות, וחלון שנפרש כדין על
           שתי שורות היה נראה כאילו הוא מגביה את היחידה. */
        var textH = Math.max(mlines[mlines.length - 1].bottom - mlines[0].top,
                             mlines.length * LH);
        if (railH > textH + 0.2 * LH)
          add(1, row, 'גובה המסילה ' + railH.toFixed(1) + ' מול גובה הטקסט ' +
                      textH.toFixed(1) + ' (' + ((railH - textH) / LH).toFixed(2) +
                      ' שורה עודפת, ' + mlines.length + ' שורות טקסט)',
              { rail: railH, text: textH, row: mrect.height, lines: (railH - textH) / LH });
      }

      /* 3. חלון-לא-בשורתו
         קו הבסיס נמדד על תיבת השורה הראשונה של הטקסט שבתוך הסמן, ולפי
         מדדי הגופן של האלמנט שנושא את הטקסט בפועל. מדידה על העוטף עצמו
         נתנה מדדי גופן אחרים (הוא יורש פרנקריהל, והחלון הוא וילנא),
         והפרש מדומה של חצי שורה. */
      if (kids.length && mlines.length) {
        var mb = baseline(mlines[0], metrics(main));
        for (j = 0; j < kids.length; j++) {
          var kt = textNodes(kids[j].el);
          var khost = kt.length ? kt[0].parentElement : kids[j].el;
          var kls = lineBoxes(kids[j].el);
          var krect = kls.length ? kls[0] : kids[j].rect;
          var kb = baseline(krect, metrics(khost));
          var d = Math.abs(kb - mb);
          if (d > 0.15 * LH)
            add(3, row, 'סמן הצד "' + kids[j].cls + '" רחוק ' + (d / LH).toFixed(2) +
                        ' שורה מקו הבסיס של השורה הראשונה',
                { cls: kids[j].cls, lines: d / LH, px: d });
        }
      }

      /* 4. חפיפה */
      for (j = 0; j < kids.length; j++) {
        for (k = j + 1; k < kids.length; k++)
          if (inter(kids[j].rect, kids[k].rect))
            add(4, row, 'שני סמני צד נחתכים: ' + kids[j].cls + ' ו' + kids[k].cls);
        if (inter(kids[j].rect, mrect))
          add(4, row, 'סמן הצד ' + kids[j].cls + ' נחתך עם הטקסט');
      }

      /* 5. חלון-קטוע */
      for (j = 0; j < kids.length; j++) {
        var e = kids[j].el;
        if (e.scrollWidth > e.clientWidth + 1)
          add(5, row, 'סמן הצד "' + kids[j].cls + '" נחתך: רוחב התוכן ' + e.scrollWidth +
                      ' והמקום ' + e.clientWidth + ' [' + e.textContent.trim().slice(0, 28) + ']',
              { scroll: e.scrollWidth, client: e.clientWidth });
      }

      /* 7. גלישה */
      for (j = 0; j < mlines.length; j++) {
        if (mlines[j].right > mrect.right + 1.5 || mlines[j].left < mrect.left - 1.5)
          add(7, row, 'שורה חורגת ממידת הטקסט ב-' +
                      Math.max(mlines[j].right - mrect.right, mrect.left - mlines[j].left).toFixed(1) +
                      ' פיקסל');
      }
      if (main.scrollWidth > main.clientWidth + 1)
        add(7, row, 'גלילה אופקית בתוך הטקסט: ' + main.scrollWidth + ' מול ' + main.clientWidth);
      /* הטקסט חייב לשבת בתוך השורה שלו. כך נתפסת פריסה שנשברה כולה -
         למשל שאילתת טלפון שבוטלה, שהוציאה את הטקסט מחוץ למסך. */
      var rrect = row.getBoundingClientRect();
      if (mrect.left < rrect.left - 2 || mrect.right > rrect.right + 2)
        add(7, row, 'הטקסט חורג ממסגרת השורה: ' +
                    (mrect.left - rrect.left).toFixed(1) + ' מימין, ' +
                    (rrect.right - mrect.right).toFixed(1) + ' משמאל');

      /* 6. סימן בלי טעם */
      var tns = textNodes(row);
      for (j = 0; j < tns.length; j++) {
        var t = tns[j].nodeValue, host = tns[j].parentElement, a;
        for (k = 0; k < ARROWS.length; k++)
          if (t.indexOf(ARROWS[k]) > -1) {
            add(6, row, 'סמן חץ או יד בטקסט המוצג (U+' +
                        ARROWS[k].charCodeAt(0).toString(16).toUpperCase() + ')');
            break;
          }
        if (t.indexOf('\t') > -1) add(6, row, 'תו טאב בטקסט המוצג');
        if (t.indexOf('�') > -1) add(6, row, 'תו החלפה U+FFFD בטקסט המוצג');
        if (ENT.test(t)) add(6, row, 'ישות HTML בטקסט המוצג: ' + t.match(ENT)[0]);
        /* גופן וגליפים: נאסף כאן ונבדק בפייתון מול ה-cmap */
        var hcs = getComputedStyle(host);
        var f = fam(hcs) + '|' + hcs.fontWeight;
        if (!fonts[f]) fonts[f] = {};
        for (k = 0; k < t.length; k++) {
          var ch = t[k];
          if (ch === ' ' || ch === '\n') continue;
          fonts[f][ch] = 1;
        }
      }
      /* פסקה שכל תוכנה פיסוק */
      for (j = 0; j < mlines.length; j++) { /* noop - נבדק על הפסקה עצמה */ }
      var paras = main.querySelectorAll('p');
      var plist = paras.length ? paras : [main];
      /* יחידה בלי טקסט כלל היא שורה ריקה בדף (ב: ציון דף או חלון שאין
         תחתיהם טקסט). אחרי המנה אין כאלה. */
      if (!main.textContent.replace(/‏/g, '').trim())
        add(2, row, 'יחידה ריקה - אין בה טקסט' +
            (row.querySelector('.dafmark') ? ' (ציון דף: ' + row.querySelector('.dafmark').textContent.trim() + ')' : '') +
            (row.querySelector('.anchor') ? ' (חלון: ' + row.querySelector('.anchor').textContent.trim().slice(0, 20) + ')' : ''));
      for (j = 0; j < plist.length; j++) {
        var isHz = kind === 'hatz' || plist[j].classList.contains('hatz');
        var pt = plist[j].textContent.replace(/‏/g, '').trim();
        if (pt && PUNCT_ONLY.test(pt) && !isHz)
          add(6, row, 'שורה שכל תוכנה פיסוק: [' + pt.slice(0, 20) + ']');
        /* פסקה שכולה כוכביות ואינה חציצה - פגם; כוכבית בתוך טקסט - מידע
           לבקרה בלבד (א6), ולכן סוג נפרד. */
        if (!isHz && /^[*\s∗⁎٭✱＊ ]+$/.test(pt))
          add(6, row, 'פסקה שכולה כוכביות מוצגת ככוכביות ולא כעיטור');
        else if (!isHz && /[*∗⁎٭✱＊]/.test(pt))
          add(11, row, 'כוכבית בתוך שורת טקסט (לא נגעה, לבקרה בלבד)');
        /* עיטור החציצה: חייב להיות העיטור של סוכה - שלוש כוכביות שגופן
           וילנא הופך לעיטור האמצעי. הרוחב נמדד מול רוחב העיטור בגופן
           שבפועל; כוכביות גולמיות רחבות ממנו בהרבה, ותו חסר צר ממנו. */
        if (isHz) {
          var hz = plist[j];
          var ms = getComputedStyle(hz);
          ctx.font = ms.fontStyle + ' ' + ms.fontWeight + ' ' + ms.fontSize + ' ' + ms.fontFamily;
          var ref = ctx.measureText('***').width;
          var raw = ctx.measureText('*').width * 3;
          var rg = document.createRange(); rg.selectNodeContents(hz);
          var hb = rg.getBoundingClientRect();
          var got = hb.width;
          var fam0 = fam(ms);
          if (pt !== '***')
            add(6, row, 'חציצה שאינה שלוש כוכביות: [' + pt.slice(0, 12) + ']');
          else if (fam0 !== 'Vilna' || ms.fontWeight !== '900')
            add(6, row, 'חציצה בגופן ' + fam0 + ' משקל ' + ms.fontWeight + ' ולא וילנא 900');
          else if (Math.abs(ref - raw) < 0.5)
            add(6, row, 'ליגטורת העיטור אינה פעילה בגופן: רוחב *** ' + ref.toFixed(1) + ' = שלוש כוכביות');
          else if (Math.abs(got - ref) > ref * 0.15)
            add(6, row, 'החציצה אינה ברוחב העיטור: ' + got.toFixed(1) + ' מול ' + ref.toFixed(1),
                { got: got, ref: ref });
        }
      }

      /* איסוף שורות הטקסט לסוג 2 */
      for (j = 0; j < plist.length; j++) {
        var role = roleOfPara(plist[j], kind);
        var ls = lineBoxes(plist[j]);
        for (k = 0; k < ls.length; k++)
          ordered.push({ L: ls[k], role: role, row: row, sheet: row.closest('.sheet') || null,
                         el: plist[j], lh: parseFloat(getComputedStyle(plist[j]).lineHeight) || LH,
                         bh: halves(plist[j], 'b'), ah: halves(plist[j], 'a') });
      }
      for (j = 0; j < kids.length; j++) {
        /* סמני הצד אינם שורות טקסט של הגוף, ואינם נכנסים לרשת */
      }
    }

    /* --- 2. שורה לבנה --- */
    for (i = 1; i < ordered.length; i++) {
      var A = ordered[i - 1], B = ordered[i];
      if (A.sheet !== B.sheet) continue;
      /* גוש פתיחת פרק וסיומו: המנה אוסרת לגעת בגודלם ובמרווח השורה
         שלהם, ולכן הרווח סביבם הוא מכוון ואינו פגם. */
      if (PEREK.indexOf(A.role) > -1 || PEREK.indexOf(B.role) > -1) continue;
      if (B.L.top <= A.L.top + 0.2) continue;                  /* טור חדש */
      if (B.L.left > A.L.right + LH || B.L.right < A.L.left - LH) continue;
      /* הרווח נמדד בין קווי הבסיס פחות שורה אחת, ולא בין קצות התיבות:
         שורה שיש בה קטע קטן יותר (הסבר ורקע) מקבלת תיבה נמוכה, ומדידת
         קצוות היתה מדווחת עליה כרווח שאינו קיים. */
      var gap = (baseline(B.L, metrics(B.el)) - baseline(A.L, metrics(A.el))) - LH;
      /* המרחק הצפוי בין שני קווי בסיס הוא ממוצע שתי תיבות השורה, ולכן
         שורה שמרווח השורה שלה גדול משלה (פתיחת פרק) אינה פגם. */
      var expect = Math.max(0, (A.lh + B.lh) / 2 - LH);
      /* סובלנות של רבע שורה: קטע מודגש או מנוקד בתוך שורה משנה את
         גובה התיבה בשבריר, וזה אינו רווח שהעין רואה. */
      var allow = (0.25 + (A.ah + B.bh) * 0.5) * LH + expect;
      if (gap > allow) {
        /* רווח שנובע מציון דף שאין תחתיו טקסט אינו פגם בקוד אלא בתוכן
           הוורד, והוא מדווח ככזה כדי שיעבור לרשימת ההגהה. */
        var why = '', e = A.row.nextElementSibling;
        while (e && e !== B.row) {
          var em = e.querySelector(':scope > .main');
          if (em && !em.textContent.trim()) {
            var dm = e.querySelector('.dafmark'), an = e.querySelector('.anchor');
            if (dm && dm.textContent.trim())
              why = ' (ציון דף שאין תחתיו טקסט: ' + dm.textContent.trim() + ')';
            else if (an && an.textContent.trim())
              why = ' (חלון שאין תחתיו טקסט: ' + an.textContent.trim().slice(0, 20) + ')';
          }
          e = e.nextElementSibling;
        }
        add(2, B.row, 'רווח לבן של ' + (gap / LH).toFixed(2) + ' שורה בין ' + A.role +
                      ' ל' + B.role + ', והמותר ' + (allow / LH).toFixed(2) + why,
            { gap: gap / LH, allow: allow / LH, from: A.role, to: B.role, why: why });
      }
    }

    /* --- 10. ניקוד חתוך או חופף ---
       הניקוד מוסיף לגובה האותיות מלמעלה ומלמטה. אם גובה הדיו של שורה
       מנוקדת עולה על תיבת השורה, הניקוד של שורה אחת נוגע באותיות
       שמעליה. נמדד ב-canvas על מחרוזת מנוקדת, בגופן ובגודל שבפועל. */
    var mm = flow.querySelector('.main.mishna');
    if (mm) {
      var mcs = getComputedStyle(mm);
      var mfs = parseFloat(mcs.fontSize) || bodyFs;
      var mlh = parseFloat(mcs.lineHeight) || LH;
      ctx.font = mcs.fontStyle + ' ' + mcs.fontWeight + ' ' + REF + 'px ' + mcs.fontFamily;
      var mk = ctx.measureText(SAMPLE_NK);
      var inkNk = ((mk.actualBoundingBoxAscent || 0) + (mk.actualBoundingBoxDescent || 0)) / REF * mfs;
      heads.mishnaNikud = { ink: inkNk, lh: mlh, fs: mfs };
      if (inkNk > mlh + 0.5)
        F.push({ code: 10, unit: '', daf: '', kind: 'mishna',
                 msg: 'הניקוד של המשנה חופף: גובה הדיו ' + inkNk.toFixed(1) +
                      ' מול תיבת השורה ' + mlh.toFixed(1),
                 num: { ink: inkNk, lh: mlh }, rect: null });
      /* ניקוד שנחתך בגיליון: שורה מנוקדת שיוצאת מגבול גוף הגיליון */
      var sh0 = mm.closest('.sheet');
      if (sh0) {
        var sb0 = sh0.querySelector('.shbody');
        if (sb0 && mm.getBoundingClientRect().bottom > sb0.getBoundingClientRect().bottom + 0.5)
          F.push({ code: 10, unit: unitOf(mm), daf: '', kind: 'mishna',
                   msg: 'משנה מנוקדת נחתכת בתחתית הגיליון', num: null, rect: null });
      }
    }

    /* --- 15. משנה לא מנוקדת: מילה עברית בפסקת משנה בלי שום ניקוד.
       לא נחשבים: ראשי תיבות וקיצורים (גרש או גרשיים בצמוד), מספרים,
       וציוני מקור בסוגריים. --- */
    (function () {
      var mp = flow.querySelectorAll('.main.mishna p'), WRE = /[א-ת֑-ׇ]+/g;
      for (var a = 0; a < mp.length; a++) {
        var tx = mp[a].cloneNode(true);
        var junk = tx.querySelectorAll('.srcb,.mlabel');
        for (var z = 0; z < junk.length; z++) junk[z].remove();
        var t = tx.textContent.replace(/\([^)]*\)/g, ' ').replace(/\[[^\]]*\]/g, ' '), m, bare = [];
        while ((m = WRE.exec(t))) {
          var w = m[0], pre = t.charAt(m.index - 1), post = t.charAt(m.index + w.length);
          if (/["'׳״]/.test(pre) || /["'׳״]/.test(post)) continue;
          if (!/[א-ת]/.test(w.replace(/[֑-ׇ]/g, '')) || /[֑-ׇ]/.test(w) || w.length < 2) continue;
          bare.push(w);
        }
        if (bare.length) add(15, mp[a].closest('.row'), 'משנה לא מנוקדת: ' + bare.slice(0, 4).join(' '), { n: bare.length });
      }
    })();

    /* --- 9. ניתוק בעמוד (רק כשיש גיליונות) --- */
    var sheets = flow.querySelectorAll('.sheet');
    /* כותרת שאין אחריה תוכן כלל עד סוף הפרק (למשל "הדרן עלך" בסגנון
       נושא או ד"ה, וחציצה שלפניו) אינה כותרת יתומה: אין לה מה להיצמד
       אליו. נמדד: אלה היו רוב ממצאי סוג 9 אחרי המנה. */
    var flatRows = [];
    for (i = 0; i < sheets.length; i++) {
      var sb0 = sheets[i].querySelector('.shbody');
      if (!sb0) continue;
      for (j = 0; j < sb0.children.length; j++) flatRows.push({ el: sb0.children[j], sheet: i });
    }
    function hasContentAfter(el) {
      var f = -1;
      for (var q = 0; q < flatRows.length; q++) if (flatRows[q].el === el) { f = q; break; }
      if (f < 0) return true;
      var HEADS0 = ['nose', 'dh', 'perek-num', 'hatz'];
      for (var q2 = f + 1; q2 < flatRows.length; q2++) {
        var kq = kindOf(flatRows[q2].el);
        if (kq === 'perek-num' || PEREK.indexOf(kq) > -1) return false;   /* פרק חדש - הקודם נגמר */
        if (HEADS0.indexOf(kq) > -1) continue;
        var mq = flatRows[q2].el.querySelector(':scope > .main');
        var tq = mq ? mq.textContent.replace(/‏/g, '').trim() : '';
        /* "הדרן עלך" בסגנון גוף הוא סיום הפרק, לא תוכן שהכותרת מבטיחה */
        if (/^הדרן\s+עלך/.test(tq)) return false;
        if (tq) return true;
      }
      return false;
    }
    for (i = 0; i < sheets.length; i++) {
      var body = sheets[i].querySelector('.shbody');
      if (!body) continue;
      var brect = body.getBoundingClientRect();
      var srows = body.children, last = null, lastIdx = -1;
      for (j = 0; j < srows.length; j++) {
        var rr = srows[j].getBoundingClientRect();
        if (rr.bottom > brect.bottom + 0.5 && rr.top < brect.bottom - 0.5)
          add(9, srows[j], 'היחידה נחתכת בתחתית הגיליון ' + (i + 1) +
                           ' (גולשת ' + (rr.bottom - brect.bottom).toFixed(1) + ' פיקסל)');
        else if (rr.top >= brect.bottom - 0.5)
          add(9, srows[j], 'היחידה נמצאת מחוץ לגיליון ' + (i + 1) + ' ואינה נראית');
        if (rr.bottom <= brect.bottom + 0.5) { last = srows[j]; lastIdx = j; }
      }
      if (last && i < sheets.length - 1) {
        var lk = kindOf(last);
        /* 'הדרן' הוא סיום פרק ואין אחריו דבר; 'פרק שם' ו'דפים בפרק'
           שייכים לגוש פתיחת הפרק, שנשמר יחד ממילא. */
        var HEADS = ['nose', 'dh', 'perek-num', 'hatz'];
        var isHead = HEADS.indexOf(lk) > -1;
        var lm = last.querySelector(':scope > .main');
        var nLines = lm ? lineBoxes(lm).length : 0;
        if (isHead && lk !== 'mishna' && hasContentAfter(last))
          add(9, last, 'כותרת (' + lk + ') היא הפריט האחרון בגיליון ' + (i + 1) +
                       ', והתוכן שלה בגיליון הבא');
        if (lm && !lm.textContent.trim() && last.querySelector('.dafmark'))
          add(9, last, 'ציון דף לבדו בתחתית גיליון ' + (i + 1));
        /* כותרת שאין אחריה שתי שורות באותו גיליון */
        for (j = 0; j < srows.length; j++) {
          var kk = kindOf(srows[j]);
          if (HEADS.indexOf(kk) === -1) continue;
          /* סופרים את שורות התוכן שאחרי הכותרת באותו גיליון. אם לפני
             שנמצאו שתי שורות באה כותרת אחרת - התוכן של הכותרת הזאת
             קצר משתי שורות וכולו כאן, ואין ממצא. */
          var after = 0, closed = false;
          for (k = j + 1; k <= lastIdx; k++) {
            var kk2 = kindOf(srows[k]);
            if (HEADS.indexOf(kk2) > -1 || PEREK.indexOf(kk2) > -1) { closed = true; break; }
            var am = srows[k].querySelector(':scope > .main');
            if (am) after += lineBoxes(am).length;
            if (after >= 2) break;
          }
          /* הגיליון נגמר לפני שתי שורות: ממצא רק אם התוכן של הכותרת
             ממשיך בראש הגיליון הבא (השורה הראשונה שם אינה כותרת). */
          var contNext = false;
          if (after < 2 && !closed) {
            var nb = sheets[i + 1] ? sheets[i + 1].querySelector('.shbody') : null;
            var first = nb && nb.children.length ? nb.children[0] : null;
            if (first) {
              var kf = kindOf(first);
              var mf = first.querySelector(':scope > .main');
              var tf = mf ? mf.textContent.replace(/‏/g, '').trim() : '';
              contNext = HEADS.indexOf(kf) < 0 && PEREK.indexOf(kf) < 0 && !!tf && !/^הדרן\s+עלך/.test(tf);
            }
          }
          if (after < 2 && !closed && contNext)
            add(9, srows[j], 'לכותרת (' + kk + ') אין שתי שורות טקסט אחריה בגיליון ' + (i + 1));
        }
      }
    }


    var fout = {};
    Object.keys(fonts).forEach(function (f) { fout[f] = Object.keys(fonts[f]).join(''); });
    return { lh: LH, bodyFs: bodyFs, ppp: PPP, findings: F, heads: heads,
             fonts: fout, rows: rows.length, sheets: sheets.length };
  };

  /* --- שליטה במצב התצוגה, כדי שהסריקה תהיה זהה בכל הרצה --- */
  window.__lgSetMode = function (mode, sheets) {
    var f = document.getElementById('flow');
    if (mode === 'book' || mode === 'print-book') {
      BOOK = true; ALL = false; SHEETS = sheets || 1;
      f.classList.remove('vert');
      f.style.setProperty('--sheets', SHEETS);
    } else {
      BOOK = false; ALL = false;
      f.classList.remove('vert', 'book');
    }
    return { mode: mode, book: BOOK };
  };
  window.__lgSections = function () { return SEC.length; };
  window.__lgRender = function (i) { render(i); return true; };
  window.__lgSecInfo = function (i) {
    return { perek: SEC[i].perek || '', name: SEC[i].perekName || '',
             from: SEC[i].from, to: SEC[i].to,
             daf: D.pages[SEC[i].from] ? D.pages[SEC[i].from].daf : '' };
  };
  /* מביא יחידה אל תוך המסגרת ומחזיר את מלבנה, לצורך צילום חתוך.
     בטורים אין scrollIntoView, ולכן נעשה שימוש בפונקציה של הדף עצמו. */
  window.__lgFocus = function (unit) {
    var el = document.getElementById('u' + unit) || document.getElementById(unit);
    if (!el) return null;
    try { toEl(el); } catch (e) { try { el.scrollIntoView({ block: 'center' }); } catch (e2) {} }
    var r = el.getBoundingClientRect();
    return { x: r.left, y: r.top, w: r.width, h: r.height };
  };
  window.__lgSqDone = function () {
    var b = document.getElementById('fbtn');
    return !b || /אוחו|כבוי/.test(b.title || '');
  };
})();
