  /* =================== חברותא בצד ההערה (19.10.2026) ===================
     25.10.2026: רכיב התצוגה משותף לכל המסכתות (בקוד המשותף), ומשמש שני מקומות: הלוח שבצד ההערה
     (hvShell, נפתח מסרגל הסקירה - החיבור בקובץ hv_glue.js) ולשונית "חברותא" במגירת המקור, ליד
     "פירוש הגמרא". בכל רגע אחד מהם מוצג, והוא hvS(). מנהל בלבד: הנתונים נמשכים מ-/hv/page במפתח המנהל ואינם בקובצי האתר.
     הלוח הוא "דף ארוך אחד" של ביאור חברותא: כל שורות העמוד ברצף, השורות הרלוונטיות להערה מודגשות והלוח גולל אליהן;
     בראשו נטען העמוד הקודם ובסופו הבא (גלילה רציפה, כותרת דקה בין העמודים). כל ההערות במקומן (מספר קטן בשורה,
     לחיצה פותחת). הלוח עוקב אחרי הסמן בטקסט הראשי (גם מחוץ לסקירה), נגרר לרוחב, מתכווץ לפס, ויש בו חיפוש.
     חומר עיון בלבד: אין העתקה לנוסח, אין פרסום, והלוח מוסתר בהדפסה. */
  const HV={on:(function(){try{return localStorage.getItem('lg-hv-on')==='1'}catch(e){return false}})(),cache:{},pages:[],
    w:(function(){try{return Math.max(260,Math.min(900,+localStorage.getItem('lg-hv-w')||460))}catch(e){return 460}})(),
    col:(function(){try{return localStorage.getItem('lg-hv-c')==='1'}catch(e){return false}})(),
    q:'',busy:false,pin:0,hover:false,mi:-1,fid:'',fdaf:'',refs:[],tab:false};
  const HVG={'א':1,'ב':2,'ג':3,'ד':4,'ה':5,'ו':6,'ז':7,'ח':8,'ט':9,'י':10,'כ':20,'ל':30,'מ':40,'נ':50,'ס':60,'ע':70,'פ':80,'צ':90,'ק':100};
  function hvKey(d){d=String(d||'').trim();const side=/:$/.test(d)?1:0;let n=0;for(const ch of d.replace(/[^א-ת]/g,''))n+=HVG[ch]||0;return n?n*2+side:null}
  function hvX(t){return String(t).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;')}
  function hvDafs(){const o=[],seen={};(D.pages||[]).forEach(p=>{const d=p.daf;if(d&&!seen[d]){seen[d]=1;o.push(d)}});return o}
  const hvBK=()=>typeof BK!=='undefined'?BK:{byId:{},ord:[],ON:false};
  function hvS(){return document.getElementById(HV.tab?'hvt':'hvs')}
  function hvSave(k,v){try{localStorage.setItem(k,v)}catch(e){}}
  function hvFont(){const f=document.getElementById('flow');const px=f?parseFloat(getComputedStyle(f).fontSize):0;return Math.max(16,Math.round((px||17)*10)/10)}
  function hvCss(){
    let st=document.getElementById('hvcss');if(!st){st=document.createElement('style');st.id='hvcss';document.head.appendChild(st)}
    st.textContent='#hvx{position:fixed;top:0;left:0;width:'+HV.w+'px;max-width:96vw;height:100%;background:#fffdf4;border-right:2px solid #7a5a00;z-index:1190;box-sizing:border-box;direction:rtl;box-shadow:2px 0 12px rgba(0,0,0,.25);display:flex;flex-direction:column;color:#2b2620}'+
      '#hvx.col{width:36px}#hvx.col .hvbody,#hvx.col #hvgrip{display:none}#hvx .hvexp{display:none}#hvx.col .hvexp{display:flex;flex-direction:column;align-items:center;gap:10px;padding-top:8px}'+
      '#hvx .hvexp button{font:inherit;border:1px solid #b9a97c;background:#f6f1e2;border-radius:5px;cursor:pointer;padding:2px 4px}#hvx .hvexp span{writing-mode:vertical-rl;color:#7a5a00;font-weight:700;font-size:15px}'+
      '#hvx .hvbody{display:flex;flex-direction:column;height:100%;min-height:0}'+
      '#hvx .hvh{display:flex;gap:5px;align-items:center;padding:6px 8px;border-bottom:1px solid #e6dfcb;color:#7a5a00;font-weight:700;font-size:15px;flex:none;flex-wrap:wrap}'+
      '#hvx .hvh .tt{flex:1;min-width:60px}#hvx .hvh button{font:inherit;font-size:14px;border:1px solid #b9a97c;background:#f6f1e2;border-radius:5px;cursor:pointer;padding:0 8px;line-height:1.5;color:#2b2620}'+
      '#hvx .hvq{display:flex;gap:5px;align-items:center;padding:4px 8px;flex:none;border-bottom:1px solid #eee6cf}#hvx .hvq input{flex:1;font:inherit;font-size:14px;min-width:0;box-sizing:border-box;border:1px solid #c9b98f;border-radius:5px;padding:1px 6px;background:#fff;color:#2b2620}#hvx .hvq small{color:#8a7d66;font-size:12px;white-space:nowrap}'+
      '#hvx .hvs{flex:1;min-height:0;overflow:auto;padding:4px 10px 24px;font-size:'+hvFont()+'px;line-height:1.75}'+
      '#hvx .hvdh{margin:14px 0 6px;text-align:center;font-size:13px;color:#7a5a00;border-top:1px solid #d9b84c;border-bottom:1px solid #d9b84c;background:#faf5e3;padding:0 6px;font-weight:700}'+
      '#hvx .sg{padding:3px 7px;border-radius:5px;margin:3px 0;border:1px solid transparent}#hvx .sg.ref{background:#fff0c4;border-color:#d9b84c}#hvx .sg.follow{background:#e3eefa;border-color:#6a98c9}'+
      '#hvx .sg b{color:#000}#hvx .sg .k{font-size:11px;color:#7a5a00;margin-left:5px}#hvx .nt{font-size:.88em;margin:4px 0;padding:3px 8px;border-right:3px solid #2e5b8a;background:#eef3f9}#hvx .dim{font-size:12px;color:#8a7d66}'+
      '#hvx sup.hvn{cursor:pointer;color:#fff;background:#2e5b8a;border-radius:8px;padding:0 5px;margin:0 2px;font-size:.68em;font-weight:700}#hvx mark.hvm{background:#ffe082;color:inherit}#hvx mark.hvm.cur{background:#ff9f43}'+
      '#hvx .hvfoot{flex:none;padding:3px 8px;border-top:1px solid #e6dfcb;font-size:11px;color:#8a7d66}#hvx .hvwarn{color:#8a3b2f}'+
      '#hvgrip{position:absolute;top:0;right:-5px;width:10px;height:100%;cursor:ew-resize;z-index:2;touch-action:none}#hvgrip:hover{background:rgba(122,90,0,.25)}'+
      '@media print{#hvx{display:none!important}}';
    hvLayout()}
  /* במסך רחב הלוח מצמצם את אזור הקריאה ולא מכסה אותו; בצר - צף */
  function hvLayout(){
    const open=!!document.getElementById('hvx')&&HV.on,wide=innerWidth>=1100;
    document.body.style.paddingLeft=(open&&wide)?((HV.col?36:HV.w)+'px'):''}
  async function hvLoad(daf){
    const key=hvKey(daf);if(key==null)return null;const c=Math.floor(key/12),ck=SLUG+'|'+daf;
    if(ck in HV.cache)return HV.cache[ck];
    let pg=null;
    try{const r=await api('/hv/page?slug='+encodeURIComponent(SLUG)+'&daf='+encodeURIComponent(daf)+'&c='+c);pg=r&&r.found?r.page:null}catch(e){pg=null}
    HV.cache[ck]=pg;return pg}
  function hvRefs(f){
    const t=(f&&f.note||'')+' '+(f&&f.evidence||'');const ks=[];let m;
    const re1=/חברותא\s+[^\s\d\]]+\s+שורה\s+(\d+)/g;while((m=re1.exec(t)))ks.push(+m[1]);
    return ks}
  function hvMark(escd){
    if(!HV.q)return escd;
    const q=hvX(HV.q).replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
    try{return escd.replace(new RegExp(q,'g'),'<mark class="hvm">$&</mark>')}catch(e){return escd}}
  /* סימון [[הערה:N]] בשורה: ההערה ה-i ברצף הסימונים בעמוד היא ההערה ה-i ברשימת העמוד (המספר מתאפס בתוך העמוד) */
  function hvSegHtml(s,daf,pg,cls){
    const notes=pg.notes||[];
    const e=hvMark(hvX(s.e||'')).replace(/\[\[הערה:(\d+)\]\]/g,(m,n)=>{
      const idx=pg._cnt++,nt=notes[idx];
      return '<sup class="hvn" data-d="'+hvX(daf)+'" data-i="'+idx+'" title="'+hvX(((nt&&nt.t)||'').slice(0,160))+'" onclick="hvNote(this)">'+n+'</sup>'});
    return '<div class="sg'+(cls?' '+cls:'')+'" data-k="'+s.k+'" data-p="'+(s.p==null?'':s.p)+'" data-d="'+hvX(daf)+'"><span class="k">'+s.k+(s.p==null?' · בלי מקבילה בקיצור':'')+'</span>'+(s.g?'<b>'+hvMark(hvX(s.g))+'</b> ':'')+e+'</div>'}
  function hvSecHtml(daf,pg){
    pg._cnt=0;
    const f=hvBK().byId[HV.fid],mine=daf===HV.fdaf&&f;
    const ps=mine?pg.segs.filter(s=>s.p===f.i).map(s=>s.k):[];
    let h='<section class="hvsec" data-daf="'+hvX(daf)+'"><div class="hvdh">דף '+hvX(daf)+'</div>';
    /* עמוד שטרם יושר (אין לו פסקאות לאוקמי בדף, או שהיישור טרם רץ): טקסט חברותא הגולמי, ונאמר */
    if(pg.raw)h+='<div class="dim hvraw">עוד לא יושר לפסקאות</div>';
    if(!pg.segs||!pg.segs.length)h+='<div class="dim">אין שורות לעמוד הזה.</div>';
    (pg.segs||[]).forEach(s=>{
      const cls=mine&&((HV.refs.length&&HV.refs.indexOf(s.k)>-1)||(!HV.refs.length&&ps.indexOf(s.k)>-1))?'ref':'';
      h+=hvSegHtml(s,daf,pg,cls)});
    return h+'</section>'}
  function hvNotFound(daf){return '<section class="hvsec" data-daf="'+hvX(daf)+'"><div class="hvdh">דף '+hvX(daf)+'</div><div class="dim">אין חומר חברותא לעמוד הזה (או שטרם הועלה).</div></section>'}
  window.hvNote=function(el){
    const seg=el.closest('.sg');if(!seg)return;
    const nx=seg.nextElementSibling;
    if(nx&&nx.classList.contains('nt')&&nx.dataset.i===el.dataset.i&&nx.dataset.d===el.dataset.d){nx.remove();return}
    const pg=HV.cache[SLUG+'|'+el.dataset.d],n=pg&&pg.notes&&pg.notes[+el.dataset.i];if(!n)return;
    const d=document.createElement('div');d.className='nt';d.dataset.i=el.dataset.i;d.dataset.d=el.dataset.d;
    d.innerHTML='<span class="dim">הערה '+n.n+' · '+hvX((n.src||[]).join(', '))+'</span><br>'+hvX(n.t);
    seg.parentNode.insertBefore(d,seg.nextSibling)};
  window.hvClose=function(){HV.on=false;hvSave('lg-hv-on','0');const p=document.getElementById('hvx');if(p)p.remove();if(!HV.tab)HV.pages=[];hvLayout();if(typeof bkBarDraw==='function'&&hvBK().ON)bkBarDraw()};
  window.hvToggle=function(){
    if(HV.on){hvClose();return}
    if(HV.tab)hvTabSet('per');
    HV.on=true;hvSave('lg-hv-on','1');
    const B=hvBK(),f=B.byId[B.curId]||B.ord[0];
    if(f)hvShow(f);else hvOpenDaf((typeof bkDafNow==='function'&&bkDafNow())||(hvDafs()[0]||''),null);
    if(typeof bkBarDraw==='function'&&B.ON)bkBarDraw()};
  window.hvCollapse=function(){HV.col=!HV.col;hvSave('lg-hv-c',HV.col?'1':'0');const p=document.getElementById('hvx');if(p)p.classList.toggle('col',HV.col);hvLayout()};
  function hvShell(){
    hvCss();let p=document.getElementById('hvx');
    if(!p){p=document.createElement('div');p.id='hvx';document.body.appendChild(p);
      p.innerHTML='<div id="hvgrip" title="גרור לשינוי הרוחב"></div>'+
        '<div class="hvexp"><button onclick="hvCollapse()" title="פתח את חברותא" aria-label="פתיחה">◀</button><span>חברותא</span></div>'+
        '<div class="hvbody"><div class="hvh"><span class="tt">חברותא</span><button onclick="hvPage(-1)" title="לעמוד הקודם (PageUp כשהעכבר על הלוח)">▲ קודם</button><button onclick="hvPage(1)" title="לעמוד הבא (PageDown כשהעכבר על הלוח)">▼ הבא</button><button onclick="hvCollapse()" title="כיווץ לפס צר">▶|</button><button onclick="hvClose()" title="סגירה" aria-label="סגירה">×</button></div>'+
        '<div class="hvq"><input id="hvq" type="search" placeholder="חיפוש בעמודים הטעונים" aria-label="חיפוש בלוח"><small id="hvqc"></small></div>'+
        '<div class="hvs" id="hvs"></div>'+
        '<div class="hvfoot"><span class="hvwarn">חומר עיון למנהל בלבד: אינו מועתק לנוסח, אינו מתפרסם ואינו מודפס.</span><br>מקור: ביאור חברותא, פרשנים וויקישיבה (CC BY-NC 3.0)</div></div>';
      const s=p.querySelector('#hvs');
      s.addEventListener('scroll',hvScroll,{passive:true});
      p.addEventListener('pointerenter',()=>{HV.hover=true});p.addEventListener('pointerleave',()=>{HV.hover=false});
      const q=p.querySelector('#hvq');let qt=0;
      q.addEventListener('input',()=>{clearTimeout(qt);qt=setTimeout(()=>{HV.q=q.value.trim();HV.mi=-1;hvRender(true);hvCount()},220)});
      q.addEventListener('keydown',e=>{e.stopPropagation();if(e.key==='Enter'){e.preventDefault();hvQNext(e.shiftKey?-1:1)}},true);
      q.addEventListener('keyup',e=>e.stopPropagation(),true);
      /* גרירת הרוחב */
      const g=p.querySelector('#hvgrip');let dr=null;
      g.addEventListener('pointerdown',e=>{dr={x:e.clientX,w:HV.w};g.setPointerCapture(e.pointerId);e.preventDefault()});
      g.addEventListener('pointermove',e=>{if(!dr)return;HV.w=Math.max(260,Math.min(900,Math.min(innerWidth-60,dr.w+(e.clientX-dr.x))));hvCss()});
      g.addEventListener('pointerup',e=>{if(!dr)return;dr=null;hvSave('lg-hv-w',String(HV.w))});
    }
    p.classList.toggle('col',HV.col);hvLayout();return p}
  document.addEventListener('keydown',e=>{
    if(!HV.on||HV.tab||!HV.hover||e.ctrlKey||e.metaKey||e.altKey)return;
    if(e.code!=='PageDown'&&e.code!=='PageUp')return;
    const s=document.getElementById('hvs');if(!s)return;
    e.preventDefault();e.stopPropagation();s.scrollTop+=(e.code==='PageDown'?1:-1)*Math.round(s.clientHeight*.85)},true);
  addEventListener('resize',()=>{if(HV.on)hvLayout()});
  function hvCount(){const c=document.getElementById('hvqc');if(!c||HV.tab)return;
    const n=document.querySelectorAll('#hvs mark.hvm').length;c.textContent=HV.q?(n?(HV.mi>=0?(HV.mi+1)+'/':'')+n:'אין'):''}
  function hvQNext(d){const ms=document.querySelectorAll('#hvs mark.hvm');if(!ms.length)return;
    HV.mi=(HV.mi+d+ms.length)%ms.length;ms.forEach((m,i)=>m.classList.toggle('cur',i===HV.mi));
    ms[HV.mi].scrollIntoView({block:'center'});hvCount()}
  function hvTopSeg(s){const sr=s.getBoundingClientRect().top;return Array.from(s.querySelectorAll('.sg')).find(x=>x.getBoundingClientRect().bottom>sr+2)||null}
  /* ציור כל העמודים הטעונים ברצף. keep: משמר את מקום הגלילה */
  function hvRender(keep){
    const s=hvS();if(!s)return;
    const top=s.scrollTop,an=keep?hvTopSeg(s):null,off=an?an.getBoundingClientRect().top-s.getBoundingClientRect().top:0;
    const ak=an?an.dataset.d+'|'+an.dataset.k:'';
    s.innerHTML=HV.pages.map(d=>{const pg=HV.cache[SLUG+'|'+d];return pg?hvSecHtml(d,pg):hvNotFound(d)}).join('');
    /* השורה המקבילה לסמן נשארת מודגשת גם כשעמוד נוסף נטען בגלילה */
    if(HV.fol&&HV.fol.length)s.querySelectorAll('.sg').forEach(x=>{if(HV.fol.indexOf(x.dataset.d+'|'+x.dataset.k)>-1)x.classList.add('follow')});
    if(keep&&ak){const n=Array.from(s.querySelectorAll('.sg')).find(x=>x.dataset.d+'|'+x.dataset.k===ak);
      if(n)s.scrollTop+=n.getBoundingClientRect().top-s.getBoundingClientRect().top-off;else s.scrollTop=top}}
  async function hvEnsure(daf,where){
    if(HV.pages.indexOf(daf)>-1)return;
    await hvLoad(daf);
    if(where==='before')HV.pages.unshift(daf);else HV.pages.push(daf)}
  async function hvScroll(){
    if(HV.busy)return;const s=hvS();if(!s)return;
    const ds=hvDafs();
    if(s.scrollTop<60){const i=ds.indexOf(HV.pages[0]);
      if(i>0){HV.busy=true;const h0=s.scrollHeight,t0=s.scrollTop;await hvEnsure(ds[i-1],'before');hvRender(false);s.scrollTop=t0+(s.scrollHeight-h0);HV.busy=false;return}}
    if(s.scrollHeight-s.scrollTop-s.clientHeight<160){const i=ds.indexOf(HV.pages[HV.pages.length-1]);
      if(i>-1&&i<ds.length-1){HV.busy=true;const t0=s.scrollTop;await hvEnsure(ds[i+1],'after');hvRender(false);s.scrollTop=t0;HV.busy=false}}}
  /* ▲ ▼: לכותרת העמוד הקודם / הבא (וטעינתו אם טרם נטען) */
  window.hvPage=async function(d){
    const s=hvS();if(!s||HV.busy)return;
    const heads=Array.from(s.querySelectorAll('.hvdh')),sr=s.getBoundingClientRect().top;
    const cur=heads.filter(h=>h.getBoundingClientRect().top<=sr+8).pop();
    const idx=cur?heads.indexOf(cur):-1;
    if(d>0){
      if(idx+1<heads.length){heads[idx+1].scrollIntoView({block:'start'});return}
      const ds=hvDafs(),i=ds.indexOf(HV.pages[HV.pages.length-1]);
      if(i>-1&&i<ds.length-1){HV.busy=true;await hvEnsure(ds[i+1],'after');hvRender(true);HV.busy=false;
        const hs=s.querySelectorAll('.hvdh');if(hs[idx+1])hs[idx+1].scrollIntoView({block:'start'})}}
    else{
      if(cur&&Math.abs(cur.getBoundingClientRect().top-sr)>12){cur.scrollIntoView({block:'start'});return}
      if(idx-1>=0){heads[idx-1].scrollIntoView({block:'start'});return}
      const ds=hvDafs(),i=ds.indexOf(HV.pages[0]);
      if(i>0){HV.busy=true;await hvEnsure(ds[i-1],'before');hvRender(false);HV.busy=false;
        const hs=s.querySelectorAll('.hvdh');if(hs[0])hs[0].scrollIntoView({block:'start'})}}};
  function hvCenter(sel){const s=hvS();if(!s)return false;
    const n=s.querySelector(sel);if(!n)return false;
    s.scrollTop+=n.getBoundingClientRect().top-s.getBoundingClientRect().top-(s.clientHeight-n.offsetHeight)/2;return true}
  function hvSel(daf){return '.hvsec[data-daf="'+String(daf).replace(/"/g,'\\"')+'"]'}
  /* פתיחה על עמוד: אם הוא כבר בלוח - רק גוללים אליו; אחרת מתחילים רצף חדש ממנו (וגם הקודם, כדי שאפשר לגלול למעלה מיד) */
  async function hvOpenDaf(daf,focusSel){
    daf=String(daf||'').trim();if(!daf)return;if(!HV.tab)hvShell();
    const fresh=HV.pages.indexOf(daf)<0;
    if(fresh){HV.pages=[];await hvEnsure(daf,'after');
      const ds=hvDafs(),i=ds.indexOf(daf);if(i>0)await hvEnsure(ds[i-1],'before');
      hvRender(false)}
    else hvRender(true);
    const s=hvS();
    if(!(focusSel&&hvCenter(focusSel))){const h=s&&s.querySelector(hvSel(daf)+' .hvdh');if(h)s.scrollTop+=h.getBoundingClientRect().top-s.getBoundingClientRect().top}
    hvCount()}
  /* הערה פעילה בסקירה: הלוח גולל לשורות שהיא מצטטת או שהותאמו לפסקה, ומדגיש */
  window.hvShow=async function(f){
    if(!HV.on||HV.tab||!f)return;
    HV.pin=Date.now();HV.fid=f.id;HV.fdaf=(f.daf||'').trim();HV.refs=hvRefs(f);
    hvShell();
    await hvOpenDaf(HV.fdaf,null);
    if(HV.fid!==f.id)return;
    if(!hvCenter('.sg.ref'))hvCenter(hvSel(HV.fdaf)+' .sg')};
  /* עוקב אחרי הסמן בטקסט הראשי (גם בלי סקירה): השורות המותאמות לפסקה מודגשות והלוח גולל אליהן */
  let HVFT=null;
  function hvFollow(target){
    if(!(HV.on||HV.tab)||Date.now()-HV.pin<1500)return;
    const el=target&&target.closest?target.closest('[data-ek]'):null;if(!el||!el.closest('#flow'))return;
    const s=slotsFull().find(x=>x.k===el.dataset.ek);if(!s)return;
    const daf=String(s.daf||'').trim();if(!daf)return;
    hvOpenDaf(daf,null).then(()=>{
      const sc=hvS();if(!sc)return;
      sc.querySelectorAll('.sg.follow').forEach(x=>x.classList.remove('follow'));
      const sec=sc.querySelector(hvSel(daf));if(!sec)return;
      const all=Array.from(sec.querySelectorAll('.sg'));if(!all.length)return;
      let hit=all.filter(x=>x.dataset.p!==''&&+x.dataset.p===s.id);
      if(!hit.length){/* אין התאמה: לשורה הקרובה לפי מקום הפסקה בתוך העמוד */
        const pg=D.pages[s.pi];let r=0;
        if(pg&&pg.units&&pg.units.length){const ix=pg.units.findIndex(u=>u.id===s.id);r=ix<0?0:ix/pg.units.length}
        hit=[all[Math.min(all.length-1,Math.floor(r*all.length))]]}
      hit.forEach(x=>x.classList.add('follow'));HV.fol=hit.map(x=>x.dataset.d+'|'+x.dataset.k);
      sc.scrollTop+=hit[0].getBoundingClientRect().top-sc.getBoundingClientRect().top-(sc.clientHeight-hit[0].offsetHeight)/2})}
  function hvFollowSoon(t){clearTimeout(HVFT);HVFT=setTimeout(()=>hvFollow(t),220)}
  document.addEventListener('click',e=>{if((HV.on||HV.tab)&&e.target.closest&&e.target.closest('#flow'))hvFollowSoon(e.target)},true);
  document.addEventListener('selectionchange',()=>{if(!(HV.on||HV.tab))return;const sel=getSelection();if(!sel||!sel.anchorNode)return;
    const n=sel.anchorNode.nodeType===1?sel.anchorNode:sel.anchorNode.parentElement;if(n&&n.closest&&n.closest('#flow'))hvFollowSoon(n)});
  /* =================== לשונית "חברותא" במגירת המקור (25.10.2026) ===================
     ליד "פירוש הגמרא", למנהל המחובר בלבד: אצל גולש ואורח הלשונית אינה נוצרת כלל (hvTabsHTML מחזיר ריק).
     אותו רכיב תצוגה של הלוח (hvSecHtml, hvOpenDaf, hvFollow, hvPage), במיכל #hvt. כל הדף ברצף, נגלל
     עם הסמן כמו פירוש הגמרא, השורה המקבילה מודגשת בעדינות, וקודם/הבא. החבילה נטענת פעם אחת לדף
     ונשמרת בזיכרון הדף (HV.cache) - לא במכשיר, לא במטמון, לא בהדפסה ולא בייצוא. Alt+J מחליף לשונית. */
  function hvTabOk(){return isAdmin()&&!!admKey()}
  function hvTabsHTML(){
    if(!hvTabOk())return '';
    return '<span class="srctabs" role="tablist"><button id="st-per" role="tab" class="'+(HV.tab||HV.tabWas?'':'on')+'" onclick="hvTabSet(\'per\')" title="פירוש הגמרא (Alt+J מחליף לחברותא)">פירוש הגמרא</button>'+
      '<button id="st-hv" role="tab" class="'+(HV.tab||HV.tabWas?'on':'')+'" onclick="hvTabSet(\'hv\')" title="ביאור חברותא, לעיון המנהל בלבד (Alt+J)">חברותא</button></span>'}
  function hvTabCss(){
    if(document.getElementById('hvtcss'))return;
    const st=document.createElement('style');st.id='hvtcss';
    st.textContent='.srctabs{display:inline-flex;gap:2px;background:#1e1a16;border-radius:5px;padding:2px}.srctabs button{background:transparent!important}.srctabs button.on{background:var(--gold)!important;color:#2b2620!important}'+
      '#hvtw{flex:1 1 auto;display:flex;flex-direction:column;min-height:0}#hvtw[hidden]{display:none}'+
      '#hvtw .hvtag{flex:none;font-size:12px;color:#8a3b2f;background:#f8efe2;border-bottom:1px solid #e0d8c4;padding:3px 14px}'+
      '#hvt{flex:1 1 auto;overflow:auto;padding:4px 18px 24px}'+
      '#hvt .hvdh{position:sticky;top:-4px;z-index:1;background:var(--paper);margin:14px 0 6px;font-size:14px;font-weight:500;color:#8a7d66;border-bottom:1px solid #e0d8c4;padding-bottom:3px}'+
      /* גופן וגודל כמו פירוש הגמרא (.prs) */
      '#hvt .sg{font-size:.84em;line-height:1.5;color:#4a4137;background:#f2ede0;border-right:2px solid #cdc3a8;border-radius:3px;margin:2px 5px 6px;padding:5px 9px}'+
      '#hvt .sg b{color:#2b2620}#hvt .sg .k{font-size:11px;color:#a08f6c;margin-left:5px}'+
      '#hvt .sg.follow{background:#f8e6b8;border-right-color:var(--gold)}#hvt .sg.ref{background:#fdf1d8}'+
      '#hvt .dim{font-size:12px;color:#8a7d66}#hvt .hvraw{color:#8a3b2f;margin:0 5px 6px}'+
      '#hvt .nt{font-size:.8em;margin:0 5px 6px;padding:3px 8px;border-right:3px solid #2e5b8a;background:#eef3f9}'+
      '#hvt sup.hvn{cursor:pointer;color:#fff;background:#2e5b8a;border-radius:8px;padding:0 5px;margin:0 2px;font-size:.68em;font-weight:700}'+
      '@media print{#hvtw,.srctabs{display:none!important}}';
    document.head.appendChild(st)}
  /* נקרא מ-openSrc: מקום הלשונית בגוף המגירה */
  function hvTabMount(box){
    if(!hvTabOk()||!box)return;
    hvTabCss();
    let w=box.querySelector('#hvtw');
    if(!w){w=document.createElement('div');w.id='hvtw';w.hidden=true;
      w.innerHTML='<div class="hvtag">חברותא - לעיון המנהל בלבד</div><div id="hvt" tabindex="-1"></div>';
      const b=box.querySelector('.srcbody');if(b)b.after(w);else box.appendChild(w);
      w.querySelector('#hvt').addEventListener('scroll',hvScroll,{passive:true})}
    if(HV.tab||HV.tabWas){HV.tabWas=false;hvTabSet('hv')}}
  /* הפסקה שעליה עומדים: הסמן בעריכה, ואחרת הפסקה שבמרכז המסך */
  function hvFlowEl(){
    const f=$('#flow'),s=getSelection();
    if(EDIT&&s&&s.rangeCount){let n=s.anchorNode;if(n&&n.nodeType===3)n=n.parentElement;
      const e=n&&n.closest&&f&&f.contains(n)?n.closest('[data-ek]'):null;if(e)return e}
    if(!f)return null;
    const fr=f.getBoundingClientRect(),cx=fr.left+fr.width/2,cy=fr.top+fr.height/2;
    for(const dx of [0,-40,40,-90,90,-160,160]){
      const e=document.elementFromPoint(cx+dx,cy),r=e&&e.closest?e.closest('.row'):null;
      const p=r&&r.querySelector('[data-ek]');if(p)return p}
    return null}
  window.hvTabSet=function(t){
    const box=$('#srcx');if(!box||!hvTabOk())return;
    const w=box.querySelector('#hvtw'),b=box.querySelector('.srcbody');if(!w)return;
    HV.tab=t==='hv';
    if(HV.tab&&HV.on)hvClose();                      /* תצוגה אחת בכל רגע: הלוח שבצד נסגר */
    w.hidden=!HV.tab;if(b)b.style.display=HV.tab?'none':'';
    box.querySelectorAll('#ss-prev,#ss-next,#ssync,#sback').forEach(x=>{x.style.visibility=HV.tab?'hidden':''});
    const a=$('#st-per'),h=$('#st-hv');if(a)a.classList.toggle('on',!HV.tab);if(h)h.classList.toggle('on',HV.tab);
    if(!HV.tab){if(SRCSYNC)srcSyncNow();srcTitle();return}
    const hd=box.querySelector('.srchd b');if(hd)hd.textContent='חברותא';
    HV.pin=0;
    const el=hvFlowEl();
    if(el)hvFollow(el);
    else hvOpenDaf((D.pages[(SEC[cur]||{from:0}).from]||{}).daf||hvDafs()[0]||'',null)};
  /* המגירה נסגרה: הלשונית אינה פעילה (אין מעקב ואין טעינות), ונפתחת שוב כשהמגירה נפתחת */
  function hvTabOff(){HV.tabWas=HV.tab;HV.tab=false}
  /* דף קודם / הבא במגירה כשהלשונית פתוחה */
  function hvTabPage(d){if(!HV.tab)return false;hvPage(d);return true}
  document.addEventListener('keydown',e=>{
    if(!e.altKey||e.ctrlKey||e.metaKey||e.shiftKey||e.code!=='KeyJ'||!hvTabOk())return;
    e.preventDefault();e.stopPropagation();
    if(!$('#srcx')){gemaraBtn();if(!$('#srcx'))return;hvTabSet('hv');return}
    hvTabSet(HV.tab?'per':'hv')},true);
