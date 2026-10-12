# -*- coding: utf-8 -*-
"""learn.py - מושך מנקודת הקליטה את בחירות המנהל ומעדכן את tosafot/תוס-למידה.md.

לכל תוספות: איזה סגנון נבחר, האם נערך (ואז: מה היה הנוסח המקורי ומה נשאר), והערת המנהל לקלוד.
הכלל שעולה מכל בחירה נכתב בידי הווקר בסוף הסבב (סעיף "מה נלמד" בקובץ הפרומפט), לא כאן.

    uv run python tools/tosafot/learn.py kiddushin
"""
import os, sys, json, io, datetime
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'bakara'))
import _api

NAMES = {'a': 'שורה אחת', 'b': 'מהודק ומובן', 'c': 'קושיה ותירוץ', 'd': 'לשון התוספות המקוצרת', 'e': 'הנפקא מינה',
         'custom': 'ערוך ידנית'}


def blind_section(slug, doc):
    """מבחן המנועים העיוור (12.10.2026): מפענח אותיות לפי tosafot/<slug>/test-reveal.json ורושם לכל תוספות מה נבחר, מה נערך ומה ההערה.
    מופעל רק כשקיים קובץ החשיפה. האותיות א-ה בשרת הן אותיות הסדר המוגרל לכל תוספות; המיפוי למנוע נמצא בקובץ החשיפה."""
    d = os.path.join(ROOT, 'tosafot', slug)
    po, pr = os.path.join(d, 'test-options.json'), os.path.join(d, 'test-reveal.json')
    if not (os.path.exists(po) and os.path.exists(pr)):
        return None
    opt = json.load(io.open(po, encoding='utf-8'))['items']
    rev = json.load(io.open(pr, encoding='utf-8'))
    bykey = {str(it['key']): (rid, it) for rid, it in opt.items()}
    picks, notes = doc.get('picks', {}), doc.get('notes', {})
    last = {}
    for l in doc.get('log', []):
        last[str(l['n'])] = l
    L = ['## מבחן המנועים העיוור (%s)' % slug, '']
    for key in sorted(bykey, key=int):
        rid, it = bykey[key]
        m = rev['map'][rid]
        pk, nt = picks.get(key), (notes.get(key) or {}).get('t', '')
        if not pk and not nt:
            L += ['### פרק %s תוספות %s (%s): טרם נבחר' % (it['perek'], it['n'], it['dh']), '']
            continue
        L.append('### פרק %s תוספות %s (%s)' % (it['perek'], it['n'], it['dh']))
        if pk:
            if pk['p'] == 'custom':
                fr = (last.get(key) or {}).get('from', '')
                L.append('- נבחר: **נוסח שנערך** (מבוסס על %s)' % rev['tokens'].get(m.get(fr, ''), {}).get('label', fr))
                L.append('- הנוסח שערך המנהל: ' + pk['t'])
                if fr in it['options']:
                    L.append('- הנוסח המקורי של אותו מנוע: ' + it['options'][fr])
            else:
                L.append('- נבחר: **%s**' % rev['tokens'].get(m.get(pk['p'], ''), {}).get('label', pk['p']))
        elif nt.startswith('[אף אחת]'):
            L.append('- **אף אחת מחמש האופציות לא טובה**')
        if nt:
            L.append('- הערה: ' + nt)
        L.append('')
    return L


def main():
    slug = sys.argv[1]
    doc = _api.call('/tos?slug=%s&adm=1' % slug).get('doc') or {}
    bl = blind_section(slug, doc)
    styles = doc.get('styles', {})
    picks = doc.get('picks', {})
    notes = doc.get('notes', {})
    lines = ['# תוס-למידה - מה בחר המנהל ומה שונה', '',
             'נוצר על ידי `tools/tosafot/learn.py` מתוך נקודת הקליטה (`/tos`), %s.' % datetime.date.today().strftime('%d.%m.%Y'), '',
             'אחרי כל סבב מעודכן `תוס-פרומפט-סיכום.md` לפי מה שלמטה.', '', '## בחירות', '']
    if not picks:
        lines.append('טרם נבחר דבר.')
    for n in sorted(picks, key=int):
        p = picks[n]
        st = styles.get(n, {})
        lines.append('### תוספות מספר %s (%s)' % (n, st.get('dh', '')))
        lines.append('- נבחר: **%s**' % NAMES.get(p['p'], p['p']))
        if p['p'] == 'custom':
            lines.append('- נוסח שערך המנהל: ' + p['t'])
            near = [k for k in 'abcde' if st.get(k) and st[k][:20] == p['t'][:20]]
            lines.append('- נוסחאות המקור לצורך השוואה:')
            for k in 'abcde':
                if st.get(k):
                    lines.append('  - %s: %s' % (NAMES[k], st[k]))
        if n in notes:
            lines.append('- הערה לקלוד: ' + notes[n]['t'])
        lines.append('')
    nn = [n for n in notes if n not in picks]
    if nn:
        lines += ['## הערות על תוספות שטרם נבחר להם נוסח', '']
        for n in sorted(nn, key=int):
            lines.append('- תוספות %s: %s' % (n, notes[n]['t']))
    if bl:
        lines += [''] + bl
    out = os.path.join(ROOT, 'tosafot', 'תוס-למידה.md' if slug == 'kiddushin' else 'תוס-למידה-%s.md' % slug)
    with io.open(out, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    print('נכתב', out, '-', len(picks), 'בחירות')


if __name__ == '__main__':
    main()
