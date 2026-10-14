  /* =================== תוספות בהערות שוליים ===================
     מוזרק לדף המסכת רק כשיש למסכת קובץ תוספות (tosafot/<slug>/live-*.json), ורק אותם תוספות שנכתב להם סיכום.
     הספירה קבועה (tosafot/<slug>/count-<פרק>.json): הערה אחת לכל דיבור המתחיל, ממוספרת ברצף לפי הפרק.
     הסימנים והערות השוליים נבנים מעל הדף אחרי כל רינדור (tsMark) ואינם חלק מנוסח הוורד:
     במצב עריכה והצעה, בתצוגת ספר ובהדפסה הם מוסרים, כדי שלא ייכנסו לטקסט.
     העוגן נשמר כקטע טקסט ומספר מופע (לא כמיקום תו). אם הקטע לא נמצא (הטקסט נערך), הסימן עובר לסוף שורת הגמרא
     הקרובה ומופיע למנהל כ"עוגן זז". תוספות לעולם אינו נעלם בשקט.

     חוויית התוספות (14.10.2026): חמש תצוגות - פאנל צד (ברירת מחדל; בנייד מגירה תחתונה), הערות שוליים, בצד, רשימה, כבוי.
     ריחוף על הסימן בכל תצוגה פותח כרטיס צף מלא. "הצע תיקון" בכל כרטיס, גם לאורח, אל תור ההצעות הקיים (סוג note, k=tos:<מפתח>).
     הד"ה המוצג הוא dhs (מקוצר); dh המלא נשאר בנתונים. בלי קישור ספריא ובלי תווית מקור בכל כרטיס. */
  (function(){
  var TS=window.__TOS||null;
  if(!TS||!TS.items||!TS.items.length)return;
  var TS_KEY='lg-tos-mode',CFG_KEY='lg-tos-cfg';
  var MODES=[['panel','פאנל צד','חלונית עדינה בצד, מסונכרנת לגלילה (בנייד: מגירה תחתונה)'],
             ['foot','הערות שוליים','סימן עילי בטקסט, וההערות בתחתית הדף'],
             ['side','בצד','לחיצה על הסימן פותחת את ההערה בכרטיס'],
             ['list','רשימה','כל התוספות ברצף ממוספר, לחזרה ולשינון'],
             ['off','כבוי','בלי סימנים כלל']];
  var STY=[['a','שורה אחת'],['b','מהודק ומובן'],['c','קושיה ותירוץ'],['d','לשון התוספות המקוצרת'],['e','הנפקא מינה']];
  var RULE={'1':'המילה בטקסט','2':'מילה מקבילה בטקסט','3':'סוף שורת הגמרא הקרובה','m':'העוגן זז: הוצמד לסוף שורת הגמרא'};
  var SGT=[['nusach','ניסוח'],['misunderstand','טעות בהבנה'],['anchor','עוגן במקום לא נכון'],['missing','חסר']];
  function lsGet(k,d){try{var v=localStorage.getItem(k);return v===null?d:v}catch(e){return d}}
  function lsSet(k,v){try{localStorage.setItem(k,v)}catch(e){}}
  var mode=lsGet(TS_KEY,'off');
  if(!/^(foot|panel|side|list|off)$/.test(mode))mode='off';
  /* הגדרות הלומד: גודל גופן, פנים תמיד, עמוד/פרק, שינון, רוחב הפאנל */
  var CFG={fs:'m',face:0,page:1,mem:0,w:300};
  try{var c0=JSON.parse(lsGet(CFG_KEY,'{}'));if(c0&&typeof c0==='object')Object.keys(CFG).forEach(function(k){if(c0[k]!==undefined)CFG[k]=c0[k]})}catch(e){}
  function cfgSave(){lsSet(CFG_KEY,JSON.stringify(CFG))}
  var PUB={};            /* n -> {p,t}: הנוסח שנבחר (מנקודת הקליטה) */
  var TOK={},TNO={};     /* מסך בדיקת התוספות: n -> true. TOK = אושרה (מסיר "טרם נבדק" ומציג מוסתרת), TNO = הוסרה מהאתר */
  var ADM=null;          /* מנהל: {styles,picks,notes} */
  var SUGS={};           /* מנהל: n -> [הצעות ממתינות על תוספות] */
  var MOVED={};          /* n -> true: העוגן זז */
  var PLACED={};         /* n -> כלל שהופעל */
  var RANGES={};         /* n -> Range של המילים המעוגנות (להדגשה) */
  /* המספור המוצג הוא מספר סידורי בספרות (הוחלט 11.10.2026); האותיות נשמרות בחיפוש בלבד */
  var byN={};TS.items.forEach(function(it){it.hnHeb=it.hn;it.hn=String(it.disp||it.n);byN[it.n]=it});
  var ALLITEMS=TS.items.slice();
  function triHide(it){return TNO[it.n]||(it.h&&!TOK[it.n])}
  function triApply(){
    TS.items.length=0;ALLITEMS.forEach(function(it){if(!triHide(it))TS.items.push(it)});
    byN={};TS.items.forEach(function(it){byN[it.n]=it});
    SORTED.length=0;TS.items.slice().sort(function(a,b){return a.n-b.n}).forEach(function(it){SORTED.push(it)})}
  var SORTED=TS.items.slice().sort(function(a,b){return a.n-b.n});
  triApply0();
  function triApply0(){TS.items.length=0;ALLITEMS.forEach(function(it){if(!it.h)TS.items.push(it)});
    byN={};TS.items.forEach(function(it){byN[it.n]=it});SORTED.length=0;TS.items.slice().sort(function(a,b){return a.n-b.n}).forEach(function(it){SORTED.push(it)})}

  var sty=document.createElement('style');
  sty.textContent=
   '.tsa{display:inline;width:0;height:0;padding:0;margin:0;border:0}'+
   '#tsl{position:fixed;left:0;top:0;width:0;height:0;z-index:5;pointer-events:none}'+
   '.tsm{position:fixed;pointer-events:auto;font-family:Vilna,serif;font-weight:700;font-size:calc(var(--fs,18px) * .66);line-height:1.1;color:#7a5a14;background:rgba(251,248,241,.97);border:1px solid #c9b46f;border-radius:7px;padding:1px 5px;cursor:pointer;-webkit-user-select:none;user-select:none;white-space:nowrap;letter-spacing:.02em;margin:0;min-width:1.7em;text-align:center;box-sizing:border-box}'+
   '.tsm:hover,.tsm:focus-visible,.tsm.hot{background:var(--blue-soft,#e6edf7);color:#12396b;outline:0}'+
   '.tsm.mv{color:#a83c2f}'+
   '::highlight(tosw){background:rgba(201,162,74,.38)}'+
   '.tsfoot,.tsn,.tsx,.tsadm,#tospop,#tosmenu,#tospb,#tpan,#toshov{color:#2b2620}'+
   '.tsfoot{margin:1.5em 0 .7em;padding:.6em .5em .3em;border-top:2px solid #b9a56a;background:#faf6ea;border-radius:0 0 6px 6px;font-size:.82em;line-height:1.7;-webkit-user-select:text;user-select:text}'+
   '.tsfoot .tsh{font-family:Vilna,serif;font-weight:700;color:#7a5a14;font-size:.98em;margin-bottom:.45em;display:flex;align-items:center;gap:.8em}'+
   '.tsfoot .tsh .tsall{font:inherit;font-size:.82em;font-weight:400;padding:0 .7em;border:1px solid #c9bfa6;border-radius:10px;background:#fff;color:#5a4a1e;cursor:pointer}'+
   '.tsfoot .tsn{margin:.15em 0;padding:.55em .45em .6em;border-bottom:1px dotted #d3c79c}'+
   '.tsfoot .tsn:last-child{border-bottom:0}'+
   '.tsn .tsnum{cursor:pointer}'+
   '.tsn .tsnum:hover,.tsn .tsnum:focus-visible{text-decoration:underline;outline:0}'+
   '#tosbtn .tsst{font-size:.72em;font-weight:700;margin-inline-start:.35em;opacity:.8}'+
   '#tosbtn .tsst::before{content:"כבוי"}'+
   '#tosbtn.on .tsst::before{content:"דלוק"}'+
   '.tsmb{display:none}'+
   '#tosbtn.on + .tsmb{display:inline-flex}'+
   '.tsn{margin:.4em 0;padding:.25em .35em;border-radius:5px;scroll-margin-top:70px}'+
   '.tsn.hot{background:#fff4d6;transition:background .3s}'+
   '.tsn .tsnum{font-family:Vilna,serif;font-weight:900;font-size:1.05em;color:#000;margin-inline-end:.35em}'+
   '.tsn .tsdh{font-family:Vilna,serif;font-size:1.05em;font-weight:700;color:#2b2620;margin-inline-end:.4em}'+
   '.tsn .tsug{display:none;font-size:.78em;margin-inline-end:.4em;padding:0 .5em;border:1px solid #c98a3a;border-radius:9px;background:#fff1dc;color:#8a4b00;white-space:nowrap}'+
   'body.adm .tsn .tsug{display:inline-block}'+
   '.tsn .tstx{display:inline}'+
   '.tsn .tsbt{display:inline-flex;gap:.35em;margin-inline-start:.5em;flex-wrap:wrap}'+
   '.tsn .tsbt button{font:inherit;font-size:.78em;padding:0 .6em;border:1px solid #c9bfa6;border-radius:10px;background:#faf6ea;color:#5a4a1e;cursor:pointer;min-height:22px}'+
   '.tsn .tsbt button:hover,.tsn .tsbt button:focus-visible{background:#f2ead2;outline:0}'+
   '.tsn .tsface{margin:.4em 0 .2em;padding:.5em .7em;background:#f6f1e3;border-radius:5px;font-size:.88em;line-height:1.6;color:#2b2620;display:block;-webkit-user-select:text;user-select:text}'+
   '.tsn .tsface[hidden]{display:none}'+
   '.tsn .tsface b{font-weight:700;font-family:Vilna,serif}'+
   '.tssgbox{margin:.5em 0 .2em;padding:.55em .65em;border:1px solid #d3c79c;border-radius:7px;background:#fffdf5;font-size:.88em;line-height:1.5;display:block;cursor:auto}'+
   '.tssgbox[hidden]{display:none}'+
   '.tssgbox textarea,.tssgbox input,.tssgbox select{width:100%;box-sizing:border-box;font:inherit;font-size:.95em;padding:.3em .4em;border:1px solid #c9bfa6;border-radius:4px;margin:.2em 0;direction:rtl;background:#fff;color:#2b2620}'+
   '.tssgbox textarea{min-height:5em}'+
   '.tssgbox .tssgb{display:flex;gap:.5em;margin-top:.3em;align-items:center;flex-wrap:wrap}'+
   '.tssgbox button{font:inherit;font-size:.92em;padding:.15em .9em;border:1px solid #b9a56a;border-radius:6px;background:#fff;cursor:pointer;min-height:28px;color:#2b2620}'+
   '.tssgbox button.go{background:#c9a24a;border-color:#a98a36}'+
   '.tssent{display:block;margin:.3em 0 0;font-size:.8em;color:#2d6a3a}'+
   '.tsadm{display:none;margin-top:.5em;padding:.5em .6em;border:1px dashed #b9a56a;border-radius:6px;background:#fffdf5;font-size:.86em;cursor:auto}'+
   'body.adm .tsadm{display:block}'+
   '.tsadm .tsah{color:#7a5a14;font-weight:700;margin-bottom:.3em}'+
   '.tsadm .tsv{display:flex;gap:.5em;align-items:flex-start;padding:.2em 0;border-bottom:1px solid #eee5cc}'+
   '.tsadm .tsv .tsvn{flex:0 0 7.5em;font-weight:700;color:#5a4a1e}'+
   '.tsadm .tsv .tsvt{flex:1 1 auto;line-height:1.5}'+
   '.tsadm .tsv.cur{background:#eaf3e6}'+
   '.tsadm .tssgq{margin:.4em 0;padding:.4em .5em;border:1px solid #d9c77e;border-radius:6px;background:#fff9e6}'+
   '.tsadm .tssgq .bf{color:#8a7f66;text-decoration:line-through}'+
   '.tsadm button{font:inherit;font-size:.9em;padding:.1em .7em;border:1px solid #b9a56a;border-radius:4px;background:#fff;cursor:pointer;min-height:26px;color:#2b2620}'+
   '.tsadm button.go{background:#c9a24a;border-color:#a98a36;color:#2b2620}'+
   '.tsadm textarea,.tsadm input{width:100%;box-sizing:border-box;font:inherit;font-size:.95em;padding:.3em .4em;border:1px solid #c9bfa6;border-radius:4px;margin:.25em 0;direction:rtl;background:#fff;color:#2b2620}'+
   '.tsadm textarea{min-height:5.5em;line-height:1.5}'+
   '.tsadm .tsw{color:#a83c2f}'+
   '#tosmenu{position:fixed;z-index:30;background:var(--paper,#fbf8f1);border:1px solid #c9bfa6;border-radius:8px;box-shadow:0 6px 24px rgba(0,0,0,.22);padding:.4em;min-width:15em;font-size:15px;display:none}'+
   '#tosmenu.open{display:block}'+
   '#tosmenu button{display:block;width:100%;text-align:right;font:inherit;background:none;border:0;padding:.45em .6em;border-radius:5px;cursor:pointer;color:inherit}'+
   '#tosmenu button small{display:block;color:#7a6f58;font-size:.82em}'+
   '#tosmenu button:hover{background:#f2ead2}'+
   '#tosmenu button.on{background:#e6edf7;font-weight:700}'+
   /* כרטיס צף: ריחוף או הקשה על הסימן, בכל תצוגה */
   '#toshov{position:fixed;z-index:31;width:min(30em,92vw);max-height:56vh;display:none;flex-direction:column;background:#fbf8f1;border:1px solid #c9b46f;border-top:3px solid #c9a24a;border-radius:9px;box-shadow:0 10px 32px rgba(10,25,50,.3);padding:.55em .75em .6em;font-size:15px;line-height:1.6;direction:rtl}'+
   '#toshov.open{display:flex}'+
   '#toshov .tsn{margin:0;padding:0;overflow:auto;flex:1 1 auto;min-height:0}'+
   '#toshov .tshov0{display:flex;gap:.4em;margin-bottom:.3em;justify-content:flex-start}'+
   '#toshov .tshov0 button{font:inherit;font-size:.8em;border:1px solid #c9bfa6;border-radius:10px;background:#faf6ea;color:#5a4a1e;cursor:pointer;padding:0 .7em;min-height:24px}'+
   '#toshov .tshov0 button:hover,#toshov .tshov0 button:focus-visible{background:#f2ead2;outline:0}'+
   '#toshov .tshov0 .sp{flex:1}'+
   /* פאנל הצד (תצוגה מרכזית) ומגירה תחתונה בנייד */
   '#tpan{position:fixed;z-index:7;left:0;top:var(--bar,46px);bottom:0;width:var(--tpw,300px);background:#fbf8f1;border-right:1px solid #c9a24a;box-shadow:2px 0 14px rgba(10,25,50,.18);display:none;flex-direction:column;direction:rtl;font-size:var(--tpfs,15px);line-height:1.6}'+
   '#tpan.open{display:flex}'+
   '#tpan .tphd{flex:0 0 auto;padding:.4em .5em .35em;border-bottom:1px solid #d9c77e;background:linear-gradient(#fffdf6,#f7f1de)}'+
   '#tpan .tpr{display:flex;align-items:center;gap:.3em;flex-wrap:wrap}'+
   '#tpan .tpttl{font-family:Vilna,serif;font-weight:700;color:#7a5a14;margin-inline-end:auto;font-size:1.02em}'+
   '#tpan .tpr button,#tpan .tpr select{font:inherit;font-size:.82em;padding:0 .5em;border:1px solid #c9bfa6;border-radius:8px;background:#fff;color:#4a3d18;cursor:pointer;min-height:26px;min-width:26px}'+
   '#tpan .tpr button.on{background:#c9a24a;border-color:#a98a36;color:#1d1a16;font-weight:700}'+
   '#tpan .tpr button:focus-visible,#tpan .tpr select:focus-visible,#tpan #tpq:focus-visible{outline:2px solid #12396b;outline-offset:1px}'+
   '#tpan #tpq{flex:1 1 6.5em;min-width:0;width:auto;box-sizing:border-box;font:inherit;font-size:.82em;margin:0;padding:0 .5em;min-height:26px;border:1px solid #c9bfa6;border-radius:8px;background:#fff;direction:rtl;color:#2b2620}'+
   '#tpan #tpl{flex:1 1 auto;overflow:auto;padding:.4em .55em .8em;-webkit-overflow-scrolling:touch}'+
   '#tpan .tsn{margin:.35em 0;padding:.45em .55em .5em;border:1px solid #e5dcb8;border-radius:8px;background:#fffdf6;cursor:pointer;transition:background .2s,border-color .2s}'+
   '#tpan .tsn.vis{background:#fff6dc;border-color:#d9b84f}'+
   '#tpan .tsn.cur{background:#fff0c4;border-color:#c9a24a;box-shadow:0 0 0 1px #c9a24a inset}'+
   '#tpan .tsn .tsbt{display:flex;margin:.35em 0 0}'+
   '#tpan .tsdaf{font-weight:700;color:#7a5a14;margin:.7em 0 .15em;font-family:Vilna,serif;font-size:.95em}'+
   '#tpan .tpe{color:#7a6f58;padding:1em .4em;text-align:center}'+
   '#tpan .tpgrip{position:absolute;top:0;bottom:0;right:-5px;width:10px;cursor:ew-resize;touch-action:none}'+
   '#tpan .tpgrip::after{content:"";position:absolute;top:50%;right:3px;width:3px;height:36px;margin-top:-18px;border-radius:2px;background:#c9a24a;opacity:.55}'+
   '#tpan.mem .tsn .tstx{display:none}'+
   '#tpan.mem .tsn.rev .tstx{display:inline}'+
   '#tpan.mem .tsn:not(.rev) .tsdh::after{content:" (לחץ להצגה)";font-weight:400;font-size:.8em;color:#8a7f66}'+
   '#tpan .tpsheet{display:none}'+
   '@media (max-width:999px){'+
     '#tpan{top:auto;left:0;right:0;width:auto;height:var(--tph,44vh);border-right:0;border-top:2px solid #c9a24a;border-radius:14px 14px 0 0;box-shadow:0 -6px 24px rgba(10,25,50,.28)}'+
     '#tpan .tpgrip{display:none}'+
     '#tpan .tpttl{display:none}'+
     '#tpan .tpsheet{display:block;flex:0 0 auto;height:22px;cursor:ns-resize;touch-action:none;text-align:center}'+
     '#tpan .tpsheet::after{content:"";display:inline-block;width:44px;height:4px;margin-top:9px;border-radius:2px;background:#c9a24a}'+
   '}'+
   /* רשימה (לוח הצד הכללי): בהיר וקריא על כל רקע */
   '#tosp{background:#fbf8f1!important;color:#2b2620!important}'+
   '#tosp h3{color:#7a5a14!important;border-bottom-color:#d9c77e!important}'+
   '#tosp .x{color:#7a5a14!important}'+
   '#tospb .tsdaf{font-weight:700;color:#7a5a14;margin:.7em 0 .2em;font-family:Vilna,serif}'+
   '#tospb .tsn{border-bottom:1px solid #eee5cc;color:#2b2620}'+
   '@media print{.tsm,#tsl,.tsa,.tsfoot,.tsx,#tosmenu,#tospop,#tpan,#toshov{display:none!important}}';
  document.head.appendChild(sty);

  /* אין התו ; בסיכומים (14.10.2026): גם נוסח שנבחר בעבר ושמור בשרת מוצג עם נקודה */
  function txt(it){var p=PUB[it.n],t=(p&&p.t)||it.sum||'';return t.replace(/\s*;\s*$/,'.').replace(/\s*;\s*/g,'. ')}
  function dispDh(it){return it.dhs||it.dh||''}
  function ge(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
  function narrow(){return window.matchMedia&&window.matchMedia('(max-width:760px)').matches}
  function wide(){return innerWidth>=1000}
  function touchy(){return !!(window.matchMedia&&window.matchMedia('(hover:none)').matches)}
  function pageIdx(dafKey){for(var i=0;i<D.pages.length;i++)if(D.pages[i].daf===dafKey)return i;return -1}
  function curDaf(){try{return D.pages[+document.getElementById('dafsel').value].daf}catch(e){return ''}}

  /* ---- אינדקס טקסט של דף: אותיות בלבד, בלי ניקוד, מקף ורווח כרווח אחד ---- */
  var NIKD=/[֑-ׇ]/, LET=/[א-ת]/, SEP=/[\s\-־]/;
  function normCtx(s){var o='',c;for(var i=0;i<s.length;i++){c=s[i];
      if(NIKD.test(c))continue;
      if(LET.test(c))o+=c;
      else if(SEP.test(c)){if(o.length&&o[o.length-1]!==' ')o+=' '}}
    return o.trim()}
  function pageRows(pi){var out=[];D.pages[pi].units.forEach(function(u){var e=document.getElementById('u'+u.id);if(e)out.push([u,e])});return out}
  function buildIndex(rows){
    var s='',map=[];
    rows.forEach(function(r){var m=r[1].querySelector(':scope > .main');if(!m)return;
      var w=document.createTreeWalker(m,NodeFilter.SHOW_TEXT,{acceptNode:function(n){
        return n.parentElement&&n.parentElement.closest('.tsm,.mlabel,.srcb')?NodeFilter.FILTER_REJECT:NodeFilter.FILTER_ACCEPT}});
      var n,lastP=null;
      while((n=w.nextNode())){
        var p=n.parentElement.closest('p');
        if(p!==lastP&&s.length&&s[s.length-1]!==' '){s+=' ';map.push(null)}
        lastP=p;
        var t=n.nodeValue;
        for(var i=0;i<t.length;i++){var c=t[i];
          if(NIKD.test(c))continue;
          if(LET.test(c)){s+=c;map.push([n,i+1])}
          else if(SEP.test(c)){if(s.length&&s[s.length-1]!==' '){s+=' ';map.push([n,i+1])}}}}
      if(s.length&&s[s.length-1]!==' '){s+=' ';map.push(null)}});
    return {s:s,map:map}}
  function findAt(idx,ctx,occ){
    var k=-1,from=0,seen=0;
    while(true){k=idx.s.indexOf(ctx,from);if(k<0)return null;
      var before=k===0||idx.s[k-1]===' ',after=k+ctx.length>=idx.s.length||idx.s[k+ctx.length]===' ';
      if(before&&after){seen++;if(seen===occ){
          var e=k+ctx.length-1;
          while(e>=k&&!idx.map[e])e--;
          var hit=idx.map[e]||null;
          if(hit){hit=hit.slice();var st=idx.map[k];if(st)hit.start=[st[0],Math.max(0,st[1]-1)]}
          return hit}}
      from=k+1}}

  /* עוגן אפס-רוחב בתוך הטקסט (אינו משנה שבירת שורות). הסימן עצמו נצבע בשכבה צפה בין השורות (tsLayer). */
  function mk(it,rule){
    var s=document.createElement('span');
    s.className='tsa';s.setAttribute('data-n',it.n);s.setAttribute('data-r',rule);
    s.setAttribute('contenteditable','false');s.setAttribute('aria-hidden','true');
    return s}
  function layerEl(){var l=document.getElementById('tsl');
    if(!l){l=document.createElement('div');l.id='tsl';l.setAttribute('aria-hidden','false');document.body.appendChild(l)}return l}
  var LQ=0;
  function tsLayerSoon(){if(LQ)return;LQ=requestAnimationFrame(function(){LQ=0;tsLayer()})}
  function tsLayer(){
    var L=layerEl(),f=document.getElementById('flow');if(!f)return;
    var anchors=[].slice.call(f.querySelectorAll('.tsa'));
    var have={};[].forEach.call(L.children,function(x){have[x.getAttribute('data-n')]=x});
    var seen={},fr=f.getBoundingClientRect(),placed=[];
    anchors.forEach(function(a){
      var n=a.getAttribute('data-n'),it=byN[n];if(!it)return;seen[n]=1;
      var el=have[n];
      if(!el){el=document.createElement('button');el.type='button';el.className='tsm'+(a.getAttribute('data-r')==='m'?' mv':'');
        el.setAttribute('data-n',n);el.textContent=it.hn;
        el.setAttribute('aria-label','תוספות '+it.hn+': '+dispDh(it));L.appendChild(el);have[n]=el}
      var r=document.createRange();r.selectNode(a);var b=r.getBoundingClientRect();
      if(!b.height&&!b.width&&!b.top){el.style.display='none';return}
      var vis=b.bottom>fr.top&&b.top<fr.bottom&&b.left>fr.left-4&&b.left<fr.right+4;
      if(!vis){el.style.display='none';return}
      el.style.display='';
      var w=el.offsetWidth||18,h=el.offsetHeight||12;
      /* מעל סוף המילה, בתוך הרווח שבין השורות; בצד שמאל של המילה (העברית נקראת מימין) */
      var left=Math.round(b.left-w*0.5),top=Math.round(b.top-h*0.78);
      /* סימנים באותו מקום: זה לצד זה, בלי חפיפה */
      for(var k=0;k<placed.length;k++){var q=placed[k];
        if(Math.abs(q.top-top)<h&&left<q.left+q.w+2&&left+w>q.left-2){left=q.left-w-2}}
      placed.push({top:top,left:left,w:w});
      el.style.left=left+'px';el.style.top=top+'px'});
    [].forEach.call(L.children,function(x){if(!seen[x.getAttribute('data-n')])x.remove()});
    tpSyncSoon()}
  window.tsLayer=tsLayer;
  addEventListener('resize',function(){tsLayerSoon();tpFit()});
  document.addEventListener('scroll',tsLayerSoon,true);
  setInterval(function(){if(document.querySelector('#flow .tsa'))tsLayer()},700);

  function lineOf(ref){var m=/\.(\d+)$/.exec(ref||'');return m?+m[1]:0}
  function placeMark(it,rows){
    var idx=buildIndex(rows),ctx=normCtx(it.t||''),hit=null,rule=String(it.rule||'1');
    if(ctx)hit=findAt(idx,ctx,it.occ||1);
    if(hit){
      var r=document.createRange();r.setStart(hit[0],hit[1]);r.collapse(true);
      /* טווח המילים המעוגנות, להדגשה בריחוף (נוצר לפני הוספת העוגן) */
      try{if(hit.start){var rg=document.createRange();rg.setStart(hit.start[0],hit.start[1]);rg.setEnd(hit[0],hit[1]);RANGES[it.n]=rg}}catch(e){}
      r.insertNode(mk(it,rule));PLACED[it.n]=rule;delete MOVED[it.n];return true}
    /* עוגן לא נמצא: סוף שורת הגמרא הקרובה (שורה קטנה או שווה לשורת התוספות, ואם אין - הראשונה) */
    var best=null,first=null;
    rows.forEach(function(x){var ln=lineOf(x[0].ref);if(!ln)return;if(!first)first=x;if(ln<=it.line)best=x});
    var tgt=best||first||rows[rows.length-1];
    if(!tgt)return false;
    var m=tgt[1].querySelector(':scope > .main');if(!m)return false;
    var ps=m.querySelectorAll(':scope > p'),host=ps.length?ps[ps.length-1]:m;
    host.appendChild(mk(it,'m'));
    PLACED[it.n]='m';MOVED[it.n]=true;return true}
  function hiWord(n,on){
    try{if(!window.CSS||!CSS.highlights||!window.Highlight)return;
      if(on&&RANGES[n])CSS.highlights.set('tosw',new Highlight(RANGES[n]));else CSS.highlights.delete('tosw')}catch(e){}}

  /* ---- בניית הערה ---- */
  /* פנים התוספות נטענים בעצלתיים מקובץ נפרד (tos-face-<מסכת>.json), כדי שהדף לא יישא מאות קילובייט.
     אין קישור ספריא ואין תווית מקור בכל כרטיס (14.10.2026): המקור נכתב פעם אחת באתר. */
  var FACE=null,FACEQ=[];
  function faceLoad(cb){
    if(FACE){cb();return}
    FACEQ.push(cb);if(FACEQ.length>1)return;
    var src=TS.face;if(!src){FACE={};FACEQ.splice(0).forEach(function(f){f()});return}
    fetch(src).then(function(r){return r.json()}).then(function(j){FACE=j||{}}).catch(function(){FACE={}}).then(function(){FACEQ.splice(0).forEach(function(f){f()})})}
  function faceHTML(it){
    var f=(FACE&&FACE[it.n])||{},t=f.text||it.text||'',i=t.indexOf(' - '),h=ge(t);
    if(i>0&&i<120)h='<b>'+ge(t.slice(0,i))+'</b> - '+ge(t.slice(i+3));
    return h}
  function sentMap(){try{return JSON.parse(lsGet('lg-tos-sent','{}'))||{}}catch(e){return {}}}
  function admSugHTML(it){
    var l=SUGS[it.n]||[];if(!l.length)return '';
    return '<div class="tsah">הצעות לתיקון ('+l.length+')</div>'+l.map(function(g){
      return '<div class="tssgq" data-id="'+ge(g.id)+'"><div><b>'+ge(g.name||'אורח')+'</b> · '+ge((g.ctx&&g.ctx.b)||'')+(g.ctx&&g.ctx.a?' · '+ge(g.ctx.a):'')+'</div>'+
        '<div class="bf">'+ge(g.was)+'</div><div>'+ge(g.note)+'</div>'+
        '<button class="go" data-id="'+ge(g.id)+'" data-n="'+it.n+'" onclick="tosSgDecide(this,\'accepted\')">אשר</button> '+
        '<button data-id="'+ge(g.id)+'" data-n="'+it.n+'" onclick="tosSgDecide(this,\'rejected\')">דחה</button> '+
        '<button data-id="'+ge(g.id)+'" data-n="'+it.n+'" onclick="tosSgEdit(this)">ערוך</button></div>'}).join('')}
  function admHTML(it){
    if(!(typeof isAdmin==='function'&&isAdmin()))return '';
    var a=ADM,h='<div class="tsadm"><div class="tsah">למנהל בלבד · מיקום הסימן: '+ge(RULE[PLACED[it.n]||String(it.rule||'1')]||'')+(MOVED[it.n]?' <span class="tsw">(העוגן זז - לאשר או לתקן)</span>':'')+'</div>'+admSugHTML(it);
    if(it.g&&!(a&&a.styles&&a.styles[it.n])){
      var pk0=a&&a.picks&&a.picks[it.n],nt0=a&&a.notes&&a.notes[it.n];
      return h+'<div>'+(pk0?'הוגה על ידך.':'נכתב בבית החרושת ועדיין לא הוגה.')+'</div>'+
        '<textarea class="tsedit" data-n="'+it.n+'" aria-label="עריכה חופשית">'+ge(txt(it))+'</textarea>'+
        (pk0?'':'<button class="go" data-n="'+it.n+'" onclick="tosApprove(this)">אישור ללא שינוי</button> ')+
        '<button data-n="'+it.n+'" onclick="tosSaveText(this)">שמור את הנוסח שערכתי</button> '+
        '<input class="tsnote" data-n="'+it.n+'" placeholder="הערה לקלוד על התוספות הזה" value="'+ge((nt0&&nt0.t)||'')+'">'+
        '<button data-n="'+it.n+'" onclick="tosSaveNote(this)">שמור הערה</button></div>'}
    if(!a||!a.styles||!a.styles[it.n]){return h+(window.__TOSTEST?'<div>הנוסח נבחר במסך "מבחן מנועים" שבתפריט תוס\'.</div>':'<div>חמשת הנוסחאות נטענות מנקודת הקליטה...</div>')+'</div>'}
    var st=a.styles[it.n],pk=a.picks&&a.picks[it.n],nt=a.notes&&a.notes[it.n];
    STY.forEach(function(s){
      if(!st[s[0]])return;
      h+='<div class="tsv'+(pk&&pk.p===s[0]?' cur':'')+'"><span class="tsvn">'+ge(s[1])+'</span><span class="tsvt">'+ge(st[s[0]]||'')+'</span>'+
         '<button class="go" data-n="'+it.n+'" data-k="'+s[0]+'" onclick="tosPick(this)">בחר</button></div>'});
    h+='<textarea class="tsedit" data-n="'+it.n+'" aria-label="עריכה חופשית">'+ge(txt(it))+'</textarea>'+
       '<button data-n="'+it.n+'" onclick="tosSaveText(this)">שמור את הנוסח שערכתי</button> '+
       '<input class="tsnote" data-n="'+it.n+'" placeholder="הערה לקלוד על התוספות הזה (למשל: חסר התירוץ השני)" value="'+ge((nt&&nt.t)||'')+'">'+
       '<button data-n="'+it.n+'" onclick="tosSaveNote(this)">שמור הערה</button></div>';
    return h}
  function noteHTML(it){
    var sent=sentMap()[it.n];
    return '<div class="tsn" data-n="'+it.n+'"><span class="tsnum" role="button" tabindex="0" aria-label="חזרה למקום בטקסט, תוספות '+ge(it.hn)+'">'+ge(it.hn)+'</span><span class="tsdh">'+ge(dispDh(it))+'</span>'+
      (it.g&&!(ADM&&ADM.picks&&ADM.picks[it.n])?'<span class="tsug" title="נכתב בבית החרושת ועדיין לא עבר עיון של המנהל">לא הוגה</span>':'')+
      (it.u&&!TOK[it.n]?'<span class="tsug" title="נפסל בביקורת האוטומטית ופורסם עד עיון של המנהל. הכרעה: תפריט תוס\' ← בדיקת תוספות">*</span>':'')+
      '<span class="tstx">'+ge(txt(it))+'</span>'+
      '<span class="tsbt"><button class="tsin" type="button" onclick="tosFace(this)" aria-expanded="false" aria-label="פנים התוספות">פנים</button>'+
      '<button type="button" onclick="tosCopy(this)" aria-label="העתק">העתק</button>'+
      '<button type="button" class="tssh lk-sh-btn" onclick="tosShare(this)" aria-label="שתף את התוספות הזה" title="שיתוף התוספות הזה: ווטסאפ, הודעה, מייל, טלגרם, קישור וקוד QR">שתף</button>'+
      '<button type="button" onclick="tosSg(this)" aria-label="הצע תיקון על התוספות">הצע תיקון</button></span>'+
      '<div class="tsface" hidden></div><div class="tssgbox" hidden></div>'+
      (sent?'<span class="tssent">הצעתך התקבלה לעיון</span>':'')+admHTML(it)+'</div>'}
  function noteOf(b){return b.closest('.tsn')}
  function faceOpen(box,open){
    var f=box.querySelector('.tsface'),b=box.querySelector('.tsin');if(!f||!b)return;
    var n=+box.getAttribute('data-n');
    if(open){
      faceLoad(function(){var it=byN[n];if(it&&!f.getAttribute('data-ok')){f.innerHTML=faceHTML(it);f.setAttribute('data-ok','1')}});
      f.removeAttribute('hidden')}else f.setAttribute('hidden','');
    b.setAttribute('aria-expanded',open?'true':'false');b.textContent=open?'סגור':'פנים'}
  window.tosFace=function(b){var box=noteOf(b);if(!box)return;var f=box.querySelector('.tsface');faceOpen(box,f.hasAttribute('hidden'))};
  /* שיתוף תוס' (14.10.2026): חלונית lk-share.js, קישור שפותח את הדף ואת הכרטיס הזה */
  window.tosShare=function(b){
    var box=noteOf(b),n=+box.getAttribute('data-n'),it=byN[n];if(!it||!window.LKShare)return;
    LKShare.tos({n:n,daf:it.daf,dh:dispDh(it),sum:txt(it)})};
  window.tosCopy=function(b){
    var box=noteOf(b),n=+box.getAttribute('data-n'),it=byN[n];if(!it)return;
    var f=box.querySelector('.tsface');
    var t='תוספות '+it.hn+', ד"ה '+dispDh(it)+': '+txt(it);
    if(f&&!f.hasAttribute('hidden')&&f.textContent)t+=String.fromCharCode(10)+f.textContent;
    function done(){if(typeof toast==='function')toast('הועתק',1800)}
    try{navigator.clipboard.writeText(t).then(done,function(){fb()})}catch(e){fb()}
    function fb(){var ta=document.createElement('textarea');ta.value=t;ta.style.position='fixed';ta.style.opacity='0';document.body.appendChild(ta);ta.select();try{document.execCommand('copy');done()}catch(e){}ta.remove()}};

  /* ---- הצעת תיקון: עורך קטן בתוך הכרטיס. נכנס לתור ההצעות הקיים (סוג note, k=tos:<מפתח>) ---- */
  window.tosSg=function(b){
    var box=noteOf(b),n=+box.getAttribute('data-n'),it=byN[n];if(!it)return;
    var sg=box.querySelector('.tssgbox');if(!sg)return;
    if(!sg.hasAttribute('hidden')){sg.setAttribute('hidden','');return}
    var nm='';try{nm=lsGet('lg-sg-name','')}catch(e){}
    sg.innerHTML='<div><b>הצע תיקון</b> · תוספות '+ge(it.hn)+'</div>'+
      '<select class="sgty" aria-label="סוג התיקון">'+SGT.map(function(x){return '<option value="'+x[0]+'">'+ge(x[1])+'</option>'}).join('')+'</select>'+
      '<textarea class="sgtx" aria-label="הנוסח המוצע">'+ge(txt(it))+'</textarea>'+
      '<input class="sgwhy" placeholder="למה? (לא חובה)" maxlength="60" aria-label="הערה קצרה">'+
      '<input class="sgnm" placeholder="שמך (לא חובה)" maxlength="40" value="'+ge(nm)+'" aria-label="שם">'+
      '<input class="sghp" tabindex="-1" autocomplete="off" style="position:absolute;left:-9999px" aria-hidden="true">'+
      '<div class="tssgb"><button class="go" type="button" onclick="tosSgSend(this)">שלח</button><button type="button" onclick="tosSg(this)">בטל</button><span class="sgmsg" role="status"></span></div>';
    sg.removeAttribute('hidden');
    var ta=sg.querySelector('.sgtx');if(ta)ta.focus()};
  window.tosSgSend=function(b){
    var sg=b.closest('.tssgbox'),box=noteOf(b),n=+box.getAttribute('data-n'),it=byN[n];if(!it)return;
    var ty=sg.querySelector('.sgty'),tx=sg.querySelector('.sgtx'),why=sg.querySelector('.sgwhy'),nm=sg.querySelector('.sgnm'),hp=sg.querySelector('.sghp'),msg=sg.querySelector('.sgmsg');
    var note=tx.value.trim(),cur=txt(it);
    if(!note){msg.textContent='כתוב מה להציע.';return}
    if(ty.value==='nusach'&&note===cur.trim()){msg.textContent='הנוסח זהה למה שמוצג. שנה אותו, או בחר סוג אחר.';return}
    if(/(https?:\/\/|www\.)/i.test(note)){msg.textContent='הצעה שיש בה קישור אינה מתקבלת.';return}
    var tl='';SGT.forEach(function(x){if(x[0]===ty.value)tl=x[1]});
    try{lsSet('lg-sg-name',nm.value.trim())}catch(e){}
    var id={pid:'',pt:''};try{if(typeof pident==='function')id=pident()}catch(e){}
    var rec={slug:SLUG,masechet:(typeof D!=='undefined'&&D.masechet)||'',daf:it.daf,uid:'',k:'tos:'+it.n,
      ctx:{b:'הצעה על תוספות '+it.hn+' | '+tl,a:why.value.trim()},was:cur,note:note,name:nm.value.trim(),type:'note',
      pid:id.pid,pt:id.pt,hp:hp.value,t:Date.now()};
    try{if(typeof sgGrp==='function')rec.grp=sgGrp()}catch(e){}
    b.disabled=true;msg.textContent='שולח...';
    api('/suggest',{method:'POST',body:JSON.stringify(rec)}).then(function(j){
      var m=sentMap();m[it.n]=Date.now();lsSet('lg-tos-sent',JSON.stringify(m));
      sg.setAttribute('hidden','');
      var s=document.createElement('span');s.className='tssent';s.textContent='הצעתך התקבלה לעיון. תודה.';
      var old=box.querySelector('.tssent');if(old)old.remove();
      sg.insertAdjacentElement('afterend',s);
      if(typeof toast==='function')toast('ההצעה נשלחה לעורך. תודה רבה.',3500)})
    .catch(function(e){b.disabled=false;msg.textContent=(e&&e.message)||'השליחה נכשלה, נסה שוב.'})};
  window.tosSgEdit=function(b){
    var n=+b.getAttribute('data-n'),id=b.getAttribute('data-id'),box=document.querySelector('.tsn[data-n="'+n+'"] .tsedit');
    var l=SUGS[n]||[],g=null;l.forEach(function(x){if(x.id===id)g=x});
    if(box&&g){box.value=g.note;box.focus()}};
  window.tosSgDecide=function(b,st){
    var n=+b.getAttribute('data-n'),id=b.getAttribute('data-id'),l=SUGS[n]||[],g=null;
    l.forEach(function(x){if(x.id===id)g=x});if(!g)return;
    var reason='';
    if(st==='rejected'){reason=prompt('סיבת הדחייה (קצרה, לא חובה):','')||''}
    b.disabled=true;
    function fin(){SUGS[n]=l.filter(function(x){return x.id!==id});tsMark();tpRender(true);
      if(typeof toast==='function')toast(st==='accepted'?'ההצעה אושרה והנוסח עודכן מיד':'ההצעה נדחתה')}
    var p=Promise.resolve();
    if(st==='accepted')p=post({n:n,pick:'custom',txt:g.note,from:'suggest'}).then(function(j){applyDoc(j)});
    p.then(function(){return api('/decide',{method:'POST',body:JSON.stringify({id:id,st:st,reason:reason,now:st==='accepted'?g.note:''})})})
     .then(fin).catch(function(e){b.disabled=false;if(typeof toast==='function')toast('לא נשמר: '+(e&&e.message||''),5000)})};

  /* ---- סימון הדף ---- */
  function strip(){
    document.querySelectorAll('#flow .tsa,#flow .tsfoot,#flow .tsx').forEach(function(x){x.remove()});
    var L=document.getElementById('tsl');if(L)L.innerHTML='';
    PLACED={};RANGES={};hiWord(0,false)}
  function off(){return mode==='off'||(typeof BOOK!=='undefined'&&BOOK)||(typeof PRINTING!=='undefined'&&PRINTING)||(typeof EDIT!=='undefined'&&EDIT)||(typeof SUGM!=='undefined'&&SUGM)}
  var warned=false,preloaded=false;
  window.tsMark=function(){
    var f=document.getElementById('flow');if(!f)return;
    strip();
    if(off()){drawList();tpRender(true);return}
    var byDaf={};
    TS.items.forEach(function(it){(byDaf[it.daf]=byDaf[it.daf]||[]).push(it)});
    var bad=[];
    Object.keys(byDaf).forEach(function(daf){
      var pi=pageIdx(daf);if(pi<0)return;
      var rows=pageRows(pi);if(!rows.length)return;
      var items=byDaf[daf].slice().sort(function(a,b){return b.n-a.n});
      var placed=0;
      items.forEach(function(it){if(placeMark(it,rows))placed++});
      if(placed!==items.length)bad.push(daf+': '+placed+' מתוך '+items.length);
      if(mode==='foot'){
        var last=rows[rows.length-1][1];
        var fo=document.createElement('div');fo.className='tsfoot';fo.setAttribute('contenteditable','false');
        fo.innerHTML='<div class="tsh">תוספות על העמוד <button type="button" class="tsall" onclick="tosAll(this)" data-open="1">פתח הכל</button></div>'+byDaf[daf].slice().sort(function(a,b){return a.n-b.n}).map(noteHTML).join('');
        last.insertAdjacentElement('afterend',fo);
        if(CFG.face)fo.querySelectorAll('.tsn').forEach(function(x){faceOpen(x,true)})}});
    if(bad.length&&typeof isAdmin==='function'&&isAdmin()&&!warned){warned=true;
      if(typeof toast==='function')toast('אזהרת שלמות בתוספות: '+bad.join('; '),6000)}
    drawList();tpRender(true);tsLayerSoon();
    /* טעינה מוקדמת ברקע של פנים התוספות, כדי שכרטיס הריחוף לא ימתין */
    if(!preloaded){preloaded=true;setTimeout(function(){faceLoad(function(){})},1200)}};
  window.tosAll=function(b){
    var open=b.getAttribute('data-open')==='1',fo=b.closest('.tsfoot');if(!fo)return;
    fo.querySelectorAll('.tsn').forEach(function(x){faceOpen(x,open)});
    b.setAttribute('data-open',open?'0':'1');b.textContent=open?'כווץ הכל':'פתח הכל'};

  /* ---- גלילה אל העוגן ---- */
  function hot(n){document.querySelectorAll('.tsm[data-n="'+n+'"]').forEach(function(x){x.classList.add('hot');setTimeout(function(){x.classList.remove('hot')},1800)});
    document.querySelectorAll('.tsn[data-n="'+n+'"]').forEach(function(x){x.classList.add('hot');setTimeout(function(){x.classList.remove('hot')},1800)})}
  function scrollToAnchor(n){
    var a=document.querySelector('#flow .tsa[data-n="'+n+'"]');
    if(!a){var it=byN[n];var pi=it?pageIdx(it.daf):-1;
      if(pi>=0&&typeof toDaf==='function'){toDaf(pi);setTimeout(function(){scrollToAnchor(n)},160)}return}
    a.scrollIntoView({block:'center',behavior:'auto'});
    /* מגירה תחתונה: העוגן מעל המגירה, לא מתחתיה */
    var p=document.getElementById('tpan');
    if(p&&p.classList.contains('open')&&!wide()){
      var r=a.getBoundingClientRect(),top=innerHeight-p.offsetHeight;
      if(r.bottom>top-24)window.scrollBy(0,r.bottom-(top-24)+10)}
    hot(n);hiWord(n,true);clearTimeout(scrollToAnchor.t);scrollToAnchor.t=setTimeout(function(){hiWord(n,false)},2600);
    tsLayerSoon()}

  /* ---- כרטיס צף ---- */
  var HOV={n:0,sticky:false,timer:0,closeT:0};
  function hovEl(){var p=document.getElementById('toshov');
    if(!p){p=document.createElement('div');p.id='toshov';p.setAttribute('role','dialog');p.setAttribute('aria-label','תוספות');document.body.appendChild(p);
      p.addEventListener('mouseenter',function(){clearTimeout(HOV.closeT)});
      p.addEventListener('mouseleave',function(){if(!HOV.sticky)hovCloseSoon()})}
    return p}
  function hovClose(){clearTimeout(HOV.timer);clearTimeout(HOV.closeT);var p=document.getElementById('toshov');if(p)p.classList.remove('open');
    if(HOV.n)hiWord(HOV.n,false);HOV.n=0;HOV.sticky=false}
  function hovCloseSoon(){clearTimeout(HOV.closeT);HOV.closeT=setTimeout(hovClose,260)}
  function hovShow(n,sticky){
    var it=byN[n];if(!it||off())return;
    var anchor=document.querySelector('#flow .tsa[data-n="'+n+'"]'),mkEl=document.querySelector('#tsl .tsm[data-n="'+n+'"]');
    var p=hovEl();
    if(HOV.n&&HOV.n!==n)hiWord(HOV.n,false);
    HOV.n=n;HOV.sticky=!!sticky;
    p.innerHTML='<div class="tshov0"><button type="button" onclick="tosPin()" aria-label="נעץ בפאנל הצד">נעץ</button><span class="sp"></span><button type="button" onclick="tosHovClose()" aria-label="סגור">סגור</button></div>'+noteHTML(it);
    var box=p.querySelector('.tsn');
    faceOpen(box,true);
    p.classList.add('open');
    hiWord(n,true);
    /* מיקום: מתחת לשורה המעוגנת, ואם אין מקום - מעליה; לעולם לא על השורה עצמה ולא מחוץ למסך */
    var rr=null;
    if(anchor){var r=document.createRange();r.selectNode(anchor);rr=r.getBoundingClientRect()}
    var mr=mkEl?mkEl.getBoundingClientRect():null;
    var lineTop=rr&&(rr.height||rr.top)?rr.top:(mr?mr.bottom:innerHeight/2),lineBot=rr&&(rr.height||rr.top)?rr.bottom:(mr?mr.bottom+10:innerHeight/2);
    if(mr&&mr.height)lineTop=Math.min(lineTop,mr.top);
    var w=p.offsetWidth,h=p.offsetHeight;
    var cx=rr&&(rr.width||rr.left)?rr.left:(mr?mr.left:innerWidth/2);
    var left=Math.min(Math.max(8,cx-w/2),innerWidth-w-8);
    var top=lineBot+10;
    if(top+h>innerHeight-8){top=lineTop-h-10;if(top<8){top=Math.max(8,Math.min(lineBot+10,innerHeight-h-8))}}
    p.style.left=left+'px';p.style.top=top+'px'}
  window.tosHovClose=hovClose;
  window.tosPin=function(){var n=HOV.n;hovClose();
    if(!n)return;
    if(mode!=='panel')tosSet('panel');
    else tpRender(true);
    tpFocus(n,true)};

  /* ---- פתיחת הערה ---- */
  function openNote(n,el,how){
    var it=byN[n];if(!it)return;
    var ts=touchy();
    if(how==='click'&&!ts){
      if(mode==='foot'){var t=document.querySelector('.tsfoot .tsn[data-n="'+n+'"]');
        if(t){t.scrollIntoView({block:'center',behavior:'smooth'});hot(n)}return}
      if(mode==='panel'){tpOpen();tpFocus(n,false);hot(n);return}
      if(mode==='list'){panelOpen();hot(n);var q=document.querySelector('#tospb .tsn[data-n="'+n+'"]');if(q)q.scrollIntoView({block:'nearest'});return}
    }
    /* בצד, ובנייד בכל תצוגה: כרטיס צף. הקשה אחת פותחת, הקשה מחוץ לו סוגרת */
    hovShow(n,true);hot(n)}
  document.addEventListener('click',function(ev){
    var m=ev.target.closest&&ev.target.closest('.tsm');
    if(m){ev.preventDefault();ev.stopPropagation();openNote(+m.getAttribute('data-n'),m,'click');return}
    var menu=document.getElementById('tosmenu');
    if(menu&&menu.classList.contains('open')&&!ev.target.closest('#tosmenu,#tosbtn,#tosmb'))menu.classList.remove('open');
    if(HOV.n&&!ev.target.closest('#toshov')&&!ev.target.closest('.tsm'))hovClose()},true);
  document.addEventListener('keydown',function(ev){
    if(ev.key==='Escape'){hovClose();var m=document.getElementById('tosmenu');if(m)m.classList.remove('open')}
    var t=ev.target;
    if((ev.key==='Enter'||ev.key===' ')&&t.classList){
      if(t.classList.contains('tsm')){ev.preventDefault();openNote(+t.getAttribute('data-n'),t,'click')}
      else if(t.classList.contains('tsnum')){ev.preventDefault();tsBack(t)}}});
  document.addEventListener('mouseover',function(ev){
    if(mode==='off'||touchy()||off())return;
    var m=ev.target.closest&&ev.target.closest('.tsm');
    if(!m)return;
    clearTimeout(HOV.timer);clearTimeout(HOV.closeT);
    var n=+m.getAttribute('data-n');
    if(HOV.n===n)return;
    HOV.timer=setTimeout(function(){hovShow(n,false)},250)});
  document.addEventListener('mouseout',function(ev){
    var m=ev.target.closest&&ev.target.closest('.tsm');
    if(!m)return;
    clearTimeout(HOV.timer);
    if(HOV.n&&!HOV.sticky)hovCloseSoon()});

  /* ---- רשימה (לוח צד כללי) ---- */
  function ensurePanel(){
    if(document.getElementById('tosp'))return;
    var p=document.createElement('div');p.className='panel';p.id='tosp';
    p.innerHTML='<button class="x" onclick="panel(&quot;tosp&quot;)">×</button><h3>תוספות - רשימה</h3><div id="tospb"></div>';
    document.body.appendChild(p)}
  function drawList(){
    ensurePanel();
    var b=document.getElementById('tospb');if(!b)return;
    if(mode!=='list'){b.innerHTML='';return}
    var by={},order=[];
    SORTED.forEach(function(it){if(!by[it.daf]){by[it.daf]=[];order.push(it.daf)}by[it.daf].push(it)});
    b.innerHTML=order.map(function(d){return '<div class="tsdaf">דף '+ge(d.replace(/[.:]$/,''))+(d.slice(-1)===':'?' ע"ב':' ע"א')+'</div>'+by[d].map(noteHTML).join('')}).join('')||'אין';
    if(CFG.face)b.querySelectorAll('.tsn').forEach(function(x){faceOpen(x,true)})}
  function panelOpen(){ensurePanel();var p=document.getElementById('tosp');if(p&&!p.classList.contains('open'))panel('tosp')}

  /* ---- פאנל הצד / מגירה ---- */
  var TP={cur:0,sig:'',quiet:0,q:''};
  var FS={s:'13px',m:'15px',l:'18px'};
  function tpEl(){
    var p=document.getElementById('tpan');
    if(p)return p;
    p=document.createElement('aside');p.id='tpan';p.setAttribute('aria-label','תוספות');p.tabIndex=-1;
    p.innerHTML='<div class="tpsheet" aria-hidden="true"></div>'+
      '<div class="tphd">'+
        '<div class="tpr"><span class="tpttl">תוספות</span>'+
          '<select id="tpmode" aria-label="תצוגת התוספות">'+MODES.map(function(x){return '<option value="'+x[0]+'">'+ge(x[1])+'</option>'}).join('')+'</select>'+
          '<button type="button" id="tpprev" aria-label="התוספות הקודם" title="קודם">&#9650;</button>'+
          '<button type="button" id="tpnext" aria-label="התוספות הבא" title="הבא">&#9660;</button>'+
          '<button type="button" id="tpx" aria-label="סגור את הפאנל" title="סגור">&times;</button></div>'+
        '<div class="tpr" style="margin-top:.3em">'+
          '<button type="button" id="tpfs-s" aria-label="גופן קטן">א</button><button type="button" id="tpfs-m" aria-label="גופן רגיל" style="font-size:.95em">א</button><button type="button" id="tpfs-l" aria-label="גופן גדול" style="font-size:1.15em">א</button>'+
          '<button type="button" id="tpface" aria-pressed="false">פנים תמיד</button>'+
          '<button type="button" id="tppage" aria-pressed="false">עמוד</button>'+
          '<button type="button" id="tpmem" aria-pressed="false" title="מצב שינון: רק הד&quot;ה, לחיצה חושפת">שינון</button>'+
        '<input id="tpq" type="search" placeholder="חיפוש, או מספר" aria-label="חיפוש בתוספות המסכת"></div>'+
      '</div><div id="tpl"></div><div class="tpgrip" aria-hidden="true"></div>';
    document.body.appendChild(p);
    p.querySelector('#tpmode').onchange=function(){tosSet(this.value)};
    p.querySelector('#tpx').onclick=function(){tosSet('off')};
    p.querySelector('#tpprev').onclick=function(){tpStep(-1)};
    p.querySelector('#tpnext').onclick=function(){tpStep(1)};
    ['s','m','l'].forEach(function(k){p.querySelector('#tpfs-'+k).onclick=function(){CFG.fs=k;cfgSave();tpFit();tpBtns()}});
    p.querySelector('#tpface').onclick=function(){CFG.face=CFG.face?0:1;cfgSave();tpRender(true);if(mode==='foot'||mode==='list')tsMark();tpBtns()};
    p.querySelector('#tppage').onclick=function(){CFG.page=CFG.page?0:1;cfgSave();tpRender(true);tpBtns()};
    p.querySelector('#tpmem').onclick=function(){CFG.mem=CFG.mem?0:1;cfgSave();tpFit();tpBtns()};
    p.querySelector('#tpq').addEventListener('input',function(){TP.q=this.value;clearTimeout(tpEl.qt);tpEl.qt=setTimeout(function(){tpRender(true)},160)});
    /* לחיצה על כרטיס: גלילה לעוגן. כפתורים ושדות בתוך הכרטיס עובדים בפני עצמם */
    p.querySelector('#tpl').addEventListener('click',function(ev){
      var box=ev.target.closest('.tsn');if(!box)return;
      if(ev.target.closest('button,textarea,input,select,a,.tsadm,.tssgbox,.tsface'))return;
      var n=+box.getAttribute('data-n');
      if(CFG.mem)box.classList.toggle('rev');
      TP.cur=n;TP.quiet=Date.now()+3000;tpMarkCur();scrollToAnchor(n)});
    p.querySelector('#tpl').addEventListener('scroll',function(){TP.quiet=Date.now()+2500},{passive:true});
    p.addEventListener('keydown',function(ev){
      if(ev.target.closest('input,textarea,select'))return;
      if(ev.key==='ArrowDown'||ev.key==='ArrowLeft'){ev.preventDefault();tpStep(1)}
      else if(ev.key==='ArrowUp'||ev.key==='ArrowRight'){ev.preventDefault();tpStep(-1)}
      else if(ev.key==='Escape'){ev.preventDefault();tosSet('off')}});
    /* גרירת הקצה (רוחב) במסך רחב */
    var g=p.querySelector('.tpgrip');
    g.addEventListener('pointerdown',function(ev){ev.preventDefault();g.setPointerCapture(ev.pointerId);
      function mv(e){CFG.w=Math.max(240,Math.min(560,Math.round(e.clientX)));tpFit()}
      function up(){g.removeEventListener('pointermove',mv);g.removeEventListener('pointerup',up);cfgSave()}
      g.addEventListener('pointermove',mv);g.addEventListener('pointerup',up)});
    /* גרירת הידית (גובה) במגירה: חצי מסך / מסך מלא / מקופלת */
    var sh=p.querySelector('.tpsheet');
    sh.addEventListener('pointerdown',function(ev){ev.preventDefault();sh.setPointerCapture(ev.pointerId);
      function mv(e){var h=Math.round(innerHeight-e.clientY);h=Math.max(70,Math.min(innerHeight-60,h));p.style.setProperty('--tph',h+'px')}
      function up(){sh.removeEventListener('pointermove',mv);sh.removeEventListener('pointerup',up);tsLayerSoon()}
      sh.addEventListener('pointermove',mv);sh.addEventListener('pointerup',up)});
    sh.addEventListener('dblclick',function(){var h=p.offsetHeight;p.style.setProperty('--tph',(h<innerHeight*0.6?Math.round(innerHeight*0.88):Math.round(innerHeight*0.44))+'px')});
    return p}
  function tpBtns(){
    var p=document.getElementById('tpan');if(!p)return;
    ['s','m','l'].forEach(function(k){p.querySelector('#tpfs-'+k).classList.toggle('on',CFG.fs===k)});
    function on(id,v,t){var b=p.querySelector(id);b.classList.toggle('on',!!v);b.setAttribute('aria-pressed',v?'true':'false');if(t)b.textContent=t}
    on('#tpface',CFG.face);on('#tppage',CFG.page,CFG.page?'העמוד':'כל הפרק');on('#tpmem',CFG.mem);
    var md=p.querySelector('#tpmode');if(md)md.value=mode}
  function tpFit(){
    var p=document.getElementById('tpan');if(!p)return;
    p.style.setProperty('--tpw',Math.max(240,Math.min(560,CFG.w|0))+'px');
    p.style.setProperty('--tpfs',FS[CFG.fs]||'15px');
    /* סרגל הכפתורים התחתון של האתר: הפאנל והמגירה יושבים מעליו */
    var mb=document.getElementById('mbot'),bh=0;
    try{if(mb&&getComputedStyle(mb).display!=='none'&&getComputedStyle(mb).position==='fixed')bh=Math.round(mb.getBoundingClientRect().height)}catch(e){}
    p.style.bottom=bh+'px';
    p.classList.toggle('mem',!!CFG.mem)}
  function tpShown(){return mode==='panel'&&!off()}
  function tpOpen(){var p=tpEl();tpFit();tpBtns();p.classList.add('open');if(wide()){var s=document.getElementById('flow');}}
  function tpClose(){var p=document.getElementById('tpan');if(p)p.classList.remove('open')}
  function tpList(){
    var l=SORTED;
    if(CFG.page){var d=curDaf();
      if(d){var m=l.filter(function(it){return it.daf===d});if(m.length)l=m}}
    var q=(TP.q||'').trim();
    if(q){
      var nq=normCtx(q),num=q.replace(/[\s"'׳״]/g,'').replace(/^תוס/,'');
      l=SORTED.filter(function(it){
        var hn=(it.hnHeb||'').replace(/["']/g,'');
        if(num&&(hn===num||String(it.disp||it.n)===num))return true;
        return nq.length>=2&&normCtx(it.dh+' '+txt(it)).indexOf(nq)>=0})}
    return l}
  /* מציג את התוספות של העמוד הנוכחי, ומדגיש את אלה שהעוגן שלהם נראה כעת */
  function tpRender(force){
    var p=document.getElementById('tpan');
    if(!tpShown()){if(p)p.classList.remove('open');return}
    p=tpEl();tpFit();tpBtns();
    var l=tpList();
    var sig=l.map(function(it){return it.n}).join(',')+'|'+CFG.face+'|'+(ADM?1:0)+'|'+Object.keys(PUB).length+'|'+JSON.stringify(Object.keys(SUGS).map(function(k){return k+':'+SUGS[k].length}));
    if(!force&&sig===TP.sig){tpMarkCur();return}
    TP.sig=sig;
    var b=p.querySelector('#tpl'),keep=b.scrollTop;
    var h='',last='';
    l.forEach(function(it){
      if(it.daf!==last){last=it.daf;h+='<div class="tsdaf">דף '+ge(it.daf.replace(/[.:]$/,''))+(it.daf.slice(-1)===':'?' ע"ב':' ע"א')+'</div>'}
      h+=noteHTML(it)});
    b.innerHTML=h||'<div class="tpe">אין תוספות להצגה כאן.</div>';
    if(CFG.face)b.querySelectorAll('.tsn').forEach(function(x){faceOpen(x,true)});
    b.scrollTop=keep;
    p.classList.add('open');
    tpMarkCur()}
  function tpVisible(){
    var out=[],L=document.getElementById('tsl');if(!L)return out;
    var mid=innerHeight/2;
    [].forEach.call(L.children,function(m){if(m.style.display==='none')return;
      var r=m.getBoundingClientRect();out.push({n:+m.getAttribute('data-n'),d:Math.abs(r.top-mid)})});
    out.sort(function(a,b){return a.d-b.d});return out}
  function tpMarkCur(){
    var p=document.getElementById('tpan');if(!p||!p.classList.contains('open'))return;
    var vis=tpVisible(),set={};vis.forEach(function(v){set[v.n]=1});
    if(!TP.pinned&&vis.length&&Date.now()>TP.quiet)TP.cur=vis[0].n;
    var curEl=null;
    p.querySelectorAll('#tpl .tsn').forEach(function(x){
      var n=+x.getAttribute('data-n');
      x.classList.toggle('vis',!!set[n]);
      var c=n===TP.cur;x.classList.toggle('cur',c);if(c)curEl=x});
    if(curEl&&Date.now()>TP.quiet){
      var b=p.querySelector('#tpl'),r=curEl.getBoundingClientRect(),br=b.getBoundingClientRect();
      if(r.top<br.top+4||r.bottom>br.bottom-4){b.scrollTop+= (r.top-br.top)-(br.height/2-r.height/2)}}}
  var TPQ=0;
  function tpSyncSoon(){if(TPQ||mode!=='panel')return;TPQ=setTimeout(function(){TPQ=0;
    if(tpShown()){
      /* עמוד אחר: הרשימה מתחלפת */
      var sig=tpList().map(function(it){return it.n}).join(',');
      if(TP.sig.split('|')[0]!==sig)tpRender(true);else tpMarkCur()}},120)}
  function tpFocus(n,flash){
    TP.cur=n;TP.quiet=Date.now()+3000;
    var p=tpEl();tpFit();p.classList.add('open');
    var x=p.querySelector('#tpl .tsn[data-n="'+n+'"]');
    if(!x){TP.q='';var qi=p.querySelector('#tpq');if(qi)qi.value='';CFG.page=0;cfgSave();tpRender(true);x=p.querySelector('#tpl .tsn[data-n="'+n+'"]')}
    tpMarkCur();
    if(x){var b=p.querySelector('#tpl'),r=x.getBoundingClientRect(),br=b.getBoundingClientRect();
      b.scrollTop+=(r.top-br.top)-(br.height/2-r.height/2)}
    if(flash)hot(n)}
  function tpStep(d){
    var l=tpList(),i=-1;l.forEach(function(it,k){if(it.n===TP.cur)i=k});
    if(i<0){var v=tpVisible();if(v.length){l.forEach(function(it,k){if(it.n===v[0].n)i=k})}}
    var j=Math.max(0,Math.min(l.length-1,i+d));if(!l[j])return;
    TP.cur=l[j].n;TP.quiet=Date.now()+3000;tpMarkCur();scrollToAnchor(l[j].n)}

  /* ---- כפתור ותפריט ---- */
  /* לחיצה אחת מדליקה ומכבה (13.10.2026). הדלקה חוזרת לאופן האחרון שנבחר (ברירת מחדל: פאנל צד).
     בחירת אופן אחר: הכפתור הקטן שליד הכפתור הראשי ('אופן'), הנראה רק כשהתוספות דלוקות. */
  function lastOn(){var l=lsGet('lg-tos-last','panel');return /^(foot|panel|side|list)$/.test(l)?l:'panel'}
  function syncBtns(){
    var on=mode!=='off';
    var b=document.getElementById('tosbtn');
    if(b){b.classList.toggle('on',on);b.setAttribute('aria-pressed',on?'true':'false')}
    var mb=document.querySelector('#mbot [data-a="tos"]');
    if(mb){mb.classList.toggle('on',on);mb.setAttribute('aria-pressed',on?'true':'false')}}
  window.tosBtn=function(){tosSet(mode==='off'?lastOn():'off')};
  window.tosModes=function(){
    var m=document.getElementById('tosmenu');
    if(!m){m=document.createElement('div');m.id='tosmenu';document.body.appendChild(m)}
    m.innerHTML=MODES.filter(function(x){return x[0]!=='off'}).map(function(x){return '<button type="button" data-m="'+x[0]+'" class="'+(x[0]===mode?'on':'')+'" onclick="tosSet(this.dataset.m)">'+ge(x[1])+'<small>'+ge(x[2])+'</small></button>'}).join('')+
      '<button type="button" data-m="off" onclick="tosSet(this.dataset.m)">כבוי<small>בלי סימנים כלל</small></button>'+
      ((typeof isAdmin==='function'&&isAdmin())?'<button type="button" onclick="tosTriOpen()">בדיקת תוספות<small>למנהל בלבד · הכרעה על מה שנפסל</small></button>':'')+
      ((window.tosTestOpen&&typeof isAdmin==='function'&&isAdmin())?((window.__TOSTEST&&window.__TOSTEST.rounds)||[{label:'מבחן מנועים'}]).map(function(rd,i){return '<button type="button" onclick="tosTestOpen('+i+')">'+ge(rd.label||'מבחן מנועים')+'<small>למנהל בלבד</small></button>'}).join(''):'');
    var b=document.getElementById('tosmb')||document.getElementById('tosbtn'),r=b.getBoundingClientRect();
    m.classList.toggle('open');
    if(!r.width){m.style.top='22vh';m.style.left=Math.max(8,(innerWidth-m.offsetWidth)/2)+'px';return}
    m.style.top=(r.bottom+6)+'px';
    m.style.left=Math.max(8,Math.min(r.left,innerWidth-m.offsetWidth-8))+'px'};
  window.tosSet=function(v){
    mode=v;lsSet(TS_KEY,v);if(v!=='off')lsSet('lg-tos-last',v);
    var m=document.getElementById('tosmenu');if(m)m.classList.remove('open');
    syncBtns();
    hovClose();
    var p=document.getElementById('tosp');if(p&&v!=='list')p.classList.remove('open');
    if(v!=='panel')tpClose();
    TP.sig='';
    tsMark();
    if(v==='list')panelOpen();
    if(v==='panel'){tpOpen();tpRender(true)}
    if(v==='foot'||v==='side'||v==='list'||v==='panel'){if(typeof isAdmin==='function'&&isAdmin())admLoad()}};
  syncBtns();
  /* חזרה מן ההערה אל הסימן שבטקסט: לחיצה על מספר ההערה */
  function tsBack(nm){
    var n=nm.closest('.tsn').getAttribute('data-n');
    scrollToAnchor(+n)}
  document.addEventListener('click',function(ev){
    var nm=ev.target.closest&&ev.target.closest('.tsn .tsnum');
    if(!nm)return;
    ev.preventDefault();ev.stopPropagation();tsBack(nm)},false);

  /* ---- חיפוש: "תוס' קל"ד" או מילים מן ההערה ---- */
  window.tsSearchHtml=function(q){
    var nq=normCtx(q||''),out=[];if(nq.length<2)return '';
    var num=/^תוס[׳']?\s*([א-ת0-9\s"'׳״]+)$/.exec((q||'').trim());
    var want=num?num[1].replace(/[\s"'׳״]/g,''):'';
    TS.items.forEach(function(it){
      var hn=(it.hnHeb||'').replace(/["']/g,'');
      var hit=(want&&(hn===want||String(it.n)===want))||normCtx(it.dh+' '+txt(it)).indexOf(nq)>=0;
      if(hit)out.push(it)});
    if(!out.length)return '';
    return '<div class="n">בתוספות: '+out.length+' תוצאות</div>'+out.slice(0,20).map(function(it){
      return '<div class="res"><a onclick="tosGo('+it.n+')"><small>תוס\' '+ge(it.hn)+'</small> '+ge(dispDh(it))+'</a></div>'}).join('')};
  window.tosGo=function(n){var it=byN[n];if(!it)return;
    if(mode==='off')tosSet(lastOn());
    var pi=pageIdx(it.daf);if(pi<0)return;
    var rows=pageRows(pi);
    if(!rows.length){toDaf(pi);setTimeout(function(){tosGo(n)},120);return}
    var s=document.getElementById('search');if(s)s.classList.remove('open');
    setTimeout(function(){
      if(mode==='panel'){tpFocus(n,true);scrollToAnchor(n)}
      else openNote(n,document.querySelector('.tsm[data-n="'+n+'"]')||document.body,'click')},60)};

  /* ---- מנהל: נוסחאות, בחירה, עריכה והערה, והצעות הלומדים ---- */
  function sugLoad(){
    if(typeof api!=='function')return;
    api('/queue?slug='+encodeURIComponent(SLUG)+'&ty=note&size=40').then(function(j){
      var m={};(j&&j.items||[]).forEach(function(g){
        var mm=/^tos:(\d+)$/.exec(g.k||'');if(mm&&g.st==='pending')(m[mm[1]]=m[mm[1]]||[]).push(g)});
      SUGS=m;tsMark()}).catch(function(){})}
  function admLoad(){
    if(ADM||typeof api!=='function')return;
    api('/tos?slug='+encodeURIComponent(SLUG)+'&adm=1').then(function(j){
      ADM=j.doc||{styles:{},picks:{},notes:{}};
      if(ADM.picks)Object.keys(ADM.picks).forEach(function(n){PUB[n]={p:ADM.picks[n].p,t:ADM.picks[n].t}});
      tsMark();sugLoad()}).catch(function(){})}
  function post(body){return api('/tos',{method:'POST',body:JSON.stringify(Object.assign({slug:SLUG},body))})}
  /* מסך מבחן המנועים מעדכן את הנוסחים הנבחרים בלי לטעון מחדש */
  window.tosPubSet=function(m){PUB=m||{};tsMark()};
  function applyDoc(j){if(j&&j.doc){ADM=ADM||{styles:{},picks:{},notes:{}};ADM.picks=j.doc.picks||{};ADM.notes=j.doc.notes||{};
      PUB={};Object.keys(ADM.picks).forEach(function(n){PUB[n]={p:ADM.picks[n].p,t:ADM.picks[n].t}})}
    reopenKeep()}
  function reopenKeep(){tsMark()}
  window.tosPick=function(b){
    var n=+b.getAttribute('data-n'),k=b.getAttribute('data-k');
    var t=ADM&&ADM.styles&&ADM.styles[n]&&ADM.styles[n][k];if(!t)return;
    b.disabled=true;
    post({n:n,pick:k,txt:t,from:k}).then(function(j){applyDoc(j);if(typeof toast==='function')toast('הנוסח נבחר ויוצג לכל הלומדים מיד')})
      .catch(function(e){b.disabled=false;if(typeof toast==='function')toast('לא נשמר: '+(e&&e.message||''),5000)})};
  window.tosApprove=function(b){
    var n=+b.getAttribute('data-n'),it=byN[n];if(!it)return;
    b.disabled=true;
    post({n:n,pick:'a',txt:(PUB[n]&&PUB[n].t)||it.sum,from:'a'}).then(function(j){applyDoc(j);if(typeof toast==='function')toast('השורה הוגתה ללא שינוי')})
      .catch(function(e){b.disabled=false;if(typeof toast==='function')toast('לא נשמר: '+(e&&e.message||''),5000)})};
  window.tosSaveText=function(b){
    var n=+b.getAttribute('data-n'),ta=b.parentElement.querySelector('textarea.tsedit');if(!ta)return;
    var v=ta.value.trim();if(!v)return;
    var from=(ADM&&ADM.picks&&ADM.picks[n]&&ADM.picks[n].p)||'b';
    b.disabled=true;
    post({n:n,pick:'custom',txt:v,from:from}).then(function(j){applyDoc(j);if(typeof toast==='function')toast('הנוסח שערכת נשמר ויוצג לכל הלומדים מיד')})
      .catch(function(e){b.disabled=false;if(typeof toast==='function')toast('לא נשמר: '+(e&&e.message||''),5000)})};
  window.tosSaveNote=function(b){
    var n=+b.getAttribute('data-n'),i=b.parentElement.querySelector('input.tsnote');if(!i)return;
    b.disabled=true;
    post({n:n,note:i.value}).then(function(j){b.disabled=false;applyDoc(j);if(typeof toast==='function')toast('ההערה נשמרה')})
      .catch(function(e){b.disabled=false;if(typeof toast==='function')toast('לא נשמר: '+(e&&e.message||''),5000)})};


  /* ================= מסך בדיקת תוספות שנפסלו (14.10.2026, מנהל בלבד) =================
     מציג תוספות אחת אחת: לשון התוספות, השורה, נימוק המבקר. נכון: מסיר "טרם נבדק" (ומציג תוספות שהוסתרה).
     לא נכון: מוריד מהאתר. דלג: עובר לסוף. ההכרעות נשמרות בשרת (/tri) ושם הן מאגר הדוגמאות של המבקר. */
  var TRI={items:null,order:[],i:0,open:false};
  var TRI_CLS={F:'טעות עניינית',D:'ייחוס שגוי',E:'תוספת דין או מסקנה',C:'השמטת נימוק',A:'מסגור או תמצות',B:'הפניה שאינה בתוספות',G:'בהירות או סגנון',H:'לא ברור',X:'כשל טכני בביקורת',Y:'שער אוטומטי'};
  var TRI_PRI={F:0,D:1,E:2,C:3,B:4,A:5,G:6,H:7,Y:8,X:9};
  function triEl(){var e=document.getElementById('tostri');if(!e){e=document.createElement('div');e.id='tostri';
      e.style.cssText='position:fixed;inset:0;z-index:60;background:rgba(20,16,10,.55);display:none;direction:rtl;overflow:auto;padding:14px';
      e.addEventListener('click',function(ev){if(ev.target===e)triClose()});document.body.appendChild(e)}return e}
  function triClose(){TRI.open=false;triEl().style.display='none'}
  function triSay(t){if(typeof toast==='function')toast(t,3000)}
  function triIsDone(it){return it.dec&&(it.dec.ans==='yes'||it.dec.ans==='no')}
  function triPri(it){return TRI_PRI[it.cls]===undefined?9:TRI_PRI[it.cls]}
  function triBuild(){
    var o=[];Object.keys(TRI.items).forEach(function(k){var it=TRI.items[k];if(!triIsDone(it)&&!it.skipped)o.push(k)});
    o.sort(function(a,b){var x=TRI.items[a],y=TRI.items[b];return triPri(x)-triPri(y)||x.slug.localeCompare(y.slug)||(x.perek-y.perek)||(x.n-y.n)});
    var sk=[];Object.keys(TRI.items).forEach(function(k){var it=TRI.items[k];if(!triIsDone(it)&&it.skipped)sk.push(k)});
    TRI.order=o.concat(sk)}
  function triRender(){
    var e=triEl(),tot=Object.keys(TRI.items).length,done=Object.keys(TRI.items).filter(function(k){return triIsDone(TRI.items[k])}).length;
    var k=TRI.order[0],h='<div style="max-width:880px;margin:0 auto;background:#fbf8f1;border-radius:12px;padding:16px 18px;color:#2b2620;font-size:17px;line-height:1.7">'+
      '<div style="display:flex;gap:10px;align-items:center"><b style="font-size:1.15em;color:#7a5a14">בדיקת תוספות שנפסלו</b><span style="flex:1"></span><span>הוכרעו '+done+' מתוך '+tot+'</span>'+
      '<button type="button" onclick="tosTriClose()" style="font:inherit;padding:2px 12px">סגור</button></div>';
    if(!k){h+='<p>אין תוספות ממתינות להכרעה.</p></div>';e.innerHTML=h;return}
    var it=TRI.items[k];
    h+='<div style="color:#777;font-size:.9em;margin-top:6px">'+ge((it.slug==='sukkah'?'סוכה':'ברכות')+', פרק '+it.perek+', דף '+it.daf+', תוספות מספר '+it.n)+' · סוג: <b>'+ge(TRI_CLS[it.cls]||it.cls)+'</b>'+
      (it.held?' · <span style="color:#a83c2f">מוסתרת מהלומדים עד הכרעתך</span>':' · מופיעה באתר בסימון כוכבית')+'</div>'+
      '<div style="font-weight:700;margin-top:8px">ד"ה: '+ge(it.dh)+'</div>'+
      '<div style="font-weight:700;color:#5b4a1e;margin-top:6px">לשון התוספות</div><div style="background:#fbf9f2;border-right:4px solid #cdbf93;padding:8px 12px;white-space:pre-wrap;max-height:34vh;overflow:auto">'+ge(it.text)+'</div>'+
      '<div style="font-weight:700;color:#5b4a1e;margin-top:6px">השורה שפורסמה</div><div style="background:#eef4fb;border-right:4px solid #6a9bd1;padding:8px 12px">'+ge(it.line)+'</div>'+
      (it.removed&&it.removed.length?'<div style="color:#8a4b00;margin-top:4px">הקוד מחק מהשורה את ההפניות: '+ge(it.removed.join(' · '))+'</div>':'')+
      '<div style="font-weight:700;color:#5b4a1e;margin-top:6px">נימוק המבקר</div><div style="background:#fdf0ee;border-right:4px solid #d9776b;padding:8px 12px">'+(it.why&&it.why.length?it.why.map(ge).join('<br>'):'(אין)')+'</div>'+
      '<div style="display:flex;gap:10px;margin-top:12px;flex-wrap:wrap;align-items:center">'+
      '<button type="button" onclick="tosTriDec(\'yes\')" style="font:inherit;font-size:1.05em;padding:6px 22px;border:2px solid #2e7d32;border-radius:8px;background:#e8f5e9;cursor:pointer">נכון</button>'+
      '<button type="button" onclick="tosTriDec(\'no\')" style="font:inherit;font-size:1.05em;padding:6px 22px;border:2px solid #b3261e;border-radius:8px;background:#fdecea;cursor:pointer">לא נכון</button>'+
      '<button type="button" onclick="tosTriSkip()" style="font:inherit;font-size:1.05em;padding:6px 22px;border:2px solid #999;border-radius:8px;background:#fff;cursor:pointer">דלג</button>'+
      '<input id="tritnote" placeholder="הערה לתיקון (לא חובה)" style="flex:1;min-width:220px;font:inherit;font-size:.95em;padding:6px 10px;border:1px solid #bbb;border-radius:8px;direction:rtl"></div>'+
      '<div style="color:#777;font-size:.85em;margin-top:6px">נכון = השורה נאמנה ואפשר להשאיר באתר (הסימון יוסר). לא נכון = תרד מהאתר מיד. ההכרעה והערתך משמשות כדוגמה למבקר.</div></div>';
    e.innerHTML=h}
  /* כפתור צף למנהל: כמה תוספות ממתינות להכרעה במסכת הזאת, ופתיחת מסך הבדיקה (14.10.2026) */
  function triFab(){
    if(!(typeof isAdmin==='function'&&isAdmin()))return;
    var n=ALLITEMS.filter(function(it){return it.u&&!TOK[it.n]&&!TNO[it.n]}).length;
    var b=document.getElementById('tostrifab');
    if(!n){if(b)b.remove();return}
    if(!b){b=document.createElement('button');b.id='tostrifab';b.type='button';
      b.style.cssText='position:fixed;z-index:29;left:12px;bottom:14px;font:inherit;font-size:15px;padding:8px 14px;border:2px solid #c9a24a;border-radius:20px;background:#fff6dc;color:#5a4a1e;cursor:pointer;box-shadow:0 3px 12px rgba(0,0,0,.25)';
      b.onclick=function(){tosTriOpen()};document.body.appendChild(b)}
    b.textContent='בדיקת תוספות ('+n+' ממתינות)'}
  setTimeout(triFab,900);setTimeout(triFab,3500);
  window.tosTriClose=triClose;
  window.tosTriOpen=function(){
    if(!(typeof isAdmin==='function'&&isAdmin())||typeof api!=='function'){triSay('המסך זמין לכניסת מנהל בלבד');return}
    var m=document.getElementById('tosmenu');if(m)m.classList.remove('open');
    var e=triEl();e.style.display='block';TRI.open=true;e.innerHTML='<div style="max-width:880px;margin:0 auto;background:#fbf8f1;border-radius:12px;padding:16px">טוען...</div>';
    Promise.all(['sukkah','berakhot'].map(function(sl){return api('/tri?slug='+sl).then(function(j){return {sl:sl,doc:(j&&j.doc)||{items:{},dec:{}}}})})).then(function(rs){
      TRI.items={};rs.forEach(function(r){Object.keys(r.doc.items||{}).forEach(function(n){
        var it=r.doc.items[n];it.slug=r.sl;it.num=+n;it.dec=(r.doc.dec||{})[n]||null;TRI.items[r.sl+':'+n]=it})});
      triBuild();triRender()}).catch(function(err){e.innerHTML='<div style="max-width:880px;margin:0 auto;background:#fbf8f1;border-radius:12px;padding:16px">לא נטען: '+ge(err&&err.message||'')+'</div>'})};
  window.tosTriSkip=function(){var k=TRI.order[0];if(!k)return;TRI.items[k].skipped=true;triBuild();triRender()};
  window.tosTriDec=function(ans){
    var k=TRI.order[0];if(!k)return;var it=TRI.items[k],ni=document.getElementById('tritnote');
    var note=ni?ni.value:'';
    api('/tri',{method:'POST',body:JSON.stringify({op:'dec',slug:it.slug,n:it.num,ans:ans,note:note})}).then(function(j){
      if(!j||!j.ok)throw new Error((j&&j.error)||'לא נשמר');
      it.dec={ans:ans,note:note};
      if(it.slug===SLUG){if(ans==='yes')TOK[it.num]=true;else TNO[it.num]=true;triApply();tsMark()}
      triFab();triBuild();triRender()}).catch(function(err){triSay('לא נשמר: '+(err&&err.message||''))})};

  /* ---- טעינה: הנוסחים שנבחרו (ציבורי) ---- */
  if(location.protocol==='http:'||location.protocol==='https:'){
    fetch(SUGGEST_API+'/tos?slug='+encodeURIComponent(SLUG),{cache:'no-store'}).then(function(r){return r.json()}).then(function(j){
      if(j&&j.ok){TOK={};TNO={};(j.tok||[]).forEach(function(n){TOK[n]=true});(j.tno||[]).forEach(function(n){TNO[n]=true});
        triApply();if(!off())tsMark()}
      if(j&&j.ok&&j.pub){var any=false;Object.keys(j.pub).forEach(function(n){if(byN[n]&&j.pub[n].t){PUB[n]=j.pub[n];any=true}});
        if(any&&!off())tsMark()}}).catch(function(){})}
  if(typeof isAdmin==='function'&&isAdmin()&&mode!=='off')setTimeout(admLoad,50);
  /* קישור מכרטיס שאלה: slug.html#daf=...&tos=<מפתח> פותח את התוספות (13.10.2026) */
  try{var hp=new URLSearchParams(location.hash.slice(1)),tn=hp.get('tos');
    if(tn&&byN[tn])setTimeout(function(){tosGo(+tn)},1200)}catch(e){}
  })();
