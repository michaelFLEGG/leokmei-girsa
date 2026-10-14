  /* =================== סקירת קלוד בתוך הדף (13.10.2026) ===================
     נטען מיד אחרי bakara_ui.js ובאותו היקף: שדרוג מערכת הבקרה, לא מערכת מקבילה.
     מוסיף: חלונית ההערות לפי סוג עם מד התקדמות וסינון, דחייה מהירה עם סיבה,
     שוחח (שרשור), דלג, מקלדת, מסך מפוצל מול גמרא ופירוש או צורת הדף, בקשת סקירה
     לתור עם אומדן טוקנים, "מה למדתי", וייצוא לוורד (הערות וורד).
     גלוי למנהל בלבד: הכול נטען רק אחרי שהמכשיר הוכר ובקשות ה-API מוגנות במפתח. */
  const SK={tab:'notes',FIL:{typ:'',sev:'',conf:'',daf:'',st:'pend'},TH:{},LR:null,Q:null,rpt:{},
            split:(function(){try{return localStorage.getItem('lg-sk-split')||''}catch(e){return ''}})()};
  /* דילוג הוא החלטה ונשמר (14.10.2026): ההערה נדחית לסוף ואינה חוזרת במעבר הנוכחי */
  BK.SKIPKEY='lg-sk-skip-'+SLUG;
  BK.SKIP=new Set((function(){try{return JSON.parse(localStorage.getItem('lg-sk-skip-'+SLUG)||'[]')}catch(e){return []}})());
  function skSkipSave(){try{localStorage.setItem(BK.SKIPKEY,JSON.stringify(Array.from(BK.SKIP).slice(-800)))}catch(e){}}
  function skGet(path){return api(path)}
  function skPost(path,body,method){return api(path,{method:method||'POST',body:JSON.stringify(body)})}
  function skCss(){if(document.getElementById('skcss'))return;
    const st=document.createElement('style');st.id='skcss';
    st.textContent=
      '.skwhy{display:flex;gap:5px;flex-wrap:wrap;margin-top:6px}.skwhy button{font:inherit;font-size:13px;border:1px solid #c9a39e;border-radius:12px;background:#fff5f3;color:#a83c2f;padding:1px 9px;cursor:pointer}'+
      '.skchat{margin-top:6px;border-top:1px dotted #c9b98f;padding-top:5px}.skchat .m{font-size:13px;margin:3px 0;padding:3px 7px;border-radius:6px;background:#f3efe3}.skchat .m.c{background:#e9f0f8}'+
      '.skchat textarea{width:100%;box-sizing:border-box;font:inherit;font-size:14px;height:46px}.skchat .w{font-size:12px;color:#8a7d66}'+
      '#bkp .sktabs{display:flex;gap:4px;margin-bottom:6px}#bkp .sktabs button{flex:1;font:inherit;font-size:14px;border:1px solid #b9a97c;border-radius:5px;background:#f6f1e2;padding:3px 4px;cursor:pointer}'+
      '#bkp .sktabs button.on{background:#2e5b8a;color:#fff;border-color:#2e5b8a}'+
      '.skprog{height:6px;background:#e6dfcb;border-radius:3px;margin:3px 0 7px;overflow:hidden}.skprog i{display:block;height:100%;background:#2e6b3f}'+
      '.bkbar .sksrc{display:inline-flex;gap:3px;align-items:center;border-right:1px solid #c9b98f;padding-right:8px;margin-right:2px}.bkbar .sksrc button.on{background:#2e5b8a;color:#fff;border-color:#2e5b8a}'+
      '#bkp .skf label{display:block;margin:5px 0;font-size:14px}#bkp .skf input,#bkp .skf select,#bkp .skf textarea{font:inherit;font-size:14px;box-sizing:border-box}'+
      '#bkp .skrate{display:flex;align-items:center;gap:6px;margin:3px 0;font-size:13px}#bkp .skrate .bar{flex:1;height:9px;background:#eadfd9;border-radius:4px;overflow:hidden;display:flex}'+
      '#bkp .skrate .bar i{display:block;height:100%}#bkp .skrate .nm{width:92px}'+
      '@media print{.skchat,.skwhy{display:none!important}}';
    document.head.appendChild(st)}
  document.addEventListener('DOMContentLoaded',skCss);skCss();

  /* ---- דחייה מהירה עם סיבה ---- */
  window.skRejectOpen=function(id){
    const w=$('#skwhy');if(!w){bkDecide(id,'no');return}
    w.style.display=w.style.display==='none'?'flex':'none';
    if(w.style.display!=='none'){BK.kb=false;const i=$('#bkwhy');if(i&&!window.matchMedia('(hover:none)').matches)i.focus()}};
  window.skReject=function(id,code){
    const f=BK.byId[id];if(!f)return;
    const i=$('#bkwhy');
    if(code==='free'){if(!i||!i.value.trim())code='unspec'}
    BK.rs=code;
    const w=SKWHY.find(x=>x[0]===code);
    if(w&&i&&!i.value.trim())i.value=w[1];
    bkKbDecide(f,'no')};
  window.skSkip=function(id){
    if(!id)return;
    BK.SKIP.add(id);skSkipSave();
    const L=BK.loc[id];if(L){SK.last=id;SK.lastOrd=L.ord;BK.curId=id;skSavePos()}
    bkHideCard(true);if(!SK.mode)bkHL();bkAdvance()};

  /* ---- שוחח ---- */
  async function skThreadLoad(id){
    try{const r=await skGet('/skira/thread?slug='+SLUG+'&id='+id);SK.TH[id]=r.msgs||[]}catch(e){SK.TH[id]=SK.TH[id]||[]}}
  function skChatDraw(id){
    const box=$('#skchat');if(!box)return;
    const m=SK.TH[id]||[];
    box.innerHTML=m.map(x=>'<div class="m '+x.who+'"><b>'+(x.who==='m'?'אתה':'קלוד')+':</b> '+esc(x.txt)+'</div>').join('')+
      '<textarea id="skmsg" placeholder="כתוב לקלוד על ההערה (Ctrl+Enter לשליחה)" aria-label="הודעה"></textarea>'+
      '<div class="bt"><button class="ok" onmousedown="event.preventDefault()" onclick="skSend(\''+id+'\')">שלח</button>'+
      '<span class="w" id="skwait"></span></div>'}
  window.skChat=async function(id){
    const box=$('#skchat');if(!box)return;
    BK.pin=true;
    if(box.style.display!=='none'){box.style.display='none';return}
    box.style.display='block';BK.kb=false;
    skChatDraw(id);await skThreadLoad(id);skChatDraw(id);
    const t=$('#skmsg');if(t){t.focus();t.addEventListener('keydown',e=>{if(e.ctrlKey&&e.key==='Enter'){e.preventDefault();skSend(id)}e.stopPropagation()})}};
  window.skSend=async function(id){
    const t=$('#skmsg');if(!t||!t.value.trim())return;
    const f=BK.byId[id];const txt=t.value.trim();t.value='';
    try{
      const r=await skPost('/skira/thread',{slug:SLUG,id,who:'m',txt});SK.TH[id]=r.msgs||[];skChatDraw(id);
      const a=await skPost('/skira/ask',{note:(f.note||'')+' | '+(f.fix||''),ctx:(f.context||f.text||''),msgs:SK.TH[id]});
      if(a.immediate&&a.txt){const r2=await skPost('/skira/thread',{slug:SLUG,id,who:'c',txt:a.txt});SK.TH[id]=r2.msgs||[];skChatDraw(id)}
      else{const w=$('#skwait');if(w)w.textContent='התשובה תגיע בהרצה הבאה.'}
    }catch(e){toast('לא נשלח: '+(e.message||'שגיאה'),5000)}};

  /* ---- מסך מפוצל: הצד השמאלי עוקב אחרי ההערה הפעילה ---- */
  function skRefOf(f){
    const L=BK.loc[f.id];if(!L)return '';
    const el=$('#flow').querySelector('[data-ek="'+L.k+'"]');
    let row=el&&el.closest?el.closest('.row'):null;
    while(row&&!row.dataset.ref)row=row.previousElementSibling;
    return row?row.dataset.ref:''}
  const SKTAB=[['gp','גמרא ופירוש'],['tz','צורת הדף'],['g','גמרא בלבד']];
  function skHasTz(){return typeof tzOpen==='function'&&!!window.__TZMAN}
  window.skSplit=function(t){
    if(t==='off'){SK.split='';try{localStorage.setItem('lg-sk-split','')}catch(e){}
      if(typeof closeSrc==='function')try{closeSrc()}catch(e){}
      if(typeof tzClose==='function')try{tzClose()}catch(e){}
      bkBarDraw();return}
    SK.split=t;try{localStorage.setItem('lg-sk-split',t)}catch(e){}
    const f=BK.byId[BK.curId]||BK.ord[0];
    if(f)skAfterGo(f);else bkBarDraw()};
  window.skAfterGo=function(f){
    if(!SK.split||!f)return;
    const ref=skRefOf(f);if(!ref){bkBarDraw();return}
    try{
      if(SK.split==='tz'&&skHasTz()){
        if(typeof closeSrc==='function'&&document.getElementById('srcx'))closeSrc();
        tzOpen(ref)}
      else{
        if(typeof tzClose==='function'&&document.getElementById('tzx'))tzClose();
        SRCVIEW=SK.split==='g'?'gem':'both';SRCMODE='split';
        try{localStorage.setItem('lg-srcview',SRCVIEW);localStorage.setItem('lg-srcmode','split')}catch(e){}
        if(document.getElementById('srcx')&&SX&&SX.ref)srcGo(ref,true);else openSrc(ref)}
    }catch(e){}
    bkBarDraw()};
  window.skBarExtra=function(m){
    if(!m)return;
    const has=SKTAB.filter(x=>x[0]!=='tz'||skHasTz());
    m.insertAdjacentHTML('beforeend','<span class="sksrc"><span class="dim">מקור:</span>'+
      has.map(x=>'<button class="'+(SK.split===x[0]?'on':'')+'" onclick="skSplit(\''+x[0]+'\')">'+x[1]+'</button>').join('')+
      (SK.split?'<button onclick="skSplit(\'off\')" title="סגירת המסך המפוצל">×</button>':'')+'</span>'+
      '<button onclick="skTab(\'req\')" title="בקשת סקירה לטווח: הבדיקות המהירות מוכנות מיד">סקור עכשיו</button>')};

  /* ---- מקלדת: Enter קבל, Delete דחה, חצים, E ערוך, C שוחח, Ctrl+Z ביטול ---- */
  function skTyping(t){return t&&(t.isContentEditable||/^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName))}
  document.addEventListener('keydown',e=>{
    if(!BK.ON||e.ctrlKey||e.metaKey||e.altKey)return;
    if(skTyping(e.target))return;
    const c=e.code;
    const f=BK.byId[BK.curId];
    const pend=f&&(bkStatus(f)==='pending'||bkStatus(f)==='todo');
    if(c==='ArrowLeft'||c==='ArrowRight'){
      /* בעברית: שמאלה = ההערה הבאה, ימינה = הקודמת */
      e.preventDefault();e.stopPropagation();BK.kb=true;bkNext(c==='ArrowLeft'?1:-1);return}
    if(!f||!pend)return;
    if(c==='Enter'||c==='NumpadEnter'){
      if(e.target&&/^(BUTTON|A)$/.test(e.target.tagName))return;
      e.preventDefault();e.stopPropagation();bkKbDecide(f,'ok');return}
    if(c==='Delete'||c==='Backspace'){e.preventDefault();e.stopPropagation();if(SK.mode&&!e.shiftKey){BK.rs='';bkKbDecide(f,'no')}else skRejectOpen(f.id);return}
    if(c==='KeyE'){e.preventDefault();e.stopPropagation();bkDecide(f.id,'edit');return}
    if(c==='KeyC'){e.preventDefault();e.stopPropagation();skChat(f.id);return}
    if(c==='KeyS'){e.preventDefault();e.stopPropagation();skSkip(f.id);return}
  },true);

  /* ---- חלונית: הערות | בקש סקירה | מה למדתי ---- */
  window.skTab=function(t){
    SK.tab=t;
    if(!BK.ON)bkToggle();
    const p=$('#bkp');if(p&&!p.classList.contains('open'))panel('bkp');
    skDrawPanel()};
  function skDafs(){const o=[],seen={};(D.pages||[]).forEach((p,i)=>{const d=p.daf;if(d&&!seen[d]){seen[d]=1;o.push([d,i])}});return o}
  function skItem(f){const st=bkStatus(f),sn=bkSplitNote(f),dec=BK.DEC[f.id];
    const lab={ok:'התקבל',no:'נדחה',edit:'נערך',todo:'לביצוע'}[dec&&dec.d];
    return '<div class="it'+(f.id===BK.curId?' cur':'')+'" onclick="bkGo(\''+f.id+'\',true)"><small>'+esc(f.daf||'')+' · '+esc(f.sev||'')+(f.conf?' · '+esc(f.conf):'')+(st!=='pending'&&lab?' · '+lab:'')+(BK.SKIP.has(f.id)?' · נדחתה לסוף':'')+'</small> <span class="mk">'+esc((f.mark||'').slice(0,40))+'</span><br><small>'+esc(sn.n.slice(0,110))+'</small></div>'}
  function skNotesHtml(){
    const F=SK.FIL;
    const opt=(a,cur)=>a.map(o=>'<option value="'+esc(o[0])+'"'+(cur===o[0]?' selected':'')+'>'+esc(o[1])+'</option>').join('');
    const dafs=[['','כל הדפים']].concat(skDafs().map(x=>[x[0],'דף '+x[0]]));
    let h='<div class="skf"><select onchange="SK.FIL.st=this.value;skDrawPanel()">'+opt([['pend','שטרם הוכרעו'],['skipped','שדילגתי'],['todo','אושרו לביצוע'],['done','הוכרעו'],['all','הכל']],F.st)+'</select>'+
      '<select onchange="SK.FIL.typ=this.value;skDrawPanel()">'+opt([['','כל הסוגים']].concat(Object.keys(SKT).map(k=>[k,SKT[k][0]])),F.typ)+'</select>'+
      '<select onchange="SK.FIL.sev=this.value;skDrawPanel()">'+opt([['','כל החומרות'],['חמור','חמור'],['בינוני','בינוני'],['קל','קל']],F.sev)+'</select>'+
      '<select onchange="SK.FIL.conf=this.value;skDrawPanel()">'+opt([['','כל רמות הוודאות'],['גבוה','ודאי'],['בינוני','סביר'],['נמוך','ספק']],F.conf)+'</select>'+
      '<select onchange="SK.FIL.daf=this.value;skDrawPanel()">'+opt(dafs,F.daf)+'</select></div>';
    const pass=f=>{const st=bkStatus(f);
      if(F.st==='pend'&&(st!=='pending'||(SK.autoQ&&SK.autoQ.has(f.id))))return false;if(F.st==='todo'&&st!=='todo')return false;
      if(F.st==='skipped'&&!(st==='pending'&&BK.SKIP.has(f.id)))return false;
      if(F.st==='done'&&(st==='pending'||st==='todo'))return false;
      if(F.typ&&bkTyp(f)!==F.typ)return false;if(F.sev&&f.sev!==F.sev)return false;
      if(F.conf&&(f.conf||'')!==F.conf)return false;if(F.daf&&(f.daf||'').trim()!==F.daf)return false;return true};
    /* שאלה למחבר (סוג ח) אינה נספרת כממצא */
    const FL=BK.F.filter(f=>bkTyp(f)!=='h'),total=FL.length,pend=FL.filter(bkPend).length;
    h='<div class="edsum">נשארו '+pend+' מתוך '+total+' · <button onclick="bkNext(1)" class="b">להערה הבאה ↓</button></div>'+
      '<div class="skprog"><i style="width:'+(total?Math.round(100*(total-pend)/total):0)+'%"></i></div>'+h;
    const lost=BK.F.filter(f=>!BK.loc[f.id]&&pass(f));
    const groups={};BK.F.filter(f=>BK.loc[f.id]&&pass(f)).sort((a,b)=>BK.loc[a.id].ord-BK.loc[b.id].ord).forEach(f=>{(groups[bkTyp(f)]=groups[bkTyp(f)]||[]).push(f)});
    const keys=Object.keys(SKT).filter(k=>groups[k]);
    if(!keys.length&&!lost.length)h+='<div class="edsum">אין הערות בסינון הזה.</div>';
    for(const k of keys){const g=groups[k],pn=g.filter(bkPend).length;
      const dec=BK.F.filter(f=>bkTyp(f)===k&&BK.DEC[f.id]&&BK.DEC[f.id].d!=='pending');
      const ok=dec.filter(f=>/^(ok|todo|edit)$/.test(BK.DEC[f.id].d)).length;
      h+='<details class="grp"'+(k==='g'?'':' open')+'><summary><b style="color:'+SKT[k][1]+'">'+esc(SKT[k][0])+'</b> <span class="n">('+pn+' ממתינות מתוך '+g.length+')</span>'+(dec.length>=3?' <small>קבלה '+Math.round(100*ok/dec.length)+'%</small>':'')+'</summary><div class="gb">'+
        (pn?'<div class="gbt">'+(SKBULK[k]?'<button onclick="bkBulk(\'typ:'+k+'\',\'ok\')">קבל את כל הסוג</button>':'<span class="dim">בסוג הזה אין אישור גורף</span>')+'<button onclick="bkBulk(\'typ:'+k+'\',\'no\')">דחה את כל הסוג</button></div>':'')+
        g.map(skItem).join('')+'</div></details>'}
    /* סוג ט: נקודות "בחר נוסח" של בית החרושת, באותו ממשק (הבחירה עצמה נעשית בחלונית הנוסחאות הקיימת) */
    if(window.__ALTS&&window.__ALTS.items&&window.altGo&&(!F.typ||F.typ==='i')&&F.st!=='todo'){
      const al=window.__ALTS.items.filter(it=>{const dn=window.altDecided&&window.altDecided(it.id);
        return F.st==='all'||(F.st==='pend'?!dn:dn)}).filter(it=>!F.daf||(F.daf.replace(/[.:]/g,'')===String(it.daf||'').replace(/[.:]/g,'')));
      if(al.length)h+='<details class="grp" open><summary><b style="color:'+SKT.i[1]+'">'+SKT.i[0]+'</b> <span class="n">('+al.length+')</span></summary><div class="gb">'+
        al.map(it=>'<div class="it" onclick="altGo(\''+esc(it.id)+'\')"><small>דף '+esc(it.daf||'')+(window.altDecided(it.id)?' · הוכרע':'')+'</small><br><small>'+esc(((it.variants[0]||{}).text||'').replace(/[⟦⟧]/g,'').slice(0,110))+'</small></div>').join('')+'</div></details>'}
    if(lost.length)h+='<h3>שלא אותרו ('+lost.length+')</h3><div class="dim">הטקסט השתנה מאז הסקירה ולכן הן אינן בתוקף. אינן נתלות בשורה אחרת.</div>'+
      lost.map(f=>'<div class="it" onclick="bkShowLost(\''+f.id+'\')"><small>'+esc(f.daf||'')+' · '+esc(f.kind)+'</small> <span class="mk">'+esc((f.mark||'').slice(0,40))+'</span></div>').join('');
    h+='<div class="gbt" style="margin-top:8px"><button onclick="skExportDocx()">ייצוא ההערות הפתוחות לוורד</button></div>';
    return h}
  function skEst(depth,n){return depth==='full'?12000+35000*n:12000+9000*n}
  function skReqHtml(){
    const dafs=skDafs();const cd=bkDafNow();
    const opt=(sel)=>dafs.map(x=>'<option value="'+esc(x[0])+'"'+(x[0]===sel?' selected':'')+'>'+esc(x[0])+'</option>').join('');
    const R=SK.rpt;
    let h='<div class="skf"><b>בקשת סקירה</b><div class="dim">הבקשה נכנסת לתור. לא צריך לעשות דבר מעבר ללחיצה; ההערות יופיעו כאן בהרצה הבאה.</div>'+
      '<label>מדף <select id="skfrom" onchange="skEstDraw()">'+opt(R.from||cd)+'</select> עד <select id="skto" onchange="skEstDraw()">'+opt(R.to||cd)+'</select></label>'+
      '<div class="gbt"><button onclick="skPreset(\'daf\')">הדף הנוכחי</button><button onclick="skPreset(\'perek\')">הפרק הנוכחי</button><button onclick="skPreset(\'all\')">כל המסכת</button></div>'+
      '<label>עומק <select id="skdepth" onchange="skEstDraw()"><option value="fast">מהירה (קוד ומודל זול)</option><option value="full">מלאה (כולל השכבה הסמנטית החזקה)</option></select></label>'+
      '<label>הערה לסוקר (לא חובה) <input type="text" id="sknote" maxlength="300" style="width:100%"></label>'+
      '<div id="skest" class="dim"></div>'+
      '<div class="gbt"><button class="go" onclick="skQueueSend()">שלח לתור</button></div></div><div id="skqlist"></div>';
    return h}
  window.skPreset=function(w){
    const ds=skDafs();const cd=bkDafNow();
    if(w==='daf'){$('#skfrom').value=cd;$('#skto').value=cd}
    else if(w==='all'){if(ds.length){$('#skfrom').value=ds[0][0];$('#skto').value=ds[ds.length-1][0]}}
    else{const sec=SEC[cur]||{from:0,to:0};const a=D.pages[sec.from],b=D.pages[sec.to];if(a&&b){$('#skfrom').value=a.daf;$('#skto').value=b.daf}}
    skEstDraw()};
  window.skEstDraw=function(){
    const a=$('#skfrom'),b=$('#skto'),d=$('#skdepth'),e=$('#skest');if(!a||!e)return;
    const ds=skDafs().map(x=>x[0]),i=ds.indexOf(a.value),j=ds.indexOf(b.value);
    if(i<0||j<i){e.textContent='הטווח אינו תקין: "עד" חייב לבוא אחרי "מדף".';return}
    const n=(j-i+1)*1;SK.rpt={from:a.value,to:b.value};
    const est=skEst(d.value,n);
    e.innerHTML='אומדן: '+(n===1?'דף אחד':n+' דפים')+', עד כ-<b>'+est.toLocaleString('he-IL')+'</b> טוקנים (פסקה שלא השתנתה מאז הסקירה הקודמת אינה נשלחת, ולכן בפועל פחות).'};
  window.skQueueSend=async function(){
    const a=$('#skfrom'),b=$('#skto'),d=$('#skdepth');if(!a)return;
    const ds=skDafs().map(x=>x[0]),i=ds.indexOf(a.value),j=ds.indexOf(b.value);
    if(i<0||j<i){toast('הטווח אינו תקין.');return}
    const est=skEst(d.value,j-i+1);
    try{await skPost('/skira/queue',{slug:SLUG,from:a.value,to:b.value,depth:d.value,note:($('#sknote')||{}).value||'',est});
      toast('הבקשה נרשמה בתור. ההערות יופיעו בהרצה הבאה.',5000);await skQLoad();skDrawPanel()}
    catch(e){toast('הבקשה לא נשלחה: '+(e.message||'שגיאה'),6000)}};
  async function skQLoad(){try{const r=await skGet('/skira/queue');SK.Q=(r.doc&&r.doc.items)||[]}catch(e){SK.Q=SK.Q||[]}}
  function skQHtml(){
    const L=(SK.Q||[]).filter(x=>x.slug===SLUG).slice(-8).reverse();
    if(!L.length)return '';
    const nm={pending:'ממתינה',running:'רצה',done:'הושלמה',failed:'נכשלה',cancelled:'בוטלה'};
    return '<h3>בקשות אחרונות</h3>'+L.map(x=>'<div class="it" style="cursor:default"><small>'+esc(x.from)+' עד '+esc(x.to)+' · '+(x.depth==='full'?'מלאה':'מהירה')+' · '+(nm[x.status]||x.status)+'</small>'+(x.result?'<br><small>'+esc(x.result)+'</small>':'')+'</div>').join('')}
  function skLearnHtml(){
    /* שיעורי קבלה לכל סוג מההכרעות הקיימות, וכללים מ-/skira/learned */
    const by={};
    for(const f of BK.F){const d=BK.DEC[f.id];if(!d||d.d==='pending')continue;
      const t=bkTyp(f),s=by[t]||(by[t]={ok:0,no:0,edit:0});
      if(d.d==='no')s.no++;else if(d.d==='edit')s.edit++;else s.ok++}
    let h='<div class="skf"><b>מה למדתי מהכרעותיך</b><div class="dim">כלל נכנס לתוקף בלי אישור; לכל כלל יש "בטל".</div></div>';
    const ks=Object.keys(by);
    if(ks.length)h+=ks.map(k=>{const s=by[k],n=s.ok+s.no+s.edit;
      return '<div class="skrate"><span class="nm" style="color:'+SKT[k][1]+'">'+esc(SKT[k][0])+'</span><span class="bar"><i style="width:'+(100*s.ok/n)+'%;background:#2e6b3f"></i><i style="width:'+(100*s.edit/n)+'%;background:#c9a24a"></i><i style="width:'+(100*s.no/n)+'%;background:#b3261e"></i></span><span>'+Math.round(100*(s.ok+s.edit)/n)+'% מתוך '+n+'</span></div>'}).join('')+
      '<div class="dim">ירוק: התקבל · זהב: נערך · אדום: נדחה</div>';
    else h+='<div class="edsum">עדיין אין הכרעות בסקירה הזאת.</div>';
    const LR=SK.LR;
    if(LR&&LR.rates&&LR.rates.runs&&LR.rates.runs.length){
      h+='<h3>קבלה לפי הרצה</h3>'+LR.rates.runs.slice(-6).map(r=>'<div class="skrate"><span class="nm">'+esc(r.date||'')+'</span><span class="bar"><i style="width:'+Math.round(100*(r.acc||0))+'%;background:#2e6b3f"></i></span><span>'+Math.round(100*(r.acc||0))+'% מתוך '+(r.n||0)+'</span></div>').join('')}
    if(LR&&LR.rates&&LR.rates.mech&&LR.rates.mech.length)h+='<h3>מועמדים למנוע המכני</h3>'+LR.rates.mech.map(x=>'<div class="it" style="cursor:default">'+esc(x)+'</div>').join('');
    const R=(LR&&LR.rules)||[];
    h+='<h3>כללים שנלמדו ('+R.length+')</h3>'+(R.length?R.map(r=>{const off=LR.off&&LR.off[r.id];
      return '<div class="it" style="cursor:default'+(off?';opacity:.55':'')+'"><b>'+esc(r.id)+'</b> <small>('+(r.n||0)+' הכרעות'+(r.src?' · '+esc(r.src):'')+')</small><br>'+esc(r.text||'')+
        (r.ex?'<br><small>'+esc(r.ex)+'</small>':'')+'<br><button onclick="skRuleOff(\''+esc(r.id)+'\','+(off?0:1)+')">'+(off?'החזר':'בטל')+'</button></div>'}).join(''):'<div class="edsum">עדיין לא נלמדו כללים.</div>');
    return h}
  window.skRuleOff=async function(id,off){
    try{const r=await skPost('/skira/learned',{id,off:!!off});SK.LR=r.doc;skDrawPanel()}catch(e){toast('לא נשמר: '+(e.message||''),5000)}};
  async function skLrLoad(){try{const r=await skGet('/skira/learned');SK.LR=r.doc}catch(e){}}
  window.skDrawPanel=function(){
    const box=$('#bkpb');if(!box)return;
    const T=[['notes','הערות'],['req','סקור עכשיו'],['auto','תוקן אוטומטית'],['learn','מה למדתי']];
    let h=(window.skHeadHtml?skHeadHtml():'')+'<div class="sktabs">'+T.map(t=>'<button class="'+(SK.tab===t[0]?'on':'')+'" onclick="skTab(\''+t[0]+'\')">'+t[1]+'</button>').join('')+'</div>';
    if(SK.tab==='auto')h+=skAutoHtml();
    else if(SK.tab==='notes')h+=(window.skTypesHtml?skTypesHtml():'')+skNotesHtml();
    else if(SK.tab==='req'){h+=skReqNowHtml()+skQHtml();
      if(SK.Q===null)skQLoad().then(()=>{if(SK.tab==='req')skDrawPanel()})}
    else{h+=skLearnHtml();if(SK.LR===null)skLrLoad().then(()=>{if(SK.tab==='learn')skDrawPanel()})}
    box.innerHTML=h;
    if(SK.tab==='req')skEstDraw()};
  SK.LR=null;SK.Q=null;

  /* ---- ייצוא לוורד: docx עם הערות וורד צמודות לטקסט (אריזה ללא דחיסה, בלי ספרייה) ---- */
  const SKCRC=(function(){const t=new Uint32Array(256);for(let n=0;n<256;n++){let c=n;for(let k=0;k<8;k++)c=c&1?0xEDB88320^(c>>>1):c>>>1;t[n]=c>>>0}return t})();
  function skCrc(b){let c=0xFFFFFFFF;for(let i=0;i<b.length;i++)c=SKCRC[(c^b[i])&255]^(c>>>8);return (c^0xFFFFFFFF)>>>0}
  function skZip(files){
    const enc=new TextEncoder(),parts=[],cen=[];let off=0;
    const u16=v=>[v&255,(v>>8)&255],u32=v=>[v&255,(v>>8)&255,(v>>16)&255,(v>>>24)&255];
    for(const f of files){
      const nm=enc.encode(f.n),d=enc.encode(f.d),crc=skCrc(d);
      const lh=new Uint8Array([0x50,0x4b,3,4,20,0,0,8,0,0,0,0,0,0,...u32(crc),...u32(d.length),...u32(d.length),...u16(nm.length),0,0]);
      parts.push(lh,nm,d);
      cen.push(new Uint8Array([0x50,0x4b,1,2,20,0,20,0,0,8,0,0,0,0,0,0,...u32(crc),...u32(d.length),...u32(d.length),...u16(nm.length),0,0,0,0,0,0,0,0,0,0,0,0,...u32(off)]),nm);
      off+=lh.length+nm.length+d.length}
    const cs=cen.reduce((a,x)=>a+x.length,0);
    const end=new Uint8Array([0x50,0x4b,5,6,0,0,0,0,...u16(files.length),...u16(files.length),...u32(cs),...u32(off),0,0]);
    return new Blob(parts.concat(cen,[end]),{type:'application/vnd.openxmlformats-officedocument.wordprocessingml.document'})}
  function skX(t){return String(t).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;')}
  window.skExportDocx=function(){
    const sec=SEC[cur]||{from:0,to:0};
    const list=BK.F.filter(f=>bkPend(f)&&BK.loc[f.id]).sort((a,b)=>BK.loc[a.id].ord-BK.loc[b.id].ord);
    if(!list.length){toast('אין הערות פתוחות לייצוא.');return}
    const W='xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"';
    let body='',cm='';
    list.forEach((f,i)=>{
      const L=BK.loc[f.id],ctx=(L.s.t||'');
      const a=Math.max(0,L.pos),mk=(f.mark||'').trim();
      const idx=mk?ctx.indexOf(mk):-1;
      const pre=idx>-1?ctx.slice(0,idx):ctx,mid=idx>-1?mk:'',post=idx>-1?ctx.slice(idx+mk.length):'';
      const lab='['+f.id+'] '+SKT[bkTyp(f)][0]+' · '+(f.sev||'')+(f.conf?' · '+f.conf:'')+': '+bkSplitNote(f).n+(f.fix?' | הצעה: '+f.fix:'');
      body+='<w:p><w:pPr><w:bidi/></w:pPr><w:r><w:rPr><w:rtl/></w:rPr><w:t xml:space="preserve">'+skX('דף '+(f.daf||'')+' · ')+'</w:t></w:r>'+
        '<w:r><w:rPr><w:rtl/></w:rPr><w:t xml:space="preserve">'+skX(pre)+'</w:t></w:r>'+
        (mid?'<w:commentRangeStart w:id="'+i+'"/><w:r><w:rPr><w:rtl/><w:b/></w:rPr><w:t xml:space="preserve">'+skX(mid)+'</w:t></w:r><w:commentRangeEnd w:id="'+i+'"/><w:r><w:commentReference w:id="'+i+'"/></w:r>':
          '<w:commentRangeStart w:id="'+i+'"/><w:commentRangeEnd w:id="'+i+'"/><w:r><w:commentReference w:id="'+i+'"/></w:r>')+
        '<w:r><w:rPr><w:rtl/></w:rPr><w:t xml:space="preserve">'+skX(post)+'</w:t></w:r></w:p>';
      cm+='<w:comment w:id="'+i+'" w:author="סקירת קלוד" w:initials="סק"><w:p><w:r><w:t xml:space="preserve">'+skX(lab)+'</w:t></w:r></w:p></w:comment>'});
    const files=[
      {n:'[Content_Types].xml',d:'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/comments.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"/></Types>'},
      {n:'_rels/.rels',d:'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>'},
      {n:'word/_rels/document.xml.rels',d:'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments" Target="comments.xml"/></Relationships>'},
      {n:'word/document.xml',d:'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document '+W+'><w:body>'+body+'<w:p><w:r><w:rPr><w:vanish/></w:rPr><w:t xml:space="preserve">SKIRA-IDS '+list.map(f=>f.id).join(' ')+'</w:t></w:r></w:p><w:sectPr/></w:body></w:document>'},
      {n:'word/comments.xml',d:'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:comments '+W+'>'+cm+'</w:comments>'}];
    const blob=skZip(files),u=URL.createObjectURL(blob),a=document.createElement('a');
    a.href=u;a.download='סקירה - '+SLUG+' - '+new Date().toISOString().slice(0,10)+'.docx';document.body.appendChild(a);a.click();a.remove();
    setTimeout(()=>URL.revokeObjectURL(u),4000);
    toast('יוצאו '+list.length+' הערות. הכרעות בוורד נקלטות כשהקובץ חוזר לדרייב.',6000)};
