# RFC-0001 — Contratos do core LFE v0.1

- **Status:** Proposta (em revisão pelo proprietário)
- **Autor e decisor:** Merlin Fachetti (@merlinfachetti)
- **Data:** 2026-10-17
- **Base auditada:** `main` @ `c780665`
- **Relacionadas:** [RFC-0002 — Primeira fatia vertical](0002-vertical-slice-01.md)
- **Escopo:** formato de dados, invariantes e superfície mínima de CLI. **Esta RFC não implementa
  nada.** Código só entra a partir do PR `feat/contracts-v0.1`, depois da aceitação desta RFC.

Convenção: **DEVE**, **NÃO DEVE**, **DEVERIA** e **PODE** têm o sentido normativo da RFC 2119.
Identificadores técnicos ficam em inglês.

---

## 1. Resumo

O LFE já define um bom método (S0–S9, G1–G6, design antes da stack, humano como piloto). O que
falta é um **núcleo determinístico** que não dependa da obediência textual de um LLM. Esta RFC
define:

1. um diretório canônico `.lfe/` em JSON;
2. sete contratos versionados (`ProjectState`, `GateDecision`, `ExperienceBaseline`,
   `RequirementSet`, `ActionRequest`/`PolicyDecision`, `EvidenceReceipt`, `AgentHandoff`);
3. invariantes testáveis, códigos de motivo e códigos de saída;
4. a ponte com os templates Markdown existentes, sem quebrar o fluxo de quem só usa chat.

Princípio central: **a autoridade vem do canal pelo qual a decisão entrou e do hash do conteúdo
aprovado, nunca do que um arquivo declara sobre si mesmo.**

## 2. Motivação: evidências da auditoria

O único enforcement executável hoje é
[`verify_project.py`](../../layout-first-engineering/scripts/verify_project.py), que lê por regex
a tabela de gates de um `PROJECT_STATE.md` escrito pelo próprio agente (linhas 20–49). Ele é útil
como checagem de sanidade, e esta RFC o preserva. Em seis sondagens executadas em memória contra
o template oficial, o resultado foi este:

| Sonda | Estado submetido | Resultado atual | Invariante desta RFC que passa a reprovar |
|---|---|---|---|
| P1 | S6 com G2–G4 `approved` sem decision ID | PASS (apenas avisos) | D-03, D-05 |
| P2 | G2–G4 `approved` com `DEC-999` inexistente | PASS, sem avisos | D-01, D-05 |
| P3 | Linhas G2–G4 `approved` anexadas ao fim do arquivo | PASS (a última linha vence) | S-02, D-01 |
| P4 | S9 sem G6 | PASS (aviso) | S-04 |
| P5 | G1 `not_started` e G2–G4 `approved` | PASS | D-04 |
| P6 | `Current stage: S3 (Produto)` | FAIL de parsing | (JSON elimina o parser frágil) |

Além disso, não existe: fronteira de ação (nada impede a escrita de código de produção antes de
G2/G3/G4), recibo verificável de teste, vínculo entre aprovação e revisão do design, nem
retomada que não dependa de o usuário pedir "registre o estado".

## 3. Objetivos e não objetivos

**Objetivos**

- O-1. Gates verificados por código, inclusive no momento em que o agente tenta agir.
- O-2. Aprovação amarrada ao conteúdo exato aprovado; mudança material invalida a aprovação.
- O-3. Evidência com formato próprio: sem prova, nunca `pass`.
- O-4. Estado portátil entre sessões, ferramentas e agentes; importar nunca eleva um status.
- O-5. Convivência com os templates Markdown e com o uso só por chat.

**Não objetivos (v0.1)**

- Autenticação criptográfica de pessoas. A v0.1 oferece **detecção** de adulteração e rótulo
  honesto de autenticidade, não prova de identidade.
- Multiusuário, servidor, banco de dados, rede.
- Substituir `SKILL.md`: o método continua nele.

## 4. Decisões já tomadas pelo proprietário

Registradas em 2026-10-17 na sessão de planejamento. A confirmação formal é a aprovação do PR
desta RFC.

| ID | Decisão | Alternativa rejeitada | Motivo |
|---|---|---|---|
| DEC-RFC-001 | Core em **Python ≥3.10, somente biblioteca padrão** | TypeScript/Node 22 | Continuidade com o validador, os testes `unittest` e o CI atuais; zero instalação. Os schemas e fixtures são o contrato neutro, então uma implementação em outra linguagem pode existir se passar na mesma suíte |
| DEC-RFC-002 | Aprovação **híbrida por risco**: G1 pode ser registrado a partir do chat; G2–G6 só por canal humano | Tudo no terminal; tudo pelo chat | Baixo atrito onde o risco é baixo (escolher direção visual) e autenticidade onde a decisão destrava código e deploy |
| DEC-RFC-003 | **JSON canônico em `.lfe/`**, Markdown gerado em blocos marcados | Markdown estruturado como fonte única | Validável, versionável e migrável; evita repetir a fragilidade de parsing (P3, P6) |

## 5. Princípios normativos

- **N-1 Canal + hash.** Uma aprovação só é válida se entrou por um canal aceito para aquele gate
  (D-03) e se o hash de cada artefato do escopo ainda confere (D-05).
- **N-2 Estado armazenado é cache.** O status de um gate é sempre **recalculado** a partir do
  ledger de decisões e dos hashes atuais. Um valor gravado que diverge do cálculo é erro.
- **N-3 Ausência de prova não é sucesso.** Ferramenta ausente, permissão negada ou zero testes
  executados resultam em `not_executed`, `blocked` ou `fail`, nunca em `pass`.
- **N-4 Importar não eleva.** Nenhuma importação, migração ou conversão de Markdown cria uma
  aprovação válida para destravar S6.
- **N-5 Core determinístico.** O core NÃO DEVE chamar LLM nem rede. Toda regra deve ser testável
  offline com `python3 -m unittest`.
- **N-6 Honestidade de autenticidade.** Toda decisão carrega `authenticity`; o valor padrão é
  `host-asserted` (o host afirma, o LFE não prova).

## 6. Layout do diretório `.lfe/`

```text
<projeto>/
  .lfe/
    state.json                 # ProjectState (contém cache de gates; nunca é a autoridade)
    decisions.jsonl            # ledger append-only de propostas e decisões (cadeia de hash)
    policy.json                # classificação de caminhos e comandos por classe de ação
    requirements.json          # RequirementSet (artefato SCOPE-###)
    baselines/
      DESIGN-001.r1.json       # ExperienceBaseline, uma revisão por arquivo
    decisions/
      ADR-001.json             # decisão de arquitetura e envelope de custo (artefato de G4)
    evidence/
      EVID-001.json            # EvidenceReceipt
      EVID-001/                # artefatos do recibo (logs, screenshots, relatórios)
    HANDOFF.md                 # gerado por `lfe handoff`; não editar à mão
  PROJECT_STATE.md             # template existente, com blocos gerados por `lfe render`
```

Regras de caminho (S-01): todo `path` em contratos DEVE ser relativo à raiz do projeto, NÃO DEVE
conter `..` nem ser absoluto, e o arquivo resolvido NÃO DEVE sair da raiz por symlink.

## 7. Tipos comuns

| Tipo | Regra |
|---|---|
| `schemaVersion` | `lfe.<contrato>/<major>.<minor>`, ex.: `lfe.state/0.1` |
| `Sha256` | `sha256:` seguido de 64 caracteres hexadecimais minúsculos |
| `Timestamp` | RFC 3339 em UTC, ex.: `2026-10-17T09:00:00Z` |
| IDs | `G[1-6]`, `S[0-9]`, `DEC-\d{3,}`, `PROP-\d{3,}`, `UI-\d{3,}`, `FR-\d{3,}`, `NFR-\d{3,}`, `SEC-\d{3,}`, `UX-\d{3,}`, `TEST-\d{3,}`, `EVID-\d{3,}`, `DIR-\d{3,}`, `DESIGN-\d{3,}`, `SCOPE-\d{3,}`, `ADR-\d{3,}`, `RC-\d{3,}`, `DEPLOY-\d{3,}` (alinhados com `references/03-product-discovery.md:23`) |
| `projectId` | `^[a-z0-9]+(-[a-z0-9]+)*$` |

**JSON canônico para hash:** UTF-8, chaves ordenadas, sem espaços (`separators=(",", ":")`),
`ensure_ascii=False`. Contratos NÃO DEVEM usar números de ponto flutuante: só inteiros, strings,
booleanos, listas e objetos. Isso mantém o hash idêntico entre linguagens.

**Hash de artefato:** cada artefato lista os arquivos que referencia em `files: [{path, sha256}]`.
O hash do artefato é o SHA-256 do seu JSON canônico (que inclui essa lista). Verificar um
artefato significa recalcular o hash do JSON **e** de cada arquivo listado. Assim, editar o HTML
do protótipo invalida a baseline sem que ninguém precise lembrar de atualizar nada.

## 8. Contratos

### 8.1 `ProjectState` — `.lfe/state.json`

| Campo | Tipo | Obrig. | Regra |
|---|---|---|---|
| `schemaVersion` | string | sim | `lfe.state/0.1` |
| `projectId` | string | sim | padrão de `projectId` |
| `name` | string | sim | não vazio |
| `locale` | string | sim | BCP 47, ex.: `pt-BR` |
| `mode` | enum | sim | `project` ou `demo` |
| `stage` | enum | sim | `S0`…`S9` |
| `artifacts` | objeto | sim | `id → {kind, revision, path, sha256}`; aponta a revisão **corrente** |
| `capabilities` | objeto | não | `nome → {status: available/limited/unavailable/unknown, checkedAt, method, blockedReason}`. Ex.: Figma com cota esgotada → `limited` com motivo; o agente segue por outra frente autorizada (ex.: protótipo HTML local) em vez de repassar tarefas mecânicas ao usuário |
| `gatesCache` | objeto | sim | `G1…G6 → {status, decisionId}`; derivado, nunca autoridade |
| `openQuestions` | lista | não | `{id, stage, question, class: blocker/important/deferred}` |
| `nextAction` | string | sim | uma única próxima ação |
| `updatedAt` | Timestamp | sim | — |

Tipos de artefato e o gate que cada um alimenta:

| `kind` | Prefixo | Gate |
|---|---|---|
| `direction-set` | `DIR-` | G1 |
| `experience-baseline` | `DESIGN-` | G2, G3 |
| `requirements-set` | `SCOPE-` | G3, G4 |
| `architecture-decision` | `ADR-` | G4 |
| `release-candidate` | `RC-` | G5, G6 |
| `deployment-plan` | `DEPLOY-` | G6 |

Invariantes:

- **S-01** caminhos seguros (seção 6).
- **S-02** `gatesCache` NÃO DEVE afirmar uma decisão que o ledger não contém (decisão inexistente,
  outro ID ou outro veredito) → `STATE_CACHE_MISMATCH`. O cache pode ficar atrás de uma mudança de
  arquivo (`approved` que virou `stale`); por isso a comparação é com o ledger, não com os hashes.
- **S-03** **Entrar** em `stage` ≥ S6 exige G2, G3 e G4 válidos → senão `STAGE_GATE_VIOLATION`
  (preserva `SKILL.md:51`). **Permanecer** em S6 com um desses gates `stale` é permitido: o estado
  continua salvável, mas ações de produção são negadas até a reaprovação.
- **S-04** Entrar em `stage` ≥ S8 exige G5 válido; entrar em S9 exige G6 válido ou `not_applicable`
  (corrige a sonda P4). Mesma regra de permanência com gate `stale`.

```json
{
  "schemaVersion": "lfe.state/0.1",
  "projectId": "vs01-leituras",
  "name": "Lista de leituras",
  "locale": "pt-BR",
  "mode": "demo",
  "stage": "S3",
  "artifacts": {
    "DIR-001": {"kind": "direction-set", "revision": 1, "path": ".lfe/directions/DIR-001.r1.json", "sha256": "sha256:…"},
    "DESIGN-001": {"kind": "experience-baseline", "revision": 2, "path": ".lfe/baselines/DESIGN-001.r2.json", "sha256": "sha256:…"}
  },
  "gatesCache": {
    "G1": {"status": "approved", "decisionId": "DEC-001"},
    "G2": {"status": "approved", "decisionId": "DEC-002"},
    "G3": {"status": "proposed", "decisionId": null},
    "G4": {"status": "not_started", "decisionId": null},
    "G5": {"status": "not_started", "decisionId": null},
    "G6": {"status": "not_started", "decisionId": null}
  },
  "nextAction": "Reconciliar regras de privacidade e propor G3",
  "updatedAt": "2026-10-17T09:00:00Z"
}
```

*Exemplo ilustrativo; hashes omitidos.*

### 8.2 `GateDecision` — linhas de `.lfe/decisions.jsonl`

O ledger guarda **propostas** (feitas pelo agente) e **decisões** (feitas por humano), uma por
linha, em ordem.

| Campo | Tipo | Obrig. | Regra |
|---|---|---|---|
| `schemaVersion` | string | sim | `lfe.decision/0.1` |
| `kind` | enum | sim | `proposal` ou `decision` |
| `seq` | inteiro | sim | começa em 1, sem lacunas |
| `id` | string | sim | `PROP-###` para proposta, `DEC-###` para decisão |
| `gate` | enum | sim | **exatamente um** de `G1`…`G6` |
| `verdict` | enum | decisão | `approved`, `rejected`, `revoked`, `not_applicable` |
| `option` | string | não | ex.: `A` (direção escolhida em G1, caso simples) |
| `composition` | objeto | não | G1 híbrido: `{primary, themeVariants[{theme, direction}], complementary[{direction, usage}], nonNegotiables[]}`. Ex.: A como dark padrão, B como light, padrões de C para coleções. É **um único produto e design system**, não três |
| `exceptions` | lista | não | só com `approved`: `[{id: EXC-###, description, owner, mustResolveBefore: G#}]`. Dívida aceita explicitamente; `mustResolveBefore` DEVE ser um gate posterior ao da decisão |
| `scope.artifacts` | lista | sim | `[{id, revision, sha256}]`; tipos exigidos pelo gate (tabela 8.1) |
| `rationale` | string | condicional | obrigatório para `not_applicable` e `revoked` |
| `actorDeclared` | string | decisão | nome declarado de quem decide |
| `channel` | enum | sim | ver D-03 |
| `evidence` | objeto | condicional | `chat-quote`: `{quote, quotedAt}`; G5: `{receipts: [EVID-…]}` |
| `authenticity` | enum | sim | `host-asserted`, `unverified`, `simulated` (`signed` reservado para versões futuras) |
| `at` | Timestamp | sim | — |
| `supersedes` | string/null | não | `DEC-###` substituída |
| `prevHash` | Sha256 | sim | hash da linha anterior; a primeira usa `sha256:` + 64 zeros |
| `hash` | Sha256 | sim | SHA-256 do JSON canônico da linha **sem** o campo `hash` |

Invariantes:

- **D-01 Cadeia íntegra.** `prevHash` de cada linha = `hash` da anterior; qualquer edição,
  remoção ou reordenação → `LEDGER_TAMPERED` (exit 5). Corrige P2 e P3: não existe "última linha
  vence" fora da cadeia.
- **D-02 Um gate por entrada.** Garantido pelo schema (`gate` é string única). Implementa I-02:
  "gostei da opção B" pode, no máximo, virar uma decisão de G1.
- **D-03 Matriz de canais.**

  | Canal | Quem produz | Gates em que uma decisão `approved` vale |
  |---|---|---|
  | `agent` | agente via `lfe propose` | **nenhum** (só propostas) |
  | `chat-quote` | agente registra citação literal do usuário | **somente G1** |
  | `human-cli` | humano em terminal interativo (`lfe approve`) | G1–G6 |
  | `studio-export` | humano no Studio local (versão futura) | G1–G6 |
  | `simulated-human` | `lfe demo` | G1–G6, **somente** com `state.mode = demo` |
  | `imported-legacy` | `lfe import-md` | **nenhum** para destravar S6+ (I-08) |

- **D-04 Ordem.** Uma decisão `approved` para G*n* exige G*n−1* válido (ou `not_applicable`)
  no momento da decisão, e a validade é reavaliada a cada consulta. Corrige P5.
  `not_applicable` é aceito na v0.1 **apenas para G1** (produto existente com design
  estabelecido, `references/01-conversation-and-state.md:51`) **e para G6** (projeto sem deploy).
  G2–G5 nunca são dispensáveis para entrar em S6.
- **D-05 Vínculo com o conteúdo.** Uma decisão `approved` é válida somente se, para cada item de
  `scope.artifacts`, `revision` e `sha256` coincidem com `state.artifacts[id]` **e** o arquivo em
  disco recalcula para o mesmo hash. Caso contrário, o status calculado é `stale`.
- **D-06 Evidência para G5.** `approved` em G5 exige que todo requisito com status `implemented`
  tenha ao menos um `EvidenceReceipt` `pass` de um teste que o cobre, com `sourceRevision.dirty =
  false`. Caso contrário → `EVIDENCE_INCOMPLETE`.
- **D-07 Última decisão vence, dentro da cadeia.** Para cada gate vale a última decisão em
  ordem de `seq`; `revoked` torna o gate não aprovado.
- **D-08 Rótulo de simulação.** Decisões `simulated-human` DEVEM aparecer como "simulado" em todo
  relatório e handoff.
- **D-09 Aprovação com exceções.** Um gate aprovado com `exceptions` é válido para avançar, mas
  cada exceção aberta bloqueia o gate indicado em `mustResolveBefore` até ser resolvida por nova
  decisão humana. Ex.: G2 aprovado com "click-through ainda não testado" (`mustResolveBefore: G5`)
  permite S3, mas impede G5. Nunca autoriza produção antes de G3/G4.

Cascata de invalidação (I-04): como G3 inclui `DESIGN-` e `SCOPE-`, G4 inclui `SCOPE-` e `ADR-`,
e G6 inclui `RC-` e `DEPLOY-`, uma mudança de baseline torna G2 e G3 `stale` automaticamente, e uma
mudança de escopo torna G3 e G4 `stale`. `lfe impact <ARTIFACT-ID>` lista os gates cujo escopo
contém o artefato e os requisitos e testes ligados a ele. A reabertura é sempre decisão humana.

### 8.3 `ExperienceBaseline` — `.lfe/baselines/DESIGN-###.rN.json`

| Campo | Regra |
|---|---|
| `schemaVersion` | `lfe.baseline/0.1` |
| `id`, `revision` | `DESIGN-###`, inteiro ≥ 1 |
| `medium` | `local-html`, `figma`, `penpot`, `image` ou `spec`. Para `local-html`, DEVE referenciar a decisão que escolheu protótipo codificado (`SKILL.md:55`, `references/01-conversation-and-state.md:53`) |
| `fidelity` | `moodboard`, `static-layout`, `editable-frames` ou `interactive-prototype`. `interactive-prototype` só com evidência de interação executada; um frame editável no Figma **não** é protótipo interativo |
| `screens[]` | `{screenId: UI-###, name, goal, states[], viewports[{width, height}], prototype: {path, query}, preview: {path}}`. `preview` é uma imagem local versionada, para a revisão ser visual e não só descritiva |
| `states` | subconjunto de `default`, `empty`, `loading`, `error`, `success`, `disabled` |
| `tokens` | `{path}` para um arquivo no formato do W3C Design Tokens Community Group (subconjunto `$value`/`$type`; versão estável a confirmar na implementação) |
| `flows[]` | `{id, steps: [UI-###]}` |
| `provenance[]` | `{asset, source, license}` para todo conteúdo de terceiros |
| `files[]` | `{path, sha256}` de todo arquivo referenciado |

Invariantes: **B-01** toda tela com entrada de dados declara `default`, `empty` e `error`
(aviso na v0.1, erro a partir da v0.2); **B-02** todo arquivo de `files[]` existe e confere o hash;
**B-03** caminhos seguros (S-01).

### 8.4 `RequirementSet` — `.lfe/requirements.json` (artefato `SCOPE-###`)

| Campo | Regra |
|---|---|
| `schemaVersion` | `lfe.requirements/0.1` |
| `id`, `revision` | `SCOPE-###`, inteiro ≥ 1 |
| `items[]` | `{id: FR/NFR/SEC/UX-###, title, acceptance: [{given, when, then}], priority: must/should/could/wont, uiRefs[], testRefs[], status: proposed/approved/implemented/verified}` |
| `tests[]` | `{id: TEST-###, kind: unit/contract/e2e/manual-review, argv[], requires[], covers[]}` |

Invariantes: **R-01** IDs únicos; **R-02** todo `uiRefs` existe na baseline corrente; **R-03**
item `implemented` tem `testRefs` não vazio; **R-04** `lfe trace --check` falha se um item
`implemented` não tem ao menos um recibo `pass` de um teste que o cobre (AC-08).

### 8.5 `ActionRequest` e `PolicyDecision`

O core classifica cada ação do agente em uma **classe** e decide.

`policy.json` (`lfe.policy/0.1`) mapeia `pathClasses: [{glob, class}]` e
`commandClasses: [{pattern, class}]`. Caminho ou comando não classificado vale como
`production_code` (padrão conservador).

| Classe | Regra para o agente na v0.1 | Código de negação |
|---|---|---|
| `docs` | permitido | — |
| `prototype` | permitido em qualquer estágio; nunca conta como produção | — |
| `lfe_state` (escrita direta em `.lfe/state.json`, `decisions.jsonl`, `evidence/`) | **sempre negado**; usar a CLI | `PROTECTED_STATE` |
| `lfe_human_command` (`lfe approve`, `reject`, `revoke`) | **sempre negado** | `HUMAN_CHANNEL_REQUIRED` |
| `production_code` | permitido só com estágio ≥ S6 e G2, G3, G4 válidos | `GATE_NOT_APPROVED` ou `GATE_STALE` |
| `deploy`, `publish`, `cost`, `delete`, `secret` | **sempre negado** ao agente na v0.1, mesmo com G6 (I-07) | `DENY_REQUIRES_EXPLICIT_AUTH` |

```json
{"schemaVersion": "lfe.action/0.1", "actor": "agent", "tool": "Write",
 "targets": ["app/src/store.js"], "command": null}
```

```json
{"schemaVersion": "lfe.policy-decision/0.1", "allowed": false,
 "class": "production_code", "reasonCode": "GATE_NOT_APPROVED",
 "message": "S6 exige G3 aprovado e válido para SCOPE-001@1.",
 "missing": ["G3"], "evaluatedAt": "2026-10-17T09:00:00Z"}
```

Leitura de arquivos nunca passa pela política. A classificação de comandos Bash é **heurística**
(um comando pode escrever arquivos por caminhos indiretos). Ela é uma camada de defesa, e a
integridade do ledger (D-01) é a camada de detecção.

### 8.6 `EvidenceReceipt` — `.lfe/evidence/EVID-###.json`

| Campo | Regra |
|---|---|
| `schemaVersion` | `lfe.evidence/0.1` |
| `id`, `testId`, `requirementIds[]` | IDs ligados ao `RequirementSet` |
| `argv[]`, `cwd` | comando efetivamente executado, **sem shell** |
| `environment` | `{os, osRelease, python, tools: {nome: versão}}`; somente lista permitida, nunca variáveis de ambiente arbitrárias |
| `sourceRevision` | `{git: sha ou null, dirty: bool}` |
| `startedAt`, `durationMs`, `exitCode` | inteiros e timestamp |
| `testsRun`, `testsSkipped` | inteiros extraídos da saída do runner |
| `status` | `pass`, `fail`, `blocked`, `skipped`, `not_executed` |
| `reason` | obrigatório quando `status` ≠ `pass` |
| `artifacts[]` | `{path, sha256}` (logs, screenshots, relatórios) |
| `limitations[]` | ex.: "ambiente local; não representa produção" |
| `producer` | `lfe-run/0.1` |

Invariantes:

- **E-01** `pass` exige `exitCode = 0`, `testsRun > 0` e `testsSkipped = 0`. Exit 0 com zero
  testes é `fail` (prática adotada do AI Engineering from Scratch, `projects/AUTHORING.md`).
- **E-02** Executável ausente → `not_executed` com `reason: tool_unavailable:<nome>` (I-06, AC-07).
  Permissão negada → `blocked`. Timeout → `fail`.
- **E-03** Recibo com `dirty = true` NÃO DEVE satisfazer D-06.
- **E-04** `lfe verify-report` recalcula o hash de todo artefato; divergência → `EVIDENCE_TAMPERED`.
- **E-05** Sem segredos: `argv` que case com padrões de credencial (`token=`, `password=`,
  `api_key=`, prefixos conhecidos de chaves) é recusado com `SECRET_IN_ARGV`; logs passam por
  redação antes de serem gravados.

### 8.7 `AgentHandoff` — gerado por `lfe handoff`

`lfe.handoff/0.1`, gerado, **nunca escrito à mão** (I-10): `projectId`, `stage`, `gates[]` com
`{gate, status calculado, decisionId, boundTo[], staleReason}`, `openQuestions[]`, `lastReceipts[]`,
`nextAction`, `prohibitions[]` (ex.: "não escrever em `app/` antes de G4"), `ledgerHead` (hash da
última linha), `generatedAt`. Também gera `.lfe/HANDOFF.md` legível, no idioma de `state.locale`.

## 9. Superfície mínima da CLI

Invocação: `python3 -m lfe <comando>` a partir do pacote `engine/lfe/` (o caminho exato de
importação é decidido no PR `feat/contracts-v0.1`).

| Comando | Quem pode | Efeito |
|---|---|---|
| `init` | humano ou agente | cria `.lfe/` vazio e válido |
| `status [--brief] [--json]` | qualquer um | estado calculado, gates `stale`, próxima ação |
| `propose <G> --artifact ID@rev…` | agente | grava proposta (`channel: agent`) |
| `approve <G> [--option X]` / `reject` / `revoke` | **só humano** | exige TTY; mostra o que será aprovado, o que destrava e o que **não** destrava; pede para digitar o gate |
| `record-chat-approval G1 --quote "…"` | agente | única exceção da DEC-RFC-002, só para G1 |
| `check-action` / `hook pre-tool-use` | hook | lê `ActionRequest` ou payload do host e responde `PolicyDecision` |
| `run <TEST-ID> -- <argv…>` | qualquer um | executa sem shell e grava `EvidenceReceipt` |
| `trace [--check]`, `impact <ID>` | qualquer um | rastreabilidade e análise de impacto |
| `export` / `import` | qualquer um | pacote portátil; import nunca eleva |
| `handoff`, `render`, `import-md`, `doctor`, `verify-report` | qualquer um | ver seções 8.7, 10 e RFC-0002 |

Códigos de saída: `0` ok ou permitido; `1` erro interno; `2` uso ou ambiente inválido;
`3` ação negada pela política; `4` `INCOMPATIBLE_SCHEMA`; `5` integridade violada
(`LEDGER_TAMPERED`, `EVIDENCE_TAMPERED`); `6` documento viola o contrato (`lfe validate`).

`approve` sem terminal interativo responde `CHANNEL_NOT_INTERACTIVE` (exit 2). É a primeira
barreira contra autoaprovação; a regra `lfe_human_command` do hook é a segunda.

## 10. Convivência com os templates Markdown

- Os templates de [`assets/`](../../layout-first-engineering/assets/) **permanecem** e continuam
  sendo o caminho de quem usa só chat ou um host sem execução de código.
- Com a CLI presente, `.lfe/` é a fonte de verdade. `lfe render` reescreve **apenas** blocos
  delimitados por `<!-- lfe:begin gates -->` e `<!-- lfe:end gates -->` em `PROJECT_STATE.md`,
  mantendo o formato de tabela de seis colunas e todo o texto humano fora dos blocos.
- Mapeamento de status calculado para o vocabulário existente (`SKILL.md:36`):

  | Calculado | Renderizado no Markdown |
  |---|---|
  | `approved` | `approved` |
  | `stale` | `needs_revision`, com "stale: hash divergente" na coluna Evidence |
  | `not_applicable` | `not_applicable` (status adicionado de forma aditiva ao validador legado no PR `feat/md-bridge`) |
  | `proposed` | `proposed` |
  | sem registro | `not_started` |

- **Teste de compatibilidade obrigatório:** todo `PROJECT_STATE.md` renderizado DEVE continuar
  passando em `verify_project.py`.
- `lfe import-md PROJECT_STATE.md` reaproveita a lógica de parsing do validador legado e grava cada
  `approved` como decisão `channel: imported-legacy`, `authenticity: unverified`. Essas decisões
  aparecem como "reconfirmar" e **nunca** destravam S6 (N-4).
  - *Nota de implementação (PR-7).* Uma decisão importada não tem artefato registrado a vincular,
    então `scope.artifacts` vazio é aceito **somente** com `channel: imported-legacy` (os dados
    legados vão em `scope.notes`); qualquer outra aprovação com escopo vazio continua
    `EMPTY_SCOPE`. Como importadas nunca são válidas, o estágio importado é rebaixado ao maior
    estágio que os gates calculados permitem (na prática, S6+ vira S5) e a pendência de
    reconfirmação vai para `nextAction`. Um gate que já tem decisão no ledger não é importado, para
    que um import nunca substitua uma decisão humana.
- `SKILL.md` receberá cerca de cinco linhas: "se o comando `lfe` estiver disponível, ele é a fonte
  de verdade do estado; use-o em vez de editar a tabela à mão".

## 11. Versionamento e migração

- Leitores aceitam o mesmo *major* e *minor* menor ou igual ao conhecido; qualquer outro valor →
  `INCOMPATIBLE_SCHEMA` com mensagem clara (AC-10).
- Migração só por comando explícito (`lfe migrate`, versão futura), nunca silenciosa, e nunca eleva
  status.
- Mudança incompatível em contrato exige nova RFC.

## 12. Considerações de segurança

| Ameaça | Mitigação v0.1 | Risco residual |
|---|---|---|
| Agente se autoaprova | TTY obrigatório em `approve`; hook nega `lfe_human_command` e escrita em `lfe_state`; `chat-quote` vale só para G1 | Agente com shell irrestrito ainda pode forjar arquivos; a cadeia de hash e o git tornam isso **detectável**, não impossível |
| Linhas anexadas ou editadas (P3) | D-01 | — |
| Aprovação reaproveitada após mudança | D-05 e cascata | — |
| Instrução maliciosa dentro de design, issue ou página | Conteúdo de artefato nunca é interpretado como comando pelo core (I-09); a política só lê metadados estruturados | Comportamento do LLM medido em evals (PR `test/agent-evals`) |
| Segredo em recibo ou log | E-05, ambiente por lista permitida | Padrões de detecção não são exaustivos |
| Path traversal ou symlink | S-01 | — |
| Falha do próprio core | Hook falha fechado (nega) para classes de escrita, aberto para leitura | Pode interromper a sessão; mensagem explica como seguir |

## 13. Plano de testes dos contratos

- Fixtures em `contracts/fixtures/<contrato>/valid/*.json` e
  `contracts/fixtures/<contrato>/invalid/<CODIGO>__descricao.json`; o nome do arquivo inválido
  declara o código de erro esperado.
- No mínimo cinco casos por contrato: entrada comum, borda, malformada, adversarial e um caso
  separado das fixtures de demonstração (prática do AI Engineering from Scratch).
- As sondagens P1–P5 viram testes negativos permanentes.
- Os 13 testes atuais continuam passando sem alteração.

## 14. Alternativas consideradas

As alternativas de linguagem, formato e canal estão na seção 4. Também foram descartadas para a
v0.1: assinatura criptográfica obrigatória (atrito alto para iniciantes; fica como opção futura
com `ssh-keygen -Y sign`, offline); servidor local para aprovações (superfície maior; o Studio
virá depois e só leitura primeiro); MCP próprio (desnecessário enquanto hooks e CLI resolvem).

## 15. Questões abertas (não bloqueantes)

1. Formato exato do payload e da resposta dos hooks `PreToolUse` e `SessionStart` na versão do
   Claude Code em uso (2.1.221 na máquina do proprietário). Verificar com uma sessão real no PR
   `feat/policy-check-action`; se não for verificável, registrar `not_executed`.
2. Confirmar que comandos executados pela ferramenta Bash do Claude Code não têm TTY (premissa da
   primeira barreira de `approve`).
3. Versão estável vigente do formato do W3C Design Tokens Community Group.
4. Suporte a Windows (caminhos e TTY), fora do primeiro marco.

## 16. Relação com o candidato v0.1.4-rc.1 e com o piloto real

O proprietário preparou fora da `main` um candidato `v0.1.4-rc.1` (patch + pacotes), a partir do
primeiro piloto real da skill (projeto privado, executado com Codex e Figma). Ele aplica limpo
sobre `c780665` (`git apply --check`) e **não conflita** com esta RFC: os dois trilhos se
complementam.

| Trilho | O que resolve | Onde vive |
|---|---|---|
| **Método (rc.1)** | O que o agente DEVE fazer: baseline visual G1 com imagens, protocolo de repositório, contratos de interação, diagnóstico de CI, inventário de direitos, cenários de avaliação | `SKILL.md`, `references/07`, `assets/*.md`, `tests/evals/scenarios.json` |
| **Core (esta RFC)** | O que o agente NÃO CONSEGUE fazer sem o humano: gates verificados por hash e canal, negação na fronteira de ação, recibos de evidência | `.lfe/`, `contracts/`, `engine/lfe/` |

Correspondências usadas para manter um vocabulário só:

| rc.1 | Contrato desta RFC |
|---|---|
| `APPROVED_VISUAL_BASELINE.md` + `verify_visual_baseline.py` | `ExperienceBaseline` com `fidelity`, `screens[].preview` e `files[]` com hash; o Markdown passa a ser uma visão gerada |
| Classificação `moodboard / static layout / editable frames / interactive prototype (verified)` | campo `fidelity` (8.3) |
| G1 híbrido (direção principal, temas, padrões complementares) | `GateDecision.composition` (8.2) |
| G2 aprovado com pendências (laboratório v0.3, LFE-015) | `GateDecision.exceptions` + D-09 |
| Bloqueio de ferramenta com recuperação (LFE-013) | `capabilities.*.status = limited` + `blockedReason` |
| Ledger `intent → authorization → execution → verification` de `REPOSITORY_STATE.md` | mesmo princípio de `EvidenceReceipt`; um contrato próprio de ação de repositório fica para versão futura, reaproveitando os estados `planned / prepared / local_commit / remote_branch / pr_open / merged / synced / failed / blocked` |
| `tests/evals/scenarios.json` (especificações, não resultados) | evals comportamentais do PR `test/agent-evals`; resultados viram recibos |

Dados privados do piloto (nomes, caminhos, links de Figma) NÃO DEVEM entrar no repositório
público sem consentimento explícito do proprietário.
