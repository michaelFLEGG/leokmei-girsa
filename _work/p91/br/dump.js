const {chromium}=require('playwright');
(async()=>{
 const slug=process.argv[2]||'shabbat', out=process.argv[3]||('/home/user/leokmei-girsa/_work/p91/live-'+slug+'-rows.json');
 const b=await chromium.launch({proxy:{server:process.env.HTTPS_PROXY||'http://127.0.0.1:38923'}}); const ctx=await b.newContext({ignoreHTTPSErrors:true}); const p=await ctx.newPage();
 const errs=[]; p.on('pageerror',e=>errs.push(String(e)));
 await p.goto('https://leokmei.com/'+slug+'.html',{waitUntil:'load',timeout:120000});
 await p.waitForFunction(()=>typeof D!=='undefined'&&D.pages&&D.pages.length>0,null,{timeout:120000});
 await p.waitForTimeout(25000);
 const r=await p.evaluate(()=>({n:D.pages.length,keys:Object.keys(window).filter(k=>/live/i.test(k)).slice(0,30),pages:D.pages.map(pg=>({daf:pg.daf,perek:pg.perek,units:pg.units.map(u=>({k:u.k,id:u.id,a:u.a,l:u.l}))}))}));
 require('fs').writeFileSync(out,JSON.stringify(r));
 console.log('pages',r.n,'keys',r.keys.join(','),'errs',errs.length, errs.slice(0,3));
 await b.close();
})();
