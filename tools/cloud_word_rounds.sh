#!/usr/bin/env bash
# הוורד בענן בקבוצות (פרומפט 44, 16.11.2026). רץ בפעולת word-cloud.yml.
# כל קבוצה: cloud_word.py בתקציב זמן (השער רץ בתוכו), שמירה ודחיפה, מצבות בשרת.
# קוד 3 מן הכלי = הקבוצה נשמרה ויש עוד בתור. ריצה שנקטעת מאבדת לכל היותר קבוצה אחת.
# משתנים: CW_TOTAL (דקות לכל הריצה, ברירת מחדל 50), CW_BUDGET (דקות החלה לקבוצה, 25).
set -u
TOTAL=$(( ${CW_TOTAL:-50} * 60 ))
BUDGET=${CW_BUDGET:-25}
START=$(date +%s)
code=0
git config user.name "leokmei-watcher"
git config user.email "watcher@users.noreply.github.com"

save() {
  git add input/docx data/edits data/word-cloud
  if git diff --cached --quiet; then echo "אין שינוי"; return 0; fi
  git commit -q -m "הוורד בענן: עריכות האתר נכתבו לוורד [skip ci]"
  for i in 1 2 3 4; do
    if git push -q; then return 0; fi
    git pull -q --rebase --autostash origin main || { git rebase --abort 2>/dev/null || true; break; }
    sleep $((i*3))
  done
  echo "::error::הוורד והשכבה לא נדחפו. הסבב הבא יקלוט מחדש; שום עריכה לא נמחקה מן השרת."
  return 1
}

round=0
while true; do
  round=$((round+1))
  left=$(( (TOTAL - ($(date +%s) - START)) / 60 ))
  b=$BUDGET
  # הבנייה והשער שאחרי ההחלה לוקחים זמן משלהם: משאירים להם מקום
  if [ $((left - 12)) -lt "$b" ]; then b=$((left - 12)); fi
  if [ "$b" -lt 3 ]; then echo "אין זמן לקבוצה נוספת בריצה הזו. הריצה הבאה תמשיך."; break; fi
  echo "=== קבוצה $round (עד $b דקות החלה, נשארו $left דקות לריצה)"
  python tools/cloud_word.py --budget "$b"
  rc=$?
  save || { code=1; break; }
  python tools/cloud_word.py --tombstones || true
  if [ $rc -eq 3 ]; then continue; fi
  code=$rc
  break
done
echo "code=$code" >> "${GITHUB_OUTPUT:-/dev/null}"
exit 0
