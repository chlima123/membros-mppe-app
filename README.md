# Membros MPPE — app de consulta (iPhone)

App web (PWA) para consultar o **Quadro Geral de Membros do MPPE**: nome, cargo, promotoria,
telefone com link de WhatsApp, e-mail, foto do acervo (quando existe) e foto 3×4 própria
(opcional, guardada só no aparelho).

- **Abrir:** https://chlima123.github.io/membros-mppe-app/
- **Instalar no iPhone:** Safari → Compartilhar → *Adicionar à Tela de Início*.
- Funciona offline depois do primeiro acesso (service worker; as fotos também ficam em cache).

## Dados

`dataset.json` — **465 membros** (79 cargos vagos excluídos), cruzando quatro fontes do vault `chlima123`:

| Campo | Fonte |
|---|---|
| nome, cargo, promotoria, entrância, circunscrição | Quadro Geral de Membros (portal MPPE, 4 telas de 18/11/2026) |
| telefone + WhatsApp | AMPPE 2026 (558 registros), com a Corregedoria-Geral como fallback; os 11 empossados de 19/11/2026 vêm do overlay `contatos_2026-11-23.json` (contatos conferidos pelo titular) |
| e-mail | export do diretório de usuários MPPE (30/01/2026, 469 registros) |
| nascimento, antiguidade, carreira | listas de antiguidade do CSMP (data-base 14/10/2026) |
| `foto` | acervo Bublup + caderno do Evernote — `fotos/<id>.jpg` |

`build_dataset.py` reconstrói o `dataset.json` a partir das fontes (roda no Mac, com o vault montado).
Quem tomou posse **depois** do retrato do Quadro entra pelo overlay `posse_AAAA-MM-DD.json` (nome +
comarca; o build preenche o cargo que estava VAGO e falha se não houver vaga, em vez de inventar
registro). Hoje: `posse_2026-11-19.json` — 11 promotores de 1ª Entrância (Portarias PGJ 3.947 a
3.957/2026, DOE de 19/11/2026).
`build.py` embute o JSON em `index.html` a partir de `app_template.html` e, no mesmo passo,
regenera a lista de fotos precacheadas no `sw.js`.

## Fotos do acervo

`tools/fotos_build.py` lê a pasta de origem (no Mac:
`~/Documents/ChatGPT/hermes_apps_factory/fotos_mppe`), recorta cada foto em quadrado 400×400
centrado no rosto e grava `fotos/<id>.jpg`, preenchendo o campo `foto` do `dataset.json`.

São **duas origens** na mesma pasta, com precedência para a primeira:

1. **Acervo Bublup** — retratos com o nome do membro no próprio nome do arquivo (9 aplicados).
2. **Caderno "Membros MPPE" do Evernote** — um arquivo `evernote_<hash>.png` por nota do membro
   (32 aplicados). O nome **não** está no arquivo: vem do título da nota correspondente e vive no
   dicionário `MAP_EVERNOTE`. Um mesmo membro pode aparecer nas duas origens (ex.: Ariano Tercio
   Silva de Aguiar); nesse caso vale o retrato do Bublup.

- Só entram arquivos que **são foto de rosto**: as duas pastas misturam retratos com PDFs de
  correição, ANEXO II da Corregedoria, prints de jornal/WhatsApp/Diário Oficial e tabelas com
  vários retratos. Esses ficam no dicionário `SKIP`, com o motivo (hoje: 41 aplicadas,
  34 ignoradas).
- A miniatura de uma nota do Evernote pode **não** ser o retrato do membro: já apareceu página do
  Diário Oficial, bilhete manuscrito e até **imagem imprópria** (nota "ANTONIO CARLOS ARAUJO",
  marcada no `SKIP` como não publicável). Todo arquivo novo passa por conferência visual antes de
  entrar — nunca aplique a miniatura só porque o nome da nota confere.
- O casamento foto → membro é **explícito** (`MAP`), conferido um a um; `APELIDOS` registra os
  casos em que o nome do arquivo difere do nome do quadro (ex.: "Carolina Gurgel Maia" ×
  "CAROLINA GURGEL LIMA").
- Recortes fora do padrão (selfie com duas pessoas, retrato largo) têm ajuste manual em `CROP`.
- Depois de rodar o script: `python3 build.py` e `python3 validate.py`.

Fotos enviadas pelo usuário não saem do aparelho: ficam em IndexedDB, por membro, e vencem a foto
do acervo. Se o arquivo da foto do acervo falhar, o avatar volta para as iniciais e a ficha volta
para o placeholder (nada de imagem quebrada).

## Cobertura verificada

- 465 membros (não 544 cargos: 79 estão vagos)
- 464 com telefone; 464 com link de WhatsApp; 450 com e-mail
- 41 com foto do acervo (9 do Bublup + 32 do caderno do Evernote); os demais mostram as iniciais no avatar
- 7 telefones marcados **não confirmados** (6 com número repetido em mais de um cadastro na fonte +
  1 empossado cuja atribuição do contato é só pela contagem da lista)
- 1 sem telefone e sem e-mail — único membro sem cadastro nas fontes de contato (os 11 empossados em
  19/11/2026, que não existem no AMPPE de ago/2026 nem no export de janeiro, entraram pelo overlay de contatos)
- 15 sem e-mail (os 11 novos + 4 recém-chegados por permuta, fora do export de janeiro)
- entrância: 1ª = 59, 2ª = 129, 3ª = 222, 2ª Instância = 55

## Estrutura

```
app_template.html      # UI (dados entram pelo marcador __DATA_JSON__)
build.py               # template + dataset.json -> index.html (+ precache de fotos no sw.js)
dataset.json           # 465 registros
build_dataset.py       # extrai/cruza as fontes do vault
posse_2026-11-19.json  # overlay das posses posteriores ao retrato do Quadro
contatos_2026-11-23.json # overlay de contato dos empossados (fora do AMPPE/export)
tools/fotos_build.py   # fotos do acervo (Bublup + Evernote) -> fotos/ + campo `foto`
fotos/                 # 41 fotos 400x400 (avatar e ficha)
index.html             # app publicado (gerado)
manifest.webmanifest   # PWA
sw.js                  # cache offline (index + ícones + fotos)
validate.py            # validação em navegador real (Playwright, perfil iPhone; MPPE_SENHA=<senha> testa o portão)
icon-180.png / icon-512.png
```

## Portão de senha

`app_template.html` abre num portão de senha (bloco `.lock` + `LOCK_HASH`) antes de mostrar o app; o
desbloqueio fica em `localStorage['mppe_unlock_v1']`. A senha **não** está escrita no arquivo: o código
guarda só o FNV-1a de `"mppe|" + senha`, e a comparação é feita em JS.

Limite conhecido: é página estática (GitHub Pages, repo público) — o portão barra acesso casual, mas
quem abrir o código-fonte ou o `dataset.json` no repositório vê os dados. Trocar a senha = recalcular o
hash e substituir `LOCK_HASH` no template (depois rodar `build.py`).
