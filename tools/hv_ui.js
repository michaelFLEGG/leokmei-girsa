  /* =================== חברותא בצד ההערה (19.10.2026) ===================
     נטען אחרי skira_ui.js ובאותו היקף. מנהל בלבד: הנתונים נמשכים מ-/hv/page במפתח המנהל ואינם בקובצי האתר.
     מציג בצד את שורות ביאור חברותא הרלוונטיות להערה הפעילה, ואת ההערות שהיא מפנה אליהן.
     חומר עיון בלבד: אין העתקה לנוסח, ואין הדפסה (הלוח מוסתר בהדפסה). */
  const HV={on:(function(){try{return localStorage.getItem('lg-hv-on')==='1'}catch(e){return false}})(),cache:{}};
  const HVG={'א':1,'ב':2,'ג':3,'ד':4,'ה':5,'ו':6,'ז':7,'ח':8,'ט':9,'י':10,'כ':20,'ל':30,'מ':40,'נ':50,'ס':60,'ע':70,'פ':80,'צ':90,'ק':100};
  function hvKey(d){d=String(d||'').trim();const side=/:$/.test(d)?1:0;let n=0;for(const ch of d.replace(/[^א-ת]/g,''))n+=HVG[ch]||0;return n?n*2+side:null}
  function hvX(t){return String(t).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}
  function hvCss(){if(document.getElementById('hvcss'))return;const st=document.createElement('style');st.id='hvcss';
    st.textContent='#hvx{position:fixed;top:0;left:0;width:min(440px,92vw);height:100%;background:#fffdf4;border-right:2px solid #7a5a00;z-index:1190;overflow:auto;padding:8px 10px 40px;box-sizing:border-box;font-size:15px;line-height:1.55;direction:rtl;box-shadow:2px 0 12px rgba(0,0,0,.25)}'+
      '#hvx h4{margin:0 0 4px;font-size:15px;color:#7a5a00;display:flex;justify-content:space-between;align-items:center}#hvx h4 button{font:inherit;border:1px solid #b9a97c;background:#f6f1e2;border-radius:5px;cursor:pointer;padding:0 8px}'+
      '#hvx .warn{font-size:12px;color:#8a3b2f;margin-bottom:6px}#hvx .sg{padding:4px 6px;border-radius:5px;margin:3px 0;border:1px solid transparent}#hvx .sg.ref{background:#fff0c4;border-color:#d9b84c}#hvx .sg.near{background:#faf5e3}'+
      '#hvx .sg b{color:#000}#hvx .sg .k{font-size:11px;color:#7a5a00;margin-left:4px}#hvx .nt{font-size:13px;margin:4px 0;padding:3px 6px;border-right:3px solid #2e5b8a;background:#eef3f9}#hvx .dim{font-size:12px;color:#8a7d66}'+
      '@media print{#hvx{display:none!important}}';document.head.appendChild(st)}
  async function hvLoad(daf){
    const key=hvKey(daf);if(key==null)return null;const c=Math.floor(key/12),ck=SLUG+'|'+daf;
    if(ck in HV.cache)return HV.cache[ck];
    let pg=null;
    try{const r=await api('/hv/page?slug='+encodeURIComponent(SLUG)+'&daf='+encodeURIComponent(daf)+'&c='+c);pg=r&&r.found?r.page:null}catch(e){pg=null}
    HV.cache[ck]=pg;return pg}
  function hvRefs(f){
    const t=(f&&f.note||'')+' '+(f&&f.evidence||'');const ks=[],ns=[];let m;
    const re1=/חברותא\s+[^\s\d\]]+\s+שורה\s+(\d+)/g;while((m=re1.exec(t)))ks.push(+m[1]);
    const re2=/חברותא\s+[^\s\d\]]+\s+הערה\s+(\d+)/g;while((m=re2.exec(t)))ns.push(+m[1]);
    return {ks,ns}}
  window.hvClose=function(){const p=document.getElementById('hvx');if(p)p.remove()};
  window.hvToggle=function(){HV.on=!HV.on;try{localStorage.setItem('lg-hv-on',HV.on?'1':'0')}catch(e){}
    if(!HV.on)hvClose();else{const f=BK.byId[BK.curId]||BK.ord[0];if(f)hvShow(f)}
    if(typeof bkBarDraw==='function')bkBarDraw()};
  window.hvShow=async function(f){
    if(!HV.on||!f)return;hvCss();
    const daf=(f.daf||'').trim();let p=document.getElementById('hvx');
    if(!p){p=document.createElement('div');p.id='hvx';document.body.appendChild(p)}
    p.innerHTML='<h4><span>חברותא · '+hvX(daf)+'</span><button onclick="hvToggle()">×</button></h4><div class="dim">טוען...</div>';
    const pg=await hvLoad(daf);
    if(!BK.curId||(BK.byId[BK.curId]&&BK.byId[BK.curId].id!==f.id))return;
    if(!pg){p.innerHTML='<h4><span>חברותא · '+hvX(daf)+'</span><button onclick="hvToggle()">×</button></h4><div class="dim">אין חומר חברותא לעמוד הזה (או שטרם הועלה).</div>';return}
    const R=hvRefs(f);let hit=pg.segs.filter(s=>R.ks.indexOf(s.k)>=0).map(s=>s.k);
    if(!hit.length){const ps=pg.segs.filter(s=>s.p===f.i);hit=ps.map(s=>s.k)}      /* אחרת: השורות שהותאמו לפסקה */
    const lo=hit.length?Math.min.apply(null,hit)-2:0,hi=hit.length?Math.max.apply(null,hit)+2:Math.min(pg.segs.length-1,12);
    let h='<h4><span>חברותא · '+hvX(daf)+'</span><button onclick="hvToggle()">×</button></h4>'+
      '<div class="warn">חומר עיון למנהל בלבד. לא מועתק לנוסח, לא מתפרסם ולא מודפס.</div>';
    pg.segs.forEach(s=>{if(s.k<lo||s.k>hi)return;
      const cl=hit.indexOf(s.k)>=0?'ref':(s.p===f.i?'near':'');
      h+='<div class="sg '+cl+'"><span class="k">שורה '+s.k+(s.p==null?' · בלי מקבילה בקיצור':'')+'</span>'+(s.g?'<b>'+hvX(s.g)+'</b> ':'')+hvX(s.e)+'</div>'});
    const nn=pg.notes.filter(n=>R.ns.indexOf(n.n)>=0);
    if(nn.length){h+='<h4><span>הערות</span></h4>';nn.forEach(n=>{h+='<div class="nt"><span class="dim">הערה '+n.n+' · '+hvX((n.src||[]).join(', '))+'</span><br>'+hvX(n.t)+'</div>'})}
    if(pg.url)h+='<div class="dim" style="margin-top:8px">מקור: ביאור חברותא, פרשני, ויקישיבה (CC BY-NC 3.0)</div>';
    p.innerHTML=h;
    const first=p.querySelector('.sg.ref');if(first&&first.scrollIntoView)first.scrollIntoView({block:'center'})};
  /* הצמדה: כל מעבר בין הערות (skAfterGo) מרענן את הלוח; כפתור ההפעלה בסרגל */
  (function(){
    const prevGo=window.skAfterGo;
    window.skAfterGo=function(f){if(typeof prevGo==='function')prevGo(f);try{hvShow(f)}catch(e){}};
    const prevBar=window.skBarExtra;
    window.skBarExtra=function(m){if(typeof prevBar==='function')prevBar(m);if(!m)return;
      m.insertAdjacentHTML('beforeend','<button class="'+(HV.on?'on':'')+'" onclick="hvToggle()" title="ביאור חברותא בצד ההערה (חומר עיון למנהל בלבד)">חברותא</button>')};
  })();
