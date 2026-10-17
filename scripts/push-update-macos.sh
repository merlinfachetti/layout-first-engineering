#!/usr/bin/env bash
# Safe manual path for edits made INSIDE the local repository after the initial publication.
set -euo pipefail
REPO='merlinfachetti/layout-first-engineering'
DEST='/Users/alden.fachetti/Projects_MerlinFachetti/layout-first-engineering'
AUTHOR='Merlin Fachetti'
EMAIL='12265786+merlinfachetti@users.noreply.github.com'
fail(){ echo "ERRO: $*" >&2; exit 1; }
[[ "$(uname -s)" == 'Darwin' ]] || fail 'Somente macOS.'
for c in git gh python3; do command -v "$c" >/dev/null || fail "Instale $c."; done
[[ "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)" == "$DEST" ]] || fail "Execute somente na cópia local do repositório: $DEST"
[[ "$(gh api user --jq .login)" == 'merlinfachetti' ]] || fail 'Autenticação GitHub incorreta.'
[[ "$(gh api user --jq .id)" == '12265786' ]] || fail 'ID da conta diferente.'
cd "$DEST"
[[ "$(git branch --show-current)" != 'main' ]] || fail 'Crie uma branch (git switch -c docs/nome-da-melhoria). Nunca faça push direto na main protegida.'
BRANCH="$(git branch --show-current)"
[[ -n "$BRANCH" ]] || fail 'HEAD detached.'
case "$(git remote get-url origin)" in
  "https://github.com/$REPO"|"https://github.com/$REPO.git"|"git@github.com:$REPO.git") ;;
  *) fail 'Origin inesperado.' ;;
esac
python3 -m unittest discover -s tests -v
python3 layout-first-engineering/scripts/verify_project.py layout-first-engineering/assets/PROJECT_STATE.md
git diff --check
printf '\n';git status --short
read -r -p 'Digite COMMIT para criar um commit pessoal nesta branch: ' A
[[ "$A" == 'COMMIT' ]] || fail 'Cancelado.'
read -r -p 'Mensagem do commit: ' MSG
[[ -n "$MSG" ]] || fail 'Mensagem obrigatória.'
if [[ "${MSG,,}" == *'co-authored-by'* ]]; then fail 'Mensagem inclui coautoria indesejada.'; fi
git config --local user.name "$AUTHOR"
git config --local user.email "$EMAIL"
git config --local user.useConfigOnly true
git add -A
git diff --cached --check
if git diff --cached --quiet; then echo 'Sem alterações.'; exit 0; fi
GIT_AUTHOR_NAME="$AUTHOR" GIT_AUTHOR_EMAIL="$EMAIL" GIT_COMMITTER_NAME="$AUTHOR" GIT_COMMITTER_EMAIL="$EMAIL" git commit -m "$MSG"
if git log -1 --format=%B | grep -Eiq '^Co-authored-by:'; then fail 'Coautoria inesperada no commit.'; fi
read -r -p "Digite PUSH_PR para enviar '$BRANCH' e abrir PR, nunca na main: " B
[[ "$B" == 'PUSH_PR' ]] || { echo 'Commit local realizado; sem push.'; exit 0; }
git push -u origin "$BRANCH"
if gh pr view "$BRANCH" --repo "$REPO" >/dev/null 2>&1; then
  echo 'Já existe um PR para esta branch:'; gh pr view "$BRANCH" --repo "$REPO" --web
else
  gh pr create --repo "$REPO" --base main --head "$BRANCH" --fill
fi
