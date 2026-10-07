  /* =================== עורך המציע, ואישור הצעות מן העורך (מנה 2, 7.10.2026) ===================
     נטען אחרי suggest_ui.js.

     המציע: אותו עורך בדיוק, עם כל הקיצורים (Ctrl+1 עד Ctrl+7, Ctrl+נקודה, Ctrl+Z/Y, רווח לפני,
     ניקוי עיצוב, Enter, Backspace, Delete, פיצול ואיחוי). ההבדל היחיד: הפעולה אינה נכתבת לאתר,
     אלא נרשמת כהצעה. הצעת סגנון נשמרת כפעולה מבנית מדויקת - איזה טווח, מאיזה סגנון לאיזה סגנון -
     ולא כטקסט חופשי, כדי שתחול אוטומטית באישור. אין מגבלה על מספר ההצעות.

     המנהל: "אשר" מחיל את ההצעה מיד על הטקסט (ונכתבת לוורד במנגנון הקליטה הקיים). אם הטקסט השתנה
     מאז שההצעה נכתבה - אזהרה, והצעה להחיל על הנוסח הנוכחי; לעולם לא בעיוורון. */
  STYPES.struct=['שינוי מבנה','⇅','#2a7a7a'];
  const SKL={text:'נוסח',create:'יצירת סגנון',remove:'הסרת סגנון',replace:'החלפת סגנון',para:'סגנון פסקה',struct:'שינוי מבנה',mixed:'כמה שינויים'};
  (function(){const st=document.createElement('style');st.textContent=
    '.sqba{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin:4px 0}.sqba>div{border-radius:5px;padding:3px 8px;font-size:15px;line-height:1.55}'+
    '.sqba .o{background:#fdf0ee;border:1px solid #e9b8b0}.sqba .n{background:#eef8f0;border:1px solid #b7dcc0}'+
    '.sqba small{display:block;color:#7a6f5c;font-size:12px}.sqba p{margin:0}'+
    '.chg-o{background:#f3b5ab;border-radius:2px}.chg-n{background:#9ed4ab;border-radius:2px}'+
    '.sqwarn{background:#fff3d6;border:1px solid #e3c277;border-radius:5px;padding:2px 8px;margin:4px 0;font-size:14px}'+
    '.sugbadge{background:#2e5b8a!important;color:#fff!important}'+
    
    '.sgmodal .box{max-width:460px}.sgmodal input[type=text]{width:100%;font:inherit;box-sizing:border-box;margin:4px 0 8px}';
    document.head.appendChild(st)})();

  /* ---------- סגנונות תו: תווית לכל תו ---------- */
  /* מפרק HTML לטקסט ולרשימת תוויות (קבוצת סגנונות תו לכל תו), ובונה אותו מחדש */
  function lbOf(html){
    const d=document.createElement('div');d.innerHTML=html||'';
    let t='';const l=[];
    (function w(n,cls){
      for(const c of n.childNodes){
        if(c.nodeType===3){const v=c.nodeValue;for(let i=0;i<v.length;i++){t+=v[i];l.push(cls)}}
        else if(c.nodeType===1){
          if(c.tagName==='BR'){t+='\n';l.push(cls);continue}
          let k=cls;
          if(c.tagName==='I'&&c.className)k=lbJoin(cls,c.className);
          else if(c.tagName==='B')k=lbJoin(cls,'b');
          w(c,k)}}})(d,'');
    return {t,l}}
  function lbJoin(a,b){return [...new Set((a?a.split(' '):[]).concat(b.split(' ')))].filter(Boolean).sort().join(' ')}
  function lbHtml(t,l,mark,mcls){
    let h='',i=0;
    while(i<t.length){
      let j=i;const m=mark&&mark.has(i);
      while(j<t.length&&l[j]===l[i]&&(!!(mark&&mark.has(j)))===!!m)j++;
      let seg=esc(t.slice(i,j)).replace(/\n/g,'<br>');
      if(m)seg='<span class="'+mcls+'">'+seg+'</span>';
      const toks=l[i]?l[i].split(' '):[];
      for(let k=toks.length-1;k>=0;k--)seg=toks[k]==='b'?'<b>'+seg+'</b>':'<i class="'+toks[k]+'">'+seg+'</i>';
      h+=seg;i=j}
    return h}
  function lbTok(s){return s?s.split(' ').filter(Boolean):[]}
  function sugStyName(c){if(c==='b')return 'מודגש';const f=CSTY.find(x=>x[0]===c);return f?f[1]:c}
  /* טווחים שבהם התווית השתנתה (אותו טקסט בשני הצדדים) */
  function lbRanges(A,B){const out=[];let i=0;const n=A.length;
    while(i<n){if(A[i]===B[i]){i++;continue}
      let j=i;while(j<n&&A[j]===A[i]&&B[j]===B[i])j++;
      out.push({a:i,b:j,from:A[i],to:B[i]});i=j}
    return out}
  function lbKind(r){const f=lbTok(r.from),t=lbTok(r.to);
    const add=t.filter(x=>f.indexOf(x)<0),rem=f.filter(x=>t.indexOf(x)<0);
    return {k:rem.length?(add.length?'replace':'remove'):'create',add,rem}}
  function lbRoundtrip(h){const x=lbOf(h);return normH(lbHtml(x.t,x.l))===normH(h)}

  /* ---------- מה המציע עשה: תיאור, סוג והפעולה המדויקת ---------- */
  function sugBaseOf(e){const b=SUGBASE[e.k];
    return b?{t:b.now,h:b.nowH,p:b.ps!==undefined?b.ps:b.wasP}:{t:e.was,h:e.wasH,p:e.wasP}}
  /* מקטע ההבדל בין שני נוסחים, מורחב לגבולות מילים */
  function sugFrag(a,b){
    let i=0;const m=Math.min(a.length,b.length);
    while(i<m&&a[i]===b[i])i++;
    let j=0;while(j<m-i&&a[a.length-1-j]===b[b.length-1-j])j++;
    let s=i,ea=a.length-j;
    while(s>0&&!/\s/.test(a[s-1]))s--;
    while(ea<a.length&&!/\s/.test(a[ea]))ea++;
    const eb=b.length-(a.length-ea);
    return {s,ea,eb,f1:a.slice(s,ea),f2:b.slice(s,eb)}}
  function sugShort(t,n){t=(t||'').replace(/\s+/g,' ').trim();return t.length>n?t.slice(0,n)+'…':t}
  function sugDescribe(e){
    if(e.op==='struct')return {type:'struct',sk:'struct',note:structName(e)+': '+sugShort(structShow(e),100),was:sugShort((e.texts||[]).join(' | '),200)};
    const base=sugBaseOf(e);
    const bt=base.t!==undefined?base.t:e.was;
    const textCh=bt!==e.now;
    const effP=e.ps!==undefined?e.ps:e.wasP, paraCh=(effP||'')!==(base.p||'');
    let charNote='',sk='';
    const lb=lbOf(base.h!==undefined?base.h:esc(bt)),ln=lbOf(e.nowH!==undefined?e.nowH:esc(e.now));
    let rs=[];
    if(!textCh&&lb.t===ln.t)rs=lbRanges(lb.l,ln.l);
    if(textCh){
      const fr=sugFrag(bt,e.now);
      const bits=[];
      const ul=x=>[...new Set(x)].sort().join('|');
      if(ul(lb.l)!==ul(ln.l))bits.push('ועיצוב');
      return {type:'nusach',sk:(paraCh||bits.length)?'mixed':'text',
        note:(fr.f2||'[מחיקה]')+(paraCh?' · '+'סגנון פסקה: '+psName(effP):''),was:fr.f1||sugShort(bt,60)}}
    if(rs.length){
      const kinds=new Set(rs.map(r=>lbKind(r).k));
      sk=kinds.size>1?'mixed':[...kinds][0];
      const first=rs[0],kd=lbKind(first),nm=a=>a.map(sugStyName).join(' + '),frag=sugShort(bt.slice(first.a,first.b),40);
      charNote=kd.k==='create'?'החלת הסגנון «'+nm(kd.add)+'» על: «'+frag+'»':
               kd.k==='remove'?'הסרת הסגנון «'+nm(kd.rem)+'» מ: «'+frag+'»':
               'החלפת הסגנון «'+nm(kd.rem)+'» ב«'+nm(kd.add)+'» ב: «'+frag+'»';
      if(rs.length>1)charNote+=' (ועוד '+(rs.length-1)+' קטעים)'}
    else if(!paraCh&&normH(base.h||'')!==normH(e.nowH||'')){sk='mixed';charNote='שינוי עיצוב'}
    if(paraCh){charNote+=(charNote?' · ':'')+'סגנון פסקה: «'+psName(base.p||'')+'» ← «'+psName(effP)+'»';sk=sk?'mixed':'para'}
    if(!charNote)return null;
    return {type:'style',sk,note:charNote,was:sugShort(bt,120)}}
  function sugEdit_(e){
    const base=sugBaseOf(e);
    if(e.op==='struct')return {op:'struct',kind:e.kind,ins:e.ins,where:e.where,texts:e.texts,res:e.res,resT:e.resT,psw:e.psw,daf:e.daf,t:e.t};
    return {k:e.k,bt:base.t,bh:base.h,bp:base.p,was:e.was,wasH:e.wasH,now:e.now,nowH:e.nowH,wasP:e.wasP,
            ps:e.ps,psw:e.psw,daf:e.daf,ctx:e.ctx,t:e.t}}

  /* ---------- כניסה ויציאה ---------- */
  let SUGT=null,SUGBUSY=false,SUGMSG='',SUGSENT={},SUGCOUNT=0;
  function sugEdit(){
    if(isAdmin()&&(admKey()||ONGESHER)){toast('אתה מנהל: כפתור "עריכה" פותח את העורך הרגיל, וההצעות באות אליך בתור.',4500);return}
    if(EDIT){setEdit(false);return}
    sugEnter()}
  function sugEnter(){
    SUGM=true;document.body.classList.add('sugm');
    SUGBASE={};SUGSENT={};SUGCOUNT=0;
    ED.forEach(x=>{if(x.op!=='struct')SUGBASE[x.k]={now:x.now,nowH:x.nowH,ps:x.ps,wasP:x.wasP}});
    setEdit(true);
    if(!EDIT){SUGM=false;document.body.classList.remove('sugm');return}
    toast('מצב הצעה: ערוך כרגיל, עם כל הקיצורים. כל פעולה נשלחת לעורך כהצעה, ואינה משנה את האתר.',6000)}
  function edChoose(){
    const old=$('#edchoose');if(old){old.remove();return}
    const m=document.createElement('div');m.className='modal sgmodal';m.id='edchoose';
    m.innerHTML='<div class="box"><h3>עריכה</h3>'+
      '<p style="margin:4px 0 8px">אפשר להציע תיקון בעורך המלא, עם כל הקיצורים: כל פעולה שלך תישלח לעורך כהצעה, והוא יאשר או ידחה.</p>'+
      '<label for="edcn">שמך (לא חובה, כדי שהעורך יידע ממי ההצעה)</label>'+
      '<input type="text" id="edcn" maxlength="80" value="'+esc(localStorage.getItem('lg-sg-name')||'')+'">'+
      '<div class="btns"><button id="edc-sug" style="font-weight:700">אני מציע תיקון</button>'+
      '<button id="edc-adm">אני המנהל</button><button id="edc-x">ביטול</button></div></div>';
    document.body.appendChild(m);
    m.addEventListener('click',e=>{if(e.target===m)m.remove()});
    $('#edc-x').onclick=()=>m.remove();
    $('#edc-sug').onclick=()=>{try{localStorage.setItem('lg-sg-name',$('#edcn').value.trim())}catch(e){}m.remove();sugEnter()};
    $('#edc-adm').onclick=()=>{m.remove();askAdminWord()}}

  /* ---------- שליחה ---------- */
  function sugSoon(){clearTimeout(SUGT);SUGT=setTimeout(()=>sugPush(0),2500);sugDraw()}
  function sugDraw(){const el=$('#edpub');if(!el)return;
    const pend=ED.filter(e=>!e.pub&&!e.lost).length;
    el.textContent=SUGMSG||(SUGBUSY?'שולח…':pend?(pend===1?'הצעה אחת ממתינה לשליחה':pend+' הצעות ממתינות לשליחה'):SUGCOUNT?SUGCOUNT+' הצעות נשלחו לעורך':'אין הצעות ממתינות');
    el.className='edpub'+(SUGMSG.indexOf('לא נשלח')===0?' bad':'')}
  /* הופך כל פעולה שטרם נשלחה להצעה בתור היוצא, ושולח */
  async function sugPush(loud){
    clearTimeout(SUGT);
    const name=(localStorage.getItem('lg-sg-name')||'').trim();
    const id=pident();
    for(const e of ED){
      if(e.pub||e.lost)continue;
      if(e.op==='struct')edKeys();
      const d=sugDescribe(e);
      if(!d){e.pub=1;continue}
      const rec={slug:SLUG,masechet:D.masechet,daf:e.daf||'',uid:((/^u(\d+)/.exec(e.k||'')||[])[1])||'',k:e.k||'',
        ctx:e.ctx||{b:'',a:''},was:d.was,note:d.note,name,type:d.type,sk:d.sk,edit:sugEdit_(e),
        pid:id.pid,pt:id.pt,grp:sgGrp(),hp:'',t:Date.now(),sent:0,ek:e.k||''};
      /* אותה שורה שנערכה שוב: מחליפה הצעה שטרם נשלחה, או מעדכנת את זו ששלחנו */
      const un=SG.findIndex(g=>g.ek&&g.ek===rec.ek&&!g.sent);
      if(un>-1){rec.upd=SG[un].upd;SG[un]=rec}
      else{if(SUGSENT[rec.ek])rec.upd=SUGSENT[rec.ek];SG.push(rec)}
      e.pub=1;e.sgi=1;e.sgk=e.sgk||e.k}
    /* הצעה ששלחנו והפעולה בוטלה (Ctrl+Z, או חזרה לנוסח המקורי): נמשכת */
    for(const k of Object.keys(SUGSENT)){
      if(ED.some(x=>x.k===k||x.sgk===k))continue;
      const sid=SUGSENT[k];delete SUGSENT[k];SUGCOUNT=Math.max(0,SUGCOUNT-1);
      try{await papi('/mine/delete',{id:sid})}catch(err){}}
    for(const g of SG){if(g.ek&&!g.sent&&!ED.some(x=>x.k===g.ek||x.sgk===g.ek)){g.sent=1;g.bad='בוטלה לפני השליחה'}}
    saveSG();
    let ok=0,fail=0,why='';
    if(SUGBUSY)return;SUGBUSY=true;
    for(const g of SG){
      if(g.sent)continue;
      if(!g.pid){const i=pident();g.pid=i.pid;g.pt=i.pt}
      try{const j=await api('/suggest',{method:'POST',body:JSON.stringify(g)});
        g.sent=1;g.id=j.id;ok++;if(g.ek)SUGSENT[g.ek]=j.id}
      catch(err){why=err.message||'';
        if(/קישור|נדחה|ארוכה|תואמת/.test(why)){g.sent=1;g.bad=why}
        else{fail++;if(/מהירה/.test(why))setTimeout(()=>sugPush(0),4000)}}}
    saveSG();SUGBUSY=false;
    SUGCOUNT=Object.keys(SUGSENT).length;
    SUGMSG=fail?(loud?'לא נשלח: '+(why||'אין חיבור')+' · ההצעות שמורות במכשיר ויישלחו שוב':''):'';
    if(loud&&ok&&!fail)toast('נשלחו '+ok+' הצעות לעורך. אפשר לעקוב ב"ההצעות שלי".');
    else if(loud&&!ok&&!fail)toast('אין הצעות חדשות לשלוח.');
    if(fail)setTimeout(()=>sugPush(0),45000);
    sugDraw();drawEd();drawSg2&&drawSg2()}
  /* יציאה מהדף: מה שנותר נשלח עם keepalive */
  function sugFlush(){
    try{
      for(const e of ED){if(e.pub||e.lost)continue;
        const d=sugDescribe(e);if(!d){e.pub=1;continue}
        const id=pident();
        SG.push({slug:SLUG,masechet:D.masechet,daf:e.daf||'',uid:((/^u(\d+)/.exec(e.k||'')||[])[1])||'',k:e.k||'',
          ctx:e.ctx||{b:'',a:''},was:d.was,note:d.note,name:(localStorage.getItem('lg-sg-name')||'').trim(),type:d.type,sk:d.sk,
          edit:sugEdit_(e),pid:id.pid,pt:id.pt,grp:sgGrp(),hp:'',t:Date.now(),sent:0,ek:e.k||'',upd:SUGSENT[e.k||'']});
        e.pub=1}
      saveSG();
      for(const g of SG){if(g.sent)continue;
        fetch(SUGGEST_API+'/suggest',{method:'POST',keepalive:true,headers:{'content-type':'application/json; charset=utf-8'},body:JSON.stringify(g)})}
    }catch(err){}}

  /* ---------- המנהל: איתור מקומה של הצעה מן העורך, החלה, ותצוגה ---------- */
  /* איתור: שורה שהטקסט שלה הוא נקודת המוצא של המציע (בלי ניקוד), לפי המפתח ואחרת לפי הטקסט, ורק אם ייחודית */
  function sqLocate(g,S){
    if(g.edit&&g.edit.op==='struct'){
      const h=findRun(g.edit.texts||[],g.edit.daf);
      if(!h)return null;
      return S.find(x=>x.k==='u'+h.u.id+'.'+(h.i+1))||null}
    if(g.edit){
      const E=g.edit,bt=nonik(E.bt!==undefined?E.bt:E.was);
      let s=S.find(x=>x.k===E.k&&nonik(x.t)===bt);if(s)return s;
      const k0=dafKey(g.daf||E.daf);
      const c=S.filter(x=>{const k=dafKey(x.daf);return (k0===null||k===null||Math.abs(k-k0)<=1)&&nonik(x.t)===bt});
      if(c.length===1)return c[0];
      /* לא תואם בדיוק: אולי הטקסט השתנה אך המקום עדיין שם */
      const r=sugRebase(E,S);
      if(r)return Object.assign({},r.s,{rebase:1});
      return null}
    const has=s=>s.t.indexOf(g.was)>-1||nonik(s.t).indexOf(nonik(g.was))>-1;
    if(g.k){const s=S.find(x=>x.k===g.k);if(s&&has(s))return s}
    if(g.uid){const c=S.filter(x=>String(x.id)===String(g.uid)&&has(x));if(c.length===1)return c[0]}
    const k0=dafKey(g.daf);
    let c=S.filter(x=>{const k=dafKey(x.daf);return (k0===null||k===null||Math.abs(k-k0)<=1)&&has(x)});
    if(c.length>1&&g.ctx){const i=x=>S.indexOf(x);
      c=c.filter(x=>{const p=S[i(x)-1],n=S[i(x)+1];
        return (!g.ctx.b||(p&&p.t.slice(-40)===g.ctx.b))&&(!g.ctx.a||(n&&n.t.slice(0,40)===g.ctx.a))})}
    return c.length===1?c[0]:null}
  /* החלה על נוסח שהשתנה: מקטע ההבדל (או טווח הסגנון) מאותר לפי הסביבה שלו, ורק אם הופיע פעם אחת */
  function sugAnchorFind(cur,bt,a,b){
    const pre=bt.slice(Math.max(0,a-20),a),mid=bt.slice(a,b),post=bt.slice(b,b+20);
    const needle=pre+mid+post;
    if(!needle.trim())return -1;
    const i=cur.indexOf(needle);
    if(i<0||cur.indexOf(needle,i+1)>-1)return -1;
    return i+pre.length}
  /* מחזיר {s,nowH,rebased} או null. exact כשהשורה זהה לנקודת המוצא של המציע */
  function sugRebase(E,S,force){
    const bt=E.bt!==undefined?E.bt:E.was;
    const k0=dafKey(E.daf);
    const cand=S.filter(x=>{const k=dafKey(x.daf);return (k0===null||k===null||Math.abs(k-k0)<=1)});
    const first=cand.find(x=>x.k===E.k);
    const pool=first?[first].concat(cand.filter(x=>x!==first)):cand;
    const textCh=bt!==E.now;
    let found=null,n=0;
    for(const s of pool){
      const r=sugApplyTo(E,s,bt,textCh);
      if(r){if(s===first){return {s,nowH:r,rebased:true}}
        n++;found={s,nowH:r,rebased:true}}}
    return n===1?found:null}
  function sugApplyTo(E,s,bt,textCh){
    const curT=s.t,curH=s.h;
    if(textCh){
      const fr=sugFrag(bt,E.now);
      const st=sugAnchorFind(curT,bt,fr.s,fr.ea);
      if(st<0)return null;
      const h=replaceInHTML(curH,curT.slice(st,st+(fr.ea-fr.s)),fr.f2);
      return h}
    /* עיצוב בלבד: הטקסט של השורה זהה, אבל אולי השתנה במקום אחר */
    if(!E.bh||!E.nowH)return null;
    const lb=lbOf(E.bh),ln=lbOf(E.nowH);
    if(lb.t!==ln.t)return null;
    const rs=lbRanges(lb.l,ln.l);if(!rs.length)return null;
    if(!lbRoundtrip(curH))return null;
    const cl=lbOf(curH);
    if(cl.t!==curT&&nonik(cl.t)!==nonik(curT))return null;
    for(const r of rs){
      const st=sugAnchorFind(cl.t,lb.t,r.a,r.b);if(st<0)return null;
      const f=lbTok(r.from),t=lbTok(r.to);
      const add=t.filter(x=>f.indexOf(x)<0),rem=f.filter(x=>t.indexOf(x)<0);
      for(let i=st;i<st+(r.b-r.a);i++){
        let tk=lbTok(cl.l[i]).filter(x=>rem.indexOf(x)<0);
        for(const a of add)if(tk.indexOf(a)<0)tk.push(a);
        cl.l[i]=tk.sort().join(' ')}}
    return lbHtml(cl.t,cl.l)}
  /* תצוגת הצעה בתור: לפני ואחרי, בצבעים */
  function sqEditCtx(g,s){
    const E=g.edit;
    const warn=(s&&s.rebase)?'<div class="sqwarn">הטקסט בשורה השתנה מאז שההצעה נכתבה. האישור יחיל אותה על הנוסח הנוכחי, אחרי שאלה.</div>':'';
    if(E.op==='struct'){
      return warn+'<div class="sqba"><div class="o"><small>לפני</small>'+esc((E.texts||[]).join(' ⟂ '))+'</div>'+
        '<div class="n"><small>אחרי ('+esc(structName(E))+')</small>'+esc(structShow(E))+'</div></div>'}
    const bt=E.bt!==undefined?E.bt:E.was,bh=E.bh!==undefined?E.bh:esc(bt);
    const textCh=bt!==E.now;
    const effP=E.ps!==undefined?E.ps:E.wasP,paraCh=(effP||'')!==(E.bp||'');
    let bHtml,nHtml;
    const lb=lbOf(bh),ln=lbOf(E.nowH!==undefined?E.nowH:esc(E.now));
    if(textCh){
      const fr=sugFrag(bt,E.now);
      const pre=bt.slice(Math.max(0,fr.s-60),fr.s),post=bt.slice(fr.ea,fr.ea+60);
      bHtml=esc(pre)+'<span class="chg-o">'+esc(fr.f1||'∅')+'</span>'+esc(post);
      nHtml=esc(pre)+'<span class="chg-n">'+esc(fr.f2||'[מחיקה]')+'</span>'+esc(post)}
    else{
      const rs=lb.t===ln.t?lbRanges(lb.l,ln.l):[];
      const mk=new Set();rs.forEach(r=>{for(let i=r.a;i<r.b;i++)mk.add(i)});
      bHtml=lbHtml(lb.t,lb.l,mk,'chg-o');nHtml=lbHtml(ln.t,ln.l,mk,'chg-n')}
    const para=paraCh?'<div class="dr">סגנון פסקה: <b>'+esc(psName(E.bp||''))+'</b> ← <b>'+esc(psName(effP))+'</b></div>':'';
    return warn+'<div class="sqba"><div class="o"><small>לפני</small><p>'+bHtml+'</p></div><div class="n"><small>אחרי</small><p>'+nHtml+'</p></div></div>'+para}

  /* הכרעה בהצעה מן העורך. דחייה/התיישנות עוברות בנתיב הרגיל. */
  async function sqDecideEdit(id,st){
    const g=QQ.find(x=>x.id===id);if(!g||!g.edit)return false;
    const E=g.edit,by='הצעה מהאתר'+(g.name?' - '+g.name:'');
    let edit=null;
    if(E.op==='struct'){
      if(!findRun(E.texts||[],E.daf)){sqAlert('הפסקה השתנתה מאז ההצעה, ואי אפשר להחיל פעולת מבנה עליה. סמן כהתיישנה.');return true}
      edKeys();
      const ne=Object.assign({},E,{t:Date.now(),pub:0,by,sg:g.id});delete ne._ap;ne.k='s'+ne.t;
      ED.push(ne);
      const pre=D.pages.map(p=>JSON.stringify(p.units));
      applyIncoming();
      if(ne.lost||!ne._ap){ED=ED.filter(x=>x!==ne);SLOTS=null;sqAlert('הפעולה לא הוחלה: הפסקה השתנתה מאז ההצעה.');return true}
      SQUNDO={id,g,prev:null,k:'',wasH:'',struct:ne,pre};
      edit=ne}
    else{
      const S=slotsFull();
      let s=null,nowH=null,rebased=false;
      const bt=E.bt!==undefined?E.bt:E.was;
      const exact=S.find(x=>x.k===E.k&&nonik(x.t)===nonik(bt))||
        (()=>{const k0=dafKey(g.daf||E.daf);const c=S.filter(x=>{const k=dafKey(x.daf);return (k0===null||k===null||Math.abs(k-k0)<=1)&&nonik(x.t)===nonik(bt)});return c.length===1?c[0]:null})();
      if(exact){
        s=exact;
        const hExact=E.bh===undefined||normH(s.h)===normH(E.bh);
        if(hExact)nowH=E.nowH!==undefined?E.nowH:esc(E.now);
        else{const r=sugApplyTo(E,s,bt,bt!==E.now);if(r!==null){nowH=r;rebased=true}}}
      if(nowH===null){
        const r=sugRebase(E,S);
        if(!r){sqAlert('הטקסט בשורה השתנה מאז ההצעה, ואי אפשר להחיל אותה עליו. סמן כהתיישנה, או דחה.');return true}
        s=r.s;nowH=r.nowH;rebased=true}
      const nowT=plain(nowH);
      if(rebased&&!SQBULK&&!confirm('הטקסט בשורה השתנה מאז שההצעה נכתבה.\nלהחיל את ההצעה על הנוסח הנוכחי?\n\nהנוסח הנוכחי: '+sugShort(s.t,120)+'\nאחרי ההחלה: '+sugShort(nowT,120)))return true;
      if(rebased&&SQBULK){sqAlert('הצעה שהטקסט שלה השתנה דולגה: '+sugShort(s.t,40));return true}
      const old=ED.find(x=>x.k===s.k&&x.op!=='struct');
      const wasT=old?old.was:s.t, wasH=old?(old.wasH!==undefined?old.wasH:s.h):s.h;
      const cls=(s.c||'').split(' ').filter(c=>PCLS.indexOf(c)>-1).join(' ');
      edit={k:s.k,was:wasT,now:nowT,wasH,nowH,wasP:old?old.wasP:cls,daf:s.daf,ctx:{b:'',a:''},t:Date.now(),pub:0,by,sg:g.id};
      const effP=E.ps!==undefined?E.ps:undefined;
      if(effP!==undefined&&(effP||'')!==(E.bp||'')){edit.ps=effP;edit.psw=E.psw!==undefined?E.psw:wsty(effP)}
      else if(old&&old.ps!==undefined){edit.ps=old.ps;edit.psw=old.psw}
      SQUNDO={id,g,prev:old||null,k:s.k,wasH:s.h};
      if(old)ED=ED.filter(x=>x!==old);
      ED.push(edit);saveED()}
    try{await api('/decide',{method:'POST',body:JSON.stringify({id,st:(st==='edited'?'accepted':st),now:edit.now||'',reason:'',edit,sty:D.sty})})}
    catch(err){
      ED=ED.filter(x=>x!==edit);SQUNDO&&SQUNDO.prev&&ED.push(SQUNDO.prev);saveED();
      if(edit.op==='struct')location.reload();
      sqAlert('ההכרעה לא נרשמה: '+err.message);return true}
    QQ=QQ.filter(x=>x.id!==id);QQTOT=Math.max(0,QQTOT-1);
    if(edit.op!=='struct'){applyTextNow(edit)}
    drawEd();pubSoon();syncSoon();sqBadge();sqMark();drawSq();
    toast('ההצעה הוחלה מיד על הטקסט. Ctrl+Z בתור מבטל.');
    return true}

  /* אישור כל ההצעות מאותו סוג של אותו מציע, עם תצוגה מקדימה */
  function sqSame(id){
    const g=QQ.find(x=>x.id===id);if(!g)return;
    const list=QQ.filter(x=>x.pid&&x.pid===g.pid&&x.type===g.type&&x.sk===g.sk&&x.edit);
    if(!list.length){toast('אין הצעות נוספות מאותו סוג.');return}
    const old=$('#sqsame');if(old)old.remove();
    const m=document.createElement('div');m.className='modal sgmodal';m.id='sqsame';
    const rows=list.map(x=>'<tr><td style="padding:2px 6px;white-space:nowrap">'+esc(x.daf||'')+'</td><td style="padding:2px 6px">'+esc(x.note)+'</td></tr>').join('');
    m.innerHTML='<div class="box" style="max-width:640px"><h3>אישור כל ההצעות מאותו סוג</h3>'+
      '<p>'+esc(g.name||'מציע בלי שם')+' · '+esc(SKL[g.sk]||'')+' · '+list.length+' הצעות. תצוגה מקדימה לפני האישור:</p>'+
      '<div style="max-height:46vh;overflow:auto;border:1px solid #d9d1bd"><table style="width:100%;border-collapse:collapse">'+rows+'</table></div>'+
      '<div class="btns"><button id="sqs-go" style="font-weight:700">אשר את כולן ('+list.length+')</button><button id="sqs-x">ביטול</button></div></div>';
    document.body.appendChild(m);
    $('#sqs-x').onclick=()=>m.remove();
    $('#sqs-go').onclick=async()=>{
      m.remove();SQBULK=true;SQMSG=[];let n=0;
      for(const x of list){const before=QQ.length;await sqDecide(x.id,'accepted');if(QQ.length<before)n++}
      SQBULK=false;
      toast('אושרו '+n+' מתוך '+list.length+(n<list.length?'. '+(list.length-n)+' דולגו (הטקסט השתנה או לא אותר).':'.'),6000);
      queueLoad()}}
  function sqStyleFilter(){const on=SQF.ty==='style';SQF.ty=on?'':'style';SQPAGE=0;queueLoad()}
