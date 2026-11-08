  /* =================== "בחר נוסח" - נוסחאות חלופיות למנהל (13.10.2026; על הטקסט עצמו - פרומפט 25, 8.11.2026) ===================
     מוזרק לדף המסכת רק כשיש למסכת קובץ data/alts/<slug>.json, וגלוי רק במצב מנהל.
     כל נקודה: פסקה שפורסם בה נוסח אחד מבין כמה נוסחים שונים באמת, מתויגים לפי סוג ההכרעה.

     מצב ההכרעה (פרומפט 25): הכול על הטקסט עצמו, בדגם הסקירה של "סכם פרק". הפסקה הנוכחית מוצגת
     בנוסח החלופי, ורק ההבדל מסומן: מה שנמחק בקו חוצה אפור, ומה שנוסף בצבע ירוק כהה עם קו תחתון דק.
     ההשוואה היא של "סכם פרק" (skpDiff, שנשען על skpWords ו-skpLcs), ואין כאן מנוע השוואה משלו.
     ליד הפסקה, בשוליים: קבל · השאר · ערוך, המונה, ותווית הנוסח החלופי. בטלפון הפס צף בתחתית.
     כניסה: הכפתור "בחר נוסח" בסרגל, או המקש N (ובמקלדת עברית נ: במקלדת עברית המקש N הוא מ, של הגמרא).
     Enter קבל · Delete השאר · E ערוך (Enter מסיים ומקבל) · חצים הבא/הקודם · Tab החלופה הבאה · Ctrl+Z ביטול · Esc יציאה.

     השמירה לא השתנתה: קבלה = עריכת מנהל רגילה (applyText: רשומת ED, pubSoon, syncSoon), מתפרסמת בפרסום
     המרוכז ונכתבת לוורד בקליטה הבאה; כל הכרעה נרשמת ביומן ההכרעות בנקודת הקליטה (logDec, /alt), ממנו לומד המנוע. */
  (function(){
  var AL=window.__ALTS||null;
  if(!AL||!AL.items||!AL.items.length)return;
  var NIK=/[֑-ׇ]/g;
  function nrm(s){return String(s||'').replace(/[⟦⟧]/g,'').replace(NIK,'').replace(/[\s ]+/g,' ').replace(/[^א-ת0-9 ]/g,'').trim()}
  function ge(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
  function plainOf(t){return String(t||'').replace(/[⟦⟧]/g,'')}
  function htmlOfText(t){
    var o='',parts=String(t||'').split(/(⟦[^⟧]*⟧)/);
    parts.forEach(function(p){
      if(p.charAt(0)==='⟦'&&p.charAt(p.length-1)==='⟧'){o+='<i class="hs">'+ge(p.slice(1,-1))+'</i>'}
      else o+=ge(p)});
    return o}
  function adm(){return typeof isAdmin==='function'&&isAdmin()}
  function say(m,ms){try{if(typeof toast==='function')toast(m,ms||3500)}catch(e){}}
  function lsGet(k,d){try{var v=localStorage.getItem(k);return v===null?d:v}catch(e){return d}}
  function lsSet(k,v){try{localStorage.setItem(k,v)}catch(e){}}
  var DKEY='lg-alt-dec-'+AL.slug;
  var DEC={};try{DEC=JSON.parse(lsGet(DKEY,'{}'))||{}}catch(e){DEC={}}
  function saveDEC(){lsSet(DKEY,JSON.stringify(DEC))}
  var byId={};AL.items.forEach(function(it,i){byId[it.id]=it;it.ix=i;it.vn=it.variants.map(function(v){return nrm(v.text)})});

  /* ---- איתור הפסקה של כל נקודה ----
     תחילה לפי הטקסט המנורמל של אחד הנוסחים (כמו קודם). פסקה שנערכה מאז שהנוסחים נכתבו - לפי קרבת
     המילים, באותו דף בלבד, ורק כשההתאמה ברורה ויחידה. משנמצאה, הנקודה נצמדת למפתח השורה (מזהה יציב
     בתוך טעינת הדף), כדי שקבלה או עריכה לא ינתקו אותה. */
  var LOC={};     /* id -> {s (שורת נתונים), el} */
  var PIN={};     /* id -> מפתח השורה (u<יחידה>.<שורה>) */
  var LOCV=-1,LOCS=null;
  function words(s){var w=nrm(s).split(' ');return w[0]===''?[]:w}
  function dice(a,b){if(!a.length||!b.length)return 0;var m={},c=0;a.forEach(function(x){m[x]=(m[x]||0)+1});
    b.forEach(function(x){if(m[x]){m[x]--;c++}});return 2*c/(a.length+b.length)}
  function dafOf(d){return String(d||'').replace(/[.:\s]/g,'')}
  function locateAll(){
    var S;try{S=slotsFull()}catch(e){return}
    if(S!==LOCS||LOCV!==(typeof DV!=='undefined'?DV:0)){
      LOCS=S;LOCV=typeof DV!=='undefined'?DV:0;LOC={};
      var by={},byK={},taken={};S.forEach(function(s,i){s._i=i;by[nrm(s.t)]=s;byK[s.k]=s});
      AL.items.forEach(function(it){var s=PIN[it.id]?byK[PIN[it.id]]:null;
        if(s){LOC[it.id]={s:s,el:null};taken[s.k]=1}});
      AL.items.forEach(function(it){if(LOC[it.id])return;var s=null;
        for(var i=0;i<it.vn.length&&!s;i++)s=by[it.vn[i]]||null;
        if(s&&!taken[s.k]){LOC[it.id]={s:s,el:null};PIN[it.id]=s.k;taken[s.k]=1}});
      AL.items.forEach(function(it){if(LOC[it.id])return;
        var vw=it.variants.map(function(v){return words(v.text)}),best=null,b1=0,b2=0;
        S.forEach(function(s){if(taken[s.k]||dafOf(s.daf)!==dafOf(it.daf))return;var w=words(s.t);if(w.length<3)return;
          var sc=0;vw.forEach(function(v){var d=dice(w,v);if(d>sc)sc=d});
          if(sc>b1){b2=b1;b1=sc;best=s}else if(sc>b2)b2=sc});
        if(best&&b1>=0.6&&b1-b2>=0.1){LOC[it.id]={s:best,el:null,fz:1};PIN[it.id]=best.k;taken[best.k]=1}})}
    var f=document.getElementById('flow');
    Object.keys(LOC).forEach(function(id){var l=LOC[id];
      if(!l.el||!l.el.isConnected)l.el=f?f.querySelector('[data-ek="'+l.s.k+'"]'):null})}
  /* הנוסח שבדף כעת (טקסט ו-HTML), כמו ב-applyText */
  function curOf(it){var l=LOC[it.id];if(!l)return null;var s=l.s,ed=null;
    try{ed=ED.find(function(x){return x.k===s.k})}catch(e){}
    return {t:ed?ed.now:s.t,h:ed?(ed.nowH!==undefined?ed.nowH:esc(ed.now)):s.h}}
  function curIndex(it){var c=curOf(it);if(!c)return -1;var n=nrm(c.t);
    for(var i=0;i<it.vn.length;i++)if(it.vn[i]===n)return i;
    return -1}
  /* הנוסח שהדף קרוב אליו ביותר (בפסקה שנערכה אין התאמה מלאה) */
  function nearIndex(it){var ci=curIndex(it);if(ci>-1)return ci;var c=curOf(it);if(!c)return -1;
    var w=words(c.t),bi=0,bs=-1;it.variants.forEach(function(v,i){var d=dice(w,words(v.text));if(d>bs){bs=d;bi=i}});return bi}
  /* החלופות: כל נוסח שאינו זה שבדף */
  function altsOf(it){var ni=nearIndex(it),o=[];it.variants.forEach(function(v,i){if(i!==ni)o.push(i)});
    if(!o.length)it.variants.forEach(function(v,i){o.push(i)});return o}

  var sty=document.createElement('style');
  sty.textContent=
   '#alml{position:fixed;left:0;top:0;width:0;height:0;z-index:6;pointer-events:none}'+
   '.alm{position:fixed;pointer-events:auto;width:16px;height:16px;padding:0;border-radius:50%;border:1px solid #b9a56a;background:rgba(255,253,245,.92);color:#7a5a14;font:700 10px/14px Vilna,serif;text-align:center;cursor:pointer;opacity:.7}'+
   '.alm:hover{opacity:1;background:#f4e7bd}'+
   '.alm.dn{border-color:#6f9a62;color:#3d6b2f;background:rgba(236,245,231,.95);opacity:.85}'+
   'body:not(.adm) .alm,body:not(.adm) #altpg,body:not(.adm) #altbar,body:not(.adm) .altv{display:none!important}'+
   'body:not(.adm) #flow [data-ek].altsrc{display:revert!important}'+
   /* הפסקה הנוכחית: מסגרת דקה בזהב בצד, בלי רקע. הטקסט בגופן ובגודל הרגילים של הדף */
   '#flow [data-ek].altsrc{display:none!important}'+
   '#flow .altv{box-shadow:3px 0 0 0 #c9a24a;scroll-margin-top:28vh;scroll-margin-bottom:30vh;outline:none}'+
   '#flow .altv.edit{box-shadow:3px 0 0 0 #c9a24a,0 0 0 1px rgba(201,162,74,.55);cursor:text}'+
   /* מה שנוסף: צבע טקסט ירוק כהה עדין וקו תחתון דק - בלי רקע. מה שנמחק: קו חוצה אפור */
   '#flow .altv .skpadd{color:#2f6b3a;text-decoration:underline;text-decoration-thickness:1px;text-underline-offset:.22em;text-decoration-color:rgba(47,107,58,.75);background:none}'+
   '#flow .altv del.skpdel{color:#9a9a9a;text-decoration:line-through;text-decoration-thickness:1px;text-decoration-color:#9a9a9a;font-size:.9em}'+
   '#flow .altv del.skpdel.long{text-decoration:none;font-size:11.5px;background:none;border:1px solid #dcdcdc;border-radius:8px;padding:0 6px;cursor:pointer;white-space:nowrap}'+
   /* שינוי קטן מאוד (מילה או שתיים): אותו סימון, מודגש יותר, כדי שהעין תמצא אותו מיד */
   '#flow .altv.sm .skpadd{font-weight:700;text-decoration-thickness:2px}'+
   '#flow .altv.sm del.skpdel{color:#7d7d7d;text-decoration-thickness:2px}'+
   '#flow .altv.sm .skpadd,#flow .altv.sm del.skpdel{box-shadow:0 -2px 0 0 transparent}'+
   '#flow .altv.sm .altdot{display:inline-block;width:5px;height:5px;border-radius:50%;background:#c9a24a;vertical-align:super;margin:0 1px}'+
   /* הפס הקטן בשוליים */
   '#altbar{position:fixed;z-index:62;direction:rtl;display:none;width:172px;box-sizing:border-box;background:rgba(255,253,247,.97);border:1px solid #d9cba3;border-radius:8px;box-shadow:0 2px 10px rgba(0,0,0,.10);padding:5px 6px 5px;font-size:12.5px;line-height:1.35;color:#3d3528}'+
   '#altbar.open{display:block}'+
   '#altbar .ab{display:flex;gap:4px}'+
   '#altbar button{font:inherit;font-size:12.5px;flex:1 1 0;padding:3px 0;border:1px solid #c9b98a;border-radius:6px;background:#fff;color:#4a3d1c;cursor:pointer;min-height:26px}'+
   '#altbar button.go{background:#c9a24a;border-color:#a98a36;color:#2b2210;font-weight:700}'+
   '#altbar button:focus-visible{outline:2px solid #2f6b3a;outline-offset:1px}'+
   '#altbar .am2{display:flex;justify-content:space-between;align-items:center;margin-top:4px;color:#6b5f48}'+
   '#altbar .am2 .x{flex:0 0 auto;min-height:0;border:0;background:none;color:#8a7f68;font-size:15px;padding:0 2px;line-height:1}'+
   '#altbar .atg{color:#8a8070;font-size:11.5px;margin-top:2px}'+
   '#altbar .atg b{font-weight:400;color:#6f6656}'+
   '#altbar .ahelp{display:none}'+
   '#altbar.mob{left:6px!important;right:6px!important;top:auto!important;bottom:6px;width:auto;padding:7px 9px 8px;font-size:14px;box-shadow:0 -2px 14px rgba(0,0,0,.14)}'+
   '#altbar.mob button{font-size:16px;min-height:42px;border-radius:9px}'+
   '#altbar.mob .atg{font-size:13px}'+
   /* מסך רחב שאין בו שוליים פנויים ליד הפסקה (תצוגת הטורים): פס קטן במרכז התחתית */
   '#altbar.dock{left:50%!important;top:auto!important;bottom:10px;transform:translateX(-50%);width:auto;min-width:330px;display:none;align-items:center;gap:10px;padding:5px 10px}'+
   '#altbar.dock.open{display:flex}#altbar.dock .ab{flex:0 0 auto}#altbar.dock button{flex:0 0 auto;padding:3px 14px}#altbar.dock .am2{margin:0;gap:8px}#altbar.dock .atg{margin:0}'+
   'body.altmode.altmob{padding-bottom:120px}'+
   /* בזמן ההכרעה בלבד: הכפתורים הצפים (עיפרון, תפריט) מוסתרים כדי שלא יכסו את הפס */
   'html.altmode #lk-fab{display:none!important}'+
   '@media print{.alm,#alml,#altpg,#altbar{display:none!important}#flow .altv{display:none!important}#flow [data-ek].altsrc{display:revert!important}}'+
   '#altpg .alr{border-top:1px solid #eadfc2;padding:.5em 0}'+
   '#altpg .alr.dn{opacity:.7}'+
   '#altpg .alr .alg{font-size:.8em;color:#7a5a14;font-weight:700}'+
   '#altpg .alr .als{font-size:.95em;margin:.15em 0}'+
   '#altpg .alr button{font:inherit;font-size:.88em;padding:.1em .7em;border:1px solid #b9a56a;border-radius:5px;background:#fff;cursor:pointer;min-height:28px}'+
   '#altpg .alnav{display:flex;gap:.5em;align-items:center;margin:.4em 0}'+
   '#altpg .aln{font-size:.78em;color:#7a6f58;margin-top:.35em}';
  document.head.appendChild(sty);

  /* ---- מצב ההכרעה ---- */
  var M={on:false,id:null,ai:0,edit:false,g:null,el:null,hist:[]};
  function openCount(){var n=0;AL.items.forEach(function(it){if(!DEC[it.id])n++});return n}

  /* ---- שכבת הסימונים (שוליים): נקודה פתוחה - נ בזהב; נקודה שהוכרעה - סימן ירוק קטן. לחיצה פותחת אותה ---- */
  function layerEl(){var l=document.getElementById('alml');
    if(!l){l=document.createElement('div');l.id='alml';document.body.appendChild(l)}return l}
  var LQ=0;
  function layerSoon(){if(LQ)return;LQ=requestAnimationFrame(function(){LQ=0;layer();barPlace()})}
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
      if(M.on&&M.id===it.id)return;
      var l=LOC[it.id];if(!l||!l.el)return;
      var b=l.el.getBoundingClientRect();
      if(!b.height||b.bottom<fr.top||b.top>fr.bottom){return}
      seen[it.id]=1;
      var el=have[it.id],dn=!!DEC[it.id];
      if(!el){el=document.createElement('button');el.type='button';el.className='alm';el.setAttribute('data-id',it.id);
        L.appendChild(el);have[it.id]=el}
      if(el.classList.contains('dn')!==dn||!el.textContent){el.classList.toggle('dn',dn);el.textContent=dn?'✓':'נ';
        el.setAttribute('title',dn?'נוסח שהוכרע - לחיצה פותחת אותו שוב':'נוסח לבחירה - לחיצה פותחת אותו')}
      /* בשוליים: מחוץ לשדה הטקסט, בצד שמאל של הפסקה (בעברית הטקסט נקרא מימין) */
      var left=Math.max(2,Math.round(b.left-22))+'px',top=Math.round(b.top+3)+'px';
      if(el.style.left!==left)el.style.left=left;if(el.style.top!==top)el.style.top=top});
    [].forEach.call(L.children,function(x){if(!seen[x.getAttribute('data-id')])x.remove()})}
  window.altLayer=layer;
  /* בדיקת שלמות (למנהל): כמה נקודות אותרו בטקסט הנוכחי, ואילו לא */
  window.altStat=function(){locateAll();
    var miss=[],fz=0;AL.items.forEach(function(it){if(!LOC[it.id])miss.push(it.id);else if(LOC[it.id].fz)fz++});
    return {total:AL.items.length,found:AL.items.length-miss.length,near:fz,missing:miss,open:openCount()}};
  addEventListener('resize',layerSoon);
  document.addEventListener('scroll',layerSoon,true);
  document.addEventListener('lg-dv',layerSoon);
  /* גיבוי לתזוזות שאינן גלילה (גופנים, פריסת הזנב), ושחזור התצוגה אם הדף צויר מחדש */
  setInterval(function(){if(document.hidden||!adm()||!document.getElementById('flow'))return;
    if(M.on&&M.g&&!M.g.isConnected&&!M.edit)show(false);
    if(!document.body.classList.contains('bk-on'))layer();barPlace()},1500);
  document.addEventListener('click',function(ev){
    var m=ev.target.closest&&ev.target.closest('.alm');
    if(m){ev.preventDefault();ev.stopPropagation();enter(m.getAttribute('data-id'));return}},true);

  /* ---- בחירה: עריכת מנהל רגילה, באותו נתיב של הצעות התיקון (לא שונה בפרומפט 25) ---- */
  function applyText(it,text,edited,vi){
    locateAll();
    var l=LOC[it.id];
    if(!l){say('הפסקה לא אותרה בטקסט הנוכחי (אולי נערכה). רענן ונסה שוב.',5000);return false}
    var s=l.s,old=ED.find(function(x){return x.k===s.k});
    var curT=old?old.now:s.t,curH=old?(old.nowH!==undefined?old.nowH:esc(old.now)):s.h;
    var wasT=old?old.was:s.t,wasH=old?(old.wasH!==undefined?old.wasH:s.h):s.h;
    var nowT=plainOf(text).trim(),nowH=htmlOfText(text.trim());
    if(!nowT){say('הנוסח ריק.');return false}
    if(/[\u2013\u2014]/.test(nowT)){say('בנוסח יש מקף ארוך. יש להשתמש במקף רגיל.',5000);return false}
    if(nrm(nowT)===nrm(curT)&&nowT===curT){return true}
    var cls=(s.c||'').split(' ').filter(function(c){return PCLS.indexOf(c)>-1}).join(' ');
    var el=l.el;
    var edit={k:s.k,was:wasT,now:nowT,wasH:wasH,nowH:nowH,wasP:old?old.wasP:cls,daf:s.daf,
              ctx:el&&typeof ctxOf==='function'?ctxOf(el):{b:'',a:''},t:Date.now(),pub:0,by:'בחירת נוסח'};
    if(old&&old.ps!==undefined){edit.ps=old.ps;edit.psw=old.psw}
    /* לביטול (Ctrl+Z): מה שהיה לפני ההחלה */
    M.lastApply={k:s.k,old:old||null,curH:curH,edit:edit};
    if(old)ED=ED.filter(function(x){return x!==old});
    ED.push(edit);saveED();applyTextNow(edit);drawEd();pubSoon();syncSoon();
    return true}
  function logDec(it,vi,text,edited){
    var rec={id:it.id,v:vi,tag:vi>=0?(it.variants[vi].tag||''):'ערוך',text:plainOf(text),edited:!!edited,at:Date.now()};
    DEC[it.id]=rec;saveDEC();
    if(typeof api==='function'){
      api('/alt',{method:'POST',body:JSON.stringify({slug:AL.slug,id:it.id,v:vi,tag:rec.tag,txt:rec.text,edited:rec.edited,variants:it.variants.map(function(x){return {t:x.tag,x:plainOf(x.text)}}),daf:it.daf||''})}).catch(function(){})}}

  /* ---- התור: הנקודות הפתוחות שאותרו בטקסט, בסדר המסכת ---- */
  function openIds(){locateAll();return AL.items.filter(function(it){return !DEC[it.id]&&LOC[it.id]}).sort(function(a,b){return LOC[a.id].s._i-LOC[b.id].s._i}).map(function(it){return it.id})}
  function nextOpen(fromId,dir){
    var ids=openIds();if(!ids.length)return null;
    var l=fromId&&LOC[fromId],pos=l?l.s._i:-1;
    if(dir>0){for(var i=0;i<ids.length;i++)if(LOC[ids[i]].s._i>pos)return ids[i];return ids[0]}
    for(var j=ids.length-1;j>=0;j--)if(LOC[ids[j]].s._i<pos)return ids[j];return ids[ids.length-1]}
  /* הנקודה הפתוחה הראשונה בדף שעל המסך, ואחר כך בהמשך המסכת */
  function firstHere(){
    var ids=openIds();if(!ids.length)return null;
    var f=document.getElementById('flow'),pi=-1;
    if(f){var fr=f.getBoundingClientRect();
      var rows=[].slice.call(f.querySelectorAll('.row[id^="u"]'));
      for(var i=0;i<rows.length;i++){var b=rows[i].getBoundingClientRect();if(b.height&&b.bottom>fr.top+4&&b.top<fr.bottom){
        var uid=+rows[i].id.slice(1);var S=LOCS||[];for(var j=0;j<S.length;j++)if(S[j].id===uid){pi=S[j].pi;break}
        if(pi>-1)break}}}
    if(pi>-1){for(var k=0;k<ids.length;k++)if(LOC[ids[k]].s.pi>=pi)return ids[k]}
    return ids[0]}

  /* ---- התצוגה במקום ---- */
  function clearView(){
    if(M.g&&M.g.parentNode)M.g.remove();
    if(M.el)M.el.classList.remove('altsrc');
    document.querySelectorAll('#flow .altsrc').forEach(function(x){x.classList.remove('altsrc')});
    document.querySelectorAll('#flow .altv').forEach(function(x){x.remove()});
    M.g=null;M.el=null;M.edit=false}
  function readBack(node){var o='';
    node.childNodes.forEach(function(n){
      if(n.nodeType===3){o+=n.nodeValue;return}
      if(n.nodeType!==1)return;
      if(n.tagName==='BR'){o+=' ';return}
      if(n.classList&&(n.classList.contains('skpdel')||n.classList.contains('altdot')))return;
      if(n.classList&&n.classList.contains('hs')){o+='⟦'+readBack(n)+'⟧';return}
      o+=readBack(n)});
    return o}
  function show(scroll){
    var it=byId[M.id];if(!it){exit();return}
    locateAll();
    var l=LOC[it.id];
    if(!l){say('הנקודה לא אותרה בטקסט הנוכחי - דילוג');var n=nextOpen(it.id,1);if(n&&n!==it.id){M.id=n;return show(scroll)}exit();return}
    if(!l.el){
      /* הנקודה בפרק אחר: מעבר לפרק (פעם אחת), ואז התצוגה */
      if(typeof jump==='function'&&M.jumped!==it.id){M.jumped=it.id;jump(l.s.pi,l.s.id);
        setTimeout(function(){locateAll();if(M.on&&M.id===it.id)show(scroll)},320);return}
      M.jumped=null;say('הפסקה לא נמצאה בדף - דילוג');var nx=nextOpen(it.id,1);if(nx&&nx!==it.id){M.id=nx;return show(scroll)}exit();return}
    M.jumped=null;
    clearView();
    var alts=altsOf(it);if(M.ai>=alts.length)M.ai=0;
    var vi=alts[M.ai],v=it.variants[vi],c=curOf(it);
    var el=l.el,g=el.cloneNode(false);
    g.removeAttribute('data-ek');g.removeAttribute('contenteditable');g.removeAttribute('id');g.removeAttribute('data-edited');
    g.classList.add('altv');g.setAttribute('data-alt',it.id);g.setAttribute('tabindex','-1');g.setAttribute('spellcheck','false');
    g.innerHTML=htmlOfText(v.text);
    var smallCh=false;
    try{
      /* ההשוואה על הטקסט הנקי שבדף: תגיות הסגנון והסמנים שבתוכו מפצלים מילים, ופסיק שאחרי תגית נראה כמילה שנמחקה */
      skpDiff(g,esc(c.t));
      /* סימן פיסוק לבדו (פסיק, סימן שאלה) אינו "מילה שנוספה" או "נמחקה" */
      var hasW=function(x){return /[א-ת0-9]/.test(x)};
      g.querySelectorAll('.skpadd').forEach(function(x){if(!hasW(x.textContent))x.replaceWith(document.createTextNode(x.textContent))});
      g.querySelectorAll('del.skpdel').forEach(function(x){if(!hasW(x.title||x.textContent)){var p=x.nextSibling;x.remove();if(p&&p.nodeType===3&&p.nodeValue===' ')p.remove()}});
      var nAdd=g.querySelectorAll('.skpadd').length,dw=0;g.querySelectorAll('del.skpdel').forEach(function(d){dw+=String(d.title||d.textContent).split(/\s+/).filter(hasW).length});
      smallCh=nAdd+dw>0&&nAdd+dw<=2;
      if(smallCh){g.classList.add('sm');
        var first=g.querySelector('.skpadd,del.skpdel');if(first){var dot=document.createElement('span');dot.className='altdot';dot.setAttribute('aria-hidden','true');first.parentNode.insertBefore(dot,first)}}
      if(!nAdd&&!dw)M.same=1;else M.same=0}catch(e){try{console.warn('alt diff',e)}catch(_){}}
    el.classList.add('altsrc');el.after(g);
    M.g=g;M.el=el;M.vi=vi;
    bar();
    /* סימון הקפיצה (רקע זהוב) אינו נשאר: בפסקה הנוכחית רק המסגרת הדקה */
    document.querySelectorAll('#flow .row.hit').forEach(function(r){r.classList.remove('hit')});
    if(scroll!==false){
      /* גלילה רכה: בתצוגה האנכית (וגם בטלפון) הפסקה בשליש העליון; בתצוגת הטורים - הטור שלה נכנס לתמונה */
      var f=document.getElementById('flow'),multi=f&&!f.classList.contains('vert')&&f.scrollWidth>f.clientWidth+4;
      try{if(multi){var rw=g.closest('.row')||g,rb=rw.getBoundingClientRect(),fb=f.getBoundingClientRect();
          if(rb.left<fb.left+2||rb.right>fb.right-2)f.scrollBy({left:rb.right-fb.right,behavior:'smooth'})}
        else g.scrollIntoView({block:'start',inline:'nearest',behavior:'smooth'})}catch(e){try{g.scrollIntoView()}catch(_){}}
      setTimeout(barPlace,450);setTimeout(barPlace,900)}
    try{if(document.activeElement&&document.activeElement!==document.body&&document.activeElement.blur)document.activeElement.blur()}catch(e){}
    try{g.focus({preventScroll:true})}catch(e){}
    layerSoon()}

  /* ---- הפס הקטן ---- */
  function barEl(){var b=document.getElementById('altbar');
    if(!b){b=document.createElement('div');b.id='altbar';b.setAttribute('role','toolbar');b.setAttribute('aria-label','בחר נוסח');document.body.appendChild(b);
      b.addEventListener('mousedown',function(ev){if(ev.target.closest('button'))ev.preventDefault()});
      b.addEventListener('click',function(ev){var x=ev.target.closest('button');if(x)act(x.getAttribute('data-a'))})}
    return b}
  function bar(){
    var it=byId[M.id],b=barEl();if(!it)return;
    var alts=altsOf(it),v=it.variants[M.vi]||{},d=DEC[it.id],h='';
    if(M.edit){
      h='<div class="ab"><button type="button" class="go" data-a="editok" title="סיים וקבל (Enter)">סיים וקבל</button><button type="button" data-a="editno" title="בטל את העריכה (Esc)">ביטול</button></div>';
    }else{
      h='<div class="ab"><button type="button" class="go" data-a="ok" title="קבל את הנוסח החלופי (Enter)">קבל</button>'+
        '<button type="button" data-a="keep" title="השאר את הנוסח שפורסם (Delete)">השאר</button>'+
        '<button type="button" data-a="edit" title="ערוך בתוך הפסקה (E), Enter מסיים ומקבל">ערוך</button></div>'}
    h+='<div class="am2"><span>'+(it.ix+1)+' מתוך '+AL.items.length+'</span>'+
       '<span><button type="button" class="x" data-a="prev" title="הקודם (חץ למעלה)">‹</button><button type="button" class="x" data-a="next" title="הבא (חץ למטה)">›</button>'+
       '<button type="button" class="x" data-a="exit" title="יציאה (Esc)" aria-label="יציאה">×</button></span></div>'+
       '<div class="atg">'+ge(v.tag||'נוסח חלופי')+(alts.length>1?' <b>· חלופה '+(M.ai+1)+' מתוך '+alts.length+' (Tab)</b>':'')+
       (M.same?' <b>· זהה לנוסח שבדף</b>':'')+
       (d?' <b>· הוכרע'+(d.tag?': '+ge(d.tag):'')+'</b>':'')+(LOC[it.id]&&LOC[it.id].fz?' <b>· הפסקה נערכה מאז</b>':'')+'</div>';
    b.innerHTML=h;b.classList.add('open');barPlace()}
  function barPlace(){
    var b=document.getElementById('altbar');if(!b||!b.classList.contains('open'))return;
    if(!M.on||!M.g||!M.g.isConnected){return}
    var r=M.g.getBoundingClientRect(),row=M.g.closest('.row'),main=M.g.closest('.main')||M.g,mr=main.getBoundingClientRect();
    var W=172,H=b.offsetHeight||64,fr=(document.getElementById('flow')||document.body).getBoundingClientRect();
    var top=Math.min(Math.max(r.top,fr.top+4),Math.max(fr.top+4,innerHeight-H-8)),left=mr.left-W-14;
    var narrow=innerWidth<=760||left<4;
    /* בשוליים בלבד: אם במקום הזה יש טקסט (טור שכן בתצוגת הטורים) - הפס צף בתחתית המסך */
    if(!narrow){var rows=document.querySelectorAll('#flow .row');
      /* שורות הטקסט עצמן (השורה כאלמנט רחבה מן הטקסט שבה) */
      for(var i=0;i<rows.length&&!narrow;i++){if(rows[i]===row)continue;var q=rows[i].getBoundingClientRect();
        if(!(q.height&&q.left<left+W&&q.right>left&&q.top<top+H&&q.bottom>top))continue;
        var rg=document.createRange();rg.selectNodeContents(rows[i]);var cs=rg.getClientRects();
        for(var j=0;j<cs.length;j++){var c=cs[j];if(c.width>2&&c.left<left+W&&c.right>left&&c.top<top+H&&c.bottom>top){narrow=true;break}}}}
    var mob=innerWidth<=760;
    b.classList.toggle('mob',narrow&&mob);b.classList.toggle('dock',narrow&&!mob);document.body.classList.toggle('altmob',narrow);document.documentElement.classList.toggle('altmob',narrow);
    if(narrow){b.style.left='';b.style.top='';
      /* מעל סרגל הניווט התחתון של הטלפון, אם הוא גלוי */
      var nv=document.getElementById('mbot'),bt='';
      if(mob&&nv&&nv.offsetHeight){var nr=nv.getBoundingClientRect();if(nr.top<innerHeight&&nr.top>innerHeight/2)bt=Math.round(innerHeight-nr.top+6)+'px'}
      if(b.style.bottom!==bt)b.style.bottom=bt;return}
    if(b.style.bottom)b.style.bottom='';
    var L=Math.round(left)+'px',T=Math.round(top)+'px';
    if(b.style.left!==L)b.style.left=L;if(b.style.top!==T)b.style.top=T}

  /* ---- הפעולות ---- */
  function enter(id){
    if(!adm())return;
    if(document.body.classList.contains('skprev')){say('קודם סיים או עצור את סקירת סכם');return}
    if((typeof BOOK!=='undefined'&&BOOK)||(typeof PRINTING!=='undefined'&&PRINTING))return;
    locateAll();
    var start=id||firstHere();
    if(!start){finish();return}
    M.on=true;M.id=start;M.ai=0;document.body.classList.add('altmode');document.documentElement.classList.add('altmode');
    var p=document.getElementById('altpg');if(p&&p.classList.contains('open')&&typeof panel==='function')panel('altpg');
    show(true)}
  function exit(){
    if(M.edit){M.edit=false}
    clearView();M.on=false;M.id=null;
    var b=document.getElementById('altbar');if(b){b.classList.remove('open','mob','dock')}
    document.body.classList.remove('altmode','altmob');document.documentElement.classList.remove('altmob','altmode');btnDraw();layerSoon()}
  function finish(){
    exit();
    var miss=0;locateAll();AL.items.forEach(function(it){if(!DEC[it.id]&&!LOC[it.id])miss++});
    var name=(typeof D!=='undefined'&&D.masechet)?D.masechet:'';
    say(miss?'כל הנוסחאות שנמצאו בטקסט הוכרעו. '+miss+' נקודות לא נמצאו בטקסט הנוכחי (הפסקה שונתה), והן ברשימת כל הנקודות.':'כל הנוסחאות ב'+name+' הוכרעו',6000)}
  function advance(){var cur=M.id,n=nextOpen(cur,1);
    if(!n){btnDraw();finish();return}
    M.id=n;M.ai=0;btnDraw();show(true)}
  function accept(){
    var it=byId[M.id];if(!it)return;
    if(M.edit){return editOk()}
    var v=it.variants[M.vi];if(!v)return;
    var prev=DEC[it.id]||null;M.lastApply=null;
    if(!applyText(it,v.text,false,M.vi))return;
    M.hist.push({id:it.id,prev:prev,ap:M.lastApply});
    logDec(it,M.vi,v.text,false);
    advance()}
  function keep(){
    var it=byId[M.id];if(!it)return;
    var prev=DEC[it.id]||null,ni=nearIndex(it),c=curOf(it);
    M.hist.push({id:it.id,prev:prev,ap:null});
    /* השאר: הנוסח שפורסם נשאר כמות שהוא; ההכרעה נרשמת ביומן כבחירה בנוסח שבדף */
    logDec(it,curIndex(it)>-1?ni:-1,c?c.t:'',curIndex(it)<0);
    advance()}
  function editOn(){
    var it=byId[M.id],g=M.g;if(!it||!g)return;
    var v=it.variants[M.vi];
    g.classList.remove('sm');g.innerHTML=htmlOfText(v.text);
    g.classList.add('edit');g.setAttribute('contenteditable','true');M.edit=true;bar();
    try{g.focus({preventScroll:true});var r=document.createRange();r.selectNodeContents(g);r.collapse(false);var s=getSelection();s.removeAllRanges();s.addRange(r)}catch(e){}
    say('עריכה בתוך הפסקה. Enter מסיים ומקבל, Esc מבטל את העריכה',4000)}
  function editOk(){
    var it=byId[M.id],g=M.g;if(!it||!g)return;
    var txt=readBack(g).replace(/[\s ]+/g,' ').replace(/⟦\s*⟧/g,'').trim();
    if(!txt){say('הנוסח ריק.');return}
    var prev=DEC[it.id]||null;M.lastApply=null;
    if(!applyText(it,txt,true,M.vi))return;
    M.hist.push({id:it.id,prev:prev,ap:M.lastApply});
    logDec(it,-1,txt,true);
    M.edit=false;advance()}
  function editNo(){M.edit=false;show(false)}
  /* Ctrl+Z: ביטול ההכרעה האחרונה. הנוסח שבדף חוזר כפי שהיה, וההכרעה נמחקת מן הרשימה שבמכשיר */
  function undo(){
    var h=M.hist.pop();if(!h){say('אין הכרעה לבטל');return}
    var a=h.ap;
    if(a){
      var cur=ED.find(function(x){return x.k===a.k});
      if(cur)ED=ED.filter(function(x){return x!==cur});
      if(a.old){a.old.t=Date.now();a.old.pub=0;ED.push(a.old);applyTextNow(a.old)}
      else{try{tomb(a.k)}catch(e){}
        try{dataSet(a.k,a.curH)}catch(e){}
        try{SLOTS=null}catch(e){}
        var el=document.getElementById('flow')&&document.getElementById('flow').querySelector('[data-ek="'+a.k+'"]');
        if(el){try{setHTML(el,a.curH)}catch(e){el.innerHTML=a.curH}delete el.dataset.edited}}
      saveED();drawEd();pubSoon();syncSoon()}
    if(h.prev)DEC[h.id]=h.prev;else delete DEC[h.id];
    saveDEC();
    M.id=h.id;M.ai=0;M.edit=false;btnDraw();
    say('ההכרעה בוטלה',2500);
    show(true)}
  function move(dir){var n=nextOpen(M.id,dir);if(!n||n===M.id){say(n?'זו הנקודה הפתוחה היחידה':'אין נקודות פתוחות');return}M.id=n;M.ai=0;show(true)}
  function tab(){var it=byId[M.id];if(!it)return;var n=altsOf(it).length;
    if(n<2){say('בנקודה הזאת יש נוסח חלופי אחד');return}
    M.ai=(M.ai+1)%n;show(false)}
  function act(a){
    if(!M.on)return;
    ({ok:accept,keep:keep,edit:editOn,editok:editOk,editno:editNo,prev:function(){move(-1)},next:function(){move(1)},exit:exit})[a]()}
  window.altMode=function(id){if(M.on&&!id){exit();return}enter(id||null)};

  /* ---- המקלדת: לפני העורך ולפני מקשי הדף (שלב הלכידה), רק במצב ההכרעה ---- */
  addEventListener('keydown',function(e){
    var k=e.key;
    var t=e.target,inG=M.g&&M.g.contains(t);
    var typing=!inG&&t&&t.closest&&t.closest('input,textarea,select,[contenteditable="true"],[contenteditable=""]');
    if(!M.on){
      /* כניסה: N (או נ בעברית), רק למנהל ורק כשאין הקלדה */
      if(typing||e.ctrlKey||e.altKey||e.metaKey||!adm())return;
      if(k==='n'||k==='N'||k==='נ'){
        if(document.body.classList.contains('skprev'))return;
        e.preventDefault();e.stopPropagation();enter(null)}
      return}
    if(typing)return;
    var stop=function(){e.preventDefault();e.stopPropagation()};
    if(M.edit){
      if(k==='Enter'&&!e.shiftKey&&!e.altKey){stop();editOk()}
      else if(k==='Escape'){stop();editNo()}
      return}
    if(e.ctrlKey&&!e.altKey&&e.code==='KeyZ'){stop();undo();return}
    if(e.ctrlKey||e.altKey||e.metaKey)return;
    if(k==='Enter'){stop();accept()}
    else if(k==='Delete'){stop();keep()}
    else if(e.code==='KeyE'){stop();editOn()}
    else if(k==='ArrowDown'||k==='ArrowLeft'){stop();move(1)}
    else if(k==='ArrowUp'||k==='ArrowRight'){stop();move(-1)}
    else if(k==='Tab'){stop();tab()}
    else if(k==='Escape'){stop();exit()}},true);

  /* ---- הכפתור בסרגל: "בחר נוסח (פתוחות)" ---- */
  function btnDraw(){
    var b=document.getElementById('altgo');if(!b)return;
    var n=openCount(),t=b.querySelector('.t');
    if(t){var s='בחר נוסח ('+n+')';if(t.textContent!==s)t.textContent=s}
    b.title='בחר נוסח: '+n+' נקודות פתוחות מתוך '+AL.items.length+'. הנוסח החלופי מוצג על הטקסט עצמו (N)';
    b.setAttribute('aria-pressed',M.on?'true':'false');
    if(!b._alt){b._alt=1;b.onclick=function(ev){ev.preventDefault();altMode()}}
    /* "רשימת כל הנקודות" - קישור קטן בתפריט המנהל, לא נפתח לבד */
    var lb=document.getElementById('lnbtn');
    if(lb&&!document.getElementById('altlist')){
      /* בתפריט המנהל: הכניסה עצמה (בטלפון הכפתור שבסרגל מוסתר), ומתחתיה הקישור הקטן לרשימה */
      var e=document.createElement('button');e.id='altmenu';e.type='button';e.onclick=function(){altMode()};lb.before(e);
      var m=document.createElement('button');m.id='altlist';m.type='button';m.style.fontSize='.85em';m.style.opacity='.85';
      m.textContent='רשימת כל הנקודות';m.title='כל נקודות "בחר נוסח" במסכת, הפתוחות וההוכרעו';
      m.onclick=function(){altPanel()};lb.before(m)}
    var em=document.getElementById('altmenu');if(em){var s2='בחר נוסח ('+n+')';if(em.textContent!==s2)em.textContent=s2;em.title=b.title}}

  /* ---- דף מרוכז "נוסחאות לבחירה" (פאנל) - רק מן הקישור בתפריט המנהל ---- */
  function pgEnsure(){
    if(document.getElementById('altpg'))return;
    var p=document.createElement('div');p.className='panel';p.id='altpg';
    p.innerHTML='<button class="x" onclick="panel(&quot;altpg&quot;)">×</button><h3>נוסחאות לבחירה</h3><div id="altpgb"></div>';
    document.body.appendChild(p)}
  function altPgDraw(){
    var b=document.getElementById('altpgb');if(!b)return;
    var open=0,done=0;AL.items.forEach(function(it){if(DEC[it.id])done++;else open++});
    locateAll();
    var h='<div class="alnav"><b>'+open+'</b> פתוחות · <b>'+done+'</b> הוכרעו · מתוך '+AL.items.length+'</div>'+
          '<div class="aln">הנוסח שפורסם נשאר אם לא תבחר. בחירה מחליפה מיד את הנוסח באתר, ונכתבת לוורד בעקוב אחר שינויים בקליטה הבאה.</div>';
    var cur='';
    AL.items.forEach(function(it){
      if(it.daf!==cur){cur=it.daf;h+='<h4 style="margin:.8em 0 .1em;color:#7a5a14">דף '+ge(cur||'')+'</h4>'}
      var ni=LOC[it.id]?nearIndex(it):0;
      h+='<div class="alr'+(DEC[it.id]?' dn':'')+'"><div class="alg">'+it.variants.map(function(v){return ge(v.tag||'')}).join(' · ')+(DEC[it.id]?' · הוכרע':'')+(LOC[it.id]?'':' · לא נמצאה בטקסט הנוכחי')+'</div>'+
         '<div class="als">'+ge(plainOf((it.variants[ni>=0?ni:0]||{}).text).slice(0,150))+'</div>'+
         (LOC[it.id]?'<button type="button" data-id="'+ge(it.id)+'" onclick="altGo(this.getAttribute(\'data-id\'))">הצג וקבע</button>':'')+'</div>'});
    b.innerHTML=h}
  window.altGo=function(id){if(!byId[id])return;var p=document.getElementById('altpg');if(p&&p.classList.contains('open')&&typeof panel==='function')panel('altpg');enter(id)};
  window.altPanel=function(){pgEnsure();altPgDraw();var p=document.getElementById('altpg');if(p&&!p.classList.contains('open'))panel('altpg')};
  /* סימון לאחר כל רינדור: ה-flow נבנה מחדש בעת מעבר בין דפים */
  window.altMark=layerSoon;
  window.altDecided=function(id){return !!DEC[id]};   /* סקירה (13.10.2026): חלונית ההערות מציגה את הנקודות כסוג "בחר נוסח" */
  /* הכרעות ממכשיר אחר: יומן ההכרעות שבנקודת הקליטה (למנהל), כדי שנקודה שהוכרעה לא תחזור לתור */
  function pullPicks(){
    if(!adm()||typeof api!=='function')return;
    try{api('/alt?slug='+encodeURIComponent(AL.slug)).then(function(j){var pk=j&&j.doc&&j.doc.picks;if(!pk)return;var ch=0;
      Object.keys(pk).forEach(function(id){if(byId[id]&&!DEC[id]){var r=pk[id]||{};DEC[id]={id:id,v:r.v,tag:r.tag||'',text:r.txt||'',edited:!!r.edited,at:r.at||0,srv:1};ch++}});
      if(ch){saveDEC();btnDraw();layerSoon()}}).catch(function(){})}catch(e){}}
  setTimeout(function(){btnDraw();layerSoon()},400);
  setTimeout(pullPicks,1800);
  })();
