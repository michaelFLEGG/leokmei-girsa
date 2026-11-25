// dump_pages.js - דף הנתונים של האתר (pages + שיוך היחידות לפרק) כפי שהדפדפן רואה אותו, לקלט של reanchor.py (פרומפט 96).
// node tools/tosafot/dump_pages.js https://leokmei.com/kiddushin.html OUT.json
const {chromium}=require('playwright');const fs=require('fs');
(async()=>{const b=await chromium.launch(process.env.HTTPS_PROXY?{proxy:{server:process.env.HTTPS_PROXY}}:{});
 const p=await b.newPage(); await p.goto(process.argv[2],{waitUntil:'load',timeout:120000}); await p.waitForTimeout(7000);
 const r=await p.evaluate(()=>{const M=window.lkTos.perekMap();return {upk:M.upk,pages:D.pages.map(p=>({daf:p.daf,units:p.units.map(u=>({id:u.id,k:u.k,ref:u.ref||'',l:(u.l||[]).map(x=>x[1])}))}))}});
 fs.writeFileSync(process.argv[3],JSON.stringify(r)); console.log(Object.keys(r.upk).length, r.pages.length); await b.close()})();
