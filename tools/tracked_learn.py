# -*- coding: utf-8 -*-
"""tracked_learn.py - חילוץ למידה מ"עקוב אחר שינויים" שבקובצי הוורד (12.10.2026).

מה זה עושה (קריאה בלבד: אינו כותב לקובצי הוורד ואינו מקבל שינויים):
  א. סופר לכל קובץ ולכל מחבר: הכנסות, מחיקות, שינויי עיצוב (תו ופסקה);
  ב. ממיין כל מחבר לאחת משלוש שכבות: מכני, סמנטי, אדם;
  ג. מחלץ זוגות "נמחק ← נכנס" (החלפות) ומדרג את הנפוצים לכל שכבה;
  ד. שינויי אדם נשמרים כולם, עם הקשר, לעיון (זה החומר היקר ללמידה);
  ה. מודד זמן פענוח לכל קובץ.

הרצה:  uv run --with lxml python tools/tracked_learn.py [--src DIR] [--out data/learn/tracked.json]
"""
import os, sys, re, json, time, zipfile, argparse, collections

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass
from lxml import etree

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
MECH = {'מנוע מכני', 'מנוע אמוראים', 'מנוע עיצוב', 'מנוע פסוקים', 'מספור קטעי משנה'}
SEM = {'Claude', 'קלוד', 'Claude - סמנטי'}


def layer(author):
    if author in MECH:
        return 'מכני'
    if author in SEM:
        return 'סמנטי'
    return 'אדם'


def seg_text(el):
    out = []
    for t in el.iter(W + 't', W + 'delText'):
        out.append(t.text or '')
    return ''.join(out)


def analyze(path):
    t0 = time.time()
    root = etree.fromstring(zipfile.ZipFile(path).read('word/document.xml'))
    st = collections.defaultdict(lambda: collections.Counter())
    pairs = collections.defaultdict(collections.Counter)      # שכבה -> (נמחק, נכנס)
    dels = collections.defaultdict(collections.Counter)
    inss = collections.defaultdict(collections.Counter)
    human = []
    pi = 0
    for p in root.iter(W + 'p'):
        pi += 1
        segs = []
        for ch in p:
            tag = ch.tag
            if tag == W + 'ins':
                a = ch.get(W + 'author') or '?'
                st[a]['ins'] += 1
                segs.append(['ins', a, seg_text(ch)])
            elif tag == W + 'del':
                a = ch.get(W + 'author') or '?'
                st[a]['del'] += 1
                segs.append(['del', a, seg_text(ch)])
            elif tag == W + 'r':
                # שינוי עיצוב תו בתוך ריצה
                rc = ch.find(W + 'rPr/' + W + 'rPrChange')
                if rc is not None:
                    st[rc.get(W + 'author') or '?']['fmt_char'] += 1
                segs.append(['keep', '', seg_text(ch)])
            elif tag == W + 'pPr':
                pc = ch.find(W + 'pPrChange')
                if pc is not None:
                    st[pc.get(W + 'author') or '?']['fmt_para'] += 1
        # החלפות: del ואחריו ins (או להפך) של אותו מחבר
        i = 0
        ptxt = None
        while i < len(segs):
            k, a, t = segs[i]
            if k in ('del', 'ins'):
                j = i + 1
                if j < len(segs) and segs[j][0] in ('del', 'ins') and segs[j][0] != k and segs[j][1] == a:
                    d = t if k == 'del' else segs[j][2]
                    n = segs[j][2] if k == 'del' else t
                    lay = layer(a)
                    if len(d) + len(n) <= 80:
                        pairs[lay][(d.strip(), n.strip())] += 1
                    if lay == 'אדם':
                        if ptxt is None:
                            ptxt = ''.join(s[2] for s in segs if s[0] != 'del')[:160]
                        human.append(dict(author=a, kind='החלפה', old=d[:200], new=n[:200], para=pi, context=ptxt))
                    i += 2
                    continue
                lay = layer(a)
                if k == 'del':
                    if len(t) <= 60: dels[lay][t.strip()] += 1
                else:
                    if len(t) <= 60: inss[lay][t.strip()] += 1
                if lay == 'אדם':
                    if ptxt is None:
                        ptxt = ''.join(s[2] for s in segs if s[0] != 'del')[:160]
                    human.append(dict(author=a, kind='מחיקה' if k == 'del' else 'הכנסה', old=t[:200] if k == 'del' else '', new=t[:200] if k == 'ins' else '', para=pi, context=ptxt))
            i += 1
    return dict(sec=round(time.time() - t0, 2), paras=pi, authors={a: dict(c) for a, c in st.items()},
                pairs=pairs, dels=dels, inss=inss, human=human)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', default=os.environ.get('LG_DRIVE') or r'C:\Users\Owner\Desktop\שיננא לHTML')
    ap.add_argument('--out', default='data/learn/tracked-12-10-2026.json')
    ap.add_argument('--top', type=int, default=40)
    a = ap.parse_args()
    files = sorted(f for f in os.listdir(a.src) if f.endswith('.docx') and not f.startswith(('~', '.')))
    perfile = {}
    tot = collections.defaultdict(collections.Counter)
    pairs = collections.defaultdict(collections.Counter)
    dels = collections.defaultdict(collections.Counter)
    inss = collections.defaultdict(collections.Counter)
    human = []
    for f in files:
        try:
            r = analyze(os.path.join(a.src, f))
        except Exception as e:
            print('כשל בקובץ', f, e); continue
        perfile[f] = dict(sec=r['sec'], paras=r['paras'], authors=r['authors'])
        for au, c in r['authors'].items():
            tot[au].update(c)
        for lay in r['pairs']:
            pairs[lay].update(r['pairs'][lay]); dels[lay].update(r['dels'][lay]); inss[lay].update(r['inss'][lay])
        for h in r['human']:
            h['file'] = f; human.append(h)
        print('%-44s %5.2fs  פסקאות %5d  מחברים %d' % (f[:44], r['sec'], r['paras'], len(r['authors'])))
    byl = collections.defaultdict(collections.Counter)
    for au, c in tot.items():
        byl[layer(au)].update(c)
    out = dict(
        date='12.10.2026', files=len(perfile),
        totals_by_author={au: dict(c) for au, c in sorted(tot.items(), key=lambda x: -sum(x[1].values()))},
        totals_by_layer={k: dict(v) for k, v in byl.items()},
        top_replacements={lay: [dict(old=o, new=n, count=c) for (o, n), c in pairs[lay].most_common(a.top)] for lay in pairs},
        top_deletions={lay: [dict(text=t, count=c) for t, c in dels[lay].most_common(a.top // 2)] for lay in dels},
        top_insertions={lay: [dict(text=t, count=c) for t, c in inss[lay].most_common(a.top // 2)] for lay in inss},
        human_changes=human,
        per_file=perfile)
    os.makedirs(os.path.dirname(a.out) or '.', exist_ok=True)
    json.dump(out, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('\nנכתב', a.out, '| קבצים', len(perfile), '| שינויי אדם', len(human))
    for k, v in byl.items():
        print(' שכבה', k, dict(v))


if __name__ == '__main__':
    main()
