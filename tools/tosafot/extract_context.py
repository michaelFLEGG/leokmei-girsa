# -*- coding: utf-8 -*-
"""extract_context.py - מחלץ לכל עמוד את שורות הלאוקמי גירסא כפי שהן באתר, ואת שורות הגמרא של ספריא.

הקלט הוא תוצר הבנייה המקומית (site/<slug>.data.js) וקובץ המקורות (data/sources/<slug>.json).
הפלט tosafot/<slug>/context.json נשמר במאגר, כדי שהרצת המנועים והעיגון לא יזדקקו לבנייה:
  {"מב.": {"daf": "42a", "gemara": ["שורה 1 מנוקדת", ...], "lines": ["שורת לאוקמי 1", ...]}}
שורת גמרא i של ספריא היא gemara[i-1], והיא אותה שורה שאליה מצביע ref התוספות (Tosafot on X 42a:4:1 = שורה 4).

    uv run python tools/tosafot/extract_context.py sukkah מב. מב: מג. מג: מד. מד:
"""
import os, sys, re, json, io, html, subprocess
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def plain(h):
    t = re.sub(r'<[^>]+>', '', h)
    t = html.unescape(t)
    return re.sub(r'\s+', ' ', t).strip()


def main():
    tolerant = '--tolerant' in sys.argv      # בית החרושת: עמוד שאינו בבנייה אינו עוצר את השאר; הרשימה נשמרת וגלויה
    argv = [a for a in sys.argv[1:] if a != '--tolerant']
    slug, dafs = argv[0], argv[1:]
    missing = []
    js = os.path.join(ROOT, 'site', slug + '.data.js')
    if not os.path.exists(js):
        raise SystemExit('עצירה: אין site/%s.data.js. הרץ קודם בנייה מקומית של המסכת' % slug)
    code = "const fs=require('fs');const D=new Function(fs.readFileSync(%s,'utf8')+';return DATA')();process.stdout.write(JSON.stringify(D.pages.filter(p=>%s.includes(p.daf)).map(p=>({daf:p.daf,perek:p.perek,units:p.units.map(u=>({ref:u.ref||null,l:(u.l||[]).map(x=>x[1])}))}))))" % (json.dumps(js), json.dumps(dafs, ensure_ascii=False))
    out = subprocess.run(['node', '-e', code], capture_output=True, text=True, encoding='utf-8', check=True).stdout
    pages, dups = {}, []
    for p_ in json.loads(out):
        if p_['daf'] in pages:
            dups.append(p_['daf'])          # תווית דף כפולה בקובץ הוורד: כמו בדפדפן (pageIdx), נשמר הדף הראשון
            continue
        pages[p_['daf']] = p_
    src = json.load(io.open(os.path.join(ROOT, 'data', 'sources', slug + '.json'), encoding='utf-8'))['pages']
    res = {}
    for d in dafs:
        if d not in pages:
            if tolerant:
                missing.append(d)
                continue
            raise SystemExit('עצירה: העמוד %s אינו בבנייה' % d)
        if d not in src:
            if tolerant:
                missing.append(d)
                continue
            raise SystemExit('עצירה: העמוד %s אינו בקובץ המקורות' % d)
        lines = []
        for ui, u in enumerate(pages[d]['units']):
            for x in u['l']:
                t = plain(x)
                if t:
                    lines.append(t)
        res[d] = {'daf': src[d]['daf'], 'perek': pages[d]['perek'], 'gemara': src[d]['gemara'], 'lines': lines}
        print(d, 'שורות לאוקמי:', len(lines), 'שורות גמרא:', len(src[d]['gemara']))
    path = os.path.join(ROOT, 'tosafot', slug, 'context.json')
    old = json.load(io.open(path, encoding='utf-8')) if os.path.exists(path) else {}
    old.update(res)
    with io.open(path, 'w', encoding='utf-8') as f:
        json.dump(old, f, ensure_ascii=False, indent=1)
    if tolerant:
        with io.open(os.path.join(ROOT, 'tosafot', slug, 'context-missing.json'), 'w', encoding='utf-8') as f:
            json.dump({'missing': missing, 'duplicateLabels': sorted(set(dups))}, f, ensure_ascii=False, indent=1)
        print('עמודים שאינם בבנייה (ללא הקשר, ההנחה לפי השכנים):', missing, '| תוויות דף כפולות בקובץ הוורד:', sorted(set(dups)))


if __name__ == '__main__':
    main()
