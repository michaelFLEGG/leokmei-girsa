  /* =================== "בחר נוסח" - נוסחאות חלופיות למנהל (13.10.2026) ===================
     מוזרק לדף המסכת רק כשיש למסכת קובץ data/alts/<slug>.json, וגלוי רק במצב מנהל.
     כל נקודה: פסקה שפורסם בה נוסח אחד מבין כמה נוסחים שונים באמת, מתויגים לפי סוג ההכרעה.
     סימון עדין בשוליים (שכבה צפה, לא תופס מקום בשורה); לחיצה פותחת חלונית ליד הקטע, בלי להסתיר אותו.
     בחירה = עריכת מנהל רגילה (אותו נתיב של הצעות התיקון): מתפרסמת בפרסום המרוכז הקיים, ונכתבת לוורד בקליטה הבאה.
     כל בחירה נרשמת ביומן ההכרעות בנקודת הקליטה (/alt), ממנו לומד המנוע. */
  (function(){
  var AL=window.__ALTS||null;
  if(!AL||!AL.items||!AL.items.length)return;
  var NIK=/[֑-ׇ]/g;
  function nrm(s){return String(s||'').replace(/[⟦⟧]/g,'').replace(NIK,'').replace(/[\s ]+/g,' ').replace(/[^א-ת0-9 ]/g,'').trim()}
  function ge(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
  function plainOf(t){return String(t||'').replace(/[⟦⟧]/g,'')}
  function htmlOfText(t){
    var o='',parts=String(t||'').split(/(⟦[^⟧]*⟧)/);
    parts.forEach(function(p){
      if(p.charAt(0)==='⟦'&&p.charAt(p.length-1)==='⟧'){o+='<i class="hs">'+ge(p.slice(1,-1))+'</i>'}
      else o+=ge(p)});
    return o}
  function adm(){return typeof isAdmin==='function'&&isAdmin()}
  function lsGet(k,d){try{var v=localStorage.getItem(k);return v===null?d:v}catch(e){return d}}
  function lsSet(k,v){try{localStorage.setItem(k,v)}catch(e){}}
  var DKEY='lg-alt-dec-'+AL.slug;
  var DEC={};try{DEC=JSON.parse(lsGet(DKEY,'{}'))||{}}catch(e){DEC={}}
  var byId={};AL.items.forEach(function(it){byId[it.id]=it;it.vn=it.variants.map(function(v){return nrm(v.text)})});

  var sty=document.createElement('style');
  sty.textContent=
   '#alml{position:fixed;left:0;top:0;width:0;height:0;z-index:6;pointer-events:none}'+
   '.alm{position:fixed;pointer-events:auto;width:18px;height:18px;padding:0;border-radius:50%;border:1px solid #b9a56a;background:rgba(255,253,245,.92);color:#7a5a14;font:700 11px/16px Vilna,serif;text-align:center;cursor:pointer;opacity:.78}'+
   '.alm:hover,.alm.on{opacity:1;background:#f4e7bd}'+
   '.alm.dn{border-color:#5a8a4a;color:#3d6b2f;background:rgba(236,245,231,.95)}'+
   'body:not(.adm) .alm,body:not(.adm) #altpop,body:not(.adm) #altpg{display:none!important}'+
   '#altpop{position:fixed;z-index:31;direction:rtl;background:var(--paper,#fbf8f1);border:1px solid #c9bfa6;border-radius:9px;box-shadow:0 8px 28px rgba(0,0,0,.26);padding:.55em .7em;font-size:15px;line-height:1.55;color:#2b2620;display:none;max-width:min(46em,96vw)}'+
   '#altpop.open{display:block}'+
   '#altpop .alh{display:flex;justify-content:space-between;align-items:center;font-weight:700;color:#7a5a14;margin-bottom:.4em}'+
   '#altpop .alh button{border:0;background:none;font-size:20px;cursor:pointer;color:#7a6f58}'+
   '#altpop .alc{display:flex;gap:.6em;align-items:stretch}'+
   '#altpop .alv{flex:1 1 0;min-width:0;border:1px solid #d8cfb8;border-radius:7px;padding:.45em .55em;background:#fffdf7;display:flex;flex-direction:column;gap:.35em}'+
   '#altpop .alv.cur{border-color:#5a8a4a;background:#f1f8ed}'+
   '#altpop .alt{font-size:.82em;font-weight:700;color:#5a4a1e}'+
   '#altpop .alx{flex:1 1 auto;white-space:pre-wrap;font-size:.98em}'+
   '#altpop .alx i.hs{font-size:.82em;color:#4a4137}'+
   '#altpop .alb{display:flex;gap:.4em;flex-wrap:wrap}'+
   '#altpop button.b{font:inherit;font-size:.88em;padding:.12em .7em;border:1px solid #b9a56a;border-radius:5px;background:#fff;cursor:pointer;min-height:28px}'+
   '#altpop button.go{background:#c9a24a;border-color:#a98a36}'+
   '#altpop button[disabled]{opacity:.55;cursor:default}'+
   '#altpop textarea{width:100%;box-sizing:border-box;font:inherit;min-height:5.5em;direction:rtl;border:1px solid #c9bfa6;border-radius:4px;padding:.3em .4em}'+
   '#altpop .aln{font-size:.78em;color:#7a6f58;margin-top:.35em}'+
   '@media (max-width:760px){#altpop{left:6px!important;right:6px!important;top:auto!important;bottom:6px;max-width:none;max-height:70vh;overflow:auto}#altpop .alc{flex-direction:column}}'+
   '@media print{.alm,#alml,#altpop,#altpg{display:none!important}}'+
   '#altpg .alr{border-top:1px solid #eadfc2;padding:.5em 0}'+
   '#altpg .alr.dn{opacity:.7}'+
   '#altpg .alr .alg{font-size:.8em;color:#7a5a14;font-weight:700}'+
   '#altpg .alr .als{font-size:.95em;margin:.15em 0}'+
   '#altpg .alr button{font:inherit;font-size:.88em;padding:.1em .7em;border:1px solid #b9a56a;border-radius:5px;background:#fff;cursor:pointer;min-height:28px}'+
   '#altpg .alnav{display:flex;gap:.5em;align-items:center;margin:.4em 0}';
  document.head.appendChild(sty);

  /* ---- איתור הפסקה של כל נקודה: לפי הטקסט המנורמל של אחד הנוסחים ---- */
  var LOC={};     /* id -> {s (שורת נתונים), el} */
  /* (26.10.2026) האיתור נשמר לפי גרסת הנתונים (DV): בעבר רץ כל 0.9 שניות על כל מקומות המסכת
     (נרמול של כל שורה), גם כשדבר לא השתנה. האלמנט שבדף נשלף מחדש רק כשהקודם כבר אינו בדף. */
  var LOCV=-1,LOCS=null;
  function locateAll(){
    var S;try{S=slotsFull()}catch(e){return}
    if(S!==LOCS||LOCV!==(typeof DV!=='undefined'?DV:0)){
      LOCS=S;LOCV=typeof DV!=='undefined'?DV:0;LOC={};
      var by={};S.forEach(function(s){by[nrm(s.t)]=s});
      AL.items.forEach(function(it){
        var s=null;
        for(var i=0;i<it.vn.length&&!s;i++)s=by[it.vn[i]]||null;
        if(s)LOC[it.id]={s:s,el:null}})}
    var f=document.getElementById('flow');
    Object.keys(LOC).forEach(function(id){var l=LOC[id];
      if(!l.el||!l.el.isConnected)l.el=f?f.querySelector('[data-ek="'+l.s.k+'"]'):null})}
  function curIndex(it){
    var l=LOC[it.id];if(!l)return -1;var n=nrm(l.s.t);
    var ed=null;try{ed=ED.find(function(x){return x.k===l.s.k})}catch(e){}
    if(ed)n=nrm(ed.now);
    for(var i=0;i<it.vn.length;i++)if(it.vn[i]===n)return i;
    return -1}

  /* ---- שכבת הסימונים (שוליים) ---- */
  function layerEl(){var l=document.getElementById('alml');
    if(!l){l=document.createElement('div');l.id='alml';document.body.appendChild(l)}return l}
  var LQ=0;
  function layerSoon(){if(LQ)return;LQ=requestAnimationFrame(function(){LQ=0;layer()})}
  function layer(){
    var L=layerEl(),f=document.getElementById('flow');
    if(!f||!adm()){L.innerHTML='';return}
    if((typeof BOOK!=='undefined'&&BOOK)||(typeof PRINTING!=='undefined'&&PRINTING)){L.innerHTML='';return}
    /* בזמן סקירה (bk-on) סימני הנוסחאות אינם מצוירים: לכל אחד קריאת מיקום אחרי כל גלילה */
    if(document.body.classList.contains('bk-on')){if(L.firstChild)L.innerHTML='';return}
    locateAll();
    var fr=f.getBoundingClientRect(),have={};
    [].forEach.call(L.children,function(x){have[x.getAttribute('data-id')]=x});
    var seen={};
    AL.items.forEach(function(it){
      var l=LOC[it.id];if(!l||!l.el)return;
      var b=l.el.getBoundingClientRect();
      if(!b.height||b.bottom<fr.top||b.top>fr.bottom){return}
      seen[it.id]=1;
      var el=have[it.id];
      if(!el){el=document.createElement('button');el.type='button';el.className='alm';el.setAttribute('data-id',it.id);
        el.textContent='נ';el.setAttribute('title','נוסחאות לבחירה: '+it.variants.length+' נוסחים');
        L.appendChild(el);have[it.id]=el}
      el.classList.toggle('dn',!!DEC[it.id]);
      /* בשוליים: מחוץ לשדה הטקסט, בצד שמאל של הפסקה (בעברית הטקסט נקרא מימין) */
      var left=Math.max(2,Math.round(b.left-24))+'px',top=Math.round(b.top+2)+'px';
      if(el.style.left!==left)el.style.left=left;if(el.style.top!==top)el.style.top=top});
    [].forEach.call(L.children,function(x){if(!seen[x.getAttribute('data-id')])x.remove()})}
  window.altLayer=layer;
  /* בדיקת שלמות (למנהל): כמה נקודות אותרו בטקסט הנוכחי, ואילו לא */
  window.altStat=function(){locateAll();
    var miss=[];AL.items.forEach(function(it){if(!LOC[it.id])miss.push(it.id)});
    return {total:AL.items.length,found:AL.items.length-miss.length,missing:miss}};
  addEventListener('resize',layerSoon);
  document.addEventListener('scroll',layerSoon,true);
  document.addEventListener('lg-dv',layerSoon);
  /* גיבוי לתזוזות שאינן גלילה (גופנים, פריסת הזנב): קריאת מיקום של הנקודות שבמסך בלבד */
  setInterval(function(){if(!document.hidden&&!document.body.classList.contains('bk-on')&&adm()&&document.getElementById('flow'))layer()},1500);

  /* ---- החלונית ---- */
  var OPEN=null,EDITV=null;
  function popEl(){var p=document.getElementById('altpop');
    if(!p){p=document.createElement('div');p.id='altpop';document.body.appendChild(p)}return p}
  function drawPop(){
    var it=byId[OPEN];if(!it)return;
    var p=popEl(),ci=curIndex(it),h='';
    h+='<div class="alh"><span>נוסחאות לבחירה'+(it.daf?' · דף '+ge(it.daf):'')+'</span><button type="button" aria-label="סגור" onclick="altClose()">×</button></div><div class="alc">';
    it.variants.forEach(function(v,i){
      var cur=(i===ci);
      h+='<div class="alv'+(cur?' cur':'')+'"><div class="alt">'+ge(v.tag||('נוסח '+(i+1)))+(cur?' · מוצג כעת':'')+(v.k===it.pub0?' · כפי שפורסם':'')+'</div>'+
         '<div class="alx">'+htmlOfText(v.text)+'</div>'+
         '<div class="alb"><button type="button" class="b go" data-v="'+i+'" onclick="altPick(this)"'+(cur?' disabled':'')+'>בחר נוסח זה</button>'+
         '<button type="button" class="b" data-v="'+i+'" onclick="altEdit(this)">שלב / ערוך</button></div></div>'});
    h+='</div>';
    if(EDITV!==null){
      var src=it.variants[EDITV];
      h+='<div class="aln">עריכה חופשית (מותר להשאיר מילות הסבר בין ⟦ ⟧):</div><textarea id="alted">'+ge(src?src.text:'')+'</textarea>'+
         '<div class="alb"><button type="button" class="b go" onclick="altPickEdited()">בחר את הנוסח שערכתי</button><button type="button" class="b" onclick="altEditCancel()">ביטול</button></div>'}
    if(DEC[it.id])h+='<div class="aln">הוכרע ב-'+ge(new Date(DEC[it.id].at).toLocaleDateString('he-IL'))+(DEC[it.id].edited?' (בעריכה)':'')+'. אפשר לבחור שוב.</div>';
    p.innerHTML=h}
  function placePop(){
    var it=byId[OPEN],l=it&&LOC[it.id],p=popEl();
    p.classList.add('open');
    if(innerWidth<=760){p.style.left='';p.style.top='';return}
    var r=l&&l.el?l.el.getBoundingClientRect():{left:innerWidth/2,right:innerWidth/2,top:100,bottom:140};
    var w=p.offsetWidth,hh=p.offsetHeight;
    /* ליד הקטע: בצד שיש בו יותר מקום, ובלי להסתיר את הפסקה עצמה */
    var spaceL=r.left,spaceR=innerWidth-r.right,left,top=Math.min(Math.max(8,r.top-8),Math.max(8,innerHeight-hh-8));
    if(spaceL>=w+30)left=r.left-w-30;
    else if(spaceR>=w+10)left=r.right+10;
    else {left=Math.max(8,(innerWidth-w)/2);top=r.bottom+8;if(top+hh>innerHeight-8)top=Math.max(8,r.top-hh-8)}
    p.style.left=Math.round(left)+'px';p.style.top=Math.round(top)+'px'}
  function openPop(id){
    OPEN=id;EDITV=null;locateAll();drawPop();
    var p=popEl();p.classList.add('open');placePop();
    document.querySelectorAll('.alm').forEach(function(x){x.classList.toggle('on',x.getAttribute('data-id')===id)})}
  window.altClose=function(){var p=document.getElementById('altpop');if(p)p.classList.remove('open');OPEN=null;EDITV=null;
    document.querySelectorAll('.alm.on').forEach(function(x){x.classList.remove('on')})};
  document.addEventListener('click',function(ev){
    var m=ev.target.closest&&ev.target.closest('.alm');
    if(m){ev.preventDefault();ev.stopPropagation();openPop(m.getAttribute('data-id'));return}
    var pop=document.getElementById('altpop');
    if(pop&&pop.classList.contains('open')&&!ev.target.closest('#altpop,#altgo,#altpg'))altClose()},true);
  document.addEventListener('keydown',function(ev){if(ev.key==='Escape')altClose()});

  /* ---- בחירה: עריכת מנהל רגילה, באותו נתיב של הצעות התיקון ---- */
  function applyText(it,text,edited,vi){
    locateAll();
    var l=LOC[it.id];
    if(!l){if(typeof toast==='function')toast('הפסקה לא אותרה בטקסט הנוכחי (אולי נערכה). רענן ונסה שוב.',5000);return false}
    var s=l.s,old=ED.find(function(x){return x.k===s.k});
    var curT=old?old.now:s.t,curH=old?(old.nowH!==undefined?old.nowH:esc(old.now)):s.h;
    var wasT=old?old.was:s.t,wasH=old?(old.wasH!==undefined?old.wasH:s.h):s.h;
    var nowT=plainOf(text).trim(),nowH=htmlOfText(text.trim());
    if(!nowT){if(typeof toast==='function')toast('הנוסח ריק.');return false}
    if(/[–—]/.test(nowT)){if(typeof toast==='function')toast('בנוסח יש מקף ארוך (– או —). יש להשתמש במקף רגיל.',5000);return false}
    if(nrm(nowT)===nrm(curT)&&nowT===curT){return true}
    var cls=(s.c||'').split(' ').filter(function(c){return PCLS.indexOf(c)>-1}).join(' ');
    var el=l.el;
    var edit={k:s.k,was:wasT,now:nowT,wasH:wasH,nowH:nowH,wasP:old?old.wasP:cls,daf:s.daf,
              ctx:el&&typeof ctxOf==='function'?ctxOf(el):{b:'',a:''},t:Date.now(),pub:0,by:'בחירת נוסח'};
    if(old&&old.ps!==undefined){edit.ps=old.ps;edit.psw=old.psw}
    if(old)ED=ED.filter(function(x){return x!==old});
    ED.push(edit);saveED();applyTextNow(edit);drawEd();pubSoon();syncSoon();
    return true}
  function logDec(it,vi,text,edited){
    var rec={id:it.id,v:vi,tag:vi>=0?(it.variants[vi].tag||''):'ערוך',text:plainOf(text),edited:!!edited,at:Date.now()};
    DEC[it.id]=rec;lsSet(DKEY,JSON.stringify(DEC));
    if(typeof api==='function'){
      api('/alt',{method:'POST',body:JSON.stringify({slug:AL.slug,id:it.id,v:vi,tag:rec.tag,txt:rec.text,edited:rec.edited,variants:it.variants.map(function(x){return {t:x.tag,x:plainOf(x.text)}}),daf:it.daf||''})}).catch(function(){})}}
  window.altPick=function(b){
    var it=byId[OPEN];if(!it)return;var vi=+b.getAttribute('data-v'),v=it.variants[vi];if(!v)return;
    if(applyText(it,v.text,false,vi)){logDec(it,vi,v.text,false);
      if(typeof toast==='function')toast('הנוסח נבחר. הוא מוצג מיד, ויתפרסם בפרסום המרוכז ויכנס לוורד בקליטה הבאה.',4500);
      layer();drawPop();placePop();altPgDraw()}};
  window.altEdit=function(b){var it=byId[OPEN];if(!it)return;EDITV=+b.getAttribute('data-v');drawPop();placePop();
    var t=document.getElementById('alted');if(t)t.focus()};
  window.altEditCancel=function(){EDITV=null;drawPop();placePop()};
  window.altPickEdited=function(){
    var it=byId[OPEN],t=document.getElementById('alted');if(!it||!t)return;
    var txt=t.value.trim();if(!txt)return;
    var from=EDITV;
    if(applyText(it,txt,true,from)){logDec(it,-1,txt,true);
      if(typeof toast==='function')toast('הנוסח שערכת נבחר ויתפרסם.',4000);
      EDITV=null;layer();drawPop();placePop();altPgDraw()}};

  /* ---- דף מרוכז "נוסחאות לבחירה" (פאנל) ---- */
  function pgEnsure(){
    if(document.getElementById('altpg'))return;
    var p=document.createElement('div');p.className='panel';p.id='altpg';
    p.innerHTML='<button class="x" onclick="panel(&quot;altpg&quot;)">×</button><h3>נוסחאות לבחירה</h3><div id="altpgb"></div>';
    document.body.appendChild(p)}
  function altPgDraw(){
    var b=document.getElementById('altpgb');if(!b)return;
    var open=0,done=0;AL.items.forEach(function(it){if(DEC[it.id])done++;else open++});
    var h='<div class="alnav"><b>'+open+'</b> פתוחות · <b>'+done+'</b> הוכרעו · מתוך '+AL.items.length+'</div>'+
          '<div class="aln">הנוסח שפורסם נשאר אם לא תבחר. בחירה מחליפה מיד את הנוסח באתר, ונכתבת לוורד בעקוב אחר שינויים בקליטה הבאה.</div>';
    var cur='';
    AL.items.forEach(function(it,i){
      if(it.daf!==cur){cur=it.daf;h+='<h4 style="margin:.8em 0 .1em;color:#7a5a14">דף '+ge(cur||'')+'</h4>'}
      var ci=curIndex(it);
      h+='<div class="alr'+(DEC[it.id]?' dn':'')+'"><div class="alg">'+it.variants.map(function(v){return ge(v.tag||'')}).join(' · ')+(DEC[it.id]?' · הוכרע':'')+'</div>'+
         '<div class="als">'+ge(plainOf((it.variants[ci>=0?ci:0]||{}).text).slice(0,150))+'</div>'+
         '<button type="button" data-id="'+ge(it.id)+'" onclick="altGo(this.getAttribute(\'data-id\'))">הצג וקבע</button></div>'});
    b.innerHTML=h}
  window.altGo=function(id){
    var it=byId[id];if(!it)return;
    var pi=-1;for(var i=0;i<D.pages.length;i++)if(D.pages[i].daf===it.daf||D.pages[i].daf===(it.daf+'.')||D.pages[i].daf===(it.daf+':')){pi=i;break}
    locateAll();
    var l=LOC[id];
    if(l&&l.s&&typeof jump==='function'){jump(l.s.pi,l.s.id)}
    else if(pi>=0&&typeof toDaf==='function')toDaf(pi);
    setTimeout(function(){layer();openPop(id)},260)};
  window.altPanel=function(){pgEnsure();altPgDraw();var p=document.getElementById('altpg');if(p&&!p.classList.contains('open'))panel('altpg')};
  /* סימון לאחר כל רינדור: ה-flow נבנה מחדש בעת מעבר בין דפים */
  window.altMark=layerSoon;
  window.altDecided=function(id){return !!DEC[id]};   /* סקירה (13.10.2026): חלונית ההערות מציגה את הנקודות כסוג "בחר נוסח" */
  setTimeout(layerSoon,400);
  })();
