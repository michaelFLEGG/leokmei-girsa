const fs=require('fs');
const OLD=require(''+process.env.OLD_CORE+'');
const NEW=require(''+require('path').resolve(__dirname,'../../sakem_core.js')+'');
const window={};eval(fs.readFileSync(''+process.env.OLD_FIX+'','utf8')+';global.oldFix=skpFixLocks;');
const RE=/נעולים|קטע שלם|נוספו שורות|תג לא מוכר/;
function oldPath(o,t){const hd=OLD.hatzDel(o,t);const o2=hd.ids.length?hd.orig:o;let x=hd.ids.length?hd.text:t;
  x=oldFix(o2,x);try{x=OLD.fixInline(o2,x).text}catch(e){}return OLD.guard(o2,x,{edited:true}).filter(e=>RE.test(e))}
function newPath(o,t){const hd=NEW.hatzDel(o,t);const o2=hd.ids.length?hd.orig:o;let x=hd.ids.length?hd.text:t;
  x=NEW.acceptPrep(o2,x).text;return NEW.acceptErrs(o2,x)}
const res={};
for(const f of process.argv.slice(2)){const jid=f.replace(/.*dump-|\.json$/g,'');const D=JSON.parse(fs.readFileSync(f,'utf8'));
  for(const it of D){if(it.kind!=='seg'||!it.live||/^ERR/.test(it.live))continue;
    const o=it.live;const a=oldPath(o,it.text),b=newPath(o,it.text);
    if(a.length||b.length)(res[jid]=res[jid]||[]).push({iid:it.iid,same:it.same,old:a[0]||'',now:b[0]||'',safe:b.length?!!NEW.acceptSafe(o,it.text):null})}}
console.log(JSON.stringify(res,null,1));
