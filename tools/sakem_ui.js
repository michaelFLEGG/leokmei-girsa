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
  /* מזהה שחוזר פעמיים (יחידה שהוכפלה בנתונים, ברכות לו:, 4.11.2026): כל הופעה של המזהה ברשימה
     מקבלת את היחידה הבאה בתור שנושאת אותו, ולא שתיהן את אותה יחידה - אחרת האיחוד נופל */
  function skmUnits(ids){const by=new Map();flatU().forEach(o=>{const a=by.get(o.u.id);if(a)a.push(o);else by.set(o.u.id,[o])});
    const used=new Map();return ids.map(id=>{const a=by.get(id);if(!a)return null;const n=used.get(id)||0;used.set(id,n+1);return a[Math.min(n,a.length-1)]}).filter(Boolean)}
  /* הנוסח שההצעה נבנתה עליו עדיין בדף? הצעה שנבנתה לפני תיקון המזהה הכפול ראתה את אותה
     יחידה פעמיים - משווים גם כך, כדי שלא תיראה כ"השתנה" */
  function skmSame(ids,orig){
    const os=skmUnits(ids);if(os.length!==ids.length)return false;
    if(skmInter(os)===orig)return true;
    if(new Set(ids).size===ids.length)return false;
    const by=new Map(flatU().map(o=>[o.u.id,o]));return skmInter(ids.map(id=>by.get(id)).filter(Boolean))===orig}
  function skmTos(daf){const T=window.__TOS;if(!T||!T.items)return [];return T.items.filter(it=>it.daf===daf&&it.t).map(it=>({n:String(it.n),t:it.t}))}
  function skmPU(o){const u=o.u,pg=D.pages[o.pi];
    return {id:u.id,k:u.k,a:u.a||'',w:u.w||'',l:(u.l||[]).map(x=>[x[0],x[1]]),mbw:u.mbw||'',ref:u.ref||'',
            daf:pg.daf||'',first:pg.units[0]===u,tos:(u.k==='u'||u.k==='m')?skmTos(pg.daf):[]}}
  function skmInter(os){return SKC.toInter(os.map(skmPU)).text}

  /* ---- הסימון: מתרחב לשורות שלמות ---- */
  /* show: האם הסימון מצדיק את "סכם" (פרומפט 24, 8.11.2026): שורה שלמה ומעלה, גרירה על כמה שורות
     או Shift+לחיצה. סימון מילה לשם סגנון אינו מקפיץ את סכם, אבל Ctrl+Shift+S פועל גם עליו. */
  function skmMark(rows,show){
    document.querySelectorAll('#flow .row.skmsel').forEach(r=>r.classList.remove('skmsel'));
    SKM.sel=null;
    if(!rows||!rows.length){skmBtnHide();return}
    const os=skmUnits(rows.map(r=>+r.id.slice(1)));
    const pis=[...new Set(os.map(o=>o.pi))];
    SKM.sel={rows,ids:os.map(o=>o.u.id),long:pis.length>SKM_MAXPG,show:show!==false};
    if(!SKM.sel.show){skmBtnHide();return}
    rows.forEach(r=>r.classList.add('skmsel'));
    skmBtnShow()}
  /* הבחירה מכסה פסקה שלמה (מארח עריכה שלם), או חוצה פסקאות */
  function skmWhole(r){
    const h=n=>{const e=n&&(n.nodeType===3?n.parentElement:n);return e&&e.closest?e.closest('[contenteditable="true"]'):null};
    const ha=h(r.startContainer),hb=h(r.endContainer);
    if(!ha||ha!==hb)return true;
    const all=(ha.textContent||'').replace(/\s+/g,''),got=r.toString().replace(/\s+/g,'');
    return !!all.length&&got.length>=all.length-1}
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
    SKM.anchor=a;skmMark(skmSpan(a,b),a!==b||skmWhole(r))}
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
    SKM.dragged=true;SKM.anchor=SKD.a;skmMark(skmSpan(SKD.a,r),true)},true);
  document.addEventListener('mouseup',()=>{SKD=null},true);
  /* הרחבה בלחיצה עם Shift על שורה אחרת */
  document.addEventListener('mousedown',e=>{
    if(!e.shiftKey||!skmOK()||!SKM.sel||!SKM.anchor)return;
    const r=skmRowOf(e.target);if(!r||r.closest('.skmghost'))return;
    e.preventDefault();skmMark(skmSpan(SKM.anchor,r),true)},true);
  document.addEventListener('keydown',e=>{
    if(e.ctrlKey&&e.shiftKey&&!e.altKey&&(e.code==='KeyS')){
      if(!skmOK())return;
      e.preventDefault();e.stopPropagation();
      if(!SKM.sel){const s=getSelection(),r=s&&s.rangeCount?s.getRangeAt(0):null,a=r&&skmRowOf(r.startContainer),b=r&&skmRowOf(r.endContainer);
        if(a&&b){SKM.anchor=a;skmMark(skmSpan(a,b),false)}}
      skmGo();return}
    if(e.key==='Escape'&&SKM.sel&&!SKM.ghost){skmMark(null)}
    /* ההצעה פתוחה והמיקוד אינו בתוכה ואינו בשדה כתיבה: Enter ו-Esc חלים עליה */
    if(SKM.ghost&&!SKM.ghost.classList.contains('edit')&&!SKM.ghost.contains(e.target)&&!e.ctrlKey&&!e.altKey&&!e.shiftKey&&
       (e.key==='Escape'||e.key==='Enter'&&!(e.target.closest&&e.target.closest('[contenteditable="true"],[contenteditable=""],input,textarea,select,button')))){
      e.preventDefault();e.stopPropagation();skmQuick(e.key)}},true);

  /* ---- הכפתור: בשוליים או בסרגל, לעולם לא על הטקסט (פרומפט 24, 8.11.2026) ----
     במחשב, כשיש שוליים משמאל לטור: "סכם" וגלגל השיניים בשוליים השמאליים, מחוץ ל-.main של השורה,
     בגובה השורה הראשונה של הסימון, אחד מתחת לשני, וצמודים לסימון בגלילה. כשאין שוליים (מסך צר):
     "סכם קטע" בסרגל העליון, ליד "סכם פרק". לפני כן הכפתור ישב בקצה השמאלי של השורה הבאה - על המילים. */
  function skmMk(id,txt,fn,cls){let b=$('#'+id);
    if(!b){b=document.createElement('button');b.id=id;b.type='button';if(cls)b.className=cls;b.textContent=txt;
      b.addEventListener('mousedown',e=>e.preventDefault());b.addEventListener('click',fn);document.body.appendChild(b)}
    return b}
  function skmBtnShow(){
    if(!SKM.sel||!SKM.sel.show){skmBtnHide();return}
    const b=skmMk('skmbtn','סכם',()=>skmGo());
    const g=skmMk('skmset','⚙',()=>skmPanel());g.title='סכם: התור';g.setAttribute('aria-label','סכם: התור');
    const tip=SKM.sel.long?'הקטע ארוך מדי, נא לסמן עד דף אחד':'הידוק ותיקון הקטע המסומן, מיד (Ctrl+Shift+S). להרחבה: גרירה על כמה שורות, או Shift+לחיצה על שורה אחרת';
    const n=SKM.sel.rows.length;
    b.textContent='סכם'+(n>1?' · '+n+' שורות':'');b.title=tip;b.classList.toggle('dim',!!SKM.sel.long);
    const rows=SKM.sel.rows.filter(r=>r.isConnected);if(!rows.length){skmBtnHide();return}
    const first=rows[0],last=rows[rows.length-1];
    const m=first.querySelector(':scope > .main')||first;
    const mr=m.getBoundingClientRect(),lr=last.getBoundingClientRect();
    const fl=$('#flow'),fr=fl?fl.getBoundingClientRect():{left:0,top:0,bottom:innerHeight};
    const barB=(($('#bar')||{}).getBoundingClientRect?$('#bar').getBoundingClientRect().bottom:44);
    b.style.display='block';g.style.display='block';
    const bw=b.offsetWidth,bh=b.offsetHeight,gw=g.offsetWidth,gh=g.offsetHeight;
    const room=mr.left-Math.max(0,fr.left);
    const tb=$('#skmtop');
    if(room>=Math.max(bw,gw)+20){
      if(tb)tb.style.display='none';
      /* גובה השורה הראשונה של הסימון: המלבן הראשון של הבחירה, אם היא מתחילה בשורה הראשונה */
      let top=mr.top;
      const s=getSelection();
      if(s&&s.rangeCount&&!s.getRangeAt(0).collapsed&&first.contains(s.getRangeAt(0).startContainer)){
        const rc=[...s.getRangeAt(0).getClientRects()].find(x=>x.width>0&&x.height>0);if(rc)top=rc.top}
      const lo=Math.max(barB+6,fr.top+4),hi=Math.min(innerHeight-bh-gh-14,lr.bottom-bh);
      if(lr.bottom<lo||mr.top>innerHeight){skmBtnHide();return}
      top=Math.max(lo,Math.min(hi,top));
      const right=mr.left-10;
      b.style.top=top+'px';b.style.left=(right-bw)+'px';
      g.style.top=(top+bh+6)+'px';g.style.left=(right-gw)+'px';
      return}
    /* אין שוליים: לסרגל העליון */
    b.style.display='none';g.style.display='none';
    let t=tb;
    if(!t){const anchor=$('#skpbtn')||$('#peresel');
      t=document.createElement('button');t.id='skmtop';t.type='button';t.className='skpbtn';
      t.addEventListener('mousedown',e=>e.preventDefault());t.addEventListener('click',()=>skmGo());
      if(anchor)anchor.after(t);else ($('#bar')||document.body).appendChild(t)}
    t.textContent='סכם קטע'+(n>1?' · '+n:'');t.title=tip;t.classList.toggle('dim',!!SKM.sel.long);t.style.display=''}
  function skmBtnHide(){['#skmbtn','#skmset','#skmtop'].forEach(s=>{const b=$(s);if(b)b.style.display='none'})}
  addEventListener('scroll',()=>{if(SKM.sel&&SKM.sel.show)skmBtnShow()},{passive:true,capture:true});
  addEventListener('resize',()=>{if(SKM.sel&&SKM.sel.show)skmBtnShow()});
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
    /* הכרעת המנהל 29.10: קטע מסומן - מיד, דרך ה-API. אין מפתח, נגמר הקרדיט או השירות נפל (השרת מחזיר queue) -
       הקטע נכנס לתור של "סכם פרק", והמשימה המתוזמנת מכינה לו הצעה */
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
      skmArrive({id:j.id,ids,orig,text:j.text,point:j.point||'',changes:j.changes||[],warn:j.warn||[],notes:j.notes||[],usd:j.usd||0,round:1});
    }catch(err){
      const m=err.message||'';
      if(err.j&&err.j.queue){
        try{await skpEnqueue('seg',ids);toast(m+' - הקטע נכנס לתור, וההצעה תוכן במשימה המתוזמנת',6000)}
        catch(e2){flash('סכם: '+(e2.message||e2))}}
      else if(/טרם פורסמו|לא נמצאה באתר/.test(m)){
        if(confirm(m+'\n\nלפרסם עכשיו את העריכות הממתינות ולנסות שוב?')){await pubNow(1);setTimeout(()=>{skmMark(rows.filter(r=>r.isConnected));skmGo()},1200)}}
      else flash('סכם: '+m)}
    finally{SKM.busy.delete(key);rows.forEach(r=>r.classList.remove('skmbusy'))}}
  function skmArrive(p){
    /* הקטע השתנה בזמן היצירה: ההצעה כבר אינה מתאימה */
    if(!skmSame(p.ids,p.orig)){flash('הקטע השתנה בזמן היצירה. סמן שוב ובקש הצעה חדשה');skmDone(p,'stale');return}
    if(SKM.ghost){SKM.wait.push(p);toast('הצעת סכם נוספת מוכנה, ותוצג אחרי שתסיים את הנוכחית');return}
    skmShow(p)}

  /* ---- הרוח: ההצעה במקום הקטע ---- */
  /* מה השתנה, במבט אחד (פרומפט 7): הסבר חדש ברקע צהוב, מספר שנוסף בזהב, ודובר שעבר בין
     השורה לכותרת הצד בקו מקווקו. הסימון הוא data-skm בלבד: הקריאה חזרה (h2i) מתעלמת ממנו. */
  function skmMarks(text,orig){
    const R=SKC.rows(text),M=R.map(()=>({hs:new Set(),num:false,mv:false}));
    if(!orig)return M;
    const nh=SKC.newHs(orig,text);
    nh.forEach(x=>{const sp=SKC.spans(R[x.ri].v,'הס');const k=sp.findIndex(s=>s.a===x.a);if(k>-1)M[x.ri].hs.add(k)});
    const bag={};SKC.nums(orig).forEach(n=>{bag[n]=(bag[n]||0)+1});
    R.forEach((r,i)=>{const n=SKC.numOf(r.p);if(!n)return;if(bag[n]){bag[n]--;return}M[i].num=true});
    /* רק כותרת או פתיח שורה חדשים: כותרת שהיתה במקור כמות שהיא לא זזה */
    const mv=new Set(SKC.movedNames(orig,text)),unNum=p=>p.replace(/^[א-י]\.\s*/,'');
    const oT={},oL={},take=(o,k)=>o[k]>0?(o[k]--,true):false;
    const opener=r=>{const s=unNum(r.v);const x=s.indexOf('{אם:')===0&&SKC.spans(s,'אם')[0];return x?SKC.nbase(SKC.plainI(x.v)):''};
    SKC.rows(orig).forEach(r=>{const k=r.k==='title'?unNum(r.p):opener(r),o=r.k==='title'?oT:oL;if(k)o[k]=(o[k]||0)+1});
    if(mv.size)R.forEach((r,i)=>{
      if(r.k==='title'){const k=unNum(r.p);M[i].mv=!take(oT,k)&&r.p.split(/[\s,]+/).some(w=>mv.has(SKC.nbase(w)))}
      else{const b=opener(r);M[i].mv=!!(b&&!take(oL,b)&&mv.has(b))}});
    return M}
  function skmMarkH(h,m){
    if(!m)return h;
    if(m.hs.size){let k=-1;h=h.replace(/<i class="hs">/g,t=>(++k,m.hs.has(k)?'<i class="hs" data-skm="new">':t))}
    if(m.num)h=h.replace(/^([א-י]\.)/,'<span data-skm="num">$1</span>');
    return h}
  function skmGhostBody(text,orig){
    const toks=SKC.parse(text);let h='',row=null,ri=0;
    const MK=skmMarks(text,orig);
    const flush=()=>{if(!row)return;
      h+='<div class="skmrow"><div class="skmrail">'+row.t.map(t=>'<span class="skmanc"'+(t.m&&t.m.mv?' data-skm="moved"':'')+'>'+skmMarkH(SKC.i2h(t.v,true),t.m)+'</span>').join('')+'</div>'+
         '<div class="skmmain">'+row.l.map(l=>l.src?'<p class="skmsrc" contenteditable="false" data-tok="'+esc(l.src).replace(/"/g,'&quot;')+'"></p>':
           '<p data-sty="'+(l.sty||'')+'" class="'+(l.sty||'')+'">'+(skmMarkH(SKC.i2h(l.v,true),l.m).replace(/<i class="am">/,x=>l.m&&l.m.mv?'<i class="am" data-skm="moved">':x)||'<br>')+'</p>').join('')+'</div></div>';row=null};
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
      /* פרומפט 27: עיטור שנמחק ליד כותרת - בקו חוצה, ונשמר כאסימון בקריאה חזרה */
      if(k.t==='line'&&/^\[מחק-עיטור:\d+\]$/.test(k.v.trim())){flush();
        h+='<div class="skmlock skphdel" contenteditable="false" data-tok="'+esc(k.v.trim())+'" title="העיטור נמחק: הכותרת עצמה היא החציצה"><del>***</del> עיטור נמחק</div>';return}
      if(k.t==='title'){if(row&&row.l.length)flush();if(!row)row={t:[],l:[]};row.t.push({v:k.v,m:MK[ri++]});return}
      if(!row)row={t:[],l:[]};row.l.push(Object.assign({},k,{m:MK[ri++]}))});
    flush();return h}
  /* קריאה חזרה מן הרוח אחרי עריכה ישירה */
  function skmReadBack(g){
    /* מה שהוצג לעיון בלבד (המילים שנמחקו בהצעה) אינו חלק מן הנוסח */
    g=g.cloneNode(true);g.querySelectorAll('del.skpdel').forEach(x=>x.remove());
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
    /* השלד במבט אחד: אם המודל לא הבין את הסוגיה, רואים זאת לפני שקוראים את הנוסח */
    g.innerHTML=(p.point?'<div class="skmpoint" contenteditable="false"><b>השלד:</b> '+esc(p.point)+'</div>':'')+
      '<div class="skmbody">'+skmGhostBody(p.text,p.orig)+'</div>'+
      '<div class="skmbar" contenteditable="false">'+
        '<span class="skmt">הצעת סכם'+(p.round>1?' · קיצור '+p.round:'')+'</span>'+
        (blocked?'<span class="skmwarn" title="'+esc(p.warn.join(' · '))+'">⚠ '+esc(p.warn.join(' · '))+'</span>':'')+
        (p.notes&&p.notes.length?'<span class="skmnote" title="'+esc(p.notes.join(' · '))+'">'+esc(p.notes.join(' · '))+'</span>':'')+
        '<button type="button" data-a="ok"'+(blocked?' hidden':'')+' title="Enter">קבל</button>'+
        '<button type="button" data-a="edit">ערוך</button>'+
        (p.id&&!p.jid?'<button type="button" data-a="more">קצר עוד</button>':'')+
        (p.hist&&p.hist.length?'<button type="button" data-a="back" title="חזרה להצעה הקודמת, בלי קריאה חדשה ובלי עלות">חזרה לקודמת</button>':'')+
        '<button type="button" data-a="no" title="Esc">בטל</button>'+
        '<button type="button" data-a="set" class="skmlink" title="התור של סכם">התור</button>'+
        (p.changes&&p.changes.length?'<details class="skmwhy"><summary>מה שיניתי</summary><ul>'+p.changes.slice(0,5).map(c=>'<li>'+esc(c)+'</li>').join('')+'</ul></details>':'')+
      '</div>';
    rows[rows.length-1].after(g);
    SKM.ghost=g;SKM.cur=p;
    /* אירועי העורך אינם נוגעים ברוח: הקלדה כאן אינה תיקון בדף */
    ['keydown','keyup','input','focusin','focusout','beforeinput'].forEach(t=>g.addEventListener(t,ev=>{
      if(t==='keydown')skmGhostKey(ev);ev.stopPropagation()}));
    g.querySelector('.skmbar').addEventListener('click',ev=>{const b=ev.target.closest('button');if(!b)return;
      ({ok:skmAccept,edit:skmEdit,more:skmMore,no:skmCancel,back:skmBack,set:()=>skmPanel()})[b.dataset.a]()});
    /* המיקוד עובר להצעה, כדי ש-Enter יקבל ו-Esc יבטל ולא יפצלו פסקה בדף */
    g.tabIndex=-1;
    g.scrollIntoView({block:'nearest',behavior:'smooth'});
    try{const a=document.activeElement;if(a&&a!==document.body&&!g.contains(a))a.blur();g.focus({preventScroll:true})}catch(e){}}
  /* קבלה מהירה: Enter = קבל, Esc = בטל (לא במצב עריכה; שם Ctrl+Enter מקבל את הנוסח הערוך) */
  function skmQuick(key){
    const g=SKM.ghost;if(!g||g.classList.contains('edit'))return;
    if(key==='Enter'){const ok=g.querySelector('[data-a="ok"]');if(ok&&!ok.hidden)skmAccept();else flash('ההצעה נחסמה בשומר: ערוך אותה או בטל');return}
    if(key==='Escape')skmCancel()}
  function skmGhostKey(ev){
    if(!SKM.ghost)return;
    if(!SKM.ghost.classList.contains('edit')){
      if(ev.key==='Escape'||ev.key==='Enter'&&!ev.ctrlKey&&!ev.altKey&&!ev.shiftKey&&!ev.target.closest('button')){ev.preventDefault();skmQuick(ev.key)}
      return}
    if(ev.key==='Enter'&&ev.ctrlKey&&!ev.altKey&&!ev.shiftKey){ev.preventDefault();skmAccept();return}
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
  /* שמירה על העריכה במקום (פרומפט 20, 5.11.2026): עוגני תוס' ומספרי משנה אינם נמחקים
     ב-Backspace/Delete (הסמן מדלג עליהם), הדבקה נכנסת כטקסט פשוט, ופתיח שמקומו בכותרת צד
     (שם אמורא עם נקודתיים, א. ב. ג., גופא, ת"ר...) מקבל הצעה עדינה "לכותרת צד" (Ctrl+.) */
  const SKM_CHIP='i.tzc,i.mk';
  const SKM_SIDE=/^\s*((?:[א-י]\.\s*)?(?:(?:ו?(?:ר'|רב|רבי|ר"|אמר|א"ל|אמרו|גופא|ת"ר|ת"ש|תניא|איתיביה|מיתיבי|ורמינהי|קשיא|קשה|תיובתא|אלא|והא|ואב"א|א"נ)[^\s:]*(?:\s[^\s:]{1,10}){0,2}:)|[^\s:]{2,10}(?:\s[^\s:]{1,10})?:|[א-י]\.)(?=\s))/;
  function skmCaretNode(dir){
    const sel=getSelection();if(!sel.rangeCount||!sel.isCollapsed)return null;
    const r=sel.getRangeAt(0);let n=r.startContainer,o=r.startOffset;
    if(n.nodeType===3){if(dir<0&&o>0)return null;if(dir>0&&o<n.nodeValue.length)return null;
      let x=n;while(x&&!(dir<0?x.previousSibling:x.nextSibling)&&x.parentElement&&!x.parentElement.matches('p'))x=x.parentElement;
      return x?(dir<0?x.previousSibling:x.nextSibling):null}
    return n.childNodes[dir<0?o-1:o]||null}
  function skmSideHint(g){
    let h=g.querySelector('.skmsidehint');
    const sel=getSelection();const p=sel.rangeCount&&sel.anchorNode&&(sel.anchorNode.nodeType===1?sel.anchorNode:sel.anchorNode.parentElement).closest('.skmmain p');
    const m=p&&SKM_SIDE.exec(p.textContent||'');
    if(!m){if(h)h.remove();return}
    if(!h){h=document.createElement('button');h.type='button';h.className='skmsidehint';h.contentEditable='false';
      h.onmousedown=e=>e.preventDefault();h.onclick=()=>skmToSide(g);g.appendChild(h)}
    h.textContent='"'+m[1].trim()+'" לכותרת צד? (Ctrl+.)';h._p=p;h._t=m[1]}
  /* העברת הפתיח של השורה לכותרת צד: השורה נפתחת שורה (skmrow) משלה אם אינה הראשונה בה */
  function skmToSide(g){
    const h=g.querySelector('.skmsidehint');if(!h||!h._p||!h._p.isConnected)return;
    const p=h._p,pre=h._t,row=p.closest('.skmrow');if(!row)return;
    const main=row.querySelector('.skmmain');let tr=row;
    if(main.firstElementChild!==p){
      tr=document.createElement('div');tr.className='skmrow';tr.innerHTML='<div class="skmrail"></div><div class="skmmain"></div>';
      const nm=tr.querySelector('.skmmain');let x=p;while(x){const nx=x.nextElementSibling;nm.appendChild(x);x=nx}
      row.after(tr)}
    /* הסרת הפתיח מתחילת השורה, בלי לשבור את התגים שבה */
    let left=pre.length;const w=document.createTreeWalker(p,NodeFilter.SHOW_TEXT);let t;
    while(left>0&&(t=w.nextNode())){const k=Math.min(left,t.nodeValue.length);t.nodeValue=t.nodeValue.slice(k);left-=k}
    w.currentNode=p;while((t=w.nextNode())){if(!t.nodeValue)continue;t.nodeValue=t.nodeValue.replace(/^\s+/,'');if(t.nodeValue)break}
    p.querySelectorAll('i,b').forEach(e=>{if(!e.textContent.trim()&&!e.matches(SKM_CHIP))e.remove()});
    const a=document.createElement('span');a.className='skmanc';a.textContent=pre.trim();
    tr.querySelector('.skmrail').appendChild(a);
    h.remove();
    const r=document.createRange();r.selectNodeContents(p);r.collapse(true);const s=getSelection();s.removeAllRanges();s.addRange(r)}
  function skmGuardEdit(g){
    const b=g.querySelector('.skmbody');if(!b||b._skmg)return;b._skmg=1;
    b.addEventListener('keydown',e=>{
      if((e.key==='Backspace'||e.key==='Delete')&&!e.ctrlKey){
        const n=skmCaretNode(e.key==='Backspace'?-1:1),c=n&&(n.nodeType===1?n:n.parentElement);
        if(c&&c.matches&&c.matches(SKM_CHIP)){e.preventDefault();e.stopPropagation();
          const r=document.createRange();if(e.key==='Backspace')r.setStartBefore(c);else r.setStartAfter(c);r.collapse(true);
          const s=getSelection();s.removeAllRanges();s.addRange(r);flash('עוגן נעול - נשמר אוטומטית')}}
      if(e.ctrlKey&&!e.altKey&&(e.key==='.'||e.code==='Period')){const h=g.querySelector('.skmsidehint');if(h){e.preventDefault();e.stopPropagation();skmToSide(g)}}},true);
    b.addEventListener('keyup',()=>skmSideHint(g));b.addEventListener('mouseup',()=>skmSideHint(g));
    b.addEventListener('paste',e=>{const t=(e.clipboardData||window.clipboardData).getData('text/plain');if(t==null)return;
      e.preventDefault();document.execCommand('insertText',false,t.replace(/\s*\n\s*/g,' '))});}
  window.skmGuardEdit=skmGuardEdit;
  function skmEdit(){
    const g=SKM.ghost;if(!g)return;
    g.classList.add('edit');
    const b=g.querySelector('.skmbody');b.setAttribute('contenteditable','');b.setAttribute('spellcheck','false');skmGuardEdit(g);
    const ok=g.querySelector('[data-a="ok"]');ok.hidden=false;ok.textContent='קבל את הנוסח הערוך';
    g.querySelector('[data-a="edit"]').hidden=true;
    const p=b.querySelector('p');if(p){p.focus();const r=document.createRange();r.selectNodeContents(p);r.collapse(false);const s=getSelection();s.removeAllRanges();s.addRange(r)}}
  async function skmMore(){
    const p=SKM.cur;if(!p)return;
    const g=SKM.ghost;g.classList.add('skmbusy');
    try{const j=await api('/sakem/more',{method:'POST',body:JSON.stringify({slug:SLUG,id:p.id})});
      /* ההצעה הקודמת נשמרת במכשיר: "חזרה לקודמת" מחזירה אותה בלי קריאה חדשה ובלי עלות */
      skmShow(Object.assign({},p,{id:j.id,text:j.text,point:j.point||p.point||'',changes:j.changes||[],warn:j.warn||[],notes:j.notes||[],round:(p.round||1)+1,
        hist:(p.hist||[]).concat([Object.assign({},p,{hist:null})])}))}
    catch(err){g.classList.remove('skmbusy');flash('קצר עוד: '+(err.message||''))}}
  function skmCancel(){const p=SKM.cur;skmClose();if(p)skmDone(p,'cancel')}
  function skmBack(){const p=SKM.cur;if(!p||!p.hist||!p.hist.length)return;
    const prev=p.hist[p.hist.length-1];
    skmShow(Object.assign({},prev,{hist:p.hist.slice(0,-1)}))}
  function skmDone(p,act,fin){
    api('/sakem/done',{method:'POST',body:JSON.stringify({slug:SLUG,id:p.id,act,final:fin||''})}).catch(()=>{})}
  /* תיקון אוטומטי של מה שעריכה ידנית עלולה לשבור, לפני השומר (פרומפט 20, 5.11.2026):
     נעולים ברמת השורה (skpFixLocks), עוגני תוס' ומספרי משנה שבתוך השורה (SKC.fixInline),
     ותגים שבורים (סוגר או פותח יתום). עריכת המנהל אינה נפסלת על דבר שאפשר לתקן לבד. */
  function skmRepair(orig,text){
    let t=String(text||'');
    try{if(window.skpFixLocks)t=window.skpFixLocks(orig,t)}catch(e){}
    let moved=[];
    try{const r=SKC.fixInline(orig,t);t=r.text;moved=r.moved}catch(e){}
    /* תג לא מוכר: פותח {x: שאינו ידוע - מוסר (התוכן נשאר); סוגר } יתום - מוסר */
    t=t.split('\n').map(ln=>{const bad=[];SKC.i2h(ln,true,bad);if(!bad.length)return ln;
      let out='',d=[];for(let i=0;i<ln.length;i++){const c=ln[i];
        if(c==='{'){const m=/^\{([^{}:\s]{1,4}):/.exec(ln.slice(i,i+8));
          if(m&&!SKC.T2C_OK(m[1])){d.push(0);i+=m[0].length-1;continue}d.push(1);out+=c;continue}
        if(c==='}'){if(!d.length)continue;if(!d.pop())continue}
        out+=c}
      return out}).join('\n');
    return {text:t,moved}}
  window.skmRepair=skmRepair;
  function skmMovedNote(m){if(m&&m.length)toast('הוחזר למקום משוער - כדאי להציץ: '+m.join(', '),6000)}
  function skmAccept(){
    const p=SKM.cur,g=SKM.ghost;if(!p||!g)return;
    const edited=g.classList.contains('edit');
    const rp=skmRepair(p.orig,edited?skmReadBack(g):p.text),text=rp.text;
    const errs=SKC.guard(p.orig,text,{edited:true}).filter(x=>/נעולים|קטע שלם|נוספו שורות|תג לא מוכר/.test(x));
    if(errs.length){flash('לא הוחל: '+errs[0]+'. העריכה שלך נשמרה פתוחה - אפשר לתקן ולנסות שוב');return}
    let r;
    try{r=skmApply(p,text)}catch(err){flash('לא הוחל: '+(err.message||err));return}
    skmClose();
    skmDone(p,edited?'edit':'accept',text);
    skmRemember(p.id,text,r.recs||[]);
    flash(r.n?'הוחל: '+r.n+' שינויים, ויפורסמו עם שאר העריכות (Ctrl+Z מבטל)':'אין שינוי להחיל');skmMovedNote(rp.moved)}

  /* =================== עריכה מאוחרת של שורה שנכתבה ב"סכם" (27.10.2026) ===================
     גם תיקון שהמנהל עושה בעורך אחרי שקיבל את ההצעה הוא לקח: השורות שנכתבו נזכרות במכשיר
     (נוסח ← מזהה ההצעה), וכל תיקון שלהן נשלח לנקודת הקליטה ונצמד לאותה הצעה ביומן הלמידה. */
  const SKMK='lg-skm-made-'+SLUG;
  function skmMade(){try{return JSON.parse(localStorage.getItem(SKMK)||'{}')}catch(e){return {}}}
  const skmNorm=t=>nonik(String(t||'')).replace(/\s+/g,' ').trim();
  function skmRemember(id,text,recs){
    const m=skmMade();
    SKC.parse(text).forEach(k=>{if(k.t==='line'){const t=skmNorm(SKC.plainI(k.v));if(t.length>3)m[t]=[id,Date.now()]}});
    const ks=Object.keys(m);if(ks.length>600)ks.sort((a,b)=>m[a][1]-m[b][1]).slice(0,ks.length-600).forEach(k=>delete m[k]);
    try{localStorage.setItem(SKMK,JSON.stringify(m))}catch(e){}
    /* גם לפי מפתח המקום: רשומה שהוחלפה בעותק מן השרת מאבדת שדות מקומיים */
    recs.forEach(e=>{if(e.op!=='struct'&&e.k){const I=SKC.h2i(e.nowH||'');e._skm=id;e._skmNow=e.now;e._skmNowI=I;m['k:'+e.k]=[id,Date.now(),e.now,I]}});
    try{localStorage.setItem(SKMK,JSON.stringify(m))}catch(e){}
    saveED()}
  SKM.lat={};
  const skmCap0=capture;
  capture=function(el){skmCap0(el);try{skmLater(el)}catch(e){}};
  function skmLater(el){
    if(!isAdmin()||SUGM)return;
    const k=el&&el.dataset&&el.dataset.ek;if(!k)return;
    const e=ED.find(x=>x.op!=='struct'&&x.k===k);if(!e||e.now===e.was)return;
    let hit=null;
    if(e._skm&&e._skmNow!==undefined&&skmNorm(e._skmNow)!==skmNorm(e.now))hit={id:e._skm,was:e._skmNow,wasI:e._skmNowI||''};
    else{const m=skmMade(),hk=m['k:'+k],h=m[skmNorm(e.was)];
      if(hk&&skmNorm(hk[2])!==skmNorm(e.now))hit={id:hk[0],was:hk[2],wasI:hk[3]||''};
      else if(h)hit={id:h[0],was:e.was,wasI:SKC.h2i(e.wasH||'')}}
    if(!hit)return;
    /* בפורמט הביניים, כדי שנקודת הקליטה תדע את סוג התיקון: מספור / הסבר (פרומפט 7) */
    SKM.lat[k]={id:hit.id,was:hit.was,now:e.now,daf:e.daf||'',wasI:hit.wasI,nowI:SKC.h2i(e.nowH||'')};
    clearTimeout(SKM.latT);SKM.latT=setTimeout(skmLaterFlush,20000)}
  function skmLaterSend(x){
    fetch(SUGGEST_API+'/sakem/later',{method:'POST',keepalive:true,headers:{'content-type':'application/json; charset=utf-8','x-admin-key':admKey()},
      body:JSON.stringify({slug:SLUG,id:x.id,was:x.was,now:x.now,daf:x.daf,wasI:x.wasI||'',nowI:x.nowI||'',kinds:x.kinds||[]})}).catch(()=>{})}
  function skmLaterFlush(){
    const L=SKM.lat;SKM.lat={};
    Object.keys(L).forEach(k=>skmLaterSend(L[k]))}
  addEventListener('pagehide',skmLaterFlush);
  /* דובר שהועבר אחרי הקבלה מן השורה לכותרת צד (או בחזרה) הוא פעולת מבנה ולא תיקון טקסט:
     כל רשומת side / unside חדשה שנוגעת בשורה שנכתבה ב"סכם" נרשמת ביומן הלמידה כסוג "דובר".
     רשומות שהקבלה עצמה יצרה (skmApply מסמן אותן כנראו) אינן תיקון של המחבר. */
  SKM.seenS=new Set(ED.filter(e=>e.op==='struct').map(e=>e.t));
  const skmSave0=saveED;
  saveED=function(){skmSave0();try{skmStructLater()}catch(e){}};
  function skmStructLater(){
    if(!isAdmin()||SUGM)return;
    let m=null;
    ED.forEach(e=>{if(e.op!=='struct'||SKM.seenS.has(e.t))return;SKM.seenS.add(e.t);
      if(!/^(side|unside|unside-merge)$/.test(e.kind||''))return;
      m=m||skmMade();
      const hit=(e.texts||[]).map(t=>m[skmNorm(t)]).find(Boolean);if(!hit)return;
      skmLaterSend({id:hit[0],was:(e.texts||[]).join(' | '),now:(e.resT||[]).join(' | '),daf:e.daf||'',kinds:['דובר']})})}

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
    let os=skmUnits(p.ids);
    if(!skmSame(p.ids,p.orig))throw new Error('הקטע השתנה מאז ההצעה. בקש הצעה חדשה');
    const pis=[...new Set(os.map(o=>o.pi))];
    const pre=pis.map(pi=>({pi,snap:JSON.stringify(D.pages[pi].units)})),befores=pis.map(snapOf);
    const RECS=[],OLDS=[];let T0=Date.now();
    const nt=()=>(T0=Math.max(T0+1,Date.now()));
    const add=e=>{e.t=nt();e.pub=0;e._ap=1;ED.push(e);RECS.push(e);if(SKM.seenS)SKM.seenS.add(e.t);return e};
    /* פרומפט 27: עיטור ליד כותרת שההצעה מוחקת ([מחק-עיטור:<מזהה>], ראה SKC.hatzDel). רק יחידת עיטור
       (k=hatz), ובאותה רשומה בדיוק שהעורך כותב ב"מחק עיטור" (hdel) - כך המחיקה עוברת לאתר ולוורד */
    const undoAll=()=>{pre.forEach(z=>{D.pages[z.pi].units=JSON.parse(z.snap)});
      RECS.forEach(e=>{const i=ED.indexOf(e);if(i>-1)ED.splice(i,1)});SLOTS=null;befores.forEach(b=>patchPage(b))};
    if(p.hdel&&p.hdel.length){
      try{p.hdel.forEach(id=>{
          const o=os.find(x=>x.u.id===id);
          if(!o||o.u.k!=='hatz')throw new Error('אפשר למחוק רק עיטור (לא פתיחת פרק ולא הדרן)');
          const items=decoItems(),i=items.findIndex(x=>x.deco&&x.j===null&&x.u.id===id);
          if(i<0)throw new Error('העיטור לא אותר בדף');
          const [prev,next]=decoNb(items,i);
          const se={op:'struct',kind:'hdel',texts:[prev,next],res:[],resT:[],daf:o.u.daf||D.pages[o.pi].daf||''};
          if(!decoApplyData({pi:o.pi,u:o.u,j:null},se))throw new Error('העיטור לא נמחק');
          add(se)});
        SLOTS=null;os=skmUnits(p.ids.filter(id=>p.hdel.indexOf(id)<0))}
      catch(err){undoAll();throw err}}
    const NS=SKC.segments(SKC.parse(newText)),OS=skmOsegs(os);
    if(NS.length!==OS.length){undoAll();throw new Error('מבנה הקטע אינו תואם (האלמנטים הנעולים)')}
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
      /* תיקון 6.11.2026 (כתובות פרק א): מפתח של תיקון ישן הוא מקום (u<יחידה>.<שורה>), ואחרי פיצול,
         איחוי או כותרת צד באותה קבלה הוא מצביע כבר על שורה אחרת. כאן נלקח בעבר התיקון הישן של
         השורה הקודמת - "was" שלו נשאר הנוסח של שורה אחרת, ובשחזור הוא דרס אותה: שורות כפולות,
         ושורות שנעלמו (אין להקשות מרב, ג' יוצר האדם, ועוד). מעתה תיקון ישן ממשיך רק כשהוא באמת
         התיקון של השורה הזאת (הנוסח שלו הוא הנוסח שבמקום); אחרת הוא "קופא" כמו בשינוי מבנה,
         ונוצר תיקון חדש. */
      const tN=s=>String(s||'').replace(/\s+/g,' ').trim(),curT=tN(plain(cur));
      ED.filter(x=>x.op!=='struct'&&x.k===k&&!x.fz&&tN(x._cur!==undefined?x._cur:x.now)!==curT).forEach(x=>{
        OLDS.push([x,JSON.stringify(x)]);tomb(x.k);x.k=x.k+'~'+x.t;x.fz=1});
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
      if(!pv||!cu)throw new Error('היחידה הקודמת לא נמצאה לאיחוד');
      const pl=usmPlan(pv,cu);if(pl.err||!pl.fuse)throw new Error(pl.err||'לא ניתן לאחד כאן שתי יחידות');
      const P=pv.u,U=cu.u,ph=P.l[P.l.length-1],nh=U.l[0];
      const texts=[plain(ph[1]),plain(nh[1])];
      const h=ph[1]+(/\s$/.test(texts[0])||/^\s/.test(texts[1])||!texts[0].trim()?'':' ')+nh[1];
      freezeEdits(texts);
      const e=add({op:'struct',kind:'unside-merge',texts,res:[[ph[0],h],[],[pl.where]],resT:[plain(h)],daf:pgDaf(cu.pi)});
      usmData(e,pv,cu);SLOTS=null;
      /* איחוד "למטה" (העליונה התרוקנה ונמחקה): היחידה העליונה חיה מעתה בתוך התחתונה.
         בלעדי זה האיטרציה הבאה חיפשה יחידה שאינה קיימת ונפלה (4.11.2026, ברכות פרק ו) */
      if(!flatU().some(x=>x.u===P))GONE.set(P,U);
      if(!flatU().some(x=>x.u===U))GONE.set(U,P)}
    const GONE=new Map();
    const live=u=>{let n=0;while(GONE.has(u)&&n++<50)u=GONE.get(u);return u};
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
        /* פרומפט 27: בלי חסימה. אין גבול מילה מתאים - חותכים בתו כלשהו; אין גם תו - נוספת שורה
           ריקה בסוף. כל חלק מקבל אחר כך את נוסחו המלא (setText), ולכן מקום החיתוך אינו משנה דבר בנוסח. */
        if(cuts.length&&cuts[cuts.length-1]<0){cuts.push(-1);continue}
        if(best<0)for(let d=0;d<L&&best<0;d++)for(const x of [c-d,c+d])if(x>0&&x<L&&(!cuts.length||x>cuts[cuts.length-1]+1)){best=x;break}
        cuts.push(best<0?-1:best)}
      let prev=0;
      cuts.forEach((c,q)=>{const el=document.createElement('div');el.innerHTML=U.l[i+q][1];
        if(c<0){split(U,i+q,U.l[i+q][1],'',daf);return}
        const sp=was[c]===' ',off=c-prev,pa=posAt(el,off),pb=posAt(el,sp?off+1:off);
        const h1=pieceHTML(el,null,pa),h2=pieceHTML(el,pb,null);
        split(U,i+q,h1,h2,daf);prev=sp?c+1:c})}
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
        /* פרומפט 27 (8.11.2026, בבא בתרא עה. "כדכד"): כותרת חדשה בראש הקטע, לפני כותרת הצד הראשונה,
           נקראת כיחידה בלי כותרת. בלי ההיסט הזה כל ההתאמה זזה ביחידה אחת: היחידה הראשונה במקור הותאמה
           לשורת הכותרת לבדה, והשנייה לשתי יחידות - והמנוע ניסה לפצל שורה קצרה לשבע ונחסם. כאן היחידה
           החדשה שבלי כותרת מצטרפת לקבוצה הראשונה, וההתאמה נמשכת מן היחידה שאחריה. */
        const sh=(N.units.length>O.units.length&&!VT[0].length&&OT[0].length&&VT.length>1)?1:0;
        const A=OT.map(t=>t.join('|')),B=VT.slice(sh).map(t=>t.join('|'));
        const L=[...Array(A.length+1)].map(()=>new Array(B.length+1).fill(0));
        for(let i=A.length-1;i>=1;i--)for(let j=B.length-1;j>=1;j--)
          L[i][j]=A[i]&&A[i]===B[j]?L[i+1][j+1]+1:Math.max(L[i+1][j],L[i][j+1]);
        const cuts=[[0,0]];
        for(let i=1,j=1;i<A.length&&j<B.length;){
          if(A[i]&&A[i]===B[j]){cuts.push([i,j]);i++;j++}else if(L[i+1][j]>=L[i][j+1])i++;else j++}
        const jb=(j,n)=>n?j+sh:j;
        const groups=cuts.map((c,n)=>{const nx=cuts[n+1]||[A.length,B.length];
          return {O:O.units.slice(c[0],nx[0]),N:N.units.slice(jb(c[1],n),jb(nx[1],1))}});
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
          else{const fu=flatU(),lu=live(o.u),n=fu.findIndex(x=>x.u===lu);
            if(n<1)throw new Error('היחידה לא נמצאה אחרי האיחוד');fuse(fu[n-1],fu[n])}}
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
          /* הוספה בלבד (חסר מהגמרא): אין שורה ישנה באמצע לפצל - השורה הקודמת נכנסת לפיצול */
          if(cur.length-pre-suf<1){if(pre)pre--;else suf--}
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

  /* =================== חלונית הניהול: התור של סכם (פרומפט 15: בלי מפתח ובלי עלות) =================== */
  function skmPanelBtn(){const box=$('#edb');if(!box||SUGM||!isAdmin())return;
    const row=box.querySelector('div[style*="flex-wrap"]');if(!row||row.querySelector('.skmpb'))return;
    const b=document.createElement('button');b.className='skmpb';b.textContent='סכם: התור';b.onclick=()=>skmPanel();row.appendChild(b)}
  const skmDraw0=drawEd;
  drawEd=function(){skmDraw0();skmPanelBtn()};
  window.skmPanel=function(){skpPanel()};
  async function skmQOpen(){
    try{const j=await api('/sakem/queue?slug='+encodeURIComponent(SLUG));SKM.q=(j.items||[]).filter(x=>!x.d);
      if(!SKM.q.length){flash('התור ריק');SKM.q=null;return}
      skmQNext()}catch(e){flash(e.message)}}
  function skmQNext(){
    if(!SKM.q||!SKM.q.length){if(SKM.q)flash('התור הסתיים');SKM.q=null;return}
    const it=SKM.q.shift();
    const os=skmUnits(it.ids);
    if(!skmSame(it.ids,it.orig)){skmDone(it,'stale');return skmQNext()}
    const r=document.getElementById('u'+it.ids[0]);if(r)r.scrollIntoView({block:'center'});
    skmShow({id:it.id,ids:it.ids,orig:it.orig,text:it.text,point:it.point||'',changes:it.changes||[],warn:it.warn||[],notes:it.notes||[],round:1})}

  /* ---- מראה ---- */
  (function(){const s=document.createElement('style');s.textContent=
    '#flow .row.skmsel{background:rgba(70,120,190,.07);box-shadow:inset 3px 0 0 rgba(70,120,190,.45)}'+
    '#flow .row.skmbusy{position:relative;opacity:.75}#flow .row.skmbusy::after{content:"";position:absolute;inset:0;pointer-events:none;'+
      'background:linear-gradient(90deg,transparent,rgba(70,120,190,.10),transparent);background-size:200% 100%;animation:skmsh 1.4s linear infinite}'+
    '@keyframes skmsh{from{background-position:200% 0}to{background-position:-200% 0}}'+
    '.skmghost .skmlock.skphdel{display:block;text-align:center;color:#9a6a62;font-size:12px;margin:2px 0}.skmghost .skmlock.skphdel del{color:#b0574c;text-decoration-thickness:2px;margin-left:6px}'+
    '#flow .row.skmold{background:rgba(190,60,50,.05)}#flow .row.skmold .main,#flow .row.skmold .anchor{text-decoration:line-through;text-decoration-color:rgba(190,60,50,.55);color:#8a5a55}'+
    '#skmbtn{position:fixed;z-index:60;display:none;padding:5px 14px;border-radius:16px;border:1px solid #2e5b8a;background:#2e5b8a;color:#fff;font:600 14px inherit;cursor:pointer;box-shadow:0 2px 8px rgba(0,0,0,.18)}'+
    '#skmbtn.dim{background:#8a98a8;border-color:#8a98a8}#skmtop.dim{opacity:.6}'+
    '#skmset{position:fixed;z-index:60;display:none;width:30px;height:30px;padding:0;border-radius:50%;border:1px solid #2e5b8a;background:#fff;color:#2e5b8a;font-size:16px;line-height:28px;cursor:pointer;box-shadow:0 2px 8px rgba(0,0,0,.15)}'+
    '.skmbar button.skmlink{border:none;background:none;text-decoration:underline;color:#4d5a4f;padding:3px 4px;margin-right:auto}'+
    '.skmghost{position:relative;margin:4px 0 10px;border:1px solid rgba(46,125,60,.35);background:rgba(46,125,60,.05);border-radius:6px;padding:6px 8px 4px}'+
    '.skmghost.skmbusy{opacity:.6}.skmghost.edit{background:#fff;border-color:#2e7d3c;box-shadow:0 0 0 2px rgba(46,125,60,.15)}'+
    '.skmrow{display:flex;gap:10px;margin:2px 0}.skmrail{flex:0 0 auto;min-width:3.4em;max-width:8em;text-align:left;font-size:.82em;color:#2e5d3a;font-weight:700;display:flex;flex-direction:column}'+
    '.skmmain{flex:1}.skmmain p{margin:0 0 2px;color:#1f4d2a}.skmmain p.in{padding-right:1.2em}.skmmain p.sp{margin-top:.6em}.skmmain p.nose,.skmhead{text-align:center;font-weight:700}'+
    '.skmhead{margin:4px 0;color:#1f4d2a}.skmlock{font-size:12px;color:#7a6a45;background:#f4ecd8;border-radius:4px;display:inline-block;padding:0 6px;margin:2px 0}.skmlock.skmhid,.skmsrc{display:none}'+
    '.skmghost i.am{font-weight:700}.skmghost i.hs{color:#5a6b78;font-size:.92em}.skmghost i.ps{font-style:italic}.skmghost i.b{font-weight:700}'+
    '.skmghost ins.skmadd,.skmghost ins.skmfix{text-decoration:underline;text-decoration-color:#e08a2c;text-decoration-thickness:2px;text-underline-offset:3px;background:rgba(224,138,44,.08)}'+
    '.skmghost i.tzc{font-style:normal;font-size:9px;line-height:1;vertical-align:super;color:#8a6d2b;background:#f6efdc;border-radius:6px;padding:0 3px;margin:0 1px;user-select:none;cursor:default}'+
    '.skmghost .skmsidehint{position:absolute;left:34px;bottom:4px;padding:1px 9px;border-radius:10px;border:1px solid #c9b27a;background:#fffaf0;color:#7a5a1a;font-size:12px;cursor:pointer;z-index:2}'+
    '.skmghost ins.skmadd::after,.skmghost ins.skmfix::after{content:"תוספת";font-size:10px;color:#b86b17;vertical-align:super;margin-right:2px}.skmghost ins.skmfix::after{content:"תיקון"}'+
    '.skmghost.edit ins::after{display:none}'+
    '.skmpoint{font-size:12.5px;color:#5d6b60;margin:0 0 4px;padding:0 0 3px;border-bottom:1px dotted rgba(46,125,60,.25);line-height:1.45}.skmpoint b{color:#2e5d3a;font-weight:600}'+
    '.skmghost [data-skm="new"]{background:rgba(250,214,80,.32);border-radius:2px}'+
    '.skmghost [data-skm="num"]{color:#a8801f;font-weight:700}'+
    '.skmghost [data-skm="moved"]{text-decoration:underline dashed;text-decoration-color:#6d8fb5;text-decoration-thickness:1.5px;text-underline-offset:3px}'+
    '.skmghost:focus{outline:none}.skmnote{color:#8a6a1f;font-size:12.5px}'+
    '.skmbar{display:flex;flex-wrap:wrap;align-items:center;gap:6px;margin-top:6px;padding-top:5px;border-top:1px dashed rgba(46,125,60,.3);font-size:14px}'+
    '.skmbar .skmt{font-weight:700;color:#2e5d3a;margin-left:6px}.skmbar button{padding:3px 12px;border-radius:12px;border:1px solid #2e7d3c;background:#fff;color:#2e5d3a;cursor:pointer}'+
    '.skmbar button[data-a="ok"]{background:#2e7d3c;color:#fff}.skmwarn{color:#a8452f;font-size:13px}.skmwhy{flex-basis:100%;font-size:13px;color:#4d5a4f}.skmwhy summary{cursor:pointer}.skmwhy ul{margin:3px 18px 0;padding:0}'+
    '.skmsb{border-color:#2e5b8a!important;color:#2e5b8a!important}.skmbox{max-width:640px}.skmsmall{font-size:12.5px;color:#6b604d}'+
    '@media print{.skmghost,#skmbtn{display:none!important}}';
    document.head.appendChild(s)})();
  if(isAdmin()&&admKey())setTimeout(()=>skmStat(),4000);
