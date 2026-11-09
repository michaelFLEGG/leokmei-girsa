# פרומפט 28: קבלת כל קטעי הסבב בעותק של הדף (שום דבר אינו נשמר), ובדיקה שהדף אחרי הקבלה זהה להצעה
NX=json.load(io.open('_work/p28/nx.json',encoding='utf-8'))
JID=os.environ.get('JID','bekhorot-s8014-p28r')
pg.evaluate("()=>{if(typeof setEdit==='function')setEdit(true)}")
pg.wait_for_timeout(9000)
r=pg.evaluate("""async([NX,JID])=>{const H=window.__p27,NL=String.fromCharCode(10);await H.skpOpen(JID);await new Promise(r=>setTimeout(r,1500));const R=H.SKP.rev;if(!R)return {err:'no rev'};
 const res=[];for(const it of R.items){const same=(()=>{try{return H.skmSame(it.ids,it.orig)}catch(e){return 'x:'+e.message}})();
   try{H.skpApplyOne(it,it.text);const F=H.flatU();const pos=new Map(F.map((o,i)=>[o.u.id,i]));
     const a=Math.min(...it.ids.filter(id=>pos.has(id)).map(id=>pos.get(id)));const z=NX[it.iid]!=null&&pos.has(NX[it.iid])?pos.get(NX[it.iid]):F.length;
     const now=H.skmInter(F.slice(a,z));const want=it.text.split(NL).filter(l=>l.indexOf('[מחק-עיטור')!==0).join(NL);
     const cl=x=>x.split(NL).filter(l=>!/^\[(מקור|דף)[:\]]/.test(l)).map(l=>l.replace(/\[תוס':\d+\]/g,''));const A=cl(now),W=cl(want);let d=null;for(let i=0;i<Math.max(A.length,W.length);i++)if(A[i]!==W[i]){d=[W[i],A[i]];break}
     res.push({iid:it.iid,same,match:!d,d})}
   catch(e){res.push({iid:it.iid,same,err:String(e.message||e).slice(0,140)})}}
 return {n:res.length,ok:res.filter(x=>x.match).length,bad:res.filter(x=>!x.match)}}""",[NX,JID])
print(json.dumps(r,ensure_ascii=False,indent=1))
