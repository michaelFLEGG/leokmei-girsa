  /* =================== סכם פרק: התור והסקירה קטע-קטע (פרומפט 15, 28.10.2026) ===================
     אין כאן שום קריאה למודל. "סכם פרק" (ליד בורר הפרק ובתפריט המנהל) בונה חבילה - יחידות הפרק
     כפי שהן בנתונים, ולשון הגמרא של דפיו (sk/<מסכת>/<דף>.json) - ושולח אותה לתור. פירוש הגמרא וחברותא אינם בחבילה: היא יורדת לריפו הציבורי
     שבנקודת הקליטה. משם היא יורדת לריפו, המשימה המתוזמנת בענן כותבת הצעות (docs/sakem-runner.md),
     והן חוזרות לכאן. גם "סכם" על קטע מסומן נכנס לאותו תור.

     הסקירה נפתחת בתוך הדף: הקטע הנוכחי מודגש, הנוסח החדש במקום הישן, ושלושה סימונים -
     ליטוש (מילים שנוספו ברקע עדין, מה שנמחק בקו חוצה אפור), קיצור מרחבי (סמליל, ובריחוף "דולג: ..."),
     והשלמה מהגמרא (צבע נפרד, ובריחוף לשון הגמרא; לחיצה מבטלת רק אותה). חסר גדול הוא פריט משלו.
     Enter קבל · Delete דחה · E ערוך (Enter מסיים ומקבל) · חצים הבא/קודם · Ctrl+ז ביטול ההכרעה האחרונה.
     הקבלה עוברת ב-skmApply - אותן רשומות שהעורך כותב, ומשם לפרסום ולוורד כמו כל עריכה. */
  const SKP={jobs:[],all:[],rev:null,tm:null};
  const SKP_H0=location.hash;   /* הקישור הישיר (#skp=...) נקרא לפני שהדף כותב את מספר הפרק בכתובת */
  const SKP_ST={wait:'ממתין לסכם',sent:'ממתין לסכם',work:'בעבודה',ready:'מוכן לסקירה',done:'נסקר'};
  const skpA=t=>esc(String(t||'')).replace(/"/g,'&quot;');
  function skpOK(){return isAdmin()&&!!admKey()&&!SUGM}
  function skpDafN(d){const V={'א':1,'ב':2,'ג':3,'ד':4,'ה':5,'ו':6,'ז':7,'ח':8,'ט':9,'י':10,'כ':20,'ל':30,'מ':40,'נ':50,'ס':60,'ע':70,'פ':80,'צ':90,'ק':100,'ר':200,'ש':300,'ת':400};
    d=String(d||'').trim();let n=0;for(const c of d.replace(/[^א-ת]/g,''))n+=V[c]||0;return n?n*2+(/:$/.test(d)?1:0):0}
  function skpTitle(si){const S=SEC[si]||{};return D.masechet+' '+(S.perek||'')+(S.perekName?' - '+S.perekName:'')}
  function skpJob(si){return SKP.jobs.find(j=>j.kind==='perek'&&j.perek===si+1&&j.st!=='done')}
  function skpStText(j){if(!j)return '';if(j.st==='work')return 'בעבודה ('+j.n+' מתוך '+(j.total||'?')+')';
    if(j.st==='ready'&&j.dec)return 'מוכן לסקירה ('+j.dec+' מתוך '+j.shown+' הוכרעו)';return SKP_ST[j.st]||''}

  /* ---- החבילה ---- */
  async function skpPacket(kind,os){
    const dafs=[...new Set(os.map(o=>D.pages[o.pi].daf).filter(Boolean))];
    const pages=await Promise.all(dafs.map(async d=>{
      try{const r=await fetch('sk/'+SLUG+'/'+skpDafN(d)+'.json',{cache:'no-cache'});const j=await r.json();
        return {daf:d,refs:j.refs||[],g:j.g||[]}}catch(e){return {daf:d,refs:[],g:[],miss:1}}}));
    if(pages.some(p=>p.miss))throw new Error('לשון הגמרא לא נמצאה לחלק מן הדפים');
    const fu=flatU(),i0=fu.findIndex(o=>o.u.id===os[0].u.id),i1=fu.findIndex(o=>o.u.id===os[os.length-1].u.id);
    return {v:1,slug:SLUG,masechet:D.masechet,kind,units:os.map(skmPU),pages,
      before:kind==='seg'?skmInter(fu.slice(Math.max(0,i0-3),i0)):'',after:kind==='seg'?skmInter(fu.slice(i1+1,i1+4)):''}}
  window.skpEnqueue=async function(kind,ids,si){
    if(!skpOK()){flash('סכם - למנהל בלבד');return}
    let os,title;
    if(kind==='perek'){si=si===undefined?cur:si;const S=SEC[si];
      os=flatU().filter(o=>o.pi>=S.from&&o.pi<=S.to);title=skpTitle(si);
      const j=skpJob(si);if(j){toast('כבר בתור: '+title+' · '+skpStText(j));return}}
    else{os=skmUnits(ids);si=secOf(os[0].pi);title=D.masechet+' דף '+(D.pages[os[0].pi].daf||'')+' (קטע)'}
    if(!os.length){flash('אין מה לסכם');return}
    toast('מכין את '+title+' לתור…');
    const packet=await skpPacket(kind,os);
    const j=await api('/sakem/job',{method:'POST',body:JSON.stringify({slug:SLUG,kind,perek:si+1,title,packet})});
    toast(j.again?'כבר בתור: '+title:'נכנס לתור סכם: '+title+'. ההצעות יוכנו במשימה המתוזמנת',5000);
    skpLoad()};

  /* ---- מצב התור: בראש הפרק, ליד בורר הפרק, ותג "מוכן לסקירה" בסרגל ---- */
  async function skpLoad(){
    if(!skpOK())return;
    try{const j=await api('/sakem/jobs');SKP.all=j.items||[];SKP.jobs=SKP.all.filter(x=>x.slug===SLUG)}catch(e){return}
    skpDraw();
    clearTimeout(SKP.tm);
    if(SKP.jobs.some(x=>/wait|sent|work/.test(x.st)))SKP.tm=setTimeout(skpLoad,60000)}
  function skpDraw(){
    if(!skpOK())return;
    const si=cur,j=skpJob(si);
    /* ליד בורר הפרק */
    let b=$('#skpbtn');const ps=$('#peresel');
    if(!b&&ps){b=document.createElement('button');b.id='skpbtn';b.type='button';b.className='skpbtn';
      b.onclick=()=>{const jj=skpJob(cur);if(jj&&jj.st==='ready')skpOpen(jj.jid);else skpEnqueue('perek')};ps.after(b)}
    if(b){b.textContent=j?(j.st==='ready'?'סקור סכם':'סכם · '+skpStText(j)):'סכם פרק';
      b.title=j?skpTitle(si)+': '+skpStText(j):'הכנסת כל הפרק לתור סכם: ליטוש, קיצור בראייה מרחבית ובדיקת חסרים מהגמרא';
      b.classList.toggle('on',!!j);b.classList.toggle('ready',!!(j&&j.st==='ready'))}
    /* בתפריט המנהל */
    const lb=$('#lnbtn');
    if(lb&&!$('#skpmenu')){const m=document.createElement('button');m.id='skpmenu';m.textContent='סכם פרק';m.title='הכנסת הפרק הנוכחי לתור סכם';
      m.onclick=()=>skpEnqueue('perek');lb.before(m);
      const q=document.createElement('button');q.id='skpqueue';q.textContent='סכם: התור';q.onclick=()=>skpPanel();lb.before(q)}
    /* בראש הפרק */
    document.querySelectorAll('.skphead').forEach(x=>x.remove());
    const S=SEC[si];const fr=S&&D.pages[S.from]&&D.pages[S.from].units[0];
    const row=fr&&document.getElementById('u'+fr.id);
    if(j&&row){const d=document.createElement('div');d.className='skphead'+(j.st==='ready'?' ready':'');
      d.textContent='סכם: '+skpStText(j);if(j.st==='ready'){d.title='לחץ לסקירה';d.onclick=()=>skpOpen(j.jid)}
      row.before(d)}
    /* התג בסרגל: כל פרק שמוכן לסקירה, גם במסכת אחרת */
    let t=$('#skptag');const rd=SKP.all.filter(x=>x.st==='ready');
    if(!rd.length){if(t)t.remove();return}
    /* פרומפט 27: תג קטן בתוך הסרגל עצמו (פריט בשורה, לא צף מעליו), ולכן לעולם אינו מכסה כפתור.
       השם המלא בריחוף; כמה פרקים מוכנים - הלחיצה פותחת רשימה קצרה */
    const bar=$('#bar');
    if(!t){t=document.createElement('button');t.id='skptag';t.type='button';(bar||document.body).appendChild(t)}
    if(!bar)t.classList.add('float');
    const f=rd.find(x=>x.slug===SLUG)||rd[0];
    const go=x=>{if(x.slug===SLUG)skpOpen(x.jid);else location.href=x.slug+'.html#p='+Math.max(0,x.perek-1)+'&skp='+x.jid};
    t.textContent='סכם'+(rd.length>1?' ('+rd.length+')':'');
    t.title='מוכן לסקירה: '+rd.map(x=>x.title||x.jid).join(' · ');
    t.onclick=ev=>{ev.stopPropagation();const old=$('#skptagm');if(old){old.remove();return}
      if(rd.length===1){go(f);return}
      const m=document.createElement('div');m.id='skptagm';m.dir='rtl';
      rd.forEach(x=>{const b=document.createElement('button');b.type='button';b.textContent=x.title||x.jid;b.onclick=()=>{m.remove();go(x)};m.appendChild(b)});
      document.body.appendChild(m);const r=t.getBoundingClientRect();
      m.style.top=Math.round(r.bottom+4)+'px';m.style.left=Math.max(8,Math.min(innerWidth-m.offsetWidth-8,Math.round(r.left+r.width/2-m.offsetWidth/2)))+'px';
      setTimeout(()=>addEventListener('click',function c(e){if(!m.contains(e.target)){m.remove();removeEventListener('click',c)}}),0)}}
  const skpR0=render;
  render=function(){const r=skpR0.apply(this,arguments);try{skpDraw()}catch(e){}return r};
  function skpPanel(){
    const old=$('#skmpanel');if(old)old.remove();
    const m=document.createElement('div');m.className='modal';m.id='skmpanel';
    const row=x=>'<tr><td>'+esc(x.title||x.jid)+'</td><td>'+esc(skpStText(x)||SKP_ST[x.st]||x.st)+'</td><td>'+
      (x.st==='ready'?'<button data-o="'+x.jid+'">סקור</button> ':'')+(x.st!=='done'?'<button data-c="'+x.jid+'">הוצא מהתור</button>':'')+'</td></tr>';
    m.innerHTML='<div class="box skmbox"><h3>סכם: התור</h3>'+
      '<p class="skmsmall">ההצעות מוכנות במשימה המתוזמנת של קלוד בענן, על המנוי - בלי תשלום נוסף. פרק שנכנס לתור מופיע כאן כ"ממתין", אחר כך "בעבודה", ואז "מוכן לסקירה".</p>'+
      (SKP.all.length?'<table class="skptab">'+SKP.all.slice().reverse().map(row).join('')+'</table>':'<p>התור ריק.</p>')+
      '<hr><div id="skpnow" class="skmsmall">סכם על קטע מסומן: בודק…</div>'+
      '<div class="btns"><button onclick="skpEnqueue(\'perek\');document.getElementById(\'skmpanel\').remove()">סכם את הפרק הנוכחי</button> <button onclick="document.getElementById(\'skmpanel\').remove()">סגירה</button></div></div>';
    document.body.appendChild(m);m.addEventListener('click',async e=>{if(e.target===m){m.remove();return}
      const b=e.target.closest('button');if(!b)return;
      if(b.dataset.o){const x=SKP.all.find(y=>y.jid===b.dataset.o);m.remove();if(x.slug===SLUG)skpOpen(x.jid);else location.href=x.slug+'.html#p='+(x.perek-1)+'&skp='+x.jid}
      if(b.dataset.c&&confirm('להוציא מן התור?')){await api('/sakem/cancel',{method:'POST',body:JSON.stringify({jid:b.dataset.c})});m.remove();await skpLoad();skpPanel()}
      if(b.id==='skpkeyb'){const v=$('#skpkey').value.trim();if(!v)return;
        try{await api('/sakem/key',{method:'POST',body:JSON.stringify({key:v})});toast('המפתח נשמר בשרת');m.remove();skpPanel()}catch(er){flash('לא נשמר: '+er.message)}}});
    /* 29.10: סכם על קטע עובד מיד דרך ה-API כשיש קרדיט; בלי מפתח או קרדיט - נכנס לתור הזה */
    api('/sakem/stat').then(st=>{const d=$('#skpnow');if(!d)return;
      const usd=x=>'$'+(+x||0).toFixed(2);
      d.innerHTML=st.hasKey&&!st.capped?'<b>סכם על קטע מסומן:</b> מיד, דרך המפתח · החודש '+usd(st.month)+' ('+(st.n||0)+' הצעות). כשהקרדיט נגמר - הקטע נכנס לתור לבד.':
        '<b>סכם על קטע מסומן:</b> '+(st.capped?'הגעת לתקרת החודש':'אין מפתח')+' - קטע נכנס לתור הזה. '+
        '<label>מפתח: <input id="skpkey" type="password" autocomplete="off" spellcheck="false" placeholder="sk-ant-..." style="width:40%"></label> <button id="skpkeyb">שמור</button>'}).catch(()=>{const d=$('#skpnow');if(d)d.textContent=''})}
  window.skpPanel=skpPanel;

  /* =================== הסקירה =================== */
  async function skpOpen(jid){
    if(!skpOK())return;
    let j;try{j=await api('/sakem/out?jid='+encodeURIComponent(jid))}catch(e){flash(e.message);return}
    const job=j.job||SKP.jobs.find(x=>x.jid===jid)||{};
    if(job.kind==='perek'&&job.perek&&cur!==job.perek-1)render(job.perek-1);
    if(!EDIT)setEdit(true);
    const items=(j.out.items||[]).filter(x=>!x.nochange);
    const R=SKP.rev={jid,job,out:j.out,items,dec:j.dec||{},i:0,hist:[],cnt:{accept:0,reject:0,edit:0}};
    try{skpRelocate(R)}catch(e){}
    Object.values(R.dec).forEach(d=>{if(R.cnt[d.act]!==undefined)R.cnt[d.act]++});
    R.i=skpNextOpen(-1,1);
    if(R.i<0){flash('כל הקטעים בפרק הזה כבר הוכרעו');SKP.rev=null;return}
    document.body.classList.add('skprev');
    skpShow()}
  /* 1.11.2026: מזהה יחידה הוא מספר הפסקה בוורד, וכל עריכה בוורד שלפני הפרק מזיזה אותו. הצעה שנכתבה
     לפני העריכה הצביעה על יחידות אחרות, ולכן הופיעה במקום הלא נכון וסורבה ("האלמנטים הנעולים אינם
     במקומם"). כאן כל הצעה מאותרת מחדש לפי תוכנה: אותיות הנוסח שההצעה נכתבה עליו מול אותיות היחידות שבדף.
     קטע שלא נמצא כלשונו (נערך באמת) מוזז באותו היסט של הקטע שלפניו, ומוצג כעריכה שלך. */
  const skpNorm=t=>String(t||'').split('\n').filter(s=>!/^\[(דף|משנה|גמרא|קבוע|מקור)(:[^\]]*)?\]$/.test(s.trim()))
    .join(' ').replace(/\[(מס|תוס'):[^\]]*\]/g,' ').replace(/[^א-ת]/g,'');
  function skpRelocate(R){
    const fu=flatU(),pos=new Map(fu.map((o,i)=>[o.u.id,i]));
    const sig=fu.map(o=>{try{return skpNorm(skmInter([o]))}catch(e){return '\u0000'}});
    let delta=0;
    const shift=ids=>{const ix=ids.map(id=>pos.get(id+delta));return ix.every((x,k)=>x!==undefined&&(!k||x===ix[k-1]+1))?ids.map(id=>id+delta):null};
    R.items.forEach(it=>{
      if(!it.ids||!it.ids.length)return;
      if(it.kind!=='seg'){if(delta){const s=shift(it.ids);if(s){it.ids=s;if(it.anchor&&pos.has(it.anchor+delta))it.anchor+=delta}}return}
      if(skmSame(it.ids,it.orig))return;
      const T=skpNorm(it.orig),n=it.ids.length;
      let best=-1,bd=Infinity;
      if(T)for(let i=0;i+n<=fu.length;i++){
        if(!T.startsWith(sig[i]))continue;
        let s='';for(let k=0;k<n&&s.length<=T.length;k++)s+=sig[i+k];
        if(s!==T)continue;
        const d=Math.abs(fu[i].u.id-(it.ids[0]+delta));if(d<bd){bd=d;best=i}}
      if(best>=0){const nids=fu.slice(best,best+n).map(o=>o.u.id);delta=nids[0]-it.ids[0];it.ids=nids;it.orig=skmInter(skmUnits(nids));return}
      if(delta){const s=shift(it.ids);if(s)it.ids=s}})}
  /* הצעה שהנעולים שבה ([דף], [מקור], [משנה] וכו') אינם כבנוסח שבדף - הנעולים נלקחים מן הדף:
     מה שחסר נשתל במקומו, מה שאינו בדף יוצא, ושורות ההצעה נשארות כמות שהן. */
  const SKP_LK=/^\[(דף|משנה|גמרא|קבוע|מקור|כותרת-נושא|כותרת-דה)(?::(.*))?\]$/;
  function skpFixLocks(orig,text){
    const key=s=>{const m=SKP_LK.exec(String(s).trim());return m?(/^כותרת/.test(m[1])?m[1]:m[1]+':'+(m[2]||'').trim()):null};
    const kind=k=>k.split(':')[0];
    /* כל שורה מקבלת את מספר הפסקה שהיא לפניה; כותרות צד נצמדות לשורה שאחריהן */
    const scan=L=>{const lk=[],body=[];let c=0,grp=[];
      L.forEach((s,i)=>{const k=key(s);if(k){lk.push({k,s,c});return}
        if(!String(s).trim())return;grp.push(s);if(!/^\[צד:.*\]$/.test(String(s).trim())){body.push(grp);grp=[];c++}});
      if(grp.length)body.push(grp);return {lk,body,n:c}};
    const O=scan(String(orig||'').split('\n')),T=scan(String(text||'').split('\n'));
    if(O.lk.map(x=>x.k).join('|')===T.lk.map(x=>x.k).join('|'))return text;
    const a=O.lk,b=T.lk,n=a.length,m=b.length,L=[...Array(n+1)].map(()=>new Array(m+1).fill(0));
    for(let i=n-1;i>=0;i--)for(let j=m-1;j>=0;j--)L[i][j]=a[i].k===b[j].k?L[i+1][j+1]+1:Math.max(L[i+1][j],L[i][j+1]);
    let P=[];for(let i=0,j=0;i<n&&j<m;){if(a[i].k===b[j].k){P.push([i,j]);i++;j++}else if(L[i+1][j]>=L[i][j+1])i++;else j++}
    /* בין הזוגות: נעול מאותו סוג שערכו השתנה (מקור אחר, דף אחר) - מוחלף במקומו */
    const Q=[];let pi=-1,pj=-1;
    P.concat([[n,m]]).forEach(([i,j])=>{let jj=pj+1;for(let ii=pi+1;ii<i;ii++)for(let t=jj;t<j;t++)if(kind(a[ii].k)===kind(b[t].k)){Q.push([ii,t]);jj=t+1;break}
      if(i<n)Q.push([i,j]);pi=i;pj=j});
    Q.sort((x,y)=>x[0]-y[0]);
    const at=new Array(n);Q.forEach(([i,j])=>{at[i]=b[j].c});
    /* נעול שאין לו זוג - במקום היחסי שלו בין שני הזוגות הסמוכים */
    for(let i=0;i<n;i++)if(at[i]===undefined){
      let p=i-1;while(p>=0&&at[p]===undefined)p--;let q=i+1;while(q<n&&at[q]===undefined)q++;
      const oa=p>=0?a[p].c:0,ob=q<n?a[q].c:O.n,ta=p>=0?at[p]:0,tb=q<n?at[q]:T.n;
      at[i]=Math.min(tb,Math.max(ta,ta+Math.round((a[i].c-oa)*(tb-ta)/Math.max(1,ob-oa))))}
    for(let i=1;i<n;i++)if(at[i]<at[i-1])at[i]=at[i-1];
    const line=i=>{const pr=Q.find(x=>x[0]===i);return pr&&/^כותרת/.test(a[i].k)?b[pr[1]].s:a[i].s};
    const out=[];let i=0;
    T.body.forEach((g,k)=>{while(i<n&&at[i]<=k)out.push(line(i++));out.push(...g)});
    while(i<n)out.push(line(i++));
    return out.join('\n')}
  window.skpFixLocks=skpFixLocks;
  function skpNextOpen(from,dir){const R=SKP.rev;for(let i=from+dir;i>=0&&i<R.items.length;i+=dir)if(!R.dec[R.items[i].iid])return i;return -1}
  function skpClose(){skmClose(true);document.querySelectorAll('.skpold').forEach(r=>r.classList.remove('skpold','skpshow'));
    const b=$('#skpbar');if(b)b.remove();SKP.rev=null;document.body.classList.remove('skprev');setTimeout(skpLoad,1500)}
  function skpRows(ids){return ids.map(id=>document.getElementById('u'+id)).filter(Boolean)}

  /* השוואת מילים: מה נוסף ומה נמחק, על הטקסט שבתצוגה עצמה (כדי שהמילים יתאימו לצמתים) */
  function skpWords(root){const out=[];const w=document.createTreeWalker(root,NodeFilter.SHOW_TEXT,{acceptNode:n=>n.parentElement.closest('.skmlock,.skmsrc,.skpdel,.tzc')?2:1});
    let n;while((n=w.nextNode()))n.nodeValue.split(/\s+/).forEach(x=>{if(x)out.push(x)});return out}
  const skpWn=w=>nonik(w).replace(/[.,:;!?"'״׳()[\]{}\-]/g,'');
  /* זוגות המילים המשותפות (LCS) בלי מגבלת גודל (פרומפט 20, 5.11.2026): קידומת וסיומת
     משותפות נחתכות, קטע קטן נפתר בטבלה, וקטע גדול מתפצל לפי הירשברג (זיכרון ליניארי).
     קודם לכן קטע ארוך (n*m>400000) דילג בשקט, ולכן בסכם פרק לא נראה קו חוצה. */
  function skpLcs(A,B){
    const pairs=[];
    function row(a0,a1,b0,b1,rev){const m=b1-b0;let pr=new Int32Array(m+1),cu=new Int32Array(m+1);
      for(let i=0;i<a1-a0;i++){const ai=rev?A[a1-1-i]:A[a0+i];cu[0]=0;
        for(let j=1;j<=m;j++){const bj=rev?B[b1-j]:B[b0+j-1];cu[j]=ai===bj?pr[j-1]+1:(pr[j]>cu[j-1]?pr[j]:cu[j-1])}
        const t=pr;pr=cu;cu=t}
      return pr}
    function small(a0,a1,b0,b1){const n=a1-a0,m=b1-b0;const L=[...Array(n+1)].map(()=>new Int32Array(m+1));
      for(let i=n-1;i>=0;i--)for(let j=m-1;j>=0;j--)L[i][j]=A[a0+i]===B[b0+j]?L[i+1][j+1]+1:Math.max(L[i+1][j],L[i][j+1]);
      let i=0,j=0;while(i<n&&j<m){if(A[a0+i]===B[b0+j]){pairs.push([a0+i,b0+j]);i++;j++}else if(L[i+1][j]>=L[i][j+1])i++;else j++}}
    function go(a0,a1,b0,b1){
      while(a0<a1&&b0<b1&&A[a0]===B[b0]){pairs.push([a0,b0]);a0++;b0++}
      const tail=[];while(a1>a0&&b1>b0&&A[a1-1]===B[b1-1]){a1--;b1--;tail.push([a1,b1])}
      if(a1>a0&&b1>b0){
        if((a1-a0)*(b1-b0)<=250000||a1-a0<2)small(a0,a1,b0,b1);
        else{const mid=(a0+a1)>>1,L1=row(a0,mid,b0,b1,false),L2=row(mid,a1,b0,b1,true),m=b1-b0;
          let k=0,best=-1;for(let j=0;j<=m;j++){const v=L1[j]+L2[m-j];if(v>best){best=v;k=j}}
          go(a0,mid,b0,b0+k);go(mid,a1,b0+k,b1)}}
      for(let t=tail.length-1;t>=0;t--)pairs.push(tail[t])}
    go(0,A.length,0,B.length);return pairs}
  function skpDiff(root,origHtml){
    const tmp=document.createElement('div');tmp.innerHTML=origHtml;
    const A=skpWords(tmp).map(skpWn),Bw=skpWords(root),B=Bw.map(skpWn),n=A.length,m=B.length;
    const add=new Array(m).fill(true),del=[...Array(m+1)].map(()=>[]);const Araw=skpWords(tmp);
    const P=skpLcs(A,B);let ai=0;
    P.forEach(([i,j])=>{while(ai<i){del[j].push(Araw[ai]);ai++}add[j]=false;ai=i+1});
    while(ai<n){del[m].push(Araw[ai]);ai++}
    /* הסימון בצמתים: מילה שנוספה - רקע עדין; מה שנמחק - קו חוצה אפור, לפני המילה שבאה במקומו */
    let k=0;const nodes=[];const w=document.createTreeWalker(root,NodeFilter.SHOW_TEXT,{acceptNode:x=>x.parentElement.closest('.skmlock,.skmsrc,.tzc')?2:1});
    let t;while((t=w.nextNode()))nodes.push(t);
    nodes.forEach(tn=>{const parts=tn.nodeValue.split(/(\s+)/);const fr=document.createDocumentFragment();
      parts.forEach(p=>{if(!p)return;if(/^\s+$/.test(p)){fr.appendChild(document.createTextNode(p));return}
        if(del[k]&&del[k].length){fr.appendChild(skpDel(del[k]));fr.appendChild(document.createTextNode(' '))}
        if(add[k]){const s=document.createElement('span');s.className='skpadd';s.textContent=p;fr.appendChild(s)}else fr.appendChild(document.createTextNode(p));k++});
      tn.replaceWith(fr)});
    if(del[m]&&del[m].length&&nodes.length){const last=root.querySelectorAll('.skmmain p');(last[last.length-1]||root).appendChild(skpDel(del[m]))}}
  /* מחיקה ארוכה (שלב שלם שדולג) מוצגת מקופלת, והנוסח המלא בריחוף ובלחיצה */
  function skpDel(ws){const d=document.createElement('del');d.className='skpdel';
    if(ws.length>8){d.classList.add('long');d.textContent='⋯ נמחקו '+ws.length+' מילים';d.title=ws.join(' ');d.onclick=()=>{d.textContent=ws.join(' ');d.classList.remove('long')}}
    else d.textContent=ws.join(' ');
    return d}

  function skpShow(){
    const R=SKP.rev;if(!R)return;
    skmClose(true);document.querySelectorAll('.skpold').forEach(r=>r.classList.remove('skpold','skpshow'));
    const it=R.items[R.i];if(!it){skpFinish();return}
    let p,conflict=false;
    if(it.kind==='missing'){
      const at=skpAnchor(it);if(!at){flash('מקום החסר לא נמצא בדף - דילוג');return skpMove(1)}
      p={id:R.jid+':'+it.iid,ids:[at.u.id],orig:skmInter([at]),text:'',point:'',changes:[],warn:[],notes:[],round:1};
      const g=document.createElement('div');g.className='skmghost skpmiss';g.dir='rtl';
      g.innerHTML='<div class="skpchips"><span class="skpchip gem" title="'+skpA(it.gem||'')+'">חסר מהגמרא</span>'+(it.why?'<span class="skpwhy">'+esc(it.why)+'</span>':'')+'</div>'+
        (it.gem?'<div class="skpgemq">'+esc(it.gem)+'</div>':'')+'<div class="skmbody">'+skmGhostBody(it.text,'')+'</div>';
      (document.getElementById('u'+at.u.id)).after(g);SKM.ghost=g;SKM.cur=p}
    else{
      const rows=skpRows(it.ids);
      if(!rows.length){skpDec(it,'stale');return skpMove(1)}
      conflict=!skmSame(it.ids,it.orig);
      p={id:R.jid+':'+it.iid,ids:it.ids,orig:it.orig,text:it.text,point:it.point||'',changes:it.changes||[],warn:[],notes:[],round:1};
      skmShow(p);
      const g=SKM.ghost;if(!g)return;
      g.classList.add('skp');
      const bar=g.querySelector('.skmbar');if(bar)bar.remove();
      rows.forEach(r=>{r.classList.remove('skmold');if(!conflict)r.classList.add('skpold')});
      /* שלושת הסימונים */
      const body=g.querySelector('.skmbody');
      let dErr=null;try{skpDiff(body,skmGhostBody(it.orig,''))}catch(e){dErr=e;try{console.warn('skpDiff',e)}catch(_){}}
      body.querySelectorAll('ins.skmadd').forEach((x,k)=>{const a=(it.adds||[])[k]||{};x.classList.add('skpgem');x.dataset.k=k;
        x.title='השלמה מהגמרא'+(a.gem?': '+a.gem:'')+' · לחיצה מבטלת רק אותה';
        x.addEventListener('click',ev=>{if(g.classList.contains('edit'))return;ev.preventDefault();x.classList.toggle('off')})});
      /* כותרת חדשה (פרומפט 20): שורת (נושא) שאינה במקור - בחום, ולחיצה מבטלת רק אותה */
      const hOld=new Set(SKC.parse(it.orig).filter(k=>(k.t==='line'&&k.sty==='nose')||(k.t==='lock'&&/^כותרת/.test(k.kind))).map(k=>nonik(SKC.plainI(k.v||k.val||'')).replace(/\s+/g,' ').trim()));
      let nNew=0;
      body.querySelectorAll('.skmmain p.nose').forEach(x=>{const t=nonik(x.textContent).replace(/\s+/g,' ').trim();if(!t||hOld.has(t))return;
        nNew++;x.classList.add('skpnewh');x.dataset.h=t;x.title='כותרת חדשה · לחיצה מבטלת רק אותה';
        x.addEventListener('click',ev=>{if(g.classList.contains('edit'))return;ev.preventDefault();x.classList.toggle('off')})});
      const chips=document.createElement('div');chips.className='skpchips';chips.contentEditable='false';
      chips.innerHTML=(it.layers||[]).map(L=>L==='קיצור מרחבי'?'<span class="skpchip sp" tabindex="0" title="דולג: '+esc(it.skipped||'')+'">קיצור מרחבי</span>':
        L==='השלמה'?'<span class="skpchip gem" title="השלמה מהגמרא: לחיצה על ההשלמה בנוסח מבטלת רק אותה">השלמה מהגמרא</span>':'<span class="skpchip">ליטוש</span>').join('')+
        (nNew?'<span class="skpchip newh" title="לחיצה על הכותרת החומה בנוסח מבטלת רק אותה">כותרת חדשה'+(nNew>1?' ('+nNew+')':'')+'</span>':'')+
        (it.skipped?'<span class="skpskip" hidden>דולג: '+esc(it.skipped)+'</span>':'')+
        (conflict?'<span class="skpconf">הקטע נערך אצלך מאז שההצעה נכתבה. העריכה שלך מוצגת למעלה.</span>':'')+
        (dErr?'<span class="skpconf" title="'+skpA(SKC.plainI(String(it.orig||'').split('\n').filter(x=>!/^\[(דף|משנה|גמרא|קבוע|מקור)/.test(x)).join(' ')))+'">לא ניתן להציג את המחיקות בקטע זה - הנוסח המקורי בריחוף, ו-⟲ מציג אותו</span>':'');
      g.prepend(chips);
      const sp=chips.querySelector('.skpchip.sp');if(sp)sp.onclick=()=>{const s=chips.querySelector('.skpskip');s.hidden=!s.hidden}}
    const g=SKM.ghost;
    g.dataset.iid=it.iid;
    /* סמלילים בצד הקטע; הכיתוב רק בריחוף */
    const side=document.createElement('div');side.className='skpside';side.contentEditable='false';
    side.innerHTML=(conflict?'<button data-a="keep" title="השאר את העריכה שלי (Delete)">✋</button><button data-a="force" title="החלף בהצעה (Enter)">⇄</button>':
      '<button data-a="ok" title="קבל ועבור לבא (Enter)">✓</button><button data-a="no" title="דחה - השאר את המקור (Delete)">✗</button>')+
      (it.kind==='seg'?'<button data-a="edit" title="ערוך במקום (E), Enter מסיים ומקבל">✎</button><button data-a="src" title="הצג מקור">⟲</button>':'')+
      '<button data-a="prev" title="הקודם (חץ למעלה)">↑</button><button data-a="next" title="הבא (חץ למטה)">↓</button>';
    g.appendChild(side);
    side.addEventListener('click',ev=>{const b=ev.target.closest('button');if(b)skpAct(b.dataset.a)});
    R.conflict=conflict;R.p=p;
    skpBar();skpTzFollow();
    const top=(it.kind==='seg'?skpRows(it.ids)[0]:null)||g;
    (conflict||it.kind==='missing'?top:g).scrollIntoView({block:'center',behavior:'smooth'});
    /* המסך המפוצל (פירוש, חברותא, צורת הדף) נגלל יחד עם הקטע, אם הוא פתוח */
    try{const o=skmUnits(it.ids).find(x=>x.u.ref);if(o&&$('#srcx')&&$('#srcx').offsetParent)openSrc(o.u.ref)}catch(e){}
    try{g.focus({preventScroll:true})}catch(e){}}
  function skpAnchor(it){
    for(const id of [it.anchor].concat(it.ids.slice().reverse())){const o=skmUnits([id])[0];if(o&&(o.u.k==='u'||o.u.k==='m')&&o.u.l&&o.u.l.length)return o}
    return null}
  /* פרומפט 29 (9.11.2026): כרטיס הציון של הפרק, ולידו הדגם - בבא בתרא פרק ה כפי שאושר - באותם מדדים לכל קטע */
  function skpScore(S){
    if(!S)return '';
    const M=(S.model&&S.model.perSeg)||{},P=S.perSeg||{},f=n=>(Math.round((+n||0)*100)/100).toString(),
      pc=n=>'<bdi dir="ltr">'+(n>0?'+':'')+(+n||0)+'%</bdi>';
    const row=(t,k)=>'<tr><td>'+t+'</td><td>'+f(P[k])+'</td><td>'+(S.model?f(M[k]):'-')+'</td></tr>';
    return '<details class="skpscore"><summary>כרטיס ציון: '+(S.block?'<b class="skpbad">'+S.block+' חוסמות</b>':'0 חוסמות')+
      ' · '+S.warnLeft+' אזהרות · הדגשות '+S.bold+' · רווחים '+S.space+' · מקפי תירוץ '+S.dash+' · כותרות צד חדשות '+S.side+
      ' · כותרות נושא חדשות '+S.nose+' · עיטורים שנמחקו '+S.hatz+' · אורך '+pc(S.lenPct)+(S.model?' (בדגם '+pc(S.model.lenPct)+')':'')+'</summary>'+
      '<table><tr><th>לכל קטע</th><th>הפרק הזה</th><th>בבא בתרא ה (הדגם)</th></tr>'+
      row('הדגשות במשנה','bold')+row('רווחים','space')+row('מקפי תירוץ','dash')+row('כותרות צד','side')+row('כותרות נושא','nose')+row('שורות אלמנות','widow')+
      '</table></details>'}
  function skpBar(){
    const R=SKP.rev;let b=$('#skpbar');
    if(!b){b=document.createElement('div');b.id='skpbar';b.dir='rtl';document.body.appendChild(b);
      b.addEventListener('click',ev=>{const x=ev.target.closest('button');if(x)skpAct(x.dataset.a)})}
    const it=R.items[R.i],sp=R.items.filter(x=>(x.layers||[]).includes('קיצור מרחבי')).length,
      ad=R.items.reduce((n,x)=>n+(x.adds||[]).length,0)+R.items.filter(x=>x.kind==='missing').length;
    b.innerHTML='<span class="skpttl">'+esc(R.job.title||R.out.title||'סכם')+'</span>'+
      '<span>קטע '+(R.i+1)+' מתוך '+R.items.length+'</span>'+
      '<span class="skpc">התקבלו '+R.cnt.accept+' · נדחו '+R.cnt.reject+' · נערכו '+R.cnt.edit+'</span>'+
      '<span class="skpc">קיצורים מרחביים: '+sp+' · השלמות מהגמרא: '+ad+'</span>'+
      /* פרומפט 28: שורת הציות (הדגשות, רווחים, מקפי תירוץ...) ומה סכם למד מאז הפרק הקודם */
      (R.out.summary||R.out.learnedNew!=null?'<span class="skpsum">'+esc(R.out.summary||'')+
        (R.out.learnedNew!=null?(R.out.summary?' · ':'')+'<a href="/admin-sakem-learn.html" target="_blank">למדתי מאז הפרק הקודם: '+(+R.out.learnedNew||0)+' כללים חדשים</a>':'')+'</span>':'')+
      skpScore(R.out.score)+
      '<button data-a="unfold" title="פרוש את כל המחיקות המקופלות בקטע (Alt+ח)">פרוש מחיקות</button>'+
      '<button data-a="allsug" title="קבל את כל הקטעים שטרם הוכרעו בסוגיה הזאת">קבל את כל הנותרים בסוגיה</button>'+
      '<button data-a="allper" title="קבל את כל הקטעים שטרם הוכרעו בפרק">קבל את כל הנותרים בפרק</button>'+
      (window.tzOpen?'<button data-a="tz" title="צורת הדף של הקטע הנסקר (Alt+צ); נעה עם הקטע">צורת הדף</button>':'')+
      '<button data-a="pause" title="עצירה - אפשר לחזור ולהמשיך מן הקטע הבא שלא הוכרע (Esc)">עצור</button>'+
      '<i style="width:'+Math.round(100*Object.keys(R.dec).length/Math.max(1,R.items.length))+'%"></i>'+
      '<div class="skpmob"><button data-a="'+(R.conflict?'force':'ok')+'">קבל</button><button data-a="'+(R.conflict?'keep':'no')+'">דחה</button>'+(it&&it.kind==='seg'?'<button data-a="edit">ערוך</button>':'')+'</div>'}

  /* ---- ההכרעות ---- */
  function skpDec(it,act,extra){
    const R=SKP.rev;if(!R)return;
    if(act==='undo')delete R.dec[it.iid];else R.dec[it.iid]={act};
    api('/sakem/dec',{method:'POST',body:JSON.stringify(Object.assign({slug:SLUG,jid:R.jid,iid:it.iid,act,layers:it.kind==='missing'?['השלמה']:(it.layers||[]),
      orig:it.orig||'',prop:it.text||'',gem:it.gem||(it.adds||[]).map(a=>a.gem).join(' | ')},extra||{}))}).catch(e=>flash('ההכרעה לא נרשמה בשרת: '+e.message))}
  /* הסרת ההשלמה ה-k ({+:...}) מן הנוסח */
  function skpDropAdd(text,k){let n=-1,out='',i=0;
    while(i<text.length){if(text.substr(i,3)==='{+:'){n++;if(n===k){let d=1,j=i+3;while(j<text.length&&d){if(text[j]==='{')d++;else if(text[j]==='}')d--;j++}
        i=j;continue}}out+=text[i];i++}
    return out.replace(/ {2,}/g,' ')}
  function skpApplyOne(it,text,orig){
    let p,t=text;
    if(it.kind==='missing'){const at=skpAnchor(it);if(!at)throw new Error('המקום לא נמצא');const o=skmInter([at]);p={id:SKP.rev.jid+':'+it.iid,ids:[at.u.id],orig:o};t=o+'\n'+it.text}
    else p={id:SKP.rev.jid+':'+it.iid,ids:it.ids,orig:orig||it.orig};
    /* פרומפט 27: עיטור ליד כותרת שההצעה מוחקת - יוצא מן המקור ומן ההצעה, ונמחק בהחלה */
    const hd=SKC.hatzDel(p.orig,t);
    /* 10.11.2026: עיטור שההצעה מוחקת אך הוא יושב מחוץ לגבולות הקטע (צמוד מלמעלה או מלמטה) - לא חוסמים
       את הקבלה. אם העיטור קיים בדף - נמחק גם הוא (skmApply מאתר אותו בדף כולו); ואם אינו קיים עוד - מדלגים
       עליו ומחילים את שאר ההצעה */
    let hdSkip=[];
    if(hd.bad.length){hdSkip=hd.bad.filter(id=>!skmUnits([id]).some(o=>o.u.k==='hatz'))}
    const hdIds=hd.ids.filter(id=>hdSkip.indexOf(id)<0);
    if(hd.ids.length){t=hd.text;if(hdIds.length)p.hdel=hdIds}
    const o2=hd.ids.length?hd.orig:p.orig;
    const rp=skmRepair(o2,t);t=rp.text;
    const errs=SKC.guard(o2,t,{edited:true}).filter(x=>/נעולים|קטע שלם|נוספו שורות|תג לא מוכר/.test(x));
    if(errs.length)throw new Error(errs[0]+'. העריכה נשארה פתוחה - אפשר לתקן ולנסות שוב');
    const r=skmApply(p,t);
    skmRemember(p.id,t,r.recs||[]);
    r.moved=rp.moved;
    return r}
  function skpAccept(force){
    const R=SKP.rev,it=R.items[R.i],g=SKM.ghost;if(!it||!g)return;
    const edited=g.classList.contains('edit');
    let text=it.kind==='missing'?it.text:edited?skmReadBack(g):it.text;
    if(it.kind==='seg'&&!edited){const off=[...g.querySelectorAll('ins.skpgem.off')].map(x=>+x.dataset.k).sort((a,b)=>b-a);off.forEach(k=>{text=skpDropAdd(text,k)});
      const hOff=new Set([...g.querySelectorAll('p.skpnewh.off')].map(x=>x.dataset.h));
      if(hOff.size)text=text.split('\n').filter(l=>!(/^\(נושא\)\s*/.test(l)&&hOff.has(nonik(SKC.plainI(l.replace(/^\(נושא\)\s*/,''))).replace(/\s+/g,' ').trim()))).join('\n')}
    else if(edited)g.querySelectorAll('ins.skpgem.off').forEach(x=>x.remove());
    let orig;if(R.conflict){if(!force)return;orig=skmInter(skmUnits(it.ids))}
    let r;try{r=skpApplyOne(it,text,orig)}catch(e){flash('לא הוחל: '+(e.message||e));return}
    skmClose(true);
    const act=edited||text!==it.text?'edit':'accept';
    R.cnt[act]++;R.hist.push({i:R.i,iid:it.iid,act,undo:r.n>0});
    skpDec(it,act,{final:act==='edit'?text:''});
    if(r.moved&&r.moved.length)toast('הוחזר למקום משוער - כדאי להציץ: '+r.moved.join(', '),6000);
    skpMove(1)}
  function skpReject(){const R=SKP.rev,it=R.items[R.i];if(!it)return;
    const act=R.conflict?'keep':'reject';R.cnt.reject++;R.hist.push({i:R.i,iid:it.iid,act:'reject'});skpDec(it,act);skpMove(1)}
  function skpUndo(){
    const R=SKP.rev,h=R.hist.pop();if(!h){flash('אין הכרעה לבטל');return}
    skmClose(true);
    if(h.undo&&!undoLast())flash('השינוי לא בוטל בדף - בטל בעורך');
    R.cnt[h.act==='keep'?'reject':h.act]--;
    const it=R.items.find(x=>x.iid===h.iid);skpDec(it,'undo');
    R.i=h.i;skpShow()}
  function skpMove(dir){
    const R=SKP.rev;if(!R)return;
    let n=skpNextOpen(R.i,dir);
    if(n<0&&dir>0)n=skpNextOpen(-1,1);
    if(n<0){skpFinish();return}
    R.i=n;skpShow()}
  function skpFinish(){const R=SKP.rev;skpClose();toast('הפרק נסקר עד סופו: התקבלו '+R.cnt.accept+', נערכו '+R.cnt.edit+', נדחו '+R.cnt.reject+'. העריכות יפורסמו עם שאר העריכות',6000)}
  function skpAll(scope){
    const R=SKP.rev,it0=R.items[R.i];
    const rest=R.items.map((x,i)=>[x,i]).filter(([x])=>!R.dec[x.iid]&&(scope==='per'||x.sugya===it0.sugya));
    if(!rest.length)return;
    if(!confirm('לקבל '+rest.length+' קטעים שטרם הוכרעו '+(scope==='per'?'בפרק':'בסוגיה')+'?'))return;
    skmClose(true);let ok=0,skip=0;
    rest.forEach(([x,i])=>{
      if(x.kind==='seg'&&!skmSame(x.ids,x.orig)){skip++;return}
      try{const r=skpApplyOne(x,x.text);R.cnt.accept++;R.hist.push({i,iid:x.iid,act:'accept',undo:r.n>0});skpDec(x,'accept');ok++}catch(e){skip++}});
    toast('התקבלו '+ok+(skip?' · '+skip+' נשארו להכרעה (נערכו בינתיים או לא הוחלו)':''),5000);
    skpMove(1)}
  function skpEditOn(){const g=SKM.ghost;if(!g||SKP.rev.items[SKP.rev.i].kind!=='seg')return;
    /* המילים שהמנוע מחק נשארות גלויות גם בעריכה (4.11.2026), פרושות במלואן ונעולות לעריכה:
       הן מידע בלבד, ואינן נקראות בחזרה לנוסח (skmReadBack מסיר אותן) */
    g.querySelectorAll('del.skpdel').forEach(x=>{if(x.classList.contains('long')){x.textContent=x.title;x.classList.remove('long')}
      x.contentEditable='false';x.classList.add('skpdelro');x.title='נמחק בהצעה - לעיון בלבד';x.onclick=null});
    g.querySelectorAll('span.skpadd').forEach(x=>x.replaceWith(...x.childNodes));
    g.querySelectorAll('ins.skpgem.off,p.skpnewh.off').forEach(x=>x.remove());
    g.classList.add('edit');const b=g.querySelector('.skmbody');b.setAttribute('contenteditable','');b.setAttribute('spellcheck','false');skmGuardEdit(g);
    const p=b.querySelector('p');if(p){p.focus();const r=document.createRange();r.selectNodeContents(p);r.collapse(false);const s=getSelection();s.removeAllRanges();s.addRange(r)}
    toast('עריכה במקום: כל קיצורי העורך פועלים. המילים שנמחקו בהצעה מוצגות באפור לעיון בלבד. Enter מסיים ומקבל, Esc מבטל את העריכה')}
  function skpUnfold(){const g=SKM.ghost;if(!g)return;
    g.querySelectorAll('del.skpdel.long').forEach(x=>{x.textContent=x.title;x.classList.remove('long')})}
  function skpAct(a){
    if(!SKP.rev)return;
    ({ok:()=>skpAccept(),force:()=>skpAccept(true),no:skpReject,keep:skpReject,edit:skpEditOn,next:()=>skpMove(1),prev:()=>skpMove(-1),
      src:()=>{const it=SKP.rev.items[SKP.rev.i];skpRows(it.ids).forEach(r=>r.classList.toggle('skpshow'))},
      unfold:skpUnfold,allsug:()=>skpAll('sug'),allper:()=>skpAll('per'),pause:skpClose,tz:skpTz})[a]()}
  /* צורת הדף בתוך הסקירה (4.11.2026): נפתחת על הקטע הנסקר, ונעה איתו בכל מעבר */
  function skpRef(it){
    if(!it)return '';
    const ids=it.kind==='missing'?[it.anchor].concat(it.ids||[]):(it.ids||[]);
    for(const r of skpRows(ids))if(r.dataset&&r.dataset.ref)return r.dataset.ref;
    const fu=flatU(),n=fu.findIndex(o=>ids.indexOf(o.u.id)>-1);
    for(let i=n;i>=0;i--)if(fu[i].u.ref)return fu[i].u.ref;
    return ''}
  function skpTz(){
    if(!window.tzOpen){flash('אין צורת דף למסכת הזאת');return}
    if(window.tzIsOpen&&tzIsOpen()){tzClose();return}
    const r=skpRef(SKP.rev.items[SKP.rev.i]);if(!r){flash('לא נמצא מקום בגמרא לקטע הזה');return}
    tzOpen(r)}
  function skpTzFollow(){
    if(!window.tzIsOpen||!tzIsOpen()||!SKP.rev)return;
    const r=skpRef(SKP.rev.items[SKP.rev.i]);if(r)try{tzOpen(r)}catch(e){}}
  /* המקלדת: לפני העורך (שלב הלכידה), רק כשהסקירה פתוחה */
  document.addEventListener('keydown',e=>{
    const R=SKP.rev;if(!R||!SKM.ghost)return;
    const ed=SKM.ghost.classList.contains('edit'),inG=SKM.ghost.contains(e.target);
    const typing=!inG&&e.target.closest&&e.target.closest('input,textarea,select,[contenteditable="true"],[contenteditable=""]');
    if(typing)return;
    const k=e.key,stop=()=>{e.preventDefault();e.stopPropagation()};
    if(ed){if(k==='Enter'&&!e.shiftKey&&!e.altKey){stop();skpAccept(R.conflict)}else if(k==='Escape'){stop();skpShow()}return}
    if(e.altKey&&!e.ctrlKey&&(k==='ח'||e.code==='KeyJ')){stop();skpUnfold();return}
    if(e.ctrlKey&&!e.altKey&&(e.code==='KeyZ')){stop();skpUndo();return}
    if(e.ctrlKey||e.altKey||e.metaKey)return;
    if(k==='Enter'){stop();skpAccept(R.conflict)}
    else if(k==='Delete'){stop();skpReject()}
    else if(e.code==='KeyE'){stop();skpEditOn()}
    else if(k==='ArrowDown'){stop();skpMove(1)}
    else if(k==='ArrowUp'){stop();skpMove(-1)}
    else if(k==='Escape'){stop();skpClose()}},true);

  /* ---- מראה ---- */
  (function(){const s=document.createElement('style');s.textContent=
    '.skpbtn{margin-inline-start:6px;padding:2px 10px;border-radius:12px;border:1px solid #2e5b8a;background:#fff;color:#2e5b8a;font:600 13px inherit;cursor:pointer;display:inline-block}.skpbtn.on{background:#eef3f9}.skpbtn.ready{background:#2e7d3c;border-color:#2e7d3c;color:#fff}'+
    '.skphead{margin:4px auto 6px;max-width:30em;text-align:center;font-size:12.5px;color:#4f6274;background:rgba(70,120,190,.07);border-radius:10px;padding:2px 10px}'+
    '.skphead.ready{color:#1f5a2c;background:rgba(46,125,60,.10);cursor:pointer}'+
    '#skptag{position:static;flex:0 0 auto;align-self:center;white-space:nowrap;margin:0 4px;padding:2px 10px;border-radius:12px;border:1px solid #2e7d3c;background:#2e7d3c;color:#fff;font:600 12.5px inherit;cursor:pointer;line-height:1.5}'+'#skptag.float{position:fixed;top:6px;left:8px;z-index:70}'+'@media (max-width:700px){#skptag{margin:0 2px;padding:1px 7px;font-size:11.5px}}'+'#skptagm{position:fixed;z-index:80;display:flex;flex-direction:column;gap:2px;padding:4px;background:#fff;border:1px solid #2e7d3c;border-radius:8px;box-shadow:0 4px 14px rgba(0,0,0,.18);max-width:calc(100vw - 16px)}'+'#skptagm button{border:none;background:none;text-align:right;padding:5px 10px;font:inherit;cursor:pointer;border-radius:5px}#skptagm button:hover{background:#eef6ef}'+
    '#flow .row.skpold{display:none}#flow .row.skpold.skpshow{display:flex;opacity:.75}#flow .row.skpold.skpshow .main{text-decoration:line-through;text-decoration-color:rgba(120,120,120,.6)}'+
    '.skmghost.skp,.skmghost.skpmiss{position:relative;border-color:rgba(46,91,138,.45);background:rgba(46,91,138,.04);box-shadow:0 0 0 3px rgba(46,91,138,.10);padding-left:34px}'+
    '.skmghost .skmmain p{color:inherit}.skmghost.skp .skmrail{color:inherit}'+
    '.skmghost .skpadd{background:rgba(250,214,80,.28);border-radius:2px}'+
    '.skmghost del.skpdel{color:#9a9a9a;text-decoration:line-through;text-decoration-thickness:1px;font-size:.9em}'+
    '.skmghost del.skpdel.long{text-decoration:none;font-size:11.5px;background:#f1f1f1;border-radius:8px;padding:0 6px;cursor:pointer;white-space:nowrap}'+
    '.skmghost ins.skpgem{text-decoration:none;background:rgba(32,150,160,.14);border-bottom:2px solid #1f8f99;cursor:pointer}'+
    '.skmghost ins.skpgem::after{content:"⊕";font-size:10px;color:#1f8f99;vertical-align:super;margin-right:1px}'+
    '.skmghost p.skpnewh{color:#8a5a1e;background:rgba(160,110,40,.10);border-radius:3px;cursor:pointer}.skmghost p.skpnewh::after{content:" ✦ כותרת חדשה";font-size:10px;color:#8a5a1e}'+
    '.skmghost p.skpnewh.off{text-decoration:line-through;color:#9a9a9a;background:none}.skmghost.edit p.skpnewh{cursor:text}'+
    '.skpchip.newh{background:rgba(160,110,40,.14);color:#7a4f17}'+
    '.skmghost ins.skpgem.off{background:none;border-bottom-style:dotted;color:#9a9a9a;text-decoration:line-through}'+
    '.skpchips{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:0 0 4px;font-size:12px}'+
    '.skpchip{padding:0 8px;border-radius:9px;background:#eef1f4;color:#4d5a66;cursor:default}.skpchip.sp{background:#f3e9ff;color:#5b3d8a;cursor:pointer}.skpchip.sp::before{content:"⤧ "}'+
    '.skpchip.gem{background:rgba(32,150,160,.14);color:#17707a}.skpchip.gem::before{content:"⊕ "}'+
    '.skpskip{color:#5b3d8a}.skpconf{color:#a8452f;font-weight:600}.skpwhy{color:#5d6b60}'+
    '.skpgemq{font-size:12.5px;color:#17707a;border-right:3px solid #1f8f99;padding:0 8px;margin:0 0 4px}'+
    '.skmghost.skpmiss .skmmain p{background:rgba(32,150,160,.08)}'+
    '.skpside{position:absolute;left:4px;top:6px;display:flex;flex-direction:column;gap:3px}'+
    '.skpside button{width:24px;height:24px;padding:0;border-radius:50%;border:1px solid #c9d3dc;background:#fff;color:#2e5b8a;font-size:13px;line-height:22px;cursor:pointer}'+
    '.skpside button[data-a="ok"],.skpside button[data-a="force"]{border-color:#2e7d3c;color:#2e7d3c}.skpside button[data-a="no"],.skpside button[data-a="keep"]{color:#a8452f}'+
    '#skpbar{position:fixed;bottom:0;left:0;right:0;z-index:65;display:flex;flex-wrap:wrap;gap:10px;align-items:center;padding:4px 12px 6px;background:rgba(255,255,255,.97);border-top:1px solid #d6dde4;font-size:12.5px;color:#3d4a55}'+
    '#skpbar>i{position:absolute;top:0;right:0;height:2px;background:#2e7d3c}#skpbar .skpttl{font-weight:700;color:#2e5b8a}#skpbar .skpc{color:#5d6b77}#skpbar .skpsum{flex-basis:100%;order:-1;color:#1f5a2c;font-size:12px}#skpbar .skpsum a{color:inherit}'+
    '#skpbar .skpscore{flex-basis:100%;order:-1;font-size:12px;color:#1f3f5a}#skpbar .skpscore summary{cursor:pointer}#skpbar .skpscore .skpbad{color:#a3261a}'+
    '#skpbar .skpscore table{border-collapse:collapse;margin:4px 0}#skpbar .skpscore td,#skpbar .skpscore th{border:1px solid #c9d3dc;padding:1px 8px;text-align:center}'+
    '#skpbar button{padding:1px 9px;border-radius:10px;border:1px solid #c9d3dc;background:#fff;color:#2e5b8a;font-size:12px;cursor:pointer}'+
    '.skmghost.edit del.skpdel.skpdelro{opacity:.55;user-select:none;cursor:default;font-size:.92em}'+'#skpbar .skpmob{display:none}body.skprev{padding-bottom:40px}'+
    '.skptab{width:100%;border-collapse:collapse;font-size:13px}.skptab td{border-bottom:1px solid #eee;padding:4px}'+
    '@media (max-width:820px),(pointer:coarse){#skpbar .skpmob{display:flex;flex-basis:100%;gap:8px}#skpbar .skpmob button{flex:1;font-size:16px;padding:10px 0;border-radius:10px}'+
      '#skpbar .skpmob button:first-child{background:#2e7d3c;color:#fff;border-color:#2e7d3c}body.skprev{padding-bottom:110px}.skpside{display:none}.skmghost.skp,.skmghost.skpmiss{padding-left:8px}}'+
    '@media print{#skpbar,#skptag,#skptagm,.skphead,.skpbtn{display:none!important}}';
    document.head.appendChild(s)})();
  if(skpOK())setTimeout(()=>{skpLoad().then(()=>{const m=/skp=([a-z0-9-]+)/.exec(SKP_H0);if(m)skpOpen(m[1])})},2500);
