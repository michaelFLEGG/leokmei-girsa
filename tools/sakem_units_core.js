  /* =================== סקירה פנימית: פירוק הצעה ליחידות (פרומפט 75, 21.11.2026) ===================
     מיכאל: "יש דברים שאני רוצה לקבל ויש דברים שאני רוצה לדחות... תיקון אחרי תיקון - קבל, דחה או ערוך".
     הצעת סכם היא נוסח ביניים (sakem_core.js) מול הנוסח המקורי. כאן היא מתפרקת ל"יחידות": כל שינוי בודד ברמת
     מילה - מחיקה, תוספת או החלפה (מחיקה ותוספת צמודות, או מופרדות ברווח בלבד, הן יחידה אחת) - וגם שינוי סגנון
     ({אם:..}, {ב:..}, (רווח), (נושא), [צד:..]) או מבנה (איחוד שורות, פיצול שורה, עיטור). סוגר מסולסל לעולם אינו
     נחצה: יחידה שפותחת סגנון בלי לסגור אותו מתאחדת עם היחידה שסוגרת אותו, כך שכל צירוף של הכרעות נותן נוסח תקין.
     compose מרכיב את הנוסח מכל צירוף הכרעות: הכל "קבל" = ההצעה כלשונה, הכל "דחה" = המקור כלשונו.
     classify משחזר מנוסח סופי (היומן של /sakem/dec: orig, prop, final) מה הוכרע בכל יחידה - לדוח הלמידה.
     הקובץ טהור (בלי DOM): רץ בדף ובבדיקות node (tools/sakem_tests/p75_units.mjs). */
  var SKU=(function(){
    var PRE=/^\((תשובה|רווח|נושא|דה|רקע|נקודה|משנה|מעוין)\) ?/;
    /* אסימונים: שורה חדשה, סגנון בראש שורה, נעול [...], פותח סגנון {xx:, סוגר }, רווח, מילה */
    function tokens(s){
      s=String(s||'');var out=[],i=0,bol=true;
      while(i<s.length){
        var c=s[i],m,r=s.slice(i,i+400);
        if(c==='\n'){out.push({k:'nl',v:'\n'});i++;bol=true;continue}
        if(bol&&(m=PRE.exec(r))){out.push({k:'pre',v:m[0]});i+=m[0].length;bol=false;continue}
        bol=false;
        if(c==='['&&(m=/^\[[^\]\n]{0,300}\]/.exec(r))){out.push({k:'lock',v:m[0]});i+=m[0].length;continue}
        if(c==='{'&&(m=/^\{(טאב|ריק)\}/.exec(r))){out.push({k:'word',v:m[0]});i+=m[0].length;continue}
        if(c==='{'&&(m=/^\{[^{}:\s]{1,4}:/.exec(r))){out.push({k:'open',v:m[0]});i+=m[0].length;continue}
        if(c==='}'){out.push({k:'close',v:'}'});i++;continue}
        if((m=/^[ \t]+/.exec(r))){out.push({k:'ws',v:m[0]});i+=m[0].length;continue}
        if((m=/^[^\s{}\[\]]+/.exec(r))){out.push({k:'word',v:m[0]});i+=m[0].length;continue}
        out.push({k:'word',v:c});i++}
      return out}
    /* LCS לפי הירשברג (זיכרון ליניארי), כמו skpLcs בדף */
    function lcs(A,B){
      var pairs=[];
      function row(a0,a1,b0,b1,rev){var m=b1-b0,pr=new Int32Array(m+1),cu=new Int32Array(m+1);
        for(var i=0;i<a1-a0;i++){var ai=rev?A[a1-1-i]:A[a0+i];cu[0]=0;
          for(var j=1;j<=m;j++){var bj=rev?B[b1-j]:B[b0+j-1];cu[j]=ai===bj?pr[j-1]+1:(pr[j]>cu[j-1]?pr[j]:cu[j-1])}
          var t=pr;pr=cu;cu=t}
        return pr}
      function small(a0,a1,b0,b1){var n=a1-a0,m=b1-b0,L=[];for(var q=0;q<=n;q++)L.push(new Int32Array(m+1));
        for(var i=n-1;i>=0;i--)for(var j=m-1;j>=0;j--)L[i][j]=A[a0+i]===B[b0+j]?L[i+1][j+1]+1:Math.max(L[i+1][j],L[i][j+1]);
        var x=0,y=0;while(x<n&&y<m){if(A[a0+x]===B[b0+y]){pairs.push([a0+x,b0+y]);x++;y++}else if(L[x+1][y]>=L[x][y+1])x++;else y++}}
      function go(a0,a1,b0,b1){
        while(a0<a1&&b0<b1&&A[a0]===B[b0]){pairs.push([a0,b0]);a0++;b0++}
        var tail=[];while(a1>a0&&b1>b0&&A[a1-1]===B[b1-1]){a1--;b1--;tail.push([a1,b1])}
        if(a1>a0&&b1>b0){
          if((a1-a0)*(b1-b0)<=250000||a1-a0<2)small(a0,a1,b0,b1);
          else{var mid=(a0+a1)>>1,L1=row(a0,mid,b0,b1,false),L2=row(mid,a1,b0,b1,true),m=b1-b0,k=0,best=-1;
            for(var j=0;j<=m;j++){var v=L1[j]+L2[m-j];if(v>best){best=v;k=j}}
            go(a0,mid,b0,b0+k);go(mid,a1,b0+k,b1)}}
        for(var t=tail.length-1;t>=0;t--)pairs.push(tail[t])}
      go(0,A.length,0,B.length);return pairs}
    /* רצף פעולות: eq / del / ins, לפי סדר הנוסח. מחיקה לפני תוספת באותו מקום */
    function ops(a,b){
      var P=lcs(a.map(function(t){return t.v}),b.map(function(t){return t.v})),o=[],i=0,j=0;
      P.concat([[a.length,b.length]]).forEach(function(p){
        while(i<p[0]){o.push({t:'del',a:a[i],ai:i});i++}
        while(j<p[1]){o.push({t:'ins',b:b[j],bi:j});j++}
        if(i<a.length&&j<b.length&&p[0]<a.length){o.push({t:'eq',a:a[i],b:b[j],ai:i,bi:j});i++;j++}});
      return o}
    function side(o,s,e,w){var r=[];for(var q=s;q<e;q++){var x=o[q];if(x.t==='eq'||(w==='a'?x.t==='del':x.t==='ins'))r.push(w==='a'?x.a:x.b)}return r}
    function txt(ts){return ts.map(function(t){return t.v}).join('')}
    function bal(ts){var d=0,lo=0;ts.forEach(function(t){if(t.k==='open')d++;else if(t.k==='close'){d--;if(d<lo)lo=d}});return {d:d,lo:lo}}
    var LAB={'אם':'אמוראים','ב':'הדגשה','הס':'הסבר','פס':'פסוק','דה':'ד"ה','נש':'נושא משנה','מש':'משנה','כב':'כותרת בשורה','אות':'אות פותחת','מפ':'מפרשים','+':'השלמה מהגמרא','!':'תיקון תוכן'};
    var PLAB={'רווח':'רווח לפני','נושא':'כותרת נושא','תשובה':'תשובה','דה':'ד"ה','רקע':'רקע','נקודה':'נקודה','משנה':'שורת משנה','מעוין':'מעוין'};
    /* סוג היחידה, לפי מה שהשתנה בה (לא לפי מה שנשאר זהה בתוכה) */
    function kindOf(ch){
      var dels=ch.filter(function(x){return x.t==='del'}).map(function(x){return x.a}),ins=ch.filter(function(x){return x.t==='ins'}).map(function(x){return x.b}),all=dels.concat(ins);
      var f=function(re){return all.filter(function(t){return re.test(t.v)})[0]};
      var t;
      if((t=f(/^\{\+:/)))return {k:'השלמה',l:'השלמה מהגמרא'};
      if((t=f(/^\[צד:/)))return {k:'כותרת צד',l:'כותרת צד'};
      if((t=f(/^\[(מחק-עיטור|קבוע):/)))return {k:'עיטור',l:'עיטור'};
      if((t=f(/^\[כותרת-/)))return {k:'כותרת',l:'כותרת'};
      if((t=all.filter(function(x){return x.k==='pre'})[0])){var n=/^\(([^)]+)\)/.exec(t.v)[1];return {k:'סגנון:'+n,l:'סגנון שורה: '+(PLAB[n]||n)}}
      if((t=all.filter(function(x){return x.k==='open'})[0])){var c=/^\{([^:]+):/.exec(t.v)[1];return {k:'סגנון:'+c,l:LAB[c]||'סגנון'}}
      if(all.some(function(x){return x.k==='lock'}))return {k:'נעול',l:'שינוי בסימון נעול'};
      var w=function(a){return a.some(function(x){return x.k==='word'})};
      var dn=dels.some(function(x){return x.k==='nl'}),inn=ins.some(function(x){return x.k==='nl'});
      if(!w(dels)&&!w(ins)){if(dn&&!inn)return {k:'איחוד שורות',l:'איחוד שורות'};if(inn&&!dn)return {k:'פיצול שורה',l:'פיצול שורה'};return {k:'רווח',l:'רווח'}}
      if(w(dels)&&w(ins))return {k:'החלפה',l:'החלפה'};
      return w(dels)?{k:'מחיקה',l:'מחיקה'}:{k:'תוספת',l:'תוספת'}}
    /* היחידות: רצפי שינוי, איחוד מעל רווח בלבד, ואיחוד עד שהסוגריים המסולסלים מאוזנים בשני הצדדים */
    function units(orig,text){
      var a=tokens(orig),b=tokens(text),o=ops(a,b),H=[],q=0;
      while(q<o.length){if(o[q].t==='eq'){q++;continue}var s=q;while(q<o.length&&o[q].t!=='eq')q++;H.push({s:s,e:q})}
      /* רווח בודד בין שני שינויים: יחידה אחת ("החלפה" של צירוף) */
      for(var h=H.length-2;h>=0;h--){var g=o.slice(H[h].e,H[h+1].s);if(g.length===1&&g[0].a.k==='ws'){H[h].e=H[h+1].e;H.splice(h+1,1)}}
      for(var guard=0;guard<10000;guard++){var moved=false;
        for(h=0;h<H.length;h++){
          var A=bal(side(o,H[h].s,H[h].e,'a')),B=bal(side(o,H[h].s,H[h].e,'b'));
          if((A.lo<0||B.lo<0)&&h>0){H[h-1].e=H[h].e;H.splice(h,1);moved=true;break}
          if((A.d>0||B.d>0||A.lo<0||B.lo<0)&&h<H.length-1){H[h].e=H[h+1].e;H.splice(h+1,1);moved=true;break}}
        if(!moved)break}
      var U=H.map(function(x,i){var ch=o.slice(x.s,x.e).filter(function(y){return y.t!=='eq'});
        var A=side(o,x.s,x.e,'a'),B=side(o,x.s,x.e,'b'),K=kindOf(ch);
        return {id:i,s:x.s,e:x.e,a:txt(A),b:txt(B),kind:K.k,label:K.l,
          /* שינוי בלתי נראה (רווחים בלבד) - מתקבל לבד ואינו מוצג */
          quiet:A.concat(B).every(function(t){return t.k==='ws'})||txt(A).replace(/[ \t]+/g,' ')===txt(B).replace(/[ \t]+/g,' ')}});
      return {a:a,b:b,o:o,u:U,orig:String(orig||''),text:String(text||'')}}
    /* הנוסח מצירוף הכרעות: dec[id] = 'a' (קבל) | 'r' (דחה) | {e:'...'} (ערוך) | חסר = def ('a' או 'r') */
    function compose(M,dec,def){
      dec=dec||{};var out='',q=0,ui=0,U=M.u;
      while(q<M.o.length){
        var u=U[ui];
        if(u&&q===u.s){var d=u.quiet?'a':(dec[u.id]!==undefined?dec[u.id]:(def||'a'));
          out+=d&&typeof d==='object'?String(d.e):(d==='r'?u.a:u.b);q=u.e;ui++;continue}
        var x=M.o[q];if(x.t==='eq')out+=x.b.v;q++}
      return out}
    /* שחזור ההכרעות מנוסח סופי: יחידה שלא נגעו בה ביחס להצעה - התקבלה; ביחס למקור - נדחתה; אחרת - נערכה */
    function untouched(X,Y,ranges){
      var o=ops(X,Y),mt=new Array(X.length).fill(false),gap=new Array(X.length+1).fill(false),i=0;
      o.forEach(function(p){if(p.t==='eq'){mt[p.ai]=true;i=p.ai+1}else if(p.t==='del')i=p.ai+1;else gap[i]=true});
      return ranges.map(function(r){if(r[0]===r[1])return !gap[r[0]];
        for(var k=r[0];k<r[1];k++)if(!mt[k])return false;for(k=r[0]+1;k<r[1];k++)if(gap[k])return false;return true})}
    function classify(orig,text,fin){
      var M=units(orig,text),F=tokens(fin);
      var rg=function(w){return M.u.map(function(u){var xs=M.o.slice(u.s,u.e).filter(function(p){return w==='a'?p.t!=='ins':p.t!=='del'}).map(function(p){return w==='a'?p.ai:p.bi});
        if(xs.length)return [Math.min.apply(null,xs),Math.max.apply(null,xs)+1];
        /* טווח ריק: המקום שבו היה השינוי */
        for(var q=u.s-1;q>=0;q--){var p=M.o[q];if(p.t==='eq'||p.t===(w==='a'?'del':'ins'))return [(w==='a'?p.ai:p.bi)+1,(w==='a'?p.ai:p.bi)+1]}
        return [0,0]})};
      var acc=untouched(M.b,F,rg('b')),rej=untouched(M.a,F,rg('a'));
      return M.u.filter(function(u){return !u.quiet}).map(function(u){return {id:u.id,kind:u.kind,label:u.label,a:u.a,b:u.b,dec:acc[u.id]?'accept':rej[u.id]?'reject':'edit'}})}
    function sig(orig,text){var s=String(orig||'')+'\u0001'+String(text||''),h=5381;for(var i=0;i<s.length;i++)h=((h<<5)+h+s.charCodeAt(i))|0;return (h>>>0).toString(36)+'.'+s.length}
    return {tokens:tokens,units:units,compose:compose,classify:classify,sig:sig}})();
  if(typeof module!=='undefined'&&module.exports)module.exports=SKU;
