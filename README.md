# Membros MPPE — app de consulta (iPhone)

App web (PWA) para consultar o **Quadro Geral de Membros do MPPE**: nome, cargo, promotoria,
telefone com link de WhatsApp, e-mail e foto 3×4 (opcional, guardada só no aparelho).

- **Abrir:** https://chlima123.github.io/membros-mppe-app/
- **Instalar no iPhone:** Safari → Compartilhar → *Adicionar à Tela de Início*.
- Funciona offline depois do primeiro acesso (service worker).

## Dados

`dataset.json` — 454 membros (90 cargos vagos excluídos), cruzando quatro fontes do vault `chlima123`:

| Campo | Fonte |
|---|---|
| nome, cargo, promotoria, entrância, circunscrição | Quadro Geral de Membros (portal MPPE, 4 telas de 18/11/2026) |
| telefone + WhatsApp | AMPPE 2026 (558 registros), com a Corregedoria-Geral como fallback |
| e-mail | export do diretório de usuários MPPE (30/01/2026, 469 registros) |

`build_dataset.py` reconstrói o `dataset.json` a partir das fontes (roda no Mac, com o vault montado).
`build.py` embute o JSON em `index.html` a partir de `app_template.html`.

## Cobertura verificada

- 454 membros (não 544 cargos: 90 estão vagos)
- 453 com telefone; 453 com link de WhatsApp; 450 com e-mail
- 6 telefones marcados **não confirmados** (número repetido em mais de um cadastro na fonte)
- 1 membro sem telefone e sem e-mail; 4 sem e-mail (recém-chegados por permuta, fora do export de janeiro)

## Estrutura

```
app_template.html      # UI (dados entram pelo marcador __DATA_JSON__)
build.py               # template + dataset.json -> index.html
dataset.json           # 454 registros
build_dataset.py       # extrai/cruza as fontes do vault
index.html             # app publicado (gerado)
manifest.webmanifest   # PWA
sw.js                  # cache offline
icon-180.png / icon-512.png
```

Fotos não saem do aparelho: ficam em IndexedDB, por membro.
