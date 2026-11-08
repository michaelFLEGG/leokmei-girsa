# תרחיש: תג "סכם" בסרגל אינו מכסה שום כפתור, בכל רוחב. ובלחיצה - רשימה של הפרקים המוכנים.
import os
pg.evaluate("()=>{if(typeof setEdit==='function')setEdit(true)}")
pg.wait_for_timeout(1500)
r = pg.evaluate("""()=>{const t=document.getElementById('skptag');if(!t)return {err:'no tag'};
  const R=t.getBoundingClientRect(),vis=e=>{const r=e.getBoundingClientRect();const cs=getComputedStyle(e);return r.width>0&&r.height>0&&cs.visibility!=='hidden'&&cs.display!=='none'};
  const hits=[];document.querySelectorAll('button,a,select,input,[role=button]').forEach(e=>{if(e===t||t.contains(e)||!vis(e))return;
    const r=e.getBoundingClientRect();const ox=Math.min(R.right,r.right)-Math.max(R.left,r.left),oy=Math.min(R.bottom,r.bottom)-Math.max(R.top,r.top);
    if(ox>1&&oy>1)hits.push((e.id||e.className||e.tagName)+':'+(e.textContent||'').trim().slice(0,15))});
  const bar=document.getElementById('bar');
  return {text:t.textContent,title:t.title,rect:[Math.round(R.left),Math.round(R.top),Math.round(R.width),Math.round(R.height)],inView:R.left>=0&&R.right<=innerWidth&&R.top>=0,
    hits,barH:bar&&Math.round(bar.getBoundingClientRect().height),barScroll:bar&&[bar.scrollWidth,bar.clientWidth],docScroll:document.documentElement.scrollWidth-innerWidth}}""")
print(json.dumps(r, ensure_ascii=False))
pg.screenshot(path=os.environ.get('SHOT','_work/p27/tag.png'), clip={'x':0,'y':0,'width':pg.viewport_size['width'],'height':120})
pg.click('#skptag'); pg.wait_for_timeout(300)
print('menu', pg.evaluate("()=>[...document.querySelectorAll('#skptagm button')].map(b=>b.textContent)"))
