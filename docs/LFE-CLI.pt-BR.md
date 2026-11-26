# `lfe` — o motor que trava, lembra e prova (guia em pt-BR)

O `lfe` é a parte executável da skill Layout-First Engineering. A skill diz **o que** o agente deve
fazer; o `lfe` garante, por código, o que ele **não consegue** fazer sem você:

- **trava:** código de produção só depois de G2, G3 e G4 aprovados e ainda válidos;
- **lembra:** guarda em `.lfe/` em que etapa o projeto parou, e uma nova sessão retoma dali;
- **prova:** cada teste executado vira um recibo verificável; sem prova não existe "passou".

Requisito: Python 3.10 ou mais novo, sem nada para instalar (só biblioteca padrão).

## 1. Onde fica o comando

Com o **plugin do Claude Code** (ver README), os hooks e os comandos `/lfe:*` já vêm configurados. Para usar o `lfe` no terminal, o lançador vem dentro da skill; use o caminho da pasta onde ela está instalada:

| Instalação | Comando |
|---|---|
| Claude Code, pessoal | `python3 ~/.claude/skills/layout-first-engineering/scripts/lfe.py` |
| Claude Code, no projeto | `python3 .claude/skills/layout-first-engineering/scripts/lfe.py` |
| Clone do repositório | `python3 layout-first-engineering/scripts/lfe.py` |

Para não digitar o caminho toda vez, crie um apelido no terminal (macOS/Linux, zsh):

```bash
echo 'alias lfe="python3 ~/.claude/skills/layout-first-engineering/scripts/lfe.py"' >> ~/.zshrc
```

```bash
source ~/.zshrc
```

```bash
lfe version
```

A última linha deve mostrar `lfe 0.3.0` e a lista de contratos. Os exemplos abaixo usam o apelido `lfe`.

## 2. Quem roda o quê

| Quem | Comandos |
|---|---|
| **Agente** (Claude, Codex, …) | `init`, `adopt`, `install`, `gate`, `artifact`, `propose`, `record-chat-approval` (G1; G2–G6 se ativado), `chat-approvals`, `run`, `trace`, `render`, `next`, `question`, `handoff`, `status` |
| **Você, no seu terminal** | `approve`, `reject`, `revoke`; confirmar um `import` que traga aprovações |

`lfe approve` recusa rodar sem um terminal interativo e pede que você digite o nome do gate.
O agente não consegue aprovar por você.

## 3. O fluxo, passo a passo

1. **Começar** (na pasta do projeto): `lfe init minha-ideia "Minha ideia"`. Cria `.lfe/` em S0.
2. **Registrar o que foi produzido.** O agente registra cada artefato com hash, por exemplo as direções visuais:
   `lfe artifact DIR-001 --kind direction-set --path .lfe/directions/DIR-001.json`
3. **Pedir uma decisão.** O agente propõe o gate amarrado ao conteúdo exato: `lfe propose G1 --artifact DIR-001`
4. **Decidir.**
   - G1 pode vir da sua fala no chat; o agente registra a citação com `lfe record-chat-approval G1 --quote "..."`.
   - G2 a G6 com você, no seu terminal: `lfe approve G2`. O comando mostra o que você aprova, o que destrava e o que **não** destrava, e pede que você digite `G2`.
   - Se você só trabalha pelo chat (celular, sessão na nuvem), veja a seção 3d: você responde com o código que o `propose` mostrou.
5. **Ver onde está:** `lfe status`. Mostra cada gate calculado, os motivos e `production code: locked|unlocked`.
6. **Se algo mudar depois de aprovado** (ex.: o protótipo), o gate vira `stale` sozinho e o código de produção volta a ficar bloqueado até você aprovar a nova revisão.
7. **Avançar de estágio:** cada estágio exige o gate que fecha o anterior (S2 exige G1, S3 exige G2, S4 exige G3, S5 a S7 exigem G4, S8 exige G5, S9 exige G6). `lfe stage S6` destrava o código de produção. Voltar de estágio é sempre permitido.
8. **Provar com testes:** `lfe run TEST-003 --req FR-001 -- python3 -m unittest tests_e2e.test_vs01`. Grava um recibo. Ferramenta ausente vira `not_executed`, nunca `pass`.
9. **Conferir rastreabilidade:** `lfe trace --check`. Cada requisito implementado precisa de teste e recibo `pass`. G5 só pode ser aprovado com isso completo.
10. **Pausar e retomar:** `lfe next "próxima ação"` e `lfe question add "dúvida" --class blocker` guardam o contexto, e `lfe handoff` gera `.lfe/HANDOFF.md`. Com os hooks do Claude Code (seção 5), a sessão nova já começa sabendo onde parou.

## 3a. Projeto que já está andando: `lfe adopt`

O `lfe init` começa em S0. Para um projeto que já tem `PROJECT_STATE.md`, `DECISIONS.md`, protótipos e capturas:

```bash
lfe adopt --dry-run
```

```bash
lfe adopt
```

O primeiro mostra o plano validado contra os contratos e não grava nada. O segundo lê a tabela de gates com
tolerância (colunas extras, `aprovado ✅`, `Etapa atual: S5`…), continua os ids do ledger depois do maior `DEC-###`
que já existe no seu Markdown, gera rascunhos tipados em `.lfe/adopted/` (direções a partir dos protótipos, telas a
partir de `docs/evidence/*.png` com o tamanho real, requisitos a partir de ids FR-/NFR- ou da tabela MoSCoW, ADRs e
relatório do G5 como estão) e propõe cada gate que o Markdown diz estar aprovado. Essas aprovações ficam como
`imported-legacy`, mantêm o projeto no lugar até S5 e não destravam nada até você reconfirmar cada uma
(`lfe approve G2` ou o código pelo chat). O arquivo `.lfe/ADOPTION.md` lista o que revisar.

## 3b. Checagem automática do G5: `lfe gate G5`

```bash
lfe gate G5 --lighthouse lh-mobile.json --lighthouse lh-desktop.json --axe axe.json
```

Lê o JSON padrão do Lighthouse e o resultado do axe-core e compara com um orçamento (padrão: performance ≥ 90,
acessibilidade ≥ 95, boas práticas ≥ 90, SEO ≥ 90, LCP ≤ 2500 ms, CLS ≤ 0,1, TBT ≤ 200 ms, nenhuma violação
crítica ou séria no axe; ajuste em `.lfe/budget.json`). Sai com 3 se falhar. Imprime um resumo no formato do
unittest, então vira recibo comum: `lfe run TEST-020 --req NFR-001 -- python3 <skill>/scripts/lfe.py gate G5 --lighthouse ...`.

## 3c. Sessões na nuvem: `lfe install --project`

Copia a skill, o motor e os hooks para `.claude/`, para que sessões sem os seus plugins carreguem tudo; faça commit.
`lfe install --check` sai com 3 se a cópia estiver ausente, alterada ou desatualizada.

## 3d. Aprovar pelo chat (dono sem terminal)

Desligado por padrão. A pessoa ativa uma vez, com as próprias palavras:

```bash
lfe chat-approvals enable --gates G2,G3,G4,G5,G6 --quote "<mensagem dela, literal>" --message-ref "<id ou link da mensagem>"
```

A partir daí, `lfe propose G3 …` mostra um código como `G3-7f3a2c`. A pessoa responde `aprovo G3-7f3a2c` e o
agente registra com `lfe record-chat-approval G3 --quote "aprovo G3-7f3a2c" --message-ref "<id>"`. O código vem do
hash daquela proposta: a aprovação só vale para o conteúdo proposto, e conteúdo novo gera proposta e código novos.
A decisão fica como `chat-quote`, `authenticity: unverified`, e deixa de contar se a opção for desligada.
Troca consciente: o terminal *impede* autoaprovação; a citação no chat a torna *detectável*.

G1 híbrido sem JSON: `--primary A --theme-variant dark=A --theme-variant light=B --complementary "C=coleções"`
(`lfe record-chat-approval --help` mostra também o formato JSON).

## 4. Levar o projeto para outra pasta ou outra ferramenta

```bash
lfe export --out meu-projeto.lfe.json
```

```bash
lfe --root ../copia import meu-projeto.lfe.json
```

O pacote leva estado, decisões, artefatos e recibos. Se ele trouxer aprovações, o `import` pede que **você** digite
`IMPORT` no terminal, porque o pacote prova que não foi editado, mas não prova quem decidiu.

## 5. Ligar no Claude Code (opcional, recomendado)

- **Retomada automática:** siga [`adapters/claude-code/session-hooks.md`](../adapters/claude-code/session-hooks.md).
- **Bloqueio na hora de agir:** o hook `PreToolUse` nega escrita em código de produção antes dos gates; ver `adapters/claude-code/README.md`.

## 6. Experimentar sem decidir nada

```bash
lfe demo examples/vs01-leituras --workdir /tmp/lfe-demo
```

Copia o exemplo para uma pasta nova e aprova as propostas como **simuladas**, sempre rotuladas assim.
O exemplo original não é tocado.

## 7. Códigos de saída

`0` ok · `2` uso/ambiente ou falta de terminal humano · `3` negado por regra de gate/estágio ·
`4` versão de contrato incompatível · `5` integridade violada (ledger ou evidência adulterados) · `6` contrato violado.

## 8. Limites honestos

- Numa máquina local, quem tem acesso total ao disco pode forjar arquivos. O `lfe` torna isso **detectável** (cadeia de hash), não impossível.
- A exigência de terminal é a primeira barreira contra autoaprovação; o hook de política é a segunda.
- Os contratos e regras estão nas [RFC-0001](rfcs/0001-core-contracts.md) e [RFC-0002](rfcs/0002-vertical-slice-01.md).
