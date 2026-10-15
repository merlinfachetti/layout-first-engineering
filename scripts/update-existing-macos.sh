#!/usr/bin/env bash
# Updates only the already published repo. Human-controlled commit and push.
set -euo pipefail
EXPECTED_USER='merlinfachetti'
EXPECTED_ID='12265786'
REPO='merlinfachetti/layout-first-engineering'
PARENT='/Users/alden.fachetti/Projects_MerlinFachetti'
DEST="$PARENT/layout-first-engineering"
SOURCE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fail() { echo "ERRO: $*" >&2; exit 1; }
[[ "$(uname -s)" == 'Darwin' ]] || fail 'Este script foi feito para macOS.'
for cmd in gh git python3 rsync; do command -v "$cmd" >/dev/null 2>&1 || fail "Instale o comando: $cmd"; done
[[ -f "$SOURCE/docs/MANUAL-MESTRE.pt-BR.md" ]] || fail 'O pacote extraído não contém o Manual Mestre.'
[[ -f "$SOURCE/layout-first-engineering/SKILL.md" ]] || fail 'A skill não foi encontrada no pacote.'
gh auth status >/dev/null 2>&1 || fail "Execute 'gh auth login'."
[[ "$(gh api user --jq '.login')" == "$EXPECTED_USER" ]] || fail 'Conta GitHub diferente de merlinfachetti.'
[[ "$(gh api user --jq '.id')" == "$EXPECTED_ID" ]] || fail 'O ID da conta GitHub não corresponde.'
gh repo view "$REPO" --json isPrivate --jq '.isPrivate' | grep -Fxq false || fail 'O repositório remoto não existe ou não está público.'
(cd "$SOURCE" && python3 -m unittest discover -s tests -v && python3 layout-first-engineering/scripts/verify_project.py layout-first-engineering/assets/PROJECT_STATE.md)
# Source and destination cannot coincide: avoid self-overwrite.
[[ "$SOURCE" != "$DEST" ]] || fail 'Extraia o pacote em Downloads, não em cima do repositório local.'
if [[ ! -e "$DEST" ]]; then
  echo "Cópia local não encontrada: $DEST"
  [[ ! -e "$PARENT" || -d "$PARENT" ]] || fail 'A pasta-pai existe mas não é um diretório.'
  read -r -p 'Digite CLONAR para clonar o repositório público para essa pasta (ou Enter para cancelar): ' AUTHCLONE
  [[ "$AUTHCLONE" == 'CLONAR' ]] || fail 'Operação cancelada.'
  mkdir -p "$PARENT"
  gh repo clone "$REPO" "$DEST"
fi
[[ -d "$DEST/.git" ]] || fail "Destino existente não é repositório Git: $DEST"
cd "$DEST"
[[ "$(git branch --show-current)" == main ]] || fail 'A branch local não é main.'
ORIGIN="$(git remote get-url origin)"
case "$ORIGIN" in
  https://github.com/merlinfachetti/layout-first-engineering.git|https://github.com/merlinfachetti/layout-first-engineering|git@github.com:merlinfachetti/layout-first-engineering.git) ;;
  *) fail "Remoto inesperado: $ORIGIN" ;;
esac
[[ -z "$(git status --porcelain)" ]] || fail 'Existem alterações locais. Salve/revise antes de atualizar; não sobrescrevi nada.'
git fetch origin main
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]] || fail 'Branch local está divergente ou desatualizada. Reconcile manualmente antes de continuar.'
echo
echo "ORIGEM: $SOURCE"
echo "DESTINO: $DEST"
echo 'Serão sincronizados arquivos de documentação, skill, testes e scripts; .git e dist não serão modificados.'
echo 'Prévia das alterações (nenhum arquivo alterado ainda):'
rsync -ain --exclude='/.git/' --exclude='/dist/' --exclude='__pycache__/' --exclude='*.pyc' --exclude='/.DS_Store' \
  "$SOURCE/" "$DEST/"
read -r -p 'Digite ATUALIZAR_DOCUMENTACAO para sincronizar o pacote 0.1.2: ' CONFIRM
[[ "$CONFIRM" == 'ATUALIZAR_DOCUMENTACAO' ]] || fail 'Cancelado sem copiar arquivos.'
# Keep Git history untouched and avoid shipping generated artifacts and bytecode.
rsync -a --exclude='/.git/' --exclude='/dist/' --exclude='__pycache__/' --exclude='*.pyc' \
  --exclude='/.DS_Store' "$SOURCE/" "$DEST/"
cd "$DEST"
git status --short
# Calls update script with separate human confirmations for commit and push.
bash scripts/push-update-macos.sh
