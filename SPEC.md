# SPEC — App iPhone de consulta aos membros do MPPE

Você vai gerar um **app web para iPhone** (PWA, single-page) que consulta os 454 membros do
Quadro Geral do MPPE. O arquivo de dados **já existe e NÃO deve ser alterado**:
`/Users/chlima/vercel-deploys/membros-mppe-app/dataset.json` (454 registros, 249 KB).

## Workspace (único lugar onde você pode escrever)

`/Users/chlima/vercel-deploys/membros-mppe-app/`

**NÃO modifique `dataset.json`, `build_dataset.py` nem nada fora desse diretório. Não toque no vault
Obsidian, não envie e-mail, não instale pacotes, não use a internet.**

## Arquivos a criar

1. **`app_template.html`** — app completo, autocontido (CSS + JS inline). Deve conter **exatamente
   uma linha** com o marcador de dados, isolado:

   ```js
   const DATA = __DATA_JSON__;
   ```

   Nenhum outro lugar do arquivo pode conter `__DATA_JSON__`.
2. **`build.py`** — lê `dataset.json` como texto (utf-8), faz a substituição literal do marcador em
   `app_template.html` e grava `index.html`. Deve falhar (exit 1) se o marcador não aparecer
   exatamente 1 vez. Sem dependências externas (só stdlib).
3. **`manifest.webmanifest`** — `name` "Membros MPPE", `short_name` "Membros", `display: standalone`,
   `background_color`, `theme_color`, `start_url: "./"`, ícones `icon-180.png` (180x180) e
   `icon-512.png` (512x512) — os PNGs são gerados por mim, apenas referencie.
4. **`sw.js`** — service worker cache-first para `./`, `./index.html`, `./manifest.webmanifest`,
   `./icon-180.png`, `./icon-512.png`; versão de cache `membros-v1`.

## Estrutura de cada registro de `dataset.json`

```json
{"id":"slug","nome":"NOME COMPLETO EM CAIXA ALTA","cargo":"4º Procurador de Justiça Criminal",
 "promotoria":"Recife","entrancia":"-","circunscricao":"2ª Instância","atribuicao":"Crime",
 "atuacao":"texto longo (pode ser vazio)","outrosCargos":[],
 "telefone":"081 987159442","whatsapp":"https://wa.me/5581987159442",
 "email":"adalberto@mppe.mp.br","fonteTelefone":"AMPPE","telefoneSuspeito":false,"matricula":""}
```

Fatos verificados (use como teste, **não digite esses números no código**; leia do JSON):
454 registros; 453 com `telefone`; 450 com `email`; 453 com `whatsapp`; 6 com
`telefoneSuspeito: true`; 1 sem telefone e sem e-mail; 4 sem e-mail.
`entrancia` vale `1ª`, `2ª`, `3ª` (promotores) ou `-` (2ª Instância / procuradores).

## Requisitos funcionais

1. **Lista** de todos os membros, ordenada por nome (A–Z), **agrupada por letra inicial** com
   cabeçalho sticky. Cada linha mostra nome, cargo e promotoria (2 linhas no máximo, com ellipsis).
2. **Busca instantânea** (input no topo, `type="search"`, `inputmode="search"`), insensível a
   acento e caixa, casando em nome, cargo, promotoria, circunscrição e e-mail. Debounce ≤ 100 ms.
   Contador `N de 454` sempre visível.
3. **Filtros** por chips horizontais roláveis: `Todas`, `1ª Entrância`, `2ª Entrância`, `3ª Entrância`,
   `2ª Instância` (= `entrancia: "-"`) + um `<select>` de **promotoria/município** (populado do JSON,
   ordenado, opção "Todos os municípios"). Botão `Limpar` quando houver filtro/busca ativos.
4. **Detalhe**: ao tocar na linha, abre uma **bottom sheet** (não navegação de página) com:
   - **foto 3:4** — caixa com `aspect-ratio: 3 / 4`, cantos arredondados, placeholder com ícone e
     texto "Adicionar foto". Se o membro tem **foto do acervo** (`foto` no dataset →
     `fotos/<id>.jpg`, quadrada 400x400), ela aparece primeiro. Toque abre seletor de arquivo
     (`accept="image/*"`); a imagem escolhida é **redimensionada para 480x640 (cover)** e guardada
     em **IndexedDB** com chave = `id` do membro, vencendo a do acervo; persiste após
     fechar/reabrir o app; botão discreto "remover foto". Precisa funcionar offline.
   - A lista mostra **avatar circular** por linha: foto do acervo quando existe, senão as iniciais
     (primeiro + último sobrenome). Se o arquivo da foto falhar, o avatar volta para as iniciais.
   - Nome completo (tipografia grande), cargo, promotoria + circunscrição, entrância.
   - `atuação` (texto do campo `atuacao`) em bloco secundário, só se não estiver vazio.
   - **Telefone** exibido no padrão local `0DDD NNNNNNNN` (ex.: `081 994324196`) com botão
     `WhatsApp` (abre `whatsapp` em nova aba) e botão `Ligar` (`tel:` com `+55`, sem o zero),
     além de "copiar número" (copia o mesmo texto exibido). Se `telefoneSuspeito` for `true`,
     mostrar selo âmbar "número não confirmado" ao lado do telefone. Se não houver telefone,
     mostrar "sem telefone no cadastro" em vez dos botões.
   - **E-mail** como `mailto:` clicável + botão copiar; se vazio, "sem e-mail no cadastro".
   - Rodapé discreto: fonte do telefone (`fonteTelefone`) e matrícula quando existir.
5. **Compartilhar** (botão no topo da sheet): `navigator.share` com nome, cargo, promotoria,
   telefone e e-mail; fallback = copiar para a área de transferência com toast "Copiado".
6. **Toast** de confirmação para cada ação de cópia (some em ~1,6 s).

## Requisitos de iPhone / PWA

- `<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover, maximum-scale=1">`
- `apple-mobile-web-app-capable`, `apple-mobile-web-app-status-bar-style=black-translucent`,
  `theme-color` com media query para claro/escuro, `<link rel="apple-touch-icon" href="./icon-180.png">`,
  `<link rel="manifest" href="./manifest.webmanifest">`.
- Safe areas: `padding-top: env(safe-area-inset-top)` no header e `env(safe-area-inset-bottom)` nos
  elementos fixos. `height: 100dvh`. Nada de scroll horizontal na página (só nos chips).
- `-webkit-tap-highlight-color: transparent`; feedback de toque imediato (`:active` com leve escala);
  `font-size: 16px` em inputs (evita zoom no iOS); `text-size-adjust: 100%`.
- Lista longa: `content-visibility: auto` + `contain-intrinsic-size` nas linhas; abrir a sheet não
  deve travar (usar transform/opacity, nada de animar layout).
- **Zero requisições externas**: nenhuma fonte web, nenhum CDN, nenhuma imagem remota. Só system font
  stack (`-apple-system, BlinkMacSystemFont, "SF Pro Text", system-ui, sans-serif`).
- Tema claro/escuro automático (`prefers-color-scheme`) + botão de alternância que persiste em
  `localStorage`; contraste mínimo AA nos dois temas.
- `prefers-reduced-motion: reduce` → sem animação de slide, só fade curto.
- Registrar o service worker só em `https:` / `localhost` e falhar silenciosamente se indisponível.
- Sheet fecha por botão, por toque no scrim e por swipe para baixo (arrastar 1:1 com o dedo,
  com histerese ~10 px; se o gesto não for vertical, ignorar).

## Design

Estilo iOS nativo, sóbrio e institucional (não é landing page): cabeçalho translúcido com
`backdrop-filter: blur(20px) saturate(180%)`, separadores finos, cantos 12–18 px, tipografia system
com tracking negativo apenas em títulos, hierarquia por peso. Verde institucional discreto como
acento (`#0b6b4f` claro / `#34c759` escuro em detalhes), WhatsApp em `#25D366` só no botão de ação.
Uma única tela + sheet — sem menus, sem abas.

## Critérios de aceite (você deve rodar e conferir antes de terminar)

Rode `python3 build.py` e verifique no `index.html` gerado, com um script Python seu:
1. `index.html` existe, > 60 KB, e não contém mais o marcador `__DATA_JSON__`.
2. O array embutido em `const DATA = [...]` faz `json.loads` e tem **454** itens; o primeiro item
   tem as chaves `id, nome, cargo, promotoria, telefone, whatsapp, email`.
3. Não há nenhuma referência a `http://` ou `https://` que não seja `https://wa.me/` em JS/template
   (exceto o comentário de fonte, se houver).
4. `node --check` (se `node` existir) passa para o JS extraído; senão, reporte que não rodou.
5. Escreva **`VERIFICACAO.md`** no workspace com: contagem de itens, tamanho dos arquivos, o que você
   testou e o que não testou. Seja honesto — não afirme teste que não rodou.

Ao terminar, responda em texto, em português: lista de arquivos criados, contagem de registros
lida do JSON, e o que ficou pendente.
