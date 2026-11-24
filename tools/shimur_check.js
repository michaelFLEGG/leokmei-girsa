/* בדיקת שימור הטקסט בדף החי (24.11.2026) - אותה בדיקה כמו shimur_check.py, אבל רצה בתוך דף המסכת עצמו,
   על הנתונים כפי שהדף מציג אותם לגולש אחרי החלת /live (D), ומחזירה רק את התוצאה.
   לכל עריכה: הנוסח שהשאירה. רצף של 3 מילים ומעלה ממנו שאינו בדף (בדף שלה ובשלושה סביבו, ואחר כך בכל המסכת),
   ושאף עריכה מאוחרת לא "ראתה" אותו בקלט שלה (כלומר לא הוסר בכוונה) - נרשם כחסר.
   הרצה: להדביק בקונסול של דף המסכת (או javascript_tool), ואז: await shimurCheck()
   ועם העריכות שהקיפול הלילי הוציא מן הרשימה החיה (data/fold/tlushot/<מסכת>.json):
     await shimurCheck({extra: (await (await fetch('https://raw.githubusercontent.com/michaelFLEGG/leokmei-girsa/main/data/fold/tlushot/'+SLUG+'.json')).json()).edits.filter(e=>!e.del)})
   חתימת הכשל שנמצא 24.11: שורה שמסתיימת בפסיק/רווח קשיח, והמשכה (השורה השנייה באיחוד או בפיצול) אינו בשום מקום בדף.
   ממצא שהמשכו קיים בניסוח אחר בשורה סמוכה - אינו אבדה (שוכתב). */
window.shimurCheck = async function (opt) {
  opt = opt || {}; var NEAR = opt.near || 3, MINRUN = 3;
  /* מחכים שהדף יסיים להחיל את התיקונים מן השרת (liveLoad -> applyStructAsync) */
  for (var w = 0; w < 300 && (!ED.length || (typeof APG !== 'undefined' && APG)); w++) await new Promise(function (r) { setTimeout(r, 100) });
  var G = {'א':1,'ב':2,'ג':3,'ד':4,'ה':5,'ו':6,'ז':7,'ח':8,'ט':9,'י':10,'כ':20,'ל':30,'מ':40,'נ':50,'ס':60,'ע':70,'פ':80,'צ':90,'ק':100,'ר':200,'ש':300,'ת':400};
  function words(s) {
    s = String(s == null ? '' : s).replace(/<[^>]+>/g, '');
    var t = document.createElement('textarea'); t.innerHTML = s; s = t.value;
    s = s.replace(/[֑-ׇ]/g, '').replace(/["'״׳]/g, '').replace(/[^א-ת0-9a-zA-Z\s]/g, ' ');
    return s.split(/\s+/).filter(Boolean);
  }
  function dafkey(d) {
    var m = /^\s*([א-ת"']+)\s*([.:])/.exec(String(d || '')); if (!m) return null;
    var n = 0; for (var c of m[1]) n += G[c] || 0; return 2 * n + (m[2] === ':' ? 1 : 0);
  }
  /* הדף כפי שהגולש רואה: כל השורות, כותרות הצד והד"ה, לפי סדר, לכל דף */
  var per = new Map(), keys = [];
  D.pages.forEach(function (p) {
    var k = dafkey(p.daf); if (!per.has(k)) { per.set(k, []); keys.push(k) }
    var a = per.get(k);
    (p.units || []).forEach(function (u) {
      if (u.a) a.push(words(u.a).join(' '));
      (u.l || []).forEach(function (l) { if (Array.isArray(l)) l.forEach(function (x) { if (typeof x === 'string' && /[א-ת]/.test(x)) a.push(words(x).join(' ')) }) });
    });
  });
  var all = ' ' + keys.map(function (k) { return per.get(k).join(' ') }).join(' ') + ' ', cache = new Map();
  function near(d) {
    if (d == null) return all; if (cache.has(d)) return cache.get(d);
    var h = ' ' + keys.filter(function (k) { return k != null && Math.abs(k - d) <= NEAR }).map(function (k) { return per.get(k).join(' ') }).join(' ') + ' ';
    cache.set(d, h); return h;
  }
  function intents(e) {
    var out = [], inp = [];
    if (e.op === 'struct') {
      inp = (e.texts || []).slice();
      if (e.resT) out = e.resT.filter(function (x) { return typeof x === 'string' });
      else (e.res || []).forEach(function (r) { if (Array.isArray(r) && r.length >= 2 && typeof r[r.length - 1] === 'string') out.push(r[r.length - 1]) });
    } else {
      if (e.was != null) inp = [e.was];
      if (e.now != null) out = [e.nowH != null ? e.nowH : e.now];
    }
    return [out, inp];
  }
  function has(h, ws) { return h.indexOf(' ' + ws.join(' ') + ' ') > -1 }
  function missing(ws, h) {
    var n = ws.length, ok = new Array(n).fill(false);
    for (var i = 0; i < n; i++) {
      for (var L of [3, 2]) { for (var a = Math.max(0, i - L + 1); a <= Math.min(i, n - L); a++) if (has(h, ws.slice(a, a + L))) { ok[i] = true; break } if (ok[i]) break }
    }
    var runs = [], cur = [];
    for (var j = 0; j < n; j++) { if (!ok[j]) cur.push(ws[j]); else { if (cur.length >= MINRUN) runs.push(cur.join(' ')); cur = [] } }
    if (cur.length >= MINRUN) runs.push(cur.join(' '));
    return runs;
  }
  /* העריכות כפי שהדף עצמו קיבל אותן (אחרי edDedup ובלי מחוקות); lost = הדף לא מצא להן מקום */
  var E = ED.concat((opt.extra || []).map(function (x) { var y = Object.assign({}, x); y._tl = 1; return y })).slice().sort(function (a, b) { return (a.t || 0) - (b.t || 0) });
  var INP = [], GI = new Map();
  E.forEach(function (e, j) {
    var xs = intents(e)[1].map(function (x) { return words(x) }).filter(function (w) { return w.length }).map(function (w) { return ' ' + w.join(' ') + ' ' });
    INP.push(xs); var seen = new Set();
    xs.forEach(function (x) { var w = x.trim().split(' '); for (var k = 0; k + 2 < w.length; k++) { var g = w.slice(k, k + 3).join(' '); if (!seen.has(g)) { seen.add(g); if (!GI.has(g)) GI.set(g, []); GI.get(g).push(j) } } });
  });
  function seenLater(i, run) {
    var g = run.split(' ').slice(0, 3).join(' '), pat = ' ' + run + ' ', L = GI.get(g) || [];
    for (var q = 0; q < L.length; q++) { var j = L[q]; if (j > i && INP[j].some(function (x) { return x.indexOf(pat) > -1 })) return j }
    return -1;
  }
  var st = { edits: E.length, 'נבדקו': 0, 'בדף': 0, 'בדף בשינוי שורות או במקום אחר': 0, 'הוסר בכוונה אחר כך': 0, 'חסר': 0 }, res = [];
  E.forEach(function (e, i) {
    intents(e)[0].forEach(function (o) {
      var ws = words(o); if (ws.length < MINRUN) return;
      st['נבדקו']++;
      var d = dafkey(e.daf), h = near(d);
      if (h.indexOf(' ' + ws.join(' ') + ' ') > -1) { st['בדף']++; return }
      var runs = missing(ws, h).filter(function (r) { return missing(r.split(' '), all).length });
      if (!runs.length) { st['בדף בשינוי שורות או במקום אחר']++; return }
      var lost = runs.filter(function (r) { return seenLater(i, r) < 0 });
      if (!lost.length) { st['הוסר בכוונה אחר כך']++; return }
      st['חסר']++;
      res.push({ daf: e.daf, k: e.k, t: e.t, op: e.op || 'text', kind: e.kind || '', lostFlag: !!e.lost, tl: !!e._tl, missing: lost, text: ws.join(' ').slice(0, 220) });
    });
  });
  st['לא הוחלו לפי הדף'] = E.filter(function (e) { return e.lost }).length;
  return { slug: SLUG, st: st, res: res };
};
