#!/usr/bin/env bash
# Caminho estável: execute de qualquer diretório após extrair este pacote.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ ! -f "$HERE/scripts/publish-macos.sh" ]]; then
  printf 'ERRO: scripts/publish-macos.sh não está na pasta extraída: %s\n' "$HERE" >&2
  printf 'Baixe o ZIP completo e extraia em ~/Downloads/lfe-publish.\n' >&2
  exit 1
fi
exec bash "$HERE/scripts/publish-macos.sh"
