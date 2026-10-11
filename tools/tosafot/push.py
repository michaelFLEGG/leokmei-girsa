# -*- coding: utf-8 -*-
"""push.py - מעלה לנקודת הקליטה את חמש הנוסחאות של כל תוספות (למסך הבחירה של המנהל באתר).

הנוסחאות אינן נכנסות לאתר הציבורי: האתר מושך אותן מ-/tos?adm=1 רק אחרי שהמכשיר הוכר כמנהל.
העלאה מחליפה את הנוסחאות, ואינה נוגעת בבחירות ובהערות שכבר נעשו.

    uv run python tools/tosafot/push.py kiddushin 1
"""
import os, sys, json, io
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'bakara'))
import _api


def main():
    slug, perek = sys.argv[1], int(sys.argv[2])
    d = os.path.join(ROOT, 'tosafot', slug)
    count = json.load(io.open(os.path.join(d, 'count-%d.json' % perek), encoding='utf-8'))
    styles = json.load(io.open(os.path.join(d, 'styles-%d.json' % perek), encoding='utf-8'))
    dh = {str(r['n']): r['dh'] for r in count['items']}
    body = {}
    for k, s in styles.items():
        o = {x: s[x] for x in 'abcde'}
        o['dh'] = dh.get(k, '')
        body[k] = o
    r = _api.call('/tos', 'PUT', {'slug': slug, 'styles': body})
    print('הועלו נוסחאות ל-%d תוספות' % r.get('n', 0))


if __name__ == '__main__':
    main()
