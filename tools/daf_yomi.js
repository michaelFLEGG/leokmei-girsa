/* daf-yomi.js - הדף היומי, מחושב בדפדפן לפי התאריך המקומי, בלי פנייה לרשת.
   מחזור 14 החל ב-5.1.2020 (ברכות ב.). המחזור הבא מתחיל מיד אחרי סיומו, ולכן
   החישוב ממשיך מעצמו. נבדק מול hebcal: שבת ב. (8.3.2020), גיטין ב. (18.5.2023),
   בכורות טז. (4.10.2026). אורך המחזור 2711 ימים. */
(function(){
  var L=[['ברכות','berakhot',2,63],['שבת','shabbat',2,156],['עירובין','eruvin',2,104],['פסחים','pesachim',2,120],
    ['שקלים','shekalim',2,21],['יומא','yoma',2,87],['סוכה','sukkah',2,55],['ביצה','beitzah',2,39],
    ['ראש השנה','rosh-hashanah',2,34],['תענית','taanit',2,30],['מגילה','megillah',2,31],['מועד קטן','moed-katan',2,28],
    ['חגיגה','chagigah',2,26],['יבמות','yevamot',2,121],['כתובות','ketubot',2,111],['נדרים','nedarim',2,90],
    ['נזיר','nazir',2,65],['סוטה','sotah',2,48],['גיטין','gittin',2,89],['קידושין','kiddushin',2,81],
    ['בבא קמא','bava-kamma',2,118],['בבא מציעא','bava-metzia',2,118],['בבא בתרא','bava-batra',2,175],
    ['סנהדרין','sanhedrin',2,112],['מכות','makkot',2,23],['שבועות','shevuot',2,48],['עבודה זרה','avodah-zarah',2,75],
    ['הוריות','horayot',2,13],['זבחים','zevachim',2,119],['מנחות','menachot',2,109],['חולין','chullin',2,141],
    ['בכורות','bekhorot',2,60],['ערכין','arakhin',2,33],['תמורה','temurah',2,33],['כריתות','keritot',2,27],
    ['מעילה','meilah',2,21],['קינים','kinnim',23,3],['תמיד','tamid',26,8],['מדות','middot',34,5],['נדה','niddah',3,71]];
  var CYCLE=0;L.forEach(function(x){CYCLE+=x[3]});
  var START=Date.UTC(2020,0,5);
  function heb(n){var t='',s=[[400,'ת'],[300,'ש'],[200,'ר'],[100,'ק'],[90,'צ'],[80,'פ'],[70,'ע'],[60,'ס'],[50,'נ'],[40,'מ'],[30,'ל'],[20,'כ'],[10,'י'],[9,'ט'],[8,'ח'],[7,'ז'],[6,'ו'],[5,'ה'],[4,'ד'],[3,'ג'],[2,'ב'],[1,'א']];
    if(n===15)return 'טו';if(n===16)return 'טז';
    s.forEach(function(p){while(n>=p[0]){t+=p[1];n-=p[0]}});return t}
  function today(d){d=d||new Date();
    var days=Math.floor((Date.UTC(d.getFullYear(),d.getMonth(),d.getDate())-START)/86400000);
    var k=((days%CYCLE)+CYCLE)%CYCLE;
    for(var i=0;i<L.length;i++){if(k<L[i][3]){var n=L[i][2]+k;
      return {name:L[i][0],slug:L[i][1],n:n,daf:heb(n)+'.',label:heb(n)}}k-=L[i][3]}}
  /* נוסף 6.10.2026 למערכת הלומד: חישוב לתאריך נתון (שנה, חודש, יום) ללא תלות באזור הזמן
     של המכשיר, הרשימה המלאה, ומספר המחזור (המחזור ה-14 התחיל ב-5.1.2020). */
  function forYMD(y,m,d){
    var days=Math.floor((Date.UTC(y,m-1,d)-START)/86400000);
    var cyc=Math.floor(days/CYCLE);
    var k=((days%CYCLE)+CYCLE)%CYCLE, idx=k;
    for(var i=0;i<L.length;i++){if(k<L[i][3]){var n=L[i][2]+k;
      return {name:L[i][0],slug:L[i][1],n:n,daf:heb(n)+'.',label:heb(n),cycle:14+cyc,index:idx}}k-=L[i][3]}}
  function forStr(s){var a=String(s).split('-');return forYMD(+a[0],+a[1],+a[2])}
  window.LGDaf={today:today,heb:heb,cycle:CYCLE,forYMD:forYMD,forStr:forStr,list:function(){return L},START:START};
})();
