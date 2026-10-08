  /* =================== צורת הדף ===================
     מוזרק לדף המסכת רק כשהמסכת במניפסט (site/tzura/manifest.json). מסכת בלי צורת הדף: אין קוד, אין כפתור.
     הנתונים הציבוריים: tzura/<slug>/<f>.json = קואורדינטות בלבד. התמונות אינן בדף ואינן במאגר:
     נמשכות מהשרת בכתובת חתומה קצרת-תוקף, ומצוירות ל-canvas (אין תמונה לשמירה, אין קובץ להורדה).
     עקרון: לא מציירים דיוק שאינו קיים. אין מיקום בטוח - מעמעמים רק את שולי הדף ומציגים "מיקום משוער". */
  (function(){
  var TZ_MAN=window.__TZMAN||null;
  if(!TZ_MAN)return;
  var TZ_API='https://leokmei-suggest.m7654301.workers.dev';
  var TZ_LOCAL=(location.hostname==='localhost'||location.hostname==='127.0.0.1');
  var TZ_IMG=TZ_LOCAL?'/tzimg/':TZ_API+'/tz/img/';
  var tzSides=TZ_MAN.sides,tzIdx={};
  tzSides.forEach(function(s,i){tzIdx[s.daf]=i});
  function tzGet(k,d){try{var v=localStorage.getItem(k);return v===null?d:v}catch(e){return d}}
  function tzSet(k,v){try{localStorage.setItem(k,v)}catch(e){}}
  var TZ={open:false,i:-1,ref:'',track:tzGet('tz-track','1')!=='0',inten:tzGet('tz-int','mid'),style:tzGet('tz-style','dim'),
          zoom:+tzGet('tz-zoom','1')||1,data:null,img:null,imgKind:'',token:null,tokenAt:0};
  var tzCache={};      /* f -> json הנתונים */
  var tzBmp={};        /* f.kind -> ImageBitmap */
  var tzSty=document.createElement('style');
  tzSty.textContent=
   '#tzl{position:fixed;left:0;top:0;width:0;height:0;z-index:5;pointer-events:none}'+
   '#tzl .tzb{position:fixed;pointer-events:auto;user-select:none;-webkit-user-select:none;display:flex;align-items:center;justify-content:center;width:28px;height:28px;padding:0;margin:0;background:var(--sheet);border:1px solid var(--line);color:var(--blue);border-radius:8px;cursor:pointer;opacity:0;transition:opacity .15s,background .15s;font:600 15px/1 "VilnaG","Vilna",serif}'+
   '#tzl .tzb.hot,#tzl .tzb:hover,#tzl .tzb:focus-visible{opacity:1}'+
   '#tzl .tzb:hover,#tzl .tzb:focus-visible{background:var(--blue-soft);border-color:var(--blue)}'+
   '@media (hover:none){#tzl .tzb{display:none}}'+
   'body.srcoff #tzl{display:none}'+
   '.tzx{position:fixed;z-index:12;background:var(--paper);display:flex;flex-direction:column;font-size:15px;box-shadow:2px 0 18px rgba(0,0,0,.22);-webkit-user-select:none;user-select:none}'+
   '.tzx.split{left:0;top:var(--barH,52px);bottom:0;width:var(--tzw,46vw)}'+
   '.tzx.full{left:0;right:0;top:0;bottom:0}'+
   'body.tzsplit .flow{width:calc(100vw - var(--tzw,46vw));margin-left:auto}'+
   '.tzhd{display:flex;flex-wrap:wrap;gap:6px 8px;align-items:center;padding:7px 12px;background:#2b2620;color:#f1ead9;font-size:14px;flex:0 0 auto}'+
   '.tzhd b{font-family:"VilnaG","Vilna",serif;font-size:17px;font-weight:400}'+
   '.tzhd .sp{flex:1}'+
   '.tzhd button,.tzhd select{font:inherit;font-size:13px;background:#4a4137;color:#f1ead9;border:0;border-radius:4px;padding:3px 10px;cursor:pointer;min-height:28px}'+
   '.tzhd button.on{background:var(--gold);color:#2b2620}'+
   '.tzbody{flex:1 1 auto;overflow-y:scroll;overflow-x:auto;background:#e9e3d3;position:relative;touch-action:pan-x pan-y}'+
   '.tzbody canvas{display:block;margin:0 auto;-webkit-touch-callout:none}'+
   '.tzmsg{padding:30px;text-align:center;color:#6e6350}'+
   '.tzft{flex:0 0 auto;padding:5px 12px;font-size:11.5px;color:#8a7d66;background:#f3eee2;border-top:1px solid #e0d8c4;text-align:center}'+
   '.tzapx{position:absolute;top:6px;right:8px;background:rgba(43,38,32,.78);color:#f1ead9;font-size:12px;padding:2px 9px;border-radius:10px;pointer-events:none}'+
   '.tzdrag{position:absolute;top:0;bottom:0;right:-12px;width:24px;cursor:col-resize;z-index:12;touch-action:none}'+
   '.tzdrag::after{content:"";position:absolute;top:0;bottom:0;left:10px;width:4px;background:rgba(201,162,74,.55);border-radius:2px}'+
   '@media screen and (max-width:760px){.tzx.split{left:0;right:0;top:auto;bottom:0;width:auto;height:62vh}body.tzsplit .flow{width:auto;margin-left:0}}'+
   '@media print{.tzx,#tzl{display:none!important}}';
  document.head.appendChild(tzSty);
  var tzL=document.createElement('div');tzL.id='tzl';tzL.setAttribute('aria-hidden','true');document.body.appendChild(tzL);

  /* שם הצד בעברית: "ברכות · דף ב עמוד א" */
  function tzTitle(i){
    var k=tzSides[i].k,m=/^([א-ת]+)([.:])$/.exec(k);
    var nm=TZ_MAN.name||'';
    return nm+' · דף '+(m?m[1]:k)+' עמוד '+(m&&m[2]===':'?'ב':'א')}
  function tzSideOf(ref){var d=refDaf(ref);return d&&tzIdx.hasOwnProperty(d[0])?tzIdx[d[0]]:-1}

  /* ---- הכפתור: ליד "מקור", מאותה שכבה ובאותו אופן ---- */
  var TZPOOL=new Map();
  function tzLayerNow(){
    var off=BOOK||PRINTING;if(off||typeof SRCPOOL==='undefined')return;
    var seen=new Set();
    SRCPOOL.forEach(function(e,k){
      var ref=k.split('|')[0];if(tzSideOf(ref)<0||e.style.display==='none')return;
      seen.add(k);
      var b=TZPOOL.get(k);
      if(!b){b=document.createElement('button');b.className='tzb';b.type='button';b.textContent='צ';b.tabIndex=-1;
        b.setAttribute('aria-label','צורת הדף');b.title='צורת הדף (Alt+צ)';
        b.addEventListener('mousedown',function(ev){ev.preventDefault()});
        b.addEventListener('click',function(){tzOpen(ref)});
        tzL.appendChild(b);TZPOOL.set(k,b)}
      var tight=e.classList.contains('tight');
      var l=parseFloat(e.style.left)||0;
      b.classList.toggle('hot',e.classList.contains('hot'));
      b.style.left=Math.round(tight?l+32:l-32)+'px';
      b.style.top=e.style.top;b.style.display=''});
    TZPOOL.forEach(function(b,k){if(!seen.has(k)){b.remove();TZPOOL.delete(k)}})}
  var _sln=srcLayerNow;
  srcLayerNow=function(){_sln.apply(this,arguments);tzLayerNow()};
  document.addEventListener('mouseover',function(ev){
    var r=ev.target.closest&&ev.target.closest('.row[data-ref]');var key=r?r.dataset.ref+'|'+r.id:null;
    TZPOOL.forEach(function(b,k){b.classList.toggle('hot',k===key)})});

  /* ---- נתונים ותמונות ---- */
  function tzJson(i){
    var f=tzSides[i].f;
    if(tzCache[f])return Promise.resolve(tzCache[f]);
    return fetch('tzura/'+SLUG+'/'+f+'.json').then(function(r){if(!r.ok)throw new Error(r.status);return r.json()}).then(function(j){tzCache[f]=j;return j})}
  function tzTok(){
    if(TZ_LOCAL)return Promise.resolve('');
    if(TZ.token&&Date.now()-TZ.tokenAt<240000)return Promise.resolve(TZ.token);
    return fetch(TZ_API+'/tz/tok').then(function(r){if(!r.ok)throw new Error(r.status);return r.json()}).then(function(j){TZ.token=j.t;TZ.tokenAt=Date.now();return j.t})}
  function tzImg(i,kind){
    var f=tzSides[i].f,id=f+'.'+kind;
    if(tzBmp[id])return Promise.resolve(tzBmp[id]);
    return tzTok().then(function(t){
      return fetch(TZ_IMG+SLUG+'/'+f+'.'+kind+'.webp'+(t?'?t='+encodeURIComponent(t):''),{credentials:'omit'})})
      .then(function(r){if(!r.ok)throw new Error(r.status);return r.blob()})
      .then(function(b){return createImageBitmap(b)})
      .then(function(bm){tzBmp[id]=bm;
        var ks=Object.keys(tzBmp);if(ks.length>8){var old=ks[0];try{tzBmp[old].close()}catch(e){}delete tzBmp[old]}
        return bm})}

  /* ---- פתיחה וסגירה ---- */
  function tzBox(){return document.getElementById('tzx')}
  function tzOpen(ref){
    var i=tzSideOf(ref);if(i<0)return;
    if(typeof closeSrc==='function')closeSrc();
    barH();
    var box=tzBox();
    var mode=innerWidth<900?'full':'split';
    if(!box){box=document.createElement('div');box.id='tzx';box.tabIndex=0;document.body.appendChild(box)}
    box.className='tzx '+mode;
    var w=+tzGet('tz-w','46');if(!(w>=28&&w<=70))w=46;
    document.documentElement.style.setProperty('--tzw',w+'vw');
    document.body.classList.toggle('tzsplit',mode==='split');
    box.innerHTML=
      '<div class="tzhd"><b id="tztl"></b>'+
      '<button id="tzpv" title="הצד הקודם (Alt+חץ ימינה)">› קודם</button><button id="tznx" title="הצד הבא (Alt+חץ שמאלה)">הבא ‹</button>'+
      '<span class="sp"></span>'+
      '<button id="tzzo" title="הקטנה">−</button><button id="tzzi" title="הגדלה">+</button><button id="tzz1" title="התאמה לרוחב">התאם</button>'+
      '<button id="tztr" title="ההדגשה נעה עם השורה שבטקסט"></button>'+
      '<select id="tzin" title="עוצמת העמעום"><option value="off">ללא</option><option value="mid">עדין</option><option value="hi">בולט</option></select>'+
      '<select id="tzst" title="צורת ההדגשה"><option value="dim">עמעום</option><option value="line">קו זהב</option></select>'+
      '<button id="tzcl" title="סגירה (Esc)">×</button></div>'+
      '<div class="tzbody" id="tzbd"><div class="tzmsg">טוען את הדף…</div></div>'+
      '<div class="tzft">צורת הדף מוצגת כאן ברישיון פרטי, לצפייה בלבד ושלא למטרה מסחרית. הקובץ אינו ניתן להורדה.</div>'+
      (mode==='split'?'<div class="tzdrag" id="tzdr" title="גרור לשינוי הרוחב"></div>':'');
    document.getElementById('tzcl').onclick=tzClose;
    document.getElementById('tzpv').onclick=function(){tzStep(-1)};
    document.getElementById('tznx').onclick=function(){tzStep(1)};
    document.getElementById('tzzi').onclick=function(){tzZoom(TZ.zoom*1.25)};
    document.getElementById('tzzo').onclick=function(){tzZoom(TZ.zoom/1.25)};
    document.getElementById('tzz1').onclick=function(){tzZoom(1)};
    var tr=document.getElementById('tztr');
    function trUi(){tr.textContent=TZ.track?'מעקב: דלוק':'מעקב: כבוי';tr.classList.toggle('on',TZ.track)}
    trUi();tr.onclick=function(){TZ.track=!TZ.track;tzSet('tz-track',TZ.track?'1':'0');trUi();if(TZ.track)tzFollow()};
    var si=document.getElementById('tzin'),ss=document.getElementById('tzst');
    si.value=TZ.inten;ss.value=TZ.style;
    si.onchange=function(){TZ.inten=si.value;tzSet('tz-int',TZ.inten);tzDraw()};
    ss.onchange=function(){TZ.style=ss.value;tzSet('tz-style',TZ.style);tzDraw()};
    var bd=document.getElementById('tzbd');
    bd.addEventListener('contextmenu',function(e){e.preventDefault()});
    bd.addEventListener('dragstart',function(e){e.preventDefault()});
    bd.addEventListener('wheel',function(e){if(e.ctrlKey){e.preventDefault();tzZoom(TZ.zoom*(e.deltaY<0?1.12:1/1.12))}},{passive:false});
    tzPinch(bd);
    box.addEventListener('keydown',function(ev){
      if(ev.key==='Escape'){tzClose();ev.stopPropagation();ev.preventDefault();return}
      if(ev.altKey&&ev.key==='ArrowRight'){tzStep(-1);ev.preventDefault();ev.stopPropagation()}
      else if(ev.altKey&&ev.key==='ArrowLeft'){tzStep(1);ev.preventDefault();ev.stopPropagation()}
      else if(ev.key==='+'||ev.key==='='){tzZoom(TZ.zoom*1.25);ev.preventDefault()}
      else if(ev.key==='-'){tzZoom(TZ.zoom/1.25);ev.preventDefault()}
      ev.stopPropagation()});
    var dr=document.getElementById('tzdr');
    if(dr){dr.addEventListener('pointerdown',function(ev){
      ev.preventDefault();dr.setPointerCapture(ev.pointerId);
      var mv=function(e2){var p=Math.max(28,Math.min(70,e2.clientX/innerWidth*100));document.documentElement.style.setProperty('--tzw',p.toFixed(1)+'vw');tzDraw()};
      var up=function(e2){dr.removeEventListener('pointermove',mv);dr.removeEventListener('pointerup',up);
        var p=Math.max(28,Math.min(70,e2.clientX/innerWidth*100));tzSet('tz-w',p.toFixed(1));try{fitAnchors();squeezeRun()}catch(e){}tzDraw()};
      dr.addEventListener('pointermove',mv);dr.addEventListener('pointerup',up)})}
    TZ.open=true;TZ.ref=ref;
    tzShow(i,false);
    try{fitAnchors();squeezeRun()}catch(e){}}
  function tzClose(){var b=tzBox();if(b)b.remove();TZ.open=false;document.body.classList.remove('tzsplit');
    try{fitAnchors();squeezeRun()}catch(e){}}
  function tzStep(d){var i=TZ.i+d;if(i<0||i>=tzSides.length)return;TZ.track=false;tzSet('tz-track','0');
    var t=document.getElementById('tztr');if(t){t.textContent='מעקב: כבוי';t.classList.remove('on')}
    tzShow(i,true)}
  function tzShow(i,reset){
    TZ.i=i;TZ.data=null;TZ.img=null;TZ.imgKind='';
    var t=document.getElementById('tztl');if(t)t.textContent=tzTitle(i);
    var bd=document.getElementById('tzbd');
    if(reset&&bd)bd.scrollTop=0;
    Promise.all([tzJson(i),tzImg(i,'v')]).then(function(r){
      if(TZ.i!==i)return;TZ.data=r[0];TZ.img=r[1];TZ.imgKind='v';tzDraw(true);
      if(i+1<tzSides.length)tzJson(i+1).catch(function(){});
    }).catch(function(e){
      var bd2=document.getElementById('tzbd');if(bd2)bd2.innerHTML='<div class="tzmsg">לא הצלחתי לטעון את הדף ('+esc(String(e.message||e))+').</div>'})}

  /* ---- ציור: התמונה, העמעום והמיקום ---- */
  function tzCover(ref){
    /* כל קטעי הגמרא שהיחידה מכסה: מקטע היחידה ועד שלפני ההפניה של היחידה הבאה */
    var out=new Set([ref]),k=refKey(ref);
    if(k===null||!TZ.data)return out;
    var L=refList(),at=L.indexOf(ref),nk=null;
    for(var j=at+1;j<L.length&&at>-1;j++){var x=refKey(L[j]);if(x!==null&&x>k){nk=x;break}}
    if(nk===null)nk=(Math.floor(k/1000)+1)*1000;
    Object.keys(TZ.data.segs).forEach(function(r){var x=refKey(r);if(x!==null&&x>=k&&x<nk)out.add(r)});
    return out}
  function tzRects(){
    /* מחזיר {rects:[[x0,y0,x1,y1]...], exact:true|false} במנות של 0..1 */
    var d=TZ.data;if(!d)return{rects:[],exact:false};
    var cov=tzCover(TZ.ref),rs=[],strong=false;
    cov.forEach(function(r){var s=d.segs[r];if(s&&s.c!=='weak'){s.l.forEach(function(l){rs.push(l)});strong=true}});
    /* חלק מן ההיקף עלול לשבת בצד אחר: אם הקטע שבראש היחידה אינו בצד הזה - אין מיקום, לא ממציאים */
    var own=d.segs[TZ.ref];
    if(!strong)return{rects:[],exact:false};
    return{rects:rs,exact:true,own:!!own}}
  var TZ_REDRAW=0,TZ_RETRY=0;
  function tzDraw(scrollTo){
    var bd=document.getElementById('tzbd');if(!bd||!TZ.img||!TZ.data)return;
    var d=TZ.data,ar=d.ar;
    if(bd.clientWidth<300){clearTimeout(TZ_RETRY);TZ_RETRY=setTimeout(function(){tzDraw(scrollTo)},120);return}
    var base=bd.clientWidth;
    var cssW=Math.round(base*TZ.zoom),cssH=Math.round(cssW/ar);
    var dpr=Math.min(window.devicePixelRatio||1,2);
    var pw=Math.min(Math.round(cssW*dpr),3000),ph=Math.round(pw/ar);
    var cv=bd.querySelector('canvas');
    if(!cv){bd.innerHTML='';cv=document.createElement('canvas');bd.appendChild(cv)}
    cv.style.width=cssW+'px';cv.style.height=cssH+'px';
    if(cv.width!==pw||cv.height!==ph){cv.width=pw;cv.height=ph}
    /* זום עמוק: מעבר לתמונה החדה, בטעינה ברקע */
    var want=(pw>1500)?'z':'v';
    if(want==='z'&&TZ.imgKind!=='z'){var i0=TZ.i;
      tzImg(i0,'z').then(function(bm){if(TZ.i===i0){TZ.img=bm;TZ.imgKind='z';tzDraw()}}).catch(function(){})}
    var ctx=cv.getContext('2d');
    ctx.setTransform(1,0,0,1,0,0);
    ctx.drawImage(TZ.img,0,0,pw,ph);
    var rr=tzRects(),exact=rr.exact;
    var A=TZ.inten==='off'?0:(TZ.inten==='hi'?0.62:0.35);
    var apx=bd.querySelector('.tzapx');
    if(apx)apx.remove();
    if(A>0||TZ.style==='line'){
      if(exact&&TZ.style==='dim'){
        /* שכבת עמעום על כל הדף, ובה "חור" רך סביב האזור */
        var m=document.createElement('canvas');m.width=pw;m.height=ph;var mc=m.getContext('2d');
        mc.fillStyle='rgba(38,32,22,'+A+')';mc.fillRect(0,0,pw,ph);
        mc.globalCompositeOperation='destination-out';
        var pad=0.0022*ph;
        rr.rects.forEach(function(r){
          var x0=r[0]*pw,y0=r[1]*ph,x1=r[2]*pw,y1=r[3]*ph;
          for(var s=4;s>=0;s--){var e=pad+s*0.0016*ph;mc.fillStyle='rgba(0,0,0,'+(s===0?1:0.22)+')';
            mc.fillRect(x0-e,y0-e,x1-x0+2*e,y1-y0+2*e)}});
        ctx.drawImage(m,0,0)}
      else if(exact&&TZ.style==='line'){
        var y0=1e9,y1=-1;rr.rects.forEach(function(r){y0=Math.min(y0,r[1]);y1=Math.max(y1,r[3])});
        ctx.fillStyle='#c9a24a';ctx.fillRect(Math.max(0,d.col[0]*pw-9),y0*ph-3,4,(y1-y0)*ph+6)}
      else{
        /* אין מיקום בטוח: עמעום עדין מאוד של מה שמחוץ לטור הגמרא, והודעה */
        var m2=document.createElement('canvas');m2.width=pw;m2.height=ph;var c2=m2.getContext('2d');
        c2.fillStyle='rgba(38,32,22,'+(A*0.35)+')';c2.fillRect(0,0,pw,ph);
        c2.globalCompositeOperation='destination-out';c2.fillStyle='#000';
        c2.fillRect(d.col[0]*pw-8,d.col[1]*ph-8,(d.col[2]-d.col[0])*pw+16,(d.col[3]-d.col[1])*ph+16);
        ctx.drawImage(m2,0,0);
        var n=document.createElement('div');n.className='tzapx';n.textContent='מיקום משוער: הטור כולו';bd.appendChild(n)}}
    /* סימן מים עדין, מצויר בבד עצמו */
    ctx.save();ctx.globalAlpha=0.07;ctx.fillStyle='#2b2620';ctx.font=Math.round(pw*0.05)+'px "VilnaG","Vilna",serif';
    ctx.textAlign='center';ctx.translate(pw*0.5,ph*0.5);ctx.rotate(-0.5);
    for(var q=-2;q<=2;q++)ctx.fillText('לאוקמי גירסא · leokmei.com',0,q*ph*0.28);
    ctx.restore();
    if(scrollTo!==false&&exact&&rr.rects.length){
      var ys=rr.rects.map(function(r){return r[1]}),ye=rr.rects.map(function(r){return r[3]});
      var cy=(Math.min.apply(null,ys)+Math.max.apply(null,ye))/2*cssH;
      bd.scrollTo({top:Math.max(0,cy-bd.clientHeight/2),behavior:scrollTo===true?'auto':'smooth'})}}
  function tzZoom(z){TZ.zoom=Math.max(1,Math.min(4,z));tzSet('tz-zoom',TZ.zoom.toFixed(2));tzDraw(false)}
  function tzPinch(el){
    var P=new Map(),d0=0,z0=1;
    el.addEventListener('pointerdown',function(e){P.set(e.pointerId,[e.clientX,e.clientY]);
      if(P.size===2){var a=Array.from(P.values());d0=Math.hypot(a[0][0]-a[1][0],a[0][1]-a[1][1]);z0=TZ.zoom}});
    el.addEventListener('pointermove',function(e){if(!P.has(e.pointerId))return;P.set(e.pointerId,[e.clientX,e.clientY]);
      if(P.size===2&&d0){var a=Array.from(P.values());var d=Math.hypot(a[0][0]-a[1][0],a[0][1]-a[1][1]);
        tzZoom(z0*d/d0);e.preventDefault()}});
    var up=function(e){P.delete(e.pointerId);if(P.size<2)d0=0};
    el.addEventListener('pointerup',up);el.addEventListener('pointercancel',up)}

  /* ---- מעקב אחרי השורה שבטקסט ---- */
  var TZ_FT=0;
  function tzFollow(){
    if(!TZ.open||!TZ.track)return;
    var r=curFlowRef();if(!r||r===TZ.ref)return;
    TZ.ref=r;var i=tzSideOf(r);
    if(i>=0&&i!==TZ.i)tzShow(i,false);else tzDraw(false)}
  document.addEventListener('DOMContentLoaded',function(){
    var f=document.getElementById('flow');if(!f)return;
    f.addEventListener('scroll',function(){clearTimeout(TZ_FT);TZ_FT=setTimeout(tzFollow,160)},{passive:true})});
  addEventListener('resize',function(){if(TZ.open)tzDraw(false)});

  /* ---- קיצור: Alt+צ פותח את צורת הדף לשורה שבמוקד ---- */
  document.addEventListener('keydown',function(ev){
    if(!(ev.altKey&&!ev.ctrlKey&&!ev.metaKey&&(ev.key==='צ'||ev.code==='KeyM')))return;
    if(TZ.open){tzClose();ev.preventDefault();return}
    var r=null;try{r=(typeof HOVER!=='undefined'&&HOVER&&HOVER.dataset&&HOVER.dataset.ref)||curFlowRef()}catch(e){r=curFlowRef()}
    if(r&&tzSideOf(r)>=0){tzOpen(r);ev.preventDefault()}});
  /* קישור עמוק: ‎#tz=<ref>‎ */
  document.addEventListener('DOMContentLoaded',function(){
    var m=/[#&]tz=([^&]+)/.exec(location.hash||'');if(m)setTimeout(function(){tzOpen(decodeURIComponent(m[1]))},900)});
  window.tzOpen=tzOpen;window.tzClose=tzClose;
  })();
