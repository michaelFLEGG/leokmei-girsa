# -*- coding: utf-8 -*-
"""handoff_e2e.py - בדיקה מקצה לקצה של ערכת החשבון השני על יחידה אחת (24.10.2026).

מעתיק את הערכה (gates.py, system-write.md) ואת היחידה לתיקייה נקייה מחוץ למאגר, ומריץ שם את כל השכבות בדיוק לפי
ההוראות הקבועות (kit/INSTRUCTIONS.md, ג.2), כש-gates.py רץ ב-`python -I` (בלי המאגר ובלי תלויות). במקום תת-סוכנים:
`claude -p --model <מודל>` עם אותה הנחיה שהתת-סוכן מקבל, וכלי הקריאה בלבד. עד ארבעה במקביל (כמו בהוראות, ג.3.ד).
זו הבדיקה היחידה שמותר להריץ במחשב הזה במודל, ועל יחידה אחת בלבד.

    uv run python tools/tosafot/handoff_e2e.py tosafot/handoff/units/<id>.json <תיקייה-נקייה>
"""
import os, sys, json, io, glob, shutil, subprocess, time, concurrent.futures as cf

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
KIT = os.path.join(ROOT, 'tosafot', 'handoff', 'kit')
MODEL_ID = {'sonnet': 'claude-sonnet-5-5', 'haiku': 'claude-haiku-5-5', 'fable': 'claude-fable-5-1', 'opus': 'claude-opus-5-5'}
SUB = ('קרא את הקובץ %s ובצע את מה שכתוב בו. אל תקרא שום קובץ אחר, אל תחפש ואל תפעיל כלים נוספים. '
       'החזר אך ורק JSON אחד, בלי גדרות קוד ובלי שום טקסט לפניו או אחריו.')


def gates(base, *args):
    t = time.time()
    r = subprocess.run([sys.executable, '-I', os.path.join(base, 'kit', 'gates.py')] + list(args), cwd=base,
                       capture_output=True, text=True, encoding='utf-8')
    print('  gates %s: %s (%.1fs)' % (args[0], (r.stdout or r.stderr).strip().replace('\n', ' | ')[:300], time.time() - t), flush=True)
    if r.returncode != 0:
        raise SystemExit('gates נכשל: ' + r.stderr[-1500:])
    return r.stdout


def run_job(path):
    model = io.open(path, encoding='utf-8').readline().split(':', 1)[1].strip()
    t = time.time()
    cmd = ['claude', '-p', SUB % path, '--model', MODEL_ID[model], '--tools', 'Read', '--allowedTools', 'Read',
           '--strict-mcp-config', '--no-session-persistence', '--disable-slash-commands', '--output-format', 'json']
    for attempt in range(2):
        r = subprocess.run(cmd, cwd=os.path.dirname(path), capture_output=True, text=True, encoding='utf-8')
        try:
            j = json.loads(r.stdout)
            txt = j.get('result', '')
            if txt.strip():
                break
        except Exception:
            j, txt = {}, ''
    d = os.path.dirname(path)
    name = os.path.basename(path)
    io.open(os.path.join(d, 'ans-%s.txt' % name), 'w', encoding='utf-8').write(txt)
    return {'job': name, 'model': model, 'sec': round(time.time() - t, 1), 'cost': j.get('total_cost_usd'),
            'in': (j.get('usage') or {}).get('input_tokens'), 'out': (j.get('usage') or {}).get('output_tokens'),
            'cr': (j.get('usage') or {}).get('cache_read_input_tokens'), 'ok': bool(txt.strip())}


def layer(wd, pattern, stats):
    jobs = sorted(p for p in glob.glob(os.path.join(wd, pattern)) if not os.path.exists(os.path.join(wd, 'ans-%s.txt' % os.path.basename(p))))
    t = time.time()
    with cf.ThreadPoolExecutor(4) as ex:
        for res in ex.map(run_job, jobs):
            stats['jobs'].append(res)
            print('    %s %s %ss ok=%s' % (res['job'], res['model'], res['sec'], res['ok']), flush=True)
    stats['layers'].append({'pattern': pattern, 'n': len(jobs), 'sec': round(time.time() - t, 1)})


def main():
    unit_src, base = sys.argv[1], os.path.abspath(sys.argv[2])
    uid = os.path.basename(unit_src)[:-5]
    os.makedirs(os.path.join(base, 'kit'), exist_ok=True)
    os.makedirs(os.path.join(base, 'units'), exist_ok=True)
    for f in ('gates.py', 'system-write.md', 'INSTRUCTIONS.md'):
        shutil.copy(os.path.join(KIT, f), os.path.join(base, 'kit', f))
    shutil.copy(unit_src, os.path.join(base, 'units', uid + '.json'))
    wd = 'work/%s/' % uid
    awd = os.path.join(base, 'work', uid)
    stats = {'unit': uid, 'jobs': [], 'layers': [], 'start': time.time()}
    gates(base, 'write-jobs', 'units/%s.json' % uid, wd)
    layer(awd, 'job-*.md', stats)
    gates(base, 'ingest-write', wd)
    gates(base, 'review-jobs', wd)
    layer(awd, 'rv-*.md', stats)
    gates(base, 'ingest-review', wd)
    gates(base, 'rewrite-jobs', wd)
    layer(awd, 'rw-*.md', stats)
    gates(base, 'ingest-rewrite', wd)
    gates(base, 'rereview-jobs', wd)
    layer(awd, 'rr-*.md', stats)
    gates(base, 'ingest-rereview', wd)
    gates(base, 'finalize', wd, 'out-%s.json' % uid)
    stats['sec'] = round(time.time() - stats.pop('start'), 1)
    out = json.load(io.open(os.path.join(base, 'out-%s.json' % uid), encoding='utf-8'))
    stats['result'] = {'ntos': out['ntos'], 'flagged': out['flagged'], 'engines': out['engines'],
                       'ok': sum(1 for r in out['recs'].values() if r['status'] == 'ok'),
                       'rewritten': sum(1 for r in out['recs'].values() if r['tries'] >= 2),
                       'rv_fix': sum(1 for r in out['recs'].values() if r['rv_fix']),
                       'questions': sum(len(r['q_keep']) for r in out['recs'].values()), 'cal': out['cal']}
    json.dump(stats, io.open(os.path.join(base, 'e2e-stats.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in stats.items() if k != 'jobs'}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
