  /* =================== ממשק ההצעות (5.10.2026) ===================
     נטען בסוף הסקריפט, ולכן הפונקציות כאן מחליפות את הגרסאות הקודמות באותו שם
     (openSg, sgSend, drawSg, drawSq, sqRow, sqDecide).

     המציע: זהות במכשיר (pid + אסימון pt, בלי סיסמה), חלון הצעה צף שאינו מסתיר
     את הטקסט, חמישה סוגי הצעה, טיוטה שנשמרת מעצמה, "ההצעות שלי" עם מצב, סיבת
     דחייה, שרשור עם המנהל והתראה.
     המנהל: תור עם צבע לכל סוג, אשר / ערוך ואשר / דחה (עם סיבה) / השב / דלג,
     מקשים, ביטול פעולה אחרונה, הצעות סותרות זו לצד זו, התיישנות, מהימנים,
     והכרעה בצרור. כל הכרעה נרשמת ביומן התיקונים (הלומד). */
  const STYPES={nusach:['תיקון נוסח','✎','#2e6b3f'],style:['תיקון סגנון','◐','#6a4a8f'],
                question:['שאלה','?','#b0721a'],note:['הערה','✉','#2e5b8a'],source:['הוספת מקור','⚓','#8a5a2e']};
  const SSTAT={pending:['ממתינה','#8a7d66'],accepted:['אושרה','#2e6b3f'],edited:['אושרה בשינוי','#5f7f2e'],
               rejected:['נדחתה','#a83c2f'],stale:['התיישנה','#7a7a7a']};
  const STYLE_CHIPS=['זה פסוק','זה שם אמורא','זה הסבר','זה נושא','זה ד"ה'];
  (function(){const st=document.createElement('style');st.textContent=
    '.sgpop{position:fixed;z-index:12;width:min(360px,94vw);background:var(--sheet);color:var(--tx);border:1px solid var(--line);border-radius:14px;box-shadow:var(--shadow);padding:12px 14px;font-size:15px;line-height:1.5}'+
    '.sgpop h3{margin:0 0 6px;font-size:15px}.sgpop textarea{width:100%;min-height:70px;box-sizing:border-box}'+
    '.sgpop input[type=text]{width:100%;box-sizing:border-box}.sgpop .sel{max-height:64px;overflow:auto;background:var(--parch);padding:4px 8px;border-radius:8px;font-size:14px}'+
    '.sgtypes{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0}.sgchips{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0}'+
    '.sgtypes button,.sgchips button{border-radius:999px!important;padding:2px 12px!important;min-height:30px!important;font-size:14px!important}'+
    '.sgtypes button.on{background:var(--blue)!important;color:var(--blue-ink)!important;border-color:var(--blue)!important}'+
    '.sgpop .btns{display:flex;gap:8px;margin-top:10px;align-items:center}'+
    '.sgpop .dr,.dr{font-size:13px;color:var(--tx2)}'+
    '.stchip{display:inline-block;background:var(--tx2);color:var(--sheet);border-radius:999px;padding:0 10px;font-size:12px;margin-left:6px}'+
    '.tychip{display:inline-block;border:1px solid;border-radius:999px;padding:0 8px;font-size:12px;margin-left:6px}'+
    '.sgthr{margin:6px 0;padding:4px 10px;border-inline-start:3px solid var(--line);font-size:14px}.sgthr .m{color:var(--blue)}.sgthr .p{color:var(--tx2)}'+
    '.sgrow .why{color:var(--rd);font-size:14px}.sgrow.cur{border-color:var(--blue)!important;box-shadow:0 0 0 2px var(--blue-soft)}.sgrow.trust{background:var(--blue-soft)}'+
    '.sgconf{display:flex;gap:8px;flex-wrap:wrap}.sgconf>.sgrow{flex:1 1 45%}'+
    '.sgrep{display:flex;gap:6px;margin-top:6px}.sgrep input{flex:1;font-size:14px}.sgbar{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0 10px;align-items:center}'+
    '.sgbar select{font-size:14px!important}.sgbar button{font-size:14px!important;min-height:34px!important}'+
    '.sgbell{background:var(--rd);color:var(--sheet);border-radius:999px;padding:0 7px;margin-right:4px;font-size:12px}'+
    '#sgq .sgrow{background:var(--sheet);border:1px solid var(--line);border-radius:14px;padding:12px 14px;margin:0 0 12px;display:block}'+
    '.sgact{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-top:10px}'+
    '.sgact>button{flex:1 1 90px;min-height:44px!important;font-size:16px!important;font-weight:700}'+
    '.sgact>button.ok{background:var(--gn)!important;border-color:var(--gn)!important;color:var(--sheet)!important}'+
    '.sgact>button.ok kbd{color:var(--sheet);border-color:var(--sheet);background:transparent}'+
    '.sgmore{flex:0 0 100%}.sgmore>summary{cursor:pointer;color:var(--blue);font-weight:600;list-style:none;padding:6px 2px;width:fit-content}'+
    '.sgmore>summary::-webkit-details-marker{display:none}.sgmore>summary::after{content:" ▾"}.sgmore[open]>summary::after{content:" ▴"}'+
    '.sgmore>div{display:flex;flex-wrap:wrap;gap:6px;margin-top:4px}.sgmore>div button{min-height:34px!important;font-size:14px!important}'+
    '.sgbulk{position:sticky;top:0;z-index:2;background:var(--blue-soft);border:1px solid var(--blue);border-radius:12px;padding:8px 12px}'+
    '.sgbulk[hidden]{display:none}.sgkeys{margin:4px 0 10px}.sgkeys kbd{margin:0 2px}';
    document.head.appendChild(st)})();

  /* ---- זהות המציע ---- */
  function rnd(n){const a=new Uint8Array(n);crypto.getRandomValues(a);return [...a].map(x=>(x%36).toString(36)).join('')}
  function pident(){let pid='',pt='';
    try{pid=localStorage.getItem('lg-pid')||'';pt=localStorage.getItem('lg-pt')||'';
      if(!pid||!pt){pid=rnd(14);pt=rnd(32);localStorage.setItem('lg-pid',pid);localStorage.setItem('lg-pt',pt)}}catch(e){pid=pid||rnd(14);pt=pt||rnd(32)}
    return {pid,pt}}
  async function papi(path,body){
    const id=pident();const o={headers:{'content-type':'application/json; charset=utf-8','x-proposer':id.pt}};
    if(body){o.method='POST';o.body=JSON.stringify(Object.assign({pid:id.pid},body))}
    const r=await fetch(SUGGEST_API+path+(body?'':(path.indexOf('?')>-1?'&':'?')+'pid='+id.pid),o);
    let j=null;try{j=await r.json()}catch(e){}
    if(!r.ok||!j||!j.ok)throw new Error((j&&j.error)||('שגיאה '+r.status));
    return j}

  /* ---- חלון הצעה צף ליד הקטע ---- */
  function sgGrp(){try{const g=JSON.parse(localStorage.getItem('lg-sg-grp')||'null');
    if(g&&Date.now()-g.t<600000){g.t=Date.now();localStorage.setItem('lg-sg-grp',JSON.stringify(g));return g.id}
    const n={id:rnd(10),t:Date.now()};localStorage.setItem('lg-sg-grp',JSON.stringify(n));return n.id}catch(e){return rnd(10)}}
  function openSg(text,el){
    closeSg();
    const u=unitOf(el),k=(el&&el.dataset&&el.dataset.ek)||'';
    const dk='lg-sg-draft-'+SLUG+'-'+k;let dr=null;try{dr=JSON.parse(localStorage.getItem(dk)||'null')}catch(e){}
    let type=(dr&&dr.type)||'nusach';
    const m=document.createElement('div');m.className='sgpop';m.id='sgm';
    m.innerHTML='<h3>הצעה · '+esc(D.masechet)+(u.daf?' · דף '+esc(u.daf):'')+'</h3>'+
      '<div class="sel">'+esc(text)+'</div>'+
      '<div class="sgtypes" id="sgty"></div>'+
      '<div class="sgchips" id="sgch" style="display:none"></div>'+
      '<label for="sgn" id="sgnl">הנוסח המוצע במקום הקטע המסומן</label>'+
      '<textarea id="sgn"></textarea>'+
      '<label for="sgw">שמך (לא חובה)</label><input type="text" id="sgw" maxlength="80" value="'+esc(localStorage.getItem('lg-sg-name')||'')+'">'+
      '<input id="sgh" name="website" tabindex="-1" autocomplete="off" style="position:absolute;left:-9999px;top:-9999px;opacity:0;height:0" aria-hidden="true">'+
      '<div class="btns"><button class="go" id="sgok">שלח</button><button id="sgx">ביטול</button><span class="dr" id="sgdr"></span></div>';
    document.body.appendChild(m);
    const sel=$('#sgn');
    sel.value=dr&&dr.note!==undefined?dr.note:text;
    function paint(){
      $('#sgty').innerHTML=Object.keys(STYPES).map(t=>'<button type="button" data-t="'+t+'" class="'+(t===type?'on':'')+'" style="'+(t===type?'background:'+STYPES[t][2]+';border-color:'+STYPES[t][2]:'color:'+STYPES[t][2])+'">'+STYPES[t][1]+' '+STYPES[t][0]+'</button>').join('');
      $('#sgty').querySelectorAll('button').forEach(b=>b.onclick=()=>{
        const was=type;type=b.dataset.t;
        if(was==='nusach'&&type!=='nusach'&&sel.value===text)sel.value='';
        if(type==='nusach'&&!sel.value)sel.value=text;
        paint();draft()});
      $('#sgch').style.display=type==='style'?'flex':'none';
      $('#sgnl').textContent=type==='nusach'?'הנוסח המוצע במקום הקטע המסומן':type==='style'?'מה הסגנון הנכון?':
        type==='question'?'השאלה':type==='source'?'המקור המוצע (שם הספר והמקום)':'ההערה'}
    $('#sgch').innerHTML=STYLE_CHIPS.map(c=>'<button type="button">'+esc(c)+'</button>').join('');
    $('#sgch').querySelectorAll('button').forEach(b=>b.onclick=()=>{sel.value=b.textContent;draft()});
    paint();
    function draft(){try{localStorage.setItem(dk,JSON.stringify({type,note:sel.value}));$('#sgdr').textContent='הטיוטה נשמרה'}catch(e){}}
    sel.addEventListener('input',()=>{clearTimeout(m.__d);m.__d=setTimeout(draft,500)});
    /* ממקם ליד הקטע, בלי להסתיר אותו: מתחת אם יש מקום, אחרת מעליו */
    const rc=el.getBoundingClientRect(),bh=m.offsetHeight||300;
    let top=rc.bottom+8;if(top+bh>innerHeight-8)top=Math.max(8,rc.top-bh-8);
    if(top+bh>innerHeight-8)top=Math.max(8,innerHeight-bh-8);
    let left=Math.min(innerWidth-m.offsetWidth-8,Math.max(8,rc.left));
    m.style.top=top+'px';m.style.left=left+'px';
    sel.focus();
    $('#sgx').onclick=()=>closeSg();
    $('#sgok').onclick=()=>{
      const note=sel.value.trim();
      if(!note){alert('כתוב מה להציע.');return}
      if(type==='nusach'&&note===text.trim()){alert('הנוסח המוצע זהה לקטע המסומן. שנה אותו, או בחר סוג אחר.');return}
      if(/(https?:\/\/|www\.)/i.test(note)){alert('הצעה שיש בה קישור אינה מתקבלת.');return}
      const name=$('#sgw').value.trim();
      try{localStorage.setItem('lg-sg-name',name);localStorage.removeItem(dk)}catch(e){}
      const id=pident();
      const rec={slug:SLUG,masechet:D.masechet,daf:u.daf,uid:u.uid,k,ctx:ctxOf(el),was:text,note,name,type,
                 pid:id.pid,pt:id.pt,grp:sgGrp(),hp:$('#sgh').value,t:Date.now(),sent:0};
      SG.push(rec);saveSG();closeSg();sgSend()};
  }
  function closeSg(){const m=$('#sgm');if(m)m.remove()}
  addEventListener('resize',()=>{});
  async function sgSend(){
    if(SGBUSY)return;SGBUSY=true;let ok=0,fail=0,why='';
    for(const g of SG){
      if(g.sent)continue;
      if(!g.pid){const i=pident();g.pid=i.pid;g.pt=i.pt}
      try{const j=await api('/suggest',{method:'POST',body:JSON.stringify(g)});g.sent=1;g.id=j.id;ok++}
      catch(e){why=e.message||'';if(/קישור|נדחה|ארוכה|תואמת/.test(why)){g.sent=1;g.bad=why}else{fail++;if(/מהירה/.test(why))setTimeout(sgSend,4000)}}
    }
    saveSG();SGBUSY=false;
    if(ok)toast('ההצעה נשלחה לעורך. תודה רבה. אפשר לעקוב אחריה ב"ההצעות שלי".');
    else if(fail)toast('אין חיבור כרגע. ההצעה נשמרה במכשיר ותישלח בטעינה הבאה.',4500);
    else if(why)toast(why,4500);
    drawSg()}

  /* ---- ההצעות שלי: מסך מלא (5.10.2026) ----
     רשימה של כל הצעותיו של המציע, עם סינון, מיון וחיפוש חופשי, עריכה במקום
     (נשמרת גרסה קודמת), חידוד והגשה מחדש של הצעה שנדחתה, ליטוש נוסף להצעה
     שאושרה, משיכה של הצעה ממתינה, וקפיצה למקום בדף. ההצעה המלאה נשמרת
     במכשיר לפי גרסה, ולכן גם מציע עם מאות הצעות טוען רק מה שהשתנה. */
  const MCK='lg-mine-cache';
  let MINE=[],MROWS=[],MINEERR='',MFIL={q:'',mas:'',st:'',daf:'',sort:'new'},MSHOW=60,MED=null,MCACHE={},MLOAD=0,MLOADING=false;
  try{MCACHE=JSON.parse(localStorage.getItem(MCK)||'{}')}catch(e){MCACHE={}}
  function mcSave(){try{localStorage.setItem(MCK,JSON.stringify(MCACHE))}catch(e){try{localStorage.removeItem(MCK)}catch(e2){}}}
  async function mineLoad(markSeen){
    if(MLOADING)return;MLOADING=true;
    try{
      const j=await papi('/mine');MROWS=j.rows||[];MINEERR='';mineBell(j.unseen||0);
      const idn=pident().pid;
      if(MCACHE.pid!==idn)MCACHE={pid:idn,items:{}};
      const have=new Set(MROWS.map(r=>r.id));
      for(const k in MCACHE.items)if(!have.has(k))delete MCACHE.items[k];
      const need=MROWS.filter(r=>{const c=MCACHE.items[r.id];return !c||!r.v||c.v!==r.v}).map(r=>r.id);
      for(let i=0;i<need.length;i+=40){
        MLOAD=Math.min(need.length,i+40);if(myOpen())mineList();
        const b=await papi('/mine/batch',{ids:need.slice(i,i+40)});
        (b.items||[]).forEach(rec=>{MCACHE.items[rec.id]={v:rec.ver||0,rec}})}
      MLOAD=0;mcSave();
      MINE=MROWS.map(r=>(MCACHE.items[r.id]||{}).rec).filter(Boolean);
      if(markSeen&&j.unseen)papi('/mine/seen',{}).then(()=>mineBell(0)).catch(()=>{})}
    catch(e){MLOAD=0;MINEERR=/הרשאה/.test(e.message)?'':(e.message||'')}
    MLOADING=false}
  function mineBell(n){const b=document.querySelector('button[onclick^="mineOpen"]');if(!b)return;
    b.innerHTML='ההצעות שלי'+(n?'<span class="sgbell">'+n+'</span>':'')}
  function stChip(st){const s=SSTAT[st]||SSTAT.pending;return '<span class="stchip" style="background:'+s[1]+'">'+s[0]+'</span>'}
  function tyChip(t){const s=STYPES[t]||STYPES.nusach;return '<span class="tychip" style="color:'+s[2]+';border-color:'+s[2]+'">'+s[1]+' '+s[0]+'</span>'}
  function thrHTML(g,admin){return (g.thread||[]).map(x=>'<div class="sgthr"><span class="'+x.from+'">'+(x.from==='m'?'העורך':'המציע')+':</span> '+esc(x.txt)+'</div>').join('')}
  (function(){const st=document.createElement('style');st.textContent=
    '.mys{position:fixed;inset:0;z-index:40;background:#fbf8ef;overflow:auto;display:none;direction:rtl;font-size:16px;line-height:1.55}'+
    '.mys .in{max-width:920px;margin:0 auto;padding:0 14px 60px}'+
    '.mysh{position:sticky;top:0;background:#fbf8ef;z-index:2;padding:10px 0 6px;border-bottom:1px solid #d9d1bd}'+
    '.mysh h2{margin:0;font-size:21px;display:inline}.mysh .l{float:left;display:flex;gap:6px}'+
    '.mysbar{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0}.mysbar input,.mysbar select{font:inherit;font-size:15px;padding:3px 6px;border:1px solid #c9b98f;border-radius:4px;background:#fff}'+
    '.mysbar input[type=search]{flex:1 1 220px;min-width:140px}.mysbar #myd{width:80px}'+
    '.mycard{background:#fff;border:1px solid #d9d1bd;border-radius:8px;padding:9px 12px;margin:9px 0}.mycard.new{outline:2px solid #c9a24a}'+
    '.mycard .mym{font-size:14px;color:#6b5f4a;margin-bottom:3px}.mycard q{display:block;color:#6b5f4a;font-size:15px;margin:2px 0}'+
    '.mycard .myn{font-size:17px;font-weight:600;white-space:pre-wrap}.mycard .why{color:#a83c2f;font-size:15px}'+
    '.mycard button,.mys button.b{font:inherit;font-size:14px;margin:6px 0 0 6px;padding:2px 11px;border:1px solid #b9a97c;border-radius:5px;background:#f6f1e2;cursor:pointer}'+
    '.mycard button.go,.mys button.go{background:#2e6b3f;color:#fff;border-color:#2e6b3f}'+
    '.mycard textarea{width:100%;box-sizing:border-box;min-height:96px;font:inherit;font-size:17px;direction:rtl;padding:6px;border:1px solid #c9b98f;border-radius:5px}'+
    '.mycard details{margin-top:5px;font-size:14px}.mycard details div{padding:2px 8px;border-right:3px solid #d9d1bd;margin:3px 0;white-space:pre-wrap}'+
    '.mycard a.mygo{color:#2e5b8a;cursor:pointer;font-size:14px;margin-right:10px;text-decoration:underline}'+
    '.mymore{text-align:center;margin:14px 0}.mydim{color:#8a7d66;font-size:14px}'+
    'body.mysopen{overflow:hidden}'+
    '@media (max-width:600px){.mys .in{padding:0 8px 60px}.mycard .myn{font-size:16px}}';
    document.head.appendChild(st)})();
  const myOpen=()=>{const o=$('#mys');return !!o&&o.style.display!=='none'};
  function mineOpen(){
    let o=$('#mys');
    if(!o){o=document.createElement('div');o.id='mys';o.className='mys';o.setAttribute('role','dialog');o.setAttribute('aria-label','ההצעות שלי');
      o.innerHTML='<div class="in"><div class="mysh"><h2>ההצעות שלי</h2> <span class="mydim" id="myc"></span>'+
        '<span class="l"><button class="b" onclick="mineMe()" title="השם שלך וקישור אישי להיכנס ממכשיר אחר">הזהות שלי</button><button class="b" onclick="mineClose()">סגירה ✕</button></span></div>'+
        '<div class="mysbar"><input type="search" id="myq" placeholder="חיפוש חופשי בהצעות" aria-label="חיפוש חופשי בהצעות">'+
        '<select id="mym" aria-label="מסכת"></select>'+
        '<select id="myst" aria-label="מצב"><option value="">כל המצבים</option><option value="pending">ממתינה</option><option value="upd">עודכנה</option><option value="accepted">אושרה</option><option value="edited">אושרה בשינוי</option><option value="rejected">נדחתה</option><option value="stale">התיישנה</option></select>'+
        '<input type="text" id="myd" placeholder="דף" aria-label="דף"><select id="myso" aria-label="סדר"><option value="new">החדשות תחילה</option><option value="old">הישנות תחילה</option><option value="loc">לפי מסכת ודף</option></select></div>'+
        '<div id="myl"></div></div>';
      document.body.appendChild(o);
      const upd=()=>{MFIL.q=$('#myq').value;MFIL.mas=$('#mym').value;MFIL.st=$('#myst').value;MFIL.daf=$('#myd').value.trim();MFIL.sort=$('#myso').value;MSHOW=60;mineList()};
      ['myq','myd'].forEach(i=>$('#'+i).addEventListener('input',()=>{clearTimeout(o.__t);o.__t=setTimeout(upd,200)}));
      ['mym','myst','myso'].forEach(i=>$('#'+i).addEventListener('change',upd))}
    o.style.display='block';document.body.classList.add('mysopen');
    mineList();
    mineLoad(true).then(()=>{if(myOpen())mineList()})}
  function mineClose(){const o=$('#mys');if(o)o.style.display='none';document.body.classList.remove('mysopen')}
  /* תאימות: קריאות ישנות לציור הרשימה */
  function drawSg(){if(myOpen())mineLoad(false).then(()=>{if(myOpen())mineList()})}
  function drawSg2(){if(myOpen())mineList()}
  function dafSortKey(d){const k=dafKey(d);return k===null?0:k}
  function mineList(){
    const box=$('#myl');if(!box)return;
    const mas=[...new Set(MINE.map(x=>x.masechet).filter(Boolean))];
    const sel=$('#mym');if(sel){const keep=MFIL.mas;
      sel.innerHTML='<option value="">כל המסכתות</option>'+mas.map(m=>'<option'+(keep===m?' selected':'')+'>'+esc(m)+'</option>').join('')}
    const q=nonik((MFIL.q||'').trim()),df=(MFIL.daf||'').replace(/[.:\s]/g,'');
    let items=MINE.filter(g=>(!MFIL.mas||g.masechet===MFIL.mas)&&
      (!MFIL.st||(MFIL.st==='upd'?(g.st==='pending'&&g.up):g.st===MFIL.st))&&
      (!df||String(g.daf||'').replace(/[.:\s]/g,'')===df)&&
      (!q||nonik([g.note,g.was,g.reason||'',g.now||'',(g.thread||[]).map(x=>x.txt).join(' '),(g.vers||[]).map(v=>v.note).join(' ')].join(' ')).indexOf(q)>-1));
    if(MFIL.sort==='old')items.sort((a,b)=>a.t-b.t);
    else if(MFIL.sort==='loc')items.sort((a,b)=>String(a.masechet).localeCompare(String(b.masechet),'he')||dafSortKey(a.daf)-dafSortKey(b.daf)||a.t-b.t);
    else items.sort((a,b)=>b.t-a.t);
    const c=$('#myc');if(c)c.textContent=MINE.length+' הצעות'+(items.length!==MINE.length?' · מוצגות '+items.length:'')+(MLOAD?' · טוען '+MLOAD+' מתוך '+MROWS.length+'…':'');
    const offline=SG.filter(g=>!g.sent);
    let h='';
    if(MINEERR)h+='<div class="mycard why">לא ניתן לקרוא את ההצעות כרגע: '+esc(MINEERR)+'</div>';
    offline.forEach(g=>{h+='<div class="mycard"><div class="mym">'+esc(g.daf||'')+' · ממתינה לשליחה (אין חיבור)</div><q>'+esc((g.was||'').slice(0,120))+'</q><div class="myn">'+esc(g.note)+'</div></div>'});
    items.slice(0,MSHOW).forEach(g=>{h+=mineCard(g)});
    if(items.length>MSHOW)h+='<div class="mymore"><button class="b" onclick="MSHOW+=60;mineList()">הצג עוד ('+(items.length-MSHOW)+')</button></div>';
    if(!items.length&&!offline.length&&!MINEERR&&!MLOAD)h+='<div class="mycard mydim">'+(MINE.length?'אין הצעות שמתאימות לסינון.':'עדיין אין הצעות. סמן טקסט בדף, ולחץ "הצע תיקון".')+'</div>';
    h+='<div class="mydim" style="margin-top:12px">ההצעות שלך נראות רק לך ולעורך עד שיאושרו. אין הגבלה על מספר ההצעות.</div>';
    const keepScroll=box.parentElement.parentElement.scrollTop;
    box.innerHTML=h;box.parentElement.parentElement.scrollTop=keepScroll;
    if(MED){const ta=$('#mye');if(ta&&!ta.__f){ta.__f=1;ta.focus();ta.setSelectionRange(ta.value.length,ta.value.length)}}}
  function mineCard(g){
    const id=esc(g.id),ed=MED&&MED.id===g.id;
    const idq="'"+id+"'";
    let h='<div class="mycard'+(g.mnew||ed?' new':'')+'" id="mc-'+id.replace(/[^\w]/g,'_')+'"><div class="mym"><b>'+esc(g.masechet||'')+(g.daf?' · דף '+esc(g.daf):'')+'</b> · '+HD.date(g.t)+' '+stChip(g.st)+
      (g.st==='pending'&&g.up?'<span class="stchip" style="background:#b0721a">עודכנה</span>':'')+tyChip(g.type)+
      (g.from?'<span class="mydim"> · חידוד של הצעה קודמת</span>':'')+
      (g.next&&g.next.length?'<span class="mydim"> · הוגשה ממנה הצעה חדשה</span>':'')+'</div>'+
      '<q>'+esc((g.was||'').slice(0,300))+'</q>';
    if(ed){
      h+='<label class="mydim" for="mye">'+(MED.mode==='edit'?'עריכת ההצעה (הגרסה הקודמת נשמרת)':MED.mode==='again'?'חידוד והגשה מחדש (תיווצר הצעה חדשה, מקושרת לקודמת)':'ליטוש נוסף (תיווצר הצעה חדשה על הנוסח שאושר)')+'</label>'+
        '<textarea id="mye" dir="rtl" oninput="MED.text=this.value;mineDraftSave()">'+esc(MED.text)+'</textarea>'+
        '<div><button class="go" onclick="mineSubmit()">'+(MED.mode==='edit'?'שמור':'הגש')+'</button><button onclick="mineCancel()">ביטול</button><span class="mydim" id="myds"></span></div>';
    }else{
      h+='<div class="myn">'+esc(g.note)+'</div>';
      if((g.st==='rejected'||g.st==='stale')&&g.reason)h+='<div class="why">סיבה: '+esc(g.reason)+'</div>';
      if(g.st==='edited'&&g.now)h+='<div class="why" style="color:#5f7f2e">נכנס בנוסח: '+esc(g.now)+'</div>';
      if(g.vers&&g.vers.length)h+='<details><summary>גרסאות קודמות ('+g.vers.length+')</summary>'+g.vers.slice().reverse().map(v=>'<div><span class="mydim">'+HD.dateTime(v.t)+'</span><br>'+esc(v.note)+'</div>').join('')+'</details>';
      h+=thrHTML(g);
      if(g.st==='pending')h+='<button onclick="mineStart('+idq+',\'edit\')">ערוך</button><button onclick="mineDel('+idq+')">משוך את ההצעה</button>';
      if(g.st==='rejected'||g.st==='stale')h+='<button class="go" onclick="mineStart('+idq+',\'again\')">חדד והגש מחדש</button>';
      if(g.st==='accepted'||g.st==='edited')h+='<button onclick="mineStart('+idq+',\'polish\')">הצע ליטוש נוסף</button>';
      h+='<button onclick="mineGo('+idq+')">קפוץ למקום</button>';
      h+='<div class="sgrep"><input type="text" maxlength="500" placeholder="תשובה או שאלה לעורך" onkeydown="if(event.key===\'Enter\')mineReply('+idq+',this)">'+
        '<button onclick="mineReply('+idq+',this.previousElementSibling)">שלח</button></div>';
    }
    return h+'</div>'}
  /* ---- עריכה במקום, חידוד וליטוש ---- */
  function mineDraftKey(id,mode){return 'lg-my-draft-'+id+'-'+mode}
  function mineDraftSave(){if(!MED)return;try{localStorage.setItem(mineDraftKey(MED.id,MED.mode),MED.text);const s=$('#myds');if(s)s.textContent='הטיוטה נשמרה'}catch(e){}}
  function mineStart(id,mode){
    const g=MINE.find(x=>x.id===id);if(!g)return;
    let dr=null;try{dr=localStorage.getItem(mineDraftKey(id,mode))}catch(e){}
    MED={id,mode,text:dr!==null&&dr!==undefined?dr:(mode==='polish'?(g.now||g.note):g.note)};
    mineList()}
  function mineCancel(){if(MED){try{localStorage.removeItem(mineDraftKey(MED.id,MED.mode))}catch(e){}}MED=null;mineList()}
  async function mineSubmit(){
    if(!MED)return;const g=MINE.find(x=>x.id===MED.id);if(!g)return;
    const note=(MED.text||'').trim();
    if(!note){alert('כתוב את ההצעה.');return}
    if(/(https?:\/\/|www\.)/i.test(note)){alert('הצעה שיש בה קישור אינה מתקבלת.');return}
    try{
      if(MED.mode==='edit'){
        await papi('/mine/edit',{id:g.id,note,type:g.type});
        toast('ההצעה עודכנה. הגרסה הקודמת נשמרה.')}
      else{
        const i=pident();
        const was=MED.mode==='polish'?(g.now||g.note):g.was;
        await api('/suggest',{method:'POST',body:JSON.stringify({slug:g.slug,masechet:g.masechet,daf:g.daf,uid:g.uid,k:g.k,ctx:g.ctx,
          was,note,name:localStorage.getItem('lg-sg-name')||g.name||'',type:g.type,pid:i.pid,pt:i.pt,from:g.id,hp:'',grp:sgGrp()})});
        toast(MED.mode==='again'?'ההצעה המחודדת נשלחה והיא מקושרת לקודמת.':'הצעת הליטוש נשלחה.')}
      try{localStorage.removeItem(mineDraftKey(MED.id,MED.mode))}catch(e){}
      MED=null;await mineLoad();mineList()}
    catch(e){alert(e.message||'השליחה נכשלה. הטקסט נשמר כטיוטה, נסה שוב.')}}
  async function mineDel(id){if(!confirm('למשוך את ההצעה? אפשר רק כל עוד לא טופלה.'))return;
    try{await papi('/mine/delete',{id});await mineLoad();mineList();toast('ההצעה נמשכה.')}
    catch(e){alert(e.message)}}
  async function mineReply(id,inp){const t=(inp.value||'').trim();if(!t)return;
    try{await papi('/mine/reply',{id,text:t});inp.value='';await mineLoad();mineList()}catch(e){alert(e.message)}}
  function sgClear(){if(SG.some(g=>!g.sent)&&!confirm('יש הצעה שטרם נשלחה. למחוק בכל זאת?'))return;SG=SG.filter(g=>!g.sent&&false);saveSG();mineList()}
  /* ---- קפיצה למקום ---- */
  function mineFlashK(k){
    const el=k&&$('#flow').querySelector('[data-ek="'+k+'"]');if(!el)return false;
    toEl(el);el.classList.add('sgpulse');setTimeout(()=>el.classList.remove('sgpulse'),4000);return true}
  function mineGo(id){
    const g=MINE.find(x=>x.id===id);if(!g)return;
    if(g.slug!==SLUG){try{sessionStorage.setItem('lg-jumpk',g.k||'')}catch(e){}
      location.href=g.slug+'.html#'+(g.uid?'u='+encodeURIComponent(g.uid):'daf='+encodeURIComponent(g.daf||''));return}
    mineClose();
    let pi=-1;D.pages.forEach((p,i)=>{if(pi<0&&p.units.some(x=>String(x.id)===String(g.uid)))pi=i});
    if(pi>=0)jump(pi,g.uid);
    else{D.pages.forEach((p,i)=>{if(pi<0&&p.daf===g.daf)pi=i});if(pi<0){toast('המקום לא נמצא: הדף השתנה מאז ההצעה.');return}render(secOf(pi));toDaf(pi)}
    setTimeout(()=>{if(!mineFlashK(g.k)){const e=$('#u'+g.uid);if(e)e.classList.add('hit')}},400)}
  try{const jk=sessionStorage.getItem('lg-jumpk');if(jk!==null){sessionStorage.removeItem('lg-jumpk');setTimeout(()=>mineFlashK(jk),1800)}}catch(e){}
  (function(){const st=document.createElement('style');st.textContent='.sgpulse{outline:3px solid #c9a24a;background:rgba(201,162,74,.22);transition:background 1s}';document.head.appendChild(st)})();
  /* ---- זהות: שם וקישור אישי לכניסה ממכשיר אחר ---- */
  function mineLink(){const i=pident();return location.origin+location.pathname.replace(/[^\/]*$/,'')+SLUG+'.html#me='+i.pid+'.'+i.pt}
  function mineMe(){
    const old=$('#mymod');if(old){old.remove();return}
    const m=document.createElement('div');m.className='modal';m.id='mymod';m.style.zIndex=60;
    m.innerHTML='<div class="box"><h3>הזהות שלי</h3>'+
      '<label for="myname">השם שיופיע בהצעות שלך (לא חובה)</label><input type="text" id="myname" maxlength="80" value="'+esc(localStorage.getItem('lg-sg-name')||'')+'" style="width:100%;box-sizing:border-box;font:inherit">'+
      '<p style="margin:10px 0 4px"><b>קישור אישי</b></p>'+
      '<div class="dr" style="font-size:14px">פתיחת הקישור במכשיר אחר מחברת אותו להצעות שלך, בלי הרשמה ובלי סיסמה. שמור אותו במקום פרטי, ואל תשלח אותו לאחרים: מי שמחזיק בו יכול לראות ולערוך את ההצעות שלך.</div>'+
      '<input type="text" id="mylink" readonly value="'+esc(mineLink())+'" style="width:100%;box-sizing:border-box;font:inherit;font-size:13px;direction:ltr;margin-top:6px" onfocus="this.select()">'+
      '<div class="btns"><button class="go" onclick="mineMeSave()">שמור שם</button><button onclick="mineLinkCopy()" id="mycp">העתק את הקישור</button><button onclick="mineMe()">סגירה</button></div></div>';
    document.body.appendChild(m);
    m.addEventListener('click',e=>{if(e.target===m)m.remove()})}
  function mineMeSave(){try{localStorage.setItem('lg-sg-name',$('#myname').value.trim())}catch(e){}toast('השם נשמר.');$('#mymod').remove()}
  function mineLinkCopy(){const v=$('#mylink').value,done=()=>{const b=$('#mycp');b.textContent='הועתק ✓'};
    if(navigator.clipboard&&navigator.clipboard.writeText)navigator.clipboard.writeText(v).then(done,()=>{$('#mylink').select();document.execCommand('copy');done()});
    else{$('#mylink').select();try{document.execCommand('copy');done()}catch(e){}}}
  /* כניסה בקישור אישי: מאמץ את הזהות שבקישור (באישור), ופותח את המסך */
  (function(){
    const m=(ME_HASH||'').match(/me=([a-z0-9]{8,20})\.([a-z0-9]{8,80})/);if(!m)return;
    const me0=pident();
    setTimeout(()=>{
      if(me0.pid!==m[1]){
        const unsent=SG.some(g=>!g.sent);
        if(!confirm('הקישור מחבר את המכשיר הזה להצעות של מציע קיים.'+(unsent?'\nיש במכשיר הצעה שטרם נשלחה, והיא תישלח בשם המציע החדש.':'')+'\nלחבר?'))return;
        try{localStorage.setItem('lg-pid',m[1]);localStorage.setItem('lg-pt',m[2]);localStorage.setItem('lg-lamed-sync','1');MCACHE={};localStorage.removeItem(MCK)}catch(e){}
        SG.forEach(g=>{if(!g.sent){g.pid=m[1];g.pt=m[2]}});saveSG()}
      try{history.replaceState(null,'',location.pathname+location.search+'#p='+cur)}catch(e){}
      mineOpen()},1200)})();
  document.addEventListener('keydown',e=>{if(e.key==='Escape'&&myOpen()&&!$('#mymod')){mineClose()}});
  setTimeout(()=>{mineLoad(false)},3000);setInterval(()=>{if(!document.hidden)mineLoad(false).then(()=>{if(myOpen()&&!MED)mineList()})},180000);

  /* ---- המנהל: תור ההצעות ---- */
  let SQCUR=0,SQUNDO=null,SQSKIP=new Set();
  /* תור גדול: דף אחד בכל פעם מן הנקודה, עם סינון (מציע / דף / סוג / עודכנה) */
  let SQF={pid:'',daf:'',ty:'',up:0},SQPAGE=0,SQMATCH=0,SQPROPS=[],SQSIZE=25,SQCNT={},SQBULK=false,SQMSG=[];
  function sqAlert(m){if(SQBULK)SQMSG.push(m);else alert(m)}
  async function queueLoad(){
    if(!isAdmin()||!admKey()){sqBadge();return}
    try{const p=['slug='+SLUG,'page='+SQPAGE,'size='+SQSIZE];
      if(SQF.pid)p.push('pid='+encodeURIComponent(SQF.pid));
      if(SQF.daf)p.push('daf='+encodeURIComponent(SQF.daf));
      if(SQF.ty)p.push('ty='+SQF.ty);
      if(SQF.up)p.push('up=1');
      const j=await api('/queue?'+p.join('&'));
      QQ=j.items||[];QQTOT=j.total||0;SQMATCH=j.matched||0;SQPROPS=j.proposers||[];SQCNT=j.counts||{};QQERR='';
      if(SQPAGE>0&&!QQ.length&&SQMATCH>0){SQPAGE=Math.max(0,Math.ceil(SQMATCH/SQSIZE)-1);return queueLoad()}}
    catch(e){QQERR=e.message||'שגיאה'}
    sqBadge();sqMark();
    if($('#sgq')&&$('#sgq').classList.contains('open'))drawSq()}
  function sqBadge(){const b=$('#sqbtn');if(!b)return;
    if(!isAdmin()){b.style.display='none';return}
    b.style.display='';const n=SQCNT[SLUG]||0;
    b.innerHTML='<svg class="ic" aria-hidden="true"><use href="#i-inbox"/></svg>'+(admKey()?('הצעות ממתינות<span class="badge">'+n+'</span>'+(QQTOT>n?' <small>(בכל המסכתות: '+QQTOT+')</small>':'')):'הצעות ממתינות - הזן מפתח');
    b.classList.toggle('on',n>0)}
  function sqFilterBar(){
    const sel=(id,opts,cur,fn)=>'<select id="'+id+'" onchange="'+fn+'">'+opts.map(o=>'<option value="'+esc(o[0])+'"'+(cur===o[0]?' selected':'')+'>'+esc(o[1])+'</option>').join('')+'</select>';
    return '<div class="sgbar">'+
      sel('sqfp',[['','כל המציעים']].concat(SQPROPS.map(x=>[x.pid,(x.name||'בלי שם')+' ('+x.n+')'])),SQF.pid,"SQF.pid=this.value;SQPAGE=0;queueLoad()")+
      sel('sqft',[['','כל הסוגים']].concat(Object.keys(STYPES).map(t=>[t,STYPES[t][0]])),SQF.ty,"SQF.ty=this.value;SQPAGE=0;queueLoad()")+
      '<input type="text" id="sqfd" placeholder="דף" size="5" value="'+esc(SQF.daf)+'" onchange="SQF.daf=this.value.trim();SQPAGE=0;queueLoad()" aria-label="דף">'+
      '<label><input type="checkbox" '+(SQF.up?'checked ':'')+'onchange="SQF.up=this.checked?1:0;SQPAGE=0;queueLoad()"> עודכנו בלבד</label>'+
      '<button class="'+(SQF.ty==='style'?'on':'')+'" onclick="sqStyleFilter()" title="כל ההצעות לשינוי סגנון מרוכזות יחד: אשר אחת-אחת (Enter), או את כל ההצעות מאותו סוג של אותו מציע">הצעות סגנון'+(SQF.ty==='style'?' ✓':'')+'</button></div>'}
  function sqPager(){
    const pages=Math.max(1,Math.ceil(SQMATCH/SQSIZE));
    return '<div class="sgbar"><button '+(SQPAGE>0?'':'disabled ')+'onclick="SQPAGE--;queueLoad()">הקודם</button>'+
      '<span class="dr">עמוד '+(SQPAGE+1)+' מתוך '+pages+' · '+SQMATCH+' הצעות</span>'+
      '<button '+(SQPAGE+1<pages?'':'disabled ')+'onclick="SQPAGE++;queueLoad()">הבא</button></div>'}
  function sqBulkBar(){
    return '<div class="sgbar sgbulk" id="sqbulk" hidden><span id="sqbn"></span><button class="ok" onclick="sqBulkAcceptSel()">אשר מסומנות</button><button onclick="sqBulkRejectSel()">דחה מסומנות</button><button class="q" onclick="sqSelAll()">סמן את כל הדף</button></div>'}
  function sqBulkShow(){const n=document.querySelectorAll('#sgqb .sqsel:checked').length,b=$('#sqbulk');if(!b)return;b.hidden=!n;const c=$('#sqbn');if(c)c.textContent=n+' מסומנות'}
  document.addEventListener('change',e=>{if(e.target&&e.target.classList&&e.target.classList.contains('sqsel'))sqBulkShow()});
  function sqSelIds(){return [...document.querySelectorAll('#sgqb .sqsel:checked')].map(x=>x.dataset.id)}
  function sqSelAll(){const a=[...document.querySelectorAll('#sgqb .sqsel')];const on=a.some(x=>!x.checked);a.forEach(x=>x.checked=on)}
  async function sqBulkAcceptSel(){
    const ids=sqSelIds();if(!ids.length){toast('לא סומנו הצעות.');return}
    if(!confirm('לאשר '+ids.length+' הצעות מסומנות? הצעת נוסח תוחל על הטקסט; הצעה שלא אותרה תדולג ותדווח.'))return;
    SQBULK=true;SQMSG=[];let n=0;
    for(const id of ids){const before=QQ.length;await sqDecide(id,'accepted');if(QQ.length<before)n++}
    SQBULK=false;
    toast('אושרו '+n+' מתוך '+ids.length+(SQMSG.length?'. '+(ids.length-n)+' דולגו (לא אותרו או השתנו).':'.'),6000);
    queueLoad()}
  async function sqBulkRejectSel(){
    const ids=sqSelIds();if(!ids.length){toast('לא סומנו הצעות.');return}
    const reason=prompt('סיבת הדחייה לכל '+ids.length+' ההצעות (לא חובה, המציעים יראו אותה):','');if(reason===null)return;
    for(let i=0;i<ids.length;i+=25){
      const part=ids.slice(i,i+25);
      try{await api('/bulk',{method:'POST',body:JSON.stringify({ids:part,st:'rejected',reason})})}catch(e){alert('הדחייה נעצרה: '+e.message);break}
      jrLog(QQ.filter(g=>part.indexOf(g.id)>-1).map(g=>({id:'sg-'+g.id,t:Date.now(),slug:SLUG,daf:g.daf,k:g.k,src:'suggest',was:g.was,now:g.note,neg:1,why:reason,ctx:g.ctx})))}
    toast('נדחו '+ids.length+' הצעות.');queueLoad()}
  /* הצעה שהמציע עדכן: הגרסה הקודמת מול הנוכחית */
  function sqUpd(g){
    if(!g.up||!(g.vers&&g.vers.length))return '';
    const prev=g.vers[g.vers.length-1];
    return '<span class="stchip" style="background:#b0721a">עודכנה</span><div class="sqctx"><small>הגרסה הקודמת ('+HD.dateTime(prev.t)+'):</small> <del style="color:#a83c2f;background:#fbe5e1">'+esc(prev.note)+'</del><br><small>עכשיו:</small> <ins style="color:#2e6b3f;background:#e3f3e6;text-decoration:none">'+esc(g.note)+'</ins></div>'}
  function sqOrdered(){const S=slotsFull(),ok=[],lost=[];
    QQ.forEach(g=>{if(SQSKIP.has(g.id))return;const s=sqLocate(g,S);(s?ok:lost).push([g,s])});
    return {S,ok,lost}}
  function drawSq(){const box=$('#sgqb');if(!box)return;
    const {ok,lost}=sqOrdered();let h='';
    if(QQERR)h+='<div class="edsum" style="color:#a83c2f">לא ניתן לקרוא את התור: '+esc(QQERR)+'</div>';
    h+=sqFilterBar()+sqBulkBar();
    h+='<div class="sgbar"><button onclick="sqBulkPage()">אשר/דחה לפי דף</button><button onclick="sqBulkWho()">דחה את כל הצעות מציע</button>'+
       '<button onclick="sqUndo()" title="Ctrl+Z">בטל פעולה אחרונה</button></div><div class="sgkeys dr">מקשים: <kbd>↑</kbd><kbd>↓</kbd> מעבר · אשר <kbd>A</kbd> · דחה <kbd>D</kbd> · דלג <kbd>S</kbd> · ערוך <kbd>E</kbd> · השב <kbd>R</kbd></div>';
    if(SQSKIP.size)h+='<div class="dr">'+SQSKIP.size+' הצעות נדחו לאחר כך <button onclick="SQSKIP.clear();drawSq()">הצג שוב</button></div>';
    if(lost.length){h+='<h3>התיישנו או לא אותרו</h3><div class="dr">הטקסט השתנה מאז ההצעה, או שהמקום לא נמצא. אינן נכנסות בעיוורון.</div>';
      lost.forEach(([g])=>{h+=sqRow(g,null)})}
    /* הצעות סותרות: כמה הצעות על אותו מקום, זו לצד זו */
    const by={};ok.forEach(([g,s])=>{(by[s.k]=by[s.k]||[]).push([g,s])});
    h+='<h3>'+SQMATCH+' הצעות ממתינות ב'+esc(D.masechet)+' · מוצגות '+ok.length+'</h3>';
    if(!ok.length&&!lost.length)h+='<div class="edsum">אין הצעות ממתינות.</div>';
    let n=0;
    for(const k in by){const grp=by[k];
      if(grp.length>1){h+='<div class="dr">הצעות סותרות על אותו מקום:</div><div class="sgconf">'+grp.map(([g,s])=>sqRow(g,s,n++)).join('')+'</div>'}
      else h+=sqRow(grp[0][0],grp[0][1],n++)}
    h+=sqPager();
    box.innerHTML=h;sqCurPaint()}
  function sqCurPaint(){const rows=[...document.querySelectorAll('#sgqb .sgrow[data-id]')];
    rows.forEach((r,i)=>r.classList.toggle('cur',i===SQCUR));
    const c=rows[SQCUR];if(c&&c.scrollIntoView)c.scrollIntoView({block:'nearest'})}
  function sqRow(g,s,n){
    const when=HD.dateTime(g.t),id=esc(g.id);
    const st=STYPES[g.type]||STYPES.nusach;
    /* בהצעה על הנוסח: מחוק באדום ומוסף בירוק, בהקשר השורה, כמו עקוב אחר שינויים */
    let ctx='';
    if(g.edit&&s){ctx=sqEditCtx(g,s)}
    else if(g.edit){ctx='<q>'+esc((g.was||'').slice(0,120))+'</q><small>לא אותר בקובץ הנוכחי: הטקסט השתנה מאז ההצעה</small>'}
    else if(s&&g.type==='nusach'&&s.t.indexOf(g.was)>-1){
      const i=s.t.indexOf(g.was);
      ctx='<div class="sqctx">'+esc(s.t.slice(Math.max(0,i-60),i))+'<del style="color:#a83c2f;background:#fbe5e1">'+esc(g.was)+'</del><ins style="color:#2e6b3f;background:#e3f3e6;text-decoration:none">'+esc(g.note)+'</ins>'+esc(s.t.slice(i+g.was.length,i+g.was.length+60))+'</div>';
    }else if(s){ctx='<div class="sqctx">'+esc(s.t).replace(esc(g.was),'<mark>'+esc(g.was)+'</mark>')+'</div>'}
    else ctx='<q>'+esc((g.was||'').slice(0,120))+'</q><small>לא אותר בקובץ הנוכחי</small>';
    const known=g.pid?true:false;
    return '<div class="sgrow'+(g.tr?' trust':'')+(s?'':' edlost')+'" data-id="'+id+'" data-n="'+(n===undefined?-1:n)+'" style="border-right:4px solid '+st[2]+'">'+
      '<label class="sqck"><input type="checkbox" class="sqsel" data-id="'+id+'" aria-label="סמן הצעה"> </label><small>'+esc(g.daf||'')+(g.name?' · '+esc(g.name):' · בלי שם')+' · '+when+'</small> '+tyChip(g.type)+(g.tr?'<span class="stchip" style="background:#c9a24a">מהימן</span>':'')+
      (g.mnew?'<span class="stchip" style="background:#a83c2f">הודעה חדשה</span>':'')+(g.sk?'<span class="stchip" style="background:#6a4a8f">'+esc(SKL[g.sk]||'')+'</span>':'')+sqUpd(g)+ctx+
      ((g.type==='nusach'&&!g.edit)?'':'<b>'+esc(g.note)+'</b>')+thrHTML(g,true)+
      '<div class="sgact">'+(s?'<button class="ok" onclick="sqDecide(\''+id+'\',\'accepted\')">אשר <kbd>A</kbd></button>':
        '<button onclick="sqDecide(\''+id+'\',\'stale\')">סמן כהתיישנה</button>')+
      '<button class="no" onclick="sqDecide(\''+id+'\',\'rejected\')">דחה <kbd>D</kbd></button>'+
      '<details class="sgmore"><summary>עוד</summary><div>'+
      (s&&g.type==='nusach'&&!g.edit?'<button onclick="sqDecide(\''+id+'\',\'edited\')">ערוך ואשר <kbd>E</kbd></button>':'')+
      (s&&g.edit&&g.pid?'<button onclick="sqSame(\''+id+'\')" title="כל ההצעות של המציע הזה מהסוג הזה, עם תצוגה מקדימה">אשר את כל מאותו סוג</button>':'')+
      (s?'<button onclick="sqJump(\''+id+'\')">הצג בדף</button>':'')+
      '<button onclick="sqSkip(\''+id+'\')">דלג <kbd>S</kbd></button><button onclick="sqReply(\''+id+'\')">השב <kbd>R</kbd></button>'+
      (known?'<button onclick="sqTrust(\''+esc(g.pid)+'\','+(g.tr?0:1)+')" title="הצעותיו יופיעו ראשונות בתור">'+(g.tr?'בטל מהימנות':'סמן כמהימן')+'</button>':'')+
      '</div></details></div></div>'}
  function sqSkip(id){SQSKIP.add(id);drawSq()}
  async function sqReply(id){const t=prompt('תשובה קצרה למציע (בלי להכריע):');if(!t||!t.trim())return;
    try{const j=await api('/reply',{method:'POST',body:JSON.stringify({id,text:t.trim()})});
      const i=QQ.findIndex(x=>x.id===id);if(i>-1)QQ[i]=j.rec;drawSq();toast('התשובה נשלחה למציע.')}
    catch(e){alert(e.message)}}
  async function sqTrust(pid,on){try{await api('/trust',{method:'POST',body:JSON.stringify({pid,on})});await queueLoad();toast(on?'המציע סומן כמהימן.':'המהימנות בוטלה.')}catch(e){alert(e.message)}}
  /* יומן התיקונים: חומר הלמידה. נכתב לנקודת הקליטה בלבד (פרטי), בלי לעצור את המנהל */
  function jrLog(items){try{api('/journal',{method:'POST',body:JSON.stringify({items})}).catch(()=>{})}catch(e){}}
  async function sqDecide(id,st,reasonIn){
    const g=QQ.find(x=>x.id===id);if(!g)return;
    let edit=null,now='',reason='';
    const accept=(st==='accepted'||st==='edited');
    if(accept&&g.edit)return sqDecideEdit(id,st);
    if(accept&&g.type==='nusach'){
      const s=sqLocate(g,slotsFull());
      if(!s){sqAlert('ההצעה לא אותרה בקובץ הנוכחי ואי אפשר להחיל אותה.');return}
      now=g.note;
      if(st==='edited'){const v=prompt('הנוסח שייכנס במקום הקטע המסומן:',g.note);if(v===null)return;now=v.trim();if(!now)return}
      const old=ED.find(x=>x.k===s.k);
      const curT=old?old.now:s.t, curH=old?(old.nowH!==undefined?old.nowH:esc(old.now)):s.h;
      const wasT=old?old.was:s.t, wasH=old?(old.wasH!==undefined?old.wasH:s.h):s.h;
      if(curT.indexOf(g.was)<0){sqAlert('הקטע שהוצע עליו התיקון כבר אינו בשורה הזאת.');return}
      const nowH=replaceInHTML(curH,g.was,now);
      const nowT=curT.replace(g.was,now);
      const cls=(s.c||'').split(' ').filter(c=>PCLS.indexOf(c)>-1).join(' ');
      edit={k:s.k,was:wasT,now:nowT,wasH,nowH:nowH!==null?nowH:esc(nowT),wasP:old?old.wasP:cls,
            daf:s.daf,ctx:{b:'',a:''},t:Date.now(),pub:0,by:'הצעה מהאתר'+(g.name?' - '+g.name:''),sg:g.id};
      if(old&&old.ps!==undefined){edit.ps=old.ps;edit.psw=old.psw}
      SQUNDO={id,g,prev:old||null,k:s.k,wasH:curH};
      if(old)ED=ED.filter(x=>x!==old);
      ED.push(edit);saveED();
    }else if(accept){SQUNDO={id,g,prev:null,k:'',wasH:''};now=g.note}
    else{
      reason=reasonIn!==undefined?reasonIn:(prompt(st==='stale'?'סיבה קצרה (לא חובה):':'סיבת הדחייה (בשורה אחת, לא חובה - המציע יראה אותה):','')||'');
      SQUNDO={id,g,prev:null,k:'',wasH:''};
    }
    try{await api('/decide',{method:'POST',body:JSON.stringify({id,st,now,reason,edit,sty:D.sty})})}
    catch(e){if(edit){ED=ED.filter(x=>x!==edit);saveED();if(SQUNDO&&SQUNDO.prev)ED.push(SQUNDO.prev)}sqAlert('ההכרעה לא נרשמה: '+e.message);return}
    if(!accept)jrLog([{id:'sg-'+id,t:Date.now(),slug:SLUG,daf:g.daf,k:g.k,src:'suggest',was:g.was,now:g.note,neg:1,why:reason,ctx:g.ctx}]);   /* הדחייה היא דוגמה שלילית; האישור נרשם בצד השרת מן העריכה עצמה */
    QQ=QQ.filter(x=>x.id!==id);QQTOT=Math.max(0,QQTOT-1);
    if(edit){applyTextNow(edit);drawEd();pubSoon();syncSoon();toast('התיקון הוחל. Ctrl+Z מבטל.')}
    else toast(accept?'ההצעה סומנה כמאושרת. ההחלה ידנית.':st==='stale'?'ההצעה סומנה כהתיישנה.':'ההצעה נדחתה והמציע יראה את הסיבה.');
    sqBadge();drawSq()}
  async function sqUndo(){
    const u=SQUNDO;if(!u){toast('אין מה לבטל.');return}
    SQUNDO=null;
    try{await api('/decide',{method:'POST',body:JSON.stringify({id:u.id,st:'pending'})})}catch(e){alert('הביטול לא נרשם: '+e.message);return}
    if(u.struct){
      /* ביטול שינוי מבנה: מחזירים את הנתונים למקורם בטעינה מחדש של הדף */
      edKeys();tomb(u.struct.k);ED=ED.filter(x=>x!==u.struct);saveED();
      try{await api('/edits',{method:'PUT',body:JSON.stringify({slug:SLUG,edits:TOMB,sty:D.sty})})}catch(e){}
      location.reload();return}
    if(u.k){
      const cur=ED.find(x=>x.sg===u.id);
      if(cur){edKeys();tomb(cur.k);ED=ED.filter(x=>x!==cur)}
      if(u.prev)ED.push(u.prev);
      dataSet(u.k,u.wasH);SLOTS=null;saveED();
      const el=$('#flow').querySelector('[data-ek="'+u.k+'"]');if(el)setHTML(el,u.wasH);
      drawEd();pubSoon();syncSoon()}
    QQ.push(Object.assign({},u.g,{st:'pending'}));QQTOT++;
    sqBadge();sqMark();drawSq();toast('הפעולה בוטלה וההצעה חזרה לתור.')}
  /* הכרעה בצרור: לפי דף, או כל הצעות מציע אחד */
  async function sqBulkPage(){
    const dafs=[...new Set(QQ.map(g=>g.daf).filter(Boolean))];if(!dafs.length){toast('אין הצעות.');return}
    const d=prompt('לאיזה דף? ('+dafs.join(', ')+')\nאחר כך תישאל אם לאשר או לדחות.');if(!d)return;
    const list=QQ.filter(g=>g.daf===d.trim());if(!list.length){toast('אין הצעות בדף הזה.');return}
    if(confirm('לאשר את כל '+list.length+' ההצעות בדף '+d+'? (אישור = כן, ביטול = ימשיך לשאלת דחייה)')){
      for(const g of list){if(g.type==='nusach'||true)await sqDecide(g.id,'accepted')}return}
    if(confirm('לדחות את כל '+list.length+' ההצעות בדף '+d+'?'))await sqBulkReject(list.map(g=>g.id),'')}
  async function sqBulkWho(){
    const names=[...new Set(QQ.map(g=>g.name||'(בלי שם)'))];if(!names.length){toast('אין הצעות.');return}
    const n=prompt('דחיית כל ההצעות של מציע. איזה שם?\n'+names.join(', '));if(!n)return;
    const list=QQ.filter(g=>(g.name||'(בלי שם)')===n.trim());if(!list.length){toast('אין הצעות בשם הזה.');return}
    if(confirm('לדחות '+list.length+' הצעות של "'+n+'"?'))await sqBulkReject(list.map(g=>g.id),'')}
  async function sqBulkReject(ids,reason){
    try{await api('/bulk',{method:'POST',body:JSON.stringify({ids,st:'rejected',reason})})}catch(e){alert(e.message);return}
    jrLog(QQ.filter(g=>ids.indexOf(g.id)>-1).map(g=>({id:'sg-'+g.id,t:Date.now(),slug:SLUG,daf:g.daf,k:g.k,src:'suggest',was:g.was,now:g.note,neg:1,why:reason,ctx:g.ctx})));
    QQ=QQ.filter(g=>ids.indexOf(g.id)<0);QQTOT=Math.max(0,QQTOT-ids.length);sqBadge();drawSq();toast('נדחו '+ids.length+' הצעות.')}
  /* מקשים בתור: חצים, A אשר, D דחה, S דלג, E ערוך ואשר, R השב, Ctrl+Z ביטול */
  document.addEventListener('keydown',e=>{
    const p=$('#sgq');if(!p||!p.classList.contains('open')||!isAdmin())return;
    const t=e.target;if(/^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName)||t.isContentEditable)return;
    const rows=[...document.querySelectorAll('#sgqb .sgrow[data-id]')];if(!rows.length&&!(e.ctrlKey&&e.code==='KeyZ'))return;
    const cur=rows[SQCUR],id=cur&&cur.dataset.id;
    if(e.ctrlKey&&!e.altKey&&e.code==='KeyZ'){e.preventDefault();sqUndo();return}
    if(e.ctrlKey||e.altKey||e.metaKey)return;
    if(e.key==='ArrowDown'||e.key==='j'){e.preventDefault();SQCUR=Math.min(rows.length-1,SQCUR+1);sqCurPaint()}
    else if(e.key==='ArrowUp'||e.key==='k'){e.preventDefault();SQCUR=Math.max(0,SQCUR-1);sqCurPaint()}
    else if(!id)return;
    else if(e.code==='KeyA'||(e.key==='Enter'&&SQF.ty==='style')){e.preventDefault();sqDecide(id,'accepted')}
    else if(e.code==='KeyD'){e.preventDefault();sqDecide(id,'rejected')}
    else if(e.code==='KeyS'){e.preventDefault();sqSkip(id)}
    else if(e.code==='KeyE'){e.preventDefault();sqDecide(id,'edited')}
    else if(e.code==='KeyR'){e.preventDefault();sqReply(id)}
  },true);

  /* ---- הלמידה היומית: סיכום קצר פעם ביום, רק אם נלמד משהו. בלי בקשת אישור. ---- */
  let LN=null;
  async function lnLoad(){if(!isAdmin()||!admKey())return;
    try{const j=await api('/learn');LN=j.summary;LN&&(LN.off=j.off||[]);lnBadge()}catch(e){}}
  function lnBadge(){const b=$('#lnbtn');if(!b)return;
    let seen=0;try{seen=+localStorage.getItem('lg-ln-seen')||0}catch(e){}
    const w=LN?Date.parse(LN.when):0;
    const any=LN&&(LN.newRules||LN.sem||LN.pending);
    b.style.display=(isAdmin()&&any&&w>seen)?'':'none'}
  function lnOpen(){panel('ln');lnDraw();try{localStorage.setItem('lg-ln-seen',String(Date.now()))}catch(e){}lnBadge()}
  function lnDraw(){const box=$('#lnb');if(!box)return;
    if(!LN){box.innerHTML='<div class="edsum">עדיין לא נלמד דבר.</div>';return}
    let h='<div class="edsum">נלמדו '+(LN.newRules||0)+' כללים מכניים חדשים, '+LN.sem+' שיפורים סמנטיים, '+LN.pending+' ממתינים לחזרה נוספת. (גרסה '+LN.ver+')</div>';
    h+='<div class="dr">הכללים חלים רק על ריצות עתידיות של המנועים, ולעולם לא על טקסט שכבר ליטשת.</div>';
    (LN.rules||[]).forEach(r=>{const off=(LN.off||[]).indexOf(r.id)>-1;
      h+='<div class="sgrow"><b>'+esc(r.find)+' ← '+esc(r.repl)+'</b> <small>('+r.n+' פעמים)</small>'+(off?' <span class="stchip" style="background:#7a7a7a">בוטל</span>':'')+
         '<div class="sqctx">'+esc(r.ex)+'</div><button onclick="lnOff(\''+esc(r.id)+'\','+(off?1:0)+')">'+(off?'החזר כלל':'בטל כלל זה')+'</button></div>'});
    if((LN.held||[]).length){h+='<h3>ממתינים לחזרה נוספת</h3>';
      LN.held.forEach(r=>{h+='<div class="sgrow"><small>'+esc(r.find)+' ← '+esc(r.repl)+' · '+esc(r.why)+'</small></div>'})}
    box.innerHTML=h}
  async function lnOff(id,on){try{const j=await api('/learn',{method:'POST',body:JSON.stringify({off:id,on:!!on})});LN.off=j.off;lnDraw();toast(on?'הכלל הוחזר.':'הכלל בוטל. הוא לא ייכנס לריצות הבאות.')}catch(e){alert(e.message)}}
  setTimeout(lnLoad,3500);

  /* ---- הערות המנהל לקלוד (6.10.2026) - פרטיות מוחלטת ----
     כפתור "הערה לקלוד" (Ctrl+Alt+H) בעורך: שדה קצר שבו המנהל מסביר את הרעיון
     שמאחורי התיקון. ההערה נשמרת בנקודת הקליטה הפרטית (מאחורי הרשאת מנהל) יחד עם
     המסכת, הדף, הטקסט המסומן, הנוסח לפני ואחרי, ותאריך. אינה עוברת לריפו, לבנייה,
     לקובצי הוורד או לתיקיית השומר. הלומד קורא אותה בכל סבב למידה. */
  let NT=null;
  async function ntLoad(){if(!isAdmin()||!admKey())return;
    try{const j=await api('/notes');NT=j.items||[]}catch(e){NT=null}ntBadge();if(typeof ntMark==='function')ntMark()}
  function ntBadge(){const b=$('#ntbtn');if(!b)return;
    b.style.display=isAdmin()?'':'none';
    const n=NT?NT.filter(x=>!x.learned).length:0;
    b.textContent='הערות לקלוד'+(n?' ('+n+')':'')}
  function dafOfEl(el){const row=el&&el.closest&&el.closest('.row');let r=row;
    while(r){const d=r.querySelector('.dafmark');if(d)return d.dataset.daf||d.textContent;r=r.previousElementSibling}return ''}
  function ntContext(){
    const el=(typeof edEl==='function')?edEl():null;
    const s=getSelection();
    let sel=s&&s.rangeCount?String(s).trim():'';
    const k=el&&el.dataset?el.dataset.ek||'':'';
    const ed=k?ED.find(x=>x.k===k):null;
    if(!sel&&el&&isTxt(el))sel=txtOf(el).trim();
    return {k,sel:sel.slice(0,4000),was:ed?ed.was:'',now:ed?ed.now:(el&&isTxt(el)?txtOf(el):''),daf:dafOfEl(el)}}
  function ntAdd(){
    if(!isAdmin()){return}
    if(!admKey()){alert('כדי לשמור הערה צריך מפתח מנהל במכשיר הזה');return}
    const ctx=ntContext();
    const old=$('#ntm');if(old)old.remove();
    const m=document.createElement('div');m.id='ntm';
    m.style.cssText='position:fixed;z-index:50;left:50%;top:18%;transform:translateX(-50%);background:#fbf8f1;border:1px solid #c9a24a;border-radius:8px;box-shadow:0 8px 30px rgba(0,0,0,.35);padding:14px 16px;width:min(480px,92vw);direction:rtl;font-size:15px';
    m.innerHTML='<b>הערה לקלוד</b><div style="font-size:12px;color:#7a6a45;margin:4px 0 6px">פרטית: רק אתה וקלוד רואים אותה. מה הרעיון שמאחורי התיקון?</div>'+
      (ctx.sel?'<div style="font-size:12px;color:#4a4137;background:#eee9da;border-radius:4px;padding:4px 8px;margin-bottom:6px;max-height:4.2em;overflow:hidden">'+esc(ctx.sel.slice(0,160))+'</div>':'')+
      '<textarea id="ntt" rows="4" style="width:100%;box-sizing:border-box;font:inherit;padding:6px" placeholder="למשל: כשהתנא נזכר בשמו מלא - להדגיש"></textarea>'+
      '<div style="margin-top:8px;display:flex;gap:8px"><button type="button" id="nts" style="background:#c9a24a;border:0;border-radius:5px;padding:5px 16px;font:inherit;font-weight:700;cursor:pointer">שמירה</button>'+
      '<button type="button" id="ntc" style="background:none;border:1px solid #b9ac8e;border-radius:5px;padding:5px 14px;font:inherit;cursor:pointer">ביטול</button></div>';
    document.body.appendChild(m);
    const t=$('#ntt');t.focus();
    $('#ntc').onclick=()=>m.remove();
    m.addEventListener('keydown',e=>{if(e.key==='Escape'){m.remove();e.stopPropagation()}else if(e.key==='Enter'&&(e.ctrlKey||e.metaKey)){$('#nts').click()}});
    $('#nts').onclick=async()=>{const v=t.value.trim();if(!v){flash('ההערה ריקה');return}
      try{const j=await api('/notes',{method:'POST',body:JSON.stringify({op:'add',slug:SLUG,masechet:D.masechet,daf:ctx.daf,k:ctx.k,sel:ctx.sel,was:ctx.was,now:ctx.now,note:v})});
        if(NT)NT.unshift(j.item);else NT=[j.item];ntBadge();if(typeof ntMark==='function')ntMark();m.remove();flash('ההערה נשמרה');if($('#nt')&&$('#nt').classList.contains('open'))ntDraw()}
      catch(e){alert(e.message)}}}
  let NTARCH=false;
  function ntOpen(){panel('nt');ntLoad().then(ntDraw)}
  function ntDraw(){const box=$('#ntb');if(!box)return;
    if(!NT){box.innerHTML='<div class="edsum">אי אפשר לטעון את ההערות (בדוק שיש מפתח מנהל במכשיר).</div>';return}
    let h='<div class="dr">ההערות פרטיות: גלויות רק לך ולקלוד, ואינן נכנסות לאתר, לריפו או לקובצי הוורד.</div>';
    if(!NT.length)h+='<div class="edsum">עדיין אין הערות. בעורך: Ctrl+Alt+H, או הכפתור "הערה לקלוד" בחלונית הסגנונות.</div>';
    /* מצב: חדשה (קלוד טרם למד) / נלמדה. נלמדה יורדת מהתצוגה ונשמרת בארכיון הלמידה */
    const arch=NT.filter(x=>x.learned).length,show=NT.filter(x=>NTARCH?x.learned:!x.learned);
    h+='<div class="sgbar"><button class="'+(NTARCH?'':'on')+'" onclick="NTARCH=false;ntDraw()">חדשות ('+NT.filter(x=>!x.learned).length+')</button>'+
       '<button class="'+(NTARCH?'on':'')+'" onclick="NTARCH=true;ntDraw()">ארכיון הלמידה ('+arch+')</button></div>';
    if(!show.length)h+='<div class="edsum">'+(NTARCH?'הארכיון ריק.':'אין הערות חדשות. קלוד למד את כולן.')+'</div>';
    show.forEach(x=>{h+='<div class="sgrow"><small>'+esc(HD.dateTime(x.t))+' · '+esc(x.masechet||x.slug||'')+(x.daf?' · דף '+esc(x.daf):'')+'</small>'+
      (x.learned?' <span class="stchip" style="background:#2e6b3f">נלמדה</span>':' <span class="stchip" style="background:#b0721a">חדשה</span>')+
      (x.sel?'<div class="sqctx">'+esc(x.sel.slice(0,120))+'</div>':'')+
      '<div>'+esc(x.note)+'</div>'+
      '<button data-id="'+esc(x.id)+'" onclick="ntEdit(this.dataset.id)">עריכה</button> <button data-id="'+esc(x.id)+'" onclick="ntDel(this.dataset.id)">מחיקה</button> <button data-id="'+esc(x.id)+'" onclick="ntLearned(this.dataset.id,'+(x.learned?0:1)+')">'+(x.learned?'סמן כלא נלמד':'סמן כנלמד')+'</button></div>'});
    box.innerHTML=h}
  async function ntEdit(id){const x=(NT||[]).find(y=>y.id===id);if(!x)return;
    const v=prompt('עריכת ההערה:',x.note);if(v===null||!v.trim())return;
    try{const j=await api('/notes',{method:'POST',body:JSON.stringify({op:'edit',id,note:v.trim()})});Object.assign(x,j.item);ntDraw();ntBadge()}catch(e){alert(e.message)}}
  async function ntDel(id){if(!confirm('למחוק את ההערה?'))return;
    try{await api('/notes',{method:'POST',body:JSON.stringify({op:'del',id})});NT=NT.filter(y=>y.id!==id);ntDraw();ntBadge()}catch(e){alert(e.message)}}
  async function ntLearned(id,on){try{await api('/notes',{method:'POST',body:JSON.stringify({op:'learned',id,on:!!on})});
    const x=NT.find(y=>y.id===id);if(x)x.learned=on?Date.now():0;ntDraw();ntBadge();if(typeof ntMark==='function')ntMark()}catch(e){alert(e.message)}}
  document.addEventListener('keydown',e=>{
    if(!EDIT||!isAdmin())return;
    if(e.ctrlKey&&e.altKey&&!e.shiftKey&&!e.metaKey&&e.code==='KeyH'){e.preventDefault();ntAdd()}});
  setTimeout(ntLoad,4000);
