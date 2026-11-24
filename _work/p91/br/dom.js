const {chromium}=require('playwright');
(async()=>{
 const slug=process.argv[2], from=process.argv[3], to=process.argv[4], out=process.argv[5];
 const b=await chromium.launch({proxy:{server:process.env.HTTPS_PROXY}}); const c=await b.newContext({ignoreHTTPSErrors:true}); const p=await c.newPage();
 const errs=[]; p.on('pageerror',e=>errs.push(String(e))); p.on('console',m=>{if(m.type()==='error')errs.push(m.text())});
 await p.goto('https://leokmei.com/'+slug+'.html#'+from,{waitUntil:'load',timeout:90000});
 await p.waitForFunction(()=>typeof D!=='undefined'&&D.pages&&D.pages.length>0,null,{timeout:90000});
 await p.waitForTimeout(12000);
 await p.evaluate((from)=>{const s=document.getElementById('dafsel');const i=D.pages.findIndex(x=>x.daf===from);s.value=String(i);s.dispatchEvent(new Event('change',{bubbles:true}));},from);
 await p.waitForTimeout(12000);
 const r=await p.evaluate(([from,to])=>{
   const f=document.getElementById('flow'); const out=[];
   [...f.children].forEach(el=>{out.push({id:el.id,cls:el.className,t:el.innerText.replace(/\s+\n/g,'\n').slice(0,2000)})});
   return {sel:(document.getElementById('dafsel')||{}).value, rows:out};
 },[from,to]);
 require('fs').writeFileSync(out,JSON.stringify(r));
 console.log('rows',r.rows.length,'errs',errs.slice(0,5));
 await b.close();
})();
