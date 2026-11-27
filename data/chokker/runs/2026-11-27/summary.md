# החוקר - סיכום הלילה 2026-11-27

מסכים: 929 · הדפסות: 640 · כפתורים: 1147 · ממצאים ייחודיים: 3852 · חדשים: 3780 · נסיגות: 0 · נעלמו/אומתו: 59

## לפי כלל (פתוחים הלילה)

- G04-tap-small (1068) - כפתורים נוחים למגע בטאבלט ובטלפון
- G02-offscreen (736) - אף רכיב לא חורג מרוחב המסך
- P07-engine-warn (666) - מנוע ההדפסה אינו מתריע
- B01-btn-fail (528) - כל כפתור לחיץ ועובד
- L13-side-long (212) - כותרת צד עד שתי מילים, שלוש רק בחריג
- T01-em-dash (111) - מקף ארוך אסור בכל מקום (תצוגה, הדפסה, ייצוא, ממשק)
- T08-space-before-punct (60) - רווח לפני סימן פיסוק
- N02-http-error (59) - אין בקשה שנכשלת (404/500)
- T06-gregorian (57) - תאריכים עבריים בלבד
- G05-font-fallback (54) - כל גופן שהדף מבקש נטען (לא גופן מערכת חלופי)
- E01-console (46) - אין שגיאות JavaScript
- L05-peliga (41) - "חלקו/חולק" במקום פליגא/פלגו/פליג
- L20-pasuk-color (36) - פסוקים בשחור
- N01-foreign-domain (30) - נטפרי: הכל תחת דומיין האתר, בלי סקריפטים, גופנים או שרתים חיצוניים
- T11-final-letter-mid (28) - אות סופית באמצע מילה
- P04-white-gap (23) - אין חללים לבנים גדולים בהדפסה
- L18-heading-no-space (19) - כל כותרת רגילה - תמיד לפחות רווח לפניה כמו Ctrl+0
- L21-daf-jump (18) - כל דף ועמוד מסומן במקומו, ברצף בלי קפיצות
- P05-unbalanced-end (17) - כל סוף פרק מאוזן בין שני הטורים ולא "צולע"
- P01-print-fail (17) - כל פרק מודפס בכל פרופיל (A4, B5, חוברת) עד הסוף
- L03-yesh-beineihem (15) - "נפק"מ" ולא "יש ביניהם"
- L11-dup-row (2) - שורה כפולה - "ודאי טעות", להסיר בלי לשאול
- L23-heading-orphan (2) - לעולם אין להפריד כותרת מהילדים שלה
- T03-latin (2) - אותיות לועזיות בגוף הטקסט (מותר רק leokmei.com, PDF, QR, A4, B5)
- L04-shaninu-sham (1) - "תנן שם"/"תנא שם" ולא "שנינו שם"
- L19-sliku (1) - "סליקו תוספות"/"כאן נשלמו דברי התוס'" ו"הדרן" אינם תוס' - לא להציג ולא למספר
- L15-side-two-lines (1) - כותרת צד שלא נכנסת - להקטין מעט ולא לשבור לשורה שנייה ("מבלבל")
- L16-side-repeat (1) - אחרי כותרת אין לכפול בשורה שאחריה את מה שכבר כתוב בה
- L02-shone-kan (1) - "שאני כאן" ולא "שונה כאן"

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
- `f0810d0abb55` [פתוח] G05-font-fallback https://xn--8dbacdxfna0hp.com/ · desktop/page,phone/page,tablet-l/page · גופן לא נטען: Heebo (2 רכיבים)
- `7eafae394bd9` [פתוח] G05-font-fallback https://xn--8dbacdxfna0hp.com/%D7%96%D7%95%D7%94%D7%A8-%D7%91%D7%92%D7%A8%D7%A1%D7%90 · desktop/page,phone/page,tablet-l/page · גופן לא נטען: Frank Ruhl Libre (4 רכיבים)
- `04b3004c98cd` [פתוח] G05-font-fallback https://xn--8dbacdxfna0hp.com/%D7%96%D7%95%D7%94%D7%A8-%D7%A8%D7%91%D7%90 · desktop/page,phone/page,tablet-l/page · גופן לא נטען: Frank Ruhl Libre (2 רכיבים)
- `bbe1d5ce8ad7` [פתוח] G05-font-fallback https://xn--8dbacdxfna0hp.com/%D7%94%D7%96%D7%95%D7%94%D7%A8-%D7%A9%D7%9C%D7%99 · desktop/page,phone/page,tablet-l/page · גופן לא נטען: Frank Ruhl Libre (2 רכיבים)
- `b032248141ca` [פתוח] L11-dup-row sukkah · desktop/book,desktop/flow,phone/flow · שורה כפולה: היכן מעמיד את הטפח
- `5630864048d6` [פתוח] L11-dup-row sukkah · desktop/book,desktop/flow,phone/flow · שורה כפולה: שלוש לשונות ברבא
- `2bee5d806e91` [פתוח] L19-sliku makkot · desktop/flow,wide/flow · "סליקו/כאן נשלמו" מוצג: כגון 'סליקום' ו'אקרא דסליקום'. [והיינו כפר הסמוך ל
- `230f1f83fae6` [פתוח] L21-daf-jump bava-batra · desktop/flow,wide/flow · רצף ציוני הדף נשבר: יט: ← כא.
- `4cc808f40cc6` [פתוח] L21-daf-jump berakhot · desktop/book,desktop/flow,phone/flow · רצף ציוני הדף נשבר: יב: ← יא.
- `95839f0bc3c6` [פתוח] L21-daf-jump berakhot · desktop/flow,wide/flow · רצף ציוני הדף נשבר: יא. ← יג.
- `f3d5d70baac6` [פתוח] L21-daf-jump yevamot · desktop/book,desktop/flow,phone/flow · רצף ציוני הדף נשבר: יא. ← יב:
- `830dd0b549d4` [פתוח] L21-daf-jump yevamot · desktop/book,desktop/flow,phone/flow · רצף ציוני הדף נשבר: יד. ← טו:
- `335f60d09a08` [פתוח] L23-heading-orphan kiddushin · desktop/book,tablet-l/book,tablet-l/flow · כותרת נותקה מילדיה בסוף טור: 'וְרָאִיתָ בַּשִּׁבְיָה' - בשעת שביה, 'א
- `33192d7fb469` [פתוח] L23-heading-orphan kiddushin · desktop/book,wide/book · כותרת נותקה מילדיה בסוף טור: מי יאמר שאין הנאה לשניהם? ועוד: 'מִשְׁכּ
- `ff7c54737a20` [פתוח] N01-foreign-domain * · net · static.cloudflareinsights.com (17 בקשות) 
- `f92bdde0130c` [פתוח] N01-foreign-domain * · net · leokmei-suggest.m7654301.workers.dev (42 בקשות) שרת ההצעות וההדפסה - לבדוק שנטפרי אינו חוסם (רצוי להעביר תחת leokmei.com)
- `8a68a384d3da` [פתוח] N01-foreign-domain * · net · www.clarity.ms (9 בקשות) 
- `be7acd5b08c0` [פתוח] N01-foreign-domain * · net · scripts.clarity.ms (9 בקשות) 
- `111afc66f5e2` [פתוח] N01-foreign-domain * · net · c.clarity.ms (2 בקשות) 
- `9115aafb744d` [פתוח] N02-http-error * · net · 403 https://xn--8dbacdxfna0hp.com/d/bk/girsa/_index.js?v=72c8c5a35a
- `be88b9a37ed1` [פתוח] N02-http-error * · net · 403 https://xn--8dbacdxfna0hp.com/d/bk/girsa/_zref-links.js?v=6018098247
- `53b90169d9c8` [פתוח] N02-http-error * · net · 403 https://xn--8dbacdxfna0hp.com/%D7%96%D7%95%D7%94%D7%A8-%D7%A8%D7%91%D7%90-%D7%A0%D7%AA%D7%95%D7%A0%D7%99%D7%9D/_index.js?v=fff5567a5fb8
- `74d69c9b4c4d` [פתוח] N02-http-error * · net · 403 https://xn--8dbacdxfna0hp.com/d/bk/rava/_hekef.js?v=4ad4a3f96c
- `fe52015d8970` [פתוח] N02-http-error * · net · 403 https://xn--8dbacdxfna0hp.com/api/raza-uploads
- `be9f70d3b976` [פתוח] P01-print-fail bava-metzia · print/a4lg/פרק חמישי|איזהו נשך,print/a4lg/פרק עשירי|הבית והעלייה,print/a4lg/פרק ראשון|שנים אוחזין · מצב blocked ניתן להדפיס פרק אחד ביום. מחר אפשר להדפיס פרק נוסף.
- `6c8aad7ba50d` [פתוח] P01-print-fail arakhin · print/a4lg/פרק חמישי|האומר משקלי עלי,print/a4lg/פרק ראשון|הכל מעריכין,print/a4lg/פרק רביעי|השג יד · מצב blocked ניתן להדפיס פרק אחד ביום. מחר אפשר להדפיס פרק נוסף.
- `18348c41cb76` [פתוח] P01-print-fail bava-batra · print/a4lg/פרק חמישי|המוכר את הספינה,print/a4lg/פרק עשירי|גט פשוט,print/a4lg/פרק ראשון|השותפין · מצב blocked ניתן להדפיס פרק אחד ביום. מחר אפשר להדפיס פרק נוסף.
- `3f562157bd6d` [פתוח] P01-print-fail nedarim · print/a4lg/פרק אחד עשר|ואלו נדרים,print/a4lg/פרק חמישי|השותפין,print/a4lg/פרק עשירי|נערה המאורסה · מצב blocked ניתן להדפיס פרק אחד ביום. מחר אפשר להדפיס פרק נוסף.
- `3f3740686351` [פתוח] P01-print-fail makkot · print/a4lg/פרק ראשון|כיצד העדים,print/a4lg/פרק שלישי|ואלו הן הלוקין,print/a4lg/פרק שני|אלו הן הגולין · מצב blocked ניתן להדפיס פרק אחד ביום. מחר אפשר להדפיס פרק נוסף.
- `745fdd11b25b` [פתוח] P04-white-gap berakhot · print/a4lg/פרק חמישי|אין עומדין,print/a4lg/פרק ראשון|מאמתי,print/a4lg/פרק רביעי|תפלת השחר · חלל לבן של 65.5 מ"מ בעמוד 1
- `d9a160eb7195` [פתוח] P04-white-gap beitzah · print/a4lg/פרק חמישי|משילין,print/a4lg/פרק ראשון|ביצה,print/a4lg/פרק רביעי|המביא כדי יין · חלל לבן של 120.4 מ"מ בעמוד 1
- `95a2cb2bced2` [פתוח] P04-white-gap yevamot · print/a4lg/פרק  תשיעי|יש מותרות,print/a4lg/פרק אחד עשר|נושאין על האנוסה,print/a4lg/פרק ארבעה עשר|חרש שנשא · חלל לבן של 249.9 מ"מ בעמוד 1
- `42796e5ecc9b` [פתוח] P04-white-gap shabbat · print/a4lg/פרק אחד ועשרים|נוטל,print/a4lg/פרק אחד עשר|הזורק,print/a4lg/פרק ארבעה ועשרים|מי שהחשיך · חלל לבן של 164.6 מ"מ בעמוד 1
- `a5c2f644e07b` [פתוח] P04-white-gap rosh-hashanah · print/a4lg/פרק ראשון|ארבעה ראשי שנים,print/a4lg/פרק רביעי|יום טוב,print/a4lg/פרק שלישי|ראוהו ב"ד · חלל לבן של 74.7 מ"מ בעמוד 1
- `901e204bf4be` [פתוח] P05-unbalanced-end berakhot · print/book/פרק ראשון|מאמתי · סוף הפרק צולע: הפרש 22.4 מ"מ בין הטורים
- `c5435b70d555` [פתוח] P05-unbalanced-end beitzah · print/book/פרק ראשון|ביצה · סוף הפרק צולע: הפרש 39.6 מ"מ בין הטורים
- `574f324d5abf` [פתוח] P05-unbalanced-end shabbat · print/a4lg/פרק ארבעה עשר|שמונה שרצים,print/a4lg/פרק עשירי|המצניע,print/a4lg/פרק שבעה עשר|כל הכלים · סוף הפרק צולע: הפרש 12.2 מ"מ בין הטורים
- `3103fd40c560` [פתוח] P05-unbalanced-end rosh-hashanah · print/book/פרק ראשון|ארבעה ראשי שנים · סוף הפרק צולע: הפרש 22.4 מ"מ בין הטורים
- `2bca731f80a0` [פתוח] P05-unbalanced-end kiddushin · print/book/פרק ראשון|האשה נקנית · סוף הפרק צולע: הפרש 36.6 מ"מ בין הטורים
- `9f1589f6dad3` [פתוח] T01-em-dash https://xn--8dbacdxfna0hp.com/%D7%A9%D7%A2%D7%A8-%D7%94%D7%A2%D7%A8%D7%9B%D7%99%D7%9D · desktop/page,phone/page,tablet-l/page · מקף ארוך אסור בכל מקום: …ופדיית הנושאים של הזוהר הקדוש — כל ערך: הגדרה, כינוייו בזוהר…
- `e714f0cdf497` [פתוח] T01-em-dash https://xn--8dbacdxfna0hp.com/%D7%A2%D7%AA%D7%99%D7%93%D7%99%D7%9D-%D7%91%D7%9E%D7%9E%D7%9C%D7%9B%D7%AA-%D7%94%D7%96%D7%95%D7%94%D7%A8 · desktop/page,phone/page,tablet-l/page · מקף ארוך אסור בכל מקום: …הר שמצטרפים לממלכת הזוהר בקרוב— לפי קטגוריה. לחצו על קטגוריה…
- `740d512e6af9` [פתוח] T01-em-dash https://xn--8dbacdxfna0hp.com/%D7%A2%D7%AA%D7%99%D7%93%D7%99%D7%9D-%D7%91%D7%9E%D7%9E%D7%9C%D7%9B%D7%AA-%D7%94%D7%96%D7%95%D7%94%D7%A8 · desktop/page,phone/page,tablet-l/page · מקף ארוך אסור בכל מקום: …לעורכים: כל שם ברשימה — מיקום להכנסת המפרש בפועל . ע…
- `2a3c91a33d01` [פתוח] T01-em-dash https://xn--8dbacdxfna0hp.com/%D7%96%D7%95%D7%94%D7%A8 · desktop/page,phone/page,tablet-l/page · מקף ארוך אסור בכל מקום: …הטקסטים שבאתר — ההגהה, הניקוד, הפיסוק, התרגו…
- `d1a82921aed4` [פתוח] T01-em-dash https://xn--8dbacdxfna0hp.com/%D7%96%D7%95%D7%94%D7%A8 · desktop/page,phone/page,tablet-l/page · מקף ארוך אסור בכל מקום: …או הפצה? אין כאן סירוב עקרוני — פנה אלינו ונשמח לסייע בדרך ה…
- `aa594375d7db` [פתוח] E01-console https://xn--8dbacdxfna0hp.com/%D7%96%D7%95%D7%94%D7%A8-%D7%91%D7%92%D7%A8%D7%A1%D7%90 · desktop/page,phone/page,tablet-l/page · console.error: Failed to load resource: the server responded with a status of 403 ()
- `e751237be987` [פתוח] E01-console https://xn--8dbacdxfna0hp.com/%D7%96%D7%95%D7%94%D7%A8-%D7%A8%D7%91%D7%90 · desktop/page,phone/page,tablet-l/page · console.error: Failed to load resource: the server responded with a status of 403 ()
- `add2d718b55e` [פתוח] E01-console https://xn--8dbacdxfna0hp.com/%D7%A8%D7%96%D7%90-%D7%93%D7%A4%D7%A8%D7%A9%D7%AA%D7%90 · desktop/page,phone/page,tablet-l/page · console.error: Failed to load resource: the server responded with a status of 403 ()
- `ad10ebfc1a0c` [פתוח] E01-console https://xn--8dbacdxfna0hp.com/chumash-rashbi · desktop/page,phone/page,tablet-l/page · console.error: Failed to load resource: the server responded with a status of 403 ()
- `ae229d84f820` [פתוח] E01-console https://xn--8dbacdxfna0hp.com/%D7%93%D7%A3-%D7%99%D7%95%D7%9E%D7%99 · desktop/page,phone/page,tablet-l/page · console.error: Failed to load resource: the server responded with a status of 403 ()
- `f1979bb62af0` [פתוח] G02-offscreen bava-batra · tablet-l/book,tablet-l/flow,tablet-p/book · אלמנט חורג מרוחב המסך: sheet
- `39d72443ddd8` [פתוח] G02-offscreen bava-batra · tablet-l/book,tablet-l/flow,tablet-p/book · אלמנט חורג מרוחב המסך: shhd
- `e75231a7fcbb` [פתוח] G02-offscreen bava-batra · tablet-p/book · אלמנט חורג מרוחב המסך: nm
- `391078f0166a` [פתוח] G02-offscreen bava-batra · tablet-l/book,tablet-l/flow,tablet-p/book · אלמנט חורג מרוחב המסך: df
- `70938214710e` [פתוח] G02-offscreen bava-batra · tablet-l/book,tablet-l/flow,tablet-p/book · אלמנט חורג מרוחב המסך: shbody
- `a35b35cd8234` [פתוח] L02-shone-kan bekhorot · desktop/book,desktop/flow,phone/flow · "שאני כאן" ולא "שונה כאן": … לאכלה אמרה התורה ולא לשריפה! שונה כאן, שכתוב לדורותיכם.…
- `00da2539fc8b` [פתוח] L03-yesh-beineihem shabbat · desktop/book,desktop/flow,phone/flow · "נפק"מ" ולא "יש ביניהם": …יאמרו טבילה בת יומא עולה לה. ויש ביניהם: כשריסקם לגמרי.…
- `914b8407f582` [פתוח] L03-yesh-beineihem eruvin · desktop/book,desktop/flow,phone/flow · "נפק"מ" ולא "יש ביניהם": …• ולא כת"ק ויש ביניהם דרב אחלי דבעי ארבעה …
- `aafdd6e8b857` [פתוח] L03-yesh-beineihem eruvin · desktop/book,desktop/flow,phone/flow · "נפק"מ" ולא "יש ביניהם": …לר"י: חוץ מפרשת סוטה שבמקדש. ויש ביניהם למחוק לה מן התורה. •…
- `4d8cb3ed9cb0` [פתוח] L03-yesh-beineihem eruvin · desktop/book,desktop/flow,phone/flow · "נפק"מ" ולא "יש ביניהם": …שני דברים. היינו תנא ראשון. - יש ביניהם יחיד בישוב.…
- `7c0ee0fced7a` [פתוח] L03-yesh-beineihem eruvin · desktop/flow,wide/flow · "נפק"מ" ולא "יש ביניהם": …טלין בתוכה. ולא רבי יוסי היא דיש ביניהם ריבועא דריבעוה רבנן.…
- `fcd1daa4d071` [פתוח] L04-shaninu-sham shabbat · desktop/book,desktop/flow,phone/flow · "תנן שם"/"תנא שם" ולא "שנינו שם": …ששנינו שם: 'שבועות שתים שהן ארב…
- `353e532e064e` [פתוח] L05-peliga bava-metzia · desktop/book,desktop/flow,phone/flow · "חלקו/חולק" במקום פליגא/פלגו: …ר שכתבו צריך לקיימו, ואי מקיים פליג, ואי לא מקיים לא דחספא ב…
- `f12ce292d84e` [פתוח] L05-peliga makkot · desktop/book,desktop/flow,phone/flow · "חלקו/חולק" במקום פליגא/פלגו: …א תני חסר קורטוב ברישא, וריב"נ פליג - אסיפא ורב כדברי הכל?…
- `169f9a56dd72` [פתוח] L05-peliga makkot · desktop/book,desktop/flow,phone/flow · "חלקו/חולק" במקום פליגא/פלגו: … חסר קורטוב ברישא, ורי"ו אסיפא פליג, ורב דאמר כדברי הכל.…
- `179fc28ebba7` [פתוח] L05-peliga temurah · desktop/book,desktop/flow,phone/flow · "חלקו/חולק" במקום פליגא/פלגו: …ך וחלל שלה נבילה רבא כר"א ור"ש פליג…
- `6c266c892ba4` [פתוח] L05-peliga temurah · desktop/flow,wide/flow · "חלקו/חולק" במקום פליגא/פלגו: … והא יוסף בן יועזר גופו מיפליג פליג בסמיכה! כי איפליג בה - ב…
- `d8e82ab898fb` [פתוח] L13-side-long bava-batra · desktop/book,desktop/flow,phone/flow · כותרת צד ארוכה מ-3 מילים: יא. הוא היה אומר,
- `b9f35ad12cf8` [פתוח] L13-side-long bava-batra · desktop/book,desktop/flow,phone/flow · כותרת צד ארוכה מ-3 מילים: - תנאי היא: א. ר"א
- `8175f174b98f` [פתוח] L13-side-long beitzah · desktop/book,desktop/flow,phone/flow · כותרת צד ארוכה מ-3 מילים: רב יוסף: לא כרי"צ
- `7155367ff2a5` [פתוח] L13-side-long beitzah · desktop/book,desktop/flow,phone/flow · כותרת צד ארוכה מ-3 מילים: רבינא ישב לפני ר"א
- `50cef437ee80` [פתוח] L13-side-long beitzah · desktop/book,desktop/flow,phone/flow · כותרת צד ארוכה מ-3 מילים: ב. רב יוסף ה"ק
- `b868d1d1b8e7` [פתוח] L15-side-two-lines sukkah · wide/flow · כותרת צד נשברת לשתי שורות: א. לריה"ג: א. רבב"ח מרי"ו: א. מרי"ו
- `25aa9cf2fc1b` [פתוח] L16-side-repeat sukkah · wide/flow · הטקסט חוזר על כותרת הצד: ת"ר
- `c48f9858a972` [פתוח] L18-heading-no-space bava-batra · desktop/book,desktop/flow,phone/flow · כותרת בלי רווח לפניה: 'ובנות ילדו להם' - רביה או מריבה לרי"ו: 
- `e6ffc48c1ece` [פתוח] L18-heading-no-space berakhot · desktop/book,desktop/flow,phone/flow · כותרת בלי רווח לפניה: אמר שלמה כנגד דוד אביו, שדר בחמשה עולמים
- `16c24c31ff58` [פתוח] L18-heading-no-space bava-batra · desktop/book,desktop/flow,phone/flow · כותרת בלי רווח לפניה: 'בִּרְכַּת אֹבֵד עָלַי תָּבֹא' - גוזל שד
- `3ce4eab36c84` [פתוח] L18-heading-no-space bava-batra · wide/flow · כותרת בלי רווח לפניה: א"כ היה לו לשנות 'חצר אחרת - מותר'! אלא 
- `1bc88ec00bec` [פתוח] L18-heading-no-space bava-batra · wide/flow · כותרת בלי רווח לפניה: מלמדי תינוקות - הולכתם, מספרם והחלפתם
- `9e2b9f104d33` [פתוח] P07-engine-warn berakhot · print/a4lg/פרק ראשון|מאמתי,print/a4lg/פרק שני|היה קורא,print/b5lg/פרק ראשון|מאמתי · 30 תוספות שטקסט העוגן שלהן אינו נמצא עוד בדף (הטקסט נערך אחרי העיגון), והוצמדו בפרק שלהן: ד', ה', י', י"א, י"ב, י"ג, י"ח, כ', כ"ד, כ"ה, כ"ו, כ"ז, כ"ח,
- `7db0f843b384` [פתוח] P07-engine-warn berakhot · print/a4lg/פרק ראשון|מאמתי,print/b5lg/פרק ראשון|מאמתי,print/book/פרק ראשון|מאמתי · גובה פסקה אינו כפולה של גובה השורה (u): 8.27 (ב:, יחידה 35)
- `289a38eb36c1` [פתוח] P07-engine-warn berakhot · print/a4lg/פרק ראשון|מאמתי,print/b5lg/פרק ראשון|מאמתי,print/book/פרק ראשון|מאמתי · גובה פסקה אינו כפולה של גובה השורה (m): 10.21 (י:, יחידה 725)
- `a1c15b30fb33` [פתוח] P07-engine-warn berakhot · print/a4lg/פרק שני|היה קורא,print/b5lg/פרק שני|היה קורא · גובה פסקה אינו כפולה של גובה השורה (m): 5.27 (יג., יחידה 900)
- `5ef039353365` [פתוח] P07-engine-warn berakhot · print/a4lg/פרק שני|היה קורא,print/b5lg/פרק שני|היה קורא · גובה פסקה אינו כפולה של גובה השורה (u): 13.32 (יג:, יחידה 944)
- `e9961798a2e6` [פתוח] T03-latin https://xn--8dbacdxfna0hp.com/%D7%90%D7%95%D7%93%D7%95%D7%AA · phone/page · אותיות לועזיות בגוף הטקסט: …ו" אפשר להכיר באתר אור הרשבי: or-harashby.org…
- `1c1493af50c1` [פתוח] T03-latin https://nach.leokmei.com/about · desktop/page,phone/page,tablet-l/page · אותיות לועזיות בגוף הטקסט: …י, נשמח לשמוע ולתקן: M7654301@gmail.com.…
- `25d6c0f8cd02` [פתוח] T06-gregorian bava-batra · desktop/book,desktop/flow,phone/flow · תאריך לועזי (רק תאריכים עבריים): …אית? א"ל: עולם הפוך ראיתי - עליונים למטה ותחתונים למעלה. א"ל…
- `efb36165a914` [פתוח] T06-gregorian berakhot · desktop/book,desktop/flow,phone/flow · תאריך לועזי (רק תאריכים עבריים): …ר"מ ביקש על בריונים שבשכנותו שציערוהו - שימו…
- `8590b8938314` [פתוח] T06-gregorian beitzah · desktop/book,desktop/flow,phone/flow · תאריך לועזי (רק תאריכים עבריים): …חלפי תרדין, וקלחי כרוב, ודלעת יונית. ר"ע: אף ככרות בעה"ב.…
- `cca10d17419f` [פתוח] T06-gregorian bava-batra · wide/flow · תאריך לועזי (רק תאריכים עבריים): … יותר? והרי אין פורסין נשבין ליונים אלא רחוק מן הישוב שלשים …
- `b6ea9539db7c` [פתוח] T06-gregorian bava-batra · wide/flow · תאריך לועזי (רק תאריכים עבריים): …: מעופפות הרבה, אבל כרסן [של היונים] מתמלא בחמשים אמה, ומעופ…
- `0fcfb13ab574` [פתוח] T11-final-letter-mid beitzah · desktop/book,desktop/flow,phone/flow · אות סופית באמצע מילה: …ן אצל בהמה, ובהמה אצל טבח וסכיןולא תבלין ומדוך אצל מדוכה, ומ…
- `d63b443737d4` [פתוח] T11-final-letter-mid rosh-hashanah · desktop/book,desktop/flow,phone/flow · אות סופית באמצע מילה: …אש, אבל שלמה המלך שעשה שורה מעץעשאה מלמעלה, והשקיעה בבנין וס…
- `9d35fd605c47` [פתוח] T11-final-letter-mid sukkah · desktop/book,desktop/flow,phone/flow · אות סופית באמצע מילה: …שוי וכן תל אן ולא פסקן, רב עמרםחסיד אבשם רחב"א בשם רב פסיקתן…
- `71a6b08159de` [פתוח] T11-final-letter-mid sukkah · wide/flow · אות סופית באמצע מילה: …אביי:תשבוכעיןתדורו, רב:א:פרצהקוראתלגנב, ונ…
- `d52bd8c38f7a` [פתוח] T11-final-letter-mid kiddushin · desktop/book,desktop/flow,phone/flow · אות סופית באמצע מילה: …י את לעצמך' לאשתו - האם גירושיןלמלאכה אמר לה, או לגמרי?…
- `891fd140dbff` [פתוח] G04-tap-small bava-batra · phone/btn:בחירת מסכת או דף,phone/btn:דף קודם,phone/btn:חזרה מהירה · כפתור קטן מדי למגע (25x11): פרק א, משנה א
- `60ab5a878c0d` [פתוח] G04-tap-small bava-batra · phone/btn:בחירת מסכת או דף,phone/btn:דף קודם,phone/btn:חזרה מהירה · כפתור קטן מדי למגע (15x15): הזוהר על סוגיא זו
- `12d48ea6d947` [פתוח] G04-tap-small bava-batra · phone/btn:דף קודם,phone/btn:חזרה מהירה,phone/btn:חיפוש · כפתור קטן מדי למגע (40x19): פרק א, משנה ג
- `0b395bd0ff64` [פתוח] G04-tap-small bava-batra · phone/btn:דף קודם,phone/btn:חזרה מהירה,phone/btn:חיפוש · כפתור קטן מדי למגע (42x19): פרק א, משנה ד
- `5a78065705e5` [פתוח] G04-tap-small bava-batra · tablet-l/book,tablet-l/flow,tablet-p/book · כפתור קטן מדי למגע (42x19): פרק א, משנה ה
- `9fd771165a5c` [פתוח] L20-pasuk-color bava-batra · desktop/book,desktop/flow,phone/flow · פסוק לא בשחור: rgb(46, 63, 107)
- `8d4dd1f6e025` [פתוח] L20-pasuk-color berakhot · desktop/book,desktop/flow,phone/flow · פסוק לא בשחור: rgb(46, 63, 107)
- `c6ec38a9f3de` [פתוח] L20-pasuk-color beitzah · desktop/book,desktop/flow,phone/flow · פסוק לא בשחור: rgb(46, 63, 107)
- `8ef2b5d6f24a` [פתוח] L20-pasuk-color yevamot · desktop/book,desktop/flow,phone/flow · פסוק לא בשחור: rgb(46, 63, 107)
- `51b161060f56` [פתוח] L20-pasuk-color bava-metzia · desktop/book,desktop/flow,phone/flow · פסוק לא בשחור: rgb(46, 63, 107)
- `3ae636150f74` [פתוח] T08-space-before-punct berakhot · desktop/flow,wide/flow · רווח לפני סימן פיסוק: …ש צריכה כוונה, ד'שמע' - כ'הסכת' , ובראש האילן אינו מכוון!…
- `97173d51188b` [פתוח] T08-space-before-punct yevamot · desktop/book,desktop/flow,phone/flow · רווח לפני סימן פיסוק: …ול וימות, קטנה - מבת י"א עד י"ב , פחות מכאן או יותר - משמשת …
- `1b8a385518c9` [פתוח] T08-space-before-punct rosh-hashanah · desktop/book,desktop/flow,phone/flow · רווח לפני סימן פיסוק: …ן מלאין - בה', שניהן חסרין -בז' , אחד מלא ואחד חסר - בו'.…
- `fb6c36b9b547` [פתוח] T08-space-before-punct temurah · desktop/book,desktop/flow,phone/flow · רווח לפני סימן פיסוק: …ה לאיש לכל עונשין שבתורה! הוצרך , מהו דתאמר ה"מ עונש דשוה בי…
- `be3dd75e0b8f` [פתוח] T08-space-before-punct temurah · desktop/book,desktop/flow,phone/flow · רווח לפני סימן פיסוק: …תרם - תרומתו תרומה. ומשמע שמאלו , תיובתא דרבא - א"ל רבא שאני…
