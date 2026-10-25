  /* =================== חברותא: החיבור לסרגל הסקירה (19.10.2026; הופרד 25.10.2026) ===================
     רכיב התצוגה עצמו (hv_ui.js) משותף לכל המסכתות, ומשמש גם את לשונית "חברותא" במגירת המקור.
     כאן רק מה שתלוי בסקירה (skira_ui.js), ולכן נטען אחריה, רק במסכת שיש לה בקרה. */
  /* הצמדה: כל מעבר בין הערות (skAfterGo) מרענן את הלוח; כפתור ההפעלה בסרגל */
  (function(){
    const prevGo=window.skAfterGo;
    window.skAfterGo=function(f){if(typeof prevGo==='function')prevGo(f);try{hvShow(f)}catch(e){}};
    const prevBar=window.skBarExtra;
    window.skBarExtra=function(m){if(typeof prevBar==='function')prevBar(m);if(!m)return;
      m.insertAdjacentHTML('beforeend','<button class="'+(HV.on?'on':'')+'" onclick="hvToggle()" title="ביאור חברותא בצד ההערה (חומר עיון למנהל בלבד)">חברותא</button>')};
  })();
  /* הלוח היה פתוח ברענון: חוזר לפתוח על הדף הנוכחי */
  setTimeout(()=>{if(HV.on&&isAdmin()&&admKey()){const f=BK.byId[BK.curId];if(f)hvShow(f);else hvOpenDaf(bkDafNow()||(hvDafs()[0]||''),null)}},2600);
