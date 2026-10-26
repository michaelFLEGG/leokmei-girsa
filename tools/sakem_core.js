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
    /* שורה מודפסת אחת, בתווים (עם רווחים, בלי ניקוד ובלי סימני הביניים). נגזר ממנוע התצוגה
       וההדפסה ולא נוחש: הטור הוא 20.75em של frank.ttf (בדפדפן; 60 מ"מ בהדפסה, כיול מול וורד
       בפרנקריהל 9 - build_site.py, --measure), והרוחב הממוצע של תו בגוף בכורות בגופן הזה הוא
       0.362em (149,565 תווים נמדדו מטבלת הרוחבים של הגופן, 26.10.2026). 20.75/0.362 = 57.
       אותו קבוע משמש את ההנחיה (כלל 17) ואת השומר. */
    var LINE=57;
    var NIK=/[֑-ׇ]/g;
    var HV={'א':1,'ב':2,'ג':3,'ד':4,'ה':5,'ו':6,'ז':7,'ח':8,'ט':9,'י':10};
    /* פתיחת פריט נוסף שבמקומה בא מספר (כלל 18ב) */
    var ALT=/^(ו?אב"א|ו?איבעית אימא|ו?א"נ|ו?אי נמי)(?=[\s:,]|$)/;
    /* כל {T:...} בשורה, עם קינון: [{a,b,v}] */
    function spans(s,tag){
      var out=[],open='{'+tag+':',i=s.indexOf(open);
      while(i>-1){var d=0,j=i;
        for(;j<s.length;j++){if(s[j]==='{')d++;else if(s[j]==='}'){d--;if(!d)break}}
        out.push({a:i,b:j+1,v:s.slice(i+open.length,j)});i=s.indexOf(open,j+1)}
      return out}
    function cutSp(s,sp){var o='',at=0;sp.forEach(function(x){o+=s.slice(at,x.a);at=x.b});return o+s.slice(at)}
    function lineLen(v){return plainI(v).replace(NIK,'').replace(/\s+/g,' ').trim().length}
    /* שורות וכותרות צד, עם הטקסט הנקי */
    function rows(text){return parse(text).filter(function(k){return k.t==='line'||k.t==='title'}).map(function(k){
      return {k:k.t,v:k.v,p:plainI(k.v).replace(/\s+/g,' ').trim()}})}
    function numOf(p){var m=/^([א-י])\.(?:\s|$)/.exec(p);return m?HV[m[1]]:0}
    function afterNum(p){return p.replace(/^[א-י]\.\s*/,'')}
    /* המספרים שבפתח שורה ובכותרות צד, לפי הסדר */
    function nums(text){return rows(text).map(function(r){return numOf(r.p)}).filter(Boolean)}
    /* מספור שלם ורציף. start: הרשימה התחילה לפני הקטע (המספר הבא שמותר לפתוח בו);
       next: המספר שבא מיד אחרי הקטע (רשימה שנמשכת אחריו אינה "פריט אחד") */
    function numbering(text,start,next){
      var bad=0,R=[];
      nums(text).forEach(function(n){
        if(n===1||(!R.length&&start&&n===start)){R.push([n]);return}
        var c=R[R.length-1];if(c&&n===c[c.length-1]+1){c.push(n);return}
        bad++;R.push([n])});
      R.forEach(function(r,i){if(r.length>1)return;
        if(i===0&&start&&r[0]===start&&r[0]>1)return;          /* ממשיך רשימה שלפני הקטע */
        if(i===R.length-1&&next===r[r.length-1]+1)return;       /* נמשך אחרי הקטע */
        bad++});
      return bad}
    function lastNum(text){var a=nums(text||'');return a.length?a[a.length-1]:0}
    /* שם (מתוך {אם:}) או מילה: בלי ניקוד, בלי סימני פיסוק, ובלי אותיות השימוש שבראשה */
    function nbase(w){w=String(w).replace(NIK,'').replace(/[:,.;!?()[\]]/g,'').trim();
      var k=0;while(k<2&&/^[ודלבהמשכ]/.test(w)&&w.length>3){w=w.slice(1);k++}return w}
    function nameOk(b){return b.length>=3||/["']/.test(b)}
    /* כמה פעמים כל שם מופיע כטקסט רגיל (מחוץ ל-{אם:}) בשורות */
    function plainNames(text){var c={};
      rows(text).filter(function(r){return r.k==='line'}).forEach(function(r){
        plainI(cutSp(r.v,spans(r.v,'אם'))).split(/[\s\-]+/).forEach(function(w){var b=nbase(w);if(b)c[b]=(c[b]||0)+1})});
      return c}
    function pnorm(s){s=String(s);if(s.normalize)s=s.normalize('NFC');
      return s.replace(/['׳]/g,'').replace(/\s+/g,' ').trim().replace(/^[\s,.:;!?\-]+|[\s,.:;!?\-]+$/g,'')}
    /* תוכני {הס:} בקטע: ריבוי (מילה שחוזרת נספרת פעמיים) */
    function hsBag(text){var b={};rows(text).forEach(function(r){spans(r.v,'הס').forEach(function(x){var k=pnorm(plainI(x.v));b[k]=(b[k]||0)+1})});return b}
    /* {הס:} שנוספו בפלט (אינם במקור): [{line, v}] */
    function newHs(origText,newText){var bag=hsBag(origText),out=[];
      rows(newText).forEach(function(r,ri){spans(r.v,'הס').forEach(function(x){var k=pnorm(plainI(x.v));
        if(bag[k]){bag[k]--;return}out.push({ri:ri,a:x.a,b:x.b,v:k})})});
      return out}
    /* מקום הדובר: t - המילים שבכותרות הצד, l - השם {אם:} שפותח שורה */
    function spkPos(text){var t={},l={};
      rows(text).forEach(function(r){
        if(r.k==='title'){afterNum(r.p).split(/[\s,]+/).forEach(function(w){var b=nbase(w);if(b)t[b]=1});return}
        var s=r.v.replace(/^[א-י]\.\s*/,'');if(s.indexOf('{אם:')!==0)return;
        var x=spans(s,'אם')[0];if(x){var b=nbase(plainI(x.v));if(nameOk(b))l[b]=1}});
      return {t:t,l:l}}
    function amNames(text){var o={};rows(text).forEach(function(r){spans(r.v,'אם').forEach(function(x){var b=nbase(plainI(x.v));if(nameOk(b))o[b]=1})});
      rows(text).forEach(function(r){if(r.k==='title')afterNum(r.p).split(/[\s,]+/).forEach(function(w){var b=nbase(w);if(/"/.test(b))o[b]=1})});
      return o}
    /* דוברים שעברו מכותרת צד לשורה, או להפך, בין נוסח a לנוסח b */
    function movedNames(a,b){var A=spkPos(a),B=spkPos(b),N=amNames(a),M=amNames(b);Object.keys(M).forEach(function(k){N[k]=1});
      return Object.keys(N).filter(function(n){return A.t[n]&&B.l[n]&&!A.l[n]||A.l[n]&&B.t[n]&&!B.l[n]})}
    /* סוגי התיקון שבין שני נוסחים - ליומן הלמידה: מספור / דובר / הסבר */
    function diffKinds(a,b){var k=[];
      var sig=function(t){return rows(t).map(function(r){return r.k[0]+numOf(r.p)}).filter(function(x){return +x.slice(1)}).join(',')};
      if(sig(a)!==sig(b))k.push('מספור');
      if(movedNames(a,b).length)k.push('דובר');
      var ha=hsBag(a),hb=hsBag(b),ks=function(o){return Object.keys(o).sort().join('|')};
      if(ks(ha)!==ks(hb)||Object.keys(ha).some(function(x){return ha[x]!==hb[x]}))k.push('הסבר');
      return k}
    /* השומר: אחרי המודל ולפני התצוגה. מחזיר רשימת כשלים (ריקה = עבר); אזהרות שאינן פוסלות
       ב-errs.warns. o: {gemara, before, after, edited} */
    function guard(origText,newText,o){
      var r=check(origText,newText,o),e=r.errs;e.warns=r.warns;return e}
    function check(origText,newText,o){
      o=o||{};var errs=[],warns=[];
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
      /* על הטקסט הנקי: שם שהמחבר סימן בשני חלקים ({אם:רמ}{אם:ב"ר}) מתאחד כאן לרמב"ר */
      var src=(plainI(A.map(function(k){return k.v||''}).join(' '))+' '+origText+' '+(o.gemara||'')).replace(/[֑-ׇ]/g,'').replace(/["'״׳]/g,'');
      var amNew=[];B.forEach(function(k){if(k.t==='line'||k.t==='title'){var r=/\{אם:([^{}]*)\}/g,m;while((m=r.exec(k.v)))amNew.push(m[1])}});
      var unknown=amNew.filter(function(n){
        var w=n.replace(/[֑-ׇ]/g,'').replace(/["'״׳:!?.,]/g,'').trim().split(/\s+/).filter(function(x){return x.length>1});
        return w.length&&!w.some(function(x){var y=x.replace(/^[ודשהכלבמ](?=..)/,'');return src.indexOf(x)>-1||src.indexOf(y)>-1})});
      if(unknown.length)errs.push('שם אמורא שאינו במקור: '+unknown.slice(0,3).join(', '));
      /* מספור א. ב. ג. (כלל 18): שלם ורציף, ובלי ואב"א / א"נ שנשארו במקום מספר */
      var st=lastNum(o.before),nx=nums(o.after||'')[0]||0;
      if(numbering(newText,st?st+1:0,nx))errs.push('מספור חסר או כפול');
      var altA=rows(origText).some(function(r){return ALT.test(afterNum(r.p))}),altB=rows(newText).some(function(r){return ALT.test(afterNum(r.p))});
      if(altB&&(altA||nums(newText).length))errs.push('ואב"א / א"נ נשאר במקום מספור (ב.)');
      /* שמות: שם שהיה {אם:} במקור אינו נשאר בשורה כטקסט רגיל */
      var am={};rows(origText).forEach(function(r){spans(r.v,'אם').forEach(function(x){var b=nbase(plainI(x.v));if(nameOk(b))am[b]=1})});
      var po=plainNames(origText),pn=plainNames(newText);
      var lost=Object.keys(am).filter(function(b){return (pn[b]||0)>(po[b]||0)});
      if(lost.length)errs.push('שם אמורא איבד סגנון: '+lost.slice(0,3).join(', '));
      /* פסוקים: נוסח וניקוד זהים אות-באות לפסוק שבמקור, או ללשון הגמרא (שאין בה ניקוד) */
      var srcP=pnorm(plainI(A.map(function(k){return k.v||''}).join(' '))),gemP=pnorm(String(o.gemara||'').replace(NIK,''));
      var psBad=[];B.forEach(function(k){if(k.t!=='line'&&k.t!=='title')return;
        spans(k.v,'פס').forEach(function(x){var v=pnorm(plainI(x.v));if(!v||srcP.indexOf(v)>-1)return;
          if(!/[֑-ׇ]/.test(v)&&gemP&&gemP.indexOf(v)>-1)return;psBad.push(v)})});
      if(psBad.length)errs.push('נוסח פסוק או ניקודו שונה מן המקור: '+psBad.slice(0,2).join(' / '));
      /* אורך: קצר מהמקור, אלא אם יש תוספת מסומנת (ואז לכל היותר כאורך המקור). הסבר חדש
         ({הס:} שאינו במקור) אינו נספר: הקיצור נמדד על הגוף, וההסבר אינו נענש (כלל 6) */
      var nh=newHs(origText,newText),R=rows(newText);
      var lenA=plainI(A.filter(function(k){return k.t!=='lock'}).map(function(k){return k.v}).join(' ')).replace(/\s+/g,'').length;
      var lenB=plainI(R.map(function(r,ri){return cutSp(r.v,nh.filter(function(x){return x.ri===ri}))}).join(' ')).replace(/\s+/g,'').length;
      var marked=/\{[+!]:/.test(newText);
      if(!o.edited&&(marked?lenB>lenA:lenB>=lenA))errs.push(marked?'ארוך מהמקור, גם עם התוספת':'אינו קצר מהמקור');
      /* אזהרות בלבד: דובר ארוך בתוך השורה (כלל 17), הסבר ארוך (כלל 6) */
      R.forEach(function(r){if(r.k!=='line')return;var s=r.v.replace(/^[א-י]\.\s*/,'');if(s.indexOf('{אם:')!==0)return;
        var x=spans(s,'אם')[0];if(!x||!/:\s*$/.test(plainI(x.v)))return;
        var n=lineLen(r.v);if(n>LINE)warns.push('דובר לכותרת צד? ('+plainI(x.v).trim()+' בשורה של '+n+' תווים, שורה מודפסת '+LINE+')')});
      nh.forEach(function(x){if(x.v.split(/\s+/).filter(Boolean).length>4)warns.push('הסבר ארוך: '+x.v.slice(0,40))});
      return {errs:errs,warns:warns}}
    return {h2i:h2i,i2h:i2h,bare:bare,plainI:plainI,toInter:toInter,parse:parse,locks:locks,segments:segments,guard:guard,check:check,
            C2T:C2T,P2T:P2T,T2P:T2P,LINE:LINE,spans:spans,rows:rows,numOf:numOf,nums:nums,newHs:newHs,movedNames:movedNames,diffKinds:diffKinds,nbase:nbase,pnorm:pnorm}
  })();
  if(typeof module!=='undefined'&&module.exports)module.exports=SKC;
