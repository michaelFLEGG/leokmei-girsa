IIDS=["s2","s20","s33"]
# שחזור במסלול המלא של הסקירה: skpOpen -> מעבר לקטע -> skpAccept (כפתור "קבל"), ואז הפרסום
pg.evaluate("()=>{if(typeof setEdit==='function')setEdit(true)}")
pg.wait_for_timeout(500)
pg.evaluate("""()=>{window.__PUTS=[];const of=window.fetch;window.fetch=function(u,o){try{if(o&&o.method==='PUT'&&String(u).indexOf('/edits')>-1)window.__PUTS.push(JSON.parse(o.body))}catch(e){}return of.apply(this,arguments)}}""")
res=[]
for iid in IIDS:
    r = pg.evaluate("""async (iid)=>{
      const H=window.__p27;if(!H.SKP.rev){await H.skpOpen('shabbat-p1');await new Promise(r=>setTimeout(r,1500))}
      const R=H.SKP.rev;const i=R.items.findIndex(x=>x.iid===iid);if(i<0)return {iid,err:'no item'};
      R.i=i;H.skpShow();await new Promise(r=>setTimeout(r,700));
      const hid=(R.items[i].text.match(/\\[מחק-עיטור:(\\d+)\\]/)||[])[1];
      const before=H.ED.length;
      let err=null;try{H.skpAccept()}catch(e){err=String(e.message||e)}
      await new Promise(r=>setTimeout(r,500));
      const flash=(document.querySelector('#flash,.flash')||{}).textContent||'';
      return {iid,hid,err,conflict:!!R.conflict,flash:flash.slice(0,120),added:H.ED.length-before,gone:hid?!H.flatU().some(o=>o.u.id===+hid):null,
        hdel:H.ED.filter(e=>e.kind==='hdel').map(e=>e.t)}}""", iid)
    res.append(r)
print(json.dumps(res, ensure_ascii=False, indent=1)[:4000])
pg.wait_for_timeout(16000)
r2 = pg.evaluate("""()=>({puts:window.__PUTS.length,hdelInLastPut:(window.__PUTS.slice(-1)[0]||{edits:[]}).edits.filter(e=>e.kind==='hdel').map(e=>({t:e.t,texts:e.texts.map(x=>x.slice(0,40))})),ed:window.__p27.ED.filter(e=>e.kind==='hdel').map(e=>({t:e.t,lost:e.lost,pub:e.pub}))})""")
print(json.dumps(r2, ensure_ascii=False, indent=1)[:3000])
io.open(os.environ.get("PUT_OUT","_work/p33-put.json"),"w",encoding="utf-8").write(json.dumps(pg.evaluate("()=>window.__PUTS.slice(-1)[0]"),ensure_ascii=False))
