"""`lfe studio`: generate the read-only visual workspace (.lfe/studio.html)."""
from __future__ import annotations

from pathlib import Path

from . import studio


def cmd_studio(args):
    out = studio.write(args.root, Path(args.out) if args.out else None)
    print(f"studio written: {out}")
    print(f"open it in a browser, e.g.: open \"{out}\"")
    return 0


def register(sub):
    p = sub.add_parser("studio", help="generate a read-only visual page of gates, design, trace and receipts")
    p.add_argument("--out", help="output HTML file (default: .lfe/studio.html)")
    p.set_defaults(func=cmd_studio)
