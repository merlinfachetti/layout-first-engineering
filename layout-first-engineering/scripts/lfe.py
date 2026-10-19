#!/usr/bin/env python3
"""Launcher for the LFE engine, so the skill works the same installed or from a clone.

Usage (from anywhere):  python3 <skill-folder>/scripts/lfe.py <command> [...]
Examples:               python3 ~/.claude/skills/layout-first-engineering/scripts/lfe.py status
                        python3 layout-first-engineering/scripts/lfe.py init my-app "My app"

Standard library only. The engine is looked up next to the skill (installed package) first,
then in the repository root (development clone).
"""
from pathlib import Path
import sys

SKILL_DIR = Path(__file__).resolve().parents[1]
for candidate in (SKILL_DIR / "engine", SKILL_DIR.parent / "engine"):
    if (candidate / "lfe" / "__main__.py").is_file():
        sys.path.insert(0, str(candidate))
        break
else:
    sys.exit("lfe: engine not found next to the skill; reinstall the full skill folder")

if sys.version_info < (3, 10):
    sys.exit(f"lfe: Python 3.10 or newer is required (found {sys.version.split()[0]})")

from lfe.__main__ import main  # noqa: E402

raise SystemExit(main())
