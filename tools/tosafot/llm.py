# -*- coding: utf-8 -*-
"""llm.py - קריאה ישירה וחד-פעמית למודל דרך `claude -p`, בלי כלים, בלי גישה לריפו ובלי הקשר שיחה.

זהו הצינור היחיד שדרכו רצים המנועים והמבקר, ולכן הוא זהה בניסוי ובפס הייצור העתידי.
אין מפתח ואין הקלדת מפתח: משתמשים רק במה שכבר קיים בסביבה (התחברות הענן, או ANTHROPIC_API_KEY אם קיים).
החזרה: {'text','in','out','think','ms','cost','model'} - הטוקנים כוללים מטמון פרומפט (קריאה ויצירה).
"""
import os, json, subprocess, tempfile, time

EMPTY = os.path.join(tempfile.gettempdir(), 'tos-llm-empty')


def call(model, system, user, thinking=0, effort=None, timeout=1200):
    """thinking=0: בלי חשיבה מורחבת. thinking=N: תקציב חשיבה של N טוקנים (למנוע החמישי בלבד).
    effort: רמת המאמץ של ה-CLI (low/medium/high/xhigh/max). נמדד ב-12.10.2026: אופוס 5.5 חושב מעצמו (240 עד 420 טוקני חשיבה לבקשה)
    גם כש-MAX_THINKING_TOKENS=0, ו---effort low מכבה זאת; בסונט 5.5 חשיבה נדלקת רק ב---effort max."""
    os.makedirs(EMPTY, exist_ok=True)
    env = dict(os.environ)
    env['MAX_THINKING_TOKENS'] = str(thinking)
    cmd = ['claude', '-p', '--model', model, '--output-format', 'json', '--tools', '', '--no-session-persistence',
           '--disable-slash-commands', '--strict-mcp-config', '--setting-sources', '', '--system-prompt', system]
    if effort:
        cmd += ['--effort', effort]
    t0 = time.time()
    r = subprocess.run(cmd, input=user, capture_output=True, text=True, cwd=EMPTY, env=env, timeout=timeout)
    ms = int((time.time() - t0) * 1000)
    if r.returncode != 0:
        raise RuntimeError('claude -p נכשל (%s): %s' % (r.returncode, (r.stderr or r.stdout)[:400]))
    j = json.loads(r.stdout)
    if j.get('is_error'):
        raise RuntimeError('claude -p החזיר שגיאה: %s' % str(j.get('result'))[:400])
    u = j.get('usage') or {}
    tin = (u.get('input_tokens') or 0) + (u.get('cache_creation_input_tokens') or 0) + (u.get('cache_read_input_tokens') or 0)
    th = ((u.get('output_tokens_details') or {}).get('thinking_tokens')) or 0
    return {'text': j.get('result') or '', 'in': tin, 'out': u.get('output_tokens') or 0, 'think': th, 'ms': ms,
            'cost': j.get('total_cost_usd'), 'model': model, 'raw_usage': u}
