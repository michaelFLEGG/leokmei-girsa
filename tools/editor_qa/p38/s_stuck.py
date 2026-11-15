pg.evaluate("()=>{if(typeof setEdit==='function')setEdit(true)}")
pg.wait_for_timeout(500)
mode=os.environ.get('ACT','safe')
r = pg.evaluate("""async (mode)=>{
  const H=window.__p27;await H.skpOpen('shabbat-p3');await new Promise(r=>setTimeout(r,1500));
  const R=H.SKP.rev;const i=R.items.findIndex(x=>x.iid==='s25');R.i=i;H.skpShow();await new Promise(r=>setTimeout(r,800));
  H.skpAccept(true);await new Promise(r=>setTimeout(r,500));
  const m=document.querySelector('#skmstuck');if(!m)return {nodialog:1,flash:(document.querySelector('#edflash')||{}).textContent,conf:!!R.conflict};
  const txt=m.innerText;const before=H.ED.length;
  m.querySelector('[data-a='+mode+']').click();await new Promise(r=>setTimeout(r,1500));
  const g=H.SKM.ghost;
  return {txt,conf:!!R.conflict,added:H.ED.length-before,dec:R.dec['s25']&&R.dec['s25'].act,i:R.i,edit:!!(g&&g.classList.contains('edit')),bad:!!document.querySelector('.skmbad')}}""", mode)
print(json.dumps(r, ensure_ascii=False, indent=1))
pg.screenshot(path='_work/p38/stuck-'+mode+'.png')
