  /* =================== פרומפט 81 (23.11.2026): ראשי תיבות בנגיעה, ומצב "חזרה מהירה" ===================
     א. ראשי תיבות: נגיעה (טלפון) או ריחוף (מחשב) על ראשי תיבות בטקסט או בכותרת צד מציגה בבועה קטנה את הפתיחה.
        המקור: המילון של פרומפט 80 (site/abbr/<מסכת>.json, השדה at), ובו רק מופעים שנמצאה להם בהקשר הסוגיה פתיחה
        אחת בלבד. מופע שאינו שם - אין בועה. בלי שום שינוי בנראות הטקסט ובהדפסה (אין קו, אין צבע). המילון נטען רק
        בנגיעה הראשונה בטקסט, ולא בטעינת הדף. כבוי במצב עריכה, במצב דפוס ובמסגרת ההדפסה.
        זיהוי המופע: לפי שדה הנתונים (data-ek: u<id>.0 הוא u.a, u<id>.N הוא u.l[N-1]) ומספר המופע בו, באותו סדר כמו
        tools/abbr_build.py (a, w, ואז השורות). אם הטקסט בדף אינו תואם את הנתונים (עריכה חיה, שכבת ניקוד) - אין בועה.
     ב. "חזרה מהירה": כפתור אחד בסרגל מקפל את הדף כך שנראים רק המשנה (ד"ה ונושאי המשנה), כותרות הנושא, ד"ה
        המשנה וכותרות הצד. לחיצה על כותרת פותחת את הטקסט שמתחתיה; לחיצה נוספת על הכפתור מחזירה הכל. המצב נשמר
        במכשיר (lg-qr). "חזרתי על הפרק" נרשם במערכת הלומד כחזרה על כל עמודי הפרק (אירוע dn, how:'qr').
        תצוגה בלבד: אינו נוגע בנתונים, בוורד ובהדפסה (המחלקה html.qr חלה רק @media screen). */
  (function(){
  'use strict';
  var RQ=new URLSearchParams(location.search);
  if(RQ.get('print')==='1'||RQ.get('qr')==='1')return;
  var Dc=document,HE=Dc.documentElement;
  function rvEdit(){try{return (typeof EDIT!=='undefined'&&EDIT)||Dc.body.classList.contains('ed')||Dc.body.classList.contains('pmopen')}catch(e){return false}}
  function rvLs(k){try{return localStorage.getItem(k)}catch(e){return null}}
  function rvLsSet(k,v){try{if(v===null)localStorage.removeItem(k);else localStorage.setItem(k,v)}catch(e){}}
  function rvToast(m,ms){try{if(typeof toast==='function')toast(m,ms||3000)}catch(e){}}
  function rvIc(n){return '<svg class="ic" aria-hidden="true"><use href="#i-'+n+'"/></svg>'}

  /* ------------------------------------------------ סגנון (מסך בלבד) */
  var css=Dc.createElement('style');css.id='rvcss';
  css.textContent='@media screen{'+
    /* הבועה */
    '#abtip{position:fixed;z-index:60;pointer-events:none;max-width:16em;padding:.28em .7em;border-radius:7px;background:#2b2620;color:#fbf7ee;'+
      'font-family:Frank,"Frank Ruhl Libre",serif;font-size:15px;line-height:1.35;direction:rtl;box-shadow:0 2px 10px rgba(0,0,0,.18);opacity:0;'+
      'transform:translateY(3px);transition:opacity .12s,transform .12s}'+
    '#abtip.on{opacity:1;transform:none}'+
    '#abtip:after{content:"";position:absolute;top:100%;right:var(--ax,50%);margin-right:-5px;border:5px solid transparent;border-top-color:#2b2620}'+
    '#abtip.dn:after{top:auto;bottom:100%;border-top-color:transparent;border-bottom-color:#2b2620}'+
    /* חזרה מהירה: גוף הסוגיה מקופל. נשארות שורות שיש בהן כותרת צד או ציון דף (בלעדיו הניווט לדף אינו מוצא מקום) */
    'html.qr #flow .row.u:not(.qro)>.main{display:none}'+
    'html.qr #flow .row.u:not(.qro):not(:has(.anchor,.dafmark)){display:none}'+
    /* כותרת הצד עוברת לטור הטקסט, שורה לכל אחת, מתחת לכותרת הנושא (במסילה היו נערמות זו על זו: גובה שורתן אפס) */
    'html.qr #flow .row.u:not(.qro)>.rail{grid-column:2;grid-row:1;display:block;padding:0;direction:rtl;text-align:right;justify-self:stretch;width:auto}'+
    'html.qr #flow .row.u:not(.qro)>.rail>*{line-height:1.55}'+
    'html.qr #flow .row.u:not(.qro) .win{display:inline;text-align:right}html.qr #flow .row.u:not(.qro) .anchor{display:inline;text-align:right}'+
    'html.qr #flow .row.u:not(.qro) .dafmark{display:inline-block;transform:none;margin-inline-end:.7em}'+
    'html.qr #flow .row.u:not(.qro) .anchor{cursor:pointer}'+
    'html.qr #flow .row.u:not(.qro) .anchor:hover{color:var(--blue,#2d4f7c)}'+
    /* משנה: ד"ה (השורה הראשונה) ונושאי המשנה (p.nsc); שאר המשנה בלחיצה */
    'html.qr #flow .main.mishna:not(.qro)>p:not(:first-of-type):not(.nsc){display:none}'+
    'html.qr #flow .main.mishna:not(.qro){cursor:pointer}'+
    'html.qr #flow .row.nose>.main,html.qr #flow .row.dh>.main{cursor:pointer}'+
    'html.qr #flow .row.qrh>.main{position:relative}'+
    'html.qr #flow .row.qrh.qrop>.main:before{content:"";position:absolute;inset:-.1em -.4em;border-radius:6px;background:rgba(201,162,74,.10);pointer-events:none}'+
    /* שכבות צפות שנמדדות לפי מקום השורות - כבויות בזמן הקיפול */
    'html.qr #tsl,html.qr #srcl,html.qr .tsa,html.qr .tsfoot{display:none!important}'+
    'html.qr #flow .row{scroll-margin-top:84px}'+
    /* הכפתור בסרגל: סמל בלבד, הכיתוב בריחוף */
    '#qrbtn.on{background:rgba(201,162,74,.22);border-radius:8px}'+
    '#mqrbtn{background:none;border:0;color:inherit;padding:6px;display:flex;align-items:center}#mqrbtn .ic{width:20px;height:20px}#mqrbtn.on{color:#c9a24a}'+
    /* הרצועה בתחתית בזמן החזרה */
    '#qrbar{position:fixed;z-index:40;left:50%;transform:translateX(-50%);bottom:18px;display:none;align-items:center;gap:.6em;direction:rtl;'+
      'background:#fbf7ee;border:1px solid #d9cfb8;border-radius:999px;padding:.3em .5em .3em .9em;box-shadow:0 2px 12px rgba(0,0,0,.12);'+
      'font-family:Frank,"Frank Ruhl Libre",serif;font-size:15px;color:#2b2620;white-space:nowrap}'+
    'html.qr #qrbar{display:flex}'+
    '#qrbar b{font-weight:700}#qrbar button{font:inherit;border:1px solid #c9a24a;background:#fff;color:#2b2620;border-radius:999px;padding:.15em .8em;cursor:pointer}'+
    '#qrbar button.pri{background:#c9a24a;color:#fff;border-color:#c9a24a}#qrbar button:disabled{opacity:.55;cursor:default}'+
    '@media (max-width:760px){#qrbar{bottom:calc(var(--mbot,58px) + 12px);font-size:14px}}'+
    'html.dev-phone #qrbar{bottom:calc(var(--mbot,58px) + 12px)}'+
    '}@media print{#abtip,#qrbar{display:none!important}}';
  Dc.head.appendChild(css);

  /* =================================================== א. ראשי תיבות */
  var AB=null,ABload=null,UMAP=null;
  /* אותו ביטוי כמו ABBR ב-tools/abbr_build.py. נבנה מתוך מחרוזת: דפדפן ישן בלי lookbehind - פשוט אין בועות */
  var ABRE=null;try{ABRE=new RegExp('(?<![\\u05D0-\\u05EA"\'\\u05F3\\u05F4])([\\u05D0-\\u05EA]{1,4})["\\u05F4]([\\u05D0-\\u05EA]{1,2})(?![\\u05D0-\\u05EA"\'\\u05F3\\u05F4])','g')}catch(e){}
  function abLoad(){
    if(ABload)return ABload;
    ABload=fetch('abbr/'+SLUG+'.json',{cache:'force-cache'}).then(function(r){return r.ok?r.json():null}).then(function(j){AB=(j&&j.at)||{};return AB}).catch(function(){AB={};return AB});
    return ABload}
  function uMap(){if(UMAP)return UMAP;UMAP={};try{D.pages.forEach(function(p){p.units.forEach(function(u){UMAP[u.id]=u})})}catch(e){}return UMAP}
  var dec=Dc.createElement('textarea');
  function plain(h){dec.innerHTML=String(h||'').replace(/<[^>]+>/g,' ');return dec.value}
  function hits(t){var o=[],m;if(!ABRE)return o;ABRE.lastIndex=0;while((m=ABRE.exec(t))){o.push({a:m[1]+'"'+m[2],i:m.index,e:m.index+m[0].length})}return o}
  /* מקטעי הנתונים של יחידה, לפי הסדר של abbr_build: a, w, ואז השורות */
  function segs(u){var s=[];if(typeof u.a==='string')s.push(['0',u.a]);if(typeof u.w==='string')s.push(['w',u.w]);
    (u.l||[]).forEach(function(l,n){if(l&&l.length>1)s.push([String(n+1),l[1]])});return s}
  function caretAt(x,y){
    if(Dc.caretPositionFromPoint){var p=Dc.caretPositionFromPoint(x,y);return p?{n:p.offsetNode,o:p.offset}:null}
    if(Dc.caretRangeFromPoint){var r=Dc.caretRangeFromPoint(x,y);return r?{n:r.startContainer,o:r.startOffset}:null}
    return null}
  /* מה ראשי התיבות שתחת הנקודה (x,y), ומה פתיחתם בהקשר זה. null - אין בועה */
  function abFind(x,y){
    if(!AB||!ABRE)return null;
    var c=caretAt(x,y);if(!c||!c.n||c.n.nodeType!==3)return null;
    var el=c.n.parentNode,seg=el&&el.closest('[data-ek],.nsi');if(!seg||!seg.closest('#flow'))return null;
    var uid,sk;
    if(seg.classList.contains('nsi')){uid=+seg.getAttribute('data-nu');sk='0'}
    else{var m=/^u(\d+)\.(\w+)$/.exec(seg.getAttribute('data-ek')||'');if(!m)return null;uid=+m[1];sk=m[2]}
    var list=AB[String(uid)];if(!list||!list.length)return null;
    var u=uMap()[uid];if(!u)return null;
    /* טקסט המקטע בדף. ד"ה שצורפה אליו כותרת הנושא (span.nsi) - בלי הכותרת, שהיא יחידה אחרת */
    var ns=[],txt='',off=-1,w0=Dc.createTreeWalker(seg,NodeFilter.SHOW_TEXT),t0;
    while((t0=w0.nextNode())){if(seg!==t0.parentNode.closest('[data-ek],.nsi'))continue;
      if(t0===c.n)off=txt.length+c.o;ns.push([t0,txt.length]);txt+=t0.nodeValue}
    if(off<0)return null;
    var dh=hits(txt),k=-1;
    for(var i=0;i<dh.length;i++){if(off>=dh[i].i&&off<=dh[i].e){k=i;break}}
    if(k<0)return null;
    /* המופעים שבמקטעים הקודמים, ובדיקה שהמקטע הנוכחי בדף תואם את הנתונים */
    var S=segs(u),before={},ok=false;
    for(var j=0;j<S.length;j++){var hs=hits(plain(S[j][1]));
      if(S[j][0]===sk){if(hs.length!==dh.length)return null;
        for(var q=0;q<hs.length;q++)if(hs[q].a!==dh[q].a)return null;
        for(q=0;q<k;q++)before[hs[q].a]=(before[hs[q].a]||0)+1;ok=true;break}
      hs.forEach(function(h){before[h.a]=(before[h.a]||0)+1})}
    if(!ok)return null;
    var a=dh[k].a,n=before[a]||0,ex=null;
    for(i=0;i<list.length;i++){if(list[i][0]===a&&list[i][1]===n){ex=list[i][2];break}}
    if(!ex)return null;
    /* מקום ראשי התיבות במסך */
    var r2=Dc.createRange(),st=null,en=null;
    for(i=0;i<ns.length;i++){var L=ns[i][0].nodeValue.length,P=ns[i][1];
      if(!st&&P+L>dh[k].i)st=[ns[i][0],dh[k].i-P];
      if(st&&P+L>=dh[k].e){en=[ns[i][0],dh[k].e-P];break}}
    if(!st||!en)return null;
    try{r2.setStart(st[0],st[1]);r2.setEnd(en[0],en[1])}catch(e){return null}
    return {ex:ex,rect:r2.getBoundingClientRect(),key:uid+'|'+sk+'|'+k}}
  var tip=null,tipKey='';
  function tipShow(f){
    if(!tip){tip=Dc.createElement('div');tip.id='abtip';tip.setAttribute('role','tooltip');Dc.body.appendChild(tip)}
    if(tipKey===f.key&&tip.classList.contains('on'))return;
    tipKey=f.key;tip.textContent=f.ex;tip.classList.remove('on','dn');
    tip.style.left='0px';tip.style.top='0px';
    var R=f.rect,W=tip.offsetWidth,H=tip.offsetHeight,cx=R.left+R.width/2;
    var L=Math.max(6,Math.min(innerWidth-W-6,cx-W/2)),T=R.top-H-8,dn=false;
    if(T<60){T=R.bottom+8;dn=true}
    tip.style.left=L+'px';tip.style.top=T+'px';
    tip.style.setProperty('--ax',Math.max(8,Math.min(W-8,L+W-cx))+'px');
    if(dn)tip.classList.add('dn');
    requestAnimationFrame(function(){tip.classList.add('on')})}
  function tipHide(){if(tip&&tip.classList.contains('on')){tip.classList.remove('on')}tipKey=''}
  var hvT=0,hvX=0,hvY=0;
  function hvCheck(){hvT=0;if(rvEdit()){tipHide();return}
    if(!AB){abLoad().then(function(){hvCheck()});return}
    var f=abFind(hvX,hvY);if(f)tipShow(f);else tipHide()}
  var flowEl=Dc.getElementById('flow');
  if(flowEl&&ABRE){
    /* מחשב: ריחוף. הבדיקה רצה רק כשהעכבר עוצר (120ms), ורק על טקסט שיש בו גרשיים */
    flowEl.addEventListener('pointermove',function(e){
      if(e.pointerType!=='mouse')return;
      var t=e.target;if(!t||!(t.textContent||'').match(/["״]/)){if(tipKey)tipHide();return}
      hvX=e.clientX;hvY=e.clientY;if(hvT)clearTimeout(hvT);hvT=setTimeout(hvCheck,120)},{passive:true});
    flowEl.addEventListener('pointerleave',function(){if(hvT)clearTimeout(hvT);hvT=0;tipHide()},{passive:true});
    /* טלפון: נגיעה (בלי גרירה). נגיעה נוספת במקום אחר - הבועה נסגרת */
    var td=null;
    flowEl.addEventListener('pointerdown',function(e){if(e.pointerType==='mouse')return;td={x:e.clientX,y:e.clientY,t:Date.now()}},{passive:true});
    flowEl.addEventListener('pointerup',function(e){
      if(e.pointerType==='mouse'||!td)return;var s=td;td=null;
      if(Math.abs(e.clientX-s.x)>8||Math.abs(e.clientY-s.y)>8||Date.now()-s.t>600)return;
      if(rvEdit())return;
      hvX=e.clientX;hvY=e.clientY;
      var go=function(){var f=abFind(hvX,hvY);if(f){tipShow(f);clearTimeout(tipHide.t);tipHide.t=setTimeout(tipHide,4000)}else tipHide()};
      if(!AB)abLoad().then(go);else go()},{passive:true});
    addEventListener('scroll',function(){if(tipKey)tipHide()},{passive:true,capture:true});
  }

  /* =================================================== ב. חזרה מהירה */
  var QK='lg-qr',OPEN={},qrT0=0;
  function isHead(r){return r&&r.classList&&r.classList.contains('row')&&(r.classList.contains('nose')||r.classList.contains('dh')||
      r.classList.contains('perek-start')||r.classList.contains('perek-range')||r.classList.contains('hadran')||r.classList.contains('hatz')||
      !!r.querySelector(':scope>.main.mishna'))}
  function uidOf(r){var m=/^u(\d+)$/.exec(r&&r.id||'');return m?+m[1]:0}
  /* היחידות שמתחת לכותרת, עד הכותרת הבאה */
  function bodyRows(h){var o=[],r=h.nextElementSibling;while(r&&!isHead(r)){if(r.classList.contains('row')&&r.classList.contains('u'))o.push(r);r=r.nextElementSibling}return o}
  function applyOpen(){
    if(!flowEl)return;
    [].forEach.call(flowEl.querySelectorAll('.row.u'),function(r){r.classList.toggle('qro',!!OPEN[uidOf(r)])});
    [].forEach.call(flowEl.querySelectorAll('.main.mishna'),function(m){var r=m.closest('.row');m.classList.toggle('qro',!!OPEN['m'+uidOf(r)])});
    [].forEach.call(flowEl.querySelectorAll('.row'),function(r){if(!isHead(r)||!(r.classList.contains('nose')||r.classList.contains('dh')))return;
      r.classList.add('qrh');var b=bodyRows(r);r.classList.toggle('qrop',b.length>0&&b.every(function(x){return OPEN[uidOf(x)]}))})}
  /* השורה שבראש המסך, כדי שהמקום לא יזוז במעבר */
  function topRow(){
    if(!flowEl)return null;
    var R=flowEl.getBoundingClientRect(),y=Math.max(R.top,0)+90,x=R.left+R.width/2;
    var el=Dc.elementFromPoint(x,y),r=el&&el.closest&&el.closest('#flow .row');
    if(r)return r;
    var rows=flowEl.querySelectorAll('.row');for(var i=0;i<rows.length;i++){var b=rows[i].getBoundingClientRect();if(b.bottom>y)return rows[i]}return null}
  function visible(r){return r&&r.getClientRects().length>0}
  function keepPlace(r){
    if(!r)return;var t=r;
    while(t&&!visible(t))t=t.previousElementSibling;
    if(t)try{t.scrollIntoView({block:'start'})}catch(e){}}
  function curPerek(){
    var pi=-1;try{var c=LAMED.track.cur();if(c)pi=c.pi}catch(e){}
    if(pi<0){var r=topRow(),dm=null;
      /* לפי ציון הדף האחרון שלפני השורה שבראש המסך */
      var all=flowEl?flowEl.querySelectorAll('.dafmark'):[];for(var i=0;i<all.length;i++){if(r&&(r.compareDocumentPosition(all[i])&Node.DOCUMENT_POSITION_FOLLOWING)&&!r.contains(all[i]))break;dm=all[i]}
      if(dm)pi=+String(dm.id||'').slice(1)}
    if(pi<0||!D.pages[pi])return null;
    var per=D.pages[pi].perek||'',dafs=[];
    D.pages.forEach(function(p){if((p.perek||'')===per&&p.units&&p.units.length){var d=(p.daf||'').trim();if(d&&dafs.indexOf(d)<0)dafs.push(d)}});
    return {perek:per,dafs:dafs}}
  function qrBar(){
    var b=Dc.getElementById('qrbar');if(b)return b;
    b=Dc.createElement('div');b.id='qrbar';b.setAttribute('role','region');b.setAttribute('aria-label','חזרה מהירה');
    b.innerHTML='<b>חזרה מהירה</b><button type="button" class="pri" id="qrdone" title="רישום חזרה על כל עמודי הפרק">חזרתי על הפרק</button><button type="button" id="qrexit" title="חזרה לדף המלא">הצג הכל</button>';
    Dc.body.appendChild(b);
    b.querySelector('#qrexit').onclick=function(){qrSet(false)};
    b.querySelector('#qrdone').onclick=function(){
      var cp=curPerek(),btn=this;
      if(!cp||!cp.dafs.length){rvToast('לא נמצא הפרק שבמסך');return}
      if(typeof LAMED==='undefined'||!LAMED.put){rvToast('מערכת הלומד אינה זמינה כרגע');return}
      var now=Date.now(),ms=Math.round(Math.min(now-(qrT0||now),3600000)/cp.dafs.length);
      try{cp.dafs.forEach(function(d){LAMED.put({k:'dn',s:SLUG,d:d,how:'qr',ms:ms,t:now},true)});LAMED.notify()}catch(e){rvToast('הרישום לא הצליח');return}
      rvToast('החזרה על '+(cp.perek||'הפרק')+' נרשמה ('+cp.dafs.length+' עמודים)',3600);
      btn.disabled=true;btn.textContent='נרשם';setTimeout(function(){btn.disabled=false;btn.textContent='חזרתי על הפרק'},6000)};
    return b}
  function qrSet(on,quiet){
    if(on&&rvEdit()){rvToast('חזרה מהירה אינה פועלת במצב עריכה');return}
    var r=topRow();
    OPEN={};
    HE.classList.toggle('qr',!!on);
    rvLsSet(QK,on?'1':null);
    if(on){qrBar();qrT0=Date.now();applyOpen()}
    [].forEach.call(Dc.querySelectorAll('#qrbtn,#mqrbtn'),function(b){b.classList.toggle('on',!!on);b.setAttribute('aria-pressed',on?'true':'false')});
    tipHide();
    if(!quiet)keepPlace(r);
    /* השכבות הצפות (תוס', מקור) נמדדות מחדש */
    if(!on)setTimeout(function(){try{dispatchEvent(new Event('resize'))}catch(e){}},30)}
  window.qrToggle=function(){qrSet(!HE.classList.contains('qr'))};
  /* לחיצה על כותרת: פותחת את מה שמתחתיה (ושוב - סוגרת) */
  if(flowEl)flowEl.addEventListener('click',function(e){
    if(!HE.classList.contains('qr')||rvEdit())return;
    var t=e.target;if(!t||t.closest('button,a,input,select,.mlabel,.tsm'))return;
    try{var sel=getSelection();if(sel&&String(sel).length>1)return}catch(x){}
    var r=t.closest('#flow .row');if(!r)return;
    var an=t.closest('.anchor');
    if(an&&r.classList.contains('u')){var id=uidOf(r);OPEN[id]=!OPEN[id];applyOpen();return}
    var ms=t.closest('.main.mishna');
    if(ms){var k='m'+uidOf(r);OPEN[k]=!OPEN[k];applyOpen();return}
    if(t.closest('.main')&&(r.classList.contains('nose')||r.classList.contains('dh'))){
      var b=bodyRows(r);if(!b.length)return;
      var all=b.every(function(x){return OPEN[uidOf(x)]});
      b.forEach(function(x){OPEN[uidOf(x)]=!all});applyOpen()}});
  /* הדף מצייר פרקים מחדש בגלילה (פרומפט 79): מה שנפתח נשאר פתוח */
  if(flowEl&&window.MutationObserver){var moT=0;
    new MutationObserver(function(){if(!HE.classList.contains('qr'))return;if(moT)return;moT=requestAnimationFrame(function(){moT=0;applyOpen()})}).observe(flowEl,{childList:true})}
  /* מצב עריכה נפתח - החזרה המהירה נסגרת */
  if(window.MutationObserver)new MutationObserver(function(){if(HE.classList.contains('qr')&&rvEdit())qrSet(false,true)}).observe(Dc.body,{attributes:true,attributeFilter:['class']});

  /* הכפתורים: בסרגל (מחשב), בסרגל העליון של הטלפון, ובתפריט "עוד" של הטלפון (mobile.js) */
  (function(){
    var more=Dc.querySelector('#bar .tools .dd[data-label="עוד"]');
    if(more&&!Dc.getElementById('qrbtn')){var b=Dc.createElement('button');b.type='button';b.id='qrbtn';b.className='ib stk';
      b.title='חזרה מהירה';b.setAttribute('aria-label','חזרה מהירה');b.setAttribute('aria-pressed','false');b.innerHTML=rvIc('fold');
      b.onclick=function(){window.qrToggle()};more.parentNode.insertBefore(b,more)}
    var mt=Dc.getElementById('mtop');
    if(mt&&!Dc.getElementById('mqrbtn')){var m=Dc.createElement('button');m.type='button';m.id='mqrbtn';m.title='חזרה מהירה';
      m.setAttribute('aria-label','חזרה מהירה');m.setAttribute('aria-pressed','false');m.innerHTML=rvIc('fold');
      m.onclick=function(){window.qrToggle()};var sr=mt.querySelector('.msr');if(sr)mt.insertBefore(m,sr);else mt.appendChild(m)}
  })();
  /* המצב האחרון של הלומד */
  if(rvLs(QK)==='1'){var st=function(){if(!rvEdit())qrSet(true,true)};if(Dc.readyState==='complete')setTimeout(st,0);else addEventListener('load',function(){setTimeout(st,0)})}
  })();
