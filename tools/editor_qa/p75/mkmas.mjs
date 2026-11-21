/* mas.js לבדיקה: mas.js החי + sakem_units_core.js + sakem_units.js, מיד אחרי sakem_perek.js (כמו בבנייה).
   node tools/editor_qa/p75/mkmas.mjs <mas.js חי> <פלט> */
import fs from 'fs';import path from 'path';
const T=path.resolve(path.dirname(new URL(import.meta.url).pathname),'../..');
const [src,dst]=process.argv.slice(2);let s=fs.readFileSync(src,'utf8');
const L=s.split('\n');const i=L.findIndex(l=>l.startsWith('  if(skpOK())setTimeout(()=>{skpLoad().then('));
if(i<0){console.error('לא נמצא סוף sakem_perek');process.exit(1)}
if(s.includes('var SKU=(function(){')){console.error('כבר מוזרק');process.exit(1)}
L.splice(i+1,0,fs.readFileSync(path.join(T,'sakem_units_core.js'),'utf8'),fs.readFileSync(path.join(T,'sakem_units.js'),'utf8'));
let out=L.join('\n');
/* פרומפט 74 (touch_review.js) - בסוף הקוד המשותף, כמו בבנייה, אם האתר החי טרם נבנה איתו */
if(!out.includes('סקירה במגע: טאבלט וטלפון'))out+='\n'+fs.readFileSync(path.join(T,'touch_review.js'),'utf8')+'\n';
fs.writeFileSync(dst,out);console.log('ok',dst);
