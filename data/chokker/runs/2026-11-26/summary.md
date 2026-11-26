# החוקר - סיכום הלילה 2026-11-26

מסכים: 9 · הדפסות: 21 · כפתורים: 28 · ממצאים ייחודיים: 131 · חדשים: 131 · נסיגות: 0 · נעלמו/אומתו: 0

## לפי כלל (פתוחים הלילה)

- P07-engine-warn (41) - מנוע ההדפסה אינו מתריע
- N01-foreign-domain (23) - נטפרי: הכל תחת דומיין האתר, בלי סקריפטים, גופנים או שרתים חיצוניים
- G02-offscreen (18) - אף רכיב לא חורג מרוחב המסך
- B01-btn-fail (15) - כל כפתור לחיץ ועובד
- G04-tap-small (13) - כפתורים נוחים למגע בטאבלט ובטלפון
- L13-side-long (6) - כותרת צד עד שתי מילים, שלוש רק בחריג
- T06-gregorian (4) - תאריכים עבריים בלבד
- L18-heading-no-space (4) - כל כותרת רגילה - תמיד לפחות רווח לפניה כמו Ctrl+0
- T08-space-before-punct (2) - רווח לפני סימן פיסוק
- L20-pasuk-color (1) - פסוקים בשחור
- L21-daf-jump (1) - כל דף ועמוד מסומן במקומו, ברצף בלי קפיצות
- G05-font-fallback (1) - כל גופן שהדף מבקש נטען (לא גופן מערכת חלופי)
- P04-white-gap (1) - אין חללים לבנים גדולים בהדפסה
- P05-unbalanced-end (1) - כל סוף פרק מאוזן בין שני הטורים ולא "צולע"

## דוגמאות (עד 5 לכל כלל)

- `162dc24e4bdb` [פתוח] B01-btn-fail bava-batra · phone/btn · דף קודם: Page.wait_for_selector: Timeout 60000ms exceeded.
Call log:
  - waiting for locator("#flow .row") to
- `def40f33884b` [פתוח] B01-btn-fail bava-batra · phone/btn · דף הבא: Page.click: Timeout 4000ms exceeded.
Call log:
  - waiting for locator("[data-chk=\"6\"]")

- `cf8b723e5343` [פתוח] B01-btn-fail bava-batra · phone/btn · גמרא: Page.click: Timeout 4000ms exceeded.
Call log:
  - waiting for locator("[data-chk=\"7\"]")

- `f48843b3a7d5` [פתוח] B01-btn-fail bava-batra · phone/btn · תוס': Page.click: Timeout 4000ms exceeded.
Call log:
  - waiting for locator("[data-chk=\"8\"]")

- `1cbfe8b3d5a7` [פתוח] B01-btn-fail bava-batra · desktop/btn,phone/btn · עוד: Page.click: Timeout 4000ms exceeded.
Call log:
  - waiting for locator("[data-chk=\"9\"]")

- `cceefa67c514` [פתוח] G05-font-fallback bava-batra · phone/btn:הש"ס · גופן לא נטען: Vilna (334 רכיבים)
- `230f1f83fae6` [פתוח] L21-daf-jump bava-batra · desktop/flow,wide/flow · רצף ציוני הדף נשבר: יט: ← כא.
- `ff7c54737a20` [פתוח] N01-foreign-domain * · net · static.cloudflareinsights.com (17 בקשות) 
- `f92bdde0130c` [פתוח] N01-foreign-domain * · net · leokmei-suggest.m7654301.workers.dev (42 בקשות) שרת ההצעות וההדפסה - לבדוק שנטפרי אינו חוסם (רצוי להעביר תחת leokmei.com)
- `8a68a384d3da` [פתוח] N01-foreign-domain * · net · www.clarity.ms (9 בקשות) 
- `be7acd5b08c0` [פתוח] N01-foreign-domain * · net · scripts.clarity.ms (9 בקשות) 
- `111afc66f5e2` [פתוח] N01-foreign-domain * · net · c.clarity.ms (2 בקשות) 
- `83a2ee7baa28` [פתוח] P04-white-gap bava-batra · print/a4lg/פרק חמישי|המוכר את הספינה,print/a4lg/פרק עשירי|גט פשוט,print/a4lg/פרק ראשון|השותפין · חלל לבן של 158.5 מ"מ בעמוד 1
- `89ee8926ec56` [פתוח] P05-unbalanced-end bava-batra · print/a4lg/פרק שלישי|חזקת,print/a4lg/פרק שני|לא יחפור,print/b5lg/פרק רביעי|המוכר את הבית · סוף הפרק צולע: הפרש 24.4 מ"מ בין הטורים
- `f1979bb62af0` [פתוח] G02-offscreen bava-batra · tablet-l/book,tablet-l/flow,tablet-p/book · אלמנט חורג מרוחב המסך: sheet
- `39d72443ddd8` [פתוח] G02-offscreen bava-batra · tablet-l/book,tablet-l/flow,tablet-p/book · אלמנט חורג מרוחב המסך: shhd
- `e75231a7fcbb` [פתוח] G02-offscreen bava-batra · tablet-p/book · אלמנט חורג מרוחב המסך: nm
- `391078f0166a` [פתוח] G02-offscreen bava-batra · tablet-l/book,tablet-l/flow,tablet-p/book · אלמנט חורג מרוחב המסך: df
- `70938214710e` [פתוח] G02-offscreen bava-batra · tablet-l/book,tablet-l/flow,tablet-p/book · אלמנט חורג מרוחב המסך: shbody
- `15884dc89b81` [פתוח] L13-side-long bava-batra · desktop/book,desktop/flow,phone/flow · כותרת צד ארוכה מ-3 מילים: ה. רבא לבני מחוזא
- `e902eeefa505` [פתוח] L13-side-long bava-batra · desktop/book,desktop/flow,phone/flow · כותרת צד ארוכה מ-3 מילים: ז. דרש ר"י בר"ש
- `d8e82ab898fb` [פתוח] L13-side-long bava-batra · desktop/book,desktop/flow,phone/flow · כותרת צד ארוכה מ-3 מילים: יא. הוא היה אומר,
- `b4f66ed9825d` [פתוח] L13-side-long bava-batra · desktop/book,desktop/flow,phone/flow · כותרת צד ארוכה מ-3 מילים: יב. ר"ד ברבי ינאי
- `b9f35ad12cf8` [פתוח] L13-side-long bava-batra · tablet-l/book · כותרת צד ארוכה מ-3 מילים: - תנאי היא: א. ר"א
- `54605729b1c4` [פתוח] L18-heading-no-space bava-batra · tablet-l/book · כותרת בלי רווח לפניה: שבי קשה מכולם - שכולם ישנם בו. קופה ותמח
- `588db531f790` [פתוח] L18-heading-no-space bava-batra · tablet-l/book · כותרת בלי רווח לפניה: שכפה את רנב"א, ולקח ממנו ד' מאות זוז לצד
- `d69bffa5e7a2` [פתוח] L18-heading-no-space bava-batra · tablet-l/book · כותרת בלי רווח לפניה: כך היו כותבי ספרים שבירושלים עושין ספריה
- `c48f9858a972` [פתוח] L18-heading-no-space bava-batra · tablet-l/book · כותרת בלי רווח לפניה: 'ובנות ילדו להם' - רביה או מריבה לרי"ו: 
- `8289df405f23` [פתוח] P07-engine-warn bava-batra · print/a4lg/פרק ראשון|השותפין,print/b5lg/פרק ראשון|השותפין,print/book/פרק ראשון|השותפין · 50 תוספות שטקסט העוגן שלהן אינו נמצא עוד בדף (הטקסט נערך אחרי העיגון), והוצמדו בפרק שלהן: י', י"ב, י"ט, כ', כ"ז, כ"ח, כ"ט, ל', ל"א, ל"ב, ל"ג, ל"ה, ל"ח
- `fc408089f44e` [פתוח] P07-engine-warn bava-batra · print/a4lg/פרק ראשון|השותפין,print/b5lg/פרק ראשון|השותפין,print/book/פרק ראשון|השותפין · גובה פסקה אינו כפולה של גובה השורה (nose): 14.43 (ב:, יחידה 39)
- `9e49050b770c` [פתוח] P07-engine-warn bava-batra · print/a4lg/פרק ראשון|השותפין,print/b5lg/פרק ראשון|השותפין,print/book/פרק ראשון|השותפין · גובה פסקה אינו כפולה של גובה השורה (u): 9.32 (ג., יחידה 78)
- `ddbe5659732f` [פתוח] P07-engine-warn bava-batra · print/a4lg/פרק ראשון|השותפין,print/b5lg/פרק ראשון|השותפין,print/book/פרק ראשון|השותפין · גובה פסקה אינו כפולה של גובה השורה (m): 13.32 (ד:, יחידה 192)
- `a9c11caee96f` [פתוח] P07-engine-warn bava-batra · print/a4lg/פרק ראשון|השותפין,print/b5lg/פרק ראשון|השותפין,print/book/פרק ראשון|השותפין · גובה פסקה אינו כפולה של גובה השורה (u): 11.27 (ז., יחידה 333)
- `ba7af6d934f0` [פתוח] T06-gregorian bava-batra · desktop/book,desktop/flow,phone/flow · תאריך לועזי (רק תאריכים עבריים): …ראית, א"ל: עולם הפוך ראיתי, עליונים למטה ותחתונים למעלה.- א"…
- `8d8414917c01` [פתוח] T06-gregorian bava-batra · tablet-l/book · תאריך לועזי (רק תאריכים עבריים): … מה פירש דוד אבא: 'פזר נתן לאביונים צדקתו עומדת לעד קרנו תרו…
- `25d6c0f8cd02` [פתוח] T06-gregorian bava-batra · tablet-l/book · תאריך לועזי (רק תאריכים עבריים): …אית? א"ל: עולם הפוך ראיתי - עליונים למטה ותחתונים למעלה. א"ל…
- `8a2a61504bd9` [פתוח] T06-gregorian bava-batra · desktop/flow,wide/flow · תאריך לועזי (רק תאריכים עבריים): …והיינו דפורסין נשבין ליונים בריחוק מישוב שלשים ריס…
- `891fd140dbff` [פתוח] G04-tap-small bava-batra · phone/btn:בחירת מסכת או דף,phone/btn:דף קודם,phone/btn:חזרה מהירה · כפתור קטן מדי למגע (25x11): פרק א, משנה א
- `60ab5a878c0d` [פתוח] G04-tap-small bava-batra · phone/btn:בחירת מסכת או דף,phone/btn:דף קודם,phone/btn:חזרה מהירה · כפתור קטן מדי למגע (15x15): הזוהר על סוגיא זו
- `12d48ea6d947` [פתוח] G04-tap-small bava-batra · phone/btn:דף קודם,phone/btn:חזרה מהירה,phone/btn:חיפוש · כפתור קטן מדי למגע (40x19): פרק א, משנה ג
- `0b395bd0ff64` [פתוח] G04-tap-small bava-batra · phone/btn:דף קודם,phone/btn:חזרה מהירה,phone/btn:חיפוש · כפתור קטן מדי למגע (42x19): פרק א, משנה ד
- `5a78065705e5` [פתוח] G04-tap-small bava-batra · tablet-l/book,tablet-l/flow,tablet-p/book · כפתור קטן מדי למגע (42x19): פרק א, משנה ה
- `9fd771165a5c` [פתוח] L20-pasuk-color bava-batra · desktop/book,desktop/flow,phone/flow · פסוק לא בשחור: rgb(46, 63, 107)
- `ed095ac402c0` [פתוח] T08-space-before-punct bava-batra · desktop/book,desktop/flow,phone/flow · רווח לפני סימן פיסוק: …ה ד' מאות דינרים לר"א: ולא קיבל , שלחה לרבא, וקיבל משום שלום…
- `9fe9527af9fa` [פתוח] T08-space-before-punct bava-batra · desktop/book,desktop/flow,phone/flow · רווח לפני סימן פיסוק: … הָאֱלֹהִים לְהִתְיַצֵּב עַל ה' , וַיֹּאמֶר ה' אֶל הַשָּׂטָן…
