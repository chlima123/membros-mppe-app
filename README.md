# Membros MPPE — app de consulta (iPhone)

App web (PWA) para consultar o **Quadro Geral de Membros do MPPE**: nome, cargo, promotoria,
telefone com link de WhatsApp, e-mail e foto 3×4 (opcional, guardada só no aparelho).

- **Abrir:** https://chlima123.github.io/membros-mppe-app/
- **Instalar no iPhone:** Safari → Compartilhar → *Adicionar à Tela de Início*.
- Funciona offline depois do primeiro acesso (service worker).

## Dados

`dataset.json` — **465 membros** (79 cargos vagos excluídos), cruzando quatro fontes do vault `chlima123`:

| Campo | Fonte |
|---|---|
| nome, cargo, promotoria, entrância, circunscrição | Quadro Geral de Membros (portal MPPE, 4 telas de 18/11/2026) |
| telefone + WhatsApp | AMPPE 2026 (558 registros), com a Corregedoria-Geral como fallback |
| e-mail | export do diretório de usuários MPPE (30/01/2026, 469 registros) |

`build_dataset.py` reconstrói o `dataset.json` a partir das fontes (roda no Mac, com o vault montado).
Quem tomou posse **depois** do retrato do Quadro entra pelo overlay `posse_AAAA-MM-DD.json` (nome +
comarca; o build preenche o cargo que estava VAGO e falha se não houver vaga, em vez de inventar
registro). Hoje: `posse_2026-11-19.json` — 11 promotores de 1ª Entrância (Portarias PGJ 3.947 a
3.957/2026, DOE de 19/11/2026).
`build.py` embute o JSON em `index.html` a partir de `app_template.html`.

## Cobertura verificada

- 465 membros (não 544 cargos: 79 estão vagos)
- 453 com telefone; 453 com link de WhatsApp; 450 com e-mail
- 6 telefones marcados **não confirmados** (número repetido em mais de um cadastro na fonte)
- 12 sem telefone e sem e-mail — os 11 empossados em 19/11/2026 (não existem no AMPPE de ago/2026 nem no
  export de e-mails de jan/2026; casar por nome dava homônimo falso) + 1 sem cadastro nas fontes
- 15 sem e-mail (os 11 novos + 4 recém-chegados por permuta, fora do export de janeiro)
- entrância: 1ª = 59, 2ª = 129, 3ª = 222, 2ª Instância = 55

## Estrutura

```
app_template.html      # UI (dados entram pelo marcador __DATA_JSON__)
build.py               # template + dataset.json -> index.html
dataset.json           # 465 registros
build_dataset.py       # extrai/cruza as fontes do vault
posse_2026-11-19.json  # overlay das posses posteriores ao retrato do Quadro
index.html             # app publicado (gerado)
manifest.webmanifest   # PWA
sw.js                  # cache offline
icon-180.png / icon-512.png
```

Fotos não saem do aparelho: ficam em IndexedDB, por membro.
