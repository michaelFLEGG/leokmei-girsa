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


def main():
    slug = sys.argv[1]
    doc = _api.call('/tos?slug=%s&adm=1' % slug).get('doc') or {}
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
    out = os.path.join(ROOT, 'tosafot', 'תוס-למידה.md')
    with io.open(out, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    print('נכתב', out, '-', len(picks), 'בחירות')


if __name__ == '__main__':
    main()
