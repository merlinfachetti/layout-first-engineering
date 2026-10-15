#!/usr/bin/env bash
# Stable entrypoint independent of current working directory.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ ! -f "$HERE/scripts/update-existing-macos.sh" ]]; then
  echo 'ERRO: o pacote extraído não contém scripts/update-existing-macos.sh' >&2
  exit 1
fi
exec bash "$HERE/scripts/update-existing-macos.sh"
