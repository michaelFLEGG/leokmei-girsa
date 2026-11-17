# -*- coding: utf-8 -*-
# פרומפט 56 ג3: כלי מדידה על עותק בדיקה (כל כתיבה לשרת חסומה). טרם הושלם - הסקירה לא נפתחה מול נתוני הבדיקה
# פרומפט 56 ג3: מדידת "קבל את כל הנותרים בפרק" על עותק בדיקה: כל כתיבה לשרת חסומה, ההצעות מקובץ שבמאגר
import json,sys,time
from playwright.sync_api import sync_playwright
REPO='/home/user/leokmei-girsa'
jid=sys.argv[1]; per=int(sys.argv[2]); label=sys.argv[3]
out=json.load(open(f'{REPO}/data/sakem/out/{jid}.json'))
job={'jid':jid,'slug':'shabbat','kind':'perek','perek':per,'title':'בדיקה','st':'ready','n':len(out.get('items',[]))}
writes=[]
def route(r):
    u=r.request.url;m=r.request.method
    if 'leokmei-suggest' not in u: return r.continue_()
    if m!='GET': writes.append(u.split('?')[0].split('/',3)[-1]); return r.fulfill(status=200,content_type='application/json',body='{"ok":1}')
    if '/sakem/jobs' in u: return r.fulfill(status=200,content_type='application/json',body=json.dumps({'items':[job]}))
    if '/sakem/out' in u: return r.fulfill(status=200,content_type='application/json',body=json.dumps({'job':job,'out':out,'dec':{}}))
    if '/sakem/' in u or '/bakara' in u: return r.fulfill(status=200,content_type='application/json',body='{"items":[],"doc":{}}')
    return r.continue_()
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1243/chrome-linux64/chrome')
    c=b.new_context(viewport={'width':1400,'height':900});c.route('**/*',route)
    c.add_init_script("localStorage.setItem('lg-admin','1');localStorage.setItem('lg-adm','fixture-no-key');")
    pg=c.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.on('dialog',lambda d:d.accept())
    t=time.time();pg.goto('https://leokmei.com/shabbat.html#daf='+sys.argv[4],wait_until='networkidle',timeout=180000);load=time.time()-t
    pg.wait_for_timeout(4000)
    res={'load_s':round(load,2)}
    pg.evaluate("()=>{const b=document.querySelector('#skpbtn');if(b)b.click()}");pg.wait_for_timeout(1500)
    res['btn']=pg.evaluate("()=>{const b=document.querySelector('#skpbtn');return b?b.textContent.trim().slice(0,60):''}")
    # בלוח: כפתור "סקור"
    res['panel']=pg.evaluate("()=>[...document.querySelectorAll('button')].filter(b=>/סקור|המשך סקירה|סקירה/.test(b.textContent)).map(b=>b.textContent.trim().slice(0,30)).slice(0,6)")
    pg.evaluate("()=>{const b=[...document.querySelectorAll('button')].find(b=>/^(סקור|המשך|התחל)/.test(b.textContent.trim()));if(b)b.click()}");pg.wait_for_timeout(4000)
    res['all']=pg.evaluate("()=>[...document.querySelectorAll('[data-a],[data-k]')].map(b=>(b.dataset.a||b.dataset.k)).filter(x=>/all/.test(x))")
    print('pre',json.dumps(res,ensure_ascii=False));pg.screenshot(path=label+'-rev.png')
    t=time.time()
    pg.evaluate("()=>{const b=document.querySelector('[data-a=allper],[data-k=allper]');window.__T0=performance.now();if(b)b.click()}")
    pg.wait_for_function("()=>document.querySelector('#skpalltoast')||(document.querySelector('#toast')&&/התקבלו/.test(document.querySelector('#toast').textContent))",timeout=90000)
    res['all_ms']=pg.evaluate("()=>Math.round(performance.now()-window.__T0)")
    res['msg']=pg.evaluate("()=>{const t=document.querySelector('#skpalltoast')||document.querySelector('#toast');return t?t.textContent:''}")
    print(json.dumps(res,ensure_ascii=False),errs[:3],writes[:5])
    pg.screenshot(path=label+'-open.png')
    b.close()
