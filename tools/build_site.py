import json, html, re, collections, sys
def build(json_path, out_path, masechet):
  blocks = json.load(open(json_path, encoding='utf-8'))

  # ---------- normalization of style names (canonical roles) ----------
  ROLE = {
   'Normal':'body','רווח לפני':'body-sp','נקודה':'body-nk','הסבר ורקע':'body-hr','אמוראים':'body','פסוק':'body',
   'חלון 3':'anchor','דף בצד':'daf','פרק':'perek-num','פרק שם':'perek-name','דפים בפרק ב':'perek-range','תחילת פרק':'perek-start','הדרן עלך':'hadran',
   'משניות':'mishna','חלק משנה מודגש':'mishna',"ד''ה משנה":'dh',"משנה ד''ה":'dh',"ד''ה משנה מודגש אפור":'dh','נושא':'nose','חציצה':'hatz'}
  CS = {'אמוראים תו':'am','פסוק תו':'ps','כותרת 3 תו':'kt','הסבר':'hs','נושא תו':'ns','אות בודדת תו':'ot','תנאי משנה תו':'tn','חלק משנה מודגש תו':'tn'}

  def runs_html(runs):
      out=[]
      for r in runs:
          t=html.escape(r['t']); c=CS.get(r['cs'])
          if r['b'] and not c: c='b'
          out.append(f'<i class="{c}">{t}</i>' if c else t)
      return ''.join(out)

  # ---------- QA: daf sequence ----------
  HEB='אבגדהוזחטיכלמנסעפצקרשת'
  def gem(s):
      s=s.strip().rstrip('.:').replace('"','').replace("'",'')
      v={'א':1,'ב':2,'ג':3,'ד':4,'ה':5,'ו':6,'ז':7,'ח':8,'ט':9,'י':10,'כ':20,'ל':30,'מ':40,'נ':50,'ס':60,'ע':70,'פ':80,'צ':90,'ק':100,'ר':200,'ש':300,'ת':400}
      return sum(v.get(ch,0) for ch in s)
  def tog(n):
      out='';
      for val,ch in ((400,'ת'),(300,'ש'),(200,'ר'),(100,'ק'),(90,'צ'),(80,'פ'),(70,'ע'),(60,'ס'),(50,'נ'),(40,'מ'),(30,'ל'),(20,'כ'),(10,'י'),(9,'ט'),(8,'ח'),(7,'ז'),(6,'ו'),(5,'ה'),(4,'ד'),(3,'ג'),(2,'ב'),(1,'א')):
          while n>=val: out+=ch; n-=val
      return out.replace('יה','טו').replace('יו','טז')
  qa=[]
  seq=[(b['i'],b['text'].strip()) for b in blocks if b['style']=='דף בצד']
  seen=collections.Counter(); prev=None
  for i,d in seq:
      seen[d]+=1
      if seen[d]>1: qa.append(('כפילות ציון דף',f'"{d}" מופיע שוב (יחידה {i})'))
      key=gem(d)*2+(1 if d.endswith(':') else 0)
      if prev is not None and key!=prev+1 and seen[d]==1:
          miss=[]; k=prev+1
          while k<key: miss.append(tog(k//2)+('.' if k%2==0 else ':')); k+=1
          if miss: qa.append(('עמוד ללא ציון דף','חסר: '+', '.join(miss)+f' (לפני {d})'))
          if key<prev: qa.append(('סדר דפים הפוך',f'"{d}" אחרי {tog(prev//2)}{"." if prev%2==0 else ":"}'))
      prev=max(prev or 0,key)
  unknown=collections.Counter(b['style'] for b in blocks if b['style'] not in ROLE)
  for s,n in unknown.items(): qa.append(('סגנון לא ממופה',f'{s} ({n})'))
  long_anchor=[b for b in blocks if b['style']=='חלון 3' and len(b['text'])>25]
  for b in long_anchor: qa.append(('חלון ארוך',b['text'][:40]))
  empty_anchor=[b for b in blocks if b['style']=='חלון 3' and not b['text'].strip()]
  if empty_anchor: qa.append(('חלון ריק',f'{len(empty_anchor)} חלונות ריקים'))

  # ---------- pages ----------
  pages=[]  # {daf, perek, perekName, units:[...]}
  cur=None; perek=''; perekName=''; unit=None
  order=[]
  for b in blocks:
      r=ROLE.get(b['style'],'body'); h=runs_html(b['runs']); t=b['text'].strip()
      if r=='perek-num': perek=t
      if r=='perek-name': perekName=t
      if r=='daf':
          cur={'daf':t,'perek':perek,'perekName':perekName,'units':[]}; pages.append(cur); unit=None
          continue
      if cur is None: continue
      cur['perek']=perek; cur['perekName']=perekName
      if r=='anchor':
          unit={'k':'u','a':h,'l':[],'id':b['i']}; cur['units'].append(unit)
      elif r.startswith('body'):
          if unit is None or unit['k']!='u': unit={'k':'u','a':'','l':[],'id':b['i']}; cur['units'].append(unit)
          unit['l'].append([r[5:] if len(r)>4 else '',h])
      elif r=='mishna':
          if cur['units'] and cur['units'][-1]['k']=='m': cur['units'][-1]['l'].append(['',h])
          else: cur['units'].append({'k':'m','a':'','l':[['',h]],'id':b['i']})
          unit=None
      elif r in ('dh','nose','hatz','perek-num','perek-name','perek-range','perek-start','hadran'):
          cur['units'].append({'k':r,'a':h,'l':[],'id':b['i']}); unit=None

  # nose TOC
  toc=[]
  for pi,p in enumerate(pages):
      for u in p['units']:
          if u['k']=='nose': toc.append([pi,u['id'],re.sub('<[^>]+>','',u['a'])])
  # amoraim index
  am=collections.Counter()
  for b in blocks:
      for r in b['runs']:
          if r['cs']=='אמוראים תו':
              n=r['t'].strip(' ,.:;!?-')
              if 2<=len(n)<=18: am[n]+=1
  amlist=[[k,v] for k,v in am.most_common(80)]
  psk=collections.Counter()
  for b in blocks:
      for r in b['runs']:
          if r['cs']=='פסוק תו':
              n=r['t'].strip(" ,.:;!?-'’‘")
              if len(n)>=4: psk[n]+=1

  data={'masechet':masechet,'pages':pages,'toc':toc,'am':amlist,'qa':qa,'nPsk':len(psk),'nAm':sum(am.values())}
  J=json.dumps(data,ensure_ascii=False).replace('</','<\\/')

  CSS=r'''
  @font-face{font-family:'Vilna';src:url(fonts/BA_TM_Vilna_ExtraBold.ttf);font-weight:900}
  @font-face{font-family:'Vilna';src:url(fonts/BA_Vilna_Bold.ttf);font-weight:700}
  @font-face{font-family:'Frank';src:url(fonts/FrankRuehl.ttf);font-weight:400}
  :root{--ink:#1d1a16;--paper:#fbf8f1;--grey:#767171;--gold:#c9a24a;--rail:20mm;--body:60mm;--zoom:2.1;--fs:9pt;--lh:11pt}
  *{box-sizing:border-box}
  html,body{margin:0;background:#e9e4d8;color:var(--ink);font-family:'Frank','Frank Ruhl Libre',FrankRuehl,serif}
  body.hc{--ink:#000;--paper:#fff;--grey:#333;background:#ddd}
  .bar{position:sticky;top:0;z-index:5;display:flex;flex-wrap:wrap;gap:6px 10px;align-items:center;padding:7px 12px;background:#2b2620;color:#f1ead9;font-size:14px}
  .bar b{font-weight:500} .bar .sp{flex:1}
  .bar button,.bar select,.bar input{font:inherit;background:#4a4137;color:#f1ead9;border:0;border-radius:4px;padding:3px 9px;cursor:pointer}
  .bar input{cursor:text;width:150px} .bar button.on{background:var(--gold);color:#2b2620}
  .bar button[title]{position:relative}
  .nav{display:flex;gap:4px;align-items:center}
  .nav .daf{min-width:56px;text-align:center;font-weight:700;font-size:16px}
  .stage{display:flex;justify-content:center;padding:22px 12px 60px}
  .sheet{width:90mm;min-height:130mm;background:var(--paper);box-shadow:0 2px 20px rgba(0,0,0,.25);padding:5mm 15mm 6mm 10mm;transform:scale(var(--zoom));transform-origin:top center;position:relative;margin-bottom:calc(130mm * (var(--zoom) - 1))}
  .head{display:flex;justify-content:space-between;font-size:6pt;letter-spacing:.06em;color:#5a5044;border-bottom:.2pt solid #b9ad99;padding-bottom:1mm;margin-bottom:1.5mm}
  .row{display:grid;grid-template-columns:var(--rail) 1fr;width:calc(var(--rail) + var(--body));margin-right:calc(-1 * var(--rail))}
  .rail{text-align:left;padding-left:1.4mm}
  .main{font-size:var(--fs);line-height:var(--lh);text-align:justify;text-align-last:right}
  .main p{margin:0} .main p.sp{margin-top:3pt} .main p.nk{font-size:calc(var(--fs) + 1pt)} .main p.hr{font-size:7pt;line-height:8pt;color:#4a4137}
  .anchor{display:inline-block;font-family:'Vilna','Frank Ruhl Libre',serif;font-weight:900;font-size:7pt;line-height:var(--lh);color:var(--grey);white-space:nowrap;max-width:20mm;overflow:hidden;text-overflow:ellipsis}
  .mlabel{font-size:5.5pt;color:#8a7d66;line-height:var(--lh)}
  .mishna{background:#eeeae1;padding:.6mm 1mm;margin:1mm 0;font-family:'Vilna','David Libre',serif;font-weight:700;border-right:1.2pt solid var(--gold)}
  .dh{text-align:center;text-align-last:center;font-family:'Vilna','Frank Ruhl Libre',serif;font-weight:900;font-size:10pt;margin:1.2mm 0 .4mm}
  .nose{text-align:center;text-align-last:center;font-family:'Vilna','David Libre',serif;font-weight:900;margin-top:3pt;font-size:var(--fs)}
  .hatz{text-align:center;text-align-last:center;letter-spacing:.3em;color:#8a7d66;line-height:9pt;margin:1mm 0}
  .perek-num .main{color:#a83c2f;font-size:5pt;line-height:6pt;font-weight:700} .perek-range .main{color:#a83c2f;font-size:6pt;line-height:7pt}
  .perek-name .main{color:#bfb4a2;font-family:'Vilna',serif;font-weight:900;font-size:8pt;text-align:right} .perek-start .main{text-align:center;text-align-last:center;font-weight:700}
  .hadran .main{text-align:center;text-align-last:center;font-weight:500;font-size:10pt;margin:3mm 0}
  i{font-style:normal} .am{font-weight:700} .ps{font-family:'Vilna','David Libre',serif;font-weight:700;color:#2e3f6b} body.hc .ps{color:#000;text-decoration:underline}
  .kt{font-weight:700} .hs{font-size:7pt;color:#4a4137} .ot{font-weight:700;font-size:6.5pt} .tn{font-weight:900} .ns{font-weight:700} .b{font-weight:700}
  .u .main:hover{background:rgba(201,162,74,.14)} .u:target .main,.hit{background:rgba(201,162,74,.28)}
  mark{background:#ffe27a;color:inherit}
  .panel{position:fixed;top:44px;right:0;bottom:0;width:min(420px,100vw);background:#fbf8f1;box-shadow:-2px 0 16px rgba(0,0,0,.25);overflow:auto;padding:14px 18px;z-index:6;display:none;font-size:15px;line-height:1.6}
  .panel.open{display:block} .panel h3{margin:12px 0 4px;font-size:15px;color:#5a5044;font-weight:500;border-bottom:1px solid #d9d1bd}
  .panel a{color:var(--ink);text-decoration:none;display:block;padding:2px 0;cursor:pointer} .panel a:hover{color:#a83c2f}
  .panel .x{float:left;background:none;border:0;font-size:22px;cursor:pointer;color:#5a5044}
  .panel .n{color:#8a7d66;font-size:12px} .res{padding:5px 0;border-bottom:1px dotted #d9d1bd} .res small{color:#8a7d66}
  .tag{display:inline-block;background:#eeeae1;border-radius:3px;padding:0 6px;margin:2px;font-size:13px}
  .chips{display:flex;flex-wrap:wrap}
  .foot{position:fixed;bottom:0;left:0;right:0;background:#2b2620;color:#cfc4ad;font-size:12px;padding:5px 12px;text-align:center}
  @media print{.bar,.panel,.foot{display:none} .stage{padding:0;display:block} .sheet{transform:none;box-shadow:none;margin:0} @page{size:90mm 130mm;margin:0}}
  @media(max-width:700px){:root{--zoom:1} .stage{padding:8px 0 70px} .sheet{width:100vw;min-height:0;margin-bottom:0;padding:4mm 5mm} .row{grid-template-columns:1fr;margin-right:0;width:auto} .rail{text-align:right;padding:0} .anchor{max-width:none;display:block;margin-top:2pt} .main{font-size:12pt;line-height:17pt} .dh{font-size:14pt} .bar input{width:110px} [data-z]{display:none}}
  '''

  JS=r'''
  const D=DATA;let cur=0;const $=s=>document.querySelector(s);
  const params=new URLSearchParams(location.hash.slice(1));
  function esc(s){return s.replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}
  function render(i,q){cur=Math.max(0,Math.min(D.pages.length-1,i));const p=D.pages[cur];
   let h=`<div class="head"><span>${D.masechet}</span><span>${esc(p.perekName)} · ${esc(p.perek)}</span><span>${esc(p.daf)}</span></div>`;
   for(const u of p.units){
    if(u.k==='u'){h+=`<div class="row u" id="u${u.id}"><div class="rail"><span class="anchor">${u.a}</span></div><div class="main">${u.l.map(l=>`<p class="${l[0]}">${l[1]}</p>`).join('')}</div></div>`}
    else if(u.k==='m'){h+=`<div class="row"><div class="rail"><span class="mlabel">משנה</span></div><div class="main mishna">${u.l.map(l=>`<p>${l[1]}</p>`).join('')}</div></div>`}
    else if(u.k==='hatz'){h+=`<div class="row"><div class="rail"></div><div class="main hatz">* * *</div></div>`}
    else h+=`<div class="row ${u.k}"><div class="rail"></div><div class="main ${u.k==='dh'||u.k==='nose'?u.k:''}">${u.a}</div></div>`}
   $('#sheet').innerHTML=q?hl(h,esc(q).replace(/"/g,'&quot;').replace(/'/g,'&#x27;')):h;$('#dafsel').value=cur;$('#curdaf').textContent=p.daf;$('#peresel').value=p.perek;
   document.title=`לאוקמי גירסא · ${D.masechet} ${p.daf}`;location.hash=`daf=${cur}`;window.scrollTo(0,0)}
  function hl(h,q){const r=new RegExp('('+q.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')+')','g');return h.replace(/>([^<]+)</g,(m,t)=>'>'+t.replace(r,'<mark>$1</mark>')+'<')}
  function go(d){render(cur+d)}
  function zoom(v){document.documentElement.style.setProperty('--zoom',v);document.querySelectorAll('[data-z]').forEach(b=>b.classList.toggle('on',+b.dataset.z===v))}
  function fs(d){const r=document.documentElement,f=parseFloat(getComputedStyle(r).getPropertyValue('--fs'))+d;r.style.setProperty('--fs',f+'pt');r.style.setProperty('--lh',(f+2)+'pt')}
  function panel(id){const p=$('#'+id),o=p.classList.contains('open');document.querySelectorAll('.panel').forEach(x=>x.classList.remove('open'));if(!o)p.classList.add('open')}
  function dec(s){return s.replace(/&quot;/g,'"').replace(/&#x27;/g,"'").replace(/&amp;/g,'&')}
  function txt(u){return dec(u.a.replace(/<[^>]+>/g,'')+' '+u.l.map(l=>l[1].replace(/<[^>]+>/g,'')).join(' '))}
  function search(q){q=q.trim();LASTQ=q;const out=$('#sres');if(q.length<2){out.innerHTML='';return}
   RES=[];let res=RES,n=0;D.pages.forEach((p,pi)=>{for(const u of p.units){const t=txt(u);const k=t.indexOf(q);if(k>-1){n++;if(res.length<120)res.push({pi,id:u.id,daf:p.daf,s:t.slice(Math.max(0,k-40),k+60)})}}});
   out.innerHTML=`<div class="n">${n} תוצאות</div>`+res.map((r,i)=>`<div class="res"><a onclick="jumpR(${i})"><small>${r.daf}</small> …${esc(r.s).replace(esc(q),'<mark>'+esc(q)+'</mark>')}…</a></div>`).join('');
   $('#search').classList.add('open')}
  let RES=[],LASTQ='';function jumpR(i){jump(RES[i].pi,RES[i].id,LASTQ)}
  function jump(pi,id,q){render(pi,q);setTimeout(()=>{const e=$('#u'+id);if(e){e.classList.add('hit');e.scrollIntoView({block:'center'})}},50)}
  function amq(i){$('#q').value=D.am[i][0];search(D.am[i][0])}
  function build(){const ds=$('#dafsel');D.pages.forEach((p,i)=>ds.add(new Option(p.daf,i)));
   const ps=$('#peresel'),seen={};D.pages.forEach((p,i)=>{if(!seen[p.perek]){seen[p.perek]=1;ps.add(new Option(p.perek+' · '+p.perekName,p.perek))}});
   ps.onchange=()=>render(D.pages.findIndex(p=>p.perek===ps.value));ds.onchange=()=>render(+ds.value);
   let t='',lp='';for(const [pi,id,s] of D.toc){const p=D.pages[pi];if(p.perek!==lp){lp=p.perek;t+=`<h3>${esc(p.perek)} · ${esc(p.perekName)}</h3>`}t+=`<a onclick="jump(${pi},${id})"><small class="n">${p.daf}</small> ${esc(s)}</a>`}$('#tocb').innerHTML=t;
   $('#amb').innerHTML=`<div class="n">${D.nAm} אזכורי אמוראים מסומנים בקובץ; ${D.nPsk} ציטוטי פסוקים שונים</div><div class="chips">`+D.am.map((a,i)=>`<a class="tag" onclick="amq(${i})">${esc(a[0])} <span class="n">${a[1]}</span></a>`).join('')+'</div>';
   $('#qab').innerHTML=D.qa.length?D.qa.map(q=>`<div class="res"><b>${q[0]}</b>: ${esc(q[1])}</div>`).join(''):'לא נמצאו חריגות';
   document.addEventListener('keydown',e=>{if(e.ctrlKey&&e.key==='ArrowLeft'){go(1);e.preventDefault()}if(e.ctrlKey&&e.key==='ArrowRight'){go(-1);e.preventDefault()}if(e.ctrlKey&&(e.key==='='||e.key==='+')){fs(1);e.preventDefault()}if(e.ctrlKey&&e.key==='-'){fs(-1);e.preventDefault()}if(e.key==='Escape')document.querySelectorAll('.panel').forEach(x=>x.classList.remove('open'))});
   render(+(params.get('daf')||0))}
  build();
  '''

  page=f'''<!DOCTYPE html><html lang="he" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
  <title>לאוקמי גירסא · {masechet}</title>
  <link href="https://fonts.googleapis.com/css2?family=Frank+Ruhl+Libre:wght@400;500;700;900&family=David+Libre:wght@400;700&display=swap" rel="stylesheet">
  <style>{CSS}</style></head><body>
  <div class="bar"><a href="index.html" style="color:inherit;text-decoration:none"><b>לאוקמי גירסא</b></a> <span>{masechet}</span>
  <select id="peresel" title="פרק"></select>
  <div class="nav"><button onclick="go(-1)" title="הקודם (Ctrl+חץ ימין)">› הקודם</button><span class="daf" id="curdaf"></span><button onclick="go(1)" title="הבא (Ctrl+חץ שמאל)">‹ הבא</button></div>
  <select id="dafsel" title="דף"></select>
  <input id="q" placeholder="חיפוש ב{masechet}" oninput="search(this.value)" onfocus="search(this.value)">
  <span class="sp"></span>
  <button onclick="panel('toc')">תוכן העניינים</button><button onclick="panel('am')">אמוראים</button><button onclick="panel('qa')">בקרה</button>
  <button data-z="1" onclick="zoom(1)">גודל ספר</button><button data-z="2.1" class="on" onclick="zoom(2.1)">מסך</button><button data-z="3" onclick="zoom(3)">גדול</button>
  <button onclick="fs(1)" title="Ctrl+=">א+</button><button onclick="fs(-1)" title="Ctrl+-">א-</button><button onclick="document.body.classList.toggle('hc')">ניגודיות</button><button onclick="window.print()">הדפסה</button></div>
  <div class="panel" id="search"><button class="x" onclick="panel('search')">×</button><h3>תוצאות חיפוש</h3><div id="sres"></div></div>
  <div class="panel" id="toc"><button class="x" onclick="panel('toc')">×</button><h3>תוכן העניינים - נושאי הסוגיות</h3><div id="tocb"></div></div>
  <div class="panel" id="am"><button class="x" onclick="panel('am')">×</button><h3>אמוראים ותנאים - לפי הסימון בקובץ</h3><div id="amb"></div></div>
  <div class="panel" id="qa"><button class="x" onclick="panel('qa')">×</button><h3>בקרת הקובץ - חריגות שנמצאו בהמרה</h3><div id="qab"></div></div>
  <div class="stage"><div class="sheet" id="sheet"></div></div>
  <div class="foot">לאוקמי גירסא · קיצור התלמוד הבבלי · מסכת {masechet} · {len(pages)} עמודים · נבנה אוטומטית מקובץ הוורד</div>
  <script>const DATA={J};</script><script>{JS}</script></body></html>'''
  open(out_path,'w',encoding='utf-8').write(page)
  return {'pages':len(pages),'toc':len(toc),'qa':qa}

if __name__=='__main__':
  r=build(sys.argv[1],sys.argv[2],sys.argv[3]); print(r['pages'],'pages',len(r['qa']),'qa')
