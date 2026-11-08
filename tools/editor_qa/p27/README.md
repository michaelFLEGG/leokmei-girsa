# בדיקות פרומפט 27 (8.11.2026)

האתר החי לקריאה בלבד, mas.js מקומי, כל כתיבה חסומה. תשובות ה-Worker לסקירה מדומות מקובץ (--fake).
המפתח "sakem/out" בלי לוכסן בראשו: ב-Git Bash לוכסן בראש ארגומנט מומר לנתיב.

    uv run python tools/editor_qa/p24/mkmas.py . _work/mas.js
    MODE=edit uv run --with playwright python tools/editor_qa/p27/probe.py _work/mas.js 1400 tools/editor_qa/p27/s_kadkod.py --fake "sakem/out=_work/p27/fake-out.json"

s_kadkod.py - בדיקת חזרה לתקלת "לא ניתן לפצל שורה קצרה לכמה שורות" (בבא בתרא עה., "ושמתי כדכד"):
כותרת (נושא) חדשה בראש הקטע הזיזה את התאמת היחידות. לפני התיקון: ok=false; אחריו: ok=true,
והשורות במקומן. fake-out.json = {ok:true, job, out (data/sakem/out/<jid>.json), dec (skm:dec:<jid>)}.
