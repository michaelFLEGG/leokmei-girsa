# בדיקות פרומפט 24 (8.11.2026): כפתור סכם, חצים כמו בוורד, שדות מימין לשמאל

הכול רץ על האתר החי לקריאה בלבד: הדף נטען מ-leokmei.com, קוד העורך (mas.js) מוגש מקובץ מקומי,
וכל כתיבה (PUT/POST, הגשר המקומי) נחסמת ונרשמת. אסימון מנהל מדומה. אין שום כתיבה לשרת.

    uv run python tools/editor_qa/p24/mkmas.py . _work/mas.js        # מרכיב את mas.js מן המקור (זהה לחי בבית לבית כשאין שינוי)
    uv run --with playwright python tools/editor_qa/p24/probe.py _work/mas.js 1000 tools/editor_qa/p24/s_test.py   # חצים, Ctrl, Home/End
    uv run --with playwright python tools/editor_qa/p24/probe.py _work/mas.js 1000 tools/editor_qa/p24/s_ui.py     # סכם, סגנונות, כותרת צד
    uv run --with playwright python tools/editor_qa/p24/qa_wrap.py _work/mas.js --base https://leokmei.com --path /bekhorot.html --n 8

שינוי CSS בדף (build_site) אינו נכנס ל-mas.js: לפני פרסום יש להזריק אותו (משתנה הסביבה P24CSS לקובץ CSS).
רוחבים שנבדקו: 1400, 1000, 743, 560. בכל ריצה: שורות OK/FAIL, ובסוף ERRORS ו-BLOCKED.
