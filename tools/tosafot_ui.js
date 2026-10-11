  /* =================== תוספות בהערות שוליים ===================
     מוזרק לדף המסכת רק כשיש למסכת קובץ תוספות (tosafot/<slug>/live-*.json), ורק אותם תוספות שנכתב להם סיכום.
     הספירה קבועה (tosafot/<slug>/count-<פרק>.json): הערה אחת לכל דיבור המתחיל, ממוספרת ברצף לפי הפרק.
     הסימנים והערות השוליים נבנים מעל הדף אחרי כל רינדור (tsMark) ואינם חלק מנוסח הוורד:
     במצב עריכה והצעה, בתצוגת ספר ובהדפסה הם מוסרים, כדי שלא ייכנסו לטקסט.
     העוגן נשמר כקטע טקסט ומספר מופע (לא כמיקום תו). אם הקטע לא נמצא (הטקסט נערך), הסימן עובר לסוף שורת הגמרא
     הקרובה ומופיע למנהל כ"עוגן זז". תוספות לעולם אינו נעלם בשקט. */
  (function(){
  var TS=window.__TOS||null;
  if(!TS||!TS.items||!TS.items.length)return;
  var TS_KEY='lg-tos-mode';
  var MODES=[['foot','הערות שוליים','סימן עילי בטקסט, וההערות בתחתית הדף'],
             ['side','בצד','לחיצה על הסימן פותחת את ההערה בחלונית, בלי להזיז את הטקסט'],
             ['list','רשימה','כל התוספות ברצף ממוספר, לחזרה ולשינון'],
             ['off','כבוי','בלי סימנים כלל']];
  var STY=[['a','שורה אחת'],['b','מהודק ומובן'],['c','קושיה ותירוץ'],['d','לשון התוספות המקוצרת'],['e','הנפקא מינה']];
  var RULE={'1':'המילה בטקסט','2':'מילה מקבילה בטקסט','3':'סוף שורת הגמרא הקרובה','m':'העוגן זז: הוצמד לסוף שורת הגמרא'};
  function lsGet(k,d){try{var v=localStorage.getItem(k);return v===null?d:v}catch(e){return d}}
  function lsSet(k,v){try{localStorage.setItem(k,v)}catch(e){}}
  var mode=lsGet(TS_KEY,'off');
  if(!/^(foot|side|list|off)$/.test(mode))mode='off';
  var PUB={};            /* n -> {p,t}: הנוסח שנבחר (מנקודת הקליטה) */
  var ADM=null;          /* מנהל: {styles,picks,notes} */
  var MOVED={};          /* n -> true: העוגן זז */
  var PLACED={};         /* n -> כלל שהופעל */
  var byN={};TS.items.forEach(function(it){byN[it.n]=it});

  var sty=document.createElement('style');
  sty.textContent=
   '.tsm{font-family:Vilna,serif;font-weight:700;font-size:.64em;vertical-align:super;line-height:0;color:#7a5a14;cursor:pointer;margin:0 .12em;padding:0 .08em;-webkit-user-select:none;user-select:none;white-space:nowrap;letter-spacing:.02em;border-radius:3px}'+
   '.tsm+.tsm::before{content:",";margin-inline-start:-.05em}'+
   '.tsm:hover,.tsm:focus-visible,.tsm.hot{background:var(--blue-soft,#e6edf7);color:#12396b;outline:0}'+
   '.tsm.mv{color:#a83c2f}'+
   '.tsfoot{margin:.9em 0 .5em;padding:.55em .2em 0;border-top:1px solid #d8cfb8;font-size:.82em;line-height:1.55;-webkit-user-select:text;user-select:text}'+
   '.tsfoot .tsh{font-family:Vilna,serif;font-weight:700;color:#7a5a14;font-size:.92em;margin-bottom:.35em}'+
   '.tsn{margin:.4em 0;padding:.25em .35em;border-radius:5px;scroll-margin-top:70px}'+
   '.tsn.hot{background:#fff4d6;transition:background .3s}'+
   '.tsn .tsnum{font-family:Vilna,serif;font-weight:900;font-size:1.05em;color:#000;margin-inline-end:.35em}'+
   '.tsn .tsdh{font-size:.78em;color:#7a5a14;margin-inline-end:.4em}'+
   '.tsn .tstx{display:inline}'+
   '.tsn .tsin{font:inherit;font-size:.78em;margin-inline-start:.5em;padding:0 .55em;border:1px solid #c9bfa6;border-radius:10px;background:#faf6ea;color:#5a4a1e;cursor:pointer}'+
   '.tsn .tsin:hover{background:#f2ead2}'+
   '.tsn .tsface{margin:.4em 0 .2em;padding:.5em .7em;background:#f6f1e3;border-radius:5px;font-size:.88em;line-height:1.6;color:#2b2620}'+
   '.tsn .tsface a{font-size:.9em;margin-inline-start:.5em;color:#12396b}'+
   '.tsn .tsface b{font-weight:700}'+
   '.tsadm{display:none;margin-top:.5em;padding:.5em .6em;border:1px dashed #b9a56a;border-radius:6px;background:#fffdf5;font-size:.86em}'+
   'body.adm .tsadm{display:block}'+
   '.tsadm .tsah{color:#7a5a14;font-weight:700;margin-bottom:.3em}'+
   '.tsadm .tsv{display:flex;gap:.5em;align-items:flex-start;padding:.2em 0;border-bottom:1px solid #eee5cc}'+
   '.tsadm .tsv .tsvn{flex:0 0 7.5em;font-weight:700;color:#5a4a1e}'+
   '.tsadm .tsv .tsvt{flex:1 1 auto;line-height:1.5}'+
   '.tsadm .tsv.cur{background:#eaf3e6}'+
   '.tsadm button{font:inherit;font-size:.9em;padding:.1em .7em;border:1px solid #b9a56a;border-radius:4px;background:#fff;cursor:pointer;min-height:26px}'+
   '.tsadm button.go{background:#c9a24a;border-color:#a98a36;color:#2b2620}'+
   '.tsadm textarea,.tsadm input{width:100%;box-sizing:border-box;font:inherit;font-size:.95em;padding:.3em .4em;border:1px solid #c9bfa6;border-radius:4px;margin:.25em 0;direction:rtl}'+
   '.tsadm textarea{min-height:5.5em;line-height:1.5}'+
   '.tsadm .tsw{color:#a83c2f}'+
   '#tosmenu{position:fixed;z-index:30;background:var(--paper,#fbf8f1);border:1px solid #c9bfa6;border-radius:8px;box-shadow:0 6px 24px rgba(0,0,0,.22);padding:.4em;min-width:15em;font-size:15px;display:none}'+
   '#tosmenu.open{display:block}'+
   '#tosmenu button{display:block;width:100%;text-align:right;font:inherit;background:none;border:0;padding:.45em .6em;border-radius:5px;cursor:pointer;color:inherit}'+
   '#tosmenu button small{display:block;color:#7a6f58;font-size:.82em}'+
   '#tosmenu button:hover{background:#f2ead2}'+
   '#tosmenu button.on{background:#e6edf7;font-weight:700}'+
   '#tospop{position:fixed;z-index:30;max-width:min(26em,92vw);background:var(--paper,#fbf8f1);border:1px solid #c9bfa6;border-radius:8px;box-shadow:0 6px 24px rgba(0,0,0,.25);padding:.5em .7em;font-size:15px;line-height:1.55;display:none}'+
   '#tospop.open{display:block}'+
   '#tospop .tsx0{position:absolute;top:2px;left:6px;border:0;background:none;font-size:18px;cursor:pointer;color:#7a6f58}'+
   '.tsx{margin:.2em 0 .6em;padding:.45em .7em;border:1px solid #d8cfb8;border-radius:6px;background:#fbf6e6;font-size:.84em;line-height:1.55}'+
   '#tospb .tsdaf{font-weight:700;color:#7a5a14;margin:.7em 0 .2em;font-family:Vilna,serif}'+
   '#tospb .tsn{border-bottom:1px solid #eee5cc}'+
   '@media (hover:none){#tospop{display:none!important}}'+
   '@media print{.tsm,.tsfoot,.tsx,#tosmenu,#tospop{display:none!important}}';
  document.head.appendChild(sty);

  function txt(it){var p=PUB[it.n];return (p&&p.t)||it.sum||''}
  function ge(s){return s.replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
  function narrow(){return window.matchMedia&&window.matchMedia('(max-width:760px)').matches}
  function pageIdx(dafKey){for(var i=0;i<D.pages.length;i++)if(D.pages[i].daf===dafKey)return i;return -1}

  /* ---- אינדקס טקסט של דף: אותיות בלבד, בלי ניקוד, מקף ורווח כרווח אחד ---- */
  var NIKD=/[֑-ׇ]/, LET=/[א-ת]/, SEP=/[\s\-־]/;
  function normCtx(s){var o='',c;for(var i=0;i<s.length;i++){c=s[i];
      if(NIKD.test(c))continue;
      if(LET.test(c))o+=c;
      else if(SEP.test(c)){if(o.length&&o[o.length-1]!==' ')o+=' '}}
    return o.trim()}
  function pageRows(pi){var out=[];D.pages[pi].units.forEach(function(u){var e=document.getElementById('u'+u.id);if(e)out.push([u,e])});return out}
  function buildIndex(rows){
    var s='',map=[];
    rows.forEach(function(r){var m=r[1].querySelector(':scope > .main');if(!m)return;
      var w=document.createTreeWalker(m,NodeFilter.SHOW_TEXT,{acceptNode:function(n){
        return n.parentElement&&n.parentElement.closest('.tsm,.mlabel,.srcb')?NodeFilter.FILTER_REJECT:NodeFilter.FILTER_ACCEPT}});
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

  function mk(it,rule){
    var s=document.createElement('sup');
    s.className='tsm'+(rule==='m'?' mv':'');
    s.setAttribute('data-n',it.n);s.setAttribute('contenteditable','false');
    s.setAttribute('role','button');s.tabIndex=0;
    s.setAttribute('title','תוספות '+it.hn+': '+it.dh);
    s.textContent=it.hn;
    return s}

  function lineOf(ref){var m=/\.(\d+)$/.exec(ref||'');return m?+m[1]:0}
  function placeMark(it,rows){
    var idx=buildIndex(rows),ctx=normCtx(it.t||''),hit=null,rule=String(it.rule||'1');
    if(ctx)hit=findAt(idx,ctx,it.occ||1);
    if(hit){
      var r=document.createRange();r.setStart(hit[0],hit[1]);r.collapse(true);
      r.insertNode(mk(it,rule));PLACED[it.n]=rule;delete MOVED[it.n];return true}
    /* עוגן לא נמצא: סוף שורת הגמרא הקרובה (שורה קטנה או שווה לשורת התוספות, ואם אין - הראשונה) */
    var best=null,first=null;
    rows.forEach(function(x){var ln=lineOf(x[0].ref);if(!ln)return;if(!first)first=x;if(ln<=it.line)best=x});
    var tgt=best||first||rows[rows.length-1];
    if(!tgt)return false;
    var m=tgt[1].querySelector(':scope > .main');if(!m)return false;
    var ps=m.querySelectorAll(':scope > p'),host=ps.length?ps[ps.length-1]:m;
    host.appendChild(mk(it,'m'));
    PLACED[it.n]='m';MOVED[it.n]=true;return true}

  /* ---- בניית הערה ---- */
  function faceHTML(it){
    var t=it.text||'',i=t.indexOf(' - '),h=ge(t);
    if(i>0&&i<120)h='<b>'+ge(t.slice(0,i))+'</b> - '+ge(t.slice(i+3));
    return h+' <a href="'+ge(it.url||'#')+'" target="_blank" rel="noopener">בספריא</a>'}
  function admHTML(it){
    if(!(typeof isAdmin==='function'&&isAdmin()))return '';
    var a=ADM,h='<div class="tsadm"><div class="tsah">למנהל בלבד · מיקום הסימן: '+ge(RULE[PLACED[it.n]||String(it.rule||'1')]||'')+(MOVED[it.n]?' <span class="tsw">(העוגן זז - לאשר או לתקן)</span>':'')+'</div>';
    if(!a||!a.styles||!a.styles[it.n]){return h+'<div>חמשת הנוסחאות נטענות מנקודת הקליטה...</div></div>'}
    var st=a.styles[it.n],pk=a.picks&&a.picks[it.n],nt=a.notes&&a.notes[it.n];
    STY.forEach(function(s){
      h+='<div class="tsv'+(pk&&pk.p===s[0]?' cur':'')+'"><span class="tsvn">'+ge(s[1])+'</span><span class="tsvt">'+ge(st[s[0]]||'')+'</span>'+
         '<button class="go" data-n="'+it.n+'" data-k="'+s[0]+'" onclick="tosPick(this)">בחר</button></div>'});
    h+='<textarea class="tsedit" data-n="'+it.n+'" aria-label="עריכה חופשית">'+ge(txt(it))+'</textarea>'+
       '<button data-n="'+it.n+'" onclick="tosSaveText(this)">שמור את הנוסח שערכתי</button> '+
       '<input class="tsnote" data-n="'+it.n+'" placeholder="הערה לקלוד על התוספות הזה (למשל: חסר התירוץ השני)" value="'+ge((nt&&nt.t)||'')+'">'+
       '<button data-n="'+it.n+'" onclick="tosSaveNote(this)">שמור הערה</button></div>';
    return h}
  function noteHTML(it){
    return '<div class="tsn" data-n="'+it.n+'"><span class="tsnum">'+ge(it.hn)+'</span><span class="tsdh">'+ge(it.dh)+'</span>'+
      '<span class="tstx">'+ge(txt(it))+'</span>'+
      '<button class="tsin" type="button" onclick="tosFace(this)" aria-expanded="false">פנים</button>'+
      '<div class="tsface" hidden>'+faceHTML(it)+'</div>'+admHTML(it)+'</div>'}
  window.tosFace=function(b){var f=b.parentElement.querySelector('.tsface');if(!f)return;
    var open=f.hasAttribute('hidden');if(open)f.removeAttribute('hidden');else f.setAttribute('hidden','');
    b.setAttribute('aria-expanded',open?'true':'false');b.textContent=open?'סגור':'פנים'};

  /* ---- סימון הדף ---- */
  function strip(){
    document.querySelectorAll('#flow .tsm,#flow .tsfoot,#flow .tsx').forEach(function(x){x.remove()});
    PLACED={}}
  function off(){return mode==='off'||(typeof BOOK!=='undefined'&&BOOK)||(typeof PRINTING!=='undefined'&&PRINTING)||(typeof EDIT!=='undefined'&&EDIT)||(typeof SUGM!=='undefined'&&SUGM)}
  var warned=false;
  window.tsMark=function(){
    var f=document.getElementById('flow');if(!f)return;
    strip();
    if(off()){drawList();return}
    var byDaf={};
    TS.items.forEach(function(it){(byDaf[it.daf]=byDaf[it.daf]||[]).push(it)});
    var bad=[];
    Object.keys(byDaf).forEach(function(daf){
      var pi=pageIdx(daf);if(pi<0)return;
      var rows=pageRows(pi);if(!rows.length)return;
      var items=byDaf[daf].slice().sort(function(a,b){return b.n-a.n});
      var placed=0;
      items.forEach(function(it){if(placeMark(it,rows))placed++});
      if(placed!==items.length)bad.push(daf+': '+placed+' מתוך '+items.length);
      if(mode==='foot'){
        var last=rows[rows.length-1][1];
        var fo=document.createElement('div');fo.className='tsfoot';fo.setAttribute('contenteditable','false');
        fo.innerHTML='<div class="tsh">תוספות על העמוד</div>'+byDaf[daf].slice().sort(function(a,b){return a.n-b.n}).map(noteHTML).join('');
        last.insertAdjacentElement('afterend',fo)}});
    if(bad.length&&typeof isAdmin==='function'&&isAdmin()&&!warned){warned=true;
      if(typeof toast==='function')toast('אזהרת שלמות בתוספות: '+bad.join('; '),6000)}
    drawList()};

  /* ---- פתיחת הערה ---- */
  function hot(n){document.querySelectorAll('.tsm[data-n="'+n+'"]').forEach(function(x){x.classList.add('hot');setTimeout(function(){x.classList.remove('hot')},1800)});
    document.querySelectorAll('.tsn[data-n="'+n+'"]').forEach(function(x){x.classList.add('hot');setTimeout(function(){x.classList.remove('hot')},1800)})}
  function popAt(el,html){
    var p=document.getElementById('tospop');
    if(!p){p=document.createElement('div');p.id='tospop';document.body.appendChild(p)}
    p.innerHTML='<button class="tsx0" aria-label="סגור" onclick="tosClose()">×</button>'+html;
    p.classList.add('open');
    var r=el.getBoundingClientRect(),w=p.offsetWidth,hgt=p.offsetHeight;
    var left=Math.min(Math.max(8,r.left+r.width/2-w/2),innerWidth-w-8);
    var top=r.bottom+8;if(top+hgt>innerHeight-8)top=Math.max(8,r.top-hgt-8);
    p.style.left=left+'px';p.style.top=top+'px'}
  window.tosClose=function(){var p=document.getElementById('tospop');if(p)p.classList.remove('open');
    document.querySelectorAll('#flow .tsx').forEach(function(x){x.remove()})};
  function openNote(n,el){
    var it=byN[n];if(!it)return;
    if(mode==='foot'){var t=document.querySelector('.tsfoot .tsn[data-n="'+n+'"]');
      if(t){t.scrollIntoView({block:'center',behavior:'smooth'});hot(n)}return}
    if(mode==='list'){panelOpen();hot(n);var q=document.querySelector('#tospb .tsn[data-n="'+n+'"]');if(q)q.scrollIntoView({block:'nearest'});return}
    if(mode==='side'){
      if(narrow()){
        var row=el.closest('.row');if(!row)return;
        var old=row.nextElementSibling;
        if(old&&old.classList.contains('tsx')&&old.getAttribute('data-n')===String(n)){old.remove();return}
        document.querySelectorAll('#flow .tsx').forEach(function(x){x.remove()});
        var d=document.createElement('div');d.className='tsx';d.setAttribute('data-n',n);d.setAttribute('contenteditable','false');
        d.innerHTML=noteHTML(it);row.insertAdjacentElement('afterend',d);hot(n);return}
      popAt(el,noteHTML(it));hot(n)}}
  document.addEventListener('click',function(ev){
    var m=ev.target.closest&&ev.target.closest('.tsm');
    if(m){ev.preventDefault();ev.stopPropagation();openNote(+m.getAttribute('data-n'),m);return}
    var menu=document.getElementById('tosmenu');
    if(menu&&menu.classList.contains('open')&&!ev.target.closest('#tosmenu,#tosbtn'))menu.classList.remove('open');
    var pop=document.getElementById('tospop');
    if(pop&&pop.classList.contains('open')&&!ev.target.closest('#tospop'))pop.classList.remove('open')},true);
  document.addEventListener('keydown',function(ev){
    if(ev.key==='Escape'){tosClose();var m=document.getElementById('tosmenu');if(m)m.classList.remove('open')}
    if((ev.key==='Enter'||ev.key===' ')&&ev.target.classList&&ev.target.classList.contains('tsm')){
      ev.preventDefault();openNote(+ev.target.getAttribute('data-n'),ev.target)}});
  var hoverT=null;
  document.addEventListener('mouseover',function(ev){
    if(mode!=='side'||narrow())return;
    var m=ev.target.closest&&ev.target.closest('.tsm');
    if(!m)return;
    clearTimeout(hoverT);
    hoverT=setTimeout(function(){openNote(+m.getAttribute('data-n'),m)},280)});
  document.addEventListener('mouseout',function(ev){
    var m=ev.target.closest&&ev.target.closest('.tsm');if(m)clearTimeout(hoverT)});

  /* ---- רשימה (פאנל) ---- */
  function ensurePanel(){
    if(document.getElementById('tosp'))return;
    var p=document.createElement('div');p.className='panel';p.id='tosp';
    p.innerHTML='<button class="x" onclick="panel(&quot;tosp&quot;)">×</button><h3>תוספות - רשימה</h3><div id="tospb"></div>';
    document.body.appendChild(p)}
  function drawList(){
    ensurePanel();
    var b=document.getElementById('tospb');if(!b)return;
    if(mode!=='list'){b.innerHTML='';return}
    var cur=null;try{cur=D.pages[+document.getElementById('dafsel').value].daf}catch(e){}
    var by={},order=[];
    TS.items.slice().sort(function(a,b){return a.n-b.n}).forEach(function(it){if(!by[it.daf]){by[it.daf]=[];order.push(it.daf)}by[it.daf].push(it)});
    b.innerHTML=order.map(function(d){return '<div class="tsdaf">דף '+ge(d.replace(/[.:]$/,''))+(d.slice(-1)===':'?' ע"ב':' ע"א')+'</div>'+by[d].map(noteHTML).join('')}).join('')||'אין'}
  function panelOpen(){ensurePanel();var p=document.getElementById('tosp');if(p&&!p.classList.contains('open'))panel('tosp')}

  /* ---- כפתור ותפריט ---- */
  window.tosBtn=function(){
    var m=document.getElementById('tosmenu');
    if(!m){m=document.createElement('div');m.id='tosmenu';document.body.appendChild(m)}
    m.innerHTML=MODES.map(function(x){return '<button type="button" data-m="'+x[0]+'" class="'+(x[0]===mode?'on':'')+'" onclick="tosSet(this.dataset.m)">'+ge(x[1])+'<small>'+ge(x[2])+'</small></button>'}).join('');
    var b=document.getElementById('tosbtn'),r=b.getBoundingClientRect();
    m.classList.toggle('open');
    /* בטלפון הכפתור מוסתר בסרגל ונפתח מתפריט "עוד": התפריט מוצג במרכז המסך */
    if(!r.width){m.style.top='22vh';m.style.left=Math.max(8,(innerWidth-m.offsetWidth)/2)+'px';return}
    m.style.top=(r.bottom+6)+'px';
    m.style.left=Math.max(8,Math.min(r.left,innerWidth-m.offsetWidth-8))+'px'};
  window.tosSet=function(v){
    mode=v;lsSet(TS_KEY,v);
    var m=document.getElementById('tosmenu');if(m)m.classList.remove('open');
    var b=document.getElementById('tosbtn');if(b)b.classList.toggle('on',v!=='off');
    tosClose();
    var p=document.getElementById('tosp');if(p&&v!=='list')p.classList.remove('open');
    tsMark();
    if(v==='list')panelOpen();
    if(v==='foot'||v==='side'||v==='list'){if(typeof isAdmin==='function'&&isAdmin())admLoad()}};
  (function(){var b=document.getElementById('tosbtn');if(b)b.classList.toggle('on',mode!=='off')})();

  /* ---- חיפוש: "תוס' קל"ד" או מילים מן ההערה ---- */
  window.tsSearchHtml=function(q){
    var nq=normCtx(q||''),out=[];if(nq.length<2)return '';
    var num=/^תוס[׳']?\s*([א-ת\s"'׳״]+)$/.exec((q||'').trim());
    var want=num?num[1].replace(/[\s"'׳״]/g,''):'';
    TS.items.forEach(function(it){
      var hn=it.hn.replace(/["']/g,'');
      var hit=(want&&hn===want)||normCtx(it.dh+' '+txt(it)).indexOf(nq)>=0;
      if(hit)out.push(it)});
    if(!out.length)return '';
    return '<div class="n">בתוספות: '+out.length+' תוצאות</div>'+out.slice(0,20).map(function(it){
      return '<div class="res"><a onclick="tosGo('+it.n+')"><small>תוס\' '+ge(it.hn)+'</small> '+ge(it.dh)+'</a></div>'}).join('')};
  window.tosGo=function(n){var it=byN[n];if(!it)return;
    if(mode==='off')tosSet('foot');
    var pi=pageIdx(it.daf);if(pi<0)return;
    var rows=pageRows(pi);
    if(!rows.length){toDaf(pi);setTimeout(function(){tosGo(n)},120);return}
    var s=document.getElementById('search');if(s)s.classList.remove('open');
    setTimeout(function(){openNote(n,document.querySelector('.tsm[data-n="'+n+'"]')||document.body)},60)};

  /* ---- מנהל: נוסחאות, בחירה, עריכה והערה ---- */
  function admLoad(){
    if(ADM||typeof api!=='function')return;
    api('/tos?slug='+encodeURIComponent(SLUG)+'&adm=1').then(function(j){
      ADM=j.doc||{styles:{},picks:{},notes:{}};
      if(ADM.picks)Object.keys(ADM.picks).forEach(function(n){PUB[n]={p:ADM.picks[n].p,t:ADM.picks[n].t}});
      tsMark()}).catch(function(){})}
  function post(body){return api('/tos',{method:'POST',body:JSON.stringify(Object.assign({slug:SLUG},body))})}
  function applyDoc(j){if(j&&j.doc){ADM=ADM||{styles:{},picks:{},notes:{}};ADM.picks=j.doc.picks||{};ADM.notes=j.doc.notes||{};
      PUB={};Object.keys(ADM.picks).forEach(function(n){PUB[n]={p:ADM.picks[n].p,t:ADM.picks[n].t}})}
    reopenKeep()}
  function reopenKeep(){tsMark()}
  window.tosPick=function(b){
    var n=+b.getAttribute('data-n'),k=b.getAttribute('data-k');
    var t=ADM&&ADM.styles&&ADM.styles[n]&&ADM.styles[n][k];if(!t)return;
    b.disabled=true;
    post({n:n,pick:k,txt:t,from:k}).then(function(j){applyDoc(j);if(typeof toast==='function')toast('הנוסח נבחר ויוצג לכל הלומדים מיד')})
      .catch(function(e){b.disabled=false;if(typeof toast==='function')toast('לא נשמר: '+(e&&e.message||''),5000)})};
  window.tosSaveText=function(b){
    var n=+b.getAttribute('data-n'),ta=b.parentElement.querySelector('textarea.tsedit');if(!ta)return;
    var v=ta.value.trim();if(!v)return;
    var from=(ADM&&ADM.picks&&ADM.picks[n]&&ADM.picks[n].p)||'b';
    b.disabled=true;
    post({n:n,pick:'custom',txt:v,from:from}).then(function(j){applyDoc(j);if(typeof toast==='function')toast('הנוסח שערכת נשמר ויוצג לכל הלומדים מיד')})
      .catch(function(e){b.disabled=false;if(typeof toast==='function')toast('לא נשמר: '+(e&&e.message||''),5000)})};
  window.tosSaveNote=function(b){
    var n=+b.getAttribute('data-n'),i=b.parentElement.querySelector('input.tsnote');if(!i)return;
    b.disabled=true;
    post({n:n,note:i.value}).then(function(j){b.disabled=false;applyDoc(j);if(typeof toast==='function')toast('ההערה נשמרה')})
      .catch(function(e){b.disabled=false;if(typeof toast==='function')toast('לא נשמר: '+(e&&e.message||''),5000)})};

  /* ---- טעינה: הנוסחים שנבחרו (ציבורי) ---- */
  if(location.protocol==='http:'||location.protocol==='https:'){
    fetch(SUGGEST_API+'/tos?slug='+encodeURIComponent(SLUG),{cache:'no-store'}).then(function(r){return r.json()}).then(function(j){
      if(j&&j.ok&&j.pub){var any=false;Object.keys(j.pub).forEach(function(n){if(byN[n]&&j.pub[n].t){PUB[n]=j.pub[n];any=true}});
        if(any&&!off())tsMark()}}).catch(function(){})}
  if(typeof isAdmin==='function'&&isAdmin()&&mode!=='off')setTimeout(admLoad,50);
  })();
