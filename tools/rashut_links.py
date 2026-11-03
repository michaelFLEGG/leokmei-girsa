# -*- coding: utf-8 -*-
"""rashut_links.py - רשת המקומות (פרומפט 1, 3.11.2026): זיהוי הפסוקים שבגמרא ומפתח הדפים לאתרים האחים.

רץ בסוף כל בנייה (build_all.main), אחרי שכל דפי המסכתות נכתבו. אינו נוגע בטקסט ובקובצי הוורד:
הוא כותב קובצי נתונים קטנים בלבד, ושכבת הקישורים (site/rashut.js) קוראת אותם בדפדפן.

  site/rashut/index.json   - לכל מסכת: שמה והדפים שקיימים בה בפועל (למי שמקשר אלינו: נ"ך המפורש, ממלכת הזוהר).
  site/rashut/<slug>.json  - לכל פסוק מזוהה בגמרא (i.ps): היחידה, השורה, מספרו בשורה, מראה המקום ושלד הקטע.

הזיהוי אינו ניחוש. לכל יחידה יש מראה מקום בספריא (ref, נקבע ב-match_sources), ושני מסלולים בלבד:
  א. ספריא: הקטע מותאם רק לפסוקים שספריא מקשרת לאותו קטע או לאותו עמוד (data/rashut/sefaria-bavli-tanakh.json,
     מן ההורדה הציבורית של ספריא). נדרשות שתי מילים לפחות ברצף, וכל מילות הקטע (עד שתיים חסרות בקטע ארוך).
  ב. נוסח ייחודי: קטע של ארבע מילים לפחות שכולו נמצא ברצף בפסוק אחד בלבד בכל המקרא.
קטע שמתאים ליותר מפסוק אחד, קטע של מילה אחת, וקטע שאינו פסוק - אינם מקושרים, ונספרים בדוח.
השלד והשוואת המילים הם של tools/verses_check.py, כדי שלא יהיו שתי הגדרות של "אותו פסוק"."""
import html as H, io, json, os, re, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import verses_check as VC

SEF = os.path.join(ROOT, 'data', 'rashut', 'sefaria-bavli-tanakh.json')
PS = re.compile(r'<i class="ps">(.*?)</i>', re.S)
TAG = re.compile(r'<[^>]+>')
STOPW = {'וגו', 'וגומר', 'וכו', 'וגו\'', 'וכתיב', 'כתיב', 'וכו\''}
# הספרים כפי שהם בנ"ך המפורש (תהלים בלי יו"ד)
HE = {'Genesis': 'בראשית', 'Exodus': 'שמות', 'Leviticus': 'ויקרא', 'Numbers': 'במדבר', 'Deuteronomy': 'דברים',
      'Joshua': 'יהושע', 'Judges': 'שופטים', 'I Samuel': 'שמואל א', 'II Samuel': 'שמואל ב', 'I Kings': 'מלכים א',
      'II Kings': 'מלכים ב', 'Isaiah': 'ישעיהו', 'Jeremiah': 'ירמיהו', 'Ezekiel': 'יחזקאל', 'Hosea': 'הושע',
      'Joel': 'יואל', 'Amos': 'עמוס', 'Obadiah': 'עובדיה', 'Jonah': 'יונה', 'Micah': 'מיכה', 'Nahum': 'נחום',
      'Habakkuk': 'חבקוק', 'Zephaniah': 'צפניה', 'Haggai': 'חגי', 'Zechariah': 'זכריה', 'Malachi': 'מלאכי',
      'Psalms': 'תהלים', 'Proverbs': 'משלי', 'Job': 'איוב', 'Song of Songs': 'שיר השירים', 'Ruth': 'רות',
      'Lamentations': 'איכה', 'Ecclesiastes': 'קהלת', 'Esther': 'אסתר', 'Daniel': 'דניאל', 'Ezra': 'עזרא',
      'Nehemiah': 'נחמיה', 'I Chronicles': 'דברי הימים א', 'II Chronicles': 'דברי הימים ב'}


def _read(p):
    return io.open(p, encoding='utf-8').read()


def load_data(site, slug):
    p = os.path.join(site, slug + '.data.js')
    if not os.path.exists(p):
        return None
    s = _read(p)
    return json.loads(s[s.index('{'):s.rindex('}') + 1])


def frag_words(raw):
    """מילות הקטע כשלדים, בלי ד'/ו' שלפני הגרש, בלי וגו' ובלי קיצורים."""
    t = H.unescape(TAG.sub(' ', raw))
    t = re.sub(r"(^|\s)[דוש](?=['׳])", r'\1', t)          # ד'ותתצב -> 'ותתצב
    out = []
    for a, b, sk, brk in VC._tokens(t):
        w = t[a:b]
        if VC.NIK.sub('', w) in STOPW or sk in ('וג', 'וגמר'):
            continue
        out.append(sk)
    return [w for w in out if w != '#']


class Tanakh:
    def __init__(self):
        verses, bi = VC.load()
        self.verses, self.bi = verses, bi
        self.by_ref = {('%s %d:%d' % (b, c, v)): i for i, (b, c, v, ws) in enumerate(verses)}

    def run(self, frag, ws):
        """הרצף הארוך ביותר של מילות הקטע (מכל נקודת התחלה) שתואם ברצף את מילות הפסוק."""
        best = 0
        for i in range(len(frag)):
            for p in range(len(ws)):
                k = 0
                while i + k < len(frag) and p + k < len(ws) and VC._eq(frag[i + k], ws[p + k]):
                    k += 1
                if k > best:
                    best = k
        return best

    def unique_full(self, frag):
        """כל הקטע ברצף בפסוק אחד בלבד בכל המקרא. מחזיר מראה מקום או None."""
        if len(frag) < 4:
            return None
        hits = set()
        for vi, p in self.bi.get((frag[0], frag[1]), []):
            ws = self.verses[vi][3]
            if p + len(frag) <= len(ws) and all(VC._eq(frag[j], ws[p + j]) for j in range(len(frag))):
                hits.add(vi)
            if len(hits) > 1:
                return None
        if len(hits) != 1:
            return None
        b, c, v, _ = self.verses[hits.pop()]
        return '%s %d:%d' % (b, c, v)


def need(n):
    """כמה מילים מן הקטע חייבות להתאים ברצף: כולן בקטע קצר, ועד שתיים חסרות בקטע ארוך."""
    return n if n <= 4 else max(4, n - 2)


def match(T, frag, cands):
    """התאמה בתוך רשימת פסוקים נתונה. מחזיר מראה מקום אחד, או None כשאין או כשיש יותר מאחד."""
    if len(frag) < 2:
        return None
    sc = {}
    for ref in cands:
        vi = T.by_ref.get(ref)
        if vi is None:
            continue
        sc[ref] = T.run(frag, T.verses[vi][3])
    ok = [r for r, s in sc.items() if s >= need(len(frag))]
    if not ok:
        return None
    top = max(sc[r] for r in ok)
    best = [r for r in ok if sc[r] == top]
    if len(best) != 1:
        # אותו נוסח בשני פסוקים (למשל חזרה בתורה) - לא מקשרים
        return None
    return best[0]


def run(site, built=None, slug_of=None):
    if not os.path.exists(SEF):
        raise SystemExit('עצירה: חסר data/rashut/sefaria-bavli-tanakh.json (רשת המקומות)')
    sef = json.loads(_read(SEF))
    T = Tanakh()
    os.makedirs(os.path.join(site, 'rashut'), exist_ok=True)
    index, stats = {}, collections.Counter()
    pv = collections.defaultdict(list)    # פסוק נביאים/כתובים -> [מסכת, דף, הקטע]: לנ"ך המפורש ("בגמרא")
    TORAH = ('Genesis ', 'Exodus ', 'Leviticus ', 'Numbers ', 'Deuteronomy ')
    slugs = sorted(f[:-8] for f in os.listdir(site) if f.endswith('.data.js'))
    for slug in slugs:
        D = load_data(site, slug)
        if not D:
            continue
        st = set(f[:-5] for f in os.listdir(os.path.join(site, slug))) if os.path.isdir(os.path.join(site, slug)) else set()
        dafs = [p['daf'] for p in D['pages'] if p.get('daf')]
        index[slug] = {'he': D.get('masechet') or slug, 'dafs': dafs, 'st': sorted(st)}
        S = sef.get(slug, {})
        by_amud = collections.defaultdict(set)
        for k, vs in S.items():
            by_amud[k.split(':')[0]].update(vs)
        out = {}
        for pg in D['pages']:
            for u in pg.get('units') or []:
                ref = u.get('ref') or ''
                m = re.match(r'^[^.]+\.(\d+[ab])\.(\d+)', ref)
                seg = set(S.get('%s:%s' % m.groups(), [])) if m else set()
                amud = by_amud.get(m.group(1), set()) if m else set()
                for li, line in enumerate(u.get('l') or []):
                    html = line[1] if isinstance(line, list) and len(line) > 1 else ''
                    for pi, raw in enumerate(PS.findall(html)):
                        stats['ps'] += 1
                        fw = frag_words(raw)
                        if len(fw) < 2:
                            stats['short'] += 1
                            continue
                        got, how = match(T, fw, seg), 's'
                        if not got:
                            got = match(T, fw, amud)
                        if not got:
                            got, how = T.unique_full(fw), 'u'
                        if not got:
                            stats['nomatch'] += 1
                            continue
                        stats['sefaria' if how == 's' else 'unique'] += 1
                        out.setdefault(str(u['id']), []).append([li + 1, pi, got, ''.join(fw)[:40]])
                        if not got.startswith(TORAH):
                            q = re.sub(r'\s+', ' ', H.unescape(TAG.sub(' ', raw))).strip(" '׳")[:80]
                            row = [slug, pg['daf'], q]
                            if not any(r[0] == slug and r[1] == pg['daf'] for r in pv[got]):
                                pv[got].append(row)
        with io.open(os.path.join(site, 'rashut', slug + '.json'), 'w', encoding='utf-8', newline='\n') as f:
            json.dump({'v': 1, 'u': out}, f, ensure_ascii=False, separators=(',', ':'))
    with io.open(os.path.join(site, 'rashut', 'index.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump({'v': 1, 'he': HE, 'm': index}, f, ensure_ascii=False, separators=(',', ':'))
    with io.open(os.path.join(site, 'rashut', 'pv.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(pv, f, ensure_ascii=False, separators=(',', ':'), sort_keys=True)
    with io.open(os.path.join(site, 'rashut', 'stats.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(dict(stats), f, ensure_ascii=False)
    shutil_copy(os.path.join(HERE, 'rashut.js'), os.path.join(site, 'rashut.js'))
    tagged = inject(site, index)
    print('רשת המקומות: %d מסכתות; פסוקים בגמרא %d - קושרו %d (ספריא %d, נוסח ייחודי %d), '
          'קצרים %d, לא זוהו %d; תג נשתל ב-%d דפים'
          % (len(index), stats['ps'], stats['sefaria'] + stats['unique'], stats['sefaria'], stats['unique'],
             stats['short'], stats['nomatch'], tagged))
    if not index:
        raise SystemExit('עצירה: רשת המקומות לא מצאה אף מסכת בנויה')


def shutil_copy(a, b):
    import shutil
    shutil.copy(a, b)


TAG_RE = re.compile(r'<script src="/rashut\.js(?:\?v=[0-9a-f]+)?" defer></script>')


def inject(site, index):
    """שורת script אחת בדפי המסכתות ובשער. אידמפוטנטי; החותמת לפי תוכן הקובץ."""
    import hashlib
    h = hashlib.md5(io.open(os.path.join(site, 'rashut.js'), 'rb').read()).hexdigest()[:8]
    tag = '<script src="/rashut.js?v=%s" defer></script>' % h
    n = 0
    for name in [s + '.html' for s in index] + ['index.html']:
        p = os.path.join(site, name)
        if not os.path.exists(p):
            continue
        s = _read(p)
        if TAG_RE.search(s):
            s2 = TAG_RE.sub(tag, s, count=1)
        else:
            i = s.rfind('</body>')
            s2 = s[:i] + tag + s[i:] if i >= 0 else s + tag
        if s2 != s:
            with io.open(p, 'w', encoding='utf-8', newline='') as f:
                f.write(s2)
        n += 1
    return n


if __name__ == '__main__':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    run(os.path.join(ROOT, 'site'))
