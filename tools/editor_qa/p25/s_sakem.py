# בדיקת פרומפט 25: סקירת "סכם פרק" לא נפגעה (הצעה מדומה, בלי כתיבה), ומצב "בחר נוסח" אינו מתערב בה
OUT = []
def row(name, val, ok):
    OUT.append(ok); print(('OK  ' if ok else 'FAIL') + ' %d %s | %s' % (W, name, json.dumps(val, ensure_ascii=False)[:300]))
fake = pg.evaluate(r"""()=>{const S=SEC[cur];const fu=flatU().filter(o=>o.pi>=S.from&&o.pi<=S.to&&o.u.k==='u'&&o.u.l&&o.u.l.length&&plain(o.u.l[0][1]).length>40);
  const o=fu[5];const orig=skmInter(skmUnits([o.u.id]));
  const lines=orig.split('\n');let i=lines.findIndex(l=>!/^\[/.test(l)&&l.trim().split(' ').length>4);
  const w=lines[i].split(' ');w.splice(2,1,'מילה-חדשה');lines[i]=w.join(' ');
  return {id:o.u.id,orig,text:lines.join('\n')}}""")
body = json.dumps({'ok': True, 'out': {'title': 'בדיקה', 'items': [{'iid': 't1', 'kind': 'seg', 'ids': [fake['id']], 'orig': fake['orig'], 'text': fake['text'], 'layers': ['ליטוש']}]}, 'job': {'jid': 'test', 'kind': 'seg', 'title': 'בדיקה'}, 'dec': {}}, ensure_ascii=False)
pg.route('**/sakem/out*', lambda r: r.fulfill(status=200, content_type='application/json; charset=utf-8', body=body.encode('utf-8')))
pg.evaluate("()=>skpOpen('test')"); pg.wait_for_timeout(1800)
s = pg.evaluate("()=>({rev:document.body.classList.contains('skprev'),ghost:!!document.querySelector('.skmghost.skp'),add:document.querySelectorAll('.skmghost .skpadd').length,del:document.querySelectorAll('.skmghost del.skpdel').length,bar:!!document.getElementById('skpbar')})")
row('סכם פרק: הסקירה נפתחת, ההשוואה מסמנת מה נוסף ומה נמחק', s, s['rev'] and s['ghost'] and s['add'] >= 1 and s['del'] >= 1 and s['bar'])
pg.screenshot(path='_work/p25-sakem-%d.png' % W)
pg.keyboard.press('n'); pg.wait_for_timeout(700)
a = pg.evaluate("()=>({alt:document.body.classList.contains('altmode'),views:document.querySelectorAll('#flow .altv').length})")
row('בזמן סקירת סכם: N אינו פותח את בחר נוסח', a, not a['alt'] and a['views'] == 0)
pg.keyboard.press('Delete'); pg.wait_for_timeout(1200)
e = pg.evaluate("()=>({rev:document.body.classList.contains('skprev'),ghost:!!document.querySelector('.skmghost')})")
row('Delete בסכם: נדחה והסקירה הסתיימה', e, not e['rev'] and not e['ghost'])
dec = [x for x in BLOCKED if '/sakem/dec' in x]
row('ההכרעה בסכם נשלחה ל-/sakem/dec כרגיל', len(dec), len(dec) == 1)
pg.keyboard.press('n'); pg.wait_for_timeout(1500)
b = pg.evaluate("()=>({alt:document.body.classList.contains('altmode'),views:document.querySelectorAll('#flow .altv').length})")
row('אחרי סכם: בחר נוסח עובד', b, b['alt'] and b['views'] == 1)
print('SUMMARY', sum(OUT), '/', len(OUT))
