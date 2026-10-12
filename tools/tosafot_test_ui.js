  /* =================== מבחן מנועים עיוור לתוספות בשורה אחת (12.10.2026) ===================
     מוזרק רק למסכת שיש לה tosafot/<slug>/test-options.json, ופעיל רק בכניסת מנהל.
     לכל תוספות כרטיס אחד: המספר, הד"ה המאומת בבולט, כפתור "פנים", וחמש אופציות שהסדר שלהן מוגרל מראש לכל תוספות
     ומסומנות באותיות א-ה בלבד. שם המנוע אינו נטען לדף עד לחיצת "חשוף את התוצאות" (קובץ נפרד).
     השמירה בנקודת הקליטה הקיימת (/tos), מיד, כך שאפשר להפסיק ולהמשיך מכל מכשיר:
       בחירה בודדת      -> pick=<אות>, txt=<נוסח>
       עריכה חופשית     -> pick=custom, from=<אות המקור>, txt=<נוסח שנערך>
       שתיים טובות      -> pick=<הראשונה>, והערה שמתחילה ב-[שתיים: ב,ד]
       אף אחת לא טובה   -> pick=none, והערה שמתחילה ב-[אף אחת]
     הבחירה מתפרסמת מיד לכל הלומדים כנוסח ההערה (עד שנבחר: אופציית פייבל, מתוך live-*.json). */
  (function(){
  var T=window.__TOSTEST||null;
  if(!T)return;
  var CUR={file:T.file,reveal:T.reveal},LOADEDF=null,VERIFY=null;
  var LET=['a','b','c','d','e'],HE={a:'א',b:'ב',c:'ג',d:'ד',e:'ה'};
  var SINCE=0,ITEMS=null,ORDER=[],DOC={picks:{},notes:{}},IDX=0,PAIR=null,EDITFROM=null,FACE=false,OPEN=false,LOADING=false;
  function ge(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
  function adm(){return typeof isAdmin==='function'&&isAdmin()}
  function say(m,ms){if(typeof toast==='function')toast(m,ms||3000)}

  var sty=document.createElement('style');
  sty.textContent=
   '#tostest{position:fixed;inset:0;z-index:60;background:var(--paper,#fbf8f1);color:#2b2620;display:none;overflow:auto;-webkit-overflow-scrolling:touch}'+
   '#tostest.open{display:block}'+
   '#tostest .ttw{max-width:46em;margin:0 auto;padding:12px 14px 80px}'+
   '#tostest .tth{display:flex;align-items:center;gap:.6em;position:sticky;top:0;background:var(--paper,#fbf8f1);padding:8px 0;border-bottom:1px solid #d8cfb8;z-index:2}'+
   '#tostest .tth h2{margin:0;font-size:1.05em;flex:1 1 auto}'+
   '#tostest button{font:inherit;cursor:pointer;border:1px solid #b9a56a;background:#fff;border-radius:6px;padding:.35em .8em;min-height:36px;color:inherit}'+
   '#tostest button.go{background:#c9a24a;border-color:#a98a36}'+
   '#tostest button.sel{background:#e6edf7;border-color:#12396b;font-weight:700}'+
   '#tostest button[disabled]{opacity:.45;cursor:default}'+
   '#tostest .ttp{height:6px;background:#eee5cc;border-radius:3px;margin:8px 0}'+
   '#tostest .ttp i{display:block;height:100%;background:#7a5a14;border-radius:3px}'+
   '#tostest .ttc{border:1px solid #d8cfb8;border-radius:10px;padding:12px 14px;background:#fffdf7;margin-top:10px}'+
   '#tostest .ttn{font-family:Vilna,serif;font-weight:900;font-size:1.25em;margin-inline-end:.4em}'+
   '#tostest .ttd{font-weight:700;font-size:1.05em;line-height:1.5}'+
   '#tostest .ttm{color:#7a6f58;font-size:.85em;margin:.2em 0 .5em}'+
   '#tostest .ttf{margin:.5em 0;padding:.6em .8em;background:#f6f1e3;border-radius:6px;font-size:.92em;line-height:1.65}'+
   '#tostest .ttl{margin:.4em 0;font-size:.88em;color:#5a4a1e}'+
   '#tostest .tto{display:flex;gap:.6em;align-items:flex-start;padding:.55em .5em;border-bottom:1px solid #eee5cc;border-radius:6px}'+
   '#tostest .tto.cur{background:#eaf3e6}'+
   '#tostest .tto.pr{background:#fff4d6}'+
   '#tostest .tto .tl{flex:0 0 1.8em;font-weight:900;font-size:1.15em;color:#7a5a14}'+
   '#tostest .tto .tt{flex:1 1 auto;line-height:1.6;font-size:1.02em}'+
   '#tostest .tto .tb{flex:0 0 auto;display:flex;flex-direction:column;gap:.3em}'+
   '#tostest .ttx{margin-top:.7em;display:flex;flex-wrap:wrap;gap:.5em}'+
   '#tostest textarea,#tostest input[type=text]{width:100%;box-sizing:border-box;font:inherit;padding:.4em .5em;border:1px solid #c9bfa6;border-radius:5px;margin:.3em 0;direction:rtl}'+
   '#tostest textarea{min-height:5em;line-height:1.5}'+
   '#tostest .ttb{margin-top:.8em;color:#7a6f58;font-size:.85em}'+
   '#tostest .ttr table{width:100%;border-collapse:collapse;font-size:.92em;margin:.5em 0}'+
   '#tostest .ttr th,#tostest .ttr td{border-bottom:1px solid #eee5cc;padding:.35em .4em;text-align:right}'+
   '#tostest .ttr h3{margin:1em 0 .2em;font-size:1em}'+
   '#tostest .ttrec{padding:.7em .9em;background:#eaf3e6;border-radius:8px;font-weight:700;margin:.8em 0}'+
   '@media (max-width:600px){#tostest .tto{flex-direction:column}#tostest .tto .tb{flex-direction:row;flex-wrap:wrap}}';
  document.head.appendChild(sty);

  function el(){var e=document.getElementById('tostest');
    if(!e){e=document.createElement('div');e.id='tostest';e.setAttribute('dir','rtl');e.setAttribute('role','dialog');e.setAttribute('aria-label','מבחן מנועים');document.body.appendChild(e)}return e}

  /* ---- מצב כרטיס ---- */
  function lets(it){return LET.filter(function(L){return it.options&&it.options[L]!=null})}
  function kk(k){return String(ITEMS[k].key)}
  function noteOf(k){var n=DOC.notes&&DOC.notes[kk(k)];return (n&&n.at>=SINCE&&n.t)||''}
  function parseNote(t){
    var m=/^\[שתיים: ([א-ה]),([א-ה])\]\s*([\s\S]*)$/.exec(t);if(m)return {kind:'two',a:m[1],b:m[2],free:m[3]};
    m=/^\[אף אחת\]\s*([\s\S]*)$/.exec(t);if(m)return {kind:'none',free:m[1]};
    return {kind:'',free:t}}
  function state(k){
    var p=DOC.picks&&DOC.picks[kk(k)];if(p&&p.at<SINCE)p=null;var pn=parseNote(noteOf(k));
    if(pn.kind==='none'&&!p)return {kind:'none',free:pn.free};
    if(p&&pn.kind==='two')return {kind:'two',a:pn.a,b:pn.b,pick:p,free:pn.free};
    if(p&&p.p==='custom')return {kind:'custom',pick:p,free:pn.free};
    if(p)return {kind:'one',pick:p,free:pn.free};
    return {kind:'',free:pn.free}}
  function decided(k){return !!state(k).kind}
  function doneCount(){var c=0;ORDER.forEach(function(k){if(decided(k))c++});return c}

  /* ---- שמירה ---- */
  function post(body){return api('/tos',{method:'POST',body:JSON.stringify(Object.assign({slug:SLUG},body))}).then(function(j){
      if(j&&j.doc){DOC.picks=j.doc.picks||{};DOC.notes=j.doc.notes||{}}
      if(typeof window.tosPubSet==='function'){var pub={};Object.keys(DOC.picks).forEach(function(n){pub[n]={p:DOC.picks[n].p,t:DOC.picks[n].t}});window.tosPubSet(pub)}
      return j})}
  function freeNote(){var i=document.getElementById('ttnote');return i?i.value.trim():''}
  function fail(e){say('לא נשמר: '+(e&&e.message||''),5000)}
  function pickOne(k,letter){
    var it=ITEMS[k];if(!it)return;
    if(PAIR!==null){
      if(PAIR.indexOf(letter)<0)PAIR.push(letter);
      if(PAIR.length<2){render();return}
      var two=PAIR.slice().sort();PAIR=null;
      post({n:+it.key,pick:two[0],txt:it.options[two[0]],from:two[0],note:'[שתיים: '+HE[two[0]]+','+HE[two[1]]+'] '+freeNote()}).then(function(){say('נשמר: שתי אופציות טובות באותה מידה');EDITFROM=null;render()}).catch(fail);
      return}
    post({n:+it.key,pick:letter,txt:it.options[letter],from:letter,note:freeNote()}).then(function(){say('נבחרה אופציה '+HE[letter]+'. הנוסח מוצג ללומדים מיד');EDITFROM=null;render()}).catch(fail)}
  function pickNone(k){
    var it=ITEMS[k];
    post({n:+it.key,pick:'none',note:'[אף אחת] '+freeNote()}).then(function(){say('נרשם: אף אחת לא טובה. ללומדים מוצג נוסח ברירת המחדל');render()}).catch(fail)}
  function saveEdit(k){
    var it=ITEMS[k],ta=document.getElementById('ttedit');if(!ta)return;
    var v=ta.value.trim();if(!v)return;
    post({n:+it.key,pick:'custom',txt:v,from:EDITFROM||'a',note:freeNote()}).then(function(){say('הנוסח שערכת נשמר ויוצג ללומדים מיד');render()}).catch(fail)}
  function saveNote(k){
    var it=ITEMS[k],st=state(k),pre='';
    if(st.kind==='two')pre='[שתיים: '+st.a+','+st.b+'] ';else if(st.kind==='none')pre='[אף אחת] ';
    post({n:+it.key,note:pre+freeNote()}).then(function(){say('ההערה נשמרה')}).catch(fail)}

  /* ---- ציור ---- */
  function cardHTML(k){
    var it=ITEMS[k],st=state(k),h='';
    var done=doneCount(),tot=ORDER.length;
    h+='<div class="ttc" data-k="'+ge(k)+'"><div><span class="ttn">'+ge(it.n)+'</span><span class="ttd">'+ge(it.dh)+'</span></div>'+
       '<div class="ttm">תוספות מספר '+ge(it.n)+' בפרק '+ge(it.perek)+' · דף '+ge(String(it.daf).replace(/[.:]$/,''))+(String(it.daf).slice(-1)===':'?' ע"ב':' ע"א')+
       (st.kind?' · <b>'+({one:'נבחרה אופציה '+(st.pick&&HE[st.pick.p]||''),two:'שתיים טובות: '+(st.a||'')+', '+(st.b||''),custom:'נבחר נוסח שנערך',none:'אף אחת לא טובה'}[st.kind])+'</b>':' · טרם נבחר')+'</div>'+
       '<button type="button" id="ttface">'+(FACE?'סגור את הפנים':'פנים')+'</button>';
    if(FACE){
      var t=it.text||'',i=t.indexOf(' - '),f=ge(t);
      if(i>0&&i<160)f='<b>'+ge(t.slice(0,i))+'</b> - '+ge(t.slice(i+3));
      h+='<div class="ttf">'+f+' <a href="'+ge(it.url||'#')+'" target="_blank" rel="noopener">בספריא</a></div>'}
    if(it.laukmi)h+='<div class="ttl">שורת הלאוקמי שבה התוספות מעוגן: '+ge(it.laukmi)+'</div>';
    h+='<div class="tto-wrap">';
    lets(it).forEach(function(L,ix){
      var cur=(st.kind==='one'&&st.pick&&st.pick.p===L)||(st.kind==='two'&&(HE[L]===st.a||HE[L]===st.b));
      var pr=PAIR&&PAIR.indexOf(L)>=0;
      h+='<div class="tto'+(cur?' cur':'')+(pr?' pr':'')+'"><span class="tl">'+HE[L]+'</span><span class="tt">'+ge(it.options[L])+'</span>'+
         '<span class="tb"><button type="button" class="go" data-a="pick" data-l="'+L+'" title="מקש '+(ix+1)+'">בחר ('+(ix+1)+')</button>'+
         '<button type="button" data-a="edit" data-l="'+L+'">ערוך</button></span></div>'});
    h+='</div><div class="ttx"><button type="button" data-a="pair"'+(PAIR!==null?' class="sel"':'')+'>שתיים טובות באותה מידה</button>'+
       '<button type="button" data-a="none">אף אחת לא טובה</button></div>';
    if(PAIR!==null)h+='<div class="ttb">סמן עכשיו את שתי האופציות הטובות (נבחרו '+PAIR.length+' מתוך 2)</div>';
    if(EDITFROM){
      var base=it.options[EDITFROM];
      h+='<div class="ttx" style="display:block"><label>עריכה חופשית (מבוסס על אופציה '+HE[EDITFROM]+')</label><textarea id="ttedit">'+ge(st.kind==='custom'&&st.pick?st.pick.t:base)+'</textarea>'+
         '<button type="button" class="go" data-a="saveedit">שמור את הנוסח שערכתי</button> <button type="button" data-a="canceledit">בטל</button></div>'}
    h+='<div class="ttx" style="display:block"><label for="ttnote">הערה לקלוד על התוספות הזה</label><input type="text" id="ttnote" value="'+ge(st.free||'')+'" placeholder="למשל: חסר התירוץ השני"> <button type="button" data-a="savenote">שמור הערה</button></div></div>';
    h+='<div class="ttb">מקשים: 1 עד '+lets(it).length+' בחירה · חץ שמאלה הבא · חץ ימינה הקודם</div>';
    return h}
  function render(){
    if(!OPEN)return;
    var e=el(),k=ORDER[IDX],done=doneCount(),tot=ORDER.length;
    e.innerHTML='<div class="ttw"><div class="tth"><h2>מבחן מנועים: '+(IDX+1)+' מתוך '+tot+' · נבחרו '+done+'</h2>'+
      '<button type="button" data-a="prev">הקודם</button><button type="button" data-a="next">הבא</button>'+
      '<button type="button" data-a="reveal"'+'>חשוף את התוצאות</button><button type="button" data-a="close" aria-label="סגור">סגור</button></div>'+
      '<div class="ttp"><i style="width:'+Math.round(100*done/Math.max(1,tot))+'%"></i></div>'+(k?cardHTML(k):'<p>אין תוספות במבחן.</p>')+'</div>';
    e.classList.add('open')}

  function go(d){IDX=Math.max(0,Math.min(ORDER.length-1,IDX+d));PAIR=null;EDITFROM=null;FACE=false;render();var e=el();e.scrollTop=0}
  document.addEventListener('click',function(ev){
    var b=ev.target.closest&&ev.target.closest('#tostest [data-a],#tostest #ttface');if(!b)return;
    var a=b.id==='ttface'?'face':b.getAttribute('data-a'),k=ORDER[IDX];
    if(a==='close'){close();return}
    if(a==='prev'){go(-1);return}
    if(a==='next'){go(1);return}
    if(a==='face'){FACE=!FACE;render();return}
    if(a==='pick'){pickOne(k,b.getAttribute('data-l'));return}
    if(a==='edit'){EDITFROM=b.getAttribute('data-l');render();setTimeout(function(){var t=document.getElementById('ttedit');if(t)t.focus()},30);return}
    if(a==='canceledit'){EDITFROM=null;render();return}
    if(a==='saveedit'){saveEdit(k);return}
    if(a==='pair'){PAIR=PAIR===null?[]:null;render();return}
    if(a==='none'){pickNone(k);return}
    if(a==='savenote'){saveNote(k);return}
    if(a==='reveal'){reveal(false);return}
    if(a==='back'){render();return}
  });
  document.addEventListener('keydown',function(ev){
    if(!OPEN)return;
    var tg=ev.target&&ev.target.tagName;
    if(ev.key==='Escape'){close();return}
    if(tg==='TEXTAREA'||tg==='INPUT')return;
    if(/^[1-5]$/.test(ev.key)){var _it=ITEMS&&ITEMS[ORDER[IDX]],_ls=_it?lets(_it):[];if(_ls[+ev.key-1]){pickOne(ORDER[IDX],_ls[+ev.key-1]);ev.preventDefault()}return}
    if(ev.key==='ArrowLeft'){go(1);ev.preventDefault();return}
    if(ev.key==='ArrowRight'){go(-1);ev.preventDefault()}});

  function close(){OPEN=false;var e=document.getElementById('tostest');if(e){e.classList.remove('open');e.innerHTML=''}}

  /* ---- חשיפה ---- */
  function reveal(force){
    var done=doneCount(),tot=ORDER.length;
    if(done<tot&&!force){
      if(!window.confirm('נבחרו '+done+' מתוך '+tot+'. לחשוף את התוצאות לפני שסיימת? אחרי החשיפה קשה יהיה להמשיך בלי הטיה.'))return}
    if(!CUR.reveal){say('קובץ החשיפה של הסבב הזה עדיין אינו באתר (יועלה אחרי שתסיים לבחור)',5000);return}
    fetch(CUR.reveal,{cache:'no-store'}).then(function(r){return r.json()}).then(function(R){
      api('/tos?slug='+encodeURIComponent(SLUG)+'&adm=1').then(function(j){
        if(j&&j.doc){DOC.picks=j.doc.picks||{};DOC.notes=j.doc.notes||{}}
        showResults(R)}).catch(function(){showResults(R)})
    }).catch(function(){say('לא נטען קובץ החשיפה',4000)})}
  function engLabel(R,id){return (R.tokens[id]&&R.tokens[id].label)||id}
  function showResults(R){
    var engines=Object.keys(R.tokens),won={},edited={},tie={};
    engines.forEach(function(e){won[e]=0;edited[e]=0;tie[e]=0});
    var flagsOnKept=0,rejectedTotal=0,rejectedFlagged=0;
    var lastLog={};(DOC.log||[]).forEach(function(l){lastLog[String(l.n)]=l});
    ORDER.forEach(function(k){
      var st=state(k),m=R.map[ITEMS[k].id]||{},rv=R.review[ITEMS[k].id]||{},keep={};
      if(st.kind==='one'){var e1=m[st.pick.p];if(e1){won[e1]++;keep[e1]=1}}
      else if(st.kind==='custom'){var lg=lastLog[kk(k)],e2=lg&&m[lg.from];if(e2){edited[e2]++;won[e2]++;keep[e2]=1}}
      else if(st.kind==='two'){[st.a,st.b].forEach(function(he){var L=LET[Object.keys(HE).map(function(x){return HE[x]}).indexOf(he)],e3=m[L];if(e3){tie[e3]++;keep[e3]=1}})}
      if(st.kind){
        engines.forEach(function(e){
          var fl=(rv[e]||[]).length>0;
          if(keep[e]){if(fl)flagsOnKept++}
          else{rejectedTotal++;if(fl)rejectedFlagged++}})}});
    if(R.verify){
      var nw=won[R.verify.new]||0,od=won[R.verify.old]||0,tw=(tie[R.verify.new]||0);
      el().innerHTML='<div class="ttw ttr"><div class="tth"><h2>תוצאות אימות הפרופיל</h2><button type="button" data-a="back">חזרה לכרטיסים</button><button type="button" data-a="close">סגור</button></div>'+
        '<div class="ttrec">הפרומפט החדש נבחר '+nw+' פעמים, הישן '+od+' פעמים, ושתיים טובות באותה מידה '+tw+' פעמים, מתוך '+ORDER.length+' תוספות. נבחרו עם תיקון: חדש '+(edited[R.verify.new]||0)+', ישן '+(edited[R.verify.old]||0)+'.</div></div>';
      return}
    var n=ORDER.length,PR=R.prices||{},SHAS=R.shas||27000;
    var rows=engines.map(function(e){
      var t=R.tokens[e],nt=Math.max(1,t.ntos),ia=t.in/nt,oa=t.out/nt;
      var pr=PR[e]||{in:0,out:0};
      var est=SHAS*(ia*pr.in+oa*pr.out)/1e6;
      return {e:e,label:engLabel(R,e),won:won[e],tie:tie[e],edited:edited[e],ia:ia,oa:oa,th:t.think/nt,cost:(t.cost||0)/nt,est:est,rate:(won[e]+tie[e])/Math.max(1,n)}});
    var best=Math.max.apply(null,rows.map(function(r){return r.rate}));
    var ok=rows.filter(function(r){return r.rate>=0.9*best&&best>0}).sort(function(a,b){return a.est-b.est});
    var h='<div class="ttw ttr"><div class="tth"><h2>תוצאות המבחן</h2><button type="button" data-a="back">חזרה לכרטיסים</button><button type="button" data-a="close">סגור</button></div>'+
      '<h3>כמה פעמים נבחר כל מנוע</h3><table><tr><th>מנוע</th><th>נבחר</th><th>שוות (בזוג)</th><th>נבחר עם תיקון</th></tr>'+
      rows.map(function(r){return '<tr><td>'+ge(r.label)+'</td><td>'+r.won+'</td><td>'+r.tie+'</td><td>'+r.edited+'</td></tr>'}).join('')+'</table>'+
      '<h3>טוקנים ועלות ממוצעת לתוספות אחד</h3><table><tr><th>מנוע</th><th>קלט</th><th>פלט</th><th>חשיבה</th><th>עלות בקריאה ישירה</th></tr>'+
      rows.map(function(r){return '<tr><td>'+ge(r.label)+'</td><td>'+Math.round(r.ia)+'</td><td>'+Math.round(r.oa)+'</td><td>'+Math.round(r.th)+'</td><td>$'+r.cost.toFixed(4)+'</td></tr>'}).join('')+'</table>'+
      '<h3>הערכת עלות לכל הש"ס ('+SHAS.toLocaleString('he-IL')+' תוספות) בעיבוד מרוכז (Batch)</h3><table><tr><th>מנוע</th><th>מחיר למיליון (קלט/פלט)</th><th>הערכה</th></tr>'+
      rows.map(function(r){var p=PR[r.e]||{in:0,out:0};return '<tr><td>'+ge(r.label)+'</td><td>'+p.in+' / '+p.out+'</td><td>$'+Math.round(r.est).toLocaleString('he-IL')+'</td></tr>'}).join('')+'</table>'+
      '<div class="ttb">ההערכה מבוססת על ממוצע הקלט והפלט בפועל לתוספות אחד במבחן הזה (כולל תקורת הקריאה). מחירים נבדקו ב-'+ge(R.pricesChecked||'')+(R.pricesNote?' · '+ge(R.pricesNote):'')+'. עם מטמון פרומפט והגשת עמודים מלאים הקלט יירד.</div>'+
      '<h3>דיוק המבקר הזול</h3><div>מתוך '+rejectedTotal+' אופציות שהמנהל לא בחר, המבקר סימן '+rejectedFlagged+' ('+(rejectedTotal?Math.round(100*rejectedFlagged/rejectedTotal):0)+'%). מתוך האופציות שנבחרו, סימן לשווא '+flagsOnKept+'.</div>'+
      '<div class="ttrec">'+(ok.length?'המלצה: '+ge(ok[0].label)+', המנוע הזול ביותר שנבחר לפחות ב-90% מקצב הנבחר ביותר (הערכה לש"ס: $'+Math.round(ok[0].est).toLocaleString('he-IL')+').':'אין עדיין מספיק בחירות להמלצה.')+'</div></div>';
    el().innerHTML=h}

  /* ---- טעינה ופתיחה ---- */
  window.tosTestOpen=function(ri){
    if(!adm()){say('המבחן זמין לכניסת מנהל בלבד');return}
    var rd=(T.rounds&&T.rounds[ri||0])||{file:T.file,reveal:T.reveal};
    CUR={file:rd.file,reveal:rd.reveal};
    if(LOADEDF!==CUR.file){ITEMS=null;ORDER=[];DOC={picks:{},notes:{}};IDX=0}
    var m=document.getElementById('tosmenu');if(m)m.classList.remove('open');
    if(LOADING)return;
    OPEN=true;
    var e=el();e.classList.add('open');e.innerHTML='<div class="ttw"><p>טוען...</p></div>';
    if(ITEMS){load2();return}
    LOADING=true;
    fetch(CUR.file,{cache:'no-store'}).then(function(r){return r.json()}).then(function(j){
      SINCE=j.since||0;ITEMS=j.items;LOADEDF=CUR.file;Object.keys(ITEMS).forEach(function(k){ITEMS[k].id=k});
      ORDER=Object.keys(ITEMS).sort(function(a,b){return ITEMS[a].key-ITEMS[b].key});
      LOADING=false;load2()}).catch(function(){LOADING=false;OPEN=false;e.classList.remove('open');say('לא נטען קובץ המבחן',4000)})};
  function load2(){
    api('/tos?slug='+encodeURIComponent(SLUG)+'&adm=1').then(function(j){
      var d=(j&&j.doc)||{};DOC={picks:d.picks||{},notes:d.notes||{},log:d.log||[]};
      /* נפתח בכרטיס הראשון שטרם נבחר */
      var first=ORDER.findIndex(function(k){return !decided(k)});IDX=first<0?0:first;render()}).catch(function(e){render();say('לא נטענו הבחירות: '+(e&&e.message||''),5000)})}
  })();
