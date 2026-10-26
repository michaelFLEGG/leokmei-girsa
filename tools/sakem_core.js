  /* =================== סכם: פורמט הביניים והשומר (26.10.2026) ===================
     המודל אינו רואה HTML ואינו מחזיר HTML. הקטע המסומן מומר לפורמט ביניים קריא,
     והתשובה מומרת ממנו בחזרה. אותו קובץ רץ בשלושה מקומות: בדף (העורך), בשרת
     (נקודת הקליטה, השומר שאחרי המודל) ובבדיקות (node), ולכן אין בו DOM.

     השורות:
       [דף:כה.]            ציון דף - נעול
       [משנה:ב] / [משנה]   פתיחת יחידת משנה (עם מספר / בלי) - נעול
       [גמרא]              חזרה לגמרא אחרי משנה - נעול
       [כותרת-נושא:...]    כותרת נושא / ד"ה משנה שהיא שורה משלה (כותרת-דה) - מקומה נעול, נוסחה פתוח
       [קבוע:N]            עיטור, פתיחת פרק, הדרן וכד' - נעול
       [מקור:25a.5]        הפניה לגמרא - נעול (סדר בלבד)
       [צד:...]            כותרת צד לשורה שאחריו; כמה ברצף = ערימת כותרות
       (תשובה) / (רווח) / (נושא) / (דה) / (רקע) / (נקודה)   סגנון הפסקה, בראש השורה
       כל שורה אחרת = פסקה.
     בתוך שורה: {אם:..} אמוראים (במשנה: תנאי המשנה), {הס:..} הסבר, {פס:..} פסוק,
     {דה:..} ד"ה משנה, {נש:..} נושא משנה, {מש:..} משנה, {כב:..} כותרת בשורה, {אות:..} אות פותחת,
     {מפ:..} מפרשים, {ב:..} מודגש, {טאב} טאב לשמאל,
     [מס:..] מספר קטע במשנה (נעול), [תוס':N] עוגן תוספות (נעול).
     סימון בתשובת המודל בלבד: {+:..} תוספת תוכן, {!:..} תיקון תוכן. */
  var SKC=(function(){
    var C2T={am:'אם',hs:'הס',ps:'פס',dm:'דה',ns:'נש',mf:'מפ',b:'ב',tn:'מש',kt:'כב',ot:'אות'};
    var T2C={};Object.keys(C2T).forEach(function(k){T2C[C2T[k]]=k});
    var P2T={'in':'תשובה',sp:'רווח',nose:'נושא',dh:'דה',hr:'רקע',nk:'נקודה'};
    var T2P={};Object.keys(P2T).forEach(function(k){T2P[P2T[k]]=k});
    var ENT={amp:'&',lt:'<',gt:'>',quot:'"',apos:"'",nbsp:' '};
    function dec(s){return String(s).replace(/&(#x[0-9a-f]+|#\d+|[a-z]+);/gi,function(m,e){
      if(e[0]==='#')return String.fromCharCode(e[1]==='x'||e[1]==='X'?parseInt(e.slice(2),16):parseInt(e.slice(1),10));
      return ENT[e.toLowerCase()]!==undefined?ENT[e.toLowerCase()]:m})}
    function escT(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}
    /* הטקסט הנקי של HTML (בלי תגיות) */
    function bare(h){return dec(String(h||'').replace(/<br\s*\/?>/gi,' ').replace(/<[^>]*>/g,''))}
    /* HTML של שורה -> שורת ביניים. תגית שאינה מוכרת נספרת ב-bad (הטקסט נשמר) */
    function h2i(h,bad){
      var out='',st=[],re=/<(\/?)([a-z0-9]+)([^>]*)>|([^<]+)/gi,m;
      h=String(h||'');
      while((m=re.exec(h))){
        if(m[4]!==undefined){out+=dec(m[4]).replace(/\t/g,'{טאב}').replace(/\n/g,' ');continue}
        var close=!!m[1],tag=m[2].toLowerCase(),at=m[3]||'';
        var cm=/class\s*=\s*"([^"]*)"/i.exec(at),cls=cm?cm[1].trim():'';
        if(tag==='br'){out+=' ';continue}
        if(close){var t=st.pop();if(t)out+=t;continue}
        if(tag==='i'&&cls==='mk'){st.push(']');out+='[מס:';continue}
        if(tag==='i'&&C2T[cls]){st.push('}');out+='{'+C2T[cls]+':';continue}
        if(tag==='b'&&!cls){st.push('}');out+='{ב:';continue}
        if(tag==='span'&&cls==='ltab'){st.push('');continue}
        if(tag==='ins'&&(cls==='skmadd'||cls==='skmfix')){st.push('}');out+=cls==='skmadd'?'{+:':'{!:';continue}
        if(bad)bad.push(tag+(cls?'.'+cls:''));
        st.push('')}
      return out.replace(/\{[^{}:]+:\}/g,'')}
    /* שורת ביניים -> HTML. keepMarks: {+:} / {!:} נשמרים כ-<ins> (לתצוגת ההצעה); אחרת נפתחים */
    function i2h(s,keepMarks,bad){
      var out='',st=[],i=0;s=String(s||'');
      while(i<s.length){
        var c=s[i];
        if(c==='{'){
          if(s.substr(i,5)==='{טאב}'){out+='\t';i+=5;continue}
          if(s.substr(i,5)==='{ריק}'){i+=5;continue}
          var m=/^\{([^{}:\s]{1,4}):/.exec(s.slice(i,i+8));
          if(m){
            var t=m[1];i+=m[0].length;
            if(t==='+'||t==='!'){
              if(keepMarks){out+='<ins class="'+(t==='+'?'skmadd':'skmfix')+'">';st.push('</ins>')}else st.push('');continue}
            if(T2C[t]){out+='<i class="'+T2C[t]+'">';st.push('</i>');continue}
            if(bad)bad.push('{'+t+':');st.push('');continue}
        }
        if(c==='}'&&st.length){out+=st.pop();i++;continue}
        if(c==='['){
          var mk=/^\[מס:([^\]]{1,12})\]/.exec(s.slice(i,i+20));
          if(mk){out+='<i class="mk">'+escT(mk[1])+'</i>';i+=mk[0].length;continue}
          var tz=/^\[תוס':[^\]]{1,12}\]/.exec(s.slice(i,i+20));
          if(tz){i+=tz[0].length;continue}
        }
        if(c==='}'){if(bad)bad.push('}');i++;continue}
        out+=escT(c);i++}
      while(st.length)out+=st.pop();
      return out}
    /* הטקסט הנקי של שורת ביניים (בלי סימנים ובלי עוגנים) */
    function plainI(s){return bare(i2h(s,false))}
    var LOCK_RE=/^\[(דף|משנה|גמרא|קבוע|מקור|כותרת-נושא|כותרת-דה)(?::(.*))?\]\s*$/;
    /* יחידות הדף -> פורמט ביניים. units: [{id,k,a,w,l,mbw,ref,daf,first,tos:[{n,t}]}] */
    function toInter(units,o){
      o=o||{};var L=[],bad=[],lastRef='',lastK='';
      units.forEach(function(u){
        if(u.first&&u.daf)L.push('[דף:'+u.daf+']');
        if(u.ref&&u.ref!==lastRef){L.push('[מקור:'+String(u.ref).replace(/^[^.]*\./,'')+']');lastRef=u.ref}
        if(u.k==='m'){L.push(u.mbw?'[משנה:'+bare(u.mbw).replace(/^\s*משנה\s*/,'').trim()+']':'[משנה]')}
        else if(u.k==='u'&&lastK==='m')L.push('[גמרא]');
        if(u.k==='u'||u.k==='m'){
          var w=u.k==='u'?u.a:u.w;
          String(w||'').split(/<br\s*\/?>/i).forEach(function(x){var t=h2i(x,bad).trim();if(t)L.push('[צד:'+t+']')});
          (u.l||[]).forEach(function(l){
            var sty=String(l[0]||'').split(' ').filter(function(c){return P2T[c]})[0];
            var t=h2i(l[1],bad).replace(/\s+/g,' ').trim();
            (u.tos||[]).forEach(function(z){if(!z.t)return;var p=t.indexOf(z.t);if(p<0||t.indexOf('[תוס\':'+z.n+']')>-1)return;
              var e=p+z.t.length;t=t.slice(0,e)+'[תוס\':'+z.n+']'+t.slice(e)});
            L.push((sty?'('+P2T[sty]+') ':'')+(t||'{ריק}'))})}
        else if(u.k==='nose'||u.k==='dh'){
          L.push('[כותרת-'+(u.k==='nose'?'נושא':'דה')+':'+h2i(u.a,bad).replace(/\s+/g,' ').trim()+']')}
        else L.push('[קבוע:'+u.id+']');
        lastK=(u.k==='u'||u.k==='m')?u.k:lastK});
      return {text:L.join('\n'),bad:bad}}
    /* פורמט ביניים -> אסימונים. כל אסימון: {t:'lock',kind,val} / {t:'title',v} / {t:'line',sty,v} */
    function parse(text){
      var out=[];
      String(text||'').replace(/\r/g,'').split('\n').forEach(function(raw){
        var s=raw.replace(/\s+$/,'').replace(/^\s+/,'');if(!s)return;
        var m=LOCK_RE.exec(s);
        if(m){out.push({t:'lock',kind:m[1],val:(m[2]||'').trim()});return}
        m=/^\[צד:(.*)\]$/.exec(s);
        if(m){out.push({t:'title',v:m[1].trim()});return}
        var sty='';
        m=/^\((תשובה|רווח|נושא|דה|רקע|נקודה)\)\s*/.exec(s);
        if(m){sty=T2P[m[1]];s=s.slice(m[0].length)}
        else{m=/^\{נושא:(.*)\}$/.exec(s);if(m){sty='nose';s=m[1]}}
        out.push({t:'line',sty:sty,v:s})});
      return out}
    /* האלמנטים הנעולים בסדרם: [דף], [משנה], [גמרא], [קבוע], [מקור], מקום הכותרות, [מס], [תוס'] */
    function locks(toks){
      var a=[];
      toks.forEach(function(k){
        if(k.t==='lock')a.push(k.kind==='כותרת-נושא'||k.kind==='כותרת-דה'?k.kind:k.kind+':'+k.val);
        else if(k.t==='line'||k.t==='title'){var r=/\[(מס|תוס'):([^\]]*)\]/g,m;while((m=r.exec(k.v)))a.push(m[1]+':'+m[2])}});
      return a}
    /* הקטעים שבין האלמנטים הנעולים (מקור אינו מפריד): לכל קטע - יחידות ושורות */
    function segments(toks){
      var segs=[],cur=null;
      function open(){cur={units:[],lock:null};segs.push(cur)}
      open();
      toks.forEach(function(k){
        if(k.t==='lock'){if(k.kind==='מקור')return;cur.lock=k;open();return}
        if(k.t==='title'){var lu=cur.units[cur.units.length-1];
          if(lu&&!lu.lines.length)lu.titles.push(k.v); else cur.units.push({titles:[k.v],lines:[]});return}
        if(!cur.units.length)cur.units.push({titles:[],lines:[]});
        cur.units[cur.units.length-1].lines.push({sty:k.sty,v:k.v})});
      return segs}
    var META=/(הטקסט|הקטע|הסוגיה)\s+(עוסק|עוסקת|דן|דנה|מתאר|מתארת)|לסיכום|בקטע זה|בסוגיה זו/;
    /* השומר: אחרי המודל ולפני התצוגה. מחזיר רשימת כשלים (ריקה = עבר) */
    function guard(origText,newText,o){
      o=o||{};var errs=[];
      var A=parse(origText),B=parse(newText);
      var la=locks(A),lb=locks(B);
      if(la.join('|')!==lb.join('|')){
        var miss=la.filter(function(x){return lb.indexOf(x)<0}),extra=lb.filter(function(x){return la.indexOf(x)<0});
        errs.push('האלמנטים הנעולים אינם במקומם'+(miss.length?' (חסר: '+miss.slice(0,4).join(', ')+')':'')+
          (extra.length?' (נוסף: '+extra.slice(0,4).join(', ')+')':'')+(!miss.length&&!extra.length?' (הסדר השתנה)':''))}
      var sa=segments(A),sb=segments(B);
      if(sa.length===sb.length)sa.forEach(function(s,i){
        var na=s.units.reduce(function(n,u){return n+u.lines.length},0),nb=sb[i].units.reduce(function(n,u){return n+u.lines.length},0);
        if(na&&!nb)errs.push('קטע שלם נעלם (לפני '+(s.lock?'['+s.lock.kind+(s.lock.val?':'+s.lock.val:'')+']':'הסוף')+')');
        if(!na&&nb)errs.push('נוספו שורות במקום שלא היו בו שורות')});
      var bad=[];
      B.forEach(function(k){if(k.t==='line'||k.t==='title')i2h(k.v,true,bad)});
      if(bad.length)errs.push('תג לא מוכר: '+bad.slice(0,3).join(' '));
      if(/[–—]/.test(newText))errs.push('מקף ארוך');
      if(META.test(newText))errs.push('לשון מטא ("הטקסט עוסק", "לסיכום")');
      /* שמות אמוראים: כל {אם:..} בפלט קיים במקור או בלשון הגמרא */
      var src=(origText+' '+(o.gemara||'')).replace(/[֑-ׇ]/g,'').replace(/["'״׳]/g,'');
      var amNew=[];B.forEach(function(k){if(k.t==='line'||k.t==='title'){var r=/\{אם:([^{}]*)\}/g,m;while((m=r.exec(k.v)))amNew.push(m[1])}});
      var unknown=amNew.filter(function(n){
        var w=n.replace(/[֑-ׇ]/g,'').replace(/["'״׳:!?.,]/g,'').trim().split(/\s+/).filter(function(x){return x.length>1});
        return w.length&&!w.some(function(x){var y=x.replace(/^[ודשהכלבמ](?=..)/,'');return src.indexOf(x)>-1||src.indexOf(y)>-1})});
      if(unknown.length)errs.push('שם אמורא שאינו במקור: '+unknown.slice(0,3).join(', '));
      /* אורך: קצר מהמקור, אלא אם יש תוספת מסומנת (ואז לכל היותר כאורך המקור) */
      var lenA=plainI(A.filter(function(k){return k.t!=='lock'}).map(function(k){return k.v}).join(' ')).replace(/\s+/g,'').length;
      var lenB=plainI(B.filter(function(k){return k.t!=='lock'}).map(function(k){return k.v}).join(' ')).replace(/\s+/g,'').length;
      var marked=/\{[+!]:/.test(newText);
      if(!o.edited&&(marked?lenB>lenA:lenB>=lenA))errs.push(marked?'ארוך מהמקור, גם עם התוספת':'אינו קצר מהמקור');
      return errs}
    return {h2i:h2i,i2h:i2h,bare:bare,plainI:plainI,toInter:toInter,parse:parse,locks:locks,segments:segments,guard:guard,C2T:C2T,P2T:P2T,T2P:T2P}
  })();
  if(typeof module!=='undefined'&&module.exports)module.exports=SKC;
