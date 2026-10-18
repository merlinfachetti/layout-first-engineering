# Session hooks — resume where the project stopped / retomar de onde parou

These two Claude Code hooks make a project resumable without asking the user to "save the state":

| Hook | Command | Effect |
|---|---|---|
| `SessionStart` | `lfe hook-session-start` | Injects stage, gate status, production lock, next action, blocking questions and rules into the new session. Silent when the folder has no `.lfe/`. |
| `Stop` | `lfe hook-stop` | Regenerates `.lfe/HANDOFF.md` at the end of every turn. Never blocks the session. |

Add to the project's `.claude/settings.json` (replace `/path/to/layout-first-engineering` with the folder where you cloned LFE):

```json
{
  "hooks": {
    "SessionStart": [
      {"hooks": [{"type": "command",
                  "command": "PYTHONPATH=/path/to/layout-first-engineering/engine python3 -m lfe --root \"$CLAUDE_PROJECT_DIR\" hook-session-start"}]}
    ],
    "Stop": [
      {"hooks": [{"type": "command",
                  "command": "PYTHONPATH=/path/to/layout-first-engineering/engine python3 -m lfe --root \"$CLAUDE_PROJECT_DIR\" hook-stop"}]}
    ]
  }
}
```

Merge these entries with the `PreToolUse` hook from [the action policy adapter](README.md) when both are installed.
A future plugin package will install all hooks in one step.

**PT-BR:** adicione o bloco acima ao `.claude/settings.json` do projeto (trocando o caminho pela pasta onde você clonou o LFE). Ao abrir uma nova sessão, o Claude recebe automaticamente o estágio, os gates, se o código de produção está liberado, a próxima ação e as perguntas bloqueadoras, sem recomeçar a descoberta. Ao fim de cada turno, `.lfe/HANDOFF.md` é atualizado.

What it is not: the injected text is guidance for the assistant. Enforcement of gates comes from the
`PreToolUse` policy hook and from `lfe approve` requiring a person at an interactive terminal.
