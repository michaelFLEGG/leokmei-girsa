  /* =================== בוררי מסכת ודף בסרגל העליון (12.10.2026, לווקר) ===================
     לחיצה על שם המסכת: כל המסכתות בטור אחד, לפי סדרי הש"ס. לחיצה על הדף: כל דפי המסכת בטור אחד.
     הרשימות נבנות מאינדקס הש"ס הקל (shas.js) ומנתוני הדף עצמו, בלי לטעון קובצי מסכת אחרים.
     דף: קפיצה מיידית, בלי לצאת מהעריכה. מסכת: תיקון שטרם פורסם נשמר ומפורסם לפני המעבר,
     ואז מגיעים למקום האחרון של הלומד באותה מסכת (מערכת הלומד), ואם לא היה בה - לתחילתה.
     נטען אחרי הקוד המשותף: משתמש ב-D, SEC, SLUG, toDaf, EDIT, capture, saveED, pubPending, pubNow. */
  (function(){
    const st=document.createElement('style');st.textContent=
    '.bar .pkb{font:inherit;cursor:pointer;background:transparent;border:0;color:inherit;display:inline-flex;align-items:center;gap:5px;padding:2px 6px;border-radius:8px}'+
    '.bar .pkb:hover,.bar .pkb.open{background:var(--blue-soft,rgba(120,150,190,.18))}'+
    '.bar .pkb .pkar{width:0;height:0;border-inline:4px solid transparent;border-top:5px solid var(--gold-500,#d1a23a);margin-top:1px}'+
    '.bar .pkb.open .pkar{transform:rotate(180deg)}'+
    '.bar .pkb.pkd{font-family:\'VilnaG\',\'Vilna\',serif;font-size:19px;min-width:3.4em;justify-content:center;min-height:30px;border-radius:0}'+
    '.bar .pkb.mn{font-family:\'Vilna\',serif;font-weight:700;font-size:21px}'+
    '#pkp{position:fixed;z-index:60;background:#0f263b;color:#f5edd6;border:1px solid #d1a23a;border-radius:10px;box-shadow:0 10px 30px rgba(0,0,0,.4);'+
      'font-family:\'Vilna\',\'VilnaG\',serif;display:flex;flex-direction:column;overflow:hidden;direction:rtl}'+
    '#pkp .pkt{display:none;padding:12px 16px 8px;font-size:19px;font-weight:700;color:#f9e08a;border-bottom:1px solid rgba(209,162,58,.35)}'+
    '#pkp .pkl{overflow-y:auto;overscroll-behavior:contain;padding:4px 0;flex:1 1 auto}'+
    '#pkp .pkh{padding:8px 16px 3px;font-size:13px;color:#c9bf9f;letter-spacing:.02em;border-top:1px solid rgba(209,162,58,.28);margin-top:4px;'+
      'background:linear-gradient(90deg,transparent,rgba(209,162,58,.14),transparent)}'+
    '#pkp .pkh:first-child{border-top:0;margin-top:0}'+
    '#pkp .pki{display:block;width:100%;text-align:right;font:inherit;font-size:18px;color:#f5edd6;background:transparent;border:0;padding:5px 18px;cursor:pointer;min-height:34px}'+
    '#pkp .pki:hover,#pkp .pki.act{background:rgba(233,195,90,.16)}'+
    '#pkp .pki.on{color:#f9e08a;font-weight:700;background:rgba(233,195,90,.22);box-shadow:inset -3px 0 0 #d1a23a}'+
    '#pkp .pki.dis{color:#7f8590;cursor:default;background:transparent!important}'+
    '#pkp .pki small{font-size:12px;color:#c9bf9f;margin-inline-start:8px}'+
    '#pkscrim{position:fixed;inset:0;z-index:59;background:rgba(3,10,18,.55)}'+
    'html.dev-phone #pkp,html.dev-tab #pkp{left:0!important;right:0!important;top:auto!important;bottom:0;width:auto!important;max-height:78dvh!important;border-radius:18px 18px 0 0;border-width:2px 0 0}'+
    'html.dev-phone #pkp .pkt,html.dev-tab #pkp .pkt{display:block}'+
    'html.dev-phone #pkp .pki,html.dev-tab #pkp .pki{min-height:50px;font-size:20px;border-bottom:1px solid rgba(209,162,58,.12)}';
    document.head.appendChild(st);

    let PK=null;             /* {kind, anchor, els, act, buf, bt} */
    const mob=()=>{const c=document.documentElement.classList;return c.contains('dev-phone')||c.contains('dev-tab')};
    const nrm=s=>String(s||'').replace(/[֑-ׇ"'׳״.:\s]/g,'');
    const dafNow=()=>+($('#dafsel')&&$('#dafsel').value)||0;

    function masItems(){
      const out=[],S=(window.LGSHAS&&LGSHAS.seder)||[];
      S.forEach(sd=>{
        out.push({head:sd.name});
        (sd.masechtot||[]).forEach(m=>out.push({label:m.name,slug:m.slug,dis:!m.built,on:m.slug===SLUG,sub:m.built?'':'טרם באתר'}))});
      return out}
    function dafItems(){
      const out=[],cur=dafNow();
      SEC.forEach((s,si)=>{
        const nm=((s.perekName||'')+'').trim()?((s.perek||'')+' '+s.perekName).trim():((s.perek||'')+'').trim();
        if(nm)out.push({head:nm});
        for(let pi=s.from;pi<=s.to;pi++){const p=D.pages[pi];if(!p)continue;
          out.push({label:p.label||p.daf||'',pi,dis:!(p.units&&p.units.length),on:pi===cur,sub:(p.units&&p.units.length)?'':'חסר בקובץ'})}});
      return out}

    function close(){
      if(!PK)return;
      PK.anchor.classList.remove('open');PK.anchor.setAttribute('aria-expanded','false');
      const p=$('#pkp');if(p)p.remove();const s=$('#pkscrim');if(s)s.remove();
      document.removeEventListener('keydown',onKey,true);
      document.removeEventListener('pointerdown',onOut,true);
      removeEventListener('resize',close);
      PK=null}
    function onOut(e){
      if(!PK)return;
      if(e.target.closest&&(e.target.closest('#pkp')||e.target.closest('#'+PK.anchor.id)))return;
      close()}
    function setAct(i,scroll){
      if(!PK)return;
      PK.els.forEach(x=>x.classList.remove('act'));
      PK.act=i;const el=PK.els[i];if(!el)return;
      el.classList.add('act');
      if(scroll!==false)el.scrollIntoView({block:'nearest'})}
    function enabled(){return PK.els.map((e,i)=>e.classList.contains('dis')?-1:i).filter(i=>i>-1)}
    function step(d){
      const en=enabled();if(!en.length)return;
      let at=en.indexOf(PK.act);
      if(at<0)at=d>0?-1:en.length;
      at=Math.max(0,Math.min(en.length-1,at+d));
      setAct(en[at])}
    function onKey(e){
      if(!PK)return;
      const k=e.key;
      if(k==='Escape'){e.preventDefault();e.stopPropagation();close();return}
      if(k==='ArrowDown'){e.preventDefault();e.stopPropagation();step(1);return}
      if(k==='ArrowUp'){e.preventDefault();e.stopPropagation();step(-1);return}
      if(k==='Home'||k==='End'){e.preventDefault();e.stopPropagation();
        const en=enabled();if(en.length)setAct(k==='Home'?en[0]:en[en.length-1]);return}
      if(k==='Enter'||k===' '&&!PK.buf){
        if(k===' '&&PK.buf)return;
        e.preventDefault();e.stopPropagation();
        const el=PK.els[PK.act];if(el&&!el.classList.contains('dis'))choose(el);return}
      if(e.ctrlKey||e.metaKey||e.altKey||k.length!==1)return;
      /* הקלדת אות או כמה אותיות: קפיצה לפריט המתאים */
      e.preventDefault();e.stopPropagation();
      clearTimeout(PK.bt);PK.buf+=k;PK.bt=setTimeout(()=>{if(PK)PK.buf=''},900);
      const q=nrm(PK.buf);
      for(let i=0;i<PK.els.length;i++){
        const el=PK.els[i];if(el.classList.contains('dis'))continue;
        if(nrm(el.dataset.l).indexOf(q)===0){setAct(i);return}}}
    function choose(el){
      const kind=PK.kind;close();
      if(kind==='mas')goMas(el.dataset.slug);else goDaf(+el.dataset.pi)}
    function goDaf(pi){
      const ae=document.activeElement;
      if(EDIT&&ae&&ae.isContentEditable){clearTimeout(CAPT);capture(ae)}
      toDaf(pi)}
    async function goMas(slug){
      if(!slug||slug===SLUG)return;
      const ae=document.activeElement;
      if(EDIT&&ae&&ae.isContentEditable){clearTimeout(CAPT);capture(ae)}
      try{saveED()}catch(e){}
      let pend=0;try{pend=pubPending()}catch(e){}
      if(pend){
        try{toast('שומר ומפרסם את התיקונים לפני המעבר…',6000)}catch(e){}
        try{await Promise.race([pubNow(true),new Promise(r=>setTimeout(r,7000))])}catch(e){}}
      /* היעד: המקום האחרון של הלומד במסכת, ואם לא היה בה - תחילתה */
      let href=slug+'.html';
      try{
        const L=window.LAMED,l=L&&L.state().last.by[slug];
        const h=l&&L.ui.readHref(slug,l.d,l);
        if(h)href=h}catch(e){}
      location.href=href}

    function open(kind,anchor,tries){
      if(PK&&PK.kind===kind){close();return}      /* לחיצה שנייה על אותה מילה: סגירה */
      close();
      if(kind==='mas'&&!(window.LGSHAS&&LGSHAS.seder)){
        if((tries||0)<12)setTimeout(()=>open(kind,anchor,(tries||0)+1),250);
        return}
      const list=kind==='mas'?masItems():dafItems();
      const pop=document.createElement('div');pop.id='pkp';pop.setAttribute('role','listbox');
      pop.setAttribute('aria-label',kind==='mas'?'מסכת':'דף');
      let h='<div class="pkt">'+(kind==='mas'?'מעבר למסכת':'מעבר לדף ב'+esc(D.masechet))+'</div><div class="pkl">';
      list.forEach(it=>{
        if(it.head){h+='<div class="pkh">'+esc(it.head)+'</div>';return}
        h+='<button type="button" class="pki'+(it.on?' on':'')+(it.dis?' dis':'')+'" role="option"'+(it.on?' aria-selected="true"':'')+
           (it.dis?' aria-disabled="true"':'')+' data-l="'+esc(it.label).replace(/"/g,'&quot;')+'"'+
           (it.slug?' data-slug="'+it.slug+'"':'')+(it.pi!==undefined?' data-pi="'+it.pi+'"':'')+'>'+esc(it.label)+
           (it.sub?'<small>'+esc(it.sub)+'</small>':'')+'</button>'});
      h+='</div>';pop.innerHTML=h;
      if(mob()){const sc=document.createElement('div');sc.id='pkscrim';sc.onclick=close;document.body.appendChild(sc)}
      document.body.appendChild(pop);
      /* מיקום: מתחת למילה שנלחצה, צר, עם גובה מרבי וגלילה פנימית */
      if(!mob()){
        const r=anchor.getBoundingClientRect(),w=kind==='mas'?230:150;
        pop.style.width=w+'px';
        let left=Math.round(r.right-w);if(left<8)left=8;if(left+w>innerWidth-8)left=innerWidth-8-w;
        pop.style.left=left+'px';pop.style.top=Math.round(r.bottom+6)+'px';
        pop.style.maxHeight=Math.max(160,Math.min(innerHeight*0.72,innerHeight-r.bottom-20))+'px'}
      const els=[...pop.querySelectorAll('.pki')];
      PK={kind,anchor,els,act:-1,buf:'',bt:0};
      anchor.classList.add('open');anchor.setAttribute('aria-expanded','true');
      /* נפתח כשהוא כבר גלול אל הפריט הנוכחי */
      const on=els.findIndex(e=>e.classList.contains('on'));
      const lst=pop.querySelector('.pkl');
      if(on>-1){setAct(on,false);
        const el=els[on];lst.scrollTop=Math.max(0,el.offsetTop-lst.clientHeight/2+el.offsetHeight/2)}
      pop.addEventListener('mousedown',e=>e.preventDefault());     /* בעריכה: הסמן נשאר במקומו */
      pop.addEventListener('click',e=>{const b=e.target.closest('.pki');if(!b||b.classList.contains('dis'))return;choose(b)});
      pop.addEventListener('mousemove',e=>{const b=e.target.closest('.pki');if(b&&!b.classList.contains('dis'))setAct(els.indexOf(b),false)});
      document.addEventListener('keydown',onKey,true);
      document.addEventListener('pointerdown',onOut,true);
      addEventListener('resize',close)}

    /* תווית הדף בכפתור: תמיד הדף של הקטע שעומדים עליו (מתעדכן מ-#curdaf, שנעקב אחרי הגלילה והסמן) */
    function label(){
      const b=$('#pkdl'),c=$('#curdaf');
      if(b)b.textContent=((c&&c.textContent)||'').trim()||(D.pages[dafNow()]&&(D.pages[dafNow()].label||D.pages[dafNow()].daf))||'דף'}
    function wire(){
      const m=$('#pkmas'),d=$('#pkdaf');if(!m||!d)return;
      [m,d].forEach(b=>b.addEventListener('mousedown',e=>e.preventDefault()));
      m.addEventListener('click',()=>open('mas',m));
      d.addEventListener('click',()=>open('daf',d));
      const c=$('#curdaf');
      if(c&&window.MutationObserver)new MutationObserver(label).observe(c,{childList:true,characterData:true,subtree:true});
      label();setTimeout(label,400)}
    window.lkPick=open;
    window.lkPickLabel=label;
    if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',wire);else wire();
  })();
