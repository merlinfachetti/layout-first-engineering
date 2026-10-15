# Guia de publicação e manutenção — @merlinfachetti

Este repositório tem **Merlin Fachetti (@merlinfachetti)** como criador e mantenedor original. IA não é adicionada como autora ou coautora dos commits iniciais. Pessoas podem contribuir por issues e pull requests; contribuições humanas preservam a atribuição de seus autores.

## 1. Publicação inicial no Mac

1. Instale `git`, `python3` e o [GitHub CLI](https://cli.github.com/) (macOS: `brew install gh`, se você utiliza Homebrew).
2. Execute `gh auth login` e entre **somente** com `merlinfachetti`; não cole tokens em arquivos do projeto.
3. Extraia o arquivo `layout-first-engineering-github-ready.zip` em um diretório temporário, fora de `Projects_MerlinFachetti`.
4. No Terminal, entre na pasta extraída e execute `bash scripts/publish-macos.sh`.
5. O script faz verificações, pergunta antes de publicar, copia para `/Users/alden.fachetti/Projects_MerlinFachetti/layout-first-engineering`, inicializa o Git usando apenas sua identidade, cria o repositório **público** na sua conta e envia o primeiro commit.

**Segurança:** por padrão, não sobrescreve diretórios existentes nem repositórios já criados. Se houver erro após a cópia ou criação remota, confira o estado manualmente antes de tentar novamente; não execute operações destrutivas.

## 2. Controles da comunidade

- Em **Settings → Rules → Rulesets**, proteja `main`, bloqueie force-push/delete, exija que testes passem e considere exigir PR antes do merge.
- `CODEOWNERS` aponta para `@merlinfachetti`, mas a revisão obrigatória precisa ser habilitada nas regras do GitHub; o arquivo sozinho não bloqueia alterações.
- Deixe Issues e Pull Requests habilitados para propostas da comunidade. Não adicione contas de IA como colaboradores/autores.
- Cada PR deve explicar o problema, testes e compatibilidade. Analise manualmente antes de merge.
- O workflow `.github/workflows/validate.yml` testa pushes/PRs e roda semanalmente; **nunca publica ou cria commits**. Jobs automáticos no GitHub não são coautores do código.

## 3. Atualizações locais

1. Edite e valide arquivos no diretório local.
2. Confira `git diff`, `git status` e ausência de segredos.
3. Rode `bash scripts/push-update-macos.sh` para testar, conferir a conta, versionar e enviar suas alterações com a identidade configurada.
4. Se ativar a regra de PR obrigatória, esse script de push direto ficará bloqueado como esperado. Nesse caso crie uma branch e um PR com `gh pr create`, revise e faça merge no GitHub.

## 4. Versões e distribuição

- Registre mudanças em `CHANGELOG.md` e incremente a versão no frontmatter de `layout-first-engineering/SKILL.md`.
- Rode `python3 scripts/build_release.py`. Os ZIPs aparecem na pasta ignorada `dist/`.
- Após testes e revisão manual, crie uma tag de versão e um GitHub Release usando sua conta: `git tag v0.1.0 && git push origin v0.1.0` e `gh release create v0.1.0 dist/layout-first-engineering-skill.zip dist/layout-first-engineering-opensource.zip --title "v0.1.0" --notes-file CHANGELOG.md` (ajuste as notas para a versão correspondente).
- A tag e o release só devem ser criados depois de confirmar que a versão ainda não existe.

## 5. Gestão contínua

- Semanalmente: consulte **Actions**, issues e PRs, revise falhas, vulnerabilidades e compatibilidade das ferramentas.
- Mensalmente: teste a skill com pelo menos um cliente atualizado; documente o resultado em `examples/acceptance-scenarios.md` ou issue.
- Por versão: revise custos/licenças/referências quando aplicável, registre o changelog, execute testes e publique release assinado pela sua conta.
- Não configure auto-merge ou push automático de código se quiser preservar revisão humana e autoria dos commits.

## 6. Limites de autoria

O GitHub determina a autoria usando os metadados do commit. O script usa `Merlin Fachetti <12265786+merlinfachetti@users.noreply.github.com>` apenas no repositório em questão e impede um `Co-authored-by:` no commit inicial. Isso **não** impede que um editor de código ou outra ferramenta gere código; atribuição técnica de autoria e divulgação de ferramentas utilizadas são temas distintos. Respeite as políticas de transparência e licenciamento aplicáveis.
