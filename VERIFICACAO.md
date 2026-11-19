# Verificação — App iPhone Membros MPPE

## Contagem de itens (lida de `const DATA = [...]` em `index.html`)

- **Total de registros:** 454
- **Com telefone:** 453 (1 sem telefone e sem e-mail)
- **Com WhatsApp:** 453
- **Com e-mail:** 450 (4 sem e-mail)
- **Com `telefoneSuspeito: true`:** 6
- **Com `matricula` preenchida:** 51
- **Distribuição por entrância (com normalização de `2º` → `2ª`):**
  - `1ª Entrância`: 48
  - `2ª Entrância`: 129 (128 registros como `2ª` + 1 registro grafado como `2º` em `dataset.json`)
  - `3ª Entrância`: 222
  - `2ª Instância` (`-`): 55
- **Municípios/promotorias únicos no `<select>`:** 98

## Tamanho dos arquivos

| Arquivo | Tamanho (bytes) |
| --- | ---: |
| `app_template.html` | 63.609 |
| `build.py` | 1.373 |
| `index.html` | 312.616 |
| `manifest.webmanifest` | 517 |
| `sw.js` | 1.374 |
| `dataset.json` (intocado) | 249.020 |

## O que foi testado

1. **Build (`python3 build.py`)**: executado com sucesso; gerou `index.html` (312.616 bytes, > 60 KB) e removeu completamente o marcador `__DATA_JSON__`.
2. **Isolamento do marcador e falha controlada do `build.py`**:
   - Verificado que `app_template.html` contém `__DATA_JSON__` exatamente 1 vez, isolado na linha `const DATA = __DATA_JSON__;`.
   - Testado `build.py` em diretório temporário com 0 e 2 ocorrências do marcador: falhou com `exit code 1` em ambos os casos.
3. **Integridade do JSON embutido em `index.html`**:
   - Extraído `const DATA = [...]` de `index.html` e parseado com `json.loads`: 454 itens válidos.
   - Verificado que o primeiro item contém todas as chaves esperadas (`id`, `nome`, `cargo`, `promotoria`, `telefone`, `whatsapp`, `email`).
   - Verificado que não há contagem `454` hardcoded em `app_template.html`.
4. **Zero requisições externas**:
   - Verificado via regex (`https?://`) que `app_template.html`, `sw.js` e `manifest.webmanifest` não contêm nenhuma URL `http://` ou `https://`.
   - Verificado que todas as 453 ocorrências de URL em `index.html` são exclusivamente `https://wa.me/...` provenientes de `dataset.json`.
5. **Sintaxe JavaScript (`node --check`, Node v22.22.3)**:
   - Passou nos 2 blocos `<script>` extraídos de `index.html`.
   - Passou em `sw.js`.
6. **Validação de `manifest.webmanifest`**:
   - Parseado com `json.loads`; confirmados `name`, `short_name`, `display: standalone`, `start_url: "./"`, `background_color`, `theme_color` e referências a `./icon-180.png` (180x180) e `./icon-512.png` (512x512).
7. **Lógica de normalização, agrupamento e busca em Node.js**:
   - Confirmado agrupamento de iniciais acentuadas (`ÉDIPO`, `ÉRICO`) na letra `E`.
   - Confirmada normalização de `entrancia: "2º"` para o filtro `2ª Entrância` (soma exata = 454).
   - Confirmada busca insensível a acento/caixa/ordinais via `NFKD` (`erico`, `vitoria de santo antao`, `2a instancia`, `4o procurador`).
   - Confirmada ordenação alfabética em português dos 98 municípios (`Água Preta` na posição correta sob `A`).

## O que NÃO foi testado

- **Renderização em navegador real / iPhone (Safari iOS e modo PWA standalone)**: não foi aberto em navegador headless nem em dispositivo físico; safe areas (`env(safe-area-inset-*)`), `backdrop-filter`, `content-visibility`, contraste visual efetivo e layout responsivo em tela real precisam de conferência no iPhone.
- **Fluxo de foto 3:4 em IndexedDB**: o seletor de arquivo, o redimensionamento via `<canvas>` (480×640 cover), a persistência após fechar/reabrir o app e o botão de remoção não foram executados em navegador.
- **Gesto de swipe-to-dismiss na bottom sheet**: o arrasto 1:1 com dedo, a histerese de 10 px e a convivência com rolagem interna da sheet não foram testados em tela sensível ao toque.
- **Service Worker offline (`sw.js`)**: o cache `membros-v1` e o funcionamento offline em `https://` ou `localhost` não foram exercitados em navegador.
- **Ações nativas de iOS**: abertura de `https://wa.me/...`, `tel:`, `mailto:`, `navigator.share` e cópia via `navigator.clipboard` não foram testadas no dispositivo.
