# -*- coding: utf-8 -*-
"""coverage.py - מפת כיסוי המאגר: לכל מסכת, מה קיים במאגר חברותא ומה חסר, וכמה מהדפים כבר יושרו מול לאוקמי.

    uv run python tools/hv/coverage.py

פלט:
  <ריפו פרטי>/coverage-map.md      - דוח מלא (כולל שמות עמודים חסרים).
  data/hv/coverage.json            - מספרים בלבד (בלי שום לשון חברותא): נטען בלוח העבודה.
"""
import os, sys, re, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hv_common as H


def parse_cov_md():
    rows = {}
    p = os.path.join(H.CHAV, 'coverage.md')
    for ln in open(p, encoding='utf-8'):
        m = re.match(r'^\|\s*([^|]+?)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)(?::\s*(.*?))?\s*\|\s*$', ln)
        if m and m.group(1) not in ('מסכת',):
            rows[m.group(1)] = {'expected': int(m.group(2)), 'exist': int(m.group(3)), 'missing': int(m.group(4)),
                                'missing_pages': (m.group(5) or '').strip()}
    return rows


def main():
    cm = parse_cov_md()
    hv = {c.get('heb'): c for c in (H.jload(os.path.join(H.CHAV, 'coverage-hv.json'), []) or [])}
    pub, md = {}, ['# מפת כיסוי - מאגר חברותא מול לאוקמי גירסא', '',
                   '| מסכת | צפוי | קיים בחברותא | חסר בחברותא | יושרו מול לאוקמי | דפים שלנו ללא חברותא/ללא כיסוי |', '|---|---|---|---|---|---|']
    for heb in sorted(cm):
        c, h = cm[heb], hv.get(heb, {})
        al = h.get('with_our_text')
        pub[heb] = {'expected': c['expected'], 'exist': c['exist'], 'missing': c['missing'], 'aligned': al,
                    'no_our_text': len(h.get('without_our_text') or []) if h else None, 'note': h.get('error')}
        md.append('| %s | %d | %d | %d (%s) | %s | %s |' % (
            heb, c['expected'], c['exist'], c['missing'], c['missing_pages'] or '-',
            al if al is not None else 'לא נבנה (%s)' % (h.get('error') or 'ללא קובץ וורד'),
            len(h.get('without_our_text') or []) if h else '-'))
    open(os.path.join(H.CHAV, 'coverage-map.md'), 'w', encoding='utf-8').write('\n'.join(md) + '\n')
    H.jsave(os.path.join(H.ROOT, 'data', 'hv', 'coverage.json'), pub)
    tot = sum(v['exist'] for v in pub.values())
    print('מסכתות: %d · עמודי חברותא קיימים: %d · יושרו: %d' % (len(pub), tot, sum((v['aligned'] or 0) for v in pub.values())))


if __name__ == '__main__':
    main()
