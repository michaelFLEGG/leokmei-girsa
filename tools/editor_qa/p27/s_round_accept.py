NX=json.load(io.open('_work/p27/nx.json',encoding='utf-8'))
pg.evaluate("()=>{if(typeof setEdit==='function')setEdit(true)}")
pg.wait_for_timeout(9000)
r=pg.evaluate("""async(NX)=>{const H=window.__p27,NL=String.fromCharCode(10);await H.skpOpen('bava-batra-s3799-p27r');await new Promise(r=>setTimeout(r,1500));const R=H.SKP.rev;
 const res=[];let ne=0;for(const it of R.items.filter(x=>['s1','s2','s3','s5','s10','s14','s17'].indexOf(x.iid)<0)){const hz=it.text.indexOf('[מחק-עיטור')>-1;
   let t=it.text;if(hz&&ne<3){ne++;const L=t.split(NL);const k=L.findIndex(l=>l&&'[('.indexOf(l[0])<0);L[k]=L[k]+' (בדיקה)';t=L.join(NL)}
   try{H.skpApplyOne(it,t);const F=H.flatU();const pos=new Map(F.map((o,i)=>[o.u.id,i]));
     const a=Math.min(...it.ids.filter(id=>pos.has(id)).map(id=>pos.get(id)));const z=NX[it.iid]!=null&&pos.has(NX[it.iid])?pos.get(NX[it.iid]):F.length;
     const now=H.skmInter(F.slice(a,z));const want=t.split(NL).filter(l=>l.indexOf('[מחק-עיטור')!==0).join(NL);
     const cl=x=>x.split(NL).filter(l=>!/^\[(מקור|דף)[:\]]/.test(l)).map(l=>l.replace(/\[תוס':\d+\]/g,''));const A=cl(now),W=cl(want);let d=null;for(let i=0;i<Math.max(A.length,W.length);i++)if(A[i]!==W[i]){d=[W[i],A[i]];break}
     res.push({iid:it.iid,edited:t!==it.text,match:!d,d})}
   catch(e){res.push({iid:it.iid,edited:t!==it.text,err:String(e.message||e).slice(0,100)})}}
 return {n:res.length,edited:res.filter(x=>x.edited).map(x=>x.iid+':'+(x.match?'ok':x.err||'mismatch')),bad:res.filter(x=>!x.match).map(x=>({iid:x.iid,err:x.err,d:x.d}))}}""",NX)
print(json.dumps(r,ensure_ascii=False,indent=1))
