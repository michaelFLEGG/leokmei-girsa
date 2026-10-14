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

  /* תיקוני תצוגה להדפסה בלבד (14.10.2026), על ה-HTML של היחידה: טקסט המקור אינו משתנה, רק עטיפה ורווחים:
     יב. "(ב.- יג.)" בראש הפרק - רווח עקבי "(ב. - יג.)".
     יג. סימן ספירה "[ד]" בסוף כותרת - קטן ואפור-קל (cnt), לא בגודל הכותרת.
     יד. "° " בתחילת פסקה - מוצא מן השדה אל המסילה (data-bul), בגודל ובמשקל של אותיות הרשימה. */
  function prnFix(kind,h){
    if(kind==='perek-range')h=h.replace(/\(\s*([א-ת]{1,3}[.:])\s*[-–‐]\s*([א-ת]{1,3}[.:])\s*\)/g,'($1 - $2)');
    if(kind==='nose'||kind==='dh'||kind==='perek-start')h=h.replace(/(\s|&nbsp;)\[([א-ת]{1,3})\](\s*)(?=<\/div>)/g,'$1<span class="cnt">[$2]</span>$3');
    if(h.indexOf('°')>-1)h=h.replace(/(<p class="[^"]*")>(\s|&nbsp;)*°(\s|&nbsp;)*/g,'$1 data-bul="1">');
    return h}

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
        /* ד (14.10.2026): ציון הדף (ב. / ב:) קרוב יותר לטקסט: מוזז בעד dafPullMm שמאלה, ורק במה שפנוי בינו לבין כותרת הצד של אותה שורה */
        '#flow .row .dafmark,.ptx .row .dafmark{position:relative;right:var(--dafpull,0px)}'+
        '#flow .rail.hw.dup .dafmark,.ptx .rail.hw.dup .dafmark{transform:translateY(-1.3em)}'+
        '.pcol .ptx.flow{position:relative;display:block;width:100%;min-height:0;overflow:hidden;padding:0;margin:0;columns:auto;column-count:1;column-width:auto;column-gap:0;column-rule:0;'+
          'background:none;direction:rtl;--measure:'+P.measure+'mm;--rail:'+P.rail+'mm;--gut:0;--lhpx:'+P.body.linePt+'pt;--fs:calc('+P.measure+'mm / '+P.body.fsFromMeasure+');'+
          'font-size:calc('+P.measure+'mm / '+P.body.fsFromMeasure+');line-height:'+P.body.linePt+'pt}'+
        '#flow .row.pcont .main{font-size:'+P.continuationPt+'pt}'+
        /* ב (14.10.2026): אוויר קבוע (כחצי שורה, mishnaGapPt) אחרי סוף משנה ולפני תיבת המשנה; המחלקה gapm נקבעת לפי סדר היחידות, לא לפי אח בעץ */
        '#flow .row.gapm>.main,.ptx .row.gapm>.main{margin-top:'+(P.mishnaGapPt||5.5)+'pt}'+
        /* ג (14.10.2026): גובה שורה מוגדר במפורש לתיבת המשנה ולד"ה/נושא, זהה במסך ובהדפסה. עד כאן קוד האתר נתן להם במסך
           1.2 מגודל הגוף (16.9px) ובהדפסה את רשת הגוף (18.9px): המדידה נעשתה במסך והקובץ הודפס בהדפסה, ותיבת המשנה
           (7 שורות) גדלה בשורה וחצי מעל מה שנמדד ודרסה את השורה שאחריה */
        '#flow .main.mishna,#flow .main.dh,#flow .main.nose,.pcol .ptx.flow .main.mishna,.pcol .ptx.flow .main.dh,.pcol .ptx.flow .main.nose{line-height:var(--lhpx)}'+
        '.phd{font-family:'+h.family+',serif;font-weight:'+h.weight+';font-size:'+h.pt+'pt}'+
        '.pfn{width:'+P.measure+'mm;font-family:'+n.family+',serif;font-weight:'+n.weight+';font-size:'+n.pt+'pt;line-height:'+n.linePt+'pt;letter-spacing:'+n.letterSpacingPt+'pt;column-count:'+n.cols+';column-gap:'+n.colGapMm+'mm}'+
        '#prnmeas{width:'+P.measure+'mm}'+
        '.pfn .fdh{font-weight:'+n.dhWeight+'}'+
        /* ח4: קו מפריד דק מעל בלוק ההערות; ט"ו: מחרוזת ארוכה נשברת ואינה חורגת מעמודת ההערות */
        '.pfn{border-top:.35pt solid #000;padding-top:.5mm;overflow-wrap:anywhere}'+
        '.cnt{font-size:.62em;font-weight:400;letter-spacing:0}'+
        '.pcut{position:absolute;left:0;right:0;bottom:11.5mm;text-align:center;font-family:Vilna,serif;font-size:'+ft.pt+'pt}'+
        '.main p[data-bul]{position:relative}.main p[data-bul]::before{content:"\\00b0";position:absolute;right:-1.15em;top:0;font-family:Vilna,serif;font-weight:900;font-size:.95em}'+
        /* סימן ההפנייה אינו תופס רוחב ואינו נוגע בגובה השורה: תיבה ברוחב אפס, מורמת אל הרווח שבין השורות (השורות חושבו במדויק) */
        'sup.tm{display:inline-block;position:relative;width:0;height:0;overflow:visible;direction:ltr;white-space:nowrap;font-family:'+n.family+',serif;font-weight:'+n.markWeight+';font-size:'+n.markScale+'em;line-height:0;vertical-align:baseline;top:-'+n.markRise+'em;letter-spacing:0;margin:0;padding:0}'+
        '.pfn .fnum{font-size:'+n.numberScale+'em;line-height:0;position:relative;top:-'+n.numberRise+'em;vertical-align:baseline;margin-left:.18em;font-weight:'+n.numberWeight+';text-decoration:none}'+
        '.pfn .fnn{margin:'+n.betweenMm+'mm 0 0}.pfn .fnn:first-child{margin-top:0}'+
        '.pg .pfn .fnm{font-size:'+n.nameScale+'em;color:'+n.nameColor+'!important;font-weight:'+n.weight+'}'+
        '.pfn .fnp{font-size:'+(n.pt-n.parenLessPt)+'pt}'+
        '.pg a.tml{position:absolute;display:block;text-decoration:none;color:transparent!important}'+
        '.pg a.fnl,.pg a.dml{text-decoration:none;color:inherit}'+
        /* עטיפת הקישור של ציון הדף אינה אלמנט גריד: בלעדי זה ציון הדף נהיה inline ואיבד את מקומו ואת ההגבהה (dup) */
        '.pg a.dml{display:contents}'+
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
          html:prnFix(u.k,unitHTML(u,first?p.daf:null,first?pi:null))});
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
    /* ח1 (14.10.2026): מספור ההערות מתחיל ב-1 בכל פרק (מספר התצוגה it.dn); המזהה it.n נשאר לקישורים */
    (function(){var order=items.slice().sort(function(a,b){return (inRange[a.daf]-inRange[b.daf])||((a.line||0)-(b.line||0))||(a.n-b.n)}),cnt={};
      order.forEach(function(it){var q=inRange[it.daf],pk=q===undefined?'':(D.pages[q].perek||'');cnt[pk]=(cnt[pk]||0)+1;it.dn=cnt[pk]})})();
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
      /* ב: אוויר סביב תיבת המשנה (ראה gapm ב-CSS) */
      crecs.forEach(function(x,i){
        var pv=i>0?crecs[i-1]:(c0[0]>0?recs[c0[0]-1]:null);
        if(!pv)return;
        var NOGAP={'perek-num':1,'perek-name':1,'perek-range':1,'perek-start':1,'hadran':1,'hatz':1,'cont':1};
        if(NOGAP[x.kind]||NOGAP[pv.kind])return;
        if((pv.kind==='m'&&x.kind!=='m')||(x.kind==='m'&&pv.kind!=='m'))x.el.classList.add('gapm')});
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
            mk.textContent=prof.notes.numbering==='digits'?String(it.dn||it.n):tosHeb(it);
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
      /* כותרת צד ששום הקטנה לא מכניסה לצד ציון הדף: ציון הדף מועלה (dup) רק אם אינו נוחת על פריט מסילה של שורה שמעליו;
         אחרת כותרת הצד מוקטנת עוד. (כלל 14.10.2026: מסילה אינה חופפת, ובדיקת החפיפות אחרי ההדפסה תופסת כל שארית) */
      (function(){
        function hit(a,b){return Math.min(a.right,b.right)-Math.max(a.left,b.left)>0.75&&Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top)>0.75}
        /* ציון הדף ושורת המסילה הם line-height:0 - גובהם הנמדד אפס; מחליפים בגובה הגופן */
        function RC(e){var r=e.getBoundingClientRect(),h=Math.max(r.height,parseFloat(getComputedStyle(e).fontSize)*0.95);
          return {left:r.left,right:r.right,top:r.top-(h-r.height)/2,bottom:r.bottom+(h-r.height)/2}}
        var rows=[].slice.call(f.querySelectorAll('.row'));
        rows.forEach(function(row,ri){
          var rl=row.querySelector(':scope > .rail'),dm=rl&&rl.querySelector('.dafmark'),w=rl&&rl.querySelector('.win');
          if(!dm||!w||!w.textContent.trim())return;
          var wa=w.querySelector('.anchor')||w;
          if(!hit(RC(dm),RC(wa)))return;
          var near=[];
          for(var k=Math.max(0,ri-3);k<ri;k++){var q=rows[k].querySelector(':scope > .rail');
            if(q)[].slice.call(q.querySelectorAll('.dafmark,.anchor')).forEach(function(e){if(e.textContent.trim())near.push(e)})}
          rl.classList.add('dup');
          var rd=RC(dm),bad=near.some(function(e){return hit(rd,RC(e))});
          if(!bad)return;
          rl.classList.remove('dup');
          var cs=parseFloat(w.style.fontSize)||1;
          [.66,.6,.55].some(function(sc){if(sc>=cs)return false;w.style.fontSize=sc+'em';return !hit(RC(dm),RC(wa))})})})();
      /* ד: משיכת ציון הדף אל הטקסט, לפי המרווח הפנוי בפועל במסילה (אחרי ההתאמה של כותרות הצד) */
      (function(){var mx=(prof.dafPullMm||0)*MM;if(!mx)return;
        [].slice.call(f.querySelectorAll('.row')).forEach(function(row){
          var dm=row.querySelector(':scope > .rail .dafmark');if(!dm)return;
          var rl=dm.closest('.rail'),w=rl.querySelector('.win');
          var rd=dm.getBoundingClientRect(),rr=rl.getBoundingClientRect();
          var lim=rd.left-rr.left-2;
          if(w&&w.textContent.trim()){var wr=w.getBoundingClientRect();lim=Math.min(lim,rd.left-wr.right-2)}
          var pull=Math.max(0,Math.min(mx,lim));
          if(pull>0.5)row.style.setProperty('--dafpull',pull.toFixed(1)+'px')})})();
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
      var num=prof.notes.numbering==='digits'?String(it.dn||it.n):tosHeb(it);
      return '<div class="fnn" id="fn-'+it.n+'"><a class="fnl" href="#tm-'+it.n+'"><span class="fnum">'+ge(num)+'</span></a> <span class="fdh">'+noteText(it.dhs||it.dh)+'</span> - '+noteText(t)+'</div>'}
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
    /* ה (14.10.2026): שורה בודדת שנותרה מקטע (עד הכותרת הבאה) אינה פותחת טור: קודם דחיסה זעירה בטור הקודם
       (עד 2 נקודות, בהזזה מדורגת של השורות - לא בכיווץ אותיות), ואם אינה מספיקה - שורה נוספת עוברת אל הטור הבא */
    var SQ=2*PT;
    function segLen(i){
      if(i>=L.length)return 0;
      var c=0;
      for(var q=i;q<L.length;q++){if(q>i&&L[q].first&&HEADS[L[q].kind])break;c++;if(c>1)break}
      return c}
    function canBreak(i,noLone){
      if(i<=0||i>=L.length)return true;
      if(!noLone&&segLen(i)===1&&!(L[i-1].ri===L[i].ri&&L[i-1].block===L[i].block))return false;
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
    function fillCol(i,cap,noLone){
      var y0=L[i].y0,best=-1,j=i,ids=[];
      while(j<L.length){
        if(j>i&&isForce(j))break;
        var nids=ids.concat(L[j].notes);
        var nf=nids.length?fnBox(nids.slice().sort(function(x,y){return x-y})):null;
        var fh=nf?nf.h+GAP:0;
        var th=L[j].y1-y0;
        if(th+fh>cap+0.5)break;
        ids=nids;j++;
        if(j>=L.length||(canBreak(j,noLone)&&!isForce(j)))best=j;
        else if(j<L.length&&isForce(j))best=j}
      return {best:best,j:j}}
    while(i<L.length){
      var r1=fillCol(i,A,true),best=r1.best,j=r1.j,sq=0;
      if(best>i&&best<L.length&&segLen(best)===1&&!(L[best-1].ri===L[best].ri&&L[best-1].block===L[best].block)){
        var r2=fillCol(i,A+SQ,true);
        if(r2.best>best&&(r2.best>=L.length||segLen(r2.best)!==1)){
          best=r2.best;j=r2.j;
          var nb=noteIds(i,best),fbx=nb.length?fnBox(nb):null;
          sq=Math.max(0,Math.min(SQ,(L[best-1].y1-L[i].y0)+(fbx?fbx.h+GAP:0)-A));R.squeezed=(R.squeezed||0)+1}
        else{var r3=fillCol(i,A,false);if(r3.best>i){best=r3.best;j=r3.j;R.loneMoved=(R.loneMoved||0)+1}}}
      if(best<=i){                                          /* אין שבירה חוקית: מה שנכנס, ולכל הפחות שורה */
        best=Math.max(j,i+1);
        if(best<L.length)R.issues.push({type:'שבירה לא חוקית',daf:L[best].daf,detail:'לא נמצאה נקודת שבירה תקינה בטור'})}
      var cn=noteIds(i,best);
      cols.push({s:i,e:best,notes:cn,sq:sq});
      i=best}

    /* ---- בדיקות אחרי העימוד (לוח התקלות): כותרת מנותקת, שורה יתומה או אלמנה, הערה שנפרדה מסימנה ---- */
    cols.forEach(function(c,ci){
      var a=L[c.s],b=L[c.e-1],pg=Math.floor(ci/prof.cols)+1;
      function iss(t,l,d){R.issues.push({type:t,page:pg,daf:l.daf,unit:recs[l.ri]&&recs[l.ri].u&&recs[l.ri].u.id,detail:d||''})}
      if(HEADS[b.kind]&&b.kind!=='hatz'&&c.e<L.length)iss('כותרת בתחתית טור',b);
      if(c.s>0&&a.ri===L[c.s-1].ri&&a.block===L[c.s-1].block&&a.k<prof.widowOrphan)iss('שורה אלמנה בראש טור',a);
      if(c.e<L.length&&L[c.e].ri===b.ri&&L[c.e].block===b.block&&(b.n-b.k-1)<prof.widowOrphan)iss('שורה יתומה בסוף טור',b);
      /* ח2, ח3: הערה זהה פעמיים באותו עמוד, וסוגר שנפתח ולא נסגר - דיווח למנהל (לא תיקון שקט) */
      (function(){var seenT={};c.notes.forEach(function(n){var it=byN[n];if(!it)return;
        var tx=String(PUBN[n]||it.sum||'');
        var key=String(it.dhs||it.dh||'')+'|'+tx;
        if(seenT[key])iss('הערה כפולה בעמוד',a,'הערות '+(seenT[key].dn||seenT[key].n)+' ו-'+(it.dn||it.n)+': '+tx.slice(0,40));
        else seenT[key]=it;
        [['[',']'],['(',')']].forEach(function(br){
          if(tx.split(br[0]).length!==tx.split(br[1]).length)iss('סוגר חסר בהערה',a,'הערה '+(it.dn||it.n)+': '+tx.slice(0,40))})})})();
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
      /* א (14.10.2026): כותרת רצה מיושרת לשדה הטקסט של הטורים: שם הפרק בקצה הימני של שדה הטקסט של הטור הימני (לא מעל המסילה),
           וציון הדפים בקצה השמאלי של שדה הטקסט של הטור השמאלי */
        var hd='<div class="phd" style="left:'+(MG.left+dx)+'mm;right:'+(MG.right-dx+prof.rail)+'mm;top:'+prof.header.topMm+'mm">'+
        '<span>'+ge(pn)+'</span><span>'+ge(pe)+'</span><span>'+ge(mname)+'</span><span>'+ge(dafSpan(firstLine.daf,lastLine.daf))+'</span></div>';
      var body='';
      cs2.forEach(function(c,ci){
        var ln=L[c.s],le=L[c.e-1];
        var yS=ln.y0-1,yE=le.y1,sqz=c.sq||0,spanY=Math.max(1,le.y1-ln.y0);
        /* ci 0 = הטור הימני: מכולה של 80 מ"מ שימינה עד שולי הימין */
        /* כל המרווח הפנוי נמצא בין שני הטורים; הטור הימני מתחיל בשולי הימין, והשמאלי בשולי השמאל */
        var boxLeft=ci===0?(PG.w-MG.right-(prof.rail+prof.measure)):MG.left;
        boxLeft+=dx;
        var rowsHtml='';
        for(var ri=ln.ri;ri<=le.ri;ri++){
          var rc=recs[ri];
          tpl.innerHTML=rc.html2;
          var cl=tpl.content.firstElementChild;
          cl.style.position='absolute';cl.style.top=(rc.gtop-yS-sqz*Math.max(0,Math.min(1,(rc.gtop-ln.y0)/spanY)))+'px';cl.style.right='0';cl.style.width=(prof.rail+prof.measure)+'mm';
          rowsHtml+=cl.outerHTML}
        var fb=c.notes.length?fnBox(c.notes):null;
        body+='<div class="pcol" style="left:'+boxLeft+'mm;top:'+MG.top+'mm;width:'+(prof.rail+prof.measure)+'mm;height:'+A_mm+'mm">'+
          '<div class="ptx flow" style="height:'+(yE-yS-sqz)+'px">'+rowsHtml+'</div>'+
          (fb?'<div class="pfnw" style="width:'+prof.measure+'mm"><div class="pfn'+(fb.one?' one':'')+'">'+fb.html+'</div></div>':'')+'</div>';
        c.notes.forEach(function(n){pageInfo.notes.push(n)});
        pageInfo.cols.push({lines:c.e-c.s,textMm:+((yE-yS)/MM).toFixed(1),notes:c.notes.length,noteMm:fb?+(fb.h/MM).toFixed(1):0})});
      var foot='<div class="pnum" style="bottom:'+prof.footer.numberFromBottomMm+'mm">'+(pgi+1)+'</div>'+
        '<div class="psite" style="left:'+(MG.left+dx)+'mm">'+(prof.footer.pageQr?'<span class="qr"></span>':'')+'<span class="st">'+ge(prof.footer.siteText)+'</span></div>';
      pgEl.innerHTML=hd+body+foot;
      pgEl.setAttribute('data-daf',firstLine.daf);
      out.appendChild(pgEl);
      R.pages.push(pageInfo)}
    /* טז (14.10.2026): טווח שנגמר באמצע סוגיה (היחידה שאחריו גוף ולא כותרת) - מסומן בסוף העמוד האחרון ומדווח */
    if(QS.get('all')!=='1'&&ti+1<D.pages.length){
      var nextU=null,nextDaf='';
      for(var qn=ti+1;qn<D.pages.length&&!nextU;qn++)if(D.pages[qn].units.length){nextU=D.pages[qn].units[0];nextDaf=D.pages[qn].daf}
      if(nextU&&!HEADS[nextU.k]&&nextU.k!=='hadran'&&out.lastChild){
        var cutEl=document.createElement('div');cutEl.className='pcut';cutEl.textContent='הסוגיה נמשכת בדף '+nextDaf;
        out.lastChild.appendChild(cutEl);
        R.issues.push({type:'הטווח נחתך באמצע סוגיה',daf:lastLine.daf,detail:'ממשיך בדף '+nextDaf})}}
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
    /* ---- בודק חפיפות וחריגות (14.10.2026): מעבר על כל תיבות הטקסט בכל עמוד והשוואת המלבנים שלהן.
       חפיפה בין שני בלוקים, או בלוק שיצא מתיבת השוליים, או פריט בכותרת הרצה שעלה אל מעל המסילה - כשל, לעולם לא בשקט.
       התוצאה ב-R.overlaps / R.bounds, וכל פריט נרשם גם ב-R.issues (לוח התקלות). render_pdf.py נכשל כשיש אחד. */
    (function auditLayout(){
      var tol=0.75,ov=[],bd=[];
      [].slice.call(out.querySelectorAll('.pg')).forEach(function(pe,pn){
        if(pe.classList.contains('cover')||pe.classList.contains('p2')||pe.classList.contains('tocp'))return;
        var pr=pe.getBoundingClientRect(),B=[],dafs=pe.getAttribute('data-daf')||'';
        function add(el,label,owner,kind){var r=el.getBoundingClientRect();
          /* שורה שחוצה את גבול הטור גזורה בידי חלון החיתוך של הטור (.ptx): רק החלק הנראה נבדק */
          var cx=el.closest('.ptx');
          if(cx){var c=cx.getBoundingClientRect();
            r={left:Math.max(r.left,c.left),right:Math.min(r.right,c.right),top:Math.max(r.top,c.top),bottom:Math.min(r.bottom,c.bottom)};
            r.width=r.right-r.left;r.height=r.bottom-r.top}
          if(r.width<1||r.height<1)return;
          B.push({l:label,o:owner,k:kind,x0:r.left-pr.left,x1:r.right-pr.left,y0:r.top-pr.top,y1:r.bottom-pr.top})}
        [].slice.call(pe.querySelectorAll('.pcol .ptx > .row')).forEach(function(row){
          var kind=(row.className.replace(/\b(row|chap1|lz)\b/g,'').trim()||'u');
          var m=row.querySelector(':scope > .main'),ps=m?[].slice.call(m.querySelectorAll(':scope > p')):[];
          var tx=(m?m.textContent:'').trim().slice(0,18);
          if(ps.length)ps.forEach(function(p){add(p,kind+': '+tx,row,'t')});else if(m)add(m,kind+': '+tx,row,'t');
          if(m&&m.classList.contains('mishna'))add(m,'תיבת משנה: '+tx,row,'box');
          [].slice.call(row.querySelectorAll(':scope > .rail .dafmark,:scope > .rail .anchor,:scope > .rail .mbox')).forEach(function(x){
            add(x,'מסילה: '+x.textContent.trim().slice(0,12),row,'r')})});
        [].slice.call(pe.querySelectorAll('.pfn')).forEach(function(x,i){add(x,'הערות שוליים',x,'f')});
        var hd=[];[].slice.call(pe.querySelectorAll('.phd > span')).forEach(function(x){add(x,'כותרת רצה: '+x.textContent.trim(),x,'h');hd.push(B[B.length-1])});
        [].slice.call(pe.querySelectorAll('.pnum,.psite')).forEach(function(x){add(x,x.className,x,'p')});
        for(var i=0;i<B.length;i++)for(var j=i+1;j<B.length;j++){
          var a=B[i],b=B[j];
          if(a.k==='p'&&b.k==='p')continue;
          if(a.o===b.o&&(a.k==='box'||b.k==='box'))continue;
          if(a.o===b.o&&a.k==='t'&&b.k==='t')continue;
          var w=Math.min(a.x1,b.x1)-Math.max(a.x0,b.x0),h=Math.min(a.y1,b.y1)-Math.max(a.y0,b.y0);
          if(w>tol&&h>tol)ov.push({page:pn+1,daf:dafs,a:a.l,b:b.l,mm:+(h/MM).toFixed(2)})}
        var xl=MG.left*MM-tol,xr=(PG.w-MG.right)*MM+tol,yt=MG.top*MM-tol,yb=(PG.h-MG.bottom)*MM+tol;
        B.forEach(function(b){
          if(b.k==='h'){if(b.x0<xl||b.x1>(PG.w-MG.right-prof.rail)*MM+tol)bd.push({page:pn+1,daf:dafs,el:b.l,why:'פריט בכותרת הרצה מעל המסילה או מחוץ לשדה הטקסט'});return}
          if(b.k==='p')return;
          if(b.x0<xl||b.x1>xr||b.y0<yt||b.y1>yb)bd.push({page:pn+1,daf:dafs,el:b.l,why:'מחוץ לשוליים'})})});
      R.overlaps=ov;R.bounds=bd;
      ov.forEach(function(o){R.issues.push({type:'חפיפה',page:o.page,daf:o.daf,detail:o.a+' <> '+o.b+' ('+o.mm+' מ"מ)'})});
      bd.forEach(function(o){R.issues.push({type:'חריגה מהשוליים',page:o.page,daf:o.daf,detail:o.el+' - '+o.why})})})();
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
      'body #flow,body #prnsq{position:absolute;top:0;right:0;height:auto;min-height:0;overflow:visible;padding:0;margin:0;'+
        'columns:auto;column-count:1;column-width:auto;column-gap:0;column-rule:0;background:#fff;visibility:hidden;direction:rtl;'+
        '--gut:0;display:block}'+
      '#flow .row{break-inside:auto}'+
      '#flow .row.pcont .main{font-family:Vilna,serif;font-weight:400;font-size:6.5pt;line-height:var(--lhpx);text-align:right}'+
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
  /* הגבלת הדפסה (13.10.2026): מבקר רגיל מדפיס פרק אחד לכל היותר בכל הפקה, עם תוספות או בלעדיהן;
     מנהל - בלי הגבלה. האכיפה האמיתית ב-Worker; כאן רק הממשק, שאינו מציג למבקר אפשרות שתיחסם. */
  var ONE_MSG='ניתן להדפיס פרק אחד בכל פעם';
  function isAdm(){try{return typeof isAdmin==='function'&&!!isAdmin()}catch(e){return false}}
  function admHdr(){try{var k=localStorage.getItem('lg-adm')||'';return (k&&!/[^\x00-\xff]/.test(k))?{'x-admin-key':k}:{}}catch(e){return {}}}
  function perekKey(p){return (p.perek||'')+'|'+(p.perekName||'')}
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
      var ADM=isAdm();
      if(PRD&&PRD.getAttribute('data-adm')!==(ADM?'1':'0')){PRD.remove();PRD=null}
      if(!PRD){
        PRD=document.createElement('div');PRD.id='prnd';PRD.setAttribute('data-adm',ADM?'1':'0');
        PRD.innerHTML=
          '<div class="pbox" role="dialog" aria-modal="true" aria-label="הדפסה ל-PDF">'+
          '<h2>הדפסה לקובץ PDF (A4, שני טורים)</h2>'+
          '<div class="pr" id="prn-type">'+
            (ADM?'<label><input type="radio" name="prt" value="all">מסכת שלמה</label>':'')+
            '<label><input type="radio" name="prt" value="perek">'+(ADM?'פרק':'פרק שלם')+'</label>'+
            '<label><input type="radio" name="prt" value="daf">דף אחד (שני עמודיו)</label>'+
            '<label><input type="radio" name="prt" value="amud">עמוד אחד</label>'+
            '<label><input type="radio" name="prt" value="range">'+(ADM?'מדף ועמוד עד דף ועמוד':'חלק מן הפרק: מדף ועמוד עד דף ועמוד')+'</label></div>'+
          '<div class="pr" id="prn-perek"><label>פרק <select id="prn-p"></select></label></div>'+
          '<div class="pr" id="prn-from"><label>מדף <select id="prn-fd"></select></label><label>עמוד <select id="prn-fa"></select></label></div>'+
          '<div class="pr" id="prn-to"><label>עד דף <select id="prn-td"></select></label><label>עמוד <select id="prn-ta"></select></label></div>'+
          '<div class="pr" id="prn-tl"><label><input type="radio" name="prtos" id="prn-tos-n" value="0" checked>בלי תוס\'</label>'+
            '<label><input type="radio" name="prtos" id="prn-tos-y" value="1">עם תוס\' (הערות שוליים)</label></div>'+
          '<div class="pr"><label><input type="checkbox" id="prn-dup">דו-צדדי (שוליים פנימיים רחבים יותר לכריכה)</label></div>'+
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
      if(!ADM){      /* בחירת הפרק הנוכחי, ורשימות הדפים מוגבלות אליו */
        var cp=D.pages[cur]?perekKey(D.pages[cur]):'';
        var ps=document.getElementById('prn-p');
        if(cp&&[].slice.call(ps.options).some(function(o){return o.value===cp}))ps.value=cp;
        prnDafs();
        if(pp&&dafInPerek(pp.base+pp.mark,ps.value)){
          var fd2=document.getElementById('prn-fd'),fa2=document.getElementById('prn-fa'),td2=document.getElementById('prn-td'),ta2=document.getElementById('prn-ta');
          fd2.value=pp.base;prnAmud(fd2,fa2);fa2.value=pp.amud;td2.value=pp.base;prnAmud(td2,ta2);ta2.value=pp.amud}}
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
      tp.forEach(function(i){var p=D.pages[i],k=perekKey(p);if((p.perek||p.perekName)&&!seenP[k]){seenP[k]=1;ps.push([k,(p.perek||'')+(p.perekName?' - '+p.perekName:'')])}});
      document.getElementById('prn-p').innerHTML=ps.map(function(x){return '<option value="'+ge(x[0])+'">'+ge(x[1])+'</option>'}).join('');
      if(!isAdm())document.getElementById('prn-p').addEventListener('change',function(){prnDafs();prnSync()})}
    /* דף (בסיס) ששייך לפרק: מבקר רגיל בוחר דפים רק מתוך הפרק שנבחר */
    function dafInPerek(key,pk){
      var i=pageIdxOf(key);return i>-1&&perekKey(D.pages[i])===pk}
    function prnDafs(){
      var pk=document.getElementById('prn-p').value,dafs=[],seen={};
      textPages().forEach(function(i){var q=dafParts(D.pages[i].daf);
        if(q&&perekKey(D.pages[i])===pk&&!seen[q.base]){seen[q.base]=1;dafs.push(q.base)}});
      ['prn-fd','prn-td'].forEach(function(id){var s=document.getElementById(id);s.innerHTML=dafs.map(function(d){return '<option>'+ge(d)+'</option>'}).join('')});
      prnAmud(document.getElementById('prn-fd'),document.getElementById('prn-fa'));
      prnAmud(document.getElementById('prn-td'),document.getElementById('prn-ta'));
      var tdl=document.getElementById('prn-td'),tal=document.getElementById('prn-ta');
      if(tdl.options.length){tdl.selectedIndex=tdl.options.length-1;prnAmud(tdl,tal);if(tal.options.length)tal.selectedIndex=tal.options.length-1}}
    function prnAmud(daf,am){
      var b=daf.value,av=[];
      var pkSel=isAdm()?null:(document.getElementById('prn-p')||{}).value;
      textPages().forEach(function(i){var q=dafParts(D.pages[i].daf);
        if(pkSel&&perekKey(D.pages[i])!==pkSel)return;
        if(q&&q.base===b&&av.indexOf(q.amud)<0)av.push(q.amud)});
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
        tp.forEach(function(i){if(perekKey(D.pages[i])===pk){if(a<0)a=i;b=i}});
        from=D.pages[a].daf;to=D.pages[b].daf}
      else if(t==='daf'){
        var f1=keyOf(fd,'א'),f2=keyOf(fd,'ב');
        var pk2=isAdm()?null:document.getElementById('prn-p').value;
        var has1=pk2?dafInPerek(f1,pk2):pageIdxOf(f1)>-1,has2=pk2?dafInPerek(f2,pk2):pageIdxOf(f2)>-1;
        from=has1?f1:f2;to=has2?f2:f1}
      else if(t==='amud'){from=keyOf(fd,fa);to=from}
      else{from=keyOf(fd,fa);to=keyOf(td,ta)}
      return {t:t,from:from,to:to}}
    function prnQuery(r,extra){
      var q=new URLSearchParams();q.set('print','1');
      if(r.t==='all')q.set('all','1');else{q.set('from',r.from);q.set('to',r.to)}
      q.set('tos',tosOn()?'1':'0');
      q.set('duplex',document.getElementById('prn-dup').checked?'1':'0');
      if(extra)for(var k in extra)q.set(k,extra[k]);
      return q}
    var DRYT=0;
    function prnSync(){
      var t=PRD.querySelector('input[name=prt]:checked').value;
      document.getElementById('prn-perek').style.display=(t==='perek'||!isAdm())?'':'none';
      document.getElementById('prn-from').style.display=(t==='daf'||t==='amud'||t==='range')?'':'none';
      document.getElementById('prn-fa').parentElement.style.display=(t==='daf')?'none':'';
      document.getElementById('prn-to').style.display=t==='range'?'':'none';
      var r=prnRange(),err=document.getElementById('prn-err'),go=document.getElementById('prn-go'),cnt=document.getElementById('prn-cnt');
      err.hidden=true;
      var a=pageIdxOf(r.from),b=pageIdxOf(r.to);
      if(a<0||b<0||b<a){cnt.textContent='';go.disabled=true;
        err.textContent=(a>-1&&b>-1&&b<a)?'סוף הטווח צריך להיות אחרי תחילתו':'הדף שנבחר אינו במסכת';err.hidden=false;return}
      if(!isAdm()){          /* לעולם לא יותר מפרק אחד, גם אם נבחר טווח שחוצה גבול */
        var k0=perekKey(D.pages[a]),multi=false;
        for(var j=a;j<=b;j++)if(perekKey(D.pages[j])!==k0){multi=true;break}
        if(multi){cnt.textContent='';go.disabled=true;err.textContent=ONE_MSG;err.hidden=false;return}}
      go.disabled=false;
      var inR={};for(var i=a;i<=b;i++)inR[D.pages[i].daf]=1;
      var n=tosItems().filter(function(it){return inR[it.daf]}).length;
      var tosY=document.getElementById('prn-tos-y'),tosN=document.getElementById('prn-tos-n'),tl=document.getElementById('prn-tl'),tn=document.getElementById('prn-tn');
      tosY.disabled=!n;tl.style.opacity=n?'':'.55';
      if(!n){tosN.checked=true;tn.textContent="תוס' עדיין לא נכתבו לדפים אלה"}
      else tn.textContent='בטווח הזה '+n+' תוספות';
      cnt.textContent='מחשב את מספר העמודים...';
      clearTimeout(DRYT);
      DRYT=setTimeout(function(){prnDry(r).then(function(rep){
        if(rep&&rep.pages)cnt.textContent='מספר העמודים הצפוי: '+rep.pages.length;
        else cnt.textContent='';
      }).catch(function(){cnt.textContent=''})},350)}
    function tosOn(){var y=document.getElementById('prn-tos-y');return !!(y&&y.checked&&!y.disabled)}
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
      if(!isAdm()){
        var a0=pageIdxOf(r.from),b0=pageIdxOf(r.to),bad=r.t==='all'||a0<0||b0<a0;
        for(var j0=a0+1;!bad&&j0<=b0;j0++)if(perekKey(D.pages[j0])!==perekKey(D.pages[a0]))bad=true;
        if(bad){err.textContent=ONE_MSG;err.hidden=false;return}}
      var q=prnQuery(r);q.delete('print');q.set('m',SLUG);
      var fname=('לאוקמי גירסא - '+D.masechet+(r.t==='all'?'':' '+r.from+(r.to!==r.from?' - '+r.to:''))+'.pdf').replace(/:/g,'꞉');   /* נקודותיים אסורות בשם קובץ בוינדוס */
      go.disabled=true;bar.style.display='block';err.hidden=true;
      go.textContent='מכין את הקובץ...';
      var t0=Date.now(),iv=setInterval(function(){go.textContent='מכין את הקובץ... '+Math.round((Date.now()-t0)/1000)+' שניות'},1000);
      var ctrl=new AbortController();PRSEL.xhr={abort:function(){ctrl.abort()}};
      fetch(PRINT_API+'/pdf?'+q.toString(),{signal:ctrl.signal,headers:admHdr()}).then(function(res){
        if(!res.ok){return res.text().then(function(t){var m='';try{m=JSON.parse(t).error||''}catch(e){}throw new Error(m||('קוד '+res.status))})}
        return res.blob()}).then(function(blob){
        var a=document.createElement('a'),u=URL.createObjectURL(blob);
        a.href=u;a.download=fname;document.body.appendChild(a);a.click();
        setTimeout(function(){URL.revokeObjectURL(u);a.remove()},4000)})
      .catch(function(e){if(e&&e.name==='AbortError')return;err.textContent='ההפקה לא הצליחה: '+((e&&e.message)||'שירות ההפקה אינו זמין כרגע')+'. אפשר לנסות שוב בעוד רגע.';err.hidden=false})
      .then(function(){clearInterval(iv);bar.style.display='none';go.disabled=false;go.textContent='הפק קובץ PDF'})}
  }
  })();
