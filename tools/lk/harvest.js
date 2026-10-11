/* harvest.js - קציר טקסטי המעטפת (8.10.2026). מורצים בדפדפן, מתוך דף באתר המקומי,
   והתוצאה נשלחת לשרת מקומי קטן שכותב את tools/lk/texts-registry.json
   (דרך tools/lk_registry.py). הרשימה משמשת את דף "טקסטים ששיניתי" לזיהוי יתומים
   ואת docs/TEXTS.md. אינה נטענת באתר הציבורי. */
(async function (PAGES, SINK, WAIT) {
  var out = {};
  for (var i = 0; i < PAGES.length; i++) {
    var f = document.createElement('iframe');
    f.style.cssText = 'position:fixed;left:0;top:0;width:1000px;height:700px;opacity:0';
    document.body.appendChild(f); f.src = PAGES[i];
    await new Promise(function (r) { setTimeout(r, WAIT || 3000); });
    try {
      var W = f.contentWindow, D = f.contentDocument, L = W.LK;
      var C = L.CONTENT, S = L.SKIP;
      var tw = D.createTreeWalker(D.body, NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT, {
        acceptNode: function (x) {
          if (x.nodeType === 3) return NodeFilter.FILTER_ACCEPT;
          if (x.matches && (x.matches(C) || x.matches(S))) return NodeFilter.FILTER_REJECT;
          return NodeFilter.FILTER_SKIP;
        }
      }), n;
      function add(scope, kind, shown) {
        var tk = L.tokenize(shown); if (!tk.t || !/[א-ת]/.test(tk.t)) return;
        var k = scope + '|' + kind + '|' + tk.t;
        out[k] = { key: L.keyFor(scope, kind === 'text' ? tk.t : kind + ':' + tk.t), page: PAGES[i].replace(/^\//, '').replace(/\.html.*/, '') };
      }
      while ((n = tw.nextNode())) add(L.scopeOf(n.parentNode), 'text', n.nodeValue);
      var pt = L.pageType().type;
      add(pt, 'doctitle', D.title);
      var m = D.querySelector('meta[name="description"]'); if (m) add(pt, 'metadesc', m.getAttribute('content') || '');
      var els = D.querySelectorAll('[title],[aria-label],[placeholder],[alt]');
      for (var j = 0; j < els.length; j++) {
        if (els[j].closest(C) || els[j].closest('.lk-ui')) continue;
        ['title', 'aria-label', 'placeholder', 'alt'].forEach(function (a) { var v = els[j].getAttribute(a); if (v) add(L.scopeOf(els[j]), a, v); });
      }
    } catch (e) { out['ERR|' + PAGES[i]] = String(e); }
    f.remove();
  }
  await fetch(SINK, { method: 'POST', body: JSON.stringify(out) });
  return Object.keys(out).length;
})
