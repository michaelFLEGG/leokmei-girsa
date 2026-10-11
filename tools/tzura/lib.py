# -*- coding: utf-8 -*-
"""כלי משותף: חילוץ מילים עם מיקום מ-PDF צורת הדף, ויישור מול נוסח הגמרא שבקובץ המקורות."""
import re, json, difflib, unicodedata, fitz

NIK = re.compile('[\u0591-\u05c7]')
FINAL = str.maketrans('ךםןףץ', 'כמנפצ')

def key(w):
    w = NIK.sub('', w)
    w = re.sub(r'[^\u05d0-\u05ea]', '', w).translate(FINAL)
    return w
def skel(w):
    """שלד עיצורי: בלי ו/י, כדי לספוג הבדלי כתיב מלא/חסר"""
    return key(w).replace('ו', '').replace('י', '')

def page_words(page):
    """כל המילים בעמוד: [(text,x0,y0,x1,y1,size,font)] מתוך תווים (rawdict)."""
    out = []
    rd = page.get_text("rawdict")
    for b in rd["blocks"]:
        for l in b.get("lines", []):
            for s in l["spans"]:
                cur = []; 
                def flush():
                    if cur:
                        t = ''.join(c[0] for c in cur)
                        x0 = min(c[1] for c in cur); y0 = min(c[2] for c in cur)
                        x1 = max(c[3] for c in cur); y1 = max(c[4] for c in cur)
                        out.append((t, x0, y0, x1, y1, s["size"], s["font"]))
                        cur.clear()
                for ch in s["chars"]:
                    c = ch["c"]
                    if c.isspace():
                        flush()
                    else:
                        bb = ch["bbox"]; cur.append((c, bb[0], bb[1], bb[2], bb[3]))
                flush()
    return out

def seg_words(html):
    t = re.sub(r'<sup[^>]*>.*?</sup>', ' ', html or '', flags=re.S)
    t = re.sub(r'<i class="footnote".*?</i>', ' ', t, flags=re.S)
    t = re.sub(r'<[^>]+>', ' ', t)
    t = t.replace('&nbsp;', ' ').replace('&thinsp;', ' ').replace('\u05be', ' ')
    return [w for w in t.split() if key(w)]
