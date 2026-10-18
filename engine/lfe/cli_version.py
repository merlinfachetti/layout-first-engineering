"""`lfe version`: reference command for the `cli_*` extension point."""
from __future__ import annotations

from . import __version__
from .contracts import KNOWN


def cmd_version(args):
    print(f"lfe {__version__}")
    print("contracts: " + ", ".join(f"lfe.{name}/{major}.{minor}" for name, v in sorted(KNOWN.items())
                                    for major, minor in sorted(v.items())))
    return 0


def register(sub):
    parser = sub.add_parser("version", help="core and contract versions")
    parser.set_defaults(func=cmd_version)
