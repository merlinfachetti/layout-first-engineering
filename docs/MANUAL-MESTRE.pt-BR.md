# Layout-First Engineering — MANUAL MESTRE (PT-BR)

**Documento canônico e permanente da comunidade**  
**Projeto:** https://github.com/merlinfachetti/layout-first-engineering  
**Criador e mantenedor original:** Merlin Fachetti — [@merlinfachetti](https://github.com/merlinfachetti)  
**Licença:** MIT · **Versão desta documentação:** 0.1.3 · **Atualizado:** 16/10/2026

> **ATUALIZAÇÃO DE MANUTENÇÃO (0.1.3):** o Ruleset `protect-main` já está ativo. **Atualizações por push direto na `main` foram substituídas pelo fluxo de branch + Pull Request**, documentado em [Comunidade, segurança e privacidade](OPEN-SOURCE-MAINTENANCE.pt-BR.md). Não use comandos antigos de atualização direta.

> **Comece por este documento.** Ele consolida o funcionamento da skill, os prompts, a instalação em clientes de IA, os conectores, a publicação original, as atualizações, a governança open source e os problemas mais frequentes. Os links para os documentos específicos são preservados — nenhum guia anterior foi removido.

## Índice

1. [Visão, funcionamento e aprovações](#1-visão-funcionamento-e-aprovações)
2. [Componentes e conteúdos do repositório](#2-componentes-e-conteúdos-do-repositório)
3. [Instalação em cada plataforma de IA](#3-instalação-em-cada-plataforma-de-ia)
4. [Conectores opcionais: design e engenharia](#4-conectores-opcionais-design-e-engenharia)
5. [Como iniciar, pausar e retomar projetos](#5-como-iniciar-pausar-e-retomar-projetos)
6. [Publicação inicial no GitHub — macOS](#6-publicação-inicial-no-github--macos)
7. [Como atualizar um repositório JÁ PUBLICADO](#7-como-atualizar-um-repositório-já-publicado)
8. [Como manter open source para a comunidade](#8-como-manter-open-source-para-a-comunidade)
9. [Versões e GitHub Releases](#9-versões-e-github-releases)
10. [Autoria, identidade Git e ausência de coautoria por IA](#10-autoria-identidade-git-e-ausência-de-coautoria-por-ia)
11. [Diagnóstico e dúvidas frequentes](#11-diagnóstico-e-dúvidas-frequentes)
12. [Documentação complementar](#12-documentação-complementar)

## 1. Visão, funcionamento e aprovações

Layout-First Engineering (LFE) é uma **skill de processo para agentes de IA**. A sequência é: **conceito visual → interfaces aprovadas → descoberta de produto → arquitetura, segurança e custo → engenharia incremental → validação → autorização de publicação → evolução**.

O usuário continua sendo o piloto: a IA conduz o processo com perguntas curtas e contextuais, faz recomendações explícitas, identifica lacunas e riscos e registra decisões. Nenhuma ferramenta ou orçamento pode ser presumido, e a aprovação não pode ser inferida do silêncio.

| Estado | Entregável | Aprovação humana |
| --- | --- | --- |
| S0 — Contexto mínimo | Propósito, público, referências e ferramentas disponíveis | — |
| S1 — Direção criativa | 2–3 direções realmente diferentes | **G1**: escolher direção |
| S2 — Interfaces | Layouts, protótipos, componentes, estados, responsividade e tokens | **G2**: aprovar visual |
| S3 — Produto | Jornadas, regras, papéis, requisitos ocultos, dados e MVP | **G3**: aprovar escopo e revisão do design |
| S4 — Arquitetura e custos | Alternativas, trade-offs, segurança, orçamento e ADRs | **G4**: aprovar stack e custo |
| S5 — Planejamento | Backlog, riscos, prioridades, critérios de aceite e marcos | Conduzido no escopo aprovado |
| S6 — Implementação | Entregas incrementais e testes com fidelidade visual | Revisões por incremento |
| S7 — Verificação | Evidências de testes, acessibilidade, segurança e performance | **G5**: aceite |
| S8 — Publicação | Preparação operacional, CI/CD, monitoramento e rollback | **G6**: autorizar deploy |
| S9 — Evolução | Melhorias, feedback, issues e revisões de custo | Quando necessário |

**Regras:** sem código de aplicação em produção antes de G2, G3 e G4. Sem publicação sem G6. A IA pode prototipar visualmente antes disso, desde que deixe claro que se trata de protótipo. Se houver conflito entre layout, segurança, custos e usabilidade, apresente opções, riscos e peça uma decisão.

## 2. Componentes e conteúdos do repositório

```text
layout-first-engineering/
├── README.md                       # apresentação em inglês
├── README.pt-BR.md                 # apresentação em português
├── LICENSE                         # licença MIT
├── CHANGELOG.md                    # histórico de versões
├── CONTRIBUTING.md                 # como colaborar
├── SECURITY.md                     # tratamento de vulnerabilidades
├── docs/
│   ├── MANUAL-MESTRE.pt-BR.md      # ESTE MANUAL — ponto único de entrada
│   ├── INSTALACAO-E-USO.pt-BR.md   # instalação detalhada
│   ├── PROMPTS-MESTRES.pt-BR.md    # os dois prompts completos
│   ├── PUBLICACAO-GITHUB-MAC.md    # publicação macOS
│   └── MAINTAINING.pt-BR.md        # manutenção e releases
├── layout-first-engineering/
│   ├── SKILL.md                     # instrução principal da skill
│   ├── references/                  # políticas detalhadas S0–S9
│   ├── assets/                      # modelos de estado, handoff, custo etc.
│   └── scripts/                     # validação local
├── scripts/
│   ├── publish-macos.sh             # somente para primeira publicação
│   ├── update-existing-macos.sh     # atualizar repositório já publicado
│   ├── push-update-macos.sh         # commit e push manual conferido
│   └── build_release.py             # distribuição da skill
├── tests/                           # testes estruturais
├── .github/                         # CI, CODEOWNERS e templates
└── PUBLICAR_NO_GITHUB.command       # atalho da primeira publicação
```

Os arquivos `PROJECT_STATE.md`, `DESIGN_HANDOFF.md`, `DECISIONS.md`, `COST_MODEL.md`, `DELIVERY_PLAN.md`, `RISK_REGISTER.md` e `TRACEABILITY.md` são modelos de documentação **de cada projeto criado com a skill**. Não confunda os modelos do repositório com decisões reais de um produto.

## 3. Instalação em cada plataforma de IA

**Duas modalidades:** instalação nativa da skill quando o cliente suportar Agent Skills; ou uso por instruções/prompt quando não suportar. **O modelo isolado (DeepSeek, Qwen etc.) não determina a instalação — o cliente/hospedeiro determina.** Sempre copie a pasta completa, não apenas `SKILL.md`.

### Claude Code (por usuário)

Na pasta raiz do repositório clonado:

```bash
mkdir -p ~/.claude/skills
cp -R layout-first-engineering ~/.claude/skills/
```

Para um só projeto: copie a pasta em `SEU_PROJETO/.claude/skills/layout-first-engineering/`.

### Gemini CLI (por usuário)

```bash
mkdir -p ~/.gemini/skills
cp -R layout-first-engineering ~/.gemini/skills/
```

Para um projeto: `SEU_PROJETO/.gemini/skills/layout-first-engineering/`. Confira com `/skills list` em clientes que ofereçam esse comando. Alguns clientes também reconhecem `.agents/skills/`.

### OpenAI Codex (por usuário)

```bash
mkdir -p ~/.agents/skills
cp -R layout-first-engineering ~/.agents/skills/
```

Para um projeto: `SEU_PROJETO/.agents/skills/layout-first-engineering/`.

### Claude.ai (web)

Quando a conta oferecer custom Skills, envie `dist/layout-first-engineering-skill.zip` pelo gerenciador de Skills. As opções dependem da conta/plano. Não presuma que o ChatGPT e o Claude.ai usem o mesmo instalador.

### ChatGPT (web)

Se a sua conta/workspace tiver **Skills nativas**, use o menu correspondente para importar o ZIP da skill. **Não é possível assumir que o ChatGPT Plus tenha essa função.** Sem acesso nativo, coloque as instruções de [`FALLBACK_SINGLE_PROMPT.md`](../FALLBACK_SINGLE_PROMPT.md) em um Projeto ou chat, anexando quando necessário o `SKILL.md` e documentos do estado. Esse caminho é um fallback e não oferece automaticamente persistência, execução de comandos ou MCP.

### DeepSeek, Qwen ou outra IA

Use um agente/cliente que suporte Agent Skills para instalar a pasta na localização documentada por ele. Se o cliente não reconhecer Skills, use o prompt universal e anexe os handoffs. A compatibilidade de comportamento e a disponibilidade de ferramentas devem ser testadas separadamente.

**Guia detalhado:** [Instalação e uso](INSTALACAO-E-USO.pt-BR.md).

## 4. Conectores opcionais: design e engenharia

**Skill é método, conector é capacidade.** A skill não concede autorização de acesso a nenhum serviço. Conecte separadamente quando fizer sentido:

- **Figma/MagicPath**: referências, telas editáveis, protótipos e UI/UX (conforme plugin/cliente).
- **Framer/Webflow**: websites visuais e publicação quando suportados.
- **Lovable/v0**: construção/prototipação de aplicativos quando autorizada.
- **GitHub**: repositório, issues, pull requests, commits, reviews e CI.
- **Pesquisa web**: comparação fundamentada e datada de tecnologia, preços, riscos e fornecedores.
- **Terminal/código**: testes, implementação, build, migrações e releases.

O agente deve declarar o que está **disponível, indisponível ou ainda não verificado**. Nunca declarar que produziu interfaces editáveis, consultou preços ou executou testes sem evidência.

## 5. Como iniciar, pausar e retomar projetos

### Comando inicial, após instalar a skill

```text
Use a skill layout-first-engineering.
Quero criar [DESCREVA IDEIA E PÚBLICO]. Meu estilo visual é [REFERÊNCIAS OU 'NÃO SEI'].
Comece por conceitos de layout, antes de decidir a stack. Faça apenas a pergunta
necessária ao estágio atual, recomende soluções e registre cada decisão.
Não implemente o aplicativo antes da aprovação do visual, do produto e da
arquitetura/custos. Não publique sem minha autorização explícita.
```

### Em plataformas sem Skills nativas

Consulte os dois [prompts mestres completos](PROMPTS-MESTRES.pt-BR.md), que explicam direção criativa e engenharia, ou use [`FALLBACK_SINGLE_PROMPT.md`](../FALLBACK_SINGLE_PROMPT.md) para todo o fluxo.

### Pausar

```text
Registre o estado atual em PROJECT_STATE.md e atualize DESIGN_HANDOFF.md,
DECISIONS.md, requisitos, custos e riscos relevantes. Identifique estágio/gate,
aprovações, pendências e próxima pergunta. Não invente aprovações.
```

### Retomar em outra IA

```text
Use layout-first-engineering. Leia PROJECT_STATE.md e DESIGN_HANDOFF.md,
compare com DECISIONS.md, confira as aprovações e retome do ponto registrado,
sem recomeçar decisões aprovadas nem avançar sem os gates.
```

**Importante:** se o chat não puder escrever arquivos, copie e salve os handoffs fora dele. Histórico do chat sozinho não é repositório versionado.

## 6. Publicação inicial no GitHub — macOS

**Esta etapa é apenas para quem ainda NÃO publicou.** O repositório `merlinfachetti/layout-first-engineering` já foi visto como público em 15/10/2026; nesse caso **não rode novamente o instalador de primeira publicação**. Use a seção 7.

Pré-requisitos: Git, Python 3, GitHub CLI (`brew install gh` para usuários Homebrew), login `gh auth login` na conta correta. Nunca insira tokens em arquivos públicos.

Se ainda não houver repositório e você tiver baixado o ZIP v0.1.2 para `~/Downloads`:

```bash
cd ~/Downloads
unzip -o layout-first-engineering-github-ready-v0.1.2.zip -d lfe-publish
bash "$HOME/Downloads/lfe-publish/PUBLICAR_NO_GITHUB.command"
```

A verificação confirma o GitHub `merlinfachetti`, prepara `/Users/alden.fachetti/Projects_MerlinFachetti/layout-first-engineering`, exige `PUBLICAR`, configura a identidade Git somente no repositório e cria repositório público e primeiro commit sem trailer de coautoria de IA. Se o destino ou repositório existir, o script aborta em vez de sobrescrever.

**Erro “No such file or directory”:** use o caminho absoluto acima; ou `find "$HOME/Downloads" -name publish-macos.sh -print` para localizar o arquivo. **Não execute `publish-macos.sh` dentro de um repositório já publicado.**

Mais detalhes em [Publicação GitHub no Mac](PUBLICACAO-GITHUB-MAC.md).

## 7. Como atualizar um repositório JÁ PUBLICADO

**A partir da versão 0.1.3, todo update passa por branch e PR**, porque o `protect-main` já exige Pull Requests e verificações. Não tente fazer push direto na `main`.

Faça download do ZIP `layout-first-engineering-community-v0.1.3.zip` e rode:

```bash
cd ~/Downloads
unzip -q layout-first-engineering-community-v0.1.3.zip -d lfe-community-update
bash "$HOME/Downloads/lfe-community-update/ATUALIZAR_GITHUB.command"
```

Este instalador **não** recria o repo nem apaga arquivos existentes: valida usuário/remoto/estado local, solicita `PREPARAR_PR`, cria a branch `docs/community-governance-v0.1.3`, copia apenas arquivos permitidos, roda testes e solicita `PUBLICAR_PR` antes de enviar ao GitHub e abrir o PR. É necessário revisar e integrar o PR manualmente após CI e avaliação dos arquivos. **Ele não altera Rulesets, configurações da conta nem cria releases.**

Para mudanças futuras editadas manualmente, consulte [guia de manutenção e comunidade](OPEN-SOURCE-MAINTENANCE.pt-BR.md#d-fluxo-protegido-de-manutenção-local--macos) e [MAINTAINING](MAINTAINING.pt-BR.md).

## 8. Como manter open source para a comunidade

- **Licença MIT:** autoriza uso, modificação e redistribuição; mantenha o aviso de copyright e licença. O projeto tem um criador original; cada contribuição humana preserva a autoria apropriada.
- **README / manuais:** `README.md` (inglês) e `README.pt-BR.md` (português), com este manual como entrada central.
- **Issues:** sugestões e bugs via templates em `.github/ISSUE_TEMPLATE/`.
- **Pull Requests:** contribuição sob revisão com `.github/PULL_REQUEST_TEMPLATE.md` e `CONTRIBUTING.md`.
- **CODEOWNERS:** identifica `@merlinfachetti` para arquivos e facilita pedidos de revisão; sozinho **não** bloqueia commits.
- **Proteção de branch:** no GitHub, **Settings → Rules → Rulesets**, exija status checks, revise PRs, bloqueie força/delete na `main` (disponibilidade conforme plano e tipo de repositório).
- **GitHub Actions:** `.github/workflows/validate.yml` executa validação nos commits, PRs e semanalmente; **não atualiza código automaticamente**.
- **Segurança:** orientações em `SECURITY.md` e revisão de dependências, segredos e permissões. Não cole credenciais no repositório.
- **Ritmo:** semanalmente verificar Actions, issues e PRs; mensalmente experimentar a skill em clientes atualizados; por release conferir changelog, versões, testes e documentação.

**A manutenção semanal de acompanhamento agendada nesta conversa é separada do GitHub Actions**: ela pode analisar o estado e recomendar ações, mas não publica mudanças nem cria commits por conta própria.

## 9. Versões e GitHub Releases

Depois de alterar a skill:

1. Atualize `layout-first-engineering/SKILL.md` (campo `metadata.version`), `CHANGELOG.md` e documentação.
2. Rode `python3 -m unittest discover -s tests -v` e `python3 layout-first-engineering/scripts/verify_project.py layout-first-engineering/assets/PROJECT_STATE.md`.
3. Rode `python3 scripts/build_release.py` para gerar artefatos em `dist/`.
4. Faça commit e publique a versão com sua conta (direto ou via PR revisado).
5. Crie a tag/release explicitamente, nunca substituindo tags existentes:

```bash
git tag v0.1.2
git push origin v0.1.2
gh release create v0.1.2 dist/layout-first-engineering-skill.zip \
  dist/layout-first-engineering-opensource.zip dist/layout-first-engineering.skill \
  --title 'Layout-First Engineering v0.1.2' --notes-file CHANGELOG.md
```

**Atenção:** confira se a tag e os anexos correspondem à versão efetivamente aprovada. O build é local e a criação do release é uma ação pública, portanto execute apenas quando desejar disponibilizar uma nova versão.

## 10. Autoria, identidade Git e ausência de coautoria por IA

O autor do commit e seu e-mail são metadados do Git; não precisam mencionar IA. Nos scripts foi configurada a conta verificada como:

```text
Nome: Merlin Fachetti
GitHub: merlinfachetti
E-mail Git: 12265786+merlinfachetti@users.noreply.github.com
```

Para conferir no repositório:

```bash
cd /Users/alden.fachetti/Projects_MerlinFachetti/layout-first-engineering
git config --local user.name
git config --local user.email
git log -1 --format='%an <%ae>%n%B'
```

O script de atualização exige a conta `merlinfachetti` e impede um trailer `Co-authored-by:` no commit que cria. Isso não equivale a apagar o histórico de contribuições de terceiros, nem garante que todas as interfaces de terceiros evitem exibir um bot como executor técnico das suas APIs. Para commits com sua identidade, prefira os comandos/scripts locais aqui documentados.

## 11. Diagnóstico e dúvidas frequentes

**Os textos “sumiram” do chat:** o histórico de chat não é a fonte permanente do projeto. Este `MANUAL-MESTRE.pt-BR.md` e os outros documentos devem ser versionados no GitHub, preservados em commits e acessíveis pelo README.

**“No such file or directory”:** confirme onde extraiu o ZIP. Acesse `ls -la "$HOME/Downloads/lfe-update"` e execute o `.command` usando caminho absoluto.

**“O repositório já existe”:** não repita o instalador da publicação inicial; use o atualizador da seção 7.

**“Skill não encontrada”:** verifique se o arquivo está em `.../layout-first-engineering/SKILL.md`, a pasta inteira foi copiada e seu cliente tem suporte a Skills.

**“Figma não disponível”:** instale e autorize o conector separadamente; a skill não desbloqueia a ferramenta.

**“Estou vendo v0.1.0 no GitHub”:** significa que o arquivo da versão mais recente ainda não foi enviado para a branch publicada. Execute a atualização da seção 7 e confira o commit no GitHub.

**“Não quero outra IA mexendo no meu Git”:** use acesso de leitura em conectores sempre que possível; escreva/commite/publíque pela sua sessão local depois de revisar. Bloqueie auto-merge e não compartilhe credenciais.

**“Quero remover a skill”:** apague somente a pasta `layout-first-engineering` da localização de Skills do cliente após conferir o caminho. Isso não apaga os documentos nem os projetos criados com ela.

## 12. Documentação complementar

- [Instalação detalhada e uso](INSTALACAO-E-USO.pt-BR.md)
- [Dois prompts mestres na íntegra](PROMPTS-MESTRES.pt-BR.md)
- [Passo a passo de publicação no GitHub/macOS](PUBLICACAO-GITHUB-MAC.md)
- [Manutenção, comunidade e releases](MAINTAINING.pt-BR.md)
- [README em português](../README.pt-BR.md)
- [README em inglês](../README.md)
- [Contribuir](../CONTRIBUTING.md)
- [Política de segurança](../SECURITY.md)
- [Histórico de versões](../CHANGELOG.md)
- [Texto universal para IAs sem Skills](../FALLBACK_SINGLE_PROMPT.md)
- [Especificação aberta Agent Skills](https://agentskills.io/specification)

**Versão canônica do manual:** `docs/MANUAL-MESTRE.pt-BR.md`. Para não perder a referência entre conversas, guarde também o link `https://github.com/merlinfachetti/layout-first-engineering/blob/main/docs/MANUAL-MESTRE.pt-BR.md` depois de publicar a atualização.
