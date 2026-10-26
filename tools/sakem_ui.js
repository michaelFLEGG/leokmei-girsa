  /* =================== סכם: מהדק ומתקן קטע נבחר (מנהל בלבד, 26.10.2026) ===================
     מסמנים קטע במצב עריכה, ו"סכם" (או Ctrl+Shift+S) מבקש מנקודת הקליטה נוסח מהודק של אותו
     קטע, כבר במבנה הלאוקמי. ההצעה מוצגת במקום הקטע כ"רוח": הישן מחוק באדום עדין, החדש בירוק,
     ותוספת או תיקון תוכן בקו כתום עם תווית. ארבעה כפתורים: קבל / ערוך / קצר עוד / בטל.

     "קבל" אינו מסלול חדש: הוא מרכיב את השינוי מאותן רשומות שהעורך כותב בעצמו (תיקון טקסט,
     סגנון פסקה, פיצול, איחוי, כותרת צד, החזרת כותרת צד לגוף, מחיקת כותרת צד ואיחוי), ושם
     אותן ב-ED. משם הן עוברות בדיוק כמו כל עריכת מנהל: הפרסום המרוכז, הבנייה והקליטה לוורד.
     Ctrl+Z מבטל את כולן בבת אחת.

     הדפדפן שולח לנקודת הקליטה את היחידות שבקטע כפי שהן בנתונים, והשרת בודק שכל שורה בהן
     קיימת באתר או בעריכות המנהל שבשרת (לא טקסט חופשי), שולף בעצמו את פירוש הגמרא, לשון
     הגמרא וביאור חברותא, ופונה למודל. */
  const SKM={sel:null,ghost:null,busy:new Set(),wait:[],stat:null,anchor:null,q:null};
  const SKM_MAXPG=2;
  function skmOK(){return typeof EDIT!=='undefined'&&EDIT&&!SUGM&&isAdmin()&&!!admKey()}
  function skmRowOf(n){const e=n&&(n.nodeType===3?n.parentElement:n);return e&&e.closest?e.closest('#flow .row'):null}
  function skmAllRows(){return [...$('#flow').querySelectorAll('.row')].filter(r=>/^u\d+$/.test(r.id)&&!r.closest('.skmghost'))}
  function skmSpan(a,b){const all=skmAllRows();let i=all.indexOf(a),j=all.indexOf(b);if(i<0||j<0)return null;if(i>j)[i,j]=[j,i];return all.slice(i,j+1)}
  /* היחידות שמאחורי השורות, לפי הסדר */
  function skmUnits(ids){const by=new Map(flatU().map(o=>[o.u.id,o]));return ids.map(id=>by.get(id)).filter(Boolean)}
  function skmTos(daf){const T=window.__TOS;if(!T||!T.items)return [];return T.items.filter(it=>it.daf===daf&&it.t).map(it=>({n:String(it.n),t:it.t}))}
  function skmPU(o){const u=o.u,pg=D.pages[o.pi];
    return {id:u.id,k:u.k,a:u.a||'',w:u.w||'',l:(u.l||[]).map(x=>[x[0],x[1]]),mbw:u.mbw||'',ref:u.ref||'',
            daf:pg.daf||'',first:pg.units[0]===u,tos:(u.k==='u'||u.k==='m')?skmTos(pg.daf):[]}}
  function skmInter(os){return SKC.toInter(os.map(skmPU)).text}

  /* ---- הסימון: מתרחב לשורות שלמות ---- */
  function skmMark(rows){
    document.querySelectorAll('#flow .row.skmsel').forEach(r=>r.classList.remove('skmsel'));
    SKM.sel=null;
    if(!rows||!rows.length){skmBtnHide();return}
    const os=skmUnits(rows.map(r=>+r.id.slice(1)));
    const pis=[...new Set(os.map(o=>o.pi))];
    rows.forEach(r=>r.classList.add('skmsel'));
    SKM.sel={rows,ids:os.map(o=>o.u.id),long:pis.length>SKM_MAXPG};
    skmBtnShow()}
  let SKMT=null;
  document.addEventListener('selectionchange',()=>{clearTimeout(SKMT);SKMT=setTimeout(skmSelChanged,160)});
  function skmSelChanged(){
    if(!skmOK()||SKM.ghost&&SKM.ghost.contains(document.activeElement)){if(!skmOK())skmMark(null);return}
    const s=getSelection();if(!s||!s.rangeCount)return;
    const r=s.getRangeAt(0);
    if(r.collapsed){if(SKM.sel&&!SKM.sel.rows.some(x=>x.contains(r.startContainer)))skmMark(null);return}
    /* סימון שנעשה בגרירה על פני כמה שורות: בחירת הדפדפן נעצרת בשורה הראשונה, והיא אינה דורסת אותו */
    if(SKM.dragged&&SKM.sel&&SKM.sel.rows.some(x=>x.contains(r.startContainer)))return;
    const a=skmRowOf(r.startContainer),b=skmRowOf(r.endContainer);
    if(!a||!b){return}
    SKM.anchor=a;skmMark(skmSpan(a,b))}
  /* גרירה על פני כמה שורות: בחירה בדפדפן נעצרת בגבול הפסקה הנערכת, ולכן הסימון עוקב אחרי
     העכבר עצמו - כל שורה שהעכבר עובר עליה בזמן הגרירה נכנסת (27.10.2026, בקשת המנהל) */
  let SKD=null;
  document.addEventListener('mousedown',e=>{
    if(e.button!==0||e.shiftKey||!skmOK())return;
    const r=skmRowOf(e.target);
    if(!r||r.closest('.skmghost')){SKD=null;return}
    SKD={a:r,last:r};SKM.dragged=false},true);
  document.addEventListener('mousemove',e=>{
    if(!SKD||!(e.buttons&1))return;
    const r=skmRowOf(document.elementFromPoint(e.clientX,e.clientY));
    if(!r||r===SKD.last||r.closest('.skmghost'))return;
    SKD.last=r;
    if(r===SKD.a&&!SKM.dragged)return;
    SKM.dragged=true;SKM.anchor=SKD.a;skmMark(skmSpan(SKD.a,r))},true);
  document.addEventListener('mouseup',()=>{SKD=null},true);
  /* הרחבה בלחיצה עם Shift על שורה אחרת */
  document.addEventListener('mousedown',e=>{
    if(!e.shiftKey||!skmOK()||!SKM.sel||!SKM.anchor)return;
    const r=skmRowOf(e.target);if(!r||r.closest('.skmghost'))return;
    e.preventDefault();skmMark(skmSpan(SKM.anchor,r))},true);
  document.addEventListener('keydown',e=>{
    if(e.ctrlKey&&e.shiftKey&&!e.altKey&&(e.code==='KeyS')){
      if(!skmOK())return;
      e.preventDefault();e.stopPropagation();skmGo();return}
    if(e.key==='Escape'&&SKM.sel&&!SKM.ghost){skmMark(null)}},true);

  /* ---- הכפתור הצף ---- */
  function skmBtnShow(){
    let b=$('#skmbtn');
    if(!b){b=document.createElement('button');b.id='skmbtn';b.type='button';
      b.addEventListener('mousedown',e=>e.preventDefault());
      b.addEventListener('click',()=>skmGo());document.body.appendChild(b)}
    const nokey=SKM.stat&&!SKM.stat.hasKey;
    b.textContent=nokey?'סכם · ממתין למפתח':'סכם';
    b.title=SKM.sel&&SKM.sel.long?'הקטע ארוך מדי, נא לסמן עד דף אחד':'הידוק ותיקון הקטע המסומן (Ctrl+Shift+S). להרחבה: גרירה על כמה שורות, או Shift+לחיצה על שורה אחרת';
    if(SKM.sel&&SKM.sel.rows.length>1)b.textContent+=' · '+SKM.sel.rows.length+' שורות';
    b.classList.toggle('dim',!!(nokey||SKM.sel&&SKM.sel.long));
    const last=SKM.sel.rows[SKM.sel.rows.length-1].getBoundingClientRect();
    const top=Math.min(innerHeight-44,Math.max(8,last.bottom+4));
    b.style.top=top+'px';b.style.left=Math.max(8,last.left+8)+'px';b.style.display='block'}
  function skmBtnHide(){const b=$('#skmbtn');if(b)b.style.display='none'}
  addEventListener('scroll',()=>{if(SKM.sel&&$('#skmbtn')&&$('#skmbtn').style.display==='block')skmBtnShow()},{passive:true,capture:true});
  /* כפתור גם בחלונית הסגנונות הצפה, כשיש בחירה */
  const skmSty0=styHtml;
  styHtml=function(el,sel){const h=skmSty0(el,sel);
    return h&&sel&&skmOK()?h+'<button class="skmsb" onmousedown="event.preventDefault()" onclick="skmGo()" title="הידוק ותיקון הקטע המסומן"><span>סכם</span><kbd>Ctrl+Shift+S</kbd></button>':h};

  /* ---- הבקשה ---- */
  async function skmStat(force){
    if(SKM.stat&&!force)return SKM.stat;
    try{const j=await api('/sakem/stat');SKM.stat=j}catch(e){SKM.stat=SKM.stat||null}
    return SKM.stat}
  window.skmGo=async function(){
    if(!skmOK()){flash('סכם פועל במצב עריכה, למנהל');return}
    if(!SKM.sel){flash('סמן קטע (אפשר להרחיב ב-Shift+לחיצה על שורה אחרת), ואז סכם');return}
    if(SKM.sel.long){flash('הקטע ארוך מדי, נא לסמן עד דף אחד');return}
    const st=await skmStat();
    if(st&&!st.hasKey){skmPanel();flash('ממתין למפתח: הדבק את מפתח הסכם בחלונית');return}
    if(st&&st.capped){flash('הגעת לתקרת החודש, הכפתור יחזור ב-1 לחודש');return}
    const ids=SKM.sel.ids.slice(),rows=SKM.sel.rows.slice();
    const key=ids.join(',');
    if(SKM.busy.has(key)){flash('ההצעה לקטע הזה כבר בדרך');return}
    clearTimeout(CAPT);document.querySelectorAll('#flow [contenteditable="true"]').forEach(el=>{if(el.contains(document.activeElement)||el===document.activeElement)capture(el)});
    const os=skmUnits(ids);
    const fu=flatU(),i0=fu.findIndex(o=>o.u.id===ids[0]),i1=fu.findIndex(o=>o.u.id===ids[ids.length-1]);
    const ctxB=fu.slice(Math.max(0,i0-3),i0),ctxA=fu.slice(i1+1,i1+4);
    const orig=skmInter(os);
    SKM.busy.add(key);rows.forEach(r=>r.classList.add('skmbusy'));skmMark(null);getSelection().removeAllRanges();
    try{
      const j=await api('/sakem',{method:'POST',body:JSON.stringify({slug:SLUG,masechet:D.masechet,
        units:os.map(skmPU),before:ctxB.map(skmPU),after:ctxA.map(skmPU)})});
      skmArrive({id:j.id,ids,orig,text:j.text,changes:j.changes||[],warn:j.warn||[],usd:j.usd||0,round:1});
    }catch(err){
      const m=err.message||'';
      if(/טרם פורסמו|לא נמצאה באתר/.test(m)){
        if(confirm(m+'\n\nלפרסם עכשיו את העריכות הממתינות ולנסות שוב?')){await pubNow(1);setTimeout(()=>{skmMark(rows.filter(r=>r.isConnected));skmGo()},1200)}}
      else if(/מפתח/.test(m)){SKM.stat=null;skmPanel();flash(m)}
      else flash('סכם: '+m)}
    finally{SKM.busy.delete(key);rows.forEach(r=>r.classList.remove('skmbusy'))}}
  function skmArrive(p){
    /* הקטע השתנה בזמן היצירה: ההצעה כבר אינה מתאימה */
    if(skmInter(skmUnits(p.ids))!==p.orig){flash('הקטע השתנה בזמן היצירה. סמן שוב ובקש הצעה חדשה');skmDone(p,'stale');return}
    if(SKM.ghost){SKM.wait.push(p);toast('הצעת סכם נוספת מוכנה, ותוצג אחרי שתסיים את הנוכחית');return}
    skmShow(p)}

  /* ---- הרוח: ההצעה במקום הקטע ---- */
  function skmGhostBody(text){
    const toks=SKC.parse(text);let h='',row=null;
    const flush=()=>{if(!row)return;
      h+='<div class="skmrow"><div class="skmrail">'+row.t.map(t=>'<span class="skmanc">'+SKC.i2h(t,true)+'</span>').join('')+'</div>'+
         '<div class="skmmain">'+row.l.map(l=>l.src?'<p class="skmsrc" contenteditable="false" data-tok="'+esc(l.src).replace(/"/g,'&quot;')+'"></p>':
           '<p data-sty="'+(l.sty||'')+'" class="'+(l.sty||'')+'">'+(SKC.i2h(l.v,true)||'<br>')+'</p>').join('')+'</div></div>';row=null};
    const LAB={'דף':v=>'דף '+v,'משנה':v=>v?'משנה '+v:'משנה','גמרא':()=>'גמרא','קבוע':()=>'(עיטור / פתיחה)','מקור':()=>''};
    toks.forEach(k=>{
      if(k.t==='lock'){
        const raw='['+k.kind+(k.val!==''||k.kind!=='גמרא'&&k.kind!=='משנה'?':'+k.val:'')+']';
        /* הפניה לגמרא אינה מפרידה בין שורות: נשמרת במקומה בתוך השורה, נסתרת */
        if(k.kind==='מקור'&&row){row.l.push({src:raw});return}
        flush();
        if(k.kind==='כותרת-נושא'||k.kind==='כותרת-דה'){
          h+='<div class="skmhead '+(k.kind==='כותרת-נושא'?'nose':'dh')+'" data-kind="'+k.kind+'">'+SKC.i2h(k.val,true)+'</div>';return}
        const lab=(LAB[k.kind]||(()=>''))(k.val);
        h+='<div class="skmlock'+(lab?'':' skmhid')+'" contenteditable="false" data-tok="'+esc(raw).replace(/"/g,'&quot;')+'">'+esc(lab)+'</div>';return}
      if(k.t==='title'){if(row&&row.l.length)flush();if(!row)row={t:[],l:[]};row.t.push(k.v);return}
      if(!row)row={t:[],l:[]};row.l.push(k)});
    flush();return h}
  /* קריאה חזרה מן הרוח אחרי עריכה ישירה */
  function skmReadBack(g){
    const L=[];
    g.querySelectorAll('.skmbody > *').forEach(n=>{
      if(n.classList.contains('skmlock')){L.push(n.dataset.tok);return}
      if(n.classList.contains('skmhead')){L.push('['+n.dataset.kind+':'+SKC.h2i(n.innerHTML).replace(/\s+/g,' ').trim()+']');return}
      if(!n.classList.contains('skmrow'))return;
      n.querySelectorAll('.skmanc').forEach(a=>{const t=SKC.h2i(a.innerHTML).replace(/\s+/g,' ').trim();if(t)L.push('[צד:'+t+']')});
      const m=n.querySelector('.skmmain');
      [...(m?m.children:[])].forEach(p=>{
        if(p.dataset.tok){L.push(p.dataset.tok);return}
        const sty=p.dataset.sty||'';const t=SKC.h2i(p.innerHTML).replace(/\s+/g,' ').trim();
        if(!t)return;
        L.push((sty&&SKC.P2T[sty]?'('+SKC.P2T[sty]+') ':'')+t)})});
    return L.join('\n')}
  function skmShow(p){
    const rows=p.ids.map(id=>document.getElementById('u'+id)).filter(Boolean);
    if(!rows.length){skmDone(p,'gone');return}
    skmClose(true);
    rows.forEach(r=>r.classList.add('skmold'));
    const g=document.createElement('div');g.className='skmghost';g.dir='rtl';
    const blocked=p.warn&&p.warn.length;
    g.innerHTML='<div class="skmbody">'+skmGhostBody(p.text)+'</div>'+
      '<div class="skmbar" contenteditable="false">'+
        '<span class="skmt">הצעת סכם'+(p.round>1?' · קיצור '+p.round:'')+'</span>'+
        (blocked?'<span class="skmwarn" title="'+esc(p.warn.join(' · '))+'">⚠ '+esc(p.warn.join(' · '))+'</span>':'')+
        '<button type="button" data-a="ok"'+(blocked?' hidden':'')+'>קבל</button>'+
        '<button type="button" data-a="edit">ערוך</button>'+
        '<button type="button" data-a="more">קצר עוד</button>'+
        '<button type="button" data-a="no">בטל</button>'+
        (p.changes&&p.changes.length?'<details class="skmwhy"><summary>מה שיניתי</summary><ul>'+p.changes.slice(0,3).map(c=>'<li>'+esc(c)+'</li>').join('')+'</ul></details>':'')+
      '</div>';
    rows[rows.length-1].after(g);
    SKM.ghost=g;SKM.cur=p;
    /* אירועי העורך אינם נוגעים ברוח: הקלדה כאן אינה תיקון בדף */
    ['keydown','keyup','input','focusin','focusout','beforeinput'].forEach(t=>g.addEventListener(t,ev=>{
      if(t==='keydown')skmGhostKey(ev);ev.stopPropagation()}));
    g.querySelector('.skmbar').addEventListener('click',ev=>{const b=ev.target.closest('button');if(!b)return;
      ({ok:skmAccept,edit:skmEdit,more:skmMore,no:skmCancel})[b.dataset.a]()});
    g.scrollIntoView({block:'nearest',behavior:'smooth'})}
  function skmGhostKey(ev){
    if(!SKM.ghost||!SKM.ghost.classList.contains('edit'))return;
    const C={Digit1:'am',Digit2:'ps',Digit4:'hs',Digit6:'dm',Digit7:'ns'};
    if(ev.ctrlKey&&!ev.altKey&&!ev.shiftKey&&(C[ev.code]||ev.code==='KeyB')){
      ev.preventDefault();const s=getSelection();if(!s.rangeCount||s.isCollapsed)return;
      const r=s.getRangeAt(0),i=document.createElement('i');i.className=C[ev.code]||'b';
      try{i.appendChild(r.extractContents());r.insertNode(i)}catch(e){}return}
    if(ev.ctrlKey&&!ev.altKey&&!ev.shiftKey&&ev.code==='Space'){ev.preventDefault();
      const s=getSelection();if(!s.rangeCount)return;let n=s.anchorNode;n=n&&n.nodeType===3?n.parentElement:n;
      const i=n&&n.closest('i');if(i&&SKM.ghost.contains(i))i.replaceWith(...i.childNodes);return}
    if(ev.key==='Escape'){ev.preventDefault();skmCancel()}}
  function skmClose(keep){
    const g=SKM.ghost;if(g)g.remove();SKM.ghost=null;
    document.querySelectorAll('#flow .row.skmold').forEach(r=>r.classList.remove('skmold'));
    if(!keep&&SKM.wait.length){const n=SKM.wait.shift();setTimeout(()=>skmArrive(n),60)}
    else if(!keep&&SKM.q)setTimeout(skmQNext,60)}
  function skmEdit(){
    const g=SKM.ghost;if(!g)return;
    g.classList.add('edit');
    const b=g.querySelector('.skmbody');b.setAttribute('contenteditable','');b.setAttribute('spellcheck','false');
    const ok=g.querySelector('[data-a="ok"]');ok.hidden=false;ok.textContent='קבל את הנוסח הערוך';
    g.querySelector('[data-a="edit"]').hidden=true;
    const p=b.querySelector('p');if(p){p.focus();const r=document.createRange();r.selectNodeContents(p);r.collapse(false);const s=getSelection();s.removeAllRanges();s.addRange(r)}}
  async function skmMore(){
    const p=SKM.cur;if(!p)return;
    const g=SKM.ghost;g.classList.add('skmbusy');
    try{const j=await api('/sakem/more',{method:'POST',body:JSON.stringify({slug:SLUG,id:p.id})});
      skmShow(Object.assign({},p,{id:j.id,text:j.text,changes:j.changes||[],warn:j.warn||[],round:(p.round||1)+1}))}
    catch(err){g.classList.remove('skmbusy');flash('קצר עוד: '+(err.message||''))}}
  function skmCancel(){const p=SKM.cur;skmClose();if(p)skmDone(p,'cancel')}
  function skmDone(p,act,fin){
    api('/sakem/done',{method:'POST',body:JSON.stringify({slug:SLUG,id:p.id,act,final:fin||''})}).catch(()=>{})}
  function skmAccept(){
    const p=SKM.cur,g=SKM.ghost;if(!p||!g)return;
    const edited=g.classList.contains('edit');
    const text=edited?skmReadBack(g):p.text;
    const errs=SKC.guard(p.orig,text,{edited:true}).filter(x=>/נעולים|קטע שלם|נוספו שורות|תג לא מוכר/.test(x));
    if(errs.length){flash('לא הוחל: '+errs[0]);return}
    let r;
    try{r=skmApply(p,text)}catch(err){flash('לא הוחל: '+(err.message||err));return}
    skmClose();
    skmDone(p,edited?'edit':'accept',text);
    flash(r.n?'הוחל: '+r.n+' שינויים, ויפורסמו עם שאר העריכות (Ctrl+Z מבטל)':'אין שינוי להחיל')}

  /* =================== ההחלה: מאותן רשומות שהעורך כותב =================== */
  function skmStyOf(cls){return String(cls||'').split(' ').filter(c=>PCLS.indexOf(c)>-1).join(' ')}
  /* הקטעים שבין האלמנטים הנעולים, מן הנתונים - באותו סדר בדיוק כמו SKC.segments על הביניים */
  function skmOsegs(os){
    const segs=[];let cur={units:[],lock:null};segs.push(cur);let lastK='';
    const close=lk=>{cur.lock=lk;cur={units:[],lock:null};segs.push(cur)};
    os.forEach(o=>{const u=o.u,pg=D.pages[o.pi];
      if(pg.units[0]===u&&pg.daf)close({kind:'דף'});
      if(u.k==='m')close({kind:'משנה'});
      else if(u.k==='u'&&lastK==='m')close({kind:'גמרא'});
      if(u.k==='u'||u.k==='m')cur.units.push(o);
      else if(u.k==='nose'||u.k==='dh')close({kind:'head',o});
      else close({kind:'קבוע'});
      if(u.k==='u'||u.k==='m')lastK=u.k});
    return segs}
  /* חלוקת רשימה ארוכה A לקבוצות רצופות, אחת לכל פריט ב-B, כך שסכום הדמיון (מילים משותפות) מרבי */
  function skmPart(A,B){
    const W=t=>new Set(String(t).replace(/[֑-ׇ"'.,:;!?\-]/g,' ').split(/\s+/).filter(x=>x.length>1));
    const BW=B.map(W),n=A.length,m=B.length,AW=A.map(W);
    const sim=(i,j,k)=>{const s=new Set();for(let x=i;x<j;x++)AW[x].forEach(w=>s.add(w));let c=0;BW[k].forEach(w=>{if(s.has(w))c++});return c};
    const F=[...Array(n+1)].map(()=>new Array(m+1).fill(-1e9)),P=[...Array(n+1)].map(()=>new Array(m+1).fill(0));
    F[0][0]=0;
    for(let j=1;j<=m;j++)for(let i=j;i<=n-(m-j);i++)for(let h=j-1;h<i;h++){
      if(F[h][j-1]<=-1e9)continue;const v=F[h][j-1]+sim(h,i,j-1);if(v>F[i][j]){F[i][j]=v;P[i][j]=h}}
    const sz=[];let i=n;for(let j=m;j>=1;j--){const h=P[i][j];sz.unshift(i-h);i=h}
    return sz}
  function skmApply(p,newText){
    const os=skmUnits(p.ids);
    if(os.length!==p.ids.length||skmInter(os)!==p.orig)throw new Error('הקטע השתנה מאז ההצעה. בקש הצעה חדשה');
    const NS=SKC.segments(SKC.parse(newText)),OS=skmOsegs(os);
    if(NS.length!==OS.length)throw new Error('מבנה הקטע אינו תואם (האלמנטים הנעולים)');
    const pis=[...new Set(os.map(o=>o.pi))];
    const pre=pis.map(pi=>({pi,snap:JSON.stringify(D.pages[pi].units)})),befores=pis.map(snapOf);
    const RECS=[],OLDS=[];let T0=Date.now();
    const nt=()=>(T0=Math.max(T0+1,Date.now()));
    const add=e=>{e.t=nt();e.pub=0;e._ap=1;ED.push(e);RECS.push(e);return e};
    const pgDaf=pi=>D.pages[pi].daf||'';
    const unitAt=line=>{for(const o of unitsAll()){const i=o.u.l.indexOf(line);if(i>-1)return {u:o.u,pi:o.pi,i}}return null};
    /* תיקון טקסט ו/או סגנון פסקה במקום אחד - כמו capture: רשומה אחת לכל מקום */
    function setText(k,nowH,wantP,daf,force){
      const cur=dataHtml(k);if(cur===null)throw new Error('מקום לא נמצא: '+k);
      const m=/^u(\d+)\.(\d+)$/.exec(k);let curCls='';
      if(m){const o=flatU().find(x=>x.u.id===+m[1]);curCls=o&&o.u.l[+m[2]-1]?o.u.l[+m[2]-1][0]:''}
      const curP=skmStyOf(curCls);
      /* force: אחרי איחוי בוורד הסגנון הוא של הפסקה האחרונה, ובאתר של הראשונה - נרשם במפורש */
      const psCh=wantP!==undefined&&(wantP!==curP||!!force);
      const cn=h=>SKC.h2i(h).replace(/\s+/g,' ').trim();
      if(cn(cur)===cn(nowH)&&!psCh)return 0;
      const now=plain(nowH);
      const old=ED.find(x=>x.op!=='struct'&&x.k===k);
      if(old){OLDS.push([old,JSON.stringify(old)]);
        old.now=now;old.nowH=nowH;old.t=nt();old.pub=0;old._ap=1;old._cur=now;
        if(old.wasP===undefined)old.wasP=curP;
        if(psCh||old.ps!==undefined){const w=psCh?wantP:old.ps;if(w!==old.wasP){old.ps=w;old.psw=wsty(w)}else{delete old.ps;delete old.psw}}}
      else{const e={k,was:plain(cur),now,wasH:cur,nowH,wasP:curP,daf,ctx:'',_cur:now};
        if(psCh){e.ps=wantP;e.psw=wsty(wantP)}
        add(e)}
      dataSet(k,nowH);if(psCh)dataCls(k,wantP);SLOTS=null;return 1}
    function unside(o){
      const u=o.u,k=wkey(u),lines=String(u[k]||'').split('<br>');
      const winH=lines[lines.length-1],winT=plain(winH);
      if(!winT.trim()){u[k]=lines.slice(0,-1).join('<br>');return null}
      const nextT=u.l.length?plain(u.l[0][1]):'',cls=u.l.length?u.l[0][0]:'b0 a0';
      freezeEdits([winT,nextT]);
      const e=add({op:'struct',kind:'unside',texts:[winT,nextT],res:[[cls,winH]],resT:[winT],daf:pgDaf(o.pi)});
      unsideApply(e,{u,pi:o.pi,daf:pgDaf(o.pi)});SLOTS=null;return u.l[0]}
    function fuse(pv,cu){
      const pl=usmPlan(pv,cu);if(pl.err||!pl.fuse)throw new Error(pl.err||'לא ניתן לאחד כאן שתי יחידות');
      const P=pv.u,U=cu.u,ph=P.l[P.l.length-1],nh=U.l[0];
      const texts=[plain(ph[1]),plain(nh[1])];
      const h=ph[1]+(/\s$/.test(texts[0])||/^\s/.test(texts[1])||!texts[0].trim()?'':' ')+nh[1];
      freezeEdits(texts);
      const e=add({op:'struct',kind:'unside-merge',texts,res:[[ph[0],h],[],[pl.where]],resT:[plain(h)],daf:pgDaf(cu.pi)});
      usmData(e,pv,cu);SLOTS=null}
    function merge(U,i,daf){
      const a=U.l[i],b=U.l[i+1],texts=[plain(a[1]),plain(b[1])];
      freezeEdits(texts);
      const h=a[1]+b[1];
      add({op:'struct',kind:'merge',texts,res:[[a[0],h]],resT:[plain(h)],daf});
      U.l.splice(i,2,[a[0],h]);delete U.lv;SLOTS=null}
    function split(U,i,h1,h2,daf){
      const cls=U.l[i][0],was=plain(U.l[i][1]);
      freezeEdits([was]);
      add({op:'struct',kind:'split',texts:[was],res:[[cls,h1],[cls,h2]],resT:[plain(h1),plain(h2)],daf});
      U.l.splice(i,1,[cls,h1],[cls,h2]);delete U.lv;SLOTS=null}
    /* פיצול שורה לכמה חלקים בגבולות מילה, ביחס לאורך שורות היעד; הנוסח עצמו אינו משתנה */
    function splitN(U,i,targets,daf){
      const was=plain(U.l[i][1]),L=was.length,tot=targets.reduce((n,t)=>n+t.length,0)||1;
      const cuts=[];let acc=0;
      for(let q=0;q<targets.length-1;q++){acc+=targets[q].length;
        let c=Math.round(L*acc/tot),best=-1;
        for(let d=0;d<L;d++){for(const x of [c-d,c+d])if(x>0&&x<L&&was[x]===' '&&(!cuts.length||x>cuts[cuts.length-1]+1)){best=x;break}if(best>-1)break}
        if(best<0)throw new Error('לא ניתן לפצל שורה קצרה לכמה שורות');
        cuts.push(best)}
      let prev=0;
      cuts.forEach((c,q)=>{const el=document.createElement('div');el.innerHTML=U.l[i+q][1];
        const off=c-prev,pa=posAt(el,off),pb=posAt(el,off+1);
        const h1=pieceHTML(el,null,pa),h2=pieceHTML(el,pb,null);
        split(U,i+q,h1,h2,daf);prev=c+1})}
    function side(U,pi,i,titleH,daf){
      const L=U.l[i],was=plain(L[1]);
      freezeEdits([was]);
      const e=add({op:'struct',kind:'side',texts:[was],res:[[L[0],L[1]],[titleH],[0,0]],resT:[was,plain(titleH)],daf});
      sideApply(e,{u:U,i,pi});SLOTS=null;
      return i===0?U:D.pages[pi].units.find(x=>x.id===e.t)}
    const titlesOf=o=>String(o.u[wkey(o.u)]||'').split(/<br\s*\/?>/i).map(x=>SKC.h2i(x).trim()).filter(Boolean);
    try{
      OS.forEach((O,si)=>{
        const N=NS[si];
        /* כותרת שהיא שורה משלה (נושא / ד"ה משנה): מקומה נעול, נוסחה פתוח */
        if(O.lock&&O.lock.kind==='head'&&N.lock){const ho=O.lock.o;
          if(SKC.h2i(ho.u.a||'').replace(/\s+/g,' ').trim()!==N.lock.val)setText('u'+ho.u.id+'.0',SKC.i2h(N.lock.val),undefined,pgDaf(ho.pi))}
        if(!O.units.length)return;
        const daf=pgDaf(O.units[0].pi);
        const tEq=(a,b)=>a.join('|')===b.join('|');
        /* כותרת צד שנשארה כמות שהיא מפרידה בין קבוצות: היא אינה נמחקת ונכתבת מחדש (פחות שינויים בוורד).
           ההתאמה: תת-הרצף המשותף הארוך ביותר של כותרות היחידות שאחרי הראשונה */
        const OT=O.units.map(titlesOf),VT=N.units.map(v=>v.titles);
        const A=OT.map(t=>t.join('|')),B=VT.map(t=>t.join('|'));
        const L=[...Array(A.length+1)].map(()=>new Array(B.length+1).fill(0));
        for(let i=A.length-1;i>=1;i--)for(let j=B.length-1;j>=1;j--)
          L[i][j]=A[i]&&A[i]===B[j]?L[i+1][j+1]+1:Math.max(L[i+1][j],L[i][j+1]);
        const cuts=[[0,0]];
        for(let i=1,j=1;i<A.length&&j<B.length;){
          if(A[i]&&A[i]===B[j]){cuts.push([i,j]);i++;j++}else if(L[i+1][j]>=L[i][j+1])i++;else j++}
        const groups=cuts.map((c,n)=>{const nx=cuts[n+1]||[A.length,B.length];
          return {O:O.units.slice(c[0],nx[0]),N:N.units.slice(c[1],nx[1])}});
        groups.forEach(g=>group(g.O,g.N,daf));
      });
      /* קבוצה: יחידות מקור שהראשונה בהן פותחת אותה, מול יחידות ההצעה המקבילות */
      function group(Ou,Nu,daf){
        const tEq=(a,b)=>a.join('|')===b.join('|');
        const nl=Nu.map(v=>v.lines.length),ol=Ou.map(o=>o.u.l.length);
        const ot=Ou.map(titlesOf),vt=Nu.map(v=>v.titles);
        const fast=Ou.length===Nu.length&&nl.every((n,j)=>n===ol[j])&&
          ot.every((t,j)=>tEq(t,vt[j])||(t.length===1&&vt[j].length===1));
        if(fast){
          Ou.forEach((o,j)=>{const v=Nu[j],u=o.u;
            if(!tEq(ot[j],vt[j]))setText('u'+u.id+(u.k==='u'?'.0':'.w'),SKC.i2h(vt[j][0]),undefined,daf);
            v.lines.forEach((l,n)=>setText('u'+u.id+'.'+(n+1),SKC.i2h(l.v).trim(),l.sty||'',daf))});
          return}
        /* המסלול הכללי: הכותרת הראשונה, ואחריה הכול לשורה אחת, נוסח אחד, ופיצול לשורות ולכותרות */
        const o1=Ou[0];let lead=null;
        if(ot[0].length&&!tEq(ot[0],vt[0])&&ot[0].length===1&&vt[0].length===1){
          setText('u'+o1.u.id+(o1.u.k==='u'?'.0':'.w'),SKC.i2h(vt[0][0]),undefined,daf);ot[0]=vt[0].slice()}
        let addFirst=[];
        if(!tEq(ot[0],vt[0])){
          while(titlesOf(o1).length){const ln=unside(o1);if(ln)lead=ln}
          addFirst=vt[0].slice()}
        for(let j=Ou.length-1;j>=1;j--){const o=Ou[j];
          if(titlesOf(o).length){while(titlesOf(o).length)unside(o)}
          else{const fu=flatU(),n=fu.findIndex(x=>x.u===o.u);fuse(fu[n-1],fu[n])}}
        /* השורות של הקבוצה רצופות עכשיו ביחידה אחת, עד סופה */
        const firstLine=lead||(o1.u.l[0]);
        let at=unitAt(firstLine);if(!at)throw new Error('השורות לא נמצאו אחרי האיחוד');
        const U=at.u,s=at.i;
        const total=U.l.length-s;
        const flat=Nu.map(v=>v.lines.map(l=>SKC.i2h(l.v).trim())).flat();
        if(!flat.length)throw new Error('אין שורות בקטע');
        const stys=Nu.map(v=>v.lines.map(l=>l.sty||'')).flat();
        if(total===flat.length){
          /* אותו מספר שורות: כל שורה מתוקנת במקומה, בלי איחוד ופיצול */
          flat.forEach((h,n)=>setText('u'+U.id+'.'+(s+n+1),h,stys[n],daf))}
        else{
          /* שורות זהות בראש ובסוף אינן נוגעות; האיחוד והפיצול רק באמצע */
          const key=(h,c)=>SKC.h2i(h).replace(/\s+/g,' ').trim()+'¦'+c;
          const cur=U.l.slice(s,s+total).map(l=>key(l[1],skmStyOf(l[0]))),want=flat.map((h,n)=>key(h,stys[n]));
          let pre=0;while(pre<cur.length&&pre<want.length&&cur[pre]===want[pre])pre++;
          let suf=0;while(suf<cur.length-pre&&suf<want.length-pre&&cur[cur.length-1-suf]===want[want.length-1-suf])suf++;
          if(want.length-pre-suf<1){if(suf)suf--;else pre--}
          const s2=s+pre,tot2=total-pre-suf,fl2=flat.slice(pre,flat.length-suf),st2=stys.slice(pre,stys.length-suf);
          const oldT=U.l.slice(s2,s2+tot2).map(l=>plain(l[1])),newT=fl2.map(h=>plain(h));
          if(tot2===fl2.length)fl2.forEach((h,n)=>setText('u'+U.id+'.'+(s2+n+1),h,st2[n],daf));
          else if(tot2>fl2.length){
            /* יותר שורות ישנות: כל שורה חדשה מקבלת קבוצת שורות ישנות רצופה (לפי דמיון), שמאוחות
               קודם (על הנוסח המקורי) ורק אחר כך מתוקנות. לעולם לא פיצול של שורה שאוחתה. */
            const G=skmPart(oldT,newT);let idx=s2+tot2;
            for(let j=fl2.length-1;j>=0;j--){const k=G[j];idx-=k;
              for(let t=1;t<k;t++)merge(U,idx,daf);
              setText('u'+U.id+'.'+(idx+1),fl2[j],st2[j],daf,k>1)}}
          else{
            /* יותר שורות חדשות: כל שורה ישנה מקבלת קבוצת שורות חדשות; היא מפוצלת קודם (על
               הנוסח המקורי, בגבול מילה), וכל חלק מתוקן בנפרד */
            const G=skmPart(newT,oldT);const st=[];let acc=0;G.forEach(k=>{st.push(acc);acc+=k});
            for(let i=tot2-1;i>=0;i--){const k=G[i],idx=s2+i,tg=fl2.slice(st[i],st[i]+k),ts=st2.slice(st[i],st[i]+k);
              if(k>1)splitN(U,idx,tg.map(h=>plain(h)),daf);
              tg.forEach((h,q)=>setText('u'+U.id+'.'+(idx+q+1),h,ts[q],daf))}}}
        /* כותרות הצד: מלמטה למעלה, כדי שהמקומות שמעל לא יזוזו */
        const starts=[];let acc=0;Nu.forEach(v=>{starts.push(acc);acc+=v.lines.length});
        const pi=at.pi;
        for(let j=Nu.length-1;j>=1;j--){const v=Nu[j];if(!v.titles.length)continue;
          let host=side(U,pi,s+starts[j],SKC.i2h(v.titles[0]),daf);
          for(let q=1;q<v.titles.length;q++)host=side(host,pi,0,SKC.i2h(v.titles[q]),daf)}
        if(addFirst.length){let host=U,i=s;
          for(const t of addFirst){host=side(host,pi,i,SKC.i2h(t),daf);i=0}}
      }
    }catch(err){
      pre.forEach(z=>{D.pages[z.pi].units=JSON.parse(z.snap)});
      RECS.forEach(e=>{const i=ED.indexOf(e);if(i>-1)ED.splice(i,1)});
      OLDS.reverse().forEach(([o,j])=>{Object.keys(o).forEach(k=>delete o[k]);Object.assign(o,JSON.parse(j))});
      SLOTS=null;befores.forEach(b=>patchPage(b));
      throw err}
    const n=RECS.length+OLDS.length;
    if(!n)return {n:0};
    UNDO.length=0;
    UNDO.push({e:null,snaps:pre,key:'u'+os[0].u.id+'.1',t:Date.now()+1,fn:()=>{
      edKeys();RECS.forEach(e=>{const i=ED.indexOf(e);if(i>-1){tomb(e.k);ED.splice(i,1)}});
      OLDS.slice().reverse().forEach(([o,j])=>{Object.keys(o).forEach(k=>delete o[k]);Object.assign(o,JSON.parse(j))})}});
    SLOTS=null;saveED();
    befores.forEach(b=>patchPage(b));
    const first=skmUnits(p.ids).find(o=>o.u.l&&o.u.l.length)||flatU().find(o=>o.u.l&&o.u.l.length&&pis.indexOf(o.pi)>-1);
    if(first)placeCaret('u'+first.u.id+'.1',0);
    drawEd();pubSoon();syncSoon();
    if($('#edn'))$('#edn').textContent=ED.length;
    return {n,recs:RECS}}

  /* =================== חלונית הניהול: מפתח, עלויות, למידה ותור הסולמיות =================== */
  function skmPanelBtn(){const box=$('#edb');if(!box||SUGM||!isAdmin())return;
    const row=box.querySelector('div[style*="flex-wrap"]');if(!row||row.querySelector('.skmpb'))return;
    const b=document.createElement('button');b.className='skmpb';b.textContent='סכם: מפתח, עלויות ותור';b.onclick=()=>skmPanel();row.appendChild(b)}
  const skmDraw0=drawEd;
  drawEd=function(){skmDraw0();skmPanelBtn()};
  window.skmPanel=async function(){
    const old=$('#skmpanel');if(old)old.remove();
    const m=document.createElement('div');m.className='modal';m.id='skmpanel';
    m.innerHTML='<div class="box skmbox"><h3>סכם</h3><div class="skmst">טוען…</div><div class="btns"><button onclick="document.getElementById(\'skmpanel\').remove()">סגירה</button></div></div>';
    document.body.appendChild(m);m.addEventListener('click',e=>{if(e.target===m)m.remove()});
    const st=await skmStat(true);const box=m.querySelector('.skmst');
    if(!st){box.textContent='אין חיבור לנקודת הקליטה.';return}
    const usd=x=>'$'+(+x||0).toFixed(x<1?3:2);
    let h='<p><b>מפתח:</b> '+(st.hasKey?'מוגדר ✓ (אינו מוצג)':'<span class="skmwarn">ממתין למפתח</span>')+'</p>';
    h+='<p><label>הדבק מפתח סכם: <input id="skmkey" type="password" autocomplete="off" spellcheck="false" placeholder="sk-ant-..." style="width:60%"></label> <button id="skmkeyb">שמור</button></p>'+
       '<p class="skmsmall">המפתח נכתב פעם אחת בשרת (מוצפן), אינו נשמר בדפדפן ואינו מוצג שוב. מפתח מן הסביבה "לאוקמי - סכם" בקונסול.</p>';
    h+='<p><b>עלות:</b> היום '+usd(st.day)+' · החודש '+usd(st.month)+' מתוך תקרה של '+usd(st.cap)+(st.capped?' · <span class="skmwarn">הגעת לתקרת החודש</span>':'')+
       ' · '+(st.n||0)+' הצעות החודש'+(st.n?' · ממוצע '+usd(st.month/st.n)+' להצעה':'')+'</p>';
    h+='<p><b>למידה:</b> '+(st.pairs||0)+' זוגות (הצעה מול הנוסח שהתקבל אחרי עריכה) · '+(st.rejects||0)+' דחיות</p>';
    if(st.suggest&&st.suggest.length)h+='<p><button id="skmex">עדכן את דוגמאות הסכם ('+st.suggest.length+' זוגות חדשים)</button></p>';
    h+='<hr><p><b>תור הסולמיות (#):</b> <button id="skmhq">הכן הצעות לכל ה-# במסכת</button>'+
       (st.queue?' <button id="skmhqo">פתח את התור ('+st.queue+')</button>':'')+'</p><div id="skmhqs" class="skmsmall"></div>';
    box.innerHTML=h;
    $('#skmkeyb').onclick=async()=>{const v=$('#skmkey').value.trim();if(!v)return;
      try{await api('/sakem/key',{method:'POST',body:JSON.stringify({key:v})});$('#skmkey').value='';SKM.stat=null;flash('המפתח נשמר בשרת');skmPanel()}
      catch(e){flash('לא נשמר: '+e.message)}};
    if($('#skmex'))$('#skmex').onclick=async()=>{try{const j=await api('/sakem/examples',{method:'POST',body:JSON.stringify({act:'apply'})});flash('הדוגמאות עודכנו ('+j.n+')');skmPanel()}catch(e){flash(e.message)}};
    $('#skmhq').onclick=()=>skmHashPrep(st);
    if($('#skmhqo'))$('#skmhqo').onclick=()=>{m.remove();skmQOpen()}};

  /* ---- תור הסולמיות: הכנת הצעות לכל שורה עם # (לא רץ מאליו) ---- */
  function skmHashRows(){const out=[];
    flatU().forEach(o=>{const u=o.u;if(u.k!=='u'&&u.k!=='m')return;
      if((u.l||[]).some(l=>plain(l[1]).indexOf('#')>-1)||plain(u.a||u.w||'').indexOf('#')>-1)out.push(o)});
    return out}
  async function skmHashPrep(st){
    const rows=skmHashRows(),box=$('#skmhqs');
    if(!rows.length){box.textContent='אין במסכת שורות עם #.';return}
    const per=st.n?st.month/st.n:0.03,est=per*rows.length,left=Math.max(0,st.cap-st.month);
    const can=per>0?Math.min(rows.length,Math.floor(left/per)):rows.length;
    box.innerHTML=rows.length+' יחידות עם # · הערכה: $'+est.toFixed(2)+' ($'+per.toFixed(3)+' להצעה) · נותר בתקרה $'+left.toFixed(2)+
      (can<rows.length?' · ייכנסו '+can+' בלבד':'')+' <button id="skmhqgo">התחל</button>';
    $('#skmhqgo').onclick=async()=>{
      let done=0,fail=0;
      for(const o of rows.slice(0,can)){
        const fu=flatU(),i=fu.findIndex(x=>x.u===o.u);
        try{await api('/sakem',{method:'POST',body:JSON.stringify({slug:SLUG,masechet:D.masechet,queue:1,
          units:[skmPU(o)],before:fu.slice(Math.max(0,i-3),i).map(skmPU),after:fu.slice(i+1,i+4).map(skmPU)})});done++}
        catch(e){fail++;if(/תקרת/.test(e.message||'')){box.textContent='נעצר: '+e.message;break}}
        box.textContent='הוכנו '+done+' מתוך '+can+(fail?' · '+fail+' נכשלו':'')}
      SKM.stat=null}}
  async function skmQOpen(){
    try{const j=await api('/sakem/queue?slug='+encodeURIComponent(SLUG));SKM.q=(j.items||[]).filter(x=>!x.d);
      if(!SKM.q.length){flash('התור ריק');SKM.q=null;return}
      skmQNext()}catch(e){flash(e.message)}}
  function skmQNext(){
    if(!SKM.q||!SKM.q.length){if(SKM.q)flash('התור הסתיים');SKM.q=null;return}
    const it=SKM.q.shift();
    const os=skmUnits(it.ids);
    if(os.length!==it.ids.length||skmInter(os)!==it.orig){skmDone(it,'stale');return skmQNext()}
    const r=document.getElementById('u'+it.ids[0]);if(r)r.scrollIntoView({block:'center'});
    skmShow({id:it.id,ids:it.ids,orig:it.orig,text:it.text,changes:it.changes||[],warn:it.warn||[],round:1})}

  /* ---- מראה ---- */
  (function(){const s=document.createElement('style');s.textContent=
    '#flow .row.skmsel{background:rgba(70,120,190,.07);box-shadow:inset 3px 0 0 rgba(70,120,190,.45)}'+
    '#flow .row.skmbusy{position:relative;opacity:.75}#flow .row.skmbusy::after{content:"";position:absolute;inset:0;pointer-events:none;'+
      'background:linear-gradient(90deg,transparent,rgba(70,120,190,.10),transparent);background-size:200% 100%;animation:skmsh 1.4s linear infinite}'+
    '@keyframes skmsh{from{background-position:200% 0}to{background-position:-200% 0}}'+
    '#flow .row.skmold{background:rgba(190,60,50,.05)}#flow .row.skmold .main,#flow .row.skmold .anchor{text-decoration:line-through;text-decoration-color:rgba(190,60,50,.55);color:#8a5a55}'+
    '#skmbtn{position:fixed;z-index:60;display:none;padding:5px 14px;border-radius:16px;border:1px solid #2e5b8a;background:#2e5b8a;color:#fff;font:600 14px inherit;cursor:pointer;box-shadow:0 2px 8px rgba(0,0,0,.18)}'+
    '#skmbtn.dim{background:#8a98a8;border-color:#8a98a8}'+
    '.skmghost{margin:4px 0 10px;border:1px solid rgba(46,125,60,.35);background:rgba(46,125,60,.05);border-radius:6px;padding:6px 8px 4px}'+
    '.skmghost.skmbusy{opacity:.6}.skmghost.edit{background:#fff;border-color:#2e7d3c;box-shadow:0 0 0 2px rgba(46,125,60,.15)}'+
    '.skmrow{display:flex;gap:10px;margin:2px 0}.skmrail{flex:0 0 auto;min-width:3.4em;max-width:8em;text-align:left;font-size:.82em;color:#2e5d3a;font-weight:700;display:flex;flex-direction:column}'+
    '.skmmain{flex:1}.skmmain p{margin:0 0 2px;color:#1f4d2a}.skmmain p.in{padding-right:1.2em}.skmmain p.sp{margin-top:.6em}.skmmain p.nose,.skmhead{text-align:center;font-weight:700}'+
    '.skmhead{margin:4px 0;color:#1f4d2a}.skmlock{font-size:12px;color:#7a6a45;background:#f4ecd8;border-radius:4px;display:inline-block;padding:0 6px;margin:2px 0}.skmlock.skmhid,.skmsrc{display:none}'+
    '.skmghost i.am{font-weight:700}.skmghost i.hs{color:#5a6b78;font-size:.92em}.skmghost i.ps{font-style:italic}.skmghost i.b{font-weight:700}'+
    '.skmghost ins.skmadd,.skmghost ins.skmfix{text-decoration:underline;text-decoration-color:#e08a2c;text-decoration-thickness:2px;text-underline-offset:3px;background:rgba(224,138,44,.08)}'+
    '.skmghost ins.skmadd::after,.skmghost ins.skmfix::after{content:"תוספת";font-size:10px;color:#b86b17;vertical-align:super;margin-right:2px}.skmghost ins.skmfix::after{content:"תיקון"}'+
    '.skmghost.edit ins::after{display:none}'+
    '.skmbar{display:flex;flex-wrap:wrap;align-items:center;gap:6px;margin-top:6px;padding-top:5px;border-top:1px dashed rgba(46,125,60,.3);font-size:14px}'+
    '.skmbar .skmt{font-weight:700;color:#2e5d3a;margin-left:6px}.skmbar button{padding:3px 12px;border-radius:12px;border:1px solid #2e7d3c;background:#fff;color:#2e5d3a;cursor:pointer}'+
    '.skmbar button[data-a="ok"]{background:#2e7d3c;color:#fff}.skmwarn{color:#a8452f;font-size:13px}.skmwhy{flex-basis:100%;font-size:13px;color:#4d5a4f}.skmwhy summary{cursor:pointer}.skmwhy ul{margin:3px 18px 0;padding:0}'+
    '.skmsb{border-color:#2e5b8a!important;color:#2e5b8a!important}.skmbox{max-width:640px}.skmsmall{font-size:12.5px;color:#6b604d}'+
    '@media print{.skmghost,#skmbtn{display:none!important}}';
    document.head.appendChild(s)})();
  if(isAdmin()&&admKey())setTimeout(()=>skmStat(),4000);
