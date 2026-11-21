  /* =================== סקירה פנימית בתוך הצעת סכם (פרומפט 75, 21.11.2026) ===================
     מיכאל: "צריך להוסיף כפתור ליד כפתור העריכה [העיפרון] שכשנכנסים אליו הוא עובד בתוך החלון הספציפי הזה
     תיקון אחרי תיקון - קבל, דחה או ערוך. וכך מהר מאוד אפשר לקבל חלק מהדברים ולדחות חלק."
     הכפתור (רשימת סימוני וי) יושב בעמודת הכפתורים מיד אחרי העיפרון; במגע (פרומפט 74: העמודה מוסתרת) - שורה בתחתית
     הכרטיס, ובזמן הסקירה הפנימית הסרגל התחתון של 74 מתחלף בסרגל היחידות (החלקה = יחידה הבאה/הקודמת). קיצור: S או Alt+ס.
     בתוך הכרטיס כל שינוי הוא יחידה (SKU.units, sakem_units_core.js). היחידה הנוכחית במסגרת דקה, בלי רקע.
     Enter קבל · ' דחה · E או Ctrl+Enter ערוך (Enter מסיים) · חץ ימינה/למטה הבא · חץ שמאלה/למעלה הקודם (כלשון ההוראה,
     וכמו ההחלקה במגע של פרומפט 74: ימינה = הבא) ·
     Ctrl+ז ביטול ההכרעה האחרונה · Esc (או הכפתור שוב) יציאה - ההכרעות נשמרות כטיוטה במכשיר וחוזרים לאותו מקום.
     Delete לעולם אינו דוחה. אחרי ההכרעה האחרונה הכרטיס מוחל כהכרעה אחת (התוצאה המעורבת, באותו מסלול של "קבל"),
     ועוברים לכרטיס הבא, עם "בטל" לכמה שניות. כל היחידות נדחו - דחיית הכרטיס. כל הכרעה ביחידה - בזיכרון ובמכשיר
     בלבד (מיידי, בלי בנייה ובלי שרת); השרת מקבל רק את ההכרעה על הכרטיס, ומן היומן שלו (orig, prop, final)
     הלמידה משחזרת כל יחידה (SKU.classify, tools/sakem/units_report.mjs). */
  const SKIU={on:false,it:null,M:null,V:[],dec:{},i:0,hist:[],ed:false,base:'',undo:null};
  const SKIU_LS='lg-skiu';
  const SKIU_ICON='<svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M1.5 3.5l1.2 1.2 2-2.2M1.5 8.5l1.2 1.2 2-2.2M1.5 13.2l1.2 1.2 2-2.2M7 3.6h7.5M7 8.6h7.5M7 13.4h7.5"/></svg>';
  function skiuAll(){try{return JSON.parse(localStorage.getItem(SKIU_LS)||'{}')||{}}catch(e){return {}}}
  function skiuKey(it){return (SKP.rev?SKP.rev.jid:'')+':'+(it?it.iid:'')}
  function skiuBase(it){
    /* בהתנגשות (הקטע נערך אצלך מאז ההצעה) - היחידות הן בין הנוסח שבדף עכשיו להצעה, ו"דחה" משאיר את שלך */
    if(SKP.rev&&SKP.rev.conflict){try{return skmInter(skmUnits(it.ids))}catch(e){}}
    return it.orig||''}
  function skiuDraft(it,base){const x=skiuAll()[skiuKey(it)];return x&&x.s===SKU.sig(base,it.text)?x:null}
  function skiuSave(){
    if(!SKIU.it)return;const A=skiuAll(),k=skiuKey(SKIU.it);
    if(Object.keys(SKIU.dec).length)A[k]={s:SKU.sig(SKIU.base,SKIU.it.text),d:SKIU.dec,i:SKIU.i,t:Date.now()};else delete A[k];
    const ks=Object.keys(A);if(ks.length>300)ks.sort((a,b)=>A[a].t-A[b].t).slice(0,ks.length-300).forEach(x=>delete A[x]);
    try{localStorage.setItem(SKIU_LS,JSON.stringify(A))}catch(e){}}
  function skiuDrop(it){const A=skiuAll();delete A[skiuKey(it)];try{localStorage.setItem(SKIU_LS,JSON.stringify(A))}catch(e){}}
  const skiuDone=()=>SKIU.V.filter(u=>SKIU.dec[u.id]!==undefined).length;
  const skiuState=d=>d===undefined?'':d==='a'?'התקבל':d==='r'?'נדחה':'נערך';

  /* ---- כניסה ויציאה ---- */
  function skiuOn(){
    const R=SKP.rev;if(!R)return;const it=R.items[R.i],g=SKM.ghost;
    if(!it||!g||it.kind!=='seg'){flash('סקירה פנימית - להצעת ליטוש בלבד');return}
    if(g.classList.contains('edit')){flash('סיים קודם את העריכה במקום');return}
    const base=skiuBase(it),M=SKU.units(base,it.text),V=M.u.filter(u=>!u.quiet);
    if(!V.length){flash('אין בהצעה הזאת שינויים להכרעה');return}
    const dr=skiuDraft(it,base);
    Object.assign(SKIU,{on:true,it,M,V,base,dec:dr?dr.d:{},hist:[],ed:false});
    SKIU.i=dr&&dr.i<V.length?dr.i:Math.max(0,V.findIndex(u=>SKIU.dec[u.id]===undefined));
    document.documentElement.classList.add('skiu');g.classList.add('skiu');
    skiuPaint(true);
    if(dr)toast('ממשיך מן הטיוטה: '+skiuDone()+' מתוך '+V.length+' הוכרעו',3000)}
  function skiuOff(reshow){
    if(!SKIU.on)return;skiuSave();SKIU.on=false;SKIU.ed=false;
    document.documentElement.classList.remove('skiu');const b=$('#skiubar');if(b)b.remove();
    try{document.documentElement.style.setProperty('--skpbarh',($('#skpbar')||{offsetHeight:40}).offsetHeight+'px')}catch(e){}
    if(reshow&&SKP.rev)skpShow()}
  function skiuToggle(){if(SKIU.on)skiuOff(true);else skiuOn()}

  /* ---- התצוגה: הנוסח המצטבר, היחידות שטרם הוכרעו כהצעה (נוסף/נמחק), הנוכחית במסגרת ----
     סימני עזר פרטיים בתוך נוסח הביניים, ואחרי skmGhostBody הם הופכים לתגיות (skiuMarks) */
  const SKIU_HS=0xE100,SKIU_HE='\uE00F',SKIU_ADD='\uE002',SKIU_ADDE='\uE003',SKIU_DEL='\uE004',SKIU_DELE='\uE005',SKIU_CHIP='\uE006',SKIU_FLD='\uE007',SKIU_DEC='\uE008';
  function skiuText(S){S=S||SKIU;
    const M=S.M,o=M.o,cur=S.V[S.i];let out='',pend='',q=0,ui=0;
    const wordish=t=>t.k==='word'||t.k==='ws';
    const em=(t,a,b)=>{if(wordish(t)){out+=pend+(a||'')+t.v+(b||'');pend=''}else out+=t.v};
    while(q<o.length){
      const u=M.u[ui];
      if(u&&q===u.s){
        const HS=String.fromCharCode(SKIU_HS+u.id),d=u.quiet?'a':S.dec[u.id],isCur=cur&&u.id===cur.id;
        if(isCur&&S.ed){pend+=HS+SKIU_FLD+SKIU_HE;q=u.e;ui++;continue}
        if(d===undefined){
          const vis=o.slice(u.s,u.e).some(x=>(x.t==='del'&&x.a.k==='word')||(x.t==='ins'&&x.b.k==='word'));
          if(!vis&&isCur)pend+=HS+SKIU_CHIP+SKIU_HE;
          for(let k=u.s;k<u.e;k++){const x=o[k];
            if(x.t==='eq')em(x.b,HS,SKIU_HE);
            else if(x.t==='del'){if(wordish(x.a))em(x.a,HS+SKIU_DEL,SKIU_DELE+SKIU_HE)}
            else{if(wordish(x.b))em(x.b,HS+SKIU_ADD,SKIU_ADDE+SKIU_HE);else out+=x.b.v}}}
        else{
          const ts=d==='a'?SKU.tokens(u.b):d==='r'?SKU.tokens(u.a):SKU.tokens(String(d.e));
          if(isCur&&!ts.some(wordish))pend+=HS+SKIU_CHIP+SKIU_HE;
          ts.forEach(t=>em(t,HS+SKIU_DEC,SKIU_HE))}
        q=u.e;ui++;continue}
      em(o[q].b);q++}
    return out+pend}
  function skiuMarks(body,S){S=S||SKIU;
    const tw=document.createTreeWalker(body,NodeFilter.SHOW_TEXT),nodes=[];let n;while((n=tw.nextNode()))nodes.push(n);
    let st={u:-1,a:0,d:0,k:0};const cur=S.V[S.i];
    nodes.forEach(tn=>{const s=tn.nodeValue;if(!/[\uE000-\uEFFF]/.test(s)&&st.u<0)return;
      const fr=document.createDocumentFragment();let buf='';
      const mk=(tag,cls)=>{const e=document.createElement(tag);e.className=cls;e.dataset.u=st.u;return e};
      const fl=()=>{if(!buf)return;if(st.u<0)fr.appendChild(document.createTextNode(buf));
        else{const e=mk(st.d?'del':st.a?'ins':'span','skiu'+(st.d?' d':'')+(st.a?' a':'')+(st.k?' k':''));e.textContent=buf;fr.appendChild(e)}buf=''};
      for(const ch of s){const c=ch.charCodeAt(0);
        if(c>=SKIU_HS&&c<=0xEFFF){fl();st.u=c-SKIU_HS;continue}
        if(c===0xE00F){fl();st={u:-1,a:0,d:0,k:0};continue}
        if(c===0xE002){fl();st.a=1;continue}if(c===0xE003){fl();st.a=0;continue}
        if(c===0xE004){fl();st.d=1;continue}if(c===0xE005){fl();st.d=0;continue}
        if(c===0xE008){fl();st.k=1;continue}
        if(c===0xE006){fl();const e=mk('span','skiu chip');e.contentEditable='false';
          const u=S.M.u[st.u];e.textContent=u?u.label:'שינוי';fr.appendChild(e);continue}
        if(c===0xE007){fl();const e=mk('span','skiu fld');fr.appendChild(e);continue}
        buf+=ch}
      fl();tn.replaceWith(fr)});
    if(cur)body.querySelectorAll('[data-u="'+cur.id+'"]').forEach(e=>e.classList.add('cur'))}
  function skiuPaint(scroll){
    const g=SKM.ghost;if(!SKIU.on||!g)return;
    const t0=performance.now();
    const body=g.querySelector('.skmbody');if(!body)return;
    body.innerHTML=skmGhostBody(skiuText(),'');
    skiuMarks(body);
    g.querySelectorAll('.skpconf.skiuerr').forEach(x=>x.remove());
    if(SKIU.ed)skiuField(body);
    skiuBar();
    SKIU.ms=Math.round(performance.now()-t0);
    const c=body.querySelector('.skiu.cur');
    if(c&&(scroll||SKIU.ed)){const r=c.getBoundingClientRect(),bh=($('#skpbar')||{offsetHeight:0}).offsetHeight;
      if(r.top<60||r.bottom>innerHeight-bh-10)c.scrollIntoView({block:'center',behavior:scroll==='jump'?'auto':'smooth'})}}

  /* ---- הסרגל: בתחתית המסך, בתוך סרגל הסקירה (תמיד מתחת לטקסט, לעולם לא מעליו) ---- */
  function skiuBar(){
    const tch=document.documentElement.classList.contains('tch'),sb=tch?document.documentElement:$('#skpbar');if(!sb)return;
    let b=$('#skiubar');
    if(!b){b=document.createElement('div');b.id='skiubar';b.dir='rtl';
      b.addEventListener('click',ev=>{const x=ev.target.closest('button');if(!x)return;ev.stopPropagation();skiuAct(x.dataset.k)})}
    if(b.parentNode!==sb)sb.appendChild(b);b.classList.toggle('fix',tch);
    const u=SKIU.V[SKIU.i],n=SKIU.V.length,dn=skiuDone(),d=u?SKIU.dec[u.id]:undefined,full=dn===n;
    b.innerHTML='<span class="skiuc"><b>סקירה פנימית</b> · <bdi>'+(SKIU.i+1)+' מתוך '+n+'</bdi>'+(u?' · '+esc(u.label)+(d!==undefined?' · <i>'+skiuState(d)+'</i>':''):'')+' · הוכרעו '+dn+'</span>'+
      '<span class="skiunav">'+
      '<button data-k="prev" title="היחידה הקודמת (חץ שמאלה או למעלה)">הקודם</button>'+
      '<button data-k="a" class="ok" title="קבל את השינוי הזה (Enter)">קבל</button>'+
      '<button data-k="r" class="no" title="דחה - החזר את הנוסח המקורי (\')">דחה</button>'+
      '<button data-k="e" title="ערוך את השינוי הזה בלבד (E או Ctrl+Enter), Enter מסיים">ערוך</button>'+
      '<button data-k="next" title="היחידה הבאה (חץ ימינה או למטה)">הבא</button></span>'+
      '<span class="skiurest">'+
      (full?'<button data-k="apply" class="ok" title="החל את התוצאה המעורבת על הקטע">החל את התוצאה</button>':
        '<button data-k="restA" title="קבל את כל מה שטרם הוכרע בכרטיס">קבל את כל השאר</button>'+
        '<button data-k="restR" title="דחה את כל מה שטרם הוכרע בכרטיס">דחה את כל השאר</button>')+
      '<button data-k="exit" title="יציאה - ההכרעות נשמרות כטיוטה (Esc)">יציאה</button></span>'+
      '<i style="width:'+Math.round(100*dn/Math.max(1,n))+'%"></i>';
    try{if(tch)document.documentElement.style.setProperty('--skiuh',b.offsetHeight+'px');else document.documentElement.style.setProperty('--skpbarh',sb.offsetHeight+'px')}catch(e){}}

  /* ---- ההכרעות ---- */
  function skiuNext(from){const V=SKIU.V,n=V.length;for(let k=1;k<=n;k++){const j=(from+k)%n;if(SKIU.dec[V[j].id]===undefined)return j}return -1}
  function skiuDecide(v){
    const u=SKIU.V[SKIU.i];if(!u)return;
    SKIU.hist.push({id:u.id,i:SKIU.i,prev:SKIU.dec[u.id]});
    SKIU.dec[u.id]=v;skiuSave();
    const nx=skiuNext(SKIU.i);
    if(nx<0){skiuPaint();skiuFinish();return}
    SKIU.i=nx;skiuPaint(true)}
  function skiuRest(v){const V=SKIU.V.filter(u=>SKIU.dec[u.id]===undefined);if(!V.length)return;
    SKIU.hist.push({many:V.map(u=>u.id),i:SKIU.i});V.forEach(u=>{SKIU.dec[u.id]=v});skiuSave();skiuPaint();skiuFinish()}
  function skiuUndoOne(){const h=SKIU.hist.pop();if(!h){flash('אין הכרעה לבטל');return}
    if(h.many)h.many.forEach(id=>delete SKIU.dec[id]);else if(h.prev===undefined)delete SKIU.dec[h.id];else SKIU.dec[h.id]=h.prev;
    SKIU.i=h.i;skiuSave();skiuPaint(true)}
  function skiuGo(dir){const n=SKIU.V.length;if(!n)return;SKIU.ed=false;SKIU.i=(SKIU.i+dir+n)%n;skiuSave();skiuPaint(true)}
  /* עריכה של היחידה הזו בלבד: שדה קטן במקומה, בנוסח הביניים של היחידה (Enter מסיים, Esc מבטל) */
  function skiuEdit(){if(!SKIU.V[SKIU.i])return;SKIU.ed=true;skiuPaint(true)}
  function skiuField(body){
    const u=SKIU.V[SKIU.i],ph=body.querySelector('.skiu.fld');if(!u||!ph)return;
    const d=SKIU.dec[u.id],v=d&&typeof d==='object'?String(d.e):d==='r'?u.a:u.b;
    const multi=/\n/.test(v)||v.length>70;
    const f=document.createElement(multi?'textarea':'input');f.className='skiufld';f.value=v;f.dir='rtl';f.spellcheck=false;
    if(!multi)f.size=Math.max(4,Math.min(60,v.length+2));else f.rows=Math.min(6,v.split('\n').length+1);
    f.title='עריכת השינוי הזה בלבד · Enter מסיים · Esc מבטל';
    ph.replaceWith(f);
    ['keyup','input','beforeinput','keypress'].forEach(t=>f.addEventListener(t,ev=>ev.stopPropagation()));
    setTimeout(()=>{try{f.focus({preventScroll:true});f.setSelectionRange(f.value.length,f.value.length)}catch(e){}},0)}
  function skiuFieldDone(f){
    const u=SKIU.V[SKIU.i];if(!u)return;let v=f.value;
    if(!multiOk(v)){flash('הסוגריים המסולסלים בעריכה אינם מאוזנים');return}
    if(f.tagName==='INPUT')v=v.replace(/\n/g,' ');
    SKIU.ed=false;skiuDecide(v===u.b?'a':v===u.a?'r':{e:v})}
  function multiOk(v){let d=0;for(const t of SKU.tokens(v)){if(t.k==='open')d++;else if(t.k==='close'&&--d<0)return false}return d===0}
  function skiuAct(k){
    if(!SKIU.on)return;
    if(SKIU.ed&&k!=='e'){const f=$('.skiufld');if(f&&(k==='a'))return skiuFieldDone(f);SKIU.ed=false}
    ({a:()=>skiuDecide('a'),r:()=>skiuDecide('r'),e:skiuEdit,next:()=>skiuGo(1),prev:()=>skiuGo(-1),
      restA:()=>skiuRest('a'),restR:()=>skiuRest('r'),apply:skiuFinish,exit:()=>skiuOff(true)}[k]||(()=>{}))()}

  /* ---- החלת הכרטיס: הכרעה אחת על הקטע כולו ---- */
  function skiuFinish(){
    const R=SKP.rev,it=SKIU.it;if(!R||!it||R.items[R.i]!==it){skiuOff(false);return}
    if(skiuDone()<SKIU.V.length){skiuPaint();return}
    const vis=SKIU.V,allR=vis.every(u=>SKIU.dec[u.id]==='r'),allA=vis.every(u=>SKIU.dec[u.id]==='a');
    const text=SKU.compose(SKIU.M,SKIU.dec),key=skiuKey(it),snap={key,v:skiuAll()[key],iid:it.iid,jid:R.jid};
    const n=vis.length,na=vis.filter(u=>SKIU.dec[u.id]==='a').length,nr=vis.filter(u=>SKIU.dec[u.id]==='r').length;
    const hist0=R.hist.length;
    SKIU.on=false;SKIU.ed=false;document.documentElement.classList.remove('skiu');const bb=$('#skiubar');if(bb)bb.remove();
    const back=why=>{
      /* לא הוחל (השומר, או אישור שורה שננעלה בהדפסה - "לחץ שוב"): נשארים בסקירה הפנימית, וההכרעות אינן אובדות */
      if(R.items[R.i]!==it||!SKM.ghost)return;
      SKIU.on=true;document.documentElement.classList.add('skiu');SKM.ghost.classList.add('skiu');skiuPaint();
      const m=document.createElement('div');m.className='skpconf skiuerr';m.textContent=why;
      const ch=SKM.ghost.querySelector('.skpchips');if(ch)ch.after(m);else SKM.ghost.prepend(m)};
    if(allR){skpReject();if(R.hist.length>hist0)skiuDrop(it)}
    else if(allA){skpAccept(R.conflict);if(R.hist.length>hist0)skiuDrop(it);else back('לא הוחל. קרא את ההודעה, ולחץ "החל את התוצאה" שוב לאישור')}
    else{
      let orig;if(R.conflict)orig=skmInter(skmUnits(it.ids));
      let r;try{r=skpApplyOne(it,text,orig)}catch(e){
        /* השומר חסם את הצירוף (למשל נעול שזז): נשארים בסקירה הפנימית, וההכרעות אינן אובדות */
        back('הצירוף הזה לא הוחל: '+(e.message||e)+'. שנה הכרעה באחת היחידות, ערוך אותה, או לחץ "החל את התוצאה" שוב');
        flash('לא הוחל: '+(e.message||e));return}
      skiuDrop(it);skmClose(true);
      R.cnt.edit++;R.hist.push({i:R.i,iid:it.iid,act:'edit',undo:r.n>0});
      skpDec(it,'edit',{final:text});
      skpMove(1)}
    if(R.hist.length>hist0){
      SKIU.undo=snap;const hh=R.hist[R.hist.length-1];
      skpAllToast(allR?'כל השינויים נדחו - הקטע נדחה':allA?'כל השינויים התקבלו':'הוחל: התקבלו '+na+', נדחו '+nr+(n-na-nr?', נערכו '+(n-na-nr):'')+' מתוך '+n,()=>{
        const A=skiuAll();if(snap.v)A[snap.key]=snap.v;try{localStorage.setItem(SKIU_LS,JSON.stringify(A))}catch(e){}
        SKIU.reopen=snap.iid;
        if(SKP.rev&&SKP.rev.jid===snap.jid){skpUndo();return}
        /* הכרטיס היה האחרון בתור והסקירה נסגרה: מחזירים את הדף, מבטלים את ההכרעה בשרת, ופותחים אותו שוב */
        if(hh&&hh.undo&&!undoLast())flash('השינוי לא בוטל בדף - בטל בעורך');
        skpDec(it,'undo',null,{jid:snap.jid,dec:{}});
        Promise.resolve(window.skpDecIdle&&skpDecIdle()).then(()=>{try{skpEmptySet(snap.jid,0)}catch(e){}skpOpen(snap.jid)})})}}

  /* ---- חיבור לסקירה הקיימת ---- */
  {const sh=skpShow;skpShow=function(){
    if(SKIU.on){skiuSave();SKIU.on=false;SKIU.ed=false;document.documentElement.classList.remove('skiu')}
    const r=sh.apply(this,arguments);
    try{skiuButtons()}catch(e){try{console.warn('skiu',e)}catch(_){}}
    try{const R=SKP.rev,it=R&&R.items[R.i];if(it&&SKIU.reopen===it.iid){SKIU.reopen=null;skiuOn()}}catch(e){}
    return r}}
  {const sb=skpBar;skpBar=function(){const r=sb.apply(this,arguments);try{skiuButtons();if(SKIU.on)skiuBar()}catch(e){}return r}}
  function skiuButtons(){
    const R=SKP.rev,g=SKM.ghost;if(!R||!g)return;const it=R.items[R.i];if(!it||it.kind!=='seg')return;
    const dr=skiuDraft(it,skiuBase(it)),badge=dr?' <bdi class="skiubdg">'+Object.keys(dr.d).length+'</bdi>':'';
    const side=g.querySelector('.skpside');
    if(side&&!side.querySelector('.skiubtn')){const b=document.createElement('button');b.type='button';b.className='skiubtn';
      b.title='סקירה פנימית: קבל/דחה כל שינוי (S)';b.setAttribute('aria-label','קבל/דחה כל שינוי');b.innerHTML=SKIU_ICON;
      b.addEventListener('click',ev=>{ev.stopPropagation();skiuToggle()});
      const ed=side.querySelector('[data-a="edit"]');if(ed)ed.after(b);else side.appendChild(b)}
    const sb=$('#skpbar'),nav=sb&&(sb.querySelector('.skpnav')||sb);
    if(nav){let t=nav.querySelector('.skiutouch');
      if(!t){t=document.createElement('button');t.type='button';t.className='skiutouch';t.title='סקירה פנימית: קבל/דחה כל שינוי (S)';
        t.addEventListener('click',ev=>{ev.stopPropagation();skiuToggle()});
        const ed=nav.querySelector('[data-a="edit"]');if(ed)ed.after(t);else nav.appendChild(t)}
      t.innerHTML=SKIU_ICON+' <span>כל שינוי</span>'+badge}
    /* במגע (פרומפט 74) העמודה שבצד והסרגל המקורי מוסתרים: שורה קטנה בתחתית הכרטיס */
    let ib=g.querySelector('.skiuin');
    if(!ib){ib=document.createElement('button');ib.type='button';ib.className='skiuin';ib.contentEditable='false';ib.title='סקירה פנימית: קבל/דחה כל שינוי (S)';
      ib.addEventListener('click',ev=>{ev.stopPropagation();skiuToggle()});g.appendChild(ib)}
    ib.innerHTML=SKIU_ICON+' <span>קבל/דחה כל שינוי</span>'+badge}
  /* לחיצה (או נגיעה) על שינוי בנוסח - הוא נעשה הנוכחי */
  document.addEventListener('click',ev=>{
    if(!SKIU.on||SKIU.ed)return;const e=ev.target.closest&&ev.target.closest('.skmghost.skiu [data-u]');if(!e)return;
    const id=+e.dataset.u,k=SKIU.V.findIndex(u=>u.id===id);if(k<0)return;ev.preventDefault();ev.stopPropagation();SKIU.i=k;skiuPaint()},true);
  /* המקלדת: לפני הסקירה ולפני העורך (שלב הלכידה על window) */
  window.addEventListener('keydown',e=>{
    const R=SKP.rev;if(!R)return;const g=SKM.ghost;
    const k=e.key,c=e.code,stop=()=>{e.preventDefault();e.stopImmediatePropagation()};
    const other=e.target&&e.target.closest&&e.target.closest('input,textarea,select,.modal,#skptagm')&&!(e.target.classList&&e.target.classList.contains('skiufld'));
    const entry=!e.ctrlKey&&!e.metaKey&&((!e.altKey&&!e.shiftKey&&c==='KeyS')||(e.altKey&&(k==='ס'||c==='KeyX')));
    if(!SKIU.on){
      if(entry&&g&&!g.classList.contains('edit')&&!other&&R.items[R.i]&&R.items[R.i].kind==='seg'){stop();skiuOn()}
      return}
    if(SKIU.ed){const f=e.target.classList&&e.target.classList.contains('skiufld')?e.target:null;
      if(k==='Escape'){stop();SKIU.ed=false;skiuPaint();return}
      if(f&&k==='Enter'&&!e.shiftKey){stop();skiuFieldDone(f);return}
      if(f){e.stopImmediatePropagation();return}
      /* המיקוד יצא מן השדה: שום מקש אינו מגיע לסקירה הרגילה (Enter שם מקבל את כל הכרטיס) */
      if(k==='Enter'||c==='Quote'||c==='KeyE'||/^Arrow/.test(k)){stop();const ff=$('.skiufld');if(ff)ff.focus()}
      return}
    if(other)return;
    if(!g||!g.classList.contains('skiu')){skiuOff(false);return}
    if(e.ctrlKey&&!e.altKey&&c==='KeyZ'){stop();skiuUndoOne();return}
    if(e.ctrlKey&&!e.altKey&&k==='Enter'){stop();skiuEdit();return}
    if(entry||k==='Escape'){stop();skiuOff(true);return}
    if(e.ctrlKey||e.altKey||e.metaKey)return;
    if(k==='Enter'){stop();skiuDecide('a')}
    else if(c==='Quote'){stop();skiuDecide('r')}
    else if(c==='KeyE'){stop();skiuEdit()}
    else if(k==='ArrowRight'||k==='ArrowDown'){stop();skiuGo(1)}
    else if(k==='ArrowLeft'||k==='ArrowUp'){stop();skiuGo(-1)}},true);
  /* מגע בזמן הסקירה הפנימית: החלקה = יחידה הבאה/הקודמת (ימינה = הבא, כמו ב-74), ושום מחווה אינה מגיעה לסקירה
     הרגילה (שם החלקה עוברת כרטיס והקשה כפולה פותחת עריכה של הכרטיס כולו) */
  let skiuX=null,skiuY=0,skiuT=0;
  window.addEventListener('touchstart',e=>{if(!SKIU.on||e.touches.length!==1){skiuX=null;return}skiuX=e.touches[0].clientX;skiuY=e.touches[0].clientY;skiuT=Date.now()},{passive:true,capture:true});
  window.addEventListener('touchend',e=>{
    if(!SKIU.on||skiuX==null)return;const X=e.changedTouches[0].clientX,Y=e.changedTouches[0].clientY,dx=X-skiuX,dy=Y-skiuY,dt=Date.now()-skiuT;skiuX=null;
    if(e.target.closest&&e.target.closest('#skiubar,.skiufld,#tchsheet'))return;
    e.stopPropagation();
    if(dt<650&&Math.abs(dx)>70&&Math.abs(dy)<50&&Math.abs(dx)>2*Math.abs(dy))skiuGo(dx>0?1:-1)},{passive:true,capture:true});
  window.skiuTest={on:skiuOn,off:skiuOff,act:skiuAct,state:()=>SKIU.on?{i:SKIU.i,n:SKIU.V.length,done:skiuDone(),ms:SKIU.ms,dec:Object.assign({},SKIU.dec),
    units:SKIU.V.map(u=>({id:u.id,kind:u.kind,a:u.a,b:u.b})),text:SKU.compose(SKIU.M,SKIU.dec)}:null};

  /* =================== פרומפט 75 ה: אותה סקירה פנימית בשורה אחת ===================
     הצעת מציע מן העורך ("הצע תיקון") שיש בה יותר משינוי אחד, והצעת "שורה שהתארכה" (קיצור נוסח) שיש בה כמה
     שינויים: כפתור "קבל/דחה כל שינוי" ליד כפתורי ההצעה. השורה נפרקת ליחידות באותו מנוע (SKU) על נוסח הביניים
     של השורה (SKC.h2i), ובסוף התוצאה המעורבת עוברת בדיוק במסלול של "אשר" / "קבל" הקיים, כנוסח ההצעה. */
  const SKIM={S:null};
  function skimOn(host,o){
    const M=SKU.units(o.orig,o.text),V=M.u.filter(u=>!u.quiet);if(V.length<2)return false;
    SKIM.S={M,V,i:0,dec:{},ed:false,host,o};document.documentElement.classList.add('skium-on');skimPaint();return true}
  function skimOff(){SKIM.S=null;document.documentElement.classList.remove('skium-on')}
  function skimPaint(){
    const S=SKIM.S;if(!S)return;const h=S.host;if(!h.isConnected){skimOff();return}
    const n=S.V.length,dn=S.V.filter(u=>S.dec[u.id]!==undefined).length,u=S.V[S.i],d=u?S.dec[u.id]:undefined;
    h.innerHTML='<div class="skimt" dir="rtl"></div><div class="skimb" dir="rtl"><span class="skiuc"><bdi>'+(S.i+1)+' מתוך '+n+'</bdi>'+(u?' · '+esc(u.label)+(d!==undefined?' · <i>'+skiuState(d)+'</i>':''):'')+'</span>'+
      '<button type="button" data-k="prev" title="הקודם (חץ שמאלה)">הקודם</button><button type="button" data-k="a" class="ok" title="קבל (Enter)">קבל</button>'+
      '<button type="button" data-k="r" class="no" title="דחה (\')">דחה</button><button type="button" data-k="e" title="ערוך (E), Enter מסיים">ערוך</button>'+
      '<button type="button" data-k="next" title="הבא (חץ ימינה)">הבא</button>'+
      '<button type="button" data-k="restA">קבל את כל השאר</button><button type="button" data-k="restR">דחה את כל השאר</button><button type="button" data-k="x" title="חזרה להצעה כולה (Esc)">ביטול</button></div>';
    const t=h.querySelector('.skimt');t.innerHTML=SKC.i2h(skiuText(S),true).replace(/\n/g,'<br>');
    skiuMarks(t,S);
    if(S.ed){const ph=t.querySelector('.skiu.fld');if(ph){const v=d&&typeof d==='object'?String(d.e):d==='r'?u.a:u.b;
      const f=document.createElement('input');f.className='skiufld';f.dir='rtl';f.value=v;f.size=Math.max(4,Math.min(60,v.length+2));ph.replaceWith(f);
      setTimeout(()=>{try{f.focus();f.setSelectionRange(v.length,v.length)}catch(e){}},0)}}
    h.querySelectorAll('.skimb button').forEach(b=>{b.addEventListener('mousedown',e=>e.preventDefault());b.onclick=e=>{e.stopPropagation();skimAct(b.dataset.k)}});
    t.onclick=e=>{const x=e.target.closest('[data-u]');if(!x||S.ed)return;const k=S.V.findIndex(q=>q.id===+x.dataset.u);if(k>-1){S.i=k;skimPaint()}}}
  function skimAct(k){
    const S=SKIM.S;if(!S)return;const n=S.V.length,u=S.V[S.i];
    if(k==='x'){const c=S.o.cancel;skimOff();if(c)c();return}
    if(k==='next'||k==='prev'){S.ed=false;S.i=(S.i+(k==='next'?1:-1)+n)%n;skimPaint();return}
    if(k==='e'){S.ed=true;skimPaint();return}
    if(k==='restA'||k==='restR'){S.V.forEach(q=>{if(S.dec[q.id]===undefined)S.dec[q.id]=k==='restA'?'a':'r'})}
    else if(k==='a'||k==='r'||k==='fld'){
      if(k==='fld'){const f=S.host.querySelector('.skiufld');if(!f)return;const v=f.value.replace(/\n/g,' ');
        if(!multiOk(v)){flash('הסוגריים המסולסלים בעריכה אינם מאוזנים');return}S.dec[u.id]=v===u.b?'a':v===u.a?'r':{e:v};S.ed=false}
      else S.dec[u.id]=k;
      for(let j=1;j<=n;j++){const q=(S.i+j)%n;if(S.dec[S.V[q].id]===undefined){S.i=q;break}}}
    if(S.V.some(q=>S.dec[q.id]===undefined)){skimPaint();return}
    const mix=SKU.compose(S.M,S.dec),st={n,a:S.V.filter(q=>S.dec[q.id]==='a').length,r:S.V.filter(q=>S.dec[q.id]==='r').length};st.e=n-st.a-st.r;
    const done=S.o.done;skimOff();done(mix,st)}
  /* תור ההצעות (suggest_ui.js): הצעה מן העורך על שורה אחת */
  function skiuSqPair(g,s){
    const E=g&&g.edit;if(!E||E.op==='struct'||!s)return null;
    try{const bh=E.bh!==undefined?E.bh:s.h,nh=E.nowH!==undefined?E.nowH:esc(E.now||'');
      const o=SKC.h2i(bh).replace(/\s+/g,' ').trim(),t=SKC.h2i(nh).replace(/\s+/g,' ').trim();
      return SKU.units(o,t).u.filter(u=>!u.quiet).length>=2?{o,t}:null}catch(e){return null}}
  if(typeof sqRow==='function'){const r0=sqRow;sqRow=function(g,s){let h=r0.apply(this,arguments);
    try{if(skiuSqPair(g,s))h=h.replace('<details class="sgmore">','<button class="skiusq" title="קבל/דחה כל שינוי בהצעה בנפרד" onclick="skiuSq(\''+esc(g.id)+'\')">'+SKIU_ICON+' כל שינוי</button><details class="sgmore">')}catch(e){}
    return h}}
  window.skiuSq=function(id){
    const g=(typeof QQ!=='undefined'?QQ:[]).find(x=>x.id===id),row=document.querySelector('#sgqb .sgrow[data-id="'+(window.CSS&&CSS.escape?CSS.escape(id):id)+'"]');if(!g||!row)return;
    const s=sqLocate?sqLocate(g,slotsFull()):null;const P=skiuSqPair(g,s);if(!P){flash('אין בהצעה הזאת יותר משינוי אחד');return}
    const host=document.createElement('div');host.className='skimhost';const act=row.querySelector('.sgact');(act||row).before(host);
    row.classList.add('skimrow');
    skimOn(host,{orig:P.o,text:P.t,cancel:()=>{row.classList.remove('skimrow');drawSq()},
      done:async(mix,st)=>{row.classList.remove('skimrow');
        if(st.r===st.n){await sqDecide(id,'rejected','');return}
        if(st.a===st.n){await sqDecide(id,'accepted');return}
        const E0=g.edit,h=SKC.i2h(mix);g.edit=Object.assign({},E0,{nowH:h,now:SKC.bare(h)});
        try{await sqDecide(id,'edited')}finally{if(QQ.find(x=>x.id===id))g.edit=E0}
        toast('הוחל: התקבלו '+st.a+', נדחו '+st.r+(st.e?', נערכו '+st.e:'')+' מתוך '+st.n,4000)}})};
  /* שורה שהתארכה (overflow_ui.js): הצעת קיצור (replace) שיש בה כמה שינויים */
  if(typeof ovDraw==='function'){const d0=ovDraw;ovDraw=function(){const r=d0.apply(this,arguments);
    try{const it=OVS.cur,s=it&&it.sug[OVS.alt],d=OVS.pop;
      if(it&&s&&!it.head&&s.kind==='replace'&&s.html&&d){
        const o=SKC.h2i(it.html).replace(/\s+/g,' ').trim(),t=SKC.h2i(s.html).replace(/\s+/g,' ').trim();
        if(SKU.units(o,t).u.filter(u=>!u.quiet).length>=2){const bs=d.querySelector('.ovbtns'),ok=bs&&bs.querySelector('[data-a="ok"]');
          if(bs){const b=document.createElement('button');b.type='button';b.className='skiuov';b.title='קבל/דחה כל שינוי בהצעה בנפרד';b.innerHTML=SKIU_ICON+' כל שינוי';
            b.addEventListener('mousedown',e=>e.preventDefault());
            b.onclick=()=>{const host=d.querySelector('.ovbody');d.classList.add('skimpop');
              skimOn(host,{orig:o,text:t,cancel:()=>{d.classList.remove('skimpop');ovDraw()},
                done:(mix,st)=>{d.classList.remove('skimpop');
                  if(st.r===st.n){ovAct('leave');return}
                  if(st.a===st.n){ovAct('ok');return}
                  const z={tool:s.tool,kind:'replace',html:SKC.i2h(mix)};
                  try{const n=ovApply(it,z);ovSend(it,'edit',{now:ovNow(z),rs:'units'});ovMark();ovGo(ovFollow(it));flash('הוחל ('+n+'): התקבלו '+st.a+', נדחו '+st.r+' · Ctrl+ז מבטל')}
                  catch(e){flash('לא הוחל: '+(e.message||e));ovDraw()}}})};
            if(ok)ok.after(b);else bs.prepend(b)}}}}catch(e){}
    return r}}
  window.addEventListener('keydown',e=>{
    const S=SKIM.S;if(!S)return;if(!S.host.isConnected){skimOff();return}
    const k=e.key,c=e.code,stop=()=>{e.preventDefault();e.stopImmediatePropagation()};
    const inF=e.target.classList&&e.target.classList.contains('skiufld');
    if(S.ed){if(k==='Escape'){stop();S.ed=false;skimPaint()}else if(inF&&k==='Enter'){stop();skimAct('fld')}else if(inF)e.stopImmediatePropagation();return}
    if(e.target.closest&&e.target.closest('input,textarea,select')&&!inF)return;
    if(e.altKey||e.metaKey)return;
    if(e.ctrlKey){if(k==='Enter'){stop();skimAct('e')}return}
    if(k==='Enter'){stop();skimAct('a')}else if(c==='Quote'){stop();skimAct('r')}else if(c==='KeyE'){stop();skimAct('e')}
    else if(k==='ArrowRight'||k==='ArrowDown'){stop();skimAct('next')}else if(k==='ArrowLeft'||k==='ArrowUp'){stop();skimAct('prev')}
    else if(k==='Escape'){stop();skimAct('x')}
    else if(/^Key[ADSR]$/.test(c))stop()},true);
  window.skimTest={on:skimOn,act:skimAct,state:()=>SKIM.S?{i:SKIM.S.i,n:SKIM.S.V.length,dec:Object.assign({},SKIM.S.dec)}:null};

  (function(){const s=document.createElement('style');s.textContent=
    '.skpside button.skiubtn{display:flex;align-items:center;justify-content:center;color:#2e5b8a}'+
    'html.skiu .skpside button.skiubtn{background:#2e5b8a;color:#fff;border-color:#2e5b8a}'+
    '.skiutouch{display:none}.skiubdg{font-size:11px;color:#2e7d3c;font-weight:700}'+
    '.skmghost.skiu .skiu.a{background:rgba(250,214,80,.28);border-radius:2px;text-decoration:none}'+
    '.skmghost.skiu .skiu.d{color:#9a9a9a;text-decoration:line-through;text-decoration-thickness:1px;font-size:.9em}'+
    '.skmghost.skiu .skiu.cur{outline:1.5px solid #2e5b8a;outline-offset:1px;border-radius:2px;-webkit-box-decoration-break:clone;box-decoration-break:clone}'+
    '.skmghost.skiu [data-u]{cursor:pointer}'+
    /* במגע - כמו בסכם של פרומפט 74: הנוסף מודגש בלי רקע מרקר */
    'html.tch .skmghost.skiu .skiu.a{background:none;font-weight:700;color:#1f4a6e}'+
    '.skmghost.skiu .skiu.chip{display:inline-block;font-size:10.5px;line-height:1.4;padding:0 6px;margin:0 2px;border-radius:8px;background:#eef1f4;color:#4d5a66;vertical-align:middle;font-weight:400}'+
    '.skmghost.skiu .skiufld{font:inherit;font-size:.95em;border:1px solid #2e5b8a;border-radius:3px;padding:0 4px;background:#fff;max-width:100%;vertical-align:baseline}'+
    '.skmghost.skiu textarea.skiufld{display:block;width:100%;box-sizing:border-box}'+
    'html.skiu #skpbar .skpnav{display:none}'+
    '#skiubar{flex-basis:100%;display:flex;flex-wrap:wrap;gap:6px 10px;align-items:center;position:relative;padding-top:4px;border-top:1px solid #e3e8ed}'+
    '#skiubar .skiuc{color:#3d4a55}#skiubar .skiuc b{color:#2e5b8a}#skiubar .skiuc i{font-style:normal;color:#2e7d3c}'+
    '#skiubar .skiunav,#skiubar .skiurest{display:flex;gap:6px;flex-wrap:wrap}#skiubar .skiunav{margin-inline-start:auto}'+
    '#skiubar button{padding:2px 12px;border-radius:10px;border:1px solid #c9d3dc;background:#fff;color:#2e5b8a;font-size:13px;cursor:pointer}'+
    '#skiubar button.ok{background:#2e7d3c;border-color:#2e7d3c;color:#fff}#skiubar button.no{color:#a8452f;border-color:#a8452f}'+
    '#skiubar>i{position:absolute;top:-1px;right:0;height:2px;background:#2e5b8a}'+
    '@media (max-width:820px),(pointer:coarse){.skiutouch{display:inline-flex;align-items:center;justify-content:center;gap:4px}'+
      '#skiubar .skiunav,#skiubar .skiurest{flex-basis:100%;margin:0}#skiubar .skiunav button,#skiubar .skiurest button{flex:1;font-size:15px;padding:10px 0;border-radius:10px;min-height:44px}'+
      '#skiubar .skiuc{flex-basis:100%;text-align:center}}'+
    '.skiuin{display:none}html.tch-skp .skmghost .skiuin{display:flex;align-items:center;gap:6px;margin:8px 0 2px;min-height:44px;padding:4px 14px;border:1px solid #b6c8dc;border-radius:12px;background:#fff;color:#2e5b8a;font:600 14px system-ui,sans-serif;cursor:pointer}'+
    'html.skiu .skmghost .skiuin{display:none!important}'+
    'html.skiu #tchbar,html.skiu #tchundo{display:none!important}'+
    '#skiubar.fix{position:fixed;left:0;right:0;bottom:var(--tchkb,0px);z-index:91;margin:0;padding:6px 8px calc(6px + env(safe-area-inset-bottom));background:rgba(250,249,246,.98);border-top:1px solid #d9d4c8;box-shadow:0 -2px 10px rgba(0,0,0,.06);font:14px system-ui,sans-serif}'+
    '#skiubar.fix .skiuc{flex-basis:100%;text-align:center}#skiubar.fix .skiunav,#skiubar.fix .skiurest{flex-basis:100%;margin:0}'+
    '#skiubar.fix button{flex:1;min-height:48px;font-size:15px;border-radius:12px}#skiubar.fix .skiurest button{min-height:40px;font-size:14px}'+
    'html.skiu.tchrev body{padding-bottom:calc(var(--skiuh,150px) + 12px)!important}'+
    '.skimhost{margin:6px 0;padding:6px 8px;border:1px solid #c9d3dc;border-radius:10px;background:#fff}.skimt{line-height:1.9;margin-bottom:4px}'+
    '.skimt .skiu.a{background:rgba(250,214,80,.28);border-radius:2px;text-decoration:none}.skimt .skiu.d{color:#9a9a9a;text-decoration:line-through;font-size:.9em}'+
    '.skimt .skiu.cur{outline:1.5px solid #2e5b8a;outline-offset:1px;border-radius:2px}.skimt [data-u]{cursor:pointer}'+
    '.skimt .skiu.chip{display:inline-block;font-size:10.5px;padding:0 6px;margin:0 2px;border-radius:8px;background:#eef1f4;color:#4d5a66}'+
    '.skimt .skiufld{font:inherit;border:1px solid #2e5b8a;border-radius:3px;padding:0 4px}'+
    '.skimb{display:flex;flex-wrap:wrap;gap:6px;align-items:center;font-size:12.5px}.skimb .skiuc{color:#3d4a55;margin-inline-end:auto}.skimb .skiuc i{font-style:normal;color:#2e7d3c}'+
    '.skimb button{padding:2px 10px;border-radius:10px;border:1px solid #c9d3dc;background:#fff;color:#2e5b8a;font-size:13px;cursor:pointer}'+
    '.skimb button.ok{background:#2e7d3c;border-color:#2e7d3c;color:#fff}.skimb button.no{color:#a8452f;border-color:#a8452f}'+
    '.sgrow.skimrow .sqba,.sgrow.skimrow .sgact{display:none}.ovpop.skimpop .ovbtns,.ovpop.skimpop .ovkeys{display:none}'+
    'button.skiusq,button.skiuov{display:inline-flex;align-items:center;gap:4px}'+
    'html.skium-on #tchbar,html.skium-on #tchundo{display:none!important}'+
    '@media (pointer:coarse){.skimb button{min-height:44px;font-size:15px;flex:1 1 30%}}'+
    '@media print{#skiubar,.skiubtn,.skiutouch,.skiuin,.skimhost{display:none!important}}';
    document.head.appendChild(s)})();
