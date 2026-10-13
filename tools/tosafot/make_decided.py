# -*- coding: utf-8 -*-
"""make_decided.py - מרכיב מהכרעות המנהל (תמונת מצב של נקודת הקליטה) את:
  tosafot/<מסכת>/decided.json        key -> הנוסח הסופי של המנהל (בחירה או עריכה). בית החרושת אינו כותב אותם מחדש.
  tosafot/factory/gold-examples.json דוגמאות הזהב לפרומפט (פנים + הנוסח הסופי), לפי רשימת מפתחות שנקבעה בניתוח.

הקלט: tosafot/<מסכת>/decisions-<תאריך>.json (תמונת מצב של /tos?adm=1: picks, notes, log) וקובצי האופציות והחשיפה של שני הסבבים.

    uv run python tools/tosafot/make_decided.py sukkah decisions-13.10.2026.json
"""
import os, sys, json, io, re
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

GOLD_KEYS = [1002, 1003, 1007, 1022, 1025, 1017, 1033, 1006, 1029, 1032, 3122, 3126, 3127, 4001, 4003, 4004, 4005, 4011, 4019]
FIXES = [("''", '"'), ('הענין', 'העין'), ("רש'י", 'רש"י')]


def jload(p):
    return json.load(io.open(p, encoding='utf-8'))


def tidy(t):
    t = t.strip()
    for a, b in FIXES:
        t = t.replace(a, b)
    return re.sub(r'\s+', ' ', t)


def rounds(d):
    out = []
    for opt, rev in (('test-options.json', 'test-reveal.json'), ('test-options-verify1.json', 'test-reveal-verify1.json')):
        po, pr = os.path.join(d, opt), os.path.join(d, rev)
        if not os.path.exists(po):
            po = os.path.join(d, 'archive', opt)
            pr = os.path.join(d, 'archive', rev)
        if os.path.exists(po) and os.path.exists(pr):
            out.append((jload(po)['items'], jload(pr)))
    return out


def main():
    slug, snap = sys.argv[1], sys.argv[2]
    d = os.path.join(ROOT, 'tosafot', slug)
    doc = jload(os.path.join(d, snap))
    picks, notes = doc['picks'], doc.get('notes', {})
    last = {str(l['n']): l for l in doc.get('log', [])}
    items, texts = {}, {}
    for opt, rev in rounds(d):
        for rid, it in opt.items():
            key = str(it['key'])
            pk = picks.get(key)
            if not pk:
                continue
            m = rev['map'][rid]
            if pk['p'] == 'custom':
                final, src = pk['t'], 'ערוך ידנית'
            else:
                eng = m.get(pk['p'])
                final, src = it['options'][pk['p']], 'נבחר: ' + str(eng)
            items[key] = {'text': final.strip(), 'source': src, 'dh': it['dh'], 'perek': it['perek'], 'n': it['n']}
            texts[key] = it
    out = {'slug': slug, 'snapshot': snap, 'note': 'הכרעות המנהל. בית החרושת אינו כותב מחדש אף אחת מהן.', 'items': items}
    with io.open(os.path.join(d, 'decided.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    gold = []
    for k in GOLD_KEYS:
        s = str(k)
        if s in items:
            gold.append({'key': k, 'dh': texts[s]['dh'], 'text': texts[s]['text'], 'line': tidy(items[s]['text'])})
    gp = os.path.join(ROOT, 'tosafot', 'factory', 'gold-examples.json')
    old = json.load(io.open(gp, encoding='utf-8')) if os.path.exists(gp) else {}
    old['tosafot'] = gold
    os.makedirs(os.path.dirname(gp), exist_ok=True)
    with io.open(gp, 'w', encoding='utf-8') as f:
        json.dump(old, f, ensure_ascii=False, indent=1)
    print('decided:', len(items), '| gold:', len(gold))


if __name__ == '__main__':
    main()
