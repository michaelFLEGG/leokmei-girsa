# תשע מסכתות חדשות - כלי העבודה (11.10.2026)

סדר ההרצה לכל מסכת חדשה (כל הכלים כותבים לתיקיית עבודה ב-LG_DRIVE, לא לתיקיית הדרייב):
1. split_nine.py - פיצול קובץ מאוחד לקובץ למסכת; compare_dropped.py - השוואת חלק שנמחק מול הקובץ באתר.
2. tools/unify_styles.py - איחוד סגנונות להגדרות הקנוניות של חולין.
3. run_mech_stage.py - איחוד סגנונות ואחריו המנוע המכני (engine/laukmi-engine).
4. tools/m6_word.py, m7_word.py, m8_word.py, m9_hadran.py, orn_clean_word.py, spacing_word.py (דרך LG_DRIVE).
5. engine/laukmi-engine/sem_batches.py prep ... - אצוות סמנטיות (ציטוטים וארמית) לסוכנים, ואחר כך apply.
6. dump_heads.py, merge_heads.py, tools/heading_insert_word.py - כותרות נושא בנוסח קלוד (חומות).
7. tools/verses_apply.py, tools/mishna_apply.py (אחרי בנייה חלקית), tools/nikud_generate.py.
8. (שבת בלבד) adv_prep.py, adv-editor-prompt.md, adv-checker-prompt.md, engine/laukmi-engine/adv_apply.py.
9. claude_findings.py, bakara_all.py, tools/bakara/push.py - ממצאי בקרה.

תיקוני תשתית שנעשו כאן: טעינת כללי "ctx" שנלמדו כבר אינה מוחלת גלובלית (היתה מוסיפה "!" אחרי כל "הוא");
הכלי המכני נבדק פעם אחת לפסקה; מספור פרקים עד 24; הבקרה מזהה "פתיחת פרק".
