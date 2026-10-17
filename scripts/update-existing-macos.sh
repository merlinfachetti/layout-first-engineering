#!/usr/bin/env bash
# Kept for backward compatibility with v0.1.2 package commands.
# Direct pushes to protected main are disabled; creates a feature branch and PR.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$HERE/update-community-macos.sh"
