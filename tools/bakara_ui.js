  /* =================== בקרת תוכן בתוך הדף (6.10.2026) ===================
     נטען בסוף הסקריפט (אחרי suggest_ui.js), ורק במסכת שיש לה קובץ ממצאי בקרה.
     גלוי למנהל בלבד: הממצאים אינם בקובצי האתר ואינם ב-HTML. הם נמשכים מנקודת
     הקליטה (מוגנת במפתח המנהל) רק אחרי שהמכשיר הוכר. לומד רגיל אינו מקבל
     כפתור, סימון, ואף לא בקשת רשת.

     הלימוד במקום: כשהמצב דלוק, מקום כל ממצא ממתין מסומן בקו תחתון דק לפי
     חומרה. הסימון הוא CSS Custom Highlight - אינו משנה את ה-DOM, ולכן אינו
     מזיז שורה, אינו משנה גובה ואינו נוגע בעריכה. ריחוף או נגיעה פותחים כרטיס
     צף (אשר / דחה / ערוך). העיגון לפי ההקשר והסימון בתוך היחידה, לעולם לא לפי
     מספר פסקה בלבד; ממצא שלא אותר עולה ל"שלא אותרו" ואינו נתלה בשורה אחרת.
     אישור של החלפה נעשה בעריכת מנהל רגילה (אותו נתיב של הצעות התיקון), וכל
     הכרעה נשמרת בנקודת הקליטה, ולכן נראית מכל מכשיר. */
  const BK={ON:false,CH:[],F:[],DEC:{},CAT:{},loaded:false,err:'',loc:{},byId:{},ord:[],
            curId:'',pin:false,FIL:{st:'pend',sev:'',det:''},undo:null,busy:false,R:[],
            OUT:'lg-bk-out-'+SLUG};
  const BKSEV={'חמור':['#c0392b','bk-hi'],'בינוני':['#c9770f','bk-mid'],'קל':['#6f7f9a','bk-lo']};
  /* סוגי הערות קבועים (סקירה, 13.10.2026): כל ממצא שייך לסוג אחד. typ מפורש גובר; אחרת לפי הגלאי */
  const SKT={a:['טעות בפשט','#b3261e'],b:['חסר שלב','#c9770f'],c:['לא מובן','#8a5a00'],d:['כותרת','#2e5b8a'],
             e:['ניסוח','#6a4c93'],f:['מבנה','#2e6b3f'],g:['מכני','#6f7f9a'],h:['שאלה למחבר','#0b7285'],i:['בחר נוסח','#a0527c'],j:['המפרשים חלוקים','#7a5a00']};
  const SKMAP={sem_hav:'a',sem_yih:'a',sem_hsr:'b',sem_lo:'c',cl_head:'d',nose_long:'d',
    aram:'e',cl_aram:'e',sem_hash:'e',hash:'e',amor_long:'e',cl_adv:'e',
    cl_mnum:'f',cl_hdr:'f',anchor:'f',cl_src:'f',cl_daf:'f',dafpos:'f',
    joined:'g',split:'g',dbl:'g',typo:'g',orphan:'g',punct:'g',abbr:'g',amor_miss:'g',psuk_bad:'g',psuk_nik:'g',psuk_miss:'g',
    sem_mil:'g',sem_sty:'g',cl_sty:'g',cl_cit:'g',cl_txt:'g',cl_bug:'g',alt:'i'};
  function bkTyp(f){return f.typ&&SKT[f.typ]?f.typ:(SKMAP[f.det]||'g')}
  /* סוגים שמותר לאשר בגורף: רק מכני ומבנה. בסוגים א-ג אין אישור גורף */
  const SKBULK={f:1,g:1};
  const SKWHY=[['no_err','לא טעות'],['my_way','כך אני כותב'],['unimp','לא חשוב'],['not_get','קלוד לא הבין את הסוגיה'],['not_here','נכון אבל לא כאן']];
  const BKX=/[֑-ׇ\s◄​-‏‪-‮]/;
  function bkCompact(t){let c='';const m=[];t=t||'';for(let i=0;i<t.length;i++){const ch=t[i];if(BKX.test(ch))continue;c+=ch;m.push(i)}return {c,m}}
  const BKCC=new Map();
  function bkCC(t){let v=BKCC.get(t);if(!v){v=bkCompact(t);if(BKCC.size>6000)BKCC.clear();BKCC.set(t,v)}return v}
  function bkStatus(f){const d=BK.DEC[f.id];return d?d.d:'pending'}
  function bkSplitNote(f){const i=(f.note||'').indexOf(' · בגמרא: ');
    return i<0?{n:f.note||'',e:''}:{n:f.note.slice(0,i),e:f.note.slice(i+10)}}
  /* מטען ההחלה (19.10.2026): כל ממצא נושא פעולה מוכנה, ו"קבל" מחיל אותה תמיד.
     f.op מובנה (נכתב בידי המנוע: tools/bakara/ops.py): {rep:{x,y}} | {ins:{after|before|end,text,cs}} | {style:{range,cs}} | {del:{range}} | {none:'סיבה'}.
     בלעדיו: החלפה "ישן ⟵ חדש" וסגנון מתוך הנוסח הישן של ההצעה. אין עוד מצב של "אושר לביצוע". */
  function bkRepFix(f){const fx=(f.fix||'').trim();
    if(fx.split('⟵').length!==2||fx.indexOf(';')>-1)return null;
    const p=fx.split('⟵'),x=p[0].trim();let y=p[1].trim();
    const unsure=/\s\?$/.test(y);if(unsure)y=y.replace(/\s\?$/,'').trim();
    if(!x||!y||x===y)return null;return {x,y,unsure}}
  function bkOp(f){
    if(f._op!==undefined)return f._op;
    let op=null;const o=f.op;
    if(o){
      if(o.rep&&o.rep.x&&o.rep.y!==undefined&&o.rep.x!==o.rep.y)op={t:'rep',x:o.rep.x,y:o.rep.y,unsure:!!o.rep.unsure};
      else if(o.ins&&o.ins.text)op={t:'ins',after:o.ins.after,before:o.ins.before,end:!!o.ins.end,text:String(o.ins.text),cs:o.ins.cs||'hs'};
      else if(o.style&&(o.style.cs||o.style.cs===''))op={t:'style',cs:o.style.cs==='plain'?'':o.style.cs,range:o.style.range||''};
      else if(o.del&&o.del.range)op={t:'rep',x:o.del.range,y:''};
      else if(o.ask)op={t:'q',why:String(o.ask)};
      else if(o.none)op={t:'none',why:String(o.none)}}
    if(!op){const rp=bkRepFix(f);if(rp)op={t:'rep',x:rp.x,y:rp.y,unsure:rp.unsure}}
    if(!op){const fx=f.fix||'';
      if(/^להחיל סגנון אמוראים/.test(fx))op={t:'style',cs:'am',range:f.mark||''};
      else if(/^להחיל סגנון פסוק/.test(fx))op={t:'style',cs:'ps',range:f.mark||''};
      else if(/^להחזיר לסגנון רגיל/.test(fx))op={t:'style',cs:'',range:f.mark||''}}
    if(!op&&bkTyp(f)==='h')op={t:'q'};
    if(!op)op={t:'none',why:''};
    f._op=op;return op}
  function bkRep(f){const o=bkOp(f);return o.t==='rep'?o:null}
  function bkAction(f){
    const o=bkOp(f);
    if(o.t==='style')return o.cs==='am'?'am':(o.cs==='ps'?'ps':'plain');
    return o.t}
  const BKACT={rep:'החלפה בנוסח',ins:'הוספת הסבר בסוגריים',am:'סגנון אמוראים',ps:'סגנון פסוק',plain:'חזרה לסגנון רגיל',q:'בדיקה או שאלה: אין שינוי בטקסט',none:'אין עדיין הצעה מוכנה'};
  /* ---- התיישנות (19.10.2026): ממצא שהטקסט הנוכחי (כולל עריכות המנהל) כבר מכסה אותו אינו מוצג ---- */
  const BKUSE=/^[ודלכמשבה]{1,3}(?=ר)/;
  function bkSlotHtml(s){const old=ED.find(x=>x.k===s.k);return old?(old.nowH!==undefined?old.nowH:esc(old.now)):s.h}
  /* לכל תו בטקסט: מחלקת הסגנון שלו ('am' / 'ps' / ...), לפי אותו HTML שעל המסך */
  function bkCharClasses(h){
    const d=document.createElement('div');d.innerHTML=h;
    const w=document.createTreeWalker(d,NodeFilter.SHOW_TEXT),cl=[];let n,t='';
    while(n=w.nextNode()){const el=n.parentElement&&n.parentElement.closest('i[class]');
      const c=el?el.className:'';
      for(let i=0;i<n.nodeValue.length;i++)cl.push(c);t+=n.nodeValue}
    return {t,cl}}
  function bkStale(f,L){
    const o=bkOp(f),s=L.s,h=bkSlotHtml(s),T=bkCharClasses(h),text=T.t;
    if(o.t==='style'){
      const hit=bkFindIn(text,f);if(!hit||!hit.len)return false;
      let a=0;const mk=bkCompact(text).c.slice(hit.pos,hit.pos+hit.len);
      const u=BKUSE.exec(mk);if(o.cs==='am'&&u)a=u[0].length;
      const want=o.cs==='ps'?'ps':'am';
      let any=false,all=true;
      for(let i=a;i<hit.len;i++){const oi=hit.sc.m[hit.pos+i],c=' '+(T.cl[oi]||'')+' ';
        const on=(o.cs===''?/ (am|ps|hs|dm|ns) /.test(c):c.indexOf(' '+want+' ')>-1);
        if(on)any=true;else all=false}
      return o.cs===''?!any:all}
    if(o.t==='ins'){
      const tx=bkCompact(o.text).c;if(tx.length<4)return false;
      return bkCompact(text).c.indexOf(tx)>-1}
    if(o.t==='rep'){
      const hit=bkFindIn(text,f);
      const xc=bkCompact(o.x).c,yc=bkCompact(o.y).c;
      if(hit){const within=bkCompact(text).c.slice(hit.pos,hit.pos+hit.len);
        if(within.indexOf(xc)<0&&yc&&bkCompact(text).c.indexOf(yc)>-1&&bkCompact(text).c.indexOf(xc)<0)return true}
      return false}
    return false}
  /* ממצא שלא אותר: אם נוסח ההחלפה כבר במקום - התיישן (ולא "אבד") */
  function bkStaleLost(f,S){
    const o=bkOp(f);if(o.t!=='rep'||!o.y)return false;
    const cx=bkCompact((f.context||f.text||'').replace(o.x,o.y)).c,yc=bkCompact(o.y).c;
    if(!cx||cx.indexOf(yc)<0)return false;
    const k0=dafKey(f.daf);
    for(const s of S){const k=dafKey(s.daf);if(k0!==null&&k!==null&&Math.abs(k-k0)>1)continue;
      if(bkCompact(plain(bkSlotHtml(s))).c.indexOf(cx)>-1)return true}
    return false}
  BK.STALE=new Set();

  /* ---- עיגון ---- */
  function bkFindIn(text,f){
    const cx=bkCC(f.context||f.text||''),mk=bkCompact(f.mark||'').c,sc=bkCC(text);
    let pos=-1,len=mk.length;
    if(cx.c){const p=sc.c.indexOf(cx.c);
      if(p>-1){const off=mk?cx.c.indexOf(mk):0;pos=p+(off>-1?off:0);if(!mk||off<0)len=mk?mk.length:cx.c.length}}
    if(pos<0&&mk){const p=sc.c.indexOf(mk);if(p>-1&&sc.c.indexOf(mk,p+1)<0)pos=p}
    return pos<0?null:{pos,len,sc}}
  function bkLocateAll(){
    const S=slotsFull();BK.loc={};BK.ord=[];BK.STALE=new Set();
    const idx=new Map();S.forEach((s,i)=>idx.set(s,i));
    for(const f of BK.F){
      const own=S.filter(s=>String(s.id)===String(f.u));
      let hits=own.map(s=>[s,bkFindIn(s.t,f)]).filter(x=>x[1]);
      if(hits.length!==1){
        const k0=dafKey(f.daf);
        const win=S.filter(s=>{const k=dafKey(s.daf);return k0===null||k===null||Math.abs(k-k0)<=1});
        const all=win.map(s=>[s,bkFindIn(s.t,f)]).filter(x=>x[1]);
        if(all.length>hits.length||!hits.length)hits=all;
        if(hits.length>1){hits.sort((a,b)=>Math.abs(a[0].id-f.u)-Math.abs(b[0].id-f.u))}}
      if(!hits.length){if(bkStatus(f)==='pending'&&bkStaleLost(f,S))BK.STALE.add(f.id);continue}
      const [s,h]=hits[0];
      BK.loc[f.id]={s,k:s.k,pi:s.pi,pos:h.pos,len:h.len,ord:idx.get(s)*100000+h.pos};
      if(bkStatus(f)==='pending'&&bkStale(f,BK.loc[f.id]))BK.STALE.add(f.id)}
    BK.ord=BK.F.filter(f=>BK.loc[f.id]&&!BK.STALE.has(f.id)).sort((a,b)=>BK.loc[a.id].ord-BK.loc[b.id].ord)}
  /* מיקום ב-DOM: טווח סימון בתוך האלמנט, לפי אותו מדד דחוס */
  function bkDomRange(f){
    const L=BK.loc[f.id];if(!L)return null;
    const el=$('#flow').querySelector('[data-ek="'+L.k+'"]');if(!el)return null;
    const nodes=[];const w=document.createTreeWalker(el,NodeFilter.SHOW_TEXT,{acceptNode(n){
      return n.parentElement&&n.parentElement.closest('.srcb,.mlabel')?NodeFilter.FILTER_REJECT:NodeFilter.FILTER_ACCEPT}});
    let n,text='';const at=[];
    while(n=w.nextNode()){for(let i=0;i<n.nodeValue.length;i++)at.push([n,i]);text+=n.nodeValue}
    const h=bkFindIn(text,f);if(!h||!h.len)return null;
    const a=at[h.sc.m[h.pos]],b=at[h.sc.m[h.pos+h.len-1]];
    if(!a||!b)return null;
    const r=document.createRange();r.setStart(a[0],a[1]);r.setEnd(b[0],b[1]+1);return {range:r,el}}

  /* ---- סימון בטקסט ---- */
  function bkCss(){if(document.getElementById('bkcss'))return;
    const st=document.createElement('style');st.id='bkcss';
    st.textContent=
      Object.keys(SKT).map(k=>'::highlight(bk-t'+k+'){text-decoration:underline;text-decoration-color:'+SKT[k][1]+';text-decoration-thickness:'+(k==='g'?1:2)+'px;text-underline-offset:3px}').join('')+
      '::highlight(bk-todo){text-decoration:underline dotted;text-decoration-color:#2e5b8a;text-decoration-thickness:2px;text-underline-offset:3px}'+
      '::highlight(bk-cur){background-color:rgba(201,162,74,.38)}'+
      '#bkbtn2.on{background:#2e5b8a;color:#fff}#bkbtn2 .bkn{background:#c0392b;color:#fff;border-radius:9px;padding:0 6px;margin-right:4px;font-size:12px}'+
      '.bkcard{position:fixed;z-index:9;width:min(340px,94vw);background:#fffdf8;border:1px solid #c9b98f;border-radius:8px;box-shadow:0 6px 22px rgba(0,0,0,.28);padding:9px 12px;font-size:15px;line-height:1.5;direction:rtl}'+
      '.bkcard .h{display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-bottom:3px}.bkcard .h .x{margin-right:auto;background:none;border:0;font-size:20px;cursor:pointer;color:#5a5044;line-height:1}'+
      '.bkchip{display:inline-block;color:#fff;border-radius:10px;padding:0 8px;font-size:12px}.bkcard .nt{font-weight:600}.bkcard .ev{font-size:13px;color:#5a5044;border-right:3px solid #d9d1bd;padding-right:7px;margin:3px 0}'+
      '.bkcard .fx{margin:4px 0;background:#f3efe3;border-radius:4px;padding:3px 7px;font-size:15px}.bkcard del{color:#a83c2f;background:#fbe5e1}.bkcard ins{color:#2e6b3f;background:#e3f3e6;text-decoration:none}.bkcard ins.hs{color:#4a4137;font-size:.92em}.bkcard .fx.dim{background:none;color:#8a7d66;font-size:13px}'+
      '.bkcard .bt{display:flex;gap:6px;margin-top:6px;flex-wrap:wrap}.bkcard .bt button{font:inherit;font-size:14px;border:1px solid #b9a97c;border-radius:5px;background:#f6f1e2;padding:2px 12px;cursor:pointer}'+
      '.bkcard .bt button.ok{background:#2e6b3f;color:#fff;border-color:#2e6b3f}.bkcard .bt button.no{color:#a83c2f}.bkcard input[type=text]{width:100%;box-sizing:border-box;font:inherit;font-size:14px;margin-top:5px}'+
      '.bkcard .dim{font-size:12px;color:#8a7d66}.bkcard .kk{font-size:10px;opacity:.7;margin-right:3px;direction:ltr;unicode-bidi:isolate}'+
      '.bkbar{position:fixed;left:12px;bottom:12px;z-index:7;background:#fffdf8;border:1px solid #c9b98f;border-radius:8px;box-shadow:0 3px 14px rgba(0,0,0,.22);padding:5px 10px;font-size:14px;display:flex;gap:8px;align-items:center;flex-wrap:wrap;direction:rtl;max-width:94vw}'+
      'body.ed .bkbar{bottom:56px}.bkbar button{font:inherit;font-size:14px;border:1px solid #b9a97c;border-radius:5px;background:#f6f1e2;padding:1px 10px;cursor:pointer}.bkbar button.go{background:#2e5b8a;color:#fff;border-color:#2e5b8a}'+
      '#bkp .grp{margin:8px 0;border:1px solid #e0d8c4;border-radius:6px;background:#fff}#bkp .grp>summary{cursor:pointer;padding:4px 8px;font-weight:600}'+
      '#bkp .grp .gb{padding:0 8px 6px}#bkp .it{padding:4px 6px;border-bottom:1px dotted #d9d1bd;cursor:pointer}#bkp .it:hover{background:#f6f1e2}#bkp .it.cur{outline:2px solid #c9a24a}'+
      '#bkp .it small{color:#8a7d66}#bkp .it .mk{font-weight:600;color:#2b2620}#bkp select{font:inherit;font-size:14px;margin:2px}#bkp .gbt button{font:inherit;font-size:13px;margin:2px 0 2px 4px;border:1px solid #b9a97c;border-radius:5px;background:#f6f1e2;padding:1px 9px;cursor:pointer}'+
      '@media print{.bkcard,.bkbar{display:none!important}}';
    document.head.appendChild(st)}
  function bkHL(){
    const f=$('#flow');BK.R=[];
    if(!window.CSS||!CSS.highlights||typeof Highlight==='undefined')return;
    const H={'bk-todo':new Highlight(),'bk-cur':new Highlight()};Object.keys(SKT).forEach(k=>{H['bk-t'+k]=new Highlight()});
    if(BK.ON&&f&&!f.classList.contains('book')){
      for(const fd of BK.ord){
        if(SK.mode&&fd.id!==BK.curId)continue;
        const st=bkStatus(fd);if(st!=='pending'&&st!=='todo')continue;
        const r=bkDomRange(fd);if(!r)continue;
        BK.R.push({f:fd,range:r.range,el:r.el});
        H[st==='todo'?'bk-todo':'bk-t'+bkTyp(fd)].add(r.range);
        if(fd.id===BK.curId)H['bk-cur'].add(r.range)}}
    for(const k in H){if(H[k].size)CSS.highlights.set(k,H[k]);else CSS.highlights.delete(k)}}
  let BKT=null;function bkSoon(){if(!BK.ON)return;clearTimeout(BKT);BKT=setTimeout(()=>{bkRefresh()},220)}
  function bkRefresh(){if(!BK.loaded)return;bkLocateAll();bkHL();bkCount();if($('#bkp')&&$('#bkp').classList.contains('open'))skDrawPanel();if(SK.mode)skPassDraw();else bkBarDraw();if(window.skAutoSoon)skAutoSoon()}
  window.bkMark=function(){if(BK.loaded&&BK.ON){bkLocateAll();bkHL();bkCount();bkBarDraw()}};
  (function(){const f=document.getElementById('flow');if(!f||!window.MutationObserver)return;
    new MutationObserver(()=>bkSoon()).observe(f,{childList:true,subtree:true,characterData:true})})();

  /* ---- טעינה: רק למכשיר שהוכר כמנהל ---- */
  function bkPend(f){return bkStatus(f)==='pending'&&!(SK.autoQ&&SK.autoQ.has(f.id))&&!BK.STALE.has(f.id)}
  function bkCount(){
    const b=$('#bkbtn2');if(!b)return;
    if(!isAdmin()||!BK.has){b.style.display='none';return}
    b.style.display='';
    if(!admKey()){b.textContent='סקירה - הזן מפתח';return}
    if(!BK.loaded){b.textContent=BK.err?'סקירה (שגיאה)':'סקירה…';b.title=BK.err||'';return}
    const sec=SEC[cur]||{from:0,to:0};
    let nSec=0,nAll=0;
    for(const f of BK.F){if(!bkPend(f))continue;nAll++;const L=BK.loc[f.id];if(L&&L.pi>=sec.from&&L.pi<=sec.to)nSec++}
    b.innerHTML='סקירה'+(nSec?'<span class="bkn">'+nSec+'</span>':'');
    b.title='ממצאי בקרה: '+nSec+' ממתינים בפרק הפתוח, '+nAll+' בכל המסכת';
    b.classList.toggle('on',BK.ON)}
  async function bkLoad(){
    if(!isAdmin()||!admKey()||BK.busy)return;BK.busy=true;
    try{
      const d=await api('/bakara/data?slug='+SLUG),c=await api('/bakara/dec?slug='+SLUG);
      const prevIds=BK.loaded?new Set(Object.keys(BK.byId)):null;
      BK.CH=[];BK.F=[];BK.CAT={};BK.byId={};BK.AUTOLOG=[];
      const pk=(d.doc&&d.doc.perakim)||{};
      for(const p of Object.keys(pk).sort((a,b)=>a-b)){
        const ch=pk[p];/* ד"ה משנה בתוך שורה אינו ממצא (הכרעה 6.10.2026): הוא נשאר בשורה, בסגנון ד"ה משנה לא ממורכז */
        const fl=(ch.findings||[]).filter(f=>f.det!=='dh_inline');
        BK.CH.push({perek:+p,range:ch.range,n:fl.length});
        (ch.catalog||[]).forEach(x=>{BK.CAT[x[0]]=x});
        if(ch.rules)BK.RULES=ch.rules;if(ch.costs)BK.COSTS=ch.costs;
        (ch.auto||[]).forEach(x=>BK.AUTOLOG.push(x));
        for(const f of fl){f.perek=+p;BK.F.push(f);BK.byId[f.id]=f}}
      BK.has=BK.F.length>0;
      BK.DEC=(c.doc&&c.doc.dec)||{};
      /* הכרעות שטרם נשלחו (אין חיבור): חדשות מן השרת גוברות רק אם מאוחרות */
      for(const it of bkOutbox()){const o=BK.DEC[it.id];if(!o||(o.t||0)<=it.t){if(it.d==='pending')delete BK.DEC[it.id];else BK.DEC[it.id]=it}}
      BK.loaded=true;BK.err='';bkFlush();
      BK.prevIds=prevIds;
    }catch(e){BK.err=e.message||'שגיאה';if(/אין הרשאה/.test(BK.err)){BK.has=BK.has||false}}
    BK.busy=false;bkCount();if(BK.ON)bkRefresh();if(window.skAfterLoad)skAfterLoad()}
  function bkOutbox(){try{return JSON.parse(localStorage.getItem(BK.OUT)||'[]')}catch(e){return[]}}
  function bkOutSave(a){try{localStorage.setItem(BK.OUT,JSON.stringify(a.slice(-500)))}catch(e){}}
  async function bkFlush(){
    const a=bkOutbox();if(!a.length||!admKey())return;
    try{await api('/bakara/dec',{method:'POST',body:JSON.stringify({slug:SLUG,items:a.slice(0,300)})});
      const left=bkOutbox().filter(x=>!a.some(y=>y.id===x.id&&y.t===x.t));bkOutSave(left)}
    catch(e){/* יישלח בפעם הבאה */}}
  /* רישום הכרעה: מיד במכשיר, ובנקודת הקליטה בצד */
  function bkPut(f,d,txt,now,auto){
    const it={id:f.id,d,txt:txt||'',det:f.det,kind:f.kind,now:now||'',t:Date.now()};
    if(BK.autoNext){auto=BK.autoNext;BK.autoNext=''}
    if(auto){it.auto=1;it.rs=typeof auto==='string'?auto:'auto'}
    else if(BK.rs){it.rs=BK.rs;BK.rs=''}
    {const o=bkOp(f);const sg=o.t==='rep'?o.y:(o.t==='ins'?'['+bkInsText(o.text)+']':(f.fix||''));if(sg&&d!=='pending')it.sug=String(sg).slice(0,900)}
    if(d==='pending')delete BK.DEC[f.id];else BK.DEC[f.id]=it;
    const a=bkOutbox().filter(x=>x.id!==f.id);a.push(it);bkOutSave(a);return it}

  /* ---- כניסה ויציאה ---- */
  function bkToggle(){
    if(!isAdmin()){return}
    {const k=admKey();if(!k||/[^\x00-\xff]/.test(k)){
      try{localStorage.removeItem('lg-adm')}catch(e){}
      Promise.resolve(admKeyAsk()).then(ok=>{if(ok&&admKey())bkLoad().then(()=>{if(BK.loaded)bkToggle()})});return}}
    if(!BK.loaded){bkLoad().then(()=>{if(BK.loaded)bkToggle();else toast('לא ניתן לטעון את ממצאי הבקרה: '+(BK.err||'שגיאה'),5000)});return}
    BK.ON=!BK.ON;bkCss();
    if(!BK.ON){bkHideCard(true);const m=$('#bkbar');if(m)m.remove();{const x=$('#skpass');if(x)x.remove();SK.mode=''}bkHL();bkCount();return}
    bkRefresh();bkBarDraw();
    if(!BK.ord.length)toast('אין הערות סקירה למסכת הזאת. אפשר לבקש סקירה מהחלונית.')}
  window.bkToggle=bkToggle;
  function bkBarDraw(){
    if(!BK.ON)return;let m=$('#bkbar');
    if(!m){m=document.createElement('div');m.id='bkbar';m.className='bkbar';document.body.appendChild(m)}
    const dafN=bkDafNow();let nd=0,ns=0,na=0;const sec=SEC[cur]||{from:0,to:0};
    for(const f of BK.F){if(!bkPend(f))continue;na++;const L=BK.loc[f.id];if(!L)continue;
      if(L.pi>=sec.from&&L.pi<=sec.to)ns++;if(D.pages[L.pi]&&D.pages[L.pi].daf===dafN)nd++}
    const lost=BK.F.filter(f=>bkPend(f)&&!BK.loc[f.id]).length;
    m.innerHTML='<b>סקירה</b><span>בדף: '+nd+' · בפרק: '+ns+' · בכל המסכת: '+na+(lost?' · לא אותרו: '+lost:'')+bkStaleTxt()+'</span>'+
      skNextBtnHtml()+
      '<button onclick="bkNext(-1)" title="להערה הקודמת (רק בלחיצה מפורשת)">↑ הקודמת</button>'+
      '<button onclick="bkPanel()">רשימה</button><button onclick="bkToggle()">סיום</button><span class="kk" style="font-size:11px;opacity:.7" title="Enter קבל · Delete דחה · ←/→ הבאה/קודמת · E ערוך · C שוחח · S דלג · Ctrl+Z ביטול">Enter קבל · Del דחה · ←→ · E · C · S</span>';if(window.skBarExtra)skBarExtra(m);if(window.skBarEnd)skBarEnd(m)}
  function bkDafNow(){return (($('#curdaf')||{}).textContent||'').trim()}

  /* ---- כרטיס צף ---- */
  /* "לפני / אחרי": מה יקרה ב-Enter. ההוספה בצבע ובגודל ההסבר */
  function bkPreviewHtml(f){
    const o=bkOp(f),c=f.context||f.text||'';
    if(o.t==='rep')return '<div class="fx"><del>'+esc(o.x)+'</del> ⟵ <ins>'+esc(o.y)+'</ins>'+(o.unsure?' <span class="dim">(המערכת אינה בטוחה)</span>':'')+'</div>';
    if(o.t==='ins'){
      const a=o.end?'':(o.after||o.before||f.mark||'');const i=a?c.indexOf(a):-1;let pre=c,post='';
      if(!o.end&&i>-1){if(o.before!==undefined&&o.after===undefined){pre=c.slice(0,i);post=c.slice(i)}else{pre=c.slice(0,i+a.length);post=c.slice(i+a.length)}}
      return '<div class="fx"><b>לפני:</b> '+esc(c)+'</div><div class="fx"><b>אחרי:</b> '+esc(pre)+' <ins class="hs">['+esc(o.text)+']</ins> '+esc(post)+'</div>'}
    if(o.t==='style')return '<div class="fx">'+esc(BKACT[bkAction(f)])+': <mark>'+esc(o.range||f.mark||'')+'</mark></div>';
    if(o.t==='none')return (f.fix?'<div class="fx">'+esc(f.fix)+'</div>':'')+'<div class="fx dim">אין עדיין הצעה מוכנה לממצא הזה. Enter מבקש הצעה ועובר להערה הבאה; E לעריכה ידנית.</div>';
    if(o.t==='q')return (f.fix?'<div class="fx">'+esc(f.fix)+'</div>':'')+'<div class="fx dim">'+esc(o.why||'בדיקה')+'. Enter: נבדק, בלי שינוי בטקסט.</div>';
    return f.fix?'<div class="fx">'+esc(f.fix)+'</div>':''}
  function bkHideCard(force){
    const c=$('#bkcard');if(!c)return;
    if(BK.pin&&!force)return;
    c.remove();BK.pin=false;BK.cardId=''}
  function bkShowCard(f,pin,rect){
    if(SK.mode&&!window.SKCARD){return}
    const old=$('#bkcard');if(old&&old.dataset.id===f.id&&(!pin||BK.pin)){return}
    if(old)old.remove();
    const c=document.createElement('div');c.className='bkcard';c.id='bkcard';c.dataset.id=f.id;
    const sv=[SKT[bkTyp(f)][1]],st=bkStatus(f),sn=bkSplitNote(f),rp=bkRep(f);
    const dec=BK.DEC[f.id];
    let fx=bkPreviewHtml(f);
    const act=bkAction(f);
    c.innerHTML='<div class="h"><span class="bkchip" style="background:'+sv[0]+'">'+esc(SKT[bkTyp(f)][0])+' · '+esc(f.kind)+'</span><span class="dim">'+esc(f.sev)+' · '+esc(f.layer||'')+(f.conf?' · ביטחון '+esc(f.conf):'')+' · דף '+esc(f.daf||'')+'</span>'+
      '<button class="x" onmousedown="event.preventDefault()" onclick="bkHideCard(true)" aria-label="סגירה">×</button></div>'+
      '<div class="nt">'+esc(sn.n)+'</div>'+(sn.e?'<div class="ev">בגמרא: '+esc(sn.e)+'</div>':'')+fx+
      (st==='pending'||st==='todo'?
        '<div class="bt"><button class="ok" onmousedown="event.preventDefault()" onclick="bkAcceptClick(\''+f.id+'\')" title="'+esc(BKACT[act])+' - Enter">'+(act==='none'?'בקש הצעה ועבור':'קבל')+' <small class="kk">Enter</small></button>'+
        '<button class="no" onmousedown="event.preventDefault()" onclick="skRejectOpen(\''+f.id+'\')" title="דחה - Delete">דחה <small class="kk">Del</small></button>'+
        '<button onmousedown="event.preventDefault()" onclick="bkDecide(\''+f.id+'\',\'edit\')" title="ערוך וקבל - E (אחר כך Alt+Enter)">ערוך וקבל <small class="kk">E</small></button>'+
        '<button onmousedown="event.preventDefault()" onclick="skChat(\''+f.id+'\')" title="שוחח על ההערה - C">שוחח <small class="kk">C</small></button>'+
        '<button onmousedown="event.preventDefault()" onclick="skSkip(\''+f.id+'\')" title="דלג - מעבר להערה הבאה בלי הכרעה">דלג</button>'+
        (st==='todo'?'<button onmousedown="event.preventDefault()" onclick="bkDecide(\''+f.id+'\',\'ok\',1)">בוצע</button>':'')+'</div>'+
        '<div id="skwhy" class="skwhy" style="display:none">'+SKWHY.map(w=>'<button onmousedown="event.preventDefault()" onclick="skReject(\''+f.id+'\',\''+w[0]+'\')">'+w[1]+'</button>').join('')+
        '<input type="text" id="bkwhy" maxlength="300" placeholder="סיבה חופשית (לא חובה) ואז Enter" aria-label="נימוק" onkeydown="if(event.key===\'Enter\'){event.preventDefault();skReject(\''+f.id+'\',\'free\')}"></div>'+
        '<div id="skchat" class="skchat" style="display:none"></div>'
      :'<div class="dim">'+(dec?({ok:'התקבל',no:'נדחה',edit:'נערך',todo:'אושר לביצוע'}[dec.d]||''):'')+(dec&&dec.txt?' · '+esc(dec.txt):'')+'</div><div class="bt"><button onmousedown="event.preventDefault()" onclick="bkDecide(\''+f.id+'\',\'pending\')">החזר לממתינים</button><button onmousedown="event.preventDefault()" onclick="skChat(\''+f.id+'\')">שוחח</button></div><div id="skchat" class="skchat" style="display:none"></div>');
    document.body.appendChild(c);BK.pin=!!pin;BK.cardId=f.id;
    bkPlace(c,rect||bkRectOf(f));
    c.addEventListener('pointerenter',()=>{clearTimeout(BK.hideT)});
    c.addEventListener('pointerleave',()=>{if(!BK.pin)bkLater()})}
  function bkRectOf(f){const r=BK.R.find(x=>x.f.id===f.id);if(!r)return null;
    const rs=r.range.getClientRects();return rs.length?rs[0]:r.el.getBoundingClientRect()}
  /* בשוליים כשיש מקום (משמאל או מימין לטור הטקסט); אחרת מתחת לשורה, ואחרת מעליה. לעולם לא על השורה */
  function bkPlace(c,rc){
    const W=c.offsetWidth||340,Hh=c.offsetHeight||170,vw=innerWidth,vh=innerHeight,fr=$('#flow').getBoundingClientRect();
    if(!rc){c.style.top='80px';c.style.left=Math.max(8,vw-W-16)+'px';return}
    let top,left;
    if(fr.left>W+16){left=fr.left-W-8;top=Math.min(vh-Hh-8,Math.max(8,rc.top-10))}
    else if(vw-fr.right>W+16){left=fr.right+8;top=Math.min(vh-Hh-8,Math.max(8,rc.top-10))}
    else{/* אין שוליים: הכרטיס מעוגן בתחתית המסך מעל הסרגל, והשורה הבעייתית נגללת מעליו */
      const bar=$('#bkbar'),bh=bar?bar.offsetHeight+10:56;
      left=Math.max(8,Math.round((vw-W)/2));top=Math.max(8,vh-Hh-bh-6);
      c.style.left=left+'px';c.style.top=Math.round(top)+'px';
      const over=rc.bottom-(top-14);
      if(over>0||rc.top<70){const d=over>0?over:rc.top-90;try{window.scrollBy({top:d,behavior:'auto'})}catch(e){window.scrollBy(0,d)}}
      return}
    c.style.left=Math.round(left)+'px';c.style.top=Math.round(top)+'px'}
  function bkLater(){clearTimeout(BK.hideT);BK.hideT=setTimeout(()=>bkHideCard(false),380)}
  function bkHit(x,y){
    for(const r of BK.R){
      for(const q of r.range.getClientRects()){
        if(x>=q.left-3&&x<=q.right+3&&y>=q.top-4&&y<=q.bottom+5)return r}}
    return null}
  let BKMV=0,BKLAST=null;
  document.addEventListener('pointermove',e=>{
    if(!BK.ON||BK.pin||e.pointerType==='touch')return;
    const x=e.clientX,y=e.clientY;if(BKMV)return;
    BKMV=requestAnimationFrame(()=>{BKMV=0;
      if(!BK.ON)return;
      const t=document.elementFromPoint(x,y);
      if(!t||!t.closest('#flow')){if(BKLAST&&!(t&&t.closest('#bkcard'))){BKLAST=null;bkLater()}return}
      const h=bkHit(x,y);
      if(h){clearTimeout(BK.hideT);if(BKLAST!==h.f.id){BKLAST=h.f.id;bkShowCard(h.f,false,null)}}
      else if(BKLAST){BKLAST=null;bkLater()}})},{passive:true});
  document.addEventListener('click',e=>{
    if(!BK.ON)return;
    if(e.target.closest&&(e.target.closest('#bkcard')||e.target.closest('#bkbar')||e.target.closest('#bkp')))return;
    const h=e.target.closest&&e.target.closest('#flow')?bkHit(e.clientX,e.clientY):null;
    if(h){BK.curId=h.f.id;bkHL();if(!EDIT||e.pointerType==='touch'||BK.pin){bkShowCard(h.f,true,null)}else bkShowCard(h.f,false,null)}
    else if(BK.pin){bkHideCard(true)}},true);
  /* ---- קיצורי מקלדת לבקרה (6.10.2026): event.code, כדי שיעבדו גם בפריסה עברית.
     Alt+חץ מעלה/מטה: ממצא קודם/הבא · Enter לבדו: אשר (כשהמיקוד על הממצא ולא בתוך טקסט)
     Alt+Enter: אשר תמיד (ואם נפתחה עריכה - "נערך") · Alt+Delete / Alt+Backspace / Alt+2: דחה
     Alt+1: אשר · Alt+3: ערוך (Escape חוזר למיקוד על הממצא) ---- */
  function bkKbFinding(){
    const c=$('#bkcard');if(!c||!BK.curId||c.dataset.id!==BK.curId)return null;
    const f=BK.byId[BK.curId];if(!f)return null;
    const st=bkStatus(f);return (st==='pending'||st==='todo')?f:null}
  function bkBlurText(){const a=document.activeElement;if(a&&a!==document.body&&(a.isContentEditable||/^(INPUT|TEXTAREA|SELECT|BUTTON|A)$/.test(a.tagName)))a.blur()}
  /* אחרי הכרעה: לממצא הבא שטרם הוכרע בפרק הפתוח, בלי לחזור להתחלה */
  function bkAdvance(){bkBlurText();BK.kb=true;skNext(1)}
  async function bkKbDecide(f,d){
    /* שני מאזיני מקלדת (כאן וב-skira_ui) שומעים את אותו Enter: ההכרעה נעשית פעם אחת, ולא גם על הממצא הבא */
    if(BK.kbBusy&&Date.now()-BK.kbBusy<5000)return;
    BK.kbBusy=Date.now();
    try{
      const id=f.id,st=bkStatus(f);
      if(d==='edit-ok'){BK.editId='';await bkDecide(id,'edit',false,true)}
      else await bkDecide(id,d,0);   /* גם ממצא שנשאר מ"אושר לביצוע" ישן: Enter מחיל את המטען ("בוצע" רק בכפתור) */
      if(bkStatus(f)!=='pending'&&bkStatus(f)!==st)bkAdvance()}
    finally{BK.kbBusy=0}}
  document.addEventListener('pointerdown',e=>{if(BK.ON&&!(e.target.closest&&e.target.closest('#bkcard,#bkbar')))BK.kb=false},true);
  document.addEventListener('keydown',e=>{
    if(!BK.ON)return;
    if(e.code==='Escape'||e.key==='Escape'){
      if(BK.editId){const f=BK.byId[BK.editId];BK.editId='';BK.kb=true;e.preventDefault();e.stopPropagation();bkBlurText();
        if(f){BK.curId=f.id;bkHL();if(!$('#bkcard'))bkShowCard(f,true,bkRectOf(f));else BK.pin=true}return}
      if($('#bkcard')){bkHideCard(true);BK.kb=false;return}}
    if(e.metaKey||e.ctrlKey)return;
    const c=e.code;
    if(e.altKey&&!e.shiftKey&&(c==='ArrowDown'||c==='ArrowUp')){
      e.preventDefault();e.stopPropagation();BK.editId='';bkBlurText();BK.kb=true;bkNext(c==='ArrowDown'?1:-1);return}
    const f=bkKbFinding();if(!f)return;
    const hit=()=>{e.preventDefault();e.stopPropagation()};
    if(e.altKey&&!e.shiftKey){
      if(c==='Enter'||c==='NumpadEnter'){hit();bkKbDecide(f,BK.editId===f.id?'edit-ok':'ok');return}
      if(c==='Digit1'){hit();BK.editId='';bkKbDecide(f,'ok');return}
      if(c==='Digit2'||c==='Delete'||c==='Backspace'){hit();BK.editId='';bkKbDecide(f,'no');return}
      if(c==='Digit3'){hit();if(bkFocusEdit(f)){BK.editId=f.id;toast('עריכה על הקטע. Alt+Enter מאשר כ"נערך", Escape חוזר למיקוד על הממצא.',4000)}return}
      return}
    /* Enter לבדו: רק כשהמיקוד על הממצא - לא בתוך טקסט ולא על כפתור/שדה */
    if(!e.altKey&&!e.shiftKey&&(c==='Enter'||c==='NumpadEnter')&&BK.kb&&!BK.editId){
      const t=e.target;
      if(t&&(t.isContentEditable||/^(INPUT|TEXTAREA|SELECT|BUTTON|A)$/.test(t.tagName)))return;
      hit();bkKbDecide(f,'ok')}},true);
  addEventListener('scroll',()=>{if(!BK.pin)bkHideCard(true)},true);
  addEventListener('resize',()=>{if(BK.ON)bkSoon()});

  /* ---- ניווט (14.10.2026): מעבר אחד קדימה לפי סדר הטקסט. "הבא" הוא תמיד ההערה שאחרי הנוכחית,
     לעולם לא ההערה הפתוחה הראשונה. דילוג הוא החלטה: ההערה נדחית לסוף ואינה חוזרת במעבר הזה. ---- */
  function bkCurOrd(){
    const f=BK.byId[BK.curId]||BK.byId[SK.last];
    if(f&&BK.loc[f.id])return BK.loc[f.id].ord;
    if(SK.lastOrd!=null&&(SK.lastOrd>=0||SK.fromTop))return SK.lastOrd;
    /* אין נקודת עמידה: הממצא הראשון שנראה במסך, ואחרת תחילת הפרק */
    const fr=$('#flow').getBoundingClientRect();
    for(const r of BK.R){const q=r.range.getClientRects()[0];if(q&&q.bottom>fr.top&&q.top<fr.bottom&&q.right>fr.left&&q.left<fr.right)return BK.loc[r.f.id].ord-1}
    const sec=SEC[cur];const first=BK.ord.find(x=>BK.loc[x.id].pi>=sec.from);return first?BK.loc[first.id].ord-1:-1}
  function bkNext(dir){
    if(!BK.loaded){return}
    if(!BK.ON){bkToggle();return}
    skNext(dir)}
  window.bkNext=bkNext;
  function bkGo(id,card){
    const f=BK.byId[id];if(!f)return;const L=BK.loc[id];
    if(!L){toast('הממצא לא אותר: הטקסט השתנה מאז.');return}
    BK.curId=id;SK.last=id;SK.lastOrd=L.ord;SK.fromTop=false;skSavePos();
    const have=!!$('#flow').querySelector('[data-ek="'+L.k+'"]');
    if(!have)jump(L.pi,L.s.id);
    setTimeout(()=>{
      if(!SK.mode||!have)bkLocateAll();
      bkHL();
      const r=BK.R.find(x=>x.f.id===id);
      if(r){const fl=$('#flow');
        if(fl.classList.contains('vert'))r.el.scrollIntoView({block:'center'});else toEl(r.el);
        setTimeout(()=>{bkHL();if(card)bkShowCard(f,true,bkRectOf(f))},60)}
      if(SK.mode)skPassDraw();else bkBarDraw();if(window.skAfterGo)skAfterGo(f)},have?0:90)}
  window.bkGo=bkGo;

  /* ---- ההכרעות ---- */
  function bkSel(f){const r=bkDomRange(f);if(!r)return null;
    const s=getSelection();s.removeAllRanges();s.addRange(r.range);return r}
  function bkReplaceAt(h,start,len,now){
    const d=document.createElement('div');d.innerHTML=h;
    const w=document.createTreeWalker(d,NodeFilter.SHOW_TEXT),ns=[];let n;
    while(n=w.nextNode())ns.push(n);
    let pos=0,first=true;
    for(const x of ns){const L=x.nodeValue.length,a=pos,b=pos+L;pos=b;
      if(b<=start||a>=start+len)continue;
      const lo=Math.max(start-a,0),hi=Math.min(start+len-a,L);
      x.nodeValue=x.nodeValue.slice(0,lo)+(first?now:'')+x.nodeValue.slice(hi);first=false}
    d.normalize();return d.innerHTML}
  /* החלפה כעריכת מנהל רגילה, באותו נתיב של הצעות התיקון. מחזיר false עם הסבר אם אי אפשר. */
  /* הוספת קטע HTML בנקודה בטקסט (לפי מקום בטקסט הפשוט). בקצה סגנון תו - מחוץ לו */
  function bkInsertAt(h,pos,frag){
    const d=document.createElement('div');d.innerHTML=h;
    const w=document.createTreeWalker(d,NodeFilter.SHOW_TEXT);let n,acc=0,tgt=null,off=0;
    while(n=w.nextNode()){const L=n.nodeValue.length;
      if(L&&acc+L>=pos){tgt=n;off=pos-acc;break}acc+=L}
    const tp=document.createElement('template');tp.innerHTML=frag;
    if(!tgt){d.appendChild(tp.content);return d.innerHTML}
    let top=tgt;while(top.parentNode&&top.parentNode!==d)top=top.parentNode;
    if(top===tgt){const rest=off>=tgt.nodeValue.length?tgt.nextSibling:tgt.splitText(off);
      if(rest)d.insertBefore(tp.content,rest);else d.appendChild(tp.content)}
    else{
      const lastTxt=(function(){const ww=document.createTreeWalker(top,NodeFilter.SHOW_TEXT);let x,l=null;while(x=ww.nextNode())l=x;return l})();
      if(off>=tgt.nodeValue.length&&lastTxt===tgt)d.insertBefore(tp.content,top.nextSibling);
      else if(off===0){const ww=document.createTreeWalker(top,NodeFilter.SHOW_TEXT);if(ww.nextNode()===tgt)d.insertBefore(tp.content,top);else{tgt.parentNode.insertBefore(tp.content,tgt)}}
      else{const rest=tgt.splitText(off);tgt.parentNode.insertBefore(tp.content,rest)}}
    return d.innerHTML}
  /* ליבת ההחלה: כעריכת מנהל רגילה. make(curT,curH) מחזיר {nowT,nowH} או הסבר כשל */
  function bkApplyCore(f,make){
    const L=BK.loc[f.id];if(!L)return 'הממצא לא אותר בטקסט הנוכחי.';
    const s=L.s,old=ED.find(x=>x.k===s.k);
    const curT=old?old.now:s.t,curH=old?(old.nowH!==undefined?old.nowH:esc(old.now)):s.h;
    const r=make(curT,curH);if(typeof r==='string')return r;
    const nowT=r.nowT,nowH=r.nowH;
    if(plain(nowH||'')!==nowT)return 'לא ניתן להחיל בלי לפגוע בסגנון התו שבשורה. השתמש ב"ערוך".';
    const wasT=old?old.was:s.t,wasH=old?(old.wasH!==undefined?old.wasH:s.h):s.h;
    const el=$('#flow').querySelector('[data-ek="'+s.k+'"]');
    const cls=(s.c||'').split(' ').filter(c=>PCLS.indexOf(c)>-1).join(' ');
    const edit={k:s.k,was:wasT,now:nowT,wasH,nowH,wasP:old?old.wasP:cls,daf:s.daf,
                ctx:el?ctxOf(el):{b:'',a:''},t:Date.now(),pub:0};
    if(old&&old.ps!==undefined){edit.ps=old.ps;edit.psw=old.psw}
    BK.undo={id:f.id,f,prev:old||null,k:s.k,wasH:curH};
    if(old)ED=ED.filter(x=>x!==old);
    ED.push(edit);saveED();applyTextNow(edit);return edit}
  function bkApplyRep(f,rp){
    return bkApplyCore(f,(curT,curH)=>{
      const h=bkFindIn(curT,f);if(!h)return 'הטקסט בשורה השתנה מאז הבקרה.';
      const xc=bkCompact(rp.x).c,mkc=bkCompact(f.mark||'').c;
      /* הקטע להחלפה נמצא בתוך הסימון (או בתוך ההקשר) - ורק התאמה אחת */
      const within=h.sc.c.slice(h.pos,h.pos+h.len);
      let cs=within.indexOf(xc);
      if(cs<0&&mkc){const c2=h.sc.c.indexOf(xc);if(c2>-1&&h.sc.c.indexOf(xc,c2+1)<0)cs=c2-h.pos;else return 'הקטע "'+rp.x+'" אינו בשורה כפי שנרשם.'}
      else if(cs<0)return 'הקטע "'+rp.x+'" אינו בשורה כפי שנרשם.';
      const cStart=h.pos+cs,cEnd=cStart+xc.length-1;
      const oStart=h.sc.m[cStart],oEnd=h.sc.m[cEnd]+1;
      return {nowT:curT.slice(0,oStart)+rp.y+curT.slice(oEnd),nowH:bkReplaceAt(curH,oStart,oEnd-oStart,rp.y)}})}
  /* הוספה: [הסבר] בסגנון "הסבר" אחרי עוגן מדויק, לפניו, או בסוף הפסקה */
  function bkInsText(t){t=String(t||'').trim().replace(/^\[+|\]+$/g,'').trim().replace(/[.\s]+$/,'');return t}
  function bkApplyIns(f,op){
    return bkApplyCore(f,(curT,curH)=>{
      const tx=bkInsText(op.text);if(!tx)return 'אין טקסט להוספה.';
      const h=bkFindIn(curT,f),sc=h?h.sc:bkCC(curT);
      const before=op.before!==undefined&&op.after===undefined&&!op.end;
      let oi;
      if(op.end)oi=curT.replace(/\s+$/,'').length;
      else{
        const a=bkCompact(op.after||op.before||f.mark||'').c;if(!a)return 'אין עוגן להוספה.';
        let p=h?sc.c.indexOf(a,Math.max(0,h.pos-a.length)):-1;if(p<0)p=sc.c.indexOf(a);
        if(p<0)return 'העוגן "'+(op.after||op.before||f.mark)+'" אינו בשורה כפי שנרשם.';
        oi=before?sc.m[p]:sc.m[p+a.length-1]+1}
      const lead=before?'':' ',tail=before?' ':'';
      return {nowT:curT.slice(0,oi)+lead+'['+tx+']'+tail+curT.slice(oi),
              nowH:bkInsertAt(curH,oi,lead+'<i class="'+(op.cs||'hs')+'">['+esc(tx)+']</i>'+tail)}})}
  function bkAfterEdit(){drawEd();pubSoon();syncSoon()}
  async function bkDecide(id,d,done,nofocus){
    const f=BK.byId[id];if(!f)return;
    const wi=$('#bkwhy'),why=wi?wi.value.trim():'';
    let now='',msg='';
    if(d==='pending'){bkPut(f,'pending');bkSave();bkHideCard(true);bkRefreshAfter();toast('הממצא חזר לממתינים.');return}
    if(d==='ok'&&!done){
      const act=bkAction(f);
      if(act==='rep'||act==='ins'){
        const r=act==='rep'?bkApplyRep(f,bkRep(f)):bkApplyIns(f,bkOp(f));
        if(typeof r==='string'){toast(r+' אפשר ללחוץ "ערוך".',6000);return}
        now=act==='rep'?bkRep(f).y:bkInsText(bkOp(f).text);bkAfterEdit();
        msg=act==='rep'?'התיקון הוחל כעריכת מנהל. Ctrl+Z מבטל.':'ההוספה הוחלה בסגנון הסבר, כעריכת מנהל. Ctrl+Z מבטל.'}
      else if(act==='am'||act==='plain'||act==='ps'){
        if(!EDIT)setEdit(true);if(!EDIT)return;
        const L=BK.loc[f.id];if(!L){toast('הממצא לא אותר בטקסט הנוכחי.');return}
        if(!(SK.mode&&BK.curId===id&&$('#flow').querySelector('[data-ek="'+L.k+'"]'))){bkGo(id,false);
          await new Promise(r=>setTimeout(r,160))}
        const el=$('#flow').querySelector('[data-ek="'+L.k+'"]');
        if(el){el.focus();if(!bkSel(f)){toast('לא נמצא הקטע לסימון. אפשר ללחוץ "ערוך".');return}
          setCs(act==='am'?'am':(act==='ps'?'ps':''));msg=act==='am'?'סגנון אמוראים הוחל.':(act==='ps'?'סגנון פסוק הוחל.':'הסגנון הוסר.')}
        else{toast('לא נמצאה השורה לעריכה.');return}}
      else if(act==='q'){msg='נרשם: הוכרעה ללא שינוי בטקסט.'}
      else{bkNeedOp(f);return}}
    if(d==='ok'&&done){/* "בוצע" אחרי עריכה ידנית */}
    if(d==='edit'){if(!nofocus&&!bkFocusEdit(f))return;msg='עריכה על הקטע. מה שתכתוב גובר על ההצעה.'}
    if(d==='no'){msg='נדחה.'}
    /* למידה: אחרי "ערוך וקבל" נשמר הנוסח שהמחבר כתב בפועל, ליד ההצעה שהוצגה */
    if(d==='edit'&&nofocus){const L=BK.loc[f.id];if(L){const old=ED.find(x=>x.k===L.s.k);now=((old?old.now:L.s.t)||'').slice(0,900)}}
    bkPut(f,d,why,now);bkSave();bkHideCard(true);bkRefreshAfter();
    if(msg&&!SK.mode)toast(msg,4000);
    if(d==='no'&&BK.ON)setTimeout(()=>{},0)}
  window.bkDecide=bkDecide;
  /* לחיצה על "קבל" בכרטיס = Enter: מחיל ועובר להבא */
  window.bkAcceptClick=function(id){const f=BK.byId[id];if(f)bkKbDecide(f,'ok')};
  /* אין מטען מוכן: לא מסמנים "אושר", לא פותחים עריכה. נרשמת בקשה להצעה (שרשור שממתין להרצה המקומית), וממשיכים להבאה */
  function bkNeedOp(f){
    skSkip(f.id);
    toast('אין עדיין הצעה מוכנה לממצא הזה. נרשמה בקשה להצעה, ועברת להערה הבאה.',5000);
    BK.needSent=BK.needSent||new Set();if(BK.needSent.has(f.id))return;BK.needSent.add(f.id);
    if(typeof skPost==='function')skPost('/skira/thread',{slug:SLUG,id:f.id,who:'m',txt:'[בקשת הצעה] אין מטען מוכן להחלה (op) לממצא הזה. נא להכין הצעה מנוסחת וקצרה.'}).catch(()=>{})}
  /* במצב מעבר מהיר: בלי חישוב מיקומים ובלי ציור חלונית בכל הכרעה (הדגשה וספירה בלבד) */
  function bkRefreshAfter(){
    if(!SK.mode){bkRefresh();return}
    bkCount();skPassDraw();bkSoon()}
  /* עריכה ממוקדת: מצב עריכה דלוק, הסמן בסוף הקטע המסומן */
  function bkFocusEdit(f){
    if(!EDIT)setEdit(true);if(!EDIT)return false;
    const L=BK.loc[f.id];if(!L){toast('הממצא לא אותר בטקסט הנוכחי.');return false}
    const have=!!$('#flow').querySelector('[data-ek="'+L.k+'"]');
    if(!have)jump(L.pi,L.s.id);
    const go=()=>{const r=bkDomRange(f);if(!r)return;
      r.el.focus();const s=getSelection();s.removeAllRanges();const c=r.range.cloneRange();c.collapse(false);s.addRange(c);
      if($('#flow').classList.contains('vert'))r.el.scrollIntoView({block:'center'});else toEl(r.el)};
    if(have)go();else setTimeout(()=>{if(!EDIT)setEdit(true);go()},120);return true}
  let BKSV=null;function bkSave(){clearTimeout(BKSV);BKSV=setTimeout(bkFlush,300)}
  /* ביטול ההכרעה האחרונה שהוחלה כהחלפה (Ctrl+Z מחוץ לעריכה) */
  function bkUndoRec(u){
    if(u.k){const cur=ED.find(x=>x.k===u.k&&!x.fz);
      if(cur){edKeys();tomb(cur.k);ED=ED.filter(x=>x!==cur)}
      if(u.prev)ED.push(u.prev);
      dataSet(u.k,u.wasH);SLOTS=null;saveED();
      const el=$('#flow').querySelector('[data-ek="'+u.k+'"]');if(el)setHTML(el,u.wasH);
      drawEd();pubSoon();syncSoon()}
    bkPut(u.f,'pending');bkSave()}
  window.bkUndoRec=bkUndoRec;
  function bkUndo(){
    const u=BK.undo;if(!u)return false;BK.undo=null;
    bkUndoRec(u);bkRefresh();toast('הפעולה בוטלה והממצא חזר לממתינים.');return true}
  document.addEventListener('keydown',e=>{
    if(!BK.ON||!BK.undo||!(e.ctrlKey&&!e.altKey&&e.code==='KeyZ'))return;
    const t=e.target;if(t&&t.isContentEditable)return;
    e.preventDefault();bkUndo()},true);

  /* ---- חלונית "בקרה": ממצאים לפי סוג, סינון והכרעה גורפת ---- */
  function bkPanel(){if(!BK.ON)bkToggle();else{panel('bkp');if($('#bkp').classList.contains('open'))skDrawPanel()}}
  window.bkPanel=bkPanel;
  /* bkDrawPanel, bkInfoHtml ו-bkItem הועברו ל-skira_ui.js (סקירה, 13.10.2026) */
  function bkShowLost(id){const f=BK.byId[id];if(!f)return;
    toast('לא אותר. הקשר: '+(f.context||f.text||'').slice(0,70)+' · '+(f.fix||''),7000)}
  window.bkShowLost=bkShowLost;
  /* הכרעה גורפת לסוג שלם: החלפות ברורות מוחלות כעריכה, הוראות נרשמות "אושר לביצוע" */
  async function bkBulk(det,d){
    const byT=det.indexOf('typ:')===0,tp=byT?det.slice(4):'';const list=BK.F.filter(f=>(byT?bkTyp(f)===tp:f.det===det)&&bkPend(f)&&BK.loc[f.id]);if(!list.length)return;
    if(d!=='no'&&!SKBULK[bkTyp(list[0])]){toast('בסוגים טעות בפשט, חסר שלב ולא מובן אין אישור גורף: כל הערה בנפרד.',5000);return}
    const c=byT?[det,SKT[tp][0]]:(BK.CAT[det]||[det,det]);
    if(d==='no'){
      const why=prompt('דחיית כל '+list.length+' הממצאים מסוג "'+c[1]+'". נימוק (לא חובה):','');if(why===null)return;
      list.forEach(f=>bkPut(f,'no',why));bkSave();bkRefresh();toast('נדחו '+list.length+' ממצאים.');return}
    const apply=list.filter(f=>/^(rep|ins)$/.test(bkAction(f))),rest=list.length-apply.length;
    if(!apply.length){toast('אין בסוג הזה הצעה מוכנה להחלה גורפת.',5000);return}
    if(!confirm('לאשר את '+apply.length+' מתוך '+list.length+' הממצאים מסוג "'+c[1]+'"?\n'+apply.length+' ההצעות יוחלו כעריכת מנהל'+(rest?'\n'+rest+' ללא הצעה מוכנה יישארו ממתינות':'')+'\nאפשר לבטל כל אחד בנפרד.'))return;
    let ok=0,skip=[];
    for(const f of apply){
      const o=bkOp(f),r=o.t==='rep'?bkApplyRep(f,o):bkApplyIns(f,o);
      if(typeof r==='string'){skip.push(f);continue}
      bkPut(f,'ok','',o.t==='rep'?o.y:bkInsText(o.text));ok++;bkLocateAll()}
    bkSave();bkAfterEdit();bkRefresh();
    toast('אושרו '+ok+' מתוך '+list.length+(skip.length?'. '+skip.length+' דולגו (הטקסט השתנה) ונשארו ממתינים.':'.'),7000)}
  window.bkBulk=bkBulk;
  /* סרגל: מונה קטן של ממצאים שהתיישנו ונסגרו (הטקסט כבר מכסה אותם) */
  function bkStaleTxt(){const n=BK.STALE?BK.STALE.size:0;return n?' · '+n+' התיישנו':''}

  /* ---- חיווט: כפתור בסרגל, חלונית, וטעינה למנהל בלבד ---- */
  window.bkInit=function(){
    if(!isAdmin()){return}
    BK.has=true;bkCount();
    if(admKey())bkLoad()};
  setTimeout(()=>{if(isAdmin()){const b=$('#bkbtn2');if(b)b.style.display='';BK.has=true;bkCount();if(admKey())bkLoad()}},1600);
  setInterval(()=>{if(!document.hidden&&isAdmin()&&admKey()&&BK.loaded){bkLoad()}},180000);
  document.addEventListener('visibilitychange',()=>{if(!document.hidden&&BK.loaded)bkLoad()});
