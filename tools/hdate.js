/* hdate.js - תאריכים עבריים בלבד, בפונקציה אחת משותפת לכל האתר (6.10.2026).
   בפנים (נתונים, מסד, חישובים) התאריכים נשמרים כפי שהם; ההמרה היא בתצוגה בלבד.
   הפורמט: "ג' תשרי תשפ"ז" (יום וחודש באותיות, שנה מקוצרת בגרשיים),
   וימי השבוע בעברית ("יום שלישי"). שעה מותרת כרגיל.
   מתי מתחלף היום העברי: לפי חצות (כמו Intl). שקיעה אינה נחשבת - ראה הדוח. */
(function (g) {
  'use strict';
  var TZ = 'Asia/Jerusalem';
  var HEB = [[400, 'ת'], [300, 'ש'], [200, 'ר'], [100, 'ק'], [90, 'צ'], [80, 'פ'], [70, 'ע'], [60, 'ס'], [50, 'נ'], [40, 'מ'],
             [30, 'ל'], [20, 'כ'], [10, 'י'], [9, 'ט'], [8, 'ח'], [7, 'ז'], [6, 'ו'], [5, 'ה'], [4, 'ד'], [3, 'ג'], [2, 'ב'], [1, 'א']];
  var WD = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי', 'שישי', 'שבת'];
  function letters(n) {
    if (n === 15) return 'טו';
    if (n === 16) return 'טז';
    var t = '';
    HEB.forEach(function (p) { while (n >= p[0]) { t += p[1]; n -= p[0]; } });
    return t.replace(/יה$/, 'טו').replace(/יו$/, 'טז');
  }
  /* מספר באותיות עם גרשיים: נ"ב, ג' */
  function q(n) {
    var t = letters(n);
    if (t.length > 1) return t.slice(0, -1) + '"' + t.slice(-1);
    return t + "'";
  }
  /* הערך המספרי של מספר באותיות (ג = 3, יב = 12, תשפ"ז = 787) */
  function num(t) {
    var n = 0;
    String(t || '').replace(/[֑-ׇ"'׳״.:\s]/g, '').split('').forEach(function (c) {
      HEB.forEach(function (p) { if (p[1] === c) n += p[0]; });
    });
    return n;
  }
  function ms(ts) {
    if (ts instanceof Date) return ts.getTime();
    if (typeof ts === 'string') { var d = Date.parse(ts); return isNaN(d) ? Date.now() : d; }
    return ts == null ? Date.now() : +ts;
  }
  function hp(ts) {
    var o = {};
    try {
      new Intl.DateTimeFormat('he-u-ca-hebrew-nu-latn', { timeZone: TZ, day: 'numeric', month: 'long', year: 'numeric' })
        .formatToParts(new Date(ms(ts))).forEach(function (p) { o[p.type] = p.value; });
    } catch (e) { return null; }
    var y = parseInt(o.year, 10);
    if (!o.day || isNaN(y)) return null;
    return { d: parseInt(o.day, 10), m: String(o.month).replace(/[׳’]/g, "'"), y: y };
  }
  function date(ts) { var p = hp(ts); return p ? q(p.d) + ' ' + p.m + ' ' + q(p.y % 1000) : ''; }
  function dateShort(ts) { var p = hp(ts); return p ? q(p.d) + ' ' + p.m : ''; }
  function wday(ts) {
    var w = '';
    try { w = new Intl.DateTimeFormat('en-US', { timeZone: TZ, weekday: 'short' }).format(new Date(ms(ts))); } catch (e) { return ''; }
    var i = { Sun: 0, Mon: 1, Tue: 2, Wed: 3, Thu: 4, Fri: 5, Sat: 6 }[w];
    return i == null ? '' : (i === 6 ? 'שבת' : 'יום ' + WD[i]);
  }
  function time(ts) {
    var o = {};
    new Intl.DateTimeFormat('en-GB', { timeZone: TZ, hour: '2-digit', minute: '2-digit', hour12: false })
      .formatToParts(new Date(ms(ts))).forEach(function (p) { o[p.type] = p.value; });
    return (o.hour === '24' ? '00' : o.hour) + ':' + o.minute;
  }
  g.HD = {
    q: q, letters: letters, num: num, parts: hp, date: date, dateShort: dateShort, weekday: wday, time: time,
    long: function (ts) { return wday(ts) + ', ' + date(ts); },
    dateTime: function (ts) { return date(ts) + ' ' + time(ts); },
    /* מחרוזת yyyy-mm-dd (יום קלנדרי) -> תאריך עברי של אותו יום (בצהריים, ללא בעיית אזור זמן) */
    ymd: function (s) { var a = String(s).split('-'); return date(Date.UTC(+a[0], +a[1] - 1, +a[2], 10)); },
    ymdShort: function (s) { var a = String(s).split('-'); return dateShort(Date.UTC(+a[0], +a[1] - 1, +a[2], 10)); },
    ymdLong: function (s) { var a = String(s).split('-'); var t = Date.UTC(+a[0], +a[1] - 1, +a[2], 10); return wday(t) + ', ' + date(t); },
    setTZ: function (tz) { if (tz) TZ = tz; }
  };
})(typeof window !== 'undefined' ? window : globalThis);
