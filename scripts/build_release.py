#!/usr/bin/env python3
"""Build deterministic skill archives locally; no network, credentials, or Git writes.

- layout-first-engineering-skill.zip: the installable skill folder, now carrying the LFE engine
  (engine/lfe) and its contract schemas, so `scripts/lfe.py` works after a plain copy.
- layout-first-engineering-opensource.zip: every file tracked by Git.
Archives are byte-for-byte reproducible: fixed timestamps, sorted entries, fixed permissions.
"""
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
import hashlib
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
SKILL = "layout-first-engineering"
FIXED_DATE = (1980, 1, 1, 0, 0, 0)
IGNORE = {".git", "dist", "__pycache__", ".pytest_cache", ".DS_Store", ".claude"}


def _wanted(path: Path):
    return path.is_file() and not any(part in IGNORE for part in path.parts) and path.suffix != ".pyc"


def skill_entries():
    """(source, arcname) pairs for the installable skill."""
    entries = [(p, p.relative_to(ROOT).as_posix()) for p in (ROOT / SKILL).rglob("*") if _wanted(p)]
    entries += [(p, f"{SKILL}/engine/lfe/{p.name}") for p in (ROOT / "engine" / "lfe").glob("*.py")]
    entries += [(p, f"{SKILL}/contracts/{p.name}") for p in (ROOT / "contracts").glob("*.schema.json")]
    return sorted(entries, key=lambda e: e[1])


def project_entries():
    try:
        listed = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True).stdout
        paths = [ROOT / name for name in listed.decode("utf-8").split("\0") if name]
    except (OSError, subprocess.CalledProcessError):
        paths = [p for p in ROOT.rglob("*") if _wanted(p)]
    return sorted(((p, p.relative_to(ROOT).as_posix()) for p in paths if _wanted(p)), key=lambda e: e[1])


def archive(target: Path, entries):
    with ZipFile(target, "w") as z:
        for source, arcname in entries:
            info = ZipInfo(arcname, date_time=FIXED_DATE)
            info.compress_type = ZIP_DEFLATED
            executable = source.suffix in {".sh", ".command"} or source.parent.name == "bin"
            info.external_attr = (0o755 if executable else 0o644) << 16
            z.writestr(info, source.read_bytes(), compresslevel=9)
    return hashlib.sha256(target.read_bytes()).hexdigest()


def build(out: Path):
    out.mkdir(parents=True, exist_ok=True)
    digests = {}
    for name, entries in (("layout-first-engineering-skill.zip", skill_entries()),
                          ("layout-first-engineering-opensource.zip", project_entries())):
        digests[name] = archive(out / name, entries)
    shutil.copyfile(out / "layout-first-engineering-skill.zip", out / "layout-first-engineering.skill")
    return digests


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "dist"
    for name, digest in build(target).items():
        print(f"{name}: SHA256 {digest}")
