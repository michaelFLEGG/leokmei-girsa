# -*- coding: utf-8 -*-
"""בדיקה אחרי ההפקה של קובץ PDF: גודל, גופנים מוטמעים, טקסט ניתן לחיפוש, תווים אסורים.
הרצה: uv run --with pymupdf python tools/print/check_pdf.py <קובץ.pdf> [--png <תיקייה> --dpi 110]"""
import argparse, json, os, re, sys

# פרומפט 48 סבב ב (16.11.2026): אות לטינית בגוף הטקסט היא תקלה (למשל קוד עיטור "F...E" סביב הדרן).
# מותרים רק כתובת האתר וקיצורים טכניים ידועים שבשער, בעמוד 2 ובתחתית.
LATIN_OK = re.compile(r'(?:https?://)?(?:www\.)?leokmei\.com\S*|\b(?:PDF|QR|B5|A4)\b', re.I)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pdf')
    ap.add_argument('--png', default='')
    ap.add_argument('--dpi', type=int, default=110)
    a = ap.parse_args()
    import fitz
    d = fitz.open(a.pdf)
    out = {'pages': len(d), 'size_mm': [round(d[0].rect.width / 72 * 25.4, 1), round(d[0].rect.height / 72 * 25.4, 1)]}
    fonts = {}
    chars = 0
    bad = {'em_dash': 0, 'en_dash': 0, 'bar': 0, 'bidi_arrow': 0}
    empty_pages = []
    latin = []
    for i, p in enumerate(d):
        t = p.get_text()
        chars += len(t)
        if not t.strip():
            empty_pages.append(i + 1)
        bad['em_dash'] += t.count('—')
        bad['en_dash'] += t.count('–')
        bad['bar'] += t.count('|') + t.count('׀')
        for w in re.findall(r'\S*[A-Za-z]\S*', LATIN_OK.sub(' ', t)):
            latin.append({'page': i + 1, 'word': w})
        for f in p.get_fonts():
            fonts[f[3]] = f[1]          # שם -> סוג; 'n/a' = לא מוטמע
        if a.png:
            os.makedirs(a.png, exist_ok=True)
            p.get_pixmap(dpi=a.dpi).save(os.path.join(a.png, 'p%03d.png' % (i + 1)))
    out['chars'] = chars
    out['fonts'] = fonts
    out['fonts_not_embedded'] = [k for k, v in fonts.items() if v in ('n/a', '') and k]
    out['empty_pages'] = empty_pages
    out['forbidden'] = bad
    out['latin'] = latin[:50]
    out['latin_count'] = len(latin)
    out['bytes'] = os.path.getsize(a.pdf)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    sys.exit(1 if (out['fonts_not_embedded'] or empty_pages or latin) else 0)


if __name__ == '__main__':
    main()
