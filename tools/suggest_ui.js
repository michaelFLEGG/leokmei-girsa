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
    '.sgpop{position:fixed;z-index:12;width:min(360px,94vw);background:#fffdf8;border:1px solid #c9b98f;border-radius:8px;box-shadow:0 6px 24px rgba(0,0,0,.28);padding:10px 12px;font-size:15px;line-height:1.5}'+
    '.sgpop h3{margin:0 0 6px;font-size:15px}.sgpop textarea{width:100%;min-height:70px;font:inherit;box-sizing:border-box}'+
    '.sgpop input[type=text]{width:100%;font:inherit;box-sizing:border-box}.sgpop .sel{max-height:64px;overflow:auto;background:#f3efe3;padding:3px 6px;border-radius:4px;font-size:14px}'+
    '.sgtypes{display:flex;flex-wrap:wrap;gap:4px;margin:6px 0}.sgtypes button,.sgchips button{font:inherit;font-size:13px;border:1px solid #d9d1bd;border-radius:12px;background:#fff;padding:1px 9px;cursor:pointer}'+
    '.sgtypes button.on{color:#fff}.sgchips{display:flex;flex-wrap:wrap;gap:4px;margin:4px 0}'+
    '.sgpop .btns{display:flex;gap:8px;margin-top:8px;align-items:center}.sgpop .go{background:#2e6b3f;color:#fff;border:0;border-radius:4px;padding:4px 14px;font:inherit;cursor:pointer}'+
    '.sgpop .dr{font-size:12px;color:#8a7d66}'+
    '.stchip{display:inline-block;color:#fff;border-radius:10px;padding:0 8px;font-size:12px;margin-left:5px}'+
    '.tychip{display:inline-block;border:1px solid;border-radius:10px;padding:0 7px;font-size:12px;margin-left:5px}'+
    '.sgthr{margin:4px 0;padding:3px 8px;border-right:3px solid #d9d1bd;font-size:14px}.sgthr .m{color:#2e5b8a}.sgthr .p{color:#5a5044}'+
    '.sgrow .why{color:#a83c2f;font-size:14px}.sgrow.cur{outline:2px solid #c9a24a}.sgrow.trust{background:#fbf6e4}'+
    '.sgconf{display:flex;gap:8px;flex-wrap:wrap}.sgconf>.sgrow{flex:1 1 45%;border:1px solid #d9d1bd;border-radius:5px;padding:4px 8px}'+
    '.sgrep{display:flex;gap:4px;margin-top:4px}.sgrep input{flex:1;font:inherit;font-size:14px}.sgbar{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0 10px}'+
    '.sgbar select,.sgbar button{font:inherit;font-size:13px}.sgbell{background:#a83c2f;color:#fff;border-radius:9px;padding:0 6px;margin-right:4px;font-size:12px}';
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
      '<textarea id="sgn" maxlength="1900"></textarea>'+
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
      catch(e){why=e.message||'';if(/קישור|נדחה|מדי/.test(why)){g.sent=1;g.bad=why}else fail++}
    }
    saveSG();SGBUSY=false;
    if(ok)toast('ההצעה נשלחה לעורך. תודה רבה. אפשר לעקוב אחריה ב"ההצעות שלי".');
    else if(fail)toast('אין חיבור כרגע. ההצעה נשמרה במכשיר ותישלח בטעינה הבאה.',4500);
    else if(why)toast(why,4500);
    drawSg()}

  /* ---- ההצעות שלי ---- */
  let MINE=[],MINEERR='',MFIL={mas:'',st:''};
  async function mineLoad(markSeen){
    try{const j=await papi('/mine');MINE=j.items||[];MINEERR='';mineBell(j.unseen||0);
      if(markSeen&&j.unseen)papi('/mine/seen',{}).then(()=>mineBell(0)).catch(()=>{})}
    catch(e){MINEERR=/הרשאה/.test(e.message)?'':(e.message||'')}
    }
  function mineBell(n){const b=document.querySelector('button[onclick^="panel(\'sg\')"]');if(!b)return;
    b.innerHTML='ההצעות שלי'+(n?'<span class="sgbell">'+n+'</span>':'')}
  function stChip(st){const s=SSTAT[st]||SSTAT.pending;return '<span class="stchip" style="background:'+s[1]+'">'+s[0]+'</span>'}
  function tyChip(t){const s=STYPES[t]||STYPES.nusach;return '<span class="tychip" style="color:'+s[2]+';border-color:'+s[2]+'">'+s[1]+' '+s[0]+'</span>'}
  function thrHTML(g,admin){return (g.thread||[]).map(x=>'<div class="sgthr"><span class="'+x.from+'">'+(x.from==='m'?'העורך':'המציע')+':</span> '+esc(x.txt)+'</div>').join('')}
  function drawSg(){const box=$('#sgb');if(!box)return;
    mineLoad(true).then(()=>drawSg2());
    drawSg2()}
  function drawSg2(){const box=$('#sgb');if(!box)return;
    const offline=SG.filter(g=>!g.sent);
    const mas=[...new Set(MINE.map(x=>x.masechet).filter(Boolean))];
    const items=MINE.filter(x=>(!MFIL.mas||x.masechet===MFIL.mas)&&(!MFIL.st||x.st===MFIL.st));
    let h='<div class="sgbar"><select id="mfm" onchange="MFIL.mas=this.value;drawSg2()"><option value="">כל המסכתות</option>'+
      mas.map(m=>'<option'+(MFIL.mas===m?' selected':'')+'>'+esc(m)+'</option>').join('')+'</select>'+
      '<select id="mfs" onchange="MFIL.st=this.value;drawSg2()"><option value="">כל המצבים</option>'+
      Object.keys(SSTAT).map(s=>'<option value="'+s+'"'+(MFIL.st===s?' selected':'')+'>'+SSTAT[s][0]+'</option>').join('')+'</select></div>';
    if(MINEERR)h+='<div class="edsum" style="color:#a83c2f">לא ניתן לקרוא את ההצעות כרגע: '+esc(MINEERR)+'</div>';
    offline.forEach(g=>{h+='<div class="sgrow"><small>'+esc(g.daf||'')+' · ממתינה לשליחה (אין חיבור)</small> <q>'+esc((g.was||'').slice(0,80))+'</q><b>'+esc(g.note)+'</b></div>'});
    let lastGrp='';
    items.forEach(g=>{
      if(g.grp&&g.grp!==lastGrp){const n=items.filter(x=>x.grp===g.grp).length;if(n>1)h+='<small class="dr">שליחה אחת, '+n+' שינויים - לכל שינוי החלטה משלו</small>'}
      lastGrp=g.grp||'';
      h+='<div class="sgrow" data-id="'+esc(g.id)+'"><small>'+esc(g.daf||'')+' · '+esc(g.masechet||'')+' · '+new Date(g.t).toLocaleDateString('he-IL')+'</small> '+
        stChip(g.st)+tyChip(g.type)+(g.edited?'<small>(נערכה)</small>':'')+
        '<q>'+esc((g.was||'').slice(0,120))+'</q><b id="mn'+esc(g.id).replace(/[^\w]/g,'_')+'">'+esc(g.note)+'</b>'+
        ((g.st==='rejected'||g.st==='stale')&&g.reason?'<div class="why">סיבה: '+esc(g.reason)+'</div>':'')+
        (g.st==='edited'&&g.now?'<div class="why" style="color:#5f7f2e">נכנס בנוסח: '+esc(g.now)+'</div>':'')+
        thrHTML(g)+
        (g.st==='pending'?'<button onclick="mineEdit(\''+esc(g.id)+'\')">ערוך</button><button onclick="mineDel(\''+esc(g.id)+'\')">מחק</button>':'')+
        '<div class="sgrep"><input type="text" maxlength="500" placeholder="תשובה או שאלה לעורך" onkeydown="if(event.key===\'Enter\')mineReply(\''+esc(g.id)+'\',this)">'+
        '<button onclick="mineReply(\''+esc(g.id)+'\',this.previousElementSibling)">שלח</button></div></div>'});
    if(!items.length&&!offline.length&&!MINEERR)h+='<div class="edsum">אין הצעות להצגה. סמן טקסט בדף, ולחץ "הצע תיקון".</div>';
    h+='<div class="dr" style="margin-top:10px">ההצעות שלך נראות רק לך ולעורך עד שיאושרו.</div>';
    box.innerHTML=h}
  async function mineEdit(id){const g=MINE.find(x=>x.id===id);if(!g)return;
    const v=prompt('ערוך את ההצעה:',g.note);if(v===null||!v.trim())return;
    try{await papi('/mine/edit',{id,note:v.trim(),type:g.type});await mineLoad();drawSg2();toast('ההצעה עודכנה.')}
    catch(e){alert(e.message)}}
  async function mineDel(id){if(!confirm('למחוק את ההצעה? אפשר רק כל עוד לא טופלה.'))return;
    try{await papi('/mine/delete',{id});MINE=MINE.filter(x=>x.id!==id);drawSg2();toast('ההצעה נמחקה.')}
    catch(e){alert(e.message)}}
  async function mineReply(id,inp){const t=(inp.value||'').trim();if(!t)return;
    try{await papi('/mine/reply',{id,text:t});inp.value='';await mineLoad();drawSg2()}catch(e){alert(e.message)}}
  function sgClear(){if(SG.some(g=>!g.sent)&&!confirm('יש הצעה שטרם נשלחה. למחוק בכל זאת?'))return;SG=SG.filter(g=>!g.sent&&false);saveSG();drawSg2()}
  setTimeout(()=>{mineLoad(false)},3000);setInterval(()=>{if(!document.hidden)mineLoad(false)},180000);

  /* ---- המנהל: תור ההצעות ---- */
  let SQCUR=0,SQUNDO=null,SQSKIP=new Set();
  function sqOrdered(){const S=slotsFull(),ok=[],lost=[];
    QQ.forEach(g=>{if(SQSKIP.has(g.id))return;const s=sqLocate(g,S);(s?ok:lost).push([g,s])});
    return {S,ok,lost}}
  function drawSq(){const box=$('#sgqb');if(!box)return;
    const {ok,lost}=sqOrdered();let h='';
    if(QQERR)h+='<div class="edsum" style="color:#a83c2f">לא ניתן לקרוא את התור: '+esc(QQERR)+'</div>';
    h+='<div class="sgbar"><button onclick="sqBulkPage()">אשר/דחה לפי דף</button><button onclick="sqBulkWho()">דחה את כל הצעות מציע</button>'+
       '<button onclick="sqUndo()" title="Ctrl+Z">בטל פעולה אחרונה</button><small class="dr">חצים: מעבר · A אשר · D דחה · S דלג · E ערוך · R השב</small></div>';
    if(SQSKIP.size)h+='<div class="dr">'+SQSKIP.size+' הצעות נדחו לאחר כך <button onclick="SQSKIP.clear();drawSq()">הצג שוב</button></div>';
    if(lost.length){h+='<h3>התיישנו או לא אותרו</h3><div class="dr">הטקסט השתנה מאז ההצעה, או שהמקום לא נמצא. אינן נכנסות בעיוורון.</div>';
      lost.forEach(([g])=>{h+=sqRow(g,null)})}
    /* הצעות סותרות: כמה הצעות על אותו מקום, זו לצד זו */
    const by={};ok.forEach(([g,s])=>{(by[s.k]=by[s.k]||[]).push([g,s])});
    h+='<h3>'+ok.length+' הצעות ממתינות ב'+esc(D.masechet)+'</h3>';
    if(!ok.length&&!lost.length)h+='<div class="edsum">אין הצעות ממתינות.</div>';
    let n=0;
    for(const k in by){const grp=by[k];
      if(grp.length>1){h+='<div class="dr">הצעות סותרות על אותו מקום:</div><div class="sgconf">'+grp.map(([g,s])=>sqRow(g,s,n++)).join('')+'</div>'}
      else h+=sqRow(grp[0][0],grp[0][1],n++)}
    box.innerHTML=h;sqCurPaint()}
  function sqCurPaint(){const rows=[...document.querySelectorAll('#sgqb .sgrow[data-id]')];
    rows.forEach((r,i)=>r.classList.toggle('cur',i===SQCUR));
    const c=rows[SQCUR];if(c&&c.scrollIntoView)c.scrollIntoView({block:'nearest'})}
  function sqRow(g,s,n){
    const when=new Date(g.t).toLocaleString('he-IL'),id=esc(g.id);
    const st=STYPES[g.type]||STYPES.nusach;
    /* בהצעה על הנוסח: מחוק באדום ומוסף בירוק, בהקשר השורה, כמו עקוב אחר שינויים */
    let ctx='';
    if(s&&g.type==='nusach'&&s.t.indexOf(g.was)>-1){
      const i=s.t.indexOf(g.was);
      ctx='<div class="sqctx">'+esc(s.t.slice(Math.max(0,i-60),i))+'<del style="color:#a83c2f;background:#fbe5e1">'+esc(g.was)+'</del><ins style="color:#2e6b3f;background:#e3f3e6;text-decoration:none">'+esc(g.note)+'</ins>'+esc(s.t.slice(i+g.was.length,i+g.was.length+60))+'</div>';
    }else if(s){ctx='<div class="sqctx">'+esc(s.t).replace(esc(g.was),'<mark>'+esc(g.was)+'</mark>')+'</div>'}
    else ctx='<q>'+esc((g.was||'').slice(0,120))+'</q><small>לא אותר בקובץ הנוכחי</small>';
    const known=g.pid?true:false;
    return '<div class="sgrow'+(g.tr?' trust':'')+(s?'':' edlost')+'" data-id="'+id+'" data-n="'+(n===undefined?-1:n)+'" style="border-right:4px solid '+st[2]+'">'+
      '<small>'+esc(g.daf||'')+(g.name?' · '+esc(g.name):' · בלי שם')+' · '+when+'</small> '+tyChip(g.type)+(g.tr?'<span class="stchip" style="background:#c9a24a">מהימן</span>':'')+
      (g.mnew?'<span class="stchip" style="background:#a83c2f">הודעה חדשה</span>':'')+ctx+
      (g.type==='nusach'?'':'<b>'+esc(g.note)+'</b>')+thrHTML(g,true)+
      (s?'<button onclick="sqDecide(\''+id+'\',\'accepted\')">אשר</button>'+
         (g.type==='nusach'?'<button onclick="sqDecide(\''+id+'\',\'edited\')">ערוך ואשר</button>':'')+
         '<button onclick="sqJump(\''+id+'\')">הצג</button>':'<button onclick="sqDecide(\''+id+'\',\'stale\')">סמן כהתיישנה</button>')+
      '<button onclick="sqDecide(\''+id+'\',\'rejected\')">דחה</button>'+
      '<button onclick="sqSkip(\''+id+'\')">דלג</button><button onclick="sqReply(\''+id+'\')">השב</button>'+
      (known?'<button onclick="sqTrust(\''+esc(g.pid)+'\','+(g.tr?0:1)+')" title="הצעותיו יופיעו ראשונות בתור">'+(g.tr?'בטל מהימנות':'סמן כמהימן')+'</button>':'')+'</div>'}
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
    if(accept&&g.type==='nusach'){
      const s=sqLocate(g,slotsFull());
      if(!s){alert('ההצעה לא אותרה בקובץ הנוכחי ואי אפשר להחיל אותה.');return}
      now=g.note;
      if(st==='edited'){const v=prompt('הנוסח שייכנס במקום הקטע המסומן:',g.note);if(v===null)return;now=v.trim();if(!now)return}
      const old=ED.find(x=>x.k===s.k);
      const curT=old?old.now:s.t, curH=old?(old.nowH!==undefined?old.nowH:esc(old.now)):s.h;
      const wasT=old?old.was:s.t, wasH=old?(old.wasH!==undefined?old.wasH:s.h):s.h;
      if(curT.indexOf(g.was)<0){alert('הקטע שהוצע עליו התיקון כבר אינו בשורה הזאת.');return}
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
    catch(e){if(edit){ED=ED.filter(x=>x!==edit);saveED();if(SQUNDO&&SQUNDO.prev)ED.push(SQUNDO.prev)}alert('ההכרעה לא נרשמה: '+e.message);return}
    if(!accept)jrLog([{id:'sg-'+id,t:Date.now(),slug:SLUG,daf:g.daf,k:g.k,src:'suggest',was:g.was,now:g.note,neg:1,why:reason,ctx:g.ctx}]);   /* הדחייה היא דוגמה שלילית; האישור נרשם בצד השרת מן העריכה עצמה */
    QQ=QQ.filter(x=>x.id!==id);QQTOT=Math.max(0,QQTOT-1);
    if(edit){applyTextNow(edit);drawEd();pubSoon();syncSoon();toast('התיקון הוחל. Ctrl+Z מבטל.')}
    else toast(accept?'ההצעה סומנה כמאושרת. ההחלה ידנית.':st==='stale'?'ההצעה סומנה כהתיישנה.':'ההצעה נדחתה והמציע יראה את הסיבה.');
    sqBadge();drawSq()}
  async function sqUndo(){
    const u=SQUNDO;if(!u){toast('אין מה לבטל.');return}
    SQUNDO=null;
    try{await api('/decide',{method:'POST',body:JSON.stringify({id:u.id,st:'pending'})})}catch(e){alert('הביטול לא נרשם: '+e.message);return}
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
    else if(e.code==='KeyA'){e.preventDefault();sqDecide(id,'accepted')}
    else if(e.code==='KeyD'){e.preventDefault();sqDecide(id,'rejected')}
    else if(e.code==='KeyS'){e.preventDefault();sqSkip(id)}
    else if(e.code==='KeyE'){e.preventDefault();sqDecide(id,'edited')}
    else if(e.code==='KeyR'){e.preventDefault();sqReply(id)}
  },true);
