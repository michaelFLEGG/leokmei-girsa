# תרחיש: מחיקת עיטור שצמוד לכותרת דרך סכם ([מחק-עיטור:<מזהה>]) - נמחק בדף, ונרשמת רשומת hdel כמו "מחק עיטור" בעורך.
# וגם: ניסיון למחוק [קבוע] שאינו עיטור - נדחה.
pg.evaluate("()=>{if(typeof setEdit==='function')setEdit(true)}")
pg.wait_for_timeout(800)
r = pg.evaluate("""async ()=>{
  const H=window.__p27;await H.skpOpen('bava-batra-p5');await new Promise(r=>setTimeout(r,800));
  const fu=H.flatU();const k=fu.findIndex(o=>o.u.k==='hatz'&&fu[k0(o)]);function k0(o){return 0}
  const hi=fu.findIndex((o,i)=>o.u.k==='hatz'&&fu[i+1]&&JSON.stringify(fu[i+1].u).indexOf('יציאה לחו')>-1);
  if(hi<0)return {err:'hatz not found'};
  const os=fu.slice(hi-1,hi+2),ids=os.map(o=>o.u.id),orig=H.skmInter(os);
  const hid=fu[hi].u.id,text=orig.replace('[קבוע:'+hid+']','[מחק-עיטור:'+hid+']');
  const it={iid:'t1',kind:'seg',ids,orig,text};
  const out={ids,hid,hasTok:text.indexOf('מחק-עיטור')>-1,ed0:H.ED.length};
  try{H.skpApplyOne(it,text);out.ok=true}catch(e){out.ok=false;out.err=String(e.message||e)}
  out.gone=!H.flatU().some(o=>o.u.id===hid);out.row=!!document.getElementById('u'+hid);
  const rec=H.ED.filter(e=>e.kind==='hdel').slice(-1)[0];out.rec=rec&&{kind:rec.kind,texts:rec.texts.map(t=>String(t).slice(0,40)),daf:rec.daf};
  /* שלילה: פתיחת פרק (perek-start) אינה נמחקת */
  const pi=H.flatU().findIndex(o=>/perek/.test(o.u.k));
  if(pi>0){const os2=H.flatU().slice(pi,pi+2),o2=H.skmInter(os2),id2=os2[0].u.id;
    try{H.skpApplyOne({iid:'t2',kind:'seg',ids:os2.map(o=>o.u.id),orig:o2},o2.replace('[קבוע:'+id2+']','[מחק-עיטור:'+id2+']'));out.neg='applied!'}catch(e){out.neg=String(e.message||e)}}
  return out}""")
print(json.dumps(r, ensure_ascii=False, indent=1))
