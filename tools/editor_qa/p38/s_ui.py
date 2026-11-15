pg.wait_for_timeout(2500)
st = lambda: pg.evaluate("()=>{const d=document.querySelector('#skpdup'),n=document.querySelector('#skpnext');return {dup:d&&d.textContent,dupOff:d&&d.classList.contains('off'),dupIn:d&&d.parentElement.id,next:n&&n.textContent,nextOff:n&&n.classList.contains('off'),cur:typeof cur!=='undefined'?cur:null}}")
print('start', st())
# go to perek with most dups
r=pg.evaluate("""()=>{const out=[];for(let i=0;i<SEC.length;i++){render(i);out.push(window.skpTop.state().dups)}return out}""")
print('dups per perek', r)
best=max(range(len(r)),key=lambda i:r[i])
pg.evaluate("(i)=>{render(i)}",best); pg.wait_for_timeout(800)
print('perek',best+1, st())
pg.click('#skpdup'); pg.wait_for_timeout(1200)
m=pg.evaluate("()=>{const e=document.querySelector('.sktdup');if(!e)return null;const cs=getComputedStyle(e);const r=e.getBoundingClientRect();return {txt:e.textContent.slice(0,60),outline:cs.outlineStyle+' '+cs.outlineWidth,bg:cs.backgroundColor,top:Math.round(r.top),h:innerHeight}}")
print('mark1', m)
pg.screenshot(path='_work/p38/shot-dup.png')
pg.click('#skpdup'); pg.wait_for_timeout(1000)
print('mark2', pg.evaluate("()=>{const e=document.querySelector('.sktdup');return e&&e.textContent.slice(0,60)}"))
# fix a dup: change the marked line's data and re-render via editor path
pg.evaluate("()=>{if(typeof setEdit==='function')setEdit(true)}"); pg.wait_for_timeout(600)
before=st()['dup']
ok=pg.evaluate("""()=>{const e=document.querySelector('.sktdup');if(!e)return 'nomark';const p=e.closest('p')||e;p.focus();
  const sel=getSelection();const rg=document.createRange();rg.selectNodeContents(p);rg.collapse(false);sel.removeAllRanges();sel.addRange(rg);
  document.execCommand('insertText',false,' תיקון בדיקה ייחודי');return 'typed'}""")
pg.wait_for_timeout(2500)
print('fix', ok, before, '->', st()['dup'])
# next
pg.click('#skpnext'); pg.wait_for_timeout(2500)
print('next1', pg.evaluate("()=>{const R=window.__p27.SKP.rev;return R?{jid:R.jid,i:R.i,iid:R.items[R.i].iid}:null}"), st())
pg.click('#skpnext'); pg.wait_for_timeout(1500)
print('next2', pg.evaluate("()=>{const R=window.__p27.SKP.rev;return R?{jid:R.jid,i:R.i,iid:R.items[R.i].iid}:null}"), st())
pg.screenshot(path='_work/p38/shot-next.png', clip={'x':0,'y':0,'width':1400,'height':120})
