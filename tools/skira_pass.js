  /* =================== סקירה חכמה (14.10.2026) ===================
     נטען אחרי skira_ui.js ובאותו היקף. מוסיף:
     א. מעבר אחד קדימה: "הבא בתור" הוא תמיד ההערה שאחרי הנוכחית; דילוג נשמר ונדחה לסוף.
     ב. מעבר מהיר לפי סוג (אשר, אשר, אשר): הסבר קבוע, כרטיס מינימלי, מקלדת, גורף עם רשימה וביטול.
     ג. תיקון אוטומטי: ציטוט פסוק שהמנוע הוכיח, וחזרה על חתימה או סוג שהמחבר כבר הכריע בו עקבית.
     ד. סקירה לפי בקשה כאן ועכשיו: פס מצב, התקדמות לפי דף, הודעה על הערות שנוספו.
     ה. יומן "תוקן אוטומטית" עם ביטול, ועזרה מובנית. */
  Object.assign(SK,{mode:'',scope:'all',last:'',lastOrd:null,pool:null,end:null,list:false,rng:null,
                    autoQ:new Set(),behind:new Set(),batch:null,passIds:[],bulk:null,helpOn:false,autoOff:{},undoRec:{}});
  const SKORDER=['g','f','e','d','i','h','c','b','a'];
  const SKEXP={g:'תיקון מכני - אין בו שיקול דעת תוכני',f:'מבנה הדף - ציוני דף, מספור וסדר',e:'ניסוח וסגנון',d:'כותרות',
               i:'בחירת נוסח',h:'שאלה שמופנית אליך',c:'מקום שאינו מובן',b:'שלב חסר בהסבר',a:'טעות בפשט'};
  const SKACT={rep:'החלפה בנוסח המוצע',am:'החלת סגנון: המילים המסומנות יקבלו סגנון אמוראים',
               plain:'חזרה לסגנון רגיל: הסגנון המיוחד יוסר מן המילים המסומנות',instr:'הוראה: עריכה ממוקדת על הקטע, הסמן יעמוד עליו'};
  const SKPOS='lg-sk-pos-'+SLUG,SKUNDO='lg-sk-undo-'+SLUG,SKOFF='lg-sk-autooff-'+SLUG;
  function skLs(k,d){try{return JSON.parse(localStorage.getItem(k)||'null')||d}catch(e){return d}}
  function skLsSet(k,v){try{localStorage.setItem(k,JSON.stringify(v))}catch(e){}}
  SK.undoRec=skLs(SKUNDO,{});SK.autoOff=skLs(SKOFF,{});

  /* ---- מיקום במעבר: נשמר לכל סוג, וחוזר מאותה נקודה ---- */
  function skSavePos(){const o=skLs(SKPOS,{});o[SK.mode||'_']=SK.last||'';skLsSet(SKPOS,o)}
  window.skSavePos=skSavePos;
  (function(){const o=skLs(SKPOS,{});if(o._&&!SK.last)SK.last=o._})();

  function skInScope(f){
    if(!SK.mode||SK.scope==='all')return true;
    const L=BK.loc[f.id];if(!L)return false;
    const sec=SEC[cur]||{from:0,to:0};return L.pi>=sec.from&&L.pi<=sec.to}
  function skInRng(f){
    if(!SK.rng)return true;
    const k=dafKey(f.daf);if(k===null||k===undefined)return false;
    return k>=SK.rng.a&&k<=SK.rng.b}
  function skPendRaw(f){return bkStatus(f)==='pending'&&!SK.autoQ.has(f.id)&&BK.loc[f.id]}
  function skCands(){
    return BK.ord.filter(f=>skPendRaw(f)&&skInScope(f)&&skInRng(f)&&(!SK.mode||f.det===SK.mode)&&
      (SK.pool?SK.pool.has(f.id):!BK.SKIP.has(f.id)))}

  /* ---- הבא בתור ---- */
  window.skNext=function(dir){
    const co=bkCurOrd();
    if(dir<0){
      const P=BK.ord.filter(f=>skPendRaw(f)&&skInScope(f)&&skInRng(f)&&(!SK.mode||f.det===SK.mode)&&BK.loc[f.id].ord<co);
      if(P.length)skShow(P[P.length-1]);else toast('זו ההערה הראשונה.');
      return}
    const pick=skCands().find(f=>BK.loc[f.id].ord>co);
    if(pick){SK.end=null;skShow(pick);return}
    skEndOfPass()};
  function skShow(f){
    if(SK.mode)bkHideCard(true);
    bkGo(f.id,!SK.mode)}
  function skEndOfPass(){
    const base=BK.ord.filter(f=>skPendRaw(f)&&(!SK.mode||f.det===SK.mode)&&skInRng(f)&&skInScope(f));
    const was=SK.pool;
    const skipped=base.filter(f=>BK.SKIP.has(f.id)&&!(was&&was.has(f.id)&&false));
    const behind=Array.from(SK.behind).filter(id=>BK.byId[id]&&bkStatus(BK.byId[id])==='pending');
    SK.pool=null;
    if(!skipped.length&&!behind.length){SK.end={done:true};toast('סיימת את המעבר. אין הערות שממתינות.',4000)}
    else SK.end={skipped:skipped.map(f=>f.id),behind};
    skBarRedraw()}
  window.skEndAnswer=function(kind,yes){
    const e=SK.end;if(!e)return;
    const ids=e[kind]||[];
    if(!yes){SK.end={done:true,kept:ids.length,kind};if(kind==='behind')SK.behind.clear();skBarRedraw();
      toast(kind==='skipped'?'ההערות שדילגת עליהן שמורות בלשונית "שדילגתי".':'ההערות שנוספו שמורות ברשימה.',4000);return}
    SK.pool=new Set(ids);SK.end=null;BK.curId='';SK.last='';SK.lastOrd=-1;SK.fromTop=true;
    if(kind==='behind')SK.behind.clear();
    skNext(1)};
  function skEndTxt(kind,n){
    if(kind==='skipped')return n===1?'נותרה הערה אחת שדילגת עליה - לעבור עליה עכשיו?':'נותרו '+n+' הערות שדילגת עליהן - לעבור עליהן עכשיו?';
    return n===1?'נוספה הערה אחת בדפים שכבר עברת - לעבור?':'נוספו '+n+' הערות בדפים שכבר עברת - לעבור?'}
  function skBarRedraw(){if(SK.mode)skPassDraw();else bkBarDraw()}

  /* ---- כפתור "הבא בתור": תמיד באותו מקום, ותמיד כתוב עליו מה קורה ---- */
  function skActiveReq(){
    const L=(SK.Q||[]).filter(x=>x.slug===SLUG&&x.prio!=='prefetch'&&(x.status==='pending'||x.status==='running'));
    return L.length?L[L.length-1]:null}
  function skWaitText(q){
    const p=q.prog||{};
    if(q.status==='pending')return 'ממתין לתחילת בדיקת התוכן (הבקשה בתור)';
    if(p.next)return 'ממתין לבדיקת התוכן של דף '+p.next+(p.eta?' - כ'+p.eta+' דקות':' - כדקה');
    return 'בדיקת התוכן בעבודה - ההערות יופיעו כאן מיד'}
  function skNextInfo(){
    const co=bkCurOrd();
    const n=skCands().filter(f=>BK.loc[f.id].ord>co).length;
    if(n)return {t:'הבא בתור ('+n+')',on:1};
    const q=skActiveReq();
    if(q)return {t:skWaitText(q),on:0,wait:1};
    if(SK.end&&!SK.end.done)return {t:'סוף המעבר - ראה למטה',on:0};
    return {t:'אין עוד הערות',on:0}}
  window.skNextBtnHtml=function(){
    const i=skNextInfo();
    return '<button class="go sknx'+(i.on?'':' idle')+'" id="sknext" onclick="skNextClick()" title="ההערה הבאה אחרי הנוכחית, לפי סדר הטקסט (Alt+חץ למטה)">'+esc(i.t)+(i.on?' ↓':'')+'</button>'};
  window.skNextClick=function(){
    const i=skNextInfo();
    if(i.on){bkNext(1);return}
    if(i.wait){toast(i.t,5000);return}
    bkNext(1)};

  /* ---- פס מצב וחלונית ---- */
  function skReqCount(q){
    const a=dafKey(q.from),b=dafKey(q.to);
    return BK.F.filter(f=>{const k=dafKey(f.daf);return k!==null&&k>=a&&k<=b&&f.layer==='קוד'}).length}
  function skReqPend(q){
    const a=dafKey(q.from),b=dafKey(q.to);
    return BK.F.filter(f=>{const k=dafKey(f.daf);return k!==null&&k>=a&&k<=b&&f.layer==='קוד'&&bkStatus(f)==='pending'}).length}
  function skContentCount(q){
    const a=dafKey(q.from),b=dafKey(q.to);
    return BK.F.filter(f=>{const k=dafKey(f.daf);return k!==null&&k>=a&&k<=b&&f.layer==='מודל'}).length}
  function skStatusText(){
    const L=(SK.Q||[]).filter(x=>x.slug===SLUG&&x.prio!=='prefetch');
    if(!L.length)return '';
    const q=skActiveReq()||L[L.length-1];
    if(!skActiveReq()&&(q.t2||q.t||0)<Date.now()-86400000)return '';
    const nm='סקירת דפים '+q.from+' עד '+q.to;
    const nq=skReqCount(q),np=skReqPend(q);
    const quick='בדיקות מהירות - מוכן ('+nq+' הערות'+(np<nq?', מהן '+np+' ממתינות להכרעה':'')+')';
    if(q.status==='pending')return nm+': '+quick+'. בדיקת תוכן - ממתינה בתור, עדיין לא התחילה.';
    if(q.status==='running'){
      const p=q.prog||{};
      return nm+': '+quick+'. בדיקת תוכן - בעבודה'+(p.total?', הושלמו '+(p.done||0)+' דפים מתוך '+p.total:'')+(p.eta?', צפי לסיום כ-'+p.eta+' דקות':'')+'.'}
    if(q.status==='done')return nm+': '+quick+'. בדיקת התוכן הושלמה ('+skContentCount(q)+' הערות תוכן).'+(q.result?' '+q.result:'');
    if(q.status==='failed')return nm+': בדיקת התוכן נכשלה. '+(q.result||'');
    return ''}
  window.skHeadHtml=function(){
    const st=skStatusText();
    return '<div class="skhead"><b>סקירת קלוד</b><button class="skqm" onclick="skHelp()" title="עזרה" aria-label="עזרה">?</button></div>'+
      (SK.helpOn?'<div class="skhelp">'+
        '<b>איך עובדים</b><br>1. "סקור עכשיו": בוחרים טווח דפים ולוחצים. הבדיקות המהירות מוכנות מיד; בדיקת התוכן מתקדמת דף אחרי דף ומצטרפת לתור לבד.<br>'+
        '2. "הבא בתור": כפתור אחד שמביא את ההערה שאחרי הנוכחית. אם אין עכשיו הערה, כתוב עליו על מה מחכים.<br>'+
        '3. "מעבר לפי סוג": לוחצים על סוג (למשל החלת סגנון) ועוברים עליו ברצף: Enter מקבל ועובר, Delete דוחה, E עורך, C משוחח, חץ ימינה מדלג.<br>'+
        '4. מה שדילגת עליו נדחה לסוף ולא חוזר באמצע.<br>'+
        '5. מה שתוקן לבד, ומה שהוכרע בעקבות החלטות קודמות שלך, רשום בלשונית "תוקן אוטומטית" ולכל שורה יש "בטל".</div>':'')+
      '<div class="skstat" id="skstat">'+(st?esc(st):'אין בקשת סקירה פעילה. אפשר לבקש בלשונית "סקור עכשיו".')+'</div>'};
  window.skHelp=function(){SK.helpOn=!SK.helpOn;skDrawPanel()};

  /* ---- סוגי הערות ומעבר לפי סוג ---- */
  function skDetCounts(){
    const o={};
    const sec=SEC[cur]||{from:0,to:0};
    for(const f of BK.ord){
      if(!skPendRaw(f)||!skInRng(f))continue;
      if(SK.scope!=='all'){const L=BK.loc[f.id];if(!(L.pi>=sec.from&&L.pi<=sec.to))continue}
      const x=o[f.det]||(o[f.det]={n:0,typ:bkTyp(f),kind:f.kind,sk:0});
      x.n++;if(BK.SKIP.has(f.id))x.sk++}
    return o}
  function skDetLabel(det,x){return x.kind||(BK.CAT[det]&&BK.CAT[det][1])||det}
  window.skTypesHtml=function(){
    const c=skDetCounts();
    const ks=Object.keys(c).sort((a,b)=>SKORDER.indexOf(c[a].typ)-SKORDER.indexOf(c[b].typ)||c[b].n-c[a].n);
    const tot=ks.reduce((a,k)=>a+c[k].n,0);
    let h='<div class="skf"><b>מעבר מהיר לפי סוג</b> <span class="dim">('+tot+' הערות '+(SK.scope==='all'?'בכל המסכת':'בפרק הפתוח')+')</span>'+
      '<div class="gbt"><button onclick="SK.scope=\''+(SK.scope==='all'?'perek':'all')+'\';skDrawPanel()">'+(SK.scope==='all'?'הצג רק את הפרק הפתוח':'הצג את כל המסכת')+'</button></div>';
    if(!ks.length)h+='<div class="edsum">אין הערות ממתינות '+(SK.scope==='all'?'':'בפרק הזה ')+'לעבור עליהן.</div>';
    h+='<div class="sktypes">'+ks.map(k=>'<button class="sktype" style="border-color:'+SKT[c[k].typ][1]+'" onclick="skPass(\''+k+'\')">'+
        '<span style="color:'+SKT[c[k].typ][1]+'">'+esc(skDetLabel(k,c[k]))+'</span> <b>'+c[k].n+'</b></button>').join('')+'</div></div>';
    return h};

  window.skPass=function(det){
    if(!BK.ON)bkToggle();
    SK.mode=det;SK.pool=null;SK.end=null;SK.list=false;SK.bulk=null;SK.batch=SK.batch&&SK.batch.mode===det?SK.batch:null;
    const o=skLs(SKPOS,{});SK.last=o[det]||'';
    const f0=BK.byId[SK.last];SK.lastOrd=f0&&BK.loc[f0.id]?BK.loc[f0.id].ord:-1;SK.fromTop=true;BK.curId='';
    SK.passIds=BK.ord.filter(f=>(f.det===det)&&BK.loc[f.id]&&skInScope(f)&&skInRng(f)&&(bkStatus(f)==='pending'&&!SK.autoQ.has(f.id)))
      .map(f=>f.id);
    bkHideCard(true);const bb=$('#bkbar');if(bb)bb.style.display='none';
    const p=$('#bkp');if(p&&p.classList.contains('open'))panel('bkp');
    skNext(1);
    if(!SK.passIds.length)skPassDraw()};
  window.skPassExit=function(){
    SK.mode='';SK.list=false;SK.bulk=null;SK.pool=null;SK.passIds=[];
    const x=$('#skpass');if(x)x.remove();
    const bb=$('#bkbar');if(bb)bb.style.display='';
    bkRefresh()};
  function skDiffHtml(f){
    const rp=bkRep(f),c=f.context||f.text||'',m=f.mark||'';
    if(rp){
      const i=c.indexOf(rp.x);
      if(i>-1)return esc(c.slice(0,i))+'<del>'+esc(rp.x)+'</del> <b>⟵</b> <ins>'+esc(rp.y)+'</ins>'+esc(c.slice(i+rp.x.length));
      return '<del>'+esc(rp.x)+'</del> <b>⟵</b> <ins>'+esc(rp.y)+'</ins>'}
    const i=m?c.indexOf(m):-1;
    const before=i>-1?esc(c.slice(0,i))+'<mark>'+esc(m)+'</mark>'+esc(c.slice(i+m.length)):esc(c)+(m?' <mark>'+esc(m)+'</mark>':'');
    return before+(f.fix?'<div class="skfix">'+esc(f.fix)+'</div>':'')}
  window.skPassDraw=function(){
    if(!SK.mode)return;
    {const m=$('#skmsg');if(m&&m.value&&document.activeElement===m)return}
    let el=$('#skpass');
    if(!el){el=document.createElement('div');el.id='skpass';el.className='skpass';document.body.appendChild(el)}
    const bb=$('#bkbar');if(bb)bb.style.display='none';
    const f=BK.byId[BK.curId];
    const done=SK.passIds.filter(id=>!(bkStatus(BK.byId[id]||{id:id})==='pending')||BK.SKIP.has(id)).length;
    const total=SK.passIds.length;
    const info=skNextInfo();
    let det=SK.mode,typ='g',kind=SK.mode;
    const any=BK.F.find(x=>x.det===SK.mode);if(any){typ=bkTyp(any);kind=any.kind}
    const idx=f?SK.passIds.indexOf(f.id):-1;
    const pend=f&&bkStatus(f)==='pending';
    let h='<div class="skph"><span class="bkchip" style="background:'+SKT[typ][1]+'">'+esc(kind)+'</span> '+
      '<span class="skexp">'+esc(SKEXP[typ]||'')+(f?' · '+esc(SKACT[bkAction(f)]):'')+'</span>'+
      (SK.autoOff[SK.mode]?' <span class="dim">הסוג הזה אינו מוחל לבד (בוטל בידך)</span>':'')+
      '<span class="skcnt">'+(total?((idx>-1?idx+1:Math.min(done+1,total))+' מתוך '+total):'0')+' בסוג</span>'+
      '<button class="x" onclick="skPassExit()" title="יציאה מהמעבר לפי סוג" aria-label="יציאה">×</button></div>';
    if(SK.bulk)h+=skBulkHtml();
    else if(SK.list)h+=skListHtml();
    else if(f){
      h+='<div class="skdiff">'+skDiffHtml(f)+'</div>'+
        '<div class="skmeta">'+esc(f.daf?'דף '+f.daf:'')+(f.sev?' · '+esc(f.sev):'')+(BK.SKIP.has(f.id)?' · נדחתה לסוף':'')+' · '+esc(bkSplitNote(f).n.slice(0,140))+'</div>';
      if(pend)h+='<div class="bt">'+
        '<button class="ok" onmousedown="event.preventDefault()" onclick="skPassDo(\'ok\')">קבל <small class="kk">Enter</small></button>'+
        '<button class="no" onmousedown="event.preventDefault()" onclick="skPassDo(\'no\')">דחה <small class="kk">Del</small></button>'+
        '<button onmousedown="event.preventDefault()" onclick="skPassDo(\'edit\')">ערוך וקבל <small class="kk">E</small></button>'+
        '<button onmousedown="event.preventDefault()" onclick="skChat(\''+f.id+'\')">שוחח <small class="kk">C</small></button>'+
        '<button onmousedown="event.preventDefault()" onclick="skSkip(\''+f.id+'\')">דלג <small class="kk">S</small></button>'+
        '<button onmousedown="event.preventDefault()" onclick="bkNext(-1)">הקודמת</button>'+
        '</div><div id="skchat" class="skchat" style="display:none"></div>';
    }else h+='<div class="skmeta">'+(total?'אין הערה נוכחית.':'אין הערות מסוג זה.')+'</div>';
    const left=SK.passIds.filter(id=>{const g=BK.byId[id];return g&&bkStatus(g)==='pending'&&!SK.autoQ.has(id)}).length;
    h+='<div class="bt skfoot"><button class="go sknx'+(info.on?'':' idle')+'" onclick="skNextClick()">'+esc(info.t)+(info.on?' ↓':'')+'</button>'+
      '<button onclick="skBulkOpen()"'+(SKBULK[typ]&&left?'':' disabled title="'+(SKBULK[typ]?'אין נותרים':'בסוג הזה אין אישור גורף: כל הערה בנפרד')+'"')+'>קבל את כל הנותרים ('+left+')</button>'+
      '<button onclick="SK.list=!SK.list;SK.bulk=null;skPassDraw()">'+(SK.list?'חזרה לכרטיס':'רשימה')+'</button>'+
      (SK.batch&&SK.batch.recs&&SK.batch.recs.length?'<button onclick="skBatchUndo()">בטל את האישור הגורף ('+SK.batch.recs.length+')</button>':'')+
      '</div>';
    if(SK.end&&!SK.end.done){
      const e=SK.end;
      h+='<div class="skend">'+
        (e.skipped&&e.skipped.length?'<div>'+skEndTxt('skipped',e.skipped.length)+' <button class="go" onclick="skEndAnswer(\'skipped\',1)">כן</button><button onclick="skEndAnswer(\'skipped\',0)">לא</button></div>':'')+
        (e.behind&&e.behind.length?'<div>'+skEndTxt('behind',e.behind.length)+' <button class="go" onclick="skEndAnswer(\'behind\',1)">כן</button><button onclick="skEndAnswer(\'behind\',0)">לא</button></div>':'')+
        '</div>'}
    else if(SK.end&&SK.end.done){
      h+='<div class="skend">'+(SK.end.kept?'נשארו '+SK.end.kept+' הערות שמורות בלשונית "שדילגתי".':'סיימת את הסוג הזה.')+
        ' <button onclick="skNextType()">לעבור לסוג הבא?</button></div>'}
    el.innerHTML=h;
    if(window.skChatRestore)skChatRestore()};
  window.skBarEnd=function(m){
    if(SK.end&&!SK.end.done){
      const e=SK.end;
      m.insertAdjacentHTML('beforeend','<span class="skendbar">'+
        (e.skipped&&e.skipped.length?skEndTxt('skipped',e.skipped.length)+' <button class="go" onclick="skEndAnswer(\'skipped\',1)">כן</button><button onclick="skEndAnswer(\'skipped\',0)">לא</button> ':'')+
        (e.behind&&e.behind.length?skEndTxt('behind',e.behind.length)+' <button class="go" onclick="skEndAnswer(\'behind\',1)">כן</button><button onclick="skEndAnswer(\'behind\',0)">לא</button>':'')+
        '</span>')}
    const st=skStatusText();
    if(st&&skActiveReq())m.insertAdjacentHTML('beforeend','<div class="skbarstat">'+esc(st)+'</div>')};
  window.skNextType=function(){
    const c=skDetCounts();
    const ks=Object.keys(c).filter(k=>k!==SK.mode).sort((a,b)=>SKORDER.indexOf(c[a].typ)-SKORDER.indexOf(c[b].typ)||c[b].n-c[a].n);
    if(!ks.length){toast('אין עוד סוגים עם הערות ממתינות. סיימת.',4000);skPassExit();return}
    skPass(ks[0])};
  window.skPassDo=function(d){
    const f=BK.byId[BK.curId];if(!f||bkStatus(f)!=='pending')return;
    if(d==='no'){BK.rs='';bkKbDecide(f,'no');return}
    if(d==='edit'){bkDecide(f.id,'edit');return}
    bkKbDecide(f,'ok')};

  /* ---- רשימה (טבלה גלולה) ---- */
  function skListHtml(){
    const L=SK.passIds.map(id=>BK.byId[id]).filter(f=>f&&bkStatus(f)==='pending'&&!SK.autoQ.has(f.id));
    if(!L.length)return '<div class="skmeta">אין הערות ממתינות בסוג הזה.</div>';
    return '<div class="sklist">'+L.map(f=>'<div class="skrow"><span class="dim">'+esc(f.daf||'')+'</span> <span class="skrd" onclick="bkGo(\''+f.id+'\',false)">'+skDiffHtml(f).replace(/<div class="skfix">.*$/,'')+'</span>'+
      '<button class="ok" onclick="skRowDo(\''+f.id+'\',\'ok\')">קבל</button><button class="no" onclick="skRowDo(\''+f.id+'\',\'no\')">דחה</button></div>').join('')+'</div>'}
  window.skRowDo=async function(id,d){
    const f=BK.byId[id];if(!f)return;
    BK.curId=id;
    if(d==='no'){BK.rs='';bkPut(f,'no','');bkSave();bkRefreshAfter();return}
    await bkDecide(id,'ok');skPassDraw()};

  /* ---- אישור גורף עם רשימה מרוכזת וביטול ---- */
  window.skBulkOpen=function(){
    const typ=bkTyp(BK.F.find(x=>x.det===SK.mode)||{});
    if(!SKBULK[typ]){toast('בסוג הזה אין אישור גורף: כל הערה בנפרד.',4000);return}
    const L=SK.passIds.map(id=>BK.byId[id]).filter(f=>f&&bkStatus(f)==='pending'&&!SK.autoQ.has(f.id)&&!BK.SKIP.has(f.id));
    SK.bulk={ids:L.map(f=>f.id),off:new Set()};SK.list=false;skPassDraw()};
  function skBulkHtml(){
    const b=SK.bulk;
    return '<div class="skbulk"><b>אישור גורף: '+(b.ids.length-b.off.size)+' מתוך '+b.ids.length+'</b> <span class="dim">סמן "לא" למה שאינך רוצה</span>'+
      '<div class="sklist">'+b.ids.map(id=>{const f=BK.byId[id];return '<label class="skrow'+(b.off.has(id)?' off':'')+'"><input type="checkbox" '+(b.off.has(id)?'':'checked ')+'onchange="skBulkToggle(\''+id+'\',this.checked)"> <span class="dim">'+esc(f.daf||'')+'</span> <span class="skrd">'+skDiffHtml(f).replace(/<div class="skfix">.*$/,'')+'</span></label>'}).join('')+'</div>'+
      '<div class="bt"><button class="ok" onclick="skBulkApply()">אשר את המסומנים</button><button onclick="SK.bulk=null;skPassDraw()">ביטול</button></div></div>'}
  window.skBulkToggle=function(id,on){if(on)SK.bulk.off.delete(id);else SK.bulk.off.add(id);skPassDraw()};
  window.skBulkApply=async function(){
    const b=SK.bulk;if(!b)return;
    const ids=b.ids.filter(id=>!b.off.has(id));
    SK.bulk=null;
    const recs=[];let ok=0,skip=0;
    for(const id of ids){
      const f=BK.byId[id];if(!f||bkStatus(f)!=='pending')continue;
      if(bkAction(f)==='rep'){
        BK.curId=id;
        const r=bkApplyRep(f,bkRep(f));
        if(typeof r==='string'){skip++;continue}
        recs.push({id,u:BK.undo&&BK.undo.id===id?{id:BK.undo.id,k:BK.undo.k,prev:BK.undo.prev,wasH:BK.undo.wasH}:null});
        bkPut(f,'ok','',bkRep(f).y);ok++}
      else if(/^(am|plain)$/.test(bkAction(f))){
        BK.curId=id;
        await bkDecide(id,'ok');
        if(bkStatus(f)==='ok')ok++;else skip++}
      else{bkPut(f,'todo','');ok++}}
    BK.undo=null;
    SK.batch={mode:SK.mode,recs};
    bkSave();bkAfterEdit();bkLocateAll();bkRefreshAfter();
    toast('אושרו '+ok+' מתוך '+ids.length+(skip?'. '+skip+' נשארו ממתינות (הטקסט השתנה).':'.')+' אפשר ללחוץ "בטל את האישור הגורף".',7000);
    skNext(1)};
  window.skBatchUndo=function(){
    const b=SK.batch;if(!b)return;
    const recs=b.recs.slice().reverse();
    for(const r of recs){
      const f=BK.byId[r.id];if(!f)continue;
      if(r.u){const u={id:r.u.id,k:r.u.k,prev:r.u.prev,wasH:r.u.wasH,f};bkUndoRec(u)}
      else{bkPut(f,'pending');bkSave()}}
    SK.batch=null;bkLocateAll();bkRefreshAfter();toast('האישור הגורף בוטל.',4000)};

  /* ---- שמירת מצב המעבר בין טעינות ---- */
  window.skPosRestore=function(){
    const o=skLs(SKPOS,{});if(o._&&BK.byId[o._]&&!SK.last)SK.last=o._;
    const f=BK.byId[SK.last];if(f&&BK.loc[f.id])SK.lastOrd=BK.loc[f.id].ord};

  /* ---- בקשת סקירה "סקור עכשיו" ---- */
  function skDafsKeys(){return skDafs().map(x=>x[0])}
  window.skReqNowHtml=function(){
    const dafs=skDafs();const cd=bkDafNow();
    const opt=(sel)=>dafs.map(x=>'<option value="'+esc(x[0])+'"'+(x[0]===sel?' selected':'')+'>'+esc(x[0])+'</option>').join('');
    const R=SK.rpt;
    return '<div class="skf"><b>סקור עכשיו</b>'+
      '<div class="dim">הבדיקות המהירות מוכנות מיד. בדיקת התוכן רצה דף אחרי דף, וההערות מצטרפות לתור לבד.</div>'+
      '<label>מדף <select id="skfrom" onchange="skEstDraw();skNowDraw()">'+opt(R.from||cd)+'</select> עד <select id="skto" onchange="skEstDraw();skNowDraw()">'+opt(R.to||cd)+'</select></label>'+
      '<div class="gbt"><button onclick="skPreset(\'daf\');skNowDraw()">הדף הנוכחי</button><button onclick="skPreset(\'perek\');skNowDraw()">הפרק הנוכחי</button><button onclick="skPreset(\'all\');skNowDraw()">כל המסכת</button></div>'+
      '<label>עומק <select id="skdepth" onchange="skEstDraw()"><option value="fast">מהירה (קוד ומודל זול)</option><option value="full">מלאה (כולל השכבה הסמנטית החזקה)</option></select></label>'+
      '<label>הערה לסוקר (לא חובה) <input type="text" id="sknote" maxlength="300" style="width:100%"></label>'+
      '<div id="skest" class="dim"></div>'+
      '<div class="gbt"><button class="go" onclick="skQueueSend()">סקור עכשיו</button></div>'+
      '<div id="sknow"></div></div><div id="skqlist"></div>'};
  window.skReqInit=function(){skNowDraw()};
  window.skNowDraw=function(){
    const a=$('#skfrom'),b=$('#skto'),e=$('#sknow');if(!a||!e)return;
    const ka=dafKey(a.value),kb=dafKey(b.value);
    if(ka===null||kb===null||kb<ka){e.innerHTML='';return}
    const L=BK.F.filter(f=>{const k=dafKey(f.daf);return k!==null&&k>=ka&&k<=kb&&bkStatus(f)==='pending'&&!SK.autoQ.has(f.id)});
    const by={};L.forEach(f=>{by[bkTyp(f)]=(by[bkTyp(f)]||0)+1});
    e.innerHTML='<div class="skready"><b>מוכן עכשיו בטווח:</b> '+L.length+' הערות'+
      (L.length?' ('+Object.keys(by).sort((x,y)=>SKORDER.indexOf(x)-SKORDER.indexOf(y)).map(k=>esc(SKT[k][0])+' '+by[k]).join(' · ')+')':'')+
      (L.length?'<div class="gbt"><button class="go" onclick="skGoRange()">לעבור עליהן עכשיו</button></div>':'')+'</div>'};
  window.skGoRange=function(){
    const a=$('#skfrom'),b=$('#skto');if(!a)return;
    SK.rng={a:dafKey(a.value),b:dafKey(b.value)};SK.pool=null;SK.end=null;
    const p=$('#bkp');if(p&&p.classList.contains('open'))panel('bkp');
    BK.curId='';SK.last='';SK.lastOrd=-1;SK.fromTop=true;
    if(!BK.ON)bkToggle();
    skNext(1)};
  window.skRngClear=function(){SK.rng=null;bkRefresh()};
  window.skQueueSend=async function(){
    const a=$('#skfrom'),b=$('#skto'),d=$('#skdepth');if(!a)return;
    const ds=skDafsKeys(),i=ds.indexOf(a.value),j=ds.indexOf(b.value);
    if(i<0||j<i){toast('הטווח אינו תקין.');return}
    const est=skEst(d.value,j-i+1);
    const ka=dafKey(a.value),kb=dafKey(b.value);
    const quick=BK.F.filter(f=>{const k=dafKey(f.daf);return k!==null&&k>=ka&&k<=kb&&f.layer==='קוד'}).length;
    try{await skPost('/skira/queue',{slug:SLUG,from:a.value,to:b.value,depth:d.value,note:($('#sknote')||{}).value||'',est,prio:'now',quick});
      toast('הבקשה נרשמה. בדיקות מהירות מוכנות (' +quick+' הערות); בדיקת התוכן תתחיל ותצטרף לתור לבד.',6000);
      await skQLoad();skPollStart();skDrawPanel()}
    catch(e){toast('הבקשה לא נשלחה: '+(e.message||'שגיאה'),6000)}};

  /* ---- ריענון תקופתי כשיש בקשה פעילה, והודעה על הערות שנוספו ---- */
  let SKPOLL=null,SKPT=0;
  window.skPollStart=function(){
    if(SKPOLL)return;
    SKPOLL=setInterval(async()=>{
      if(document.hidden||!BK.loaded){return}
      await skQLoad();
      if(!skActiveReq()){clearInterval(SKPOLL);SKPOLL=null;await bkLoad();skRedrawStat();return}
      if(Date.now()-SKPT>25000){SKPT=Date.now();await bkLoad()}
      skRedrawStat()},12000)};
  function skRedrawStat(){
    const e=$('#skstat');if(e){const st=skStatusText();e.textContent=st||'אין בקשת סקירה פעילה. אפשר לבקש בלשונית "סקור עכשיו".'}
    if(SK.mode)skPassDraw();else if(BK.ON)bkBarDraw();
    const n=$('#sknext');if(n){const i=skNextInfo();n.textContent=i.t+(i.on?' ↓':'');n.classList.toggle('idle',!i.on)}}
  window.skAfterLoad=function(){
    if(window.skPosRestore)skPosRestore();
    /* הערות שנוספו מאז הטעינה הקודמת: לפני המקום הנוכחי - נספרות; אחריו - הודעה קטנה */
    if(BK.prevIds){
      const co=bkCurOrd();let ahead={};
      for(const f of BK.F){
        if(BK.prevIds.has(f.id)||bkStatus(f)!=='pending'||!BK.loc[f.id])continue;
        if(BK.loc[f.id].ord<co&&(SK.last||BK.curId))SK.behind.add(f.id);
        else ahead[f.daf||'?']=(ahead[f.daf||'?']||0)+1}
      const ks=Object.keys(ahead);
      if(ks.length&&BK.ON){
        toast(ks.slice(0,3).map(d=>'נוספו '+ahead[d]+' הערות מדף '+d).join(' · ')+'.',5000)}}
    skAutoRun();
    skQLoad().then(()=>{if(skActiveReq())skPollStart();skRedrawStat()}).catch(()=>{})};

  /* ---- תיקון אוטומטי והכרעה לפי חתימה וסוג ---- */
  function skSig(f){
    const rp=bkRep(f);
    return f.det+'|'+bkCompact(f.mark||'').c+(rp?'|'+bkCompact(rp.x).c+'>'+bkCompact(rp.y).c:'')}
  const SKNOAUTO={psuk_nik:1,psuk_miss:1,sem_hav:1,sem_yih:1,sem_hsr:1,sem_lo:1,sk_pshat:1,sk_step:1,sk_lo:1,sk_q:1,sk_miss:1,sk_mach:1,alt:1,hash:1,sem_hash:1};
  function skHistory(){
    const bySig={},byDet={};
    for(const f of BK.F){
      const d=BK.DEC[f.id];if(!d||d.d==='pending'||d.auto)continue;
      const dir=d.d==='no'?'no':(d.d==='edit'?'edit':'ok');
      const s=skSig(f);(bySig[s]||(bySig[s]=[])).push({dir,t:d.t||0});
      (byDet[f.det]||(byDet[f.det]=[])).push({dir,t:d.t||0,act:bkAction(f)})}
    return {bySig,byDet}}
  function skDetVerdict(arr){
    if(!arr||arr.length<10)return '';
    const L=arr.slice().sort((a,b)=>a.t-b.t),last=L.slice(-3);
    const ok=L.filter(x=>x.dir==='ok').length,no=L.filter(x=>x.dir==='no').length,n=L.length;
    if(ok/n>=0.9&&last.every(x=>x.dir==='ok'))return 'ok';
    if(no/n>=0.85&&last.every(x=>x.dir==='no'))return 'no';
    return ''}
  async function skAutoRun(){
    if(SK.autoBusy||!BK.loaded||!isAdmin()||!admKey())return;
    SK.autoBusy=true;
    try{
      bkLocateAll();
      const H=skHistory();
      const verdict={};
      for(const det in H.byDet){
        if(SKNOAUTO[det]||SK.autoOff[det])continue;
        const t=bkTyp(BK.F.find(x=>x.det===det)||{});
        if(!/^[gfe]$/.test(t))continue;
        const v=skDetVerdict(H.byDet[det]);if(v)verdict[det]=v}
      SK.autoDet=verdict;
      const sec=SEC[cur]||{from:0,to:0};
      const jobs={no:[],ok:[],queued:[]};
      for(const f of BK.F){
        if(bkStatus(f)!=='pending')continue;
        if(SK.autoOff[f.det])continue;
        const act=bkAction(f);
        let how='';
        if(f.auto&&act==='rep')how='ok';
        if(!how){const h=H.bySig[skSig(f)];
          if(h&&h.length&&h.every(x=>x.dir==='no'))how='no';
          else if(h&&h.length&&h.every(x=>x.dir==='ok')&&act==='rep'&&!SKNOAUTO[f.det])how='ok'}
        if(!how&&verdict[f.det]){
          if(verdict[f.det]==='no')how='no';
          else if(act==='rep')how='ok'}
        if(!how)continue;
        if(how==='no')jobs.no.push(f);
        else{
          const L=BK.loc[f.id];
          const inDom=L&&L.pi>=sec.from&&L.pi<=sec.to&&$('#flow').querySelector('[data-ek="'+L.k+'"]');
          if(inDom)jobs.ok.push(f);else if(L)jobs.queued.push(f)}}
      /* דחייה אוטומטית: החלטה בלבד, בלי נגיעה בטקסט */
      let nNo=0;
      for(const f of jobs.no.slice(0,600)){bkPut(f,'no','','','auto_'+(f.auto?'v':(H.bySig[skSig(f)]?'sig':'type')));nNo++}
      /* החלה אוטומטית: עד 40 בכל טעינה, רק בפרק הפתוח, כעריכת מנהל רגילה (נכנסת לוורד בעקוב אחר שינויים) */
      let nOk=0;
      for(const f of jobs.ok.slice(0,40)){
        const act=bkAction(f);
        if(act==='rep'){
          const r=bkApplyRep(f,bkRep(f));
          if(typeof r==='string')continue;
          const rec=BK.undo&&BK.undo.id===f.id?{k:BK.undo.k,prev:BK.undo.prev,wasH:BK.undo.wasH}:null;
          BK.undo=null;
          if(rec){SK.undoRec[f.id]=rec}
          bkPut(f,'ok','',bkRep(f).y,'auto_'+(f.auto?'v':(H.bySig[skSig(f)]?'sig':'type')));nOk++}
        else continue}
      if(nOk)bkAfterEdit();
      SK.autoQ=new Set(jobs.queued.map(f=>f.id));
      if(nNo||nOk){
        const ks=Object.keys(SK.undoRec);if(ks.length>300)ks.slice(0,ks.length-300).forEach(k=>delete SK.undoRec[k]);
        skLsSet(SKUNDO,SK.undoRec);
        bkSave();bkLocateAll();bkHL();bkCount();
        if(BK.ON)toast('תוקן אוטומטית: '+nOk+' תיקונים, '+nNo+' הערות שהוכרעו לפי החלטות קודמות שלך. הפירוט בלשונית "תוקן אוטומטית".',7000)}
      if($('#bkp')&&$('#bkp').classList.contains('open'))skDrawPanel();
      if(BK.ON){if(SK.mode)skPassDraw();else bkBarDraw()}
    }catch(e){try{console.warn('skAutoRun',e)}catch(_){}}
    SK.autoBusy=false}
  window.skAutoRun=skAutoRun;
  /* פרק שנפתח אחרי הטעינה: מה שמחכה בו להחלה אוטומטית יוחל עכשיו (ללא לולאה: רק כשיש ממתינות בפרק) */
  let SKAT=null;
  window.skAutoSoon=function(){
    if(!SK.autoQ.size||SK.autoBusy)return;
    const sec=SEC[cur]||{from:0,to:0};
    const here=Array.from(SK.autoQ).some(id=>{const L=BK.loc[id];return L&&L.pi>=sec.from&&L.pi<=sec.to});
    if(!here)return;
    clearTimeout(SKAT);SKAT=setTimeout(()=>{SK.autoQ.clear();skAutoRun()},1200)};
  setInterval(()=>{if(BK.loaded&&SK.autoQ.size&&!document.hidden)skAutoSoon()},2500);

  /* ---- יומן "תוקן אוטומטית" ---- */
  window.skAutoHtml=function(){
    const rows=BK.F.filter(f=>{const d=BK.DEC[f.id];return d&&d.auto});
    const by={};rows.forEach(f=>{const k=f.kind||f.det;(by[k]||(by[k]=[])).push(f)});
    const closed=BK.AUTOLOG||[];
    let h='<div class="skf"><b>מה תוקן או הוכרע לבד</b><div class="dim">לא חוסם ולא מבקש דבר. אפשר לעיין, ולכל שורה יש "בטל".</div></div>';
    const det=SK.autoDet||{};
    const dets=Object.keys(det);
    if(dets.length)h+='<h3>סוגים שמוחלים מעתה לבד</h3>'+dets.map(k=>{
      const n=BK.F.filter(f=>f.det===k&&BK.DEC[f.id]&&BK.DEC[f.id].auto).length;
      return '<div class="it" style="cursor:default"><b>'+esc((BK.CAT[k]&&BK.CAT[k][1])||k)+'</b> <small>('+(det[k]==='ok'?'מאושר':'נדחה')+' - '+n+' פעמים עד כה)</small><br>'+
        'הסוג הזה מוחל מעתה לבד לפי ההכרעות שלך. <button onclick="skAutoOff(\''+k+'\',1)">החזר לשאלה</button></div>'}).join('');
    const off=Object.keys(SK.autoOff).filter(k=>SK.autoOff[k]);
    if(off.length)h+='<h3>סוגים שהחזרת לשאלה</h3>'+off.map(k=>'<div class="it" style="cursor:default">'+esc((BK.CAT[k]&&BK.CAT[k][1])||k)+' <button onclick="skAutoOff(\''+k+'\',0)">אפשר שוב לבד</button></div>').join('');
    if(SK.autoQ.size)h+='<div class="edsum">'+SK.autoQ.size+' הערות יוחלו לבד כשהפרק שלהן ייפתח.</div>';
    if(closed.length){
      const q=closed.filter(x=>x.what==='ציטוט שלם');
      h+='<details class="grp"><summary><b>ציטוטי פסוקים שנמצאו שלמים</b> <span class="n">('+q.length+')</span></summary><div class="gb">'+
        '<div class="dim">הגרשים פותחים וסוגרים כראוי; לא נדרש תיקון ולא הוצגה הערה.</div>'+
        q.slice(0,60).map(x=>'<div class="it" style="cursor:default"><small>'+esc(x.daf||'')+'</small> '+esc((x.ctx||x.mark||'').slice(0,90))+'</div>').join('')+
        (q.length>60?'<div class="dim">ועוד '+(q.length-60)+'...</div>':'')+'</div></details>'}
    const ks=Object.keys(by).sort((a,b)=>by[b].length-by[a].length);
    h+=ks.map(k=>'<details class="grp"><summary><b>'+esc(k)+'</b> <span class="n">('+by[k].length+')</span></summary><div class="gb">'+
      by[k].map(f=>{const d=BK.DEC[f.id];
        return '<div class="it" style="cursor:default"><small>'+esc(f.daf||'')+' · '+esc(skAutoWhy(d.rs))+'</small> <span class="mk">'+esc((f.mark||'').slice(0,40))+'</span> '+
        '<button onclick="skAutoUndo(\''+f.id+'\')">בטל את התיקון הזה</button></div>'}).join('')+'</div></details>').join('');
    if(!ks.length&&!closed.length)h+='<div class="edsum">עדיין לא תוקן דבר לבד.</div>';
    return h};
  function skAutoWhy(rs){return {auto_v:'ציטוט פסוק לפי נוסח המקרא',auto_sig:'אותה הכרעה שנתת בעבר',auto_type:'הסוג הזה מוחל לבד לפי הכרעותיך',auto:'אוטומטי'}[rs]||'אוטומטי'}
  window.skAutoUndo=function(id){
    const f=BK.byId[id];if(!f)return;
    const rec=SK.undoRec[id];
    if(rec){bkUndoRec({id,k:rec.k,prev:rec.prev,wasH:rec.wasH,f});delete SK.undoRec[id];skLsSet(SKUNDO,SK.undoRec)}
    else{bkPut(f,'pending');bkSave()}
    SK.autoOff[f.det]=SK.autoOff[f.det]||0;
    bkLocateAll();bkRefresh();toast('התיקון בוטל וההערה חזרה לממתינות.',4000)};
  window.skAutoOff=function(det,off){
    SK.autoOff[det]=off?1:0;skLsSet(SKOFF,SK.autoOff);
    if(off&&SK.autoDet)delete SK.autoDet[det];
    skDrawPanel()};

  /* ---- עיצוב ---- */
  (function(){
    if(document.getElementById('skpcss'))return;
    const st=document.createElement('style');st.id='skpcss';
    st.textContent=
      '.skpass{color:#2b2620;position:fixed;left:50%;transform:translateX(-50%);bottom:12px;z-index:8;width:min(760px,96vw);background:#fffdf8;border:1px solid #c9b98f;border-radius:10px;box-shadow:0 6px 24px rgba(0,0,0,.3);padding:8px 12px;font-size:15px;line-height:1.5;direction:rtl;max-height:70vh;overflow:auto}'+
      'body.ed .skpass{bottom:56px}'+
      '.skph{display:flex;align-items:center;gap:8px;flex-wrap:wrap;border-bottom:1px solid #e6dfcb;padding-bottom:4px;margin-bottom:5px}'+
      '.skph .skexp{font-weight:600}.skph .skcnt{margin-right:auto;font-size:13px;color:#5a5044}.skph .x{background:none;border:0;font-size:20px;cursor:pointer;color:#5a5044;line-height:1}'+
      '.skdiff{background:#f3efe3;border-radius:6px;padding:6px 9px;font-size:17px;margin:3px 0}.skdiff del{color:#a83c2f;background:#fbe5e1}.skdiff ins{color:#2e6b3f;background:#e3f3e6;text-decoration:none}.skdiff mark{background:#f6e3a0}'+
      '.skdiff .skfix{margin-top:4px;font-size:14px;color:#2e6b3f}.skmeta{font-size:13px;color:#6b604d;margin:2px 0}'+
      '.skpass .bt{display:flex;gap:6px;margin-top:5px;flex-wrap:wrap}.skpass .bt button{font:inherit;font-size:14px;border:1px solid #b9a97c;border-radius:5px;background:#f6f1e2;padding:2px 12px;cursor:pointer}'+
      '.skpass .bt button.ok,.skpass .bt button.go{background:#2e6b3f;color:#fff;border-color:#2e6b3f}.skpass .bt button.no{color:#a83c2f}.skpass .bt button[disabled]{opacity:.5;cursor:default}'+
      '.skpass .kk{font-size:10px;opacity:.7;margin-right:3px;direction:ltr;unicode-bidi:isolate}'+
      '.skpass .skfoot{border-top:1px dotted #d9d1bd;padding-top:5px}.sknx.idle{background:#e6dfcb!important;color:#5a5044!important;border-color:#c9b98f!important}'+
      '.skend,.skendbar{background:#fdf1d8;border-radius:6px;padding:4px 8px;margin-top:6px;font-size:14px}.skend button,.skendbar button{font:inherit;font-size:14px;margin:0 4px}'+
      '.sklist{max-height:34vh;overflow:auto;border:1px solid #e0d8c4;border-radius:6px;margin-top:5px}.skrow{display:flex;gap:6px;align-items:center;padding:3px 7px;border-bottom:1px dotted #d9d1bd;font-size:14px}'+
      '.skrow.off{opacity:.5}.skrow .skrd{flex:1}.skrow del{color:#a83c2f}.skrow ins{color:#2e6b3f;text-decoration:none}'+
      '.skrow button{font:inherit;font-size:13px;border:1px solid #b9a97c;border-radius:5px;background:#f6f1e2;padding:0 9px;cursor:pointer}.skrow button.ok{background:#2e6b3f;color:#fff}'+
      '.sktypes{display:flex;gap:6px;flex-wrap:wrap;margin-top:6px}.sktype{font:inherit;font-size:14px;border:2px solid #b9a97c;border-radius:14px;background:rgba(255,255,255,.08);color:inherit;padding:2px 11px;cursor:pointer}.sktype b{margin-right:4px}'+
      '.skhead{display:flex;align-items:center;gap:8px;margin-bottom:4px}.skqm{font:inherit;width:24px;height:24px;border-radius:12px;border:1px solid #b9a97c;background:rgba(255,255,255,.1);color:inherit;cursor:pointer;padding:0}'+
      '.skhelp{background:rgba(46,91,138,.22);border-radius:6px;padding:6px 9px;font-size:14px;margin-bottom:6px}'+
      '.skstat{background:rgba(201,162,74,.18);border-radius:6px;padding:4px 8px;font-size:14px;margin-bottom:6px;border-right:3px solid #2e5b8a;min-height:1.4em}'+
      '.skbarstat{width:100%;font-size:13px;color:#5a5044}.skready{margin-top:6px;background:rgba(46,107,63,.25);border-radius:6px;padding:5px 8px}'+
      '@media print{.skpass{display:none!important}}';
    document.head.appendChild(st)})();
  /* חץ ימינה/שמאלה וה-Delete במצב מעבר: מטופלים בידי המאזין הכללי ב-skira_ui.js */
