#!/bin/bash
# העלאת תמונות צורת הדף של מסכת (או כמה) לדלי R2 המוגן: tools/tzura/upload_r2.sh sukkah beitzah
# דורש wrangler מחובר (OAuth) בחשבון. התמונות אינן באתר ואינן במאגר: _work/tzura/assets/<slug>/
cd "$(dirname "$0")/../../worker/leokmei-suggest" || exit 1
ASSETS="$(cd ../../_work/tzura/assets && pwd)"
for slug in "$@"; do
  find "$ASSETS/$slug" -name '*.webp' | sort | xargs -P 6 -I{} sh -c '
    f="{}"; k="'"$slug"'/$(basename "$f")"
    for try in 1 2 3; do
      npx --yes wrangler r2 object put "leokmei-tzura/$k" --file "$f" --content-type image/webp --remote >/dev/null 2>&1 && { echo "ok $k"; exit 0; }
      sleep 2
    done
    echo "FAIL $k"'
done
