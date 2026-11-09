# פרומפט 28: הנוסח החי של כל קטע בבכורות פרק ט, לפי מיקום בדף (לא לפי טווח מזהים: קבלות יוצרות מזהים חדשים)
R=json.load(io.open('_work/p28/ranges.json',encoding='utf-8'))
pg.evaluate("()=>{if(typeof setEdit==='function')setEdit(true)}")
pg.wait_for_timeout(9000)
out=pg.evaluate("""(R)=>{const H=window.__p27,F=H.flatU(),pos=new Map(F.map((o,i)=>[o.u.id,i]));
 const st=R.map(r=>{const p=r.ids.filter(id=>pos.has(id)).map(id=>pos.get(id));return p.length?Math.min(...p):-1});
 const res=[];for(let k=0;k<R.length;k++){const a=st[k];if(a<0){res.push({iid:R[k].iid,err:'no ids'});continue}
   let z=F.length;for(let j=k+1;j<R.length;j++)if(st[j]>=0){z=st[j];break}
   /* סוף הפרק: עד הדרן / פתיחת פרק הבא (כמו בסוף הטווח המקורי) */
   if(k===R.length-1){const last=R[k].ids[R[k].ids.length-1];if(pos.has(last))z=pos.get(last)+1}
   const U=F.slice(a,z);let s;try{s=H.skmInter(U)}catch(e){s='ERR '+e.message}
   res.push({iid:R[k].iid,ids:U.map(o=>o.u.id),kinds:U.map(o=>o.u.k),text:s,real:true})}
 return res}""",R)
io.open('_work/p28/base-live.json','w',encoding='utf-8').write(json.dumps(out,ensure_ascii=False,indent=1))
print('items',len(out),'errs',[o['iid'] for o in out if o.get('err') or str(o.get('text','')).startswith('ERR')])
