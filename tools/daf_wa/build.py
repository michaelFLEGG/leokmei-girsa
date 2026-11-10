# -*- coding: utf-8 -*-
"""הדף היומי בווטסאפ (פרומפט 23, 8.11.2026) - תצוגת הטלפון הקלה של הדף, היעד של הקישור בהודעה.

רץ בסוף build_all, אחרי שכל המסכתות נבנו, וקורא את site/<slug>.data.js שהבנייה כבר כתבה
(אותו מנוע תצוגה, אותם נתונים מן הוורד). כותב:
  site/daf/<slug>-<n>.html   - דף מעבר (פרומפט 28, 9.11.2026): נושא את תגיות התצוגה המקדימה (הכרטיס היומי) ומוביל
                               מיד אל הדף עצמו בדף המסכת באתר (/<slug>.html?src=wa#daf=<דף>). כך גם הודעות ישנות
                               שכבר נשלחו מגיעות לאתר, והקישור בהודעות אינו משתנה.
  site/daf-preview/<slug>-<n>.html - תצוגת הטלפון הקלה הקודמת (עמודת 20.75em בפרנק, משנה מנוקדת בוילנא). נשמרה
                               בכתובת פנימית, בלי קישור אליה ובלי אינדוקס.
  site/daf/index.html        - leokmei.com/daf: מפנה תמיד לדף של היום
  site/daf/data/*.json       - תוכן ההודעה היומית (מ-data/daf-wa), ללוח ולשולח
  site/daf/og/*.jpg          - כרטיס התצוגה המקדימה של כל דף (נוצר ב-card.py ונשמר במאגר)
  site/daf/wa/*.jpg          - פרומפט 30: הכרטיס הריבועי שנשלח כתמונה בווטסאפ (card.py, card-sq.html). בלעדיו ההודעה אינה יוצאת
  site/daf-board.html        - לוח ההכנה (למנהל בלבד; השרת בודק את המפתח)
תצוגת המחשב של האתר אינה משתנה: זה דף חדש ונפרד.
כישלון כאן אינו מפיל את בניית האתר, אבל נכתב בקול (עצירה רועשת) ל-site/daf/build-report.json."""
import datetime as dt
import html as H
import io
import json
import os
import re
import shutil
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DATA = os.path.join(ROOT, 'data', 'daf-wa')
OG_TITLE = 'לאוקמי גירסא - קיצור הדף היומי'
SITE_URL = 'https://leokmei.com'
NK = re.compile('[֑-ׇ]')
HEB = [(400, 'ת'), (300, 'ש'), (200, 'ר'), (100, 'ק'), (90, 'צ'), (80, 'פ'), (70, 'ע'), (60, 'ס'), (50, 'נ'), (40, 'מ'),
       (30, 'ל'), (20, 'כ'), (10, 'י'), (9, 'ט'), (8, 'ח'), (7, 'ז'), (6, 'ו'), (5, 'ה'), (4, 'ד'), (3, 'ג'), (2, 'ב'), (1, 'א')]


def letters(n):
    if n == 15:
        return 'טו'
    if n == 16:
        return 'טז'
    t = ''
    for v, c in HEB:
        while n >= v:
            t += c
            n -= v
    return t.replace('יה', 'טו').replace('יו', 'טז') if t.endswith(('יה', 'יו')) else t


def gq(n):
    t = letters(n)
    return t[:-1] + '"' + t[-1] if len(t) > 1 else t + "'"


def num_of(heb):
    v = dict((c, x) for x, c in HEB)
    return sum(v.get(c, 0) for c in heb)


# ------------------------------------------------------------ הדף היומי (מאותו מקור כמו daf-yomi.js)
def cycle():
    js = io.open(os.path.join(ROOT, 'tools', 'daf_yomi.js'), encoding='utf-8').read()
    L = [(a, b, int(c), int(d)) for a, b, c, d in re.findall(r"\['([^']+)','([a-z-]+)',(\d+),(\d+)\]", js)]
    if len(L) < 40:
        raise SystemExit('עצירה: רשימת המסכתות ב-daf_yomi.js לא נקראה')
    return L


def daf_of(day, L=None):
    """(שם, slug, מספר דף, הדף האחרון במסכת) ליום נתון"""
    L = L or cycle()
    tot = sum(x[3] for x in L)
    k = (day - dt.date(2020, 1, 5)).days % tot
    for name, slug, first, cnt in L:
        if k < cnt:
            return name, slug, first + k, first + cnt - 1
        k -= cnt


def date_of(slug, n, around, L=None):
    """התאריך שבו נלמד הדף במחזור הקרוב ביותר ל-around"""
    L = L or cycle()
    tot = sum(x[3] for x in L)
    off = 0
    for name, s, first, cnt in L:
        if s == slug:
            off += n - first
            break
        off += cnt
    base = dt.date(2020, 1, 5) + dt.timedelta(days=off)
    k = round((around - base).days / tot)
    return base + dt.timedelta(days=k * tot)


# ------------------------------------------------------------ נתוני המסכת
def load_data(site, slug):
    p = os.path.join(site, slug + '.data.js')
    if not os.path.exists(p):
        return None
    s = io.open(p, encoding='utf-8').read()
    return json.loads(s[s.index('{'):s.rindex('}') + 1])


def daf_num(label):
    return num_of(re.sub(r'[^א-ת]', '', label or ''))


def mishna_src(slug):
    p = os.path.join(ROOT, 'data', 'mishna', slug + '.json')
    if not os.path.exists(p):
        return None
    try:
        return json.load(io.open(p, encoding='utf-8')).get('chapters')
    except Exception:
        return None


def norm(w):
    return re.sub(r'[^א-ת]', '', NK.sub('', w))


def vocalize(html_line, src_words, ptr):
    """מילה בלי ניקוד מקבלת את הניקוד מן המשנה המנוקדת (אותה מילה, בסדר הופעתה). חלוקת השורות - של הוורד"""
    out = []
    for part in re.split(r'(<[^>]+>)', html_line):
        if part.startswith('<'):
            out.append(part)
            continue
        toks = re.split(r'(\s+)', part)
        for i, w in enumerate(toks):
            n = norm(w)
            if not n or len(n) < 2:
                continue
            if NK.search(w):
                for j in range(ptr[0], min(ptr[0] + 8, len(src_words))):
                    if norm(src_words[j]) == n:
                        ptr[0] = j + 1
                        break
                continue
            for j in range(ptr[0], min(ptr[0] + 8, len(src_words))):
                sw = src_words[j]
                if norm(sw) == n:
                    core = re.sub(r'[^ְ-ׇא-ת]', '', sw)
                    m = re.match(r'^([^א-ת]*)(.*?)([^א-ת]*)$', w)
                    toks[i] = m.group(1) + core + m.group(3) if m else w
                    ptr[0] = j + 1
                    break
        out.append(''.join(toks))
    return ''.join(out)


# ------------------------------------------------------------ כותרות צד: לעולם לא יותר משתי מילים
SPLITS = []
CONNECT = {'אלא', 'ומאי', 'מאי', 'והא', 'ואכתי', 'ואי', 'ואימא', 'איני', 'ומי', 'ולא', 'והתניא', 'והתנן', 'ורמינהי',
           'דתניא', 'דתנן', 'תא', 'אי', 'אמר', 'ואמר', 'מתיב', 'בעי', 'בעא', 'ובא', 'א"ל', 'וא"ל'}
NAMEW = {"ר'", 'רב', 'רבי', 'בר', 'בן', 'ברבי', 'ורב', "ור'", 'רבן', 'ורבי', 'דרב', 'מרב'}


def rail_split(a, slug, n, uid):
    parts = re.split(r'<br\s*/?>', a or '')
    head, extra = parts[0].strip(), [x.strip() for x in parts[1:] if x.strip()]
    plain = H.unescape(re.sub(r'<[^>]+>', '', head)).strip()
    words = plain.split()
    if len(words) <= 2:
        return head, extra
    cut = None
    for i in range(min(2, len(words))):
        if words[i].endswith((':', '?')):
            cut = i + 1
            break
    if cut is None:
        if words[0].rstrip(',') in CONNECT:
            cut = 1                                   # "אלא | אמר דוד:"
        elif words[1] in NAMEW or words[2] in NAMEW or words[-1].endswith(':'):
            cut = 0                                   # שם דובר ארוך: כולו לתוך השורה, לא נחתך באמצע
        else:
            cut = 2
    rail, rest = ' '.join(words[:cut]), ' '.join(words[cut:])
    SPLITS.append({'slug': slug, 'daf': n, 'uid': uid, 'was': plain, 'rail': rail, 'inline': rest})
    return H.escape(rail, quote=False), [H.escape(rest, quote=False)] + extra


def clean(t):
    t = re.sub(r'(&nbsp;\s*){2,}', '  ', t or '')
    return t.replace('\t', ' ')


REDIRECT_TPL = '''<!DOCTYPE html>
<html lang="he" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>@@TITLE@@</title>
<meta name="description" content="@@DESC@@">
<meta name="robots" content="noindex,follow">
<meta property="og:type" content="article"><meta property="og:locale" content="he_IL">
<meta property="og:site_name" content="לאוקמי גירסא"><meta property="og:title" content="@@OGTITLE@@">
<meta property="og:description" content="@@DESC@@"><meta property="og:url" content="@@URL@@">
<meta property="og:image" content="@@OG@@"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="480">
<meta property="og:image:alt" content="@@DAF@@"><meta name="twitter:card" content="summary_large_image">
<style>html,body{margin:0;background:#fdfbf6;color:#2a2520;font-family:serif}p{text-align:center;margin-top:30vh;font-size:16px;color:#7a7060;line-height:1.8}a{color:#8f6a1e}</style>
<script>(function(){var t=@@JS@@;try{var q=new URLSearchParams(location.search);q.delete("src");var x=q.toString();if(x)t=t.replace("?src=wa","?src=wa&"+x);}catch(e){}location.replace(t);})();</script>
</head><body><p>פותח את @@DAF@@ באתר...<br><a href="@@HREF@@">לחצו כאן אם הדף אינו נפתח</a></p></body></html>
'''


def redirect_html(slug, label, title, desc, url, og):
    """דף המעבר של הקישור בהודעה (פרומפט 28): תגיות התצוגה המקדימה כמו קודם (השרת מחזיר אותן בראש הדף,
    וכך ווטסאפ ממשיך להציג את הכרטיס היומי), ומעבר מיידי אל הדף בדף המסכת, בראש הדף.
    ?src=wa מסמן לדף המסכת להציג את רצועת ההצטרפות הדקה; הדף מסיר אותו מן הכתובת מיד."""
    target = '/%s.html?src=wa#daf=%s' % (slug, label)
    return (REDIRECT_TPL.replace('@@TITLE@@', H.escape(title + ' · ' + OG_TITLE)).replace('@@OGTITLE@@', H.escape(OG_TITLE))
            .replace('@@DESC@@', H.escape(desc)).replace('@@URL@@', url).replace('@@OG@@', og).replace('@@DAF@@', H.escape(title))
            .replace('@@JS@@', json.dumps(target, ensure_ascii=False))
            .replace('@@HREF@@', H.escape(target)))


def page_html(slug, D, n, src, heb_date_iso, has_og, content):
    name = D.get('masechet', '')
    title = '%s דף %s' % (name, gq(n))
    out = []
    pages = [p for p in D['pages'] if daf_num(p['daf']) == n]
    for p in pages:
        out.append('<div class="dafrow">%s</div>' % H.escape(p['daf']))
        for u in p['units']:
            k = u.get('k')
            a = clean(u.get('a', ''))
            if k == 'nose':
                w = u.get('w', '')
                out.append('<div class="nose">%s%s</div>' % ((H.escape(w) + ' ') if w else '', a))
            elif k == 'dh':
                out.append('<div class="r sp"><div class="h"></div><p class="dh">%s</p></div>' % a)
            elif k == 'hadran':
                out.append('<div class="hadran">%s</div>' % a)
            elif k == 'perek-start':
                out.append('<div class="perek">%s</div>' % a)
            elif k == 'hatz':
                out.append('<div class="hatz">• • •</div>')
            elif k == 'm':
                lines = u.get('lv') or u.get('l') or []
                words = []
                if src and u.get('mp') and u.get('mb'):
                    try:
                        words = src[u['mp'] - 1][u['mb'] - 1].split()
                    except (IndexError, TypeError):
                        words = []
                ptr = [0]
                body = ''.join('<p>%s</p>' % vocalize(clean(x[1]), words, ptr) for x in lines)
                out.append('<div class="r mrow"><div class="h"><span class="ml">%s</span></div><div class="mish">%s</div></div>'
                           % (H.escape(u.get('mbw') or 'משנה'), body))
            else:
                rail, extra = rail_split(a, slug, n, u.get('id'))
                ls = u.get('l') or []
                for i, (cls, txt) in enumerate(ls):
                    txt = clean(txt)
                    if not txt.strip() and i:
                        continue
                    if 'nose' in cls.split():
                        out.append('<div class="nose">%s</div>' % txt)
                        continue
                    pre = ''.join('<span class="am">%s</span> ' % x for x in extra) if i == 0 else ''
                    c = 'r' + (' sp' if 'sp' in cls.split() else '') + (' in' if 'in' in cls.split() else '')
                    out.append('<div class="%s"><div class="h">%s</div><p>%s%s</p></div>' % (c, rail if i == 0 else '', pre, txt))
    if not pages:
        return None
    url = '%s/daf/%s-%d' % (SITE_URL, slug, n)
    og = '%s/daf/og/%s-%d.jpg' % (SITE_URL, slug, n) if has_og else SITE_URL + '/brand/og-image.png'
    desc = title + (' · ' + content['card'] if content and content.get('card') else ' · קיצור הדף בתצוגה קלה לטלפון')
    full = '/%s.html#daf=%s' % (slug, H.escape(pages[0]['daf']))
    tpl = io.open(os.path.join(HERE, 'page.html'), encoding='utf-8').read()
    return (redirect_html(slug, pages[0]['daf'], title, desc, url, og), tpl.replace('@@TITLE@@', H.escape(title + ' · ' + OG_TITLE))
            .replace('@@OGTITLE@@', H.escape(OG_TITLE)).replace('@@DESC@@', H.escape(desc))
            .replace('@@URL@@', url).replace('@@OG@@', og).replace('@@DAF@@', H.escape(title))
            .replace('@@DATE@@', heb_date_iso).replace('@@FULL@@', full).replace('@@BODY@@', '\n'.join(out)))


def which_slugs(site, today):
    """המסכת של היום ושתי הבאות אחריה בלוח, וכל מסכת שיש לה תוכן להודעה"""
    L = cycle()
    _, s0, _, _ = daf_of(today, L)
    order = [x[1] for x in L]
    i = order.index(s0)
    want = [order[(i + j) % len(order)] for j in range(3)]
    for f in os.listdir(DATA) if os.path.isdir(DATA) else []:
        m = re.match(r'^([a-z-]+)-\d+\.json$', f)
        if m and m.group(1) not in want:
            want.append(m.group(1))
    return [s for s in want if os.path.exists(os.path.join(site, s + '.data.js'))], want


def run(site, today=None):
    rep = {'ok': True, 'pages': 0, 'content': 0, 'og': 0, 'wa': 0, 'wa_missing': [], 'errors': [], 'missing': [], 'at': dt.datetime.now(dt.timezone.utc).replace(tzinfo=None).isoformat() + 'Z'}
    out = os.path.join(site, 'daf')
    os.makedirs(os.path.join(out, 'data'), exist_ok=True)
    os.makedirs(os.path.join(out, 'og'), exist_ok=True)
    os.makedirs(os.path.join(out, 'wa'), exist_ok=True)
    prev = os.path.join(site, 'daf-preview')
    os.makedirs(prev, exist_ok=True)
    today = today or (dt.datetime.now(dt.timezone.utc).replace(tzinfo=None) + dt.timedelta(hours=2)).date()
    try:
        L = cycle()
        built, want = which_slugs(site, today)
        rep['missing'] = [s for s in want if s not in built]
        if not built:   # עצירה רועשת: אין אף מסכת בנויה - כנראה נתיב שגוי
            raise RuntimeError('לא נמצאה אף מסכת בנויה ב-' + site)
        index = []
        for slug in built:
            D = load_data(site, slug)
            if not D:
                rep['missing'].append(slug)
                continue
            src = mishna_src(slug)
            nums = sorted(set(daf_num(p['daf']) for p in D['pages'] if daf_num(p['daf'])))
            for n in nums:
                cj = os.path.join(DATA, '%s-%d.json' % (slug, n))
                content = json.load(io.open(cj, encoding='utf-8')) if os.path.exists(cj) else None
                og = os.path.join(DATA, 'og', '%s-%d.jpg' % (slug, n))
                if os.path.exists(og):
                    shutil.copy(og, os.path.join(out, 'og', os.path.basename(og)))
                    rep['og'] += 1
                wa = os.path.join(DATA, 'wa', '%s-%d.jpg' % (slug, n))
                if os.path.exists(wa):
                    shutil.copy(wa, os.path.join(out, 'wa', os.path.basename(wa)))
                    rep['wa'] += 1
                elif content and (content.get('check') or {}).get('ok'):
                    rep['wa_missing'].append('%s-%d' % (slug, n))   # יש תוכן בדוק ואין תמונה לשליחה - ההודעה לא תצא
                if content:
                    content = dict(content, last=nums[-1], url='leokmei.com/daf/%s-%d' % (slug, n))
                    io.open(os.path.join(out, 'data', '%s-%d.json' % (slug, n)), 'w', encoding='utf-8').write(json.dumps(content, ensure_ascii=False))
                    rep['content'] += 1
                d = date_of(slug, n, today, L)
                h = page_html(slug, D, n, src, d.isoformat(), os.path.exists(og), content)
                if h:
                    redir, phone = h
                    io.open(os.path.join(out, '%s-%d.html' % (slug, n)), 'w', encoding='utf-8', newline='').write(redir)
                    io.open(os.path.join(prev, '%s-%d.html' % (slug, n)), 'w', encoding='utf-8', newline='').write(phone)
                    rep['pages'] += 1
                    index.append({'slug': slug, 'n': n, 'date': d.isoformat(), 'content': bool(content), 'og': os.path.exists(og)})
        json.dump({'dafim': index, 'masechtot': built}, io.open(os.path.join(out, 'index.json'), 'w', encoding='utf-8'), ensure_ascii=False)
        gen = os.path.join(DATA, 'og', '_general.jpg')
        if os.path.exists(gen):
            shutil.copy(gen, os.path.join(out, 'og', '_general.jpg'))
        shutil.copy(os.path.join(HERE, 'index.html'), os.path.join(out, 'index.html'))
        shutil.copy(os.path.join(HERE, 'board.html'), os.path.join(site, 'daf-board.html'))
        json.dump(SPLITS, io.open(os.path.join(out, 'rail-splits.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
        rep['rail_splits'] = len(SPLITS)
    except Exception as e:
        rep['ok'] = False
        rep['errors'].append(repr(e))
        rep['trace'] = traceback.format_exc()[-1500:]
        print('!!! הדף היומי בווטסאפ: הבנייה נכשלה -', e, file=sys.stderr)
    json.dump(rep, io.open(os.path.join(out, 'build-report.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('הדף היומי בווטסאפ: %d דפים, %d הודעות, %d כרטיסים, %d תמונות לשליחה%s' % (rep['pages'], rep['content'], rep['og'], rep['wa'],
          '' if rep['ok'] else ' - נכשל!'))
    if rep['wa_missing']:
        print('!!! הדף היומי בווטסאפ: חסרה תמונה לשליחה (card.py --wa) -', ', '.join(rep['wa_missing']), file=sys.stderr)
    return rep


if __name__ == '__main__':
    run(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'site'))
