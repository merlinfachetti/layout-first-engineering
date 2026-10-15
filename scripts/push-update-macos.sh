#!/usr/bin/env bash
# Human-reviewed changes only. Never runs in CI or autonomously.
set -euo pipefail
EXPECTED_USER='merlinfachetti'
AUTHOR_NAME='Merlin Fachetti'
AUTHOR_EMAIL='12265786+merlinfachetti@users.noreply.github.com'
DEST='/Users/alden.fachetti/Projects_MerlinFachetti/layout-first-engineering'
[[ "$(uname -s)" == 'Darwin' ]] || { echo 'Requires macOS.' >&2; exit 1; }
[[ "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)" == "$DEST" ]] || { echo "Run only from $DEST" >&2; exit 1; }
cd "$DEST"
[[ "$(gh api user --jq '.login')" == "$EXPECTED_USER" ]] || { echo 'Wrong GitHub account.' >&2; exit 1; }
[[ "$(git branch --show-current)" == 'main' ]] || { echo 'Checkout main first.' >&2; exit 1; }
ORIGIN="$(git remote get-url origin)"
case "$ORIGIN" in
  https://github.com/merlinfachetti/layout-first-engineering.git|git@github.com:merlinfachetti/layout-first-engineering.git) ;;
  *) echo "Unexpected origin URL: $ORIGIN" >&2; exit 1 ;;
esac
python3 -m unittest discover -s tests -v
python3 layout-first-engineering/scripts/verify_project.py layout-first-engineering/assets/PROJECT_STATE.md

git config --local user.name "$AUTHOR_NAME"
git config --local user.email "$AUTHOR_EMAIL"
git config --local user.useConfigOnly true

git fetch origin main
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]] || { echo 'Local main differs from origin/main; reconcile before updating.' >&2; exit 1; }

git status --short
git diff --check
read -r -p 'Digite ATUALIZAR para versionar mudanças locais sob seu usuário: ' CONFIRM
[[ "$CONFIRM" == 'ATUALIZAR' ]] || { echo 'Cancelled.'; exit 1; }
read -r -p 'Mensagem do commit (sem Co-authored-by): ' MSG
[[ -n "$MSG" ]] && [[ "$MSG" != *Co-authored-by* ]] || { echo 'Invalid commit message.' >&2; exit 1; }
git add -A
if git diff --cached --quiet; then echo 'No changes to commit.'; exit 0; fi
GIT_AUTHOR_NAME="$AUTHOR_NAME" GIT_AUTHOR_EMAIL="$AUTHOR_EMAIL" \
GIT_COMMITTER_NAME="$AUTHOR_NAME" GIT_COMMITTER_EMAIL="$AUTHOR_EMAIL" \
git commit -m "$MSG"
[[ "$(git log -1 --pretty='%an <%ae>')" == "${AUTHOR_NAME} <${AUTHOR_EMAIL}>" ]] || { echo 'Invalid author; not pushed.' >&2; exit 1; }
if git log -1 --pretty='%B' | grep -Eiq '^Co-authored-by:'; then echo 'Unexpected co-author; not pushed.' >&2; exit 1; fi
git push origin main
echo 'Committed and pushed as your personal GitHub identity.'
