  /* =================== הצע כותרת (12.10.2026, לווקר) ===================
     כפתור "הצע כותרת" בחלונית הצפה של עיטור (***), ובחלונית הסגנונות ליד המילה (Ctrl+Alt+K), למנהל בלבד.
     לחיצה מציגה מיד שלוש הצעות לכותרת על הקטע שאחרי המקום. מקורן בשכבה מוכנה מראש
     (titlesug-<מסכת>.json, נבנית בהרצה מרוכזת), ו"עוד הצעות" מציג את שלוש הנוספות מאותה שכבה.
     אין הצעה מוכנה, או שאזלו: קריאה חיה לשרת ההצעות (POST /title), שבו המפתח שמור כסוד.
     בחירה: עיטור הופך לכותרת (נושא או ד"ה משנה), ושורה רגילה מקבלת כותרת נושא לפניה עם "רווח לפני".
     הכותרת מסומנת "ניסוח קלוד" (חום, למנהל בלבד), ונרשמות גם ההצעה וגם הנוסח הסופי (cl). */
  (function(){
    const st=document.createElement('style');st.textContent=
    '#tspop{position:fixed;z-index:70;width:340px;max-width:calc(100vw - 16px);background:#0f263b;color:#f5edd6;border:1px solid #d1a23a;border-radius:12px;'+
      'box-shadow:0 10px 30px rgba(0,0,0,.42);font-family:var(--ui,\'Vilna\',serif);direction:rtl;padding:6px 8px 8px}'+
    '#tspop .tsh{display:flex;align-items:center;gap:8px;padding:4px 4px 6px;border-bottom:1px solid rgba(209,162,58,.35)}'+
    '#tspop .tsh b{flex:1;color:#f9e08a;font-size:17px;font-weight:700}'+
    '#tspop button{font:inherit;cursor:pointer;color:#f5edd6;background:transparent;border:1px solid rgba(209,162,58,.45);border-radius:8px;padding:3px 10px;min-height:32px}'+
    '#tspop button:hover{background:rgba(233,195,90,.16)}'+
    '#tspop button.on{background:rgba(233,195,90,.28);color:#fff3c4;border-color:#f9e08a}'+
    '#tspop .tsx{border:0;font-size:20px;line-height:1;padding:2px 8px}'+
    '#tspop .tsty{display:flex;gap:6px;padding:6px 2px 2px}'+
    '#tspop .tsty button{flex:1;font-size:14px}'+
    '#tspop .tsr{display:flex;align-items:center;gap:10px;width:100%;text-align:right;margin-top:6px;font-size:18px;min-height:42px;padding:6px 10px}'+
    '#tspop .tsr b{flex:none;width:22px;height:22px;border-radius:50%;background:#d1a23a;color:#2b2620;font-size:14px;display:flex;align-items:center;justify-content:center}'+
    '#tspop .tsr span{flex:1}'+
    '#tspop .tsmsg{padding:14px 8px;text-align:center;color:#c9bf9f;font-size:15px}'+
    '#tspop .tsf{display:flex;gap:8px;margin-top:8px}'+
    '#tspop .tsf button{flex:1}'+
    '#tspop input{width:100%;box-sizing:border-box;font:600 19px \'Vilna\',serif;color:#2b2620;background:#fdf8e7;border:1px solid #d1a23a;border-radius:8px;padding:8px 10px;margin-top:8px;direction:rtl}'+
    '#tspop .tsok{background:#d1a23a;color:#2b2620;border-color:#d1a23a;font-weight:700}'+
    '#tspop .tsok:hover{background:#e9c35a}'+
    '#tspop .tsld{display:inline-block;width:14px;height:14px;border:2px solid #d1a23a;border-top-color:transparent;border-radius:50%;animation:tsspin .8s linear infinite;vertical-align:middle;margin-inline-end:8px}'+
    '@keyframes tsspin{to{transform:rotate(360deg)}}'+
    'body.adm p.prop,body.adm p.prop *{color:#7B3F00!important}'+
    '#decobar button.tsb{color:var(--gd,#8f6a1e);font-weight:700}';
    document.head.appendChild(st);

    const TS={bank:null,bankP:null,live:null,pop:null};
    const NL=String.fromCharCode(10);
    function tsKey(t){return plain(String(t||'')).replace(/[^א-ת ]/g,' ').replace(/\s+/g,' ').trim().slice(0,40)}
    function loadBank(){
      if(TS.bank)return Promise.resolve(TS.bank);
      if(TS.bankP)return TS.bankP;
      TS.bankP=fetch('titlesug-'+SLUG+'.json').then(r=>r.ok?r.json():{}).catch(()=>({})).then(j=>{TS.bank=j||{};return TS.bank});
      return TS.bankP}
    /* דוגמאות לסגנון: כותרות הנושא הקיימות במסכת (שכתב המנהל או שבחר), עד 12 */
    function examples(){
      const out=[];
      D.pages.forEach(p=>p.units.forEach(u=>{if(u.k==='nose'&&!/\bprop\b/.test(u.s||'')){
        const t=plain(u.a).replace(/\s+/g,' ').trim();
        if(t&&t.split(' ').length<=8)out.push(t)}}));
      const step=Math.max(1,Math.floor(out.length/12)),pick=[];
      for(let i=0;i<out.length&&pick.length<12;i+=step)pick.push(out[i]);
      return pick}
    /* הקטע שאחרי המקום: עד הכותרת או החציצה הבאה, עד 900 תווים */
    function ctxFrom(items,i){
      const parts=[];let n=0;
      for(let k=i+1;k<items.length&&n<900;k++){
        const it=items[k];
        if(it.deco)break;
        if(it.u.k!=='u'&&it.u.k!=='m')break;
        const t=it.t.replace(/\s+/g,' ').trim();
        if(t){parts.push(t);n+=t.length}}
      return parts.join(' ').slice(0,900)}
    function target(){
      if(DECO.el){
        const h=decoOfEl(DECO.el);
        if(h){
          const items=decoItems(),i=items.findIndex(x=>x.u===h.u&&x.j===h.j&&x.deco);
          if(i>-1){const nb=decoNb(items,i);
            return {mode:'deco',el:DECO.el,h,key:tsKey(nb[1]),ctx:ctxFrom(items,i),inM:!!DECO.el.closest('.main.mishna')}}}}
      const el=edEl();
      if(el&&isTxt(el)){
        const t=txtOf(el),head=isHeadEl(el);
        const items=decoItems();
        let i=items.findIndex(x=>x.t&&x.t===plain(t)&&true);
        const ctx=(i>-1?[items[i].t].concat([ctxFrom(items,i)]).join(' '):t).replace(/\s+/g,' ').trim().slice(0,900);
        return {mode:head?'head':'line',el,key:tsKey(t),ctx,inM:!!el.closest('.main.mishna')}}
      return null}

    function close(){
      const p=$('#tspop');if(p)p.remove();
      document.removeEventListener('keydown',onKey,true);
      document.removeEventListener('pointerdown',onOut,true);
      TS.pop=null}
    function onOut(e){if(TS.pop&&!(e.target.closest&&e.target.closest('#tspop'))&&!(e.target.closest&&e.target.closest('#decobar,#stybar')))close()}
    function onKey(e){
      const P=TS.pop;if(!P)return;
      const inp=document.querySelector('#tspop input');
      if(e.key==='Escape'){e.preventDefault();e.stopPropagation();if(inp)render();else close();return}
      if(inp){if(e.key==='Enter'){e.preventDefault();e.stopPropagation();confirm()}return}
      if(/^[1-3]$/.test(e.key)&&!e.ctrlKey&&!e.altKey&&!e.metaKey){
        const i=+e.key-1;if(P.shown[i]!==undefined){e.preventDefault();e.stopPropagation();pick(i)}}}
    function place(){
      const P=TS.pop,p=$('#tspop');if(!P||!p)return;
      const rc=P.el.getBoundingClientRect(),h=p.offsetHeight||240,w=p.offsetWidth||340;
      const vis=rc.bottom>0&&rc.top<innerHeight&&rc.right>0&&rc.left<innerWidth;
      let top=rc.bottom+8,left=rc.left+Math.min(rc.width,w)/2-w/2;
      if(!vis){top=(innerHeight-h)/2;left=(innerWidth-w)/2}
      else if(top+h>innerHeight-8)top=rc.top-h-8;
      top=Math.max(8,Math.min(innerHeight-h-8,top));
      left=Math.max(8,Math.min(innerWidth-w-8,left));
      p.style.top=Math.round(top)+'px';p.style.left=Math.round(left)+'px'}
    function render(){
      const P=TS.pop;if(!P)return;
      let p=$('#tspop');
      if(!p){p=document.createElement('div');p.id='tspop';p.setAttribute('role','dialog');p.setAttribute('aria-label','הצעות לכותרת');document.body.appendChild(p);
        p.addEventListener('mousedown',e=>{if(e.target.tagName!=='INPUT')e.preventDefault()});
        p.addEventListener('click',onClick)}
      let h='<div class="tsh"><b>'+(P.mode==='head'?'הצעות לכותרת חלופית':'הצעות לכותרת')+'</b><button type="button" class="tsx" data-a="x" title="סגירה (Esc)">×</button></div>';
      if(P.mode==='deco'&&!P.inM&&PSTY.some(x=>x[0]==='dh')){
        h+='<div class="tsty"><button type="button" data-a="t" data-v="nose" class="'+(P.head==='nose'?'on':'')+'">כותרת נושא</button>'+
           '<button type="button" data-a="t" data-v="dh" class="'+(P.head==='dh'?'on':'')+'">ד"ה משנה</button></div>'}
      if(P.editing!==undefined){
        h+='<input type="text" value="'+esc(P.cand[P.editing]).replace(/"/g,'&quot;')+'" aria-label="נוסח הכותרת" maxlength="120">'+
           '<div class="tsf"><button type="button" class="tsok" data-a="ok">אישור</button><button type="button" data-a="back">חזרה להצעות</button></div>'}
      else if(P.loading){h+='<div class="tsmsg"><span class="tsld"></span>מכין הצעות…</div>'}
      else if(P.err&&!P.shown.length){h+='<div class="tsmsg">'+esc(P.err)+'</div>'+
        '<div class="tsf"><button type="button" data-a="more">נסה שוב</button><button type="button" data-a="x">סגור</button></div>'}
      else{
        P.shown.forEach((ix,k)=>{h+='<button type="button" class="tsr" data-a="pick" data-i="'+k+'"><b>'+(k+1)+'</b><span>'+esc(P.cand[ix])+'</span></button>'});
        if(P.err)h+='<div class="tsmsg" style="padding:6px">'+esc(P.err)+'</div>';
        h+='<div class="tsf"><button type="button" data-a="more">עוד הצעות</button><button type="button" data-a="x">סגור</button></div>'}
      p.innerHTML=h;
      place();
      const inp=p.querySelector('input');if(inp){inp.focus();inp.select()}}
    function onClick(e){
      const b=e.target.closest&&e.target.closest('button');if(!b)return;
      const a=b.dataset.a,P=TS.pop;if(!P)return;
      if(a==='x')close();
      else if(a==='pick')pick(+b.dataset.i);
      else if(a==='back'){delete P.editing;render()}
      else if(a==='ok')confirm();
      else if(a==='more')more();
      else if(a==='t'){P.head=b.dataset.v;render()}}
    function pick(k){const P=TS.pop;if(!P||P.shown[k]===undefined)return;P.editing=P.shown[k];render()}
    /* עוד הצעות: קודם מן השכבה המוכנה (עד שש בסך הכול), ואחר כך מן השכבה החיה */
    async function more(){
      const P=TS.pop;if(!P)return;
      P.err='';
      const next=[];for(let i=0;i<P.cand.length&&next.length<3;i++)if(P.shown.indexOf(i)<0&&P.used.indexOf(i)<0)next.push(i);
      if(next.length){P.shown=next;P.used.push(...next);render();return}
      P.loading=true;render();
      const t0=performance.now();
      try{
        const j=await api('/title',{method:'POST',body:JSON.stringify({slug:SLUG,ctx:P.ctx,examples:examples(),avoid:P.cand.slice(0,12),n:3})});
        if(TS.pop!==P)return;
        const fresh=(j.s||[]).filter(x=>x&&P.cand.indexOf(x)<0);
        if(!fresh.length)throw new Error('לא התקבלו הצעות חדשות');
        const from=P.cand.length;P.cand.push(...fresh);
        P.shown=fresh.map((_,i)=>from+i);P.used.push(...P.shown);P.loading=false;
        P.liveMs=Math.round(performance.now()-t0);render()}
      catch(err){
        if(TS.pop!==P)return;
        P.loading=false;
        P.err=/טרם הופעל|503/.test(err.message||'')?'אין עוד הצעות מוכנות, ושירות ההצעות החי טרם הופעל':(err.message||'השירות אינו זמין כרגע');
        render()}}
    async function open(){
      if(!isAdmin()){flash('הצעת כותרת זמינה למנהל בלבד');return}
      const T=target();
      if(!T){flash('העמד את הסמן בשורה, או סמן עיטור');return}
      close();
      TS.pop=Object.assign(T,{cand:[],shown:[],used:[],loading:true,head:'nose',err:''});
      document.addEventListener('keydown',onKey,true);
      document.addEventListener('pointerdown',onOut,true);
      render();
      const t0=performance.now();
      const bank=await loadBank();
      const P=TS.pop;if(!P||P!==TS.pop)return;
      const got=bank&&bank[P.key];
      if(got&&got.length){
        P.cand=got.slice();P.shown=P.cand.slice(0,3).map((_,i)=>i);P.used=P.shown.slice();P.loading=false;
        P.readyMs=Math.round(performance.now()-t0);render();return}
      /* אין הצעה מוכנה: השכבה החיה */
      P.loading=true;
      try{
        const j=await api('/title',{method:'POST',body:JSON.stringify({slug:SLUG,ctx:P.ctx,examples:examples(),n:3})});
        if(TS.pop!==P)return;
        P.cand=(j.s||[]).slice();
        if(!P.cand.length)throw new Error('לא התקבלו הצעות');
        P.shown=P.cand.slice(0,3).map((_,i)=>i);P.used=P.shown.slice();P.loading=false;
        P.liveMs=Math.round(performance.now()-t0);render()}
      catch(err){
        if(TS.pop!==P)return;
        P.loading=false;
        P.err=/טרם הופעל|503/.test(err.message||'')?'אין הצעה מוכנה למקום הזה, ושירות ההצעות החי טרם הופעל':(err.message||'השירות אינו זמין כרגע');
        render()}}

    function confirm(){
      const P=TS.pop,inp=$('#tspop input');if(!P||!inp)return;
      const sug=P.cand[P.editing];
      const title=inp.value.replace(/[–—]/g,'-').replace(/\s+/g,' ').trim();
      if(!title){inp.focus();return}
      const cl={sug,fin:title,i:P.editing,dec:title!==sug?1:0};
      const mode=P.mode,head=P.head,el=P.el,h=P.h;
      close();
      if(mode==='deco')applyDeco(head,title,cl);
      else if(mode==='head')applyHead(el,title,cl);
      else applyLine(el,title,cl)}
    /* עיטור -> כותרת: אותו מסלול של "החלף בכותרת", ואז הטקסט נכתב בה ונרשם */
    function applyDeco(head,title,cl){
      const t=decoDo('hrep',head);
      if(!t){return}
      setTimeout(()=>{
        const key='u'+t+'.0';
        const el=$('#flow').querySelector('[data-ek="'+key+'"]');
        let u=null;D.pages.forEach(p=>p.units.forEach(x=>{if(x.id===t)u=x}));
        if(!el||!u||!u.hph){flash('הכותרת לא נכנסה: רענן את הדף ונסה שוב');return}
        u.hph.cl=cl;
        el.textContent=title;
        u.s=((u.s||'')+' prop').trim();el.classList.add('prop');
        hrepCapture(el);
        placeCaret(key,title.length);
        flash('הכותרת נכנסה: '+title+'. לביטול: "העריכות שלי"')},60)}
    /* כותרת קיימת: מחליפים את הנוסח (עריכת טקסט רגילה) */
    function applyHead(el,title,cl){
      el.focus();
      const r=document.createRange();r.selectNodeContents(el);const s=getSelection();s.removeAllRanges();s.addRange(r);
      document.execCommand('insertText',false,title);
      clearTimeout(CAPT);capture(el);
      el.classList.add('prop');
      flash('הכותרת הוחלפה: '+title)}
    /* שורה רגילה: כותרת נושא חדשה לפניה, עם "רווח לפני" */
    function applyLine(el,title,cl){
      if(!newParaP(el,'before')){flash('אי אפשר להוסיף כאן כותרת');return}
      setTimeout(()=>{
        const ne=edEl();
        if(!ne||!isTxt(ne)){flash('הכותרת לא נכנסה: רענן את הדף ונסה שוב');return}
        document.execCommand('insertText',false,title);
        clearTimeout(CAPT);capture(ne);
        const pe=pinEntry(ne);
        const pn=pe&&PINS.get(pe.ent);
        if(pn&&pn.se)pn.se.cl=cl;
        if(PSTY.some(x=>x[0]==='nose'))setPs('nose');
        const ne2=edEl()||ne;
        /* "רווח לפני": מחלקת הרווח b1 נרשמת ברשומת ההוספה עצמה (res), לא רק בתצוגה */
        const pe2=pinEntry(ne2),pn2=pe2&&PINS.get(pe2.ent);
        if(pe2){
          const cls=(pe2.ent[0]||'').split(' ').filter(x=>x&&!/^b\d$/.test(x));
          cls.push('b1');pe2.ent[0]=cls.join(' ');
          if(pn2&&pn2.se&&pn2.se.res&&pn2.se.res[0]){pn2.se.res[0][0]=pe2.ent[0];pn2.se.pub=0}}
        [...ne2.classList].filter(x=>/^b\d$/.test(x)).forEach(x=>ne2.classList.remove(x));
        ne2.classList.add('b1');
        ne2.classList.add('prop');
        saveED();drawEd();pubSoon();
        flash('הכותרת נכנסה: '+title+'. לביטול: "העריכות שלי"')},80)}

    window.tsOpen=open;
    document.addEventListener('keydown',e=>{
      if(!EDIT||!e.ctrlKey||!e.altKey||e.shiftKey||e.metaKey||e.code!=='KeyK')return;
      e.preventDefault();e.stopPropagation();open()},true);
  })();
