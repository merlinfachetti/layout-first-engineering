#!/usr/bin/env bash
# One-time local publication: only the authenticated GitHub user can initiate it.
set -euo pipefail
EXPECTED_USER="merlinfachetti"
EXPECTED_ID="12265786"
AUTHOR_NAME="Merlin Fachetti"
AUTHOR_EMAIL="${EXPECTED_ID}+${EXPECTED_USER}@users.noreply.github.com"
REPO="${EXPECTED_USER}/layout-first-engineering"
PROJECTS_DIR="/Users/alden.fachetti/Projects_MerlinFachetti"
DEST="${PROJECTS_DIR}/layout-first-engineering"
SOURCE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

fail() { echo "ERROR: $*" >&2; exit 1; }
[[ "$(uname -s)" == "Darwin" ]] || fail "Execute este script no seu Mac (macOS)."
[[ -f "${SOURCE}/layout-first-engineering/SKILL.md" ]] || fail "Fonte da skill não encontrada em ${SOURCE}."
for cmd in git gh python3; do command -v "$cmd" >/dev/null 2>&1 || fail "É necessário instalar: ${cmd}."; done

gh auth status >/dev/null || fail "Execute 'gh auth login' na sua conta pessoal e tente novamente."
ACTIVE_USER="$(gh api user --jq '.login')"
[[ "$ACTIVE_USER" == "$EXPECTED_USER" ]] || fail "Conta GitHub errada: '${ACTIVE_USER}'. Exigida: ${EXPECTED_USER}."
ACTIVE_ID="$(gh api user --jq '.id')"
[[ "$ACTIVE_ID" == "$EXPECTED_ID" ]] || fail "O ID da conta não corresponde ao previamente verificado."

[[ ! -e "$DEST" ]] || fail "O destino já existe: $DEST. Para preservar seus arquivos, nada será sobrescrito."
if gh repo view "$REPO" >/dev/null 2>&1; then
  fail "O repositório remoto já existe: ${REPO}. Não vou sobrescrever o conteúdo."
fi

(cd "$SOURCE" && python3 -m unittest discover -s tests -v && python3 layout-first-engineering/scripts/verify_project.py layout-first-engineering/assets/PROJECT_STATE.md)
echo
echo "Destino local: $DEST"
echo "Repositório GitHub público: https://github.com/${REPO}"
echo "Autoria inicial: ${AUTHOR_NAME} <${AUTHOR_EMAIL}>"
echo "NENHUMA ferramenta/IA será adicionada como coautora."
read -r -p "Digite PUBLICAR para criar e enviar o repositório (ou Enter para cancelar): " CONSENT
[[ "$CONSENT" == "PUBLICAR" ]] || fail "Publicação cancelada sem alterações."

mkdir -p "$PROJECTS_DIR"
cp -R "$SOURCE" "$DEST"
cd "$DEST"
git init -b main
git config --local user.name "$AUTHOR_NAME"
git config --local user.email "$AUTHOR_EMAIL"
git config --local user.useConfigOnly true
git add --all
GIT_AUTHOR_NAME="$AUTHOR_NAME" GIT_AUTHOR_EMAIL="$AUTHOR_EMAIL" \
GIT_COMMITTER_NAME="$AUTHOR_NAME" GIT_COMMITTER_EMAIL="$AUTHOR_EMAIL" \
git commit -m "feat: publish Layout-First Engineering v0.1.0"

ACTUAL_AUTHOR="$(git log -1 --pretty='%an <%ae>')"
[[ "$ACTUAL_AUTHOR" == "${AUTHOR_NAME} <${AUTHOR_EMAIL}>" ]] || fail "Autoria incorreta: ${ACTUAL_AUTHOR}. Nada foi publicado."
if git log -1 --pretty='%B' | grep -Eiq '^Co-authored-by:'; then
  fail "Foi detectado Co-authored-by no commit. Nada foi publicado."
fi

gh repo create "$REPO" --public --description "A human-led, design-first Agent Skill from visual concept to secure production engineering." --source . --remote origin --push

echo "\nPUBLICAÇÃO CONCLUÍDA: https://github.com/${REPO}"
echo "Diretório local: $DEST"
echo "Configure opcionalmente a proteção de main em Settings > Rules > Rulesets."
