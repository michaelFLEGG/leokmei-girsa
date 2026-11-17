# -*- coding: utf-8 -*-
"""מחולל "שורה שהתארכה" (פרומפט 41, 15.11.2026).

בלאוקמי גירסא כל פסקה בוורד היא שורה שבעל הפרויקט כיוון. בהדפסה המוגדלת (a4-large) חלק מהשורות גולשות.
הכלי הזה:
  א. מריץ את מנוע ההדפסה על מסכת שלמה בשני הפרופילים (a4, a4-large), עם רישום השורות של כל פסקה.
     כלי 1 (הצרה עד 2.5%) כבר מוחל בתוך המנוע בשתי ההרצות.
  ב. פסקה גולשת = יותר שורות ב-a4-large מאשר ב-a4. לכל אחת: הדף, הטקסט, המילים שגלשו, ו"כמה חסר"
     (רוחב הגלישה בפיקסלים, ובאותיות ממוצעות של הגוף).
  ג. כלי 2 (מחיקת תווים מכנית) בקוד בלבד, מן הרשימה data/overflow/abbr.json וכללי הרווחים.
  ד. כלים 3-5 (ניסוח קצר, חיתוך, העברה) נקראים מקובץ ההצעות של העובד: data/overflow/sugg/<מסכת>.json.
  ה. כל הצעה נבדקת במנוע לפני שהיא נכנסת לרשימה: אינה גולשת ב-a4-large, אינה גולשת ב-a4, וכל חלק נכנס בשורות
     שהיו לו ב-a4 (חיתוך: כל חלק בשורה אחת). הצעה שנכשלה אינה מוצגת.

הרצה (ענן או מחשב, Chromium של Playwright):
  uv run --with playwright python tools/overflow/overflow_gen.py --slug berakhot --site <תיקיית האתר>
  --reuse: משתמש בדוחות ההרצה הקודמת (בדיקת הצעות בלבד).
הפלט: data/overflow/<מסכת>.json (נקרא בדף, במצב מנהל).
"""
import argparse, hashlib, html as H, io, json, math, os, re, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
RENDER = os.path.join(ROOT, 'tools', 'print', 'render_pdf.py')
ODIR = os.path.join(ROOT, 'data', 'overflow')
NIK = re.compile(r'[֑-ׇ⁠]')


def run_engine(site, slug, profile, out, extra=(), probe=None, frm=None):
    # פרומפט 56: a4 הישן בוטל ו-a4 מקבל את המוגדל. השורה שכיוון הכותב נמדדת בפרופיל הישן מן הארכיון (a4ref)
    eng = 'a4ref' if profile == 'a4' else profile
    cmd = [sys.executable, RENDER, '--site', site, '--slug', slug, '--dev', '--no-pdf', '--profile', eng, '--out', out]
    cmd += (['--from', frm, '--to', frm] if frm else ['--all', '--lines'])
    if probe:
        cmd += ['--probe', probe]
    cmd += list(extra)
    p = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
    if p.returncode not in (0, 3):
        raise SystemExit('עצירה: מנוע ההדפסה נכשל (%s):\n%s' % (profile, (p.stdout + p.stderr)[-1500:]))
    return p.stdout


def plain(h):
    return H.unescape(re.sub(r'<[^>]+>', '', h or ''))


def key_id(k):
    return hashlib.sha1(k.encode('utf-8')).hexdigest()[:16]


# ---------- כלי 2: מחיקת תווים מכנית ----------
def protected_spans(t):
    """אזורים שאסור לגעת בהם בטקסט הנקי: ציטוט/פסוק במירכאות, סוגריים מרובעים, וסוגריים עגולים (מראי מקום)"""
    out = []
    for m in re.finditer(r"(?:^|(?<=[\s>דושכלבמה]))'[^']{2,}?'(?=[\s.,:;!?)\-]|$)", t):
        out.append((m.start(), m.end()))
    for m in re.finditer(r'"[^"]{4,}?"(?=[\s.,:;!?)\-]|$)', t):
        if ' ' in m.group(0):      # מירכאות כפולות של ציטוט (לא ראשי תיבות)
            out.append((m.start(), m.end()))
    for m in re.finditer(r'\[[^\]]*\]|\([^)]*\)', t):
        out.append((m.start(), m.end()))
    return out


def text_runs(h):
    """[[טקסט, מוגן, תגית]] - הטקסט שבין התגיות. מוגן: תוכן <i class="ps"> (פסוק) ותוכן <sup> (הפניה לתוספות)"""
    runs, st, pos = [], [], 0
    for m in re.finditer(r'<(/?)([a-z0-9]+)([^>]*)>', h):
        if m.start() > pos:
            runs.append([h[pos:m.start()], any(st), False])
        tag = m.group(0)
        if m.group(2) in ('br',) or tag.endswith('/>'):
            pass
        elif not m.group(1):
            st.append('class="ps"' in m.group(3) or m.group(2) == 'sup')
        elif st:
            st.pop()
        runs.append([tag, True, True])
        pos = m.end()
    if pos < len(h):
        runs.append([h[pos:], any(st), False])
    return runs


def mech_cands(h, abbr):
    """המקומות שבהם כלי 2 יכול לפעול ב-HTML: (runs, [(מקטע, התחלה, סוף, חדש, תיאור, סוג, חתימה)]).
    החתימה (סוג, מלא, מספר המופע) זהה בשתי צורות ה-HTML של אותה שורה (בנתונים ובהדפסה), וכך ההצעה שנבדקה
    בהדפסה היא אותה הצעה שנכנסת לוורד"""
    runs = text_runs(h)
    flat, idx = '', []
    for i, (t, prot, is_tag) in enumerate(runs):
        if is_tag:
            continue
        u = H.unescape(t)
        idx.append((i, len(flat), len(flat) + len(u)))
        flat += u
    spans = protected_spans(flat)

    def is_prot(a, b):
        return any(not (b <= x or a >= y) for x, y in spans)

    def run_of(a, b):
        for i, s0, e0 in idx:
            if s0 <= a and b <= e0 and not runs[i][1]:
                return i, s0
        return None

    cands = []
    for it in abbr:
        a, b = it['long'], it['short']
        if it['kind'] == 'num':
            pat = re.compile(r'(?<![א-ת"\'])' + re.escape(a) + r'(?= [א-ת])')
        else:
            pat = re.compile(r'(?<![א-ת"\'])' + re.escape(a) + r'(?![א-ת"])')
        k = 0
        for m in pat.finditer(flat):
            if is_prot(m.start(), m.end()):
                continue
            ro = run_of(m.start(), m.end())
            if not ro:
                continue
            cands.append((ro[0], m.start() - ro[1], m.end() - ro[1], b, '%s במקום %s' % (b, a), 'abbr:' + a + '>' + b, ('abbr', a, k)))
            k += 1
    k = 0
    for m in re.finditer(r' {2,}| +(?=[.,:;!?])|(?<= -) {2,}', flat):
        if is_prot(m.start(), m.end()):
            continue
        ro = run_of(m.start(), m.end())
        if not ro:
            continue
        rep = '' if re.match(r' +(?=[.,:;!?])', flat[m.start():]) else ' '
        cands.append((ro[0], m.start() - ro[1], m.end() - ro[1], rep, 'רווח מיותר', 'space', ('space', '', k)))
        k += 1
    return runs, cands


def apply_cands(runs, sel):
    rr = [list(x) for x in runs]
    by = {}
    for c in sel:
        by.setdefault(c[0], []).append(c)
    for i, cs in by.items():
        u = H.unescape(rr[i][0])
        for c in sorted(cs, key=lambda c: -c[1]):
            u = u[:c[1]] + c[3] + u[c[2]:]
        rr[i][0] = H.escape(u, quote=False)
    return ''.join(x[0] for x in rr)


def mech_variants(h_print, h_data, abbr):
    """הצעות כלי 2: [(html להדפסה לבדיקה, html לנתונים, תיאור, סוג)] - אחת אחת מן הסוף, ואחר כך הכול יחד"""
    rp, cp = mech_cands(h_print, abbr)
    rd, cd = mech_cands(h_data, abbr)
    bd = {c[6]: c for c in cd}
    pairs = [(c, bd[c[6]]) for c in cp if c[6] in bd]
    out = []
    for c, d in sorted(pairs, key=lambda x: (-x[1][0], -x[1][1])):
        out.append((apply_cands(rp, [c]), apply_cands(rd, [d]), d[4], d[5]))
    if len(pairs) > 1:
        out.append((apply_cands(rp, [c for c, d in pairs]), apply_cands(rd, [d for c, d in pairs]),
                    ' + '.join(sorted({d[4] for c, d in pairs})), 'multi'))
    return out


# ---------- הצעות העובד (כלים 3-5) ----------
def _flatmap(h):
    """ה-HTML כמקטעים, והטקסט הנקי עם מיפוי כל תו (מקטע, היסט). רווח קשיח נחשב רווח (העובד ראה את ההדפסה)"""
    runs = text_runs(h)
    flat, mp, depth, dep_at = '', [], 0, {}
    for i, (t, prot, is_tag) in enumerate(runs):
        if is_tag:
            if re.match(r'^<[a-z]', t) and not t.endswith('/>') and not t.startswith('<br'):
                depth += 1
            elif t.startswith('</'):
                depth -= 1
            continue
        dep_at[i] = depth
        u = H.unescape(t).replace('\u00a0', ' ')
        for k, ch in enumerate(u):
            flat += ch
            mp.append((i, k))
    return runs, flat, mp, dep_at


def _norm_needle(x):
    return re.sub(r'\u2060\d+', '', x).replace('\u00a0', ' ').replace('\u2060', '')


def worker_to_html(h, s0):
    """הצעת עובד ({tool:3, find, replace} / {tool:4, split_before, side}) -> הצעה עם HTML. שומר את העיצוב (הסבר, פסוק)"""
    s0 = dict(s0)
    for f in ('find', 'split_before', 'replace'):
        if s0.get(f) is not None:
            s0[f] = _norm_needle(s0[f])
    s = dict(s0)
    runs, flat, mp, dep_at = _flatmap(h)
    key = s0.get('find') if s0.get('tool') == 3 else s0.get('split_before')
    if not key:
        return None, 'הצעה לא מוכרת'
    n = flat.count(key)
    if n != 1:
        return None, 'המחרוזת מופיעה %d פעמים' % n
    a = flat.index(key)
    b = a + len(key)
    if s0.get('tool') == 3:
        touched = sorted({mp[x][0] for x in range(a, b)})
        if any(runs[i][1] for i in touched):
            return None, 'שינוי בתוך פסוק או הפניה'
        rr = [list(x) for x in runs]
        texts = {i: H.unescape(rr[i][0]) for i in touched}
        # הטקסט החדש נכנס למקטע הראשון שהשינוי נוגע בו, ומן השאר נמחק מה שבטווח
        for idx, i in enumerate(touched):
            u = texts[i]
            ks = [mp[x][1] for x in range(a, b) if mp[x][0] == i]
            k0, k1 = min(ks), max(ks) + 1
            u = u[:k0] + (s0['replace'] if idx == 0 else '') + u[k1:]
            rr[i][0] = H.escape(u, quote=False)
        out = ''.join(x[0] for x in rr)
        out = re.sub(r'<(i|b)( class="[a-z]+")?>\s*</\1>', '', out)
        s.update(kind='replace', html=re.sub(r'  +', ' ', out).strip())
        return s, ''
    i, k = mp[a]
    if runs[i][1] and k:
        return None, 'חיתוך בתוך פסוק'
    # חיתוך בתחילת מקטע מעוצב: נקודת החיתוך זזה אל לפני תגיות הפתיחה שלו
    j = i
    if k == 0:
        while j > 0 and runs[j - 1][2] and re.match(r'^<[a-z]', runs[j - 1][0]):
            j -= 1
        cut_depth = dep_at[i] - (i - j)
    else:
        cut_depth = dep_at[i]
    if cut_depth != 0:
        return None, 'חיתוך בתוך עיצוב (הסבר, פסוק או אמוראים)'
    if k == 0:
        pre = ''.join(x[0] for x in runs[:j])
        post = ''.join(x[0] for x in runs[j:])
    else:
        u = H.unescape(runs[i][0])
        pre = ''.join(x[0] for x in runs[:i]) + H.escape(u[:k], quote=False)
        post = H.escape(u[k:], quote=False) + ''.join(x[0] for x in runs[i + 1:])
    p1, p2 = pre.rstrip(), post.strip()
    if len(plain(p1).split()) < 3 or len(plain(p2).split()) < 3:
        return None, 'אחד החלקים קצר משלוש מילים'
    if plain(p2).strip().startswith(('-', '–')) or plain(p1).strip().endswith(('-', '–')):
        return None, 'שורה שפותחת או נגמרת במקף'
    if re.search(r'(?:^|\s)(של|על|את|אל|עם|מן|כמו)$', plain(p1).strip()):
        return None, 'חיתוך אחרי מילית'
    s.update(kind='split', parts=[p1, p2], side=(s0.get('side') or '').strip())
    return s, ''


# ---------- בדיקה במנוע ----------
# האתר מעבד את ה-HTML של הפסקה לפני התצוגה (lgLook ב-build_site.py): רווח קבוע (.og, 1.3em) אחרי פסיק או נקודה
# שלפני אמוראים/כותרת בשורה, והמילים לכו"ע / נחלקו בסגנון אמוראים. הבדיקה מדפיסה בדיוק את מה שיודפס, ולכן אותו עיבוד
LG_AMW = re.compile(r'(^|[^א-ת])(ו?(?:לכו(?:"|&quot;|\'\'|&#x27;&#x27;|״|”)ע|נחלקו))(?![א-ת])')


def lg_am_words(h):
    if 'לכו' not in h and 'נחלקו' not in h:
        return h
    out, dep = [], 0
    for m in re.finditer(r'(<[^>]+>)|([^<]+)', h):
        tag, txt = m.group(1), m.group(2)
        if tag:
            if re.match(r'^<(i|b)[\s>]', tag):
                dep += 1
            elif re.match(r'^</(i|b)>', tag):
                dep = max(0, dep - 1)
            out.append(tag)
        else:
            out.append(txt if dep else LG_AMW.sub(r'\1<i class="am">\2</i>', txt))
    return ''.join(out)


def lg_look(h):
    h = re.sub(r'([,.])(?:\s|&nbsp;|\u00a0)*(?=<i class="(?:am|kt|ot)">)', r'\1<span class="bkx og" contenteditable="false"></span> ', h)
    return lg_am_words(h)



PROBE = r"""
(function(){var LIST=__LIST__;var X=window.__PRNX;if(!X)return {err:'אין __PRNX'};
 var sq=document.getElementById('prnsq');
 if(!sq){sq=document.createElement('div');sq.className='flow';sq.id='prnsq';
   sq.style.cssText='position:fixed;left:0;top:0;visibility:hidden;pointer-events:none;height:auto;overflow:hidden;columns:auto;column-count:1;padding:0;z-index:-1';
   sq.innerHTML='<div class="row"><div class="rail"></div><div class="main"><p></p></div></div>';document.body.appendChild(sq)}
 var GM=sq.querySelector('.main'),GP=sq.querySelector('p');
 var row=document.getElementById('ovtrow');
 if(!row){row=document.createElement('div');row.className='row';row.id='ovtrow';row.innerHTML='<div class="rail"></div><div class="main"><p></p></div>';sq.appendChild(row)}
 var HM=row.querySelector('.main'),HP=row.querySelector('p'),W=HM.getBoundingClientRect().width,out=[];
 LIST.forEach(function(c){var r=[];c.parts.forEach(function(h){
   HM.className=c.mc||'main';HP.className=c.pc||'';HP.style.wordSpacing='';HP.style.letterSpacing='';HP.removeAttribute('data-sq25');HP.innerHTML=h;
   if(HP.textContent.trim().length>=12)X.squeeze25(HP,GM,GP,W);
   X.loneFix(HP,GM,GP);
   var inf=X.lineInfo(HP);
   HP.style.whiteSpace='nowrap';var rg=document.createRange();rg.selectNodeContents(HP);var nw=rg.getBoundingClientRect().width;HP.style.whiteSpace='';
   r.push({n:inf?inf.n:0,nw:+nw.toFixed(1)})});
   out.push({id:c.id,r:r,W:+W.toFixed(1)})});
 return out})()
"""


def verify(site, slug, frm, cands, tmp):
    """cands: [{id, mc, pc, parts:[html]}] -> {id: {'a4-large': [n...], 'a4': [n...]}}"""
    res = {}
    if not cands:
        return res
    for prof in ('a4-large', 'a4'):
        for i in range(0, len(cands), 120):
            chunk = cands[i:i + 120]
            pf = os.path.join(tmp, 'ovprobe.js')
            io.open(pf, 'w', encoding='utf-8').write(PROBE.replace('__LIST__', json.dumps(chunk, ensure_ascii=False)))
            out = run_engine(site, slug, prof, os.path.join(tmp, 'ovv.pdf'), probe=pf, frm=frm)
            m = re.search(r'^PROBE (.*)$', out, flags=re.M)
            if not m:
                raise SystemExit('עצירה: בדיקת ההצעות לא החזירה תוצאה:\n' + out[-1200:])
            got = json.loads(m.group(1))
            if isinstance(got, dict) and got.get('err'):
                raise SystemExit('עצירה: ' + got['err'])
            for g in got:
                res.setdefault(g['id'], {})[prof] = [x['n'] for x in g['r']]
    return res


# ---------- כותרות (פרומפט 48, תיקון 4, 16.11.2026) ----------
# כותרת (נושא, ד"ה משנה) שתופסת יותר משורה בהדפסה: המנוע מצר אותה עד 2.5% ושובר במקום הנכון, ומה שנשאר ביותר משורה
# מקבל כאן הצעת קיצור (כלי 2: ראשי תיבות מקובלים ורווחים; כלי 3: ניסוח קצר של העובד) שמגיעה למנהל לאישור כמו השורות.
# הצעה עוברת רק אם במנוע, בשני הגדלים, הכותרת נכנסת בשורה אחת (אחרי אותה הצרה שהמנוע עושה)
HPROBE = r"""
(function(){var LIST=__LIST__;var X=window.__PRNX;if(!X||!X.headNL)return {err:'אין __PRNX.headNL (מנוע ישן)'};
 var sq=document.getElementById('prnsq');
 if(!sq){sq=document.createElement('div');sq.className='flow';sq.id='prnsq';
   sq.style.cssText='position:fixed;left:0;top:0;visibility:hidden;pointer-events:none;height:auto;overflow:hidden;columns:auto;column-count:1;padding:0;z-index:-1';
   document.body.appendChild(sq)}
 var row=document.getElementById('ovhrow');
 if(!row){row=document.createElement('div');row.id='ovhrow';row.innerHTML='<div class="rail"></div><div class="main"></div>';sq.appendChild(row)}
 var HM=row.querySelector('.main'),out=[];
 LIST.forEach(function(c){row.className='row '+c.k;HM.className=c.mc||('main '+c.k);HM.style.wordSpacing='';HM.style.letterSpacing='';HM.removeAttribute('data-sq25');
   HM.innerHTML=String(c.h).replace(/(\s|&nbsp;)\[([א-ת]{1,3})\](\s*)$/,'$1<span class="cnt">[$2]</span>$3');
   X.headSqueeze(HM);out.push({id:c.id,n:X.headNL(HM)})});
 return out})()
"""


def hverify(site, slug, cands, tmp):
    """cands: [{id, k, mc, h}] -> {id: {'a4-large': n, 'a4': n}}"""
    res = {}
    for prof in ('a4-large', 'a4'):
        for i in range(0, len(cands), 150):
            chunk = cands[i:i + 150]
            pf = os.path.join(tmp, 'ovhprobe.js')
            io.open(pf, 'w', encoding='utf-8').write(HPROBE.replace('__LIST__', json.dumps(chunk, ensure_ascii=False)))
            out = run_engine(site, slug, prof, os.path.join(tmp, 'ovh.pdf'), probe=pf, frm='ב.')
            m = re.search(r'^PROBE (.*)$', out, flags=re.M)
            if not m:
                raise SystemExit('עצירה: בדיקת הצעות הכותרות לא החזירה תוצאה:\n' + out[-1200:])
            got = json.loads(m.group(1))
            if isinstance(got, dict) and got.get('err'):
                raise SystemExit('עצירה: ' + got['err'])
            for g in got:
                res.setdefault(g['id'], {})[prof] = g['n']
    return res


def head_items(rep, site, slug, tmp, abbr, wsug):
    """הכותרות שתופסות יותר משורה (בגודל כלשהו) והצעות הקיצור שנבדקו. מחזיר (items, stats)"""
    HA = {x['u']: x for x in rep['a4'].get('hlines') or []}
    HB = {x['u']: x for x in rep['a4-large'].get('hlines') or []}
    if not HA or not HB:
        raise SystemExit('עצירה: המנוע לא רשם כותרות (hlines). מנוע ישן?')
    miss = [u for u in HB if u not in HA]
    if miss:
        raise SystemExit('עצירה: %d כותרות קיימות רק בפרופיל המוגדל' % len(miss))
    items, cands, meta, st = [], [], {}, {'stale': [], 'unplaced': []}
    for u, x in HB.items():
        ax = HA[u]
        if max(x['n'], ax['n']) < 2:
            continue
        key = 'h%d' % u
        W = x['W'] or 1
        vis = len(NIK.sub('', x['text']).replace(' ', '')) or 1
        avg = x['nw'] / (vis + x['text'].count(' ') * 0.45)
        miss_px = max(1.0, x['nw'] - W) if x['n'] > 1 else max(1.0, ax['nw'] - ax['W'])
        it = {'key': key, 'id': key_id(key), 'u': u, 'li': 0, 'head': x['k'], 'daf': x['daf'], 'cls': '', 'mc': x['mc'],
              'html': x['a'], 'ph': x['a'], 'text': re.sub(r'\s+', ' ', plain(x['a'])).strip(), 'over': '',
              'nA4': ax['n'], 'nLarge': x['n'], 'missPx': round(miss_px, 1), 'miss': int(math.ceil(miss_px / avg)),
              'long': False, 'sug': []}
        items.append(it)
        cands.append({'id': key + '|ctl', 'k': x['k'], 'mc': x['mc'], 'h': x['a']})
        for j, (hp, hd, why, kind) in enumerate(mech_variants(x['a'], x['a'], abbr)[:8]):
            cid = '%s|2|%d' % (key, j)
            cands.append({'id': cid, 'k': x['k'], 'mc': x['mc'], 'h': hd})
            meta[cid] = (it, {'tool': 2, 'kind': 'replace', 'html': hd, 'why': why, 'type': kind})
        ws = wsug.get(key) or {}
        if ws.get('orig') and NIK.sub('', _norm_needle(ws['orig'])).split() != NIK.sub('', it['text'].replace(' ', ' ')).split():
            st['stale'].append(key)
            continue
        for j, s0 in enumerate(ws.get('sug', [])):
            if s0.get('tool') != 3:
                st['unplaced'].append('%s: בכותרת רק ניסוח קצר (כלי 3)' % key)
                continue
            s, err = worker_to_html(x['a'], s0)
            if err:
                st['unplaced'].append('%s: %s' % (key, err))
                continue
            cid = '%s|w|%d' % (key, j)
            cands.append({'id': cid, 'k': x['k'], 'mc': x['mc'], 'h': s['html']})
            meta[cid] = (it, s)
    if not items:
        return [], dict(st, count=0, ctlMismatch=[], rejected=0)
    res = hverify(site, slug, cands, tmp)
    ctl_bad = [it['key'] for it in items if res.get(it['key'] + '|ctl', {}).get('a4-large') != it['nLarge']
               or res.get(it['key'] + '|ctl', {}).get('a4') != it['nA4']]
    if len(ctl_bad) > max(1, len(items) // 10):
        raise SystemExit('עצירה: בדיקת הכותרות אינה משחזרת את ההדפסה ב-%d מתוך %d: %s' % (len(ctl_bad), len(items), ', '.join(ctl_bad[:12])))
    bad = 0
    for cid, (it, s) in meta.items():
        r = res.get(cid) or {}
        if 'a4' not in r or 'a4-large' not in r:
            raise SystemExit('עצירה: אין תוצאת בדיקה להצעת כותרת ' + cid)
        if r['a4-large'] > 1 or r['a4'] > 1:
            bad += 1
            continue
        s['ok'] = {'large': [r['a4-large']], 'a4': [r['a4']]}
        it['sug'].append(s)
    for it in items:
        if it['key'] in ctl_bad:
            it['ctlMismatch'] = res.get(it['key'] + '|ctl')
        seen, keep = set(), []
        for s in sorted(it['sug'], key=lambda s: (s['tool'], len(plain(s.get('html', ''))))):
            if s['tool'] in seen:
                continue
            seen.add(s['tool'])
            keep.append(s)
        it['sug'] = keep[:3]
        it['tool6'] = not it['sug']
    return items, dict(st, count=len(items), ctlMismatch=ctl_bad, rejected=bad)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--slug', default='berakhot')
    ap.add_argument('--site', required=True)
    ap.add_argument('--tmp', default=os.path.join(ROOT, '_work', 'overflow'))
    ap.add_argument('--reuse', action='store_true')
    ap.add_argument('--out', default='')
    a = ap.parse_args()
    os.makedirs(a.tmp, exist_ok=True)
    t0 = time.time()
    rep = {}
    for prof in ('a4', 'a4-large'):
        rp = os.path.join(a.tmp, '%s-%s.pdf.json' % (a.slug, prof))
        if not (a.reuse and os.path.exists(rp)):
            run_engine(a.site, a.slug, prof, os.path.join(a.tmp, '%s-%s.pdf' % (a.slug, prof)))
        rep[prof] = json.load(io.open(rp, encoding='utf-8'))
    A = {(x['u'], x['li']): x for x in rep['a4']['plines']}
    B = rep['a4-large']['plines']
    if not B or not A:
        raise SystemExit('עצירה: המנוע לא רשם שורות (lines=1)')
    # שער: כל פסקה של a4-large קיימת גם ב-a4 (אותו נוסח). אחרת - עצירה רועשת, לא דילוג שקט
    miss = [x for x in B if (x['u'], x['li']) not in A]
    if miss:
        raise SystemExit('עצירה: %d פסקאות קיימות רק בפרופיל המוגדל (הנוסח השתנה בין ההרצות?)' % len(miss))
    data = {}
    try:
        txt = io.open(os.path.join(a.site, a.slug + '.data.js'), encoding='utf-8').read()
        D = json.loads(txt[txt.index('{'):txt.rindex('}') + 1])
        for pg in D.get('pages', []):
            for u in pg.get('units', []):
                for li, l in enumerate(u.get('l') or [], 1):
                    data[(u['id'], li)] = l
    except Exception as e:
        raise SystemExit('עצירה: נתוני המסכת לא נקראו (%s)' % e)
    items = []
    for x in B:
        ax = A[(x['u'], x['li'])]
        # 17.11.2026 (מיכאל: "צא לדרך"): גם פסקה שלא גלשה בהגדלה, אבל השורה האחרונה שלה היא מילה בודדת או זנב קצר
        # (עד 15% מן השורה) בגודל הרגיל החדש (המוגדל) - מועמדת לאיחוי: היעד שורה אחת פחות. רק שינוי מכני (כלי 2)
        # או ניסוח מזערי (כלי 3) מוחלים בה לבד; חיתוך ואיחוי עם שורה סמוכה אינם מקצרים אותה ואינם מוצעים
        tail = False
        if x['n'] <= ax['n']:
            tw = re.sub(r'\u2060\d+', '', x['text'][x['start']:]).strip()
            if x['n'] < 2 or (x.get('mc') or 'main') != 'main' or not (len(tw.split()) == 1 or x['lastW'] <= 0.15 * x['W']):
                continue
            tail = True
        # הנוסח כפי שהוא בדף בזמן ההדפסה (כולל עריכות המנהל החיות), ולא הנוסח הבנוי
        l = [x['dc'], x['dh']] if x.get('dh') is not None else data.get((x['u'], x['li']))
        if not l:
            raise SystemExit('עצירה: פסקה u%s.%s אינה בנתונים' % (x['u'], x['li']))
        W = x['W']
        vis = len(NIK.sub('', x['text']).replace(' ', '')) or 1
        avg = x['nw'] / (vis + x['text'].count(' ') * 0.45)
        over = re.sub(r'\u2060\d+', '', x['text'][x['start']:]).strip()   # בלי מספרי ההפניות לתוספות
        # כמה חסר: הרוחב הטבעי פחות מה שנכנס ב-(n-1) שורות. בפסקה ארוכה זו הערכה מלמטה
        miss_px = max(1.0, x['nw'] - (x['n'] - 1) * W)
        items.append({'key': 'u%d.%d' % (x['u'], x['li']), 'id': key_id('u%d.%d' % (x['u'], x['li'])), 'u': x['u'], 'li': x['li'],
                      'daf': x['daf'], 'cls': l[0], 'mc': x.get('mc') or 'main', 'html': l[1], 'ph': l[1], 'text': re.sub(r'\s+', ' ', plain(l[1])).strip(), 'over': over,
                      'nA4': ax['n'], 'nLarge': x['n'], 'missPx': round(miss_px, 1), 'miss': int(math.ceil(miss_px / avg)),
                      'long': ax['n'] >= 2, 'tail': tail, 'sug': []})
    # ---- הצעות ----
    abbr = json.load(io.open(os.path.join(ODIR, 'abbr.json'), encoding='utf-8'))['items']
    sp = os.path.join(ODIR, 'sugg', a.slug + '.json')
    wsug = json.load(io.open(sp, encoding='utf-8')) if os.path.exists(sp) else {}
    cands, meta = [], {}
    # ביקורת: הנוסח הנוכחי של כל שורה נמדד באותה בדיקה. אם הבדיקה אינה משחזרת את מספר השורות של ההדפסה
    # המלאה - היא אינה אמינה, והמחולל עוצר (לא מציג הצעות שנבדקו בכלי שגוי)
    for it in items:
        cands.append({'id': it['key'] + '|ctl', 'mc': it['mc'], 'pc': it['cls'], 'parts': [lg_look(it['ph'])]})
    neighbor = {}
    for it in items:
        for j, (hp, hd, why, kind) in enumerate(mech_variants(it['ph'], it['html'], abbr)[:8]):
            cid = '%s|2|%d' % (it['key'], j)
            cands.append({'id': cid, 'mc': it['mc'], 'pc': it['cls'], 'parts': [lg_look(hp)]})
            meta[cid] = (it, {'tool': 2, 'kind': 'replace', 'html': hd, 'why': why, 'type': kind})
        ws = wsug.get(it['key']) or {}
        # ההצעה נכתבה על נוסח מסוים: אם הנוסח השתנה מאז - אינה מוצגת, ונספרת (לא נעלמת בשקט)
        if ws.get('orig') and NIK.sub('', _norm_needle(ws['orig'])).split() != NIK.sub('', it['text'].replace('\u00a0', ' ')).split():
            neighbor.setdefault('stale', []).append(it['key'])
            continue
        for j, s0 in enumerate(ws.get('sug', [])):
            cid = '%s|w|%d' % (it['key'], j)
            s, err = worker_to_html(it['html'], s0)
            if err:
                neighbor.setdefault('unplaced', []).append('%s: %s' % (it['key'], err))
                continue
            parts = s['parts'] if s['kind'] == 'split' else [s['html']]
            cands.append({'id': cid, 'mc': it['mc'], 'pc': it['cls'], 'parts': [lg_look(x) for x in parts]})
            meta[cid] = (it, s)
    # ---- כלי 4 מכני (פרומפט 53, 17.11.2026): חיתוך במקום טבעי, בלי שינוי מילה ----
    # מיכאל: "אם זה נכנס - שיישאר כך", בלי אישור ידני. עד היום חיתוך הוצע רק כשהעובד כתב אותו. כאן הוא נגזר
    # בקוד: אחרי סימן פיסוק (, . : ; ? !) הקרוב לאמצע השורה. אותם כללים כמו חיתוך של העובד (worker_to_html):
    # כל חלק שלוש מילים לפחות, לא אחרי מילית, לא בתוך הסבר/פסוק/אמוראים. ונבדק במנוע: כל חלק בשורה אחת בשני הגדלים
    msplit = 0
    for it in items:
        if it['nA4'] != 1 or it['mc'] != 'main' or it.get('tail'):
            continue
        if any((s0.get('tool') == 4) for s0 in (wsug.get(it['key']) or {}).get('sug', [])):
            continue
        runs, flat, mp, dep_at = _flatmap(it['html'])
        L = len(flat.strip())
        # בלי נקודתיים: שורה שנגמרת בנקודתיים היא שורת דובר/פתיחה, ואינה מקום חיתוך מכני.
        # ולא בתוך ציטוט או סוגריים (protected_spans של כלי 2)
        spans = protected_spans(flat)
        pts = [m.end() for m in re.finditer(r'[,.;?!](?=\s+\S)', flat) if not any(a0 < m.end() < b0 for a0, b0 in spans)]
        pts = [x + len(re.match(r'\s*', flat[x:]).group(0)) for x in pts]
        pts = sorted(set(x for x in pts if 0 < x < len(flat)), key=lambda x: abs(x - L / 2))
        k = 0
        for x in pts:
            if k >= 3:
                break
            if x < L * 0.25 or x > L * 0.8:
                continue
            key = None
            for ln in range(6, len(flat) - x + 1):
                if flat.count(flat[x:x + ln]) == 1:
                    key = flat[x:x + ln]
                    break
            if not key:
                continue
            sg, err = worker_to_html(it['html'], {'tool': 4, 'split_before': key, 'side': ''})
            if err:
                continue
            cid = '%s|4m|%d' % (it['key'], k)
            cands.append({'id': cid, 'mc': it['mc'], 'pc': it['cls'], 'parts': [lg_look(z) for z in sg['parts']]})
            meta[cid] = (it, dict(sg, why='חיתוך אחרי סימן פיסוק', src='mech'))
            k += 1
            msplit += 1
    # ---- כלי 5: איחוי עם השורה הסמוכה (פרומפט 44) ----
    # בעל הפרויקט, 16.11.2026: איחוי אוטומטי של שורות מסתדר פעמים רבות, גם בשורות ארוכות.
    # עד היום הכלי לא הוצע כלל (העובד לא כתב הצעות כאלה, והמחולל לא הכיר אותן). כאן הוא מכני:
    # השורה מתאחדת עם הקודמת או הבאה באותה יחידה ובאותו סגנון (אותה יחידת מחשבה), בלי לשנות
    # אות. ההצעה עוברת רק אם במנוע, בשני הגדלים, הפסקה המאוחדת אינה תופסת יותר שורות משתי
    # הפסקאות יחד בהדפסה הרגילה - כלומר אינה גולשת ואינה דוחקת שורה אחרת.
    joins = 0
    for it in items:
        if it['mc'] != 'main' or it.get('tail'):
            continue
        for tgt, dl in (('prev', -1), ('next', 1)):
            nk = (it['u'], it['li'] + dl)
            nl = data.get(nk)
            na = A.get(nk)
            if not nl or not na or nl[0] != it['cls'] or (na.get('mc') or 'main') != 'main':
                continue
            nt = re.sub(r'\s+', ' ', plain(nl[1])).strip()
            if len(nt.split()) < 2 or nt.endswith(':'):
                continue                # כותרת או שורת דובר: אינה אותה יחידת מחשבה
            merged = (nl[1].rstrip() + ' ' + it['html'].strip()) if tgt == 'prev' else (it['html'].rstrip() + ' ' + nl[1].strip())
            cid = '%s|5|%s' % (it['key'], tgt)
            cands.append({'id': cid, 'mc': it['mc'], 'pc': it['cls'], 'parts': [lg_look(merged)]})
            meta[cid] = (it, {'tool': 5, 'kind': 'join', 'target': tgt, 'html': merged, 'targetOrig': nl[1],
                              'targetLines': na['n'], 'why': 'איחוי עם השורה ה%s' % ('קודמת' if tgt == 'prev' else 'באה')})
            joins += 1
    frm = items[0]['daf'] if items else None
    res = verify(a.site, a.slug, 'ב.', cands, a.tmp) if cands else {}
    bad = 0
    ctl_bad = [it['key'] for it in items if res.get(it['key'] + '|ctl', {}).get('a4-large', [0])[0] != it['nLarge']
               or res.get(it['key'] + '|ctl', {}).get('a4', [0])[0] != it['nA4']]
    if len(ctl_bad) > max(3, len(items) // 20):
        raise SystemExit('עצירה: בדיקת ההצעות אינה משחזרת את ההדפסה ב-%d מתוך %d שורות: %s' % (len(ctl_bad), len(items), ', '.join(ctl_bad[:12])))
    for it in items:
        if it['key'] in ctl_bad:
            it['ctlMismatch'] = res.get(it['key'] + '|ctl')
    for cid, (it, s) in meta.items():
        r = res.get(cid)
        if not r or 'a4' not in r or 'a4-large' not in r:
            raise SystemExit('עצירה: אין תוצאת בדיקה להצעה ' + cid)
        if s.get('kind') == 'split':
            need = [1] * len(r['a4-large'])
        elif s.get('kind') == 'move':
            need = [it['nA4'], s.get('targetLines', 1)]
        elif s.get('kind') == 'join':
            need = [it['nA4'] + s.get('targetLines', 1)]
        else:
            need = [it['nA4']]
        if it.get('tail'):
            # זנב קצר: ההצעה עוברת רק אם חסכה שורה בגודל הרגיל (המוגדל), ואינה מוסיפה שורה בקטן
            if s.get('kind') in ('split', 'move', 'join'):
                bad += 1
                continue
            ok = r['a4-large'][0] <= it['nLarge'] - 1 and r['a4'][0] <= it['nA4']
        else:
            ok = all(n <= m for n, m in zip(r['a4-large'], need)) and all(n <= m for n, m in zip(r['a4'], need))
        if not ok:
            bad += 1
            continue
        s['ok'] = {'large': r['a4-large'], 'a4': r['a4']}
        it['sug'].append(s)
    # לכל שורה: לכל היותר הצעה אחת מכל כלי, בסדר הכלים; עד שלוש
    for it in items:
        seen, keep = set(), []
        # איחוי (כלי 5) ראשון: אינו משנה אות, ובעל הפרויקט מצא שהוא מסתדר יפה (16.11.2026)
        for s in sorted(it['sug'], key=lambda s: (0 if s['tool'] == 5 else s['tool'], len(plain(s.get('html', '')) or ''))):
            if s['tool'] in seen:
                continue
            seen.add(s['tool'])
            keep.append(s)
        it['sug'] = keep[:3]
        it['tool6'] = not it['sug']
        if it['long'] and not it['sug']:
            it['leave'] = True
    by_tool = {}
    for it in items:
        if it['sug']:
            by_tool[it['sug'][0]['tool']] = by_tool.get(it['sug'][0]['tool'], 0) + 1
    hitems, hst = head_items(rep, a.site, a.slug, a.tmp, abbr, wsug)
    hmulti = {p: rep[p].get('headMulti') or {} for p in ('a4', 'a4-large')}
    doc = {'slug': a.slug, 'made': time.strftime('%Y-%m-%d %H:%M'), 'profile': 'a4-large',
           'pages': {'a4': len(rep['a4']['pages']), 'a4-large': len(rep['a4-large']['pages'])},
           'sq25': {'a4': rep['a4'].get('sq25', 0), 'a4-large': rep['a4-large'].get('sq25', 0)},
           'count': len(items), 'firstTool': by_tool, 'joinCands': joins, 'mechSplitCands': msplit, 'ctlMismatch': ctl_bad, 'rejected': bad, 'stale': neighbor.get('stale', []), 'unplaced': neighbor.get('unplaced', []),
           'heads': {'count': hst['count'], 'withSug': sum(1 for x in hitems if x['sug']), 'rejected': hst['rejected'], 'ctlMismatch': hst['ctlMismatch'],
                     'stale': hst['stale'], 'unplaced': hst['unplaced'], 'engine': {p: {k: v for k, v in hmulti[p].items() if k != 'list'} for p in hmulti}},
           'items': items + hitems}
    out = a.out or os.path.join(ODIR, a.slug + '.json')
    io.open(out, 'w', encoding='utf-8').write(json.dumps(doc, ensure_ascii=False, indent=1))
    print('שורות גולשות: %d | הצעות: %s | נפסלו בבדיקה: %d | כותרות ביותר משורה: %d (עם הצעה: %d) | %.0f שניות' % (len(items), by_tool, bad, len(hitems), sum(1 for x in hitems if x['sug']), time.time() - t0))


if __name__ == '__main__':
    main()
