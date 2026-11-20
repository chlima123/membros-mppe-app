#!/usr/bin/env python3
"""Mescla enriquecimento.json (datas/antiguidade) no dataset.json do app.

Regra de nome: casa por id do dataset (o enriquecimento já vem indexado por id).
Grava os campos novos e MANTÉM todos os antigos. Idempotente: pode rodar de novo.

Uso:  /usr/bin/python3 tools/merge_dataset.py
"""
import json, os, sys

APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DS = os.path.join(APP, "dataset.json")
ENR = os.path.join(APP, "enriquecimento.json")

CAMPOS = ["nascimento", "ingressoMP", "ingressoEntrancia", "inicioCargo",
          "ato", "portaria", "posicaoAntiguidade", "listaAntiguidade",
          "diasMP", "diasEntrancia", "nomeLista"]

ds = json.load(open(DS, encoding="utf-8"))
enr = json.load(open(ENR, encoding="utf-8"))

# fotos já extraídas (fotos/<id>.jpg) -> marca no registro
fotodir = os.path.join(APP, "fotos")
tem_foto = set()
if os.path.isdir(fotodir):
    tem_foto = {f[:-4] for f in os.listdir(fotodir) if f.lower().endswith(".jpg")}

n = 0
for r in ds:
    e = enr.get(r["id"], {})
    for c in CAMPOS:
        if c in e and e[c] not in (None, ""):
            r[c] = e[c]
        elif c in r and c not in e:
            pass  # mantém o que já existia
    r["foto"] = ("fotos/%s.jpg" % r["id"]) if r["id"] in tem_foto else ""
    if e:
        n += 1

json.dump(ds, open(DS, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print(f"dataset.json: {len(ds)} registros | com enriquecimento: {n} | com foto: {len(tem_foto)}")
