# -*- coding: utf-8 -*-
"""print_pdf.py - מפיק PDF של פרק בעמוד הספר, ומודד אותו.

שער היציאה של משימה ד: כל עמוד 90x130 מ"מ, טור אחד, קצה ימני של
המסילה ב-90 מ"מ וקצה שמאלי של הטקסט ב-10. המדידה נעשית על הקובץ
שהופק בפועל, לא על ה-CSS.

  uv run --with playwright --with pypdf --with pypdfium2 python tools/print_pdf.py sukkah beitzah
"""
import os, sys, json

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MM = 72.0 / 25.4          # מ"מ לנקודות PDF


def make(slug, site, out_dir, shots=3):
    from playwright.sync_api import sync_playwright
    os.makedirs(out_dir, exist_ok=True)
    pdf = os.path.join(out_dir, 'הדפסה-%s-פרק-א.pdf' % slug)
    info = {'slug': slug, 'pdf': pdf}
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        pg = br.new_context(viewport={'width': 1400, 'height': 900}).new_page()
        pg.goto('file:///' + os.path.join(site, slug + '.html').replace(os.sep, '/'))
        pg.wait_for_timeout(1200)
        # פרק א' בלבד, בתצוגת הספר - שהיא עתה גם ההדפסה
        pg.evaluate("()=>{BOOK=true;ALL=false;SHEETS=1;render(0);}")
        pg.wait_for_timeout(2500)
        info['sheets'] = pg.evaluate("()=>document.querySelectorAll('.sheet').length")
        # המדידה בפריסת ההדפסה עצמה
        pg.emulate_media(media='print')
        pg.wait_for_timeout(400)
        info['edges'] = pg.evaluate("""()=>{
          const px2mm = 25.4/96;
          const sh=document.querySelector('.sheet'); if(!sh)return null;
          const b=sh.getBoundingClientRect();
          const rail=sh.querySelector('.rail'), main=sh.querySelector('.main');
          const r=rail.getBoundingClientRect(), m=main.getBoundingClientRect();
          return {sheetW:+(b.width*px2mm).toFixed(2), sheetH:+(b.height*px2mm).toFixed(2),
                  railRight:+((r.right-b.left)*px2mm).toFixed(2),
                  textLeft:+((m.left-b.left)*px2mm).toFixed(2),
                  textW:+(m.width*px2mm).toFixed(2)};}""")
        pg.pdf(path=pdf, prefer_css_page_size=True, print_background=True)
        br.close()
    # מדידת הקובץ עצמו
    from pypdf import PdfReader
    rd = PdfReader(pdf)
    sizes = set()
    for p in rd.pages:
        bx = p.mediabox
        sizes.add((round(float(bx.width) / MM, 1), round(float(bx.height) / MM, 1)))
    info['pages'] = len(rd.pages)
    info['sizes_mm'] = sorted(sizes)
    # צילום שלושה עמודים רצופים
    try:
        import pypdfium2 as pdfium
        doc = pdfium.PdfDocument(pdf)
        names = []
        for i in range(min(shots, len(doc))):
            im = doc[i].render(scale=4).to_pil()
            n = 'עמוד-%s-%d.png' % (slug, i + 1)
            im.save(os.path.join(out_dir, n)); names.append(n)
        info['shots'] = names
    except Exception as e:
        info['shots_error'] = str(e)
    return info


if __name__ == '__main__':
    site = os.environ.get('LG_SITE') or os.path.join(ROOT, 'site')
    out = os.environ.get('LG_REPORTS') or os.path.join(ROOT, '_שומר', 'דוחות')
    res = [make(s, site, out) for s in (sys.argv[1:] or ['sukkah'])]
    print(json.dumps(res, ensure_ascii=False, indent=1))
