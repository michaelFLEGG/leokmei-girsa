# -*- coding: utf-8 -*-
"""מריץ את המנוע המכני על בכורות. בבכורות סגנונות הגוף המוזח נקראים
0.1, 0.2 ו-List Paragraph (בחולין: "פיסקת תשובה"), ולכן הם נוספים כאן
לקבוצת הגוף - בלי לגעת בטבלאות המשותפות."""
import sys, runpy
import laukmi_rules
laukmi_rules.BODY |= {"0.1", "0.2", "List Paragraph"}
sys.argv = ['masechet_1_mechani.py'] + sys.argv[1:]
runpy.run_path('masechet_1_mechani.py', run_name='__main__')
