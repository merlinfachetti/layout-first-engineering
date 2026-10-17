> **ATENÇÃO — projeto já publicado:** `merlinfachetti/layout-first-engineering` já existe e sua branch `main` tem Ruleset ativo. Este guia de **primeira publicação** é histórico e NÃO deve ser executado novamente. Para atualizações use [Comunidade, segurança, privacidade e PR](OPEN-SOURCE-MAINTENANCE.pt-BR.md).

# Publicar Layout-First Engineering no GitHub — macOS

**Objetivo:** criar o repositório público `merlinfachetti/layout-first-engineering` e sua cópia local em `/Users/alden.fachetti/Projects_MerlinFachetti/layout-first-engineering`, com o usuário `merlinfachetti` como autor do commit inicial e **sem `Co-authored-by` de IA**.

## Correção: `scripts/publish-macos.sh: No such file or directory`

O script **existe no ZIP original**, mas só pode ser chamado por um caminho que corresponda ao local da extração. `bash scripts/publish-macos.sh` funciona **apenas** se você estiver dentro da raiz extraída do projeto. Um erro desse tipo não é um erro do GitHub ou da autoria.

No Terminal do Mac, com o ZIP salvo na pasta Downloads, execute **exatamente**:

```bash
cd ~/Downloads
unzip -o layout-first-engineering-github-ready-v0.1.2.zip -d lfe-publish
bash "$HOME/Downloads/lfe-publish/PUBLICAR_NO_GITHUB.command"
```

**Alternativa sem o atalho:**

```bash
bash "$HOME/Downloads/lfe-publish/scripts/publish-macos.sh"
```

### Diagnóstico

```bash
pwd
ls -la "$HOME/Downloads/lfe-publish/scripts"
find "$HOME/Downloads" -name publish-macos.sh -print
```

Se o `unzip` indicar que o arquivo não existe, confira em qual pasta o navegador salvou o ZIP e seu nome exato. Não presuma que o Finder extraiu o arquivo na mesma pasta ou sem um diretório adicional.

## Pré-requisitos

- macOS com `git` e `python3` disponíveis.
- GitHub CLI (`gh`): se usa Homebrew, `brew install gh`.
- Autenticação via `gh auth login` usando **somente** o usuário `merlinfachetti`.
- `gh auth status` deve confirmar que sua sessão está autenticada.
- O diretório de destino ainda não pode existir; o script não sobrescreve arquivos existentes.
- O repositório remoto ainda não pode existir; o script não sobrescreve o GitHub.

## O que acontece após rodar o script

1. Confere macOS e ferramentas necessárias.
2. Confere login e ID da conta GitHub.
3. Confere se fonte, diretório final e repositório remoto estão em condições seguras.
4. Executa verificações da skill.
5. Mostra o local e solicita `PUBLICAR` antes de copiar/criar/publicar.
6. Faz o commit inicial com metadados locais configurados para `Merlin Fachetti <12265786+merlinfachetti@users.noreply.github.com>`.
7. Verifica que a mensagem do commit não tem `Co-authored-by:`.
8. Usa `gh repo create` para criar e enviar o repositório público.

Se houver erro depois da confirmação, confira o estado local e remoto antes de repetir. **Não remova diretórios nem faça force-push para tentar consertar automaticamente.**

## Manutenção após a publicação

Dentro do diretório local já publicado:

```bash
cd /Users/alden.fachetti/Projects_MerlinFachetti/layout-first-engineering
bash scripts/push-update-macos.sh
```

Esse segundo script testa a skill, verifica a conta e a branch, mostra os arquivos alterados, pede confirmação e usa seu usuário para criar o commit. Se o repositório possuir branch protection que exija PR, o push direto pode ser bloqueado; use uma branch e um Pull Request.

**Importante:** apenas o GitHub CLI executado no seu Mac poderá criar o repositório inicial; disponibilizar o ZIP aqui não significa que ele já foi publicado, nem que foi salvo no seu Mac.


> **Já publicou?** Não execute novamente o comando desta página. Consulte o [Manual Mestre — atualização de repositório existente](MANUAL-MESTRE.pt-BR.md#7-como-atualizar-um-repositório-já-publicado).
