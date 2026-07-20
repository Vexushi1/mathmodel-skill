#!/usr/bin/env python3
"""Pack a modeling project while excluding caches and temporary build files."""
from __future__ import annotations
import argparse, zipfile
from pathlib import Path
EXCLUDE_DIRS={'.git','__pycache__','.pytest_cache','.mypy_cache','.venv','venv'}
EXCLUDE_SUFFIX={'.aux','.log','.out','.toc','.synctex.gz','.fdb_latexmk','.fls'}
def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument('project',nargs='?',default='.')
    ap.add_argument('--output',default='hsk_submission_backup.zip'); a=ap.parse_args()
    root=Path(a.project).resolve(); out=Path(a.output).resolve()
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        for f in root.rglob('*'):
            if not f.is_file() or any(x in EXCLUDE_DIRS for x in f.parts): continue
            if f.suffix in EXCLUDE_SUFFIX or f==out: continue
            z.write(f,f.relative_to(root))
    print(out); return 0
if __name__=='__main__': raise SystemExit(main())
