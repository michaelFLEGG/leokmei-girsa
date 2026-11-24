const {chromium}=require('playwright');
(async()=>{
 const [slug,from,ids,out]=process.argv.slice(2);
 const b=await chromium.launch({proxy:{server:process.env.HTTPS_PROXY}}); const c=await b.newContext({ignoreHTTPSErrors:true}); const p=await c.newPage();
 await p.goto('https://leokmei.com/'+slug+'.html',{waitUntil:'load',timeout:90000});
 await p.waitForFunction(()=>typeof D!=='undefined'&&D.pages&&D.pages.length>0,null,{timeout:90000});
 await p.waitForTimeout(10000);
 await p.evaluate((from)=>{const s=document.getElementById('dafsel');const i=D.pages.findIndex(x=>x.daf===from);s.value=String(i);s.dispatchEvent(new Event('change',{bubbles:true}));},from);
 await p.waitForTimeout(12000);
 const r=await p.evaluate((ids)=>ids.split(',').map(id=>{const el=document.getElementById('u'+id);if(!el)return {id,missing:1};
   return {id,cls:el.className,html:el.innerHTML.slice(0,3000),
     ps:[...el.querySelectorAll('p,div.nose,div.dh,.side,.win')].map(x=>({tag:x.tagName,cls:x.className,k:x.dataset&&x.dataset.k,h:x.innerHTML}))}}),ids);
 require('fs').writeFileSync(out,JSON.stringify(r,null,1)); await b.close();
})();
