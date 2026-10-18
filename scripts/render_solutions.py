"""Typeset unofficial worked solutions for one exam and attach them to its questions.
Usage (from the repo root): python3 scripts/render_solutions.py . <exam_id>
Reads solutions/<exam_id>.json ({problem number: LaTeX body}). Needs Docker and a local image with
pdflatex, built once with:
    printf 'FROM alpine:3.20\nRUN apk add --no-cache texlive texmf-dist-latexextra texmf-dist-fontsrecommended texmf-dist-mathscience\n' | docker build -t uwmf-tex -
Writes:
- questions/<qid>_ans.png for each solved question, with answer_unofficial: true
- if the exam has no official key, exams/<exam_id>Ans_unofficial.pdf becomes its key (answer_key_unofficial: true)"""
import json, os, subprocess, sys, shutil
import numpy as np, pymupdf
from PIL import Image
R, eid = sys.argv[1], sys.argv[2]
import tempfile
sol = json.load(open(f'{R}/solutions/{eid}.json'))
qs = json.load(open(f'{R}/questions.json')); ex = json.load(open(f'{R}/exams.json'))
e = next(x for x in ex if x['id'].lower() == eid.lower())
mine = {q['source']['problem']: q for q in qs if q['source'].get('exam_id') == eid and (not q.get('answer_image') or q.get('answer_unofficial'))}
title = f"{e['course']} {e['type']}, {e['quarter']} {e['year']}" + (f" ({e['instructor']})" if e.get('instructor') not in (None, 'Staff') and e['type'] != 'Final' else '')
pages = []
for n in sorted(mine):
    body = sol[str(n)]
    pages.append(r"""\noindent{\small\textsf{\textbf{Unofficial worked solution} --- written by UWMathFinder, not by the instructor. Spot an error? Report it on the site.}}\par\vspace{2pt}\hrule\vspace{8pt}
\noindent\textbf{%s --- Problem %d}\par\medskip
%s
""" % (title.replace('&', r'\&'), n, body))
tex = r"""\documentclass[11pt]{article}
\usepackage[paperwidth=8.5in,paperheight=14in,margin=0.6in]{geometry}
\usepackage{amsmath,amssymb}\usepackage[T1]{fontenc}\usepackage{lmodern}
\pagestyle{empty}\setlength{\parindent}{0pt}\setlength{\parskip}{4pt}
\begin{document}
""" + "\n\\newpage\n".join(pages) + "\n\\end{document}\n"
work = tempfile.mkdtemp(prefix=f'sol_{eid}_')
open(f'{work}/s.tex', 'w').write(tex)
r = subprocess.run(['docker', 'run', '--rm', '--network', 'none', '-v', f'{work}:/work', 'uwmf-tex', 'pdflatex', '-interaction=nonstopmode', '-halt-on-error', 's.tex'],
                   capture_output=True, text=True)
if r.returncode:
    print(r.stdout[-2500:]); sys.exit('LaTeX failed')
doc = pymupdf.open(f'{work}/s.pdf'); assert doc.page_count == len(mine), (doc.page_count, len(mine))
def trim(im, pad=26):
    a = np.asarray(im.convert('L')) < 200; rows = np.where(a.any(axis=1))[0]
    return im.crop((0, max(0, rows[0] - pad), im.width, min(im.height, rows[-1] + pad)))
for pg, n in zip(doc, sorted(mine)):
    p = pg.get_pixmap(dpi=150); im = trim(Image.frombytes('RGB', (p.width, p.height), p.samples))
    q = mine[n]; q['answer_image'] = f"questions/{q['id']}_ans.png"; q['answer_unofficial'] = True
    im.save(f"{R}/{q['answer_image']}", optimize=True)
if e.get('answer_key') in (None, '#') or e.get('answer_key_unofficial'):
    e['answer_key'] = f'exams/{eid}Ans_unofficial.pdf'; e['answer_key_unofficial'] = True
    shutil.copy(f'{work}/s.pdf', f"{R}/{e['answer_key']}")
for f, data in (('questions.json', qs), ('exams.json', ex)):
    with open(f'{R}/{f}', 'w') as fh: json.dump(data, fh, indent=2, ensure_ascii=False); fh.write('\n')
print(eid, 'solved', len(mine), 'problems ->', doc.page_count, 'pages')
