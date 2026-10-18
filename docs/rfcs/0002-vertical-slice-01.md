# RFC-0002 — Primeira fatia vertical: VS-01 "Lista de leituras"

- **Status:** Proposta (em revisão pelo proprietário)
- **Autor e decisor:** Merlin Fachetti (@merlinfachetti)
- **Data:** 2026-10-17
- **Depende de:** [RFC-0001 — Contratos do core](0001-core-contracts.md)

## 1. Objetivo

Comprovar, no menor exemplo possível e **offline**, a cadeia completa
**visual → contrato → aprovação → implementação → teste → continuidade**, antes de qualquer
Studio, trilha de aprendizado ou integração externa.

Produto-exemplo: uma lista de leituras local (adicionar, listar, marcar como concluída).
Barato, sem backend, mas com validação, persistência, estados vazio e erro, e privacidade local.

## 2. Escopo

**Dentro:** duas direções visuais, um protótipo navegável com estados, baseline versionada,
requisitos rastreáveis, ADR com duas arquiteturas, uma fatia funcional, testes reais, recibos de
evidência, retomada em outra sessão e checklist de release **sem** deploy.

**Fora:** Studio completo, adapters Figma/Penpot, login ou multiusuário, backend, deploy público,
plugin ou marketplace, evals com tokens no CI, modo Learn, laboratório de custos, Storybook,
regressão visual por pixel, assinatura criptográfica.

## 3. Estrutura de arquivos

```text
examples/vs01-leituras/
  project.json            # manifesto (status draft/ready; ready só com arquivos e testes)
  DEMO_README.md          # passo a passo reproduzível, versões e limites
  directions/A-editorial.html
  directions/B-biblioteca.html
  prototype/index.html    # estados via ?state=empty|error|storage-error
  prototype/tokens.json   # tokens no formato DTCG (subconjunto)
  app/index.html, app/app.js, app/styles.css   # HTML/CSS/JS sem dependências
  tests_e2e/test_vs01.py  # Playwright (opcional), via unittest
  .lfe/                   # estado, ledger, baseline, requisitos, ADR-001, recibos
```

## 4. Jornada e quem age em cada passo

| Etapa | Agente | Humano | Registro |
|---|---|---|---|
| S0 | pergunta objetivo, público e preferência estética; audita ferramentas | responde | `state.json` |
| S1 | entrega as direções A (editorial, leitura contemplativa) e B (biblioteca, navegação rápida), estruturalmente distintas, com trade-offs | escolhe no chat ("quero a A") | G1 por `chat-quote` (DEC-RFC-002) |
| S2 | propõe a escolha do meio "protótipo HTML local" e depois a baseline `DESIGN-001` | `lfe approve` da decisão de meio e de G2 no terminal | G2 vinculado ao hash |
| S3 | descobre regras (o que salvar, privacidade local) e propõe `SCOPE-001` | `lfe approve G3` | G3 |
| S4 | propõe ADR-001: *local-only* com `localStorage` vs backend mínimo (Python stdlib + arquivo JSON) | `lfe approve G4` | G4 |
| S5–S6 | implementa `app/`; antes disso, o hook nega escrita em `app/` | — | negação registrada |
| S7 | roda testes via `lfe run` | revisa o relatório; `lfe approve G5` | recibos + G5 |
| S8 | prepara checklist de release | **não** autoriza deploy | G6 permanece `not_started` |

## 5. Baseline e requisitos

**Tela UI-001 "Minhas leituras"** (formulário de adicionar + lista), viewports 390×844 e
1280×800, estados `default`, `empty`, `error` (validação) e `error` (armazenamento).

| ID | Requisito | Aceite (Given/When/Then resumido) |
|---|---|---|
| FR-001 | Adicionar leitura com título obrigatório | dado um título válido, ao salvar, o item aparece na lista |
| FR-002 | Persistir a lista | dado um item salvo, ao recarregar, ele continua lá |
| FR-003 | Marcar como concluída | ao marcar, o estado persiste após recarregar |
| FR-004 | Recusar título vazio ou só espaços | nada é salvo e o erro é anunciado (`aria-live`) |
| FR-005 | Falha de armazenamento | se o `localStorage` lançar erro, a interface mostra erro visível e não finge sucesso |
| UX-001 | Teclado | todas as ações principais funcionam com Tab, Enter e Espaço, com foco visível |

Modelo de dados: chave `lfe-vs01:readings:v1`, itens `{id, title, done, createdAt}`.

## 6. Testes

| ID | Tipo | Cobre |
|---|---|---|
| TEST-001 | unit (core) | política: escrita em `app/` negada sem G2–G4 |
| TEST-002 | contract | fixtures válidas e inválidas da RFC-0001 |
| TEST-003 | e2e | FR-001, FR-002, FR-003 |
| TEST-004 | e2e | FR-004, FR-005 (storage bloqueado por script de inicialização) |
| TEST-005 | e2e | UX-001 (jornada só por teclado, dois viewports, screenshots como artefatos) |
| TEST-006 | manual-review | revisão humana de acessibilidade, registrada separadamente |

O Playwright é **opcional e com versão fixada** (a versão exata é definida no PR `test/vs01-e2e` e
gravada no recibo). Sem ele, os recibos E2E ficam `not_executed` e G5 não pode ser aprovado.

## 7. Critérios de aceite

| AC | Prova | Caso de falha obrigatório |
|---|---|---|
| AC-01 | `lfe doctor` lista versões; demo roda com Python ≥3.10, sem conta paga | Python 3.9 → exit 2 com mensagem clara |
| AC-02 | `check-action` em `app/` sem G2–G4 → exit 3, `GATE_NOT_APPROVED`; payload do hook → negação | G3 vinculado a escopo antigo → `GATE_STALE` |
| AC-03 | depois de G1, G2–G6 permanecem inalterados; `chat-quote` não vale para G2 | tentar aprovar dois gates numa entrada → recusado |
| AC-04 | editar o protótipo → G2 e G3 `stale`; `lfe impact DESIGN-001` lista UI → FR → TEST | nova revisão sem decisão não destrava S6 |
| AC-05 | TEST-003 e TEST-004 `pass` | storage bloqueado → erro visível |
| AC-06 | TEST-001, TEST-002 e ao menos um E2E com recibo `pass` | exit 0 com zero testes → `fail` |
| AC-07 | E2E sem Playwright → `not_executed`; `approve G5` → `EVIDENCE_INCOMPLETE` | permissão negada → `blocked` |
| AC-08 | `lfe trace --check` passa só com recibo `pass` para cada FR implementado | FR sem recibo → falha |
| AC-09 | TEST-005 `pass` + TEST-006 registrado à parte | ação inacessível por teclado → `fail` |
| AC-10 | `export` → `import` em outro diretório preserva decisões e hashes | `schemaVersion` desconhecida → exit 4 |
| AC-11 | classes deploy/publish/cost negadas; demo passa com rede bloqueada no teste | pedido de deploy → `DENY_REQUIRES_EXPLICIT_AUTH` |
| AC-12 | `TEST_REPORT` com SHA git e `dirty`; `lfe verify-report` recalcula hashes | artefato alterado depois do recibo → falha |

## 8. Reprodução

- **Guiada:** seguir `DEMO_README.md`; a própria pessoa executa `lfe approve` em cada gate.
- **Replay:** `python3 -m lfe demo vs01 --workdir <tmp>`. Usa decisões `simulated-human`, válidas
  apenas com `mode: demo` e sempre rotuladas "simulado" nos relatórios.

## 9. Limites declarados

Os resultados valem para o ambiente local registrado no recibo. Não provam compatibilidade com
Windows, comportamento de outros hosts de agente, produção, nem conformidade WCAG completa (a
verificação automática cobre teclado e foco; o restante depende de revisão humana).

## 10. Pré-condição operacional

O CI do repositório precisa voltar a executar (em 2026-10-17 os jobs não iniciavam por bloqueio
de cobrança da conta no GitHub). Sem CI, os critérios podem ser demonstrados localmente, mas não
como verificação contínua no PR.
