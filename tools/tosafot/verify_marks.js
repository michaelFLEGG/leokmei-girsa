// verify_marks.js - בדיקה בדפדפן של סימני התוס' (פרומפט 96): לכל תוס' - היחידה שנמצאה, העמוד, והסדר בדף בכל פרק.
// node tools/tosafot/verify_marks.js URL [new_anchors.json להזרקה לפני פרסום]
const {chromium}=require('playwright');const fs=require('fs');
(async()=>{const b=await chromium.launch(process.env.HTTPS_PROXY?{proxy:{server:process.env.HTTPS_PROXY}}:{});
 const ctx=await b.newContext(); await ctx.addInitScript(()=>{try{localStorage.setItem('lg-tos-mode','foot');localStorage.setItem('lg-tos-v6','1')}catch(e){}}); const p=await ctx.newPage(); const errs=[]; p.on('pageerror',e=>errs.push(e.message));
 await p.goto(process.argv[2],{waitUntil:'load',timeout:120000}); await p.waitForTimeout(7000);
 const inject=process.argv[3]?JSON.parse(fs.readFileSync(process.argv[3],'utf8')):null;
 const r=await p.evaluate(async(inj)=>{
   const T=window.__TOS,LK=window.lkTos;
   if(inj){const by={};inj.forEach(x=>by[x.n]=x);T.items.forEach(it=>{const x=by[it.n];if(x){['t','occ','rule','page','daf','why'].forEach(k=>it[k]=x[k])}})}
   LK.reset();const M=LK.perekMap();const pageOf={};M.flat.forEach(x=>pageOf[x.u.id]=D.pages[x.q].daf);
   const out={total:T.items.length,how:{},noUid:0,wrongPage:[],perekMis:0,dom:{},inv:[]};
   T.items.forEach(it=>{const rs=LK.resolve(it);out.how[rs.how]=(out.how[rs.how]||0)+1;if(!rs.uid){out.noUid++;return}
     if(pageOf[rs.uid]!==(it.page||it.daf))out.wrongPage.push(it.n);if(M.upk[rs.uid]!==+it.perek)out.perekMis++});
   // DOM: לכל פרק - מעבר לעמוד בפרק, הדלקת התוס' והסימון
   const sel=document.getElementById('dafsel');
   for(let pk=1;pk<=M.np;pk++){const q=M.flat[M.starts[pk-1]+3].q; sel.value=String(q); sel.dispatchEvent(new Event('change',{bubbles:true}));
     await new Promise(r=>setTimeout(r,2500)); if(window.tsMark){try{localStorage.setItem('lg-tos','foot')}catch(e){}}
     window.tsMark&&window.tsMark(); await new Promise(r=>setTimeout(r,800));
     const ns=[...document.querySelectorAll('#flow .tsa')].map(e=>+e.getAttribute('data-n')).filter(n=>T.items.find(i=>i.n===n&&+i.perek===pk));
     out.dom[pk]=ns.length; for(let i=1;i<ns.length;i++)if(ns[i]<ns[i-1])out.inv.push(ns[i-1]+'>'+ns[i])}
   return out},inject);
 console.log(JSON.stringify(r)); console.log('errs',errs.slice(0,5)); await b.close()})();
