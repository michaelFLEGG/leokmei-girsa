  /* =================== מנוע הדפסה ל-PDF (11.10.2026) ===================
     מוזרק לדף המסכת. במצב הדפסה (?print=1) הוא מחליף את התצוגה בעמודי A4 בשני טורים, ואת העימוד הוא מחשב בעצמו:
     סרגל אחד רציף (#flow) ברוחב המסילה והמידה, מדידת כל שורה, ואז מילוי טור אחר טור עד לגובה הנטו פחות הערות
     השוליים של אותו טור. הטור מוצג כחלון חיתוך על הסרגל הרציף, ולכן שבירת השורות זהה לאתר.
     כל המידות בקובץ הפרופיל (print-profiles/a4.json). פרופיל B5 יהיה קובץ נוסף ולא מנוע חדש.
     הפקת ה-PDF עצמו: tools/print/render_pdf.py (דפדפן אחד קבוע, לא דפדפן הלומד). */
  (function(){
  var QS=new URLSearchParams(location.search);
  var ON=QS.get('print')==='1';
  var MM=96/25.4;                         /* פיקסלים למילימטר */
  var PT=96/72;
  var FAM=[['Frank',400],['Frank',700],['Frank',900],['Vilna',300],['Vilna',400],['Vilna',500],['Vilna',700],['Vilna',900]];
  var HEADS={'nose':1,'dh':1,'perek-range':1,'perek-start':1,'hatz':1};
  function ge(s){return String(s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
  function lsGet(k,d){try{var v=localStorage.getItem(k);return v===null?d:v}catch(e){return d}}
  function lsSet(k,v){try{localStorage.setItem(k,v)}catch(e){}}

  /* ---------- טעינת נתוני התוספות והנוסחים שנבחרו ---------- */
  function tosItems(){return (window.__TOS&&window.__TOS.items)||[]}
  function tosHeb(it){return it.hnHeb||it.hn}
  function pageIdxOf(daf){for(var i=0;i<D.pages.length;i++)if(D.pages[i].daf===daf)return i;return -1}

  /* ---------- עוגן הסימן בטקסט (אותו אלגוריתם כמו באתר: טקסט הקשר ומספר מופע) ---------- */
  var NIKD=/[֑-ׇ]/, LET=/[א-ת]/, SEP=/[\s\-־]/;
  function normCtx(s){var o='',c;for(var i=0;i<s.length;i++){c=s[i];
      if(NIKD.test(c))continue;
      if(LET.test(c))o+=c;
      else if(SEP.test(c)){if(o.length&&o[o.length-1]!==' ')o+=' '}}
    return o.trim()}
  function buildIndex(rows){
    var s='',map=[];
    rows.forEach(function(r){var m=r[1].querySelector(':scope > .main');if(!m)return;
      var w=document.createTreeWalker(m,NodeFilter.SHOW_TEXT,{acceptNode:function(n){
        return n.parentElement&&n.parentElement.closest('.tm,.mlabel,.srcb')?NodeFilter.FILTER_REJECT:NodeFilter.FILTER_ACCEPT}});
      var n,lastP=null;
      while((n=w.nextNode())){
        var p=n.parentElement.closest('p');
        if(p!==lastP&&s.length&&s[s.length-1]!==' '){s+=' ';map.push(null)}
        lastP=p;
        var t=n.nodeValue;
        for(var i=0;i<t.length;i++){var c=t[i];
          if(NIKD.test(c))continue;
          if(LET.test(c)){s+=c;map.push([n,i+1])}
          else if(SEP.test(c)){if(s.length&&s[s.length-1]!==' '){s+=' ';map.push([n,i+1])}}}}
      if(s.length&&s[s.length-1]!==' '){s+=' ';map.push(null)}});
    return {s:s,map:map}}
  function findAt(idx,ctx,occ){
    var k=-1,from=0,seen=0;
    while(true){k=idx.s.indexOf(ctx,from);if(k<0)return null;
      var before=k===0||idx.s[k-1]===' ',after=k+ctx.length>=idx.s.length||idx.s[k+ctx.length]===' ';
      if(before&&after){seen++;if(seen===occ){
          var e=k+ctx.length-1;
          while(e>=k&&!idx.map[e])e--;
          return idx.map[e]||null}}
      from=k+1}}
  function lineOf(ref){var m=/\.(\d+)$/.exec(ref||'');return m?+m[1]:0}

  /* זיהוי מילה בודדת בשורה האחרונה: כמו lastLineIsLone של האתר, אך לפי מרכז האות ולא קצה עליון
     (קטע בגופן קטן באמצע שורה נתן הפרש של קצה עליון ואותה שורה זוהתה בטעות כשורה נפרדת) */
  function loneStrict(p){
    var w=document.createTreeWalker(p,NodeFilter.SHOW_TEXT),nodes=[],nd;
    while((nd=w.nextNode()))if(nd.nodeValue.trim())nodes.push(nd);
    if(!nodes.length)return false;
    var full=nodes.map(function(x){return x.nodeValue}).join(''),m=[],re=/\S+/g,mm;
    while((mm=re.exec(full)))m.push(mm.index);
    if(m.length<3)return false;
    var r=document.createRange();
    function cy(i){var off=m[i];
      for(var k=0;k<nodes.length;k++){var L=nodes[k].nodeValue.length;
        if(off<L){r.setStart(nodes[k],off);r.setEnd(nodes[k],Math.min(off+1,L));
          var b=r.getBoundingClientRect();return b.height?(b.top+b.bottom)/2:null}
        off-=L}
      return null}
    var a=cy(m.length-1),b=cy(m.length-2);
    return a!==null&&b!==null&&Math.abs(a-b)>6}

  /* רווח קשיח בין שתי המילים האחרונות של הפסקה: השורה האחרונה תכיל שתי מילים לפחות */
  function glueLastWords(el){
    var w=document.createTreeWalker(el,NodeFilter.SHOW_TEXT),ns=[],n;
    while((n=w.nextNode()))ns.push(n);
    var seenWord=false;
    for(var i=ns.length-1;i>=0;i--){
      var v=ns[i].nodeValue;
      for(var k=v.length-1;k>=0;k--){
        var c=v[k];
        if(/\s/.test(c)){
          if(c===' '){seenWord=true;continue}
          if(seenWord){ns[i].nodeValue=v.slice(0,k)+'\u00A0'+v.slice(k+1);return true}
        }else if(c!=='\u2060')seenWord=true}}
    return false}

  /* ---------- מנוע ההדפסה ---------- */
  async function runPrint(){
    var R={warn:[],pages:[],notes:0,placed:0,moved:[],issues:[],t:{}};var T0=performance.now();function TM(k){R.t[k]=Math.round(performance.now()-T0)}
    window.__PRN={state:'running',report:R};
    function W(m){R.warn.push(m);try{console.warn('[print] '+m)}catch(e){}}
    var prof=await (await fetch('print-profiles/'+(QS.get('profile')||'a4')+'.json',{cache:'no-store'})).json();
    (function(){var P=prof,n=P.notes,h=P.header,ft=P.footer;
      var c=document.createElement('style');
      c.textContent=
        '#flow,#flow .row,#prnsq,#prnsq .row{--measure:'+P.measure+'mm;--rail:'+P.rail+'mm}'+
        '#flow,#prnsq{width:'+(P.rail+P.measure)+'mm;font-size:calc('+P.measure+'mm / '+P.body.fsFromMeasure+');line-height:'+P.body.linePt+'pt;--lhpx:'+P.body.linePt+'pt;--fs:calc('+P.measure+'mm / '+P.body.fsFromMeasure+')}'+
        '#flow .row,#prnsq .row,.ptx .row{grid-template-columns:'+P.rail+'mm '+P.measure+'mm}'+
        '.pcol .ptx.flow{position:relative;display:block;width:100%;min-height:0;overflow:hidden;padding:0;margin:0;columns:auto;column-count:1;column-width:auto;column-gap:0;column-rule:0;'+
          'background:none;direction:rtl;--measure:'+P.measure+'mm;--rail:'+P.rail+'mm;--gut:0;--lhpx:'+P.body.linePt+'pt;--fs:calc('+P.measure+'mm / '+P.body.fsFromMeasure+');'+
          'font-size:calc('+P.measure+'mm / '+P.body.fsFromMeasure+');line-height:'+P.body.linePt+'pt}'+
        '#flow .row.pcont .main{font-size:'+P.continuationPt+'pt}'+
        '.phd{font-family:'+h.family+',serif;font-weight:'+h.weight+';font-size:'+h.pt+'pt}'+
        '.pfn{width:'+P.measure+'mm;font-family:'+n.family+',serif;font-weight:'+n.weight+';font-size:'+n.pt+'pt;line-height:'+n.linePt+'pt;letter-spacing:'+n.letterSpacingPt+'pt;column-count:'+n.cols+';column-gap:'+n.colGapMm+'mm}'+
        '#prnmeas{width:'+P.measure+'mm}'+
        '.pfn .fdh{font-weight:'+n.dhWeight+'}'+
        /* סימן ההפנייה אינו תופס רוחב ואינו נוגע בגובה השורה: תיבה ברוחב אפס, מורמת אל הרווח שבין השורות (השורות חושבו במדויק) */
        'sup.tm{display:inline-block;position:relative;width:0;height:0;overflow:visible;direction:ltr;white-space:nowrap;font-family:'+n.family+',serif;font-weight:'+n.markWeight+';font-size:'+n.markScale+'em;line-height:0;vertical-align:baseline;top:-'+n.markRise+'em;letter-spacing:0;margin:0;padding:0}'+
        '.pfn .fnum{font-size:'+n.numberScale+'em;line-height:0;position:relative;top:-'+n.numberRise+'em;vertical-align:baseline;margin-left:.18em;font-weight:'+n.numberWeight+';text-decoration:none}'+
        '.pfn .fnn{margin:'+n.betweenMm+'mm 0 0}.pfn .fnn:first-child{margin-top:0}'+
        '.pg .pfn .fnm{font-size:'+n.nameScale+'em;color:'+n.nameColor+'!important;font-weight:'+n.weight+'}'+
        '.pfn .fnp{font-size:'+(n.pt-n.parenLessPt)+'pt}'+
        '.pg a.tml{position:absolute;display:block;text-decoration:none;color:transparent!important}'+
        '.pg a.fnl,.pg a.dml{text-decoration:none;color:inherit}'+
        '.pnum{font-family:Vilna,serif;font-weight:400;font-size:'+ft.pt+'pt}'+
        '.psite{bottom:6mm;font-family:Vilna,serif;font-size:'+ft.sitePt+'pt}'+
        '.psite .qr{width:'+ft.qrMm+'mm;height:'+ft.qrMm+'mm}';
      document.head.appendChild(c)})();
    TM('profile');
    var withTos=QS.get('tos')==='1'&&tosItems().length>0;
    var duplex=QS.get('duplex')==='1';
    var N=prof.notes, PG=prof.page, MG=prof.margins;
    var A_mm=PG.h-MG.top-MG.bottom;                       /* גובה הנטו של טור */
    var A=A_mm*MM;
    /* ---- טווח ---- */
    var fi=0,ti=D.pages.length-1;
    if(QS.get('all')!=='1'){
      var from=QS.get('from'),to=QS.get('to')||from;
      if(from){fi=pageIdxOf(from);if(fi<0)throw new Error('דף לא נמצא: '+from)}
      if(to){ti=pageIdxOf(to);if(ti<0)throw new Error('דף לא נמצא: '+to)}
      if(ti<fi)throw new Error('סוף הטווח לפני תחילתו')}
    /* ---- נוסחי התוספות שנבחרו (נקודת הקליטה) ---- */
    var PUBN={};
    if(withTos){
      try{
        var r=await fetch(SUGGEST_API+'/tos?slug='+encodeURIComponent(SLUG),{cache:'no-store'});
        var j=await r.json();
        if(j&&j.ok&&j.pub)Object.keys(j.pub).forEach(function(n){if(j.pub[n]&&j.pub[n].t)PUBN[n]=j.pub[n].t});
      }catch(e){W('לא נמשכו הנוסחים שנבחרו מנקודת הקליטה: מודפס נוסח ברירת המחדל')}}
    TM('picks');
    /* ---- יחידות ---- */
    var recs=[],groups=[];
    var firstUnit=null;
    for(var pi=fi;pi<=ti;pi++){var p=D.pages[pi];if(!p.units.length)continue;var first=true;var g0=recs.length;
      for(var k=0;k<p.units.length;k++){var u=p.units[k];
        if(!firstUnit)firstUnit={u:u,p:p};
        recs.push({u:u,pi:pi,daf:p.daf,perek:p.perek||'',perekName:p.perekName||'',kind:u.k,
          html:unitHTML(u,first?p.daf:null,first?pi:null)});
        first=false}
      groups.push([g0,recs.length])}
    if(!recs.length)throw new Error('אין בטווח טקסט');
    TM('units');
    /* פתיחת הטווח באמצע פרק: שורה קטנה "המשך פרק", כדי שהדף לא ייפתח יתום */
    if(firstUnit&&firstUnit.u.k!=='perek-range'&&firstUnit.u.k!=='perek-start'&&firstUnit.p.perek){
      var contLine='<div class="row pcont"><div class="rail"></div><div class="main">המשך '+ge(firstUnit.p.perek)+'</div></div>';
      recs.unshift({u:null,pi:recs[0].pi,daf:recs[0].daf,perek:firstUnit.p.perek,perekName:firstUnit.p.perekName||'',kind:'cont',html:contLine});
      groups.forEach(function(g){g[0]++;g[1]++});groups[0][0]=0}
    /* מקבצים לנתחים של כמה מאות יחידות לפי גבולות עמוד: פריסה של מסכת שלמה בגוש אחד נמדדה בדקות */
    var chunks=[],cur0=0;
    groups.forEach(function(g){if(g[1]-cur0>=150){chunks.push([cur0,g[1]]);cur0=g[1]}});
    if(cur0<recs.length)chunks.push([cur0,recs.length]);
    /* אלמנט הסרגל נוצר כאן מחדש (id=flow, כדי ש-fitAnchors של האתר ימדוד אותו) */
    var f=document.createElement('div');f.id='flow';f.className='flow';
    var oldF=document.getElementById('flow');
    if(oldF)oldF.replaceWith(f);else document.body.insertBefore(f,document.body.firstChild);
    document.body.classList.add('prn');document.documentElement.classList.add('prn');
    await Promise.all(FAM.map(function(x){return document.fonts.load(x[1]+' 20px '+x[0],'אבגדה')}));
    TM('fontsload');
    var items=[],L=[],odd={},fixedLone=0,fixedGlue=0,Ybase=0,sqMs=0;
    var inRange={};for(var q=fi;q<=ti;q++)inRange[D.pages[q].daf]=q;
    if(withTos)tosItems().forEach(function(it){if(inRange[it.daf]!==undefined)items.push(it)});
    R.notes=items.length;
    /* סרגל קטן למדידת איחוי שורה יתומה (פריסה של פסקה אחת בלבד) */
    var sq=document.createElement('div');sq.className='flow';sq.id='prnsq';
    sq.style.cssText='position:fixed;left:0;top:0;visibility:hidden;pointer-events:none;height:auto;overflow:hidden;columns:auto;column-count:1;padding:0;z-index:-1';
    sq.innerHTML='<div class="row"><div class="rail"></div><div class="main"><p></p></div></div>';
    document.body.appendChild(sq);
    var GM=sq.querySelector('.main'),GP=sq.querySelector('p');
    for(var ci0=0;ci0<chunks.length;ci0++){
      var c0=chunks[ci0],crecs=recs.slice(c0[0],c0[1]);
      var curF=document.getElementById('flow');
      if(curF!==f){if(curF)curF.remove();document.body.insertBefore(f,document.body.firstChild)}
      f.innerHTML=crecs.map(function(x){return x.html}).join('');
      var els=[].slice.call(f.children);
      if(els.length!==crecs.length)throw new Error('מספר השורות אינו תואם: '+els.length+' מול '+crecs.length);
      crecs.forEach(function(x,i){x.el=els[i];x.el.removeAttribute('id')});
      /* סימוני התוספות של דפי הנתח */
      if(withTos){
        var byUnitEls={};crecs.forEach(function(x){if(x.u)byUnitEls[x.u.id]=x.el});
        var inChunk={};crecs.forEach(function(x){inChunk[x.daf]=x.pi});
        var byDaf={};items.forEach(function(it){if(inChunk[it.daf]!==undefined)(byDaf[it.daf]=byDaf[it.daf]||[]).push(it)});
        Object.keys(byDaf).forEach(function(daf){
          var rows=[];D.pages[inChunk[daf]].units.forEach(function(u){var e=byUnitEls[u.id];if(e)rows.push([u,e])});
          if(!rows.length)return;
          byDaf[daf].slice().sort(function(a,b){return b.n-a.n}).forEach(function(it){
            var idx=buildIndex(rows),ctx=normCtx(it.t||''),hit=null;
            if(ctx)hit=findAt(idx,ctx,it.occ||1);
            var mk=document.createElement('sup');mk.className='tm';mk.setAttribute('data-n',it.n);
            mk.textContent=prof.notes.numbering==='digits'?String(it.n):tosHeb(it);
            mk.id='tm-'+it.n;
            if(hit){
              /* אחרי הניקוד של האות האחרונה, כדי שהסימן לא יפריד אות מניקודה */
              var hv=hit[0].nodeValue,ho=hit[1];while(ho<hv.length&&NIKD.test(hv[ho]))ho++;
              var rg=document.createRange();rg.setStart(hit[0],ho);rg.collapse(true);rg.insertNode(mk);
              mk.parentNode.insertBefore(document.createTextNode('\u2060'),mk);   /* צמד-מילה: הסימן לא יישבר מן המילה שלו */
              R.placed++;return}
            /* עוגן שלא נמצא: סוף שורת הגמרא הקרובה, ומדווח (לעולם לא נעלם בשקט) */
            var best=null,fst=null;
            rows.forEach(function(x){var ln=lineOf(x[0].ref);if(!ln)return;if(!fst)fst=x;if(ln<=it.line)best=x});
            var tgt=best||fst||rows[rows.length-1];
            var m=tgt[1].querySelector(':scope > .main');
            if(!m){W('עוגן תוספות '+tosHeb(it)+' לא נמצא ואין שורה להצמדה');return}
            var ps=m.querySelectorAll(':scope > p'),host=ps.length?ps[ps.length-1]:m;
            host.appendChild(document.createTextNode('\u2060'));host.appendChild(mk);R.placed++;R.moved.push(tosHeb(it))})})}
      await document.fonts.ready;
      /* קוד האתר עשוי להחליף את אלמנט הסרגל בזמן ההמתנה: מחזירים את שלנו (וכל המדידות אחריו) */
      var curF2=document.getElementById('flow');
      if(curF2!==f||!f.isConnected){
        R.reattach=(R.reattach||0)+1;
        if(curF2&&curF2!==f)curF2.remove();
        if(!f.isConnected)document.body.insertBefore(f,document.body.firstChild)}
      if(ci0===0){
        var missingFont=FAM.filter(function(x){return !document.fonts.check(x[1]+' 20px '+x[0],'אבגדה')});
        if(missingFont.length)W('גופן שלא נטען: '+missingFont.map(function(x){return x[0]+' '+x[1]}).join(', '))}
      if(typeof setDafW==='function')setDafW();
      if(typeof fitAnchors==='function')fitAnchors();
      if(typeof ltFit==='function')ltFit(f);
      /* איחוי שורה יתומה (כלל עימוד 4): בדיקה במקום, וניסיונות בסרגל; רק התוצאה נכתבת לפסקה */
      var tSq=performance.now();
      var ps0=[].slice.call(f.querySelectorAll('.main p')).filter(function(p){return p.textContent.trim().length>=12&&loneStrict(p)});
      var todo=[];
      ps0.forEach(function(p){
        GM.className=p.parentElement.className;GP.className=p.className;GP.style.wordSpacing='';GP.style.letterSpacing='';
        GP.innerHTML=p.innerHTML;
        if(!loneStrict(GP))return;
        var h0=GP.offsetHeight;
        for(var s2=0;s2<STEPS.length;s2++){
          GP.style.wordSpacing=STEPS[s2][0]?STEPS[s2][0]+'em':'';GP.style.letterSpacing=STEPS[s2][1]?STEPS[s2][1]+'em':'';
          if(GP.offsetHeight<h0){todo.push([p,STEPS[s2],false]);return}}
        /* הדחיסה אינה מספיקה: מורידים עוד מילה אל השורה האחרונה (רווח קשיח לפני המילה האחרונה) */
        GP.style.wordSpacing='';GP.style.letterSpacing='';GP.innerHTML=p.innerHTML;
        var gn=0,gok=false;
        while(gn<3&&glueLastWords(GP)){gn++;if(!loneStrict(GP)&&GP.offsetHeight<=h0){gok=true;break}}
        if(gok)todo.push([p,[0,0],gn])});
      todo.forEach(function(t){
        if(t[1][0]||t[1][1]){t[0].style.wordSpacing=t[1][0]?t[1][0]+'em':'';t[0].style.letterSpacing=t[1][1]?t[1][1]+'em':'';t[0].dataset.sq='1'}
        if(t[2]){for(var g2=0;g2<t[2];g2++)glueLastWords(t[0]);t[0].dataset.glue=String(t[2]);fixedGlue++}
        fixedLone++});
      sqMs+=performance.now()-tSq;
      if(todo.length&&typeof fitAnchors==='function')fitAnchors();
      /* שער: מילה בודדת שנותרה אחרי הדחיסה והרווח הקשיח נרשמת בלוח התקלות (לעולם לא בשקט) */
      [].slice.call(f.querySelectorAll('.main p')).forEach(function(p){
        if(p.textContent.trim().length>=12&&loneStrict(p)){
          var rw=p.closest('.row'),rc2=null;for(var q2=0;q2<crecs.length;q2++)if(crecs[q2].el===rw){rc2=crecs[q2];break}
          R.issues.push({type:'מילה בודדת בשורה אחרונה',daf:rc2?rc2.daf:'',unit:rc2&&rc2.u&&rc2.u.id,detail:p.textContent.trim().slice(-30)})}});
      R.semicolons=(R.semicolons||0)+(f.textContent.split(';').length-1);
      /* ---- מדידת שורות הנתח ---- */
      var fr=f.getBoundingClientRect(),Lc0=L.length;
      crecs.forEach(function(x,i){
        var ri=c0[0]+i;
        var row=x.el,main=row.querySelector(':scope > .main'),rail=row.querySelector(':scope > .rail');
        var rr=row.getBoundingClientRect();
        if(main&&main.scrollWidth>main.clientWidth+2)R.issues.push({type:'טקסט חורג מרוחב הטור',daf:x.daf,unit:x.u&&x.u.id,detail:'רוחב '+main.scrollWidth+' מול '+main.clientWidth});
        var blocks=main?[].slice.call(main.querySelectorAll(':scope > p')):[];
        if(main&&!blocks.length)blocks=[main];
        var railBottom=rail?rail.getBoundingClientRect().bottom-fr.top:0;
        var rowFirst=L.length;
        blocks.forEach(function(b,bi){
          var cs=getComputedStyle(b),br=b.getBoundingClientRect();
          var lh=parseFloat(cs.lineHeight);if(!lh||isNaN(lh))lh=11*PT;
          var pt=parseFloat(cs.paddingTop)||0,pb=parseFloat(cs.paddingBottom)||0;
          var bt=parseFloat(cs.borderTopWidth)||0,bb=parseFloat(cs.borderBottomWidth)||0;
          var h=br.height-pt-pb-bt-bb;
          if(h<1&&!b.textContent.trim()){return}                /* פסקה ריקה אינה שורה */
          if(h<1&&!b.isConnected)throw new Error('אלמנט הסרגל נותק באמצע המדידה');
          var n=Math.max(1,Math.round(h/lh));
          if(Math.abs(h/lh-n)>0.2){var key=x.kind+':'+cs.fontSize;
            if(!odd[key]){odd[key]=1;W('גובה פסקה אינו כפולה של גובה השורה ('+x.kind+'): '+(h/lh).toFixed(2))}}
          var top=Ybase+br.top-fr.top+pt+bt;
          for(var k=0;k<n;k++){
            L.push({ri:ri,kind:x.kind,block:bi,k:k,n:n,y0:top+k*lh,y1:top+(k+1)*lh,
                    daf:x.daf,perek:x.perek,perekName:x.perekName,notes:[],first:false,last:false})}});
        if(L.length>rowFirst){
          L[rowFirst].first=true;L[L.length-1].last=true;
          var lastL=L[L.length-1];
          lastL.y1=Math.max(lastL.y1,Ybase+railBottom,Ybase+rr.bottom-fr.top)}
        x.gtop=Ybase+rr.top-fr.top});
      /* כל סימן שייך לשורה שבה הוא יושב */
      [].slice.call(f.querySelectorAll('sup.tm')).forEach(function(s){
        var rg=document.createRange();rg.selectNode(s);var rcs=rg.getClientRects();
        var yy=rcs.length?Ybase+(rcs[0].top+rcs[0].bottom)/2-fr.top:null;
        var ri=-1;for(var i=0;i<crecs.length;i++)if(crecs[i].el.contains(s)){ri=c0[0]+i;break}
        var n=+s.getAttribute('data-n'),best=-1,bd=1e9;
        for(var j=Lc0;j<L.length;j++){if(L[j].ri!==ri)continue;
          var d=yy===null?0:(yy<L[j].y0?L[j].y0-yy:(yy>L[j].y1?yy-L[j].y1:0));
          if(d<bd){bd=d;best=j}}
        if(best<0){W('סימן תוספות '+n+' ללא שורה');return}
        L[best].notes.push(n)});
      crecs.forEach(function(x){x.html2=x.el.outerHTML;x.el=null});
      Ybase+=fr.height;
      f.innerHTML=''}
    sq.remove();
    R.loneFixed=fixedLone;R.glued=fixedGlue;R.msSqueeze=Math.round(sqMs);R.chunks=chunks.length;
    if(withTos&&R.placed!==items.length)W('ספירת התוספות אינה שלמה: '+R.placed+' מתוך '+items.length);
    if(!L.length)throw new Error('לא נמדדו שורות');
    TM('measure');

    /* ---- הערות שוליים: בניית HTML ומדידת גובה ---- */
    var byN={};items.forEach(function(it){byN[it.n]=it});
    /* שמות המפרשים בתוך ההערה: גופן קטן יותר ואפור. הרשימה סגורה (לא כל "ר'" הוא מפרש: תנאים אינם נכללים) */
    var NAMES=new RegExp('(?<![א-ת"\'׳])((?:[ולבכמשה]{0,3})(?:תוס[\'׳]\\s+)?(?:רש"י|ר"ת|ר"י|ר"מ|ר"ח|רי"ף|רמב"ם|רמב"ן|רשב"א|ריטב"א|רא"ש|רשב"ם|מהר"י|מהר"ם|רבנו תם|רבינו [א-ת]+|ה"ר [א-ת]+|ר[\'׳] (?:נתנאל|ברוך|יהודה מקורבי"ל|יצחק|שמשון|אליעזר|יעקב|פרץ)):?)(?![א-ת"])','g');
    /* ציון מקור של פסוק (ספר פרק:פסוק) בסוגריים נמחק: ההערות מקוצרות. מקורות גמרא נשארים */
    var VERSE=/\s*\((?:פסוק\s+)?(?:בראשית|שמות|ויקרא|במדבר|דברים|יהושע|שופטים|שמואל(?: [אב])?|מלכים(?: [אב])?|ישעיה|ירמיה|יחזקאל|הושע|יואל|עמוס|עובדיה|יונה|מיכה|נחום|חבקוק|צפניה|חגי|זכריה|מלאכי|תהלים|משלי|איוב|שיר השירים|רות|איכה|קהלת|אסתר|דניאל|עזרא|נחמיה|דברי הימים(?: [אב])?)\s+[א-ת]{1,3}\s*[:.,]\s*[א-ת]{1,3}(?:\s*[-–]\s*[א-ת]{1,3})?\)/g;
    function noteText(t){
      t=String(t).replace(/;/g,'.').replace(VERSE,'');   /* אין נקודה-פסיק: נקודה בלבד */
      var o='',last=0,m;NAMES.lastIndex=0;
      /* סוגריים עגולות: קטנות ב-2 נקודות מגופן ההערה */
      function paren(x){return ge(x).replace(/\([^()]*\)/g,function(q){return '<span class="fnp">'+q+'</span>'})}
      while((m=NAMES.exec(t))){o+=paren(t.slice(last,m.index))+'<span class="fnm">'+ge(m[1])+'</span>';last=m.index+m[0].length}
      return o+paren(t.slice(last))}
    function noteHTML(n){
      var it=byN[n];var t=PUBN[n]||it.sum||'';
      var num=prof.notes.numbering==='digits'?String(it.n):tosHeb(it);
      return '<div class="fnn" id="fn-'+it.n+'"><a class="fnl" href="#tm-'+it.n+'"><span class="fnum">'+ge(num)+'</span></a> <span class="fdh">'+noteText(it.dh)+'</span> - '+noteText(t)+'</div>'}
    var meas=document.createElement('div');meas.id='prnmeas';document.body.appendChild(meas);
    var fcache={};
    function fnBox(ids){
      var k=ids.join(',');
      if(fcache[k])return fcache[k];
      var o={html:'',h:0};
      if(ids.length){
        o.html=ids.map(noteHTML).join('');
        meas.className='pfn'+(ids.length<2?' one':'');meas.innerHTML=o.html;
        o.h=meas.getBoundingClientRect().height;
        o.one=ids.length<2}
      fcache[k]=o;return o}
    var GAP=N.gapAboveMm*MM;
    function noteIds(a,b){var s=[];for(var i=a;i<b;i++)for(var t=0;t<L[i].notes.length;t++)s.push(L[i].notes[t]);
      return s.sort(function(x,y){return x-y})}

    /* ---- כללי השבירה ---- */
    function isForce(i){var l=L[i];
      return l.first&&(l.kind==='perek-range'||(l.kind==='perek-start'&&!(i>0&&L[i-1].kind==='perek-range')))}
    function canBreak(i){
      if(i<=0||i>=L.length)return true;
      var a=L[i-1],b=L[i];
      if(a.ri===b.ri&&a.block===b.block){                  /* בתוך פסקה: שתי שורות לפחות מכל צד */
        return b.k>=prof.widowOrphan&&(b.n-b.k)>=prof.widowOrphan}
      if(b.kind==='hadran')return false;                    /* הדרן אינו נפתח טור */
      /* כותרת אינה נפרדת מן התוכן שאחריה: שתי שורות תוכן לפחות אחריה באותו טור */
      var c=0,j=i-1;
      while(j>=0&&!HEADS[L[j].kind]){c++;j--;if(c>=prof.keepAfterHeading)break}
      if(j>=0&&HEADS[L[j].kind]&&c<prof.keepAfterHeading)return false;
      /* בתוך תוכן: כבר בדקנו; בין יחידות מותר */
      return true}

    /* ---- מילוי טורים ---- */
    var cols=[],i=0;
    while(i<L.length){
      var y0=L[i].y0,best=-1,j=i,ids=[],F=0,fbox=null;
      while(j<L.length){
        if(j>i&&isForce(j))break;
        var nids=ids.concat(L[j].notes);
        var nf=nids.length?fnBox(nids.slice().sort(function(x,y){return x-y})):null;
        var fh=nf?nf.h+GAP:0;
        var th=L[j].y1-y0;
        if(th+fh>A+0.5)break;
        ids=nids;j++;
        if(j>=L.length||(canBreak(j)&&!isForce(j)))best=j;
        else if(j<L.length&&isForce(j))best=j}
      if(best<=i){                                          /* אין שבירה חוקית: מה שנכנס, ולכל הפחות שורה */
        best=Math.max(j,i+1);
        if(best<L.length)R.issues.push({type:'שבירה לא חוקית',daf:L[best].daf,detail:'לא נמצאה נקודת שבירה תקינה בטור'})}
      var cn=noteIds(i,best);
      cols.push({s:i,e:best,notes:cn});
      i=best}

    /* ---- בדיקות אחרי העימוד (לוח התקלות): כותרת מנותקת, שורה יתומה או אלמנה, הערה שנפרדה מסימנה ---- */
    cols.forEach(function(c,ci){
      var a=L[c.s],b=L[c.e-1],pg=Math.floor(ci/prof.cols)+1;
      function iss(t,l,d){R.issues.push({type:t,page:pg,daf:l.daf,unit:recs[l.ri]&&recs[l.ri].u&&recs[l.ri].u.id,detail:d||''})}
      if(HEADS[b.kind]&&b.kind!=='hatz'&&c.e<L.length)iss('כותרת בתחתית טור',b);
      if(c.s>0&&a.ri===L[c.s-1].ri&&a.block===L[c.s-1].block&&a.k<prof.widowOrphan)iss('שורה אלמנה בראש טור',a);
      if(c.e<L.length&&L[c.e].ri===b.ri&&L[c.e].block===b.block&&(b.n-b.k-1)<prof.widowOrphan)iss('שורה יתומה בסוף טור',b);
      var inCol={};c.notes.forEach(function(n){inCol[n]=1});
      for(var i3=c.s;i3<c.e;i3++)L[i3].notes.forEach(function(n){if(!inCol[n])iss('הערה נפרדה מסימנה',L[i3],String(n))})});
    TM('paginate');
    /* ---- בניית העמודים ---- */
    var out=document.createElement('div');out.id='prnout';
    var tpl=document.createElement('template');
    var nPages=Math.ceil(cols.length/prof.cols);
    var mname=D.masechet;
    var lastPerek=null;
    function dafSpan(a,b){return a===b?a:(a+' - '+b)}
    for(var pgi=0;pgi<nPages;pgi++){
      var cs2=cols.slice(pgi*prof.cols,pgi*prof.cols+prof.cols);
      var firstLine=L[cs2[0].s],lastLine=L[cs2[cs2.length-1].e-1];
      var pe=firstLine.perek,pn=firstLine.perekName;
      var pgEl=document.createElement('section');pgEl.className='pg';
      var dx=0;if(duplex){dx=(pgi%2===0?-1:1)*prof.duplexInnerExtra}
      var pageInfo={n:pgi+1,daf0:firstLine.daf,daf1:lastLine.daf,perek:pe,notes:[],cols:[]};
      var hd='<div class="phd" style="left:'+(MG.left+dx)+'mm;right:'+(MG.right-dx)+'mm;top:'+prof.header.topMm+'mm">'+
        '<span>'+ge(pn)+'</span><span>'+ge(pe)+'</span><span>'+ge(mname)+'</span><span>'+ge(dafSpan(firstLine.daf,lastLine.daf))+'</span></div>';
      var body='';
      cs2.forEach(function(c,ci){
        var ln=L[c.s],le=L[c.e-1];
        var yS=ln.y0-1,yE=le.y1;
        /* ci 0 = הטור הימני: מכולה של 80 מ"מ שימינה עד שולי הימין */
        /* כל המרווח הפנוי נמצא בין שני הטורים; הטור הימני מתחיל בשולי הימין, והשמאלי בשולי השמאל */
        var boxLeft=ci===0?(PG.w-MG.right-(prof.rail+prof.measure)):MG.left;
        boxLeft+=dx;
        var rowsHtml='';
        for(var ri=ln.ri;ri<=le.ri;ri++){
          var rc=recs[ri];
          tpl.innerHTML=rc.html2;
          var cl=tpl.content.firstElementChild;
          cl.style.position='absolute';cl.style.top=(rc.gtop-yS)+'px';cl.style.right='0';cl.style.width=(prof.rail+prof.measure)+'mm';
          rowsHtml+=cl.outerHTML}
        var fb=c.notes.length?fnBox(c.notes):null;
        body+='<div class="pcol" style="left:'+boxLeft+'mm;top:'+MG.top+'mm;width:'+(prof.rail+prof.measure)+'mm;height:'+A_mm+'mm">'+
          '<div class="ptx flow" style="height:'+(yE-yS)+'px">'+rowsHtml+'</div>'+
          (fb?'<div class="pfnw" style="width:'+prof.measure+'mm"><div class="pfn'+(fb.one?' one':'')+'">'+fb.html+'</div></div>':'')+'</div>';
        c.notes.forEach(function(n){pageInfo.notes.push(n)});
        pageInfo.cols.push({lines:c.e-c.s,textMm:+((yE-yS)/MM).toFixed(1),notes:c.notes.length,noteMm:fb?+(fb.h/MM).toFixed(1):0})});
      var foot='<div class="pnum" style="bottom:'+prof.footer.numberFromBottomMm+'mm">'+(pgi+1)+'</div>'+
        '<div class="psite" style="left:'+(MG.left+dx)+'mm">'+(prof.footer.pageQr?'<span class="qr"></span>':'')+'<span class="st">'+ge(prof.footer.siteText)+'</span></div>';
      pgEl.innerHTML=hd+body+foot;
      pgEl.setAttribute('data-daf',firstLine.daf);
      out.appendChild(pgEl);
      R.pages.push(pageInfo)}
    /* ---- מסכת שלמה: שער, עמוד 2 הקבוע ותוכן עניינים (לפני גוף המסכת) ---- */
    var p2frame=null;
    if(QS.get('all')==='1'){
      var toc=[];
      cols.forEach(function(c,ci){for(var i2=c.s;i2<c.e;i2++){var l=L[i2];
        if(l.kind==='perek-start'&&l.first)toc.push({perek:l.perek,name:l.perekName,page:Math.floor(ci/prof.cols)+1,daf:l.daf})}});
      var first=out.firstChild;
      var cov=document.createElement('section');cov.className='pg cover';
      cov.innerHTML='<div class="cv"><div class="cv1">לאוקמי גירסא</div><div class="cv2">מסכת '+ge(mname)+'</div>'+
        '<div class="cv3">מכון לאוקמי גירסא</div><div class="cv4">leokmei.com</div></div>';
      out.insertBefore(cov,first);
      var p2=document.createElement('section');p2.className='pg p2';
      var left='<div style="font-size:15px;line-height:1.5">©</div><div>כל הזכויות שמורות</div><div style="margin-top:6px">כתיבה ועריכה:</div>'+
        '<div style="font-family:\'Vilna Bold\',serif">מ.ח. מיכאל פלעג שליט״א</div><div style="margin-top:6px;font-family:\'Vilna Bold\',serif">מכון לאוקמי גירסא</div>'+
        '<div dir="ltr" style="margin-top:2px">leokmei.com</div><div id="p2qr" style="width:62px;height:62px;margin-top:10px"></div>';
      var p2html=await (await fetch('print-page2.html',{cache:'no-store'})).text();
      p2html=p2html.replace('<!--LEFT-->',left);
      if(prof.footer.bookQr){
        try{await new Promise(function(ok,no){if(window.qrcode)return ok();var sc=document.createElement('script');sc.src='print-qr.js';sc.onload=ok;sc.onerror=no;document.head.appendChild(sc)});
          var qq=qrcode(0,'M');qq.addData(prof.footer.siteUrl+SLUG+'.html');qq.make();
          p2html=p2html.replace('<div id="p2qr" style="width:62px;height:62px;margin-top:10px"></div>','<div style="width:62px;height:62px;margin-top:10px">'+qq.createSvgTag({cellSize:1,margin:0,scalable:true})+'</div>')}catch(e){W('QR לעמוד 2: '+e.message)}}
      p2frame=document.createElement('iframe');p2frame.className='p2f';p2frame.setAttribute('srcdoc',p2html);
      p2.appendChild(p2frame);
      out.insertBefore(p2,first);
      var tc=document.createElement('section');tc.className='pg tocp';
      tc.innerHTML='<div class="toct">תוכן עניינים</div><div class="tocm">מסכת '+ge(mname)+'</div>'+
        toc.map(function(t){return '<div class="tocr"><span class="tn">'+ge(t.perek)+(t.name?' - '+ge(t.name):'')+'</span><span class="td"></span><span class="tp">'+t.page+'</span></div>'}).join('');
      out.insertBefore(tc,first);
      R.toc=toc}
    document.body.appendChild(out);
    if(p2frame){
      await new Promise(function(ok){if(p2frame.contentDocument&&p2frame.contentDocument.readyState==='complete'&&p2frame.contentDocument.body&&p2frame.contentDocument.body.children.length)return ok();p2frame.onload=function(){ok()};setTimeout(ok,15000)});
      try{await p2frame.contentDocument.fonts.ready}catch(e){}}
    f.style.display='none';meas.remove();
    /* ---- קישורים בקובץ: סימן הפנייה -> ההערה; ציון דף -> מקומו באתר ---- */
    try{
      var siteBase=prof.footer.siteUrl+SLUG+'.html#daf=';
      [].forEach.call(out.querySelectorAll('.pg'),function(pe){
        var pr=pe.getBoundingClientRect();
        [].forEach.call(pe.querySelectorAll('sup.tm'),function(s){
          var n=s.getAttribute('data-n');if(!n)return;
          var rg=document.createRange();rg.selectNodeContents(s);
          var r=rg.getBoundingClientRect();
          if(!r.width||!r.height)return;
          var a=document.createElement('a');a.className='tml';a.setAttribute('href','#fn-'+n);a.setAttribute('title',(byN[n]&&(PUBN[n]||byN[n].sum))||'');
          a.style.cssText='left:'+(r.left-pr.left-1)+'px;top:'+(r.top-pr.top-1)+'px;width:'+(r.width+2)+'px;height:'+(r.height+2)+'px';
          pe.appendChild(a)});
        [].forEach.call(pe.querySelectorAll('b.dafmark'),function(b){
          var d=b.getAttribute('data-daf');if(!d||b.parentNode.tagName==='A')return;
          var a=document.createElement('a');a.className='dml';a.setAttribute('href',siteBase+encodeURIComponent(d));
          b.parentNode.insertBefore(a,b);a.appendChild(b)})})
    }catch(e){W('קישורים בקובץ: '+e.message)}
    TM('pages');R.cols=cols.length;R.lines=L.length;
    /* קוד QR לכל עמוד: מוביל לדף שבו העמוד מתחיל. הספרייה נטענת רק בהדפסה (print-qr.js) */
    if(prof.footer.pageQr){
      try{
        await new Promise(function(ok,no){var sc=document.createElement('script');sc.src='print-qr.js';sc.onload=ok;sc.onerror=function(){no(new Error('print-qr.js'))};document.head.appendChild(sc)});
        var pgsQ=out.querySelectorAll('.pg');
        R.pages.forEach(function(pg,k){
          var q=qrcode(0,'M');q.addData(prof.footer.siteUrl+SLUG+'.html#daf='+encodeURIComponent(pg.daf0));q.make();
          var hold=pgsQ[k]&&pgsQ[k].querySelector('.qr');
          if(hold)hold.innerHTML=q.createSvgTag({cellSize:1,margin:0,scalable:true})})
      }catch(e){W('קוד QR לא נוצר: '+e.message)}}
    window.__prnSetQr=function(list){
      var pgs=out.querySelectorAll('.pg');
      list.forEach(function(svg,k){var q=pgs[k]&&pgs[k].querySelector('.qr');if(q&&svg)q.innerHTML=svg})};
    await document.fonts.ready;
    /* מדפיסים רק אחרי שהעמודים צוירו: הדפסה מיידית הניבה קובץ ריק (בלי טקסט) */
    await new Promise(function(r){requestAnimationFrame(function(){requestAnimationFrame(r)})});
    await new Promise(function(r){setTimeout(r,300)});
    try{R.fonts=Array.from(document.fonts).map(function(f){return f.family+" "+f.weight+" "+f.status})}catch(e){}
    window.__PRN.state='done';
    document.title='לאוקמי גירסא - '+mname+' - '+QS.get('from')+' - '+(QS.get('to')||QS.get('from'));
  }

  /* ---------- עיצוב מצב ההדפסה ---------- */
  if(ON){
    window.__PRN_ON=1;
    render=function(){};          /* build() אינו מצייר את התצוגה הרגילה */
    var st=document.createElement('style');
    st.textContent=
      '@page{size:210mm 297mm;margin:0}'+
      "@font-face{font-family:'Vilna';src:url(fonts/vilna-l.woff2) format('woff2'),url(fonts/vilna-l.otf);font-weight:300;font-display:block}"+
      'html.prn,html.prn body,body.prn{margin:0;padding:0;background:#fff;height:auto;overflow:visible;display:block;color:#000}'+
      'body:not(.prn) > *:not(#flow):not(script):not(style){display:none!important}'+
      'body.prn > *:not(#prnout):not(#prnmeas):not(#prnsq):not(#flow):not(script):not(style){display:none!important}'+
      'body #flow,body #prnsq{position:absolute;top:0;right:0;width:80mm;height:auto;min-height:0;overflow:visible;padding:0;margin:0;'+
        'columns:auto;column-count:1;column-width:auto;column-gap:0;column-rule:0;background:#fff;visibility:hidden;direction:rtl;'+
        '--measure:60mm;--rail:20mm;--gut:0;--fs:calc(60mm / 20.75);--lhpx:11pt;font-size:calc(60mm / 20.75);line-height:11pt;display:block}'+
      '#flow .row{grid-template-columns:20mm 60mm;break-inside:auto}'+
      '#flow .row.pcont .main{font-family:Vilna,serif;font-weight:400;font-size:6.5pt;line-height:11pt;text-align:right}'+
      '#prnout{position:static;direction:rtl}'+
      '.pg{position:relative;width:210mm;height:297mm;overflow:hidden;break-after:page;page-break-after:always;background:#fff;color:#000}'+
      '.pg:last-child{break-after:auto;page-break-after:auto}'+
      '.pg *{color:#000!important;text-shadow:none}'+
      '.pcol{position:absolute;direction:rtl}'+
      '.ptx{position:relative;overflow:hidden;width:100%}'+
      '.pfnw{position:absolute;left:0;bottom:0}'+
      '#prnmeas{position:absolute;left:0;top:0;visibility:hidden}'+
      '.pfn .fnn{break-inside:avoid;margin:0}'+
      '.pfn{direction:rtl;text-align:justify;hyphens:none;column-fill:balance}'+
      '.pfn.one{column-count:1!important}'+
      '.pnum{position:absolute;left:0;right:0;text-align:center;line-height:1}'+
      '.psite{position:absolute;display:flex;align-items:flex-end;gap:1.5mm;direction:ltr;line-height:1}'+
      '.phd{position:absolute;display:flex;justify-content:space-between;align-items:baseline;line-height:1;white-space:nowrap}'+
      '.psite .qr{display:block}.psite .qr svg{display:block;width:100%;height:100%}'+
      '.pg.cover .cv{position:absolute;left:0;right:0;top:78mm;text-align:center}'+
      '.cv1{font-family:Franknatan,Vilna,serif;font-size:46pt;line-height:1.1}'+
      '.cv2{font-family:Vilna,serif;font-weight:900;font-size:30pt;margin-top:10mm}'+
      '.cv3{font-family:Vilna,serif;font-weight:700;font-size:15pt;margin-top:60mm}'+
      '.cv4{font-family:Frank,serif;font-size:11pt;margin-top:3mm;direction:ltr}'+
      '.pg.p2{background:#fff}.p2f{position:absolute;right:0;top:0;width:512px;height:840px;border:0;transform-origin:top right;transform:scale(1.3363)}'+
      '.pg.tocp{padding:30mm 30mm 0 30mm;box-sizing:border-box}'+
      '.toct{font-family:Vilna,serif;font-weight:900;font-size:22pt;text-align:center}'+
      '.tocm{font-family:Vilna,serif;font-weight:700;font-size:13pt;text-align:center;margin:3mm 0 12mm}'+
      '.tocr{display:flex;align-items:baseline;gap:2mm;font-family:Vilna,serif;font-weight:500;font-size:12pt;line-height:1.9}'+
      '.tocr .td{flex:1;border-bottom:1px dotted #000;transform:translateY(-3px)}.tocr .tp{font-weight:900}'+
      '@media print{.pg{break-inside:avoid}}';
    document.head.appendChild(st);
    /* ההרצה אחרי טעינת כל הסקריפטים (הזנב הפרטי של המסכת, build ושאר הקוד של הדף): קודם לכן נתוני התוספות עדיין אינם קיימים,
       וקוד אחר של הדף עלול לשנות את גוף המסמך אחרי העימוד */
    var go=function(){setTimeout(function(){runPrint().catch(function(e){window.__PRN={state:'error',error:String(e&&e.message||e),report:(window.__PRN&&window.__PRN.report)||null};
      try{console.error('[print] '+e)}catch(x){}})},100)};
    if(document.readyState==='complete')go();else window.addEventListener('load',go);
  }

  /* ---------- חלון ההדפסה (הלומד) ---------- */
  var PRINT_API='https://leokmei-print.m7654301.workers.dev';
  if(!ON){
    function dafParts(key){var m=/^(.*?)([.:])$/.exec(key||'');return m?{base:m[1],amud:m[2]===':'?'ב':'א',mark:m[2]}:null}
    function textPages(){var o=[];D.pages.forEach(function(p,i){if(p.units&&p.units.length)o.push(i)});return o}
    function prnCss(){
      if(document.getElementById('prn-css'))return;
      var c=document.createElement('style');c.id='prn-css';
      c.textContent=
        '#prnd{position:fixed;inset:0;z-index:60;display:none;align-items:center;justify-content:center;background:rgba(10,20,40,.55);direction:rtl}'+
        '#prnd.open{display:flex}'+
        '#prnd .pbox{background:var(--paper,#fbf8f1);color:var(--ink,#1d1a16);width:min(30em,94vw);max-height:92vh;overflow:auto;border-radius:10px;border:1px solid #c9bfa6;box-shadow:0 10px 40px rgba(0,0,0,.35);padding:1em 1.2em 1.1em;font-family:inherit;font-size:16px;line-height:1.5}'+
        '#prnd h2{margin:0 0 .5em;font-size:1.15em;color:#7a5a14}'+
        '#prnd .pr{display:flex;flex-wrap:wrap;gap:.35em .9em;margin:.3em 0}'+
        '#prnd label{display:inline-flex;align-items:center;gap:.35em;cursor:pointer}'+
        '#prnd select{font:inherit;padding:.15em .4em;border:1px solid #c9bfa6;border-radius:5px;background:#fff;color:inherit;min-height:34px}'+
        '#prnd .pnote{color:#7a6f58;font-size:.88em;margin:.2em 0}'+
        '#prnd .pcnt{margin:.6em 0;font-weight:700}'+
        '#prnd .pbtn{display:flex;gap:.6em;margin-top:.8em}'+
        '#prnd button{font:inherit;padding:.4em 1.1em;border-radius:6px;border:1px solid #a98a36;background:#fff;cursor:pointer;min-height:38px}'+
        '#prnd button.go{background:#c9a24a;color:#2b2620;font-weight:700}'+
        '#prnd button:disabled{opacity:.55;cursor:default}'+
        '#prnd .pbar{height:8px;border-radius:4px;background:#e8e0cc;overflow:hidden;margin-top:.6em;display:none}'+
        '#prnd .pbar i{display:block;height:100%;width:40%;background:#c9a24a;animation:prnbar 1.1s linear infinite}'+
        '@keyframes prnbar{0%{margin-right:-40%}100%{margin-right:100%}}'+
        '#prnd .perr{color:#a83c2f;margin-top:.5em}';
      document.head.appendChild(c)}
    var PRD=null,PRSEL={};
    window.prnOpen=function(){
      prnCss();
      var tp=textPages();
      if(!tp.length)return;
      if(!PRD){
        PRD=document.createElement('div');PRD.id='prnd';
        PRD.innerHTML=
          '<div class="pbox" role="dialog" aria-modal="true" aria-label="הדפסה ל-PDF">'+
          '<h2>הדפסה לקובץ PDF (A4, שני טורים)</h2>'+
          '<div class="pr" id="prn-type">'+
            '<label><input type="radio" name="prt" value="all">מסכת שלמה</label>'+
            '<label><input type="radio" name="prt" value="perek">פרק</label>'+
            '<label><input type="radio" name="prt" value="daf">דף אחד (שני עמודיו)</label>'+
            '<label><input type="radio" name="prt" value="amud">עמוד אחד</label>'+
            '<label><input type="radio" name="prt" value="range">מדף ועמוד עד דף ועמוד</label></div>'+
          '<div class="pr" id="prn-perek"><label>פרק <select id="prn-p"></select></label></div>'+
          '<div class="pr" id="prn-from"><label>מדף <select id="prn-fd"></select></label><label>עמוד <select id="prn-fa"></select></label></div>'+
          '<div class="pr" id="prn-to"><label>עד דף <select id="prn-td"></select></label><label>עמוד <select id="prn-ta"></select></label></div>'+
          '<div class="pr"><label id="prn-tl"><input type="checkbox" id="prn-tos">עם תוספות (הערות שוליים)</label>'+
            '<label><input type="checkbox" id="prn-dup">דו-צדדי (שוליים פנימיים רחבים יותר לכריכה)</label></div>'+
          '<div class="pnote" id="prn-tn"></div>'+
          '<div class="pcnt" id="prn-cnt"></div>'+
          '<div class="pbar" id="prn-bar"><i></i></div>'+
          '<div class="perr" id="prn-err" hidden></div>'+
          '<div class="pbtn"><button class="go" id="prn-go" type="button">הפק קובץ PDF</button><button id="prn-x" type="button">סגור</button></div>'+
          '</div>';
        document.body.appendChild(PRD);
        PRD.addEventListener('click',function(e){if(e.target===PRD)prnClose()});
        document.getElementById('prn-x').onclick=prnClose;
        document.getElementById('prn-go').onclick=prnGo;
        document.addEventListener('keydown',function(e){if(e.key==='Escape'&&PRD.classList.contains('open'))prnClose()});
        prnFill();
        [].forEach.call(PRD.querySelectorAll('input,select'),function(x){x.addEventListener('change',prnSync)})}
      var cur=0;try{cur=+document.getElementById('dafsel').value||0}catch(e){}
      var key=D.pages[cur]&&D.pages[cur].daf;
      var pp=dafParts(key);
      if(pp){var fd=document.getElementById('prn-fd'),fa=document.getElementById('prn-fa');
        var o=[].slice.call(fd.options).map(function(x){return x.value});
        if(o.indexOf(pp.base)>-1){fd.value=pp.base;prnAmud(fd,fa);fa.value=pp.amud;
          var td=document.getElementById('prn-td'),ta=document.getElementById('prn-ta');
          td.value=pp.base;prnAmud(td,ta);ta.value=pp.amud}}
      var r=PRD.querySelector('input[name=prt][value=amud]');if(r)r.checked=true;
      PRD.classList.add('open');
      prnSync()};
    function prnClose(){if(PRD)PRD.classList.remove('open');if(PRSEL.xhr){try{PRSEL.xhr.abort()}catch(e){}}}
    function prnFill(){
      var tp=textPages(),dafs=[],seen={};
      tp.forEach(function(i){var q=dafParts(D.pages[i].daf);if(q&&!seen[q.base]){seen[q.base]=1;dafs.push(q.base)}});
      ['prn-fd','prn-td'].forEach(function(id){var s=document.getElementById(id);s.innerHTML=dafs.map(function(d){return '<option>'+ge(d)+'</option>'}).join('')});
      ['prn-fd','prn-td'].forEach(function(id){document.getElementById(id).addEventListener('change',function(){prnAmud(this,document.getElementById(id==='prn-fd'?'prn-fa':'prn-ta'))})});
      prnAmud(document.getElementById('prn-fd'),document.getElementById('prn-fa'));
      prnAmud(document.getElementById('prn-td'),document.getElementById('prn-ta'));
      var seenP={},ps=[];
      tp.forEach(function(i){var p=D.pages[i],k=p.perek||'';if(k&&!seenP[k]){seenP[k]=1;ps.push([k,(p.perek||'')+(p.perekName?' - '+p.perekName:'')])}});
      document.getElementById('prn-p').innerHTML=ps.map(function(x){return '<option value="'+ge(x[0])+'">'+ge(x[1])+'</option>'}).join('')}
    function prnAmud(daf,am){
      var b=daf.value,av=[];
      textPages().forEach(function(i){var q=dafParts(D.pages[i].daf);if(q&&q.base===b&&av.indexOf(q.amud)<0)av.push(q.amud)});
      av.sort();
      am.innerHTML=av.map(function(a){return '<option>'+a+'</option>'}).join('')}
    function keyOf(d,a){return d+(a==='א'?'.':':')}
    function prnRange(){
      var t=PRD.querySelector('input[name=prt]:checked').value,tp=textPages();
      var first=D.pages[tp[0]].daf,last=D.pages[tp[tp.length-1]].daf;
      var fd=document.getElementById('prn-fd').value,fa=document.getElementById('prn-fa').value;
      var td=document.getElementById('prn-td').value,ta=document.getElementById('prn-ta').value;
      var from,to;
      if(t==='all'){from=first;to=last}
      else if(t==='perek'){
        var pk=document.getElementById('prn-p').value,a=-1,b=-1;
        tp.forEach(function(i){if(D.pages[i].perek===pk){if(a<0)a=i;b=i}});
        from=D.pages[a].daf;to=D.pages[b].daf}
      else if(t==='daf'){
        var f1=keyOf(fd,'א'),f2=keyOf(fd,'ב');
        var has1=pageIdxOf(f1)>-1,has2=pageIdxOf(f2)>-1;
        from=has1?f1:f2;to=has2?f2:f1}
      else if(t==='amud'){from=keyOf(fd,fa);to=from}
      else{from=keyOf(fd,fa);to=keyOf(td,ta)}
      return {t:t,from:from,to:to}}
    function prnQuery(r,extra){
      var q=new URLSearchParams();q.set('print','1');
      if(r.t==='all')q.set('all','1');else{q.set('from',r.from);q.set('to',r.to)}
      q.set('tos',document.getElementById('prn-tos').checked?'1':'0');
      q.set('duplex',document.getElementById('prn-dup').checked?'1':'0');
      if(extra)for(var k in extra)q.set(k,extra[k]);
      return q}
    var DRYT=0;
    function prnSync(){
      var t=PRD.querySelector('input[name=prt]:checked').value;
      document.getElementById('prn-perek').style.display=t==='perek'?'':'none';
      document.getElementById('prn-from').style.display=(t==='daf'||t==='amud'||t==='range')?'':'none';
      document.getElementById('prn-fa').parentElement.style.display=(t==='daf')?'none':'';
      document.getElementById('prn-to').style.display=t==='range'?'':'none';
      var r=prnRange(),err=document.getElementById('prn-err'),go=document.getElementById('prn-go'),cnt=document.getElementById('prn-cnt');
      err.hidden=true;
      var a=pageIdxOf(r.from),b=pageIdxOf(r.to);
      if(a<0||b<0||b<a){cnt.textContent='';go.disabled=true;
        err.textContent=(a>-1&&b>-1&&b<a)?'סוף הטווח צריך להיות אחרי תחילתו':'הדף שנבחר אינו במסכת';err.hidden=false;return}
      go.disabled=false;
      var inR={};for(var i=a;i<=b;i++)inR[D.pages[i].daf]=1;
      var n=tosItems().filter(function(it){return inR[it.daf]}).length;
      var tos=document.getElementById('prn-tos'),tl=document.getElementById('prn-tl'),tn=document.getElementById('prn-tn');
      tos.disabled=!n;tl.style.opacity=n?'':'.55';
      if(!n){tos.checked=false;tn.textContent="תוס' עדיין לא נכתבו לדפים אלה"}
      else{
        if(PRSEL.tosTouched!==true&&PRSEL.autoTos!==true){tos.checked=true;PRSEL.autoTos=true}
        tn.textContent='בטווח הזה '+n+' תוספות'}
      cnt.textContent='מחשב את מספר העמודים...';
      clearTimeout(DRYT);
      DRYT=setTimeout(function(){prnDry(r).then(function(rep){
        if(rep&&rep.pages)cnt.textContent='מספר העמודים הצפוי: '+rep.pages.length;
        else cnt.textContent='';
      }).catch(function(){cnt.textContent=''})},350)}
    document.addEventListener('change',function(e){if(e.target&&e.target.id==='prn-tos')PRSEL.tosTouched=true},true);
    var DRYFR=null;
    function prnDry(r){
      return new Promise(function(ok,no){
        var key=prnQuery(r).toString();
        if(DRYFR){DRYFR.remove();DRYFR=null}
        var f=document.createElement('iframe');
        f.style.cssText='position:fixed;left:0;top:0;width:794px;height:1123px;visibility:hidden;border:0;pointer-events:none';
        f.setAttribute('aria-hidden','true');
        f.src=location.pathname.split('/').pop()+'?'+key+'&dry=1';
        DRYFR=f;document.body.appendChild(f);
        var t0=Date.now();
        var iv=setInterval(function(){
          if(DRYFR!==f){clearInterval(iv);return no()}
          try{var P=f.contentWindow.__PRN;
            if(P&&P.state==='done'){clearInterval(iv);var rep=P.report;f.remove();DRYFR=null;ok(rep)}
            else if(P&&P.state==='error'){clearInterval(iv);f.remove();DRYFR=null;no()}}catch(e){}
          if(Date.now()-t0>90000){clearInterval(iv);f.remove();DRYFR=null;no()}},300)})}
    function prnGo(){
      var r=prnRange(),go=document.getElementById('prn-go'),bar=document.getElementById('prn-bar'),err=document.getElementById('prn-err');
      var q=prnQuery(r);q.delete('print');q.set('m',SLUG);
      var fname=('לאוקמי גירסא - '+D.masechet+(r.t==='all'?'':' '+r.from+(r.to!==r.from?' - '+r.to:''))+'.pdf').replace(/:/g,'꞉');   /* נקודותיים אסורות בשם קובץ בוינדוס */
      go.disabled=true;bar.style.display='block';err.hidden=true;
      go.textContent='מכין את הקובץ...';
      var t0=Date.now(),iv=setInterval(function(){go.textContent='מכין את הקובץ... '+Math.round((Date.now()-t0)/1000)+' שניות'},1000);
      var ctrl=new AbortController();PRSEL.xhr={abort:function(){ctrl.abort()}};
      fetch(PRINT_API+'/pdf?'+q.toString(),{signal:ctrl.signal}).then(function(res){
        if(!res.ok){return res.text().then(function(t){var m='';try{m=JSON.parse(t).error||''}catch(e){}throw new Error(m||('קוד '+res.status))})}
        return res.blob()}).then(function(blob){
        var a=document.createElement('a'),u=URL.createObjectURL(blob);
        a.href=u;a.download=fname;document.body.appendChild(a);a.click();
        setTimeout(function(){URL.revokeObjectURL(u);a.remove()},4000)})
      .catch(function(e){if(e&&e.name==='AbortError')return;err.textContent='ההפקה לא הצליחה: '+((e&&e.message)||'שירות ההפקה אינו זמין כרגע')+'. אפשר לנסות שוב בעוד רגע.';err.hidden=false})
      .then(function(){clearInterval(iv);bar.style.display='none';go.disabled=false;go.textContent='הפק קובץ PDF'})}
  }
  })();
