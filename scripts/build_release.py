#!/usr/bin/env python3
"""Build reproducible-ish skill archives locally; no network, credentials, or Git writes."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import hashlib
import shutil
import sys

root = Path(__file__).resolve().parent.parent
out = root / 'dist'
out.mkdir(exist_ok=True)
ignore_names = {'.git', 'dist', '__pycache__', '.pytest_cache', '.DS_Store'}


def include(path):
    return path.is_file() and not any(part in ignore_names for part in path.parts) and path.suffix != '.pyc'


def archive(target, paths):
    with ZipFile(target, 'w', ZIP_DEFLATED, compresslevel=9) as z:
        for file in sorted(paths):
            z.write(file, arcname=file.relative_to(root).as_posix())
    return hashlib.sha256(target.read_bytes()).hexdigest()

skill_files = [p for p in (root / 'layout-first-engineering').rglob('*') if include(p)]
project_files = [p for p in root.rglob('*') if include(p) and 'dist' not in p.relative_to(root).parts]
for name, paths in [('layout-first-engineering-skill.zip', skill_files), ('layout-first-engineering-opensource.zip', project_files)]:
    target = out / name
    print(f'{target.name}: SHA256 {archive(target, paths)}')
shutil.copyfile(out / 'layout-first-engineering-skill.zip', out / 'layout-first-engineering.skill')
