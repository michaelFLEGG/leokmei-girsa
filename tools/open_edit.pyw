# -*- coding: utf-8 -*-
"""open_edit.pyw - משגר שקט לקיצור "לאוקמי גירסא - עריכה" שבשולחן העבודה.

הקיצור הישן היה קובץ כתובת שפתח ישר את 127.0.0.1:8760. אם הגשר לא רץ
באותו רגע (אחרי הדלקת המחשב המשימה המתוזמנת מרימה אותו רק אחרי עד
שתי דקות) הדפדפן הציג דף ריק או שגיאה. המשגר הזה:

א. בודק אם הגשר חי.
ב. אם לא - מרים אותו (קודם דרך המשימה המתוזמנת, ואם לא הצליח - ישירות).
ג. ממתין עד שהוא עונה, ורק אז פותח את הדפדפן.
ד. אם נכשל בכל זאת - פותח דף מקומי בעברית שאומר מה קרה, מנסה שוב מעצמו,
   ומציע לעבור לכתובת הרגילה שבה העריכה עובדת גם בלי הגשר.

הוא רץ ב-pythonw ולכן אינו פותח חלון שחור. הקובץ יושב בתיקיית הגשר
(ב-ASCII בלבד בנתיב) ואינו תלוי בעותק-העבודה.
"""
import os, sys, io, json, time, subprocess, urllib.request, webbrowser

PORT = 8760
HOME = os.path.join(os.path.expanduser('~'), 'leokmei-gesher')
TASK = 'לאוקמי גירסא - גשר הפרסום'
PUBLIC = 'https://leokmei.com/'
LOCAL = 'http://127.0.0.1:%d/index.html' % PORT
LOG = os.path.join(HOME, 'open_edit.log')
NOWIN = 0x08000000  # CREATE_NO_WINDOW


def log(*a):
    try:
        io.open(LOG, 'a', encoding='utf-8').write(
            time.strftime('%d.%m %H:%M:%S ') + ' '.join(str(x) for x in a) + '\n')
    except Exception:
        pass


def alive():
    try:
        with urllib.request.urlopen('http://127.0.0.1:%d/shalom' % PORT, timeout=2) as r:
            return json.loads(r.read().decode('utf-8')).get('ok') is True
    except Exception:
        return False


def start_bridge():
    me = os.path.join(HOME, 'gesher.py')
    # הדרך המהירה: הרמה ישירה (כחצי שנייה). המשימה המתוזמנת היא הגיבוי -
    # הפעלתה דרך מתזמן המשימות לבדה אורכת כחמש שניות.
    pyw = os.path.join(os.path.dirname(sys.executable), 'pythonw.exe')
    if not os.path.exists(pyw):
        pyw = sys.executable
    try:
        subprocess.Popen([pyw, me, '--once'], creationflags=NOWIN | 0x00000008,
                         close_fds=True)
    except Exception as e:
        log('popen', e)
    t0 = time.time()
    while time.time() - t0 < 6:
        if alive():
            return True
        time.sleep(0.15)
    try:
        subprocess.run(['schtasks', '/Run', '/TN', TASK], capture_output=True,
                       creationflags=NOWIN, timeout=15)
    except Exception as e:
        log('schtasks', e)
    t0 = time.time()
    while time.time() - t0 < 10:
        if alive():
            return True
        time.sleep(0.3)
    return False


FALLBACK = '''<!DOCTYPE html><html lang="he" dir="rtl"><meta charset="utf-8">
<title>לאוקמי גירסא - עריכה</title>
<body style="font-family:Arial,sans-serif;background:#f1ead9;color:#2b2620;text-align:center;padding:60px 20px">
<h2>הגשר שבמחשב עדיין לא עלה</h2>
<p>אין בכך כל פגם: העריכה עובדת גם בלעדיו.</p>
<p style="margin:26px"><a href="%(pub)s" style="background:#c9a24a;color:#2b2620;padding:12px 26px;border-radius:6px;text-decoration:none;font-weight:700">פתח את האתר הרגיל לעריכה</a></p>
<p id="m" style="color:#6a6050">מנסה שוב להרים את הגשר...</p>
<script>
async function t(){try{const r=await fetch('http://127.0.0.1:%(port)d/shalom',{cache:'no-store'});
 if(r.ok){location.href='%(local)s';return}}catch(e){}
 setTimeout(t,3000)}
t();
</script></body></html>'''


def serve_inprocess():
    """מרים את הגשר בתוך התהליך של המשגר עצמו: הפעלת פייתון שנייה
    עולה כשתי שניות (נמדד), וזה מה שהחזיק את הפתיחה מעל חמש שניות.
    מחזיר את השרת, או None אם נכשל."""
    try:
        import threading
        sys.path.insert(0, HOME)
        import gesher
        gesher.LOG = os.path.join(HOME, 'gesher.log')
        srv = gesher.ThreadingHTTPServer(('127.0.0.1', PORT), gesher.H)
        srv.daemon_threads = True
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        gesher.log('הגשר עלה (מן המשגר) על 127.0.0.1:%d' % PORT)
        return srv
    except Exception as e:
        log('בתוך התהליך נכשל:', repr(e))
        return None


def main():
    srv = None
    if not alive():
        log('הגשר אינו עונה, מרים')
        srv = serve_inprocess()
        ok = (srv is not None and alive()) or start_bridge()
        log('אחרי ההרמה:', ok)
    else:
        ok = True
    if ok:
        webbrowser.open(LOCAL)
        if srv is not None:
            # התהליך הזה הוא הגשר מעכשיו, ונשאר חי כל עוד המחשב דולק
            while True:
                time.sleep(3600)
        return
    p = os.path.join(HOME, 'fallback.html')
    io.open(p, 'w', encoding='utf-8').write(
        FALLBACK % {'pub': PUBLIC, 'port': PORT, 'local': LOCAL})
    webbrowser.open('file:///' + p.replace('\\', '/'))
    # ממשיך לנסות להרים ברקע כדי שהדף המקומי יעבור מעצמו
    for _ in range(2):
        if start_bridge():
            break


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        log('שגיאה', repr(e))
