#!/bin/bash
# rebuild_all.sh <קלט.docx> <פלט.docx>: מחיל מחדש את כל ההחלטות השמורות (ב, ג) על קובץ ורד עדכני.
# שלבים: 0 קבלת ממתינים בטווח, 1 מכני, ב, ג. כל השלבים מבוססי טקסט, ולכן ניתנים להחלה על כל גרסה.
set -e
U=C:/Users/Owner/leokmei-bkh-work
H="$(cd "$(dirname "$0")" && pwd)"
IN="$1"; OUT="$2"
cd "$H"
export PYTHONIOENCODING=utf-8
uv run --with lxml python stage0_accept.py "$IN" $U/out/r0.docx $U/out/r0.learn.json
uv run --with lxml python stage1_mech.py $U/out/r0.docx $U/out/r1.docx $U/out/r1.log.json | tail -3
BARGS=""; for i in 01 02 03 04 05 06 07 08 09 10 11; do BARGS="$BARGS $U/units/d$i/b-out.json"; done
uv run --with lxml python apply_ops.py b $U/out/r1.docx $U/out/r2.docx $BARGS | tail -4
CARGS=""
for i in 01 02 03 04 05 06 07 08 09 10 11; do
  if [ "$i" = "01" ]; then d="units_pilot"; else d="units_c"; fi
  if [ -f "/c/Users/Owner/leokmei-bkh-work/$d/d$i/c-final.json" ]; then f="c-final.json"; else f="c-out.json"; fi
  CARGS="$CARGS $U/$d/d$i/$f"
done
rm -f $U/out/alts-raw.json
uv run --with lxml python apply_ops.py c $U/out/r2.docx "$OUT" $CARGS --alts $U/out/alts-raw.json | tail -14
