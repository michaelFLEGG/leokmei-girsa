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
         pages:[],issues:[],ii:-1,later:pmLs('lg-pm-later-'+(typeof SLUG!=='undefined'?SLUG:''),[]),t0:0,lastMs:0,anchor:null};
  var P=pmLs('lg-pm-prefs',{paper:'b5',big:1,tos:1,view:'page',spread:0,zoom:'fit',z:1});
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
  function pmShowPerek(pk){
    try{if(typeof SEC==='undefined'||typeof render!=='function')return;
      for(var i=0;i<SEC.length;i++){var p=D.pages[SEC[i].to];if(p&&((p.perek||'')+'|'+(p.perekName||''))===pk){if(i!==cur)render(i);return}}}catch(e){}}

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
      '.pmdelta{position:absolute;z-index:6;font:bold 12px sans-serif;color:#1d3557;background:#fff;border:1px solid #1d3557;border-radius:4px;padding:0 5px;transition:opacity .6s}'+
      '.ptx .main p,.ptx .main.dh,.ptx .main.nose{cursor:text}'+
      '[contenteditable].pmed{outline:1.5px solid #1d6fa5;outline-offset:1px;background:#fff;position:relative;z-index:4}'+
      '.pmflash{outline:2px solid #1d6fa5;outline-offset:2px;transition:outline-color 1.2s}'+
    '}'+
    '@media print{.pmmk,.pmready,.pmdelta,#pmcols{display:none!important}}';

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
    $p('pm-x').addEventListener('click',pmClose);
    $p('pmcr').addEventListener('input',function(){$p('pmcard').style.width=(CARD_MM*this.value)+'px'});
    $p('pmcok').addEventListener('click',function(){PXMM=+$p('pmcr').value;pmLsSet('lg-pm-pxmm',PXMM);cal.classList.remove('on');pmZoom('nat')});
    $p('pmcx').addEventListener('click',function(){cal.classList.remove('on')});
    $p('pmcr0').addEventListener('click',function(){PXMM=0;pmLsSet('lg-pm-pxmm',0);cal.classList.remove('on');pmZoom('nat')});
    document.addEventListener('click',function(e){if(!menu.contains(e.target))menu.style.display='none'},true);
    /* כל שינוי בנתוני הדף (עריכה, קבלת הצעה, פיצול) - עימוד חוזר */
    document.addEventListener('lg-dv',function(){if(S.open&&!S.editing)pmSoon()});
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
    /* חזרה לדף הרגיל - למקום שבו עמדת במצב הדפוס */
    if(a){var r=document.getElementById('u'+a);if(r)r.scrollIntoView({block:'center'})}}
  function pmUrl(){
    var q=new URLSearchParams();q.set('print','1');q.set('pm','1');
    var pk=S.pk,a=-1,b=-1;
    D.pages.forEach(function(p,i){if(p.units&&p.units.length&&((p.perek||'')+'|'+(p.perekName||''))===pk){if(a<0)a=i;b=i}});
    if(a<0){a=0;b=D.pages.length-1}
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
    if(keep){var el=pmFindRow(doc,keep.k.u,keep.k.li);if(el){var dy=el.getBoundingClientRect().top-keep.y;doc.scrollingElement.scrollTop+=dy;pmDelta(doc,el)}}
    else if(S.anchor){var r0=pmFindRow(doc,S.anchor,0);if(r0)pmScrollTo(r0,'start')}
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

  /* ---------- עריכה בתוך העמוד ----------
     לחיצה על שורה פותחת את הפסקה לעריכה במקום, ברוחב הטור המודפס ובגופן המודפס. בזמן העריכה בפסקה נוסח העורך
     (בלי סימני התוספות ובלי רכיבי תצוגה). Enter או יציאה מן הפסקה שומרים: הנוסח נכתב לשורה המקבילה בעורך הקיים
     (אותה רשומה, אותה שמירה ואותו פרסום), ואז עימוד חוזר מן הנתונים. Esc מבטל. */
  function pmMainEl(u,li){
    var k='u'+u+'.'+(li||0);
    var el=document.querySelector('#flow [data-ek="'+k+'"]');
    if(!el){pmShowPerek(S.pk);try{if(typeof revealTail==='function')revealTail()}catch(e){}el=document.querySelector('#flow [data-ek="'+k+'"]')}
    return el}
  function pmEdit(p){
    if(S.editing)pmCommit();
    var row=p.closest('.row');if(!row||!row.getAttribute('data-u'))return;
    var u=+row.getAttribute('data-u');
    var li=0;if(p.tagName==='P'){li=[].indexOf.call(row.querySelectorAll(':scope > .main > p'),p)+1}
    if(row.classList.contains('hatz')||p.classList.contains('hatz')){pmMsg('עיטור אינו נערך כאן');return}
    var el=pmMainEl(u,li);
    if(!el){pmMsg('השורה לא נמצאה בעורך. פתח אותה בדף הרגיל');return}
    try{if(el.__was===undefined&&typeof edBase==='function')edBase(el)}catch(e){}
    var before=el.innerHTML;
    S.editing={p:p,el:el,u:u,li:li,before:before,orig:p.innerHTML};
    S.focusKey={u:u,li:li};
    p.innerHTML=before;
    p.setAttribute('contenteditable','true');p.classList.add('pmed');p.spellcheck=false;
    p.focus();
    try{var sel=p.ownerDocument.getSelection(),rg=p.ownerDocument.createRange();rg.selectNodeContents(p);rg.collapse(false);sel.removeAllRanges();sel.addRange(rg)}catch(e){}
    pmStat('עריכה: Enter שומר · Esc מבטל',0)}
  function pmCommit(cancel){
    var E=S.editing;if(!E)return;S.editing=null;
    var p=E.p;p.removeAttribute('contenteditable');p.classList.remove('pmed');
    var now=p.innerHTML;
    if(cancel||now===E.before){p.innerHTML=E.orig;pmStat('',0);return}
    if(!E.el.isConnected){var el2=pmMainEl(E.u,E.li);if(el2)E.el=el2}
    if(!E.el||!E.el.isConnected){p.innerHTML=E.orig;pmMsg('העריכה לא נשמרה: השורה לא נמצאה בעורך');return}
    try{E.el.innerHTML=now;if(typeof capture==='function')capture(E.el);else throw new Error('העורך אינו זמין')}
    catch(e){p.innerHTML=E.orig;pmMsg('העריכה לא נשמרה: '+(e.message||e));return}
    pmMsg('נשמר, ויפורסם עם שאר העריכות');
    pmSoon()}
  function pmDelta(doc,el){
    var E=S.lastEdit;if(!E)return;S.lastEdit=null;
    try{var row=el.closest?el.closest('.row'):null;if(!row)return;
      var r=pmLines(el.tagName==='P'?el:row.querySelector('.main'));
      var d=r-E.lines;if(!d)return;
      var out=doc.getElementById('prnout'),o=out.getBoundingClientRect(),z=S.z||1,er=el.getBoundingClientRect();
      var b=doc.createElement('div');b.className='pmdelta';b.textContent=(d>0?'+':'')+d+' שורה';
      b.style.top=((er.top-o.top)/z)+'px';b.style.left=((er.left-o.left)/z-60)+'px';out.appendChild(b);
      setTimeout(function(){b.style.opacity='0'},1600);setTimeout(function(){b.remove()},2400)}catch(e){}}
  function pmLines(el){if(!el)return 0;var rg=el.ownerDocument.createRange();rg.selectNodeContents(el);var t={};[].forEach.call(rg.getClientRects(),function(r){if(r.width>1)t[Math.round(r.top)]=1});return Object.keys(t).length}

  var LINESEL='#prnout .pg .ptx .main > p, #prnout .pg .ptx .main.dh, #prnout .pg .ptx .main.nose';
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
      if(S.editing)pmCommit();
      if(!p||S.phone)return;
      var sel=doc.getSelection();if(sel&&!sel.isCollapsed)return;
      pmEdit(p)},true);
    doc.addEventListener('keydown',function(e){
      if(S.editing){
        if(e.key==='Escape'){e.preventDefault();pmCommit(true);return}
        if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();var E=S.editing;S.lastEdit={lines:pmLines(E.p)};pmCommit();return}
        return}
      pmKeys(e)});
    doc.addEventListener('contextmenu',function(e){
      var mk=e.target.closest&&e.target.closest('.pmmk.k-later');
      if(mk){e.preventDefault();var i=S.issues[+mk.getAttribute('data-i')];if(i&&i.later){S.later.splice(S.later.indexOf(i.later),1);pmLaterSave();pmRefreshIssues()}return}
      var p=pmLineAt(doc,e);if(!p)return;
      e.preventDefault();
      var row=p.closest('.row'),u=+row.getAttribute('data-u'),li=p.tagName==='P'?[].indexOf.call(row.querySelectorAll(':scope > .main > p'),p)+1:0;
      var menu=document.getElementById('pmmenu'),fr=S.fr.getBoundingClientRect();
      menu.innerHTML='<div data-a="later">לבדוק אחר כך</div><div data-a="note">לבדוק אחר כך, עם הערה...</div><div data-a="edit">ערוך את השורה</div><div data-a="main">פתח בדף הרגיל</div>';
      var kk=fr.width/(S.fr.offsetWidth||fr.width||1);
      menu.style.top=(fr.top+e.clientY*kk)+'px';menu.style.left=(fr.left+e.clientX*kk)+'px';menu.style.display='block';
      menu.onclick=function(ev){var a=ev.target.getAttribute('data-a');menu.style.display='none';
        if(a==='later'||a==='note'){var note=a==='note'?(prompt('הערה:','')||''):'';
          var daf='';try{var pg=S.pages[pmPageOf(p)-1];daf=(S.report.pages[pmPageOf(p)-1]||{}).daf0||''}catch(x){}
          S.later.push({u:u,li:li,txt:(p.textContent||'').trim().slice(0,60),daf:daf,note:note,t:Date.now()});pmLaterSave();pmRefreshIssues();pmMsg('נרשם ברשימת "לבדוק אחר כך"')}
        else if(a==='edit')pmEdit(p);
        else if(a==='main'){S.anchor=u;pmClose();var el=pmMainEl(u,li);if(el){el.scrollIntoView({block:'center'});try{el.focus()}catch(x){}}}}});
    doc.addEventListener('scroll',function(){clearTimeout(S.st);S.st=setTimeout(pmTrackPage,80)},{passive:true});
    doc.addEventListener('keydown',function(){},true)}
  function pmKeys(e){
    if(e.key==='F8'||e.key==='Escape'){e.preventDefault();pmClose();return true}
    if((e.key==='n'||e.key==='מ')&&!e.ctrlKey&&!e.altKey&&!e.metaKey){e.preventDefault();pmNext();return true}
    if(e.key==='PageDown'||e.key==='PageUp'){var n=(+document.getElementById('pm-pg').value||1)+(e.key==='PageDown'?1:-1);e.preventDefault();pmGoPage(n);return true}
    if((e.ctrlKey||e.metaKey)&&(e.key==='p'||e.key==='פ')){e.preventDefault();pmPrint();return true}
    return false}

  /* ---------- הדפס מה שאני רואה ---------- */
  function pmPrint(){
    pmCommit();
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
  window.lkPrintMode={open:pmOpen,close:pmClose,state:function(){return {open:S.open,busy:S.busy,pages:S.pages.length,issues:S.issues.map(function(i){return {type:i.type,page:i.page,u:i.u,detail:i.detail,src:i.src}}),ms:S.lastMs,zoom:S.z,view:S.view}},
    relayout:pmRelayout,next:pmNext,go:pmGoPage,report:function(){return S.report}};
  })();
