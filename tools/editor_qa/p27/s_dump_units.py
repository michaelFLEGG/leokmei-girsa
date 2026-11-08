pg.evaluate("()=>{if(typeof setEdit==='function')setEdit(true)}")
pg.wait_for_timeout(9000)
r=pg.evaluate("""()=>{const H=window.__p27;const F=H.flatU();let a=-1,b=-1;F.forEach((o,i)=>{if(o.u.id>=3790&&o.u.id<=4830){if(a<0)a=i;b=i}});
 const out=F.slice(a,b+1).map(o=>{let s;try{s=H.skmInter([o])}catch(e){s='ERR '+e.message}return {id:o.u.id,k:o.u.k,s}});return {n:F.length,out}}""")
print('flat',r['n'],len(r['out']))
io.open('_work/p27/page-units.json','w',encoding='utf-8').write(json.dumps(r['out'],ensure_ascii=False,indent=0))
