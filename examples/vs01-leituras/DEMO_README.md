# VS-01 Lista de leituras: demo guiada

Esta pasta é a primeira fatia vertical do Layout-First Engineering
([RFC-0002](../../docs/rfcs/0002-vertical-slice-01.md)). Ela mostra, num produto pequeno e
offline, a cadeia **visual → contrato → aprovação → implementação → teste**, com cada decisão
gravada num ledger encadeado por hash.

O estado vem **sem nenhuma aprovação**. O agente fez a parte dele: entregou duas direções, um
protótipo, a baseline, os requisitos e o ADR, e propôs G1 a G4. Quem aprova é você, no seu
terminal.

## O que tem aqui

| Caminho | O que é |
|---|---|
| `directions/A-editorial.html` | Direção A, **Sumário**: coluna única, a lista composta como o sumário de um livro |
| `directions/B-biblioteca.html` | Direção B, **Fichário**: busca, estantes, índice A–Z e fichas catalográficas |
| `prototype/index.html` | Protótipo da direção A com os estados `?state=default`, `empty`, `error` e `storage-error` |
| `prototype/tokens.json` | Tokens no formato W3C Design Tokens (subconjunto `$value`/`$type`, com aliases) |
| `prototype/previews/` | Capturas do protótipo em 390×844 e 1280×800 |
| `app/` | O app em HTML, CSS e JavaScript, sem dependências e sem rede |
| `.lfe/` | Estado, ledger, baseline `DESIGN-001`, requisitos `SCOPE-001`, direções `DIR-001`, `ADR-001` |
| `project.json` | Manifesto: estágios, o que está pronto e o que está pendente |

Todos os títulos, datas e textos são fictícios, escritos para esta demo.

## Antes de começar

- Python 3.10 ou mais novo (só a biblioteca padrão).
- Um navegador atual. Nada é baixado da internet.
- Um terminal interativo de verdade: `lfe approve` recusa rodar sem um (é a primeira barreira
  contra um agente aprovar a si mesmo).

Trabalhe numa cópia, para o repositório continuar limpo. Na raiz do repositório:

```bash
export PYTHONPATH="$PWD/engine"
```

```bash
DEMO="$(mktemp -d)/vs01" && cp -R examples/vs01-leituras "$DEMO" && cd "$DEMO"
```

Daqui em diante, todo comando roda dentro de `$DEMO`.

## Passo 1: ver onde o projeto parou

```bash
python3 -m lfe status
```

Você vê G1 a G4 como `proposed`, G5 e G6 como `not_started` e `production code: locked`.
Nenhum gate está aprovado: as propostas `PROP-001` a `PROP-004` estão no ledger, cada uma presa
ao hash exato dos arquivos que você vai revisar.

## Passo 2: escolher a direção (G1)

Abra `directions/A-editorial.html` e `directions/B-biblioteca.html` no navegador. As duas têm,
no fim da página, um bloco de trade-offs. Compare a estrutura, não só a cor: A é uma coluna de
leitura; B é uma ferramenta de busca.

Numa sessão real, você responde no chat ("quero a A") e o agente registra a sua frase literal.
Aqui, você mesmo faz esse registro:

```bash
python3 -m lfe record-chat-approval G1 --quote "quero a A" --option A
```

Saída: `DEC-001 recorded from chat quote: G1 approved (authenticity: unverified)`. Uma citação de
chat só vale para G1. Tentar o mesmo para G2 é recusado com `CHANNEL_NOT_ALLOWED`.

> O protótipo já está na direção A, como no roteiro da RFC-0002. Se você escolher B, o caminho
> correto é rejeitar G2 (`lfe reject G2 --rationale "..."`) e pedir um novo protótipo.

## Passo 3: revisar o protótipo e aprovar G2

Abra `prototype/index.html`. A barra no topo troca entre os estados:

- `?state=default`: seis leituras, duas lidas;
- `?state=empty`: a lista vazia, com o convite para o primeiro título;
- `?state=error`: o erro de título vazio sob o campo;
- `?state=storage-error`: o aviso de que o navegador recusou a gravação.

As mesmas telas estão em `prototype/previews/`. Se estiver tudo certo:

```bash
python3 -m lfe approve G2 --option local-html
```

O comando mostra o que você está aprovando (o hash de `DESIGN-001`) e pede que você digite `G2`.
A decisão vira `DEC-002`, que é o número que a baseline já cita em `mediumDecisionId`: aprovar
G2 com `--option local-html` é também escolher o protótipo HTML local como meio.

## Passo 4: aprovar o escopo (G3)

Leia `.lfe/requirements.json`: FR-001 a FR-005, UX-001, SEC-001 e NFR-001, cada um com critério
de aceite e os testes TEST-001 a TEST-006 que o cobrem.

```bash
python3 -m lfe approve G3
```

## Passo 5: aprovar a arquitetura (G4)

Leia `.lfe/adr/ADR-001.md`: local-only com `localStorage` contra um backend mínimo em Python. A
proposta é local-only.

```bash
python3 -m lfe approve G4 --option local-only
```

Agora `lfe status` mostra G1 a G4 `approved` e `production code: unlocked`. Só agora o projeto
pode entrar em S6:

```bash
python3 -m lfe stage S6
```

Antes do passo 5, o mesmo comando falha com `STAGE_GATE_VIOLATION` e diz quais gates faltam.

## Passo 6: usar o app

Sirva a pasta localmente (o `localStorage` fica preso a esta origem):

```bash
python3 -m http.server 8000 --bind 127.0.0.1
```

Abra `http://127.0.0.1:8000/app/` e confira cada requisito:

| Requisito | Como verificar | O que você vê |
|---|---|---|
| FR-001 | Escreva um título e pressione Enter | O item aparece no topo do sumário; o campo esvazia e mantém o foco |
| FR-002 | Recarregue a página | A lista continua lá |
| FR-003 | Marque a caixa de um item e recarregue | O item continua lido; a contagem acompanha |
| FR-004 | Pressione Enter com o campo vazio ou só com espaços | "Escreva um título antes de adicionar…" sob o campo; nada é salvo |
| FR-005 | Veja abaixo | Aviso vermelho no topo; a lista não muda e o título continua no campo |
| UX-001 | Use só Tab, Enter e Espaço | Tudo funciona, sempre com o anel de foco verde visível |

Para provocar o FR-005, cole no console do navegador e tente adicionar um título:

```js
Storage.prototype.setItem = () => { throw new DOMException("cheio", "QuotaExceededError"); };
```

Recarregue a página para desfazer. Os dados ficam na chave `lfe-vs01:readings:v1`, como
`{id, title, done, createdAt}`.

## Passo 7: ver uma aprovação ficar velha

Mude qualquer byte do protótipo e consulte o estado:

```bash
echo "<!-- ajuste -->" >> prototype/index.html && python3 -m lfe status
```

G2 e G3 passam a `stale` ("prototype/index.html changed after it was hashed") e G4 fica
`blocked`, porque depende de G3. O código de produção volta a `locked`. Reabrir é sempre decisão
humana: registrar a nova revisão (`lfe artifact ... --refresh-files`), propor de novo e aprovar.

## Passo 8: testes e evidências

```bash
python3 -m lfe run TEST-003 --req FR-001 --req FR-002 --req FR-003 --requires python:playwright -- python3 -m unittest discover -s tests_e2e
```

Sem o Playwright para Python instalado, o recibo sai `not_executed` com
`tool_unavailable:playwright`, e não `pass`. Ele não conta como prova.

```bash
python3 -m lfe handoff
```

Gera `.lfe/HANDOFF.md`: estágio, gates calculados, últimos recibos e o que o agente não pode
fazer. É o que uma próxima sessão lê para retomar sem adivinhar.

## Testes automáticos deste exemplo

Na raiz do repositório, sem navegador:

```bash
python3 -m unittest tests.test_vs01_example -v
```

O teste confere que os contratos são válidos, que todo hash bate com o disco, que o ledger está
íntegro e só tem propostas, que o HTML do app tem rótulo, `aria-live` e os IDs que o E2E vai
usar, que os tokens batem com o CSS e que nenhum arquivo cita caminho absoluto ou recurso de
rede.

### IDs que o E2E vai usar

Mudar um destes IDs em `app/index.html` exige mudar o teste E2E.

| Seletor | Papel |
|---|---|
| `#reading-form` | formulário de adicionar |
| `#reading-title` | campo do título, com `<label for>` "Próxima leitura" |
| `#reading-submit` | botão Adicionar |
| `#reading-error` | erro de validação, `aria-live="assertive"` (FR-004) |
| `#storage-error` | erro de armazenamento, `role="alert"` (FR-005) |
| `#reading-status` | anúncios de sucesso, `role="status"` |
| `#reading-list` | a lista; cada item é `li.entry[data-id]` com `input.entry-check` (FR-003) |
| `#reading-summary` | contagem "N para ler, N lidas" |
| `#empty-state` | estado vazio |

## Limites

Esta demo prova menos do que parece à primeira vista. O que ela **não** prova:

- **E2E com navegador real.** `tests_e2e/test_vs01.py` cobre FR-001..FR-005 e UX-001 (teclado em 390×844 e
  1280×800) com Playwright 1.49.1 e Chromium. A prova completa roda com um comando, na raiz do repositório:

  ```bash
  sh scripts/vs01-proof.sh ../lfe-vs01-prova
  ```

  Ela copia o exemplo para `../lfe-vs01-prova` (fora do repositório), aprova os gates como **simulados**, roda TEST-001 a TEST-005 com
  `lfe run`, confere os recibos e a rastreabilidade e grava `TEST_REPORT.json`, `.lfe/HANDOFF.md` e
  `.lfe/studio.html`. Sem o Playwright instalado, TEST-003 a TEST-005 ficam `not_executed` e a
  rastreabilidade fica **incompleta** (saída 6). Isso é proposital: sem prova, nada passa. No GitHub, o job
  `vs01-proof` instala o navegador e roda tudo a cada PR; os recibos ficam como artefato do job.
- **Política do core em uso.** TEST-001 prova, com o motor real, que escrever em `app/` é negado antes de
  G2, G3 e G4 e que o agente não consegue rodar `lfe approve`.
- **O app vem pronto antes das aprovações.** Num projeto real, `app/` só seria escrito depois de
  G2, G3 e G4 válidos. Aqui ele vem junto para a demo rodar offline e ser reproduzível.
- **A decisão de meio não tem comando próprio.** A baseline cita `DEC-002` porque, seguindo os
  passos na ordem, a aprovação de G2 com `--option local-html` recebe esse número. Se você
  registrar outra decisão antes, os números deixam de bater.
- **Acessibilidade:** contraste calculado (texto a partir de 6,5:1), teclado e foco conferidos
  à mão. A revisão humana (TEST-006) não foi feita. Isso não é uma declaração de conformidade
  WCAG.
- **Fontes do sistema.** A serifa muda entre aparelhos (Iowan, Palatino ou Georgia), e as
  capturas foram geradas com Chromium no macOS.
- **Ambiente.** Testado em macOS com Python 3.11. Windows não foi testado. Não há tema escuro.
- **`localStorage`** tem limite de alguns megabytes, pode ser apagado pela pessoa ou pelo
  navegador e não sincroniza entre aparelhos (ver ADR-001).
- **Replay automático** (`lfe demo vs01`, com decisões `simulated-human`) ainda não existe.
