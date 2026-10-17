# Guia de manutenção do repositório — @merlinfachetti

**Versão vigente: 0.1.3 — branch `main` protegida.** O repositório já está publicado: **não execute a publicação inicial novamente**.

O guia canônico e atualizado de contribuições, privacidade, regras de proteção, segurança, release e PR está em **[Comunidade, segurança e privacidade](OPEN-SOURCE-MAINTENANCE.pt-BR.md)**. O [Manual Mestre](MANUAL-MESTRE.pt-BR.md) preserva os procedimentos de instalação da skill e o histórico da metodologia.

## Atualizar com o pacote de governança

```bash
cd ~/Downloads
unzip -q layout-first-engineering-community-v0.1.3.zip -d lfe-community-update
bash "$HOME/Downloads/lfe-community-update/ATUALIZAR_GITHUB.command"
```

O script só atua na cópia local `/Users/alden.fachetti/Projects_MerlinFachetti/layout-first-engineering`, valida a conta `merlinfachetti`, preserva o trabalho existente, cria uma branch, executa testes e solicita confirmações antes do commit e do push. Ele **não** faz merge nem release automaticamente.

## Atualizações futuras

Crie uma branch a partir de `main` limpa e atualizada. Edite e teste. Use `bash scripts/push-update-macos.sh` na **branch**, nunca na `main`, para enviar e abrir PR. Confira CI e revisão antes de `Squash and merge`. Rode `git switch main && git pull --ff-only origin main` para atualizar sua cópia local.

## Releases

Atualize versão/CHANGELOG, teste (`python3 -m unittest discover -s tests -v`), construa (`python3 scripts/build_release.py`) e publique o GitHub Release **apenas depois de mesclar o PR na `main`**. Verifique arquivos, tag e autoria antes de publicar. Sem auto-merge, sem commits automatizados e sem trailer `Co-authored-by` de IA nos commits do mantenedor. Contribuidores humanos mantêm crédito próprio.

## Checklist recorrente

- Semanal: Actions, Issues, PRs, relatórios de vulnerabilidades e compatibilidade.
- Mensal: pelo menos um teste real em host/modelo com identificação da versão e conectores.
- Cada release: licence check para novos assets, versão, testes, notas, bugs conhecidos, privacidade e canais de suporte.
