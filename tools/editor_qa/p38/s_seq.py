pg.evaluate("()=>{if(typeof setEdit==='function')setEdit(true)}")
pg.wait_for_timeout(500)
r = pg.evaluate("""async ()=>{
  const H=window.__p27;await H.skpOpen('shabbat-s1-mwev8jkj');await new Promise(r=>setTimeout(r,1500));
  const R=H.SKP.rev;const out=[];const tgt=R.items.findIndex(x=>/חפץ או רשות/.test(x.text));
  for(let i=0;i<=Math.min(tgt+2,R.items.length-1);i++){R.i=i;H.skpShow();await new Promise(r=>setTimeout(r,300));
    const f0=document.querySelector('#edflash');if(f0)f0.textContent='';
    const before=H.ED.length;const it=R.items[i];
    const live=H.skmInter(H.skmUnits(it.ids));
    try{H.skpAccept()}catch(e){out.push({i,ex:String(e)})}
    await new Promise(r=>setTimeout(r,250));
    const f=(document.querySelector('#edflash')||{}).textContent||'';
    out.push({i,iid:it.iid,ok:!!R.dec[it.iid],conf:!!R.conflict,flash:f.slice(0,200),same:live===it.orig})}
  return out}""")
print(json.dumps(r, ensure_ascii=False, indent=0)[:6000])
