# Claude Code adapter — action policy / política de ações

> **Easiest path / caminho mais fácil:** install the Claude Code plugin (`claude plugin install lfe@layout-first-engineering`, see the README); it ships these hooks already configured. The manual setup below is for projects that copy the skill folder instead.

[Português](#português) · [English](#english)

---

## Português

Este adaptador liga o Claude Code à política de ações do LFE (RFC-0001, seção 8.5). Antes de cada
`Write`, `Edit`, `MultiEdit`, `NotebookEdit` ou `Bash`, o hook `PreToolUse` pergunta ao core se a
ação é permitida. Se não for, o Claude recebe a negação com o motivo e a ação não acontece.

O que fica bloqueado para o agente:

| Classe | Exemplos | Regra na v0.1 | Código |
|---|---|---|---|
| `docs` | `docs/**`, `*.md`, artefatos em `.lfe/` (baselines, requisitos, ADR), `ls`, `git status`, `lfe status`, `lfe propose` | permitido | — |
| `prototype` | `prototype/**`, `directions/**` | permitido em qualquer estágio | — |
| `lfe_state` | `.lfe/state.json`, `.lfe/decisions.jsonl`, `.lfe/evidence/**`, `.lfe/policy.json`, `.lfe/HANDOFF.md`, `.claude/settings*.json` | sempre negado; use a CLI | `PROTECTED_STATE` |
| `lfe_human_command` | `lfe approve`, `reject`, `revoke` (também via `python3 -m lfe`) | sempre negado | `HUMAN_CHANNEL_REQUIRED` |
| `production_code` | tudo que não foi classificado (ex.: `app/x.js`, `node app.js`) | só em S6+ com G2, G3 e G4 válidos | `GATE_NOT_APPROVED`, `GATE_STALE`, `STAGE_NOT_REACHED` |
| `deploy`, `publish`, `cost`, `delete`, `secret` | `vercel deploy`, `npm publish`, `gh release create`, `aws …`, `rm -rf`, `git push --force`, `.env` | sempre negado, mesmo com G6 | `DENY_REQUIRES_EXPLICIT_AUTH` |

### Instalação passo a passo

1. **Pré-requisitos:** Python 3.10 ou mais novo e o Claude Code instalados. Verificado com
   Claude Code 2.1.221 no macOS.
2. **Clone o LFE** numa pasta fixa, por exemplo `~/tools/layout-first-engineering`.
3. **Inicialize o projeto** (na raiz do *seu* projeto, não do LFE):

   ```bash
   PYTHONPATH=~/tools/layout-first-engineering/engine python3 -m lfe init meu-projeto "Meu projeto"
   ```

4. **Copie o modelo** de configuração para o projeto:

   ```bash
   mkdir -p .claude && cp ~/tools/layout-first-engineering/adapters/claude-code/settings.template.json .claude/settings.json
   ```

   Se o projeto já tiver `.claude/settings.json`, junte as chaves `permissions.deny` e `hooks` à mão.
5. **Troque o caminho** `/path/to/layout-first-engineering` pelo caminho absoluto da pasta do passo 2
   (são três ocorrências: `PreToolUse`, `SessionStart` e `Stop`).
6. **Teste o hook sem abrir o Claude**, simulando uma escrita em `app/`:

   ```bash
   echo "{\"tool_name\":\"Write\",\"tool_input\":{\"file_path\":\"$PWD/app/x.js\",\"content\":\"\"}}" | PYTHONPATH=~/tools/layout-first-engineering/engine python3 -m lfe --root "$PWD" hook-pre-tool-use
   ```

   A saída deve conter `"permissionDecision": "deny"` e `GATE_NOT_APPROVED`.
7. **Abra o Claude Code** no projeto. Peça para criar `app/x.js`: a escrita será negada até você
   aprovar G2, G3 e G4 com `lfe approve` no seu terminal e o projeto chegar a S6 (`lfe stage S6`).

Os hooks `SessionStart` e `Stop` do mesmo modelo retomam o projeto de onde parou; veja
[session-hooks.md](session-hooks.md).

### Como o adaptador decide

- **Permitido:** o hook não imprime nada. O fluxo normal de permissões do Claude Code continua
  valendo; o hook só tira permissões, nunca concede.
- **Negado:** o hook responde no formato oficial
  `{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": "…"}}`
  e o motivo é mostrado ao Claude.
- **Sem `.lfe/`:** o hook permite tudo (o LFE não está em uso naquela pasta).
- **Erro interno:** para ferramentas de escrita, o hook nega (falha fechado). O `|| exit 2` do
  modelo cobre o caso em que o próprio Python não inicia (caminho errado, por exemplo): o código 2
  bloqueia a ação em vez de deixá-la passar.
- **`permissions.deny`:** uma segunda barreira, do próprio Claude Code, contra edição direta dos
  arquivos protegidos. Regras `Edit(...)` valem para todas as ferramentas que editam arquivos,
  inclusive `Write`; regras `Write(...)` não são consultadas pelo Claude Code.

### Ajustar a política do projeto

Sem `.lfe/policy.json`, vale a política padrão (`lfe show-policy` mostra). Para personalizar,
**a própria pessoa** cria o arquivo; o agente não pode escrevê-lo:

```bash
PYTHONPATH=~/tools/layout-first-engineering/engine python3 -m lfe show-policy > .lfe/policy.json
```

Regras: `pathClasses` usa globs relativos à raiz (`*` dentro de um segmento, `**` entre segmentos,
sem diferenciar maiúsculas); `commandClasses` usa expressões regulares procuradas no comando.
Quando várias regras casam, vence a classe mais restritiva. As regras embutidas (estado, ledger,
evidências, a própria política, comandos humanos e deploy/publish/cost/delete/secret) valem sempre,
mesmo que o arquivo não as repita.

### Limites conhecidos

- A classificação de comandos `Bash` é **heurística**: um comando pode escrever por caminhos
  indiretos (um script, `python -c`). É uma camada de defesa; a cadeia de hash do ledger e o git
  são a camada de detecção (RFC-0001, 8.5 e 12).
- Comandos `Bash` não classificados contam como `production_code`, então antes de S6 só passam os
  comandos de leitura e os comandos `lfe` do agente. Isso é intencional (padrão conservador).
- Ler arquivos nunca passa pela política.

---

## English

This adapter connects Claude Code to the LFE action policy (RFC-0001, section 8.5). Before every
`Write`, `Edit`, `MultiEdit`, `NotebookEdit` or `Bash` call, the `PreToolUse` hook asks the core
whether the action is allowed. If it is not, Claude receives the denial with its reason and the
action does not happen.

| Class | Examples | v0.1 rule | Code |
|---|---|---|---|
| `docs` | `docs/**`, `*.md`, artifacts in `.lfe/` (baselines, requirements, ADR), `ls`, `git status`, `lfe status`, `lfe propose` | allowed | — |
| `prototype` | `prototype/**`, `directions/**` | allowed at any stage | — |
| `lfe_state` | `.lfe/state.json`, `.lfe/decisions.jsonl`, `.lfe/evidence/**`, `.lfe/policy.json`, `.lfe/HANDOFF.md`, `.claude/settings*.json` | always denied; use the CLI | `PROTECTED_STATE` |
| `lfe_human_command` | `lfe approve`, `reject`, `revoke` (also through `python3 -m lfe`) | always denied | `HUMAN_CHANNEL_REQUIRED` |
| `production_code` | anything not classified (e.g. `app/x.js`, `node app.js`) | only at S6+ with G2, G3 and G4 valid | `GATE_NOT_APPROVED`, `GATE_STALE`, `STAGE_NOT_REACHED` |
| `deploy`, `publish`, `cost`, `delete`, `secret` | `vercel deploy`, `npm publish`, `gh release create`, `aws …`, `rm -rf`, `git push --force`, `.env` | always denied, even with G6 | `DENY_REQUIRES_EXPLICIT_AUTH` |

### Step-by-step installation

1. **Requirements:** Python 3.10 or newer and Claude Code. Verified with Claude Code 2.1.221 on macOS.
2. **Clone LFE** into a fixed folder, for example `~/tools/layout-first-engineering`.
3. **Initialize your project** (at the root of *your* project, not LFE's):

   ```bash
   PYTHONPATH=~/tools/layout-first-engineering/engine python3 -m lfe init my-project "My project"
   ```

4. **Copy the template** into the project:

   ```bash
   mkdir -p .claude && cp ~/tools/layout-first-engineering/adapters/claude-code/settings.template.json .claude/settings.json
   ```

   If the project already has `.claude/settings.json`, merge the `permissions.deny` and `hooks` keys by hand.
5. **Replace** `/path/to/layout-first-engineering` with the absolute path from step 2 (three
   occurrences: `PreToolUse`, `SessionStart` and `Stop`).
6. **Test the hook without Claude**, simulating a write to `app/`:

   ```bash
   echo "{\"tool_name\":\"Write\",\"tool_input\":{\"file_path\":\"$PWD/app/x.js\",\"content\":\"\"}}" | PYTHONPATH=~/tools/layout-first-engineering/engine python3 -m lfe --root "$PWD" hook-pre-tool-use
   ```

   The output must contain `"permissionDecision": "deny"` and `GATE_NOT_APPROVED`.
7. **Open Claude Code** in the project and ask it to create `app/x.js`: the write is denied until you
   approve G2, G3 and G4 with `lfe approve` in your own terminal and the project reaches S6 (`lfe stage S6`).

The `SessionStart` and `Stop` hooks in the same template resume the project where it stopped; see
[session-hooks.md](session-hooks.md).

### How the adapter decides

- **Allowed:** the hook prints nothing, so Claude Code's normal permission flow still applies. The
  hook only takes permissions away; it never grants them.
- **Denied:** the hook answers in the official format
  `{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": "…"}}`;
  the reason is shown to Claude.
- **No `.lfe/`:** the hook allows everything (LFE is not in use in that folder).
- **Internal error:** for writing tools the hook denies (fail closed). The template's `|| exit 2`
  covers the case where Python itself does not start (wrong path, for example): exit code 2 blocks
  the action instead of letting it through.
- **`permissions.deny`:** a second barrier, enforced by Claude Code itself, against editing the
  protected files directly. `Edit(...)` rules apply to every file-editing tool, `Write` included;
  `Write(...)` rules are never consulted by Claude Code.

### Customizing the project policy

Without `.lfe/policy.json` the default policy applies (`lfe show-policy` prints it). To customize it,
**the person** creates the file; the agent cannot write it:

```bash
PYTHONPATH=~/tools/layout-first-engineering/engine python3 -m lfe show-policy > .lfe/policy.json
```

`pathClasses` take project-relative globs (`*` within one segment, `**` across segments,
case-insensitive); `commandClasses` take regular expressions searched in the command. When several
rules match, the most restrictive class wins. Built-in rules (state, ledger, evidence, the policy
itself, human commands and deploy/publish/cost/delete/secret) always apply, even if the file does not
repeat them.

### Known limits

- `Bash` classification is **heuristic**: a command can write through indirect paths (a script,
  `python -c`). It is a defence layer; the ledger hash chain and git are the detection layer
  (RFC-0001, 8.5 and 12).
- Unclassified `Bash` commands count as `production_code`, so before S6 only read-only commands and
  the agent's own `lfe` commands pass. This is intentional (conservative default).
- Reading files never goes through the policy.
