#!/usr/bin/env python3
"""Compile an existing LaTeX final project; v6.2 does not assemble old Stage-8 markdown."""
from __future__ import annotations
import argparse, shutil, subprocess
from pathlib import Path

def run(cmd: list[str], cwd: Path) -> None:
    r=subprocess.run(cmd,cwd=cwd,text=True,capture_output=True)
    if r.returncode:
        print(r.stdout); print(r.stderr); raise SystemExit(r.returncode)

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('project',nargs='?',default='final_latex')
    ap.add_argument('--main',default=None,help='main tex filename; autodetect if omitted')
    ap.add_argument('--engine',choices=['xelatex','pdflatex','lualatex'],default='xelatex')
    ap.add_argument('--runs',type=int,default=3)
    ap.add_argument('--bibtex',action='store_true')
    a=ap.parse_args(); d=Path(a.project).resolve()
    if not d.exists(): raise SystemExit(f'not found: {d}')
    if not shutil.which(a.engine): raise SystemExit(f'engine not found: {a.engine}')
    if a.main:
        main=d/a.main
    else:
        candidates=[d/'main.tex',d/'paper.tex',d/'hsk_main.tex']
        main=next((x for x in candidates if x.exists()),None)
        if main is None:
            tex=list(d.glob('*.tex'))
            if len(tex)!=1: raise SystemExit('cannot uniquely identify main .tex; use --main')
            main=tex[0]
    for i in range(max(1,a.runs)):
        run([a.engine,'-interaction=nonstopmode','-halt-on-error',main.name],d)
        if i==0 and a.bibtex:
            if not shutil.which('bibtex'): raise SystemExit('bibtex not found')
            run(['bibtex',main.stem],d)
    pdf=d/(main.stem+'.pdf')
    if not pdf.exists(): raise SystemExit('compile finished but PDF missing')
    print(pdf); return 0
if __name__=='__main__': raise SystemExit(main())
