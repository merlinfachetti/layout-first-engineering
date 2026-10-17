# Layout-First Engineering — Comunidade, segurança, privacidade e publicação (PT-BR)

**Criador e mantenedor:** [@merlinfachetti](https://github.com/merlinfachetti)  
**Repositório:** https://github.com/merlinfachetti/layout-first-engineering  
**Última revisão:** 2026-10-16  
**Status:** guia operacional; não é parecer jurídico nem certificação de conformidade.

## A. O que torna o projeto realmente open source

1. **Público**: código e documentação podem ser acessados sem autenticação.
2. **Licenciado**: `LICENSE` contém MIT; a comunidade pode usar, modificar e redistribuir respeitando as condições da licença.
3. **Colaborativo**: `CONTRIBUTING.md`, templates e PRs orientam melhorias por forks. Isso não exige acesso direto de escrita.
4. **Governança**: `GOVERNANCE.md`, `CODEOWNERS` e Ruleset protegem a versão oficial; contribuições humanas preservam crédito/autoria individual.
5. **Segurança e privacidade**: `SECURITY.md`, `PRIVACY.md`, CI com permissões mínimas, relatos privados e sem segredos em commits.

A licença MIT permite forks e usos derivados; você mantém o projeto oficial e autoria original, mas não pode proibir legalmente modificações permitidas pela licença. "Sem IA como co-author" aplica-se às mensagens de commit que você produz; não retire a atribuição de colaboradores humanos.

## B. Arquivos e finalidade

| Arquivo | Por que existe |
|---|---|
| `README.md`, `README.pt-BR.md` | Apresentação, instalação e links principais |
| `LICENSE` | Termos legais de uso e redistribuição |
| `CODE_OF_CONDUCT.md` | Regras de convivência, moderação e denúncia |
| `CONTRIBUTING.md` | Como abrir Issues, PRs e validar mudanças |
| `GOVERNANCE.md` | Quem decide, quem aprova, autoria e roadmap |
| `SECURITY.md` | Canal privado e procedimentos para vulnerabilidades |
| `PRIVACY.md` | Tratamento de dados durante colaboração no GitHub |
| `SUPPORT.md` | Onde obter ajuda sem expor informação privada |
| `ACCESSIBILITY.md` | Canal e critérios para questões de acessibilidade |
| `ROADMAP.md` | Prioridades abertas e contribuição inicial |
| `.github/CODEOWNERS` | Responsável por revisão |
| `.github/workflows/validate.yml` | Testes sem escrita automática |
| `.github/ISSUE_TEMPLATE/` | Formulários adequados a problemas, ideias e compatibilidade |

## C. Configurar manualmente no GitHub (uma vez)

1. **Ruleset já existe**: visite https://github.com/merlinfachetti/layout-first-engineering/rules e confirme `protect-main` ativo, alvo `Default` (main), PR obrigatório, 1 aprovação, Code Owner, `lint-and-check-gates`, branch atualizada, sem force push/deleção, merge `squash`, bypass só via PR. **Não crie outro ruleset redundante**.
2. **Issues / Discussions**: em *Settings → General → Features*, mantenha `Issues` ligado e habilite `Discussions`. Teste ambos em uma janela sem login e, se possível, com outra conta de testes.
3. **Private vulnerability reporting**: *Settings → Advanced Security → Private vulnerability reporting → Enable*. Veja `SECURITY.md`. Isso é **separado** da existência do arquivo `SECURITY.md`.
4. **Actions**: *Settings → Actions → General → Workflow permissions*, escolha permissões de leitura como padrão; mantenha desmarcado `Allow GitHub Actions to create and approve pull requests`, salvo necessidade concreta. `.github/workflows/validate.yml` já declara `contents: read`.
5. **Segurança adicional**: verifique quais opções de Dependabot, secret scanning e push protection estão disponíveis na conta; habilite as aplicáveis. Elas não são substituídas pelo CI estrutural.
6. **Community profile**: confira *Insights → Community Standards* (localização pode variar). Corrija os itens realmente faltantes sem criar duplicatas.
7. **About**: configure descrição, URL, tópicos `agent-skills`, `design-first`, `open-source`, `software-engineering`, `ai-agents`; deixe o acesso ao README PT-BR em destaque.
8. **Releases**: depois que o PR de atualização for mesclado, confira a versão e crie uma release na aba *Releases*, com tag correspondente à documentação, e anexe somente artefatos construídos e verificados a partir do commit lançado.
9. **GitHub Discussions**: crie categorias `General`, `Ideas`, `Q&A`, `Show and tell` se útil, e faça postagem fixada com regras básicas, documentação e links.
10. **Labels**: crie/revise `good first issue`, `help wanted`, `bug`, `documentation`, `security` (para tarefas públicas não sensíveis), `compatibility`, `design`, `testing`. Nunca publique detalhes de uma vulnerabilidade na label/Issue pública.

## D. Fluxo protegido de manutenção local — macOS

**Pasta de trabalho pretendida:** `/Users/alden.fachetti/Projects_MerlinFachetti/layout-first-engineering`

Nunca execute novamente `publish-macos.sh` depois da primeira publicação. Nunca faça push direto na `main` protegida. **Não copie um ZIP antigo por cima do diretório Git**; preserve alterações de colaboradores.

**Atualização com o pacote desta versão:**

```bash
cd ~/Downloads
unzip -q layout-first-engineering-community-v0.1.3.zip -d lfe-community-update
bash "$HOME/Downloads/lfe-community-update/ATUALIZAR_GITHUB.command"
```

O atualizador valida autenticação `merlinfachetti`, diretório, `origin`, sincronização da `main`, testes e mudanças esperadas. Faz uma cópia incremental dos arquivos da distribuição **sem remover arquivos existentes** e somente após sua confirmação. Depois cria uma branch `docs/community-governance-v0.1.3`, permite revisar o diff, pede confirmação para fazer commit/push e abre um PR na sua conta. **O script não faz merge e não cria release automaticamente**.

Para edições futuras sem ZIP:

```bash
cd /Users/alden.fachetti/Projects_MerlinFachetti/layout-first-engineering
git switch main && git pull --ff-only origin main
git switch -c docs/minha-melhoria
# edite e valide os arquivos
python3 -m unittest discover -s tests -v
git diff --check
git add -A
git -c user.name="Merlin Fachetti" -c user.email="12265786+merlinfachetti@users.noreply.github.com" commit -m "docs: minha melhoria"
git push -u origin docs/minha-melhoria
gh pr create --base main --head docs/minha-melhoria --fill
```

Revise o PR em `https://github.com/merlinfachetti/layout-first-engineering/pulls`, aguarde o CI, confira o diff, use bypass administrativo por PR **somente se necessário**, e então faça *Squash and merge*. Em seguida:

```bash
git switch main
git pull --ff-only origin main
```

Não publique tokens nem configure uma IA como coautora. No seu repositório pessoal, a autoria do commit deve representar corretamente quem fez cada contribuição. A autoria inicial registrada não é alterada por contribuições externas.

## E. Teste prático com a comunidade

1. Visite o repositório no modo anônimo: conteúdo, MIT, `README` e documentação devem estar acessíveis.
2. Use **outra conta de testes autorizada**, ou convide uma pessoa de confiança, para fazer fork, editar documentação e abrir PR.
3. Confira se os checks executam no PR; provoque uma falha de teste em uma branch de testes e verifique se o merge **sem bypass** é bloqueado (não faça merge desse PR).
4. Verifique se um PR da comunidade pede revisão do `@merlinfachetti` via CODEOWNERS; valide status, conversas e método de merge.
5. Use Issues/Discussions para sugestões não sensíveis. Para vulnerabilidades, use o formulário privado de Security Advisories.

## F. O que é e não é "conforme a lei"

- **MIT** é uma licença open source reconhecida, mas a licença não resolve automaticamente privacidade, direitos autorais de conteúdo de terceiros, marcas, segurança, proteção do consumidor ou obrigações de um produto hospedado.
- **Privacidade**: contribuições no GitHub podem envolver informações pessoais públicas. Oriente minimização de dados e procure não coletar dados fora do serviço. O GDPR, quando aplicável, exige análise de finalidade, base jurídica, transparência, retenção, transferências e direitos. `PRIVACY.md` é um aviso inicial; não é certificado de conformidade.
- **Direitos de terceiros**: contribuidores devem confirmar permissão para incluir código, imagens, fontes e materiais gerados por IA. Verifique licenças externas e termos de fornecedores.
- **Distribuição**: o repositório fornece uma skill. Produtos e serviços construídos com ela precisam de suas próprias políticas e auditoria jurídica/técnica quando necessário.
- **Responsabilidade**: testes automatizados não provam ausência de falhas, segurança de qualquer aplicativo ou conformidade com WCAG/GDPR.

Se surgir monetização, hospedagem de usuários, assinatura, telemetria própria, contratação de contribuidores, transferência de dados para conectores ou marca comercial, avalie com profissional jurídico qualificado no(s) país(es) relevante(s) antes de lançar.

## G. Fontes oficiais para revisão periódica

- GitHub Community Standards: https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/about-community-profiles-for-public-repositories
- GitHub Rulesets: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets
- Private vulnerability reporting: https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/configure-vulnerability-reporting/configure-for-a-repository
- GitHub Actions permissions: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository
- MIT SPDX: https://spdx.org/licenses/MIT
- GDPR principles: https://commission.europa.eu/law/law-topic/data-protection/information-business-and-organisations/principles-gdpr_en
- GDPR transparency: https://commission.europa.eu/law/law-topic/data-protection/information-business-and-organisations/obligations_en
- GitHub Privacy: https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement
