# Layout-First Engineering — guia definitivo de instalação e uso

**Autor e mantenedor original:** [Merlin Fachetti (@merlinfachetti)](https://github.com/merlinfachetti)  
**Skill:** `layout-first-engineering` · **Licença:** MIT

> Este é o guia de referência da comunidade. Leia-o antes de instalar. A instalação nativa depende do **produto/cliente** (Claude Code, Gemini CLI, Codex etc.), não apenas do nome do modelo (Claude, Gemini, DeepSeek, Qwen). Ferramentas como Figma, MagicPath e GitHub precisam de integração e autorização **separadas**.

## 1. O que esta skill faz e como funciona

A pessoa descreve um produto ou website e a IA a conduz, **começando pelo layout**, até uma aplicação pronta para ser validada. Em cada etapa, o agente trabalha e pergunta apenas o que falta naquele momento. **Não começa a escrever a aplicação em produção antes das aprovações relevantes.** A IA recomenda; a pessoa decide.

| Etapa | O que acontece | Como o usuário participa |
| --- | --- | --- |
| S0: Ideia | Objetivo, público, inspiração, recursos disponíveis | Descreve livremente a ideia, mesmo incompleta |
| S1: Direção visual | 2–3 propostas realmente distintas, incluindo benefícios e riscos | **G1:** escolhe/mistura a direção |
| S2: UI/UX | Layouts, telas e fluxos, responsividade, estados, tokens, acessibilidade | **G2:** aprova as interfaces |
| S3: Produto | Fluxos ocultos, requisitos, permissões, dados, regras de negócio e MVP | **G3:** aprova escopo e ajustes ao layout |
| S4: Arquitetura e custos | Alternativas tecnológicas, ADRs, segurança, orçamento de implantação e manutenção | **G4:** aprova arquitetura e limite de investimento |
| S5: Gestão | Backlog, riscos, prioridades, critérios de aceite e milestones | Acompanha e esclarece bloqueios |
| S6: Engenharia | Implementação incremental orientada ao design, testes e CI/CD | Avalia incrementos relevantes |
| S7: QA | Testes reais: funcional, visual, acessibilidade, desempenho, segurança | **G5:** aceita versão candidata |
| S8: Release | Operação, observabilidade, rollback, backups quando cabíveis | **G6:** autoriza publicação |
| S9: Evolução | Feedback, bugs, custos e evolução de produto | Prioriza novas alterações |

### Regras inegociáveis

- **Layout primeiro, não tecnologia primeiro.** Há descoberta mínima inicial para o design fazer sentido, e descoberta profunda somente após o conceito visual.
- **Perguntas sob demanda**: em geral uma pergunta importante por vez; até três relacionadas, quando necessário. Respostas como “não sei”, “sugira você” e “quero acrescentar algo” são válidas.
- **Sem aprovações fictícias**: silêncio ou ausência de resposta nunca libera um gate. Não escrever código da aplicação antes de G2, G3 e G4 aprovados.
- **Sem ferramentas fictícias**: a skill não instala Figma/Canva/MagicPath, não cria conta, não fornece acesso ao GitHub nem faz deploy por si só. O cliente precisa fornecer e autorizar tais ferramentas.
- **Sem orçamento inventado**: preços atuais e disponibilidade só podem ser declarados após consulta a fonte confiável; custos não verificáveis são marcados como hipóteses.
- **Sem perda de decisões**: salvar `PROJECT_STATE.md`, `DESIGN_HANDOFF.md`, `DECISIONS.md` e documentos pertinentes quando houver acesso a arquivos. Em chats sem escrita de arquivos, pedir ao agente resumo copiável para persistir fora do chat.
- **Segurança e acessibilidade desde a concepção**. Publicação e operações irreversíveis exigem autorização humana específica.

## 2. O que baixar

Após publicar o repositório, encontre a pasta [`layout-first-engineering/`](../layout-first-engineering/SKILL.md) com `SKILL.md`, `references/`, `assets/` e `scripts/`. **Sempre copie a pasta inteira.**

Para interfaces com upload de Skills, gere/baixe `layout-first-engineering-skill.zip` (o pacote da skill; não o ZIP de todo o repositório). Para conversar com uma IA sem Skills nativas, use [`FALLBACK_SINGLE_PROMPT.md`](../FALLBACK_SINGLE_PROMPT.md).

Estrutura essencial:

```text
layout-first-engineering/
├── SKILL.md
├── references/    # práticas por etapa
├── assets/        # modelos de estado, design, requisitos, custos e riscos
└── scripts/       # verificação local do estado
```

## 3. Instalar no Claude Code

A documentação do Claude Code reconhece as pastas de Skills em `.claude/skills/` (projeto) e `~/.claude/skills/` (pessoal).

**Global no Mac/Linux, a partir da raiz do repositório clonado ou extraído:**

```bash
mkdir -p ~/.claude/skills
cp -R layout-first-engineering ~/.claude/skills/
```

**Somente em um projeto específico:**

```bash
mkdir -p /caminho/do/projeto/.claude/skills
cp -R layout-first-engineering /caminho/do/projeto/.claude/skills/
```

Abra Claude Code no projeto e solicite: `Use a skill layout-first-engineering para conceber [IDEIA]. Comece pela direção visual e faça a primeira pergunta necessária.` Quando suportado, também pode acionar `/layout-first-engineering`. Verifique as permissões de execução e ferramentas conectadas.

**Claude.ai web:** nas contas habilitadas, acesse **Settings → Features → Skills / Custom Skills** e envie o ZIP **da skill**, não o ZIP do repositório. Disponibilidade e nomenclatura mudam de acordo com plano e interface; siga as opções existentes na sua conta.

Referência: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview

## 4. Instalar no Google Gemini CLI

**Forma manual (a partir da raiz do repositório):**

```bash
mkdir -p ~/.gemini/skills
cp -R layout-first-engineering ~/.gemini/skills/
```

Ou instale apenas no projeto em `.gemini/skills/` ou `.agents/skills/`.

**Após publicação no GitHub, forma gerenciada (quando suportada pela versão):**

```bash
gemini skills install https://github.com/merlinfachetti/layout-first-engineering.git --path layout-first-engineering
```

No Gemini CLI, confirme com `/skills list` e atualize a descoberta com `/skills reload`. Para desenvolvimento local, use `gemini skills link /caminho/para/layout-first-engineering` conforme a versão.

**Atenção:** o aplicativo Gemini no navegador não equivale ao Gemini CLI. Se a interface não oferecer Skills, use o prompt de fallback com os arquivos necessários.

Referência: https://geminicli.com/docs/cli/using-agent-skills/

## 5. Instalar no OpenAI Codex

**Global (a partir da raiz do repositório):**

```bash
mkdir -p ~/.agents/skills
cp -R layout-first-engineering ~/.agents/skills/
```

**Por projeto:** copie para `/caminho/do/projeto/.agents/skills/layout-first-engineering/`.

Abra Codex no projeto e escreva: `Use $layout-first-engineering para criar [IDEIA], iniciando pela experiência visual, sem escrever a aplicação antes dos checkpoints.` A disponibilidade do acionamento com `$` varia por cliente; solicitar em linguagem natural também funciona quando a skill é descoberta.

Codex e ChatGPT web não têm necessariamente o mesmo gerenciamento de Skills.

Referência: https://developers.openai.com/blog/skills-agents-sdk

## 6. Instalar no ChatGPT (web)

De acordo com a documentação atual, **Skills nativas no ChatGPT estão disponíveis para contas elegíveis Business, Enterprise, Healthcare e Edu, sujeitas a configurações administrativas**. Não prometa upload nativo em contas Free/Go/Plus/Pro sem confirmação de acesso. Se disponível:

1. Abra **Plugins → Skills**.
2. Selecione **Create → Upload from your computer**.
3. Envie `layout-first-engineering-skill.zip` e analise os avisos de segurança.
4. Peça: `Use a skill layout-first-engineering para [IDEIA]`.

**Sem o menu Skills:** crie um Projeto do ChatGPT e utilize `FALLBACK_SINGLE_PROMPT.md` nas instruções do projeto, anexando o `SKILL.md` e as referências necessárias, ou cole o prompt em uma conversa. Essa alternativa **não** equivale à instalação nativa nem garante execução, ferramentas ou persistência automática.

Referência: https://help.openai.com/en/articles/20001066-skills-in-chatgpt

## 7. DeepSeek, Qwen e outras IAs

DeepSeek e Qwen são famílias de modelos; **a instalação depende do cliente/agent host que os executa**. Se esse host implementar Agent Skills, siga a documentação dele e coloque `layout-first-engineering/SKILL.md` na localização reconhecida. Caso contrário:

1. Abra `FALLBACK_SINGLE_PROMPT.md` e forneça as instruções no chat ou campo de instruções customizadas.
2. Anexe/copie `PROJECT_STATE.md` e o handoff do design nas sessões seguintes.
3. Confirme separadamente acesso a ferramentas de design, terminal, filesystem, Git e web.
4. Não presuma que o chat executa scripts, mantém arquivos entre sessões ou usa MCP automaticamente.

**A mesma skill pode inspirar o fluxo em qualquer modelo; não existe garantia de instalação nativa ou execução idêntica em “qualquer IA”.**

## 8. Conectar Figma, MagicPath, Framer, GitHub e outras ferramentas

Skill ≠ conector MCP. A skill instrui *como trabalhar*, enquanto o MCP/app fornece *acesso efetivo*.

- **Design**: autorize Figma ou ferramentas equivalentes no agente; o agente deve listar quais conectores consegue efetivamente utilizar.
- **Criatividade**: ferramentas como MagicPath ou Framer são opcionais, dependendo de suporte e disponibilidade. Não há dependência obrigatória.
- **Engenharia**: conecte repositório Git e ferramentas de programação somente quando chegar às etapas de engenharia e com permissões apropriadas.
- **Pesquisa/custos**: habilite pesquisa atualizada, caso queira comparação de preços com fonte e data.
- **Publicação**: confirme branch, conta, ambiente e custos; deploy exige G6.

A ausência de um conector não impede o processo: a IA pode fornecer um handoff escrito, mas deve indicar precisamente o que não conseguiu executar.

## 9. Como iniciar uma ideia — prompt copiável

```text
Use a skill layout-first-engineering.

Quero criar [DESCREVA A IDEIA] para [PÚBLICO-ALVO].
Minha inspiração visual é [ESTILOS, LINKS, TELAS OU 'AINDA NÃO SEI'].

Você deve iniciar com a exploração criativa e as interfaces, não com a stack.
Conduza as etapas S0–S9, uma por vez, trazendo recomendações fundamentadas.
Faça apenas as perguntas relevantes à decisão atual; posso responder livremente,
dizer 'não sei' ou adicionar contexto. Registre tudo o que aprovamos.

Não escreva a aplicação em produção antes de aprovarmos visual (G2),
escopo (G3) e arquitetura/custos (G4). Não publique sem G6.

Primeiro, verifique quais conectores estão realmente disponíveis e
faça somente a próxima pergunta necessária para começar.
```

### Como o agente deve agir em uma conversa real

**Usuário:** “Quero um website inovador para organizar minhas pesquisas, mas não sei a stack.”

**Agente:** “Vou começar pelo conceito visual. Vejo três direções: biblioteca editorial, mesa de investigação ou painel espacial. Recomendo biblioteca editorial para leitura e descoberta. Qual delas quer explorar primeiro?”

**Usuário:** “Biblioteca editorial, mas com interações futuristas.”

**Agente:** “Vou criar a primeira tela e registrar sua direção. Por enquanto, não preciso que você escolha banco de dados ou hospedagem.”

*(Depois da aprovação do layout)*

**Agente:** “O layout mostra arquivos particulares. Eles serão privados por usuário ou compartilhados por equipe? Essa decisão altera permissões e arquitetura; recomendo começar com privacidade por usuário.”

## 10. Pausar, retomar e trocar de IA

Solicite ao agente: `Salve o PROJECT_STATE.md, DESIGN_HANDOFF.md, DECISIONS.md e arquivos relacionados, com os links e decisões aprovadas. Diga em qual estágio/gate estamos.`

Em outra IA, forneça esses arquivos e peça:

```text
Use layout-first-engineering. Retome o projeto do PROJECT_STATE.md e do DESIGN_HANDOFF.md.
Valide a consistência com DECISIONS.md, identifique lacunas e continue do gate atual.
Não reinicie a descoberta nem assuma aprovações ausentes.
```

Sem filesystem ou armazenamento persistente, salve manualmente os documentos gerados; um chat sozinho não equivale a um repositório.

## 11. Atualizar e desinstalar

- Clone/atualize o repositório, revise o `CHANGELOG.md` e substitua/re-sincronize **a pasta inteira** da skill na plataforma escolhida. A instalação por cópia não atualiza automaticamente.
- Para Gemini CLI gerenciado, consulte `gemini skills` para atualização/reinstalação de acordo com a versão.
- Para Claude.ai/ChatGPT web, envie novamente uma nova versão quando disponibilizada; não presuma sincronização automática via GitHub.
- Para remover uma instalação por cópia, remova **apenas** o diretório de skill conhecido, como `~/.claude/skills/layout-first-engineering`, após conferir seu conteúdo. Isso não remove os documentos de projeto.

## 12. Solução de problemas

**“Skill não encontrada”**: confirme que o caminho termina em `layout-first-engineering/SKILL.md` e que o YAML `name` e `description` está intacto. Verifique o diretório que seu cliente procura e reinicie/recarregue.

**“Figma não está disponível”**: instalar a skill não instala Figma/MCP; verifique o conector no cliente.

**“Perdi as decisões”**: forneça `PROJECT_STATE.md` e `DECISIONS.md`; configure persistência em arquivos nas próximas sessões.

**“O agente começou a programar antes do design”**: diga `Pare em G2. Aplique as regras S0–S2 do SKILL.md; sem código da aplicação antes de G2+G3+G4.`

**“bash: scripts/publish-macos.sh: No such file or directory”**: você não está na raiz do pacote extraído. Confira com `pwd` e `find ~/Downloads -name publish-macos.sh -print`, ou siga [o guia de publicação](PUBLICACAO-GITHUB-MAC.md).

## Referências oficiais

- Agent Skills specification: https://agentskills.io/specification
- Claude Skills: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview
- Gemini CLI Skills: https://geminicli.com/docs/cli/using-agent-skills/
- OpenAI Codex Skills: https://developers.openai.com/blog/skills-agents-sdk
- ChatGPT Skills eligibility: https://help.openai.com/en/articles/20001066-skills-in-chatgpt
