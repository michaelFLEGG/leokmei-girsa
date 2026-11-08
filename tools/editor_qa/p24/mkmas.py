# -*- coding: utf-8 -*-
"""מרכיב את mas.js מקוד המקור בלי נתונים (לבדיקת העורך בלבד). פלט: נתיב בארגומנט."""
import ast, io, os, sys
root = sys.argv[1]; out = sys.argv[2]
fp = os.path.join(root, 'tools', 'build_site.py')
src = io.open(fp, encoding='utf-8').read()
tree = ast.parse(src)
fn = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'build'][0]
JS = None; asm = []
for st in fn.body:
    if isinstance(st, ast.Assign) and any(getattr(t, 'id', '') == 'JS' for t in st.targets):
        if JS is None and isinstance(st.value, ast.Constant):
            JS = st.value.value
        elif JS is not None:
            asm.append(ast.get_source_segment(src, st))
    if isinstance(st, ast.Assign) and any(getattr(t, 'id', '') == '_SHARED_BODY' for t in st.targets):
        asm.append(ast.get_source_segment(src, st)); break
    if isinstance(st, ast.Assign) and any(getattr(t, 'id', '') == '_td' for t in st.targets):
        asm.append(ast.get_source_segment(src, st))
ns = {'JS': JS, 'io': io, 'os': os, '__file__': fp, 'chr': chr}
for a in asm:
    exec(a, ns)
io.open(out, 'wb').write((ns['_SHARED_BODY'] + chr(10)).encode('utf-8'))
print(len(ns['_SHARED_BODY']), 'chars ->', out, '| steps', len(asm))
