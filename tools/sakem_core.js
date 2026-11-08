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
       (משנה)              שורת משנה: השורה האחרונה לפני [משנה] נכנסת לתיבת המשנה (6.11.2026)
       כל שורה אחרת = פסקה.
     בתוך שורה: {אם:..} אמוראים (במשנה: תנאי המשנה), {הס:..} הסבר, {פס:..} פסוק,
     {דה:..} ד"ה משנה, {נש:..} נושא משנה, {מש:..} משנה, {כב:..} כותרת בשורה, {אות:..} אות פותחת,
     {מפ:..} מפרשים, {ב:..} מודגש, {טאב} טאב לשמאל,
     [מס:..] מספר קטע במשנה (נעול), [תוס':N] עוגן תוספות (נעול).
     סימון בתשובת המודל בלבד: {+:..} תוספת תוכן, {!:..} תיקון תוכן. */
  var SKC=(function(){
    var C2T={am:'אם',hs:'הס',ps:'פס',dm:'דה',ns:'נש',mf:'מפ',b:'ב',tn:'מש',kt:'כב',ot:'אות'};
    var T2C={};Object.keys(C2T).forEach(function(k){T2C[C2T[k]]=k});
    var P2T={'in':'תשובה',sp:'רווח',nose:'נושא',dh:'דה',hr:'רקע',nk:'נקודה',mi:'משנה'};
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
      /* צ'יפ עוגן התוס' (i2h עם keepMarks) חוזר להיות [תוס':N] */
      h=String(h||'').replace(/<i\b[^>]*class="tzc"[^>]*>[\s\S]*?<\/i>/gi,function(x){
        var n=/data-n="([^"]*)"/.exec(x);return n?''+dec(n[1])+'':''});
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
      return out.replace(/\{[^{}:]+:\}/g,'').replace(/([^]*)/g,function(x,n){return '[תוס\':'+n+']'})}
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
          var tz=/^\[תוס':([^\]]{1,12})\]/.exec(s.slice(i,i+20));
          /* עוגן תוס': בתצוגת ההצעה (keepMarks) - צ'יפ אטומי שאינו נערך ונקרא חזרה ב-h2i,
             כדי שעריכה במקום לא תאבד אותו (פרומפט 20, 5.11.2026). בדף עצמו - אינו נכתב */
          if(tz){if(keepMarks)out+='<i class="tzc" contenteditable="false" data-n="'+escT(tz[1]).replace(/"/g,'&quot;')+'" title="עוגן תוס\' '+escT(tz[1])+' - נשמר אוטומטית">ת</i>';
            i+=tz[0].length;continue}
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
            var sty=String(l[0]||'').split(' ').filter(function(c){return P2T[c]&&!(c==='mi'&&u.k==='m')})[0];   /* שורת משנה שכבר בתוך התיבה - בלי (משנה) */
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
        m=/^\((תשובה|רווח|נושא|דה|רקע|נקודה|משנה)\)\s*/.exec(s);
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

    /* =========== כותרת צד קצרה בלבד, וללא כפילות אחרי כותרת (פרומפט 22, 8.11.2026) ===========
       הכרעת בעל הפרויקט: כותרת צד = עוגן (דובר, מפרש, מילת מהלך, מספור), עד שתי מילים; שלוש - רק
       דובר + מילת מהלך. כל מה שמעבר הוא נושא: שורת (נושא) מעל, ומתחתיה כותרת צד קצרה. ומה שכתוב
       בכותרת אינו חוזר בפתח השורה שאחריה. */
    var MOVE_W={'קשה':1,'קשיא':1,'אלא':1,'והא':1,'הא':1,'תש':1,'מיתיבי':1,'איתיביה':1,'גופא':1,'תר':1,'ואבא':1,'ומיירי':1,'והיינו':1,'היינו':1,'נפקמ':1,'דחה':1,'דחייה':1,'תיובתא':1,'ורמינהי':1,'רמינהי':1,'פשיטא':1,'קמל':1,'איבעיא':1,'תיקו':1,'וצריכי':1,'צריכא':1,'וצריכא':1,'ולכוע':1,'נחלקו':1,'ותיובתא':1,'אמר':1,'אומר':1,'אמרי':1,'סבר':1,'סברי':1};
    function twWords(p){return String(p||'').replace(NIK,'').replace(/^\s*[א-י]\.\s*/,'').replace(/\s*[:.]\s*$/,'').replace(/\s+/g,' ').trim().split(' ').filter(function(w){return w&&!/^[-:,.]+$/.test(w)})}
    function moveKey(w){return String(w).replace(NIK,'').replace(/["'״׳.:,]/g,'')}
    function isMoveW(w){var k=moveKey(w);return !!MOVE_W[k]||(k.length>3&&k[0]==='ו'&&!!MOVE_W[k.slice(1)])}
    var SPK_RE=/^(ר'|רבי|רב|רבא|אביי|שמואל|מר|ר"[א-ת]+|רבה|ריש|רבן|אמימר|בר|ת"ר|תנא|תנן|דתניא|אמר)/;
    function isSpkW(w){var k=String(w).replace(NIK,'');return SPK_RE.test(k)||/^[א-ת]"[א-ת]/.test(k)||/^ר[א-ת]{1,2}'?$/.test(k)}
    /* כותרת צד ארוכה: 'long' (מעל שלוש), 'three' (שלוש שאינן דובר + מהלך), או '' */
    function titleLen(p){var w=twWords(p),n=w.length;
      if(n<=2)return '';
      if(n>3)return 'long';
      var mv=w.some(isMoveW);return mv?'':'three'}
    /* השלמת 8.11.2026: תואר (רב, רבי, ר', רבן, מר, ריש) אינו נפרד מן השם שאחריו, וגם לא "בר/בן" ושם האב.
       בלי זה "רב יוסף לא הלך" נחתך לכותרת צד "רב:" ולכותרת נושא "יוסף לא הלך". מחזיר את מקום המילה האחרונה שנלקחה */
    var TITLE_W={"ר'":1,'רבי':1,'רב':1,'רבן':1,'מר':1,'ריש':1};
    /* תואר עם תחילית (ור', דרב, לרבי). לא "ריש"/"מר": "דריש", "ומר" הן מילים רגילות */
    var PFX_TITLE={"ר'":1,'רבי':1,'רב':1,'רבן':1};
    function takeName(w,i,a){
      var k=String(w[i]).replace(NIK,'').replace(/[:,]$/,'');
      /* תואר עם תחילית (ור', ורב, דרבי): גם הוא אינו נפרד מן השם */
      if(!TITLE_W[k]&&/^[ודכלמש]/.test(k)&&PFX_TITLE[k.slice(1)])k=k.slice(1);
      if(!TITLE_W[k]||/[:,]$/.test(w[i])||i+1>=w.length)return i;
      /* "רבי" ו"רב" עומדים גם לבדם (רבי, רב): לא לוקחים אחריהם פועל, מילת קשר או שם אחר (ושמואל, דרבנן) */
      var nk=String(w[i+1]).replace(NIK,'').replace(/[:,.!?]+$/,'');
      if((k==='רבי'||k==='רב')&&((/^[וד]/.test(nk)&&!NAME_W[nk])||NOT_NAME[nk]||(TRANS_W&&TRANS_W[nk])||(REL_W&&REL_W[nk])))return i;
      /* "מר בר רב אשי": התואר הוא השם, ו"בר" מתחיל את שם האב */
      if(/^(בר|בן|ב"ר)$/.test(nk)){
        if(i+2<w.length){a.push(w[++i]);a.push(w[++i]);if(TITLE_W[String(w[i]).replace(NIK,'')]&&i+1<w.length)a.push(w[++i])}
        return i}
      a.push(w[++i]);
      while(i+2<w.length&&/^(בר|בן|ב"ר)$/.test(String(w[i+1]).replace(NIK,''))&&!/[:,]$/.test(w[i])){a.push(w[++i]);a.push(w[++i])}
      return i}
    /* עוגן קצר מתוך כותרת ארוכה: [מספור] + עד שתי המילים הראשונות אם הן דובר/מהלך. מחזיר {anchor,rest} */
    function splitTitle(p){var num=(/^\s*([א-י]\.)\s*/.exec(p)||[])[1]||'';
      var w=twWords(p),a=[];
      for(var i=0;i<w.length&&a.length<2;i++){
        var x=w[i];
        if(i===0&&(isMoveW(x)||isSpkW(x))){a.push(x);i=takeName(w,i,a);continue}
        if(i>0&&(isMoveW(x)||isSpkW(x)||/^[א-ת]"[א-ת]$/.test(x.replace(NIK,'').replace(/:$/,'')))){a.push(x);i=takeName(w,i,a)}else break}
      if(!a.length)return {anchor:num,rest:w.join(' ')};
      var anchor=(num?num+' ':'')+a.join(' ').replace(/:$/,'')+(/:$/.test(String(p).trim())||a.length&&isSpkW(a[0])&&!/אמר$/.test(a.join(' '))?':':'');
      return {anchor:anchor.replace(/\s+/g,' ').trim().replace(/,(:?)$/,'$1'),rest:w.slice(a.length).join(' ')}}
    /* ===== כותרת צד מול כותרת נושא (הכרעת בעל הפרויקט, 8.11.2026, אחרי סקירת בכורות) =====
       שני עולמות: כותרת צד היא עוגן (בעל השמועה, דובר, מילת מהלך); כותרת נושא היא כותרת שעומדת
       בראש כמה שורות. שם של אמורא אינו כותרת נושא לעולם: מקצרים את כותרת הצד עד בעל השמועה
       ("תרגמה שמואל אליבא דרב" -> "שמואל אליבא דרב"; "והך דתני ר' אבהו" -> "והך דר' אבהו";
       "תני תנא לפני ר"י" -> "תני לפני ר"י"; "תרגמה רהב"ס בדרבא בריגלא" -> "רהב"ס"). תוכן שנכתב
       ככותרת צד ושם בסופו ("ומפצי ביומי תשרי- כשמואל") חוזר לשורה. כותרת נושא מוצעת רק כשאין בה
       שם ושמועה, ויש תחתיה לפחות שלוש שורות עד הכותרת הבאה. */
    var NOT_NAME={};'בשם דריש הורה גזר שונה מתני חזר דייק לא אומר היא הוא אמר סבר בעי קאמר'.split(' ').forEach(function(x){NOT_NAME[x]=1});
    var EPITHET={};'הקטן הגדול הזקן הבבלי איש הכהן החסיד בגדתאה בנו בריה אחוה'.split(' ').forEach(function(x){EPITHET[x]=1});
    var NAME_W={};('שמואל רבא אביי רבה רבינא אמימר עולא זעירי חזקיה לוי רבנן חכמים שמעיה הלל שמאי זומא עזאי אחאי '+
      'יוסי יהודה מאיר שמעון אליעזר יהושע עקיבא טרפון ישמעאל יוחנן אלעזר חנינא יצחק נחמן ששת יוסף הונא חסדא פפא זירא אשי '+
      'כהנא ירמיה אבהו אמי אסי ספרא דימי אבין יונתן נתן גמליאל חייא אושעיא ינאי שמלאי אידי מני אחא אבא הושעיא פנחס ב"ש ב"ה').split(' ').forEach(function(x){NAME_W[x]=1});
    var TRANS_W={};('תני תאני תנא תנן תניא תרגמה תרגמא תרגמי נהג משמיה משום אליבא מתקיף איתיביה אמר אמרי אמרו קרי אישתמיטתיה '+
      'בעי בעא דבעי סבר סברי סברה קתני דקתני דתנן שאל שאלו א"ל וא"ל א"ר וא"ר דא"ר ה"ק וה"ק').split(' ').forEach(function(x){TRANS_W[x]=1});
    var REL_W={'לפני':1,'לפניו':1,'אליבא':1,'משום':1,'משמיה':1,'בשם':1,'על':1,'והך':1,'הך':1,'הא':1,'תני':1,'אמר':1};
    function bareW(w){return String(w).replace(NIK,'').replace(/[:,.!?;]+$/,'').replace(/''/g,'"').replace(/״/g,'"').replace(/׳/g,"'")}
    /* האם המילה היא שם חכם (כולל תחילית ד/ו/כ/ל/מ/ש): תואר, שם ידוע או ראשי תיבות של חכם (ר"ט, רהב"ס, אר"א) */
    function isNameW(w){var k=bareW(w);
      for(var cut=0;cut<=2;cut++){var x=k.slice(cut);if(cut&&!/^[דוכלמש]/.test(k.slice(cut-1)))break;
        if((cut?PFX_TITLE[x]:TITLE_W[x])||NAME_W[x]||/^(ר|אר|רש|ראב|רהב|ריב|רי)[א-ת]*"[א-ת]+$/.test(x)||/^ר'$/.test(x))return true;
        if(cut<2&&!/^[דוכלמש]/.test(x))break}
      return false}
    function isTransW(w){var k=bareW(w);return !!TRANS_W[k]||(k.length>3&&/^[וד]/.test(k)&&!!TRANS_W[k.slice(1)])||/^דתני(א)?$/.test(k)||/^וכך$|^כך$/.test(k)}
    /* כותרת שיש בה שם חכם או לשון שמועה */
    function speakerTitle(p){return twWords(p).some(function(w){return isNameW(w)||isTransW(w)})}
    /* קיצור כותרת צד של שמועה עד בעל השמועה. מחזיר {text} או {unside:1} או null (להכרעה) */
    function shortSide(p){
      var raw=String(p||'').replace(NIK,'').replace(/\s+/g,' ').trim(),num=(/^\s*([א-י]\.)\s*/.exec(raw)||[])[1]||'';
      var w=twWords(raw);if(!w.length)return null;
      /* תוכן ואחריו מקף ושם ("ומפצי ביומי תשרי- כשמואל"): התוכן חוזר לשורה */
      var dm=/^(.*\S)\s*-\s*(\S+(?:\s+\S+)?)\s*:?$/.exec(raw.replace(/^\s*[א-י]\.\s*/,''));
      if(dm&&!isNameW(w[0])&&!isTransW(w[0])&&twWords(dm[2]).every(isNameW))return {unside:1};
      var i=0;
      while(i<w.length&&/^(ו?כך|והכי|נהג|תרגמה|תרגמא|תרגמי)$/.test(bareW(w[i])))i++;
      if(i>=w.length)return null;
      var a=[];
      for(;i<w.length;i++){var x=w[i],k=bareW(x);
        if(/^(תני|תאני)$/.test(k)&&w[i+1]&&bareW(w[i+1])==='תנא'){a.push('תני');i++;continue}
        /* "והך דתני X" בלבד (בפתח): לא "רבי וראבר"ש דתניא, רבי" */
        if(/^(ו?)דתני(א)?$/.test(k)&&w[i+1]&&isNameW(w[i+1])&&a.every(function(y){return /^ו?הך$/.test(bareW(y))})){
          var nx=String(w[i+1]);a.push((k[0]==='ו'?'וד':'ד')+nx);i++;
          if(TITLE_W[bareW(nx)]&&w[i+1]){a.push(w[++i])}continue}
        if(isNameW(x)){
          /* שם שני צמוד בלי ו/ד/ל/מ/אר ובלי מילת קשר לפניו ("ור"א ר"א היא") - נשוא, לא המשך השרשרת */
          var pv=a.length?bareW(a[a.length-1]):'';
          if(a.some(isNameW)&&!REL_W[pv]&&!/^(ו|ד|ל|מ|ב|אר)/.test(k)){break}
          a.push(x);var ii=takeName(w,i,a);i=ii;continue}
        if(REL_W[k]&&a.length<4){a.push(x);continue}
        if(/^(ד|מ)/.test(k)&&isNameW(k.slice(1))&&!/^(ריש|מר)$/.test(k.slice(1))){a.push(x);continue}
        break}
      /* תואר נלווה לשם ("שמואל הקטן", "רב יוסף איש הוצל"): אין לחתוך - להכרעה */
      if(i<w.length&&EPITHET[bareW(w[i])])return null;
      /* מילות קישור בסוף ("לפני", "בשם") בלי שם אחריהן: המקור שאחריהן אינו מוכר כשם - להכרעה */
      if(a.length&&/^(בשם|משום|משמיה|אליבא|לפני|לפניו)$/.test(bareW(a[a.length-1]))&&i<w.length)return null;
      /* המשך השרשרת אחרי החיתוך ("מבר קפרא", "מר"ח"): בעל השמועה הוא שם, לא חותכים - להכרעה */
      if(w.slice(i).some(function(x){return /^מ(בי|בר|בן|ר'|רב|רבי|ר"|רש|רי)/.test(bareW(x))}))return null;
      while(a.length&&REL_W[bareW(a[a.length-1])]&&!isNameW(a[a.length-1]))a.pop();
      if(!a.length||!a.some(isNameW))return null;
      if(i<w.length&&!w.slice(i).every(function(x){return isNameW(x)||REL_W[bareW(x)]})){
        /* אחרי בעל השמועה בא תוכן: נשאר רק בעל השמועה (כמו "רהב"ס"), ובתנאי שהתחלנו בשם,
           ושבהמשך אין עוד שם, ראשי תיבות או סוגריים - אחרת אולי חותכים את שרשרת המסירה */
        if(w.slice(i).some(function(x){return isNameW(x)||/["'\[\]()]/.test(bareW(x))||/^(בר|בן)$/.test(bareW(x))}))return null;
        if(!isNameW(w[0])&&!/^(ו?כך|נהג|תרגמה|תרגמא|תרגמי|תני|תאני|ו?דתני|ו?הך)$/.test(bareW(w[0])))return null}
      if(a.length>4)return null;
      var t=a.join(' ').replace(/(^|\s)(ו?ד?)רבי(?=\s)/g,"$1$2ר'").replace(/[:,]+$/,'');
      t=/[?!]$/.test(t)?t:t+':';
      if(bareW(t)===bareW(raw)||twWords(t).length>=w.length)return null;
      return {text:(num?num+' ':'')+t}}
    /* כמה שורות גוף מתחת לשורה i עד הכותרת הבאה (נושא, ד"ה, משנה, גמרא, דף) */
    function linesUnder(T,i){var n=0;
      for(var k=i+1;k<T.length;k++){var s=T[k].trim();if(!s)continue;
        if(/^\((נושא|דה)\)|^\[(כותרת-|משנה|גמרא|דף|קבוע|מקור)/.test(s))break;
        if(/^\[צד:/.test(s))continue;n++}
      return n}
    /* חפיפה בין כותרת לפתח השורה שאחריה: כמה מילים מתחילת הכותרת (או חלקה) חוזרות בראש השורה.
       מחזיר מספר מילים חוזרות בראש השורה (0 = אין). כפילות: 2 ומעלה, או הכותרת כולה (גם מילה אחת) */
    function overlapN(titleP,lineV){
      var tw=twWords(titleP).map(function(w){return nbaseQ(w)}).filter(Boolean);
      var lw=twWords(plainI(lineV)).map(function(w){return nbaseQ(w)}).filter(Boolean).slice(0,tw.length+3);
      if(!tw.length||!lw.length)return 0;
      var best=0;
      for(var i=0;i<tw.length;i++){var k=0;while(i+k<tw.length&&k<lw.length&&tw[i+k]===lw[k])k++;if(k>best)best=k}
      return (best>=2||(best>=1&&best===tw.length))?best:0}
    function nbaseQ(w){return qnorm(String(w)).replace(/\s/g,'')}
    /* הסרת n מילים מראש שורת ביניים (בלי לשבור סימון), כולל "אמר/אומר" אחרי שם הדובר */
    function stripWords(v,n,dropSay){
      var o='',i=0,left=n,seenWord=false,inW=false;v=String(v);
      /* דילוג על מספור בפתח */
      var m=/^([א-י]\.\s*)/.exec(v);if(m){o=m[1];i=m[1].length}
      while(i<v.length&&left>0){
        var c=v[i];
        if(c==='{'){var mm=/^\{[^{}:\s]{1,4}:/.exec(v.slice(i,i+8));if(mm){o+=mm[0];i+=mm[0].length;continue}}
        if(c==='}'){o+=c;i++;continue}
        if(/\s/.test(c)){i++;if(inW){inW=false;left--}continue}
        inW=true;i++}
      if(inW)left--;
      var rest=v.slice(i);
      if(dropSay){rest=rest.replace(/^((?:\}|\s)*)(אמר|אומר)(?=[\s}:]|$)/,function(x,a){return a.replace(/\s/g,'')})}
      var r=(o+rest.replace(/^[\s:,\-]+/,'')).replace(/\{[^{}:]+:\}/g,'').replace(/^\s+/,'').replace(/^((?:\}\s*)*)[-:,]+\s*/,'$1');
      return r}
    /* תיקון אוטומטי של כותרות צד ארוכות וכפילויות ברורות. מחזיר {text,notes,changed} */
    function autofixTitles(text){
      var T=String(text||'').replace(/\r/g,'').split('\n'),out=[],notes=[],ch=0,items=[];
      var P=parse(text);
      /* עוברים על השורות בסדר, ומזהים כותרות צד לפי התחביר */
      for(var i=0;i<T.length;i++){
        var raw=T[i],s=raw.trim(),m=/^\[צד:(.*)\]$/.exec(s);
        if(m){var p=plainI(m[1]).replace(/\s+/g,' ').trim();
          if(titleLen(p)==='long'){
            /* עוגן קצר + נושא. אם כבר בא מיד לפני שורת (נושא) - לא מוסיפים עוד אחת */
            var sp=splitTitle(p);
            var restW=twWords(sp.rest).filter(function(w){return w.replace(/[^א-ת]/g,'').length>=2});
            /* (8.11.2026) שם ושמועה אינם נושא, וכותרת נושא רק מעל שלוש שורות לפחות */
            /* נושא אמיתי: בלי שם, בלי לשון שמועה, בלי ראשי תיבות (ת"ל, וה"ק, ב"ש - לשון הסוגיה ולא נושא),
               ובלי עוגן שנגמר בתואר או באמירה (א"ר, ר', אמר: מה שאחריו הוא שם) */
            var ancW=twWords(sp.anchor),ancLast=ancW.length?bareW(ancW[ancW.length-1]):'';
            var notTopic=speakerTitle(sp.rest)||/"/.test(bareW(sp.rest).replace(/''/g,'"'))||/^(בן|בר)\s/.test(sp.rest)||
              !!TITLE_W[ancLast]||!!TITLE_W[ancLast.slice(1)]||/^(ו?ד?א"ר|ו?אמר|ו?ד?אמר)$/.test(ancLast);
            if(notTopic||restW.length<3||linesUnder(T,i)<3){
              var ss=speakerTitle(p)?shortSide(p):null;
              if(ss&&ss.text){out.push('[צד:'+ss.text+']');items.push({kind:'long',title:p,heading:'',side:ss.text});
                notes.push('כותרת צד של שמועה קוצרה עד בעל השמועה: '+p.slice(0,40));ch++;continue}
              if(ss&&ss.unside){items.push({kind:'long',title:p,heading:'',side:'',unside:1});
                notes.push('כותרת צד שהיא תוכן - מוצע להחזירה לשורה: '+p.slice(0,40));out.push(raw);continue}
              notes.push('כותרת צד ארוכה - דורשת עריכה ידנית: '+p.slice(0,40));
              items.push({kind:'long',manual:1,title:p,why:speakerTitle(p)?'name':(restW.length<3?'short':'few')});out.push(raw);continue}
            if(restW.length<3){notes.push('כותרת צד ארוכה - דורשת עריכה ידנית: '+p.slice(0,40));items.push({kind:'long',manual:1,title:p});out.push(raw);continue}
            if(sp.rest){
              var prev=out.length?out[out.length-1]:'';
              /* (8.11.2026, אחרי סקירת בכורות) כותרת נושא אינה נוצרת בקוד: הקוד אינו יודע אם היא באמת עומדת
                 בראש כמה שורות. מסומן להכרעה, עם החלוקה האפשרית כרמז בלבד */
              if(!/^\((נושא)\)/.test(prev)&&!/^\[כותרת-נושא:/.test(prev)){
                /* פותחת בשם (רבא: ...): הפעולה המוכנה היא קיצור עד בעל השמועה, כמו בתיקוני בכורות */
                var ss2=speakerTitle(p)?shortSide(p):null;
                if(ss2&&ss2.text){out.push('[צד:'+ss2.text+']');items.push({kind:'long',title:p,heading:'',side:ss2.text,maybe:sp.rest.replace(/:$/,'')});
                  notes.push('כותרת צד של שמועה קוצרה עד בעל השמועה: '+p.slice(0,40));ch++;continue}
                notes.push('ייתכן שזו כותרת נושא - להכרעה: '+p.slice(0,40));
                items.push({kind:'long',manual:1,why:'topic',title:p,heading:sp.rest.replace(/:$/,''),side:sp.anchor});out.push(raw);continue}
              notes.push('כותרת ארוכה הוחלפה בעוגן; הנושא כבר קיים: '+sp.rest.slice(0,30));
              if(sp.anchor&&sp.anchor!==''&&twWords(sp.anchor).length)out.push('[צד:'+sp.anchor+']');
              items.push({kind:'long',title:p,heading:sp.rest.replace(/:$/,''),side:sp.anchor});
              notes.push('כותרת צד ארוכה פוצלה: '+p.slice(0,40));ch++;continue}}
        }
        out.push(raw)}
      /* כפילות: כותרת (צד / נושא) והשורה הבאה */
      for(var j=0;j<out.length-1;j++){
        var a=out[j].trim(),tm=/^\[צד:(.*)\]$/.exec(a),tn=/^\((נושא)\)\s*(.*)$/.exec(a),tl=/^\[כותרת-(?:נושא|דה):(.*)\]$/.exec(a);
        var tp=tm?tm[1]:tn?tn[2]:tl?tl[1]:null;if(tp===null)continue;
        /* השורה הבאה: דילוג על כותרות צד נוספות רק כשזו כותרת צד */
        var k=j+1;while(k<out.length&&/^\[צד:/.test(out[k].trim()))k++;
        if(k>=out.length)continue;
        var nl=out[k].trim();if(/^\[(?:דף|משנה|גמרא|קבוע|מקור|כותרת-נושא|כותרת-דה)/.test(nl))continue;
        var sty=/^\((תשובה|רווח|נושא|דה|רקע|נקודה|משנה)\)\s*/.exec(nl),body=sty?nl.slice(sty[0].length):nl;
        if(tn&&sty&&sty[1]==='נושא')continue;
        var n=overlapN(tp,body);if(!n)continue;
        var tw=twWords(plainI(tp));
        /* תיקון רק כשהחפיפה פותחת את השורה והשארית אינה ריקה (ברור) */
        var firstOverlap=n===tw.length||n>=2;
        var fixed=stripWords(body,n,tw.length<=2);
        var fp=plainI(fixed).trim(),fw=twWords(fp).length;
        /* ברור: החפיפה פותחת את השורה, ומיד אחריה מפריד (מקף / נקודתיים / פסיק) או שהכותרת כולה חזרה */
        var pb=plainI(body),pw=pb.split(/(\s+)/),cnt=0,endAt=0;
        for(var q=0;q<pw.length&&cnt<n;q++){endAt+=pw[q].length;if(pw[q]&&!/^\s+$/.test(pw[q]))cnt++}
        var sepOk=/^\s*[-:,.]/.test(pb.slice(endAt))||n===tw.length&&/^\s*(אמר|אומר)?\s*[א-ת{]/.test(pb.slice(endAt));
        if(firstOverlap&&!sepOk){items.push({kind:'dup',manual:1,title:plainI(tp),line:pb});continue}
        if(firstOverlap&&fw>=4&&!/^[\[(•]/.test(fp)&&fixed!==body){
          items.push({kind:'dup',title:plainI(tp),line:plainI(body),fixed:plainI(fixed)});
          out[k]=(sty?sty[0]:'')+fixed;notes.push('כפילות אחרי כותרת הוסרה: '+tw.join(' ').slice(0,30));ch++}}
      return {text:out.join('\n'),notes:notes,changed:ch,items:items}}
    /* שגיאות/אזהרות של כותרות צד וכפילות, על נוסח. orig: הנוסח המקורי (כותרות שלא השתנו - אזהרה, לא שגיאה) */
    function titleIssues(newText,origText){
      var E=[],W=[],origT={};
      if(origText!=null)parse(origText).forEach(function(k){if(k.t==='title')origT[pnorm(plainI(k.v))]=1});
      var P=parse(newText);
      P.forEach(function(k,i){
        if(k.t==='title'){var p=plainI(k.v).replace(/\s+/g,' ').trim(),L=titleLen(p);
          if(L==='long'){(origT[pnorm(p)]?W:E).push('כותרת צד ארוכה (מעל שלוש מילים) - נושא לכותרת נושא: '+p.slice(0,40))}
          else if(L==='three')W.push('כותרת צד של שלוש מילים שאינה דובר + מילת מהלך: '+p.slice(0,40))}
        if(k.t==='title'||(k.t==='line'&&k.sty==='nose')||(k.t==='lock'&&(k.kind==='כותרת-נושא'||k.kind==='כותרת-דה'))){
          var tp=k.t==='lock'?k.val:k.v,j=i+1;
          if(k.t==='title')while(j<P.length&&P[j].t==='title')j++;
          var nx=P[j];if(!nx||nx.t!=='line'||(k.t==='line'&&nx.sty==='nose'))return;
          if(overlapN(plainI(tp),nx.v))E.push('כפילות בין כותרת לשורה שאחריה: '+plainI(tp).slice(0,30)+' | '+plainI(nx.v).slice(0,30))}});
      return {errs:E,warns:W}}
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
    /* גם פריטים ממוספרים בתוך שורה אחת ("א. ... ב. ...") - כלל בעל הפרויקט: לא להרבות בשורות (6.11.2026) */
    function numsIn(p){var a=[],n=numOf(p);if(!n)return a;a.push(n);
      var r=/\s([א-י])\.\s/g,m;while((m=r.exec(p))){if(HV[m[1]]===a[a.length-1]+1)a.push(HV[m[1]])}return a}
    function nums(text){var a=[];rows(text).forEach(function(r){a=a.concat(numsIn(r.p))});return a}
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
    /* מילות מסגרת שסומנו בטעות בסגנון אמורא (אבל, דוקא, נחלקו...) אינן שם: הסרת הסגנון מהן היא תיקון ולא אובדן (פרומפט עבודה גרסה 2) */
    var NOTNAME={'אבל':1,'דוקא':1,'נחלקו':1,'חלקו':1,'אי':1,'או':1,'אלא':1,'והך':1,'דהך':1};
    function nameOk(b){return !NOTNAME[b]&&(b.length>=3||/["']/.test(b))}
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
    /* ---- פרומפט 26 (8.11.2026): לשון הקודש ולא ארמית, ומובנות לפני הידוק ----
       aramNew: מילה ארמית מן הרשימה שמספר מופעיה בהצעה גדול ממספרם במקור (נוספה, או שהחליפה מילה עברית).
       נספר על הטקסט הנקי, בלי פסוקים ({פס:}) ובלי לשון גמרא מובאת ({כב:}). מונחי הסוגיה הקבועים אינם ברשימה. */
    var ARAM='איכא ליכא הוי הואי נמי הכי היכי מיהו דהא תרי תרתי קמא שקיל שקלה שקלי שדי שדיא שדו אמאי מאי היכא לאו אית ליה ביה בהו להו להון דידיה נפשיה איהו איהי הוה הות קאמר קתני טייעא גמלא מסא בריש תנורא זימנא זימני השתא מיבעיא איפכא כוותיה כוותייהו תלינן חדא לאיתויי אתי אתא אזל אזיל הכא התם אמינא ניהו מיניה מינה גביה בהדי כוליה טובא פורתא מנלן ומפרשא אתריה אתרא אפילו'.split(' ').filter(function(w){return w!=='אפילו'});
    var ARAM_S={};ARAM.forEach(function(w){ARAM_S[w]=1});
    function aramWords(text){var c={};
      rows(text).forEach(function(r){var v=cutSp(cutSp(r.v,spans(r.v,'כב')),[]);v=cutSp(v,spans(v,'פס'));
        plainI(v).replace(NIK,'').replace(/'[^']*'/g,' ').split(/[\s,.:!?;()\[\]\-]+/).forEach(function(w){
          w=w.replace(/["״׳]/g,'');if(!w)return;var k=null;
          if(ARAM_S[w])k=w;else if(w.length>2&&/^[ודשהבלכ]/.test(w)&&ARAM_S[w.slice(1)])k=w.slice(1);
          else if(w==='אי'||w==='ואי'||w==='דאי')k='אי';
          if(k)c[k]=(c[k]||0)+1})});
      return c}
    function aramNew(origText,newText){var a=aramWords(origText),b=aramWords(newText);
      return Object.keys(b).filter(function(k){return b[k]>(a[k]||0)})}
    /* squeeze: הידוק יתר. כל שורה בהצעה מוצמדת לשורת המקור שחולקת איתה הכי הרבה מילים; שורת מקור (25 תווים ומעלה)
       שכל השורות שהוצמדו לה יחד קצרות ממחצית אורכה - חשודה. וגם הקטע כולו: גוף ההצעה (בלי {הס:} חדש) מתחת ל-65%
       ממקורו. הסף כויל על ההכרעות בבכורות (data/sakem/decisions/bekhorot-review-8.11.json). שורה חשודה עוברת
       לקורא נפרד שאינו רואה את המקור (runner: השדה read; בדף: קריאה נוספת למודל). */
    var SQ_SEG=0.65,SQ_LINE=0.5,SQ_MIN=25;
    function sqW(t){return qnorm(t).split(' ').filter(function(w){return w.length>1})}
    function squeeze(origText,newText){
      var A=rows(origText).filter(function(r){return r.k==='line'}),nh=newHs(origText,newText);
      var Ball=rows(newText),B=[];
      Ball.forEach(function(r,ri){if(r.k!=='line')return;var v=cutSp(r.v,nh.filter(function(x){return x.ri===ri}));
        B.push({v:r.v,p:r.p,len:plainI(v).replace(NIK,'').replace(/\s+/g,'').length})});
      var lenOf=function(r){return r.p.replace(NIK,'').replace(/\s+/g,'').length};
      var la=A.reduce(function(n,r){return n+lenOf(r)},0),lb=B.reduce(function(n,r){return n+r.len},0);
      var aw=A.map(function(r){var o={};sqW(r.p).forEach(function(w){o[w]=(o[w]||0)+1});return o});
      var got=A.map(function(){return {n:0,rows:[]}});
      B.forEach(function(b){var best=-1,bs=1;sqW(b.p).forEach(function(){});
        var ws=sqW(b.p);aw.forEach(function(o,i){var c={},sc=0;ws.forEach(function(w){if(o[w]&&(c[w]||0)<o[w]){c[w]=(c[w]||0)+1;sc++}});if(sc>bs){bs=sc;best=i}});
        if(best>-1){got[best].n+=b.len;got[best].rows.push(b.v)}});
      var lines=[];A.forEach(function(r,i){var L=lenOf(r);if(L<SQ_MIN||!got[i].rows.length)return;
        if(got[i].n<L*SQ_LINE)lines.push({orig:r.v,now:got[i].rows.join('\n'),r:Math.round(100*got[i].n/L)})});
      var ratio=la?lb/la:1;
      return {ratio:Math.round(ratio*100)/100,lines:lines,seg:ratio<SQ_SEG,flag:ratio<SQ_SEG||lines.length>0}}
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
      /* 6.11.2026 (בעל הפרויקט): אין ; בשום מקום באתר - נקודה רגילה במקומה */
      if(/;/.test(newText))errs.push('נקודה-פסיק (;) - לכתוב נקודה');
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
      if(numbering(newText,st?st+1:0,nx)&&!numbering(origText,st?st+1:0,nx))errs.push('מספור חסר או כפול');
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
      /* פרומפט 26: אין חובה לקצר (מובנות לפני הידוק). רק הצעה שהתארכה ממש נעצרת: מעבר ל-15% (ועוד 10 תווים),
         ועם תוספת מסומנת - 30% (ועוד 20). מילות {הס:} חדשות אינן נספרות */
      if(!o.edited&&lenB>(marked?lenA*1.3+20:lenA*1.15+10))errs.push(marked?'ארוך מהמקור, גם עם התוספת':'ארוך מהמקור');
      var an=aramNew(origText,newText);
      if(an.length)errs.push('ארמית במקום לשון הקודש: '+an.slice(0,5).join(', '));
      var sq=squeeze(origText,newText);
      if(sq.seg)warns.push('הידוק יתר: הקטע ירד ל-'+Math.round(sq.ratio*100)+'% מאורכו - לבדיקת מובנות');
      sq.lines.forEach(function(x){warns.push('הידוק יתר ('+x.r+'%): '+plainI(x.now).slice(0,60))});
      /* אזהרות בלבד: דובר ארוך בתוך השורה (כלל 17), הסבר ארוך (כלל 6) */
      R.forEach(function(r){if(r.k!=='line')return;var s=r.v.replace(/^[א-י]\.\s*/,'');if(s.indexOf('{אם:')!==0)return;
        var x=spans(s,'אם')[0];if(!x||!/:\s*$/.test(plainI(x.v)))return;
        var n=lineLen(r.v);if(n>LINE)warns.push('דובר לכותרת צד? ('+plainI(x.v).trim()+' בשורה של '+n+' תווים, שורה מודפסת '+LINE+')')});
      nh.forEach(function(x){if(x.v.split(/\s+/).filter(Boolean).length>4)warns.push('הסבר ארוך: '+x.v.slice(0,40))});
      /* שורה אלמנה (כלל 17ז, פרומפט 20): השורה המודפסת האחרונה של פסקה ובה מילה או שתיים */
      R.forEach(function(r){if(r.k!=='line')return;var n=lineLen(r.v);if(n<=LINE)return;
        var w=plainI(r.v).replace(NIK,'').replace(/\s+/g,' ').trim().split(' '),cur=0,last=[];
        w.forEach(function(x){if(cur&&cur+1+x.length>LINE){cur=x.length;last=[x]}else{cur+=(cur?1:0)+x.length;last.push(x)}});
        if(last.length<=2)warns.push('שורה אלמנה ('+last.join(' ')+') - להדק או לשבור מוקדם')});
      /* ---- פרומפט עבודה גרסה 2 (5.11.2026): שלמות, עקביות וסימטריה - חובה לפני העימוד ---- */
      var ti=titleIssues(newText,origText);ti.errs.forEach(function(e){errs.push(e)});ti.warns.forEach(function(e){warns.push(e)});
      quality(newText,o).forEach(function(e){errs.push(e)});
      return {errs:errs,warns:warns}}
    /* בדיקות האיכות של הפרק, משותפות לשומר (על ההצעה) ולבדיקת הפרק (tools/print/lint_chapter.mjs, על הנתונים).
       o.mishna: לשון המשניות של הקטע (מ-data/mishna), לבדיקת תיבת המשנה */
    var NIKQ=/[\u0591-\u05C7]/g;
    function qnorm(t){return String(t).replace(NIKQ,'').replace(/["'״׳]/g,'').replace(/[^א-ת\s]/g,' ').replace(/\s+/g,' ').trim()}
    function quality(text,o){
      o=o||{};var E=[],seen={};
      /* שורות תיבת המשנה אינן נבדקות לכפילות: הגמרא מצטטת את המשנה, וזו חזרה מכוונת */
      var R=rows(text),RD=[],inM0=false;parse(text).forEach(function(k){
        if(k.t==='lock'){if(k.kind!=='מקור')inM0=k.kind==='משנה';return}
        if((k.t==='line'||k.t==='title')&&!inM0)RD.push({k:k.t,v:k.v,p:plainI(k.v).replace(/\s+/g,' ').trim()})});
      /* א1: שורות כפולות או כמעט כפולות (שורה שכולה בתוך שורה אחרת) */
      RD.forEach(function(r,i){var n=qnorm(r.p);if(n.length<8)return;
        if(seen[n]!==undefined){E.push('שורה כפולה: '+r.p.slice(0,40));return}
        seen[n]=i});
      RD.forEach(function(r,i){var n=qnorm(r.p);if(n.length<14)return;
        RD.forEach(function(q,j){if(i===j)return;var m=qnorm(q.p);if(m.length>n.length&&m.indexOf(n)>-1&&m.length-n.length<n.length)E.push('שורה שחוזרת בתוך שורה אחרת: '+r.p.slice(0,40))})});
      /* א5: סמלילים מיותרים */
      R.forEach(function(r){var p=r.p;
        if(/(^|\s)•(\s|$)/.test(p)||/:\s*•/.test(p))E.push('סמליל מיותר (•): '+p.slice(0,40));
        if(/[א-ת'"]\.-[א-ת]/.test(p)||/(^|\s)-[א-ת]/.test(p))E.push('מקף מיותר צמוד למילה: '+p.slice(0,40));
        /* א6: ניקיון */
        if(/\s[,.:;!?](?![.])/.test(p))E.push('רווח לפני פיסוק: '+p.slice(0,40));
        if(/[,;:!?][א-ת]/.test(p.replace(/[א-ת]"[א-ת]/g,'')))E.push('חסר רווח אחרי פיסוק: '+p.slice(0,40));
        if(/\.\(/.test(p))E.push('חסר רווח בין נקודה לסוגריים: '+p.slice(0,40));
        if(/[א-ת]''[א-ת]/.test(p))E.push("גרשיים כפולים ('') במקום גרשיים (\"): "+p.slice(0,40));
        if(/[א-ת]\.[א-ת]/.test(p.replace(/(^|\s)[א-י]\.\s?/g,' ')))E.push('חסר רווח אחרי נקודה: '+p.slice(0,40))});
      /* א4: מספור א. ב. ג. של אותה רשימה - כולו בכותרת צד או כולו בגוף */
      var pos=[];parse(text).forEach(function(k){if(k.t==='title'){var m=/^([א-י])\./.exec(plainI(k.v).trim());if(m)pos.push([HV[m[1]],'צד'])}
        else if(k.t==='line'){var m2=/^([א-י])\.\s/.exec(plainI(k.v).trim());if(m2)pos.push([HV[m2[1]],'גוף'])}});
      for(var i=1;i<pos.length;i++)if(pos[i][0]===pos[i-1][0]+1&&pos[i][1]!==pos[i-1][1])
        E.push('מספור לא עקבי: '+'אבגדהוזחטי'[pos[i-1][0]-1]+'. ב'+pos[i-1][1]+' ו-'+'אבגדהוזחטי'[pos[i][0]-1]+'. ב'+pos[i][1]);
      /* א2-א3: תיבת המשנה - רק לשון המשנה, מנוקדת */
      /* השוואה לפי שלד: כתיב מלא מול חסר (מדובללת / מדבללת) ואותיות סופיות אינם הבדל */
      var skel=function(t){return qnorm(t).replace(/[וי]/g,'').replace(/ך/g,'כ').replace(/ם/g,'מ').replace(/ן/g,'נ').replace(/ף/g,'פ').replace(/ץ/g,'צ')};
      /* שורת משנה (משנה): רק השורה האחרונה שלפני [משנה] (6.11.2026) */
      var TK=parse(text).filter(function(k){return !(k.t==='lock'&&k.kind==='מקור')});
      TK.forEach(function(k,i){if(k.t!=='line'||k.sty!=='mi')return;var nx=TK[i+1];
        if(!nx||nx.t!=='lock'||nx.kind!=='משנה')E.push('(משנה) מותר רק בשורה שמיד לפני [משנה]: '+plainI(k.v).slice(0,40))});
      if(o.mishna){var src=' '+skel(o.mishna)+' ',inM=false;
        var ratio=function(p){var w=skel(p).split(' ').filter(function(x){return x.length>1});if(w.length<2)return -1;
          return w.filter(function(x){return src.indexOf(' '+x+' ')>-1||src.indexOf(x)>-1}).length/w.length};
        TK.forEach(function(k,i){
          if(k.t==='lock'){inM=k.kind==='משנה';return}
          if(k.t!=='line')return;
          var p=plainI(k.v),r=ratio(p);if(r<0)return;
          if(inM||k.sty==='mi'){
            /* הניקוד מועתק בבנייה מן המשנה המנוקדת רק למילה שאותיותיה זהות למקור (nikud_mishna.py): שורה רחוקה מן המקור
               היא גם טקסט זר וגם משנה שלא תנוקד */
            if(r<0.6)E.push('טקסט שאינו מן המשנה בתוך תיבת המשנה (וגם לא ינוקד): '+p.slice(0,40));return}
          /* שורה מלשון המשנה שעומדת מחוץ לתיבה, מיד לפניה (סוכה כו: "מעשה והביאו לריב"ז") - נכנסת לתיבה */
          /* רק שורה בסגנון "רווח לפני" (כך נכתבה בוורד שורת הפתיחה של המשנה שנשארה מחוץ לתיבה), מלשון המשנה,
             שמיד אחריה [משנה]. שורת גמרא שמסכמת את המשנה (סוכה כא: "א. עבדים פטורים...") אינה בסגנון הזה */
          var nx=TK[i+1];
          if(k.sty==='sp'&&nx&&nx.t==='lock'&&nx.kind==="משנה"&&r>=0.6&&p.split(/\s+/).length>=3)
            E.push('שורה מלשון המשנה מחוץ לתיבה, מיד לפניה - לסמן (משנה) בראש השורה: '+p.slice(0,40))})}
      return E}
    /* ---- החזרת עוגנים שבתוך השורה ([תוס':N], [מס:N]) אחרי עריכה ידנית (פרומפט 20, 5.11.2026) ----
       עריכה של המנהל לעולם אינה נפסלת בגלל עוגן שנמחק או זז: עוגן שחסר מוחזר אחרי המילים
       שקדמו לו במקור (אם הן עדיין בנוסח), ואם לא - במקום היחסי שלו, בסוף מילה. כשסדר העוגנים
       בנוסח הערוך שונה מן המקור, כולם מוסרים ומוחזרים לפי אותו כלל, בסדר המקור.
       מחזיר {text, moved:[שמות העוגנים שהוחזרו למקום משוער]} */
    var INL=/\[(תוס'|מס):([^\]]{1,12})\]/g;
    function inlScan(text){
      /* מפת התווים הנקיים (בלי סימנים, בלי ניקוד, בלי שורות נעולות) -> מקומם בטקסט */
      var P=[],I=[],A=[],lines=String(text).split('\n'),off=0;
      lines.forEach(function(ln){
        var t=ln.trim(),lock=LOCK_RE.test(t);
        if(!lock){
          var i=0,ls=P.length;
          var m0=/^\s*(\((?:תשובה|רווח|נושא|דה|רקע|נקודה)\)\s*|\[צד:)/.exec(ln),end=ln.length;if(m0)i=m0[0].length;
          if(m0&&m0[1]==='[צד:'&&/\]\s*$/.test(ln))end=ln.lastIndexOf(']');
          while(i<end){
            var c=ln[i];
            if(c==='['){var mm=/^\[(תוס'|מס):([^\]]{1,12})\]/.exec(ln.slice(i,i+20));
              if(mm){A.push({k:mm[1]+':'+mm[2],s:mm[0],at:off+i,pl:P.length,ls:P.length===ls});i+=mm[0].length;continue}}
            if(c==='{'){var tb=/^\{(טאב|ריק)\}/.exec(ln.slice(i,i+6));if(tb){i+=tb[0].length;continue}
              var op=/^\{[^{}:\s]{1,4}:/.exec(ln.slice(i,i+8));if(op){i+=op[0].length;continue}}
            if(c==='}'){i++;continue}
            if(/[֑-ׇ"'״׳]/.test(c)){i++;continue}
            P.push(/\s/.test(c)?' ':c);I.push(off+i);i++}
          P.push(' ');I.push(off+ln.length)}
        off+=ln.length+1});
      return {p:P.join(''),i:I,a:A}}
    function fixInline(orig,text){
      var O=inlScan(orig),T=inlScan(text),moved=[];
      var ok=O.a.map(function(x){return x.k}),tk=T.a.map(function(x){return x.k});
      if(ok.join('|')===tk.join('|'))return {text:text,moved:moved};
      /* האם העוגנים שבנוסח הם תת-סדרה של המקור, באותו סדר (רק חסרים)? */
      var keep=[],j=0;
      for(var q=0;q<ok.length&&j<tk.length;q++)if(ok[q]===tk[j]){keep[q]=T.a[j];j++}
      var sub=j===tk.length&&tk.every(function(k){return ok.indexOf(k)>-1});
      if(!sub){
        /* סדר אחר או עוגן זר: מסירים את כל העוגנים שבנוסח ומחזירים את כולם */
        text=String(text).replace(INL,'');T=inlScan(text);keep=[]}
      var ins=[];  /* {pos (מקום בטקסט), s} */
      var Tp=T.p,n=O.a.length;
      function plOf(q){return keep[q]?keep[q].pl:null}
      for(var q2=0;q2<n;q2++){
        if(keep[q2])continue;
        var a=O.a[q2];
        /* הגבולות: אחרי העוגן הקודם ולפני הבא (בתווים הנקיים של הנוסח) */
        var lo=0,hi=Tp.length;
        for(var b=q2-1;b>=0;b--){var x=plOf(b);if(x!==null){lo=x;break}
          var y=ins.filter(function(z){return z.q===b})[0];if(y){lo=y.pl;break}}
        for(var c2=q2+1;c2<n;c2++){var x2=plOf(c2);if(x2!==null){hi=x2;break}}
        var ctx=O.p.slice(Math.max(0,a.pl-14),a.pl).replace(/^\S*\s/,'').replace(/\s+$/,'');
        var pl=-1;
        [ctx,ctx.slice(-7)].some(function(cx){
          if(cx.replace(/\s/g,'').length<3)return false;
          var f=Tp.indexOf(cx,lo);
          if(f>-1&&f+cx.length<=hi){pl=f+cx.length;return true}return false});
        var guess=pl<0;
        if(guess){
          var ratio=O.p.length?a.pl/O.p.length:0;
          pl=Math.max(lo,Math.min(hi,Math.round(ratio*Tp.length)));
          /* סוף מילה */
          while(pl<hi&&pl<Tp.length&&Tp[pl]!==' ')pl++;
          moved.push(a.k.replace(':',' '))}
        /* מקום בטקסט: אחרי התו הנקי האחרון שלפני pl, ואחרי סוגרי סימנים שצמודים לו */
        var pos;
        if(pl<=0)pos=T.i.length?T.i[0]:0;
        else{pos=T.i[pl-1]+1;while(pos<text.length&&text[pos]==='}')pos++;
          /* עוגן שעמד בפתח שורה (מספר משנה) - בפתח השורה הבאה, אחרי סימן הסגנון */
          if(a.ls){var nl=text.indexOf('\n',pos-1);if(nl>-1){pos=nl+1;
            var pf=/^(\((?:תשובה|רווח|נושא|דה|רקע|נקודה)\)\s*)/.exec(text.slice(pos,pos+12));if(pf)pos+=pf[0].length}}}
        ins.push({q:q2,pl:pl,pos:pos,s:a.s})}
      ins.sort(function(x,y){return y.pos-x.pos||y.q-x.q});
      ins.forEach(function(z){text=text.slice(0,z.pos)+z.s+text.slice(z.pos)});
      return {text:text,moved:moved}}
    /* =========== מחיקת עיטור ליד כותרת (פרומפט 27, 8.11.2026) ===========
       הכרעת בעל הפרויקט: הכותרת עצמה היא החציצה, ולכן עיטור שצמוד לכותרת נושא או לכותרת ד"ה נמחק.
       [קבוע] נשאר נעול לכל דבר אחר. ההצעה כותבת במקום השורה [קבוע:<מזהה>] את השורה [מחק-עיטור:<מזהה>].
       hatzDel מוציא את שתיהן (מן המקור ומן ההצעה), וכל השאר (השומר, השחזור, ההחלה) עובד כרגיל.
       מי שמחיל מוחק את העיטור עצמו (hdel: אותו מנגנון כמו "מחק עיטור" בעורך - עד הוורד). */
    var HDEL_RE=/^\s*\[מחק-עיטור:(\d+)\]\s*$/;
    function hatzDel(orig,text){
      var ids=[],bad=[],seen={};
      var T=String(text||'').split('\n').filter(function(s){var m=HDEL_RE.exec(s);if(m){ids.push(+m[1]);return false}return true});
      if(!ids.length)return {orig:orig,text:text,ids:[],bad:[]};
      var O=String(orig||'').split('\n').filter(function(s){var m=/^\s*\[קבוע:(\d+)\]\s*$/.exec(s);if(m&&ids.indexOf(+m[1])>-1){seen[m[1]]=1;return false}return true});
      ids.forEach(function(id){if(!seen[id])bad.push(id)});
      return {orig:O.join('\n'),text:T.join('\n'),ids:ids,bad:bad}}
    /* האם השורה היא כותרת (נושא / ד"ה) */
    function isHeadLine(s){s=String(s||'').trim();return /^\((נושא|דה)\)/.test(s)||/^\[כותרת-(נושא|דה)/.test(s)||/^\{(נושא|דה):/.test(s)}
    /* העיטור צמוד לכותרת: השורה שמעליו או שמתחתיו (בדילוג על [מקור], [דף] וכותרות צד) היא כותרת */
    function hatzNearHead(text,id){
      var L=String(text||'').split('\n'),i=-1,k,m;
      for(k=0;k<L.length;k++){m=HDEL_RE.exec(L[k]);if(m&&+m[1]===+id){i=k;break}}
      if(i<0)return false;
      var skip=function(s){return !String(s).trim()||/^\s*\[(מקור|דף|צד)[:\]]/.test(s)};
      /* כותרת נושא שבדף שמורה לעתים ככותרת צד ארוכה ([צד:המוכר שטר לחבירו]) - גם היא כותרת לעניין זה */
      var topic=function(s){var m=/^\s*\[צד:(.+)\]\s*$/.exec(s);if(!m)return false;var v=m[1].trim();return !/:$/.test(v)&&!/^[א-ת]{1,2}\.$/.test(v)&&v.split(/\s+/).length>=2};
      var head=function(s){return isHeadLine(s)||topic(s)};
      for(k=i-1;k>=0;k--){if(head(L[k]))return true;if(skip(L[k]))continue;break}
      for(k=i+1;k<L.length;k++){if(head(L[k]))return true;if(skip(L[k]))continue;return false}
      return false}
    return {hatzDel:hatzDel,hatzNearHead:hatzNearHead,isHeadLine:isHeadLine,h2i:h2i,i2h:i2h,bare:bare,plainI:plainI,toInter:toInter,parse:parse,locks:locks,segments:segments,guard:guard,check:check,autofixTitles:autofixTitles,titleIssues:titleIssues,titleLen:titleLen,splitTitle:splitTitle,shortSide:shortSide,speakerTitle:speakerTitle,overlapN:overlapN,fixInline:fixInline,T2C_OK:function(t){return !!T2C[t]||t==='+'||t==='!'},
            quality:quality,qnorm:qnorm,aramNew:aramNew,aramWords:aramWords,squeeze:squeeze,SQ:{SEG:SQ_SEG,LINE:SQ_LINE,MIN:SQ_MIN},C2T:C2T,P2T:P2T,T2P:T2P,LINE:LINE,spans:spans,rows:rows,numOf:numOf,nums:nums,newHs:newHs,movedNames:movedNames,diffKinds:diffKinds,nbase:nbase,pnorm:pnorm}
  })();
  if(typeof module!=='undefined'&&module.exports)module.exports=SKC;
