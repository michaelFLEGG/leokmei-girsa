  /* =================== שורה שהתארכה (פרומפט 41, 15.11.2026, מנהל בלבד) ===================
     בהדפסה המוגדלת (A4 מוגדל) חלק מן השורות שבעל הפרויקט כיוון גולשות לשורה שנייה. המחולל
     (tools/overflow/overflow_gen.py) כותב את הרשימה ואת ההצעות שנבדקו במנוע: data/overflow/<מסכת>.json.
     כאן, במצב מנהל: קו גלי אדום דק מתחת לשורה (בלי רקע), והמילים שגלשו באדום. הסימון נעשה ב-CSS Highlight
     ולא בתגית, כדי שהעורך לעולם לא יקרא אותו כחלק מן הטקסט.
     לחיצה על השורה: חלונית - "חסרות X אותיות", ההצעה (מה שנמחק בקו חוצה, מה שנוסף מודגש), וקבל / ערוך /
     הצעה אחרת / השאר / בטל. "קבל" אינו מסלול חדש: הוא משתמש ב-skmApply של סכם, כלומר באותן רשומות
     שהעורך כותב (תיקון טקסט, פיצול, כותרת צד), ומשם לפרסום, לבנייה ולוורד דרך tools/cloud_word.py בלבד.
     כל הכרעה נרשמת בשרת (bakara/dec, מסכת "ov-<מסכת>") כחומר למידה למחולל. */
  const OVS={doc:null,items:[],byP:new WeakMap(),dec:{},cur:null,alt:0,pop:null,loaded:false};
  const OV_RAW='https://raw.githubusercontent.com/michaelFLEGG/leokmei-girsa/main/data/overflow/';
  function ovOK(){try{return typeof isAdmin==='function'&&isAdmin()}catch(e){return false}}
  function ovNorm(s){return String(s||'').replace(/[֑-ׇ⁠ ]/g,'').replace(/[\s]+/g,' ').trim()}
  function ovPlain(h){const d=document.createElement('div');d.innerHTML=String(h||'');return d.textContent}
  async function ovLoad(){
    if(OVS.loaded||!ovOK())return;OVS.loaded=true;
    let doc=null;
    for(const u of [OV_RAW+SLUG+'.json?t='+Math.floor(Date.now()/300000),'overflow/'+SLUG+'.json']){
      try{const r=await fetch(u,{cache:'no-store'});if(r.ok){doc=await r.json();break}}catch(e){}}
    if(!doc||!doc.items)return;
    OVS.doc=doc;OVS.items=doc.items;
    try{const j=await api('/bakara/dec?slug=ov-'+SLUG);OVS.dec=(j.doc&&j.doc.dec)||{}}catch(e){OVS.dec={}}
    ovMark();ovBar()}
  function ovDone(it){const d=OVS.dec[it.id];return !!(d&&d.d!=='todo'&&d.d!=='pending')}
  /* הפסקה באתר: יחידה u<מזהה>, פסקה li. אם הנוסח השתנה מאז שהרשימה נבנתה - אינה מסומנת (המחולל ירוץ שוב) */
  function ovPara(it){
    const row=document.getElementById('u'+it.u);if(!row)return null;
    const m=row.querySelector(':scope > .main');if(!m)return null;
    /* פרומפט 48 (תיקון 4): כותרת (נושא, ד"ה) שתופסת יותר משורה בהדפסה - הסימון על הכותרת עצמה */
    if(it.head)return ovNorm(ovPText(m))===ovNorm(it.text)?m:null;
    const p=m.querySelectorAll(':scope > p')[it.li-1];if(!p)return null;
    return ovNorm(ovPText(p))===ovNorm(it.text)?p:null}
  /* הטקסט של הפסקה בלי סימני התוספות ובלי רכיבי תצוגה שאינם טקסט */
  function ovPText(p){const c=p.cloneNode(true);c.querySelectorAll('sup,.tzc,.bkx,.tm,.tmg,.og').forEach(x=>x.remove());return c.textContent}
  function ovMark(){
    if(!OVS.items.length)return;
    const hasHL=typeof CSS!=='undefined'&&CSS.highlights&&typeof Highlight!=='undefined';
    const L=hasHL?new Highlight():null,R=hasHL?new Highlight():null;
    OVS.byP=new WeakMap();let n=0;
    OVS.items.forEach(it=>{
      if(ovDone(it))return;
      const p=ovPara(it);if(!p)return;
      OVS.byP.set(p,it);n++;it._p=p;
      if(!hasHL){p.classList.add('ovfb');return}
      const rg=document.createRange();rg.selectNodeContents(p);L.add(rg);
      /* המילים שגלשו: הסיפא של הטקסט, לפי מספר התווים (בלי ניקוד) מן הסוף */
      const want=ovNorm(it.over).replace(/ /g,'').length;if(!want)return;
      const w=document.createTreeWalker(p,NodeFilter.SHOW_TEXT),ns=[];let x;while((x=w.nextNode()))ns.push(x);
      let left=want,end=null,start=null;
      for(let i=ns.length-1;i>=0&&left>0;i--){const v=ns[i].nodeValue;
        for(let k=v.length-1;k>=0;k--){if(!end){if(/\s/.test(v[k]))continue;end=[ns[i],k+1]}
          if(!/[\s֑-ׇ⁠ ]/.test(v[k]))left--;
          if(left<=0){start=[ns[i],k];break}}}
      if(start&&end){const r2=document.createRange();r2.setStart(start[0],start[1]);r2.setEnd(end[0],end[1]);R.add(r2)}});
    if(hasHL){CSS.highlights.set('ovline',L);CSS.highlights.set('ovword',R)}
    OVS.shown=n}
  function ovLeft(){return OVS.items.filter(it=>!ovDone(it)&&it._p&&it._p.isConnected).length}
  function ovBar(){
    if(!ovOK()||!OVS.items.length)return;
    let b=$('#ovnext');
    if(!b){const after=$('#skpnext')||$('#skpdup')||$('#skptag')||$('#skpbtn')||$('#peresel');
      b=document.createElement('button');b.id='ovnext';b.type='button';b.className='skpbtn skptop ovtop';
      b.addEventListener('mousedown',e=>e.preventDefault());b.onclick=e=>{e.stopPropagation();ovNext()};
      if(after)after.after(b);else ($('#bar')||document.body).appendChild(b)}
    const n=ovLeft();
    b.textContent='↵ '+n;b.classList.toggle('off',!n);
    b.setAttribute('aria-label','שורה שהתארכה - הבאה, נותרו '+n);
    b.title=n?'שורה שהתארכה - הבאה · '+n+' שורות שגולשות בהדפסה המוגדלת וטרם הוכרעו. לחיצה קופצת לבאה':'שורה שהתארכה: הכל הוכרע';
    try{if(typeof barH==='function')barH()}catch(e){}}
  function ovNext(){
    const list=OVS.items.filter(it=>!ovDone(it)&&it._p&&it._p.isConnected);
    if(!list.length){flash('שורה שהתארכה: אין שורות שטרם הוכרעו');return}
    const y=innerHeight*0.35;
    let nx=list.find(it=>it._p.getBoundingClientRect().top>y+4)||list[0];
    nx._p.scrollIntoView({block:'center'});setTimeout(()=>ovOpen(nx),250)}
  /* ---- החלונית ---- */
  function ovWords(s){return ovPlain(s).replace(/\s+/g,' ').trim().split(' ').filter(Boolean)}
  /* הבדל במילים: מה שנמחק בקו חוצה, מה שנוסף מודגש (כמו בסכם) */
  function ovDiff(a,b){
    const A=ovWords(a),B=ovWords(b),n=A.length,m=B.length,F=[...Array(n+1)].map(()=>new Array(m+1).fill(0));
    for(let i=n-1;i>=0;i--)for(let j=m-1;j>=0;j--)F[i][j]=A[i]===B[j]?F[i+1][j+1]+1:Math.max(F[i+1][j],F[i][j+1]);
    const out=[];let i=0,j=0;
    while(i<n||j<m){
      if(i<n&&j<m&&A[i]===B[j]){out.push(ge(A[i]));i++;j++}
      else if(j<m&&(i>=n||F[i][j+1]>=F[i+1][j])){out.push('<b class="ovadd">'+ge(B[j])+'</b>');j++}
      else{out.push('<s class="ovdel">'+ge(A[i])+'</s>');i++}}
    return out.join(' ')}
  function ge(s){return String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
  const OV_TOOL={2:'מחיקת תווים',3:'ניסוח קצר',4:'חיתוך לשתי שורות',5:'איחוי עם השורה הסמוכה'};
  function ovSugHtml(it,s){
    if(!s)return '<div class="ovnone">אין הצעה שעוברת את הבדיקה. אפשר לערוך ביד, או להשאיר.</div>';
    let h='<div class="ovtool">'+(OV_TOOL[s.tool]||'')+(s.why?' · '+ge(s.why):'')+'</div>';
    if(s.kind==='split')h+='<div class="ovsplit"><div class="ovl">'+ge(ovPlain(s.parts[0]))+'</div>'+
      (s.side?'<div class="ovl ovl2"><span class="ovside">'+ge(s.side)+'</span>'+ge(ovPlain(s.parts[1]))+'</div>':'<div class="ovl">'+ge(ovPlain(s.parts[1]))+'</div>')+'</div>';
    else if(s.kind==='join')h+='<div class="ovl">'+ge(ovPlain(s.html))+'</div>';
    else if(s.kind==='move')h+='<div class="ovl">'+ovDiff(it.html,s.html)+'</div><div class="ovl ovnb">'+ovDiff(s.targetOrig||'',s.targetHtml)+'</div>';
    else h+='<div class="ovl">'+ovDiff(it.html,s.html)+'</div>';
    return h}
  /* 17.11.2026 (מיכאל, דחוף): דילוג על השורה הנוכחית בלי להכריע עליה - "הבא ›" בחלונית, או Tab.
     השורה נשארת פתוחה (לא "השאר"), והחלונית עוברת מיד לשורה הבאה שטרם הוכרעה בסדר הדף. Shift+Tab - לקודמת.
     במצב דפוס, מצב הדפוס קובע מהו "הבא" (window.ovSkipFn, נקבע ב-pmOv). */
  function ovSkip(dir){
    const it=OVS.cur,f=window.ovSkipFn;
    if(f&&dir<0){flash('במצב דפוס: Tab או F4 לשורה הבאה');return}
    if(f){ovClose();try{f()}catch(e){}return}
    const list=OVS.items.filter(x=>x!==it&&!ovDone(x)&&x._p&&x._p.isConnected);
    if(!list.length){ovClose();flash('אין שורות נוספות שטרם הוכרעו');return}
    const after=x=>it&&it._p&&it._p.isConnected?!!(it._p.compareDocumentPosition(x._p)&Node.DOCUMENT_POSITION_FOLLOWING)||(x._p===it._p&&OVS.items.indexOf(x)>OVS.items.indexOf(it)):true;
    let nx;
    if(dir>0)nx=list.find(after)||list[0];
    else{const bef=list.filter(x=>!after(x));nx=bef.length?bef[bef.length-1]:list[list.length-1]}
    ovClose();nx._p.scrollIntoView({block:'center'});setTimeout(()=>ovOpen(nx),200)}
  function ovOpen(it){
    ovClose();OVS.cur=it;OVS.alt=0;window.ovSkipFn=null;
    const d=document.createElement('div');d.id='ovpop';d.className='ovpop';d.setAttribute('role','dialog');d.setAttribute('dir','rtl');d.tabIndex=-1;d.style.outline='none';
    document.body.appendChild(d);OVS.pop=d;ovDraw();
    const r=it._p.getBoundingClientRect();
    d.style.top=Math.max(54,Math.min(innerHeight-d.offsetHeight-10,r.bottom+6))+'px';
    d.style.left=Math.max(8,Math.min(innerWidth-d.offsetWidth-8,r.left))+'px';
    d.focus&&d.focus()}
  function ovDraw(){
    const it=OVS.cur,d=OVS.pop;if(!it||!d)return;
    const s=it.sug[OVS.alt]||null,more=it.sug.length>1;
    const type=s&&s.tool===2&&/^abbr:/.test(s.type||'')?s.type:'';
    const nType=type?OVS.items.filter(x=>!ovDone(x)&&x.sug.some(z=>z.type===type)).length:0;
    d.innerHTML='<div class="ovhd">'+(it.head?'כותרת בשתי שורות · ':'')+'חסרות '+it.miss+' אותיות'+(it.long?' · פסקה ארוכה':'')+'<span class="ovdaf">'+ge(it.daf||'')+'</span></div>'+
      '<div class="ovbody">'+ovSugHtml(it,s)+'</div>'+
      '<div class="ovbtns">'+
      (s?'<button data-a="ok" class="ovp">קבל</button>':'')+'<button data-a="edit">ערוך</button>'+
      (more?'<button data-a="alt">הצעה אחרת</button>':'')+'<button data-a="leave">השאר</button><button data-a="prev" title="השורה הקודמת (Shift+Tab)">‹ הקודם</button><button data-a="skip" class="ovskip" title="דלג על השורה הזו בלי להכריע - לשורה הבאה (Tab)">הבא ›</button><button data-a="x">בטל</button>'+
      (type&&nType>1?'<button data-a="all" class="ovall">קבל את כל ההצעות מהסוג הזה במסכת ('+nType+')</button>':'')+'</div>'+
      '<div class="ovkeys">Enter קבל · Tab הבא · Shift+Tab הקודם · Esc בטל</div>';
    d.querySelectorAll('button').forEach(b=>{b.addEventListener('mousedown',e=>e.preventDefault());b.onclick=()=>ovAct(b.dataset.a)})}
  function ovClose(){if(OVS.pop){OVS.pop.remove();OVS.pop=null}OVS.cur=null}
  function ovSend(it,d,extra){
    const s=it.sug[OVS.alt]||{};
    const rec=Object.assign({id:it.id,d,txt:ovPlain(it.html).slice(0,1000),det:String(it.miss),kind:'ov'+(s.tool||0)+(s.kind?':'+s.kind:''),
      sug:s.kind==='split'?s.parts.map(ovPlain).join(' / ').slice(0,1000):ovPlain(s.html||'').slice(0,1000),t:Date.now()},extra||{});
    OVS.dec[it.id]=rec;
    api('/bakara/dec',{method:'POST',body:JSON.stringify({slug:'ov-'+SLUG,items:[rec]})}).catch(e=>toast('ההכרעה לא נשמרה בשרת: '+(e.message||e),5000))}
  async function ovAct(a){
    const it=OVS.cur;if(!it)return;
    if(a==='x'){ovClose();return}
    if(a==='skip'){ovSkip(1);return}
    if(a==='prev'){ovSkip(-1);return}
    if(a==='alt'){ovSend(it,'todo',{rs:'other'});OVS.alt=(OVS.alt+1)%it.sug.length;ovDraw();return}
    if(a==='leave'){ovSend(it,'no');ovClose();ovAfter();flash('הושאר כמות שהוא');return}
    if(a==='edit'){ovEditBox(it);return}
    if(a==='ok'){const s=it.sug[OVS.alt];if(!s)return;
      try{const n=ovApply(it,s);ovSend(it,'ok',{now:ovNow(s)});ovClose();ovAfter();flash('הוחל: '+n+' שינויים, ויפורסמו עם שאר העריכות (Ctrl+ז מבטל)')}
      catch(e){flash('לא הוחל: '+(e.message||e))}return}
    if(a==='all'){const s=it.sug[OVS.alt],type=s.type;
      const list=OVS.items.filter(x=>!ovDone(x)&&x._p&&x._p.isConnected&&x.sug.some(z=>z.type===type));
      if(!confirm('להחיל "'+(s.why||type)+'" ב-'+list.length+' שורות במסכת?'))return;
      let ok=0,bad=0;
      list.forEach(x=>{const z=x.sug.find(q=>q.type===type);try{ovApply(x,z);OVS.alt=x.sug.indexOf(z);ovSend(x,'ok',{now:ovNow(z),rs:'all'});ok++}catch(e){bad++}});
      ovClose();ovAfter();flash('הוחל ב-'+ok+' שורות'+(bad?' · '+bad+' לא הוחלו (הנוסח השתנה)':''));return}}
  function ovNow(s){return (s.kind==='split'?s.parts.map(ovPlain).join(' / '):ovPlain(s.html||'')).slice(0,1000)}
  function ovAfter(){ovMark();ovBar()}
  /* ערוך: ההצעה (או הנוסח הנוכחי) כטקסט שניתן לעריכה. Enter בתוך התיבה = שורה חדשה (חיתוך), Ctrl+Enter = קבל */
  function ovEditBox(it){
    const s=it.sug[OVS.alt],d=OVS.pop;
    const start=s?(s.kind==='split'?s.parts.map(ovPlain).join('\n'):ovPlain(s.html)):ovPlain(it.html);
    d.querySelector('.ovbody').innerHTML='<textarea class="ovta" dir="rtl" rows="3"></textarea><div class="ovkeys">שורה חדשה = חיתוך לשתי פסקאות. Ctrl+Enter קבל</div>';
    const ta=d.querySelector('.ovta');ta.value=start;ta.focus();
    d.querySelector('.ovbtns').innerHTML='<button data-a="okedit" class="ovp">קבל</button><button data-a="x">בטל</button>';
    const go=()=>{const lines=ta.value.split('\n').map(x=>x.replace(/\s+/g,' ').trim()).filter(Boolean);
      if(!lines.length){flash('אין טקסט');return}
      if(it.head&&lines.length>1){flash('כותרת נשארת בשורה אחת. קצר את הנוסח');return}
      const z=lines.length>1?{tool:s?s.tool:0,kind:'split',parts:lines.map(ge),side:''}:{tool:s?s.tool:0,kind:'replace',html:ovKeepTags(it.html,lines[0])};
      try{const n=ovApply(it,z);ovSend(it,'edit',{now:ovNow(z)});ovClose();ovAfter();flash('הוחל: '+n+' שינויים (Ctrl+ז מבטל)')}
      catch(e){flash('לא הוחל: '+(e.message||e))}};
    ta.addEventListener('keydown',e=>{if(e.key==='Enter'&&(e.ctrlKey||e.metaKey)){e.preventDefault();go()}else if(e.key==='Escape'){e.preventDefault();ovClose()}});
    d.querySelectorAll('.ovbtns button').forEach(b=>{b.addEventListener('mousedown',e=>e.preventDefault());b.onclick=()=>b.dataset.a==='okedit'?go():ovClose()})}
  /* טקסט שנערך ביד: אם לא השתנה דבר מלבד מחיקת מילים/תווים, שומרים את עיצוב המקור (הסבר, פסוק) על המילים שנשארו */
  function ovKeepTags(h,txt){return ovPlain(h).replace(/\s+/g,' ').trim()===txt?h:ge(txt)}
  /* ההחלה: מרכיבים את הקטע (יחידה אחת) בפורמט הביניים של סכם, מחליפים את השורה, ו-skmApply כותב את הרשומות */
  function ovApply(it,s){
    if(typeof skmApply!=='function'||typeof SKC==='undefined')throw new Error('מנגנון ההחלה של סכם אינו זמין בדף');
    if(typeof EDIT!=='undefined'&&!EDIT&&typeof setEdit==='function')setEdit(true);
    const os=skmUnits([it.u]);if(!os.length)throw new Error('היחידה לא נמצאה');
    const orig=skmInter(os),L=orig.split('\n');
    /* כותרת: השורה [כותרת-נושא:...] / [כותרת-דה:...] - מקומה נעול ונוסחה פתוח (sakem_core). רק החלפת נוסח */
    if(it.head){
      if(s.kind!=='replace')throw new Error('בכותרת רק קיצור נוסח');
      const hi=L.findIndex(x=>/^\[כותרת-(נושא|דה):/.test(x));if(hi<0)throw new Error('הכותרת לא נמצאה בקטע');
      const hm=/^\[(כותרת-(?:נושא|דה)):(.*)\]$/.exec(L[hi]);
      if(!hm||ovNorm(SKC.bare(SKC.i2h(hm[2])))!==ovNorm(ovPlain(it.html)))throw new Error('הכותרת השתנתה מאז ההצעה. המחולל ירוץ שוב');
      const LH=L.slice();LH[hi]='['+hm[1]+':'+SKC.h2i(s.html).replace(/\s+/g,' ').trim()+']';
      const textH=LH.join('\n'),errsH=SKC.acceptErrs(orig,textH);
      if(errsH&&errsH.length)throw new Error(errsH.map(e=>e.msg||e).join('; '));
      const rH=skmApply({ids:[it.u],orig,text:textH,hdel:[]},textH);
      return rH&&rH.n!==undefined?rH.n:1}
    /* שורות התוכן של היחידה: כל מה שאינו נעול ואינו כותרת צד */
    const content=[];L.forEach((x,i)=>{if(!/^\[(דף|מקור|משנה|גמרא|קבוע|כותרת-|צד:)/.test(x))content.push(i)});
    const at=content[it.li-1];if(at===undefined)throw new Error('השורה לא נמצאה בקטע');
    const old=L[at],pm=/^\((תשובה|רווח|מעוין|נושא|דה|רקע|נקודה|משנה)\)\s*/.exec(old),pre=pm?pm[0]:'',oldBody=old.slice(pre.length);
    if(ovNorm(SKC.bare(SKC.i2h(oldBody)).replace(/\[תוס':[^\]]*\]/g,''))!==ovNorm(ovPlain(it.html)))throw new Error('השורה השתנתה מאז ההצעה. המחולל ירוץ שוב אחרי הפרסום');
    const tos=[...oldBody.matchAll(/\[תוס':([^\]]*)\]/g)].map(m=>m[1]);
    const T=(typeof skmTos==='function'?skmTos(D.pages[os[0].pi].daf):[]);
    /* עוגני התוספות שהיו בשורה חוזרים אחרי טקסט העוגן שלהם; עוגן שטקסטו נמחק - עצירה, לא אובדן שקט */
    const putTos=(line)=>{tos.forEach(n=>{if(line.indexOf('[תוס\':'+n+']')>-1)return;const z=T.find(q=>q.n===n);
        const p=z&&z.t?line.indexOf(z.t):-1;if(p<0)throw new Error('עוגן תוספות '+n+' היה בשורה וטקסטו השתנה. ערוך ביד');
        line=line.slice(0,p+z.t.length)+'[תוס\':'+n+']'+line.slice(p+z.t.length)});return line};
    const one=h=>SKC.h2i(h).replace(/\s+/g,' ').trim();
    let rep;
    if(s.kind==='split'){
      const a=one(s.parts[0]),b=one(s.parts[1]);
      /* עוגן תוספות - לחלק שבו טקסט העוגן נמצא */
      const ab=putTos(a+'\u0001'+b).split('\u0001');
      rep=[pre+ab[0]].concat(s.side?['[צד:'+s.side+']']:[]).concat([ab[1]])}
    else if(s.kind!=='join')rep=[pre+putTos(one(s.html))];
    /* פרומפט 44, כלי 5: איחוי עם השורה הסמוכה. השורה יוצאת, והסמוכה מקבלת את שתיהן (עוגני התוספות של שתיהן נשמרים) */
    if(s.kind==='join'){
      const ti=content[it.li-1+(s.target==='prev'?-1:1)];if(ti===undefined)throw new Error('השורה הסמוכה לא נמצאה');
      const tOld=L[ti],tm=/^\((תשובה|רווח|מעוין|נושא|דה|רקע|נקודה|משנה)\)\s*/.exec(tOld),tp=tm?tm[0]:'',tBody=tOld.slice(tp.length);
      if(ovNorm(SKC.bare(SKC.i2h(tBody)).replace(/\[תוס':[^\]]*\]/g,''))!==ovNorm(ovPlain(s.targetOrig||'')))throw new Error('השורה הסמוכה השתנתה מאז ההצעה');
      [...tBody.matchAll(/\[תוס':([^\]]*)\]/g)].forEach(m=>{if(tos.indexOf(m[1])<0)tos.push(m[1])});
      const L3=L.slice();L3[ti]=(s.target==='prev'?tp:pre)+putTos(one(s.html));L3.splice(at,1);
      const text3=L3.join('\n');const errs3=SKC.acceptErrs(orig,text3);
      if(errs3&&errs3.length)throw new Error(errs3.map(e=>e.msg||e).join('; '));
      const r3=skmApply({ids:[it.u],orig,text:text3,hdel:[]},text3);
      return r3&&r3.n!==undefined?r3.n:1}
    const L2=L.slice(0,at).concat(rep,L.slice(at+1));
    let extra=null;
    if(s.kind==='move'){
      const ti=content[it.li-1+(s.target==='prev'?-1:1)];if(ti===undefined)throw new Error('השורה הסמוכה לא נמצאה');
      const tIdx=ti+(ti>at?rep.length-1:0),tOld=L2[tIdx],tm=/^\((תשובה|רווח|מעוין|נושא|דה|רקע|נקודה|משנה)\)\s*/.exec(tOld),tp=tm?tm[0]:'';
      L2[tIdx]=tp+one(s.targetHtml);extra=1}
    const text=L2.join('\n');
    const errs=SKC.acceptErrs(orig,text);
    if(errs&&errs.length)throw new Error(errs.map(e=>e.msg||e).join('; '));
    const r=skmApply({ids:[it.u],orig,text,hdel:[]},text);
    return r&&r.n!==undefined?r.n:1}
  /* לחיצה על שורה מסומנת פותחת את החלונית (לא כשמסמנים טקסט בגרירה) */
  document.addEventListener('click',e=>{
    if(!ovOK()||!OVS.items.length)return;
    if(OVS.pop&&OVS.pop.contains(e.target))return;
    const p=e.target.closest&&(e.target.closest('#flow .main > p')||e.target.closest('#flow .row.nose > .main,#flow .row.dh > .main'));
    const it=p&&OVS.byP.get(p);
    if(!it){if(OVS.pop)ovClose();return}
    const sel=getSelection();if(sel&&!sel.isCollapsed)return;
    ovOpen(it)},true);
  document.addEventListener('keydown',e=>{
    if(!OVS.pop||e.target.closest&&e.target.closest('.ovta'))return;
    if(e.key==='Escape'){e.preventDefault();e.stopPropagation();ovClose()}
    else if(e.key==='Tab'){e.preventDefault();e.stopPropagation();ovSkip(e.shiftKey?-1:1)}
    else if(e.key==='Enter'&&!e.ctrlKey&&!e.shiftKey){const it=OVS.cur;if(it&&it.sug[OVS.alt]){e.preventDefault();e.stopPropagation();ovAct('ok')}}},true);
  (function(){const s=document.createElement('style');s.textContent=
    '::highlight(ovline){text-decoration:underline wavy #c62828;text-decoration-thickness:1px;text-underline-offset:3px}'+
    '::highlight(ovword){color:#c62828}'+
    '#flow .main p.ovfb,#flow .main.ovfb{text-decoration:underline wavy #c62828 1px;text-underline-offset:3px}'+
    '.ovpop{position:fixed;z-index:60;max-width:min(560px,94vw);background:#fff;border:1px solid #c9bfa8;border-radius:8px;box-shadow:0 6px 24px rgba(0,0,0,.22);padding:10px 12px;font:15px/1.6 inherit;color:#2b2620}'+
    '.ovhd{font-weight:700;color:#c62828;margin-bottom:6px}.ovdaf{float:left;color:#8a7d66;font-weight:400}'+
    '.ovtool{font-size:12px;color:#8a7d66;margin-bottom:3px}.ovl{font-family:Frank,serif;font-size:17px;line-height:1.7}.ovnb{color:#5a5044}'+
    '.ovsplit .ovl{border-right:2px solid #c9bfa8;padding-right:6px;margin:2px 0}.ovside{font-weight:700;color:#2e5b8a;margin-left:6px;font-size:.85em}'+
    '.ovdel{color:#9a3b3b}.ovadd{color:#1f6b3a}.ovnone{color:#5a5044}'+
    '.ovbtns{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}.ovbtns button{font:inherit;font-size:14px;border:1px solid #c9bfa8;background:#f7f4ee;border-radius:5px;padding:3px 12px;cursor:pointer}'+
    '.ovbtns button.ovp{background:#2e7d3c;border-color:#2e7d3c;color:#fff}.ovbtns button.ovskip{border-color:#2e5b8a;color:#2e5b8a;font-weight:700}.ovbtns button.ovall{flex-basis:100%}'+
    '.ovkeys{font-size:11px;color:#8a7d66;margin-top:4px}.ovta{width:100%;font:17px/1.6 Frank,serif;box-sizing:border-box}'+
    '@media print{.ovpop,.ovtop{display:none!important}}';document.head.appendChild(s)})();
  setTimeout(()=>{ovLoad().catch(()=>{})},2600);
  /* פרומפט 49 חלק 0 (17.11.2026): הכרעות "שורה שהתארכה" נשמרות לתמיד (data/overflow/keep/<מסכת>.json).
     למנהל: אם שורה שהוכרעה אינה עוד פסקה בדף (נדרסה, למשל בקבלת הצעת סכם שנכתבה על נוסח ישן) - הודעה בקול,
     עם הדף והמילים הראשונות. בלי רקע ובלי לגעת בטקסט. הבודק של ההפקה (tools/overflow/keep.py) עוצר את המסירה. */
  async function ovKeepCheck(){
    if(!ovOK()||typeof D==='undefined'||!D.pages)return;
    /* מחכים שהעריכות של המנהל מן השרת יוחלו על הנתונים (syncNow מסמן __LGSYNC) */
    for(let i=0;i<40&&!window.__LGSYNC;i++)await new Promise(r=>setTimeout(r,1500));
    await new Promise(r=>setTimeout(r,3000));
    let doc=null;
    try{const r=await fetch(OV_RAW+'keep/'+SLUG+'.json?t='+Math.floor(Date.now()/300000),{cache:'no-store'});if(r.ok)doc=await r.json()}catch(e){}
    if(!doc||!doc.items||!doc.items.length)return;
    const K=s=>String(s||'').replace(/<[^>]+>/g,'').replace(/&[^;]+;/g,'').replace(/[^א-ת0-9]/g,'');
    const have=new Set();D.pages.forEach(pg=>(pg.units||[]).forEach(u=>(u.l||[]).forEach(x=>have.add(K(x&&x[1])))));
    const lost=[];doc.items.forEach(it=>(it.lines||[]).forEach(ln=>{if(!have.has(K(ln)))lost.push((it.daf?it.daf+' ':'')+ln.split(' ').slice(0,4).join(' '))}));
    OVS.keepLost=lost;
    if(lost.length)toast('שורה שהתארכה: '+lost.length+' הכרעות שלך אינן עוד בדף כפי שהוכרעו: '+lost.slice(0,4).join(' | ')+(lost.length>4?' ...':''),12000)}
  setTimeout(()=>{ovKeepCheck().catch(()=>{})},9000);
  /* =================== פרומפט 53 (17.11.2026): איחוי אוטומטי - "מה שנכנס נשאר" ===================
     המרשם האוטומטי (keep/<מסכת>.auto.json) - כל שורה שבהדפסה בשורה אחת - נטען ל-window.__OVLOCK, ו-skmApply
     חוסם בו קבלת הצעה שנכתבה על נוסח ישן. היומן (auto/<מסכת>.json) - מה שהוחל לבד: כפתור בסרגל פותח רשימה
     (דף, לפני, אחרי, כלי) עם "בטל" אחד לכל שורה. בטל מחזיר את הנוסח ונרשם כ"השאר", כדי שלא יוחל שוב.
     ליד שורה שהוחלה בשבוע האחרון - נקודה זעירה בשוליים, בלי רקע מאחורי הטקסט. */
  const OVA={log:[],undone:new Set()};
  async function ovAutoLoad(){
    if(!ovOK())return;
    const get=async f=>{try{const r=await fetch(OV_RAW+f+'?t='+Math.floor(Date.now()/300000),{cache:'no-store'});if(r.ok)return await r.json()}catch(e){}return null};
    const lk=await get('keep/'+SLUG+'.auto.json');
    if(lk&&lk.items)window.__OVLOCK=new Set(Object.values(lk.items).map(x=>String(x.k||'').replace(/[0-9]/g,'')).filter(Boolean));
    const lg=await get('auto/'+SLUG+'.json');
    OVA.log=((lg&&lg.log)||[]).filter(e=>!e.undone);
    /* הכרעות "השאר" שנרשמו מן היומן (rs=undo) - לא מוצגות עוד, גם לפני שהמחולל רץ */
    Object.keys(OVS.dec||{}).forEach(id=>{const d=OVS.dec[id];if(d&&d.rs==='undo')OVA.undone.add(id)});
    ovAutoMark();ovAutoBar()}
  function ovAutoLive(){return OVA.log.filter(e=>!OVA.undone.has(e.id))}
  function ovAutoParas(e){
    const row=document.getElementById('u'+String(e.key||'').replace(/^u(\d+)\..*$/,'$1'));if(!row)return [];
    const ps=[...row.querySelectorAll(':scope > .main > p')];
    const want=(e.kind==='split'?String(e.after).split(' / '):[e.after]).map(ovNorm);
    return ps.filter(p=>want.indexOf(ovNorm(ovPText(p)))>-1)}
  function ovAutoMark(){
    document.querySelectorAll('#flow p.ovauto').forEach(p=>p.classList.remove('ovauto'));
    const wk=Date.now()-7*864e5;
    ovAutoLive().forEach(e=>{const t=Date.parse(String(e.at||'').replace(' ','T'));if(!(t>wk))return;
      ovAutoParas(e).forEach(p=>{p.classList.add('ovauto');p.title='הוחל אוטומטית ('+(e.toolName||'')+') - אפשר לבטל ברשימת האיחויים האוטומטיים'})})}
  function ovAutoBar(){
    const n=ovAutoLive().length;let b=$('#ovauto');
    if(!n){if(b)b.remove();return}
    if(!b){b=document.createElement('button');b.id='ovauto';b.type='button';b.className='skpbtn skptop ovtop';
      b.addEventListener('mousedown',e=>e.preventDefault());b.onclick=e=>{e.stopPropagation();ovAutoPanel()};
      const after=$('#ovnext')||$('#skpnext')||$('#skpbtn')||$('#peresel');if(after)after.after(b);else ($('#bar')||document.body).appendChild(b)}
    b.textContent='⤶ '+n;b.title='איחויים אוטומטיים: '+n+' שורות שנכנסו לשורה אחת בלי אישור. לחיצה פותחת את הרשימה, עם "בטל" לכל שורה';
    b.setAttribute('aria-label','איחויים אוטומטיים, '+n);
    try{if(typeof barH==='function')barH()}catch(e){}}
  function ovAutoPanel(){
    ovClose();
    const d=document.createElement('div');d.id='ovpop';d.className='ovpop ovapanel';d.setAttribute('role','dialog');d.setAttribute('dir','rtl');
    document.body.appendChild(d);OVS.pop=d;
    const L=ovAutoLive();
    d.innerHTML='<div class="ovhd" style="color:#2b2620">איחויים אוטומטיים · '+L.length+'<span class="ovdaf"><button data-x="1">✕</button></span></div>'+
      '<div class="ovalist">'+L.map((e,i)=>'<div class="ovarow"><div class="ovameta">'+ge(e.daf||'')+' · '+ge(e.toolName||'')+(e.why?' · '+ge(e.why):'')+'</div>'+
        '<div class="ovl">'+(e.kind==='split'?ge(e.before)+'<div class="ovnb">↓ '+ge(String(e.after).split(' / ').join(' ⏎ '))+'</div>':ovDiff(e.before,e.after))+'</div>'+
        '<button data-i="'+i+'">בטל</button></div>').join('')+'</div>';
    d.style.top='60px';d.style.left=Math.max(8,(innerWidth-d.offsetWidth)/2)+'px';
    d.querySelector('[data-x]').onclick=()=>ovClose();
    d.querySelectorAll('.ovarow button').forEach(b=>{b.addEventListener('mousedown',e=>e.preventDefault());b.onclick=()=>{
      const e=L[+b.dataset.i];try{ovAutoUndo(e);b.disabled=true;b.textContent='בוטל';flash('הנוסח הוחזר, ולא יוחל שוב')}catch(er){flash('לא בוטל: '+(er.message||er))}}})}
  /* בטל: אותו מסלול כמו כל עריכה (ovApply -> skmApply). טקסט: מחליף בחזרה. חיתוך: מאחה את שני החלקים לנוסח הקודם */
  function ovAutoUndo(e){
    const u=+String(e.key).replace(/^u(\d+)\..*$/,'$1'),ps=ovAutoParas(e);
    if(!ps.length)throw new Error('השורה כבר אינה בדף כפי שהוחלה (נערכה מאז)');
    const all=[...document.getElementById('u'+u).querySelectorAll(':scope > .main > p')];
    if(e.kind==='split'){
      const parts=String(e.after).split(' / '),i1=all.findIndex(p=>ovNorm(ovPText(p))===ovNorm(parts[0]));
      if(i1<0||!all[i1+1]||ovNorm(ovPText(all[i1+1]))!==ovNorm(parts[1]))throw new Error('שני החלקים אינם עוד זה אחר זה');
      ovApply({u,li:i1+1,html:ge(parts[0])},{kind:'join',target:'next',html:e.beforeH,targetOrig:ge(parts[1])})}
    else{const i1=all.indexOf(ps[0]);ovApply({u,li:i1+1,html:e.afterH},{kind:'replace',html:e.beforeH})}
    OVA.undone.add(e.id);
    const rec={id:e.id,d:'no',rs:'undo',txt:String(e.before).slice(0,1000),det:'auto',kind:'ov'+e.tool+':undo',sug:String(e.after).slice(0,1000),t:Date.now()};
    OVS.dec[e.id]=rec;
    api('/bakara/dec',{method:'POST',body:JSON.stringify({slug:'ov-'+SLUG,items:[rec]})}).catch(er=>toast('הביטול לא נשמר בשרת: '+(er.message||er),5000));
    ovAutoMark();ovAutoBar()}
  setTimeout(()=>{(async()=>{for(let i=0;i<20&&!OVS.loaded;i++)await new Promise(r=>setTimeout(r,500));await ovAutoLoad()})().catch(()=>{})},4000);
  (function(){const s=document.createElement('style');s.textContent=
    '#flow .main p.ovauto{position:relative}#flow .main p.ovauto::after{content:"";position:absolute;right:-9px;top:.7em;width:3px;height:3px;border-radius:50%;background:#b39b62;pointer-events:none}'+
    '.ovapanel{max-height:72vh;overflow:auto;width:min(620px,94vw)}.ovarow{border-top:1px solid #e6dfcf;padding:6px 0;display:flex;flex-wrap:wrap;gap:4px;align-items:flex-start}'+
    '.ovarow .ovl{flex:1 1 80%}.ovameta{flex-basis:100%;font-size:12px;color:#8a7d66}.ovarow button,.ovapanel .ovdaf button{font:inherit;font-size:13px;border:1px solid #c9bfa8;background:#f7f4ee;border-radius:5px;padding:1px 10px;cursor:pointer}'+
    '@media print{#flow .main p.ovauto::after{display:none}}';document.head.appendChild(s)})();
  /* אחרי פרסום, עריכה או מעבר עמוד - הסימון מחושב מחדש (שורה שתוקנה אינה מסומנת עוד) */
  document.addEventListener('input',()=>{clearTimeout(OVS.ti);OVS.ti=setTimeout(()=>{if(OVS.items.length){ovMark();ovBar()}},1200)},true);
  /* הדף נפרס בהדרגה (הזנב נטען בגלילה): שורות שנוספו מסומנות כשהן מגיעות */
  setTimeout(()=>{const f=document.getElementById('flow');if(!f||typeof MutationObserver==='undefined')return;
    new MutationObserver(()=>{if(!OVS.items.length||OVS.pop)return;clearTimeout(OVS.tm);OVS.tm=setTimeout(()=>{ovMark();ovBar()},700)}).observe(f,{childList:true})},3000);
  window.lkOverflow={/* לבדיקות קבלה (פרומפט 53) */_apply:(it,z)=>ovApply(it,z),_skm:(p,t)=>skmApply(p,t),_inter:id=>skmInter(skmUnits([id])),_ed:()=>ED.slice(-6),auto:()=>({log:ovAutoLive().length,lock:window.__OVLOCK?window.__OVLOCK.size:0}),autoLoad:ovAutoLoad,autoUndo:ovAutoUndo,load:ovLoad,mark:ovMark,next:ovNext,keepCheck:ovKeepCheck,state:()=>({items:OVS.items.length,left:ovLeft(),shown:OVS.shown||0,keepLost:OVS.keepLost||null})};
