  /* =================== מצב דפוס (פרומפט 49, 16.11.2026, מנהל בלבד) ===================
     לראות ולערוך כל פרק בדיוק כפי שיודפס. אמת אחת: מה שמוצג כאן הוא תוצר מנוע ההדפסה עצמו (print_engine.js),
     באותו פרופיל, אותה מדידה, אותה הצרה, אותו איזון ופיצול הערות. הוא רץ במסגרת פנימית של אותו דף (?print=1&pm=1),
     על הנתונים של דף המנהל כפי שהם עכשיו (__pmSnapshot), כולל עריכה שטרם פורסמה. "הדפס מה שאני רואה" מדפיס את
     המסגרת עצמה, ולכן ה-PDF הוא אותו עימוד בדיוק. אחרי עריכה המסגרת מעמדת מחדש (__prnRerun) בלי טעינה מחדש.
     העיצוב של המצב (רקע, גבול דף, הגדלה, סימני בדיקה) כולו תחת @media screen ואינו נכנס להדפסה.
     הגדלה תמיד ב-transform של הגוש כולו, לעולם לא שינוי גופן, כדי שהשבירות לא יזוזו.
     תיעוד: docs/מצב-דפוס.md */
  (function(){
  var PQ=new URLSearchParams(location.search);
  if(PQ.get('print')==='1')return;            /* בתוך המסגרת: רק המנוע רץ */
  function pmAdm(){try{return typeof isAdmin==='function'&&!!isAdmin()}catch(e){return false}}
  function pmGe(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
  function pmLs(k,d){try{var v=localStorage.getItem(k);return v===null?d:JSON.parse(v)}catch(e){return d}}
  function pmLsSet(k,v){try{localStorage.setItem(k,JSON.stringify(v))}catch(e){}}
  function pmMsg(m){try{if(typeof flash==='function')flash(m);else if(typeof toast==='function')toast(m,3000)}catch(e){}}
  var CARD_MM=85.6;                             /* רוחב כרטיס אשראי (ISO 7810) לכיול "גודל טבעי" */
  var S={open:false,fr:null,busy:false,dirty:false,report:null,pk:null,view:'page',spread:false,zoom:'fit',z:1,
         pages:[],issues:[],ii:-1,pend:0,bal:0,staleFrom:0,cross:0,badges:{},mv:{},cmdMs:[],kbuf:'',later:pmLs('lg-pm-later-'+(typeof SLUG!=='undefined'?SLUG:''),[]),t0:0,lastMs:0,anchor:null};
  var P=pmLs('lg-pm-prefs',{paper:'b5',big:1,tos:1,view:'page',spread:0,zoom:'fit',z:1,auto:0});
  var PXMM=pmLs('lg-pm-pxmm',0);              /* פיקסלים למילימטר במסך הזה (אחרי כיול). 0 = לא כויל: 96/25.4 */
  S.view=P.view||'page';S.spread=!!P.spread;S.zoom=P.zoom||'fit';S.z=+P.z||1;

  /* ---------- הנתונים שהמסגרת מעמדת: עותק של הדף כפי שהוא עכשיו ---------- */
  window.__pmSnapshot=function(){try{return D.pages.map(function(p){return JSON.parse(JSON.stringify(p.units||[]))})}catch(e){return null}};

  /* ---------- הפרקים ---------- */
  function pmPerakim(){
    var out=[],seen={};
    try{var M=window.lkTos.perekMap();
      M.lab.forEach(function(l,i){var k=(l.perek||'')+'|'+(l.perekName||'');if(!l.perek||seen[k])return;seen[k]=1;out.push({key:k,n:i+1,label:(l.perek||'')+(l.perekName?' - '+l.perekName:'')})})}catch(e){}
    if(!out.length)D.pages.forEach(function(p){var k=(p.perek||'')+'|'+(p.perekName||'');if(!p.perek||seen[k])return;seen[k]=1;out.push({key:k,n:out.length+1,label:(p.perek||'')+(p.perekName?' - '+p.perekName:'')})});
    return out}
  /* הפרק שבו הלומד עומד: היחידה הראשונה שנראית בדף, ולפיה הפרק במפת הפרקים */
  function pmTopUnit(){
    var f=document.getElementById('flow');if(!f)return null;
    var rows=f.querySelectorAll('.row[id^="u"]'),y=Math.max(60,innerHeight*0.18);
    for(var i=0;i<rows.length;i++){var r=rows[i].getBoundingClientRect();if(r.bottom>y&&r.height>0)return +rows[i].id.slice(1)}
    return rows.length?+rows[0].id.slice(1):null}
  function pmCurPerek(uid){
    var L=pmPerakim();if(!L.length)return null;
    try{var M=window.lkTos.perekMap();if(uid&&M.upk[uid]){var n=M.upk[uid];var l=M.lab[n-1];if(l)return (l.perek||'')+'|'+(l.perekName||'')}}catch(e){}
    try{if(typeof SEC!=='undefined'&&typeof cur!=='undefined'&&SEC[cur]){var p=D.pages[SEC[cur].to];return (p.perek||'')+'|'+(p.perekName||'')}}catch(e){}
    return L[0].key}
  /* הדף הרגיל עובר לפרק הזה, כדי שהעריכה תיכתב בעורך הקיים על השורה הנכונה */
  function pmShowPerek(pk,force){
    try{if(typeof SEC==='undefined'||typeof render!=='function')return;
      for(var i=0;i<SEC.length;i++){var p=D.pages[SEC[i].to];if(p&&((p.perek||'')+'|'+(p.perekName||''))===pk){if(i!==cur||force)render(i);return}}}catch(e){}}

  /* ---------- העיצוב של המצב (בדף המנהל) ---------- */
  function pmCss(){
    if(document.getElementById('pmcss'))return;
    var c=document.createElement('style');c.id='pmcss';
    c.textContent=
      '#pm{position:fixed;inset:0;z-index:55;display:none;flex-direction:column;background:#d9d5cc;direction:rtl;font:14px/1.4 Frank,serif;color:#2b2620}'+
      '#pm.open{display:flex}body.pmopen{overflow:hidden}'+
      '#pmbar{display:flex;flex-wrap:wrap;align-items:center;gap:4px 8px;padding:5px 10px;background:#f7f4ee;border-bottom:1px solid #c9bfa8;box-shadow:0 1px 4px rgba(0,0,0,.08)}'+
      '#pmbar .pmt{font-weight:700;color:#1d3557;margin-left:6px}'+
      '#pmbar select,#pmbar input,#pmbar button{font:inherit;font-size:13px;border:1px solid #c9bfa8;background:#fff;border-radius:5px;padding:2px 7px;cursor:pointer;color:inherit}'+
      '#pmbar input[type=number]{width:3.6em;cursor:text}#pmbar input[type=checkbox]{padding:0}'+
      '#pmbar .pmg{display:inline-flex;gap:2px;align-items:center}#pmbar button.on{background:#1d3557;border-color:#1d3557;color:#fff}'+
      '#pmbar .pmsep{width:1px;height:18px;background:#c9bfa8}'+
      '#pm-next{color:#a3361f;font-weight:700}#pm-next.ok{color:#2e7d3c}'+
      '#pm-stat{color:#8a7d66;font-size:12px;min-width:7em;max-width:34em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}#pm-stat.busy{color:#a3361f}'+
      '#pm-x{margin-right:auto;font-weight:700}'+
      '#pmmain{position:relative;flex:1;display:flex;min-height:0}'+
      '#pmf{flex:1;border:0;background:#d9d5cc;min-width:0}'+
      '#pmside{width:230px;overflow:auto;background:#f7f4ee;border-right:1px solid #c9bfa8;padding:6px 8px;font-size:13px;display:none}'+
      '#pmside.on{display:block}#pmside h4{margin:2px 0 6px;font-size:14px}#pmside .pml{padding:3px 0;border-bottom:1px dotted #c9bfa8;cursor:pointer}'+
      '#pmside .pml b{color:#8a7d66;font-weight:400;font-size:12px}#pmside .pml .x{float:left;color:#a3361f;cursor:pointer}'+
      '#pmcal{position:fixed;inset:0;z-index:70;background:rgba(0,0,0,.35);display:none;align-items:center;justify-content:center}#pmcal.on{display:flex}'+
      '#pmcal .bx{background:#fff;border-radius:8px;padding:14px 18px;max-width:94vw;direction:rtl}'+
      '#pmcal .card{height:54mm;background:#e8eef6;border:1px solid #1d3557;border-radius:3mm;margin:10px 0}'+
      '#pmcal input[type=range]{width:min(560px,80vw)}'+
      '#pmmenu{position:fixed;z-index:72;background:#fff;border:1px solid #c9bfa8;border-radius:6px;box-shadow:0 4px 16px rgba(0,0,0,.2);padding:3px 0;display:none;direction:rtl}'+
      '#pmmenu div{padding:4px 14px;cursor:pointer}#pmmenu div:hover{background:#f1ece2}'+
      '#pm-done.hot{border-color:#a3361f;color:#a3361f;font-weight:700}#pm-pend{color:#a3361f;font-size:12px;max-width:40em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}'+
      'body.pmopen #keyscard,body.pmopen .modal{z-index:80!important}'+
      /* הדף הרגיל שמתחת למצב אינו נפרס על המסך: העורך עובד עליו, אבל הדפדפן אינו מחשב את הפריסה שלו בכל פקודה */
      'body.pmopen #flow{content-visibility:hidden}'+
      '@media (max-width:700px){#pmbar{font-size:12px}#pmbar .pmwide{display:none}#pmside{display:none!important}}'+
      '@media print{#pm,#pmbtn{display:none!important}}';
    document.head.appendChild(c)}

  /* ---------- העיצוב בתוך המסגרת (רק במסך; ההדפסה אינה משתנה) ---------- */
  var FRAME_CSS=
    '@media screen{'+
      'html.prn,html.prn body,body.prn{background:#d9d5cc!important}'+
      'body.prn{padding:14px 0 40vh!important}'+
      '#prnout{position:relative!important;transform-origin:top right;transform:scale(var(--pmz,1));width:var(--pmw,auto);'+
        'margin-right:var(--pmr,0px);margin-bottom:var(--pmb,0px)}'+
      '#prnout > .pg,#prnout > .shp{margin:0 0 10mm 0;box-shadow:0 0 0 .35px #555,0 2px 10px rgba(0,0,0,.12)}'+
      'html.pmspread #prnout{display:flex;flex-wrap:wrap;align-content:flex-start;column-gap:6mm}'+
      'html.pmspread #prnout > .pmsp{visibility:hidden;box-shadow:none!important}'+
      'html.pmcol #prnout > .pg,html.pmcol #prnout > .shp,html.pmcol #prnout > .pmsp{display:none!important}'+
      '#pmcols{display:none}html.pmcol #pmcols{display:block}'+
      '#pmcols .pmc{position:relative;margin:0 0 4mm 0;background:#fff;box-shadow:0 0 0 .35px #555}'+
      '#pmcols .pmc > .pg{margin:0!important;box-shadow:none!important;overflow:hidden}'+
      '#pmcols .pmcn{position:absolute;right:-9mm;top:0;font:10px Frank,serif;color:#6b6b6b}'+
      '.pmmk{position:absolute;width:12px;height:12px;margin-top:-1px;border-radius:50%;cursor:pointer;z-index:5;'+
        'font:bold 9px/12px sans-serif;text-align:center;color:#fff;background:#c0392b;box-shadow:0 0 0 1.5px #fff}'+
      '.pmmk.k-hole,.pmmk.k-bal{background:#b9770e}.pmmk.k-ov{background:#7d3c98}.pmmk.k-later{background:#1d6fa5}.pmmk.cur{outline:2px solid #1d3557;outline-offset:2px}'+
      '.pmready{position:absolute;z-index:5;font:bold 12px Frank,serif;color:#2e7d3c;border:1px solid #2e7d3c;border-radius:4px;padding:1px 6px;background:#fff}'+
      '.pmdelta{position:absolute;z-index:6;font:bold 11px sans-serif;color:#1d3557;border:1px solid #1d3557;border-radius:4px;padding:0 4px;white-space:nowrap}'+
      '.pmdelta.up{color:#a3361f;border-color:#a3361f}.pmdelta.dn{color:#2e7d3c;border-color:#2e7d3c}.pmdelta.eq{color:#6b6b6b;border-color:#b8b0a0}'+
      '#prnout > .pmstale{box-shadow:0 0 0 .35px #555,inset -3px 0 0 #d68910!important}'+
      '.pmovl{position:absolute;right:0;z-index:6;font:bold 10px sans-serif;color:#a3361f;white-space:nowrap}'+
      '.ptx .main p,.ptx .main.dh,.ptx .main.nose{cursor:text}'+
      '[contenteditable].pmed{outline:1px solid #1d6fa5;outline-offset:1px;position:relative;z-index:4;caret-color:#1d6fa5}'+
      '.pmflash{outline:2px solid #1d6fa5;outline-offset:2px;transition:outline-color 1.2s}'+
    '}'+
    '@media print{.pmmk,.pmready,.pmdelta,.pmovl,#pmcols{display:none!important}}';

  /* ---------- סרגל המצב ---------- */
  function pmBuild(){
    if(document.getElementById('pm'))return;
    pmCss();
    var d=document.createElement('div');d.id='pm';d.setAttribute('dir','rtl');
    var pks=pmPerakim().map(function(p){return '<option value="'+pmGe(p.key)+'">'+pmGe(p.label)+'</option>'}).join('');
    d.innerHTML=
      '<div id="pmbar">'+
        '<span class="pmt">מצב דפוס</span>'+
        '<select id="pm-pk" title="פרק">'+pks+'</select>'+
        '<span class="pmg"><select id="pm-paper" title="גודל הדף"><option value="b5">B5</option><option value="a4">A4</option></select>'+
        '<select id="pm-big" title="גודל הגוף"><option value="1">מוגדל</option><option value="0">רגיל</option></select>'+
        '<label title="עם הערות התוס\'"><input type="checkbox" id="pm-tos"> תוס\'</label></span>'+
        '<span class="pmsep"></span>'+
        '<span class="pmg"><button data-v="page" title="עמודים כפי שיודפסו">עמוד</button><button data-v="spread" class="pmwide" title="עמוד מול עמוד">כפולה</button><button data-v="col" title="הטורים בלבד, זה מתחת לזה">טור</button></span>'+
        '<span class="pmg"><button data-z="nat" title="מילימטרים אמיתיים על המסך">גודל טבעי</button><button data-z="fit" title="לרוחב המסך">רוחב מסך</button>'+
        '<button data-z="-" title="הקטן">−</button><button data-z="+" title="הגדל">+</button><button data-z="cal" class="pmwide" title="כיול הגודל הטבעי בכרטיס אשראי">כיול</button></span>'+
        '<span class="pmsep"></span>'+
        '<span class="pmg">עמוד <input type="number" id="pm-pg" min="1" value="1" title="עמוד בקובץ"> <span id="pm-pgn">/ -</span></span>'+
        '<span class="pmg pmwide">דף <select id="pm-daf" title="קפיצה לדף"></select></span>'+
        '<span class="pmsep"></span>'+
        '<button id="pm-next" title="הממצא הבא (N)">-</button>'+
        '<button id="pm-later" class="pmwide" title="רשימת \'לבדוק אחר כך\'">לבדוק אחר כך <span id="pm-ln">0</span></button>'+
        '<button id="pm-done" title="עימוד מלא של הפרק אחרי התיקונים (F9)">השלם עימוד</button>'+
        '<select id="pm-auto" class="pmwide" title="השלמת עימוד לבד אחרי שקט"><option value="0">השלמה ידנית</option><option value="5">לבד אחרי 5 שנ\'</option><option value="15">לבד אחרי 15 שנ\'</option><option value="30">לבד אחרי 30 שנ\'</option></select>'+
        '<span id="pm-pend"></span>'+
        '<button id="pm-print" title="הדפסה של העימוד הזה בדיוק">הדפס מה שאני רואה</button>'+
        '<span id="pm-stat"></span>'+
        '<button id="pm-x" title="יציאה (Esc או F8)">✕ יציאה</button>'+
      '</div>'+
      '<div id="pmmain"><iframe id="pmf" title="מצב דפוס"></iframe><div id="pmside"></div></div>';
    document.body.appendChild(d);
    var cal=document.createElement('div');cal.id='pmcal';
    cal.innerHTML='<div class="bx"><b>כיול גודל טבעי</b><div>הצמד כרטיס אשראי למסך, והזז את הסרגל עד שהמלבן הכחול ברוחב הכרטיס בדיוק.</div>'+
      '<div class="card" id="pmcard"></div><input type="range" id="pmcr" min="2" max="9" step="0.01"><div style="display:flex;gap:8px;margin-top:8px"><button id="pmcok">שמור</button><button id="pmcx">בטל</button><button id="pmcr0">ברירת מחדל</button></div></div>';
    document.body.appendChild(cal);
    var menu=document.createElement('div');menu.id='pmmenu';document.body.appendChild(menu);
    var $p=function(id){return document.getElementById(id)};
    $p('pm-paper').value=P.paper;$p('pm-big').value=String(P.big);$p('pm-tos').checked=!!P.tos;
    ['pm-paper','pm-big','pm-tos'].forEach(function(id){$p(id).addEventListener('change',function(){
      P.paper=$p('pm-paper').value;P.big=+$p('pm-big').value;P.tos=$p('pm-tos').checked?1:0;pmLsSet('lg-pm-prefs',P);pmLoad()})});
    $p('pm-pk').addEventListener('change',function(){S.pk=this.value;S.anchor=null;pmShowPerek(S.pk);pmLoad()});
    [].forEach.call(d.querySelectorAll('[data-v]'),function(b){b.addEventListener('click',function(){
      var n=+document.getElementById('pm-pg').value||1;
      var v=b.getAttribute('data-v');S.view=v==='spread'?'page':v;S.spread=v==='spread';P.view=S.view;P.spread=S.spread?1:0;pmLsSet('lg-pm-prefs',P);pmApplyView();
      pmGoPage(n)})});
    [].forEach.call(d.querySelectorAll('[data-z]'),function(b){b.addEventListener('click',function(){pmZoom(b.getAttribute('data-z'))})});
    $p('pm-pg').addEventListener('change',function(){pmGoPage(+this.value)});
    $p('pm-daf').addEventListener('change',function(){pmGoDaf(this.value)});
    $p('pm-next').addEventListener('click',function(){pmNext()});
    $p('pm-later').addEventListener('click',function(){$p('pmside').classList.toggle('on');pmSide()});
    $p('pm-print').addEventListener('click',pmPrint);
    $p('pm-done').addEventListener('click',function(){pmComplete()});
    $p('pm-auto').value=String(+P.auto||0);$p('pm-auto').addEventListener('change',function(){P.auto=+this.value;pmLsSet('lg-pm-prefs',P);pmAutoArm()});
    $p('pm-x').addEventListener('click',pmClose);
    $p('pmcr').addEventListener('input',function(){$p('pmcard').style.width=(CARD_MM*this.value)+'px'});
    $p('pmcok').addEventListener('click',function(){PXMM=+$p('pmcr').value;pmLsSet('lg-pm-pxmm',PXMM);cal.classList.remove('on');pmZoom('nat')});
    $p('pmcx').addEventListener('click',function(){cal.classList.remove('on')});
    $p('pmcr0').addEventListener('click',function(){PXMM=0;pmLsSet('lg-pm-pxmm',0);cal.classList.remove('on');pmZoom('nat')});
    document.addEventListener('click',function(e){if(!menu.contains(e.target))menu.style.display='none'},true);
    /* פרומפט 52: שינוי בנתוני הדף שלא בא מן המצב (קבלת הצעה, סכם) - רק היחידות שהשתנו נבנות מחדש, בלי עימוד */
    document.addEventListener('lg-dv',function(){if(S.open)setTimeout(pmExternal,0)});
    window.addEventListener('resize',function(){if(!S.open)return;pmFrameSize(S.fr);if(S.zoom==='fit')pmZoom('fit')})}

  /* ---------- פתיחה, טעינה, עימוד ---------- */
  function pmProfile(){return (P.paper==='a4'?'a4':'b5')+(+P.big?'lg':'')}
  function pmOpen(){
    if(!pmAdm()){pmMsg('מצב דפוס - למנהל בלבד');return}
    if(S.open)return;
    pmBuild();
    /* העורך הקיים פעיל, כדי שעריכה מן המצב תיכתב באותן רשומות ובאותו פרסום */
    try{if(typeof EDIT!=='undefined'&&!EDIT&&typeof setEdit==='function')setEdit(true)}catch(e){}
    /* בטלפון: צפייה בלבד, תצוגת "טור" */
    S.phone=innerWidth<=700;if(S.phone){S.view='col';S.spread=false}
    var uid=pmTopUnit();S.anchor=uid;
    S.pk=pmCurPerek(uid);
    var PL=pmPerakim();if(!PL.some(function(x){return x.key===S.pk}))S.pk=PL.length?PL[0].key:S.pk;   /* תמיד פרק אחד, לעולם לא המסכת כולה */
    /* פרומפט 52: העורך שמתחת למצב מחזיק רק את הפרק, לא את המסכת כולה ("רצף"). כל פקודה של העורך מעבדת את הדף שלו,
       ובמסכת שלמה (כ-3000 שורות) פיצול אחד לקח כ-120 אלפיות; בפרק אחד כ-20. ביציאה התצוגה חוזרת למה שהיתה */
    try{if(typeof ALL!=='undefined'&&ALL){S.wasAll=true;ALL=false}}catch(e){}
    pmShowPerek(S.pk,S.wasAll);
    document.getElementById('pm-pk').value=S.pk||'';
    document.getElementById('pm').classList.add('open');document.body.classList.add('pmopen');
    S.open=true;pmLsSet('lg-pm-on',1);
    pmLoad()}
  function pmClose(){
    if(!S.open)return;
    pmCommit();
    var a=S.anchor;
    S.open=false;pmLsSet('lg-pm-on',0);
    document.getElementById('pm').classList.remove('open');document.body.classList.remove('pmopen');
    var fr=document.getElementById('pmf');if(fr)fr.src='about:blank';S.fr=null;
    /* הדף הרגיל נצבע מחדש: בזמן המצב הוא לא נפרס על המסך (content-visibility), והתצוגה ("רצף") חוזרת */
    try{if(S.wasAll){ALL=true;S.wasAll=false}if(typeof render==='function'&&typeof cur!=='undefined')render(cur)}catch(e){}
    /* חזרה לדף הרגיל - למקום שבו עמדת במצב הדפוס */
    if(a){var r=document.getElementById('u'+a);if(r)r.scrollIntoView({block:'center'})}}
  function pmUrl(){
    var q=new URLSearchParams();q.set('print','1');q.set('pm','1');
    var pk=S.pk,a=-1,b=-1;
    D.pages.forEach(function(p,i){if(p.units&&p.units.length&&((p.perek||'')+'|'+(p.perekName||''))===pk){if(a<0)a=i;b=i}});
    if(a<0){a=0;b=D.pages.length-1}
    S.pkPi=[Math.max(0,a-1),Math.min(D.pages.length-1,b+1)];
    q.set('from',D.pages[a].daf);q.set('to',D.pages[b].daf);q.set('pk',pk);
    q.set('tos',+P.tos?'1':'0');q.set('duplex','0');q.set('profile',pmProfile());
    return location.pathname.split('/').pop()+'?'+q.toString()}
  /* מסך צר (טלפון, חלון קטן): עיצוב האתר לטלפון משנה את הגופן והרוחב של הסרגל, והמנוע היה מודד עליו עימוד אחר.
     לכן המסגרת תמיד ברוחב של מחשב (FRW), ומוקטנת כגוש להתאים למסך. העימוד זהה להדפסה גם בטלפון */
  var FRW=1100;
  function pmFrameSize(fr){
    var box=document.getElementById('pmmain');if(!fr||!box)return;
    var w=box.clientWidth||innerWidth;
    if(w>=FRW){fr.style.cssText='';return}
    var k=w/FRW,h=(box.clientHeight||innerHeight)/k;
    fr.style.cssText='flex:none;width:'+FRW+'px;height:'+h+'px;transform:scale('+k+');transform-origin:top right;position:absolute;top:0;right:0'}
  function pmStat(t,busy){var e=document.getElementById('pm-stat');if(!e)return;e.textContent=t||'';e.classList.toggle('busy',!!busy)}
  function pmLoad(){
    /* מסגרת חדשה בכל טעינה: המסמך הקודם (פרק אחר, פרופיל אחר) נזרק מיד ואינו יכול "לסיים" במקום החדש */
    var old=document.getElementById('pmf'),fr=document.createElement('iframe');fr.id='pmf';fr.title='מצב דפוס';
    old.parentNode.replaceChild(fr,old);
    pmFrameSize(fr);
    S.fr=fr;S.busy=true;S.t0=performance.now();S.report=null;S.pages=[];S.issues=[];
    S.editing=null;S.pend=0;S.bal=0;S.staleFrom=0;S.cross=0;S.badges={};S.mv={};S.completing=null;S.resume=null;
    pmStat('מעמד...',1);
    fr.src=pmUrl();
    pmWait()}
  function pmWait(){
    var fr=S.fr,t0=S.t0;clearInterval(S.iv);
    S.iv=setInterval(function(){
      if(!S.open||fr!==S.fr){clearInterval(S.iv);return}
      var W=null;try{W=fr.contentWindow.__PRN}catch(e){}
      if(W&&W.state==='done'){clearInterval(S.iv);pmDone(W.report)}
      else if(W&&W.state==='error'){clearInterval(S.iv);S.busy=false;pmStat('שגיאה: '+W.error,1)}
      else if(performance.now()-t0>120000){clearInterval(S.iv);S.busy=false;pmStat('העימוד לא הסתיים',1)}},120)}
  /* עימוד חוזר אחרי עריכה: באותה מסגרת, בלי טעינה */
  var PMT=0;
  function pmSoon(){clearTimeout(PMT);PMT=setTimeout(pmRelayout,250)}
  function pmRelayout(){
    var fr=S.fr,w=null;try{w=fr&&fr.contentWindow}catch(e){}
    if(!w||!w.__prnRerun){pmLoad();return}
    if(S.busy){S.dirty=true;return}
    S.busy=true;S.dirty=false;S.t0=performance.now();
    var keep=pmKeep();
    pmStat('מעמד...',1);
    var oldPages=S.report?S.report.pages.length:0;
    w.__prnRerun().then(function(){
      var rep=w.__PRN&&w.__PRN.report;pmDone(rep,keep,oldPages)},
      function(e){S.busy=false;pmStat('שגיאה: '+(e&&e.message||e),1)})}
  /* מה שהמנהל רואה: הפסקה שנערכה (או השורה העליונה) ומקומה על המסך, כדי שהדף לא יקפוץ */
  function pmKeep(){
    var doc=pmDoc();if(!doc)return null;
    var k=S.focusKey,el=null;
    if(k)el=pmFindRow(doc,k.u,k.li);
    if(!el){var rows=doc.querySelectorAll('#prnout .pg .ptx .row[data-u]');for(var i=0;i<rows.length;i++){var r=rows[i].getBoundingClientRect();if(r.bottom>40){el=rows[i];k={u:+rows[i].getAttribute('data-u'),li:0};break}}}
    if(!el)return null;
    return {k:k,y:el.getBoundingClientRect().top}}
  /* גלילה בתוך המסגרת בלבד (scrollIntoView היה גולל גם את דף המנהל שמתחת) */
  function pmScrollTo(el,how){var doc=pmDoc();if(!doc||!el)return;var r=el.getBoundingClientRect(),h=S.fr.clientHeight||600;
    doc.scrollingElement.scrollTop+=how==='center'?(r.top+r.height/2-h/2):(r.top-30)}
  function pmDoc(){try{return S.fr&&S.fr.contentDocument}catch(e){return null}}
  function pmFindRow(doc,u,li){
    var rows=doc.querySelectorAll('#prnout .pg .ptx .row[data-u="'+u+'"]');if(!rows.length)return null;
    if(!li)return rows[0];
    /* שורה שעוברת טור נמצאת בשני הטורים: הפסקה שבחלון החיתוך הנראה */
    for(var i=0;i<rows.length;i++){var p=rows[i].querySelectorAll(':scope > .main > p')[li-1];if(!p)continue;
      var ptx=rows[i].closest('.ptx'),pr=p.getBoundingClientRect(),tr=ptx.getBoundingClientRect();
      if(pr.top>=tr.top-2&&pr.top<tr.bottom-2)return p}
    return rows[0].querySelectorAll(':scope > .main > p')[li-1]||rows[0]}

  function pmDone(rep,keep,oldPages){
    var doc=pmDoc();S.busy=false;if(!doc||!rep)return;
    S.report=rep;S.lastMs=Math.round(performance.now()-S.t0);
    try{S.lh=parseFloat(getComputedStyle(doc.querySelector('#prnout .ptx')).lineHeight)||S.lh}catch(e){}
    if(!doc.getElementById('pmfcss')){var st=doc.createElement('style');st.id='pmfcss';st.textContent=FRAME_CSS;doc.head.appendChild(st)}
    var out=doc.getElementById('prnout');if(!out)return;
    S.pages=[].slice.call(out.querySelectorAll(':scope > .shp, :scope > .pg'));
    pmCols(doc,out);
    pmApplyView(true);
    pmBind(doc);
    pmIssues(doc,out,rep);
    pmDafs(rep);
    var n=S.pages.length;
    document.getElementById('pm-pgn').textContent='/ '+n;document.getElementById('pm-pg').max=n;
    var dl='';if(oldPages&&oldPages!==n)dl=' · '+(n>oldPages?'+':'')+(n-oldPages)+' עמ\'';
    pmStat('פרק: '+n+' עמודים'+dl+' · '+(S.lastMs/1000).toFixed(1)+' שנ\'',0);
    /* מקום הקריאה: היחידה שבה עמדת, או הפסקה שנערכה - באותו גובה על המסך */
    if(keep){var el=pmFindRow(doc,keep.k.u,keep.k.li);if(el){var dy=el.getBoundingClientRect().top-keep.y;doc.scrollingElement.scrollTop+=dy}}
    else if(S.anchor){var r0=pmFindRow(doc,S.anchor,0);if(r0)pmScrollTo(r0,'start')}
    if(S.completing)pmAfterFull();else pmBar();
    if(S.dirty)pmSoon()}

  /* ---------- תצוגות: עמוד / כפולה / טור ---------- */
  function pmCols(doc,out){
    var old=doc.getElementById('pmcols');if(old)old.remove();
    var box=doc.createElement('div');box.id='pmcols';
    var sh=(S.report&&S.report.shrink&&S.report.shrink.scale)||1;
    S.pages.forEach(function(pe,pi){
      var pg=pe.classList.contains('pg')?pe:pe.querySelector('.pg');if(!pg)return;
      [].forEach.call(pg.querySelectorAll(':scope > .pcol'),function(c,ci){
        var tx=c.querySelector('.ptx'),fn=c.querySelector('.pfnw');
        var h=(tx?tx.offsetHeight:0)+(fn?fn.offsetHeight+8:0),w=c.offsetWidth;
        /* הטור עטוף בעמוד מדומה (.pg) כדי שכל עיצוב ההדפסה (שחור בלבד, ההפניות, ההערות) יחול עליו כמו בעמוד; ובדף B5 - אותה הקטנה */
        var wrap=doc.createElement('div');wrap.className='pmc';wrap.style.width=(w*sh)+'px';wrap.style.height=(h*sh)+'px';
        var fp=doc.createElement('section');fp.className='pg pmcpg';
        fp.style.setProperty('width',w+'px','important');fp.style.setProperty('height',h+'px','important');
        fp.style.position='absolute';fp.style.left='0';fp.style.top='0';fp.style.transformOrigin='0 0';fp.style.transform='scale('+sh+')';
        var cl=c.cloneNode(true);cl.style.left='0';cl.style.top='0';cl.style.height=h+'px';
        [].forEach.call(cl.querySelectorAll('[id]'),function(x){x.removeAttribute('id')});   /* בלי מזהים כפולים */
        [].forEach.call(cl.querySelectorAll('[data-u]'),function(x){x.setAttribute('data-cu',x.getAttribute('data-u'));x.removeAttribute('data-u')});   /* הממצאים והעריכה - בעמודים עצמם */
        fp.appendChild(cl);wrap.appendChild(fp);
        var nm=doc.createElement('div');nm.className='pmcn';nm.textContent=(pi+1)+(ci===0?' ימ\'':' שמ\'');wrap.appendChild(nm);
        wrap.setAttribute('data-pg',pi+1);
        box.appendChild(wrap)})});
    out.insertBefore(box,out.firstChild)}
  function pmApplyView(keepScroll){
    var doc=pmDoc();if(!doc)return;var H=doc.documentElement;
    [].forEach.call(document.querySelectorAll('#pmbar [data-v]'),function(b){var v=b.getAttribute('data-v');b.classList.toggle('on',v==='spread'?(S.view==='page'&&S.spread):(v===S.view&&!(v==='page'&&S.spread)))});
    H.classList.toggle('pmcol',S.view==='col');
    H.classList.toggle('pmspread',S.view==='page'&&S.spread);
    var out=doc.getElementById('prnout');if(!out)return;
    var sp=out.querySelector(':scope > .pmsp');
    if(S.view==='page'&&S.spread&&!sp&&S.pages[0]){sp=S.pages[0].cloneNode(false);sp.className=(S.pages[0].className+' pmsp');sp.innerHTML='';out.insertBefore(sp,S.pages[0])}
    if(!(S.view==='page'&&S.spread)&&sp)sp.remove();
    pmZoom(S.zoom==='nat'||S.zoom==='fit'?S.zoom:'keep')}
  function pmNatW(){
    var doc=pmDoc();if(!doc)return 800;var out=doc.getElementById('prnout');
    if(S.view==='col'){var c=doc.querySelector('#pmcols .pmc');return c?c.offsetWidth:600}   /* כבר בגודל המודפס (גם ב-B5) */
    var p=S.pages[0];if(!p)return 800;
    return S.view==='page'&&S.spread?p.offsetWidth*2+6*96/25.4+8:p.offsetWidth}
  function pmZoom(z){
    if(z==='cal'){var c=document.getElementById('pmcal');var r=document.getElementById('pmcr');r.value=PXMM||(96/25.4);document.getElementById('pmcard').style.width=(CARD_MM*r.value)+'px';c.classList.add('on');return}
    var doc=pmDoc();if(!doc)return;var out=doc.getElementById('prnout');if(!out)return;
    var fw=S.fr.clientWidth-90,natw=pmNatW();   /* מקום לסימני הבדיקה בשוליים */
    if(z==='fit'){S.zoom='fit';S.z=Math.max(0.2,Math.min(4,fw/natw))}
    else if(z==='nat'){S.zoom='nat';S.z=(PXMM||(96/25.4))/(96/25.4)}
    else if(z==='+'){S.zoom='z';S.z=Math.min(5,S.z*1.15)}
    else if(z==='-'){S.zoom='z';S.z=Math.max(0.15,S.z/1.15)}
    P.zoom=S.zoom;P.z=S.z;pmLsSet('lg-pm-prefs',P);
    [].forEach.call(document.querySelectorAll('#pmbar [data-z]'),function(b){var v=b.getAttribute('data-z');b.classList.toggle('on',v===S.zoom)});
    /* הגדלה כגוש (transform) - אורך הגלילה מתוקן במרווח שלילי/חיובי, והגוש ממורכז */
    var prevTop=doc.scrollingElement.scrollTop,prevZ=+(out.style.getPropertyValue('--pmz')||1);
    out.style.setProperty('--pmw',natw+'px');
    out.style.setProperty('--pmz',S.z);
    var natH=out.offsetHeight;
    out.style.setProperty('--pmb',(natH*(S.z-1))+'px');
    out.style.setProperty('--pmr',Math.max(8,(S.fr.clientWidth-natw*S.z)/2)+'px');
    if(prevZ&&prevZ!==S.z)doc.scrollingElement.scrollTop=prevTop*S.z/prevZ;
    pmIssuesPos()}

  /* ---------- ניווט ---------- */
  function pmPageEl(n){
    if(S.view==='col'){var d=pmDoc();return d&&d.querySelector('#pmcols .pmc[data-pg="'+n+'"]')}
    return S.pages[n-1]}
  function pmGoPage(n){n=Math.max(1,Math.min(S.pages.length,n||1));var e=pmPageEl(n);if(e)pmScrollTo(e,'start');document.getElementById('pm-pg').value=n}
  function pmDafs(rep){
    var sel=document.getElementById('pm-daf'),seen={},h='';
    (rep.pages||[]).forEach(function(p,i){[p.daf0,p.daf1].forEach(function(d){if(d&&!seen[d]){seen[d]=i+1;h+='<option value="'+pmGe(d)+'">'+pmGe(d)+'</option>'}})});
    S.dafPage=seen;sel.innerHTML=h}
  function pmGoDaf(d){
    var doc=pmDoc();if(!doc)return;
    /* סימן הדף עצמו בעמוד (מדויק יותר מתחילת העמוד) */
    var mk=[].slice.call(doc.querySelectorAll('#prnout .ptx .dafmark')).find(function(x){var t=(x.getAttribute('data-daf')||x.textContent||'').trim();return t===d||t.replace(/[^א-ת.:]/g,'')===d.replace(/[^א-ת.:]/g,'')});
    if(mk&&S.view!=='col'){pmScrollTo(mk,'center');return}
    if(S.dafPage&&S.dafPage[d])pmGoPage(S.dafPage[d])}
  /* העמוד שבמרכז המסך - למונה "עמוד N" */
  function pmTrackPage(){
    var doc=pmDoc();if(!doc||!S.pages.length)return;var mid=(S.fr.clientHeight||600)/3,n=1;
    for(var i=0;i<S.pages.length;i++){var e=pmPageEl(i+1);if(!e)continue;var r=e.getBoundingClientRect();if(r.top<=mid)n=i+1;else break}
    var inp=document.getElementById('pm-pg');if(document.activeElement!==inp)inp.value=n}

  /* ---------- הבודק החי ---------- */
  var KIND={'חור בטור':'hole','סוף פרק לא מאוזן':'bal','שורה שהתארכה':'ov','לבדוק אחר כך':'later'};
  var HINT={
    'מילה בודדת בשורה אחרונה':'לחץ על השורה ושנה מילה, או קצר/האריך את הפסקה כך שתרד מילה נוספת',
    'כותרת בתחתית טור':'אפשר להוסיף או להסיר שורה לפני הכותרת, כדי שתעבור עם התוכן שלה',
    'כותרת בלי רווח לפניה':'הוסף "רווח לפני" בעורך (Ctrl+נקודה)',
    'חור בטור':'הוסף או קצר טקסט לפני המקום, או שנה את הפסקה שלפני החור',
    'סוף פרק לא מאוזן':'הוסף או הסר שורה בטור הארוך',
    'שורה אלמנה בראש טור':'קצר או האריך את הפסקה בשורה',
    'שורה יתומה בסוף טור':'קצר או האריך את הפסקה בשורה',
    'סימן דף קרוב משלוש אותיות לטקסט':'קצר את כותרת הצד או הזז את סימן הדף',
    'כותרת שנשברה':'קצר את הכותרת לשורה אחת',
    'אות לועזית':'מחק את האות הלועזית',
    'שורה שהתארכה':'לחיצה: ההצעות לקיצור. Enter מקבל',
    'לבדוק אחר כך':'סימון שלך. לחיצה ימנית על הסימן מסירה אותו'};
  function pmIssues(doc,out,rep){
    [].forEach.call(out.querySelectorAll('.pmmk,.pmready'),function(x){x.remove()});
    var L=[];
    (rep.issues||[]).forEach(function(i){if(i.type==='חור בטור'&&rep.holes)return;L.push({type:i.type,page:i.page,daf:i.daf,u:i.unit,detail:i.detail||'',src:'engine'})});
    (rep.holes||[]).forEach(function(h){var x=(rep.issues||[]).find(function(i){return i.type==='חור בטור'&&i.page===h.page&&i.detail&&i.detail.indexOf(h.col)>-1});
      L.push({type:'חור בטור',page:h.page,daf:h.daf,u:x&&x.unit,col:h.col,detail:'טור '+h.col+': ריק של '+h.lines+' שורות'+(h.why?' ('+h.why+')':''),src:'engine'})});
    /* תוספות של המצב (לא במנוע): כותרת שנשברה לשתי שורות, אות לועזית, שורה שהתארכה, וסימני "לבדוק אחר כך" */
    var lh=0;try{lh=parseFloat(getComputedStyle(doc.querySelector('#prnout .ptx')).lineHeight)||0}catch(e){}
    var seenH={};
    [].forEach.call(out.querySelectorAll('.pg .ptx .row.dh > .main, .pg .ptx .row.nose > .main'),function(m){
      var row=m.parentElement,u=+row.getAttribute('data-u');if(!u||seenH[u])return;seenH[u]=1;
      var rg=doc.createRange();rg.selectNodeContents(m);var tops={};[].forEach.call(rg.getClientRects(),function(r){if(r.width>1)tops[Math.round(r.top)]=1});
      if(Object.keys(tops).length>1)L.push({type:'כותרת שנשברה',page:pmPageOf(row),u:u,detail:'הכותרת נשברה ל-'+Object.keys(tops).length+' שורות',src:'pm'})});
    var seenL={};
    [].forEach.call(out.querySelectorAll('.pg .ptx .row[data-u] .main'),function(m){var row=m.closest('.row');var u=+row.getAttribute('data-u');if(seenL[u])return;
      var t=m.textContent||'';var mm=/[A-Za-z]/.exec(t.replace(/leokmei\.com/g,''));if(mm){seenL[u]=1;L.push({type:'אות לועזית',page:pmPageOf(row),u:u,detail:'"'+t.substr(Math.max(0,mm.index-8),18)+'"',src:'pm'})}});
    try{if(typeof OVS!=='undefined'&&OVS.items&&OVS.items.length){
      var inPk={};S.pages.forEach(function(pe){[].forEach.call(pe.querySelectorAll('.ptx .row[data-u]'),function(r){inPk[+r.getAttribute('data-u')]=1})});
      OVS.items.forEach(function(it){if(typeof ovDone==='function'&&ovDone(it))return;if(!inPk[it.u])return;
        L.push({type:'שורה שהתארכה',u:it.u,li:it.li,page:0,detail:'חסרות '+it.miss+' אותיות'+(it.sug&&it.sug[0]?' · הצעה: '+(typeof ovPlain==='function'?ovPlain:String)(it.sug[0].kind==='split'?it.sug[0].parts.join(' / '):it.sug[0].html||'').slice(0,60):''),ov:it,src:'ov'})})}}catch(e){}
    S.later.forEach(function(x){L.push({type:'לבדוק אחר כך',u:x.u,li:x.li,page:0,detail:x.note||'',later:x,src:'later'})});
    /* מיקום: העמוד והשורה בעימוד הנוכחי */
    /* ממצא בלי יחידה (תווית, סימן דף): לפי סימן הדף בעמוד, ואם אין - בראש העמוד או הפרק. ממצא של המנוע לעולם אינו נשמט */
    var DM=[].slice.call(out.querySelectorAll('.pg .ptx .dafmark'));
    L.forEach(function(i){var el=i.u?pmFindRow(doc,i.u,i.li||0):null;
      if(!el&&i.daf){var dn=String(i.daf).replace(/[^א-ת.:]/g,'');el=DM.find(function(x){return String(x.getAttribute('data-daf')||x.textContent).replace(/[^א-ת.:]/g,'')===dn})||null;if(el)el=el.closest('.row')||el}
      if(!el&&i.page&&S.pages[i.page-1])el=S.pages[i.page-1];
      if(!el&&i.src==='engine')el=S.pages[0];
      i.el=el;if(el&&!i.page)i.page=pmPageOf(el)});
    L=L.filter(function(i){return i.el});
    L.sort(function(a,b){return (a.page-b.page)||(a.el.getBoundingClientRect().top-b.el.getBoundingClientRect().top)});
    S.issues=L;S.ii=-1;
    var nb=L.filter(function(i){return i.src!=='later'}).length;
    var bt=document.getElementById('pm-next');bt.textContent=nb?(nb+' לבדיקה ‹ הבא'):'מוכן לדפוס ✓';bt.classList.toggle('ok',!nb);
    document.getElementById('pm-ln').textContent=S.later.length;
    L.forEach(function(i,k){var m=doc.createElement('div');m.className='pmmk k-'+(KIND[i.type]||'e');m.textContent=i.src==='later'?'?':'!';
      m.title=i.type+(i.detail?'\n'+i.detail:'')+(HINT[i.type]?'\n'+HINT[i.type]:'');m.setAttribute('data-i',k);i.mk=m;out.appendChild(m)});
    if(!nb&&S.pages[0]){var rd=doc.createElement('div');rd.className='pmready';rd.textContent='מוכן לדפוס';out.appendChild(rd);S.readyEl=rd}else S.readyEl=null;
    pmIssuesPos();pmSide()}
  function pmPageOf(el){for(var i=0;i<S.pages.length;i++)if(S.pages[i].contains(el))return i+1;return 0}
  function pmIssuesPos(){
    var doc=pmDoc();if(!doc)return;var out=doc.getElementById('prnout');if(!out)return;
    var o=out.getBoundingClientRect(),z=S.z||1;
    S.issues.forEach(function(i){if(!i.mk)return;var col=S.view==='col';
      var el=i.el;if(col){i.mk.style.display='none';return}
      i.mk.style.display='';
      var pe=S.pages[i.page-1]||el,pr=pe.getBoundingClientRect(),r=el.getBoundingClientRect();
      i.mk.style.top=((r.top-o.top)/z)+'px';
      i.mk.style.left=((pr.right-o.left)/z+6)+'px'});
    /* "מוכן לדפוס": בשוליים העליונים של העמוד הראשון, בפינה השמאלית (אין שם טקסט) */
    if(S.readyEl&&S.pages[0]){var pr0=S.pages[0].getBoundingClientRect();S.readyEl.style.top=((pr0.top-o.top)/z+6)+'px';S.readyEl.style.left=((pr0.left-o.left)/z+8)+'px'}}
  function pmNext(){
    var L=S.issues.filter(function(i){return i.src!=='later'});if(!L.length){pmMsg('מוכן לדפוס: אין ממצאים בפרק');return}
    var doc=pmDoc(),y=(S.fr.clientHeight||600)*0.3;
    var nx=L.find(function(i){return i.el.getBoundingClientRect().top>y+4})||L[0];
    pmFocusIssue(nx)}
  function pmFocusIssue(i){
    if(S.view==='col'){S.view='page';pmApplyView()}
    S.issues.forEach(function(x){if(x.mk)x.mk.classList.toggle('cur',x===i)});
    pmScrollTo(i.el,'center');
    try{i.el.classList.add('pmflash');setTimeout(function(){i.el.classList.remove('pmflash')},1600)}catch(e){}
    pmStat(i.type+(i.detail?': '+i.detail:''),0)}
  function pmIssueClick(i){
    if(i.ov){pmOv(i.ov);return}
    if(i.src==='later'){pmFocusIssue(i);return}
    var p=i.el&&i.el.tagName==='P'?i.el:(i.el&&i.el.querySelector&&i.el.querySelector('.main > p'));
    pmFocusIssue(i);if(p&&p.closest('.ptx'))pmEdit(p)}
  /* שורה שהתארכה: חלונית ההצעות הקיימת (overflow_ui), מעל מצב הדפוס. Enter מקבל */
  function pmOv(it){
    try{if(!it._p||!it._p.isConnected){if(typeof ovMark==='function')ovMark()}
      if(typeof ovOpen!=='function'||!it._p){pmMsg('ההצעות לשורה זו אינן זמינות כרגע');return}
      ovOpen(it);var d=document.getElementById('ovpop');if(d){d.style.zIndex=71;d.style.top='60px';d.style.left='12px'}}catch(e){pmMsg('ההצעות לא נפתחו: '+(e.message||e))}}
  function pmSide(){
    var s=document.getElementById('pmside');if(!s||!s.classList.contains('on'))return;
    var h='<h4>לבדוק אחר כך</h4>';
    if(!S.later.length)h+='<div style="color:#8a7d66">לחיצה ימנית על שורה בעמוד: "לבדוק אחר כך"</div>';
    S.later.forEach(function(x,k){h+='<div class="pml" data-k="'+k+'"><span class="x" data-x="'+k+'" title="הסר">✕</span>'+pmGe(x.txt||'')+'<br><b>'+pmGe(x.daf||'')+(x.note?' · '+pmGe(x.note):'')+'</b></div>'});
    s.innerHTML=h;
    [].forEach.call(s.querySelectorAll('.pml'),function(e){e.addEventListener('click',function(ev){
      if(ev.target.getAttribute('data-x')!==null){S.later.splice(+ev.target.getAttribute('data-x'),1);pmLaterSave();pmRefreshIssues();return}
      var x=S.later[+e.getAttribute('data-k')];var doc=pmDoc();var el=doc&&pmFindRow(doc,x.u,x.li);if(el){if(S.view==='col'){S.view='page';pmApplyView()}pmScrollTo(el,'center')}})})}
  function pmLaterSave(){pmLsSet('lg-pm-later-'+SLUG,S.later)}
  function pmRefreshIssues(){var doc=pmDoc();if(doc&&S.report)pmIssues(doc,doc.getElementById('prnout'),S.report)}

  /* ---------- עריכה בתוך העמוד (פרומפט 52, 17.11.2026): העורך עצמו, בעמוד המודפס, ומהיר ----------
     מצב דפוס הוא העורך הקיים, רק בעמוד המודפס. אין עורך שני:
     א. לחיצה על שורה מכניסה את הסמן לפסקה במקום שנלחץ (בנוסח העורך, בלי מספרי התוס'). הקלדה רגילה נשארת בדפדפן
        ואינה מפעילה שום עבודה כבדה: הנוסח עובר לשורה המקבילה בעורך (pmMainEl) כ-150 אלפיות אחרי ההקשה האחרונה,
        עם אירוע input, ומשם השמירה של העורך עצמו (captureSoon).
     ב. כל פקודה של העורך (Enter, Delete בסוף, Backspace בהתחלה, Ctrl/Alt עם מקש, Ctrl+Z/Y וכו') מועברת אל העורך:
        הנוסח והסמן מועתקים לשורה המקבילה בדף המנהל, והמקש נשלח אליה. מה שהעורך שינה בנתונים (יחידה אחת או כמה,
        גם יחידות חדשות או שנמחקו) נבנה מחדש במסגרת בפונקציה של מנוע ההדפסה (__pmEng.row), ומשובץ במקומו בטור.
        הסמן חוזר למקום שבו העורך השאיר אותו. פקודה שהעורך אינו מטפל בה - נשארת לדפדפן במסגרת.
     ג. אין עימוד מחדש של הפרק אחרי עריכה. הפסקה נשברת לשורות בעצמה (אותו רוחב ואותו גופן), ושאר הטור זז
        למעלה או למטה בלבד. אם מספר השורות לא השתנה - שום שורה אחרת אינה זזה, והעמוד אינו מסומן. אם השתנה -
        העמוד ומה שאחריו מסומנים "לא מעודכן" (קו דק בשולי הדף), שורה שגולשת מתחת לטור נראית חלשה, והסרגל אומר
        כמה שינויים ממתינים. "השלם עימוד" (F9) מעמד את הפרק כולו כמו קודם. */
  var LINESEL='#prnout .pg .ptx .main > p, #prnout .pg .ptx .main.dh, #prnout .pg .ptx .main.nose, #prnout .pg .ptx .rail .anchor';
  function pmWin(){try{return S.fr&&S.fr.contentWindow}catch(e){return null}}
  /* היעד במסגרת -> מפתח העורך (u<יחידה>.<n>): פסקה n, 0 = כותרת או כותרת צד, w = חלון המשנה */
  function pmKeyOf(t){
    var row=t&&t.closest&&t.closest('.row');if(!row||!row.getAttribute('data-u'))return null;
    var u=+row.getAttribute('data-u');
    if(t.classList.contains('anchor'))return {u:u,k:row.classList.contains('u')?'0':'w'};
    if(t.tagName==='P')return {u:u,k:String([].indexOf.call(row.querySelectorAll(':scope > .main > p'),t)+1)};
    return {u:u,k:'0'}}
  function pmMainEl(u,k){
    var key='u'+u+'.'+(k==null?0:k);
    var el=document.querySelector('#flow [data-ek="'+key+'"]');
    if(!el){pmShowPerek(S.pk);try{if(typeof revealTail==='function')revealTail()}catch(e){}el=document.querySelector('#flow [data-ek="'+key+'"]')}
    if(el&&el.getAttribute('contenteditable')!=='true'){try{if(typeof setEdit==='function'&&typeof EDIT!=='undefined'&&!EDIT)setEdit(true)}catch(e){}}
    return el}
  /* העותק הנראה של היעד בעמוד (שורה שחוצה טור נמצאת בשני הטורים: זו שבחלון הנראה) */
  function pmVisible(t){var tx=t.closest('.ptx');if(!tx)return true;var r=t.getBoundingClientRect(),b=tx.getBoundingClientRect();return r.bottom>b.top+2&&r.top<b.top+(parseFloat(tx.style.height)||b.height)*(S.z||1)-2}
  function pmFrameEl(doc,u,k){
    var rows=doc.querySelectorAll('#prnout .pg .ptx > .row[data-u="'+u+'"]'),c=[];
    [].forEach.call(rows,function(row){var t=null;
      if(k==='w'||(k==='0'&&row.classList.contains('u')&&!row.querySelector(':scope > .main.dh,:scope > .main.nose')))t=row.querySelector('.rail .anchor');
      else if(k==='0')t=row.querySelector(':scope > .main.dh,:scope > .main.nose')||row.querySelector('.rail .anchor');
      else t=row.querySelectorAll(':scope > .main > p')[+k-1];
      if(t)c.push(t)});
    return c.find(pmVisible)||c[0]||null}
  /* היסט בטקסט (בלי סימני התוס') <-> מקום בעץ */
  function pmOff(root,node,off){try{var r=root.ownerDocument.createRange();r.setStart(root,0);r.setEnd(node,off);
    var f=r.cloneContents();[].forEach.call(f.querySelectorAll('sup.tm,span.tmg'),function(x){x.remove()});return f.textContent.length}catch(e){return 0}}
  /* fwd: גבול בין שני צמתים - תחילת הבא (לתחילת בחירה), ולא סוף הקודם. כך בחירה של מילה שבתוך סגנון תו נשארת בתוכו */
  function pmPos(root,off,fwd){var w=root.ownerDocument.createTreeWalker(root,NodeFilter.SHOW_TEXT),n,last=null;
    while((n=w.nextNode())){if(n.parentElement&&n.parentElement.closest('sup.tm,span.tmg'))continue;last=n;var L=n.nodeValue.length;if(off<L||(off===L&&!fwd))return [n,off];off-=L}
    return last?[last,last.nodeValue.length]:[root,root.childNodes.length]}
  function pmSetSel(root,a,b){var d=root.ownerDocument,s=d.getSelection();if(!s)return;
    var sel=b!=null&&b!==a,lo=sel?Math.min(a,b):a,A=pmPos(root,a,sel&&a===lo);
    try{var r=d.createRange();r.setStart(A[0],A[1]);r.collapse(true);s.removeAllRanges();s.addRange(r);
      if(sel&&s.extend){var B=pmPos(root,b,b===lo);s.extend(B[0],B[1])}}catch(e){}}
  /* מקום מדויק בעץ (מסלול של מספרי ילדים): בין שני עותקים זהים של אותו HTML - המסגרת ושורת העורך */
  function pmPath(root,node){var p=[];while(node&&node!==root){var par=node.parentNode;if(!par)return null;p.unshift([].indexOf.call(par.childNodes,node));node=par}return node===root?p:null}
  function pmAt(root,path){var n=root;for(var i=0;i<path.length;i++){n=n.childNodes[path[i]];if(!n)return null}return n}
  function pmGetSel(root){var s=root.ownerDocument.getSelection();if(!s||!s.rangeCount||!root.contains(s.anchorNode))return null;
    return [pmOff(root,s.anchorNode,s.anchorOffset),pmOff(root,s.focusNode,s.focusOffset)]}
  function pmLines(el){if(!el)return 0;var rg=el.ownerDocument.createRange();rg.selectNodeContents(el);var t={};
    [].forEach.call(rg.getClientRects(),function(r){if(r.width>1&&r.height>1)t[Math.round((r.top+r.bottom)/2/3)]=1});return Object.keys(t).length}

  /* ---- כניסה לשורה ---- */
  function pmEdit(t,ev,off){
    if(S.phone||!t)return;
    var K=pmKeyOf(t);if(!K)return;
    var row=t.closest('.row');
    if(row.classList.contains('hatz')||t.classList.contains('hatz')){pmMsg('עיטור אינו נערך כאן');return}
    if(S.editing&&S.editing.p===t)return;
    if(off==null&&ev){var doc=t.ownerDocument,cr=doc.caretRangeFromPoint&&doc.caretRangeFromPoint(ev.clientX,ev.clientY);if(cr&&t.contains(cr.startContainer))off=pmOff(t,cr.startContainer,cr.startOffset)}
    pmLeave();
    var el=pmMainEl(K.u,K.k);
    if(!el){pmMsg('השורה לא נמצאה בעורך. פתח אותה בדף הרגיל');return}
    try{if(el.__was===undefined&&typeof edBase==='function')edBase(el)}catch(e){}
    t=pmFrameEl(pmDoc(),K.u,K.k)||t;row=t.closest('.row');
    S.editing={p:t,el:el,u:K.u,k:K.k,row:row,orig:t.innerHTML,dirty:false,n:pmLines(t),h:row.offsetHeight};
    S.focusKey={u:K.u,li:+K.k||0};
    t.innerHTML=el.innerHTML;
    t.setAttribute('contenteditable','true');t.classList.add('pmed');t.spellcheck=false;
    try{t.focus({preventScroll:true})}catch(e){}
    pmSetSel(t,off==null?t.textContent.length:off);
    pmStat('עריכה: כמו בעורך · Esc יציאה מן השורה · F9 השלם עימוד',0)}
  /* יציאה מן השורה: הנוסח עובר לעורך (אם לא עבר), והיחידה נבנית מחדש מן הנתונים (עם סימני התוס') */
  function pmLeave(){
    var E=S.editing;if(!E)return;
    pmSyncNow();S.editing=null;
    E.p.removeAttribute('contenteditable');E.p.classList.remove('pmed');
    var el=pmEnsureEl(E);
    if(el&&E.touched){try{if(typeof capture==='function')capture(el)}catch(e){}}
    if(E.touched)pmRender([E.u]);else E.p.innerHTML=E.orig;
    pmStat('',0)}
  function pmCommit(cancel){pmLeave()}
  function pmEnsureEl(E){if(E.el&&E.el.isConnected)return E.el;var el=pmMainEl(E.u,E.k);if(el)E.el=el;return el}
  /* הקלדה: בלי עבודה על כל הקשה. רק מדידת השורות של הפסקה (בפריים הבא), והעברה לעורך אחרי הפסקה קצרה */
  function pmOnInput(){var E=S.editing;if(!E)return;E.dirty=E.touched=true;
    clearTimeout(S.syncT);S.syncT=setTimeout(pmSyncNow,150);
    if(!S.raf)S.raf=requestAnimationFrame(function(){S.raf=0;pmMeasure()});
    pmAutoArm()}
  function pmSyncNow(){
    clearTimeout(S.syncT);var E=S.editing;if(!E||!E.dirty)return;E.dirty=false;
    var el=pmEnsureEl(E);if(!el)return;
    if(el.innerHTML!==E.p.innerHTML){el.innerHTML=E.p.innerHTML;try{el.dispatchEvent(new Event('input',{bubbles:true}))}catch(e){}}}
  /* הפסקה שבעריכה נשברה לשורות אחרות: שאר הטור זז, מדד ליד הפסקה, וסימון "לא מעודכן" */
  function pmMeasure(){
    var E=S.editing;if(!E||!E.p.isConnected)return;
    var h=E.row.offsetHeight;
    if(h!==E.h){pmShift(E.row,h-E.h);E.h=h;pmCross(E.row)}else pmMove(E.row,0)}

  /* ---- שינוי בטור: הזזה בתוך הטור בלבד, גלישה, וסימון ---- */
  function pmShift(row,dh){
    if(!dh)return;var tx=row.parentElement;if(!tx)return;var t0=parseFloat(row.style.top)||0;
    [].forEach.call(tx.children,function(r){if(r===row||!r.classList.contains('row'))return;var t=parseFloat(r.style.top)||0;if(t>t0+0.5)r.style.top=(t+dh)+'px'});
    pmOverflow(tx);pmMove(row,dh)}
  function pmOverflow(tx){
    var H=parseFloat(tx.style.height)||tx.clientHeight,over=0;
    [].forEach.call(tx.querySelectorAll(':scope > .row'),function(r){var t=parseFloat(r.style.top)||0;if(t+r.offsetHeight>H+1)over=Math.max(over,t+r.offsetHeight-H)});
    if(tx.dataset.pmclip===undefined)tx.dataset.pmclip=tx.style.clipPath||'';
    var col=tx.parentElement,lb=col&&col.querySelector(':scope > .pmovl');
    if(over>1){
      tx.style.clipPath='inset('+(String(tx.dataset.pmclip).match(/inset\(([^ ]+)/)||[0,'0'])[1]+' 0 -'+Math.ceil(over+4)+'px 0)';
      tx.style.webkitMaskImage=tx.style.maskImage='linear-gradient(to bottom,#000 0,#000 '+H+'px,rgba(0,0,0,.32) '+H+'px)';
      var lh=parseFloat(getComputedStyle(tx).lineHeight)||20;
      if(!lb&&col){lb=tx.ownerDocument.createElement('div');lb.className='pmovl';col.appendChild(lb)}
      if(lb){lb.style.top=(H+1)+'px';lb.textContent='גולש '+Math.max(1,Math.round(over/lh))+' שורות · השלם עימוד (F9)'}}
    else{tx.style.clipPath=tx.dataset.pmclip;tx.style.webkitMaskImage=tx.style.maskImage='';if(lb)lb.remove()}}
  /* מאזן לפי יחידה: כמה שורות היחידה הרוויחה או הפסידה מאז ההשלמה. יחידה שחזרה לאפס - העמוד שוב מדויק */
  function pmMove(row,dh){
    if(!row||!row.getAttribute)return;var uid=row.getAttribute('data-u');if(!uid)return;
    if((parseFloat(row.style.top)||0)<-0.5)return;     /* ההמשך של שורה שחוצה טור: נספר פעם אחת */
    var m=S.mv[uid]||(S.mv[uid]={px:0,pg:0});m.px+=dh||0;m.row=row;
    /* הסימנים מתעדכנים פעם אחת לפריים, ולא בכל שורה שזזה: כל קריאת מיקום אחרי כתיבה מכריחה פריסה של כל העמודים */
    if(!S.rcT)S.rcT=requestAnimationFrame(function(){S.rcT=0;pmRecalc()})}
  function pmStaleAt(el){pmMove(el&&el.closest?el.closest('.row'):el,0)}
  function pmRecalc(){
    var lh=S.lh||20,pend=0,bal=0,from=0,doc=pmDoc();if(!doc)return;var out=doc.getElementById('prnout');if(!out)return;
    var ids=Object.keys(S.mv),geo=[];
    /* קריאה: כל המיקומים בבת אחת */
    var o=out.getBoundingClientRect(),z=S.z||1;
    ids.forEach(function(uid){var m=S.mv[uid],n=Math.round(m.px/lh),row=m.row;
      if(!row||!row.isConnected)row=m.row=[].find.call(doc.querySelectorAll('#prnout .pg .ptx > .row[data-u="'+uid+'"]'),function(r){return (parseFloat(r.style.top)||0)>=-0.5})||null;
      if(row)m.pg=pmPageOf(row)||m.pg;
      if(n){pend++;bal+=n;if(!from||m.pg<from)from=m.pg}
      if(row){var er=row.getBoundingClientRect(),pg=row.closest('.pg'),pr=pg?pg.getBoundingClientRect():er;geo.push([uid,n,(er.top-o.top)/z,(pr.left-o.left)/z-62])}
      else geo.push([uid,n,null,null])});
    /* כתיבה */
    geo.forEach(function(g){var b=S.badges[g[0]];
      if(g[2]==null){if(b)b.remove();delete S.badges[g[0]];return}
      if(!b||!b.isConnected){b=doc.createElement('div');out.appendChild(b);S.badges[g[0]]=b}
      b.className='pmdelta '+(g[1]<0?'dn':g[1]>0?'up':'eq');b.textContent=g[1]?((g[1]>0?'+':'')+g[1]+' שורה'):'✓ לא זז';
      b.style.top=g[2]+'px';b.style.left=g[3]+'px'});
    if(from!==S.staleFrom)S.pages.forEach(function(pe,i){pe.classList.toggle('pmstale',!!from&&i+1>=from)});
    S.pend=pend;S.bal=bal;S.staleFrom=from;
    pmBar();pmAutoArm()}
  /* שורה שחוצה טור או עמוד: אם מספר השורות שלה השתנה, החלוקה בין החלקים כבר אינה מדויקת - רק "השלם עימוד" יודע */
  function pmCross(row){var u=row.getAttribute('data-u'),doc=row.ownerDocument;
    if(doc.querySelectorAll('#prnout .pg .ptx > .row[data-u="'+u+'"]').length>1){S.cross=1;pmBar()}}
  /* ---- בנייה מחדש של יחידות במסגרת, מן הנתונים של דף המנהל ---- */
  function pmLoc(DD,uid){for(var i=0;i<DD.pages.length;i++){var U=DD.pages[i].units;for(var k=0;k<U.length;k++)if(U[k].id===uid)return {pi:i,ki:k,u:U[k]}}return null}
  function pmCarryMarks(oldRow,newRow){
    var op=oldRow.querySelectorAll(':scope > .main > p'),np=newRow.querySelectorAll(':scope > .main > p');
    [].forEach.call(op,function(p,i){var q=np[i];if(!q)return;
      var ms=[].filter.call(p.querySelectorAll('sup.tm,span.tmg'),function(m){return !m.parentElement.closest('span.tmg')});
      ms.forEach(function(m){var r=p.ownerDocument.createRange();r.setStart(p,0);r.setEndBefore(m);var f=r.cloneContents();
        [].forEach.call(f.querySelectorAll('sup.tm,span.tmg'),function(x){x.remove()});var at=pmPos(q,f.textContent.length);
        try{var rr=q.ownerDocument.createRange();rr.setStart(at[0],at[1]);rr.insertNode(m.cloneNode(true))}catch(e){}})})}
  function pmRender(uids){
    var w=pmWin(),doc=pmDoc();if(!w||!w.__pmEng||!doc)return;
    var FD=w.__pmEng.data(),seen={};
    uids.forEach(function(uid){if(seen[uid])return;seen[uid]=1;
      var loc=pmLoc(D,uid),floc=pmLoc(FD,uid);
      var rows=[].slice.call(doc.querySelectorAll('#prnout .pg .ptx > .row[data-u="'+uid+'"]'));
      if(!loc){rows.forEach(function(r){pmShift(r,-r.offsetHeight);r.remove()});if(floc)FD.pages[floc.pi].units.splice(floc.ki,1);return}
      var nu=JSON.parse(JSON.stringify(loc.u));
      if(floc)FD.pages[floc.pi].units[floc.ki]=nu;
      else{var at=0,pu=D.pages[loc.pi].units;for(var k=loc.ki-1;k>=0;k--){var fp=pmLoc(FD,pu[k].id);if(fp){at=fp.ki+1;break}}FD.pages[loc.pi].units.splice(at,0,nu)}
      var html=w.__pmEng.row(nu,loc.pi),tpl=doc.createElement('template');
      if(!rows.length){
        /* יחידה חדשה: אחרי השורה של היחידה שלפניה, באותו טור */
        var prev=null;for(var q=loc.ki-1;q>=0&&!prev;q--){var pr=doc.querySelectorAll('#prnout .pg .ptx > .row[data-u="'+D.pages[loc.pi].units[q].id+'"]');if(pr.length)prev=pr[pr.length-1]}
        if(!prev){S.cross=1;pmBar();return}
        tpl.innerHTML=html;var nr=tpl.content.firstElementChild;if(!nr)return;
        nr.removeAttribute('id');nr.setAttribute('data-u',uid);nr.style.cssText=prev.style.cssText;
        nr.style.top=((parseFloat(prev.style.top)||0)+prev.offsetHeight)+'px';
        prev.parentNode.insertBefore(nr,prev.nextSibling);
        var t1=parseFloat(nr.style.top);[].forEach.call(nr.parentNode.children,function(r){if(r!==nr&&r.classList.contains('row')&&(parseFloat(r.style.top)||0)>=t1-0.5)r.style.top=((parseFloat(r.style.top)||0)+nr.offsetHeight)+'px'});
        pmOverflow(nr.parentNode);pmMove(nr,nr.offsetHeight);return}
      rows.forEach(function(r){
        tpl.innerHTML=html;var nr=tpl.content.firstElementChild;if(!nr)return;
        nr.removeAttribute('id');nr.setAttribute('data-u',uid);nr.style.cssText=r.style.cssText;
        if(r.classList.contains('gapm'))nr.classList.add('gapm');
        var o1=r.querySelector(':scope > .main > p:first-child')||r.querySelector(':scope > .main'),n1=nr.querySelector(':scope > .main > p:first-child')||nr.querySelector(':scope > .main');
        if(o1&&n1&&o1.style.marginTop)n1.style.marginTop=o1.style.marginTop;
        pmCarryMarks(r,nr);
        var h0=r.offsetHeight;r.replaceWith(nr);var dh=nr.offsetHeight-h0;
        if(dh)pmShift(nr,dh);else pmMove(nr,0)});
      if(rows.length>1)pmCross(rows[0])})}
  /* מה השתנה בנתונים סביב יחידה (העמוד שלה ושניים סמוכים): לפני ואחרי פקודה */
  function pmSnap(uid){var L=pmLoc(D,uid),m={pis:[]};if(!L)return m;
    for(var i=Math.max(0,L.pi-1);i<=Math.min(D.pages.length-1,L.pi+1);i++){m.pis.push(i);D.pages[i].units.forEach(function(u){m[u.id]=JSON.stringify(u)})}return m}
  function pmDiff(m){var ch=[],now={};
    m.pis.forEach(function(i){D.pages[i].units.forEach(function(u){now[u.id]=1;if(m[u.id]!==JSON.stringify(u))ch.push(u.id)})});
    Object.keys(m).forEach(function(k){if(k!=='pis'&&!now[k])ch.push(+k)});return ch}

  /* ---- פקודה של העורך: מועברת לשורה המקבילה בדף המנהל ---- */
  function pmProxy(e){
    var E=S.editing;if(!E)return false;
    var t0=performance.now(),TP={};var tp=function(k){TP[k]=Math.round(performance.now()-t0)};
    pmSyncNow();tp('sync');
    var el=pmEnsureEl(E);if(!el)return false;
    var sel=pmGetSel(E.p)||[0,0],snap=pmSnap(E.u);
    /* אותו מקום בדיוק בעץ (העותקים זהים אחרי pmSyncNow): גם גבול של סגנון תו נשמר כפי שהוא */
    var fs=E.p.ownerDocument.getSelection(),xs=null;
    if(fs&&fs.rangeCount&&E.p.contains(fs.anchorNode)&&(el.innerHTML===E.p.innerHTML||el.textContent===E.p.textContent)){var pa=pmPath(E.p,fs.anchorNode),pf=pmPath(E.p,fs.focusNode);if(pa&&pf)xs=[pa,fs.anchorOffset,pf,fs.focusOffset]}
    S.proxying=true;
    /* פקודה של העורך שמכניסה HTML במקום הסמן (טאב יישור לשמאל): document.execCommand אינו פועל בדף המנהל כשהמיקוד
       הוא במסגרת. בזמן ההעברה בלבד - אותה פעולה בטווח הבחירה, בלי execCommand */
    var EX=document.execCommand;
    document.execCommand=function(cmd,ui,val){
      if(cmd==='insertHTML'||cmd==='insertText'){var s0=getSelection();if(!s0.rangeCount)return false;var rg=s0.getRangeAt(0);rg.deleteContents();
        var sc=rg.startContainer;if(sc.nodeType===3&&rg.startOffset>0&&sc.nodeValue.charAt(rg.startOffset-1)===' '){var so=rg.startOffset;sc.nodeValue=sc.nodeValue.slice(0,so-1)+'\u00a0'+sc.nodeValue.slice(so);rg.setStart(sc,so);rg.collapse(true)}
        var fr=cmd==='insertHTML'?rg.createContextualFragment(String(val)):document.createTextNode(String(val));
        /* כמו execCommand: רווח בקצה של מה שהוכנס נשמר כרווח קשיח, כדי שלא יתמזג */
        var tw=document.createTreeWalker(fr.nodeType===3?(function(){var d=document.createDocumentFragment();d.appendChild(fr);fr=d;return d})():fr,NodeFilter.SHOW_TEXT),tn,tl=[];while((tn=tw.nextNode()))tl.push(tn);
        if(tl.length){tl[0].nodeValue=tl[0].nodeValue.replace(/^ /,'\u00a0');var z=tl[tl.length-1];z.nodeValue=z.nodeValue.replace(/ $/,'\u00a0')}
        var last=fr.lastChild||fr;rg.insertNode(fr);
        try{rg.setStartAfter(last);rg.collapse(true);s0.removeAllRanges();s0.addRange(rg)}catch(x){}
        try{(rg.startContainer.nodeType===1?rg.startContainer:rg.startContainer.parentElement).dispatchEvent(new Event('input',{bubbles:true}))}catch(x){}
        return true}
      return EX.apply(document,arguments)};
    var ev=new KeyboardEvent('keydown',{key:e.key,code:e.code,ctrlKey:e.ctrlKey,altKey:e.altKey,shiftKey:e.shiftKey,metaKey:e.metaKey,modifierAltGraph:!!(e.getModifierState&&e.getModifierState('AltGraph')),bubbles:true,cancelable:true});
    try{try{window.focus();el.focus({preventScroll:true})}catch(x){}
      var ok=false;
      if(xs){var na=pmAt(el,xs[0]),nf=pmAt(el,xs[2]),fa=pmAt(E.p,xs[0]),ff=pmAt(E.p,xs[2]);
        var same=function(x,y){return x&&y&&x.nodeType===y.nodeType&&(x.nodeType!==3||x.nodeValue===y.nodeValue)};
        if(same(na,fa)&&same(nf,ff)){try{var ms=getSelection(),mr=document.createRange();mr.setStart(na,xs[1]);mr.collapse(true);ms.removeAllRanges();ms.addRange(mr);if(na!==nf||xs[1]!==xs[3])ms.extend(nf,xs[3]);ok=true}catch(x){}}}
      if(!ok)pmSetSel(el,sel[0],sel[1]);
      el.dispatchEvent(ev);tp('editor')}
    finally{S.proxying=false;document.execCommand=EX}
    if(!ev.defaultPrevented){try{E.p.focus({preventScroll:true})}catch(x){}pmSetSel(E.p,sel[0],sel[1]);return false}
    e.preventDefault();
    /* הסמן בדף המנהל, אחרי הפקודה */
    var s=document.getSelection(),an=s&&s.anchorNode,ae=document.activeElement;
    var host=(an&&(an.nodeType===1?an:an.parentElement)||{}).closest?(an.nodeType===1?an:an.parentElement).closest('[data-ek]'):null;
    if(!host&&ae&&ae.closest)host=ae.closest('[data-ek]');
    var ek=host&&host.getAttribute('data-ek'),g=host?pmGetSel(host):null;
    /* נוסח שהעורך שינה בלי לשמור (סגנון תו) - נשמר עכשיו, כדי שהנתונים יהיו מעודכנים */
    try{if(host&&typeof capture==='function')capture(host);if(el.isConnected&&el!==host&&typeof capture==='function')capture(el)}catch(x){}
    tp('capture');var ch=pmDiff(snap);if(ch.indexOf(E.u)<0)ch.push(E.u);tp('diff');
    E.p.removeAttribute('contenteditable');E.p.classList.remove('pmed');S.editing=null;
    var n0=E.n;
    pmRender(ch);tp('render');
    var m=ek&&/^u(\d+)\.(\w+)$/.exec(ek);
    var t=m&&pmFrameEl(pmDoc(),+m[1],m[2]);
    if(t){pmEdit(t,null,g?g[1]:0);if(g&&g[0]!==g[1])pmSetSel(t,g[0],g[1])}
    else{try{(pmDoc().body||{}).focus&&pmDoc().body.focus()}catch(x){}}
    /* מדד השורות של הפסקה שבה עמדת לפני הפקודה */
    tp('caret');S.lastCmd={path:!!xs,tp:TP,key:(e.ctrlKey?'Ctrl+':'')+(e.altKey?'Alt+':'')+(e.shiftKey?'Shift+':'')+(e.code||e.key),ms:Math.round(performance.now()-t0)};
    S.cmdMs.push(S.lastCmd.ms);if(S.cmdMs.length>200)S.cmdMs.shift();
    pmBar();pmAutoArm();
    return true}

  /* ---- ניווט בין השורות של העמוד (חיצים, PageUp/PageDown) ---- */
  function pmTargets(){var doc=pmDoc();if(!doc)return [];return [].filter.call(doc.querySelectorAll(LINESEL),function(t){return pmVisible(t)&&!t.closest('.hatz')})}
  function pmCaretRect(doc){var s=doc.getSelection();if(!s||!s.rangeCount)return null;var r=s.getRangeAt(0).cloneRange();r.collapse(!(s.focusNode===r.endContainer&&s.focusOffset===r.endOffset));
    var rs=r.getClientRects();if(rs.length)return rs[0];var b=r.getBoundingClientRect();return b.height?b:null}
  function pmNav(e){
    var E=S.editing,doc=pmDoc();if(!E||!doc)return false;
    var k=e.key;if(e.ctrlKey||e.altKey||e.metaKey||e.shiftKey)return false;
    var p=E.p,L=pmTargets(),i=L.indexOf(p);
    var go=function(t,end,x){if(!t)return true;
      var off=null;if(x!=null){var r=t.getClientRects(),rr=end?r[r.length-1]:r[0];if(rr){var cr=doc.caretRangeFromPoint&&doc.caretRangeFromPoint(Math.max(rr.left+1,Math.min(rr.right-1,x)),rr.top+rr.height/2);if(cr&&t.contains(cr.startContainer))off=pmOff(t,cr.startContainer,cr.startOffset)}}
      pmEdit(t,null,off==null?(end?1e9:0):off);if(S.editing)pmSetSel(S.editing.p,Math.min(off==null?(end?S.editing.p.textContent.length:0):off,S.editing.p.textContent.length));
      var pe=S.editing&&S.editing.p.getBoundingClientRect();if(pe&&(pe.bottom>(S.fr.clientHeight||600)-20||pe.top<20))pmScrollTo(S.editing.p,'center');return true};
    if(k==='ArrowDown'||k==='ArrowUp'){
      var c=pmCaretRect(doc),rs=p.getClientRects();if(!c||!rs.length)return false;
      var lastTop=rs[rs.length-1].top,firstTop=rs[0].top;
      if(k==='ArrowDown'&&c.top>=lastTop-2){e.preventDefault();return go(L[i+1],false,c.left)}
      if(k==='ArrowUp'&&c.top<=firstTop+2){e.preventDefault();return go(L[i-1],true,c.left)}
      return false}
    if(k==='ArrowLeft'||k==='ArrowRight'){
      var g=pmGetSel(p);if(!g||g[0]!==g[1])return false;var len=p.textContent.length;
      /* מימין לשמאל: שמאלה = קדימה בטקסט */
      if(k==='ArrowLeft'&&g[1]>=len){e.preventDefault();return go(L[i+1],false,null)}
      if(k==='ArrowRight'&&g[1]<=0){e.preventDefault();return go(L[i-1],true,null)}
      return false}
    if(k==='PageDown'||k==='PageUp'){
      e.preventDefault();var pg=pmPageOf(p)+(k==='PageDown'?1:-1);if(pg<1||pg>S.pages.length)return true;
      var t=L.find(function(x){return pmPageOf(x)===pg});pmGoPage(pg);return go(t,false,null)}
    return false}

  /* ---- השלם עימוד (F9) ---- */
  function pmComplete(then){
    if(S.busy){S.then=then||S.then;S.dirty=true;S.completing=S.completing||{pages:S.pages.length,cols:[]};return}
    var E=S.editing,keep=null;
    if(E){var g=pmGetSel(E.p);keep={u:E.u,k:E.k,off:g?g[1]:0};pmLeave()}
    S.resume=keep;S.then=then||null;S.completing={pages:S.pages.length,cols:S.report?S.report.pages.map(function(p){return p.cols.reduce(function(a,c){return a+c.lines},0)}):[]};
    S.focusKey=keep?{u:keep.u,li:+keep.k||0}:S.focusKey;
    pmRelayout()}
  /* אחרי עימוד מלא: הסימונים נמחקים, מה זז, והסמן חוזר */
  function pmAfterFull(){
    var C=S.completing;S.completing=null;
    var n=S.pages.length,msg='';
    if(C){var nc=S.report.pages.map(function(p){return p.cols.reduce(function(a,c){return a+c.lines},0)});
      msg='הפרק: '+(C.pages===n?n+' עמודים':C.pages+' → '+n+' עמודים');
      for(var i=0;i<Math.min(C.cols.length,nc.length);i++)if(C.cols[i]!==nc[i]){var d=nc[i]-C.cols[i];msg+=' · עמוד '+(i+1)+(d>0?' קיבל '+d:' מסר '+(-d))+' שורות';break}}
    S.pend=0;S.bal=0;S.staleFrom=0;S.cross=0;S.badges={};S.mv={};
    pmBar(msg);
    var R=S.resume;S.resume=null;
    if(R){var t=pmFrameEl(pmDoc(),R.u,R.k);if(t){pmEdit(t,null,R.off);if(S.kbuf&&S.editing){try{pmDoc().execCommand('insertText',false,S.kbuf)}catch(e){}}}}
    S.kbuf='';
    if(S.then){var f=S.then;S.then=null;setTimeout(f,50)}}
  /* השלמה לבד אחרי X שניות שקט (הגדרה, ברירת מחדל: כבוי) */
  function pmAutoArm(){clearTimeout(S.autoT);var x=+P.auto||0;if(!x||!S.pend)return;S.autoT=setTimeout(function(){if(S.open&&S.pend&&!S.busy)pmComplete()},x*1000)}

  /* ---- הסרגל: שינויים ממתינים, מאזן השורות, חיסכון עמוד ---- */
  function pmBar(msg){
    var b=document.getElementById('pm-done'),pd=document.getElementById('pm-pend');if(!b||!pd)return;
    var t='';
    if(S.pend||S.bal||S.cross){
      t=(S.pend?S.pend+' שינויים ממתינים':'')+(S.bal?' · הפרק: '+(S.bal>0?'+':'')+S.bal+' שורות מאז ההשלמה':'');
      var lp=S.report&&S.report.pages&&S.report.pages[S.report.pages.length-1];
      if(lp&&S.bal<=0){var need=lp.cols.reduce(function(a,c){return a+c.lines},0)+S.bal;if(need>0&&need<=15)t+=' · לחיסכון עמוד: עוד כ-'+need+' שורות'}
      if(S.cross)t+=' · השלם עימוד לבדיקה'}
    else if(msg)t=msg;
    pd.textContent=t;b.classList.toggle('hot',!!(S.pend||S.cross))}

  /* ---- שינוי שלא בא מן המצב (קבלת הצעה בחלונית, סכם): רק היחידות שהשתנו ---- */
  function pmExternal(){
    if(!S.open||S.busy||S.proxying)return;
    var w=pmWin();if(!w||!w.__pmEng||!S.report||!S.pkPi)return;
    var FD=w.__pmEng.data(),ch=[],E=S.editing;
    for(var i=S.pkPi[0];i<=S.pkPi[1];i++){var p=D.pages[i],fp=FD.pages[i];if(!p||!fp)continue;
      var fu={};fp.units.forEach(function(u){fu[u.id]=JSON.stringify(u)});
      p.units.forEach(function(u){var j=JSON.stringify(u);
        if(fu[u.id]!==j){if(E&&u.id===E.u){var fl=pmLoc(FD,u.id);if(fl)FD.pages[fl.pi].units[fl.ki]=JSON.parse(j)}else ch.push(u.id)}
        delete fu[u.id]});
      Object.keys(fu).forEach(function(k){ch.push(+k)})}
    if(ch.length)pmRender(ch)}

  function pmLineAt(doc,e){
    var p=e.target.closest&&e.target.closest(LINESEL);if(p)return p;
    var L=doc.elementsFromPoint?doc.elementsFromPoint(e.clientX,e.clientY):[];
    for(var i=0;i<L.length;i++){var q=L[i].closest&&L[i].closest(LINESEL);if(q)return q}
    return null}
  function pmBind(doc){
    if(doc.__pmb)return;doc.__pmb=1;
    doc.addEventListener('click',function(e){
      var mk=e.target.closest&&e.target.closest('.pmmk');
      if(mk){e.preventDefault();var i=S.issues[+mk.getAttribute('data-i')];if(i)pmIssueClick(i);return}
      if(S.editing&&S.editing.p.contains(e.target))return;
      /* קישורי הקובץ (ציון דף, סימן התוס') אינם קופצים במצב דפוס: הלחיצה היא על השורה שמתחתם */
      if(e.target.closest&&e.target.closest('#prnout a'))e.preventDefault();
      var p=pmLineAt(doc,e);
      if(!p||S.phone){pmLeave();return}
      var sel=doc.getSelection();if(sel&&!sel.isCollapsed&&!(S.editing&&S.editing.p.contains(sel.anchorNode)))return;
      pmEdit(p,e)},true);
    doc.addEventListener('input',function(e){if(S.editing&&S.editing.p.contains(e.target))pmOnInput()},true);
    doc.addEventListener('paste',function(e){if(!S.editing||!S.editing.p.contains(e.target))return;e.preventDefault();
      var t=(e.clipboardData||{}).getData?e.clipboardData.getData('text/plain').replace(/\s+/g,' '):'';doc.execCommand('insertText',false,t)},true);
    doc.addEventListener('keydown',function(e){
      if(S.busy&&!S.editing){
        /* בזמן השלמת העימוד: הקלדה נשמרת, ונכנסת לשורה כשהעימוד מסתיים. הקלדה תמיד קודמת */
        if(e.key.length===1&&!e.ctrlKey&&!e.altKey&&!e.metaKey){e.preventDefault();S.kbuf=(S.kbuf||'')+e.key;return}
        if(e.key!=='F8'&&e.key!=='F9'){e.preventDefault();return}}
      if(e.key==='F9'){e.preventDefault();pmComplete();return}
      if(S.editing&&S.editing.p.isConnected){
        if(e.key==='Escape'){e.preventDefault();pmLeave();return}
        if(e.key==='F8'){e.preventDefault();pmClose();return}
        /* F2 (כניסה ויציאה ממצב עריכה) אינו פועל כאן: מצב דפוס הוא תמיד עריכה */
        if(e.key==='F2'){e.preventDefault();pmMsg('מצב דפוס הוא תמיד מצב עריכה. F8 יוצא ממנו');return}
        if((e.ctrlKey||e.metaKey)&&!e.altKey&&(e.key==='p'||e.key==='פ')){e.preventDefault();pmPrint();return}
        if(e.altKey&&!e.ctrlKey&&(e.key==='PageDown'||e.key==='PageUp')){e.preventDefault();pmMishna(e.key==='PageDown'?1:-1);return}
        if(pmNav(e))return;
        var k=e.key,mod=e.ctrlKey||e.altKey||e.metaKey;
        /* העתקה, גזירה, בחירת הכל - של הדפדפן */
        if(mod&&!e.altKey&&/^(KeyC|KeyX|KeyA|KeyV)$/.test(e.code))return;
        var g=null;
        if(k==='Delete'||k==='Backspace'){g=pmGetSel(S.editing.p);if(!g||g[0]!==g[1])return;
          if(k==='Delete'&&g[1]<S.editing.p.textContent.length&&!mod)return;
          if(k==='Backspace'&&g[1]>0&&!mod)return}
        if(mod||k==='Enter'||k==='Delete'||k==='Backspace'||k==='Tab')pmProxy(e);
        return}
      pmKeys(e)});
    doc.addEventListener('contextmenu',function(e){
      var mk=e.target.closest&&e.target.closest('.pmmk.k-later');
      if(mk){e.preventDefault();var i=S.issues[+mk.getAttribute('data-i')];if(i&&i.later){S.later.splice(S.later.indexOf(i.later),1);pmLaterSave();pmRefreshIssues()}return}
      var p=pmLineAt(doc,e);if(!p)return;
      e.preventDefault();
      var row=p.closest('.row'),u=+row.getAttribute('data-u'),K=pmKeyOf(p),li=K?(+K.k||0):0;
      var menu=document.getElementById('pmmenu'),fr=S.fr.getBoundingClientRect();
      menu.innerHTML='<div data-a="later">לבדוק אחר כך</div><div data-a="note">לבדוק אחר כך, עם הערה...</div><div data-a="edit">ערוך את השורה</div><div data-a="main">פתח בדף הרגיל</div>';
      var kk=fr.width/(S.fr.offsetWidth||fr.width||1);
      menu.style.top=(fr.top+e.clientY*kk)+'px';menu.style.left=(fr.left+e.clientX*kk)+'px';menu.style.display='block';
      menu.onclick=function(ev){var a=ev.target.getAttribute('data-a');menu.style.display='none';
        if(a==='later'||a==='note'){var note=a==='note'?(prompt('הערה:','')||''):'';
          var daf='';try{daf=(S.report.pages[pmPageOf(p)-1]||{}).daf0||''}catch(x){}
          S.later.push({u:u,li:li,txt:(p.textContent||'').trim().slice(0,60),daf:daf,note:note,t:Date.now()});pmLaterSave();pmRefreshIssues();pmMsg('נרשם ברשימת "לבדוק אחר כך"')}
        else if(a==='edit')pmEdit(p);
        else if(a==='main'){S.anchor=u;pmClose();var el=pmMainEl(u,K?K.k:0);if(el){el.scrollIntoView({block:'center'});try{el.focus()}catch(x){}}}}});
    doc.addEventListener('scroll',function(){clearTimeout(S.st);S.st=setTimeout(pmTrackPage,80)},{passive:true})}
  /* Alt+PageUp/PageDown: המשנה הבאה / הקודמת בעמודים */
  function pmMishna(d){var doc=pmDoc();if(!doc)return;
    var L=[].filter.call(doc.querySelectorAll('#prnout .pg .ptx > .row > .main.mishna > p:first-child'),pmVisible);
    var cur=S.editing?S.editing.p.getBoundingClientRect().top:0,pg0=S.editing?pmPageOf(S.editing.p):0;
    var srt=L.map(function(t){return {t:t,pg:pmPageOf(t),y:t.getBoundingClientRect().top}});
    var nx=d>0?srt.find(function(x){return x.pg>pg0||(x.pg===pg0&&x.y>cur+2)}):srt.slice().reverse().find(function(x){return x.pg<pg0||(x.pg===pg0&&x.y<cur-2)});
    if(nx){pmEdit(nx.t,null,0);pmScrollTo(nx.t,'center')}}
  function pmKeys(e){
    if(S.proxying)return false;
    if(e.key==='F9'){e.preventDefault();pmComplete();return true}
    if(e.key==='F8'||e.key==='Escape'){e.preventDefault();pmClose();return true}
    if((e.key==='n'||e.key==='מ')&&!e.ctrlKey&&!e.altKey&&!e.metaKey){e.preventDefault();pmNext();return true}
    if(e.key==='PageDown'||e.key==='PageUp'){var n=(+document.getElementById('pm-pg').value||1)+(e.key==='PageDown'?1:-1);e.preventDefault();pmGoPage(n);return true}
    if((e.ctrlKey||e.metaKey)&&(e.key==='p'||e.key==='פ')){e.preventDefault();pmPrint();return true}
    return false}

  /* ---------- הדפס מה שאני רואה ---------- */
  function pmPrint(){
    pmCommit();
    if(S.pend||S.cross||S.busy){pmMsg('משלים עימוד לפני הדפסה');pmComplete(pmPrint);return}
    var w=null;try{w=S.fr.contentWindow}catch(e){}
    if(!w||!S.report){pmMsg('העימוד עוד לא הסתיים');return}
    try{w.focus();w.print()}catch(e){pmMsg('ההדפסה לא נפתחה: '+(e.message||e))}}

  /* ---------- הכפתור והקיצור ---------- */
  function pmButton(){
    if(!pmAdm()||document.getElementById('pmbtn'))return;
    var after=document.getElementById('ovnext')||document.getElementById('skpnext')||document.getElementById('skpbtn')||document.getElementById('peresel');
    var b=document.createElement('button');b.id='pmbtn';b.type='button';b.className='skpbtn skptop';
    b.textContent='מצב דפוס';b.title='מצב דפוס (F8): הפרק בדיוק כפי שיודפס, עם עריכה במקום';
    b.addEventListener('mousedown',function(e){e.preventDefault()});
    b.addEventListener('click',function(e){e.stopPropagation();S.open?pmClose():pmOpen()});
    if(after&&after.parentNode)after.parentNode.insertBefore(b,after.nextSibling);else (document.getElementById('bar')||document.body).appendChild(b);
    try{if(typeof barH==='function')barH()}catch(e){}}
  document.addEventListener('keydown',function(e){
    if(e.key==='F8'&&!e.ctrlKey&&!e.altKey&&!e.metaKey){if(!pmAdm())return;e.preventDefault();S.open?pmClose():pmOpen();return}
    if(S.open&&!(e.target&&e.target.closest&&e.target.closest('#pmbar input,#ovpop,#pmcal'))){
      if(document.getElementById('ovpop'))return;
      if(pmKeys(e))e.stopPropagation()}},true);
  setTimeout(function(){pmButton();
    /* זוכר את הבחירה במכשיר: מנהל שיצא מן הדף במצב דפוס חוזר אליו */
    if(pmAdm()&&pmLs('lg-pm-on',0)&&innerWidth>700&&!S.open)setTimeout(function(){if(!S.open)pmOpen()},600)},3200);
  setInterval(function(){if(pmAdm()&&!document.getElementById('pmbtn'))pmButton()},5000);
  window.lkPrintMode={open:pmOpen,close:pmClose,state:function(){return {open:S.open,busy:S.busy,pages:S.pages.length,issues:S.issues.map(function(i){return {type:i.type,page:i.page,u:i.u,detail:i.detail,src:i.src}}),ms:S.lastMs,zoom:S.z,view:S.view,editing:S.editing?{u:S.editing.u,k:S.editing.k}:null,pend:S.pend,bal:S.bal,cross:S.cross,lastCmd:S.lastCmd,cmdMs:S.cmdMs.slice()}},
    complete:pmComplete,
    relayout:pmRelayout,next:pmNext,go:pmGoPage,report:function(){return S.report}};
  })();
