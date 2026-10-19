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

A última linha deve mostrar `lfe 0.2.0` e a lista de contratos. Os exemplos abaixo usam o apelido `lfe`.

## 2. Quem roda o quê

| Quem | Comandos |
|---|---|
| **Agente** (Claude, Codex, …) | `init`, `artifact`, `propose`, `record-chat-approval G1`, `run`, `trace`, `render`, `next`, `question`, `handoff`, `status` |
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
   - G2 a G6 só com você, no seu terminal: `lfe approve G2`. O comando mostra o que você aprova, o que destrava e o que **não** destrava, e pede que você digite `G2`.
5. **Ver onde está:** `lfe status`. Mostra cada gate calculado, os motivos e `production code: locked|unlocked`.
6. **Se algo mudar depois de aprovado** (ex.: o protótipo), o gate vira `stale` sozinho e o código de produção volta a ficar bloqueado até você aprovar a nova revisão.
7. **Avançar de estágio:** `lfe stage S6`. É recusado se G2, G3 ou G4 não estiverem válidos.
8. **Provar com testes:** `lfe run TEST-003 --req FR-001 -- python3 -m unittest tests_e2e.test_vs01`. Grava um recibo. Ferramenta ausente vira `not_executed`, nunca `pass`.
9. **Conferir rastreabilidade:** `lfe trace --check`. Cada requisito implementado precisa de teste e recibo `pass`. G5 só pode ser aprovado com isso completo.
10. **Pausar e retomar:** `lfe next "próxima ação"` e `lfe question add "dúvida" --class blocker` guardam o contexto, e `lfe handoff` gera `.lfe/HANDOFF.md`. Com os hooks do Claude Code (seção 5), a sessão nova já começa sabendo onde parou.

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
