# -*- coding: utf-8 -*-
"""run_mech_stage.py <מסכת> - איחוד סגנונות (s1) ואחריו המנוע המכני (s2) על קובץ המסכת מ-docx/.
כותב ל-stage/<מסכת>.s1.docx ול-stage/<מסכת>.s2.docx, ויומן ל-stage/<מסכת>.mech.log. אינו נוגע בשום דבר אחר."""
import sys, os, subprocess, time, io, datetime
M = sys.argv[1]
W = r'C:\Users\Owner\leokmei-nine-work'
WT = r'C:\Users\Owner\leokmei-girsa-nine'
GOLD = r'C:\Users\Owner\Desktop\שיננא לHTML\חולין לקלוד שיננא.docx'
src = os.path.join(W, 'docx', M + '.docx')
s1 = os.path.join(W, 'stage', M + '.s1.docx')
s2 = os.path.join(W, 'stage', M + '.s2.docx')
log = io.open(os.path.join(W, 'stage', M + '.mech.log'), 'w', encoding='utf-8')
def say(*a):
    log.write(' '.join(str(x) for x in a) + '\n'); log.flush()
say('התחלה', datetime.datetime.now().isoformat())
if not os.path.exists(s1):
    r = subprocess.run([sys.executable, os.path.join(WT, 'tools', 'unify_styles.py'), src, GOLD, s1], capture_output=True, text=True, encoding='utf-8')
    say(r.stdout, r.stderr)
    if r.returncode: say('נכשל איחוד'); sys.exit(1)
t = time.time()
r = subprocess.run([sys.executable, '_run_mech_nine.py', s1, s2], cwd=os.path.join(WT, 'engine', 'laukmi-engine'),
                   capture_output=True, text=True, encoding='utf-8')
say(r.stdout, r.stderr)
say('סיום', 'קוד', r.returncode, 'שניות', int(time.time() - t))
