#!/usr/bin/env python3
"""Casa nomes do dataset com as listas/fichas de forma conservadora.

Regras (nesta ordem, e só aceita quando o candidato é ÚNICO):
  R1. Chave exata (tokens sem acento, sem partículas, com variantes grafadas igualadas).
  R2. Conjunto de tokens da lista é SUBCONJUNTO do nome do dataset (nome de casada).
  R3. Conjunto de tokens do dataset é SUBCONJUNTO do nome da lista.
Não usa "N tokens em comum": isso casa homônimo parcial (dois "JÉSSICA ... ALMEIDA").
A camada fuzzy (R4) fica em quem chama e exige mesmo prenome e candidato único.
"""
import re
import unicodedata

# grafias que a mesma pessoa recebe nas diferentes fontes (Quadro x Lista de Antiguidade)
VARIANTES = {
    "souza": "sousa", "souzaa": "sousa",
    "vasconcelos": "vasconcellos", "vasconceloscoelho": "vasconcelloscoelho",
    "medes": "mendes", "mendez": "mendes",
    "viega": "veiga",
    "calvalcanti": "cavalcanti",
    "heriberto": "heriberto",
    "deymison": "deymison",
}


def fold(s):
    nf = unicodedata.normalize("NFKD", s or "")
    return "".join(c for c in nf if not unicodedata.combining(c)).lower()


def toks(s):
    out = []
    for t in re.split(r"[^a-z]+", fold(s)):
        if not t or t in {"de", "da", "do", "das", "dos", "e"}:
            continue
        out.append(VARIANTES.get(t, t))
    return out


def match(nome, pool):
    """pool: dict chave(tokens unidos por espaço)->valor. Devolve (valor, regra) ou (None, motivo)."""
    t = toks(nome)
    if not t:
        return None, "sem-nome"
    k = " ".join(t)
    if k in pool:
        return pool[k], "R1"
    ts = set(t)
    r2, r3 = [], []
    for kk, v in pool.items():
        ks = set(kk.split())
        if len(ks) >= 2 and ks <= ts:
            r2.append(v)
        elif len(ts) >= 2 and ts <= ks:
            r3.append(v)
    for cands, regra in ((r2, "R2"), (r3, "R3")):
        if len(cands) == 1:
            return cands[0], regra
        if len(cands) > 1:
            return None, f"ambiguo-{regra}"
    return None, "sem-match"
