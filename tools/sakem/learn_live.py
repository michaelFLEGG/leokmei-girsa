#!/usr/bin/env python3
"""המקליט מן השכבה החיה (פרומפט 62, 18.11.2026).

מאז פרומפט 51 העריכות אינן נכנסות עוד ל-data/edits, ולכן המקליט הישן (learn.mjs record) אינו רואה
את עריכות המנהל. הכלי הזה קורא את השכבה החיה (/live?slug=...) של מסכת, מפריד בין קבלת הצעות סכם
(ההחלה עצמה, שנרשמת בשכבה כפרץ של עריכות באותה שנייה) לבין עריכה ידנית של המנהל אחרי סכם,
ומוסיף את הידניות ל-data/sakem/learn/<מסכת>.jsonl במבנה שהמקליט הישן כתב (post:1), כך
ש-`runner.mjs lessons` מציג אותן כרגיל.

  python3 tools/sakem/learn_live.py <מסכת> [--since=YYYY-MM-DDTHH:MM] [--dry] [--report=<קובץ>]

מיון:
  סכם (src:'סכם', אינה נלמדת): עריכת נוסח שהנוסח החדש שלה הוא נוסח הצעת סכם (data/sakem/out/<מסכת>-*.json),
      או עריכת צורה/מבנה שנעשתה עד 3 שניות אחרי קבלה כזאת באותו דף (מנגנון ההחלה).
  ידנית: כל השאר. "תיקון של סכם" - כשהנוסח הקודם הוא נוסח סכם והחדש שונה ממנו.
רשומה שכבר נקלטה (אותו k ואותו t) אינה נכפלת. הכלי אינו כותב לשרת ואינו משנה את הטקסט החי.
"""
import json, re, sys, os, glob, urllib.request, datetime, collections

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
API = os.environ.get('SAKEM_API', 'https://leokmei-suggest.m7654301.workers.dev')


def norm(s):
    s = re.sub(r'<[^>]+>', '', s or '').replace('&nbsp;', ' ').replace('&quot;', '"').replace('&#x27;', "'")
    s = re.sub(r"\[[^\]:]{1,12}:[0-9.a-z ,]*\]", '', s)
    s = re.sub(r'\[(?:מקור|דף)[^\]]*\]', '', s)
    s = re.sub(r'(?m)^\s*[א-י]\.\s', '', s)
    s = re.sub(r'\[(?:צד|כותרת-דה|כותרת-נושא|כותרת|משנה|קבוע)[^:\]]*:?', '', s)
    s = re.sub(r'\{[^:{}]+:', '', s)
    s = re.sub(r'[֑-ׇ]', '', s)
    return re.sub(r'[^א-ת0-9]', '', s)


def main():
    a = sys.argv[1:]
    if not a or a[0].startswith('-'):
        print(__doc__); sys.exit(2)
    slug = a[0]
    opt = dict((x[2:].split('=', 1) + [''])[:2] for x in a[1:] if x.startswith('--'))
    since = 0
    if opt.get('since'):
        since = int(datetime.datetime.fromisoformat(opt['since']).replace(tzinfo=datetime.timezone(datetime.timedelta(hours=2))).timestamp() * 1000)
    sak = []
    for f in sorted(glob.glob(os.path.join(ROOT, 'data', 'sakem', 'out', slug + '-*.json'))):
        if f.endswith('.old.json'):
            continue
        d = json.load(open(f, encoding='utf8'))
        sak.append(''.join(norm(it.get('text', '')) for it in d.get('items', [])))
    ALL = '|'.join(sak)
    if not ALL:
        print('אין הצעות סכם למסכת ' + slug + ' - הכל ייחשב ידני')
    req = urllib.request.Request(API + '/live?slug=' + slug, headers={'User-Agent': 'leokmei-sakem-learn/1'})
    with urllib.request.urlopen(req, timeout=60) as r:
        doc = json.load(r)['doc']
    E = sorted([e for e in doc.get('edits', []) if e.get('t', 0) >= since], key=lambda e: e['t'])
    # שלב א: עריכות נוסח
    acc_t = collections.defaultdict(list)  # daf -> זמני קבלה
    for e in E:
        if e.get('op') == 'struct':
            continue
        nw, wa = norm(e.get('nowH') or e.get('now')), norm(e.get('wasH') or e.get('was'))
        if nw == wa:
            e['_c'] = 'form'
        elif nw and nw in ALL:
            e['_c'] = 'sakem'; acc_t[e.get('daf', '')].append(e['t'])
        elif wa and wa in ALL:
            e['_c'] = 'fix'
        else:
            e['_c'] = 'manual'
    # שלב ב: צורה ומבנה צמודים לקבלה. קבלה נרשמת כפרץ: ארבע עריכות ומעלה באותן שתי שניות - קצב שאינו של אדם.
    burst = collections.Counter(e['t'] // 2000 for e in E)
    for e in E:
        if e.get('op') == 'struct' or e.get('_c') == 'form':
            near = burst[e['t'] // 2000] >= 4 or any(0 <= e['t'] - t <= 3000 for t in acc_t.get(e.get('daf', ''), []))
            e['_c'] = 'sakem-mech' if near else ('struct' if e.get('op') == 'struct' else 'form')
    cnt = collections.Counter(e['_c'] for e in E)
    man = [e for e in E if e['_c'] in ('manual', 'fix', 'form', 'struct')]
    f = lambda t: datetime.datetime.utcfromtimestamp(t / 1000 + 7200).strftime('%d.%m %H:%M:%S')
    print('%s: %d עריכות בשכבה מאז %s · %s' % (slug, len(E), f(since) if since else 'ההתחלה', dict(cnt)))
    if man:
        print('ידניות: %d, הראשונה %s, האחרונה %s' % (len(man), f(man[0]['t']), f(man[-1]['t'])))
    out = os.path.join(ROOT, 'data', 'sakem', 'learn', slug + '.jsonl')
    seen = set()
    if os.path.exists(out):
        for l in open(out, encoding='utf8'):
            try:
                r = json.loads(l); seen.add((r.get('k'), r.get('t')))
            except Exception:
                pass
    CLS = {'manual': ('תוכן', ''), 'fix': ('תוכן', 'תיקון של סכם'), 'form': ('צורה', 'סימון'), 'struct': ('צורה', 'מבנה')}
    recs = []
    for e in man:
        if (e['k'], e['t']) in seen:
            continue
        r = {'k': e['k'], 't': e['t'], 'daf': e.get('daf', ''), 'cls': CLS[e['_c']][0], 'sub': CLS[e['_c']][1], 'w': 2, 'post': 1, 'from': 'live'}
        for x in ('op', 'kind', 'texts', 'resT', 'was', 'now', 'wasH', 'nowH'):
            if x in e:
                r[x] = e[x]
        recs.append(r)
    if opt.get('report'):
        json.dump(man, open(opt['report'], 'w', encoding='utf8'), ensure_ascii=False, indent=1)
    if 'dry' in opt:
        print('(בדיקה בלבד) היו נוספות %d רשומות ל-%s' % (len(recs), os.path.relpath(out, ROOT)))
        return
    with open(out, 'a', encoding='utf8') as w:
        for r in recs:
            w.write(json.dumps(r, ensure_ascii=False) + '\n')
    print('נוספו %d רשומות ל-%s' % (len(recs), os.path.relpath(out, ROOT)))


if __name__ == '__main__':
    main()
