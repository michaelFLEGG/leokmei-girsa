pg.evaluate("()=>{if(typeof setEdit==='function')setEdit(true)}")
pg.wait_for_timeout(500)
jid=os.environ['JID']
r = pg.evaluate("""async (jid)=>{
  const H=window.__p27;await H.skpOpen(jid);await new Promise(r=>setTimeout(r,1500));
  const R=H.SKP.rev;if(!R)return {err:'norev'};
  return R.items.map(it=>{let live=null,same=null;try{live=it.kind==='seg'?H.skmInter(H.skmUnits(it.ids)):null;same=it.kind==='seg'?H.skmSame(it.ids,it.orig):null}catch(e){live='ERR '+e}
    return {iid:it.iid,kind:it.kind,ids:it.ids,orig:it.orig,text:it.text,live,same}})}""", jid)
io.open('_work/p38/dump-'+jid+'.json','w',encoding='utf-8').write(json.dumps(r,ensure_ascii=False))
print(jid, len(r) if isinstance(r,list) else r)
