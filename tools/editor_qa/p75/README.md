# בדיקות פרומפט 75 (21.11.2026): סקירה פנימית - קבל/דחה/ערוך לכל שינוי בתוך הצעה

על האתר החי (leokmei.com), כמנהל מדומה; כל כתיבה לשרת העריכות נלכדת ואינה נשלחת. הכרטיסים הם הצעות סכם אמיתיות
מן המאגר (data/sakem/out) שנדחו, ולכן הנוסח החי עדיין המקורי.

    # לפני הפרסום: mas.js החי + הקבצים החדשים, מיד אחרי sakem_perek.js (כמו בבנייה)
    curl -s "https://leokmei.com/mas.js" -o /tmp/mas.js
    node tools/editor_qa/p75/mkmas.mjs /tmp/mas.js /tmp/mas75.js
    node tools/editor_qa/p75/run.mjs   --mas /tmp/mas75.js [--touch tab-portrait|tab-landscape] [--shots <תיקייה>]
    node tools/editor_qa/p75/edge.mjs  --mas /tmp/mas75.js [--conflict 1]
    node tools/editor_qa/p75/lines.mjs --mas /tmp/mas75.js
    # אחרי הפרסום: אותן פקודות בלי --mas
    node tools/sakem_tests/p75_units.mjs     # המנוע על כל ההצעות שבמאגר

- `run.mjs` - כרטיס עם 10+ שינויים: כפתור ליד העיפרון (במגע - בתחתית הכרטיס), קבל/דחה/ערוך, יציאה וחזרה (גם אחרי
  רענון), Delete אינו דוחה, ההחלה כהכרעה אחת עם "בטל", הנוסח בדף ושכבת העריכות, היומן ושחזור היחידות ממנו.
- `edge.mjs` - דחה/קבל את כל השאר, "בטל" אחרי הכרטיס האחרון בתור, כל היחידות נדחו = דחיית הכרטיס, התנגשות ושורה
  שננעלה בהדפסה ("לחץ שוב").
- `lines.mjs` - אותה סקירה בשורה אחת: "שורה שהתארכה" והצעת מציע מן העורך.
