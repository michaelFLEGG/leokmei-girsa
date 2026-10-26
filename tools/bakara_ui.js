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
  /* פענוח מטען אחד - של הממצא עצמו או של נוסח חלופי (alts). (26.10.2026) נוספו:
       {anchor:{text, rest}}  כותרת הצד (חלון 3) מקבלת את text, ו-rest עובר לראש השורה
       {anchor:{take}}        הדובר שבראש השורה יוצא לכותרת צד (או {anchor:{text}} כשאין כותרת: כותרת חדשה)
       {anchor:{unside:1}}    כותרת הצד חוזרת לשורה
       {heading:{text}}       כותרת נושא חדשה לפני הפסקה ("ניסוח קלוד")
       {nikud:{x,y}}          הפסוק בנוסח המנוקד מן המקרא (החלפה)
       {split:{at}}           פיצול השורה אחרי המילים at
       {join:1}               איחוי הפסקה עם הבאה אחריה */
  function bkOpRaw(o){
    if(!o||typeof o!=='object')return null;
    if(o.rep&&o.rep.x&&o.rep.y!==undefined&&o.rep.x!==o.rep.y)return {t:'rep',x:o.rep.x,y:o.rep.y,unsure:!!o.rep.unsure};
    if(o.nikud&&o.nikud.x&&o.nikud.y&&o.nikud.x!==o.nikud.y)return {t:'rep',x:o.nikud.x,y:o.nikud.y,nik:1};
    if(o.ins&&o.ins.text)return {t:'ins',after:o.ins.after,before:o.ins.before,end:!!o.ins.end,text:String(o.ins.text),cs:o.ins.cs||'hs'};
    if(o.style&&(o.style.cs||o.style.cs===''))return {t:'style',cs:o.style.cs==='plain'?'':o.style.cs,range:o.style.range||''};
    if(o.del&&o.del.range)return {t:'rep',x:o.del.range,y:''};
    if(o.anchor&&(o.anchor.text||o.anchor.take||o.anchor.unside))return {t:'anchor',text:String(o.anchor.text||'').trim(),rest:String(o.anchor.rest||'').trim(),take:String(o.anchor.take||'').trim(),unside:!!o.anchor.unside};
    if(o.heading&&o.heading.text)return {t:'heading',text:String(o.heading.text).trim()};
    if(o.split&&o.split.at)return {t:'split',at:String(o.split.at)};
    if(o.join)return {t:'join'};
    if(o.ask)return {t:'q',why:String(o.ask)};
    if(o.none)return {t:'none',why:String(o.none)};
    return null}
  function bkOp(f){
    if(f._op!==undefined)return f._op;
    let op=bkOpRaw(f.op);
    if(!op){const rp=bkRepFix(f);if(rp)op={t:'rep',x:rp.x,y:rp.y,unsure:rp.unsure}}
    if(!op){const fx=f.fix||'';
      if(/^להחיל סגנון אמוראים/.test(fx))op={t:'style',cs:'am',range:f.mark||''};
      else if(/^להחיל סגנון פסוק/.test(fx))op={t:'style',cs:'ps',range:f.mark||''};
      else if(/^להחזיר לסגנון רגיל/.test(fx))op={t:'style',cs:'',range:f.mark||''}}
    if(!op&&bkTyp(f)==='h')op={t:'q'};
    if(!op)op={t:'none',why:''};
    f._op=op;return op}
  /* עד שלושה נוסחים: המטען עצמו ואחריו החלופות (f.alts, באותו מבנה של f.op). מקש 1/2/3 בוחר ומחיל */
  function bkOpts(f){
    const a=[bkOp(f)];
    for(const x of (Array.isArray(f.alts)?f.alts:[])){const o=bkOpRaw(x);if(o&&/^(rep|ins|style|anchor|heading|split|join)$/.test(o.t))a.push(o)}
    return a.slice(0,3)}
  /* שער התור (26.10.2026): רק ממצא שיש לו פעולה מוכנה להחלה נכנס לתור של המחבר. שאלה למחבר
     (סוג ח) היא היחידה שמותרת בלי מטען. השאר חוזר להפקה, ומוצג בלשונית "ניהול" בלבד */
  const BKEXEC={rep:1,ins:1,style:1,anchor:1,heading:1,split:1,join:1};
  function bkReady(f){const o=bkOp(f);return !!BKEXEC[o.t]||(o.t==='q'&&bkTyp(f)==='h')}
  window.bkReady=bkReady;
  function bkRep(f){const o=bkOp(f);return o.t==='rep'?o:null}
  function bkAction(f){
    const o=bkOp(f);
    if(o.t==='style')return o.cs==='am'?'am':(o.cs==='ps'?'ps':'plain');
    return o.t}
  const BKACT={rep:'החלפה בנוסח',ins:'הוספת הסבר בסוגריים',am:'סגנון אמוראים',ps:'סגנון פסוק',plain:'חזרה לסגנון רגיל',
               anchor:'כותרת צד',heading:'כותרת נושא חדשה',split:'פיצול שורה',join:'איחוי עם השורה הבאה',
               q:'בדיקה או שאלה: אין שינוי בטקסט',none:'אין עדיין הצעה מוכנה'};
  /* ---- התיישנות (19.10.2026): ממצא שהטקסט הנוכחי (כולל עריכות המנהל) כבר מכסה אותו אינו מוצג ---- */
  const BKUSE=/^[ודלכמשבה]{1,3}(?=ר)/;
  /* העריכה האחרונה של מקום, לפי מפתח. בבכורות 7,000 עריכות: ED.find לכל מקום ולכל ממצא היה
     מאות מיליוני השוואות בכל איתור. המפה נבנית פעם אחת לכל גרסת נתונים (26.10.2026) */
  let BKEDM=null;
  function bkEdOf(k){
    if(!BKEDM||BKEDM.ed!==ED||BKEDM.n!==ED.length||BKEDM.v!==DV){const m=new Map();for(const x of ED)if(x&&x.k&&!m.has(x.k))m.set(x.k,x);BKEDM={ed:ED,n:ED.length,v:DV,m}}
    return BKEDM.m.get(k)}
  function bkSlotHtml(s){const old=bkEdOf(s.k);return old?(old.nowH!==undefined?old.nowH:esc(old.now)):s.h}
  /* לכל תו בטקסט: מחלקת הסגנון שלו ('am' / 'ps' / ...), לפי אותו HTML שעל המסך */
  const BKCLC=new Map();
  function bkCharClasses(h){
    let v=BKCLC.get(h);if(v)return v;
    const d=document.createElement('div');d.innerHTML=h;
    const w=document.createTreeWalker(d,NodeFilter.SHOW_TEXT),cl=[];let n,t='';
    while(n=w.nextNode()){const el=n.parentElement&&n.parentElement.closest('i[class]');
      const c=el?el.className:'';
      for(let i=0;i<n.nodeValue.length;i++)cl.push(c);t+=n.nodeValue}
    v={t,cl};if(BKCLC.size>3000)BKCLC.clear();BKCLC.set(h,v);return v}
  function bkStale(f,L){
    const o=bkOp(f),s=L.s,h=bkSlotHtml(s),T=bkCharClasses(h),text=T.t;
    if(o.t==='style'){
      const hit=bkFindIn(text,f);if(!hit||!hit.len)return false;
      let a=0;const mk=hit.sc.c.slice(hit.pos,hit.pos+hit.len);
      const u=BKUSE.exec(mk);if(o.cs==='am'&&u)a=u[0].length;
      const want=o.cs==='ps'?'ps':'am';
      let any=false,all=true;
      for(let i=a;i<hit.len;i++){const oi=hit.sc.m[hit.pos+i],c=' '+(T.cl[oi]||'')+' ';
        const on=(o.cs===''?/ (am|ps|hs|dm|ns) /.test(c):c.indexOf(' '+want+' ')>-1);
        if(on)any=true;else all=false}
      return o.cs===''?!any:all}
    if(o.t==='ins'){
      const tx=bkCompact(o.text).c;if(tx.length<4)return false;
      return bkCC(text).c.indexOf(tx)>-1}
    if(o.t==='rep'){
      const hit=bkFindIn(text,f);
      const xc=bkCompact(o.x).c,yc=bkCompact(o.y).c,all=bkCC(text).c;
      if(hit){const within=all.slice(hit.pos,hit.pos+hit.len);
        if(within.indexOf(xc)<0&&yc&&all.indexOf(yc)>-1&&all.indexOf(xc)<0)return true}
      return false}
    return false}
  /* ממצא שלא אותר: אם נוסח ההחלפה כבר במקום - התיישן (ולא "אבד") */
  function bkStaleLost(f,ix){
    const o=bkOp(f);if(o.t!=='rep'||!o.y)return false;
    const cx=bkCompact((f.context||f.text||'').replace(o.x,o.y)).c,yc=bkCompact(o.y).c;
    if(!cx||cx.indexOf(yc)<0)return false;
    for(const s of bkWin(ix,dafKey(f.daf)))if(bkCC(plain(bkSlotHtml(s))).c.indexOf(cx)>-1)return true;
    return false}
  BK.STALE=new Set();BK.STR=new Set();

  /* ---- עיגון ---- */
  function bkFindIn(text,f){
    const cx=bkCC(f.context||f.text||''),mk=bkCC(f.mark||'').c,sc=bkCC(text);
    let pos=-1,len=mk.length;
    if(cx.c){const p=sc.c.indexOf(cx.c);
      if(p>-1){const off=mk?cx.c.indexOf(mk):0;pos=p+(off>-1?off:0);if(!mk||off<0)len=mk?mk.length:cx.c.length}}
    if(pos<0&&mk){const p=sc.c.indexOf(mk);if(p>-1&&sc.c.indexOf(mk,p+1)<0)pos=p}
    return pos<0?null:{pos,len,sc}}
  /* ---- איתור מהיר (26.10.2026) ----
     אינדקס של מקומות המסכת לפי מזהה יחידה ולפי חלון דפים, שנבנה פעם אחת לכל גרסת נתונים (DV).
     כשהטקסט לא השתנה - אין איתור כלל. כשהשתנו מקומות מעטים (עריכה, קבל) - מאותרים מחדש רק
     הממצאים שבאותן יחידות, ואלה שלא אותרו בחלון הדפים שלהן. איתור מלא רק כשהמבנה זז (פיצול,
     איחוי) או כשנטענו ממצאים חדשים. */
  let BKIX=null;
  function bkIndex(){
    const S=slotsFull();
    if(BKIX&&BKIX.S===S)return {ix:BKIX,changed:new Set()};
    const byU=new Map(),pos=new Map();
    S.forEach((s,i)=>{const u=String(s.id);let a=byU.get(u);if(!a)byU.set(u,a=[]);a.push(s);pos.set(s,i)});
    let changed=null;
    if(BKIX&&BKIX.S.length===S.length){
      changed=new Set();
      for(let i=0;i<S.length;i++){const s=S[i],o=BKIX.S[i];
        if(o.k!==s.k){changed=null;break}
        if(o.t!==s.t||o.h!==s.h)changed.add(s.k)}}
    BKIX={S,byU,pos,win:new Map()};
    return {ix:BKIX,changed}}
  /* המקומות שבחלון של דף אחד לפניו ואחד אחריו (ציון דף לא ידוע - כל המסכת) */
  function bkWin(ix,k0){
    let w=ix.win.get(k0);
    if(!w){w=ix.S.filter(s=>{const k=dafKey(s.daf);return k0===null||k===null||Math.abs(k-k0)<=1});ix.win.set(k0,w)}
    return w}
  function bkLocOne(f,ix){
    const own=ix.byU.get(String(f.u))||[];
    let hits=own.map(s=>[s,bkFindIn(s.t,f)]).filter(x=>x[1]);
    if(hits.length!==1){
      const all=bkWin(ix,dafKey(f.daf)).map(s=>[s,bkFindIn(s.t,f)]).filter(x=>x[1]);
      if(all.length>hits.length||!hits.length)hits=all;
      if(hits.length>1){hits.sort((a,b)=>Math.abs(a[0].id-f.u)-Math.abs(b[0].id-f.u))}}
    if(!hits.length){if(bkStaleLost(f,ix))BK.STR.add(f.id);return}
    const [s,h]=hits[0];
    BK.loc[f.id]={s,k:s.k,pi:s.pi,pos:h.pos,len:h.len,ord:ix.pos.get(s)*100000+h.pos};
    if(bkStale(f,BK.loc[f.id]))BK.STR.add(f.id)}
  /* ממתין שהטקסט כבר מכסה אותו: התיישן. סדר הממצאים לפי מקומם בטקסט */
  function bkStaleSync(){
    BK.STALE=new Set();for(const id of BK.STR){const f=BK.byId[id];if(f&&bkStatus(f)==='pending')BK.STALE.add(id)}
    BK.ord=BK.F.filter(f=>BK.loc[f.id]&&!BK.STALE.has(f.id)).sort((a,b)=>BK.loc[a.id].ord-BK.loc[b.id].ord)}
  function bkLocateAll(force){
    const r=bkIndex(),ix=r.ix;let changed=r.changed;
    if(force||BK.locF!==BK.F||!BK.locIx)changed=null;
    if(changed&&!changed.size&&BK.locIx===ix){bkStaleSync();return}
    let todo;
    if(changed){
      const cu=new Set(),cd=[];
      for(const s of ix.S)if(changed.has(s.k)){const m=/^u(\d+)/.exec(s.k);if(m)cu.add(m[1]);cd.push(dafKey(s.daf))}
      /* המבנה לא זז: רשומת המיקום מפנה לאובייקט שבאינדקס החדש, באותו מקום */
      for(const f of BK.F){const L=BK.loc[f.id];if(L){const s=ix.S[Math.floor(L.ord/100000)];if(s&&s.k===L.k)L.s=s}}
      todo=BK.F.filter(f=>{const L=BK.loc[f.id];
        if(L&&changed.has(L.k))return true;
        if(cu.has(String(f.u)))return true;
        if(!L){const k0=dafKey(f.daf);return cd.some(c=>k0===null||c===null||Math.abs(c-k0)<=1)}
        return false})}
    else{todo=BK.F;BK.loc={};BK.STR=new Set()}
    for(const f of todo){delete BK.loc[f.id];BK.STR.delete(f.id);bkLocOne(f,ix)}
    BK.locIx=ix;BK.locF=BK.F;BK.locN=(BK.locN||0)+1;
    bkStaleSync()}
  /* מיקום ב-DOM: טווח סימון בתוך האלמנט, לפי אותו מדד דחוס */
  /* ctx (לא חובה): {els: מפה מפתח->אלמנט של כל מה שעל המסך, tx: מטמון טקסט לאלמנט} - כשמסמנים
     ממצאים רבים בבת אחת, הדף נסרק פעם אחת ולא פעם לכל ממצא */
  function bkElText(el,tx){
    let v=tx&&tx.get(el);if(v)return v;
    const w=document.createTreeWalker(el,NodeFilter.SHOW_TEXT,{acceptNode(n){
      return n.parentElement&&n.parentElement.closest('.srcb,.mlabel,.bkx')?NodeFilter.FILTER_REJECT:NodeFilter.FILTER_ACCEPT}});
    let n,text='';const at=[];
    while(n=w.nextNode()){for(let i=0;i<n.nodeValue.length;i++)at.push([n,i]);text+=n.nodeValue}
    v={text,at};if(tx)tx.set(el,v);return v}
  function bkElMap(){const m=new Map(),fl=$('#flow');if(fl)for(const el of fl.querySelectorAll('[data-ek]'))if(!m.has(el.dataset.ek))m.set(el.dataset.ek,el);return m}
  function bkDomRange(f,ctx){
    const L=BK.loc[f.id];if(!L)return null;
    const el=ctx?ctx.els.get(L.k):$('#flow').querySelector('[data-ek="'+L.k+'"]');if(!el)return null;
    const T=bkElText(el,ctx&&ctx.tx),at=T.at;
    const h=bkFindIn(T.text,f);if(!h||!h.len)return null;
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
      '.bkcard{position:fixed;z-index:1250;width:min(340px,94vw);background:#fffdf8;border:1px solid #c9b98f;border-radius:8px;box-shadow:0 6px 22px rgba(0,0,0,.28);padding:9px 12px;font-size:15px;line-height:1.5;direction:rtl}'+
      '.bkcard .h{display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-bottom:3px}.bkcard .h .x{margin-right:auto;background:none;border:0;font-size:20px;cursor:pointer;color:#5a5044;line-height:1}'+
      '.bkchip{display:inline-block;color:#fff;border-radius:10px;padding:0 8px;font-size:12px}.bkcard .nt{font-weight:600}.bkcard .ev{font-size:13px;color:#5a5044;border-right:3px solid #d9d1bd;padding-right:7px;margin:3px 0}'+
      '.bkcard .fx{margin:4px 0;background:#f3efe3;border-radius:4px;padding:3px 7px;font-size:15px}.bkcard del{color:#a83c2f;background:#fbe5e1}.bkcard ins{color:#2e6b3f;background:#e3f3e6;text-decoration:none}.bkcard ins.hs{color:#4a4137;font-size:.92em}.bkcard .fx.dim{background:none;color:#8a7d66;font-size:13px}'+
      '.bkcard .bt{display:flex;gap:6px;margin-top:6px;flex-wrap:wrap}.bkcard .bt button{font:inherit;font-size:14px;border:1px solid #b9a97c;border-radius:5px;background:#f6f1e2;padding:2px 12px;cursor:pointer}'+
      '.bkcard .bt button.ok{background:#2e6b3f;color:#fff;border-color:#2e6b3f}.bkcard .bt button.no{color:#a83c2f}.bkcard input[type=text]{width:100%;box-sizing:border-box;font:inherit;font-size:14px;margin-top:5px}'+
      '.bkcard .dim{font-size:12px;color:#8a7d66}.bkcard .kk{font-size:10px;opacity:.7;margin-right:3px;direction:ltr;unicode-bidi:isolate}'+
      '.bkbar{position:fixed;left:12px;bottom:12px;z-index:1240;background:#fffdf8;border:1px solid #c9b98f;border-radius:8px;box-shadow:0 3px 14px rgba(0,0,0,.22);padding:5px 10px;font-size:14px;display:flex;gap:8px;align-items:center;flex-wrap:wrap;direction:rtl;max-width:94vw}'+
      'body.ed .bkbar{bottom:56px}.bkbar button{font:inherit;font-size:14px;border:1px solid #b9a97c;border-radius:5px;background:#f6f1e2;padding:1px 10px;cursor:pointer}.bkbar button.go{background:#2e5b8a;color:#fff;border-color:#2e5b8a}'+
      '#bkp .grp{margin:8px 0;border:1px solid #e0d8c4;border-radius:6px;background:#fff}#bkp .grp>summary{cursor:pointer;padding:4px 8px;font-weight:600}'+
      '#bkp .grp .gb{padding:0 8px 6px}#bkp .it{padding:4px 6px;border-bottom:1px dotted #d9d1bd;cursor:pointer}#bkp .it:hover{background:#f6f1e2}#bkp .it.cur{outline:2px solid #c9a24a}'+
      '#bkp .it small{color:#8a7d66}#bkp .it .mk{font-weight:600;color:#2b2620}#bkp select{font:inherit;font-size:14px;margin:2px}#bkp .gbt button{font:inherit;font-size:13px;margin:2px 0 2px 4px;border:1px solid #b9a97c;border-radius:5px;background:#f6f1e2;padding:1px 9px;cursor:pointer}'+
      '.bkbar .bkprog{display:inline-block;width:90px;height:6px;background:#eee6cf;border-radius:3px;overflow:hidden;vertical-align:middle}.bkbar .bkprog i{display:block;height:100%;background:#2e6b3f}'+
      '::highlight(bk-del){text-decoration:line-through;text-decoration-color:#8a7d66;color:#9a8f7c}::highlight(bk-prev){background-color:rgba(46,107,63,.18)}'+
      '.bkx-ins{color:#1f6b3a;background:#e3f3e6;border-radius:3px;padding:0 2px}.bkx-hs{font-size:.9em}.bkx-side{font-weight:700}.bkx-br{color:#1f6b3a;font-weight:700}'+
      '.bkx-head{color:#1f6b3a;background:#eef8f0;font-weight:700;border-right:3px solid #2e6b3f;padding:1px 8px;margin:4px 0;border-radius:3px}'+
      '.bkcard .sug{margin:6px 0 2px;font-size:16px;line-height:1.6}.bkcard .sug ins,.bkcard .alt ins{color:#1f6b3a;background:#e3f3e6;text-decoration:none}.bkcard .sug del,.bkcard .alt del{color:#8a7d66;background:none}'+
      '.bkcard .alts{display:flex;flex-direction:column;gap:4px;margin:6px 0}.bkcard .alt{font:inherit;font-size:15px;text-align:right;border:1px solid #d9d1bd;background:#fff;border-radius:6px;padding:3px 8px;cursor:pointer}.bkcard .alt.on{border-color:#2e6b3f;box-shadow:0 0 0 2px rgba(46,107,63,.18)}.bkcard .alt b{display:inline-block;min-width:1.2em;color:#2e6b3f}'+
      'body .bkcard .bt button{padding:3px 8px;min-height:32px;gap:3px}body .bkcard .bt button .kk{margin:0}.bkcard .bt button.why{margin-right:auto}.bkcard .whyb{margin-top:6px;border-top:1px dashed #d9d1bd;padding-top:5px}.bkcard .whyb[hidden]{display:none}.bkcard .bt.bksrc button{font-size:12px;padding:0 8px}'+
      '.bkrs{position:fixed;left:50%;transform:translateX(-50%);bottom:70px;z-index:1250;background:#fffdf8;border:1px solid #c9b98f;border-radius:8px;box-shadow:0 3px 14px rgba(0,0,0,.2);padding:4px 8px;font-size:14px;display:flex;gap:6px;align-items:center;direction:rtl}.bkrs button{font:inherit;font-size:13px;border:1px solid #b9a97c;border-radius:5px;background:#f6f1e2;padding:1px 8px;cursor:pointer}'+
      '@media print{.bkcard,.bkbar,.bkx,.bkrs{display:none!important}}';
    document.head.appendChild(st)}
  function bkHL(){
    const f=$('#flow');BK.R=[];
    if(!window.CSS||!CSS.highlights||typeof Highlight==='undefined')return;
    const H={'bk-todo':new Highlight(),'bk-cur':new Highlight()};Object.keys(SKT).forEach(k=>{H['bk-t'+k]=new Highlight()});
    if(BK.ON&&f&&!f.classList.contains('book')){
      const ctx={els:bkElMap(),tx:new Map()};
      for(const fd of BK.ord){
        if(SK.mode&&fd.id!==BK.curId)continue;
        const st=bkStatus(fd);if(st!=='pending'&&st!=='todo')continue;
        const r=bkDomRange(fd,ctx);if(!r)continue;
        BK.R.push({f:fd,range:r.range,el:r.el});
        H[st==='todo'?'bk-todo':'bk-t'+bkTyp(fd)].add(r.range);
        if(fd.id===BK.curId)H['bk-cur'].add(r.range)}}
    for(const k in H){if(H[k].size)CSS.highlights.set(k,H[k]);else CSS.highlights.delete(k)}
    BK.hlCur=BK.curId;BK.hlN=BK.locN;BK.hlD=BK.decN}
  /* מעבר בין ממצאים בלי שינוי בטקסט: רק הדגשת הנוכחי מתחלפת */
  function bkHLCur(){
    if(!window.CSS||!CSS.highlights||typeof Highlight==='undefined'||SK.mode){bkHL();return}
    let r=BK.R.find(x=>x.f.id===BK.curId);
    if(!r&&BK.curId&&BK.byId[BK.curId]){const fd=BK.byId[BK.curId],d=bkDomRange(fd);if(d){r={f:fd,range:d.range,el:d.el};BK.R.push(r)}}
    const h=new Highlight();if(r)h.add(r.range);
    if(h.size)CSS.highlights.set('bk-cur',h);else CSS.highlights.delete('bk-cur');BK.hlCur=BK.curId}
  let BKT=null;function bkSoon(){if(!BK.ON)return;clearTimeout(BKT);BKT=setTimeout(()=>{bkRefresh()},120)}
  function bkRefresh(){if(!BK.loaded)return;bkLocateAll();if(BK.hlN!==BK.locN||BK.hlD!==BK.decN)bkHL();else bkHLCur();bkCount();if($('#bkp')&&$('#bkp').classList.contains('open'))skDrawPanel();if(SK.mode)skPassDraw();else bkBarDraw();if(window.skAutoSoon)skAutoSoon()}
  window.bkMark=function(){if(BK.loaded&&BK.ON){bkLocateAll();bkHL();bkCount();bkBarDraw()}};
  /* (26.10.2026) אין עוד MutationObserver על כל הזרם: כל שינוי טקסט עובר בנתונים (DV), והנתונים
     מודיעים כאן. שינוי זעיר בזרם הפעיל בעבר איתור מלא של כל הממצאים (כ-10 שניות קיפאון).
     ציור מחדש של פרק מודיע בעצמו (render קורא ל-bkMark). */
  document.addEventListener('lg-dv',()=>{if(BK.ON&&BK.loaded)bkSoon()});

  /* ---- טעינה: רק למכשיר שהוכר כמנהל ---- */
  function bkPend(f){return bkStatus(f)==='pending'&&!(SK.autoQ&&SK.autoQ.has(f.id))&&!BK.STALE.has(f.id)&&bkReady(f)}
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
    /* ההצעה שהוצגה (הנוסח שנבחר, אם היו כמה): חומר הלמידה של הסוקר. alt = מספר הנוסח שנבחר */
    {const ai=(BK.alt&&BK.alt[f.id])||0,o=bkOpts(f)[ai]||bkOp(f);const sg=bkSugText(o)||(f.fix||'');if(sg&&d!=='pending')it.sug=String(sg).slice(0,900);if(ai&&d!=='pending')it.alt=ai}
    BK.decN=(BK.decN||0)+1;
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
    /* סקירה פעילה: טיימרים שאינם נחוצים לה (מקום הקריאה, סרגל הטלפון, סימני הנוסחאות והתוס') מושהים */
    document.body.classList.toggle('bk-on',BK.ON);
    if(!BK.ON&&window.sqResume)setTimeout(sqResume,300);
    if(!BK.ON){bkHideCard(true);const m=$('#bkbar');if(m)m.remove();{const x=$('#skpass');if(x)x.remove();SK.mode=''}bkHL();bkCount();return}
    bkRefresh();bkBarDraw();
    if(!BK.ord.length)toast('אין הערות סקירה למסכת הזאת. אפשר לבקש סקירה מהחלונית.')}
  window.bkToggle=bkToggle;
  /* קצב ההכרעה: חציון הזמן בין הכרעות רצופות של המחבר (בין חצי שנייה לדקה); בלעדיו 6 שניות */
  function bkPace(){
    const ts=Object.values(BK.DEC).filter(d=>d&&!d.auto&&d.t).map(d=>d.t).sort((a,b)=>a-b),g=[];
    for(let i=1;i<ts.length;i++){const x=ts[i]-ts[i-1];if(x>500&&x<60000)g.push(x)}
    if(g.length<5)return 6000;g.sort((a,b)=>a-b);return g[g.length>>1]}
  /* סרגל אחד פשוט (26.10.2026): "נשארו 41 בפרק · כ-3 דקות" ומד התקדמות. מה שלא אותר, שהתיישן או
     שחזר להפקה - בלשונית "ניהול" ולא כאן */
  function bkBarDraw(){
    if(!BK.ON)return;let m=$('#bkbar');
    if(!m){m=document.createElement('div');m.id='bkbar';m.className='bkbar';document.body.appendChild(m)}
    const sec=SEC[cur]||{from:0,to:0};let ns=0,nt=0,na=0;
    for(const f of BK.F){
      const L=BK.loc[f.id];if(!L||!bkReady(f)||BK.STALE.has(f.id)||(SK.autoQ&&SK.autoQ.has(f.id)))continue;
      const st=bkStatus(f),inS=L.pi>=sec.from&&L.pi<=sec.to;
      if(inS){nt++;if(st==='pending')ns++}
      if(st==='pending')na++}
    const mins=Math.max(1,Math.round(ns*bkPace()/60000)),pct=nt?Math.round(100*(nt-ns)/nt):100;
    m.innerHTML='<b>סקירה</b><span class="bkleft">'+(ns?'נשארו '+ns+' בפרק · כ-'+mins+' דקות':'הפרק הושלם')+
      (na>ns?' <small class="dim">('+na+' במסכת)</small>':'')+'</span>'+
      '<span class="bkprog" title="'+pct+'% מן הפרק"><i style="width:'+pct+'%"></i></span>'+
      skNextBtnHtml()+
      '<button onclick="bkNext(-1)" title="להערה הקודמת">↑</button>'+
      '<button onclick="bkPanel()">רשימה</button><button onclick="bkToggle()">סיום</button>'+
      '<span class="kk" style="font-size:11px;opacity:.7" title="Enter קבל · Delete דחה · E ערוך בשורה · 1/2/3 נוסח · S דלג · ? למה · ←/→ הבאה/קודמת · Ctrl+Z ביטול">Enter · Del · E · 1-3 · S · ?</span>';
    if(window.skBarExtra)skBarExtra(m);if(window.skBarEnd)skBarEnd(m);
    {const l=bkSides().lo+12+'px';if(m.style.left!==l)m.style.left=l}}
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
  /* ---- כרטיס צף (26.10.2026): ההצעה היא הכרטיס ----
     השורה שבטקסט כבר מוצגת במצב "אחרי" (bkPrevShow). בכרטיס: שם הסוג, ההצעה במילים ספורות, והכפתורים.
     הנימוק (מה הבעיה, הציטוט מן הגמרא, המקור בצד) מקופל מאחורי "למה?" (או ?), וסגור כברירת מחדל.
     עד שלושה נוסחים: 1/2/3 בוחר ומחיל. שום כפתור אינו פותח חלון ביניים. */
  function bkSugHtml(f,op){
    const q=s=>'«'+esc(s)+'»';
    if(op.t==='rep')return op.y?'<del>'+esc(op.x)+'</del> ← <ins>'+esc(op.y)+'</ins>'+(op.nik?' <span class="dim">(ניקוד המקרא)</span>':''):'מחיקת <del>'+esc(op.x)+'</del>';
    if(op.t==='ins')return '<ins class="hs">['+esc(bkInsText(op.text))+']</ins> <span class="dim">'+(op.end?'בסוף הפסקה':(op.before!==undefined&&op.after===undefined?'לפני ':'אחרי ')+(op.end?'':q(op.after||op.before||f.mark||'')))+'</span>';
    if(op.t==='style')return esc(BKACT[op.cs==='am'?'am':(op.cs==='ps'?'ps':'plain')])+': <mark>'+esc(op.range||f.mark||'')+'</mark>';
    if(op.t==='anchor'){
      if(op.unside)return 'כותרת הצד חוזרת לשורה';
      if(op.take)return 'הדובר '+q(op.take)+' יוצא לכותרת צד'+(op.text&&op.text!==op.take?': <ins>'+esc(op.text)+'</ins>':'');
      return 'כותרת צד: <ins>'+esc(op.text)+'</ins>'+(op.rest?' · לשורה: <ins>'+esc(op.rest)+'</ins>':'')}
    if(op.t==='heading')return 'כותרת נושא: <ins>'+esc(op.text)+'</ins>';
    if(op.t==='split')return 'פיצול השורה אחרי '+q(op.at);
    if(op.t==='join')return 'איחוי עם השורה הבאה';
    if(op.t==='q')return esc(op.why||f.fix||'שאלה למחבר')+' <span class="dim">(Enter: נענתה, בלי שינוי בטקסט)</span>';
    return '<span class="dim">אין עדיין הצעה מוכנה. Enter מחזיר להפקה ועובר להבאה.</span>'}
  function bkHideCard(force){
    const c=$('#bkcard');if(!c)return;
    if(BK.pin&&!force)return;
    c.remove();BK.pin=false;BK.cardId='';bkPrevClear()}
  function bkAltI(f){const n=bkOpts(f).length;let i=(BK.alt&&BK.alt[f.id])||0;return i<n?i:0}
  function bkCardOp(f){return bkOpts(f)[bkAltI(f)]}
  function bkShowCard(f,pin,rect){
    if(SK.mode&&!window.SKCARD){return}
    const old=$('#bkcard');if(old&&old.dataset.id===f.id&&(!pin||BK.pin)){return}
    if(old)old.remove();
    const c=document.createElement('div');c.className='bkcard';c.id='bkcard';c.dataset.id=f.id;
    const st=bkStatus(f),sn=bkSplitNote(f),dec=BK.DEC[f.id],opts=bkOpts(f),ai=bkAltI(f),op=opts[ai];
    const pend=st==='pending'||st==='todo';
    const B=(cls,on,lab,k,tip)=>'<button'+(cls?' class="'+cls+'"':'')+' onmousedown="event.preventDefault()" onclick="'+on+'"'+(tip?' title="'+esc(tip)+'"':'')+'>'+lab+(k?' <small class="kk">'+k+'</small>':'')+'</button>';
    let h='<div class="h"><span class="bkchip" style="background:'+SKT[bkTyp(f)][1]+'">'+esc(SKT[bkTyp(f)][0])+'</span>'+
      '<span class="dim">'+esc(f.daf?'דף '+f.daf:'')+'</span>'+
      '<button class="x" onmousedown="event.preventDefault()" onclick="bkHideCard(true)" aria-label="סגירה">×</button></div>';
    if(opts.length>1)h+='<div class="alts">'+opts.map((o,i)=>'<button class="alt'+(i===ai?' on':'')+'" onmousedown="event.preventDefault()" onclick="bkAltPick(\''+f.id+'\','+i+',1)" title="נוסח '+(i+1)+' - מקש '+(i+1)+'"><b>'+(i+1)+'</b> '+bkSugHtml(f,o)+'</button>').join('')+'</div>';
    else h+='<div class="sug">'+bkSugHtml(f,op)+'</div>';
    if(pend){
      const nop=!BKEXEC[op.t]&&op.t!=='q';
      h+='<div class="bt">'+B('ok','bkAcceptClick(\''+f.id+'\')',nop?'החזר להפקה':'קבל','Enter',BKACT[bkAction(f)])+
        B('no','bkRejectNow(\''+f.id+'\')','דחה','Del')+
        B('','bkDecide(\''+f.id+'\',\'edit\')','ערוך','E','עריכה בתוך השורה עצמה; Alt+Enter מאשר')+
        B('','skSkip(\''+f.id+'\')','דלג','S')+
        B('why','bkWhy()','למה?','?')+'</div>'}
    else h+='<div class="dim">'+(dec?({ok:'התקבל',no:'נדחה',edit:'נערך',todo:'אושר לביצוע'}[dec.d]||''):'')+(dec&&dec.txt?' · '+esc(dec.txt):'')+'</div>'+
      '<div class="bt">'+B('','bkDecide(\''+f.id+'\',\'pending\')','החזר לממתינים','')+B('why','bkWhy()','למה?','?')+'</div>';
    h+='<div class="whyb" id="bkwhyb"'+(BK.whyOpen?'':' hidden')+'><div class="nt">'+esc(sn.n)+'</div>'+
      (sn.e?'<div class="ev">בגמרא: '+esc(sn.e)+'</div>':'')+
      (f.fix&&op.t==='none'?'<div class="fx">'+esc(f.fix)+'</div>':'')+
      '<div class="dim">'+esc(f.kind||'')+(f.sev?' · '+esc(f.sev):'')+(f.conf?' · ביטחון '+esc(f.conf):'')+(f.layer?' · '+esc(f.layer):'')+'</div>'+
      '<div class="bt bksrc">'+B('','skSplit(\'gp\')','גמרא ופירוש','')+B('','skSplit(\'g\')','גמרא','')+B('','skChat(\''+f.id+'\')','שוחח','C')+'</div>'+
      '<div id="skchat" class="skchat" style="display:none"></div></div>';
    c.innerHTML=h;
    document.body.appendChild(c);BK.pin=!!pin;BK.cardId=f.id;
    if(pin&&pend)bkPrevShow(f,op);
    bkPlace(c,rect||bkRectOf(f));
    c.addEventListener('pointerenter',()=>{clearTimeout(BK.hideT)});
    c.addEventListener('pointerleave',()=>{if(!BK.pin)bkLater()})}
  window.bkWhy=function(){BK.whyOpen=!BK.whyOpen;const w=$('#bkwhyb');if(w)w.hidden=!BK.whyOpen;const dd=$('#skpass .skwhyd');if(dd)dd.open=BK.whyOpen;const c=$('#bkcard');if(c)bkPlace(c,bkRectOf(BK.byId[c.dataset.id]||{}))};
  /* בחירת נוסח (1/2/3): מוצג בשורה, ובלחיצה כפולה או במקש - מוחל ועובר להבא */
  window.bkAltPick=function(id,i,apply){
    const f=BK.byId[id];if(!f)return;BK.alt=BK.alt||{};
    if(i>=bkOpts(f).length)return;
    BK.alt[id]=i;
    if(apply){bkKbDecide(f,'ok');return}
    const c=$('#bkcard');if(c){c.remove();bkShowCard(f,true,bkRectOf(f))}};
  /* דחייה מיידית; הסיבה אינה חובה: אחרי המעבר מוצגת רצועה קטנה עם סיבות, ולחיצה מצרפת אותה להכרעה */
  window.bkRejectNow=function(id){const f=BK.byId[id];if(!f)return;BK.rs='';bkKbDecide(f,'no');bkWhyStrip(f)};
  function bkWhyStrip(f){
    const o=$('#bkrs');if(o)o.remove();
    const s=document.createElement('div');s.id='bkrs';s.className='bkrs';
    s.innerHTML='<span class="dim">נדחה. סיבה (לא חובה):</span>'+SKWHY.map(w=>'<button onmousedown="event.preventDefault()" onclick="bkWhySet(\''+f.id+'\',\''+w[0]+'\')">'+w[1]+'</button>').join('');
    document.body.appendChild(s);clearTimeout(BK.rsT);BK.rsT=setTimeout(()=>s.remove(),6000)}
  window.bkWhySet=function(id,code){
    const f=BK.byId[id],d=BK.DEC[id];if(!f||!d||d.d!=='no')return;
    const w=SKWHY.find(x=>x[0]===code);BK.rs=code;bkPut(f,'no',w?w[1]:'');bkSave();
    const s=$('#bkrs');if(s)s.remove();toast('הסיבה נרשמה.',1800)};
  function bkRectOf(f){const r=BK.R.find(x=>x.f.id===f.id);if(!r)return null;
    const rs=r.range.getClientRects();return rs.length?rs[0]:r.el.getBoundingClientRect()}
  /* בשוליים כשיש מקום (משמאל או מימין לטור הטקסט); אחרת מתחת לשורה, ואחרת מעליה. לעולם לא על השורה */
  /* בשוליים כשיש מקום (משמאל או מימין לשורת הטקסט, מחוץ ללוחות הצד: חברותא, גמרא, צורת הדף);
     אחרת מעוגן בתחתית המסך, והשורה נגללת מעליו. לעולם אינו מכסה את השורה ואת זו שלפניה (26.10.2026) */
  /* גבולות האזור הפנוי בין לוחות הצד (חברותא, גמרא, צורת הדף, תוס') */
  function bkSides(){
    const vw=innerWidth;let lo=0,hi=vw;
    for(const s of ['#hvx','#srcx','#tzx','#tpan']){const e=$(s);if(!e||!e.getClientRects().length)continue;
      const r=e.getBoundingClientRect();if(!r.width||r.width>vw*.8)continue;
      if(r.left<vw/2)lo=Math.max(lo,r.right);else hi=Math.min(hi,r.left)}
    return {lo,hi}}
  function bkPlace(c,rc){
    const W=c.offsetWidth||340,Hh=c.offsetHeight||170,vw=innerWidth,vh=innerHeight,fl=$('#flow');
    if(!rc){c.style.top='80px';c.style.left=Math.max(8,vw-W-16)+'px';return}
    const cur=BK.R.find(x=>x.f.id===BK.cardId),row=cur&&cur.el&&cur.el.closest('.row');
    const tr=(row||fl).getBoundingClientRect();
    const sd=bkSides(),lo=sd.lo,hi=sd.hi;
    let top,left;
    if(tr.left-lo>W+16){left=tr.left-W-8;top=Math.min(vh-Hh-8,Math.max(8,rc.top-10))}
    else if(hi-tr.right>W+16){left=tr.right+8;top=Math.min(vh-Hh-8,Math.max(8,rc.top-10))}
    else{/* אין שוליים: הכרטיס מעוגן בתחתית המסך מעל הסרגל, והשורה הבעייתית (ושלפניה) נגללות מעליו */
      const bar=$('#bkbar'),bh=bar?bar.offsetHeight+10:56;
      left=Math.max(lo+8,Math.round((lo+hi-W)/2));top=Math.max(8,vh-Hh-bh-6);
      c.style.left=left+'px';c.style.top=Math.round(top)+'px';
      const over=rc.bottom-(top-14),need=rc.top-(rc.height*1.6+8);
      if(over>0||need<70){const d=over>0?over:need-90;
        const sc=fl&&fl.scrollHeight>fl.clientHeight+4?fl:null;
        try{(sc||window).scrollBy({top:d,behavior:'auto'})}catch(e){(sc||window).scrollBy(0,d)}}
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
    /* (26.10.2026) בלי נעילה של 5 שניות, שבלעה Enter מהיר. מאזין המקלדת השני (skira_ui) אינו
       שומע את אותו Enter (stopImmediatePropagation), ואותו ממצא אינו מוכרע פעמיים במקביל.
       קבל אופטימי: ההחלה על הנתונים מיידית, הכרטיס הבא מוצג מיד, והציור, הספירה והשמירה ברקע. */
    if(BK.kbId===f.id)return;
    BK.kbId=f.id;
    try{
      const id=f.id,st=bkStatus(f);
      if(d==='edit-ok'){BK.editId='';await bkDecide(id,'edit',false,true)}
      else await bkDecide(id,d,0);   /* גם ממצא שנשאר מ"אושר לביצוע" ישן: Enter מחיל את המטען ("בוצע" רק בכפתור) */
      if(bkStatus(f)!=='pending'&&bkStatus(f)!==st)bkAdvance()}
    finally{BK.kbId=''}}
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
    const hit=()=>{e.preventDefault();e.stopImmediatePropagation()};
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
    /* (26.10.2026) הכרטיס מוצג באותה משימה: איתור רק אם הטקסט השתנה, והדגשה מלאה רק כשהמיקומים
       זזו; אחרת מתחלפת רק הדגשת הנוכחי. המקור בצד נפתח אחרי שהכרטיס כבר על המסך */
    const run=()=>{
      bkLocateAll();
      if(!have||SK.mode||BK.hlN!==BK.locN)bkHL();else bkHLCur();
      let r=BK.R.find(x=>x.f.id===id);
      if(!r&&!SK.mode){bkHL();r=BK.R.find(x=>x.f.id===id)}
      if(r){const fl=$('#flow');
        if(fl.classList.contains('vert'))r.el.scrollIntoView({block:'center'});else toEl(r.el);
        if(card)bkShowCard(f,true,bkRectOf(f))}
      if(SK.mode)skPassDraw();else bkBarDraw();
      if(window.skAfterGo)setTimeout(()=>{if(BK.curId===id)skAfterGo(f)},0)};
    if(have)run();else setTimeout(run,90)}
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
  /* סגנון תו על הנתונים (26.10.2026): בלי מצב עריכה, בלי בחירה בדף ובלי קפיצה אל השורה.
     כמו Ctrl+1 (setCs): סגנונות והדגשה שבתוך הקטע מוסרים, והקטע נעטף בסגנון החדש (או נשאר
     רגיל). קידומת (ו, ד, ל...) נשארת בתוך הסגנון, כמו ברוב הספר (313 מול 12 בבכורות). */
  function bkStyleHtml(h,start,len,cs){
    const d=document.createElement('div');d.innerHTML=h;
    const at=[],w=document.createTreeWalker(d,NodeFilter.SHOW_TEXT);let n;
    while(n=w.nextNode())for(let i=0;i<n.nodeValue.length;i++)at.push([n,i]);
    const a=at[start],b=at[start+len-1];if(!a||!b)return null;
    const r=document.createRange();r.setStart(a[0],a[1]);r.setEnd(b[0],b[1]+1);
    {const ca=r.commonAncestorContainer,hh=ca.nodeType===3?ca.parentElement:ca,wi=hh&&hh.closest&&hh.closest('i');
     if(wi&&wi!==d&&d.contains(wi)&&OKCLS.indexOf(wi.className)>-1&&r.toString()===wi.textContent)r.selectNode(wi)}
    const box=document.createElement('div');box.appendChild(r.extractContents());
    [...box.querySelectorAll('i,b')].forEach(x=>{if((x.tagName==='I'&&OKCLS.indexOf(x.className)>-1&&x.className!=='mk')||x.tagName==='B')x.replaceWith(...x.childNodes)});
    let node;
    if(cs){node=document.createElement('i');node.className=cs;while(box.firstChild)node.appendChild(box.firstChild)}
    else{node=document.createDocumentFragment();while(box.firstChild)node.appendChild(box.firstChild)}
    r.insertNode(node);
    d.querySelectorAll('i,b').forEach(x=>{if(!x.textContent)x.remove()});
    d.normalize();return d.innerHTML}
  function bkApplyStyle(f,op){
    return bkApplyCore(f,(curT,curH)=>{
      const h=bkFindIn(curT,f);if(!h||!h.len)return 'הטקסט בשורה השתנה מאז הבקרה.';
      let cs=h.pos,cl=h.len;
      const rc=op.range?bkCompact(op.range).c:'';
      if(rc){const within=h.sc.c.slice(h.pos,h.pos+h.len),i=within.indexOf(rc);
        if(i>-1){cs=h.pos+i;cl=rc.length}
        else{const j=h.sc.c.indexOf(rc);if(j>-1&&h.sc.c.indexOf(rc,j+1)<0){cs=j;cl=rc.length}else return 'הקטע "'+op.range+'" אינו בשורה כפי שנרשם.'}}
      const oStart=h.sc.m[cs],oEnd=h.sc.m[cs+cl-1]+1;
      const nowH=bkStyleHtml(curH,oStart,oEnd-oStart,op.cs||'');
      if(nowH===null)return 'לא נמצא הקטע לסימון.';
      if(nowH===curH)return 'הסגנון כבר במקומו.';
      return {nowT:curT,nowH}})}
  window.bkApplyStyle=bkApplyStyle;
  /* ---- מטענים חדשים (26.10.2026): כותרת צד, כותרת נושא, פיצול ואיחוי ----
     כולם על הנתונים ובאותן רשומות שהעורך עצמו כותב (side / unside / split / merge, ועריכת טקסט
     רגילה), ולכן נקלטים בוורד ובבנייה בדיוק כמו פעולה ידנית. ביטול (Ctrl+Z) מחזיר את המצב שלפני. */
  function bkUnitOf(f){
    const L=BK.loc[f.id];if(!L)return null;
    const m=/^u(\d+)\.(\d+|w|mb)$/.exec(L.k||'');if(!m)return null;
    const u=unitById(+m[1]);if(!u)return null;
    return {L,u,n:m[2],i:/^\d+$/.test(m[2])?(+m[2])-1:-1,pi:L.pi,daf:L.s.daf}}
  /* קטע של HTML לפי מקומות בטקסט (a עד b), עם סגנונות התו שבו */
  function bkSliceHtml(h,a,b){
    const d=document.createElement('div');d.innerHTML=h;
    const at=[],w=document.createTreeWalker(d,NodeFilter.SHOW_TEXT);let n;
    while(n=w.nextNode())for(let i=0;i<n.nodeValue.length;i++)at.push([n,i]);
    const r=document.createRange();r.selectNodeContents(d);
    if(a>0&&at[a])r.setStart(at[a][0],at[a][1]);else if(a>0&&a>=at.length){return ''}
    if(b<at.length&&at[b])r.setEnd(at[b][0],at[b][1]);
    const x=document.createElement('div');x.appendChild(r.cloneContents());
    x.querySelectorAll('i,b').forEach(e=>{if(!e.textContent)e.remove()});
    return x.innerHTML}
  /* רשומת מבנה על הנתונים: תמונת העמוד לפני, החלה, רישום, ציור מחדש של העמוד בלבד */
  function bkStructCommit(f,e,pi,apply){
    const snap=JSON.stringify(D.pages[pi].units),before=snapOf(pi);
    freezeEdits(e.texts||[]);
    apply();
    e._ap=1;ED.push(e);UNDO.push({e,pi,snap,t:Date.now()});
    SLOTS=null;saveED();patchPage(before);
    BK.undo={id:f.id,f,struct:{e,pi,snap}};
    return e}
  /* עריכת טקסט של מקום לפי מפתח (כותרת הצד, השורה הראשונה), כעריכת מנהל רגילה */
  function bkEditKey(k,nowH,daf){
    const old=ED.find(x=>x.k===k&&x.op!=='struct');
    const curH=dataHtml(k);if(curH===null)return null;
    const nowT=plain(nowH),wasT=old?old.was:plain(curH),wasH=old?(old.wasH!==undefined?old.wasH:curH):curH;
    const el=$('#flow').querySelector('[data-ek="'+k+'"]');
    const edit={k,was:wasT,now:nowT,wasH,nowH,wasP:old?old.wasP:'',daf,ctx:el?ctxOf(el):{b:'',a:''},t:Date.now(),pub:0};
    if(old&&old.ps!==undefined){edit.ps=old.ps;edit.psw=old.psw}
    const rec={k,prev:old||null,wasH:curH};
    if(old)ED=ED.filter(x=>x!==old);
    ED.push(edit);saveED();applyTextNow(edit);return rec}
  function bkApplyAnchor(f,op){
    const x=bkUnitOf(f);if(!x)return 'הממצא לא אותר בטקסט הנוכחי.';
    const u=x.u,wk=wkey(u),daf=x.daf;
    if(u.k!=='u'&&u.k!=='m')return 'כותרת צד אפשרית רק בפסקת גוף.';
    const head=u[wk]||'';
    if(op.unside){
      const lines=head.split('<br>'),winH=lines[lines.length-1],winT=plain(winH);
      if(!winT.trim())return 'אין כותרת צד להחזיר לשורה.';
      const nextT=u.l.length?plain(u.l[0][1]):'',cls=u.l.length?u.l[0][0]:'';
      const e={op:'struct',kind:'unside',texts:[winT,nextT],res:[[cls,winH]],resT:[winT],daf,t:Date.now(),pub:0};
      bkStructCommit(f,e,x.pi,()=>unsideApply(e,{u,pi:x.pi,daf}));return {k:'u'+u.id+'.1'}}
    if(op.take){
      const i=x.i<0?0:x.i;if(!u.l[i])return 'השורה לא נמצאה.';
      const cls=u.l[i][0],lineH=u.l[i][1],text=plain(lineH),tc=bkCC(text),kc=bkCompact(op.take).c;
      let p=tc.c.indexOf(kc);if(p<0||tc.c.indexOf(kc,p+1)>-1)return 'הדובר "'+op.take+'" אינו בשורה פעם אחת בדיוק.';
      let cs=tc.m[p],ce=tc.m[p+kc.length-1]+1;
      if(text[ce]===' ')ce++;else if(cs>0&&text[cs-1]===' ')cs--;
      const bodyT=text.slice(0,cs)+text.slice(ce),whole=!bodyT.trim();
      const bodyH=whole?'':bkReplaceAt(lineH,cs,ce-cs,'');
      const wH=esc(op.text||text.slice(tc.m[p],tc.m[p+kc.length-1]+1).trim());
      const e={op:'struct',kind:'side',texts:[text],res:[[cls,bodyH],[wH],[whole?0:cs,whole?text.length:ce-cs]],
               resT:[whole?'':bodyT,plain(wH)],daf,t:Date.now(),pub:0};
      bkStructCommit(f,e,x.pi,()=>sideApply(e,{u,i,pi:x.pi}));return {k:'side'}}
    if(!op.text)return 'אין נוסח לכותרת הצד.';
    if(!plain(head).trim()){
      /* אין כותרת: כותרת חדשה בראש השורה, והשורה כמות שהיא */
      const i=x.i<0?0:x.i;if(!u.l[i])return 'השורה לא נמצאה.';
      const cls=u.l[i][0],lineH=u.l[i][1],text=plain(lineH);
      const e={op:'struct',kind:'side',texts:[text],res:[[cls,lineH],[esc(op.text)],[0,0]],resT:[text,op.text],daf,t:Date.now(),pub:0};
      bkStructCommit(f,e,x.pi,()=>sideApply(e,{u,i,pi:x.pi}));return {k:'side'}}
    /* יש כותרת: היא מקבלת את הנוסח החדש, וההמשך (rest) עובר לראש השורה הראשונה */
    const hk='u'+u.id+(wk==='a'?'.0':'.w');
    const lines=head.split('<br>');let j=lines.length-1;
    if(f.mark){const mc=bkCompact(f.mark).c;const jj=lines.findIndex(l=>bkCompact(plain(l)).c.indexOf(mc)>-1||mc.indexOf(bkCompact(plain(l)).c)>-1);if(jj>-1)j=jj}
    lines[j]=esc(op.text);
    const recs=[];
    const r1=bkEditKey(hk,lines.join('<br>'),daf);if(!r1)return 'כותרת הצד לא נמצאה בנתונים.';recs.push(r1);
    if(op.rest&&u.l.length){
      const lk='u'+u.id+'.1',cur=dataHtml(lk)||'';
      const r2=bkEditKey(lk,esc(op.rest)+' '+cur.replace(/^\s+/,''),daf);if(r2)recs.push(r2)}
    BK.undo={id:f.id,f,multi:recs};return {k:hk}}
  function bkApplyHeading(f,op){
    const x=bkUnitOf(f);if(!x||x.i<0||!x.u.l[x.i])return 'כותרת נושא נכנסת לפני פסקת גוף בלבד.';
    const u=x.u,i=x.i,A=u.l[i],aT=plain(A[1]);
    const sp=(A[0]||'').split(' ').filter(c=>/^a\d$/.test(c));
    const nRow=[['nose','b1'].concat(sp.length?sp:['a0']).join(' '),esc(op.text)];
    const e={op:'struct',kind:'split',ins:1,where:'before',texts:[aT],res:[nRow,[A[0],A[1]]],resT:[op.text,aT],
             psw:wsty('nose'),daf:x.daf,t:Date.now(),pub:0,cl:{sug:op.text,fin:op.text,i:0,dec:0}};
    bkStructCommit(f,e,x.pi,()=>{u.l.splice(i,1,nRow,[A[0],A[1]]);delete u.lv});
    const el=$('#flow').querySelector('[data-ek="u'+u.id+'.'+(i+1)+'"]');if(el)el.classList.add('prop');
    return {k:'u'+u.id+'.'+(i+1)}}
  function bkApplySplit(f,op){
    const x=bkUnitOf(f);if(!x||x.i<0||!x.u.l[x.i])return 'פיצול אפשרי בפסקת גוף בלבד.';
    const u=x.u,i=x.i,cls=u.l[i][0],h=u.l[i][1],t=plain(h),tc=bkCC(t),ac=bkCompact(op.at).c;
    const p=tc.c.indexOf(ac);if(p<0||tc.c.indexOf(ac,p+1)>-1)return 'מקום הפיצול "'+op.at+'" אינו בשורה פעם אחת בדיוק.';
    let pos=tc.m[p+ac.length-1]+1;
    let a=pos;while(a>0&&/\s/.test(t[a-1]))a--;
    let b=pos;while(b<t.length&&/\s/.test(t[b]))b++;
    if(a<=0||b>=t.length)return 'הפיצול בקצה השורה: אין מה לפצל.';
    const ha=bkSliceHtml(h,0,a),hb=bkSliceHtml(h,b,t.length);
    const e={op:'struct',kind:'split',texts:[t],res:[[cls,ha],[cls,hb]],resT:[plain(ha),plain(hb)],daf:x.daf,t:Date.now(),pub:0};
    bkStructCommit(f,e,x.pi,()=>{u.l.splice(i,1,[cls,ha],[cls,hb]);delete u.lv});
    return {k:'u'+u.id+'.'+(i+1)}}
  function bkApplyJoin(f){
    const x=bkUnitOf(f);if(!x||x.i<0||!x.u.l[x.i])return 'איחוי אפשרי בפסקת גוף בלבד.';
    const u=x.u,i=x.i;if(!u.l[i+1])return 'השורה הבאה ביחידה אחרת: יש לאחות ידנית (Delete בסוף השורה).';
    const t1=plain(u.l[i][1]),t2=plain(u.l[i+1][1]),cls=u.l[i][0];
    const gap=/\s$/.test(t1)||/^\s/.test(t2)?'':' ';
    const h=u.l[i][1]+gap+u.l[i+1][1];
    const e={op:'struct',kind:'merge',texts:[t1,t2],res:[[cls,h]],resT:[plain(h)],daf:x.daf,t:Date.now(),pub:0};
    bkStructCommit(f,e,x.pi,()=>{u.l.splice(i,2,[cls,h]);delete u.lv});
    return {k:'u'+u.id+'.'+(i+1)}}
  /* החלה לפי סוג המטען. מחזיר מחרוזת הסבר כשאי אפשר; אחרת אובייקט (עריכה או {k}) */
  function bkApplyOp(f,op){
    if(op.t==='rep')return bkApplyRep(f,op);
    if(op.t==='ins')return bkApplyIns(f,op);
    if(op.t==='style')return bkApplyStyle(f,op);
    if(op.t==='anchor')return bkApplyAnchor(f,op);
    if(op.t==='heading')return bkApplyHeading(f,op);
    if(op.t==='split')return bkApplySplit(f,op);
    if(op.t==='join')return bkApplyJoin(f);
    return 'אין מה להחיל.'}
  /* הנוסח שנשמר בהכרעה (ללמידה): מה שהוחל בפועל */
  function bkSugText(op){
    if(op.t==='rep')return op.y;
    if(op.t==='ins')return '['+bkInsText(op.text)+']';
    if(op.t==='anchor')return op.unside?'(כותרת הצד חזרה לשורה)':(op.take?'כותרת צד: '+(op.text||op.take):'כותרת צד: '+op.text+(op.rest?' | לשורה: '+op.rest:''));
    if(op.t==='heading')return 'כותרת: '+op.text;
    if(op.t==='split')return 'פיצול אחרי: '+op.at;
    if(op.t==='join')return 'איחוי';
    if(op.t==='style')return BKACT[op.cs==='am'?'am':(op.cs==='ps'?'ps':'plain')]+': '+(op.range||'');
    return ''}

  /* ---- התצוגה בתוך השורה (26.10.2026): השורה מוצגת כבר במצב "אחרי" ----
     מה שנוסף: בירוק עדין, ברכיב שאינו ניתן לעריכה ואינו נקרא כטקסט (.bkx). מה שנמחק: קו חוצה אפור
     (CSS Highlight, בלי לגעת ב-DOM). לפני כל החלה התצוגה מוסרת, ולכן אינה נכנסת לנתונים לעולם. */
  function bkPrevClear(){
    const fl=$('#flow');if(fl)fl.querySelectorAll('.bkx').forEach(x=>{const p=x.parentNode;x.remove();if(p&&p.normalize)p.normalize()});
    if(window.CSS&&CSS.highlights){CSS.highlights.delete('bk-del');CSS.highlights.delete('bk-prev')}
    BK.prevId=''}
  function bkRepPos(text,f,rp){
    const h=bkFindIn(text,f);if(!h)return null;
    const xc=bkCompact(rp.x).c;if(!xc)return null;
    const within=h.sc.c.slice(h.pos,h.pos+h.len);let cs=within.indexOf(xc);
    if(cs<0){const c2=h.sc.c.indexOf(xc);if(c2>-1&&h.sc.c.indexOf(xc,c2+1)<0)cs=c2-h.pos;else return null}
    const c0=h.pos+cs;return {a:h.sc.m[c0],b:h.sc.m[c0+xc.length-1]+1}}
  function bkInsPos(text,f,op){
    if(op.end)return text.replace(/\s+$/,'').length;
    const h=bkFindIn(text,f),sc=h?h.sc:bkCC(text);
    const before=op.before!==undefined&&op.after===undefined;
    const a=bkCompact(op.after||op.before||f.mark||'').c;if(!a)return null;
    let p=h?sc.c.indexOf(a,Math.max(0,h.pos-a.length)):-1;if(p<0)p=sc.c.indexOf(a);if(p<0)return null;
    return before?sc.m[p]:sc.m[p+a.length-1]+1}
  function bkPrevShow(f,op){
    bkPrevClear();
    if(!f||!op||!BKEXEC[op.t])return;
    const L=BK.loc[f.id];if(!L)return;
    const el=$('#flow').querySelector('[data-ek="'+L.k+'"]');if(!el)return;
    const T=bkElText(el,null),at=T.at,text=T.text;
    const HL=!!(window.CSS&&CSS.highlights&&typeof Highlight!=='undefined');
    const rng=(a,b)=>{const A=at[a],B=at[b-1];if(!A||!B||b<=a)return null;const r=document.createRange();r.setStart(A[0],A[1]);r.setEnd(B[0],B[1]+1);return r};
    const mark=(name,r)=>{if(!HL||!r)return;const h=new Highlight(r);CSS.highlights.set(name,h)};
    const span=(cls,t)=>{const s=document.createElement('span');s.className='bkx '+cls;s.setAttribute('contenteditable','false');s.setAttribute('aria-hidden','true');s.textContent=t;return s};
    const put=(pos,node)=>{const r=document.createRange();
      if(pos>=text.length){const B=at[text.length-1];if(!B){el.appendChild(node);return}r.setStart(B[0],B[1]+1)}
      else{const A=at[pos];if(!A)return;r.setStart(A[0],A[1])}
      r.collapse(true);r.insertNode(node)};
    try{
      if(op.t==='rep'){const p=bkRepPos(text,f,op);if(!p)return;
        mark('bk-del',rng(p.a,p.b));if(op.y)put(p.b,span('bkx-ins',op.y))}
      else if(op.t==='ins'){const oi=bkInsPos(text,f,op);if(oi===null)return;
        const before=op.before!==undefined&&op.after===undefined&&!op.end;
        put(oi,span('bkx-ins bkx-hs',(before?'':' ')+'['+bkInsText(op.text)+']'+(before?' ':'')))}
      else if(op.t==='style'){const h=bkFindIn(text,f);if(!h)return;mark('bk-prev',rng(h.sc.m[h.pos],h.sc.m[h.pos+h.len-1]+1))}
      else if(op.t==='anchor'){
        const x=bkUnitOf(f);if(!x)return;
        const hk='u'+x.u.id+(wkey(x.u)==='a'?'.0':'.w'),hel=$('#flow').querySelector('[data-ek="'+hk+'"]');
        if(op.take){const tc=bkCC(text),kc=bkCompact(op.take).c,p=tc.c.indexOf(kc);if(p>-1)mark('bk-del',rng(tc.m[p],tc.m[p+kc.length-1]+1))}
        if(op.unside&&hel){const r=document.createRange();r.selectNodeContents(hel);mark('bk-del',r)}
        if(op.text&&hel&&plain(x.u[wkey(x.u)]||'').trim()){const r=document.createRange();r.selectNodeContents(hel);mark('bk-del',r);hel.appendChild(span('bkx-ins',' '+op.text))}
        else if(op.text||op.take)el.insertBefore(span('bkx-ins bkx-side',(op.text||op.take)+' '),el.firstChild);
        if(op.rest)el.insertBefore(span('bkx-ins',op.rest+' '),el.firstChild)}
      else if(op.t==='heading'){const d=document.createElement('div');d.className='bkx bkx-head';d.setAttribute('contenteditable','false');d.textContent=op.text;
        el.parentNode.insertBefore(d,el)}
      else if(op.t==='split'){const tc=bkCC(text),ac=bkCompact(op.at).c,p=tc.c.indexOf(ac);if(p<0)return;put(tc.m[p+ac.length-1]+1,span('bkx-br',' ¶ '))}
      else if(op.t==='join')el.appendChild(span('bkx-br',' ⤶'));
      BK.prevId=f.id}catch(e){bkPrevClear()}}
  /* אחרי החלה: רשימת העריכות, הפרסום והסנכרון - ברקע, אחרי שהכרטיס הבא כבר על המסך */
  function bkAfterEdit(){setTimeout(()=>{drawEd();pubSoon();syncSoon()},0)}
  async function bkDecide(id,d,done,nofocus){
    const f=BK.byId[id];if(!f)return;
    const wi=$('#bkwhy'),why=wi?wi.value.trim():'';
    let now='',msg='';
    if(d==='pending'){bkPut(f,'pending');bkSave();bkHideCard(true);bkRefreshAfter();toast('הממצא חזר לממתינים.');return}
    if(d==='ok'&&!done){
      /* הנוסח שנבחר (1/2/3) או המטען עצמו; התצוגה בשורה מוסרת לפני ההחלה */
      const op=bkCardOp(f),act=op.t==='style'?(op.cs==='am'?'am':(op.cs==='ps'?'ps':'plain')):op.t;
      bkPrevClear();
      const ar=BKEXEC[op.t]?bkApplyOp(f,op):null;
      if(ar!==null&&typeof ar!=='string'){
        now=bkSugText(op);bkAfterEdit();
        msg={rep:'התיקון הוחל כעריכת מנהל.',ins:'ההוספה הוחלה בסגנון הסבר.',am:'סגנון אמוראים הוחל.',ps:'סגנון פסוק הוחל.',plain:'הסגנון הוסר.',
             anchor:'כותרת הצד עודכנה.',heading:'כותרת הנושא נוספה.',split:'השורה פוצלה.',join:'השורות אוחו.'}[act]+' Ctrl+Z מבטל.'}
      else if(act==='am'||act==='plain'||act==='ps'){
        /* גיבוי: כשההחלה על הנתונים אינה אפשרית - בדף, במצב עריכה, כמו קודם */
        if(!EDIT)setEdit(true);if(!EDIT)return;
        const L=BK.loc[f.id];if(!L){toast('הממצא לא אותר בטקסט הנוכחי.');return}
        if(!(SK.mode&&BK.curId===id&&$('#flow').querySelector('[data-ek="'+L.k+'"]'))){bkGo(id,false);
          await new Promise(r=>setTimeout(r,160))}
        const el=$('#flow').querySelector('[data-ek="'+L.k+'"]');
        if(el){el.focus();if(!bkSel(f)){toast('לא נמצא הקטע לסימון. אפשר ללחוץ "ערוך".');return}
          setCs(act==='am'?'am':(act==='ps'?'ps':''));msg=act==='am'?'סגנון אמוראים הוחל.':(act==='ps'?'סגנון פסוק הוחל.':'הסגנון הוסר.')}
        else{toast('לא נמצאה השורה לעריכה.');return}}
      else if(BKEXEC[op.t]){toast((typeof ar==='string'?ar:'לא הוחל.')+' אפשר ללחוץ E לעריכה בשורה.',6000);return}
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
    /* הכרעה מהמקלדת: הכרטיס הבא מוצג מיד (bkAdvance), והריענון המלא בא אחריו */
    if(BK.kbId){bkSoon();return}
    if(!SK.mode){bkRefresh();return}
    bkCount();skPassDraw();bkSoon()}
  /* עריכה ממוקדת: מצב עריכה דלוק, הסמן בסוף הקטע המסומן */
  function bkFocusEdit(f){
    bkPrevClear();
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
  function bkUndoOne(r){
    const cur=ED.find(x=>x.k===r.k&&!x.fz);
    if(cur){edKeys();tomb(cur.k);ED=ED.filter(x=>x!==cur)}
    if(r.prev)ED.push(r.prev);
    dataSet(r.k,r.wasH);SLOTS=null;saveED();
    const el=$('#flow').querySelector('[data-ek="'+r.k+'"]');if(el)setHTML(el,r.wasH)}
  function bkUndoRec(u){
    bkPrevClear();
    if(u.k){bkUndoOne(u);drawEd();pubSoon();syncSoon()}
    /* כמה עריכות (כותרת צד והמשכה בשורה): מבוטלות בסדר הפוך */
    if(u.multi){u.multi.slice().reverse().forEach(bkUndoOne);drawEd();pubSoon();syncSoon()}
    /* רשומת מבנה (כותרת צד, כותרת נושא, פיצול, איחוי): העמוד חוזר לתמונה שלפני, והרשומה נמחקת */
    if(u.struct){const x=u.struct,before=snapOf(x.pi);
      D.pages[x.pi].units=JSON.parse(x.snap);
      const i=ED.indexOf(x.e);if(i>-1){edKeys();tomb(x.e.k);ED.splice(i,1)}
      const j=UNDO.findIndex(y=>y.e===x.e);if(j>-1)UNDO.splice(j,1);
      SLOTS=null;saveED();patchPage(before);drawEd();pubSoon();syncSoon()}
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
