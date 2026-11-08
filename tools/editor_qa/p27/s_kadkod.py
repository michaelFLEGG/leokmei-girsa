# תרחיש: "ערוך" בקטע "ושמתי כדכד" (בבא בתרא עה.) - המנהל משנה רק מילים בשורה האחרונה ומקבל.
# MODE=direct  - הנוסח כפי שהוצע (קבל בלי עריכה)
# MODE=edit    - כניסה לעריכה במקום, "כזה וכזה" -> "כדין וכדין", קריאה חזרה מן הדף, וקבלה
import os
MODE = os.environ.get('MODE', 'edit')
pg.evaluate("()=>{if(typeof setEdit==='function')setEdit(true)}")
pg.wait_for_timeout(800)
r = pg.evaluate("""async (mode)=>{
  const H=window.__p27;await H.skpOpen('bava-batra-p5');
  await new Promise(r=>setTimeout(r,1200));
  const R=H.SKP.rev;if(!R)return {err:'no rev',toast:(document.getElementById('toast')||{}).textContent,fl:[...document.querySelectorAll('.flash,.hint')].map(x=>x.textContent)};
  let i=R.items.findIndex(x=>x.text.indexOf('כדכד')>-1);R.i=i;H.skpShow();
  await new Promise(r=>setTimeout(r,500));
  const it=R.items[i];
  const out={iid:it.iid,conflict:R.conflict,same:H.skmSame(it.ids,it.orig)};
  let text=it.text;
  if(mode==='edit'){
    H.skpEditOn();
    const g=H.SKM.ghost;const w=document.createTreeWalker(g,NodeFilter.SHOW_TEXT);let n,hit=0;
    while((n=w.nextNode()))if(n.nodeValue.indexOf('כזה וכזה')>-1){n.nodeValue=n.nodeValue.replace('כזה וכזה','כדין וכדין');hit++}
    out.hit=hit;
    text=H.skmReadBack(g);if(!hit){text=text.replace('כזה וכזה','כדין וכדין');out.hitRB=text.indexOf('כדין וכדין')>-1}
    out.readback=text;out.sameAsProp=text===it.text}
  try{const res=H.skpApplyOne(it,text);out.ok=true;out.n=res.n}catch(e){out.ok=false;out.err=String(e.message||e)}
  /* מה יש עכשיו בדף, אחרי ההחלה */
  const fu=H.flatU();const k0=fu.findIndex(o=>JSON.stringify(o.u).indexOf('סעודה לצדיקים')>-1);
  const tx=h=>String(h||'').replace(/<[^>]+>/g,'').replace(/&quot;/g,'"').replace(/&#x27;/g,"'");
  out.after=fu.slice(Math.max(0,k0-1),k0+5).map(o=>o.u.k+'#'+o.u.id+' ['+tx(o.u.a||o.u.w||'')+'] '+(o.u.l||[]).map(l=>(l[0].indexOf('nose')>-1?'(נושא)':'')+tx(l[1])).join(' / '));
  return out}""", MODE)
print(json.dumps(r, ensure_ascii=False, indent=1))
