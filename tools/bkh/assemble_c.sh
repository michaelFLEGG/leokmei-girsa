#!/bin/bash
# assemble_c.sh <out.docx> [--dry]: מחיל את כל יחידות מנוע ג (c-final אם קיים, אחרת c-out) על s2.docx
U=C:/Users/Owner/leokmei-bkh-work
ARGS=""
for i in 01 02 03 04 05 06 07 08 09 10 11; do
  if [ "$i" = "01" ]; then d="units_pilot"; else d="units_c"; fi
  if [ -f "/c/Users/Owner/leokmei-bkh-work/$d/d$i/c-final.json" ]; then f="c-final.json"; else f="c-out.json"; fi
  ARGS="$ARGS $U/$d/d$i/$f"
done
rm -f /c/Users/Owner/leokmei-bkh-work/out/alts-raw.json
cd "$(dirname "$0")"
PYTHONIOENCODING=utf-8 uv run --with lxml python apply_ops.py c "$U/out/s2.docx" "$1" $ARGS --alts "$U/out/alts-raw.json" $2
