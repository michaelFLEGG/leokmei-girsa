# -*- coding: utf-8 -*-
"""bakara_all.py [מסכת ...] - ממצאי Claude + שכבת הקוד של הבקרה לכל פרקי המסכתות, לקובצי data/bakara (בלי העלאה)."""
import sys, os, re, subprocess, io
W = r'C:\Users\Owner\leokmei-nine-work'; G = r'C:\Users\Owner\leokmei-girsa-nine'
MAP = {'ערכין': 'arakhin', 'תמורה': 'temurah', 'כריתות': 'keritot', 'מעילה': 'meilah', 'נדה': 'niddah', 'זבחים': 'zevachim',
       'מנחות': 'menachot', 'עירובין': 'eruvin', 'שבת': 'shabbat'}
names = sys.argv[1:] or list(MAP)
env = dict(os.environ, LG_DRIVE=os.path.join(W, 'fullbuild', 'docx'), LG_DOCX=os.path.join(W, 'fullbuild', 'docx'), PYTHONIOENCODING='utf-8')
log = io.open(os.path.join(W, 'bakara-run.log'), 'a', encoding='utf-8')
for m in names:
    s = MAP[m]
    r = subprocess.run([sys.executable, os.path.join(W, 'claude_findings.py'), m, s], capture_output=True, text=True, encoding='utf-8', env=env)
    last = (r.stdout.strip().splitlines() or [''])[-1]
    log.write(last + '\n'); log.flush()
    mm = re.search(r'פרקים (\d+)', last)
    if not mm:
        log.write('נכשל claude_findings %s: %s\n' % (m, r.stderr[-300:])); continue
    for c in range(1, int(mm.group(1)) + 1):
        r = subprocess.run([sys.executable, '-W', 'ignore', os.path.join(G, 'tools', 'bakara', 'run.py'), s, str(c), '--no-sync', '--no-push', '--force-code-only'],
                           capture_output=True, text=True, encoding='utf-8', env=env, cwd=G)
        ok = [l for l in r.stdout.splitlines() if l.startswith('נכתב')]
        log.write('%s-%d: %s\n' % (s, c, ok[0] if ok else ('ERR ' + r.stderr[-200:])))
        log.flush()
log.write('סיום\n'); log.close()
