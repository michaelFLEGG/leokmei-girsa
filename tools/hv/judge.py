# -*- coding: utf-8 -*-
"""judge.py - בדיקת דגימה בלתי תלויה של ממצאי הסקירה (מודל חזק בהקשר נקי, שלא ראה את תהליך הייצור).

    uv run --with lxml python tools/hv/judge.py <slug> <קובץ-ממצאים.json> [--out דוח.json]

לכל ממצא: הפסקה שלנו, פירוש הגמרא, וכל חבילת חברותא של העמוד (גם לממצאי בסיס שנוצרו בלעדיה, כדי שהשיפוט יהיה הוגן).
פסק: "אמיתי" (המחבר צריך להעיר/לתקן), "סביר" (סביר אך לא ודאי או שולי), "סרק" (שגוי או לא נחוץ). הפלט נשאר בריפו הפרטי.
"""
import os, sys, json, argparse, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hv_common as H
from hv_common import C
import review as R

SYS = """אתה שופט עצמאי בסקירת "לאוקמי גירסא" (קיצור הבבלי של מחבר יחיד). קיבלת ממצא שמודל הציע למחבר, ואת המקורות: הפסקה בקיצור, פירוש הגמרא, וביאור חברותא לעמוד.
פסוק: "אמיתי" = הממצא נכון והמחבר היה רוצה לדעת עליו (טעות, חסר מהותי, כותרת ראויה, הבהרה חיונית). "סביר" = נכון אך שולי או שאלה לגיטימית. "סרק" = שגוי, מבוסס על קריאה לא נכונה, או שהקיצור מקצר בכוונה, או שאין לו בסיס במקורות.
החזר JSON בלבד: {"v":"אמיתי|סביר|סרק","why":"משפט אחד"}. אל תצטט את חברותא."""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('slug')
    ap.add_argument('file')
    ap.add_argument('--out')
    a = ap.parse_args()
    rows = H.jload(a.file, [])
    src = H.jload(os.path.join(H.ROOT, 'data', 'sources', a.slug + '.json'), {}) or {}
    out, spent = [], 0.0
    for r in rows:
        if r.get('blocked'):
            continue
        pk = H.jload(os.path.join(H.CHAV, 'packs', a.slug, H.file_of_label(r['daf']) + '.json'), {})
        para = next((p['text'] for p in pk.get('paras', []) if p['i'] == r['i']), '')
        pg = (src.get('pages') or {}).get(r['daf']) or {}
        perush = '\n'.join(R.TAG.sub('', x) for x in pg.get('perush', []))[:5000]
        chav = '\n'.join('[%d] %s | %s' % (s['k'], s['gemara'][:150], s['explain'][:600]) for s in pk.get('segs', []))
        u = 'ממצא: %s\n\nהפסקה: %s\n\nפירוש הגמרא:\n%s\n\nחברותא:\n%s' % (
            json.dumps({k: r.get(k) for k in ('kind', 'mark', 'note', 'fix', 'sev', 'conf')}, ensure_ascii=False), para, perush, chav[:9000])
        x = R.call_llm('sonnet', SYS, u)
        spent += float(x.get('cost') or 0)
        try:
            j = R.extract_json(x['text'])
            j = j[0] if isinstance(j, list) and j else j
        except Exception:
            j = {'v': '?', 'why': 'פלט לא תקין'}
        out.append({'daf': r['daf'], 'i': r['i'], 'kind': r['kind'], 'v': j.get('v'), 'why': C.no_dash(str(j.get('why', '')))})
        print(r['daf'], r['kind'], '->', j.get('v'))
    cnt = {}
    for o in out:
        cnt[o['v']] = cnt.get(o['v'], 0) + 1
    res = {'n': len(out), 'counts': cnt, 'spent_usd': round(spent, 3), 'rows': out}
    H.jsave(a.out or a.file.replace('.json', '-judge.json'), res)
    print(json.dumps({k: res[k] for k in ('n', 'counts', 'spent_usd')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
