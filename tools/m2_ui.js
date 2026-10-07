  /* =================== מנה 2 מתוך 3 (7.10.2026) ===================
     נטען אחרי suggest_ui.js ו-suggest_edit.js.
       א. פנל ניווט בעריכה: רשימת פרקים ודפים, קפיצה בלי לאבד שינויים.
       ב. Ctrl+L (וגיבוי Ctrl+Shift+L): טאב יישור לשמאל. מזוהה לפי המקש הפיזי (בעברית L נותן ך).
       ג. עיטור (***): מחיקה, והחלפה בכותרת. שינוי מבנה משלו (hdel / hrep), מעוגן בטקסט שתי הפסקאות השכנות.
       ד. Ctrl+1 על שם תנא או אמורא: הסגנון חל גם על הנקודתיים, והרווח שלפניהן נמחק.
       ה. הערות המנהל לקלוד: סימון עדין בשוליים, "חדשה" / "נלמדה".
       ו. מערכת עיצוב אחת לכפתורים (זהב בתלת-מימד), ניהול פנלים במקום אחד. */

  /* ---------- ב. טאב יישור לשמאל ----------
     הסימן בטקסט הוא U+2063 (מפריד בלתי נראה). בוורד הוא נכתב כטאב מיקום
     (w:ptab, יישור לשמאל מול השוליים) - tools/word_apply ו-tools/docx2json. באתר הוא נעטף
     ב-span.ltab, ורוחבו נמדד כך שהטקסט שאחריו יסתיים בקצה השמאלי של השורה. */
  const LTCH='⁣';
  function LTX(h){return (typeof h==='string'&&h.indexOf(LTCH)>-1)?h.split(LTCH).join('<span class="ltab">'+LTCH+'</span>'):h}
  (function(){const st=document.createElement('style');st.textContent=
    '.ltab{display:inline-block;width:0;height:1em;vertical-align:baseline}'+
    'body.ed .ltab{background:linear-gradient(90deg,transparent 0,transparent calc(100% - 2px),#c9a24a 0);min-width:2px}'+
    '.main.nose:empty::before,.main.dh:empty::before{content:"כתוב כאן את הכותרת";color:#b9ac8e}'+
    '.main.nose:empty,.main.dh:empty{min-height:1.5em}';
    document.head.appendChild(st)})();
  let LTT=null;
  function ltFitSoon(){clearTimeout(LTT);LTT=setTimeout(()=>ltFit($('#flow')),90)}
  function ltFit(root){
    if(!root||!root.querySelector('.ltab'))return;
    const all=[...root.querySelectorAll('.ltab')];
    all.forEach(sp=>{sp.style.width='0px'});
    all.forEach(sp=>{
      const p=sp.closest('p,.main,.anchor');if(!p)return;
      const cs=getComputedStyle(p),pr=p.getBoundingClientRect();
      const left=pr.left+(parseFloat(cs.paddingLeft)||0)+(parseFloat(cs.borderLeftWidth)||0);
      const r0=sp.getBoundingClientRect();
      const rg=document.createRange();rg.setStartAfter(sp);
      let last=p.lastChild;while(last&&last.lastChild)last=last.lastChild;
      if(!last)return;
      if(last.nodeType===3)rg.setEnd(last,last.nodeValue.length);else rg.setEndAfter(last);
      const mid=(r0.top+r0.bottom)/2;
      const rects=[...rg.getClientRects()].filter(r=>r.width>0&&Math.abs((r.top+r.bottom)/2-mid)<Math.max(6,r0.height*.6));
      const end=rects.length?Math.min(...rects.map(r=>r.left)):r0.left;
      sp.style.width=Math.max(0,Math.floor(end-left-1))+'px'})}
  addEventListener('resize',ltFitSoon);
  document.addEventListener('DOMContentLoaded',()=>{const f=document.getElementById('flow');if(!f)return;
    new MutationObserver(ltFitSoon).observe(f,{childList:true,subtree:true,characterData:true});
    if(document.fonts&&document.fonts.ready)document.fonts.ready.then(ltFitSoon)});
  /* המדידה הראשונה של המסילה רצה לפני שהגופנים נטענו, והציבה את ציון הדף מעלה בלי צורך.
     אחרי שהגופנים נטענו - מודדים שוב. */
  (function(){let t=null;const again=()=>{clearTimeout(t);t=setTimeout(()=>{try{setDafW();fitAnchors()}catch(e){}},80)};
    document.addEventListener('DOMContentLoaded',()=>{
      if(document.fonts){if(document.fonts.ready)document.fonts.ready.then(again);
        if(document.fonts.addEventListener)document.fonts.addEventListener('loadingdone',again)}
      setTimeout(again,1500)})})();
  function ltInsert(){
    const el=edEl();
    if(!el||!isTxt(el)){flash('העמד את הסמן בתוך פסקת טקסט');return}
    const s=getSelection();if(!s.rangeCount)return;
    sPush(el);
    s.getRangeAt(0).collapse(false);
    document.execCommand('insertHTML',false,'<span class="ltab">'+LTCH+'</span>');
    capture(el);ltFitSoon();
    flash('טאב יישור לשמאל נוסף (Ctrl+Z מבטל)')}
  /* בכרום Ctrl+L שייך לשורת הכתובת; בדפדפן שאינו מאפשר לתפוס אותו - Ctrl+Shift+L */
  document.addEventListener('keydown',e=>{
    if(!EDIT||!e.target.isContentEditable||e.altKey||e.metaKey||!e.ctrlKey)return;
    if(e.code==='KeyL'){e.preventDefault();e.stopPropagation();ltInsert()}},true);

  /* ---------- ד. Ctrl+1 על תנא או אמורא: גם הנקודתיים, בלי הרווח שלפניהן ---------- */
  function amColon(el,s){
    try{
      const r=s.getRangeAt(0);
      const a=cutOff(el,r.startContainer,r.startOffset);
      let b=cutOff(el,r.endContainer,r.endOffset);
      let text=txtOf(el);
      const cut=(x,y)=>{if(y<=x)return;const pa=posAt(el,x),pb=posAt(el,y),rr=document.createRange();
        rr.setStart(pa[0],pa[1]);rr.setEnd(pb[0],pb[1]);rr.deleteContents();el.normalize()};
      /* הבחירה כבר כוללת את הנקודתיים, ולפניהן רווח: הרווח נמחק */
      if(text[b-1]===':'&&/[  \t]/.test(text[b-2]||'')){
        let k=b-1;while(k>a&&/[  \t]/.test(text[k-1]))k--;
        cut(k,b-1);b-=(b-1-k)}
      else{
        let k=b;while(k<text.length&&/[  \t]/.test(text[k]))k++;
        if(text[k]!==':')return;
        cut(b,k)}
      text=txtOf(el);
      const end=text[b-1]===':'?b:b+1;
      const pa=posAt(el,a),pb=posAt(el,end),nr=document.createRange();
      nr.setStart(pa[0],pa[1]);nr.setEnd(pb[0],pb[1]);
      s.removeAllRanges();s.addRange(nr)}
    catch(err){}}

  /* ---------- א. פנל ניווט ---------- */
  const NAVW=196;
  (function(){const st=document.createElement('style');st.textContent=
    '#navp{position:fixed;top:var(--barH,52px);right:0;bottom:0;width:'+NAVW+'px;background:#fbf8f1;border-left:1px solid #d9d1bd;'+
      'box-shadow:-2px 0 12px rgba(0,0,0,.18);z-index:7;display:none;flex-direction:column;font-size:14px;direction:rtl}'+
    'body.navp #navp{display:flex}body.navp.navc #navp{width:30px}'+
    '#navp .nh{display:flex;align-items:center;gap:6px;padding:6px 8px;border-bottom:1px solid #d9d1bd;background:#f1ead9;font-weight:700}'+
    '#navp .nh button{margin-inline-start:auto;font:inherit;border:0;background:none;cursor:pointer;font-size:18px;line-height:1}'+
    '#navp .nb{flex:1;overflow:auto;padding:4px 6px 14px}'+
    'body.navc #navp .nb,body.navc #navp .nh b{display:none}'+
    '#navp details{margin:2px 0}#navp summary{cursor:pointer;padding:3px 4px;border-radius:4px;color:#3a332a}'+
    '#navp summary:hover{background:#efe6cc}#navp a{display:block;padding:2px 14px;border-radius:4px;color:#3a332a;text-decoration:none;cursor:pointer}'+
    '#navp a:hover{background:#efe6cc}#navp a.on{background:#c9a24a;color:#2b2620;font-weight:700}'+
    'body.navp:not(.navc) #flow{margin-right:'+NAVW+'px}body.navp.navc #flow{margin-right:30px}'+
    'body.navp .panel{right:'+NAVW+'px}body.navp.navc .panel{right:30px}'+
    '@media (max-width:700px){#navp{width:150px}body.navp:not(.navc) #flow{margin-right:150px}body.navp .panel{right:150px}}';
    document.head.appendChild(st)})();
  function navBuild(){
    const cur_=+($('#dafsel')&&$('#dafsel').value)||0;
    let h='';
    SEC.forEach((s,si)=>{
      const nm=((s.perekName||'')+'').trim()?((s.perek||'')+' '+s.perekName).trim():((s.perek||'')+'').trim()||('חלק '+(si+1));
      const inSec=cur_>=s.from&&cur_<=s.to;
      h+='<details'+(inSec?' open':'')+'><summary>'+esc(nm)+'</summary>';
      for(let pi=s.from;pi<=s.to;pi++){const p=D.pages[pi];if(!p.units.length)continue;
        h+='<a data-pi="'+pi+'" class="'+(pi===cur_?'on':'')+'">'+esc(p.label||p.daf||'')+'</a>'}
      h+='</details>'});
    return h}
  function navDraw(){
    let p=$('#navp');
    if(!p){p=document.createElement('div');p.id='navp';
      p.innerHTML='<div class="nh"><b>ניווט</b><button type="button" title="קיפול הפנל" onclick="navFold()">‹›</button></div><div class="nb" id="navb"></div>';
      document.body.appendChild(p);
      p.addEventListener('click',e=>{const a=e.target.closest&&e.target.closest('a[data-pi]');if(a){navGo(+a.dataset.pi)}})}
    $('#navb').innerHTML=navBuild()}
  /* קפיצה בעריכה: קודם לוכדים את מה שהוקלד, כדי שדבר לא יאבד */
  function navGo(pi){
    const ae=document.activeElement;
    if(EDIT&&ae&&ae.isContentEditable){clearTimeout(CAPT);capture(ae)}
    toDaf(pi);
    setTimeout(navDraw,80)}
  function navOpen(on){
    const was=document.body.classList.contains('navp');
    if(on===undefined)on=!was;
    document.body.classList.toggle('navp',!!on);
    if(on){navDraw();document.body.classList.toggle('navc',innerWidth<=700);
      document.querySelectorAll('.panel').forEach(x=>x.classList.remove('open'))}
    setTimeout(()=>{try{fitAnchors()}catch(e){}ltFitSoon()},60);
    const b=$('#navbtn');if(b)b.classList.toggle('on',!!on)}
  function navFold(){document.body.classList.toggle('navc');setTimeout(()=>{try{fitAnchors()}catch(e){}},60)}
  document.addEventListener('keydown',e=>{
    if(!EDIT||e.ctrlKey||e.metaKey||!e.altKey||e.shiftKey||e.code!=='KeyN')return;
    e.preventDefault();navOpen()});
  /* הכפתור בסרגל העריכה, וסגירה ביציאה ממצב עריכה */
  const _edToolsDrawNav=null;

  /* ---------- ג. עיטור (***): מחיקה והחלפה בכותרת ---------- */
  /* פריטי הטקסט של המסכת לפי הסדר: פסקאות גוף ומשנה, כותרות, ועיטורים.
     השכנים של עיטור הם הפריטים הקרובים שאינם עיטור; הם העוגן. */
  function decoItems(){
    const items=[];
    D.pages.forEach((p,pi)=>p.units.forEach((u,n)=>{
      if(u.k==='hatz')items.push({t:'',deco:true,pi,n,u,j:null,daf:p.daf});
      else if(u.k==='u'||u.k==='m')u.l.forEach((x,j)=>{
        if(x[0]==='hatz')items.push({t:'',deco:true,pi,n,u,j,daf:p.daf});
        else items.push({t:plain(x[1]),deco:false,pi,n,u,j,daf:p.daf})});
      else if(plain(u.a||'').trim())items.push({t:plain(u.a),deco:false,pi,n,u,j:null,daf:p.daf})}));
    return items}
  const _dn=t=>(t||'').replace(/\s+/g,' ').trim();
  function decoNb(items,i){
    let a='',b='';
    for(let k=i-1;k>=0;k--)if(!items[k].deco){a=items[k].t;break}
    for(let k=i+1;k<items.length;k++)if(!items[k].deco){b=items[k].t;break}
    return [a,b]}
  function decoFind(texts,daf){
    if((texts||[]).length!==2)return null;
    const w0=_dn(texts[0]),w1=_dn(texts[1]),items=decoItems(),hits=[];
    items.forEach((it,i)=>{if(!it.deco)return;const [a,b]=decoNb(items,i);if(_dn(a)===w0&&_dn(b)===w1)hits.push(it)});
    if(hits.length===1)return hits[0];
    if(hits.length>1&&daf){const k0=dafKey(daf);
      const near=hits.filter(h=>{const k=dafKey(h.daf);return k0!==null&&k!==null&&Math.abs(k-k0)<=1});
      if(near.length===1)return near[0]}
    return null}
  function decoDone(e){
    const t=e.texts||[];if(t.length!==2)return false;
    const mid=e.kind==='hrep'?[_dn((e.resT||[''])[0])]:[];
    const items=decoItems(),want=[_dn(t[0])].concat(mid,[_dn(t[1])]);
    for(let i=0;i+want.length<=items.length;i++){
      const seq=items.slice(i,i+want.length);
      if(seq.some(x=>x.deco))continue;
      if(seq.every((x,k)=>_dn(x.t)===want[k]))return true}
    return false}
  /* מחיל על הנתונים. מחזיר false אם אי אפשר (החלפה בתוך משנה) */
  function decoApplyData(h,e){
    const us=D.pages[h.pi].units;
    if(h.j!==null){
      if(e.kind==='hrep')return false;
      h.u.l.splice(h.j,1);delete h.u.lv;return true}
    if(e.kind==='hdel'){us.splice(us.indexOf(h.u),1);return true}
    const r=(e.res||[])[0];if(!r||(r[0]!=='nose'&&r[0]!=='dh'))return false;
    us[us.indexOf(h.u)]={k:r[0],a:r[1],l:[],id:e.t,s:''};return true}
  /* האלמנט שנלחץ -> מקומו בנתונים */
  function decoOfEl(el){
    const row=el.closest('.row');if(!row)return null;
    const id=+row.id.slice(1);
    const p=el.closest('p');
    const items=decoItems();
    if(row.classList.contains('hatz'))return items.find(x=>x.deco&&x.j===null&&x.u.id===id)||null;
    if(p&&p.classList.contains('hatz')){
      const ps=[...row.querySelectorAll('.main p')],j=ps.indexOf(p);
      return items.find(x=>x.deco&&x.j===j&&x.u.id===id)||null}
    return null}
  function decoDo(kind,head){
    const el=DECO.el;if(!el)return;
    const h=decoOfEl(el);if(!h){flash('העיטור לא אותר בנתונים. רענן את הדף ונסה שוב');return}
    if(kind==='hrep'&&h.j!==null){flash('בתוך משנה אפשר רק למחוק את העיטור');return}
    const items=decoItems(),i=items.findIndex(x=>x.u===h.u&&x.j===h.j&&x.deco);
    const [prev,next]=decoNb(items,i);
    const daf=h.daf||dafOfEl(el);
    const snp=[snapOf(h.pi)],usnap=JSON.stringify(D.pages[h.pi].units);
    const t=Date.now();
    const se={op:'struct',kind,texts:[prev,next],res:[],resT:[],daf,t,pub:0,_ap:1};
    if(kind==='hrep'){se.res=[[head,'']];se.resT=[''];se.psw=wsty(head)}
    /* החלפה בכותרת: היחידה החדשה היא "פסקה ריקה" (מצב עבודה בלבד): הרשומה נכתבת רק כשנכתב בה טקסט */
    if(!decoApplyData(h,kind==='hdel'?se:Object.assign({},se,{res:[[head,'']]}))){flash('לא ניתן להחיל כאן');return}
    if(kind==='hdel')ED.push(se);
    else{const nu=D.pages[h.pi].units.find(u=>u.id===t);if(nu)nu.hph={texts:[prev,next],head,daf}}
    UNDO.length=0;UNDO.push({e:kind==='hdel'?se:null,snaps:[{pi:h.pi,snap:usnap}],key:kind==='hdel'?'':'u'+t+'.0',t:Date.now()});
    SLOTS=null;saveED();decoHide();
    snp.forEach(s=>patchPage(s));
    if(kind==='hrep')setTimeout(()=>placeCaret('u'+t+'.0',0),30);
    drawEd();pubSoon();syncSoon();
    flash(kind==='hdel'?'העיטור נמחק (Ctrl+Z מבטל)':'העיטור הוחלף בשורה ריקה: כתוב את הכותרת')}
  /* כותרת שהחליפה עיטור: כשנכתב בה טקסט היא נרשמת, וכשהתרוקנה היא חוזרת להיות מצב עבודה */
  function hrepCapture(el){
    const k=el.dataset&&el.dataset.ek||'';const m=/^u(\d+)\.0$/.exec(k);if(!m)return false;
    let u=null,pi=-1;
    D.pages.forEach((p,i)=>p.units.forEach(x=>{if(x.id===+m[1]&&x.hph){u=x;pi=i}}));
    if(!u)return false;
    const nowH=htmlOf(el),nowT=txtOf(el),ph=u.hph;
    u.a=nowH;delete u.lv;SLOTS=null;
    if(!nowT.trim()){
      if(ph.se){const i=ED.indexOf(ph.se);if(i>-1){edKeys();tomb(ph.se.k);ED.splice(i,1)}delete ph.se;saveED();drawEd();pubSoon()}
      return true}
    if(!ph.se){
      const se={op:'struct',kind:'hrep',texts:ph.texts,head:ph.head,res:[[ph.head,nowH]],resT:[nowT],psw:wsty(ph.head),
                daf:ph.daf,t:u.id,pub:0,_ap:1};
      ph.se=se;ED.push(se)}
    else{ph.se.res=[[ph.head,nowH]];ph.se.resT=[nowT];ph.se.pub=0;ph.se.t=ph.se.t}
    saveED();drawEd();pubSoon();syncSoon();return true}
  /* הסרגל הקטן שמעל עיטור מסומן */
  const DECO={el:null};
  (function(){const st=document.createElement('style');st.textContent=
    'body.ed .row.hatz .main.hatz,body.ed .main.mishna p.hatz{cursor:pointer}'+
    '.decosel{outline:2px solid #c9a24a;outline-offset:2px;border-radius:3px}'+
    '#decobar{position:fixed;z-index:9;display:none;gap:4px;background:#2b2620;border-radius:7px;padding:4px 6px;box-shadow:0 4px 16px rgba(0,0,0,.4)}'+
    '#decobar button{font:inherit;font-size:13px;color:#2b2620;border:0;border-radius:5px;padding:3px 10px;cursor:pointer;'+
      'background:linear-gradient(#f0d98c,#c9a24a);box-shadow:inset 0 1px 0 rgba(255,255,255,.55),0 1px 2px rgba(0,0,0,.4)}'+
    '#decobar button:hover{filter:brightness(1.07);box-shadow:inset 0 1px 0 rgba(255,255,255,.6),0 0 8px rgba(240,200,90,.7)}';
    document.head.appendChild(st)})();
  function decoShow(el){
    decoHide();DECO.el=el;el.classList.add('decosel');
    let b=$('#decobar');
    if(!b){b=document.createElement('div');b.id='decobar';
      b.innerHTML='<button type="button" onmousedown="event.preventDefault()" onclick="decoDo(\'hdel\')" title="מוחק את העיטור (Delete)">מחק עיטור</button>'+
        '<button type="button" data-h="nose" onmousedown="event.preventDefault()" onclick="decoDo(\'hrep\',\'nose\')" title="במקום העיטור: שורה ריקה בסגנון נושא">החלף בכותרת נושא</button>'+
        '<button type="button" data-h="dh" onmousedown="event.preventDefault()" onclick="decoDo(\'hrep\',\'dh\')" title="במקום העיטור: שורה ריקה בסגנון ד&quot;ה משנה">החלף בד"ה משנה</button>';
      document.body.appendChild(b)}
    const inM=!!el.closest('.main.mishna');
    b.querySelectorAll('button[data-h]').forEach(x=>{x.style.display=(inM||!PSTY.some(p=>p[0]===x.dataset.h))?'none':''});
    b.style.display='flex';
    const rc=el.getBoundingClientRect();
    b.style.top=Math.max(8,rc.top-38)+'px';
    b.style.left=Math.max(8,Math.min(innerWidth-b.offsetWidth-8,rc.left+rc.width/2-b.offsetWidth/2))+'px'}
  function decoHide(){const b=$('#decobar');if(b)b.style.display='none';
    document.querySelectorAll('.decosel').forEach(x=>x.classList.remove('decosel'));DECO.el=null}
  document.addEventListener('mousedown',e=>{
    if(!EDIT)return;
    if(e.target.closest&&e.target.closest('#decobar'))return;
    const h=e.target.closest&&e.target.closest('.row.hatz .main.hatz,.main.mishna p.hatz');
    if(h){e.preventDefault();decoShow(h);return}
    decoHide()},true);
  document.addEventListener('keydown',e=>{
    if(!EDIT||!DECO.el)return;
    if(e.key==='Delete'||e.key==='Backspace'){e.preventDefault();e.stopPropagation();decoDo('hdel')}
    else if(e.key==='Escape')decoHide()},true);

  /* ---------- ה. הערות המנהל לקלוד: סימון עדין בשוליים היכן שיש הערה חדשה ---------- */
  (function(){const st=document.createElement('style');st.textContent=
    'body.ed .hasnt{position:relative}'+
    'body.ed .hasnt::after{content:"";position:absolute;left:-14px;top:.35em;width:8px;height:8px;border-radius:50%;'+
      'background:radial-gradient(circle at 35% 35%,#f0d98c,#c9a24a);box-shadow:0 0 0 1px rgba(90,70,20,.35)}';
    document.head.appendChild(st)})();
  function ntMark(){
    const f=$('#flow');if(!f)return;
    f.querySelectorAll('.hasnt').forEach(x=>{x.classList.remove('hasnt');x.removeAttribute('data-nt')});
    if(!isAdmin()||!NT)return;
    for(const x of NT){
      if(x.learned||x.slug!==SLUG||!x.k)continue;
      const el=f.querySelector('[data-ek="'+x.k+'"]');
      if(el){el.classList.add('hasnt');el.dataset.nt='הערה לקלוד: '+(x.note||'').slice(0,60)}}}
  document.addEventListener('DOMContentLoaded',()=>{const f=document.getElementById('flow');if(!f)return;
    let t=null;new MutationObserver(()=>{clearTimeout(t);t=setTimeout(ntMark,200)}).observe(f,{childList:true,subtree:true})});

  /* ---------- ו. סרגל מסודר: כפתור עריכה אחד ---------- */
  /* מנהל מוכר: "עריכה". כל אחד אחר: "הצע תיקון" (עורך מלא, כל פעולה נרשמת כהצעה). */
  function editBtn(){
    if(EDIT){setEdit(false);return}
    if(isAdmin()&&(admKey()||ONGESHER)){SUGM=false;setEdit(true);return}
    sugEnter()}
  function edBtnLabel(){const b=$('#edbtn');if(b)b.textContent=(isAdmin()&&(admKey()||ONGESHER))?'עריכה':'הצע תיקון'}
  document.addEventListener('DOMContentLoaded',()=>{edBtnLabel();setTimeout(edBtnLabel,1200);setInterval(edBtnLabel,4000)});

  /* ---------- ו. פנלים מנוהלים במקום אחד ----------
     צד ימין: פנל הניווט (מעגן, דוחף את הטקסט) ופנלי המידע (מעל הטקסט). נפתח פנל מידע - הניווט מתקפל
     ואינו נסגר; נפתח הניווט - פנלי המידע נסגרים. צד שמאל: מגירת המקור וחלונית הסגנונות. נפתחה
     מגירת המקור בפיצול - חלונית הסגנונות מתקפלת לפס, ולא עולה עליה. */
  (function(){
    const mo=new MutationObserver(()=>{
      const open=[...document.querySelectorAll('.panel.open')].length>0;
      if(open&&document.body.classList.contains('navp')&&!document.body.classList.contains('navc')){
        document.body.classList.add('navc','navauto')}
      else if(!open&&document.body.classList.contains('navauto')){
        document.body.classList.remove('navc','navauto')}
      if(document.body.classList.contains('splitsrc')&&typeof styCollapse==='function'&&!document.body.__styc){
        document.body.__styc=1;try{styCollapse(1)}catch(e){}}
      else if(!document.body.classList.contains('splitsrc'))document.body.__styc=0});
    document.addEventListener('DOMContentLoaded',()=>{
      document.querySelectorAll('.panel').forEach(p=>mo.observe(p,{attributes:true,attributeFilter:['class']}));
      mo.observe(document.body,{attributes:true,attributeFilter:['class']})})})();
