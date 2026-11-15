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
    skpBgCheck();
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
    /* פרומפט 36: ליד בורר הפרק - אילו פרקים במסכת הזו מוכנים לסקירה, בקישורים */
    let rl=$('#skpready');
    const rdy=SKP.jobs.filter(x=>x.st==='ready'),byP=new Map();
    rdy.forEach(x=>{const k=+x.perek||0;if(!byP.has(k))byP.set(k,x)});
    if(!byP.size){if(rl)rl.remove()}
    else if(b){
      /* פרומפט 40: הרשימה אינה יושבת עוד בסרגל (דחקה את "עריכה" אל מחוץ למסך). היא בתפריט "כלים" של המנהל, וגם בריחוף על "סקור סכם" */
      const host=$('#admbtn~.admp')||null;
      if(!rl){rl=document.createElement('span');rl.id='skpready'}
      if(host){if(rl.parentNode!==host)host.insertBefore(rl,host.firstChild)}else if(rl.parentNode!==b.parentNode)b.after(rl);
      const nm=k=>k?(window.HD?HD.letters(k):String(k)):'קטע';
      b.title+=' · בפרקי המסכת הזו מוכנים לסקירה: '+[...byP.keys()].sort((a,c)=>a-c).map(nm).join(', ');
      rl.innerHTML='בפרקי המסכת הזו מוכנים לסקירה: '+[...byP.keys()].sort((a,c)=>a-c).map(k=>'<a href="#" data-j="'+skpA(byP.get(k).jid)+'" title="'+skpA(byP.get(k).title||'')+'">'+nm(k)+'</a>').join(', ');
      rl.onclick=ev=>{const a=ev.target.closest('a');if(!a)return;ev.preventDefault();skpOpen(a.dataset.j)}}
    /* בתפריט המנהל */
    const lb=$('#lnbtn');
    if(lb&&!$('#skpmenu')){const m=document.createElement('button');m.id='skpmenu';m.textContent='סכם פרק';m.title='הכנסת הפרק הנוכחי לתור סכם';
      m.onclick=()=>skpEnqueue('perek');lb.before(m);
      const q=document.createElement('button');q.id='skpqueue';q.textContent='סכם: התור';q.onclick=()=>skpPanel();lb.before(q);
      /* פרומפט 36: הלוח המרוכז */
      const w=document.createElement('button');w.id='skpwhat';w.textContent='מה מוכן לי';w.title='כל הפרקים לפי מסכת: מה מוכן לסקירה, מה בעבודה ומה ממתין';
      w.onclick=()=>{location.href='/admin-sakem.html'};lb.before(w)}
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
    /* פרומפט 36: "מה מוכן לי (N)". פרק אחד - ישר לסקירה; יותר - הלוח המרוכז */
    t.textContent='מה מוכן לי ('+rd.length+')';
    t.title='מוכן לסקירה: '+rd.map(x=>x.title||x.jid).join(' · ');
    t.onclick=ev=>{ev.stopPropagation();const old=$('#skptagm');if(old){old.remove();return}
      if(rd.length===1){go(f);return}
      if(rd.length>1){location.href='/admin-sakem.html';return}
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
    const R=SKP.rev={jid,job,out:j.out,items,dec:j.dec||{},i:0,hist:[],cnt:{accept:0,reject:0,edit:0},bad:new Set(),stale:0};
    try{skpRelocate(R)}catch(e){}
    /* פרומפט 36 (15.11.2026): "השאר את שלי" (keep) הוא דחייה, ונספר כך גם בטעינה (קודם "נדחו 0" אף שהיו) */
    Object.values(R.dec).forEach(d=>{const a=d.act==='keep'?'reject':d.act;if(R.cnt[a]!==undefined)R.cnt[a]++});
    /* פרומפט 36: בדיקת התיישנות בכל פתיחה. קטע שאינו מאותר בדף באופן אמין (המזהים אינם רצף קיים גם אחרי
       האיתור לפי תוכן ולפי דמיון) אינו מוצג שבור: הוא מסומן "מתיישן", וסכם מוזמן מחדש על הנוסח החי
       לאזור שלו בלבד. ההכרעות שכבר נעשו אינן נוגעות. */
    try{R.stale=await skpRedo(R)}catch(e){try{console.warn('skpRedo',e)}catch(_){}}
    R.i=skpNextOpen(-1,1);
    if(R.i<0){flash(R.stale?'כל הקטעים שנותרו התיישנו ונשלחו לסבב על הנוסח החי ('+R.stale+')':'כל הקטעים בפרק הזה כבר הוכרעו');SKP.rev=null;skpLoad();return}
    document.body.classList.add('skprev');document.documentElement.classList.add('skprev');   /* כפתור העיפרון יושב תחת html */
    if(R.stale)toast(R.stale+' קטעים התיישנו (הנוסח בדף השתנה מאז שנכתבו) ונשלחו לסבב חדש של סכם על הנוסח החי. השאר מוכנים לסקירה',7000);
    skpShow()}
  /* ---- התיישנות (פרומפט 36, 15.11.2026) ---- */
  /* קטע מאותר באמת: כל המזהים קיימים בדף, ברצף. חסר - לפי העוגן */
  function skpLocated(it,pos){
    if(it.kind==='missing')return !!skpAnchor(it);
    if(!it.ids||!it.ids.length)return false;
    const ix=it.ids.map(id=>pos.get(id));
    return ix.every((x,k)=>x!==undefined&&(!k||x===ix[k-1]+1))}
  function skpStaleList(R){
    const fu=flatU(),pos=new Map(fu.map((o,i)=>[o.u.id,i]));
    return {fu,pos,list:R.items.filter(it=>!R.dec[it.iid]&&!skpLocated(it,pos))}}
  const SKP_CLAIM=new Set();
  /* האזור החי של רצף קטעים מתיישנים: בין הקטע המאותר שלפניו לקטע המאותר שאחריו (בתוך הפרק) */
  async function skpRedo(R){
    const {fu,pos,list:all}=skpStaleList(R);
    /* אותו קטע לעולם אינו מוזמן פעמיים (הבדיקה ברקע והפתיחה רצות לעתים יחד): נתפס מיד, לפני כל המתנה */
    const key=it=>R.jid+':'+it.iid;
    all.filter(it=>SKP_CLAIM.has(key(it))).forEach(it=>{R.dec[it.iid]={act:'stale'}});
    const list=all.filter(it=>!SKP_CLAIM.has(key(it)));
    list.forEach(it=>SKP_CLAIM.add(key(it)));
    if(!list.length)return all.length;
    const sid=new Set(list.map(x=>x.iid));
    const si=R.job.perek?R.job.perek-1:cur;
    const S=SEC[si]||{from:0,to:D.pages.length-1};
    const inSec=i=>fu[i]&&fu[i].pi>=S.from&&fu[i].pi<=S.to;
    let a0=fu.findIndex((o,i)=>inSec(i)),a1=-1;for(let i=fu.length-1;i>=0;i--)if(inSec(i)){a1=i;break}
    const span=it=>{if(it.kind==='missing'||!skpLocated(it,pos))return null;const ix=it.ids.map(id=>pos.get(id));return [Math.min(...ix),Math.max(...ix)]};
    const runs=[];let cur=null;
    R.items.forEach((it,k)=>{if(sid.has(it.iid)){if(!cur){cur={k0:k,k1:k,its:[]};runs.push(cur)}cur.k1=k;cur.its.push(it)}
      else if(span(it))cur=null});
    let sent=0,jobs=[];
    for(const r of runs){
      let lo=a0,hi=a1;
      for(let k=r.k0-1;k>=0;k--){const sp=span(R.items[k]);if(sp){lo=sp[1]+1;break}}
      for(let k=r.k1+1;k<R.items.length;k++){const sp=span(R.items[k]);if(sp){hi=sp[0]-1;break}}
      const os=[];for(let i=Math.max(lo,a0);i<=Math.min(hi,a1);i++)os.push(fu[i]);
      try{
        if(os.some(o=>o.u.k==='u'||o.u.k==='m')){
          const title=skpTitle(si)+' · סבב על הנוסח החי ('+r.its.map(x=>x.iid).join(', ')+')';
          const packet=await skpPacket('seg',os);
          packet.parent=R.jid;packet.stale=r.its.map(x=>x.iid);
          const j=await api('/sakem/job',{method:'POST',body:JSON.stringify({slug:SLUG,kind:'seg',perek:si+1,title,packet})});
          jobs.push(j.jid)}
        /* רק אחרי שההזמנה נרשמה: ההצעה הישנה יוצאת מן הסקירה (ואינה מוזמנת שוב) */
        r.its.forEach(it=>{skpDec(it,'stale',null,R);sent++})}
      catch(e){
        /* ההזמנה נכשלה: הקטעים אינם מוצגים שבורים בפתיחה הזו, וייבדקו שוב בפתיחה הבאה. נאמר בקול */
        r.its.forEach(it=>{SKP_CLAIM.delete(key(it));if(R.bad)R.bad.add(it.iid)});
        flash('סבב על הנוסח החי לא הוזמן ('+r.its.map(x=>x.iid).join(', ')+'): '+(e.message||e))}}
    return sent+(all.length-list.length)}
  /* בדיקה ברקע, לפני שעבודה מוצגת "מוכן לסקירה": אחרי שהדף משך את כל העריכות (__LGSYNC), פעם אחת לכל עבודה בטעינה */
  const SKP_BG=new Set();
  async function skpBgCheck(){
    if(!skpOK()||SKP.rev)return;
    for(let k=0;k<30&&!window.__LGSYNC;k++)await new Promise(r=>setTimeout(r,2000));
    if(!window.__LGSYNC||SKP.rev)return;
    let any=0;
    for(const x of SKP.jobs.filter(y=>y.st==='ready'&&!SKP_BG.has(y.jid))){
      SKP_BG.add(x.jid);
      try{const j=await api('/sakem/out?jid='+encodeURIComponent(x.jid));
        const R={jid:x.jid,job:j.job||x,out:j.out,items:(j.out.items||[]).filter(y=>!y.nochange),dec:j.dec||{},cnt:{accept:0,reject:0,edit:0},bad:new Set()};
        try{skpRelocate(R)}catch(e){}
        const n=await skpRedo(R);
        if(n){any+=n;toast(esc(x.title||x.jid)+': '+n+' קטעים התיישנו ונשלחו לסבב חדש של סכם על הנוסח החי',6000)}}
      catch(e){}}
    if(any)setTimeout(skpLoad,1500)}
  /* 1.11.2026: מזהה יחידה הוא מספר הפסקה בוורד, וכל עריכה בוורד שלפני הפרק מזיזה אותו. הצעה שנכתבה
     לפני העריכה הצביעה על יחידות אחרות, ולכן הופיעה במקום הלא נכון וסורבה ("האלמנטים הנעולים אינם
     במקומם"). כאן כל הצעה מאותרת מחדש לפי תוכנה: אותיות הנוסח שההצעה נכתבה עליו מול אותיות היחידות שבדף.
     קטע שלא נמצא כלשונו (נערך באמת) מוזז באותו היסט של הקטע שלפניו, ומוצג כעריכה שלך. */
  const skpNorm=t=>String(t||'').split('\n').filter(s=>!/^\[(דף|משנה|גמרא|קבוע|מקור)(:[^\]]*)?\]$/.test(s.trim()))
    .join(' ').replace(/\[(מס|תוס'):[^\]]*\]/g,' ').replace(/[^א-ת]/g,'');
  function skpRelocate(R){
    const fu=flatU(),pos=new Map(fu.map((o,i)=>[o.u.id,i]));
    const sig=fu.map(o=>{try{return skpNorm(skmInter([o]))}catch(e){return '\u0000'}});
    let delta=0,exp=-1;
    const shift=ids=>{const ix=ids.map(id=>pos.get(id+delta));return ix.every((x,k)=>x!==undefined&&(!k||x===ix[k-1]+1))?ids.map(id=>id+delta):null};
    R.items.forEach(it=>{
      if(!it.ids||!it.ids.length)return;
      if(it.kind!=='seg'){if(delta){const s=shift(it.ids);if(s){it.ids=s;if(it.anchor&&pos.has(it.anchor+delta))it.anchor+=delta}}return}
      if(skmSame(it.ids,it.orig)){const q=pos.get(it.ids[it.ids.length-1]);if(q!==undefined)exp=q+1;return}
      const T=skpNorm(it.orig),n=it.ids.length;
      let best=-1,bd=Infinity;
      if(T)for(let i=0;i+n<=fu.length;i++){
        if(!T.startsWith(sig[i]))continue;
        let s='';for(let k=0;k<n&&s.length<=T.length;k++)s+=sig[i+k];
        if(s!==T)continue;
        const d=Math.abs(fu[i].u.id-(it.ids[0]+delta));if(d<bd){bd=d;best=i}}
      if(best>=0){const nids=fu.slice(best,best+n).map(o=>o.u.id);delta=nids[0]-it.ids[0];skpRemap(it,nids);it.ids=nids;it.orig=skmInter(skmUnits(nids));exp=best+n;return}
      if(delta){const s=shift(it.ids);if(s){skpRemap(it,s);it.ids=s;const q=pos.get(s[s.length-1]);if(q!==undefined)exp=q+1;return}}
      /* 15.11.2026 (שבת פרק כירה): אחרי בניית הוורד מחדש כל המזהים זזו, וגם הנוסח נערך בינתיים - שום קטע
         לא נמצא כלשונו, וההיסט לא עזר (מזהי עריכות האתר אינם זזים יחד עם מזהי הוורד). כל ההצעות הצביעו
         על יחידות אחרות או על כלום: "קבל" נחסם ("נוספו שורות במקום שלא היו בו שורות"), והחץ לקטע הבא
         הוביל לשום מקום. כאן איתור לפי דמיון: היחידות שבדף שרוב אותיות הנוסח שלהן נמצא בנוסח שההצעה נכתבה
         עליו, ברצף (עד שתי יחידות שנערכו ביניהן), קרוב למקום הצפוי. הקטע נמצא ומוצג כעריכה שלך (התנגשות). */
      const f=skpFuzzy(it,T,exp);
      if(f){const nids=fu.slice(f.i,f.last+1).map(o=>o.u.id);skpRemap(it,nids);it.ids=nids;exp=f.last+1}});
    function skpFuzzy(it,T,exp0){
      if(!T)return null;
      const hit=(s)=>{if(!s||s==='\u0000')return -1;if(s.length<6)return T.indexOf(s)>-1?1:0;
        let n=0,f=0;for(let i=0;i+6<=s.length;i+=6){n++;if(T.indexOf(s.substr(i,6))>-1)f++}return f/n};
      const lo=exp0<0?0:Math.max(0,exp0-800),hi=exp0<0?fu.length:Math.min(fu.length,exp0+800);
      const h=new Map();const H=i=>{if(!h.has(i))h.set(i,hit(sig[i]));return h.get(i)};
      let best=null;
      for(let i=lo;i<hi;i++){if(H(i)<0.6)continue;
        let last=i,gap=0,len=0,m=0;
        for(let j=i;j<fu.length;j++){const r=H(j);if(r<0)continue;
          if(r>=0.6){last=j;gap=0;m+=sig[j].length*r;len+=sig[j].length}else{gap++;if(gap>2)break;len+=sig[j].length}
          if(len>T.length*1.5)break}
        const sc=Math.min(m,T.length)/T.length,d=exp0<0?0:Math.abs(i-exp0);
        if(!best||sc>best.sc+0.05||(Math.abs(sc-best.sc)<=0.05&&d<best.d))best={i,last,sc,d}}
      return best&&best.sc>=0.5?best:null}}
  /* פרומפט 33 (12.11.2026) - התקלה "מחיקת עיטור שסכם הציע לא נשמרת אחרי קבל" (שבת פרקים א-ד):
     כשהמזהים זזו מאז ההצעה (פסקה שנוספה בוורד לפני הפרק), skpRelocate עדכן את it.ids ואת it.orig, אבל לא את
     המזהים שבתוך נוסח ההצעה. [מחק-עיטור:<מזהה ישן>] לא נמצא אז בקטע, דולג בשקט, ו-skpFixLocks החזיר את העיטור
     ([קבוע:<מזהה חדש>]) מן הדף: הקבלה הצליחה, העיטור נשאר, ושום רשומה לא נוצרה. בשבת פרק ד כל המזהים זזו ב-1
     (2788 בהצעה, 2789 בדף). כאן המזהים שבנוסח עוברים יחד עם הקטע, לפי מקומם: המזהה ה-k הישן - המזהה ה-k החדש. */
  function skpRemap(it,nids){
    const old=it.ids||[];if(!it.text||old.length!==nids.length)return;
    const M=new Map();old.forEach((id,k)=>{if(id!==nids[k])M.set(+id,nids[k])});if(!M.size)return;
    it.text=String(it.text).replace(/\[(מחק-עיטור|קבוע):(\d+)\]/g,(m,t,id)=>M.has(+id)?'['+t+':'+M.get(+id)+']':m);
    if(Array.isArray(it.hdel))it.hdel=it.hdel.map(id=>M.has(+id)?M.get(+id):id)}
  /* הצעה שהנעולים שבה ([דף], [מקור], [משנה] וכו') אינם כבנוסח שבדף - הנעולים נלקחים מן הדף:
     מה שחסר נשתל במקומו, מה שאינו בדף יוצא, ושורות ההצעה נשארות כמות שהן. */
  /* פרומפט 38 (15.11.2026): היישור עבר לקובץ המשותף (SKC.fixLocks), כדי שהדף והכותב (put) יבדקו אותו דבר.
     שם [מקור] אינו משתתף ביישור - הוא שגרם ל"קטע שלם נעלם" בשבת ז: */
  function skpFixLocks(orig,text){return SKC.fixLocks(orig,text)}
  window.skpFixLocks=skpFixLocks;
  function skpNextOpen(from,dir){const R=SKP.rev;for(let i=from+dir;i>=0&&i<R.items.length;i+=dir)if(!R.dec[R.items[i].iid]&&!(R.bad&&R.bad.has(R.items[i].iid)))return i;return -1}
  function skpClose(){skmClose(true);document.querySelectorAll('.skpold').forEach(r=>r.classList.remove('skpold','skpshow'));
    const b=$('#skpbar');if(b)b.remove();SKP.rev=null;document.body.classList.remove('skprev');document.documentElement.classList.remove('skprev');setTimeout(skpLoad,1500)}
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
      /* פרומפט 36: הרוח לא נבנתה - לא נתקעים: הקטע נדלג בפתיחה הזו, ונאמר בקול */
      const g=SKM.ghost;if(!g){R.bad.add(it.iid);flash('קטע '+it.iid+' לא הוצג בדף - דילוג');return skpMove(1)}
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
    /* פרומפט 36: בהתנגשות אמיתית (ערכת את הקטע אחרי ההצעה) - שלוש פעולות בכתב, לא רק סמלילים */
    if(conflict){const cb=document.createElement('div');cb.className='skpconfb';cb.contentEditable='false';
      cb.innerHTML='<button data-a="force">קבל את ההצעה</button><button data-a="keep">השאר את שלי</button>'+(it.kind==='seg'?'<button data-a="edit">ערוך</button>':'');
      cb.addEventListener('click',ev=>{const b=ev.target.closest('button');if(b){ev.stopPropagation();skpAct(b.dataset.a)}});
      const ch=g.querySelector('.skpchips');if(ch)ch.after(cb);else g.prepend(cb)}
    R.conflict=conflict;R.p=p;
    skpBar();skpTzFollow();
    /* פרומפט 36: בכל מעבר הרוח עצמה במרכז המסך, תמיד */
    g.scrollIntoView({block:'center',behavior:'smooth'});
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
      '<span class="skpc">התקבלו '+R.cnt.accept+' · נדחו '+R.cnt.reject+' · נערכו '+R.cnt.edit+(R.stale?' · התיישנו ונשלחו לסבב על הנוסח החי '+R.stale:'')+'</span>'+
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
      /* פרומפט 36: הפעולות גלויות תמיד (גם במחשב), ופועלות בלי תלות במיקוד */
      '<div class="skpnav"><button data-a="prev" title="הקטע הקודם (חץ למעלה)">הקודם</button>'+
      '<button data-a="'+(R.conflict?'force':'ok')+'" class="ok" title="'+(R.conflict?'קבל את ההצעה במקום העריכה שלך':'קבל ועבור לבא')+' (Enter)">'+(R.conflict?'קבל את ההצעה':'קבל')+'</button>'+
      '<button data-a="'+(R.conflict?'keep':'no')+'" class="no" title="'+(R.conflict?'השאר את העריכה שלך':'דחה - השאר את המקור')+' (Delete)">'+(R.conflict?'השאר את שלי':'דחה')+'</button>'+
      (it&&it.kind==='seg'?'<button data-a="edit" title="ערוך במקום (E)">ערוך</button>':'')+
      '<button data-a="next" title="דלג לקטע הבא בלי להכריע (חץ למטה)">דלג לבא</button></div>';
    /* פרומפט 36: גובה הסרגל משתנה (שורת סיכום, כרטיס ציון). כפתור העיפרון הצף ותחתית הדף זזים מעליו, כדי שלא יסתירו כפתור */
    try{document.documentElement.style.setProperty('--skpbarh',b.offsetHeight+'px')}catch(e){}}

  /* ---- ההכרעות ---- */
  function skpDec(it,act,extra,R0){
    const R=R0||SKP.rev;if(!R)return;
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
    /* פרומפט 33: עיטור מחוץ לקטע נמחק רק כשהוא צמוד לגבולות הקטע (מעליו או מתחתיו, בדילוג על עיטורים סמוכים).
       עיטור במקום אחר בדף - מזהה שזז - לעולם לא נמחק, ונאמר בקול (קודם דולג בשקט, או שנמחק עיטור אחר) */
    if(hd.bad.length){const fu=flatU(),ix=p.ids.map(id=>fu.findIndex(o=>o.u.id===id)).filter(i=>i>-1);
      const lo=Math.min(...ix),hi=Math.max(...ix),near=id=>{const i=fu.findIndex(o=>o.u.id===id);if(i<0||fu[i].u.k!=='hatz')return false;
        let a=i<lo?i:hi,b=i<lo?lo:i;for(let q=a+1;q<b;q++)if(fu[q].u.k!=='hatz')return false;return true};
      hdSkip=hd.bad.filter(id=>!near(id));
      if(hdSkip.length)toast('עיטור שסכם הציע למחוק לא אותר במקומו ('+hdSkip.join(', ')+') - לא נמחק. אם הוא עדיין צמוד לכותרת, מחק אותו בעורך',8000)}
    const hdIds=hd.ids.filter(id=>hdSkip.indexOf(id)<0);
    if(hd.ids.length){t=hd.text;if(hdIds.length)p.hdel=hdIds}
    const o2=hd.ids.length?hd.orig:p.orig;
    const rp=skmRepair(o2,t);t=rp.text;
    const errs=SKC.acceptErrs(o2,t);
    if(errs.length){const e=new Error(errs[0]);e.skpStuck={it,p,orig:o2,text:t,errs};throw e}
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
    let r;try{r=skpApplyOne(it,text,orig)}catch(e){
      /* פרומפט 38: לא תקוע - חלון עם "החל בכל זאת בלי השינוי הבעייתי" ו"פתח לעריכה במקום הבעייתי" */
      if(e.skpStuck&&window.skmStuck){const S=e.skpStuck;skmStuck({orig:S.orig,text:S.text,errs:S.errs,
        onEdit:()=>{if(!g.classList.contains('edit'))skpEditOn()},
        onSafe:t2=>{let r2;try{r2=skmApply(S.p,t2)}catch(er){flash('לא הוחל: '+(er.message||er));return}
          skmRemember(SKP.rev.jid+':'+it.iid,t2,r2.recs||[]);skmClose(true);R.cnt.edit++;R.hist.push({i:R.i,iid:it.iid,act:'edit',undo:r2.n>0});
          skpDec(it,'edit',{final:t2});toast('הוחל בלי החלק הבעייתי',4000);skpMove(1)}});return}
      flash('לא הוחל: '+(e.message||e));return}
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
    const R=SKP.rev;if(!R)return;
    /* פרומפט 36: המקשים פועלים כל עוד הסקירה פתוחה, בלי תלות במיקוד - חוץ משדה טופס או חלון, ומבתוך עריכה */
    const G=SKM.ghost,ed=!!(G&&G.classList.contains('edit')),inG=!!(G&&G.contains(e.target));
    const typing=!inG&&e.target.closest&&e.target.closest('input,textarea,select,.modal,#skptagm');
    if(typing)return;
    if(!G&&!/^Arrow(Up|Down)$|^Escape$/.test(e.key))return;
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
    '#skpready{margin-inline-start:8px;font-size:12.5px;color:#1f5a2c;white-space:nowrap}#skpready a{color:#1f5a2c;font-weight:700;text-decoration:none;padding:0 2px}#skpready a:hover{text-decoration:underline}'+
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
    '.skmghost.edit del.skpdel.skpdelro{opacity:.55;user-select:none;cursor:default;font-size:.92em}'+'body.skprev{padding-bottom:calc(var(--skpbarh,40px) + 8px)!important}html.skprev.skprev #lk-fab{bottom:calc(var(--skpbarh,40px) + 12px)!important}'+
    '#skpbar .skpnav{display:flex;gap:6px;margin-inline-start:auto}#skpbar .skpnav button{font-size:13px;padding:2px 12px}#skpbar .skpnav button.ok{background:#2e7d3c;border-color:#2e7d3c;color:#fff}#skpbar .skpnav button.no{color:#a8452f;border-color:#a8452f}'+
    '.skpconfb{display:flex;flex-wrap:wrap;gap:8px;margin:2px 0 6px}.skpconfb button{padding:3px 12px;border-radius:10px;border:1px solid #2e5b8a;background:#fff;color:#2e5b8a;font:600 13px inherit;cursor:pointer}.skpconfb button[data-a="force"]{background:#2e7d3c;border-color:#2e7d3c;color:#fff}.skpconfb button[data-a="keep"]{color:#a8452f;border-color:#a8452f}'+
    '.skptab{width:100%;border-collapse:collapse;font-size:13px}.skptab td{border-bottom:1px solid #eee;padding:4px}'+
    '@media (max-width:820px),(pointer:coarse){#skpbar .skpnav{flex-basis:100%;gap:6px;margin:0}#skpbar .skpnav button{flex:1;font-size:15px;padding:10px 0;border-radius:10px}'+
      '.skpside{display:none}.skmghost.skp,.skmghost.skpmiss{padding-left:8px}}'+
    '@media print{#skpbar,#skptag,#skptagm,.skphead,.skpbtn{display:none!important}}';
    document.head.appendChild(s)})();
  /* =================== פרומפט 38 (15.11.2026): שני כפתורים בסרגל העליון, למנהל =================== 
     "שורות כפולות N" - הכפולות והכמעט כפולות בפרק הנוכחי (SKC.dupFlags, אותה בדיקה של השומר, א1), ובשדה ההצעה
     הפתוח - בו. לחיצה קופצת לבאה במעגל ומסמנת במסגרת דקה בלבד (בלי רקע). המספר מתעדכן אחרי כל תיקון.
     "סכם הבא N" - ההצעות שטרם הוכרעו בפרק (או במסכת, כשבפרק אין). לחיצה פותחת את הבאה לסקירה; מן האחרונה בפרק -
     לראשונה בפרק הבא שיש בו הצעות. כשאין - "סכם: הכל הוכרע", אפור. "הבא בתור" שבתוך ההצעה נשאר כמו שהוא. */
  const SKTOP={dupI:-1,mark:null,tm:0};
  function sktLines(){
    const g=SKM.ghost;
    if(g&&g.isConnected){const ps=[...g.querySelectorAll('.skmmain p:not(.skmsrc)')].filter(p=>!p.closest('.skpdelro'));
      return {inGhost:true,list:ps.map(p=>({el:p,t:(p.textContent||'').replace(/\s+/g,' ').trim()}))}}
    const S=SEC[cur];if(!S)return {list:[]};
    const out=[];
    for(let pi=S.from;pi<=S.to;pi++)(D.pages[pi].units||[]).forEach(u=>{if(u.k!=='u'||!u.l)return;
      u.l.forEach((l,i)=>out.push({id:u.id,i,t:SKC.bare(l[1]||'').replace(/\s+/g,' ').trim()}))});
    return {list:out}}
  function sktDups(){const L=sktLines();const f=SKC.dupFlags(L.list.map(x=>x.t));
    const seen=new Set(),ds=[];f.forEach(d=>{if(!seen.has(d.i)){seen.add(d.i);ds.push(d)}});ds.sort((a,b)=>a.i-b.i);
    return {L,ds}}
  function sktEl(x){if(x.el)return x.el;const row=document.getElementById('u'+x.id);if(!row)return null;
    const ps=row.querySelectorAll('.main p');return ps[x.i]||row}
  function sktDupGo(){
    const {L,ds}=sktDups();if(!ds.length){sktDraw();return}
    SKTOP.dupI=(SKTOP.dupI+1)%ds.length;const x=L.list[ds[SKTOP.dupI].i];
    let el=sktEl(x);
    if(!el&&x.id){const pi=D.pages.findIndex(p=>(p.units||[]).some(u=>u.id===x.id));if(pi>-1&&typeof toDaf==='function'){toDaf(pi);el=sktEl(x)}}
    if(!el)return;
    if(SKTOP.mark)SKTOP.mark.classList.remove('sktdup');SKTOP.mark=el;el.classList.add('sktdup');
    try{el.scrollIntoView({block:'center',behavior:'smooth'})}catch(e){}
    const tw=L.list[ds[SKTOP.dupI].j];
    toast((ds[SKTOP.dupI].kind==='same'?'שורה כפולה':'כמעט כפולה: כולה בתוך שורה אחרת')+' ('+(SKTOP.dupI+1)+' מתוך '+ds.length+')'+(tw?' · הזוג: '+tw.t.slice(0,40):''),3500);
    clearTimeout(SKTOP.tm);SKTOP.tm=setTimeout(()=>{if(SKTOP.mark)SKTOP.mark.classList.remove('sktdup')},8000)}
  /* ההצעות שטרם הוכרעו: לכל עבודה מוכנה במסכת - כמה נשארו (בסקירה הפתוחה - מן ההכרעות שבדף, שהן מעודכנות יותר) */
  function sktLeft(j){const R=SKP.rev;if(R&&R.jid===j.jid)return R.items.filter(x=>!R.dec[x.iid]).length;
    return j.shown!=null?Math.max(0,(+j.shown||0)-(+j.dec||0)):1}
  function sktJobs(){return SKP.jobs.filter(j=>j.st==='ready'&&sktLeft(j)>0).sort((a,b)=>(a.perek||0)-(b.perek||0))}
  function sktNext(){
    const R=SKP.rev,J=sktJobs();
    if(R){const n=skpNextOpen(R.i,1);if(n>-1){R.i=n;skpShow();return}
      const w=skpNextOpen(-1,1);
      const cp=(R.job&&R.job.perek)||cur+1,nx=J.find(j=>j.jid!==R.jid&&(j.perek||0)>cp)||J.find(j=>j.jid!==R.jid);
      if(nx){skpOpen(nx.jid);return}
      if(w>-1){R.i=w;skpShow();return}
      sktDraw();return}
    const here=J.filter(j=>j.perek===cur+1),nx=here[0]||J.find(j=>(j.perek||0)>cur+1)||J[0];
    if(nx)skpOpen(nx.jid);else sktDraw()}
  function sktDraw(){
    if(!(typeof isAdmin==='function'&&isAdmin()))return;
    const ps=$('#peresel');let d=$('#skpdup'),n=$('#skpnext');
    const after=$('#skptag')||$('#skpbtn')||ps;
    if(!d&&after){d=document.createElement('button');d.id='skpdup';d.type='button';d.className='skpbtn skptop';d.onclick=e=>{e.stopPropagation();sktDupGo()};after.after(d)}
    if(!n&&d&&skpOK()){n=document.createElement('button');n.id='skpnext';n.type='button';n.className='skpbtn skptop';n.onclick=e=>{e.stopPropagation();sktNext()};d.after(n)}
    /* פרומפט 40: בסרגל סמליל קטן עם מונה; הכיתוב המלא בריחוף ובקורא המסך */
    if(d){const {L,ds}=sktDups();d.textContent='≡ '+ds.length;d.setAttribute('aria-label','שורות כפולות '+ds.length);d.classList.toggle('off',!ds.length);
      d.title='שורות כפולות · '+(L.inGhost?'בשדה ההצעה הפתוח':'בפרק הנוכחי')+': '+(ds.length?ds.length+' שורות כפולות או כמעט כפולות. לחיצה קופצת לבאה':'אין שורות כפולות');
      if(SKTOP.dupI>=ds.length)SKTOP.dupI=-1}
    if(n){const J=sktJobs(),here=J.filter(j=>j.perek===cur+1),R=SKP.rev;
      const cnt=(here.length?here:J).reduce((a,j)=>a+sktLeft(j),0);
      n.textContent=J.length?'◂ '+cnt:'◂ ✓';n.setAttribute('aria-label',J.length?'סכם הבא '+cnt:'סכם: הכל הוכרע');n.classList.toggle('off',!J.length);
      n.title=J.length?'סכם הבא · '+(here.length?'הצעות שטרם הוכרעו בפרק: ':'בפרק אין. הצעות שטרם הוכרעו במסכת: ')+cnt+'. לחיצה פותחת את הבאה'+(R?' (מן האחרונה בפרק - לפרק הבא)':''):'כל הצעות סכם במסכת הוכרעו'}
    try{if(typeof barH==='function')barH()}catch(e){}}
  window.skpTop={draw:sktDraw,dup:sktDupGo,next:sktNext,state:()=>{const J=sktJobs(),h=J.filter(j=>j.perek===cur+1);return {dups:sktDups().ds.length,left:(h.length?h:J).reduce((a,j)=>a+sktLeft(j),0),any:J.length>0}}};
  {const dr=skpDraw;skpDraw=function(){dr.apply(this,arguments);try{sktDraw()}catch(e){}}}
  {const sh=skpShow;skpShow=function(){const r=sh.apply(this,arguments);try{sktDraw()}catch(e){}return r}}
  {const dc=skpDec;skpDec=function(){const r=dc.apply(this,arguments);try{sktDraw()}catch(e){}return r}}
  /* אחרי כל תיקון - המספר מתעדכן מיד (אחרי שהעורך רשם את התיקון בנתונים, 700ms) */
  document.addEventListener('input',()=>{clearTimeout(SKTOP.ti);SKTOP.ti=setTimeout(()=>{try{sktDraw()}catch(e){}},1000)},true);
  document.addEventListener('keyup',e=>{if(e.ctrlKey||e.metaKey){clearTimeout(SKTOP.ti);SKTOP.ti=setTimeout(()=>{try{sktDraw()}catch(x){}},1000)}},true);
  setTimeout(()=>{try{sktDraw()}catch(e){}},1800);
  (function(){const s=document.createElement('style');s.textContent=
    '.skpbtn.skptop{font-weight:500;font-variant-numeric:tabular-nums;white-space:nowrap}.skpbtn.skptop.off{opacity:.45;cursor:default}'+
    '.sktdup{outline:1.5px solid #8a6d3b;outline-offset:2px;border-radius:2px}'+
    '@media print{.skptop{display:none!important}.sktdup{outline:0}}';document.head.appendChild(s)})();
  if(skpOK())setTimeout(()=>{skpLoad().then(()=>{const m=/skp=([a-z0-9-]+)/.exec(SKP_H0);if(m)skpOpen(m[1])})},2500);
