# לאוקמי גירסא - האתר

מקור האמת הוא קובצי הוורד בתיקיית הדרייב "שיננא לHTML". השומר (GitHub Actions) מוריד אותם כל חצי שעה,
ממיר לפי הסגנונות (tools/docx2json.py), בונה את עמודי המסכתות והשער (tools/build_all.py) ומפרסם ל-GitHub Pages.

הרצה מקומית: `pip install lxml && python tools/fetch.py && python tools/build_all.py` ואז לפתוח site/index.html.
