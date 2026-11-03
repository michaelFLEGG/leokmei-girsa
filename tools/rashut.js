/* רשת המקומות (פרומפט 1, 3.11.2026): שכבת קישורים דקה בין לאוקמי גירסא לנ"ך המפורש ולממלכת הזוהר.

   אינה משנה את עיצוב דף התוכן ואינה נוגעת בטקסט: רק מסמנת, בלחיצה פותחת חלונית הצצה, ומוסיפה סמנים קטנים.
   א. פסוק מזוהה בגמרא (i.ps) - לחיץ. החלונית מראה את מקום הפסוק; בנביאים וכתובים גם את הפסוק והפירוש
      המשולב מנ"ך המפורש, וכפתור "להרחבת העניין וביאורו". פסוק מן התורה: רק המקום (נ"ך המפורש אינו כולל תורה).
      הנתונים: /rashut/<מסכת>.json, שנבנה ב-tools/rashut_links.py. לפני כל סימון נבדק שהקטע שבדף הוא
      אותו קטע שזוהה בבנייה (שלד האותיות), כדי שתיקון חי בדף לא יקבל קישור של קטע אחר.
   ב. "הזוהר על סוגיא זו" - סמל קטן ליד ציון הדף שיש עליו ציוני גמרא בזוהר (נ"ך המפורש, /links/zg/<מסכת>.json).
   ג. כפתור קבוע לנ"ך המפורש בסרגל העליון, רצועה בעמוד הבית, והצעה עדינה כשעמוד נרשם כנלמד.
   ד. ספירת לחיצות בלוח נתוני הגלישה הקיים (ev "רשת|...", מונה השיתופים). */
(function () {
  'use strict';
  var W = window, D = document;
  if (W.__rashut) return; W.__rashut = 1;
  var NACH = 'https://nach.leokmei.com';
  var MORE = 'להרחבת העניין וביאורו';
  var HE = { Genesis: 'בראשית', Exodus: 'שמות', Leviticus: 'ויקרא', Numbers: 'במדבר', Deuteronomy: 'דברים', Joshua: 'יהושע', Judges: 'שופטים',
    'I Samuel': 'שמואל א', 'II Samuel': 'שמואל ב', 'I Kings': 'מלכים א', 'II Kings': 'מלכים ב', Isaiah: 'ישעיהו', Jeremiah: 'ירמיהו', Ezekiel: 'יחזקאל',
    Hosea: 'הושע', Joel: 'יואל', Amos: 'עמוס', Obadiah: 'עובדיה', Jonah: 'יונה', Micah: 'מיכה', Nahum: 'נחום', Habakkuk: 'חבקוק', Zephaniah: 'צפניה',
    Haggai: 'חגי', Zechariah: 'זכריה', Malachi: 'מלאכי', Psalms: 'תהלים', Proverbs: 'משלי', Job: 'איוב', 'Song of Songs': 'שיר השירים', Ruth: 'רות',
    Lamentations: 'איכה', Ecclesiastes: 'קהלת', Esther: 'אסתר', Daniel: 'דניאל', Ezra: 'עזרא', Nehemiah: 'נחמיה', 'I Chronicles': 'דברי הימים א',
    'II Chronicles': 'דברי הימים ב' };
  var TORAH = { Genesis: 1, Exodus: 1, Leviticus: 1, Numbers: 1, Deuteronomy: 1 };

  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function heb(n) {
    n = +n || 0;
    var L = [[400, 'ת'], [300, 'ש'], [200, 'ר'], [100, 'ק'], [90, 'צ'], [80, 'פ'], [70, 'ע'], [60, 'ס'], [50, 'נ'], [40, 'מ'], [30, 'ל'], [20, 'כ'], [10, 'י']], s = '';
    for (var i = 0; i < L.length; i++) while (n >= L[i][0]) { s += L[i][1]; n -= L[i][0]; }
    if (n === 15) return s + 'טו'; if (n === 16) return s + 'טז';
    if (s.slice(-1) === 'י' && (n === 5 || n === 6)) return s.slice(0, -1) + (n === 5 ? 'טו' : 'טז');
    return s + (n ? 'אבגדהוזחט'[n - 1] : '');
  }
  function parseRef(r) { var m = /^(.+) (\d+):(\d+)$/.exec(r || ''); return m ? { b: m[1], c: +m[2], v: +m[3], he: HE[m[1]] || m[1] } : null; }
  function refHe(p) { return p.he + ' ' + heb(p.c) + ', ' + heb(p.v); }
  function nachUrl(p) { return NACH + '/?p=' + encodeURIComponent(p.he) + '&e=' + p.c + '&v=' + p.v; }
  function admin() { try { return !!(W.LK && LK.isAdminDevice && LK.isAdminDevice()); } catch (e) { return false; } }
  function count(what) {
    if (admin() || !/(^|\.)leokmei\.com$/.test(location.hostname)) return;
    try {
      var api = (W.LK && LK.cfg && LK.cfg.api) || 'https://leokmei-suggest.m7654301.workers.dev';
      var body = JSON.stringify({ ev: 'רשת|' + what });
      if (navigator.sendBeacon) navigator.sendBeacon(api + '/stats/hit', new Blob([body], { type: 'text/plain;charset=UTF-8' }));
    } catch (e) { /* הספירה אינה מעכבת את הלומד */ }
  }
  /* השלד של tools/verses_check.skel: בלי ניקוד וגרשיים, סופיות כרגילות, בלי ו' וי' */
  var FIN = { 'ך': 'כ', 'ם': 'מ', 'ן': 'נ', 'ף': 'פ', 'ץ': 'צ' };
  function skelText(t) {
    t = String(t || '').replace(/[֑-ׇ]/g, '').replace(/(^|\s)[דוש](?=['׳])/g, '$1');
    var ws = t.match(/[א-ת]+['"׳״]?[א-ת]*/g) || [], out = '';
    for (var i = 0; i < ws.length; i++) {
      var raw = ws[i];
      if (/["״][א-ת]/.test(raw)) continue;            /* ראשי תיבות אינם חלק מפסוק */
      var w = raw.replace(/['׳"״]/g, '').replace(/[ךםןףץ]/g, function (c) { return FIN[c]; });
      if (/^אלק/.test(w)) w = 'אלה' + w.slice(3);
      if (w === 'וגו' || w === 'וגומר' || w === 'וכו' || w === 'וכתיב' || w === 'כתיב') continue;
      var s = w.replace(/[וי]/g, '');
      out += s || w;
    }
    return out;
  }

  /* ---------------------------------------------------------------- עיצוב */
  var css = [
    'i.ps.rs-ps{cursor:pointer;border-radius:3px;transition:background .15s}',
    'i.ps.rs-ps:hover{background:rgba(209,162,58,.16);box-shadow:0 1px 0 rgba(143,106,30,.55)}',
    '.rs-zg{display:flex;align-items:center;justify-content:center;margin:3px auto 0;width:18px;height:18px;border-radius:50%;border:1px solid #c9a24a;',
    '  background:#0f263b;color:#e9c35a;font:700 10px/1 Frank,serif;cursor:pointer;padding:0}',
    '.rs-zg:hover{background:#173a58}',
    '#rsPeek{position:fixed;z-index:2147483000;top:0;left:0;bottom:0;width:min(400px,92vw);background:#fffdf8;color:#1b1b1b;box-shadow:0 0 0 1px #e3dacb,0 10px 40px rgba(11,28,42,.28);',
    '  display:flex;flex-direction:column;transform:translateX(-104%);transition:transform .22s ease;direction:rtl;font-family:Frank,"Frank Ruehl CLM",serif}',
    '#rsPeek.open{transform:none}',
    '#rsPeek .rs-h{display:flex;align-items:center;gap:8px;padding:10px 14px;background:#0b1c2a;color:#f5edd6;border-bottom:2px solid #c9a24a}',
    '#rsPeek .rs-h b{flex:1;font-size:17px;color:#e9c35a}',
    '#rsPeek .rs-x{background:none;border:0;color:#f5edd6;font-size:22px;line-height:1;cursor:pointer;padding:2px 6px}',
    '#rsPeek .rs-b{flex:1;overflow:auto;padding:12px 16px;font-size:17px;line-height:1.6}',
    '#rsPeek .rs-v{font-size:19px;line-height:1.65;margin:0 0 10px}',
    '#rsPeek .rs-p{border-top:1px solid #e3dacb;padding-top:8px;color:#2b2620}',
    '#rsPeek .rs-p sup{display:none}',
    '#rsPeek .rs-dim{color:#5a534a;font-size:15px}',
    '#rsPeek .rs-li{display:block;padding:8px 0;border-bottom:1px solid #eee3cf;color:#173a58;text-decoration:none}',
    '#rsPeek .rs-li small{display:block;color:#8f6a1e;font-size:13px}',
    '#rsPeek .rs-f{padding:10px 14px;border-top:1px solid #e3dacb;background:#f7f3ea}',
    '#rsPeek .rs-go{display:block;text-align:center;background:#0b1c2a;color:#e9c35a;border:1px solid #c9a24a;border-radius:8px;padding:10px;font-size:16px;text-decoration:none}',
    '#rsPeek .rs-go:hover{background:#173a58}',
    '@media (max-width:700px){#rsPeek{top:auto;right:0;width:auto;max-height:72vh;border-radius:14px 14px 0 0;transform:translateY(104%)}#rsPeek.open{transform:none}}',
    '.rs-sis{display:inline-flex;align-items:center;margin-inline-start:6px;padding:1px 7px;border:1px solid rgba(201,162,74,.7);border-radius:12px;',
    '  color:#e9c35a!important;font:600 12px/1.5 Frank,serif;text-decoration:none!important;white-space:nowrap;flex:none}',
    '.rs-sis:hover{background:rgba(233,195,90,.15)}',
    '#mtop .rs-sis-m{margin:0;padding:4px 9px;font-size:13px;height:28px;box-sizing:border-box}',
    '.rs-strip{display:flex;align-items:center;gap:14px;max-width:620px;margin:18px auto 6px;padding:14px 18px;border:1px solid #8f6a1e;border-radius:12px;box-sizing:border-box;',
    '  background:var(--velvet-bg,radial-gradient(ellipse 80% 60% at 50% 20%,#102a42,#091827 55%,#060f18));color:#f5edd6;text-decoration:none;box-shadow:0 6px 22px rgba(0,0,0,.35);direction:rtl}',
    '@media (max-width:660px){.rs-strip{margin:16px 12px 6px}}',
    '.rs-strip img{width:32px;height:48px;flex:none;filter:drop-shadow(0 0 6px rgba(240,196,90,.35))}',
    '.rs-strip b{display:block;font:700 19px/1.3 Frank,serif;background:linear-gradient(170deg,#fbe7a1,#e6bd52 30%,#c38f2a 55%,#efcf6b 75%,#b07c1f);-webkit-background-clip:text;background-clip:text;color:transparent}',
    '.rs-strip span{font-size:14px;color:#c7bc9c}',
    '.rs-strip:hover{border-color:#e9c35a}',
    '.rs-sug{position:fixed;z-index:2147482000;bottom:96px;left:50%;transform:translateX(-50%);background:#0f263b;color:#f3ead0;border:1px solid #8f6a1e;border-radius:10px;',
    '  padding:9px 14px;font:15px Frank,serif;box-shadow:0 8px 24px rgba(0,0,0,.3);direction:rtl;max-width:92vw}',
    '.rs-sug a{color:#e9c35a;margin-inline-start:8px}',
    '.rs-sug button{background:none;border:0;color:#c9bd98;cursor:pointer;font-size:16px;margin-inline-start:6px}',
    '@media print{.rs-zg,#rsPeek,.rs-sis,.rs-sug{display:none!important}}'
  ].join('\n');
  var st = D.createElement('style'); st.textContent = css; D.head.appendChild(st);

  /* ---------------------------------------------------------------- חלונית ההצצה */
  var peek = null;
  function openPeek(title, body, foot) {
    if (!peek) {
      peek = D.createElement('aside'); peek.id = 'rsPeek'; peek.setAttribute('role', 'dialog'); peek.setAttribute('aria-label', 'הצצה');
      peek.innerHTML = '<div class="rs-h"><b></b><button type="button" class="rs-x" aria-label="סגירה">×</button></div><div class="rs-b"></div><div class="rs-f"></div>';
      D.body.appendChild(peek);
      peek.querySelector('.rs-x').onclick = closePeek;
      D.addEventListener('keydown', function (e) { if (e.key === 'Escape') closePeek(); });
      D.addEventListener('mousedown', function (e) { if (peek.classList.contains('open') && !peek.contains(e.target) && !(e.target.closest && e.target.closest('.rs-ps,.rs-zg'))) closePeek(); });
    }
    peek.querySelector('.rs-h b').textContent = title;
    peek.querySelector('.rs-b').innerHTML = body;
    var f = peek.querySelector('.rs-f'); f.innerHTML = foot || ''; f.style.display = foot ? '' : 'none';
    requestAnimationFrame(function () { peek.classList.add('open'); });
    return peek.querySelector('.rs-b');
  }
  function closePeek() { if (peek) peek.classList.remove('open'); }

  /* תוכן הפסוק מנ"ך המפורש: הפסוק מקובץ הפרק, והפירוש המשולב מן השכבה החיה */
  var chCache = {};
  function nachChapter(p) {
    var key = p.he + '-' + p.c;
    if (chCache[key]) return chCache[key];
    chCache[key] = Promise.all([
      fetch(NACH + '/' + encodeURIComponent('נך-נתונים') + '/' + encodeURIComponent(key) + '.js?rs=' + new Date().toISOString().slice(0, 10)).then(function (r) { if (!r.ok) throw 0; return r.text(); })
        .then(function (t) { var i = t.indexOf('"] = {'); return JSON.parse(t.slice(t.indexOf('{', i), t.lastIndexOf('}') + 1)); }),
      fetch(NACH + '/api/nach-live?c=' + encodeURIComponent(key)).then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; })
    ]);
    return chCache[key];
  }
  function verseFrom(html, v) {
    var box = D.createElement('div'); box.innerHTML = html || '';
    var el = box.querySelector('.zp[data-v="' + v + '"]'); if (!el) return '';
    var n = el.querySelector('.pnum'); if (n) n.remove();
    return el.textContent.trim();
  }
  function showVerse(ref) {
    var p = parseRef(ref); if (!p) return;
    count(TORAH[p.b] ? 'פסוק-תורה' : 'פסוק-נך');
    if (TORAH[p.b]) {
      openPeek(refHe(p), '<p class="rs-dim">הפסוק מן התורה. נ״ך המפורש כולל את הנביאים והכתובים בלבד.</p>', '');
      return;
    }
    var url = nachUrl(p);
    var foot = '<a class="rs-go" href="' + esc(url) + '" target="_blank" rel="noopener" data-rs="נך-מעבר">' + MORE + '</a>';
    var b = openPeek(refHe(p), '<p class="rs-dim">טוען…</p>', foot);
    nachChapter(p).then(function (r) {
      var vt = verseFrom(r[0] && r[0].zohar, p.v);
      var it = r[1] && r[1].items && r[1].items[String(p.v)];
      var pr = it && it.html ? it.html.replace(/<(script|iframe|style)[\s\S]*?<\/\1>/gi, '') : '';
      b.innerHTML = (vt ? '<p class="rs-v">' + esc(vt) + '</p>' : '') +
        (pr ? '<div class="rs-p">' + pr + '</div>' : '<p class="rs-dim">הפירוש המשולב לפסוק זה עדיין בכתיבה.</p>');
    }).catch(function () { delete chCache[p.he + '-' + p.c]; b.innerHTML = '<p class="rs-dim">לא ניתן לטעון כאן את הפסוק. הכפתור שלמטה פותח אותו בלשונית חדשה.</p>'; });
  }
  D.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('a[data-rs]');
    if (a) count(a.getAttribute('data-rs'));
  }, true);

  /* ---------------------------------------------------------------- דף מסכת */
  var SLUG = (location.pathname.match(/\/([a-z-]+)\.html$/) || [])[1];
  var isMas = !!(SLUG && D.getElementById('flow'));
  var MAP = null, ZG = null;

  function editing() { return !!D.querySelector('#flow [contenteditable="true"]'); }
  function mark() {
    if (!MAP || editing()) return;
    Object.keys(MAP).forEach(function (uid) {
      var row = D.getElementById('u' + uid); if (!row) return;
      MAP[uid].forEach(function (m) {
        var p = row.querySelector('p[data-ek="u' + uid + '.' + m[0] + '"]'); if (!p) return;
        var el = p.querySelectorAll('i.ps')[m[1]]; if (!el || el.classList.contains('rs-ps')) return;
        if (skelText(el.textContent).slice(0, 40) !== m[3]) return;   /* הקטע השתנה מאז הבנייה: לא מקשרים */
        el.classList.add('rs-ps'); el.setAttribute('data-rs-ref', m[2]);
        var pr = parseRef(m[2]); if (pr) el.title = refHe(pr);
      });
    });
    if (ZG) zgMark();
  }
  function zgMark() {
    Array.prototype.forEach.call(D.querySelectorAll('#flow .dafmark'), function (dm) {
      var list = ZG[dm.getAttribute('data-daf')];
      if (!list || !list.length) return;
      var rail = dm.parentElement; if (!rail || rail.querySelector('.rs-zg')) return;
      var b = D.createElement('button'); b.type = 'button'; b.className = 'rs-zg'; b.textContent = 'ז';
      b.title = 'הזוהר על סוגיא זו'; b.setAttribute('aria-label', 'הזוהר על סוגיא זו');
      b.onclick = function (e) {
        e.stopPropagation(); count('זוהר-על-הסוגיא');
        openPeek('הזוהר על סוגיא זו', list.map(function (z) {
          return '<a class="rs-li" href="' + esc(z[2]) + '" target="_blank" rel="noopener" data-rs="זוהר-מעבר">' + esc(z[0]) + '<small>' + esc(z[1]) + '</small></a>';
        }).join(''), '');
      };
      dm.insertAdjacentElement('afterend', b);
    });
  }
  var mt = 0;
  function soon() { clearTimeout(mt); mt = setTimeout(mark, 120); }
  if (isMas) {
    fetch('/rashut/' + SLUG + '.json').then(function (r) { return r.ok ? r.json() : null; }).then(function (j) { MAP = (j && j.u) || {}; soon(); }).catch(function () { });
    fetch(NACH + '/links/zg/' + SLUG + '.json').then(function (r) { return r.ok ? r.json() : null; }).then(function (j) { ZG = (j && j.d) || null; soon(); }).catch(function () { });
    if (W.MutationObserver) new MutationObserver(soon).observe(D.getElementById('flow'), { childList: true, subtree: true });
    D.addEventListener('click', function (e) {
      var el = e.target.closest && e.target.closest('i.ps.rs-ps');
      if (!el || editing()) return;
      e.preventDefault(); e.stopPropagation();
      showVerse(el.getAttribute('data-rs-ref'));
    }, true);
  }

  /* ---------------------------------------------------------------- האתר האח: סרגל, שער, סיום עמוד */
  function sisLink() {
    var a = D.createElement('a'); a.className = 'rs-sis'; a.href = NACH + '/'; a.target = '_blank'; a.rel = 'noopener';
    a.setAttribute('data-rs', 'נך-סרגל'); a.title = 'נ״ך המפורש - פירוש משולב על כל הנ״ך'; a.textContent = 'נ״ך';
    return a;
  }
  function sisBar() {
    var loc = D.querySelector('#bar .bg.loc');
    if (loc && !loc.querySelector('.rs-sis')) {
      loc.appendChild(sisLink());
      try { if (typeof W.barFit === 'function') W.barFit(); } catch (e) { /* */ }
    }
    /* בטלפון הסרגל העליון הוא #mtop (#bar מוסתר): הכפתור בין שם המסכת לחיפוש, באותה שורה */
    var mt = D.getElementById('mtop'), sr = mt && mt.querySelector('.msr');
    if (mt && !mt.querySelector('.rs-sis')) { var m = sisLink(); m.classList.add('rs-sis-m'); mt.insertBefore(m, sr || null); }
  }
  function homeStrip() {
    var old = D.getElementById('lmNachLink'); if (!old || D.querySelector('.rs-strip')) return;
    var a = D.createElement('a'); a.className = 'rs-strip'; a.href = NACH + '/'; a.target = '_blank'; a.rel = 'noopener'; a.setAttribute('data-rs', 'נך-שער');
    a.innerHTML = '<img src="brand/shaar-v2/shaar-zohar-96.webp" alt="" width="32" height="48"><div><b>נ״ך המפורש</b><span>פירוש משולב על כל הנביאים והכתובים, באותה דרך לימוד</span></div>';
    old.parentNode.insertBefore(a, old); old.style.display = 'none';
  }
  /* כשעמוד נרשם כנלמד (מערכת הלומד מציגה הודעה): הצעה עדינה, פעם ביום לכל היותר */
  function doneWatch() {
    if (!W.MutationObserver || !isMas) return;
    new MutationObserver(function (ms) {
      ms.forEach(function (m) {
        Array.prototype.forEach.call(m.addedNodes, function (n) {
          if (!n.classList || !n.classList.contains('lm-toast') || !/נרשם כנלמד/.test(n.textContent || '')) return;
          var day = new Date().toISOString().slice(0, 10);
          try { if (localStorage.getItem('rsSug') === day) return; localStorage.setItem('rsSug', day); } catch (e) { return; }
          setTimeout(function () {
            var b = D.createElement('div'); b.className = 'rs-sug';
            b.innerHTML = 'אחרי הגמרא, פרק בנ״ך עם פירוש משולב?<a href="' + NACH + '/" target="_blank" rel="noopener" data-rs="נך-סיום">לנ״ך המפורש</a><button type="button" aria-label="סגירה">×</button>';
            b.querySelector('button').onclick = function () { b.remove(); };
            D.body.appendChild(b); setTimeout(function () { if (b.parentNode) b.remove(); }, 14000);
          }, 2600);
        });
      });
    }).observe(D.body, { childList: true });
  }
  function boot() { if (isMas) sisBar(); homeStrip(); doneWatch(); }
  if (D.readyState === 'loading') D.addEventListener('DOMContentLoaded', boot); else boot();
  W.rashut = { showVerse: showVerse, skel: skelText };
})();
