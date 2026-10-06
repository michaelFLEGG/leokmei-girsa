/* lamed - מערכת הלומד של לאוקמי גירסא (6.10.2026).
   ליבה: כלים, אחסון מקומי של אירועים, חישוב מצב מהם, קצב ותחזית.
   הכול רץ בדפדפן, בלי מודל שפה ובלי פנייה לרשת, חוץ מסנכרון אופציונלי.

   עיקרון: נשמרים אירועים (ישיבת לימוד, סיום עמוד, סימון ידני, הגדרה), ולא רק
   סיכומים. כך אפשר לחשב מחדש, לאחד בין מכשירים בלי כפילות (לפי מזהה האירוע),
   ולתקן טעויות. נתוני הלומד שלו: הם נשמרים במכשירו, ואינם נשלחים לשום כתובת
   אלא אם ביקש סנכרון. */
(function () {
  'use strict';
  var LG = window.LAMED = window.LAMED || {};
  LG.version = 1;

  /* ------------------------------------------------------------ כלים */
  var HEB = [[400, 'ת'], [300, 'ש'], [200, 'ר'], [100, 'ק'], [90, 'צ'], [80, 'פ'], [70, 'ע'], [60, 'ס'], [50, 'נ'],
    [40, 'מ'], [30, 'ל'], [20, 'כ'], [10, 'י'], [9, 'ט'], [8, 'ח'], [7, 'ז'], [6, 'ו'], [5, 'ה'], [4, 'ד'], [3, 'ג'], [2, 'ב'], [1, 'א']];
  function heb(n) {
    n = Math.round(n);
    if (n <= 0) return '';
    var t = '';
    if (n === 15) return 'טו';
    if (n === 16) return 'טז';
    HEB.forEach(function (p) { while (n >= p[0]) { t += p[1]; n -= p[0]; } });
    return t;
  }
  /* מספר באותיות עם גרשיים (נ"ב) לשימוש בטקסט רץ */
  function hebq(n) {
    var t = heb(n);
    if (t.length > 1) t = t.slice(0, -1) + '"' + t.slice(-1);
    else if (t.length === 1) t += "'";
    return t;
  }
  function gem(s) {
    var v = 0, m = {};
    HEB.forEach(function (p) { m[p[1]] = p[0]; });
    String(s || '').replace(/[.:"'׳״]/g, '').split('').forEach(function (c) { v += m[c] || 0; });
    return v;
  }
  /* תווית עמוד: אותיות ונקודה (עמוד א) או נקודתיים (עמוד ב), כמו בדף */
  function dafLabel(n, amud) { return heb(n) + (amud ? ':' : '.'); }
  function dafNum(label) { return gem(String(label || '').replace(/[.:]/g, '')); }
  function dafAmud(label) { return String(label || '').trim().slice(-1) === ':' ? 1 : 0; }
  /* מפתח סדר מספרי של עמוד: 2a=4, 2b=5 */
  function dafKey(label) { var n = dafNum(label); return n ? n * 2 + dafAmud(label) : 0; }

  function nf(x) { return Math.round(x).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ','); }
  function pct(x) { return Math.round(x * 100) + '%'; }

  /* משך בעברית טבעית: "שעה ו-12 דקות", "כ-3 שעות", "45 דקות", "דקה" */
  function dur(ms, approx) {
    var m = Math.round(ms / 60000);
    if (m < 1) return ms >= 20000 ? 'פחות מדקה' : 'אפס דקות';
    function mins(k) { return k === 1 ? 'דקה' : (k === 2 ? 'שתי דקות' : nf(k) + ' דקות'); }
    if (m < 60) return (approx && m > 10 ? 'כ-' : '') + mins(m);
    var h = Math.floor(m / 60), r = m % 60;
    function hrs(k) { return k === 1 ? 'שעה' : (k === 2 ? 'שעתיים' : nf(k) + ' שעות'); }
    if (approx) {
      var hh = Math.round(m / 60 * 2) / 2;
      if (hh >= 10) return 'כ-' + nf(Math.round(hh)) + ' שעות';
      if (hh % 1) return 'כ-' + (hh - 0.5 === 0 ? '' : nf(hh - 0.5) + ' ') + (hh - 0.5 === 0 ? 'חצי שעה' : 'שעות וחצי');
      return 'כ-' + hrs(hh);
    }
    if (h >= 24) { return hrs(h) + (r ? ' ו-' + mins(r) : ''); }
    return hrs(h) + (r ? ' ו-' + mins(r) : '');
  }
  function days(n) { return n === 1 ? 'יום' : (n === 2 ? 'יומיים' : nf(n) + ' ימים'); }

  /* ------------------------------------------------------------ תאריכים
     ימים נחשבים לפי שעון ישראל (כולל חילופי שעון קיץ וחורף), אלא אם הלומד
     בחר אזור אחר בהגדרות. */
  var TZ = 'Asia/Jerusalem';
  LG.setTZ = function (tz) { if (tz) TZ = tz; };
  var _fmtYMD = null, _fmtTZ = '';
  function ymd(ts) {
    if (!_fmtYMD || _fmtTZ !== TZ) {
      try { _fmtYMD = new Intl.DateTimeFormat('en-CA', { timeZone: TZ, year: 'numeric', month: '2-digit', day: '2-digit' }); }
      catch (e) { TZ = 'Asia/Jerusalem'; _fmtYMD = new Intl.DateTimeFormat('en-CA', { timeZone: TZ, year: 'numeric', month: '2-digit', day: '2-digit' }); }
      _fmtTZ = TZ;
    }
    return _fmtYMD.format(new Date(ts));
  }
  function parts(ts) {
    var f = new Intl.DateTimeFormat('en-GB', { timeZone: TZ, hour: '2-digit', minute: '2-digit', weekday: 'short', hour12: false });
    var o = {};
    f.formatToParts(new Date(ts)).forEach(function (p) { o[p.type] = p.value; });
    var wd = { Sun: 0, Mon: 1, Tue: 2, Wed: 3, Thu: 4, Fri: 5, Sat: 6 }[o.weekday];
    return { h: parseInt(o.hour, 10) % 24, mi: parseInt(o.minute, 10), wd: wd };
  }
  var WD = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי', 'שישי', 'שבת'];
  function ymdToUTC(s) { var a = s.split('-'); return Date.UTC(+a[0], +a[1] - 1, +a[2]); }
  function addDays(s, n) { return new Date(ymdToUTC(s) + n * 86400000).toISOString().slice(0, 10); }
  function diffDays(a, b) { return Math.round((ymdToUTC(b) - ymdToUTC(a)) / 86400000); }
  /* תאריך עברי באותיות: כ"ה בתשרי תשפ"ז. הדפדפן נותן מספרים, והאותיות מחושבות כאן */
  function hebParts(ts) {
    try {
      var o = {};
      new Intl.DateTimeFormat('he-u-ca-hebrew-nu-latn', { timeZone: TZ, day: 'numeric', month: 'long', year: 'numeric' })
        .formatToParts(new Date(ts)).forEach(function (p) { o[p.type] = p.value; });
      return { d: parseInt(o.day, 10), m: o.month, y: parseInt(o.year, 10) };
    } catch (e) { return null; }
  }
  function hebMonthPref(m) { return /^[בוכלמשהד]/.test(m) && false ? m : 'ב' + m; }
  function hebDate(ts) {
    var p = hebParts(ts);
    return p ? hebq(p.d) + ' ' + hebMonthPref(p.m) + ' ' + hebq(p.y % 1000) : '';
  }
  function hebDateShort(ts) {
    var p = hebParts(ts);
    return p ? hebq(p.d) + ' ' + hebMonthPref(p.m) : '';
  }
  function gDate(ts) {
    var s = ymd(ts).split('-');
    return +s[2] + '.' + +s[1] + '.' + s[0];
  }
  function gDateShort(s) { var a = s.split('-'); return +a[2] + '.' + +a[1]; }
  function relDay(s, today) {
    var d = diffDays(s, today);
    if (d <= 0) return 'היום';
    if (d === 1) return 'אתמול';
    if (d === 2) return 'לפני יומיים';
    if (d < 14) return 'לפני ' + d + ' ימים';
    if (d < 60) return 'לפני ' + Math.round(d / 7) + ' שבועות';
    return 'לפני ' + Math.round(d / 30) + ' חודשים';
  }
  function uid() { return Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 9); }
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  /* נרמול טקסט לטביעת אצבע: בלי ניקוד, סימנים, סגנון */
  function fpOf(t) {
    return String(t || '').replace(/[֑-ׇ]/g, '').replace(/[^א-ת ]/g, '').replace(/\s+/g, ' ').trim().slice(0, 40);
  }

  Object.assign(LG, { heb: heb, hebq: hebq, gem: gem, dafLabel: dafLabel, dafNum: dafNum, dafAmud: dafAmud, dafKey: dafKey,
    nf: nf, pct: pct, dur: dur, days: days, ymd: ymd, parts: parts, WD: WD, addDays: addDays, diffDays: diffDays, ymdToUTC: ymdToUTC,
    hebDate: hebDate, hebDateShort: hebDateShort, gDate: gDate, gDateShort: gDateShort, relDay: relDay, uid: uid, esc: esc, fpOf: fpOf,
    tz: function () { return TZ; } });

  /* ------------------------------------------------------------ מפת הש"ס */
  /* מזהי מסכתות ושמותיהן: מן shas.js (נבנה עם האתר), ואם חסר - מן לוח הדף היומי */
  LG.shas = function () { return window.LGSHAS || { seder: [] }; };
  LG.masechtot = function () {
    var out = [];
    LG.shas().seder.forEach(function (s) { s.masechtot.forEach(function (m) { out.push(Object.assign({ seder: s.name }, m)); }); });
    return out;
  };
  LG.masechet = function (slug) { return LG.masechtot().filter(function (m) { return m.slug === slug; })[0] || null; };
  LG.nameOf = function (slug) {
    var m = LG.masechet(slug);
    if (m) return m.name;
    var d = window.LGDaf && LGDaf.list ? LGDaf.list().filter(function (x) { return x[1] === slug; })[0] : null;
    return d ? d[0] : slug;
  };
  /* העמודים של מסכת: מן הנתונים אם עלתה לאתר, אחרת טווח כללי מלוח הדף היומי */
  LG.amudim = function (slug) {
    var m = LG.masechet(slug);
    if (m && m.dafim && m.dafim.length) return m.dafim.map(function (d) { return { daf: d[0], words: d[1] }; });
    var L = window.LGDaf && LGDaf.list ? LGDaf.list().filter(function (x) { return x[1] === slug; })[0] : null;
    if (!L) return [];
    var out = [];
    for (var n = L[2]; n < L[2] + L[3]; n++) { out.push({ daf: dafLabel(n, 0), words: 0 }); out.push({ daf: dafLabel(n, 1), words: 0 }); }
    return out;
  };
  LG.avgWords = function () {
    var s = 0, c = 0;
    LG.masechtot().forEach(function (m) { (m.dafim || []).forEach(function (d) { if (d[1] > 40) { s += d[1]; c++; } }); });
    return c ? s / c : 330;
  };

  /* ------------------------------------------------------------ אחסון
     IndexedDB (אירועים), עם גיבוי ב-localStorage. פורמט עם מספר גרסה. */
  var DBN = 'lg-lamed', DBV = 1, BAK = 'lg-lamed-bak', SCHEMA = 1;
  var db = null, EV = [], BYID = {}, listeners = [], loaded = null, wipe = false;

  function lsGet(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function lsSet(k, v) { try { if (v === null) localStorage.removeItem(k); else localStorage.setItem(k, v); return true; } catch (e) { return false; } }

  function openDB() {
    return new Promise(function (res) {
      try {
        var r = indexedDB.open(DBN, DBV);
        r.onupgradeneeded = function () {
          var d = r.result;
          if (!d.objectStoreNames.contains('ev')) d.createObjectStore('ev', { keyPath: 'id' });
          if (!d.objectStoreNames.contains('meta')) d.createObjectStore('meta', { keyPath: 'k' });
        };
        r.onsuccess = function () { res(r.result); };
        r.onerror = function () { res(null); };
        r.onblocked = function () { res(null); };
      } catch (e) { res(null); }
    });
  }
  function allFrom(store) {
    return new Promise(function (res) {
      try {
        var q = db.transaction(store, 'readonly').objectStore(store).getAll();
        q.onsuccess = function () { res(q.result || []); };
        q.onerror = function () { res([]); };
      } catch (e) { res([]); }
    });
  }
  function putDB(store, obj) {
    if (!db) return;
    try { db.transaction(store, 'readwrite').objectStore(store).put(obj); } catch (e) { /* גיבוי ב-localStorage */ }
  }
  var bakT = null;
  function saveBak() {
    clearTimeout(bakT);
    bakT = setTimeout(function () {
      /* הגיבוי כולל את כל האירועים, אך מצומצם: ps נשמר רק האחרון לכל מסכת */
      var keep = compact(EV);
      var s = JSON.stringify({ schema: SCHEMA, ev: keep });
      if (s.length > 4000000) s = JSON.stringify({ schema: SCHEMA, ev: keep.slice(-3000) });
      lsSet(BAK, s);
    }, 800);
  }
  /* צמצום: מעמדות מקום ("ps") נשמר רק האחרון לכל מסכת, ו"cf" רק האחרון לכל מפתח */
  function compact(list) {
    var lastPs = {}, lastCf = {}, out = [];
    list.forEach(function (e) {
      if (e.k === 'ps') { var k = e.s || '*'; if (!lastPs[k] || lastPs[k].t < e.t) lastPs[k] = e; }
      else if (e.k === 'cf') { if (!lastCf[e.key] || lastCf[e.key].t < e.t) lastCf[e.key] = e; }
    });
    list.forEach(function (e) {
      if (e.k === 'ps') { if (lastPs[e.s || '*'] === e) out.push(e); }
      else if (e.k === 'cf') { if (lastCf[e.key] === e) out.push(e); }
      else out.push(e);
    });
    return out;
  }
  function migrate(e) { return e; }   /* הגירה בין גרסאות הפורמט: כרגע גרסה אחת */

  LG.ready = function () {
    if (loaded) return loaded;
    if (window.__lmDemo) { loaded = Promise.resolve(true); return loaded; }   /* הדגמה: בזיכרון בלבד */
    loaded = (async function () {
      db = await openDB();
      var list = db ? await allFrom('ev') : [];
      if (!list.length) {
        var b = lsGet(BAK);
        if (b) { try { list = (JSON.parse(b).ev || []); list.forEach(function (e) { putDB('ev', e); }); } catch (e) { } }
      }
      list.map(migrate).forEach(function (e) { if (e && e.id && !BYID[e.id]) { BYID[e.id] = e; EV.push(e); } });
      /* ישיבה שנקטעה בסגירת הלשונית נשמרה ב-localStorage: ממזגים אותה */
      var pend = lsGet('lg-lamed-pend');
      if (pend) {
        try { JSON.parse(pend).forEach(function (e) { LG.put(e, true); }); } catch (e) { }
        lsSet('lg-lamed-pend', null);
      }
      EV.sort(function (a, b) { return (a.t || 0) - (b.t || 0); });
      var st = LG.state();
      LG.setTZ(st.settings.tz);
      return true;
    })();
    return loaded;
  };

  function notify() { _state = null; listeners.slice().forEach(function (f) { try { f(); } catch (e) { } }); }
  LG.onChange = function (f) { listeners.push(f); };
  LG.notify = function () { EV.sort(function (a, b) { return (a.t || 0) - (b.t || 0); }); notify(); };
  /* הוספת אירוע. אירוע עם אותו מזהה מחליף את הקודם (ישיבה פתוחה מתעדכנת) */
  LG.put = function (e, quiet) {
    if (!e.id) e.id = uid();
    if (!e.t) e.t = Date.now();
    if (BYID[e.id]) { var i = EV.indexOf(BYID[e.id]); if (i > -1) EV[i] = e; }
    else EV.push(e);
    BYID[e.id] = e;
    if (!window.__lmDemo) { putDB('ev', e); saveBak(); }
    if (!quiet) notify();
    return e;
  };
  LG.events = function () { return EV.slice(); };
  /* ייצוא וייבוא: גיבוי ידני לקובץ */
  LG.exportJSON = function () { return JSON.stringify({ app: 'lamed', schema: SCHEMA, exported: new Date().toISOString(), ev: compact(EV) }, null, 1); };
  LG.importJSON = function (txt) {
    var j = JSON.parse(txt), n = 0;
    if (!j || j.app !== 'lamed' || !Array.isArray(j.ev)) throw new Error('הקובץ אינו גיבוי של מערכת הלומד');
    j.ev.forEach(function (e) { if (e && e.id && !BYID[e.id]) { LG.put(e, true); n++; } });
    EV.sort(function (a, b) { return (a.t || 0) - (b.t || 0); });
    notify();
    return n;
  };
  /* מחיקה מלאה של כל נתוני הלומד במכשיר */
  LG.wipeAll = async function () {
    wipe = true;
    EV = []; BYID = {};
    try {
      if (db) { db.close(); db = null; }
      await new Promise(function (res) { var r = indexedDB.deleteDatabase(DBN); r.onsuccess = r.onerror = r.onblocked = function () { res(); }; });
    } catch (e) { }
    ['lg-lamed-bak', 'lg-lamed-pend', 'lg-lamed-id', 'lg-lamed-sync', 'lg-lamed-last', 'lg-lamed-ob', 'lg-lamed-act'].forEach(function (k) { lsSet(k, null); });
    loaded = null;
    db = await openDB();
    notify();
  };

  /* ------------------------------------------------------------ הגדרות */
  var DEFAULTS = {
    types: [],            /* visitor, regular, yomi, scholar */
    my: [],               /* מסכתות אישיות */
    goals: {},            /* slug -> {end:'YYYY-MM-DD', minutes:N, perWeek:N} */
    clock: true, bar: true, streak: true, share: true, dark: 'auto',
    remind: { on: false, time: '06:00', browser: false },
    tz: 'Asia/Jerusalem', skipDays: [], name: '', gdoc: true, target: { 0: 10 }
  };

  /* ------------------------------------------------------------ מצב מחושב מן האירועים */
  var _state = null;
  function emptyAmud() { return { n: 0, dates: [], ms: [], active: 0, last: 0, ext: 0, extT: 0, prog: 0 }; }

  LG.state = function () {
    if (_state) return _state;
    var S = {
      settings: JSON.parse(JSON.stringify(DEFAULTS)), last: { all: null, by: {} }, amud: {}, sessions: [], editMs: 0,
      days: {}, totalMs: 0, doneEvents: [], sugg: LG.sugg || null
    };
    var cfT = {};
    var cleared = {};     /* מפתח עמוד -> זמן סימון ביטול אחרון */
    var evs = EV.slice().sort(function (a, b) { return (a.t || 0) - (b.t || 0); });
    evs.forEach(function (e) {
      if (e.k === 'un') { cleared[e.s + '|' + e.d] = Math.max(cleared[e.s + '|' + e.d] || 0, e.t); }
    });
    evs.forEach(function (e) {
      if (e.k === 'cf') {
        if (!cfT[e.key] || cfT[e.key] <= e.t) { cfT[e.key] = e.t; S.settings[e.key] = e.val; }
      } else if (e.k === 'ps') {
        var p = { s: e.s, d: e.d, pid: e.pid, fp: e.fp, rel: e.rel || 0, t: e.t };
        S.last.by[e.s] = p;
        if (!S.last.all || S.last.all.t <= e.t) S.last.all = p;
      } else if (e.k === 'ss') {
        var ses = { id: e.id, t0: e.t0 || e.t, t1: e.t1 || e.t, ms: e.ms || 0, s: e.s, per: e.per || {}, ymd: ymd(e.t0 || e.t) };
        S.sessions.push(ses);
        S.totalMs += ses.ms;
        var dd = S.days[ses.ymd] || (S.days[ses.ymd] = { ms: 0, done: 0, ext: 0 });
        dd.ms += ses.ms;
        Object.keys(ses.per).forEach(function (key) {
          var sp = key.split('|');
          var a = (S.amud[sp[0]] || (S.amud[sp[0]] = {}))[sp[1]] || (S.amud[sp[0]][sp[1]] = emptyAmud());
          a.active += ses.per[key];
          a.last = Math.max(a.last, ses.t1);
        });
      } else if (e.k === 'dn') {
        if ((cleared[e.s + '|' + e.d] || 0) > e.t) return;
        var A = S.amud[e.s] || (S.amud[e.s] = {});
        var a2 = A[e.d] || (A[e.d] = emptyAmud());
        var dy = ymd(e.t);
        if (a2.dates.indexOf(dy) < 0) { a2.dates.push(dy); a2.ms.push(e.ms || 0); a2.n++; S.doneEvents.push({ s: e.s, d: e.d, t: e.t, ymd: dy, ms: e.ms || 0, how: e.how }); (S.days[dy] || (S.days[dy] = { ms: 0, done: 0, ext: 0 })).done++; }
        else { var ix = a2.dates.indexOf(dy); a2.ms[ix] = Math.max(a2.ms[ix], e.ms || 0); }
        a2.last = Math.max(a2.last, e.t);
      } else if (e.k === 'pr') {
        var Ap = S.amud[e.s] || (S.amud[e.s] = {});
        var a3 = Ap[e.d] || (Ap[e.d] = emptyAmud());
        a3.prog = Math.max(a3.prog, e.p || 0);
      } else if (e.k === 'ex') {
        /* למדתי בשיעור או בספר: טווח עמודים, בצבע נפרד ובלי זמן */
        LG.range(e.s, e.from, e.to).forEach(function (dl) {
          if ((cleared[e.s + '|' + dl] || 0) > e.t) return;
          var A2 = S.amud[e.s] || (S.amud[e.s] = {});
          var a4 = A2[dl] || (A2[dl] = emptyAmud());
          a4.ext = 1; a4.extT = Math.max(a4.extT, e.t);
          var dy2 = ymd(e.t);
          (S.days[dy2] || (S.days[dy2] = { ms: 0, done: 0, ext: 0 })).ext++;
        });
      } else if (e.k === 'ed') {
        S.editMs += e.ms || 0;
      }
    });
    LG.setTZ(S.settings.tz);
    _state = S;
    return S;
  };
  /* כל העמודים בטווח (כולל) של מסכת, לפי סדר העמודים */
  LG.range = function (slug, from, to) {
    var list = LG.amudim(slug).map(function (a) { return a.daf; });
    var k1 = dafKey(from), k2 = dafKey(to || from);
    if (k1 > k2) { var t = k1; k1 = k2; k2 = t; }
    var out = list.filter(function (d) { var k = dafKey(d); return k >= k1 && k <= k2; });
    if (!out.length) {
      for (var k = k1; k <= k2; k++) out.push(dafLabel(Math.floor(k / 2), k % 2));
    }
    return out;
  };

  /* ------------------------------------------------------------ סטטוס עמוד וחישובים */
  /* מצב עמוד: done (נלמד במחזור הנוכחי), prog (בתהליך), ext (נלמד מחוץ לאתר), none */
  LG.cycles = function (slug) {
    var S = LG.state(), list = LG.amudim(slug);
    if (!list.length) return 0;
    var A = S.amud[slug] || {};
    var mn = Infinity;
    list.forEach(function (a) { var x = A[a.daf]; var n = x ? x.n + (x.ext && !x.n ? 1 : 0) : 0; if (n < mn) mn = n; });
    return mn === Infinity ? 0 : mn;
  };
  LG.amudInfo = function (slug, daf) {
    var S = LG.state(), a = (S.amud[slug] || {})[daf];
    var cyc = LG.cycles(slug);
    if (!a) return { st: 'none', n: 0, cyc: cyc };
    var n = a.n + (a.ext && !a.n ? 1 : 0), st;
    if (n > cyc) st = a.n > cyc ? 'done' : 'ext';
    else st = (a.prog > 0.02 || a.active > 20000) ? 'prog' : 'none';
    return { st: st, n: n, cyc: cyc, a: a };
  };
  LG.masechetStats = function (slug) {
    var S = LG.state(), list = LG.amudim(slug), A = S.amud[slug] || {};
    var cyc = LG.cycles(slug), done = 0, ext = 0, prog = 0, ms = 0, words = 0, leftWords = 0, learned = 0;
    list.forEach(function (it) {
      var a = A[it.daf], n = a ? a.n + (a.ext && !a.n ? 1 : 0) : 0;
      if (a) ms += a.active;
      var w = it.words || LG.avgWords();
      words += w;
      if (n > cyc) { learned++; if (a && a.n > cyc) done++; else ext++; }
      else { leftWords += w; if (a && (a.prog > 0.02 || a.active > 20000)) prog++; }
    });
    var total = list.length;
    /* דפים: דף שלם = שני עמודים */
    var dafimDone = 0, byDaf = {};
    list.forEach(function (it) {
      var k = dafNum(it.daf);
      var x = LG.amudInfo(slug, it.daf);
      (byDaf[k] = byDaf[k] || []).push(x.st === 'done' || x.st === 'ext');
    });
    Object.keys(byDaf).forEach(function (k) { if (byDaf[k].every(Boolean)) dafimDone++; });
    var dafimTotal = Object.keys(byDaf).length;
    return { slug: slug, total: total, learned: learned, done: done, ext: ext, prog: prog, cycle: cyc, ms: ms, words: words, leftWords: leftWords,
      dafimDone: dafimDone, dafimTotal: dafimTotal, ratio: total ? learned / total : 0 };
  };

  /* ------------------------------------------------------------ קצב אישי ותחזית
     נוסחאות (מתועדות בדוח):
     א. קצב: זמן פעיל למילה, משוקלל לטובת 20 הסיומים האחרונים:
        w_i = 0.93^(מרחק מהאחרון); קצב = Σ w_i*ms_i / Σ w_i*words_i.
        הזמן לעמוד = מילים בעמוד * קצב (העמודים אינם שווים באורכם).
     ב. בלי היסטוריה: ממוצע כללי אם נמסר, ובהעדרו הערכה סבירה (6 דקות
        לעמוד ממוצע), עם הערה "הערכה ראשונית".
     ג. זמן נותר = Σ הזמן הצפוי של עמודים שטרם נלמדו.
     ד. זמן יומי = ממוצע הדקות בימי הלימוד של 14 הימים האחרונים, או הערך שבמחוון.
     ה. תאריך סיום = היום + ימי לימוד נדרשים, בדילוג על ימים שנבחרו. */
  LG.pace = function (slug) {
    var S = LG.state(), amudim = {};
    LG.amudim(slug).forEach(function (a) { amudim[a.daf] = a.words || LG.avgWords(); });
    var recs = [];
    S.doneEvents.forEach(function (d) { if (d.ms > 20000 && amudim[d.d] && (!slug || d.s === slug)) recs.push(d); });
    if (!recs.length && slug) { /* היסטוריה ממסכתות אחרות */
      S.doneEvents.forEach(function (d) { if (d.ms > 20000) recs.push(d); });
    }
    recs.sort(function (a, b) { return a.t - b.t; });
    recs = recs.slice(-20);
    var num = 0, den = 0, n = recs.length;
    recs.forEach(function (d, i) {
      var w = Math.pow(0.93, n - 1 - i);
      var words = (LG.masechet(d.s) && LG.amudim(d.s).filter(function (x) { return x.daf === d.d; })[0] || {}).words || LG.avgWords();
      num += w * d.ms; den += w * words;
    });
    if (den > 0) return { perWord: num / den, est: false, n: n };
    return { perWord: (6 * 60000) / LG.avgWords(), est: true, n: 0 };
  };
  LG.dailyMs = function () {
    var S = LG.state(), today = ymd(Date.now()), tot = 0, c = 0;
    for (var i = 0; i < 14; i++) {
      var d = S.days[addDays(today, -i)];
      if (d && d.ms > 60000) { tot += d.ms; c++; }
    }
    return c ? tot / c : 0;
  };
  LG.remainingMs = function (slug) {
    var S = LG.state(), A = S.amud[slug] || {}, cyc = LG.cycles(slug), p = LG.pace(slug), ms = 0;
    LG.amudim(slug).forEach(function (it) {
      var a = A[it.daf], n = a ? a.n + (a.ext && !a.n ? 1 : 0) : 0;
      if (n <= cyc) ms += (it.words || LG.avgWords()) * p.perWord;
    });
    return ms;
  };
  LG.finishDate = function (remMs, dailyMs, skip) {
    if (!dailyMs || dailyMs < 60000) return null;
    var need = Math.ceil(remMs / dailyMs), d = ymd(Date.now()), n = 0, guard = 0;
    skip = skip || [];
    while (n < need && guard < 4000) {
      d = addDays(d, 1); guard++;
      var wd = new Date(ymdToUTC(d)).getUTCDay();
      if (skip.indexOf(wd) < 0) n++;
    }
    return { ymd: d, days: guard };
  };
  LG.streak = function () {
    var S = LG.state(), today = ymd(Date.now()), n = 0, d = today;
    function active(x) { var o = S.days[x]; return o && (o.ms >= 120000 || o.done > 0 || o.ext > 0); }
    if (!active(d)) d = addDays(d, -1);
    while (active(d)) { n++; d = addDays(d, -1); }
    return n;
  };
  LG.settings = function () { return LG.state().settings; };
  LG.setSetting = function (key, val) { LG.put({ k: 'cf', key: key, val: val, t: Date.now() }); };
})();
