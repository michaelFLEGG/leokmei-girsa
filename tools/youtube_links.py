# -*- coding: utf-8 -*-
"""youtube_links.py - docs/youtube-links.md: לכל שיעור ביוטיוב, הכתובת של הדף המקביל
באתר ושורת תיאור מוכנה להדבקה (פרומפט 10, 28.10.2026).

המקור הוא רשימת השיעורים של האתר (שרת leokmei-suggest, נקודה /lessons, קריאה פתוחה),
כי זו הרשימה היחידה שקושרה כבר למסכת ולדף. הכלי אינו נוגע בערוץ עצמו.
הרצה:  uv run python tools/youtube_links.py
"""
import os, io, json, urllib.request, datetime

API = 'https://leokmei-suggest.m7654301.workers.dev/lessons'
BASE = 'https://leokmei.com'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'docs', 'youtube-links.md')
GEM = {'א': 1, 'ב': 2, 'ג': 3, 'ד': 4, 'ה': 5, 'ו': 6, 'ז': 7, 'ח': 8, 'ט': 9, 'י': 10, 'כ': 20, 'ל': 30, 'מ': 40,
       'נ': 50, 'ס': 60, 'ע': 70, 'פ': 80, 'צ': 90, 'ק': 100, 'ר': 200, 'ש': 300, 'ת': 400}


def daf_path(daf):
    n = sum(GEM.get(c, 0) for c in str(daf))
    return '%d%s' % (n, 'b' if str(daf).strip().endswith(':') else 'a') if n else ''


def main():
    req = urllib.request.Request(API, headers={'User-Agent': 'leokmei-build/1.0'})
    items = json.loads(urllib.request.urlopen(req, timeout=20).read().decode('utf-8')).get('items', [])
    out = ['# קישורי יוטיוב לדפים באתר', '',
           'נוצר ב-%s מרשימת השיעורים של האתר (%d שיעורים).' % (datetime.date.today().strftime('%d.%m.%Y'), len(items)), '',
           'לכל שיעור: הכתובת של הדף המקביל, ושורה מוכנה להדבקה בראש התיאור ביוטיוב. '
           'קישור מתיאור השיעור לדף הנקי באתר הוא אחד האותות החזקים שגוגל מקבל מבחוץ.', '']
    if not items:
        out += ['**כרגע אין שיעורים ברשימת האתר.** ברגע שיתווספו שיעורים במדור "שיעורים" (מסך המנהל), '
                'הרצה חוזרת של הכלי תמלא כאן את הרשימה.', '',
                '## התבנית לכל שיעור', '',
                'שורת התיאור (להדבקה בראש התיאור ביוטיוב, במקום [מסכת], [דף] והכתובת):', '',
                '```', 'קיצור הדף בכתב - [מסכת] [דף] בקיצור, לאוקמי גירסא: https://leokmei.com/[מסכת-באנגלית]/[דף].html',
                'קיצור הדף היומי בכל יום: https://leokmei.com/hadaf-hayomi.html', '```', '',
                'דוגמה: ערכין דף טו עמוד ב - https://leokmei.com/arakhin/15b.html']
    for l in items:
        dp = daf_path(l.get('from', ''))
        url = '%s/%s/%s.html' % (BASE, l['slug'], dp) if dp else '%s/%s/' % (BASE, l['slug'])
        out += ['## %s' % l.get('title', ''), '',
                '- השיעור: https://www.youtube.com/watch?v=%s' % l.get('vid', ''),
                '- הדף באתר: %s' % url, '', '```',
                'קיצור הדף בכתב - לאוקמי גירסא: %s' % url,
                'קיצור הדף היומי בכל יום: %s/hadaf-hayomi.html' % BASE, '```', '']
    io.open(OUT, 'w', encoding='utf-8').write('\n'.join(out) + '\n')
    print('נכתב', OUT, '-', len(items), 'שיעורים')


if __name__ == '__main__':
    main()
