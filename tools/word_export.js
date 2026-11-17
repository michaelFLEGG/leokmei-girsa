  /* =================== הורד וורד (פרומפט 51, 16.11.2026) ===================
     הוורד הוא תוצר בלבד, נגזר מן הספר בכיוון אחד. כאן הוא מופק בדפדפן מן הדף כפי שהמנהל רואה אותו עכשיו,
     כולל עריכות היום שעוד לא קופלו: הסגנונות, ההגדרות והגופנים לקוחים מן הספר עצמו (word/<מסכת>.docx,
     שהבנייה מעתיקה מן הוורד הקנוני), וגוף המסמך נכתב מחדש פסקה אחר פסקה מן הנתונים שבדף. בלי שרת,
     בלי ספרייה חיצונית (פתיחת ה-zip ודחיסתו בכלי הדפדפן). */
  (function(){
  function u8(s){return new TextEncoder().encode(s)}
  var CRCT=null;
  function crc32(b){if(!CRCT){CRCT=new Uint32Array(256);for(var n=0;n<256;n++){var c=n;for(var k=0;k<8;k++)c=c&1?0xEDB88320^(c>>>1):c>>>1;CRCT[n]=c>>>0}}
    var c=0xFFFFFFFF;for(var i=0;i<b.length;i++)c=CRCT[(c^b[i])&255]^(c>>>8);return (c^0xFFFFFFFF)>>>0}
  async function pipe(data,stream){var r=new Response(new Blob([data]).stream().pipeThrough(stream));return new Uint8Array(await r.arrayBuffer())}
  async function unzip(buf){
    var b=new Uint8Array(buf),dv=new DataView(buf),eocd=-1;
    for(var i=b.length-22;i>=0&&i>b.length-70000;i--)if(dv.getUint32(i,true)===0x06054b50){eocd=i;break}
    if(eocd<0)throw new Error('קובץ הוורד פגום');
    var n=dv.getUint16(eocd+10,true),off=dv.getUint32(eocd+16,true),out=[];
    for(var e=0;e<n;e++){
      var m=dv.getUint16(off+10,true),csz=dv.getUint32(off+20,true),nl=dv.getUint16(off+28,true),xl=dv.getUint16(off+30,true),cl=dv.getUint16(off+32,true),lo=dv.getUint32(off+42,true);
      var name=new TextDecoder().decode(b.subarray(off+46,off+46+nl));
      var lnl=dv.getUint16(lo+26,true),lxl=dv.getUint16(lo+28,true),ds=lo+30+lnl+lxl,raw=b.subarray(ds,ds+csz);
      var data=m===0?raw:await pipe(raw,new DecompressionStream('deflate-raw'));
      out.push({name:name,data:data});off+=46+nl+xl+cl}
    return out}
  async function zip(files){
    var parts=[],cen=[],off=0;
    for(var i=0;i<files.length;i++){
      var f=files[i],nm=u8(f.name),crc=crc32(f.data),comp=await pipe(f.data,new CompressionStream('deflate-raw'));
      var h=new DataView(new ArrayBuffer(30));h.setUint32(0,0x04034b50,true);h.setUint16(4,20,true);h.setUint16(6,0x0800,true);h.setUint16(8,8,true);
      h.setUint32(14,crc,true);h.setUint32(18,comp.length,true);h.setUint32(22,f.data.length,true);h.setUint16(26,nm.length,true);
      parts.push(new Uint8Array(h.buffer),nm,comp);
      var c=new DataView(new ArrayBuffer(46));c.setUint32(0,0x02014b50,true);c.setUint16(4,20,true);c.setUint16(6,20,true);c.setUint16(8,0x0800,true);c.setUint16(10,8,true);
      c.setUint32(16,crc,true);c.setUint32(20,comp.length,true);c.setUint32(24,f.data.length,true);c.setUint16(28,nm.length,true);c.setUint32(42,off,true);
      cen.push(new Uint8Array(c.buffer),nm);off+=30+nm.length+comp.length}
    var csz=cen.reduce(function(a,x){return a+x.length},0),e=new DataView(new ArrayBuffer(22));
    e.setUint32(0,0x06054b50,true);e.setUint16(8,files.length,true);e.setUint16(10,files.length,true);e.setUint32(12,csz,true);e.setUint32(16,off,true);
    return new Blob(parts.concat(cen,[new Uint8Array(e.buffer)]),{type:'application/vnd.openxmlformats-officedocument.wordprocessingml.document'})}
  function xe(s){return String(s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}

  /* ---- שורה בדף -> ריצות: [טקסט, מחלקה] (כמו sync_runs שבצד השרת) ---- */
  var SKIPSEL='.tm,.tmg,.srcb,.mlabel,.lgx,sup';
  function runsOf(h){
    var d=document.createElement('div');d.innerHTML=String(h||'').replace(/<br\s*\/?>/gi,' ');
    [].forEach.call(d.querySelectorAll(SKIPSEL),function(x){x.remove()});
    var out=[];
    (function walk(n,cls,bold){
      [].forEach.call(n.childNodes,function(c){
        if(c.nodeType===3){var t=c.nodeValue.replace(/‏/g,'');if(!t)return;
          var k=cls||(bold?'b':null);
          if(out.length&&out[out.length-1][1]===k)out[out.length-1][0]+=t;else out.push([t,k])}
        else if(c.nodeType===1){var tg=c.tagName.toLowerCase(),cl=cls,b=bold;
          if(tg==='i'&&c.className)cl=String(c.className).split(/\s+/)[0]||cl;
          if(tg==='b'||tg==='strong')b=true;
          walk(c,cl,b)}})})(d,null,false);
    return out}
  function plainOf(h){return runsOf(h).map(function(r){return r[0]}).join('').replace(/\s+/g,' ').trim()}
  function psOf(cls){var t=String(cls||'').split(/\s+/);
    if(t.indexOf('nk')>-1)return 'נקודה';if(t.indexOf('hr')>-1)return 'רקע והסבר';if(t.indexOf('in')>-1)return 'פיסקת תשובה';if(t.indexOf('sp')>-1)return 'רווח לפני';return null}
  /* פריטי העמוד בסדר הוורד - אותו סדר כמו items_of_page שבקיפול (tools/fold.py) */
  function itemsOf(pg){
    var out=[];
    function side(a){String(a||'').split(/<br\s*\/?>/i).forEach(function(p){if(plainOf(p))out.push({t:'S',h:p})})}
    (pg.units||[]).forEach(function(u){
      var k=u.k;
      if(u.syn)return;                       /* ד"ה אוטומטי שהבנייה יוצרת (dhauto) - אינו בספר */
      var mkl=u.mkl||{},mka=u.mka?u.mka+' ':'';   /* מספר הקטע שהאתר מסתיר, חוזר לוורד */
      if(k==='u'){side(u.a);(u.l||[]).forEach(function(l,li){var cls=l[0]||'',h=(mkl[li]?mkl[li]+' ':'')+l[1];if(cls==='hatz')return;
          var cl=cls.split(/\s+/);
          if(cl.indexOf('nose')>-1||cl.indexOf('dh')>-1){out.push({t:cl.indexOf('nose')>-1?'H':'D',h:h});return}
          if(!plainOf(h))return;
          /* פרומפט 53: מעוין - חלון (סגנון כותרת הצד) ובו ◆, לפני הפסקה; אם יש לפסקה כותרת צד - הכותרת במקומו */
          if(cl.indexOf('mu')>-1&&!(li===0&&plainOf(u.a)))out.push({t:'S',h:'\u25c6'});
          out.push({t:'L',h:h,ps:psOf(cls)})})}
      else if(k==='m'){
        if(u.mbw&&u.mbh==='word')out.push({t:'X',st:'משנה בצד',h:u.mbw});
        side(u.w);(u.l||[]).forEach(function(l,li){if(l[0]==='hatz')return;out.push({t:'L',h:(mkl[li]?mkl[li]+' ':'')+l[1],ps:'משניות',m:1})})}
      else if(k==='hatz'||k==='perek-range'||k==='perek-start'||k==='hadran'){
        out.push({t:'X',st:{'hatz':'חציצה','perek-range':'דפים בפרק ב','perek-start':'פתיחת פרק','hadran':'הדרן'}[k],h:u.a||''})}
      else if(k==='dh'||k==='nose'){side(u.w);out.push({t:k==='dh'?'D':'H',h:mka+(u.a||'')})}});
    return out}

  window.wordExport=async function(btn){
    var lab=btn&&btn.textContent;
    function say(t){if(btn)btn.textContent=t}
    try{
      say('מכין את הוורד...');
      var res=await fetch('word/'+SLUG+'.docx',{cache:'no-store'});
      if(!res.ok)throw new Error('הספר של המסכת אינו זמין באתר ('+res.status+')');
      var files=await unzip(await res.arrayBuffer());
      var get=function(n){return files.find(function(f){return f.name===n})};
      var dec=function(f){return new TextDecoder().decode(f.data)};
      var stx=dec(get('word/styles.xml')),doc=dec(get('word/document.xml'));
      /* שם סגנון -> מזהה, ובחירה בין שמות חלופיים לפי השימוש בספר עצמו */
      var ID={};stx.replace(/<w:style\b[^>]*w:styleId="([^"]+)"[^>]*>[\s\S]*?<w:name w:val="([^"]+)"/g,function(_,id,nm){ID[nm.replace(/&apos;/g,"'").replace(/&quot;/g,'"')]=id;return _});
      var use=function(id,kind){if(!id)return -1;var m=doc.match(new RegExp('<w:'+kind+' w:val="'+id.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')+'"','g'));return m?m.length:0};
      var pick=function(names,kind){var best=null,bn=-1;names.forEach(function(n){var u=use(ID[n],kind);if(ID[n]&&u>bn){best=ID[n];bn=u}});return best};
      var P={P:pick(['דף בצד'],'pStyle'),S:pick(['חלון 3','דף בצד תוכן'],'pStyle'),H:pick(['נושא'],'pStyle'),D:pick(["ד''ה משנה","משנה ד''ה"],'pStyle'),
             L:ID['Normal']||pick(['Normal'],'pStyle'),M:pick(['משניות'],'pStyle')};
      var PS={};['רקע והסבר','רווח לפני','פיסקת תשובה','נקודה','חציצה','משנה בצד','דפים בפרק ב','פתיחת פרק','הדרן'].forEach(function(n){PS[n]=ID[n]||null});
      var CC={am:['אמוראים תו'],hs:['רקע והסבר תו','הסבר'],ps:['פסוק תו'],dm:["ד''ה משנה תו","משנה ד''ה תו"],ns:['נושא תו'],tn:['תנאי משנה תו','משניות כותרת תו'],
              kt:['כותרת 3 תו'],ot:['אות בודדת תו'],mk:['מספר קטע'],mf:['מפרשים']},C={};
      for(var c in CC)C[c]=pick(CC[c],'rStyle');
      var CM={am:pick(['תנאי המשנה'],'rStyle')||C.am,hs:pick(['הסבר במשנה'],'rStyle')||C.hs};
      function para(sid,h,inM){
        var r=runsOf(h).map(function(x){
          var t=x[0],k=x[1],rs=k&&k!=='b'?((inM&&CM[k])||C[k]):null,pr='';
          if(rs)pr+='<w:rStyle w:val="'+rs+'"/>';
          if(k==='b')pr+='<w:b/><w:bCs/>';
          pr+='<w:rtl/>';
          var body=t.split('\t').map(function(s){return '<w:t xml:space="preserve">'+xe(s)+'</w:t>'}).join('<w:tab/>');
          return '<w:r><w:rPr>'+pr+'</w:rPr>'+body+'</w:r>'}).join('');
        return '<w:p><w:pPr>'+(sid?'<w:pStyle w:val="'+sid+'"/>':'')+'<w:bidi/></w:pPr>'+r+'</w:p>'}
      say('כותב את הפסקאות...');
      var xs=[];
      D.pages.forEach(function(pg){
        if(!pg.units||!pg.units.length)return;
        xs.push(para(P.P,xe(pg.daf)));
        itemsOf(pg).forEach(function(it){
          if(it.t==='S')xs.push(para(P.S,it.h));
          else if(it.t==='H')xs.push(para(P.H,it.h));
          else if(it.t==='D')xs.push(para(P.D,it.h));
          else if(it.t==='X')xs.push(para(PS[it.st]||P.L,it.h));
          else if(it.m)xs.push(para(P.M||P.L,it.h,true));
          else xs.push(para((it.ps&&PS[it.ps])||P.L,it.h))})});
      /* מה שלפני ציון הדף הראשון (שם המסכת, הקדמה) נשאר מן הספר כמות שהוא, וכן הגדרות העמוד שבסוף */
      var bi=doc.indexOf('<w:body>')+8,be=doc.lastIndexOf('<w:sectPr'),body=doc.slice(bi,be);
      var head='',re=/<w:p[ >][\s\S]*?<\/w:p>/g,mm,pid=P.P;
      while((mm=re.exec(body))){if(pid&&mm[0].indexOf('w:val="'+pid+'"')>-1)break;head+=mm[0]}
      var nd=doc.slice(0,bi)+head+xs.join('')+doc.slice(be);
      get('word/document.xml').data=u8(nd);
      say('אורז...');
      var blob=await zip(files);
      var d=new Date(),ds=d.getDate()+'.'+(d.getMonth()+1)+'.'+d.getFullYear();
      var a=document.createElement('a'),url=URL.createObjectURL(blob);
      a.href=url;a.download=D.masechet+' - '+ds+'.docx';document.body.appendChild(a);a.click();
      setTimeout(function(){URL.revokeObjectURL(url);a.remove()},5000);
      say('הורד וורד ✓');setTimeout(function(){say(lab)},3000)}
    catch(e){say(lab);alert('הוורד לא הופק: '+((e&&e.message)||e))}};
  })();
