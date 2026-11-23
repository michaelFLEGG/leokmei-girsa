  /* ---- לימוד בלי חיבור (פרומפט 79, 23.11.2026) ----
     כפתור בתפריט "עוד": שומר במכשיר את כל מה שהמסכת צריכה (הדף, הטקסט, התוס', הגמרא שבצד, הגופנים והקוד),
     במטמון של ה-Service Worker (sw.js) שאינו נמחק בעדכון האתר. בפתיחה הבאה עם חיבור השמירה מתעדכנת לבד:
     קבצים שגרסתם בכתובת (?v=) ולא השתנו אינם יורדים שוב, ושאר הקבצים נבדקים מול השרת (304 כשלא השתנו).
     הכול מאותו דומיין בלבד (נטפרי וסינונים). אין שינוי בנראות הדף: רק פריט בתפריט וחלונית. */
  (function(){
    var OK = ('serviceWorker' in navigator) && ('caches' in window);
    var LSK = 'lg-off-' + (typeof SLUG !== 'undefined' ? SLUG : '');
    function lsGet(k){try{return localStorage.getItem(k)}catch(e){return null}}
    function lsSet(k,v){try{if(v===null)localStorage.removeItem(k);else localStorage.setItem(k,v)}catch(e){}}
    /* כתובות שאסור לשמור: שרתי העריכה וההצעות, קבצי מצב משתנים, ובקשות שעוקפות מטמון בכוונה */
    function skip(u){
      return u.origin !== location.origin || /^\/(api|live|cdn-cgi)(\/|$)/.test(u.pathname) || /(^|\/)fold\//.test(u.pathname) ||
        /(edited-pages|status|layout-audit)\.json$/.test(u.pathname) || /[?&](_|z|r|t)=/.test(u.search) || /\.html?$/.test(u.pathname) && u.pathname !== location.pathname}
    function urls(){
      var set = {}, add = function(h){ if(!h) return; try{ var u = new URL(h, location.href); u.hash = ''; if(skip(u)) return; set[u.pathname + u.search] = 1 }catch(e){} };
      add(location.pathname);
      document.querySelectorAll('script[src],link[href]').forEach(function(e){ var r = (e.getAttribute('rel')||'').toLowerCase();
        if(e.tagName === 'LINK' && !/stylesheet|preload|icon|manifest|modulepreload/.test(r)) return; add(e.src || e.href) });
      try{ performance.getEntriesByType('resource').forEach(function(r){ add(r.name) }) }catch(e){}
      /* גופנים שהוגדרו בגיליונות הסגנון ועוד לא נטענו (למשל מודגש שעוד לא הופיע במסך) */
      try{ [].forEach.call(document.styleSheets, function(ss){ var rules; try{ rules = ss.cssRules }catch(e){ return }
        [].forEach.call(rules || [], function(r){ if(r.type === 5){ var m, re = /url\(["']?([^"')]+)["']?\)/g, src = r.style.getPropertyValue('src');
          while((m = re.exec(src))) add(new URL(m[1], ss.href || location.href).href) } }) }) }catch(e){}
      /* קבצים שהדף טוען רק כשצריך: הגמרא שבצד, פנים התוס' */
      if(typeof SLUG !== 'undefined'){ add('sources/' + SLUG + '.json'); if(window.__TOS && __TOS.face) add(__TOS.face) }
      add('shas.json');
      return Object.keys(set)}
    function sw(){ return navigator.serviceWorker.ready.then(function(r){ return r.active }) }
    function ask(msg, ms){ return sw().then(function(a){ return new Promise(function(res, rej){
      if(!a){ rej(new Error('no sw')); return }
      var ch = new MessageChannel(); ch.port1.onmessage = function(e){ res(e.data) }; a.postMessage(msg, [ch.port2]);
      setTimeout(function(){ rej(new Error('timeout')) }, ms || 600000) }) }) }
    /* גרסה ישנה של ה-Service Worker (לפני פרומפט 79) אינה עונה. בודקים קודם בשאלה קצרה, ואם אין תשובה - מבקשים
       מן הדפדפן לעדכן אותו, ומודיעים ללומד לנסות שוב בעוד רגע (בלי המתנה שקטה) */
    function ready(){ return ask({ type: 'lg-list' }, 4000).then(function(r){ return !!(r && r.ok) }, function(){
      return navigator.serviceWorker.getRegistration().then(function(g){ return g && g.update() }).then(function(){
        return ask({ type: 'lg-list' }, 4000).then(function(r){ return !!(r && r.ok) }, function(){ return false }) }, function(){ return false }) }) }
    function mb(n){ return (n / 1048576).toFixed(n > 10485760 ? 0 : 1) }
    function save(box){
      var st = box.querySelector('.offst'); st.textContent = 'שומר במכשיר... (אפשר להמשיך ללמוד)';
      return ready().then(function(ok){
        if(!ok){ st.textContent = 'רכיב השמירה במכשיר מתעדכן עכשיו. נסה שוב בעוד דקה (או רענן את הדף).'; draw(box); return null }
        return ask({ type: 'lg-save', slug: SLUG, urls: urls() }) }).then(function(r){
        if(r === null) return;
        if(!r || !r.ok){ st.textContent = 'השמירה לא הושלמה' + (r && r.failed ? ' (' + r.failed + ' קבצים לא ירדו)' : '') + '. נסה שוב כשהחיבור טוב.'; return }
        lsSet(LSK, String(Date.now()));
        st.textContent = 'נשמר: ' + r.n + ' קבצים, ' + mb(r.bytes) + ' מגה. המסכת תיפתח גם בלי חיבור, ותתעדכן לבד בכל כניסה עם חיבור.';
        draw(box) }).catch(function(){ st.textContent = 'השמירה לא הושלמה. נסה שוב כשהחיבור טוב.' }) }
    function draw(box){
      var saved = !!lsGet(LSK), b = box.querySelector('.btns');
      b.innerHTML = (saved ? '<button type="button" class="go" data-a="save">עדכן עכשיו</button><button type="button" data-a="rm">הסר מן המכשיר</button>'
                           : '<button type="button" class="go" data-a="save">שמור מסכת ' + (typeof D !== 'undefined' ? D.masechet : '') + '</button>') +
                    '<button type="button" data-a="x">סגור</button>' }
    window.offOpen = function(){
      var m = document.createElement('div'); m.className = 'modal'; m.setAttribute('role', 'dialog'); m.setAttribute('aria-label', 'לימוד בלי חיבור');
      var nm = typeof D !== 'undefined' ? D.masechet : '';
      m.innerHTML = '<div class="box"><h3>לימוד בלי חיבור</h3>' +
        (OK ? '<div>שמירת מסכת ' + nm + ' במכשיר: כל הפרקים, התוס\' והגמרא שבצד. אחרי השמירה הדף נפתח גם בלי אינטרנט (בטלפון כשר, ברשת מסוננת או בלי קליטה), ומתעדכן לבד כשיש חיבור.</div>' +
              '<div class="ref">הפרק נמצא בתוך קובץ המסכת, ולכן שמירה של פרק אחד היא בפועל שמירה של המסכת.</div><div class="offst ref"></div><div class="btns"></div>'
            : '<div>הדפדפן הזה אינו תומך בשמירה במכשיר. אפשר לנסות בדפדפן אחר (כרום, פיירפוקס, ספארי חדש).</div><div class="btns"><button type="button" data-a="x">סגור</button></div>') + '</div>';
      document.body.appendChild(m);
      var box = m.querySelector('.box');
      if(OK){ draw(box); var st = box.querySelector('.offst'); if(lsGet(LSK)) st.textContent = 'המסכת שמורה במכשיר (עודכנה ' + new Date(+lsGet(LSK)).toLocaleDateString('he-IL') + ').' }
      m.addEventListener('click', function(e){
        if(e.target === m){ m.remove(); return }
        var a = e.target.closest && e.target.closest('[data-a]'); if(!a) return;
        var k = a.getAttribute('data-a');
        if(k === 'x') m.remove();
        else if(k === 'save'){ a.disabled = true; save(box) }
        else if(k === 'rm') ask({ type: 'lg-remove', slug: SLUG }).then(function(){ lsSet(LSK, null); box.querySelector('.offst').textContent = 'הוסר מן המכשיר.'; draw(box) }).catch(function(){}) });
      m.addEventListener('keydown', function(e){ if(e.key === 'Escape') m.remove() }) };
    /* עדכון לבד: מסכת שמורה, ופתיחה עם חיבור - אחרי שהדף נרגע, פעם בשש שעות לכל היותר */
    if(OK && typeof SLUG !== 'undefined' && lsGet(LSK)) addEventListener('load', function(){
      setTimeout(function(){
        if(!navigator.onLine || Date.now() - (+lsGet(LSK + '-chk') || 0) < 6 * 3600000) return;
        lsSet(LSK + '-chk', String(Date.now()));
        ready().then(function(ok){ return ok ? ask({ type: 'lg-save', slug: SLUG, urls: urls(), quiet: 1 }) : null }).then(function(r){ if(r && r.ok) lsSet(LSK, String(Date.now())) }).catch(function(){}) }, 15000) });
  })();
