# בדיקות פרומפט 25 (8.11.2026): "בחר נוסח" על הטקסט עצמו

האתר החי לקריאה בלבד: קובץ המסכת (bekhorot.x.js) נמשך מן האתר, וקטע "בחר נוסח" שבו מוחלף בקובץ המקומי
(אם הקוד הישן לא נמצא כלשונו - הבדיקה עוצרת). כל כתיבה נחסמת ונרשמת. אסימון מנהל מדומה.

    git show origin/main:tools/alts_ui.js > _work/alts_old.js      # הגרסה שבאתר, לאיתור הקטע להחלפה
    uv run --with playwright python tools/editor_qa/p25/probe.py tools/alts_ui.js 1400 tools/editor_qa/p25/s_flow.py
    P25EDIT=1 uv run --with playwright python tools/editor_qa/p25/probe.py tools/alts_ui.js 1400 tools/editor_qa/p25/s_flow.py
    uv run --with playwright python tools/editor_qa/p25/probe.py tools/alts_ui.js 400 tools/editor_qa/p25/s_phone.py 860
    uv run --with playwright python tools/editor_qa/p25/probe.py tools/alts_ui.js 1400 tools/editor_qa/p25/s_sakem.py

אחרי פרסום: "-" במקום הקובץ המקומי בודק את הקוד החי כפי שהוא.
