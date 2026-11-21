  /* =================== סקירה במגע: טאבלט וטלפון (פרומפט 74, 21.11.2026) ===================
     רק במכשיר מגע (pointer: coarse). במחשב הקובץ אינו עושה דבר: כל הקיצורים והמראה נשארים בדיוק כמו קודם.
     סרגל פעולות אחד קבוע בתחתית המסך, לכל מצבי הסקירה: "קבל", "דחה", "ערוך", "הקודם", "הבא בתור", ו"פרטים".
     הכפתורים אינם מסלול חדש: כל אחד קורא לפעולה הקיימת של המצב (skpAct בסכם, ovAct בשורה שהתארכה,
     sqDecide בתור ההצעות, הכפתורים של מצב דפוס), ולכן השמירה, הפרסום והביטול הם אותם מסלולים.
       - התוכן מקבל ריפוד תחתון בגובה הסרגל, והסרגל של המצב עצמו (בסכם: שורת המונים והכפתורים הנוספים)
         נפתח רק בהקשה על "פרטים", בחלון תחתון שנסגר בהחלקה למטה.
       - החלקה ימינה/שמאלה על הטקסט: ניווט בלבד (בכיוון עברי, כמו בדף: ימינה = הבא). אף פעם לא קבלה או דחייה.
       - הקשה כפולה על הקטע: עריכה.
       - אחרי "קבל" או "דחה": "בטל" קטן לכמה שניות.
       - מקלדת וירטואלית פתוחה: הסרגל עולה מעליה, ובזמן עריכה הוא מתקצר ל"סיים וקבל" / "בטל עריכה". */
  (function(){
    if(!(window.matchMedia&&matchMedia('(pointer:coarse)').matches))return;
    if(new URLSearchParams(location.search).get('print')==='1')return;
    const H=document.documentElement;H.classList.add('tch');
    const TR={mode:null,bar:null,sheet:null,undo:null,ut:0,kb:0,sig:''};
    const IC={
      prev:'<path d="M9 6l6 6-6 6"/>',next:'<path d="M15 6l-6 6 6 6"/>',
      ok:'<path d="M5 12.5l4.5 4.5L19 7.5"/>',no:'<path d="M6.5 6.5l11 11M17.5 6.5l-11 11"/>',
      edit:'<path d="M4 20h4L19 9l-4-4L4 16z"/><path d="M13.5 6.5l4 4"/>',more:'<circle cx="6" cy="12" r="1.4"/><circle cx="12" cy="12" r="1.4"/><circle cx="18" cy="12" r="1.4"/>',
      undo:'<path d="M9 7L4 12l5 5"/><path d="M4 12h10a6 6 0 010 12"/>',x:'<path d="M6.5 6.5l11 11M17.5 6.5l-11 11"/>',
      page:'<path d="M6 3h9l3 3v15H6z"/><path d="M9 10h6M9 14h6"/>'};
    const svg=n=>'<svg viewBox="0 0 24 24" aria-hidden="true">'+IC[n]+'</svg>';
    const q=s=>document.querySelector(s);
    const call=f=>{try{return f()}catch(e){try{console.warn('touch',e)}catch(_){}}};
    function buzz(){try{navigator.vibrate&&navigator.vibrate(8)}catch(e){}}

    /* ---- המצבים: מי פעיל, אילו כפתורים, ומה כל כפתור עושה ---- */
    const MODES=[
      {id:'skp',name:'סכם',
        on:()=>typeof SKP!=='undefined'&&!!SKP.rev&&!!q('#skpbar'),
        editing:()=>!!(SKM.ghost&&SKM.ghost.classList.contains('edit')),
        btns:()=>{const R=SKP.rev,it=R&&R.items[R.i];return {prev:'הקודם',ok:R.conflict?'קבל הצעה':'קבל',no:R.conflict?'השאר שלי':'דחה',
          edit:it&&it.kind==='seg'?'ערוך':'',next:'הבא בתור',more:'פרטים'}},
        act:a=>{const R=SKP.rev;if(!R)return;
          if(a==='ok')skpAct(R.conflict?'force':'ok');else if(a==='no')skpAct(R.conflict?'keep':'no');
          else if(a==='edit')skpAct('edit');else if(a==='next')skpAct('next');else if(a==='prev')skpAct('prev')},
        doneEdit:ok=>{const R=SKP.rev;if(!R)return;if(ok)skpAccept(R.conflict);else skpShow()},
        undo:()=>skpUndo(),
        target:t=>!!(t&&t.closest&&!t.closest('#bar,#mtop,#topbar,.panel,#msheet,.modal,#skptagm'))},
      {id:'ov',name:'שורה שהתארכה',
        on:()=>typeof OVS!=='undefined'&&!!OVS.pop&&!!OVS.cur,
        editing:()=>false,
        btns:()=>({prev:'הקודם',ok:OVS.cur&&OVS.cur.sug[OVS.alt]?'קבל':'',no:'השאר',edit:'ערוך',next:'הבא בתור',more:''}),
        act:a=>{const m={ok:'ok',no:'leave',edit:'edit',next:'skip',prev:'prev'}[a];if(m)ovAct(m)},
        undo:()=>{document.dispatchEvent(new KeyboardEvent('keydown',{key:'z',code:'KeyZ',ctrlKey:true,bubbles:true,cancelable:true}))},
        target:t=>!!(t&&t.closest&&!t.closest('#bar,#mtop,#topbar,.panel,#msheet,.modal'))},
      {id:'sq',name:'הצעות תיקון',
        on:()=>{const p=q('#sgq');return !!(p&&p.classList.contains('open')&&typeof isAdmin==='function'&&isAdmin()&&q('#sgqb .sgrow[data-id]'))},
        editing:()=>false,
        btns:()=>({prev:'הקודם',ok:'קבל',no:'דחה',edit:'ערוך',next:'הבא בתור',more:''}),
        act:a=>{const rows=[...document.querySelectorAll('#sgqb .sgrow[data-id]')];if(!rows.length)return;
          SQCUR=Math.max(0,Math.min(rows.length-1,SQCUR));const id=rows[SQCUR].dataset.id;
          if(a==='ok')sqDecide(id,'accepted');else if(a==='no')sqDecide(id,'rejected');else if(a==='edit')sqDecide(id,'edited');
          else{SQCUR=Math.max(0,Math.min(rows.length-1,SQCUR+(a==='next'?1:-1)));sqCurPaint()}},
        undo:()=>sqUndo(),
        target:t=>!!(t&&t.closest&&t.closest('#sgqb'))},
      {id:'pm',name:'מצב דפוס',
        on:()=>document.body.classList.contains('pmopen')&&!(typeof OVS!=='undefined'&&OVS.pop),
        editing:()=>false,
        btns:()=>({prev:'',ok:'בסדר',no:'',edit:'',next:'הבא בתור',more:'',page:'השלם עימוד',x:'יציאה'}),
        act:a=>{const id={ok:'pm-ok',next:'pm-next',page:'pm-done',x:'pm-x'}[a];const b=id&&document.getElementById(id);if(b)b.click()},
        target:()=>false}];

    function build(){
      if(TR.bar)return;
      const b=document.createElement('nav');b.id='tchbar';b.dir='rtl';b.setAttribute('aria-label','פעולות סקירה');
      /* תחת html ולא תחת body: בטאבלט לרוחב יש ל-body טרנספורמציה, ואז "קבוע" נצמד אליו ולא למסך */
      H.appendChild(b);TR.bar=b;
      /* משוב מיידי: הכפתור נצבע כבר במגע, והפעולה רצה בלחיצה */
      b.addEventListener('pointerdown',e=>{const x=e.target.closest('button');if(x){x.classList.add('tap');buzz()}});
      ['pointerup','pointercancel','pointerleave'].forEach(t=>b.addEventListener(t,()=>b.querySelectorAll('.tap').forEach(x=>x.classList.remove('tap'))));
      /* הלחיצה נתפסת כבר בחלון (שלב הלכידה), לפני מאזיני "לחיצה מחוץ לחלונית סוגרת" של המצבים
         (בשורה שהתארכה: מאזין הלכידה במסמך סגר את החלונית לפני שהכפתור הספיק לפעול) */
      addEventListener('click',e=>{const x=e.target.closest&&e.target.closest('#tchbar button,#tchundo button');if(!x||x.disabled)return;
        e.preventDefault();e.stopPropagation();if(x.closest('#tchundo')){if(TR.undo)TR.undo()}else press(x.dataset.a)},true);
      const s=document.createElement('div');s.id='tchsheet';s.dir='rtl';s.setAttribute('role','dialog');s.setAttribute('aria-label','פרטים');
      s.innerHTML='<div class="tchgrip" aria-hidden="true"></div><div class="tchsb"></div>';
      H.appendChild(s);TR.sheet=s;
      const scrim=document.createElement('div');scrim.id='tchscrim';H.appendChild(scrim);
      scrim.addEventListener('click',sheetClose);
      let y0=null;
      s.addEventListener('touchstart',e=>{y0=(e.target.closest('.tchgrip')||s.scrollTop<=0)?e.touches[0].clientY:null},{passive:true});
      s.addEventListener('touchend',e=>{if(y0==null)return;const dy=e.changedTouches[0].clientY-y0;y0=null;if(dy>70)sheetClose()},{passive:true})}

    function press(a){
      const M=TR.mode;if(!M)return;
      if(a==='more'){sheetToggle();return}
      if(a==='kbok'||a==='kbx'){call(()=>M.doneEdit(a==='kbok'));setTimeout(sync,30);return}
      sheetClose();
      call(()=>M.act(a));
      if((a==='ok'||a==='no')&&M.undo)undoShow(M,a==='ok'?'התקבל':'נדחה');
      setTimeout(sync,30)}

    /* ---- "בטל" קטן לכמה שניות ---- */
    function undoShow(M,msg){
      clearTimeout(TR.ut);let u=q('#tchundo');
      if(!u){u=document.createElement('div');u.id='tchundo';u.dir='rtl';H.appendChild(u)}
      u.innerHTML='<span></span><button type="button">'+svg('undo')+'<span>בטל</span></button>';
      u.querySelector('span').textContent=msg;
      TR.undo=()=>{TR.undo=null;u.classList.remove('on');call(()=>M.undo());setTimeout(sync,50)};
      u.classList.add('on');TR.ut=setTimeout(()=>{u.classList.remove('on');TR.undo=null},5000)}

    /* ---- החלון התחתון "פרטים": הסרגל המקורי של סכם עובר אליו (אותו אלמנט, אותם כפתורים) ---- */
    function sheetToggle(){if(H.classList.contains('tchsheet'))sheetClose();else sheetOpen()}
    function sheetOpen(){
      const M=TR.mode;if(!M||M.id!=='skp')return;
      const sb=TR.sheet.querySelector('.tchsb');const bar=q('#skpbar');
      sb.innerHTML='';
      const ch=SKM.ghost&&SKM.ghost.querySelector('.skpchips');
      if(ch&&ch.textContent.trim()){const c=ch.cloneNode(true);c.classList.add('tchchips');c.querySelectorAll('[hidden]').forEach(x=>x.hidden=false);sb.appendChild(c)}
      const it=SKP.rev.items[SKP.rev.i];
      if(it&&it.point){const p=document.createElement('div');p.className='tchwhy';p.textContent=it.point;sb.appendChild(p)}
      if(bar){bar.classList.add('insheet');sb.appendChild(bar)}
      H.classList.add('tchsheet')}
    function sheetClose(){
      if(!H.classList.contains('tchsheet'))return;
      H.classList.remove('tchsheet');
      const bar=q('#skpbar');if(bar&&bar.classList.contains('insheet')){bar.classList.remove('insheet');document.body.appendChild(bar)}}

    /* ---- ציור הסרגל לפי המצב ---- */
    function sync(){
      const M=MODES.find(m=>call(m.on))||null;
      if(M!==TR.mode){if(TR.mode&&TR.mode.id==='skp')sheetClose();TR.mode=M}
      H.classList.toggle('tchrev',!!M);
      ['skp','ov','sq','pm'].forEach(id=>H.classList.toggle('tch-'+id,!!M&&M.id===id));
      if(!M){if(TR.bar)TR.bar.hidden=true;H.style.removeProperty('--tchh');return}
      build();
      const ed=call(M.editing)&&TR.kb;
      const B=ed?{kbx:'בטל עריכה',kbok:'סיים וקבל'}:call(M.btns)||{};
      const order=ed?['kbx','kbok']:['prev','no','edit','ok','next','page','x','more'];
      const icon={kbx:'x',kbok:'ok'};
      const sig=M.id+'|'+order.map(k=>k+':'+(B[k]||'')).join(',');
      if(sig!==TR.sig){TR.sig=sig;
        TR.bar.innerHTML=order.filter(k=>B[k]).map(k=>'<button type="button" data-a="'+k+'" class="t-'+k+'">'+svg(icon[k]||k)+'<span>'+esc(B[k])+'</span></button>').join('')}
      TR.bar.hidden=false;
      H.style.setProperty('--tchh',(TR.bar.offsetHeight||64)+'px')}

    /* ---- מקלדת וירטואלית: הסרגל עולה מעליה ---- */
    function kb(){
      const v=window.visualViewport;if(!v)return;
      /* מקום הסרגל נמדד מול חלון הפריסה (שם יושבים אלמנטים קבועים), לא מול innerHeight, שגדל כשהדף מוקטן */
      const lay=H.clientHeight||innerHeight;
      const gap=Math.max(0,Math.round(lay-v.height-v.offsetTop));
      const open=gap>120;TR.kb=open?gap:0;
      H.classList.toggle('tchkb',open);
      H.style.setProperty('--tchkb',(open?gap:0)+'px');
      sync();
      /* שדה העריכה לעולם אינו נשאר מתחת לסרגל */
      if(open){const s=getSelection(),n=s&&s.rangeCount&&s.getRangeAt(0).getBoundingClientRect();
        const lim=v.height+v.offsetTop-(TR.bar&&!TR.bar.hidden?TR.bar.offsetHeight:0)-12;
        if(n&&n.bottom>lim)scrollBy(0,n.bottom-lim+24)}}
    if(window.visualViewport){visualViewport.addEventListener('resize',kb);visualViewport.addEventListener('scroll',kb)}

    /* ---- מחוות: החלקה = ניווט בלבד, הקשה כפולה = עריכה ---- */
    let x0=null,y0=0,t0=0,tg=null,lastTap=0,lastX=0,lastY=0;
    document.addEventListener('touchstart',e=>{
      if(e.touches.length!==1){x0=null;return}
      x0=e.touches[0].clientX;y0=e.touches[0].clientY;t0=Date.now();tg=e.target},{passive:true,capture:true});
    document.addEventListener('touchend',e=>{
      const M=TR.mode;if(x0==null||!M)return;
      const X=e.changedTouches[0].clientX,Y=e.changedTouches[0].clientY,dx=X-x0,dy=Y-y0,dt=Date.now()-t0;x0=null;
      const isSwipe=dt<650&&Math.abs(dx)>70&&Math.abs(dy)<50&&Math.abs(dx)>2*Math.abs(dy);
      /* בזמן סקירה החלקה לעולם אינה מחליפה דף (מאזין הדפדוף של mobile.js אינו שומע אותה) */
      if(isSwipe&&M.id!=='pm')e.stopPropagation();
      if(!tg||!M.target(tg)||call(M.editing))return;
      if(tg.closest&&tg.closest('#tchbar,#tchsheet,#tchundo,.ovpop,input,select,textarea,.tzbody,#srcx'))return;
      if(getSelection()&&!getSelection().isCollapsed)return;
      if(isSwipe){buzz();call(()=>M.act(dx>0?'next':'prev'));setTimeout(sync,30);lastTap=0;return}
      if(tg.closest&&tg.closest('button,a'))return;
      if(dt<300&&Math.abs(dx)<12&&Math.abs(dy)<12){
        const now=Date.now();
        if(now-lastTap<330&&Math.abs(X-lastX)<30&&Math.abs(Y-lastY)<30){lastTap=0;
          const onGhost=M.id!=='skp'||(tg.closest&&tg.closest('.skmghost'));
          const onLine=M.id!=='ov'||(OVS.cur&&OVS.cur._p&&OVS.cur._p.contains(tg));
          if(onGhost&&onLine&&M.id!=='sq'&&call(M.btns).edit){e.preventDefault();e.stopPropagation();call(()=>M.act('edit'));setTimeout(sync,30)}}
        else{lastTap=now;lastX=X;lastY=Y}}},{passive:false,capture:true});

    /* ---- מעקב: הסרגל מתעדכן אחרי כל שינוי (פתיחה, מעבר, סגירה), בלי לולאה כבדה ---- */
    let st=0;const soon=()=>{clearTimeout(st);st=setTimeout(sync,40)};
    new MutationObserver(soon).observe(document.body,{childList:true,attributes:true,attributeFilter:['class']});
    ['click','keyup'].forEach(t=>document.addEventListener(t,soon,true));
    addEventListener('resize',soon);
    setInterval(sync,1500);
    setTimeout(sync,500);

    (function(){const s=document.createElement('style');s.textContent=
      /* הסרגל: קבוע בתחתית, צבעים עדינים, כפתור של 48 פיקסלים לפחות, מתחשב ב-safe-area ובמקלדת */
      '#tchbar{position:fixed;left:0;right:0;bottom:var(--tchkb,0px);z-index:90;display:flex;gap:6px;padding:6px 8px calc(6px + env(safe-area-inset-bottom));'+
        'background:rgba(250,249,246,.98);border-top:1px solid #d9d4c8;box-shadow:0 -2px 10px rgba(0,0,0,.06);font-family:system-ui,"Segoe UI",sans-serif}'+
      'html.tchkb #tchbar{padding-bottom:6px}'+
      '#tchbar[hidden]{display:none}'+
      '#tchbar button{flex:1 1 0;min-width:0;min-height:52px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px;'+
        'border:1px solid #d6d0c4;border-radius:12px;background:#fff;color:#3b4a5a;font:600 14px/1.1 inherit;padding:4px 2px;cursor:pointer;'+
        '-webkit-tap-highlight-color:transparent;touch-action:manipulation;transition:background .06s,transform .06s}'+
      '#tchbar button svg{width:22px;height:22px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}'+
      '#tchbar button span{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100%}'+
      '#tchbar button.t-ok,#tchbar button.t-kbok{color:#2f6b3f;border-color:#a9c9b1;background:#f3f8f4}'+
      '#tchbar button.t-no{color:#8a4a3a;border-color:#dcc0b8;background:#fbf6f4}'+
      '#tchbar button.t-next{color:#2e5b8a;border-color:#b6c8dc}'+
      '#tchbar button.t-more,#tchbar button.t-x{flex:0 0 64px}'+
      '#tchbar button.tap{transform:scale(.96);background:#e9eef3}'+
      '@media (max-width:520px){#tchbar{gap:4px;padding-left:4px;padding-right:4px}#tchbar button{font-size:12.5px}#tchbar button.t-more,#tchbar button.t-x{flex-basis:52px}}'+
      /* התוכן מקבל ריפוד תחתון בגובה הסרגל: השורה האחרונה לעולם אינה מוסתרת */
      'html.tchrev body{padding-bottom:calc(var(--tchh,64px) + 12px)!important}'+
      'html.tchrev #flow{scroll-padding-bottom:calc(var(--tchh,64px) + 16px)}'+
      /* סרגל הניווט של הטלפון/הטאבלט, כפתור העיפרון וסרגל סכם המקורי אינם יושבים מעל הסקירה */
      'html.tchrev #mbot,html.tchrev #lk-fab,html.tchrev #lm-fin{display:none!important}'+
      'html.tch-skp #skpbar:not(.insheet){display:none!important}'+
      'html.tch-skp .skpside{display:none!important}'+
      /* סכם במגע: הנוסף מודגש בעדינות (בלי רקע מרקר), הנמחק בקו חוצה אפור; הסימונים והסיבה רק ב"פרטים" */
      'html.tch .skmghost .skpadd{background:none;font-weight:700;color:#1f4a6e}'+
      'html.tch-skp .skmghost>.skpchips{display:none}html.tch-skp .skmghost.skp,html.tch-skp .skmghost.skpmiss{padding-left:10px}'+
      'html.tch-skp .skmghost .skpconfb button{min-height:44px;padding:4px 14px}'+
      /* החלון התחתון "פרטים" */
      '#tchsheet{position:fixed;left:0;right:0;bottom:0;z-index:95;max-height:70vh;overflow:auto;background:#fff;border-radius:16px 16px 0 0;'+
        'box-shadow:0 -6px 24px rgba(0,0,0,.18);padding:6px 14px calc(14px + env(safe-area-inset-bottom));transform:translateY(105%);transition:transform .18s ease-out;font-size:15px}'+
      'html.tchsheet #tchsheet{transform:none}'+
      '#tchscrim{position:fixed;inset:0;z-index:94;background:rgba(0,0,0,.18);display:none}html.tchsheet #tchscrim{display:block}'+
      '.tchgrip{width:44px;height:5px;border-radius:3px;background:#cfc9bd;margin:4px auto 10px}'+
      '.tchwhy{margin:6px 0;color:#4a5560}.tchchips{display:flex!important}'+
      '#tchsheet #skpbar.insheet{position:static;display:flex;flex-wrap:wrap;gap:8px;padding:0;border:0;background:none;font-size:14px}'+
      '#tchsheet #skpbar.insheet .skpnav{display:none}'+
      '#tchsheet #skpbar.insheet button{min-height:44px;font-size:14px;padding:4px 14px;border-radius:10px}'+
      '#tchsheet #skpbar.insheet>i{display:none}'+
      /* "בטל" קטן */
      '#tchundo{position:fixed;left:50%;bottom:calc(var(--tchh,64px) + var(--tchkb,0px) + 10px);transform:translate(-50%,20px);opacity:0;pointer-events:none;z-index:96;'+
        'display:flex;gap:12px;align-items:center;background:#2f3a44;color:#fff;border-radius:22px;padding:4px 6px 4px 14px;font:14px system-ui,sans-serif;transition:opacity .15s,transform .15s}'+
      '#tchundo.on{opacity:1;transform:translate(-50%,0);pointer-events:auto}'+
      '#tchundo button{display:flex;align-items:center;gap:4px;min-height:40px;border:0;border-radius:18px;background:#4b5a67;color:#fff;font:600 14px inherit;padding:0 12px}'+
      '#tchundo svg{width:18px;height:18px;fill:none;stroke:currentColor;stroke-width:2}'+
      /* שורה שהתארכה במגע: החלונית יושבת בתחתית, מעל הסרגל, ולא צפה מעל הטקסט. הכפתורים הכפולים - בסרגל */
      'html.tch-ov .ovpop{top:auto!important;left:8px!important;right:8px!important;max-width:none;bottom:calc(var(--tchh,64px) + var(--tchkb,0px) + 6px);max-height:38vh;overflow:auto;border-radius:12px}'+
      'html.tch-ov .ovbtns button[data-a="ok"],html.tch-ov .ovbtns button[data-a="edit"],html.tch-ov .ovbtns button[data-a="leave"],'+
        'html.tch-ov .ovbtns button[data-a="prev"],html.tch-ov .ovbtns button[data-a="skip"],html.tch-ov .ovkeys{display:none}'+
      'html.tch-ov .ovbtns button{min-height:44px}'+
      /* תור ההצעות במגע: השורה הנבחרת מסומנת, וכפתורי השורה נשארים גדולים */
      'html.tch-sq #sgqb .sgrow button{min-height:44px}'+
      /* מצב דפוס במגע: הסרגל העליון בשורה אחת שנגללת לצד, והמסגרת אינה מתחת לסרגל התחתון */
      'html.tch-pm #pmbar{flex-wrap:nowrap;overflow-x:auto;-webkit-overflow-scrolling:touch}html.tch-pm #pmbar .pmwide{display:none}'+
      'html.tch-pm #pmbar button,html.tch-pm #pmbar select{min-height:40px}html.tch-pm #pm-next,html.tch-pm #pm-ok,html.tch-pm #pm-done,html.tch-pm #pm-x{display:none}'+
      'html.tch-pm #pm{bottom:calc(var(--tchh,64px) + var(--tchkb,0px))}'+
      '@media print{#tchbar,#tchsheet,#tchscrim,#tchundo{display:none!important}}';
      document.head.appendChild(s)})();
    window.lgTouch={sync,kb,mode:()=>TR.mode&&TR.mode.id,press};
  })();
