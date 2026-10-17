#!/usr/bin/env bash
# Explicit, human-reviewed update to an EXISTING GitHub repository via feature branch and PR.
set -euo pipefail

OWNER='merlinfachetti'
GITHUB_USER_ID='12265786'
REPO="$OWNER/layout-first-engineering"
DEST='/Users/alden.fachetti/Projects_MerlinFachetti/layout-first-engineering'
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BRANCH='docs/community-governance-v0.1.3'
AUTHOR='Merlin Fachetti'
EMAIL='12265786+merlinfachetti@users.noreply.github.com'
fail() { printf 'ERRO: %s\n' "$*" >&2; exit 1; }
[[ "$(uname -s)" == 'Darwin' ]] || fail 'Este script foi projetado para macOS.'
for cmd in git gh python3; do command -v "$cmd" >/dev/null 2>&1 || fail "Instale $cmd antes de continuar."; done
[[ -f "$SRC/GOVERNANCE.md" ]] || fail 'Execute o script na cópia extraída do pacote v0.1.3.'
[[ "$SRC" != "$DEST" ]] || fail 'O pacote extraído não deve estar dentro da pasta do projeto.'
[[ -d "$DEST/.git" ]] || fail "Não encontrei repositório local: $DEST. Clone com: gh repo clone $REPO '$DEST'"
[[ "$(gh api user --jq .login)" == "$OWNER" ]] || fail 'Você não está autenticado em merlinfachetti no GitHub CLI.'
[[ "$(gh api user --jq .id)" == "$GITHUB_USER_ID" ]] || fail 'A identidade GitHub autenticada não corresponde à conta esperada.'
[[ "$(gh repo view "$REPO" --json isPrivate --jq .isPrivate)" == 'false' ]] || fail 'O repositório esperado não está público, ou não foi encontrado.'

cd "$DEST"
ORIGIN="$(git remote get-url origin)"
case "$ORIGIN" in
  "https://github.com/$REPO"|"https://github.com/$REPO.git"|"git@github.com:$REPO.git") ;;
  *) fail "Repositório origin inesperado: $ORIGIN" ;;
esac
[[ "$(git branch --show-current)" == 'main' ]] || fail 'Mude para main antes de começar. Não mudarei sua branch atual.'
[[ -z "$(git status --porcelain)" ]] || fail 'Existem alterações locais não salvas. Faça backup/commit antes de prosseguir.'
git fetch origin main
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]] || fail 'main local diferente do remoto. Use git pull --ff-only ou reconcilie antes.'
[[ -z "$(git branch --list "$BRANCH")" ]] || fail "A branch '$BRANCH' já existe. Resolva-a antes de continuar."
[[ -z "$(git ls-remote --heads origin "$BRANCH")" ]] || fail "A branch remota '$BRANCH' já existe. Resolva-a antes de continuar."

# Deliberate allowlist: preserve anything added by the community since the last archive.
FILES=(
  'README.md' 'README.pt-BR.md' 'CHANGELOG.md' 'layout-first-engineering/SKILL.md'
  'CODE_OF_CONDUCT.md' 'CONTRIBUTING.md' 'GOVERNANCE.md'
  'PRIVACY.md' 'SECURITY.md' 'SUPPORT.md' 'ACCESSIBILITY.md' 'ROADMAP.md'
  'docs/MANUAL-MESTRE.pt-BR.md' 'docs/MAINTAINING.pt-BR.md' 'docs/PUBLICACAO-GITHUB-MAC.md'
  'docs/OPEN-SOURCE-MAINTENANCE.pt-BR.md' 'docs/OPEN-SOURCE-MAINTENANCE.md'
  '.github/ISSUE_TEMPLATE/config.yml' '.github/ISSUE_TEMPLATE/compatibility.md'
  '.github/PULL_REQUEST_TEMPLATE.md'
  'tests/test_community.py'
  'ATUALIZAR_GITHUB.command' 'scripts/update-community-macos.sh'
  'scripts/update-existing-macos.sh' 'scripts/push-update-macos.sh'
)
for f in "${FILES[@]}"; do
  [[ -f "$SRC/$f" ]] || fail "Faltou arquivo do pacote: $f"
done
printf '\nRepositório: %s\nPasta local: %s\nBranch proposta: %s\n' "$REPO" "$DEST" "$BRANCH"
printf 'Serão atualizados SOMENTE os %s arquivos listados no script. Outros arquivos não serão removidos.\n' "${#FILES[@]}"
read -r -p 'Digite PREPARAR_PR para criar uma branch e copiar os arquivos: ' CONFIRM
[[ "$CONFIRM" == 'PREPARAR_PR' ]] || fail 'Cancelado sem mudanças.'

git switch -c "$BRANCH"
for f in "${FILES[@]}"; do
  mkdir -p "$(dirname "$DEST/$f")"
  cp "$SRC/$f" "$DEST/$f"
done

git diff --check
python3 -m unittest discover -s tests -v
python3 layout-first-engineering/scripts/verify_project.py layout-first-engineering/assets/PROJECT_STATE.md
printf '\n===== ARQUIVOS MODIFICADOS =====\n'
git status --short
printf '\n===== RESUMO =====\n'
git diff --stat
printf '\nReveja os arquivos com git diff e só prossiga se concordar.\n'
read -r -p 'Digite PUBLICAR_PR para fazer commit/push e abrir PR (ou Enter para parar e revisar): ' CONFIRM2
[[ "$CONFIRM2" == 'PUBLICAR_PR' ]] || { echo 'Branch local criada para sua revisão. Nenhum push realizado.'; exit 0; }

git config --local user.name "$AUTHOR"
git config --local user.email "$EMAIL"
git config --local user.useConfigOnly true
git add -- "${FILES[@]}"
git diff --cached --check
if git diff --cached --quiet; then echo 'Nenhuma modificação a publicar.'; exit 0; fi
GIT_AUTHOR_NAME="$AUTHOR" GIT_AUTHOR_EMAIL="$EMAIL" GIT_COMMITTER_NAME="$AUTHOR" GIT_COMMITTER_EMAIL="$EMAIL" \
  git commit -m 'docs: add open-source governance, privacy and community safeguards'
[[ "$(git log -1 --pretty='%an <%ae>')" == "$AUTHOR <$EMAIL>" ]] || fail 'Autoria não corresponde à identidade desejada.'
if git log -1 --format=%B | grep -Eiq '^Co-authored-by:'; then fail 'Commit possui coautoria inesperada.'; fi

git push -u origin "$BRANCH"
PR_BODY="$(mktemp)"
trap 'rm -f "$PR_BODY"' EXIT
cat > "$PR_BODY" <<'EOF'
## Summary
- Add community conduct, governance, privacy, support, accessibility and roadmap files.
- Improve responsible vulnerability disclosure and contributor attribution.
- Add installation/maintenance checklist and safer protected-branch updating via PR.
- Add offline tests for required community files.

## Validation
- [x] Local unittest suite and state validator executed before commit.
- [ ] Maintainer to review diff, CI and any legally sensitive statements before merge.

Closes no existing issue. No AI Co-authored-by attribution.
EOF

gh pr create --repo "$REPO" --base main --head "$BRANCH" \
  --title 'docs: community governance, privacy and contributor safety' --body-file "$PR_BODY"
printf '\nPR ABERTO. Revise checks e diff no GitHub. NÃO houve merge automático.\n'
