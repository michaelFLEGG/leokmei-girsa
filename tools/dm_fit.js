  /* ---------- פרומפט 95 (25.11.2026, מיכאל): המעוין שבתוך השורה - רכיב משותף אחד ----------
     המעוין (span.bkx.dm, נוצר ב-lgSep שב-build_site.py וב-pmSep שב-print_mode.js) מחליף רווח גדול בין שתי שיטות.
     העיצוב הקבוע (גודל, אפור, מרכז גובה האות) ב-CSS של .bkx.dm ב-build_site.py. כאן המרווח החכם והכיול:
     א. גובה: מרכז המעוין במרכז גובה האותיות העבריות של הפסקה (נמדד בגופן עצמו, בקנבס), לא באמצע השורה.
     ב. מרכז אופקי: באמצע הריק שבין המילה שלפניו למילה שאחריו (הרווח הרגיל שלפניו + הרהיט), ולכן שני צדיו שווים.
     ג. מרווח חכם: הריק העודף בשורה (מה שהיישור לשני הצדדים היה מפזר בין המילים) ניתן קודם לשני צדי המעוין, שווה
        בשווה, עד תקרה של כרוחב טאב (DMCAP) לכל צד; מה שנשאר - מתחלק כרגיל בין המילים. אין ריק - הרוחב הבסיסי בלבד.
     ד. לעולם לא שבירה או גלישה: שבירת השורות אינה תלויה ביישור, ולכן הריק נמדד כשהפסקה מיושרת לימין (שורות זהות),
        וכל תוספת קטנה ממנו. הרוחב הבסיסי של הרהיט אינו משתנה, ולכן שום איחוי אינו מתבטל.
     ה. התוספת נכתבת כמשתני עיצוב על הרהיט בלבד (style="--dm..."). מי שמעתיק את תוכן הפסקה למדידה (איחוי, הצרה)
        משתמש ב-dmPlain, שמסיר אותם, כדי שהמדידה תהיה על הרוחב הבסיסי. הרהיט עצמו (bkx) אינו נכנס לנתונים ולוורד. */
  var DMCAP=1.5,      /* תקרת הריק לכל צד, ביחידות גופן הפסקה (טאב ממוצע: 1.5-2) */
      DMDIAG=0.72;    /* אלכסון המעוין ביחס לגובה האות (כ-85% מן המעוין שלפני פרומפט 95, שנמדד ביחס לגופן הרהיט) */
  var DMHC={};
  /* מדדי הגופן ביחס לגודלו, לפי משפחה ומשקל (נמדד בקנבס, בגופן עצמו):
     h - גובה האות העברית בלי ניקוד (אותיות בלי עוקץ עולה או יורד), d - היורד של תיבת הגופן (מקו הבסיס עד תחתית התיבה) */
  function dmMetrics(cs){
    var k=cs.fontStyle+'|'+cs.fontWeight+'|'+cs.fontFamily;
    if(DMHC[k])return DMHC[k];
    var v={h:0.62,d:0.3};
    try{var c=dmMetrics.c||(dmMetrics.c=document.createElement('canvas')),x=c.getContext('2d');
      x.font=cs.fontStyle+' '+cs.fontWeight+' 100px '+cs.fontFamily;
      var m=x.measureText('\u05D1\u05D4\u05DE\u05E9\u05EA'),a=m.actualBoundingBoxAscent,dd=m.actualBoundingBoxDescent;
      /* בחלק מן הגופנים האות העברית יורדת מעט מתחת לקו הבסיס: מרכז האות הוא מרכז הדיו שלה */
      if(a>20&&a<120)v.h=(a+Math.max(0,Math.min(dd,a*0.1)))/100,v.o=Math.max(0,Math.min(dd,a*0.1))/100;
      if(m.fontBoundingBoxDescent>0)v.d=m.fontBoundingBoxDescent/100;
      DMHC[k]=v}catch(e){}
    return v}
  function dmPlain(p){var h=p.innerHTML;return h.indexOf('--dm')<0?h:h.replace(/ style="--dm[^"]*"/g,'')}
  window.dmPlain=dmPlain;
  /* שורות הפסקה: לכל שורה הקצה השמאלי של הטקסט (סוף השורה בעברית) והימני, לפי המלבנים של כל קטעי הטקסט */
  function dmLines(p){
    var rg=document.createRange();rg.selectNodeContents(p);
    var R=[].slice.call(rg.getClientRects()).filter(function(r){return r.width>0.5&&r.height>1}),L=[];
    R.forEach(function(r){var my=(r.top+r.bottom)/2,hit=null;
      for(var i=0;i<L.length;i++){var l=L[i];if(my>l.t&&my<l.b){hit=l;break}}
      if(hit){hit.l=Math.min(hit.l,r.left);hit.r=Math.max(hit.r,r.right);hit.t=Math.min(hit.t,r.top);hit.b=Math.max(hit.b,r.bottom)}
      else L.push({l:r.left,r:r.right,t:r.top,b:r.bottom})});
    return L}
  function dmLineOf(L,y){for(var i=0;i<L.length;i++)if(y>=L[i].t-0.5&&y<=L[i].b+0.5)return L[i];return null}
  /* המעוין בפסקאות: קריאה אחת של כל הפריסה, וכתיבה אחת. ps: פסקאות (או אלמנטים שמכילים פסקאות) */
  function dmFit(list){
    var ps=[];
    [].forEach.call(list||[],function(e){if(!e||!e.isConnected)return;
      if(e.matches&&e.matches('p')){if(e.querySelector('.bkx.dm'))ps.push(e)}
      else if(e.querySelectorAll)[].forEach.call(e.querySelectorAll('p'),function(p){if(p.querySelector('.bkx.dm'))ps.push(p)})});
    if(!ps.length)return 0;
    /* 1. ניקוי התוספות הקודמות ומדידה ביישור לימין (השורות זהות, הריק כולו בסוף כל שורה) */
    var D=[];
    ps.forEach(function(p){[].forEach.call(p.querySelectorAll('.bkx.dm'),function(s){s.style.removeProperty('--dmx');s.style.removeProperty('--dmc');s.style.removeProperty('--dmb');s.style.removeProperty('--dmd')});
      p.classList.add('dmq')});
    ps.forEach(function(p){
      var cs=getComputedStyle(p),fs=parseFloat(cs.fontSize)||16,pr=p.getBoundingClientRect(),
          inL=pr.left+(parseFloat(cs.borderLeftWidth)||0)+(parseFloat(cs.paddingLeft)||0),
          L=dmLines(p),ss=[].slice.call(p.querySelectorAll('.bkx.dm')).filter(function(s){return s.style.display!=='none'&&s.offsetParent!==null});
      if(!ss.length)return;
      var MT=dmMetrics(cs),lh=MT.h*fs,lo=(MT.o||0)*fs;
      var it=ss.map(function(s){var r=s.getBoundingClientRect();
        var pv=s.previousSibling,sp=0;
        if(pv&&pv.nodeType===3&&/\s$/.test(pv.nodeValue)){var q=document.createRange();q.setStart(pv,pv.nodeValue.length-1);q.setEnd(pv,pv.nodeValue.length);
          var qr=q.getBoundingClientRect();if(qr.width>0&&Math.abs((qr.top+qr.bottom)/2-(r.top+r.bottom)/2)<lh)sp=qr.width}
        var ln=dmLineOf(L,(r.top+r.bottom)/2);
        return {s:s,r:r,sp:sp,ln:ln,first:!!(ln&&r.right>=ln.r-1)}});
      D.push({p:p,fs:fs,lh:lh,lo:lo,inL:inL,it:it})});
    ps.forEach(function(p){p.classList.remove('dmq')});
    /* 2. חישוב: לכל שורה הריק שבסופה, מחולק בין המעוינים שבה */
    var W=[];
    D.forEach(function(d){
      var byLn=new Map();d.it.forEach(function(o){if(!o.ln)return;var a=byLn.get(o.ln)||[];a.push(o);byLn.set(o.ln,a)});
      d.it.forEach(function(o){
        /* הרוחב הבסיסי: הרהיט, פחות ההצרה שמנוע ההדפסה נתן לו (שוליים שליליים משמאל, ogSet) */
        var cs=getComputedStyle(o.s),w=o.r.width+Math.min(0,parseFloat(cs.marginLeft)||0),sfs=parseFloat(cs.fontSize)||d.fs,
            /* קו הבסיס בתוך הרהיט: מעל תחתית תיבת התוכן שלו בשיעור היורד של הגופן שלו */
            desc=dmMetrics(cs).d*sfs,
            dg=DMDIAG*d.lh,sd=dg/Math.SQRT2,
            gap=o.first?w:w+o.sp,           /* הריק כולו: הרווח הרגיל שלפניו והרהיט (בתחילת שורה - הרהיט בלבד) */
            base=(gap-dg)/2,                 /* כל צד, בלי תוספת */
            x=0;
        if(o.ln&&!o.first){
          var slack=Math.max(0,o.ln.l-d.inL-1),n=(byLn.get(o.ln)||[o]).length;
          /* כל צד מקבל מן הריק עד התקרה; לא יותר מחלקו בריק (שני צדדים, וכל המעוינים שבשורה) */
          x=Math.max(0,Math.min(DMCAP*d.fs-base,slack/n/2))}
        /* מרכז המעוין, מן הקצה הימני של הרהיט (כולל התוספת שמימינו): חצי הריק כולו פחות הרווח שלפניו */
        var c=(gap+2*x)/2-(o.first?0:o.sp);
        W.push([o.s,x,c,desc+d.lh/2-d.lo-sd/2,sd])})});
    /* 3. כתיבה */
    W.forEach(function(a){var s=a[0];
      if(a[1]>0.3)s.style.setProperty('--dmx',a[1].toFixed(2)+'px');
      s.style.setProperty('--dmc',a[2].toFixed(2)+'px');
      s.style.setProperty('--dmd',a[4].toFixed(2)+'px');
      s.style.setProperty('--dmb',a[3].toFixed(2)+'px')});
    return W.length}
  window.dmFit=dmFit;
